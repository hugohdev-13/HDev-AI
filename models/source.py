"""Content source persistence model."""

from extensions import db


class Source(db.Model):
    """An external or manual source from which content can originate."""

    __tablename__ = "sources"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    slug = db.Column(db.String(160), nullable=False, unique=True)
    website_url = db.Column(db.String(500), nullable=True)
    feed_url = db.Column(db.String(1000), nullable=True)
    source_type = db.Column(db.String(50), nullable=False, default="rss")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    sync_interval_minutes = db.Column(db.Integer, nullable=False, default=60)
    last_synced_at = db.Column(db.DateTime, nullable=True)
    last_sync_status = db.Column(db.String(50), nullable=True)
    last_sync_message = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    articles = db.relationship("Article", back_populates="source", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Source {self.name}>"
