"""Authorization decorators for protected Flask routes."""

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import abort
from flask_login import current_user

from core.audit import log_audit_event
from extensions import login_manager
from services.authorization_service import AuthorizationService


logger = logging.getLogger(__name__)


def permission_required(permission_name: str) -> Callable:
    """Require authentication, a valid role, and a named permission."""
    def decorator(view_function: Callable) -> Callable:
        """Wrap a Flask view and enforce authorization before execution."""
        @wraps(view_function)
        def wrapped_view(*args: Any, **kwargs: Any) -> Any:
            try:
                if current_user is None or not current_user.is_authenticated:
                    logger.info("Anonymous access redirected permission=%s", permission_name)
                    return login_manager.unauthorized()

                if getattr(current_user, "role", None) is None:
                    logger.warning("User without role user_id=%s", current_user.id)
                    log_audit_event(
                        "authorization.user_without_role",
                        user_id=current_user.id,
                        permission=permission_name,
                    )
                    abort(403)

                granted = AuthorizationService.has_permission(current_user, permission_name)
                if granted:
                    logger.info(
                        "Permission granted user_id=%s permission=%s",
                        current_user.id,
                        permission_name,
                    )
                else:
                    logger.warning(
                        "Permission denied user_id=%s permission=%s",
                        current_user.id,
                        permission_name,
                    )
                    abort(403)
            except Exception as error:
                if getattr(error, "code", None) == 403:
                    raise
                logger.exception(
                    "Authorization failure user_id=%s permission=%s",
                    getattr(current_user, "id", None),
                    permission_name,
                )
                abort(403)

            # Keep the view outside authorization error handling: a database,
            # template, or dashboard error must remain a 500, never a false 403.
            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator
