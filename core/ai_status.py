"""Centralized processing states for article AI analysis."""


class AIProcessingStatus:
    """Defines string statuses compatible with SQL Server columns."""

    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
