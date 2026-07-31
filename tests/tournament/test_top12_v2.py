from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from crypto_trade.tournament import (
    activation_top12_v2,
    journal_top12_v2,
    orchestrator_top12_v2,
    runner_top12_v2,
    scoring_top12_v2,
    source_archive_top12_v2,
    top12_universe_v1,
    top12_v2,
)
from crypto_trade.tournament.engine_v2 import EvaluationResult
from crypto_trade.tournament.layout_top12_v2 import TOP12_V2_LAYOUT

ROOT = Path(__file__).resolve().parents[2]


def _accepted(team_id: str, trial: int) -> dict[str, object]:
    return {
        "team_id": team_id,
        "run_id": f"{team_id.replace('-', '')}-run-{trial:02d}",
        "trial_number": trial,
        "candidate_id": f"{team_id.replace('-', '')}-candidate-{trial:02d}",
        "purpose": "bounded preregistered test",
        "metadata": {"tags": ["baseline"]},
        "authority": {"source_bundle_sha256": "1" * 64},
        "output_path": f"reports-top12-v2/is/{team_id}/run-{trial:02d}",
    }


def _success(request: dict[str, object]) -> dict[str, object]:
    payload = request["payload"]
    return {
        "team_id": payload["team_id"],
        "run_id": payload["run_id"],
        "candidate_id": payload["candidate_id"],
        "request_sha256": request["record_sha256"],
        "summary_path": f"reports-top12-v2/is/{payload['team_id']}/summary.json",
        "summary_sha256": "2" * 64,
    }


def _candidate_authority(team_id: str) -> dict[str, str]:
    candidate_id = f"{team_id.replace('-', '')}-finalist-v1"
    candidate_root = f"tournament/top12-v2/teams/{team_id}/candidates/{candidate_id}"
    digest = hashlib.sha256(team_id.encode("ascii")).hexdigest()
    return {
        "team_id": team_id,
        "candidate_id": candidate_id,
        "candidate_root": candidate_root,
        "entrypoint": f"{candidate_root}/strategy.py",
        "source_bundle_sha256": digest,
        "source_archive_path": (
            f"tournament/top12-v2/source-archives/{team_id}/{candidate_id}.json"
        ),
        "source_archive_sha256": "1" * 64,
        "strategy_sha256": "2" * 64,
        "risk_policy_sha256": "3" * 64,
        "config_sha256": "4" * 64,
        "dependency_lock_sha256": "5" * 64,
        "data_manifest_sha256": "6" * 64,
        "evaluator_sha256": "7" * 64,
    }


def _historical_selection(team_ids: tuple[str, ...]) -> dict[str, object]:
    return {
        "advancing": [
            {
                "rank": rank,
                "team_id": team_id,
                "candidate_id": _candidate_authority(team_id)["candidate_id"],
                "authority": _candidate_authority(team_id),
                "trial_count": 8,
            }
            for rank, team_id in enumerate(team_ids, start=1)
        ],
        "ensemble": {
            "constituent_weights": {team_id: 0.30 for team_id in team_ids},
            "cash_weight": max(0.0, 1.0 - 0.30 * len(team_ids)),
        },
    }


def _historical_request(team_id: str, sequence: int) -> dict[str, object]:
    authority = _candidate_authority(team_id)
    run_id = (
        f"{team_id.replace('-', '')}-historical-oos-"
        f"{authority['source_bundle_sha256'][:12]}"
    )
    return {
        "event_type": "historical_accepted",
        "record_sha256": f"{sequence:064x}",
        "payload": {
            "team_id": team_id,
            "candidate_id": authority["candidate_id"],
            "run_id": run_id,
            "selection_record_sha256": "a" * 64,
            "output_path": (
                f"tournament/top12-v2/private/historical-oos/{team_id}/{run_id}"
            ),
        },
    }


def _historical_append_stub(state: SimpleNamespace, events: list[dict[str, object]]):
    def append(
        _path: Path, event_type: str, payload: dict[str, object]
    ) -> dict[str, object]:
        record = {
            "event_type": event_type,
            "payload": dict(payload),
            "record_sha256": f"{len(events) + 100:064x}",
        }
        events.append(record)
        team_id = str(payload.get("team_id", ""))
        if event_type == "historical_accepted":
            state.historical_requests[team_id] = record
        elif event_type == "historical_started":
            state.historical_starts[team_id] = record
        elif event_type in {"historical_succeeded", "historical_failed"}:
            state.historical_terminals[team_id] = record
        elif event_type == "release_authorized":
            state.release = record["payload"]
        return record

    return append


def test_v2_contract_has_twelve_teams_and_three_strict_stages() -> None:
    loaded = top12_v2.load_config(root=ROOT)
    assert loaded.raw["teams"] == list(TOP12_V2_LAYOUT.team_ids)
    assert TOP12_V2_LAYOUT.team_ids[-1] == "team-12"
    assert (
        runner_top12_v2._authorized_window(loaded.raw, "is").score_start
        == "2020-08-03T00:00:00Z"
    )
    confirmation = runner_top12_v2._authorized_window(loaded.raw, "is_confirmation")
    assert confirmation.score_start == "2023-07-01T00:00:00Z"
    assert confirmation.end_exclusive == "2024-07-01T00:00:00Z"
    historical = runner_top12_v2._authorized_window(loaded.raw, "historical_oos")
    assert historical.score_start == "2024-07-01T00:00:00Z"
    assert historical.end_exclusive == "2026-07-01T00:00:00Z"
    with pytest.raises(ValueError, match="is_confirmation"):
        runner_top12_v2._authorized_window(loaded.raw, "validation")


def test_metric_window_normalizes_utc_start_and_date_only_end() -> None:
    index = pd.date_range("2020-02-03T00:00:00Z", periods=180, freq="1D")
    daily = pd.Series([0.001, -0.0005] * 90, index=index, name="net_return")
    authorized = runner_top12_v2.AuthorizedWindow(
        stage="is",
        replay_start="2020-02-03T00:00:00Z",
        end_exclusive="2020-08-01T00:00:00Z",
        score_start="2020-02-03T00:00:00Z",
        score_end_inclusive="2020-07-31",
    )
    packet = runner_top12_v2._compute_metrics(
        daily,
        daily,
        daily,
        daily,
        {
            "statistics": {
                "bootstrap_samples": 100,
                "bootstrap_block_days": 5,
                "bootstrap_seed": 20260719,
            }
        },
        authorized,
    )
    assert packet["scored_window"].start == authorized.score_start
    assert packet["scored_window"].end == authorized.score_end_inclusive


def test_config_rejects_a_softened_gate() -> None:
    loaded = top12_v2.load_config(root=ROOT)
    changed = json.loads(json.dumps(loaded.raw))
    changed["selection"]["floors"]["minimum_net_sharpe_inclusive"] = -1.0
    with pytest.raises(ValueError, match="frozen contract"):
        top12_v2.validate_config(changed)


def test_activated_result_commands_refuse_wide_cpu_affinity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    activation = tmp_path / TOP12_V2_LAYOUT.activation_freeze_path
    activation.parent.mkdir(parents=True)
    activation.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(orchestrator_top12_v2.os, "sched_getaffinity", lambda _pid: set(range(8)))
    with pytest.raises(orchestrator_top12_v2.OrchestratorError, match="two CPUs"):
        orchestrator_top12_v2._require_cpu_budget(tmp_path)
    monkeypatch.setattr(orchestrator_top12_v2.os, "sched_getaffinity", lambda _pid: {0, 1})
    orchestrator_top12_v2._require_cpu_budget(tmp_path)


def test_universe_reproduces_exact_weekly_six_month_top_twelve() -> None:
    report = top12_universe_v1.audit_top12_universe(ROOT)
    assert report["status"] == "passed"
    assert report["membership_rows"] == 3_708
    assert report["weekly_reconstitutions"] == 309
    assert report["ranking"] == {
        "liquidity_measure": "median-daily-quote-volume",
        "lookback_complete_days": 180,
        "point_in_time": True,
        "reconstitution": "weekly-monday-00:00-utc",
        "tie_breaker": "lexicographically-smaller-symbol",
        "universe_size": 12,
    }
    assert len(report["latest_members"]) == 12
    assert report["classification"]["forbidden_exposure_violations"] == 0


def test_config_freezes_strategy_blindness_and_disallows_team_collisions() -> None:
    loaded = top12_v2.load_config(root=ROOT)
    isolation = loaded.raw["isolation"]
    assert isolation["prior_strategy_blind"] is True
    assert isolation["cross_team_blind"] is True
    assert isolation["rediscovery_of_prior_mechanism_allowed"] is False
    assert isolation["previous_oos_tested_mechanisms_ineligible"] is True
    assert isolation["cross_team_mechanism_collision_allowed"] is False
    assert len(set(loaded.raw["mandates"].values())) == 12


def test_journal_is_hash_chained_and_an_accepted_failure_consumes_trial(
    tmp_path: Path,
) -> None:
    path = tmp_path / "journal.jsonl"
    journal_top12_v2.initialize(path)
    request = dict(journal_top12_v2.append(path, "is_accepted", _accepted("team-01", 1)))
    journal_top12_v2.append(
        path,
        "is_failed",
        {
            "team_id": "team-01",
            "run_id": request["payload"]["run_id"],
            "candidate_id": request["payload"]["candidate_id"],
            "request_sha256": request["record_sha256"],
            "failure": "synthetic failure",
        },
    )
    state = journal_top12_v2.read(path)
    assert state.trials_by_team["team-01"] == 1
    assert request["record_sha256"] in state.is_terminals
    with pytest.raises(journal_top12_v2.JournalError, match="numbering"):
        journal_top12_v2.append(path, "is_accepted", _accepted("team-01", 3))


def test_journal_rejects_early_nomination_and_detects_tampering(tmp_path: Path) -> None:
    path = tmp_path / "journal.jsonl"
    request = dict(journal_top12_v2.append(path, "is_accepted", _accepted("team-02", 1)))
    success = dict(journal_top12_v2.append(path, "is_succeeded", _success(request)))
    with pytest.raises(journal_top12_v2.JournalError, match="thirteen"):
        journal_top12_v2.append(
            path,
            "nominated",
            {
                "team_id": "team-02",
                "candidate_id": request["payload"]["candidate_id"],
                "success_record_sha256": success["record_sha256"],
                "certificate_path": "certificate.json",
                "certificate_sha256": "3" * 64,
                "nomination_path": "nomination.json",
                "nomination_sha256": "4" * 64,
            },
        )
    rows = path.read_text(encoding="ascii").splitlines()
    first = json.loads(rows[0])
    first["payload"]["purpose"] = "tampered"
    rows[0] = json.dumps(first, separators=(",", ":"), sort_keys=True)
    path.write_text("\n".join(rows) + "\n", encoding="ascii")
    with pytest.raises(journal_top12_v2.JournalError, match="hash"):
        journal_top12_v2.read(path)


def test_journal_recovers_only_an_unterminated_crash_tail(tmp_path: Path) -> None:
    path = tmp_path / "journal.jsonl"
    journal_top12_v2.append(path, "is_accepted", _accepted("team-01", 1))
    committed = path.read_bytes()
    with path.open("ab") as handle:
        handle.write(b'{"partial":')
    state = journal_top12_v2.read(path)
    assert state.record_count == 1
    assert path.read_bytes() == committed

    with path.open("ab") as handle:
        handle.write(b"{}\n")
    with pytest.raises(journal_top12_v2.JournalError, match="schema"):
        journal_top12_v2.read(path)


def test_journal_rejects_duplicate_run_ids_across_teams(tmp_path: Path) -> None:
    path = tmp_path / "journal.jsonl"
    first = _accepted("team-01", 1)
    journal_top12_v2.append(path, "is_accepted", first)
    duplicate = _accepted("team-02", 1)
    duplicate["run_id"] = first["run_id"]
    with pytest.raises(journal_top12_v2.JournalError, match="duplicate tournament run_id"):
        journal_top12_v2.append(path, "is_accepted", duplicate)


def test_journal_allows_an_empty_bracket_but_never_lowers_the_floors(
    tmp_path: Path,
) -> None:
    path = tmp_path / "journal.jsonl"
    for team_id in TOP12_V2_LAYOUT.team_ids:
        for trial in range(1, 14):
            request = dict(journal_top12_v2.append(path, "is_accepted", _accepted(team_id, trial)))
            journal_top12_v2.append(
                path,
                "is_failed",
                {
                    "team_id": team_id,
                    "run_id": request["payload"]["run_id"],
                    "candidate_id": request["payload"]["candidate_id"],
                    "request_sha256": request["record_sha256"],
                    "failure": "falsified research candidate",
                },
            )
        journal_top12_v2.append(
            path,
            "retired",
            {"team_id": team_id, "reason": "no candidate passed every frozen IS floor"},
        )
    before = journal_top12_v2.read(path)
    journal_top12_v2.append(
        path,
        "confirmation_frozen",
        {
            "input_head_sha256": before.head_sha256,
            "nominees": [],
            "confirmation_freeze_path": "tournament/top12-v2/confirmation-freeze.json",
            "confirmation_freeze_sha256": "4" * 64,
        },
    )
    before_selection = journal_top12_v2.read(path)
    selection = dict(
        journal_top12_v2.append(
            path,
            "selection_frozen",
            {
                "input_head_sha256": before_selection.head_sha256,
                "advancing": [],
                "selection_freeze_path": "tournament/top12-v2/selection-freeze.json",
                "selection_freeze_sha256": "5" * 64,
            },
        )
    )
    journal_top12_v2.append(
        path,
        "confirmation_release_authorized",
        {
            "selection_record_sha256": selection["record_sha256"],
            "terminal_record_sha256s": [],
            "staging_path": "reports-top12-v2/.is-confirmation-staging",
            "release_path": "reports-top12-v2/is-confirmation",
            "manifest_sha256": "8" * 64,
            "bundle_sha256": "9" * 64,
        },
    )
    journal_top12_v2.append(
        path,
        "release_authorized",
        {
            "selection_record_sha256": selection["record_sha256"],
            "terminal_record_sha256s": [],
            "staging_path": "reports-top12-v2/.historical-oos-staging",
            "release_path": "reports-top12-v2/historical-oos",
            "manifest_sha256": "6" * 64,
            "bundle_sha256": "7" * 64,
        },
    )
    state = journal_top12_v2.read(path)
    assert state.selection["advancing"] == []
    assert state.release is not None
    assert state.confirmation["nominees"] == []
    with pytest.raises(journal_top12_v2.JournalError, match="confirmation freeze"):
        journal_top12_v2.append(path, "is_accepted", _accepted("team-01", 14))


def _passing_is_packet() -> dict[str, object]:
    fold = {
        "base_cumulative_return": 0.10,
        "base_arithmetic_pnl": 0.08,
        "double_cost_cumulative_return": 0.06,
        "double_cost_metrics": {"net_sharpe": 0.9},
    }
    return {
        "team_id": "team-01",
        "bootstrap_probability_positive_mean": 1.0,
        "scored_window": {
            "base_metrics": {
                "net_sharpe": 1.2,
                "annualized_return": 0.10,
                "max_drawdown": 0.10,
                "positive_quarter_fraction": 0.75,
            },
            "double_cost_metrics": {"net_sharpe": 0.8},
            "triple_cost_metrics": {"net_sharpe": 0.3},
        },
        "diagnostics": {
            "annualized_turnover": 8.0,
            "gross_edge_per_turnover_bps": 100.0,
            "base_cost_share_of_positive_gross_pnl": 0.20,
            "long_gross_pnl": 0.08,
            "short_gross_pnl": 0.04,
            "top_five_day_absolute_return_share": 0.20,
            "maximum_fold_positive_pnl_share": 0.25,
        },
        "folds": [dict(fold) for _ in range(6)],
        "regime_sharpe": {"bull": 0.8, "bear": 0.4, "chop": 0.3, "stress": -0.2},
    }


def test_is_selection_is_conjunctive_and_includes_neighborhood_gate() -> None:
    config = top12_v2.load_config(root=ROOT).raw
    packet = _passing_is_packet()
    failed = scoring_top12_v2.assess_is(packet, config, trial_count=13)
    assert failed["eligible"] is False
    assert failed["gates"]["neighborhood_stability"] is False
    passed = scoring_top12_v2.assess_is(packet, config, trial_count=13, neighborhood_passed=True)
    assert passed["eligible"] is True
    packet["diagnostics"]["annualized_turnover"] = 18.0001
    result = scoring_top12_v2.assess_is(packet, config, trial_count=13, neighborhood_passed=True)
    assert result["eligible"] is False
    assert result["gates"]["annualized_turnover"] is False


def test_confirmation_is_conjunctive_and_has_no_soft_backfill() -> None:
    config = top12_v2.load_config(root=ROOT).raw
    packet = {
        "team_id": "team-01",
        "scored_window": {
            "base_metrics": {
                "annualized_return": 0.08,
                "net_sharpe": 0.90,
                "max_drawdown": 0.12,
                "positive_quarter_fraction": 0.75,
            },
            "double_cost_metrics": {"annualized_return": 0.04, "net_sharpe": 0.60},
        },
        "diagnostics": {
            "annualized_turnover": 10.0,
            "gross_edge_per_turnover_bps": 70.0,
            "base_cost_share_of_positive_gross_pnl": 0.20,
        },
    }
    passed = scoring_top12_v2.assess_is_confirmation(packet, config)
    assert passed["eligible"] is True
    packet["scored_window"]["double_cost_metrics"]["net_sharpe"] = 0.49
    failed = scoring_top12_v2.assess_is_confirmation(packet, config)
    assert failed["eligible"] is False
    assert failed["gates"]["double_cost_sharpe"] is False
    assert config["is_confirmation"]["no_qualifier_means_no_finalist"] is True


def test_neighborhood_coordinate_identity_normalizes_signed_zero() -> None:
    positive = orchestrator_top12_v2._coordinate_vector_key({"lookback": 0.0, "buffer": 1})
    negative = orchestrator_top12_v2._coordinate_vector_key({"lookback": -0.0, "buffer": 1.0})
    assert positive == negative


def test_confirmation_ranking_prefers_the_stronger_generalization_floor() -> None:
    def row(team_id: str, confirmation: float, median: float, worst: float) -> dict[str, object]:
        return {
            "team_id": team_id,
            "confirmation": {
                "ranking_vector": {
                    "double_cost_sharpe": confirmation,
                    "base_annualized_return": 0.10,
                }
            },
            "selection": {
                "ranking_vector": {
                    "median_fold_double_cost_sharpe": median,
                    "worst_fold_double_cost_sharpe": worst,
                }
            },
        }

    candidates = [
        row("team-01", 1.8, 0.8, 0.0),
        row("team-02", 1.1, 1.1, 0.2),
        row("team-03", 0.9, 1.4, 0.3),
    ]
    candidates.sort(key=orchestrator_top12_v2._confirmation_selection_key)
    assert [candidate["team_id"] for candidate in candidates] == [
        "team-02",
        "team-03",
        "team-01",
    ]


def test_nomination_retry_replaces_only_an_unjournaled_orphan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    team_id = "team-01"
    authority = orchestrator_top12_v2.CandidateAuthority(**_candidate_authority(team_id))
    candidate_id = authority.candidate_id
    state = SimpleNamespace(
        selection=None,
        confirmation=None,
        nominations={},
        retired={},
        trials_by_team={team_id: 13},
    )
    loaded = SimpleNamespace(
        sha256="8" * 64,
        raw={"research": {"minimum_accepted_trials_before_nomination": 13}},
    )
    terminal = {
        "payload": {"summary_path": "summary.json", "summary_sha256": "2" * 64}
    }
    request = {"payload": {"authority": authority.as_dict()}}
    append_attempts = 0

    def append(_path: Path, event_type: str, _payload: dict[str, object]) -> dict[str, str]:
        nonlocal append_attempts
        assert event_type == "nominated"
        append_attempts += 1
        if append_attempts == 1:
            raise OSError("simulated crash after nomination projection")
        return {"record_sha256": "f" * 64}

    monkeypatch.setattr(activation_top12_v2, "validate", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(top12_v2, "load_config", lambda *_args, **_kwargs: loaded)
    monkeypatch.setattr(
        orchestrator_top12_v2,
        "_close_interrupted_is_requests",
        lambda _root: state,
    )
    monkeypatch.setattr(
        orchestrator_top12_v2,
        "_candidate_success",
        lambda *_args: ("3" * 64, terminal, "4" * 64, request),
    )
    monkeypatch.setattr(
        orchestrator_top12_v2, "_validate_authority_current", lambda *_args: authority
    )
    monkeypatch.setattr(orchestrator_top12_v2, "_verified_summary", lambda *_args: {})
    monkeypatch.setattr(
        orchestrator_top12_v2,
        "_certificate",
        lambda *_args, **_kwargs: ({"schema_version": 1}, "5" * 64, {}),
    )
    monkeypatch.setattr(
        scoring_top12_v2,
        "assess_is",
        lambda *_args, **_kwargs: {"eligible": True, "gates": {}},
    )
    monkeypatch.setattr(orchestrator_top12_v2, "_write_nomination_registry", lambda *_args: None)
    monkeypatch.setattr(journal_top12_v2, "append", append)
    monkeypatch.setattr(journal_top12_v2, "read", lambda _path: state)

    certificate = "tournament/top12-v2/certificates/team-01/research.json"
    with pytest.raises(OSError, match="simulated crash"):
        orchestrator_top12_v2.nominate(tmp_path, team_id, candidate_id, certificate)
    nomination_path = (
        tmp_path / f"tournament/top12-v2/nominations/{team_id}-{candidate_id}.json"
    )
    assert json.loads(nomination_path.read_text())["trial_count"] == 13

    state.trials_by_team[team_id] = 14
    result = orchestrator_top12_v2.nominate(tmp_path, team_id, candidate_id, certificate)

    assert result["ok"] is True
    assert append_attempts == 2
    assert json.loads(nomination_path.read_text())["trial_count"] == 14


def test_close_is_idempotency_verifies_the_journal_bound_freeze(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = SimpleNamespace(
        selection={
            "advancing": ["team-01"],
            "selection_freeze_path": TOP12_V2_LAYOUT.selection_freeze_path,
        },
        nominations={},
        retired={},
    )
    checked = False

    def reject_corrupt_freeze(_root: Path, observed: SimpleNamespace):
        nonlocal checked
        checked = True
        assert observed is state
        raise orchestrator_top12_v2.OrchestratorError(
            "selection freeze changed after journal binding"
        )

    monkeypatch.setattr(activation_top12_v2, "validate", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        top12_v2,
        "load_config",
        lambda *_args, **_kwargs: SimpleNamespace(raw={}, sha256="1" * 64),
    )
    monkeypatch.setattr(
        orchestrator_top12_v2,
        "_close_interrupted_is_requests",
        lambda _root: state,
    )
    monkeypatch.setattr(orchestrator_top12_v2, "_write_nomination_registry", lambda *_args: None)
    monkeypatch.setattr(orchestrator_top12_v2, "_selection_freeze", reject_corrupt_freeze)

    with pytest.raises(orchestrator_top12_v2.OrchestratorError, match="journal binding"):
        orchestrator_top12_v2.close_is(tmp_path)
    assert checked is True


def test_historical_batch_accepts_every_finalist_before_first_snapshot_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    team_ids = ("team-01", "team-02")
    selection = _historical_selection(team_ids)
    state = SimpleNamespace(
        release=None,
        historical_requests={},
        historical_starts={},
        historical_terminals={},
        selection_record_sha256="a" * 64,
    )
    events: list[dict[str, object]] = []
    validations: list[bool] = []

    def validate(_root: Path, *, verify_universe_snapshot: bool = True) -> dict[str, object]:
        validations.append(verify_universe_snapshot)
        if verify_universe_snapshot:
            assert set(state.historical_requests) == set(team_ids)
            assert state.historical_starts == {}
            raise RuntimeError("first snapshot read sentinel")
        return {}

    monkeypatch.setattr(activation_top12_v2, "validate", validate)
    monkeypatch.setattr(
        top12_v2,
        "load_config",
        lambda *_args, **_kwargs: SimpleNamespace(raw={}, sha256="b" * 64),
    )
    monkeypatch.setattr(journal_top12_v2, "read", lambda _path: state)
    monkeypatch.setattr(journal_top12_v2, "append", _historical_append_stub(state, events))
    monkeypatch.setattr(orchestrator_top12_v2, "_selection_freeze", lambda *_args: selection)

    with pytest.raises(RuntimeError, match="first snapshot read sentinel"):
        orchestrator_top12_v2.historical_release(tmp_path)

    assert validations == [False, True]
    assert [event["event_type"] for event in events] == [
        "historical_accepted",
        "historical_accepted",
    ]


def test_historical_base_exception_stops_after_recording_only_the_started_dnf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class StopTournamentError(BaseException):
        pass

    team_ids = ("team-01", "team-02")
    selection = _historical_selection(team_ids)
    requests = {
        team_id: _historical_request(team_id, sequence)
        for sequence, team_id in enumerate(team_ids, start=1)
    }
    state = SimpleNamespace(
        release=None,
        historical_requests=requests,
        historical_starts={},
        historical_terminals={},
        selection_record_sha256="a" * 64,
    )
    events: list[dict[str, object]] = []

    monkeypatch.setattr(activation_top12_v2, "validate", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        top12_v2,
        "load_config",
        lambda *_args, **_kwargs: SimpleNamespace(raw={}, sha256="b" * 64),
    )
    monkeypatch.setattr(journal_top12_v2, "read", lambda _path: state)
    monkeypatch.setattr(journal_top12_v2, "append", _historical_append_stub(state, events))
    monkeypatch.setattr(orchestrator_top12_v2, "_selection_freeze", lambda *_args: selection)
    monkeypatch.setattr(
        orchestrator_top12_v2,
        "_validate_authority_current",
        lambda _root, _loaded, expected: orchestrator_top12_v2.CandidateAuthority(**dict(expected)),
    )
    monkeypatch.setattr(
        orchestrator_top12_v2,
        "_run_team",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(StopTournamentError()),
    )

    with pytest.raises(StopTournamentError):
        orchestrator_top12_v2.historical_release(tmp_path)

    assert [event["event_type"] for event in events] == [
        "historical_started",
        "historical_failed",
    ]
    assert events[-1]["payload"]["failure_code"] == "candidate-execution-dnf"
    assert set(state.historical_starts) == {"team-01"}
    assert set(state.historical_terminals) == {"team-01"}


def test_authorized_release_rebuilds_missing_staging_before_promotion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    release = {
        "staging_path": "reports-top12-v2/.historical-oos-staging",
        "release_path": "reports-top12-v2/historical-oos",
        "manifest_sha256": "a" * 64,
        "bundle_sha256": "b" * 64,
    }
    state = SimpleNamespace(release=release)
    calls: list[str] = []
    promotion_attempts = 0

    def promote(_root: Path, observed: dict[str, object]) -> dict[str, object]:
        nonlocal promotion_attempts
        assert observed is release
        promotion_attempts += 1
        calls.append("promote")
        if promotion_attempts == 1:
            raise orchestrator_top12_v2.OrchestratorError("authorized staging is missing")
        return {"ok": True, "release_path": release["release_path"], "recovered": False}

    def rebuild(_root: Path, _selection: dict[str, object], observed: SimpleNamespace):
        assert observed is state
        calls.append("rebuild")
        return release["staging_path"], release["release_path"], release["manifest_sha256"]

    def validate(*_args, **kwargs) -> None:
        calls.append("validate")
        assert kwargs["manifest_sha256"] == release["manifest_sha256"]
        assert kwargs["bundle_sha256"] == release["bundle_sha256"]

    monkeypatch.setattr(orchestrator_top12_v2, "_promote_authorized", promote)
    monkeypatch.setattr(orchestrator_top12_v2, "_release_bundle", rebuild)
    monkeypatch.setattr(
        orchestrator_top12_v2,
        "_strict_object",
        lambda *_args: {"bundle_sha256": release["bundle_sha256"]},
    )
    monkeypatch.setattr(orchestrator_top12_v2, "_validate_staged_release", validate)

    result = orchestrator_top12_v2._recover_authorized_release(tmp_path, {}, state)

    assert calls == ["promote", "rebuild", "validate", "promote"]
    assert result["recovered"] is True


def test_inverse_volatility_cap_leaves_cash_when_bracket_is_too_small(
    tmp_path: Path,
) -> None:
    nominees = []
    for index, team_id in enumerate(("team-01", "team-02"), start=1):
        artifact = tmp_path / f"{team_id}.csv"
        frame = pd.DataFrame(
            {
                    "date": pd.date_range("2020-08-03", "2023-07-01", inclusive="left", tz="UTC"),
            }
        )
        frame["net_return"] = [(-1) ** day * 0.001 * index for day in range(len(frame))]
        artifact.write_text(frame.to_csv(index=False), encoding="utf-8")
        summary = {
            "runner": {
                "artifacts": {"daily_returns": artifact.relative_to(tmp_path).as_posix()},
                "artifact_sha256": {
                    "daily_returns": hashlib.sha256(artifact.read_bytes()).hexdigest()
                },
            }
        }
        summary_path = tmp_path / f"{team_id}.json"
        summary_path.write_text(json.dumps(summary), encoding="utf-8")
        nominees.append(
            {
                "team_id": team_id,
                "summary_path": summary_path.relative_to(tmp_path).as_posix(),
                "summary_sha256": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
            }
        )
    weights, cash = orchestrator_top12_v2._capped_inverse_vol_weights(tmp_path, nominees, 0.30)
    assert sum(weights.values()) == pytest.approx(0.60)
    assert max(weights.values()) <= 0.30
    assert cash == pytest.approx(0.40)


def test_source_archive_accepts_team_12_namespace(tmp_path: Path) -> None:
    files = (
        source_archive_top12_v2.SourceFile(
            path="strategy.py",
            size=4,
            sha256=hashlib.sha256(b"pass").hexdigest(),
            content=b"pass",
        ),
    )
    bundle = source_archive_top12_v2.bundle_fingerprint(item.manifest_entry for item in files)
    archive = source_archive_top12_v2.write_source_archive(
        tmp_path,
        team_id="team-12",
        candidate_id="team12-test-v1",
        candidate_root="tournament/top12-v2/teams/team-12/candidates/team12-test-v1",
        entrypoint="strategy.py",
        source_bundle_sha256=bundle,
        files=files,
    )
    loaded = source_archive_top12_v2.read_source_archive(
        tmp_path, archive.path, archive.sha256, expected_team_id="team-12"
    )
    assert loaded.source_bundle_sha256 == bundle


def test_worker_bundle_is_materialized_from_archive_bytes(tmp_path: Path) -> None:
    content = b"def build_strategy():\n    return None\n"
    files = (
        source_archive_top12_v2.SourceFile(
            path="strategy.py",
            size=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
            content=content,
        ),
    )
    manifest = tuple(item.manifest_entry for item in files)
    bundle = source_archive_top12_v2.bundle_fingerprint(manifest)
    destination = tmp_path / "bundle"
    assert (
        runner_top12_v2._stage_archived_source_bundle(
            destination,
            files,
            expected_fingerprint=bundle,
            expected_entries=manifest,
        )
        == bundle
    )
    assert (destination / "strategy.py").read_bytes() == content


def test_artifact_publisher_keeps_independent_base_double_and_triple_cost_runs(
    tmp_path: Path,
) -> None:
    index = pd.date_range("2021-01-01", periods=3, freq="8h", tz="UTC")

    def evaluation(value: float) -> EvaluationResult:
        return EvaluationResult(
            returns=pd.DataFrame({"net_return": value}, index=index),
            positions=pd.DataFrame({"BTCUSDT": 0.0}, index=index),
            events=pd.DataFrame(),
        )

    daily_index = pd.date_range("2021-01-01", periods=1, tz="UTC")
    artifacts = runner_top12_v2._publish_artifacts(
        tmp_path,
        "team-12",
        stage="is",
        output_relative="reports-top12-v2/is/team-12/triple-test",
        targets=pd.DataFrame({"BTCUSDT": 0.0}, index=index),
        base=evaluation(0.001),
        stressed=evaluation(0.0005),
        triple=evaluation(0.0001),
        base_daily=pd.Series([0.003], index=daily_index),
        stressed_daily=pd.Series([0.0015], index=daily_index),
        triple_daily=pd.Series([0.0003], index=daily_index),
    )
    assert set(artifacts) >= {
        "evaluator_returns",
        "double_cost_evaluator_returns",
        "triple_cost_evaluator_returns",
        "daily_returns",
        "double_cost_daily_returns",
        "triple_cost_daily_returns",
    }
    triple = pd.read_csv(tmp_path / artifacts["triple_cost_daily_returns"])
    assert triple["net_return"].iloc[0] == pytest.approx(0.0003)


def test_worker_masks_all_data_tournament_and_report_namespaces(tmp_path: Path) -> None:
    from crypto_trade.tournament import _strategy_worker_v4

    (tmp_path / "reports-unrelated").mkdir()
    sensitive = set(_strategy_worker_v4._sensitive_paths(tmp_path))
    assert (tmp_path / "data").absolute() in sensitive
    assert (tmp_path / "tournament").absolute() in sensitive
    assert (tmp_path / "reports-unrelated").absolute() in sensitive


def test_authority_path_helpers_reject_symlink_components(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    (real / "authority.py").write_text("pass\n", encoding="utf-8")
    (tmp_path / "alias").symlink_to(real, target_is_directory=True)
    with pytest.raises(orchestrator_top12_v2.OrchestratorError, match="symlink"):
        orchestrator_top12_v2._path(tmp_path, "alias/authority.py")
    with pytest.raises(activation_top12_v2.ActivationError, match="symlink"):
        activation_top12_v2._file(tmp_path, "alias/authority.py")


def test_activation_scope_is_explicit_and_complete() -> None:
    assert len(activation_top12_v2.FROZEN_SCOPE) == len(set(activation_top12_v2.FROZEN_SCOPE))
    missing = [
        relative for relative in activation_top12_v2.FROZEN_SCOPE if not (ROOT / relative).is_file()
    ]
    assert missing == []
