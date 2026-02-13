"""add_email_metadata_to_packages

Revision ID: 509cdb398a2d
Revises: 29a342be5504
Create Date: 2026-02-12 07:27:45.104701

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '509cdb398a2d'
down_revision: Union[str, Sequence[str], None] = '29a342be5504'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add email metadata columns to packages table
    op.add_column('packages', sa.Column('email_source', sa.String(255), nullable=True))
    op.add_column('packages', sa.Column('email_subject', sa.String(500), nullable=True))
    op.add_column('packages', sa.Column('email_sender', sa.String(255), nullable=True))
    op.add_column('packages', sa.Column('email_date', sa.String(100), nullable=True))
    op.add_column('packages', sa.Column('email_body_snippet', sa.Text, nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove email metadata columns from packages table
    op.drop_column('packages', 'email_body_snippet')
    op.drop_column('packages', 'email_date')
    op.drop_column('packages', 'email_sender')
    op.drop_column('packages', 'email_subject')
    op.drop_column('packages', 'email_source')
