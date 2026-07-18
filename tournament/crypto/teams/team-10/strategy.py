"""team-10 strategy — CWMOM: confirmation-weighted cross-sectional momentum.

Mechanism: follow volume-backed cross-sectional moves, weighting each move by how much
participation it brought relative to the name's OWN pre-move baseline. The confirmation
term acts as a strength gate in [0, 1] on the momentum core: it never flips a name's sign,
it only shrinks the weight of moves that arrived on thin participation.

Pure, deterministic, past-only function of its inputs. Consumes ONLY pn['close'],
pn['quote_volume'], and aux['eligibility']. No other panel is touched; aux['seed'] is
unused (the signal carries no randomness). Symbols are derived from the panel columns at
runtime — no names or column counts are hard-coded, so it is column-set agnostic.

Frozen configuration (QE specification, section 8):
    L = 12   move window (12 x 8h = 3 days)
    B = 90   own pre-move participation baseline (30 days)
    H = 3    EMA smoothing span (turnover control)
    K = 1.0  confirmation-gate offset -> gate = (C + K) / (1 + K) in [0, 1]
"""

from __future__ import annotations

import numpy as np
import pandas as pd

L = 12
B = 90
H = 3
K = 1.0
EPS = 1e-12


def build_raw_weights(pn: dict[str, pd.DataFrame], aux: dict) -> pd.DataFrame:
    """Raw signed weights (candle-index x symbol-columns). NaN/ineligible -> 0 (flat).

    Exact order of operations (all rolling stats past-only; do NOT reorder):
      1. move over the last L candles,
      2. participation vs the own pre-move baseline (baseline excludes the move window),
      3. cross-sectional centered percentile ranks over ELIGIBLE names only,
      4. confirmation gate in [0, 1],
      5. mask -> fillna(0) -> per-column EMA (adjust=False).
    """
    close = pn["close"]
    qv = pn["quote_volume"]
    elig = aux["eligibility"].astype(bool)

    # 1. Move (L x 8h candles).
    ret_L = close / close.shift(L) - 1.0

    # 2. Participation vs own PRE-MOVE baseline (baseline excludes the move window).
    ma_L = qv.rolling(L, min_periods=L).mean()
    ma_B = qv.rolling(B, min_periods=B).mean().shift(L)
    conf = np.log(ma_L.clip(lower=EPS)) - np.log(ma_B.clip(lower=EPS))
    conf = conf.where((ma_L > 0) & (ma_B > 0))  # zero/NaN volume -> NaN

    # 3. Cross-sectional centered percentile ranks over eligible names only (NaN stays NaN).
    C = 2.0 * (conf.where(elig).rank(axis=1, pct=True) - 0.5)   # confirmation in [-1, +1]
    M = 2.0 * (ret_L.where(elig).rank(axis=1, pct=True) - 0.5)  # momentum rank in [-1, +1]

    # 4. Confirmation gate (K = 1: gate in [0, 1] — thin-extreme weight -> 0, never sign-flips).
    G = (C + K) / (1.0 + K)

    # 5. Signal, NaN policy, smoothing (exact order: mask -> fillna -> EMA).
    S = (M * G).where(elig).fillna(0.0)
    S = S.ewm(span=H, adjust=False).mean()  # per-column EMA, adjust=False
    return S
