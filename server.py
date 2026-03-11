"""
FastAPI 后端服务
────────────────────────────────────────────────
启动方式: python -m uvicorn server:app --reload
地址:      http://localhost:8000
────────────────────────────────────────────────
"""

import base64
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime

import cv2
import numpy as np
import mediapipe as mp
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import init_db, get_db
from models_db import Session as DbSession, EmotionLog, ChatMessage
from emotion.detector import get_emotion

# ── 环境配置 ─────────────────────────────────────────────────────────────────
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

ai_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
)

# ── 应用生命周期（启动时初始化数据库）────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

# ── FastAPI App ────────────────────────────────────────────────────────────────
app = FastAPI(title="情绪感知 AI 聊天系统", lifespan=lifespan)

# ── MediaPipe 初始化 ──────────────────────────────────────────────────────────
_BaseOptions        = mp.tasks.BaseOptions
_FaceLandmarker     = mp.tasks.vision.FaceLandmarker
_FaceLandmarkerOpts = mp.tasks.vision.FaceLandmarkerOptions
_VideoMode          = mp.tasks.vision.RunningMode.VIDEO

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "face_landmarker.task")

def _make_landmarker():
    opts = _FaceLandmarkerOpts(
        base_options=_BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=_VideoMode,
        output_face_blendshapes=True,
        num_faces=1,
    )
    return _FaceLandmarker.create_from_options(opts)


# ══════════════════════════════════════════════════════════════
# 会话管理 API
# ══════════════════════════════════════════════════════════════

@app.post("/api/session/start")
async def start_session(db: AsyncSession = Depends(get_db)):
    """创建新的对话会话"""
    session = DbSession(started_at=datetime.utcnow())
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {"session_id": session.id, "started_at": session.started_at.isoformat()}


@app.post("/api/session/end/{session_id}")
async def end_session(session_id: int, db: AsyncSession = Depends(get_db)):
    """结束指定会话"""
    result = await db.execute(select(DbSession).where(DbSession.id == session_id))
    session = result.scalar_one_or_none()
    if session:
        session.ended_at = datetime.utcnow()
        await db.commit()
    return {"ok": True}


# ══════════════════════════════════════════════════════════════
# 历史数据查询 API
# ══════════════════════════════════════════════════════════════

@app.get("/api/sessions")
async def list_sessions(db: AsyncSession = Depends(get_db)):
    """获取所有会话列表（倒序）"""
    result = await db.execute(
        select(DbSession).order_by(DbSession.started_at.desc())
    )
    sessions = result.scalars().all()

    out = []
    for s in sessions:
        # 统计该会话的主要情绪
        emo_result = await db.execute(
            select(EmotionLog.emotion, func.count(EmotionLog.id).label("cnt"))
            .where(EmotionLog.session_id == s.id)
            .group_by(EmotionLog.emotion)
            .order_by(func.count(EmotionLog.id).desc())
            .limit(1)
        )
        top = emo_result.first()
        dominant_emotion = top.emotion if top else "Neutral :|"

        # 消息数量
        msg_result = await db.execute(
            select(func.count(ChatMessage.id)).where(ChatMessage.session_id == s.id)
        )
        msg_count = msg_result.scalar() or 0

        out.append({
            "id": s.id,
            "started_at": s.started_at.isoformat(),
            "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            "dominant_emotion": dominant_emotion,
            "message_count": msg_count,
        })
    return out


@app.get("/api/session/{session_id}/emotions")
async def get_session_emotions(session_id: int, db: AsyncSession = Depends(get_db)):
    """获取某会话的情绪分布（饼图数据）"""
    result = await db.execute(
        select(EmotionLog.emotion, func.count(EmotionLog.id).label("cnt"))
        .where(EmotionLog.session_id == session_id)
        .group_by(EmotionLog.emotion)
    )
    rows = result.all()
    return {row.emotion: row.cnt for row in rows}


@app.get("/api/session/{session_id}/messages")
async def get_session_messages(session_id: int, db: AsyncSession = Depends(get_db)):
    """获取某会话的完整聊天记录"""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.timestamp)
    )
    msgs = result.scalars().all()
    return [
        {
            "role": m.role,
            "content": m.content,
            "emotion_at_time": m.emotion_at_time,
            "timestamp": m.timestamp.isoformat(),
        }
        for m in msgs
    ]


@app.get("/api/stats")
async def global_stats(db: AsyncSession = Depends(get_db)):
    """全局情绪统计（所有会话合计，饼图数据）"""
    result = await db.execute(
        select(EmotionLog.emotion, func.count(EmotionLog.id).label("cnt"))
        .group_by(EmotionLog.emotion)
    )
    rows = result.all()
    return {row.emotion: row.cnt for row in rows}


# ══════════════════════════════════════════════════════════════
# WebSocket：视频帧 → 情绪检测 + 写入数据库
# ══════════════════════════════════════════════════════════════

@app.websocket("/ws/emotion/{session_id}")
async def emotion_ws(websocket: WebSocket, session_id: int):
    await websocket.accept()
    start_time = time.time()
    last_emotion = None

    async with AsyncSessionLocal() as db:
        with _make_landmarker() as landmarker:
            try:
                while True:
                    data = await websocket.receive_text()

                    # base64 data URL 解码 → OpenCV 帧
                    payload = data.split(",", 1)[1] if "," in data else data
                    img_bytes = base64.b64decode(payload)
                    arr   = np.frombuffer(img_bytes, np.uint8)
                    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)

                    if frame is None:
                        await websocket.send_json({"emotion": "No Face", "confidence": 0.0})
                        continue

                    ts_ms = int((time.time() - start_time) * 1000)
                    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                    result = landmarker.detect_for_video(mp_img, ts_ms)

                    if result and result.face_blendshapes:
                        emotion, conf = get_emotion(result.face_blendshapes[0])
                    else:
                        emotion, conf = "No Face", 0.0

                    # 情绪变化时写入数据库（避免过于频繁写入）
                    if emotion != last_emotion and emotion != "No Face":
                        log = EmotionLog(
                            session_id=session_id,
                            emotion=emotion,
                            confidence=round(conf, 2),
                            timestamp=datetime.utcnow(),
                        )
                        db.add(log)
                        await db.commit()
                        last_emotion = emotion

                    await websocket.send_json({
                        "emotion":    emotion,
                        "confidence": round(conf, 2),
                    })

            except WebSocketDisconnect:
                pass


# ── AsyncSessionLocal 在 WebSocket 中使用 ────────────────────────────────────
from database import AsyncSessionLocal  # noqa: E402


# ══════════════════════════════════════════════════════════════
# REST API：AI 聊天 + 保存记录
# ══════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    message:    str
    emotion:    str   = "Neutral :|"
    confidence: float = 0.0
    history:    list  = []
    session_id: int   = 0     # 0 表示未创建会话（兼容旧前端）


@app.post("/api/chat")
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    system_prompt = f"""你是一个具有极强共情能力的 AI 视觉伴侣。
    你现在正通过摄像头看着用户，你实时观察到了用户的情绪是：【{req.emotion}】。

要求：
1. **必须在回复的开头或合适位置，自然地提到你观察到的情绪**。
   - 例如 (Happy): "看到你笑得这么开心，我也跟着高兴起来了！发生什么好事了？"
   - 例如 (Sad): "你的眼神看起来有些低落，是遇到什么心事了吗？我会一直陪着你的。"
   - 例如 (Angry): "感觉你现在心情有些急躁，先深呼吸一下，慢慢跟我说..."
2. 语气要极其自然，像真正的朋友在面对面聊天。
3. 结合用户说的话：{req.message}。
4. 中文回复，字数控制在 100 字以内。"""

    messages = [{"role": "system", "content": system_prompt}]
    for h in req.history[-8:]:
        messages.append(h)
    messages.append({"role": "user", "content": req.message})

    resp = ai_client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        max_tokens=300,
        temperature=0.8,
    )
    reply = resp.choices[0].message.content

    # 保存聊天记录到数据库
    if req.session_id:
        user_msg = ChatMessage(
            session_id=req.session_id,
            role="user",
            content=req.message,
            emotion_at_time=req.emotion,
            timestamp=datetime.utcnow(),
        )
        ai_msg = ChatMessage(
            session_id=req.session_id,
            role="ai",
            content=reply,
            emotion_at_time=req.emotion,
            timestamp=datetime.utcnow(),
        )
        db.add(user_msg)
        db.add(ai_msg)
        await db.commit()

    return {"reply": reply}


# ── 静态文件（必须在所有路由之后挂载）────────────────────────────────────────
app.mount("/", StaticFiles(directory="static", html=True), name="static")
