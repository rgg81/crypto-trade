from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from crypto_trade.tournament.layout import TOP40_V2_LAYOUT
from crypto_trade.tournament.top40_v2 import TEAM_IDS, load_config, validate_run_state

REPOSITORY = Path(__file__).parents[2]
CONFIG = TOP40_V2_LAYOUT.config_path


def _load_cli_module():
    path = REPOSITORY / "scripts/top40_v2_tournament.py"
    spec = importlib.util.spec_from_file_location("top40_v2_cli_for_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def cli():
    return _load_cli_module()


def _args(**values):
    defaults = {"config": CONFIG, "json_out": None}
    defaults.update(values)
    return SimpleNamespace(**defaults)


def _copy_contract(root: Path) -> None:
    destination = root / TOP40_V2_LAYOUT.tournament_root
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(REPOSITORY / TOP40_V2_LAYOUT.tournament_root, destination)


def _initialize(cli, root: Path, monkeypatch) -> None:
    _copy_contract(root)
    monkeypatch.chdir(root)
    assert cli._init_teams(_args(force=False)) == 0


def _read_state(root: Path) -> dict:
    return json.loads((root / TOP40_V2_LAYOUT.state_path).read_text(encoding="utf-8"))


def _open_research(root: Path) -> None:
    state = _read_state(root)
    state["phase"] = "research"
    for team in state["teams"].values():
        team["status"] = "researching"
    (root / TOP40_V2_LAYOUT.state_path).write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _family(team_id: str, family_id: str, parent: str | None) -> dict:
    return {
        "schema_version": 1,
        "team_id": team_id,
        "family_id": family_id,
        "parent_family_id": parent,
        "registered_at_utc": "2026-07-16T10:00:00Z",
        "mechanism": f"mechanism {family_id}",
        "economic_thesis": "a falsifiable economic thesis",
        "expected_regime_roles": {
            "bull": "long sleeve earns",
            "bear": "short sleeve earns",
            "chop": "cross-sectional spread earns",
            "stress": "risk is reduced",
            "long_sleeve": "owns positive residuals",
            "short_sleeve": "shorts negative residuals",
        },
        "falsifier": "stitched OOF Sharpe is non-positive",
        "parameter_ranges": {"lookback": [10, 20, 30]},
        "selection_metric": "stitched OOF net Sharpe",
        "risk_policy_plan": "ablate the drawdown brake",
    }


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _candidate_bindings(root: Path, config, team_id: str) -> tuple[str, str]:
    strategy = root / TOP40_V2_LAYOUT.team_root(team_id) / "strategy.py"
    strategy.write_text("def decide(context):\n    return {}\n", encoding="utf-8")
    risk = root / TOP40_V2_LAYOUT.team_root(team_id) / "risk_policy.json"
    return (
        hashlib.sha256(strategy.read_bytes()).hexdigest(),
        hashlib.sha256(risk.read_bytes()).hexdigest(),
    )


def _development_evidence(
    root: Path,
    config,
    *,
    team_id: str = "team-01",
    candidate_id: str = "candidate-1",
    trial_count: int = 1,
    passing: bool = True,
) -> dict:
    strategy_sha, risk_sha = _candidate_bindings(root, config, team_id)
    return {
        "schema_version": 1,
        "stage": "development",
        "team_id": team_id,
        "candidate_id": candidate_id,
        "strategy_sha256": strategy_sha,
        "risk_policy_sha256": risk_sha,
        "config_sha256": config.sha256,
        "trial_count": trial_count,
        "aggregate": {
            "net_sharpe": 0.8 if passing else -0.1,
            "annualized_return": 0.1,
            "calmar": 0.5,
            "max_drawdown": 0.2,
            "double_cost_sharpe": 0.4,
            "positive_quarter_fraction": 0.6,
            "trial_adjusted_probability_positive": 0.95,
        },
        "folds": [
            {"fold_id": f"fold-{index}", "net_return": 0.01 if index < 6 else -0.01}
            for index in range(1, 7)
        ],
        "regimes": {
            "bull": {"net_return": 0.1, "net_sharpe": 0.8},
            "bear": {"net_return": 0.05, "net_sharpe": 0.4},
            "chop": {"net_return": 0.03, "net_sharpe": 0.3},
            "stress": {"net_return": -0.01, "net_sharpe": -0.1},
        },
        "roles": {
            "long_bull_net_return": 0.06,
            "short_bear_net_return": 0.04,
            "combined_chop_net_return": 0.03,
        },
        "sleeves": {
            side: {
                "active_bar_fraction": 0.2,
                "mean_gross_exposure": 0.05,
                "executed_notional_usdt": 50_000,
            }
            for side in ("long", "short")
        },
        "stability": {
            "profitable_neighbor_fraction": 0.8,
            "neighbor_median_sharpe": 0.6,
            "maximum_positive_pnl_concentration": 0.3,
        },
    }


def _private_evidence(root: Path, config, development: dict, *, passing: bool = True) -> dict:
    return {
        key: development[key]
        for key in (
            "schema_version",
            "team_id",
            "candidate_id",
            "strategy_sha256",
            "risk_policy_sha256",
            "config_sha256",
            "trial_count",
        )
    } | {
        "stage": "private",
        "aggregate": {
            "net_sharpe": 0.6 if passing else -0.2,
            "annualized_return": 0.05,
            "max_drawdown": 0.2,
            "double_cost_sharpe": 0.1,
            "positive_quarter_fraction": 0.75,
        },
    }


def _register_initial_family(cli, root: Path) -> None:
    registration = root / "family-1.json"
    _write_json(registration, _family("team-01", "family-1", None))
    assert (
        cli._register_family(
            _args(team_id="team-01", registration=str(registration)), pivot=False
        )
        == 0
    )


def _qualify_team_one(cli, root: Path) -> None:
    _register_initial_family(cli, root)
    config = load_config(root / CONFIG)
    development = _development_evidence(root, config, trial_count=2)
    development_path = root / "development.json"
    _write_json(development_path, development)
    assert (
        cli._record_development_assessment(
            _args(team_id="team-01", evidence=str(development_path))
        )
        == 0
    )
    private = _private_evidence(root, config, development)
    private_path = root / "private.json"
    _write_json(private_path, private)
    assert (
        cli._record_private_assessment(_args(team_id="team-01", evidence=str(private_path)))
        == 0
    )


def test_init_teams_is_v2_only_and_creates_valid_pending_state(cli, tmp_path, monkeypatch):
    sentinel = tmp_path / "tournament/top40/do-not-touch.txt"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text("v1", encoding="utf-8")
    _initialize(cli, tmp_path, monkeypatch)

    config = load_config(tmp_path / CONFIG)
    state = _read_state(tmp_path)
    validate_run_state(state, config)
    assert state["phase"] == "phase0_pending"
    assert len(state["teams"]) == 10
    assert sentinel.read_text(encoding="utf-8") == "v1"
    assert (tmp_path / "reports-top40-v2/team-10").is_dir()


def test_family_registration_and_two_pivots_preserve_cumulative_budget(
    cli, tmp_path, monkeypatch
):
    _initialize(cli, tmp_path, monkeypatch)
    _open_research(tmp_path)

    parent = None
    for index in range(1, 4):
        family_id = f"family-{index}"
        registration = tmp_path / f"family-{index}.json"
        _write_json(registration, _family("team-01", family_id, parent))
        command = cli._register_family
        assert command(
            _args(team_id="team-01", registration=str(registration)), pivot=index > 1
        ) == 0
        parent = family_id

    fourth = tmp_path / "family-4.json"
    _write_json(fourth, _family("team-01", "family-4", "family-3"))
    with pytest.raises(ValueError, match="exhausted.*pivot"):
        cli._register_family(
            _args(team_id="team-01", registration=str(fourth)), pivot=True
        )
    team = _read_state(tmp_path)["teams"]["team-01"]
    assert (team["family_count"], team["pivot_count"], team["trial_count"]) == (3, 2, 0)


def test_failed_development_is_research_not_submission_then_passing_candidate_freezes(
    cli, tmp_path, monkeypatch
):
    _initialize(cli, tmp_path, monkeypatch)
    _open_research(tmp_path)
    _register_initial_family(cli, tmp_path)
    config = load_config(tmp_path / CONFIG)
    failed = _development_evidence(tmp_path, config, trial_count=1, passing=False)
    failed_path = tmp_path / "failed.json"
    _write_json(failed_path, failed)
    assert (
        cli._record_development_assessment(
            _args(team_id="team-01", evidence=str(failed_path))
        )
        == 1
    )
    assert _read_state(tmp_path)["teams"]["team-01"]["status"] == "researching"

    passed = _development_evidence(tmp_path, config, trial_count=2)
    passed_path = tmp_path / "passed.json"
    _write_json(passed_path, passed)
    assert (
        cli._record_development_assessment(
            _args(team_id="team-01", evidence=str(passed_path))
        )
        == 0
    )
    team = _read_state(tmp_path)["teams"]["team-01"]
    assert team["status"] == "qualifier_candidate_frozen"
    assert team["trial_count"] == 2
    assert team["qualifier_candidate"]["candidate_id"] == "candidate-1"


def test_development_assessment_requires_a_preregistered_family(cli, tmp_path, monkeypatch):
    _initialize(cli, tmp_path, monkeypatch)
    _open_research(tmp_path)
    config = load_config(tmp_path / CONFIG)
    evidence = _development_evidence(tmp_path, config)
    path = tmp_path / "development.json"
    _write_json(path, evidence)

    with pytest.raises(ValueError, match="preregistered mechanism family"):
        cli._record_development_assessment(
            _args(team_id="team-01", evidence=str(path))
        )


def test_private_ticket_is_single_shot_and_public_state_contains_no_observations(
    cli, tmp_path, monkeypatch
):
    _initialize(cli, tmp_path, monkeypatch)
    _open_research(tmp_path)
    _register_initial_family(cli, tmp_path)
    config = load_config(tmp_path / CONFIG)
    development = _development_evidence(tmp_path, config, trial_count=2)
    development_path = tmp_path / "development.json"
    _write_json(development_path, development)
    cli._record_development_assessment(
        _args(team_id="team-01", evidence=str(development_path))
    )
    private = _private_evidence(tmp_path, config, development)
    private_path = tmp_path / "private.json"
    _write_json(private_path, private)
    assert (
        cli._record_private_assessment(_args(team_id="team-01", evidence=str(private_path)))
        == 0
    )

    team = _read_state(tmp_path)["teams"]["team-01"]
    assert team["status"] == "qualified"
    assert team["private_attempts"] == 1
    assert "observed" not in json.dumps(team["private_result"])
    sealed = json.loads(
        (tmp_path / "tournament/top40-v2/private/team-01.json").read_text(encoding="utf-8")
    )
    assert sealed["assessment"]["gates"][0]["observed"] == 0.6
    with pytest.raises(ValueError, match="private assessment requires|already consumed"):
        cli._record_private_assessment(
            _args(team_id="team-01", evidence=str(private_path))
        )


def test_private_assessment_cli_hides_numeric_feedback_by_default(
    cli, tmp_path, monkeypatch
):
    _initialize(cli, tmp_path, monkeypatch)
    config = load_config(tmp_path / CONFIG)
    development = _development_evidence(tmp_path, config)
    private = _private_evidence(tmp_path, config, development)
    private_path = tmp_path / "private.json"
    output = tmp_path / "feedback.json"
    _write_json(private_path, private)

    assert cli._assess_qualification(
        _args(
            stage="private",
            evidence=str(private_path),
            include_private_observations=False,
            json_out=str(output),
        )
    ) == 0
    feedback = json.loads(output.read_text(encoding="utf-8"))
    assert feedback["feedback_mode"] == "pass-fail-only"
    assert feedback["passed"] is True
    assert all("observed" not in gate for gate in feedback["gates"])


def test_close_and_finalist_lock_advance_only_qualified_teams(cli, tmp_path, monkeypatch):
    _initialize(cli, tmp_path, monkeypatch)
    _open_research(tmp_path)
    _qualify_team_one(cli, tmp_path)

    assert cli._close_qualification(_args()) == 0
    closed = _read_state(tmp_path)
    assert closed["phase"] == "qualification_closed"
    assert closed["teams"]["team-01"]["status"] == "qualified"
    assert all(closed["teams"][team]["status"] == "dnf" for team in TEAM_IDS[1:])

    assert cli._lock_finalist_cohort(_args()) == 0
    frozen = _read_state(tmp_path)
    assert frozen["phase"] == "finalist_cohort_frozen"
    assert frozen["teams"]["team-01"]["status"] == "finalist_frozen"
    cohort = json.loads(
        (tmp_path / TOP40_V2_LAYOUT.finalist_cohort_lock_path).read_text(encoding="utf-8")
    )
    assert cohort["finalist_team_ids"] == ["team-01"]
    assert "observed" not in json.dumps(cohort)


def test_zero_qualifiers_produces_no_qualified_model(cli, tmp_path, monkeypatch):
    _initialize(cli, tmp_path, monkeypatch)
    _open_research(tmp_path)
    cli._withdraw_team(_args(team_id="team-01", reason="mechanism falsified"))
    cli._close_qualification(_args())
    cli._lock_finalist_cohort(_args())

    state = _read_state(tmp_path)
    assert state["phase"] == "no_qualified_model"
    assert all(state["teams"][team]["status"] == "dnf" for team in TEAM_IDS)


def test_freeze_phase0_binds_committed_inputs_and_opens_research(
    cli, tmp_path, monkeypatch
):
    from crypto_trade.tournament import snapshot

    _initialize(cli, tmp_path, monkeypatch)
    minimal_frozen = (CONFIG, TOP40_V2_LAYOUT.orchestrator_script)
    monkeypatch.setattr(cli, "PHASE0_FROZEN_FILES", minimal_frozen)
    script_target = tmp_path / TOP40_V2_LAYOUT.orchestrator_script
    script_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPOSITORY / TOP40_V2_LAYOUT.orchestrator_script, script_target)
    manifest = tmp_path / "tournament/top40/data_manifest.json"
    _write_json(manifest, {"schema_version": 1, "files": []})
    monkeypatch.setattr(snapshot, "verify_snapshot_manifest", lambda path: {"verified": path})
    subprocess.run(
        ["git", "init", "-q", "-b", TOP40_V2_LAYOUT.branch], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "V2 Test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "common V2 inputs"], cwd=tmp_path, check=True)

    assert cli._freeze_phase0(_args()) == 0
    freeze = json.loads(
        (tmp_path / TOP40_V2_LAYOUT.phase0_freeze_path).read_text(encoding="utf-8")
    )
    assert set(freeze) == {
        "schema_version",
        "frozen_at_utc",
        "branch",
        "common_freeze_commit",
        "config_sha256",
        "shared_snapshot_manifest_path",
        "shared_snapshot_manifest_sha256",
        "frozen_files",
    }
    assert freeze["schema_version"] == 2
    assert set(freeze["frozen_files"]) == set(minimal_frozen)
    state = _read_state(tmp_path)
    assert state["phase"] == "research"
    assert all(state["teams"][team]["status"] == "researching" for team in TEAM_IDS)


def test_risk_policy_validator_reports_explicit_policy_state(cli, tmp_path, monkeypatch):
    _initialize(cli, tmp_path, monkeypatch)
    policy_path = tmp_path / TOP40_V2_LAYOUT.team_root("team-01") / "risk_policy.json"
    output = tmp_path / "risk-result.json"
    assert cli._validate_risk_policy(
        SimpleNamespace(policy=str(policy_path), json_out=str(output))
    ) == 0
    assert json.loads(output.read_text(encoding="utf-8")) == {
        "enabled": False,
        "policy_id": "team-01-base",
        "schema_version": 1,
        "valid": True,
    }


def test_config_hash_mismatch_is_rejected_before_assessment(cli, tmp_path, monkeypatch):
    _initialize(cli, tmp_path, monkeypatch)
    config = load_config(tmp_path / CONFIG)
    evidence = _development_evidence(tmp_path, config)
    changed = deepcopy(evidence)
    changed["config_sha256"] = "0" * 64
    path = tmp_path / "changed.json"
    _write_json(path, changed)
    with pytest.raises(ValueError, match="current V2 config"):
        cli._assess_qualification(
            _args(
                stage="development",
                evidence=str(path),
                include_private_observations=False,
            )
        )
