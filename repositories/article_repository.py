from models import Article
from extensions import db


class ArticleRepository:

    @staticmethod
    def get_all():
        return Article.query.all()

    @staticmethod
    def get_by_id(article_id):
        return db.session.get(Article, article_id)

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
    def search(title=None):

        query = Article.query

        if title:
            query = query.filter(
                Article.title.ilike(f"%{title}%")
            )

        return query.order_by(
            Article.created_at.desc()
        )
