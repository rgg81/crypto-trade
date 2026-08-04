"""Fail-closed machine contract for the CUP-20 tournament."""

from __future__ import annotations

import dataclasses
import hashlib
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd

IS_END = pd.Timestamp("2024-08-01T00:00:00Z")
SEALED_START = pd.Timestamp("2024-08-01T00:00:00Z")
SEALED_END = pd.Timestamp("2026-08-01T00:00:00Z")

TEAM_IDS = tuple(f"team-{index:02d}" for index in range(1, 13))

_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "name",
        "policy_status",
        "charter_path",
        "teams",
        "paths",
        "data",
        "splits",
        "universe",
        "execution",
        "risk_unit",
        "research",
        "statistics",
        "floors",
        "selection",
        "holdout",
        "mandates",
    }
)

_FROZEN_SCALARS: dict[tuple[str, ...], object] = {
    ("schema_version",): 1,
    ("name",): "cup20",
    ("splits", "is_end"): "2024-08-01T00:00:00Z",
    ("splits", "sealed_start"): "2024-08-01T00:00:00Z",
    ("splits", "sealed_end"): "2026-08-01T00:00:00Z",
    ("universe", "target_size"): 20,
    ("universe", "entry_rank"): 20,
    ("universe", "exit_rank"): 25,
    ("universe", "lookback_days"): 180,
    ("execution", "interval_hours"): 8,
    ("execution", "taker_fee_bps_per_side"): 5.0,
    ("execution", "slippage_bps_per_side"): 2.5,
    ("execution", "max_gross_exposure"): 1.0,
    ("execution", "max_symbol_exposure"): 0.20,
    ("risk_unit", "target_annualized_volatility"): 0.10,
    ("risk_unit", "lookback_days"): 90,
    ("risk_unit", "minimum_scale"): 0.20,
    ("risk_unit", "maximum_scale"): 3.0,
    ("research", "trial_budget"): 12,
    ("research", "minimum_trials_for_nomination"): 8,
    ("statistics", "minimum_trial_adjusted_confidence"): 0.90,
    ("floors", "max_drawdown"): 0.20,
    ("floors", "minimum_realized_volatility"): 0.06,
    ("selection", "advancing_slots"): 3,
    ("holdout", "max_drawdown"): 0.25,
}


@dataclasses.dataclass(frozen=True, slots=True)
class LoadedConfig:
    """Canonical config bytes and parsed policy."""

    path: Path
    sha256: str
    raw: Mapping[str, Any]


def _lookup(raw: Mapping[str, Any], path: tuple[str, ...]) -> object:
    current: object = raw
    for component in path:
        if not isinstance(current, Mapping):
            raise ValueError(f"CUP-20 config {'.'.join(path)} is not a table")
        current = current.get(component)
    return current


def validate_config(raw: Mapping[str, Any]) -> None:
    """Reject any semantic drift in the activated CUP-20 policy."""
    if set(raw) != _TOP_LEVEL_KEYS:
        raise ValueError("CUP-20 config has missing or unexpected top-level tables")
    for path, expected in _FROZEN_SCALARS.items():
        if _lookup(raw, path) != expected:
            raise ValueError(f"CUP-20 config {'.'.join(path)} differs from the frozen contract")
    if tuple(raw["teams"]) != TEAM_IDS:
        raise ValueError("CUP-20 config team roster differs from the frozen contract")
    if tuple(sorted(raw["mandates"])) != TEAM_IDS:
        raise ValueError("CUP-20 config mandates must cover exactly the twelve teams")
    if len(set(raw["mandates"].values())) != len(TEAM_IDS):
        raise ValueError("CUP-20 mandates must be distinct mechanism lanes")
    cost_multipliers = _lookup(raw, ("execution", "cost_multipliers"))
    if not isinstance(cost_multipliers, list | tuple) or tuple(cost_multipliers) != (1, 2, 3):
        raise ValueError("CUP-20 cost multipliers are frozen at 1, 2 and 3")


def load_config(path: str | Path) -> LoadedConfig:
    """Read, hash and validate the frozen machine contract."""
    config_path = Path(path)
    payload = config_path.read_bytes()
    raw = tomllib.loads(payload.decode("utf-8"))
    validate_config(raw)
    return LoadedConfig(
        path=config_path,
        sha256=hashlib.sha256(payload).hexdigest(),
        raw=raw,
    )
