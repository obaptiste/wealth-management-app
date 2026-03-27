"""
Tests for the new sentiment-analysis endpoints.

Covers:
- POST /sentiment/analyze          (text analysis)
- POST /sentiment/analyze-tweets   (tweet batch analysis)
- GET  /sentiment/history/{symbol} (historical trend)

The FinBERT model and Twitter API are mocked so these tests run offline.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import backend.globalSetting as globalSetting
from backend.main import app


# ---------------------------------------------------------------------------
# Shared mock for the sentiment model
# ---------------------------------------------------------------------------

class _MockSentimentModel:
    """Lightweight stand-in for the FinBERT pipeline."""

    def analyze(self, text: str):
        label = (
            "positive" if "great" in text.lower()
            else "negative" if "bad" in text.lower()
            else "neutral"
        )
        return [{"label": label, "score": 0.9}]

    def __call__(self, texts):
        results = []
        for text in texts:
            label = (
                "positive" if "great" in text.lower()
                else "negative" if "bad" in text.lower()
                else "neutral"
            )
            results.append({"label": label, "score": 0.9})
        return results


@pytest.fixture(autouse=True)
def mock_sentiment(monkeypatch):
    """Replace the global sentiment model for every test in this module."""
    monkeypatch.setattr(globalSetting, "sentiment_model", _MockSentimentModel())


# ---------------------------------------------------------------------------
# /sentiment/analyze
# ---------------------------------------------------------------------------

def test_analyze_positive_text():
    """Positive text returns 'positive' sentiment."""
    client = TestClient(app)
    resp = client.post("/sentiment/analyze", json={"text": "This stock is great!"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["sentiment"] == "positive"
    assert 0.0 <= data["confidence"] <= 1.0


def test_analyze_negative_text():
    """Negative text returns 'negative' sentiment."""
    client = TestClient(app)
    resp = client.post("/sentiment/analyze", json={"text": "This stock is really bad."})
    assert resp.status_code == 200, resp.text
    assert resp.json()["sentiment"] == "negative"


def test_analyze_neutral_text():
    """Neutral text returns 'neutral' sentiment."""
    client = TestClient(app)
    resp = client.post("/sentiment/analyze", json={"text": "The stock exists."})
    assert resp.status_code == 200, resp.text
    assert resp.json()["sentiment"] == "neutral"


def test_analyze_missing_field():
    """Missing 'text' field returns 422 Unprocessable Entity."""
    client = TestClient(app)
    resp = client.post("/sentiment/analyze", json={})
    assert resp.status_code == 422


def test_analyze_empty_text():
    """Empty string is accepted (model decides sentiment)."""
    client = TestClient(app)
    resp = client.post("/sentiment/analyze", json={"text": ""})
    # May be 200 (neutral) or 422 depending on validation rules – just check not 5xx
    assert resp.status_code in (200, 422)


def test_analyze_service_unavailable(monkeypatch):
    """Returns 503 when the sentiment model is None."""
    monkeypatch.setattr(globalSetting, "sentiment_model", None)
    client = TestClient(app)
    resp = client.post("/sentiment/analyze", json={"text": "test"})
    assert resp.status_code == 503


# ---------------------------------------------------------------------------
# /sentiment/analyze-tweets
# ---------------------------------------------------------------------------

_MOCK_TWEETS = {
    "symbol": "AAPL",
    "tweets": [
        {"text": "AAPL is great today!", "created_at": "2024-01-01T10:00:00Z"},
        {"text": "AAPL results were bad", "created_at": "2024-01-01T11:00:00Z"},
        {"text": "Bought some AAPL shares", "created_at": "2024-01-01T12:00:00Z"},
    ],
}


def test_analyze_tweets_returns_summary():
    """POST /sentiment/analyze-tweets returns sentiment summary and detail."""
    with patch("backend.main.get_tweets_about_stock", return_value=_MOCK_TWEETS):
        client = TestClient(app)
        resp = client.post("/sentiment/analyze-tweets?symbol=AAPL")

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert data["total_tweets"] == 3
    summary = data["sentiment_summary"]
    assert set(summary.keys()) == {"positive", "negative", "neutral"}
    assert sum(summary.values()) == pytest.approx(100.0, abs=0.1)
    assert "detailed_sentiments" in data


def test_analyze_tweets_no_tweets():
    """When no tweets are found the endpoint returns empty summary."""
    mock_data = {"symbol": "UNKNOWN", "tweets": []}
    with patch("backend.main.get_tweets_about_stock", return_value=mock_data):
        client = TestClient(app)
        resp = client.post("/sentiment/analyze-tweets?symbol=UNKNOWN")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_tweets"] == 0
    assert data["sentiment_summary"]["neutral"] == 100


def test_analyze_tweets_api_error():
    """When the Twitter API returns an error the endpoint returns 500."""
    mock_data = {"error": "API rate limit exceeded"}
    with patch("backend.main.get_tweets_about_stock", return_value=mock_data):
        client = TestClient(app)
        resp = client.post("/sentiment/analyze-tweets?symbol=AAPL")

    assert resp.status_code == 500
    assert "rate limit" in resp.json()["detail"].lower()


def test_analyze_tweets_symbol_required():
    """Missing 'symbol' query parameter returns 422."""
    client = TestClient(app)
    resp = client.post("/sentiment/analyze-tweets")
    assert resp.status_code == 422


def test_analyze_tweets_model_unavailable(monkeypatch):
    """Returns 503 when the model is None."""
    monkeypatch.setattr(globalSetting, "sentiment_model", None)
    mock_data = {"symbol": "AAPL", "tweets": [{"text": "test", "created_at": ""}]}
    with patch("backend.main.get_tweets_about_stock", return_value=mock_data):
        client = TestClient(app)
        resp = client.post("/sentiment/analyze-tweets?symbol=AAPL")
    assert resp.status_code == 503


# ---------------------------------------------------------------------------
# /sentiment/history/{symbol}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sentiment_history_empty(test_client):
    """GET /sentiment/history/AAPL returns empty list when no history exists."""
    resp = await test_client.get("/sentiment/history/AAPL")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert isinstance(data["sentiment_trends"], list)


@pytest.mark.asyncio
async def test_sentiment_history_days_param(test_client):
    """The 'days' query parameter is reflected in the response."""
    resp = await test_client.get("/sentiment/history/MSFT?days=14")
    assert resp.status_code == 200
    assert resp.json()["days_analyzed"] == 14


@pytest.mark.asyncio
async def test_sentiment_history_invalid_days(test_client):
    """'days' outside [1, 30] is rejected with 422."""
    resp = await test_client.get("/sentiment/history/AAPL?days=0")
    assert resp.status_code == 422

    resp2 = await test_client.get("/sentiment/history/AAPL?days=31")
    assert resp2.status_code == 422
