"""Canonical V4 diagnostics, qualification gates, and ranking vectors."""

from __future__ import annotations

import dataclasses
import hashlib
import io
import os
import stat
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from crypto_trade.tournament import metrics_v3, runner_v4


class ScoringError(ValueError):
    """A runner artifact or proposed V4 score packet is not canonical."""


def _stable_artifact_bytes(path: Path, *, maximum: int = 256 * 1024 * 1024) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
                raise ScoringError("runner artifact is not a bounded regular file")
            payload = handle.read(maximum + 1)
            after = os.fstat(handle.fileno())
        path_after = path.lstat()
    except OSError as exc:
        raise ScoringError("runner artifact cannot be read stably") from exc
    before_identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    after_identity = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    path_identity = (
        path_after.st_dev,
        path_after.st_ino,
        path_after.st_size,
        path_after.st_mtime_ns,
    )
    if (
        len(payload) > maximum
        or before_identity != after_identity
        or after_identity != path_identity
        or stat.S_ISLNK(path_after.st_mode)
    ):
        raise ScoringError("runner artifact changed while being read")
    return payload


def _artifact(root: Path, result: runner_v4.TeamWindowRunResult, name: str) -> bytes:
    relative = result.artifacts.get(name)
    expected = result.artifact_sha256.get(name)
    if not isinstance(relative, str) or not isinstance(expected, str):
        raise ScoringError(f"runner result lacks the {name} artifact authority")
    raw_path = root / relative
    path = raw_path.resolve()
    current = root
    unsafe_component = False
    try:
        parts = raw_path.relative_to(root).parts
    except ValueError:
        parts = ()
        unsafe_component = True
    for part in parts:
        current = current / part
        if os.path.lexists(current) and current.is_symlink():
            unsafe_component = True
            break
    if unsafe_component or not path.is_relative_to(root) or not path.is_file():
        raise ScoringError(f"runner {name} artifact is missing or unsafe")
    payload = _stable_artifact_bytes(path)
    expected_size = result.artifact_sizes.get(name)
    if (
        isinstance(expected_size, bool)
        or not isinstance(expected_size, int)
        or len(payload) != expected_size
        or hashlib.sha256(payload).hexdigest() != expected
    ):
        raise ScoringError(f"runner {name} artifact changed after evaluation")
    return payload


def _daily(payload: bytes) -> pd.Series:
    frame = pd.read_csv(io.BytesIO(payload))
    if list(frame.columns) != ["date", "net_return"]:
        raise ScoringError("daily return artifact schema changed")
    index = pd.DatetimeIndex(pd.to_datetime(frame["date"], utc=True, errors="coerce"))
    values = pd.to_numeric(frame["net_return"], errors="coerce")
    if (
        index.hasnans
        or index.duplicated().any()
        or not index.is_monotonic_increasing
        or values.isna().any()
        or not np.isfinite(values.to_numpy(dtype=float)).all()
    ):
        raise ScoringError("daily return artifact is noncanonical")
    return pd.Series(values.to_numpy(dtype=float), index=index, name="net_return")


def _metrics(values: pd.Series) -> dict[str, float]:
    result = metrics_v3.compute_window_metrics(values)
    return {field.name: float(getattr(result, field.name)) for field in dataclasses.fields(result)}


def _cumulative_return(values: pd.Series) -> float:
    return float((1.0 + values).prod() - 1.0)


def _probability_positive_mean(
    values: pd.Series, *, samples: int, block_days: int, seed: int
) -> float:
    """Deterministic circular block-bootstrap probability that arithmetic mean is positive."""

    array = values.to_numpy(dtype=float)
    if len(array) < 2:
        return 0.0
    if samples < 100 or block_days < 1:
        raise ScoringError("bootstrap requires at least 100 samples and positive block_days")
    blocks = int(np.ceil(len(array) / block_days))
    generator = np.random.default_rng(seed)
    starts = generator.integers(0, len(array), size=(samples, blocks))
    offsets = np.arange(block_days)
    indices = (starts[:, :, None] + offsets[None, None, :]) % len(array)
    resampled = array[indices.reshape(samples, -1)[:, : len(array)]]
    return float((resampled.mean(axis=1) > 0.0).mean())


def trial_adjusted_confidence(probability: float, trial_count: int) -> float:
    if not 0.0 <= probability <= 1.0 or trial_count < 1:
        raise ScoringError("invalid trial-adjustment inputs")
    return float(max(0.0, min(1.0, 1.0 - trial_count * (1.0 - probability))))


def _folds(
    base: pd.Series,
    double: pd.Series,
    folds: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for fold in folds:
        start = pd.Timestamp(str(fold["start"]))
        end = pd.Timestamp(str(fold["end_exclusive"]))
        base_fold = base.loc[(base.index >= start) & (base.index < end)]
        double_fold = double.loc[(double.index >= start) & (double.index < end)]
        if base_fold.empty or not base_fold.index.equals(double_fold.index):
            raise ScoringError(f"fold {fold.get('name')} is incomplete")
        rows.append(
            {
                "name": str(fold["name"]),
                "start": str(fold["start"]),
                "end_exclusive": str(fold["end_exclusive"]),
                "base_cumulative_return": _cumulative_return(base_fold),
                "base_arithmetic_pnl": float(base_fold.sum()),
                "base_metrics": _metrics(base_fold),
                "double_cost_cumulative_return": _cumulative_return(double_fold),
                "double_cost_metrics": _metrics(double_fold),
            }
        )
    return rows


def _return_concentration(
    base: pd.Series, folds: Sequence[Mapping[str, Any]]
) -> tuple[float, float]:
    absolute = base.abs().sort_values(ascending=False)
    total_absolute = float(absolute.sum())
    top_five_share = float(absolute.iloc[:5].sum() / total_absolute) if total_absolute else 1.0
    positive_fold_pnl = [max(0.0, float(row["base_arithmetic_pnl"])) for row in folds]
    total_positive = float(sum(positive_fold_pnl))
    fold_share = max(positive_fold_pnl) / total_positive if total_positive else 1.0
    return top_five_share, float(fold_share)


def _bar_diagnostics(
    payload: bytes, *, start: pd.Timestamp, end: pd.Timestamp
) -> dict[str, float | int | None]:
    frame = pd.read_csv(io.BytesIO(payload))
    required = {
        "timestamp",
        "price_pnl",
        "funding_pnl",
        "fees",
        "slippage",
        "turnover",
        "gross_exposure",
        "long_price_pnl",
        "short_price_pnl",
        "long_funding_pnl",
        "short_funding_pnl",
    }
    if not required.issubset(frame.columns):
        raise ScoringError("bar return artifact lacks required V4 diagnostics")
    timestamps = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    bars = frame.loc[(timestamps >= start) & (timestamps < end)].copy()
    if bars.empty:
        raise ScoringError("bar return artifact does not cover the scored window")
    numeric_columns = sorted(required - {"timestamp"})
    numeric = bars.loc[:, numeric_columns].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any() or not np.isfinite(numeric.to_numpy()).all():
        raise ScoringError("bar return diagnostics contain nonfinite values")
    years = (end - start).total_seconds() / (365.0 * 24.0 * 3600.0)
    turnover = float(numeric["turnover"].sum())
    gross_pnl = float((numeric["price_pnl"] + numeric["funding_pnl"]).sum())
    costs = float((numeric["fees"] + numeric["slippage"]).sum())
    return {
        "annualized_turnover": float(turnover / years),
        "average_gross_exposure": float(numeric["gross_exposure"].mean()),
        "base_cost": costs,
        "base_cost_share_of_positive_gross_pnl": costs / gross_pnl if gross_pnl > 0.0 else None,
        "gross_edge_per_turnover_bps": gross_pnl / turnover * 10_000.0 if turnover > 0.0 else None,
        "gross_pnl": gross_pnl,
        "long_gross_pnl": float((numeric["long_price_pnl"] + numeric["long_funding_pnl"]).sum()),
        "short_gross_pnl": float((numeric["short_price_pnl"] + numeric["short_funding_pnl"]).sum()),
        "total_one_way_turnover": turnover,
    }


def summarize_run(
    root: str | Path,
    result: runner_v4.TeamWindowRunResult,
    config: Mapping[str, Any],
    *,
    trial_count: int,
) -> dict[str, Any]:
    """Build a complete deterministic IS or historical-OOS score packet."""

    root_path = Path(root).resolve()
    split = config["splits"][result.stage]
    start = pd.Timestamp(str(split["start"]))
    end = pd.Timestamp(str(split["end_exclusive"]))
    base = _daily(_artifact(root_path, result, "daily_returns"))
    double = _daily(_artifact(root_path, result, "double_cost_daily_returns"))
    triple = _daily(_artifact(root_path, result, "triple_cost_daily_returns"))
    for label, values in (("base", base), ("double", double), ("triple", triple)):
        selected = values.loc[(values.index >= start) & (values.index < end)]
        if selected.empty:
            raise ScoringError(f"{label} daily returns do not cover the scored window")
        if label == "base":
            base = selected
        elif label == "double":
            double = selected
        else:
            triple = selected
    if not base.index.equals(double.index) or not base.index.equals(triple.index):
        raise ScoringError("cost scenarios do not share one exact daily grid")

    bar_diagnostics = _bar_diagnostics(
        _artifact(root_path, result, "evaluator_returns"), start=start, end=end
    )
    base_metrics = _metrics(base)
    double_metrics = _metrics(double)
    triple_metrics = _metrics(triple)
    statistics = config["statistics"]
    bootstrap_probability = _probability_positive_mean(
        base,
        samples=int(statistics["bootstrap_samples"]),
        block_days=int(statistics["bootstrap_block_days"]),
        seed=int(statistics["bootstrap_seed"]),
    )
    packet: dict[str, Any] = {
        "schema_version": "top40-v4-r1-run-summary-v1",
        "stage": result.stage,
        "team_id": result.team_id,
        "candidate_identity": {
            "config_sha256": result.config_sha256,
            "data_manifest_sha256": result.data_manifest_sha256,
            "dependency_lock_sha256": result.dependency_lock_sha256,
            "entrypoint": result.entrypoint,
            "evaluator_sha256": result.evaluator_sha256,
            "risk_policy_sha256": result.risk_policy_sha256,
            "source_bundle_sha256": result.source_bundle_sha256,
            "strategy_sha256": result.strategy_sha256,
        },
        "scored_window": {
            "start": str(split["start"]),
            "end_exclusive": str(split["end_exclusive"]),
            "base_cumulative_return": _cumulative_return(base),
            "base_metrics": base_metrics,
            "double_cost_cumulative_return": _cumulative_return(double),
            "double_cost_metrics": double_metrics,
            "triple_cost_cumulative_return": _cumulative_return(triple),
            "triple_cost_metrics": triple_metrics,
        },
        "diagnostics": bar_diagnostics,
        "regime_sharpe": {key: float(value) for key, value in result.regime_sharpe.items()},
        "bootstrap_probability_positive_mean": bootstrap_probability,
        "trial_count_at_summary": int(trial_count),
        "trial_adjusted_confidence": trial_adjusted_confidence(bootstrap_probability, trial_count),
        "runner": result.organizer_fields(),
    }
    if result.stage == "is":
        folds = _folds(base, double, config["selection"]["folds"])
        top_five_share, fold_share = _return_concentration(base, folds)
        packet["folds"] = folds
        packet["diagnostics"].update(
            {
                "top_five_day_absolute_return_share": top_five_share,
                "maximum_fold_positive_pnl_share": fold_share,
            }
        )
        packet["selection"] = assess_is(packet, config, trial_count=trial_count)
    elif result.stage == "historical_oos":
        packet["championship"] = assess_historical_oos(packet, config)
    else:
        raise ScoringError("V4 summary stage must be is or historical_oos")
    return packet


def assess_is(
    packet: Mapping[str, Any],
    config: Mapping[str, Any],
    *,
    trial_count: int,
    neighborhood_passed: bool = False,
) -> dict[str, Any]:
    floors = config["selection"]["floors"]
    window = packet["scored_window"]
    base = window["base_metrics"]
    double = window["double_cost_metrics"]
    triple = window["triple_cost_metrics"]
    diagnostics = packet["diagnostics"]
    folds = packet["folds"]
    regimes = packet["regime_sharpe"]
    double_fold_sharpes = [float(row["double_cost_metrics"]["net_sharpe"]) for row in folds]
    adjusted = trial_adjusted_confidence(
        float(packet["bootstrap_probability_positive_mean"]), trial_count
    )
    edge = diagnostics["gross_edge_per_turnover_bps"]
    cost_share = diagnostics["base_cost_share_of_positive_gross_pnl"]
    gates = {
        "net_sharpe": float(base["net_sharpe"]) >= float(floors["minimum_net_sharpe_inclusive"]),
        "annualized_return": float(base["annualized_return"])
        >= float(floors["minimum_annualized_return_inclusive"]),
        "max_drawdown": float(base["max_drawdown"]) <= float(floors["maximum_drawdown_inclusive"]),
        "double_cost_sharpe": float(double["net_sharpe"])
        >= float(floors["minimum_double_cost_sharpe_inclusive"]),
        "triple_cost_sharpe": float(triple["net_sharpe"])
        > float(floors["minimum_triple_cost_sharpe_exclusive"]),
        "positive_quarters": float(base["positive_quarter_fraction"])
        >= float(floors["minimum_positive_quarter_fraction_inclusive"]),
        "positive_base_folds": sum(float(row["base_cumulative_return"]) > 0.0 for row in folds)
        >= int(floors["minimum_positive_base_folds"]),
        "positive_double_cost_folds": sum(
            float(row["double_cost_cumulative_return"]) > 0.0 for row in folds
        )
        >= int(floors["minimum_positive_double_cost_folds"]),
        "worst_fold_sharpe": min(double_fold_sharpes)
        >= float(floors["minimum_worst_fold_sharpe_inclusive"]),
        "annualized_turnover": float(diagnostics["annualized_turnover"])
        <= float(floors["maximum_annualized_turnover_inclusive"]),
        "gross_edge_density": edge is not None
        and float(edge) >= float(floors["minimum_gross_edge_per_turnover_bps_inclusive"]),
        "base_cost_share": cost_share is not None
        and float(cost_share) <= float(floors["maximum_base_cost_share_inclusive"]),
        "trial_adjusted_confidence": adjusted
        >= float(floors["minimum_trial_adjusted_confidence_inclusive"]),
        "bull_sharpe": float(regimes["bull"]) > float(floors["minimum_bull_sharpe_exclusive"]),
        "bear_sharpe": float(regimes["bear"]) > float(floors["minimum_bear_sharpe_exclusive"]),
        "chop_sharpe": float(regimes["chop"]) > float(floors["minimum_chop_sharpe_exclusive"]),
        "stress_sharpe": float(regimes["stress"])
        >= float(floors["minimum_stress_sharpe_inclusive"]),
        "long_gross_pnl": float(diagnostics["long_gross_pnl"])
        > float(floors["minimum_long_gross_pnl_exclusive"]),
        "short_gross_pnl": float(diagnostics["short_gross_pnl"])
        > float(floors["minimum_short_gross_pnl_exclusive"]),
        "top_five_day_concentration": float(diagnostics["top_five_day_absolute_return_share"])
        <= float(floors["maximum_top_five_day_absolute_return_share_inclusive"]),
        "fold_pnl_concentration": float(diagnostics["maximum_fold_positive_pnl_share"])
        <= float(floors["maximum_fold_positive_pnl_share_inclusive"]),
        "neighborhood_stability": bool(neighborhood_passed),
    }
    return {
        "eligible": all(gates.values()),
        "gates": gates,
        "trial_adjusted_confidence": adjusted,
        "ranking_vector": {
            "worst_fold_double_cost_sharpe": min(double_fold_sharpes),
            "median_fold_double_cost_sharpe": float(np.median(double_fold_sharpes)),
            "trial_adjusted_confidence": adjusted,
            "gross_edge_per_turnover_bps": edge,
            "annualized_turnover": float(diagnostics["annualized_turnover"]),
            "team_id": str(packet["team_id"]),
        },
    }


def is_ranking_key(selection: Mapping[str, Any]) -> tuple[Any, ...]:
    vector = selection["ranking_vector"]
    return (
        -float(vector["worst_fold_double_cost_sharpe"]),
        -float(vector["median_fold_double_cost_sharpe"]),
        -float(vector["trial_adjusted_confidence"]),
        -float(vector["gross_edge_per_turnover_bps"]),
        float(vector["annualized_turnover"]),
        str(vector["team_id"]),
    )


def assess_historical_oos(packet: Mapping[str, Any], config: Mapping[str, Any]) -> dict[str, Any]:
    policy = config["historical_oos"]
    floors = policy["winner_eligibility"]
    window = packet["scored_window"]
    base = window["base_metrics"]
    double = window["double_cost_metrics"]
    diagnostics = packet["diagnostics"]
    quarters = int(round(float(base["positive_quarter_fraction"]) * 8.0))
    gates = {
        "positive_base_return": float(base["annualized_return"])
        > float(floors["minimum_base_annualized_return_exclusive"]),
        "positive_double_cost_return": float(double["annualized_return"])
        > float(floors["minimum_double_cost_annualized_return_exclusive"]),
        "positive_double_cost_sharpe": float(double["net_sharpe"])
        > float(floors["minimum_double_cost_sharpe_exclusive"]),
        "max_drawdown": float(base["max_drawdown"]) <= float(floors["maximum_drawdown_inclusive"]),
        "positive_quarters": quarters >= int(floors["minimum_positive_quarters"]),
    }
    return {
        "winner_eligible": all(gates.values()),
        "gates": gates,
        "positive_quarters": quarters,
        "ranking_vector": {
            "double_cost_sharpe": float(double["net_sharpe"]),
            "base_annualized_return": float(base["annualized_return"]),
            "max_drawdown": float(base["max_drawdown"]),
            "gross_edge_per_turnover_bps": diagnostics["gross_edge_per_turnover_bps"],
            "annualized_turnover": float(diagnostics["annualized_turnover"]),
            "team_id": str(packet["team_id"]),
        },
    }


def historical_ranking_key(championship: Mapping[str, Any]) -> tuple[Any, ...]:
    vector = championship["ranking_vector"]
    edge = vector["gross_edge_per_turnover_bps"]
    return (
        -float(vector["double_cost_sharpe"]),
        -float(vector["base_annualized_return"]),
        float(vector["max_drawdown"]),
        -float(edge) if edge is not None else float("inf"),
        float(vector["annualized_turnover"]),
        str(vector["team_id"]),
    )


__all__ = [
    "ScoringError",
    "assess_historical_oos",
    "assess_is",
    "historical_ranking_key",
    "is_ranking_key",
    "summarize_run",
    "trial_adjusted_confidence",
]
