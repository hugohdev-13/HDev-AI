"""Persistence operations for one-to-one article AI analyses."""

import logging

from sqlalchemy import func, select

from extensions import db
from models import ArticleAnalysis


logger = logging.getLogger(__name__)


class ArticleAnalysisRepository:
    """Encapsulates transactional access to ``ArticleAnalysis`` records."""

    @staticmethod
    def get_by_id(analysis_id: int) -> ArticleAnalysis | None:
        """Return an analysis by primary key."""
        return db.session.get(ArticleAnalysis, analysis_id)

    @staticmethod
    def get_by_article_id(article_id: int) -> ArticleAnalysis | None:
        """Return the single analysis associated with an article."""
        statement = select(ArticleAnalysis).where(ArticleAnalysis.article_id == article_id)
        return db.session.scalar(statement)

    @staticmethod
    def create(analysis: ArticleAnalysis) -> ArticleAnalysis:
        """Persist a new analysis and roll back safely on failure."""
        try:
            db.session.add(analysis)
            db.session.commit()
            logger.info(
                "Article analysis created analysis_id=%s article_id=%s status=%s",
                analysis.id,
                analysis.article_id,
                analysis.status,
            )
            return analysis
        except Exception as error:
            db.session.rollback()
            logger.exception("Unable to create article analysis")
            raise RuntimeError("Unable to create article analysis.") from error

    @staticmethod
    def save(analysis: ArticleAnalysis) -> ArticleAnalysis:
        """Commit changes to an existing analysis with rollback protection."""
        try:
            db.session.commit()
            logger.info(
                "Article analysis saved analysis_id=%s article_id=%s status=%s",
                analysis.id,
                analysis.article_id,
                analysis.status,
            )
            return analysis
        except Exception as error:
            db.session.rollback()
            logger.exception("Unable to save article analysis id=%s", analysis.id)
            raise RuntimeError("Unable to save article analysis.") from error

    @staticmethod
    def delete(analysis: ArticleAnalysis) -> None:
        """Delete an analysis and roll back safely on failure."""
        try:
            db.session.delete(analysis)
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            logger.exception("Unable to delete article analysis id=%s", analysis.id)
            raise RuntimeError("Unable to delete article analysis.") from error

    @staticmethod
    def get_by_status(status: str) -> list[ArticleAnalysis]:
        """Return analyses that share a processing status."""
        statement = select(ArticleAnalysis).where(ArticleAnalysis.status == status)
        return list(db.session.scalars(statement))

    @staticmethod
    def count_by_status(status: str) -> int:
        """Return the number of analyses in a processing status."""
        statement = (
            select(func.count())
            .select_from(ArticleAnalysis)
            .where(ArticleAnalysis.status == status)
        )
        return db.session.scalar(statement) or 0
