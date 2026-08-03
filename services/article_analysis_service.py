"""Application service that analyzes and persists one article at a time."""

import logging

from ai.dto.article_analysis import ArticleAnalysisDTO
from ai.services.ai_service import AIService
from core.ai_status import AIProcessingStatus
from core.exceptions import AIAnalysisProcessingError, ArticleNotFoundError
from models import ArticleAnalysis
from repositories.article_analysis_repository import ArticleAnalysisRepository
from repositories.article_repository import ArticleRepository


logger = logging.getLogger(__name__)


class ArticleAnalysisService:
    """Coordinates article lookup, AI analysis, and transactional persistence."""

    def __init__(
        self,
        ai_service: AIService | None = None,
        article_repository: type[ArticleRepository] = ArticleRepository,
        analysis_repository: type[ArticleAnalysisRepository] = ArticleAnalysisRepository,
    ) -> None:
        self._ai_service = ai_service or AIService()
        self._article_repository = article_repository
        self._analysis_repository = analysis_repository

    def process_article(self, article_id: int, force: bool = False) -> ArticleAnalysis:
        """Analyze and persist an article while preserving a single analysis row."""
        article = self._article_repository.get_by_id(article_id)
        if article is None:
            raise ArticleNotFoundError(f"Article {article_id} was not found.")

        analysis = self._analysis_repository.get_by_article_id(article_id)
        if self._should_reuse_analysis(analysis, force):
            logger.info("Reusing article analysis article_id=%s status=%s", article_id, analysis.status)
            return analysis

        analysis = self._prepare_analysis(analysis, article_id)
        logger.info(
            "AI analysis processing started article_id=%s analysis_id=%s provider=%s",
            article_id,
            analysis.id,
            getattr(self._ai_service, "_provider", None).__class__.__name__,
        )

        try:
            dto = self._ai_service.analyze(article)
            if not isinstance(dto, ArticleAnalysisDTO):
                raise TypeError("AIService must return an ArticleAnalysisDTO.")
        except Exception:
            logger.exception("Unexpected AI analysis error article_id=%s", article_id)
            return self._persist_unexpected_failure(analysis)

        return self._persist_dto_result(analysis, dto)

    def get_analysis(self, article_id: int) -> ArticleAnalysis | None:
        """Return the analysis associated with an article, when present."""
        return self._analysis_repository.get_by_article_id(article_id)

    def retry_analysis(self, article_id: int) -> ArticleAnalysis:
        """Force reprocessing regardless of the current analysis status."""
        logger.info("AI analysis retry requested article_id=%s", article_id)
        return self.process_article(article_id, force=True)

    def get_status_counts(self) -> dict[str, int]:
        """Return counts for every central processing status."""
        statuses = [
            value
            for name, value in vars(AIProcessingStatus).items()
            if name.isupper() and isinstance(value, str)
        ]
        return {status: self._analysis_repository.count_by_status(status) for status in statuses}

    def _should_reuse_analysis(
        self,
        analysis: ArticleAnalysis | None,
        force: bool,
    ) -> bool:
        """Avoid duplicate provider calls for completed or active work."""
        return bool(
            analysis
            and not force
            and analysis.status
            in {AIProcessingStatus.COMPLETED, AIProcessingStatus.PROCESSING}
        )

    def _prepare_analysis(
        self,
        analysis: ArticleAnalysis | None,
        article_id: int,
    ) -> ArticleAnalysis:
        """Create if needed and persist PROCESSING before invoking AIService."""
        if analysis is None:
            analysis = ArticleAnalysis(
                article_id=article_id,
                status=AIProcessingStatus.PENDING,
            )
            try:
                analysis = self._analysis_repository.create(analysis)
            except RuntimeError as error:
                raise AIAnalysisProcessingError("Unable to initialize analysis.") from error

        analysis.mark_processing()
        try:
            return self._analysis_repository.save(analysis)
        except RuntimeError as error:
            raise AIAnalysisProcessingError("Unable to mark analysis as processing.") from error

    def _persist_dto_result(
        self,
        analysis: ArticleAnalysis,
        dto: ArticleAnalysisDTO,
    ) -> ArticleAnalysis:
        """Persist either a completed provider result or a provider failure."""
        if dto.status == AIProcessingStatus.COMPLETED:
            self._apply_dto(analysis, dto)
            analysis.mark_completed()
            logger.info(
                "AI analysis completed article_id=%s analysis_id=%s provider=%s",
                analysis.article_id,
                analysis.id,
                dto.provider,
            )
        else:
            analysis.provider = dto.provider or analysis.provider
            analysis.model_used = dto.model_used or analysis.model_used
            analysis.mark_failed(dto.error_message or "AI provider returned a failed analysis.")
            logger.warning(
                "AI analysis failed article_id=%s analysis_id=%s provider=%s",
                analysis.article_id,
                analysis.id,
                dto.provider,
            )

        try:
            return self._analysis_repository.save(analysis)
        except RuntimeError as error:
            logger.exception("AI analysis persistence failed article_id=%s", analysis.article_id)
            raise AIAnalysisProcessingError("Unable to persist AI analysis.") from error

    def _persist_unexpected_failure(self, analysis: ArticleAnalysis) -> ArticleAnalysis:
        """Persist a safe failed state after an unexpected provider exception."""
        analysis.mark_failed("AI analysis processing failed unexpectedly.")
        try:
            return self._analysis_repository.save(analysis)
        except RuntimeError as error:
            logger.exception("Unable to persist unexpected analysis failure article_id=%s", analysis.article_id)
            raise AIAnalysisProcessingError("Unable to persist AI analysis failure.") from error

    @staticmethod
    def _apply_dto(analysis: ArticleAnalysis, dto: ArticleAnalysisDTO) -> None:
        """Copy normalized DTO values onto the persistence model without commit."""
        analysis.summary = dto.summary
        analysis.suggested_category = dto.suggested_category
        analysis.difficulty = dto.difficulty
        analysis.technologies = dto.technologies
        analysis.keywords = dto.keywords
        analysis.sentiment = dto.sentiment
        analysis.provider = dto.provider
        analysis.model_used = dto.model_used
