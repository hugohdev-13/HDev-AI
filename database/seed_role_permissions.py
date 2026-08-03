"""Idempotent role-to-permission bootstrap assignments."""

import logging

from core.permissions import Permissions
from extensions import db
from models import Permission, Role


logger = logging.getLogger(__name__)
BOOTSTRAP_ADMIN_ROLE_NAMES = ("Administrator", "Admin", "Administrador")
ROLE_PERMISSIONS = {
    "Editor": [
        Permissions.ARTICLES_VIEW,
        Permissions.ARTICLES_CREATE,
        Permissions.ARTICLES_EDIT,
        Permissions.ARTICLES_DELETE,
        Permissions.AI_ANALYSIS_VIEW,
        Permissions.AI_ANALYSIS_PROCESS,
        Permissions.AI_ANALYSIS_RETRY,
    ],
    "Reader": [Permissions.DASHBOARD_VIEW],
    "Autor": [
        Permissions.DASHBOARD_VIEW,
        Permissions.ARTICLES_VIEW,
        Permissions.ARTICLES_CREATE,
        Permissions.ARTICLES_EDIT,
        Permissions.AI_ANALYSIS_VIEW,
        Permissions.AI_ANALYSIS_PROCESS,
    ],
    "Lector": [Permissions.DASHBOARD_VIEW, Permissions.AI_ANALYSIS_VIEW],
}


def seed_role_permissions() -> None:
    """Assign bootstrap permissions to existing roles without duplicates."""
    permissions_by_code = {
        permission.code: permission for permission in Permission.query.all()
    }
    all_permissions = list(permissions_by_code.values())

    for role_name in BOOTSTRAP_ADMIN_ROLE_NAMES:
        role = Role.query.filter_by(name=role_name).first()
        if role is not None:
            role.permissions = all_permissions

    for role_name, permission_codes in ROLE_PERMISSIONS.items():
        role = Role.query.filter_by(name=role_name).first()
        if role is not None:
            role.permissions = [
                permissions_by_code[code]
                for code in permission_codes
                if code in permissions_by_code
            ]

    db.session.commit()
    logger.info("Role-permission seed completed")
