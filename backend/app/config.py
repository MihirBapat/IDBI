"""Config-as-product loader.

The product shelf, strategy library, category map, and suitability rules are
versioned YAML treated as product, not code (architecture §11). Every engine
that consumes one pins its content hash (``sha256`` of the file bytes, first 12
hex) into the reasoning trace, so a recommendation is bit-for-bit attributable
to the exact config that produced it.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

DATA_DIR = Path(__file__).resolve().parent / "data"


@lru_cache(maxsize=None)
def _read_bytes(name: str) -> bytes:
    return (DATA_DIR / name).read_bytes()


def load_yaml(name: str) -> Any:
    """Load a YAML config file from ``app/data/`` by filename."""
    return yaml.safe_load(_read_bytes(name).decode("utf-8"))


def file_sha(name: str) -> str:
    """First 12 hex of the sha256 of the config file — the version pin.

    Line endings are normalized to LF before hashing so the pin is stable across
    platforms and git checkouts (autocrlf must not change a config's identity).
    """
    normalized = _read_bytes(name).replace(b"\r\n", b"\n")
    return hashlib.sha256(normalized).hexdigest()[:12]
