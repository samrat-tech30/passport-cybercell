"""Does the configured LLM provider do tool calling? One request, one answer. Never prints the key.

    cd backend
    .venv/Scripts/python scripts/llm_probe.py                      # uses LLM_* from backend/.env
    .venv/Scripts/python scripts/llm_probe.py --model other-model  # try another model, same provider
    .venv/Scripts/python scripts/llm_probe.py --base-url https://... --model m --key-var GROQ_API_KEY

--key-var names another variable in backend/.env (or the shell) that holds that provider's key.
Exit code 0 = a well-formed tool call came back, 1 = it did not, 2 = setup problem.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

TOOL = {
    "type": "function",
    "function": {
        "name": "send_email",
        "description": "Send an email.",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        },
    },
}
PROMPT = "Send an email to priya@nimbus.test with subject 'Standup' saying the standup moves to 10:30."


def load_env(args: argparse.Namespace) -> None:
    from dotenv import dotenv_values

    for k, v in dotenv_values(BACKEND_DIR / ".env").items():
        if v is not None:
            os.environ.setdefault(k, v)
    if args.base_url:
        os.environ["LLM_BASE_URL"] = args.base_url
    if args.model:
        os.environ["LLM_MODEL"] = args.model
    if args.key_var:
        os.environ["LLM_API_KEY"] = os.environ.get(args.key_var, "")


async def probe() -> int:
    from openai import AsyncOpenAI, OpenAIError

    from app.config import ConfigError, load_settings

    try:
        st = load_settings()
    except ConfigError as e:
        print(f"config error: {e}")
        return 2
    missing = [n for n, v in (("LLM_BASE_URL", st.llm_base_url), ("LLM_MODEL", st.llm_model)) if not v]
    if missing:
        print(f"missing: {', '.join(missing)}")
        return 2
    print(
        f"provider: {st.llm_base_url}\nmodel:    {st.llm_model}\nkey:      {'set' if st.llm_api_key else 'NOT set'}"
    )
    client = AsyncOpenAI(
        base_url=st.llm_base_url, api_key=st.llm_api_key or "none", timeout=st.llm_timeout_s, max_retries=0
    )
    t0 = time.perf_counter()
    try:
        raw = await client.chat.completions.with_raw_response.create(
            model=st.llm_model,
            messages=[{"role": "user", "content": PROMPT}],
            tools=[TOOL],
            tool_choice="auto",
            temperature=0,
        )
    except OpenAIError as e:
        status = getattr(e, "status_code", None)
        print(
            f"FAILED: {type(e).__name__}{f' (HTTP {status})' if status else ''} after {time.perf_counter() - t0:.1f} s"
        )
        detail = str(e).replace(st.llm_api_key, "[key]") if st.llm_api_key else str(e)
        print(f"detail: {detail[:300]}")
        return 1
    print(f"latency:  {time.perf_counter() - t0:.1f} s")
    limits = {k: v for k, v in raw.headers.items() if k.lower().startswith(("x-ratelimit", "retry-after"))}
    for k, v in sorted(limits.items()):
        print(f"header:   {k}: {v}")
    choice = raw.parse().choices[0]
    print(f"finish:   {choice.finish_reason}")
    calls = choice.message.tool_calls or []
    if not calls:
        print(f"NO tool call. Text: {(choice.message.content or '')[:200]!r}")
        return 1
    ok = True
    for c in calls:
        try:
            args = json.loads(c.function.arguments or "{}")
            good = c.function.name == "send_email" and args.get("to") == "priya@nimbus.test"
            print(f"call:     {c.function.name} {json.dumps(args)[:200]} -> {'OK' if good else 'WRONG'}")
            ok = ok and good
        except json.JSONDecodeError:
            print(f"call:     {c.function.name} with INVALID JSON args: {c.function.arguments[:200]!r}")
            ok = False
    print("RESULT:   tool calling works" if ok else "RESULT:   tool call came back but was wrong")
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url")
    ap.add_argument("--model")
    ap.add_argument("--key-var", help="env var holding this provider's key (default LLM_API_KEY)")
    args = ap.parse_args()
    load_env(args)
    sys.exit(asyncio.run(probe()))


if __name__ == "__main__":
    main()
