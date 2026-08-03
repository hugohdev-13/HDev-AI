"""Seed the canonical permission catalog without duplicates."""

import logging

from core.permissions import Permissions
from extensions import db
from models import Permission


logger = logging.getLogger(__name__)


def seed_permissions() -> None:
    """Create every permission declared in ``Permissions`` when missing."""
    permission_codes = [
        value
        for name, value in vars(Permissions).items()
        if name.isupper() and isinstance(value, str)
    ]
    existing_codes = set(db.session.scalars(db.select(Permission.code)))

    for code in permission_codes:
        if code not in existing_codes:
            db.session.add(Permission(code=code, name=code.replace(".", " ").title()))

    db.session.commit()
    logger.info("Permission seed completed total=%s", len(permission_codes))
