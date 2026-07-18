"""team-01 — t01-funding-carry-xs-v1 (cross-sectional funding-rate carry).

Frozen QR specification (research_brief.md → QE SPEC). Short the coins the crowd pays to
hold long (persistent positive funding); long the coins shorts pay for (persistent negative
funding); smoothed to low turnover. Raw signed weights ONLY — the engine owns the eligibility
mask, gross-normalisation, caps, decision lag, costs, funding P&L, and vol-targeting.

Order of operations is load-bearing (research_brief.md binding note 1):
    mask -> smooth -> mask -> rank -> vol-divide -> zero-fill -> weight-EWM -> re-mask.

Pure, deterministic, past-only; column-set agnostic; NaN-tolerant. aux['seed'] is
intentionally unused (no randomness). No I/O, no imports beyond numpy/pandas.
"""

import numpy as np
import pandas as pd

HALFLIFE = 2.0        # candles — funding EWM halflife
MIN_FUND_OBS = 2      # min funding observations before a name gets a signal
VOL_WIN = 63          # candles — realized-vol window for inverse-vol sizing
VOL_MIN_PERIODS = 21  # min obs for the vol estimate (younger names stay flat)
WEIGHT_SPAN = 2       # causal EWM span over weight rows (turnover damping)


def build_raw_weights(pn, aux):
    close = pn["close"]
    cols, idx = close.columns, close.index

    # --- defensive alignment (widening-safe; no-op on the real panels) ---
    fund = aux["funding"].reindex(index=idx, columns=cols)
    elig = aux["eligibility"].reindex(index=idx, columns=cols)
    elig = elig.astype("boolean").fillna(False).astype(bool)

    alive = close.notna()          # listed-and-trading mask
    mask = elig & alive            # tradable: in-force top-40 AND alive

    # --- signal: smoothed same-bar funding (past-only: ewm over rows <= t) ---
    fund_m = fund.where(alive)     # funding panel is 0.0-filled where never listed
    sm = fund_m.ewm(halflife=HALFLIFE, min_periods=MIN_FUND_OBS,
                    adjust=True, ignore_na=False).mean()
    sm = sm.where(mask)

    # --- cross-sectional transform: centered percentile rank, negated ---
    r = sm.rank(axis=1, pct=True)            # ascending, average ties, NaN excluded
    w = -(r.sub(r.mean(axis=1), axis=0))     # short high funding, long low/negative

    # --- inverse-vol sizing ---
    vol = close.pct_change(fill_method=None).rolling(
        VOL_WIN, min_periods=VOL_MIN_PERIODS).std(ddof=1)
    w = w.div(vol.replace(0.0, np.nan))
    w = w.replace([np.inf, -np.inf], np.nan)

    # --- mask, flatten NaN, damp turnover, re-mask ---
    w = w.where(mask, 0.0).fillna(0.0)
    w = w.ewm(span=WEIGHT_SPAN, adjust=True, ignore_na=False).mean()
    w = w.where(mask, 0.0)
    return w
