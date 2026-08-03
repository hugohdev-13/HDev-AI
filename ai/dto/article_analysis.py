"""Normalized contract returned by AI article analysis providers."""

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from core.ai_status import AIProcessingStatus


VALID_STATUSES = frozenset(
    value
    for name, value in vars(AIProcessingStatus).items()
    if name.isupper() and isinstance(value, str)
)


@dataclass(slots=True)
class ArticleAnalysisDTO:
    """Represents a provider-neutral result from article analysis."""

    summary: str
    suggested_category: str
    difficulty: str
    technologies: list[str]
    keywords: list[str]
    sentiment: str
    provider: str
    model_used: str
    status: str
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of this analysis result."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "ArticleAnalysisDTO":
        """Build a valid DTO from external or mock provider data."""
        data = data or {}
        status = cls._string_value(data.get("status"))
        error_message = data.get("error_message")

        return cls(
            summary=cls._string_value(data.get("summary")),
            suggested_category=cls._string_value(data.get("suggested_category")),
            difficulty=cls._string_value(data.get("difficulty")),
            technologies=cls._normalize_string_list(data.get("technologies")),
            keywords=cls._normalize_string_list(data.get("keywords")),
            sentiment=cls._string_value(data.get("sentiment")),
            provider=cls._string_value(data.get("provider")),
            model_used=cls._string_value(data.get("model_used")),
            status=status if status in VALID_STATUSES else AIProcessingStatus.FAILED,
            error_message=cls._string_value(error_message) if error_message is not None else None,
        )

    @staticmethod
    def _string_value(value: Any) -> str:
        """Normalize optional scalar values into stripped strings."""
        return value.strip() if isinstance(value, str) else ""

    @staticmethod
    def _normalize_string_list(value: Any) -> list[str]:
        """Remove empty and duplicate string entries while keeping order."""
        if not isinstance(value, list):
            return []

        normalized_values: list[str] = []
        seen_values: set[str] = set()

        for item in value:
            if not isinstance(item, str):
                continue
            normalized_item = item.strip()
            if normalized_item and normalized_item not in seen_values:
                normalized_values.append(normalized_item)
                seen_values.add(normalized_item)

        return normalized_values
