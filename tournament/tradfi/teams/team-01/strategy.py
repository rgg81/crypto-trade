"""team-01 submission — t01-residual-momentum-v1 (residual / beta-stripped momentum).

`build_raw_weights(pn, aux)` is a PURE, DETERMINISTIC, PAST-ONLY function of its inputs.
It uses ONLY `pn['close']` and `aux['sector_map']`; `aux['vix']` and `aux['seed']` are
unused (the strategy carries no randomness). The engine owns gross-normalisation, the
|w_i|<=0.10 / |Sigma w|<=0.25 caps, the `.shift(1)` decision lag, costs, and vol-targeting;
this function emits RAW signed weights only (NaN = flat).

This is the exact, parameter-frozen implementation of the QR's research brief §3
(`research_brief.md`), which is the working reference `scratch_common.build()` evaluated with
the exp-013 `CHOSEN` config. Every parameter below is fixed by the brief — no research choices
are made here.

Pipeline (all operators causal: rolling windows end at t, `.shift(+skip)` reaches into the
PAST, `.ewm` is forward-recursive, ranks/means are row-wise cross-sectional):
  1. simple daily returns from close
  2. equal-weight market proxy (row-wise skipna mean)
  3. market residual  e  = ret - beta(63d) * mkt          (no alpha subtraction)
  4. sector residual  e2 = e   - gamma(63d) * self-excluded EW sector-residual basket
     (buckets with <3 members untouched; undefined cells fall back to the market residual)
  5. residual momentum over L=231 days, min_periods=208, shifted past the 21d reversal zone
  6. 50/50 blend of pct-rank(idiosyncratic IR) and pct-rank(residual sum)
  7. cross-sectional pct-rank -> dollar-neutral (net-zero) weights
  8. EMA smoothing (halflife 10) on 0-filled weights
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from neutralize import dollar_neutralize  # approved substrate module (charter §5)

# ---- frozen parameters (research_brief.md §2; provenance in experiments.jsonl) ----------------
_BETA_WIN = 63       # beta/gamma estimation window (min_periods = win)
_FORM = 252          # formation lookback (canonical 12-month)
_SKIP = 21           # skip / reversal zone
_L = _FORM - _SKIP   # momentum window length = 231
_MP = int(round(0.9 * _L))  # rolling min_periods = round(0.9 * 231) = 208
_HALFLIFE = 10       # EMA smoothing halflife


def _daily_returns(close: pd.DataFrame) -> pd.DataFrame:
    """Simple daily returns; NaN propagates (no forward-fill)."""
    return close / close.shift(1) - 1.0


def _rolling_beta(ret: pd.DataFrame, mkt: pd.Series, win: int) -> pd.DataFrame:
    """Past-only rolling beta of each name's returns to `mkt` (window ends at current bar)."""
    var = mkt.rolling(win, min_periods=win).var()
    out = {c: ret[c].rolling(win, min_periods=win).cov(mkt) for c in ret.columns}
    return pd.DataFrame(out, index=ret.index).div(var, axis=0)


def _market_residual(ret: pd.DataFrame, win: int) -> pd.DataFrame:
    """e_t = r_t - beta_t * m_t, with m_t the equal-weight (skipna) cross-sectional mean."""
    mkt = ret.mean(axis=1)
    beta = _rolling_beta(ret, mkt, win)
    return ret - beta.mul(mkt, axis=0)


def _sector_residual(e: pd.DataFrame, sector_map: dict, win: int) -> pd.DataFrame:
    """Strip each name's loading on its self-excluded EW sector-residual basket.

    Members of a bucket are processed independently off the ORIGINAL market-residual block
    (not sequentially). Buckets with <3 members are left untouched. Undefined sector-stage
    cells fall back to the market-only residual."""
    e2 = e.copy()
    sectors: dict[str, list[str]] = {}
    for c in e.columns:
        sectors.setdefault(sector_map.get(c, "Unknown"), []).append(c)
    for cols in sectors.values():
        if len(cols) < 3:
            continue
        block = e[cols]
        n = block.notna().sum(axis=1)
        s_sum = block.sum(axis=1)
        for c in cols:
            n_ex = (n - block[c].notna().astype(int)).replace(0, np.nan)
            s_ex = (s_sum - block[c].fillna(0.0)) / n_ex
            var = s_ex.rolling(win, min_periods=win).var()
            g = block[c].rolling(win, min_periods=win).cov(s_ex) / var
            e2[c] = block[c] - g * s_ex
    return e2.where(e2.notna(), e)


def _resid_momentum(e: pd.DataFrame, scaling: str) -> pd.DataFrame:
    """Momentum over residual days [t-L+1-skip .. t-skip]. scaling='ir' -> t-stat-like
    idiosyncratic IR = sum(e)/(std(e)*sqrt(L)); scaling='sum' -> plain sum(e)."""
    S = e.rolling(_L, min_periods=_MP).sum().shift(_SKIP)
    if scaling == "sum":
        return S
    V = e.rolling(_L, min_periods=_MP).std().shift(_SKIP)
    return S / (V * np.sqrt(_L))


def build_raw_weights(pn: dict, aux: dict) -> pd.DataFrame:
    """Raw signed residual-momentum weights on the full panel grid (NaN = flat).

    pn: {'open','high','low','close','volume'} (dates x tickers). aux: {'vix','sector_map','seed'}.
    Only pn['close'] and aux['sector_map'] are read. Tickers are derived from the panel columns.
    """
    close = pn["close"]
    sector_map = aux["sector_map"]

    ret = _daily_returns(close)

    # residualization: market, then sector (self-excluded), both at the 63d window
    e = _market_residual(ret, _BETA_WIN)
    e = _sector_residual(e, sector_map, _BETA_WIN)

    # 50/50 blend of the two variants' cross-sectional pct-ranks
    m_ir = _resid_momentum(e, "ir")
    m_sum = _resid_momentum(e, "sum")
    mom = 0.5 * m_ir.rank(axis=1, pct=True) + 0.5 * m_sum.rank(axis=1, pct=True)

    # cross-sectional pct-rank -> dollar-neutral raw weights (NaN stays NaN)
    r = mom.rank(axis=1, pct=True)
    w = dollar_neutralize(r)

    # turnover-control EMA on 0-filled weights (ineligible -> 0 before smoothing)
    return w.fillna(0.0).ewm(halflife=_HALFLIFE, min_periods=1).mean()
