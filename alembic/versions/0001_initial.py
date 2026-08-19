from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    status_enum = sa.Enum("draft", "active", "won", "lost", name="tenderstatus", native_enum=False)
    status_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "tenders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("customer", sa.String(length=300), nullable=False),
        sa.Column("contract_number", sa.String(length=100), nullable=True),
        sa.Column("initial_price", sa.Numeric(15, 2), nullable=False),
        sa.Column("status", status_enum, nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tenders_status", "tenders", ["status"])
    op.create_table(
        "tender_status_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tender_id", sa.Integer(), sa.ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("old_status", status_enum, nullable=False),
        sa.Column("new_status", status_enum, nullable=False),
        sa.Column("changed_by", sa.String(length=200), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tender_status_history_tender_id", "tender_status_history", ["tender_id"])


def downgrade() -> None:
    op.drop_index("ix_tender_status_history_tender_id", table_name="tender_status_history")
    op.drop_table("tender_status_history")
    op.drop_index("ix_tenders_status", table_name="tenders")
    op.drop_table("tenders")
