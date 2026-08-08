"""The integrity review scans a team's WHOLE working directory, not the archive it chose to freeze.

The mutation this file exists to catch is the reviewer running ``scan_for_blindness_violations``
over ``candidates/<id>/`` and calling it a workspace check. That scan reads the files a team
nominated; a team that opened the sealed snapshot and left the evidence in a research note, a
notebook, a log or a ``.pyc`` hands in a spotless archive. Every test below that asserts the
workspace scan found something also asserts the archive scan found NOTHING on the same tree -- so
none of them can pass by accident on a scanner that is merely the old one under a new name.
"""

import json
import re

import pandas as pd
import pytest

from crypto_trade.cup20.archive import (
    _MAX_CONTENT_SCAN_BYTES,
    FORBIDDEN_PATTERNS,
    WorkspaceScan,
    scan_for_blindness_violations,
    scan_workspace_for_blindness_violations,
)
from crypto_trade.cup20.config import IS_END, SEALED_END, SEALED_START
from crypto_trade.cup20.harness import CoachingPacket, GateDetail
from crypto_trade.cup20.metrics import is_folds

TOKEN = "9f" * 32

# The two date rules, taken from the module rather than retyped, so a test can never assert against
# a pattern the scanner does not actually run. Located by BEHAVIOUR rather than by index: appending
# a pattern to FORBIDDEN_PATTERNS must not silently re-point these at the wrong rule, and a build
# where neither pattern matches a post-cutoff date must fail loudly at import (StopIteration) rather
# than leave every test below asserting against nothing.
_AFTER_CUTOFF_PATTERN = next(p for p in FORBIDDEN_PATTERNS if re.search(p, "2024-09-15"))
_LATER_YEARS_PATTERN = next(p for p in FORBIDDEN_PATTERNS if re.search(p, "2026-08-01"))

# The exact rule the pattern replaced. Kept as a literal on purpose: several tests below prove
# their own non-vacuity by showing the text they scan WOULD have been flagged under it.
_SUPERSEDED_PATTERN = r"(?<!\d)2024-(?:0[89]|1[0-2])-\d{2}"


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
        ("backtested through 2024-09-30\n", _AFTER_CUTOFF_PATTERN),
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


# --- containment: what makes check 5 being weaker than check 4 acceptable -------------------------
#
# INTEGRITY-REVIEW.md check 5 runs `scan_for_blindness_violations` over each nominated candidate,
# and that surface is weaker than check 4's in three specific ways: it never matches the canary
# token by value, it stops reading a file's content at 256 KiB without saying which files it
# skipped, and it excludes __pycache__. The review states those gaps and then argues they are
# closed because every nominated candidate sits INSIDE the team directory check 4 walks. That
# argument is load-bearing, so it is asserted here rather than left as prose: each test below plants
# evidence inside `candidates/c1/`, shows the archive scan of that candidate reports nothing, and
# shows the workspace scan of the team root reports it.


def test_a_token_inside_a_nominated_candidate_is_invisible_to_the_archive_scan(tmp_path):
    candidate = _workspace(tmp_path)
    (candidate / "notes.md").write_text(f"cup20-holdout-canary:{TOKEN}\n")

    # scan_for_blindness_violations takes no canary_tokens argument at all -- check 5 structurally
    # cannot produce the strongest evidence the review has.
    assert scan_for_blindness_violations(candidate, team_id="team-01") == ()

    scan = scan_workspace_for_blindness_violations(
        tmp_path, team_id="team-01", canary_tokens=(TOKEN,)
    )
    assert "candidates/c1/notes.md:1:sealed-canary-token" in scan.violations


def test_content_past_the_archive_cap_inside_a_candidate_is_read_by_the_workspace_scan(tmp_path):
    candidate = _workspace(tmp_path)
    # Just past the archive scan's cap, which it skips silently -- there is no `unscanned` list on
    # that surface, so nothing tells the reviewer the content went unread.
    padded = candidate / "weights.json"
    padded.write_text(" " * (_MAX_CONTENT_SCAN_BYTES + 1) + "\ndata/cup20/sealed\n")
    assert padded.stat().st_size > _MAX_CONTENT_SCAN_BYTES
    assert scan_for_blindness_violations(candidate, team_id="team-01") == ()

    scan = scan_workspace_for_blindness_violations(tmp_path, team_id="team-01")
    assert "candidates/c1/weights.json:2:data/cup20/sealed" in scan.violations
    assert scan.unscanned == ()  # comfortably under the workspace scan's 8 MiB cap


# --- the IS cutoff is not a post-cutoff date -----------------------------------------------------
#
# The IS window is the half-open ``[IS_START, 2024-08-01)``. The cutoff is the first EXCLUDED
# instant, so the literal ``2024-08-01`` says only where the visible data stops -- it reveals
# nothing about the holdout, and it is universally disclosed: the charter's window table, the
# playbook, ``config.toml`` twice over (``is_end`` AND ``sealed_start``), and the organiser's own
# harness, which prints it into every packet it writes into a team's workspace. Matching it made the
# organiser hand each team a file that tripped the team's own blindness scan. Only dates strictly
# after the cutoff are evidence, so only those are matched.
#
# These tests pin the boundary in BOTH directions on BOTH scan surfaces. Loosening this control by a
# day more than intended is worse than the false positive it fixes, so the widening is bounded by an
# exhaustive differential (``test_the_carve_out_is_exactly_one_day_wide``) rather than by examples.

_PERMITTED_CUTOFF_FORMS = (
    "2024-08-01",
    "2024-08-01Z",
    "2024-08-01T00:00:00Z",  # config.toml's is_end / sealed_start spelling
    "2024-08-01 00:00:00+00:00",  # str(pd.Timestamp) -- what the packet JSON carries
    "window           [2020-08-17 00:00:00+00:00, 2024-08-01 00:00:00+00:00)   seed 7",
    "folds            F1 [2020-08-17, 2021-08-01), F4 [2023-08-01, 2024-08-01)",
    "IS research | `[IS_START, 2024-08-01)` | full artifacts",
)

_REFUSED_AFTER_CUTOFF = (
    "2024-08-02",  # the very next day
    "2024-08-02T00:00:00Z",
    "2024-08-03",
    "2024-08-10",
    "2024-08-31",
    "2024-09-01",
    "2024-12-31",
    "2024-08-012",  # a digit-extended run must not be read as the permitted day plus noise
    "2024-08-010",
)


@pytest.mark.parametrize("text", _PERMITTED_CUTOFF_FORMS)
def test_the_is_cutoff_itself_is_not_a_violation(tmp_path, text):
    """Catches: reverting the August branch to ``0[89]``, which flags the cutoff instant.

    That mutation is the organiser defect this rule was rewritten for -- it made every coaching
    packet the harness writes into a team workspace fail the team's own scan.
    """
    _workspace(tmp_path)
    note = tmp_path / "research" / "scratch.md"
    note.write_text(text + "\n")

    assert scan_workspace_for_blindness_violations(tmp_path, team_id="team-01").violations == ()
    assert scan_for_blindness_violations(tmp_path / "research", team_id="team-01") == ()

    # Not vacuous: the superseded rule DID flag this exact text, so the assertions above are about
    # the boundary and not about a file that happens to contain no date at all.
    flagged = scan_workspace_for_blindness_violations(
        tmp_path, team_id="team-01", extra_patterns=(_SUPERSEDED_PATTERN,)
    )
    assert flagged.violations == (f"research/scratch.md:1:{_SUPERSEDED_PATTERN}",)


@pytest.mark.parametrize("text", _REFUSED_AFTER_CUTOFF)
def test_every_date_after_the_cutoff_is_still_a_violation(tmp_path, text):
    """Catches: widening the carve-out past one day.

    ``(?!01(?!\\d))`` narrowed to ``(?!0)`` would permit 2024-08-02..09; dropping the August branch
    entirely would permit the whole month; dropping the inner ``(?!\\d)`` would permit the
    digit-extended ``2024-08-012``.
    """
    _workspace(tmp_path)
    (tmp_path / "research" / "scratch.md").write_text(text + "\n")

    scan = scan_workspace_for_blindness_violations(tmp_path, team_id="team-01")
    assert scan.violations == (f"research/scratch.md:1:{_AFTER_CUTOFF_PATTERN}",)
    assert scan_for_blindness_violations(tmp_path / "research", team_id="team-01") == (
        f"scratch.md:1:{_AFTER_CUTOFF_PATTERN}",
    )


def test_the_carve_out_is_exactly_one_day_wide():
    """Catches: any widening at all, by comparing against the superseded rule exhaustively.

    Examples cannot bound a regex; this can. Over every ``2024-MM-DD`` string -- all twelve months
    against all hundred two-digit day fields, real and impossible -- exactly one verdict may differ
    from the rule this replaced, and it must be the cutoff. A pattern that permitted 2024-08-02, or
    that quietly stopped matching September, fails here even if every example above still passes.
    """
    superseded = re.compile(_SUPERSEDED_PATTERN)
    current = re.compile(_AFTER_CUTOFF_PATTERN)
    differing = [
        candidate
        for month in range(1, 13)
        for day in range(100)
        for candidate in (f"2024-{month:02d}-{day:02d}",)
        if bool(superseded.search(candidate)) != bool(current.search(candidate))
    ]
    assert differing == ["2024-08-01"]


def test_the_sealed_start_and_the_is_end_are_the_same_instant_and_treated_alike():
    """Catches: permitting the cutoff only where it is spelled as an IS end.

    ``config.toml`` prints this one instant twice, as ``is_end`` and as ``sealed_start``. A rule
    that keyed on the surrounding words rather than the value would let a team write one and not the
    other, which is an inconsistency in a security control and a trap for whoever hits it second.
    """
    assert IS_END == SEALED_START
    current = re.compile(_AFTER_CUTOFF_PATTERN)
    later = re.compile(_LATER_YEARS_PATTERN)
    for line in (f'is_end = "{IS_END}"', f'sealed_start = "{SEALED_START}"'):
        assert not current.search(line) and not later.search(line)


def test_the_sealed_end_is_still_a_violation(tmp_path):
    """Catches: 'fixing' the later-years rule too.

    ``SEALED_END`` is 2026-08-01 -- genuinely inside the forbidden region, and the far edge of the
    holdout. It is not a boundary a team may know, and nothing the organiser writes into a team
    workspace contains it.
    """
    _workspace(tmp_path)
    (tmp_path / "research" / "scratch.md").write_text(f"sealed_end = {SEALED_END}\n")
    scan = scan_workspace_for_blindness_violations(tmp_path, team_id="team-01")
    assert scan.violations == (f"research/scratch.md:1:{_LATER_YEARS_PATTERN}",)


def _coaching_packet(is_start):
    """A packet shaped exactly as ``build_coaching_packet`` returns one, at the frozen cutoff."""
    return CoachingPacket(
        team_id="team-01",
        candidate_id="baseline",
        trial_sequence=3,
        accepted_trials=3,
        trial_budget=12,
        source_sha256="ab" * 32,
        snapshot_sha256="cd" * 32,
        window=(is_start, IS_END),
        folds=is_folds(is_start, IS_END),
        seed=7,
        declared_roles=("core",),
        observed_roles=("core",),
        cost_levels={"1": {"net_sharpe": 1.0}, "2": {"net_sharpe": 0.7}},
        fold_sharpes={"F1": 0.5, "F2": 0.9, "F3": 1.1, "F4": 0.8},
        scored={"net_sharpe": 1.0},
        gate_details=(
            GateDetail(
                name="net_sharpe",
                passed=True,
                observed=1.0,
                comparison=">=",
                floor=0.8,
                measured=True,
            ),
        ),
        unmeasured_gates=(),
        exposure_caps={
            stage: {
                "boundaries": 10,
                "trimmed_boundaries": 1,
                "minimum_scale": 0.9,
                "median_scale": 1.0,
                "binding_cap_counts": {},
            }
            for stage in ("requested", "executed")
        },
        risk_scalars={"median": 1.0, "minimum": 0.5, "maximum": 2.0},
        bootstrap_positive_fraction=0.95,
        trial_adjusted_confidence=0.92,
        ranking_score=1.0,
        workspace=WorkspaceScan(root="/w", violations=(), unscanned=(), files_scanned=3),
    )


@pytest.mark.parametrize("form", ["rendered", "json"])
def test_an_organiser_written_packet_scans_clean(tmp_path, form):
    """The regression that would have caught the defect.

    ``scripts/cup20_evaluate.py`` prints ``report.render()`` (teams redirect it into their tree) and
    writes ``report.as_dict()`` to ``--output``, a path inside the team workspace. Both carry the
    window banner and the F4 fold, both of which end at the cutoff. Under the superseded rule the
    organiser handed every team a file that failed the team's own blindness scan -- team 02 hit it
    and had to strip banner lines out of its own packets to submit.

    Catches: the superseded rule, and any future edit that re-flags the cutoff -- including one made
    somewhere other than this pattern, since this test scans real harness output rather than a
    hand-typed string.
    """
    _workspace(tmp_path)
    packet = _coaching_packet(pd.Timestamp("2020-08-17T00:00:00Z"))
    body = (
        packet.render()
        if form == "rendered"
        else json.dumps(packet.as_dict(), indent=2, sort_keys=True)
    )
    destination = tmp_path / "research" / f"packet.{'log' if form == 'rendered' else 'json'}"
    destination.write_text(body + "\n")

    # Non-vacuity, asserted three ways: the cutoff really is in there, it is there because the
    # harness put it there (not because this test typed it), and the superseded rule flagged it.
    assert "2024-08-01" in body
    assert packet.folds[-1][-1] == IS_END
    superseded = scan_workspace_for_blindness_violations(
        tmp_path, team_id="team-01", extra_patterns=(_SUPERSEDED_PATTERN,)
    )
    assert any(_SUPERSEDED_PATTERN in violation for violation in superseded.violations)

    scan = scan_workspace_for_blindness_violations(tmp_path, team_id="team-01")
    assert scan.violations == ()
    assert scan.clean


def test_pycache_inside_a_nominated_candidate_is_read_by_the_workspace_scan(tmp_path):
    candidate = _workspace(tmp_path)
    cache = candidate / "__pycache__"
    cache.mkdir()
    (cache / "strategy.cpython-313.pyc").write_bytes(
        b"\x00\x0c\r\n\x00\x00data/cup20/acquisition\x00\xff"
    )
    assert scan_for_blindness_violations(candidate, team_id="team-01") == ()

    scan = scan_workspace_for_blindness_violations(tmp_path, team_id="team-01")
    assert any("data/cup20/acquisition" in violation for violation in scan.violations)
