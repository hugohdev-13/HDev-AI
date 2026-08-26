"""Unit tests for AIService dependency injection and error handling."""

import unittest
from types import SimpleNamespace

from ai.dto.article_analysis import ArticleAnalysisDTO
from ai.dto.editorial_review import EditorialReviewDTO
from ai.providers.base_provider import BaseProvider
from ai.services.ai_service import AIService
from core.ai_status import AIProcessingStatus


class CompletedProvider(BaseProvider):
    """Minimal injectable provider that returns a completed DTO."""

    @property
    def provider_name(self) -> str:
        return "test"

    @property
    def model_name(self) -> str:
        return "test-model"

    def analyze_article(self, article):
        self._validate_article(article)
        return ArticleAnalysisDTO("summary", "category", "basic", [], [], "neutral", self.provider_name, self.model_name, AIProcessingStatus.COMPLETED)


class FailingProvider(CompletedProvider):
    """Injectable provider used to verify graceful failures."""

    def analyze_article(self, article):
        raise RuntimeError("provider failure")


class AIServiceTestCase(unittest.TestCase):
    """Verifies service results without Flask or SQL Server."""

    article = SimpleNamespace(id=1, title="Python con Flask", content="Contenido técnico suficiente.", summary="")

    def test_injected_provider_returns_completed_dto(self) -> None:
        result = AIService(CompletedProvider()).analyze(self.article)
        self.assertEqual(result.status, AIProcessingStatus.COMPLETED)
        self.assertEqual(result.provider, "test")

    def test_failing_provider_returns_failed_dto(self) -> None:
        result = AIService(FailingProvider()).analyze(self.article)
        self.assertEqual(result.status, AIProcessingStatus.FAILED)
        self.assertEqual(result.provider, "test")

    def test_editorial_provider_failure_returns_safe_failed_dto(self) -> None:
        provider = SimpleNamespace(
            provider_name="test",
            model_name="test-model",
            generate_editorial_suggestions=lambda _article: (_ for _ in ()).throw(
                RuntimeError("provider unavailable")
            ),
        )

        result = AIService(provider).generate_editorial_suggestions(self.article)

        self.assertEqual(result.status, AIProcessingStatus.FAILED)
        self.assertEqual(result.provider, "test")
        self.assertNotIn("provider unavailable", result.error)

    def test_editorial_review_failure_returns_safe_failed_dto(self) -> None:
        provider = SimpleNamespace(
            provider_name="test",
            model_name="test-model",
            review_editorial_quality=lambda _article: (_ for _ in ()).throw(
                RuntimeError("secret provider response")
            ),
        )

        result = AIService(provider).review_editorial_quality(self.article)

        self.assertIsInstance(result, EditorialReviewDTO)
        self.assertEqual(result.status, AIProcessingStatus.FAILED)
        self.assertEqual(result.error, "No fue posible completar la revisión editorial.")
