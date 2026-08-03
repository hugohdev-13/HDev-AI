"""Unit tests for ArticleAnalysisRepository transaction behavior."""

import unittest
from unittest.mock import MagicMock, patch

from models.article_analysis import ArticleAnalysis
from repositories.article_analysis_repository import ArticleAnalysisRepository


class ArticleAnalysisRepositoryTestCase(unittest.TestCase):
    """Verifies session interaction without a live SQL Server connection."""

    @patch("repositories.article_analysis_repository.db.session")
    def test_get_by_id_uses_session_get(self, session):
        analysis = ArticleAnalysis(id=1, article_id=1)
        session.get.return_value = analysis
        self.assertIs(ArticleAnalysisRepository.get_by_id(1), analysis)
        session.get.assert_called_once_with(ArticleAnalysis, 1)

    @patch("repositories.article_analysis_repository.db.session")
    def test_create_rolls_back_on_commit_error(self, session):
        session.commit.side_effect = RuntimeError("database error")
        with self.assertRaises(RuntimeError):
            ArticleAnalysisRepository.create(ArticleAnalysis(article_id=1))
        session.rollback.assert_called_once()

    @patch("repositories.article_analysis_repository.db.session")
    def test_count_by_status_uses_database_count(self, session):
        session.scalar.return_value = 2
        self.assertEqual(ArticleAnalysisRepository.count_by_status("completed"), 2)
