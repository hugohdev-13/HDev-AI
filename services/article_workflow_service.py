"""Business service for controlled editorial article transitions."""

from datetime import datetime, timezone

from core.article_status import ArticleStatus
from repositories.article_repository import ArticleRepository


class ArticleWorkflowError(ValueError):
    """Raised when an editorial state change is not allowed."""


class ArticleWorkflowService:
    """Apply server-side editorial transitions without HTTP coupling."""

    @staticmethod
    def transition(article_id: int, target_status: str, actor=None):
        """Transition an article, updating publication time consistently."""
        article = ArticleRepository.get_by_id(article_id)
        if article is None:
            return None

        target = (target_status or "").strip().lower()
        if not ArticleStatus.is_valid(target):
            raise ArticleWorkflowError("El estado editorial solicitado no es válido.")
        if not ArticleStatus.can_transition(article.status, target):
            raise ArticleWorkflowError(
                "La transición editorial solicitada no está permitida."
            )

        article.status = target
        if target == ArticleStatus.PUBLISHED and article.published_at is None:
            article.published_at = datetime.now(timezone.utc).replace(tzinfo=None)
        elif target == ArticleStatus.DRAFT:
            article.published_at = None
        ArticleRepository.update()
        return article
