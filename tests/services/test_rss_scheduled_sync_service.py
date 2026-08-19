from types import SimpleNamespace
from unittest.mock import patch

from services.rss_import_service import RSSImportResult
from services.rss_scheduled_sync_service import RSSScheduledSyncService


@patch("services.rss_scheduled_sync_service.SourceService.get_active_sources", return_value=[])
def test_no_eligible_sources_returns_empty_summary(_sources):
    result = RSSScheduledSyncService.sync_all()
    assert result.total_sources == 0
    assert result.to_dict()["results"] == {}


@patch("services.rss_scheduled_sync_service.RSSImportService.import_source")
@patch("services.rss_scheduled_sync_service.SourceService.get_active_sources")
@patch("services.rss_scheduled_sync_service.RSSSyncHistoryService.finish")
@patch("services.rss_scheduled_sync_service.RSSSyncHistoryService.start", return_value=object())
def test_syncs_only_active_rss_sources(_start, _finish, sources, import_source):
    sources.return_value = [
        SimpleNamespace(id=1, source_type="rss"),
        SimpleNamespace(id=2, source_type="api"),
    ]
    import_source.return_value = RSSImportResult(
        True, 1, imported_count=2, duplicate_count=3
    )

    result = RSSScheduledSyncService.sync_all()

    import_source.assert_called_once_with(1)
    assert result.successful_sources == 1
    assert result.imported_count == 2
    assert result.duplicate_count == 3


@patch("services.rss_scheduled_sync_service.RSSImportService.import_source")
@patch("services.rss_scheduled_sync_service.SourceService.get_active_sources")
@patch("services.rss_scheduled_sync_service.RSSSyncHistoryService.finish")
@patch("services.rss_scheduled_sync_service.RSSSyncHistoryService.start", return_value=object())
def test_failure_isolated_and_next_source_continues(_start, _finish, sources, import_source):
    sources.return_value = [
        SimpleNamespace(id=1, source_type="rss"),
        SimpleNamespace(id=2, source_type="rss"),
    ]
    import_source.side_effect = [RuntimeError("fail"), RSSImportResult(True, 2)]

    result = RSSScheduledSyncService.sync_all()

    assert import_source.call_count == 2
    assert result.failed_sources == 1
    assert result.successful_sources == 1
    assert set(result.results) == {1, 2}
