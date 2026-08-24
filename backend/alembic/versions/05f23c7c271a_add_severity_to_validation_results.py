"""add severity to validation_results
Revision ID: 05f23c7c271a
Revises: bccde37db354
Create Date: 2026-08-24 15:56:40.022661
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '05f23c7c271a'
down_revision: Union[str, Sequence[str], None] = 'bccde37db354'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

validation_severity_enum = sa.Enum('INFO', 'WARNING', 'CRITICAL', name='validation_severity')


def upgrade() -> None:
    """Upgrade schema."""
    validation_severity_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'validation_results',
        sa.Column(
            'severity',
            validation_severity_enum,
            nullable=False,
            server_default='INFO',
        ),
    )
    op.alter_column('validation_results', 'severity', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('validation_results', 'severity')
    validation_severity_enum.drop(op.get_bind(), checkfirst=True)