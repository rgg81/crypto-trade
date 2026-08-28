"""team-02 -- funding convexity.  Nomination candidate.

Cross-sectional funding carry priced *per unit of a dispersion-informed forecast of forward
realized variance*, expressed as a slow rank-triangular long/short book.

    score_i  =  -( carry_i - median(carry) ) / vhat_i
    w_i      =  triangular rank weight of score_i,  gross-normalised, net-neutral

where

  carry_i  is realized funding per day over the trailing 21 days (frequency-agnostic: a
           time-window sum divided by elapsed days, so a contract switched to hourly
           settlement stays comparable with one settling every eight hours);

  vhat_i   is a relative forward-variance forecast -- an equal-weight HAR blend of log
           Garman-Klass 8h variance at 3d / 7d / 21d, plus b * log(funding dispersion),
           where b is fitted online from past-only streamed rows, constrained non-negative,
           and *smoothly shrunk* toward zero by t^2 / (t^2 + 4^2).

The dispersion term is the mandate's convexity term and it enters the denominator only --
the one place it can act without becoming a volatility target.  Its coefficient carries the
thesis falsifier inside the strategy: if trailing funding dispersion adds nothing to a HAR
baseline in the streamed panel, b shrinks to zero and the book degenerates cleanly to
carry-per-unit-of-realized-variance.  The shrinkage is continuous rather than a t-threshold,
so no small perturbation of the data can toggle the book between two regimes.

Sign: funding f > 0 means longs pay shorts, so a position of sign p accrues -p*f.  Rich
funding earns a short.  The cross-sectional demedian is what keeps this relative value rather
than an outright short in a bull tape; it is not optional.

Design target, set by the measured cost curve rather than by preference: the book must earn
more than ~3 x 8 bps of gross edge per unit of turnover to survive triple cost, which is a
floor on the holding period, not a parameter.  Everything slow about this file -- the 21-day
carry window, the daily rebalance, the smooth rank weighting whose boundary names carry zero
weight -- exists to raise edge per unit traded.

No state survives a call.  No absolute date, symbol identity or price level is compared
against a literal.  Every statistic is scale-free or is reduced to a cross-sectional rank.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

# ------------------------------------------------------------------ windows (days / prints)
CARRY_DAYS = 21.0            # realized-funding window: the persistent premium, not the blip
DISP_DAYS = 21.0             # THESIS knob 2 `l` = 63 intervals, primary-cell value
HIST_DAYS = 63.0             # THESIS 4.3 universe screen: 189 intervals of history
LIQ_DAYS = 63.0              # THESIS 4.3 liquidity screen window
RV_DAYS = (3.0, 7.0, 21.0)   # HAR components on Garman-Klass variance
HORIZON_DAYS = 1.0           # h = 3 intervals, fixed by preregistration
FUND_LOOKBACK_DAYS = 220.0   # funding rows retained per decision; bounds the work, not the model

MIN_CARRY_OBS = 40           # of a nominal 63 prints in the carry window; tolerates gaps
MIN_HIST_OBS = 150           # of a nominal 189 prints in the history window

# --------------------------------------------------------- fixed implementation constants
REBAL_STRIDE = 3             # one rebalance per day at the 00:00 UTC funding boundary
PANEL_BARS = 540             # depth of the online regression panel, per symbol
MIN_FIT_ROWS = 400           # pooled rows below which no dispersion coefficient is admitted
MIN_SYM_FIT_ROWS = 40        # per-symbol rows below which that symbol is not pooled
T0 = 4.0                     # shrinkage half-point on the dispersion t-statistic
B_MAX = 1.0                  # cap on the admitted dispersion coefficient
LOG_V_CLIP = 0.6             # variance tilt band: exp(+-0.6) is 0.55x .. 1.82x

TARGET_BREADTH = 16.0        # effective breadth held constant across universe sizes
TAU_MAX = 0.90
GROSS = 0.98                 # sum |w| <= 1.0
MAX_W = 0.090                # |w_i|   <= 0.10
MAX_NET = 0.10               # |sum w| <= 0.25
MIN_NAMES = 14

VAR_FLOOR = 1e-12
GK_C = 2.0 * math.log(2.0) - 1.0
NS_PER_DAY = 86_400_000_000_000.0

_BAR_COLS = ("open_time", "open", "high", "low", "close", "quote_volume")
_LOOP_ERRORS = (ArithmeticError, AttributeError, IndexError, KeyError, TypeError, ValueError)


# ------------------------------------------------------------------------------- helpers
def _to_ns(values):
    """Timestamps -> int64 nanoseconds since epoch, tz-safe.

    ``is_datetime64_any_dtype`` accepts both naive and tz-aware columns.  A plain
    ``np.issubdtype`` raises on a tz-aware pandas dtype, which is not a numpy dtype at all,
    and would take the whole book flat for the entire window while looking like no edge.
    """
    ser = values if isinstance(values, pd.Series) else pd.Series(values)
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
    t = _to_ns(frame["open_time"].iloc[-65:])
    d = np.diff(t)
    d = d[d > 0]
    if d.size == 0:
        return 3.0
    step = float(np.median(d))
    if not np.isfinite(step) or step <= 0.0:
        return 3.0
    bpd = NS_PER_DAY / step
    if not np.isfinite(bpd) or bpd <= 0.0:
        return 3.0
    return bpd


def _gk(frame):
    """Per-bar Garman-Klass variance.  Scale-free: it reads log ranges only."""
    o = frame["open"].to_numpy(dtype=float)
    h = frame["high"].to_numpy(dtype=float)
    lo = frame["low"].to_numpy(dtype=float)
    c = frame["close"].to_numpy(dtype=float)
    ok = (o > 0.0) & (h > 0.0) & (lo > 0.0) & (c > 0.0) & (h >= lo)
    with np.errstate(invalid="ignore", divide="ignore"):
        hl = np.log(np.where(ok, h, 1.0) / np.where(ok, lo, 1.0))
        co = np.log(np.where(ok, c, 1.0) / np.where(ok, o, 1.0))
        v = 0.5 * hl * hl - GK_C * co * co
    v = np.where(ok & np.isfinite(v), v, np.nan)
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


def _roll_std(x, w, min_obs):
    """Trailing sample standard deviation over ``w`` samples, NaN-tolerant."""
    n = x.size
    if n == 0 or w < 2:
        return np.full(n, np.nan)
    good = np.isfinite(x)
    xf = np.where(good, x, 0.0)
    c1 = np.concatenate(([0.0], np.cumsum(xf)))
    c2 = np.concatenate(([0.0], np.cumsum(xf * xf)))
    cn = np.concatenate(([0.0], np.cumsum(good.astype(float))))
    hi = np.arange(1, n + 1)
    lo = np.maximum(hi - w, 0)
    k = cn[hi] - cn[lo]
    s1 = c1[hi] - c1[lo]
    s2 = c2[hi] - c2[lo]
    kk = np.maximum(k, 1.0)
    mean = s1 / kk
    var = (s2 / kk - mean * mean) * kk / np.maximum(kk - 1.0, 1.0)
    ok = (k >= max(2.0, float(min_obs))) & np.isfinite(var) & (var > 0.0)
    with np.errstate(invalid="ignore"):
        return np.where(ok, np.sqrt(np.where(ok, var, 1.0)), np.nan)


def _align_prev(src_t, src_v, tgt_t):
    """Last source value *strictly before* each target timestamp (step-hold join)."""
    out = np.full(tgt_t.size, np.nan)
    if src_t.size == 0:
        return out
    pos = np.searchsorted(src_t, tgt_t, side="left") - 1
    ok = pos >= 0
    if np.any(ok):
        out[ok] = src_v[pos[ok]]
    return out


def _funding_by_symbol(funding, decision_ns):
    """Per-symbol (times, rates) from the funding frame, trimmed and time-sorted.

    Keyed on ``funding_time`` -- never on the positional index -- and grouped per symbol
    rather than pivoted into a union panel.  A contract on hourly settlement therefore
    cannot inject rows that turn every other symbol's window into NaN.
    """
    if funding is None or len(funding) == 0:
        return None
    cols = funding.columns
    if "symbol" not in cols or "funding_rate" not in cols:
        return None
    if "funding_time" in cols:
        tcol = "funding_time"
    elif "settlement_time" in cols:
        tcol = "settlement_time"
    else:
        return None

    t = _to_ns(funding[tcol])
    r = pd.to_numeric(funding["funding_rate"], errors="coerce").to_numpy(dtype=float)
    s = funding["symbol"].to_numpy()
    keep = np.isfinite(r) & (t >= decision_ns - int(FUND_LOOKBACK_DAYS * NS_PER_DAY))
    keep &= t < decision_ns
    if not bool(keep.any()):
        return None

    flat = pd.DataFrame({"s": s[keep], "t": t[keep], "r": r[keep]})
    flat = flat.drop_duplicates(subset=["s", "t"], keep="last")
    flat = flat.sort_values(["s", "t"], kind="mergesort")
    out = {}
    for sym, grp in flat.groupby("s", sort=False):
        out[sym] = (grp["t"].to_numpy(dtype="int64"), grp["r"].to_numpy(dtype=float))
    return out


def _fit_dispersion_slope(stack_x, stack_y):
    """Pooled within-symbol OLS slope of the HAR residual on log funding dispersion.

    Both sides are demeaned per symbol before pooling, so the slope answers the question the
    falsifier asks -- does *variation* in a symbol's funding dispersion predict *variation* in
    its forward realized variance beyond its own HAR baseline -- rather than being carried by
    cross-sectional level differences.

    The coefficient is constrained non-negative and shrunk smoothly by t^2/(t^2 + T0^2).  T0
    sits above the thesis's preregistered t = 2.5 because pooled overlapping forward windows
    inflate a naive t-statistic by roughly sqrt(horizon); the shrinkage is continuous so that
    no small perturbation flips the book between a dispersion regime and a HAR regime.
    """
    if not stack_x:
        return 0.0
    x = np.concatenate(stack_x)
    y = np.concatenate(stack_y)
    if x.size < MIN_FIT_ROWS:
        return 0.0
    sxx = float(x @ x)
    if not np.isfinite(sxx) or sxx <= 0.0:
        return 0.0
    b = float(x @ y) / sxx
    if not np.isfinite(b) or b <= 0.0:
        return 0.0
    resid = y - b * x
    dof = x.size - 1 - len(stack_x)
    if dof <= 10:
        return 0.0
    s2 = float(resid @ resid) / dof
    if not np.isfinite(s2) or s2 <= 0.0:
        return 0.0
    se = math.sqrt(s2 / sxx)
    if not np.isfinite(se) or se <= 0.0:
        return 0.0
    t = b / se
    if not np.isfinite(t) or t <= 0.0:
        return 0.0
    return float(min(b * (t * t) / (t * t + T0 * T0), B_MAX))


def _variance_tilt(bars, names, disp, widths):
    """Relative forward-variance forecast per symbol, centred on the cross-sectional median.

    Only the *ratio* across symbols is ever used, so the level of the forecast -- and with it
    any dependence on the price scale or the variance unit -- cancels identically.
    """
    w_s, w_m, w_l, w_h = widths
    n = len(names)
    trim = PANEL_BARS + w_l + w_h + 5
    har_now = np.full(n, np.nan)
    x_now = np.full(n, np.nan)
    stack_x = []
    stack_y = []

    for i, sym in enumerate(names):
        try:
            frame = bars[sym]
            if len(frame) > trim:
                frame = frame.iloc[-trim:]
            gk = _gk(frame)
            m = gk.size
            if m < w_l + w_h + 10:
                continue
            with np.errstate(invalid="ignore", divide="ignore"):
                har = (
                    np.log(_roll_mean(gk, w_s))
                    + np.log(_roll_mean(gk, w_m))
                    + np.log(_roll_mean(gk, w_l))
                ) / 3.0
                fwd = _roll_mean(gk, w_h)
                y = np.full(m, np.nan)
                y[: m - w_h] = np.log(fwd[w_h:])     # realized RV over the NEXT w_h bars
                d_t, d_v = disp[sym]
                x = np.log(_align_prev(d_t, d_v, _to_ns(frame["open_time"])))

            har_now[i] = har[-1]
            x_now[i] = x[-1]

            lo = max(0, m - PANEL_BARS)
            hi = m - w_h                              # forward window entirely in the past
            if hi - lo < MIN_SYM_FIT_ROWS:
                continue
            sh, sx, sy = har[lo:hi], x[lo:hi], y[lo:hi]
            ok = np.isfinite(sh) & np.isfinite(sx) & np.isfinite(sy)
            if int(ok.sum()) < MIN_SYM_FIT_ROWS:
                continue
            rx = sx[ok]
            ry = sy[ok] - sh[ok]
            stack_x.append(rx - float(rx.mean()))
            stack_y.append(ry - float(ry.mean()))
        except _LOOP_ERRORS:
            continue

    b = _fit_dispersion_slope(stack_x, stack_y)
    dev = np.zeros(n)
    if b > 0.0 and np.any(np.isfinite(x_now)):
        centre = float(np.nanmedian(x_now))
        dev = np.where(np.isfinite(x_now), x_now - centre, 0.0)
    log_v = har_now + b * dev

    ok = np.isfinite(log_v)
    if int(ok.sum()) < MIN_NAMES:
        return None, b
    log_v = np.where(ok, log_v, float(np.median(log_v[ok])))
    rel = np.exp(np.clip(log_v - float(np.median(log_v)), -LOG_V_CLIP, LOG_V_CLIP))
    return np.where(ok, rel, np.nan), b


def _rank_weights(score):
    """Triangular rank weights: soft-thresholded in rank space, gross-normalised, net-flat.

    Ranks rather than raw scores, so the book is invariant to any monotone rescaling of the
    signal and cannot be dragged around by one outlier.  The threshold ``tau`` is set from the
    universe size to hold effective breadth at TARGET_BREADTH whatever the universe does, and
    -- the point of a triangle rather than a top-K bucket -- a name sitting at the threshold
    carries *zero* weight, so two names swapping rank there generates no trade at all.
    """
    n = int(score.size)
    if n < MIN_NAMES:
        return None
    r = pd.Series(score).rank(method="average").to_numpy(dtype=float)
    u = 2.0 * (r - 0.5) / float(n) - 1.0                  # symmetric on (-1, 1)
    tau = 1.0 - TARGET_BREADTH / (0.75 * float(n))
    tau = min(max(tau, 0.0), TAU_MAX)
    v = np.sign(u) * np.maximum(np.abs(u) - tau, 0.0)
    if float(np.abs(v).sum()) <= 0.0:
        v = u
    v = v - float(v.mean())

    g = float(np.abs(v).sum())
    if not np.isfinite(g) or g <= 0.0:
        return None
    w = v * (GROSS / g)
    for _ in range(5):
        w = np.clip(w, -MAX_W, MAX_W)
        w = w - float(w.mean())
        g = float(np.abs(w).sum())
        if not np.isfinite(g) or g <= 0.0:
            return None
        w = w * (GROSS / g)

    # Centre first, cap last, then only ever scale down: both caps are hard afterwards.
    w = w - float(w.mean())
    w = np.clip(w, -MAX_W, MAX_W)
    g = float(np.abs(w).sum())
    if not np.isfinite(g) or g <= 0.0:
        return None
    if g > GROSS:
        w = w * (GROSS / g)
    net = float(w.sum())
    if abs(net) > MAX_NET:
        w = np.clip(w - net / float(n), -MAX_W, MAX_W)
        g = float(np.abs(w).sum())
        if g > GROSS:
            w = w * (GROSS / g)
    if not np.all(np.isfinite(w)):
        return None
    return w


# --------------------------------------------------------------------------- the decision
def _decide(context):
    bars = context.bars
    eligible = [s for s in context.eligible_symbols if s in bars]
    if len(eligible) < MIN_NAMES:
        return None

    usable = []
    ref = None
    longest = 0
    for sym in eligible:
        frame = bars[sym]
        if any(col not in frame.columns for col in _BAR_COLS):
            continue
        usable.append(sym)
        if len(frame) > longest:
            longest = len(frame)
            ref = frame
    if ref is None or len(usable) < MIN_NAMES:
        return None

    bpd = _bars_per_day(ref)
    step_ns = int(round(NS_PER_DAY / bpd))
    if step_ns <= 0:
        return None

    # Stateless rebalance clock: the decision boundary counted in whole bar intervals since
    # the epoch, in exact integer arithmetic.  It holds no state, does not depend on appended
    # future rows, ignores symbol identity and price scale, and -- because one day is exactly
    # REBAL_STRIDE bar intervals -- any whole-day calendar shift leaves the phase unchanged.
    # Routed through the same coercion as every other timestamp rather than through
    # ``Timestamp.value``, whose meaning depends on the object's resolution.
    decision_ns = int(_to_ns(pd.Series([pd.Timestamp(context.decision_time)]))[0])
    if (decision_ns // step_ns) % REBAL_STRIDE:
        return None

    w_s = max(2, int(round(RV_DAYS[0] * bpd)))
    w_m = max(3, int(round(RV_DAYS[1] * bpd)))
    w_l = max(5, int(round(RV_DAYS[2] * bpd)))
    w_h = max(1, int(round(HORIZON_DAYS * bpd)))
    w_liq = max(10, int(round(LIQ_DAYS * bpd)))

    funding = _funding_by_symbol(context.funding, decision_ns)
    if funding is None:
        return None

    carry_start = decision_ns - int(CARRY_DAYS * NS_PER_DAY)
    hist_start = decision_ns - int(HIST_DAYS * NS_PER_DAY)

    names = []
    carry = []
    hist_obs = []
    liquidity = []
    disp = {}
    for sym in usable:
        try:
            found = funding.get(sym)
            if found is None:
                continue
            t, r = found
            n_carry = int(np.count_nonzero(t >= carry_start))
            if n_carry < MIN_CARRY_OBS:
                continue
            n_hist = int(np.count_nonzero(t >= hist_start))

            # Per-day, not per-print: a contract switched to hourly settlement stays
            # comparable with one settling every eight hours.
            c = float(r[t >= carry_start].sum()) / CARRY_DAYS
            if not np.isfinite(c):
                continue
            pps = n_carry / CARRY_DAYS
            w_disp = int(min(400, max(20, round(DISP_DAYS * pps))))
            d = _roll_std(r, w_disp, max(10, w_disp // 2)) * math.sqrt(max(pps, 1e-9))
            if not np.any(np.isfinite(d)):
                continue

            qv = bars[sym]["quote_volume"].to_numpy(dtype=float)
            if qv.size > w_liq:
                qv = qv[-w_liq:]
            q = float(np.nanmedian(qv)) if qv.size else float("nan")
            if not np.isfinite(q) or q <= 0.0:
                continue

            names.append(sym)
            carry.append(c)
            hist_obs.append(n_hist)
            liquidity.append(q)
            disp[sym] = (t, d)
        except _LOOP_ERRORS:
            continue

    if len(names) < MIN_NAMES:
        return None
    carry = np.asarray(carry, dtype=float)
    hist_obs = np.asarray(hist_obs, dtype=float)
    liquidity = np.asarray(liquidity, dtype=float)

    # THESIS 4.3 minimum-history screen.  The declared 63-day floor binds whenever it is
    # feasible; it cannot be demanded before that much history exists anywhere, so during
    # warm-up it steps down to the most the universe actually has -- and only then.
    keep = hist_obs >= float(MIN_HIST_OBS)
    if int(keep.sum()) < MIN_NAMES:
        keep = hist_obs >= float(np.median(hist_obs))
    if int(keep.sum()) < MIN_NAMES:
        keep = np.ones(hist_obs.shape, dtype=bool)
    names = [s for s, k in zip(names, keep) if k]
    carry, liquidity = carry[keep], liquidity[keep]
    if len(names) < MIN_NAMES:
        return None

    # THESIS 4.3 liquidity screen: top half of the surviving universe, point in time.
    cut = float(np.median(liquidity))
    keep = liquidity >= cut
    if int(keep.sum()) < MIN_NAMES:
        keep = np.ones(liquidity.shape, dtype=bool)
    names = [s for s, k in zip(names, keep) if k]
    carry = carry[keep]
    if len(names) < MIN_NAMES:
        return None

    rel_v, _ = _variance_tilt(bars, names, disp, (w_s, w_m, w_l, w_h))
    if rel_v is None:
        return None
    ok = np.isfinite(rel_v) & (rel_v > 0.0) & np.isfinite(carry)
    if int(ok.sum()) < MIN_NAMES:
        return None
    live = [s for s, k in zip(names, ok) if k]
    carry = carry[ok]
    rel_v = rel_v[ok]

    # Carry demedianed BEFORE the variance divide.  Dividing the raw (positive-mean) funding
    # level by variance would leave a pure 1/variance term in every score and turn the book
    # into a systematic short-low-vol / long-high-vol bet with nothing to do with the mandate.
    score = -(carry - float(np.median(carry))) / rel_v
    if not np.all(np.isfinite(score)):
        return None
    w = _rank_weights(score)
    if w is None:
        return None
    return {sym: float(val) for sym, val in zip(live, w) if abs(val) > 1e-9}


class FundingConvexityBook:
    """Stateless: every decision is recomputed from the past-only context handed in."""

    def target_weights(self, context, *, seed):
        try:
            return _decide(context)
        except (ArithmeticError, AttributeError, IndexError, KeyError,
                TypeError, ValueError, np.linalg.LinAlgError):
            # A malformed decision holds the existing book rather than churning it flat.
            # This is a known diagnostic blind spot and RATIONALE.md reports it as one:
            # if mean gross exposure comes back near zero, this book did not run.
            return None


def build_strategy():
    """Canonical entrypoint: one clean, stateless instance per run."""
    return FundingConvexityBook()
