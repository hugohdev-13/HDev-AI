"""Business rules for role-based authorization."""

import logging

from flask import g
from flask_login import UserMixin

from core.audit import log_audit_event
from repositories.authorization_repository import AuthorizationRepository


logger = logging.getLogger(__name__)
BOOTSTRAP_ADMIN_ROLES = frozenset(
    {
        "admin",
        "administrator",
        "superadmin",
        "super administrator",
        "administrador",
    }
)


class AuthorizationService:
    """Provides the only application-level access point for RBAC checks."""

    @staticmethod
    def has_permission(user: UserMixin, permission: str) -> bool:
        """Return whether an authenticated user owns a requested permission.

        Bootstrap administrator roles bypass permission queries. This keeps a
        new installation accessible before role-permission seed data exists.
        """
        if not user or not getattr(user, "is_authenticated", False):
            return False

        try:
            role = getattr(user, "role", None)
        except Exception:
            logger.warning("Unable to load role for user_id=%s", getattr(user, "id", None))
            log_audit_event("authorization.role_missing", user_id=getattr(user, "id", None))
            return False

        if role is None:
            logger.warning("User without role user_id=%s", user.id)
            log_audit_event("authorization.user_without_role", user_id=user.id)
            return False

        role_name = (getattr(role, "name", "") or "").strip()
        if not role_name:
            logger.warning("Role without name user_id=%s role_id=%s", user.id, role.id)
            log_audit_event("authorization.role_missing", user_id=user.id, role_id=role.id)
            return False

        if role_name.casefold() in BOOTSTRAP_ADMIN_ROLES:
            logger.info("Permission granted by bootstrap role user_id=%s", user.id)
            log_audit_event("authorization.granted", user_id=user.id, permission=permission)
            return True

        granted = permission in AuthorizationService.get_permissions(user)
        log_audit_event(
            "authorization.granted" if granted else "authorization.denied",
            user_id=user.id,
            permission=permission,
        )
        return granted

    @staticmethod
    def get_permissions(user: UserMixin) -> frozenset[str]:
        """Return permissions while caching the result for this request."""
        if not user or not getattr(user, "is_authenticated", False):
            return frozenset()

        cache_key = f"permissions_{user.id}"
        cached_permissions = getattr(g, cache_key, None)

        if cached_permissions is None:
            cached_permissions = frozenset(
                AuthorizationRepository.get_user_permissions(user.id)
            )
            setattr(g, cache_key, cached_permissions)

        return cached_permissions

    @staticmethod
    def get_roles(user: UserMixin) -> list[str]:
        """Return user roles while caching the result for this request."""
        if not user or not getattr(user, "is_authenticated", False):
            return []

        cache_key = f"roles_{user.id}"
        cached_roles = getattr(g, cache_key, None)

        if cached_roles is None:
            cached_roles = AuthorizationRepository.get_user_roles(user.id)
            setattr(g, cache_key, cached_roles)

        return cached_roles
