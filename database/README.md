# Database administration tools

`QueryRunner` is a console-only administrative utility. It creates the official Flask application with `create_app()` and uses `extensions.db`; it does not create an engine or direct ODBC connection.

## Run reports

```powershell
.\venv\Scripts\python.exe -m database.scripts.reports
.\venv\Scripts\python.exe -m database.scripts.diagnostics
```

Use individual reports from PowerShell:

```powershell
.\venv\Scripts\python.exe -c "from database.scripts.reports import print_articles; print_articles()"
```

## Run a query and export it

```python
from database.query_runner import QueryRunner
from database.sql_queries import SQLQueries

runner = QueryRunner()
results = runner.execute_select(SQLQueries.GET_ALL_ARTICLES)
runner.save_to_csv(results, "exports/articles.csv")
runner.save_to_json(results, "exports/articles.json")
```

Use parameterized SQL for dynamic values. Do not call `QueryRunner` from Flask routes; application routes must continue to use Service and Repository layers.

## Add a report

Add a reusable query to `database/sql_queries.py`, then create a small function in `database/scripts/reports.py` that sends it through `_print_query`.
