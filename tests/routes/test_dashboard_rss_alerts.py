from datetime import datetime
from types import SimpleNamespace

from flask import render_template

from app import app


def _health(status="operational", alerts=None):
    alerts = alerts or []
    return {
        "global_status": status,
        "total_active_rss_sources": len(alerts),
        "healthy_sources": 0,
        "warning_sources": sum(
            item["health"].health_status == "warning" for item in alerts
        ),
        "critical_sources": sum(
            item["health"].health_status == "critical" for item in alerts
        ),
        "never_synced_sources": 0,
        "attention_sources": alerts,
    }


def _render(health):
    dashboard_data = {
        "total_articles": 0,
        "published_articles": 0,
        "draft_articles": 0,
        "analyzed_articles": 0,
        "active_users": 0,
        "total_sources": 0,
        "recent_articles": [],
        "article_status_distribution": [],
        "top_technologies": [],
        "rss_health": health,
    }
    with app.test_request_context("/dashboard"):
        return render_template(
            "dashboard/index.html",
            dashboard_data=dashboard_data,
            current_user=SimpleNamespace(first_name="Admin", is_authenticated=True),
        )


def _alert(name, status, message):
    return {
        "source": SimpleNamespace(name=name),
        "health": SimpleNamespace(
            health_status=status,
            consecutive_failures=3 if status == "critical" else 1,
            last_success_at=datetime(2026, 8, 18, 20, 0),
            last_error_message=message,
        ),
    }


def test_dashboard_renders_operational_rss_state_without_alerts():
    page = _render(_health())
    assert "RSS: Operativo" in page
    assert "No hay alertas RSS activas." in page


def test_dashboard_renders_warning_and_history_link():
    page = _render(
        _health("attention_required", [_alert("TechCrunch", "warning", "Timeout")])
    )
    assert "RSS: Atención requerida" in page
    assert "TechCrunch" in page
    assert "Advertencia" in page
    assert 'href="/sources/sync-history"' in page


def test_dashboard_renders_critical_as_priority_visual_state():
    page = _render(
        _health("attention_required", [_alert("Critical Feed", "critical", "Timeout")])
    )
    assert "Crítica" in page
    assert "Acción prioritaria" in page
    assert "text-bg-danger" in page
