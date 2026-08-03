"""Application service for validated, idempotent article integrations."""

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from core.ai_status import AIProcessingStatus
from models import Article, ArticleAnalysis
from services.article_analysis_service import ArticleAnalysisService
from services.article_service import ArticleMutationResult, ArticleService
from services.automatic_analysis_service import AutomaticAnalysisResult


class IntegrationPayloadValidationError(ValueError):
    """Represents invalid integration input without exposing internal details."""

    def __init__(self, details: dict[str, str]) -> None:
        super().__init__("Invalid integration payload")
        self.details = details


@dataclass(slots=True)
class IntegrationArticleResult:
    """Result of an idempotent article integration request."""

    created: bool
    duplicate: bool
    article: Article
    ai_analysis: AutomaticAnalysisResult


class IntegrationArticleService:
    """Validates incoming data and delegates persistence to ArticleService."""

    _STRING_LIMITS = {
        "title": 250,
        "author": 150,
        "status": 50,
        "source_url": 500,
        "image_url": 500,
        "external_id": 255,
    }
    _OPTIONAL_FIELDS = {
        "summary",
        "content",
        "author",
        "status",
        "source_url",
        "image_url",
        "external_id",
    }

    @classmethod
    def create_or_reuse(cls, payload: Any) -> IntegrationArticleResult:
        """Create an article once, or return its existing idempotent match."""
        data = cls.validate_payload(payload)
        existing_article = ArticleService.find_duplicate_for_integration(data)
        if existing_article is not None:
            return IntegrationArticleResult(
                created=False,
                duplicate=True,
                article=existing_article,
                ai_analysis=cls._existing_analysis_result(existing_article),
            )

        mutation = ArticleService.create_article_with_analysis(data)
        return cls._created_result(mutation)

    @classmethod
    def validate_payload(cls, payload: Any) -> dict[str, Any]:
        """Normalize and validate the public n8n article payload contract."""
        if not isinstance(payload, dict):
            raise IntegrationPayloadValidationError({"payload": "A JSON object is required"})

        errors: dict[str, str] = {}
        data: dict[str, Any] = {}
        for field_name, maximum_length in cls._STRING_LIMITS.items():
            value = payload.get(field_name)
            if value is None:
                continue
            if not isinstance(value, str):
                errors[field_name] = "This field must be a string"
                continue
            normalized = value.strip()
            if len(normalized) > maximum_length:
                errors[field_name] = f"Maximum length is {maximum_length} characters"
                continue
            data[field_name] = normalized or None

        for field_name in ("summary", "content"):
            value = payload.get(field_name)
            if value is None:
                continue
            if not isinstance(value, str):
                errors[field_name] = "This field must be a string"
                continue
            data[field_name] = value.strip() or None

        title = data.get("title")
        if not title:
            errors["title"] = "This field is required"
        if not data.get("summary") and not data.get("content"):
            errors["content"] = "At least one of summary or content is required"

        for field_name in ("source_url", "image_url"):
            value = data.get(field_name)
            if value and not cls._is_valid_url(value):
                errors[field_name] = "A valid HTTP or HTTPS URL is required"

        for field_name in ("category_id", "source_id"):
            value = payload.get(field_name)
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                errors[field_name] = "This field must be a positive integer"
                continue
            data[field_name] = value

        data["status"] = data.get("status") or "draft"
        if errors:
            raise IntegrationPayloadValidationError(errors)
        return data

    @staticmethod
    def _is_valid_url(value: str) -> bool:
        """Allow only absolute HTTP(S) source and image URLs."""
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    @staticmethod
    def _created_result(mutation: ArticleMutationResult) -> IntegrationArticleResult:
        """Translate ArticleService's existing result into integration output."""
        return IntegrationArticleResult(
            created=True,
            duplicate=False,
            article=mutation.article,
            ai_analysis=mutation.ai_analysis,
        )

    @staticmethod
    def _existing_analysis_result(article: Article) -> AutomaticAnalysisResult:
        """Describe a prior analysis without re-running the AI provider."""
        analysis: ArticleAnalysis | None = ArticleAnalysisService().get_analysis(article.id)
        if analysis is None:
            return AutomaticAnalysisResult(False, None, None, None)
        return AutomaticAnalysisResult(
            triggered=False,
            status=analysis.status,
            analysis_id=analysis.id,
            message=None,
            failed=analysis.status == AIProcessingStatus.FAILED,
        )
