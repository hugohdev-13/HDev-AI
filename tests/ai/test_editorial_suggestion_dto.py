"""Tests for the isolated editorial-suggestion contract."""

from ai.dto.editorial_suggestion import EditorialSuggestionDTO
from core.ai_status import AIProcessingStatus


def test_editorial_suggestion_dto_normalizes_untrusted_provider_data():
    result = EditorialSuggestionDTO.from_dict(
        {
            "suggested_title": " Título ",
            "keywords": ["Python", "", "Python", 1],
            "status": "unexpected",
            "error": 99,
        }
    )

    assert result.suggested_title == "Título"
    assert result.keywords == ["Python"]
    assert result.status == AIProcessingStatus.FAILED
    assert result.error is None
