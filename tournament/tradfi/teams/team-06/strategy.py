"""team-06 strategy — t06-vix-regime-books-v1 (family #7 pivot, COMBO B / exp-038).

VIX-conditional regime books. Calm state -> cross-sectional 12-1 momentum book;
stressed state -> short-horizon (10-day) reversal book. The regime state is a trailing
504-day VIX percentile driving a hard hysteresis switch (stressed when pct >= 0.85, calm
when pct <= 0.70, carry the previous state in between, start calm). The composite is
(1 - s) * w_mom + s * w_rev, then EMA-smoothed at halflife 3 days.

The alpha claim is the STATE-CONDITIONALITY itself: the short-horizon reversal premium
concentrates in high-VIX states (liquidity-provision snap-backs) while cross-sectional
momentum earns its premium in calm states and crashes in high-VIX rebounds. Switching the
book composition deploys each ingredient only where its premium exists.

Contract (CHARTER section 7): pure, deterministic, PAST-ONLY function of its inputs. Uses
ONLY pn['close'] and aux['vix']. No file reads, no network, no wall clock, no randomness
(aux['seed'] is unused). Tickers are derived from the panel columns at runtime. Returns RAW
signed weights only; the engine owns gross-normalisation, the 0.10/0.25 caps, the .shift(1)
decision lag, taker costs, and vol-targeting. Every parameter is fixed by the QR spec
(research_brief.md section P7); nothing here is a hidden research choice.

Causality / truncation-safety: every per-row output is computable from bars at or before that
row. Momentum/reversal signals are backward shifts; the cross-sectional transform is strictly
row-wise; the VIX percentile uses a trailing window ending at the row; the hysteresis state
machine iterates from row 0 with an initial calm state; the EMA is causal. Truncating or
corrupting future bars cannot change any output at or before the cut.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# --- fixed parameters (research_brief.md section P7 — COMBO B / exp-038) -------------------------
PCT_WIN = 504  # trailing VIX-percentile window (rows)
MIN_PCT_OBS = 252  # min finite VIX obs inside the window before a state is defined
HI = 0.85  # hysteresis: switch to stressed when pct >= HI
LO = 0.70  # hysteresis: switch to calm when pct <= LO
MOM_SKIP = 21  # momentum book: numerator lag  (close.shift(SKIP))
MOM_FORM = 252  # momentum book: denominator lag (close.shift(FORM))
REV_WIN = 10  # reversal book lookback
WINS = 3.0  # cross-sectional winsorization clip
MIN_NAMES = 10  # min finite cross-sectional names per row (else the row is flat)
EMA_HL = 3.0  # composite EMA halflife (rows)


def _vix_state(vix: pd.Series, index: pd.DatetimeIndex) -> pd.Series:
    """Regime state s in {0=calm, 1=stressed} as a pure causal function of the VIX history.

    pct[t] = fraction of the trailing PCT_WIN-row window of forward-filled VIX (finite values
    only) that is <= vix[t], defined only when the window holds >= MIN_PCT_OBS finite values
    and vix[t] is finite. A hard hysteresis switch then iterates rows in order from an initial
    calm state: stressed once pct >= HI, calm once pct <= LO, otherwise carry the prior state.
    Row t depends solely on rows <= t, so the series is start-anchored and truncation-safe.
    """
    v = vix.reindex(index).ffill()
    x = v.to_numpy(dtype=float)
    n = len(index)

    pct = np.full(n, np.nan)
    for t in range(n):
        w0 = max(0, t - PCT_WIN + 1)
        seg = x[w0 : t + 1]
        seg = seg[np.isfinite(seg)]
        if len(seg) >= MIN_PCT_OBS and np.isfinite(x[t]):
            pct[t] = float((seg <= x[t]).mean())

    s = np.zeros(n)
    cur = 0.0
    for t in range(n):
        if np.isfinite(pct[t]):
            if pct[t] >= HI:
                cur = 1.0
            elif pct[t] <= LO:
                cur = 0.0
        s[t] = cur
    return pd.Series(s, index=index)


def _xz_book(sig: pd.DataFrame, *, negate: bool) -> pd.DataFrame:
    """Cross-sectional z -> winsorize -> re-demean -> (negate) -> row gross-normalise.

    Every step is strictly row-wise (axis=1), so a row's book is a function of that row's
    cross-section only. Rows with fewer than MIN_NAMES finite names are set flat; a zero
    gross row is flat. Returns a NaN-free panel (flat cells are 0.0).
    """
    mu = sig.mean(axis=1)
    sd = sig.std(axis=1, ddof=1)
    z = sig.sub(mu, axis=0).div(sd.replace(0.0, np.nan), axis=0)
    z = z.clip(-WINS, WINS)
    z = z.sub(z.mean(axis=1), axis=0)
    if negate:
        z = -z
    n_valid = z.notna().sum(axis=1)
    z = z.where(n_valid.ge(MIN_NAMES), other=np.nan)
    g = z.abs().sum(axis=1).replace(0.0, np.nan)
    return z.div(g, axis=0).fillna(0.0)


def build_raw_weights(pn: dict, aux: dict) -> pd.DataFrame:
    """Raw signed weights (dates x tickers). See module docstring for the full contract."""
    close = pn["close"].astype(float)

    # Calm book — cross-sectional 12-1 momentum.
    mom_sig = close.shift(MOM_SKIP) / close.shift(MOM_FORM) - 1.0
    w_mom = _xz_book(mom_sig, negate=False)

    # Stressed book — short-horizon reversal (negated cross-sectional return).
    rev_sig = close / close.shift(REV_WIN) - 1.0
    w_rev = _xz_book(rev_sig, negate=True)

    # Regime blend + causal EMA smoothing.
    s = _vix_state(aux["vix"], close.index)
    raw = w_mom.mul(1.0 - s, axis=0) + w_rev.mul(s, axis=0)
    raw = raw.ewm(halflife=EMA_HL, min_periods=1).mean()
    return raw
