"""Equal-risk ensemble of the three eligible finalists.

Why this desk exists. Across six editions the one reliable finding is that in-sample rank carries
almost no information about out-of-sample rank at the top, and CUP-20 measured a rank correlation
of -1 between its top three and their forward record. Picking one winner and deploying it is a bet
on a ranking the evidence says is noise. So the final stage runs four desks: the winner, both
runners-up, and this one, and the pre-registered capital rule reads the forward record rather than
the leaderboard.

What it is. An ordinary TargetStrategyV2 over one more frozen source bundle, not a special case in
the tick. It instantiates the three finalists from their own frozen bundles at their own frozen
centres, sizes each one's intended book to the common volatility target *before* averaging, and
emits the mean. Equalising first is the whole point: averaging raw books would silently weight the
ensemble toward whichever finalist happens to run the largest gross, which is the opposite of
equal-risk.

The evaluator then applies the common risk pass and the caps to the averaged book exactly as it
does for any team, so this desk is sized and constrained on identical terms to the other three.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.cup50v2 import toolkit
from crypto_trade.cup50v2.common_risk import BARS_PER_YEAR, _ewma_covariance
from crypto_trade.cup50v2.protocol import DecisionContextV2
from crypto_trade.cup50v2.replay import (
    apply_strategy_parameters,
    load_strategy_module,
    strategy_from_module,
)

# The evaluator's own risk-unit constants, read from the same config the tournament froze rather
# than restated here. A second copy of a number is a second thing to drift (amendment A2).
_MANIFEST = Path(__file__).resolve().parent / "finalists.json"


class EqualRiskEnsemble:
    """Average three finalists after sizing each to the common volatility target."""

    def __init__(self, finalists: list[Mapping[str, object]], policy: Mapping[str, float]) -> None:
        self._policy = dict(policy)
        self._members: list[tuple[str, object]] = []
        for entry in finalists:
            bundle = Path(str(entry["bundle"]))
            strategy = strategy_from_module(load_strategy_module(bundle / "strategy.py"))
            apply_strategy_parameters(strategy, dict(entry["centre"]))
            self._members.append((str(entry["team_id"]), strategy))
        # A finalist that holds contributes what it last emitted, so a hold means "no change to my
        # book", not "I have no book". Treating a hold as flat would quietly de-risk the ensemble
        # every time one member went quiet.
        self._last: dict[str, dict[str, float]] = {team: {} for team, _ in self._members}

    def _scalar(self, weights: Mapping[str, float], panel: pd.DataFrame) -> float:
        """The evaluator's ex-ante unit, computed for one book at one decision."""
        held = {name: float(value) for name, value in weights.items() if float(value) != 0.0}
        if not held:
            return 1.0
        window_bars = int(self._policy["risk_window_bars"])
        minimum_bars = int(self._policy["risk_minimum_symbol_bars"])
        names = sorted(name for name in held if name in panel.columns)
        if not names:
            return 1.0
        returns = panel[names].pct_change().iloc[-window_bars:]
        counts = returns.notna().sum(axis=0).to_numpy()
        qualified = counts >= minimum_bars
        if not qualified.any():
            return 1.0
        vector = np.array([held[name] for name in names], dtype=float)
        covariance = np.zeros((len(names), len(names)), dtype=float)
        observed = np.nan_to_num(
            returns.loc[:, qualified].to_numpy(dtype=float), nan=0.0, posinf=0.0, neginf=0.0
        )
        estimated = _ewma_covariance(observed, float(self._policy["risk_halflife_bars"]))
        index = np.flatnonzero(qualified)
        covariance[np.ix_(index, index)] = estimated
        if not qualified.all():
            fallback = float(np.median(np.diag(estimated)))
            for missing in np.flatnonzero(~qualified):
                covariance[missing, missing] = fallback
        variance = float(vector @ covariance @ vector)
        annualized = math.sqrt(max(variance, 0.0) * BARS_PER_YEAR)
        if not math.isfinite(annualized) or annualized <= 0.0:
            return float(self._policy["risk_maximum_scale"])
        return min(
            float(self._policy["risk_maximum_scale"]),
            max(
                float(self._policy["risk_minimum_scale"]),
                float(self._policy["risk_target"]) / annualized,
            ),
        )

    def target_weights(
        self, context: DecisionContextV2, *, seed: int
    ) -> Mapping[str, float] | None:
        panel = toolkit.close_panel(context)
        emitted = False
        books: list[dict[str, float]] = []
        for team_id, member in self._members:
            raw = member.target_weights(context, seed=seed)
            if raw is None:
                books.append(dict(self._last[team_id]))
                continue
            emitted = True
            scaled = {
                str(name): float(value) * self._scalar(raw, panel)
                for name, value in dict(raw).items()
                if float(value) != 0.0
            }
            self._last[team_id] = scaled
            books.append(scaled)
        if not emitted:
            return None
        # Only names that are eligible right now. A member that holds contributes the book it last
        # emitted, and the Top-50 universe rotates weekly, so a stale book can still name a symbol
        # that has since left the cross-section. A lane strategy never meets this because it
        # rebuilds from the current section every decision; an ensemble that reuses books must
        # prune them. Emitting a departed symbol is a candidate failure, and correctly so: the
        # evaluator force-settles a name on its way out and will not let a strategy re-enter it.
        eligible = set(context.eligible_symbols)
        names = sorted({name for book in books for name in book if name in eligible})
        if not names:
            return {}
        count = float(len(self._members))
        averaged = {
            name: sum(book.get(name, 0.0) for book in books) / count for name in names
        }
        return {name: value for name, value in averaged.items() if value != 0.0}


def build_strategy() -> EqualRiskEnsemble:
    payload = json.loads(_MANIFEST.read_text())
    if payload.get("schema_version") != 1:
        raise ValueError("unknown ensemble finalist manifest")
    finalists = list(payload["finalists"])
    if len(finalists) != 3:
        raise ValueError("the equal-risk ensemble is defined over exactly three finalists")
    return EqualRiskEnsemble(finalists, payload["risk_policy"])
