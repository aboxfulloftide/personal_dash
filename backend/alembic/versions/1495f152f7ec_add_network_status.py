"""add_network_status

Revision ID: 1495f152f7ec
Revises: ccd0cec1e458
Create Date: 2026-02-09 21:26:24.095286

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1495f152f7ec'
down_revision: Union[str, Sequence[str], None] = 'ccd0cec1e458'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'network_status',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('isp', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_network_status_user_timestamp', 'network_status', ['user_id', 'timestamp'])

    op.create_table(
        'network_ping_results',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('target_host', sa.String(length=255), nullable=False),
        sa.Column('target_name', sa.String(length=100), nullable=True),
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('jitter_ms', sa.Float(), nullable=True),
        sa.Column('packet_loss_pct', sa.Float(), nullable=True),
        sa.Column('is_reachable', sa.Boolean(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ping_user_timestamp', 'network_ping_results', ['user_id', 'timestamp'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_ping_user_timestamp', table_name='network_ping_results')
    op.drop_table('network_ping_results')
    op.drop_index('idx_network_status_user_timestamp', table_name='network_status')
    op.drop_table('network_status')
