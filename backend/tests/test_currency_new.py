"""
Tests for the currency endpoints.

The external exchange-rate API is mocked so these tests run offline.

Covers:
- POST /currency/convert
- GET  /currency/rates
- GET  /currency/supported
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app, get_exchange_rates_from_api


# Ensure the lru_cache is cleared before each test to avoid cross-test contamination.
@pytest.fixture(autouse=True)
def clear_rate_cache():
    get_exchange_rates_from_api.cache_clear()
    yield
    get_exchange_rates_from_api.cache_clear()


_MOCK_RATES_USD = {
    "base": "USD",
    "rates": {
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "JPY": 149.50,
        "CHF": 0.88,
        "CAD": 1.35,
        "AUD": 1.52,
        "CNY": 7.24,
    },
    "last_updated": "2024-01-01T00:00:00Z",
}


# ---------------------------------------------------------------------------
# /currency/convert
# ---------------------------------------------------------------------------

def test_convert_usd_to_eur():
    """Converting USD to EUR returns correct converted amount."""
    with patch("backend.main.get_exchange_rates_from_api", return_value=_MOCK_RATES_USD):
        client = TestClient(app)
        resp = client.post(
            "/currency/convert",
            json={"from_currency": "USD", "to_currency": "EUR", "amount": 100.0},
        )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["from_currency"] == "USD"
    assert data["to_currency"] == "EUR"
    assert data["amount"] == 100.0
    assert data["converted_amount"] == pytest.approx(92.0, rel=0.01)
    assert data["exchange_rate"] == pytest.approx(0.92, rel=0.01)
    assert "last_updated" in data


def test_convert_same_currency():
    """Converting to the same currency yields the same amount."""
    with patch("backend.main.get_exchange_rates_from_api", return_value=_MOCK_RATES_USD):
        client = TestClient(app)
        resp = client.post(
            "/currency/convert",
            json={"from_currency": "USD", "to_currency": "USD", "amount": 500.0},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["converted_amount"] == pytest.approx(500.0)


def test_convert_unsupported_currency():
    """Converting to an unsupported currency returns 400."""
    with patch("backend.main.get_exchange_rates_from_api", return_value=_MOCK_RATES_USD):
        client = TestClient(app)
        resp = client.post(
            "/currency/convert",
            json={"from_currency": "USD", "to_currency": "XYZ", "amount": 100.0},
        )

    assert resp.status_code == 400
    assert "not supported" in resp.json()["detail"].lower()


def test_convert_missing_field():
    """Missing required field returns 422."""
    client = TestClient(app)
    resp = client.post(
        "/currency/convert",
        json={"from_currency": "USD", "to_currency": "EUR"},  # missing amount
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# /currency/rates
# ---------------------------------------------------------------------------

def test_get_exchange_rates():
    """GET /currency/rates returns base currency and a rates dictionary."""
    with patch("backend.main.get_exchange_rates_from_api", return_value=_MOCK_RATES_USD):
        client = TestClient(app)
        resp = client.get("/currency/rates?base=USD")

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["base"] == "USD"
    assert isinstance(data["rates"], dict)
    assert "EUR" in data["rates"]
    assert "last_updated" in data


def test_get_exchange_rates_default_base():
    """GET /currency/rates without ?base defaults to USD."""
    with patch("backend.main.get_exchange_rates_from_api", return_value=_MOCK_RATES_USD):
        client = TestClient(app)
        resp = client.get("/currency/rates")

    assert resp.status_code == 200
    assert resp.json()["base"] == "USD"


# ---------------------------------------------------------------------------
# /currency/supported
# ---------------------------------------------------------------------------

def test_get_supported_currencies():
    """GET /currency/supported returns a non-empty dictionary of currencies."""
    client = TestClient(app)
    resp = client.get("/currency/supported")

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "currencies" in data
    currencies = data["currencies"]
    assert isinstance(currencies, dict)
    assert len(currencies) > 0
    # A few well-known codes should always be present
    for code in ("USD", "EUR", "GBP", "JPY"):
        assert code in currencies


def test_get_supported_currencies_values_are_strings():
    """Currency values are human-readable strings."""
    client = TestClient(app)
    data = client.get("/currency/supported").json()
    for name in data["currencies"].values():
        assert isinstance(name, str)
        assert len(name) > 0
