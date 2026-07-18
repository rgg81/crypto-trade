from __future__ import annotations

from copy import copy, deepcopy

import pytest

from crypto_trade.tournament.qualification_v3 import (
    CandidateIdentity,
    MetricCheck,
    PrivateAssessment,
    PublicAssessment,
    assess_private,
    assess_public,
    rank_public_assessments,
    robustness_score,
    select_public_cohort,
)


def _identity(
    team_id: str = "team-01",
    candidate_id: str | None = None,
    **changes: str,
) -> CandidateIdentity:
    values = {
        "team_id": team_id,
        "candidate_id": candidate_id or f"{team_id}-candidate",
        "source_bundle_sha256": "a" * 64,
        "strategy_sha256": "b" * 64,
        "dependency_lock_sha256": "c" * 64,
        "config_sha256": "d" * 64,
        "risk_policy_sha256": "e" * 64,
        "data_authority_sha256": "f" * 64,
        "evaluator_sha256": "1" * 64,
    }
    values.update(changes)
    return CandidateIdentity(**values)


def _hard_checks(**changes: bool) -> dict[str, bool]:
    values = {
        "reproducible": True,
        "data_authority": True,
        "universe_compliant": True,
        "causal": True,
        "execution_compliant": True,
        "solvent": True,
        "window_complete": True,
    }
    values.update(changes)
    return values


def _public_metrics() -> dict[str, object]:
    return {
        "net_sharpe": 1.0,
        "annualized_return": 0.10,
        "max_drawdown": 0.20,
        "double_cost_sharpe": 0.70,
        "positive_quarter_fraction": 0.60,
        "trade_count": 2_000,
        "regime_sharpe": {
            "bull": 0.50,
            "bear": 0.20,
            "chop": 0.40,
            "stress": -0.10,
        },
    }


def _public(
    team_id: str = "team-01",
    metrics: dict[str, object] | None = None,
) -> PublicAssessment:
    return assess_public(
        _identity(team_id),
        metrics or _public_metrics(),
        **_hard_checks(),
    )


def test_candidate_identity_binds_every_executable_authority_hash():
    identity = _identity()

    assert len(identity.sha256) == 64
    for field in (
        "source_bundle_sha256",
        "strategy_sha256",
        "dependency_lock_sha256",
        "config_sha256",
        "risk_policy_sha256",
        "data_authority_sha256",
        "evaluator_sha256",
    ):
        changed = _identity(**{field: "2" * 64})
        assert changed.sha256 != identity.sha256

    with pytest.raises(ValueError, match="team_id"):
        _identity("team-11")
    with pytest.raises(ValueError, match="SHA-256"):
        _identity(source_bundle_sha256="not-a-hash")


def test_public_exact_boundaries_are_eligible_without_a_score_cutoff():
    metrics = {
        "net_sharpe": 0.75,
        "annualized_return": 1e-12,
        "max_drawdown": 0.30,
        "double_cost_sharpe": 0.35,
        "positive_quarter_fraction": 0.50,
        "trade_count": 1_000,
        "regime_sharpe": {
            "bull": 0.10,
            "bear": 0.10,
            "chop": -0.75,
            "stress": -0.75,
        },
    }

    assessment = assess_public(_identity(), metrics, **_hard_checks())

    assert assessment.eligible
    assert assessment.failed_core_floor_names == ()
    assert assessment.robustness_score < 50.0
    assert assessment.positive_regime_count == 2
    assert assessment.worst_regime_sharpe == -0.75


@pytest.mark.parametrize(
    ("field", "value", "failed_name"),
    [
        ("net_sharpe", 0.749999, "net_sharpe"),
        ("annualized_return", 0.0, "annualized_return"),
        ("max_drawdown", 0.300001, "max_drawdown"),
        ("double_cost_sharpe", 0.349999, "double_cost_sharpe"),
        ("positive_quarter_fraction", 0.499999, "positive_quarter_fraction"),
        ("trade_count", 999, "trade_count"),
    ],
)
def test_public_scalar_floor_failures_are_not_compensated(field, value, failed_name):
    metrics = _public_metrics()
    metrics[field] = value

    assessment = assess_public(_identity(), metrics, **_hard_checks())

    assert not assessment.eligible
    assert assessment.failed_core_floor_names == (failed_name,)


def test_public_regime_boundaries_are_enforced():
    too_few = _public_metrics()
    too_few["regime_sharpe"] = {
        "bull": 0.1,
        "bear": 0.0,
        "chop": -0.1,
        "stress": -0.2,
    }
    catastrophic = _public_metrics()
    catastrophic["regime_sharpe"] = {
        "bull": 0.1,
        "bear": 0.1,
        "chop": -0.750001,
        "stress": 0.1,
    }

    too_few_result = assess_public(_identity(), too_few, **_hard_checks())
    catastrophic_result = assess_public(_identity(), catastrophic, **_hard_checks())

    assert too_few_result.failed_core_floor_names == ("positive_regime_count",)
    assert catastrophic_result.failed_core_floor_names == ("worst_regime_sharpe",)


@pytest.mark.parametrize(
    "hard_check_name",
    [
        "reproducible",
        "data_authority",
        "universe_compliant",
        "causal",
        "execution_compliant",
        "solvent",
        "window_complete",
    ],
)
def test_each_structural_hard_check_is_an_immutable_public_veto(hard_check_name):
    assessment = assess_public(
        _identity(),
        _public_metrics(),
        **_hard_checks(**{hard_check_name: False}),
    )

    assert not assessment.eligible
    assert assessment.failed_core_floor_names == ()
    assert assessment.structural_checks.failed_names == (hard_check_name,)
    with pytest.raises(AttributeError):
        assessment.structural_checks.reproducible = True


def test_assessment_construction_and_invariant_vectors_fail_closed():
    with pytest.raises(TypeError, match="assess_public"):
        PublicAssessment()
    with pytest.raises(TypeError, match="assess_private"):
        PrivateAssessment()
    with pytest.raises(TypeError, match="qualification factories"):
        MetricCheck()

    assessment = _public()
    tampered_score = copy(assessment)
    object.__setattr__(tampered_score, "robustness_score", assessment.robustness_score + 1.0)
    with pytest.raises(ValueError, match="score is not canonical"):
        rank_public_assessments({"team-01": tampered_score})

    tampered_checks = copy(assessment)
    object.__setattr__(tampered_checks, "core_checks", ())
    with pytest.raises(ValueError, match="check vector is not canonical"):
        rank_public_assessments({"team-01": tampered_checks})


def test_robustness_function_rejects_values_that_could_leave_its_frozen_range():
    with pytest.raises(ValueError, match="at most 4"):
        robustness_score(
            net_sharpe=1.0,
            annualized_return=0.1,
            max_drawdown=0.2,
            double_cost_sharpe=0.7,
            positive_quarter_fraction=0.6,
            positive_regime_count=5,
            worst_regime_sharpe=-0.1,
        )


V2_CANDIDATES = {
    "team-04": {
        "net_sharpe": 1.5251401450635822,
        "annualized_return": 0.22961686194837383,
        "max_drawdown": 0.15948658451650777,
        "double_cost_sharpe": 1.326264500422908,
        "positive_quarter_fraction": 0.5,
        "trade_count": 5775,
        "regime_sharpe": {
            "bull": 1.8164528189119538,
            "bear": 0.7867376412555669,
            "chop": 2.5636916917000785,
            "stress": 1.3266068181061883,
        },
    },
    "team-07": {
        "net_sharpe": 1.019403099046629,
        "annualized_return": 0.11385400886282504,
        "max_drawdown": 0.112721416228173,
        "double_cost_sharpe": 0.919400173865222,
        "positive_quarter_fraction": 0.7142857142857143,
        "trade_count": 3696,
        "regime_sharpe": {
            "bull": 1.2493875924147464,
            "bear": 0.07000458174379083,
            "chop": 2.662496219997043,
            "stress": 0.4817470742798446,
        },
    },
    "team-05": {
        "net_sharpe": 1.119340119061177,
        "annualized_return": 0.18952832447900492,
        "max_drawdown": 0.17530333533769826,
        "double_cost_sharpe": 1.006506530900231,
        "positive_quarter_fraction": 0.5714285714285714,
        "trade_count": 17185,
        "regime_sharpe": {
            "bull": 1.3676076160757955,
            "bear": 0.25017123016029813,
            "chop": 0.27305035771138747,
            "stress": 1.8163745481211946,
        },
    },
    "team-09": {
        "net_sharpe": 0.920044252591556,
        "annualized_return": 0.03164704592923351,
        "max_drawdown": 0.05230692496442779,
        "double_cost_sharpe": 0.7421922620931425,
        "positive_quarter_fraction": 0.6428571428571429,
        "trade_count": 7521,
        "regime_sharpe": {
            "bull": 2.1589620638911358,
            "bear": -0.30494532432063326,
            "chop": 1.8875283385310286,
            "stress": -0.36707829545048376,
        },
    },
}


def test_v2_calibration_is_team_bound_and_ranked_by_unrounded_robustness():
    assessments = {
        team_id: assess_public(_identity(team_id), metrics, **_hard_checks())
        for team_id, metrics in V2_CANDIDATES.items()
    }

    assert all(item.eligible for item in assessments.values())
    assert assessments["team-09"].robustness_score == pytest.approx(46.14891896646174)
    assert assessments["team-09"].robustness_score < 50.0
    assert rank_public_assessments(assessments) == (
        "team-04",
        "team-07",
        "team-05",
        "team-09",
    )


def test_public_rank_uses_every_frozen_tie_break_then_team_id():
    first_metrics = _public_metrics()
    first_metrics["max_drawdown"] = 0.09
    lower_drawdown_metrics = deepcopy(first_metrics)
    lower_drawdown_metrics["max_drawdown"] = 0.08
    first = _public("team-01", first_metrics)
    lower_drawdown = _public("team-02", lower_drawdown_metrics)
    assert first.robustness_score == lower_drawdown.robustness_score
    assert rank_public_assessments({"team-01": first, "team-02": lower_drawdown})[0] == (
        "team-02"
    )

    lower_cost_metrics = _public_metrics()
    lower_cost_metrics["double_cost_sharpe"] = 1.1
    higher_cost_metrics = deepcopy(lower_cost_metrics)
    higher_cost_metrics["double_cost_sharpe"] = 1.2
    lower_cost = _public("team-01", lower_cost_metrics)
    higher_cost = _public("team-02", higher_cost_metrics)
    assert lower_cost.robustness_score == higher_cost.robustness_score
    assert rank_public_assessments({"team-01": lower_cost, "team-02": higher_cost})[0] == (
        "team-02"
    )

    lower_worst_metrics = _public_metrics()
    lower_worst_metrics["regime_sharpe"] = {
        "bull": 1.2,
        "bear": 1.1,
        "chop": 1.0,
        "stress": 0.8,
    }
    higher_worst_metrics = deepcopy(lower_worst_metrics)
    higher_worst_metrics["regime_sharpe"]["stress"] = 0.9
    lower_worst = _public("team-01", lower_worst_metrics)
    higher_worst = _public("team-02", higher_worst_metrics)
    assert lower_worst.robustness_score == higher_worst.robustness_score
    assert rank_public_assessments({"team-01": lower_worst, "team-02": higher_worst})[0] == (
        "team-02"
    )

    identical_one = _public("team-01")
    identical_two = _public("team-02")
    assert rank_public_assessments(
        {"team-02": identical_two, "team-01": identical_one}
    ) == ("team-01", "team-02")


def test_rank_uses_unrounded_score_and_rejects_identity_key_mismatch():
    lower_metrics = _public_metrics()
    lower_metrics["annualized_return"] = 0.1000000000001
    higher_metrics = _public_metrics()
    higher_metrics["annualized_return"] = 0.1000000000002
    lower = _public("team-01", lower_metrics)
    higher = _public("team-02", higher_metrics)

    assert rank_public_assessments({"team-01": lower, "team-02": higher})[0] == "team-02"
    with pytest.raises(ValueError, match="match identity.team_id"):
        rank_public_assessments({"team-02": lower})
    with pytest.raises(ValueError, match="frozen V3 team IDs"):
        rank_public_assessments({"candidate-01": lower})


def test_public_cohort_is_capped_at_four_and_advances_all_when_fewer_pass():
    assessments = {}
    for number in range(1, 6):
        team_id = f"team-{number:02d}"
        metrics = _public_metrics()
        metrics["annualized_return"] = number / 100.0
        assessments[team_id] = _public(team_id, metrics)

    assert select_public_cohort(assessments) == (
        "team-05",
        "team-04",
        "team-03",
        "team-02",
    )
    assert select_public_cohort(dict(list(assessments.items())[:3])) == (
        "team-03",
        "team-02",
        "team-01",
    )


@pytest.mark.parametrize(
    ("team_id", "metrics", "expected_failures"),
    [
        (
            "team-02",
            {
                **_public_metrics(),
                "regime_sharpe": {
                    "bull": 1.9272882271946317,
                    "bear": -1.0155758613712025,
                    "chop": 0.8611137173031981,
                    "stress": 2.2542068737080267,
                },
            },
            ("worst_regime_sharpe",),
        ),
        (
            "team-10",
            {
                **_public_metrics(),
                "regime_sharpe": {
                    "bull": 1.9967498283478824,
                    "bear": -1.3505783247443206,
                    "chop": 0.9332701962859367,
                    "stress": 1.3926047654643599,
                },
            },
            ("worst_regime_sharpe",),
        ),
    ],
)
def test_v2_catastrophic_bear_near_misses_retain_the_calibrated_veto(
    team_id,
    metrics,
    expected_failures,
):
    assessment = assess_public(_identity(team_id), metrics, **_hard_checks())

    assert not assessment.eligible
    assert assessment.failed_core_floor_names == expected_failures


def test_private_boundaries_identity_and_every_structural_veto():
    passing = {
        "net_sharpe": 1e-12,
        "annualized_return": 1e-12,
        "max_drawdown": 0.35,
        "double_cost_sharpe": 1e-12,
    }
    identity = _identity()
    result = assess_private(identity, passing, **_hard_checks())

    assert result.identity == identity
    assert result.eligible
    for field in ("net_sharpe", "annualized_return", "double_cost_sharpe"):
        failing = deepcopy(passing)
        failing[field] = 0.0
        failed = assess_private(identity, failing, **_hard_checks())
        assert not failed.eligible
        assert failed.failed_core_floor_names == (field,)

    drawdown_failure = deepcopy(passing)
    drawdown_failure["max_drawdown"] = 0.350001
    assert assess_private(
        identity,
        drawdown_failure,
        **_hard_checks(),
    ).failed_core_floor_names == ("max_drawdown",)

    for field in _hard_checks():
        failed = assess_private(
            identity,
            passing,
            **_hard_checks(**{field: False}),
        )
        assert not failed.eligible
        assert failed.structural_checks.failed_names == (field,)
