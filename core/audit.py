"""Structured audit logging helpers for security-relevant application events."""

import logging
from typing import Any


audit_logger = logging.getLogger("hdev_ai.audit")


def log_audit_event(event: str, **details: Any) -> None:
    """Write an audit event through Python logging without exposing secrets."""
    audit_logger.info("event=%s details=%s", event, details)
