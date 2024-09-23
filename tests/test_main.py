import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.main import app
from backend import models
from backend.database import get_db

@pytest.mark.asyncio
async def test_register_user():

    #cleanup: remove any existing user with the test email
    async with get_db() as db:
        await db.execute(select(models.User).where(models.User.email == "john@example.com"))
        await db.commit()

    #test register user
    # app.dependency_overrides[get_db] = override_get_db  #override the get_db dependency to use the test database
    # app.dependency_overrides[get_current_user] = override_get_current_user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/register",
            json={
                "username": "John Doe",
                "email": "john@example.com",
                "password": "securepassword123"
            }
        )
    print("Status Code:", response.status_code)
    print("Response Body:", response.text)
    assert response.status_code == 200, f"Response status code is {response.status_code}, response body: {response.text}"
