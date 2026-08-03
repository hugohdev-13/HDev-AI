"""Centralized permission codes for the HDev AI RBAC system."""


class Permissions:
    """Defines the canonical permission codes used by the application."""

    DASHBOARD_VIEW = "dashboard.view"

    ARTICLES_VIEW = "articles.view"
    ARTICLES_CREATE = "articles.create"
    ARTICLES_EDIT = "articles.edit"
    ARTICLES_DELETE = "articles.delete"

    CATEGORIES_VIEW = "categories.view"
    CATEGORIES_CREATE = "categories.create"
    CATEGORIES_EDIT = "categories.edit"
    CATEGORIES_DELETE = "categories.delete"

    SOURCES_VIEW = "sources.view"
    SOURCES_CREATE = "sources.create"
    SOURCES_EDIT = "sources.edit"
    SOURCES_DELETE = "sources.delete"

    USERS_VIEW = "users.view"
    USERS_CREATE = "users.create"
    USERS_EDIT = "users.edit"
    USERS_DELETE = "users.delete"

    ROLES_VIEW = "roles.view"
    ROLES_CREATE = "roles.create"
    ROLES_EDIT = "roles.edit"
    ROLES_DELETE = "roles.delete"

    SETTINGS_VIEW = "settings.view"
    SETTINGS_EDIT = "settings.edit"

    AI_ANALYSIS_VIEW = "ai_analysis.view"
    AI_ANALYSIS_PROCESS = "ai_analysis.process"
    AI_ANALYSIS_RETRY = "ai_analysis.retry"
