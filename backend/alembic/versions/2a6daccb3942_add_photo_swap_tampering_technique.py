"""add photo swap tampering technique

Revision ID: 2a6daccb3942
Revises: 05f23c7c271a
Create Date: 2026-08-25 00:06:02.896207

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a6daccb3942'
down_revision: Union[str, Sequence[str], None] = '05f23c7c271a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE tampering_technique "
        "ADD VALUE IF NOT EXISTS 'PHOTO_SWAP'"
    )


def downgrade() -> None:
    pass