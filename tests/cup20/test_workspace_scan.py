"""The integrity review scans a team's WHOLE working directory, not the archive it chose to freeze.

The mutation this file exists to catch is the reviewer running ``scan_for_blindness_violations``
over ``candidates/<id>/`` and calling it a workspace check. That scan reads the files a team
nominated; a team that opened the sealed snapshot and left the evidence in a research note, a
notebook, a log or a ``.pyc`` hands in a spotless archive. Every test below that asserts the
workspace scan found something also asserts the archive scan found NOTHING on the same tree -- so
none of them can pass by accident on a scanner that is merely the old one under a new name.
"""

import pytest

from crypto_trade.cup20.archive import (
    scan_for_blindness_violations,
    scan_workspace_for_blindness_violations,
)

TOKEN = "9f" * 32


def _workspace(root):
    """A structurally real team workspace: a clean frozen candidate plus research scratch."""
    candidate = root / "candidates" / "c1"
    candidate.mkdir(parents=True)
    (candidate / "strategy.py").write_text("FORMATION_BARS = 30\n")
    (candidate / "risk_policy.json").write_text("{}\n")
    (root / "research").mkdir()
    (root / "RESEARCH-CERTIFICATE.md").write_text("# certificate\n")
    return candidate


def test_a_clean_workspace_is_clean(tmp_path):
    _workspace(tmp_path)
    scan = scan_workspace_for_blindness_violations(tmp_path, team_id="team-01")
    assert scan.violations == ()
    assert scan.unscanned == ()
    assert scan.clean
    assert scan.files_scanned == 3


def test_the_workspace_scan_catches_evidence_the_archive_scan_cannot_see(tmp_path):
    """The whole reason this function exists."""
    candidate = _workspace(tmp_path)
    (tmp_path / "research" / "scratch.md").write_text(
        "peeked at data/cup20/sealed/bars.parquet, drawdown looks fine\n"
    )
    # The frozen archive -- what a pre-flight gate reads -- is spotless.
    assert scan_for_blindness_violations(candidate, team_id="team-01") == ()
    scan = scan_workspace_for_blindness_violations(tmp_path, team_id="team-01")
    assert scan.violations == ("research/scratch.md:1:data/cup20/sealed",)
    assert not scan.clean


def test_evidence_in_a_log_outside_every_declared_directory_is_caught(tmp_path):
    _workspace(tmp_path)
    (tmp_path / "nohup.out").write_text("ls tournament/cup20/private/\n")
    scan = scan_workspace_for_blindness_violations(tmp_path, team_id="team-01")
    assert scan.violations == ("nohup.out:1:tournament/cup20/private",)


def test_a_forbidden_reference_spelled_into_a_directory_name_is_caught(tmp_path):
    _workspace(tmp_path)
    stash = tmp_path / "research" / "data" / "cup20" / "acquisition"
    stash.mkdir(parents=True)
    (stash / "notes.txt").write_text("nothing here\n")
    scan = scan_workspace_for_blindness_violations(tmp_path, team_id="team-01")
    assert scan.violations == (
        "research/data/cup20/acquisition/notes.txt:0:data/cup20/acquisition",
    )


def test_pycache_content_is_scanned_even_though_the_archive_scan_skips_it(tmp_path):
    # A team can delete the .py and keep the compiled artefact; the string survives in the
    # constant pool. The archive scan excludes __pycache__ outright.
    _workspace(tmp_path)
    cache = tmp_path / "research" / "__pycache__"
    cache.mkdir()
    (cache / "peek.cpython-313.pyc").write_bytes(
        b"\x00\x0c\r\n\x00\x00data/cup20/sealed/funding.parquet\x00\xff"
    )
    assert scan_for_blindness_violations(tmp_path, team_id="team-01") == ()
    scan = scan_workspace_for_blindness_violations(tmp_path, team_id="team-01")
    assert any("data/cup20/sealed" in violation for violation in scan.violations)


def test_a_symlink_is_reported_and_so_is_where_it_points(tmp_path):
    _workspace(tmp_path)
    link = tmp_path / "research" / "peek"
    link.symlink_to("../../../data/cup20/sealed")
    scan = scan_workspace_for_blindness_violations(tmp_path, team_id="team-01")
    assert "research/peek:0:symlink-not-allowed" in scan.violations
    assert "research/peek:0:data/cup20/sealed" in scan.violations


def test_a_symlink_is_never_followed_into_its_target_tree(tmp_path):
    # A link to a directory full of legitimate files must not multiply the scan or hash its
    # contents -- only the link itself and its target string are evidence.
    _workspace(tmp_path)
    outside = tmp_path.parent / "outside"
    outside.mkdir()
    (outside / "big.txt").write_text("x\n")
    (tmp_path / "research" / "link").symlink_to(outside)
    scan = scan_workspace_for_blindness_violations(tmp_path, team_id="team-01")
    assert scan.files_scanned == 3
    assert scan.violations == ("research/link:0:symlink-not-allowed",)


def test_a_planted_canary_token_is_found_by_value(tmp_path):
    _workspace(tmp_path)
    (tmp_path / "research" / "dump.txt").write_text(f"cup20-holdout-canary:{TOKEN}\n")
    scan = scan_workspace_for_blindness_violations(
        tmp_path, team_id="team-01", canary_tokens=(TOKEN,)
    )
    assert "research/dump.txt:1:sealed-canary-token" in scan.violations


def test_the_token_is_only_evidence_when_the_reviewer_supplies_it(tmp_path):
    # Not vacuous: the same tree is clean without the token, so the assertion above is about the
    # token and not about some other pattern the file happens to trip.
    _workspace(tmp_path)
    (tmp_path / "research" / "dump.txt").write_text(f"{TOKEN}\n")
    assert scan_workspace_for_blindness_violations(tmp_path, team_id="team-01").violations == ()


def test_an_empty_token_never_matches_every_file(tmp_path):
    # `"" in text` is True for every string; an empty token must not turn the scan into a
    # universal accusation.
    _workspace(tmp_path)
    scan = scan_workspace_for_blindness_violations(tmp_path, team_id="team-01", canary_tokens=("",))
    assert scan.violations == ()


def test_an_extra_pattern_covers_a_path_that_could_not_be_frozen_in_advance(tmp_path):
    # The quarantine root is chosen when the tournament starts, so it can never be a literal in
    # FORBIDDEN_PATTERNS; the review passes it in.
    _workspace(tmp_path)
    (tmp_path / "research" / "notes.md").write_text("/srv/cup20-quarantine/sealed\n")
    assert scan_workspace_for_blindness_violations(tmp_path, team_id="team-01").violations == ()
    scan = scan_workspace_for_blindness_violations(
        tmp_path, team_id="team-01", extra_patterns=("cup20-quarantine",)
    )
    assert scan.violations == ("research/notes.md:1:cup20-quarantine",)


def test_an_oversized_file_is_reported_rather_than_silently_skipped(tmp_path):
    _workspace(tmp_path)
    big = tmp_path / "research" / "cache.parquet"
    big.write_bytes(b"\x00" * 2048)
    scan = scan_workspace_for_blindness_violations(
        tmp_path, team_id="team-01", max_content_bytes=1024
    )
    assert scan.violations == ()
    assert scan.unscanned == ("research/cache.parquet:2048",)
    assert not scan.clean  # unread content is a hole in the verdict, not a pass


def test_an_oversized_file_still_has_its_path_scanned(tmp_path):
    _workspace(tmp_path)
    big = tmp_path / "research" / "reports-cup20-holdout.parquet"
    big.write_bytes(b"\x00" * 2048)
    scan = scan_workspace_for_blindness_violations(
        tmp_path, team_id="team-01", max_content_bytes=1024
    )
    assert scan.violations == ("research/reports-cup20-holdout.parquet:0:reports-cup20",)
    assert scan.unscanned == ("research/reports-cup20-holdout.parquet:2048",)


def test_a_team_may_name_its_own_directory_but_not_another_teams(tmp_path):
    _workspace(tmp_path)
    (tmp_path / "research" / "notes.md").write_text(
        "mine: tournament/cup20/teams/team-01/research\n"
        "theirs: tournament/cup20/teams/team-07/candidates\n"
    )
    scan = scan_workspace_for_blindness_violations(tmp_path, team_id="team-01")
    assert scan.violations == ("research/notes.md:2:foreign-team-directory",)


def test_without_a_team_id_every_team_directory_reference_is_foreign(tmp_path):
    _workspace(tmp_path)
    (tmp_path / "research" / "notes.md").write_text("tournament/cup20/teams/team-01/research\n")
    scan = scan_workspace_for_blindness_violations(tmp_path)
    assert scan.violations == ("research/notes.md:1:foreign-team-directory",)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("backtested through 2024-09-30\n", r"(?<!\d)2024-(?:0[89]|1[0-2])-\d{2}"),
        ("holdout ends 2026-08-01\n", r"(?<!\d)20(?:2[5-9]|[3-9]\d)-\d{2}-\d{2}"),
        ("copied HOLDOUT-CANARY-DO-NOT-READ.txt\n", "HOLDOUT-CANARY-DO-NOT-READ"),
    ],
)
def test_post_cutoff_and_canary_references_are_caught_in_scratch_files(tmp_path, text, expected):
    _workspace(tmp_path)
    (tmp_path / "research" / "scratch.md").write_text(text)
    scan = scan_workspace_for_blindness_violations(tmp_path, team_id="team-01")
    assert scan.violations == (f"research/scratch.md:1:{expected}",)


def test_a_non_utf8_file_is_searched_as_text_rather_than_skipped(tmp_path):
    _workspace(tmp_path)
    (tmp_path / "research" / "blob.bin").write_bytes(
        b"\xff\xfe\x00 data/cup20/acquisition \x80\x81"
    )
    scan = scan_workspace_for_blindness_violations(tmp_path, team_id="team-01")
    assert scan.violations == ("research/blob.bin:1:data/cup20/acquisition",)


def test_the_scan_reports_the_resolved_root_it_actually_walked(tmp_path):
    _workspace(tmp_path)
    scan = scan_workspace_for_blindness_violations(tmp_path, team_id="team-01")
    assert scan.root == str(tmp_path.resolve())
