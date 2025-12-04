"""add logistics shipping fields to orders

Revision ID: 813e6092a285
Revises: 02929eabf69b
Create Date: 2025-12-04 03:14:31.580256

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '813e6092a285'
down_revision: Union[str, Sequence[str], None] = '02929eabf69b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('shipping_id', sa.Integer(), nullable=True))
    op.add_column('orders', sa.Column('shipping_status', sa.String(length=50), nullable=True))
    op.add_column('orders', sa.Column('shipping_transport_type', sa.String(length=20), nullable=True))
    op.add_column('orders', sa.Column('shipping_total_cost', sa.Numeric(10, 2), nullable=True))
    op.add_column('orders', sa.Column('shipping_currency', sa.String(length=3), nullable=True))

    # índice opcional
    op.create_index('ix_orders_shipping_id', 'orders', ['shipping_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_orders_shipping_id', table_name='orders')
    op.drop_column('orders', 'shipping_currency')
    op.drop_column('orders', 'shipping_total_cost')
    op.drop_column('orders', 'shipping_transport_type')
    op.drop_column('orders', 'shipping_status')
    op.drop_column('orders', 'shipping_id')