import os
import tempfile

os.environ.setdefault("DATABASE_PATH", os.path.join(tempfile.mkdtemp(), "import.db"))

import pytest
import db
from app import app


@pytest.fixture
def anon_client(tmp_path, monkeypatch):
    """A browser that isn't logged in, with an empty database."""
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)
    return app.test_client()


@pytest.fixture
def client(anon_client):
    """A browser that is already logged in."""
    with anon_client.session_transaction() as session:
        session["logged_in"] = True
    return anon_client