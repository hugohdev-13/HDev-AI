"""Data access operations for RBAC authorization."""

from sqlalchemy import select

from extensions import db
from models import Permission, Role, RolePermission, User


class AuthorizationRepository:
    """Retrieves roles and permissions through SQLAlchemy only."""

    @staticmethod
    def get_user_permissions(user_id: int) -> list[str]:
        """Return the permission codes assigned to a user role."""
        statement = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(User, User.role_id == Role.id)
            .where(User.id == user_id)
        )
        return list(db.session.scalars(statement))

    @staticmethod
    def get_role_permissions(role_id: int) -> list[str]:
        """Return the permission codes assigned to a role."""
        statement = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
        )
        return list(db.session.scalars(statement))

    @staticmethod
    def get_user_roles(user_id: int) -> list[str]:
        """Return the role names assigned to a user."""
        statement = select(Role.name).join(User, User.role_id == Role.id).where(User.id == user_id)
        return list(db.session.scalars(statement))

    @staticmethod
    def has_permission(user_id: int, permission_name: str) -> bool:
        """Determine whether a user receives a permission from its role."""
        statement = (
            select(Permission.id)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(User, User.role_id == Role.id)
            .where(User.id == user_id, Permission.code == permission_name)
            .limit(1)
        )
        return db.session.scalar(statement) is not None
