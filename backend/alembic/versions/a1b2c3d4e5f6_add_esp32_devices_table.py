"""Add esp32_devices table

Revision ID: a1b2c3d4e5f6
Revises: f4g5h6i7j8k9
Create Date: 2026-03-18
"""
from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, tuple] = ('f4g5h6i7j8k9', '3c8b1a2d4e5f')
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "esp32_devices",
        sa.Column("id",           sa.Integer(),    primary_key=True, index=True),
        sa.Column("user_id",      sa.Integer(),    sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scanner_host", sa.String(64),   nullable=False),
        sa.Column("display_name", sa.String(100),  nullable=False),
        sa.Column("created_at",   sa.DateTime(),   server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("esp32_devices")
