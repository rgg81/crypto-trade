"""team-03 scratch signal builder — sector-relative short-horizon mean reversion.

Family: t03-sector-residual-reversal-v1 (approved). QR exploration code; the QE re-implements
the FROZEN spec in strategy.py from research_brief.md — this file is reference only.

Pipeline (all knobs pre-registered per experiment in experiments.jsonl):
  1. daily simple returns from close
  2. sector-basket return per name = equal-weight mean of ACTIVE sector peers (excluding self);
     fallback to universe mean (excluding self) when peer count < peers_min
  3. residual e = r - basket; L-day rolling sum R (skip most recent `skip` days)
  4. optional residual-vol standardisation: R / (sigma_e * sqrt(L)), sigma_e = rolling vol_win std
  5. signal s = -core  (fade the idiosyncratic move)
  6. cross-sectional transform over active names: winsorised z-score or centered rank
  7. optional time smoothing: EMA(span=ema_span) of the transformed signal
  8. optional sector-demean of weights (exact sector-neutral book at emission)
  9. optional inverse-total-vol scaling
Emit raw signed weights; engine owns gross-norm, caps, shift(1), costs, vol-target.

Uses ONLY view panels + aux['sector_map']. No ret_fwd, no VIX, no volume (family purity).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def daily_returns(close: pd.DataFrame) -> pd.DataFrame:
    return close / close.shift(1) - 1.0


def active_mask(close: pd.DataFrame, r: pd.DataFrame, min_hist: int = 63) -> pd.DataFrame:
    """Tradable today: bar present AND >= min_hist daily returns in the trailing 2*min_hist days."""
    hist = r.notna().rolling(2 * min_hist, min_periods=1).sum()
    return close.notna() & (hist >= min_hist)


def sector_residual(
    r: pd.DataFrame, sector_map: dict[str, str], active: pd.DataFrame, peers_min: int = 2
) -> pd.DataFrame:
    """e_i = r_i - basket_i. Basket = mean of active sector peers excl self (>= peers_min),
    else mean of the active universe excl self. NaN where r_i is NaN."""
    rA = r.where(active)
    uni_sum = rA.sum(axis=1).to_numpy()[:, None]
    uni_cnt = rA.notna().sum(axis=1).to_numpy()[:, None]
    e = pd.DataFrame(np.nan, index=r.index, columns=r.columns)
    for sec in sorted(set(sector_map.values())):
        cols = [c for c in r.columns if sector_map.get(c) == sec]
        if not cols:
            continue
        S = rA[cols]
        v = S.to_numpy()
        own = S.notna().to_numpy()
        vf = np.nan_to_num(v)
        ssum = np.nansum(v, axis=1)[:, None]
        scnt = own.sum(axis=1)[:, None]
        peer_cnt = scnt - own.astype(int)
        with np.errstate(invalid="ignore", divide="ignore"):
            peer_mean = (ssum - vf) / np.maximum(peer_cnt, 1)
            uni_mean = (uni_sum - vf) / np.maximum(uni_cnt - own.astype(int), 1)
        basket = np.where(peer_cnt >= peers_min, peer_mean, uni_mean)
        e[cols] = v - basket
    return e


def xs_transform(s: pd.DataFrame, kind: str = "z", winsor: float = 3.0) -> pd.DataFrame:
    if kind == "rank":
        pct = s.rank(axis=1, pct=True)
        return (pct - 0.5) * 2.0
    mu = s.mean(axis=1)
    sd = s.std(axis=1)
    z = s.sub(mu, axis=0).div(sd.replace(0.0, np.nan), axis=0)
    z = z.clip(-winsor, winsor)
    if kind == "blend":  # fixed 50/50 average of unit-scaled z and centered rank — no tuning
        pct = s.rank(axis=1, pct=True)
        return 0.5 * (z / winsor) + 0.5 * ((pct - 0.5) * 2.0)
    return z


def build_raw(
    view: dict[str, pd.DataFrame],
    aux: dict,
    *,
    L: int = 5,
    skip: int = 0,
    vol_std: bool = False,
    vol_win: int = 63,
    transform: str = "z",
    winsor: float = 3.0,
    ema_span: int = 1,
    z_in: float = 0.0,
    exhaust: bool = False,
    vix_mode: str | None = None,  # None | "level" | "pct" | "scale"
    vix_thr: float = 20.0,
    sector_demean: bool = False,
    inv_vol: bool = False,
    peers_min: int = 2,
    min_hist: int = 63,
) -> pd.DataFrame:
    close = view["close"]
    r = daily_returns(close)
    active = active_mask(close, r, min_hist=min_hist)
    e = sector_residual(r, aux["sector_map"], active, peers_min=peers_min)

    eL = e.shift(skip) if skip else e
    R = eL.fillna(0.0).rolling(L, min_periods=1).sum().where(active)
    if vol_std:
        sigma = e.rolling(vol_win, min_periods=40).std()
        R = R / (sigma * np.sqrt(L))
    s = -R

    w = xs_transform(s.where(active), kind=transform, winsor=winsor)
    if z_in > 0.0:  # soft-threshold: fade only tail dislocations, dead-zone the noise band
        w = np.sign(w) * (w.abs() - z_in).clip(lower=0.0)
    if exhaust:
        # close-location-in-range gate: fade a down-dislocation (w>0) only when day-t close
        # bounced into the upper half of the day's range (selling exhausted), and vice versa.
        h, lo_, c = view["high"], view["low"], view["close"]
        rng = (h - lo_).replace(0.0, np.nan)
        clr = ((c - lo_) / rng).fillna(0.5)  # 0=closed at low, 1=closed at high
        gate = (2.0 * (clr - 0.5) * np.sign(w)).clip(0.0, 1.0)
        w = w * gate
    if vix_mode:
        # In-family stress conditioner (registered expected_regime_behavior: edge lives in
        # elevated-VIX dislocation episodes). Same-bar VIX close is decide-at-close info.
        v = aux["vix"].reindex(close.index).ffill(limit=5)
        if vix_mode == "level":
            g = (v > vix_thr).astype(float)
        else:
            pct = v.rolling(252, min_periods=126).rank(pct=True)
            g = (
                (pct > vix_thr).astype(float)
                if vix_mode == "pct"
                else ((pct - vix_thr) / max(1.0 - vix_thr, 1e-9)).clip(0.0, 1.0)
            )
        w = w.mul(g.fillna(0.0), axis=0)
    if ema_span and ema_span > 1:
        w = w.ewm(span=ema_span, min_periods=1).mean()
    w = w.where(active)
    if sector_demean:
        sm = aux["sector_map"]
        for sec in sorted(set(sm.values())):
            cols = [c for c in w.columns if sm.get(c) == sec]
            if cols:
                w[cols] = w[cols].sub(w[cols].mean(axis=1), axis=0)
    if inv_vol:
        sig_tot = r.rolling(vol_win, min_periods=40).std()
        w = w / sig_tot
    return w.where(active)
