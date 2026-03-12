"""Add router and router_poll_results tables

Revision ID: f4g5h6i7j8k9
Revises: e2f3a4b5c6d7
Create Date: 2026-03-11
"""
from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = 'f4g5h6i7j8k9'
down_revision: Union[str, None] = 'e2f3a4b5c6d7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "routers",
        sa.Column("id",               sa.Integer(),     primary_key=True, index=True),
        sa.Column("user_id",          sa.Integer(),     sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name",             sa.String(100),   nullable=False),
        sa.Column("hostname",         sa.String(255),   nullable=False),
        sa.Column("ssh_port",         sa.Integer(),     default=22),
        sa.Column("ssh_user",         sa.String(100),   default="root"),
        sa.Column("ssh_password_enc", sa.Text()),
        sa.Column("ssh_key",          sa.Text()),
        sa.Column("poll_interval",    sa.Integer(),     default=60),
        sa.Column("script",           sa.Text()),
        sa.Column("is_online",        sa.Boolean(),     default=False),
        sa.Column("ping_ms",          sa.Float()),
        sa.Column("last_seen",        sa.DateTime()),
        sa.Column("last_polled",      sa.DateTime()),
        sa.Column("created_at",       sa.DateTime(),    server_default=sa.func.now()),
    )

    op.create_table(
        "router_poll_results",
        sa.Column("id",            sa.BigInteger(),  primary_key=True, index=True),
        sa.Column("router_id",     sa.Integer(),     sa.ForeignKey("routers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("is_online",     sa.Boolean(),     default=False),
        sa.Column("ping_ms",       sa.Float()),
        sa.Column("script_output", sa.Text()),
        sa.Column("recorded_at",   sa.DateTime(),    server_default=sa.func.now(), index=True),
    )


def downgrade() -> None:
    op.drop_table("router_poll_results")
    op.drop_table("routers")
