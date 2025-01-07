import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select
from sqlalchemy import delete
from main import app
from backend import models
from backend.database import get_db


@pytest.mark.asyncio
async def test_register_user():
    # Cleanup: remove any existing user with the test email
    async with get_db() as db:
        await db.execute(delete(models.User).where(models.User.email == "john@example.com"))
        await db.commit()

    # Register user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/register",
            json={
                "username": "John Doe",
                "email": "john@example.com",
                "password": "securepassword123"
            }
        )
    assert response.status_code == 200, f"Response status code is {response.status_code}, response body: {response.text}"

    # Verify user creation
    async with get_db() as db:
        result = await db.execute(select(models.User).where(models.User.email == "john@example.com"))
        created_user = result.scalars().first()
        assert created_user is not None, "User was not created in the database"