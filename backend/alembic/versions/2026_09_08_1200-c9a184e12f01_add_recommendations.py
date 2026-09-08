"""add recommendations and recommendation_items tables

Revision ID: c9a184e12f01
Revises: b1ec38fec3ea
Create Date: 2026-09-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9a184e12f01'
down_revision: Union[str, Sequence[str], None] = 'b1ec38fec3ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create recommendations table
    op.create_table(
        'recommendations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('risk_category', sa.String(length=50), nullable=False),
        sa.Column('risk_score', sa.Integer(), nullable=False),
        sa.Column('monthly_capacity', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('target_equity_pct', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('target_debt_pct', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('target_gold_pct', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('target_cash_pct', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('total_monthly_sip', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('total_lump_sum', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('is_valid', sa.Boolean(), nullable=False),
        sa.Column('validation_details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recommendations_id'), 'recommendations', ['id'], unique=False)
    op.create_index(op.f('ix_recommendations_user_id'), 'recommendations', ['user_id'], unique=False)

    # 2. Create recommendation_items table
    op.create_table(
        'recommendation_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('recommendation_id', sa.Integer(), nullable=False),
        sa.Column('financial_product_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('product_type', sa.String(length=50), nullable=False),
        sa.Column('asset_class', sa.String(length=50), nullable=False),
        sa.Column('risk_level', sa.String(length=50), nullable=False),
        sa.Column('suitability_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('allocation_percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('monthly_sip_amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('lump_sum_amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('selection_reasons', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['financial_product_id'], ['financial_products.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['recommendation_id'], ['recommendations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recommendation_items_id'), 'recommendation_items', ['id'], unique=False)
    op.create_index(op.f('ix_recommendation_items_recommendation_id'), 'recommendation_items', ['recommendation_id'], unique=False)
    op.create_index(op.f('ix_recommendation_items_financial_product_id'), 'recommendation_items', ['financial_product_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_recommendation_items_financial_product_id'), table_name='recommendation_items')
    op.drop_index(op.f('ix_recommendation_items_recommendation_id'), table_name='recommendation_items')
    op.drop_index(op.f('ix_recommendation_items_id'), table_name='recommendation_items')
    op.drop_table('recommendation_items')
    op.drop_index(op.f('ix_recommendations_user_id'), table_name='recommendations')
    op.drop_index(op.f('ix_recommendations_id'), table_name='recommendations')
    op.drop_table('recommendations')
