"""Prospective pandas-3 UTC slicing compatibility for the V3 research extension."""

from __future__ import annotations

import contextlib
import dataclasses
from collections.abc import Iterator, Mapping
from typing import Any

import pandas as pd

from crypto_trade.tournament import runner_v3
from crypto_trade.tournament.metrics_v3 import (
    classify_btc_regimes,
    compute_regime_sharpes,
    compute_window_metrics,
    sharpe_confidence_interval,
)


def _utc(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def compute_metrics_utc_compatible(
    base_daily: pd.Series,
    stressed_daily: pd.Series,
    btc_daily: pd.Series,
    config: Mapping[str, Any],
    authorized: runner_v3.AuthorizedWindow,
) -> dict[str, Any]:
    """Apply the frozen metric formulas after normalizing both slice bounds to UTC."""

    start = _utc(authorized.score_start)
    end = _utc(authorized.score_end_inclusive)
    scored = base_daily.loc[(base_daily.index >= start) & (base_daily.index <= end)]
    stressed_scored = stressed_daily.loc[
        (stressed_daily.index >= start) & (stressed_daily.index <= end)
    ]
    classified = classify_btc_regimes(btc_daily)
    labels = classified.loc[(classified.index >= start) & (classified.index <= end)]
    if not labels.index.equals(scored.index) or labels.notna().sum() == 0:
        raise ValueError(f"BTC regime labels do not cover the exact {authorized.stage} grid")
    statistics = config["statistics"]
    interval_kwargs = {
        "samples": int(statistics["bootstrap_samples"]),
        "block_days": int(statistics["bootstrap_block_days"]),
        "seed": int(statistics["bootstrap_seed"]),
    }
    scored_metrics = compute_window_metrics(scored)
    return {
        "scored_window": runner_v3.EvaluationWindow(
            authorized.score_start,
            authorized.score_end_inclusive,
            runner_v3.WindowMetrics(**dataclasses.asdict(scored_metrics)),
        ),
        "double_cost_sharpe": compute_window_metrics(stressed_scored).net_sharpe,
        "regime_sharpe": dict(compute_regime_sharpes(scored, labels)),
        "net_sharpe_confidence_interval": sharpe_confidence_interval(
            scored, **interval_kwargs
        ),
        "double_cost_sharpe_confidence_interval": sharpe_confidence_interval(
            stressed_scored, **interval_kwargs
        ),
    }


@contextlib.contextmanager
def utc_metric_slice_compatibility() -> Iterator[None]:
    """Install the reviewed compatibility only for one serial organizer invocation."""

    original = runner_v3._compute_metrics
    if original is compute_metrics_utc_compatible:
        raise RuntimeError("UTC metric compatibility is already active")
    runner_v3._compute_metrics = compute_metrics_utc_compatible
    try:
        yield
    finally:
        runner_v3._compute_metrics = original


__all__ = ["compute_metrics_utc_compatible", "utc_metric_slice_compatibility"]
