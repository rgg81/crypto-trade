"""Blended residual cross-sectional momentum, distress-filtered, with a rebound guard.

Almost all of an altcoin's variance is market beta, so a raw cross-sectional momentum book is
mostly a leveraged bet on the index that works right up until the index turns.  This lane ranks
names on what survives once the market factor is taken out twice over: the beta-implied move is
subtracted from each formation return, and the surviving score is then made orthogonal to the
cross-section's own beta and traded-value ranks, because an estimated beta leaves a residual tilt
and because in this universe liquidity is itself a priced factor.

Three things separate the book from the obvious version of that idea.

*It does not pick a formation window or a skip.*  One horizon is one opinion about where a trend
starts and one skip is one opinion about where it stops being a trend, and on the research window
each opinion is worth several points in either direction with no stable interior best.  So the same
residual is read over a grid of five formation lengths and three skipped stretches and the
cross-sectional ranks are averaged.  The view survives; the two arbitrary choices do not.

*It refuses to read a collapse as a momentum observation.*  A name that has fallen by half, or far
past what the market did, over the days being skipped is not a slow-moving trend: it is a
distressed asset whose short leg is a squeeze lottery and whose long leg is a falling knife.  It is
dropped from the cross-section for that decision.  This is the largest signal control in the book.

*It stands down after a deep index drawdown turns up.*  That is the momentum crash the lane is
known for -- the names the book is short rebound hardest -- and it is where an unguarded residual
book takes its worst loss.  The guard is binary because a smaller book is not something a team owns:
the common risk unit prices whatever shape it is handed and scales a halved book straight back up.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from crypto_trade.cup50v2 import toolkit
from crypto_trade.cup50v2.protocol import DecisionContextV2, TargetStrategyV2

# A cross-section too thin to rank is not a cross-section; below this the book stands down.
MIN_NAMES = 20
# A name must have traded through at least this share of its formation window to be ranked.
COVERAGE = 0.80


def _rank_centred(values: np.ndarray) -> np.ndarray:
    """Ranks mapped to [-0.5, 0.5]: scale-free, outlier-proof, and averageable across horizons."""
    order = np.argsort(np.argsort(values, kind="stable"), kind="stable").astype(float)
    return (order + 0.5) / len(values) - 0.5


def _neutralise(score: np.ndarray, factors: list[np.ndarray]) -> np.ndarray:
    """Cross-sectional OLS residual of ``score`` on an intercept and the given factors.

    Written as explicit Gram-Schmidt rather than ``lstsq`` so the arithmetic is a fixed sequence of
    small dot products: the evaluator requires determinism across worker counts and hash seeds, and
    a least-squares driver is the one place in this source where a library could reorder a
    reduction.
    """
    residual = score - float(score.mean())
    basis: list[np.ndarray] = []
    for factor in factors:
        vector = factor - float(factor.mean())
        for previous in basis:
            vector = vector - float(vector @ previous) * previous
        norm = math.sqrt(float(vector @ vector))
        if norm > 1e-12:
            basis.append(vector / norm)
    for previous in basis:
        residual = residual - float(residual @ previous) * previous
    return residual


def _pairwise_beta(returns: np.ndarray, reference: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-name slope on the index, using each name's own overlapping observations."""
    mask = np.isfinite(returns) & np.isfinite(reference)[:, None]
    y = np.where(mask, returns, 0.0)
    x = np.where(mask, reference[:, None], 0.0)
    n = mask.sum(axis=0).astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        sx, sy = x.sum(axis=0), y.sum(axis=0)
        var = (x * x).sum(axis=0) - sx * sx / np.where(n > 0, n, np.nan)
        cov = (x * y).sum(axis=0) - sx * sy / np.where(n > 0, n, np.nan)
        beta = np.where(var > 0, cov / var, np.nan)
    return beta, n


def _panels(context: DecisionContextV2) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Close and traded-value matrices for the eligible cross-section, oldest row first.

    Equivalent to ``toolkit.close_panel`` and ``toolkit.column_panel`` and far cheaper: the two of
    them together were most of a replay's wall clock at this decision rate.
    """
    names: list[str] = []
    stamps: list[np.ndarray] = []
    closes: list[np.ndarray] = []
    volumes: list[np.ndarray] = []
    for symbol in context.eligible_symbols:
        history = context.bars.get(symbol)
        if history is None or len(history) == 0:
            continue
        names.append(str(symbol))
        stamps.append(pd.DatetimeIndex(history["close_time"]).asi8)
        closes.append(history["close"].to_numpy(dtype=float))
        volumes.append(
            history["quote_volume"].to_numpy(dtype=float)
            if "quote_volume" in history
            else np.full(len(history), np.nan)
        )
    if not names:
        return [], np.empty((0, 0)), np.empty((0, 0))
    grid = np.unique(np.concatenate(stamps))
    close = np.full((len(grid), len(names)), np.nan)
    volume = np.full((len(grid), len(names)), np.nan)
    for column, (times, price, traded) in enumerate(zip(stamps, closes, volumes, strict=True)):
        position = np.searchsorted(grid, times)
        close[position, column] = price
        volume[position, column] = traded
    return names, close, volume


class Smoother:
    """Exponential blending, a no-trade band, and a one-sided fast exit.

    Not a dataclass: the evaluator execs a candidate into a module that is never registered in
    ``sys.modules``, and ``dataclasses`` resolves ``cls.__module__`` through that registry.
    """

    def __init__(self, decay: float, band: float, prune: float = 5e-4, gross: float = 1.0) -> None:
        self.decay = float(decay)
        self.band = float(band)
        self.prune = float(prune)
        self.gross = float(gross)
        self.current: dict[str, float] = {}
        self.emitted: dict[str, float] = {}

    def update(self, raw: Mapping[str, float], eligible: Sequence[str]) -> dict[str, float] | None:
        allowed = set(map(str, eligible))
        blended: dict[str, float] = {}
        for symbol in set(self.current) | set(raw):
            if symbol not in allowed:
                continue
            previous = float(self.current.get(symbol, 0.0))
            target = float(raw.get(symbol, 0.0))
            value = (1.0 - self.decay) * previous + self.decay * target
            if target * previous >= 0.0 and abs(target) < abs(previous):
                # Never delay getting smaller in a name. Blending is a cost control on the way in;
                # on the way out it is a risk amplifier, because the reason a target collapsed is
                # usually that the name's own risk just exploded. Removing this one line costs the
                # research window more than any other single change measured in this lane.
                value = target
            if abs(value) >= self.prune:
                blended[symbol] = value
        total = sum(abs(value) for value in blended.values())
        if total > self.gross > 0.0:
            blended = {s: v / total * self.gross for s, v in blended.items()}
        self.current = blended
        move = sum(
            abs(blended.get(s, 0.0) - self.emitted.get(s, 0.0))
            for s in set(blended) | set(self.emitted)
        )
        if self.emitted and move < self.band:
            # Below the band the book is already where it wants to be; not rebalancing is free.
            return None
        self.emitted = dict(blended)
        return dict(blended)


class ResidualCrossSectionalMomentum:
    """Long the strongest blended residual scores, short the weakest, beta-balanced."""

    # --- signal ---------------------------------------------------------------------------
    form_days = 90
    form_blend = 5
    form_spread = 1.6
    skip_days = 14
    skip_blend = 3
    skip_spread = 1.6
    beta_days = 90
    vol_days = 30
    liq_days = 30
    min_form_days = 45
    # --- distress -------------------------------------------------------------------------
    distress = 0.5
    distress_rel = 0.4
    distress_days = 14
    # --- book -----------------------------------------------------------------------------
    top_k = 10
    hold_k = 16
    symbol_cap = 0.15
    side_tilt_cap = 0.15
    smooth_decay = 0.20
    smooth_band = 0.06
    # --- guard ----------------------------------------------------------------------------
    guard_drawdown = 0.30
    guard_lookback_days = 120
    guard_rebound_days = 10

    def __init__(self) -> None:
        self._smoother: Smoother | None = None
        self._longs: set[str] = set()
        self._shorts: set[str] = set()

    def _tape(self) -> Smoother:
        if self._smoother is None:
            self._smoother = Smoother(float(self.smooth_decay), float(self.smooth_band))
        return self._smoother

    def target_weights(self, context: DecisionContextV2, *, seed: int) -> dict[str, float] | None:
        if not toolkit.is_daily_decision(context):
            return None
        columns, prices, traded_value = _panels(context)
        if len(columns) < MIN_NAMES or len(prices) < 3:
            return self._stand_down(context)
        simple = prices[1:] / prices[:-1] - 1.0
        simple = np.where(np.isfinite(simple), simple, np.nan)
        with np.errstate(invalid="ignore"):
            market = np.nanmean(simple, axis=1)
        if not np.isfinite(market).any():
            return self._stand_down(context)
        # The market factor is the eligible cross-section's own equal-weight book: no single name
        # is guaranteed to be a member, so the panel has to supply its own benchmark.
        level = np.cumprod(1.0 + np.nan_to_num(market, nan=0.0))

        if self._rebound_after_drawdown(level):
            return self._flatten()

        skip = toolkit.bars_for_days(self.skip_days)
        form = min(toolkit.bars_for_days(self.form_days), len(simple) - skip - 1)
        # A warm-up floor can never exceed the window it is gating, or the book would stand down
        # for ever and a permanently flat book scores zero rather than nothing.
        floor = min(
            toolkit.bars_for_days(self.min_form_days), toolkit.bars_for_days(self.form_days)
        )
        if form < floor:
            return self._stand_down(context)

        beta_bars = min(toolkit.bars_for_days(self.beta_days), len(simple))
        beta, pairs = _pairwise_beta(simple[-beta_bars:], market[-beta_bars:])

        end = len(prices) - 1 - skip
        start = end - form
        if start < 0:
            return self._stand_down(context)
        segment = np.log(prices[start + 1 : end + 1] / prices[start:end])
        traded = np.isfinite(segment).sum(axis=0)

        sigma = self._sigma(prices)
        liquidity = self._liquidity(traded_value)
        usable = (
            (traded >= form * COVERAGE)
            & (pairs >= max(30.0, beta_bars / 4.0))
            & np.isfinite(beta)
            & np.isfinite(sigma)
            & (sigma > 0.0)
            & np.isfinite(liquidity)
        )
        # The count that decides whether to trade at all is taken before the distress filter, so a
        # crowded distress list can thin the book but can never silently stand it down. Measured:
        # letting the filter trip the stand-down was worth nothing and cost the worst fold.
        if int(usable.sum()) < max(MIN_NAMES, 2 * int(self.top_k)):
            return self._stand_down(context)
        window = toolkit.bars_for_days(self.distress_days)
        usable = usable & (self._distress_severity(prices, level, beta, window) <= 1.0)
        if int(usable.sum()) < 4:
            return self._stand_down(context)

        names = np.asarray(columns, dtype=object)[usable]
        horizons = self._horizons(form, end)
        ends = self._ends(prices, skip)
        if not horizons or not ends:
            return self._stand_down(context)
        blended = np.zeros(int(usable.sum()), dtype=float)
        for stop in ends:
            for span in horizons:
                blended = blended + _rank_centred(
                    self._residual_over(prices, level, beta, stop, span, usable)
                )
        residual = blended / float(len(ends) * len(horizons))
        score = _neutralise(
            residual, [_rank_centred(beta[usable]), _rank_centred(liquidity[usable])]
        )

        signals = self._membership(names, score)
        if not signals:
            return self._stand_down(context)
        weights = self._book(
            signals,
            dict(zip(names, sigma[usable], strict=True)),
            dict(zip(names, beta[usable], strict=True)),
        )
        if not weights:
            return self._stand_down(context)
        return self._tape().update(weights, context.eligible_symbols)

    # --- signal construction ------------------------------------------------------------------

    def _horizons(self, form: int, end: int) -> list[int]:
        """Formation lengths to read the same residual over, longest first."""
        count = max(1, int(self.form_blend))
        if count == 1:
            return [form] if 3 <= form <= end else []
        spread = max(1.02, float(self.form_spread))
        offsets = np.linspace(-1.0, 1.0, count)
        spans = sorted({int(round(form * spread**offset)) for offset in offsets}, reverse=True)
        return [span for span in spans if 3 <= span <= end]

    def _ends(self, prices: np.ndarray, skip: int) -> list[int]:
        """Bar indices a formation window may finish on, one per skipped stretch."""
        last = len(prices) - 1
        count = max(1, int(self.skip_blend))
        if count == 1:
            return [last - skip] if last - skip > 3 else []
        spread = max(1.02, float(self.skip_spread))
        offsets = np.linspace(-1.0, 1.0, count)
        skips = sorted({max(1, int(round(skip * spread**offset))) for offset in offsets})
        return [last - value for value in skips if last - value > 3]

    def _residual_over(
        self,
        prices: np.ndarray,
        level: np.ndarray,
        beta: np.ndarray,
        end: int,
        span: int,
        usable: np.ndarray,
    ) -> np.ndarray:
        """Formation log return over one window with the beta-implied index move removed."""
        start = max(0, end - span)
        segment = np.log(prices[start + 1 : end + 1] / prices[start:end])
        formation = np.nansum(np.where(np.isfinite(segment), segment, np.nan), axis=0)
        leg = (
            float(np.log(level[end - 1] / level[start - 1]))
            if start >= 1
            else float(np.log(level[end - 1]))
        )
        residual = formation[usable] - beta[usable] * leg
        return np.where(np.isfinite(residual), residual, 0.0)

    def _distress_severity(
        self, prices: np.ndarray, level: np.ndarray, beta: np.ndarray, window: int
    ) -> np.ndarray:
        """How far into distress each name is, as a multiple of the declared limit.

        Two readings of the same idea, and the worse of them wins.  The absolute one asks whether
        the name has collapsed; the market-relative one asks whether the collapse was the name's
        own, because in a broad crash an absolute floor flags most of the cross-section and the
        survivors are then selected on exactly the dimension this lane trades.
        """
        width = prices.shape[1]
        if window <= 0 or len(prices) <= window:
            return np.zeros(width, dtype=float)
        severity = np.zeros(width, dtype=float)
        limit_abs = float(self.distress)
        limit_rel = float(self.distress_rel)
        if limit_abs > 0.0:
            fall = 1.0 - prices[-1] / prices[-1 - window]
            # A name whose recent price cannot be read is not a tradeable observation, so it takes
            # the maximum severity rather than the benefit of the doubt.
            severity = np.maximum(severity, np.where(np.isfinite(fall), fall, np.inf) / limit_abs)
        if limit_rel > 0.0:
            with np.errstate(divide="ignore", invalid="ignore"):
                own = np.log(prices[-1] / prices[-1 - window])
                index_leg = float(np.log(level[-1] / level[-1 - window]))
            shortfall = -(own - beta * index_leg)
            severity = np.maximum(
                severity, np.where(np.isfinite(shortfall), shortfall, np.inf) / limit_rel
            )
        return severity

    def _sigma(self, prices: np.ndarray) -> np.ndarray:
        """Per-bar realised volatility, the inverse of which sizes each name."""
        bars = max(3, min(toolkit.bars_for_days(self.vol_days), len(prices) - 1))
        block = np.log(prices[-bars:] / prices[-bars - 1 : -1])
        block = np.where(np.isfinite(block), block, np.nan)
        counts = np.isfinite(block).sum(axis=0)
        with np.errstate(invalid="ignore"):
            sigma = np.nanstd(block, axis=0, ddof=1)
        return np.where(counts >= max(3, bars // 4), sigma, np.nan)

    def _liquidity(self, traded_value: np.ndarray) -> np.ndarray:
        """Log median traded value over the trailing window: this universe's size factor."""
        window = traded_value[-toolkit.bars_for_days(self.liq_days) :]
        with np.errstate(invalid="ignore"):
            median = np.nanmedian(window, axis=0)
        value = np.log(np.maximum(median, 1.0))
        if not np.isfinite(value).any():
            return np.zeros(traded_value.shape[1])
        return np.where(np.isfinite(value), value, float(np.nanmedian(value[np.isfinite(value)])))

    # --- book construction --------------------------------------------------------------------

    def _membership(self, names: np.ndarray, score: np.ndarray) -> dict[str, float]:
        """Rank the cross-section and update the sticky long and short sets."""
        ranked = [
            str(name)
            for _, name in sorted(
                zip(-score, names.astype(str), strict=True), key=lambda pair: (pair[0], pair[1])
            )
        ]
        entry = max(1, min(int(self.top_k), len(ranked) // 2))
        # The hold band is derived at call time so it stays wider than the entry rank however
        # top_k is perturbed, and never so wide that the two bands could overlap -- an overlap
        # would let one name be held long and short at once.
        hold = max(entry, min(max(int(self.hold_k), entry + 3), len(ranked) // 2))
        self._longs = set(ranked[:entry]) | (self._longs & set(ranked[:hold]))
        self._shorts = set(ranked[-entry:]) | (self._shorts & set(ranked[-hold:]))
        signals = {symbol: 1.0 for symbol in sorted(self._longs)}
        signals.update({symbol: -1.0 for symbol in sorted(self._shorts)})
        return signals

    def _book(
        self, signals: dict[str, float], sigma: dict[str, float], beta: dict[str, float]
    ) -> dict[str, float]:
        """Inverse-volatility weights within each side, then balance the sides on beta."""
        sides: dict[float, dict[str, float]] = {1.0: {}, -1.0: {}}
        for symbol, direction in signals.items():
            scale = float(sigma.get(symbol, float("nan")))
            if not math.isfinite(scale) or scale <= 0.0:
                continue
            sides[1.0 if direction > 0.0 else -1.0][symbol] = 1.0 / scale
        if not sides[1.0] or not sides[-1.0]:
            return {}
        share: dict[float, dict[str, float]] = {}
        exposure: dict[float, float] = {}
        for side, raw in sides.items():
            total = sum(raw.values())
            if total <= 0.0:
                return {}
            share[side] = {s: v / total for s, v in raw.items()}
            exposure[side] = sum(w * float(beta.get(s, 1.0)) for s, w in share[side].items())
        long_gross = 0.5
        if exposure[1.0] > 0.0 and exposure[-1.0] > 0.0:
            # Equal dollars on two legs of unequal beta is not a neutral book. Balancing on
            # beta-weighted exposure instead is what keeps the bull and bear cells from mirroring
            # each other; the tilt it may take is capped so an extreme beta reading cannot run away
            # with the book.
            balanced = exposure[-1.0] / (exposure[1.0] + exposure[-1.0])
            tilt = float(self.side_tilt_cap)
            long_gross = min(0.5 + tilt, max(0.5 - tilt, balanced))
        weights = {s: long_gross * v for s, v in share[1.0].items()}
        weights.update({s: -(1.0 - long_gross) * v for s, v in share[-1.0].items()})
        return self._cap(weights)

    def _cap(self, weights: dict[str, float]) -> dict[str, float]:
        """Per-name ceiling within each side, redistributing what the ceiling refuses."""
        cap = float(self.symbol_cap)
        result: dict[str, float] = {}
        for sign in (1.0, -1.0):
            side = {s: abs(v) for s, v in weights.items() if v * sign > 0.0}
            if not side:
                continue
            available = sum(side.values())
            remaining = dict(side)
            while remaining and available > 1e-15:
                total = sum(remaining.values())
                if total <= 0.0:
                    break
                scaled = {s: v / total * available for s, v in remaining.items()}
                over = [s for s, v in scaled.items() if v > cap + 1e-15]
                if not over:
                    result.update({s: sign * v for s, v in scaled.items()})
                    break
                for symbol in over:
                    result[symbol] = sign * cap
                    del remaining[symbol]
                available -= cap * len(over)
        gross = sum(abs(v) for v in result.values())
        if gross > 1.0:
            result = {s: v / gross for s, v in result.items()}
        return {s: v for s, v in result.items() if math.isfinite(v) and v != 0.0}

    # --- hazard control -----------------------------------------------------------------------

    def _rebound_after_drawdown(self, level: np.ndarray) -> bool:
        """True when the index is deep below a recent high and has turned back up.

        Every bar in ``level`` closed before the decision, so the trigger is causal.  This is the
        momentum crash: the beaten-down names rebound hardest and the short side pays for it.
        """
        if float(self.guard_drawdown) >= 1.0:
            return False
        rebound = toolkit.bars_for_days(self.guard_rebound_days)
        if len(level) <= rebound + 2:
            return False
        window = level[-(toolkit.bars_for_days(self.guard_lookback_days) + 1) :]
        high = float(np.nanmax(window))
        last = float(level[-1])
        if not math.isfinite(high) or high <= 0.0 or not math.isfinite(last):
            return False
        drawdown = last / high - 1.0
        # Any non-negative turn counts. A threshold on the size of the bounce would be a second
        # guess at the same event, and the research window says it is a worse one.
        turn = last / float(level[-1 - rebound]) - 1.0
        return drawdown <= -float(self.guard_drawdown) and turn >= 0.0

    def _flatten(self) -> dict[str, float]:
        """Stand all the way down, and forget the book that was."""
        self._longs.clear()
        self._shorts.clear()
        tape = self._tape()
        tape.current = {}
        tape.emitted = {}
        return {}

    def _stand_down(self, context: DecisionContextV2) -> dict[str, float] | None:
        """No usable view: decay the book toward flat rather than hold a stale one."""
        self._longs.clear()
        self._shorts.clear()
        return self._tape().update({}, context.eligible_symbols)


def build_strategy() -> TargetStrategyV2:
    return ResidualCrossSectionalMomentum()
