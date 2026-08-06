"""SQLAlchemy persistence operations for categories."""
from sqlalchemy import func, or_, select, true
from extensions import db
from models import Article, Category


class CategoryRepository:
    @staticmethod
    def get_by_id(category_id: int) -> Category | None: return db.session.get(Category, category_id)
    @staticmethod
    def get_by_name(name: str) -> Category | None: return db.session.scalar(select(Category).where(func.lower(Category.name) == name.lower()))
    @staticmethod
    def get_by_slug(slug: str) -> Category | None: return db.session.scalar(select(Category).where(Category.slug == slug))
    @staticmethod
    def list_active() -> list[Category]: return list(db.session.scalars(select(Category).where(Category.is_active == true()).order_by(Category.name)))
    @staticmethod
    def search(search_term: str = ""):
        term = (search_term or "").strip(); statement = select(Category)
        if term:
            pattern = f"%{term}%"; statement = statement.where(or_(Category.name.ilike(pattern), Category.slug.ilike(pattern), Category.description.ilike(pattern)))
        return statement.order_by(Category.name)
    @staticmethod
    def paginate(search_term: str, page: int, per_page: int): return db.paginate(CategoryRepository.search(search_term), page=max(page, 1), per_page=per_page, error_out=False)
    @staticmethod
    def create(category: Category) -> Category:
        try: db.session.add(category); db.session.commit(); return category
        except Exception: db.session.rollback(); raise
    @staticmethod
    def save(category: Category) -> Category:
        try: db.session.commit(); return category
        except Exception: db.session.rollback(); raise
    @staticmethod
    def delete(category: Category) -> None:
        try: db.session.delete(category); db.session.commit()
        except Exception: db.session.rollback(); raise
    @staticmethod
    def count_articles(category_id: int) -> int: return int(db.session.scalar(select(func.count()).select_from(Article).where(Article.category_id == category_id)) or 0)
    @staticmethod
    def slug_exists(slug: str, exclude_id: int | None = None) -> bool:
        statement = select(Category.id).where(Category.slug == slug)
        if exclude_id is not None: statement = statement.where(Category.id != exclude_id)
        return db.session.scalar(statement) is not None
    @staticmethod
    def name_exists(name: str, exclude_id: int | None = None) -> bool:
        statement = select(Category.id).where(func.lower(Category.name) == name.lower())
        if exclude_id is not None: statement = statement.where(Category.id != exclude_id)
        return db.session.scalar(statement) is not None
