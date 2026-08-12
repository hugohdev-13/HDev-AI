"""Manual RSS-entry import orchestration."""
from dataclasses import dataclass, field
from services.article_category_classifier import ArticleCategoryClassifier
from services.article_service import ArticleService
from services.category_service import CategoryService
from services.rss_feed_service import RSSFeedService
from services.source_service import SourceService
from repositories.source_repository import SourceRepository

@dataclass
class RSSImportResult:
    success: bool
    source_id: int
    total_entries: int = 0
    imported_count: int = 0
    duplicate_count: int = 0
    failed_count: int = 0
    analyzed_count: int = 0
    analysis_failed_count: int = 0
    categorized_count: int = 0
    uncategorized_count: int = 0
    imported_articles: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    message: str = ""

class RSSImportService:
    @staticmethod
    def import_source(source_id: int, limit: int = 20):
        source = SourceService.get_source(source_id)
        preview = RSSFeedService.get_entries(source, min(max(limit, 1), 50))
        if not preview.success:
            return RSSImportResult(False, source_id, message=preview.message, errors=[preview.message])
        result = RSSImportResult(True, source_id, total_entries=len(preview.entries))
        categories = CategoryService.get_active_categories()
        for entry in preview.entries:
            data = {"title": entry.title, "source_url": entry.url, "external_id": entry.external_id, "summary": entry.summary, "content": entry.summary or entry.title, "author": entry.author, "published_at": entry.published_at, "image_url": entry.image_url, "source_id": source_id, "category_id": None, "status": "draft"}
            try:
                if ArticleService.find_duplicate_for_integration(data):
                    result.duplicate_count += 1
                    continue
                mutation = ArticleService.create_article_with_analysis(data)
                article = mutation.article
                result.imported_articles.append(article)
                result.imported_count += 1
                if mutation.ai_analysis.failed:
                    result.analysis_failed_count += 1
                elif mutation.ai_analysis.triggered:
                    result.analyzed_count += 1
                category_id = ArticleCategoryClassifier.classify(mutation.ai_analysis, categories)
                if category_id:
                    ArticleService.update_article(article.id, {"title": article.title, "content": article.content, "status": article.status, "category_id": category_id})
                    result.categorized_count += 1
                else:
                    result.uncategorized_count += 1
            except Exception as error:
                result.failed_count += 1
                result.errors.append(str(error))
        source.last_sync_status = "partial" if result.failed_count else "success"
        source.last_sync_message = (
            f"Importados {result.imported_count}, duplicados "
            f"{result.duplicate_count}, errores {result.failed_count}."
        )
        SourceRepository.save(source)
        result.message = (
            f"Sincronización completada: {result.imported_count} importados, "
            f"{result.duplicate_count} duplicados, {result.failed_count} errores."
        )
        return result
