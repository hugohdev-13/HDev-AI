"""Repository query-shape tests for Article eager-loading behavior."""

import inspect
import unittest

from repositories.article_repository import ArticleRepository


class ArticleRepositoryTestCase(unittest.TestCase):
    """Verify Article reads request the related category in the same load plan."""

    def test_article_read_methods_eager_load_category(self):
        for method in (
            ArticleRepository.get_all,
            ArticleRepository.get_by_id,
            ArticleRepository.search,
        ):
            self.assertIn(
                "selectinload(Article.category)",
                inspect.getsource(method),
            )

    def test_search_combines_category_and_status_filters(self):
        source = inspect.getsource(ArticleRepository.search)

        self.assertIn("Article.category_id == category_id", source)
        self.assertIn("Article.status == status", source)
