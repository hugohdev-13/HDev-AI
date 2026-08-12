from unittest.mock import patch

from app import app
from services.rss_scheduled_sync_service import RSSScheduledSyncResult


@patch("app.RSSScheduledSyncService.sync_all")
def test_sync_rss_cli_reports_empty_execution(sync_all):
    sync_all.return_value = RSSScheduledSyncResult()
    result = app.test_cli_runner().invoke(args=["sync-rss"])
    assert result.exit_code == 0
    assert "sources=0" in result.output
