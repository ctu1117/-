"""
数据库连接与初始化

使用 SQLAlchemy 2.x async + aiosqlite
数据库文件: emotion.db
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "sqlite+aiosqlite:///./emotion.db"

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def init_db():
    from models_db import ChatMessage, EmotionLog, JournalEntry, Session, User, UserMemory  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        result = await conn.execute(text("PRAGMA table_info(journal_entries)"))
        columns = [row[1] for row in result.fetchall()]
        if "session_id" not in columns:
            await conn.execute(text("ALTER TABLE journal_entries ADD COLUMN session_id INTEGER"))


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
