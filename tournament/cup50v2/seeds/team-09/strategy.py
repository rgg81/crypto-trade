"""Cluster-relative reversal: fade a name against its own correlated peers, not the market.

One-week reversal is real in altcoins, but most of any name's weekly move is its sector and the
market riding through it, so fading the raw move is mostly a short-horizon bet against beta. This
lane re-derives peer clusters periodically from a trailing correlation matrix, z-scores the recent
return inside each cluster only, and fades what is left over -- the idiosyncratic dislocation, which
is the part with a reason to revert. A cluster too small to describe a peer group is simply skipped.
"""

from __future__ import annotations

import pandas as pd

from crypto_trade.cup50v2 import toolkit
from crypto_trade.cup50v2.protocol import DecisionContextV2, TargetStrategyV2


class ClusterRelativeReversal:
    """Fade the within-cluster component of a short-horizon move."""

    clusters = 6
    rev_days = 5
    z_min = 1.0
    top_k = 10

    # Held out of the declared neighbourhood: the correlation window and the recluster cadence
    # change which names are peers, which re-partitions the universe rather than moving the
    # mechanism along a single axis.
    cluster_days = 90
    recluster_days = 30
    # Three is the smallest group where a z-score describes a member against peers rather than
    # against one other name.
    min_cluster = 3

    def __init__(self) -> None:
        # Fast lane: a 5-day signal turns over quickly, so blend harder than a trend book would and
        # keep a wide band so the daily reshuffling of near-threshold names is not paid for.
        self._smoother = toolkit.TargetSmoother(decay=0.35, band=0.10)
        self._labels: dict[str, int] | None = None
        self._clustered_on: pd.Timestamp | None = None

    def _recluster(self, panel: pd.DataFrame, seed: int) -> dict[str, int] | None:
        """Partition the cross-section by correlation, or None when it cannot be done honestly."""
        window = toolkit.bars_for_days(self.cluster_days)
        # Drop the leading NaN row of the return panel before trimming, so a short history costs
        # bars rather than every column.
        returns = toolkit.bar_returns(panel).iloc[1:].tail(window)
        if len(returns) < window // 2:
            return None
        full = returns.dropna(axis=1, how="any")
        if full.shape[1] < self.min_cluster:
            return None
        matrix = full.corr()
        # A name with no variation over the window correlates with nothing; its row is all NaN and
        # would otherwise poison every distance k-means computes.
        usable = [str(name) for name in matrix.columns if bool(matrix[name].notna().all())]
        if len(usable) < self.min_cluster:
            return None
        matrix = matrix.loc[usable, usable]
        labels = toolkit.kmeans_labels(matrix.to_numpy(), int(self.clusters), seed=seed)
        return {name: int(label) for name, label in zip(usable, labels, strict=True)}

    def target_weights(self, context: DecisionContextV2, *, seed: int) -> dict[str, float] | None:
        if not toolkit.is_daily_decision(context):
            return None
        panel = toolkit.close_panel(context)
        if panel.empty:
            return None

        today = pd.Timestamp(context.decision_time).normalize()
        stale = self._clustered_on is None or (today - self._clustered_on).days >= (
            self.recluster_days
        )
        if self._labels is None or stale:
            fresh = self._recluster(panel, seed)
            if fresh is not None:
                # Keep the previous partition when a refresh is not possible; a book with stale
                # peers is far better behaved than one with no peer structure at all.
                self._labels = fresh
                self._clustered_on = today
        if not self._labels:
            return None

        move = toolkit.trailing_return(panel, toolkit.bars_for_days(self.rev_days))
        if move.empty:
            return None

        signals: dict[str, float] = {}
        for group in sorted(set(self._labels.values())):
            members = [str(name) for name in move.index if self._labels.get(str(name)) == group]
            if len(members) < self.min_cluster:
                continue
            # The z-score is taken inside the cluster only: that is the whole mechanism, since a
            # universe-wide z would mostly re-measure which sector moved.
            for name, score in toolkit.cross_sectional_z(move.loc[members]).items():
                if abs(float(score)) > self.z_min:
                    signals[str(name)] = -float(score)

        series = pd.Series(signals, dtype=float)
        picks: dict[str, float] = {}
        if not series.empty:
            # Cap each side independently, so a day where one cluster tail dominates does not
            # deliver a directional book through the back door.
            for side in (series[series > 0.0], series[series < 0.0]):
                picks.update(toolkit.top_by_absolute(side, int(self.top_k)).to_dict())

        weights = toolkit.vol_parity(
            picks,
            toolkit.realised_sigma(panel),
            symbol_cap=0.15,
            neutral=True,
        )
        return self._smoother.update(weights, context.eligible_symbols)


def build_strategy() -> TargetStrategyV2:
    return ClusterRelativeReversal()
