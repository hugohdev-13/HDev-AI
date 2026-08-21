from types import SimpleNamespace
from unittest.mock import patch

from flask import get_flashed_messages

from app import app
from routes.articles import transition_status, update
from services.article_workflow_service import ArticleWorkflowError


def _view():
    return transition_status.__wrapped__.__wrapped__


@patch("routes.articles.current_user", SimpleNamespace(id=7))
@patch("routes.articles.log_audit_event")
@patch("routes.articles.ArticleWorkflowService.transition")
def test_valid_transition_uses_service_and_redirects(transition, audit):
    transition.return_value = SimpleNamespace(id=3, status="review")
    with app.test_request_context("/articles/3/status", method="POST", data={"status": "review"}):
        response = _view()(3)
    assert response.status_code == 302
    transition.assert_called_once()
    audit.assert_called_once()


@patch("routes.articles.current_user", SimpleNamespace(id=7))
@patch("routes.articles.ArticleWorkflowService.transition", side_effect=ArticleWorkflowError("No permitida"))
def test_invalid_transition_flashes_error_and_redirects(_transition):
    with app.test_request_context("/articles/3/status", method="POST", data={"status": "published"}):
        response = _view()(3)
    assert response.status_code == 302


def test_transition_route_requires_post():
    rules = [rule for rule in app.url_map.iter_rules() if rule.endpoint == "articles.transition_status"]
    assert len(rules) == 1
    assert rules[0].methods == {"OPTIONS", "POST"}


@patch("routes.articles.current_user", SimpleNamespace(id=7))
@patch("routes.articles.log_audit_event")
@patch("routes.articles.ArticleService.update_article_with_analysis")
def test_update_route_reads_workflow_regression_from_mutation_contract(
    update_article,
    _audit,
):
    update_article.return_value = SimpleNamespace(
        article=SimpleNamespace(id=3, status="review"),
        workflow_regressed=True,
        ai_analysis=SimpleNamespace(status="not_triggered", failed=False),
    )
    view = update.__wrapped__.__wrapped__
    with app.test_request_context(
        "/articles/3/edit",
        method="POST",
        data={"title": "Título", "content": "Contenido"},
    ):
        response = view(3)
        messages = get_flashed_messages(with_categories=True)
    assert response.status_code == 302
    assert ("warning", "El artículo fue modificado y regresó a revisión.") in messages
