"""SQLAlchemy persistence operations for content sources."""

from sqlalchemy import func, or_, select, true

from extensions import db
from models import Article, Source


class SourceRepository:
    """Encapsulate Source persistence without route-level database access."""

    @staticmethod
    def get_by_id(source_id: int) -> Source | None:
        return db.session.get(Source, source_id)

    @staticmethod
    def get_by_name(name: str) -> Source | None:
        return db.session.scalar(
            select(Source).where(func.lower(Source.name) == name.lower())
        )

    @staticmethod
    def get_by_slug(slug: str) -> Source | None:
        return db.session.scalar(select(Source).where(Source.slug == slug))

    @staticmethod
    def get_by_feed_url(feed_url: str) -> Source | None:
        return db.session.scalar(select(Source).where(Source.feed_url == feed_url))

    @staticmethod
    def list_active() -> list[Source]:
        statement = select(Source).where(Source.is_active == true()).order_by(Source.name)
        return list(db.session.scalars(statement))

    @staticmethod
    def list_active_rss() -> list[Source]:
        """Return only enabled RSS sources eligible for health monitoring."""
        statement = (
            select(Source)
            .where(
                Source.is_active == true(),
                Source.source_type == "rss",
            )
            .order_by(Source.name)
        )
        return list(db.session.scalars(statement))

    @staticmethod
    def search(search_term: str = ""):
        term = (search_term or "").strip()
        statement = select(Source)
        if term:
            pattern = f"%{term}%"
            statement = statement.where(
                or_(
                    Source.name.ilike(pattern),
                    Source.slug.ilike(pattern),
                    Source.website_url.ilike(pattern),
                    Source.feed_url.ilike(pattern),
                )
            )
        return statement.order_by(Source.name)

    @staticmethod
    def paginate(search_term: str, page: int, per_page: int):
        return db.paginate(
            SourceRepository.search(search_term),
            page=max(page, 1),
            per_page=per_page,
            error_out=False,
        )

    @staticmethod
    def create(source: Source) -> Source:
        try:
            db.session.add(source)
            db.session.commit()
            return source
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def save(source: Source) -> Source:
        try:
            db.session.commit()
            return source
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete(source: Source) -> None:
        try:
            db.session.delete(source)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def name_exists(name: str, exclude_id: int | None = None) -> bool:
        statement = select(Source.id).where(func.lower(Source.name) == name.lower())
        if exclude_id is not None:
            statement = statement.where(Source.id != exclude_id)
        return db.session.scalar(statement) is not None

    @staticmethod
    def slug_exists(slug: str, exclude_id: int | None = None) -> bool:
        statement = select(Source.id).where(Source.slug == slug)
        if exclude_id is not None:
            statement = statement.where(Source.id != exclude_id)
        return db.session.scalar(statement) is not None

    @staticmethod
    def feed_url_exists(feed_url: str, exclude_id: int | None = None) -> bool:
        statement = select(Source.id).where(Source.feed_url == feed_url)
        if exclude_id is not None:
            statement = statement.where(Source.id != exclude_id)
        return db.session.scalar(statement) is not None

    @staticmethod
    def count_articles(source_id: int) -> int:
        statement = select(func.count()).select_from(Article).where(
            Article.source_id == source_id
        )
        return int(db.session.scalar(statement) or 0)

    @staticmethod
    def article_counts(source_ids: list[int]) -> dict[int, int]:
        """Return article counts for multiple sources in one aggregate query."""
        if not source_ids:
            return {}
        statement = (
            select(Article.source_id, func.count(Article.id))
            .where(Article.source_id.in_(source_ids))
            .group_by(Article.source_id)
        )
        return {source_id: int(count) for source_id, count in db.session.execute(statement)}
