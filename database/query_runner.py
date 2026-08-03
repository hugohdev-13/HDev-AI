"""Administrative SQL execution utilities using the official application connection."""

import csv
import json
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import create_app
from extensions import db


logger = logging.getLogger(__name__)


class QueryRunner:
    """Executes administrative SQL within the configured Flask application context."""

    def __init__(self) -> None:
        """Create an application that reuses the project's configured extensions."""
        self.app = create_app()

    def execute_select(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a SELECT query and return serializable row dictionaries."""
        with self.app.app_context():
            try:
                result = db.session.execute(text(query), parameters or {})
                return [dict(row._mapping) for row in result.fetchall()]
            except SQLAlchemyError as error:
                db.session.rollback()
                logger.exception("Administrative SELECT query failed")
                raise RuntimeError("Unable to execute administrative SELECT query.") from error

    def execute_command(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> int:
        """Execute an administrative INSERT, UPDATE, or DELETE transaction."""
        with self.app.app_context():
            try:
                result = db.session.execute(text(query), parameters or {})
                db.session.commit()
                return result.rowcount
            except SQLAlchemyError as error:
                db.session.rollback()
                logger.exception("Administrative command query failed")
                raise RuntimeError("Unable to execute administrative command.") from error

    @staticmethod
    def print_results(results: list[dict[str, Any]]) -> None:
        """Print results in an aligned console table without external libraries."""
        if not results:
            print("No results found.")
            return

        columns = list(results[0])
        widths = {
            column: max(len(column), *(len(str(row.get(column, ""))) for row in results))
            for column in columns
        }
        header = " | ".join(column.ljust(widths[column]) for column in columns)
        separator = "-+-".join("-" * widths[column] for column in columns)

        print(header)
        print(separator)
        for row in results:
            print(" | ".join(str(row.get(column, "")).ljust(widths[column]) for column in columns))

    @staticmethod
    def save_to_csv(results: list[dict[str, Any]], filename: str | Path) -> Path:
        """Export results to a UTF-8 CSV file and return its resolved path."""
        path = Path(filename).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        columns = list(results[0]) if results else []
        with path.open("w", newline="", encoding="utf-8") as file_handle:
            writer = csv.DictWriter(file_handle, fieldnames=columns)
            writer.writeheader()
            writer.writerows(results)
        return path

    @staticmethod
    def save_to_json(results: list[dict[str, Any]], filename: str | Path) -> Path:
        """Export results to an indented UTF-8 JSON file and return its path."""
        path = Path(filename).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file_handle:
            json.dump(results, file_handle, ensure_ascii=False, indent=2, default=str)
        return path
