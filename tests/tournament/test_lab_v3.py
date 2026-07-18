from __future__ import annotations

from copy import copy
from dataclasses import replace

import pytest

from crypto_trade.tournament.lab_v3 import (
    CandidateCheckpoint,
    ComebackRoundAuthorization,
    ValidationLedgerState,
    ValidationProbeAuthorization,
    assess_nomination,
    authorize_validation_probe,
    new_validation_ledger,
    open_comeback_round,
    replay_validation_ledger,
)
from crypto_trade.tournament.qualification_v3 import (
    TEAM_IDS,
    CandidateIdentity,
    StructuralChecks,
    assess_public,
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


def _structural(**changes: bool) -> StructuralChecks:
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
    return StructuralChecks(**values)


def _hard_kwargs(**changes: bool) -> dict[str, bool]:
    checks = _structural(**changes)
    return {
        "reproducible": checks.reproducible,
        "data_authority": checks.data_authority,
        "universe_compliant": checks.universe_compliant,
        "causal": checks.causal,
        "execution_compliant": checks.execution_compliant,
        "solvent": checks.solvent,
        "window_complete": checks.window_complete,
    }


def _checkpoint(
    stage: str,
    identity: CandidateIdentity | None = None,
    **changes: object,
) -> CandidateCheckpoint:
    values: dict[str, object] = {
        "stage": stage,
        "identity": identity or _identity(),
        "structural_checks": _structural(),
        "net_sharpe": 1.0,
        "annualized_return": 0.1,
        "double_cost_sharpe": 0.7,
    }
    values.update(changes)
    return CandidateCheckpoint(**values)


def _public_metrics() -> dict[str, object]:
    return {
        "net_sharpe": 1.0,
        "annualized_return": 0.1,
        "max_drawdown": 0.15,
        "double_cost_sharpe": 0.7,
        "positive_quarter_fraction": 0.6,
        "trade_count": 2_000,
        "regime_sharpe": {
            "bull": 0.5,
            "bear": 0.2,
            "chop": 0.3,
            "stress": -0.1,
        },
    }


def _public(
    identity: CandidateIdentity | None = None,
    metrics: dict[str, object] | None = None,
    **hard_changes: bool,
):
    return assess_public(
        identity or _identity(),
        metrics or _public_metrics(),
        **_hard_kwargs(**hard_changes),
    )


def _authorized_opening(identity: CandidateIdentity):
    return authorize_validation_probe(
        new_validation_ledger(),
        identity,
        round_name="opening",
    )


def _ordinary_snapshot(*assessments) -> dict[str, object]:
    snapshot: dict[str, object] = {team_id: None for team_id in TEAM_IDS}
    for assessment in assessments:
        snapshot[assessment.identity.team_id] = assessment
    return snapshot


def _decision(
    *,
    identity: CandidateIdentity | None = None,
    training=None,
    validation=None,
    public=None,
    ledger=None,
    authorization=None,
    prior_formal_submission_count: int = 0,
):
    selected_identity = identity or _identity()
    if ledger is None or authorization is None:
        default_ledger, default_authorization = _authorized_opening(selected_identity)
        ledger = ledger or default_ledger
        authorization = authorization or default_authorization
    return assess_nomination(
        training=training or _checkpoint("training", selected_identity),
        validation=validation or _checkpoint("validation", selected_identity),
        public_assessment=public or _public(selected_identity),
        validation_ledger=ledger,
        validation_authorization=authorization,
        prior_formal_submission_count=prior_formal_submission_count,
    )


def test_positive_matching_core_eligible_candidate_can_lock_once():
    assert _decision().allowed
    decision = _decision(prior_formal_submission_count=1)
    assert not decision.allowed
    assert decision.failed_requirements == ("one_formal_nomination",)


@pytest.mark.parametrize("stage", ["training", "validation"])
@pytest.mark.parametrize("field", ["net_sharpe", "annualized_return", "double_cost_sharpe"])
def test_nonpositive_training_or_validation_cannot_be_submitted(stage, field):
    identity = _identity()
    checkpoint = _checkpoint(stage, identity, **{field: 0.0})
    decision = (
        _decision(identity=identity, training=checkpoint)
        if stage == "training"
        else _decision(identity=identity, validation=checkpoint)
    )

    assert not decision.allowed
    assert f"positive_{stage}_checkpoint" in decision.failed_requirements


@pytest.mark.parametrize(
    "field",
    [
        "source_bundle_sha256",
        "strategy_sha256",
        "dependency_lock_sha256",
        "config_sha256",
        "risk_policy_sha256",
        "data_authority_sha256",
        "evaluator_sha256",
    ],
)
def test_every_executable_identity_hash_must_match_across_all_records(field):
    identity = _identity()
    changed_identity = _identity(**{field: "2" * 64})
    changed_training = _checkpoint("training", changed_identity)

    decision = _decision(identity=identity, training=changed_training)

    assert not decision.allowed
    assert "candidate_identity_match" in decision.failed_requirements


def test_public_assessment_identity_must_match_both_checkpoints():
    identity = _identity()
    other_identity = _identity(candidate_id="other-candidate", strategy_sha256="2" * 64)

    decision = _decision(identity=identity, public=_public(other_identity))

    assert not decision.allowed
    assert "candidate_identity_match" in decision.failed_requirements


@pytest.mark.parametrize("stage", ["training", "validation"])
@pytest.mark.parametrize(
    "hard_check",
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
def test_each_checkpoint_structural_hard_gate_is_required(stage, hard_check):
    identity = _identity()
    checkpoint = _checkpoint(
        stage,
        identity,
        structural_checks=_structural(**{hard_check: False}),
    )
    decision = (
        _decision(identity=identity, training=checkpoint)
        if stage == "training"
        else _decision(identity=identity, validation=checkpoint)
    )

    assert not decision.allowed
    assert f"{stage}_structural_hard_gates" in decision.failed_requirements


def test_formal_nomination_requires_public_core_eligibility():
    identity = _identity()
    failing_metrics = _public_metrics()
    failing_metrics["net_sharpe"] = 0.74
    public = _public(identity, failing_metrics)

    decision = _decision(identity=identity, public=public)

    assert not decision.allowed
    assert "public_core_eligibility" in decision.failed_requirements


def test_opening_probe_budget_is_per_team_monotonic_and_identity_bound():
    state = new_validation_ledger()
    authorizations = []
    for number in range(1, 4):
        identity = _identity(candidate_id=f"opening-{number}", strategy_sha256=f"{number}" * 64)
        state, authorization = authorize_validation_probe(
            state,
            identity,
            round_name="opening",
        )
        authorizations.append(authorization)

    assert [item.team_round_probe_number for item in authorizations] == [1, 2, 3]
    assert [item.team_total_probe_number for item in authorizations] == [1, 2, 3]
    with pytest.raises(ValueError, match="opening validation probe budget exceeded"):
        authorize_validation_probe(
            state,
            _identity(candidate_id="opening-4", strategy_sha256="4" * 64),
            round_name="opening",
        )
    duplicate_state, _ = _authorized_opening(_identity())
    with pytest.raises(ValueError, match="second validation observation"):
        authorize_validation_probe(
            duplicate_state,
            _identity(),
            round_name="opening",
        )


def test_comeback_is_derived_from_probed_assessments_and_grants_exactly_two():
    passer_identity = _identity("team-01", "passer")
    failing_identity = _identity("team-02", "near-miss")
    state = new_validation_ledger()
    state, _ = authorize_validation_probe(state, passer_identity, round_name="opening")
    state, _ = authorize_validation_probe(state, failing_identity, round_name="opening")
    failing_metrics = _public_metrics()
    failing_metrics["net_sharpe"] = 0.74
    snapshot = _ordinary_snapshot(
        _public(passer_identity),
        _public(failing_identity, failing_metrics),
    )

    state = open_comeback_round(state, snapshot)

    assert "team-01" not in state.comeback_eligible_team_ids
    assert "team-02" in state.comeback_eligible_team_ids
    assert "team-10" in state.comeback_eligible_team_ids
    with pytest.raises(ValueError, match="not organizer-authorized"):
        authorize_validation_probe(
            state,
            _identity("team-01", "passer-comeback"),
            round_name="comeback",
        )

    comeback_authorizations = []
    for number in range(1, 3):
        comeback_identity = _identity(
            "team-02",
            f"comeback-{number}",
            strategy_sha256=f"{number + 2}" * 64,
        )
        state, authorization = authorize_validation_probe(
            state,
            comeback_identity,
            round_name="comeback",
        )
        comeback_authorizations.append(authorization)
    assert [item.team_round_probe_number for item in comeback_authorizations] == [1, 2]
    assert [item.team_total_probe_number for item in comeback_authorizations] == [2, 3]
    assert all(item.comeback_eligible for item in comeback_authorizations)
    with pytest.raises(ValueError, match="comeback validation probe budget exceeded"):
        authorize_validation_probe(
            state,
            _identity("team-02", "comeback-3", strategy_sha256="5" * 64),
            round_name="comeback",
        )


def test_comeback_refuses_three_passers_unprobed_results_and_bad_snapshot_keys():
    state = new_validation_ledger()
    passers = []
    for number in range(1, 4):
        team_id = f"team-{number:02d}"
        identity = _identity(team_id, f"passer-{number}")
        state, _ = authorize_validation_probe(state, identity, round_name="opening")
        passers.append(_public(identity))

    with pytest.raises(ValueError, match="at least three teams"):
        open_comeback_round(state, _ordinary_snapshot(*passers))

    with pytest.raises(ValueError, match="exactly one entry"):
        open_comeback_round(state, {"team-01": passers[0]})

    unprobed = _public(_identity("team-04", "unprobed"))
    with pytest.raises(ValueError, match="not bound to a consumed opening probe"):
        open_comeback_round(state, _ordinary_snapshot(unprobed))

    mismatched = _ordinary_snapshot(passers[0])
    mismatched["team-01"] = _public(_identity("team-02", "wrong-key"))
    with pytest.raises(ValueError, match="match identity.team_id"):
        open_comeback_round(state, mismatched)


def test_probe_authorization_must_be_in_ledger_and_bound_to_validation_identity():
    identity = _identity()
    state = new_validation_ledger()
    state, matching = authorize_validation_probe(state, identity, round_name="opening")
    other_identity = _identity(candidate_id="other-probed", strategy_sha256="2" * 64)
    state, other = authorize_validation_probe(state, other_identity, round_name="opening")

    wrong_binding = _decision(
        identity=identity,
        ledger=state,
        authorization=other,
    )
    assert not wrong_binding.allowed
    assert "validation_probe_identity_binding" in wrong_binding.failed_requirements

    unrelated_state, unrelated = _authorized_opening(_identity("team-02"))
    absent = _decision(
        identity=identity,
        ledger=state,
        authorization=unrelated,
    )
    assert not absent.allowed
    assert "validation_probe_authorization" in absent.failed_requirements
    assert matching in state.probe_authorizations
    assert unrelated in unrelated_state.probe_authorizations


def test_validation_ledger_replay_is_canonical_and_rejects_hash_tampering():
    identity = _identity()
    state, authorization = _authorized_opening(identity)
    replayed = replay_validation_ledger(state.entries)

    assert replayed == state
    assert state.head_sha256 == authorization.record_sha256

    tampered = copy(authorization)
    object.__setattr__(tampered, "record_sha256", "f" * 64)
    with pytest.raises(ValueError, match="authorization hash is invalid"):
        replay_validation_ledger((tampered,))

    with pytest.raises(TypeError, match="canonical replay"):
        ValidationLedgerState()
    with pytest.raises(TypeError, match="authorize_validation_probe"):
        ValidationProbeAuthorization()
    with pytest.raises(TypeError, match="open_comeback_round"):
        ComebackRoundAuthorization()


def test_checkpoint_schema_is_fail_closed():
    with pytest.raises(ValueError, match="stage"):
        _checkpoint("private")
    with pytest.raises(ValueError, match="finite"):
        _checkpoint("training", net_sharpe=float("nan"))
    with pytest.raises(ValueError, match="structural_checks"):
        _checkpoint("training", structural_checks=True)

    checkpoint = _checkpoint("training")
    with pytest.raises(AttributeError):
        checkpoint.identity = _identity("team-02")
    assert replace(checkpoint, annualized_return=0.2).annualized_return == 0.2
