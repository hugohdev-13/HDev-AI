"""Add RSS sync history.

Revision ID: a7c9d2e4f611
Revises: d0e4c5a1b9f2
"""
from alembic import op
import sqlalchemy as sa

revision = "a7c9d2e4f611"
down_revision = "d0e4c5a1b9f2"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("rss_sync_history", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("source_id", sa.Integer(), nullable=False), sa.Column("trigger_type", sa.String(20), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("imported_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("duplicate_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("total_entries", sa.Integer(), nullable=False, server_default="0"), sa.Column("message", sa.String(500)), sa.Column("started_at", sa.DateTime(), nullable=False), sa.Column("finished_at", sa.DateTime()), sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"), sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("GETDATE()")), sa.ForeignKeyConstraint(["source_id"], ["sources.id"]))
    op.create_index("ix_rss_sync_history_source_id", "rss_sync_history", ["source_id"])
    op.create_index("ix_rss_sync_history_status", "rss_sync_history", ["status"])
    op.create_index("ix_rss_sync_history_created_at", "rss_sync_history", ["created_at"])

def downgrade():
    op.drop_index("ix_rss_sync_history_created_at", table_name="rss_sync_history")
    op.drop_index("ix_rss_sync_history_status", table_name="rss_sync_history")
    op.drop_index("ix_rss_sync_history_source_id", table_name="rss_sync_history")
    op.drop_table("rss_sync_history")
