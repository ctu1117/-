"""
FastAPI 后端服务

启动方式:
    python -m uvicorn server:app --reload
访问地址:
    http://localhost:8000
"""

import base64
import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, time as dt_time, timedelta, timezone

import bcrypt
import cv2
import jwt
import mediapipe as mp
import numpy as np
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal, get_db, init_db
from emotion.detector import get_emotion
from models_db import ChatMessage, EmotionLog, JournalEntry, Session as DbSession, User, UserMemory

CST = timezone(timedelta(hours=8))


def now_cst() -> datetime:
    return datetime.now(tz=CST).replace(tzinfo=None)


SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key-12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.InvalidTokenError as exc:
        raise credentials_exception from exc

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
ai_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="情绪感知 AI 伴侣系统", lifespan=lifespan, debug=True)

_BaseOptions = mp.tasks.BaseOptions
_FaceLandmarker = mp.tasks.vision.FaceLandmarker
_FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
_VideoMode = mp.tasks.vision.RunningMode.VIDEO
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "face_landmarker.task")


def _make_landmarker():
    options = _FaceLandmarkerOptions(
        base_options=_BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=_VideoMode,
        output_face_blendshapes=True,
        num_faces=1,
    )
    return _FaceLandmarker.create_from_options(options)


class UserCreate(BaseModel):
    username: str
    password: str


class JournalCreate(BaseModel):
    title: str = Field(default="", max_length=120)
    content: str = Field(min_length=1, max_length=4000)
    emotion: str = Field(default="Neutral :|", max_length=32)
    session_id: int | None = None


class ChatRequest(BaseModel):
    message: str
    emotion: str = "Neutral :|"
    confidence: float = 0.0
    history: list = []
    session_id: int = 0


def serialize_journal_entry(entry: JournalEntry) -> dict:
    return {
        "id": entry.id,
        "title": entry.title,
        "content": entry.content,
        "emotion": entry.emotion,
        "session_id": entry.session_id,
        "created_at": entry.created_at.isoformat(),
        "updated_at": entry.updated_at.isoformat(),
    }


def stabilize_emotion(history: deque[tuple[str, float]], min_votes: int = 3) -> tuple[str, float]:
    valid_items = [(emotion, confidence) for emotion, confidence in history if emotion != "No Face"]
    if not valid_items:
        return "No Face", 0.0

    counts: dict[str, int] = defaultdict(int)
    confidences: dict[str, float] = defaultdict(float)
    for emotion, confidence in valid_items:
        counts[emotion] += 1
        confidences[emotion] += confidence

    stable_emotion = max(counts, key=lambda item: (counts[item], confidences[item]))
    vote_count = counts[stable_emotion]
    avg_confidence = round(confidences[stable_emotion] / vote_count, 2)

    if stable_emotion == "Neutral :|":
        return ("Neutral :|", avg_confidence) if vote_count >= 2 else ("No Face", 0.0)

    if vote_count < min_votes:
        return "Neutral :|", 0.0

    return stable_emotion, avg_confidence


@app.post("/api/register")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already registered")

    new_user = User(username=user.username, password_hash=get_password_hash(user.password))
    db.add(new_user)
    await db.flush()
    db.add(UserMemory(user_id=new_user.id))
    await db.commit()
    return {"message": "Success"}


@app.post("/api/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": token, "token_type": "bearer", "username": user.username}


@app.post("/api/session/start")
async def start_session(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = DbSession(user_id=current_user.id, started_at=now_cst())
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {"session_id": session.id, "started_at": session.started_at.isoformat()}


@app.post("/api/session/end/{session_id}")
async def end_session(session_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DbSession).where(DbSession.id == session_id))
    session = result.scalar_one_or_none()
    if session:
        session.ended_at = now_cst()
        await db.commit()
    return {"ok": True}


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(DbSession).where(DbSession.id == session_id, DbSession.user_id == current_user.id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
    return {"ok": True}


@app.get("/api/sessions")
async def list_sessions(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(DbSession).where(DbSession.user_id == current_user.id).order_by(DbSession.started_at.desc())
    )
    sessions = result.scalars().all()

    output = []
    for session in sessions:
        emotion_result = await db.execute(
            select(EmotionLog.emotion, func.count(EmotionLog.id).label("cnt"))
            .where(EmotionLog.session_id == session.id)
            .group_by(EmotionLog.emotion)
            .order_by(func.count(EmotionLog.id).desc())
            .limit(1)
        )
        top = emotion_result.first()
        dominant_emotion = top.emotion if top else "Neutral :|"

        message_result = await db.execute(
            select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session.id)
        )
        journal_result = await db.execute(
            select(func.count(JournalEntry.id)).where(JournalEntry.session_id == session.id)
        )

        output.append(
            {
                "id": session.id,
                "started_at": session.started_at.isoformat(),
                "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                "dominant_emotion": dominant_emotion,
                "message_count": message_result.scalar() or 0,
                "journal_count": journal_result.scalar() or 0,
            }
        )
    return output


@app.get("/api/session/{session_id}/emotions")
async def get_session_emotions(session_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(EmotionLog.emotion, func.count(EmotionLog.id).label("cnt"))
        .join(DbSession)
        .where(EmotionLog.session_id == session_id, DbSession.user_id == current_user.id)
        .group_by(EmotionLog.emotion)
    )
    rows = result.all()
    return {row.emotion: row.cnt for row in rows}


@app.get("/api/session/{session_id}/messages")
async def get_session_messages(session_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(ChatMessage)
        .join(DbSession)
        .where(ChatMessage.session_id == session_id, DbSession.user_id == current_user.id)
        .order_by(ChatMessage.timestamp)
    )
    messages = result.scalars().all()
    return [
        {
            "role": message.role,
            "content": message.content,
            "emotion_at_time": message.emotion_at_time,
            "timestamp": message.timestamp.isoformat(),
        }
        for message in messages
    ]


@app.get("/api/session/{session_id}/trend")
async def get_session_trend(session_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(EmotionLog)
        .join(DbSession)
        .where(EmotionLog.session_id == session_id, DbSession.user_id == current_user.id)
        .order_by(EmotionLog.timestamp)
    )
    logs = result.scalars().all()
    return [
        {
            "timestamp": log.timestamp.isoformat(),
            "emotion": log.emotion,
            "confidence": round(log.confidence, 2),
        }
        for log in logs
    ]


@app.get("/api/emotions/calendar")
async def get_emotions_calendar(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(func.date(EmotionLog.timestamp).label("day"), EmotionLog.emotion, func.count(EmotionLog.id).label("cnt"))
        .join(DbSession)
        .where(DbSession.user_id == current_user.id)
        .group_by(func.date(EmotionLog.timestamp), EmotionLog.emotion)
    )

    day_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in result.all():
        day_counts[row.day][row.emotion] = row.cnt

    calendar_data = []
    for day, counts in day_counts.items():
        counts.pop("No Face", None)
        if not counts:
            continue
        dominant = max(counts.items(), key=lambda item: item[1])[0]
        calendar_data.append([day, dominant])
    return calendar_data


@app.get("/api/stats")
async def global_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(EmotionLog.emotion, func.count(EmotionLog.id).label("cnt"))
        .join(DbSession)
        .where(DbSession.user_id == current_user.id)
        .group_by(EmotionLog.emotion)
    )
    rows = result.all()
    return {row.emotion: row.cnt for row in rows}


@app.get("/api/reports/today")
async def today_report(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = now_cst().date()
    day_start = datetime.combine(today, dt_time.min)
    day_end = day_start + timedelta(days=1)

    sessions_result = await db.execute(
        select(DbSession)
        .where(DbSession.user_id == current_user.id, DbSession.started_at >= day_start, DbSession.started_at < day_end)
        .order_by(DbSession.started_at.desc())
    )
    sessions_today = sessions_result.scalars().all()
    session_ids = [session.id for session in sessions_today]

    dominant_emotion = "Neutral :|"
    message_count = 0

    if session_ids:
        message_result = await db.execute(
            select(func.count(ChatMessage.id)).where(ChatMessage.session_id.in_(session_ids))
        )
        message_count = message_result.scalar() or 0

        emotion_result = await db.execute(
            select(EmotionLog.emotion, func.count(EmotionLog.id).label("cnt"))
            .where(EmotionLog.session_id.in_(session_ids))
            .group_by(EmotionLog.emotion)
            .order_by(func.count(EmotionLog.id).desc())
            .limit(1)
        )
        top = emotion_result.first()
        if top:
            dominant_emotion = top.emotion

    journal_result = await db.execute(
        select(func.count(JournalEntry.id)).where(
            JournalEntry.user_id == current_user.id,
            JournalEntry.created_at >= day_start,
            JournalEntry.created_at < day_end,
        )
    )

    return {
        "date": today.isoformat(),
        "session_count": len(sessions_today),
        "message_count": message_count,
        "journal_count": journal_result.scalar() or 0,
        "dominant_emotion": dominant_emotion,
    }


@app.get("/api/journal")
async def list_journal_entries(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(JournalEntry).where(JournalEntry.user_id == current_user.id).order_by(JournalEntry.created_at.desc())
    )
    entries = result.scalars().all()
    return [serialize_journal_entry(entry) for entry in entries]


@app.post("/api/journal")
async def create_journal_entry(payload: JournalCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Journal content cannot be empty")

    session_id = payload.session_id
    if session_id is not None:
        session_result = await db.execute(
            select(DbSession).where(DbSession.id == session_id, DbSession.user_id == current_user.id)
        )
        if session_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Session not found")

    entry = JournalEntry(
        user_id=current_user.id,
        session_id=session_id,
        title=payload.title.strip(),
        content=content,
        emotion=payload.emotion.strip() or "Neutral :|",
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return serialize_journal_entry(entry)


@app.delete("/api/journal/{entry_id}")
async def delete_journal_entry(entry_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(JournalEntry).where(JournalEntry.id == entry_id, JournalEntry.user_id == current_user.id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    await db.delete(entry)
    await db.commit()
    return {"ok": True}


@app.websocket("/ws/emotion/{session_id}")
async def emotion_ws(websocket: WebSocket, session_id: int):
    await websocket.accept()
    start_time = time.time()
    last_emotion = None
    emotion_history: deque[tuple[str, float]] = deque(maxlen=5)

    async with AsyncSessionLocal() as db:
        with _make_landmarker() as landmarker:
            try:
                while True:
                    data = await websocket.receive_text()
                    payload = data.split(",", 1)[1] if "," in data else data
                    img_bytes = base64.b64decode(payload)
                    arr = np.frombuffer(img_bytes, np.uint8)
                    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)

                    if frame is None:
                        await websocket.send_json({"emotion": "No Face", "confidence": 0.0})
                        continue

                    ts_ms = int((time.time() - start_time) * 1000)
                    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                    result = landmarker.detect_for_video(mp_img, ts_ms)

                    if result and result.face_blendshapes:
                        raw_emotion, raw_confidence = get_emotion(result.face_blendshapes[0])
                    else:
                        raw_emotion, raw_confidence = "No Face", 0.0

                    emotion_history.append((raw_emotion, raw_confidence))
                    stable_emotion, stable_confidence = stabilize_emotion(emotion_history)

                    if stable_emotion != last_emotion and stable_emotion not in {"No Face", "Neutral :|"}:
                        db.add(
                            EmotionLog(
                                session_id=session_id,
                                emotion=stable_emotion,
                                confidence=stable_confidence,
                                timestamp=now_cst(),
                            )
                        )
                        await db.commit()
                        last_emotion = stable_emotion
                    elif stable_emotion == "Neutral :|":
                        last_emotion = stable_emotion

                    await websocket.send_json({"emotion": stable_emotion, "confidence": stable_confidence})
            except WebSocketDisconnect:
                pass


@app.post("/api/chat")
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    system_prompt = f"""你是一个具有很强共情能力的 AI 情绪陪伴助手。
你现在通过摄像头观察到用户当前情绪是：{req.emotion}。
要求：
1. 在回复中自然提到你观察到的情绪变化。
2. 语气像朋友一样温和、真诚。
3. 结合用户输入内容：{req.message}
4. 中文回复，控制在 100 字以内。"""

    messages = [{"role": "system", "content": system_prompt}]
    for history_item in req.history[-8:]:
        messages.append(history_item)
    messages.append({"role": "user", "content": req.message})

    response = ai_client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        max_tokens=300,
        temperature=0.8,
    )
    reply = response.choices[0].message.content

    if req.session_id:
        db.add(
            ChatMessage(
                session_id=req.session_id,
                role="user",
                content=req.message,
                emotion_at_time=req.emotion,
                timestamp=now_cst(),
            )
        )
        db.add(
            ChatMessage(
                session_id=req.session_id,
                role="ai",
                content=reply,
                emotion_at_time=req.emotion,
                timestamp=now_cst(),
            )
        )
        await db.commit()

    return {"reply": reply}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
