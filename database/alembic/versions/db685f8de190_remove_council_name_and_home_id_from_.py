"""remove council_name and home_id from bins

Revision ID: db685f8de190
Revises: a442378b5dac
Create Date: 2026-02-05 01:32:00.798958

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'db685f8de190'
down_revision: Union[str, Sequence[str], None] = 'a442378b5dac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('bins', schema=None) as batch_op:
        batch_op.drop_column('council_name')
        batch_op.drop_column('home_id')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('bins', schema=None) as batch_op:
        batch_op.add_column(sa.Column('council_name', sa.String(), nullable=False))
        batch_op.add_column(sa.Column('home_id', sa.Integer(), nullable=False))
