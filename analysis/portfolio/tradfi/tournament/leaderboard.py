"""Team IS runs, canonical reproduction, and Stage-1 ranking.

One evaluator code path serves both the team-facing ``team-run`` and the orchestrator's
canonical rerun: ``run_team`` computes, ``write_team_artifacts`` persists, and
``reproduce_team`` re-runs from the SHA-verified frozen bundle and demands byte-identical
artifacts. Reported numbers ARE canonical numbers by construction — the freeze reads them
from ``out/``, never from prose.

Stage-1 ranking (locked): net IS Sharpe @1× cost, ties broken by 2×-cost Sharpe, then by
max drawdown (less negative wins). The Critic PASS gate is applied by the orchestrator via
the team list passed to ``build_stage1``.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from tournament import constants as tc  # noqa: E402
from tournament import engine as te  # noqa: E402
from tournament import protocol as tp  # noqa: E402


class ReproductionError(RuntimeError):
    """Canonical rerun did not reproduce the frozen artifacts byte-identically."""


def _net_csv_text(net: pd.Series) -> str:
    # %.17g: full float64 precision — pandas 3.0's default truncates the 17th significant
    # digit, which would break the bit-exact IS-replay check in holdout._check_is_replay
    return net.rename("net").to_csv(index_label="date", float_format="%.17g")


def run_team(
    team_dir: Path,
    snapshot_dir: Path = tc.SNAPSHOT_DIR,
    manifest_path: Path = tc.MANIFEST_PATH,
) -> tuple[dict, pd.Series]:
    """Deterministic IS scoring of a team bundle -> (metrics payload, 1x net series).

    The payload carries NO timestamps — byte-stable JSON so reproduction is a byte-compare.
    """
    pn, aux = te.load_is_panels(snapshot_dir, manifest_path)
    mod = tp.load_strategy(team_dir)
    raw = te.conform_raw(mod.build_raw_weights(te.team_view(pn), aux), pn)
    net1, w1 = te.net_series(raw, pn["ret_fwd"], cost_mult=1.0)
    net2, w2 = te.net_series(raw, pn["ret_fwd"], cost_mult=2.0)
    m1 = te.evaluate(net1, w1, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
    m2 = te.evaluate(net2, w2, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
    payload = {
        "schema": 1,
        "team_id": Path(team_dir).name,
        "window": {"lo": str(tc.TRN_IS_START.date()), "hi_exclusive": str(tc.TRN_IS_HI.date())},
        "metrics": {"1x": m1.to_dict(), "2x": m2.to_dict()},
    }
    tp.purge_team_modules()
    return payload, net1


def write_team_artifacts(team_dir: Path, payload: dict, net1: pd.Series) -> dict:
    out = Path(team_dir) / "out"
    out.mkdir(parents=True, exist_ok=True)
    (out / "is_metrics.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    (out / "net_is.csv").write_text(_net_csv_text(net1))
    return payload


def reproduce_team(
    team_dir: Path,
    snapshot_dir: Path = tc.SNAPSHOT_DIR,
    manifest_path: Path = tc.MANIFEST_PATH,
) -> dict:
    """SHA-verify the frozen bundle, rerun, and byte-compare every canonical artifact.
    Returns the (now-proven) metrics payload; raises ``ReproductionError`` on ANY drift."""
    team_dir = Path(team_dir)
    sub = tp.check_submission_shas(team_dir)
    payload, net1 = run_team(team_dir, snapshot_dir, manifest_path)
    want_json = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    have_json = (team_dir / "out" / "is_metrics.json").read_text()
    if want_json != have_json:
        raise ReproductionError(f"{team_dir.name}: is_metrics.json does not reproduce")
    want_csv = _net_csv_text(net1)
    have_csv = (team_dir / "out" / "net_is.csv").read_text()
    if want_csv != have_csv:
        raise ReproductionError(f"{team_dir.name}: net_is.csv does not reproduce")
    if sub["reported"] != payload["metrics"]:
        raise ReproductionError(f"{team_dir.name}: submission.json reported metrics drifted")
    if sub["net_is_csv_sha256"] != tp._sha256_bytes(want_csv.encode()):
        raise ReproductionError(f"{team_dir.name}: net_is.csv sha mismatch vs submission.json")
    return payload


def stage1_rank(entries: list[dict]) -> list[dict]:
    """Rank by net IS Sharpe @1x; ties: 2x Sharpe, then maxDD (less negative). NaN sinks."""

    def _f(x) -> float:
        try:
            v = float(x)
        except (TypeError, ValueError):
            return -math.inf
        return v if math.isfinite(v) else -math.inf

    ranked = sorted(
        entries,
        key=lambda e: (-_f(e["sharpe_1x"]), -_f(e["sharpe_2x"]), -_f(e["maxdd"])),
    )
    for i, e in enumerate(ranked, start=1):
        e["rank"] = i
    return ranked


def build_stage1(
    team_ids: list[str],
    teams_dir: Path = tc.TEAMS_DIR,
    snapshot_dir: Path = tc.SNAPSHOT_DIR,
    manifest_path: Path = tc.MANIFEST_PATH,
    *,
    advance: int = 4,
) -> dict:
    """Canonically rerun every Critic-passed team; rank; mark the top-``advance`` finalists.
    A reproduction failure is recorded (status=reproduction-failure) and excluded from ranking.
    """
    entries: list[dict] = []
    failures: list[dict] = []
    for team_id in team_ids:
        td = tc.team_dir(team_id, teams_dir)
        try:
            payload = reproduce_team(td, snapshot_dir, manifest_path)
        except (tp.SubmissionError, ReproductionError) as e:
            failures.append({"team_id": team_id, "error": str(e)})
            continue
        m1, m2 = payload["metrics"]["1x"], payload["metrics"]["2x"]
        entries.append(
            {
                "team_id": team_id,
                "sharpe_1x": m1["sharpe"],
                "sharpe_2x": m2["sharpe"],
                "maxdd": m1["maxdd"],
                "ann_turnover": m1["ann_turnover"],
                "regime_sharpe": m1["regime_sharpe"],
                "median_names_long": m1["median_names_long"],
                "median_names_short": m1["median_names_short"],
            }
        )
    ranked = stage1_rank(entries)
    for e in ranked:
        e["finalist"] = e["rank"] <= advance
    return {"ranked": ranked, "failures": failures, "advance": advance}
