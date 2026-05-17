"""make_speedtest_user_id_nullable

Revision ID: 15edd2971d30
Revises: b1c2d3e4f5a6
Create Date: 2026-05-16 16:10:22.678624

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '15edd2971d30'
down_revision: Union[str, Sequence[str], None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'speed_test_results',
        'user_id',
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'speed_test_results',
        'user_id',
        existing_type=sa.Integer(),
        nullable=False,
    )
