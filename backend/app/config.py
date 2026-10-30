"""Every environment variable is read and validated here, once, at start-up.

Nothing else in the backend reads os.environ. If a value is invalid the app refuses to start
with a clear message (fail early, not at 3 a.m. during the demo).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


class ConfigError(RuntimeError):
    pass


def _bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    if raw.lower() in {"1", "true", "yes", "on"}:
        return True
    if raw.lower() in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"{name} must be true or false, got {raw!r}")


def _int(name: str, default: int, lo: int, hi: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError as e:
        raise ConfigError(f"{name} must be a whole number, got {raw!r}") from e
    if not lo <= value <= hi:
        raise ConfigError(f"{name} must be between {lo} and {hi}, got {value}")
    return value


@dataclass(frozen=True)
class Settings:
    app_env: str = "dev"
    data_dir: Path = BACKEND_DIR / "var"
    allowed_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")
    demo_access_code: str | None = None
    llm_base_url: str | None = None
    llm_api_key: str | None = field(default=None, repr=False)  # never printed
    llm_model: str | None = None
    llm_timeout_s: int = 30
    allow_live_llm: bool = True
    record_fixtures: bool = False  # live sessions save their turns to app/fixtures/ for replay
    approval_timeout_s: int = 120
    max_agent_steps: int = 8
    rate_limit_per_min: int = 30
    max_body_bytes: int = 64_000
    gateway_token: str | None = field(default=None, repr=False)  # unset = gateway API off (503)
    gateway_approval_wait_s: int = 40  # below the MCP client's ~60 s tool timeout
    gateway_rate_limit_per_min: int = 300

    @property
    def db_path(self) -> Path:
        return self.data_dir / "passport.db"

    @property
    def live_llm_ready(self) -> bool:
        return bool(self.allow_live_llm and self.llm_base_url and self.llm_api_key and self.llm_model)


def load_settings() -> Settings:
    app_env = os.environ.get("APP_ENV", "dev").strip().lower()
    if app_env not in {"dev", "test", "prod"}:
        raise ConfigError(f"APP_ENV must be dev, test or prod, got {app_env!r}")

    origins_raw = os.environ.get("ALLOWED_ORIGINS", "")
    origins = (
        tuple(o.strip().rstrip("/") for o in origins_raw.split(",") if o.strip()) or Settings.allowed_origins
    )
    if "*" in origins:
        raise ConfigError("ALLOWED_ORIGINS must list real origins; '*' is not allowed")
    if app_env == "prod" and any("localhost" in o or "127.0.0.1" in o for o in origins) and not origins_raw:
        raise ConfigError("In prod, set ALLOWED_ORIGINS to the deployed frontend URL")

    data_dir = Path(os.environ.get("DATA_DIR") or (BACKEND_DIR / "var")).resolve()

    code = os.environ.get("DEMO_ACCESS_CODE") or None
    if code is not None and len(code) < 6:
        raise ConfigError("DEMO_ACCESS_CODE must be at least 6 characters (or unset)")

    gateway_token = os.environ.get("PASSPORT_GATEWAY_TOKEN") or None
    if gateway_token is not None and len(gateway_token) < 24:
        raise ConfigError("PASSPORT_GATEWAY_TOKEN must be at least 24 characters (or unset)")

    return Settings(
        app_env=app_env,
        data_dir=data_dir,
        allowed_origins=origins,
        demo_access_code=code,
        llm_base_url=os.environ.get("LLM_BASE_URL") or None,
        llm_api_key=os.environ.get("LLM_API_KEY") or None,
        llm_model=os.environ.get("LLM_MODEL") or None,
        llm_timeout_s=_int("LLM_TIMEOUT_S", 30, 5, 120),
        # Live LLM calls cost money and can be abused on a public URL: off by default in prod.
        allow_live_llm=_bool("ALLOW_LIVE_LLM", app_env != "prod"),
        record_fixtures=_bool("RECORD_FIXTURES", False),
        approval_timeout_s=_int("APPROVAL_TIMEOUT_S", 120, 5, 600),
        max_agent_steps=_int("MAX_AGENT_STEPS", 8, 1, 20),
        rate_limit_per_min=_int("RATE_LIMIT_PER_MIN", 30, 1, 10_000),
        max_body_bytes=_int("MAX_BODY_BYTES", 64_000, 1_000, 1_000_000),
        gateway_token=gateway_token,
        gateway_approval_wait_s=_int("GATEWAY_APPROVAL_WAIT_S", 40, 1, 55),
    )


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def reset_settings_for_tests() -> None:
    global _settings
    _settings = None
