"""Add the PASSPORT gateway to Claude Desktop (macOS / Windows) in one command.

    make claude-setup                 # your real Gmail (PASSPORT_UPSTREAM=gmail), server name "passport-gmail"
    make claude-setup UPSTREAM=nimbus # the synthetic demo inbox instead, server name "passport-demo"

What it does:
  * reads PASSPORT_GATEWAY_TOKEN from backend/.env (never prints it);
  * backs up claude_desktop_config.json to claude_desktop_config.json.bak-<time>;
  * adds or replaces ONLY its own entry under "mcpServers", keeping every other server you have;
  * stops without writing anything if the existing file isn't valid JSON.
Then quit Claude Desktop completely (Cmd+Q) and open it again.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def config_path() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if sys.platform == "win32":
        return Path(os.environ["APPDATA"]) / "Claude" / "claude_desktop_config.json"
    return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def gateway_token(env_file: Path) -> str:
    token = os.environ.get("PASSPORT_GATEWAY_TOKEN", "")
    if not token and env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() == "PASSPORT_GATEWAY_TOKEN":
                token = value.split(" #", 1)[0].strip().strip('"').strip("'")
    if len(token) < 24:
        raise SystemExit(
            "Put PASSPORT_GATEWAY_TOKEN (24+ characters) in backend/.env first, and restart make backend."
        )
    return token


def main() -> None:
    ap = argparse.ArgumentParser(description="Add the PASSPORT gateway to Claude Desktop")
    ap.add_argument("--upstream", choices=("gmail", "nimbus"), default="gmail")
    ap.add_argument("--env-file", type=Path, default=ROOT / "backend" / ".env")
    a = ap.parse_args()

    if a.upstream == "gmail" and not (Path.home() / ".passport" / "gmail-token.json").is_file():
        raise SystemExit("Sign in to Gmail first: make gmail-login")
    python = ROOT / "backend" / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not python.is_file():
        raise SystemExit(f"No backend venv at {python}. Run: make setup")

    path = config_path()
    config: dict = {}
    if path.is_file() and path.read_text(encoding="utf-8").strip():
        try:
            config = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as e:
            raise SystemExit(f"{path} is not valid JSON ({e}). Fix or move it, then run this again.") from e
        backup = path.with_name(f"{path.name}.bak-{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.copy2(path, backup)
        print(f"Backed up your current config to {backup}")
    if not isinstance(config, dict):
        raise SystemExit(f"{path} doesn't contain a JSON object. Fix or move it, then run this again.")

    name = "passport-gmail" if a.upstream == "gmail" else "passport-demo"
    env = {
        "PASSPORT_URL": "http://127.0.0.1:8000",
        "PASSPORT_GATEWAY_TOKEN": gateway_token(a.env_file),
        "PASSPORT_UPSTREAM": a.upstream,
        "PASSPORT_AGENT_NAME": "Claude Desktop",
    }
    if a.upstream == "nimbus":
        env["NIMBUS_INBOX"] = "s2_hidden_instruction"
    servers = config.setdefault("mcpServers", {})
    servers[name] = {
        "command": str(python),
        "args": [str(ROOT / "integrations" / "passport_gateway" / "server.py")],
        "env": env,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)  # it now holds the gateway token
    others = sorted(k for k in servers if k != name)
    print(f'Added "{name}" to {path}' + (f" (kept: {', '.join(others)})" if others else ""))
    print("Now quit Claude Desktop completely (Cmd+Q) and open it again.")


if __name__ == "__main__":
    main()
