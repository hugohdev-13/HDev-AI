"""Ephemeral AI editorial suggestions with no article mutation."""

from ai.dto.editorial_suggestion import EditorialSuggestionDTO
from ai.services.ai_service import AIService
from core.exceptions import ArticleNotFoundError
from repositories.article_repository import ArticleRepository


class EditorialAssistantService:
    """Load one article and obtain human-reviewable AI suggestions."""

    def __init__(
        self,
        ai_service: AIService | None = None,
        article_repository: type[ArticleRepository] = ArticleRepository,
    ) -> None:
        self._ai_service = ai_service or AIService()
        self._article_repository = article_repository

    def generate_suggestions(self, article_id: int) -> EditorialSuggestionDTO:
        """Return suggestions only; never persist or alter the loaded article."""
        article = self._article_repository.get_by_id(article_id)
        if article is None:
            raise ArticleNotFoundError(f"Article {article_id} was not found.")
        return self._ai_service.generate_editorial_suggestions(article)
