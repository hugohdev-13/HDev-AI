"""Coverage for the editorial dashboard aggregation contract."""

from datetime import datetime
from unittest.mock import patch

from services.dashboard_service import DashboardService


def _rss_health():
    return {
        "global_status": "operational",
        "total_active_rss_sources": 0,
        "healthy_sources": 0,
        "warning_sources": 0,
        "critical_sources": 0,
        "never_synced_sources": 0,
        "attention_sources": [],
    }


@patch("services.dashboard_service.SourceService.get_active_rss_sources", return_value=[])
@patch("services.dashboard_service.RSSSourceHealthService.get_health_summary")
@patch("services.dashboard_service.DashboardRepository")
def test_dashboard_aggregates_editorial_counts_without_mutating_articles(
    repository,
    health_summary,
    _sources,
):
    repository.total_articles.return_value = 8
    repository.draft_articles.return_value = 2
    repository.review_articles.return_value = 1
    repository.approved_articles.return_value = 3
    repository.scheduled_articles.return_value = 1
    repository.published_articles.return_value = 2
    repository.analyzed_articles.return_value = 0
    repository.total_users.return_value = 0
    repository.active_users.return_value = 0
    repository.total_sources.return_value = 0
    repository.recent_articles.return_value = []
    repository.article_status_distribution.return_value = []
    repository.top_technologies.return_value = []
    repository.articles_in_review.return_value = []
    repository.approved_pending_articles.return_value = []
    repository.upcoming_scheduled_articles.return_value = []
    repository.overdue_scheduled_articles.return_value = []
    repository.recently_published_articles.return_value = []
    health_summary.return_value = _rss_health()

    dashboard_data = DashboardService.get_dashboard_data()

    assert dashboard_data["draft_articles"] == 2
    assert dashboard_data["review_articles"] == 1
    assert dashboard_data["approved_articles"] == 3
    assert dashboard_data["scheduled_articles"] == 1
    assert dashboard_data["published_articles"] == 2
    assert dashboard_data["rss_health"]["global_status"] == "operational"
    assert not hasattr(repository, "update") or not repository.update.called


@patch("services.dashboard_service.SourceService.get_active_rss_sources", return_value=[])
@patch("services.dashboard_service.RSSSourceHealthService.get_health_summary")
@patch("services.dashboard_service.DashboardRepository")
def test_dashboard_preserves_upcoming_and_overdue_article_lists(
    repository,
    health_summary,
    _sources,
):
    for method in (
        "total_articles",
        "draft_articles",
        "review_articles",
        "approved_articles",
        "scheduled_articles",
        "published_articles",
        "analyzed_articles",
        "total_users",
        "active_users",
        "total_sources",
    ):
        getattr(repository, method).return_value = 0
    repository.recent_articles.return_value = []
    repository.article_status_distribution.return_value = []
    repository.top_technologies.return_value = []
    repository.articles_in_review.return_value = []
    repository.approved_pending_articles.return_value = []
    repository.upcoming_scheduled_articles.return_value = [
        {"id": 2, "title": "Más próximo", "scheduled_publish_at": datetime(2026, 8, 21, 21, 0)},
        {"id": 3, "title": "Después", "scheduled_publish_at": datetime(2026, 8, 22, 21, 0)},
    ]
    repository.overdue_scheduled_articles.return_value = [
        {"id": 1, "title": "Vencido", "scheduled_publish_at": datetime(2026, 8, 20, 21, 0)}
    ]
    repository.recently_published_articles.return_value = []
    health_summary.return_value = _rss_health()

    dashboard_data = DashboardService.get_dashboard_data()

    assert [item["id"] for item in dashboard_data["upcoming_scheduled_articles"]] == [2, 3]
    assert dashboard_data["overdue_scheduled_articles"][0]["title"] == "Vencido"
