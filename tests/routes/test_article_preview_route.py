from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app import app
from routes.articles import preview


def _article(status):
    return SimpleNamespace(
        id=1,
        title="Artículo de prueba",
        status=status,
        published_at=datetime(2026, 8, 20) if status == "published" else None,
        created_at=datetime(2026, 8, 19),
        summary=None,
        content="Contenido editorial",
        author=None,
        category=None,
        image_url=None,
        source=None,
        source_url=None,
    )


def _view():
    return preview.__wrapped__.__wrapped__


def test_preview_redirects_anonymous_users_to_login():
    response = app.test_client().get("/articles/1/preview")
    assert response.status_code == 302
    assert "/auth/login" in response.location


@pytest.mark.parametrize("status", ["draft", "review", "approved", "published"])
@patch("routes.articles.current_user", SimpleNamespace(is_authenticated=True))
@patch("routes.articles.render_template")
@patch("routes.articles.ArticleService.get_article")
def test_preview_loads_every_editorial_state(get_article, render_template, status):
    article = _article(status)
    get_article.return_value = article
    with app.test_request_context("/articles/1/preview"):
        _view()(1)
    assert render_template.call_args.args[0] == "articles/preview.html"
    assert render_template.call_args.kwargs["article"] is article
    assert article.status == status
    if status == "published":
        assert article.published_at == datetime(2026, 8, 20)


@patch("routes.articles.ArticleService.get_article", return_value=None)
def test_preview_returns_404_for_missing_article(_get_article):
    with app.test_request_context("/articles/999/preview"):
        with pytest.raises(Exception) as error:
            _view()(999)
    assert getattr(error.value, "code", None) == 404
