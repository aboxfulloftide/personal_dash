"""Add apps and user_app_access tables for central auth

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-03-22
"""
from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "apps",
        sa.Column("id",           sa.Integer(),    primary_key=True, index=True),
        sa.Column("slug",         sa.String(64),   nullable=False, unique=True, index=True),
        sa.Column("display_name", sa.String(100),  nullable=False),
        sa.Column("description",  sa.String(255)),
        sa.Column("is_active",    sa.Boolean(),    nullable=False, server_default="1"),
        sa.Column("created_at",   sa.DateTime(),   server_default=sa.func.now()),
    )

    op.create_table(
        "user_app_access",
        sa.Column("id",         sa.Integer(),  primary_key=True, index=True),
        sa.Column("user_id",    sa.Integer(),  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("app_id",     sa.Integer(),  sa.ForeignKey("apps.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("level",      sa.String(16), nullable=False, server_default="viewer"),
        sa.Column("granted_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "app_id", name="uq_user_app"),
    )

    # Seed the personal_dash app
    op.execute(
        "INSERT INTO apps (slug, display_name, description, is_active) "
        "VALUES ('personal_dash', 'Personal Dash', 'Main home dashboard', 1)"
    )

    # Grant existing active users access to personal_dash
    # Admins get 'admin', everyone else gets 'user'
    op.execute("""
        INSERT INTO user_app_access (user_id, app_id, level)
        SELECT u.id, a.id,
               CASE WHEN u.is_admin = 1 THEN 'admin' ELSE 'user' END
        FROM users u
        CROSS JOIN apps a
        WHERE a.slug = 'personal_dash'
          AND u.is_active = 1
    """)


def downgrade() -> None:
    op.drop_table("user_app_access")
    op.drop_table("apps")
