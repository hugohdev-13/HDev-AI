from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from services.rss_sync_history_service import RSSSyncHistoryService


@patch("services.rss_sync_history_service.RSSSyncHistoryRepository.save")
def test_finish_persists_counts_status_and_non_negative_duration(save):
    history = SimpleNamespace(started_at=datetime.now(), source_id=1)
    result = SimpleNamespace(success=True, failed_count=0, imported_count=2, duplicate_count=3, total_entries=5, message="ok")

    RSSSyncHistoryService.finish(history, result)

    assert history.status == "success"
    assert history.duration_ms >= 0
    assert history.imported_count == 2
    save.assert_called_once_with(history)
