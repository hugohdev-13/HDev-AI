"""Deterministic mock implementation of an OpenAI provider."""

from typing import Any

from ai.dto.article_analysis import ArticleAnalysisDTO
from ai.providers.base_provider import BaseProvider
from core.ai_status import AIProcessingStatus


class OpenAIProvider(BaseProvider):
    """Returns a predictable software-development analysis mock."""

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._config.OPENAI_MODEL

    def analyze_article(self, article: Any) -> ArticleAnalysisDTO:
        title, text = self._validate_article(article)
        return ArticleAnalysisDTO(
            summary=f"Resumen OpenAI: {self._build_summary(text)}",
            suggested_category="Desarrollo de software",
            difficulty="Intermedio",
            technologies=["Python", "Flask"] if "python" in title.lower() + text.lower() else ["API", "Backend"],
            keywords=[title, "backend", "api"],
            sentiment="neutral",
            provider=self.provider_name,
            model_used=self.model_name,
            status=AIProcessingStatus.COMPLETED,
        )
