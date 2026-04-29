"""v2 validation helpers — Deflated Sharpe Ratio and regime-stratified Sharpe.

iter-v2/001 implements:

- ``deflated_sharpe_ratio(...)`` — AFML Ch. 11 DSR with skew/kurt correction.
- ``regime_stratified_sharpe(...)`` — per-(Hurst bucket × ATR percentile bucket)
  OOS Sharpe breakdown, writes a ``per_regime_v2.csv``.

Deferred (raised stubs) for iter-v2/002-003:

- ``probability_of_backtest_overfitting(...)`` — PBO from CPCV paths
- ``estimate_embargo_size(...)`` — ACF-based embargo sizing

References:
- López de Prado, *Advances in Financial Machine Learning*, Ch. 11-12
- ``~/.claude/skills/walk-forward-validation/scripts/overfit_detector.py``
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm

# Euler-Mascheroni constant — shows up in the expected-max-Sharpe approximation
_EULER_MASCHERONI = 0.5772156649


def deflated_sharpe_ratio(
    observed_sr: float,
    num_trials: int,
    backtest_length: int,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
) -> dict[str, float]:
    """Deflated Sharpe Ratio after multiple-testing correction (AFML Ch. 11).

    Returns a dict with:

    - ``dsr`` — z-score of observed SR vs expected max under null
    - ``p_value`` — probability the true SR exceeds zero given the trial count
    - ``expected_max_sr`` — expected best Sharpe under the null (N random trials)
    - ``sr_std_err`` — standard error of the observed Sharpe

    Parameters
    ----------
    observed_sr
        Annualized Sharpe ratio of the SELECTED strategy.
    num_trials
        Total strategies tested across the track (v2 iteration count for v2's DSR).
    backtest_length
        Number of return observations (e.g., OOS trade count or OOS daily bars).
    skewness
        Skewness of the return series.
    kurtosis
        Raw kurtosis of the return series (3 for normal; pass the observed value).
    """
    if num_trials <= 0:
        raise ValueError("num_trials must be positive")
    if backtest_length <= 1:
        raise ValueError("backtest_length must be > 1")

    # Standard error of the Sharpe ratio, adjusted for skew and kurt
    variance_num = 1.0 - skewness * observed_sr + (kurtosis - 1.0) / 4.0 * observed_sr**2
    variance_num = max(variance_num, 1e-12)
    sr_std = math.sqrt(variance_num / (backtest_length - 1))

    # Expected max Sharpe under the null across num_trials random strategies
    ln_n = math.log(num_trials)
    if num_trials == 1 or ln_n <= 0:
        expected_max_sr = 0.0
    else:
        expected_max_sr = (
            (1.0 - _EULER_MASCHERONI) * norm.ppf(1.0 - 1.0 / num_trials)
            + _EULER_MASCHERONI * norm.ppf(1.0 - 1.0 / (num_trials * math.e))
        )

    dsr_z = (observed_sr - expected_max_sr) / sr_std if sr_std > 0 else 0.0
    p_value = float(norm.cdf(dsr_z))

    return {
        "dsr": float(dsr_z),
        "p_value": p_value,
        "expected_max_sr": float(expected_max_sr),
        "sr_std_err": float(sr_std),
    }


def regime_stratified_sharpe(
    trades: pd.DataFrame,
    features_lookup: dict[str, pd.DataFrame],
    hurst_col: str = "hurst_100",
    atr_pct_col: str = "atr_pct_rank_200",
    hurst_edges: tuple[float, ...] = (0.0, 0.4, 0.6, 1.5),
    atr_pct_edges: tuple[float, ...] = (0.0, 0.33, 0.66, 1.01),
) -> pd.DataFrame:
    """Break OOS Sharpe down by (Hurst bucket × ATR percentile bucket).

    Parameters
    ----------
    trades
        DataFrame with at minimum ``symbol``, ``open_time`` (epoch ms),
        ``weighted_pnl`` (signed, fee-adjusted) columns.
    features_lookup
        ``{symbol: pd.DataFrame}`` with ``open_time``, the Hurst and ATR
        percentile columns. Used to assign each trade to a regime bucket.
    hurst_col
        Feature column for the Hurst regime axis.
    atr_pct_col
        Feature column for the ATR percentile axis.
    hurst_edges
        Bucket edges for Hurst. Defaults to mean-reverting (<0.4) /
        neutral (0.4-0.6) / trending (>=0.6).
    atr_pct_edges
        Bucket edges for ATR percentile rank. Defaults to low/medium/high vol.

    Returns
    -------
    pd.DataFrame with columns:
        hurst_bucket, atr_bucket, n_trades, mean_pnl, std_pnl, sharpe
    """
    if len(trades) == 0:
        return pd.DataFrame(
            columns=["hurst_bucket", "atr_bucket", "n_trades", "mean_pnl", "std_pnl", "sharpe"]
        )

    # Per-trade regime lookup — binary search on each symbol's features frame
    hurst_vals: list[float] = []
    atr_vals: list[float] = []
    for _, row in trades.iterrows():
        sym = row["symbol"]
        ot = int(row["open_time"])
        feat = features_lookup.get(sym)
        if feat is None or len(feat) == 0:
            hurst_vals.append(np.nan)
            atr_vals.append(np.nan)
            continue
        times = feat["open_time"].to_numpy()
        idx = int(np.searchsorted(times, ot))
        if idx >= len(times) or int(times[idx]) != ot:
            hurst_vals.append(np.nan)
            atr_vals.append(np.nan)
            continue
        hurst_vals.append(float(feat[hurst_col].iat[idx]))
        atr_vals.append(float(feat[atr_pct_col].iat[idx]))

    df = trades.copy()
    df["_hurst"] = hurst_vals
    df["_atr_pct"] = atr_vals

    def _bucket(x: float, edges: tuple[float, ...]) -> str:
        if not np.isfinite(x):
            return "NA"
        for i in range(len(edges) - 1):
            if edges[i] <= x < edges[i + 1]:
                return f"[{edges[i]:.2f},{edges[i + 1]:.2f})"
        return "NA"

    df["hurst_bucket"] = df["_hurst"].apply(lambda x: _bucket(x, hurst_edges))
    df["atr_bucket"] = df["_atr_pct"].apply(lambda x: _bucket(x, atr_pct_edges))

    grouped = df.groupby(["hurst_bucket", "atr_bucket"], as_index=False).agg(
        n_trades=("weighted_pnl", "count"),
        mean_pnl=("weighted_pnl", "mean"),
        std_pnl=("weighted_pnl", "std"),
    )
    grouped["sharpe"] = np.where(
        (grouped["std_pnl"] > 0) & (grouped["n_trades"] > 1),
        grouped["mean_pnl"] / grouped["std_pnl"] * np.sqrt(grouped["n_trades"]),
        np.nan,
    )
    return grouped.sort_values(["hurst_bucket", "atr_bucket"]).reset_index(drop=True)


def probability_of_backtest_overfitting(cpcv_path_sharpes: Any) -> float:
    """PBO from a matrix of CPCV path Sharpes. iter-v2/003 implements."""
    raise NotImplementedError(
        "iter-v2/003 implements PBO; scaffold stub (requires CPCV from iter-v2/002)"
    )


def estimate_embargo_size(features: Any, significance: float = 0.05) -> int:
    """Recommend embargo size from feature autocorrelation decay.

    iter-v2/003 implements this. Scaffold stub raises.
    """
    raise NotImplementedError(
        "iter-v2/003 implements ACF-based embargo sizing; scaffold stub"
    )


__all__ = [
    "deflated_sharpe_ratio",
    "regime_stratified_sharpe",
    "probability_of_backtest_overfitting",
    "estimate_embargo_size",
]
