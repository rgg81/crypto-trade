"""Pre-bound official trial budget and permanently non-promoteable controls."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from collections.abc import Mapping
from pathlib import Path

from crypto_trade.cup50v2.config import ResearchPolicy, active_policy
from crypto_trade.cup50v2.journal import append_record, read_records

# What a trial costs, and what it may become. A neighbourhood probe is charged because it is a
# look at the research window, but it is not promoteable: only an official trial can supply a
# centre. Controls are free because charging for honest self-examination is how a prior edition
# made its own research certificate unaffordable.
PROMOTEABLE_KINDS = frozenset({"official"})
CHARGED_KINDS = frozenset({"official", "neighbourhood"})
CONTROL_KINDS = frozenset({"ablation", "falsifier"})
KINDS = PROMOTEABLE_KINDS | CHARGED_KINDS | CONTROL_KINDS


def source_bundle_digest(path: str | Path) -> str:
    source = Path(path)
    if source.is_file():
        return hashlib.sha256(source.read_bytes()).hexdigest()
    if not source.is_dir():
        raise ValueError("trial source bundle does not exist")
    entries = [
        {
            "path": item.relative_to(source).as_posix(),
            "sha256": hashlib.sha256(item.read_bytes()).hexdigest(),
        }
        for item in sorted(candidate for candidate in source.rglob("*") if candidate.is_file())
    ]
    payload = json.dumps(entries, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


@dataclasses.dataclass(frozen=True, slots=True)
class TrialBinding:
    team_id: str
    trial_id: str
    kind: str
    promoteable: bool
    source_sha256: str
    parameters: Mapping[str, object]
    risk_policy_sha256: str
    seed: int
    data_sha256: str
    config_sha256: str
    scorer_sha256: str
    purpose: str

    def validate(self) -> None:
        if not self.team_id.startswith("team-") or not self.trial_id:
            raise ValueError("trial needs valid team_id and trial_id")
        digests = (
            self.source_sha256,
            self.risk_policy_sha256,
            self.data_sha256,
            self.config_sha256,
            self.scorer_sha256,
        )
        if any(
            len(value) != 64 or any(char not in "0123456789abcdef" for char in value)
            for value in digests
        ):
            raise ValueError("every material trial artifact must be pre-bound by lowercase SHA-256")
        if not self.purpose.strip():
            raise ValueError("trial purpose cannot be empty")
        if self.kind not in KINDS:
            raise ValueError(f"unknown trial kind: {self.kind}")
        # One rule now covers both directions: a neighbourhood probe is charged and can never be
        # promoted, and a control is uncharged and can never be promoted.
        if self.promoteable != (self.kind in PROMOTEABLE_KINDS):
            raise ValueError("only an official trial is promoteable")
        for name, value in self.parameters.items():
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError(f"trial parameter {name} is non-finite")

    @property
    def binding_sha256(self) -> str:
        payload = json.dumps(
            dataclasses.asdict(self), sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        return hashlib.sha256(payload.encode()).hexdigest()


def _trial_payloads(path: str | Path, team_id: str) -> list[Mapping[str, object]]:
    return [
        dict(record["payload"])
        for record in read_records(path)
        if record["event"] == "trial-registered"
        and isinstance(record.get("payload"), Mapping)
        and record["payload"].get("team_id") == team_id
    ]


def charged_trial_count(path: str | Path, team_id: str) -> int:
    """Trials that consume the budget: official centres and neighbourhood probes."""
    return sum(
        1 for payload in _trial_payloads(path, team_id) if payload.get("kind") in CHARGED_KINDS
    )


def completed_charged_trials(path: str | Path, team_id: str) -> int:
    """Charged trials that actually produced a terminal result."""
    registered = {
        str(payload["trial_id"])
        for payload in _trial_payloads(path, team_id)
        if payload.get("kind") in CHARGED_KINDS
    }
    return sum(
        1
        for record in read_records(path)
        if record["event"] == "trial-result"
        and record["payload"].get("team_id") == team_id
        and str(record["payload"].get("trial_id")) in registered
    )


def official_trial_count(path: str | Path, team_id: str) -> int:
    return sum(bool(payload.get("promoteable")) for payload in _trial_payloads(path, team_id))


def resolve_trial_binding(
    path: str | Path, *, team_id: str, trial_id: str, binding_sha256: str
) -> Mapping[str, object]:
    matches = [
        payload
        for payload in _trial_payloads(path, team_id)
        if payload.get("trial_id") == trial_id and payload.get("binding_sha256") == binding_sha256
    ]
    if len(matches) != 1:
        raise ValueError("evaluation does not match one preregistered trial binding")
    completed = [
        record
        for record in read_records(path)
        if record["event"] == "trial-result"
        and record["payload"].get("team_id") == team_id
        and record["payload"].get("trial_id") == trial_id
    ]
    if completed:
        raise ValueError("a preregistered trial can be evaluated only once")
    return matches[0]


def register_trial(
    path: str | Path,
    binding: TrialBinding,
    *,
    policy: ResearchPolicy | None = None,
    seed_binding: Mapping[str, object] | None = None,
) -> Mapping[str, object]:
    rules = policy if policy is not None else active_policy().research
    budget = rules.official_trial_budget
    binding.validate()
    existing = _trial_payloads(path, binding.team_id)
    if any(payload.get("trial_id") == binding.trial_id for payload in existing):
        raise ValueError(f"trial_id already exists for {binding.team_id}: {binding.trial_id}")
    charged = sum(1 for payload in existing if payload.get("kind") in CHARGED_KINDS)
    if binding.kind in CHARGED_KINDS and charged >= budget:
        raise ValueError(f"{binding.team_id} exhausted its {budget} official trials")
    if binding.kind in CHARGED_KINDS and not existing and seed_binding is not None:
        # The first thing a team spends is its own seed, unchanged. It costs one trial and buys a
        # common floor: every later result is reported as a distance from it.
        if binding.source_sha256 != seed_binding["source_sha256"] or dict(
            binding.parameters
        ) != dict(seed_binding["parameters"]):
            raise ValueError(
                f"{binding.team_id} must spend its first charged trial on the unmodified seed"
            )
    payload = {**dataclasses.asdict(binding), "binding_sha256": binding.binding_sha256}
    return append_record(path, "trial-registered", payload)


def record_trial_result(
    path: str | Path,
    *,
    team_id: str,
    trial_id: str,
    binding_sha256: str,
    source_path: str | Path,
    result_sha256: str,
    succeeded: bool,
) -> Mapping[str, object]:
    matches = [
        payload for payload in _trial_payloads(path, team_id) if payload.get("trial_id") == trial_id
    ]
    if len(matches) != 1 or matches[0].get("binding_sha256") != binding_sha256:
        raise ValueError("trial result does not match one preregistered binding")
    if any(
        record["event"] == "trial-result"
        and record["payload"].get("team_id") == team_id
        and record["payload"].get("trial_id") == trial_id
        for record in read_records(path)
    ):
        raise ValueError("trial already has a terminal result")
    source_digest = source_bundle_digest(source_path)
    if source_digest != matches[0]["source_sha256"]:
        raise ValueError("trial source mutated after preregistration")
    if len(result_sha256) != 64:
        raise ValueError("result_sha256 is invalid")
    return append_record(
        path,
        "trial-result",
        {
            "team_id": team_id,
            "trial_id": trial_id,
            "binding_sha256": binding_sha256,
            "result_sha256": result_sha256,
            "succeeded": bool(succeeded),
        },
    )


def nomination_is_promoteable(
    path: str | Path,
    team_id: str,
    trial_id: str,
    *,
    source_sha256: str | None = None,
) -> bool:
    try:
        nomination_trial_binding(
            path,
            team_id,
            trial_id,
            source_sha256=source_sha256,
        )
    except ValueError:
        return False
    return True


def nomination_trial_binding(
    path: str | Path,
    team_id: str,
    trial_id: str,
    *,
    source_sha256: str | None = None,
    minimum_trials: int = 0,
) -> Mapping[str, object]:
    """Return the one successful official binding eligible to supply a centre nomination."""
    if minimum_trials:
        completed = completed_charged_trials(path, team_id)
        if completed < minimum_trials:
            raise ValueError(
                f"{team_id} completed {completed} charged trials; {minimum_trials} are required "
                "before a nomination"
            )
    registrations = _trial_payloads(path, team_id)
    selected = [payload for payload in registrations if payload.get("trial_id") == trial_id]
    if len(selected) != 1 or selected[0].get("kind") not in PROMOTEABLE_KINDS:
        raise ValueError("trial is not one promoteable official registration")
    if source_sha256 is not None and selected[0].get("source_sha256") != source_sha256:
        raise ValueError("trial source differs from the nomination source")
    results = [
        record["payload"]
        for record in read_records(path)
        if record["event"] == "trial-result"
        and record["payload"].get("team_id") == team_id
        and record["payload"].get("trial_id") == trial_id
    ]
    if len(results) != 1 or not bool(results[0].get("succeeded")):
        raise ValueError("trial does not have one successful terminal result")
    return selected[0]
