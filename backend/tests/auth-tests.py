"""
Authentication tests for the wealth management API.
Tests user registration, token generation, and validation.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.main import app
from backend.models import User
from backend.database import get_db


@pytest.mark.asyncio
async def test_health_check():
    """Test the health check endpoint."""
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_register_user():
    """Test user registration."""
    # Create test DB session
    async with get_db() as db:
        # Clean up any existing test user
        await db.execute(delete(User).where(User.email == "test_user@example.com"))
        await db.commit()

    # Register a new user
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
        response = await client.post(
            "/register",
            json={
                "username": "Test User",
                "email": "test_user@example.com",
                "password": "securepassword123"
            }
        )
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["username"] == "Test User"
        assert user_data["email"] == "test_user@example.com"
        assert "id" in user_data

    # Verify user exists in database
    async with get_db() as db:
        result = await db.execute(select(User).where(User.email == "test_user@example.com"))
        user = result.scalars().first()
        assert user is not None
        assert user.username == "Test User"


@pytest.mark.asyncio
async def test_login_token_generation():
    """Test login and token generation."""
    # Register user first if not exists
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
        # First try to register (in case user doesn't exist)
        await client.post(
            "/register",
            json={
                "username": "Token Test User",
                "email": "token_test@example.com",
                "password": "tokenpassword123"
            }
        )
        
        # Now try to get a token
        response = await client.post(
            "/token",
            data={
                "username": "token_test@example.com",
                "password": "tokenpassword123"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_invalid_login():
    """Test login with invalid credentials."""
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
        response = await client.post(
            "/token",
            data={
                "username": "nonexistent@example.com",
                "password": "wrongpassword"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 401
        assert "detail" in response.json()


@pytest.mark.asyncio
async def test_register_duplicate_email():
    """Test registering with an email that already exists."""
    # First register a user
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
        # Ensure user exists
        await client.post(
            "/register",
            json={
                "username": "Duplicate Test",
                "email": "duplicate@example.com",
                "password": "duplicatepass123"
            }
        )
        
        # Try to register again with the same email
        response = await client.post(
            "/register",
            json={
                "username": "Duplicate Test 2",
                "email": "duplicate@example.com",
                "password": "anotherpass123"
            }
        )
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]