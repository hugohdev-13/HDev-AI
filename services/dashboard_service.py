from repositories.dashboard_repository import DashboardRepository


class DashboardService:
    @staticmethod
    def get_dashboard_metrics():
        chart = DashboardRepository.articles_by_month()

        return {
            "articles": DashboardRepository.total_articles(),
            "categories": DashboardRepository.total_categories(),
            "sources": DashboardRepository.total_sources(),
            "users": DashboardRepository.total_users(),
            "latest_articles": DashboardRepository.latest_articles(),
            "chart": {
                "labels": [item["month"] for item in chart],
                "values": [item["count"] for item in chart],
            },
        }
