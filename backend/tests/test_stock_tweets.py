import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from unittest.mock import patch

@pytest.mark.asyncio
async def test_stock_tweets_success():
    # Prepare mock data for a given symbol
    mock_data = {
        "symbol": "AAPL",
        "tweets": [
            {"text": "AAPL is soaring high!", "created_at": "2024-01-01T10:00:00Z"},
            {"text": "AAPL quarterly results look good", "created_at": "2024-01-01T11:00:00Z"}
        ]
    }
    with patch("backend.main.get_tweets_about_stock", return_value=mock_data):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/stock-tweets/AAPL")
            assert resp.status_code == 200, f"Response: {resp.text}"
            data = resp.json()
            assert data["symbol"] == "AAPL"
            assert isinstance(data["tweets"], list)
            assert len(data["tweets"]) == 2
