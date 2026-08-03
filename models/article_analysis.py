"""Persistence model for AI-generated article analysis results."""

import json
from datetime import datetime, timezone
from typing import Any

from core.ai_status import AIProcessingStatus
from extensions import db


class ArticleAnalysis(db.Model):
    """Stores a single AI analysis lifecycle and result for one article."""

    __tablename__ = "article_analyses"

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(
        db.Integer,
        db.ForeignKey("articles.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    summary = db.Column(db.Text, nullable=True)
    suggested_category = db.Column(db.String(150), nullable=True)
    difficulty = db.Column(db.String(50), nullable=True)
    technologies_json = db.Column(db.Text, nullable=True)
    keywords_json = db.Column(db.Text, nullable=True)
    sentiment = db.Column(db.String(50), nullable=True)
    provider = db.Column(db.String(50), nullable=True)
    model_used = db.Column(db.String(100), nullable=True)
    status = db.Column(
        db.String(30),
        nullable=False,
        default=AIProcessingStatus.PENDING,
        index=True,
    )
    error_message = db.Column(db.Text, nullable=True)
    processed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    article = db.relationship("Article", back_populates="analysis")

    @property
    def technologies(self) -> list[str]:
        """Return technologies as a safe list regardless of stored JSON."""
        return self._load_json_list(self.technologies_json)

    @technologies.setter
    def technologies(self, value: list[str]) -> None:
        """Store technologies as a JSON array in the SQL Server text column."""
        self.technologies_json = self._dump_json_list(value)

    @property
    def keywords(self) -> list[str]:
        """Return keywords as a safe list regardless of stored JSON."""
        return self._load_json_list(self.keywords_json)

    @keywords.setter
    def keywords(self, value: list[str]) -> None:
        """Store keywords as a JSON array in the SQL Server text column."""
        self.keywords_json = self._dump_json_list(value)

    def mark_processing(self) -> None:
        """Mark this analysis as currently being processed."""
        self.status = AIProcessingStatus.PROCESSING
        self.error_message = None

    def mark_completed(self) -> None:
        """Mark this analysis as completed using a timezone-consistent UTC value."""
        self.status = AIProcessingStatus.COMPLETED
        self.processed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.error_message = None

    def mark_failed(self, message: str) -> None:
        """Mark this analysis as failed and retain a bounded diagnostic message."""
        self.status = AIProcessingStatus.FAILED
        self.error_message = (message or "Analysis processing failed.")[:1000]

    @staticmethod
    def _load_json_list(value: str | None) -> list[str]:
        """Deserialize a JSON array without allowing invalid data to propagate."""
        if not value:
            return []

        try:
            parsed_value: Any = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return []

        return parsed_value if isinstance(parsed_value, list) else []

    @staticmethod
    def _dump_json_list(value: list[str] | None) -> str:
        """Serialize a list into valid JSON, treating invalid input as empty."""
        return json.dumps(value if isinstance(value, list) else [])

    def __repr__(self) -> str:
        """Return a concise debugging representation."""
        return f"<ArticleAnalysis article_id={self.article_id} status={self.status}>"
