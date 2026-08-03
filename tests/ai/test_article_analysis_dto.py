"""Unit tests for ArticleAnalysisDTO normalization."""

import unittest

from ai.dto.article_analysis import ArticleAnalysisDTO
from core.ai_status import AIProcessingStatus


class ArticleAnalysisDTOTestCase(unittest.TestCase):
    """Verifies safe DTO normalization without SQL Server."""

    def test_from_dict_normalizes_lists_and_status(self) -> None:
        result = ArticleAnalysisDTO.from_dict(
            {"technologies": ["Python", "", "Python", 4, " Flask "], "keywords": None, "status": "unknown"}
        )
        self.assertEqual(result.technologies, ["Python", "Flask"])
        self.assertEqual(result.keywords, [])
        self.assertEqual(result.status, AIProcessingStatus.FAILED)
