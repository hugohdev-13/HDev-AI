"""Safe, configuration-derived AI health contract for the dashboard."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AIHealthStatus:
    """Expose provider readiness without retaining or serializing secrets."""

    provider: str
    model: str
    configured: bool
    status: str
    message: str
    automatic_analysis_enabled: bool
    editorial_assistant_available: bool
    editorial_review_available: bool

    def to_dict(self) -> dict[str, Any]:
        """Return only safe, presentation-ready operational information."""
        return asdict(self)
