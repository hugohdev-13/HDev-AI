"""Persistence operations for RSS synchronization history."""
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from extensions import db
from models import RSSSyncHistory


class RSSSyncHistoryRepository:
    @staticmethod
    def create(history):
        db.session.add(history)
        db.session.commit()
        return history

    @staticmethod
    def save(history):
        db.session.commit()
        return history

    @staticmethod
    def get_by_id(history_id):
        return db.session.get(RSSSyncHistory, history_id)

    @staticmethod
    def list_recent(limit=50):
        statement = select(RSSSyncHistory).options(selectinload(RSSSyncHistory.source)).order_by(RSSSyncHistory.created_at.desc()).limit(limit)
        return list(db.session.scalars(statement))

    @staticmethod
    def list_by_source(source_id, limit=50):
        statement = select(RSSSyncHistory).where(RSSSyncHistory.source_id == source_id).order_by(RSSSyncHistory.created_at.desc()).limit(limit)
        return list(db.session.scalars(statement))

    @staticmethod
    def list_by_source_ids(source_ids: list[int]):
        """Return history ordered newest-first for a group of sources.

        The health service groups these rows in memory, avoiding one query per
        source while keeping the calculation derived from persisted history.
        """
        if not source_ids:
            return []

        statement = (
            select(RSSSyncHistory)
            .where(RSSSyncHistory.source_id.in_(source_ids))
            .order_by(
                RSSSyncHistory.source_id,
                RSSSyncHistory.created_at.desc(),
                RSSSyncHistory.id.desc(),
            )
        )
        return list(db.session.scalars(statement))
