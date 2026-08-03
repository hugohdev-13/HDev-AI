"""Unit tests for ArticleAnalysisService without SQL Server."""

import unittest
from types import SimpleNamespace

from ai.dto.article_analysis import ArticleAnalysisDTO
from core.ai_status import AIProcessingStatus
from core.exceptions import ArticleNotFoundError
from models.article_analysis import ArticleAnalysis
from services.article_analysis_service import ArticleAnalysisService


class InMemoryAnalysisRepository:
    """Minimal analysis repository fake for service orchestration tests."""

    analysis = None
    saves = 0

    @classmethod
    def reset(cls):
        cls.analysis = None
        cls.saves = 0

    @classmethod
    def get_by_article_id(cls, article_id):
        return cls.analysis

    @classmethod
    def create(cls, analysis):
        analysis.id = 1
        cls.analysis = analysis
        return analysis

    @classmethod
    def save(cls, analysis):
        cls.analysis = analysis
        cls.saves += 1
        return analysis

    @classmethod
    def count_by_status(cls, status):
        return int(cls.analysis is not None and cls.analysis.status == status)


class ArticleRepositoryFake:
    """Article repository fake with a configurable result."""

    article = SimpleNamespace(id=1, title="Flask", content="Contenido técnico", summary="")

    @classmethod
    def get_by_id(cls, article_id):
        return cls.article if article_id == 1 else None


class AIServiceFake:
    """Injectable AI service fake with a configurable DTO or exception."""

    def __init__(self, result):
        self.result = result
        self.calls = 0

    def analyze(self, article):
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def completed_dto():
    """Return a representative completed DTO."""
    return ArticleAnalysisDTO("summary", "category", "basic", ["Python"], ["flask"], "neutral", "test", "test-model", AIProcessingStatus.COMPLETED)


class ArticleAnalysisServiceTestCase(unittest.TestCase):
    """Verifies lifecycle, reuse, retry, mapping, and status behavior."""

    def setUp(self):
        InMemoryAnalysisRepository.reset()
        ArticleRepositoryFake.article = SimpleNamespace(id=1, title="Flask", content="Contenido técnico", summary="")

    def service(self, ai_service):
        return ArticleAnalysisService(ai_service, ArticleRepositoryFake, InMemoryAnalysisRepository)

    def test_missing_article_raises_domain_error(self):
        with self.assertRaises(ArticleNotFoundError):
            self.service(AIServiceFake(completed_dto())).process_article(99)

    def test_new_analysis_persists_completed_dto(self):
        analysis = self.service(AIServiceFake(completed_dto())).process_article(1)
        self.assertEqual(analysis.status, AIProcessingStatus.COMPLETED)
        self.assertEqual(analysis.technologies, ["Python"])
        self.assertEqual(analysis.provider, "test")

    def test_completed_analysis_is_reused_without_force(self):
        existing = ArticleAnalysis(article_id=1, status=AIProcessingStatus.COMPLETED)
        InMemoryAnalysisRepository.analysis = existing
        ai_service = AIServiceFake(completed_dto())
        self.assertIs(self.service(ai_service).process_article(1), existing)
        self.assertEqual(ai_service.calls, 0)

    def test_force_reprocesses_existing_analysis(self):
        InMemoryAnalysisRepository.analysis = ArticleAnalysis(article_id=1, status=AIProcessingStatus.COMPLETED)
        ai_service = AIServiceFake(completed_dto())
        analysis = self.service(ai_service).process_article(1, force=True)
        self.assertEqual(ai_service.calls, 1)
        self.assertEqual(analysis.status, AIProcessingStatus.COMPLETED)

    def test_failed_dto_is_persisted(self):
        failed = ArticleAnalysisDTO("", "", "", [], [], "", "test", "model", AIProcessingStatus.FAILED, "mock error")
        analysis = self.service(AIServiceFake(failed)).process_article(1)
        self.assertEqual(analysis.status, AIProcessingStatus.FAILED)
        self.assertEqual(analysis.error_message, "mock error")

    def test_processing_analysis_is_reused(self):
        existing = ArticleAnalysis(article_id=1, status=AIProcessingStatus.PROCESSING)
        InMemoryAnalysisRepository.analysis = existing
        ai_service = AIServiceFake(completed_dto())
        self.assertIs(self.service(ai_service).process_article(1), existing)
        self.assertEqual(ai_service.calls, 0)

    def test_retry_forces_processing(self):
        InMemoryAnalysisRepository.analysis = ArticleAnalysis(article_id=1, status=AIProcessingStatus.COMPLETED)
        ai_service = AIServiceFake(completed_dto())
        self.service(ai_service).retry_analysis(1)
        self.assertEqual(ai_service.calls, 1)

    def test_status_counts_include_all_states(self):
        counts = self.service(AIServiceFake(completed_dto())).get_status_counts()
        self.assertEqual(set(counts), {"pending", "queued", "processing", "completed", "failed"})
