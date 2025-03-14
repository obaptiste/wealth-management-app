# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import asynccontextmanager
import logging

from .config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create async engine using settings
engine = create_async_engine(
    settings.database_url_async,
    echo=settings.debug,
    pool_pre_ping=True,  # Check connection health before using
    pool_size=10,        # Sensible connection pool size
    max_overflow=20      # Allow additional connections under load
)

# Session factory for creating database sessions
async_session_factory = sessionmaker(
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False      # Prevent automatic flushing for better control
)

# Base class for SQLAlchemy models
Base = declarative_base()

@asynccontextmanager
async def get_db():
    """
    Dependency that provides a database session.
    
    Usage:
        async with get_db() as db:
            # Use db here
    
    Or with FastAPI:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            # Use db here
    """
    session = async_session_factory()
    try:
        yield session
        # No commit here - it should be explicitly called when needed
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

# For FastAPI dependency injection
async def get_db_dependency():
    """
    For FastAPI dependency injection.
    
    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db_dependency)):
            # Use db here
    """
    async with get_db() as session:
        yield session