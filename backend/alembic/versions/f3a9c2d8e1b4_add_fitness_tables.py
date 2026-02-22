"""add_fitness_tables

Revision ID: f3a9c2d8e1b4
Revises: b8e2d4f7a01c
Create Date: 2026-02-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f3a9c2d8e1b4'
down_revision: Union[str, Sequence[str], None] = 'b8e2d4f7a01c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add source column to existing weight_entries table
    op.add_column('weight_entries',
        sa.Column('source', sa.String(length=20), nullable=True, server_default='manual')
    )

    # Create garmin_credentials table
    op.create_table('garmin_credentials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('garmin_username', sa.String(length=255), nullable=True),
        sa.Column('encrypted_tokens', sa.Text(), nullable=True),
        sa.Column('sync_enabled', sa.Boolean(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('sync_status', sa.String(length=20), nullable=True, server_default='never'),
        sa.Column('sync_error', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index(op.f('ix_garmin_credentials_id'), 'garmin_credentials', ['id'], unique=False)

    # Create garmin_daily_stats table
    op.create_table('garmin_daily_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('steps', sa.Integer(), nullable=True),
        sa.Column('active_calories', sa.Integer(), nullable=True),
        sa.Column('sleep_minutes', sa.Integer(), nullable=True),
        sa.Column('resting_hr', sa.Integer(), nullable=True),
        sa.Column('synced_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'date', name='uq_garmin_daily_user_date'),
    )
    op.create_index(op.f('ix_garmin_daily_stats_id'), 'garmin_daily_stats', ['id'], unique=False)
    op.create_index('idx_garmin_daily_user_date', 'garmin_daily_stats', ['user_id', 'date'], unique=False)

    # Create garmin_activities table
    op.create_table('garmin_activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('garmin_activity_id', sa.String(length=100), nullable=False),
        sa.Column('activity_type', sa.String(length=100), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('distance_km', sa.Numeric(8, 3), nullable=True),
        sa.Column('calories', sa.Integer(), nullable=True),
        sa.Column('avg_hr', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'garmin_activity_id', name='uq_garmin_activity_user_id'),
    )
    op.create_index(op.f('ix_garmin_activities_id'), 'garmin_activities', ['id'], unique=False)
    op.create_index('idx_garmin_activity_user_time', 'garmin_activities', ['user_id', 'start_time'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_garmin_activity_user_time', table_name='garmin_activities')
    op.drop_index(op.f('ix_garmin_activities_id'), table_name='garmin_activities')
    op.drop_table('garmin_activities')

    op.drop_index('idx_garmin_daily_user_date', table_name='garmin_daily_stats')
    op.drop_index(op.f('ix_garmin_daily_stats_id'), table_name='garmin_daily_stats')
    op.drop_table('garmin_daily_stats')

    op.drop_index(op.f('ix_garmin_credentials_id'), table_name='garmin_credentials')
    op.drop_table('garmin_credentials')

    op.drop_column('weight_entries', 'source')
