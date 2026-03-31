import argparse
import asyncio
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import async_session_factory
from .models import Portfolio, PortfolioSnapshot
from .portfolio_snapshots import capture_portfolio_snapshot

logger = logging.getLogger(__name__)


@dataclass
class SnapshotJobResult:
    """Summary of a portfolio snapshot job run."""

    snapshot_date: date
    portfolios_seen: int = 0
    snapshots_created: int = 0
    snapshots_skipped: int = 0
    failures: int = 0


async def capture_missing_snapshots_for_date(
    db: AsyncSession,
    snapshot_date: date,
) -> SnapshotJobResult:
    """Capture the snapshot for every portfolio that does not already have one."""

    result = SnapshotJobResult(snapshot_date=snapshot_date)
    portfolios = (
        await db.execute(select(Portfolio).order_by(Portfolio.id.asc()))
    ).scalars().all()
    result.portfolios_seen = len(portfolios)

    for portfolio in portfolios:
        existing_snapshot = (
            await db.execute(
                select(PortfolioSnapshot.id)
                .where(PortfolioSnapshot.portfolio_id == portfolio.id)
                .where(PortfolioSnapshot.snapshot_date == snapshot_date)
                .limit(1)
            )
        ).scalar_one_or_none()

        if existing_snapshot is not None:
            result.snapshots_skipped += 1
            continue

        try:
            snapshot = await capture_portfolio_snapshot(
                db,
                int(portfolio.id),
                int(portfolio.owner_id),
                snapshot_date=snapshot_date,
            )
            if snapshot is None:
                result.failures += 1
                logger.warning(
                    "Daily snapshot job skipped portfolio %s because it could not be loaded",
                    portfolio.id,
                )
                continue

            result.snapshots_created += 1
        except Exception as exc:
            await db.rollback()
            result.failures += 1
            logger.exception(
                "Daily snapshot job failed for portfolio %s on %s: %s",
                portfolio.id,
                snapshot_date,
                exc,
            )

    logger.info(
        "Daily snapshot job finished for %s: seen=%s created=%s skipped=%s failures=%s",
        snapshot_date,
        result.portfolios_seen,
        result.snapshots_created,
        result.snapshots_skipped,
        result.failures,
    )
    return result


async def run_snapshot_job_for_date(snapshot_date: date) -> SnapshotJobResult:
    """Run the daily capture job in its own database session."""

    async with async_session_factory() as db:
        return await capture_missing_snapshots_for_date(db, snapshot_date)


async def capture_missing_snapshots_for_range(
    db: AsyncSession,
    start_date: date,
    end_date: date,
) -> list[SnapshotJobResult]:
    """Backfill missing snapshots across an inclusive date range in one session."""

    if end_date < start_date:
        raise ValueError("end_date must be greater than or equal to start_date")

    results: list[SnapshotJobResult] = []
    current_date = start_date
    while current_date <= end_date:
        results.append(await capture_missing_snapshots_for_date(db, current_date))
        current_date += timedelta(days=1)

    return results


async def run_snapshot_backfill(
    start_date: date,
    end_date: date,
) -> list[SnapshotJobResult]:
    """Backfill missing snapshots across an inclusive date range."""

    async with async_session_factory() as db:
        return await capture_missing_snapshots_for_range(db, start_date, end_date)


async def run_daily_snapshot_scheduler(stop_event: asyncio.Event) -> None:
    """Run a lightweight scheduler loop for a single dedicated process."""

    last_attempted_date: Optional[date] = None

    while not stop_event.is_set():
        now = datetime.now(timezone.utc)
        target_today = now.replace(
            hour=settings.snapshot_capture_hour_utc,
            minute=settings.snapshot_capture_minute_utc,
            second=0,
            microsecond=0,
        )
        should_run = (
            now >= target_today and last_attempted_date != now.date()
        )

        if should_run:
            logger.info(
                "Running scheduled daily snapshot capture for %s at %s UTC",
                now.date(),
                now.isoformat(),
            )
            await run_snapshot_job_for_date(now.date())
            last_attempted_date = now.date()
            continue

        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=max(settings.snapshot_scheduler_poll_seconds, 30),
            )
        except TimeoutError:
            continue


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Portfolio snapshot job runner")
    parser.add_argument(
        "--date",
        dest="snapshot_date",
        help="Capture missing snapshots for a single YYYY-MM-DD date. Defaults to today (UTC).",
    )
    parser.add_argument(
        "--backfill-start",
        dest="backfill_start",
        help="Inclusive start date for a backfill run (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--backfill-end",
        dest="backfill_end",
        help="Inclusive end date for a backfill run (YYYY-MM-DD). Defaults to today when --backfill-start is set.",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run the lightweight scheduler loop for a dedicated process.",
    )
    return parser.parse_args()


def _parse_date_arg(raw_value: Optional[str], default_value: Optional[date] = None) -> Optional[date]:
    if raw_value is None:
        return default_value
    return date.fromisoformat(raw_value)


async def _run_from_args(args: argparse.Namespace) -> None:
    if args.daemon:
        stop_event = asyncio.Event()
        try:
            await run_daily_snapshot_scheduler(stop_event)
        except asyncio.CancelledError:
            logger.info("Daily snapshot scheduler cancelled")
            raise
        return

    if args.backfill_start:
        start_date = _parse_date_arg(args.backfill_start)
        end_date = _parse_date_arg(
            args.backfill_end,
            datetime.now(timezone.utc).date(),
        )
        await run_snapshot_backfill(start_date, end_date)
        return

    snapshot_date = _parse_date_arg(
        args.snapshot_date,
        datetime.now(timezone.utc).date(),
    )
    await run_snapshot_job_for_date(snapshot_date)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO if not settings.debug else logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(_run_from_args(_parse_args()))


if __name__ == "__main__":
    main()
