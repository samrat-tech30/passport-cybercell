"""Sign in to Gmail once, for the PASSPORT Gmail connector.

    make gmail-login        (= backend/.venv/bin/python integrations/gmail_mcp/login.py --env-file backend/.env)

Reads GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET (your Google Cloud "Desktop app" OAuth client) from the
environment or from --env-file, prints a Google sign-in link, waits for Google to redirect back to
http://127.0.0.1:<random port>, and saves the refresh token to ~/.passport/gmail-token.json (mode 600).
Scopes: read mail + write drafts. Nothing is ever sent from your account.
"""

from __future__ import annotations

import argparse
import os
import secrets
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from oauth import AUTH_URL, SCOPES, TOKEN_URL, pkce_pair, save_credentials  # noqa: E402


def read_env_file(path: Path) -> dict[str, str]:
    """Only the two Gmail client values, from a KEY=value file."""
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip() in ("GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET"):
            out[key.strip()] = value.split(" #", 1)[0].strip().strip('"').strip("'")
    return out


class _Callback(BaseHTTPRequestHandler):
    """Receives Google's redirect once. The code never reaches the terminal or a log."""

    expected_state = ""
    result: dict[str, str] = {}

    def do_GET(self) -> None:  # noqa: N802 - the stdlib's name
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        ok = q.get("state", [""])[0] == self.expected_state and "code" in q
        if ok:
            _Callback.result["code"] = q["code"][0]
        elif "favicon" not in self.path:
            _Callback.result["error"] = q.get("error", ["state mismatch"])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        msg = (
            "Signed in. Close this tab and go back to the terminal."
            if ok
            else "Sign-in failed: see the terminal."
        )
        self.wfile.write(msg.encode())

    def log_message(self, *args: object) -> None:
        return


def main() -> None:
    ap = argparse.ArgumentParser(description="Sign in to Gmail for the PASSPORT Gmail connector")
    ap.add_argument("--env-file", type=Path, help="read GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET from this file")
    a = ap.parse_args()
    env = read_env_file(a.env_file) if a.env_file and a.env_file.is_file() else {}
    client_id = os.environ.get("GMAIL_CLIENT_ID") or env.get("GMAIL_CLIENT_ID", "")
    client_secret = os.environ.get("GMAIL_CLIENT_SECRET") or env.get("GMAIL_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise SystemExit(
            "Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in backend/.env (see integrations/README.md)."
        )

    verifier, challenge = pkce_pair()
    _Callback.expected_state = secrets.token_urlsafe(24)
    server = HTTPServer(("127.0.0.1", 0), _Callback)
    redirect = f"http://127.0.0.1:{server.server_port}"
    url = (
        AUTH_URL
        + "?"
        + urllib.parse.urlencode(
            {
                "client_id": client_id,
                "redirect_uri": redirect,
                "response_type": "code",
                "scope": " ".join(SCOPES),
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "state": _Callback.expected_state,
                "access_type": "offline",
                "prompt": "consent",
            }
        )
    )
    print("\nOpen this link, sign in with the Gmail account you added as a test user, and allow access:\n")
    print(url + "\n")
    try:
        webbrowser.open(url)
    except webbrowser.Error:
        pass
    while not _Callback.result:
        server.handle_request()
    server.server_close()
    if "error" in _Callback.result:
        raise SystemExit(f"Google sign-in failed: {_Callback.result['error']}")

    r = httpx.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": _Callback.result["code"],
            "code_verifier": verifier,
            "grant_type": "authorization_code",
            "redirect_uri": redirect,
        },
        timeout=20,
    )
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    if r.status_code != 200 or not body.get("refresh_token"):
        raise SystemExit(f"Google refused the sign-in ({body.get('error', r.status_code)}).")
    path = save_credentials(
        {"client_id": client_id, "client_secret": client_secret, "refresh_token": body["refresh_token"]}
    )
    print(f"Signed in. Saved to {path} (only your user can read it). The gateway can now use your Gmail.")


if __name__ == "__main__":
    main()
