from pathlib import Path


TEMPLATE = (Path(__file__).resolve().parents[2] / "templates" / "articles" / "index.html").read_text(encoding="utf-8")


def test_workflow_template_contains_only_contextual_editorial_actions():
    assert "Enviar a revisión" in TEMPLATE
    assert "Aprobar" in TEMPLATE
    assert "Publicar" in TEMPLATE
    assert "Despublicar" in TEMPLATE
    assert "articles.transition_status" in TEMPLATE
