import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.mark.asyncio

async def test_update_portfolio():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.put(
            "/portfolio/1",
            json={
                "name": "Updated Portfolio Name",
                "assets": [
                    {
                        "symbol": "AAPL",
                        "quantity": 10,
                        "purchase_price": 150.0,
                        "purchase_date": "2023-01-01T00:00:00Z"
                    }
                ]
            }
        )
    assert response.status_code == 200, f"Response status code is not 200. Body: {response.text}"
