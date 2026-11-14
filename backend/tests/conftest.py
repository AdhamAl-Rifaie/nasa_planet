import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config, db, registry  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Fresh database per test, worker started by the app lifespan."""
    from fastapi.testclient import TestClient
    monkeypatch.setattr(config, "VAR_DIR", tmp_path)
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(config, "ARTIFACT_DIR", tmp_path / "artifacts")
    registry.reset_registry()
    from app.main import app
    with TestClient(app) as c:
        yield c
    db.init_db()
