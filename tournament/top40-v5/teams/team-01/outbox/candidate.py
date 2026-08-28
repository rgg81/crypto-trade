"""team-01 — cross-sectional funding carry, held slowly, discounted for crowding.

Diagnosis behind this build.  Trial t01 (the unmodified organiser seed) failed four
gates -- ``turnover_ceiling``, ``gross_edge_density``, ``cost_share`` and
``survives_triple_cost``.  Those are one failure, not four.  Backing gross return out
of the 1x and 3x net numbers (net(1)=G-C=-2.87%, net(3)=G-3C=-37.13%) gives
C ~ 17.1%/yr of cost against G ~ +14.3%/yr of gross edge on 289 turns of annual
turnover: roughly 5.9bp of cost per unit of turnover, and a gross Sharpe near 1.4.
The funding premium is present in this universe.  It is being spent on trading it.

So this is not a signal problem and it is not a parameter problem.  The mechanism
here pays for *holding* the side opposite the crowd -- the funding transfer accrues
every settlement whether or not I trade -- and the seed's construction converts that
into a high-frequency ranking exercise.  This build keeps the economics and rebuilds
the transport:

  * carry is an exponentially-weighted, 8h-*equivalent* funding accrual with a
    two-week centre of mass, so the tradable object is the funding regime rather
    than the funding print;
  * the settlement schedule is inferred from the data (Binance settles 8h/4h/1h by
    symbol and regime), so fast-settling names are not systematically mis-ranked;
  * the book is a soft-thresholded, rank-based tilt over the whole liquid
    cross-section rather than two hard quantile buckets, so names cross the leg
    boundary at zero weight instead of at full weight;
  * every input to the crowding overlay is slow by construction, so the overlay
    cannot inject turnover of its own.

Stateless by design: ``target_weights`` is a pure function of the context.  No RNG,
no persistence across decisions, no absolute dates, no symbol identity, no embedded
data, and every quantity is scale-free (ranks, log returns, ratios).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Organizer-reserved target-artifact column; never a tradable symbol.
RESERVED_COLUMN = "__crypto_trade_rebalance__"

BAR_HOURS = 8.0
NS_PER_HOUR = 3.6e12

# --- panel -----------------------------------------------------------------
TAIL_BARS = 200          # deepest window any statistic below needs, plus slack
MIN_BARS = 45            # listing burn-in: funding at listing is not tradable
MIN_NAMES = 14           # below this the book is not a portfolio; hold instead

# --- universe --------------------------------------------------------------
UNIVERSE_N = 75          # declared U
LIQ_WIN = 90             # declared 30-day median quote-volume screen

# --- carry -----------------------------------------------------------------
CARRY_TAU_H = 336.0      # exponential decay constant: 14-day centre of mass
CARRY_MAX_AGE_H = 1008.0 # 3 tau
MIN_FUNDING_ROWS = 8     # ~3 days of 8h settlements

# --- risk normalisation ----------------------------------------------------
VOL_WIN = 63             # declared trailing realised-vol window
VOL_FLOOR = 0.005        # 8h log-return floor; scale-free
MIN_VOL_OBS = 20

# --- beta neutralisation ---------------------------------------------------
BETA_WIN = 180
MIN_BETA_OBS = 40
BETA_SHRINK = 0.65       # shrink toward the cross-sectional unit beta
BETA_MAX_SHARE = 0.35    # hedge may not restructure more than this of the book

# --- crowding --------------------------------------------------------------
FLOW_FAST_HL = 21.0      # declared K = 21 bars (7d)
FLOW_SLOW_HL = 84.0      # reference level for the aggressor-share trend
CROWD_LAMBDA = 0.5       # declared overlay strength

# --- construction ----------------------------------------------------------
ACTIVE_FRAC = 0.50       # ~ declared q: top and bottom quarter carry the book
MIN_PER_SIDE = 7
MAX_WEIGHT = 0.10
TARGET_GROSS = 1.0


# --------------------------------------------------------------------------
# pure helpers
# --------------------------------------------------------------------------
def _floats(series: pd.Series) -> np.ndarray:
    """Numeric column as float64, with a free fast path when it already is."""
    arr = series.to_numpy()
    if arr.dtype.kind == "f":
        return arr
    if arr.dtype.kind in "iub":
        return arr.astype(np.float64)
    return pd.to_numeric(series, errors="coerce").to_numpy(dtype=np.float64)


def _epoch_ns(values) -> np.ndarray:
    """Timestamps as int64 nanoseconds since epoch, whatever they arrive as.

    Bare integer epochs are rescaled to nanoseconds by magnitude, so a millisecond
    column and ``decision_time`` cannot end up on different clocks -- that mismatch
    would filter every funding row away and hold a flat book without raising.
    """
    arr = np.asarray(values)
    if np.issubdtype(arr.dtype, np.datetime64):
        return arr.astype("datetime64[ns]").view("i8")
    if np.issubdtype(arr.dtype, np.integer) or arr.dtype.kind == "f":
        scaled = np.nan_to_num(arr.astype(np.float64), nan=0.0, posinf=0.0, neginf=0.0)
        magnitude = float(np.abs(scaled).max()) if scaled.size else 0.0
        if magnitude < 1e11:        # seconds
            factor = 1e9
        elif magnitude < 1e14:      # milliseconds
            factor = 1e6
        elif magnitude < 1e17:      # microseconds
            factor = 1e3
        else:                       # already nanoseconds
            factor = 1.0
        return (scaled * factor).astype(np.int64)
    converted = pd.to_datetime(pd.Series(arr), errors="coerce", utc=True)
    return converted.to_numpy().astype("datetime64[ns]").view("i8")


def _rank_pct(values: np.ndarray) -> np.ndarray:
    """Cross-sectional rank percentile in (0, 1), ties averaged."""
    n = values.size
    if n == 0:
        return values
    if n == 1:
        return np.full(1, 0.5)
    ranks = pd.Series(values).rank(method="average").to_numpy()
    out = (ranks - 0.5) / n
    return np.where(np.isfinite(out), out, 0.5)


def _fill_median(values: np.ndarray) -> np.ndarray:
    """Replace non-finite entries with the finite cross-sectional median."""
    finite = np.isfinite(values)
    if not finite.any():
        return np.zeros_like(values)
    filler = float(np.median(values[finite]))
    return np.where(finite, values, filler)


def _column_stat(block: np.ndarray, min_obs: int, fn) -> np.ndarray:
    """Apply a nan-aware column statistic only where enough observations exist."""
    counts = np.isfinite(block).sum(axis=0)
    out = np.full(block.shape[1], np.nan)
    usable = counts >= min_obs
    if usable.any():
        out[usable] = fn(block[:, usable])
    return out


def _soft_threshold_side(magnitude: np.ndarray, keep: int) -> np.ndarray:
    """Keep the ``keep`` largest magnitudes, softly: entrants arrive at zero weight."""
    size = magnitude.size
    if size == 0:
        return magnitude
    keep = int(min(max(keep, 1), size))
    if keep >= size:
        cut = 0.0
    else:
        cut = float(np.partition(magnitude, size - keep - 1)[size - keep - 1])
    return np.maximum(magnitude - cut, 0.0)


# --------------------------------------------------------------------------
# strategy
# --------------------------------------------------------------------------
class SlowFundingCarry:
    """Dollar- and beta-neutral cross-sectional funding carry with a crowding discount.

    Harvest direction, as preregistered: long the most-negative-funding names, short
    the most-positive.  The instance carries no mutable state; the same context
    always produces the same book.
    """

    def target_weights(self, context, *, seed):
        try:
            return self._book(context)
        except Exception:
            # Hold the existing book rather than abandoning it on a bad bar.
            return None

    # -- panel construction -------------------------------------------------
    @staticmethod
    def _panels(bars, symbols):
        """Align close / quote volume / taker-buy volume on ``open_time``.

        The per-symbol frames carry a positional index and unequal history, so the
        only correct alignment key is the timestamp column.  All frames are
        truncated at the same boundary, so the longest tail spans every other.
        """
        lengths = [len(bars[s]) for s in symbols]
        grid = _epoch_ns(bars[symbols[int(np.argmax(lengths))]]["open_time"].to_numpy()[-TAIL_BARS:])
        rows = grid.size
        cols = len(symbols)
        close = np.full((rows, cols), np.nan)
        qvol = np.full((rows, cols), np.nan)
        taker = np.full((rows, cols), np.nan)
        for j, symbol in enumerate(symbols):
            frame = bars[symbol].iloc[-TAIL_BARS:]
            stamps = _epoch_ns(frame["open_time"].to_numpy())
            slot = np.clip(np.searchsorted(grid, stamps), 0, rows - 1)
            hit = grid[slot] == stamps
            if not hit.any():
                continue
            target = slot[hit]
            close[target, j] = _floats(frame["close"])[hit]
            qvol[target, j] = _floats(frame["quote_volume"])[hit]
            taker[target, j] = _floats(frame["taker_buy_quote_volume"])[hit]
        return close, qvol, taker

    # -- funding ------------------------------------------------------------
    @staticmethod
    def _funding_features(funding, universe, decision_time):
        """8h-equivalent EW funding accrual, its sign-persistence, and a row count.

        Binance settles 8h, 4h or hourly depending on symbol and regime, and the
        published rate carries a ``/(8/N)`` divisor.  Ranking unadjusted per-interval
        rates therefore mis-ranks exactly the fast-settling, cap-pinned names this
        thesis is about.  The average interval is inferred per symbol from the
        spacing of its own settlements, and the accrual is rescaled to 8 hours.
        """
        count = len(universe)
        blank = (np.full(count, np.nan), np.full(count, np.nan), np.zeros(count))
        if funding is None or len(funding) == 0:
            return blank
        columns = funding.columns
        if "symbol" not in columns or "funding_rate" not in columns:
            return blank
        time_column = "settlement_time" if "settlement_time" in columns else "funding_time"
        if time_column not in columns:
            return blank

        stamps = _epoch_ns(funding[time_column].to_numpy())
        now_ns = pd.Timestamp(decision_time).value
        # Float subtraction: an int64 NaT sentinel would otherwise wrap silently.
        age_h = (float(now_ns) - stamps.astype(np.float64)) / NS_PER_HOUR
        recent = np.isfinite(age_h) & (age_h >= 0.0) & (age_h <= CARRY_MAX_AGE_H)
        if not recent.any():
            return blank

        codes = pd.Categorical(
            funding["symbol"].to_numpy()[recent], categories=list(universe)
        ).codes.astype(np.int64)
        rates = _floats(funding["funding_rate"])[recent]
        ages = age_h[recent]
        member = (codes >= 0) & np.isfinite(rates)
        if not member.any():
            return blank

        codes, rates, ages = codes[member], rates[member], ages[member]
        weights = np.exp(-ages / CARRY_TAU_H)
        table = pd.DataFrame(
            {
                "code": codes,
                "rate": rates,
                "age": ages,
                "w": weights,
                "wr": weights * rates,
                "absr": np.abs(rates),
            }
        )
        grouped = table.groupby("code", sort=True).agg(
            sw=("w", "sum"),
            swr=("wr", "sum"),
            n=("rate", "size"),
            oldest=("age", "max"),
            newest=("age", "min"),
            abs_sum=("absr", "sum"),
            signed_sum=("rate", "sum"),
        )
        grouped = grouped.reindex(np.arange(count))

        n = grouped["n"].to_numpy(dtype=np.float64)
        n = np.where(np.isfinite(n), n, 0.0)
        span = grouped["oldest"].to_numpy() - grouped["newest"].to_numpy()
        interval = np.where(n > 1.0, span / np.maximum(n - 1.0, 1.0), BAR_HOURS)
        interval = np.clip(np.where(np.isfinite(interval), interval, BAR_HOURS), 0.5, 24.0)

        sw = grouped["sw"].to_numpy()
        carry = BAR_HOURS * (grouped["swr"].to_numpy() / np.where(sw > 0, sw, np.nan)) / interval

        abs_sum = grouped["abs_sum"].to_numpy()
        # C1, staleness: magnitude-weighted sign persistence over the window.  One if
        # the premium has been one-signed throughout, zero if it has been balanced.
        persistence = np.abs(grouped["signed_sum"].to_numpy()) / np.where(abs_sum > 0, abs_sum, np.nan)
        return carry, persistence, n

    # -- book ---------------------------------------------------------------
    def _book(self, context):
        bars = context.bars
        seen = set()
        listed = []       # every eligible name, in context order, for an explicit flat default
        candidates = []
        for symbol in context.eligible_symbols:
            if not isinstance(symbol, str) or symbol == RESERVED_COLUMN or symbol in seen:
                continue
            seen.add(symbol)
            listed.append(symbol)
            frame = bars.get(symbol)
            if frame is None or len(frame) < MIN_BARS:
                continue
            if "open_time" not in frame.columns:
                continue
            candidates.append(symbol)
        if len(candidates) < MIN_NAMES:
            return None

        close, qvol, taker = self._panels(bars, candidates)

        # Liquidity screen: trailing median quote volume, then top-N.
        med_volume = _column_stat(qvol[-LIQ_WIN:, :], 10, lambda b: np.nanmedian(b, axis=0))
        tradable = np.where(np.isfinite(med_volume) & (med_volume > 0.0))[0]
        if tradable.size < MIN_NAMES:
            return None
        if tradable.size > UNIVERSE_N:
            keep = np.argsort(med_volume[tradable], kind="stable")[::-1][:UNIVERSE_N]
            tradable = np.sort(tradable[keep])
        universe = [candidates[i] for i in tradable]

        with np.errstate(divide="ignore", invalid="ignore"):
            prices = np.where(close[:, tradable] > 0.0, close[:, tradable], np.nan)
            log_returns = np.diff(np.log(prices), axis=0)

        vol = _column_stat(log_returns[-VOL_WIN:, :], MIN_VOL_OBS, lambda b: np.nanstd(b, axis=0))
        beta = self._betas(log_returns[-BETA_WIN:, :])
        carry, persistence, funding_rows = self._funding_features(
            context.funding, universe, context.decision_time
        )

        valid = (
            np.isfinite(carry)
            & np.isfinite(vol)
            & (vol > 0.0)
            & (funding_rows >= MIN_FUNDING_ROWS)
        )
        live = np.where(valid)[0]
        if live.size < MIN_NAMES:
            return None

        universe = [universe[i] for i in live]
        carry = carry[live]
        beta = _fill_median(beta[live])
        vol = np.maximum(vol[live], VOL_FLOOR)
        med_volume = med_volume[tradable][live]
        persistence = _fill_median(persistence[live])
        flow_trend = self._flow_trend(qvol[:, tradable], taker[:, tradable])[live]

        # ---- carry signal: harvest, risk-normalised, ranked -----------------
        # s = -f: long the payers of negative funding, short the payers of positive.
        tilt = _rank_pct(-carry / vol) * 2.0 - 1.0
        tilt -= tilt.mean()

        # ---- crowding composite --------------------------------------------
        c1 = _rank_pct(persistence)                                   # stale premium
        c2 = _rank_pct(-np.sign(carry) * _fill_median(flow_trend))    # flow no longer refreshed
        c3 = _rank_pct(_rank_pct(np.abs(carry)) - _rank_pct(np.log(med_volume)))  # carry per flow
        crowding = _rank_pct((c1 + c2 + c3) / 3.0)

        score = tilt * (1.0 - CROWD_LAMBDA * crowding)
        score -= score.mean()
        peak = float(np.max(np.abs(score)))
        if not np.isfinite(peak) or peak <= 0.0:
            return None
        score /= peak

        # ---- soft-thresholded, side-balanced construction -------------------
        weights = self._construct(score, beta)
        if weights is None:
            return None

        # Name every eligible symbol explicitly: an omitted symbol is an ambiguous
        # instruction, and a stale carried position is the expensive reading of it.
        book = {symbol: 0.0 for symbol in listed}
        for symbol, weight in zip(universe, weights):
            value = float(weight)
            if np.isfinite(value):
                book[symbol] = value
        return book

    @staticmethod
    def _betas(block: np.ndarray) -> np.ndarray:
        """Shrunk betas against the equal-weight eligible universe."""
        cols = block.shape[1]
        if block.shape[0] < MIN_BETA_OBS:
            return np.ones(cols)
        finite = np.isfinite(block)
        per_row = finite.sum(axis=1)
        row_sum = np.where(finite, block, 0.0).sum(axis=1)
        market = np.where(per_row > 0, row_sum / np.maximum(per_row, 1), np.nan)
        both = finite & np.isfinite(market)[:, None]
        x = np.where(both, block, 0.0)
        y = np.where(both, market[:, None], 0.0)
        n = both.sum(axis=0)
        safe = np.maximum(n, 1)
        mx = x.sum(axis=0) / safe
        my = y.sum(axis=0) / safe
        cov = (x * y).sum(axis=0) / safe - mx * my
        var = (y * y).sum(axis=0) / safe - my * my
        raw = np.where((n >= MIN_BETA_OBS) & (var > 0.0), cov / np.where(var > 0.0, var, 1.0), 1.0)
        raw = np.clip(np.where(np.isfinite(raw), raw, 1.0), 0.0, 3.0)
        return BETA_SHRINK * raw + (1.0 - BETA_SHRINK)

    @staticmethod
    def _flow_trend(qvol: np.ndarray, taker: np.ndarray) -> np.ndarray:
        """Trend in the aggressor-buy share: fast EW level minus slow EW level."""
        cols = qvol.shape[1]
        if qvol.shape[0] < 30:
            return np.zeros(cols)
        with np.errstate(divide="ignore", invalid="ignore"):
            share = np.where(qvol > 0.0, taker / qvol, np.nan)
        frame = pd.DataFrame(np.where(np.isfinite(share), share, np.nan))
        fast = frame.ewm(halflife=FLOW_FAST_HL, min_periods=10, ignore_na=True).mean()
        slow = frame.ewm(halflife=FLOW_SLOW_HL, min_periods=20, ignore_na=True).mean()
        return fast.to_numpy()[-1] - slow.to_numpy()[-1]

    @staticmethod
    def _construct(score: np.ndarray, beta: np.ndarray):
        """Soft-threshold both sides, balance them, hedge beta, cap and normalise."""
        n = score.size
        per_side = int(min(max(MIN_PER_SIDE, round(0.5 * ACTIVE_FRAC * n)), n // 2))
        weights = np.zeros(n)
        for sign in (1.0, -1.0):
            side = np.where(np.sign(score) == sign)[0]
            if side.size == 0:
                continue
            weights[side] = sign * _soft_threshold_side(np.abs(score[side]), per_side)

        longs = weights > 0.0
        shorts = weights < 0.0
        long_gross = float(weights[longs].sum())
        short_gross = float(-weights[shorts].sum())
        if long_gross <= 0.0 or short_gross <= 0.0:
            return None
        if (longs.sum() + shorts.sum()) < MIN_NAMES:
            return None
        half = 0.5 * (long_gross + short_gross)
        weights[longs] *= half / long_gross
        weights[shorts] *= half / short_gross

        # Beta hedge inside the active set only: a demeaned adjustment there sums to
        # zero, so dollar neutrality survives and dormant names are not woken up.
        active = np.where(weights != 0.0)[0]
        if active.size >= 8:
            b = beta[active]
            centred = b - b.mean()
            denom = float(centred @ centred)
            if denom > 1e-10:
                adjustment = (float(weights[active] @ b) / denom) * centred
                gross = float(np.abs(weights[active]).sum())
                size = float(np.abs(adjustment).sum())
                if size > BETA_MAX_SHARE * gross and size > 0.0:
                    adjustment *= BETA_MAX_SHARE * gross / size
                weights[active] -= adjustment

        total = float(np.abs(weights).sum())
        if not np.isfinite(total) or total <= 0.0:
            return None
        weights *= TARGET_GROSS / total
        for _ in range(3):
            if not (np.abs(weights) > MAX_WEIGHT).any():
                break
            weights = np.clip(weights, -MAX_WEIGHT, MAX_WEIGHT)
            total = float(np.abs(weights).sum())
            if total <= 0.0:
                return None
            weights *= TARGET_GROSS / total
        weights = np.clip(weights, -MAX_WEIGHT, MAX_WEIGHT)

        # Final dollar-neutrality pass; clipping is the only step that can break it.
        longs = weights > 0.0
        shorts = weights < 0.0
        long_gross = float(weights[longs].sum())
        short_gross = float(-weights[shorts].sum())
        if long_gross > 0.0 and short_gross > 0.0:
            half = 0.5 * (long_gross + short_gross)
            weights[longs] *= half / long_gross
            weights[shorts] *= half / short_gross
        weights = np.clip(weights, -MAX_WEIGHT, MAX_WEIGHT)

        total = float(np.abs(weights).sum())
        if total > TARGET_GROSS:
            weights *= TARGET_GROSS / total
        return weights


def build_strategy():
    """Factory used by the common runner."""
    return SlowFundingCarry()
