"""team-04 — residual cross-sectional momentum (discovery candidate).

Direct expression of the mandate: rank the cross-section on the part of each contract's recent
return that the equal-weighted market factor does not explain, then hold a long-short book that is
both dollar-neutral and neutral to the same estimated betas that produced the residuals.

This is the pre-registered *primary configuration* of `lane/scouting/THESIS.md` §4.1 and nothing
else: beta window 90d, shrinkage lambda = 0.5, momentum lookback 7d, hold 3d, vol-scaled signal.
No knob has been moved after seeing a result, because no result has been seen.

Construction notes that matter for reading the code:

* Horizons are declared in **days** and converted to bars from the observed bar spacing. The thesis
  assumes 8h funding-aligned bars (90d = 270 bars, 7d = 21, 3d = 9); deriving the spacing rather
  than hard-coding it means the book still expresses the declared horizons if the runner streams a
  different frequency, instead of silently trading a 3-day lookback labelled as 7.
* The 3-day hold is implemented **statelessly**, as a Jegadeesh-Titman overlapping portfolio: the
  rank score is averaged over the H formation windows ending at t, t-1, ... t-H+1. That is the same
  book as rebalancing a third of the capital every day, and it carries no state across decisions.
* Beta neutrality is a projection of the score onto the orthogonal complement of {1, beta_hat}, so
  `sum(w) == 0` and `sum(w * beta_hat) == 0` hold simultaneously by construction.

Every number below is a construction constant or a declared parameter, never a fitted one; nothing
is keyed to a date, a symbol, or a price level.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# --- Declared parameter surface, primary configuration (THESIS.md §4.1) ------------------------
BETA_WINDOW_DAYS = 90.0       # W = 270 bars at 8h
LOOKBACK_DAYS = 7.0           # L = 21 bars at 8h
HOLD_DAYS = 3.0               # H = 9 bars at 8h
BETA_SHRINK = 0.5             # lambda: beta_hat = (1 - lambda) * beta_ols + lambda * 1.0
VOL_SCALED_SIGNAL = True      # s = residual-vol-scaled

# --- Fixed by fiat (THESIS.md §4.2) ------------------------------------------------------------
LIQUIDITY_DAYS = 30.0         # trailing median quote volume horizon for the universe screen
UNIVERSE_SIZE = 150           # top-N liquid contracts
BETA_WINSOR_LOW = -1.0        # winsorise beta_ols before shrinking, per Sila et al. (2025)
BETA_WINSOR_HIGH = 3.0

# --- Engine-facing construction constants ------------------------------------------------------
MIN_SYMBOLS = 12              # below this a cross-sectional book is not a portfolio
MIN_BETA_BARS = 45            # hard floor on a usable beta window
TARGET_GROSS = 0.98           # shape only; the organizer owns the ex-ante risk unit
MAX_WEIGHT = 0.095            # engine cap is 0.10
MAX_NET = 0.20                # engine cap is 0.25
WEIGHT_FLOOR = 1e-6           # drop dust rather than pay to trade it
DEFAULT_BARS_PER_DAY = 3.0    # fallback when the bar index is not a timestamp index
MIN_BARS_PER_DAY = 0.25
MAX_BARS_PER_DAY = 96.0


def _bars_per_day(index) -> float:
    """Observed bars per day, from the median spacing of the most recent bars."""
    if not isinstance(index, pd.DatetimeIndex) or len(index) < 4:
        return DEFAULT_BARS_PER_DAY
    deltas = pd.Series(index[-64:]).diff().dropna().dt.total_seconds()
    deltas = deltas[deltas > 0.0]
    if deltas.empty:
        return DEFAULT_BARS_PER_DAY
    step = float(deltas.median())
    if not np.isfinite(step) or step <= 0.0:
        return DEFAULT_BARS_PER_DAY
    return float(min(max(86400.0 / step, MIN_BARS_PER_DAY), MAX_BARS_PER_DAY))


def _bars(days: float, per_day: float, floor: int) -> int:
    """Convert a declared horizon in days into a bar count."""
    return max(floor, int(round(days * per_day)))


def _liquidity(frame: pd.DataFrame, n_bars: int) -> float:
    """Trailing median quote volume; the only place volume enters (THESIS.md §4.3)."""
    columns = frame.columns
    if "quote_volume" in columns:
        notional = pd.to_numeric(frame["quote_volume"], errors="coerce")
    elif "volume" in columns and "close" in columns:
        notional = pd.to_numeric(frame["volume"], errors="coerce") * pd.to_numeric(
            frame["close"], errors="coerce"
        )
    else:
        return float("nan")
    tail = notional.tail(n_bars).dropna()
    if tail.empty:
        return float("nan")
    value = float(tail.median())
    return value if np.isfinite(value) else float("nan")


def _close_panel(frames, symbols, reference, n_rows: int):
    """Right-aligned close panel over the last ``n_rows`` bars of the reference grid.

    On a timestamp index the panel is aligned on the timestamps themselves, so a symbol with a gap
    contributes a NaN rather than a silently shifted price. Without a timestamp index the only safe
    assumption is that every eligible symbol's last row is the same period, so alignment is
    positional from the end.
    """
    columns = {}
    if isinstance(reference, pd.DatetimeIndex):
        target = reference[-n_rows:]
        for symbol in symbols:
            series = pd.to_numeric(frames[symbol]["close"], errors="coerce")
            if not isinstance(series.index, pd.DatetimeIndex):
                continue
            series = series[~series.index.duplicated(keep="last")]
            try:
                aligned = series.reindex(target)
            except (TypeError, ValueError):
                # e.g. a tz-aware symbol against a tz-naive grid: drop the symbol, keep the book.
                continue
            columns[symbol] = aligned.to_numpy(dtype="float64")
    else:
        for symbol in symbols:
            series = pd.to_numeric(frames[symbol]["close"], errors="coerce")
            values = series.to_numpy(dtype="float64")
            if values.size >= n_rows:
                columns[symbol] = values[-n_rows:]
    if not columns:
        return None, []
    names = list(columns)
    panel = np.column_stack([columns[name] for name in names])
    return panel, names


def _log_returns(panel: np.ndarray):
    """Log returns from a close panel; non-positive prices become NaN rather than -inf."""
    prices = np.where(panel > 0.0, panel, np.nan)
    return np.log(prices[1:, :]) - np.log(prices[:-1, :])


def _rank_score(values: np.ndarray):
    """Cross-sectional rank z-score. Symbols without a signal score neutral (zero)."""
    series = pd.Series(values, dtype="float64")
    valid = series.notna().to_numpy()
    count = int(valid.sum())
    if count < MIN_SYMBOLS:
        return None
    ranks = series[valid].rank(method="average").to_numpy(dtype="float64")
    centred = (ranks - (count + 1.0) / 2.0) / (count / 2.0)
    centred = centred - centred.mean()
    spread = float(centred.std(ddof=0))
    if not np.isfinite(spread) or spread <= 0.0:
        return None
    scores = np.zeros(series.size, dtype="float64")
    scores[valid] = centred / spread
    return scores


class ResidualCrossSectionalMomentum:
    """Rank on market-orthogonalised return; hold dollar- and beta-neutral."""

    def target_weights(self, context, *, seed):
        bars = context.bars
        eligible = []
        for symbol in context.eligible_symbols:
            if symbol not in bars:
                continue
            frame = bars[symbol]
            if not isinstance(frame, pd.DataFrame) or "close" not in frame.columns:
                continue
            if len(frame.index) < MIN_BETA_BARS + 2:
                continue
            eligible.append(symbol)
        if len(eligible) < MIN_SYMBOLS:
            return None

        frames = {symbol: bars[symbol] for symbol in eligible}
        reference = max((frames[s].index for s in eligible), key=len)
        if isinstance(reference, pd.DatetimeIndex):
            reference = reference[~reference.duplicated(keep="last")]

        per_day = _bars_per_day(reference)
        beta_bars_wanted = _bars(BETA_WINDOW_DAYS, per_day, MIN_BETA_BARS)
        lookback = _bars(LOOKBACK_DAYS, per_day, 3)
        hold = _bars(HOLD_DAYS, per_day, 1)
        liquidity_bars = _bars(LIQUIDITY_DAYS, per_day, 5)

        universe = self._screen(frames, eligible, liquidity_bars)

        signal_bars = lookback + hold - 1
        min_returns = max(signal_bars, MIN_BETA_BARS)
        available = len(reference)

        # Preferred window first; a shorter one only if too few contracts have a clean full
        # history. This is a data-availability fallback, not a searched knob.
        wanted = [
            min(beta_bars_wanted + signal_bars + 1, available),
            min(min_returns + 1, available),
        ]
        returns = None
        names: list = []
        for n_rows in dict.fromkeys(wanted):
            if n_rows < min_returns + 1:
                continue
            panel, panel_names = _close_panel(frames, universe, reference, n_rows)
            if panel is None:
                continue
            candidate = _log_returns(panel)
            complete = np.isfinite(candidate).all(axis=0)
            if int(complete.sum()) < MIN_SYMBOLS:
                continue
            returns = candidate[:, complete]
            names = [name for name, keep in zip(panel_names, complete) if keep]
            break
        if returns is None or returns.shape[0] < min_returns:
            return None

        market = returns.mean(axis=1)
        beta = self._beta(returns, market, min(beta_bars_wanted, returns.shape[0]))
        if beta is None:
            return None

        residual = returns[-signal_bars:, :] - np.outer(market[-signal_bars:], beta)
        score = self._score(residual, lookback, hold)
        if score is None:
            return None

        weights = self._neutralise(score, beta)
        if weights is None:
            return None
        return {
            name: float(weight)
            for name, weight in zip(names, weights)
            if np.isfinite(weight) and abs(float(weight)) >= WEIGHT_FLOOR
        }

    def _screen(self, frames, eligible, liquidity_bars):
        """Top-N by trailing median quote volume, in the order the venue offered them."""
        ranked = []
        for position, symbol in enumerate(eligible):
            notional = _liquidity(frames[symbol], liquidity_bars)
            if np.isfinite(notional) and notional > 0.0:
                ranked.append((-notional, position, symbol))
        if len(ranked) < MIN_SYMBOLS:
            return list(eligible)
        ranked.sort()
        return [symbol for _, _, symbol in ranked[:UNIVERSE_SIZE]]

    def _beta(self, returns, market, window):
        """Winsorised OLS beta on the equal-weighted market factor, shrunk toward 1.0."""
        if window < MIN_BETA_BARS:
            return None
        panel = returns[-window:, :]
        factor = market[-window:]
        factor_centred = factor - factor.mean()
        variance = float(factor_centred @ factor_centred)
        if not np.isfinite(variance) or variance <= 0.0:
            return None
        panel_centred = panel - panel.mean(axis=0, keepdims=True)
        ols = (factor_centred @ panel_centred) / variance
        ols = np.clip(np.nan_to_num(ols, nan=1.0), BETA_WINSOR_LOW, BETA_WINSOR_HIGH)
        return (1.0 - BETA_SHRINK) * ols + BETA_SHRINK

    def _score(self, residual, lookback, hold):
        """Rank score averaged over the H overlapping formation windows — the stateless hold."""
        end = residual.shape[0]
        total = np.zeros(residual.shape[1], dtype="float64")
        used = 0
        for offset in range(hold):
            stop = end - offset
            start = stop - lookback
            if start < 0:
                break
            window = residual[start:stop, :]
            cumulative = window.sum(axis=0)
            if VOL_SCALED_SIGNAL:
                spread = window.std(axis=0, ddof=1)
                positive = spread > 0.0
                cumulative = np.where(
                    positive, cumulative / np.where(positive, spread, 1.0), np.nan
                )
            ranked = _rank_score(cumulative)
            if ranked is None:
                continue
            total += ranked
            used += 1
        if used == 0:
            return None
        return total / used

    def _neutralise(self, score, beta):
        """Project off {1, beta_hat}, then size to the target gross and the engine's caps."""
        centred = score - score.mean()
        beta_centred = beta - beta.mean()
        dispersion = float(beta_centred @ beta_centred)
        if dispersion > 1e-12:
            centred = centred - (float(centred @ beta_centred) / dispersion) * beta_centred
        centred = centred - centred.mean()

        gross = float(np.abs(centred).sum())
        if not np.isfinite(gross) or gross <= 0.0:
            return None
        weights = np.clip(centred * (TARGET_GROSS / gross), -MAX_WEIGHT, MAX_WEIGHT)

        net = float(weights.sum())
        if abs(net) > MAX_NET:
            weights = np.clip(weights - net / weights.size, -MAX_WEIGHT, MAX_WEIGHT)
        gross = float(np.abs(weights).sum())
        if gross > TARGET_GROSS:
            weights = weights * (TARGET_GROSS / gross)
        if not np.isfinite(weights).all():
            return None
        return weights


def build_strategy():
    return ResidualCrossSectionalMomentum()
