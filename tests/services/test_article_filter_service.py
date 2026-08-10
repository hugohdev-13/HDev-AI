"""Unit tests for read-only article listing filters."""

import unittest
from unittest.mock import patch

from services.article_service import ArticleService


class ArticleFilterServiceTests(unittest.TestCase):
    """Ensure filters are normalized before reaching the repository layer."""

    @patch("services.article_service.ArticleRepository.paginate")
    def test_listing_without_filters_uses_safe_defaults(self, paginate):
        ArticleService.get_paginated_articles()

        paginate.assert_called_once_with(
            search_term="", category_id=None, status=None, page=1, per_page=10
        )

    @patch("services.article_service.ArticleRepository.paginate")
    def test_search_only_is_forwarded(self, paginate):
        ArticleService.get_paginated_articles(" Flask ", page=2)

        paginate.assert_called_once_with(
            search_term="Flask", category_id=None, status=None, page=2, per_page=10
        )

    @patch("services.article_service.ArticleRepository.paginate")
    def test_category_only_is_normalized(self, paginate):
        ArticleService.get_paginated_articles(category_id="3")

        paginate.assert_called_once_with(
            search_term="", category_id=3, status=None, page=1, per_page=10
        )

    @patch("services.article_service.ArticleRepository.paginate")
    def test_status_only_is_forwarded(self, paginate):
        ArticleService.get_paginated_articles(status="published")

        paginate.assert_called_once_with(
            search_term="", category_id=None, status="published", page=1, per_page=10
        )

    @patch("services.article_service.ArticleRepository.paginate")
    def test_combined_filters_are_forwarded(self, paginate):
        ArticleService.get_paginated_articles(
            "Python", category_id="4", status="draft", page=3, per_page=20
        )

        paginate.assert_called_once_with(
            search_term="Python", category_id=4, status="draft", page=3, per_page=20
        )

    def test_empty_category_and_status_do_not_filter(self):
        filters = ArticleService.normalize_list_filters("", "", "")

        self.assertEqual(
            filters, {"search_term": "", "category_id": None, "status": None}
        )

    def test_invalid_category_is_ignored_safely(self):
        for value in ("abc", "0", 0, -1):
            with self.subTest(value=value):
                self.assertIsNone(
                    ArticleService.normalize_list_filters(category_id=value)["category_id"]
                )

    def test_invalid_status_is_ignored_safely(self):
        self.assertIsNone(
            ArticleService.normalize_list_filters(status="unexpected")["status"]
        )

    def test_supported_statuses_are_preserved(self):
        for status in ("draft", "published", "archived"):
            with self.subTest(status=status):
                self.assertEqual(
                    ArticleService.normalize_list_filters(status=status)["status"], status
                )

