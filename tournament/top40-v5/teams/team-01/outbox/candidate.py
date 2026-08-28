"""team-01 nomination — cross-sectional funding carry, held on a three-day clock.

Mechanism, in one line: funding is a pure transfer from levered directional longs to whoever
is willing to warehouse them, so hold notional of the sign opposite to funding -- long the
most-negative-funding names, short the most-positive -- and collect the transfer.

The premium accrues to the **holder**, not to the trader.  Both charged trials failed on cost,
not on signal, and the two packets identify the cost exactly: ``gross_edge_bps_per_turnover x
cost_share_of_positive_gross`` equals 7.500 in both, so the venue charges 7.5 bp per unit of
annualised turnover and survival at triple cost is the single condition ``gross edge density >
22.5 bp``.  Everything structural below exists to put density there:

  * one 63-bar regime horizon drives both the carry estimate and the risk estimate, so the
    tradable object is the funding regime rather than the funding print;
  * the book is rebalanced on a nine-bar (three-day) clock derived from the panel's own
    origin, and holds in between -- re-establishing the same book every eight hours is the
    waste that consumed the premium in both prior trials;
  * legs are fixed-size and inverse-vol weighted inside each leg, so there is no book-wide
    renormalisation, no soft-threshold cut and no beta overlay moving every weight every bar;
  * crowding protection is expressed entirely through *selection and eligibility* -- a
    capacity discount, a cap-pinned tail trim, carry-to-risk normalisation and inverse-vol
    weighting -- so it costs no turnover of its own.

Stateless by construction: ``target_weights`` is a pure function of the context.  No RNG, no
persistence across decisions, no absolute dates, no symbol identity, no embedded data, and
every quantity is scale-free (ranks, log returns, ratios).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Organizer-reserved target-artifact column; never a tradable symbol.
RESERVED_COLUMN = "__crypto_trade_rebalance__"

BAR_HOURS = 8.0
NS_PER_HOUR = 3.6e12

# --- panel -----------------------------------------------------------------
TAIL_BARS = 200          # deepest window below (beta, 180 returns) plus slack
MIN_BARS = 95            # listing burn-in; funding at listing is not tradable carry
MIN_NAMES = 25           # below this the cross-section cannot carry two legs

# --- universe --------------------------------------------------------------
UNIVERSE_N = 75          # declared U
LIQ_WIN = 90             # declared 30-day median quote-volume screen

# --- one regime horizon, used for both carry and risk ----------------------
REGIME_BARS = 63.0
CARRY_TAU_H = BAR_HOURS * REGIME_BARS    # 504h, a 21-day centre of mass
CARRY_MAX_AGE_H = 3.0 * CARRY_TAU_H
MIN_FUNDING_ROWS = 6
VOL_WIN = 63
MIN_VOL_OBS = 20
VOL_FLOOR = 0.004        # 8h log-return floor; a ratio, so scale-free

# --- beta ------------------------------------------------------------------
BETA_WIN = 180
MIN_BETA_OBS = 40
BETA_SHRINK = 0.65       # shrink toward the cross-sectional unit beta

# --- selection -------------------------------------------------------------
TAIL_TRIM = 0.02         # declared T: cap-pinned prints are not tradable carry
CROWD_LAMBDA = 0.5       # declared overlay strength, applied to selection only
LEG_FRACTION = 0.15      # inside the declared q range {0.10, 0.20}
MIN_PER_LEG = 8
MAX_PER_LEG = 20

# --- weighting -------------------------------------------------------------
INV_VOL_LO = 0.7         # inverse-vol multiplier clipped to [0.7, 1.5] x leg mean
INV_VOL_HI = 1.5
LEG_GROSS = 0.4975       # each leg; total gross 0.995, inside the 1.0 contract cap
MAX_WEIGHT = 0.095       # inside the 0.10 contract cap

# --- clock -----------------------------------------------------------------
REBALANCE_BARS = 9       # three days at the data's native 8h resolution


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

    Bare integer epochs are rescaled by magnitude, so a millisecond column and
    ``decision_time`` cannot end up on different clocks -- that mismatch would filter every
    funding row away and hold a flat book without raising anything.
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


def _residualise(target: np.ndarray, factor: np.ndarray) -> np.ndarray:
    """Strip the ``factor`` component out of ``target`` cross-sectionally."""
    centred_factor = factor - factor.mean()
    denominator = float(centred_factor @ centred_factor)
    centred_target = target - target.mean()
    if not np.isfinite(denominator) or denominator <= 0.0:
        return centred_target
    loading = float(centred_target @ centred_factor) / denominator
    return centred_target - loading * centred_factor


def _leg_weights(vol: np.ndarray) -> np.ndarray:
    """Inverse-volatility weights inside one leg, bounded and capped.

    Equal risk contribution rather than equal notional: a name whose realised volatility has
    already expanded -- which in this universe means a name inside a liquidation cascade --
    carries proportionally less of the book.  The multiplier is clipped to a 2.1:1 band so
    the leg cannot collapse onto one name, and so effective breadth stays near the name count.
    """
    inverse = 1.0 / np.maximum(vol, VOL_FLOOR)
    reference = float(inverse.mean())
    if not np.isfinite(reference) or reference <= 0.0:
        return np.full(vol.size, LEG_GROSS / max(vol.size, 1))
    inverse = np.clip(inverse, INV_VOL_LO * reference, INV_VOL_HI * reference)
    total = float(inverse.sum())
    if not np.isfinite(total) or total <= 0.0:
        return np.full(vol.size, LEG_GROSS / max(vol.size, 1))
    weights = LEG_GROSS * inverse / total

    # Respect the per-symbol cap without letting the leg fall short of its gross.
    for _ in range(4):
        over = weights > MAX_WEIGHT
        if not over.any():
            break
        weights = np.minimum(weights, MAX_WEIGHT)
        free = ~over
        slack = LEG_GROSS - float(weights.sum())
        free_total = float(weights[free].sum()) if free.any() else 0.0
        if slack <= 0.0 or free_total <= 0.0:
            break
        weights[free] *= (free_total + slack) / free_total
    return np.minimum(weights, MAX_WEIGHT)


def _bar_phase(bars, decision_time, modulus: int) -> int:
    """Bar index modulo ``modulus``, measured from the panel's own origin.

    The origin is the earliest ``open_time`` anywhere in the panel and the step is the median
    bar spacing of the longest frame, so the phase is invariant to a shift of the whole
    calendar (origin and decision move together), to symbol pseudonymisation (a minimum over
    all names), and to appended future rows (frames are truncated at the boundary).  No
    absolute date is referenced anywhere.
    """
    origin = None
    widest = -1
    reference = None
    for symbol in sorted(bars):
        frame = bars[symbol]
        if frame is None or len(frame) == 0 or "open_time" not in frame.columns:
            continue
        first = _epoch_ns(frame["open_time"].to_numpy()[:1])
        if first.size == 0:
            continue
        value = int(first[0])
        if origin is None or value < origin:
            origin = value
        if len(frame) > widest:
            widest = len(frame)
            reference = symbol
    if origin is None or reference is None:
        return 0  # degrade to rebalancing rather than to a frozen book

    stamps = _epoch_ns(bars[reference]["open_time"].to_numpy()[-64:])
    gaps = np.diff(stamps.astype(np.float64))
    gaps = gaps[np.isfinite(gaps) & (gaps > 0.0)]
    if gaps.size == 0:
        return 0
    step = float(np.median(gaps))
    if not np.isfinite(step) or step <= 0.0:
        return 0
    now = float(pd.Timestamp(decision_time).value)
    index = int(round((now - float(origin)) / step))
    return index % int(modulus)


# --------------------------------------------------------------------------
# strategy
# --------------------------------------------------------------------------
class HeldFundingCarry:
    """Dollar-neutral cross-sectional funding carry, selected for capacity, held three days.

    Harvest direction, as preregistered: long the most-negative-funding names, short the
    most-positive.  The instance carries no mutable state; the same context always produces
    the same instruction.
    """

    def target_weights(self, context, *, seed):
        try:
            if _bar_phase(context.bars, context.decision_time, REBALANCE_BARS) != 0:
                # Hold.  The funding transfer accrues to the holder at every settlement
                # whether or not the book is touched, so trading between decisions is pure
                # cost against a premium that is already being collected.
                return None
            return self._book(context)
        except Exception:
            # Hold the existing book rather than abandoning it on a single bad bar.
            return None

    # -- panel construction -------------------------------------------------
    @staticmethod
    def _panels(bars, symbols):
        """Align close and quote volume on the ``open_time`` column.

        The per-symbol frames carry a positional index and unequal history, so the timestamp
        column is the only correct alignment key; concatenating on the index would return an
        almost entirely empty panel and an empty book that raises nothing.
        """
        lengths = [len(bars[s]) for s in symbols]
        longest = symbols[int(np.argmax(lengths))]
        grid = _epoch_ns(bars[longest]["open_time"].to_numpy()[-TAIL_BARS:])
        rows = grid.size
        cols = len(symbols)
        close = np.full((rows, cols), np.nan)
        qvol = np.full((rows, cols), np.nan)
        if rows == 0:
            return close, qvol
        for j, symbol in enumerate(symbols):
            frame = bars[symbol].iloc[-TAIL_BARS:]
            stamps = _epoch_ns(frame["open_time"].to_numpy())
            slot = np.clip(np.searchsorted(grid, stamps), 0, max(rows - 1, 0))
            hit = grid[slot] == stamps
            if not hit.any():
                continue
            target = slot[hit]
            close[target, j] = _floats(frame["close"])[hit]
            if "quote_volume" in frame.columns:
                qvol[target, j] = _floats(frame["quote_volume"])[hit]
        return close, qvol

    # -- funding ------------------------------------------------------------
    @staticmethod
    def _carry(funding, universe, decision_time):
        """Exponentially weighted 8h-equivalent funding accrual, and a settlement count.

        Binance settles 8h, 4h or hourly depending on symbol and regime, and the published
        rate carries a ``/(8/N)`` divisor, so ranking unadjusted per-interval rates
        systematically mis-ranks exactly the fast-settling, cap-pinned names this mandate is
        about.  The mean interval is inferred per symbol from the spacing of its own
        settlements and the accrual is rescaled to eight hours.

        Positive means longs pay shorts, so the harvest signal is its negation.
        """
        count = len(universe)
        blank = (np.full(count, np.nan), np.zeros(count))
        if funding is None or len(funding) == 0:
            return blank
        columns = funding.columns
        if "symbol" not in columns or "funding_rate" not in columns:
            return blank
        time_column = None
        for name in ("settlement_time", "funding_time"):
            if name in columns:
                time_column = name
                break
        if time_column is None:
            return blank

        stamps = _epoch_ns(funding[time_column].to_numpy())
        now_ns = float(pd.Timestamp(decision_time).value)
        # Float subtraction: an int64 NaT sentinel would otherwise wrap silently.
        age_h = (now_ns - stamps.astype(np.float64)) / NS_PER_HOUR
        fresh = np.isfinite(age_h) & (age_h >= 0.0) & (age_h <= CARRY_MAX_AGE_H)
        if not fresh.any():
            return blank

        codes = pd.Categorical(
            funding["symbol"].to_numpy()[fresh], categories=list(universe)
        ).codes.astype(np.int64)
        rates = _floats(funding["funding_rate"])[fresh]
        ages = age_h[fresh]
        member = (codes >= 0) & np.isfinite(rates)
        if not member.any():
            return blank

        codes, rates, ages = codes[member], rates[member], ages[member]
        decay = np.exp(-ages / CARRY_TAU_H)
        table = pd.DataFrame(
            {
                "code": codes,
                "rate": rates,
                "age": ages,
                "w": decay,
                "wr": decay * rates,
            }
        )
        grouped = table.groupby("code", sort=True).agg(
            sw=("w", "sum"),
            swr=("wr", "sum"),
            n=("rate", "size"),
            oldest=("age", "max"),
            newest=("age", "min"),
        )
        grouped = grouped.reindex(np.arange(count))

        n = grouped["n"].to_numpy(dtype=np.float64)
        n = np.where(np.isfinite(n), n, 0.0)
        span = grouped["oldest"].to_numpy() - grouped["newest"].to_numpy()
        interval = np.where(n > 1.0, span / np.maximum(n - 1.0, 1.0), BAR_HOURS)
        interval = np.clip(np.where(np.isfinite(interval), interval, BAR_HOURS), 0.5, 24.0)

        sw = grouped["sw"].to_numpy()
        carry = BAR_HOURS * (grouped["swr"].to_numpy() / np.where(sw > 0.0, sw, np.nan)) / interval
        return carry, n

    @staticmethod
    def _betas(block: np.ndarray) -> np.ndarray:
        """Shrunk betas against the equal-weight return of the eligible universe."""
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

    # -- book ---------------------------------------------------------------
    def _book(self, context):
        bars = context.bars
        seen = set()
        listed = []       # every eligible name, so nothing is carried by omission
        candidates = []
        for symbol in context.eligible_symbols:
            if not isinstance(symbol, str) or symbol == RESERVED_COLUMN or symbol in seen:
                continue
            seen.add(symbol)
            listed.append(symbol)
            frame = bars.get(symbol)
            if frame is None or len(frame) < MIN_BARS:
                continue
            if "open_time" not in frame.columns or "close" not in frame.columns:
                continue
            candidates.append(symbol)
        candidates.sort()
        if len(candidates) < MIN_NAMES:
            return None

        close, qvol = self._panels(bars, candidates)

        # ---- universe: seasoned, priced, and in the liquid top-N ------------
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
        carry, funding_rows = self._carry(context.funding, universe, context.decision_time)
        liquidity = med_volume[tradable]

        live = np.where(
            np.isfinite(carry)
            & np.isfinite(vol)
            & (vol > 0.0)
            & (funding_rows >= MIN_FUNDING_ROWS)
        )[0]
        if live.size < MIN_NAMES:
            return None

        universe = [universe[i] for i in live]
        carry = carry[live]
        vol = np.maximum(vol[live], VOL_FLOOR)
        beta = _fill_median(beta[live])
        liquidity = liquidity[live]

        # ---- cap-pinned tail trim -------------------------------------------
        # At the funding cap the printed rate no longer clears the imbalance, so it stops
        # being a measurement of the premium; it is also where the cascade lands.  Dropping
        # both raw tails is the cheapest available expression of "not the last holder", and
        # because it is an eligibility rule it costs no turnover.
        size = carry.size
        trim = int(np.floor(TAIL_TRIM * size))
        if trim > 0 and size > 6 * trim:
            order = np.argsort(carry, kind="stable")
            keep = np.sort(order[trim:size - trim])
            universe = [universe[i] for i in keep]
            carry, vol, beta, liquidity = carry[keep], vol[keep], beta[keep], liquidity[keep]
        count = carry.size
        if count < MIN_NAMES:
            return None

        # ---- signal: harvest, risk-normalised, ranked, beta-residualised -----
        # s = -f: long the receivers of negative funding, short the payers of positive.
        # Ranking corrects an exchange-mechanical bias as well as a statistical one -- the
        # funding cap scales with the maintenance margin ratio, which is itself larger for
        # riskier alts, so a raw-funding sort mechanically overweights junk.  Dividing by
        # realised volatility does the same for the cascade names, whose volatility has
        # already expanded by the time their funding is extreme.
        tilt = 2.0 * _rank_pct(-carry / vol) - 1.0
        tilt = _residualise(tilt, beta)

        # ---- crowding: capacity, applied to selection rather than to weights -
        # A large premium sitting on thin turnover is not a harvestable premium: there is no
        # capacity behind it and no exit, which is precisely the state in which being the
        # last holder is expensive.  The discount shrinks the magnitude of a tilt
        # symmetrically, so it moves names toward the middle of the book rather than moving
        # the book in one direction, and because both inputs are 63-90 bar statistics it
        # introduces no churn of its own.
        crowding = 1.0 - _rank_pct(liquidity)
        score = tilt * (1.0 - CROWD_LAMBDA * crowding)
        score = score - score.mean()
        if not np.isfinite(score).all():
            return None

        # ---- fixed-size legs, inverse-vol inside each ------------------------
        per_leg = int(round(LEG_FRACTION * count))
        per_leg = max(MIN_PER_LEG, min(per_leg, MAX_PER_LEG, count // 3))
        if per_leg < MIN_PER_LEG or 2 * per_leg > count:
            return None

        order = np.argsort(score, kind="stable")
        short_leg = order[:per_leg]
        long_leg = order[count - per_leg:]

        long_weights = _leg_weights(vol[long_leg])
        short_weights = _leg_weights(vol[short_leg])
        gross = min(float(long_weights.sum()), float(short_weights.sum()))
        if not np.isfinite(gross) or gross <= 0.0:
            return None
        long_weights *= gross / float(long_weights.sum())
        short_weights *= gross / float(short_weights.sum())

        weights = np.zeros(count)
        weights[long_leg] = long_weights
        weights[short_leg] = -short_weights

        total = float(np.abs(weights).sum())
        if not np.isfinite(total) or total <= 0.0:
            return None
        if total > 2.0 * LEG_GROSS:
            weights *= (2.0 * LEG_GROSS) / total

        # Name every eligible symbol explicitly: an omitted symbol is an ambiguous
        # instruction, and a stale carried position is the expensive reading of it.
        book = {symbol: 0.0 for symbol in listed}
        for symbol, weight in zip(universe, weights):
            value = float(weight)
            if np.isfinite(value):
                book[symbol] = value
        return book


def build_strategy():
    """Factory used by the common runner."""
    return HeldFundingCarry()
