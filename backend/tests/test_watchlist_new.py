"""
Tests for the watchlist management endpoints.

Covers:
- GET    /watchlist          (empty list, populated list, unauthenticated)
- POST   /watchlist          (add item, duplicate returns 409, unauthenticated)
- DELETE /watchlist/{symbol} (delete existing, delete missing 404, case-insensitive, unauthenticated)
- Sentiment enrichment on GET/POST when a SentimentResult row exists
"""
import pytest
from datetime import datetime, timezone

from backend.models import SentimentResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _add_symbol(auth_client, symbol: str, display_name=None, notes=None):
    """Helper to add a symbol to the watchlist and assert 201."""
    payload = {"symbol": symbol}
    if display_name:
        payload["display_name"] = display_name
    if notes:
        payload["notes"] = notes
    resp = await auth_client.post("/watchlist", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _seed_sentiment(test_db, symbol: str, sentiment: str, confidence: float):
    """Insert a SentimentResult row so enrichment tests have data to read."""
    row = SentimentResult(
        symbol=symbol,
        sentiment=sentiment,
        confidence=confidence,
        source_text="test_seed",
    )
    test_db.add(row)
    await test_db.commit()
    return row


# ---------------------------------------------------------------------------
# GET /watchlist
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_watchlist_schema(auth_client):
    """GET /watchlist returns a list with the expected item schema."""
    resp = await auth_client.get("/watchlist")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, list)
    # Verify every returned item has the expected fields.
    for item in data:
        assert "symbol" in item
        assert "added_at" in item


@pytest.mark.asyncio
async def test_get_watchlist_unauthenticated(test_client):
    """GET /watchlist without auth returns 401."""
    resp = await test_client.get("/watchlist")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_watchlist_returns_added_symbols(auth_client):
    """GET /watchlist includes symbols that were previously added."""
    await _add_symbol(auth_client, "MSFT")
    await _add_symbol(auth_client, "GOOG")

    resp = await auth_client.get("/watchlist")
    assert resp.status_code == 200, resp.text
    symbols = [item["symbol"] for item in resp.json()]
    assert "MSFT" in symbols
    assert "GOOG" in symbols


@pytest.mark.asyncio
async def test_get_watchlist_sentiment_enrichment(auth_client, test_db):
    """GET /watchlist items include latest_sentiment when a SentimentResult exists."""
    await _seed_sentiment(test_db, "NVDA", "positive", 0.92)
    await _add_symbol(auth_client, "NVDA")

    resp = await auth_client.get("/watchlist")
    assert resp.status_code == 200, resp.text

    nvda_items = [i for i in resp.json() if i["symbol"] == "NVDA"]
    assert len(nvda_items) >= 1

    sentiment = nvda_items[0]["latest_sentiment"]
    assert sentiment is not None
    assert sentiment["label"] == "positive"
    assert abs(sentiment["confidence"] - 0.92) < 1e-6
    # score for positive = +confidence
    assert abs(sentiment["score"] - 0.92) < 1e-6


@pytest.mark.asyncio
async def test_get_watchlist_no_sentiment(auth_client):
    """GET /watchlist items have latest_sentiment=null when no SentimentResult exists."""
    await _add_symbol(auth_client, "RARE")

    resp = await auth_client.get("/watchlist")
    assert resp.status_code == 200, resp.text

    rare_items = [i for i in resp.json() if i["symbol"] == "RARE"]
    assert len(rare_items) >= 1
    assert rare_items[0]["latest_sentiment"] is None


# ---------------------------------------------------------------------------
# POST /watchlist
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_add_to_watchlist(auth_client):
    """POST /watchlist creates an item and returns 201 with correct data."""
    data = await _add_symbol(auth_client, "TSLA", display_name="Tesla", notes="EV stock")
    assert data["symbol"] == "TSLA"
    assert data["display_name"] == "Tesla"
    assert data["notes"] == "EV stock"
    assert "added_at" in data


@pytest.mark.asyncio
async def test_add_duplicate_returns_409(auth_client):
    """POST /watchlist with an already-present symbol returns 409 Conflict."""
    await _add_symbol(auth_client, "AMZN")

    resp = await auth_client.post("/watchlist", json={"symbol": "AMZN"})
    assert resp.status_code == 409, resp.text
    assert "AMZN" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_add_to_watchlist_unauthenticated(test_client):
    """POST /watchlist without auth returns 401."""
    resp = await test_client.post("/watchlist", json={"symbol": "AAPL"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_add_invalid_symbol_rejected(auth_client):
    """POST /watchlist with a symbol that fails pattern validation returns 422."""
    # Lowercase is rejected by the schema pattern ^[A-Z0-9.]{1,20}$
    resp = await auth_client.post("/watchlist", json={"symbol": "aapl"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_add_with_sentiment_returns_enriched(auth_client, test_db):
    """POST /watchlist response includes sentiment when a SentimentResult exists."""
    await _seed_sentiment(test_db, "META", "negative", 0.75)
    data = await _add_symbol(auth_client, "META")

    sentiment = data["latest_sentiment"]
    assert sentiment is not None
    assert sentiment["label"] == "negative"
    # score for negative = -confidence
    assert abs(sentiment["score"] - (-0.75)) < 1e-6


# ---------------------------------------------------------------------------
# DELETE /watchlist/{symbol}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_existing_symbol(auth_client):
    """DELETE /watchlist/{symbol} removes the item and returns 204."""
    await _add_symbol(auth_client, "IBM")

    resp = await auth_client.delete("/watchlist/IBM")
    assert resp.status_code == 204

    # Verify it no longer appears in the list
    list_resp = await auth_client.get("/watchlist")
    symbols = [i["symbol"] for i in list_resp.json()]
    assert "IBM" not in symbols


@pytest.mark.asyncio
async def test_delete_missing_symbol_returns_404(auth_client):
    """DELETE /watchlist/{symbol} for a symbol not on the watchlist returns 404."""
    resp = await auth_client.delete("/watchlist/NOTEXIST")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_case_insensitive(auth_client):
    """DELETE /watchlist/aapl correctly deletes AAPL (symbol is normalized to upper)."""
    await _add_symbol(auth_client, "AAPL")

    resp = await auth_client.delete("/watchlist/aapl")
    assert resp.status_code == 204

    # Confirm removal
    list_resp = await auth_client.get("/watchlist")
    symbols = [i["symbol"] for i in list_resp.json()]
    assert "AAPL" not in symbols


@pytest.mark.asyncio
async def test_delete_unauthenticated(test_client):
    """DELETE /watchlist/{symbol} without auth returns 401."""
    resp = await test_client.delete("/watchlist/AAPL")
    assert resp.status_code == 401
