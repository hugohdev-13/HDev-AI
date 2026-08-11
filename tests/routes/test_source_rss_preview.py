from app import app


def test_preview_requires_post():
    app.config["TESTING"] = True
    assert app.test_client().get("/sources/1/preview").status_code == 405
