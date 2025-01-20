
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from asgi_lifespan import LifespanManager  # Optional if you're testing app lifespan


@pytest.mark.asyncio
async def test_analyse_text():
    # Test with valid input
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/analyse_text", json={"text": "The stock market is doing great!"})
        assert response.status_code == 200, f"Response status code is not 200. Body: {response.text}"

        # Verify response structure and content
        response_json = response.json()
        assert isinstance(response_json, dict), "Response is not a dictionary"
        assert "sentiment" in response_json, "Response does not contain 'sentiment' key"
        assert isinstance(response_json["sentiment"], list), "'sentiment' is not a list"
        assert len(response_json["sentiment"]) > 0, "'sentiment' list is empty"
        first_sentiment = response_json["sentiment"][0]
        assert "label" in first_sentiment, "'label' key is missing in sentiment result"
        assert "score" in first_sentiment, "'score' key is missing in sentiment result"
        assert isinstance(first_sentiment["label"], str), "'label' is not a string"
        assert isinstance(first_sentiment["score"], float), "'score' is not a float"