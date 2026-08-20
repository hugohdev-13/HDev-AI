from pathlib import Path


TEMPLATE = (Path(__file__).resolve().parents[2] / "templates" / "articles" / "form.html").read_text(encoding="utf-8")


def test_editor_includes_supported_fields_and_image_preview():
    for field in ("title", "slug", "summary", "content", "image_url", "author", "category_id", "source_url"):
        assert f'name="{field}"' in TEMPLATE
    assert "Vista previa de la imagen" in TEMPLATE
    assert "Sin imagen destacada." in TEMPLATE


def test_editor_excludes_mutable_status_and_published_at_inputs():
    assert 'name="status"' not in TEMPLATE
    assert 'name="published_at"' not in TEMPLATE
    assert "Fuente original" in TEMPLATE
