"""Seed application roles required by the RBAC bootstrap."""

import logging

from extensions import db
from models import Role


logger = logging.getLogger(__name__)
ROLES = [
    ("Administrator", "Full access to the system"),
    ("Admin", "Bootstrap administrator alias"),
    ("Editor", "Manages articles"),
    ("Autor", "Creates and edits articles"),
    ("Reader", "Dashboard access only"),
    ("Lector", "Legacy dashboard access role"),
    ("Administrador", "Legacy administrator role"),
]


def seed_roles() -> None:
    """Create missing roles without deleting legacy role records."""
    for name, description in ROLES:
        if Role.query.filter_by(name=name).first() is None:
            db.session.add(Role(name=name, description=description))

    db.session.commit()
    logger.info("Role seed completed")
