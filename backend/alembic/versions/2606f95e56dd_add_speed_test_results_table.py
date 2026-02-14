"""add_speed_test_results_table

Revision ID: 2606f95e56dd
Revises: d0481e118d14
Create Date: 2026-02-13 20:24:12.747557

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2606f95e56dd'
down_revision: Union[str, Sequence[str], None] = 'd0481e118d14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'speed_test_results',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('download_mbps', sa.Float(), nullable=True),
        sa.Column('upload_mbps', sa.Float(), nullable=True),
        sa.Column('ping_ms', sa.Float(), nullable=True),
        sa.Column('server_id', sa.String(length=50), nullable=True),
        sa.Column('server_name', sa.String(length=255), nullable=True),
        sa.Column('server_location', sa.String(length=255), nullable=True),
        sa.Column('server_sponsor', sa.String(length=255), nullable=True),
        sa.Column('test_duration_seconds', sa.Float(), nullable=True),
        sa.Column('is_successful', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.String(length=500), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_speedtest_user_timestamp', 'speed_test_results', ['user_id', 'timestamp'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_speedtest_user_timestamp', table_name='speed_test_results')
    op.drop_table('speed_test_results')
