from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from crypto_trade.tournament import (
    activation_v4,
    journal_v4,
    orchestrator_v4,
    runner_v4,
    scoring_v4,
    source_archive_v4,
    top40_v4,
)
from crypto_trade.tournament.engine_v2 import EvaluationResult
from crypto_trade.tournament.layout_v4 import TOP40_V4_LAYOUT

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
        "output_path": f"reports-top40-v4-r1/is/{team_id}/run-{trial:02d}",
    }


def _success(request: dict[str, object]) -> dict[str, object]:
    payload = request["payload"]
    return {
        "team_id": payload["team_id"],
        "run_id": payload["run_id"],
        "candidate_id": payload["candidate_id"],
        "request_sha256": request["record_sha256"],
        "summary_path": f"reports-top40-v4-r1/is/{payload['team_id']}/summary.json",
        "summary_sha256": "2" * 64,
    }


def _candidate_authority(team_id: str) -> dict[str, str]:
    candidate_id = f"{team_id.replace('-', '')}-finalist-v1"
    candidate_root = f"tournament/top40-v4-r1/teams/{team_id}/candidates/{candidate_id}"
    digest = hashlib.sha256(team_id.encode("ascii")).hexdigest()
    return {
        "team_id": team_id,
        "candidate_id": candidate_id,
        "candidate_root": candidate_root,
        "entrypoint": f"{candidate_root}/strategy.py",
        "source_bundle_sha256": digest,
        "source_archive_path": (
            f"tournament/top40-v4-r1/source-archives/{team_id}/{candidate_id}.json"
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
                f"tournament/top40-v4-r1/private/historical-oos/{team_id}/{run_id}"
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


def test_v4_contract_has_twelve_teams_and_only_two_historical_stages() -> None:
    loaded = top40_v4.load_config(root=ROOT)
    assert loaded.raw["teams"] == list(TOP40_V4_LAYOUT.team_ids)
    assert TOP40_V4_LAYOUT.team_ids[-1] == "team-12"
    assert runner_v4._authorized_window(loaded.raw, "is").score_start == "2020-02-03T00:00:00Z"
    historical = runner_v4._authorized_window(loaded.raw, "historical_oos")
    assert historical.score_start == "2024-07-01T00:00:00Z"
    assert historical.end_exclusive == "2026-07-01T00:00:00Z"
    with pytest.raises(ValueError, match="is or historical_oos"):
        runner_v4._authorized_window(loaded.raw, "validation")


def test_metric_window_normalizes_utc_start_and_date_only_end() -> None:
    index = pd.date_range("2020-02-03T00:00:00Z", periods=180, freq="1D")
    daily = pd.Series([0.001, -0.0005] * 90, index=index, name="net_return")
    authorized = runner_v4.AuthorizedWindow(
        stage="is",
        replay_start="2020-02-03T00:00:00Z",
        end_exclusive="2020-08-01T00:00:00Z",
        score_start="2020-02-03T00:00:00Z",
        score_end_inclusive="2020-07-31",
    )
    packet = runner_v4._compute_metrics(
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
    loaded = top40_v4.load_config(root=ROOT)
    changed = json.loads(json.dumps(loaded.raw))
    changed["selection"]["floors"]["minimum_net_sharpe_inclusive"] = -1.0
    with pytest.raises(ValueError, match="frozen contract"):
        top40_v4.validate_config(changed)


def test_journal_is_hash_chained_and_an_accepted_failure_consumes_trial(
    tmp_path: Path,
) -> None:
    path = tmp_path / "journal.jsonl"
    journal_v4.initialize(path)
    request = dict(journal_v4.append(path, "is_accepted", _accepted("team-01", 1)))
    journal_v4.append(
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
    state = journal_v4.read(path)
    assert state.trials_by_team["team-01"] == 1
    assert request["record_sha256"] in state.is_terminals
    with pytest.raises(journal_v4.JournalError, match="numbering"):
        journal_v4.append(path, "is_accepted", _accepted("team-01", 3))


def test_journal_rejects_early_nomination_and_detects_tampering(tmp_path: Path) -> None:
    path = tmp_path / "journal.jsonl"
    request = dict(journal_v4.append(path, "is_accepted", _accepted("team-02", 1)))
    success = dict(journal_v4.append(path, "is_succeeded", _success(request)))
    with pytest.raises(journal_v4.JournalError, match="eight"):
        journal_v4.append(
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
    with pytest.raises(journal_v4.JournalError, match="hash"):
        journal_v4.read(path)


def test_journal_recovers_only_an_unterminated_crash_tail(tmp_path: Path) -> None:
    path = tmp_path / "journal.jsonl"
    journal_v4.append(path, "is_accepted", _accepted("team-01", 1))
    committed = path.read_bytes()
    with path.open("ab") as handle:
        handle.write(b'{"partial":')
    state = journal_v4.read(path)
    assert state.record_count == 1
    assert path.read_bytes() == committed

    with path.open("ab") as handle:
        handle.write(b"{}\n")
    with pytest.raises(journal_v4.JournalError, match="schema"):
        journal_v4.read(path)


def test_journal_rejects_duplicate_run_ids_across_teams(tmp_path: Path) -> None:
    path = tmp_path / "journal.jsonl"
    first = _accepted("team-01", 1)
    journal_v4.append(path, "is_accepted", first)
    duplicate = _accepted("team-02", 1)
    duplicate["run_id"] = first["run_id"]
    with pytest.raises(journal_v4.JournalError, match="duplicate tournament run_id"):
        journal_v4.append(path, "is_accepted", duplicate)


def test_journal_allows_an_empty_bracket_but_never_lowers_the_floors(
    tmp_path: Path,
) -> None:
    path = tmp_path / "journal.jsonl"
    for team_id in TOP40_V4_LAYOUT.team_ids:
        for trial in range(1, 9):
            request = dict(journal_v4.append(path, "is_accepted", _accepted(team_id, trial)))
            journal_v4.append(
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
        journal_v4.append(
            path,
            "retired",
            {"team_id": team_id, "reason": "no candidate passed every frozen IS floor"},
        )
    before = journal_v4.read(path)
    selection = dict(
        journal_v4.append(
            path,
            "selection_frozen",
            {
                "input_head_sha256": before.head_sha256,
                "advancing": [],
                "selection_freeze_path": "tournament/top40-v4-r1/selection-freeze.json",
                "selection_freeze_sha256": "5" * 64,
            },
        )
    )
    journal_v4.append(
        path,
        "release_authorized",
        {
            "selection_record_sha256": selection["record_sha256"],
            "terminal_record_sha256s": [],
            "staging_path": "reports-top40-v4-r1/.historical-oos-staging",
            "release_path": "reports-top40-v4-r1/historical-oos",
            "manifest_sha256": "6" * 64,
            "bundle_sha256": "7" * 64,
        },
    )
    state = journal_v4.read(path)
    assert state.selection["advancing"] == []
    assert state.release is not None
    with pytest.raises(journal_v4.JournalError, match="selection freeze"):
        journal_v4.append(path, "is_accepted", _accepted("team-01", 9))


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
            "triple_cost_metrics": {"net_sharpe": 0.2},
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
        "folds": [dict(fold) for _ in range(5)],
        "regime_sharpe": {"bull": 0.8, "bear": 0.4, "chop": 0.3, "stress": -0.2},
    }


def test_is_selection_is_conjunctive_and_includes_neighborhood_gate() -> None:
    config = top40_v4.load_config(root=ROOT).raw
    packet = _passing_is_packet()
    failed = scoring_v4.assess_is(packet, config, trial_count=8)
    assert failed["eligible"] is False
    assert failed["gates"]["neighborhood_stability"] is False
    passed = scoring_v4.assess_is(packet, config, trial_count=8, neighborhood_passed=True)
    assert passed["eligible"] is True
    packet["diagnostics"]["annualized_turnover"] = 20.0001
    result = scoring_v4.assess_is(packet, config, trial_count=8, neighborhood_passed=True)
    assert result["eligible"] is False
    assert result["gates"]["annualized_turnover"] is False


def test_neighborhood_coordinate_identity_normalizes_signed_zero() -> None:
    positive = orchestrator_v4._coordinate_vector_key({"lookback": 0.0, "buffer": 1})
    negative = orchestrator_v4._coordinate_vector_key({"lookback": -0.0, "buffer": 1.0})
    assert positive == negative


@pytest.mark.parametrize(
    ("team_ids", "expected"),
    [
        (
            ("team-06", "team-03", "team-01", "team-05", "team-02", "team-04"),
            ["team-01", "team-02", "team-03", "team-04", "team-05"],
        ),
        (("team-03", "team-02", "team-01"), ["team-01", "team-02", "team-03"]),
    ],
)
def test_close_is_selects_exact_top_five_and_never_backfills(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    team_ids: tuple[str, ...],
    expected: list[str],
) -> None:
    scores = {
        "team-01": 1.0,
        "team-02": 1.0,
        "team-03": 0.9,
        "team-04": 0.8,
        "team-05": 0.7,
        "team-06": 0.6,
    }
    nominations: dict[str, dict[str, object]] = {}
    for team_id in team_ids:
        authority = _candidate_authority(team_id)
        nomination = {
            "team_id": team_id,
            "candidate_id": authority["candidate_id"],
            "trial_count": 8,
            "authority": authority,
            "selection": {
                "eligible": True,
                "ranking_vector": {
                    "worst_fold_double_cost_sharpe": scores[team_id],
                    "median_fold_double_cost_sharpe": scores[team_id],
                    "trial_adjusted_confidence": 0.95,
                    "gross_edge_per_turnover_bps": 100.0,
                    "annualized_turnover": 8.0,
                    "team_id": team_id,
                },
            },
        }
        nominations[team_id] = {
            "payload": {
                "nomination_path": f"nominations/{team_id}.json",
                "nomination_sha256": hashlib.sha256(team_id.encode("ascii")).hexdigest(),
            },
            "nomination": nomination,
        }
    state = SimpleNamespace(
        selection=None,
        nominations=nominations,
        retired={
            team_id: {} for team_id in TOP40_V4_LAYOUT.team_ids if team_id not in nominations
        },
        head_sha256="a" * 64,
    )
    loaded = SimpleNamespace(
        sha256="b" * 64,
        raw={
            "selection": {"ranking": {"advance_count": 5}},
            "ensemble": {
                "weight_method": "capped-inverse-is-volatility",
                "maximum_constituent_weight": 0.30,
            },
        },
    )
    captured: dict[str, object] = {}

    def append(_path: Path, event_type: str, payload: dict[str, object]) -> dict[str, str]:
        assert event_type == "selection_frozen"
        captured.update(payload)
        return {"record_sha256": "c" * 64}

    def weights(_root: Path, nominees: list[dict[str, object]], cap: float):
        allocation = min(cap, 1.0 / len(nominees))
        result = {str(row["team_id"]): allocation for row in nominees}
        return result, 1.0 - allocation * len(nominees)

    monkeypatch.setattr(
        activation_v4,
        "validate",
        lambda *_args, **_kwargs: {"record_sha256": "d" * 64},
    )
    monkeypatch.setattr(top40_v4, "load_config", lambda *_args, **_kwargs: loaded)
    monkeypatch.setattr(orchestrator_v4, "_close_interrupted_is_requests", lambda _root: state)
    monkeypatch.setattr(orchestrator_v4, "_write_nomination_registry", lambda *_args: None)
    monkeypatch.setattr(
        orchestrator_v4, "_verified_nomination", lambda _root, record: record["nomination"]
    )
    monkeypatch.setattr(orchestrator_v4, "_capped_inverse_vol_weights", weights)
    monkeypatch.setattr(journal_v4, "append", append)

    result = orchestrator_v4.close_is(tmp_path)

    assert result["advancing"] == expected
    assert captured["advancing"] == expected
    freeze = json.loads((tmp_path / TOP40_V4_LAYOUT.selection_freeze_path).read_text())
    assert [row["team_id"] for row in freeze["advancing"]] == expected


def test_nomination_retry_replaces_only_an_unjournaled_orphan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    team_id = "team-01"
    authority = orchestrator_v4.CandidateAuthority(**_candidate_authority(team_id))
    candidate_id = authority.candidate_id
    state = SimpleNamespace(
        selection=None,
        nominations={},
        retired={},
        trials_by_team={team_id: 8},
    )
    loaded = SimpleNamespace(
        sha256="8" * 64,
        raw={"research": {"minimum_accepted_trials_before_nomination": 8}},
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

    monkeypatch.setattr(activation_v4, "validate", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(top40_v4, "load_config", lambda *_args, **_kwargs: loaded)
    monkeypatch.setattr(orchestrator_v4, "_close_interrupted_is_requests", lambda _root: state)
    monkeypatch.setattr(
        orchestrator_v4,
        "_candidate_success",
        lambda *_args: ("3" * 64, terminal, "4" * 64, request),
    )
    monkeypatch.setattr(
        orchestrator_v4, "_validate_authority_current", lambda *_args: authority
    )
    monkeypatch.setattr(orchestrator_v4, "_verified_summary", lambda *_args: {})
    monkeypatch.setattr(
        orchestrator_v4,
        "_certificate",
        lambda *_args, **_kwargs: ({"schema_version": 1}, "5" * 64, {}),
    )
    monkeypatch.setattr(
        scoring_v4,
        "assess_is",
        lambda *_args, **_kwargs: {"eligible": True, "gates": {}},
    )
    monkeypatch.setattr(orchestrator_v4, "_write_nomination_registry", lambda *_args: None)
    monkeypatch.setattr(journal_v4, "append", append)
    monkeypatch.setattr(journal_v4, "read", lambda _path: state)

    certificate = "tournament/top40-v4-r1/certificates/team-01/research.json"
    with pytest.raises(OSError, match="simulated crash"):
        orchestrator_v4.nominate(tmp_path, team_id, candidate_id, certificate)
    nomination_path = (
        tmp_path / f"tournament/top40-v4-r1/nominations/{team_id}-{candidate_id}.json"
    )
    assert json.loads(nomination_path.read_text())["trial_count"] == 8

    state.trials_by_team[team_id] = 9
    result = orchestrator_v4.nominate(tmp_path, team_id, candidate_id, certificate)

    assert result["ok"] is True
    assert append_attempts == 2
    assert json.loads(nomination_path.read_text())["trial_count"] == 9


def test_close_is_idempotency_verifies_the_journal_bound_freeze(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = SimpleNamespace(
        selection={
            "advancing": ["team-01"],
            "selection_freeze_path": TOP40_V4_LAYOUT.selection_freeze_path,
        },
        nominations={},
        retired={},
    )
    checked = False

    def reject_corrupt_freeze(_root: Path, observed: SimpleNamespace):
        nonlocal checked
        checked = True
        assert observed is state
        raise orchestrator_v4.OrchestratorError("selection freeze changed after journal binding")

    monkeypatch.setattr(activation_v4, "validate", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        top40_v4,
        "load_config",
        lambda *_args, **_kwargs: SimpleNamespace(raw={}, sha256="1" * 64),
    )
    monkeypatch.setattr(orchestrator_v4, "_close_interrupted_is_requests", lambda _root: state)
    monkeypatch.setattr(orchestrator_v4, "_write_nomination_registry", lambda *_args: None)
    monkeypatch.setattr(orchestrator_v4, "_selection_freeze", reject_corrupt_freeze)

    with pytest.raises(orchestrator_v4.OrchestratorError, match="journal binding"):
        orchestrator_v4.close_is(tmp_path)
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

    monkeypatch.setattr(activation_v4, "validate", validate)
    monkeypatch.setattr(
        top40_v4,
        "load_config",
        lambda *_args, **_kwargs: SimpleNamespace(raw={}, sha256="b" * 64),
    )
    monkeypatch.setattr(journal_v4, "read", lambda _path: state)
    monkeypatch.setattr(journal_v4, "append", _historical_append_stub(state, events))
    monkeypatch.setattr(orchestrator_v4, "_selection_freeze", lambda *_args: selection)

    with pytest.raises(RuntimeError, match="first snapshot read sentinel"):
        orchestrator_v4.historical_release(tmp_path)

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

    monkeypatch.setattr(activation_v4, "validate", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        top40_v4,
        "load_config",
        lambda *_args, **_kwargs: SimpleNamespace(raw={}, sha256="b" * 64),
    )
    monkeypatch.setattr(journal_v4, "read", lambda _path: state)
    monkeypatch.setattr(journal_v4, "append", _historical_append_stub(state, events))
    monkeypatch.setattr(orchestrator_v4, "_selection_freeze", lambda *_args: selection)
    monkeypatch.setattr(
        orchestrator_v4,
        "_validate_authority_current",
        lambda _root, _loaded, expected: orchestrator_v4.CandidateAuthority(**dict(expected)),
    )
    monkeypatch.setattr(
        orchestrator_v4,
        "_run_team",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(StopTournamentError()),
    )

    with pytest.raises(StopTournamentError):
        orchestrator_v4.historical_release(tmp_path)

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
        "staging_path": "reports-top40-v4-r1/.historical-oos-staging",
        "release_path": "reports-top40-v4-r1/historical-oos",
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
            raise orchestrator_v4.OrchestratorError("authorized staging is missing")
        return {"ok": True, "release_path": release["release_path"], "recovered": False}

    def rebuild(_root: Path, _selection: dict[str, object], observed: SimpleNamespace):
        assert observed is state
        calls.append("rebuild")
        return release["staging_path"], release["release_path"], release["manifest_sha256"]

    def validate(*_args, **kwargs) -> None:
        calls.append("validate")
        assert kwargs["manifest_sha256"] == release["manifest_sha256"]
        assert kwargs["bundle_sha256"] == release["bundle_sha256"]

    monkeypatch.setattr(orchestrator_v4, "_promote_authorized", promote)
    monkeypatch.setattr(orchestrator_v4, "_release_bundle", rebuild)
    monkeypatch.setattr(
        orchestrator_v4,
        "_strict_object",
        lambda *_args: {"bundle_sha256": release["bundle_sha256"]},
    )
    monkeypatch.setattr(orchestrator_v4, "_validate_staged_release", validate)

    result = orchestrator_v4._recover_authorized_release(tmp_path, {}, state)

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
                "date": pd.date_range("2020-02-03", "2024-07-01", inclusive="left", tz="UTC"),
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
    weights, cash = orchestrator_v4._capped_inverse_vol_weights(tmp_path, nominees, 0.30)
    assert sum(weights.values()) == pytest.approx(0.60)
    assert max(weights.values()) <= 0.30
    assert cash == pytest.approx(0.40)


def test_source_archive_accepts_team_12_namespace(tmp_path: Path) -> None:
    files = (
        source_archive_v4.SourceFile(
            path="strategy.py",
            size=4,
            sha256=hashlib.sha256(b"pass").hexdigest(),
            content=b"pass",
        ),
    )
    bundle = source_archive_v4.bundle_fingerprint(item.manifest_entry for item in files)
    archive = source_archive_v4.write_source_archive(
        tmp_path,
        team_id="team-12",
        candidate_id="team12-test-v1",
        candidate_root="tournament/top40-v4-r1/teams/team-12/candidates/team12-test-v1",
        entrypoint="strategy.py",
        source_bundle_sha256=bundle,
        files=files,
    )
    loaded = source_archive_v4.read_source_archive(
        tmp_path, archive.path, archive.sha256, expected_team_id="team-12"
    )
    assert loaded.source_bundle_sha256 == bundle


def test_worker_bundle_is_materialized_from_archive_bytes(tmp_path: Path) -> None:
    content = b"def build_strategy():\n    return None\n"
    files = (
        source_archive_v4.SourceFile(
            path="strategy.py",
            size=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
            content=content,
        ),
    )
    manifest = tuple(item.manifest_entry for item in files)
    bundle = source_archive_v4.bundle_fingerprint(manifest)
    destination = tmp_path / "bundle"
    assert (
        runner_v4._stage_archived_source_bundle(
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
    artifacts = runner_v4._publish_artifacts(
        tmp_path,
        "team-12",
        stage="is",
        output_relative="reports-top40-v4-r1/is/team-12/triple-test",
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
    with pytest.raises(orchestrator_v4.OrchestratorError, match="symlink"):
        orchestrator_v4._path(tmp_path, "alias/authority.py")
    with pytest.raises(activation_v4.ActivationError, match="symlink"):
        activation_v4._file(tmp_path, "alias/authority.py")


def test_activation_scope_is_explicit_and_complete() -> None:
    assert len(activation_v4.FROZEN_SCOPE) == len(set(activation_v4.FROZEN_SCOPE))
    missing = [
        relative for relative in activation_v4.FROZEN_SCOPE if not (ROOT / relative).is_file()
    ]
    assert missing == []
