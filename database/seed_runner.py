"""Execute the RBAC bootstrap seeds in dependency order."""

import logging

from app import create_app
from database.seed_admin import seed_admin
from database.seed_permissions import seed_permissions
from database.seed_role_permissions import seed_role_permissions
from database.seed_roles import seed_roles


logging.basicConfig(level=logging.INFO)
app = create_app()

with app.app_context():
    seed_roles()
    seed_permissions()
    seed_role_permissions()
    seed_admin()
