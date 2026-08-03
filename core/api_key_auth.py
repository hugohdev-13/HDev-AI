"""API-key authentication for machine-to-machine integration endpoints."""

from functools import wraps
import hmac
import logging
from typing import Callable, TypeVar

from flask import current_app, jsonify, request

from core.audit import log_audit_event


logger = logging.getLogger(__name__)
ViewFunction = TypeVar("ViewFunction", bound=Callable)


def api_key_required(view: ViewFunction) -> ViewFunction:
    """Require the configured ``X-API-Key`` without using browser sessions."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        configured_key = current_app.config.get("N8N_API_KEY")
        provided_key = request.headers.get("X-API-Key")

        if not isinstance(configured_key, str) or not configured_key:
            logger.error("N8N integration is disabled because N8N_API_KEY is not configured")
            log_audit_event("integration.authentication_failed", source="n8n", reason="disabled")
            return _unauthorized_response()

        if not isinstance(provided_key, str) or not hmac.compare_digest(
            provided_key,
            configured_key,
        ):
            logger.warning("Invalid n8n API key attempt path=%s", request.path)
            log_audit_event("integration.authentication_failed", source="n8n", reason="invalid_key")
            return _unauthorized_response()

        return view(*args, **kwargs)

    return wrapped  # type: ignore[return-value]


def _unauthorized_response():
    """Return the stable public authentication failure contract."""
    return jsonify({"error": "unauthorized", "message": "Invalid or missing API key"}), 401
