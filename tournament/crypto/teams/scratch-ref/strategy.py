"""scratch-ref — organizer dry-run reference strategy (NOT a competitor; deleted pre-Phase-1).

Plain cross-sectionally-demeaned 28-day momentum, inverse-vol sized. Past-only by
construction. Exists solely to sanity-check the scoring pipeline end-to-end.
"""

import numpy as np


def build_raw_weights(pn, aux):
    close = pn["close"]
    mom = close / close.shift(84) - 1.0  # 28d trailing return
    rvol = close.pct_change().rolling(84).std()
    sig = mom.sub(mom.mean(axis=1), axis=0)  # cross-sectional demean -> ~dollar-neutral
    raw = sig / rvol.replace(0.0, np.nan)
    return raw.fillna(0.0)
