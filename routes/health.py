"""Minimal unauthenticated health endpoints for platform monitoring."""

import logging

from flask import Blueprint, jsonify
from sqlalchemy import text

from extensions import db


logger = logging.getLogger(__name__)
health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    """Return liveness without exposing configuration or version details."""
    return jsonify({"status": "ok", "service": "hdev-ai"})


@health_bp.get("/health/database")
def database_health():
    """Return database readiness using one bounded SQL Server query."""
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ok", "service": "hdev-ai"})
    except Exception:
        logger.exception("Database health check failed")
        return jsonify({"status": "unavailable", "service": "hdev-ai"}), 503
