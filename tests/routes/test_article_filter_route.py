"""Route tests for the article-list filter handoff without authentication IO."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app import app
from routes.articles import index


class ArticleFilterRouteTests(unittest.TestCase):
    """Exercise the original view after authentication is tested elsewhere."""

    def setUp(self):
        self.view = index.__wrapped__.__wrapped__
        self.pagination = SimpleNamespace(items=[], total=0)

    @patch("routes.articles.render_template")
    @patch("routes.articles.CategoryService.get_active_categories")
    @patch("routes.articles.ArticleService.get_paginated_articles")
    def test_route_passes_filters_and_active_categories(
        self, get_paginated, get_active_categories, render_template
    ):
        active_categories = [SimpleNamespace(id=3, name="Python")]
        get_paginated.return_value = self.pagination
        get_active_categories.return_value = active_categories

        with app.test_request_context(
            "/articles/?search=Flask&category=3&status=published&page=2"
        ):
            self.view()

        get_paginated.assert_called_once_with(
            page=2, search_term="Flask", category_id=3, status="published"
        )
        self.assertEqual(render_template.call_args.kwargs["categories"], active_categories)
        self.assertEqual(render_template.call_args.kwargs["selected_category_id"], 3)
        self.assertEqual(render_template.call_args.kwargs["selected_status"], "published")

    @patch("routes.articles.render_template")
    @patch("routes.articles.CategoryService.get_active_categories")
    @patch("routes.articles.ArticleService.get_paginated_articles")
    def test_invalid_filter_values_do_not_error(
        self, get_paginated, get_active_categories, render_template
    ):
        get_paginated.return_value = self.pagination
        get_active_categories.return_value = []

        with app.test_request_context("/articles/?category=abc&status=invalid"):
            self.view()

        get_paginated.assert_called_once_with(
            page=1, search_term="", category_id=None, status=None
        )
        self.assertIsNone(render_template.call_args.kwargs["selected_category_id"])
        self.assertIsNone(render_template.call_args.kwargs["selected_status"])

