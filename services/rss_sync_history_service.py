"""Lifecycle service for persistent RSS synchronization history."""
from datetime import datetime, timezone
from models import RSSSyncHistory
from repositories.rss_sync_history_repository import RSSSyncHistoryRepository


class RSSSyncHistoryService:
    @staticmethod
    def start(source_id, trigger_type):
        return RSSSyncHistoryRepository.create(RSSSyncHistory(source_id=source_id, trigger_type=trigger_type, status="failed", started_at=datetime.now(timezone.utc).replace(tzinfo=None)))

    @staticmethod
    def finish(history, result):
        finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
        history.finished_at = finished_at
        history.duration_ms = max(int((finished_at - history.started_at).total_seconds() * 1000), 0)
        history.status = "failed" if not result.success else "partial" if result.failed_count else "success"
        history.imported_count = result.imported_count
        history.duplicate_count = result.duplicate_count
        history.failed_count = result.failed_count
        history.total_entries = result.total_entries
        history.message = result.message[:500] if result.message else None
        return RSSSyncHistoryRepository.save(history)

    @staticmethod
    def recent(limit=50):
        return RSSSyncHistoryRepository.list_recent(limit)
