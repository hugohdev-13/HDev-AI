from database.query_runner import QueryRunner

runner = QueryRunner()

results = runner.execute_select(
   "SELECT table_name FROM information_schema.tables WHERE table_type='HDevAI' "
)

runner.print_results(results)

from database.query_runner import QueryRunner
runner = QueryRunner()
results = runner.execute_select("SELECT id, title, status FROM articles")
runner.print_results(results)