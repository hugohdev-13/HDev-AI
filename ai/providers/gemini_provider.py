"""Deterministic mock implementation of a Gemini provider."""

from typing import Any

from ai.dto.article_analysis import ArticleAnalysisDTO
from ai.providers.base_provider import BaseProvider
from core.ai_status import AIProcessingStatus


class GeminiProvider(BaseProvider):
    """Returns a predictable technical-knowledge analysis mock."""

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._config.GEMINI_MODEL

    def analyze_article(self, article: Any) -> ArticleAnalysisDTO:
        title, text = self._validate_article(article)
        return ArticleAnalysisDTO(
            summary=f"Síntesis Gemini de {title}: {self._build_summary(text)}",
            suggested_category="Conocimiento técnico",
            difficulty="Avanzado" if len(text.split()) > 120 else "Intermedio",
            technologies=["Arquitectura", "Automatización"],
            keywords=[title, "documentación", "tecnología"],
            sentiment="positivo",
            provider=self.provider_name,
            model_used=self.model_name,
            status=AIProcessingStatus.COMPLETED,
        )
