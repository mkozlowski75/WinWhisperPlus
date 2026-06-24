"""Helpers for resolving bundled application resources."""

from __future__ import annotations

import sys
from pathlib import Path


def resource_path(relative_path: str) -> Path:
    """Return a resource path for source runs and PyInstaller bundles."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base_path / relative_path


def app_version(default: str = "unknown") -> str:
    """Return the application version from the bundled VERSION file."""
    try:
        version = resource_path("VERSION").read_text(encoding="ascii").strip()
    except OSError:
        return default
    return version or default
