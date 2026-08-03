"""WSGI entry point for Azure App Service and Gunicorn."""

from app import create_app


application = create_app()
app = application
