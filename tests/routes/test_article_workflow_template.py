from pathlib import Path


TEMPLATE = (Path(__file__).resolve().parents[2] / "templates" / "articles" / "index.html").read_text(encoding="utf-8")


def test_workflow_template_contains_only_contextual_editorial_actions():
    assert "Enviar a revisión" in TEMPLATE
    assert "Aprobar" in TEMPLATE
    assert "Publicar" in TEMPLATE
    assert "Despublicar" in TEMPLATE
    assert "articles.transition_status" in TEMPLATE


def test_workflow_template_exposes_approved_article_schedule_controls():
    assert "scheduled_publish_at" in TEMPLATE
    assert "articles.schedule" in TEMPLATE
    assert "articles.cancel_schedule" in TEMPLATE
    assert "Programar" in TEMPLATE
    assert "Cancelar programación" in TEMPLATE
