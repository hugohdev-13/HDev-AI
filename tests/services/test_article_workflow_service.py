from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from services.article_workflow_service import (
    ArticleWorkflowError,
    ArticleWorkflowService,
)


def _article(status, published_at=None):
    return SimpleNamespace(
        id=1,
        status=status,
        published_at=published_at,
        title="Título editorial",
        slug="titulo-editorial",
        summary="Resumen editorial",
        content="Contenido editorial",
    )


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("draft", "review"),
        ("review", "draft"),
        ("review", "approved"),
        ("approved", "review"),
        ("approved", "published"),
        ("published", "draft"),
    ],
)
@patch("services.article_workflow_service.ArticleRepository")
def test_allowed_editorial_transitions_are_persisted(repository, current, target):
    article = _article(current, datetime(2026, 8, 1) if current == "published" else None)
    repository.get_by_id.return_value = article
    repository.get_by_slug.return_value = None

    result = ArticleWorkflowService.transition(1, target)

    assert result is article
    assert article.status == target
    repository.update.assert_called_once()


@pytest.mark.parametrize(
    ("current", "target"),
    [("draft", "published"), ("draft", "approved"), ("review", "published")],
)
@patch("services.article_workflow_service.ArticleRepository")
def test_invalid_editorial_transitions_do_not_change_article(repository, current, target):
    article = _article(current)
    repository.get_by_id.return_value = article

    with pytest.raises(ArticleWorkflowError):
        ArticleWorkflowService.transition(1, target)

    assert article.status == current
    repository.update.assert_not_called()


@patch("services.article_workflow_service.ArticleRepository")
def test_publishing_sets_published_at_and_unpublishing_retains_it(repository):
    article = _article("approved")
    repository.get_by_id.return_value = article
    repository.get_by_slug.return_value = None
    ArticleWorkflowService.transition(1, "published")
    assert article.published_at is not None

    repository.update.reset_mock()
    ArticleWorkflowService.transition(1, "draft")
    assert article.published_at is not None
    repository.update.assert_called_once()


@pytest.mark.parametrize(
    "current,target",
    [("draft", "review"), ("review", "approved"), ("approved", "published")],
)
@patch("services.article_workflow_service.ArticleRepository")
def test_incomplete_article_cannot_advance_workflow(repository, current, target):
    article = _article(current)
    article.summary = ""
    repository.get_by_id.return_value = article
    with pytest.raises(ArticleWorkflowError, match="Completa: resumen"):
        ArticleWorkflowService.transition(1, target)
    assert article.status == current
    repository.update.assert_not_called()


@patch("services.article_workflow_service.ArticleRepository")
def test_publish_rejects_slug_owned_by_other_article(repository):
    article = _article("approved")
    repository.get_by_id.return_value = article
    repository.get_by_slug.return_value = SimpleNamespace(id=2)
    with pytest.raises(ArticleWorkflowError, match="slug único"):
        ArticleWorkflowService.transition(1, "published")
    repository.update.assert_not_called()
