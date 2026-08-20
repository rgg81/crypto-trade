from __future__ import annotations

import dataclasses
import hashlib

import pytest

from crypto_trade.cup50v2.config import TEAM_IDS
from crypto_trade.cup50v2.journal import read_records
from crypto_trade.cup50v2.lifecycle import (
    CandidateFailureError,
    OrganizerFailureError,
    compile_leaderboard,
    freeze_field,
    observe_point,
    recover_interrupted_points,
    start_observation_batch,
    verify_field,
)
from crypto_trade.cup50v2.trials import (
    TrialBinding,
    official_trial_count,
    record_trial_result,
    register_trial,
    resolve_trial_binding,
    source_bundle_digest,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _binding(number: int, *, promoteable: bool = True) -> TrialBinding:
    return TrialBinding(
        team_id="team-01",
        trial_id=f"t{number}",
        kind="official" if promoteable else "falsifier",
        promoteable=promoteable,
        source_sha256=_digest(f"s{number}"),
        parameters={"lookback": number},
        risk_policy_sha256=_digest("risk"),
        seed=number,
        data_sha256=_digest("data"),
        config_sha256=_digest("config"),
        scorer_sha256=_digest("score"),
        purpose="test",
    )


def test_trial_budget_and_uncharged_nonpromoteable_controls(tmp_path) -> None:
    journal = tmp_path / "trials.jsonl"
    for number in range(12):
        register_trial(journal, _binding(number))
    register_trial(journal, _binding(100, promoteable=False))
    assert official_trial_count(journal, "team-01") == 12
    with pytest.raises(ValueError, match="exhausted"):
        register_trial(journal, _binding(13))


def test_trial_source_is_bound_and_result_is_one_shot(tmp_path) -> None:
    journal = tmp_path / "trials.jsonl"
    source = tmp_path / "strategy.py"
    source.write_text("VALUE = 1\n")
    binding = dataclasses.replace(_binding(1), source_sha256=source_bundle_digest(source))
    register_trial(journal, binding)
    resolved = resolve_trial_binding(
        journal,
        team_id=binding.team_id,
        trial_id=binding.trial_id,
        binding_sha256=binding.binding_sha256,
    )
    assert resolved["source_sha256"] == binding.source_sha256
    record_trial_result(
        journal,
        team_id=binding.team_id,
        trial_id=binding.trial_id,
        binding_sha256=binding.binding_sha256,
        source_path=source,
        result_sha256=_digest("result"),
        succeeded=True,
    )
    with pytest.raises(ValueError, match="only once"):
        resolve_trial_binding(
            journal,
            team_id=binding.team_id,
            trial_id=binding.trial_id,
            binding_sha256=binding.binding_sha256,
        )


def test_field_authentication_start_before_point_and_crash_to_dnf(tmp_path) -> None:
    dispositions = {
        team: {
            "state": "nominated",
            "nomination_sha256": _digest(team),
            "point_ids": [f"{team}-p1"],
        }
        for team in TEAM_IDS
    }
    key = b"a" * 32
    field_path = tmp_path / "field.json"
    freeze_field(
        field_path,
        dispositions=dispositions,
        observation_order=TEAM_IDS,
        activation_sha256=_digest("activation"),
        signing_key=key,
    )
    field = verify_field(field_path, signing_key=key)
    journal = tmp_path / "observe.jsonl"
    start_observation_batch(
        journal,
        field_sha256=field["field_sha256"],
        sealed_manifest_sha256=_digest("sealed"),
        observation_order=TEAM_IDS,
        expected_points={team: [f"{team}-p1"] for team in TEAM_IDS},
    )

    def crash():
        raise CandidateFailureError("candidate-crashed")

    result = observe_point(
        journal,
        team_id="team-01",
        point_id="team-01-p1",
        nomination_sha256=_digest("team-01"),
        evaluator=crash,
        private_stage=tmp_path / "private",
    )
    assert result["status"] == "dnf" and result["score"] == 0
    with pytest.raises(ValueError, match="never be retried"):
        observe_point(
            journal,
            team_id="team-01",
            point_id="team-01-p1",
            nomination_sha256=_digest("team-01"),
            evaluator=lambda: {},
            private_stage=tmp_path / "private",
        )


def test_interrupted_started_point_is_terminal_without_evaluator(tmp_path) -> None:
    from crypto_trade.cup50v2.journal import append_record

    journal = tmp_path / "observe.jsonl"
    start_observation_batch(journal, field_sha256=_digest("f"), sealed_manifest_sha256=_digest("s"))
    append_record(
        journal,
        "point-start",
        {"team_id": "team-01", "point_id": "p", "nomination_sha256": _digest("n")},
    )
    assert recover_interrupted_points(journal) == ("p",)
    assert read_records(journal)[-1]["payload"]["score"] == 0.0


def test_organizer_failure_pauses_and_can_resume_same_point(tmp_path) -> None:
    journal = tmp_path / "observe.jsonl"
    start_observation_batch(journal, field_sha256=_digest("f"), sealed_manifest_sha256=_digest("s"))
    arguments = {
        "team_id": "team-01",
        "point_id": "p",
        "nomination_sha256": _digest("n"),
        "private_stage": tmp_path / "private",
    }
    with pytest.raises(OrganizerFailureError):
        observe_point(journal, evaluator=lambda: 1 / 0, **arguments)
    assert recover_interrupted_points(journal) == ()
    result = observe_point(
        journal,
        evaluator=lambda: {"score": 1.0},
        resume_organizer_failure=True,
        **arguments,
    )
    assert result["status"] == "succeeded"


def test_private_evidence_compiles_complete_deterministic_leaderboard(tmp_path) -> None:
    dispositions = {
        team: {
            "state": "nominated",
            "nomination_sha256": _digest(f"nomination-{team}"),
            "source_bundle_sha256": _digest(f"source-{team}"),
            "candidate_id": f"candidate-{team}",
            "centre_index": 0,
            "point_ids": [f"{team}-p0"],
        }
        for team in TEAM_IDS
    }
    key = b"b" * 32
    field_path = tmp_path / "field.json"
    freeze_field(
        field_path,
        dispositions=dispositions,
        observation_order=TEAM_IDS,
        activation_sha256=_digest("activation"),
        signing_key=key,
    )
    field = verify_field(field_path, signing_key=key)
    journal = tmp_path / "observation.jsonl"
    start_observation_batch(
        journal,
        field_sha256=field["field_sha256"],
        sealed_manifest_sha256=_digest("sealed"),
        observation_order=TEAM_IDS,
        expected_points={
            team: disposition["point_ids"] for team, disposition in dispositions.items()
        },
    )
    stage = tmp_path / "private"
    for number, team in enumerate(TEAM_IDS, start=1):
        point_id = f"{team}-p0"
        value = float(number)
        observe_point(
            journal,
            team_id=team,
            point_id=point_id,
            nomination_sha256=dispositions[team]["nomination_sha256"],
            private_stage=stage,
            evaluator=lambda team=team, point_id=point_id, value=value: {
                "team_id": team,
                "point_id": point_id,
                "source_bundle_sha256": dispositions[team]["source_bundle_sha256"],
                "score": {
                    "score": value,
                    "fold_cost_cells": {"F1": {"3": {"q": value}}},
                    "all_cost_cells": {"3": {"drawdown": 0.01}},
                },
                "centre_turnover": 1.0,
            },
        )

    leaderboard = compile_leaderboard(field=field, journal_path=journal, private_stage=stage)

    assert len(leaderboard["entries"]) == 12
    assert leaderboard["winner_team_id"] == "team-12"
    assert leaderboard["entries"][0]["official_score"] == 12.0
