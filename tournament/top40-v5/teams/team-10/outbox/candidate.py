"""team-10 -- taker-flow pressure (nomination).

Aggressor imbalance, accumulated and conditioned by three preset-sign resolution
variables, residualised against the contemporaneous price/volume state, and held
long enough that a flat 7.5 bps-per-unit-turnover charge cannot eat the edge.

The mechanism is unchanged from the refinement candidate.  The one substantive
change is the position filter, which is set from cost arithmetic recovered from
the two feedback packets -- not from any return, Sharpe or drawdown.

No network, no filesystem, no subprocess, no RNG, no embedded data, and no state
carried across decisions: every number below is recomputed from the past-only
rows streamed through DecisionContext.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Declared configuration.  See RATIONALE.md; the ensemble is the whole surface,
# there is no per-configuration selection anywhere in this file.
# ---------------------------------------------------------------------------

_COLS = ("close", "quote_volume", "taker_buy_quote_volume", "trade_count")

_ACCUM = (9, 21)                 # knob 2 (L): cost-feasible accumulation windows
_STD = (90, 360)                 # knob 3 (W): trailing standardisation windows
_NORMS = ("ratio", "trailing")   # knob 1 (N): flow normalisation fork

_WINSOR = 3.0                    # fixed, thesis 5.3.3
_HALFLIFE = 24.0                 # bars (8 days); position-level linear low-pass
_SMOOTH = 96                     # bars retained for the filter (4 half-lives)
_RESID = 192                     # bars pooled into the residualising regression
_MIN_OBS = 60                    # minimum pooled rows before residualising

_HIST = 620                      # panel depth: max(L + W) + _RESID + headroom
_MIN_HISTORY = 130               # bars a symbol needs before it can be held

_GROSS = 1.0
_MAX_W = 0.10
_MAX_NET = 0.25
_MIN_NAMES = 6
_EPS = 1e-12

_RESERVED = "__crypto_trade_rebalance__"


# ---------------------------------------------------------------------------
# Pure array helpers.  All windows are strictly trailing with min_periods equal
# to the full window, so nothing here can see past the decision boundary.
# ---------------------------------------------------------------------------


def _window_sum(x: np.ndarray, w: int) -> np.ndarray:
    """Trailing sum over ``w`` rows; NaN for the first ``w - 1`` rows."""
    t = x.shape[0]
    out = np.full(x.shape, np.nan, dtype=np.float64)
    if t < w:
        return out
    cs = np.cumsum(x, axis=0)
    out[w - 1 :] = cs[w - 1 :]
    if t > w:
        out[w:] -= cs[: t - w]
    return out


def _roll_moments(a: np.ndarray, w: int):
    """Trailing mean and standard deviation, requiring a fully observed window."""
    ok = np.isfinite(a)
    x = np.where(ok, a, 0.0)
    n = _window_sum(ok.astype(np.float64), w)
    s1 = _window_sum(x, w)
    s2 = _window_sum(x * x, w)
    full = np.isfinite(n) & (n >= w - 0.5)
    mean = np.where(full, s1 / float(w), np.nan)
    var = np.where(full, s2 / float(w) - mean * mean, np.nan)
    return mean, np.sqrt(np.maximum(var, 0.0))


def _roll_mean(a: np.ndarray, w: int) -> np.ndarray:
    return _roll_moments(a, w)[0]


def _roll_sd(a: np.ndarray, w: int) -> np.ndarray:
    return _roll_moments(a, w)[1]


def _roll_z(a: np.ndarray, w: int) -> np.ndarray:
    """Trailing z-score, winsorised at +/- 3 sigma (thesis 5.3.3)."""
    mean, sd = _roll_moments(a, w)
    good = np.isfinite(a) & np.isfinite(mean) & (sd > _EPS)
    safe = np.where(sd > _EPS, sd, 1.0)
    z = np.where(good, (a - mean) / safe, np.nan)
    return np.clip(z, -_WINSOR, _WINSOR)


def _ewma(a: np.ndarray, span: float) -> np.ndarray:
    """Expanding-normalised EWMA, computed without a Python loop over rows."""
    t = a.shape[0]
    lam = 1.0 - 2.0 / (float(span) + 1.0)
    log_lam = np.log(lam)
    idx = np.arange(t, dtype=np.float64).reshape(-1, 1)
    up = np.exp(-log_lam * idx)
    dn = np.exp(log_lam * idx)
    ok = np.isfinite(a)
    x = np.where(ok, a, 0.0)
    num = np.cumsum(x * up, axis=0) * dn
    den = np.cumsum(ok.astype(np.float64) * up, axis=0) * dn
    return np.where(den > _EPS, num / np.maximum(den, _EPS), np.nan)


def _stack_mean(items) -> np.ndarray:
    """Equal-weight mean over the members that are observed at each cell."""
    arr = np.stack(items, axis=0)
    ok = np.isfinite(arr)
    cnt = ok.sum(axis=0).astype(np.float64)
    tot = np.where(ok, arr, 0.0).sum(axis=0)
    return np.where(cnt > 0.0, tot / np.maximum(cnt, 1.0), np.nan)


def _xs_demean(a: np.ndarray) -> np.ndarray:
    """Remove the per-timestamp cross-sectional mean."""
    ok = np.isfinite(a)
    cnt = ok.sum(axis=1, keepdims=True).astype(np.float64)
    tot = np.where(ok, a, 0.0).sum(axis=1, keepdims=True)
    mu = np.where(cnt > 0.0, tot / np.maximum(cnt, 1.0), 0.0)
    return np.where(ok, a - mu, np.nan)


# ---------------------------------------------------------------------------
# Frame handling.  Per-symbol frames carry a positional RangeIndex and unequal
# history, so every panel is aligned on the ``open_time`` column and never on
# the integer index.
# ---------------------------------------------------------------------------


def _build_panel(bars, symbols):
    """Return (kept symbols, sorted open_time index, T x N x len(_COLS) cube)."""
    frames = []
    keep = []
    for sym in symbols:
        frame = bars[sym]
        if frame is None or len(frame) < _MIN_HISTORY:
            continue
        cols = frame.columns
        if "open_time" not in cols:
            continue
        if any(c not in cols for c in _COLS):
            continue
        tail = frame.iloc[-_HIST:]
        dup = tail["open_time"].duplicated(keep="last").to_numpy()
        if dup.any():
            tail = tail.loc[~dup]
            if len(tail) < _MIN_HISTORY:
                continue
        block = tail.set_index("open_time")[list(_COLS)].astype(np.float64)
        frames.append(block)
        keep.append(sym)

    if len(keep) < _MIN_NAMES:
        return [], None, None

    wide = pd.concat(frames, axis=1, keys=keep).sort_index()
    if len(wide) > _HIST:
        wide = wide.iloc[-_HIST:]
    raw = wide.to_numpy(dtype=np.float64)
    rows = raw.shape[0]
    if rows < _MIN_HISTORY or raw.shape[1] != len(keep) * len(_COLS):
        return [], None, None
    return keep, wide.index, raw.reshape(rows, len(keep), len(_COLS))


def _funding_panel(funding, symbols, index):
    """Funding rate as-of each bar boundary; ``None`` if it cannot be aligned."""
    if funding is None or len(funding) == 0 or index is None or len(index) == 0:
        return None
    try:
        cols = funding.columns
        for needed in ("symbol", "funding_rate", "funding_time"):
            if needed not in cols:
                return None
        sub = funding.loc[
            funding["funding_time"] >= index[0],
            ["symbol", "funding_rate", "funding_time"],
        ]
        if sub.empty:
            return None
        sub = sub.loc[sub["symbol"].isin(list(symbols))]
        if sub.empty:
            return None
        sub = sub.sort_values("funding_time")
        sub = sub.drop_duplicates(subset=["funding_time", "symbol"], keep="last")
        wide = sub.pivot(index="funding_time", columns="symbol", values="funding_rate")
        wide = wide.sort_index().reindex(columns=list(symbols))
        aligned = wide.reindex(index, method="ffill")
        arr = aligned.to_numpy(dtype=np.float64)
        if arr.shape != (len(index), len(symbols)):
            return None
        return arr
    except Exception:
        # The funding conditioner is one of four; if the frame cannot be aligned
        # the book still trades on the remaining three rather than going flat.
        return None


# ---------------------------------------------------------------------------
# Signal construction.
# ---------------------------------------------------------------------------


def _primitives(cube):
    """Scale-free per-bar primitives from the raw cube."""
    close = cube[:, :, 0]
    qvol = cube[:, :, 1]
    tbq = cube[:, :, 2]
    trades = cube[:, :, 3]

    price_ok = np.isfinite(close) & (close > 0.0)
    logc = np.where(price_ok, np.log(np.where(price_ok, close, 1.0)), np.nan)
    ret = np.full(logc.shape, np.nan, dtype=np.float64)
    ret[1:] = logc[1:] - logc[:-1]

    qv_ok = np.isfinite(qvol) & (qvol > 0.0)
    # Any strictly positive per-symbol scale works: it cancels exactly in both
    # normalisations, and only keeps the EWMA cumulants numerically tame.
    cnt = qv_ok.sum(axis=0).astype(np.float64)
    tot = np.where(qv_ok, qvol, 0.0).sum(axis=0)
    scale = np.where(cnt > 0.0, tot / np.maximum(cnt, 1.0), np.nan)
    safe_scale = np.where(np.isfinite(scale) & (scale > 0.0), scale, np.nan)

    qv_n = qvol / safe_scale
    flow_n = (2.0 * tbq - qvol) / safe_scale

    # A bar in which nothing traded carries no aggressor information: the flow
    # signal is zero there, never interpolated (thesis 5.3.8).
    dead = np.isfinite(qvol) & (qvol <= 0.0)

    ratio = np.where(qv_n > 0.0, flow_n / np.where(qv_n > 0.0, qv_n, 1.0), np.nan)
    ratio = np.where(dead, 0.0, ratio)

    trade_ok = np.isfinite(trades) & (trades > 0.0)
    comp_ok = qv_ok & trade_ok
    size = np.where(comp_ok, qvol / np.where(trade_ok, trades, 1.0), np.nan)
    comp = np.where(comp_ok & (size > 0.0), np.log(np.where(size > 0.0, size, 1.0)), np.nan)

    logv = np.where(qv_ok, np.log(np.where(qv_ok, qvol, 1.0)), np.nan)

    return ret, qv_n, flow_n, dead, ratio, comp, logv


def _trailing_flow(flow_n, qv_n, dead, span):
    """Knob 1 level ``trailing``: strictly lagged, scale-matched denominator."""
    ewm = _ewma(qv_n, span)
    lagged = np.full(ewm.shape, np.nan, dtype=np.float64)
    lagged[1:] = ewm[:-1]
    usable = np.isfinite(lagged) & (lagged > _EPS)
    out = np.where(usable, flow_n / np.where(usable, lagged, 1.0), np.nan)
    return np.where(dead, 0.0, out)


def _ensemble(ret, ratio, trailing, comp, logv, fund):
    """Equal-weight ensemble over the declared surface, plus its control set.

    Returns ``(signal, accumulated_return, log_volume, single_bar_return)``.
    """
    shared = {}
    ctrl_ret = []
    ctrl_vol = []
    ctrl_r1 = []

    for width in _STD:
        z_r1 = _roll_z(ret, width)
        ctrl_r1.append(z_r1)
        sd_r = _roll_sd(ret, width)
        for lag in _ACCUM:
            span_sd = sd_r * np.sqrt(float(lag))
            acc_ret = _roll_mean(ret, lag) * float(lag)
            usable = np.isfinite(span_sd) & (span_sd > _EPS)
            z_ret = np.clip(
                np.where(usable, acc_ret / np.where(usable, span_sd, 1.0), np.nan),
                -_WINSOR,
                _WINSOR,
            )
            z_vol = _roll_z(_roll_mean(logv, lag), width)
            z_comp = _roll_z(_roll_mean(comp, lag), width)
            z_fund = None if fund is None else _roll_z(_roll_mean(fund, lag), width)
            shared[(lag, width)] = (z_ret, z_vol, z_comp, z_fund)
            ctrl_ret.append(z_ret)
            ctrl_vol.append(z_vol)

    signals = []
    for norm in _NORMS:
        for width in _STD:
            flow = ratio if norm == "ratio" else trailing[width]
            for lag in _ACCUM:
                z_flow = _roll_z(_roll_mean(flow, lag), width)
                z_ret, _z_vol, z_comp, z_fund = shared[(lag, width)]
                # absorption: price response per unit flow.  High response ->
                # informed, follow.  Low response -> absorbed, fade.
                z_abs = np.clip((z_ret - z_flow) / np.sqrt(2.0), -_WINSOR, _WINSOR)
                # none -> 1 (follow), absorption -> z_abs, funding -> -z_fund
                # (rich funding fades), composition -> z_comp (large trades follow).
                terms = [np.ones_like(z_flow), z_abs, z_comp]
                if z_fund is not None:
                    terms.append(-z_fund)
                signals.append(z_flow * _stack_mean(terms))

    return (
        _stack_mean(signals),
        _stack_mean(ctrl_ret),
        _stack_mean(ctrl_vol),
        _stack_mean(ctrl_r1),
    )


def _residualise(signal, controls):
    """Strip the part of the signal spanned by the contemporaneous state.

    Pooled trailing cross-sectional OLS over the retained window.  Every
    variable is demeaned per timestamp first, which absorbs the intercept and
    any common time effect; the regression uses only quantities observable at
    the same instant as the signal, so it cannot import a forward return.

    The window is deliberately long.  Betas re-estimated on a short window
    wander from bar to bar, and that wander is turnover the book is charged for
    and earns nothing on.
    """
    target = _xs_demean(signal)
    design = [_xs_demean(c) for c in controls]

    usable = np.isfinite(target)
    for col in design:
        usable = usable & np.isfinite(col)

    beta = np.zeros(len(design), dtype=np.float64)
    if int(usable.sum()) >= _MIN_OBS:
        y_vec = target[usable]
        x_mat = np.column_stack([col[usable] for col in design])
        spread = x_mat.std(axis=0)
        live = spread > _EPS
        if bool(live.any()) and np.isfinite(y_vec).all():
            solved = np.linalg.lstsq(x_mat[:, live] / spread[live], y_vec, rcond=None)[0]
            beta[live] = solved / spread[live]

    fitted = np.zeros(target.shape, dtype=np.float64)
    for weight, col in zip(beta, design):
        fitted = fitted + weight * np.where(np.isfinite(col), col, 0.0)
    return target - fitted


def _smooth(resid):
    """Exponential low-pass over the retained window; the turnover control."""
    rows = resid.shape[0]
    decay = 0.5 ** (1.0 / _HALFLIFE)
    weights = (decay ** np.arange(rows - 1, -1, -1, dtype=np.float64)).reshape(-1, 1)
    ok = np.isfinite(resid)
    numer = (np.where(ok, resid, 0.0) * weights).sum(axis=0)
    denom = (ok.astype(np.float64) * weights).sum(axis=0)
    total = float(weights.sum())
    value = np.where(denom > _EPS, numer / np.maximum(denom, _EPS), np.nan)
    covered = (denom / total) >= 0.25
    return np.where(covered & np.isfinite(resid[-1]), value, np.nan)


def _book(score):
    """Map a cross-sectional score to capped, near-net-flat unlevered weights."""
    centred = score - score.mean()
    spread = centred.std()
    if spread > _EPS:
        centred = np.clip(centred, -_WINSOR * spread, _WINSOR * spread)
        centred = centred - centred.mean()
    gross = np.abs(centred).sum()
    if not np.isfinite(gross) or gross <= _EPS:
        return None

    weights = centred * (_GROSS / gross)
    for _ in range(5):
        weights = np.clip(weights, -_MAX_W, _MAX_W)
        gross = np.abs(weights).sum()
        if gross <= _EPS:
            return None
        if gross >= _GROSS - 1e-9:
            break
        weights = weights * (_GROSS / gross)
    weights = np.clip(weights, -_MAX_W, _MAX_W)

    net = float(weights.sum())
    if abs(net) > 0.8 * _MAX_NET:
        weights = np.clip(weights - net / weights.size, -_MAX_W, _MAX_W)
        gross = np.abs(weights).sum()
        if gross > _GROSS:
            weights = weights * (_GROSS / gross)
    return weights


# ---------------------------------------------------------------------------
# Strategy.
# ---------------------------------------------------------------------------


class TakerFlowPressure:
    """Conditioned aggressor imbalance, orthogonal to the contemporaneous state.

    The instance holds no mutable attributes: every decision is a pure function
    of the ``DecisionContext`` it is handed.
    """

    def target_weights(self, context, *, seed):
        eligible = [s for s in context.eligible_symbols if s != _RESERVED]
        if len(eligible) < _MIN_NAMES:
            return {}
        flat = {sym: 0.0 for sym in eligible}

        bars = context.bars
        candidates = sorted({s for s in eligible if s in bars})
        if len(candidates) < _MIN_NAMES:
            return flat

        keep, index, cube = _build_panel(bars, candidates)
        if not keep or cube is None:
            return flat

        ret, qv_n, flow_n, dead, ratio, comp, logv = _primitives(cube)
        trailing = {w: _trailing_flow(flow_n, qv_n, dead, w) for w in _STD}
        fund = _funding_panel(context.funding, keep, index)

        signal, ctrl_ret, ctrl_vol, ctrl_r1 = _ensemble(
            ret, ratio, trailing, comp, logv, fund
        )

        window = min(_RESID, signal.shape[0])
        if window < 2:
            return flat
        resid = _residualise(
            signal[-window:],
            (ctrl_ret[-window:], ctrl_vol[-window:], ctrl_r1[-window:]),
        )

        tail = min(_SMOOTH, resid.shape[0])
        score = _smooth(resid[-tail:])

        live = np.isfinite(score)
        if int(live.sum()) < _MIN_NAMES:
            return flat

        weights = _book(score[live].astype(np.float64))
        if weights is None:
            return flat

        names = [keep[i] for i in range(len(keep)) if bool(live[i])]
        for name, value in zip(names, weights):
            if name in flat and np.isfinite(value):
                flat[name] = float(value)
        return flat


def build_strategy():
    return TakerFlowPressure()
