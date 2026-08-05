"""Dashboard routes for HDev AI."""

from flask import Blueprint, render_template
from flask_login import login_required

from core.decorators import permission_required
from core.permissions import Permissions
from services.dashboard_service import DashboardService


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

    return render_template(
        "dashboard/index.html",
        dashboard_data=dashboard_data,
    )
