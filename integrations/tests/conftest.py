"""Integration tests reuse the backend's test setup (temp database, test settings, no network).

The two servers are both called server.py, so they are loaded under distinct module names.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

from tests.conftest import fresh_db  # noqa: E402, F401  (sets test env before the app is imported)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


nimbus = _load("nimbus_server", ROOT / "integrations" / "nimbus_mcp" / "server.py")
gateway = _load("passport_gateway_server", ROOT / "integrations" / "passport_gateway" / "server.py")
