"""Application operations for article CRUD and optional automatic analysis."""

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import Any

from slugify import slugify

from models import Article
from repositories.article_repository import ArticleRepository
from services.category_service import CategoryService
from services.automatic_analysis_service import AutomaticAnalysisResult, AutomaticAnalysisService


logger = logging.getLogger(__name__)


class ArticleValidationError(ValueError):
    """Business validation error with field-specific Spanish messages."""
    def __init__(self, errors: dict[str, str]):
        self.errors = errors
        super().__init__("Datos de artículo inválidos")

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
        data = ArticleService.normalize_and_validate(data)
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
        data = ArticleService.normalize_and_validate(data, article.category_id)
        changed_fields: set[str] = set()
        for field_name in ("title", "author", "summary", "content", "status", "category_id"):
            current_value = getattr(article, field_name)
            new_value = data.get(field_name, current_value)
            if not ArticleService._values_equivalent(current_value, new_value):
                setattr(article, field_name, new_value)
                changed_fields.add(field_name)
        if article.status == "published" and article.published_at is None:
            article.published_at = datetime.now(timezone.utc).replace(tzinfo=None)
            changed_fields.add("published_at")
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
    def search_articles(search_term=None):
        return ArticleRepository.search((search_term or "").strip())

    @staticmethod
    def get_paginated_articles(search_term: str, page: int):
        return ArticleRepository.paginate((search_term or "").strip(), page, 10)

    @staticmethod
    def normalize_and_validate(data: dict[str, Any], current_category_id: int | None = None) -> dict[str, Any]:
        """Normalize form input and enforce article business invariants."""
        normalized = {field: (value.strip() if isinstance(value, str) else value) for field, value in data.items()}
        errors = {}
        title, content, status = normalized.get("title", ""), normalized.get("content", ""), normalized.get("status", "draft")
        raw_category_id = normalized.get("category_id")
        if raw_category_id in (None, "", "0"):
            normalized["category_id"] = None
        else:
            try:
                category_id = int(raw_category_id)
                category = CategoryService.get_category(category_id)
                if category is None:
                    errors["category_id"] = "La categoría seleccionada no existe."
                elif not category.is_active and category_id != current_category_id:
                    errors["category_id"] = "La categoría seleccionada no está activa."
                normalized["category_id"] = category_id
            except (TypeError, ValueError):
                errors["category_id"] = "La categoría seleccionada no es válida."
        if not isinstance(title, str) or not 3 <= len(title) <= 250: errors["title"] = "El título debe tener entre 3 y 250 caracteres."
        if not isinstance(content, str) or not content: errors["content"] = "El contenido es obligatorio."
        if status not in {"draft", "published", "archived"}: errors["status"] = "El estado seleccionado no es válido."
        if errors: raise ArticleValidationError(errors)
        return normalized

    @staticmethod
    def _values_equivalent(current_value: Any, new_value: Any) -> bool:
        """Treat optional empty strings and ``None`` as equivalent values."""
        return (current_value is None and new_value == "") or (current_value == "" and new_value is None) or current_value == new_value
