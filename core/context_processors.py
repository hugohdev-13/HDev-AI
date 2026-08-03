"""Application-wide Jinja context processors."""

from datetime import date

from flask import Flask
from flask_login import current_user

from core.permissions import Permissions
from services.authorization_service import AuthorizationService


def inject_application_context() -> dict:
    """Expose shared application metadata and RBAC helpers to templates."""
    def has_permission(permission_name: str) -> bool:
        """Check a permission through the cached authorization service."""
        return AuthorizationService.has_permission(current_user, permission_name)

    return {"app_name": "HDev AI", "app_version": "1.0.0", "current_year": date.today().year, "has_permission": has_permission, "Permissions": Permissions}


def register_context_processors(app: Flask) -> None:
    """Register the application context processors with a Flask instance."""
    app.context_processor(inject_application_context)
