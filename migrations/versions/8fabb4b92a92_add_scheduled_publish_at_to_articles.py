"""Add scheduled publish at to articles.

Revision ID: 8fabb4b92a92
Revises: a7c9d2e4f611
Create Date: 2026-08-21 14:39:36.565180
"""

from alembic import op
import sqlalchemy as sa


revision = "8fabb4b92a92"
down_revision = "a7c9d2e4f611"
branch_labels = None
depends_on = None


def upgrade():
    """Add the nullable effective-publication schedule only."""
    op.add_column(
        "articles",
        sa.Column("scheduled_publish_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    """Remove only the scheduled publication column."""
    op.drop_column("articles", "scheduled_publish_at")
