"""Route coverage for the protected editorial review endpoint."""

from types import SimpleNamespace
from unittest.mock import patch

from ai.dto.editorial_review import EditorialReviewDTO
from app import app
from core.ai_status import AIProcessingStatus
from routes.articles import editorial_review


def _view():
    return editorial_review.__wrapped__.__wrapped__


def _review():
    return EditorialReviewDTO(
        overall_score=85, clarity_score=84, structure_score=83,
        summary_quality_score=82, title_content_alignment_score=81,
        readability_score=80, factual_risk_level="low", publication_readiness="ready",
        strengths=["Clara"], issues=[], recommendations=[], missing_information=[],
        status=AIProcessingStatus.COMPLETED, provider="openai", model="mock-openai",
    )


def test_editorial_review_requires_authenticated_editor():
    response = app.test_client().post("/articles/1/editorial-review")
    assert response.status_code == 302
    assert "/auth/login" in response.location


@patch("routes.articles.current_user", SimpleNamespace(id=7))
@patch("routes.articles.log_audit_event")
@patch("routes.articles.EditorialReviewService")
def test_editorial_review_returns_ephemeral_json(service, audit):
    service.return_value.review_article.return_value = _review()
    with app.test_request_context("/articles/1/editorial-review", method="POST"):
        response = _view()(1)

    assert response.status_code == 200
    assert response.get_json()["review"]["overall_score"] == 85
    service.return_value.review_article.assert_called_once_with(1)
    audit.assert_called_once()


def test_editorial_review_route_only_accepts_post():
    rules = [rule for rule in app.url_map.iter_rules() if rule.endpoint == "articles.editorial_review"]
    assert len(rules) == 1
    assert rules[0].methods == {"OPTIONS", "POST"}
