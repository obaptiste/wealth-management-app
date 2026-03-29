"""add watchlist_items table

Revision ID: a1b2c3d4e5f6
Revises: f9d3e2c1a8b4
Create Date: 2026-03-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f9d3e2c1a8b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'watchlist_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_watchlist_items_id'), 'watchlist_items', ['id'], unique=False)
    # Unique per-user per-symbol to prevent duplicates
    op.create_index('idx_watchlist_user_symbol', 'watchlist_items', ['user_id', 'symbol'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_watchlist_user_symbol', table_name='watchlist_items')
    op.drop_index(op.f('ix_watchlist_items_id'), table_name='watchlist_items')
    op.drop_table('watchlist_items')
