"""Pytest configuration for commercial-agent tests.

The production code uses module-level imports that resolve relative to the
repo root (e.g. `from config.system_prompt import ...`, `from tools import ...`).
We make the repo root importable so tests can import these packages as-is,
without needing to install the commercial-agent as a package.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
