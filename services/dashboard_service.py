"""Presentation-neutral dashboard aggregation service."""

from repositories.dashboard_repository import DashboardRepository


class DashboardService:
    """Build one safe dashboard data contract for routes and templates."""

    @staticmethod
    def get_dashboard_data() -> dict:
        repository = DashboardRepository
        return {
            "total_articles": repository.total_articles() or 0,
            "published_articles": repository.published_articles() or 0,
            "draft_articles": repository.draft_articles() or 0,
            "analyzed_articles": repository.analyzed_articles() or 0,
            "total_users": repository.total_users() or 0,
            "active_users": repository.active_users() or 0,
            "total_sources": repository.total_sources() or 0,
            "recent_articles": repository.recent_articles(5) or [],
            "article_status_distribution": repository.article_status_distribution() or [],
            "top_technologies": repository.top_technologies(8) or [],
        }

    @staticmethod
    def get_dashboard_metrics() -> dict:
        """Preserve the prior public service contract during transition."""
        return DashboardService.get_dashboard_data()
