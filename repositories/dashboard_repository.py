from calendar import month_abbr

from sqlalchemy import extract, func

from models import Article, Category, Source, User


class DashboardRepository:
    @staticmethod
    def total_articles():
        return Article.query.count()

    @staticmethod
    def total_categories():
        return Category.query.count()

    @staticmethod
    def total_sources():
        return Source.query.count()

    @staticmethod
    def total_users():
        return User.query.count()

    @staticmethod
    def latest_articles(limit=5):
        return (
            Article.query.with_entities(
                Article.id,
                Article.title,
                Article.created_at,
            )
            .order_by(Article.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def articles_by_month():
        rows = (
            Article.query.with_entities(
                extract("year", Article.created_at).label("year"),
                extract("month", Article.created_at).label("month"),
                func.count(Article.id).label("count"),
            )
            .group_by(
                extract("year", Article.created_at),
                extract("month", Article.created_at),
            )
            .order_by(
                extract("year", Article.created_at),
                extract("month", Article.created_at),
            )
            .all()
        )

        return [
            {
                "month": month_abbr[int(row.month)],
                "count": int(row.count),
            }
            for row in rows
        ]
