"""add_tracking_url_to_packages

Revision ID: cdb7ce79815d
Revises: 509cdb398a2d
Create Date: 2026-02-12 10:50:35.223914

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cdb7ce79815d'
down_revision: Union[str, Sequence[str], None] = '509cdb398a2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('packages', sa.Column('tracking_url', sa.Text, nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('packages', 'tracking_url')
