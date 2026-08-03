"""Provider-agnostic orchestration of article analysis."""

import logging
from typing import Any

from ai.dto.article_analysis import ArticleAnalysisDTO
from ai.factory.provider_factory import ProviderFactory
from ai.providers.base_provider import BaseProvider
from core.ai_status import AIProcessingStatus


logger = logging.getLogger(__name__)


class AIService:
    """Analyzes articles through an injected or configured provider."""

    def __init__(self, provider: BaseProvider | None = None) -> None:
        self._provider = provider or ProviderFactory.create()

    def analyze(self, article: Any) -> ArticleAnalysisDTO:
        """Validate, analyze, and normalize an article without persistence."""
        provider_name = self._safe_provider_attribute("provider_name")
        model_name = self._safe_provider_attribute("model_name")
        article_id = getattr(article, "id", None)
        logger.info("AI analysis started article_id=%s provider=%s", article_id, provider_name)

        try:
            self._provider._validate_article(article)
            result = self._provider.analyze_article(article)
            if not isinstance(result, ArticleAnalysisDTO):
                raise TypeError("AI provider must return an ArticleAnalysisDTO.")

            normalized_result = ArticleAnalysisDTO.from_dict(result.to_dict())
            logger.info("AI analysis completed article_id=%s provider=%s", article_id, provider_name)
            return normalized_result
        except Exception as error:
            logger.exception("AI provider error article_id=%s provider=%s", article_id, provider_name)
            return ArticleAnalysisDTO(
                summary="",
                suggested_category="",
                difficulty="",
                technologies=[],
                keywords=[],
                sentiment="",
                provider=provider_name,
                model_used=model_name,
                status=AIProcessingStatus.FAILED,
                error_message=f"AI analysis failed: {error.__class__.__name__}",
            )

    def _safe_provider_attribute(self, attribute_name: str) -> str:
        """Read optional provider metadata without hiding analysis errors."""
        try:
            value = getattr(self._provider, attribute_name)
            return value if isinstance(value, str) else ""
        except Exception:
            return ""
