"""add_custom_widget_data

Revision ID: a3f7c9e12d45
Revises: d19bfb2fd00b
Create Date: 2026-02-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f7c9e12d45'
down_revision: Union[str, Sequence[str], None] = 'd19bfb2fd00b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'custom_widget_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('widget_id', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('subtitle', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('link_url', sa.Text(), nullable=True),
        sa.Column('link_text', sa.String(length=100), nullable=True),
        sa.Column('visible', sa.Boolean(), nullable=True),
        sa.Column('alert_active', sa.Boolean(), nullable=True),
        sa.Column('alert_severity', sa.String(length=20), nullable=True),
        sa.Column('alert_message', sa.String(length=255), nullable=True),
        sa.Column('highlight', sa.Boolean(), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_custom_widget_items', 'custom_widget_data', ['user_id', 'widget_id', 'visible'], unique=False)
    op.create_index('idx_custom_widget_alerts', 'custom_widget_data', ['user_id', 'alert_active'], unique=False)
    op.create_index(op.f('ix_custom_widget_data_id'), 'custom_widget_data', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_custom_widget_data_id'), table_name='custom_widget_data')
    op.drop_index('idx_custom_widget_alerts', table_name='custom_widget_data')
    op.drop_index('idx_custom_widget_items', table_name='custom_widget_data')
    op.drop_table('custom_widget_data')
