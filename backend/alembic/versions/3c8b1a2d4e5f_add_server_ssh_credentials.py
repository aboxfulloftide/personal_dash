"""Add SSH credentials to servers

Revision ID: 3c8b1a2d4e5f
Revises: 2f7a9c1d3b4e
Create Date: 2026-03-13
"""
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "3c8b1a2d4e5f"
down_revision: Union[str, None] = "2f7a9c1d3b4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("servers", sa.Column("ssh_host", sa.String(length=255), nullable=True))
    op.add_column("servers", sa.Column("ssh_port", sa.Integer(), server_default="22", nullable=True))
    op.add_column("servers", sa.Column("ssh_user", sa.String(length=100), server_default="root", nullable=True))
    op.add_column("servers", sa.Column("ssh_password_enc", sa.Text(), nullable=True))
    op.add_column("servers", sa.Column("ssh_key", sa.Text(), nullable=True))
    op.add_column("servers", sa.Column("sudo_password_enc", sa.Text(), nullable=True))

    # Remove defaults after backfill
    op.alter_column("servers", "ssh_port", server_default=None)
    op.alter_column("servers", "ssh_user", server_default=None)


def downgrade() -> None:
    op.drop_column("servers", "sudo_password_enc")
    op.drop_column("servers", "ssh_key")
    op.drop_column("servers", "ssh_password_enc")
    op.drop_column("servers", "ssh_user")
    op.drop_column("servers", "ssh_port")
    op.drop_column("servers", "ssh_host")
