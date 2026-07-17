"""team-03 — stress-gated sector-residual reversal (family t03-sector-residual-reversal-v1).

FROZEN SPEC transcription of research_brief.md §2 (which pins the reference
`scratch_lib.build_raw` at exactly:
  L=5, skip=0, vol_std=True, vol_win=63, transform="blend", winsor=3.0, ema_span=5,
  z_in=0.0, exhaust=False, vix_mode="pct", vix_thr=0.85, sector_demean=False,
  inv_vol=False, peers_min=2, min_hist=63).

Dead branches (skip / z_in / exhaust / level-VIX / sector_demean / inv_vol) are removed as
the brief's QE checklist directs; the numerics and step order of the LIVE branches are
preserved bit-for-bit so `cli.py team-run` reproduces exp-014.

Mechanism: large idiosyncratic single-name moves against the sector basket revert at a 5-day
horizon; the book is switched ON only in the top-VIX-percentile stress states (rolling-252d
percentile > 0.85) where forced flows widen the dislocations enough to clear 6 bps/side.

PURE, DETERMINISTIC, PAST-ONLY. Uses ONLY pn['close'], aux['vix'], aux['sector_map'].
aux['seed'] is unused (no randomness). No file I/O, no network, no subprocess, no wall clock.
Tickers are taken from pn['close'].columns at runtime — never hard-coded. The engine owns
gross-normalisation, per-name/net caps, the shift(1) decision lag, costs, and vol-targeting;
this function emits RAW signed weights only (NaN = flat).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ---- frozen parameters (research_brief.md §2 / experiments.jsonl exp-014) ----
_L = 5  # residual horizon (days)
_VOL_WIN = 63  # residual-vol standardisation window
_VOL_MIN = 40  # min periods for the residual-vol std
_WINSOR = 3.0  # z-score clip for the blend transform
_EMA_SPAN = 5  # time-smoothing span
_VIX_THR = 0.85  # rolling-252d VIX percentile gate threshold
_VIX_WIN = 252  # VIX percentile lookback (days)
_VIX_MIN = 126  # min periods for the VIX percentile
_VIX_FFILL = 5  # max forward-fill for VIX gaps (days)
_PEERS_MIN = 2  # min active sector peers to use the sector basket
_MIN_HIST = 63  # min daily returns in trailing 2*min_hist days to be active


def _daily_returns(close: pd.DataFrame) -> pd.DataFrame:
    return close / close.shift(1) - 1.0


def _active_mask(close: pd.DataFrame, r: pd.DataFrame) -> pd.DataFrame:
    """Tradable today: bar present AND >= _MIN_HIST daily returns in the trailing 2*_MIN_HIST days."""
    hist = r.notna().rolling(2 * _MIN_HIST, min_periods=1).sum()
    return close.notna() & (hist >= _MIN_HIST)


def _sector_residual(
    r: pd.DataFrame, sector_map: dict[str, str], active: pd.DataFrame
) -> pd.DataFrame:
    """e_i = r_i - basket_i. Basket = mean of ACTIVE sector peers excl. self (>= _PEERS_MIN),
    else mean of the active universe excl. self. NaN where r_i is NaN.

    Missing tickers fall into group "Unknown" because make_aux maps every tradable name via
    SECTOR_MAP.get(t, "Unknown"); each sector writes to a disjoint column block so the group
    iteration order is immaterial to the result."""
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
        basket = np.where(peer_cnt >= _PEERS_MIN, peer_mean, uni_mean)
        e[cols] = v - basket
    return e


def _blend_transform(s: pd.DataFrame) -> pd.DataFrame:
    """Fixed 50/50 blend (no tuning) of unit-scaled winsorised z-score and centered rank,
    computed cross-sectionally per day over active names."""
    mu = s.mean(axis=1)
    sd = s.std(axis=1)
    z = s.sub(mu, axis=0).div(sd.replace(0.0, np.nan), axis=0)
    z = z.clip(-_WINSOR, _WINSOR)
    pct = s.rank(axis=1, pct=True)
    return 0.5 * (z / _WINSOR) + 0.5 * ((pct - 0.5) * 2.0)


def build_raw_weights(pn: dict[str, pd.DataFrame], aux: dict) -> pd.DataFrame:
    close = pn["close"]
    r = _daily_returns(close)
    active = _active_mask(close, r)
    e = _sector_residual(r, aux["sector_map"], active)

    # signal core: vol-standardised L-day residual reversal
    R = e.fillna(0.0).rolling(_L, min_periods=1).sum().where(active)
    sigma = e.rolling(_VOL_WIN, min_periods=_VOL_MIN).std()
    R = R / (sigma * np.sqrt(_L))
    s = -R

    # cross-sectional transform over active names
    w = _blend_transform(s.where(active))

    # stress gate (BEFORE smoothing — order is load-bearing): rolling-252d VIX percentile > 0.85
    v = aux["vix"].reindex(close.index).ffill(limit=_VIX_FFILL)
    pctile = v.rolling(_VIX_WIN, min_periods=_VIX_MIN).rank(pct=True)
    g = (pctile > _VIX_THR).astype(float)
    w = w.mul(g.fillna(0.0), axis=0)

    # time smoothing, then mask to active names (NaN = flat)
    w = w.ewm(span=_EMA_SPAN, min_periods=1).mean()
    return w.where(active)
