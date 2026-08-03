"""Console reports backed by centralized administrative SQL queries."""

from database.query_runner import QueryRunner
from database.sql_queries import SQLQueries


def _print_query(query: str, parameters: dict | None = None) -> None:
    """Execute and print a reusable report query."""
    runner = QueryRunner()
    QueryRunner.print_results(runner.execute_select(query, parameters))


def print_articles() -> None:
    """Print all articles."""
    _print_query(SQLQueries.GET_ALL_ARTICLES)


def print_published_articles() -> None:
    """Print articles that are published."""
    _print_query(SQLQueries.GET_PUBLISHED_ARTICLES, {"status": "published"})


def print_article_analyses() -> None:
    """Print persisted AI article analyses."""
    _print_query(SQLQueries.GET_ANALYSES)


def print_users() -> None:
    """Print registered users and their roles."""
    _print_query(SQLQueries.GET_ALL_USERS)


def print_roles() -> None:
    """Print configured roles."""
    _print_query(SQLQueries.GET_ALL_ROLES)


def print_permissions() -> None:
    """Print configured permissions."""
    _print_query(SQLQueries.GET_ALL_PERMISSIONS)


def print_dashboard_summary() -> None:
    """Print dashboard-level database totals."""
    _print_query(SQLQueries.DASHBOARD_SUMMARY)


def main() -> None:
    """Run the default administrative dashboard report."""
    print_dashboard_summary()


if __name__ == "__main__":
    main()
