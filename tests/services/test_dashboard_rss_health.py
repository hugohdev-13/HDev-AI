from unittest.mock import patch

from services.dashboard_service import DashboardService


@patch("services.dashboard_service.SourceService.get_active_rss_sources", return_value=[])
@patch("services.dashboard_service.RSSSourceHealthService.get_health_summary")
@patch("services.dashboard_service.DashboardRepository")
def test_dashboard_data_includes_rss_health_summary(repository, health_summary, _sources):
    repository.total_articles.return_value = 0
    repository.published_articles.return_value = 0
    repository.draft_articles.return_value = 0
    repository.review_articles.return_value = 0
    repository.approved_articles.return_value = 0
    repository.scheduled_articles.return_value = 0
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
    health_summary.return_value = {
        "total_active_rss_sources": 0,
        "healthy_sources": 0,
        "warning_sources": 0,
        "critical_sources": 0,
        "never_synced_sources": 0,
        "attention_sources": [],
    }

    dashboard_data = DashboardService.get_dashboard_data()

    assert dashboard_data["rss_health"]["critical_sources"] == 0
    assert dashboard_data["scheduled_articles"] == 0
    assert dashboard_data["upcoming_scheduled_articles"] == []
    health_summary.assert_called_once_with([])
