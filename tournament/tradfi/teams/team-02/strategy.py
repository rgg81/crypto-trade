"""team-02 strategy — t02-anchor-discount-contrarian-v1.

Long-horizon contrarian on the 52-week-high anchor: LONG names trading at a deep
discount to their trailing 252-day high, SHORT names at/near the anchor. Mechanism:
overreaction + systematic dip-buying flow in retail-heavy US mega-cap perps
(De Bondt-Thaler long-horizon reversal, anchored on the trailing high rather than a
past-return window). This is the pivoted family (single team pivot spent) — the sign is
the empirical IS finding documented in research_brief.md PART B/C, not the original
George-Hwang direction (which was falsified, PART A/B).

This module implements EXACTLY research_brief.md PART D.2 — no research choices are made
here. The QE (this file) makes no research decisions; every parameter and every transform
step is fixed by the frozen spec.

Purity / determinism contract (CHARTER §7):
  - Pure, deterministic function of (pn, aux); no file reads, no network, no subprocess,
    no wall-clock, no unseeded randomness.
  - There is NO randomness in this strategy: it is deterministic pure pandas. `aux['seed']`
    is therefore UNUSED (stated explicitly here for the Critic). `aux['vix']` and
    `aux['sector_map']` are also unused; only `pn['close']` and `pn['high']` are read.
  - Past-only: every row's value is computable from bars at or before that row. All ops
    are trailing (rolling / ewm / shift) with fixed windows; no full-sample statistic and
    no forward-looking transform appears anywhere.
  - The ENGINE owns everything downstream (gross=1 normalisation, |w_i|<=0.10, |net|<=0.25,
    the .shift(1) decision lag, 6 bps/side cost on |Δw|, 15% vol-target). We emit RAW
    signed rows only — never normalise, cap, lag, or scale here.
"""

from __future__ import annotations

import pandas as pd

# Frozen parameters (research_brief.md PART D.2 / D.4). No sweeping, no overrides.
_L = 252  # anchor window: trailing 252 US trading days (~52 weeks)
_M = 126  # history floor: >= 126 non-NaN highs required in the window, else flat
_SKIP = 21  # PH lagged 21 panel rows (~1 month): month-old anchor distance
_H = 42.0  # EWM halflife (panel rows) for temporal smoothing of the signal
_SIGN = -1.0  # reversed sign: long deep-discount, short near-anchor (pivoted family)


def build_raw_weights(pn: dict[str, pd.DataFrame], aux: dict) -> pd.DataFrame:
    """Raw signed weights for the anchor-discount contrarian book (NaN = flat).

    Parameters
    ----------
    pn : dict of {'open','high','low','close','volume'} -> DataFrame (dates x tickers).
        Only 'close' and 'high' are read. Ragged starts, never forward-filled.
    aux : dict with keys 'vix', 'sector_map', 'seed'. ALL UNUSED (see module docstring;
        the strategy is deterministic pure pandas — `aux['seed']` drives no randomness).

    Returns
    -------
    DataFrame with the same index/columns as ``pn['close']``. NaN entries are flat.
    """
    del aux  # unused — no RNG, no VIX, no sector map (documented for the Critic)

    close = pn["close"]
    high = pn["high"]

    # 1. Anchor: rolling max of highs (ignores NaN bars; needs >= 126 non-NaN highs / 252).
    anchor = high.rolling(window=_L, min_periods=_M).max()

    # 2. Proximity ratio in (0, 1]; NaN when close is NaN or the anchor is NaN.
    ph0 = (close / anchor).where(close.notna())

    # 3. Skip: shift the proximity by 21 PANEL ROWS (month-old anchor distance), but never
    #    a signal for a name without a current bar (re-mask on today's close).
    ph = ph0.shift(_SKIP).where(close.notna())

    # 4. Cross-sectional percentile rank (ties: pandas default 'average'; NaN PH -> NaN rank).
    r = ph.rank(axis=1, pct=True)

    # 5. Row-demean for an exactly dollar-neutral raw book.
    c = r.sub(r.mean(axis=1), axis=0)

    # 6. Reversed sign — the pivoted family's defining direction.
    s = _SIGN * c

    # 7. Temporal smoothing: per-name EWM over time on the panel as-is.
    s = s.ewm(halflife=_H, adjust=True, ignore_na=False, min_periods=1).mean()

    # 8. Final mask: flat whenever the step-3 PH is NaN (the EWM never bridges a missing
    #    current bar into a live position).
    raw = s.where(ph.notna())

    # 9. Same index/columns as pn['close']; NaN = flat. Engine owns all downstream steps.
    return raw
