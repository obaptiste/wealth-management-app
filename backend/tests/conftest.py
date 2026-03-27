"""
PyTest configuration file with fixtures for testing.

Uses an in-memory SQLite database so tests run without a running PostgreSQL
instance. All tests that hit the database should use the ``test_client`` or
``auth_client`` fixtures defined here.
"""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from backend.models import Base
from backend.database import get_db_dependency
from backend import main

# ---------------------------------------------------------------------------
# Test database – in-memory SQLite (no external service required)
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Provide a single event loop for the whole test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create the in-memory SQLite engine and schema once per session."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="session")
async def test_db(test_engine):
    """
    Session-scoped database session shared across all tests.

    Tests that create data should use unique identifiers (e.g. unique e-mail
    addresses) to avoid conflicts between test functions.
    """
    session_factory = async_sessionmaker(
        test_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with session_factory() as session:
        yield session


# ---------------------------------------------------------------------------
# App / HTTP client fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def test_client(test_db):
    """
    Unauthenticated HTTP client wired to the in-memory test database.

    The ``get_db_dependency`` FastAPI dependency is overridden so every
    request uses the same in-memory SQLite session.
    """
    from httpx import AsyncClient, ASGITransport

    async def _override_get_db():
        yield test_db

    main.app.dependency_overrides[get_db_dependency] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=main.app), base_url="http://test"
    ) as client:
        yield client

    main.app.dependency_overrides.clear()


@pytest.fixture
async def auth_client(test_client):
    """
    Authenticated HTTP client.

    Registers a dedicated test user, obtains a JWT token and returns an
    ``AsyncClient`` that sends the ``Authorization: Bearer …`` header
    automatically.
    """
    from httpx import AsyncClient, ASGITransport

    # Register the helper user (ignore 400 if it already exists from a
    # previous fixture invocation in the same session).
    email = "fixture_user@test.example"
    password = "FixturePass1!"

    reg_resp = await test_client.post(
        "/auth/register",
        json={"username": "fixture_user", "email": email, "password": password},
    )
    assert reg_resp.status_code in (200, 400), (
        f"Unexpected registration status: {reg_resp.status_code} – {reg_resp.text}"
    )

    # Obtain token
    token_resp = await test_client.post(
        "/auth/token",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert token_resp.status_code == 200, (
        f"Token request failed: {token_resp.status_code} – {token_resp.text}"
    )
    token = token_resp.json()["access_token"]

    # Return a new client that always sends the auth header.
    # The DB override is already active (applied by the test_client fixture above).
    async with AsyncClient(
        transport=ASGITransport(app=main.app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client