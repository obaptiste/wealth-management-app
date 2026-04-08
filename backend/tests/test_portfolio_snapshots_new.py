"""
Tests for persisted portfolio snapshot endpoints and same-day refresh behavior.
"""
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from backend.portfolio_snapshots import capture_portfolio_snapshot


async def _create_portfolio(auth_client, name="Snapshot Test Portfolio"):
    resp = await auth_client.post(
        "/portfolios",
        json={"name": name, "description": "for snapshot tests"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _mock_yf_ticker(close=150.0):
    mock_ticker = MagicMock()
    mock_df = pd.DataFrame(
        {
            "Close": [close],
            "Open": [close - 5],
            "High": [close + 5],
            "Low": [close - 10],
            "Volume": [1000000],
        },
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


@pytest.mark.asyncio
async def test_capture_portfolio_snapshot_endpoint(auth_client):
    portfolio = await _create_portfolio(auth_client, "Capture Snapshot Portfolio")
    pid = portfolio["id"]

    with patch("yfinance.Ticker", return_value=_mock_yf_ticker(150.0)):
        create_resp = await auth_client.post(f"/portfolios/{pid}/assets", json=_ASSET_PAYLOAD)
        assert create_resp.status_code == 200, create_resp.text

        capture_resp = await auth_client.post(f"/portfolios/{pid}/snapshots/capture")

    assert capture_resp.status_code == 200, capture_resp.text
    data = capture_resp.json()
    assert data["portfolio_id"] == pid
    assert data["summary"]["total_value"] == pytest.approx(1500.0)
    assert data["summary"]["total_cost"] == pytest.approx(1450.0)
    assert data["summary"]["total_profit_loss"] == pytest.approx(50.0)
    assert data["holdings"][0]["symbol"] == "AAPL"
    assert data["holdings"][0]["allocation_percent"] == pytest.approx(100.0)


@pytest.mark.asyncio
async def test_list_portfolio_snapshots_returns_persisted_history(auth_client):
    portfolio = await _create_portfolio(auth_client, "Snapshot History Portfolio")
    pid = portfolio["id"]

    with patch("yfinance.Ticker", return_value=_mock_yf_ticker(150.0)):
        create_resp = await auth_client.post(f"/portfolios/{pid}/assets", json=_ASSET_PAYLOAD)

    assert create_resp.status_code == 200, create_resp.text

    history_resp = await auth_client.get(f"/portfolios/{pid}/snapshots?days=30")
    assert history_resp.status_code == 200, history_resp.text
    data = history_resp.json()
    assert data["portfolio_id"] == pid
    assert len(data["points"]) == 1
    assert data["points"][0]["portfolio_value"] == pytest.approx(1500.0)


@pytest.mark.asyncio
async def test_snapshot_upserts_same_day_after_asset_update(auth_client):
    portfolio = await _create_portfolio(auth_client, "Snapshot Update Portfolio")
    pid = portfolio["id"]
    today = datetime.now(timezone.utc).date().isoformat()

    with patch("yfinance.Ticker", return_value=_mock_yf_ticker(150.0)):
        create_resp = await auth_client.post(f"/portfolios/{pid}/assets", json=_ASSET_PAYLOAD)
    assert create_resp.status_code == 200, create_resp.text
    asset_id = create_resp.json()["id"]

    with patch("yfinance.Ticker", return_value=_mock_yf_ticker(160.0)):
        update_resp = await auth_client.put(
            f"/portfolios/{pid}/assets/{asset_id}",
            json={"quantity": 20.0},
        )
    assert update_resp.status_code == 200, update_resp.text

    detail_resp = await auth_client.get(f"/portfolios/{pid}/snapshots/{today}")
    assert detail_resp.status_code == 200, detail_resp.text
    detail = detail_resp.json()
    assert detail["summary"]["total_value"] == pytest.approx(3200.0)
    assert detail["summary"]["total_cost"] == pytest.approx(2900.0)
    assert detail["summary"]["total_profit_loss"] == pytest.approx(300.0)
    assert detail["holdings"][0]["quantity"] == pytest.approx(20.0)

    history_resp = await auth_client.get(f"/portfolios/{pid}/snapshots?days=30")
    assert history_resp.status_code == 200, history_resp.text
    history = history_resp.json()
    assert len(history["points"]) == 1


@pytest.mark.asyncio
async def test_snapshot_refreshes_to_zero_after_asset_delete(auth_client):
    portfolio = await _create_portfolio(auth_client, "Snapshot Delete Portfolio")
    pid = portfolio["id"]
    today = datetime.now(timezone.utc).date().isoformat()

    with patch("yfinance.Ticker", return_value=_mock_yf_ticker(150.0)):
        create_resp = await auth_client.post(f"/portfolios/{pid}/assets", json=_ASSET_PAYLOAD)
    assert create_resp.status_code == 200, create_resp.text
    asset_id = create_resp.json()["id"]

    delete_resp = await auth_client.delete(f"/portfolios/{pid}/assets/{asset_id}")
    assert delete_resp.status_code == 204, delete_resp.text

    detail_resp = await auth_client.get(f"/portfolios/{pid}/snapshots/{today}")
    assert detail_resp.status_code == 200, detail_resp.text
    detail = detail_resp.json()
    assert detail["summary"]["total_value"] == pytest.approx(0.0)
    assert detail["summary"]["total_cost"] == pytest.approx(0.0)
    assert detail["summary"]["total_profit_loss"] == pytest.approx(0.0)
    assert detail["holdings"] == []


@pytest.mark.asyncio
async def test_compare_portfolio_snapshots_returns_summary_and_holding_deltas(
    auth_client,
    test_db,
):
    portfolio = await _create_portfolio(auth_client, "Snapshot Compare Portfolio")
    pid = portfolio["id"]
    owner_id = portfolio["owner_id"]

    with patch("yfinance.Ticker", return_value=_mock_yf_ticker(150.0)):
        create_resp = await auth_client.post(f"/portfolios/{pid}/assets", json=_ASSET_PAYLOAD)
    assert create_resp.status_code == 200, create_resp.text
    asset_id = create_resp.json()["id"]

    with patch("yfinance.Ticker", return_value=_mock_yf_ticker(150.0)):
        await capture_portfolio_snapshot(
            test_db,
            pid,
            owner_id,
            snapshot_date=date(2026, 3, 30),
        )

    with patch("yfinance.Ticker", return_value=_mock_yf_ticker(160.0)):
        update_resp = await auth_client.put(
            f"/portfolios/{pid}/assets/{asset_id}",
            json={"quantity": 20.0},
        )
    assert update_resp.status_code == 200, update_resp.text

    with patch("yfinance.Ticker", return_value=_mock_yf_ticker(160.0)):
        await capture_portfolio_snapshot(
            test_db,
            pid,
            owner_id,
            snapshot_date=date(2026, 3, 31),
        )

    compare_resp = await auth_client.get(
        f"/portfolios/{pid}/snapshots/compare?current_date=2026-03-31&previous_date=2026-03-30"
    )
    assert compare_resp.status_code == 200, compare_resp.text
    data = compare_resp.json()
    assert data["portfolio_id"] == pid
    assert data["current_as_of"] == "2026-03-31"
    assert data["previous_as_of"] == "2026-03-30"
    assert data["summary"]["value_change"] == pytest.approx(1700.0)
    assert data["holdings"][0]["symbol"] == "AAPL"
    assert data["holdings"][0]["status"] == "changed"
    assert data["holdings"][0]["value_change"] == pytest.approx(1700.0)
