"""HTTP-level protection for the backend itself (separate from the PASSPORT gate).

* Security headers on every response (no sniffing, no framing, no caching of API data).
* Request body size limit (413 before we parse anything big).
* Per-client rate limit on expensive endpoints (429).
* Optional demo access code for anything that starts work or changes state (401).
"""

from __future__ import annotations

import hmac
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.config import get_settings

SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    (b"cross-origin-opener-policy", b"same-origin"),
    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
    (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'"),
    (b"cache-control", b"no-store"),
]


class SecurityHeadersMiddleware:
    """Pure ASGI (safe for streaming responses such as SSE)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                existing = {k.lower() for k, _ in message.get("headers", [])}
                message.setdefault("headers", [])
                message["headers"] = list(message["headers"]) + [
                    (k, v) for k, v in SECURITY_HEADERS if k not in existing
                ]
            await send(message)

        await self.app(scope, receive, send_with_headers)


class BodySizeLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            for k, v in scope.get("headers", []):
                if k == b"content-length" and v.isdigit() and int(v) > self.max_bytes:
                    body = b'{"error":{"code":"payload_too_large","message":"Request body is too large."}}'
                    await send(
                        {
                            "type": "http.response.start",
                            "status": 413,
                            "headers": [(b"content-type", b"application/json"), *SECURITY_HEADERS],
                        }
                    )
                    await send({"type": "http.response.body", "body": body})
                    return
        await self.app(scope, receive, send)


class RateLimiter:
    """Sliding one-minute window per (client, bucket). In memory: fine for one demo instance."""

    def __init__(self) -> None:
        self.hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    def check(self, client: str, bucket: str, limit: int) -> None:
        now = time.monotonic()
        q = self.hits[(client, bucket)]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(
                status_code=429,
                detail={"code": "rate_limited", "message": "Too many requests. Wait a minute."},
            )
        q.append(now)

    def reset(self) -> None:
        self.hits.clear()


limiter = RateLimiter()


def client_id(request: Request) -> str:
    # Behind a proxy, run uvicorn with --proxy-headers so request.client is the real caller.
    return request.client.host if request.client else "unknown"


def rate_limit(bucket: str):
    def dep(request: Request) -> None:
        limiter.check(client_id(request), bucket, get_settings().rate_limit_per_min)

    return dep


def require_access(request: Request) -> None:
    """If DEMO_ACCESS_CODE is set, state-changing calls must send it in X-Demo-Code."""
    code = get_settings().demo_access_code
    if code is None:
        return
    given = request.headers.get("x-demo-code", "")
    if not hmac.compare_digest(given.encode(), code.encode()):
        raise HTTPException(
            status_code=401, detail={"code": "access_code_required", "message": "Enter the demo access code."}
        )
