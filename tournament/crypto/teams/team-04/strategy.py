"""team-04 — t04-ts-trend-v2: per-name multi-horizon time-series log-price trend.

Each name's raw weight is computed from its OWN close history only — direction is the sign of
a vol-normalized multi-horizon trend "t-stat", conviction is the (clipped) trend magnitude
relative to the name's own volatility, and inverse-vol sizing risk-parities across names.
There is NO cross-sectional ranking, demeaning, residualization, or peer comparison anywhere:
this is a pure TIME-SERIES mechanism. Cross-sectional interaction enters ONLY through the
organizer's book construction (eligibility mask + gross-normalization + caps), which is
outside this signal and owned by the engine.

This module implements ``research_brief.md`` section 8 (the frozen QE SPEC) EXACTLY:
    H = (21, 63, 126, 252), transform = clip with Z = 2.0, inverse-vol sizing ON,
    EMA span E = 3, vol window V = 126 (min_periods 63), close panel only.

Contract (CHARTER section 7): PURE, DETERMINISTIC, PAST-ONLY function of its inputs. Reads
``pn["close"]`` ONLY. ``aux`` is accepted but intentionally UNUSED — no eligibility applied
(the engine masks), no randomness (``aux["seed"]`` intentionally unused). Symbols are derived
from ``pn["close"].columns`` at runtime; names and counts are never hard-coded. Emits RAW
signed weights only; NaN = flat. Does NOT normalize, cap, lag, mask, fillna, or scale — all
of that is engine-owned. Imports: numpy, pandas only.

Pandas defaults are load-bearing and left explicit-by-default: rolling std ddof=1;
ewm adjust=True, ignore_na=False.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Frozen QE-SPEC parameters (research_brief.md section 8; ledger e10/e11).
_HORIZONS = (21, 63, 126, 252)  # candles = 7d, 21d, 42d, 84d on the 8h grid
_CLIP_Z = 2.0                   # conviction saturation of the vol-normalized trend
_VOL_WIN = 126                  # per-name volatility window V
_VOL_MIN_PERIODS = 63           # V // 2
_VOL_FLOOR = 1e-6               # degenerate / stale series -> NaN (flat)
_EMA_SPAN = 3                   # turnover-smoothing EMA span E


def build_raw_weights(pn: dict, aux: dict) -> pd.DataFrame:  # noqa: ARG001 (aux unused by spec)
    """Raw signed weights, candle-index x symbol-columns (NaN = flat).

    ``aux`` is accepted to honor the interface but is intentionally unread: this strategy has
    no randomness and applies no eligibility (both engine-owned). Every step below is applied
    column-wise and is strictly backward-looking, so the output is past-only and column-set
    agnostic (adding columns cannot change existing columns' weights).
    """
    # 1. Close panel only, as float. DatetimeIndex x symbol columns.
    C = pn["close"].astype(float)
    # 2. Log price. NaN where C is NaN; NEVER ffill / impute.
    lp = np.log(C)
    # 3. 8h log returns; NaN across listing gaps.
    r = lp.diff(1)
    # 4. Per-name own volatility (rolling std, ddof=1 default).
    vol = r.rolling(_VOL_WIN, min_periods=_VOL_MIN_PERIODS).std()
    # 5. Degenerate / stale series -> NaN (flat). (0-vol constant prices vanish here.)
    vol = vol.where(vol > _VOL_FLOOR)

    # 6. Per-horizon vol-normalized trend t-stat, clipped to +/-Z. NaN horizon -> abstains.
    # 7. NaN-skipping blend: mean over the AVAILABLE horizons only. A cell is NaN only when
    #    ALL four horizons are NaN. (A plain (a+b+c+d)/4 would wrongly flatten young names
    #    that only have the short horizons.)
    num = None
    cnt = None
    for L in _HORIZONS:
        s_L = ((lp - lp.shift(L)) / (vol * np.sqrt(L))).clip(-_CLIP_Z, _CLIP_Z)
        filled = s_L.fillna(0.0)
        present = s_L.notna()
        num = filled if num is None else num + filled
        cnt = present if cnt is None else cnt + present
    sig = num / cnt.replace(0, np.nan)

    # 8. Inverse-vol sizing (risk parity across names).
    w = sig / vol
    # 9. Turnover-smoothing EMA (pandas defaults: adjust=True, ignore_na=False).
    w = w.ewm(span=_EMA_SPAN, min_periods=1).mean()
    # 10. The EMA must not resurrect flat/NaN cells: re-mask to the signal's support.
    w = w.where(sig.notna())
    # 11. Same index and columns as pn["close"]. No normalize / cap / lag / mask / fillna.
    return w
