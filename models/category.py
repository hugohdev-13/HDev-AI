"""Category model for organizing article content."""

from extensions import db


class Category(db.Model):
    """A primary article category with presentation metadata."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    slug = db.Column(db.String(140), nullable=False, unique=True)
    description = db.Column(db.String(500), nullable=True)
    color = db.Column(db.String(20), nullable=False, default="#2563EB")
    icon = db.Column(db.String(100), nullable=False, default="bi-folder")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    articles = db.relationship("Article", back_populates="category", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Category {self.name}>"
