"""Provider-neutral, ephemeral suggestions for the article editor."""

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from core.ai_status import AIProcessingStatus


@dataclass(slots=True)
class EditorialSuggestionDTO:
    """Represents suggestions that require explicit human acceptance."""

    suggested_title: str
    suggested_summary: str
    suggested_content: str
    suggested_category: str
    keywords: list[str]
    technologies: list[str]
    notes: str
    status: str
    provider: str
    model: str
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe, normalized suggestion payload."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "EditorialSuggestionDTO":
        """Normalize provider output and reject unknown result statuses safely."""
        data = data or {}
        status = cls._string(data.get("status"))
        allowed_statuses = {
            AIProcessingStatus.COMPLETED,
            AIProcessingStatus.FAILED,
        }
        return cls(
            suggested_title=cls._string(data.get("suggested_title")),
            suggested_summary=cls._string(data.get("suggested_summary")),
            suggested_content=cls._string(data.get("suggested_content")),
            suggested_category=cls._string(data.get("suggested_category")),
            keywords=cls._strings(data.get("keywords")),
            technologies=cls._strings(data.get("technologies")),
            notes=cls._string(data.get("notes")),
            status=status if status in allowed_statuses else AIProcessingStatus.FAILED,
            provider=cls._string(data.get("provider")),
            model=cls._string(data.get("model")),
            error=cls._string(data.get("error")) or None,
        )

    @staticmethod
    def _string(value: Any) -> str:
        return value.strip() if isinstance(value, str) else ""

    @classmethod
    def _strings(cls, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        seen: set[str] = set()
        normalized: list[str] = []
        for item in value:
            normalized_item = cls._string(item)
            if normalized_item and normalized_item not in seen:
                seen.add(normalized_item)
                normalized.append(normalized_item)
        return normalized
