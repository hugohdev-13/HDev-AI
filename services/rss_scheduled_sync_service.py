"""External-scheduler entry point for daily RSS synchronization."""

from dataclasses import asdict, dataclass, field
import logging

from services.rss_import_service import RSSImportService
from services.source_service import SourceService
from services.rss_sync_history_service import RSSSyncHistoryService


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RSSScheduledSyncResult:
    """Serializable aggregate result of one scheduler invocation."""

    total_sources: int = 0
    successful_sources: int = 0
    partial_sources: int = 0
    failed_sources: int = 0
    imported_count: int = 0
    duplicate_count: int = 0
    failed_count: int = 0
    results: dict[int, dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Return a plain structure suitable for CLI or scheduler reporting."""
        return asdict(self)


class RSSScheduledSyncService:
    """Synchronize eligible RSS sources without owning scheduling concerns."""

    @staticmethod
    def sync_all() -> RSSScheduledSyncResult:
        """Continue after per-source failures and aggregate every outcome."""
        eligible_sources = [
            source
            for source in SourceService.get_active_sources()
            if source.source_type == "rss"
        ]
        result = RSSScheduledSyncResult(total_sources=len(eligible_sources))
        logger.info("rss.sync.started total_sources=%s", result.total_sources)

        for source in eligible_sources:
            logger.info("rss.sync.source.started source_id=%s", source.id)
            history = RSSSyncHistoryService.start(source.id, "scheduled")
            try:
                source_result = RSSImportService.import_source(source.id)
                RSSSyncHistoryService.finish(history, source_result)
                result.results[source.id] = {
                    "success": source_result.success,
                    "imported_count": source_result.imported_count,
                    "duplicate_count": source_result.duplicate_count,
                    "failed_count": source_result.failed_count,
                    "message": source_result.message,
                }
                result.imported_count += source_result.imported_count
                result.duplicate_count += source_result.duplicate_count
                result.failed_count += source_result.failed_count

                if not source_result.success:
                    result.failed_sources += 1
                elif source_result.failed_count:
                    result.partial_sources += 1
                else:
                    result.successful_sources += 1
                logger.info(
                    "rss.sync.source.completed source_id=%s success=%s",
                    source.id,
                    source_result.success,
                )
            except Exception as error:
                class FailedResult:
                    success = False
                    imported_count = duplicate_count = failed_count = total_entries = 0
                    message = "No fue posible sincronizar la fuente."
                RSSSyncHistoryService.finish(history, FailedResult())
                result.failed_sources += 1
                result.failed_count += 1
                result.results[source.id] = {
                    "success": False,
                    "imported_count": 0,
                    "duplicate_count": 0,
                    "failed_count": 1,
                    "message": "No fue posible sincronizar la fuente.",
                }
                logger.exception("rss.sync.source.failed source_id=%s", source.id)

        logger.info(
            "rss.sync.completed total_sources=%s failed_sources=%s",
            result.total_sources,
            result.failed_sources,
        )
        return result
