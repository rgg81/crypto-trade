"""Run every check in tournament/cup20/INTEGRITY-REVIEW.md and print one verdict.

Run from the repository root, after the holdout has been scored and before anyone advances.

    uv run python scripts/cup20_integrity_review.py
    uv run python scripts/cup20_integrity_review.py --quarantine-root /srv/cup20-quarantine

Each check prints ``PASS``, ``FAIL`` or ``SKIP`` with the reason. The process exits non-zero if any
check FAILED. A SKIP is never silent and never counts as a pass: it names the artifact that was
missing, and the review document says which skips are legitimate at which phase.

Nothing here is a substitute for reading the output. A clean run means the mechanical checks found
nothing, which is a different claim from "nobody cheated" -- see charter section 14.8.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

from crypto_trade.cup20.activation import verify_activation
from crypto_trade.cup20.archive import (
    scan_for_blindness_violations,
    scan_workspace_for_blindness_violations,
    verify_neighbourhood_coordinates,
)
from crypto_trade.cup20.config import load_config
from crypto_trade.cup20.journal import verify_chain
from crypto_trade.cup20.neighbourhood import load_declaration
from crypto_trade.cup20.quarantine import (
    load_receipt,
    read_canary_token,
    sealed_access_report,
    verify_quarantine_covered_research,
)

CONFIG_PATH = Path("tournament/cup20/config.toml")


class Review:
    """Accumulates check outcomes so one failure never hides the rest."""

    def __init__(self) -> None:
        self.failures: list[str] = []
        self.skips: list[str] = []

    def check(self, name: str, run: Callable[[], str]) -> None:
        try:
            detail = run()
        except FileNotFoundError as error:
            self.skips.append(name)
            print(f"SKIP  {name}\n        missing artifact: {error}")
        except Exception as error:  # noqa: BLE001 - every failure is a finding, not a crash
            self.failures.append(name)
            print(f"FAIL  {name}\n        {type(error).__name__}: {error}")
        else:
            print(f"PASS  {name}" + (f"\n        {detail}" if detail else ""))


def _teams(team_root: Path) -> list[Path]:
    return sorted(path for path in team_root.glob("team-*") if path.is_dir())


def _candidates(team: Path) -> list[Path]:
    candidates = team / "candidates"
    if not candidates.is_dir():
        return []
    return sorted(path for path in candidates.iterdir() if (path / "strategy.py").is_file())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quarantine-root",
        default=None,
        help="the quarantine destination, so its path can be scanned for as a forbidden reference",
    )
    parser.add_argument("--config", default=str(CONFIG_PATH))
    arguments = parser.parse_args()

    config = load_config(arguments.config).raw
    paths = config["paths"]
    tournament_root = Path(paths["tournament_root"])
    receipt_path = tournament_root / "quarantine-receipt.json"
    baseline_path = tournament_root / "sealed-access-baseline.json"
    team_root = Path(paths["team_root"])
    review = Review()

    # Check 1 -- the authorities are the ones activation bound.
    def _activation() -> str:
        record = verify_activation(paths["activation_freeze"])
        return f"sealed manifest {record['sealed_manifest_sha256'][:16]}... unchanged"

    review.check("1. activation record verifies against every bound authority", _activation)

    # Check 2 -- the journal is a chain, before anything is read off its ordering.
    def _chain() -> str:
        return f"{verify_chain(paths['research_journal'])} records chain cleanly"

    review.check("2. research journal chain verifies", _chain)

    # Check 3 -- quarantine bracketed the research phase, proved by that ordering.
    def _custody() -> str:
        report = verify_quarantine_covered_research(
            journal_path=paths["research_journal"], receipt_path=receipt_path
        )
        return (
            f"quarantine at seq {report['quarantine_sequence']}, "
            f"{report['trials_covered']} trials in "
            f"[{report['first_trial_sequence']}, {report['last_trial_sequence']}], "
            f"restore at seq {report['restore_sequence']}"
        )

    review.check("3. quarantine covered every accepted trial", _custody)

    # The canary token is read from the quarantine root, never from the repository.
    tokens: tuple[str, ...] = ()
    extra_patterns: tuple[str, ...] = ()
    try:
        tokens = (read_canary_token(receipt_path=receipt_path),)
        quarantine_root = arguments.quarantine_root or load_receipt(receipt_path)["quarantine_root"]
        extra_patterns = (Path(quarantine_root).name,)
    except (OSError, ValueError) as error:
        print(f"NOTE  canary token unavailable ({error}); check 4 runs without it")

    # An empty loop is a silent pass, which is the one outcome a review must never produce: a
    # reviewer pointed at the wrong root, or run before any team started, would see checks 4-6
    # emit nothing at all and read the absence as approval. Count first, and say so.
    teams = _teams(team_root)
    nominations = [(team, candidate) for team in teams for candidate in _candidates(team)]

    def _something_to_scan() -> str:
        if not teams:
            raise FileNotFoundError(f"no team directories under {team_root}")
        if not nominations:
            raise FileNotFoundError(f"no nominated candidates under {team_root}")
        return f"{len(teams)} teams, {len(nominations)} nominated candidates"

    review.check("4-6. there is something to scan", _something_to_scan)

    # Check 4 -- every team's WHOLE workspace, not the archive they chose to freeze.
    for team in _teams(team_root):

        def _workspace(team: Path = team) -> str:
            scan = scan_workspace_for_blindness_violations(
                team,
                team_id=team.name,
                canary_tokens=tokens,
                extra_patterns=extra_patterns,
            )
            if scan.violations:
                raise ValueError(f"{len(scan.violations)} violations: {list(scan.violations[:8])}")
            if scan.unscanned:
                raise ValueError(
                    f"{len(scan.unscanned)} files too large to read; review by hand: "
                    f"{list(scan.unscanned[:8])}"
                )
            return f"{scan.files_scanned} files scanned, nothing found"

        review.check(f"4. {team.name} workspace scans clean", _workspace)

    # Check 5 -- every frozen candidate archive, on the narrower pre-flight surface.
    for team in _teams(team_root):
        for candidate in _candidates(team):

            def _archive(team: Path = team, candidate: Path = candidate) -> str:
                violations = scan_for_blindness_violations(candidate, team_id=team.name)
                if violations:
                    raise ValueError(f"{list(violations[:8])}")
                return "clean"

            review.check(f"5. {team.name}/{candidate.name} frozen archive scans clean", _archive)

    # Check 6 -- the declared neighbourhood is a real surface of the frozen source.
    for team in _teams(team_root):
        for candidate in _candidates(team):

            def _coordinates(candidate: Path = candidate) -> str:
                declaration = load_declaration(candidate / "neighbourhood.json")
                declaration.validate(int(config["research"]["neighbourhood_minimum_points"]))
                violations = verify_neighbourhood_coordinates(candidate, declaration)
                if violations:
                    raise ValueError(f"{list(violations)}")
                return f"{len(declaration.coordinates)} coordinates verify against strategy.py"

            review.check(f"6. {team.name}/{candidate.name} neighbourhood verifies", _coordinates)

    # Check 7 -- the phase-3 access tripwire. Reported, never treated as proof on its own.
    def _access() -> str:
        report = sealed_access_report(config["data"]["sealed_root"], baseline_path=baseline_path)
        if report["appeared"] or report["vanished"]:
            raise ValueError(
                f"sealed tree membership changed since arming: "
                f"appeared={report['appeared']} vanished={report['vanished']}"
            )
        if not report["atime_is_recorded"]:
            raise ValueError(
                f"mount options {report['mount_options']} include noatime; this control is "
                "INERT here and its empty result is not evidence of anything"
            )
        return f"read since arming: {report['accessed'] or 'nothing'}"

    review.check("7. sealed access tripwire", _access)

    print()
    if review.failures:
        print(f"INTEGRITY REVIEW FAILED: {len(review.failures)} checks")
        for name in review.failures:
            print(f"  - {name}")
        raise SystemExit(1)
    if review.skips:
        print(f"INTEGRITY REVIEW INCOMPLETE: {len(review.skips)} checks skipped")
        for name in review.skips:
            print(f"  - {name}")
        raise SystemExit(2)
    print("INTEGRITY REVIEW PASSED: every mechanical check found nothing")


if __name__ == "__main__":
    main()
