"""add_dismissed_to_packages

Revision ID: 1823f4b0495f
Revises: 61be8e991af1
Create Date: 2026-02-07 15:11:41.038782

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1823f4b0495f'
down_revision: Union[str, Sequence[str], None] = '61be8e991af1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add dismissed and dismissed_at columns to packages table
    op.add_column('packages', sa.Column('dismissed', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('packages', sa.Column('dismissed_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove dismissed columns from packages table
    op.drop_column('packages', 'dismissed_at')
    op.drop_column('packages', 'dismissed')
