import pytest 
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio

async def test_analyse_text():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/analyse_text", json={"text": "The stock market is doing great!"})
        assert response.status_code == 200, f"Response status code is not 200. Body: {response.text}"
        print(response.json())
        # assert "label" in response.json()
        # assert response.json()["label"] == "POSITIVE"
        # assert "score" in response.json()
        # assert response.json()["score"] > 0.5