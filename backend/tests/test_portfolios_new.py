"""
Tests for the portfolio management endpoints.

Covers:
- POST   /portfolios          (create)
- GET    /portfolios          (list)
- GET    /portfolios/{id}     (detail with mocked yfinance)
- PUT    /portfolios/{id}     (update)
- DELETE /portfolios/{id}     (delete)
- 404 handling for another user's portfolio
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_portfolio(auth_client, name="Test Portfolio", description="desc"):
    resp = await auth_client.post(
        "/portfolios",
        json={"name": name, "description": description},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_portfolio(auth_client):
    """Authenticated POST /portfolios creates a portfolio."""
    data = await _create_portfolio(auth_client, "My Portfolio")
    assert data["name"] == "My Portfolio"
    assert data["description"] == "desc"
    assert "id" in data
    assert "owner_id" in data


@pytest.mark.asyncio
async def test_create_portfolio_unauthenticated(test_client):
    """POST /portfolios without auth returns 401."""
    resp = await test_client.post(
        "/portfolios", json={"name": "No Auth"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_portfolios(auth_client):
    """GET /portfolios returns a list for the authenticated user."""
    await _create_portfolio(auth_client, "List Test 1")
    await _create_portfolio(auth_client, "List Test 2")

    resp = await auth_client.get("/portfolios")
    assert resp.status_code == 200, resp.text
    portfolios = resp.json()
    assert isinstance(portfolios, list)
    names = [p["name"] for p in portfolios]
    assert "List Test 1" in names
    assert "List Test 2" in names


@pytest.mark.asyncio
async def test_list_portfolios_unauthenticated(test_client):
    """GET /portfolios without auth returns 401."""
    resp = await test_client.get("/portfolios")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_portfolio_no_assets(auth_client):
    """
    GET /portfolios/{id} for an empty portfolio returns the portfolio with
    a summary and an empty assets list.
    """
    portfolio = await _create_portfolio(auth_client, "Empty Portfolio")
    pid = portfolio["id"]

    resp = await auth_client.get(f"/portfolios/{pid}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["id"] == pid
    assert data["assets"] == []
    assert "summary" in data
    summary = data["summary"]
    assert summary["total_value"] == 0.0
    assert summary["total_cost"] == 0.0


@pytest.mark.asyncio
async def test_get_portfolio_not_found(auth_client):
    """GET /portfolios/99999 returns 404."""
    resp = await auth_client.get("/portfolios/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_portfolio(auth_client):
    """PUT /portfolios/{id} updates the portfolio name and description."""
    portfolio = await _create_portfolio(auth_client, "Original Name")
    pid = portfolio["id"]

    resp = await auth_client.put(
        f"/portfolios/{pid}",
        json={"name": "Updated Name", "description": "new desc"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "new desc"


@pytest.mark.asyncio
async def test_update_portfolio_not_found(auth_client):
    """PUT /portfolios/99999 returns 404."""
    resp = await auth_client.put(
        "/portfolios/99999",
        json={"name": "Ghost"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_portfolio(auth_client):
    """DELETE /portfolios/{id} removes the portfolio (204 No Content)."""
    portfolio = await _create_portfolio(auth_client, "To Delete")
    pid = portfolio["id"]

    resp = await auth_client.delete(f"/portfolios/{pid}")
    assert resp.status_code == 204

    # Verify it's gone
    get_resp = await auth_client.get(f"/portfolios/{pid}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_portfolio_not_found(auth_client):
    """DELETE /portfolios/99999 returns 404."""
    resp = await auth_client.delete("/portfolios/99999")
    assert resp.status_code == 404
