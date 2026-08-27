"""team-10 — taker-flow pressure, discovery baseline.

Direct expression of the mandate: the exchange-reported aggressor imbalance,
accumulated over one day, standardized against its own trailing distribution,
demeaned across the cross-section, and mapped linearly into a two-sided book.

Configuration is the ``C = none`` corner of the preregistered parameter surface
(THESIS.md 5.1) with the sign preset by mechanism, not estimated:

    N = ratio      (2*taker_buy_quote - quote_volume) / quote_volume
    L = 3          accumulation window, bars  (1 day = all three funding stamps)
    W = 90         standardization window, bars  (~30 days)
    C = none       no conditioner
    X = ts z + cross-sectional demean

Sign: follow the flow (positive). Source: Kim & Hansen 2026, the only
horizon-matched published result, which is the preset for ``C = none`` in
THESIS.md 3. If the data prefer the opposite sign that falsifies the thesis;
it is not a knob to flip.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

# --- searched knobs, at their declared discovery levels (THESIS.md 5.1) ---
_L = 3          # flow accumulation window, in 8h bars
_W = 90         # trailing standardization window, in 8h bars

# --- fixed, declared and not searched (THESIS.md 5.3) --------------------
_WINSOR = 3.0   # standardized-signal winsorization, 5.3.3
_SIGN = 1.0     # preset for C = none: follow the flow, 3

# --- contract limits from RESEARCH-BRIEF.md ------------------------------
_GROSS = 1.0    # sum |w| <= 1.0
_CAP = 0.10     # per-symbol |w| <= 0.10
_NET = 0.15     # own working limit, inside the 0.25 contract limit

# --- structural floors, not fitted quantities ----------------------------
_MIN_NAMES = 8  # below this the cross-section is not a portfolio
_CAP_PASSES = 8 # water-filling iterations for the per-symbol cap
_TINY = 1e-12


def _visible(frame: pd.DataFrame, boundary) -> pd.DataFrame:
    """Past-only slice.

    A no-op on well-formed context frames, which already stop at the boundary.
    It exists so the strategy is invariant to rows appended after the decision
    regardless of how the frame was assembled. Falls back to the frame as given
    when the index is positional or the timezones do not compare.
    """
    if isinstance(frame.index, pd.DatetimeIndex) and isinstance(boundary, pd.Timestamp):
        try:
            return frame.loc[:boundary]
        except (TypeError, KeyError, ValueError):
            return frame
    return frame


def _flow_columns(frame: pd.DataFrame):
    """Total traded and taker-buy traded, paired so the ratio is dimensionless.

    Quote terms are preferred. The base pair is an exact fallback rather than a
    different signal: within one bar both express the same aggressor share.
    """
    cols = frame.columns
    if "quote_volume" in cols and "taker_buy_quote_volume" in cols:
        return frame["quote_volume"], frame["taker_buy_quote_volume"]
    if "volume" in cols and "taker_buy_volume" in cols:
        return frame["volume"], frame["taker_buy_volume"]
    return None, None


def _imbalance(frame: pd.DataFrame):
    """Per-bar aggressor imbalance in [-1, +1].

    imb = (2 * taker_buy - total) / total. Positive means takers lifted more
    than they hit, so the maker sector absorbed imb * total of unwanted short
    inventory over the bar. Bars in which nothing traded contribute 0
    (THESIS.md 5.3.8): no interpolation, no forward-fill.
    """
    total, taker = _flow_columns(frame)
    if total is None:
        return None
    q = pd.to_numeric(total, errors="coerce").to_numpy(dtype=float)
    t = pd.to_numeric(taker, errors="coerce").to_numpy(dtype=float)
    out = np.zeros(q.shape[0], dtype=float)
    live = np.isfinite(q) & np.isfinite(t) & (q > 0.0)
    out[live] = (2.0 * t[live] - q[live]) / q[live]
    return np.clip(out, -1.0, 1.0)


def _signal(frame: pd.DataFrame):
    """Winsorized trailing z-score of the L-bar accumulated aggressor imbalance.

    Returns ``None`` when the symbol does not carry a full W-bar standardization
    window, which is the min_periods rule in THESIS.md 5.3.2 rather than a
    liquidity screen.
    """
    imb = _imbalance(frame)
    if imb is None or imb.shape[0] < _W + _L - 1:
        return None
    # acc[k] is the trailing L-bar sum ending at bar k + L - 1.
    acc = np.convolve(imb, np.ones(_L, dtype=float), mode="valid")
    if acc.shape[0] < _W:
        return None
    window = acc[-_W:]
    if not np.all(np.isfinite(window)):
        return None
    sd = float(window.std(ddof=1))
    if not math.isfinite(sd) or sd <= _TINY:
        return None
    z = (float(window[-1]) - float(window.mean())) / sd
    if not math.isfinite(z):
        return None
    return max(-_WINSOR, min(_WINSOR, z))


def _apply_cap(weights):
    """Water-fill the per-symbol cap, redistributing to uncapped names."""
    out = {k: max(-_CAP, min(_CAP, v)) for k, v in weights.items()}
    for _ in range(_CAP_PASSES):
        spill = 0.0
        free = 0.0
        for value in weights.values():
            size = abs(value)
            if size > _CAP:
                spill += size - _CAP
            else:
                free += size
        if spill <= _TINY or free <= _TINY:
            break
        lift = 1.0 + spill / free
        weights = {
            k: (math.copysign(_CAP, v) if abs(v) > _CAP else v * lift)
            for k, v in weights.items()
        }
        out = {k: max(-_CAP, min(_CAP, v)) for k, v in weights.items()}
    return out


def _neutralize(weights):
    """Trim residual net exposure left by the cap. Demeaned scores rarely need it."""
    if not weights:
        return weights
    net = sum(weights.values())
    if abs(net) <= _NET:
        return weights
    shift = net / float(len(weights))
    return {k: max(-_CAP, min(_CAP, v - shift)) for k, v in weights.items()}


def _book(scores):
    """Linear position map: weight proportional to the demeaned signal."""
    mass = sum(abs(v) for v in scores.values())
    if not math.isfinite(mass) or mass <= _TINY:
        return {}
    weights = {k: _GROSS * v / mass for k, v in scores.items()}
    weights = _neutralize(_apply_cap(weights))
    gross = sum(abs(v) for v in weights.values())
    if gross > _GROSS:
        weights = {k: v * (_GROSS / gross) for k, v in weights.items()}
    return {k: float(v) for k, v in weights.items() if abs(v) > 1e-9}


class TakerFlowPressure:
    """Follow the aggressor, cross-sectionally, at the funding-clock horizon."""

    def target_weights(self, context, *, seed):
        symbols = context.eligible_symbols
        if not symbols:
            return {}
        bars = context.bars
        boundary = context.decision_time

        raw = {}
        for symbol in symbols:
            if symbol.startswith("__"):
                continue  # organizer-reserved target metadata, never tradable
            frame = bars.get(symbol)
            if frame is None or len(frame) < _W + _L - 1:
                continue
            score = _signal(_visible(frame, boundary))
            if score is not None:
                raw[symbol] = _SIGN * score

        if len(raw) < _MIN_NAMES:
            return {}

        centre = sum(raw.values()) / float(len(raw))
        return _book({k: v - centre for k, v in raw.items()})


def build_strategy():
    return TakerFlowPressure()
