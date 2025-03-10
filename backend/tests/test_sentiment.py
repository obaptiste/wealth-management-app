import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.main import app
import backend.globalSetting as globalSetting

client = TestClient(app)

# Mock the sentiment model
class MockSentimentModel:
    def __call__(self, texts):
        if isinstance(texts, list):
            return [
                {"label": "positive", "score": 0.9} if "great" in text.lower() else
                {"label": "negative", "score": 0.8} if "bad" in text.lower() else
                {"label": "neutral", "score": 0.7}
                for text in texts
            ]
        else:
            if "great" in texts.lower():
                return [{"label": "positive", "score": 0.9}]
            elif "bad" in texts.lower():
                return [{"label": "negative", "score": 0.8}]
            else:
                return [{"label": "neutral", "score": 0.7}]


@pytest.fixture(autouse=True)
def mock_sentiment_model():
    """Replace the sentiment model with our mock implementation for all tests"""
    original_model = globalSetting.sentiment_model
    globalSetting.sentiment_model = MockSentimentModel()
    yield
    globalSetting.sentiment_model = original_model


@pytest.fixture
def mock_tweets():
    """Mock the tweet fetching function"""
    with patch("backend.main.get_tweets_about_stock") as mock:
        mock.return_value = {
            "symbol": "AAPL",
            "tweets": [
                {"text": "AAPL stock is doing great today!", "created_at": "2023-01-01T12:00:00Z"},
                {"text": "Not sure about AAPL's future", "created_at": "2023-01-01T12:30:00Z"},
                {"text": "AAPL quarterly results were bad", "created_at": "2023-01-01T13:00:00Z"}
            ]
        }
        yield mock


def test_analyse_text():
    """Test the analyse_text endpoint with different sentiments"""
    # Test positive sentiment
    response = client.post("/analyse_text", json={"text": "This stock is great!"})
    assert response.status_code == 200
    assert response.json()["sentiment"][0]["label"] == "positive"
    
    # Test negative sentiment
    response = client.post("/analyse_text", json={"text": "This stock is bad!"})
    assert response.status_code == 200
    assert response.json()["sentiment"][0]["label"] == "negative"
    
    # Test neutral sentiment
    response = client.post("/analyse_text", json={"text": "This stock exists."})
    assert response.status_code == 200
    assert response.json()["sentiment"][0]["label"] == "neutral"


def test_analyse_tweets(mock_tweets):
    """Test the analyse_tweets endpoint with mocked tweets"""
    response = client.post("/analyse_tweets?symbol=AAPL")
    assert response.status_code == 200
    
    # Check response structure
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["total_tweets"] == 3
    assert "sentiment_summary" in data
    assert "detailed_sentiments" in data
    
    # Check sentiment summary percentages
    summary = data["sentiment_summary"]
    assert summary["positive"] == pytest.approx(33.33, 0.01)
    assert summary["negative"] == pytest.approx(33.33, 0.01)
    assert summary["neutral"] == pytest.approx(33.33, 0.01)


def test_analyse_tweets_no_tweets(mock_tweets):
    """Test the analyse_tweets endpoint when no tweets are found"""
    mock_tweets.return_value = {"symbol": "UNKNOWN", "tweets": []}
    
    response = client.post("/analyse_tweets?symbol=UNKNOWN")
    assert response.status_code == 200
    assert response.json() == {"symbol": "UNKNOWN", "sentiment": "No recent tweets found"}


@patch("backend.main.get_tweets_about_stock")
def test_analyse_tweets_error(mock_get_tweets):
    """Test the analyse_tweets endpoint when an error occurs"""
    mock_get_tweets.return_value = {"error": "API rate limit exceeded"}
    
    response = client.post("/analyse_tweets?symbol=AAPL")
    assert response.status_code == 500
    assert response.json()["detail"] == "API rate limit exceeded"


def test_sentiment_model_loading():
    """Test that the sentiment model can be correctly accessed"""
    assert globalSetting.sentiment_model is not None