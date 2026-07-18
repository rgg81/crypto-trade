"""team-08 strategy — perp participation-commitment cross-sectional book.

Family t08-oi-price-confirmation-v3, confirm-only structure S1g0 (frozen QE SPEC A8).

Mechanism: every 8h price move in the weekly top-40 carries a commitment signature in the
positioning ledger. We ride the cross-section of vol-scaled displacement ONLY on names whose
ledger confirms fresh commitment over the matched window (rising over M candles); unconfirmed
names stand aside. One frozen config, no options, no tuning.

Pipeline (order fixed): clean OI -> vol-scaled L-candle displacement + M-candle log-OI change
-> eligibility-gated centered rank, kept only where the ledger rises -> per-row name-count
guard -> abs-sum normalize -> EMA smooth -> raw signed weights.

PURE, DETERMINISTIC, PAST-ONLY. Symbols derive from the close-panel columns at runtime; no
file/network access, no randomness. Every row is computable from data at or before that row
(rolling / shift / ewm are all causal); aux rows of candle t are same-bar info at t and are
NOT shifted here — the evaluator owns the decision lag.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

L = 18          # displacement lookback (candles, ~6d)
M = 18          # commitment-change (log-OI) window (candles, matched to L)
H = 2.0         # EMA halflife (candles) — turnover control on a slow signal
MIN_NAMES = 10  # per-row minimum scored names; thinner rows are held flat
VOL_WIN = 42    # trailing window for the 1-candle-return volatility (~14d)
VOL_MINP = 21   # min periods for the volatility window
CLIP = 3.0      # winsor clip on the sigma-scaled displacement


def build_raw_weights(pn: dict, aux: dict) -> pd.DataFrame:
    """Raw signed weights (candle-index x symbol-columns; NaN-free, 0.0 == flat)."""
    close = pn["close"]                       # derive the symbol set from THIS panel only
    idx = close.index
    cols = close.columns

    # aux panels reindexed onto the close grid: widening-safe (unseen names -> NaN/False, flat)
    elig = aux["eligibility"].reindex(index=idx, columns=cols).fillna(False).astype(bool)
    oi_r = aux["oi"].reindex(index=idx, columns=cols)
    oi = oi_r.where(oi_r > 0)                 # non-positive / missing OI -> NaN (name flat)

    # vol-scaled L-candle displacement (winsorized)
    r1 = close / close.shift(1) - 1.0
    sig = r1.rolling(VOL_WIN, min_periods=VOL_MINP).std()
    retL = close / close.shift(L) - 1.0
    zret = (retL / (sig * np.sqrt(L))).clip(-CLIP, CLIP)

    # M-candle log-OI change — the commitment ledger; NaN propagates to keep names flat
    log_oi = np.log(oi)
    doi = log_oi - log_oi.shift(M)

    # eligibility-gated centered cross-sectional rank of displacement
    s = zret.where(elig & doi.notna())
    rk = s.rank(axis=1)                       # pandas default (average) ranks over valid names
    n = rk.count(axis=1)
    c = rk.sub((n + 1) / 2.0, axis=0)         # center at (n+1)/2

    # confirm-only gate: keep the rank only where the ledger rose (doi > 0); else 0
    gate = (doi > 0).astype(float)            # NaN -> False -> 0.0
    score = c * gate

    # per-row name-count guard: thin rows (also the 1-name pre-coverage era) go fully flat
    guard = pd.DataFrame(
        np.repeat((n >= MIN_NAMES).to_numpy()[:, None], score.shape[1], axis=1),
        index=score.index,
        columns=score.columns,
    )
    score = score.where(guard)

    # abs-sum normalize, then EMA smooth over the 0-filled panel
    den = score.abs().sum(axis=1).replace(0.0, np.nan)
    w = score.div(den, axis=0).fillna(0.0)
    w = w.ewm(halflife=H, adjust=True).mean()
    return w
