"""Unit tests for the approved-article scheduling service."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from core.article_status import ArticleStatus
from services.article_scheduling_service import (
    ArticleSchedulingError,
    ArticleSchedulingService,
)


def _article(article_id=1, status=ArticleStatus.APPROVED):
    return SimpleNamespace(
        id=article_id,
        status=status,
        title="Artículo listo",
        slug="articulo-listo",
        summary="Resumen listo",
        content="Contenido listo",
        published_at=None,
        scheduled_publish_at=None,
    )


@patch("services.article_scheduling_service.ArticleRepository")
def test_schedule_keeps_approved_status_and_sets_future_date(repository):
    article = _article()
    repository.get_by_id.return_value = article
    scheduled_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)

    result = ArticleSchedulingService.schedule(article.id, scheduled_at)

    assert result is article
    assert article.status == ArticleStatus.APPROVED
    assert article.published_at is None
    assert article.scheduled_publish_at == scheduled_at
    repository.update.assert_called_once_with()


@patch("services.article_scheduling_service.ArticleRepository")
def test_schedule_rejects_non_approved_articles(repository):
    repository.get_by_id.return_value = _article(status=ArticleStatus.REVIEW)
    scheduled_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)

    with pytest.raises(ArticleSchedulingError, match="aprobados"):
        ArticleSchedulingService.schedule(1, scheduled_at)

    repository.update.assert_not_called()


@patch("services.article_scheduling_service.ArticleRepository")
def test_schedule_rejects_past_datetime(repository):
    repository.get_by_id.return_value = _article()
    past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)

    with pytest.raises(ArticleSchedulingError, match="futura"):
        ArticleSchedulingService.schedule(1, past)

    repository.update.assert_not_called()


def test_local_datetime_is_converted_to_utc_before_persistence():
    local_datetime = datetime(2026, 8, 21, 15, 0)

    result = ArticleSchedulingService.local_to_utc(
        local_datetime,
        "America/Mexico_City",
    )

    assert result == datetime(2026, 8, 21, 21, 0)


@patch("services.article_scheduling_service.ArticleRepository")
@patch.object(
    ArticleSchedulingService,
    "_utc_now",
    return_value=datetime(2026, 8, 21, 20, 0),
)
def test_future_mexico_city_local_datetime_is_accepted(_utc_now, repository):
    article = _article()
    repository.get_by_id.return_value = article
    local_future = datetime(2026, 8, 21, 15, 0)

    ArticleSchedulingService.schedule(
        article.id,
        ArticleSchedulingService.local_to_utc(
            local_future,
            "America/Mexico_City",
        ),
    )

    assert article.scheduled_publish_at == datetime(2026, 8, 21, 21, 0)


@patch("services.article_scheduling_service.ArticleRepository")
@patch.object(
    ArticleSchedulingService,
    "_utc_now",
    return_value=datetime(2026, 8, 21, 20, 0),
)
def test_past_mexico_city_local_datetime_is_rejected(_utc_now, repository):
    repository.get_by_id.return_value = _article()
    local_past = datetime(2026, 8, 21, 13, 0)

    with pytest.raises(ArticleSchedulingError, match="futura"):
        ArticleSchedulingService.schedule(
            1,
            ArticleSchedulingService.local_to_utc(
                local_past,
                "America/Mexico_City",
            ),
        )


@patch("services.article_scheduling_service.ArticleRepository")
def test_cancel_clears_schedule_without_changing_publication_state(repository):
    article = _article()
    article.scheduled_publish_at = datetime(2026, 9, 1, 12, 0)
    repository.get_by_id.return_value = article

    result = ArticleSchedulingService.cancel(article.id)

    assert result is article
    assert article.status == ArticleStatus.APPROVED
    assert article.published_at is None
    assert article.scheduled_publish_at is None
    repository.update.assert_called_once_with()


@patch("services.article_scheduling_service.ArticleRepository")
def test_publish_due_articles_returns_empty_summary_when_nothing_is_due(repository):
    repository.list_due_for_publication.return_value = []

    result = ArticleSchedulingService.publish_due_articles(datetime(2026, 8, 21, 12, 0))

    assert result.to_dict() == {
        "total": 0,
        "published": 0,
        "failed": 0,
        "details": [],
    }


@patch("services.article_scheduling_service.ArticleRepository")
def test_due_query_converts_aware_local_reference_time_to_utc(repository):
    repository.list_due_for_publication.return_value = []
    local_now = datetime(2026, 8, 21, 15, 0, tzinfo=ZoneInfo("America/Mexico_City"))

    ArticleSchedulingService.publish_due_articles(local_now)

    repository.list_due_for_publication.assert_called_once_with(
        datetime(2026, 8, 21, 21, 0)
    )


@patch("services.article_scheduling_service.ArticleWorkflowService.transition")
@patch("services.article_scheduling_service.ArticleRepository")
def test_publish_due_articles_clears_schedule_after_workflow_publish(
    repository,
    transition,
):
    article = _article()
    article.scheduled_publish_at = datetime(2026, 8, 21, 10, 0)
    repository.list_due_for_publication.return_value = [article]
    transition.return_value = article

    result = ArticleSchedulingService.publish_due_articles(datetime(2026, 8, 21, 12, 0))

    transition.assert_called_once_with(article.id, ArticleStatus.PUBLISHED)
    assert article.scheduled_publish_at is None
    assert result.published == 1
    assert result.failed == 0
    assert result.details == [{"article_id": article.id, "success": True}]


@patch("services.article_scheduling_service.ArticleWorkflowService.transition")
@patch("services.article_scheduling_service.ArticleRepository")
def test_publish_due_articles_isolates_failures_and_continues(repository, transition):
    first = _article(1)
    second = _article(2)
    repository.list_due_for_publication.return_value = [first, second]
    transition.side_effect = [RuntimeError("fallo controlado"), second]

    result = ArticleSchedulingService.publish_due_articles(datetime(2026, 8, 21, 12, 0))

    assert transition.call_count == 2
    assert result.total == 2
    assert result.published == 1
    assert result.failed == 1
    assert result.details[0]["article_id"] == 1
    assert result.details[0]["success"] is False
    assert result.details[1] == {"article_id": 2, "success": True}
