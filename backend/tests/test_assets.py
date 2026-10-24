import hashlib

import pytest

from app import assets
from app.settings import data_path


def test_asset_download_rejects_wrong_hash(monkeypatch, tmp_path):
    payload = b"wrong model"
    monkeypatch.setattr(
        assets,
        "MANIFEST",
        {
            "revision": "test",
            "files": {
                "test.bin": {
                    "source": "test.bin",
                    "size": len(payload),
                    "sha256": hashlib.sha256(b"correct").hexdigest(),
                }
            },
        },
    )
    monkeypatch.setattr(assets, "asset_path", lambda name: tmp_path / name)
    monkeypatch.setattr(assets.time, "sleep", lambda seconds: None)

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def raise_for_status(self):
            pass

        def iter_content(self, size):
            yield payload

    monkeypatch.setattr(assets.requests, "get", lambda *args, **kwargs: Response())
    with pytest.raises(ValueError, match="Prüfsumme"):
        assets.ensure_assets(["test.bin"], lambda *args: None)
    assert list(tmp_path.iterdir()) == []


def test_data_path_rejects_traversal():
    with pytest.raises(ValueError):
        data_path("../../outside.txt")
