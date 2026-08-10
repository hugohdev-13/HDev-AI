"""Tests for public category DTO normalization."""

import unittest
from unittest.mock import patch

from services.public_service import PublicService


class PublicCategoryServiceTests(unittest.TestCase):
    """Verify public categories are safe dictionaries for Jinja."""

    @patch("services.public_service.PublicRepository.public_categories")
    def test_none_description_and_missing_visual_metadata_use_fallbacks(self, source):
        source.return_value = [
            {
                "id": 1,
                "name": "HTML",
                "slug": "html",
                "description": None,
                "color": None,
                "icon": None,
                "article_count": None,
            }
        ]

        category = PublicService.get_public_categories()[0]

        self.assertEqual(category["description"], "")
        self.assertEqual(category["color"], "#2563EB")
        self.assertEqual(category["icon"], "bi-folder")
        self.assertEqual(category["article_count"], 0)

    @patch("services.public_service.PublicRepository.public_categories")
    def test_invalid_color_icon_and_negative_count_are_safe(self, source):
        source.return_value = [{"id": 1, "name": "AI", "slug": "ai", "color": "bad", "icon": "<script>", "article_count": -2}]

        category = PublicService.get_public_categories()[0]

        self.assertEqual(category["color"], "#2563EB")
        self.assertEqual(category["icon"], "bi-folder")
        self.assertEqual(category["article_count"], 0)

    @patch("services.public_service.PublicRepository.public_categories")
    def test_service_requests_at_most_four_categories_by_default(self, source):
        source.return_value = []

        self.assertEqual(PublicService.get_public_categories(), [])

        source.assert_called_once_with(4)

    @patch("services.public_service.PublicRepository.public_categories", return_value=[])
    @patch("services.public_service.PublicRepository.statistics", return_value={})
    @patch("services.public_service.PublicRepository.recent_published", return_value=[])
    def test_landing_data_contains_public_categories(self, *_mocks):
        self.assertIn("categories", PublicService.get_landing_data())

