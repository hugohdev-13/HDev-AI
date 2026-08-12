from types import SimpleNamespace
from unittest.mock import patch

from flask import render_template
from app import app
from routes.sources import edit


def test_edit_source_renders_existing_sqlalchemy_like_object():
    source = SimpleNamespace(id=7, name="OpenAI", website_url="https://openai.com", feed_url="https://openai.com/feed", source_type="rss", sync_interval_minutes=60, is_active=True)
    view = edit.__wrapped__.__wrapped__
    with app.test_request_context("/sources/7/edit"), patch("routes.sources.SourceService.get_source", return_value=source):
        response = view(7)
    assert "OpenAI" in response
    assert "https://openai.com/feed" in response


def test_form_renders_dictionary_after_validation_error():
    with app.test_request_context("/sources/new"):
        response = render_template(
            "sources/form.html",
            source=None,
            form_data={"name": "Bad", "source_type": "manual", "is_active": False},
            errors={"name": "Error"},
            mode="create",
        )
    assert "Bad" in response
    assert "Error" in response
