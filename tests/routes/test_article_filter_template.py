"""Template contract tests for article-list filter navigation."""

from pathlib import Path
import unittest


TEMPLATE_PATH = (
    Path(__file__).resolve().parents[2] / "templates" / "articles" / "index.html"
)


class ArticleFilterTemplateTests(unittest.TestCase):
    """Keep filter controls and paging links aligned with the route contract."""

    @classmethod
    def setUpClass(cls):
        cls.template = TEMPLATE_PATH.read_text(encoding="utf-8")

    def test_pagination_preserves_every_filter(self):
        self.assertIn("search=search, category=selected_category_id", self.template)
        self.assertIn("status=selected_status", self.template)

    def test_empty_filtered_listing_and_clear_action_are_present(self):
        self.assertIn(
            "No se encontraron artículos con los filtros seleccionados.",
            self.template,
        )
        self.assertIn("Limpiar filtros", self.template)

    def test_active_category_selector_is_rendered(self):
        self.assertIn("{% for category in categories %}", self.template)
        self.assertIn("selected_category_id", self.template)
