from app.db import audit
from app.db.database import get_conn


def test_untouched_chain_verifies():
    for i in range(3):
        audit.append("decision", {"n": i}, session_id="s")
    assert audit.verify()["ok"] is True


def test_editing_a_row_breaks_the_chain_at_that_row():
    for i in range(5):
        audit.append("decision", {"verdict": "DENY", "n": i}, session_id="s")
    get_conn().execute("UPDATE audit_log SET payload = ? WHERE seq = 3", ('{"n":2,"verdict":"ALLOW"}',))
    assert audit.verify() == {"ok": False, "broken_at": 3, "rows": 3}


def test_deleting_a_middle_row_breaks_the_chain():
    for i in range(4):
        audit.append("decision", {"n": i})
    get_conn().execute("DELETE FROM audit_log WHERE seq = 2")
    result = audit.verify()
    assert result["ok"] is False and result["broken_at"] == 3
