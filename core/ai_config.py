"""Environment-backed configuration for simulated AI providers."""

import os


def _get_positive_int(name: str, default: int) -> int:
    """Read a positive integer environment setting with a safe fallback."""
    try:
        value = int(os.getenv(name, str(default)))
        return value if value > 0 else default
    except (TypeError, ValueError):
        return default


def _get_boolean(name: str, default: bool) -> bool:
    """Read a boolean environment setting using an explicit true allowlist."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"true", "1", "yes", "on"}


class AIConfig:
    """Centralizes AI behavior without exposing provider credentials."""

    AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "mock-openai")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "mock-gemini")
    AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL", "mock-azure")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mock-ollama")
    AI_DEFAULT_LANGUAGE = os.getenv("AI_DEFAULT_LANGUAGE", "es")
    AI_MAX_ARTICLE_LENGTH = _get_positive_int("AI_MAX_ARTICLE_LENGTH", 12000)
    AI_SUMMARY_MAX_WORDS = _get_positive_int("AI_SUMMARY_MAX_WORDS", 200)
    AI_AUTO_ANALYZE_ON_CREATE = _get_boolean("AI_AUTO_ANALYZE_ON_CREATE", True)
    AI_AUTO_ANALYZE_ON_UPDATE = _get_boolean("AI_AUTO_ANALYZE_ON_UPDATE", False)
    AI_REANALYZE_ON_CONTENT_CHANGE = _get_boolean(
        "AI_REANALYZE_ON_CONTENT_CHANGE",
        True,
    )
