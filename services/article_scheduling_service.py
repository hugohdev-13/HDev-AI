"""Scheduling operations for approved editorial articles."""

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from core.article_status import ArticleStatus
from repositories.article_repository import ArticleRepository
from services.article_workflow_service import ArticleWorkflowService


logger = logging.getLogger(__name__)


class ArticleSchedulingError(ValueError):
    """Raised when scheduling rules are not satisfied."""


@dataclass(slots=True)
class ScheduledPublicationSummary:
    """Serializable outcome for one due-publication pass."""

    total: int = 0
    published: int = 0
    failed: int = 0
    details: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class ArticleSchedulingService:
    """Schedule approved articles and publish due items through the workflow."""

    @staticmethod
    def schedule(article_id: int, scheduled_at: datetime):
        article = ArticleRepository.get_by_id(article_id)
        if article is None:
            return None
        if article.status != ArticleStatus.APPROVED:
            raise ArticleSchedulingError(
                "Solo los artículos aprobados pueden programarse."
            )
        scheduled_at = ArticleSchedulingService._normalize_datetime(scheduled_at)
        now = ArticleSchedulingService._utc_now()
        if scheduled_at is None or scheduled_at <= now:
            raise ArticleSchedulingError(
                "La fecha de publicación programada debe ser futura."
            )
        missing = ArticleWorkflowService.validate_editorial_readiness(article)
        if missing:
            raise ArticleSchedulingError(
                f"No se puede programar. Completa: {', '.join(missing)}."
            )
        article.scheduled_publish_at = scheduled_at
        ArticleRepository.update()
        return article

    @staticmethod
    def cancel(article_id: int):
        article = ArticleRepository.get_by_id(article_id)
        if article is None:
            return None
        article.scheduled_publish_at = None
        ArticleRepository.update()
        return article

    @staticmethod
    def publish_due_articles(
        now: datetime | None = None,
    ) -> ScheduledPublicationSummary:
        reference_time = (
            ArticleSchedulingService._normalize_datetime(now)
            or ArticleSchedulingService._utc_now()
        )
        due_articles = ArticleRepository.list_due_for_publication(reference_time)
        summary = ScheduledPublicationSummary(total=len(due_articles))
        logger.info("articles.publish_scheduled.started total=%s", summary.total)
        for article in due_articles:
            try:
                logger.info(
                    "articles.publish_scheduled.article.started article_id=%s",
                    article.id,
                )
                published = ArticleWorkflowService.transition(
                    article.id,
                    ArticleStatus.PUBLISHED,
                )
                if published is None:
                    raise ArticleSchedulingError("Artículo no encontrado.")
                published.scheduled_publish_at = None
                ArticleRepository.update()
                summary.published += 1
                summary.details.append({"article_id": article.id, "success": True})
                logger.info(
                    "articles.publish_scheduled.article.completed article_id=%s",
                    article.id,
                )
            except Exception as error:
                summary.failed += 1
                summary.details.append(
                    {"article_id": article.id, "success": False, "error": str(error)}
                )
                logger.exception(
                    "articles.publish_scheduled.article.failed article_id=%s",
                    article.id,
                )
        logger.info(
            "articles.publish_scheduled.completed total=%s published=%s failed=%s",
            summary.total,
            summary.published,
            summary.failed,
        )
        return summary

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)

    @staticmethod
    def local_to_utc(value: datetime, timezone_name: str) -> datetime:
        """Interpret a ``datetime-local`` value in the configured local zone."""
        try:
            local_timezone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as error:
            raise ArticleSchedulingError(
                "La zona horaria configurada no es válida."
            ) from error

        local_value = value
        if local_value.tzinfo is None:
            local_value = local_value.replace(tzinfo=local_timezone)
        else:
            local_value = local_value.astimezone(local_timezone)
        return ArticleSchedulingService._normalize_datetime(local_value)

    @staticmethod
    def utc_to_local(value: datetime | None, timezone_name: str) -> datetime | None:
        """Convert a UTC-naive persisted schedule into a display-local datetime."""
        if value is None:
            return None
        try:
            local_timezone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            return value
        return value.replace(tzinfo=timezone.utc).astimezone(local_timezone)

    @staticmethod
    def _normalize_datetime(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value
