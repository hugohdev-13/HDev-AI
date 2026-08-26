"""Data transfer objects for the AI analysis layer."""

from .article_analysis import ArticleAnalysisDTO
from .ai_health_status import AIHealthStatus
from .editorial_review import EditorialReviewDTO
from .editorial_suggestion import EditorialSuggestionDTO

__all__ = [
    "ArticleAnalysisDTO",
    "AIHealthStatus",
    "EditorialReviewDTO",
    "EditorialSuggestionDTO",
]
