"""Domain exceptions that can be handled without exposing internal details."""


class ArticleNotFoundError(Exception):
    """Raised when an article requested for analysis does not exist."""


class AIAnalysisProcessingError(Exception):
    """Raised when an analysis cannot be persisted safely."""
