"""add_email_credentials_table

Revision ID: 7173fd5fce17
Revises: e1fa63c00ecf
Create Date: 2026-02-07 01:30:22.507028

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7173fd5fce17'
down_revision: Union[str, Sequence[str], None] = 'e1fa63c00ecf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'email_credentials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('imap_server', sa.String(length=255), nullable=False),
        sa.Column('imap_port', sa.Integer(), nullable=False, server_default='993'),
        sa.Column('email_address', sa.String(length=255), nullable=False),
        sa.Column('encrypted_password', sa.String(length=500), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('scan_interval_hours', sa.Integer(), nullable=False, server_default='6'),
        sa.Column('days_to_scan', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('last_scan_at', sa.DateTime(), nullable=True),
        sa.Column('last_scan_status', sa.String(length=50), nullable=True),
        sa.Column('last_scan_message', sa.String(length=500), nullable=True),
        sa.Column('packages_found_last_scan', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_email_credentials_user_id', 'email_credentials', ['user_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_email_credentials_user_id', table_name='email_credentials')
    op.drop_table('email_credentials')
