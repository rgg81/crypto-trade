"""team-02 -- funding convexity. Discovery baseline.

Implements the preregistered primary cell of ``lane/scouting/THESIS.md`` (§4.2) and nothing
else:

    signal_i  =  - carry_i / sigma2_hat_i        cross-sectionally demeaned

where ``carry_i`` is trailing realized funding per day (s = 3 days), and ``sigma2_hat_i`` is a
forward-variance forecast built as an equal-weight geometric blend, in cross-sectionally
centred logs, of trailing Garman-Klass realized variance (v = 3 days) and trailing funding
dispersion (l = 21 days).  Funding dispersion enters the *denominator* -- that is the one
place the mandate's convexity term can enter without becoming a volatility target (§4.4).

Sign, committed in §1.6: funding f > 0 means longs pay shorts, so a position of sign p accrues
-p*f.  Rich funding therefore earns a short.  The cross-sectional demean is what keeps this a
relative-value book rather than an outright short in a bull tape; it is not optional.

The book carries no state between decisions, reads no absolute dates, no symbol identities and
no price levels, and is invariant to a common rescaling of prices or of the variance unit (the
level of ``sigma2_hat`` cancels in the demean-and-normalise step).
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

# --- Preregistered constants (THESIS.md §4.1 / §4.2 / §4.3). ---------------------------------
SHORT_DAYS = 3.0            # s = 9 x 8h intervals: the trailing funding-carry window.
LONG_DAYS = 21.0            # l = 63 x 8h intervals: the funding-dispersion window.
RV_DAYS = 3.0               # v := s, tied not free.
MIN_HISTORY_DAYS = 63.0     # universe screen: 189 intervals of history at signal formation.
MIN_FUNDING_PRINTS = 40     # of a nominal 63 in the long window; tolerates gaps, not newness.
MIN_NAMES = 8               # below this the book is not a portfolio; stand flat instead.

# --- Constraint envelope, held strictly inside the stated caps. ------------------------------
GROSS = 0.98                # sum |w| <= 1.0
MAX_W = 0.099               # |w_i|    <= 0.10
MAX_NET = 0.05              # |sum w|  <= 0.25

Z_CLIP = 3.0                # cross-sectional winsorisation, in sigmas; hygiene, not a threshold.
GK_C = 2.0 * math.log(2.0) - 1.0
NS_PER_DAY = 86_400_000_000_000.0
DEFAULT_BAR_DAYS = 1.0 / 3.0   # 8h, the funding cadence; used only if the bar index is unusable.
MIN_BAR_DAYS = 1.0 / 1440.0    # sanity band on an inferred bar spacing: one minute ...
MAX_BAR_DAYS = 7.0             # ... to one week.
EPS = 1e-15


# --- Pure helpers ----------------------------------------------------------------------------

def _epoch_ns(values):
    """Coerce a time-like array to float64 nanoseconds since epoch.

    Handles datetime64, tz-aware and tz-naive timestamps, and integer epochs in s / ms / us / ns.
    Unparseable entries come back as NaN and are dropped by the callers' window masks.
    """
    arr = np.asarray(values)
    if arr.size and np.issubdtype(arr.dtype, np.number):
        v = arr.astype("float64")
        finite = v[np.isfinite(v)]
        if finite.size == 0:
            return np.full(v.shape, np.nan)
        magnitude = float(np.median(np.abs(finite)))
        if magnitude > 1e17:
            unit = 1.0            # already nanoseconds
        elif magnitude > 1e14:
            unit = 1e3            # microseconds
        elif magnitude > 1e11:
            unit = 1e6            # milliseconds
        elif magnitude > 1e8:
            unit = 1e9            # seconds
        else:
            return np.full(v.shape, np.nan)   # a positional index, not a clock
        return v * unit
    try:
        stamps = pd.to_datetime(pd.Series(arr), utc=True, errors="coerce")
        missing = stamps.isna().to_numpy()
        naive = stamps.dt.tz_localize(None).to_numpy(dtype="datetime64[ns]")
        out = naive.astype("int64").astype("float64")
    except (TypeError, ValueError, OverflowError):
        return np.full(arr.shape, np.nan)
    out[missing] = np.nan
    return out


def _epoch_ns_scalar(stamp):
    """Coerce the decision boundary to float64 nanoseconds since epoch."""
    ts = pd.Timestamp(stamp)
    ts = ts.tz_localize("UTC") if ts.tz is None else ts.tz_convert("UTC")
    return float(ts.value)


def _column(frame, name):
    """Numeric column as float64, or ``None`` if absent or uncoercible."""
    if name not in frame.columns:
        return None
    try:
        return pd.to_numeric(frame[name], errors="coerce").to_numpy(dtype="float64")
    except (TypeError, ValueError):
        return None


def _bar_span_days(frame):
    """Median bar spacing in days, inferred from the frame's own index, or ``None``."""
    index = frame.index
    if len(index) < 4:
        return None
    stamps = _epoch_ns(index.to_numpy()[-65:])
    deltas = np.diff(stamps) / NS_PER_DAY
    deltas = deltas[np.isfinite(deltas) & (deltas > 0.0)]
    if deltas.size == 0:
        return None
    span = float(np.median(deltas))
    if MIN_BAR_DAYS <= span <= MAX_BAR_DAYS:
        return span
    return None


def _garman_klass(frame, n_bars):
    """Mean per-bar Garman-Klass variance over the last ``n_bars``, or ``None``.

    Units are per-bar, not per-day.  That is deliberate: every symbol shares one bar grid, so a
    common multiplicative constant on the variance cancels in the cross-sectional normalisation.
    """
    tail = frame.iloc[-n_bars:]
    o = _column(tail, "open")
    h = _column(tail, "high")
    lo = _column(tail, "low")
    c = _column(tail, "close")
    if o is None or h is None or lo is None or c is None:
        return None
    ok = np.isfinite(o) & np.isfinite(h) & np.isfinite(lo) & np.isfinite(c)
    ok &= (o > 0.0) & (h > 0.0) & (lo > 0.0) & (c > 0.0) & (h >= lo)
    if int(ok.sum()) < 3:
        return None
    o, h, lo, c = o[ok], h[ok], lo[ok], c[ok]
    hl = np.log(h / lo)
    co = np.log(c / o)
    variance = float(np.mean(0.5 * hl * hl - GK_C * co * co))
    if np.isfinite(variance) and variance > 0.0:
        return variance
    # §5.5: at coarse resolution GK can go negative on a quiet bar. Fall back to close-to-close.
    r = np.diff(np.log(c))
    if r.size < 2:
        return None
    variance = float(np.mean(r * r))
    return variance if np.isfinite(variance) and variance > 0.0 else None


def _median_turnover(frame, n_bars):
    """Median per-bar quote volume over the last ``n_bars``; used only for a relative screen."""
    tail = frame.iloc[-n_bars:]
    q = _column(tail, "quote_volume")
    if q is None or not np.isfinite(q).any():
        v = _column(tail, "volume")
        c = _column(tail, "close")
        if v is None or c is None:
            return None
        q = v * c
    q = q[np.isfinite(q) & (q > 0.0)]
    if q.size == 0:
        return None
    value = float(np.median(q))
    return value if np.isfinite(value) and value > 0.0 else None


def _funding_stats(funding, decision_ns):
    """Per-symbol (daily carry, daily funding dispersion, print count) over the two windows.

    Both statistics are expressed per *day* rather than per print, so a contract that has been
    switched to hourly settlement stays comparable with one settling every eight hours (§1.1).
    """
    if funding is None or len(funding) == 0:
        return None
    columns = funding.columns
    if "symbol" not in columns or "funding_rate" not in columns:
        return None
    if "funding_time" in columns:
        time_column = "funding_time"
    elif "settlement_time" in columns:
        time_column = "settlement_time"
    else:
        return None

    stamps = _epoch_ns(funding[time_column].to_numpy())
    rate = _column(funding, "funding_rate")
    if rate is None:
        return None
    symbol = funding["symbol"].to_numpy()

    long_start = decision_ns - LONG_DAYS * NS_PER_DAY
    short_start = decision_ns - SHORT_DAYS * NS_PER_DAY
    window = (stamps >= long_start) & (stamps < decision_ns) & np.isfinite(rate)
    if not bool(window.any()):
        return None

    long_rows = pd.DataFrame(
        {"symbol": symbol[window], "rate": rate[window], "t": stamps[window]}
    )
    grouped = long_rows.groupby("symbol")["rate"]
    dispersion = grouped.std(ddof=1)
    count = grouped.count()

    short_rows = long_rows.loc[long_rows["t"].to_numpy() >= short_start]
    if len(short_rows) == 0:
        return None
    carry = short_rows.groupby("symbol")["rate"].sum() / SHORT_DAYS

    # Per-print dispersion -> per-day dispersion.
    prints_per_day = (count / LONG_DAYS).clip(lower=EPS)
    dispersion = dispersion * np.sqrt(prints_per_day)

    return carry.to_dict(), dispersion.to_dict(), count.to_dict()


def _finalize(symbols, raw):
    """Cross-sectionally demean, normalise, cap and net-neutralise into submittable weights."""
    x = raw - float(np.mean(raw))
    sd = float(np.std(x))
    if not np.isfinite(sd) or sd <= EPS:
        return {}
    z = np.clip(x / sd, -Z_CLIP, Z_CLIP)
    z = z - float(np.mean(z))

    gross = float(np.abs(z).sum())
    if gross <= EPS:
        return {}
    w = z * (GROSS / gross)

    # Alternate capping and re-centring; this converges quickly and keeps net near zero.
    for _ in range(6):
        w = np.clip(w, -MAX_W, MAX_W)
        w = w - float(np.mean(w))
    w = np.clip(w, -MAX_W, MAX_W)

    gross = float(np.abs(w).sum())
    largest = float(np.max(np.abs(w)))
    if gross <= EPS or largest <= EPS:
        return {}
    w = w * min(GROSS / gross, MAX_W / largest)

    net = float(w.sum())
    if abs(net) > MAX_NET:
        w = np.clip(w - net / float(w.size), -MAX_W, MAX_W)
        gross = float(np.abs(w).sum())
        if gross > GROSS:
            w = w * (GROSS / gross)

    return {
        str(s): float(v)
        for s, v in zip(symbols, w)
        if np.isfinite(v) and abs(v) > 1e-6
    }


# --- Strategy --------------------------------------------------------------------------------

class FundingConvexityBook:
    """Stateless carry-per-unit-of-forecast-variance book.

    Every decision is a pure function of the context handed in.  Nothing is carried across
    calls, so exact replay is deterministic and there is no channel for look-ahead.
    """

    def target_weights(self, context, *, seed):
        try:
            return self._weights(context)
        except Exception:
            # A malformed decision stands flat rather than holding a stale book. See RATIONALE.md
            # -- this guard is a known diagnostic blind spot and is reported as one.
            return {}

    def _weights(self, context):
        eligible = [str(s) for s in context.eligible_symbols]
        if len(eligible) < MIN_NAMES:
            return {}

        decision_ns = _epoch_ns_scalar(context.decision_time)
        stats = _funding_stats(context.funding, decision_ns)
        if stats is None:
            return {}
        carry_by_symbol, dispersion_by_symbol, count_by_symbol = stats

        bars = context.bars
        span = None
        for symbol in eligible:
            frame = bars.get(symbol)
            if frame is not None and len(frame) >= 4:
                span = _bar_span_days(frame)
                if span is not None:
                    break
        if span is None:
            span = DEFAULT_BAR_DAYS

        min_rows = max(10, int(round(MIN_HISTORY_DAYS / span)))
        rv_bars = max(3, int(round(RV_DAYS / span)))
        liquidity_bars = max(5, min_rows)

        symbols = []
        carry = []
        dispersion = []
        variance = []
        liquidity = []

        for symbol in eligible:
            frame = bars.get(symbol)
            if frame is None or len(frame) < min_rows:
                continue                                   # §4.3 minimum-history screen
            if int(count_by_symbol.get(symbol, 0)) < MIN_FUNDING_PRINTS:
                continue
            d = float(dispersion_by_symbol.get(symbol, np.nan))
            c = float(carry_by_symbol.get(symbol, np.nan))
            if not (np.isfinite(d) and d > 0.0) or not np.isfinite(c):
                continue
            v = _garman_klass(frame, rv_bars)
            if v is None:
                continue
            q = _median_turnover(frame, liquidity_bars)
            if q is None:
                continue
            symbols.append(symbol)
            carry.append(c)
            dispersion.append(d)
            variance.append(v)
            liquidity.append(q)

        if len(symbols) < MIN_NAMES:
            return {}

        carry = np.asarray(carry, dtype="float64")
        dispersion = np.asarray(dispersion, dtype="float64")
        variance = np.asarray(variance, dtype="float64")
        liquidity = np.asarray(liquidity, dtype="float64")

        # §4.3 liquidity screen: top half of the surviving universe, point in time.
        keep = liquidity >= float(np.median(liquidity))
        if int(keep.sum()) < MIN_NAMES:
            keep = np.ones(liquidity.shape, dtype=bool)
        symbols = [s for s, k in zip(symbols, keep) if k]
        carry, dispersion, variance = carry[keep], dispersion[keep], variance[keep]
        if len(symbols) < MIN_NAMES:
            return {}

        # Dispersion-informed forward-variance forecast: an equal-weight geometric blend of the
        # two variance proxies, in cross-sectionally centred logs.  Dispersion is squared so both
        # terms are variance-like; equal weights are a preregistered choice, not a fitted one.
        log_rv = np.log(variance)
        log_disp = 2.0 * np.log(dispersion)
        if not (np.isfinite(log_rv).all() and np.isfinite(log_disp).all()):
            return {}
        a = np.clip(log_rv - float(np.mean(log_rv)), -Z_CLIP, Z_CLIP)
        b = np.clip(log_disp - float(np.mean(log_disp)), -Z_CLIP, Z_CLIP)
        forecast_variance = np.exp(0.5 * a + 0.5 * b)      # level is arbitrary; it cancels below

        raw = -carry / np.clip(forecast_variance, EPS, None)
        if not np.isfinite(raw).all():
            return {}
        return _finalize(symbols, raw)


def build_strategy():
    """Canonical entrypoint: one clean, stateless instance per run."""
    return FundingConvexityBook()
