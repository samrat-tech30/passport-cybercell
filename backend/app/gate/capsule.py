"""Freeze the user's intent BEFORE any untrusted content is read.

Deterministic on purpose (regex + keyword map, no LLM): nothing an attacker writes can reach it.
"""

from __future__ import annotations

import hashlib
import json
import re

from app.contracts import Capsule

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
FILE = re.compile(r"(?<![\w@])[\w./-]+\.(?:md|csv|txt|pdf|json)\b")
AMOUNT = re.compile(r"(?:₹|\brs\.?|\binr)\s?([\d][\d,]*)", re.I)
CAP = re.compile(
    r"(?:under|below|max(?:imum)?|up\s?to|not more than)\s*(?:₹|rs\.?|inr)?\s?([\d][\d,]*)", re.I
)

# word pattern in the lower-cased request -> tools it unlocks (word boundaries: "payroll" is not "pay")
KEYWORDS: dict[str, tuple[str, ...]] = {
    r"\bsummar": ("list_unread_emails", "read_email"),
    r"\binbox\b": ("list_unread_emails", "read_email"),
    r"\bunread\b": ("list_unread_emails", "read_email"),
    r"\be-?mails?\b": (
        "list_unread_emails",
        "read_email",
    ),  # reading only; sending needs a verb or an address
    r"\bsend": ("send_email",),
    r"\brepl(?:y|ies)\b": ("read_email", "send_email"),
    r"\bforward": ("read_email", "send_email"),
    r"\bread\b": ("list_unread_emails", "read_email", "read_file"),
    r"\bfiles?\b": ("read_file",),
    r"\binvoices?\b": ("read_file",),
    r"\bpay(?:ing|ment)?\b": ("read_file", "pay_invoice"),
    r"\bdelete": ("delete_file",),
    r"\bremove": ("delete_file",),
}

PHRASES = {
    "list_unread_emails": "read your inbox",
    "read_file": "read {files}",
    "pay_invoice": "pay an invoice (I'll ask you first)",
    "delete_file": "delete files (I'll ask you first)",
}


def build_capsule(user_text: str) -> Capsule:
    low = user_text.lower()
    tools = sorted({t for pattern, ts in KEYWORDS.items() if re.search(pattern, low) for t in ts})
    recipients = sorted({m.group(0).lower().rstrip(".") for m in EMAIL.finditer(user_text)})
    if recipients:  # naming an address is an intent to send to it
        tools = sorted(set(tools) | {"send_email"})
    files = sorted({m.group(0).lstrip("./") for m in FILE.finditer(user_text)})
    caps = [int(m.group(1).replace(",", "")) for m in CAP.finditer(user_text)]
    amounts = [int(m.group(1).replace(",", "")) for m in AMOUNT.finditer(user_text)]
    max_amount = min(caps) if caps else (max(amounts) if amounts else None)

    parts = []
    for t in tools:
        if t == "send_email":
            parts.append(f"send email to {', '.join(recipients)}" if recipients else "send an email")
        elif t == "read_file":
            parts.append(PHRASES[t].format(files=", ".join(files) if files else "files you name"))
        elif t in PHRASES:
            parts.append(PHRASES[t])
    if max_amount is not None:
        parts.append(f"spend at most Rs {max_amount:,}")
    summary = (
        ("I'll " + "; ".join(parts) + ". Nothing else.")
        if parts
        else "I didn't find an action I'm allowed to take."
    )

    body = {
        "goal": user_text,
        "allowed_tools": tools,
        "recipients": recipients,
        "files": files,
        "max_amount_inr": max_amount,
    }
    sha = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return Capsule(**body, summary=summary, sha256=sha)
