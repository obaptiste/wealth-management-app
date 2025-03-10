import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend import models
from backend.database import get_db
from sqlalchemy.future import select
from sqlalchemy import delete

@pytest.mark.asyncio
async def test_token_generation():
    # Clean up any existing test user
    async with get_db() as db:
        await db.execute(delete(models.User).where(models.User.email=="testuser@example.com"))
        await db.commit()
        
    # Register test user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        reg_resp = await client.post("/register", json={
            "username": "TestUser",
            "email": "testuser@example.com",
            "password": "testpassword"
        })
        assert reg_resp.status_code == 200, f"Registration failed: {reg_resp.text}"
        
        # Login and get token (using x-www-form-urlencoded)
        login_data = {"username": "testuser@example.com", "password": "testpassword"}
        token_resp = await client.post(
            "/token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert token_resp.status_code == 200, f"Token request failed: {token_resp.text}"
        json_data = token_resp.json()
        assert "access_token" in json_data
        assert json_data["token_type"] == "bearer"
