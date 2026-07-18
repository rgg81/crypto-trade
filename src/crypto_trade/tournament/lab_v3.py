"""Fail-closed Top-40 V3 probe-ledger and formal-nomination controls.

Validation observations are authorized by an organizer-owned canonical hash chain.  A nomination
must present the exact consumed authorization bound to the same immutable identity as its training,
validation, and public-qualification records.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from collections.abc import Iterable, Mapping

from crypto_trade.tournament.qualification_v3 import (
    TEAM_IDS,
    CandidateIdentity,
    PublicAssessment,
    StructuralChecks,
    validate_public_assessment,
)

OPENING_VALIDATION_PROBES = 3
COMEBACK_VALIDATION_PROBES = 2
_GENESIS_SHA256 = "0" * 64
_ROUNDS = ("opening", "comeback")


def _canonical_sha256(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _finite(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _new_instance(cls: type[object], **fields: object):
    instance = object.__new__(cls)
    for name, value in fields.items():
        object.__setattr__(instance, name, value)
    return instance


@dataclasses.dataclass(frozen=True)
class CandidateCheckpoint:
    """Metrics and hard-gate facts from one identity-bound train or validation run."""

    stage: str
    identity: CandidateIdentity
    structural_checks: StructuralChecks
    net_sharpe: float
    annualized_return: float
    double_cost_sharpe: float

    def __post_init__(self) -> None:
        if self.stage not in {"training", "validation"}:
            raise ValueError("checkpoint stage must be training or validation")
        if not isinstance(self.identity, CandidateIdentity):
            raise ValueError("checkpoint identity must be a CandidateIdentity")
        if not isinstance(self.structural_checks, StructuralChecks):
            raise ValueError("checkpoint structural_checks must be StructuralChecks")
        for field in ("net_sharpe", "annualized_return", "double_cost_sharpe"):
            object.__setattr__(self, field, _finite(getattr(self, field), field))

    @property
    def positive(self) -> bool:
        return (
            self.net_sharpe > 0.0
            and self.annualized_return > 0.0
            and self.double_cost_sharpe > 0.0
        )

    @property
    def readiness_eligible(self) -> bool:
        return self.structural_checks.passed and self.positive


@dataclasses.dataclass(frozen=True, init=False)
class ComebackRoundAuthorization:
    """Hash-chain declaration of the exact teams eligible for the one comeback round."""

    sequence: int
    eligible_team_ids: tuple[str, ...]
    ordinary_assessment_snapshot_sha256: str
    previous_record_sha256: str
    record_sha256: str

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("comeback authorizations are created only by open_comeback_round")


@dataclasses.dataclass(frozen=True, init=False)
class ValidationProbeAuthorization:
    """One consumed, identity-bound validation observation in the organizer hash chain."""

    sequence: int
    team_id: str
    candidate_identity_sha256: str
    round_name: str
    team_round_probe_number: int
    team_total_probe_number: int
    comeback_eligible: bool
    previous_record_sha256: str
    record_sha256: str

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("probe authorizations are created only by authorize_validation_probe")


ValidationLedgerEntry = ComebackRoundAuthorization | ValidationProbeAuthorization


@dataclasses.dataclass(frozen=True, init=False)
class ValidationLedgerState:
    """Canonical replay result for all consumed validation observations."""

    entries: tuple[ValidationLedgerEntry, ...]
    head_sha256: str
    comeback_open: bool
    comeback_eligible_team_ids: tuple[str, ...]
    opening_counts: tuple[tuple[str, int], ...]
    comeback_counts: tuple[tuple[str, int], ...]

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("ValidationLedgerState objects are created only by canonical replay")

    @property
    def probe_authorizations(self) -> tuple[ValidationProbeAuthorization, ...]:
        return tuple(
            entry for entry in self.entries if isinstance(entry, ValidationProbeAuthorization)
        )


def _comeback_payload(
    *,
    sequence: int,
    eligible_team_ids: tuple[str, ...],
    ordinary_assessment_snapshot_sha256: str,
    previous_record_sha256: str,
) -> dict[str, object]:
    return {
        "eligible_team_ids": list(eligible_team_ids),
        "event": "comeback-round-opened",
        "ordinary_assessment_snapshot_sha256": ordinary_assessment_snapshot_sha256,
        "previous_record_sha256": previous_record_sha256,
        "sequence": sequence,
    }


def _probe_payload(
    *,
    sequence: int,
    team_id: str,
    candidate_identity_sha256: str,
    round_name: str,
    team_round_probe_number: int,
    team_total_probe_number: int,
    comeback_eligible: bool,
    previous_record_sha256: str,
) -> dict[str, object]:
    return {
        "candidate_identity_sha256": candidate_identity_sha256,
        "comeback_eligible": comeback_eligible,
        "event": "validation-probe-consumed",
        "previous_record_sha256": previous_record_sha256,
        "round_name": round_name,
        "sequence": sequence,
        "team_id": team_id,
        "team_round_probe_number": team_round_probe_number,
        "team_total_probe_number": team_total_probe_number,
    }


def _counts_tuple(counts: Mapping[str, int]) -> tuple[tuple[str, int], ...]:
    return tuple((team_id, counts[team_id]) for team_id in TEAM_IDS if counts[team_id])


def replay_validation_ledger(
    entries: Iterable[ValidationLedgerEntry],
) -> ValidationLedgerState:
    """Replay and verify the full canonical validation hash chain, failing closed on any gap."""

    if isinstance(entries, (str, bytes, Mapping)):
        raise ValueError("validation ledger entries must be an ordered iterable")
    try:
        frozen_entries = tuple(entries)
    except TypeError as exc:
        raise ValueError("validation ledger entries must be an ordered iterable") from exc

    head = _GENESIS_SHA256
    comeback_open = False
    eligible_team_ids: tuple[str, ...] = ()
    opening_counts = {team_id: 0 for team_id in TEAM_IDS}
    comeback_counts = {team_id: 0 for team_id in TEAM_IDS}
    observed_candidate_identities: set[str] = set()

    for sequence, entry in enumerate(frozen_entries, start=1):
        if type(entry) is ComebackRoundAuthorization:
            if comeback_open:
                raise ValueError("the comeback round may be opened only once")
            if type(entry.sequence) is not int or entry.sequence != sequence:
                raise ValueError("validation ledger sequence is not contiguous")
            if entry.previous_record_sha256 != head:
                raise ValueError("validation ledger previous hash does not match")
            if (
                not isinstance(entry.eligible_team_ids, tuple)
                or not entry.eligible_team_ids
                or entry.eligible_team_ids != tuple(sorted(set(entry.eligible_team_ids)))
                or any(team_id not in TEAM_IDS for team_id in entry.eligible_team_ids)
            ):
                raise ValueError("comeback eligible teams are invalid")
            if not _is_sha256(entry.ordinary_assessment_snapshot_sha256):
                raise ValueError("ordinary assessment snapshot hash is invalid")
            expected_hash = _canonical_sha256(
                _comeback_payload(
                    sequence=sequence,
                    eligible_team_ids=entry.eligible_team_ids,
                    ordinary_assessment_snapshot_sha256=(
                        entry.ordinary_assessment_snapshot_sha256
                    ),
                    previous_record_sha256=head,
                )
            )
            if not _is_sha256(entry.record_sha256) or entry.record_sha256 != expected_hash:
                raise ValueError("comeback authorization hash is invalid")
            eligible_team_ids = entry.eligible_team_ids
            comeback_open = True
            head = entry.record_sha256
            continue

        if type(entry) is not ValidationProbeAuthorization:
            raise ValueError("validation ledger contains an unknown entry type")
        if type(entry.sequence) is not int or entry.sequence != sequence:
            raise ValueError("validation ledger sequence is not contiguous")
        if entry.previous_record_sha256 != head:
            raise ValueError("validation ledger previous hash does not match")
        if entry.team_id not in TEAM_IDS:
            raise ValueError("probe authorization has an invalid team ID")
        if not _is_sha256(entry.candidate_identity_sha256):
            raise ValueError("probe authorization has an invalid candidate identity hash")
        if entry.candidate_identity_sha256 in observed_candidate_identities:
            raise ValueError("a candidate identity cannot consume a second validation observation")
        if entry.round_name not in _ROUNDS:
            raise ValueError("probe authorization has an invalid round")
        if type(entry.comeback_eligible) is not bool:
            raise ValueError("probe comeback eligibility must be Boolean")

        if entry.round_name == "opening":
            if comeback_open:
                raise ValueError("opening probes cannot be consumed after comeback opens")
            if entry.comeback_eligible:
                raise ValueError("an opening probe cannot claim comeback eligibility")
            next_round_count = opening_counts[entry.team_id] + 1
            if next_round_count > OPENING_VALIDATION_PROBES:
                raise ValueError("opening validation probe budget exceeded")
            opening_counts[entry.team_id] = next_round_count
        else:
            if not comeback_open or entry.team_id not in eligible_team_ids:
                raise ValueError("team is not authorized for a comeback probe")
            if not entry.comeback_eligible:
                raise ValueError("comeback probe must bind organizer-declared eligibility")
            next_round_count = comeback_counts[entry.team_id] + 1
            if next_round_count > COMEBACK_VALIDATION_PROBES:
                raise ValueError("comeback validation probe budget exceeded")
            comeback_counts[entry.team_id] = next_round_count

        expected_total = opening_counts[entry.team_id] + comeback_counts[entry.team_id]
        if (
            type(entry.team_round_probe_number) is not int
            or entry.team_round_probe_number != next_round_count
        ):
            raise ValueError("team round probe number is not canonical")
        if (
            type(entry.team_total_probe_number) is not int
            or entry.team_total_probe_number != expected_total
        ):
            raise ValueError("team total probe number is not canonical")
        expected_hash = _canonical_sha256(
            _probe_payload(
                sequence=sequence,
                team_id=entry.team_id,
                candidate_identity_sha256=entry.candidate_identity_sha256,
                round_name=entry.round_name,
                team_round_probe_number=entry.team_round_probe_number,
                team_total_probe_number=entry.team_total_probe_number,
                comeback_eligible=entry.comeback_eligible,
                previous_record_sha256=head,
            )
        )
        if not _is_sha256(entry.record_sha256) or entry.record_sha256 != expected_hash:
            raise ValueError("validation probe authorization hash is invalid")
        observed_candidate_identities.add(entry.candidate_identity_sha256)
        head = entry.record_sha256

    return _new_instance(
        ValidationLedgerState,
        entries=frozen_entries,
        head_sha256=head,
        comeback_open=comeback_open,
        comeback_eligible_team_ids=eligible_team_ids,
        opening_counts=_counts_tuple(opening_counts),
        comeback_counts=_counts_tuple(comeback_counts),
    )


def new_validation_ledger() -> ValidationLedgerState:
    """Return the canonical empty organizer validation ledger."""

    return replay_validation_ledger(())


def _validated_state(state: ValidationLedgerState) -> ValidationLedgerState:
    if type(state) is not ValidationLedgerState:
        raise ValueError("validation_ledger must be a ValidationLedgerState")
    replayed = replay_validation_ledger(state.entries)
    if replayed != state:
        raise ValueError("validation ledger state does not match canonical replay")
    return replayed


def open_comeback_round(
    state: ValidationLedgerState,
    ordinary_assessments: Mapping[str, PublicAssessment | None],
) -> ValidationLedgerState:
    """Derive and hash-bind comeback eligibility from the exact ten-team public snapshot."""

    verified = _validated_state(state)
    if verified.comeback_open:
        raise ValueError("the comeback round is already open")
    if not isinstance(ordinary_assessments, Mapping) or set(ordinary_assessments) != set(TEAM_IDS):
        raise ValueError("ordinary_assessments must contain exactly one entry for every V3 team")

    snapshot: list[dict[str, object]] = []
    eligible_list: list[str] = []
    passer_count = 0
    for team_id in TEAM_IDS:
        assessment = ordinary_assessments[team_id]
        if assessment is None:
            snapshot.append(
                {
                    "candidate_identity_sha256": None,
                    "core_checks": None,
                    "eligible": False,
                    "structural_failed_names": None,
                    "team_id": team_id,
                }
            )
            eligible_list.append(team_id)
            continue
        validate_public_assessment(assessment)
        if assessment.identity.team_id != team_id:
            raise ValueError("ordinary assessment key must match identity.team_id")
        if not any(
            authorization.round_name == "opening"
            and authorization.team_id == team_id
            and authorization.candidate_identity_sha256 == assessment.identity.sha256
            for authorization in verified.probe_authorizations
        ):
            raise ValueError("ordinary assessment is not bound to a consumed opening probe")
        is_eligible = assessment.eligible
        passer_count += int(is_eligible)
        if not is_eligible:
            eligible_list.append(team_id)
        snapshot.append(
            {
                "candidate_identity_sha256": assessment.identity.sha256,
                "core_checks": [
                    {
                        "name": check.name,
                        "observed": check.observed,
                        "operator": check.operator,
                        "passed": check.passed,
                        "threshold": check.threshold,
                    }
                    for check in assessment.core_checks
                ],
                "eligible": is_eligible,
                "structural_failed_names": list(assessment.structural_checks.failed_names),
                "team_id": team_id,
            }
        )
    if passer_count >= 3:
        raise ValueError("comeback cannot open when at least three teams pass the public core")
    eligible = tuple(eligible_list)
    snapshot_sha256 = _canonical_sha256({"ordinary_assessments": snapshot})
    sequence = len(verified.entries) + 1
    payload = _comeback_payload(
        sequence=sequence,
        eligible_team_ids=eligible,
        ordinary_assessment_snapshot_sha256=snapshot_sha256,
        previous_record_sha256=verified.head_sha256,
    )
    declaration = _new_instance(
        ComebackRoundAuthorization,
        sequence=sequence,
        eligible_team_ids=eligible,
        ordinary_assessment_snapshot_sha256=snapshot_sha256,
        previous_record_sha256=verified.head_sha256,
        record_sha256=_canonical_sha256(payload),
    )
    return replay_validation_ledger((*verified.entries, declaration))


def authorize_validation_probe(
    state: ValidationLedgerState,
    identity: CandidateIdentity,
    *,
    round_name: str,
) -> tuple[ValidationLedgerState, ValidationProbeAuthorization]:
    """Consume one identity-bound probe and append its canonical organizer authorization."""

    verified = _validated_state(state)
    if not isinstance(identity, CandidateIdentity):
        raise ValueError("identity must be a CandidateIdentity")
    if round_name not in _ROUNDS:
        raise ValueError("round_name must be opening or comeback")
    opening_counts = dict(verified.opening_counts)
    comeback_counts = dict(verified.comeback_counts)
    opening_count = opening_counts.get(identity.team_id, 0)
    comeback_count = comeback_counts.get(identity.team_id, 0)

    if round_name == "opening":
        if verified.comeback_open:
            raise ValueError("opening probes are closed after the comeback declaration")
        if opening_count >= OPENING_VALIDATION_PROBES:
            raise ValueError("opening validation probe budget exceeded")
        round_probe_number = opening_count + 1
        comeback_eligible = False
    else:
        if not verified.comeback_open or identity.team_id not in verified.comeback_eligible_team_ids:
            raise ValueError("team is not organizer-authorized for the comeback round")
        if comeback_count >= COMEBACK_VALIDATION_PROBES:
            raise ValueError("comeback validation probe budget exceeded")
        round_probe_number = comeback_count + 1
        comeback_eligible = True

    sequence = len(verified.entries) + 1
    total_probe_number = opening_count + comeback_count + 1
    payload = _probe_payload(
        sequence=sequence,
        team_id=identity.team_id,
        candidate_identity_sha256=identity.sha256,
        round_name=round_name,
        team_round_probe_number=round_probe_number,
        team_total_probe_number=total_probe_number,
        comeback_eligible=comeback_eligible,
        previous_record_sha256=verified.head_sha256,
    )
    authorization = _new_instance(
        ValidationProbeAuthorization,
        sequence=sequence,
        team_id=identity.team_id,
        candidate_identity_sha256=identity.sha256,
        round_name=round_name,
        team_round_probe_number=round_probe_number,
        team_total_probe_number=total_probe_number,
        comeback_eligible=comeback_eligible,
        previous_record_sha256=verified.head_sha256,
        record_sha256=_canonical_sha256(payload),
    )
    updated = replay_validation_ledger((*verified.entries, authorization))
    return updated, authorization


@dataclasses.dataclass(frozen=True)
class NominationDecision:
    """Complete deterministic result of the formal-submission preflight."""

    allowed: bool
    failed_requirements: tuple[str, ...]


def assess_nomination(
    *,
    training: CandidateCheckpoint,
    validation: CandidateCheckpoint,
    public_assessment: PublicAssessment,
    validation_ledger: ValidationLedgerState,
    validation_authorization: ValidationProbeAuthorization,
    prior_formal_submission_count: int,
) -> NominationDecision:
    """Decide whether one exact public-core-eligible candidate may create its only lock."""

    if not isinstance(training, CandidateCheckpoint) or training.stage != "training":
        raise ValueError("training must be a training CandidateCheckpoint")
    if not isinstance(validation, CandidateCheckpoint) or validation.stage != "validation":
        raise ValueError("validation must be a validation CandidateCheckpoint")
    validate_public_assessment(public_assessment)
    verified_ledger = _validated_state(validation_ledger)
    if type(validation_authorization) is not ValidationProbeAuthorization:
        raise ValueError("validation_authorization must be a canonical probe authorization")
    if (
        isinstance(prior_formal_submission_count, bool)
        or not isinstance(prior_formal_submission_count, int)
        or prior_formal_submission_count < 0
    ):
        raise ValueError("prior_formal_submission_count must be a nonnegative integer")

    failed: list[str] = []
    identities = (training.identity, validation.identity, public_assessment.identity)
    if not all(identity == identities[0] for identity in identities[1:]):
        failed.append("candidate_identity_match")
    if not training.structural_checks.passed:
        failed.append("training_structural_hard_gates")
    if not validation.structural_checks.passed:
        failed.append("validation_structural_hard_gates")
    if not training.positive:
        failed.append("positive_training_checkpoint")
    if not validation.positive:
        failed.append("positive_validation_checkpoint")
    if not public_assessment.eligible:
        failed.append("public_core_eligibility")

    authorization_present = any(
        item.record_sha256 == validation_authorization.record_sha256
        and item == validation_authorization
        for item in verified_ledger.probe_authorizations
    )
    if not authorization_present:
        failed.append("validation_probe_authorization")
    elif (
        validation_authorization.team_id != validation.identity.team_id
        or validation_authorization.candidate_identity_sha256 != validation.identity.sha256
    ):
        failed.append("validation_probe_identity_binding")
    if prior_formal_submission_count != 0:
        failed.append("one_formal_nomination")
    return NominationDecision(allowed=not failed, failed_requirements=tuple(failed))
