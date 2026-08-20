from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from services.article_service import ArticleService, ArticleValidationError


def _article():
    return SimpleNamespace(
        id=1,
        title="Original",
        slug="original",
        summary="Antes",
        content="Contenido inicial",
        image_url=None,
        source_url="https://example.com/original",
        author="Autor",
        category_id=None,
        status="published",
        published_at=datetime(2026, 8, 1),
    )


@patch("services.article_service.ArticleRepository")
def test_editor_updates_explicit_content_fields_but_not_operational_fields(repository):
    article = _article()
    repository.get_by_id.return_value = article
    repository.get_by_slug.return_value = None
    payload = {
        "title": "Título editado",
        "slug": "titulo-editorial",
        "summary": "Resumen editado",
        "content": "Contenido editado",
        "author": "Editora",
        "image_url": "https://cdn.example.com/image.jpg",
        "source_url": "https://example.com/nueva-url",
        "category_id": "",
        "status": "draft",
        "published_at": None,
    }

    result = ArticleService.update_article_with_changes(1, payload)

    assert result.article.title == "Título editado"
    assert result.article.slug == "titulo-editorial"
    assert result.article.summary == "Resumen editado"
    assert result.article.content == "Contenido editado"
    assert result.article.author == "Editora"
    assert result.article.image_url == "https://cdn.example.com/image.jpg"
    assert result.article.source_url == "https://example.com/nueva-url"
    assert result.article.status == "published"
    assert result.article.published_at == datetime(2026, 8, 1)


@patch("services.article_service.ArticleRepository")
def test_editor_rejects_slug_owned_by_another_article(repository):
    repository.get_by_id.return_value = _article()
    repository.get_by_slug.return_value = SimpleNamespace(id=2)
    with pytest.raises(ArticleValidationError) as error:
        ArticleService.update_article_with_changes(
            1,
            {"title": "Título válido", "content": "Contenido válido", "slug": "ocupado"},
        )
    assert "slug" in error.value.errors


def test_editor_rejects_required_title_and_invalid_image_url():
    with pytest.raises(ArticleValidationError) as error:
        ArticleService.normalize_and_validate(
            {"title": " ", "content": "contenido", "image_url": "ftp://invalid"}
        )
    assert "title" in error.value.errors
    assert "image_url" in error.value.errors
