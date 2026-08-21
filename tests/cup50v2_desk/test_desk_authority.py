"""Desk identity is data, and the desk must not be able to replay something it was not given.

CUP-50's desk hard-coded its winner in module constants, which is correct for one desk and
impossible for four. The risk introduced by making it data is that a desk could now be pointed at
the wrong lane, or at the right lane with the wrong centre, by editing a JSON file. These tests
pin the checks that make that fail loudly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from crypto_trade.cup50v2_desk.authority import (
    DeploymentChangedError,
    Desk,
    desk_bundle,
    load_desk,
    paper_root,
)

DIGEST = "a" * 64


def _desk(**overrides) -> dict[str, object]:
    payload = {
        "schema_version": 1,
        "desk_id": "winner",
        "team_id": "team-07",
        "candidate_id": "flow-neutral-001",
        "centre": {"blend_decay": 0.09, "trade_band": 0.12},
        "nomination_sha256": DIGEST,
    }
    payload.update(overrides)
    return payload


def _write(root: Path, payload: dict[str, object]) -> Path:
    directory = root / "paper-cup50v2" / str(payload["desk_id"])
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "desk.json").write_text(json.dumps(payload))
    return root


def test_a_desk_is_read_from_its_own_directory(tmp_path: Path) -> None:
    _write(tmp_path, _desk())
    desk = load_desk("winner", tmp_path)
    assert desk.team_id == "team-07"
    assert desk.candidate_id == "flow-neutral-001"
    assert desk.centre == {"blend_decay": 0.09, "trade_band": 0.12}


def test_four_desks_coexist_without_colliding(tmp_path: Path) -> None:
    """The property the whole final stage rests on."""
    for desk_id, team in (
        ("winner", "team-07"),
        ("runner-up-1", "team-06"),
        ("runner-up-2", "team-11"),
        ("ensemble-eq3", "ensemble-eq3"),
    ):
        _write(tmp_path, _desk(desk_id=desk_id, team_id=team))
    desks = [load_desk(name, tmp_path) for name in
             ("winner", "runner-up-1", "runner-up-2", "ensemble-eq3")]
    assert len({d.desk_id for d in desks}) == 4
    assert len({paper_root(d, tmp_path) for d in desks}) == 4, "desks must not share a paper root"
    assert paper_root(desks[0], tmp_path).name == "winner"
    assert desk_bundle(desks[0], tmp_path).name == "team-07"


def test_an_unknown_schema_is_refused(tmp_path: Path) -> None:
    _write(tmp_path, _desk(schema_version=2))
    with pytest.raises(DeploymentChangedError, match="unknown CUP-50 v2 desk schema"):
        load_desk("winner", tmp_path)


@pytest.mark.parametrize("desk_id", ["../escape", "a/b", ""])
def test_a_desk_id_cannot_escape_its_directory(tmp_path: Path, desk_id: str) -> None:
    """desk_id becomes a path segment, so it is the one field that must not be trusted."""
    with pytest.raises(ValueError, match="unsafe desk id"):
        load_desk(desk_id, tmp_path)


def test_a_desk_must_name_the_centre_it_replays(tmp_path: Path) -> None:
    """An empty centre would silently replay the strategy at its source defaults.

    That is the failure this desk design most needs to exclude: it looks like a working desk, ticks
    cleanly, publishes a record, and is not the frozen candidate the tournament ranked.
    """
    with pytest.raises(ValueError, match="must name the centre"):
        Desk(
            desk_id="winner",
            team_id="team-07",
            candidate_id="flow-neutral-001",
            centre={},
            nomination_sha256=DIGEST,
        )


def test_a_desk_must_carry_a_real_nomination_digest() -> None:
    with pytest.raises(ValueError, match="must be a SHA-256"):
        Desk(
            desk_id="winner",
            team_id="team-07",
            candidate_id="flow-neutral-001",
            centre={"blend_decay": 0.09},
            nomination_sha256="short",
        )


def test_a_desk_is_frozen() -> None:
    """Nothing may repoint a live desk at another lane mid-run."""
    import dataclasses

    desk = Desk(
        desk_id="winner",
        team_id="team-07",
        candidate_id="flow-neutral-001",
        centre={"blend_decay": 0.09},
        nomination_sha256=DIGEST,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        desk.team_id = "team-06"


def _lineage_fixture(tmp_path: Path, *, nomination_centre: dict, desk_centre: dict,
                     nomination_digest: str = DIGEST) -> tuple[Path, Desk]:
    """Everything verify_lineage reads, with verify_desk_authority stubbed by the caller."""
    (tmp_path / "reports-cup50v2").mkdir(parents=True, exist_ok=True)
    (tmp_path / "reports-cup50v2" / "leaderboard.json").write_text(
        json.dumps({"entries": [{"team_id": "team-07"}, {"team_id": "team-06"}]})
    )
    config_dir = tmp_path / "tournament" / "cup50v2"
    config_dir.mkdir(parents=True, exist_ok=True)
    source = Path("tournament/cup50v2/config.toml").read_text()
    (config_dir / "config.toml").write_text(source)
    (config_dir / "nominations").mkdir(parents=True, exist_ok=True)
    (config_dir / "nominations" / "team-07.json").write_text(
        json.dumps({"freeze_sha256": nomination_digest, "centre": nomination_centre})
    )
    desk = Desk(
        desk_id="winner",
        team_id="team-07",
        candidate_id="flow-neutral-001",
        centre=desk_centre,
        nomination_sha256=DIGEST,
    )
    paper = tmp_path / "paper-cup50v2" / "winner"
    paper.mkdir(parents=True, exist_ok=True)
    (paper / "reconstruction.json").write_text(
        json.dumps({"parity": True, "team_id": "team-07", "lineage_sha256": "l" * 64})
    )
    return tmp_path, desk


def _stub_authority(monkeypatch, *, nomination_sha256: str = DIGEST) -> None:
    import crypto_trade.cup50v2_desk.authority as module

    monkeypatch.setattr(
        module,
        "verify_desk_authority",
        lambda *args, **kwargs: {
            "public_data_only": True,
            "nomination_sha256": nomination_sha256,
            "lineage_sha256": "l" * 64,
            "launch_time": "2026-08-22T00:00:00+00:00",
        },
    )


def test_a_matching_centre_passes(tmp_path: Path, monkeypatch) -> None:
    from crypto_trade.cup50v2_desk.authority import verify_lineage

    centre = {"blend_decay": 0.09, "trade_band": 0.12}
    root, desk = _lineage_fixture(tmp_path, nomination_centre=centre, desk_centre=dict(centre))
    _stub_authority(monkeypatch)
    assert verify_lineage(desk, root)["nomination"]["freeze_sha256"] == DIGEST


def test_a_desk_cannot_replay_a_lane_at_a_centre_it_never_froze(
    tmp_path: Path, monkeypatch
) -> None:
    """The failure that would otherwise be invisible.

    A desk pointed at the right lane with a nudged parameter ticks cleanly, publishes a record, and
    is not the candidate the tournament ranked. Nothing downstream would notice: the bundle digest
    matches, the lane matches, only the number differs.
    """
    from crypto_trade.cup50v2_desk.authority import verify_lineage

    root, desk = _lineage_fixture(
        tmp_path,
        nomination_centre={"blend_decay": 0.09, "trade_band": 0.12},
        desk_centre={"blend_decay": 0.09, "trade_band": 0.13},   # one digit
    )
    _stub_authority(monkeypatch)
    with pytest.raises(DeploymentChangedError, match="centre parameters drifted"):
        verify_lineage(desk, root)


def test_a_desk_bound_to_another_lanes_nomination_is_refused(
    tmp_path: Path, monkeypatch
) -> None:
    from crypto_trade.cup50v2_desk.authority import verify_lineage

    centre = {"blend_decay": 0.09}
    root, desk = _lineage_fixture(
        tmp_path, nomination_centre=centre, desk_centre=dict(centre), nomination_digest="b" * 64
    )
    _stub_authority(monkeypatch, nomination_sha256="b" * 64)
    with pytest.raises(DeploymentChangedError, match="binds a nomination the lane did not freeze"):
        verify_lineage(desk, root)


def test_a_desk_whose_lane_is_not_in_the_release_is_refused(
    tmp_path: Path, monkeypatch
) -> None:
    from crypto_trade.cup50v2_desk.authority import verify_lineage

    centre = {"blend_decay": 0.09}
    root, desk = _lineage_fixture(tmp_path, nomination_centre=centre, desk_centre=dict(centre))
    (root / "reports-cup50v2" / "leaderboard.json").write_text(
        json.dumps({"entries": [{"team_id": "team-06"}]})
    )
    _stub_authority(monkeypatch)
    with pytest.raises(DeploymentChangedError, match="does not rank team-07"):
        verify_lineage(desk, root)
