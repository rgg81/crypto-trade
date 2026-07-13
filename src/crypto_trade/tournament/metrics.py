"""Canonical daily, risk, and regime metrics for tournament evaluator returns."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

from crypto_trade.tournament.top40 import REQUIRED_REGIMES, WindowMetrics

ANNUALIZATION_DAYS = 365
BOOTSTRAP_SAMPLES = 2_000
BOOTSTRAP_BLOCK_DAYS = 10
BOOTSTRAP_SEED = 20_260_713


def aggregate_daily_returns(bar_returns: pd.Series) -> pd.Series:
    """Compound bar returns into a gap-free UTC daily return series."""
    series = _return_series(bar_returns)
    if series.empty:
        return series
    daily = (1.0 + series).resample("1D").prod() - 1.0
    full_index = pd.date_range(daily.index.min(), daily.index.max(), freq="1D", tz="UTC")
    return daily.reindex(full_index, fill_value=0.0).rename("net_return")


def compute_window_metrics(daily_returns: pd.Series) -> WindowMetrics:
    """Compute the exact scalar metrics consumed by the submission schema."""
    returns = _return_series(daily_returns)
    if returns.empty:
        return WindowMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    sharpe = _annualized_sharpe(returns)
    downside = np.sqrt(np.mean(np.square(np.minimum(returns.to_numpy(), 0.0))))
    sortino = float(np.sqrt(ANNUALIZATION_DAYS) * returns.mean() / downside) if downside else 0.0
    total_growth = float((1.0 + returns).prod())
    annualized_return = (
        total_growth ** (ANNUALIZATION_DAYS / len(returns)) - 1.0 if total_growth > 0 else -1.0
    )
    equity = np.concatenate(([1.0], (1.0 + returns).cumprod().to_numpy()))
    running_peak = np.maximum.accumulate(equity)
    max_drawdown = float(-np.min(equity / running_peak - 1.0))
    calmar = float(annualized_return / max_drawdown) if max_drawdown > 1e-12 else 0.0
    quarterly = (1.0 + returns).resample("QE").prod() - 1.0
    positive_quarter_fraction = float((quarterly > 0.0).mean()) if len(quarterly) else 0.0
    return WindowMetrics(
        net_sharpe=sharpe,
        net_sortino=sortino,
        calmar=calmar,
        annualized_return=annualized_return,
        max_drawdown=max_drawdown,
        positive_quarter_fraction=positive_quarter_fraction,
    )


def classify_btc_regimes(btc_daily_returns: pd.Series) -> pd.Series:
    """Apply the charter's one-day-lagged, mutually exclusive BTC regime map."""
    returns = _return_series(btc_daily_returns)
    trailing_return = (1.0 + returns).rolling(60, min_periods=60).apply(np.prod, raw=True) - 1.0
    trailing_vol = returns.rolling(30, min_periods=30).std(ddof=1) * np.sqrt(ANNUALIZATION_DAYS)
    trailing_return = trailing_return.shift(1)
    trailing_vol = trailing_vol.shift(1)
    labels = pd.Series("chop", index=returns.index, dtype="object")
    labels.loc[trailing_return > 0.10] = "bull"
    labels.loc[trailing_return < -0.10] = "bear"
    labels.loc[trailing_vol > 0.80] = "stress"
    labels.loc[trailing_return.isna() | trailing_vol.isna()] = pd.NA
    return labels.rename("regime")


def compute_regime_sharpes(
    strategy_daily_returns: pd.Series, regime_labels: pd.Series
) -> Mapping[str, float]:
    """Compute annualized Sharpe in each fixed regime, returning zero for an empty bucket."""
    returns = _return_series(strategy_daily_returns)
    labels = regime_labels.copy()
    labels.index = pd.to_datetime(labels.index, utc=True)
    aligned = pd.concat([returns.rename("return"), labels.rename("regime")], axis=1).dropna()
    return {
        regime: _annualized_sharpe(aligned.loc[aligned["regime"] == regime, "return"])
        for regime in sorted(REQUIRED_REGIMES)
    }


def sharpe_confidence_interval(
    daily_returns: pd.Series,
    *,
    samples: int = BOOTSTRAP_SAMPLES,
    block_days: int = BOOTSTRAP_BLOCK_DAYS,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float]:
    """Return a deterministic 95% circular block-bootstrap Sharpe interval."""
    returns = _return_series(daily_returns)
    if len(returns) < 2:
        return (0.0, 0.0)
    if samples < 100 or block_days < 1:
        raise ValueError("bootstrap requires at least 100 samples and a positive block length")
    values = returns.to_numpy()
    blocks = int(np.ceil(len(values) / block_days))
    generator = np.random.default_rng(seed)
    starts = generator.integers(0, len(values), size=(samples, blocks))
    offsets = np.arange(block_days)
    indices = (starts[:, :, None] + offsets[None, None, :]) % len(values)
    resampled = values[indices.reshape(samples, -1)[:, : len(values)]]
    means = resampled.mean(axis=1)
    deviations = resampled.std(axis=1, ddof=1)
    sharpes = np.divide(
        np.sqrt(ANNUALIZATION_DAYS) * means,
        deviations,
        out=np.zeros_like(means),
        where=deviations > 1e-15,
    )
    lower, upper = np.quantile(sharpes, [0.025, 0.975])
    return (float(lower), float(upper))


def _annualized_sharpe(returns: pd.Series) -> float:
    if len(returns) < 2:
        return 0.0
    standard_deviation = float(returns.std(ddof=1))
    if standard_deviation <= 1e-15:
        return 0.0
    return float(np.sqrt(ANNUALIZATION_DAYS) * returns.mean() / standard_deviation)


def _return_series(values: pd.Series) -> pd.Series:
    series = pd.Series(values, dtype=float).copy()
    series.index = pd.to_datetime(series.index, utc=True)
    if not np.isfinite(series.to_numpy()).all():
        raise ValueError("return series contains NaN or infinite values")
    if (series <= -1.0).any():
        raise ValueError("return series contains a loss of 100% or worse")
    return series.sort_index()
