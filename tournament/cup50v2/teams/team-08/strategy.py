"""Fade the forced-flow half of a volume shock, and cut the half that was repricing.

The lane's hazard is stated in one line: a genuine repricing looks identical to a cascade for one
bar. Two things separate them here, and neither needs to know what the news was.

The first is context. A shock that drives a name *against* its prevailing drift is flow -- a margin
call or a squeeze, forced by position, not by information -- and it overshoots. A shock that
extends the drift is the market agreeing with itself, and fading it is the way this lane dies. The
book therefore trades only the first kind.

The second is what happens next. A cascade stops; a repricing keeps going. So every fade carries a
volatility-scaled stop measured from the shock bar's own close, and a position that keeps losing is
closed as soon as it has proved itself to be the other kind of event. Everything else is the naive
construction: an event is an extreme move on abnormal turnover, each fade is held for a fixed
number of bars and then flattened, and the book is empty whenever nothing has happened.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd

from crypto_trade.cup50v2 import toolkit
from crypto_trade.cup50v2.protocol import DecisionContextV2, TargetStrategyV2

# One trailing month defines "normal" for both halves of the event test, so the two cannot
# disagree about what they are measuring against.
_REFERENCE_BARS = toolkit.bars_for_days(30)
_SIGMA_BARS = _REFERENCE_BARS
_MIN_SIGMA_BARS = 30
_SYMBOL_CAP = 0.15
# Every statistic below reads a fixed number of trailing bars, so the decision only ever needs
# that many. Materialising the whole year at each of three daily boundaries costs a hundredfold
# more arithmetic and changes nothing it computes.
_CONTEXT_BARS = 400


def _tail_panel(context: DecisionContextV2, column: str) -> pd.DataFrame:
    """Wide view of the last ``_CONTEXT_BARS`` observations per eligible symbol, oldest first."""
    columns = {}
    for symbol in context.eligible_symbols:
        history = context.bars.get(symbol)
        if history is None or history.empty or column not in history:
            continue
        frame = history.tail(_CONTEXT_BARS)
        series = frame.set_index("close_time")[column]
        columns[str(symbol)] = series[~series.index.duplicated(keep="last")]
    if not columns:
        return pd.DataFrame()
    return pd.DataFrame(columns).sort_index()


class VolumeShockEventReversal:
    """Short the forced pop, buy the forced flush, hold on the clock, and stop out of repricing."""

    # --- declared dimensions -------------------------------------------------------------
    k_sigma = 2.0        # how extreme the bar's move has to be, in trailing bar sigmas
    vol_mult = 3.5       # how abnormal the bar's traded value has to be, versus its own month
    hold_bars = 75       # outer clock exit, in 8h bars
    stop_sigma = 1.5     # adverse excursion from the shock close that ends a fade, in bar sigmas
    # --- held fixed at the centre ---------------------------------------------------------
    trend_bars = 60      # window of the prevailing drift the shock has to oppose
    trend_min = 0.25     # the drift must be this many random-walk sigmas from zero to count
    cooldown_bars = 30   # re-entry ban after an event, in 8h bars
    max_open = 15        # concurrent fades; event scarcity binds long before this does

    def __init__(self) -> None:
        # Nothing in a single decision's context records which bar a position was opened on, so an
        # event book has to carry its own roster. Everything in it is derived from bars that had
        # already closed when the position was opened.
        self._open: dict[str, dict[str, object]] = {}
        self._cooldown: dict[str, pd.Timestamp] = {}

    # ---------------------------------------------------------------------------- interface
    def target_weights(
        self, context: DecisionContextV2, *, seed: int
    ) -> Mapping[str, float] | None:
        now = pd.Timestamp(context.decision_time)
        eligible = [str(symbol) for symbol in context.eligible_symbols]
        eligible_set = set(eligible)
        panel = _tail_panel(context, "close")
        sigma_bar = self._bar_sigma(panel)

        before = self._roster()
        self._retire(now, eligible_set, panel, sigma_bar)
        self._enter(context, panel, sigma_bar, now, eligible_set)
        after = self._roster()

        if after == before and before:
            # An event book trades on events. Between them the roster is unchanged and holding the
            # existing quantities costs nothing, where restating the same weights every eight hours
            # would pay the spread three times a day to stand still.
            return None
        if not self._open:
            return {} if before else None

        annual = sigma_bar * math.sqrt(toolkit.BARS_PER_YEAR)
        signals = {symbol: float(state["direction"]) for symbol, state in self._open.items()}
        return toolkit.vol_parity(signals, annual, neutral=True, symbol_cap=_SYMBOL_CAP)

    # ------------------------------------------------------------------------------ helpers
    def _roster(self) -> tuple[tuple[str, float], ...]:
        return tuple(
            sorted((symbol, float(state["direction"])) for symbol, state in self._open.items())
        )

    @staticmethod
    def _bar_sigma(panel: pd.DataFrame) -> pd.Series:
        """Per-bar volatility of log returns over the trailing month."""
        if panel.empty or len(panel) < 3:
            return pd.Series(dtype=float)
        logs = np.log(panel).diff().replace([np.inf, -np.inf], np.nan)
        window = logs.tail(_SIGMA_BARS)
        counts = window.notna().sum()
        sigma = window.std(ddof=1)
        return sigma.where(counts >= _MIN_SIGMA_BARS).dropna()

    def _retire(
        self,
        now: pd.Timestamp,
        eligible: set[str],
        panel: pd.DataFrame,
        sigma_bar: pd.Series,
    ) -> None:
        """Close on the clock, on the stop, or on losing eligibility; release expired bans.

        The clock states the thesis -- the overshoot decays over days, so the exit is dated, not
        optimised. The stop states the hazard: a fade that keeps losing was never a cascade, and
        holding it to the clock is how a reversal book turns one bad classification into a
        drawdown.
        """
        horizon = int(max(1, self.hold_bars))
        stop = float(self.stop_sigma)
        latest = panel.iloc[-1] if not panel.empty else pd.Series(dtype=float)
        for symbol, state in list(self._open.items()):
            if symbol not in eligible:
                del self._open[symbol]
                continue
            if int(state["age"]) + 1 >= horizon:
                del self._open[symbol]
                continue
            state["age"] = int(state["age"]) + 1
            if stop <= 0.0:
                continue
            reference = float(state["reference"])
            scale = float(state["sigma"])
            price = float(latest.get(symbol, float("nan")))
            if not math.isfinite(price) or price <= 0.0 or reference <= 0.0 or scale <= 0.0:
                continue
            excursion = float(state["direction"]) * (price / reference - 1.0)
            if excursion <= -stop * scale:
                del self._open[symbol]
        for symbol, release in list(self._cooldown.items()):
            if now >= release:
                del self._cooldown[symbol]

    def _enter(
        self,
        context: DecisionContextV2,
        panel: pd.DataFrame,
        sigma_bar: pd.Series,
        now: pd.Timestamp,
        eligible: set[str],
    ) -> None:
        shocks = self._shocks(context, panel, sigma_bar)
        if shocks.empty:
            return
        latest = panel.iloc[-1]
        ranked = sorted(shocks.index, key=lambda name: (-abs(float(shocks[name])), str(name)))
        room = max(0, int(self.max_open)) - len(self._open)
        for symbol in ranked:
            if room <= 0:
                break
            if symbol not in eligible or symbol in self._open or symbol in self._cooldown:
                continue
            move = float(shocks[symbol])
            reference = float(latest.get(symbol, float("nan")))
            scale = float(sigma_bar.get(symbol, float("nan")))
            if not math.isfinite(reference) or reference <= 0.0:
                continue
            if not math.isfinite(scale) or scale <= 0.0:
                continue
            self._open[symbol] = {
                "direction": -1.0 if move > 0.0 else 1.0,
                "age": 0,
                "reference": reference,
                "sigma": scale,
            }
            # A name that keeps printing events is repricing, not liquidating, so it is barred
            # for a fixed span after each event rather than for as long as the trade happens to
            # live. Tying the ban to the clock made the clock two knobs wearing one name.
            self._cooldown[symbol] = now + pd.Timedelta(
                hours=8 * int(max(1, self.cooldown_bars))
            )
            room -= 1

    def _shocks(
        self, context: DecisionContextV2, panel: pd.DataFrame, sigma_bar: pd.Series
    ) -> pd.Series:
        """Signed returns of names whose last bar was extreme, abnormal, and against the drift."""
        trend_bars = int(max(1, self.trend_bars))
        if panel.empty or sigma_bar.empty or len(panel) <= trend_bars + 2:
            return pd.Series(dtype=float)
        moves = toolkit.trailing_return(panel, 1)
        volume = _tail_panel(context, "quote_volume")
        if moves.empty or len(volume) <= _REFERENCE_BARS:
            return pd.Series(dtype=float)
        latest_volume = volume.iloc[-1]
        # The shock bar is excluded from its own reference: a big print must not raise the bar it
        # has to clear.
        usual_volume = volume.iloc[-1 - _REFERENCE_BARS : -1].median()
        # The drift is measured up to the bar *before* the shock, so a violent enough move cannot
        # define the trend it is supposed to be opposing.
        prior = panel.iloc[-2]
        earlier = panel.iloc[-2 - trend_bars]
        fired: dict[str, float] = {}
        for symbol in moves.index:
            move = float(moves[symbol])
            scale = float(sigma_bar.get(symbol, float("nan")))
            if not math.isfinite(scale) or scale <= 0.0:
                continue
            if abs(move) <= self.k_sigma * scale:
                continue
            traded = float(latest_volume.get(symbol, float("nan")))
            normal = float(usual_volume.get(symbol, float("nan")))
            if not math.isfinite(traded) or not math.isfinite(normal) or normal <= 0.0:
                continue
            if traded <= self.vol_mult * normal:
                continue
            start = float(earlier.get(symbol, float("nan")))
            end = float(prior.get(symbol, float("nan")))
            if not math.isfinite(start) or not math.isfinite(end) or start <= 0.0:
                continue
            drift = end / start - 1.0
            # "Against the drift" is only a statement when there is a drift. A name whose prior
            # move is inside the noise of a random walk of the same length has no direction for the
            # shock to oppose, and reading a sign off that noise is how the gate becomes a coin
            # toss at exactly the moments -- market turns -- when it matters most.
            if abs(drift) <= self.trend_min * scale * math.sqrt(trend_bars):
                continue
            if (drift > 0.0) == (move > 0.0):
                continue  # with the drift: repricing, not forced flow
            fired[str(symbol)] = move
        return pd.Series(fired, dtype=float)


def build_strategy() -> TargetStrategyV2:
    return VolumeShockEventReversal()
