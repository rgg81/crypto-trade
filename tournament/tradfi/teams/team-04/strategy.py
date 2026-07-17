"""team-04 strategy — t04-xs-momentum-12-1-v1.

Plain 12-1 (skip=0) cross-sectional momentum with rank-hysteresis membership.

    build_raw_weights(pn, aux) -> pd.DataFrame   # dates x tickers, raw signed weights

PURE, DETERMINISTIC, PAST-ONLY function of ``pn['close']`` only (aux unused; the
strategy is deterministic, rank ties broken by panel column order via method="first").
No file I/O, no network, no subprocess, no randomness. The engine owns gross-normalisation,
the 0.10/0.25 caps, the ``.shift(1)`` decision lag, taker costs, and vol-targeting — none of
those are pre-applied here.

Binding spec: ``research_brief.md`` §2 (exact; no degrees of freedom). Reference translated
(NOT imported): ``out/scratch/scratch_explore_f.py :: hysteresis_weights(252, 0, 0.20, 0.35)``.
The two lookback operators are ``close.ffill()`` and ``.shift(252)`` (both causal), and the
membership loop's state at row t is a function only of rows <= t — so truncated-replay,
future-corruption, and same-bar equivalence hold by construction.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# --- Fixed parameters (research_brief.md §2 table; no degrees of freedom) --------------------
FORMATION = 252   # trailing formation window in panel rows (~12 months)
SKIP = 0          # classic 1-month skip FALSIFIED on this panel (exp-010 / exp-024)
Q_IN = 0.20       # fresh-entry tail fraction (long top 20% / short bottom 20%)
Q_STAY = 0.35     # retention (stay) band fraction — hysteresis overlay
MIN_SIDE = 5      # minimum members per side (charter breadth floor)


def build_raw_weights(pn: dict, aux: dict) -> pd.DataFrame:  # noqa: ARG001 — aux intentionally unused
    close = pn["close"]

    # Causal forward-fill: propagates last real bar forward, never looks ahead.
    c = close.ffill()

    # 1. Signal — trailing FORMATION-row return, skip=SKIP.
    #    mom[t, i] = C[t-SKIP, i] / C[t-SKIP-FORMATION, i] - 1  (SKIP=0 -> C / C.shift(252) - 1)
    sig = c.shift(SKIP) / c.shift(SKIP + FORMATION) - 1.0

    # 2. Eligibility — a real bar today AND a finite momentum value.
    elig = close.notna() & np.isfinite(sig)

    # 3. Rank — ascending among eligible names (rank 1 = worst); ties by column order.
    ranks = sig.where(elig).rank(axis=1, method="first")
    n = ranks.notna().sum(axis=1).astype(float)  # N[t] = number of eligible names

    r = ranks.to_numpy()
    nn = n.to_numpy()
    n_rows, n_cols = r.shape
    w = np.zeros((n_rows, n_cols), dtype=float)

    # 4. Hysteresis membership — stateful causal loop; state = prior day's long/short sets,
    #    both initialised EMPTY at the first panel row.
    long_prev = np.zeros(n_cols, dtype=bool)
    short_prev = np.zeros(n_cols, dtype=bool)
    for t in range(n_rows):
        n_t = nn[t]
        n_in = np.floor(Q_IN * n_t)
        if n_in < MIN_SIDE or n_t <= 0:
            # Row is FLAT; both member sets reset to empty.
            long_prev = np.zeros(n_cols, dtype=bool)
            short_prev = np.zeros(n_cols, dtype=bool)
            continue
        n_stay = np.floor(Q_STAY * n_t)
        rt = r[t]
        valid = np.isfinite(rt)  # names with a real rank today (no bar -> drops out)
        lng = (valid & (rt > n_t - n_in)) | (long_prev & valid & (rt > n_t - n_stay))
        sht = (valid & (rt <= n_in)) | (short_prev & valid & (rt <= n_stay))
        clash = lng & sht  # a name qualifying for BOTH sides is removed from both
        lng = lng & ~clash
        sht = sht & ~clash
        n_long = int(lng.sum())
        n_short = int(sht.sum())
        if n_long >= MIN_SIDE and n_short >= MIN_SIDE:
            # 5. Weights — equal-weight tails: +1/n_long long, -1/n_short short.
            w[t, lng] = 1.0 / n_long
            w[t, sht] = -1.0 / n_short
            long_prev = lng
            short_prev = sht
        else:
            # Either side below the floor -> FLAT; reset both member sets.
            long_prev = np.zeros(n_cols, dtype=bool)
            short_prev = np.zeros(n_cols, dtype=bool)

    return pd.DataFrame(w, index=close.index, columns=close.columns)
