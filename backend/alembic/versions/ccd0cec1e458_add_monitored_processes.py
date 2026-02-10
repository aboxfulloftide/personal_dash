"""add_monitored_processes

Revision ID: ccd0cec1e458
Revises: 1823f4b0495f
Create Date: 2026-02-09 11:37:56.792848

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ccd0cec1e458'
down_revision: Union[str, Sequence[str], None] = '1823f4b0495f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'monitored_processes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('server_id', sa.Integer(), nullable=False),
        sa.Column('process_name', sa.String(length=255), nullable=False),
        sa.Column('match_pattern', sa.String(length=255), nullable=False),
        sa.Column('is_running', sa.Boolean(), default=False),
        sa.Column('cpu_percent', sa.Float(), nullable=True),
        sa.Column('memory_mb', sa.BigInteger(), nullable=True),
        sa.Column('pid', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_monitored_processes_server_id'), 'monitored_processes', ['server_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_monitored_processes_server_id'), table_name='monitored_processes')
    op.drop_table('monitored_processes')
