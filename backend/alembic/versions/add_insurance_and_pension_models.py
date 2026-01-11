"""add insurance and pension models

Revision ID: f9d3e2c1a8b4
Revises: e437b7899491
Create Date: 2026-01-11 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9d3e2c1a8b4'
down_revision: Union[str, None] = 'e437b7899491'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create insurance_products table
    op.create_table(
        'insurance_products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('coverage_amount', sa.Float(), nullable=False),
        sa.Column('monthly_premium', sa.Float(), nullable=False),
        sa.Column('min_age', sa.Integer(), nullable=False),
        sa.Column('max_age', sa.Integer(), nullable=False),
        sa.Column('min_income', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_insurance_products_id'), 'insurance_products', ['id'], unique=False)

    # Create pension_plans table
    op.create_table(
        'pension_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('current_age', sa.Integer(), nullable=False),
        sa.Column('target_retirement_age', sa.Integer(), nullable=False),
        sa.Column('monthly_contribution', sa.Float(), nullable=False),
        sa.Column('current_savings', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('expected_return', sa.Float(), nullable=False),
        sa.Column('projected_value', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pension_plans_id'), 'pension_plans', ['id'], unique=False)
    op.create_index('idx_pension_user', 'pension_plans', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop pension_plans table
    op.drop_index('idx_pension_user', table_name='pension_plans')
    op.drop_index(op.f('ix_pension_plans_id'), table_name='pension_plans')
    op.drop_table('pension_plans')

    # Drop insurance_products table
    op.drop_index(op.f('ix_insurance_products_id'), table_name='insurance_products')
    op.drop_table('insurance_products')
