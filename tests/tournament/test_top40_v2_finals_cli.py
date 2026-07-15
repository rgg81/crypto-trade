from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from crypto_trade.tournament import runner_v2
from crypto_trade.tournament.finals_v2 import (
    BoundFinalistPerformance,
    FinalistSourceBinding,
)
from crypto_trade.tournament.layout import TOP40_V2_LAYOUT
from crypto_trade.tournament.scoring_v2 import (
    FinalistPerformance,
    RoleStabilityObservations,
    WindowPerformance,
)
from crypto_trade.tournament.top40_v2 import (
    TEAM_IDS,
    EvaluationWindow,
    LoadedV2Config,
    WindowMetrics,
    load_config,
)

REPOSITORY = Path(__file__).parents[2]
CONFIG = TOP40_V2_LAYOUT.config_path
FINALISTS = TEAM_IDS[:2]


def _load_cli_module() -> Any:
    path = REPOSITORY / "scripts/top40_v2_tournament.py"
    spec = importlib.util.spec_from_file_location("top40_v2_finals_cli_for_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def cli() -> Any:
    return _load_cli_module()


def _args(**values: object) -> SimpleNamespace:
    defaults: dict[str, object] = {"config": CONFIG, "json_out": None}
    defaults.update(values)
    return SimpleNamespace(**defaults)


def _json_bytes(payload: object) -> bytes:
    return (
        json.dumps(payload, allow_nan=False, indent=2, sort_keys=True).encode("utf-8")
        + b"\n"
    )


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(payload))


def _read_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    return raw


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _candidate(team_id: str) -> dict[str, str]:
    strategy_sha256 = (team_id[-2:] * 32)[:64]
    return {
        "candidate_id": f"candidate-{team_id}",
        "strategy_sha256": strategy_sha256,
        "risk_policy_sha256": "b" * 64,
        "source_bundle_sha256": "c" * 64,
    }


def _base_state(root: Path) -> dict[str, Any]:
    cohort_path = root / TOP40_V2_LAYOUT.finalist_cohort_lock_path
    _write_json(
        cohort_path,
        {
            "schema_version": 1,
            "tournament": TOP40_V2_LAYOUT.name,
            "finalist_team_ids": list(FINALISTS),
        },
    )
    teams: dict[str, dict[str, Any]] = {}
    for team_id in TEAM_IDS:
        finalist = team_id in FINALISTS
        candidate = _candidate(team_id) if finalist else None
        teams[team_id] = {
            "team_id": team_id,
            "status": "finalist_frozen" if finalist else "dnf",
            "qualifier_candidate": candidate,
            "private_result": {"status": "passed"} if finalist else None,
            "finalist_freeze": dict(candidate) if candidate is not None else None,
            "canonical_result": None,
            "dnf": None
            if finalist
            else {"reason_code": "not-qualified", "stage": "qualification"},
        }
    return {
        "schema_version": 1,
        "phase": "finalist_cohort_frozen",
        "teams": teams,
        "finalist_cohort_lock": {
            "path": TOP40_V2_LAYOUT.finalist_cohort_lock_path,
            "sha256": _sha256(cohort_path),
            "finalist_team_ids": list(FINALISTS),
        },
    }


def _bound_finalist(
    config: LoadedV2Config,
    state: dict[str, Any],
    team_id: str,
    *,
    final_sharpe: float,
) -> BoundFinalistPerformance:
    candidate = state["teams"][team_id]["qualifier_candidate"]
    final_record_sha256 = state["teams"][team_id]["canonical_result"][
        "runner_record_sha256"
    ]
    binding = FinalistSourceBinding(
        team_id=team_id,
        candidate_id=candidate["candidate_id"],
        config_sha256=config.sha256,
        strategy_sha256=candidate["strategy_sha256"],
        risk_policy_sha256=candidate["risk_policy_sha256"],
        source_bundle_sha256=candidate["source_bundle_sha256"],
        data_manifest_sha256="d" * 64,
        development_evidence_sha256="e" * 64,
        private_sealed_record_sha256="f" * 64,
        private_runner_record_sha256="1" * 64,
        final_oos_runner_record_sha256=final_record_sha256,
    )
    performance = FinalistPerformance(
        team_id=team_id,
        development=WindowPerformance(1.1, 0.18, 0.9, 0.2, 0.75),
        private=WindowPerformance(0.85, 0.12, 0.6, 0.2, 0.75),
        final_oos=WindowPerformance(final_sharpe, 0.2, 1.0, 0.2, 0.75),
        double_cost_oos_sharpe=0.7,
        regime_sharpes=(
            ("bull", 1.1),
            ("bear", 0.7),
            ("chop", 0.5),
            ("stress", 0.2),
        ),
        role_stability=RoleStabilityObservations(0.12, 0.08, 0.08, 0.8, 1.0),
    )
    return BoundFinalistPerformance(binding, performance)


@pytest.fixture
def harness(tmp_path: Path, cli: Any, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    root = tmp_path / "repository"
    contract = root / TOP40_V2_LAYOUT.tournament_root
    contract.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(REPOSITORY / TOP40_V2_LAYOUT.tournament_root, contract)
    state_path = root / TOP40_V2_LAYOUT.state_path
    _write_json(state_path, _base_state(root))
    config = load_config(root / CONFIG)
    locked_finalists: list[BoundFinalistPerformance] | None = None

    def read_state(unused_root: Path, unused_config: LoadedV2Config) -> dict[str, Any]:
        assert unused_root == root
        assert unused_config.sha256 == config.sha256
        return _read_json(state_path)

    def objective_inputs(
        unused_root: Path,
        current_config: LoadedV2Config,
        state: dict[str, Any],
    ) -> tuple[list[BoundFinalistPerformance], list[str], list[str]]:
        nonlocal locked_finalists
        assert unused_root == root
        if locked_finalists is None:
            locked_finalists = [
                _bound_finalist(
                    current_config,
                    state,
                    team_id,
                    final_sharpe=1.2 - index * 0.2,
                )
                for index, team_id in enumerate(FINALISTS)
            ]
        return list(locked_finalists), list(FINALISTS), list(TEAM_IDS[len(FINALISTS) :])

    monkeypatch.chdir(root)
    monkeypatch.setattr(cli, "read_run_state", read_state)
    monkeypatch.setattr(cli, "validate_run_state", lambda state, config: None)
    monkeypatch.setattr(cli, "_verify_qualified_candidate", lambda root, team, raw: None)
    monkeypatch.setattr(cli, "_objective_inputs", objective_inputs)
    monkeypatch.setattr(cli, "_emit", lambda payload, json_out=None: None)
    return SimpleNamespace(root=root, state_path=state_path, cli=cli, config=config)


def _install_mock_runner(
    harness: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    *,
    mismatch_team: str | None = None,
) -> list[tuple[str, str]]:
    calls: list[tuple[str, str]] = []
    replay_counts: dict[str, int] = {}

    def fake_run_team(
        root: Path,
        team_id: str,
        entrypoint: str,
        config_path: str,
        snapshot_manifest: str,
        *,
        stage: str,
        _authorization: object,
        _output_relative: str,
    ) -> runner_v2.TeamWindowRunResult:
        assert root == harness.root
        assert config_path == CONFIG
        assert snapshot_manifest == str(
            harness.config.raw["paths"]["shared_snapshot_manifest"]
        )
        assert _authorization is runner_v2._ORGANIZER_RUN_AUTHORIZATION
        assert stage == "final_oos"
        replay_counts[team_id] = replay_counts.get(team_id, 0) + 1
        replay = replay_counts[team_id]
        calls.append((team_id, _output_relative))
        artifact = root / _output_relative / "returns.csv"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(f"timestamp,return\n{team_id},0.01\n", encoding="utf-8")
        artifact_sha256 = hashlib.sha256(artifact.read_bytes()).hexdigest()
        net_sharpe = 1.2 if team_id == FINALISTS[0] else 1.0
        if mismatch_team == team_id and replay == 2:
            net_sharpe -= 0.25
        candidate = _candidate(team_id)
        return runner_v2.TeamWindowRunResult(
            stage=stage,
            team_id=team_id,
            entrypoint=entrypoint,
            seed=int(harness.config.raw["research_budget"]["strategy_seed"]),
            data_manifest_sha256="d" * 64,
            config_sha256=harness.config.sha256,
            strategy_sha256=candidate["strategy_sha256"],
            risk_policy_sha256=candidate["risk_policy_sha256"],
            source_bundle_sha256=candidate["source_bundle_sha256"],
            output_dir=_output_relative,
            artifacts={"returns": artifact.relative_to(root).as_posix()},
            artifact_sha256={"returns": artifact_sha256},
            artifact_sizes={"returns": artifact.stat().st_size},
            scored_window=EvaluationWindow(
                start=str(harness.config.raw["splits"]["final_oos_start"]),
                end=str(harness.config.raw["splits"]["final_oos_end_inclusive"]),
                metrics=WindowMetrics(
                    net_sharpe=net_sharpe,
                    net_sortino=1.4,
                    calmar=1.0,
                    annualized_return=0.2,
                    max_drawdown=0.2,
                    positive_quarter_fraction=0.75,
                ),
            ),
            double_cost_sharpe=0.7,
            regime_sharpe={"bull": 1.1, "bear": 0.7, "chop": 0.5, "stress": 0.2},
            net_sharpe_confidence_interval=(0.5, 1.5),
            double_cost_sharpe_confidence_interval=(0.1, 1.0),
            decision_count=100,
            event_count=20,
            trade_count=10,
        )

    monkeypatch.setattr(runner_v2, "run_team", fake_run_team)
    return calls


def _advance_to_objective(
    harness: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> list[tuple[str, str]]:
    calls = _install_mock_runner(harness, monkeypatch)
    for team_id in FINALISTS:
        assert harness.cli._run_finalist(_args(team_id=team_id)) == 0
    assert harness.cli._lock_final_oos(_args()) == 0
    assert harness.cli._lock_objective(_args()) == 0
    return calls


def _critic_ballot(
    config: LoadedV2Config,
    *,
    findings: dict[str, list[dict[str, str]]] | None = None,
) -> dict[str, object]:
    categories = tuple(config.raw["critic"]["category_order"])
    return {
        "schema_version": 1,
        "scores": {
            team_id: {
                category: 2.0 if team_id == FINALISTS[0] else 1.0
                for category in categories
            }
            for team_id in FINALISTS
        },
        "reviews": {team_id: f"Synthetic review for {team_id}." for team_id in FINALISTS},
        "dq_findings": findings or {},
    }


def _confirmation(confirmations: dict[str, list[str]]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "authority": "synthetic organizer",
        "confirmations": confirmations,
        "notes": "Synthetic confirmation decision.",
    }


def _user_ballot() -> dict[str, object]:
    return {
        "schema_version": 1,
        "scores": {FINALISTS[0]: 12.0, FINALISTS[1]: 8.0},
        "rationales": {
            team_id: f"Synthetic rationale for {team_id}." for team_id in FINALISTS
        },
    }


def test_final_reservation_is_first_add_and_cannot_be_repeated(
    harness: SimpleNamespace,
) -> None:
    candidate_id, reservation_sha256 = harness.cli._reserve_finalist_run(
        harness.root, harness.config, FINALISTS[0]
    )

    state = _read_json(harness.state_path)
    reservation = (
        harness.root
        / "tournament/top40-v2/private/final-oos-reservations/team-01.json"
    )
    assert candidate_id == f"candidate-{FINALISTS[0]}"
    assert reservation_sha256 == _sha256(reservation)
    assert state["teams"][FINALISTS[0]]["status"] == "canonical_running"
    with pytest.raises(ValueError, match="unused finalist freeze"):
        harness.cli._reserve_finalist_run(harness.root, harness.config, FINALISTS[0])
    assert _sha256(reservation) == reservation_sha256


def test_finalist_command_requires_two_matching_mocked_replays(
    harness: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _install_mock_runner(harness, monkeypatch)

    assert harness.cli._run_finalist(_args(team_id=FINALISTS[0])) == 0

    assert calls == [
        (FINALISTS[0], f"tournament/top40-v2/private/final-replays/{FINALISTS[0]}/replay-1"),
        (FINALISTS[0], f"tournament/top40-v2/private/final-replays/{FINALISTS[0]}/replay-2"),
    ]
    state = _read_json(harness.state_path)
    result = state["teams"][FINALISTS[0]]["canonical_result"]
    assert state["teams"][FINALISTS[0]]["status"] == "canonical_complete"
    assert result["replay_outputs_match"] is True
    assert len(result["internal_replays"]) == 2
    assert result["internal_replays"][0]["artifact_sha256"] == result[
        "internal_replays"
    ][1]["artifact_sha256"]
    assert result["runner_record_sha256"] == _sha256(
        harness.root / result["runner_record_path"]
    )


def test_mismatched_final_replays_fail_closed_and_consume_reservation(
    harness: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _install_mock_runner(harness, monkeypatch, mismatch_team=FINALISTS[0])

    with pytest.raises(ValueError, match="replay records or artifacts differ"):
        harness.cli._run_finalist(_args(team_id=FINALISTS[0]))

    assert len(calls) == 2
    state = _read_json(harness.state_path)
    assert state["teams"][FINALISTS[0]]["status"] == "canonical_failed"
    assert state["teams"][FINALISTS[0]]["canonical_result"]["status"] == "failed"
    with pytest.raises(ValueError, match="unused finalist freeze"):
        harness.cli._run_finalist(_args(team_id=FINALISTS[0]))


def test_complete_finals_chain_binds_every_exact_predecessor_lock(
    harness: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _advance_to_objective(harness, monkeypatch)
    assert len(calls) == 2 * len(FINALISTS)

    critic_input = harness.root / "critic-ballot.json"
    _write_json(critic_input, _critic_ballot(harness.config))
    assert harness.cli._lock_critic(_args(ballot=str(critic_input))) == 0

    confirmation_input = harness.root / "critic-confirmation.json"
    _write_json(confirmation_input, _confirmation({}))
    assert harness.cli._lock_critic_confirmations(
        _args(confirmation=str(confirmation_input))
    ) == 0

    user_input = harness.root / "user-ballot.json"
    _write_json(user_input, _user_ballot())
    assert harness.cli._lock_user_ballot(_args(ballot=str(user_input))) == 0
    assert harness.cli._lock_selection(_args()) == 0
    assert harness.cli._freeze_winner(_args()) == 0
    assert harness.cli._verify_winner_freeze(_args()) == 0

    paths = {
        "cohort": TOP40_V2_LAYOUT.finalist_cohort_lock_path,
        "final_oos": harness.cli.FINAL_OOS_LOCK_PATH,
        "objective": harness.cli.OBJECTIVE_LOCK_PATH,
        "critic": harness.cli.CRITIC_LOCK_PATH,
        "confirmation": harness.cli.CRITIC_CONFIRMATION_LOCK_PATH,
        "user": harness.cli.USER_BALLOT_LOCK_PATH,
        "selection": harness.cli.SELECTION_LOCK_PATH,
        "winner": harness.cli.WINNER_FREEZE_PATH,
    }
    digests = {name: _sha256(harness.root / path) for name, path in paths.items()}
    final_oos = _read_json(harness.root / paths["final_oos"])
    objective = _read_json(harness.root / paths["objective"])
    critic = _read_json(harness.root / paths["critic"])
    confirmation = _read_json(harness.root / paths["confirmation"])
    user = _read_json(harness.root / paths["user"])
    selection = _read_json(harness.root / paths["selection"])
    winner = _read_json(harness.root / paths["winner"])

    assert final_oos["cohort_lock_sha256"] == digests["cohort"]
    assert objective["cohort_lock_sha256"] == digests["cohort"]
    assert objective["final_oos_lock_sha256"] == digests["final_oos"]
    assert critic["objective_lock_sha256"] == digests["objective"]
    assert confirmation["critic_lock_sha256"] == digests["critic"]
    assert user["critic_confirmation_lock_sha256"] == digests["confirmation"]
    assert selection["objective_lock_sha256"] == digests["objective"]
    assert selection["critic_lock_sha256"] == digests["critic"]
    assert selection["critic_confirmation_lock_sha256"] == digests["confirmation"]
    assert selection["user_ballot_lock_sha256"] == digests["user"]
    assert winner["selection_lock_sha256"] == digests["selection"]

    state = _read_json(harness.state_path)
    assert state["phase"] == "paper_frozen"
    assert state["selection_lock"]["winner_team_id"] == FINALISTS[0]
    for state_key, path_key in (
        ("final_oos_lock", "final_oos"),
        ("objective_lock", "objective"),
        ("critic_lock", "critic"),
        ("critic_confirmation_lock", "confirmation"),
        ("user_ballot_lock", "user"),
        ("selection_lock", "selection"),
        ("winner_freeze", "winner"),
    ):
        assert state[state_key]["path"] == paths[path_key]
        assert state[state_key]["sha256"] == digests[path_key]


def test_all_confirmed_dqs_stop_before_user_and_selection_phases(
    harness: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    _advance_to_objective(harness, monkeypatch)
    findings: dict[str, list[dict[str, str]]] = {}
    for team_id in FINALISTS:
        evidence = harness.root / f"critic-evidence-{team_id}.txt"
        evidence.write_text(f"Evidence for {team_id}.\n", encoding="utf-8")
        findings[team_id] = [
            {
                "code": "reproducibility-failure",
                "evidence_path": evidence.relative_to(harness.root).as_posix(),
                "evidence_sha256": _sha256(evidence),
            }
        ]
    critic_input = harness.root / "critic-all-dq.json"
    _write_json(critic_input, _critic_ballot(harness.config, findings=findings))
    assert harness.cli._lock_critic(_args(ballot=str(critic_input))) == 0

    confirmation_input = harness.root / "confirm-all-dq.json"
    _write_json(
        confirmation_input,
        _confirmation(
            {team_id: ["reproducibility-failure"] for team_id in FINALISTS}
        ),
    )
    assert harness.cli._lock_critic_confirmations(
        _args(confirmation=str(confirmation_input))
    ) == 0

    state = _read_json(harness.state_path)
    assert state["phase"] == "integrity_review_required"
    user_input = harness.root / "user-after-all-dq.json"
    _write_json(user_input, _user_ballot())
    with pytest.raises(ValueError, match="requires run phase dq_confirmed"):
        harness.cli._lock_user_ballot(_args(ballot=str(user_input)))
    assert not (harness.root / harness.cli.USER_BALLOT_LOCK_PATH).exists()
    assert not (harness.root / harness.cli.SELECTION_LOCK_PATH).exists()


def test_incomplete_critic_and_user_ballots_fail_closed(
    harness: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    _advance_to_objective(harness, monkeypatch)
    incomplete_critic = _critic_ballot(harness.config)
    incomplete_critic["scores"].pop(FINALISTS[1])  # type: ignore[union-attr]
    critic_input = harness.root / "critic-incomplete.json"
    _write_json(critic_input, incomplete_critic)
    with pytest.raises(ValueError, match="score every finalist exactly"):
        harness.cli._lock_critic(_args(ballot=str(critic_input)))
    assert _read_json(harness.state_path)["phase"] == "objective_locked"
    assert not (harness.root / harness.cli.CRITIC_LOCK_PATH).exists()

    valid_critic = harness.root / "critic-complete.json"
    _write_json(valid_critic, _critic_ballot(harness.config))
    assert harness.cli._lock_critic(_args(ballot=str(valid_critic))) == 0
    confirmation_input = harness.root / "confirm-no-dq.json"
    _write_json(confirmation_input, _confirmation({}))
    assert harness.cli._lock_critic_confirmations(
        _args(confirmation=str(confirmation_input))
    ) == 0

    incomplete_user = _user_ballot()
    incomplete_user["rationales"].pop(FINALISTS[1])  # type: ignore[union-attr]
    user_input = harness.root / "user-incomplete.json"
    _write_json(user_input, incomplete_user)
    with pytest.raises(ValueError, match="explain every original finalist exactly"):
        harness.cli._lock_user_ballot(_args(ballot=str(user_input)))
    assert _read_json(harness.state_path)["phase"] == "dq_confirmed"
    assert not (harness.root / harness.cli.USER_BALLOT_LOCK_PATH).exists()


def test_tampered_lock_bytes_and_state_bindings_are_rejected(
    harness: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    _advance_to_objective(harness, monkeypatch)
    critic_input = harness.root / "critic-after-tamper.json"
    _write_json(critic_input, _critic_ballot(harness.config))
    objective_path = harness.root / harness.cli.OBJECTIVE_LOCK_PATH
    original = objective_path.read_bytes()

    objective_path.write_bytes(original + b" ")
    with pytest.raises(ValueError, match="bytes differ from the run-state binding"):
        harness.cli._lock_critic(_args(ballot=str(critic_input)))

    objective_path.write_bytes(original)
    state = _read_json(harness.state_path)
    state["objective_lock"]["sha256"] = "0" * 64
    _write_json(harness.state_path, state)
    with pytest.raises(ValueError, match="bytes differ from the run-state binding"):
        harness.cli._lock_critic(_args(ballot=str(critic_input)))
    assert not (harness.root / harness.cli.CRITIC_LOCK_PATH).exists()
