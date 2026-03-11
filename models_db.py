"""
ORM 数据模型
────────────────────────────────────────────────
三张表：
  Session       - 一次对话会话（开始/结束时间）
  EmotionLog    - 情绪检测记录（每次情绪变化时写入）
  ChatMessage   - 聊天消息记录（user + ai）
"""

from datetime import datetime
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Session(Base):
    __tablename__ = "sessions"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at:   Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    emotion_logs: Mapped[list["EmotionLog"]]   = relationship(back_populates="session", cascade="all, delete-orphan")
    chat_messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class EmotionLog(Base):
    __tablename__ = "emotion_logs"

    id:         Mapped[int]   = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int]   = mapped_column(Integer, ForeignKey("sessions.id"))
    timestamp:  Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    emotion:    Mapped[str]   = mapped_column(String(32))
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    session: Mapped["Session"] = relationship(back_populates="emotion_logs")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id:             Mapped[int]   = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id:     Mapped[int]   = mapped_column(Integer, ForeignKey("sessions.id"))
    timestamp:      Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    role:           Mapped[str]   = mapped_column(String(16))        # "user" | "ai"
    content:        Mapped[str]   = mapped_column(String(4096))
    emotion_at_time: Mapped[str]  = mapped_column(String(32), default="Neutral :|")

    session: Mapped["Session"] = relationship(back_populates="chat_messages")
