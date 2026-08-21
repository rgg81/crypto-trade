"""Cluster-relative reversal: fade the idiosyncratic part of a move, only when volume agrees.

A name's weekly move is mostly its market and its peer group riding through it, and both of those
are momentum-bearing at this horizon: fading the raw move is a short-horizon bet against trend and
loses badly whenever the cross-section trends. The lane's claim is that the part worth fading is
what is left after the peer group is removed, so the cross-section is partitioned by trailing
return correlation and the dislocation is measured only inside a partition.

Three things were added to the seed, each because a measurement demanded it.

* **Volume confirmation.** A name that moved on ordinary volume was pushed; a name that moved on a
  multiple of its own normal volume is being repriced, and repricing continues. Down-weighting the
  second group by how abnormal its volume was is what turns the bull-market cell from a large loss
  into a small gain: it is the single largest change here.
* **Beta neutralisation.** Measured on the seed, the book was short beta in up months and long beta
  in down months -- the recent winners it shorted were the high-beta names and the recent losers it
  bought were too -- so it was structurally positioned against whichever way the market was going.
  A dollar-neutral book is not a market-neutral one. The trailing beta to an equal-weight index of
  the eligible cross-section is projected out of the weights.
* **A position, not a signal.** The dislocation is turned into membership with hysteresis and each
  member is held at its own risk rather than in proportion to its score, because a weight that
  tracks a noisy score pays the spread for re-expressing a view it already holds. Cost, not signal
  absence, is what this lane runs into.

Every state kept here -- the partition, the membership set, the blended book -- is rebuilt from the
streamed past alone.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from crypto_trade.cup50v2 import toolkit
from crypto_trade.cup50v2.protocol import DecisionContextV2, TargetStrategyV2


def _capped(weights: dict[str, float], *, symbol_cap: float, gross: float) -> dict[str, float]:
    """Per-name ceiling with the freed budget refilled, so the book keeps the size it asked for."""
    result: dict[str, float] = {}
    for sign in (1.0, -1.0):
        side = {name: value for name, value in weights.items() if math.copysign(1.0, value) == sign}
        side = {name: value for name, value in side.items() if value != 0.0}
        if not side:
            continue
        budget = sum(abs(value) for value in side.values())
        remaining = {name: abs(value) for name, value in side.items()}
        available = budget
        while remaining and available > 1e-15:
            total = sum(remaining.values())
            if total <= 0.0:
                break
            scaled = {name: value / total * available for name, value in remaining.items()}
            over = [name for name, value in scaled.items() if value > symbol_cap + 1e-15]
            if not over:
                result.update({name: sign * value for name, value in scaled.items()})
                available = 0.0
                break
            for name in over:
                result[name] = sign * symbol_cap
                del remaining[name]
            available -= symbol_cap * len(over)
    total = sum(abs(value) for value in result.values())
    if total > gross > 0.0:
        result = {name: value / total * gross for name, value in result.items()}
    return {name: value for name, value in result.items() if math.isfinite(value) and value != 0.0}


class ClusterRelativeReversal:
    """Fade the within-cluster component of a short-horizon move, volume-confirmed."""

    # --- declared neighbourhood ------------------------------------------------------------
    rev_days = 10
    z_enter = 0.52
    vol_confirm = 2.0
    blend = 0.65

    # --- held out of the declared neighbourhood --------------------------------------------
    # The correlation window and the recluster cadence decide which names are peers at all, so
    # moving them re-partitions the universe rather than moving the mechanism along one axis.
    clusters = 5
    cluster_days = 90
    recluster_days = 30
    # Three is the smallest group in which a z-score describes a member against peers rather than
    # against one other name.
    min_cluster = 3
    # A partition needs some history, but demanding the full window would leave the book flat for a
    # quarter at the start of any replay, and an absent book scores zero rather than small.
    min_cluster_history = 45
    # Hysteresis: a name is admitted on a clear dislocation and kept until it has largely closed.
    # Tying the exit to the entry keeps the band meaningful wherever the entry is probed.
    exit_fraction = 0.34
    beta_days = 60
    volume_base_days = 60
    symbol_cap = 0.15
    max_net = 0.30
    trade_band = 0.15

    def __init__(self) -> None:
        self._smoother = toolkit.TargetSmoother(
            decay=float(self.blend), band=float(self.trade_band)
        )
        self._labels: dict[str, int] | None = None
        self._clustered_on: pd.Timestamp | None = None
        self._held: set[str] = set()
        self._blend_set = False

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _daily(panel: pd.DataFrame) -> pd.DataFrame:
        """Closes at the daily boundary only: the 8h grid's last bar of each UTC day."""
        if panel.empty:
            return panel
        hours = pd.DatetimeIndex(panel.index).hour
        return panel.loc[hours == 23]

    def _recluster(self, daily: pd.DataFrame, seed: int) -> dict[str, int] | None:
        """Partition the cross-section by correlation, or None when it cannot be done honestly."""
        returns = daily.pct_change().replace([np.inf, -np.inf], np.nan).iloc[1:]
        window = min(int(self.cluster_days), len(returns))
        if window < int(self.min_cluster_history):
            return None
        returns = returns.tail(window)
        full = returns.dropna(axis=1, how="any")
        if full.shape[1] < int(self.min_cluster):
            return None
        matrix = full.corr()
        # A name with no variation over the window correlates with nothing; its row is all NaN and
        # would otherwise poison every distance k-means computes.
        usable = [str(name) for name in matrix.columns if bool(matrix[name].notna().all())]
        if len(usable) < int(self.min_cluster):
            return None
        matrix = matrix.loc[usable, usable]
        labels = toolkit.kmeans_labels(matrix.to_numpy(), int(self.clusters), seed=seed)
        return {name: int(label) for name, label in zip(usable, labels, strict=True)}

    def _relative_volume(self, context: DecisionContextV2, names: list[str]) -> pd.Series:
        """Traded value over the formation window against the name's own normal daily level.

        Aggregated to whole days first: the 8h grid has a pronounced time-of-day pattern, and a
        ratio of a mean to a median taken across bars would measure that pattern as well as the
        thing it is meant to measure.
        """
        volume = toolkit.column_panel(context, "quote_volume", symbols=names)
        if volume.empty:
            return pd.Series(dtype=float)
        daily = volume.groupby(pd.DatetimeIndex(volume.index).normalize()).sum(min_count=1)
        recent = daily.tail(int(self.rev_days)).mean(skipna=True)
        base = daily.tail(int(self.volume_base_days)).median(skipna=True)
        ratio = recent / base.where(base > 0.0)
        return ratio.replace([np.inf, -np.inf], np.nan).dropna()

    def _betas(self, daily: pd.DataFrame) -> pd.Series:
        """Trailing beta of each name to an equal-weight index of the eligible cross-section."""
        returns = daily.pct_change().replace([np.inf, -np.inf], np.nan).iloc[1:]
        window = min(int(self.beta_days), len(returns))
        if window < 20:
            return pd.Series(dtype=float)
        returns = returns.tail(window)
        market = returns.mean(axis=1, skipna=True)
        variance = float(market.var(ddof=1))
        if not math.isfinite(variance) or variance <= 0.0:
            return pd.Series(dtype=float)
        counts = returns.notna().sum()
        betas = returns.apply(lambda column: column.cov(market) / variance)
        return betas.where(counts >= window // 2).replace([np.inf, -np.inf], np.nan).dropna()

    def _neutralise(self, weights: dict[str, float], betas: pd.Series) -> dict[str, float]:
        """Project the book's market exposure out of it, then restore gross and the name ceiling."""
        shared = [name for name in weights if name in betas.index]
        if len(shared) < 2:
            return weights
        loadings = np.array([float(betas[name]) for name in shared], dtype=float)
        held = np.array([float(weights[name]) for name in shared], dtype=float)
        denominator = float(loadings @ loadings)
        if not math.isfinite(denominator) or denominator <= 0.0:
            return weights
        adjusted = held - (float(held @ loadings) / denominator) * loadings
        result = dict(weights)
        for name, value in zip(shared, adjusted, strict=True):
            result[name] = float(value)
        net = sum(result.values())
        # A beta-neutral book need not be dollar-neutral, but it should not become a directional
        # position by the back door: the tilt is capped and any excess is scaled away pro rata.
        if abs(net) > self.max_net:
            magnitude = sum(abs(value) for value in result.values())
            if magnitude > 0.0:
                excess = (abs(net) - self.max_net) * math.copysign(1.0, net)
                result = {
                    name: value - excess * abs(value) / magnitude for name, value in result.items()
                }
        return _capped(result, symbol_cap=float(self.symbol_cap), gross=1.0)

    # ------------------------------------------------------------------ interface
    def target_weights(self, context: DecisionContextV2, *, seed: int) -> dict[str, float] | None:
        if not toolkit.is_daily_decision(context):
            return None
        if not self._blend_set:
            self._smoother.decay = float(self.blend)
            self._smoother.band = float(self.trade_band)
            self._blend_set = True
        panel = toolkit.close_panel(context)
        if panel.empty:
            return None
        daily = self._daily(panel)
        if daily.empty or len(daily) <= int(self.rev_days) + 1:
            return None

        today = pd.Timestamp(context.decision_time).normalize()
        stale = self._clustered_on is None or (today - self._clustered_on).days >= int(
            self.recluster_days
        )
        if self._labels is None or stale:
            fresh = self._recluster(daily, seed)
            if fresh is not None:
                # Keep the previous partition when a refresh is not possible; a book with stale
                # peers is far better behaved than one with no peer structure at all.
                self._labels = fresh
                self._clustered_on = today
        if not self._labels:
            return None

        sigma = toolkit.realised_sigma(panel)
        move = (daily.iloc[-1] / daily.iloc[-1 - int(self.rev_days)] - 1.0).replace(
            [np.inf, -np.inf], np.nan
        )
        # The dislocation is measured in units of the name's own risk. Fading raw percentage moves
        # is mostly a bet that the most volatile names in a cluster mean-revert, which is a
        # different claim from the one this lane makes.
        move = (move / sigma.reindex(move.index).where(sigma > 0.0)).dropna()
        if move.empty:
            return None

        scores: dict[str, float] = {}
        for group in sorted(set(self._labels.values())):
            members = [str(name) for name in move.index if self._labels.get(str(name)) == group]
            if len(members) < int(self.min_cluster):
                continue
            # The z-score is taken inside the cluster only: that is the whole mechanism, since a
            # universe-wide z would mostly re-measure which sector moved.
            for name, score in toolkit.cross_sectional_z(move.loc[members]).items():
                scores[str(name)] = -float(score)

        enter = float(self.z_enter)
        leave = enter * float(self.exit_fraction)
        eligible = set(map(str, context.eligible_symbols))
        members: dict[str, float] = {}
        for name, score in scores.items():
            if name not in eligible:
                continue
            magnitude = abs(score)
            if magnitude >= enter or (name in self._held and magnitude >= leave):
                members[name] = math.copysign(1.0, score)
        self._held = set(members)

        if members:
            ratio = self._relative_volume(context, sorted(members))
            confirmed: dict[str, float] = {}
            limit = float(self.vol_confirm)
            for name, direction in members.items():
                value = float(ratio.get(name, float("nan")))
                # Three states, not a continuous multiplier. An ordinary-volume mover was pushed
                # and is faded in full; one trading at a multiple of its own normal turnover is
                # being repriced and is dropped. Quantising matters as much as the rule itself: a
                # multiplier that moves a little every day retrades the whole book for nothing,
                # and this lane's binding constraint is what it pays to trade, not what it knows.
                if not math.isfinite(value) or value <= limit:
                    damp = 1.0
                elif value <= 2.0 * limit:
                    damp = 0.5
                else:
                    damp = 0.0
                if damp > 0.0:
                    confirmed[name] = direction * damp
            members = confirmed

        weights = toolkit.vol_parity(
            members,
            sigma,
            symbol_cap=float(self.symbol_cap),
            neutral=True,
        )
        if weights:
            weights = self._neutralise(weights, self._betas(daily))
        return self._smoother.update(weights, context.eligible_symbols)


def build_strategy() -> TargetStrategyV2:
    return ClusterRelativeReversal()
