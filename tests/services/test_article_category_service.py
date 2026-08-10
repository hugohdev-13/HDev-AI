"""Backend category-assignment tests for ArticleService without Azure SQL."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from services.article_service import ArticleService, ArticleValidationError
from services.automatic_analysis_service import AutomaticAnalysisResult


VALID = {"title": "Artículo válido", "content": "Contenido válido", "status": "draft"}


ARTICLE_STATE = VALID | {"author": None, "summary": None}


class ArticleCategoryServiceTests(unittest.TestCase):
    """Verify normalization and active-category rules at the service boundary."""

    def validate(self, category_id, category=None, current=None):
        with patch("services.article_service.CategoryService.get_category", return_value=category):
            return ArticleService.normalize_and_validate(VALID | {"category_id": category_id}, current)

    def test_missing_and_empty_category_are_none(self):
        self.assertIsNone(self.validate(None)["category_id"])
        self.assertIsNone(self.validate("")["category_id"])

    def test_numeric_string_and_integer_are_normalized(self):
        active = SimpleNamespace(is_active=True)
        self.assertEqual(self.validate("3", active)["category_id"], 3)
        self.assertEqual(self.validate(3, active)["category_id"], 3)

    def test_non_numeric_and_non_positive_ids_are_invalid(self):
        for value in ("abc", 0, -1):
            with self.assertRaises(ArticleValidationError) as context:
                self.validate(value)
            self.assertIn("category_id", context.exception.errors)

    def test_nonexistent_category_is_rejected(self):
        with self.assertRaises(ArticleValidationError) as context:
            self.validate(9, None)
        self.assertIn("category_id", context.exception.errors)

    def test_active_category_is_valid(self):
        self.assertEqual(self.validate(4, SimpleNamespace(is_active=True))["category_id"], 4)

    def test_inactive_category_is_rejected_on_create(self):
        with self.assertRaises(ArticleValidationError):
            self.validate(4, SimpleNamespace(is_active=False))

    def test_existing_inactive_category_can_be_preserved(self):
        result = self.validate(4, SimpleNamespace(is_active=False), current=4)
        self.assertEqual(result["category_id"], 4)

    def test_changing_to_other_inactive_category_is_rejected(self):
        with self.assertRaises(ArticleValidationError):
            self.validate(5, SimpleNamespace(is_active=False), current=4)

    @patch("services.article_service.ArticleRepository")
    def test_category_can_be_removed_on_edit(self, repository):
        article = SimpleNamespace(category_id=4, **ARTICLE_STATE)
        repository.get_by_id.return_value = article

        result = ArticleService.update_article_with_changes(
            1, VALID | {"category_id": ""}
        )

        self.assertIsNone(result.article.category_id)
        self.assertIn("category_id", result.changed_fields)
        repository.update.assert_called_once()

    @patch("services.article_service.ArticleRepository")
    @patch("services.article_service.CategoryService.get_category")
    def test_edit_keeps_same_active_category(self, get_category, repository):
        article = SimpleNamespace(category_id=4, **ARTICLE_STATE)
        get_category.return_value = SimpleNamespace(is_active=True)
        repository.get_by_id.return_value = article

        result = ArticleService.update_article_with_changes(1, VALID | {"category_id": "4"})

        self.assertEqual(result.article.category_id, 4)
        self.assertNotIn("category_id", result.changed_fields)
        repository.update.assert_called_once()

    @patch("services.article_service.ArticleRepository")
    @patch("services.article_service.CategoryService.get_category")
    def test_edit_keeps_same_inactive_category(self, get_category, repository):
        article = SimpleNamespace(category_id=4, **ARTICLE_STATE)
        get_category.return_value = SimpleNamespace(is_active=False)
        repository.get_by_id.return_value = article

        result = ArticleService.update_article_with_changes(1, VALID | {"category_id": 4})

        self.assertEqual(result.article.category_id, 4)
        repository.update.assert_called_once()

    @patch("services.article_service.ArticleRepository")
    @patch("services.article_service.CategoryService.get_category")
    def test_edit_can_change_to_another_active_category(self, get_category, repository):
        article = SimpleNamespace(category_id=4, **ARTICLE_STATE)
        get_category.return_value = SimpleNamespace(is_active=True)
        repository.get_by_id.return_value = article

        result = ArticleService.update_article_with_changes(1, VALID | {"category_id": "5"})

        self.assertEqual(result.article.category_id, 5)
        self.assertIn("category_id", result.changed_fields)

    @patch("services.article_service.ArticleRepository")
    @patch("services.article_service.CategoryService.get_category")
    def test_edit_rejects_another_inactive_category(self, get_category, repository):
        repository.get_by_id.return_value = SimpleNamespace(
            category_id=4, **ARTICLE_STATE
        )
        get_category.return_value = SimpleNamespace(is_active=False)

        with self.assertRaises(ArticleValidationError):
            ArticleService.update_article_with_changes(1, VALID | {"category_id": 5})

        repository.update.assert_not_called()

    @patch("services.article_service.ArticleRepository")
    @patch("services.article_service.CategoryService.get_category")
    def test_create_article_keeps_category_and_analysis_path(self, get_category, repository):
        get_category.return_value = SimpleNamespace(is_active=True)
        repository.get_by_slug.return_value = None
        repository.create.side_effect = lambda article: article
        article = ArticleService.create_article(VALID | {"category_id": "2"})
        self.assertEqual(article.category_id, 2)
        repository.create.assert_called_once()

    @patch("services.article_service.ArticleRepository")
    @patch("services.article_service.CategoryService.get_category")
    def test_create_with_category_preserves_automatic_analysis_flow(
        self, get_category, repository
    ):
        get_category.return_value = SimpleNamespace(is_active=True)
        repository.get_by_slug.return_value = None
        repository.create.side_effect = lambda article: article
        coordinator = MagicMock()
        coordinator.analyze_after_create.return_value = AutomaticAnalysisResult(
            True, "completed", 17, None
        )

        result = ArticleService.create_article_with_analysis(
            VALID | {"category_id": 2}, coordinator
        )

        self.assertEqual(result.article.category_id, 2)
        self.assertTrue(result.ai_analysis.triggered)
        coordinator.analyze_after_create.assert_called_once_with(result.article)
