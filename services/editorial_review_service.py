"""Read-only editorial quality review use case."""

from ai.dto.editorial_review import EditorialReviewDTO
from ai.services.ai_service import AIService
from core.exceptions import ArticleNotFoundError
from repositories.article_repository import ArticleRepository


class EditorialReviewService:
    """Load one article and request a non-persistent quality review."""

    def __init__(
        self,
        ai_service: AIService | None = None,
        article_repository: type[ArticleRepository] = ArticleRepository,
    ) -> None:
        self._ai_service = ai_service or AIService()
        self._article_repository = article_repository

    def review_article(self, article_id: int) -> EditorialReviewDTO:
        """Return an advisory review without mutating article fields or workflow."""
        article = self._article_repository.get_by_id(article_id)
        if article is None:
            raise ArticleNotFoundError(f"Article {article_id} was not found.")
        return self._ai_service.review_editorial_quality(article)
