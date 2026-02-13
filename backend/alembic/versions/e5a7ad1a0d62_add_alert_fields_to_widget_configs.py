"""add_alert_fields_to_widget_configs

Revision ID: e5a7ad1a0d62
Revises: cdb7ce79815d
Create Date: 2026-02-12 11:11:03.343334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5a7ad1a0d62'
down_revision: Union[str, Sequence[str], None] = 'cdb7ce79815d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add alert system fields to widget_configs table
    op.add_column('widget_configs', sa.Column('alert_active', sa.Boolean, server_default='0', nullable=False))
    op.add_column('widget_configs', sa.Column('alert_severity', sa.String(20), nullable=True))
    op.add_column('widget_configs', sa.Column('alert_message', sa.Text, nullable=True))
    op.add_column('widget_configs', sa.Column('alert_triggered_at', sa.DateTime, nullable=True))
    op.add_column('widget_configs', sa.Column('original_layout_x', sa.Integer, nullable=True))
    op.add_column('widget_configs', sa.Column('original_layout_y', sa.Integer, nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove alert system fields from widget_configs table
    op.drop_column('widget_configs', 'original_layout_y')
    op.drop_column('widget_configs', 'original_layout_x')
    op.drop_column('widget_configs', 'alert_triggered_at')
    op.drop_column('widget_configs', 'alert_message')
    op.drop_column('widget_configs', 'alert_severity')
    op.drop_column('widget_configs', 'alert_active')
