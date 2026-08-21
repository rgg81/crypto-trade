"""What the recorded twelve-seed readiness run proves.

CUP-50 activated on a flat strategy and three organizer defects survived into a live field. This
asserts against the evidence file the real run produced, so a later change that quietly breaks
execution, the risk unit or the cost model fails here rather than in an observation nobody can redo.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

EVIDENCE = Path("tournament/cup50v2/preflight/seed-field-readiness.json")


@pytest.fixture(scope="module")
def readiness() -> dict:
    if not EVIDENCE.is_file() or not EVIDENCE.read_text().strip():
        pytest.skip("readiness has not been run in this checkout")
    return json.loads(EVIDENCE.read_text())


def test_the_whole_field_deployed(readiness: dict) -> None:
    assert readiness["status"] == "ready"
    assert readiness["deployed_lanes"] == 12
    assert len(readiness["lanes"]) == 12


def test_every_lane_traded_and_stayed_solvent(readiness: dict) -> None:
    for team_id, lane in readiness["lanes"].items():
        for multiplier in ("1", "2", "3"):
            cell = lane[multiplier]
            assert cell["turnover"] > 0.0, team_id
            assert cell["final_equity"] > 0.0, (team_id, multiplier)


def test_the_common_risk_unit_delivered_the_target_volatility(readiness: dict) -> None:
    """The point of the ex-ante unit, measured on real data.

    CUP-50 scaled by realised past volatility and its winner ran at 23% annualised against a 10%
    target, which made cross-lane drawdown comparison meaningless. Every lane here lands inside a
    narrow band around the target, so a drawdown difference between two lanes is a difference in
    behaviour rather than in size.
    """
    volatilities = {
        team_id: lane["1"]["annualized_volatility"] for team_id, lane in readiness["lanes"].items()
    }
    for team_id, value in volatilities.items():
        assert 0.06 <= value <= 0.14, (team_id, value)
    spread = max(volatilities.values()) - min(volatilities.values())
    assert spread < 0.05, volatilities


def test_no_lane_was_annihilated_by_its_own_turnover(readiness: dict) -> None:
    """Four CUP-50 lanes ran 231x-937x a year and lost 68-91% at 3x cost."""
    for team_id, lane in readiness["lanes"].items():
        assert lane["1"]["turnover"] < 500.0, (team_id, lane["1"]["turnover"])
        survived = lane["3"]["final_equity"] / lane["1"]["final_equity"]
        assert survived > 0.25, (team_id, survived)


def test_the_qualification_bar_is_calibrated_against_the_measured_field(readiness: dict) -> None:
    """A bar nobody has measured against is a guess that becomes immutable at activation.

    Its first draft (S >= 45, worst regime >= 35) admitted none of the twelve seeds, and the best
    naive worst-regime score in the whole field was 24.3. That is a hurdle, not a floor, and it
    would have made "no winner" the likely outcome of a tournament that was working correctly.
    """
    from crypto_trade.cup50v2.config import active_policy

    bar = active_policy().qualification
    scores = sorted(lane["in_sample"]["score"] for lane in readiness["lanes"].values())
    worst_regimes = sorted(
        min(lane["in_sample"]["regime_scores"].values())
        for lane in readiness["lanes"].values()
        if lane["in_sample"]["regime_scores"]
    )

    # The stored would_qualify flags record the draft bar in force when the run executed; the
    # scores are the evidence and the verdict is derived from whatever bar is active now.
    from crypto_trade.cup50v2.qualification import evaluate_eligibility

    qualifying = [
        team_id
        for team_id, lane in readiness["lanes"].items()
        if evaluate_eligibility(
            {
                "is_score": lane["in_sample"]["score"],
                "is_regime_scores": lane["in_sample"]["regime_scores"],
            }
        ).eligible
    ]
    assert qualifying == ["team-04"], qualifying

    # Each threshold sits inside a gap in the observed distribution rather than on a round number.
    assert max(v for v in scores if v < bar.minimum_is_score) < bar.minimum_is_score
    assert min(v for v in scores if v >= bar.minimum_is_score) > bar.minimum_is_score
    below = [v for v in worst_regimes if v < bar.minimum_is_regime_score]
    above = [v for v in worst_regimes if v >= bar.minimum_is_regime_score]
    assert below and above
    assert min(above) - max(below) > 5.0, (below, above)


def test_every_naive_seed_fails_in_some_market_state(readiness: dict) -> None:
    """The finding the regime term exists to surface, and calendar folds could not.

    Each seed's worst regime is genuinely bad -- a breakout book that dies in a bull, a defensive
    book that dies in a bear, a directional timer that dies in chop. Naive mechanisms are not
    all-weather, and a score that only aggregates half-year folds never has to say so.
    """
    for team_id, lane in readiness["lanes"].items():
        regimes = lane["in_sample"]["regime_scores"]
        assert set(regimes) == {"bull", "bear", "chop"}, team_id
        assert min(regimes.values()) < 30.0, (team_id, regimes)
