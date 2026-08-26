"""Mocked unit tests for the remote OpenAI editorial provider."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from ai.providers.openai_provider import OpenAIProvider
from ai.services.ai_service import AIService
from core.ai_status import AIProcessingStatus


def _article():
    return SimpleNamespace(
        id=5,
        title="Flask y OpenAI",
        summary="Resumen original",
        content="Contenido original sobre integración segura.",
        status="approved",
        published_at=None,
        scheduled_publish_at=None,
    )


def _response(payload=None):
    payload = payload or {
        "suggested_title": "Flask con OpenAI",
        "suggested_summary": "Resumen mejorado",
        "suggested_content": "Contenido mejorado",
        "suggested_category": "Desarrollo de software",
        "keywords": ["Flask", "OpenAI"],
        "technologies": ["Python", "Flask"],
        "notes": "Revisar hechos.",
    }
    return SimpleNamespace(
        status="completed",
        output_text=json.dumps(payload),
        usage=SimpleNamespace(input_tokens=11, output_tokens=7, total_tokens=18),
    )


def _client(response=None, side_effect=None):
    client = MagicMock()
    client.responses.create.return_value = response or _response()
    client.responses.create.side_effect = side_effect
    return client


def test_openai_provider_uses_responses_structured_output_without_mutation():
    article = _article()
    client = _client()

    result = OpenAIProvider(client=client).generate_editorial_suggestions(article)

    assert result.status == AIProcessingStatus.COMPLETED
    assert result.suggested_title == "Flask con OpenAI"
    assert article.status == "approved"
    assert article.published_at is None
    assert article.scheduled_publish_at is None
    kwargs = client.responses.create.call_args.kwargs
    assert kwargs["text"]["format"]["type"] == "json_schema"
    assert kwargs["text"]["format"]["strict"] is True
    assert kwargs["store"] is False


def test_openai_provider_rejects_invalid_structured_output_safely():
    client = _client(_response(["not", "an", "object"]))

    result = AIService(OpenAIProvider(client=client)).generate_editorial_suggestions(
        _article()
    )

    assert result.status == AIProcessingStatus.FAILED
    assert result.error == "No fue posible generar sugerencias de IA."


def test_missing_openai_key_returns_configured_safe_message():
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        result = AIService(OpenAIProvider()).generate_editorial_suggestions(_article())

    assert result.status == AIProcessingStatus.FAILED
    assert result.error == "El proveedor de IA no está configurado."


def test_openai_timeout_auth_and_rate_limit_are_safe_and_do_not_expose_secrets():
    for error in (
        TimeoutError("request timed out"),
        RuntimeError("authentication failed key=super-secret"),
        RuntimeError("rate limit exceeded"),
    ):
        result = AIService(
            OpenAIProvider(client=_client(side_effect=error))
        ).generate_editorial_suggestions(_article())

        assert result.status == AIProcessingStatus.FAILED
        assert result.error == "No fue posible generar sugerencias de IA."
        assert "super-secret" not in (result.error or "")


def test_openai_provider_uses_structured_output_for_editorial_review():
    client = _client(_response({
        "overall_score": 88, "clarity_score": 87, "structure_score": 86,
        "summary_quality_score": 85, "title_content_alignment_score": 84,
        "readability_score": 83, "factual_risk_level": "low",
        "publication_readiness": "ready", "strengths": ["Clara"],
        "issues": [], "recommendations": ["Añadir fuente primaria"],
        "missing_information": [],
    }))

    result = OpenAIProvider(client=client).review_editorial_quality(_article())

    assert result.overall_score == 88
    assert result.status == AIProcessingStatus.COMPLETED
    kwargs = client.responses.create.call_args.kwargs
    assert kwargs["text"]["format"]["name"] == "editorial_review"
    assert kwargs["text"]["format"]["strict"] is True
