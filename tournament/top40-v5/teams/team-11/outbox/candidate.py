"""team-11 -- participant mix from average trade size.

Economic family: microstructure and participation.

Average trade size S = quote_volume / trade_count is the notional that rode on each print.
log S == log V - log N exactly, so S is the *composition* of trading, orthogonal in direction to
the *scale* of trading that a volume factor loads on. S is unsigned, so it cannot set a direction
on its own; it conditions the sign of taker order flow, which is the one signed participation
variable this dataset exposes.

Long  when large prints accompany net taker buying   (professional accumulation -> continuation).
Short when small prints accompany net taker buying   (retail chasing            -> reversal).

Both inputs are measured only as within-asset deviations from their own trailing distribution,
never as levels and never as raw cross-sectional ranks, so the book cannot become a size or
liquidity factor in disguise.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

# --- Signal construction -------------------------------------------------------------------
NORM_WINDOW = 180   # 60d: trailing distribution for the within-asset z-score
NORM_MIN = 90       # 30d: shortest trailing window accepted
SMOOTH = 45         # 15d: conviction smoothing -- this is the turnover budget knob
BURN_IN = 30        # declared hygiene: discard a listing's first 30 bars
CLIP = 3.0          # declared winsorisation, in SD

MIN_ROWS = BURN_IN + NORM_MIN + SMOOTH   # 165 bars ~ 55 days of clean history
TAIL_ROWS = NORM_WINDOW + SMOOTH         # all that the last z-value can depend on

# --- Rebalance cadence ---------------------------------------------------------------------
# 9 bars = 3 days = 9 funding epochs. The decision grid is 8h; trading it is not affordable.
REBALANCE_EVERY = 9

# --- Portfolio construction ----------------------------------------------------------------
MAX_WEIGHT = 0.09   # inside the 0.10 per-symbol cap
MAX_GROSS = 1.0
MAX_NET = 0.20      # inside the 0.25 net cap
MIN_NAMES = 12
DUST = 2e-4


def _last_smoothed_z(values: np.ndarray) -> float | None:
    """Mean of the last SMOOTH trailing z-scores of ``values``; None if not identified.

    The z-score is taken first and smoothed second, so the trailing scale is estimated from
    NORM_WINDOW raw observations rather than from a handful of overlapping averages.
    """
    if values.shape[0] < NORM_MIN + SMOOTH:
        return None
    series = pd.Series(values[-TAIL_ROWS:], dtype="float64")
    roll = series.rolling(NORM_WINDOW, min_periods=NORM_MIN)
    scale = roll.std(ddof=0)
    z = (series - roll.mean()) / scale.where(scale > 0.0)
    tail = z.to_numpy()[-SMOOTH:]
    tail = tail[np.isfinite(tail)]
    if tail.shape[0] * 3 < SMOOTH * 2:
        return None
    value = float(tail.mean())
    if not math.isfinite(value):
        return None
    return float(np.clip(value, -CLIP, CLIP))


def _conviction(frame) -> float | None:
    """Signed conviction for one symbol: smoothed z(taker imbalance) x smoothed z(log trade size)."""
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return None
    for column in ("quote_volume", "trade_count", "taker_buy_quote_volume"):
        if column not in frame.columns:
            return None
    if "open_time" in frame.columns:
        frame = frame.sort_values("open_time", kind="mergesort")

    quote = pd.to_numeric(frame["quote_volume"], errors="coerce").to_numpy(dtype="float64")
    count = pd.to_numeric(frame["trade_count"], errors="coerce").to_numpy(dtype="float64")
    taker = pd.to_numeric(frame["taker_buy_quote_volume"], errors="coerce").to_numpy(dtype="float64")

    usable = (
        np.isfinite(quote) & np.isfinite(count) & np.isfinite(taker)
        & (quote > 0.0) & (count > 0.0)
    )
    quote, count, taker = quote[usable], count[usable], taker[usable]
    if quote.shape[0] < MIN_ROWS:
        return None
    quote, count, taker = quote[BURN_IN:], count[BURN_IN:], taker[BURN_IN:]

    # Composition: USD notional per print. Scale-equivariant once z-scored.
    size = np.log(quote / count)
    # Direction: net taker imbalance in [-1, +1]. Scale-invariant by construction.
    flow = 2.0 * np.clip(taker / quote, 0.0, 1.0) - 1.0

    z_size = _last_smoothed_z(size)
    z_flow = _last_smoothed_z(flow)
    if z_size is None or z_flow is None:
        return None
    return float(np.clip(z_flow * z_size, -CLIP, CLIP))


def _weights(convictions: dict[str, float]) -> dict[str, float] | None:
    """Cross-sectionally demeaned conviction -> signed, capped, net-zero weights.

    The signed square root is portfolio construction, not signal: the conviction is a product of
    two z-scores and is therefore leptokurtic with a peak at zero, which concentrates a linear
    book into a handful of names. The compression is monotone and odd, so it preserves the
    ordering and the zero -- a name sitting at its own trailing median still gets no weight.
    """
    symbols = sorted(convictions)
    raw = np.array([convictions[s] for s in symbols], dtype="float64")
    centred = raw - raw.mean()

    tilt = np.sign(centred) * np.sqrt(np.abs(centred))
    tilt = tilt - tilt.mean()
    gross = float(np.abs(tilt).sum())
    if not math.isfinite(gross) or gross <= 0.0:
        return None

    weights = tilt / gross
    weights = np.clip(weights, -MAX_WEIGHT, MAX_WEIGHT)
    weights = weights - weights.mean()
    gross = float(np.abs(weights).sum())
    if not math.isfinite(gross) or gross <= 0.0:
        return None
    weights = weights / gross

    # Scale down by whichever constraint binds; the organizer owns the risk unit, not me.
    denom = max(
        1.0,
        float(np.abs(weights).max()) / MAX_WEIGHT,
        float(np.abs(weights).sum()) / MAX_GROSS,
        abs(float(weights.sum())) / MAX_NET,
    )
    weights = weights / denom

    book: dict[str, float] = {}
    for symbol, weight in zip(symbols, weights):
        value = float(weight)
        if not math.isfinite(value):
            return None
        book[symbol] = 0.0 if abs(value) < DUST else value
    return book


class ParticipantMixStrategy:
    """Stateless: every decision is recomputed from the past-only rows in the context."""

    def target_weights(self, context, *, seed):
        bars = context.bars
        eligible = context.eligible_symbols
        if bars is None or eligible is None or len(bars) == 0 or len(eligible) == 0:
            return None

        # Data-derived cadence counter. Bar history grows by one row per decision, so this
        # advances with the run without referring to any absolute date.
        lengths = [len(frame) for frame in bars.values() if frame is not None]
        if not lengths:
            return None
        if max(lengths) % REBALANCE_EVERY != 0:
            return None  # hold current quantities; no trade, no cost

        convictions: dict[str, float] = {}
        for symbol in eligible:
            value = _conviction(bars.get(symbol))
            if value is not None:
                convictions[symbol] = value
        if len(convictions) < MIN_NAMES:
            return None

        return _weights(convictions)


def build_strategy():
    return ParticipantMixStrategy()
