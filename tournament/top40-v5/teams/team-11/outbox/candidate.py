"""team-11 nomination -- participant mix from average trade size.

Economic family: microstructure and participation.
Mandate: average trade size as a retail-versus-institutional proxy.

Average trade size S = quote_volume / trade_count is the USD notional that rode on each print.

    log S  ==  log V - log N        (exact identity)

N is the arrival clock; conditional on the clock, S is the *composition* of trading rather than
its *scale*. A volume factor loads on the (+1,+1) direction in (log V, log N) space; this mandate
lives on (+1,-1) and nowhere else.

S is unsigned -- large prints do not say "up" -- so it conditions the sign of the one signed
participation variable this dataset exposes, the taker imbalance:

    OFI = 2 * taker_buy_quote_volume / quote_volume - 1      in [-1, +1]

    long  when large prints accompany relative net taker buying    (professional accumulation)
    short when small prints accompany relative net taker buying    (retail chasing)

The sign is the one pre-committed in the sealed thesis and is unchanged after a negative
development result. Both inputs enter only as within-asset deviations from their own trailing
distribution -- never as levels, never as raw cross-sectional ranks -- so the book cannot become a
size or liquidity factor in disguise.

The signature property, preserved exactly by the construction below: a name whose average trade
size sits at its own trailing median gets conviction zero and weight zero, no matter how large its
volume is. A volume proxy cannot have that property.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

# --- Signal construction -------------------------------------------------------------------
NORM_WINDOW = 180   # 60d: trailing distribution for the within-asset z-score
NORM_MIN = 90       # 30d: shortest trailing window accepted
SMOOTH = 90         # 30d: conviction smoothing -- this is the turnover budget knob
BURN_IN = 30        # declared hygiene: discard a listing's first 30 bars
CLIP = 3.0          # declared winsorisation, in SD

MIN_ROWS = BURN_IN + NORM_MIN + SMOOTH   # 210 bars ~ 70 days of clean history
TAIL_ROWS = NORM_WINDOW + SMOOTH         # 270 bars: all the last smoothed z can depend on

# --- Rebalance cadence ---------------------------------------------------------------------
# 18 bars = 6 days = 61 book refreshes per year. Between refreshes the strategy returns None,
# which the protocol defines as holding current quantities: no trade, no cost.
REBALANCE_EVERY = 18

# --- Portfolio construction ----------------------------------------------------------------
MAX_WEIGHT = 0.09   # inside the 0.10 per-symbol cap
MAX_GROSS = 1.0
MAX_NET = 0.25
MIN_NAMES = 10
SIDE_FLOOR = 0.05   # a side thinner than this is not a portfolio; sit the refresh out
DUST = 2e-4


def _smoothed_z(values: np.ndarray) -> float | None:
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


def _factors(frame) -> tuple[float, float] | None:
    """Return ``(z_size, z_flow)`` for one symbol, or None if either is not identified.

    Every quantity is read out of the symbol's own frame, so no cross-symbol panel is ever
    built and the positional-RangeIndex alignment trap cannot arise here.
    """
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

    # Composition: USD notional per print. A price rescaling shifts log S by a constant that the
    # trailing mean subtraction removes, so this is scale-equivariant by construction.
    size = np.log(quote / count)
    # Direction: net taker imbalance in [-1, +1], a ratio and so scale-invariant outright.
    flow = 2.0 * np.clip(taker / quote, 0.0, 1.0) - 1.0

    z_size = _smoothed_z(size)
    z_flow = _smoothed_z(flow)
    if z_size is None or z_flow is None:
        return None
    return z_size, z_flow


def _balance(weights: np.ndarray) -> np.ndarray | None:
    """Scale each side until long and short gross are equal.

    Neutralisation by *scaling* rather than by *shifting*: a shift would hand a nonzero weight to
    a name sitting at its own trailing median, which is precisely the property that separates this
    book from a volume book. Scaling maps zero to zero and preserves the ordering within a side.
    """
    longs = weights > 0.0
    shorts = weights < 0.0
    long_gross = float(weights[longs].sum())
    short_gross = float(-weights[shorts].sum())
    gross = long_gross + short_gross
    if not math.isfinite(gross) or gross <= 0.0:
        return None
    if min(long_gross, short_gross) < SIDE_FLOOR * gross:
        return None

    balanced = weights.copy()
    balanced[longs] = weights[longs] * (0.5 * gross / long_gross)
    balanced[shorts] = weights[shorts] * (0.5 * gross / short_gross)
    return balanced


def _book(sizes: list[float], flows: list[float]) -> np.ndarray | None:
    """Per-symbol factors -> signed, capped, side-balanced weights."""
    size = np.asarray(sizes, dtype="float64")
    flow = np.asarray(flows, dtype="float64")

    # Cross-sectional demeaning of the *flow* factor only. It removes the market-wide buy/sell
    # wave that would otherwise put a common directional tilt on every name, and it guarantees
    # both sides are populated -- while leaving conviction exactly zero wherever z_size is zero.
    flow = flow - flow.mean()
    conviction = np.clip(flow * size, -CLIP, CLIP)

    # Signed square root: conviction is a product of two z-scores, so it is leptokurtic with a
    # density that diverges at zero, and a linear map concentrates the book into a few names.
    # The map is monotone and odd, so it preserves the ordering and the zero. Portfolio
    # construction, not a re-specified signal.
    weights = np.sign(conviction) * np.sqrt(np.abs(conviction))
    gross = float(np.abs(weights).sum())
    if not math.isfinite(gross) or gross <= 0.0:
        return None
    weights = weights / gross

    balanced = _balance(weights)
    if balanced is None:
        return None
    balanced = _balance(np.clip(balanced, -MAX_WEIGHT, MAX_WEIGHT))
    if balanced is None:
        return None

    gross = float(np.abs(balanced).sum())
    peak = float(np.abs(balanced).max())
    net = abs(float(balanced.sum()))
    if not math.isfinite(gross) or gross <= 0.0 or not math.isfinite(peak) or peak <= 0.0:
        return None

    # One uniform rescale by whichever contract constraint binds. Uniform, so the exact side
    # balance survives it. The organizer owns the risk unit; these are caps, not a risk target.
    scale = min(MAX_GROSS / gross, MAX_WEIGHT / peak)
    if net > 0.0:
        scale = min(scale, MAX_NET / net)
    weights = balanced * scale
    if not np.all(np.isfinite(weights)):
        return None
    return np.where(np.abs(weights) < DUST, 0.0, weights)


class ParticipantMixStrategy:
    """Stateless: every decision is recomputed from the past-only rows in the context."""

    def target_weights(self, context, *, seed):
        del seed  # nothing here is stochastic; the book is a pure function of the context

        bars = context.bars
        eligible = context.eligible_symbols
        if bars is None or eligible is None or len(bars) == 0 or len(eligible) == 0:
            return None

        # Data-derived cadence counter. Bar history grows by one row per decision, so this
        # advances with the run without ever referring to an absolute date.
        lengths = [len(frame) for frame in bars.values() if frame is not None]
        if not lengths:
            return None
        if max(lengths) % REBALANCE_EVERY != 0:
            return None  # hold current quantities; no trade, no cost

        symbols: list[str] = []
        sizes: list[float] = []
        flows: list[float] = []
        for symbol in sorted(eligible):
            factors = _factors(bars.get(symbol))
            if factors is None:
                continue
            symbols.append(symbol)
            sizes.append(factors[0])
            flows.append(factors[1])
        if len(symbols) < MIN_NAMES:
            return None

        weights = _book(sizes, flows)
        if weights is None:
            return None
        return {symbol: float(weight) for symbol, weight in zip(symbols, weights)}


def build_strategy():
    return ParticipantMixStrategy()
