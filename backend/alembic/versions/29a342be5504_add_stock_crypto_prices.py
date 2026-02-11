"""add_stock_crypto_prices

Revision ID: 29a342be5504
Revises: 2170352e470a
Create Date: 2026-02-10 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '29a342be5504'
down_revision: Union[str, Sequence[str], None] = '2170352e470a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Stock quotes table
    op.create_table(
        'stock_quotes',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('change_percent', sa.Float(), nullable=True),
        sa.Column('provider', sa.String(20), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_stock_quotes_symbol', 'stock_quotes', ['symbol'], unique=False)
    op.create_index('ix_stock_quotes_recorded_at', 'stock_quotes', ['recorded_at'], unique=False)
    op.create_index('idx_stock_symbol_recorded', 'stock_quotes', ['symbol', 'recorded_at'], unique=False)

    # Crypto prices table
    op.create_table(
        'crypto_prices',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('coin_id', sa.String(50), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('change_24h', sa.Float(), nullable=True),
        sa.Column('provider', sa.String(20), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_crypto_prices_coin_id', 'crypto_prices', ['coin_id'], unique=False)
    op.create_index('ix_crypto_prices_recorded_at', 'crypto_prices', ['recorded_at'], unique=False)
    op.create_index('idx_crypto_coin_recorded', 'crypto_prices', ['coin_id', 'recorded_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_crypto_coin_recorded', table_name='crypto_prices')
    op.drop_index('ix_crypto_prices_recorded_at', table_name='crypto_prices')
    op.drop_index('ix_crypto_prices_coin_id', table_name='crypto_prices')
    op.drop_table('crypto_prices')

    op.drop_index('idx_stock_symbol_recorded', table_name='stock_quotes')
    op.drop_index('ix_stock_quotes_recorded_at', table_name='stock_quotes')
    op.drop_index('ix_stock_quotes_symbol', table_name='stock_quotes')
    op.drop_table('stock_quotes')
