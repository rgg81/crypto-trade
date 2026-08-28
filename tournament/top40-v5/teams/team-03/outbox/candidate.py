"""team-03 refinement candidate — defensive, beta-controlled cross-sectional book.

Long low realised volatility / low trailing funding, short high realised volatility / high
trailing funding, across seasoned and liquid Binance USD-M perpetual members. Weights are
Frazzini-Pedersen rank weights; each leg is independently scaled to unit beta against the
equal-weight member index, subject to the protocol's net-exposure limit.

The book is deliberately slow. It recomputes and resubmits targets on a 42-bar (14 day)
data-relative grid and returns ``None`` in between, which holds quantities and costs nothing.
Every decision is a pure function of the supplied ``DecisionContext``: no attribute is mutated,
no state is carried, no absolute date, symbol name or price level is referenced.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

# --- preregistered surface (THESIS section 4) ------------------------------------------------
VOL_LOOKBACK = 189      # bars (63 days); longest declared realised-volatility window
CORR_WINDOW = 378       # bars (126 days); declared beta correlation window
BETA_SHRINK = 0.6       # beta = w * beta_hat + (1 - w) * 1, Frazzini-Pedersen shrinkage
REBALANCE_BARS = 42     # bars (14 days); slowest declared rebalance
MIN_HISTORY = 252       # bars (84 days); declared seasoning screen
LIQ_WINDOW = 63         # bars (21 days); declared liquidity-screen window
LIQ_KEEP = 0.70         # declared: keep the most liquid 70% of the member universe
NAME_CAP = 0.05         # declared per-name cap as a fraction of gross

# --- implementation limits (protocol, not signal) --------------------------------------------
HARD_NAME_CAP = 0.095   # protocol limit is 0.10
NET_CAP = 0.20          # protocol limit is 0.25
MIN_NAMES = 12
MIN_LEG = 5
LEG_DUST = 0.01         # drop leg members below 1% of their own leg
BETA_FLOOR = 0.35
BETA_CEIL = 2.5
EPS = 1e-12


def _column_panel(bars, symbols, column):
    """Align one bar column across symbols on ``open_time`` (never on the positional index)."""
    series = {}
    for sym in symbols:
        if sym not in bars:
            continue
        frame = bars[sym]
        if frame is None or len(frame) == 0:
            continue
        if "open_time" not in frame.columns or column not in frame.columns:
            continue
        col = pd.to_numeric(frame[column], errors="coerce")
        col.index = pd.Index(frame["open_time"])
        col = col[col.index.notna()]
        col = col[~col.index.duplicated(keep="last")]
        if len(col) == 0:
            continue
        series[sym] = col
    if not series:
        return pd.DataFrame()
    return pd.concat(series, axis=1).sort_index()


def _rank_z(values):
    """Cross-sectional z-score of the cross-sectional rank; missing names score neutral."""
    out = pd.Series(0.0, index=values.index, dtype=float)
    clean = values.replace([np.inf, -np.inf], np.nan).dropna()
    if len(clean) < 3:
        return out
    ranks = clean.rank(method="average")
    spread = float(ranks.std(ddof=0))
    if not np.isfinite(spread) or spread <= EPS:
        return out
    out.loc[clean.index] = (ranks - ranks.mean()) / spread
    return out


def _parkinson(high, low, window):
    """Declared volatility estimator: Parkinson high-low over ``window`` bars."""
    hi = high.tail(window)
    lo = low.tail(window)
    ratio = hi / lo
    ratio = ratio.where(ratio > 0)
    squared = np.log(ratio) ** 2
    counts = squared.notna().sum()
    var = squared.mean(skipna=True) / (4.0 * math.log(2.0))
    var = var.where(counts >= window // 2)
    return np.sqrt(var.where(var > 0))


def _funding_mean(funding, symbols, cutoff, window):
    """Trailing mean 8h funding rate per symbol, using rows no later than ``cutoff``."""
    empty = pd.Series(dtype=float)
    if funding is None or len(funding) == 0:
        return empty
    needed = ("symbol", "funding_rate", "funding_time")
    if any(name not in funding.columns for name in needed):
        return empty
    frame = funding.loc[:, list(needed)].copy()
    frame["funding_rate"] = pd.to_numeric(frame["funding_rate"], errors="coerce")
    frame = frame.dropna()
    if cutoff is not None:
        try:
            frame = frame[frame["funding_time"] <= cutoff]
        except (TypeError, ValueError):
            pass
    frame = frame[frame["symbol"].isin(list(symbols))]
    if len(frame) == 0:
        return empty
    frame = frame.sort_values("funding_time")
    tail = frame.groupby("symbol", sort=False).tail(window)
    grouped = tail.groupby("symbol", sort=False)["funding_rate"]
    return grouped.mean().where(grouped.size() >= window // 3)


def _score_at(high, low, funding, symbols, cutoff):
    """Defensive composite: equal-weight rank z-scores of Parkinson vol and trailing funding.

    Higher score = more defensive = long. Both components enter with a negative sign: high
    realised volatility is the lottery/junk leg, and high trailing funding is crowded levered
    long demand paying to be carried.
    """
    if cutoff is None:
        hi, lo = high, low
    else:
        hi, lo = high.loc[:cutoff], low.loc[:cutoff]
    park = _parkinson(hi, lo, VOL_LOOKBACK)
    fund = _funding_mean(funding, symbols, cutoff, VOL_LOOKBACK).reindex(park.index)
    return -(0.5 * _rank_z(park) + 0.5 * _rank_z(fund)), park


def _shrunk_beta(ret, mkt, symbols):
    """Frazzini-Pedersen beta_hat = rho * sigma_i / sigma_m, shrunk toward one."""
    default = pd.Series(1.0, index=pd.Index(symbols), dtype=float)
    window = ret.tail(VOL_LOOKBACK)
    market_window = mkt.tail(VOL_LOOKBACK)
    sigma_m = float(market_window.std(ddof=0))
    if not np.isfinite(sigma_m) or sigma_m <= EPS:
        return default
    counts = window.notna().sum()
    sigma_i = window.std(ddof=0).where(counts >= VOL_LOOKBACK // 2)
    rho = ret.tail(CORR_WINDOW).corrwith(mkt.tail(CORR_WINDOW))
    raw = (rho * sigma_i / sigma_m).replace([np.inf, -np.inf], np.nan)
    beta = BETA_SHRINK * raw + (1.0 - BETA_SHRINK)
    beta = beta.reindex(pd.Index(symbols)).fillna(1.0)
    return beta.clip(lower=BETA_FLOOR, upper=BETA_CEIL)


def _cap_and_normalise(vector, cap):
    """Scale to unit gross subject to a per-element cap, by repeated clip-and-renormalise."""
    out = np.asarray(vector, dtype=float).copy()
    out[~np.isfinite(out)] = 0.0
    gross = float(np.abs(out).sum())
    if gross <= EPS:
        return np.zeros_like(out)
    out = out / gross
    for _ in range(12):
        if float(np.abs(out).max()) <= cap + EPS:
            break
        out = np.clip(out, -cap, cap)
        gross = float(np.abs(out).sum())
        if gross <= EPS:
            return np.zeros_like(out)
        out = out / gross
    return np.clip(out, -cap, cap)


class DefensiveBetaControlledBook:
    """Stateless defensive book: each call is a pure function of ``context``."""

    def target_weights(self, context, *, seed):
        try:
            return self._decide(context)
        except Exception:
            # Hold rather than go flat on an unexpected shape; never raise into the runner.
            return None

    # -- decision ------------------------------------------------------------------------
    def _decide(self, context):
        eligible = [s for s in context.eligible_symbols if s in context.bars]
        if len(eligible) < MIN_NAMES:
            return None

        # Data-relative rebalance clock. Row counts shift with the calendar, so this grid is
        # calendar-shift equivariant in a way that a timestamp modulo would not be.
        clock = max(len(context.bars[s]) for s in eligible)
        if clock < MIN_HISTORY or clock % REBALANCE_BARS != 0:
            return None

        close = _column_panel(context.bars, eligible, "close")
        high = _column_panel(context.bars, eligible, "high")
        low = _column_panel(context.bars, eligible, "low")
        if close.empty or high.empty or low.empty:
            return None
        high = high.reindex(index=close.index, columns=close.columns)
        low = low.reindex(index=close.index, columns=close.columns)

        universe = self._screen(context, close)
        if universe is None:
            return None

        price = close.where(close > 0)
        ret = np.log(price).diff()
        market = ret.mean(axis=1, skipna=True)

        score, park = self._smoothed_score(context, high, low, close.index, universe)
        valid = [s for s in universe if np.isfinite(park.get(s, np.nan))]
        if len(valid) < MIN_NAMES:
            return None

        beta = _shrunk_beta(ret.loc[:, valid], market, valid)
        return self._book(score.reindex(valid).fillna(0.0), beta, valid)

    # -- universe ------------------------------------------------------------------------
    def _screen(self, context, close):
        """Declared screens: >= 252 bars of seasoning, then the most liquid 70%."""
        history = close.notna().sum()
        seasoned = [s for s in close.columns if float(history[s]) >= MIN_HISTORY]
        if len(seasoned) < MIN_NAMES:
            return None
        quote = _column_panel(context.bars, seasoned, "quote_volume")
        if quote.empty:
            return seasoned
        liquidity = quote.reindex(columns=seasoned).tail(LIQ_WINDOW).median().dropna()
        liquidity = liquidity[liquidity > 0]
        if len(liquidity) < MIN_NAMES:
            return seasoned
        keep = max(MIN_NAMES, int(math.ceil(LIQ_KEEP * len(liquidity))))
        universe = list(liquidity.sort_values(ascending=False).index[:keep])
        return universe if len(universe) >= MIN_NAMES else None

    # -- signal --------------------------------------------------------------------------
    def _smoothed_score(self, context, high, low, index, universe):
        """Average the composite over this grid point and the previous one.

        One holding period of smoothing halves the rank churn that has to be paid for at each
        rebalance without shortening any declared estimation window.
        """
        hi = high.loc[:, universe]
        lo = low.loc[:, universe]
        score, park = _score_at(hi, lo, context.funding, universe, None)
        if len(index) <= REBALANCE_BARS + MIN_HISTORY:
            return score, park
        try:
            cutoff = index[-(REBALANCE_BARS + 1)]
            lagged, _ = _score_at(hi, lo, context.funding, universe, cutoff)
            blended = pd.concat([score, lagged], axis=1).mean(axis=1, skipna=True)
            if blended.notna().sum() >= MIN_NAMES:
                return blended.reindex(score.index), park
        except Exception:
            pass
        return score, park

    # -- portfolio -----------------------------------------------------------------------
    def _book(self, score, beta, symbols):
        """Rank-weighted legs, each independently scaled to unit beta, then capped."""
        ranks = score.rank(method="average")
        centred = (ranks - ranks.mean()).to_numpy(dtype=float)
        betas = beta.reindex(score.index).to_numpy(dtype=float)

        long_leg = np.clip(centred, 0.0, None)
        short_leg = np.clip(-centred, 0.0, None)
        if int((long_leg > 0).sum()) < MIN_LEG or int((short_leg > 0).sum()) < MIN_LEG:
            return None

        cap = min(HARD_NAME_CAP, max(NAME_CAP, 1.2 / len(symbols)))
        long_leg = self._unit_leg(long_leg, 2.0 * cap)
        short_leg = self._unit_leg(short_leg, 2.0 * cap)
        if long_leg is None or short_leg is None:
            return None

        beta_long = float(np.clip(np.dot(long_leg, betas), BETA_FLOOR, BETA_CEIL))
        beta_short = float(np.clip(np.dot(short_leg, betas), BETA_FLOOR, BETA_CEIL))
        long_share = 1.0 / beta_long
        short_share = 1.0 / beta_short
        total = long_share + short_share
        long_share /= total
        short_share /= total

        net = long_share - short_share
        if abs(net) > NET_CAP:
            net = math.copysign(NET_CAP, net)
            long_share = 0.5 * (1.0 + net)
            short_share = 0.5 * (1.0 - net)

        long_leg = self._unit_leg(long_leg, min(0.95, cap / max(long_share, EPS)))
        short_leg = self._unit_leg(short_leg, min(0.95, cap / max(short_share, EPS)))
        if long_leg is None or short_leg is None:
            return None

        weights = long_share * long_leg - short_share * short_leg
        return self._emit(weights, symbols)

    def _unit_leg(self, leg, cap):
        """Non-negative leg vector, dust removed, summing to one under a per-name cap."""
        out = _cap_and_normalise(leg, cap)
        out = np.where(out < LEG_DUST, 0.0, out)
        if int((out > 0).sum()) < MIN_LEG:
            return None
        out = _cap_and_normalise(out, cap)
        return out if float(out.sum()) > EPS else None

    def _emit(self, weights, symbols):
        """Final protocol conformance: finite, gross <= 1, |net| <= 0.25, |w| <= 0.10."""
        weights = np.asarray(weights, dtype=float)
        if not np.all(np.isfinite(weights)):
            return None
        weights = np.clip(weights, -HARD_NAME_CAP, HARD_NAME_CAP)
        gross = float(np.abs(weights).sum())
        if gross <= EPS:
            return None
        if gross > 1.0:
            weights = weights / gross
        if abs(float(weights.sum())) > 0.25:
            return None
        book = {
            sym: float(w)
            for sym, w in zip(symbols, weights)
            if np.isfinite(w) and abs(float(w)) > EPS
        }
        return book if len(book) >= MIN_NAMES else None


def build_strategy():
    return DefensiveBetaControlledBook()
