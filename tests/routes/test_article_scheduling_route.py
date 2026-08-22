"""Route-level coverage for article scheduling actions."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from app import app
from routes.articles import cancel_schedule, schedule
from services.article_scheduling_service import ArticleSchedulingError


def _view(view):
    return view.__wrapped__.__wrapped__


def test_scheduling_routes_only_accept_post():
    rules = {
        rule.endpoint: rule
        for rule in app.url_map.iter_rules()
        if rule.endpoint in {"articles.schedule", "articles.cancel_schedule"}
    }

    assert rules["articles.schedule"].methods == {"OPTIONS", "POST"}
    assert rules["articles.cancel_schedule"].methods == {"OPTIONS", "POST"}


@patch("routes.articles.current_user", SimpleNamespace(id=7))
@patch("routes.articles.log_audit_event")
@patch("routes.articles.ArticleSchedulingService.schedule")
def test_schedule_route_delegates_to_service_and_redirects(schedule_article, audit):
    schedule_article.return_value = SimpleNamespace(id=3)
    with app.test_request_context(
        "/articles/3/schedule",
        method="POST",
        data={"scheduled_publish_at": "2026-09-01T10:30"},
    ):
        response = _view(schedule)(3)

    assert response.status_code == 302
    schedule_article.assert_called_once_with(3, datetime(2026, 9, 1, 16, 30))
    audit.assert_called_once()


@patch("routes.articles.current_user", SimpleNamespace(id=7))
@patch(
    "routes.articles.ArticleSchedulingService.schedule",
    side_effect=ArticleSchedulingError("Fecha no válida"),
)
def test_schedule_route_handles_business_validation_error(_schedule_article):
    with app.test_request_context(
        "/articles/3/schedule",
        method="POST",
        data={"scheduled_publish_at": "2026-09-01T10:30"},
    ):
        response = _view(schedule)(3)

    assert response.status_code == 302


@patch("routes.articles.current_user", SimpleNamespace(id=7))
@patch("routes.articles.log_audit_event")
@patch("routes.articles.ArticleSchedulingService.cancel")
def test_cancel_schedule_route_delegates_to_service_and_redirects(
    cancel_article,
    audit,
):
    cancel_article.return_value = SimpleNamespace(id=3)
    with app.test_request_context("/articles/3/cancel-schedule", method="POST"):
        response = _view(cancel_schedule)(3)

    assert response.status_code == 302
    cancel_article.assert_called_once_with(3)
    audit.assert_called_once()
