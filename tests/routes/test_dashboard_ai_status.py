from types import SimpleNamespace

from flask import render_template

from ai.dto.ai_health_status import AIHealthStatus
from app import app


def _dashboard_data(api_key=""):
    return {
        "total_articles": 0, "published_articles": 0, "draft_articles": 0,
        "review_articles": 0, "approved_articles": 0, "scheduled_articles": 0,
        "analyzed_articles": 0, "active_users": 0, "total_sources": 0,
        "recent_articles": [], "article_status_distribution": [], "top_technologies": [],
        "review_attention_articles": [], "approved_pending_articles": [],
        "upcoming_scheduled_articles": [], "overdue_scheduled_articles": [],
        "recently_published_articles": [],
        "rss_health": {"global_status": "operational", "total_active_rss_sources": 0,
                       "healthy_sources": 0, "warning_sources": 0, "critical_sources": 0,
                       "never_synced_sources": 0, "attention_sources": []},
        "ai_health": AIHealthStatus(
            provider="OpenAI", model="gpt-4.1-mini", configured=False,
            status="configuration_required", message="El proveedor de IA requiere configuración.",
            automatic_analysis_enabled=True, editorial_assistant_available=False,
            editorial_review_available=False,
        ),
        "analysis_metrics": {"completed": 3, "failed": 1, "pending": 2},
        "api_key": api_key,
    }


def test_dashboard_renders_safe_ai_status_and_persisted_analysis_metrics():
    secret = "sk-dashboard-secret"
    with app.test_request_context("/dashboard"):
        page = render_template(
            "dashboard/index.html", dashboard_data=_dashboard_data(secret),
            current_user=SimpleNamespace(first_name="Admin", is_authenticated=True),
            dashboard_timezone="America/Mexico_City", has_permission=lambda _permission: False,
        )

    assert "Estado de IA" in page
    assert "OpenAI" in page
    assert "gpt-4.1-mini" in page
    assert "Configuración requerida" in page
    assert "Análisis completados" in page
    assert "3" in page
    assert secret not in page
