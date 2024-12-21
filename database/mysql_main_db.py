from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from utils.config_loader import MYSQL_CONNECTION_STRING

# Enhanced engine configuration
engine = create_async_engine(
    MYSQL_CONNECTION_STRING,
    echo=False,  # Set to False in production for better performance
    pool_size=40,  # Reduced from 20 to prevent excess connections
    max_overflow=20,  # Reduced from 10 to prevent resource exhaustion
    pool_timeout=30,  # Reduced timeout for faster error detection
    pool_recycle=3600,  # Increased to reduce connection cycling overhead
    pool_pre_ping=True,  # Enable connection health checks
    
)

# Async sessionmaker
# Optimized session configuration
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False  # Prevent automatic flushing for better control
)


# Define the declarative base
Base = declarative_base()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create and manage database session with proper error handling and cleanup.
    Uses async context manager for better resource management.
    """
    session = AsyncSessionLocal()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

async def init_db() -> None:
    """
    Initialize database connection and perform startup checks.
    """
    try:
        async with engine.begin() as conn:
            # Optional: Create tables
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise