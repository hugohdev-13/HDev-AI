"""Dashboard routes for HDev AI."""

from flask import Blueprint, current_app, render_template
from flask_login import login_required

from core.decorators import permission_required
from core.permissions import Permissions
from services.dashboard_service import DashboardService
from services.article_scheduling_service import ArticleSchedulingService


home_bp = Blueprint(
    "home",
    __name__,
)


@home_bp.get("/dashboard")
@login_required
@permission_required(Permissions.DASHBOARD_VIEW)
def index():
    """Render the authenticated enterprise dashboard."""
    dashboard_data = DashboardService.get_dashboard_data()
    timezone_name = current_app.config["APP_TIMEZONE"]
    for article in dashboard_data["upcoming_scheduled_articles"]:
        article["scheduled_publish_at_local"] = (
            ArticleSchedulingService.utc_to_local(
                article.get("scheduled_publish_at"),
                timezone_name,
            )
        )

    return render_template(
        "dashboard/index.html",
        dashboard_data=dashboard_data,
        dashboard_timezone=timezone_name,
    )
