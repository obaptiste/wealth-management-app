"""add portfolio snapshot tables

Revision ID: c4d5e6f7a8b9
Revises: a1b2c3d4e5f6
Create Date: 2026-03-31 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "portfolio_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("total_value", sa.Float(), nullable=False),
        sa.Column("total_cost", sa.Float(), nullable=False),
        sa.Column("total_profit_loss", sa.Float(), nullable=False),
        sa.Column("total_profit_loss_percent", sa.Float(), nullable=False),
        sa.Column("asset_count", sa.Integer(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_portfolio_snapshots_id"), "portfolio_snapshots", ["id"], unique=False)
    op.create_index(
        "idx_portfolio_snapshot_portfolio_date",
        "portfolio_snapshots",
        ["portfolio_id", "snapshot_date"],
        unique=True,
    )

    op.create_table(
        "portfolio_snapshot_holdings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("portfolio_snapshot_id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=True),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("current_value", sa.Float(), nullable=False),
        sa.Column("allocation_percent", sa.Float(), nullable=False),
        sa.Column("total_cost", sa.Float(), nullable=False),
        sa.Column("profit_loss", sa.Float(), nullable=False),
        sa.Column("profit_loss_percent", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["portfolio_snapshot_id"], ["portfolio_snapshots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_portfolio_snapshot_holdings_id"),
        "portfolio_snapshot_holdings",
        ["id"],
        unique=False,
    )
    op.create_index(
        "idx_snapshot_holding_snapshot_symbol",
        "portfolio_snapshot_holdings",
        ["portfolio_snapshot_id", "symbol"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_snapshot_holding_snapshot_symbol", table_name="portfolio_snapshot_holdings")
    op.drop_index(op.f("ix_portfolio_snapshot_holdings_id"), table_name="portfolio_snapshot_holdings")
    op.drop_table("portfolio_snapshot_holdings")

    op.drop_index("idx_portfolio_snapshot_portfolio_date", table_name="portfolio_snapshots")
    op.drop_index(op.f("ix_portfolio_snapshots_id"), table_name="portfolio_snapshots")
    op.drop_table("portfolio_snapshots")
