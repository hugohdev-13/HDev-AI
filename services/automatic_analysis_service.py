"""Policy service for optional synchronous automatic AI analysis."""

import logging
from dataclasses import asdict, dataclass
from typing import Any

from core.ai_config import AIConfig
from core.ai_status import AIProcessingStatus
from models import ArticleAnalysis
from services.article_analysis_service import ArticleAnalysisService


logger = logging.getLogger(__name__)
RELEVANT_ANALYSIS_FIELDS = frozenset({"title", "summary", "content"})


@dataclass(slots=True)
class AutomaticAnalysisResult:
    """Safe outcome of an automatic analysis attempt for routes and APIs."""

    triggered: bool
    status: str | None
    analysis_id: int | None
    message: str | None
    failed: bool = False

    def to_dict(self) -> dict[str, bool | str | int | None]:
        """Return a serializable result without internal exception details."""
        return asdict(self)


class AutomaticAnalysisService:
    """Decides when an already persisted article should be analyzed."""

    def __init__(self, analysis_service: ArticleAnalysisService | None = None, config: type[AIConfig] = AIConfig) -> None:
        self._analysis_service = analysis_service or ArticleAnalysisService()
        self._config = config

    def analyze_after_create(self, article: Any) -> AutomaticAnalysisResult:
        """Run optional analysis after creation without risking the article commit."""
        if not self._config.AI_AUTO_ANALYZE_ON_CREATE:
            logger.debug("Automatic AI analysis disabled for article creation")
            return self._not_triggered_result()
        if not self.is_article_eligible(article):
            logger.warning("Automatic AI analysis skipped for insufficient article content")
            return self._not_triggered_result("Article content is insufficient for analysis.")
        try:
            logger.info("Automatic AI analysis started article_id=%s", article.id)
            result = self._result_from_analysis(
                self._analysis_service.process_article(article.id)
            )
            logger.info(
                "Automatic AI analysis result article_id=%s analysis_id=%s status=%s",
                article.id,
                result.analysis_id,
                result.status,
            )
            return result
        except Exception:
            logger.exception("Automatic AI analysis failed after create article_id=%s", article.id)
            return AutomaticAnalysisResult(True, AIProcessingStatus.FAILED, None, "Automatic AI analysis failed.", True)

    def analyze_after_update(self, article: Any, changed_fields: set[str]) -> AutomaticAnalysisResult:
        """Retry optional analysis after relevant article content changes."""
        if not self.should_analyze_after_update(article, changed_fields):
            logger.debug("Automatic AI reanalysis skipped changed_fields=%s", changed_fields)
            return self._not_triggered_result()
        try:
            logger.info("Automatic AI reanalysis started article_id=%s fields=%s", article.id, sorted(changed_fields))
            return self._result_from_analysis(self._analysis_service.retry_analysis(article.id))
        except Exception:
            logger.exception("Automatic AI reanalysis failed article_id=%s", article.id)
            return AutomaticAnalysisResult(True, AIProcessingStatus.FAILED, None, "Automatic AI reanalysis failed.", True)

    def should_analyze_after_create(self, article: Any) -> bool:
        """Return whether creation analysis is enabled and the article is eligible."""
        return bool(self._config.AI_AUTO_ANALYZE_ON_CREATE and self.is_article_eligible(article))

    def should_analyze_after_update(self, article: Any, changed_fields: set[str]) -> bool:
        """Return whether configuration, eligibility, and changes allow retry."""
        if not self._config.AI_AUTO_ANALYZE_ON_UPDATE or not self.is_article_eligible(article):
            return False
        if not self._config.AI_REANALYZE_ON_CONTENT_CHANGE:
            return True
        return bool(RELEVANT_ANALYSIS_FIELDS.intersection(changed_fields))

    @staticmethod
    def is_article_eligible(article: Any) -> bool:
        """Require a title and meaningful content or summary before processing."""
        if article is None or not isinstance(getattr(article, "title", None), str):
            return False
        if not article.title.strip():
            return False
        return any(isinstance(value, str) and value.strip() for value in (getattr(article, "content", None), getattr(article, "summary", None)))

    @staticmethod
    def _not_triggered_result(message: str | None = None) -> AutomaticAnalysisResult:
        """Create a consistent result for disabled or ineligible analysis."""
        return AutomaticAnalysisResult(False, None, None, message)

    @staticmethod
    def _result_from_analysis(analysis: ArticleAnalysis) -> AutomaticAnalysisResult:
        """Map a persisted model to a safe automatic processing result."""
        failed = analysis.status == AIProcessingStatus.FAILED
        return AutomaticAnalysisResult(True, analysis.status, analysis.id, "Automatic AI analysis failed." if failed else None, failed)
