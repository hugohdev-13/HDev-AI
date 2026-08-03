from extensions import db


class Source(db.Model):
    __tablename__ = "sources"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False, unique=True)

    website = db.Column(db.String(300))

    rss_url = db.Column(db.String(500))

    is_active = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    articles = db.relationship(
        "Article",
        backref="source",
        lazy=True
    )

    def __repr__(self):
        return f"<Source {self.name}>"