"""Add payment reports."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "14b8744e4f57"
down_revision: Union[str, None] = "78973802deaf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payment_report",
        sa.Column("payment_report_id", sa.UUID(), nullable=False),
        sa.Column("cooperative_id", sa.UUID(), nullable=False),
        sa.Column("farmer_id", sa.UUID(), nullable=False),
        sa.Column("report_type", sa.String(length=30), nullable=False),
        sa.Column("reported_month_start", sa.Date(), nullable=False),
        sa.Column("reported_month_label", sa.String(length=40), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("confirmation_sms_sent", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["cooperative_id"],
            ["cooperative.cooperative_id"],
        ),
        sa.ForeignKeyConstraint(
            ["farmer_id"],
            ["farmer.user_id"],
        ),
        sa.PrimaryKeyConstraint("payment_report_id"),
    )

    op.create_index(
        "ix_payment_report_cooperative_id",
        "payment_report",
        ["cooperative_id"],
        unique=False,
    )
    op.create_index(
        "ix_payment_report_farmer_id",
        "payment_report",
        ["farmer_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_payment_report_farmer_id",
        table_name="payment_report",
    )
    op.drop_index(
        "ix_payment_report_cooperative_id",
        table_name="payment_report",
    )
    op.drop_table("payment_report")
