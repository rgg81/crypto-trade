"""Frozen machine contract for the CUP-50 v2 tournament.

The constants here are deliberately independent from every earlier tournament.  A CUP-50 v2 caller
may reuse raw archive bytes, but it cannot silently inherit a split, universe rule, qualification
gate, or lane from an earlier edition.

Structure lives in this module: the windows, the folds, the lane roster, and the identifiers that
name which rule is in force.  Every *tunable number* lives in ``config.toml`` and reaches the
scorer, the evaluator, the risk unit, the neighbourhood and the trial ledger through
:class:`Policy`.  CUP-50 restated its caps, costs and score weights in three places at once, so
changing one meant editing two or three files and hoping they agreed; here a number appears
exactly once, and the bytes that carry it are bound by the activation record and re-checked by
every trial.
"""

from __future__ import annotations

import dataclasses
import functools
import hashlib
import math
import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from crypto_trade.cup50v2.regimes import REGIMES, RegimePolicy

SCHEMA_VERSION = 2
NAME = "cup50v2"

IS_START = pd.Timestamp("2021-03-15T00:00:00Z")
OOS_START = pd.Timestamp("2024-02-01T00:00:00Z")
OOS_END = pd.Timestamp("2026-08-01T00:00:00Z")

TEAM_IDS = tuple(f"team-{number:02d}" for number in range(1, 13))
LANES = (
    "multi-horizon-trend",
    "channel-position-breakout",
    "residual-cross-sectional-momentum",
    "regime-allocated-ensemble",
    "funding-carry-crowding-guarded",
    "defensive-quality-neutral",
    "taker-flow-pressure",
    "volume-shock-event-reversal",
    "cluster-relative-reversal",
    "attention-flow",
    "walk-forward-learned-model",
    "breadth-market-state-timing",
)
MANDATES = dict(zip(TEAM_IDS, LANES, strict=True))

FOLDS = (
    ("F1", pd.Timestamp("2024-02-01T00:00:00Z"), pd.Timestamp("2024-08-01T00:00:00Z")),
    ("F2", pd.Timestamp("2024-08-01T00:00:00Z"), pd.Timestamp("2025-02-01T00:00:00Z")),
    ("F3", pd.Timestamp("2025-02-01T00:00:00Z"), pd.Timestamp("2025-08-01T00:00:00Z")),
    ("F4", pd.Timestamp("2025-08-01T00:00:00Z"), pd.Timestamp("2026-02-01T00:00:00Z")),
    ("F5", pd.Timestamp("2026-02-01T00:00:00Z"), pd.Timestamp("2026-08-01T00:00:00Z")),
)

# The same machinery scores the in-sample window, so a team sees the shape it will be judged on and
# the qualification bar can be stated in the same units as the result.
IS_FOLDS = (
    ("I1", IS_START, pd.Timestamp("2021-08-01T00:00:00Z")),
    ("I2", pd.Timestamp("2021-08-01T00:00:00Z"), pd.Timestamp("2022-02-01T00:00:00Z")),
    ("I3", pd.Timestamp("2022-02-01T00:00:00Z"), pd.Timestamp("2022-08-01T00:00:00Z")),
    ("I4", pd.Timestamp("2022-08-01T00:00:00Z"), pd.Timestamp("2023-02-01T00:00:00Z")),
    ("I5", pd.Timestamp("2023-02-01T00:00:00Z"), pd.Timestamp("2023-08-01T00:00:00Z")),
    ("I6", pd.Timestamp("2023-08-01T00:00:00Z"), OOS_START),
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
        "qualification",
        "regimes",
        "paper",
        "mandates",
    }
)

_FROZEN: dict[tuple[str, ...], object] = {
    # Structure only. Every tunable number is read from the config through ``Policy`` rather than
    # restated here, so this table cannot drift from what the evaluator actually applies.
    ("schema_version",): SCHEMA_VERSION,
    ("name",): NAME,
    ("splits", "is_start"): IS_START.isoformat().replace("+00:00", "Z"),
    ("splits", "oos_start"): OOS_START.isoformat().replace("+00:00", "Z"),
    ("splits", "oos_end"): OOS_END.isoformat().replace("+00:00", "Z"),
    ("universe", "liquidity_measure"): "median-daily-usdt-quote-volume",
    ("universe", "hysteresis"): False,
    ("universe", "classification_policy"): "pure-crypto-fail-closed-v1",
    ("execution", "unavailability_policy"): "causal-no-replacement-last-close-v1",
    ("risk_unit", "team_volatility_targeting"): "forbidden",
    ("research", "controls"): "preregistered-permanently-non-promoteable",
    ("scoring", "rounding"): "decimal-half-even-1e-6",
    ("scoring", "qualification_gates"): "in-sample-bar-v1",
    ("paper", "launch"): "first-canonical-8h-boundary-strictly-after-release",
    ("paper", "data_policy"): "public-only-append-invariant",
    ("data", "archive_reuse_policy"): "checksum-verified-raw-bytes-only",
    ("data", "acquisition_root"): "data/cup50v2/acquisition",
    ("data", "is_root"): "data/cup50v2/is",
    ("data", "team_is_root"): "data/cup50v2/team-is",
    ("data", "sealed_root"): "data/cup50v2/sealed",
}

DEFAULT_CONFIG_PATH = Path("tournament/cup50v2/config.toml")


@dataclasses.dataclass(frozen=True, slots=True)
class UniversePolicy:
    target_size: int
    lookback_days: int
    bars_per_complete_day: int
    reconstitution_weekday: int
    hysteresis: bool


@dataclasses.dataclass(frozen=True, slots=True)
class ExecutionPolicy:
    interval_hours: int
    initial_equity: float
    taker_fee_bps_per_side: float
    slippage_bps_per_side: float
    cost_multipliers: tuple[int, ...]
    max_gross_exposure: float
    max_abs_net_exposure: float
    max_symbol_exposure: float
    max_bar_participation: float


@dataclasses.dataclass(frozen=True, slots=True)
class RiskUnitPolicy:
    target_annualized_volatility: float
    covariance_halflife_bars: int
    covariance_window_bars: int
    minimum_symbol_bars: int
    minimum_scale: float
    maximum_scale: float


@dataclasses.dataclass(frozen=True, slots=True)
class ResearchPolicy:
    official_trial_budget: int
    minimum_official_trials: int
    maximum_dimensions: int
    strategy_history_days: int
    neighbourhood_scale_step: float
    neighbourhood_logit_step: float
    neighbourhood_signed_step: float


@dataclasses.dataclass(frozen=True, slots=True)
class ScoringPolicy:
    drawdown_penalty: float
    underdeployment_penalty: float
    concentration_penalty: float
    volatility_reference: float
    activity_reference: float
    activity_exposure_floor: float
    minimum_activity: float
    concentration_threshold: float
    concentration_top_days: int
    squash_scale: float
    cost_weights: Mapping[int, float]
    fold_weights: tuple[float, ...]
    is_fold_weights: tuple[float, ...]
    generalization_weight: float
    regime_weight: float
    all_window_weight: float
    neighbourhood_weights: tuple[float, ...]
    lower_quartile_fraction: int
    rounding_places: int


@dataclasses.dataclass(frozen=True, slots=True)
class QualificationPolicy:
    minimum_is_score: float
    minimum_is_regime_score: float


@dataclasses.dataclass(frozen=True, slots=True)
class PaperPolicy:
    minimum_days: int


@dataclasses.dataclass(frozen=True, slots=True)
class Policy:
    """Every tunable the tournament applies, read from one hash-bound file."""

    universe: UniversePolicy
    execution: ExecutionPolicy
    risk_unit: RiskUnitPolicy
    research: ResearchPolicy
    scoring: ScoringPolicy
    qualification: QualificationPolicy
    regimes: RegimePolicy
    paper: PaperPolicy


@dataclasses.dataclass(frozen=True, slots=True)
class LoadedConfig:
    path: Path
    sha256: str
    raw: Mapping[str, Any]
    policy: Policy


def _lookup(raw: Mapping[str, Any], path: tuple[str, ...]) -> object:
    value: object = raw
    for component in path:
        if not isinstance(value, Mapping) or component not in value:
            raise ValueError(f"CUP-50 v2 config is missing {'.'.join(path)}")
        value = value[component]
    return value


def _number(
    raw: Mapping[str, Any],
    path: tuple[str, ...],
    *,
    minimum: float,
    maximum: float,
    integral: bool = False,
) -> float:
    value = _lookup(raw, path)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"CUP-50 v2 config {'.'.join(path)} must be a number")
    if integral and not isinstance(value, int):
        raise ValueError(f"CUP-50 v2 config {'.'.join(path)} must be an integer")
    number = float(value)
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise ValueError(f"CUP-50 v2 config {'.'.join(path)} is outside its permitted range")
    return number


def _weights(raw: Mapping[str, Any], path: tuple[str, ...], *, count: int) -> tuple[float, ...]:
    value = _lookup(raw, path)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) != count:
        raise ValueError(f"CUP-50 v2 config {'.'.join(path)} needs exactly {count} weights")
    weights = tuple(float(item) for item in value)
    if any(not math.isfinite(weight) or weight < 0.0 for weight in weights):
        raise ValueError(f"CUP-50 v2 config {'.'.join(path)} weights must be finite and positive")
    if abs(sum(weights) - 1.0) > 1e-12:
        raise ValueError(f"CUP-50 v2 config {'.'.join(path)} weights must sum to one")
    return weights


def build_policy(raw: Mapping[str, Any]) -> Policy:
    """Project the validated config onto the tunables the tournament code consumes."""
    multipliers = tuple(int(value) for value in _lookup(raw, ("execution", "cost_multipliers")))
    cost_weights = _weights(raw, ("scoring", "cost_weights"), count=len(multipliers))
    universe = UniversePolicy(
        target_size=int(
            _number(raw, ("universe", "target_size"), minimum=1, maximum=500, integral=True)
        ),
        lookback_days=int(
            _number(raw, ("universe", "lookback_days"), minimum=1, maximum=1_000, integral=True)
        ),
        bars_per_complete_day=int(
            _number(
                raw, ("universe", "bars_per_complete_day"), minimum=1, maximum=24, integral=True
            )
        ),
        reconstitution_weekday=int(
            _number(
                raw, ("universe", "reconstitution_weekday"), minimum=0, maximum=6, integral=True
            )
        ),
        hysteresis=bool(_lookup(raw, ("universe", "hysteresis"))),
    )
    execution = ExecutionPolicy(
        interval_hours=int(
            _number(raw, ("execution", "interval_hours"), minimum=1, maximum=24, integral=True)
        ),
        initial_equity=_number(raw, ("execution", "initial_equity"), minimum=1.0, maximum=1e12),
        taker_fee_bps_per_side=_number(
            raw, ("execution", "taker_fee_bps_per_side"), minimum=0.0, maximum=1_000.0
        ),
        slippage_bps_per_side=_number(
            raw, ("execution", "slippage_bps_per_side"), minimum=0.0, maximum=1_000.0
        ),
        cost_multipliers=multipliers,
        max_gross_exposure=_number(
            raw, ("execution", "max_gross_exposure"), minimum=1e-6, maximum=100.0
        ),
        max_abs_net_exposure=_number(
            raw, ("execution", "max_abs_net_exposure"), minimum=1e-6, maximum=100.0
        ),
        max_symbol_exposure=_number(
            raw, ("execution", "max_symbol_exposure"), minimum=1e-6, maximum=100.0
        ),
        max_bar_participation=_number(
            raw, ("execution", "max_bar_participation"), minimum=1e-9, maximum=1.0
        ),
    )
    risk_unit = RiskUnitPolicy(
        target_annualized_volatility=_number(
            raw, ("risk_unit", "target_annualized_volatility"), minimum=1e-6, maximum=10.0
        ),
        covariance_halflife_bars=int(
            _number(
                raw,
                ("risk_unit", "covariance_halflife_bars"),
                minimum=1,
                maximum=10_000,
                integral=True,
            )
        ),
        covariance_window_bars=int(
            _number(
                raw,
                ("risk_unit", "covariance_window_bars"),
                minimum=2,
                maximum=10_000,
                integral=True,
            )
        ),
        minimum_symbol_bars=int(
            _number(
                raw, ("risk_unit", "minimum_symbol_bars"), minimum=2, maximum=10_000, integral=True
            )
        ),
        minimum_scale=_number(raw, ("risk_unit", "minimum_scale"), minimum=1e-6, maximum=100.0),
        maximum_scale=_number(raw, ("risk_unit", "maximum_scale"), minimum=1e-6, maximum=100.0),
    )
    if risk_unit.minimum_scale > risk_unit.maximum_scale:
        raise ValueError("CUP-50 v2 risk scalar minimum exceeds its maximum")
    research = ResearchPolicy(
        official_trial_budget=int(
            _number(
                raw, ("research", "official_trial_budget"), minimum=1, maximum=1_000, integral=True
            )
        ),
        minimum_official_trials=int(
            _number(
                raw,
                ("research", "minimum_official_trials"),
                minimum=0,
                maximum=1_000,
                integral=True,
            )
        ),
        maximum_dimensions=int(
            _number(raw, ("research", "maximum_dimensions"), minimum=1, maximum=50, integral=True)
        ),
        strategy_history_days=int(
            _number(
                raw, ("research", "strategy_history_days"), minimum=1, maximum=3_650, integral=True
            )
        ),
        neighbourhood_scale_step=_number(
            raw, ("research", "neighbourhood_scale_step"), minimum=1.0 + 1e-9, maximum=10.0
        ),
        neighbourhood_logit_step=_number(
            raw, ("research", "neighbourhood_logit_step"), minimum=1.0 + 1e-9, maximum=10.0
        ),
        neighbourhood_signed_step=_number(
            raw, ("research", "neighbourhood_signed_step"), minimum=1e-9, maximum=10.0
        ),
    )
    if research.minimum_official_trials > research.official_trial_budget:
        raise ValueError("CUP-50 v2 nomination minimum exceeds the trial budget")
    scoring = ScoringPolicy(
        drawdown_penalty=_number(raw, ("scoring", "drawdown_penalty"), minimum=0.0, maximum=100.0),
        underdeployment_penalty=_number(
            raw, ("scoring", "underdeployment_penalty"), minimum=0.0, maximum=100.0
        ),
        concentration_penalty=_number(
            raw, ("scoring", "concentration_penalty"), minimum=0.0, maximum=100.0
        ),
        volatility_reference=_number(
            raw, ("scoring", "volatility_reference"), minimum=1e-6, maximum=10.0
        ),
        activity_reference=_number(
            raw, ("scoring", "activity_reference"), minimum=1e-6, maximum=1.0
        ),
        activity_exposure_floor=_number(
            raw, ("scoring", "activity_exposure_floor"), minimum=0.0, maximum=1.0
        ),
        minimum_activity=_number(raw, ("scoring", "minimum_activity"), minimum=0.0, maximum=1.0),
        concentration_threshold=_number(
            raw, ("scoring", "concentration_threshold"), minimum=0.0, maximum=1.0
        ),
        concentration_top_days=int(
            _number(
                raw, ("scoring", "concentration_top_days"), minimum=1, maximum=365, integral=True
            )
        ),
        squash_scale=_number(raw, ("scoring", "squash_scale"), minimum=1e-6, maximum=100.0),
        cost_weights=dict(zip(multipliers, cost_weights, strict=True)),
        fold_weights=_weights(raw, ("scoring", "fold_weights"), count=len(FOLDS)),
        is_fold_weights=_weights(raw, ("scoring", "is_fold_weights"), count=len(IS_FOLDS)),
        generalization_weight=_number(
            raw, ("scoring", "generalization_weight"), minimum=0.0, maximum=1.0
        ),
        regime_weight=_number(raw, ("scoring", "regime_weight"), minimum=0.0, maximum=1.0),
        all_window_weight=_number(raw, ("scoring", "all_window_weight"), minimum=0.0, maximum=1.0),
        neighbourhood_weights=_weights(raw, ("scoring", "neighbourhood_weights"), count=3),
        lower_quartile_fraction=int(
            _number(
                raw, ("scoring", "lower_quartile_fraction"), minimum=1, maximum=100, integral=True
            )
        ),
        rounding_places=int(
            _number(raw, ("scoring", "rounding_places"), minimum=1, maximum=12, integral=True)
        ),
    )
    if (
        abs(scoring.generalization_weight + scoring.regime_weight + scoring.all_window_weight - 1.0)
        > 1e-12
    ):
        raise ValueError("CUP-50 v2 point weights must sum to one")
    qualification = QualificationPolicy(
        minimum_is_score=_number(
            raw, ("qualification", "minimum_is_score"), minimum=0.0, maximum=100.0
        ),
        minimum_is_regime_score=_number(
            raw, ("qualification", "minimum_is_regime_score"), minimum=0.0, maximum=100.0
        ),
    )
    regimes = RegimePolicy(
        bull_threshold=_number(raw, ("regimes", "bull_threshold"), minimum=0.0, maximum=10.0),
        bear_threshold=_number(raw, ("regimes", "bear_threshold"), minimum=-10.0, maximum=0.0),
        minimum_days=int(
            _number(raw, ("regimes", "minimum_days"), minimum=1, maximum=10_000, integral=True)
        ),
        weights=_weights(raw, ("regimes", "weights"), count=len(REGIMES)),
    )
    paper = PaperPolicy(
        minimum_days=int(
            _number(raw, ("paper", "minimum_days"), minimum=1, maximum=10_000, integral=True)
        ),
    )
    return Policy(
        universe=universe,
        execution=execution,
        risk_unit=risk_unit,
        research=research,
        scoring=scoring,
        qualification=qualification,
        regimes=regimes,
        paper=paper,
    )


def validate_config(raw: Mapping[str, Any]) -> Policy:
    """Fail on any drift from the policy that observation will score under."""
    if set(raw) != _TOP_LEVEL:
        raise ValueError("CUP-50 v2 config has missing or unexpected top-level tables")
    for path, expected in _FROZEN.items():
        if _lookup(raw, path) != expected:
            raise ValueError(f"CUP-50 v2 config {'.'.join(path)} differs from the frozen contract")
    if tuple(raw["teams"]) != TEAM_IDS:
        raise ValueError("CUP-50 v2 team roster must contain team-01 through team-12 in order")
    if dict(raw["mandates"]) != MANDATES:
        raise ValueError("CUP-50 v2 mandates must match the twelve independent frozen lanes")
    policy = build_policy(raw)
    if policy.execution.cost_multipliers != (1, 2, 3):
        raise ValueError("CUP-50 v2 cost multipliers are exactly 1x, 2x, and 3x")
    return policy


def load_config(path: str | Path) -> LoadedConfig:
    config_path = Path(path)
    payload = config_path.read_bytes()
    raw = tomllib.loads(payload.decode("utf-8"))
    policy = validate_config(raw)
    return LoadedConfig(config_path, hashlib.sha256(payload).hexdigest(), raw, policy)


@functools.cache
def _cached_config(resolved: str, digest: str) -> LoadedConfig:
    return load_config(resolved)


def active_config(path: str | Path | None = None) -> LoadedConfig:
    """Load the canonical config, re-reading whenever its bytes change.

    Callers that never mention a config get the repository's canonical file.  The sandboxed
    evaluator mounts its own copy and passes the path explicitly, so nothing depends on a working
    directory that only exists outside the container.
    """
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    payload = config_path.read_bytes()
    return _cached_config(str(config_path), hashlib.sha256(payload).hexdigest())


def active_policy(path: str | Path | None = None) -> Policy:
    return active_config(path).policy
