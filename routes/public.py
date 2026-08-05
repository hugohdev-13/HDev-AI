"""Unauthenticated marketing routes."""
from flask import Blueprint, render_template
from flask_login import current_user
from services.public_service import PublicService

public_bp = Blueprint("public", __name__)


@public_bp.get("/")
def landing():
    return render_template("public/landing.html", landing_data=PublicService.get_landing_data(), is_authenticated=current_user.is_authenticated)
