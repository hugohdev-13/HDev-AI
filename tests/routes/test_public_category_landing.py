"""Public landing tests for dynamic category rendering."""

import unittest
from unittest.mock import patch

from app import app


class PublicCategoryLandingTests(unittest.TestCase):
    """The public landing remains available with populated or empty categories."""

    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    @patch("routes.public.PublicService.get_landing_data")
    def test_landing_returns_200_with_no_categories(self, get_landing_data):
        get_landing_data.return_value = {
            "statistics": {}, "recent_articles": [], "tutorials": [],
            "projects": [], "categories": [],
        }

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("No hay categorías públicas disponibles todavía.".encode(), response.data)

    @patch("routes.public.PublicService.get_landing_data")
    def test_landing_renders_an_active_public_category(self, get_landing_data):
        get_landing_data.return_value = {
            "statistics": {}, "recent_articles": [], "tutorials": [], "projects": [],
            "categories": [{"id": 1, "name": "HTML", "slug": "html", "description": "Web", "color": "#2563EB", "icon": "bi-code-square", "article_count": 1}],
        }

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"HTML", response.data)
        self.assertIn("1 artículo".encode(), response.data)
