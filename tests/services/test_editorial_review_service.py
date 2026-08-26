from types import SimpleNamespace

import pytest

from ai.dto.editorial_review import EditorialReviewDTO
from core.ai_status import AIProcessingStatus
from core.exceptions import ArticleNotFoundError
from services.editorial_review_service import EditorialReviewService


class _AIService:
    def review_editorial_quality(self, article):
        return EditorialReviewDTO(
            overall_score=85, clarity_score=84, structure_score=83,
            summary_quality_score=82, title_content_alignment_score=81,
            readability_score=80, factual_risk_level="low", publication_readiness="ready",
            strengths=["Clara"], issues=[], recommendations=[], missing_information=[],
            status=AIProcessingStatus.COMPLETED, provider="test", model="test-model",
        )


class _Repository:
    article = None

    @classmethod
    def get_by_id(cls, _article_id):
        return cls.article


def _article():
    return SimpleNamespace(id=8, title="Título original", summary="Resumen original", content="Contenido original", status="approved", published_at=None, scheduled_publish_at=None)


def test_review_article_is_read_only_for_editorial_and_workflow_fields():
    article = _article()
    _Repository.article = article

    result = EditorialReviewService(_AIService(), _Repository).review_article(article.id)

    assert result.status == AIProcessingStatus.COMPLETED
    assert (article.title, article.summary, article.content) == ("Título original", "Resumen original", "Contenido original")
    assert article.status == "approved"
    assert article.published_at is None
    assert article.scheduled_publish_at is None


def test_review_article_rejects_a_missing_article():
    _Repository.article = None
    with pytest.raises(ArticleNotFoundError):
        EditorialReviewService(_AIService(), _Repository).review_article(999)
