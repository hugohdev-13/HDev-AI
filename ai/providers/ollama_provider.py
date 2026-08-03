"""Deterministic mock implementation of an Ollama provider."""

from typing import Any

from ai.dto.article_analysis import ArticleAnalysisDTO
from ai.providers.base_provider import BaseProvider
from core.ai_status import AIProcessingStatus


class OllamaProvider(BaseProvider):
    """Returns a predictable local-model analysis mock."""

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._config.OLLAMA_MODEL

    def analyze_article(self, article: Any) -> ArticleAnalysisDTO:
        title, text = self._validate_article(article)
        return ArticleAnalysisDTO(
            summary=f"Resumen Ollama local: {self._build_summary(text)}",
            suggested_category="IA local",
            difficulty="Básico" if len(text.split()) < 80 else "Intermedio",
            technologies=["Ollama", "Modelos locales"],
            keywords=[title, "local", "privacidad"],
            sentiment="neutral",
            provider=self.provider_name,
            model_used=self.model_name,
            status=AIProcessingStatus.COMPLETED,
        )
