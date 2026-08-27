"""team-06 -- cluster relative value.  Discovery-phase candidate (trial T1).

Mandate: rolling correlation clusters, trading deviation from cluster mean.
Sector-neutral statistical arbitrage where the sectors are discovered rather
than declared.

This is the preregistered baseline of lane/scouting/THESIS.md 4.4, at the
declared midpoint defaults and nothing else:

    W = 180 (60d)   q_max = 0.4    K = MP-adaptive   m_min = 5
    H = 3 (1d)      Z = within-cluster cross-sectional
    S = 3           z_enter = 0.75
    alpha = 0       gamma = 0      sign_mode = contrarian

alpha = 0 and gamma = 0 mean the funding tilt and the liquidity weighting are
switched off here.  They are declared knobs (thesis 4.3, axes 9 and 10) held
at their neutral setting, not omissions.

At each decision the pipeline is exactly thesis 4.1:

    eligible -> liquidity-capped universe -> 8h log-return panel (winsorized)
    -> Spearman correlation -> Marchenko-Pastur eigenvalue clipping
    -> market (top) eigenvector removed -> average-linkage clustering into K
    -> H-bar return minus own cluster's equal-weight H-bar return
    -> within-cluster cross-sectional z, clipped, averaged over S decisions
    -> contrarian sign, dead-zone -> cluster-neutral, market-neutral weights.

No persistent state: every number is recomputed from the past-only rows in the
context at each call.  No RNG, no symbol identity, no absolute dates, no
volatility targeting -- the book is normalised to a fixed gross of 1.0 and the
engine's common ex-ante risk unit rescales it from there.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Declared parameter surface (thesis 4.3), pinned at the T1 configuration.
# --------------------------------------------------------------------------
_W = 180          # correlation window, in 8h bars (60 days)
_Q_MAX = 0.4      # cap on the correlation matrix aspect ratio N / T
_M_MIN = 5        # smallest cluster that is allowed to trade
_H = 3            # deviation lookback, in bars (1 day)
_S = 3            # decisions averaged in the smoothed signal
_Z_ENTER = 0.75   # entry dead-zone, applied as a soft threshold
_SIGN = -1.0      # sign_mode = contrarian

# Frozen by fiat (thesis 4.2).
_WINSOR = 0.01    # 1% / 99% winsorization of returns within the window
_Z_CLIP = 3.0     # z clip
_MAX_W = 0.10     # per-symbol exposure cap
_K_LO = 2         # MP-adaptive K is clamped to [2, 10]
_K_HI = 10
_MIN_NAMES = 12   # below this the cross-section cannot support a portfolio
_EPS = 1e-12


# --------------------------------------------------------------------------
# Pure helpers
# --------------------------------------------------------------------------
def _rank_columns(a: np.ndarray) -> np.ndarray:
    """Average ranks down each column; tied values share their mean rank.

    Pearson correlation of these ranks is Spearman correlation.  Ties matter
    here: a thin contract can print the same close for several bars, and
    ordinal tie-breaking would turn those flat stretches into arbitrary
    orderings.
    """
    t, n = a.shape
    order = np.argsort(a, axis=0, kind="mergesort")
    srt = np.take_along_axis(a, order, axis=0)
    pos = np.arange(t, dtype=float)[:, None]

    starts_new = np.empty((t, n), dtype=bool)
    starts_new[0, :] = True
    starts_new[1:, :] = srt[1:, :] != srt[:-1, :]

    ends_new = np.empty((t, n), dtype=bool)
    ends_new[:-1, :] = starts_new[1:, :]
    ends_new[-1, :] = True

    starts = np.maximum.accumulate(np.where(starts_new, pos, 0.0), axis=0)
    ends = np.minimum.accumulate(
        np.where(ends_new, pos, float(t))[::-1, :], axis=0
    )[::-1, :]

    ranks = np.empty((t, n), dtype=float)
    np.put_along_axis(ranks, order, 0.5 * (starts + ends), axis=0)
    return ranks


def _correlation(a: np.ndarray) -> np.ndarray:
    """Column-wise Pearson correlation, safe on constant columns."""
    x = a - a.mean(axis=0, keepdims=True)
    sd = np.sqrt((x * x).sum(axis=0))
    x = x / np.where(sd > _EPS, sd, 1.0)
    c = x.T @ x
    c = 0.5 * (c + c.T)
    np.fill_diagonal(c, 1.0)
    return np.clip(c, -1.0, 1.0)


def _denoise_and_deflate(c: np.ndarray, q: float) -> tuple[np.ndarray, int]:
    """Marchenko-Pastur eigenvalue clipping, then removal of the market mode.

    Returns the residual correlation matrix (renormalised to a unit diagonal)
    and the number of eigenvalues above the MP edge, which is the F1b
    structure-above-noise diagnostic and also supplies the adaptive K.

    Laloux et al. (thesis 2.2): the bulk of the empirical spectrum is
    indistinguishable from a matrix with no correlation structure at all, so
    clustering on the raw sample matrix clusters noise geometry.  Clipping the
    bulk to its own mean preserves the trace.  Dropping the top eigenvector
    afterwards is the market-factor removal of thesis 2.4 / 2.11 -- without it
    the discovered partition is mostly a beta sort.
    """
    vals, vecs = np.linalg.eigh(0.5 * (c + c.T))
    order = np.argsort(vals)[::-1]
    vals = vals[order]
    vecs = vecs[:, order]

    edge = (1.0 + np.sqrt(q)) ** 2
    above = vals > edge
    n_above = int(above.sum())

    bulk = ~above
    if bulk.any():
        vals = vals.copy()
        vals[bulk] = float(vals[bulk].mean())

    # Drop the leading (market) mode and rebuild from the denoised remainder.
    resid = (vecs[:, 1:] * vals[1:]) @ vecs[:, 1:].T
    scale = np.sqrt(np.clip(np.diag(resid), 1e-10, None))
    rc = resid / scale[:, None] / scale[None, :]
    rc = np.clip(0.5 * (rc + rc.T), -1.0, 1.0)
    np.fill_diagonal(rc, 1.0)
    return rc, n_above


def _average_linkage(dist: np.ndarray, k: int) -> np.ndarray:
    """Agglomerative clustering, average linkage, cut at k groups.

    Lance-Williams update on a dense distance matrix.  N is capped at
    q_max * W (72 here), so the naive O(N^3) form is cheap.
    """
    n = dist.shape[0]
    m = np.array(dist, dtype=float, copy=True)
    m = np.where(np.isfinite(m), m, np.inf)
    np.fill_diagonal(m, np.inf)

    sizes = np.ones(n, dtype=float)
    labels = np.arange(n)
    live = n

    while live > k:
        flat = int(np.argmin(m))
        i, j = flat // n, flat % n
        if not np.isfinite(m[i, j]):
            break
        wi, wj = sizes[i], sizes[j]
        row = (wi * m[i, :] + wj * m[j, :]) / (wi + wj)
        row[i] = np.inf
        row[j] = np.inf
        m[i, :] = row
        m[:, i] = row
        m[j, :] = np.inf
        m[:, j] = np.inf
        sizes[i] = wi + wj
        labels[labels == j] = i
        live -= 1

    _, compact = np.unique(labels, return_inverse=True)
    return np.asarray(compact, dtype=int)


def _select_universe(bars, eligible, window: int, n_max: int) -> list[str]:
    """Point-in-time universe: enough history, then the most liquid n_max.

    The aspect-ratio cap is not a taste parameter.  With ~150-250 eligible
    perps and a 180-bar window the sample correlation matrix would be
    rank-deficient and its partition meaningless (thesis 2.2).
    """
    scored: list[tuple[str, float]] = []
    for sym in eligible:
        if sym not in bars:
            continue
        frame = bars[sym]
        if frame is None or len(frame) < window + 1:
            continue
        qv = np.asarray(
            frame["quote_volume"].iloc[-window:].to_numpy(), dtype=float
        )
        qv = qv[np.isfinite(qv)]
        if qv.size == 0:
            continue
        med = float(np.median(qv))
        if not np.isfinite(med) or med <= 0.0:
            continue
        scored.append((sym, med))

    if len(scored) < _MIN_NAMES:
        return []
    vols = np.array([v for _, v in scored], dtype=float)
    order = np.argsort(-vols, kind="mergesort")[:n_max]
    return [scored[i][0] for i in order]


def _build_panel(bars, names: list[str], rows: int) -> pd.DataFrame:
    """Align closes across symbols on ``open_time``, never on the row index.

    Each per-symbol frame carries a positional RangeIndex and symbols have
    unequal history, so concatenating on the default index yields disjoint
    integer ranges and an almost entirely NaN panel.  ``open_time`` is the
    only correct alignment key.
    """
    tail = rows + 25
    keys: list[str] = []
    series: list[pd.Series] = []
    for sym in names:
        frame = bars[sym]
        cut = frame.iloc[max(0, len(frame) - tail):]
        cut = cut.drop_duplicates(subset="open_time", keep="last")
        keys.append(sym)
        series.append(
            pd.Series(
                np.asarray(cut["close"].to_numpy(), dtype=float),
                index=pd.Index(cut["open_time"].to_numpy()),
            )
        )
    if not keys:
        return pd.DataFrame()

    panel = pd.concat(series, axis=1, keys=keys).sort_index()

    # Drop grid rows almost nobody trades on, then forward-fill genuine gaps
    # (a missing bar is a bar with no observed price change, not a hole).
    present = panel.notna().sum(axis=1).to_numpy()
    panel = panel.loc[present >= max(2, int(0.5 * panel.shape[1]))]
    panel = panel.ffill().iloc[-rows:]
    if panel.shape[0] < rows:
        return pd.DataFrame()
    return panel.loc[:, panel.notna().all(axis=0).to_numpy()]


def _cluster_z(returns: np.ndarray, members: np.ndarray) -> np.ndarray:
    """Smoothed within-cluster z of the H-bar deviation from the cluster mean.

    The residual is the H-bar return minus the cluster's equal-weight H-bar
    return (beta fixed at 1: estimating a beta per name on 180 bars adds more
    noise than it removes).  The same residual is measured at each of the last
    S decision boundaries and the z-scores averaged, which is how the signal
    is made slowly varying without remembering anything.
    """
    sub = returns[:, members]
    resid = sub - sub.mean(axis=1, keepdims=True)
    t = resid.shape[0]

    acc = np.zeros(members.size, dtype=float)
    for lag in range(_S):
        end = t - lag
        cum = resid[end - _H:end, :].sum(axis=0)
        sd = float(cum.std())
        if sd <= _EPS:
            continue
        acc += np.clip(cum / sd, -_Z_CLIP, _Z_CLIP)
    return acc / float(_S)


def _finalise(raw: np.ndarray) -> np.ndarray:
    """Normalise to gross 1.0 and enforce the per-symbol cap."""
    gross = float(np.abs(raw).sum())
    if gross <= _EPS:
        return np.zeros_like(raw)
    w = raw / gross

    for _ in range(12):
        if not (np.abs(w) > _MAX_W).any():
            break
        w = np.clip(w, -_MAX_W, _MAX_W)
        gross = float(np.abs(w).sum())
        if gross <= _EPS:
            return np.zeros_like(raw)
        w = w / gross
    w = np.clip(w, -_MAX_W, _MAX_W)

    net = float(w.sum())
    if abs(net) > 0.20:
        w = np.clip(w - net / float(w.size), -_MAX_W, _MAX_W)
        gross = float(np.abs(w).sum())
        if gross > 1.0:
            w = w / gross
    return w


# --------------------------------------------------------------------------
# Decision
# --------------------------------------------------------------------------
def _decide(context) -> dict:
    bars = context.bars
    n_max = int(_Q_MAX * _W)

    names = _select_universe(bars, context.eligible_symbols, _W, n_max)
    if len(names) < _MIN_NAMES:
        return {}

    panel = _build_panel(bars, names, _W + 1)
    if panel.shape[1] < _MIN_NAMES:
        return {}

    px = np.asarray(panel.to_numpy(), dtype=float)
    # Drop names with a bad print rather than losing the whole decision to one.
    usable = np.isfinite(px).all(axis=0) & (px > 0.0).all(axis=0)
    if int(usable.sum()) < _MIN_NAMES:
        return {}
    px = px[:, usable]
    syms = [str(c) for c in panel.columns[usable]]

    rets = np.diff(np.log(px), axis=0)
    rets = np.where(np.isfinite(rets), rets, 0.0)
    lo = np.quantile(rets, _WINSOR, axis=0)
    hi = np.quantile(rets, 1.0 - _WINSOR, axis=0)
    rets = np.clip(rets, lo, hi)

    n_obs, n_sym = rets.shape
    if n_obs < _H + _S or n_sym < _MIN_NAMES:
        return {}

    corr = _correlation(_rank_columns(rets))
    resid_corr, n_above = _denoise_and_deflate(corr, float(n_sym) / float(n_obs))

    # K = 1 + (eigenvalues above the MP edge, excluding the market mode).
    k = min(max(n_above, _K_LO), _K_HI)
    k = min(k, max(_K_LO, n_sym // _M_MIN))

    dist = np.sqrt(np.clip(2.0 * (1.0 - resid_corr), 0.0, None))
    labels = _average_linkage(dist, k)

    signal = np.zeros(n_sym, dtype=float)
    traded = np.zeros(n_sym, dtype=bool)
    for lab in np.unique(labels):
        members = np.flatnonzero(labels == lab)
        if members.size < _M_MIN:
            continue          # undersized clusters are not traded
        signal[members] = _cluster_z(rets, members)
        traded[members] = True

    if int(traded.sum()) < _MIN_NAMES:
        return {}

    # Contrarian, with the dead-zone applied as a soft threshold so the
    # ranking inside the surviving tails is preserved.
    raw = _SIGN * np.sign(signal) * np.maximum(np.abs(signal) - _Z_ENTER, 0.0)
    raw = np.where(traded, raw, 0.0)

    # Cluster-neutral by construction, then market-neutral.
    for lab in np.unique(labels[traded]):
        members = np.flatnonzero((labels == lab) & traded)
        raw[members] -= raw[members].mean()
    idx = np.flatnonzero(traded)
    raw[idx] -= raw[idx].mean()

    weights = _finalise(raw[idx])
    return {
        syms[idx[p]]: float(weights[p])
        for p in range(idx.size)
        if np.isfinite(weights[p]) and abs(weights[p]) > 1e-6
    }


class ClusterRelativeValue:
    """Stateless cluster-residual reversal book.

    Holds no attributes: every decision is recomputed from the past-only rows
    of the context, which is what exact-replay determinism requires.
    """

    __slots__ = ()

    def target_weights(self, context, *, seed):
        try:
            return _decide(context)
        except Exception:
            # A degenerate cross-section at a single decision (a failed
            # eigendecomposition, a collapsed panel) should cost that
            # decision, not the run.  A systematic failure is unmistakable in
            # the packet: gross exposure and turnover are zero everywhere.
            return {}


def build_strategy():
    return ClusterRelativeValue()
