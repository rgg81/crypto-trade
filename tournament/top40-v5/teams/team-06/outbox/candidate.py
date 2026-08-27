"""team-06 -- cluster relative value.

Discovery baseline. This is trial T1 of the preregistered surface in
``lane/scouting/THESIS.md`` section 4.4: the thesis at its midpoint defaults, with every
optional axis switched off (alpha = 0 funding tilt, gamma = 0 liquidity weighting,
contrarian sign, cross-sectional z). Nothing here is fitted to a result -- there are no
results yet.

Pipeline at each decision, following THESIS section 4.1:

  1. eligible symbols with at least ``CORR_WINDOW + 1`` bars of close history
  2. rank by median quote volume over the window, keep the top ``floor(q_max * W)``
  3. aligned panel of log close-to-close returns, winsorized 1%/99% within the window
  4. Spearman correlation -> denoise by clipping the Marchenko-Pastur bulk to its mean
  5. remove the top (market) eigenvector, renormalize to correlation form
  6. distance ``d = sqrt(2 (1 - rho))``, average-linkage agglomerative clustering into K
  7. residual = own H-bar return minus its cluster's equal-weight mean H-bar return
  8. within-cluster z, clipped, averaged over the last S decisions, dead-zone entry gate
  9. contrarian sign, demean within cluster then globally, budget gross subject to the
     per-name cap

No persistent state, no randomness, no symbol identity, no date literals, no embedded
data. The only inputs are the past-only rows carried on the context.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

# --- frozen by fiat (THESIS section 4.2) ------------------------------------------
WINSOR_LO = 0.01
WINSOR_HI = 0.99
Z_CLIP = 3.0
K_FLOOR = 2
K_CEIL = 10

# --- trial T1 settings on the declared surface (THESIS section 4.3) ----------------
CORR_WINDOW = 180  # W, 8h bars ~ 60 days
ASPECT_CAP = 0.4  # q_max, cap on N/T so the sample correlation matrix is not noise geometry
MIN_CLUSTER = 5  # m_min, clusters smaller than this are not traded
DEV_LOOKBACK = 3  # H, deviation measured over 3 bars ~ 1 day
SMOOTH = 3  # S, decisions averaged
Z_ENTER = 0.75  # dead-zone, applied as an entry gate on the smoothed z

# --- book construction (engine owns the risk unit; these are shape, not risk) -------
GROSS_TARGET = 0.98  # headroom under the hard 1.0 gross cap
NAME_CAP = 0.099  # headroom under the hard 0.10 per-name cap
NET_GUARD = 0.20  # headroom under the hard 0.25 net cap
WEIGHT_FLOOR = 1e-6

# --- numerical hygiene --------------------------------------------------------------
MIN_NAMES = 20  # below this the cross-section cannot support a partition
MIN_ROWS = 91  # 90 usable returns, the floor of the declared W range
ROW_COVERAGE = 0.9  # a timestamp is usable if this share of names has a bar on it
EPS = 1e-12


def _closing_panel(bars, symbols, rows_needed):
    """Aligned, strictly positive close panel over the common timestamp grid."""
    columns = {}
    for symbol in symbols:
        frame = bars.get(symbol)
        if frame is None or len(frame) < rows_needed:
            continue
        if "close" not in frame.columns:
            continue
        series = frame["close"].iloc[-rows_needed:].astype(float)
        if series.index.has_duplicates:
            series = series[~series.index.duplicated(keep="last")]
        columns[symbol] = series
    if len(columns) < MIN_NAMES:
        return None

    panel = pd.concat(columns, axis=1).sort_index()
    coverage = panel.notna().sum(axis=1) / float(panel.shape[1])
    panel = panel.loc[coverage >= ROW_COVERAGE]
    panel = panel.iloc[-rows_needed:]
    if panel.shape[0] < MIN_ROWS:
        return None

    usable = panel.notna().all(axis=0) & (panel.min(axis=0) > 0.0)
    panel = panel.loc[:, usable]
    if panel.shape[1] < MIN_NAMES:
        return None
    return panel


def _liquidity_ranked(bars, symbols, window, min_history, keep):
    """Top ``keep`` names, by median quote volume, among those with enough history."""
    scored = []
    for symbol in symbols:
        frame = bars.get(symbol)
        if frame is None or len(frame) < min_history:
            continue
        if "quote_volume" not in frame.columns or "close" not in frame.columns:
            continue
        median = float(frame["quote_volume"].iloc[-window:].astype(float).median())
        if not np.isfinite(median) or median <= 0.0:
            continue
        scored.append((symbol, median))
    scored.sort(key=lambda pair: (-pair[1], pair[0]))
    return [symbol for symbol, _ in scored[:keep]]


def _spearman(returns):
    """Rank correlation of the columns, plus the surviving column mask."""
    ranks = returns.rank(axis=0, method="average").to_numpy(dtype=float)
    centred = ranks - ranks.mean(axis=0, keepdims=True)
    scale = centred.std(axis=0, ddof=0)
    alive = scale > EPS
    if int(alive.sum()) < MIN_NAMES:
        return None, alive
    centred = centred[:, alive] / scale[alive]
    corr = (centred.T @ centred) / float(centred.shape[0])
    corr = np.clip(corr, -1.0, 1.0)
    np.fill_diagonal(corr, 1.0)
    return corr, alive


def _denoise_and_detone(corr, q):
    """MP eigenvalue clipping (trace preserved), then removal of the market mode.

    Returns the detoned correlation matrix, a mask of names retaining usable residual
    variance, and the count of signal eigenvalues beyond the top one.
    """
    values, vectors = np.linalg.eigh(corr)
    order = np.argsort(values)[::-1]
    values = values[order]
    vectors = vectors[:, order]

    edge = (1.0 + np.sqrt(q)) ** 2
    signal = values > edge
    clipped = values.copy()
    if (~signal).any():
        clipped[~signal] = values[~signal].mean()
    extra_modes = max(int(signal.sum()) - 1, 0)

    detoned_values = clipped.copy()
    detoned_values[0] = 0.0
    residual = (vectors * detoned_values) @ vectors.T

    variance = np.diag(residual).copy()
    keep = variance > 1e-8
    if int(keep.sum()) < MIN_NAMES:
        return None, keep, extra_modes

    residual = residual[np.ix_(keep, keep)]
    scale = np.sqrt(np.clip(np.diag(residual), EPS, None))
    detoned = residual / np.outer(scale, scale)
    detoned = np.clip(detoned, -1.0, 1.0)
    np.fill_diagonal(detoned, 1.0)
    return detoned, keep, extra_modes


def _average_linkage(distance, k):
    """UPGMA agglomerative clustering cut at ``k`` groups. Deterministic tie-breaking."""
    n = distance.shape[0]
    if k >= n or n <= 1:
        return np.arange(n)

    working = np.array(distance, dtype=float, copy=True)
    working[~np.isfinite(working)] = np.inf
    np.fill_diagonal(working, np.inf)

    sizes = np.ones(n, dtype=float)
    members = [[index] for index in range(n)]
    alive = n

    while alive > k:
        flat = int(np.argmin(working))
        left, right = flat // n, flat % n
        if not np.isfinite(working[left, right]):
            break
        if left > right:
            left, right = right, left

        weight_left, weight_right = sizes[left], sizes[right]
        merged = (weight_left * working[left] + weight_right * working[right]) / (
            weight_left + weight_right
        )
        working[left] = merged
        working[:, left] = merged
        working[left, left] = np.inf
        working[right, :] = np.inf
        working[:, right] = np.inf

        sizes[left] = weight_left + weight_right
        members[left] = members[left] + members[right]
        members[right] = []
        alive -= 1

    labels = np.zeros(n, dtype=int)
    cluster_id = 0
    for index in range(n):
        if members[index]:
            for member in members[index]:
                labels[member] = cluster_id
            cluster_id += 1
    return labels


def _cluster_scores(returns, labels, tradeable):
    """Within-cluster demeaned return, standardized by within-cluster dispersion."""
    scores = np.zeros_like(returns)
    for cluster_id in tradeable:
        index = np.flatnonzero(labels == cluster_id)
        block = returns[index]
        if not np.isfinite(block).all():
            continue
        residual = block - block.mean()
        dispersion = residual.std(ddof=1)
        if not np.isfinite(dispersion) or dispersion <= EPS:
            continue
        scores[index] = np.clip(residual / dispersion, -Z_CLIP, Z_CLIP)
    return scores


def _budget(raw, gross, cap):
    """Scale to the gross budget under a per-name cap, by water-filling."""
    magnitude = np.abs(raw)
    live = int((magnitude > 0.0).sum())
    if live == 0:
        return np.zeros_like(raw)
    if live * cap <= gross:
        return np.sign(raw) * cap

    high = 1.0
    for _ in range(200):
        if np.minimum(high * magnitude, cap).sum() >= gross:
            break
        high *= 2.0
    low = 0.0
    for _ in range(80):
        mid = 0.5 * (low + high)
        if np.minimum(mid * magnitude, cap).sum() < gross:
            low = mid
        else:
            high = mid
    return np.sign(raw) * np.minimum(high * magnitude, cap)


class ClusterRelativeValue:
    """Cluster-neutral residual reversal. Stateless across decisions by construction."""

    def target_weights(self, context, *, seed) -> Mapping[str, float] | None:
        bars = context.bars
        eligible = [
            symbol
            for symbol in context.eligible_symbols
            if isinstance(symbol, str) and not symbol.startswith("__")
        ]
        if len(eligible) < MIN_NAMES:
            return {}

        rows_needed = CORR_WINDOW + 1
        keep = max(int(ASPECT_CAP * CORR_WINDOW), MIN_NAMES)
        shortlist = _liquidity_ranked(bars, eligible, CORR_WINDOW, rows_needed, keep)
        if len(shortlist) < MIN_NAMES:
            return {}

        panel = _closing_panel(bars, shortlist, rows_needed)
        if panel is None:
            return {}

        # Enforce q_max against the window actually available, not the requested one:
        # a rank-deficient correlation matrix has cluster structure that is pure noise
        # geometry (THESIS section 2.2). Panel columns are already volume-ordered.
        allowed = max(int(ASPECT_CAP * (panel.shape[0] - 1)), MIN_NAMES)
        if panel.shape[1] > allowed:
            panel = panel.iloc[:, :allowed]

        names = list(panel.columns)
        log_close = np.log(panel.to_numpy(dtype=float))
        returns = pd.DataFrame(np.diff(log_close, axis=0), columns=names)
        if returns.shape[0] < MIN_ROWS - 1:
            return {}

        lower = returns.quantile(WINSOR_LO, axis=0)
        upper = returns.quantile(WINSOR_HI, axis=0)
        returns = returns.clip(lower=lower, upper=upper, axis=1)

        corr, alive = _spearman(returns)
        if corr is None:
            return {}
        names = [name for name, ok in zip(names, alive) if ok]
        log_close = log_close[:, alive]

        periods = float(returns.shape[0])
        q = float(corr.shape[0]) / periods
        detoned, retained, extra_modes = _denoise_and_detone(corr, q)
        if detoned is None:
            return {}
        names = [name for name, ok in zip(names, retained) if ok]
        log_close = log_close[:, retained]

        distance = np.sqrt(np.clip(2.0 * (1.0 - detoned), 0.0, None))
        k = int(np.clip(1 + extra_modes, K_FLOOR, K_CEIL))
        labels = _average_linkage(distance, k)

        unique, counts = np.unique(labels, return_counts=True)
        tradeable = [
            int(cluster_id)
            for cluster_id, size in zip(unique, counts)
            if size >= MIN_CLUSTER
        ]
        if not tradeable:
            return {}

        n_rows = log_close.shape[0]
        accumulated = np.zeros(log_close.shape[1])
        used = 0
        for lag in range(SMOOTH):
            end = n_rows - 1 - lag
            start = end - DEV_LOOKBACK
            if start < 0:
                break
            horizon_return = log_close[end] - log_close[start]
            if not np.isfinite(horizon_return).all():
                continue
            accumulated += _cluster_scores(horizon_return, labels, tradeable)
            used += 1
        if used == 0:
            return {}
        smoothed = accumulated / float(used)

        # Dead-zone as an entry gate, with the weight transform linear in the clipped,
        # smoothed z (THESIS section 4.2). A name entering at the gate carries the
        # smallest weight in the book, so the discontinuity is bounded in book terms.
        gated = np.where(np.abs(smoothed) >= Z_ENTER, smoothed, 0.0)
        raw = -gated  # contrarian: fade the deviation from the cluster

        # Neutralize within each cluster over that cluster's active names, then globally.
        # Demeaning over the active subset keeps gated-out names at exactly zero while
        # still making every cluster's contribution sum to zero.
        traded = np.zeros(raw.shape[0], dtype=bool)
        for cluster_id in tradeable:
            index = np.flatnonzero((labels == cluster_id) & (raw != 0.0))
            if index.size < 2:
                raw[np.flatnonzero(labels == cluster_id)] = 0.0
                continue
            traded[index] = True
            raw[index] -= raw[index].mean()
        raw[~traded] = 0.0
        if traded.sum() > 1:
            raw[traded] -= raw[traded].mean()
        else:
            return {}

        weights = _budget(raw, GROSS_TARGET, NAME_CAP)

        # The per-name cap can bind asymmetrically and reintroduce net exposure. Demean
        # the capped weights over their own support and re-budget once.
        if abs(float(weights.sum())) > NET_GUARD:
            support = np.flatnonzero(weights != 0.0)
            if support.size > 1:
                weights[support] -= weights[support].mean()
                weights = _budget(weights, GROSS_TARGET, NAME_CAP)
            if abs(float(weights.sum())) > NET_GUARD:
                return {}

        book = {}
        for name, weight in zip(names, weights):
            value = float(weight)
            if np.isfinite(value) and abs(value) >= WEIGHT_FLOOR:
                book[name] = value
        if not book:
            return {}

        gross = sum(abs(value) for value in book.values())
        if gross > GROSS_TARGET:
            book = {name: value * (GROSS_TARGET / gross) for name, value in book.items()}
        return book


def build_strategy():
    return ClusterRelativeValue()
