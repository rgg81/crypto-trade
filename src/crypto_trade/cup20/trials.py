"""Material trials: what identifies one, what a team spends, and the organiser-owned append.

Charter section 7.1. A trial is journaled **before** market data are opened, and acceptance
consumes it whether or not the run that follows ever completes. This module is the organiser-owned
path the playbook refers to when it says a team "requests an append" -- teams never write
``research-journal.jsonl`` themselves, they call :func:`record_trial`, which is the only function
in the repository that appends a ``trial_accepted`` record.

Three things live here and nowhere else:

* **the material tuple**, as a value object (:class:`MaterialTrial`). Section 7.1 defines a
  material trial as one whose tuple of (source bytes, config, feature set, seed, parameters,
  window, cost model, risk policy) differs from an earlier one. Every one of those is a field
  below, and :meth:`MaterialTrial.material` returns exactly that tuple as JSON-safe values so it
  survives a round trip through the journal and can be compared field by field afterwards.
* **the budget**, enforced at the append rather than at nomination. Twelve accepted trials per
  team; the thirteenth is refused by name and count. Refusing late -- at the certificate -- would
  mean a team discovers the wall after it has already spent the work.
* **the lock**. Phase 1 runs twelve teams in parallel against ONE journal file. Two unsynchronised
  appends read the same head, write the same ``previous_sha256`` and produce two records claiming
  the same sequence number, which ``verify_chain`` then reports as a corrupt chain that nobody
  actually corrupted. :func:`record_trial` therefore holds an exclusive lock across read-count,
  read-head and append.

Why the source digest is a digest of the candidate DIRECTORY and not of ``strategy.py`` alone:
``risk_policy.json`` and ``neighbourhood.json`` are as material as the code -- a different declared
policy is a different evaluation of the same code -- and a team that split its mechanism across a
helper module beside ``strategy.py`` would otherwise change its behaviour without changing its
recorded identity. ``bundle_digest`` covers file names and bytes, excludes symlinks (which the
blindness scan reports separately) and excludes ``__pycache__`` (derived, and its presence must not
make an unchanged candidate look changed).
"""

from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import json
import os
import time
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

from crypto_trade.cup20.archive import bundle_digest
from crypto_trade.cup20.config import TEAM_IDS
from crypto_trade.cup20.journal import accepted_trial_count, append_record, read_records

TRIAL_ACCEPTED_EVENT = "trial_accepted"
"""The one journal event type that consumes a trial. Nothing else counts against the budget."""

TRIAL_KINDS: tuple[str, ...] = ("point", "neighbourhood", "falsification")
"""The three shapes section 7.1 recognises.

``point`` is an ordinary evaluation of one frozen candidate state. ``neighbourhood`` is the
declared sweep, which is one trial however many points it contains. ``falsification`` is the
battery (exact sign inversion + gross-edge placebo), one trial for the same reason. The kind is
part of the material tuple so that the harness can refuse to run a falsification battery against a
trial journaled as an ordinary point -- otherwise a team would get the battery for free off a
trial it had already spent on something else.
"""

RECOGNISED_ROLES: tuple[str, ...] = ("long", "short")
"""The only role names ``qualification.evaluate_floors`` knows. Validated here so a typo fails at
journal time with a readable message rather than as a bare ``KeyError`` from inside the floors."""

MATERIAL_FIELDS: tuple[str, ...] = (
    "kind",
    "source_sha256",
    "config_sha256",
    "risk_policy_sha256",
    "snapshot_sha256",
    "seed",
    "window",
    "cost_model",
    "parameters",
    "declared_roles",
)
"""Exactly what makes two trials the same trial. Compared field by field, never by a stored
fingerprint: the fingerprint is a convenience for humans reading the journal, and a value a team
could in principle write is not evidence about the value it describes."""

ENTRYPOINT = "strategy.py"
RISK_POLICY_FILENAME = "risk_policy.json"

_HEX_DIGITS = frozenset("0123456789abcdef")
_LOCK_TIMEOUT_SECONDS = 60.0
_LOCK_POLL_SECONDS = 0.05


class TrialBudgetExhaustedError(RuntimeError):
    """The team has already spent every material trial the config allows."""


class JournalBusyError(RuntimeError):
    """Another append is in flight, or a previous one died holding the lock."""


def _canonical(payload: Mapping[str, Any]) -> str:
    """Byte-stable JSON. ``allow_nan=False`` so a non-finite parameter cannot enter the chain as
    the non-standard ``NaN`` token, which would make the record unparseable by a strict reader."""
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def _require_digest(value: str, label: str) -> str:
    if len(value) != 64 or not set(value) <= _HEX_DIGITS:
        raise ValueError(f"{label} must be a SHA-256 digest, got {value!r}")
    return value


def candidate_source_digest(candidate_root: str | Path) -> str:
    """The candidate's source bytes, as one digest over the whole candidate directory.

    Fails closed on a missing directory and on a directory with no ``strategy.py``. Both matter:
    ``bundle_digest`` of an empty or absent tree is ``sha256("")``, a perfectly stable value that
    would journal cleanly and then match every other empty candidate in the tournament.
    """
    root = Path(candidate_root)
    if not root.is_dir():
        raise FileNotFoundError(f"candidate directory does not exist: {root}")
    if not (root / ENTRYPOINT).is_file():
        raise FileNotFoundError(
            f"{root / ENTRYPOINT} is missing; a candidate is identified by its source bytes and "
            f"{ENTRYPOINT} is the entrypoint the evaluator loads"
        )
    return bundle_digest(root)


def risk_policy_digest(candidate_root: str | Path) -> str:
    """The declared risk policy's digest.

    Required, not optional. The policy is a named component of the material tuple, so a candidate
    evaluated without one has an undeclared component -- and "no policy" and "a policy that
    declares nothing" are different claims that must not share an identity.
    """
    path = Path(candidate_root) / RISK_POLICY_FILENAME
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} is missing; the declared risk policy is part of the material tuple and every "
            "frozen candidate carries one (charter section 11)"
        )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cost_model(execution: Mapping[str, Any]) -> dict[str, Any]:
    """The cost model as the journal records it, read out of the frozen ``[execution]`` table.

    Recorded explicitly as well as implied by ``config_sha256`` because a reader of the journal
    should be able to see what a trial was costed at without resolving a hash against a config
    revision, and because the charter names the cost model as its own element of the tuple.
    """
    return {
        "taker_fee_bps_per_side": float(execution["taker_fee_bps_per_side"]),
        "slippage_bps_per_side": float(execution["slippage_bps_per_side"]),
        "cost_multipliers": [int(value) for value in execution["cost_multipliers"]],
    }


@dataclasses.dataclass(frozen=True, slots=True)
class MaterialTrial:
    """One material trial's complete identity, before any number exists."""

    team_id: str
    candidate_id: str
    purpose: str
    kind: str
    source_sha256: str
    config_sha256: str
    risk_policy_sha256: str
    snapshot_sha256: str
    seed: int
    window_start: str
    window_end: str
    cost_model: Mapping[str, Any]
    parameters: Mapping[str, Any]
    declared_roles: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.team_id not in TEAM_IDS:
            raise ValueError(
                f"unknown team {self.team_id!r}; the roster is {list(TEAM_IDS)}. The trial budget "
                "is counted per team id, so an id outside the roster would spend nobody's budget."
            )
        if not self.candidate_id.strip():
            raise ValueError("candidate_id must not be blank")
        if not self.purpose.strip():
            raise ValueError(
                "purpose must not be blank; the journal is the research record and a trial with no "
                "stated question is not one"
            )
        if self.kind not in TRIAL_KINDS:
            raise ValueError(f"kind must be one of {list(TRIAL_KINDS)}, got {self.kind!r}")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise ValueError(f"seed must be an integer, got {self.seed!r}")
        for label, digest in (
            ("source_sha256", self.source_sha256),
            ("config_sha256", self.config_sha256),
            ("risk_policy_sha256", self.risk_policy_sha256),
            ("snapshot_sha256", self.snapshot_sha256),
        ):
            _require_digest(digest, label)
        if not self.declared_roles:
            raise ValueError(
                "declared_roles must name at least one of "
                f"{list(RECOGNISED_ROLES)}; the roles floor is checked against the sides the book "
                "actually traded, and a claim has to exist before it can be checked"
            )
        if len(set(self.declared_roles)) != len(self.declared_roles):
            raise ValueError(f"declared_roles contains duplicates: {list(self.declared_roles)}")
        unknown = [role for role in self.declared_roles if role not in RECOGNISED_ROLES]
        if unknown:
            raise ValueError(
                f"unrecognised declared role(s) {unknown}; the floors know only "
                f"{list(RECOGNISED_ROLES)}"
            )
        # Round-trips through the journal as JSON, so it has to BE JSON now -- a non-serialisable
        # or non-finite parameter must fail here, naming the trial, rather than at append time
        # naming a dict.
        _canonical(dict(self.parameters))

    def material(self) -> dict[str, Any]:
        """The tuple that decides whether two trials are the same trial, as JSON-safe values."""
        return {
            "kind": self.kind,
            "source_sha256": self.source_sha256,
            "config_sha256": self.config_sha256,
            "risk_policy_sha256": self.risk_policy_sha256,
            "snapshot_sha256": self.snapshot_sha256,
            "seed": int(self.seed),
            "window": {"start": self.window_start, "end": self.window_end},
            "cost_model": dict(self.cost_model),
            "parameters": dict(self.parameters),
            "declared_roles": list(self.declared_roles),
        }

    def fingerprint(self) -> str:
        """A digest of :meth:`material`, for humans reading the journal. Never the comparison."""
        return hashlib.sha256(_canonical(self.material()).encode("utf-8")).hexdigest()

    def payload(self) -> dict[str, Any]:
        """The journal payload: identity, purpose, and the material tuple flattened alongside."""
        return {
            "team_id": self.team_id,
            "candidate_id": self.candidate_id,
            "purpose": self.purpose,
            "fingerprint": self.fingerprint(),
            **self.material(),
        }


@dataclasses.dataclass(frozen=True, slots=True)
class AcceptedTrial:
    """What a team gets back when an append succeeds."""

    sequence: int
    record_sha256: str
    team_id: str
    spent: int
    budget: int

    @property
    def remaining(self) -> int:
        return self.budget - self.spent


@contextlib.contextmanager
def journal_lock(
    journal_path: str | Path,
    *,
    timeout_seconds: float = _LOCK_TIMEOUT_SECONDS,
    poll_seconds: float = _LOCK_POLL_SECONDS,
) -> Iterator[Path]:
    """Hold an exclusive lock beside the journal for the whole read-then-append.

    ``O_CREAT | O_EXCL`` is the primitive: the create either wins or raises, with no window
    between checking and taking. A stale lock (a previous append killed mid-flight) blocks until
    the timeout and then raises rather than being broken automatically -- the failure mode of
    breaking a lock that is actually held is a silently corrupted chain, and the failure mode of
    refusing is a message telling an organiser to delete one file.
    """
    lock = Path(str(journal_path) + ".lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise JournalBusyError(
                    f"{lock} is held after {timeout_seconds:.0f}s. Another append is in flight, or "
                    "one died holding it. If no other run is active, delete that file."
                ) from None
            time.sleep(poll_seconds)
            continue
        break
    try:
        os.write(handle, f"{os.getpid()}\n".encode("ascii"))
        os.close(handle)
        yield lock
    finally:
        lock.unlink(missing_ok=True)


def _is_trial_record(record: Mapping[str, Any], team_id: str) -> bool:
    """The same predicate ``journal.accepted_trial_count`` counts with, to the letter.

    Deliberately duplicated rather than shared: if the lookup and the counter could ever disagree
    about which records are trials, a team could be told it has spent eleven while the harness
    finds a twelfth to run against. A test asserts the two agree on a journal containing malformed
    records, which is the only place they could plausibly drift.
    """
    return (
        record.get("event_type") == TRIAL_ACCEPTED_EVENT
        and isinstance(record.get("payload"), Mapping)
        and record.get("payload", {}).get("team_id") == team_id
    )


def accepted_trials(journal_path: str | Path, team_id: str) -> tuple[dict[str, Any], ...]:
    """Every accepted trial record for one team, in journal order."""
    return tuple(
        record for record in read_records(journal_path) if _is_trial_record(record, team_id)
    )


def record_trial(
    journal_path: str | Path,
    trial: MaterialTrial,
    *,
    budget: int,
    lock_timeout_seconds: float = _LOCK_TIMEOUT_SECONDS,
) -> AcceptedTrial:
    """Append one accepted trial, refusing the one past the budget.

    The whole read-count / read-head / append sequence happens under :func:`journal_lock`, so a
    second team appending at the same moment cannot see the same head or be told the same
    remaining count.
    """
    limit = int(budget)
    if limit < 1:
        raise ValueError(f"trial budget must be at least 1, got {budget!r}")
    with journal_lock(journal_path, timeout_seconds=lock_timeout_seconds):
        spent = accepted_trial_count(journal_path, trial.team_id)
        if spent >= limit:
            raise TrialBudgetExhaustedError(
                f"{trial.team_id} has spent all {limit} material trials ({spent} accepted); this "
                f"would be trial {spent + 1} and is refused. The budget is not extendable, and a "
                "negative result written up honestly is a legitimate and respectable outcome."
            )
        sequence = len(read_records(journal_path)) + 1
        digest = append_record(journal_path, TRIAL_ACCEPTED_EVENT, trial.payload())
    return AcceptedTrial(
        sequence=sequence,
        record_sha256=digest,
        team_id=trial.team_id,
        spent=spent + 1,
        budget=limit,
    )


def _recorded_material(record: Mapping[str, Any]) -> dict[str, Any]:
    payload = record.get("payload")
    if not isinstance(payload, Mapping):
        return {}
    return {field: payload.get(field) for field in MATERIAL_FIELDS}


def matching_trials(
    records: Sequence[Mapping[str, Any]], trial: MaterialTrial
) -> tuple[dict[str, Any], ...]:
    """Every accepted record whose material tuple equals this one's, field by field."""
    wanted = trial.material()
    return tuple(dict(record) for record in records if _recorded_material(record) == wanted)


def describe_difference(record: Mapping[str, Any], trial: MaterialTrial) -> tuple[str, ...]:
    """Which material fields differ between a journaled trial and this candidate state.

    This is the coaching half of the refusal. "No accepted trial for this candidate" is true but
    useless; "the source bytes differ" tells a team it edited its strategy after journaling, and
    "the seed differs" tells it that it did not.
    """
    recorded = _recorded_material(record)
    wanted = trial.material()
    return tuple(
        f"{field}: journaled {recorded.get(field)!r}, this run {wanted[field]!r}"
        for field in MATERIAL_FIELDS
        if recorded.get(field) != wanted[field]
    )


class TrialNotAcceptedError(RuntimeError):
    """No accepted trial covers exactly this candidate state, so nothing may be evaluated."""


@dataclasses.dataclass(frozen=True, slots=True)
class TrialResolution:
    """The accepted trial an evaluation is running under, and the identity it licences."""

    sequence: int
    record: Mapping[str, Any]
    trial: MaterialTrial


def _rebuild(record: Mapping[str, Any], recomputed: Mapping[str, Any]) -> MaterialTrial | None:
    """The journaled trial's declaration, re-stated against today's recomputed authorities.

    Seed, roles, parameters and purpose come from the RECORD -- they are the team's declaration and
    are not recoverable from the filesystem. Everything else comes from ``recomputed``. Comparing
    the two therefore answers exactly the right question: given what this team declared, does the
    candidate on disk right now still hash to what it journaled, against the config, snapshot,
    window and cost model in force right now?

    Returns ``None`` for a record this module cannot turn back into a valid declaration -- a
    hand-edited role name, a missing seed. Such a record can never match, and skipping it is safer
    than raising: one malformed record elsewhere in a shared journal must not deny an evaluation
    that has a perfectly good trial two lines further down.
    """
    payload = record.get("payload")
    if not isinstance(payload, Mapping):
        return None
    roles = payload.get("declared_roles")
    if not isinstance(roles, Sequence) or isinstance(roles, (str, bytes)):
        return None
    parameters = payload.get("parameters")
    if not isinstance(parameters, Mapping):
        return None
    try:
        return MaterialTrial(
            team_id=str(payload.get("team_id")),
            candidate_id=str(payload.get("candidate_id")),
            purpose=str(payload.get("purpose")),
            kind=str(recomputed["kind"]),
            source_sha256=str(recomputed["source_sha256"]),
            config_sha256=str(recomputed["config_sha256"]),
            risk_policy_sha256=str(recomputed["risk_policy_sha256"]),
            snapshot_sha256=str(recomputed["snapshot_sha256"]),
            seed=payload.get("seed"),  # type: ignore[arg-type]
            window_start=str(recomputed["window_start"]),
            window_end=str(recomputed["window_end"]),
            cost_model=dict(recomputed["cost_model"]),
            parameters=dict(parameters),
            declared_roles=tuple(str(role) for role in roles),
        )
    except (ValueError, TypeError):
        return None


def resolve_accepted_trial(
    journal_path: str | Path,
    *,
    team_id: str,
    candidate_id: str,
    recomputed: Mapping[str, Any],
    pinned_sequence: int | None = None,
) -> TrialResolution:
    """Find the accepted trial that licences evaluating this exact candidate state, or refuse.

    This is what makes "journaled before you look at a number" real rather than aspirational: with
    no matching trial there is no evaluation, and with a *different* source digest there is no
    evaluation either, because editing the strategy after journaling produces a different material
    trial that has not been accepted.

    The most recent match wins. A team that journals the same state twice has spent two trials and
    may run either; citing the later one in the certificate is the honest reading.
    """
    kind = str(recomputed["kind"])
    records = accepted_trials(journal_path, team_id)
    for_candidate = [
        record
        for record in records
        if isinstance(record.get("payload"), Mapping)
        and record["payload"].get("candidate_id") == candidate_id
    ]
    if pinned_sequence is not None:
        for_candidate = [
            record for record in for_candidate if record.get("sequence") == pinned_sequence
        ]
        if not for_candidate:
            raise TrialNotAcceptedError(
                f"journal sequence #{pinned_sequence} is not an accepted trial for "
                f"{team_id}/{candidate_id}"
            )
    of_kind = [record for record in for_candidate if record["payload"].get("kind") == kind]
    for record in reversed(of_kind):
        rebuilt = _rebuild(record, recomputed)
        if rebuilt is not None and not describe_difference(record, rebuilt):
            return TrialResolution(sequence=int(record["sequence"]), record=record, trial=rebuilt)

    if not for_candidate:
        raise TrialNotAcceptedError(
            f"{team_id} has no accepted trial for candidate {candidate_id!r}. Journal one first:\n"
            f"  uv run python scripts/cup20_trial.py --team {team_id} --candidate {candidate_id} "
            f'--kind {kind} --purpose "..." --seed <int> --roles long,short'
        )
    if not of_kind:
        kinds = sorted({str(record["payload"].get("kind")) for record in for_candidate})
        raise TrialNotAcceptedError(
            f"{team_id}/{candidate_id} has accepted trials of kind {kinds}, but none of kind "
            f"{kind!r}. Each kind is its own material trial (charter section 7.1)."
        )
    latest = of_kind[-1]
    rebuilt = _rebuild(latest, recomputed)
    if rebuilt is None:
        raise TrialNotAcceptedError(
            f"journal sequence #{latest.get('sequence')} for {team_id}/{candidate_id} is not a "
            "well-formed trial declaration and cannot licence an evaluation"
        )
    differences = "\n".join(f"    {line}" for line in describe_difference(latest, rebuilt))
    raise TrialNotAcceptedError(
        f"{team_id}/{candidate_id}: the most recent accepted trial of kind {kind!r} is journal "
        f"sequence #{latest.get('sequence')}, and it does not describe this candidate state:\n"
        f"{differences}\n"
        "That is a NEW material trial (charter section 7.1: a trial is any evaluation whose tuple "
        "of source bytes, config, feature set, seed, parameters, window, cost model and risk "
        "policy differs from an earlier one). Journal it before evaluating."
    )
