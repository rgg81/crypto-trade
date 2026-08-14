"""Sleeve signal library. Every sleeve emits a unit-gross weight matrix on the decision grid.

Causality convention (verified against engine_v2.generate_targets):
at decision index i (global bar index gi = panel.t0 + i) the strategy may read bars with
close_time <= decision_time, i.e. global bar indices <= gi-1, and funding settlements strictly
before decision_time, i.e. 8h funding buckets <= gi-1. Nothing here touches index gi or later.
"""
from __future__ import annotations

import numpy as np


def _unit_gross(W: np.ndarray) -> np.ndarray:
    g = np.abs(W).sum(axis=1)
    return W / np.where(g > 0, g, 1.0)[:, None]


def _demean_rank(x: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Cross-sectional rank in [-1, 1], zero-mean, over the masked entries of one row."""
    out = np.zeros_like(x)
    idx = np.where(mask & np.isfinite(x))[0]
    n = len(idx)
    if n < 4:
        return out
    order = idx[np.argsort(x[idx], kind="stable")]
    r = np.arange(n, dtype=float)
    r = (r - r.mean()) / (r.std() if r.std() > 0 else 1.0)
    out[order] = r
    return out


def _top_bottom(x: np.ndarray, mask: np.ndarray, k: int, sign: float) -> np.ndarray:
    out = np.zeros_like(x)
    idx = np.where(mask & np.isfinite(x))[0]
    if len(idx) < 2 * k:
        return out
    order = idx[np.argsort(x[idx], kind="stable")]
    out[order[-k:]] = sign
    out[order[:k]] = -sign
    return out


def carry(panel, elig, *, lookback: int, k: int = 0, use_rank: bool = True) -> np.ndarray:
    """Cross-sectional funding carry: short the names paying the most, long those paying least.

    Causal base: the perpetual funding mechanism transfers cash from the crowded side to the
    uncrowded side. Trailing funding measures how much leveraged positioning is being paid for.
    """
    n = len(panel.times); ns = len(panel.symbols); t0 = panel.t0
    rate = panel.funding_rate_bar
    W = np.zeros((n, ns))
    csum = np.nancumsum(np.nan_to_num(rate), axis=0)
    for i in range(n):
        gi = t0 + i
        if gi - lookback < 0:
            continue
        s = (csum[gi - 1] - csum[gi - 1 - lookback]) / lookback
        m = elig[i]
        W[i] = -( _demean_rank(s, m) if use_rank or k == 0 else _top_bottom(s, m, k, 1.0) )
    return _unit_gross(W)


def trend(panel, elig, *, lookback: int, vol_lookback: int = 90, vol_scale: bool = True) -> np.ndarray:
    """Per-coin time-series momentum: long names in an uptrend, short names in a downtrend.

    Causal base: slow diffusion of information across a fragmented 24/7 retail base plus
    reflexive leverage. Net exposure is a free variable and swings with the market's own state.
    """
    n = len(panel.times); ns = len(panel.symbols); t0 = panel.t0
    cl = panel.close
    lr = np.diff(np.log(cl), axis=0, prepend=np.nan)
    W = np.zeros((n, ns))
    for i in range(n):
        gi = t0 + i
        if gi - lookback - 1 < 0:
            continue
        r = cl[gi - 1] / cl[gi - 1 - lookback] - 1.0
        m = elig[i] & np.isfinite(r)
        s = np.sign(r)
        if vol_scale:
            v = np.nanstd(lr[gi - vol_lookback : gi], axis=0)
            v = np.where(np.isfinite(v) & (v > 0), v, np.nan)
            s = s / v
        s = np.where(m & np.isfinite(s), s, 0.0)
        W[i] = s
    return _unit_gross(W)


def lowrisk(panel, elig, *, lookback: int, measure: str = "vol") -> np.ndarray:
    """Cross-sectional low-risk selection: long the calm names, short the wild ones.

    Causal base: leverage-constrained and lottery-seeking participants overpay for high-volatility
    names, so risk is priced too cheaply at the calm end of a 20-name blue-chip cross-section.
    """
    n = len(panel.times); ns = len(panel.symbols); t0 = panel.t0
    cl = panel.close
    lr = np.diff(np.log(cl), axis=0, prepend=np.nan)
    W = np.zeros((n, ns))
    for i in range(n):
        gi = t0 + i
        if gi - lookback < 0:
            continue
        win = lr[gi - lookback : gi]
        if measure == "vol":
            s = np.nanstd(win, axis=0)
        elif measure == "downside":
            neg = np.where(win < 0, win, np.nan)
            s = np.sqrt(np.nanmean(neg ** 2, axis=0))
        elif measure == "maxdd":
            eq = np.nancumsum(np.nan_to_num(win), axis=0)
            s = np.nanmax(np.maximum.accumulate(eq, axis=0) - eq, axis=0)
        else:
            raise ValueError(measure)
        m = elig[i]
        W[i] = -_demean_rank(s, m)
    return _unit_gross(W)


def clock(panel, elig, *, warmup: int = 1095, bucket: str = "hour") -> np.ndarray:
    """Settlement-clock seasonality, estimated from an expanding past-only window.

    Causal base: participation is not uniform around the 24h clock or the week; the funding
    settlement grid at 00/08/16 UTC and the Asia/Europe/US session handover concentrate flow.
    Long the whole eligible cross-section in buckets whose past mean 8h return is positive,
    short it in buckets whose past mean is negative.
    """
    n = len(panel.times); ns = len(panel.symbols); t0 = panel.t0
    cl = panel.close
    lr = np.diff(np.log(cl), axis=0, prepend=np.nan)
    xs = np.nanmean(lr, axis=1)           # equal-weight cross-sectional 8h log return
    times = panel.full_times
    if bucket == "hour":
        key = np.asarray(times.hour) // 8
    elif bucket == "dow":
        key = np.asarray(times.dayofweek)
    elif bucket == "dowhour":
        key = np.asarray(times.dayofweek) * 3 + np.asarray(times.hour) // 8
    else:
        raise ValueError(bucket)
    nk = int(key.max()) + 1
    W = np.zeros((n, ns))
    sums = np.zeros(nk); cnts = np.zeros(nk)
    # prime with everything strictly before the first decision boundary
    for gi in range(1, t0):
        if np.isfinite(xs[gi]):
            sums[key[gi]] += xs[gi]; cnts[key[gi]] += 1
    for i in range(n):
        gi = t0 + i
        # the bar that closed at this boundary is gi-1 and IS observable
        if i > 0 and np.isfinite(xs[gi - 1]):
            sums[key[gi - 1]] += xs[gi - 1]; cnts[key[gi - 1]] += 1
        if cnts.min() < warmup / nk:
            continue
        mu = sums / np.maximum(cnts, 1)
        # the bucket the FILL bar occupies is gi (the bar we are about to hold)
        b = key[gi]
        m = elig[i]
        if m.sum() == 0:
            continue
        W[i, m] = np.sign(mu[b]) / m.sum()
    return _unit_gross(W)


def hold_cadence(W: np.ndarray, cadence: int, phase: int) -> np.ndarray:
    """Boolean rebalance instruction: act only on boundaries congruent to `phase` mod `cadence`."""
    n = len(W)
    r = np.zeros(n, dtype=bool)
    r[np.arange(n) % cadence == phase % cadence] = True
    r &= np.abs(W).sum(axis=1) > 0
    return r


def trend_blend(panel, elig, *, lookbacks, vol_lookback: int = 90) -> np.ndarray:
    """Multi-horizon time-series trend: mean of the sign of trailing returns at several horizons,
    divided by the name's own realised volatility. Blending horizons is the standard remedy for
    the single-lookback lottery, and it is chosen a priori rather than picked from the sweep."""
    n = len(panel.times); ns = len(panel.symbols); t0 = panel.t0
    cl = panel.close
    lr = np.diff(np.log(cl), axis=0, prepend=np.nan)
    W = np.zeros((n, ns))
    lb_max = max(lookbacks)
    for i in range(n):
        gi = t0 + i
        if gi - lb_max - 1 < 0:
            continue
        acc = np.zeros(ns)
        for lb in lookbacks:
            r = cl[gi - 1] / cl[gi - 1 - lb] - 1.0
            acc += np.sign(np.where(np.isfinite(r), r, 0.0))
        acc /= len(lookbacks)
        v = np.nanstd(lr[gi - vol_lookback : gi], axis=0)
        v = np.where(np.isfinite(v) & (v > 0), v, np.nan)
        s = np.where(elig[i], acc / v, 0.0)
        W[i] = np.nan_to_num(s)
    return _unit_gross(W)


def carry_blend(panel, elig, *, lookbacks, mode: str = "rank") -> np.ndarray:
    """Multi-horizon cross-sectional funding carry."""
    n = len(panel.times); ns = len(panel.symbols); t0 = panel.t0
    rate = panel.funding_rate_bar
    csum = np.nancumsum(np.nan_to_num(rate), axis=0)
    W = np.zeros((n, ns))
    lb_max = max(lookbacks)
    for i in range(n):
        gi = t0 + i
        if gi - lb_max - 1 < 0:
            continue
        acc = np.zeros(ns)
        m = elig[i]
        for lb in lookbacks:
            s = (csum[gi - 1] - csum[gi - 1 - lb]) / lb
            acc += _demean_rank(s, m)
        W[i] = -acc / len(lookbacks)
    return _unit_gross(W)


def lowrisk_blend(panel, elig, *, lookbacks, measures=("vol", "downside", "maxdd")) -> np.ndarray:
    """Multi-horizon, multi-measure cross-sectional risk selection."""
    n = len(panel.times); ns = len(panel.symbols); t0 = panel.t0
    cl = panel.close
    lr = np.diff(np.log(cl), axis=0, prepend=np.nan)
    W = np.zeros((n, ns))
    lb_max = max(lookbacks)
    for i in range(n):
        gi = t0 + i
        if gi - lb_max - 1 < 0:
            continue
        m = elig[i]
        acc = np.zeros(ns)
        cnt = 0
        for lb in lookbacks:
            win = lr[gi - lb : gi]
            for meas in measures:
                if meas == "vol":
                    s = np.nanstd(win, axis=0)
                elif meas == "downside":
                    neg = np.where(win < 0, win, np.nan)
                    with np.errstate(invalid="ignore"):
                        s = np.sqrt(np.nanmean(neg ** 2, axis=0))
                elif meas == "maxdd":
                    eq = np.nancumsum(np.nan_to_num(win), axis=0)
                    s = np.nanmax(np.maximum.accumulate(eq, axis=0) - eq, axis=0)
                else:
                    raise ValueError(meas)
                acc += _demean_rank(s, m)
                cnt += 1
        W[i] = -acc / cnt
    return _unit_gross(W)


def takerflow(panel, elig, *, lookback: int, sign: float = 1.0) -> np.ndarray:
    """Cross-sectional aggressive-flow imbalance: which names market orders are lifting.

    Causal base: taker flow is the footprint of impatient, price-insensitive demand. Sign +1 goes
    with the flow (pressure continuation); sign -1 fades it (inventory-risk premium to the
    liquidity provider who absorbs it).
    """
    n = len(panel.times); ns = len(panel.symbols); t0 = panel.t0
    tb = np.nan_to_num(panel.taker_buy_quote)
    qv = np.nan_to_num(panel.quote_volume)
    imb = np.where(qv > 0, (2.0 * tb - qv) / np.where(qv > 0, qv, 1.0), np.nan)
    W = np.zeros((n, ns))
    for i in range(n):
        gi = t0 + i
        if gi - lookback < 0:
            continue
        with np.errstate(invalid="ignore"):
            s = np.nanmean(imb[gi - lookback : gi], axis=0)
        W[i] = sign * _demean_rank(s, elig[i])
    return _unit_gross(W)


def revshock(panel, elig, *, lookback: int, sign: float = -1.0, scale_by_vol: bool = True) -> np.ndarray:
    """Short-horizon reversal on volume-normalised moves.

    Causal base: a liquidity provider absorbing an impatient flow demands compensation, so a move
    achieved on unusually thin participation reverts. Horizon is hours, not months, which is a
    different axis of orthogonality from the causal one.
    """
    n = len(panel.times); ns = len(panel.symbols); t0 = panel.t0
    cl = panel.close
    lr = np.diff(np.log(cl), axis=0, prepend=np.nan)
    W = np.zeros((n, ns))
    for i in range(n):
        gi = t0 + i
        if gi - lookback - 90 < 0:
            continue
        r = np.nansum(lr[gi - lookback : gi], axis=0)
        if scale_by_vol:
            v = np.nanstd(lr[gi - 90 : gi], axis=0)
            r = r / np.where(np.isfinite(v) & (v > 0), v, np.nan)
        W[i] = sign * _demean_rank(r, elig[i])
    return _unit_gross(W)


def takerflow_blend(panel, elig, *, lookbacks, sign: float = 1.0) -> np.ndarray:
    """Multi-horizon cross-sectional aggressive-flow imbalance."""
    n = len(panel.times); ns = len(panel.symbols); t0 = panel.t0
    tb = np.nan_to_num(panel.taker_buy_quote)
    qv = np.nan_to_num(panel.quote_volume)
    imb = np.where(qv > 0, (2.0 * tb - qv) / np.where(qv > 0, qv, 1.0), np.nan)
    W = np.zeros((n, ns))
    lb_max = max(lookbacks)
    for i in range(n):
        gi = t0 + i
        if gi - lb_max < 0:
            continue
        m = elig[i]
        acc = np.zeros(ns)
        for lb in lookbacks:
            with np.errstate(invalid="ignore"):
                s = np.nanmean(imb[gi - lb : gi], axis=0)
            acc += _demean_rank(s, m)
        W[i] = sign * acc / len(lookbacks)
    return _unit_gross(W)


# ---------------------------------------------------------------------------------------------
# Final frozen sleeve constructors, written to mirror candidates/*/strategy.py exactly
# (including its finite-history requirements). Validated against the real strategy by parity.py.
# ---------------------------------------------------------------------------------------------

def _ug1(v: np.ndarray) -> np.ndarray:
    g = float(np.abs(v).sum())
    return v / g if g > 0.0 else v


def s_carry(panel, elig, *, lookback: int) -> np.ndarray:
    n = len(panel.times); ns = len(panel.symbols); t0 = panel.t0
    rate = np.nan_to_num(panel.funding_rate_bar)
    has = (panel.funding_rate_bar != 0) | np.isfinite(panel.funding_rate_bar)
    present = (np.abs(panel.funding_rate_bar) >= 0)  # rows exist for all buckets after listing
    csum = np.cumsum(rate, axis=0)
    ccnt = np.cumsum(panel.funding_present.astype(float), axis=0)
    W = np.zeros((n, ns))
    for i in range(n):
        gi = t0 + i
        s = np.full(ns, np.nan)
        lo = gi - lookback
        if lo < 0:
            continue
        cnt = ccnt[gi - 1] - (ccnt[lo - 1] if lo > 0 else 0.0)
        tot = csum[gi - 1] - (csum[lo - 1] if lo > 0 else 0.0)
        ok = cnt > 0
        s[ok] = tot[ok] / lookback
        W[i] = _ug1(-_demean_rank(s, elig[i]))
    return W


def s_trend(panel, elig, *, base: int, vol_lookback: int = 90) -> np.ndarray:
    lbs = (base // 2, base, 3 * base // 2)
    n = len(panel.times); ns = len(panel.symbols); t0 = panel.t0
    cl = panel.close
    lr = np.diff(np.log(cl), axis=0, prepend=np.nan)
    need = max(max(lbs) + 1, vol_lookback + 1)
    W = np.zeros((n, ns))
    for i in range(n):
        gi = t0 + i
        if gi - need < 0:
            continue
        hist_ok = np.isfinite(cl[gi - need : gi]).all(axis=0)
        acc = np.zeros(ns)
        for lb in lbs:
            r = cl[gi - 1] / cl[gi - 1 - lb] - 1.0
            acc += np.sign(np.where(np.isfinite(r), r, 0.0))
        acc /= len(lbs)
        v = np.std(lr[gi - vol_lookback : gi], axis=0, ddof=0)
        ok = hist_ok & np.isfinite(v) & (v > 0)
        s = np.zeros(ns)
        s[ok] = acc[ok] / v[ok]
        W[i] = _ug1(np.where(elig[i], s, 0.0))
    return W


def s_lowrisk(panel, elig, *, base: int) -> np.ndarray:
    lbs = (base, 2 * base, 3 * base)
    n = len(panel.times); ns = len(panel.symbols); t0 = panel.t0
    cl = panel.close
    lr = np.diff(np.log(cl), axis=0, prepend=np.nan)
    W = np.zeros((n, ns))
    for i in range(n):
        gi = t0 + i
        acc = np.zeros(ns)
        for lb in lbs:
            s = np.full(ns, np.nan)
            if gi - lb - 1 >= 0:
                win = lr[gi - lb : gi]
                ok = np.isfinite(cl[gi - lb - 1 : gi]).all(axis=0)
                eq = np.cumsum(np.where(np.isfinite(win), win, 0.0), axis=0)
                dd = np.max(np.maximum.accumulate(eq, axis=0) - eq, axis=0)
                s[ok] = dd[ok]
            acc += _demean_rank(s, elig[i])
        W[i] = _ug1(-acc / len(lbs))
    return W


def s_flow(panel, elig, *, base: int) -> np.ndarray:
    lbs = (base, 2 * base)
    n = len(panel.times); ns = len(panel.symbols); t0 = panel.t0
    tb = panel.taker_buy_quote
    qv = panel.quote_volume
    with np.errstate(invalid="ignore", divide="ignore"):
        imb = np.where(np.isfinite(qv) & (qv > 0), (2.0 * tb - qv) / qv, np.nan)
    W = np.zeros((n, ns))
    for i in range(n):
        gi = t0 + i
        acc = np.zeros(ns)
        for lb in lbs:
            s = np.full(ns, np.nan)
            if gi - lb >= 0:
                win = imb[gi - lb : gi]
                cnt = np.isfinite(win).sum(axis=0)
                with np.errstate(invalid="ignore"):
                    m = np.nanmean(win, axis=0)
                ok = cnt > 0
                s[ok] = m[ok]
            acc += _demean_rank(s, elig[i])
        W[i] = _ug1(acc / len(lbs))
    return W
