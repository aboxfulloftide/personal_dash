"""Add acknowledged fields to custom_widget_data

Revision ID: b8e2d4f7a01c
Revises: a3f7c9e12d45
Create Date: 2026-02-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b8e2d4f7a01c'
down_revision: Union[str, Sequence[str], None] = 'a3f7c9e12d45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('custom_widget_data', sa.Column('acknowledged', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('custom_widget_data', sa.Column('acknowledged_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('custom_widget_data', 'acknowledged_at')
    op.drop_column('custom_widget_data', 'acknowledged')
