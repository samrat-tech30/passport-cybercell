"""Gateway tests reuse the backend's test setup (temp database, test settings, no network)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
for p in (ROOT / "backend", ROOT / "integrations" / "mcp_gateway"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from tests.conftest import fresh_db  # noqa: E402, F401  (sets test env before the app is imported)
