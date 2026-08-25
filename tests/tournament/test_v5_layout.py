from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import pytest

from crypto_trade.tournament.v5.layout import TOP40_V5_LAYOUT, TournamentLayoutV5

ROOT = Path(__file__).resolve().parents[2]


def _layout(**overrides: object) -> TournamentLayoutV5:
    return dataclasses.replace(TOP40_V5_LAYOUT, **overrides)  # type: ignore[arg-type]


def test_frozen_layout_identity() -> None:
    assert TOP40_V5_LAYOUT.name == "quant-portfolio-blind-top40-v5"
    assert TOP40_V5_LAYOUT.tournament_root == "tournament/top40-v5"
    assert TOP40_V5_LAYOUT.reports_root == "reports-top40-v5"
    assert len(TOP40_V5_LAYOUT.team_ids) == 15
    assert TOP40_V5_LAYOUT.team_ids[0] == "team-01"
    assert TOP40_V5_LAYOUT.team_ids[-1] == "team-15"
    assert TOP40_V5_LAYOUT.maximum_trials == 12
    assert TOP40_V5_LAYOUT.minimum_trials_before_decision == 8
    assert TOP40_V5_LAYOUT.desk_individual_count == 3


def test_sealed_artifacts_are_physically_separate_from_the_team_visible_root() -> None:
    """The team packet must be unable to reach a sealed statistic even by mistake.

    A filter can be forgotten once. A directory that the visible-artifact code never opens
    cannot be. Assert the two roots are disjoint subtrees, not merely different strings.
    """

    visible = Path(TOP40_V5_LAYOUT.is_reports_root)
    sealed = Path(TOP40_V5_LAYOUT.sealed_private_root)
    assert not sealed.is_relative_to(visible)
    assert not visible.is_relative_to(sealed)
    assert sealed.is_relative_to(Path(TOP40_V5_LAYOUT.private_root))
    assert not Path(TOP40_V5_LAYOUT.private_root).is_relative_to(Path(TOP40_V5_LAYOUT.reports_root))


def test_scouting_root_is_not_inside_the_lane_feedback_surface() -> None:
    """Phase S runs with the network on, so it must not be able to read lane feedback.

    The offline profile mounts the whole team root, feedback included. The scouting profile
    mounts only this subtree, so it must be a sibling of feedback rather than an ancestor.
    """

    scouting = Path(TOP40_V5_LAYOUT.team_scouting_root("team-01"))
    feedback = Path(TOP40_V5_LAYOUT.team_root("team-01")) / "feedback"
    candidates = Path(TOP40_V5_LAYOUT.team_root("team-01")) / "candidates"
    outbox = Path(TOP40_V5_LAYOUT.team_root("team-01")) / "outbox"
    for sibling in (feedback, candidates, outbox):
        assert not sibling.is_relative_to(scouting)
        assert not scouting.is_relative_to(sibling)


def test_team_kit_root_is_derived_not_hard_coded() -> None:
    """V4 hard-coded its kit root as a module constant, so a new edition silently inherited
    the previous edition's kit. Deriving it makes that unrepresentable."""

    assert TOP40_V5_LAYOUT.team_kit_root.startswith(TOP40_V5_LAYOUT.tournament_root + "/")
    moved = _layout(tournament_root="tournament/elsewhere")
    assert moved.team_kit_root == "tournament/elsewhere/team-kit"


def test_every_authority_path_stays_inside_a_declared_root() -> None:
    roots = (TOP40_V5_LAYOUT.tournament_root, TOP40_V5_LAYOUT.reports_root, "tests")
    paths = (
        TOP40_V5_LAYOUT.config_path,
        TOP40_V5_LAYOUT.activation_freeze_path,
        TOP40_V5_LAYOUT.journal_path,
        TOP40_V5_LAYOUT.result_lock_path,
        TOP40_V5_LAYOUT.nomination_registry_path,
        TOP40_V5_LAYOUT.selection_freeze_path,
        TOP40_V5_LAYOUT.calibration_report_path,
        TOP40_V5_LAYOUT.snapshot_preflight_path,
        TOP40_V5_LAYOUT.mutation_ledger_path,
        TOP40_V5_LAYOUT.team_kit_root,
        TOP40_V5_LAYOUT.private_root,
        TOP40_V5_LAYOUT.is_reports_root,
        TOP40_V5_LAYOUT.sealed_private_root,
        TOP40_V5_LAYOUT.scouting_private_root,
        TOP40_V5_LAYOUT.historical_private_root,
        TOP40_V5_LAYOUT.historical_release_root,
        TOP40_V5_LAYOUT.source_archive_root,
        TOP40_V5_LAYOUT.team_root("team-07"),
        TOP40_V5_LAYOUT.team_scouting_root("team-07"),
    )
    for path in paths:
        assert not Path(path).is_absolute()
        assert ".." not in Path(path).parts
        assert any(path == root or path.startswith(root + "/") for root in roots), path


def test_unknown_team_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown V5 team"):
        TOP40_V5_LAYOUT.require_team("team-99")
    with pytest.raises(ValueError, match="unknown V5 team"):
        TOP40_V5_LAYOUT.team_root("team-00")


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"name": "Top40-V5"}, "kebab-case"),
        ({"branch": "has space"}, "branch is invalid"),
        ({"tournament_root": "/abs/path"}, "safe repository-relative"),
        ({"tournament_root": "../escape"}, "safe repository-relative"),
        ({"team_ids": ("team-01", "team-03")}, "contiguous"),
        ({"team_ids": ("team-01", "team-01")}, "unique teams"),
        ({"maximum_trials": 0}, "maximum_trials must be positive"),
        ({"minimum_trials_before_decision": 13}, "must fit inside the trial budget"),
        ({"desk_individual_count": 0}, "desk_individual_count must fit"),
        ({"desk_individual_count": 99}, "desk_individual_count must fit"),
    ],
)
def test_invalid_layouts_are_rejected(overrides: dict[str, object], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        _layout(**overrides)


def _edition_suffix_branches(source: str) -> list[str]:
    """Find real ``<expr>.endswith("-<edition>")`` calls, ignoring prose that mentions them."""

    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"endswith", "startswith"} or not node.args:
            continue
        argument = node.args[0]
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
            if argument.value.startswith("-"):
                found.append(f"line {node.lineno}: .{node.func.attr}({argument.value!r})")
    return found


def test_v5_package_declares_no_edition_string_branch() -> None:
    """V4 carries 81 ``name.endswith("-r2")`` tests, and a third edition would silently take
    the R1 arm at every one. V5 is one edition; the idiom must never enter the package."""

    package = ROOT / "src" / "crypto_trade" / "tournament" / "v5"
    offenders = {
        module.relative_to(ROOT).as_posix(): branches
        for module in sorted(package.rglob("*.py"))
        if (branches := _edition_suffix_branches(module.read_text(encoding="utf-8")))
    }
    assert offenders == {}


def test_the_edition_branch_detector_actually_detects() -> None:
    """Mutation guard: a checker that never fires is indistinguishable from a clean tree."""

    assert _edition_suffix_branches('x = name.endswith("-r2")') != []
    assert _edition_suffix_branches('"""prose mentioning endswith("-r2") only"""') == []
    assert _edition_suffix_branches('x = name.endswith("json")') == []
