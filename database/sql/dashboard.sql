SELECT
    (SELECT COUNT(*) FROM articles) AS total_articles,
    (SELECT COUNT(*) FROM categories) AS total_categories,
    (SELECT COUNT(*) FROM sources) AS total_sources,
    (SELECT COUNT(*) FROM users) AS total_users;
