"""Team 06 HORIZON CHECK -- the nominee at a fortnightly rather than a weekly cadence.

MECHANISM
---------
In a 24/7 venue where retail can lever 50x and every position is marked continuously, the left tail
of a coin's return distribution is not an act of god: it is manufactured by the positioning that
also makes the coin expensive. Crowded leveraged length is liquidated *into* a falling book, so
deleveraging is one-sided and reflexive -- the down move triggers the liquidations that extend the
down move. A coin that has been repeatedly forced through that channel is carrying, at any moment,
more of the marginal leveraged buyer than a coin whose two-sided churn is the same width. That is
the thing this book selects on: not "how wide is this coin's distribution" but "how much of that
width is the deleveraging channel, and how long does it take to climb back out".

Four characteristics, one per facet of downside risk, equally weighted because there is no honest
basis for weighting them differently:

    cvar_5        left-tail depth        mean of the worst 5% of 8h log returns
    semideviation semivariance          root mean square of the below-mean returns
    max_drawdown  drawdown depth        deepest peak-to-trough on the window's close path
    underwater    recovery time         fraction of the window spent below its running maximum

Each is cross-sectionally z-scored inside the point-in-time top-20 at the decision and summed. The
book is long the SELECTION_COUNT names with the lowest composite and short the SELECTION_COUNT
highest -- a cross-sectional risk sort, with no view on any coin's expected return anywhere in it.

The one control is a leg-weight tilt: the two sleeves' dollar sizes are set so that their trailing
market betas offset, rather than their dollar amounts. Selecting on risk necessarily produces two
sleeves of unequal beta, and without the tilt the book is a short-beta bet wearing a cross-sectional
costume. The tilt is a control, is declared as one, and its ablation is in the certificate.

WHAT WOULD FALSIFY IT: if the trailing composite carried no forecast of the *forward* realised
downside character, the book would be paid for a stale label rather than for a risk. Measured on the
in-sample window at these parameters: trailing composite vs next-21-bar realised composite, rank
correlation 0.52 (t 32.6), positive in all four folds.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np

from crypto_trade.tournament.protocol import DecisionContext

# ---------------------------------------------------------------------------------------------
# Declared neighbourhood coordinates. Module level, one value each, plain literals.
# ---------------------------------------------------------------------------------------------

FORMATION_BARS = 252
"""8h bars of history the downside-risk characteristics are measured over (84 days)."""

SELECTION_COUNT = 6
"""Names per sleeve. Roughly a third of a 20-name universe on each side."""

REBALANCE_PHASE = 2
"""Offset of the weekly rebalance on the absolute 8h clock, in bars.

Phase is a first-order axis for any cadence longer than one bar, not a detail: a cadence-21 result
measured at a single offset is a result about that offset. It is declared as a swept coordinate so
the scored median is a phase-agnostic estimate rather than a phase-lucky one.
"""

# ---------------------------------------------------------------------------------------------
# Fixed structure. Not swept, and not a free parameter of the mechanism.
# ---------------------------------------------------------------------------------------------

REBALANCE_BARS = 42
"""Fortnightly cadence on the 8h grid."""

TAIL_FRACTION = 0.05
"""The left tail CVaR averages over: the worst 5% of the window's returns."""

BETA_LEG_FLOOR = 0.20
"""Smallest share of gross the long sleeve may take under the beta tilt."""

BETA_LEG_CAP = 0.80
"""Largest share of gross the long sleeve may take under the beta tilt."""

MINIMUM_NAMES = 12
"""Below this many scoreable members the cross-section is too thin to sort into sleeves."""

_BAR_NANOSECONDS = 8 * 3600 * 1_000_000_000


def _zscore(values: np.ndarray) -> np.ndarray:
    spread = float(values.std())
    if not math.isfinite(spread) or spread <= 1e-12:
        return np.zeros_like(values)
    return (values - float(values.mean())) / spread


class DownsideRiskTercile:
    """Long the lowest-downside-risk third of the point-in-time top-20, short the highest."""

    def target_weights(
        self, context: DecisionContext, *, seed: int
    ) -> Mapping[str, float] | None:
        del seed  # the book is deterministic; nothing here is sampled

        bar_index = int(context.decision_time.value // _BAR_NANOSECONDS)
        if (bar_index - REBALANCE_PHASE) % REBALANCE_BARS != 0:
            return None

        names: list[str] = []
        returns: list[np.ndarray] = []
        closes: list[np.ndarray] = []
        for symbol in context.eligible_symbols:
            frame = context.bars.get(symbol)
            if frame is None or len(frame) < FORMATION_BARS + 1:
                continue
            path = np.asarray(frame["close"].to_numpy()[-(FORMATION_BARS + 1) :], dtype=float)
            if not np.isfinite(path).all() or (path <= 0.0).any():
                continue
            logs = np.log(path)
            names.append(symbol)
            closes.append(logs)
            returns.append(np.diff(logs))

        if len(names) < max(MINIMUM_NAMES, 2 * SELECTION_COUNT):
            return None

        matrix = np.vstack(returns)
        paths = np.vstack(closes)

        # --- the four downside-risk characteristics -------------------------------------------
        deviations = matrix - matrix.mean(axis=1, keepdims=True)
        below = np.minimum(deviations, 0.0)
        semideviation = np.sqrt((below**2).mean(axis=1))

        tail = max(1, int(round(TAIL_FRACTION * matrix.shape[1])))
        worst = np.sort(matrix, axis=1)[:, :tail]
        cvar = -worst.mean(axis=1)

        running_max = np.maximum.accumulate(paths, axis=1)
        drawdown = running_max - paths
        max_drawdown = drawdown.max(axis=1)
        underwater = (drawdown[:, 1:] > 1e-12).mean(axis=1)

        score = (
            _zscore(cvar)
            + _zscore(semideviation)
            + _zscore(max_drawdown)
            + _zscore(underwater)
        )
        if not np.isfinite(score).all():
            return None

        order = np.argsort(score, kind="stable")
        long_rows = order[:SELECTION_COUNT]
        short_rows = order[-SELECTION_COUNT:]

        # --- the control: size the sleeves so their trailing market betas offset ---------------
        market = matrix.mean(axis=0)
        variance = float(market.var())
        long_share = 0.5
        if variance > 1e-18:
            centred = market - float(market.mean())
            betas = (matrix - matrix.mean(axis=1, keepdims=True)) @ centred / (
                variance * matrix.shape[1]
            )
            long_beta = float(betas[long_rows].mean())
            short_beta = float(betas[short_rows].mean())
            total = long_beta + short_beta
            if math.isfinite(total) and total > 1e-6:
                long_share = min(max(short_beta / total, BETA_LEG_FLOOR), BETA_LEG_CAP)

        weights: dict[str, float] = {}
        for row in long_rows:
            weights[names[row]] = long_share / SELECTION_COUNT
        for row in short_rows:
            weights[names[row]] = -(1.0 - long_share) / SELECTION_COUNT
        return weights


def build_strategy() -> DownsideRiskTercile:
    return DownsideRiskTercile()


__all__: Sequence[str] = ("build_strategy", "DownsideRiskTercile")
