from types import SimpleNamespace
from unittest.mock import Mock

from services.rss_feed_service import RSSFeedService
from unittest.mock import patch


def _source(**values):
    data = {"source_type": "rss", "is_active": True, "feed_url": "https://example.com/feed", "last_synced_at": None, "last_sync_status": None, "last_sync_message": None}
    data.update(values)
    return SimpleNamespace(**data)


def test_rss_parsing_normalizes_summary_date_author_and_image():
    content = b'''<rss><channel><title>Feed</title><item><title>Title</title><link>https://example.com/a</link><guid>entry-1</guid><description>&lt;b&gt;Safe&lt;/b&gt; text</description><author>Ada</author><pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate><media:content xmlns:media="http://search.yahoo.com/mrss/" url="https://example.com/i.png" /></item></channel></rss>'''
    title, entries = RSSFeedService.parse_feed(content)
    assert title == "Feed"
    assert entries[0].summary == "Safe text"
    assert entries[0].author == "Ada"
    assert entries[0].published_at is not None
    assert entries[0].image_url == "https://example.com/i.png"



def test_safe_url_rejects_ssrf_targets():
    for url in ("http://localhost", "http://127.0.0.1", "http://10.0.0.1", "http://169.254.169.254"):
        try:
            RSSFeedService.safe_url(url)
        except ValueError:
            continue
        assert False, url


@patch("services.rss_feed_service.requests.get")
@patch("services.rss_feed_service.RSSFeedService.safe_url")
def test_redirect_destination_is_validated_against_ssrf(mock_safe_url, mock_get):
    mock_safe_url.side_effect = [
        "https://example.com/feed",
        ValueError("URL bloqueada por seguridad."),
    ]
    mock_get.return_value = SimpleNamespace(
        status_code=302,
        headers={"Location": "http://127.0.0.1/internal"},
    )

    try:
        RSSFeedService.fetch_feed("https://example.com/feed")
    except ValueError:
        pass
    else:
        assert False, "The redirect target must be rejected."

    mock_get.assert_called_once()


@patch("services.rss_feed_service.SourceRepository.save")
@patch("services.rss_feed_service.requests.get")
def test_inactive_non_rss_and_missing_feed_fail_without_http(
    mock_get,
    mock_save,
):
    inactive = RSSFeedService.get_entries(
        _source(is_active=False)
    )
    assert not inactive.success

    non_rss = RSSFeedService.get_entries(
        _source(source_type="manual")
    )
    assert not non_rss.success

    missing_feed = RSSFeedService.get_entries(
        _source(feed_url=None)
    )
    assert not missing_feed.success

    mock_get.assert_not_called()
