"""Where was this value born? Trace one argument value to the segment it came from.

Search order: user -> trusted -> secret -> untrusted. First hit wins, so:
  * the user wins ties (if you typed it, it's yours, even if an email also mentions it);
  * secrets are checked before untrusted text, so a secret can't be laundered through an email.
Inside each origin, if exact matching finds nothing, a second pass looks for the value written in
disguise ("at"/"dot", base64, Indic digits and digit words, zero-width characters): see disguise.py.
No hit at all = MODEL_INVENTED (the model wrote it itself).
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from app.contracts import Evidence, Origin, Segment, Trust
from app.gate.disguise import find_disguised, views
from app.gate.segments import SegmentStore

ORDER = (Trust.USER, Trust.TRUSTED, Trust.SECRET, Trust.UNTRUSTED)
_AMOUNT = re.compile(r"^(?:₹|rs\.?|inr)?\s*([\d][\d,\s]*)$", re.I)
_THOUSANDS = re.compile(r"(?<=\d)[,\s](?=\d)")
# A whole value, not part of a longer one: "ya@nimbus.test" is not inside "priya@nimbus.test", and
# "ACCT-1122" is not inside "ACCT-11223344". Used where a match GRANTS trust (user, trusted config).
_BEFORE = r"(?<![\w.%+\-@/\\])"
_AFTER = r"(?![\w%+\-@/\\]|\.\w)"


def norm_text(s: str) -> str:
    return unicodedata.normalize("NFKC", s).lower()


def norm_value(v: Any) -> str:
    s = norm_text(str(v)).strip()
    return s.removeprefix("mailto:")


def as_amount(v: Any) -> str | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return str(v)
    m = _AMOUNT.match(norm_value(v))
    return _THOUSANDS.sub("", m.group(1)).strip() if m else None


def find_in_segment(seg: Segment, value: Any, whole: bool = False) -> tuple[int, str] | None:
    """Return (1-based line, original line text) of the first occurrence, or None.

    whole=True: only a whole value counts (no address or path characters glued on either side)."""
    lines = seg.text.splitlines() or [seg.text]
    amount = as_amount(value)
    if amount is not None:
        pattern = re.compile(rf"(?<!\d){re.escape(amount)}(?!\d)")
        for i, line in enumerate(lines, start=1):
            if pattern.search(_THOUSANDS.sub("", norm_text(line))):
                return i, line
        return None
    needle = norm_value(value)
    if not needle:
        return None
    hay = norm_text(seg.text)
    if whole:
        m = re.search(_BEFORE + re.escape(needle) + _AFTER, hay)
        idx = m.start() if m else -1
    else:
        idx = hay.find(needle)
    if idx < 0:
        return None
    line_no = hay[:idx].count("\n") + 1
    return line_no, lines[min(line_no, len(lines)) - 1]


def _holds_secret(seg: Segment, text: str) -> tuple[int, str] | None:
    """A value is secret-born only if it CONTAINS the whole secret. The reverse (a value inside a
    random canary, like amount 2 inside "CANARY_db_2b27...") is a coincidence, not a leak."""
    secret = norm_text(seg.text).strip()
    return (1, seg.text) if secret and secret in text else None


def _search(arg, value, segs, redact, sink, shown, find, disguised: bool) -> Evidence | None:
    for seg in segs:
        hit = find(seg, value)
        if hit:
            line, text = hit
            return Evidence(
                arg=arg,
                value=shown,
                origin=Origin(seg.trust.value),
                segment_id=seg.id,
                source=seg.source,
                line=line,
                snippet=None if seg.hidden else str(redact(text.strip()))[:240],
                sink=sink,
                disguised=disguised,
            )
    return None


def trace(arg: str, value: Any, store: SegmentStore, redact=lambda v: v, sink: bool = True) -> Evidence:
    shown = str(redact(str(value)))[:200]
    amount = as_amount(value)
    if amount is None and len(norm_value(value)) < 3:
        return Evidence(arg=arg, value=shown, origin=Origin.CONSTANT, sink=sink)

    def exact(seg: Segment, v: Any) -> tuple[int, str] | None:
        if seg.trust == Trust.SECRET:
            return _holds_secret(seg, norm_value(v))
        # Strict where a match grants trust (user, config), loose where it takes trust away (untrusted).
        return find_in_segment(seg, v, whole=seg.trust in (Trust.USER, Trust.TRUSTED))

    def disguised(seg: Segment, v: Any) -> tuple[int, str] | None:
        if seg.trust == Trust.SECRET:
            return next(filter(None, (_holds_secret(seg, view) for view in views(str(v)))), None)
        return find_disguised(seg.text, v, amount)

    # Each origin is searched exactly AND in disguise before the next one, so "priya at nimbus dot test"
    # typed by the user still beats an email that has priya@nimbus.test written plainly.
    for trust in ORDER:
        segs = [seg for seg in store.items if seg.trust == trust]
        ev = _search(arg, value, segs, redact, sink, shown, exact, disguised=False) or _search(
            arg, value, segs, redact, sink, shown, disguised, disguised=True
        )
        if ev:
            return ev
    return Evidence(arg=arg, value=shown, origin=Origin.MODEL_INVENTED, sink=sink)
