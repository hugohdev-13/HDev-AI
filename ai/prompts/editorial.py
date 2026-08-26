"""Structured prompt and schema for human-reviewed editorial suggestions."""

from typing import Any


EDITORIAL_INSTRUCTIONS = """Eres un asistente editorial para HDev AI, una plataforma educativa de noticias y contenido tecnológico.
Responde en el idioma editorial indicado. Preserva hechos presentes en el artículo y no inventes fuentes, cifras, citas ni URLs.
Mejora claridad y estructura, sugiere un título profesional, resumen conciso, contenido mejorado, categoría, keywords y tecnologías.
No decidas publicación, estados editoriales ni fechas. Las sugerencias serán revisadas por una persona."""

EDITORIAL_SUGGESTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "suggested_title": {"type": "string"},
        "suggested_summary": {"type": "string"},
        "suggested_content": {"type": "string"},
        "suggested_category": {"type": "string"},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "technologies": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string"},
    },
    "required": [
        "suggested_title",
        "suggested_summary",
        "suggested_content",
        "suggested_category",
        "keywords",
        "technologies",
        "notes",
    ],
}


def build_editorial_input(article: Any, language: str, max_length: int) -> str:
    """Create a bounded, explicit input without exposing internal prompts."""
    title = str(getattr(article, "title", "") or "").strip()
    summary = str(getattr(article, "summary", "") or "").strip()
    content = str(getattr(article, "content", "") or "").strip()
    text = (content or summary)[:max_length]
    return (
        f"Idioma editorial: {language}\n"
        f"Título actual: {title}\n"
        f"Resumen actual: {summary[:max_length]}\n"
        f"Contenido actual:\n{text}"
    )
