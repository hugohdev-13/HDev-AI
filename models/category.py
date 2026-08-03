from extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False, unique=True)

    description = db.Column(db.String(300))

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    articles = db.relationship(
        "Article",
        backref="category",
        lazy=True
    )

    def __repr__(self):
        return f"<Category {self.name}>"