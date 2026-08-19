from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from services.rss_source_health_service import RSSSourceHealthService


NOW = datetime(2026, 8, 18, 12, 0)


def _source(source_id=1, interval=60, is_active=True):
    return SimpleNamespace(
        id=source_id,
        source_type="rss",
        sync_interval_minutes=interval,
        is_active=is_active,
        name=f"Source {source_id}",
    )


def _history(source_id, status, minutes_ago, message=None):
    timestamp = NOW - timedelta(minutes=minutes_ago)
    return SimpleNamespace(
        source_id=source_id,
        status=status,
        started_at=timestamp,
        finished_at=timestamp,
        created_at=timestamp,
        message=message,
    )


def _health(source, histories):
    with patch(
        "services.rss_source_health_service.RSSSyncHistoryRepository.list_by_source_ids",
        return_value=histories,
    ):
        return RSSSourceHealthService.get_health_for_sources([source], now=NOW)[source.id]


def test_never_synced_source_has_never_synced_health():
    health = _health(_source(), [])
    assert health.health_status == "never_synced"
    assert health.minutes_since_last_sync is None
    assert health.needs_attention is False


def test_recent_success_is_healthy_and_exposes_last_success():
    health = _health(_source(), [_history(1, "success", 10)])
    assert health.health_status == "healthy"
    assert health.consecutive_failures == 0
    assert health.last_success_at == NOW - timedelta(minutes=10)


def test_partial_execution_is_warning():
    health = _health(_source(), [_history(1, "partial", 10)])
    assert health.health_status == "warning"
    assert health.needs_attention is True


def test_one_or_two_consecutive_failures_are_warnings():
    one_failure = _health(_source(), [_history(1, "failed", 10, "one")])
    two_failures = _health(
        _source(),
        [_history(1, "failed", 10), _history(1, "failed", 20)],
    )
    assert one_failure.health_status == "warning"
    assert two_failures.health_status == "warning"
    assert two_failures.consecutive_failures == 2


def test_three_consecutive_failures_are_critical_and_expose_error():
    health = _health(
        _source(),
        [
            _history(1, "failed", 10, "Network timeout\ntraceback omitted"),
            _history(1, "failed", 20),
            _history(1, "failed", 30),
        ],
    )
    assert health.health_status == "critical"
    assert health.consecutive_failures == 3
    assert health.last_failure_at == NOW - timedelta(minutes=10)
    assert health.last_error_message == "Network timeout"


def test_recent_success_resets_previous_failure_streak():
    health = _health(
        _source(),
        [
            _history(1, "success", 5),
            _history(1, "failed", 15, "old error"),
            _history(1, "failed", 25),
        ],
    )
    assert health.health_status == "healthy"
    assert health.consecutive_failures == 0
    assert health.last_failure_at == NOW - timedelta(minutes=15)


def test_overdue_active_source_is_warning_but_inactive_source_is_not():
    overdue = _health(_source(interval=60), [_history(1, "success", 61)])
    inactive = _health(
        _source(interval=60, is_active=False),
        [_history(1, "success", 61)],
    )
    assert overdue.health_status == "warning"
    assert inactive.health_status == "healthy"


def test_health_summary_counts_attention_sources():
    sources = [_source(1), _source(2)]
    histories = [_history(1, "success", 5), _history(2, "failed", 5, "failed")]
    with patch(
        "services.rss_source_health_service.RSSSyncHistoryRepository.list_by_source_ids",
        return_value=histories,
    ):
        summary = RSSSourceHealthService.get_health_summary(sources, now=NOW)
    assert summary["total_active_rss_sources"] == 2
    assert summary["healthy_sources"] == 1
    assert summary["warning_sources"] == 1
    assert [item["source"].id for item in summary["attention_sources"]] == [2]
