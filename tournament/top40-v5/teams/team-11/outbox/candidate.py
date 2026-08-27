"""team-11 discovery candidate — participant mix via average trade size.

This is the primary expression of the preregistered thesis (THESIS.md §1.5) at the central
setting of the declared parameter surface (§4.1). Nothing clever is attempted here: the point
of the discovery trial is a baseline whose every moving part can be diagnosed from one feedback
packet.

    S_t   = quote_volume_t / trade_count_t              average USD notional per print
    Z_t   = winsor( trailing z-score of log S_t , 3 )   within-asset participant mix
    OFI_t = 2 * taker_buy_quote_volume_t / quote_volume_t - 1        signed taker flow
    signal_t = mean_k(OFI) * mean_k(Z)                  sign pre-committed positive

Both Z and OFI are within-asset and unit-free, so the book carries no level of S anywhere —
which is the whole point (§4.3, failure mode #3). The signature property of the mechanism is
that when average trade size sits at its own trailing median the position is zero no matter
how large volume is; a volume proxy cannot have that property.

Declared settings used, all central values of §4.1:
    knob 1 normalisation   = trailing z-score
    knob 2 window W        = 90 bars (30 days)
    knob 3 smoothing k     = 3 bars (1 day), applied to both Z and OFI
    knob 4 contrast        = Z = normalize_W(log S)
    knob 5 cross-section   = time-series, own-asset only (no cross-sectional demeaning)

No volatility targeting anywhere: the signal emits a unitless conviction and the organizer's
common ex-ante risk unit does all scaling. The caps applied below are the contract's exposure
constraints, not a risk target.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# --- declared parameter surface (THESIS.md §4.1), at its central setting ---------------
_WINDOW = 90            # knob 2: trailing window for the z-score, in 8h bars (30 days)
_SMOOTH = 3             # knob 3: smoothing of both Z and OFI, in 8h bars (1 day)

# --- fixed by preregistration (THESIS.md §4.3), not knobs -----------------------------
_WARMUP = 30            # hygiene: ignore the first 30 bars after an asset's first observation
_WINSOR = 3.0           # position map is clipped linear at 3 SD; |OFI| <= 1 bounds the product

# --- exposure constraints owned by the contract, not by the thesis --------------------
_MAX_WEIGHT = 0.10      # per-symbol
_MAX_NET = 0.25         # absolute net
_TARGET_GROSS = 1.0     # sum of absolute weights

_REQUIRED_COLUMNS = ("quote_volume", "trade_count", "taker_buy_quote_volume")


def _usable_history(frame):
    """Return ``(log_size, ofi)`` for one symbol's usable history, or ``None``.

    Applies the preregistered hygiene rule: skip the first ``_WARMUP`` bars after the asset's
    first observation, then drop any bar with no trades or no quote volume. Both outputs are
    ordered oldest to newest and aligned to the same surviving bars.
    """
    if frame is None or len(frame) <= _WARMUP:
        return None
    columns = frame.columns
    for name in _REQUIRED_COLUMNS:
        if name not in columns:
            return None

    tail = frame.iloc[_WARMUP:]
    quote = pd.to_numeric(tail["quote_volume"], errors="coerce").to_numpy(dtype=float)
    trades = pd.to_numeric(tail["trade_count"], errors="coerce").to_numpy(dtype=float)
    taker_buy = pd.to_numeric(tail["taker_buy_quote_volume"], errors="coerce").to_numpy(dtype=float)

    live = (
        np.isfinite(quote)
        & np.isfinite(trades)
        & np.isfinite(taker_buy)
        & (quote > 0.0)
        & (trades > 0.0)
    )
    if not live.any():
        return None
    quote, trades, taker_buy = quote[live], trades[live], taker_buy[live]

    log_size = np.log(quote / trades)
    ofi = np.clip(2.0 * (taker_buy / quote) - 1.0, -1.0, 1.0)
    return log_size, ofi


def _trailing_z(series, end, window):
    """Winsorised z-score of ``series[end - 1]`` against the ``window`` bars ending at ``end``."""
    sample = series[end - window:end]
    scale = float(sample.std(ddof=1))
    if not np.isfinite(scale) or scale <= 0.0:
        return None
    score = (float(series[end - 1]) - float(sample.mean())) / scale
    if not np.isfinite(score):
        return None
    return float(np.clip(score, -_WINSOR, _WINSOR))


def _conviction(log_size, ofi, window, smooth):
    """Signed conviction ``mean_k(OFI) * mean_k(Z)`` at the latest bar, or ``None``."""
    count = log_size.size
    if count < window + smooth - 1:
        return None

    total = 0.0
    for lag in range(smooth):
        score = _trailing_z(log_size, count - lag, window)
        if score is None:
            return None
        total += score
    mix = total / smooth

    flow = float(np.mean(ofi[count - smooth:]))
    if not np.isfinite(flow):
        return None

    # |flow| <= 1 and |mix| <= _WINSOR, so the product is already inside the +/-3 clip.
    return flow * mix


def _cap_net(weights):
    """Scale down the dominant side until absolute net exposure respects the contract."""
    net = float(weights.sum())
    if not np.isfinite(net) or abs(net) <= _MAX_NET:
        return weights

    longs = weights > 0.0
    shorts = weights < 0.0
    long_gross = float(weights[longs].sum())
    short_gross = float(-weights[shorts].sum())

    capped = weights.copy()
    if net > _MAX_NET and long_gross > 0.0:
        capped[longs] = weights[longs] * ((_MAX_NET + short_gross) / long_gross)
    elif net < -_MAX_NET and short_gross > 0.0:
        capped[shorts] = weights[shorts] * ((_MAX_NET + long_gross) / short_gross)
    return capped


def _to_book(symbols, convictions):
    """Normalise convictions to a gross-one book, then apply the contract's exposure caps."""
    raw = np.asarray(convictions, dtype=float)
    gross = float(np.abs(raw).sum())
    if not np.isfinite(gross) or gross <= 0.0:
        return {}

    weights = _cap_net(np.clip(raw / gross * _TARGET_GROSS, -_MAX_WEIGHT, _MAX_WEIGHT))
    return {
        symbol: float(weight)
        for symbol, weight in zip(symbols, weights)
        if np.isfinite(weight)
    }


class ParticipantMixStrategy:
    """Signed taker flow conditioned on within-asset participant mix.

    Holds no state between decisions: every quantity is recomputed from the past-only rows in
    the context that is handed to it.
    """

    def target_weights(self, context, *, seed):
        del seed  # nothing here is stochastic; the book is a pure function of the context

        bars = context.bars
        symbols = []
        convictions = []

        for symbol in context.eligible_symbols:
            if symbol not in bars:
                continue
            history = _usable_history(bars[symbol])
            if history is None:
                continue
            signal = _conviction(history[0], history[1], _WINDOW, _SMOOTH)
            if signal is None or not np.isfinite(signal):
                continue
            symbols.append(symbol)
            convictions.append(signal)

        if not symbols:
            return {}
        return _to_book(symbols, convictions)


def build_strategy():
    return ParticipantMixStrategy()
