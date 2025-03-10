"""
Sentiment analysis tests for the wealth management API.
Tests text analysis and tweet sentiment analysis with mocks.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock

from backend.main import app


# Mock sentiment analysis results for different inputs
MOCK_SENTIMENT_RESULTS = {
    "The market is doing great today!": [{"label": "positive", "score": 0.95}],
    "Stock prices are falling rapidly.": [{"label": "negative", "score": 0.87}],
    "The company announced their quarterly earnings.": [{"label": "neutral", "score": 0.78}]
}


class MockSentimentModel:
    """Mock sentiment analysis model."""
    
    def __call__(self, text):
        """Mock the model's prediction function."""
        if text in MOCK_SENTIMENT_RESULTS:
            return MOCK_SENTIMENT_RESULTS[text]
        
        # Default to neutral for unknown text
        return [{"label": "neutral", "score": 0.5}]


@pytest.mark.asyncio
async def test_analyse_text():
    """Test analyzing text sentiment."""
    # Patch the sentiment model dependency
    with patch("backend.globalSetting.sentiment_model", MockSentimentModel()):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Test positive sentiment
            response = await client.post(
                "/analyse_text",
                json={"text": "The market is doing great today!"}
            )
            
            assert response.status_code == 200
            result = response.json()
            assert "sentiment" in result
            assert result["sentiment"][0]["label"] == "positive"
            assert result["sentiment"][0]["score"] > 0.9
            
            # Test negative sentiment
            response = await client.post(
                "/analyse_text",
                json={"text": "Stock prices are falling rapidly."}
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["sentiment"][0]["label"] == "negative"
            
            # Test neutral sentiment
            response = await client.post(
                "/analyse_text",
                json={"text": "The company announced their quarterly earnings."}
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["sentiment"][0]["label"] == "neutral"


@pytest.mark.asyncio
async def test_invalid_text_input():
    """Test providing invalid input to the sentiment analysis endpoint."""
    with patch("backend.globalSetting.sentiment_model", MockSentimentModel()):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Test with empty text
            response = await client.post(
                "/analyse_text",
                json={"text": ""}
            )
            
            # The model should still return a result for empty text
            assert response.status_code == 200
            
            # Test with missing text field
            response = await client.post(
                "/analyse_text",
                json={"not_text": "This should fail"}
            )
            
            # Should fail validation
            assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyse_tweets():
    """Test analyzing tweets about a stock."""
    # Mock the tweet fetching and sentiment model
    with patch("backend.main.get_tweets_about_stock") as mock_get_tweets, \
         patch("backend.globalSetting.sentiment_model", MockSentimentModel()):
        
        # Setup mock tweet data
        mock_get_tweets.return_value = {
            "symbol": "TSLA",
            "tweets": [
                "Tesla stock is soaring today!",
                "Just bought more $TSLA shares.",
                "Worried about Tesla's valuation."
            ]
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/analyse_tweets", params={"symbol": "TSLA"})
            
            assert response.status_code == 200
            result = response.json()
            assert result["symbol"] == "TSLA"
            assert "sentiment_summary" in result
            assert "total_tweets" in result
            assert result["total_tweets"] == 3
            

@pytest.mark.asyncio
async def test_analyse_tweets_no_tweets():
    """Test analyzing tweets when no tweets are found."""
    with patch("backend.main.get_tweets_about_stock") as mock_get_tweets, \
         patch("backend.globalSetting.sentiment_model", MockSentimentModel()):
        
        # Setup mock empty tweet data
        mock_get_tweets.return_value = {
            "symbol": "UNKNOWN",
            "tweets": []
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/analyse_tweets", params={"symbol": "UNKNOWN"})
            
            assert response.status_code == 200
            result = response.json()
            assert result["symbol"] == "UNKNOWN"
            assert "sentiment" in result
            assert result["sentiment"] == "No recent tweets found"


@pytest.mark.asyncio
async def test_analyse_tweets_error():
    """Test error handling when tweet fetching fails."""
    with patch("backend.main.get_tweets_about_stock") as mock_get_tweets:
        
        # Setup mock error response
        mock_get_tweets.return_value = {
            "error": "API rate limit exceeded"
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/analyse_tweets", params={"symbol": "AAPL"})
            
            assert response.status_code == 500
            assert "detail" in response.json()
            assert "API rate limit" in response.json()["detail"]
