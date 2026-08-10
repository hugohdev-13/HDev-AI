"""Query-shape tests for public category aggregation."""

import inspect
import unittest

from repositories.public_repository import PublicRepository


class PublicCategoryRepositoryTests(unittest.TestCase):
    """Ensure the landing query stays aggregated and publication-only."""

    def test_query_filters_active_categories_and_published_articles(self):
        source = inspect.getsource(PublicRepository.public_categories)

        self.assertIn('Article.status == "published"', source)
        self.assertIn("Category.is_active == true()", source)
        self.assertIn("outerjoin", source)

    def test_query_orders_by_count_and_applies_limit(self):
        source = inspect.getsource(PublicRepository.public_categories)

        self.assertIn("article_count.desc()", source)
        self.assertIn("Category.name.asc()", source)
        self.assertIn(".limit(limit)", source)

