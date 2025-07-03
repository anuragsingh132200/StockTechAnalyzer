import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from contextlib import asynccontextmanager

from config import settings

# Create async engine
def get_database_url():
    url = settings.DATABASE_URL
    if "postgresql://" in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    # Remove SSL parameters that might cause issues with asyncpg
    if "?sslmode=" in url:
        url = url.split("?")[0]
    return url

engine = create_async_engine(
    get_database_url(),
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300
)

# Create session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def init_db():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            # Import models to ensure they're registered
            from models import User, Subscription, RateLimit
            await conn.run_sync(Base.metadata.create_all)
        logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error creating database tables: {e}")
        raise

@asynccontextmanager
async def get_db():
    """Get database session"""
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()
