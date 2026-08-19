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
