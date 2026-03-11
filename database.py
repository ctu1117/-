"""
数据库连接与初始化
────────────────────────────────────────────────
使用 SQLAlchemy 2.x (async) + aiosqlite
数据库文件：emotion.db（项目根目录）
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
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
    """创建所有数据表（如不存在则新建）"""
    from models_db import Session, EmotionLog, ChatMessage  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """FastAPI 依赖注入：提供一个异步数据库 Session"""
    async with AsyncSessionLocal() as session:
        yield session
