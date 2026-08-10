import logging

from flask import Flask, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

from config import get_config

from core.context_processors import register_context_processors
from core.audit import log_audit_event

from extensions import db, migrate, login_manager

from models import (
    Article,
    Category,
    Source,
    User,
    Role,
    Permission,
    RolePermission
)

from routes.home import home_bp
from routes.articles import articles_bp
from routes.api_articles import api_articles
from routes.api_integrations import api_integrations
from routes.auth import auth_bp
from routes.health import health_bp
from routes.public import public_bp
from routes.categories import categories_bp
from routes.sources import sources_bp


def create_app(config_object=None):

    app = Flask(__name__)

    app.config.from_object(config_object or get_config())
    if app.config.get("APP_ENV") == "production":
        # Azure App Service terminates TLS and forwards one trusted proxy hop.
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    logging.basicConfig(
        level=getattr(logging, app.config["LOG_LEVEL"], logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    register_context_processors(app)

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Debes iniciar sesión para continuar."
    login_manager.login_message_category = "warning"
    login_manager.session_protection = app.config["LOGIN_SESSION_PROTECTION"]

    app.register_blueprint(public_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(api_articles)
    app.register_blueprint(api_integrations)
    app.register_blueprint(articles_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(sources_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(health_bp)

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(error):
        app.logger.warning("Forbidden request path=%s", request.path)
        log_audit_event("authorization.forbidden", path=request.path)
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.exception("Unhandled internal server error")
        return render_template("errors/500.html"), 500

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
