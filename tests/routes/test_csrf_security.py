"""End-to-end CSRF coverage for browser-session mutations."""

from unittest.mock import patch

from flask_login import UserMixin
from flask_wtf.csrf import generate_csrf

from app import app
from extensions import login_manager


def _csrf_token(client):
    raw_token = "test-csrf-session-token"
    with client.session_transaction() as session:
        session["csrf_token"] = raw_token
    with app.test_request_context():
        from flask import session

        session["csrf_token"] = raw_token
        return generate_csrf()


def test_administrative_and_editorial_posts_require_a_csrf_token():
    client = app.test_client()
    for path in (
        "/articles/1/editorial-suggestions",
        "/articles/1/editorial-review",
        "/articles/1/schedule",
        "/sources/1/import",
    ):
        assert client.post(path).status_code == 400


def test_valid_csrf_token_reaches_login_protection_for_editorial_ajax():
    client = app.test_client()
    token = _csrf_token(client)

    response = client.post(
        "/articles/1/editorial-suggestions",
        headers={"X-CSRFToken": token, "Accept": "application/json"},
    )

    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_logout_only_allows_post_and_invalidates_authenticated_session():
    client = app.test_client()
    assert client.get("/auth/logout").status_code == 405

    class User(UserMixin):
        id = 1

    user = User()
    token = _csrf_token(client)
    with client.session_transaction() as session:
        session["_user_id"] = "1"
        session["_fresh"] = True
    with patch.object(login_manager, "_user_callback", return_value=user):
        response = client.post("/auth/logout", data={"csrf_token": token})

    assert response.status_code == 302
    assert response.location.startswith("/auth/login")
    with client.session_transaction() as session:
        assert "_user_id" not in session


def test_editorial_javascript_sends_the_standard_csrf_header():
    assistant = (app.root_path + "/static/js/editorial_assistant.js")
    review = (app.root_path + "/static/js/editorial_review.js")

    assert '"X-CSRFToken"' in open(assistant, encoding="utf-8").read()
    assert '"X-CSRFToken"' in open(review, encoding="utf-8").read()
