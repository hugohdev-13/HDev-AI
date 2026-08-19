"""Derived RSS source health calculations based on synchronization history."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterable

from repositories.rss_sync_history_repository import RSSSyncHistoryRepository


@dataclass(frozen=True)
class RSSSourceHealth:
    """Presentation-neutral health state for one RSS source."""

    source_id: int
    health_status: str
    consecutive_failures: int
    last_success_at: datetime | None
    last_failure_at: datetime | None
    last_error_message: str | None
    last_sync_at: datetime | None
    minutes_since_last_sync: int | None
    needs_attention: bool

    def to_dict(self) -> dict:
        """Expose a serializable representation for callers that need it."""
        return asdict(self)


class RSSSourceHealthService:
    """Calculate source health without persisting another operational state."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    NEVER_SYNCED = "never_synced"

    @classmethod
    def get_health_for_sources(
        cls,
        sources: Iterable,
        now: datetime | None = None,
    ) -> dict[int, RSSSourceHealth]:
        """Build health values for RSS sources using one history query."""
        rss_sources = [
            source
            for source in sources
            if getattr(source, "source_type", None) == "rss"
        ]
        source_ids = [source.id for source in rss_sources]
        histories_by_source = defaultdict(list)
        for history in RSSSyncHistoryRepository.list_by_source_ids(source_ids):
            histories_by_source[history.source_id].append(history)

        reference_time = cls._normalize_datetime(now or datetime.now(timezone.utc))
        return {
            source.id: cls._build_health(
                source,
                histories_by_source[source.id],
                reference_time,
            )
            for source in rss_sources
        }

    @classmethod
    def get_health_summary(
        cls,
        sources: Iterable,
        now: datetime | None = None,
    ) -> dict:
        """Return dashboard metrics plus the individual health contracts."""
        source_list = list(sources)
        health_by_source = cls.get_health_for_sources(source_list, now=now)
        statuses = [item.health_status for item in health_by_source.values()]
        return {
            "total_active_rss_sources": len(source_list),
            "healthy_sources": statuses.count(cls.HEALTHY),
            "warning_sources": statuses.count(cls.WARNING),
            "critical_sources": statuses.count(cls.CRITICAL),
            "never_synced_sources": statuses.count(cls.NEVER_SYNCED),
            "attention_sources": [
                {
                    "source": source,
                    "health": health_by_source[source.id],
                }
                for source in source_list
                if health_by_source[source.id].needs_attention
            ],
            "health_by_source": health_by_source,
        }

    @classmethod
    def _build_health(cls, source, histories: list, now: datetime) -> RSSSourceHealth:
        if not histories:
            return RSSSourceHealth(
                source_id=source.id,
                health_status=cls.NEVER_SYNCED,
                consecutive_failures=0,
                last_success_at=None,
                last_failure_at=None,
                last_error_message=None,
                last_sync_at=None,
                minutes_since_last_sync=None,
                needs_attention=False,
            )

        last_sync = histories[0]
        last_sync_at = cls._history_time(last_sync)
        last_success = next(
            (item for item in histories if item.status == "success"),
            None,
        )
        last_failure = next(
            (item for item in histories if item.status == "failed"),
            None,
        )
        consecutive_failures = cls._consecutive_failures(histories)
        minutes_since_last_sync = cls._minutes_between(last_sync_at, now)
        is_overdue = cls._is_overdue(source, last_sync_at, now)

        if consecutive_failures >= 3:
            health_status = cls.CRITICAL
        elif (
            last_sync.status == "partial"
            or consecutive_failures in {1, 2}
            or is_overdue
        ):
            health_status = cls.WARNING
        else:
            health_status = cls.HEALTHY

        return RSSSourceHealth(
            source_id=source.id,
            health_status=health_status,
            consecutive_failures=consecutive_failures,
            last_success_at=cls._history_time(last_success),
            last_failure_at=cls._history_time(last_failure),
            last_error_message=cls._safe_message(last_failure),
            last_sync_at=last_sync_at,
            minutes_since_last_sync=minutes_since_last_sync,
            needs_attention=health_status in {cls.WARNING, cls.CRITICAL},
        )

    @staticmethod
    def _consecutive_failures(histories: list) -> int:
        failures = 0
        for history in histories:
            if history.status != "failed":
                break
            failures += 1
        return failures

    @classmethod
    def _is_overdue(cls, source, last_sync_at: datetime | None, now: datetime) -> bool:
        if not getattr(source, "is_active", True) or last_sync_at is None:
            return False
        interval = max(int(getattr(source, "sync_interval_minutes", 60) or 60), 1)
        return cls._minutes_between(last_sync_at, now) > interval

    @staticmethod
    def _history_time(history) -> datetime | None:
        if history is None:
            return None
        return RSSSourceHealthService._normalize_datetime(
            getattr(history, "finished_at", None)
            or getattr(history, "started_at", None)
            or getattr(history, "created_at", None)
        )

    @staticmethod
    def _normalize_datetime(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    @staticmethod
    def _minutes_between(start: datetime | None, end: datetime) -> int | None:
        if start is None:
            return None
        return max(int((end - start).total_seconds() // 60), 0)

    @staticmethod
    def _safe_message(history) -> str | None:
        if history is None or not getattr(history, "message", None):
            return None
        # Display only one concise line: operational diagnostics, never traces.
        return " ".join(str(history.message).splitlines()[0].split())[:200] or None
