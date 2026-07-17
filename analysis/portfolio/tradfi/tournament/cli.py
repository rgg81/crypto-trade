"""tradfi-cup-01 CLI — the single front door for teams AND the orchestrator.

  uv run python analysis/portfolio/tradfi/tournament/cli.py <command> [...]

Team-facing:      team-run --team NN | audit --team NN
Orchestrator:     build-snapshot | verify-snapshot | init-teams | register-family |
                  freeze --team NN --family-id ID | leaderboard --teams a,b,c |
                  run-holdout --team NN --confirm-holdout [...] | final-report
Every state-changing command appends one line to tournament/tradfi/journal.jsonl.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from tournament import constants as tc  # noqa: E402
from tournament import harness as th  # noqa: E402
from tournament import holdout as thold  # noqa: E402
from tournament import leaderboard as tlb  # noqa: E402
from tournament import protocol as tp  # noqa: E402
from tournament import snapshot as tsnap  # noqa: E402

BOOTSTRAP_TEMPLATE = """\
# {team_id} — tradfi-cup-01 boot card

You are one of ten independent teams. Read, in order:
1. `tournament/tradfi/CHARTER.md`  — the rules. Binding.
2. `tournament/tradfi/config.toml` — machine-readable parameters.
3. `tournament/tradfi/FAMILY-MENU.md` — seeded mechanism families (yours must be registered
   and approved in `tournament/tradfi/registry.jsonl` before you build).

Workspace: this directory ONLY. Data: the frozen IS snapshot `tournament/tradfi/data_is/`
reached exclusively through the evaluator (`cli.py team-run` / `tournament.engine`).

Deliverables checklist (all required to freeze):
- [ ] research_brief.md   — mechanism, economic rationale, falsifier, parameter plan
- [ ] strategy.py         — `build_raw_weights(pn, aux)` (+ optional helper .py files)
- [ ] test_strategy.py    — team-owned tests incl. a future-corruption self-check
- [ ] experiments.jsonl   — append-only: one line per material experiment, BEFORE reading
                            its result
- [ ] is_report.md        — numbers ONLY from `team-run` output (out/is_metrics.json)
- [ ] provenance.md       — what you read, what you imported, independence statement
- [ ] PASS from `cli.py audit --team {team_id}`
Then the orchestrator freezes: `cli.py freeze --team {team_id} --family-id <id>`.
"""


def _cmd_build_snapshot(args) -> int:
    commit = ""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:  # noqa: BLE001 — commit hash is best-effort provenance
        pass
    manifest = tsnap.build_is_snapshot(Path(args.src), source_commit=commit)
    tc.journal("snapshot_built", n_files=manifest["n_files"], files_sha256=manifest["files_sha256"])
    print(f"snapshot: {manifest['n_files']} files, digest {manifest['files_sha256'][:16]}…")
    return 0


def _cmd_verify_snapshot(_args) -> int:
    m = tsnap.verify_manifest()
    print(f"snapshot OK: {m['n_files']} files verified, IS end {m['is_end']}")
    return 0


def _cmd_init_teams(_args) -> int:
    for team_id in tc.TEAM_IDS:
        td = tc.TEAMS_DIR / team_id
        (td / "out").mkdir(parents=True, exist_ok=True)
        boot = td / "BOOTSTRAP.md"
        if not boot.exists():
            boot.write_text(BOOTSTRAP_TEMPLATE.format(team_id=team_id))
        exp = td / "experiments.jsonl"
        if not exp.exists():
            exp.write_text("")
    tc.CRITIC_DIR.mkdir(parents=True, exist_ok=True)
    tc.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    tc.journal("teams_initialized", teams=list(tc.TEAM_IDS))
    print(f"initialized {len(tc.TEAM_IDS)} team dirs under {tc.TEAMS_DIR}")
    return 0


def _cmd_register_family(args) -> int:
    status = "vetoed" if args.veto else "approved"
    entry = {
        "team_id": args.team,
        "family_id": args.family_id,
        "summary": args.summary,
        "status": status,
        "reason": args.reason,
    }
    with tc.REGISTRY_PATH.open("a") as f:
        f.write(json.dumps({"ts_event": "family_registration", **entry}, sort_keys=True) + "\n")
    tc.journal("family_registration", **entry)
    print(f"{args.team}: family {args.family_id!r} {status.upper()}")
    return 0


def _cmd_team_run(args) -> int:
    td = tc.team_dir(args.team)
    payload, net1 = tlb.run_team(td)
    tlb.write_team_artifacts(td, payload, net1)
    m1, m2 = payload["metrics"]["1x"], payload["metrics"]["2x"]
    print(json.dumps({"1x": m1, "2x": m2}, indent=2, sort_keys=True))
    print(
        f"\n{args.team}: IS Sharpe {m1['sharpe']:+.3f} @1x / {m2['sharpe']:+.3f} @2x  "
        f"maxDD {m1['maxdd'] * 100:.1f}%  breadth L/S "
        f"{m1['median_names_long']:.0f}/{m1['median_names_short']:.0f}"
    )
    return 0


def _cmd_audit(args) -> int:
    td = tc.team_dir(args.team)
    rep = th.audit_strategy(td, n_truncations=args.n_truncations)
    (td / "out").mkdir(parents=True, exist_ok=True)
    (td / "out" / "harness.json").write_text(
        json.dumps(rep.to_dict(), indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(rep.to_dict(), indent=2, sort_keys=True))
    print(f"\n{args.team}: harness {'PASS' if rep.ok else 'FAIL'}")
    return 0 if rep.ok else 1


def _cmd_freeze(args) -> int:
    td = tc.team_dir(args.team)
    metrics_path = td / "out" / "is_metrics.json"
    if not metrics_path.exists():
        print(f"{args.team}: no out/is_metrics.json — run team-run first")
        return 1
    rep = th.audit_strategy(td)  # fresh, full-strength audit at freeze time
    (td / "out" / "harness.json").write_text(
        json.dumps(rep.to_dict(), indent=2, sort_keys=True) + "\n"
    )
    if not rep.ok:
        print(f"{args.team}: harness FAIL — cannot freeze\n" + "\n".join(rep.violations))
        return 1
    payload = json.loads(metrics_path.read_text())
    net_csv = (td / "out" / "net_is.csv").read_bytes()
    sub = tp.write_submission(
        td,
        family_id=args.family_id,
        reported=payload["metrics"],
        net_is_csv_sha256=tp._sha256_bytes(net_csv),
        harness="PASS",
    )
    tc.journal(
        "team_frozen",
        team_id=args.team,
        family_id=args.family_id,
        n_sources=len(sub["sources_sha256"]),
        sharpe_1x=payload["metrics"]["1x"]["sharpe"],
    )
    print(f"{args.team}: FROZEN (family {args.family_id}, {len(sub['sources_sha256'])} files)")
    return 0


def _cmd_leaderboard(args) -> int:
    team_ids = args.teams.split(",") if args.teams else list(tc.TEAM_IDS)
    board = tlb.build_stage1(team_ids, advance=args.advance)
    tc.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (tc.RESULTS_DIR / "stage1_leaderboard.json").write_text(
        json.dumps(board, indent=2, sort_keys=True) + "\n"
    )
    lines = [
        "# tradfi-cup-01 — Stage-1 leaderboard (net IS Sharpe @1x, critic-gated)",
        "",
        "| rank | team | IS Sharpe 1x | IS Sharpe 2x | maxDD | ann. turnover | finalist |",
        "|---|---|---|---|---|---|---|",
    ]
    for e in board["ranked"]:
        lines.append(
            f"| {e['rank']} | {e['team_id']} | {e['sharpe_1x']:+.3f} | {e['sharpe_2x']:+.3f} "
            f"| {e['maxdd'] * 100:.1f}% | {e['ann_turnover']:.1f} "
            f"| {'YES' if e['finalist'] else ''} |"
        )
    for f in board["failures"]:
        lines.append(f"\nFAILED reproduction: {f['team_id']} — {f['error']}")
    (tc.RESULTS_DIR / "stage1_leaderboard.md").write_text("\n".join(lines) + "\n")
    tc.journal(
        "stage1_leaderboard",
        teams=team_ids,
        finalists=[e["team_id"] for e in board["ranked"] if e["finalist"]],
        failures=[f["team_id"] for f in board["failures"]],
    )
    print("\n".join(lines))
    return 0


def _cmd_run_holdout(args) -> int:
    label = args.label
    if label is None:
        parts = []
        if not args.funding:
            parts.append("nofunding")
        if args.cost_mult != 1.0:
            parts.append(f"cost{args.cost_mult:g}x")
        if args.exclude:
            parts.append("ex-" + "-".join(args.exclude.split(",")))
        label = "_".join(parts) if parts else "canonical"
    result, _net = thold.evaluate_holdout(
        args.team,
        confirm=args.confirm_holdout,
        apply_funding=args.funding,
        cost_mult=args.cost_mult,
        exclude=tuple(args.exclude.split(",")) if args.exclude else (),
        label=label,
        results_dir=tc.RESULTS_DIR,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _cmd_final_report(_args) -> int:
    rows = []
    for p in sorted(tc.RESULTS_DIR.glob("holdout_team-*.json")):
        r = json.loads(p.read_text())
        if r["label"] == "canonical":
            rows.append(r)
    rows.sort(key=lambda r: -(r["metrics"]["sharpe"] or float("-inf")))
    lines = [
        "# tradfi-cup-01 — Stage-2 sealed holdout (2024-07-01 .. 2026-06-30, funding on)",
        "",
        "| rank | team | holdout Sharpe | maxDD | ann. turnover | IS-replay |",
        "|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows, start=1):
        m = r["metrics"]
        lines.append(
            f"| {i} | {r['team_id']} | {m['sharpe']:+.3f} | {m['maxdd'] * 100:.1f}% "
            f"| {m['ann_turnover']:.1f} | {'OK' if r['is_replay_identical'] else 'MISMATCH'} |"
        )
    if rows:
        lines.append(f"\n**WINNER: {rows[0]['team_id']}** (best net holdout Sharpe, funding on)")
    (tc.RESULTS_DIR / "stage2_holdout_report.md").write_text("\n".join(lines) + "\n")
    (tc.RESULTS_DIR / "stage2_holdout_report.json").write_text(
        json.dumps(rows, indent=2, sort_keys=True) + "\n"
    )
    tc.journal("stage2_report", winner=rows[0]["team_id"] if rows else None)
    print("\n".join(lines))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tradfi-cup-01")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("build-snapshot", help="freeze the IS snapshot from a full data dir")
    p.add_argument("--src", default=str(ct_root_data()))
    p.set_defaults(fn=_cmd_build_snapshot)

    sub.add_parser("verify-snapshot").set_defaults(fn=_cmd_verify_snapshot)
    sub.add_parser("init-teams").set_defaults(fn=_cmd_init_teams)

    p = sub.add_parser("register-family")
    p.add_argument("--team", required=True)
    p.add_argument("--family-id", required=True)
    p.add_argument("--summary", default="")
    p.add_argument("--veto", action="store_true")
    p.add_argument("--reason", default="")
    p.set_defaults(fn=_cmd_register_family)

    p = sub.add_parser("team-run", help="IS run @1x and @2x cost; writes out/ artifacts")
    p.add_argument("--team", required=True)
    p.set_defaults(fn=_cmd_team_run)

    p = sub.add_parser("audit", help="leak harness + static scan")
    p.add_argument("--team", required=True)
    p.add_argument("--n-truncations", type=int, default=8)
    p.set_defaults(fn=_cmd_audit)

    p = sub.add_parser("freeze", help="full audit + SHA-bind the submission")
    p.add_argument("--team", required=True)
    p.add_argument("--family-id", required=True)
    p.set_defaults(fn=_cmd_freeze)

    p = sub.add_parser("leaderboard", help="canonical reruns + Stage-1 ranking")
    p.add_argument("--teams", default="", help="comma list of Critic-PASSED team ids")
    p.add_argument("--advance", type=int, default=4)
    p.set_defaults(fn=_cmd_leaderboard)

    p = sub.add_parser("run-holdout", help="ORCHESTRATOR ONLY — sealed Stage-2 evaluation")
    p.add_argument("--team", required=True)
    p.add_argument("--confirm-holdout", action="store_true")
    p.add_argument("--no-funding", dest="funding", action="store_false")
    p.add_argument("--cost-mult", type=float, default=1.0)
    p.add_argument("--exclude", default="", help="comma list, e.g. PAYPUSDT")
    p.add_argument("--label", default=None)
    p.set_defaults(fn=_cmd_run_holdout)

    sub.add_parser("final-report").set_defaults(fn=_cmd_final_report)

    args = ap.parse_args(argv)
    return args.fn(args)


def ct_root_data() -> Path:
    import core_tradfi as ct

    return ct._ROOT / "data"


if __name__ == "__main__":
    raise SystemExit(main())
