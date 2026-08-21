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
        """Transition an article after validating its editorial readiness."""
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

        if target in {
            ArticleStatus.REVIEW,
            ArticleStatus.APPROVED,
            ArticleStatus.PUBLISHED,
        }:
            missing_fields = ArticleWorkflowService.validate_editorial_readiness(
                article,
                require_unique_slug=target == ArticleStatus.PUBLISHED,
            )
            if missing_fields:
                action = {
                    ArticleStatus.REVIEW: "enviar a revisión",
                    ArticleStatus.APPROVED: "aprobar",
                    ArticleStatus.PUBLISHED: "publicar",
                }[target]
                raise ArticleWorkflowError(
                    f"No se puede {action}. Completa: {', '.join(missing_fields)}."
                )

        article.status = target
        if target == ArticleStatus.PUBLISHED and article.published_at is None:
            article.published_at = datetime.now(timezone.utc).replace(tzinfo=None)
        # published_at is retained when unpublished as a historical timestamp.
        ArticleRepository.update()
        return article

    @staticmethod
    def validate_editorial_readiness(
        article,
        require_unique_slug: bool = False,
    ) -> list[str]:
        """Return missing editorial fields without coupling to a route."""
        fields = {
            "título": getattr(article, "title", None),
            "slug": getattr(article, "slug", None),
            "resumen": getattr(article, "summary", None),
            "contenido": getattr(article, "content", None),
        }
        missing = [
            label
            for label, value in fields.items()
            if not isinstance(value, str) or not value.strip()
        ]
        if require_unique_slug and "slug" not in missing:
            existing = ArticleRepository.get_by_slug(article.slug)
            if existing is not None and existing.id != article.id:
                missing.append("slug único")
        return missing
