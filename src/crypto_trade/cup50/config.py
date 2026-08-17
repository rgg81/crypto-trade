"""Frozen machine contract for the CUP-50 tournament.

The constants in this module are deliberately independent from every earlier tournament.  A
CUP-50 caller may reuse raw archive bytes, but it cannot silently inherit a split, universe rule,
qualification gate, or lane from CUP-20.
"""

from __future__ import annotations

import dataclasses
import hashlib
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd

SCHEMA_VERSION = 2
NAME = "cup50"

IS_START = pd.Timestamp("2021-03-15T00:00:00Z")
OOS_START = pd.Timestamp("2024-02-01T00:00:00Z")
OOS_END = pd.Timestamp("2026-08-01T00:00:00Z")

TEAM_IDS = tuple(f"team-{number:02d}" for number in range(1, 13))
LANES = (
    "slow-trend",
    "breakout-trend",
    "volume-confirmed-trend",
    "residual-cross-sectional-momentum",
    "liquidity-shock-reversal",
    "defensive-low-risk-selection",
    "funding-carry",
    "funding-crowding-reversal",
    "taker-flow-pressure",
    "relative-value-convergence",
    "calendar-settlement-seasonality",
    "preregistered-simple-regime-ensemble",
)
MANDATES = dict(zip(TEAM_IDS, LANES, strict=True))

FOLDS = (
    ("F1", pd.Timestamp("2024-02-01T00:00:00Z"), pd.Timestamp("2024-08-01T00:00:00Z")),
    ("F2", pd.Timestamp("2024-08-01T00:00:00Z"), pd.Timestamp("2025-02-01T00:00:00Z")),
    ("F3", pd.Timestamp("2025-02-01T00:00:00Z"), pd.Timestamp("2025-08-01T00:00:00Z")),
    ("F4", pd.Timestamp("2025-08-01T00:00:00Z"), pd.Timestamp("2026-02-01T00:00:00Z")),
    ("F5", pd.Timestamp("2026-02-01T00:00:00Z"), pd.Timestamp("2026-08-01T00:00:00Z")),
)

_TOP_LEVEL = frozenset(
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
        "scoring",
        "paper",
        "mandates",
    }
)

_FROZEN: dict[tuple[str, ...], object] = {
    ("schema_version",): SCHEMA_VERSION,
    ("name",): NAME,
    ("splits", "is_start"): IS_START.isoformat().replace("+00:00", "Z"),
    ("splits", "oos_start"): OOS_START.isoformat().replace("+00:00", "Z"),
    ("splits", "oos_end"): OOS_END.isoformat().replace("+00:00", "Z"),
    ("universe", "target_size"): 50,
    ("universe", "lookback_days"): 180,
    ("universe", "bars_per_complete_day"): 3,
    ("universe", "reconstitution_weekday"): 0,
    ("universe", "liquidity_measure"): "median-daily-usdt-quote-volume",
    ("universe", "hysteresis"): False,
    ("execution", "interval_hours"): 8,
    ("execution", "initial_equity"): 100_000.0,
    ("execution", "taker_fee_bps_per_side"): 5.0,
    ("execution", "slippage_bps_per_side"): 2.5,
    ("execution", "max_gross_exposure"): 1.0,
    ("execution", "max_abs_net_exposure"): 1.0,
    ("execution", "max_symbol_exposure"): 0.20,
    ("execution", "max_bar_participation"): 0.001,
    ("execution", "unavailability_policy"): "causal-no-replacement-last-close-v1",
    ("risk_unit", "target_annualized_volatility"): 0.10,
    ("risk_unit", "lookback_days"): 90,
    ("risk_unit", "minimum_scale"): 0.20,
    ("risk_unit", "maximum_scale"): 3.0,
    ("risk_unit", "team_volatility_targeting"): "forbidden",
    ("research", "official_trial_budget"): 12,
    ("research", "minimum_official_trials"): 0,
    ("research", "maximum_dimensions"): 10,
    ("research", "strategy_history_days"): 180,
    ("scoring", "return_weight"): 1.0,
    ("scoring", "drawdown_penalty"): 0.50,
    ("scoring", "underdeployment_penalty"): 0.10,
    ("scoring", "concentration_penalty"): 0.05,
    ("scoring", "generalization_weight"): 0.85,
    ("scoring", "all_window_weight"): 0.15,
    ("scoring", "rounding"): "decimal-half-even-1e-6",
    ("scoring", "qualification_gates"): "none",
    ("paper", "minimum_days"): 365,
    ("paper", "launch"): "first-canonical-8h-boundary-strictly-after-release",
    ("paper", "data_policy"): "public-only-append-invariant",
    ("data", "archive_reuse_policy"): "checksum-verified-raw-bytes-only",
    ("data", "acquisition_root"): "data/cup50/acquisition-remediated-20260817",
    ("data", "is_root"): "data/cup50/is",
    ("data", "team_is_root"): "data/cup50/team-is",
    ("data", "sealed_root"): "data/cup50/sealed",
    ("universe", "classification_policy"): "pure-crypto-fail-closed-v1",
    ("research", "controls"): "preregistered-permanently-non-promoteable",
}


@dataclasses.dataclass(frozen=True, slots=True)
class LoadedConfig:
    path: Path
    sha256: str
    raw: Mapping[str, Any]


def _lookup(raw: Mapping[str, Any], path: tuple[str, ...]) -> object:
    value: object = raw
    for component in path:
        if not isinstance(value, Mapping) or component not in value:
            raise ValueError(f"CUP-50 config is missing {'.'.join(path)}")
        value = value[component]
    return value


def validate_config(raw: Mapping[str, Any]) -> None:
    """Fail on any drift from the policy that observation will score under."""
    if set(raw) != _TOP_LEVEL:
        raise ValueError("CUP-50 config has missing or unexpected top-level tables")
    for path, expected in _FROZEN.items():
        if _lookup(raw, path) != expected:
            raise ValueError(f"CUP-50 config {'.'.join(path)} differs from the frozen contract")
    if tuple(raw["teams"]) != TEAM_IDS:
        raise ValueError("CUP-50 team roster must contain team-01 through team-12 in order")
    if dict(raw["mandates"]) != MANDATES:
        raise ValueError("CUP-50 mandates must match the twelve independent frozen lanes")
    if tuple(_lookup(raw, ("execution", "cost_multipliers"))) != (1, 2, 3):
        raise ValueError("CUP-50 cost multipliers are exactly 1x, 2x, and 3x")


def load_config(path: str | Path) -> LoadedConfig:
    config_path = Path(path)
    payload = config_path.read_bytes()
    raw = tomllib.loads(payload.decode("utf-8"))
    validate_config(raw)
    return LoadedConfig(config_path, hashlib.sha256(payload).hexdigest(), raw)
