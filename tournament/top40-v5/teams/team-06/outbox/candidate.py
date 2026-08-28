"""team-06 -- cluster relative value.  Nomination candidate.

Mandate: rolling correlation clusters, trading deviation from cluster mean.
Sector-neutral statistical arbitrage where the sectors are discovered rather
than declared.

The book at each decision, recomputed from past-only rows and nothing else:

  1. eligible symbols with enough history, ranked by median quote_volume;
     the top ``q_max * W`` form the correlation universe, and the tradeable
     weight is tapered to zero across the bottom of that ranking so a name
     crossing the universe boundary does not generate a discrete trade;
  2. Spearman correlation of winsorised 8h log returns;
  3. Marchenko-Pastur eigenvalue clipping of the noise bulk, then removal of
     the top (market) eigenvector;
  4. average-linkage agglomeration, read off at FIVE nested cut levels
     (K = 12, 8, 6, 4, 3) rather than one -- a consensus benchmark;
  5. per level, the leave-one-out mean of the name's own group; the benchmark
     is the average of those across levels, skipping levels where the group is
     smaller than m_min;
  6. residual return series, scaled by the name's own residual volatility;
  7. displacement = a symmetric triangular kernel over the last 63 bars
     (21 days) of that residual -- a slow spread *level*, near-blind to the
     most recent bars;
  8. centred within the coarse (K = 4) partition, scaled cross-sectionally,
     clipped at +/-3, contrarian sign, soft dead zone;
  9. plus a cluster-relative funding tilt, which costs no turnover;
 10. taper-weighted demean inside each coarse cluster and then globally, gross
     normalised to 1.0, per-name cap 0.09, |net| <= 0.20.

No persistent state, no RNG, no network, no filesystem, no absolute dates, no
symbol identity, no price levels.  ``seed`` is unused.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# --- universe -----------------------------------------------------------
_W_LADDER = (180, 120, 90)   # correlation window in 8h bars; first that fills
_Q_MAX = 0.40                # cap on the matrix aspect ratio N / T
_TAPER_FRAC = 0.60           # full trading weight below this fraction of ranks
_MIN_NAMES = 24              # below this the cross-section is not a portfolio

# --- clustering ---------------------------------------------------------
_CUTS = (12, 8, 6, 4, 3)     # nested cut levels of one dendrogram
_NEUTRAL_CUT = 4             # partition the book is made neutral to
_M_MIN = 5                   # smallest group allowed to be a benchmark

# --- signal -------------------------------------------------------------
_L = 63                      # triangular kernel length, 21 days
_WINSOR = 0.005              # per-column return winsorization
_Z_CLIP = 3.0
_Z_ENTER = 0.85              # soft dead zone
_SIGN = -1.0                 # contrarian
_ALPHA = 0.40                # weight on the cluster-relative funding tilt
_FUND_TAIL = 21              # funding settlements averaged
_FUND_ROWS = 20000           # rows of the funding frame inspected
_FUND_CLIP = 3.0

# --- book ---------------------------------------------------------------
_GROSS = 1.0
_MAX_W = 0.09
_NET_CAP = 0.20
_DUST = 1e-5
_EPS = 1e-12


# ------------------------------------------------------------------------
# pure helpers
# ------------------------------------------------------------------------
def _corr(a: np.ndarray) -> np.ndarray:
    """Column-wise Pearson correlation, safe on constant columns."""
    x = a - a.mean(axis=0, keepdims=True)
    sd = np.sqrt((x * x).sum(axis=0))
    x = x / np.where(sd > _EPS, sd, 1.0)
    c = x.T @ x
    c = 0.5 * (c + c.T)
    np.fill_diagonal(c, 1.0)
    return np.clip(c, -1.0, 1.0)


def _denoise(c: np.ndarray, q: float) -> np.ndarray:
    """MP-clip the noise bulk, drop the market mode, renormalise to unit diagonal.

    Laloux et al.: the bulk of an empirical spectrum is indistinguishable from
    a matrix with no correlation structure, so clustering the raw sample matrix
    clusters noise geometry.  Removing the leading eigenvector afterwards is
    what stops the discovered partition from being a beta sort.
    """
    vals, vecs = np.linalg.eigh(0.5 * (c + c.T))
    order = np.argsort(vals)[::-1]
    vals = vals[order]
    vecs = vecs[:, order]

    edge = (1.0 + np.sqrt(max(q, 0.0))) ** 2
    bulk = vals <= edge
    v = vals.copy()
    if bulk.any():
        v[bulk] = float(vals[bulk].mean())
    v = np.clip(v, 0.0, None)
    v[0] = 0.0

    resid = (vecs * v) @ vecs.T
    d = np.sqrt(np.clip(np.diag(resid), 1e-10, None))
    rc = resid / d[:, None] / d[None, :]
    rc = np.clip(0.5 * (rc + rc.T), -1.0, 1.0)
    np.fill_diagonal(rc, 1.0)
    return rc


def _linkage_cuts(dist: np.ndarray, cuts) -> dict:
    """Average-linkage agglomeration, labels snapshotted at each cut level.

    One dendrogram, read at several heights.  The cuts are nested by
    construction, which is what lets an undersized group at a fine level fall
    back on a coarser one.
    """
    n = int(dist.shape[0])
    work = np.array(dist, dtype=float, copy=True)
    work = np.where(np.isfinite(work), work, 4.0)
    np.fill_diagonal(work, np.inf)

    sizes = np.ones(n, dtype=float)
    labels = np.arange(n, dtype=np.int64)
    wanted = {int(k) for k in cuts if 2 <= int(k) <= n}
    snaps: dict = {}
    for k in cuts:
        if int(k) > n:
            snaps[int(k)] = np.arange(n, dtype=np.int64)
    if not wanted:
        return snaps

    live = n
    lowest = min(wanted)
    while live > lowest:
        flat = int(np.argmin(work))
        i, j = flat // n, flat % n
        if not np.isfinite(work[i, j]):
            break
        wi, wj = sizes[i], sizes[j]
        row = (wi * work[i, :] + wj * work[j, :]) / (wi + wj)
        row[i] = np.inf
        row[j] = np.inf
        work[i, :] = row
        work[:, i] = row
        work[j, :] = np.inf
        work[:, j] = np.inf
        sizes[i] = wi + wj
        labels[labels == j] = i
        live -= 1
        if live in wanted:
            snaps[live] = np.unique(labels, return_inverse=True)[1].astype(np.int64)
    return snaps


def _loo_resid(rets: np.ndarray, lab: np.ndarray, m_min: int):
    """Leave-one-out group-mean residual; names in undersized groups are invalid."""
    n = rets.shape[1]
    resid = np.zeros_like(rets)
    valid = np.zeros(n, dtype=bool)
    for c in range(int(lab.max()) + 1):
        idx = np.flatnonzero(lab == c)
        m = idx.size
        if m < m_min:
            continue
        block = rets[:, idx]
        peer = (block.sum(axis=1, keepdims=True) - block) / float(m - 1)
        resid[:, idx] = block - peer
        valid[idx] = True
    return resid, valid


def _unit(v: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Scale a component to unit cross-sectional dispersion over ``mask``."""
    if not mask.any():
        return np.zeros_like(v)
    s = float(v[mask].std())
    if s > _EPS:
        return v / s
    return np.zeros_like(v)


def _group_demean(vec: np.ndarray, lab: np.ndarray, taper: np.ndarray,
                  active: np.ndarray, m_min: int) -> None:
    """Taper-weighted demean inside each group, in place.

    Weighting the offset by the taper is what keeps a boundary name at a
    boundary-sized weight: a flat demean would hand it back the group offset
    and undo the taper.
    """
    for c in range(int(lab.max()) + 1):
        idx = np.flatnonzero((lab == c) & active)
        if idx.size < m_min:
            continue
        tt = float(taper[idx].sum())
        if tt > _EPS:
            vec[idx] -= taper[idx] * (float(vec[idx].sum()) / tt)


def _global_demean(vec: np.ndarray, taper: np.ndarray, active: np.ndarray) -> None:
    idx = np.flatnonzero(active)
    if idx.size == 0:
        return
    tt = float(taper[idx].sum())
    if tt > _EPS:
        vec[idx] -= taper[idx] * (float(vec[idx].sum()) / tt)


def _finalise(raw: np.ndarray, taper: np.ndarray, active: np.ndarray):
    """Gross normalisation, per-name cap, net cap.  No volatility targeting."""
    w = np.where(active, raw, 0.0).astype(float)
    for _ in range(10):
        g = float(np.abs(w).sum())
        if g <= _EPS:
            return None
        w = w * (_GROSS / g)
        if float(np.abs(w).max()) <= _MAX_W + 1e-12:
            break
        w = np.clip(w, -_MAX_W, _MAX_W)
        _global_demean(w, taper, active)
        w = np.where(active, w, 0.0)

    w = np.clip(w, -_MAX_W, _MAX_W)
    g = float(np.abs(w).sum())
    if g <= _EPS:
        return None
    if g > _GROSS:
        w = w * (_GROSS / g)

    net = float(w.sum())
    if abs(net) > _NET_CAP:
        idx = np.flatnonzero(active)
        if idx.size:
            w[idx] -= (net - np.sign(net) * _NET_CAP) / float(idx.size)
        w = np.clip(w, -_MAX_W, _MAX_W)
        g = float(np.abs(w).sum())
        if g > _GROSS:
            w = w * (_GROSS / g)

    if not np.isfinite(w).all():
        return None
    return w


def _funding_means(funding) -> dict:
    """Mean funding rate over the last settlements, per symbol.

    Read positionally from the tail of the frame and sorted only within that
    tail, so no absolute date enters and a large frame is not re-sorted at
    every decision.  If the frame is not time-ordered the tail covers too few
    symbols and the tilt disables itself rather than misreading.
    """
    if not isinstance(funding, pd.DataFrame) or len(funding) == 0:
        return {}
    cols = set(funding.columns)
    if "symbol" not in cols or "funding_rate" not in cols:
        return {}
    keep = ["symbol", "funding_rate"]
    if "funding_time" in cols:
        keep.append("funding_time")
    f = funding.iloc[-_FUND_ROWS:].loc[:, keep].dropna()
    if len(f) == 0:
        return {}
    if "funding_time" in f.columns:
        f = f.sort_values("funding_time", kind="mergesort")
    tail = f.groupby("symbol", sort=False).tail(_FUND_TAIL)
    means = tail.groupby("symbol", sort=False)["funding_rate"].mean()
    return {str(k): float(v) for k, v in means.items() if np.isfinite(v)}


def _rank_universe(bars, eligible):
    """Point-in-time universe: enough history, then the most liquid.

    The window ladder exists so the book is not silently flat at the start of
    the run, when few contracts carry 60 days of history.  Ties in the
    liquidity ranking fall back on the order the organiser supplied
    ``eligible_symbols`` in, never on the symbol string.
    """
    for window in _W_LADDER:
        scored = []
        for sym in eligible:
            if sym not in bars:
                continue
            frame = bars[sym]
            if frame is None or len(frame) < window + 1:
                continue
            qv = np.asarray(frame["quote_volume"].to_numpy(), dtype=float)[-window:]
            qv = qv[np.isfinite(qv)]
            if qv.size < window // 2:
                continue
            med = float(np.median(qv))
            if np.isfinite(med) and med > 0.0:
                scored.append((med, sym))
        if len(scored) >= _MIN_NAMES + 8:
            scored.sort(key=lambda pair: -pair[0])
            n_max = min(int(_Q_MAX * window), len(scored))
            if n_max >= _MIN_NAMES:
                return window, [sym for _, sym in scored[:n_max]]
    return 0, []


def _taper(n_max: int) -> np.ndarray:
    """Trading weight by liquidity rank: flat, then a linear ramp to zero.

    A hard top-N cut turns every boundary crossing into a full-size trade.
    Ramping the weight to zero at the boundary means a name arrives and leaves
    at ~0, which removes universe churn as a turnover source without any
    memory of the previous book.
    """
    ranks = np.arange(n_max, dtype=float)
    full = float(int(_TAPER_FRAC * n_max))
    denom = max(float(n_max) - full, 1.0)
    return np.clip((float(n_max) - ranks) / denom, 0.0, 1.0)


def _panel(bars, names, rows: int):
    """Closes aligned across symbols on ``open_time``, never on the row index.

    Each per-symbol frame carries a positional RangeIndex and symbols have
    unequal history, so concatenating on the default index puts two symbols in
    disjoint integer ranges and returns an all-NaN panel -- a strategy that
    raises nothing and holds a flat book forever.  ``open_time`` is the only
    correct key, and the columns are re-indexed back onto ``names`` so the
    liquidity ordering the taper depends on cannot be permuted.
    """
    tail_rows = rows + 30
    series = []
    for sym in names:
        frame = bars[sym].iloc[-tail_rows:]
        s = pd.Series(
            np.asarray(frame["close"].to_numpy(), dtype=float),
            index=pd.Index(frame["open_time"].to_numpy()),
        )
        series.append(s[~s.index.duplicated(keep="last")])
    if not series:
        return None
    panel = pd.concat(series, axis=1, keys=list(names)).sort_index()
    panel = panel.loc[:, list(names)]

    present = panel.notna().to_numpy().sum(axis=1)
    panel = panel.loc[present >= max(2, int(0.5 * panel.shape[1]))]
    panel = panel.ffill(limit=4).iloc[-rows:]
    if panel.shape[0] < rows:
        return None
    return panel


# ------------------------------------------------------------------------
# the decision
# ------------------------------------------------------------------------
def _decide(context):
    bars = context.bars
    if not bars:
        return None
    eligible = [str(s) for s in context.eligible_symbols]
    if len(eligible) < _MIN_NAMES:
        return None

    window, names = _rank_universe(bars, eligible)
    if window == 0:
        return None

    taper = _taper(len(names))
    panel = _panel(bars, names, window + 1)
    if panel is None or panel.shape[1] < _MIN_NAMES:
        return None

    px = np.asarray(panel.to_numpy(), dtype=float)
    ok = np.isfinite(px).all(axis=0) & (px > 0.0).all(axis=0)
    if int(ok.sum()) < _MIN_NAMES:
        return None
    keep = np.flatnonzero(ok)
    px = px[:, keep]
    names = [names[i] for i in keep]
    taper = taper[keep]

    rets = np.diff(np.log(px), axis=0)
    rets = np.where(np.isfinite(rets), rets, 0.0)
    lo = np.quantile(rets, _WINSOR, axis=0)
    hi = np.quantile(rets, 1.0 - _WINSOR, axis=0)
    rets = np.clip(rets, lo, hi)

    n_obs, n_sym = rets.shape
    if n_obs < _L + 4 or n_sym < _MIN_NAMES:
        return None

    # -- discovered sectors: one dendrogram, read at five heights ---------
    ranks = pd.DataFrame(rets).rank(axis=0).to_numpy(dtype=float)
    resid_corr = _denoise(_corr(ranks), float(n_sym) / float(n_obs))
    dist = np.sqrt(np.clip(2.0 * (1.0 - resid_corr), 0.0, None))
    cuts = _linkage_cuts(dist, _CUTS)

    acc = np.zeros_like(rets)
    cnt = np.zeros(n_sym, dtype=float)
    for k in _CUTS:
        lab = cuts.get(int(k))
        if lab is None:
            continue
        block, valid = _loo_resid(rets, lab, _M_MIN)
        if not valid.any():
            continue
        acc[:, valid] += block[:, valid]
        cnt[valid] += 1.0
    tradable = cnt > 0.0
    if int(tradable.sum()) < _MIN_NAMES:
        return None
    resid = acc / np.where(cnt > 0.0, cnt, 1.0)[None, :]

    # -- displacement: a slow spread level, not a recent return -----------
    scale = resid.std(axis=0)
    typical = float(np.median(scale[tradable]))
    scale = np.where(scale > _EPS, scale, typical if typical > _EPS else 1.0)
    kern = 1.0 - np.abs(np.arange(_L, dtype=float) - 0.5 * (_L - 1)) / (0.5 * (_L - 1))
    kern = np.clip(kern, 0.0, None)
    norm = float(np.sqrt(float((kern * kern).sum())))
    disp = (kern[::-1] @ resid[-_L:, :]) / (scale * norm)
    disp = np.where(np.isfinite(disp), disp, 0.0)

    # -- the partition the book is made neutral to ------------------------
    lab_n = cuts.get(_NEUTRAL_CUT)
    if lab_n is None:
        lab_n = np.zeros(n_sym, dtype=np.int64)
    big = np.zeros(n_sym, dtype=bool)
    for c in range(int(lab_n.max()) + 1):
        idx = np.flatnonzero(lab_n == c)
        if idx.size >= _M_MIN:
            big[idx] = True

    active = tradable & big & np.isfinite(disp)
    if int(active.sum()) < _MIN_NAMES:
        return None

    centred = np.where(active, disp, 0.0)
    for c in range(int(lab_n.max()) + 1):
        idx = np.flatnonzero((lab_n == c) & active)
        if idx.size >= _M_MIN:
            centred[idx] -= centred[idx].mean()
    sd = float(centred[active].std())
    if sd <= _EPS:
        return None
    z = np.where(active, np.clip(centred / sd, -_Z_CLIP, _Z_CLIP), 0.0)

    price = _SIGN * np.sign(z) * np.maximum(np.abs(z) - _Z_ENTER, 0.0)
    price = _unit(price * taper, active)

    # -- funding tilt: carry and crowding, at no turnover cost ------------
    fund = np.zeros(n_sym, dtype=float)
    try:
        fmap = _funding_means(context.funding)
        if fmap:
            rate = np.array([fmap.get(s, np.nan) for s in names], dtype=float)
            have = np.isfinite(rate) & active
            if int(have.sum()) >= _MIN_NAMES:
                f = np.where(have, rate, 0.0)
                for c in range(int(lab_n.max()) + 1):
                    idx = np.flatnonzero((lab_n == c) & have)
                    if idx.size >= _M_MIN:
                        f[idx] -= f[idx].mean()
                    else:
                        f[idx] = 0.0
                fs = float(f[have].std())
                if fs > _EPS:
                    tilt = -np.clip(f / fs, -_FUND_CLIP, _FUND_CLIP)
                    fund = _unit(np.where(have, tilt, 0.0) * taper, active)
    except Exception:
        fund = np.zeros(n_sym, dtype=float)

    raw = np.where(active, price + _ALPHA * fund, 0.0)
    for _ in range(2):
        _group_demean(raw, lab_n, taper, active, _M_MIN)
        _global_demean(raw, taper, active)
        raw = np.where(active, raw, 0.0)

    weights = _finalise(raw, taper, active)
    if weights is None:
        return None

    book = {sym: 0.0 for sym in eligible}
    for pos, sym in enumerate(names):
        value = float(weights[pos])
        if np.isfinite(value) and abs(value) > _DUST:
            book[sym] = value
    return book


class ClusterRelativeValue:
    """Stateless: every number is recomputed from the past-only rows supplied."""

    __slots__ = ()

    def target_weights(self, context, *, seed):
        try:
            return _decide(context)
        except Exception:
            # A degenerate cross-section at one decision should cost that
            # decision, not the run.  Holding beats churning to flat and back.
            return None


def build_strategy():
    return ClusterRelativeValue()
