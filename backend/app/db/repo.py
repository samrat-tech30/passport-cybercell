"""Queries for sessions, decisions, world events and eval runs. Only the db package runs SQL."""

from __future__ import annotations

import json
import time
from typing import Any

from app.contracts import Decision
from app.db.database import query, tx


def create_session(
    session_id: str, scenario_id: str | None, user_request: str, shield_on: bool, mode: str
) -> None:
    with tx() as c:
        c.execute(
            "INSERT INTO sessions (id, created_at, scenario_id, user_request, shield_on, mode, status) "
            "VALUES (?, ?, ?, ?, ?, ?, 'created')",
            (session_id, time.time(), scenario_id, user_request, int(shield_on), mode),
        )


def set_session_status(session_id: str, status: str) -> None:
    finished = time.time() if status in {"done", "error"} else None
    with tx() as c:
        c.execute(
            "UPDATE sessions SET status = ?, finished_at = COALESCE(?, finished_at) WHERE id = ?",
            (status, finished, session_id),
        )


def set_session_capsule(session_id: str, capsule: dict[str, Any]) -> None:
    with tx() as c:
        c.execute("UPDATE sessions SET capsule_json = ? WHERE id = ?", (json.dumps(capsule), session_id))


def create_gateway_session(session_id: str, agent_name: str, client: str, shield_on: bool) -> None:
    """A gateway session: no request until the agent calls start_task (stored as "")."""
    with tx() as c:
        c.execute(
            "INSERT INTO sessions (id, created_at, scenario_id, user_request, shield_on, mode, status) "
            "VALUES (?, ?, NULL, '', ?, 'live', 'created')",
            (session_id, time.time(), int(shield_on)),
        )
        c.execute(
            "INSERT INTO gateway_sessions (session_id, agent_name, client) VALUES (?, ?, ?)",
            (session_id, agent_name, client),
        )


def set_session_request(session_id: str, user_request: str) -> None:
    with tx() as c:
        c.execute("UPDATE sessions SET user_request = ? WHERE id = ?", (user_request, session_id))


def list_gateway_sessions(limit: int = 50) -> list[dict[str, Any]]:
    rows = query(
        "SELECT s.id, s.created_at, s.user_request, s.shield_on, s.status, g.agent_name, g.client, "
        "SUM(d.verdict = 'ALLOW') AS n_allow, SUM(d.verdict = 'REQUIRE_APPROVAL') AS n_ask, "
        "SUM(d.verdict = 'DENY') AS n_deny "
        "FROM gateway_sessions g JOIN sessions s ON s.id = g.session_id "
        "LEFT JOIN decisions d ON d.session_id = s.id "
        "GROUP BY s.id ORDER BY s.created_at DESC LIMIT ?",
        (limit,),
    )
    return [
        {
            "session_id": r["id"],
            "agent_name": r["agent_name"],
            "client": r["client"],
            "shield_on": bool(r["shield_on"]),
            "intent": r["user_request"] or None,
            "status": r["status"],
            "counts": {
                "ALLOW": r["n_allow"] or 0,
                "REQUIRE_APPROVAL": r["n_ask"] or 0,
                "DENY": r["n_deny"] or 0,
            },
            "created_ts": r["created_at"],
        }
        for r in rows
    ]


def get_session(session_id: str) -> dict[str, Any] | None:
    rows = query(
        "SELECT s.*, g.agent_name, g.client FROM sessions s "
        "LEFT JOIN gateway_sessions g ON g.session_id = s.id WHERE s.id = ?",
        (session_id,),
    )
    if not rows:
        return None
    r = dict(rows[0])
    r["shield_on"] = bool(r["shield_on"])
    if r["agent_name"] is not None:
        r["mode"] = "gateway"
    else:
        r.pop("agent_name")
        r.pop("client")
    r["capsule"] = json.loads(r.pop("capsule_json")) if r.get("capsule_json") else None
    return r


def save_decision(d: Decision) -> None:
    with tx() as c:
        c.execute(
            "INSERT OR REPLACE INTO decisions (id, session_id, step, tool, args_json, verdict, rule_id, risk, message, "
            "reasons_json, passports_json, shield_on, executed, approval, ts) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                d.id,
                d.session_id,
                d.step,
                d.tool,
                json.dumps(d.args, ensure_ascii=False),
                d.verdict.value,
                d.rule_id,
                d.risk,
                d.message,
                json.dumps([r.model_dump(mode="json") for r in d.reasons], ensure_ascii=False),
                json.dumps([p.model_dump(mode="json") for p in d.passports], ensure_ascii=False),
                int(d.shield_on),
                int(d.executed),
                d.approval,
                d.ts,
            ),
        )


def list_decisions(session_id: str) -> list[dict[str, Any]]:
    out = []
    for r in query("SELECT * FROM decisions WHERE session_id = ? ORDER BY ts", (session_id,)):
        d = dict(r)
        d["args"] = json.loads(d.pop("args_json"))
        d["reasons"] = json.loads(d.pop("reasons_json"))
        d["passports"] = json.loads(d.pop("passports_json"))
        d["shield_on"] = bool(d["shield_on"])
        d["executed"] = bool(d["executed"])
        out.append(d)
    return out


def add_world_event(session_id: str, kind: str, data: dict[str, Any]) -> None:
    with tx() as c:
        c.execute(
            "INSERT INTO world_events (session_id, kind, data_json, ts) VALUES (?, ?, ?, ?)",
            (session_id, kind, json.dumps(data, ensure_ascii=False), time.time()),
        )


def list_world_events(
    session_id: str | None = None, kind: str | None = None, limit: int = 200
) -> list[dict[str, Any]]:
    sql = "SELECT * FROM world_events WHERE 1=1"
    params: list[Any] = []
    if session_id:
        sql += " AND session_id = ?"
        params.append(session_id)
    if kind:
        sql += " AND kind = ?"
        params.append(kind)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    return [
        {
            "id": r["id"],
            "session_id": r["session_id"],
            "kind": r["kind"],
            "data": json.loads(r["data_json"]),
            "ts": r["ts"],
        }
        for r in query(sql, tuple(params))
    ]


def save_eval_run(run_id: str, summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    with tx() as c:
        c.execute(
            "INSERT INTO eval_runs (id, ts, summary_json, rows_json) VALUES (?, ?, ?, ?)",
            (run_id, time.time(), json.dumps(summary), json.dumps(rows)),
        )


def latest_eval_run() -> dict[str, Any] | None:
    rows = query("SELECT * FROM eval_runs ORDER BY ts DESC LIMIT 1")
    if not rows:
        return None
    r = rows[0]
    return {
        "id": r["id"],
        "ts": r["ts"],
        "summary": json.loads(r["summary_json"]),
        "rows": json.loads(r["rows_json"]),
    }


def clear_demo_data() -> None:
    """Delete sessions, decisions and world events. The audit log is never deleted."""
    with tx() as c:
        c.execute("DELETE FROM world_events")
        c.execute("DELETE FROM decisions")
        c.execute("DELETE FROM gateway_sessions")
        c.execute("DELETE FROM sessions")
