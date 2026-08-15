"""The desk's deployment authority is what refuses to run a changed deployment -- test it like one.

Every one of the six digests must be provably capable of detecting its own change, and the
cross-check against the recorded selection freeze must fire when the winner's bytes and the freeze
disagree. Mutations are built by constructing a ``DeskAuthority`` with one field altered, or by
doctoring a COPY of the repository in ``tmp_path`` -- never by editing the hash-bound tree, which
``tournament/cup20/activation-freeze.json`` binds byte for byte.
"""

import dataclasses
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from crypto_trade.cup20.activation import verify_activation
from crypto_trade.cup20_desk.authority import (
    AUTHORITY_FIELDS,
    WINNER_CANDIDATE_ID,
    WINNER_TEAM_ID,
    DeploymentChangedError,
    DeskAuthority,
    current_desk_authority,
    verify_desk_authority,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SELECTION_FREEZE = REPO_ROOT / "tournament" / "cup20" / "selection-freeze.json"
ACTIVATION_FREEZE = REPO_ROOT / "tournament" / "cup20" / "activation-freeze.json"

# A syntactically valid digest that is not any real one, so a mutated field is rejected for
# disagreeing rather than for being malformed.
OTHER_DIGEST = "f" * 64

# Each recorded finalist digest paired with the desk field it must agree with.
FREEZE_CROSS_CHECKS: tuple[tuple[str, str], ...] = (
    ("source_sha256", "strategy_sha256"),
    ("risk_policy_sha256", "risk_policy_sha256"),
    ("neighbourhood_sha256", "neighbourhood_sha256"),
)


def _finalist(payload: dict) -> dict:
    for entry in payload["finalists"]:
        if entry["team_id"] == WINNER_TEAM_ID and entry["candidate_id"] == WINNER_CANDIDATE_ID:
            return entry
    raise AssertionError(f"{WINNER_TEAM_ID}/{WINNER_CANDIDATE_ID} is not a recorded finalist")


def _mirror_repository(destination: Path) -> Path:
    """A copy of exactly the paths the authority reads, so a test can doctor one of them."""
    (destination / "tournament" / "cup20").mkdir(parents=True)
    (destination / "src" / "crypto_trade").mkdir(parents=True)
    for name in ("config.toml", "selection-freeze.json", "activation-freeze.json"):
        shutil.copy2(
            REPO_ROOT / "tournament" / "cup20" / name,
            destination / "tournament" / "cup20" / name,
        )
    shutil.copytree(
        REPO_ROOT / "tournament" / "cup20" / "teams" / WINNER_TEAM_ID,
        destination / "tournament" / "cup20" / "teams" / WINNER_TEAM_ID,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copytree(
        REPO_ROOT / "src" / "crypto_trade" / "cup20",
        destination / "src" / "crypto_trade" / "cup20",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    return destination


def test_authority_fields_are_the_six_the_desk_pins():
    assert AUTHORITY_FIELDS == (
        "strategy_sha256",
        "risk_policy_sha256",
        "neighbourhood_sha256",
        "config_sha256",
        "selection_freeze_sha256",
        "evaluator_sha256",
    )
    assert tuple(field.name for field in dataclasses.fields(DeskAuthority)) == AUTHORITY_FIELDS


def test_authority_verifies_against_the_real_repository():
    authority = current_desk_authority()
    assert verify_desk_authority(authority) == authority


def test_authority_digests_match_the_recorded_freezes():
    authority = current_desk_authority()
    finalist = _finalist(json.loads(SELECTION_FREEZE.read_text()))
    for recorded, field in FREEZE_CROSS_CHECKS:
        assert getattr(authority, field) == finalist[recorded]
    activation = json.loads(ACTIVATION_FREEZE.read_text())
    assert authority.evaluator_sha256 == activation["implementation_sha256"]
    assert authority.config_sha256 == activation["config_sha256"]
    assert (
        authority.selection_freeze_sha256
        == hashlib.sha256(SELECTION_FREEZE.read_bytes()).hexdigest()
    )


@pytest.mark.parametrize("field", AUTHORITY_FIELDS)
def test_each_digest_independently_detects_a_change(field):
    expected = dataclasses.replace(current_desk_authority(), **{field: OTHER_DIGEST})
    with pytest.raises(DeploymentChangedError) as error:
        verify_desk_authority(expected)
    assert field in str(error.value)
    assert OTHER_DIGEST in str(error.value)


@pytest.mark.parametrize("field", AUTHORITY_FIELDS)
def test_a_changed_digest_is_named_alone(field):
    """Naming every field on any drift would make the message useless for attribution."""
    expected = dataclasses.replace(current_desk_authority(), **{field: OTHER_DIGEST})
    with pytest.raises(DeploymentChangedError) as error:
        verify_desk_authority(expected)
    named = [other for other in AUTHORITY_FIELDS if other in str(error.value)]
    assert named == [field]


def test_mirrored_repository_reproduces_the_real_authority(tmp_path):
    """Without this, a doctored-mirror test could pass for the wrong reason."""
    mirror = _mirror_repository(tmp_path / "mirror")
    assert current_desk_authority(mirror) == current_desk_authority()


@pytest.mark.parametrize(("recorded", "field"), FREEZE_CROSS_CHECKS)
def test_selection_freeze_cross_check_fires(tmp_path, recorded, field):
    mirror = _mirror_repository(tmp_path / "mirror")
    freeze_path = mirror / "tournament" / "cup20" / "selection-freeze.json"
    payload = json.loads(freeze_path.read_text())
    _finalist(payload)[recorded] = OTHER_DIGEST
    freeze_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with pytest.raises(DeploymentChangedError) as error:
        current_desk_authority(mirror)
    assert recorded in str(error.value)
    assert field in str(error.value)
    assert "selection-freeze" in str(error.value)


def test_evaluator_cross_check_fires_against_the_activation_freeze(tmp_path):
    mirror = _mirror_repository(tmp_path / "mirror")
    freeze_path = mirror / "tournament" / "cup20" / "activation-freeze.json"
    payload = json.loads(freeze_path.read_text())
    payload["implementation_sha256"] = OTHER_DIGEST
    freeze_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with pytest.raises(DeploymentChangedError) as error:
        current_desk_authority(mirror)
    assert "evaluator_sha256" in str(error.value)
    assert "implementation_sha256" in str(error.value)


def test_missing_winner_candidate_is_refused(tmp_path):
    mirror = _mirror_repository(tmp_path / "mirror")
    shutil.rmtree(
        mirror
        / "tournament"
        / "cup20"
        / "teams"
        / WINNER_TEAM_ID
        / "candidates"
        / WINNER_CANDIDATE_ID
    )
    with pytest.raises(FileNotFoundError):
        current_desk_authority(mirror)


def test_json_round_trip():
    authority = current_desk_authority()
    assert DeskAuthority.from_json(authority.to_json()) == authority


def test_serialised_authority_is_readable_json():
    payload = json.loads(current_desk_authority().to_json())
    assert set(payload) >= set(AUTHORITY_FIELDS)
    for field in AUTHORITY_FIELDS:
        assert payload[field] == getattr(current_desk_authority(), field)


def test_deserialising_refuses_a_missing_field():
    payload = json.loads(current_desk_authority().to_json())
    del payload["evaluator_sha256"]
    with pytest.raises(ValueError, match="evaluator_sha256"):
        DeskAuthority.from_json(json.dumps(payload))


def test_deserialising_refuses_a_non_digest():
    payload = json.loads(current_desk_authority().to_json())
    payload["config_sha256"] = "not-a-digest"
    with pytest.raises(ValueError, match="config_sha256"):
        DeskAuthority.from_json(json.dumps(payload))


def test_activation_freeze_still_verifies(monkeypatch):
    """The desk may not disturb one byte of what the tournament hash-bound."""
    # The record stores its authority paths relative to the repository root, so it can only be
    # verified from there.
    monkeypatch.chdir(REPO_ROOT)
    verify_activation("tournament/cup20/activation-freeze.json")
