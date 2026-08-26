"""Provider-agnostic orchestration of article analysis."""

import logging
from typing import Any

from ai.dto.article_analysis import ArticleAnalysisDTO
from ai.dto.editorial_review import EditorialReviewDTO
from ai.dto.editorial_suggestion import EditorialSuggestionDTO
from ai.factory.provider_factory import ProviderFactory
from ai.providers.base_provider import BaseProvider
from core.ai_status import AIProcessingStatus
from core.exceptions import AIProviderNotConfiguredError


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
            logger.warning(
                "AI provider failed article_id=%s provider=%s error_type=%s",
                article_id,
                provider_name,
                error.__class__.__name__,
            )
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

    def generate_editorial_suggestions(self, article: Any) -> EditorialSuggestionDTO:
        """Generate an ephemeral editorial result without persistence or mutation."""
        provider_name = self._safe_provider_attribute("provider_name")
        model_name = self._safe_provider_attribute("model_name")
        article_id = getattr(article, "id", None)
        try:
            result = self._provider.generate_editorial_suggestions(article)
            if not isinstance(result, EditorialSuggestionDTO):
                raise TypeError("AI provider must return an EditorialSuggestionDTO.")
            return EditorialSuggestionDTO.from_dict(result.to_dict())
        except Exception as error:
            logger.warning(
                "Editorial AI suggestion failed article_id=%s provider=%s "
                "error_type=%s",
                article_id,
                provider_name,
                error.__class__.__name__,
            )
            safe_error = (
                "El proveedor de IA no está configurado."
                if isinstance(error, AIProviderNotConfiguredError)
                else "No fue posible generar sugerencias de IA."
            )
            return EditorialSuggestionDTO(
                suggested_title="",
                suggested_summary="",
                suggested_content="",
                suggested_category="",
                keywords=[],
                technologies=[],
                notes="",
                status=AIProcessingStatus.FAILED,
                provider=provider_name,
                model=model_name,
                error=safe_error,
            )

    def review_editorial_quality(self, article: Any) -> EditorialReviewDTO:
        """Evaluate quality without persisting or mutating the supplied article."""
        provider_name = self._safe_provider_attribute("provider_name")
        model_name = self._safe_provider_attribute("model_name")
        article_id = getattr(article, "id", None)
        try:
            result = self._provider.review_editorial_quality(article)
            if not isinstance(result, EditorialReviewDTO):
                raise TypeError("AI provider must return an EditorialReviewDTO.")
            return EditorialReviewDTO.from_dict(result.to_dict())
        except Exception as error:
            logger.warning(
                "Editorial AI review failed article_id=%s provider=%s "
                "operation=editorial_review error_type=%s",
                article_id,
                provider_name,
                error.__class__.__name__,
            )
            return EditorialReviewDTO(
                overall_score=0,
                clarity_score=0,
                structure_score=0,
                summary_quality_score=0,
                title_content_alignment_score=0,
                readability_score=0,
                factual_risk_level="medium",
                publication_readiness="needs_review",
                strengths=[],
                issues=[],
                recommendations=[],
                missing_information=[],
                status=AIProcessingStatus.FAILED,
                provider=provider_name,
                model=model_name,
                error="No fue posible completar la revisión editorial.",
            )

    def _safe_provider_attribute(self, attribute_name: str) -> str:
        """Read optional provider metadata without hiding analysis errors."""
        try:
            value = getattr(self._provider, attribute_name)
            return value if isinstance(value, str) else ""
        except Exception:
            return ""
