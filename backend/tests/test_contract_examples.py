"""Live responses must keep the same shape (keys and status) as contracts/examples/*.json.
If this fails, either the code drifted from the contract or the contract changed without
regenerating the examples (python ../scripts/make_contract_examples.py). Decide which is right."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

EXAMPLES = Path(__file__).resolve().parents[2] / "contracts" / "examples"


def keys(v, path=""):
    """All key paths in a JSON value (list items merged)."""
    out = set()
    if isinstance(v, dict):
        for k, x in v.items():
            out.add(f"{path}.{k}")
            out |= keys(x, f"{path}.{k}")
    elif isinstance(v, list):
        for x in v:
            out |= keys(x, f"{path}[]")
    return out


@pytest.fixture
def client():
    from app.main import create_app

    with TestClient(create_app()) as c:
        yield c


def wait(c, sid):
    for _ in range(100):
        if c.get(f"/sessions/{sid}").json()["session"]["status"] in ("done", "error"):
            return
        time.sleep(0.05)


SIMPLE = [
    "health.ok",
    "scenarios.ok",
    "sessions.create.ok",
    "sessions.create.scenario_required",
    "error.invalid_input",
    "approvals.not_pending",
    "audit.verify.ok",
    "decide.deny",
    "decide.allow",
]


@pytest.mark.parametrize("name", SIMPLE)
def test_response_shape_matches_the_contract_example(client, name):
    ex = json.loads((EXAMPLES / f"{name}.json").read_text(encoding="utf-8"))
    req = ex["request"]
    r = (
        client.request(req["method"], req["path"], json=req["body"])
        if req["body"] is not None
        else client.request(req["method"], req["path"])
    )
    assert r.status_code == ex["response"]["status"]
    assert keys(r.json()) == keys(ex["response"]["body"]), (
        f"{name}: shape differs from contracts/examples/{name}.json"
    )


def test_session_detail_and_evidence_shapes_match(client):
    sid = client.post("/sessions", json={"scenario_id": "s2"}).json()["session_id"]
    wait(client, sid)
    for name, path in (
        ("sessions.get.ok", f"/sessions/{sid}"),
        ("segments.get.ok", f"/sessions/{sid}/segments/email:3"),
    ):
        ex = json.loads((EXAMPLES / f"{name}.json").read_text(encoding="utf-8"))
        r = client.get(path)
        assert r.status_code == ex["response"]["status"]
        assert keys(r.json()) == keys(ex["response"]["body"]), name
