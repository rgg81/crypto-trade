"""team-08 discovery candidate — per-contract, volatility-scaled, multi-horizon time-series trend.

This is the direct expression of the mandate and of the Tier-1 centre cell declared in
``lane/scouting/THESIS.md`` (§7.1 fixed defaults; W=ALL, T=tanh, N=30).

The signal for contract *i* is a function of contract *i*'s own past log prices and nothing else:
a fixed log-spaced ladder of lookbacks, each rung standardised by the contract's own ex-ante
volatility, each rung mapped to a position by ``tanh``, and the rungs equally weighted. Position
size is inverse to the contract's own volatility. There is no cross-sectional ranking, no funding
or basis signal, no reversal overlay, no order-flow feature, and no volatility-regime gate.

The strategy is a pure function of the ``DecisionContext`` it is handed: no persistent state, no
randomness, no absolute dates, no symbol identity, no embedded parameters fitted off-line.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

# --- Declared configuration (THESIS §7.1 fixed; §7.2 cell W=ALL, T=tanh, N=30) ----------------

# The ladder is declared in *days*, not in bars, so the economic horizons are the same whatever
# the bar spacing of the mounted dataset turns out to be. On an 8h clock these are the declared
# {3, 6, 12, 21, 45, 90, 180, 360} bars.
LADDER_DAYS = (1.0, 2.0, 4.0, 7.0, 15.0, 30.0, 60.0, 120.0)

VOL_COM_DAYS = 20.0        # EWMA centre of mass for ex-ante vol (= 60 bars on an 8h clock)
VOL_RANK_DAYS = 30.0       # trailing window for the liquidity screen
UNIVERSE_N = 30            # top-N by trailing median quote volume
RISK_CAP_MULT = 3.0        # concentration cap: 3x the median inverse-vol weight

MIN_LADDER_RUNGS = 3       # below this, "multiple lookbacks" no longer means anything
MIN_NAMES_FOR_DEPTH = 10   # names needed before a deeper ladder rung is worth carrying
MIN_NAMES_TO_TRADE = 5     # below this the book is not a portfolio; hold flat instead
MIN_VOL_OBS = 20           # minimum return observations before a vol estimate is trusted

GROSS_CAP = 0.99           # tournament caps, with a margin so float error cannot trip them
NET_CAP = 0.245
SYMBOL_CAP = 0.099
WEIGHT_FLOOR = 1e-6

DEFAULT_BARS_PER_DAY = 3.0  # fallback only, if the bar index is not datetime-like
EWMA_TRUNCATION = 12.0      # keep the last 12 centres of mass; the tail weight is < 1e-4


# --- Pure helpers -----------------------------------------------------------------------------


def _bars_per_day(frame: pd.DataFrame) -> float:
    """Infer bar spacing from the frame's own index, in bars per day.

    Relative spacing only — never an absolute date — so this is calendar-shift equivariant.
    """
    index = frame.index
    if len(index) < 3:
        return DEFAULT_BARS_PER_DAY
    try:
        stamps = pd.DatetimeIndex(index)
        if stamps.tz is not None:
            stamps = stamps.tz_convert("UTC").tz_localize(None)
        nanos = stamps.to_numpy(dtype="datetime64[ns]").astype("int64")
    except Exception:
        return DEFAULT_BARS_PER_DAY
    steps = np.diff(nanos) / 1e9
    steps = steps[np.isfinite(steps) & (steps > 0.0)]
    if steps.size == 0:
        return DEFAULT_BARS_PER_DAY
    step = float(np.median(steps))
    if not math.isfinite(step) or step <= 0.0:
        return DEFAULT_BARS_PER_DAY
    per_day = 86400.0 / step
    if per_day < 0.5 or per_day > 48.0:
        return DEFAULT_BARS_PER_DAY
    return per_day


def _log_prices(frame: pd.DataFrame):
    """Return log closes as a float array, NaN where the close is unusable, or None."""
    if "close" not in frame.columns:
        return None
    closes = pd.to_numeric(frame["close"], errors="coerce").to_numpy(dtype=float)
    if closes.size < 2:
        return None
    usable = np.isfinite(closes) & (closes > 0.0)
    if int(usable.sum()) < 2 or not bool(usable[-1]):
        return None
    out = np.full(closes.shape, np.nan, dtype=float)
    out[usable] = np.log(closes[usable])
    return out


def _ewma_sigma(log_prices, com_bars: float) -> float:
    """Ex-ante per-bar volatility: EWMA of squared log returns, MOP form."""
    keep = int(EWMA_TRUNCATION * com_bars) + MIN_VOL_OBS
    tail = log_prices[-keep:] if log_prices.size > keep else log_prices
    returns = pd.Series(tail).diff()
    if int(returns.notna().sum()) < MIN_VOL_OBS:
        return float("nan")
    variance = (returns * returns).ewm(com=com_bars, min_periods=MIN_VOL_OBS).mean()
    value = float(variance.iloc[-1])
    if not math.isfinite(value) or value <= 0.0:
        return float("nan")
    return math.sqrt(value)


def _median_quote_volume(frame: pd.DataFrame, window_bars: int) -> float:
    """Trailing median quote volume — the liquidity screen, computed past-only."""
    if "quote_volume" not in frame.columns:
        return float("nan")
    values = pd.to_numeric(frame["quote_volume"], errors="coerce").to_numpy(dtype=float)
    tail = values[-window_bars:] if values.size > window_bars else values
    tail = tail[np.isfinite(tail) & (tail >= 0.0)]
    if tail.size == 0:
        return float("nan")
    return float(np.median(tail))


def _blend_ladder(log_prices, sigma: float, rung_bars, depth: int) -> float:
    """Equal-weighted mean of ``tanh`` of each rung's volatility-standardised trend.

    Every contract in the book uses the identical ladder; a contract that cannot support one of
    the rungs is rejected upstream rather than run on a shorter ladder.
    """
    last = log_prices[-1]
    total = 0.0
    used = 0
    for position in range(depth):
        span = rung_bars[position]
        if log_prices.size <= span:
            continue
        prior = log_prices[-1 - span]
        if not math.isfinite(prior):
            continue
        scale = sigma * math.sqrt(float(span))
        if not math.isfinite(scale) or scale <= 0.0:
            continue
        total += math.tanh((last - prior) / scale)
        used += 1
    if used < depth:
        return float("nan")
    return total / float(depth)


def _apply_symbol_cap(weights, cap: float):
    """Clip each |w| to ``cap``, redistributing the clipped exposure across uncapped names."""
    book = dict(weights)
    names = list(book)
    if not names:
        return book
    if len(names) * cap <= 1.0:
        return {name: max(-cap, min(cap, value)) for name, value in book.items()}
    for _ in range(8):
        over = {name for name in names if abs(book[name]) > cap}
        if not over:
            break
        excess = sum(abs(book[name]) - cap for name in over)
        for name in over:
            book[name] = cap if book[name] > 0.0 else -cap
        free = sum(abs(book[name]) for name in names if name not in over)
        if free <= 0.0:
            break
        scale = (free + excess) / free
        for name in names:
            if name not in over:
                book[name] *= scale
    # The loop can exit on its iteration bound; the cap is hard, so clip unconditionally.
    return {name: max(-cap, min(cap, value)) for name, value in book.items()}


def _apply_net_cap(weights, cap: float):
    """Bring |net| inside ``cap`` by shrinking the dominant side.

    Shrinking, not shifting: a uniform shift would flip the sign of small positions, which would
    override a per-contract trend forecast with a book-level adjustment. Shrinking never changes
    any contract's direction, and it preserves more gross than a shift does.
    """
    book = dict(weights)
    longs = sum(value for value in book.values() if value > 0.0)
    shorts = -sum(value for value in book.values() if value < 0.0)
    net = longs - shorts
    if net > cap and longs > 0.0:
        factor = (cap + shorts) / longs
        return {n: (v * factor if v > 0.0 else v) for n, v in book.items()}
    if net < -cap and shorts > 0.0:
        factor = (cap + longs) / shorts
        return {n: (v * factor if v < 0.0 else v) for n, v in book.items()}
    return book


# --- Strategy ---------------------------------------------------------------------------------


class MultiHorizonTrend:
    """Per-contract multi-horizon time-series trend, inverse-volatility sized.

    Holds no state between decisions; every number is recomputed from the past-only rows in the
    context it is given.
    """

    def target_weights(self, context, *, seed):
        # Deterministic by construction: the seed is deliberately unused.
        bars = context.bars

        # 1. Usable price histories for the point-in-time membership.
        prepared = []
        per_day = DEFAULT_BARS_PER_DAY
        longest = -1
        for symbol in context.eligible_symbols:
            if symbol not in bars:
                continue
            frame = bars[symbol]
            if not isinstance(frame, pd.DataFrame) or frame.shape[0] < 5:
                continue
            log_prices = _log_prices(frame)
            if log_prices is None:
                continue
            prepared.append((symbol, frame, log_prices))
            if frame.shape[0] > longest:
                longest = frame.shape[0]
                per_day = _bars_per_day(frame)
        if len(prepared) < MIN_NAMES_TO_TRADE:
            return {}

        # 2. Translate the declared day-ladder onto this dataset's bar clock.
        com_bars = max(2.0, VOL_COM_DAYS * per_day)
        rung_bars = [max(1, int(round(days * per_day))) for days in LADDER_DAYS]
        warmup = int(math.ceil(com_bars)) + 1

        # 3. Ladder depth: carry the longest rungs only while enough contracts can support them,
        #    and keep the ladder identical across every contract in the book.
        depth = MIN_LADDER_RUNGS
        for candidate_depth in range(len(rung_bars), MIN_LADDER_RUNGS - 1, -1):
            needed = rung_bars[candidate_depth - 1] + warmup
            supported = sum(1 for _, _, lp in prepared if lp.size >= needed)
            if supported >= MIN_NAMES_FOR_DEPTH:
                depth = candidate_depth
                break
        needed = rung_bars[depth - 1] + warmup
        usable = [item for item in prepared if item[2].size >= needed]
        if len(usable) < MIN_NAMES_TO_TRADE:
            return {}

        # 4. Liquidity screen — top N by trailing median quote volume. This protects the
        #    participation limit; it is not a signal.
        window_bars = max(5, int(round(VOL_RANK_DAYS * per_day)))
        ranked = []
        for symbol, frame, log_prices in usable:
            volume = _median_quote_volume(frame, window_bars)
            if not math.isfinite(volume) or volume <= 0.0:
                continue
            ranked.append((volume, symbol, log_prices))
        if len(ranked) < MIN_NAMES_TO_TRADE:
            return {}
        ranked.sort(key=lambda item: (-item[0], item[1]))
        selected = ranked[:UNIVERSE_N]

        # 5. Per-contract signal and per-contract risk weight.
        signals = {}
        inverse_vol = {}
        for _, symbol, log_prices in selected:
            sigma = _ewma_sigma(log_prices, com_bars)
            if not math.isfinite(sigma) or sigma <= 0.0:
                continue
            blended = _blend_ladder(log_prices, sigma, rung_bars, depth)
            if not math.isfinite(blended):
                continue
            signals[symbol] = blended
            inverse_vol[symbol] = 1.0 / sigma
        if len(signals) < MIN_NAMES_TO_TRADE:
            return {}

        # 6. Volatility scaling, with the declared concentration cap on the risk weight.
        risk = np.array([inverse_vol[symbol] for symbol in signals], dtype=float)
        median_risk = float(np.median(risk))
        risk_cap = RISK_CAP_MULT * median_risk if median_risk > 0.0 else float("inf")
        book = {
            symbol: signals[symbol] * min(inverse_vol[symbol], risk_cap) for symbol in signals
        }

        gross = sum(abs(value) for value in book.values())
        if not math.isfinite(gross) or gross <= 0.0:
            return {}
        book = {symbol: value / gross for symbol, value in book.items()}

        # 7. Tournament exposure constraints, applied in an order I can reason about.
        book = _apply_symbol_cap(book, SYMBOL_CAP)
        book = _apply_net_cap(book, NET_CAP)
        gross = sum(abs(value) for value in book.values())
        if not math.isfinite(gross) or gross <= 0.0:
            return {}
        if gross > GROSS_CAP:
            shrink = GROSS_CAP / gross
            book = {symbol: value * shrink for symbol, value in book.items()}

        return {
            symbol: float(value)
            for symbol, value in book.items()
            if math.isfinite(value) and abs(value) >= WEIGHT_FLOOR
        }


def build_strategy():
    return MultiHorizonTrend()
