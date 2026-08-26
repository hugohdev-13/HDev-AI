"""Route coverage for the protected editorial suggestion endpoint."""

from types import SimpleNamespace
from unittest.mock import patch

from ai.dto.editorial_suggestion import EditorialSuggestionDTO
from app import app
from core.ai_status import AIProcessingStatus
from routes.articles import editorial_suggestions


def _view():
    return editorial_suggestions.__wrapped__.__wrapped__


def _suggestions():
    return EditorialSuggestionDTO(
        suggested_title="Título sugerido",
        suggested_summary="Resumen sugerido",
        suggested_content="Contenido sugerido",
        suggested_category="Desarrollo de software",
        keywords=["Python"],
        technologies=["Flask"],
        notes="Revisar.",
        status=AIProcessingStatus.COMPLETED,
        provider="openai",
        model="mock-openai",
    )


def test_editorial_suggestions_requires_authenticated_editor():
    response = app.test_client().post("/articles/1/editorial-suggestions")

    assert response.status_code == 302
    assert "/auth/login" in response.location


@patch("routes.articles.current_user", SimpleNamespace(id=7))
@patch("routes.articles.log_audit_event")
@patch("routes.articles.EditorialAssistantService")
def test_editorial_suggestions_returns_ephemeral_json(service, audit):
    service.return_value.generate_suggestions.return_value = _suggestions()
    with app.test_request_context("/articles/1/editorial-suggestions", method="POST"):
        response = _view()(1)

    assert response.status_code == 200
    assert response.get_json()["suggestions"]["suggested_title"] == "Título sugerido"
    service.return_value.generate_suggestions.assert_called_once_with(1)
    audit.assert_called_once()


def test_editorial_suggestions_route_only_accepts_post():
    rules = [
        rule
        for rule in app.url_map.iter_rules()
        if rule.endpoint == "articles.editorial_suggestions"
    ]

    assert len(rules) == 1
    assert rules[0].methods == {"OPTIONS", "POST"}
