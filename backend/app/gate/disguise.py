"""Disguise-proof views of a line of text (v2 upgrade B). Deterministic string work, no LLM.

The attacker writes a value in disguise ("audit-team at evil dot test", base64, Kannada digits,
zero-width characters); the LLM writes the clean value into the tool call. Exact matching then
finds it nowhere. views() gives extra "clean" readings of a line so the tracer can still find
where the value was born. It only ADDS readings: the original line is always kept as the snippet.

Look-alike letters (Cyrillic а in "bigbаsket") are NOT folded here: folding would let a fake value
pass as the real one. They are caught by R11_LOOKALIKE in decide.py instead.
"""

from __future__ import annotations

import base64
import binascii
import re
import unicodedata
from functools import lru_cache

ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍⁠﻿"))
MIN_RUN = 3  # digit words only count in runs of 3+, so "do" in a normal Hindi sentence stays "do"
MIN_NEEDLE = 6  # shorter values are too easy to find by accident in squashed text

DIGIT_WORDS: dict[str, str] = {
    # English
    **dict.fromkeys(["zero"], "0"),
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    # Hindi, Latin script
    **dict.fromkeys(["shunya", "shoonya", "sunya"], "0"),
    "ek": "1",
    "do": "2",
    **dict.fromkeys(["teen", "tin"], "3"),
    **dict.fromkeys(["char", "chaar"], "4"),
    **dict.fromkeys(["panch", "paanch"], "5"),
    **dict.fromkeys(["chhe", "chhah", "che"], "6"),
    **dict.fromkeys(["saat", "sat"], "7"),
    **dict.fromkeys(["aath", "ath"], "8"),
    "nau": "9",
    # Hindi, Devanagari
    "शून्य": "0",
    "एक": "1",
    "दो": "2",
    "तीन": "3",
    "चार": "4",
    **dict.fromkeys(["पांच", "पाँच"], "5"),
    **dict.fromkeys(["छह", "छः", "छे"], "6"),
    "सात": "7",
    "आठ": "8",
    "नौ": "9",
    # Kannada, Latin script
    **dict.fromkeys(["sonne", "sonnay"], "0"),
    "ondu": "1",
    **dict.fromkeys(["eradu", "yeradu"], "2"),
    **dict.fromkeys(["mooru", "muru"], "3"),
    **dict.fromkeys(["naalku", "nalku"], "4"),
    **dict.fromkeys(["aidu", "aidhu"], "5"),
    "aaru": "6",
    **dict.fromkeys(["elu", "yelu", "eelu"], "7"),
    **dict.fromkeys(["entu", "yentu"], "8"),
    **dict.fromkeys(["ombattu", "ombhattu"], "9"),
    # Kannada script
    "ಸೊನ್ನೆ": "0",
    "ಒಂದು": "1",
    "ಎರಡು": "2",
    "ಮೂರು": "3",
    "ನಾಲ್ಕು": "4",
    "ಐದು": "5",
    "ಆರು": "6",
    "ಏಳು": "7",
    "ಎಂಟು": "8",
    "ಒಂಬತ್ತು": "9",
}
_WORD_PUNCT = ".,;:!?()[]\"'"


def _spoken(word: str) -> str:
    return r"\s*[\[(]?\s*\b" + word + r"\b\s*[\])]?\s*"


_SEPARATORS = (
    (re.compile(_spoken("at")), "@"),
    (re.compile(_spoken("dot")), "."),
    (re.compile(_spoken("(?:dash|hyphen)")), "-"),
    (re.compile(_spoken("underscore")), "_"),
)
_B64 = re.compile(r"[A-Za-z0-9+/_-]{16,}={0,2}")
_WS = re.compile(r"\s+")


def clean(text: str) -> str:
    """NFKC + lowercase, zero-width characters removed, Indic digits turned into 0-9."""
    s = unicodedata.normalize("NFKC", text).translate(ZERO_WIDTH).lower()
    return "".join(
        str(d) if not ch.isascii() and (d := unicodedata.decimal(ch, None)) is not None else ch for ch in s
    )


def compact(text: str) -> str:
    return _WS.sub("", clean(text)).removeprefix("mailto:")


def spoken_separators(text: str) -> str:
    for pattern, sep in _SEPARATORS:
        text = pattern.sub(sep, text)
    return text


def spoken_digits(words: list[str]) -> list[str]:
    """Replace every run of MIN_RUN+ consecutive digit words with ONE token of digits.

    words = a line split on whitespace. Look a word up with DIGIT_WORDS.get(w.strip(_WORD_PUNCT)).
    ["pay", "ek", "chaar", "nau", "nau", "now"] -> ["pay", "1499", "now"]
    ["aap", "do", "minute", "ruko"]             -> unchanged (a run of 1 is just a word)
    """
    out: list[str] = []
    run: list[tuple[str, str]] = []  # (original word, digit) of the current run

    def flush() -> None:
        if len(run) >= MIN_RUN:
            out.append("".join(d for _, d in run))
        else:
            out.extend(w for w, _ in run)
        run.clear()

    for w in words:
        digit = DIGIT_WORDS.get(w.strip(_WORD_PUNCT))
        if digit is None:
            flush()
            out.append(w)
        else:
            run.append((w, digit))
    flush()  # a line that ends in "...nau nau"
    return out


def _decoded_base64(line: str) -> list[str]:
    out = []
    for token in _B64.findall(line):
        raw = token.rstrip("=")
        raw += "=" * (-len(raw) % 4)
        alt = b"-_" if ("-" in raw or "_" in raw) else None
        try:
            text = base64.b64decode(raw, altchars=alt, validate=True).decode("utf-8")
        except (binascii.Error, ValueError):
            continue
        if text and all(ch.isprintable() or ch.isspace() for ch in text):
            out.append(text)
    return out


@lru_cache(maxsize=1024)
def _spaced_views(line: str) -> tuple[str, ...]:
    out: list[str] = []
    for text in (line, *_decoded_base64(line)):  # one level of base64 only
        base = clean(text)
        spoken = spoken_separators(base)
        out += [base, spoken, " ".join(spoken_digits(spoken.split()))]
    return tuple(dict.fromkeys(out))


@lru_cache(maxsize=1024)
def _all_views(line: str) -> tuple[str, ...]:
    spaced = _spaced_views(line)
    return tuple(dict.fromkeys([*spaced, *(_WS.sub("", v) for v in spaced)]))


def views(line: str) -> list[str]:
    """Every clean reading of a line, including compact ones without spaces."""
    return list(_all_views(line))


def find_disguised(text: str, value: object, amount: str | None) -> tuple[int, str] | None:
    """(1-based line, ORIGINAL line) where value appears in disguise, or None."""
    lines = text.splitlines() or [text]
    if amount is not None:
        # Spaced views only: squashing "14 99" into "1499" would invent numbers.
        pattern = re.compile(rf"(?<!\d){re.escape(amount)}(?!\d)")
        thousands = re.compile(r"(?<=\d)[,\s](?=\d)")
        for i, line in enumerate(lines, start=1):
            if any(pattern.search(thousands.sub("", v)) for v in _spaced_views(line)):
                return i, line
        return None
    needle = compact(str(value))
    if len(needle) < MIN_NEEDLE:
        return None
    for i, line in enumerate(lines, start=1):
        if any(needle in v for v in _all_views(line)):
            return i, line
    return None


def leaked_in_views(text: str, vault: dict[str, str]) -> list[str]:
    """Secret names whose value hides in a clean view of text (zero-width split, base64-wrapped...)."""
    found = _all_views(text)
    return [
        name for name, value in vault.items() if (v := value.lower()) and any(v in view for view in found)
    ]


# Look-alike letters -> the Latin letter they imitate. Used ONLY to say "looks like <value>" in R11's
# message, never to accept a value.
LOOKALIKES = str.maketrans(
    {
        "а": "a",
        "е": "e",
        "о": "o",
        "р": "p",
        "с": "c",
        "х": "x",
        "і": "i",
        "ѕ": "s",  # Cyrillic
        "А": "A",
        "Е": "E",
        "О": "O",
        "Р": "P",
        "С": "C",
        "Х": "X",
        "І": "I",
        "Ѕ": "S",
        "ο": "o",
        "α": "a",
        "Ο": "O",
        "Α": "A",  # Greek
    }
)


def fold_lookalikes(value: str) -> str:
    return value.translate(LOOKALIKES).translate(ZERO_WIDTH)
