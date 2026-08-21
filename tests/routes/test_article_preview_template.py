from pathlib import Path


TEMPLATE = (Path(__file__).resolve().parents[2] / "templates" / "articles" / "preview.html").read_text(encoding="utf-8")
FORM = (Path(__file__).resolve().parents[2] / "templates" / "articles" / "form.html").read_text(encoding="utf-8")


def test_preview_template_uses_public_layout_and_contains_editorial_banner():
    assert 'extends "layouts/public.html"' in TEMPLATE
    assert "Vista previa editorial" in TEMPLATE
    assert "Volver al editor" in TEMPLATE
    assert "Volver a artículos" in TEMPLATE
    assert "Sin imagen destacada" in TEMPLATE


def test_existing_article_editor_offers_preview_without_exposing_status_input():
    assert "Vista previa" in FORM
    assert "articles.preview" in FORM
    assert 'name="status"' not in FORM
