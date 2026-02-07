"""allow_multiple_email_accounts_per_user

Revision ID: 61be8e991af1
Revises: 7173fd5fce17
Create Date: 2026-02-07 01:54:56.024153

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61be8e991af1'
down_revision: Union[str, Sequence[str], None] = '7173fd5fce17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the unique constraint on user_id to allow multiple email accounts per user
    op.drop_constraint('user_id', 'email_credentials', type_='unique')


def downgrade() -> None:
    """Downgrade schema."""
    # Restore the unique constraint on user_id
    op.create_unique_constraint('user_id', 'email_credentials', ['user_id'])
