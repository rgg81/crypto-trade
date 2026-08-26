"""The single-shot freeze, and every refusal that stands between it and a lane starting."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from crypto_trade.tournament.v5 import activation, contract, journal, lanes

REPO = Path(__file__).resolve().parents[2]
SHIPPED_CONFIG = REPO / "tournament" / "top40-v5" / "config.toml"


@pytest.fixture
def bench(tmp_path: Path):
    """A tournament root that would activate, so each test can break exactly one thing."""

    root = tmp_path / "tournament"
    (root / "teams").mkdir(parents=True)
    for lane in lanes.LANES:
        lane_root = root / "teams" / lane.team_id
        lane_root.mkdir()
        (lane_root / "TEAM-BRIEF.md").write_text(lane.brief(), encoding="utf-8")
        for name in ("SCOUTING-BRIEF.md", "RESEARCH-BRIEF.md", "ACCESS-POLICY.json"):
            (lane_root / name).write_text("{}", encoding="utf-8")

    preflight = tmp_path / "snapshot-preflight.json"
    preflight.write_text(json.dumps({"ok": True, "blocking_findings": 0}), encoding="utf-8")

    config = tmp_path / "config.toml"
    config.write_text(_calibrated_config(), encoding="utf-8")

    artifacts = {"config": config, "snapshot_preflight": preflight}
    for name in activation.REQUIRED_ARTIFACTS:
        if name in artifacts:
            continue
        path = tmp_path / f"{name}.txt"
        path.write_text(f"{name} content", encoding="utf-8")
        artifacts[name] = path

    journal_path = tmp_path / "research-journal.jsonl"
    journal.initialize(journal_path)

    return {
        "root": root,
        "artifacts": artifacts,
        "journal": journal_path,
        "freeze": tmp_path / "activation-freeze.json",
        "tmp": tmp_path,
    }


def _calibrated_config() -> str:
    """The shipped config with its placeholder tags replaced by calibrated ones.

    Built from the real file so the fixture cannot drift from the schema the contract enforces.
    """

    body = SHIPPED_CONFIG.read_text(encoding="utf-8")
    return body.replace(':placeholder"', ':0123456789abcdef"')


def _freeze(bench, **overrides):
    options = {
        "artifacts": bench["artifacts"],
        "tournament_root": bench["root"],
        "journal_path": bench["journal"],
        "destination": bench["freeze"],
    }
    options.update(overrides)
    return activation.freeze(**options)


# -- the shipped config deliberately cannot activate ---------------------------------------------


def test_the_shipped_config_has_been_calibrated():
    """The config shipped unable to activate so a calibration run had to happen first. It has.

    A config that activated on placeholders would be one nobody ever calibrated, which is why this
    test asserted the opposite until the run produced real artifact hashes for all thirty-five.
    """

    loaded = contract.load_config(SHIPPED_CONFIG)

    contract.assert_no_placeholder_provenance(loaded)
    assert loaded.counts_by_source()["calibrated"] > 0
    assert loaded.counts_by_source()["derived"] > 0


def test_activation_refuses_a_config_with_placeholder_provenance(bench):
    """The guard, exercised on an uncalibrated config rather than trusted."""

    placeholder = bench["tmp"] / "placeholder.toml"
    body = SHIPPED_CONFIG.read_text(encoding="utf-8")
    # Put the placeholders back, so this tests the guard rather than the calibrated file.
    body = re.sub(
        r'"(structural|inherited|calibrated|derived)[^"]*"', '"calibrated:placeholder"', body
    )
    placeholder.write_text(body, encoding="utf-8")
    artifacts = dict(bench["artifacts"], config=placeholder)

    with pytest.raises(contract.ContractError, match="placeholder"):
        _freeze(bench, artifacts=artifacts)

    assert not bench["freeze"].exists()


# -- a freeze that succeeds ----------------------------------------------------------------------


def test_a_complete_edition_activates_and_records_every_artifact(bench):
    frozen = _freeze(bench)

    assert set(frozen.artifacts) == set(activation.REQUIRED_ARTIFACTS)
    assert set(frozen.lane_surfaces) == {entry.team_id for entry in lanes.LANES}
    assert frozen.numeric_provenance
    assert bench["freeze"].is_file()

    records = list(journal.iter_events(bench["journal"], "tournament_activated"))
    assert len(records) == 1
    assert records[0].payload["freeze_sha256"] == frozen.sha256()


def test_activation_is_single_shot(bench):
    _freeze(bench)

    with pytest.raises(activation.ActivationError, match="single-shot"):
        _freeze(bench)


def test_validation_of_an_untouched_freeze_is_clean_and_repeatable(bench):
    _freeze(bench)

    for _ in range(2):
        findings = activation.validate(
            bench["artifacts"], tournament_root=bench["root"], freeze_path=bench["freeze"]
        )
        assert findings == []


# -- every refusal -------------------------------------------------------------------------------


def test_a_missing_required_artifact_refuses_activation(bench):
    incomplete = {
        name: path for name, path in bench["artifacts"].items() if name != "calibration_report"
    }

    with pytest.raises(activation.ActivationError, match="calibration_report"):
        _freeze(bench, artifacts=incomplete)

    assert not bench["freeze"].exists()


def test_a_blocking_preflight_finding_refuses_activation(bench):
    """Every decision boundary must be executable before a lane starts.

    CUP-20 passed 862 tests and still had 21 boundaries that would have crashed every team.
    """

    bench["artifacts"]["snapshot_preflight"].write_text(
        json.dumps({"ok": False, "blocking_findings": 3}), encoding="utf-8"
    )

    with pytest.raises(activation.ActivationError, match="blocking finding"):
        _freeze(bench)


def test_a_lane_brief_that_drifted_from_the_roster_refuses_activation(bench):
    """A mandate that no longer matches the code measures something other than what it says."""

    drifted = bench["root"] / "teams" / "team-06" / "TEAM-BRIEF.md"
    drifted.write_text("# team-06 — actually do whatever you like\n", encoding="utf-8")

    with pytest.raises(activation.ActivationError, match="differs from the roster"):
        _freeze(bench)


def test_a_missing_lane_file_refuses_activation(bench):
    (bench["root"] / "teams" / "team-09" / "ACCESS-POLICY.json").unlink()

    with pytest.raises(activation.ActivationError, match="ACCESS-POLICY"):
        _freeze(bench)


def test_a_lane_that_was_never_scaffolded_refuses_activation(bench):
    import shutil

    shutil.rmtree(bench["root"] / "teams" / "team-12")

    with pytest.raises(activation.ActivationError, match="TEAM-BRIEF"):
        _freeze(bench)


def test_nothing_is_written_when_activation_is_refused(bench):
    """A partial freeze left behind is one a later run could mistake for a real one."""

    bench["artifacts"]["snapshot_preflight"].write_text(
        json.dumps({"ok": False, "blocking_findings": 1}), encoding="utf-8"
    )

    with pytest.raises(activation.ActivationError):
        _freeze(bench)

    assert not bench["freeze"].exists()
    assert list(journal.iter_events(bench["journal"], "tournament_activated")) == []


# -- detecting change after the fact -------------------------------------------------------------


def test_a_changed_artifact_is_detected(bench):
    _freeze(bench)
    bench["artifacts"]["charter"].write_text("a quietly different charter", encoding="utf-8")

    findings = activation.validate(
        bench["artifacts"], tournament_root=bench["root"], freeze_path=bench["freeze"]
    )

    assert findings == ["charter: content changed since activation"]


def test_a_changed_lane_surface_is_detected(bench):
    _freeze(bench)
    (bench["root"] / "teams" / "team-03" / "extra.py").write_text("smuggled", encoding="utf-8")

    findings = activation.validate(
        bench["artifacts"], tournament_root=bench["root"], freeze_path=bench["freeze"]
    )

    assert findings == ["team-03: lane surface changed since activation"]


def test_validation_reports_every_finding_rather_than_the_first(bench):
    """When a freeze breaks, the useful question is what changed -- stopping at the first
    difference hides the rest."""

    _freeze(bench)
    bench["artifacts"]["charter"].write_text("changed", encoding="utf-8")
    bench["artifacts"]["evaluator"].write_text("also changed", encoding="utf-8")
    (bench["root"] / "teams" / "team-01" / "extra.txt").write_text("x", encoding="utf-8")

    findings = activation.validate(
        bench["artifacts"], tournament_root=bench["root"], freeze_path=bench["freeze"]
    )

    assert len(findings) == 3


def test_a_lane_may_not_start_without_a_freeze(bench):
    with pytest.raises(activation.ActivationError, match="not activated"):
        activation.assert_activated(bench["freeze"])

    _freeze(bench)
    assert activation.assert_activated(bench["freeze"]).schema_version == activation.SCHEMA_VERSION


def test_an_amendment_must_state_its_reason(bench):
    with pytest.raises(activation.ActivationError, match="must state its reason"):
        activation.amend(bench["journal"], reason="  ", affects=["gates"])

    activation.amend(bench["journal"], reason="purge width corrected", affects=["sealed"])
    records = list(journal.iter_events(bench["journal"], "tournament_activated"))
    assert records[-1].payload["amendment"] == "purge width corrected"
