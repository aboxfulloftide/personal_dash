"""add_acknowledged_reminder_status

Revision ID: c4d5e6f7a890
Revises: f3a9c2d8e1b4
Create Date: 2026-02-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7a890'
down_revision: Union[str, None] = 'f3a9c2d8e1b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert existing 'dismissed' instances to 'acknowledged'
    # since the old 'dismissed' was equivalent to the new 'acknowledged' (completed/hidden)
    op.execute(
        "UPDATE reminder_instances SET status = 'acknowledged' WHERE status = 'dismissed'"
    )


def downgrade() -> None:
    # Convert 'acknowledged' back to 'dismissed'
    op.execute(
        "UPDATE reminder_instances SET status = 'dismissed' WHERE status = 'acknowledged'"
    )
