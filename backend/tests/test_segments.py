"""Every email field the agent can see must be labelled UNTRUSTED, not only From/Subject/body.

Expected values below are worked out by hand from the world data files, not by the code under test.
"""

from app.contracts import Origin
from app.gate.segments import SegmentStore
from app.gate.tracer import trace
from app.tools.world import World


def store_after_reading(inbox: str) -> SegmentStore:
    s = SegmentStore()
    s.add(
        "user", "Your request", "user", "Summarise my unread email and send the summary to priya@nimbus.test"
    )
    s.ingest("list_unread_emails", {}, World(inbox=inbox).list_unread_emails())
    return s


def test_reply_to_header_is_untrusted():
    # s9b: Email #2 has "reply_to": "finance-desk@evil.test" and the address is nowhere else.
    ev = trace("to", "finance-desk@evil.test", store_after_reading("s9b_reply_to_header"))
    assert ev.origin == Origin.UNTRUSTED
    assert ev.segment_id == "email:2"


def test_attachment_name_is_untrusted():
    # s13b: the address and the path exist only inside Email #3's attachment name.
    s = store_after_reading("s13b_attachment_name")
    assert trace("to", "hr-archive@evil.test", s).origin == Origin.UNTRUSTED
    assert trace("path", "payroll.csv", s).origin == Origin.UNTRUSTED


def test_a_header_we_have_never_seen_is_untrusted_too():
    # Fail closed: a field nobody planned for (a future tool, a new header) still gets labelled.
    s = SegmentStore()
    s.ingest(
        "read_email",
        {"email_id": 9},
        {"id": 9, "from": "a@b.test", "subject": "hi", "body": "hello", "x_return_path": "bounce@evil.test"},
    )
    assert trace("to", "bounce@evil.test", s).origin == Origin.UNTRUSTED


def test_plain_emails_keep_their_text_and_line_numbers():
    # Evidence lines on slides ("Email #3, line 13" in s2) must not move for emails without extra fields.
    s = store_after_reading("s2_hidden_instruction")
    assert s.get("email:1").text == (
        "From: priya@nimbus.test\nSubject: Standup moved\n\n"
        "Hi,\nTomorrow's standup moves to 10:30 because of the client call.\nPriya"
    )
    assert trace("to", "audit-team@evil.test", s).line == 13
