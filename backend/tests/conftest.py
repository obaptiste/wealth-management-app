"""
PyTest configuration file with fixtures for testing.
"""
import pytest
import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import event

from backend.models import Base
from backend.database import get_db
from backend import main


# Test database URL - Use an in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create the test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False}  # Needed for SQLite
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def test_db(test_engine):
    """Get a test database session."""
    # Create a new session for a test
    # Create a new session for a test
    async_session = async_sessionmaker(
        test_engine, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Rollback all changes after test
        await session.rollback()


@pytest.fixture
async def override_get_db(test_db):
    """Override the get_db dependency in the app."""
    async def _override_get_db():
        yield test_db
    
    # Replace the dependency in the app
    app = main.app
    app.dependency_overrides[get_db] = _override_get_db
    
    yield
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def test_app(override_get_db):
    """Get the test app with overridden dependencies."""
    return main.app


@pytest.fixture
async def test_client(test_app):
    """Get a test client for the app."""
    from httpx import AsyncClient
    from httpx import ASGITransport
    
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        yield client