"""Application operations for article CRUD and optional automatic analysis."""

from dataclasses import dataclass
import logging
from typing import Any

from slugify import slugify

from models import Article
from repositories.article_repository import ArticleRepository
from services.automatic_analysis_service import AutomaticAnalysisResult, AutomaticAnalysisService


logger = logging.getLogger(__name__)

@dataclass(slots=True)
class ArticleUpdateResult:
    """Typed internal result for a saved article update and changed fields."""
    article: Article | None
    changed_fields: set[str]


@dataclass(slots=True)
class ArticleMutationResult:
    """Describes a persisted article and its automatic analysis outcome."""
    article: Article
    ai_analysis: AutomaticAnalysisResult
    changed_fields: set[str]


class ArticleService:
    """Manages articles without coupling CRUD to a concrete AI provider."""

    @staticmethod
    def get_articles():
        return ArticleRepository.get_all()

    @staticmethod
    def get_article(article_id):
        return ArticleRepository.get_by_id(article_id)

    @staticmethod
    def create_article(data: dict[str, Any]) -> Article:
        """Create and commit an article before any automatic analysis begins."""
        title = data["title"]
        base_slug = slugify(title)
        slug = base_slug
        counter = 2
        while ArticleRepository.get_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        article = Article(title=title, slug=slug, external_id=data.get("external_id"), summary=data.get("summary"), content=data.get("content"), image_url=data.get("image_url"), source_url=data.get("source_url"), author=data.get("author"), category_id=data.get("category_id"), source_id=data.get("source_id"), status=data.get("status", "draft"), published_at=data.get("published_at"))
        return ArticleRepository.create(article)

    @staticmethod
    def find_duplicate_for_integration(data: dict[str, Any]) -> Article | None:
        """Find an upstream duplicate using external ID, URL, then generated slug."""
        external_id = data.get("external_id")
        if external_id:
            article = ArticleRepository.get_by_external_id(external_id)
            if article is not None:
                return article

        source_url = data.get("source_url")
        if source_url:
            article = ArticleRepository.get_by_source_url(source_url)
            if article is not None:
                return article

        return ArticleRepository.get_by_slug(slugify(data["title"]))

    @staticmethod
    def create_article_with_analysis(data: dict[str, Any], automatic_analysis_service: AutomaticAnalysisService | None = None) -> ArticleMutationResult:
        """Create first, then safely request optional automatic analysis."""
        article = ArticleService.create_article(data)
        logger.info("Article created and committed article_id=%s", article.id)
        coordinator = automatic_analysis_service or AutomaticAnalysisService()
        analysis_result = coordinator.analyze_after_create(article)
        logger.info(
            "Automatic analysis finished article_id=%s triggered=%s analysis_id=%s status=%s",
            article.id,
            analysis_result.triggered,
            analysis_result.analysis_id,
            analysis_result.status,
        )
        return ArticleMutationResult(article, analysis_result, set())

    @staticmethod
    def delete_article(article_id):
        article = ArticleRepository.get_by_id(article_id)
        if article is None:
            return None
        ArticleRepository.delete(article)
        return True

    @staticmethod
    def update_article(article_id: int, data: dict[str, Any]) -> Article | None:
        """Update an article while preserving the original public return contract."""
        return ArticleService.update_article_with_changes(article_id, data).article

    @staticmethod
    def update_article_with_changes(article_id: int, data: dict[str, Any]) -> ArticleUpdateResult:
        """Persist real changes and expose their names through a typed result."""
        article = ArticleRepository.get_by_id(article_id)
        if article is None:
            return ArticleUpdateResult(None, set())
        changed_fields: set[str] = set()
        for field_name in ("title", "author", "summary", "content", "status"):
            current_value = getattr(article, field_name)
            new_value = data.get(field_name, current_value)
            if not ArticleService._values_equivalent(current_value, new_value):
                setattr(article, field_name, new_value)
                changed_fields.add(field_name)
        ArticleRepository.update()
        return ArticleUpdateResult(article, changed_fields)

    @staticmethod
    def update_article_with_analysis(article_id: int, data: dict[str, Any], automatic_analysis_service: AutomaticAnalysisService | None = None) -> ArticleMutationResult | None:
        """Update first, then safely request optional reanalysis."""
        update_result = ArticleService.update_article_with_changes(article_id, data)
        if update_result.article is None:
            return None
        coordinator = automatic_analysis_service or AutomaticAnalysisService()
        return ArticleMutationResult(update_result.article, coordinator.analyze_after_update(update_result.article, update_result.changed_fields), update_result.changed_fields)

    @staticmethod
    def search_articles(title=None):
        return ArticleRepository.search(title)

    @staticmethod
    def _values_equivalent(current_value: Any, new_value: Any) -> bool:
        """Treat optional empty strings and ``None`` as equivalent values."""
        return (current_value is None and new_value == "") or (current_value == "" and new_value is None) or current_value == new_value
