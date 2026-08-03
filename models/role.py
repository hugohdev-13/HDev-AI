from extensions import db


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(50),
        nullable=False,
        unique=True
    )

    description = db.Column(
        db.String(200)
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    users = db.relationship(
        "User",
        back_populates="role"
    )

    permissions = db.relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles"
    )

    def __repr__(self):
        return f"<Role {self.name}>"