from types import SimpleNamespace
from unittest.mock import patch

from services.rss_feed_service import RSSFeedResult
from services.rss_import_service import RSSImportService


@patch("services.rss_import_service.SourceRepository.save")
@patch("services.rss_import_service.CategoryService.get_active_categories", return_value=[])
@patch("services.rss_import_service.RSSFeedService.get_entries")
@patch("services.rss_import_service.SourceService.get_source")
def test_empty_sync_marks_source_success(source_get, feed, _categories, save):
    source = SimpleNamespace(id=1)
    source_get.return_value = source
    feed.return_value = RSSFeedResult(True, [], None, None)

    result = RSSImportService.import_source(1)

    assert result.success
    assert source.last_sync_status == "success"
    assert result.message == "Sincronización completada: 0 importados, 0 duplicados, 0 errores."
    save.assert_called_once_with(source)
