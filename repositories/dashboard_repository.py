"""Read-only SQLAlchemy queries used by the enterprise dashboard."""

import json
from collections import Counter

from sqlalchemy import func, select, true

from core.ai_status import AIProcessingStatus
from extensions import db
from models import Article, ArticleAnalysis, Source, User


class DashboardRepository:
    """Encapsulate dashboard queries without coupling them to Flask routes."""

    @staticmethod
    def _count(statement) -> int:
        return int(db.session.scalar(statement) or 0)

    @classmethod
    def total_articles(cls):
        return cls._count(
            select(func.count()).select_from(Article)
        )

    @classmethod
    def published_articles(cls):
        return cls._count(
            select(func.count())
            .select_from(Article)
            .where(Article.status == "published")
        )

    @classmethod
    def draft_articles(cls):
        return cls._count(
            select(func.count())
            .select_from(Article)
            .where(Article.status == "draft")
        )

    @classmethod
    def analyzed_articles(cls):
        return cls._count(
            select(func.count())
            .select_from(ArticleAnalysis)
            .where(
                ArticleAnalysis.status
                == AIProcessingStatus.COMPLETED
            )
        )

    @classmethod
    def total_users(cls):
        return cls._count(
            select(func.count()).select_from(User)
        )

    @classmethod
    def active_users(cls):
        return cls._count(
            select(func.count())
            .select_from(User)
            .where(User.is_active == true())
        )

    @classmethod
    def total_sources(cls):
        return cls._count(
            select(func.count()).select_from(Source)
        )

    @staticmethod
    def recent_articles(limit: int = 5):
        statement = (
            select(
                Article.id,
                Article.title,
                Article.status,
                Article.created_at,
            )
            .order_by(
                Article.created_at.desc(),
                Article.id.desc(),
            )
            .limit(limit)
        )

        return [
            dict(row._mapping)
            for row in db.session.execute(statement)
        ]

    @staticmethod
    def article_status_distribution():
        statement = (
            select(
                Article.status,
                func.count(Article.id).label("count"),
            )
            .group_by(Article.status)
        )

        return [
            {
                "status": row.status or "unknown",
                "count": int(row.count or 0),
            }
            for row in db.session.execute(statement)
        ]

    @staticmethod
    def top_technologies(limit: int = 8):
        counts = Counter()

        statement = (
            select(ArticleAnalysis.technologies_json)
            .where(
                ArticleAnalysis.technologies_json.is_not(None)
            )
        )

        for value in db.session.scalars(statement):
            try:
                technologies = json.loads(value)
            except (TypeError, json.JSONDecodeError):
                continue

            if isinstance(technologies, list):
                counts.update(
                    str(item).strip()
                    for item in technologies
                    if str(item).strip()
                )

        return [
            {
                "technology": name,
                "count": count,
            }
            for name, count in counts.most_common(limit)
        ]