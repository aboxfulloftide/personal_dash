"""add_system_settings_table

Revision ID: a1b2c3d4e5f6
Revises: 15edd2971d30
Create Date: 2026-05-16 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'f7e8d9c0b1a2'
down_revision: Union[str, Sequence[str], None] = '15edd2971d30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'system_settings',
        sa.Column('key', sa.String(100), primary_key=True),
        sa.Column('value', sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('system_settings')
