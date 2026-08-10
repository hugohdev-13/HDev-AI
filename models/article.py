from extensions import db


class Article(db.Model):

    __tablename__ = "articles"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(250),
        nullable=False,
        index=True
    )

    slug = db.Column(
        db.String(250),
        unique=True,
        index=True
    )

    summary = db.Column(db.Text)

    content = db.Column(db.Text)

    image_url = db.Column(db.String(500))

    source_url = db.Column(db.String(500))

    author = db.Column(db.String(150))

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id"),
        nullable=True,
        index=True,
    )

    source_id = db.Column(
        db.Integer,
        db.ForeignKey("sources.id"),
        nullable=True
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="draft"
    )

    published_at = db.Column(
        db.DateTime,
        index=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    external_id = db.Column(
        db.String(255),
        nullable=True,
    )

    __table_args__ = (
        db.Index(
            "ix_articles_external_id",
            "external_id",
            unique=True,
            mssql_where=db.text("external_id IS NOT NULL"),
        ),
    )

    analysis = db.relationship(
        "ArticleAnalysis",
        back_populates="article",
        uselist=False,
        cascade="all, delete-orphan"
    )
    category = db.relationship("Category", back_populates="articles")
    source = db.relationship("Source", back_populates="articles")

    def __repr__(self):
        return f"<Article {self.title}>"
