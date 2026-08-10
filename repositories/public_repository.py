"""Read-only public landing page queries."""
from sqlalchemy import and_, func, select, true
from extensions import db
from models import Article, Category, Source, User


class PublicRepository:
    @staticmethod
    def recent_published(limit: int = 6):
        statement = select(Article).where(Article.status == "published").order_by(Article.published_at.desc(), Article.id.desc()).limit(limit)
        return list(db.session.scalars(statement))

    @staticmethod
    def statistics() -> dict[str, int]:
        return {"articles": int(db.session.scalar(select(func.count()).select_from(Article)) or 0), "published": int(db.session.scalar(select(func.count()).where(Article.status == "published")) or 0), "sources": int(db.session.scalar(select(func.count()).select_from(Source)) or 0), "users": int(db.session.scalar(select(func.count()).select_from(User)) or 0)}

    @staticmethod
    def public_categories(limit: int = 4) -> list[dict]:
        """Return active landing categories with published-article counts."""
        article_count = func.count(Article.id).label("article_count")
        statement = (
            select(
                Category.id,
                Category.name,
                Category.slug,
                Category.description,
                Category.color,
                Category.icon,
                article_count,
            )
            .outerjoin(
                Article,
                and_(
                    Article.category_id == Category.id,
                    Article.status == "published",
                ),
            )
            .where(Category.is_active == true())
            .group_by(
                Category.id,
                Category.name,
                Category.slug,
                Category.description,
                Category.color,
                Category.icon,
            )
            .order_by(article_count.desc(), Category.name.asc())
            .limit(limit)
        )
        return [dict(row) for row in db.session.execute(statement).mappings()]
