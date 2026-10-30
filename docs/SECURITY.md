# Security of PASSPORT itself

PASSPORT is a security product, so judges will poke the app too. This page lists every control, where it lives, and how it's tested.

## Backend (FastAPI)
| Control | Where | Test |
|---|---|---|
| Strict request models (`extra="forbid"`, max lengths, id patterns) | `app/api/schemas.py` | test_api: unknown fields → 422 |
| Uniform error body, no stack traces | `app/main.py` handlers | test_api, contracts/examples |
| Security headers (nosniff, DENY framing, no-referrer, CSP `default-src 'none'`, no-store) | `app/security.py` (pure ASGI, SSE-safe) | test_api: health headers |
| Body size limit (413) | `BodySizeLimitMiddleware` | test_api: 70 KB body → 413 |
| Rate limit per client (429) on sessions, eval, decide | `RateLimiter` | test_api: 3rd call → 429 |
| Optional demo access code on all POSTs (constant-time compare) | `require_access` | test_api: 401 without code |
| CORS allowlist from env, never `*`, no credentials | `app/main.py`, `config.py` refuses `*` | test_api: evil origin gets no ACAO |
| Config validated at start-up; bad values stop the app | `app/config.py` | – |
| Live LLM off by default in prod (cost abuse) | `ALLOW_LIVE_LLM` | – |
| API docs hidden in prod | `docs_url=None` when `APP_ENV=prod` | – |
| Non-root container, only `/data` writable | `backend/Dockerfile` | – |
| Real client IP behind proxies (for rate limiting) | uvicorn `--proxy-headers` | – |

## Data
| Control | Where |
|---|---|
| All data synthetic, `.test` domains | `app/world_data/` |
| Canary secrets random per session, never in the repo | `tools/world.py` |
| Secrets redacted (raw/base64/hex/URL/reversed) before DB, audit, events, API | `world.redact()`; test_scenarios `test_secrets_never_reach_the_database_or_audit_log` |
| Hidden vault segments never served by the evidence endpoint | `routes.segment` → 404 |
| File tools can't leave the shared drive (`..`, absolute, backslash, NUL) | `World._safe_path`; test_world |
| Delete/pay/send are in-memory only | `tools/world.py` |
| SQL only with `?` parameters, only in `app/db/` | guard hook checks f-string SQL |
| Audit log append-only in code, hash-chained | `app/db/audit.py` |

## Frontend
| Control | Where |
|---|---|
| No `dangerouslySetInnerHTML`; evidence shows hidden HTML as text | components |
| Only `VITE_API_URL` in env (public); access code kept in sessionStorage, sent only as a header | `lib/api/client.ts` |
| Security headers on static hosting | `frontend/vercel.json`, `public/_headers` |

## Repo hygiene
`.env*` ignored (except examples) · guard hook blocks API keys, private keys, JWTs and canary values in files · `.claude/settings.json` denies reading `.env` and rewriting git history · CI runs `scripts/check.sh` on every push.

## Known gaps (honest)
- In-memory rate limiter and session registry: fine for one demo instance, not for several replicas.
- SQLite on a free host's disk may reset on redeploy (fine for a demo; say so).
- No user accounts: the access code protects a demo URL, it isn't authentication.
