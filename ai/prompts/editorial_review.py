"""Structured prompt and schema for advisory editorial quality reviews."""

from typing import Any

from ai.prompts.editorial import build_editorial_input


EDITORIAL_REVIEW_INSTRUCTIONS = """Eres un revisor editorial para HDev AI.
Evalúa exclusivamente el título, resumen y contenido recibidos, en el idioma editorial indicado.
No modifiques el artículo ni decidas su publicación o workflow. No afirmes haber verificado hechos en Internet y no inventes fuentes, citas o URLs. Cuando una afirmación no sea comprobable con el texto, indica que requiere verificación.
Evalúa claridad, estructura, calidad del resumen, coherencia título/contenido, legibilidad, afirmaciones que requieren verificación, lenguaje exagerado o clickbait e información faltante. Ofrece mejoras concretas y accionables. publication_readiness es solo una recomendación para un editor humano."""

EDITORIAL_REVIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "overall_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "clarity_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "structure_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "summary_quality_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "title_content_alignment_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "readability_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "factual_risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
        "publication_readiness": {"type": "string", "enum": ["ready", "needs_review", "not_ready"]},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "issues": {"type": "array", "items": {"type": "string"}},
        "recommendations": {"type": "array", "items": {"type": "string"}},
        "missing_information": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "overall_score", "clarity_score", "structure_score", "summary_quality_score",
        "title_content_alignment_score", "readability_score", "factual_risk_level",
        "publication_readiness", "strengths", "issues", "recommendations",
        "missing_information",
    ],
}


def build_editorial_review_input(article: Any, language: str, max_length: int) -> str:
    """Build a bounded review input using the same safe article representation."""
    return build_editorial_input(article, language, max_length)
