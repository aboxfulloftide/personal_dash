"""add_network_target_index

Revision ID: d0481e118d14
Revises: e5a7ad1a0d62
Create Date: 2026-02-13 09:27:31.482274

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0481e118d14'
down_revision: Union[str, Sequence[str], None] = 'e5a7ad1a0d62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add composite index for efficient per-target historical queries
    op.create_index(
        'idx_ping_user_target_timestamp',
        'network_ping_results',
        ['user_id', 'target_host', 'timestamp'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the composite index
    op.drop_index('idx_ping_user_target_timestamp', table_name='network_ping_results')
