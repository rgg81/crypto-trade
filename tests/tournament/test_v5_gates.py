"""Every declared gate must read a real field and be able to fail.

This repository's dominant infrastructure defect is a gate that exists, passes its own unit test,
and gates nothing -- ten instances in one prior edition. V4-R1 called ``neighborhood_stability``
non-negotiable and it read false on all three advancing finalists. V4-R2 validated
``lower_floors_to_fill_bracket = false`` while the code had been patched so the eligibility raise
never fired.

The meta-test below is the countermeasure: for each gate it breaks exactly the input that gate
claims to read and demands that exactly that gate flips. A gate that never flips, or one that
flips when a different input is broken, fails here.
"""

from __future__ import annotations

import dataclasses

import pytest

from crypto_trade.tournament.v5 import gates

THRESHOLDS = gates.GateThresholds(
    minimum_mean_gross_exposure=0.30,
    minimum_median_effective_breadth=6.0,
    minimum_breadth_pass_fraction=0.80,
    minimum_active_bar_fraction=0.80,
    minimum_side_exposure_share=0.20,
    volatility_band=(0.06, 0.15),
    maximum_risk_unit_capped_fraction=0.50,
    minimum_annualised_turnover=4.0,
    maximum_annualised_turnover=90.0,
    minimum_gross_edge_bps_per_turnover=20.0,
    maximum_cost_share_of_positive_gross=0.50,
    minimum_positive_fold_fraction=0.80,
    minimum_deflated_sharpe_probability=0.70,
    maximum_vol_normalised_drawdown=0.25,
    maximum_top_symbol_gross_pnl_share=0.40,
    minimum_deletion_profile_p05_sharpe=0.0,
    minimum_accepted_trials=8,
)

PASSING = gates.SelectionEvidence(
    mean_gross_exposure=0.55,
    median_effective_breadth=11.0,
    breadth_pass_fraction=0.95,
    active_bar_fraction=0.97,
    long_exposure_share=0.50,
    short_exposure_share=0.50,
    realized_annual_volatility=0.10,
    risk_unit_capped_fraction=0.05,
    ruined=False,
    annualised_turnover=25.0,
    gross_edge_bps_per_turnover=60.0,
    cost_share_of_positive_gross=0.20,
    triple_cost_annualised_return=0.04,
    net_sharpe=1.3,
    double_cost_sharpe=1.0,
    max_drawdown=0.12,
    positive_fold_fraction=1.0,
    deflated_sharpe_probability=0.90,
    top_symbol_gross_pnl_share=0.18,
    deletion_profile_p05_sharpe=0.55,
    accepted_trials=12,
    source_review_passed=True,
    invariance_suite_passed=True,
)

# The single field each gate claims to read, and a value that must break it.
BREAKS: dict[str, dict[str, object]] = {
    "not_ruined": {"ruined": True},
    "mean_gross_exposure": {"mean_gross_exposure": 0.037},
    "effective_breadth": {"median_effective_breadth": 2.17},
    "breadth_persistence": {"breadth_pass_fraction": 0.40},
    "participation": {"active_bar_fraction": 0.47},
    "both_sides_used": {"short_exposure_share": 0.02},
    "risk_unit_attained": {"realized_annual_volatility": 0.202},
    "risk_unit_not_permanently_capped": {"risk_unit_capped_fraction": 0.90},
    "turnover_floor": {"annualised_turnover": 1.39},
    "source_review": {"source_review_passed": False},
    "causal_invariance": {"invariance_suite_passed": False},
    "research_budget": {"accepted_trials": 3},
    "turnover_ceiling": {"annualised_turnover": 268.0},
    "gross_edge_density": {"gross_edge_bps_per_turnover": -358.0},
    "cost_share": {"cost_share_of_positive_gross": 5.56},
    "survives_triple_cost": {"triple_cost_annualised_return": -0.01},
    "fold_breadth": {"positive_fold_fraction": 0.20},
    "deflated_sharpe": {"deflated_sharpe_probability": 0.01},
    "vol_normalised_drawdown": {"max_drawdown": 0.60},
    "symbol_concentration": {"top_symbol_gross_pnl_share": 0.84},
    "deletion_robustness": {"deletion_profile_p05_sharpe": -0.94},
}


def _with(**overrides: object) -> gates.SelectionEvidence:
    return dataclasses.replace(PASSING, **overrides)  # type: ignore[arg-type]


def test_the_baseline_evidence_passes_everything() -> None:
    """A meta-test over a baseline that already fails proves nothing about the mutations."""

    for stage in (gates.DEVELOPMENT_STAGE, gates.SEALED_STAGE):
        assessment = gates.assess(PASSING, THRESHOLDS, stage=stage)
        assert assessment.eligible, assessment.failures()
        assert all(assessment.gates.values())


def test_every_declared_gate_has_a_declared_break() -> None:
    """A gate with no break would silently skip the meta-test below."""

    assert set(BREAKS) == set(gates.ALL_GATES)


@pytest.mark.parametrize("gate_name", sorted(gates.ALL_GATES))
def test_every_gate_reads_a_real_field_and_can_fail(gate_name: str) -> None:
    """Break exactly this gate's input; exactly this gate must flip."""

    assessment = gates.assess(_with(**BREAKS[gate_name]), THRESHOLDS, stage=gates.SEALED_STAGE)
    assert assessment.gates[gate_name] is False, f"gate {gate_name} does not read its field"
    flipped = {name for name, ok in assessment.gates.items() if not ok}
    assert flipped == {gate_name}, f"breaking {gate_name} also flipped {flipped - {gate_name}}"
    assert not assessment.eligible


def test_a_broken_gate_names_itself_in_the_failures() -> None:
    assessment = gates.assess(_with(ruined=True), THRESHOLDS, stage=gates.SEALED_STAGE)
    assert assessment.failures() == ("not_ruined",)


# -- what each stage is entitled to conclude ---------------------------------------------------


def test_development_reports_performance_rather_than_enforcing_it() -> None:
    """Twelve feedback-driven trials make a development Sharpe a statement about a search.

    Every prior edition's floor set admitted zero of the ninety-four measured trials, so enforcing
    performance here is how a field ends up empty and a fallback path ends up choosing.
    """

    weak = _with(deflated_sharpe_probability=0.01, positive_fold_fraction=0.2)
    development = gates.assess(weak, THRESHOLDS, stage=gates.DEVELOPMENT_STAGE)
    assert development.gates["deflated_sharpe"] is False
    assert "deflated_sharpe" in development.reported
    assert "deflated_sharpe" not in development.enforced
    assert development.eligible, "a performance miss must not fail the development stage"


def test_the_sealed_stage_enforces_performance() -> None:
    """The sealed blocks were never optimised against, so that is where performance decides."""

    weak = _with(deflated_sharpe_probability=0.01)
    sealed = gates.assess(weak, THRESHOLDS, stage=gates.SEALED_STAGE)
    assert "deflated_sharpe" in sealed.enforced
    assert not sealed.eligible


def test_degeneracy_stays_hard_at_every_stage() -> None:
    """A book that is not a portfolio is not a marginal candidate at any stage."""

    for name in gates.DEGENERACY_GATES:
        broken = _with(**BREAKS[name])
        for stage in (gates.DEVELOPMENT_STAGE, gates.SEALED_STAGE):
            assert not gates.assess(broken, THRESHOLDS, stage=stage).eligible, (name, stage)


def test_cost_gates_stay_hard_at_every_stage() -> None:
    for name in gates.COST_GATES:
        broken = _with(**BREAKS[name])
        for stage in (gates.DEVELOPMENT_STAGE, gates.SEALED_STAGE):
            assert not gates.assess(broken, THRESHOLDS, stage=stage).eligible, (name, stage)


def test_every_gate_belongs_to_exactly_one_category() -> None:
    """A gate in no category would be evaluated and then ignored."""

    categories = (gates.DEGENERACY_GATES, gates.COST_GATES, gates.PERFORMANCE_GATES)
    seen: set[str] = set()
    for category in categories:
        overlap = seen & set(category)
        assert not overlap, f"gate declared in two categories: {overlap}"
        seen |= set(category)
    assert seen == set(gates.ALL_GATES)


# -- evidence discipline -------------------------------------------------------------------


def test_evidence_cannot_be_constructed_with_a_missing_field() -> None:
    """V4 defaulted ``neighborhood_passed`` to False and reported it false on every finalist that
    advanced. Without defaults, omitting evidence is an error at the call site."""

    with pytest.raises(TypeError):
        gates.SelectionEvidence(mean_gross_exposure=0.5)  # type: ignore[call-arg]


def test_no_evidence_field_has_a_default() -> None:
    for field in dataclasses.fields(gates.SelectionEvidence):
        assert field.default is dataclasses.MISSING, field.name
        assert field.default_factory is dataclasses.MISSING, field.name


def test_impossible_evidence_is_rejected() -> None:
    with pytest.raises(gates.GateError, match="fraction"):
        _with(active_bar_fraction=1.4)
    with pytest.raises(gates.GateError, match="accepted_trials"):
        _with(accepted_trials=-1)


def test_an_unknown_stage_is_rejected_rather_than_defaulted() -> None:
    with pytest.raises(gates.GateError, match="unknown selection stage"):
        gates.assess(PASSING, THRESHOLDS, stage="whatever")


# -- the drawdown restatement ----------------------------------------------------------------


def test_drawdown_is_judged_at_a_common_risk_unit() -> None:
    """A raw cap across a field spanning 7.3%-20.2% realized vol caps book size, not quality.

    These are V4-R9's actual extremes: its least-risky finalist and its winner.
    """

    least_risky = _with(realized_annual_volatility=0.073, max_drawdown=0.200)
    winner = _with(realized_annual_volatility=0.202, max_drawdown=0.194)

    assert gates._vol_normalised_drawdown(least_risky, THRESHOLDS) == pytest.approx(0.274, abs=0.01)
    assert gates._vol_normalised_drawdown(winner, THRESHOLDS) == pytest.approx(0.096, abs=0.01)

    # Under a raw 20% cap the winner looks worse than the flat book; restated, it is far better.
    assert winner.max_drawdown < least_risky.max_drawdown
    assert gates._vol_normalised_drawdown(winner, THRESHOLDS) < gates._vol_normalised_drawdown(
        least_risky, THRESHOLDS
    )


def test_a_zero_volatility_book_cannot_pass_the_drawdown_gate() -> None:
    """Dividing by a vanishing risk unit must not manufacture a flattering ratio."""

    flat = _with(realized_annual_volatility=0.0)
    assert gates._vol_normalised_drawdown(flat, THRESHOLDS) == float("inf")
    assert (
        gates.assess(flat, THRESHOLDS, stage=gates.SEALED_STAGE).gates["vol_normalised_drawdown"]
        is False
    )


def test_assessment_serialises_its_reasoning() -> None:
    payload = gates.assess(_with(ruined=True), THRESHOLDS, stage=gates.SEALED_STAGE).as_dict()
    assert payload["eligible"] is False
    assert payload["failures"] == ["not_ruined"]
    assert set(payload["gates"]) == set(gates.ALL_GATES)
