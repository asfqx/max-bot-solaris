"""create users table

Revision ID: 202604060001
Revises:
Create Date: 2026-04-06 00:01:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "202604060001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("last_reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_reminder_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_reminder_index", sa.Integer(), nullable=False, server_default=sa.text("-1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("uuid"),
    )
    op.create_index(op.f("ix_user_chat_id"), "user", ["chat_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_chat_id"), table_name="user")
    op.drop_table("user")
