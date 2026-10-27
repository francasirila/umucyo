"""initial unified schema

Revision ID: 77690829ab60
Revises:
Create Date: 2026-10-27 12:13:07.873166

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "77690829ab60"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
