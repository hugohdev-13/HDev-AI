"""Read-only public landing page queries."""
from sqlalchemy import func, select
from extensions import db
from models import Article, Source, User


class PublicRepository:
    @staticmethod
    def recent_published(limit: int = 6):
        statement = select(Article).where(Article.status == "published").order_by(Article.published_at.desc(), Article.id.desc()).limit(limit)
        return list(db.session.scalars(statement))

    @staticmethod
    def statistics() -> dict[str, int]:
        return {"articles": int(db.session.scalar(select(func.count()).select_from(Article)) or 0), "published": int(db.session.scalar(select(func.count()).where(Article.status == "published")) or 0), "sources": int(db.session.scalar(select(func.count()).select_from(Source)) or 0), "users": int(db.session.scalar(select(func.count()).select_from(User)) or 0)}
