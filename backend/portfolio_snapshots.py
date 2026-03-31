import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import yfinance as yf
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    Asset,
    AssetPriceHistory,
    Portfolio,
    PortfolioSnapshot,
    PortfolioSnapshotHolding,
)
from .schemas import (
    HistoricalSnapshotPoint,
    PortfolioSnapshotHistoryResponse,
    PortfolioSnapshotHoldingOut,
    PortfolioSnapshotOut,
    PortfolioSummary,
)

logger = logging.getLogger(__name__)


@dataclass
class ResolvedSnapshotHolding:
    """Normalized holding values ready to persist into a snapshot row."""

    asset_id: Optional[int]
    symbol: str
    quantity: float
    price: float
    current_value: float
    total_cost: float
    profit_loss: float
    profit_loss_percent: float


async def get_owned_portfolio(
    db: AsyncSession,
    portfolio_id: int,
    owner_id: int,
    *,
    include_assets: bool = False,
) -> Optional[Portfolio]:
    """Load a portfolio owned by the current user."""

    query = select(Portfolio).where(Portfolio.id == portfolio_id).where(Portfolio.owner_id == owner_id)
    if include_assets:
        query = query.options(selectinload(Portfolio.assets))

    result = await db.execute(query)
    return result.scalars().first()


async def resolve_asset_price(
    db: AsyncSession,
    asset: Asset,
    captured_at: datetime,
) -> float:
    """Resolve the best available price for a snapshot.

    Order of preference:
    1. Fresh yfinance quote and persist it into AssetPriceHistory
    2. Most recent stored AssetPriceHistory row
    3. Purchase price
    """

    try:
        stock = yf.Ticker(str(asset.symbol))
        history = stock.history(period="1d")
        latest_close = history["Close"].iloc[-1]
        latest_price = float(latest_close)

        db.add(
            AssetPriceHistory(
                asset_id=int(asset.id),
                price=latest_price,
                timestamp=captured_at,
            )
        )
        return latest_price
    except Exception as exc:
        logger.warning("Could not fetch live price for %s during snapshot capture: %s", asset.symbol, exc)

    result = await db.execute(
        select(AssetPriceHistory.price)
        .where(AssetPriceHistory.asset_id == asset.id)
        .order_by(AssetPriceHistory.timestamp.desc())
        .limit(1)
    )
    latest_stored_price = result.scalar_one_or_none()
    if latest_stored_price is not None:
        return float(latest_stored_price)

    logger.warning(
        "Snapshot capture for %s fell back to purchase price because no historical price exists",
        asset.symbol,
    )
    return float(asset.purchase_price)


def build_snapshot_response(snapshot: PortfolioSnapshot) -> PortfolioSnapshotOut:
    """Serialize an ORM snapshot row into the API response shape."""

    ordered_holdings = sorted(
        snapshot.holdings,
        key=lambda holding: holding.current_value,
        reverse=True,
    )
    return PortfolioSnapshotOut(
        portfolio_id=int(snapshot.portfolio_id),
        as_of=snapshot.snapshot_date,
        captured_at=snapshot.captured_at,
        summary=PortfolioSummary(
            total_value=float(snapshot.total_value),
            total_cost=float(snapshot.total_cost),
            total_profit_loss=float(snapshot.total_profit_loss),
            total_profit_loss_percent=float(snapshot.total_profit_loss_percent),
            last_updated=snapshot.captured_at,
        ),
        holdings=[
            PortfolioSnapshotHoldingOut(
                asset_id=holding.asset_id,
                symbol=str(holding.symbol),
                quantity=float(holding.quantity),
                price=float(holding.price),
                current_value=float(holding.current_value),
                allocation_percent=float(holding.allocation_percent),
                total_cost=float(holding.total_cost),
                profit_loss=float(holding.profit_loss),
                profit_loss_percent=float(holding.profit_loss_percent),
            )
            for holding in ordered_holdings
        ],
    )


async def capture_portfolio_snapshot(
    db: AsyncSession,
    portfolio_id: int,
    owner_id: int,
    *,
    snapshot_date: Optional[date] = None,
) -> Optional[PortfolioSnapshotOut]:
    """Capture or refresh the daily snapshot for a portfolio."""

    portfolio = await get_owned_portfolio(db, portfolio_id, owner_id, include_assets=True)
    if portfolio is None:
        return None

    target_date = snapshot_date or datetime.now(timezone.utc).date()
    captured_at = datetime.now(timezone.utc)

    resolved_holdings: list[ResolvedSnapshotHolding] = []
    total_cost = 0.0
    total_value = 0.0

    for asset in portfolio.assets:
        price = await resolve_asset_price(db, asset, captured_at)
        quantity = float(asset.quantity)
        total_asset_cost = quantity * float(asset.purchase_price)
        current_value = quantity * price
        profit_loss = current_value - total_asset_cost
        profit_loss_percent = (profit_loss / total_asset_cost) * 100 if total_asset_cost > 0 else 0.0

        resolved_holdings.append(
            ResolvedSnapshotHolding(
                asset_id=int(asset.id),
                symbol=str(asset.symbol),
                quantity=quantity,
                price=price,
                current_value=current_value,
                total_cost=total_asset_cost,
                profit_loss=profit_loss,
                profit_loss_percent=profit_loss_percent,
            )
        )
        total_cost += total_asset_cost
        total_value += current_value

    total_profit_loss = total_value - total_cost
    total_profit_loss_percent = (total_profit_loss / total_cost) * 100 if total_cost > 0 else 0.0

    result = await db.execute(
        select(PortfolioSnapshot)
        .where(PortfolioSnapshot.portfolio_id == portfolio_id)
        .where(PortfolioSnapshot.snapshot_date == target_date)
        .limit(1)
    )
    snapshot = result.scalars().first()

    if snapshot is None:
        snapshot = PortfolioSnapshot(
            portfolio_id=portfolio_id,
            snapshot_date=target_date,
            total_value=total_value,
            total_cost=total_cost,
            total_profit_loss=total_profit_loss,
            total_profit_loss_percent=total_profit_loss_percent,
            asset_count=len(resolved_holdings),
            captured_at=captured_at,
        )
        db.add(snapshot)
        await db.flush()
    else:
        snapshot.total_value = total_value
        snapshot.total_cost = total_cost
        snapshot.total_profit_loss = total_profit_loss
        snapshot.total_profit_loss_percent = total_profit_loss_percent
        snapshot.asset_count = len(resolved_holdings)
        snapshot.captured_at = captured_at
        await db.flush()
        await db.execute(
            delete(PortfolioSnapshotHolding).where(
                PortfolioSnapshotHolding.portfolio_snapshot_id == snapshot.id
            )
        )

    for holding in resolved_holdings:
        allocation_percent = (holding.current_value / total_value) * 100 if total_value > 0 else 0.0
        db.add(
            PortfolioSnapshotHolding(
                portfolio_snapshot_id=int(snapshot.id),
                asset_id=holding.asset_id,
                symbol=holding.symbol,
                quantity=holding.quantity,
                price=holding.price,
                current_value=holding.current_value,
                allocation_percent=allocation_percent,
                total_cost=holding.total_cost,
                profit_loss=holding.profit_loss,
                profit_loss_percent=holding.profit_loss_percent,
            )
        )

    await db.commit()

    result = await db.execute(
        select(PortfolioSnapshot)
        .options(selectinload(PortfolioSnapshot.holdings))
        .where(PortfolioSnapshot.id == snapshot.id)
    )
    saved_snapshot = result.scalars().first()
    if saved_snapshot is None:
        return None

    return build_snapshot_response(saved_snapshot)


async def get_portfolio_snapshot_history(
    db: AsyncSession,
    portfolio_id: int,
    owner_id: int,
    *,
    days: int = 30,
) -> Optional[PortfolioSnapshotHistoryResponse]:
    """Return persisted daily portfolio value history."""

    portfolio = await get_owned_portfolio(db, portfolio_id, owner_id)
    if portfolio is None:
        return None

    to_date = datetime.now(timezone.utc).date()
    from_date = to_date - timedelta(days=max(days - 1, 0))

    result = await db.execute(
        select(PortfolioSnapshot)
        .where(PortfolioSnapshot.portfolio_id == portfolio_id)
        .where(PortfolioSnapshot.snapshot_date >= from_date)
        .where(PortfolioSnapshot.snapshot_date <= to_date)
        .order_by(PortfolioSnapshot.snapshot_date.asc())
    )
    snapshots = result.scalars().all()

    return PortfolioSnapshotHistoryResponse(
        portfolio_id=portfolio_id,
        from_date=from_date,
        to_date=to_date,
        points=[
            HistoricalSnapshotPoint(
                as_of=snapshot.snapshot_date,
                portfolio_value=float(snapshot.total_value),
            )
            for snapshot in snapshots
        ],
    )


async def get_portfolio_snapshot_by_date(
    db: AsyncSession,
    portfolio_id: int,
    owner_id: int,
    snapshot_date: date,
) -> Optional[PortfolioSnapshotOut]:
    """Return a single persisted snapshot for a portfolio and date."""

    portfolio = await get_owned_portfolio(db, portfolio_id, owner_id)
    if portfolio is None:
        return None

    result = await db.execute(
        select(PortfolioSnapshot)
        .options(selectinload(PortfolioSnapshot.holdings))
        .where(PortfolioSnapshot.portfolio_id == portfolio_id)
        .where(PortfolioSnapshot.snapshot_date == snapshot_date)
        .limit(1)
    )
    snapshot = result.scalars().first()
    if snapshot is None:
        return None

    return build_snapshot_response(snapshot)
