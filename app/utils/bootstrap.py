"""Ensure app and src packages are importable from page scripts."""

from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parents[1]
_SRC_DIR = _APP_DIR.parent / "src"

for path in (_APP_DIR, _SRC_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)
