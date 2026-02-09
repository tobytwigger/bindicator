"""change_date_put_out_at_to_datetime

Revision ID: 0eb5d4a8f7aa
Revises: d25086ea163f
Create Date: 2026-02-08 21:04:38.493596

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0eb5d4a8f7aa'
down_revision: Union[str, Sequence[str], None] = 'd25086ea163f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
