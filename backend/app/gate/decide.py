"""The Policy Decision Point: one tool call in, ALLOW / REQUIRE_APPROVAL / DENY out, with evidence.

Deterministic code over data origins. The LLM is allowed to be fooled; it just can't act on it.
Every rule that fires adds a Reason. Final verdict = the strongest one (DENY > ASK > ALLOW).
Any exception => DENY (fail closed).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from app.contracts import VERDICT_RANK, Capsule, Decision, Evidence, Origin, Reason, Verdict
from app.gate.disguise import fold_lookalikes
from app.gate.policy import Policy
from app.gate.segments import SegmentStore
from app.gate.tracer import trace
from app.tools.registry import TOOLS, InvalidArgs, validate_args
from app.tools.world import World

log = logging.getLogger("passport.gate")


@dataclass
class GateContext:
    session_id: str
    policy: Policy
    store: SegmentStore
    capsule: Capsule
    world: World
    profile: str
    fault: str | None = None  # "gate_error" injects a crash (scenario S8 proves fail-closed)


def _where(ev: Evidence) -> str:
    if ev.source and ev.line:
        return f"{ev.source}, line {ev.line}"
    return ev.source or "an unknown source"


def _lookalike_of(value: str, ctx: GateContext) -> str | None:
    """The trusted or user-typed value this one imitates, for the message only. Never used to allow."""
    folded = fold_lookalikes(value).lower()
    if not folded.isascii():
        return None
    for known in ctx.world.vendors.values():
        if known.lower() == folded:
            return known
    user = ctx.store.get("user")
    if user and folded in user.text.lower():
        i = user.text.lower().index(folded)
        return user.text[i : i + len(folded)]
    return None


def _safe_redact(ctx: GateContext, args: Any) -> dict[str, Any]:
    try:
        red = ctx.world.redact(args)
        return red if isinstance(red, dict) else {"_raw": str(red)[:500]}
    except Exception:  # noqa: BLE001 - redaction must never be the reason a DENY fails
        return {"_raw": "[unavailable]"}


def decide(ctx: GateContext, tool: str, raw_args: Any, step: int) -> Decision:
    try:
        return _decide(ctx, tool, raw_args, step)
    except InvalidArgs as e:
        return _deny0(ctx, tool, raw_args, step, f"Blocked: the call's arguments are invalid ({e}).")
    except Exception as e:  # noqa: BLE001 - fail closed on ANY error
        log.warning("gate error on %s: %s", tool, type(e).__name__)
        return _deny0(ctx, tool, raw_args, step, "The gate hit an error, so the call was blocked to be safe.")


def _deny0(ctx: GateContext, tool: str, raw_args: Any, step: int, message: str) -> Decision:
    risk = ctx.policy.risk.get("R0_FAIL_CLOSED", 100) if ctx.policy else 100
    reason = Reason(rule_id="R0_FAIL_CLOSED", verdict=Verdict.DENY, message=message, risk=risk)
    return Decision(
        session_id=ctx.session_id,
        step=step,
        tool=str(tool)[:64],
        args=_safe_redact(ctx, raw_args),
        verdict=Verdict.DENY,
        rule_id="R0_FAIL_CLOSED",
        message=message,
        risk=risk,
        reasons=[reason],
    )


def _decide(ctx: GateContext, tool: str, raw_args: Any, step: int) -> Decision:
    if ctx.fault == "gate_error":
        raise RuntimeError("injected fault (scenario S8)")
    if tool not in TOOLS:
        raise InvalidArgs(f"unknown tool {tool!r}")
    args = validate_args(tool, raw_args)

    P, store, cap, world = ctx.policy, ctx.store, ctx.capsule, ctx.world
    redact = world.redact
    reasons: list[Reason] = []

    def add(rule: str, verdict: Verdict, message: str, ev: Evidence | None = None) -> None:
        reasons.append(Reason(rule_id=rule, verdict=verdict, message=message, risk=P.risk[rule], evidence=ev))

    # R1: is this tool allowed for this assistant at all?
    if tool not in P.profiles[ctx.profile]:
        add("R1_PROFILE", Verdict.DENY, f"This assistant is not allowed to use {tool}.")

    # R2: canary secrets in ANY argument, in any common encoding = proof of exfiltration.
    leaked = world.leaked_secrets(json.dumps(args, ensure_ascii=False))
    if leaked:
        add(
            "R2_CANARY",
            Verdict.DENY,
            f"Secret {', '.join(leaked)} is inside the arguments: this would leak it.",
        )

    # R3 / R4 / R5: the passport of every sink argument.
    passports: list[Evidence] = []
    soft = P.soft_sinks.get(tool, frozenset())
    for arg in P.sinks.get(tool, ()):
        if arg not in args:
            continue
        ev = trace(arg, args[arg], store, redact)
        passports.append(ev)
        if ev.origin == Origin.UNTRUSTED and arg in soft:
            add(
                "R7_HIGH_IMPACT",
                Verdict.REQUIRE_APPROVAL,
                f"'{arg}' = {ev.value} was read from {_where(ev)}. Please check it.",
                ev,
            )
        elif ev.origin == Origin.UNTRUSTED:
            add(
                "R3_SINK_UNTRUSTED",
                Verdict.DENY,
                f"'{arg}' = {ev.value} came from {_where(ev)}{' (written in disguise)' if ev.disguised else ''}:"
                " content you didn't write can't choose this.",
                ev,
            )
        elif ev.origin == Origin.SECRET and tool in P.egress:
            add("R4_SECRET_EGRESS", Verdict.DENY, f"'{arg}' is a secret value and {tool} sends data out.", ev)
        elif ev.origin == Origin.MODEL_INVENTED and store.read_untrusted:
            add(
                "R5_SINK_INVENTED",
                Verdict.REQUIRE_APPROVAL,
                f"'{arg}' = {ev.value} wasn't typed by you or found in a trusted source (the AI wrote it after reading outside content).",
                ev,
            )

        # R11: addresses, accounts, paths and keys are plain ASCII. Any other character is a disguise.
        if isinstance(args[arg], str) and not args[arg].isascii():
            twin = _lookalike_of(args[arg], ctx)
            add(
                "R11_LOOKALIKE",
                Verdict.DENY,
                f"'{arg}' = {ev.value} contains look-alike characters"
                + (f" (looks like {twin})." if twin else " that are not plain letters or digits."),
                ev,
            )

    # R4 also covers non-sink arguments of egress tools (e.g. a body that IS a secret).
    if tool in P.egress:
        for arg, value in args.items():
            if arg in P.sinks.get(tool, ()) or not isinstance(value, str) or len(value) < 6:
                continue
            ev = trace(arg, value, store, redact, sink=False)
            if ev.origin == Origin.SECRET:
                add(
                    "R4_SECRET_EGRESS",
                    Verdict.DENY,
                    f"'{arg}' is a secret value and {tool} sends data out.",
                    ev,
                )

    # R6: outside the frozen intent.
    if tool not in cap.allowed_tools:
        add("R6_OUT_OF_INTENT", Verdict.REQUIRE_APPROVAL, f"You didn't ask me to use {tool}.")
    amount = args.get("amount_inr")
    if cap.max_amount_inr is not None and isinstance(amount, int) and amount > cap.max_amount_inr:
        add(
            "R6_OUT_OF_INTENT",
            Verdict.REQUIRE_APPROVAL,
            f"Rs {amount:,} is above your limit of Rs {cap.max_amount_inr:,}.",
        )

    # R8: lethal trifecta - secret seen + outside content seen + data leaving.
    if tool in P.egress and store.revealed and store.read_untrusted:
        add(
            "R8_TRIFECTA",
            Verdict.REQUIRE_APPROVAL,
            "This session has seen a secret and outside content, so sending data out needs your OK.",
        )

    # R7: high-impact tools always need a human yes.
    if tool in P.high_impact and not any(r.verdict != Verdict.ALLOW for r in reasons):
        add("R7_HIGH_IMPACT", Verdict.REQUIRE_APPROVAL, f"{tool} is a high-impact action.")

    return _combine(ctx, tool, args, step, reasons, passports)


def _combine(
    ctx: GateContext,
    tool: str,
    args: dict[str, Any],
    step: int,
    reasons: list[Reason],
    passports: list[Evidence],
) -> Decision:
    redacted = ctx.world.redact(args)
    if not reasons:
        return Decision(
            session_id=ctx.session_id,
            step=step,
            tool=tool,
            args=redacted,
            verdict=Verdict.ALLOW,
            rule_id="ALLOW",
            message="Every value traced to you or a trusted source.",
            risk=0,
            reasons=[],
            passports=passports,
        )
    verdict = max((r.verdict for r in reasons), key=VERDICT_RANK.__getitem__)
    primary = max((r for r in reasons if r.verdict == verdict), key=lambda r: r.risk)
    return Decision(
        session_id=ctx.session_id,
        step=step,
        tool=tool,
        args=redacted,
        verdict=verdict,
        rule_id=primary.rule_id,
        message=primary.message,
        risk=max(r.risk for r in reasons),
        reasons=reasons,
        passports=passports,
    )
