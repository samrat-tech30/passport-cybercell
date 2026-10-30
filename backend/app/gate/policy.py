"""Load and validate policy.yaml. A broken policy stops the app at start-up (fail closed)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from app.tools.registry import TOOLS

POLICY_PATH = Path(__file__).resolve().parent / "policy.yaml"
RULE_IDS = {
    "R0_FAIL_CLOSED",
    "R1_PROFILE",
    "R2_CANARY",
    "R3_SINK_UNTRUSTED",
    "R4_SECRET_EGRESS",
    "R5_SINK_INVENTED",
    "R6_OUT_OF_INTENT",
    "R7_HIGH_IMPACT",
    "R8_TRIFECTA",
    "R11_LOOKALIKE",
}


class PolicyError(RuntimeError):
    pass


@dataclass(frozen=True)
class Policy:
    profiles: dict[str, frozenset[str]]
    default_profile: str
    sinks: dict[str, tuple[str, ...]]
    soft_sinks: dict[str, frozenset[str]]
    egress: frozenset[str]
    high_impact: frozenset[str]
    risk: dict[str, int]


def _tools(names, where: str) -> frozenset[str]:
    unknown = set(names) - set(TOOLS)
    if unknown:
        raise PolicyError(f"{where} names unknown tool(s): {sorted(unknown)}")
    return frozenset(names)


def parse_policy(raw: dict) -> Policy:
    try:
        profiles = {name: _tools(tools, f"profile {name}") for name, tools in raw["profiles"].items()}
        default = raw["default_profile"]
        if default not in profiles:
            raise PolicyError(f"default_profile {default!r} is not a profile")
        sinks: dict[str, tuple[str, ...]] = {}
        for tool, args in raw.get("sinks", {}).items():
            _tools([tool], "sinks")
            params = {p.name for p in TOOLS[tool].params}
            if not set(args) <= params:
                raise PolicyError(f"sinks for {tool} name unknown argument(s): {sorted(set(args) - params)}")
            sinks[tool] = tuple(args)
        soft = {tool: frozenset(args) for tool, args in raw.get("soft_sinks", {}).items()}
        for tool, args in soft.items():
            if not args <= set(sinks.get(tool, ())):
                raise PolicyError(f"soft_sinks for {tool} must also be sinks")
        risk = {k: int(v) for k, v in raw["risk"].items()}
        if set(risk) != RULE_IDS:
            raise PolicyError(f"risk must list exactly these rules: {sorted(RULE_IDS)}")
        return Policy(
            profiles=profiles,
            default_profile=default,
            sinks=sinks,
            soft_sinks=soft,
            egress=_tools(raw.get("egress", []), "egress"),
            high_impact=_tools(raw.get("high_impact", []), "high_impact"),
            risk=risk,
        )
    except (KeyError, TypeError, ValueError) as e:
        raise PolicyError(f"policy.yaml is malformed: {e}") from e


@lru_cache(maxsize=1)
def load_policy(path: Path = POLICY_PATH) -> Policy:
    return parse_policy(yaml.safe_load(path.read_text(encoding="utf-8")))
