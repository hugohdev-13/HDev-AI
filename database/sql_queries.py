"""Centralized SQL statements for administrative reports and diagnostics."""


class SQLQueries:
    """Contains reusable read-only SQL used by database administration scripts."""

    GET_ALL_ARTICLES = """
        SELECT id, title, slug, author, status, created_at, updated_at
        FROM articles
        ORDER BY created_at DESC
    """
    GET_PUBLISHED_ARTICLES = """
        SELECT id, title, slug, author, published_at
        FROM articles
        WHERE status = :status
        ORDER BY published_at DESC
    """
    GET_ALL_USERS = """
        SELECT users.id, users.first_name, users.last_name, users.email,
               roles.name AS role_name, users.is_active, users.created_at
        FROM users
        INNER JOIN roles ON roles.id = users.role_id
        ORDER BY users.created_at DESC
    """
    GET_ALL_ROLES = "SELECT id, name, description, created_at FROM roles ORDER BY name"
    GET_ALL_PERMISSIONS = "SELECT id, code, name, description FROM permissions ORDER BY code"
    GET_ANALYSES = """
        SELECT article_analyses.id, article_analyses.article_id, articles.title,
               article_analyses.status, article_analyses.provider,
               article_analyses.model_used, article_analyses.processed_at
        FROM article_analyses
        INNER JOIN articles ON articles.id = article_analyses.article_id
        ORDER BY article_analyses.updated_at DESC
    """
    VERIFY_ARTICLE_ANALYSES = """
        SELECT
            a.id,
            a.title,
            aa.id AS analysis_id,
            aa.status
        FROM articles AS a
        LEFT JOIN article_analyses AS aa ON aa.article_id = a.id
        ORDER BY a.id DESC
    """
    DASHBOARD_SUMMARY = """
        SELECT
            (SELECT COUNT(*) FROM articles) AS total_articles,
            (SELECT COUNT(*) FROM categories) AS total_categories,
            (SELECT COUNT(*) FROM sources) AS total_sources,
            (SELECT COUNT(*) FROM users) AS total_users,
            (SELECT COUNT(*) FROM article_analyses) AS total_ai_analyses,
            (SELECT COUNT(*) FROM article_analyses WHERE status = 'pending') AS pending_analyses,
            (SELECT COUNT(*) FROM article_analyses WHERE status = 'completed') AS completed_analyses
    """
