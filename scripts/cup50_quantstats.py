#!/usr/bin/env python3
"""Generate IS, OOS, and continuous QuantStats reports for the CUP-50 winner."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import pandas as pd

from crypto_trade.backtest_report import generate_html_report
from crypto_trade.cup50.availability import load_unavailability_audit
from crypto_trade.cup50.config import IS_START, OOS_END, OOS_START
from crypto_trade.cup50.paper import verify_desk_authority
from crypto_trade.cup50.replay import (
    apply_strategy_parameters,
    load_strategy_module,
    run_candidate,
    strategy_from_module,
)
from crypto_trade.cup50.scoring import score_point
from crypto_trade.cup50.snapshot import load_snapshot, stitch_snapshots

TEAM_ID = "team-02"
NORMAL_COST_MULTIPLIER = 1


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _daily_returns(bar_returns: pd.Series) -> pd.Series:
    values = pd.to_numeric(bar_returns, errors="raise").astype(float)
    if not isinstance(values.index, pd.DatetimeIndex) or values.index.tz is None:
        raise ValueError("CUP-50 returns need a timezone-aware DatetimeIndex")
    if not values.index.is_monotonic_increasing or not values.index.is_unique:
        raise ValueError("CUP-50 returns need a unique ascending index")
    if not values.map(math.isfinite).all() or (values <= -1.0).any():
        raise ValueError("CUP-50 returns contain an invalid value")
    daily = (1.0 + values).resample("1D").prod() - 1.0
    calendar = pd.date_range(
        IS_START.normalize(), OOS_END.normalize(), freq="D", inclusive="left", tz="UTC"
    )
    daily = daily.reindex(calendar, fill_value=0.0)
    daily.name = "net_return"
    return daily


def _statistics(returns: pd.Series) -> dict[str, float | int | str]:
    if returns.empty:
        raise ValueError("cannot summarize an empty report window")
    wealth = (1.0 + returns).cumprod()
    drawdown = 1.0 - wealth / wealth.cummax()
    years = len(returns) / 365.0
    total = float(wealth.iloc[-1] - 1.0)
    annual = float((1.0 + total) ** (1.0 / years) - 1.0)
    volatility = float(returns.std(ddof=1) * math.sqrt(365.0))
    sharpe = (
        float(returns.mean() / returns.std(ddof=1) * math.sqrt(365.0))
        if returns.std(ddof=1) > 0
        else 0.0
    )
    return {
        "start": returns.index.min().date().isoformat(),
        "end": returns.index.max().date().isoformat(),
        "days": int(len(returns)),
        "total_return": total,
        "annualized_return": annual,
        "annualized_volatility": volatility,
        "daily_sharpe_365": sharpe,
        "maximum_drawdown": float(drawdown.max()),
    }


def generate(repository: Path, destination: Path) -> dict[str, object]:
    corrected_release = repository / "reports-cup50" / "corrected-leaderboard.json"
    release = json.loads(corrected_release.read_text())
    if release.get("winner_team_id") != TEAM_ID:
        raise ValueError("corrected CUP-50 release does not name Team 02 as winner")

    team_root = repository / "tournament" / "cup50" / "teams" / TEAM_ID
    authority_path = repository / "paper-cup50" / TEAM_ID / "authority.json"
    authority = verify_desk_authority(
        authority_path,
        release_path=corrected_release,
        winner_bundle=team_root,
    )
    nomination = json.loads(
        (repository / "tournament" / "cup50" / "nominations" / f"{TEAM_ID}.json").read_text()
    )
    evidence = json.loads(
        (
            repository
            / "tournament"
            / "cup50"
            / "private"
            / "point-evidence"
            / f"{TEAM_ID}-p00.json"
        ).read_text()
    )

    strategy = strategy_from_module(load_strategy_module(team_root / "strategy.py"))
    apply_strategy_parameters(strategy, nomination["centre"])
    snapshot = stitch_snapshots(
        load_snapshot(repository / "data" / "cup50" / "is"),
        load_snapshot(repository / "data" / "cup50" / "sealed"),
    )
    audit_path = (
        repository / "tournament" / "cup50" / "organizer-recovery-unavailability.json"
    )
    replay = run_candidate(
        strategy,
        snapshot=snapshot,
        start=IS_START,
        end=OOS_END,
        seed=2,
        terminal=False,
        unavailability=load_unavailability_audit(audit_path),
        record_events=False,
    )
    observed_score = score_point(replay.costs).score
    expected_score = float(evidence["score"]["score"])
    if observed_score != expected_score:
        raise ValueError(
            f"winner replay parity failed: {observed_score!r} != {expected_score!r}"
        )

    daily = _daily_returns(replay.costs[NORMAL_COST_MULTIPLIER].returns["net_return"])
    periods = {
        "is": daily.loc[(daily.index >= IS_START) & (daily.index < OOS_START)],
        "oos": daily.loc[(daily.index >= OOS_START) & (daily.index < OOS_END)],
        "full": daily.loc[(daily.index >= IS_START) & (daily.index < OOS_END)],
    }

    outputs = {
        name: destination / f"cup50-{TEAM_ID}-{name}-quantstats.html" for name in periods
    }
    daily_path = destination / f"cup50-{TEAM_ID}-daily-returns.csv"
    manifest_path = destination / "manifest.json"
    existing = [path for path in (*outputs.values(), daily_path, manifest_path) if path.exists()]
    if existing:
        raise FileExistsError(f"QuantStats output already exists: {existing[0]}")
    destination.mkdir(parents=True, exist_ok=True)

    daily_frame = daily.rename("net_return").to_frame()
    daily_frame.index.name = "date"
    daily_frame["period"] = "IS"
    daily_frame.loc[daily_frame.index >= OOS_START, "period"] = "OOS"
    daily_frame.reset_index().to_csv(
        daily_path, index=False, lineterminator="\n", float_format="%.17g"
    )

    for name, returns in periods.items():
        quantstats_returns = returns.copy()
        quantstats_returns.index = quantstats_returns.index.tz_convert(None)
        generate_html_report(
            quantstats_returns,
            outputs[name],
            title=f"CUP-50 Team 02 corrected winner — {name.upper()} — 1x net",
            compounded=True,
        )

    manifest: dict[str, object] = {
        "schema_version": 1,
        "namespace": "cup50-quantstats",
        "team_id": TEAM_ID,
        "candidate_id": "centre-v1",
        "continuous_replay": True,
        "cost_multiplier": NORMAL_COST_MULTIPLIER,
        "fee_bps_per_side": 5.0,
        "slippage_bps_per_side": 2.5,
        "score_parity": True,
        "centre_score": observed_score,
        "corrected_release_sha256": _sha256(corrected_release),
        "paper_authority_sha256": authority["authority_sha256"],
        "source_bundle_sha256": authority["winner_bundle_sha256"],
        "nomination_sha256": authority["nomination_sha256"],
        "snapshot_sha256": snapshot.manifest_sha256,
        "unavailability_audit_sha256": _sha256(audit_path),
        "daily_returns": {"path": daily_path.name, "sha256": _sha256(daily_path)},
        "reports": {
            name: {
                "path": path.name,
                "sha256": _sha256(path),
                "statistics": _statistics(periods[name]),
            }
            for name, path in outputs.items()
        },
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports-cup50/team-02/quantstats"),
    )
    arguments = parser.parse_args()
    repository = arguments.repository.resolve()
    destination = (
        arguments.output
        if arguments.output.is_absolute()
        else repository / arguments.output
    ).resolve()
    manifest = generate(repository, destination)
    print(
        json.dumps(
            {
                "status": "generated",
                "team_id": manifest["team_id"],
                "output": str(destination),
                "reports": sorted(manifest["reports"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
