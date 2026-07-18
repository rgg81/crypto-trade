"""team-07 — family t07-vol-structure-v1 — vol-DYNAMICS cross-section.

Mechanism (as supported by the frozen research): within the volume-ranked top-40 perps,
rank names by SUSTAINED short-vs-long realized-vol elevation (a smoothed expansion ratio) and
go long the persistently vol-EXPANDED tail / short the vol-COMPRESSED tail, cross-sectionally
demeaned every candle. Signal uses klines close + the organizer eligibility mask ONLY; funding
enters exclusively through the engine's native funding P&L.

`build_raw_weights(pn, aux) -> pd.DataFrame` is PURE, DETERMINISTIC, and PAST-ONLY: every row
is computable from data at or before that row. No file I/O, no network, no randomness
(`aux["seed"]` intentionally unused). Symbols are derived from `pn["close"].columns` at runtime
so the strategy is widening-safe (never hard-codes names or column counts).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_raw_weights(pn: dict, aux: dict) -> pd.DataFrame:
    """Raw signed weights: positive on HIGH smoothed vol-expansion (long expansion / short
    compression). NaN -> flat; row-demeaned (row net exactly 0 among ranked names)."""
    C = pn["close"]

    # 1. 8h log returns, per column.
    r = np.log(C).diff()
    # 2-3. short / long realized vol (pandas ddof=1 default). min_periods = max(8, ceil(0.75*W)).
    vol_s = r.rolling(12, min_periods=9).std()
    vol_l = r.rolling(84, min_periods=63).std()
    # 4. expansion ratio; guard the vol_l == 0 degenerate (dead/flat feeds) -> NaN.
    vt = (vol_s / vol_l).replace([np.inf, -np.inf], np.nan)
    # 5. per-name score EMA (kwargs pinned; pandas defaults made explicit).
    sm = vt.ewm(halflife=72, min_periods=1, adjust=True, ignore_na=False).mean()
    # 6. align the organizer mask to the close panel; absent columns -> False -> flat.
    elig = (
        aux["eligibility"]
        .reindex(index=C.index, columns=C.columns)
        .fillna(False)
        .astype(bool)
    )
    # 7. rank among eligible names only.
    masked = sm.where(elig)
    # 8. cross-sectional percentile rank (method="average", ascending=True, na_option="keep").
    p = masked.rank(axis=1, pct=True)
    # 9. row-demean; SIGN: positive weight on high smoothed expansion.
    w = p.sub(p.mean(axis=1), axis=0)
    # 10. NaN -> flat; emit every candle on the full panel index.
    return w.fillna(0.0)
