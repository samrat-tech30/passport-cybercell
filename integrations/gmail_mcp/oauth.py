"""Google sign-in for the Gmail connector (OAuth 2.0 for desktop apps: loopback redirect + PKCE).

Checked 2026-10-31 (docs/API-NOTES.md "Gmail"): authorization at accounts.google.com/o/oauth2/v2/auth,
token exchange and refresh at oauth2.googleapis.com/token, loopback redirect http://127.0.0.1:<port>,
PKCE S256, and installed apps always get a refresh token.

The refresh token, client id and client secret are saved to ~/.passport/gmail-token.json (mode 600),
outside the repo, and are never printed or logged. Override the path with GMAIL_TOKEN_FILE.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any

import httpx

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"  # noqa: S105 - a URL, not a password
# Read the inbox and write drafts (the connector), and insert test emails into your own inbox (make
# gmail-seed, like an IMAP append). No send scope: an allowed send_email becomes a draft you send yourself.
SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.insert",
)


class AuthError(Exception):
    """Sign-in is missing or was refused. The message never contains a token."""


def token_file() -> Path:
    return Path(os.environ.get("GMAIL_TOKEN_FILE") or Path.home() / ".passport" / "gmail-token.json")


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)[:96]
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    return verifier, challenge


def save_credentials(data: dict[str, Any], path: Path | None = None) -> Path:
    path = path or token_file()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, path)
    return path


def load_credentials(path: Path | None = None) -> dict[str, Any]:
    path = path or token_file()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise AuthError("Not signed in to Gmail yet. Run: make gmail-login") from e
    if not all(
        isinstance(data.get(k), str) and data[k] for k in ("client_id", "client_secret", "refresh_token")
    ):
        raise AuthError("The Gmail sign-in file is incomplete. Run: make gmail-login")
    return data


class AccessToken:
    """Short-lived access token from the saved refresh token, refreshed a minute before it expires."""

    def __init__(self, creds: dict[str, Any], http: httpx.AsyncClient) -> None:
        self.creds, self.http = creds, http
        self.value: str | None = None
        self.expires = 0.0

    async def get(self, force: bool = False) -> str:
        if force or not self.value or time.time() > self.expires - 60:
            r = await self.http.post(
                TOKEN_URL,
                data={
                    "client_id": self.creds["client_id"],
                    "client_secret": self.creds["client_secret"],
                    "refresh_token": self.creds["refresh_token"],
                    "grant_type": "refresh_token",
                },
                timeout=15,
            )
            body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            if r.status_code != 200 or not isinstance(body.get("access_token"), str):
                # Google's error code only ("invalid_grant" = revoked or expired sign-in), never the body
                raise AuthError(
                    f"Gmail sign-in was refused ({body.get('error', r.status_code)}). Run: make gmail-login"
                )
            self.value = body["access_token"]
            self.expires = time.time() + int(body.get("expires_in", 3600))
        return self.value
