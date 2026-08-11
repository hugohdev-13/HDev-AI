from app import app


def test_import_requires_post():
    app.config["TESTING"] = True
    assert app.test_client().get("/sources/1/import").status_code == 405
