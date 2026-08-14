"""Team 12 -- preregistered multi-sleeve ensemble.

Four sleeves on four distinct causal bases, combined by a rule that was written down and
journaled before any combined number existed:

  CARRY    the perpetual funding mechanism moves cash from the crowded side to the uncrowded
           side, so the names paying the most funding are the ones whose longs are paying to
           stay long.  Cross-sectional rank of trailing mean funding, sign flipped.
  TREND    information diffuses slowly across a fragmented 24/7 retail base and leverage makes
           the diffusion reflexive.  Per-coin time-series momentum, volatility-scaled, blended
           over three horizons.  Its net exposure is a free variable and swings with the market.
  LOWRISK  leverage-constrained and lottery-seeking participants overpay for the wild names, so
           risk is priced too cheaply at the calm end of a blue-chip cross-section.  Cross-
           sectional rank of trailing drawdown depth, sign flipped.
  FLOW     aggressive, price-insensitive demand leaves a persistent footprint in the buy/sell
           split of traded volume.  Cross-sectional rank of trailing taker-buy share.

COMBINATION RULE -- preregistered, and the thing this lane is actually testing:

  At every decision boundary each sleeve emits a unit-gross weight vector.  Sleeve k contributes
  that vector times 1 / sigma_k(t), where sigma_k(t) is the sample standard deviation (ddof=1)
  of sleeve k's own past-only proxy return series over the most recent RISK_PARITY_BARS
  observations attributed to boundaries strictly before t.  The proxy return attributed to
  boundary g is the sleeve's own unit-gross vector formed at boundary g-1 applied to the
  close-to-close simple return of the bar that closed at g; no costs, no funding, no leverage.
  Before RISK_PARITY_BARS observations exist, or if sigma_k(t) is not finite and strictly
  positive, the multiplier is 1.  The book is the plain sum of the scaled sleeve vectors,
  returned unnormalised; the evaluator's unit-gross normalisation then applies.  No other
  sleeve-level multiplier, tilt, cap, floor, sign flip, correlation term or performance-
  conditioned term is applied anywhere.

Naive inverse volatility rather than a full equal-risk-contribution solve, deliberately: the
correlation matrix is the channel through which a combination learns from the answer, and this
lane forbids that.

Causality.  At a decision boundary the runner exposes bars whose close time is at or before the
boundary and funding settlements strictly before it.  Every read below is off the tail of those
frames.  No execution price, no fill, no PnL and no equity is available and none is used.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

# --- sleeve formation horizons, in 8h decision boundaries -------------------------------------
CARRY_LOOKBACK = 126           # 42 days of funding settlements
TREND_BASE_LOOKBACK = 90       # blended over TREND_BASE/2, TREND_BASE, 3*TREND_BASE/2
LOWRISK_BASE_LOOKBACK = 189    # blended over LOWRISK_BASE, 2x, 3x
FLOW_BASE_LOOKBACK = 63        # blended over FLOW_BASE and 2*FLOW_BASE
TREND_VOL_LOOKBACK = 90        # realised-volatility scaler for the trend sleeve

# --- the combination rule's own parameter -----------------------------------------------------
RISK_PARITY_BARS = 270         # 90 days, matching the organiser's own common-risk-unit lookback

# --- rebalance schedule -----------------------------------------------------------------------
REBALANCE_CADENCE = 6          # act every 6th boundary (48h); hold quantities in between
REBALANCE_PHASE = 3            # which residue class of the boundary index is acted on

# --- sleeve switches: 1 includes the sleeve, 0 removes it (used by the ablation candidates) ----
USE_CARRY = 0
USE_TREND = 1
USE_LOWRISK = 1
USE_FLOW = 1

# --- combination switch: 0 = the preregistered inverse-volatility rule, 1 = equal notional -----
EQUAL_NOTIONAL = 0

# --- transparent-baseline switch: 1 replaces the whole book with an equal-weight long basket ---
BASELINE_LONG_ONLY = 0

TREND_LOOKBACKS = (TREND_BASE_LOOKBACK // 2, TREND_BASE_LOOKBACK, 3 * TREND_BASE_LOOKBACK // 2)
LOWRISK_LOOKBACKS = (LOWRISK_BASE_LOOKBACK, 2 * LOWRISK_BASE_LOOKBACK, 3 * LOWRISK_BASE_LOOKBACK)
FLOW_LOOKBACKS = (FLOW_BASE_LOOKBACK, 2 * FLOW_BASE_LOOKBACK)

_MIN_CROSS_SECTION = 4
_EIGHT_HOURS = pd.Timedelta(hours=8)


def _demean_rank(values: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Cross-sectional rank of the valid entries, standardised to zero mean and unit spread."""
    out = np.zeros(values.shape[0], dtype=float)
    idx = np.where(valid & np.isfinite(values))[0]
    n = idx.size
    if n < _MIN_CROSS_SECTION:
        return out
    order = idx[np.argsort(values[idx], kind="stable")]
    ranks = np.arange(n, dtype=float)
    spread = ranks.std()
    out[order] = (ranks - ranks.mean()) / (spread if spread > 0.0 else 1.0)
    return out


def _unit_gross(vector: np.ndarray) -> np.ndarray:
    gross = float(np.abs(vector).sum())
    return vector / gross if gross > 0.0 else vector


class MultiSleeveEnsemble:
    """Four preregistered sleeves, combined by inverse volatility of their own past returns."""

    def __init__(self) -> None:
        self._boundary = -1
        self._history: dict[str, list[float]] = {}
        self._previous_weights: dict[str, dict[str, float]] = {}
        self._previous_close: dict[str, float] = {}

    # -- sleeve signals -------------------------------------------------------------------------

    def _carry(self, symbols, closes, flows, funding, decision_time) -> np.ndarray:
        raw = np.full(len(symbols), np.nan)
        if funding is None or funding.empty:
            return np.zeros(len(symbols))
        cutoff = decision_time - CARRY_LOOKBACK * _EIGHT_HOURS
        recent = funding.tail(40_000)
        settlement = pd.to_datetime(recent["funding_time"], utc=True).dt.floor("h")
        window = recent.loc[(settlement >= cutoff).to_numpy()]
        if window.empty:
            return np.zeros(len(symbols))
        totals = window.groupby("symbol")["funding_rate"].sum()
        for position, symbol in enumerate(symbols):
            if symbol in totals.index:
                raw[position] = float(totals[symbol]) / CARRY_LOOKBACK
        valid = np.isfinite(raw)
        return _unit_gross(-_demean_rank(raw, valid))

    def _trend(self, symbols, closes, flows, funding, decision_time) -> np.ndarray:
        need = max(TREND_LOOKBACKS) + 1
        signal = np.zeros(len(symbols))
        for position, symbol in enumerate(symbols):
            close = closes[symbol]
            if close.size < max(need, TREND_VOL_LOOKBACK + 1):
                continue
            score = 0.0
            for lookback in TREND_LOOKBACKS:
                ratio = close[-1] / close[-1 - lookback] - 1.0
                score += math.copysign(1.0, ratio) if ratio != 0.0 else 0.0
            score /= len(TREND_LOOKBACKS)
            logs = np.diff(np.log(close[-(TREND_VOL_LOOKBACK + 1) :]))
            volatility = float(np.std(logs, ddof=0))
            if not math.isfinite(volatility) or volatility <= 0.0:
                continue
            signal[position] = score / volatility
        return _unit_gross(signal)

    def _lowrisk(self, symbols, closes, flows, funding, decision_time) -> np.ndarray:
        accumulated = np.zeros(len(symbols))
        counted = 0
        for lookback in LOWRISK_LOOKBACKS:
            raw = np.full(len(symbols), np.nan)
            for position, symbol in enumerate(symbols):
                close = closes[symbol]
                if close.size < lookback + 1:
                    continue
                logs = np.diff(np.log(close[-(lookback + 1) :]))
                equity = np.cumsum(logs)
                raw[position] = float(np.max(np.maximum.accumulate(equity) - equity))
            accumulated += _demean_rank(raw, np.isfinite(raw))
            counted += 1
        return _unit_gross(-accumulated / max(counted, 1))

    def _flow(self, symbols, closes, flows, funding, decision_time) -> np.ndarray:
        accumulated = np.zeros(len(symbols))
        counted = 0
        for lookback in FLOW_LOOKBACKS:
            raw = np.full(len(symbols), np.nan)
            for position, symbol in enumerate(symbols):
                imbalance = flows[symbol]
                if imbalance.size < lookback:
                    continue
                window = imbalance[-lookback:]
                if not np.isfinite(window).all():
                    window = window[np.isfinite(window)]
                    if window.size == 0:
                        continue
                raw[position] = float(window.mean())
            accumulated += _demean_rank(raw, np.isfinite(raw))
            counted += 1
        return _unit_gross(accumulated / max(counted, 1))

    # -- the preregistered combination ---------------------------------------------------------

    def _sleeve_names(self) -> tuple[str, ...]:
        active = []
        if USE_CARRY:
            active.append("carry")
        if USE_TREND:
            active.append("trend")
        if USE_LOWRISK:
            active.append("lowrisk")
        if USE_FLOW:
            active.append("flow")
        return tuple(active)

    def _record_proxy_returns(self, symbols, closes) -> None:
        """Append each sleeve's own past-only proxy return for the bar that closed at t."""
        realised: dict[str, float] = {}
        for position, symbol in enumerate(symbols):
            close = closes[symbol]
            previous = self._previous_close.get(symbol)
            if previous is None or close.size == 0 or previous <= 0.0:
                continue
            realised[symbol] = close[-1] / previous - 1.0
        for name in self._sleeve_names():
            weights = self._previous_weights.get(name)
            if not weights:
                continue
            total = 0.0
            for symbol, weight in weights.items():
                move = realised.get(symbol)
                if move is not None and math.isfinite(move):
                    total += weight * move
            self._history.setdefault(name, []).append(total)

    def _multiplier(self, name: str) -> float:
        if EQUAL_NOTIONAL:
            return 1.0
        history = self._history.get(name, [])
        if len(history) < RISK_PARITY_BARS:
            return 1.0
        window = np.asarray(history[-RISK_PARITY_BARS:], dtype=float)
        if not np.isfinite(window).all():
            return 1.0
        deviation = float(np.std(window, ddof=1))
        if not math.isfinite(deviation) or deviation <= 0.0:
            return 1.0
        return 1.0 / deviation

    # -- protocol -------------------------------------------------------------------------------

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        self._boundary += 1
        symbols: Sequence[str] = sorted(context.eligible_symbols)
        if not symbols:
            return {}
        closes: dict[str, np.ndarray] = {}
        flows: dict[str, np.ndarray] = {}
        longest = max(
            CARRY_LOOKBACK,
            max(TREND_LOOKBACKS) + 1,
            max(LOWRISK_LOOKBACKS) + 1,
            max(FLOW_LOOKBACKS),
            TREND_VOL_LOOKBACK + 1,
        )
        for symbol in symbols:
            frame = context.bars[symbol]
            tail = frame.iloc[-(longest + 2) :]
            closes[symbol] = tail["close"].to_numpy(dtype=float)
            quote = tail["quote_volume"].to_numpy(dtype=float)
            taker = tail["taker_buy_quote_volume"].to_numpy(dtype=float)
            with np.errstate(invalid="ignore", divide="ignore"):
                flows[symbol] = np.where(quote > 0.0, (2.0 * taker - quote) / quote, np.nan)

        # sigma is measured on observations attributed to boundaries strictly before t, so the
        # history is read BEFORE this boundary's own observation is appended.
        multipliers = {name: self._multiplier(name) for name in self._sleeve_names()}
        self._record_proxy_returns(symbols, closes)

        builders = {
            "carry": self._carry,
            "trend": self._trend,
            "lowrisk": self._lowrisk,
            "flow": self._flow,
        }
        combined = np.zeros(len(symbols))
        for name in self._sleeve_names():
            vector = builders[name](symbols, closes, flows, context.funding, context.decision_time)
            self._previous_weights[name] = {
                symbol: float(vector[position])
                for position, symbol in enumerate(symbols)
                if vector[position] != 0.0
            }
            combined += multipliers[name] * vector

        for symbol in symbols:
            close = closes[symbol]
            if close.size:
                self._previous_close[symbol] = float(close[-1])

        if BASELINE_LONG_ONLY:
            combined = np.full(len(symbols), 1.0 / len(symbols))

        if self._boundary % REBALANCE_CADENCE != REBALANCE_PHASE % REBALANCE_CADENCE:
            return None
        if not np.isfinite(combined).all() or float(np.abs(combined).sum()) <= 0.0:
            return None
        return {symbol: float(combined[position]) for position, symbol in enumerate(symbols)}


def build_strategy() -> MultiSleeveEnsemble:
    return MultiSleeveEnsemble()
