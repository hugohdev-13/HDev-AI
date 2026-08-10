"""SQLite repository tests for the content-source persistence layer."""

from flask import Flask
import unittest

from extensions import db
from models import Article, Source
from repositories.source_repository import SourceRepository


class SourceRepositoryTests(unittest.TestCase):
    """Exercise SourceRepository without SQL Server or Azure dependencies."""

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            SQLALCHEMY_DATABASE_URI="sqlite://",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def source(self, name="OpenAI Blog", **values):
        source = Source(
            name=name,
            slug=values.pop("slug", name.lower().replace(" ", "-")),
            website_url=values.pop("website_url", "https://openai.com"),
            feed_url=values.pop("feed_url", "https://openai.com/feed.xml"),
            source_type=values.pop("source_type", "rss"),
            **values,
        )
        db.session.add(source)
        db.session.commit()
        return source

    def test_getters_find_source_by_supported_identifiers(self):
        source = self.source()

        self.assertEqual(SourceRepository.get_by_id(source.id).id, source.id)
        self.assertEqual(SourceRepository.get_by_name("openai blog").id, source.id)
        self.assertEqual(SourceRepository.get_by_slug("openai-blog").id, source.id)
        self.assertEqual(
            SourceRepository.get_by_feed_url("https://openai.com/feed.xml").id,
            source.id,
        )

    def test_list_active_excludes_inactive_sources(self):
        self.source("Active", slug="active", is_active=True)
        self.source("Inactive", slug="inactive", is_active=False)

        self.assertEqual([item.name for item in SourceRepository.list_active()], ["Active"])

    def test_search_covers_all_public_source_identifiers(self):
        self.source(
            "Microsoft Learn",
            slug="learn",
            website_url="https://learn.microsoft.com",
            feed_url="https://learn.microsoft.com/rss.xml",
        )

        self.assertEqual(
            [item.name for item in db.session.scalars(SourceRepository.search("rss.xml"))],
            ["Microsoft Learn"],
        )

    def test_paginate_orders_by_name(self):
        self.source("Zulu", slug="zulu", feed_url="https://zulu.example/rss")
        self.source("Alpha", slug="alpha", feed_url="https://alpha.example/rss")

        page = SourceRepository.paginate("", 1, 1)

        self.assertEqual(page.total, 2)
        self.assertEqual(page.items[0].name, "Alpha")

    def test_exists_helpers_respect_excluded_source(self):
        source = self.source()

        self.assertTrue(SourceRepository.name_exists("OPENAI BLOG"))
        self.assertTrue(SourceRepository.slug_exists("openai-blog"))
        self.assertTrue(SourceRepository.feed_url_exists("https://openai.com/feed.xml"))
        self.assertFalse(SourceRepository.name_exists("OpenAI Blog", source.id))
        self.assertFalse(SourceRepository.slug_exists("openai-blog", source.id))
        self.assertFalse(
            SourceRepository.feed_url_exists("https://openai.com/feed.xml", source.id)
        )

    def test_count_articles_returns_integer(self):
        source = self.source()
        db.session.add(
            Article(title="Article", slug="article", content="Content", source_id=source.id)
        )
        db.session.commit()

        self.assertEqual(SourceRepository.count_articles(source.id), 1)

