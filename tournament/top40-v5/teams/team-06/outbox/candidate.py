"""team-06 -- cluster relative value.

Statistical arbitrage on the deviation of a perpetual's *cumulative* return from the
equal-weight mean of the correlation cluster it is discovered to belong to.

Pipeline at each decision (all quantities recomputed from past-only rows):

  1. snap the view to a coarse decision grid derived from bar counts, so the target book
     is piecewise constant between weekly refreshes;
  2. select the liquid universe, capped by the matrix aspect ratio N/T;
  3. Spearman correlation of winsorised 8h log returns;
  4. Marchenko-Pastur eigenvalue clipping, then removal of the top (market) eigenvector;
  5. average-linkage agglomerative clustering into an MP-adaptive number of groups;
  6. leave-one-out cluster-mean residual return series per name;
  7. Ornstein-Uhlenbeck fit of the cumulative residual -> s-score, with a mean-reversion
     speed filter;
  8. contrarian dead-zoned s-score, tilted by cluster-relative funding;
  9. within-cluster then global demean, gross normalisation and per-name caps.

No persistent state, no randomness, no absolute dates, no symbol identity, no price levels.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

# --- estimation windows (8h bars) ---------------------------------------------------
CORR_WINDOW = 180  # W: correlation window, 60 days
FALLBACK_WINDOW = 90  # used only if too few names carry W bars of history
OU_WINDOW = 90  # M: OU fit window on the cumulative residual, 30 days
ASPECT_CAP = 0.4  # q_max: N <= q_max * W, keeps the sample matrix out of the noise regime

# --- clustering ---------------------------------------------------------------------
MIN_CLUSTER = 5  # m_min: clusters smaller than this are not traded
MAX_CLUSTERS = 10
MIN_NAMES = 12

# --- signal -------------------------------------------------------------------------
COVERAGE = 0.85  # minimum fraction of finite returns for a column to be usable
WINSOR = 0.01
Z_ENTER = 0.75  # dead zone on the s-score
Z_CLIP = 3.0
B_MAX = 0.97  # OU: reversion faster than half the fit window
FUND_TILT = 0.5  # alpha: weight on the cluster-relative funding deviation
FUND_TAIL = 21  # funding settlements averaged
FUND_CLIP = 2.0

# --- trading cadence and portfolio --------------------------------------------------
REBAL_GRID = 21  # decisions between signal refreshes (7 days)
SKIP_BARS = 3  # bars excluded from the signal (1 day)
NAME_CAP = 0.06  # soft per-name cap, below the 0.10 contract limit
HARD_NAME_CAP = 0.095
GROSS = 0.999
NET_CAP = 0.15
DUST = 1e-4


# ------------------------------------------------------------------------------------
# small pure helpers
# ------------------------------------------------------------------------------------
def _reference_length(bars) -> int:
    """Longest available history, used as a shift-invariant bar counter."""
    best = 0
    for frame in bars.values():
        n = len(frame)
        if n > best:
            best = n
    return best


def _median_quote_volume(frame, n_drop: int, window: int) -> float:
    col = frame["quote_volume"]
    if n_drop:
        keep = len(col) - n_drop
        if keep <= 0:
            return float("nan")
        col = col.iloc[:keep]
    arr = col.iloc[-window:].to_numpy(dtype="float64")
    if arr.size == 0:
        return float("nan")
    with np.errstate(invalid="ignore"):
        if not np.isfinite(arr).any():
            return float("nan")
        return float(np.nanmedian(arr))


def _close_panel(bars, names, rows):
    frames = {}
    for sym in names:
        frame = bars[sym]
        tail = frame.iloc[-rows:]
        stamps = pd.to_datetime(tail["open_time"].to_numpy(), utc=True)
        series = pd.Series(tail["close"].to_numpy(dtype="float64"), index=stamps)
        series = series[~series.index.duplicated(keep="last")]
        frames[sym] = series
    if not frames:
        return None
    return pd.concat(frames, axis=1).sort_index()


def _winsorise(mat, frac):
    with np.errstate(invalid="ignore"):
        lo = np.nanquantile(mat, frac, axis=0)
        hi = np.nanquantile(mat, 1.0 - frac, axis=0)
    lo = np.where(np.isfinite(lo), lo, -np.inf)
    hi = np.where(np.isfinite(hi), hi, np.inf)
    return np.clip(mat, lo, hi)


def _spearman(mat):
    """Rank correlation of the columns of ``mat`` (rows are time)."""
    ranks = pd.DataFrame(mat).rank(axis=0).to_numpy(dtype="float64")
    ranks -= ranks.mean(axis=0, keepdims=True)
    scale = ranks.std(axis=0, keepdims=True)
    scale = np.where(scale > 0.0, scale, 1.0)
    ranks /= scale
    corr = (ranks.T @ ranks) / float(ranks.shape[0])
    corr = 0.5 * (corr + corr.T)
    np.fill_diagonal(corr, 1.0)
    return np.clip(corr, -1.0, 1.0)


def _denoise_and_strip_market(corr, aspect):
    """MP-clip the noise bulk, drop the market eigenvector, renormalise to a correlation.

    Returns the residual correlation matrix and the number of informative directions
    remaining once the market direction is set aside.
    """
    edge = (1.0 + math.sqrt(max(aspect, 0.0))) ** 2
    vals, vecs = np.linalg.eigh(corr)
    bulk = vals < edge
    clipped = vals.copy()
    if bulk.any():
        clipped[bulk] = float(vals[bulk].mean())
    n_struct = int(np.count_nonzero(~bulk))
    clipped[-1] = 0.0  # eigh returns ascending order: the last is the market factor
    clipped = np.clip(clipped, 0.0, None)
    resid = (vecs * clipped) @ vecs.T
    diag = np.sqrt(np.clip(np.diag(resid), 1e-12, None))
    resid = resid / np.outer(diag, diag)
    resid = 0.5 * (resid + resid.T)
    np.fill_diagonal(resid, 1.0)
    return np.clip(resid, -1.0, 1.0), max(0, n_struct - 1)


def _average_linkage(dist, k):
    """Agglomerative average-linkage clustering down to ``k`` groups."""
    n = dist.shape[0]
    if k >= n:
        return np.arange(n)
    work = dist.astype("float64").copy()
    np.fill_diagonal(work, np.inf)
    alive = np.ones(n, dtype=bool)
    sizes = np.ones(n, dtype="float64")
    members = [[i] for i in range(n)]
    remaining = n
    while remaining > k:
        live = np.where(alive)[0]
        block = work[np.ix_(live, live)]
        flat = int(np.argmin(block))
        row, col = divmod(flat, live.size)
        i, j = int(live[row]), int(live[col])
        if i == j or not np.isfinite(work[i, j]):
            break
        merged = (sizes[i] * work[i, :] + sizes[j] * work[j, :]) / (sizes[i] + sizes[j])
        work[i, :] = merged
        work[:, i] = merged
        work[i, i] = np.inf
        work[j, :] = np.inf
        work[:, j] = np.inf
        sizes[i] += sizes[j]
        members[i] = members[i] + members[j]
        members[j] = []
        alive[j] = False
        remaining -= 1
    labels = np.zeros(n, dtype="int64")
    for tag, root in enumerate(np.where(alive)[0]):
        for member in members[root]:
            labels[member] = tag
    return labels


def _cluster_residuals(returns, labels, n_clusters):
    """Leave-one-out demeaning of each name against its own cluster."""
    resid = np.zeros_like(returns)
    tradable = np.zeros(returns.shape[1], dtype=bool)
    for tag in range(n_clusters):
        idx = np.where(labels == tag)[0]
        if idx.size < MIN_CLUSTER:
            continue
        block = returns[:, idx]
        total = block.sum(axis=1, keepdims=True)
        peers = (total - block) / float(idx.size - 1)
        resid[:, idx] = block - peers
        tradable[idx] = True
    return resid, tradable


def _ou_scores(resid, window):
    """Avellaneda-Lee s-score of the cumulative residual, with a reversion-speed filter."""
    block = resid[-window:, :]
    cum = np.cumsum(block, axis=0)
    lag, lead = cum[:-1, :], cum[1:, :]
    m_lag = lag.mean(axis=0)
    m_lead = lead.mean(axis=0)
    d_lag = lag - m_lag
    d_lead = lead - m_lead
    var = (d_lag * d_lag).sum(axis=0)
    cov = (d_lag * d_lead).sum(axis=0)
    safe_var = np.where(var > 0.0, var, 1.0)
    slope = np.where(var > 0.0, cov / safe_var, 1.0)
    intercept = m_lead - slope * m_lag
    err = lead - (intercept + slope * lag)
    dof = max(1, lag.shape[0] - 2)
    err_var = (err * err).sum(axis=0) / float(dof)

    gap = 1.0 - slope
    gap_sq = 1.0 - slope * slope
    good = (
        (var > 0.0)
        & (slope > 0.0)
        & (slope < B_MAX)
        & (err_var > 0.0)
        & (gap_sq > 1e-9)
        & (np.abs(gap) > 1e-6)
    )
    level = np.where(np.abs(gap) > 1e-6, intercept / np.where(np.abs(gap) > 1e-6, gap, 1.0), 0.0)
    spread = np.sqrt(np.maximum(err_var, 1e-30) / np.maximum(gap_sq, 1e-9))
    spread = np.where(spread > 0.0, spread, 1.0)
    score = (cum[-1, :] - level) / spread
    score = np.where(np.isfinite(score), score, 0.0)

    if int(good.sum()) < MIN_NAMES:
        # Numerical fallback: plain standardisation of the cumulative residual.
        centre = cum.mean(axis=0)
        scale = cum.std(axis=0)
        alt_good = scale > 0.0
        alt = np.where(alt_good, (cum[-1, :] - centre) / np.where(alt_good, scale, 1.0), 0.0)
        return np.where(np.isfinite(alt), alt, 0.0), alt_good
    return score, good


def _funding_means(funding, cutoff):
    out = {}
    if funding is None or len(funding) == 0:
        return out
    cols = set(funding.columns)
    if "symbol" not in cols or "funding_rate" not in cols:
        return out
    frame = funding.loc[:, [c for c in ("symbol", "funding_rate", "funding_time") if c in cols]]
    frame = frame.dropna(subset=["symbol", "funding_rate"])
    if len(frame) == 0:
        return out
    if "funding_time" in frame.columns:
        stamps = pd.to_datetime(frame["funding_time"], utc=True, errors="coerce")
        bound = pd.Timestamp(cutoff)
        bound = bound.tz_localize("UTC") if bound.tzinfo is None else bound.tz_convert("UTC")
        frame = frame.loc[stamps.notna() & (stamps <= bound)]
        if len(frame) == 0:
            return out
        frame = frame.assign(_stamp=stamps.loc[frame.index]).sort_values("_stamp")
    recent = frame.groupby("symbol", sort=False).tail(FUND_TAIL)
    means = recent.groupby("symbol", sort=False)["funding_rate"].mean()
    return {str(k): float(v) for k, v in means.items() if np.isfinite(v)}


def _standardise(vec, mask):
    if not mask.any():
        return vec
    scale = float(vec[mask].std())
    if scale > 0.0:
        return vec / scale
    return vec


def _shape_book(raw, labels, active, n_clusters):
    """Cluster-neutral, market-neutral, gross-normalised, capped."""
    weights = raw.copy()
    weights[~active] = 0.0
    for tag in range(n_clusters):
        idx = np.where((labels == tag) & active)[0]
        if idx.size >= MIN_CLUSTER:
            weights[idx] -= weights[idx].mean()
        else:
            weights[idx] = 0.0
    live = np.where(active)[0]
    if live.size == 0:
        return None
    weights[live] -= weights[live].mean()

    for _ in range(4):
        gross = float(np.abs(weights).sum())
        if gross <= 0.0:
            return None
        weights *= GROSS / gross
        weights = np.clip(weights, -NAME_CAP, NAME_CAP)
        weights[live] -= weights[live].mean()
        weights[~active] = 0.0

    gross = float(np.abs(weights).sum())
    if gross <= 0.0:
        return None
    if gross > GROSS:
        weights *= GROSS / gross
    weights = np.clip(weights, -HARD_NAME_CAP, HARD_NAME_CAP)

    net = float(weights.sum())
    if abs(net) > NET_CAP:
        weights[live] -= (net - math.copysign(NET_CAP, net)) / float(live.size)
        weights = np.clip(weights, -HARD_NAME_CAP, HARD_NAME_CAP)
    gross = float(np.abs(weights).sum())
    if gross > GROSS:
        weights *= GROSS / gross
    weights[np.abs(weights) < DUST] = 0.0
    if not np.isfinite(weights).all():
        return None
    return weights


# ------------------------------------------------------------------------------------
# the decision
# ------------------------------------------------------------------------------------
def _decide(context):
    bars = context.bars
    if not bars:
        return {}
    eligible = [str(s) for s in context.eligible_symbols]
    if not eligible:
        return {}
    eligible_set = set(eligible)
    flat = {sym: 0.0 for sym in eligible}

    ref_len = _reference_length(bars)
    if ref_len <= 0:
        return flat
    # Snap to a coarse decision grid. ``n_drop`` grows by one bar per decision inside a
    # block, so the observation window -- and therefore the target book -- is unchanged
    # until the grid advances. Derived from row counts only, so it is invariant to any
    # calendar shift.
    n_drop = (ref_len % REBAL_GRID) + SKIP_BARS

    window = 0
    candidates = []
    for trial in (CORR_WINDOW, FALLBACK_WINDOW):
        need = trial + 1 + n_drop
        found = [s for s, frame in bars.items() if len(frame) >= need]
        if len(found) >= MIN_NAMES:
            window, candidates = trial, found
            break
    if window == 0:
        return flat

    ranked = []
    for sym in candidates:
        med = _median_quote_volume(bars[sym], n_drop, window)
        if np.isfinite(med) and med > 0.0:
            ranked.append((med, sym))
    if len(ranked) < MIN_NAMES:
        return flat
    ranked.sort(key=lambda item: -item[0])
    cap = max(MIN_NAMES, int(ASPECT_CAP * window))
    names = [sym for _, sym in ranked[:cap]]

    panel = _close_panel(bars, names, window + 1 + n_drop + 8)
    if panel is None or panel.shape[1] < MIN_NAMES:
        return flat
    if n_drop:
        keep = len(panel) - n_drop
        if keep <= OU_WINDOW + 2:
            return flat
        panel = panel.iloc[:keep]
    panel = panel.iloc[-(window + 1):]
    if len(panel) < OU_WINDOW + 2:
        return flat

    panel = panel.where(panel > 0.0).ffill(limit=2)
    cutoff = panel.index[-1]
    names = [str(c) for c in panel.columns]
    prices = panel.to_numpy(dtype="float64")
    with np.errstate(invalid="ignore", divide="ignore"):
        returns = np.diff(np.log(prices), axis=0)

    finite = np.isfinite(returns)
    coverage = finite.sum(axis=0) / float(returns.shape[0])
    usable = (coverage >= COVERAGE) & np.isfinite(prices[-1])
    keep_idx = np.where(usable)[0]
    if keep_idx.size < MIN_NAMES:
        return flat
    names = [names[i] for i in keep_idx]
    returns = np.where(finite, returns, 0.0)[:, keep_idx]
    returns = _winsorise(returns, WINSOR)
    n_names, n_obs = returns.shape[1], returns.shape[0]

    corr = _spearman(returns)
    resid_corr, n_struct = _denoise_and_strip_market(corr, n_names / float(n_obs))

    n_clusters = min(MAX_CLUSTERS, max(2, 1 + n_struct))
    n_clusters = max(2, min(n_clusters, n_names // MIN_CLUSTER, n_names - 1))
    dist = np.sqrt(np.clip(2.0 * (1.0 - resid_corr), 0.0, None))
    labels = _average_linkage(dist, n_clusters)
    n_clusters = int(labels.max()) + 1

    resid, tradable = _cluster_residuals(returns, labels, n_clusters)
    if not tradable.any():
        return flat

    scores, reverting = _ou_scores(resid, min(OU_WINDOW, n_obs))
    eligible_mask = np.array([sym in eligible_set for sym in names], dtype=bool)
    active = tradable & reverting & eligible_mask & np.isfinite(scores)
    if int(active.sum()) < MIN_NAMES:
        # Too narrow to be a portfolio: stand aside rather than fail breadth on purpose.
        return flat

    clipped = np.clip(scores, -Z_CLIP, Z_CLIP)
    deviation = np.sign(clipped) * np.maximum(np.abs(clipped) - Z_ENTER, 0.0)
    price_signal = -deviation  # rich to its cluster -> short it
    price_signal[~active] = 0.0
    price_signal = _standardise(price_signal, active)

    fund_map = _funding_means(context.funding, cutoff)
    fund_signal = np.zeros(n_names, dtype="float64")
    if fund_map:
        raw_fund = np.array([fund_map.get(sym, np.nan) for sym in names], dtype="float64")
        has_fund = np.isfinite(raw_fund)
        for tag in range(n_clusters):
            idx = np.where((labels == tag) & active & has_fund)[0]
            if idx.size < MIN_CLUSTER:
                continue
            block = raw_fund[idx]
            scale = float(block.std())
            if scale > 0.0:
                fund_signal[idx] = np.clip((block - block.mean()) / scale, -FUND_CLIP, FUND_CLIP)
        fund_signal = -fund_signal  # crowded longs pay: be the short
        fund_signal = _standardise(fund_signal, active)

    combined = price_signal + FUND_TILT * fund_signal
    weights = _shape_book(combined, labels, active, n_clusters)
    if weights is None:
        return flat

    book = dict(flat)
    for sym, weight in zip(names, weights):
        if weight != 0.0 and sym in eligible_set:
            book[sym] = float(weight)
    return book


class ClusterRelativeValue:
    """Stateless: every decision is recomputed from the past-only rows it is handed."""

    def target_weights(self, context, *, seed):
        try:
            return _decide(context)
        except Exception:
            # Hold rather than churn if anything about the shape surprises us.
            return None


def build_strategy():
    return ClusterRelativeValue()
