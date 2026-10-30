"""Tamper-evident audit log (hash chain).

hash_n = SHA-256(prev_hash | ts | session_id | kind | payload). Change, insert or delete any
row in the middle and verify() names the first row whose hash no longer matches.
Honest limit: deleting rows from the END is not detected by the chain alone; we show the head
hash in the UI so it can be written down or published (see docs/SECURITY.md).
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from app.db.database import query, tx

GENESIS = "0" * 64


def canonical(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _hash(prev: str, ts: str, session_id: str | None, kind: str, payload: str) -> str:
    return hashlib.sha256(f"{prev}|{ts}|{session_id or ''}|{kind}|{payload}".encode()).hexdigest()


def append(kind: str, data: dict[str, Any], session_id: str | None = None) -> str:
    """Append one event; returns its hash. Callers must pass already-redacted data."""
    payload = canonical(data)
    ts = f"{time.time():.6f}"
    with tx() as conn:
        row = conn.execute("SELECT hash FROM audit_log ORDER BY seq DESC LIMIT 1").fetchone()
        prev = row[0] if row else GENESIS
        h = _hash(prev, ts, session_id, kind, payload)
        conn.execute(
            "INSERT INTO audit_log (ts, session_id, kind, payload, prev_hash, hash) VALUES (?, ?, ?, ?, ?, ?)",
            (ts, session_id, kind, payload, prev, h),
        )
    return h


def verify() -> dict[str, Any]:
    prev = GENESIS
    count = 0
    for r in query("SELECT seq, ts, session_id, kind, payload, prev_hash, hash FROM audit_log ORDER BY seq"):
        count += 1
        if r["prev_hash"] != prev or r["hash"] != _hash(
            r["prev_hash"], r["ts"], r["session_id"], r["kind"], r["payload"]
        ):
            return {"ok": False, "broken_at": r["seq"], "rows": count}
        prev = r["hash"]
    return {"ok": True, "rows": count, "head": prev}


def recent(limit: int = 100, session_id: str | None = None) -> list[dict[str, Any]]:
    if session_id:
        rows = query(
            "SELECT seq, ts, session_id, kind, payload, prev_hash, hash FROM audit_log WHERE session_id = ? "
            "ORDER BY seq DESC LIMIT ?",
            (session_id, limit),
        )
    else:
        rows = query(
            "SELECT seq, ts, session_id, kind, payload, prev_hash, hash FROM audit_log ORDER BY seq DESC LIMIT ?",
            (limit,),
        )
    return [
        {
            "seq": r["seq"],
            "ts": float(r["ts"]),
            "session_id": r["session_id"],
            "kind": r["kind"],
            "payload": json.loads(r["payload"]),
            "prev_hash": r["prev_hash"],
            "hash": r["hash"],
        }
        for r in rows
    ]
