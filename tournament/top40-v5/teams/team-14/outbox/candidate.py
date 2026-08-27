"""team-14 — discovery candidate.

Mandate: time net exposure from cross-sectional breadth and dispersion.

This module implements the *declared baseline configuration* of ``lane/scouting/THESIS.md``
(§4.1 fixed items, §4.4 baseline values) with no knob searched and no result seen. Every
number below is either a §4.1/§4.4 declaration or a stated numerical guard (marked as such);
nothing here is fitted, tabulated, or dated.

Shape of the book, per THESIS §1.6:

    s_i,t     = (close_i,t / SMA_Lb(close_i)_t - 1) / sigma_i,t      per-symbol primitive
    B_t       = mean_i sign(s_i,t)                                   breadth   (1st moment)
    D_t       = xs-std(L_d-bar returns) / (mean_i sigma_i * sqrt(L_d))  dispersion (2nd moment)
    F_t       = 2 * frac_i(taker-buy quote share over L_d bars > 1/2) - 1   flow breadth
    C_t       = mean_i (funding paid per bar), trailing L_d bars      funding crowding
    S_t       = z(B) + w_f*z(F) - w_d*z(D) - w_c*z(C)                 state variable
    net_t     = 0.25 * tanh((S_t + b) / kappa),  floored at |net|>=0.05
    w_i,t     = gamma * demeaned_rank(s_i,t)/gross + net_t * invvol_i,t

The neutral leg is not decoration: a *pure* net tilt has book volatility |net_t|*sigma_R, so
the organizer's common ex-ante risk unit divides the timing magnitude straight back out and
only the sign survives. Carrying a roughly state-independent neutral leg alongside the timed
tilt makes the *share* of risk coming from net exposure vary with state, which is what keeps
the mandate testable after risk normalisation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------------------
# Declared configuration. THESIS §4.1 (fixed by design) and §4.4 (baseline). Not searched.
# ---------------------------------------------------------------------------------------
UNIVERSE_K = 60          # §4.1 top-K by trailing median quote volume
LIQ_LB = 30              # §4.1 bars used for the liquidity median
VOL_LB = 45              # §4.1 bars of 8h log returns for per-symbol realised vol
Z_WINDOW = 360           # §4.1 causal z-scoring window (120 days at 8h)
L_B = 21                 # §4.4 breadth / trend lookback
L_D = 9                  # §4.4 dispersion / flow / funding lookback
W_F = 0.5                # §4.4 flow-breadth weight, sign fixed +
W_D = 0.5                # §4.4 dispersion weight, sign fixed -
W_C = 0.5                # §4.4 funding-crowding weight, sign fixed -
KAPPA = 1.0              # §4.4 tanh saturation scale
TILT_B = 0.5             # §4.4 unconditional long tilt
GAMMA = 1.0              # §4.4 neutral-leg gross relative to the net leg
NET_CAP = 0.25           # §4.1 / contract
NET_FLOOR = 0.05         # §4.1, sign(0) := +1
GROSS_TARGET = 1.0       # contract cap; the organizer's risk unit rescales from here
MAX_WEIGHT = 0.10        # contract per-symbol cap

# ---------------------------------------------------------------------------------------
# Numerical guards. Not signal knobs, not searched; present so the book degrades gracefully
# instead of silently returning nothing (which would score as "no edge" rather than "no run").
# ---------------------------------------------------------------------------------------
MIN_NAMES = 8            # fewer usable symbols than this -> hold rather than trade noise
Z_MIN_OBS = 60           # fewer history points than this -> that z-term contributes 0
Z_CLIP = 4.0             # bound a z built on a near-degenerate dispersion
SIGMA_FLOOR_FRAC = 0.20  # inverse-vol weights floor sigma at 20% of its cross-sectional median

_LOOKBACK = max(L_B, VOL_LB + 1, L_D + 1)
MIN_HISTORY = _LOOKBACK + 10           # §4.1 "max lookback + 10 bars"
PANEL_ROWS = Z_WINDOW + _LOOKBACK + 5

_TIME_COLUMNS = ("close_time", "open_time", "timestamp", "time", "datetime", "date")
_PANEL_COLUMNS = ("close", "quote_volume", "taker_buy_quote_volume")
_FUNDING_TIME_COLUMNS = ("funding_time", "settlement_time")


# ---------------------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------------------
def _min_periods(window):
    """Leniency rule: a rolling statistic needs two thirds of its window populated.

    Strict ``min_periods == window`` would drop any symbol with a single missing bar, and a
    universe that shrinks below ``MIN_NAMES`` produces a permanently flat book.
    """
    return max(3, (2 * int(window)) // 3)


def _time_index(frame):
    """Return a UTC ``DatetimeIndex`` for ``frame``, or ``None`` if it has no usable stamps."""
    idx = frame.index
    if isinstance(idx, pd.DatetimeIndex):
        try:
            return pd.DatetimeIndex(pd.to_datetime(idx, utc=True))
        except (ValueError, TypeError):
            return None
    for name in _TIME_COLUMNS:
        if name in frame.columns:
            try:
                conv = pd.to_datetime(frame[name], utc=True, errors="coerce")
            except (ValueError, TypeError):
                return None
            if bool(conv.notna().all()):
                return pd.DatetimeIndex(conv)
            return None
    return None


def _epoch(index):
    """UTC nanoseconds as int64, tolerant of tz-aware and tz-naive inputs."""
    di = pd.DatetimeIndex(index)
    if di.tz is not None:
        di = di.tz_convert("UTC").tz_localize(None)
    return di.to_numpy(dtype="datetime64[ns]").astype("int64")


def _panel(bars, symbols, columns, n_rows):
    """Right-align ``columns`` across ``symbols`` onto one grid.

    Preferred path aligns on timestamps. If any frame carries no usable stamps the fallback
    aligns positionally from the newest row backwards, which is correct on a complete grid
    and degrades gracefully on a gapped one. Returns ``(index_or_None, {column: DataFrame})``.
    """
    cols = list(symbols)
    stamps = {}
    dated = True
    for sym in cols:
        idx = _time_index(bars[sym])
        if idx is None:
            dated = False
            break
        stamps[sym] = idx

    if dated:
        # Only each symbol's newest n_rows stamps can reach the newest n_rows of the union,
        # so trimming first is exact and keeps the per-decision cost off total history length.
        tails = {sym: stamps[sym][-n_rows:] for sym in cols}
        union = None
        for sym in cols:
            idx = tails[sym].drop_duplicates()
            union = idx if union is None else union.union(idx)
        if union is not None and union.shape[0] > 0:
            union = union.sort_values()
            if union.shape[0] > n_rows:
                union = union[-n_rows:]
            out = {}
            for col in columns:
                data = {}
                for sym in cols:
                    frame = bars[sym]
                    if col not in frame.columns:
                        continue
                    values = pd.to_numeric(frame[col].iloc[-n_rows:], errors="coerce")
                    ser = pd.Series(values.to_numpy(dtype=float), index=tails[sym])
                    ser = ser[~ser.index.duplicated(keep="last")]
                    data[sym] = ser.reindex(union)
                if data:
                    out[col] = pd.concat(data, axis=1).reindex(columns=cols).astype(float)
                else:
                    out[col] = pd.DataFrame(np.nan, index=union, columns=cols)
            return union, out

    out = {}
    index = pd.RangeIndex(n_rows)
    for col in columns:
        mat = np.full((n_rows, len(cols)), np.nan)
        for j, sym in enumerate(cols):
            frame = bars[sym]
            if col not in frame.columns:
                continue
            values = pd.to_numeric(frame[col], errors="coerce").to_numpy(dtype=float)
            take = int(min(values.shape[0], n_rows))
            if take > 0:
                mat[n_rows - take:, j] = values[values.shape[0] - take:]
        out[col] = pd.DataFrame(mat, index=index, columns=cols)
    return None, out


def _universe(context):
    """Top-K point-in-time members by trailing median quote volume (§4.1).

    Ties keep ``eligible_symbols`` order via a stable sort, so the choice never depends on
    symbol identity.
    """
    bars = context.bars
    scored = []
    seen = set()
    for sym in context.eligible_symbols:
        if sym in seen or sym not in bars:
            continue
        seen.add(sym)
        frame = bars[sym]
        if "close" not in frame.columns or frame.shape[0] < MIN_HISTORY:
            continue
        liquidity = 0.0
        if "quote_volume" in frame.columns:
            tail = pd.to_numeric(frame["quote_volume"].iloc[-LIQ_LB:], errors="coerce")
            if bool(tail.notna().any()):
                candidate = float(tail.median())
                if np.isfinite(candidate):
                    liquidity = candidate
        scored.append((liquidity, sym))
    scored.sort(key=lambda item: -item[0])
    return [sym for _, sym in scored[:UNIVERSE_K]]


def _z_last(values, window, min_obs):
    """Causal z-score of the newest observation against its own trailing window."""
    arr = np.asarray(values, dtype=float)
    if arr.size == 0 or not np.isfinite(arr[-1]):
        return 0.0
    history = arr[-window:]
    history = history[np.isfinite(history)]
    if history.size < min_obs:
        return 0.0
    spread = float(np.std(history))
    if not np.isfinite(spread) or spread <= 0.0:
        return 0.0
    score = (float(arr[-1]) - float(np.mean(history))) / spread
    if not np.isfinite(score):
        return 0.0
    return float(np.clip(score, -Z_CLIP, Z_CLIP))


def _funding_crowding(funding, index, symbols):
    """Per-bar funding *paid*, cross-sectionally averaged over ``symbols``.

    Binance settlement frequency changed over the sample (8h default, 4h for many USD-M
    contracts, 1h while a rate sits at its cap), so a bar may contain one, two or eight
    events. Summing within the bar and averaging across symbols keeps the series on a
    "cost borne over the bar" footing rather than a per-interval one. Returns ``None``
    whenever the frame cannot be read, in which case the term contributes 0.
    """
    if not isinstance(index, pd.DatetimeIndex) or index.shape[0] == 0:
        return None
    if not isinstance(funding, pd.DataFrame) or funding.shape[0] == 0:
        return None
    if "funding_rate" not in funding.columns or "symbol" not in funding.columns:
        return None
    time_column = None
    for name in _FUNDING_TIME_COLUMNS:
        if name in funding.columns:
            time_column = name
            break
    if time_column is None:
        return None

    try:
        stamps = pd.to_datetime(funding[time_column], utc=True, errors="coerce")
    except (ValueError, TypeError):
        return None
    stamp_i8 = _epoch(pd.DatetimeIndex(stamps))
    grid_i8 = _epoch(index)

    # Bar 0 is dropped deliberately: rows older than the panel would otherwise all collapse
    # onto it. One bar out of PANEL_ROWS costs nothing and the rolling mean tolerates the gap.
    # The mask is applied to raw arrays rather than to the frame: `funding` carries the whole
    # past and is re-read at every decision, so a DataFrame copy here is not affordable.
    selected = stamp_i8 > grid_i8[0]
    if not bool(selected.any()):
        return None
    stamp_i8 = stamp_i8[selected]
    symbol_column = pd.Series(funding["symbol"].to_numpy()[selected])
    rates = pd.to_numeric(
        pd.Series(funding["funding_rate"].to_numpy()[selected]), errors="coerce"
    )

    column_of = {sym: j for j, sym in enumerate(symbols)}
    mapped = symbol_column.map(column_of)
    if not bool(mapped.notna().any()):
        mapped = symbol_column.astype(str).map(column_of)
    keep = (mapped.notna() & rates.notna()).to_numpy()
    if not bool(keep.any()):
        return None

    slots = np.searchsorted(grid_i8, stamp_i8[keep], side="left")
    columns = mapped.to_numpy(dtype=float)[keep].astype(np.int64)
    values = rates.to_numpy(dtype=float)[keep]
    inside = slots < grid_i8.shape[0]
    if not bool(inside.any()):
        return None
    slots = slots[inside]
    columns = columns[inside]
    values = values[inside]

    n_bars = grid_i8.shape[0]
    n_syms = len(symbols)
    flat = slots * n_syms + columns
    totals = np.bincount(flat, weights=values, minlength=n_bars * n_syms)
    counts = np.bincount(flat, minlength=n_bars * n_syms)
    totals = totals.reshape(n_bars, n_syms)
    counts = counts.reshape(n_bars, n_syms)

    observed = counts > 0
    names_per_bar = observed.sum(axis=1)
    summed = np.where(observed, totals, 0.0).sum(axis=1)
    per_bar = np.where(names_per_bar > 0, summed / np.maximum(names_per_bar, 1), np.nan)
    return pd.Series(per_bar, index=index)


def _enforce_caps(weights):
    """Normalise gross, then apply the contract's per-symbol and net caps."""
    book = {}
    for sym, value in weights.items():
        number = float(value)
        if np.isfinite(number) and number != 0.0:
            book[sym] = number
    if not book:
        return {}

    gross = sum(abs(v) for v in book.values())
    if not np.isfinite(gross) or gross <= 0.0:
        return {}
    scale = GROSS_TARGET / gross
    book = {sym: value * scale for sym, value in book.items()}
    book = {sym: max(-MAX_WEIGHT, min(MAX_WEIGHT, value)) for sym, value in book.items()}

    net = sum(book.values())
    if abs(net) > NET_CAP:
        book = {sym: value * (NET_CAP / abs(net)) for sym, value in book.items()}
    gross = sum(abs(v) for v in book.values())
    if gross > 1.0:
        book = {sym: value / gross for sym, value in book.items()}
    return book


# ---------------------------------------------------------------------------------------
# Strategy
# ---------------------------------------------------------------------------------------
class BreadthStateBook:
    """Net exposure timed on cross-sectional breadth and dispersion.

    Stateless by construction: every decision is recomputed from the past-only rows in the
    context it is handed, so replaying the same context twice gives the same book.
    """

    def target_weights(self, context, *, seed):
        del seed  # no randomness is used anywhere in this strategy

        symbols = _universe(context)
        if len(symbols) < MIN_NAMES:
            return None

        index, panel = _panel(context.bars, symbols, _PANEL_COLUMNS, PANEL_ROWS)
        close = panel["close"]
        close = close.where(close > 0.0)
        if close.shape[0] < MIN_HISTORY:
            return None

        # --- per-symbol primitive: vol-normalised distance from its own moving average ---
        log_returns = np.log(close).diff()
        sigma = log_returns.rolling(VOL_LB, min_periods=_min_periods(VOL_LB)).std(ddof=0)
        sigma = sigma.where(sigma > 0.0)
        average = close.rolling(L_B, min_periods=_min_periods(L_B)).mean()
        primitive = (close / average.where(average > 0.0) - 1.0) / sigma
        primitive = primitive.where(np.isfinite(primitive))

        populated = primitive.notna().sum(axis=1)

        # --- first moment: breadth ---
        breadth = np.sign(primitive).mean(axis=1).where(populated >= MIN_NAMES)

        # --- second moment: dispersion, in correlation-proxy form ---
        horizon_returns = np.log(close) - np.log(close.shift(L_D))
        horizon_returns = horizon_returns.where(np.isfinite(horizon_returns))
        cross_std = horizon_returns.std(axis=1, ddof=0)
        normaliser = sigma.mean(axis=1) * np.sqrt(float(L_D))
        dispersion = (cross_std / normaliser.where(normaliser > 0.0)).where(
            horizon_returns.notna().sum(axis=1) >= MIN_NAMES
        )

        # --- flow breadth: how many names are seeing net taker buying ---
        taker = panel["taker_buy_quote_volume"]
        quote = panel["quote_volume"]
        bought = taker.rolling(L_D, min_periods=_min_periods(L_D)).sum()
        traded = quote.rolling(L_D, min_periods=_min_periods(L_D)).sum()
        share = bought / traded.where(traded > 0.0)
        share = share.where(np.isfinite(share))
        share_ok = share.notna()
        share_count = share_ok.sum(axis=1)
        share_above = ((share > 0.5) & share_ok).sum(axis=1)
        flow = (2.0 * (share_above / share_count.where(share_count >= MIN_NAMES)) - 1.0)

        # --- funding crowding: how one-sided the leveraged book is ---
        funding_bar = _funding_crowding(context.funding, index, symbols)
        if funding_bar is None:
            z_crowd = 0.0
        else:
            crowding = funding_bar.rolling(L_D, min_periods=1).mean()
            z_crowd = _z_last(crowding.to_numpy(dtype=float), Z_WINDOW, Z_MIN_OBS)

        z_breadth = _z_last(breadth.to_numpy(dtype=float), Z_WINDOW, Z_MIN_OBS)
        z_flow = _z_last(flow.to_numpy(dtype=float), Z_WINDOW, Z_MIN_OBS)
        z_dispersion = _z_last(dispersion.to_numpy(dtype=float), Z_WINDOW, Z_MIN_OBS)

        # Signs are fixed by prior (THESIS §4.1): breadth and flow enter positively,
        # dispersion and funding crowding negatively. They are never flipped on evidence.
        state = z_breadth + W_F * z_flow - W_D * z_dispersion - W_C * z_crowd

        net = NET_CAP * float(np.tanh((state + TILT_B) / KAPPA))
        if abs(net) < NET_FLOOR:
            net = NET_FLOOR if net >= 0.0 else -NET_FLOOR

        # --- legs ---
        latest = primitive.iloc[-1]
        latest_sigma = sigma.iloc[-1]
        usable = (latest.notna() & latest_sigma.notna()).to_numpy()
        names = [sym for sym, keep in zip(symbols, usable) if bool(keep)]
        if len(names) < MIN_NAMES:
            return None

        scores = latest.loc[names].astype(float)
        ranks = scores.rank(method="average")
        demeaned = ranks - float(ranks.mean())
        spread = float(demeaned.abs().sum())
        if not np.isfinite(spread) or spread <= 0.0:
            neutral = demeaned * 0.0
        else:
            neutral = demeaned / spread

        vols = latest_sigma.loc[names].astype(float)
        median_vol = float(vols.median())
        if np.isfinite(median_vol) and median_vol > 0.0:
            vols = vols.clip(lower=SIGMA_FLOOR_FRAC * median_vol)
        inverse = 1.0 / vols
        inverse_total = float(inverse.sum())
        if not np.isfinite(inverse_total) or inverse_total <= 0.0:
            inverse = pd.Series(1.0 / float(len(names)), index=pd.Index(names))
        else:
            inverse = inverse / inverse_total

        raw = GAMMA * neutral + net * inverse
        return _enforce_caps({sym: float(raw.loc[sym]) for sym in names})


def build_strategy():
    """Entrypoint required by the tournament runner."""
    return BreadthStateBook()
