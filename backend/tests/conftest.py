"""Test setup: a fresh temporary database per test, test settings, no network."""

from __future__ import annotations

import os
import tempfile

# Must be set before the app (and its settings) are imported anywhere.
os.environ["APP_ENV"] = "test"
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="passport-test-")
os.environ.pop("DEMO_ACCESS_CODE", None)
os.environ.pop("LLM_API_KEY", None)

import pytest  # noqa: E402

from app.config import get_settings, reset_settings_for_tests  # noqa: E402
from app.db import database  # noqa: E402
from app.security import limiter  # noqa: E402
from app.sessions import PENDING, SESSIONS  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    reset_settings_for_tests()
    database.close()
    database.connect(get_settings().db_path)
    limiter.reset()
    SESSIONS.clear()
    PENDING.clear()
    yield
    database.close()
    reset_settings_for_tests()
