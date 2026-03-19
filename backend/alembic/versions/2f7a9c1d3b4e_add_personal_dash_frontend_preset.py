"""Add Personal Dash frontend process preset

Revision ID: 2f7a9c1d3b4e
Revises: e2f3a4b5c6d7
Create Date: 2026-03-13
"""
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "2f7a9c1d3b4e"
down_revision: Union[str, None] = "e2f3a4b5c6d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO process_presets (category, name, pattern, hint, sort_order, is_builtin)
            SELECT :category, :name, :pattern, :hint, :sort_order, :is_builtin
            WHERE NOT EXISTS (
                SELECT 1 FROM process_presets
                WHERE category = :category AND name = :name AND pattern = :pattern
            )
            """
        ).bindparams(
            category="Personal Dash",
            name="Dash Frontend",
            pattern="personal-dash-frontend.service",
            hint="Frontend web UI service (personal-dash-frontend.service)",
            sort_order=30,
            is_builtin=True,
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM process_presets
            WHERE category = :category AND name = :name AND pattern = :pattern
            """
        ).bindparams(
            category="Personal Dash",
            name="Dash Frontend",
            pattern="personal-dash-frontend.service",
        )
    )
