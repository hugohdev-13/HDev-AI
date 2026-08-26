"""Provider-neutral, ephemeral editorial quality reviews."""

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from core.ai_status import AIProcessingStatus


@dataclass(slots=True)
class EditorialReviewDTO:
    """Represent a human-advisory review without changing an article."""

    overall_score: int
    clarity_score: int
    structure_score: int
    summary_quality_score: int
    title_content_alignment_score: int
    readability_score: int
    factual_risk_level: str
    publication_readiness: str
    strengths: list[str]
    issues: list[str]
    recommendations: list[str]
    missing_information: list[str]
    status: str
    provider: str
    model: str
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe review payload."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "EditorialReviewDTO":
        """Normalize untrusted provider output into bounded review values."""
        data = data or {}
        status = cls._string(data.get("status"))
        allowed_statuses = {
            AIProcessingStatus.COMPLETED,
            AIProcessingStatus.FAILED,
        }
        return cls(
            overall_score=cls._score(data.get("overall_score")),
            clarity_score=cls._score(data.get("clarity_score")),
            structure_score=cls._score(data.get("structure_score")),
            summary_quality_score=cls._score(data.get("summary_quality_score")),
            title_content_alignment_score=cls._score(
                data.get("title_content_alignment_score")
            ),
            readability_score=cls._score(data.get("readability_score")),
            factual_risk_level=cls._choice(
                data.get("factual_risk_level"), {"low", "medium", "high"}, "medium"
            ),
            publication_readiness=cls._choice(
                data.get("publication_readiness"),
                {"ready", "needs_review", "not_ready"},
                "needs_review",
            ),
            strengths=cls._strings(data.get("strengths")),
            issues=cls._strings(data.get("issues")),
            recommendations=cls._strings(data.get("recommendations")),
            missing_information=cls._strings(data.get("missing_information")),
            status=(
                status if status in allowed_statuses else AIProcessingStatus.FAILED
            ),
            provider=cls._string(data.get("provider")),
            model=cls._string(data.get("model")),
            error=cls._string(data.get("error")) or None,
        )

    @staticmethod
    def _score(value: Any) -> int:
        """Coerce score values and clamp them to the public 0--100 scale."""
        try:
            return max(0, min(100, int(value)))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _string(value: Any) -> str:
        return value.strip() if isinstance(value, str) else ""

    @classmethod
    def _strings(cls, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [normalized for item in value if (normalized := cls._string(item))]

    @classmethod
    def _choice(cls, value: Any, allowed: set[str], default: str) -> str:
        normalized = cls._string(value).lower()
        return normalized if normalized in allowed else default
