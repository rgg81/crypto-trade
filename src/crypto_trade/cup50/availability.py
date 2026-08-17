"""Frozen causal contract-unavailability policy for CUP-50."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path

import pandas as pd


@dataclasses.dataclass(frozen=True, slots=True)
class UnavailabilityWindow:
    symbol: str
    start: pd.Timestamp
    end: pd.Timestamp
    reason: str
    settlement_price: float


def load_unavailability_audit(
    source: str | Path | Mapping[str, object] | None,
) -> tuple[UnavailabilityWindow, ...]:
    """Validate the pre-activation organizer audit and return half-open windows."""
    if source is None:
        return ()
    if isinstance(source, (str, Path)):
        payload = json.loads(Path(source).read_text())
    else:
        payload = dict(source)
    if (
        payload.get("schema_version") != 1
        or payload.get("namespace") != "cup50"
        or payload.get("policy_id") != "causal-no-replacement-unavailability-v1"
        or payload.get("freeze_phase") != "pre-activation-before-feedback"
    ):
        raise ValueError("invalid CUP-50 unavailability audit")
    windows: list[UnavailabilityWindow] = []
    for item in payload.get("windows", []):
        if not isinstance(item, Mapping):
            raise ValueError("unavailability audit window must be an object")
        start, end = pd.Timestamp(item["start"]), pd.Timestamp(item["end"])
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("unavailability windows must be UTC-aware")
        start, end = start.tz_convert("UTC"), end.tz_convert("UTC")
        canonical_start = start == start.floor("8h")
        canonical_end = end == end.floor("8h")
        symbol, reason = str(item.get("symbol", "")), str(item.get("reason", ""))
        if start >= end or not canonical_start or not canonical_end:
            raise ValueError("unavailability windows require ordered canonical 8h boundaries")
        if not symbol.endswith("USDT") or symbol != symbol.upper() or not reason:
            raise ValueError("unavailability windows require a symbol and reason")
        evidence = item.get("evidence")
        if not isinstance(evidence, Mapping):
            raise ValueError("unavailability windows require checksum evidence")
        def valid_digest(key: str) -> bool:
            digest = str(evidence.get(key, ""))
            return len(digest) == 64 and not any(
                character not in "0123456789abcdef" for character in digest
            )

        lower_interval_evidence = valid_digest("daily_1h_archive_sha256") and valid_digest(
            "daily_1m_archive_sha256"
        )
        canonical_evidence = valid_digest("monthly_8h_archive_sha256")
        if not lower_interval_evidence and not canonical_evidence:
            raise ValueError(
                "unavailability requires lower-interval or canonical archive SHA-256 evidence"
            )
        last_observation = pd.Timestamp(evidence.get("last_observation_close_time"))
        if last_observation.tzinfo is None:
            raise ValueError("last unavailability observation must be UTC-aware")
        last_observation = last_observation.tz_convert("UTC")
        last_close = float(evidence.get("last_observation_close", math.nan))
        if (
            last_observation >= start
            or last_observation.ceil("8h") != start
            or not math.isfinite(last_close)
            or last_close <= 0
        ):
            raise ValueError("unavailability evidence does not establish the first boundary")
        if end.weekday() != 0 or end != end.normalize():
            raise ValueError("unavailability must end at the next frozen Monday roster boundary")
        windows.append(
            UnavailabilityWindow(
                symbol=symbol,
                start=start,
                end=end,
                reason=reason,
                settlement_price=last_close,
            )
        )
    ordered = sorted(windows, key=lambda window: (window.symbol, window.start, window.end))
    if windows != ordered:
        raise ValueError("unavailability windows must be canonically sorted")
    for previous, current in zip(ordered, ordered[1:]):
        if previous.symbol == current.symbol and current.start < previous.end:
            raise ValueError("unavailability windows overlap")
    return tuple(windows)


def unavailable_symbols(
    windows: Sequence[UnavailabilityWindow], decision: pd.Timestamp
) -> frozenset[str]:
    timestamp = pd.Timestamp(decision)
    if timestamp.tzinfo is None:
        raise ValueError("availability decision must be UTC-aware")
    timestamp = timestamp.tz_convert("UTC")
    return frozenset(
        window.symbol for window in windows if window.start <= timestamp < window.end
    )


def audit_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
