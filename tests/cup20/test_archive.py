import json
import os
import tarfile
from pathlib import Path

from crypto_trade.cup20.archive import (
    archive_directory,
    bundle_digest,
    scan_for_blindness_violations,
    verify_neighbourhood_coordinates,
)
from crypto_trade.cup20.neighbourhood import NeighbourhoodDeclaration


def _team(tmp_path: Path, body: str) -> Path:
    root = tmp_path / "team-01"
    root.mkdir(parents=True)
    (root / "strategy.py").write_text(body)
    return root


def test_bundle_digest_is_stable_and_content_sensitive(tmp_path):
    first = _team(tmp_path / "a", "x = 1\n")
    second = _team(tmp_path / "b", "x = 1\n")
    third = _team(tmp_path / "c", "x = 2\n")
    assert bundle_digest(first) == bundle_digest(second)
    assert bundle_digest(first) != bundle_digest(third)


def test_archive_directory_writes_tar_and_sidecar(tmp_path):
    root = _team(tmp_path / "src", "x = 1\n")
    digest = archive_directory(root, tmp_path / "archives")
    assert (tmp_path / "archives" / f"{digest}.tar").exists()
    assert (tmp_path / "archives" / f"{digest}.json").exists()


def test_sealed_data_path_is_a_violation(tmp_path):
    root = _team(tmp_path, "PATH = 'data/cup20/sealed/bars.parquet'\n")
    violations = scan_for_blindness_violations(root)
    assert any("data/cup20/sealed" in violation for violation in violations)


def test_post_cutoff_date_literal_is_a_violation(tmp_path):
    root = _team(tmp_path, "CUTOFF = '2025-03-01'\n")
    assert scan_for_blindness_violations(root)


def test_prior_tournament_directory_is_a_violation(tmp_path):
    root = _team(tmp_path, "import crypto_trade.tournament.top40_v4\n")
    assert scan_for_blindness_violations(root)


def test_another_team_directory_is_a_violation(tmp_path):
    root = _team(tmp_path, "OTHER = 'tournament/cup20/teams/team-07/candidates'\n")
    assert scan_for_blindness_violations(root, team_id="team-01")


def test_own_team_directory_is_allowed(tmp_path):
    root = _team(tmp_path, "SELF = 'tournament/cup20/teams/team-01/candidates'\n")
    assert scan_for_blindness_violations(root, team_id="team-01") == ()


def test_declared_coordinate_absent_from_frozen_source_is_a_violation(tmp_path):
    from crypto_trade.cup20.archive import verify_neighbourhood_coordinates
    from crypto_trade.cup20.neighbourhood import NeighbourhoodDeclaration

    root = _team(tmp_path, "LOOKBACK = 60\nTHRESHOLD = 1.0\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0, "INVENTED": 3.0},
        points=({"LOOKBACK": 40.0, "INVENTED": 2.0},),
        coordinates=("LOOKBACK", "INVENTED"),
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert any("INVENTED" in violation for violation in violations)
    assert not any("LOOKBACK" in violation for violation in violations)


def test_nominee_value_must_match_the_frozen_source(tmp_path):
    from crypto_trade.cup20.archive import verify_neighbourhood_coordinates
    from crypto_trade.cup20.neighbourhood import NeighbourhoodDeclaration

    root = _team(tmp_path, "LOOKBACK = 60\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 90.0},
        points=({"LOOKBACK": 40.0},),
        coordinates=("LOOKBACK",),
    )
    assert verify_neighbourhood_coordinates(root, declaration)


def test_matching_coordinates_and_values_have_no_violations(tmp_path):
    from crypto_trade.cup20.archive import verify_neighbourhood_coordinates
    from crypto_trade.cup20.neighbourhood import NeighbourhoodDeclaration

    root = _team(tmp_path, "LOOKBACK = 60\nTHRESHOLD = 1.5\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0, "THRESHOLD": 1.5},
        points=({"LOOKBACK": 40.0, "THRESHOLD": 1.2},),
        coordinates=("LOOKBACK", "THRESHOLD"),
    )
    assert verify_neighbourhood_coordinates(root, declaration) == ()


def test_verify_never_imports_the_frozen_source(tmp_path):
    from crypto_trade.cup20.archive import verify_neighbourhood_coordinates
    from crypto_trade.cup20.neighbourhood import NeighbourhoodDeclaration

    # Importing this module would raise; parsing it must not.
    root = _team(tmp_path, "LOOKBACK = 60\nraise RuntimeError('team code must never execute')\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    assert verify_neighbourhood_coordinates(root, declaration) == ()


def test_clean_source_has_no_violations(tmp_path):
    root = _team(
        tmp_path,
        "from crypto_trade.tournament.protocol import DecisionContext\n"
        "LOOKBACK = 60\n"
        "IS_ERA_NOTE = '2023-01-01 was a chop regime, 2024-07-31 is the last IS day'\n",
    )
    assert scan_for_blindness_violations(root, team_id="team-01") == ()


# --- Everything below this line is additional hardening beyond the brief's own 12 tests above. --
#
# This module's job is resisting a team that wants to game it, so every test below was written by
# trying to defeat the brief's Step 3 code as literally transcribed. Each docstring says what
# mutation/scenario it guards. Where a test exposed a real defect (not just a disclosed, accepted
# limitation of a line-based regex scan), the fix lives in crypto_trade.cup20.archive itself; the
# task report for this module records, for each fix, that the corresponding test was confirmed to
# FAIL against the brief's unmodified Step 3 code before the fix landed -- not merely reasoned
# about.


# --- bundle_digest / archive_directory determinism -----------------------------------------------


def test_bundle_digest_is_unaffected_by_mtime_change(tmp_path):
    """Proves invariance with an actual mutation (touching mtime), not by calling the function
    twice on an untouched fixture -- the latter would pass even if the digest secretly depended on
    wall-clock time, since nothing about the file would differ between the two calls."""
    root = _team(tmp_path, "x = 1\n")
    before = bundle_digest(root)
    os.utime(root / "strategy.py", (1_000_000, 1_000_000))
    after = bundle_digest(root)
    assert before == after


def test_bundle_digest_changes_when_a_file_is_renamed_with_identical_content(tmp_path):
    """A bundle's identity is which file holds what content, not an unordered bag of content
    blobs -- the relative path is deliberately part of the hash. Renaming strategy.py must
    therefore change the digest even though not one byte of content changed."""
    root = _team(tmp_path, "x = 1\n")
    before = bundle_digest(root)
    (root / "strategy.py").rename(root / "renamed.py")
    after = bundle_digest(root)
    assert before != after


def test_symlinks_are_excluded_from_the_digest_and_the_archived_tar(tmp_path):
    """A symlink dereferences differently for hashing (reading through it) than for archiving
    (tarfile.gettarinfo records a link, not a copy of the target's bytes) -- so letting
    bundle_digest silently follow a symlink would make the digest describe bytes the tar does not
    durably contain (the target can move, change, or vanish after archiving). Both functions must
    simply not see the symlink at all: present vs. absent must not change the digest, and the
    symlink must never appear as a tar member."""
    root = _team(tmp_path, "x = 1\n")
    outside = tmp_path / "outside.py"
    outside.write_text("SECRET = 'should never be smuggled into a bundle'\n")
    (root / "link.py").symlink_to(outside)

    with_link = bundle_digest(root)
    (root / "link.py").unlink()
    without_link = bundle_digest(root)
    assert with_link == without_link

    (root / "link.py").symlink_to(outside)
    digest = archive_directory(root, tmp_path / "archives")
    with tarfile.open(tmp_path / "archives" / f"{digest}.tar") as archive:
        assert archive.getnames() == ["strategy.py"]


def test_tar_members_have_neutralized_metadata_for_reproducibility(tmp_path):
    """The brief's stated reason tar members get mtime=0/uid=gid=0/mode=0o644: so the archive is
    byte-identical regardless of who built it or when. None of the given tests actually check
    these header fields -- only that a .tar file exists at all."""
    root = tmp_path / "team-01"
    root.mkdir(parents=True)
    (root / "strategy.py").write_text("x = 1\n")
    os.utime(root / "strategy.py", (1_234_567, 1_234_567))
    digest = archive_directory(root, tmp_path / "archives")
    with tarfile.open(tmp_path / "archives" / f"{digest}.tar") as archive:
        member = archive.getmember("strategy.py")
        assert member.mtime == 0
        assert member.uid == 0
        assert member.gid == 0
        assert member.mode == 0o644


def test_archiving_the_same_content_twice_produces_byte_identical_tar_bytes(tmp_path):
    """The determinism claim end-to-end: not just 'the digest matches' but the actual archived
    .tar BYTES are identical across two independent archiving runs of equivalent content with
    deliberately different mtimes -- proving the neutralized tar headers really do make the
    artifact itself reproducible, not merely the digest that names it."""
    first_root = tmp_path / "first" / "team-01"
    first_root.mkdir(parents=True)
    (first_root / "strategy.py").write_text("x = 1\n")
    os.utime(first_root / "strategy.py", (111_111, 111_111))

    second_root = tmp_path / "second" / "team-01"
    second_root.mkdir(parents=True)
    (second_root / "strategy.py").write_text("x = 1\n")
    os.utime(second_root / "strategy.py", (999_999_999, 999_999_999))

    digest_a = archive_directory(first_root, tmp_path / "out_a")
    digest_b = archive_directory(second_root, tmp_path / "out_b")
    assert digest_a == digest_b
    assert (tmp_path / "out_a" / f"{digest_a}.tar").read_bytes() == (
        tmp_path / "out_b" / f"{digest_b}.tar"
    ).read_bytes()


def test_archive_sidecar_and_tar_members_match_the_digest_and_source_tree(tmp_path):
    """The brief's own test only checks that the .tar and .json files EXIST, not that their
    content is right -- a digest bug that still produces *some* valid-looking tar/json pair would
    pass it. This pins the actual content: the returned digest equals a fresh bundle_digest of the
    same tree, the sidecar's own bundle_sha256 field agrees, the sidecar's file list is exactly the
    source tree's relative paths, and the tar's member names agree too."""
    root = tmp_path / "team-01"
    root.mkdir(parents=True)
    (root / "strategy.py").write_text("x = 1\n")
    (root / "helpers.py").write_text("y = 2\n")
    digest = archive_directory(root, tmp_path / "archives")
    assert digest == bundle_digest(root)

    sidecar = json.loads((tmp_path / "archives" / f"{digest}.json").read_text())
    assert sidecar["bundle_sha256"] == digest
    assert sorted(sidecar["files"]) == ["helpers.py", "strategy.py"]

    with tarfile.open(tmp_path / "archives" / f"{digest}.tar") as archive:
        assert sorted(archive.getnames()) == ["helpers.py", "strategy.py"]


# --- scan_for_blindness_violations: evasion attempts ----------------------------------------------


def test_forbidden_pattern_hidden_in_a_directory_path_is_caught_independent_of_content(
    tmp_path,
):
    """A team could try to smuggle sealed data by naming a subdirectory 'data/cup20/sealed'. The
    path itself must be checked independently of content -- this fixture's own bytes are the raw
    0-255 value range, which does not happen to reproduce the forbidden pattern as text, so if this
    test passes it is specifically because of path-scanning, not a content-scan coincidence (now
    that content scanning is no longer suffix-gated, see test_content_is_scanned_regardless_of_
    file_extension below, a fixture that put the pattern in content too would no longer isolate
    which check caught it)."""
    root = tmp_path / "team-01"
    (root / "data" / "cup20" / "sealed").mkdir(parents=True)
    (root / "data" / "cup20" / "sealed" / "cache.dat").write_bytes(bytes(range(256)))
    violations = scan_for_blindness_violations(root)
    assert any("data/cup20/sealed" in violation for violation in violations)


def test_forbidden_pattern_in_a_bare_filename_is_a_violation(tmp_path):
    """Putting the forbidden reference in a FILENAME rather than file content must still be
    caught -- the file's own text content here says nothing forbidden at all."""
    root = tmp_path / "team-01"
    root.mkdir(parents=True)
    (root / "reports-top40_summary.md").write_text("nothing forbidden in the text itself\n")
    violations = scan_for_blindness_violations(root)
    assert any("reports-top40" in violation for violation in violations)


def test_string_concatenation_evades_the_content_scan(tmp_path):
    """Documented, disclosed limitation, not a claim of airtightness: this is a line-based regex
    scan of literal source text, not an expression evaluator. A forbidden string assembled at
    parse time by concatenation never appears as one contiguous substring on any line, so it is
    not caught. Blindness is enforced PRIMARILY by absence -- the sealed rows are simply never in
    a team's data directory -- and this scan is a disclosed-imperfect second layer on top of that,
    not the sole safeguard. Pinning this as a passing test keeps the gap visible and
    regression-tracked instead of silently assumed away."""
    root = _team(tmp_path, "PATH = 'data/cup20/' + 'sealed/bars.parquet'\n")
    assert scan_for_blindness_violations(root) == ()


def test_content_is_scanned_regardless_of_file_extension(tmp_path):
    """Fix round: the extension allowlist (_SCANNED_SUFFIXES) was removed. It was a self-imposed
    filter, not a safety measure -- path.read_text(errors='replace') already tolerated non-UTF8
    bytes, so restricting which extensions got read bought no safety, only a blind spot. A
    forbidden string typed into a .dat file's content, with nothing in its path hinting at it,
    must now be caught."""
    root = tmp_path / "team-01"
    root.mkdir(parents=True)
    (root / "notes.dat").write_text("PATH = 'data/cup20/sealed/bars.parquet'\n")
    violations = scan_for_blindness_violations(root)
    assert any("data/cup20/sealed" in violation for violation in violations)


def test_content_scan_is_skipped_above_the_size_cap_but_path_scan_is_not(tmp_path):
    """The size cap that replaced the extension allowlist exists purely so a large, legitimate
    data/model file cannot make the scan pathologically slow -- it must not become a reinstated
    allowlist by another name. A file just over the cap, with the forbidden reference only in
    CONTENT (nothing in its path), is not flagged; an otherwise-identical file just under the cap
    still is. Path-scanning itself is size-independent (proven separately by the directory-path
    and bare-filename tests above, both using tiny fixtures) and is not re-tested for cap
    sensitivity here."""
    from crypto_trade.cup20.archive import _MAX_CONTENT_SCAN_BYTES

    root = tmp_path / "team-01"
    root.mkdir(parents=True)
    (root / "small.py").write_text("x = 1\n" * 10 + "PATH = 'data/cup20/sealed/x'\n")
    padding = "z" * (_MAX_CONTENT_SCAN_BYTES + 1024)
    (root / "large.py").write_text(f"PAD = '{padding}'\nPATH = 'data/cup20/sealed/x'\n")
    assert (root / "small.py").stat().st_size < _MAX_CONTENT_SCAN_BYTES
    assert (root / "large.py").stat().st_size > _MAX_CONTENT_SCAN_BYTES

    violations = scan_for_blindness_violations(root)
    assert any("small.py" in v and "data/cup20/sealed" in v for v in violations)
    assert not any("large.py" in v and "data/cup20/sealed" in v for v in violations)


def test_symlink_anywhere_in_the_tree_is_a_violation(tmp_path):
    """A symlink is a way to have a file 'present' in the working tree that is invisible to both
    the archive and the digest (see the _files docstring) and whose target never has to appear as
    text anywhere the content/path scan looks. Its mere presence must be flagged, regardless of
    whether the target even exists."""
    root = _team(tmp_path, "x = 1\n")
    (root / "link.py").symlink_to(tmp_path / "does" / "not" / "exist.py")
    violations = scan_for_blindness_violations(root)
    assert any("symlink" in violation for violation in violations)


def test_own_team_directory_via_path_structure_is_still_allowed(tmp_path):
    """Regression guard for the path-scan addition: a team's own nested directory structure must
    stay clean even though the path check now runs unconditionally on every file's own path, not
    only on file content."""
    root = tmp_path / "team-01"
    (root / "tournament" / "cup20" / "teams" / "team-01").mkdir(parents=True)
    (root / "tournament" / "cup20" / "teams" / "team-01" / "candidates.py").write_text("x = 1\n")
    assert scan_for_blindness_violations(root, team_id="team-01") == ()


def test_foreign_team_directory_via_path_structure_is_a_violation(tmp_path):
    """The foreign-team-directory rule must apply to a directory NAME a team creates, not only to
    a string literal typed into file content."""
    root = tmp_path / "team-01"
    (root / "tournament" / "cup20" / "teams" / "team-07").mkdir(parents=True)
    (root / "tournament" / "cup20" / "teams" / "team-07" / "candidates.py").write_text("x = 1\n")
    violations = scan_for_blindness_violations(root, team_id="team-01")
    assert any("foreign-team-directory" in violation for violation in violations)


# --- verify_neighbourhood_coordinates: scope restriction ------------------------------------------


def test_function_body_local_variable_is_not_a_frozen_parameter(tmp_path):
    """A local variable assigned inside a function body is not a material parameter of the
    strategy -- it is not even guaranteed to run, let alone be read from outside the function.
    Before the fix, _frozen_numeric_parameters used ast.walk, which recurses into every nested
    scope with no notion of 'module level' at all: a team could plant LOOKBACK = <favourable
    value> inside a throwaway function and have it accepted as if it governed anything. Confirmed
    against the brief's literal Step 3 code: this assertion FAILED there (violations was empty)."""
    root = _team(tmp_path, "def foo():\n    LOOKBACK = 90\n    return LOOKBACK\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 90.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert any("LOOKBACK" in violation and "absent" in violation for violation in violations)


def test_class_defined_inside_a_function_is_not_a_frozen_parameter(tmp_path):
    """A class (and therefore its attributes) defined inside a function is not part of the
    module's own top-level surface -- the class object does not even exist until the function
    runs."""
    root = _team(
        tmp_path, "def build():\n    class Config:\n        LOOKBACK = 90\n    return Config\n"
    )
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 90.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert any("LOOKBACK" in violation and "absent" in violation for violation in violations)


def test_class_attribute_alone_is_reported_absent(tmp_path):
    """Fix-round negative control: a class attribute, with no name collision against a
    module-level constant, must still be reported absent -- proving the exclusion is a real scope
    rule on its own, not merely a side effect of the collision-avoidance regression test below."""
    root = _team(tmp_path, "class Config:\n    LOOKBACK = 60\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert any("LOOKBACK" in violation and "absent" in violation for violation in violations)


def test_module_level_function_keyword_default_is_no_longer_collected(tmp_path):
    """Fix-round negative control: function keyword defaults were dropped as a collection source
    entirely (see _frozen_numeric_parameters), not merely fixed -- a coordinate declared against
    one is now reported absent, never matched."""
    root = _team(tmp_path, "def get_signal(symbol, lookback=60):\n    return lookback\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"lookback": 60.0}, points=({"lookback": 40.0},), coordinates=("lookback",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert any("lookback" in violation and "absent" in violation for violation in violations)


def test_method_keyword_default_is_no_longer_collected(tmp_path):
    """The method-default mirror of the test above -- also dropped, doubly so (it is both a
    function keyword default and nested inside a class body)."""
    root = _team(
        tmp_path,
        "class Strategy:\n    def __init__(self, lookback=60):\n        self.lookback = lookback\n",
    )
    declaration = NeighbourhoodDeclaration(
        nominee={"lookback": 60.0}, points=({"lookback": 40.0},), coordinates=("lookback",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert any("lookback" in violation and "absent" in violation for violation in violations)


# --- verify_neighbourhood_coordinates: fix round 1 -- false accusations against honest teams ------
#
# The scope-restriction fix above closed a real evasion (a decoy assignment buried in a function
# body or a dead conditional branch) but, as first shipped, opened the more dangerous failure in
# the opposite direction: falsely accusing an HONEST team. A missed evasion lets one cheat through;
# a false accusation disqualifies someone honest and, in a tournament, brands them dishonest. Every
# test below reproduces one of the confirmed false positives/misattributions against the pre-fix
# code and asserts the corrected, honest outcome.


def test_if_guarded_module_level_assignment_is_a_frozen_parameter(tmp_path):
    """A name assigned inside a module-level `if` (no `else`) is a genuine module-level name --
    an extremely common real pattern (an environment/PROD guard). Before this fix round,
    scope-restriction excluded ALL module-level control flow, including this, and reported
    'absent' for a team that had declared the objectively correct value."""
    root = _team(tmp_path, "PROD = True\nif PROD:\n    LOOKBACK = 60\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    assert verify_neighbourhood_coordinates(root, declaration) == ()


def test_try_except_body_assignment_is_a_frozen_parameter(tmp_path):
    """A name assigned inside a module-level try body (defensive-coding pattern) is likewise a
    genuine module-level name."""
    root = _team(tmp_path, "try:\n    LOOKBACK = 60\nexcept Exception:\n    pass\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    assert verify_neighbourhood_coordinates(root, declaration) == ()


def test_try_except_handler_body_assignment_is_a_frozen_parameter(tmp_path):
    """The ruling names handlers explicitly ('else/finally/handlers'): an assignment inside the
    except block itself must be reached too, not only the try body."""
    root = _team(tmp_path, "try:\n    1 / 0\nexcept ZeroDivisionError:\n    LOOKBACK = 60\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    assert verify_neighbourhood_coordinates(root, declaration) == ()


def test_try_else_body_assignment_is_a_frozen_parameter(tmp_path):
    """try's own `else` clause (runs only if no exception was raised) is a separate body from
    both `body` and `finalbody` and must be reached too."""
    root = _team(
        tmp_path, "try:\n    pass\nexcept Exception:\n    pass\nelse:\n    LOOKBACK = 60\n"
    )
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    assert verify_neighbourhood_coordinates(root, declaration) == ()


def test_try_finally_body_assignment_is_a_frozen_parameter(tmp_path):
    root = _team(tmp_path, "try:\n    pass\nfinally:\n    LOOKBACK = 60\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    assert verify_neighbourhood_coordinates(root, declaration) == ()


def test_for_loop_body_assignment_is_a_frozen_parameter(tmp_path):
    root = _team(tmp_path, "for _ in range(1):\n    LOOKBACK = 60\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    assert verify_neighbourhood_coordinates(root, declaration) == ()


def test_while_loop_body_assignment_is_a_frozen_parameter(tmp_path):
    root = _team(tmp_path, "while False:\n    LOOKBACK = 60\n    break\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    assert verify_neighbourhood_coordinates(root, declaration) == ()


def test_with_block_body_assignment_is_a_frozen_parameter(tmp_path):
    root = _team(
        tmp_path,
        "class _Ctx:\n"
        "    def __enter__(self):\n"
        "        return self\n"
        "    def __exit__(self, *args):\n"
        "        return False\n"
        "\n"
        "with _Ctx():\n"
        "    LOOKBACK = 60\n",
    )
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    assert verify_neighbourhood_coordinates(root, declaration) == ()


def test_tuple_unpacking_assignment_is_a_frozen_parameter(tmp_path):
    """The ruling explicitly calls out excluding this as having 'no anti-cheat benefit
    whatsoever' -- a module-level tuple assignment executes unconditionally exactly like a plain
    one."""
    root = _team(tmp_path, "LOOKBACK, THRESHOLD = 60, 1.5\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0, "THRESHOLD": 1.5},
        points=({"LOOKBACK": 40.0, "THRESHOLD": 1.2},),
        coordinates=("LOOKBACK", "THRESHOLD"),
    )
    assert verify_neighbourhood_coordinates(root, declaration) == ()


def test_tuple_unpacking_with_a_starred_target_is_not_paired(tmp_path):
    """A shape this function does not confidently understand -- here, unpacking with a starred
    target, so the target tuple (2 elements) and value tuple (3 elements) have different lengths
    -- must be skipped, not guessed at: reported absent, never misattributed."""
    root = _team(tmp_path, "LOOKBACK, *rest = 60, 1, 2\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert any("LOOKBACK" in violation and "absent" in violation for violation in violations)


def test_class_attribute_of_an_unrelated_class_does_not_clobber_a_module_level_constant(tmp_path):
    """The exact false accusation confirmed empirically against the pre-fix code: a module-level
    LOOKBACK of 60 (correct) followed by an UNRELATED class's own, differently-valued LOOKBACK
    attribute (999) must not overwrite the real value in the collector. Class bodies are never
    recursed into at all now, so there is no shared namespace for the two to collide in -- before
    this fix, both lived in the same flat found[str, float] dict keyed only by bare name, and
    whichever was visited last (here, the class attribute) silently won."""
    root = _team(tmp_path, "LOOKBACK = 60\nclass UnrelatedConfig:\n    LOOKBACK = 999\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    assert verify_neighbourhood_coordinates(root, declaration) == ()


def test_positional_only_parameter_default_is_absent_not_misattributed(tmp_path):
    """The posonlyargs bug: the OLD keyword-default collector aligned ast.arguments.defaults
    against `args.args + args.kwonlyargs`, omitting posonlyargs from the name list entirely. For
    `def get_signal(a=1, /, lookback=2)`, this zipped lookback's own default (2) away and instead
    attributed a's default (1) to the name 'lookback' -- so a team declaring the objectively
    correct nominee lookback=2.0 got 'nominee-2.0-differs-from-frozen-1.0': a false accusation of
    having declared the WRONG value, not merely an omission. Function keyword defaults are now
    dropped as a collection source entirely, so the correct outcome is 'absent' -- never again a
    wrong 'differs' value attributed to the wrong parameter."""
    root = _team(tmp_path, "def get_signal(a=1, /, lookback=2):\n    return a, lookback\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"lookback": 2.0}, points=({"lookback": 0.5},), coordinates=("lookback",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert violations == ("strategy.py:lookback:absent-from-frozen-source",)
    assert not any("differs" in violation for violation in violations)


def test_if_live_guarded_decoy_in_the_else_branch_is_a_conflict(tmp_path):
    """Fix round 2, finding 2, the coordinator's own exact reproduction: the code genuinely uses 5
    (LIVE is True), but a team declares nominee=60 -- the value in the textually-last branch -- and
    fix round 1's 'resolves to whichever branch is written last' behaviour ACCEPTED it. That is a
    decoy planted in the last branch defeating the exact check whose purpose is proving the
    nominated point is what the frozen code does; fix round 1 called this a disclosed limitation,
    but it is a working evasion, not a mere limitation. Fix round 2 closes it: two different values
    for the same name at module scope, however reached, is now always a conflict. Neither the
    decoy (60) nor the real value (5) is silently accepted -- a team whose material parameter is
    genuinely ambiguous like this cannot pass at all, which is the point: the honest fix is a
    single, unconditional module-level constant."""
    root = _team(tmp_path, "LIVE = True\nif LIVE:\n    LOOKBACK = 5\nelse:\n    LOOKBACK = 60\n")
    for candidate_nominee in (5.0, 60.0):
        declaration = NeighbourhoodDeclaration(
            nominee={"LOOKBACK": candidate_nominee},
            points=({"LOOKBACK": 1.0},),
            coordinates=("LOOKBACK",),
        )
        violations = verify_neighbourhood_coordinates(root, declaration)
        assert any(
            "LOOKBACK" in violation and "conflict" in violation for violation in violations
        ), f"nominee={candidate_nominee} unexpectedly accepted: {violations}"


def test_if_elif_else_with_three_diverging_values_is_a_conflict(tmp_path):
    """A second, independent diverging-branch fixture (three branches, not two) confirming the fix
    generalises beyond the coordinator's exact if/else reproduction -- e.g. an elif chain, not just
    a plain if/else, and more than two distinct candidate values."""
    root = _team(
        tmp_path,
        "x = 1\n"
        "if x == 0:\n"
        "    LOOKBACK = 10\n"
        "elif x == 1:\n"
        "    LOOKBACK = 60\n"
        "else:\n"
        "    LOOKBACK = 20\n",
    )
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 5.0},), coordinates=("LOOKBACK",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert any("LOOKBACK" in violation and "conflict" in violation for violation in violations)


# --- verify_neighbourhood_coordinates: nomination integrity ---------------------------------------


def test_a_later_reassignment_of_a_different_value_is_now_a_conflict(tmp_path):
    """CONTRACT CHANGE from fix round 2, disclosed explicitly rather than quietly changed: fix
    round 1 had LOOKBACK = 90 then LOOKBACK = 40 (two DIFFERENT values at module scope) resolve via
    last-assignment-wins to 40, treating 90 as a superseded decoy -- and this test used to assert
    exactly that (nominee=90 was a violation, nominee=40 was accepted). Fix round 2 tightened the
    rule: a coordinate must have exactly one numeric value at module scope, so two different values
    anywhere -- regardless of which is textually last -- is now ITSELF a violation, neither one
    silently accepted. This is the direct consequence of closing the diverging-branch decoy fix
    round 2 found (see test_if_live_guarded_decoy_in_the_else_branch_is_a_conflict below):
    "textually last" was never a reliable signal for what the frozen code actually does, and a
    plain top-to-bottom reassignment is not structurally different from an if/else in that respect
    -- both are two different values for the same name at module scope. An honest team assigning a
    single constant is unaffected either way, which is why this is the safe direction."""
    root = _team(tmp_path, "LOOKBACK = 90\nLOOKBACK = 40\n")
    for candidate_nominee in (90.0, 40.0):
        declaration = NeighbourhoodDeclaration(
            nominee={"LOOKBACK": candidate_nominee},
            points=({"LOOKBACK": 30.0},),
            coordinates=("LOOKBACK",),
        )
        violations = verify_neighbourhood_coordinates(root, declaration)
        assert any(
            "LOOKBACK" in violation and "conflict" in violation for violation in violations
        ), f"nominee={candidate_nominee} unexpectedly accepted: {violations}"


def test_the_same_value_assigned_twice_is_not_a_conflict(tmp_path):
    """Explicitly required by the fix round 2 ruling: 'assigning the same value twice is fine'.
    Two module-level assignments of the identical numeric value must collapse to a single-element
    set internally and produce no violation -- this is the case that distinguishes 'two different
    values is a conflict' from 'reassignment itself is suspicious', which it is not."""
    root = _team(tmp_path, "LOOKBACK = 60\nLOOKBACK = 60\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 30.0},), coordinates=("LOOKBACK",)
    )
    assert verify_neighbourhood_coordinates(root, declaration) == ()


# --- verify_neighbourhood_coordinates: untested raise paths and branches --------------------------


def test_missing_entrypoint_is_reported_as_a_violation(tmp_path):
    """Untested by the brief's own 12 tests: no fixture ever omits strategy.py entirely."""
    root = tmp_path / "team-01"
    root.mkdir(parents=True)
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert violations == ("strategy.py:missing-entrypoint",)


def test_missing_entrypoint_with_a_custom_entrypoint_name(tmp_path):
    """The entrypoint keyword-only argument is part of the public contract but no given test ever
    passes anything other than the default."""
    root = tmp_path / "team-01"
    root.mkdir(parents=True)
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration, entrypoint="model.py")
    assert violations == ("model.py:missing-entrypoint",)


def test_a_directory_named_like_the_entrypoint_is_treated_as_missing(tmp_path):
    """Path.exists() is True for a directory too; the guard must be is_file() specifically, or
    Path.read_text() on a directory raises IsADirectoryError instead of failing closed cleanly as
    a violation string."""
    root = tmp_path / "team-01"
    (root / "strategy.py").mkdir(parents=True)
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert violations == ("strategy.py:missing-entrypoint",)


def test_unparseable_source_is_reported_as_a_violation_not_raised(tmp_path):
    """Global constraint: failures are violation strings, not raises. ast.parse raises SyntaxError
    on malformed source; team code is untrusted, so this must fail closed as a violation rather
    than propagate an exception out of the check. Confirmed against the brief's literal Step 3
    code: this call raised an uncaught SyntaxError there instead of returning."""
    root = _team(tmp_path, "def foo(:\n    this is not valid python\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert violations == ("strategy.py:unparseable-source",)


def test_source_with_a_null_byte_is_reported_as_a_violation_not_raised(tmp_path):
    """A second unparseable-source fixture distinct from a plain grammar error, so the guard is
    not just pattern-matching on one specific exception shape: on this repo's Python 3.13,
    ast.parse raises SyntaxError with the message 'source code string cannot contain null bytes'
    for this input (verified directly, not assumed -- older Pythons raised ValueError for the same
    input, which is exactly why _UNPARSEABLE_SOURCE_ERRORS catches both)."""
    root = tmp_path / "team-01"
    root.mkdir(parents=True)
    (root / "strategy.py").write_bytes(b"LOOKBACK = 60\x00\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert violations == ("strategy.py:unparseable-source",)


def test_negative_numeric_literal_is_supported(tmp_path):
    """A negative frozen-source literal (ast.UnaryOp(USub, Constant)) must both be found and
    compared correctly, not silently dropped as non-numeric."""
    root = _team(tmp_path, "THRESHOLD = -1.5\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"THRESHOLD": -1.5}, points=({"THRESHOLD": -0.5},), coordinates=("THRESHOLD",)
    )
    assert verify_neighbourhood_coordinates(root, declaration) == ()


def test_source_with_no_numeric_parameters_reports_every_coordinate_absent(tmp_path):
    """A source containing no numeric literals at all must report EVERY declared coordinate as
    absent, not silently pass or crash on an empty parameters dict."""
    root = _team(tmp_path, "NAME = 'my strategy'\nTAG = 'v1'\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0, "THRESHOLD": 1.0},
        points=({"LOOKBACK": 40.0, "THRESHOLD": 0.5},),
        coordinates=("LOOKBACK", "THRESHOLD"),
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert len(violations) == 2
    assert all("absent-from-frozen-source" in violation for violation in violations)


def test_non_numeric_value_is_not_coerced_into_matching_a_coordinate(tmp_path):
    root = _team(tmp_path, "LOOKBACK = 'sixty'\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert any("absent-from-frozen-source" in violation for violation in violations)


def test_boolean_literal_is_not_treated_as_a_numeric_parameter(tmp_path):
    """bool is a subclass of int in Python, and True == 1.0 / False == 0.0 under ==. Without an
    explicit exclusion a team could satisfy a coordinate against a boolean flag's int-coerced
    value. _numeric already special-cases this in the brief's own Step 3 code; this test pins it
    as a tested contract instead of an incidental, unverified property."""
    root = _team(tmp_path, "ENABLED = True\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"ENABLED": 1.0}, points=({"ENABLED": 0.0},), coordinates=("ENABLED",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert any("absent-from-frozen-source" in violation for violation in violations)


def test_declared_value_within_floating_point_tolerance_is_accepted(tmp_path):
    """math.isclose, not ==: a frozen-source literal like 0.30000000000000004 (the real binary64
    result of computing 0.1 + 0.2 and writing down the literal) must still match a nominee
    declared as the clean 0.3."""
    root = _team(tmp_path, "THRESHOLD = 0.30000000000000004\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"THRESHOLD": 0.3}, points=({"THRESHOLD": 0.1},), coordinates=("THRESHOLD",)
    )
    assert verify_neighbourhood_coordinates(root, declaration) == ()


def test_nominee_missing_a_declared_coordinate_is_a_violation_not_a_crash(tmp_path):
    """NeighbourhoodDeclaration.validate() would normally catch a nominee that omits one of its
    own declared coordinates, but validate() is opt-in -- the plain dataclass constructor does not
    enforce it, and this function cannot assume its caller already ran it. Before the fix, a bare
    `declaration.nominee[coordinate]` subscript raised an uncaught KeyError for exactly this input
    -- the same defect class Task 8's own review caught in positive_point_fraction."""
    root = _team(tmp_path, "LOOKBACK = 60\n")
    declaration = NeighbourhoodDeclaration(
        nominee={}, points=({"LOOKBACK": 40.0},), coordinates=("LOOKBACK",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert violations == ("strategy.py:LOOKBACK:nominee-missing-declared-coordinate",)


def test_computed_expression_is_not_a_plain_numeric_literal(tmp_path):
    """Only plain (optionally negated) literal constants are collected, not arbitrary expressions:
    'THRESHOLD = 0.1 + 0.2' is a BinOp, not a Constant, so it is reported absent rather than
    evaluated. Disclosed both ways: a team cannot hide a decoy behind a computed expression
    either, but a genuinely computed real parameter is (correctly, conservatively) unsupported."""
    root = _team(tmp_path, "THRESHOLD = 0.1 + 0.2\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"THRESHOLD": 0.3}, points=({"THRESHOLD": 0.1},), coordinates=("THRESHOLD",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert any("absent-from-frozen-source" in violation for violation in violations)


# --- verify_neighbourhood_coordinates: fix round 2 -- untrusted-input crashes -----------------
#
# Round 1's scope-restriction fix, and this module's own tuple-unpacking/unary-negation support,
# all recurse over untrusted, team-authored ASTs with no depth guard as originally shipped. An
# elif chain is nested If.orelse, not extra source indentation, so ordinary Python recursion-depth
# limits never bounded it: a team-supplied file a few thousand branches long, comfortably under a
# megabyte, raised an uncaught RecursionError/MemoryError THROUGH THE PUBLIC API. In a module whose
# entire job is resisting a team, a file that crashes the anti-cheat check itself is a cheap denial
# of service, and a competing team has direct incentive to submit one.


def test_elif_chain_far_past_the_former_crash_depth_returns_a_violation_not_a_raise(tmp_path):
    """Reproduces the coordinator's own finding: an elif chain with a genuinely different value
    per branch, at a depth comfortably past where the pre-fix module raised an uncaught
    RecursionError (confirmed directly at n=1200, ~41 KB, and n=5000, ~178 KB -- this test uses
    n=2000, ~71 KB, comfortably under _MAX_ENTRYPOINT_BYTES so it exercises the real iterative
    traversal and ast.parse itself, not just the size-cap fast path). Every branch's value
    differs, so under the fix round 2 single-value rule the correct outcome is a
    'conflicting-module-level-values' violation -- the point of this test is that it returns
    that violation cleanly, rather than raising."""
    depth = 2000
    lines = ["x = 0", "if x == 0:\n    LOOKBACK = 0"]
    for i in range(1, depth):
        lines.append(f"elif x == {i}:\n    LOOKBACK = {i}")
    lines.append("else:\n    LOOKBACK = -1")
    root = _team(tmp_path, "\n".join(lines) + "\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 0.0}, points=({"LOOKBACK": 1.0},), coordinates=("LOOKBACK",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)  # must not raise
    assert violations != ()
    assert all(isinstance(violation, str) for violation in violations)
    assert any("LOOKBACK" in v and "conflict" in v for v in violations)


def test_entrypoint_larger_than_the_size_cap_is_a_violation_not_a_parse_attempt(tmp_path):
    """A cheap, fast rejection before ever calling ast.parse, which is itself capable of
    exhausting memory on pathological input regardless of what this module's own traversal does
    (confirmed: ast.parse alone raised MemoryError on a large enough elif chain). A file just over
    _MAX_ENTRYPOINT_BYTES is rejected on size alone, never reaching the parser."""
    from crypto_trade.cup20.archive import _MAX_ENTRYPOINT_BYTES

    root = tmp_path / "team-01"
    root.mkdir(parents=True)
    padding = "z" * (_MAX_ENTRYPOINT_BYTES + 1024)
    (root / "strategy.py").write_text(f"PAD = '{padding}'\nLOOKBACK = 60\n")
    assert (root / "strategy.py").stat().st_size > _MAX_ENTRYPOINT_BYTES
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 1.0},), coordinates=("LOOKBACK",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert violations == ("strategy.py:entrypoint-too-large",)


# --- verify_neighbourhood_coordinates: fix round 2 -- self-initiated extension -----------------
#
# Not named in the coordinator's finding. Found by asking the same adversarial question ("where
# else does this module recurse over an untrusted AST with no depth guard?") of every recursive
# site, not just the one the coordinator pointed at. _numeric's UnaryOp handling (chained
# negation, e.g. `----5`) and _record_numeric_target's Tuple-pairing (nested single-element tuple
# unpacking) are both EXPRESSION-tree recursions with the identical shape of vulnerability -- and
# chained negation is cheaper for an attacker than the elif-chain case (about one byte of source
# per recursion level, vs. ~30-40 for an elif branch). Both are now guarded by the same
# _MAX_EXPRESSION_DEPTH used nowhere else, confirmed to engage at a precise, isolated boundary
# (not merely "large enough numbers don't crash").


def test_expression_depth_guard_engages_for_unary_negation(tmp_path):
    """Precise, isolated proof the guard in _numeric actually engages, not just that nothing
    crashes at an extreme depth (see the extreme-depth test below, where ast.parse's own
    resilience is really what is being exercised). Confirmed directly: ast.parse itself parses 25
    nested unary minuses with no difficulty at all (no parser-level failure to confound the
    result), so if this reports absent, it is because _MAX_EXPRESSION_DEPTH made _numeric give up,
    not because parsing failed."""
    root = _team(tmp_path, "LOOKBACK = " + "-" * 25 + "5\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 5.0}, points=({"LOOKBACK": 1.0},), coordinates=("LOOKBACK",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert any("LOOKBACK" in v and "absent" in v for v in violations)


def test_expression_depth_guard_engages_for_nested_tuple_unpacking(tmp_path):
    """The Tuple-pairing counterpart of the test above -- same precise-boundary proof, same
    confirmation that ast.parse itself tolerates this depth (25) with no difficulty, isolating
    _record_numeric_target's own guard as the reason LOOKBACK is reported absent."""
    depth = 25
    target = "LOOKBACK"
    value = "60"
    for _ in range(depth):
        target = f"({target},)"
        value = f"({value},)"
    root = _team(tmp_path, f"{target} = {value}\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 1.0},), coordinates=("LOOKBACK",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)
    assert any("LOOKBACK" in v and "absent" in v for v in violations)


def test_extreme_unary_negation_depth_does_not_raise(tmp_path):
    """Defense in depth at the far end of the scale: 5000 nested unary minuses (a few KB of
    source) must not raise, regardless of which guard or layer is what actually stops it."""
    root = _team(tmp_path, "LOOKBACK = " + "-" * 5000 + "5\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 5.0}, points=({"LOOKBACK": 1.0},), coordinates=("LOOKBACK",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)  # must not raise
    assert isinstance(violations, tuple)


def test_extreme_nested_tuple_depth_does_not_raise(tmp_path):
    """The Tuple counterpart at extreme scale -- and an honest correction to what actually
    protects it, checked directly rather than assumed: CPython's own parser has a hard-coded
    nesting guard that has nothing to do with this module, confirmed to raise
    'SyntaxError: too many nested parentheses' for any depth past roughly 300 (independently of
    available memory or the interpreter's recursion limit -- 100 parses fine, 300 already fails).
    That SyntaxError was already caught by _UNPARSEABLE_SOURCE_ERRORS before this fix round
    existed, so at depth 3000 this test does NOT exercise the round 2 exception-broadening
    (RecursionError/MemoryError) or prove _record_numeric_target's own depth guard is what saves
    it -- ast.parse never gets far enough for either to matter. It is still worth keeping: it
    proves the whole system does not crash at this scale, for whichever reason, and see
    test_expression_depth_guard_engages_for_nested_tuple_unpacking above for the test that
    actually isolates this module's own guard (at depth 25, confirmed ast.parse has no difficulty
    at all, so that result is unambiguously this module's own doing)."""
    depth = 3000
    target = "LOOKBACK"
    value = "60"
    for _ in range(depth):
        target = f"({target},)"
        value = f"({value},)"
    root = _team(tmp_path, f"{target} = {value}\n")
    declaration = NeighbourhoodDeclaration(
        nominee={"LOOKBACK": 60.0}, points=({"LOOKBACK": 1.0},), coordinates=("LOOKBACK",)
    )
    violations = verify_neighbourhood_coordinates(root, declaration)  # must not raise
    assert isinstance(violations, tuple)
