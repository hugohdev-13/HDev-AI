from flask import Blueprint, render_template
from flask_login import login_required

from core.decorators import permission_required
from core.permissions import Permissions
from services.dashboard_service import DashboardService


home_bp = Blueprint("home", __name__)


@home_bp.route("/")
@login_required
@permission_required(Permissions.DASHBOARD_VIEW)
def index():
    metrics = DashboardService.get_dashboard_metrics()

    return render_template("dashboard/index.html", metrics=metrics)
