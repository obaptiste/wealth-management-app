"""
Tests for the stock-data endpoints.

yfinance is mocked so these tests run offline.

Covers:
- GET /stocks/{symbol}          – current price data
- GET /stocks/{symbol}/history  – historical OHLCV data
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from fastapi.testclient import TestClient
from backend.main import app


def _make_mock_ticker(close=150.0, empty=False):
    """Build a mock yfinance Ticker that returns a single-row DataFrame."""
    mock_ticker = MagicMock()
    if empty:
        mock_ticker.history.return_value = pd.DataFrame()
    else:
        mock_ticker.history.return_value = pd.DataFrame(
            {
                "Open": [145.0],
                "Close": [close],
                "High": [155.0],
                "Low": [140.0],
                "Volume": [5_000_000],
            },
            index=[pd.Timestamp("2024-01-15")],
        )
    return mock_ticker


# ---------------------------------------------------------------------------
# /stocks/{symbol}
# ---------------------------------------------------------------------------

def test_get_stock_data_success():
    """GET /stocks/AAPL returns price, change, volume etc. for a valid symbol."""
    with patch("yfinance.Ticker", return_value=_make_mock_ticker(150.0)):
        client = TestClient(app)
        resp = client.get("/stocks/AAPL")

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert data["price"] == pytest.approx(150.0)
    assert "change" in data
    assert "change_percent" in data
    assert "volume" in data
    assert "high" in data
    assert "low" in data


def test_get_stock_data_symbol_uppercased():
    """Symbol is normalised to upper case."""
    with patch("yfinance.Ticker", return_value=_make_mock_ticker()):
        client = TestClient(app)
        resp = client.get("/stocks/aapl")

    assert resp.status_code == 200
    assert resp.json()["symbol"] == "AAPL"


def test_get_stock_data_no_data():
    """When yfinance returns an empty DataFrame the endpoint returns an error key."""
    with patch("yfinance.Ticker", return_value=_make_mock_ticker(empty=True)):
        client = TestClient(app)
        resp = client.get("/stocks/FAKE")

    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data


# ---------------------------------------------------------------------------
# /stocks/{symbol}/history
# ---------------------------------------------------------------------------

def _make_history_ticker(periods=5):
    """Return a mock Ticker with ``periods`` rows of history data."""
    mock_ticker = MagicMock()
    dates = pd.date_range("2024-01-01", periods=periods, freq="D")
    mock_ticker.history.return_value = pd.DataFrame(
        {
            "Open": [100.0 + i for i in range(periods)],
            "Close": [102.0 + i for i in range(periods)],
            "High": [105.0 + i for i in range(periods)],
            "Low": [98.0 + i for i in range(periods)],
            "Volume": [1_000_000] * periods,
        },
        index=dates,
    )
    return mock_ticker


def test_get_stock_history_default_period():
    """GET /stocks/AAPL/history returns OHLCV data for the default period."""
    with patch("yfinance.Ticker", return_value=_make_history_ticker(5)):
        client = TestClient(app)
        resp = client.get("/stocks/AAPL/history")

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert "history" in data
    assert len(data["history"]) == 5
    first = data["history"][0]
    assert "date" in first
    assert "open" in first
    assert "close" in first
    assert "high" in first
    assert "low" in first
    assert "volume" in first


def test_get_stock_history_custom_period():
    """GET /stocks/AAPL/history?period=5d uses the provided period."""
    with patch("yfinance.Ticker", return_value=_make_history_ticker(3)):
        client = TestClient(app)
        resp = client.get("/stocks/AAPL/history?period=5d")

    assert resp.status_code == 200
    data = resp.json()
    assert data["period"] == "5d"


def test_get_stock_history_invalid_period():
    """An invalid period query value is rejected."""
    client = TestClient(app)
    resp = client.get("/stocks/AAPL/history?period=invalid")
    assert resp.status_code == 422


def test_get_stock_history_empty():
    """When no historical data exists the endpoint returns an empty list."""
    with patch("yfinance.Ticker", return_value=_make_mock_ticker(empty=True)):
        client = TestClient(app)
        resp = client.get("/stocks/UNKNOWN/history")

    assert resp.status_code == 200
    data = resp.json()
    assert data["history"] == []
