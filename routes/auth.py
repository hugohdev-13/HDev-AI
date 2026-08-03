from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    current_user,
    login_user,
    logout_user,
    login_required
)

from services.auth_service import AuthService
from core.audit import log_audit_event

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]

        user = AuthService.authenticate(
            email,
            password
        )

        if user:

            login_user(user)
            log_audit_event("authentication.login", user_id=user.id)

            return redirect(
                url_for("home.index")
            )

        flash(
            "Correo o contraseña incorrectos.",
            "danger"
        )

    return render_template("auth/login.html")


@auth_bp.get("/logout")
@login_required
def logout():

    log_audit_event("authentication.logout", user_id=current_user.id)
    logout_user()

    return redirect(
        url_for("auth.login")
    )
