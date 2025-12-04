"""cart and order items without products fk

Revision ID: 02929eabf69b
Revises: 929a317dd1fd
Create Date: 2025-11-24 20:10:41.554760

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '02929eabf69b'
down_revision: Union[str, Sequence[str], None] = '929a317dd1fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
