"""CLI coverage for publishing approved articles that are due."""

from unittest.mock import patch

from app import app
from services.article_scheduling_service import ScheduledPublicationSummary


@patch("app.ArticleSchedulingService.publish_due_articles")
def test_publish_scheduled_cli_reports_summary(publish_due_articles):
    publish_due_articles.return_value = ScheduledPublicationSummary(
        total=2,
        published=2,
    )

    result = app.test_cli_runner().invoke(args=["publish-scheduled"])

    assert result.exit_code == 0
    assert "total=2" in result.output
    assert "published=2" in result.output


@patch("app.ArticleSchedulingService.publish_due_articles")
def test_publish_scheduled_cli_fails_when_one_item_cannot_publish(
    publish_due_articles,
):
    publish_due_articles.return_value = ScheduledPublicationSummary(
        total=1,
        failed=1,
    )

    result = app.test_cli_runner().invoke(args=["publish-scheduled"])

    assert result.exit_code != 0
    assert "fallaron" in result.output
