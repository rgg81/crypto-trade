"""Canonical completion clock for the CUP-50 paper desk."""

from __future__ import annotations

import pandas as pd

INTERVAL = pd.Timedelta(hours=8)
DEFAULT_LAG_SECONDS = 25 * 60


def _utc(value: object) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        raise ValueError("paper timestamps must be timezone-aware UTC")
    return stamp.tz_convert("UTC")


def ready_boundary(now: object, *, lag_seconds: int = DEFAULT_LAG_SECONDS) -> pd.Timestamp:
    """Newest decision whose own transaction bar closed and cleared publication lag."""
    if lag_seconds < 0:
        raise ValueError("publication lag cannot be negative")
    return (_utc(now) - pd.Timedelta(seconds=lag_seconds)).floor("8h") - INTERVAL
