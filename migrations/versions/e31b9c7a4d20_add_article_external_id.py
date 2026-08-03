"""Add article external id.

Revision ID: e31b9c7a4d20
Revises: c95fe2ff215e
Create Date: 2026-08-01
"""

from alembic import op
import sqlalchemy as sa


revision = "e31b9c7a4d20"
down_revision = "c95fe2ff215e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add a nullable, unique upstream identifier to articles."""
    op.add_column("articles", sa.Column("external_id", sa.String(length=255), nullable=True))
    op.create_index(
        op.f("ix_articles_external_id"),
        "articles",
        ["external_id"],
        unique=True,
        mssql_where=sa.text("external_id IS NOT NULL"),
    )


def downgrade() -> None:
    """Remove the external identifier and its supporting index."""
    op.drop_index(op.f("ix_articles_external_id"), table_name="articles")
    op.drop_column("articles", "external_id")
