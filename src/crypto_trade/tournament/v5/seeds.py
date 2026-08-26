"""The fifteen organizer seeds: each lane's idea in the least clever form that could work.

Every lane's **first charged trial is its unmodified seed**, and that serves three purposes at once.

It makes the fifteen seed scores a *measured distribution* against which every calibrated threshold
is placed, in an observed gap rather than at a round number somebody liked. Prior editions set
floors by inheritance and discovered afterwards that their full floor set admitted zero of
ninety-four measured trials.

It gives the leaderboard a **distance from seed**, so a team that ends up far from where it started
has to have learned something, and one that ships the seed with a parameter changed is visible as
such.

And it is an honest baseline for the mandate itself. If the naive form of a family already works,
that is worth knowing before a team spends twelve trials elaborating it -- in a prior edition the
naive seed was the only entry to clear its bar.

These are deliberately unsophisticated. They use one signal, rank it cross-sectionally, and take a
symmetric long/short book at a fixed gross. No fitting, no tuning, no volatility targeting -- the
organizer's ex-ante risk unit handles the last of those for every book equally, and a seed that
tuned anything would stop being a baseline and start being an opinion.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext

# Every seed takes the same symmetric book, so their scores differ by signal rather than by sizing.
SEED_GROSS = 0.60
SEED_SIDE_COUNT = 6
MINIMUM_HISTORY = 40

# The columns the seeds actually read, declared so a fixture can be checked against the real
# snapshot instead of against someone's memory of it.
#
# This exists because the alternative failed. The funding column is ``funding_rate``; an earlier
# revision read ``last_funding_rate`` -- the raw Binance name, not the tournament's canonical one --
# and two seeds silently produced no book at all. Nothing raised. The unit fixture used the same
# wrong name, so it passed, and only a run against the real snapshot showed two lanes scoring
# exactly zero across 808 days. A fixture that encodes the same assumption as the code cannot
# falsify it.
FUNDING_COLUMNS = ("symbol", "funding_rate")
BAR_COLUMNS = (
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_volume",
    "trade_count",
    "taker_buy_volume",
    "taker_buy_quote_volume",
)


class SeedError(RuntimeError):
    """A seed was asked for something the context cannot support."""


def _panel(context: DecisionContext, column: str, *, span: int) -> pd.DataFrame:
    """The last ``span`` rows of one column, one column per eligible symbol.

    Symbols without enough history are dropped rather than forward-filled: a seed that pads a short
    contract with repeated values is inventing the very placeholder bars this edition excludes.
    """

    series: dict[str, pd.Series] = {}
    for symbol in context.eligible_symbols:
        frame = context.bars.get(symbol)
        if frame is None or len(frame) < span:
            continue
        values = frame[column].to_numpy(dtype=float)[-span:]
        if not np.isfinite(values).all():
            continue
        series[symbol] = pd.Series(values)
    return pd.DataFrame(series)


def _long_short(scores: pd.Series, *, count: int = SEED_SIDE_COUNT) -> dict[str, float]:
    """Top ``count`` long, bottom ``count`` short, equal weight, gross fixed.

    Symmetric by construction. V4-R2 tried to guarantee two-sidedness by requiring the long leg to
    have *made money*, which is a performance test wearing a structure test's clothes and left 27 of
    94 trials structurally one-sided while nominally passing it.
    """

    usable = scores.dropna()
    if len(usable) < 2 * count:
        count = len(usable) // 2
    if count < 1:
        return {}
    ordered = usable.sort_values(ascending=False)
    longs, shorts = ordered.index[:count], ordered.index[-count:]
    per_name = SEED_GROSS / (2.0 * count)
    weights = {str(symbol): per_name for symbol in longs}
    weights.update({str(symbol): -per_name for symbol in shorts})
    return weights


def _returns(panel: pd.DataFrame) -> pd.DataFrame:
    return panel.pct_change().replace([np.inf, -np.inf], np.nan)


class _Seed:
    """Common shape. Subclasses supply ``score`` and their own ``span``; the book is shared.

    Deliberately **not** a dataclass. It was one, and the generated ``__init__`` assigned
    ``self.span = 60`` on every instance -- so each subclass's ``span`` override was silently
    ignored and all fifteen seeds ran at the same lookback. Nothing raised; the seeds simply
    stopped differing in the way their mandates require, and one of them then indexed past the end
    of a window it believed was longer. A plain class attribute is read from the subclass.
    """

    span: int = 60

    def score(self, context: DecisionContext) -> pd.Series:  # pragma: no cover - overridden
        raise NotImplementedError

    def target_weights(self, context: DecisionContext, *, seed: int) -> Mapping[str, float] | None:
        if len(context.eligible_symbols) < 4:
            return None
        try:
            scores = self.score(context)
        except (KeyError, ValueError):
            return None
        if scores is None or scores.dropna().empty:
            return None
        return _long_short(scores)


# -- risk-premium harvesting ---------------------------------------------------------------------


class FundingCarrySeed(_Seed):
    """team-01. Long the members paying you to hold them, short those you pay."""

    def score(self, context: DecisionContext) -> pd.Series:
        funding = context.funding
        if funding.empty or "funding_rate" not in funding.columns:
            return pd.Series(dtype=float)
        recent = funding[funding["symbol"].isin(context.eligible_symbols)]
        if recent.empty:
            return pd.Series(dtype=float)
        mean_rate = recent.groupby("symbol")["funding_rate"].mean()
        # Negative funding means shorts pay longs, so a long earns it: score is the negated rate.
        return -mean_rate


class FundingConvexitySeed(_Seed):
    """team-02. Funding dispersion against realized volatility."""

    def score(self, context: DecisionContext) -> pd.Series:
        closes = _panel(context, "close", span=self.span)
        if closes.empty:
            return pd.Series(dtype=float)
        volatility = _returns(closes).std()
        funding = context.funding
        if funding.empty:
            return pd.Series(dtype=float)
        recent = funding[funding["symbol"].isin(closes.columns)]
        dispersion = recent.groupby("symbol")["funding_rate"].std()
        aligned = dispersion.reindex(volatility.index)
        return -(aligned / volatility.replace(0.0, np.nan))


class DefensiveBetaSeed(_Seed):
    """team-03. Long low realized volatility, short high."""

    def score(self, context: DecisionContext) -> pd.Series:
        closes = _panel(context, "close", span=self.span)
        if closes.empty:
            return pd.Series(dtype=float)
        return -_returns(closes).std()


# -- cross-sectional mispricing --------------------------------------------------------------------


class ResidualMomentumSeed(_Seed):
    """team-04. Momentum on returns orthogonalised to the equal-weight member index."""

    span: int = 90

    def score(self, context: DecisionContext) -> pd.Series:
        closes = _panel(context, "close", span=self.span)
        if closes.shape[1] < 4:
            return pd.Series(dtype=float)
        returns = _returns(closes).dropna(how="all")
        market = returns.mean(axis=1)
        variance = float(market.var())
        if variance <= 0.0:
            return pd.Series(dtype=float)
        residual = {}
        for symbol in returns.columns:
            column = returns[symbol]
            paired = pd.concat([column, market], axis=1).dropna()
            if len(paired) < MINIMUM_HISTORY:
                continue
            beta = float(paired.cov().iloc[0, 1] / paired.iloc[:, 1].var())
            residual[symbol] = float((paired.iloc[:, 0] - beta * paired.iloc[:, 1]).sum())
        return pd.Series(residual, dtype=float)


class IlliquidityReversalSeed(_Seed):
    """team-05. Short-horizon reversal, weighted by how illiquid the name was."""

    span: int = 30

    def score(self, context: DecisionContext) -> pd.Series:
        closes = _panel(context, "close", span=self.span)
        volumes = _panel(context, "quote_volume", span=self.span)
        if closes.empty or volumes.empty:
            return pd.Series(dtype=float)
        recent = _returns(closes).tail(3).sum()
        # Amihud in spirit: absolute return per unit of traded value.
        illiquidity = (_returns(closes).abs().mean() / volumes.mean().replace(0.0, np.nan)).rank()
        return -recent * illiquidity.reindex(recent.index)


class ClusterRelativeValueSeed(_Seed):
    """team-06. Deviation from the mean of the names a symbol moves with."""

    span: int = 90

    def score(self, context: DecisionContext) -> pd.Series:
        closes = _panel(context, "close", span=self.span)
        if closes.shape[1] < 6:
            return pd.Series(dtype=float)
        returns = _returns(closes).dropna(how="all")
        correlation = returns.corr()
        recent = returns.tail(5).sum()
        scores = {}
        for symbol in returns.columns:
            neighbours = correlation[symbol].drop(symbol).nlargest(3).index
            if len(neighbours) < 3:
                continue
            scores[symbol] = float(recent[list(neighbours)].mean() - recent[symbol])
        return pd.Series(scores, dtype=float)


class CointegrationSeed(_Seed):
    """team-07. Spread against the most correlated partner, in units of its own deviation."""

    span: int = 120

    def score(self, context: DecisionContext) -> pd.Series:
        closes = _panel(context, "close", span=self.span)
        if closes.shape[1] < 4:
            return pd.Series(dtype=float)
        logs = np.log(closes.replace(0.0, np.nan)).dropna(how="all")
        correlation = logs.diff().corr()
        scores = {}
        for symbol in logs.columns:
            partner = correlation[symbol].drop(symbol).idxmax()
            spread = logs[symbol] - logs[partner]
            deviation = float(spread.std())
            if deviation <= 0.0 or not math.isfinite(deviation):
                continue
            scores[symbol] = -float((spread.iloc[-1] - spread.mean()) / deviation)
        return pd.Series(scores, dtype=float)


# -- time-series trend -----------------------------------------------------------------------------


class TimeseriesMomentumSeed(_Seed):
    """team-08. Average sign of return over several lookbacks."""

    span: int = 120

    def score(self, context: DecisionContext) -> pd.Series:
        closes = _panel(context, "close", span=self.span)
        if closes.empty:
            return pd.Series(dtype=float)
        signals = [np.sign(closes.iloc[-1] / closes.iloc[-window] - 1.0) for window in (15, 45, 90)]
        return sum(signals) / float(len(signals))


class VolumeBreakoutSeed(_Seed):
    """team-09. Channel position, gated on above-average participation."""

    span: int = 60

    def score(self, context: DecisionContext) -> pd.Series:
        highs = _panel(context, "high", span=self.span)
        lows = _panel(context, "low", span=self.span)
        closes = _panel(context, "close", span=self.span)
        volumes = _panel(context, "quote_volume", span=self.span)
        if closes.empty or highs.empty or lows.empty or volumes.empty:
            return pd.Series(dtype=float)
        span = (highs.max() - lows.min()).replace(0.0, np.nan)
        position = (closes.iloc[-1] - lows.min()) / span
        confirmed = volumes.tail(5).mean() > volumes.mean()
        return (position - 0.5).where(confirmed, 0.0)


# -- microstructure and participation ----------------------------------------------------------


class TakerFlowSeed(_Seed):
    """team-10. Aggressor imbalance. The only lane permitted this as a primary signal."""

    span: int = 30

    def score(self, context: DecisionContext) -> pd.Series:
        taker = _panel(context, "taker_buy_quote_volume", span=self.span)
        total = _panel(context, "quote_volume", span=self.span)
        if taker.empty or total.empty:
            return pd.Series(dtype=float)
        share = (taker / total.replace(0.0, np.nan)).tail(10).mean()
        return share - 0.5


class ParticipantMixSeed(_Seed):
    """team-11. Average trade size as a retail-versus-institutional proxy."""

    span: int = 60

    def score(self, context: DecisionContext) -> pd.Series:
        volumes = _panel(context, "quote_volume", span=self.span)
        counts = _panel(context, "trade_count", span=self.span)
        if volumes.empty or counts.empty:
            return pd.Series(dtype=float)
        size = volumes / counts.replace(0.0, np.nan)
        recent, baseline = size.tail(10).mean(), size.mean()
        return (recent / baseline.replace(0.0, np.nan)) - 1.0


# -- event and state -------------------------------------------------------------------------------


class VolumeShockSeed(_Seed):
    """team-12. Extreme quote-volume z-score as an event; fade the move that came with it."""

    span: int = 60

    def score(self, context: DecisionContext) -> pd.Series:
        volumes = _panel(context, "quote_volume", span=self.span)
        closes = _panel(context, "close", span=self.span)
        if volumes.empty or closes.empty:
            return pd.Series(dtype=float)
        deviation = volumes.std().replace(0.0, np.nan)
        shock = (volumes.iloc[-1] - volumes.mean()) / deviation
        move = _returns(closes).iloc[-1]
        return -move.where(shock > 2.0, 0.0)


class InclusionAttentionSeed(_Seed):
    """team-13. Trade the members that most recently became tradable.

    Newness is proxied by how much history the snapshot holds for a symbol, which is what a weekly
    entrant actually looks like from inside a decision context.
    """

    span: int = 30

    def score(self, context: DecisionContext) -> pd.Series:
        lengths = {}
        for symbol in context.eligible_symbols:
            frame = context.bars.get(symbol)
            if frame is None or frame.empty:
                continue
            lengths[symbol] = float(len(frame))
        if not lengths:
            return pd.Series(dtype=float)
        # Shorter history ranks higher: the seed goes long the newest members.
        return -pd.Series(lengths, dtype=float)


class BreadthStateSeed(_Seed):
    """team-14. Directional by mandate: net exposure timed from cross-sectional breadth."""

    span: int = 60

    def score(self, context: DecisionContext) -> pd.Series:
        closes = _panel(context, "close", span=self.span)
        if closes.empty:
            return pd.Series(dtype=float)
        return _returns(closes).tail(20).sum()

    def target_weights(self, context: DecisionContext, *, seed: int) -> Mapping[str, float] | None:
        """Overridden to carry net exposure, which the shared symmetric book cannot.

        The mandate requires it: a field of fifteen market-neutral books can say nothing about
        market state, so this lane tilts with breadth inside the |net| <= 0.25 cap.
        """

        # Repeated from the base rather than inherited, because overriding target_weights skips it
        # -- which is exactly how this seed traded a two-name cross-section in an earlier revision.
        if len(context.eligible_symbols) < 4:
            return None
        scores = self.score(context)
        if scores.dropna().empty:
            return None
        book = dict(_long_short(scores))
        if not book:
            return None
        breadth = float((scores > 0).mean()) - 0.5
        tilt = max(-0.20, min(0.20, breadth * 0.40)) / max(len(book), 1)
        return {symbol: weight + tilt for symbol, weight in book.items()}


# -- combination --------------------------------------------------------------------------------


class RegimeEnsembleSeed(_Seed):
    """team-15. Trend when the cross-section is dispersed, reversal when it is compressed."""

    span: int = 90

    def score(self, context: DecisionContext) -> pd.Series:
        closes = _panel(context, "close", span=self.span)
        if closes.empty:
            return pd.Series(dtype=float)
        returns = _returns(closes)
        dispersion = float(returns.tail(20).std().mean())
        baseline = float(returns.std().mean())
        trend = closes.iloc[-1] / closes.iloc[-45] - 1.0
        reversal = -returns.tail(3).sum()
        return trend if dispersion >= baseline else reversal


_FACTORIES: Mapping[str, type[_Seed]] = {
    "funding_carry": FundingCarrySeed,
    "funding_convexity": FundingConvexitySeed,
    "defensive_beta": DefensiveBetaSeed,
    "residual_momentum": ResidualMomentumSeed,
    "illiquidity_reversal": IlliquidityReversalSeed,
    "cluster_relative_value": ClusterRelativeValueSeed,
    "cointegration": CointegrationSeed,
    "timeseries_momentum": TimeseriesMomentumSeed,
    "volume_breakout": VolumeBreakoutSeed,
    "taker_flow": TakerFlowSeed,
    "participant_mix": ParticipantMixSeed,
    "volume_shock": VolumeShockSeed,
    "inclusion_attention": InclusionAttentionSeed,
    "breadth_state": BreadthStateSeed,
    "regime_ensemble": RegimeEnsembleSeed,
}


def build_seed(name: str) -> _Seed:
    """Instantiate one organizer seed by the name its lane declares."""

    if name not in _FACTORIES:
        raise SeedError(f"unknown organizer seed: {name}")
    return _FACTORIES[name]()


def seed_names() -> tuple[str, ...]:
    return tuple(sorted(_FACTORIES))


def assert_every_lane_has_a_seed(lane_seeds: Sequence[str]) -> None:
    """Every lane's declared seed must exist, and no seed may be orphaned.

    Both directions. A lane naming a seed that was never written fails at scaffolding rather than
    on its first charged trial; a seed no lane claims is dead code that a reader would mistake for
    part of the field.
    """

    declared, available = set(lane_seeds), set(_FACTORIES)
    missing = sorted(declared - available)
    if missing:
        raise SeedError(f"lanes declare seeds that do not exist: {missing}")
    orphaned = sorted(available - declared)
    if orphaned:
        raise SeedError(f"seeds exist that no lane claims: {orphaned}")


__all__ = [
    "MINIMUM_HISTORY",
    "SEED_GROSS",
    "SEED_SIDE_COUNT",
    "BAR_COLUMNS",
    "FUNDING_COLUMNS",
    "SeedError",
    "assert_every_lane_has_a_seed",
    "build_seed",
    "seed_names",
]
