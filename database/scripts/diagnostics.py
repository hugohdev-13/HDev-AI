"""Database connection diagnostics for administrators."""

import logging

from database.query_runner import QueryRunner


logger = logging.getLogger(__name__)


def check_database() -> dict[str, object]:
    """Collect and print SQL Server version, schema, migration, and connection state."""
    runner = QueryRunner()
    try:
        version = runner.execute_select("SELECT @@VERSION AS sql_server_version")[0]
        table_count = runner.execute_select(
            "SELECT COUNT(*) AS table_count FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
        )[0]
        migration = runner.execute_select("SELECT version_num FROM alembic_version")[0]
        diagnostics = {
            "connection_status": "connected",
            "sql_server_version": version["sql_server_version"],
            "table_count": table_count["table_count"],
            "migration": migration["version_num"],
        }
        QueryRunner.print_results([diagnostics])
        return diagnostics
    except RuntimeError:
        logger.exception("Database diagnostics failed")
        diagnostics = {"connection_status": "failed"}
        QueryRunner.print_results([diagnostics])
        return diagnostics


def main() -> None:
    """Run database connectivity diagnostics from the console."""
    check_database()


if __name__ == "__main__":
    main()
