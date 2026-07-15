from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import pytest

from crypto_trade.tournament import finals_v2
from crypto_trade.tournament.finals_v2 import (
    BoundFinalistPerformance,
    FinalistSourceBinding,
    HashBoundJson,
    assess_paper_eligibility,
    build_finalist_performance,
    combine_locked_scores,
    lock_objective_scores,
    validate_finalist_ballots,
    validate_integrity_disqualifications,
)
from crypto_trade.tournament.qualification import assess_private
from crypto_trade.tournament.scoring_v2 import (
    FinalistPerformance,
    RoleStabilityObservations,
    WindowPerformance,
)
from crypto_trade.tournament.top40_v2 import TEAM_IDS, LoadedV2Config, load_config

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "tournament/top40-v2/config.toml"
STRATEGY_SHA = "1" * 64
RISK_SHA = "2" * 64
SOURCE_SHA = "3" * 64
MANIFEST_SHA = "4" * 64


def _json_bytes(payload: object) -> bytes:
    return (
        json.dumps(payload, allow_nan=False, indent=2, sort_keys=True).encode("utf-8")
        + b"\n"
    )


def _bound_json(payload: object) -> HashBoundJson:
    encoded = _json_bytes(payload)
    return HashBoundJson(encoded, hashlib.sha256(encoded).hexdigest())


def _development_evidence(
    config: LoadedV2Config, team_id: str, *, candidate_id: str = "candidate-a"
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "stage": "development",
        "team_id": team_id,
        "candidate_id": candidate_id,
        "strategy_sha256": STRATEGY_SHA,
        "risk_policy_sha256": RISK_SHA,
        "config_sha256": config.sha256,
        "trial_count": 12,
        "aggregate": {
            "net_sharpe": 1.1,
            "annualized_return": 0.18,
            "calmar": 0.9,
            "max_drawdown": 0.2,
            "double_cost_sharpe": 0.7,
            "positive_quarter_fraction": 0.75,
            "trial_adjusted_probability_positive": 0.97,
        },
        "folds": [
            {"fold_id": f"fold-{index}", "net_return": 0.02 + index / 100}
            for index in range(1, 7)
        ],
        "regimes": {
            "bull": {"net_return": 0.2, "net_sharpe": 1.2},
            "bear": {"net_return": 0.1, "net_sharpe": 0.7},
            "chop": {"net_return": 0.08, "net_sharpe": 0.5},
            "stress": {"net_return": 0.03, "net_sharpe": 0.2},
        },
        "roles": {
            "long_bull_net_return": 0.12,
            "short_bear_net_return": 0.08,
            "combined_chop_net_return": 0.08,
        },
        "sleeves": {
            side: {
                "active_bar_fraction": 0.25,
                "mean_gross_exposure": 0.15,
                "executed_notional_usdt": 25000.0,
            }
            for side in ("long", "short")
        },
        "stability": {
            "profitable_neighbor_fraction": 0.8,
            "neighbor_median_sharpe": 0.8,
            "maximum_positive_pnl_concentration": 0.25,
        },
    }


def _private_evidence(
    config: LoadedV2Config, team_id: str, *, candidate_id: str = "candidate-a"
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "stage": "private",
        "team_id": team_id,
        "candidate_id": candidate_id,
        "strategy_sha256": STRATEGY_SHA,
        "risk_policy_sha256": RISK_SHA,
        "config_sha256": config.sha256,
        "trial_count": 12,
        "aggregate": {
            "net_sharpe": 0.85,
            "annualized_return": 0.12,
            "max_drawdown": 0.2,
            "double_cost_sharpe": 0.4,
            "positive_quarter_fraction": 0.75,
        },
    }


def _sealed_private(
    config: LoadedV2Config,
    team_id: str,
    *,
    private_runner_sha256: str,
    candidate_id: str = "candidate-a",
) -> dict[str, Any]:
    evidence = _private_evidence(config, team_id, candidate_id=candidate_id)
    evidence_sha = "5" * 64
    assessment = assess_private(
        evidence,
        config.qualification_thresholds,
        evidence_sha256=evidence_sha,
    )
    return {
        "schema_version": 1,
        "sealed_at_utc": "2026-08-02T12:00:00+00:00",
        "evidence": evidence,
        "provenance": {"builder": "top40-v2-evidence-v1"},
        "assessment": assessment.to_dict(include_observations=True),
        "runner_record_path": (
            f"tournament/top40-v2/private/artifacts/{team_id}/runner_record.json"
        ),
        "runner_record_sha256": private_runner_sha256,
        "organizer_journal_head_sha256": "6" * 64,
        "registration_sha256": "7" * 64,
    }


def _runner_record(
    config: LoadedV2Config,
    team_id: str,
    stage: str,
    *,
    net_sharpe: float | None = None,
) -> dict[str, Any]:
    if stage == "private":
        output = f"tournament/top40-v2/private/artifacts/{team_id}"
        start = str(config.raw["splits"]["private_qualifier_start"])
        end = str(config.raw["splits"]["private_qualifier_end_inclusive"])
        metrics = {
            "net_sharpe": 0.85 if net_sharpe is None else net_sharpe,
            "net_sortino": 1.0,
            "calmar": 0.6,
            "annualized_return": 0.12,
            "max_drawdown": 0.2,
            "positive_quarter_fraction": 0.75,
        }
        double_cost = 0.4
    else:
        output = f"reports-top40-v2/{team_id}/final-oos"
        start = str(config.raw["splits"]["final_oos_start"])
        end = str(config.raw["splits"]["final_oos_end_inclusive"])
        metrics = {
            "net_sharpe": 1.2 if net_sharpe is None else net_sharpe,
            "net_sortino": 1.4,
            "calmar": 1.0,
            "annualized_return": 0.2,
            "max_drawdown": 0.2,
            "positive_quarter_fraction": 0.75,
        }
        double_cost = 0.7
    filenames = {
        "targets": "targets.parquet",
        "events": "events.parquet",
        "positions": "positions.parquet",
        "evaluator_returns": "bar_returns.csv",
        "double_cost_evaluator_returns": "double_cost_bar_returns.csv",
        "daily_returns": "daily_returns.csv",
        "double_cost_daily_returns": "double_cost_daily_returns.csv",
        "trades": "trades.csv",
    }
    return {
        "stage": stage,
        "team_id": team_id,
        "entrypoint": f"tournament/top40-v2/teams/{team_id}/strategy.py",
        "seeds": [config.raw["research_budget"]["strategy_seed"]],
        "data_manifest_sha256": MANIFEST_SHA,
        "config_sha256": config.sha256,
        "strategy_sha256": STRATEGY_SHA,
        "risk_policy_sha256": RISK_SHA,
        "source_bundle_sha256": SOURCE_SHA,
        "output_dir": output,
        "scored_window": {"start": start, "end": end, "metrics": metrics},
        "double_cost_sharpe": double_cost,
        "regime_sharpe": {"bull": 1.1, "bear": 0.7, "chop": 0.5, "stress": 0.2},
        "confidence_intervals": {
            "net_sharpe_95": [0.5, 1.5],
            "double_cost_sharpe_95": [0.1, 1.0],
        },
        "artifacts": {name: f"{output}/{filename}" for name, filename in filenames.items()},
        "artifact_sha256": {name: "8" * 64 for name in filenames},
        "artifact_sizes": {name: 100 for name in filenames},
        "decision_count": 100,
        "event_count": 20,
        "trade_count": 10,
    }


@dataclasses.dataclass(frozen=True)
class _FinalistFixture:
    config: LoadedV2Config
    binding: FinalistSourceBinding
    development: HashBoundJson
    sealed_private: HashBoundJson
    private_runner: HashBoundJson
    final_runner: HashBoundJson

    def build(self) -> BoundFinalistPerformance:
        return build_finalist_performance(
            binding=self.binding,
            development_evidence=self.development,
            private_sealed_record=self.sealed_private,
            private_runner_record=self.private_runner,
            final_oos_runner_record=self.final_runner,
            config=self.config,
        )


def _fixture(
    config: LoadedV2Config,
    team_id: str = "team-01",
    *,
    development_transform: Callable[[dict[str, Any]], None] | None = None,
    sealed_transform: Callable[[dict[str, Any]], None] | None = None,
    private_runner_transform: Callable[[dict[str, Any]], None] | None = None,
    final_runner_transform: Callable[[dict[str, Any]], None] | None = None,
) -> _FinalistFixture:
    development_raw = _development_evidence(config, team_id)
    private_raw = _runner_record(config, team_id, "private")
    final_raw = _runner_record(config, team_id, "final_oos")
    for transform, raw in (
        (development_transform, development_raw),
        (private_runner_transform, private_raw),
        (final_runner_transform, final_raw),
    ):
        if transform is not None:
            transform(raw)
    development = _bound_json(development_raw)
    private = _bound_json(private_raw)
    final = _bound_json(final_raw)
    sealed_raw = _sealed_private(
        config, team_id, private_runner_sha256=private.sha256
    )
    if sealed_transform is not None:
        sealed_transform(sealed_raw)
    sealed = _bound_json(sealed_raw)
    binding = FinalistSourceBinding(
        team_id=team_id,
        candidate_id="candidate-a",
        config_sha256=config.sha256,
        strategy_sha256=STRATEGY_SHA,
        risk_policy_sha256=RISK_SHA,
        source_bundle_sha256=SOURCE_SHA,
        data_manifest_sha256=MANIFEST_SHA,
        development_evidence_sha256=development.sha256,
        private_sealed_record_sha256=sealed.sha256,
        private_runner_record_sha256=private.sha256,
        final_oos_runner_record_sha256=final.sha256,
    )
    return _FinalistFixture(config, binding, development, sealed, private, final)


@pytest.fixture(scope="module")
def config() -> LoadedV2Config:
    return load_config(CONFIG_PATH)


def test_constructs_performance_only_after_full_hash_and_record_reconciliation(
    config: LoadedV2Config,
) -> None:
    finalist = _fixture(config).build()

    assert finalist.performance.team_id == "team-01"
    assert finalist.performance.development.net_sharpe == 1.1
    assert finalist.performance.private.calmar == 0.6
    assert finalist.performance.final_oos.net_sharpe == 1.2
    assert finalist.performance.double_cost_oos_sharpe == 0.7
    assert finalist.performance.role_stability.parameter_stability == 0.8
    assert finalist.performance.role_stability.positive_fold_fraction == 1.0
    assert dict(finalist.performance.regime_sharpes)["stress"] == 0.2
    assert len(finalist.sha256) == 64


def test_exact_byte_hashes_and_strict_json_are_fail_closed() -> None:
    payload = b'{"schema_version":1}'
    with pytest.raises(ValueError, match="differ from the expected SHA"):
        HashBoundJson(payload + b" ", hashlib.sha256(payload).hexdigest())

    duplicated = b'{"team_id":"team-01","team_id":"team-02"}'
    record = HashBoundJson(duplicated, hashlib.sha256(duplicated).hexdigest())
    with pytest.raises(ValueError, match="duplicate JSON key"):
        record.object("duplicated record")

    nonfinite = b'{"value":NaN}'
    record = HashBoundJson(nonfinite, hashlib.sha256(nonfinite).hexdigest())
    with pytest.raises(ValueError, match="non-finite JSON number"):
        record.object("nonfinite record")


def test_rejects_nonpassing_development_and_private_runner_metric_drift(
    config: LoadedV2Config,
) -> None:
    def fail_development(raw: dict[str, Any]) -> None:
        raw["aggregate"]["net_sharpe"] = -0.2

    with pytest.raises(ValueError, match="does not pass every qualification gate"):
        _fixture(config, development_transform=fail_development).build()

    def drift_private(raw: dict[str, Any]) -> None:
        raw["scored_window"]["metrics"]["net_sharpe"] = 0.9

    with pytest.raises(ValueError, match="differs between qualification evidence"):
        _fixture(config, private_runner_transform=drift_private).build()


def test_rejects_tampered_sealed_assessment_and_runner_identity(
    config: LoadedV2Config,
) -> None:
    def alter_assessment(raw: dict[str, Any]) -> None:
        raw["assessment"]["gates"][0]["observed"] = 99.0

    with pytest.raises(ValueError, match="assessment does not match"):
        _fixture(config, sealed_transform=alter_assessment).build()

    def alter_source(raw: dict[str, Any]) -> None:
        raw["source_bundle_sha256"] = "9" * 64

    with pytest.raises(ValueError, match="identity binding"):
        _fixture(config, final_runner_transform=alter_source).build()


def _simple_bound(
    config: LoadedV2Config, team_id: str, *, final_sharpe: float
) -> BoundFinalistPerformance:
    digest_seed = team_id[-2:]
    digest = (digest_seed * 32)[:64]
    binding = FinalistSourceBinding(
        team_id=team_id,
        candidate_id=f"candidate-{team_id}",
        config_sha256=config.sha256,
        strategy_sha256=digest,
        risk_policy_sha256=RISK_SHA,
        source_bundle_sha256=SOURCE_SHA,
        data_manifest_sha256=MANIFEST_SHA,
        development_evidence_sha256="5" * 64,
        private_sealed_record_sha256="6" * 64,
        private_runner_record_sha256="7" * 64,
        final_oos_runner_record_sha256="8" * 64,
    )
    performance = FinalistPerformance(
        team_id=team_id,
        development=WindowPerformance(1.1, 0.18, 0.9, 0.2, 0.75),
        private=WindowPerformance(0.85, 0.12, 0.6, 0.2, 0.75),
        final_oos=WindowPerformance(final_sharpe, 0.2, 1.0, 0.2, 0.75),
        double_cost_oos_sharpe=0.7,
        regime_sharpes=(
            ("bull", 1.1),
            ("bear", 0.7),
            ("chop", 0.5),
            ("stress", 0.2),
        ),
        role_stability=RoleStabilityObservations(0.12, 0.08, 0.08, 0.8, 1.0),
    )
    return BoundFinalistPerformance(binding, performance)


def _objective_lock(config: LoadedV2Config) -> finals_v2.ObjectiveScoreLock:
    finalists = TEAM_IDS[:3]
    records = tuple(
        _simple_bound(config, team_id, final_sharpe=1.4 - index / 10)
        for index, team_id in enumerate(finalists)
    )
    return lock_objective_scores(
        records,
        finalist_team_ids=finalists,
        dnf_team_ids=TEAM_IDS[3:],
        config=config,
    )


def test_objective_lock_handles_variable_and_zero_cohorts_without_fabricating_dnf(
    config: LoadedV2Config,
) -> None:
    locked = _objective_lock(config)

    assert locked.status == "scored"
    assert tuple(record.team_id for record in locked.records) == TEAM_IDS[:3]
    assert not set(locked.dnf_team_ids).intersection(record.team_id for record in locked.records)
    assert sorted(record.objective_rank for record in locked.records) == [1, 2, 3]
    assert all(record.automatic_score <= 70 for record in locked.records)
    assert len(locked.sha256) == 64
    with pytest.raises(dataclasses.FrozenInstanceError):
        locked.status = "no-qualified-model"  # type: ignore[misc]

    empty = lock_objective_scores(
        (),
        finalist_team_ids=(),
        dnf_team_ids=TEAM_IDS,
        config=config,
    )
    assert empty.status == "no-qualified-model"
    assert empty.records == ()


def test_objective_lock_requires_exact_ten_team_partition_and_excludes_dnf_inputs(
    config: LoadedV2Config,
) -> None:
    finalist = _simple_bound(config, "team-01", final_sharpe=1.2)
    dnf = _simple_bound(config, "team-02", final_sharpe=1.0)
    with pytest.raises(ValueError, match="partition all ten"):
        lock_objective_scores(
            (finalist,),
            finalist_team_ids=("team-01",),
            dnf_team_ids=("team-03",),
            config=config,
        )
    with pytest.raises(ValueError, match="DNF excluded"):
        lock_objective_scores(
            (finalist, dnf),
            finalist_team_ids=("team-01",),
            dnf_team_ids=TEAM_IDS[1:],
            config=config,
        )


def test_ballots_are_exact_bounded_finalist_maps_and_dq_is_finalist_only(
    config: LoadedV2Config,
) -> None:
    locked = _objective_lock(config)
    critic = {team_id: 10.0 for team_id in TEAM_IDS[:3]}
    user = {team_id: 11.0 for team_id in TEAM_IDS[:3]}
    ballots = validate_finalist_ballots(
        locked, critic_ballot=critic, user_ballot=user
    )
    assert dict(ballots.critic) == critic

    with pytest.raises(ValueError, match="score every finalist exactly"):
        validate_finalist_ballots(
            locked,
            critic_ballot={"team-01": 10.0},
            user_ballot=user,
        )
    with pytest.raises(ValueError, match=r"\[0, 15\]"):
        validate_finalist_ballots(
            locked,
            critic_ballot={**critic, "team-01": 15.1},
            user_ballot=user,
        )
    with pytest.raises(ValueError, match="numeric"):
        validate_finalist_ballots(
            locked,
            critic_ballot={**critic, "team-01": True},
            user_ballot=user,
        )
    with pytest.raises(ValueError, match="finite"):
        validate_finalist_ballots(
            locked,
            critic_ballot=critic,
            user_ballot={**user, "team-01": math.nan},
        )

    with pytest.raises(ValueError, match="non-finalists"):
        validate_integrity_disqualifications(locked, {"team-04": ["provenance-failure"]})
    with pytest.raises(ValueError, match="at least one"):
        validate_integrity_disqualifications(locked, {"team-01": []})
    with pytest.raises(ValueError, match="unique"):
        validate_integrity_disqualifications(
            locked, {"team-01": ["data-leak", "data-leak"]}
        )
    with pytest.raises(ValueError, match="noncanonical reason codes"):
        validate_integrity_disqualifications(locked, {"team-01": ["data-leak"]})


def test_combination_uses_locked_objective_scores_without_recomputation(
    config: LoadedV2Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    locked = _objective_lock(config)
    objective_values = {
        record.team_id: (record.objective_rank, record.automatic_score)
        for record in locked.records
    }

    def forbidden_recomputation(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("objective scoring must not run during jury combination")

    monkeypatch.setattr(finals_v2.scoring_v2, "score_finalists", forbidden_recomputation)
    combined = combine_locked_scores(
        locked,
        critic_ballot={"team-01": 5.0, "team-02": 15.0, "team-03": 10.0},
        user_ballot={"team-01": 5.0, "team-02": 15.0, "team-03": 10.0},
        integrity_disqualifications={"team-02": ["reproducibility-failure"]},
    )

    assert combined.objective_lock_sha256 == locked.sha256
    assert combined.winner_team_id in {"team-01", "team-03"}
    assert combined.scores[-1].team_id == "team-02"
    assert combined.scores[-1].rank is None
    assert combined.scores[-1].total_score is None
    assert combined.scores[-1].integrity_disqualified
    assert {
        score.team_id: (score.objective_rank, score.automatic_score)
        for score in combined.scores
    } == objective_values


def test_all_finalists_disqualified_requires_integrity_review(
    config: LoadedV2Config,
) -> None:
    locked = _objective_lock(config)
    ballot = {team_id: 10.0 for team_id in TEAM_IDS[:3]}
    combined = combine_locked_scores(
        locked,
        critic_ballot=ballot,
        user_ballot=ballot,
        integrity_disqualifications={
            team_id: ["reproducibility-failure"] for team_id in TEAM_IDS[:3]
        },
    )

    assert combined.status == "integrity-review-required"
    assert combined.winner_team_id is None
    assert all(score.rank is None for score in combined.scores)
    assert all(score.total_score is None for score in combined.scores)


def test_zero_cohort_requires_empty_ballots_and_combines_to_no_qualified_model(
    config: LoadedV2Config,
) -> None:
    locked = lock_objective_scores(
        (), finalist_team_ids=(), dnf_team_ids=TEAM_IDS, config=config
    )
    combined = combine_locked_scores(
        locked,
        critic_ballot={},
        user_ballot={},
        integrity_disqualifications={},
    )

    assert combined.status == "no-qualified-model"
    assert combined.winner_team_id is None
    assert combined.scores == ()
    with pytest.raises(ValueError, match="score every finalist exactly"):
        combine_locked_scores(
            locked,
            critic_ballot={"team-01": 0.0},
            user_ballot={},
            integrity_disqualifications={},
        )


def test_paper_eligibility_is_separate_and_mechanical(
    config: LoadedV2Config,
) -> None:
    eligible = assess_paper_eligibility(
        _simple_bound(config, "team-01", final_sharpe=1.2), config
    )
    ineligible = assess_paper_eligibility(
        _simple_bound(config, "team-02", final_sharpe=0.9), config
    )

    assert eligible.eligible
    assert len(eligible.gates) == 8
    assert not ineligible.eligible
    failed = {gate.name for gate in ineligible.gates if not gate.passed}
    assert failed == {"final_oos.net_sharpe"}
    assert all(gate.name != "tournament.rank" for gate in eligible.gates)


def test_source_binding_rejects_invalid_hash_or_candidate() -> None:
    valid: Mapping[str, object] = {
        "team_id": "team-01",
        "candidate_id": "candidate-a",
        "config_sha256": "0" * 64,
        "strategy_sha256": STRATEGY_SHA,
        "risk_policy_sha256": RISK_SHA,
        "source_bundle_sha256": SOURCE_SHA,
        "data_manifest_sha256": MANIFEST_SHA,
        "development_evidence_sha256": "5" * 64,
        "private_sealed_record_sha256": "6" * 64,
        "private_runner_record_sha256": "7" * 64,
        "final_oos_runner_record_sha256": "8" * 64,
    }
    with pytest.raises(ValueError, match="64 lowercase"):
        FinalistSourceBinding(**{**valid, "strategy_sha256": "ABC"})  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="candidate_id"):
        FinalistSourceBinding(**{**valid, "candidate_id": ""})  # type: ignore[arg-type]
