"""add user auth fields (full_name, is_active)

Revision ID: e8f12a34b5c6
Revises: c9a184e12f01
Create Date: 2026-09-08 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8f12a34b5c6'
down_revision: Union[str, Sequence[str], None] = 'c9a184e12f01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('full_name', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'full_name')
