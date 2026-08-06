"""Extend category metadata.

Revision ID: f92c17a4d61b
Revises: e31b9c7a4d20
"""

from alembic import op
import sqlalchemy as sa


revision = "f92c17a4d61b"
down_revision = "e31b9c7a4d20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add additive category metadata without removing existing records."""
    op.alter_column("categories", "name", existing_type=sa.String(length=100), type_=sa.String(length=120), existing_nullable=False)
    op.alter_column("categories", "description", existing_type=sa.String(length=300), type_=sa.String(length=500), existing_nullable=True)
    # Nullable during rollout preserves existing categories; a later data migration
    # can backfill slugs before enforcing non-null at database level.
    op.add_column("categories", sa.Column("slug", sa.String(length=140), nullable=True))
    op.add_column("categories", sa.Column("color", sa.String(length=20), nullable=False, server_default="#2563EB"))
    op.add_column("categories", sa.Column("icon", sa.String(length=100), nullable=False, server_default="bi-folder"))
    op.add_column("categories", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("categories", sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True, mssql_where=sa.text("slug IS NOT NULL"))
    op.create_index("ix_categories_is_active", "categories", ["is_active"], unique=False)
    op.create_index("ix_articles_category_id", "articles", ["category_id"], unique=False)


def downgrade() -> None:
    """Remove only the metadata introduced by this revision."""
    op.drop_index("ix_articles_category_id", table_name="articles")
    op.drop_index("ix_categories_is_active", table_name="categories")
    op.drop_index("ix_categories_slug", table_name="categories")
    op.drop_column("categories", "updated_at")
    op.drop_column("categories", "is_active")
    op.drop_column("categories", "icon")
    op.drop_column("categories", "color")
    op.drop_column("categories", "slug")
    op.alter_column("categories", "description", existing_type=sa.String(length=500), type_=sa.String(length=300), existing_nullable=True)
    op.alter_column("categories", "name", existing_type=sa.String(length=120), type_=sa.String(length=100), existing_nullable=False)
