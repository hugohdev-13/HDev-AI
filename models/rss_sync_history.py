"""Persistent audit-style history for RSS synchronization attempts."""

from extensions import db


class RSSSyncHistory(db.Model):
    __tablename__ = "rss_sync_history"

    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey("sources.id"), nullable=False, index=True)
    trigger_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, index=True)
    imported_count = db.Column(db.Integer, nullable=False, default=0)
    duplicate_count = db.Column(db.Integer, nullable=False, default=0)
    failed_count = db.Column(db.Integer, nullable=False, default=0)
    total_entries = db.Column(db.Integer, nullable=False, default=0)
    message = db.Column(db.String(500), nullable=True)
    started_at = db.Column(db.DateTime, nullable=False)
    finished_at = db.Column(db.DateTime, nullable=True)
    duration_ms = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    source = db.relationship("Source", back_populates="sync_history")
