"""team-05 — illiquidity-conditioned short-horizon reversal (discovery baseline).

Direct expression of the mandate: fade the last bar's cross-sectional move, and size that
fade in proportion to how illiquid the name was *before* the move happened.

    weight_i  ~  (-reversal_rank_i) * illiquidity_percentile_i * (median_sigma / sigma_i)

Everything is a cross-sectional rank, so the book carries no price levels, no dates and no
symbol identities. There is no time-series volatility target: gross exposure is a constant
1.0 every bar and the organizer's common ex-ante risk unit sets book-level risk.

Deliberately omitted at this phase (declared in the thesis, evaluated later): the taker-flow
inventory proxy, the Corwin-Schultz illiquidity estimator, multi-bar formation and holding
windows, and the no-trade turnover band. See RATIONALE.md section "What this is not".
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

# --- Structural constants (lookback geometry and exposure limits, not fitted values) -------

FORMATION_BARS = 1          # 8h inventory-shock window
ILLIQ_LOOKBACK_BARS = 21    # ~7 days of 8h bars: an illiquidity *state*, still current
VOL_LOOKBACK_BARS = 21      # matched to the illiquidity window
HISTORY_FLOOR_BARS = 30     # declared universe floor: 30-bar median quote volume
VOLUME_FLOOR_QUANTILE = 0.20
INV_VOL_CLIP_LOW = 0.5      # bound the 1/sigma multiplier so one quiet name cannot dominate
INV_VOL_CLIP_HIGH = 2.0
MIN_UNIVERSE = 10           # below this a rank book is not a portfolio
TARGET_GROSS = 1.0
MAX_ABS_WEIGHT = 0.10
MAX_ABS_NET = 0.20          # internal guard, inside the 0.25 contract limit
DUST_WEIGHT = 1e-4          # positions below this are not executable, only turnover


def _column(frame: pd.DataFrame, name: str) -> np.ndarray | None:
    """Return ``name`` as a 1-D float array, or ``None`` if it is not usable."""
    if name not in frame.columns:
        return None
    values = np.asarray(frame[name], dtype="float64")
    if values.ndim != 1 or values.size == 0:
        return None
    return values


def _bar_log_returns(close: np.ndarray) -> np.ndarray:
    """Bar-over-bar log returns; non-positive or missing prices become NaN."""
    if close.size < 2:
        return np.empty(0, dtype="float64")
    prev = close[:-1]
    curr = close[1:]
    out = np.full(curr.shape, np.nan, dtype="float64")
    usable = np.isfinite(prev) & np.isfinite(curr) & (prev > 0.0) & (curr > 0.0)
    out[usable] = np.log(curr[usable] / prev[usable])
    return out


def _formation_return(close: np.ndarray, span: int) -> float:
    """Log return over the last ``span`` bars, anchored at the newest row."""
    if close.size < span + 1:
        return float("nan")
    start = close[-1 - span]
    end = close[-1]
    if not (np.isfinite(start) and np.isfinite(end) and start > 0.0 and end > 0.0):
        return float("nan")
    return float(np.log(end / start))


def _amihud_illiquidity(close: np.ndarray, quote_volume: np.ndarray, span: int) -> float:
    """Amihud: mean absolute log return per unit of quote volume over the last ``span`` bars."""
    returns = _bar_log_returns(close)
    if returns.size < span or quote_volume.size < returns.size + 1:
        return float("nan")
    window_returns = returns[-span:]
    window_volume = quote_volume[1:][-span:]
    usable = (
        np.isfinite(window_returns) & np.isfinite(window_volume) & (window_volume > 0.0)
    )
    if int(usable.sum()) < max(2, span // 2):
        return float("nan")
    return float(np.mean(np.abs(window_returns[usable]) / window_volume[usable]))


def _realized_vol(close: np.ndarray, span: int) -> float:
    """Trailing realized volatility of log returns; used only for cross-sectional balancing."""
    returns = _bar_log_returns(close)
    if returns.size < span:
        return float("nan")
    window = returns[-span:]
    window = window[np.isfinite(window)]
    if window.size < max(2, span // 2):
        return float("nan")
    sigma = float(np.std(window))
    return sigma if sigma > 0.0 else float("nan")


def _median_quote_volume(quote_volume: np.ndarray, span: int) -> float:
    """Rolling median quote volume: the declared tradeability floor."""
    if quote_volume.size < span:
        return float("nan")
    window = quote_volume[-span:]
    window = window[np.isfinite(window) & (window > 0.0)]
    if window.size < max(2, span // 2):
        return float("nan")
    return float(np.median(window))


def _percentile_rank(values: np.ndarray) -> np.ndarray:
    """Cross-sectional rank on (0, 1), ties averaged, endpoints never degenerate."""
    count = values.size
    if count < 2:
        return np.full(count, 0.5, dtype="float64")
    ranks = np.asarray(pd.Series(values).rank(method="average"), dtype="float64")
    return (ranks - 0.5) / float(count)


def _measure_symbol(frame: pd.DataFrame) -> tuple[float, float, float, float] | None:
    """Formation return, illiquidity, realized vol and volume floor for one symbol."""
    if frame is None or len(frame) < HISTORY_FLOOR_BARS:
        return None
    close = _column(frame, "close")
    quote_volume = _column(frame, "quote_volume")
    if close is None or quote_volume is None or close.size != quote_volume.size:
        return None

    formation = _formation_return(close, FORMATION_BARS)
    illiquidity = _amihud_illiquidity(close, quote_volume, ILLIQ_LOOKBACK_BARS)
    sigma = _realized_vol(close, VOL_LOOKBACK_BARS)
    volume_floor = _median_quote_volume(quote_volume, HISTORY_FLOOR_BARS)

    measures = (formation, illiquidity, sigma, volume_floor)
    if not all(np.isfinite(value) for value in measures):
        return None
    return measures


def _finalize(scores: np.ndarray) -> np.ndarray:
    """Turn signed scores into a dollar-neutral book at unit gross, inside every cap."""
    centered = scores - float(np.mean(scores))
    gross = float(np.sum(np.abs(centered)))
    if not np.isfinite(gross) or gross <= 0.0:
        return np.zeros(scores.size, dtype="float64")

    weights = np.clip(
        centered * (TARGET_GROSS / gross), -MAX_ABS_WEIGHT, MAX_ABS_WEIGHT
    )

    net = float(np.sum(weights))
    if abs(net) > MAX_ABS_NET:
        weights = np.clip(
            weights - net / float(weights.size), -MAX_ABS_WEIGHT, MAX_ABS_WEIGHT
        )

    gross = float(np.sum(np.abs(weights)))
    if gross > TARGET_GROSS:
        weights = weights * (TARGET_GROSS / gross)

    weights[np.abs(weights) < DUST_WEIGHT] = 0.0
    return weights


class IlliquidityConditionedReversal:
    """Stateless: every decision is recomputed from the past-only rows in ``context``."""

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        bars = context.bars
        eligible = context.eligible_symbols
        if bars is None or eligible is None or len(eligible) < MIN_UNIVERSE:
            return {}

        symbols: list[str] = []
        formation: list[float] = []
        illiquidity: list[float] = []
        sigma: list[float] = []
        volume_floor: list[float] = []

        for symbol in eligible:
            if symbol not in bars:
                continue
            measured = _measure_symbol(bars[symbol])
            if measured is None:
                continue
            symbols.append(symbol)
            formation.append(measured[0])
            illiquidity.append(measured[1])
            sigma.append(measured[2])
            volume_floor.append(measured[3])

        if len(symbols) < MIN_UNIVERSE:
            return {}

        volume_array = np.asarray(volume_floor, dtype="float64")
        keep = volume_array >= float(np.quantile(volume_array, VOLUME_FLOOR_QUANTILE))
        if int(keep.sum()) < MIN_UNIVERSE:
            return {}

        symbols = [symbol for symbol, alive in zip(symbols, keep) if alive]
        formation_array = np.asarray(formation, dtype="float64")[keep]
        illiquidity_array = np.asarray(illiquidity, dtype="float64")[keep]
        sigma_array = np.asarray(sigma, dtype="float64")[keep]

        # Reversal: fade the cross-sectional move. Ranking the raw formation return is
        # identical to ranking it after removing the cross-sectional mean, so the declared
        # demeaning is carried by the rank transform itself.
        reversal = 0.5 - _percentile_rank(formation_array)

        # The mandate, as one factor: reversal strength rises linearly in the illiquidity
        # percentile measured *before* the move. Continuous, so no threshold is being fit.
        illiquidity_tilt = _percentile_rank(illiquidity_array)

        # Cross-sectional risk balancing only. Gross stays at 1.0, so this is not a
        # volatility target -- it stops the most volatile names owning the book's risk.
        median_sigma = float(np.median(sigma_array))
        if not np.isfinite(median_sigma) or median_sigma <= 0.0:
            inverse_vol = np.ones(sigma_array.size, dtype="float64")
        else:
            inverse_vol = np.clip(
                median_sigma / sigma_array, INV_VOL_CLIP_LOW, INV_VOL_CLIP_HIGH
            )

        weights = _finalize(reversal * illiquidity_tilt * inverse_vol)

        book = {
            symbol: float(weight)
            for symbol, weight in zip(symbols, weights)
            if np.isfinite(weight) and weight != 0.0
        }
        if len(book) < MIN_UNIVERSE:
            return {}
        return book


def build_strategy() -> IlliquidityConditionedReversal:
    return IlliquidityConditionedReversal()
