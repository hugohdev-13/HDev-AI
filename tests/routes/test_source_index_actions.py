from types import SimpleNamespace

from flask import render_template

from app import app


def _render(source):
    with app.test_request_context("/sources/"):
        return render_template(
            "sources/index.html",
            sources=[source],
            pagination=SimpleNamespace(),
            search="",
            total=1,
        )


def test_active_rss_shows_post_sync_action():
    source = SimpleNamespace(id=1, name="RSS", website_url=None, feed_url="https://example.com/feed", source_type="rss", is_active=True, last_sync_status="never", last_sync_message=None, article_count=0, last_synced_at=None)
    page = _render(source)
    assert "Sincronizar ahora" in page
    assert 'action="/sources/1/import"' in page
    assert 'method="post"' in page


def test_inactive_rss_and_non_rss_hide_sync_action():
    inactive = SimpleNamespace(id=1, name="RSS", website_url=None, feed_url=None, source_type="rss", is_active=False, last_sync_status="never", last_sync_message=None, article_count=0, last_synced_at=None)
    manual = SimpleNamespace(id=2, name="Manual", website_url=None, feed_url=None, source_type="manual", is_active=True, last_sync_status="never", last_sync_message=None, article_count=0, last_synced_at=None)
    assert "Sincronizar ahora" not in _render(inactive)
    assert "Sincronizar ahora" not in _render(manual)
