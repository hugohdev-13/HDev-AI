from types import SimpleNamespace
from unittest.mock import patch

from dtos.rss_entry_dto import RSSEntryDTO
from services.rss_feed_service import RSSFeedResult
from services.rss_import_service import RSSImportService


def _entry():
    return RSSEntryDTO("Title", "https://example.com/a", "entry-1", "text", "Ada", None, None)


@patch("services.rss_import_service.CategoryService.get_active_categories", return_value=[])
@patch("services.rss_import_service.ArticleService.create_article_with_analysis")
@patch("services.rss_import_service.ArticleService.find_duplicate_for_integration", return_value=None)
@patch("services.rss_import_service.RSSFeedService.get_entries")
@patch("services.rss_import_service.SourceService.get_source", return_value=SimpleNamespace(id=1))
def test_new_rss_entry_calls_ai_once(_source, feed, duplicate, create, _categories):
    feed.return_value = RSSFeedResult(True, [_entry()], None, None)
    article = SimpleNamespace(id=3, title="Title", content="text", status="draft")
    create.return_value = SimpleNamespace(article=article, ai_analysis=SimpleNamespace(failed=False, triggered=True))
    result = RSSImportService.import_source(1)
    assert result.imported_count == 1
    assert result.analyzed_count == 1
    create.assert_called_once()


@patch("services.rss_import_service.RSSFeedService.get_entries")
@patch("services.rss_import_service.SourceService.get_source", return_value=SimpleNamespace(id=1))
@patch("services.rss_import_service.ArticleService.find_duplicate_for_integration", return_value=object())
@patch("services.rss_import_service.CategoryService.get_active_categories", return_value=[])
def test_duplicate_does_not_consume_ai(_categories, _duplicate, _source, feed):
    feed.return_value = RSSFeedResult(True, [_entry()], None, None)
    with patch("services.rss_import_service.ArticleService.create_article_with_analysis") as create:
        result = RSSImportService.import_source(1)
    assert result.duplicate_count == 1
    create.assert_not_called()
