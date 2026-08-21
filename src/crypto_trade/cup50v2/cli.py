"""Unified CUP-50 v2 command line lifecycle."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import math
import os
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from crypto_trade.cup50v2.acquisition import acquire_execution_gaps, acquire_terminal_gaps
from crypto_trade.cup50v2.activation import build_activation_record
from crypto_trade.cup50v2.availability import load_unavailability_audit
from crypto_trade.cup50v2.config import (
    IS_START,
    OOS_END,
    OOS_START,
    TEAM_IDS,
    active_policy,
    load_config,
)
from crypto_trade.cup50v2.falsifiers import (
    corruption_cut_points,
    determinism,
    future_corruption,
    sign_inversion,
)
from crypto_trade.cup50v2.isolation import (
    export_evaluator_bundle,
    export_protocol_bundle,
    require_image_digest,
    require_isolation_available,
    scan_research_root,
)
from crypto_trade.cup50v2.journal import append_record, read_records
from crypto_trade.cup50v2.lifecycle import (
    CandidateFailureError,
    atomic_release,
    compile_leaderboard,
    freeze_field,
    integrity_review,
    observation_order,
    observe_point,
    recover_interrupted_points,
    restart_interrupted_points,
    start_observation_batch,
    verify_field,
)
from crypto_trade.cup50v2.neighbourhood import (
    Dimension,
    freeze_nomination,
    generate_neighbourhood,
    reject_inert_dimensions,
    verify_nomination,
)
from crypto_trade.cup50v2.paper import (
    digest_markdown,
    first_boundary_after,
    freeze_desk_authority,
    healthcheck,
    verify_parity,
)
from crypto_trade.cup50v2.qualification import (
    evaluate_eligibility,
    verify_certificate,
    verify_risk_declaration,
)
from crypto_trade.cup50v2.quarantine import create_receipt, verify_receipt
from crypto_trade.cup50v2.replay import (
    StrategyFailureError,
    apply_strategy_parameters,
    decision_grid,
    generate_targets,
    load_strategy_module,
    require_execution_coverage,
    run_candidate,
    strategy_from_module,
)
from crypto_trade.cup50v2.research_snapshot import (
    EXECUTION_MODE,
    research_snapshot_from_team_visible,
)
from crypto_trade.cup50v2.reuse import reuse_acquisition
from crypto_trade.cup50v2.scoring import (
    round_half_even,
    rounded_neighbourhood,
    score_in_sample_point,
    score_neighbourhood,
    score_point,
)
from crypto_trade.cup50v2.snapshot import (
    load_snapshot,
    stitch_snapshots,
    verify_semantic_coverage,
    write_split_snapshots,
    write_team_visible_snapshot,
)
from crypto_trade.cup50v2.trials import (
    TrialBinding,
    nomination_trial_binding,
    record_trial_result,
    register_trial,
    resolve_trial_binding,
    source_bundle_digest,
)
from crypto_trade.cup50v2.universe import (
    build_membership,
    canonical_daily_quote_volume,
    classify_current_exchange_contracts,
    derive_listing_episodes,
    episode_eligibility,
    first_full_boundary,
    pure_crypto_symbols,
    require_exact_membership,
    weekly_reconstitution_times,
)


def _json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text())


def _write_json(path: str | Path, payload: object) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")


def _key(path: str | Path) -> bytes:
    value = Path(path).read_bytes().strip()
    if len(value) < 32:
        raise ValueError("field signing key must contain at least 32 bytes")
    return value


def _build(arguments: argparse.Namespace) -> Mapping[str, object]:
    acquisition = Path(arguments.acquisition)
    acquisition_manifest = _json(arguments.acquisition_manifest)
    classification_audit = _json(arguments.classification_audit)
    if (
        classification_audit.get("schema_version") != 1
        or classification_audit.get("namespace") != "cup50v2"
        or classification_audit.get("policy_id") != "pure-crypto-fail-closed-v1"
    ):
        raise ValueError("historical classification audit is not a CUP-50 v2 policy artifact")
    historical_classifications = {
        str(symbol): str(entry["classification"])
        for symbol, entry in classification_audit.get("entries", {}).items()
    }
    entries = acquisition_manifest.get("files", [])
    by_name = {str(entry.get("name")): entry for entry in entries if isinstance(entry, dict)}
    required_files = {
        "bars": acquisition / "bars.parquet",
        "funding": acquisition / "funding.parquet",
        "mark_prices": acquisition / "mark_prices.parquet",
        "contract_metadata": acquisition / "contract_metadata.parquet",
    }
    for name, path in required_files.items():
        entry = by_name.get(name)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if entry is None or digest != entry.get("sha256"):
            raise ValueError(f"acquisition file lacks its verified manifest binding: {name}")
    bars = pd.read_parquet(acquisition / "bars.parquet")
    funding = pd.read_parquet(acquisition / "funding.parquet")
    marks = pd.read_parquet(acquisition / "mark_prices.parquet")
    metadata = pd.read_parquet(acquisition / "contract_metadata.parquet")
    metadata = classify_current_exchange_contracts(
        metadata, historical_classifications=historical_classifications
    )
    allowed = pure_crypto_symbols(metadata)
    volume = canonical_daily_quote_volume(bars, end=OOS_END)
    universe_policy = active_policy().universe
    boundaries = weekly_reconstitution_times(
        volume.index.min() + pd.Timedelta(days=universe_policy.lookback_days), OOS_END
    )
    eligible = episode_eligibility(
        derive_listing_episodes(bars),
        boundaries,
    ).reindex(index=pd.DatetimeIndex(boundaries), columns=volume.columns, fill_value=False)
    eligible.loc[:, [column for column in volume.columns if str(column) not in allowed]] = False
    membership = build_membership(
        volume,
        eligible=eligible,
        reconstitution_times=boundaries,
    )
    measured = first_full_boundary(membership)
    if measured != IS_START:
        raise ValueError(
            f"first full Top-{universe_policy.target_size} boundary drifted: "
            f"{measured} != {IS_START}"
        )
    membership = membership.loc[
        pd.to_datetime(membership["reconstitution_time"], utc=True) >= IS_START
    ].reset_index(drop=True)
    exact_boundaries = weekly_reconstitution_times(IS_START, OOS_END)
    require_exact_membership(membership, exact_boundaries)
    members = set(membership["symbol"].astype(str))
    audit = {
        "schema_version": 1,
        "namespace": "cup50v2",
        "policy_id": "pure-crypto-fail-closed-v1",
        "status": "passed",
        "members_audited": len(members),
        "members": sorted(members),
        "positive_classifications": len(allowed),
        "classification_audit_sha256": hashlib.sha256(
            Path(arguments.classification_audit).read_bytes()
        ).hexdigest(),
        "unknown_fail_closed": sorted(
            set(metadata.loc[metadata["classification"].eq("unknown"), "symbol"].astype(str))
        ),
        "acquisition_manifest_sha256": hashlib.sha256(
            Path(arguments.acquisition_manifest).read_bytes()
        ).hexdigest(),
    }
    _write_json(arguments.pure_crypto_audit_output, audit)
    bars = bars.loc[bars["symbol"].astype(str).isin(members)].reset_index(drop=True)
    funding = funding.loc[funding["symbol"].astype(str).isin(members)].reset_index(drop=True)
    marks = marks.loc[marks["symbol"].astype(str).isin(members)].reset_index(drop=True)
    metadata = metadata.loc[metadata["symbol"].astype(str).isin(members)].reset_index(drop=True)
    research, sealed = write_split_snapshots(
        bars,
        funding,
        marks,
        membership,
        metadata,
        is_root=arguments.is_root,
        sealed_root=arguments.sealed_root,
    )
    team_visible = write_team_visible_snapshot(
        load_snapshot(research.root), root=arguments.team_is_root
    )
    return {
        "status": "built",
        "is_manifest": str(research.manifest),
        "sealed_manifest": str(sealed.manifest),
        "team_is_manifest": str(team_visible.manifest),
        "is_start": measured.isoformat(),
        "pure_crypto_audit": arguments.pure_crypto_audit_output,
    }


def _acquire_reuse(arguments: argparse.Namespace) -> Mapping[str, object]:
    record = reuse_acquisition(arguments.source, arguments.destination, receipt=arguments.receipt)
    return {
        "command": "acquire-reuse",
        "files": len(record["files"]),
        "receipt_sha256": record["receipt_sha256"],
        "source_manifest_sha256": record["source_manifest_sha256"],
    }


def _acquire(arguments: argparse.Namespace) -> Mapping[str, object]:
    return acquire_terminal_gaps(
        source_root=arguments.source_acquisition,
        source_manifest=arguments.source_manifest,
        membership_path=arguments.membership,
        destination=arguments.output,
        workers=arguments.workers,
    )


def _acquire_coverage(arguments: argparse.Namespace) -> Mapping[str, object]:
    return acquire_execution_gaps(
        source_root=arguments.source_acquisition,
        source_manifest=arguments.source_manifest,
        is_root=arguments.is_root,
        sealed_root=arguments.sealed_root,
        destination=arguments.output,
        unavailability=load_unavailability_audit(arguments.unavailability_audit),
        workers=arguments.workers,
    )


def _readiness(arguments: argparse.Namespace) -> Mapping[str, object]:
    """Prove the windows are executable by running the field that will be scored on them.

    CUP-50 activated on a flat readiness strategy. A flat book never carries a position into a
    roster exit, never meets the participation ceiling, and never needs a mark after a contract
    stops trading, so three organizer defects survived into a live field and invalidated all twelve
    trials twice. Readiness here replays every lane seed over the whole in-sample window at all
    three cost levels, and requires the field to trade and to be sized by the common unit.
    """
    research, sealed = load_snapshot(arguments.is_root), load_snapshot(arguments.sealed_root)
    verify_semantic_coverage(research)
    verify_semantic_coverage(sealed)
    combined = stitch_snapshots(research, sealed)
    boundaries = weekly_reconstitution_times(IS_START, OOS_END, weekday=0)
    require_exact_membership(combined.membership, boundaries)
    decisions = pd.date_range(IS_START, OOS_END, freq="8h", inclusive="left")
    unavailability = load_unavailability_audit(arguments.unavailability_audit)
    require_execution_coverage(combined, decisions, unavailability=unavailability)

    seed_root = Path(arguments.seed_root)
    lanes: dict[str, Mapping[str, object]] = {}
    deployed_lanes = 0
    for team_id in TEAM_IDS:
        source = seed_root / team_id / "strategy.py"
        strategy = strategy_from_module(load_strategy_module(source))
        replay = run_candidate(
            strategy,
            snapshot=research,
            start=IS_START,
            end=OOS_START,
            seed=int(team_id.split("-")[1]),
            unavailability=unavailability,
            record_events=False,
        )
        summary: dict[str, object] = {}
        for multiplier, result in replay.costs.items():
            returns = result.returns
            gross = returns["gross_return"].to_numpy(dtype=float)
            realized = float(np.std(gross, ddof=1)) * math.sqrt(365 * 24 / 8)
            summary[str(multiplier)] = {
                "turnover": float(returns["turnover"].sum()),
                "activity": float((returns["gross_exposure"] >= 0.05).mean()),
                "annualized_volatility": realized,
                "final_equity": float(returns["equity"].iloc[-1]),
            }
            if not np.isfinite(returns["net_return"].to_numpy()).all():
                raise ValueError(f"{team_id} produced a non-finite return at {multiplier}x")
            if float(returns["equity"].min()) <= 0.0:
                raise ValueError(f"{team_id} went insolvent at {multiplier}x")
        # Score the seed on the research window too. The qualification bar is stated in these
        # units, and a bar nobody has ever measured against is a guess that becomes immutable at
        # activation.
        scored = score_in_sample_point(replay.costs, regime_labels=research.regime_labels)
        summary["in_sample"] = _point_report(scored)
        verdict = evaluate_eligibility(
            {
                "is_score": scored.score,
                "is_regime_scores": dict(scored.regime_scores),
            }
        )
        summary["would_qualify"] = verdict.eligible
        summary["qualification_note"] = verdict.reason
        base = summary["1"]
        if float(base["activity"]) >= 0.05:
            deployed_lanes += 1
            if float(base["turnover"]) <= 0.0:
                raise ValueError(f"{team_id} deployed without ever trading")
        lanes[team_id] = summary

    if deployed_lanes < 9:
        raise ValueError(
            f"only {deployed_lanes} of {len(TEAM_IDS)} lane seeds deployed; readiness has to "
            "exercise execution, not merely survive it"
        )
    return {
        "status": "ready",
        "is_manifest_sha256": research.manifest_sha256,
        "sealed_manifest_sha256": sealed.manifest_sha256,
        "decision_boundaries": len(decisions),
        "deployed_lanes": deployed_lanes,
        "lanes": lanes,
    }


def _activate(arguments: argparse.Namespace) -> Mapping[str, object]:
    docker_version = require_isolation_available()
    resolved_image = require_image_digest(arguments.sandbox_image, arguments.sandbox_image_digest)
    verify_receipt(arguments.quarantine_receipt)
    preflight = _json(arguments.preflight)
    # What activation binds is the tournament: the policy, the evaluator, and the isolation the
    # whole evaluation model rests on. The forward desk is downstream of the release and is not
    # hash-bound here, so its parity smoke is a precondition of launching a desk rather than of
    # running the field -- requiring it now would force the desk to be built before any research
    # happens, for no integrity gain. The sandbox smoke takes its place, because if isolation is
    # broken then every result the field produces is worthless.
    required_checks = {
        "focused_suite",
        "full_pytest",
        "ruff",
        "deterministic_worker_counts",
        "deterministic_hash_seeds",
        "full_is_readiness_field",
        "clean_room_workspace_scan",
        "sandbox_isolation_smoke",
    }
    if set(preflight) != required_checks or any(value != "passed" for value in preflight.values()):
        raise ValueError("activation preflight is incomplete or contains a failed check")
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=arguments.repository_root,
        capture_output=True,
        text=True,
    )
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=arguments.repository_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    record = build_activation_record(
        arguments.output,
        repository_root=arguments.repository_root,
        artifacts=[
            arguments.charter,
            arguments.config,
            arguments.dependency_lock,
            arguments.pure_crypto_audit,
            arguments.quarantine_receipt,
            arguments.preflight,
            *arguments.data_manifest,
            *arguments.artifact,
        ],
        evaluator_entries=arguments.evaluator_entry,
        git_commit=commit,
        git_clean=status.returncode == 0 and not status.stdout,
        sandbox_image=arguments.sandbox_image,
        sandbox_image_digest=resolved_image.removeprefix("sha256:"),
        focused_test_transcript=arguments.focused_test_transcript,
        isolation_verified=True,
    )
    return {**record, "docker_version": docker_version}


def _quarantine(arguments: argparse.Namespace) -> Mapping[str, object]:
    roots = {
        name: getattr(arguments, name)
        for name in ("acquisition", "sealed", "private", "caches", "reports")
    }
    return create_receipt(arguments.output, roots=roots, research_roots=arguments.research_root)


def _export_protocol(arguments: argparse.Namespace) -> Mapping[str, object]:
    return export_protocol_bundle(arguments.source, arguments.output)


def _export_evaluator(arguments: argparse.Namespace) -> Mapping[str, object]:
    return export_evaluator_bundle(arguments.source, arguments.output)


def _trial(arguments: argparse.Namespace) -> Mapping[str, object]:
    binding = TrialBinding(**_json(arguments.binding))
    record = register_trial(arguments.journal, binding)
    if arguments.result_sha256:
        record = record_trial_result(
            arguments.journal,
            team_id=binding.team_id,
            trial_id=binding.trial_id,
            binding_sha256=binding.binding_sha256,
            source_path=arguments.source,
            result_sha256=arguments.result_sha256,
            succeeded=not arguments.failed,
        )
    return record


def _evaluate(arguments: argparse.Namespace) -> Mapping[str, object]:
    if os.environ.get("CUP50V2_SANDBOX") != "network-none-read-only":
        raise RuntimeError("official evaluation must run in the frozen network-disabled sandbox")
    binding = resolve_trial_binding(
        arguments.trial_journal,
        team_id=arguments.team_id,
        trial_id=arguments.trial_id,
        binding_sha256=arguments.binding_sha256,
    )
    if arguments.seed != int(binding["seed"]):
        raise ValueError("evaluation seed differs from its preregistered binding")
    if (
        pd.Timestamp(arguments.start) != IS_START
        or pd.Timestamp(arguments.end) != OOS_START
        or arguments.terminal
    ):
        raise ValueError("official IS feedback must use the complete non-terminal IS window")
    source_path = Path(arguments.source_bundle).resolve()
    strategy_path = Path(arguments.strategy).resolve()
    if not (
        strategy_path == source_path
        or (source_path.is_dir() and strategy_path.is_relative_to(source_path))
    ):
        raise ValueError("evaluation strategy entrypoint is outside its source bundle")
    if source_bundle_digest(source_path) != binding["source_sha256"]:
        raise ValueError("evaluation strategy differs from its preregistered source")
    snapshot = load_snapshot(arguments.snapshot)
    if snapshot.manifest_sha256 != binding["data_sha256"]:
        raise ValueError("evaluation snapshot differs from its preregistered data")
    if hashlib.sha256(Path(arguments.config).read_bytes()).hexdigest() != binding["config_sha256"]:
        raise ValueError("evaluation config differs from its preregistered config")
    if (
        hashlib.sha256(Path(arguments.risk_policy).read_bytes()).hexdigest()
        != binding["risk_policy_sha256"]
    ):
        raise ValueError("evaluation risk policy differs from its preregistered policy")
    # Check the shipped policy against the config, never against a copy of it living here. An
    # inline dict is a second place for a policy to live, and the second place is the one that goes
    # stale: this check named a superseded policy id and no charged trial could pass it.
    policy = _json(arguments.risk_policy)
    expected_id = str(load_config(arguments.config).raw["risk_unit"]["policy_id"])
    if (
        int(policy.get("schema_version", 0)) != 1
        or str(policy.get("policy_id")) != expected_id
        or bool(policy.get("team_specific_controls"))
        or bool(policy.get("team_specific_volatility_targeting"))
    ):
        raise ValueError("CUP-50 v2 permits only the frozen common risk-unit policy")
    scorer = Path(__file__).with_name("scoring.py")
    if hashlib.sha256(scorer.read_bytes()).hexdigest() != binding["scorer_sha256"]:
        raise ValueError("evaluation scorer differs from its preregistered scorer")
    strategy = strategy_from_module(load_strategy_module(arguments.strategy))
    apply_strategy_parameters(strategy, binding["parameters"])
    try:
        replay = run_candidate(
            strategy,
            snapshot=snapshot,
            start=pd.Timestamp(arguments.start),
            end=pd.Timestamp(arguments.end),
            seed=arguments.seed,
            terminal=arguments.terminal,
            unavailability=load_unavailability_audit(arguments.unavailability_audit),
        )
    except StrategyFailureError as error:
        failure_digest = hashlib.sha256(
            json.dumps(
                {
                    "team_id": arguments.team_id,
                    "trial_id": arguments.trial_id,
                    "failure": type(error).__name__,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        record_trial_result(
            arguments.trial_journal,
            team_id=arguments.team_id,
            trial_id=arguments.trial_id,
            binding_sha256=arguments.binding_sha256,
            source_path=source_path,
            result_sha256=failure_digest,
            succeeded=False,
        )
        return {"status": "candidate-dnf", "bundle_sha256": failure_digest}
    output = Path(arguments.output)
    output.mkdir(parents=True, exist_ok=False)
    replay.raw_targets.to_parquet(output / "targets.parquet")
    replay.risk_scalars.rename("risk_scalar").to_frame().to_parquet(output / "risk-scalars.parquet")
    for cost, result in replay.costs.items():
        result.returns.to_parquet(output / f"returns-{cost}x.parquet")
        result.events.to_parquet(output / f"events-{cost}x.parquet")
    digest = hashlib.sha256(
        b"".join(path.read_bytes() for path in sorted(output.iterdir()) if path.is_file())
    ).hexdigest()
    record_trial_result(
        arguments.trial_journal,
        team_id=arguments.team_id,
        trial_id=arguments.trial_id,
        binding_sha256=arguments.binding_sha256,
        source_path=source_path,
        result_sha256=digest,
        succeeded=True,
    )
    return {"status": "evaluated", "bundle_sha256": digest}


def _research_eval(arguments: argparse.Namespace) -> Mapping[str, object]:
    """An unlimited, journaled look at the research window, on approximate execution.

    Costs a team nothing and can never be nominated. CUP-50 gave twelve charged trials and no other
    way to run anything, so nothing was iterated and its field was twelve unchanged seeds; a
    research loop that costs a trial is not a research loop.
    """
    if os.environ.get("CUP50V2_SANDBOX") != "network-none-read-only":
        raise RuntimeError("research evaluation must run inside the isolated sandbox")
    snapshot = research_snapshot_from_team_visible(
        arguments.team_snapshot, regimes=active_policy().regimes
    )
    strategy = strategy_from_module(load_strategy_module(arguments.strategy))
    parameters = _json(arguments.parameters).get("centre", {}) if arguments.parameters else {}
    if parameters:
        apply_strategy_parameters(strategy, parameters)
    # The team-visible audit, not the organizer's: a cessation dated after the split is a sealed
    # fact. Without it the replay demands an executable price from a contract that had stopped
    # trading, which is a real event in this window rather than a data defect.
    replay = run_candidate(
        strategy,
        snapshot=snapshot,
        start=snapshot.window_start,
        end=snapshot.window_end,
        seed=int(arguments.seed),
        unavailability=load_unavailability_audit(arguments.unavailability_audit),
        record_events=False,
    )
    scored = score_in_sample_point(replay.costs, regime_labels=snapshot.regime_labels)
    report = {
        "schema_version": 1,
        "namespace": "cup50v2",
        "team_id": arguments.team_id,
        "execution": EXECUTION_MODE,
        "purpose": arguments.purpose,
        "parameters": dict(parameters),
        "seed": int(arguments.seed),
        "score": _point_report(scored),
        "diagnostics": _diagnostics(replay),
        "caveat": (
            "Approximate execution: fills are priced at the last visible close rather than the "
            "transaction open. Direction, not the number."
        ),
    }
    Path(arguments.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    append_record(
        arguments.research_journal,
        "research-eval",
        {
            "team_id": arguments.team_id,
            "purpose": arguments.purpose,
            "parameters": dict(parameters),
            "seed": int(arguments.seed),
            "source_sha256": source_bundle_digest(arguments.strategy),
            "score": scored.score,
        },
    )
    return {"command": "research-eval", "team_id": arguments.team_id, "score": scored.score}


def _diagnostics(replay) -> Mapping[str, object]:
    """What a team needs to see to fix something, all of it in sample."""
    summary: dict[str, object] = {}
    for multiplier, result in replay.costs.items():
        returns = result.returns
        gross = returns["gross_return"].to_numpy(dtype=float)
        costs = float(returns["fees_slippage"].sum())
        gross_total = float(np.abs(gross).sum())
        summary[str(multiplier)] = {
            "turnover": float(returns["turnover"].sum()),
            "activity": float((returns["gross_exposure"] >= 0.05).mean()),
            "mean_gross_exposure": float(returns["gross_exposure"].mean()),
            "annualized_volatility": float(np.std(gross, ddof=1)) * math.sqrt(365 * 24 / 8),
            "cost_share_of_gross": costs / gross_total if gross_total > 0 else None,
            "final_equity": float(returns["equity"].iloc[-1]),
        }
    return summary


def _point_report(scored) -> Mapping[str, object]:
    return {
        "score": scored.score,
        "generalization": scored.generalization,
        "regime": scored.regime,
        "all_window": scored.all_window,
        "fold_scores": dict(scored.fold_scores),
        "regime_scores": dict(scored.regime_scores),
    }


def _critic_pack(arguments: argparse.Namespace) -> Mapping[str, object]:
    """Assemble what the critic reviews, and nothing that would let it rank anyone.

    The pack deliberately omits every score. A reviewer who can see a number starts reasoning about
    whether a lane deserves to advance, and that is the scorer's job.
    """
    nomination = verify_nomination(arguments.nomination)
    scrubbed = {
        key: value
        for key, value in nomination.items()
        if key not in {"is_score", "is_point_scores", "is_regime_scores"}
    }
    pack = {
        "schema_version": 1,
        "namespace": "cup50v2",
        "team_id": nomination["team_id"],
        "nomination": scrubbed,
        "falsifiers": nomination.get("falsifiers", []),
        "risk_declaration": _json(arguments.risk_declaration),
        "certificate_path": str(arguments.certificate),
        "clean_room_scan": list(scan_research_root(arguments.research_root)),
        "transcript_audit": _json(arguments.transcript_audit),
        "trial_ledger": [
            record["payload"]
            for record in read_records(arguments.trial_journal)
            if record["payload"].get("team_id") == nomination["team_id"]
        ],
        "instruction": (
            "Return PASS or exactly one allowlisted disqualification code. No score is included "
            "here, and performance is never an integrity finding."
        ),
    }
    Path(arguments.output).write_text(json.dumps(pack, indent=2, sort_keys=True) + "\n")
    return {"command": "critic-pack", "team_id": pack["team_id"], "output": str(arguments.output)}


def _nominate(arguments: argparse.Namespace) -> Mapping[str, object]:
    source = Path(arguments.source_bundle)
    source_digest = source_bundle_digest(source)
    strategy_path = Path(arguments.strategy).resolve()
    source_path = source.resolve()
    if not (
        strategy_path == source_path
        or (source_path.is_dir() and strategy_path.is_relative_to(source_path))
    ):
        raise ValueError("nomination strategy entrypoint is outside its frozen source bundle")
    if source_digest != arguments.source_bundle_sha256:
        raise ValueError("nomination source bundle digest does not match its trial binding")
    binding = nomination_trial_binding(
        arguments.trial_journal,
        arguments.team_id,
        arguments.trial_id,
        source_sha256=source_digest,
        minimum_trials=active_policy().research.minimum_official_trials,
    )
    payload = _json(arguments.parameters)
    if payload.get("centre") != binding["parameters"]:
        raise ValueError("nomination centre differs from its preregistered trial parameters")
    dimensions = tuple(Dimension(**item) for item in payload.get("dimensions", []))
    neighbourhood = generate_neighbourhood(payload["centre"], dimensions)
    snapshot = load_snapshot(arguments.is_snapshot)
    decisions = decision_grid(IS_START, OOS_START)
    unavailability = load_unavailability_audit(arguments.unavailability_audit)

    def target_digest(parameters: Mapping[str, float]) -> str:
        strategy = strategy_from_module(load_strategy_module(arguments.strategy))
        apply_strategy_parameters(strategy, parameters)
        targets = generate_targets(
            strategy,
            bars=snapshot.bars,
            funding=snapshot.funding,
            auxiliary={},
            membership=snapshot.membership,
            decision_times=decisions,
            seed=int(binding["seed"]),
            unavailability=unavailability,
        )
        payload = targets.to_json(orient="split", date_format="iso", double_precision=15).encode()
        return hashlib.sha256(payload).hexdigest()

    reject_inert_dimensions(neighbourhood, target_digest)

    verify_risk_declaration(
        _json(arguments.risk_declaration), candidate_id=str(arguments.trial_id)
    )
    verify_certificate(Path(arguments.certificate))

    # Score every declared point on the research window. CUP-50 replayed each point's target stream
    # only to test inertness, so a nomination carried no evidence and the qualification question had
    # to be answered later, after the sealed window had already been opened.
    def replay_point(parameters: Mapping[str, float], *, invert: bool = False):
        strategy = strategy_from_module(load_strategy_module(arguments.strategy))
        apply_strategy_parameters(strategy, parameters)
        wrapped = _InvertedStrategy(strategy) if invert else strategy
        return run_candidate(
            wrapped,
            snapshot=snapshot,
            start=IS_START,
            end=OOS_START,
            seed=int(binding["seed"]),
            unavailability=unavailability,
            record_events=False,
        )

    point_scores = []
    centre_point = None
    for index, parameters in enumerate(neighbourhood.points):
        replay = replay_point(parameters)
        scored = score_in_sample_point(replay.costs, regime_labels=snapshot.regime_labels)
        point_scores.append(scored)
        if index == neighbourhood.centre_index:
            centre_point = scored
    is_neighbourhood = rounded_neighbourhood(
        score_neighbourhood(point_scores, centre_index=neighbourhood.centre_index)
    )

    signing_key = Path(arguments.falsifier_key).read_bytes()
    inverted = replay_point(neighbourhood.points[neighbourhood.centre_index], invert=True)
    inverted_score = score_in_sample_point(
        inverted.costs, regime_labels=snapshot.regime_labels
    ).score
    outcomes = [sign_inversion(centre_point.score, inverted_score)]

    def generate_stream(bars: pd.DataFrame) -> pd.DataFrame:
        strategy = strategy_from_module(load_strategy_module(arguments.strategy))
        apply_strategy_parameters(strategy, neighbourhood.points[neighbourhood.centre_index])
        return generate_targets(
            strategy,
            bars=bars,
            funding=snapshot.funding,
            auxiliary={},
            membership=snapshot.membership,
            decision_times=decisions,
            seed=int(binding["seed"]),
            unavailability=unavailability,
        )

    outcomes.append(
        future_corruption(
            generate_stream,
            snapshot.bars,
            cut_points=corruption_cut_points(decisions, key=signing_key),
        )
    )
    first = generate_stream(snapshot.bars)
    second = generate_stream(snapshot.bars)
    outcomes.append(determinism(first, second))
    failed = [outcome for outcome in outcomes if not outcome.passed]
    if failed:
        raise ValueError(
            "nomination refused by the falsification battery: "
            + "; ".join(f"{outcome.name}: {outcome.detail}" for outcome in failed)
        )

    regime_scores = {
        name: round_half_even(value) for name, value in centre_point.regime_scores.items()
    }
    record = freeze_nomination(
        arguments.output,
        team_id=arguments.team_id,
        candidate_id=arguments.candidate_id,
        source_bundle_sha256=arguments.source_bundle_sha256,
        neighbourhood=neighbourhood,
        trial_id=arguments.trial_id,
        is_score=is_neighbourhood.official_score,
        is_point_scores=list(is_neighbourhood.point_scores),
        is_regime_scores=regime_scores,
        falsifiers=[dataclasses.asdict(outcome) for outcome in outcomes],
    )
    verdict = evaluate_eligibility(record)
    return {**record, "eligible": verdict.eligible, "eligibility_reason": verdict.reason}


class _InvertedStrategy:
    """The candidate with every weight flipped, for the sign-inversion falsifier."""

    def __init__(self, inner: object) -> None:
        self._inner = inner

    def target_weights(self, context, *, seed: int):
        weights = self._inner.target_weights(context, seed=seed)
        if not weights:
            return weights
        return {symbol: -float(value) for symbol, value in weights.items()}


def _field_close(arguments: argparse.Namespace) -> Mapping[str, object]:
    payload = _json(arguments.dispositions)
    key = _key(arguments.signing_key)
    # Derive the order here rather than accept one. lifecycle.observation_order has existed and
    # been tested since the fork, and nothing on the lifecycle path ever called it -- so the order
    # C17 requires to be key-derived was in practice whatever the organizer typed. An organizer who
    # picks the order picks which lanes are read first, which is the fact C17 exists to remove.
    order = observation_order(key, activation_sha256=arguments.activation_sha256)
    supplied = payload.get("observation_order")
    if supplied is not None and tuple(str(team) for team in supplied) != order:
        raise ValueError(
            "observation order is derived from the signing key and may not be supplied; "
            "remove observation_order from the dispositions payload"
        )
    return freeze_field(
        arguments.output,
        dispositions=payload["dispositions"],
        observation_order=order,
        activation_sha256=arguments.activation_sha256,
        signing_key=key,
    )


def _observe(arguments: argparse.Namespace) -> Mapping[str, object]:
    field = verify_field(arguments.field, signing_key=_key(arguments.signing_key))
    if arguments.action == "start":
        result = start_observation_batch(
            arguments.journal,
            field_sha256=str(field["field_sha256"]),
            sealed_manifest_sha256=arguments.sealed_manifest_sha256,
            observation_order=[
                team_id
                for team_id in field["observation_order"]
                if field["dispositions"][team_id]["state"] == "nominated"
            ],
            expected_points={
                team_id: field["dispositions"][team_id]["point_ids"]
                for team_id in field["observation_order"]
                if field["dispositions"][team_id]["state"] == "nominated"
            },
        )
        # Deliberately generic: no team/candidate progress leaves the private observation process.
        return {"status": "observation-started", "record_sha256": result["record_sha256"]}
    if arguments.action == "recover":
        interrupted = recover_interrupted_points(arguments.journal)
        return {"status": "recovered", "terminal_interruptions": len(interrupted)}
    if arguments.action == "restart":
        outcome = restart_interrupted_points(
            arguments.journal, private_stage=arguments.private_stage
        )
        return {
            "status": "restarted",
            "completed_from_evidence": len(outcome["completed"]),
            "resumable": len(outcome["resumable"]),
        }
    if os.environ.get("CUP50V2_SANDBOX") != "network-none-read-only":
        raise RuntimeError(
            "sealed point observation must run in the frozen network-disabled sandbox"
        )
    job = _json(arguments.job)

    # Bind the job to the frozen field, not merely to the nomination file it names. Without this
    # the disposition's nomination_sha256 is decorative: freeze_field requires only that it be
    # non-empty, and nothing compared it with the point actually being observed, so the field
    # freeze did not in fact pin which nomination each lane is read against.
    field_record = verify_field(arguments.field, signing_key=_key(arguments.signing_key))
    disposition = field_record["dispositions"].get(str(job["team_id"]))
    if disposition is None:
        raise ValueError("point names a team that is not in the frozen field")
    if disposition["state"] != "nominated":
        raise ValueError("point names a lane the field did not record as nominated")
    if str(disposition["nomination_sha256"]) != str(job["nomination_sha256"]):
        raise ValueError(
            "point's nomination digest differs from the one the field froze for this lane"
        )
    if str(job["point_id"]) not in {str(value) for value in disposition["point_ids"]}:
        raise ValueError("point id is not one the field froze for this lane")

    def evaluator() -> Mapping[str, object]:
        nomination = verify_nomination(job["nomination"])
        if (
            nomination["freeze_sha256"] != job["nomination_sha256"]
            or nomination["team_id"] != job["team_id"]
            or nomination["source_bundle_sha256"]
            != source_bundle_digest(job.get("source_bundle", job["strategy"]))
        ):
            raise CandidateFailureError("point differs from its frozen nomination")
        point_index = int(job["point_index"])
        points = nomination["points"]
        if not 0 <= point_index < len(points):
            raise CandidateFailureError("point index is outside the frozen neighbourhood")

        # The durable batch-start record already exists before either snapshot is opened here.
        research = load_snapshot(job["is_root"])
        sealed = load_snapshot(job["sealed_root"])
        from crypto_trade.cup50v2.journal import read_records

        batch = read_records(arguments.journal)[0]["payload"]
        if sealed.manifest_sha256 != batch["sealed_manifest_sha256"]:
            raise ValueError("sealed snapshot differs from the batch binding")
        verify_semantic_coverage(research)
        verify_semantic_coverage(sealed)
        snapshot = stitch_snapshots(research, sealed)
        decisions = decision_grid(IS_START, OOS_END)
        unavailability = load_unavailability_audit(job["unavailability_audit"])
        require_execution_coverage(snapshot, decisions, unavailability=unavailability)
        try:
            strategy = strategy_from_module(load_strategy_module(job["strategy"]))
            apply_strategy_parameters(strategy, points[point_index])
        except Exception as error:
            raise CandidateFailureError(
                f"candidate source or parameters failed: {type(error).__name__}"
            ) from error
        try:
            replay = run_candidate(
                strategy,
                snapshot=snapshot,
                start=IS_START,
                end=OOS_END,
                seed=int(job.get("seed", 0)),
                terminal=False,
                unavailability=unavailability,
                record_events=False,
            )
            score = score_point(replay.costs, regime_labels=snapshot.regime_labels)
            centre_returns = replay.costs[3].returns
            centre_turnover = float(
                centre_returns.loc[
                    (centre_returns.index >= OOS_START) & (centre_returns.index < OOS_END),
                    "turnover",
                ].sum()
            )
        except StrategyFailureError as error:
            raise CandidateFailureError(
                f"candidate point failed: {type(error).__name__}"
            ) from error
        return {
            "team_id": job["team_id"],
            "point_id": job["point_id"],
            "point_index": point_index,
            "parameters": points[point_index],
            "score": dataclasses.asdict(score),
            "centre_turnover": centre_turnover,
            "source_bundle_sha256": nomination["source_bundle_sha256"],
            "is_manifest_sha256": research.manifest_sha256,
            "sealed_manifest_sha256": sealed.manifest_sha256,
        }

    observe_point(
        arguments.journal,
        team_id=job["team_id"],
        point_id=job["point_id"],
        nomination_sha256=job["nomination_sha256"],
        evaluator=evaluator,
        private_stage=arguments.private_stage,
        resume_organizer_failure=arguments.action == "resume",
    )
    return {"status": "point-terminal"}


def _review(arguments: argparse.Namespace) -> Mapping[str, object]:
    field = verify_field(arguments.field, signing_key=_key(arguments.signing_key))
    result = integrity_review(
        field=field, journal_path=arguments.journal, private_stage=arguments.private_stage
    )
    _write_json(arguments.output, result)
    return result


def _leaderboard(arguments: argparse.Namespace) -> Mapping[str, object]:
    field = verify_field(arguments.field, signing_key=_key(arguments.signing_key))
    result = compile_leaderboard(
        field=field,
        journal_path=arguments.journal,
        private_stage=arguments.private_stage,
    )
    _write_json(arguments.output, result)
    return {"status": "compiled", "entries": len(result["entries"])}


def _release(arguments: argparse.Namespace) -> Mapping[str, object]:
    return atomic_release(
        arguments.output,
        leaderboard=_json(arguments.leaderboard),
        integrity=_json(arguments.integrity_review),
    )


def _paper(arguments: argparse.Namespace) -> Mapping[str, object]:
    if arguments.action == "launch-time":
        boundary = first_boundary_after(pd.Timestamp(arguments.release_time))
        return {"launch_time": boundary.isoformat().replace("+00:00", "Z")}
    if arguments.action == "parity":
        backtest, paper = pd.read_parquet(arguments.backtest), pd.read_parquet(arguments.paper)
        return {"status": "parity", "target_sha256": verify_parity(backtest, paper)}
    if arguments.action == "freeze-authority":
        return freeze_desk_authority(
            arguments.output,
            release_path=arguments.release,
            winner_bundle=arguments.winner_bundle,
            nomination_sha256=arguments.nomination_sha256,
            release_time=pd.Timestamp(arguments.release_time),
        )
    state = _json(arguments.state)
    health = healthcheck(state, now=pd.Timestamp(arguments.now))
    if arguments.action == "healthcheck":
        return dataclasses.asdict(health)
    markdown = digest_markdown(
        health, forward_days=arguments.forward_days, observations=arguments.observations
    )
    Path(arguments.output).write_text(markdown)
    return {"status": health.status, "digest": arguments.output}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="cup50v2", description="CUP-50 v2 tournament lifecycle")
    commands = root.add_subparsers(dest="command", required=True)

    reuse = commands.add_parser("acquire-reuse")
    reuse.add_argument("--source", required=True)
    reuse.add_argument("--destination", required=True)
    reuse.add_argument("--receipt", required=True)
    reuse.set_defaults(handler=_acquire_reuse)

    acquire = commands.add_parser("acquire")
    acquire.add_argument("--source-acquisition", required=True)
    acquire.add_argument("--source-manifest", required=True)
    acquire.add_argument("--membership", required=True)
    acquire.add_argument("--output", required=True)
    acquire.add_argument("--workers", type=int, default=8)
    acquire.set_defaults(handler=_acquire)

    coverage = commands.add_parser("acquire-coverage")
    coverage.add_argument("--source-acquisition", required=True)
    coverage.add_argument("--source-manifest", required=True)
    coverage.add_argument("--is-root", required=True)
    coverage.add_argument("--sealed-root", required=True)
    coverage.add_argument("--output", required=True)
    coverage.add_argument("--unavailability-audit", required=True)
    coverage.add_argument("--workers", type=int, default=8)
    coverage.set_defaults(handler=_acquire_coverage)

    build = commands.add_parser("build")
    build.add_argument("--acquisition", required=True)
    build.add_argument("--acquisition-manifest", required=True)
    build.add_argument("--classification-audit", required=True)
    build.add_argument("--pure-crypto-audit-output", required=True)
    build.add_argument("--is-root", required=True)
    build.add_argument("--sealed-root", required=True)
    build.add_argument("--team-is-root", required=True)
    build.set_defaults(handler=_build)

    ready = commands.add_parser("readiness")
    ready.add_argument("--is-root", required=True)
    ready.add_argument("--seed-root", default="tournament/cup50v2/seeds")
    ready.add_argument("--sealed-root", required=True)
    ready.add_argument("--unavailability-audit", required=True)
    ready.set_defaults(handler=_readiness)

    activate = commands.add_parser("activate")
    activate.add_argument("--repository-root", default=".")
    activate.add_argument("--output", required=True)
    activate.add_argument("--charter", required=True)
    activate.add_argument("--config", required=True)
    activate.add_argument("--dependency-lock", required=True)
    activate.add_argument("--pure-crypto-audit", required=True)
    activate.add_argument("--quarantine-receipt", required=True)
    activate.add_argument("--data-manifest", action="append", required=True)
    activate.add_argument("--preflight", required=True)
    activate.add_argument("--artifact", action="append", default=[])
    activate.add_argument("--evaluator-entry", action="append", required=True)
    activate.add_argument("--focused-test-transcript", required=True)
    activate.add_argument("--sandbox-image", required=True)
    activate.add_argument("--sandbox-image-digest", required=True)
    activate.set_defaults(handler=_activate)

    quarantine = commands.add_parser("quarantine")
    for name in ("acquisition", "sealed", "private", "caches", "reports"):
        quarantine.add_argument(f"--{name}", required=True)
    quarantine.add_argument("--research-root", action="append", default=[])
    quarantine.add_argument("--output", required=True)
    quarantine.set_defaults(handler=_quarantine)

    protocol_export = commands.add_parser("export-protocol")
    protocol_export.add_argument("--source", required=True)
    protocol_export.add_argument("--output", required=True)
    protocol_export.set_defaults(handler=_export_protocol)

    evaluator_export = commands.add_parser("export-evaluator")
    evaluator_export.add_argument("--source", required=True)
    evaluator_export.add_argument("--output", required=True)
    evaluator_export.set_defaults(handler=_export_evaluator)

    trial = commands.add_parser("trial")
    trial.add_argument("--journal", required=True)
    trial.add_argument("--binding", required=True)
    trial.add_argument("--source")
    trial.add_argument("--result-sha256")
    trial.add_argument("--failed", action="store_true")
    trial.set_defaults(handler=_trial)

    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("--strategy", required=True)
    evaluate.add_argument("--source-bundle", required=True)
    evaluate.add_argument("--snapshot", required=True)
    evaluate.add_argument("--config", required=True)
    evaluate.add_argument("--risk-policy", required=True)
    evaluate.add_argument("--unavailability-audit", required=True)
    evaluate.add_argument("--trial-journal", required=True)
    evaluate.add_argument("--team-id", required=True)
    evaluate.add_argument("--trial-id", required=True)
    evaluate.add_argument("--binding-sha256", required=True)
    evaluate.add_argument("--start", required=True)
    evaluate.add_argument("--end", required=True)
    evaluate.add_argument("--seed", type=int, default=0)
    evaluate.add_argument("--terminal", action="store_true")
    evaluate.add_argument("--output", required=True)
    evaluate.set_defaults(handler=_evaluate)

    nominate = commands.add_parser("nominate")
    nominate.add_argument("--team-id", required=True)
    nominate.add_argument("--candidate-id", required=True)
    nominate.add_argument("--source-bundle-sha256", required=True)
    nominate.add_argument("--source-bundle", required=True)
    nominate.add_argument("--strategy", required=True)
    nominate.add_argument("--is-snapshot", required=True)
    nominate.add_argument("--unavailability-audit", required=True)
    nominate.add_argument("--trial-journal", required=True)
    nominate.add_argument("--trial-id", required=True)
    nominate.add_argument("--parameters", required=True)
    nominate.add_argument("--output", required=True)
    research = commands.add_parser("research-eval")
    research.add_argument("--team-id", required=True)
    research.add_argument("--team-snapshot", required=True)
    research.add_argument("--strategy", required=True)
    research.add_argument("--parameters")
    research.add_argument("--seed", type=int, default=0)
    research.add_argument("--purpose", required=True)
    research.add_argument(
        "--unavailability-audit", default="tournament/cup50v2/is-unavailability.json"
    )
    research.add_argument("--research-journal", required=True)
    research.add_argument("--output", required=True)
    research.set_defaults(handler=_research_eval)

    pack = commands.add_parser("critic-pack")
    pack.add_argument("--nomination", required=True)
    pack.add_argument("--risk-declaration", required=True)
    pack.add_argument("--certificate", required=True)
    pack.add_argument("--research-root", required=True)
    pack.add_argument("--transcript-audit", required=True)
    pack.add_argument("--trial-journal", required=True)
    pack.add_argument("--output", required=True)
    pack.set_defaults(handler=_critic_pack)

    nominate.add_argument("--risk-declaration", required=True)
    nominate.add_argument("--certificate", required=True)
    nominate.add_argument("--falsifier-key", required=True)
    nominate.set_defaults(handler=_nominate)

    close = commands.add_parser("field-close")
    close.add_argument("--dispositions", required=True)
    close.add_argument("--activation-sha256", required=True)
    close.add_argument("--signing-key", required=True)
    close.add_argument("--output", required=True)
    close.set_defaults(handler=_field_close)

    observe = commands.add_parser("observe")
    observe.add_argument("action", choices=("start", "point", "resume", "recover", "restart"))
    observe.add_argument("--field", required=True)
    observe.add_argument("--signing-key", required=True)
    observe.add_argument("--journal", required=True)
    observe.add_argument("--sealed-manifest-sha256")
    observe.add_argument("--job")
    observe.add_argument("--private-stage")
    observe.set_defaults(handler=_observe)

    review = commands.add_parser("integrity-review")
    review.add_argument("--field", required=True)
    review.add_argument("--signing-key", required=True)
    review.add_argument("--journal", required=True)
    review.add_argument("--private-stage", required=True)
    review.add_argument("--output", required=True)
    review.set_defaults(handler=_review)

    leaderboard = commands.add_parser("leaderboard")
    leaderboard.add_argument("--field", required=True)
    leaderboard.add_argument("--signing-key", required=True)
    leaderboard.add_argument("--journal", required=True)
    leaderboard.add_argument("--private-stage", required=True)
    leaderboard.add_argument("--output", required=True)
    leaderboard.set_defaults(handler=_leaderboard)

    release = commands.add_parser("release")
    release.add_argument("--leaderboard", required=True)
    release.add_argument("--integrity-review", required=True)
    release.add_argument("--output", required=True)
    release.set_defaults(handler=_release)

    paper = commands.add_parser("paper")
    paper.add_argument(
        "action",
        choices=("launch-time", "freeze-authority", "parity", "healthcheck", "digest"),
    )
    paper.add_argument("--release-time")
    paper.add_argument("--backtest")
    paper.add_argument("--paper")
    paper.add_argument("--state")
    paper.add_argument("--now")
    paper.add_argument("--forward-days", type=int, default=0)
    paper.add_argument("--observations", type=int, default=0)
    paper.add_argument("--output")
    paper.add_argument("--release")
    paper.add_argument("--winner-bundle")
    paper.add_argument("--nomination-sha256")
    paper.set_defaults(handler=_paper)
    return root


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    result = arguments.handler(arguments)
    # Observation deliberately emits only generic status; other phases may print their own facts.
    print(json.dumps(result, sort_keys=True, allow_nan=False, default=str))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
