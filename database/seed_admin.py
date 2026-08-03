"""Create or repair the bootstrap administrator account."""

import logging
import os

from werkzeug.security import generate_password_hash

from extensions import db
from models import Role, User


logger = logging.getLogger(__name__)
ADMIN_EMAIL = os.getenv("HDEV_ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("HDEV_ADMIN_PASSWORD")
ADMIN_ROLE_NAME = "Administrator"


def seed_admin() -> None:
    """Ensure the bootstrap administrator always has the Administrator role."""
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        logger.error(
            "Bootstrap administrator skipped: HDEV_ADMIN_EMAIL and "
            "HDEV_ADMIN_PASSWORD must be configured"
        )
        return

    administrator_role = Role.query.filter_by(name=ADMIN_ROLE_NAME).first()
    if administrator_role is None:
        logger.warning("Bootstrap Administrator role does not exist")
        return

    admin = User.query.filter_by(email=ADMIN_EMAIL).first()
    if admin is None:
        admin = User(
            first_name="Hector Hugo",
            last_name="Hernandez",
            email=ADMIN_EMAIL,
            password_hash=generate_password_hash(ADMIN_PASSWORD),
            role_id=administrator_role.id,
            is_active=True,
        )
        db.session.add(admin)
        logger.info("Bootstrap administrator created user_email=%s", ADMIN_EMAIL)
    elif admin.role_id != administrator_role.id:
        admin.role_id = administrator_role.id
        logger.info("Bootstrap administrator role repaired user_id=%s", admin.id)

    db.session.commit()
