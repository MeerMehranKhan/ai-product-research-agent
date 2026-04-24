from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / ".vendor"


def configure_paths() -> None:
    """Prefer the active environment and keep vendored packages as fallback."""
    root_path = str(ROOT)
    vendor_path = str(VENDOR)

    sys.path[:] = [path for path in sys.path if path not in {root_path, vendor_path}]
    sys.path.insert(0, root_path)

    if VENDOR.exists():
        sys.path.append(vendor_path)
