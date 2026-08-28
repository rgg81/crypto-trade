"""team-02 — funding convexity.

Cross-sectional funding carry priced *per unit of a dispersion-informed forecast of
forward realized variance*, held on a daily rebalance so the carry has time to pay for
its own transaction costs.

Signal, in one line:

    w_i  ~  -( carry_i - median(carry) ) / vhat_i        cross-sectionally demeaned

where ``carry_i`` is the mean of the last 21 eight-hour funding prints (7 days, THESIS
grid knob 1) and ``vhat_i`` is a forward-variance forecast from a HAR baseline on
Garman-Klass 8h variance plus a trailing funding-dispersion term over 63 prints
(21 days, grid knob 2).  The dispersion coefficient is fitted online from past-only
streamed rows and is admitted only if it is positive with a pooled t-statistic above
4.0; otherwise it is set to zero and the forecast degenerates to the HAR baseline.
That is the thesis falsifier (F1) wired into the strategy itself: if funding dispersion
carries no incremental information about forward realized variance in the streamed
data, the dispersion term switches itself off.

No persistent state: every quantity is recomputed from the past-only context at each
decision.  The rebalance clock is a pure function of the number of bars already
streamed, so it is deterministic, future-append invariant and calendar-shift
equivariant.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

# --------------------------------------------------------------- preregistered
# THESIS §4.1 grid / §4.2 primary cell.  Windows are counted in 8h funding prints.
CARRY_PRINTS = 21       # knob 1 `s`: 7 days.  Slow end of the declared {3, 9, 21}.
DISP_PRINTS = 63        # knob 2 `l`: 21 days.  Primary-cell value.
HIST_PRINTS_MAX = 189   # §4.3 universe screen: 63 days of history.
LIQ_DAYS = 63.0         # §4.3 liquidity screen window.
RV_DAYS = (1.0, 3.0, 7.0)   # HAR components; the long leg is the tied `v := s`.
HORIZON_DAYS = 1.0      # §4.1 fixed forecast horizon h = 3 intervals.

# ------------------------------------------------- fixed implementation constants
# None of these are searched.  They are set once, from the t01 cost curve and from
# ordinary numerical-robustness practice, and are declared in RATIONALE.md.
REBAL_STRIDE = 3        # rebalance every 3rd decision boundary -> once per day
PANEL_BARS = 1095       # cap on regression-panel depth per symbol
MIN_PANEL_ROWS = 600    # below this the online fit is not attempted
DISP_T_MIN = 4.0        # runtime F1 gate on the dispersion coefficient
DISP_B_HI = 1.0         # cap on the admitted dispersion coefficient
VAR_LO = 0.30           # bounds on the relative variance forecast
VAR_HI = 3.00
Z_CLIP = 2.5            # winsorisation of the cross-sectional score
SOFT_TAU = 0.40         # soft-threshold: drop no-conviction names to exactly zero
MIN_NONZERO = 10        # breadth floor; below it the soft threshold is switched off
MIN_NAMES = 8
GROSS = 0.99
MAX_W = 0.095
MIN_CARRY_OBS = 12
MIN_DISP_OBS = 40
VAR_FLOOR = 1e-8
GK_C = 2.0 * math.log(2.0) - 1.0

_BAR_COLS = ("open_time", "open", "high", "low", "close", "quote_volume")
_FUND_COLS = ("symbol", "funding_time", "funding_rate")


# ---------------------------------------------------------------------- helpers
def _to_ns(values):
    """Timestamps -> int64 nanoseconds since epoch, tz-safe."""
    ser = values if isinstance(values, pd.Series) else pd.Series(values)
    # ``is_datetime64_any_dtype`` accepts both naive and tz-aware columns.  A plain
    # ``np.issubdtype`` would raise on a tz-aware pandas dtype, which is not a numpy
    # dtype at all, and would take the whole book flat for the entire window.
    if not pd.api.types.is_datetime64_any_dtype(ser):
        try:
            ser = pd.to_datetime(ser, utc=True)
        except (TypeError, ValueError):
            return np.asarray(ser, dtype="int64")
    if isinstance(ser.dtype, pd.DatetimeTZDtype):
        ser = ser.dt.tz_convert("UTC").dt.tz_localize(None)
    return ser.to_numpy(dtype="datetime64[ns]").astype("int64")


def _bars_per_day(frame):
    """Infer the bar cadence from ``open_time`` rather than assuming 8h bars."""
    if len(frame) < 3:
        return 3.0
    t = _to_ns(frame["open_time"])
    d = np.diff(t)
    d = d[d > 0]
    if d.size == 0:
        return 3.0
    step = float(np.median(d))
    if not np.isfinite(step) or step <= 0.0:
        return 3.0
    bpd = 86400.0e9 / step
    if not np.isfinite(bpd) or bpd <= 0.0:
        return 3.0
    return bpd


def _gk(frame):
    """Per-bar Garman-Klass variance (THESIS §4.2 RV estimator)."""
    o = frame["open"].to_numpy(dtype=float)
    h = frame["high"].to_numpy(dtype=float)
    lo = frame["low"].to_numpy(dtype=float)
    c = frame["close"].to_numpy(dtype=float)
    ok = (o > 0.0) & (h > 0.0) & (lo > 0.0) & (c > 0.0) & (h >= lo)
    safe = np.where(ok, 1.0, np.nan)
    hl = np.log(np.where(ok, h, 1.0) * safe / np.where(ok, lo, 1.0))
    co = np.log(np.where(ok, c, 1.0) * safe / np.where(ok, o, 1.0))
    v = 0.5 * hl * hl - GK_C * co * co
    v = np.where(np.isfinite(v), v, np.nan)
    return np.maximum(v, VAR_FLOOR)


def _roll_mean(x, w):
    """Trailing mean over ``w`` samples, NaN-tolerant, cumsum based."""
    n = x.size
    out = np.full(n, np.nan)
    if w <= 0 or n < w:
        return out
    good = np.isfinite(x)
    xf = np.where(good, x, 0.0)
    cs = np.concatenate(([0.0], np.cumsum(xf)))
    cc = np.concatenate(([0.0], np.cumsum(good.astype(float))))
    s = cs[w:] - cs[:-w]
    k = cc[w:] - cc[:-w]
    need = max(2.0, 0.6 * w)
    out[w - 1:] = np.where(k >= need, s / np.maximum(k, 1.0), np.nan)
    return out


def _align_prev(src_t, src_v, tgt_t):
    """Last source value at or before each target timestamp (step-hold join)."""
    out = np.full(tgt_t.size, np.nan)
    if src_t.size == 0:
        return out
    pos = np.searchsorted(src_t, tgt_t, side="right") - 1
    ok = pos >= 0
    if np.any(ok):
        out[ok] = src_v[pos[ok]]
    return out


def _funding_panel(funding, max_rows):
    """Wide funding panel: rows are settlement times (int64 ns), columns symbols."""
    if funding is None or len(funding) == 0:
        return None
    cols = funding.columns
    for name in _FUND_COLS:
        if name not in cols:
            return None
    f = funding.loc[:, list(_FUND_COLS)].dropna()
    if len(f) == 0:
        return None
    rate = f["funding_rate"].to_numpy(dtype=float)
    flat = pd.DataFrame(
        {"symbol": f["symbol"].to_numpy(), "t": _to_ns(f["funding_time"]), "r": rate}
    )
    flat = flat.loc[np.isfinite(rate)]
    if len(flat) == 0:
        return None
    times = np.unique(flat["t"].to_numpy())
    if times.size > max_rows:
        flat = flat.loc[flat["t"].to_numpy() >= times[times.size - max_rows]]
    flat = flat.drop_duplicates(subset=["symbol", "t"], keep="last")
    if len(flat) == 0:
        return None
    panel = flat.pivot(index="t", columns="symbol", values="r").sort_index()
    if panel.shape[0] < 2 or panel.shape[1] < MIN_NAMES:
        return None
    return panel


def _fit_dispersion_har(stack_x, stack_y):
    """Pooled OLS of log forward RV on the HAR basis plus log funding dispersion.

    Returns the coefficient vector with the dispersion loading zeroed unless it is
    positive with t >= DISP_T_MIN.  The threshold is deliberately above the thesis's
    2.5 because pooled overlapping forward windows inflate a naive t-statistic by
    roughly sqrt(horizon).  Returns ``None`` if the fit is unusable.
    """
    if not stack_x:
        return None
    x = np.vstack(stack_x)
    y = np.concatenate(stack_y)
    if x.shape[0] < MIN_PANEL_ROWS:
        return None
    a = np.column_stack([np.ones(x.shape[0]), x])
    try:
        beta = np.linalg.lstsq(a, y, rcond=None)[0]
        resid = y - a @ beta
        dof = a.shape[0] - a.shape[1]
        if dof <= 1:
            return None
        s2 = float(resid @ resid) / dof
        cov = np.linalg.inv(a.T @ a) * s2
        se = math.sqrt(max(float(cov[4, 4]), 0.0))
    except np.linalg.LinAlgError:
        return None
    if not np.all(np.isfinite(beta)):
        return None
    tstat = beta[4] / se if se > 0.0 else 0.0
    if not (np.isfinite(tstat) and tstat >= DISP_T_MIN and beta[4] > 0.0):
        beta[4] = 0.0          # F1 has not fired on the streamed panel: HAR only.
    beta[4] = min(float(beta[4]), DISP_B_HI)
    return beta


def _variance_forecast(bars, syms, disp_hist, widths):
    """Relative forward-variance forecast per symbol, normalised to median 1."""
    w_s, w_m, w_l, w_h = widths
    d_t = disp_hist.index.to_numpy(dtype="int64")
    d_v = disp_hist.to_numpy(dtype=float)
    n_sym = len(syms)
    cur = np.full((n_sym, 4), np.nan)
    log_fallback = np.full(n_sym, np.nan)
    stack_x = []
    stack_y = []

    for i, sym in enumerate(syms):
        frame = bars[sym]
        gk = _gk(frame)
        n = gk.size
        if n < w_l + w_h + 5:
            continue
        x1 = np.log(_roll_mean(gk, w_s))
        x2 = np.log(_roll_mean(gk, w_m))
        x3 = np.log(_roll_mean(gk, w_l))
        rh = _roll_mean(gk, w_h)
        y = np.full(n, np.nan)
        y[: n - w_h] = np.log(rh[w_h:])          # realised RV over the NEXT w_h bars
        d_al = _align_prev(d_t, d_v[:, i], _to_ns(frame["open_time"]))
        x4 = np.log(np.where(d_al > 0.0, d_al, np.nan))

        log_fallback[i] = x3[-1]          # trailing 7d log variance, HAR-free path
        cur[i, 0] = x1[-1]
        cur[i, 1] = x2[-1]
        cur[i, 2] = x3[-1]
        cur[i, 3] = x4[-1]

        lo = max(0, n - PANEL_BARS)
        hi = n - w_h                              # forward window fully in the past
        if hi - lo < 20:
            continue
        s1, s2, s3, s4, sy = x1[lo:hi], x2[lo:hi], x3[lo:hi], x4[lo:hi], y[lo:hi]
        m = (
            np.isfinite(s1) & np.isfinite(s2) & np.isfinite(s3)
            & np.isfinite(s4) & np.isfinite(sy)
        )
        if int(m.sum()) >= 20:
            stack_x.append(np.column_stack([s1[m], s2[m], s3[m], s4[m]]))
            stack_y.append(sy[m])

    beta = _fit_dispersion_har(stack_x, stack_y)
    if beta is None:
        log_v = log_fallback
    else:
        filled = cur.copy()
        for j in range(4):
            col = filled[:, j]
            med = np.nanmedian(col) if np.any(np.isfinite(col)) else np.nan
            if np.isfinite(med):
                filled[:, j] = np.where(np.isfinite(col), col, med)
        log_v = beta[0] + filled @ beta[1:]
        log_v = np.where(np.isfinite(log_v), log_v, log_fallback)

    usable = np.isfinite(log_v)
    if int(usable.sum()) < MIN_NAMES:
        return None
    centre = np.median(log_v[usable])
    rel = np.exp(np.clip(log_v - centre, -3.0, 3.0))
    rel = np.clip(rel, VAR_LO, VAR_HI)
    return np.where(usable, rel, np.nan)


def _screen(bars, panel, eligible, w_liq):
    """THESIS §4.3 universe screen: minimum history, then top-half liquidity."""
    cols = [s for s in eligible if s in panel.columns]
    if len(cols) < MIN_NAMES:
        return None
    sub = panel.loc[:, cols]
    counts = sub.notna().sum().to_numpy(dtype=float)
    live = counts > 0.0
    if int(live.sum()) < MIN_NAMES:
        return None

    # The declared 63-day floor binds whenever it is feasible.  It cannot be
    # demanded before that much history exists anywhere, so during the warm-up
    # weeks it steps down to the most the universe actually has -- and only then.
    keep = counts >= float(HIST_PRINTS_MAX)
    if int(keep.sum()) < MIN_NAMES:
        med = float(np.median(counts[live]))
        need = min(float(HIST_PRINTS_MAX), max(float(CARRY_PRINTS), med))
        keep = counts >= need
    if int(keep.sum()) < MIN_NAMES:
        order = np.argsort(-counts)
        keep = np.zeros(counts.shape, dtype=bool)
        keep[order[: max(MIN_NAMES, int(live.sum()) // 2)]] = True
    syms = [c for c, k in zip(cols, keep) if k]
    if len(syms) < MIN_NAMES:
        return None

    liq = np.empty(len(syms))
    for i, sym in enumerate(syms):
        qv = bars[sym]["quote_volume"].to_numpy(dtype=float)
        if qv.size > w_liq:
            qv = qv[-w_liq:]
        med_qv = np.nanmedian(qv) if qv.size else np.nan
        liq[i] = med_qv if np.isfinite(med_qv) else -np.inf
    n = len(syms)
    k = max(MIN_NAMES, int(math.ceil(n / 2.0)))
    if k < n:
        top = np.sort(np.argsort(-liq)[:k])
        syms = [syms[i] for i in top]
    return syms


def _project(raw):
    """Score -> compliant book: winsorise, soft-threshold, neutralise, cap, scale."""
    raw = raw - raw.mean()
    scale = float(np.median(np.abs(raw)))
    if not np.isfinite(scale) or scale <= 0.0:
        scale = float(np.mean(np.abs(raw)))
    if not np.isfinite(scale) or scale <= 0.0:
        return None
    z = np.clip(raw / (1.4826 * scale), -Z_CLIP, Z_CLIP)
    zt = np.sign(z) * np.maximum(np.abs(z) - SOFT_TAU, 0.0)
    if int(np.count_nonzero(zt)) < MIN_NONZERO:
        zt = z
    zt = zt - zt.mean()
    gross = float(np.abs(zt).sum())
    if not np.isfinite(gross) or gross <= 0.0:
        return None
    w = zt * (GROSS / gross)
    for _ in range(4):
        w = np.clip(w, -MAX_W, MAX_W)
        w = w - w.mean()
        gross = float(np.abs(w).sum())
        if not np.isfinite(gross) or gross <= 0.0:
            return None
        w = w * (GROSS / gross)
    # Centre first, cap last, then only ever scale down: this makes the per-symbol
    # cap and the gross cap hard, and leaves at most a negligible residual net.
    w = w - w.mean()
    w = np.clip(w, -MAX_W, MAX_W)
    gross = float(np.abs(w).sum())
    if not np.isfinite(gross) or gross <= 0.0:
        return None
    if gross > GROSS:
        w = w * (GROSS / gross)
    if not np.all(np.isfinite(w)):
        return None
    return w


# ------------------------------------------------------------------ the decision
def _decide(context):
    bars = context.bars
    eligible = [s for s in context.eligible_symbols if s in bars]
    if len(eligible) < MIN_NAMES:
        return None

    longest = 0
    ref = None
    usable = []
    for sym in eligible:
        frame = bars[sym]
        cols = frame.columns
        if any(name not in cols for name in _BAR_COLS):
            continue
        usable.append(sym)
        if len(frame) > longest:
            longest = len(frame)
            ref = frame
    if ref is None or len(usable) < MIN_NAMES:
        return None
    eligible = usable

    bpd = _bars_per_day(ref)

    # Stateless rebalance clock: the decision boundary counted in whole bar
    # intervals since the epoch, in exact integer arithmetic.  It holds no state,
    # does not depend on appended future rows, ignores symbol identity and price
    # scale, and -- because one day is exactly REBAL_STRIDE bar intervals -- any
    # whole-day calendar shift leaves the rebalance phase unchanged.
    step_ns = int(round(86400.0e9 / bpd))
    if step_ns <= 0:
        return None
    if (int(pd.Timestamp(context.decision_time).value) // step_ns) % REBAL_STRIDE:
        return None

    w_s = max(2, int(round(RV_DAYS[0] * bpd)))
    w_m = max(3, int(round(RV_DAYS[1] * bpd)))
    w_l = max(5, int(round(RV_DAYS[2] * bpd)))
    w_h = max(2, int(round(HORIZON_DAYS * bpd)))
    w_liq = max(10, int(round(LIQ_DAYS * bpd)))

    panel = _funding_panel(context.funding, PANEL_BARS + DISP_PRINTS + 8)
    if panel is None:
        return None
    syms = _screen(bars, panel, eligible, w_liq)
    if syms is None:
        return None

    sub = panel.loc[:, syms]
    tail_c = sub.tail(CARRY_PRINTS)
    carry = tail_c.mean().to_numpy(dtype=float)
    c_obs = tail_c.count().to_numpy(dtype=float)
    disp_hist = sub.rolling(DISP_PRINTS, min_periods=MIN_DISP_OBS).std().shift(1)

    vhat = _variance_forecast(bars, syms, disp_hist, (w_s, w_m, w_l, w_h))
    if vhat is None:
        return None

    ok = np.isfinite(carry) & (c_obs >= MIN_CARRY_OBS) & np.isfinite(vhat) & (vhat > 0.0)
    if int(ok.sum()) < MIN_NAMES:
        return None
    live = [s for s, keep in zip(syms, ok) if keep]
    carry = carry[ok]
    vhat = vhat[ok]

    # Carry demeaned BEFORE the variance divide.  Dividing the raw (positive-mean)
    # funding level by variance would leave a pure 1/variance term in the score and
    # turn the book into a systematic short-low-vol / long-high-vol bet that has
    # nothing to do with the mandate.
    raw = -(carry - np.median(carry)) / vhat
    w = _project(raw)
    if w is None:
        return None
    return {sym: float(val) for sym, val in zip(live, w)}


class FundingConvexityBook:
    """Stateless: every decision is recomputed from the past-only context."""

    def target_weights(self, context, *, seed):
        try:
            return _decide(context)
        except (ArithmeticError, AttributeError, IndexError, KeyError,
                TypeError, ValueError, np.linalg.LinAlgError):
            return None


def build_strategy():
    return FundingConvexityBook()
