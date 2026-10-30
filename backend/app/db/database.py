"""The only module that opens the SQLite database.

One connection per process, guarded by a lock (FastAPI runs our code on one event loop plus a
small thread pool). WAL mode lets readers work while a writer writes. Migrations in
app/db/migrations/ are applied in filename order and recorded in schema_version.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"

_lock = threading.RLock()
_conn: sqlite3.Connection | None = None
_path: Path | None = None


def connect(db_path: Path) -> sqlite3.Connection:
    """Open (or reopen) the database at db_path and apply migrations."""
    global _conn, _path
    with _lock:
        if _conn is not None and _path == db_path:
            return _conn
        if _conn is not None:
            _conn.close()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        _migrate(conn)
        _conn, _path = conn, db_path
        return conn


def _migrate(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version (version TEXT PRIMARY KEY, applied_at REAL NOT NULL)"
    )
    done = {r[0] for r in conn.execute("SELECT version FROM schema_version")}
    for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if sql_file.stem in done:
            continue
        conn.executescript("BEGIN;\n" + sql_file.read_text(encoding="utf-8") + "\nCOMMIT;")
        conn.execute(
            "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)", (sql_file.stem, time.time())
        )


def get_conn() -> sqlite3.Connection:
    if _conn is None:
        raise RuntimeError("Database not connected: call app.db.database.connect() at start-up")
    return _conn


@contextmanager
def tx() -> Iterator[sqlite3.Connection]:
    """A write transaction. Use for every multi-statement write."""
    conn = get_conn()
    with _lock:
        conn.execute("BEGIN IMMEDIATE")
        try:
            yield conn
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        else:
            conn.execute("COMMIT")


def query(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    conn = get_conn()
    with _lock:
        return conn.execute(sql, params).fetchall()


def close() -> None:
    global _conn, _path
    with _lock:
        if _conn is not None:
            _conn.close()
        _conn, _path = None, None
