"""
Tests for the asset management endpoints.

Covers:
- POST   /portfolios/{id}/assets          (create)
- GET    /portfolios/{id}/assets          (list)
- GET    /portfolios/{id}/assets/{aid}    (detail with mocked yfinance)
- PUT    /portfolios/{id}/assets/{aid}    (update)
- DELETE /portfolios/{id}/assets/{aid}    (delete)
- 404 handling for missing portfolio / asset
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_portfolio(auth_client, name="Asset Test Portfolio"):
    resp = await auth_client.post(
        "/portfolios", json={"name": name, "description": "for asset tests"}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _mock_yf_ticker(close=150.0):
    """Return a mock yfinance Ticker whose history() gives one row."""
    mock_ticker = MagicMock()
    mock_df = pd.DataFrame(
        {"Close": [close], "Open": [145.0], "High": [155.0], "Low": [140.0], "Volume": [1000000]},
        index=[pd.Timestamp("2024-01-01")],
    )
    mock_ticker.history.return_value = mock_df
    return mock_ticker


_ASSET_PAYLOAD = {
    "symbol": "AAPL",
    "quantity": 10.0,
    "purchase_price": 145.0,
    "purchase_date": "2024-01-01T00:00:00Z",
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_asset(auth_client):
    """POST /portfolios/{id}/assets creates an asset."""
    portfolio = await _create_portfolio(auth_client, "Create Asset Portfolio")
    pid = portfolio["id"]

    with patch("yfinance.Ticker", return_value=_mock_yf_ticker()):
        resp = await auth_client.post(f"/portfolios/{pid}/assets", json=_ASSET_PAYLOAD)

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert data["quantity"] == 10.0
    assert data["purchase_price"] == 145.0
    assert data["portfolio_id"] == pid


@pytest.mark.asyncio
async def test_create_asset_symbol_stored_uppercase(auth_client):
    """Schema enforces uppercase symbol; endpoint stores what was submitted."""
    portfolio = await _create_portfolio(auth_client, "Case Portfolio")
    pid = portfolio["id"]

    # Schema requires uppercase – provide a valid uppercase symbol
    payload = {**_ASSET_PAYLOAD, "symbol": "MSFT"}
    with patch("yfinance.Ticker", return_value=_mock_yf_ticker()):
        resp = await auth_client.post(f"/portfolios/{pid}/assets", json=payload)

    assert resp.status_code == 200, resp.text
    assert resp.json()["symbol"] == "MSFT"


@pytest.mark.asyncio
async def test_create_asset_symbol_lowercase_rejected(auth_client):
    """The schema pattern rejects lowercase symbols with 422."""
    portfolio = await _create_portfolio(auth_client, "Validation Portfolio")
    pid = portfolio["id"]

    payload = {**_ASSET_PAYLOAD, "symbol": "msft"}
    resp = await auth_client.post(f"/portfolios/{pid}/assets", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_asset_portfolio_not_found(auth_client):
    """POST /portfolios/99999/assets returns 404."""
    with patch("yfinance.Ticker", return_value=_mock_yf_ticker()):
        resp = await auth_client.post("/portfolios/99999/assets", json=_ASSET_PAYLOAD)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_asset_unauthenticated(test_client):
    """POST /portfolios/{id}/assets without auth returns 401."""
    resp = await test_client.post("/portfolios/1/assets", json=_ASSET_PAYLOAD)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_assets(auth_client):
    """GET /portfolios/{id}/assets lists all assets in the portfolio."""
    portfolio = await _create_portfolio(auth_client, "List Assets Portfolio")
    pid = portfolio["id"]

    with patch("yfinance.Ticker", return_value=_mock_yf_ticker()):
        await auth_client.post(f"/portfolios/{pid}/assets", json=_ASSET_PAYLOAD)
        await auth_client.post(
            f"/portfolios/{pid}/assets",
            json={**_ASSET_PAYLOAD, "symbol": "GOOG"},
        )

    resp = await auth_client.get(f"/portfolios/{pid}/assets")
    assert resp.status_code == 200, resp.text
    assets = resp.json()
    assert isinstance(assets, list)
    symbols = {a["symbol"] for a in assets}
    assert "AAPL" in symbols
    assert "GOOG" in symbols


@pytest.mark.asyncio
async def test_list_assets_portfolio_not_found(auth_client):
    """GET /portfolios/99999/assets returns 404."""
    resp = await auth_client.get("/portfolios/99999/assets")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_asset_with_performance(auth_client):
    """GET /portfolios/{id}/assets/{aid} returns asset with performance metrics."""
    portfolio = await _create_portfolio(auth_client, "Get Asset Portfolio")
    pid = portfolio["id"]

    with patch("yfinance.Ticker", return_value=_mock_yf_ticker(160.0)):
        create_resp = await auth_client.post(
            f"/portfolios/{pid}/assets", json=_ASSET_PAYLOAD
        )
        asset_id = create_resp.json()["id"]

    with patch("yfinance.Ticker", return_value=_mock_yf_ticker(160.0)):
        resp = await auth_client.get(f"/portfolios/{pid}/assets/{asset_id}")

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["id"] == asset_id
    assert "current_price" in data
    assert "current_value" in data
    assert "profit_loss" in data
    assert "profit_loss_percent" in data
    # With close=160 and purchase_price=145, profit should be positive
    assert data["profit_loss"] > 0


@pytest.mark.asyncio
async def test_get_asset_not_found(auth_client):
    """GET /portfolios/{id}/assets/99999 returns 404."""
    portfolio = await _create_portfolio(auth_client, "Asset 404 Portfolio")
    pid = portfolio["id"]

    resp = await auth_client.get(f"/portfolios/{pid}/assets/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_asset(auth_client):
    """PUT /portfolios/{id}/assets/{aid} updates quantity and purchase_price."""
    portfolio = await _create_portfolio(auth_client, "Update Asset Portfolio")
    pid = portfolio["id"]

    with patch("yfinance.Ticker", return_value=_mock_yf_ticker()):
        create_resp = await auth_client.post(
            f"/portfolios/{pid}/assets", json=_ASSET_PAYLOAD
        )
        asset_id = create_resp.json()["id"]

    resp = await auth_client.put(
        f"/portfolios/{pid}/assets/{asset_id}",
        json={"quantity": 20.0, "purchase_price": 160.0},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["quantity"] == 20.0
    assert data["purchase_price"] == 160.0


@pytest.mark.asyncio
async def test_update_asset_not_found(auth_client):
    """PUT /portfolios/{id}/assets/99999 returns 404."""
    portfolio = await _create_portfolio(auth_client, "Update 404 Portfolio")
    pid = portfolio["id"]

    resp = await auth_client.put(
        f"/portfolios/{pid}/assets/99999",
        json={"quantity": 5.0},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_asset(auth_client):
    """DELETE /portfolios/{id}/assets/{aid} removes the asset (204)."""
    portfolio = await _create_portfolio(auth_client, "Delete Asset Portfolio")
    pid = portfolio["id"]

    with patch("yfinance.Ticker", return_value=_mock_yf_ticker()):
        create_resp = await auth_client.post(
            f"/portfolios/{pid}/assets", json=_ASSET_PAYLOAD
        )
        asset_id = create_resp.json()["id"]

    del_resp = await auth_client.delete(f"/portfolios/{pid}/assets/{asset_id}")
    assert del_resp.status_code == 204

    get_resp = await auth_client.get(f"/portfolios/{pid}/assets/{asset_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_asset_not_found(auth_client):
    """DELETE /portfolios/{id}/assets/99999 returns 404."""
    portfolio = await _create_portfolio(auth_client, "Delete 404 Portfolio")
    pid = portfolio["id"]

    resp = await auth_client.delete(f"/portfolios/{pid}/assets/99999")
    assert resp.status_code == 404
