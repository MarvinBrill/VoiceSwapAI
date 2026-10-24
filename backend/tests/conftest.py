import os
import tempfile

import pytest
from fastapi.testclient import TestClient

os.environ["VOICESWAP_DATA"] = tempfile.mkdtemp(prefix="voiceswap-tests-")
os.environ["VOICESWAP_AUTO_SETUP"] = "0"
os.environ["VOICESWAP_ALLOWED_HOSTS"] = "testserver,localhost,127.0.0.1"

from app import main


@pytest.fixture
def client(monkeypatch, tmp_path):
    main.store.path = tmp_path / "test.sqlite3"
    with main.store.connect() as db:
        db.execute("CREATE TABLE items (id TEXT PRIMARY KEY, kind TEXT NOT NULL, body TEXT NOT NULL)")
    monkeypatch.setattr(main.queue, "start", lambda: None)
    monkeypatch.setattr(main.queue, "close", lambda: None)
    with TestClient(main.app) as client:
        yield client


@pytest.fixture
def records():
    audio = main.store.create(
        "audio",
        name="Gesang.wav",
        path="uploads/example.wav",
        duration=4.2,
        size=12,
        sample_rate=40000,
        channels=1,
    )
    model = main.store.create(
        "model",
        name="Teststimme",
        path="models/test.pth",
        speakers=1,
        version="v2",
        sample_rate=40000,
        size=10,
        index_path=None,
    )
    return audio, model
