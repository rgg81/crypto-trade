"""v2 validation helpers — iter-v2/001 implements DSR and regime-stratified reports.

Phased delivery:

- iter-v2/001: Deflated Sharpe Ratio (DSR) + regime-stratified OOS Sharpe
- iter-v2/002: Combinatorial Purged CV (CPCV) splitter
- iter-v2/003: Probability of Backtest Overfitting (PBO) + ACF-based embargo sizing

References:
- López de Prado, Advances in Financial Machine Learning, Ch. 11-12
- ``~/.claude/skills/walk-forward-validation/references/overfit_detection.md``
- ``~/.claude/skills/walk-forward-validation/scripts/overfit_detector.py``
"""

from __future__ import annotations

from typing import Any


def deflated_sharpe_ratio(
    observed_sr: float,
    num_trials: int,
    backtest_length: int,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
) -> float:
    """Probability-style Deflated Sharpe Ratio after multiple-testing correction.

    Inputs as in AFML Ch. 11. ``num_trials`` is the v2 iteration count (NOT v1's
    cumulative count — v2 multiple-testing is scoped to its own track).

    iter-v2/001 implements this. Scaffold stub raises.
    """
    raise NotImplementedError(
        "iter-v2/001 implements DSR; scaffold stub (see overfit_detector.py reference)"
    )


def regime_stratified_sharpe(
    trades: Any,
    features: Any,
    hurst_col: str = "hurst_100",
    atr_pct_col: str = "atr_pct_rank_200",
    n_buckets: int = 3,
) -> Any:
    """Compute OOS Sharpe per (Hurst bucket × ATR percentile bucket).

    Used to surface regime dependence of the strategy. A strategy whose Sharpe
    collapses outside one regime quadrant is a warning sign for live deployment.

    iter-v2/001 implements this. Scaffold stub raises.
    """
    raise NotImplementedError(
        "iter-v2/001 implements regime-stratified Sharpe; scaffold stub"
    )


def probability_of_backtest_overfitting(
    cpcv_path_sharpes: Any,
) -> float:
    """PBO from a matrix of CPCV path Sharpes. iter-v2/003 implements."""
    raise NotImplementedError(
        "iter-v2/003 implements PBO; scaffold stub"
    )


def estimate_embargo_size(
    features: Any,
    significance: float = 0.05,
) -> int:
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
