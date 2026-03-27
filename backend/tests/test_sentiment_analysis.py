
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app


@pytest.mark.asyncio
async def test_analyse_text():
    # Test with valid input
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/analyse_text", json={"text": "The stock market is doing great!"})
        assert response.status_code == 200, f"Response status code is not 200. Body: {response.text}"

        # The /analyse_text endpoint now delegates to /sentiment/analyze which returns
        # {"sentiment": str, "confidence": float}
        response_json = response.json()
        assert isinstance(response_json, dict), "Response is not a dictionary"
        assert "sentiment" in response_json, "Response does not contain 'sentiment' key"
        assert isinstance(response_json["sentiment"], str), "'sentiment' is not a string"
        assert "confidence" in response_json, "Response does not contain 'confidence' key"
        assert isinstance(response_json["confidence"], float), "'confidence' is not a float"
        assert 0.0 <= response_json["confidence"] <= 1.0, "'confidence' is out of range"