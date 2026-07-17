"""team-01 scratch research library — residual (beta-stripped) momentum. IS data only.

Data reaches this code ONLY via tournament.engine (manifest-verified frozen snapshot).
Signals are built from te.team_view(pn) + aux exclusively; pn['ret_fwd'] is never touched
in signal construction — it stays inside te.run_is (scoring only).
"""

from __future__ import annotations

import sys

sys.path.insert(0, "analysis/portfolio/tradfi")

import numpy as np
import pandas as pd
from neutralize import dollar_neutralize  # approved substrate module

from tournament import engine as te

_CACHE: dict = {}


def load():
    """(pn, view, aux) — pn is passed ONLY to te.run_is; signals use view/aux."""
    if "pn" not in _CACHE:
        pn, aux = te.load_is_panels()
        _CACHE["pn"] = pn
        _CACHE["aux"] = aux
        _CACHE["view"] = te.team_view(pn)
    return _CACHE["pn"], _CACHE["view"], _CACHE["aux"]


# ------------------------------------------------------------------ signal pipeline --------------
def daily_returns(view: dict) -> pd.DataFrame:
    close = view["close"]
    return close / close.shift(1) - 1.0


def ew_market(ret: pd.DataFrame) -> pd.Series:
    """Equal-weight market proxy: cross-sectional mean of available names' returns."""
    return ret.mean(axis=1)


def rolling_beta(ret: pd.DataFrame, mkt: pd.Series, win: int) -> pd.DataFrame:
    """Past-only rolling beta (window ends at current bar; no future bars touched)."""
    var = mkt.rolling(win, min_periods=win).var()
    out = {c: ret[c].rolling(win, min_periods=win).cov(mkt) for c in ret.columns}
    return pd.DataFrame(out, index=ret.index).div(var, axis=0)


def market_residual(ret: pd.DataFrame, beta_win: int) -> pd.DataFrame:
    """e_t = r_t - beta_t * m_t. Alpha is NOT subtracted — idiosyncratic drift IS the signal."""
    mkt = ew_market(ret)
    beta = rolling_beta(ret, mkt, beta_win)
    return ret - beta.mul(mkt, axis=0)


def sector_residual(e: pd.DataFrame, sector_map: dict, win: int) -> pd.DataFrame:
    """Second-stage: strip each name's loading on its (self-excluded) EW sector residual basket.
    Falls back to the market-only residual where the sector stage is undefined (n<3 members)."""
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


def resid_momentum(e: pd.DataFrame, form: int, skip: int, scaling: str = "ir",
                   mp_frac: float = 0.9) -> pd.DataFrame:
    """Momentum over residual days [t-form+1 .. t-skip] (length L=form-skip), shifted by skip.
    scaling='ir': sum(e)/ (std(e)*sqrt(L))  — t-stat-like idiosyncratic IR (family core)
    scaling='sum': plain sum(e)             — un-normalised variant."""
    L = form - skip
    mp = int(round(mp_frac * L))
    S = e.rolling(L, min_periods=mp).sum().shift(skip)
    if scaling == "sum":
        return S
    V = e.rolling(L, min_periods=mp).std().shift(skip)
    return S / (V * np.sqrt(L))


def to_weights(mom: pd.DataFrame, scheme: str = "rank", q: float = 0.3) -> pd.DataFrame:
    """Cross-sectional transform -> dollar-neutral raw weights. NaN = ineligible (flat)."""
    r = mom.rank(axis=1, pct=True)
    if scheme == "rank":
        return dollar_neutralize(r)
    if scheme == "quantile":
        w = pd.DataFrame(
            np.where(r >= 1.0 - q, 1.0, np.where(r <= q, -1.0, 0.0)),
            index=r.index, columns=r.columns,
        )
        w = w.where(mom.notna())
        return dollar_neutralize(w)
    raise ValueError(scheme)


def smooth(w: pd.DataFrame, halflife: float | None) -> pd.DataFrame:
    """Past-only EMA of target weights (turnover control). Ineligible -> 0 before smoothing."""
    w = w.fillna(0.0)
    if not halflife:
        return w
    return w.ewm(halflife=halflife, min_periods=1).mean()


def build(view: dict, aux: dict, cfg: dict) -> pd.DataFrame:
    """cfg keys: resid ('none'|'market'|'market+sector'), beta_win, form, skip,
    scaling ('ir'|'sum'), scheme ('rank'|'quantile'), q, halflife, mp_frac."""
    ret = daily_returns(view)
    if cfg["resid"] == "none":
        e = ret
    else:
        e = market_residual(ret, cfg["beta_win"])
        if cfg["resid"] == "market+sector":
            e = sector_residual(e, aux["sector_map"], cfg["beta_win"])
    scaling = cfg.get("scaling", "ir")
    if scaling == "blend":  # 50/50 average of the two variants' cross-sectional pct-ranks
        m_ir = resid_momentum(e, cfg["form"], cfg["skip"], "ir", cfg.get("mp_frac", 0.9))
        m_sum = resid_momentum(e, cfg["form"], cfg["skip"], "sum", cfg.get("mp_frac", 0.9))
        mom = 0.5 * m_ir.rank(axis=1, pct=True) + 0.5 * m_sum.rank(axis=1, pct=True)
    else:
        mom = resid_momentum(e, cfg["form"], cfg["skip"], scaling, cfg.get("mp_frac", 0.9))
    w = to_weights(mom, cfg.get("scheme", "rank"), cfg.get("q", 0.3))
    return smooth(w, cfg.get("halflife"))


def score(cfg: dict, label: str, cost_mults=(1.0, 2.0)) -> dict:
    """Evaluate one config through the organizer engine at the given cost tiers."""
    pn, view, aux = load()
    raw = build(view, aux, cfg)
    res = {"label": label, "cfg": cfg}
    for cm in cost_mults:
        _net, _w, m = te.run_is(raw, pn, cost_mult=cm)
        res[f"cost_{cm:g}x"] = m.to_dict()
    return res


def brief_line(res: dict) -> str:
    m1 = res["cost_1x"]
    m2 = res.get("cost_2x")
    s = (f"{res['label']:<34} S1x={m1['sharpe']:+.3f}"
         f" dd={m1['maxdd']:+.3f} to={m1['ann_turnover']:6.1f}"
         f" brL={m1['median_names_long']:.0f} brS={m1['median_names_short']:.0f}")
    if m2:
        s += f" | S2x={m2['sharpe']:+.3f}"
    rs = m1.get("regime_sharpe") or {}
    if rs:
        s += (f" | bull={rs.get('bull', float('nan')):+.2f}"
              f" bear={rs.get('bear', float('nan')):+.2f}"
              f" chop={rs.get('chop', float('nan')):+.2f}")
    return s
