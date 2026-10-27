"""remove db constraints

Revision ID: ec054aa4f5b7
Revises: 77690829ab60
Create Date: 2026-10-27 12:42:00.030989

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "ec054aa4f5b7"
down_revision: Union[str, None] = "77690829ab60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
