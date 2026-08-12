"""Team-07 -- funding carry with a crowding-crash weight guard.

Mechanism
---------
Perpetual funding is a cashflow paid by the crowded side. Its cross-sectional *level* is the
carry: a name whose perpetual pays 60% annualised is a name whose longs are paying to stay long,
and taking the other side collects that payment. Its *duration* -- the fraction of recent
settlements in which the contract traded at a premium to its index at all -- measures how
entrenched that crowd is, and entrenchment is the thing that hurts a carry book, because an
entrenched crowd is one the market has been validating.

The book therefore has two parts and they are deliberately separable:

1.  CARRY. Rank the eligible cross-section by carry-to-risk, ``(f_i - median f) / sigma_i``, where
    ``f_i`` is the mean funding rate over the last ``CARRY_LOOKBACK`` settlements and ``sigma_i``
    the realised volatility of the last ``RISK_LOOKBACK`` bar returns. Short the ``SLEEVE_NAMES``
    richest, buy the ``SLEEVE_NAMES`` cheapest, size every position at ``1/sigma_i`` so each name
    contributes comparable risk, and normalise each sleeve to equal gross so the book is dollar
    neutral by construction.

2.  CROWDING GUARD. For short positions only, multiply the weight by
    ``1 - CROWDING_PENALTY * premium_duration_i``, where ``premium_duration_i`` is the fraction of
    the last ``CROWDING_LOOKBACK`` settlements whose funding rate exceeded ``PREMIUM_BASELINE``
    (0.01% per 8h -- Binance's interest component, so "above it" means the perpetual actually
    traded at a premium rather than merely paying the base rate). A name the crowd has occupied
    continuously is not removed from the book -- its carry is the most valuable in the sleeve --
    but it is sized down in favour of the less entrenched shorts beside it. ``CROWDING_PENALTY = 0``
    disables the guard exactly and changes nothing else, which is how the ablation is run.

    The guard is asymmetric on purpose. Positive funding is the resting state of a crypto
    perpetual, so persistent premium marks a crowd that is being paid to stay; persistent
    *discount* is rare, marks capitulation, and is the one the book most wants to be long of.

Everything is causal: funding rows arrive strictly before the decision, bars close at or before
it, and no execution price, fill, cost or equity is visible to this module.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext, TargetStrategy

# --- declared neighbourhood coordinates (module-level, one plain literal each) ---------------
CARRY_LOOKBACK = 63
RISK_LOOKBACK = 63
SLEEVE_NAMES = 7
CROWDING_PENALTY = 0.00

# --- fixed structural constants (not swept) --------------------------------------------------
CROWDING_LOOKBACK = 63
PREMIUM_BASELINE = 0.0001
REBALANCE_CADENCE = 2
REBALANCE_PHASE = 0
RISK_SIZING = 0


def _tail_mean(values: np.ndarray, window: int, minimum: int) -> float:
    if values.size < minimum:
        return math.nan
    tail = values[-window:]
    return float(tail.mean())


class FundingCarryCrowdingGuard:
    """Cross-sectional funding carry, risk-sized, with a crowding weight guard on the shorts."""

    def __init__(self) -> None:
        self._rates: dict[str, list[float]] = {}
        self._covered: dict[str, pd.Timestamp] = {}
        self._global_last: pd.Timestamp | None = None
        self._boundary = -1

    # -- funding bookkeeping ------------------------------------------------------------------
    def _ingest(self, funding: pd.DataFrame, eligible: tuple[str, ...]) -> None:
        """Accumulate per-symbol funding history from the past-only rows the context supplies.

        The context filters funding to the currently eligible names, so a symbol that leaves and
        later rejoins the universe has a hole in whatever we accumulated while it was out. Any
        name not covered through the previous call's horizon is therefore rebuilt in full rather
        than appended to.
        """
        if funding.empty:
            return
        times = funding["funding_time"]
        previous = self._global_last
        if previous is None:
            fresh = funding
        else:
            start = int(times.searchsorted(previous, side="right"))
            fresh = funding.iloc[start:]
        stale = [
            symbol
            for symbol in eligible
            if previous is None
            or self._covered.get(symbol) is None
            or self._covered[symbol] < previous
        ]
        if stale:
            subset = funding[funding["symbol"].isin(stale)]
            for symbol, group in subset.groupby("symbol", observed=True, sort=False):
                self._rates[symbol] = [float(v) for v in group["funding_rate"].to_numpy()]
        elif not fresh.empty:
            for symbol, group in fresh.groupby("symbol", observed=True, sort=False):
                bucket = self._rates.setdefault(symbol, [])
                bucket.extend(float(v) for v in group["funding_rate"].to_numpy())
        horizon = pd.Timestamp(times.iloc[-1])
        for symbol in eligible:
            self._covered[symbol] = horizon
        self._global_last = horizon

    # -- the decision -------------------------------------------------------------------------
    def target_weights(
        self, context: DecisionContext, *, seed: int
    ) -> Mapping[str, float] | None:
        del seed  # the book is deterministic; nothing here is sampled
        eligible = tuple(context.eligible_symbols)
        self._boundary += 1
        self._ingest(context.funding, eligible)
        cadence = max(1, int(REBALANCE_CADENCE))
        if (self._boundary % cadence) != (int(REBALANCE_PHASE) % cadence):
            return None

        carry_window = max(2, int(CARRY_LOOKBACK))
        risk_window = max(4, int(RISK_LOOKBACK))
        crowd_window = max(2, int(CROWDING_LOOKBACK))
        sleeve = max(1, int(SLEEVE_NAMES))

        carry: dict[str, float] = {}
        risk: dict[str, float] = {}
        crowd: dict[str, float] = {}
        for symbol in eligible:
            rates = self._rates.get(symbol)
            if rates is None or len(rates) < carry_window // 2 or len(rates) < crowd_window // 2:
                continue
            frame = context.bars.get(symbol)
            if frame is None or len(frame) < risk_window // 2 + 1:
                continue
            closes = frame["close"].to_numpy(dtype=float)[-(risk_window + 1):]
            if closes.size < 3 or not np.isfinite(closes).all() or (closes <= 0).any():
                continue
            returns = closes[1:] / closes[:-1] - 1.0
            sigma = float(returns.std(ddof=1)) if returns.size > 1 else math.nan
            if not math.isfinite(sigma) or sigma <= 0.0:
                continue
            history = np.asarray(rates, dtype=float)
            mean_rate = _tail_mean(history, carry_window, carry_window // 2)
            if not math.isfinite(mean_rate):
                continue
            premium = history[-crowd_window:]
            duration = float((premium > PREMIUM_BASELINE).mean())
            carry[symbol] = mean_rate
            risk[symbol] = sigma
            crowd[symbol] = duration

        if len(carry) < 2 * sleeve:
            return None

        risk_sized = int(RISK_SIZING) != 0
        centre = float(np.median(np.fromiter(carry.values(), dtype=float, count=len(carry))))
        # ties broken by symbol so the ranking is a total order and the run is exactly replayable
        if risk_sized:
            ordered = sorted(carry, key=lambda s: ((carry[s] - centre) / risk[s], s))
        else:
            ordered = sorted(carry, key=lambda s: (carry[s] - centre, s))
        longs = ordered[:sleeve]
        shorts = ordered[-sleeve:]

        unit = (lambda s: 1.0 / risk[s]) if risk_sized else (lambda s: 1.0)
        raw_long = {s: unit(s) for s in longs}
        raw_short = {s: unit(s) for s in shorts}
        penalty = float(CROWDING_PENALTY)
        if penalty != 0.0:
            for s in shorts:
                raw_short[s] *= min(1.0, max(0.0, 1.0 - penalty * crowd[s]))

        long_gross = sum(raw_long.values())
        short_gross = sum(raw_short.values())
        if long_gross <= 0.0 or short_gross <= 0.0:
            return None

        weights: dict[str, float] = {}
        for s, v in raw_long.items():
            weights[s] = 0.5 * v / long_gross
        for s, v in raw_short.items():
            weights[s] = -0.5 * v / short_gross
        return weights


def build_strategy() -> TargetStrategy:
    return FundingCarryCrowdingGuard()
