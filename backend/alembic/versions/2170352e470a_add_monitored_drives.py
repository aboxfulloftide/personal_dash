"""add_monitored_drives

Revision ID: 2170352e470a
Revises: 1495f152f7ec
Create Date: 2026-02-10 11:59:42.802839

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2170352e470a'
down_revision: Union[str, Sequence[str], None] = '1495f152f7ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'monitored_drives',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('server_id', sa.Integer(), nullable=False),
        sa.Column('mount_point', sa.String(length=255), nullable=False),
        sa.Column('device', sa.String(length=255), nullable=True),
        sa.Column('fstype', sa.String(length=50), nullable=True),
        sa.Column('total_bytes', sa.BigInteger(), nullable=True),
        sa.Column('used_bytes', sa.BigInteger(), nullable=True),
        sa.Column('free_bytes', sa.BigInteger(), nullable=True),
        sa.Column('percent_used', sa.Float(), nullable=True),
        sa.Column('is_mounted', sa.Boolean(), default=False),
        sa.Column('is_readonly', sa.Boolean(), default=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('server_id', 'mount_point', name='uq_server_mount')
    )
    op.create_index(op.f('ix_monitored_drives_server_id'), 'monitored_drives', ['server_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_monitored_drives_server_id'), table_name='monitored_drives')
    op.drop_table('monitored_drives')
