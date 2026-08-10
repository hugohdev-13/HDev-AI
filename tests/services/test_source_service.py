"""Unit tests for content-source business rules."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from services.source_service import (
    SourceDeletionError,
    SourceService,
    SourceValidationError,
)


def valid_data(**overrides):
    """Return a valid RSS source payload for source-service tests."""
    return {
        "name": "OpenAI Blog",
        "website_url": "https://openai.com",
        "feed_url": "https://openai.com/feed.xml",
        "source_type": "rss",
        "is_active": "on",
        "sync_interval_minutes": "60",
    } | overrides


class SourceServiceTests(unittest.TestCase):
    """Verify source validation and lifecycle without a database dependency."""

    def configure_repository(self, repository):
        repository.name_exists.return_value = False
        repository.feed_url_exists.return_value = False
        repository.slug_exists.return_value = False

    @patch("services.source_service.SourceRepository")
    def test_valid_rss_creation_uses_defaults(self, repository):
        self.configure_repository(repository)
        repository.create.side_effect = lambda source: source

        source = SourceService.create_source(valid_data())

        self.assertEqual(source.slug, "openai-blog")
        self.assertEqual(source.source_type, "rss")
        self.assertTrue(source.is_active)
        self.assertEqual(source.sync_interval_minutes, 60)
        self.assertEqual(source.last_sync_status, "never")

    @patch("services.source_service.SourceRepository")
    def test_rss_requires_feed_url(self, repository):
        self.configure_repository(repository)

        with self.assertRaises(SourceValidationError) as error:
            SourceService.create_source(valid_data(feed_url=""))

        self.assertIn("feed_url", error.exception.errors)

    @patch("services.source_service.SourceRepository")
    def test_api_and_manual_sources_are_valid(self, repository):
        self.configure_repository(repository)
        repository.create.side_effect = lambda source: source

        api_source = SourceService.create_source(
            valid_data(source_type="API", feed_url="", website_url="https://api.example")
        )
        manual_source = SourceService.create_source(
            valid_data(source_type="manual", feed_url="", website_url="")
        )

        self.assertEqual(api_source.source_type, "api")
        self.assertEqual(manual_source.source_type, "manual")

    @patch("services.source_service.SourceRepository")
    def test_invalid_url_and_type_are_rejected(self, repository):
        self.configure_repository(repository)

        with self.assertRaises(SourceValidationError) as error:
            SourceService.validate_source_data(
                valid_data(website_url="ftp://invalid", source_type="unknown")
            )

        self.assertIn("website_url", error.exception.errors)
        self.assertIn("source_type", error.exception.errors)

    @patch("services.source_service.SourceRepository")
    def test_sync_interval_bounds_and_duplicates_are_enforced(self, repository):
        self.configure_repository(repository)
        for interval in ("4", "10081"):
            with self.subTest(interval=interval):
                with self.assertRaises(SourceValidationError):
                    SourceService.validate_source_data(valid_data(sync_interval_minutes=interval))

        repository.name_exists.return_value = True
        with self.assertRaises(SourceValidationError) as error:
            SourceService.validate_source_data(valid_data())
        self.assertIn("name", error.exception.errors)

        repository.name_exists.return_value = False
        repository.feed_url_exists.return_value = True
        with self.assertRaises(SourceValidationError) as error:
            SourceService.validate_source_data(valid_data())
        self.assertIn("feed_url", error.exception.errors)

    @patch("services.source_service.SourceRepository")
    def test_slug_collision_uses_incrementing_suffix(self, repository):
        repository.slug_exists.side_effect = [True, True, False]

        self.assertEqual(SourceService.generate_unique_slug("OpenAI Blog"), "openai-blog-3")

    @patch("services.source_service.SourceRepository")
    def test_update_regenerates_slug_only_when_name_changes(self, repository):
        self.configure_repository(repository)
        source = SimpleNamespace(
            id=1,
            name="Old Name",
            slug="old-name",
            website_url=None,
            feed_url=None,
            source_type="rss",
            is_active=True,
            sync_interval_minutes=60,
        )
        repository.get_by_id.return_value = source
        repository.save.side_effect = lambda value: value

        updated = SourceService.update_source(1, valid_data(name="New Name"))

        self.assertEqual(updated.slug, "new-name")
        self.assertEqual(updated.name, "New Name")

    @patch("services.source_service.SourceRepository")
    def test_toggle_and_delete_rules(self, repository):
        source = SimpleNamespace(id=1, is_active=True)
        repository.get_by_id.return_value = source
        repository.save.side_effect = lambda value: value

        self.assertFalse(SourceService.toggle_source(1).is_active)

        repository.count_articles.return_value = 0
        self.assertTrue(SourceService.delete_source(1))
        repository.delete.assert_called_once_with(source)

        repository.count_articles.return_value = 1
        with self.assertRaises(SourceDeletionError):
            SourceService.delete_source(1)

    def test_boolean_normalization_and_defaults(self):
        self.assertTrue(SourceService._normalize_boolean(True))
        self.assertTrue(SourceService._normalize_boolean("1"))
        self.assertTrue(SourceService._normalize_boolean("on"))
        self.assertFalse(SourceService._normalize_boolean(False))
        self.assertFalse(SourceService._normalize_boolean("false"))
        self.assertFalse(SourceService._normalize_boolean(None))
