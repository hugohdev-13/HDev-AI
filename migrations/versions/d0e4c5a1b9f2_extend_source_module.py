"""Extend source metadata for the content-source module.

Revision ID: d0e4c5a1b9f2
Revises: f92c17a4d61b
"""

from alembic import op
import sqlalchemy as sa


revision = "d0e4c5a1b9f2"
down_revision = "f92c17a4d61b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Rename legacy URL columns and add non-destructive source metadata.

    ``slug`` starts nullable because pre-existing source rows have no safe,
    deterministic slug until they are reviewed or updated through the service.
    """
    op.alter_column(
        "sources",
        "website",
        new_column_name="website_url",
        existing_type=sa.String(length=300),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
    op.alter_column(
        "sources",
        "rss_url",
        new_column_name="feed_url",
        existing_type=sa.String(length=500),
        type_=sa.String(length=1000),
        existing_nullable=True,
    )
    op.add_column("sources", sa.Column("slug", sa.String(length=160), nullable=True))
    op.add_column(
        "sources",
        sa.Column("source_type", sa.String(length=50), nullable=False, server_default="rss"),
    )
    op.add_column(
        "sources",
        sa.Column(
            "sync_interval_minutes",
            sa.Integer(),
            nullable=False,
            server_default="60",
        ),
    )
    op.add_column("sources", sa.Column("last_synced_at", sa.DateTime(), nullable=True))
    op.add_column(
        "sources", sa.Column("last_sync_status", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "sources", sa.Column("last_sync_message", sa.String(length=500), nullable=True)
    )
    op.add_column(
        "sources",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.text("GETDATE()"),
        ),
    )
    op.execute("UPDATE sources SET is_active = 1 WHERE is_active IS NULL")
    op.alter_column(
        "sources",
        "is_active",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.text("1"),
    )
    op.create_index(
        "ix_sources_slug",
        "sources",
        ["slug"],
        unique=True,
        mssql_where=sa.text("slug IS NOT NULL"),
    )
    op.create_index(
        "ix_sources_feed_url",
        "sources",
        ["feed_url"],
        unique=True,
        mssql_where=sa.text("feed_url IS NOT NULL"),
    )


def downgrade() -> None:
    """Remove only the new metadata and restore legacy URL column names."""
    op.drop_index("ix_sources_feed_url", table_name="sources")
    op.drop_index("ix_sources_slug", table_name="sources")
    op.drop_column("sources", "last_sync_message")
    op.drop_column("sources", "last_sync_status")
    op.drop_column("sources", "last_synced_at")
    op.drop_column("sources", "sync_interval_minutes")
    op.drop_column("sources", "source_type")
    op.drop_column("sources", "updated_at")
    op.drop_column("sources", "slug")
    op.alter_column(
        "sources",
        "feed_url",
        new_column_name="rss_url",
        existing_type=sa.String(length=1000),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
    op.alter_column(
        "sources",
        "website_url",
        new_column_name="website",
        existing_type=sa.String(length=500),
        type_=sa.String(length=300),
        existing_nullable=True,
    )
