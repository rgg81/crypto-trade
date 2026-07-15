from __future__ import annotations

import dataclasses
import math

import pytest

from crypto_trade.tournament.scoring_v2 import (
    ABSOLUTE_COMPONENT_WEIGHTS,
    RELATIVE_COMPONENT_WEIGHTS,
    FinalistPerformance,
    RoleStabilityObservations,
    WindowPerformance,
    apply_integrity_disqualifications,
    score_finalists,
)


def _window(
    *,
    sharpe: float = 1.0,
    annualized_return: float = 0.15,
    max_drawdown: float = 0.20,
    positive_quarters: float = 0.625,
) -> WindowPerformance:
    return WindowPerformance(
        net_sharpe=sharpe,
        annualized_return=annualized_return,
        calmar=0.75,
        max_drawdown=max_drawdown,
        positive_quarter_fraction=positive_quarters,
    )


def _performance(
    team_id: str,
    *,
    development_sharpe: float = 1.0,
    private_sharpe: float = 0.8,
    final_sharpe: float = 1.0,
    final_return: float = 0.15,
    final_drawdown: float = 0.20,
    final_positive_quarters: float = 0.625,
    double_cost_sharpe: float = 0.5,
    regime_sharpes: tuple[tuple[str, float], ...] | None = None,
    parameter_stability: float = 0.8,
    positive_fold_fraction: float = 4 / 6,
    bull_long_attribution: float = 0.05,
    bear_short_attribution: float = 0.04,
    chop_combined_return: float = 0.03,
) -> FinalistPerformance:
    return FinalistPerformance(
        team_id=team_id,
        development=_window(sharpe=development_sharpe),
        private=_window(sharpe=private_sharpe),
        final_oos=_window(
            sharpe=final_sharpe,
            annualized_return=final_return,
            max_drawdown=final_drawdown,
            positive_quarters=final_positive_quarters,
        ),
        double_cost_oos_sharpe=double_cost_sharpe,
        regime_sharpes=regime_sharpes
        or (("bull", 1.0), ("bear", 0.5), ("chop", 0.4), ("stress", 0.2)),
        role_stability=RoleStabilityObservations(
            bull_long_attribution=bull_long_attribution,
            bear_short_attribution=bear_short_attribution,
            chop_combined_return=chop_combined_return,
            parameter_stability=parameter_stability,
            positive_fold_fraction=positive_fold_fraction,
        ),
    )


def _component(components: tuple[tuple[str, float], ...], name: str) -> float:
    return dict(components)[name]


def test_formula_weights_are_exactly_fifty_absolute_and_twenty_relative() -> None:
    assert sum(weight for _, weight in ABSOLUTE_COMPONENT_WEIGHTS) == 50.0
    assert sum(weight for _, weight in RELATIVE_COMPONENT_WEIGHTS) == 20.0
    assert [name for name, _ in ABSOLUTE_COMPONENT_WEIGHTS] == [
        "final_oos_sharpe",
        "final_oos_drawdown",
        "double_cost_oos_sharpe",
        "final_oos_annualized_return",
        "final_oos_positive_quarters",
        "regime_robustness",
        "generalization_role_stability",
    ]


def test_fixed_absolute_bands_cap_at_zero_and_fifty() -> None:
    perfect = _performance(
        "team-01",
        development_sharpe=1.5,
        private_sharpe=1.5,
        final_sharpe=1.5,
        final_return=0.30,
        final_drawdown=0.15,
        final_positive_quarters=0.75,
        double_cost_sharpe=0.75,
        regime_sharpes=(
            ("bull", 0.75),
            ("bear", 0.75),
            ("chop", 0.75),
            ("stress", 0.75),
        ),
        parameter_stability=1.0,
        positive_fold_fraction=1.0,
    )
    weak = _performance(
        "team-02",
        development_sharpe=0.0,
        private_sharpe=0.0,
        final_sharpe=0.0,
        final_return=0.0,
        final_drawdown=0.40,
        final_positive_quarters=0.50,
        double_cost_sharpe=0.0,
        regime_sharpes=(
            ("bull", -0.25),
            ("bear", -0.25),
            ("chop", -0.25),
            ("stress", -0.25),
        ),
        parameter_stability=0.0,
        positive_fold_fraction=0.0,
        bull_long_attribution=0.0,
        bear_short_attribution=0.0,
        chop_combined_return=0.0,
    )

    scored = {score.team_id: score for score in score_finalists([perfect, weak]).scores}

    assert scored["team-01"].absolute_score == 50.0
    assert scored["team-02"].absolute_score == 0.0
    assert _component(scored["team-02"].absolute_components, "final_oos_sharpe") == 0.0
    assert _component(scored["team-02"].absolute_components, "final_oos_drawdown") == 0.0
    assert (
        _component(scored["team-02"].absolute_components, "double_cost_oos_sharpe")
        == 0.0
    )


@pytest.mark.parametrize("cohort_size", [1, 3, 7, 10])
def test_variable_finalist_cohort_scores_only_supplied_finalists(cohort_size: int) -> None:
    finalists = [
        _performance(f"team-{index:02d}", final_sharpe=0.5 + index / 10)
        for index in range(1, cohort_size + 1)
    ]

    result = score_finalists(finalists)

    assert result.status == "scored"
    assert len(result.scores) == cohort_size
    assert {score.team_id for score in result.scores} == {
        finalist.team_id for finalist in finalists
    }
    assert sorted(score.rank for score in result.scores if score.rank is not None) == list(
        range(1, cohort_size + 1)
    )


def test_zero_finalists_is_explicit_no_qualified_model_and_dnf_is_not_fabricated() -> None:
    result = score_finalists([])

    assert result.status == "no-qualified-model"
    assert result.winner_team_id is None
    assert result.scores == ()


def test_tie_aware_relative_percentiles_and_team_id_tie_breaks_are_deterministic() -> None:
    lower = _performance("team-01", final_sharpe=0.5)
    tied_later = _performance("team-03", final_sharpe=1.0)
    tied_earlier = _performance("team-02", final_sharpe=1.0)

    result = score_finalists([tied_later, lower, tied_earlier])
    scored = {score.team_id: score for score in result.scores}

    assert _component(scored["team-01"].relative_components, "final_oos_sharpe") == 0.0
    assert _component(scored["team-02"].relative_components, "final_oos_sharpe") == 5.25
    assert _component(scored["team-03"].relative_components, "final_oos_sharpe") == 5.25
    assert scored["team-02"].automatic_score == scored["team-03"].automatic_score
    assert scored["team-02"].objective_rank < scored["team-03"].objective_rank
    assert scored["team-02"].rank < scored["team-03"].rank


def test_lower_drawdown_receives_the_better_relative_rank() -> None:
    safer = _performance("team-01", final_drawdown=0.10)
    riskier = _performance("team-02", final_drawdown=0.35)
    scored = {score.team_id: score for score in score_finalists([safer, riskier]).scores}

    assert _component(scored["team-01"].relative_components, "final_oos_drawdown") == 4.0
    assert _component(scored["team-02"].relative_components, "final_oos_drawdown") == 0.0


def test_single_finalist_receives_neutral_relative_percentiles() -> None:
    score = score_finalists([_performance("team-01")]).scores[0]

    assert score.relative_score == 10.0
    assert all(
        points == pytest.approx(weight * 0.5)
        for (_, points), (_, weight) in zip(
            score.relative_components, RELATIVE_COMPONENT_WEIGHTS, strict=True
        )
    )


def test_critic_and_user_scores_are_bounded_and_unknown_teams_are_rejected() -> None:
    finalist = _performance("team-01")
    score = score_finalists(
        [finalist],
        critic_scores={"team-01": 15.0},
        user_scores={"team-01": 14.5},
    ).scores[0]
    assert score.total_score == pytest.approx(score.automatic_score + 29.5)
    assert score.total_score <= 100.0

    with pytest.raises(ValueError, match=r"\[0, 15\]"):
        score_finalists([finalist], critic_scores={"team-01": 15.1})
    with pytest.raises(ValueError, match="finite"):
        score_finalists([finalist], user_scores={"team-01": math.nan})
    with pytest.raises(ValueError, match="numeric"):
        score_finalists([finalist], critic_scores={"team-01": True})
    with pytest.raises(ValueError, match="unknown finalists"):
        score_finalists([finalist], critic_scores={"team-09": 1.0})


def test_performance_inputs_validate_finite_domains_regimes_and_are_immutable() -> None:
    with pytest.raises(ValueError, match="finite"):
        _window(sharpe=math.nan)
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        _window(max_drawdown=1.1)
    with pytest.raises(ValueError, match="exactly"):
        _performance(
            "team-01",
            regime_sharpes=(("bull", 1.0), ("bear", 0.5), ("chop", 0.4)),
        )
    with pytest.raises(ValueError, match="duplicate"):
        _performance(
            "team-01",
            regime_sharpes=(
                ("bull", 1.0),
                ("bull", 0.5),
                ("chop", 0.4),
                ("stress", 0.2),
            ),
        )

    finalist = _performance("team-01")
    assert finalist.regime_sharpes == tuple(sorted(finalist.regime_sharpes))
    with pytest.raises(dataclasses.FrozenInstanceError):
        finalist.team_id = "team-02"  # type: ignore[misc]


def test_later_integrity_dq_preserves_locked_objective_scores_and_ranks() -> None:
    finalists = [
        _performance("team-01", final_sharpe=0.8),
        _performance("team-02", final_sharpe=1.1),
        _performance("team-03", final_sharpe=1.4),
    ]
    locked = score_finalists(
        finalists,
        critic_scores={team.team_id: 10.0 for team in finalists},
        user_scores={team.team_id: 10.0 for team in finalists},
    )
    baseline = {score.team_id: score for score in locked.scores}

    adjudicated = apply_integrity_disqualifications(
        locked, {"team-02": ("proven future-data access",)}
    )
    after = {score.team_id: score for score in adjudicated.scores}

    for team_id, original in baseline.items():
        assert after[team_id].absolute_score == original.absolute_score
        assert after[team_id].relative_score == original.relative_score
        assert after[team_id].automatic_score == original.automatic_score
        assert after[team_id].objective_rank == original.objective_rank
    disqualified = after["team-02"]
    assert disqualified.integrity_disqualified
    assert disqualified.rank is None
    assert disqualified.total_score is None
    assert disqualified.disqualification_reasons == ("proven future-data access",)
    assert adjudicated.winner_team_id == "team-03"
    assert sorted(score.rank for score in adjudicated.scores if score.rank is not None) == [1, 2]


def test_integrity_dq_validation_cannot_mutate_or_name_unknown_objective_records() -> None:
    locked = score_finalists([_performance("team-01")])

    with pytest.raises(ValueError, match="nonempty strings"):
        apply_integrity_disqualifications(locked, {"team-01": ("",)})
    with pytest.raises(ValueError, match="unknown finalists"):
        apply_integrity_disqualifications(locked, {"team-02": ("leak",)})
