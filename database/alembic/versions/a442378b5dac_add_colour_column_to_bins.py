"""add colour column to bins

Revision ID: a442378b5dac
Revises: b3950592f43e
Create Date: 2026-02-05 01:30:03.306404

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'a442378b5dac'
down_revision: Union[str, Sequence[str], None] = 'b3950592f43e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('bins', schema=None) as batch_op:
        batch_op.add_column(sa.Column('colour', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('bins', schema=None) as batch_op:
        batch_op.drop_column('colour')
