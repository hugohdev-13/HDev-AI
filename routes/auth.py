from urllib.parse import urljoin, urlparse

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)

from core.audit import log_audit_event
from services.auth_service import AuthService


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth",
)


def _is_safe_redirect_url(target: str) -> bool:
    """Allow redirects only to URLs hosted by this application."""
    if not target:
        return False

    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))

    return (
        redirect_url.scheme in {"http", "https"}
        and host_url.netloc == redirect_url.netloc
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = AuthService.authenticate(email, password)

        if user:
            login_user(user, remember=False)
            log_audit_event(
                "authentication.login",
                user_id=user.id,
            )

            next_url = request.args.get("next")

            if next_url and _is_safe_redirect_url(next_url):
                return redirect(next_url)

            return redirect(url_for("home.index"))

        flash(
            "Correo o contraseña incorrectos.",
            "danger",
        )

    return render_template("auth/login.html")


@auth_bp.get("/logout")
@login_required
def logout():
    log_audit_event(
        "authentication.logout",
        user_id=current_user.id,
    )

    logout_user()

    return redirect(url_for("auth.login"))