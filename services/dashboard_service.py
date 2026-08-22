"""Presentation-neutral dashboard aggregation service."""

from datetime import datetime, timezone

from repositories.dashboard_repository import DashboardRepository
from services.rss_source_health_service import RSSSourceHealthService
from services.source_service import SourceService


class DashboardService:
    """Build one safe dashboard data contract for routes and templates."""

    @staticmethod
    def get_dashboard_data() -> dict:
        repository = DashboardRepository
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        source_health = RSSSourceHealthService.get_health_summary(
            SourceService.get_active_rss_sources()
        )
        return {
            "total_articles": repository.total_articles() or 0,
            "published_articles": repository.published_articles() or 0,
            "draft_articles": repository.draft_articles() or 0,
            "review_articles": repository.review_articles() or 0,
            "approved_articles": repository.approved_articles() or 0,
            "scheduled_articles": repository.scheduled_articles() or 0,
            "analyzed_articles": repository.analyzed_articles() or 0,
            "total_users": repository.total_users() or 0,
            "active_users": repository.active_users() or 0,
            "total_sources": repository.total_sources() or 0,
            "recent_articles": repository.recent_articles(5) or [],
            "article_status_distribution": repository.article_status_distribution() or [],
            "top_technologies": repository.top_technologies(8) or [],
            "review_attention_articles": repository.articles_in_review(5) or [],
            "approved_pending_articles": repository.approved_pending_articles(5) or [],
            "upcoming_scheduled_articles": (
                repository.upcoming_scheduled_articles(now, 5) or []
            ),
            "overdue_scheduled_articles": (
                repository.overdue_scheduled_articles(now, 5) or []
            ),
            "recently_published_articles": repository.recently_published_articles(5)
            or [],
            "rss_health": source_health,
        }

    @staticmethod
    def get_dashboard_metrics() -> dict:
        """Preserve the prior public service contract during transition."""
        return DashboardService.get_dashboard_data()
