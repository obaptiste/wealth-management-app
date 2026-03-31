"""
Tests for the scheduled and backfill portfolio snapshot job helpers.
"""
from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from sqlalchemy import func, select

from backend.models import PortfolioSnapshot
from backend.snapshot_jobs import (
    capture_missing_snapshots_for_date,
    capture_missing_snapshots_for_range,
)


async def _create_portfolio(auth_client, name="Snapshot Job Portfolio"):
    resp = await auth_client.post(
        "/portfolios",
        json={"name": name, "description": "for snapshot job tests"},
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
async def test_daily_snapshot_job_skips_existing_snapshots(auth_client, test_db):
    portfolio = await _create_portfolio(auth_client, "Daily Snapshot Job Portfolio")
    pid = portfolio["id"]

    with patch("yfinance.Ticker", return_value=_mock_yf_ticker(150.0)):
        create_resp = await auth_client.post(f"/portfolios/{pid}/assets", json=_ASSET_PAYLOAD)
        assert create_resp.status_code == 200, create_resp.text

    snapshot_date = date(2026, 3, 30)

    with patch("yfinance.Ticker", return_value=_mock_yf_ticker(155.0)):
        first_run = await capture_missing_snapshots_for_date(test_db, snapshot_date)
        second_run = await capture_missing_snapshots_for_date(test_db, snapshot_date)

    assert first_run.portfolios_seen >= 1
    assert first_run.snapshots_created == 1
    assert first_run.snapshots_skipped == 0
    assert second_run.snapshots_created == 0
    assert second_run.snapshots_skipped >= 1

    snapshot_count = (
        await test_db.execute(
            select(func.count())
            .select_from(PortfolioSnapshot)
            .where(PortfolioSnapshot.snapshot_date == snapshot_date)
        )
    ).scalar_one()
    assert snapshot_count == 1


@pytest.mark.asyncio
async def test_snapshot_job_backfills_missing_date_range(auth_client, test_db):
    portfolio = await _create_portfolio(auth_client, "Snapshot Backfill Portfolio")
    pid = portfolio["id"]

    with patch("yfinance.Ticker", return_value=_mock_yf_ticker(150.0)):
        create_resp = await auth_client.post(f"/portfolios/{pid}/assets", json=_ASSET_PAYLOAD)
        assert create_resp.status_code == 200, create_resp.text

    with patch("yfinance.Ticker", return_value=_mock_yf_ticker(152.0)):
        results = await capture_missing_snapshots_for_range(
            test_db,
            date(2026, 3, 27),
            date(2026, 3, 29),
        )

    assert len(results) == 3
    assert sum(result.snapshots_created for result in results) == 3

    snapshot_count = (
        await test_db.execute(
            select(func.count())
            .select_from(PortfolioSnapshot)
            .where(PortfolioSnapshot.snapshot_date >= date(2026, 3, 27))
            .where(PortfolioSnapshot.snapshot_date <= date(2026, 3, 29))
        )
    ).scalar_one()
    assert snapshot_count == 3
