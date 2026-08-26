from ai.dto.editorial_review import EditorialReviewDTO
from core.ai_status import AIProcessingStatus


def test_editorial_review_dto_normalizes_scores_choices_and_lists():
    result = EditorialReviewDTO.from_dict(
        {
            "overall_score": 120, "clarity_score": "72", "structure_score": -2,
            "summary_quality_score": "invalid", "title_content_alignment_score": 83.9,
            "readability_score": 75, "factual_risk_level": "unknown",
            "publication_readiness": "invalid", "strengths": [" Clara ", "", 3],
            "issues": ["Falta contexto"], "recommendations": "not-a-list",
            "missing_information": ["Fuente primaria"],
            "status": AIProcessingStatus.COMPLETED, "provider": " test ", "model": " model ",
        }
    )

    assert result.overall_score == 100
    assert result.clarity_score == 72
    assert result.structure_score == 0
    assert result.summary_quality_score == 0
    assert result.title_content_alignment_score == 83
    assert result.factual_risk_level == "medium"
    assert result.publication_readiness == "needs_review"
    assert result.strengths == ["Clara"]
    assert result.recommendations == []
    assert result.provider == "test"


def test_editorial_review_dto_rejects_unknown_status_safely():
    assert EditorialReviewDTO.from_dict({"status": "unknown"}).status == AIProcessingStatus.FAILED
