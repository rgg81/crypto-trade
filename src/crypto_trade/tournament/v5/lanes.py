"""The fifteen assigned lanes, as data rather than prose.

Assigned mechanism families are the only construction in this repository's history that has ever
prevented convergence. Left free, fields collapse onto whatever is easiest to express: V4-R9's
fifteen open lanes produced four of five finalists on taker-flow, tradfi-cup-01 put eight of ten on
residual momentum, crypto-cup-01 seven of ten on breakout. A tournament whose lanes all discover the
same mechanism has run one experiment fifteen times.

So the families are assigned, organised by **economic source** rather than technique -- what the
return is compensation for, not which estimator computes it. Two lanes may both use a rolling
regression; they are different lanes if one is harvesting an insurance premium and the other is
trading a convergence.

Three constraints are encoded here rather than left to the mandate text, because a rule that lives
only in prose is one nobody re-checks:

* **Taker-flow is rationed to exactly one lane.** :func:`assert_lane_invariants` fails if a second
  lane claims it. This is the direct structural fix for the convergence above.
* **One lane is mandated to run directional.** Fifteen market-neutral books would leave the field
  unable to say anything about market state, so team-14 must carry non-zero net inside the cap.
* **Every lane names a falsifier.** A mandate that cannot be wrong is not a mandate.

The mandate names the family and never a parameter, an implementation or an expected sign.
Convergent independent ideas remain allowed -- what is forbidden is reading another team's work.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence

# The one signal family rationed to a single lane.
RATIONED_SIGNAL = "taker-flow"


class LaneError(RuntimeError):
    """The lane roster violates a constraint the edition depends on."""


@dataclasses.dataclass(frozen=True, slots=True)
class Lane:
    """One assigned research lane."""

    team_id: str
    family: str
    title: str
    mandate: str
    falsifier: str
    seed: str
    rations: str | None = None
    directional: bool = False

    def brief(self) -> str:
        """The lane's own TEAM-BRIEF.md body. Everything a lane is told, and nothing more."""

        lines = [
            f"# {self.team_id} — {self.title}",
            "",
            f"**Economic family:** {self.family}",
            "",
            "## Your mandate",
            "",
            self.mandate,
            "",
            "## Your falsifier",
            "",
            "State this on visible development data before you look at a result. A mandate that "
            "cannot be wrong is not a mandate.",
            "",
            f"> {self.falsifier}",
            "",
            "## What is fixed",
            "",
            "- Your first charged trial is the **unmodified organizer seed**. The leaderboard "
            "reports how far your nomination moved from it.",
            "- The mandate names a family, never a parameter, an implementation or an expected "
            "sign. How you express it is yours.",
            "- You may not target volatility yourself. A common ex-ante risk unit scales every "
            "book to the same ex-ante volatility, so all lanes are compared at equal risk.",
        ]
        if self.rations:
            lines += [
                "",
                f"- **You are the only lane permitted to use {self.rations} as a primary "
                "signal.** No other lane may build on it.",
            ]
        if self.directional:
            lines += [
                "",
                "- **You are mandated to run non-zero net exposure** inside the |net| ≤ 0.25 cap. "
                "A market-neutral book does not satisfy this mandate.",
            ]
        return "\n".join(lines) + "\n"


LANES: tuple[Lane, ...] = (
    Lane(
        team_id="team-01",
        family="risk-premium harvesting",
        title="funding carry with crowding protection",
        mandate=(
            "Harvest the funding premium across the cross-section. The premium is real and it is "
            "compensation for a crash risk that arrives exactly when the carry is largest. Earn it "
            "without being the last holder."
        ),
        falsifier=(
            "If sorting on funding produces no spread in forward returns once crowding is "
            "controlled for, the premium is not harvestable in this universe."
        ),
        seed="funding_carry",
    ),
    Lane(
        team_id="team-02",
        family="risk-premium harvesting",
        title="funding convexity",
        mandate=(
            "Trade the realized-funding term structure against realized volatility. Funding is an "
            "insurance premium with a jump component; this is the nearest thing this dataset "
            "supports to a variance-risk-premium trade."
        ),
        falsifier=(
            "If funding dispersion carries no information about forward realized volatility, there "
            "is no convexity to trade."
        ),
        seed="funding_convexity",
    ),
    Lane(
        team_id="team-03",
        family="risk-premium harvesting",
        title="defensive, beta-controlled allocation",
        mandate=(
            "Betting-against-beta and quality-minus-junk in their crypto form: short high-"
            "volatility, high-illiquidity names against low, neutral to an equal-weight member "
            "index."
        ),
        falsifier=(
            "If low-volatility members do not outperform high-volatility members on a "
            "beta-adjusted basis, the defensive premium does not exist here."
        ),
        seed="defensive_beta",
    ),
    Lane(
        team_id="team-04",
        family="cross-sectional mispricing",
        title="residual cross-sectional momentum",
        mandate=(
            "Momentum on returns orthogonalised to the market factor, so the book is not a levered "
            "index position wearing a momentum label."
        ),
        falsifier=(
            "If residual momentum's edge disappears once the market factor is removed, the signal "
            "was market beta all along."
        ),
        seed="residual_momentum",
    ),
    Lane(
        team_id="team-05",
        family="cross-sectional mispricing",
        title="illiquidity-conditioned short-horizon reversal",
        mandate=(
            "Reversal is a liquidity-provision premium. Condition it on when liquidity was "
            "actually scarce rather than trading every short-horizon move."
        ),
        falsifier=(
            "If reversal strength does not increase with illiquidity, the premium is not "
            "compensation for providing liquidity."
        ),
        seed="illiquidity_reversal",
    ),
    Lane(
        team_id="team-06",
        family="cross-sectional mispricing",
        title="cluster relative value",
        mandate=(
            "Rolling correlation clusters, trading deviation from cluster mean. Sector-neutral "
            "statistical arbitrage where the sectors are discovered rather than declared."
        ),
        falsifier=(
            "If cluster membership is unstable week to week, deviations from cluster mean are "
            "noise rather than relative value."
        ),
        seed="cluster_relative_value",
    ),
    Lane(
        team_id="team-07",
        family="cross-sectional mispricing",
        title="cointegration convergence",
        mandate=(
            "Rolling pairwise cointegration on log prices, with a preregistered half-life and a "
            "divergence stop. The stop is the hard part of this mandate."
        ),
        falsifier=(
            "If cointegrating relationships do not survive out of the window they were estimated "
            "in, there is nothing to converge to."
        ),
        seed="cointegration",
    ),
    Lane(
        team_id="team-08",
        family="time-series trend",
        title="multi-horizon time-series momentum",
        mandate=(
            "The CTA transplant: per-contract, volatility scaled, multiple lookbacks. The most-"
            "studied premium in the literature and a genuine baseline."
        ),
        falsifier=(
            "If no lookback horizon produces positive average returns per contract, time-series "
            "trend does not persist in this universe."
        ),
        seed="timeseries_momentum",
    ),
    Lane(
        team_id="team-09",
        family="time-series trend",
        title="volume-confirmed breakout",
        mandate=(
            "Channel breakout gated on participation, so the book does not buy every false break."
        ),
        falsifier=(
            "If volume confirmation does not separate continuations from reversals at the break, "
            "the gate adds nothing."
        ),
        seed="volume_breakout",
    ),
    Lane(
        team_id="team-10",
        family="microstructure and participation",
        title="taker-flow pressure",
        mandate=(
            "Aggressor imbalance as a signal about who is pressing and where the pressure resolves."
        ),
        falsifier=(
            "If taker imbalance carries no forward information beyond contemporaneous returns, it "
            "is a description of the past bar rather than a signal."
        ),
        seed="taker_flow",
        rations=RATIONED_SIGNAL,
    ),
    Lane(
        team_id="team-11",
        family="microstructure and participation",
        title="participant mix",
        mandate=(
            "Average trade size as a retail-versus-institutional proxy. A family this dataset "
            "uniquely supports and that no prior edition has attempted."
        ),
        falsifier=(
            "If average trade size is merely a volume proxy, it carries no information that volume "
            "does not already carry."
        ),
        seed="participant_mix",
    ),
    Lane(
        team_id="team-12",
        family="event and state",
        title="volume-shock events",
        mandate=(
            "Extreme quote-volume z-scores as events. Trade the subsequent drift or reversal, "
            "whichever the evidence supports."
        ),
        falsifier=(
            "If post-shock returns are symmetric around zero, the shock is not an event worth "
            "trading in either direction."
        ),
        seed="volume_shock",
    ),
    Lane(
        team_id="team-13",
        family="event and state",
        title="universe inclusion and attention",
        mandate=(
            "Trade weekly membership entry and exit. This lane must model the inclusion effect "
            "explicitly and prove it under the unseasoned-universe rerun, rather than leaving it "
            "to be discovered by accident by a book that then dies of it."
        ),
        falsifier=(
            "If entrants and leavers show no abnormal return around their membership change, "
            "inclusion carries no attention effect."
        ),
        seed="inclusion_attention",
    ),
    Lane(
        team_id="team-14",
        family="event and state",
        title="breadth and market state",
        mandate=(
            "Time net exposure from cross-sectional breadth and dispersion, so the field contains "
            "at least one lane taking a view on market state."
        ),
        falsifier=(
            "If breadth does not lead index returns, it is a coincident summary rather than a "
            "state variable."
        ),
        seed="breadth_state",
        directional=True,
    ),
    Lane(
        team_id="team-15",
        family="combination",
        title="regime-allocated ensemble",
        mandate=(
            "Allocate across mechanism states. In a prior edition this was the only naive seed to "
            "clear its bar, and its ensemble was the best object that edition produced."
        ),
        falsifier=(
            "If a fixed equal-weight blend matches the regime-allocated one, the regime variable "
            "is not doing any work."
        ),
        seed="regime_ensemble",
    ),
)


def lane(team_id: str) -> Lane:
    for entry in LANES:
        if entry.team_id == team_id:
            return entry
    raise LaneError(f"unknown lane: {team_id}")


def assert_lane_invariants(lanes: Sequence[Lane] = LANES) -> None:
    """The roster constraints, checked rather than described.

    Each of these is a property the field's diversity depends on, and each is invisible in any
    single lane's brief -- they are only checkable across the roster, which is why they live here
    rather than in the mandate prose.
    """

    identifiers = [entry.team_id for entry in lanes]
    if len(set(identifiers)) != len(identifiers):
        raise LaneError("duplicate lane identifiers")
    if len(lanes) != 15:
        raise LaneError(f"expected fifteen lanes, found {len(lanes)}")

    rationed = [entry.team_id for entry in lanes if entry.rations == RATIONED_SIGNAL]
    if len(rationed) != 1:
        raise LaneError(
            f"{RATIONED_SIGNAL} must be rationed to exactly one lane, found {rationed}; "
            "an unrationed microstructure signal is what collapsed a prior field onto it"
        )

    directional = [entry.team_id for entry in lanes if entry.directional]
    if len(directional) != 1:
        raise LaneError(
            f"exactly one lane must be mandated directional, found {directional}; "
            "a field of fifteen market-neutral books can say nothing about market state"
        )

    if len({entry.seed for entry in lanes}) != len(lanes):
        raise LaneError("two lanes share an organizer seed")
    for entry in lanes:
        if not entry.falsifier.strip():
            raise LaneError(f"{entry.team_id} has no falsifier; a mandate that cannot be wrong")

    families = {entry.family for entry in lanes}
    if len(families) < 5:
        raise LaneError(f"lane families collapsed to {sorted(families)}")


assert_lane_invariants()


__all__ = ["LANES", "RATIONED_SIGNAL", "Lane", "LaneError", "assert_lane_invariants", "lane"]
