"""Tests that editorial suggestions remain ephemeral and non-mutating."""

from types import SimpleNamespace

import pytest

from ai.dto.editorial_suggestion import EditorialSuggestionDTO
from core.ai_status import AIProcessingStatus
from core.exceptions import ArticleNotFoundError
from services.editorial_assistant_service import EditorialAssistantService


class _AIService:
    def generate_editorial_suggestions(self, article):
        return EditorialSuggestionDTO(
            suggested_title="Título sugerido",
            suggested_summary="Resumen sugerido",
            suggested_content="Contenido sugerido",
            suggested_category="Desarrollo de software",
            keywords=["Python"],
            technologies=["Flask"],
            notes="Revisar antes de guardar.",
            status=AIProcessingStatus.COMPLETED,
            provider="test",
            model="test-model",
        )


class _Repository:
    article = None

    @classmethod
    def get_by_id(cls, _article_id):
        return cls.article


def _article():
    return SimpleNamespace(
        id=8,
        title="Título original",
        summary="Resumen original",
        content="Contenido original",
        status="approved",
        published_at=None,
        scheduled_publish_at=None,
    )


def test_generate_suggestions_does_not_modify_article_or_editorial_state():
    article = _article()
    _Repository.article = article
    service = EditorialAssistantService(_AIService(), _Repository)

    result = service.generate_suggestions(article.id)

    assert result.status == AIProcessingStatus.COMPLETED
    assert article.title == "Título original"
    assert article.summary == "Resumen original"
    assert article.content == "Contenido original"
    assert article.status == "approved"
    assert article.published_at is None
    assert article.scheduled_publish_at is None


def test_generate_suggestions_rejects_missing_article():
    _Repository.article = None
    service = EditorialAssistantService(_AIService(), _Repository)

    with pytest.raises(ArticleNotFoundError):
        service.generate_suggestions(999)
