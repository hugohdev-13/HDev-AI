from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from models import Article
from extensions import db


class ArticleRepository:

    @staticmethod
    def get_all():
        return Article.query.options(selectinload(Article.category)).all()

    @staticmethod
    def get_by_id(article_id):
        return Article.query.options(selectinload(Article.category)).filter_by(id=article_id).first()

    @staticmethod
    def create(article):
        db.session.add(article)
        db.session.commit()
        return article

    @staticmethod
    def update():
        db.session.commit()

    @staticmethod
    def delete(article):
        db.session.delete(article)
        db.session.commit()

    @staticmethod
    def get_by_slug(slug):
        return Article.query.filter_by(slug=slug).first()

    @staticmethod
    def get_by_external_id(external_id: str):
        """Return an article by the upstream system identifier."""
        return Article.query.filter_by(external_id=external_id).first()

    @staticmethod
    def get_by_source_url(source_url: str):
        """Return an article by its normalized source URL."""
        return Article.query.filter_by(source_url=source_url).first()

    @staticmethod
    def search(
        search_term: str | None = None,
        category_id: int | None = None,
        status: str | None = None,
    ):
        """Search safely across CMS text fields using SQL Server-compatible ILIKE."""
        query = Article.query
        if search_term:
            pattern = f"%{search_term}%"
            query = query.filter(or_(Article.title.ilike(pattern), Article.author.ilike(pattern), Article.summary.ilike(pattern), Article.content.ilike(pattern)))
        if category_id is not None:
            query = query.filter(Article.category_id == category_id)
        if status:
            query = query.filter(Article.status == status)
        return query.options(selectinload(Article.category)).order_by(Article.created_at.desc(), Article.id.desc())

    @staticmethod
    def paginate(
        search_term: str | None = None,
        category_id: int | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 10,
    ):
        """Return bounded pagination and avoid errors for non-existent pages."""
        return ArticleRepository.search(
            search_term, category_id, status
        ).paginate(page=max(page, 1), per_page=per_page, error_out=False)
