"""Unit tests for automatic analysis decisions without SQL Server."""

import unittest
from types import SimpleNamespace

from core.ai_status import AIProcessingStatus
from models.article_analysis import ArticleAnalysis
from services.automatic_analysis_service import AutomaticAnalysisResult, AutomaticAnalysisService


class ConfigFake:
    AI_AUTO_ANALYZE_ON_CREATE = True
    AI_AUTO_ANALYZE_ON_UPDATE = True
    AI_REANALYZE_ON_CONTENT_CHANGE = True


class AnalysisServiceFake:
    def __init__(self, analysis=None, error=None):
        self.analysis = analysis or ArticleAnalysis(id=1, article_id=1, status=AIProcessingStatus.COMPLETED)
        self.error = error
        self.process_calls = 0
        self.retry_calls = 0

    def process_article(self, article_id):
        self.process_calls += 1
        if self.error:
            raise self.error
        return self.analysis

    def retry_analysis(self, article_id):
        self.retry_calls += 1
        if self.error:
            raise self.error
        return self.analysis


def config_with(**values):
    defaults = {"AI_AUTO_ANALYZE_ON_CREATE": True, "AI_AUTO_ANALYZE_ON_UPDATE": True, "AI_REANALYZE_ON_CONTENT_CHANGE": True}
    return type("Config", (), defaults | values)


class AutomaticAnalysisServiceTestCase(unittest.TestCase):
    article = SimpleNamespace(id=1, title="Flask", summary="", content="Contenido suficiente")

    def test_enabled_create_returns_completed_result(self):
        service = AnalysisServiceFake()
        result = AutomaticAnalysisService(service, ConfigFake).analyze_after_create(self.article)
        self.assertTrue(result.triggered)
        self.assertEqual(result.status, AIProcessingStatus.COMPLETED)
        self.assertEqual(service.process_calls, 1)

    def test_disabled_create_returns_not_triggered(self):
        service = AnalysisServiceFake()
        result = AutomaticAnalysisService(service, config_with(AI_AUTO_ANALYZE_ON_CREATE=False)).analyze_after_create(self.article)
        self.assertFalse(result.triggered)
        self.assertEqual(service.process_calls, 0)

    def test_missing_content_returns_not_triggered(self):
        result = AutomaticAnalysisService(AnalysisServiceFake(), ConfigFake).analyze_after_create(SimpleNamespace(id=1, title="Flask", summary="", content=""))
        self.assertFalse(result.triggered)

    def test_failure_returns_safe_failed_result(self):
        result = AutomaticAnalysisService(AnalysisServiceFake(error=RuntimeError("AI failure")), ConfigFake).analyze_after_create(self.article)
        self.assertTrue(result.triggered)
        self.assertTrue(result.failed)
        self.assertEqual(result.status, AIProcessingStatus.FAILED)

    def test_only_relevant_fields_trigger_reanalysis(self):
        service = AnalysisServiceFake()
        coordinator = AutomaticAnalysisService(service, ConfigFake)
        self.assertFalse(coordinator.analyze_after_update(self.article, {"status"}).triggered)
        self.assertTrue(coordinator.analyze_after_update(self.article, {"content"}).triggered)
        self.assertEqual(service.retry_calls, 1)

    def test_reanalysis_can_be_disabled(self):
        service = AnalysisServiceFake()
        result = AutomaticAnalysisService(service, config_with(AI_AUTO_ANALYZE_ON_UPDATE=False)).analyze_after_update(self.article, {"title"})
        self.assertFalse(result.triggered)
        self.assertEqual(service.retry_calls, 0)

    def test_result_is_serializable(self):
        self.assertEqual(AutomaticAnalysisResult(True, "completed", 1, None).to_dict()["analysis_id"], 1)
