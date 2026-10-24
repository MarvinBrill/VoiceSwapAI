import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from .settings import DATA, prepare_directories


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self):
        prepare_directories()
        self.path = DATA / "library.sqlite3"
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute(
                "CREATE TABLE IF NOT EXISTS items (id TEXT PRIMARY KEY, kind TEXT NOT NULL, body TEXT NOT NULL)"
            )
            db.execute("CREATE INDEX IF NOT EXISTS items_kind ON items(kind)")

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=30)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def create(self, collection, **fields):
        item = {"id": uuid.uuid4().hex, "created_at": now(), **fields}
        with self.connect() as db:
            db.execute("INSERT INTO items VALUES (?, ?, ?)", (item["id"], collection, json.dumps(item)))
        return item

    def get(self, kind, item_id):
        with self.connect() as db:
            row = db.execute("SELECT body FROM items WHERE kind=? AND id=?", (kind, item_id)).fetchone()
        if not row:
            raise KeyError(item_id)
        return json.loads(row[0])

    def list(self, kind):
        with self.connect() as db:
            rows = db.execute("SELECT body FROM items WHERE kind=? ORDER BY rowid DESC", (kind,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def update(self, kind, item_id, **fields):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT body FROM items WHERE kind=? AND id=?", (kind, item_id)).fetchone()
            if not row:
                raise KeyError(item_id)
            item = {**json.loads(row[0]), **fields, "updated_at": now()}
            db.execute("UPDATE items SET body=? WHERE kind=? AND id=?", (json.dumps(item), kind, item_id))
        return item

    def delete(self, kind, item_id):
        with self.connect() as db:
            db.execute("DELETE FROM items WHERE kind=? AND id=?", (kind, item_id))
