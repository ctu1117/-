"""
ORM 数据模型
────────────────────────────────────────────────
三张表：
  Session       - 一次对话会话（开始/结束时间）
  EmotionLog    - 情绪检测记录（每次情绪变化时写入）
  ChatMessage   - 聊天消息记录（user + ai）
"""

from datetime import datetime, timezone, timedelta

# 北京时间 UTC+8
CST = timezone(timedelta(hours=8))
def now_cst() -> datetime:
    return datetime.now(tz=CST).replace(tzinfo=None)
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str]     = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str]= mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_cst)

    sessions: Mapped[list["Session"]]  = relationship(back_populates="user", cascade="all, delete-orphan")
    memory: Mapped["UserMemory"]       = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    journal_entries: Mapped[list["JournalEntry"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserMemory(Base):
    __tablename__ = "user_memories"

    id: Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int]      = mapped_column(Integer, ForeignKey("users.id"))
    facts: Mapped[str]        = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_cst, onupdate=now_cst)

    user: Mapped["User"]      = relationship(back_populates="memory")


class Session(Base):
    __tablename__ = "sessions"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:    Mapped[int]      = mapped_column(Integer, ForeignKey("users.id"), nullable=True) # nullable temporarily
    started_at: Mapped[datetime] = mapped_column(DateTime, default=now_cst)
    ended_at:   Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="sessions")

    emotion_logs: Mapped[list["EmotionLog"]]   = relationship(back_populates="session", cascade="all, delete-orphan")
    chat_messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    journal_entries: Mapped[list["JournalEntry"]] = relationship(back_populates="session")


class EmotionLog(Base):
    __tablename__ = "emotion_logs"

    id:         Mapped[int]   = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int]   = mapped_column(Integer, ForeignKey("sessions.id"))
    timestamp:  Mapped[datetime] = mapped_column(DateTime, default=now_cst)
    emotion:    Mapped[str]   = mapped_column(String(32))
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    session: Mapped["Session"] = relationship(back_populates="emotion_logs")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id:             Mapped[int]   = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id:     Mapped[int]   = mapped_column(Integer, ForeignKey("sessions.id"))
    timestamp:      Mapped[datetime] = mapped_column(DateTime, default=now_cst)
    role:           Mapped[str]   = mapped_column(String(16))        # "user" | "ai"
    content:        Mapped[str]   = mapped_column(String(4096))
    emotion_at_time: Mapped[str]  = mapped_column(String(32), default="Neutral :|")

    session: Mapped["Session"] = relationship(back_populates="chat_messages")


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    session_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sessions.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(120), default="")
    content: Mapped[str] = mapped_column(Text)
    emotion: Mapped[str] = mapped_column(String(32), default="Neutral :|")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_cst)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_cst, onupdate=now_cst)

    user: Mapped["User"] = relationship(back_populates="journal_entries")
    session: Mapped["Session"] = relationship(back_populates="journal_entries")
