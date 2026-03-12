"""Add temperatures column to server_metrics

Revision ID: d7e8f9a0b1c2
Revises: c4d5e6f7a890
Create Date: 2026-03-11
"""
from typing import Union, Sequence
from alembic import op
import sqlalchemy as sa

revision: str = 'd7e8f9a0b1c2'
down_revision: Union[str, None] = 'c4d5e6f7a890'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('server_metrics',
        sa.Column('temperatures_json', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('server_metrics', 'temperatures_json')
