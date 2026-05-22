"""Structured decision log for live engine — JSONL.

Captures the data needed to post-mortem any live↔backtest parity break:
signal evaluations (probabilities, threshold, decision), feature values seen
at inference, training completions, and cache load/clear events. Append-only,
one JSON object per line.

Singleton — call ``configure(path)`` once at engine start. ``log(event)`` is
a no-op if not configured (so backtest/test code paths stay clean).
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from threading import Lock
from typing import Any

import numpy as np

_LOG_FILE: Path | None = None
_LOCK = Lock()


def configure(log_path: Path) -> None:
    """Set the JSONL output file. Creates parent directories."""
    global _LOG_FILE
    _LOG_FILE = Path(log_path)
    _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def is_configured() -> bool:
    return _LOG_FILE is not None


def log(event: dict[str, Any]) -> None:
    """Append one event to the JSONL file. No-op when not configured."""
    if _LOG_FILE is None:
        return
    event.setdefault("ts_ms", int(time.time() * 1000))
    with _LOCK:
        with open(_LOG_FILE, "a") as f:
            f.write(json.dumps(event, default=_json_default) + "\n")


def hash_features(values: np.ndarray) -> str:
    """Stable short hash of a feature row (handles NaN consistently)."""
    arr = np.asarray(values, dtype=np.float64)
    return hashlib.sha256(arr.tobytes()).hexdigest()[:16]


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (np.integer, np.int_)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64)):
        v = float(obj)
        return v if not np.isnan(v) else None
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, Path):
        return str(obj)
    return repr(obj)
