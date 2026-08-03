SELECT users.id, users.first_name, users.last_name, users.email, roles.name AS role_name
FROM users
INNER JOIN roles ON roles.id = users.role_id
ORDER BY users.created_at DESC;
