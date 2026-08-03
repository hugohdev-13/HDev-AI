"""Tests for authenticated n8n integration routes without a real n8n server."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app import app
from services.automatic_analysis_service import AutomaticAnalysisResult
from services.integration_article_service import (
    IntegrationArticleResult,
    IntegrationArticleService,
    IntegrationPayloadValidationError,
)
from services.article_service import ArticleService


VALID_PAYLOAD = {
    "external_id": "rss-123",
    "title": "Flask and n8n",
    "summary": "A valid integration summary.",
    "source_url": "https://example.com/articles/flask-n8n",
}


def _result(created: bool = True, failed: bool = False) -> IntegrationArticleResult:
    """Build a public-service result without database access."""
    article = SimpleNamespace(id=7, title="Flask and n8n", slug="flask-and-n8n", status="draft")
    analysis = AutomaticAnalysisResult(created, "failed" if failed else "completed", 3, None, failed)
    return IntegrationArticleResult(created, not created, article, analysis)


class ApiIntegrationsRouteTests(unittest.TestCase):
    """Assert API-key behavior and HTTP contracts for the integration blueprint."""

    def setUp(self) -> None:
        app.config.update(TESTING=True, N8N_API_KEY="test-n8n-key")
        self.client = app.test_client()

    def test_health_requires_valid_key(self) -> None:
        response = self.client.get("/api/integrations/health")
        self.assertEqual(response.status_code, 401)

    def test_health_accepts_valid_key(self) -> None:
        response = self.client.get("/api/integrations/health", headers={"X-API-Key": "test-n8n-key"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["integration"], "n8n")

    def test_invalid_key_returns_unauthorized(self) -> None:
        response = self.client.post("/api/integrations/articles", headers={"X-API-Key": "wrong"}, json=VALID_PAYLOAD)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json["error"], "unauthorized")

    @patch("routes.api_integrations.IntegrationArticleService.create_or_reuse")
    def test_valid_payload_creates_article(self, create_or_reuse) -> None:
        create_or_reuse.return_value = _result()
        response = self.client.post("/api/integrations/articles", headers={"X-API-Key": "test-n8n-key"}, json=VALID_PAYLOAD)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json["created"])
        self.assertFalse(response.json["duplicate"])

    def test_missing_title_returns_validation_error(self) -> None:
        response = self.client.post("/api/integrations/articles", headers={"X-API-Key": "test-n8n-key"}, json={"content": "text"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["details"]["title"], "This field is required")

    def test_missing_summary_and_content_returns_validation_error(self) -> None:
        response = self.client.post("/api/integrations/articles", headers={"X-API-Key": "test-n8n-key"}, json={"title": "Only title"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("content", response.json["details"])

    @patch("routes.api_integrations.IntegrationArticleService.create_or_reuse")
    def test_duplicate_returns_200(self, create_or_reuse) -> None:
        create_or_reuse.return_value = _result(created=False)
        response = self.client.post("/api/integrations/articles", headers={"X-API-Key": "test-n8n-key"}, json=VALID_PAYLOAD)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["duplicate"])

    @patch("routes.api_integrations.IntegrationArticleService.create_or_reuse")
    def test_failed_ai_does_not_change_creation_response(self, create_or_reuse) -> None:
        create_or_reuse.return_value = _result(failed=True)
        response = self.client.post("/api/integrations/articles", headers={"X-API-Key": "test-n8n-key"}, json=VALID_PAYLOAD)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json["ai_analysis"]["failed"])


class IntegrationArticleServiceTests(unittest.TestCase):
    """Test validation and idempotency priorities at the service boundary."""

    def test_valid_payload_is_normalized(self) -> None:
        data = IntegrationArticleService.validate_payload({"title": "  Hello  ", "content": "  text  "})
        self.assertEqual(data["title"], "Hello")
        self.assertEqual(data["content"], "text")
        self.assertEqual(data["status"], "draft")

    def test_invalid_url_is_rejected(self) -> None:
        with self.assertRaises(IntegrationPayloadValidationError) as context:
            IntegrationArticleService.validate_payload({"title": "Hello", "content": "Text", "source_url": "invalid"})
        self.assertIn("source_url", context.exception.details)

    @patch("services.article_service.ArticleRepository")
    def test_duplicate_uses_external_id_first(self, repository) -> None:
        expected = object()
        repository.get_by_external_id.return_value = expected
        found = ArticleService.find_duplicate_for_integration({"title": "Hello", "external_id": "rss-1", "source_url": "https://example.com"})
        self.assertIs(found, expected)
        repository.get_by_source_url.assert_not_called()

    @patch("services.article_service.ArticleRepository")
    def test_duplicate_uses_source_url_after_external_id(self, repository) -> None:
        expected = object()
        repository.get_by_external_id.return_value = None
        repository.get_by_source_url.return_value = expected
        found = ArticleService.find_duplicate_for_integration({"title": "Hello", "external_id": "rss-1", "source_url": "https://example.com"})
        self.assertIs(found, expected)
        repository.get_by_slug.assert_not_called()

    @patch("services.article_service.ArticleRepository")
    def test_duplicate_uses_slug_last(self, repository) -> None:
        expected = object()
        repository.get_by_slug.return_value = expected
        found = ArticleService.find_duplicate_for_integration({"title": "Hello World"})
        self.assertIs(found, expected)
        repository.get_by_slug.assert_called_once_with("hello-world")

    @patch("services.integration_article_service.ArticleService")
    def test_duplicate_does_not_create_or_reanalyze(self, article_service) -> None:
        article_service.find_duplicate_for_integration.return_value = SimpleNamespace(id=8)
        with patch("services.integration_article_service.ArticleAnalysisService") as analysis_service:
            analysis_service.return_value.get_analysis.return_value = None
            result = IntegrationArticleService.create_or_reuse({"title": "Hello", "content": "Text"})
        self.assertTrue(result.duplicate)
        article_service.create_article_with_analysis.assert_not_called()

