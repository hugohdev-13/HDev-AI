"""Deterministic mock implementation of an Azure OpenAI provider."""

from typing import Any

from ai.dto.article_analysis import ArticleAnalysisDTO
from ai.providers.base_provider import BaseProvider
from core.ai_status import AIProcessingStatus


class AzureProvider(BaseProvider):
    """Returns a predictable enterprise-focused analysis mock."""

    @property
    def provider_name(self) -> str:
        return "azure"

    @property
    def model_name(self) -> str:
        return self._config.AZURE_OPENAI_MODEL

    def analyze_article(self, article: Any) -> ArticleAnalysisDTO:
        title, text = self._validate_article(article)
        return ArticleAnalysisDTO(
            summary=f"Análisis Azure empresarial: {self._build_summary(text)}",
            suggested_category="Plataformas empresariales",
            difficulty="Avanzado",
            technologies=["Azure", "Seguridad", "Integración"],
            keywords=[title, "empresa", "gobernanza"],
            sentiment="neutral",
            provider=self.provider_name,
            model_used=self.model_name,
            status=AIProcessingStatus.COMPLETED,
        )
