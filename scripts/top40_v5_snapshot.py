#!/usr/bin/env python3
"""Build, verify and preflight the canonical Top-40 V5 market snapshot.

``build`` and ``preflight`` are deliberately separate commands over the same artifacts. Building
proves the archives are the ones Binance published; the preflight proves the built snapshot can
actually support the decision grid the tournament will run on. Those are different claims, and
CUP-20 is the reason they are kept apart: it had 862 passing tests over a snapshot holding 21
boundaries that would have crashed every team on their first backtest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tomllib
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from crypto_trade.tournament.v5.layout import TOP40_V5_LAYOUT  # noqa: E402
from crypto_trade.tournament.v5.snapshot_preflight import (  # noqa: E402
    BLOCKING_KINDS,
    MAX_REPORTED_BOUNDARIES,
    assert_decision_grid_is_executable,
    check_decision_grid,
)
from crypto_trade.tournament.v5.universe import membership_shape  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / TOP40_V5_LAYOUT.tournament_root / "SNAPSHOT-BUILD.toml"


def _config() -> dict[str, object]:
    with CONFIG_PATH.open("rb") as handle:
        return tomllib.load(handle)


def _paths() -> tuple[Path, Path, Path]:
    config = _config()
    data = config["data"]
    return (
        ROOT / str(data["snapshot_dir"]),
        ROOT / str(data["manifest_path"]),
        ROOT / str(data["common_report_dir"]),
    )


def _load(snapshot_dir: Path) -> dict[str, pd.DataFrame]:
    return {
        name: pd.read_parquet(snapshot_dir / f"{name}.parquet")
        for name in ("bars", "funding", "mark_prices", "membership")
    }


def _build(args: argparse.Namespace) -> int:
    from crypto_trade.tournament.snapshot import build_snapshot

    snapshot_dir, manifest_path, common_reports = _paths()
    manifest = build_snapshot(
        CONFIG_PATH,
        snapshot_dir,
        manifest_path,
        common_reports,
        resume=not args.no_resume,
    )
    digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    print(
        f"snapshot built: files={len(manifest['files'])} "
        f"archives={manifest['sources']['archive_count']} manifest_sha256={digest}"
    )
    return 0


def _preflight(args: argparse.Namespace) -> int:
    config = _config()
    snapshot_dir, _, _ = _paths()
    frames = _load(snapshot_dir)
    splits = config["splits"]
    data = config["data"]

    start = str(splits["in_sample_start"])
    end_exclusive = str(data["hard_end_exclusive"])

    shape = membership_shape(frames["membership"], size=int(config["universe"]["size"]))
    print(f"membership: {shape}")

    # Always compute the full report and write it before deciding whether to fail. Raising first
    # would leave the previous run's report on disk next to a failed build, which reads as a pass.
    report = check_decision_grid(
        frames["bars"],
        frames["mark_prices"],
        frames["funding"],
        frames["membership"],
        start=start,
        end_exclusive=end_exclusive,
        limit=args.limit,
    )

    payload = dict(report.as_dict())
    payload["membership_shape"] = shape
    destination = ROOT / TOP40_V5_LAYOUT.snapshot_preflight_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        f"preflight: ok={report.ok} boundaries={report.boundaries} "
        f"symbols={report.membership_symbols} "
        f"blocking={len(report.blocking)} advisory={len(report.advisory)} "
        f"counts={report.counts_by_kind()}"
    )
    for finding in (*report.blocking[:5], *report.advisory[:5]):
        severity = "BLOCK" if finding.kind in BLOCKING_KINDS else "advise"
        print(f"  [{severity}] {finding.kind} {finding.boundary} {list(finding.symbols)[:8]}")
    print(f"written: {destination.relative_to(ROOT)}")

    if report.ok or args.report_only:
        return 0 if report.ok else 1
    assert_decision_grid_is_executable(
        frames["bars"],
        frames["mark_prices"],
        frames["funding"],
        frames["membership"],
        start=start,
        end_exclusive=end_exclusive,
        limit=args.limit,
    )
    return 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build", help="acquire, verify and publish the snapshot")
    build.add_argument(
        "--no-resume",
        action="store_true",
        help="reacquire every archive instead of reusing checksum-verified cached copies",
    )
    build.set_defaults(handler=_build)

    preflight = commands.add_parser(
        "preflight", help="assert the built snapshot supports its own decision grid"
    )
    preflight.add_argument(
        "--limit",
        type=int,
        default=MAX_REPORTED_BOUNDARIES,
        help="maximum offending boundaries to record per finding kind",
    )
    preflight.add_argument(
        "--report-only",
        action="store_true",
        help="write the report and exit non-zero on findings instead of raising",
    )
    preflight.set_defaults(handler=_preflight)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    return int(arguments.handler(arguments))


if __name__ == "__main__":
    raise SystemExit(main())
