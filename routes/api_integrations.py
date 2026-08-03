"""Machine-to-machine endpoints used by approved external integrations."""

import logging
from typing import Any

from flask import Blueprint, jsonify, request

from core.api_key_auth import api_key_required
from core.audit import log_audit_event
from services.integration_article_service import (
    IntegrationArticleResult,
    IntegrationArticleService,
    IntegrationPayloadValidationError,
)


logger = logging.getLogger(__name__)
api_integrations = Blueprint("api_integrations", __name__, url_prefix="/api/integrations")


@api_integrations.get("/health")
@api_key_required
def health():
    """Return a lightweight authenticated health response for n8n."""
    return jsonify({"status": "ok", "service": "hdev-ai", "integration": "n8n"})


@api_integrations.post("/articles")
@api_key_required
def create_article():
    """Accept an idempotent n8n article and trigger the existing AI pipeline."""
    payload = request.get_json(silent=True)
    metadata = _safe_metadata(payload)
    log_audit_event("integration.article.received", source="n8n", **metadata)

    try:
        result = IntegrationArticleService.create_or_reuse(payload)
    except IntegrationPayloadValidationError as error:
        logger.warning("n8n article validation failed fields=%s", sorted(error.details))
        log_audit_event(
            "integration.article.validation_failed",
            source="n8n",
            **metadata,
        )
        return jsonify({"error": "validation_error", "details": error.details}), 400
    except Exception:
        logger.exception("n8n article integration failed")
        return jsonify({"error": "integration_error", "message": "Unable to process article"}), 500

    event = "integration.article.duplicate" if result.duplicate else "integration.article.created"
    log_audit_event(event, source="n8n", article_id=result.article.id, **metadata)
    if result.ai_analysis.failed:
        log_audit_event(
            "integration.ai_analysis_failed",
            source="n8n",
            article_id=result.article.id,
            **metadata,
        )

    return jsonify(_serialize_result(result)), 200 if result.duplicate else 201


def _serialize_result(result: IntegrationArticleResult) -> dict[str, Any]:
    """Return the public response without exposing provider error details."""
    return {
        "created": result.created,
        "duplicate": result.duplicate,
        "article": {
            "id": result.article.id,
            "title": result.article.title,
            "slug": result.article.slug,
            "status": result.article.status,
        },
        "ai_analysis": {
            "triggered": result.ai_analysis.triggered,
            "status": result.ai_analysis.status,
            "analysis_id": result.ai_analysis.analysis_id,
            "failed": result.ai_analysis.failed,
        },
    }


def _safe_metadata(payload: Any) -> dict[str, str]:
    """Extract non-sensitive identifiers for audit records from an arbitrary body."""
    if not isinstance(payload, dict):
        return {}
    metadata = {}
    for field_name in ("external_id", "source_url"):
        value = payload.get(field_name)
        if isinstance(value, str) and value:
            metadata[field_name] = value[:500]
    return metadata
