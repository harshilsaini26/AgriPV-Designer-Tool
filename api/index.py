"""Vercel Python function: every /api/* request is rewritten here (vercel.json)."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.app import app

__all__ = ["app"]
