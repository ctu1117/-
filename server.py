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

import cv2
import numpy as np
import mediapipe as mp
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI

from emotion.detector import get_emotion

# ── 环境配置 ─────────────────────────────────────────────────────────────────
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

ai_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",   # 换 Kimi 改为 https://api.moonshot.cn/v1
)

# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(title="情绪感知 AI 聊天系统")

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


# ── WebSocket：视频帧 → 情绪检测 ──────────────────────────────────────────────
@app.websocket("/ws/emotion")
async def emotion_ws(websocket: WebSocket):
    await websocket.accept()
    start_time = time.time()

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

                # 时间戳必须单调递增（VIDEO 模式要求）
                ts_ms = int((time.time() - start_time) * 1000)

                mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                result = landmarker.detect_for_video(mp_img, ts_ms)

                if result and result.face_blendshapes:
                    emotion, conf = get_emotion(result.face_blendshapes[0])
                else:
                    emotion, conf = "No Face", 0.0

                await websocket.send_json({
                    "emotion":    emotion,
                    "confidence": round(conf, 2),
                })

        except WebSocketDisconnect:
            pass


# ── REST API：AI 聊天 ──────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message:    str
    emotion:    str   = "Neutral :|"
    confidence: float = 0.0
    history:    list  = []


@app.post("/api/chat")
async def chat(req: ChatRequest):
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
    for h in req.history[-8:]:       # 保留最近 8 条历史
        messages.append(h)
    messages.append({"role": "user", "content": req.message})

    resp = ai_client.chat.completions.create(
        model="deepseek-chat",        # Kimi 改为 "moonshot-v1-8k"
        messages=messages,
        max_tokens=300,
        temperature=0.8,
    )
    return {"reply": resp.choices[0].message.content}


# ── 静态文件（必须在所有路由之后挂载）────────────────────────────────────────
app.mount("/", StaticFiles(directory="static", html=True), name="static")
