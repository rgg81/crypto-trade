from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import inspect
import json
import os
import stat
import subprocess
import sys
import time
import tomllib
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from crypto_trade.tournament import (
    activation_v4,
    isolation_v4,
    journal_v4,
    orchestrator_v4,
    pure_crypto_universe_v4_r2,
    research_runtime_v4,
    runner_v4,
    scoring_v4,
    top40_v4,
)
from crypto_trade.tournament.layout_v4 import TOP40_V4_R2_LAYOUT

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "tournament/top40-v4-r2/config.toml"


def _config() -> dict[str, object]:
    return tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _r2_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment["CRYPTO_TRADE_TOP40_V4_EDITION"] = "r2"
    environment["PYTHONPATH"] = "src"
    return environment


def _broker_module():
    path = ROOT / "scripts/top40_v4_r2_team_broker.py"
    spec = importlib.util.spec_from_file_location("top40_v4_r2_team_broker_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tournament_cli_module():
    path = ROOT / "scripts/top40_v4_r2_tournament.py"
    spec = importlib.util.spec_from_file_location("top40_v4_r2_tournament_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pretrial_recovery_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Path]:
    tournament = tmp_path / TOP40_V4_R2_LAYOUT.tournament_root
    for team_id in TOP40_V4_R2_LAYOUT.team_ids:
        team = tmp_path / TOP40_V4_R2_LAYOUT.team_root(team_id)
        for directory, filename, payload in (
            ("candidates", "README.md", b"seed\n"),
            ("feedback", ".keep", b""),
            ("outbox", ".keep", b""),
            ("work", ".keep", b""),
        ):
            path = team / directory
            path.mkdir(parents=True, exist_ok=True)
            (path / filename).write_bytes(payload)
    journal = tmp_path / TOP40_V4_R2_LAYOUT.journal_path
    journal.parent.mkdir(parents=True, exist_ok=True)
    journal.write_bytes(b"")
    old_record = "1" * 64
    old_activation = json.dumps({"record_sha256": old_record}, sort_keys=True).encode()
    old_tests = b"old activation tests passed\n"
    old_launch = b'{"launcher_version":"top40-v4-r2-research-runtime-v7"}\n'
    activation = tmp_path / TOP40_V4_R2_LAYOUT.activation_freeze_path
    activation.write_bytes(old_activation)
    tests = tournament / "activation-tests.out"
    tests.write_bytes(old_tests)
    launch = tmp_path / activation_v4._PRETRIAL_OLD_LAUNCH_PATH
    launch.parent.mkdir(parents=True, exist_ok=True)
    launch.write_bytes(old_launch)
    smoke = tmp_path / activation_v4._PRETRIAL_SMOKE_RECEIPT_PATH
    smoke.parent.mkdir(parents=True, exist_ok=True)
    smoke.write_bytes((ROOT / activation_v4._PRETRIAL_SMOKE_RECEIPT_PATH).read_bytes())
    monkeypatch.setattr(
        activation_v4,
        "_PRETRIAL_OLD_ACTIVATION_FILE_SHA256",
        hashlib.sha256(old_activation).hexdigest(),
    )
    monkeypatch.setattr(
        activation_v4, "_PRETRIAL_OLD_ACTIVATION_RECORD_SHA256", old_record
    )
    monkeypatch.setattr(
        activation_v4,
        "_PRETRIAL_OLD_TEST_OUTPUT_SHA256",
        hashlib.sha256(old_tests).hexdigest(),
    )
    monkeypatch.setattr(
        activation_v4,
        "_PRETRIAL_OLD_LAUNCH_SHA256",
        hashlib.sha256(old_launch).hexdigest(),
    )
    return {
        "activation": activation,
        "tests": tests,
        "launch": launch,
        "journal": journal,
    }


def _fresh_restart_fixture(tmp_path: Path) -> Path:
    tournament_prefix = f"{TOP40_V4_R2_LAYOUT.tournament_root}/"
    reports_prefix = f"{TOP40_V4_R2_LAYOUT.reports_root}/"
    for relative in activation_v4.FROZEN_SCOPE:
        if not relative.startswith((tournament_prefix, reports_prefix)):
            continue
        source = ROOT / relative
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
    journal = tmp_path / TOP40_V4_R2_LAYOUT.journal_path
    journal.parent.mkdir(parents=True, exist_ok=True)
    journal.write_bytes(b"")
    journal.chmod(0o600)
    return tmp_path


def _fresh_restart_scope_entries(root: Path) -> list[dict[str, object]]:
    relevant = {
        activation_v4._FRESH_RESTART_AUTHORITY_PATH,
        *(
            f"{TOP40_V4_R2_LAYOUT.team_root(team_id)}/{relative}"
            for team_id in TOP40_V4_R2_LAYOUT.team_ids
            for relative in (
                "ACCESS-POLICY.json",
                "TEAM-BRIEF.md",
                "candidates/README.md",
                "feedback/.keep",
                "outbox/.keep",
                "work/.keep",
            )
        ),
        *(
            relative
            for relative in activation_v4.FROZEN_SCOPE
            if relative.startswith(f"{TOP40_V4_R2_LAYOUT.reports_root}/")
        ),
    }
    return [
        {
            "path": relative,
            "size": (root / relative).stat().st_size,
            "sha256": hashlib.sha256((root / relative).read_bytes()).hexdigest(),
        }
        for relative in sorted(relevant)
    ]


def _patch_fresh_activation(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    test_results: list[tuple[bytes, int]],
) -> None:
    results = iter(test_results)
    scope_entries = _fresh_restart_scope_entries(root)
    monkeypatch.setattr(activation_v4, "_implementation_commit", lambda _root: "1" * 40)
    monkeypatch.setattr(
        activation_v4,
        "_validate_snapshot_window",
        lambda _root, _config: None,
    )
    monkeypatch.setattr(
        activation_v4,
        "_verify_full_snapshot_once",
        lambda _root, _config: "2" * 64,
    )
    monkeypatch.setattr(activation_v4, "_validate_adversarial_review", lambda _root: None)
    monkeypatch.setattr(
        activation_v4,
        "_scope",
        lambda _root, **_kwargs: (scope_entries, "3" * 64),
    )
    monkeypatch.setattr(activation_v4, "_audit_sha256", lambda _root, _config: "4" * 64)
    monkeypatch.setattr(activation_v4, "_run_tests", lambda _root: next(results))
    monkeypatch.setattr(
        research_runtime_v4,
        "validate_frozen_model_smoke",
        lambda _root: {"status": "passed"},
    )
    monkeypatch.setattr(
        activation_v4.top40_v4,
        "load_config",
        lambda **_kwargs: SimpleNamespace(raw={}, sha256="5" * 64),
    )


def test_r2_layout_has_fifteen_fresh_lanes_and_six_finalists() -> None:
    assert TOP40_V4_R2_LAYOUT.team_ids == tuple(
        f"team-{number:02d}" for number in range(1, 16)
    )
    assert TOP40_V4_R2_LAYOUT.advance_count == 6
    assert TOP40_V4_R2_LAYOUT.branch == "quant-portfolio-blind-top40-v4-r1-v2-restart7"
    assert TOP40_V4_R2_LAYOUT.tournament_root == "tournament/top40-v4-r2"
    assert TOP40_V4_R2_LAYOUT.reports_root == "reports-top40-v4-r2"


def test_r2_config_uses_open_lanes_and_july_inclusive_holdout() -> None:
    config = _config()
    assert config["teams"] == list(TOP40_V4_R2_LAYOUT.team_ids)
    assert set(config["mandates"].values()) == {"open-independent-mechanism"}
    assert config["selection"]["ranking"]["advance_count"] == 6
    assert config["selection"]["ranking"]["minimum_finalist_count"] == 5
    assert (
        config["selection"]["ranking"]["eligible_population"]
        == "one-successful-representative-per-team"
    )
    assert config["data"]["hard_end_exclusive"] == "2026-08-01T00:00:00Z"
    assert config["splits"]["historical_oos"] == {
        "start": "2024-07-01T00:00:00Z",
        "end_exclusive": "2026-08-01T00:00:00Z",
        "raw_data_visible_to_teams": False,
        "feedback": "one-atomic-simultaneous-release",
        "globally_pristine": False,
        "candidate_relative_oos": True,
    }
    assert config["splits"]["live_forward"]["start"] == "2026-09-01T00:00:00Z"
    assert config["historical_oos"]["winner_eligibility"]["minimum_positive_quarters"] == 5


def test_r2_cli_selects_edition_before_import_and_audits_all_surfaces() -> None:
    completed = subprocess.run(
        (
            sys.executable,
            "scripts/top40_v4_r2_tournament.py",
            "audit-isolation",
        ),
        cwd=ROOT,
        env=_r2_environment(),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["ok"] is True
    assert result["team_count"] == 15
    assert "checked_files" not in result


def test_r2_research_status_never_discloses_other_lane_progress(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    completed = subprocess.run(
        (sys.executable, "scripts/top40_v4_r2_tournament.py", "status"),
        cwd=ROOT,
        env=_r2_environment(),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["phase"] == "is-research"
    assert "teams" not in result
    assert result["research"] == {
        "interim_disclosure": False,
        "status": "lane state sealed until IS close",
    }
    assert result["journal_head_sha256"] == journal_v4.GENESIS_SHA256

    # Even a changed private research journal head must map to the same public status.
    private_state = SimpleNamespace(
        head_sha256="f" * 64,
        release=None,
        selection=None,
    )
    monkeypatch.setattr(journal_v4, "read", lambda _path: private_state)
    direct = orchestrator_v4.status.__wrapped__(ROOT)
    assert direct["journal_head_sha256"] == journal_v4.GENESIS_SHA256
    assert direct["research"] == result["research"]


def test_every_lane_starts_without_a_strategy_or_result() -> None:
    team_root = ROOT / TOP40_V4_R2_LAYOUT.tournament_root / "teams"
    for team_id in TOP40_V4_R2_LAYOUT.team_ids:
        files = sorted(
            path.relative_to(team_root / team_id).as_posix()
            for path in (team_root / team_id).rglob("*")
            if path.is_file()
        )
        assert files == [
            "ACCESS-POLICY.json",
            "TEAM-BRIEF.md",
            "candidates/README.md",
            "feedback/.keep",
            "outbox/.keep",
            "work/.keep",
        ]
        policy = json.loads((team_root / team_id / "ACCESS-POLICY.json").read_text())
        assert policy["team_id"] == team_id
        assert policy["default_access"] == "deny"
        serialized = json.dumps(policy)
        other_teams = (other for other in TOP40_V4_R2_LAYOUT.team_ids if other != team_id)
        assert not any(other in serialized for other in other_teams)


def test_r2_journal_enforces_fifteen_teams_and_six_finalists_in_fresh_process() -> None:
    script = """
from crypto_trade.tournament import journal_v4
from crypto_trade.tournament.layout_v4 import TOP40_V4_LAYOUT
state = journal_v4.replay_bytes(b'')
assert len(state.trials_by_team) == 15
assert TOP40_V4_LAYOUT.team_ids[-1] == 'team-15'
assert TOP40_V4_LAYOUT.advance_count == 6
try:
    journal_v4._validate_payload('selection_frozen', {
        'input_head_sha256': '0' * 64,
        'advancing': list(TOP40_V4_LAYOUT.team_ids[:7]),
        'selection_freeze_path': 'x',
        'selection_freeze_sha256': '1' * 64,
    })
except journal_v4.JournalError:
    pass
else:
    raise AssertionError('seven finalists were accepted')
"""
    completed = subprocess.run(
        (sys.executable, "-c", script),
        cwd=ROOT,
        env=_r2_environment(),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_activated_r2_decorator_remains_a_noop_for_default_r1_edition(
    tmp_path: Path,
) -> None:
    script = """
from pathlib import Path
import sys
from crypto_trade.tournament import research_runtime_v4
@research_runtime_v4.serialized_activated_r2_command
def sample(root):
    return Path(root).name
assert sample(sys.argv[1]) == Path(sys.argv[1]).name
"""
    environment = dict(os.environ)
    environment.pop("CRYPTO_TRADE_TOP40_V4_EDITION", None)
    environment["PYTHONPATH"] = "src"
    completed = subprocess.run(
        (sys.executable, "-c", script, str(tmp_path)),
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_open_lane_allows_exactly_one_explicit_mechanism_pivot() -> None:
    script = """
from types import SimpleNamespace
from crypto_trade.tournament import orchestrator_v4

def record(number, candidate_id, mechanism, tags, parent=None):
    return {'payload': {'team_id': 'team-01', 'metadata': {
        'mechanism': mechanism, 'tags': tags, 'parent_candidate_id': parent,
    }, 'trial_number': number, 'candidate_id': candidate_id}}

first = SimpleNamespace(is_requests={})
orchestrator_v4._validate_open_lane_mechanism(
    first, team_id='team-01', metadata={
        'mechanism': 'alpha', 'tags': ['baseline'], 'parent_candidate_id': None,
    }
)
history = SimpleNamespace(is_requests={
    'a': record(1, 'baseline', 'alpha', ['baseline']),
})
try:
    orchestrator_v4._validate_open_lane_mechanism(
        history, team_id='team-01', metadata={
            'mechanism': 'beta', 'tags': ['baseline'], 'parent_candidate_id': None,
        }
    )
except orchestrator_v4.OrchestratorError:
    pass
else:
    raise AssertionError('untagged pivot was accepted')
orchestrator_v4._validate_open_lane_mechanism(
    history,
    team_id='team-01',
    metadata={
        'mechanism': 'price-only control of alpha',
        'tags': ['control-ablation'],
        'parent_candidate_id': 'baseline',
    },
)
try:
    orchestrator_v4._validate_open_lane_mechanism(
        history,
        team_id='team-01',
        metadata={
            'mechanism': 'unparented control of alpha',
            'tags': ['control-ablation'],
            'parent_candidate_id': None,
        },
    )
except orchestrator_v4.OrchestratorError:
    pass
else:
    raise AssertionError('unparented descriptive variant was accepted')
orchestrator_v4._validate_open_lane_mechanism(
    history,
    team_id='team-01',
    metadata={
        'mechanism': 'beta', 'tags': ['mechanism-pivot'], 'parent_candidate_id': None,
    },
)
used = SimpleNamespace(is_requests={
    'a': record(1, 'baseline', 'alpha', ['baseline']),
    'b': record(2, 'pivot', 'beta', ['mechanism-pivot']),
})
try:
    orchestrator_v4._validate_open_lane_mechanism(
        used,
        team_id='team-01',
        metadata={
            'mechanism': 'beta', 'tags': ['mechanism-pivot'], 'parent_candidate_id': 'pivot',
        },
    )
except orchestrator_v4.OrchestratorError:
    pass
else:
    raise AssertionError('no-op repeated pivot tag was accepted')
try:
    orchestrator_v4._validate_open_lane_mechanism(
        used,
        team_id='team-01',
        metadata={
            'mechanism': 'gamma', 'tags': ['mechanism-pivot'], 'parent_candidate_id': 'pivot',
        },
    )
except orchestrator_v4.OrchestratorError:
    pass
else:
    raise AssertionError('second pivot was accepted')
"""
    completed = subprocess.run(
        (sys.executable, "-c", script),
        cwd=ROOT,
        env=_r2_environment(),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_candidate_attestation_fails_closed_on_one_false_fact(tmp_path: Path) -> None:
    candidate = (
        tmp_path
        / "tournament/top40-v4-r2/teams/team-01/candidates/attested-candidate"
    )
    candidate.mkdir(parents=True)
    attestation = {
        "schema_version": 1,
        "tournament": "quant-portfolio-blind-top40-v4-r2",
        "team_id": "team-01",
        "candidate_id": "attested-candidate",
        "access_policy_followed": True,
        "other_team_artifacts_accessed": False,
        "legacy_tournament_artifacts_accessed": False,
        "sealed_data_accessed": False,
        "timestamp_target_table_embedded": False,
    }
    path = candidate / "cleanroom-attestation.json"
    path.write_text(json.dumps(attestation), encoding="utf-8")
    script = """
import sys
from crypto_trade.tournament.isolation_v4 import validate_candidate_attestation
validate_candidate_attestation(
    sys.argv[1], team_id='team-01', candidate_id='attested-candidate',
    candidate_root=sys.argv[2],
)
"""
    accepted = subprocess.run(
        (sys.executable, "-c", script, str(tmp_path), str(candidate)),
        cwd=ROOT,
        env=_r2_environment(),
        check=False,
        capture_output=True,
        text=True,
    )
    assert accepted.returncode == 0, accepted.stderr
    attestation["sealed_data_accessed"] = True
    path.write_text(json.dumps(attestation), encoding="utf-8")
    rejected = subprocess.run(
        (sys.executable, "-c", script, str(tmp_path), str(candidate)),
        cwd=ROOT,
        env=_r2_environment(),
        check=False,
        capture_output=True,
        text=True,
    )
    assert rejected.returncode != 0
    assert "attestation is missing or false" in rejected.stderr


def test_candidate_metadata_requires_coordinate_to_match_material_parameter(
    tmp_path: Path,
) -> None:
    team_root = orchestrator_v4.TOP40_V4_LAYOUT.team_root("team-01")
    candidate = tmp_path / team_root / "candidates/role-control"
    candidate.mkdir(parents=True)
    (candidate / "strategy.py").write_text("VALUE = 1\n", encoding="utf-8")
    (candidate / "candidate.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "team_id": "team-01",
                "candidate_id": "role-control",
                "parent_candidate_id": "baseline",
                "mechanism": "role control",
                "hypothesis": "causal role check",
                "falsifier": "role contribution is absent",
                "formation_horizon": "six completed bars",
                "rebalance_horizon": "every completed boundary",
                "control_profile": "long role only",
                "neighborhood_id": None,
                "neighborhood_coordinates": {"active_role": 1},
                "tags": ["role-check"],
                "material_parameters": {"formation_bars": 6},
            }
        ),
        encoding="utf-8",
    )
    (candidate / "cleanroom-attestation.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "tournament": orchestrator_v4.TOP40_V4_LAYOUT.name,
                "team_id": "team-01",
                "candidate_id": "role-control",
                "access_policy_followed": True,
                "other_team_artifacts_accessed": False,
                "legacy_tournament_artifacts_accessed": False,
                "sealed_data_accessed": False,
                "timestamp_target_table_embedded": False,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(
        orchestrator_v4.OrchestratorError,
        match="coordinate must match a numeric material parameter",
    ):
        orchestrator_v4._candidate_metadata(
            tmp_path,
            {"mandates": {"team-01": "open-independent-mechanism"}},
            "team-01",
            f"{team_root}/candidates/role-control/strategy.py",
        )


def test_accepted_trial_receipt_preserves_certificate_request_hash(tmp_path: Path) -> None:
    script = """
import json, sys
from pathlib import Path
from crypto_trade.tournament.orchestrator_v4 import _write_trial_receipt
request_hash = 'a' * 64
request = {'payload': {
    'team_id': 'team-15', 'trial_number': 3, 'run_id': 'team15-is-03-candidate',
    'candidate_id': 'candidate', 'metadata': {'tags': ['baseline', 'formation-grid']},
}}
relative = _write_trial_receipt(Path(sys.argv[1]), request_hash, request)
print(json.dumps({'relative': relative}))
"""
    completed = subprocess.run(
        (sys.executable, "-c", script, str(tmp_path)),
        cwd=ROOT,
        env=_r2_environment(),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    relative = json.loads(completed.stdout)["relative"]
    receipt = json.loads((tmp_path / relative).read_text(encoding="utf-8"))
    assert relative.startswith("reports-top40-v4-r2/is/team-15/receipts/")
    assert receipt["request_record_sha256"] == "a" * 64
    assert receipt["tags"] == ["baseline", "formation-grid"]


def test_nomination_proves_exact_sign_inversion_from_target_artifacts() -> None:
    script = """
import pandas as pd
from crypto_trade.tournament import orchestrator_v4
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN as FLAG

index = pd.date_range('2020-01-01', periods=2, freq='8h', tz='UTC')
baseline_targets = pd.DataFrame({FLAG: [True, False], 'AUSDT': [0.1, 0.0]}, index=index)
inverted_targets = pd.DataFrame({FLAG: [True, False], 'AUSDT': [-0.1, -0.0]}, index=index)
frames = {'b': baseline_targets, 'i': inverted_targets}
orchestrator_v4._verified_request_targets = lambda _root, _state, digest: frames[digest]

def request(candidate_id, parent):
    return {'payload': {
        'candidate_id': candidate_id,
        'metadata': {
            'parent_candidate_id': parent,
            'mechanism': 'independent-mechanism',
            'formation_horizon': '30-bars',
            'rebalance_horizon': 'weekly',
            'control_profile': 'controls-off',
        },
        'authority': {'risk_policy_sha256': 'a' * 64},
    }}

requests = {'b': request('baseline', None), 'i': request('inversion', 'baseline')}
evidence = {'baseline': ['b'], 'sign-inversion': ['i']}
state = type('State', (), {'is_terminals': {
    'b': {'event_type': 'is_succeeded'},
    'i': {'event_type': 'is_succeeded'},
}})()
orchestrator_v4._validate_exact_sign_inversions(None, state, requests, evidence)
frames['i'] = baseline_targets
try:
    orchestrator_v4._validate_exact_sign_inversions(None, state, requests, evidence)
except orchestrator_v4.OrchestratorError:
    pass
else:
    raise AssertionError('a mislabeled positive copy passed exact inversion proof')
"""
    completed = subprocess.run(
        (sys.executable, "-c", script),
        cwd=ROOT,
        env=_r2_environment(),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_july_holdout_counts_nine_calendar_quarters() -> None:
    config = _config()
    packet = {
        "scored_window": {
            "base_metrics": {
                "annualized_return": 0.1,
                "max_drawdown": 0.1,
                "positive_quarter_fraction": 5.0 / 9.0,
            },
            "double_cost_metrics": {"annualized_return": 0.05, "net_sharpe": 0.5},
        },
        "diagnostics": {"gross_edge_per_turnover_bps": 100.0, "annualized_turnover": 2.0},
        "team_id": "team-01",
    }
    result = scoring_v4.assess_historical_oos(packet, config)
    assert result["positive_quarters"] == 5
    assert result["winner_eligible"] is True


def test_ensemble_release_index_includes_every_july_2026_day(tmp_path: Path) -> None:
    staging = tmp_path / "release"
    packet = orchestrator_v4._ensemble_release(
        tmp_path,
        staging,
        {
            "ensemble": {
                "available": False,
                "minimum_constituents": 2,
                "constituent_weights": {},
                "cash_weight": 1.0,
            }
        },
        object(),
        _config(),
    )
    frame = pd.read_csv(staging / "ensemble/base_daily_returns.csv")
    dates = pd.to_datetime(frame["date"], utc=True)
    assert dates.iloc[0] == pd.Timestamp("2024-07-01T00:00:00Z")
    assert dates.iloc[-1] == pd.Timestamp("2026-07-31T00:00:00Z")
    assert len(frame) == 761
    assert packet["scenarios"]["base"]["cumulative_return"] == 0.0


def test_activation_rejects_a_manifest_that_stops_before_july_2026(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"window": {"hard_end_exclusive": "2026-07-01T00:00:00+00:00"}}),
        encoding="utf-8",
    )
    config = {
        "data": {
            "manifest_path": "manifest.json",
            "hard_end_exclusive": "2026-08-01T00:00:00Z",
        },
        "splits": {"historical_oos": {"end_exclusive": "2026-08-01T00:00:00Z"}},
    }
    with pytest.raises(activation_v4.ActivationError, match="does not cover"):
        activation_v4._validate_snapshot_window(tmp_path, config)


def test_activation_test_process_is_explicitly_r2(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def run(*_args: object, **kwargs: object) -> SimpleNamespace:
        captured.update(kwargs)
        return SimpleNamespace(stdout=b"passed\n", returncode=0)

    monkeypatch.setattr(activation_v4.subprocess, "run", run)
    output, returncode = activation_v4._run_tests(ROOT)
    assert output == b"passed\n"
    assert returncode == 0
    assert captured["env"]["CRYPTO_TRADE_TOP40_V4_EDITION"] == "r2"


def test_activation_cli_bootstrap_does_not_hold_child_broker_lease(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cli = _tournament_cli_module()
    calls: list[Path] = []
    monkeypatch.setattr(
        cli.orchestrator_v4,
        "activate",
        lambda root: calls.append(Path(root)) or {"activated": True},
    )

    @contextlib.contextmanager
    def forbidden_lease(_root: Path):
        raise AssertionError("activation must not hold the broker lease across child tests")
        yield  # pragma: no cover

    monkeypatch.setattr(cli.research_runtime_v4, "broker_lease", forbidden_lease)
    assert cli.main(("--root", str(tmp_path), "activate")) == 0
    assert calls == [tmp_path]
    assert json.loads(capsys.readouterr().out) == {"activated": True}


def test_pre_activation_result_call_cannot_invert_activation_lock_order(
    tmp_path: Path,
) -> None:
    direct_script = """
from pathlib import Path
import sys
from crypto_trade.tournament import orchestrator_v4
try:
    orchestrator_v4.run_is(
        Path(sys.argv[1]),
        'team-01',
        'missing/strategy.py',
        purpose='must fail before broker lease',
    )
except BaseException as exc:
    print(type(exc).__name__, flush=True)
else:
    raise AssertionError('pre-activation result call unexpectedly succeeded')
"""
    with orchestrator_v4._result_lock(tmp_path):
        commands = (
            (sys.executable, "-c", direct_script, str(tmp_path)),
            (
                sys.executable,
                "scripts/top40_v4_r2_tournament.py",
                "--root",
                str(tmp_path),
                "is-run",
                "team-01",
                "missing/strategy.py",
                "--purpose",
                "must fail before broker lease",
            ),
        )
        observations: list[tuple[int, str, str]] = []
        for command in commands:
            child = subprocess.Popen(
                command,
                cwd=ROOT,
                env=_r2_environment(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                stdout, stderr = child.communicate(timeout=5)
            finally:
                if child.poll() is None:
                    child.kill()
                    child.wait(timeout=5)
            observations.append((int(child.returncode), stdout, stderr))
    direct, cli = observations
    assert direct[0] == 0, direct[2]
    assert direct[1].strip() in {"ActivationError", "FileNotFoundError", "ValueError"}
    assert cli[0] == 2
    assert "top40-v4-r2:" in cli[2]


def test_verified_snapshot_contains_final_july_bar_and_excludes_august() -> None:
    config = _config()
    manifest_path = ROOT / config["data"]["manifest_path"]
    manifest_payload = manifest_path.read_bytes()
    manifest = json.loads(manifest_payload)
    assert hashlib.sha256(manifest_payload).hexdigest() == config["data"]["manifest_sha256"]
    assert manifest["window"]["hard_end_exclusive"] == "2026-08-01T00:00:00+00:00"
    entries = {row["name"]: row for row in manifest["files"]}
    assert len(entries) == 12

    bars = pd.read_parquet(ROOT / entries["bars"]["path"], columns=["open_time"])
    bar_times = pd.to_datetime(bars["open_time"], utc=True)
    assert bar_times.max() == pd.Timestamp("2026-07-31T16:00:00Z")
    assert not (bar_times >= pd.Timestamp("2026-08-01T00:00:00Z")).any()

    funding = pd.read_parquet(
        ROOT / entries["funding"]["path"], columns=["funding_time"]
    )
    funding_times = pd.to_datetime(funding["funding_time"], utc=True)
    assert funding_times.max().month == 7 and funding_times.max().year == 2026
    assert not (funding_times >= pd.Timestamp("2026-08-01T00:00:00Z")).any()


def test_r2_pure_crypto_report_is_bound_and_unreviewed_archives_are_ineligible() -> None:
    config = _config()
    report = pure_crypto_universe_v4_r2.audit_report_bytes(ROOT, config)
    parsed = json.loads(report)
    authority = config["universe"]["a6_authority"]
    assert hashlib.sha256(report).hexdigest() == authority["audit_report_sha256"]
    assert parsed["status"] == "passed"
    assert parsed["violations"] == []
    assert parsed["counts"]["membership_symbols"] == 328
    assert parsed["excluded_unreviewed_archive_symbol_ids"] == ["AERGOUSDT", "BTCSTUSDT"]
    membership = pd.read_parquet(
        ROOT / config["universe"]["membership_path"], columns=["symbol"]
    )
    assert not set(parsed["excluded_unreviewed_archive_symbol_ids"]).intersection(
        membership["symbol"]
    )


def test_r1_default_layout_and_contract_remain_reproducible() -> None:
    script = """
from crypto_trade.tournament import (
    activation_v4, journal_v4, orchestrator_v4, source_archive_v4, top40_v4,
)
from crypto_trade.tournament.layout_v4 import TOP40_V4_LAYOUT
loaded = top40_v4.load_config(root='.')
assert TOP40_V4_LAYOUT.name == 'quant-portfolio-blind-top40-v4-r1'
assert len(TOP40_V4_LAYOUT.team_ids) == 12
assert loaded.raw['selection']['ranking']['advance_count'] == 5
assert journal_v4.SCHEMA_VERSION == 'top40-v4-r1-lifecycle-journal-v1'
assert source_archive_v4.SCHEMA_VERSION == 'top40-v4-r1-candidate-source-archive-v1'
assert activation_v4.SCHEMA_VERSION == 'top40-v4-r1-activation-freeze-v1'
assert orchestrator_v4._SCHEMA_PREFIX == 'top40-v4-r1'
"""
    environment = dict(os.environ)
    environment.pop("CRYPTO_TRADE_TOP40_V4_EDITION", None)
    environment["PYTHONPATH"] = "src"
    completed = subprocess.run(
        (sys.executable, "-c", script),
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("splits", "historical_oos", "raw_data_visible_to_teams"), True),
        (("splits", "historical_oos", "feedback"), "per-finalist-immediate"),
        (("selection", "ranking", "eligible_population"), "any-nominee"),
        (("selection", "ranking", "minimum_finalist_count"), 4),
        (
            ("selection", "ranking", "qualification_policy"),
            "strict-gates-only",
        ),
        (("selection", "ranking", "fallback_changes_frozen_gate_results"), True),
        (("ensemble", "role"), "winner-eligible"),
        (("isolation", "research_network_enabled"), True),
    ),
)
def test_r2_critical_contract_mutations_fail_closed(
    path: tuple[str, ...], value: object
) -> None:
    config = deepcopy(_config())
    current: dict[str, object] = config
    for component in path[:-1]:
        current = current[component]  # type: ignore[assignment]
    current[path[-1]] = value
    with pytest.raises(ValueError, match="frozen contract|isolation policy"):
        top40_v4.validate_config(config)


def test_dnf_ensemble_weight_is_reported_as_effective_cash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(orchestrator_v4, "_historical_summary_for_team", lambda *_: None)
    staging = tmp_path / "release"
    packet = orchestrator_v4._ensemble_release(
        tmp_path,
        staging,
        {
            "ensemble": {
                "available": True,
                "minimum_constituents": 2,
                "constituent_weights": {"team-01": 0.25},
                "cash_weight": 0.75,
            }
        },
        object(),
        _config(),
    )
    assert packet["frozen_cash_weight"] == 0.75
    assert packet["dnf_constituent_weights_to_cash"] == {"team-01": 0.25}
    assert packet["active_constituent_weights"] == {}
    assert packet["effective_cash_weight"] == 1.0
    assert packet["cash_weight"] == 1.0
    assert sum(packet["active_constituent_weights"].values()) + packet["cash_weight"] == 1.0


def test_source_capture_rejects_symlink_fifo_hardlink_and_substitution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")
    symlink = tmp_path / "symlink.py"
    symlink.symlink_to(target)
    with pytest.raises(runner_v4.StrategySandboxError):
        runner_v4._stable_file_bytes(symlink)

    fifo = tmp_path / "fifo.py"
    os.mkfifo(fifo)
    with pytest.raises(runner_v4.StrategySandboxError):
        runner_v4._stable_file_bytes(fifo)

    hardlink = tmp_path / "hardlink.py"
    os.link(target, hardlink)
    with pytest.raises(runner_v4.StrategySandboxError):
        runner_v4._stable_file_bytes(target)

    source = tmp_path / "source.py"
    replacement = tmp_path / "replacement.py"
    displaced = tmp_path / "displaced.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    replacement.write_text("VALUE = 2\n", encoding="utf-8")
    real_open = os.open

    def swapping_open(path: object, flags: int, *args: object) -> int:
        descriptor = real_open(path, flags, *args)
        if Path(path) == source:
            source.rename(displaced)
            replacement.rename(source)
        return descriptor

    monkeypatch.setattr(runner_v4.os, "open", swapping_open)
    with pytest.raises(runner_v4.StrategySandboxError, match="changed while reading"):
        runner_v4._stable_file_bytes(source)


def test_source_capture_pins_intermediate_candidate_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    candidate = (
        tmp_path
        / TOP40_V4_R2_LAYOUT.team_root("team-01")
        / "candidates"
        / "candidate"
    )
    candidate.mkdir(parents=True)
    (candidate / "strategy.py").write_text("VALUE = 'approved'\n", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "strategy.py").write_text("VALUE = 'outside'\n", encoding="utf-8")
    displaced = candidate.with_name("candidate-displaced")
    real_open = os.open
    swapped = False

    def swapping_directory_open(
        path: object, flags: int, *args: object, **kwargs: object
    ) -> int:
        nonlocal swapped
        descriptor = real_open(path, flags, *args, **kwargs)
        if path == "candidate" and kwargs.get("dir_fd") is not None and not swapped:
            swapped = True
            candidate.rename(displaced)
            candidate.symlink_to(outside, target_is_directory=True)
        return descriptor

    monkeypatch.setattr(runner_v4.os, "open", swapping_directory_open)
    with pytest.raises(runner_v4.StrategySandboxError, match="pin|changed"):
        runner_v4.capture_source_bundle(
            tmp_path,
            "team-01",
            (candidate / "strategy.py").relative_to(tmp_path),
        )
    assert swapped is True


def test_r2_worker_mount_contains_python_only(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "strategy.py").write_text("def build_strategy():\n    return object()\n")
    (candidate / "helper.py").write_text("VALUE = 1\n")
    (candidate / "README.md").write_text("encoded-looking evidence stays non-executable\n")
    (candidate / "risk_policy.json").write_text('{"schema_version":1}\n')
    files = runner_v4._team_tree_files(candidate)
    staged = {item.relative for item in files if item.staged}
    assert staged == {"helper.py", "strategy.py"}
    assert {item.relative for item in files if not item.staged} == {
        "README.md",
        "risk_policy.json",
    }


def test_r2_worker_sanitized_environment_binds_source_and_starts(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    runtime_site_packages = tmp_path / "runtime-site-packages"
    empty_dir = tmp_path / "empty-dir"
    empty_file = tmp_path / "empty-file"
    for directory in (bundle, runtime_site_packages, empty_dir):
        directory.mkdir()
    empty_file.touch()
    (bundle / "strategy.py").write_text(
        "class Strategy:\n"
        "    def target_weights(self, context, *, seed):\n"
        "        return {}\n"
        "def build_strategy():\n"
        "    return Strategy()\n",
        encoding="utf-8",
    )
    repository_parent = runner_v4._runner_repository_parent()
    site_packages = runner_v4._current_venv_site_packages(repository_parent)
    environment = runner_v4._strategy_worker_environment(ROOT, 20260713)
    assert environment["PYTHONPATH"] == str((ROOT / "src").resolve())
    assert "HOME" in environment and environment["HOME"] == "/nonexistent"
    command = runner_v4._strategy_worker_command(
        ROOT,
        repository_parent,
        bundle,
        site_packages,
        runtime_site_packages,
        "strategy.py",
        empty_dir,
        empty_file,
    )
    completed = subprocess.run(
        command,
        cwd=tmp_path,
        env=environment,
        input="",
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode == 0, (completed.stdout, completed.stderr)


def test_missing_lane_marker_is_restored_but_conflicts_fail_closed(tmp_path: Path) -> None:
    team = tmp_path / TOP40_V4_R2_LAYOUT.team_root("team-01")
    for directory in ("outbox", "work"):
        path = team / directory
        path.mkdir(parents=True)
        path.chmod(0o755)
    work_marker = team / "work/.keep"
    work_marker.write_bytes(b"\n")
    work_marker.chmod(0o644)

    assert research_runtime_v4._restore_writable_lane_markers(tmp_path, "team-01") == (
        "outbox",
    )
    outbox_marker = team / "outbox/.keep"
    assert outbox_marker.read_bytes() == b"\n"
    assert stat.S_IMODE(outbox_marker.stat().st_mode) == 0o644
    assert outbox_marker.stat().st_nlink == 1
    assert research_runtime_v4._restore_writable_lane_markers(tmp_path, "team-01") == ()

    outbox_marker.write_bytes(b"changed\n")
    with pytest.raises(research_runtime_v4.ResearchRuntimeError, match="frozen authority"):
        research_runtime_v4._restore_writable_lane_markers(tmp_path, "team-01")
    assert outbox_marker.read_bytes() == b"changed\n"


@pytest.mark.parametrize("resume_path", ("consume", "broker-launch", "direct-launch"))
def test_crash_missing_markers_are_restored_before_activation_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    resume_path: str,
) -> None:
    team = tmp_path / TOP40_V4_R2_LAYOUT.team_root("team-01")
    for directory in ("outbox", "work"):
        path = team / directory
        path.mkdir(parents=True)
        path.chmod(0o755)
    if resume_path == "consume":
        (team / "outbox/batch-1.json").write_text("{}\n", encoding="utf-8")

    checked: list[bool] = []

    def stop_after_marker_check(*_args: object, **_kwargs: object) -> None:
        for directory in ("outbox", "work"):
            marker = team / directory / ".keep"
            assert marker.read_bytes() == b"\n"
            assert stat.S_IMODE(marker.stat().st_mode) == 0o644
            assert marker.stat().st_nlink == 1
        checked.append(True)
        raise activation_v4.ActivationError("stop after marker recovery")

    monkeypatch.setattr(activation_v4, "validate", stop_after_marker_check)
    with pytest.raises(activation_v4.ActivationError, match="stop after marker recovery"):
        if resume_path == "direct-launch":
            research_runtime_v4.launch_team_phase.__wrapped__(
                tmp_path, "team-01", "discovery"
            )
        else:
            broker = _broker_module()
            if resume_path == "consume":
                broker.consume_batch.__wrapped__(tmp_path, "team-01", "discovery")
            else:
                broker.launch_phase.__wrapped__(tmp_path, "team-01", "discovery")
    assert checked == [True]


def test_lane_audit_is_independent_of_peer_corruption(tmp_path: Path) -> None:
    for team_id in ("team-01", "team-02"):
        team = tmp_path / TOP40_V4_R2_LAYOUT.team_root(team_id)
        for directory in ("candidates", "feedback", "outbox", "work"):
            (team / directory).mkdir(parents=True, exist_ok=True)
        (team / "ACCESS-POLICY.json").write_text(
            json.dumps(isolation_v4.access_policy(team_id), indent=2, sort_keys=True) + "\n"
        )
        (team / "TEAM-BRIEF.md").write_text(isolation_v4.team_brief(team_id))
    first = isolation_v4.audit_team_surface(tmp_path, "team-01")
    (tmp_path / TOP40_V4_R2_LAYOUT.team_root("team-02") / "candidates" / "opaque.bin").write_bytes(
        b"peer progress must not affect lane one"
    )
    second = isolation_v4.audit_team_surface(tmp_path, "team-01")
    assert first == second == {
        "ok": True,
        "applicable": True,
        "tournament": TOP40_V4_R2_LAYOUT.name,
    }


def test_research_profile_is_networkless_and_cannot_read_repository_root() -> None:
    spec = research_runtime_v4.profile_spec(ROOT, "team-01")
    filesystem = spec["filesystem"]
    assert spec["network"] == {"enabled": False}
    assert spec["approvals"] == "never"
    assert str(ROOT) not in filesystem
    assert filesystem[":minimal"] == "read"
    assert filesystem[str(ROOT / "tournament/top40-v4-r2/team-kit")] == "read"
    assert filesystem[str(ROOT / TOP40_V4_R2_LAYOUT.team_root("team-01"))] == "read"
    team = ROOT / TOP40_V4_R2_LAYOUT.team_root("team-01")
    assert filesystem[str(team / "candidates")] == "write"
    assert filesystem[str(team / "outbox")] == "write"
    assert filesystem[str(team / "work")] == "write"
    runtime = spec["model_runtime"]
    assert runtime["skill_catalog"] == "empty-system-marker"
    assert str(ROOT / runtime["codex_home"]) not in filesystem


def test_model_exec_uses_permission_profile_without_legacy_sandbox() -> None:
    profile_arguments = research_runtime_v4.codex_profile_arguments(ROOT, "team-01")
    disabled_arguments = sum(
        (["--disable", feature] for feature in research_runtime_v4._DISABLED_FEATURES), []
    )
    command = research_runtime_v4._codex_exec_command(
        ROOT, "team-01", model="test-model", prompt="test prompt"
    )
    expected_prefix = [
        command[0],
        "exec",
        "--strict-config",
        "--ignore-user-config",
        *profile_arguments,
        *disabled_arguments,
    ]
    assert command[: len(expected_prefix)] == expected_prefix
    assert "-s" not in command
    assert "--sandbox" not in command
    ignored = command.index("--ignore-user-config")
    assert all(index > ignored for index, argument in enumerate(command) if argument == "-c")
    assert all(
        index > ignored for index, argument in enumerate(command) if argument == "--disable"
    )


def test_private_model_runtime_is_auth_only_and_skill_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    organizer = tmp_path / "organizer-codex"
    (organizer / "skills").mkdir(parents=True)
    (organizer / "plugins").mkdir()
    (organizer / "auth.json").write_bytes(b'{"auth":"fixture"}\n')
    root = tmp_path / "root"
    root.mkdir()
    monkeypatch.setattr(research_runtime_v4, "_organizer_codex_home", lambda: organizer)
    monkeypatch.setattr(research_runtime_v4, "_codex_binary", lambda: Path("/usr/bin/true"))
    monkeypatch.setattr(
        research_runtime_v4,
        "_codex_version",
        lambda _binary: research_runtime_v4._EXPECTED_CODEX_VERSION,
    )

    spec = research_runtime_v4.ensure_private_model_runtime(root, "team-01")
    private = (
        root
        / research_runtime_v4._PRIVATE_MODEL_RUNTIME_RELATIVE
        / "team-01/codex-home"
    )
    assert (private / "auth.json").read_bytes() == b'{"auth":"fixture"}\n'
    assert sorted(path.relative_to(private).as_posix() for path in private.rglob("*")) == [
        "auth.json",
        "skills",
        "skills/.system",
        "skills/.system/.codex-system-skills.marker",
    ]
    assert spec["skill_catalog"] == "empty-system-marker"
    assert research_runtime_v4.model_runtime_sha256(root, "team-01") == hashlib.sha256(
        research_runtime_v4._canonical(spec)
    ).hexdigest()
    assert spec["team_id"] == "team-01"
    assert spec["codex_version"] == "codex-cli 0.148.0"
    assert research_runtime_v4.model_runtime_sha256(
        root, "team-02"
    ) != research_runtime_v4.model_runtime_sha256(root, "team-01")
    for path in (
        root / research_runtime_v4._PRIVATE_MODEL_RUNTIME_RELATIVE,
        private,
        private / "skills",
        private / "skills/.system",
    ):
        assert path.stat().st_mode & 0o077 == 0


def test_private_model_runtime_clears_bounded_client_state_between_phases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    organizer = tmp_path / "organizer-codex"
    organizer.mkdir()
    (organizer / "auth.json").write_bytes(b'{"auth":"fixture"}\n')
    root = tmp_path / "root"
    root.mkdir()
    codex_home = (
        root
        / research_runtime_v4._PRIVATE_MODEL_RUNTIME_RELATIVE
        / "team-01/codex-home"
    )

    def prompt_probe(*_args: object, **_kwargs: object) -> SimpleNamespace:
        (codex_home / "installation_id").write_bytes(b"codex-explicit-public-mode")
        (codex_home / "memories_1.sqlite").write_bytes(b"phase-local-state")
        (codex_home / "state_5.sqlite-shm").write_bytes(b"phase-local-shared-memory")
        (codex_home / "state_5.sqlite-wal").write_bytes(b"phase-local-write-ahead-log")
        (codex_home / "shell_snapshots").mkdir()
        (codex_home / "installation_id").chmod(0o644)
        (codex_home / "memories_1.sqlite").chmod(0o600)
        (codex_home / "state_5.sqlite-shm").chmod(0o600)
        (codex_home / "state_5.sqlite-wal").chmod(0o600)
        (codex_home / "shell_snapshots").chmod(0o700)
        return SimpleNamespace(returncode=0, stdout=b"catalog-probe", stderr=b"")

    monkeypatch.setattr(research_runtime_v4, "_organizer_codex_home", lambda: organizer)
    monkeypatch.setattr(research_runtime_v4, "_codex_binary", lambda: Path("/usr/bin/true"))
    monkeypatch.setattr(
        research_runtime_v4,
        "_codex_version",
        lambda _binary: research_runtime_v4._EXPECTED_CODEX_VERSION,
    )
    monkeypatch.setattr(research_runtime_v4.subprocess, "run", prompt_probe)

    research_runtime_v4.ensure_private_model_runtime(root, "team-01")
    assert sorted(path.relative_to(codex_home).as_posix() for path in codex_home.rglob("*")) == [
        "auth.json",
        "skills",
        "skills/.system",
        "skills/.system/.codex-system-skills.marker",
    ]

    # A safely bounded artifact left by an interrupted prior subprocess is removed before the
    # next prompt inspection as well as after it.
    (codex_home / "state_5.sqlite").write_bytes(b"interrupted-state")
    (codex_home / "state_5.sqlite").chmod(0o600)
    research_runtime_v4.ensure_private_model_runtime(root, "team-01")
    assert not (codex_home / "state_5.sqlite").exists()
    assert not (codex_home / "state_5.sqlite-shm").exists()
    assert not (codex_home / "state_5.sqlite-wal").exists()
    assert not (codex_home / "memories_1.sqlite").exists()


def test_private_model_runtime_does_not_follow_installation_marker_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    organizer = tmp_path / "organizer-codex"
    organizer.mkdir()
    (organizer / "auth.json").write_bytes(b'{"auth":"fixture"}\n')
    root = tmp_path / "root"
    root.mkdir()
    monkeypatch.setattr(research_runtime_v4, "_organizer_codex_home", lambda: organizer)
    monkeypatch.setattr(research_runtime_v4, "_codex_binary", lambda: Path("/usr/bin/true"))
    monkeypatch.setattr(
        research_runtime_v4,
        "_codex_version",
        lambda _binary: research_runtime_v4._EXPECTED_CODEX_VERSION,
    )
    research_runtime_v4.ensure_private_model_runtime(root, "team-01")
    outside = tmp_path / "outside"
    outside.write_bytes(b"must-not-change")
    outside.chmod(0o644)
    marker = (
        root
        / research_runtime_v4._PRIVATE_MODEL_RUNTIME_RELATIVE
        / "team-01/codex-home/installation_id"
    )
    marker.symlink_to(outside)
    with pytest.raises(
        research_runtime_v4.ResearchRuntimeError,
        match="installation marker is unsafe",
    ):
        research_runtime_v4.ensure_private_model_runtime(root, "team-01")
    assert outside.read_bytes() == b"must-not-change"
    assert stat.S_IMODE(outside.stat().st_mode) == 0o644


def test_private_model_runtime_resumes_partial_nested_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    organizer = tmp_path / "organizer-codex"
    organizer.mkdir()
    (organizer / "auth.json").write_bytes(b'{"auth":"fixture"}\n')
    root = tmp_path / "root"
    root.mkdir()
    monkeypatch.setattr(research_runtime_v4, "_organizer_codex_home", lambda: organizer)
    monkeypatch.setattr(research_runtime_v4, "_codex_binary", lambda: Path("/usr/bin/true"))
    monkeypatch.setattr(
        research_runtime_v4,
        "_codex_version",
        lambda _binary: research_runtime_v4._EXPECTED_CODEX_VERSION,
    )
    research_runtime_v4.ensure_private_model_runtime(root, "team-01")
    runtime = root / research_runtime_v4._PRIVATE_MODEL_RUNTIME_RELATIVE / "team-01"

    # Model a crash after some wrapper names and the private TMP lock were durably unlinked but
    # before their now-partial parent directories were removed.
    wrapper = runtime / "codex-home/tmp/arg0/codex-arg0ABCDEF"
    wrapper.mkdir(parents=True, mode=0o700)
    (runtime / "codex-home/tmp").chmod(0o700)
    (runtime / "codex-home/tmp/arg0").chmod(0o700)
    (wrapper / "apply_patch").symlink_to("/usr/bin/true")
    (wrapper / "codex-linux-sandbox").symlink_to("/usr/bin/true")
    sandbox_tmp = runtime / "tmp/codex-bwrap-synthetic-mount-targets-123"
    sandbox_tmp.mkdir(mode=0o700)

    research_runtime_v4.ensure_private_model_runtime(root, "team-01")
    assert not (runtime / "codex-home/tmp").exists()
    assert list((runtime / "tmp").iterdir()) == []


def test_private_model_runtime_rejects_partial_wrapper_with_wrong_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    organizer = tmp_path / "organizer-codex"
    organizer.mkdir()
    (organizer / "auth.json").write_bytes(b'{"auth":"fixture"}\n')
    root = tmp_path / "root"
    root.mkdir()
    monkeypatch.setattr(research_runtime_v4, "_organizer_codex_home", lambda: organizer)
    monkeypatch.setattr(research_runtime_v4, "_codex_binary", lambda: Path("/usr/bin/true"))
    monkeypatch.setattr(
        research_runtime_v4,
        "_codex_version",
        lambda _binary: research_runtime_v4._EXPECTED_CODEX_VERSION,
    )
    research_runtime_v4.ensure_private_model_runtime(root, "team-01")
    wrapper = (
        root
        / research_runtime_v4._PRIVATE_MODEL_RUNTIME_RELATIVE
        / "team-01/codex-home/tmp/arg0/codex-arg0ABCDEF"
    )
    wrapper.mkdir(parents=True, mode=0o700)
    (wrapper.parents[1]).chmod(0o700)
    wrapper.parent.chmod(0o700)
    (wrapper / "apply_patch").symlink_to("/bin/false")

    with pytest.raises(
        research_runtime_v4.ResearchRuntimeError,
        match="wrapper target differs",
    ):
        research_runtime_v4.ensure_private_model_runtime(root, "team-01")
    assert (wrapper / "apply_patch").is_symlink()


def test_private_model_runtime_rejects_group_readable_client_state_before_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    organizer = tmp_path / "organizer-codex"
    organizer.mkdir()
    (organizer / "auth.json").write_bytes(b'{"auth":"fixture"}\n')
    root = tmp_path / "root"
    root.mkdir()
    monkeypatch.setattr(research_runtime_v4, "_organizer_codex_home", lambda: organizer)
    monkeypatch.setattr(research_runtime_v4, "_codex_binary", lambda: Path("/usr/bin/true"))
    monkeypatch.setattr(
        research_runtime_v4,
        "_codex_version",
        lambda _binary: research_runtime_v4._EXPECTED_CODEX_VERSION,
    )
    research_runtime_v4.ensure_private_model_runtime(root, "team-01")
    state = (
        root
        / research_runtime_v4._PRIVATE_MODEL_RUNTIME_RELATIVE
        / "team-01/codex-home/state_5.sqlite"
    )
    state.write_bytes(b"unsafe-state")
    state.chmod(0o640)
    with pytest.raises(
        research_runtime_v4.ResearchRuntimeError,
        match="volatile file is unsafe",
    ):
        research_runtime_v4.ensure_private_model_runtime(root, "team-01")
    assert state.read_bytes() == b"unsafe-state"


def test_private_model_runtime_rejects_group_readable_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    organizer = tmp_path / "organizer-codex"
    organizer.mkdir()
    (organizer / "auth.json").write_bytes(b'{"auth":"fixture"}\n')
    root = tmp_path / "root"
    root.mkdir()
    monkeypatch.setattr(research_runtime_v4, "_organizer_codex_home", lambda: organizer)
    monkeypatch.setattr(research_runtime_v4, "_codex_binary", lambda: Path("/usr/bin/true"))
    monkeypatch.setattr(
        research_runtime_v4,
        "_codex_version",
        lambda _binary: research_runtime_v4._EXPECTED_CODEX_VERSION,
    )
    research_runtime_v4.ensure_private_model_runtime(root, "team-01")
    private = root / "tournament/top40-v4-r2/private"
    private.chmod(0o750)
    with pytest.raises(
        research_runtime_v4.ResearchRuntimeError,
        match="directory permissions are unsafe",
    ):
        research_runtime_v4.ensure_private_model_runtime(root, "team-01")


def test_private_model_runtime_rejects_model_visible_skill_catalog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    organizer = tmp_path / "organizer-codex"
    organizer.mkdir()
    (organizer / "auth.json").write_bytes(b'{"auth":"fixture"}\n')
    root = tmp_path / "root"
    root.mkdir()
    monkeypatch.setattr(research_runtime_v4, "_organizer_codex_home", lambda: organizer)
    monkeypatch.setattr(research_runtime_v4, "_codex_binary", lambda: Path("/usr/bin/true"))
    monkeypatch.setattr(
        research_runtime_v4,
        "_codex_version",
        lambda _binary: research_runtime_v4._EXPECTED_CODEX_VERSION,
    )
    monkeypatch.setattr(
        research_runtime_v4.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout=b"<skills_instructions>host skill</skills_instructions>",
            stderr=b"",
        ),
    )
    with pytest.raises(
        research_runtime_v4.ResearchRuntimeError,
        match="prompt still exposes installed skills",
    ):
        research_runtime_v4.ensure_private_model_runtime(root, "team-01")


def test_private_model_runtime_rejects_codex_version_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    organizer = tmp_path / "organizer-codex"
    organizer.mkdir()
    (organizer / "auth.json").write_bytes(b'{"auth":"fixture"}\n')
    root = tmp_path / "root"
    root.mkdir()
    monkeypatch.setattr(research_runtime_v4, "_organizer_codex_home", lambda: organizer)
    monkeypatch.setattr(research_runtime_v4, "_codex_binary", lambda: Path("/usr/bin/true"))
    monkeypatch.setattr(
        research_runtime_v4,
        "_codex_version",
        lambda _binary: "codex-cli 0.149.0",
    )
    with pytest.raises(
        research_runtime_v4.ResearchRuntimeError,
        match="version differs",
    ):
        research_runtime_v4.ensure_private_model_runtime(root, "team-01")


def test_model_environment_is_frozen_per_team_and_excludes_host_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", "/host/home/must-not-pass")
    monkeypatch.setenv("CODEX_HOME", "/host/codex/must-not-pass")
    monkeypatch.setenv("TMPDIR", "/host/tmp/must-not-pass")
    environment = research_runtime_v4._private_model_environment(tmp_path, "team-03")
    assert environment["HOME"] == str(
        tmp_path / "tournament/top40-v4-r2/private/model-runtime/team-03/home"
    )
    assert environment["CODEX_HOME"] == str(
        tmp_path / "tournament/top40-v4-r2/private/model-runtime/team-03/codex-home"
    )
    assert environment["TMPDIR"] == str(
        tmp_path / "tournament/top40-v4-r2/private/model-runtime/team-03/tmp"
    )
    assert not any("/host/" in value for value in environment.values())
    assert research_runtime_v4.model_environment_sha256(
        tmp_path, "team-03"
    ) != research_runtime_v4.model_environment_sha256(tmp_path, "team-04")


def test_private_model_runtime_rejects_unexpected_home_residue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    organizer = tmp_path / "organizer-codex"
    organizer.mkdir()
    (organizer / "auth.json").write_bytes(b'{"auth":"fixture"}\n')
    root = tmp_path / "root"
    root.mkdir()
    monkeypatch.setattr(research_runtime_v4, "_organizer_codex_home", lambda: organizer)
    monkeypatch.setattr(research_runtime_v4, "_codex_binary", lambda: Path("/usr/bin/true"))
    monkeypatch.setattr(
        research_runtime_v4,
        "_codex_version",
        lambda _binary: research_runtime_v4._EXPECTED_CODEX_VERSION,
    )
    research_runtime_v4.ensure_private_model_runtime(root, "team-01")
    home = root / research_runtime_v4._PRIVATE_MODEL_RUNTIME_RELATIVE / "team-01/home"
    (home / ".agents").mkdir()
    with pytest.raises(
        research_runtime_v4.ResearchRuntimeError,
        match="HOME is not empty",
    ):
        research_runtime_v4.ensure_private_model_runtime(root, "team-01")


def test_frozen_model_smoke_semantics_bind_current_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = research_runtime_v4.validate_frozen_model_smoke(ROOT)
    assert receipt["environment_sha256"] == research_runtime_v4.model_environment_sha256(
        ROOT, "team-01"
    )
    original = (ROOT / activation_v4._PRETRIAL_SMOKE_RECEIPT_PATH).read_bytes()
    mutated = json.loads(original)
    mutated["prompt_catalog_empty"] = False
    payload = (json.dumps(mutated, sort_keys=True) + "\n").encode()
    monkeypatch.setattr(
        research_runtime_v4,
        "_stable_bytes",
        lambda path, **_kwargs: (
            payload
            if path == ROOT / activation_v4._PRETRIAL_SMOKE_RECEIPT_PATH
            else original
        ),
    )
    with pytest.raises(
        research_runtime_v4.ResearchRuntimeError,
        match="receipt authority differs",
    ):
        research_runtime_v4.validate_frozen_model_smoke(ROOT)


def test_pretrial_recovery_archives_old_then_new_authority_and_is_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _pretrial_recovery_fixture(tmp_path, monkeypatch)
    prepared = activation_v4.prepare_pretrial_recovery(tmp_path)
    assert prepared["status"] == "prepared-awaiting-v8-activation"
    assert not paths["activation"].exists()
    assert not paths["tests"].exists()
    assert paths["launch"].is_file()
    assert activation_v4.pretrial_recovery_pending(tmp_path) is True

    fresh = {
        "record_sha256": "2" * 64,
        "implementation_commit": "3" * 40,
    }
    new_payload = (json.dumps(fresh, sort_keys=True) + "\n").encode()
    paths["activation"].write_bytes(new_payload)
    monkeypatch.setattr(activation_v4, "validate", lambda _root, **_kwargs: fresh)
    completed = activation_v4.complete_pretrial_recovery(tmp_path)
    assert completed["status"] == "completed-before-first-trial"
    assert completed["old_activation"]["record_sha256"] == "1" * 64
    assert completed["new_activation"] == {
        "file_sha256": hashlib.sha256(new_payload).hexdigest(),
        "record_sha256": "2" * 64,
        "implementation_commit": "3" * 40,
        "launcher_version": "top40-v4-r2-research-runtime-v9",
    }
    assert not paths["launch"].exists()
    assert activation_v4.pretrial_recovery_pending(tmp_path) is False
    assert activation_v4.complete_pretrial_recovery(tmp_path) == completed


def test_fresh_restart_authority_is_an_explicit_alternative_to_incident_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = ROOT / activation_v4._FRESH_RESTART_AUTHORITY_PATH
    destination = tmp_path / activation_v4._FRESH_RESTART_AUTHORITY_PATH
    destination.parent.mkdir(parents=True)
    destination.write_bytes(source.read_bytes())
    assert activation_v4.pretrial_recovery_pending(tmp_path) is False
    authority = activation_v4.require_completed_pretrial_recovery(tmp_path)
    assert authority["feedback_disclosed"] is False
    assert authority["results_reused"] is False
    worker_incident = authority["worker_bootstrap_incident"]
    assert worker_incident["journal_records"] == 16
    assert worker_incident["trials_accepted"] == 8
    assert worker_incident["trials_failed"] == 8
    assert worker_incident["trials_succeeded"] == 0
    assert worker_incident["discovery_feedback_disclosed_to_team_01"] is True
    assert worker_incident["holdout_rows_disclosed_to_team"] is False
    assert worker_incident["results_reused"] is False
    zero_candidate = authority["zero_candidate_incident"]
    assert zero_candidate["batch_rejected_count"] == 15
    assert zero_candidate["selected_finalists"] == 0
    assert zero_candidate["winner"] is None
    assert zero_candidate["is_result_files"] == 0
    assert zero_candidate["feedback_disclosed"] is False
    assert zero_candidate["results_reused"] is False
    assert zero_candidate["research_provenance_reused"] is False
    assert zero_candidate["holdout_end_exclusive"] == "2026-08-01T00:00:00Z"
    minimum_finalist = authority["minimum_finalist_incident"]
    assert minimum_finalist["journal_records"] == 85
    assert minimum_finalist["accepted_trials"] == 38
    assert minimum_finalist["successful_trials"] == 36
    assert minimum_finalist["pending_trials"] == 1
    assert minimum_finalist["nominations_created"] == 0
    assert minimum_finalist["selection_created"] is False
    assert minimum_finalist["results_reused"] is False
    assert minimum_finalist["research_provenance_reused"] is False

    old_launch = tmp_path / activation_v4._PRETRIAL_OLD_LAUNCH_PATH
    old_launch.parent.mkdir(parents=True)
    legacy_payload = b"exact superseded launch fixture\n"
    old_launch.write_bytes(legacy_payload)
    monkeypatch.setattr(
        activation_v4,
        "_PRETRIAL_OLD_LAUNCH_SHA256",
        hashlib.sha256(legacy_payload).hexdigest(),
    )
    assert activation_v4.pretrial_recovery_pending(tmp_path) is True
    with pytest.raises(activation_v4.ActivationError, match="superseded v7 launch"):
        activation_v4.require_completed_pretrial_recovery(tmp_path)


def test_fresh_restart_accepts_only_the_exact_current_discovery_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = ROOT / activation_v4._FRESH_RESTART_AUTHORITY_PATH
    destination = tmp_path / activation_v4._FRESH_RESTART_AUTHORITY_PATH
    destination.parent.mkdir(parents=True)
    destination.write_bytes(source.read_bytes())
    launch = tmp_path / activation_v4._PRETRIAL_OLD_LAUNCH_PATH
    launch.parent.mkdir(parents=True)
    captured = b"current launch authority fixture\n"
    launch.write_bytes(captured)
    calls: list[tuple[Path, str, str, bytes]] = []

    def validate_current(
        root: str | Path, team_id: str, phase: str, payload: bytes
    ) -> dict[str, str]:
        calls.append((Path(root), team_id, phase, payload))
        return {"path": str(launch), "sha256": hashlib.sha256(payload).hexdigest()}

    monkeypatch.setattr(
        research_runtime_v4, "validate_launch_authority_payload", validate_current
    )
    assert activation_v4.pretrial_recovery_pending(tmp_path) is False
    assert activation_v4.require_completed_pretrial_recovery(tmp_path)["results_reused"] is False
    assert calls == [
        (tmp_path, "team-01", "discovery", captured),
        (tmp_path, "team-01", "discovery", captured),
    ]

    def reject_current(
        _root: str | Path, _team_id: str, _phase: str, _payload: bytes
    ) -> None:
        raise research_runtime_v4.ResearchRuntimeError("invalid current fixture")

    monkeypatch.setattr(
        research_runtime_v4, "validate_launch_authority_payload", reject_current
    )
    assert activation_v4.pretrial_recovery_pending(tmp_path) is True
    with pytest.raises(activation_v4.ActivationError, match="launch authority is not current"):
        activation_v4.require_completed_pretrial_recovery(tmp_path)


def test_launch_authority_requires_exact_canonical_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(research_runtime_v4, "profile_sha256", lambda _root, _team: "1" * 64)
    monkeypatch.setattr(research_runtime_v4, "_team_kit_sha256", lambda _root: "2" * 64)
    recorded = research_runtime_v4._record_launch_authority(
        tmp_path, "team-01", "discovery"
    )
    launch = tmp_path / recorded["path"]
    canonical = launch.read_bytes()
    assert research_runtime_v4.validate_launch_authority_payload(
        tmp_path, "team-01", "discovery", canonical
    ) == recorded

    semantic = json.loads(canonical)
    assert semantic["model"] == research_runtime_v4._MODEL_NAME
    assert semantic["environment_sha256"] == research_runtime_v4.model_environment_sha256(
        tmp_path, "team-01"
    )
    assert semantic["prompt_sha256"] == hashlib.sha256(
        research_runtime_v4.team_phase_prompt("team-01", "discovery").encode()
    ).hexdigest()
    assert semantic["command_sha256"] == research_runtime_v4._model_command_authority(
        tmp_path, "team-01", "discovery"
    )["command_sha256"]
    noncanonical = json.dumps(semantic, separators=(",", ":")).encode() + b"\n"
    duplicate = canonical.replace(b"{\n", b'{\n  "schema_version": 1,\n', 1)
    for payload in (noncanonical, duplicate):
        with pytest.raises(
            research_runtime_v4.ResearchRuntimeError,
            match="launch authority differs",
        ):
            research_runtime_v4.validate_launch_authority_payload(
                tmp_path, "team-01", "discovery", payload
            )


def test_fresh_restart_validates_the_same_stable_launch_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(research_runtime_v4, "profile_sha256", lambda _root, _team: "1" * 64)
    monkeypatch.setattr(research_runtime_v4, "_team_kit_sha256", lambda _root: "2" * 64)
    recorded = research_runtime_v4._record_launch_authority(
        tmp_path, "team-01", "discovery"
    )
    launch = tmp_path / recorded["path"]
    canonical = launch.read_bytes()
    validate_payload = research_runtime_v4.validate_launch_authority_payload
    seen: list[bytes] = []

    def substitute_after_capture(
        root: str | Path, team_id: str, phase: str, payload: bytes
    ) -> dict[str, str]:
        seen.append(payload)
        launch.write_bytes(b"substituted after stable capture\n")
        return dict(validate_payload(root, team_id, phase, payload))

    monkeypatch.setattr(
        research_runtime_v4,
        "validate_launch_authority_payload",
        substitute_after_capture,
    )
    activation_v4._validate_fresh_restart_launch(tmp_path)
    assert seen == [canonical]
    assert launch.read_bytes() != canonical


def test_fresh_restart_seed_state_binds_exact_clean_genesis(tmp_path: Path) -> None:
    root = _fresh_restart_fixture(tmp_path)
    state = activation_v4._fresh_restart_seed_state(
        root, activation_tests_present=False
    )
    assert state == {
        "mode": "score-blind-fresh-restart",
        "authority_sha256": activation_v4._FRESH_RESTART_AUTHORITY_SHA256,
        "journal_sha256": hashlib.sha256(b"").hexdigest(),
        "lane_count": 15,
        "surface_file_count": 94,
        "surface_head_sha256": state["surface_head_sha256"],
    }
    scope_entries = _fresh_restart_scope_entries(root)
    activation_v4._validate_fresh_restart_binding(root, state, scope_entries)
    changed = dict(state)
    changed["lane_count"] = 14
    with pytest.raises(activation_v4.ActivationError, match="binding changed"):
        activation_v4._validate_fresh_restart_binding(root, changed, scope_entries)
    changed = dict(state)
    changed["surface_head_sha256"] = "0" * 64
    with pytest.raises(activation_v4.ActivationError, match="binding changed"):
        activation_v4._validate_fresh_restart_binding(root, changed, scope_entries)


@pytest.mark.parametrize(
    "relative",
    (
        "tournament/top40-v4-r2/teams/team-01/candidates/residue.py",
        "tournament/top40-v4-r2/teams/team-01/outbox/batch-1.json",
        "tournament/top40-v4-r2/teams/team-01/feedback/batch-1.json",
        "tournament/top40-v4-r2/teams/team-01/work/scratch.txt",
        "tournament/top40-v4-r2/research-sessions/launches/team-02/discovery.json",
        "tournament/top40-v4-r2/nomination-registry.json",
        "tournament/top40-v4-r2/selection-freeze.json",
        "tournament/top40-v4-r2/private/historical-oos/release.json",
        "reports-top40-v4-r2/is/team-01/summary.json",
        "reports-top40-v4-r2/source-archives/team-01/archive.json",
    ),
)
def test_fresh_restart_seed_state_rejects_runtime_residue(
    tmp_path: Path, relative: str
) -> None:
    root = _fresh_restart_fixture(tmp_path)
    residue = root / relative
    residue.parent.mkdir(parents=True, exist_ok=True)
    residue.write_bytes(b"residue\n")
    with pytest.raises(activation_v4.ActivationError):
        activation_v4._fresh_restart_seed_state(
            root, activation_tests_present=False
        )


def test_fresh_restart_seed_state_rejects_nonempty_journal_and_linked_seed(
    tmp_path: Path,
) -> None:
    root = _fresh_restart_fixture(tmp_path)
    journal = root / TOP40_V4_R2_LAYOUT.journal_path
    journal.write_bytes(b"historical record\n")
    with pytest.raises(activation_v4.ActivationError, match="byte-empty"):
        activation_v4._fresh_restart_seed_state(
            root, activation_tests_present=False
        )

    root = _fresh_restart_fixture(tmp_path / "linked")
    marker = (
        root / TOP40_V4_R2_LAYOUT.team_root("team-01") / "feedback" / ".keep"
    )
    external = root / "external-alias"
    os.link(marker, external)
    with pytest.raises(activation_v4.ActivationError, match="unsafe"):
        activation_v4._fresh_restart_seed_state(
            root, activation_tests_present=False
        )


def test_fresh_restart_seed_state_binds_activation_test_transition(
    tmp_path: Path,
) -> None:
    root = _fresh_restart_fixture(tmp_path)
    initial = activation_v4._fresh_restart_seed_state(
        root, activation_tests_present=False
    )
    tests = root / activation_v4.TEST_OUTPUT_PATH
    tests.write_bytes(b"focused tests passed\n")
    assert (
        activation_v4._fresh_restart_seed_state(
            root, activation_tests_present=True
        )
        == initial
    )
    with pytest.raises(activation_v4.ActivationError):
        activation_v4._fresh_restart_seed_state(
            root, activation_tests_present=False
        )


def test_fresh_restart_activation_freezes_seed_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fresh_restart_fixture(tmp_path)
    _patch_fresh_activation(root, monkeypatch, [(b"passed\n", 0)])
    monkeypatch.setattr(isolation_v4, "audit_surface", lambda _root: {})
    record = orchestrator_v4.activate(root)
    assert record["fresh_restart"]["mode"] == "score-blind-fresh-restart"
    assert record["fresh_restart"]["surface_file_count"] == 94
    assert (root / TOP40_V4_R2_LAYOUT.activation_freeze_path).is_file()
    assert (
        root / TOP40_V4_R2_LAYOUT.result_lock_path
    ).read_bytes() == f"pid={os.getpid()}\n".encode()


def test_canonical_activation_never_repairs_a_preactivation_journal(
    tmp_path: Path,
) -> None:
    root = _fresh_restart_fixture(tmp_path / "fragment")
    journal = root / TOP40_V4_R2_LAYOUT.journal_path
    fragment = b'{"interrupted":"must remain evidence"}'
    journal.write_bytes(fragment)
    journal.chmod(0o600)
    with pytest.raises(journal_v4.JournalError, match="byte-empty"):
        orchestrator_v4.activate(root)
    assert journal.read_bytes() == fragment
    assert not (root / TOP40_V4_R2_LAYOUT.activation_freeze_path).exists()
    assert not (root / activation_v4.TEST_OUTPUT_PATH).exists()

    root = _fresh_restart_fixture(tmp_path / "hardlink")
    journal = root / TOP40_V4_R2_LAYOUT.journal_path
    journal.unlink()
    external = root / "external-authority"
    external.write_bytes(b"external bytes must never be truncated")
    external.chmod(0o600)
    os.link(external, journal)
    with pytest.raises(journal_v4.JournalError, match="byte-empty"):
        orchestrator_v4.activate(root)
    assert external.read_bytes() == b"external bytes must never be truncated"
    assert journal.read_bytes() == external.read_bytes()
    assert not (root / TOP40_V4_R2_LAYOUT.activation_freeze_path).exists()
    assert not (root / activation_v4.TEST_OUTPUT_PATH).exists()


def test_run_team_preactivation_never_recovers_the_journal(
    tmp_path: Path,
) -> None:
    root = _fresh_restart_fixture(tmp_path)
    journal = root / TOP40_V4_R2_LAYOUT.journal_path
    fragment = b'{"preactivation":"fragment remains immutable"}'
    journal.write_bytes(fragment)
    journal.chmod(0o600)
    broker = _broker_module()
    with pytest.raises(activation_v4.ActivationError):
        broker.run_team(root, "team-01")
    assert journal.read_bytes() == fragment

    completed = subprocess.run(
        (
            sys.executable,
            "scripts/top40_v4_r2_team_broker.py",
            "--root",
            str(root),
            "run-team",
            "team-01",
        ),
        cwd=ROOT,
        env=_r2_environment(),
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode != 0
    assert completed.stderr
    assert journal.read_bytes() == fragment


def test_run_team_activation_gate_precedes_the_terminal_journal_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fresh_restart_fixture(tmp_path)
    broker = _broker_module()
    reads: list[Path] = []

    def refuse(_root: Path) -> None:
        raise activation_v4.ActivationError("synthetic activation refusal")

    monkeypatch.setattr(broker.activation_v4, "validate", refuse)
    monkeypatch.setattr(broker.journal_v4, "read", lambda path: reads.append(Path(path)))
    with pytest.raises(activation_v4.ActivationError, match="synthetic activation refusal"):
        broker.run_team.__wrapped__(root, "team-01")
    assert reads == []


def test_preactivation_status_and_validate_never_recover_the_journal(
    tmp_path: Path,
) -> None:
    root = _fresh_restart_fixture(tmp_path)
    journal = root / TOP40_V4_R2_LAYOUT.journal_path
    fragment = b'{"read-only":"commands preserve this fragment"}'
    journal.write_bytes(fragment)
    journal.chmod(0o600)

    with pytest.raises(journal_v4.JournalError, match="byte-empty"):
        orchestrator_v4.status(root)
    assert journal.read_bytes() == fragment
    with pytest.raises(journal_v4.JournalError, match="byte-empty"):
        orchestrator_v4.validate(root, require_activation=False)
    assert journal.read_bytes() == fragment

    for command in (("status",), ("validate", "--pre-activation")):
        completed = subprocess.run(
            (
                sys.executable,
                "scripts/top40_v4_r2_tournament.py",
                "--root",
                str(root),
                *command,
            ),
            cwd=ROOT,
            env=_r2_environment(),
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert completed.returncode != 0
        assert "byte-empty" in completed.stderr
        assert journal.read_bytes() == fragment


@pytest.mark.parametrize("operation", ("read", "append"))
def test_runtime_journal_rejects_hardlinks_without_mutation(
    tmp_path: Path, operation: str
) -> None:
    journal = tmp_path / "research-journal.jsonl"
    external = tmp_path / "external-authority"
    original = b'{"unterminated":"external evidence"}' if operation == "read" else b""
    external.write_bytes(original)
    external.chmod(0o600)
    os.link(external, journal)
    with pytest.raises(journal_v4.JournalError, match="private regular"):
        if operation == "read":
            journal_v4.read(journal)
        else:
            journal_v4.append(journal, "is_accepted", {})
    assert external.read_bytes() == original
    assert journal.read_bytes() == original


@pytest.mark.parametrize("operation", ("read", "append"))
def test_runtime_journal_rejects_path_substitution_before_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    journal = tmp_path / "research-journal.jsonl"
    displaced = tmp_path / "opened-journal"
    original = b'{"unterminated":"must remain"}' if operation == "read" else b""
    replacement = b"replacement pathname evidence"
    journal.write_bytes(original)
    journal.chmod(0o600)
    real_stat = os.stat
    swapped = False

    def substituting_stat(
        path: object, *args: object, **kwargs: object
    ) -> os.stat_result:
        nonlocal swapped
        if path == journal.name and kwargs.get("dir_fd") is not None and not swapped:
            swapped = True
            journal.rename(displaced)
            journal.write_bytes(replacement)
            journal.chmod(0o600)
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr(journal_v4.os, "stat", substituting_stat)
    with pytest.raises(journal_v4.JournalError, match="authority changed"):
        if operation == "read":
            journal_v4.read(journal)
        else:
            journal_v4.append(journal, "is_accepted", {})
    assert swapped is True
    assert displaced.read_bytes() == original
    assert journal.read_bytes() == replacement


def test_r2_append_never_recreates_a_missing_runtime_journal(tmp_path: Path) -> None:
    journal = tmp_path / "research-journal.jsonl"
    with pytest.raises(journal_v4.JournalError, match="missing or unsafe"):
        journal_v4.append(journal, "is_accepted", {})
    assert not os.path.lexists(journal)


def test_fresh_restart_activation_rejects_dirty_root_before_freeze(
    tmp_path: Path,
) -> None:
    root = _fresh_restart_fixture(tmp_path)
    residue = root / TOP40_V4_R2_LAYOUT.team_root("team-04") / "outbox" / "batch.json"
    residue.write_bytes(b"residue\n")
    with pytest.raises(activation_v4.ActivationError):
        activation_v4.activate(root)
    assert not (root / TOP40_V4_R2_LAYOUT.activation_freeze_path).exists()
    assert not (root / activation_v4.TEST_OUTPUT_PATH).exists()


def test_fresh_restart_activation_reruns_after_test_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fresh_restart_fixture(tmp_path)
    _patch_fresh_activation(
        root,
        monkeypatch,
        [(b"first run failed\n", 1), (b"second run passed\n", 0)],
    )
    with pytest.raises(activation_v4.ActivationError, match="focused activation tests failed"):
        activation_v4.activate(root)
    assert not (root / TOP40_V4_R2_LAYOUT.activation_freeze_path).exists()
    assert (root / activation_v4.TEST_OUTPUT_PATH).read_bytes() == b"first run failed\n"

    record = activation_v4.activate(root)
    assert record["tests"]["output_sha256"] == hashlib.sha256(
        b"second run passed\n"
    ).hexdigest()
    assert (root / activation_v4.TEST_OUTPUT_PATH).read_bytes() == b"second run passed\n"
    assert (root / TOP40_V4_R2_LAYOUT.activation_freeze_path).is_file()


def test_result_lock_rejects_links_before_mutating_their_target(tmp_path: Path) -> None:
    lock = tmp_path / TOP40_V4_R2_LAYOUT.result_lock_path
    lock.parent.mkdir(parents=True)
    target = tmp_path / "outside-authority"
    target.write_bytes(b"must remain unchanged\n")
    os.link(target, lock)
    with pytest.raises(orchestrator_v4.OrchestratorError, match="private regular file"):
        with orchestrator_v4._result_lock(tmp_path):
            pytest.fail("unsafe hard-linked lock was acquired")
    assert target.read_bytes() == b"must remain unchanged\n"

    lock.unlink()
    lock.symlink_to(target)
    with pytest.raises(orchestrator_v4.OrchestratorError):
        with orchestrator_v4._result_lock(tmp_path):
            pytest.fail("unsafe symlinked lock was acquired")
    assert target.read_bytes() == b"must remain unchanged\n"


def test_pretrial_recovery_resumes_after_each_authority_move(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _pretrial_recovery_fixture(tmp_path, monkeypatch)
    stage = tmp_path / activation_v4._PRETRIAL_INCIDENT_STAGE
    stage.mkdir(parents=True)
    os.replace(paths["activation"], stage / "superseded-activation-freeze.json")
    activation_v4.prepare_pretrial_recovery(tmp_path)
    assert not paths["tests"].exists()

    fresh = {
        "record_sha256": "2" * 64,
        "implementation_commit": "3" * 40,
    }
    new_payload = (json.dumps(fresh, sort_keys=True) + "\n").encode()
    paths["activation"].write_bytes(new_payload)
    monkeypatch.setattr(activation_v4, "validate", lambda _root, **_kwargs: fresh)
    archived_launch = stage / "superseded-team-01-discovery-v7.json"
    os.replace(paths["launch"], archived_launch)
    archived_launch_sha256 = hashlib.sha256(archived_launch.read_bytes()).hexdigest()
    completed = activation_v4.complete_pretrial_recovery(tmp_path)
    assert completed["old_launch_authority"]["sha256"] == archived_launch_sha256


def test_pretrial_prepare_resumes_same_inode_activation_duplicate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _pretrial_recovery_fixture(tmp_path, monkeypatch)
    stage = tmp_path / activation_v4._PRETRIAL_INCIDENT_STAGE
    stage.mkdir(parents=True)
    archived = stage / "superseded-activation-freeze.json"
    os.link(paths["activation"], archived)
    assert archived.stat().st_nlink == 2
    activation_v4.prepare_pretrial_recovery(tmp_path)
    assert not paths["activation"].exists()
    assert archived.stat().st_nlink == 1


def test_pretrial_complete_resumes_same_inode_launch_duplicate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _pretrial_recovery_fixture(tmp_path, monkeypatch)
    activation_v4.prepare_pretrial_recovery(tmp_path)
    fresh = {
        "record_sha256": "2" * 64,
        "implementation_commit": "3" * 40,
    }
    paths["activation"].write_text(json.dumps(fresh, sort_keys=True) + "\n")
    monkeypatch.setattr(activation_v4, "validate", lambda _root, **_kwargs: fresh)
    stage = tmp_path / activation_v4._PRETRIAL_INCIDENT_STAGE
    archived = stage / "superseded-team-01-discovery-v7.json"
    os.link(paths["launch"], archived)
    assert paths["launch"].stat().st_nlink == archived.stat().st_nlink == 2
    completed = activation_v4.complete_pretrial_recovery(tmp_path)
    assert completed["status"] == "completed-before-first-trial"
    final_launch = (
        tmp_path
        / activation_v4._PRETRIAL_INCIDENT_FINAL
        / "superseded-team-01-discovery-v7.json"
    )
    assert not paths["launch"].exists()
    assert final_launch.stat().st_nlink == 1


@pytest.mark.parametrize("authority", ["activation", "tests", "launch"])
def test_pretrial_prepare_rejects_unrelated_staged_hardlink_before_any_move(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, authority: str
) -> None:
    paths = _pretrial_recovery_fixture(tmp_path, monkeypatch)
    stage = tmp_path / activation_v4._PRETRIAL_INCIDENT_STAGE
    stage.mkdir(parents=True)
    names = {
        "activation": "superseded-activation-freeze.json",
        "tests": "superseded-activation-tests.out",
        "launch": "superseded-team-01-discovery-v7.json",
    }
    unrelated = tmp_path / f"unrelated-{authority}"
    unrelated.write_bytes(paths[authority].read_bytes())
    os.link(unrelated, stage / names[authority])
    before = {name: path.read_bytes() for name, path in paths.items() if name != "journal"}

    with pytest.raises(activation_v4.ActivationError, match="unsafe duplicate"):
        activation_v4.prepare_pretrial_recovery(tmp_path)

    assert all(paths[name].read_bytes() == payload for name, payload in before.items())


@pytest.mark.parametrize("duplicate_launch", [False, True])
def test_canonical_pretrial_recovery_resumes_after_fresh_activation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    duplicate_launch: bool,
) -> None:
    paths = _pretrial_recovery_fixture(tmp_path, monkeypatch)
    activation_v4.prepare_pretrial_recovery(tmp_path)
    fresh = {
        "record_sha256": "2" * 64,
        "implementation_commit": "3" * 40,
    }
    new_tests = b"new activation tests passed\n"
    paths["tests"].write_bytes(new_tests)
    fresh["tests"] = {
        "output_path": activation_v4.TEST_OUTPUT_PATH,
        "exit_code": 0,
        "output_size": len(new_tests),
        "output_sha256": hashlib.sha256(new_tests).hexdigest(),
    }
    paths["activation"].write_text(json.dumps(fresh, sort_keys=True) + "\n")
    monkeypatch.setattr(activation_v4, "validate", lambda _root, **_kwargs: fresh)
    monkeypatch.setattr(
        orchestrator_v4,
        "activate",
        lambda _root: pytest.fail("valid fresh activation was replaced"),
    )
    if duplicate_launch:
        stage = tmp_path / activation_v4._PRETRIAL_INCIDENT_STAGE
        os.link(
            paths["launch"], stage / "superseded-team-01-discovery-v7.json"
        )

    result = orchestrator_v4.recover_pretrial(tmp_path)

    assert result["ok"] is True
    assert result["incident"]["status"] == "completed-before-first-trial"
    assert not paths["launch"].exists()


def test_canonical_pretrial_recovery_reruns_after_successor_test_output_crash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _pretrial_recovery_fixture(tmp_path, monkeypatch)
    activation_v4.prepare_pretrial_recovery(tmp_path)
    paths["tests"].write_bytes(b"interrupted successor activation tests\n")
    successful_tests = b"rerun successor activation tests passed\n"
    fresh = {
        "record_sha256": "2" * 64,
        "implementation_commit": "3" * 40,
        "tests": {
            "output_path": activation_v4.TEST_OUTPUT_PATH,
            "exit_code": 0,
            "output_size": len(successful_tests),
            "output_sha256": hashlib.sha256(successful_tests).hexdigest(),
        },
    }

    def validate(root: Path, **_kwargs: object) -> dict[str, object]:
        activation = root / TOP40_V4_R2_LAYOUT.activation_freeze_path
        if not activation.exists():
            raise activation_v4.ActivationError("V4 is not activated")
        return fresh

    def activate(root: Path) -> dict[str, object]:
        paths["tests"].write_bytes(successful_tests)
        paths["activation"].write_text(json.dumps(fresh, sort_keys=True) + "\n")
        return fresh

    monkeypatch.setattr(activation_v4, "validate", validate)
    monkeypatch.setattr(orchestrator_v4, "activate", activate)

    result = orchestrator_v4.recover_pretrial(tmp_path)

    assert result["ok"] is True
    assert paths["tests"].read_bytes() == successful_tests
    assert result["incident"]["status"] == "completed-before-first-trial"


def test_pretrial_prepare_rejects_single_staged_external_hardlink_before_move(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _pretrial_recovery_fixture(tmp_path, monkeypatch)
    stage = tmp_path / activation_v4._PRETRIAL_INCIDENT_STAGE
    stage.mkdir(parents=True)
    staged_tests = stage / "superseded-activation-tests.out"
    external = tmp_path / "external-tests-alias"
    external.write_bytes(paths["tests"].read_bytes())
    os.link(external, staged_tests)
    paths["tests"].unlink()
    old_activation = paths["activation"].read_bytes()

    with pytest.raises(activation_v4.ActivationError, match="unsafe duplicate"):
        activation_v4.prepare_pretrial_recovery(tmp_path)

    assert paths["activation"].read_bytes() == old_activation
    assert staged_tests.stat().st_ino == external.stat().st_ino


def test_pretrial_authority_move_resumes_identical_duplicate_and_rejects_difference(
    tmp_path: Path,
) -> None:
    source = tmp_path / "active/authority.json"
    destination = tmp_path / "archive/authority.json"
    source.parent.mkdir(parents=True)
    destination.parent.mkdir(parents=True)
    payload = b"exact authority\n"
    expected = hashlib.sha256(payload).hexdigest()
    source.write_bytes(payload)
    destination.write_bytes(payload)
    activation_v4._move_pretrial_file(
        tmp_path, "active/authority.json", destination, expected
    )
    assert not source.exists()
    assert destination.read_bytes() == payload

    destination.unlink()
    source.write_bytes(payload)
    os.link(source, destination)
    assert source.stat().st_ino == destination.stat().st_ino
    assert source.stat().st_nlink == 2
    activation_v4._move_pretrial_file(
        tmp_path, "active/authority.json", destination, expected
    )
    assert not source.exists()
    assert destination.stat().st_nlink == 1

    source.write_bytes(payload)
    destination.write_bytes(b"different authority\n")
    with pytest.raises(activation_v4.ActivationError, match="unsafe duplicate"):
        activation_v4._move_pretrial_file(
            tmp_path, "active/authority.json", destination, expected
        )
    assert source.read_bytes() == payload


def test_pretrial_authority_move_rejects_unrelated_hardlink_before_source_mutation(
    tmp_path: Path,
) -> None:
    source = tmp_path / "active/authority.json"
    destination = tmp_path / "archive/authority.json"
    unrelated = tmp_path / "third/authority.json"
    for parent in (source.parent, destination.parent, unrelated.parent):
        parent.mkdir(parents=True)
    payload = b"exact authority\n"
    source.write_bytes(payload)
    unrelated.write_bytes(payload)
    os.link(unrelated, destination)
    assert source.stat().st_nlink == 1
    assert destination.stat().st_nlink == 2
    with pytest.raises(activation_v4.ActivationError, match="unsafe duplicate"):
        activation_v4._move_pretrial_file(
            tmp_path,
            "active/authority.json",
            destination,
            hashlib.sha256(payload).hexdigest(),
        )
    assert source.read_bytes() == payload
    assert destination.stat().st_ino == unrelated.stat().st_ino


def test_pretrial_authority_move_persists_destination_before_source_removal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "active/authority.json"
    destination = tmp_path / "archive/authority.json"
    source.parent.mkdir(parents=True)
    destination.parent.mkdir(parents=True)
    payload = b"exact authority\n"
    source.write_bytes(payload)
    events: list[tuple[str, Path]] = []
    original_file = activation_v4._fsync_regular_file
    original_directory = activation_v4._fsync_directory

    def fsync_file(path: Path) -> None:
        events.append(("file", path))
        original_file(path)

    def fsync_directory(path: Path) -> None:
        events.append(("directory", path))
        original_directory(path)

    monkeypatch.setattr(activation_v4, "_fsync_regular_file", fsync_file)
    monkeypatch.setattr(activation_v4, "_fsync_directory", fsync_directory)
    activation_v4._move_pretrial_file(
        tmp_path,
        "active/authority.json",
        destination,
        hashlib.sha256(payload).hexdigest(),
    )
    first_file = events.index(("file", destination))
    destination_directory = events.index(("directory", destination.parent))
    source_directory = events.index(("directory", source.parent))
    assert first_file < destination_directory < source_directory


@pytest.mark.parametrize(
    "mutation",
    [
        "journal",
        "candidate",
        "research-receipt",
        "missing-launch",
        "old-tests",
        "old-activation",
    ],
)
def test_pretrial_recovery_rejects_nonempty_or_mismatched_state_without_moving_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    paths = _pretrial_recovery_fixture(tmp_path, monkeypatch)
    if mutation == "journal":
        paths["journal"].write_bytes(b"not empty\n")
    elif mutation == "candidate":
        candidate = (
            tmp_path
            / TOP40_V4_R2_LAYOUT.team_root("team-01")
            / "candidates/created.py"
        )
        candidate.write_text("created = True\n")
    elif mutation == "research-receipt":
        receipt = (
            tmp_path
            / TOP40_V4_R2_LAYOUT.tournament_root
            / "research-sessions/receipts/team-01/unexpected.json"
        )
        receipt.parent.mkdir(parents=True)
        receipt.write_text("{}\n")
    elif mutation == "missing-launch":
        paths["launch"].unlink()
    elif mutation == "old-tests":
        paths["tests"].write_bytes(b"different activation tests\n")
    else:
        paths["activation"].write_bytes(b"different old activation\n")
    with pytest.raises(activation_v4.ActivationError):
        activation_v4.prepare_pretrial_recovery(tmp_path)
    assert paths["activation"].exists()
    assert paths["tests"].exists()
    assert paths["launch"].exists() is (mutation != "missing-launch")


def test_pretrial_recovery_validates_new_activation_before_moving_stale_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _pretrial_recovery_fixture(tmp_path, monkeypatch)
    activation_v4.prepare_pretrial_recovery(tmp_path)
    paths["activation"].write_bytes(b"invalid new activation\n")

    def reject(_root: Path) -> None:
        raise activation_v4.ActivationError("new activation is invalid")

    monkeypatch.setattr(activation_v4, "validate", reject)
    with pytest.raises(activation_v4.ActivationError, match="new activation is invalid"):
        activation_v4.complete_pretrial_recovery(tmp_path)
    assert paths["launch"].is_file()
    assert activation_v4.pretrial_recovery_pending(tmp_path) is True


@pytest.mark.parametrize(
    "mutation",
    [
        "manifest",
        "self-consistent-manifest",
        "manifest-hardlink",
        "prepared-hardlink",
        "archive",
        "current-activation",
    ],
)
def test_completed_pretrial_authority_is_required_and_detects_corruption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    paths = _pretrial_recovery_fixture(tmp_path, monkeypatch)
    activation_v4.prepare_pretrial_recovery(tmp_path)
    fresh = {
        "record_sha256": "2" * 64,
        "implementation_commit": "3" * 40,
    }
    paths["activation"].write_text(json.dumps(fresh, sort_keys=True) + "\n")
    monkeypatch.setattr(activation_v4, "validate", lambda _root, **_kwargs: fresh)
    activation_v4.complete_pretrial_recovery(tmp_path)
    final = tmp_path / activation_v4._PRETRIAL_INCIDENT_FINAL
    if mutation == "manifest":
        (final / "incident.json").write_text("{}\n")
    elif mutation == "self-consistent-manifest":
        incident_path = final / "incident.json"
        incident = json.loads(incident_path.read_text())
        incident["reason"] = "tampered but self-consistent"
        incident["new_activation"]["record_sha256"] = "4" * 64
        incident["new_activation"]["implementation_commit"] = "5" * 40
        incident.pop("record_sha256")
        incident["record_sha256"] = hashlib.sha256(
            activation_v4._canonical(incident)
        ).hexdigest()
        incident_path.write_text(json.dumps(incident, indent=2, sort_keys=True) + "\n")
    elif mutation == "manifest-hardlink":
        os.link(final / "incident.json", tmp_path / "incident-alias.json")
    elif mutation == "prepared-hardlink":
        os.link(final / "prepared.json", tmp_path / "prepared-alias.json")
    elif mutation == "archive":
        (final / "superseded-team-01-discovery-v7.json").write_text("changed\n")
    else:
        paths["activation"].write_text("changed new activation\n")
    with pytest.raises(activation_v4.ActivationError):
        activation_v4.require_completed_pretrial_recovery(tmp_path)


def test_journal_binds_research_session_to_exact_source_authority() -> None:
    source = "a" * 64
    payload = {
        "team_id": "team-01",
        "run_id": "team01-is-01-source",
        "trial_number": 1,
        "candidate_id": "candidate",
        "purpose": "baseline",
        "metadata": {},
        "authority": {"source_bundle_sha256": source},
        "research_session": {
            "path": f"tournament/top40-v4-r2/research-sessions/team-01/{source}.json",
            "sha256": "b" * 64,
            "source_bundle_sha256": source,
        },
        "output_path": "reports-top40-v4-r2/is/team-01/run",
    }
    journal_v4._validate_payload("is_accepted", payload)
    payload["research_session"]["source_bundle_sha256"] = "c" * 64
    with pytest.raises(journal_v4.JournalError, match="differs from accepted source"):
        journal_v4._validate_payload("is_accepted", payload)


def test_static_source_review_rejects_hidden_encoded_payload() -> None:
    source = ("PAYLOAD = '" + ("A" * 300) + "'\n").encode()
    item = runner_v4.source_archive_v4.SourceFile(
        path="strategy.py",
        size=len(source),
        sha256=hashlib.sha256(source).hexdigest(),
        content=source,
    )
    executable, findings = research_runtime_v4._static_source_findings((item,))
    assert executable == ["strategy.py"]
    assert any("encoded-looking" in finding for finding in findings)


def test_static_source_review_rejects_split_ordinal_prefit_payload() -> None:
    chunks = ["L§S§" * 225 for _ in range(6)]
    source = "\n".join(
        f"CHUNK_{number} = {chunk!r}" for number, chunk in enumerate(chunks)
    ).encode()
    item = runner_v4.source_archive_v4.SourceFile(
        path="strategy.py",
        size=len(source),
        sha256=hashlib.sha256(source).hexdigest(),
        content=source,
    )
    _executable, findings = research_runtime_v4._static_source_findings((item,))
    assert any("aggregate string payload" in finding for finding in findings)


def test_static_semantic_subset_rejects_compact_ordinal_state() -> None:
    source = b"""
PACKED_A = 'L' * 63
PACKED_B = 'S' * 63
class Strategy:
    def target_weights(self, context, *, seed):
        self.step = self.step + 1
        token = PACKED_A[self.step % 63]
        return {symbol: (0.01 if token == 'L' else -0.01) for symbol in context.eligible_symbols}
def build_strategy():
    return Strategy()
"""
    item = runner_v4.source_archive_v4.SourceFile(
        path="strategy.py",
        size=len(source),
        sha256=hashlib.sha256(source).hexdigest(),
        content=source,
    )
    _executable, findings = research_runtime_v4._static_source_findings((item,))
    assert any("stateless" in finding for finding in findings)
    assert any("ordinal/packing" in finding for finding in findings)
    assert any("packed literal construction" in finding for finding in findings)


def test_static_semantic_subset_accepts_transparent_stateless_strategy() -> None:
    source = b"""
class Strategy:
    def target_weights(self, context, *, seed):
        weights = {}
        for symbol in context.eligible_symbols:
            frame = context.bars[symbol]
            if frame.empty:
                continue
            if float(frame['close'].iloc[-1]) > 0:
                weights[symbol] = 0.01
        return weights
def build_strategy():
    return Strategy()
"""
    item = runner_v4.source_archive_v4.SourceFile(
        path="strategy.py",
        size=len(source),
        sha256=hashlib.sha256(source).hexdigest(),
        content=source,
    )
    executable, findings = research_runtime_v4._static_source_findings((item,))
    assert executable == ["strategy.py"]
    assert findings == []


def test_team_kit_strategy_template_passes_the_exact_static_checker() -> None:
    payload = (
        ROOT / "tournament/top40-v4-r2/team-kit/templates/strategy.py"
    ).read_bytes()
    item = runner_v4.source_archive_v4.SourceFile(
        path="strategy.py",
        size=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        content=payload,
    )
    executable, findings = research_runtime_v4._static_source_findings((item,))
    assert executable == ["strategy.py"]
    assert findings == []
    checker = (
        ROOT / "tournament/top40-v4-r2/team-kit/ADMISSION-CHECKER.md"
    ).read_text(encoding="utf-8")
    for rejected_call in ("Series", "get", "range", "append", "to_dict"):
        assert rejected_call in checker
    allowlist = json.loads(
        (
            ROOT
            / "tournament/top40-v4-r2/team-kit/admission-call-allowlist.json"
        ).read_text(encoding="utf-8")
    )
    assert set(allowlist) == {
        "allowed_attribute_calls",
        "allowed_name_calls",
        "schema_version",
    }
    assert allowlist["schema_version"] == 1
    assert set(allowlist["allowed_name_calls"]) == set(
        research_runtime_v4._TARGET_ALLOWED_NAME_CALLS
    )
    assert set(allowlist["allowed_attribute_calls"]) == set(
        research_runtime_v4._TARGET_ALLOWED_ATTRIBUTE_CALLS
    )


def test_launcher_repairs_invalid_batch_before_recording_any_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    team = tmp_path / TOP40_V4_R2_LAYOUT.team_root("team-01")
    for directory in ("candidates", "feedback", "outbox", "work"):
        (team / directory).mkdir(parents=True, exist_ok=True)
    outbox = team / "outbox/batch-1.json"
    calls: list[int] = []
    recorded: list[tuple[str, ...]] = []

    monkeypatch.setattr(activation_v4, "validate", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        activation_v4, "require_completed_pretrial_recovery", lambda *_args: {}
    )
    monkeypatch.setattr(
        research_runtime_v4, "validate_frozen_model_smoke", lambda *_args: {}
    )
    monkeypatch.setattr(
        research_runtime_v4, "_validate_runtime_launch_lifecycle", lambda *_args: None
    )
    monkeypatch.setattr(
        research_runtime_v4.isolation_v4, "audit_team_surface", lambda *_args: {}
    )
    monkeypatch.setattr(
        research_runtime_v4, "run_profile_probes", lambda *_args: {"passed": True}
    )
    monkeypatch.setattr(
        research_runtime_v4,
        "_record_launch_authority",
        lambda *_args: {"path": "launch.json", "sha256": "1" * 64},
    )
    monkeypatch.setattr(research_runtime_v4, "_codex_exec_command", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(research_runtime_v4, "_private_model_environment", lambda *_args: {})
    monkeypatch.setattr(research_runtime_v4, "ensure_private_model_runtime", lambda *_args: {})
    monkeypatch.setattr(
        research_runtime_v4, "_restore_writable_lane_markers", lambda *_args: ()
    )
    monkeypatch.setattr(
        research_runtime_v4,
        "_restore_writable_lane_markers_before_activation",
        lambda *_args: (),
    )
    monkeypatch.setattr(research_runtime_v4, "profile_sha256", lambda *_args: "2" * 64)
    monkeypatch.setattr(
        research_runtime_v4, "model_runtime_sha256", lambda *_args: "3" * 64
    )

    def run_model(*_args: object, **_kwargs: object) -> SimpleNamespace:
        calls.append(len(calls) + 1)
        outbox.write_bytes(b"invalid\n" if len(calls) == 1 else b"valid\n")
        return SimpleNamespace(returncode=0)

    def inspect(*_args: object, **_kwargs: object) -> dict[str, object]:
        if outbox.read_bytes() == b"invalid\n":
            return {
                "candidate_ids": ["candidate-1"],
                "findings": [
                    "candidate-1: strategy.py: target_weights method call is outside pure "
                    "allowlist: get"
                ],
                "outbox_sha256": hashlib.sha256(b"invalid\n").hexdigest(),
                "source_bundle_sha256s": ["4" * 64],
            }
        return {
            "candidate_ids": ["candidate-1"],
            "findings": [],
            "outbox_sha256": hashlib.sha256(b"valid\n").hexdigest(),
            "source_bundle_sha256s": ["5" * 64],
        }

    def receipts(
        _root: Path,
        _team_id: str,
        _phase: str,
        candidate_ids: list[str],
        **_kwargs: object,
    ) -> tuple[dict[str, str], ...]:
        recorded.append(tuple(candidate_ids))
        return ({"path": "receipt.json", "sha256": "6" * 64},)

    monkeypatch.setattr(research_runtime_v4.subprocess, "run", run_model)
    monkeypatch.setattr(research_runtime_v4, "_score_blind_batch_inspection", inspect)
    monkeypatch.setattr(research_runtime_v4, "record_candidate_receipts", receipts)

    result = research_runtime_v4.launch_team_phase.__wrapped__(
        tmp_path, "team-01", "discovery"
    )
    assert calls == [1, 2]
    assert recorded == [("candidate-1",)]
    assert result["model_sessions"] == 2
    assert result["repair_attempts"] == 1
    private_attempt = (
        tmp_path
        / "tournament/top40-v4-r2/research-sessions/admission-attempts/team-01/"
        "discovery-01.json"
    )
    attempt = json.loads(private_attempt.read_text(encoding="utf-8"))
    assert attempt["score_data_opened"] is False
    assert attempt["outbox_sha256"] == hashlib.sha256(b"invalid\n").hexdigest()
    feedback = json.loads(
        (team / "feedback/admission-discovery-01.json").read_text(encoding="utf-8")
    )
    assert feedback["remaining_repair_sessions"] == 3
    assert feedback["findings"] == attempt["findings"]


def test_launcher_exhausts_exactly_three_uniform_repairs_without_receipts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    team = tmp_path / TOP40_V4_R2_LAYOUT.team_root("team-01")
    for directory in ("candidates", "feedback", "outbox", "work"):
        (team / directory).mkdir(parents=True, exist_ok=True)
    outbox = team / "outbox/batch-1.json"
    calls: list[int] = []

    monkeypatch.setattr(activation_v4, "validate", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        activation_v4, "require_completed_pretrial_recovery", lambda *_args: {}
    )
    monkeypatch.setattr(
        research_runtime_v4, "validate_frozen_model_smoke", lambda *_args: {}
    )
    monkeypatch.setattr(
        research_runtime_v4, "_validate_runtime_launch_lifecycle", lambda *_args: None
    )
    monkeypatch.setattr(
        research_runtime_v4.isolation_v4, "audit_team_surface", lambda *_args: {}
    )
    monkeypatch.setattr(
        research_runtime_v4, "run_profile_probes", lambda *_args: {"passed": True}
    )
    monkeypatch.setattr(
        research_runtime_v4,
        "_record_launch_authority",
        lambda *_args: {"path": "launch.json", "sha256": "1" * 64},
    )
    monkeypatch.setattr(research_runtime_v4, "_codex_exec_command", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(research_runtime_v4, "_private_model_environment", lambda *_args: {})
    monkeypatch.setattr(research_runtime_v4, "ensure_private_model_runtime", lambda *_args: {})
    monkeypatch.setattr(
        research_runtime_v4, "_restore_writable_lane_markers", lambda *_args: ()
    )
    monkeypatch.setattr(
        research_runtime_v4,
        "_restore_writable_lane_markers_before_activation",
        lambda *_args: (),
    )

    def run_model(*_args: object, **_kwargs: object) -> SimpleNamespace:
        calls.append(len(calls) + 1)
        outbox.write_text(f"invalid-{len(calls)}\n", encoding="utf-8")
        return SimpleNamespace(returncode=0)

    def inspect(*_args: object, **_kwargs: object) -> dict[str, object]:
        payload = outbox.read_bytes()
        return {
            "candidate_ids": ["candidate-1"],
            "findings": ["candidate-1: deterministic source finding"],
            "outbox_sha256": hashlib.sha256(payload).hexdigest(),
            "source_bundle_sha256s": ["4" * 64],
        }

    monkeypatch.setattr(research_runtime_v4.subprocess, "run", run_model)
    monkeypatch.setattr(research_runtime_v4, "_score_blind_batch_inspection", inspect)
    monkeypatch.setattr(
        research_runtime_v4,
        "record_candidate_receipts",
        lambda *_args, **_kwargs: pytest.fail("invalid batch received a receipt"),
    )
    with pytest.raises(
        research_runtime_v4.CandidateRepairExhaustedError,
        match="every score-blind repair",
    ):
        research_runtime_v4.launch_team_phase.__wrapped__(
            tmp_path, "team-01", "discovery"
        )
    assert calls == [1, 2, 3, 4]
    attempts = sorted(
        (
            tmp_path
            / "tournament/top40-v4-r2/research-sessions/admission-attempts/team-01"
        ).glob("discovery-*.json")
    )
    assert [path.name for path in attempts] == [
        "discovery-01.json",
        "discovery-02.json",
        "discovery-03.json",
        "discovery-04.json",
    ]


def test_unchanged_repair_crash_never_grants_an_extra_model_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    team = tmp_path / TOP40_V4_R2_LAYOUT.team_root("team-01")
    for directory in ("candidates", "feedback", "outbox", "work"):
        (team / directory).mkdir(parents=True, exist_ok=True)
    outbox = team / "outbox/batch-1.json"
    calls: list[int] = []
    inspections = 0
    interrupted = False

    monkeypatch.setattr(activation_v4, "validate", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        activation_v4, "require_completed_pretrial_recovery", lambda *_args: {}
    )
    monkeypatch.setattr(
        research_runtime_v4, "validate_frozen_model_smoke", lambda *_args: {}
    )
    monkeypatch.setattr(
        research_runtime_v4, "_validate_runtime_launch_lifecycle", lambda *_args: None
    )
    monkeypatch.setattr(
        research_runtime_v4.isolation_v4, "audit_team_surface", lambda *_args: {}
    )
    monkeypatch.setattr(
        research_runtime_v4, "run_profile_probes", lambda *_args: {"passed": True}
    )
    monkeypatch.setattr(
        research_runtime_v4,
        "_record_launch_authority",
        lambda *_args: {"path": "launch.json", "sha256": "1" * 64},
    )
    monkeypatch.setattr(
        research_runtime_v4, "_codex_exec_command", lambda *_args, **_kwargs: []
    )
    monkeypatch.setattr(
        research_runtime_v4, "_private_model_environment", lambda *_args: {}
    )
    monkeypatch.setattr(
        research_runtime_v4, "ensure_private_model_runtime", lambda *_args: {}
    )
    monkeypatch.setattr(
        research_runtime_v4, "_restore_writable_lane_markers", lambda *_args: ()
    )
    monkeypatch.setattr(
        research_runtime_v4,
        "_restore_writable_lane_markers_before_activation",
        lambda *_args: (),
    )

    def run_model(*_args: object, **_kwargs: object) -> SimpleNamespace:
        calls.append(len(calls) + 1)
        outbox.write_bytes(b"unchanged-invalid\n")
        return SimpleNamespace(returncode=0)

    def inspect(*_args: object, **_kwargs: object) -> dict[str, object]:
        nonlocal inspections, interrupted
        inspections += 1
        if inspections == 3 and not interrupted:
            interrupted = True
            try:
                raise OSError("host interrupted post-model inspection")
            except OSError as exc:
                raise research_runtime_v4.ResearchRuntimeError(
                    "post-model inspection unavailable"
                ) from exc
        return {
            "candidate_ids": ["candidate-1"],
            "findings": ["candidate-1: deterministic source finding"],
            "outbox_sha256": hashlib.sha256(b"unchanged-invalid\n").hexdigest(),
            "source_bundle_sha256s": ["4" * 64],
        }

    monkeypatch.setattr(research_runtime_v4.subprocess, "run", run_model)
    monkeypatch.setattr(research_runtime_v4, "_score_blind_batch_inspection", inspect)
    monkeypatch.setattr(
        research_runtime_v4,
        "record_candidate_receipts",
        lambda *_args, **_kwargs: pytest.fail("invalid batch received a receipt"),
    )
    with pytest.raises(
        research_runtime_v4.ResearchRuntimeError,
        match="post-model inspection unavailable",
    ):
        research_runtime_v4.launch_team_phase.__wrapped__(
            tmp_path, "team-01", "discovery"
        )
    assert calls == [1, 2]

    with pytest.raises(research_runtime_v4.CandidateRepairExhaustedError):
        research_runtime_v4.launch_team_phase.__wrapped__(
            tmp_path, "team-01", "discovery"
        )
    assert calls == [1, 2, 3, 4]
    assert len(
        research_runtime_v4._admission_session_issues(
            tmp_path, "team-01", "discovery", "1" * 64
        )
    ) == 4
    assert len(
        research_runtime_v4._admission_attempts(
            tmp_path, "team-01", "discovery"
        )
    ) == 4


def test_admission_attempt_feedback_publish_crash_recovers_exact_guidance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    team = tmp_path / TOP40_V4_R2_LAYOUT.team_root("team-01")
    (team / "feedback").mkdir(parents=True)
    inspection = {
        "candidate_ids": ["candidate-1"],
        "findings": ["candidate-1: deterministic source finding"],
        "outbox_sha256": "1" * 64,
        "source_bundle_sha256s": ["2" * 64],
    }
    original_write = research_runtime_v4._write_immutable

    def interrupt_feedback(path: Path, payload: bytes, **kwargs: object) -> None:
        if path.parent == team / "feedback":
            raise OSError("host interrupted feedback publication")
        original_write(path, payload, **kwargs)

    monkeypatch.setattr(research_runtime_v4, "_write_immutable", interrupt_feedback)
    with pytest.raises(OSError, match="interrupted feedback"):
        research_runtime_v4._record_admission_attempt(
            tmp_path, "team-01", "discovery", inspection, repeat=True
        )
    attempts = research_runtime_v4._admission_attempts(
        tmp_path, "team-01", "discovery"
    )
    assert len(attempts) == 1
    feedback = team / "feedback/admission-discovery-01.json"
    assert not feedback.exists()

    monkeypatch.setattr(research_runtime_v4, "_write_immutable", original_write)
    research_runtime_v4._ensure_admission_feedback_chain(
        tmp_path, "team-01", "discovery", attempts
    )
    assert feedback.read_bytes() == research_runtime_v4._admission_feedback_payload(
        attempts[0]
    )


def test_close_is_revalidates_abandoned_batch_evidence_before_registry_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    disposition = {
        "event_type": "batch_abandoned",
        "payload": {
            "team_id": "team-01",
            "phase": "discovery",
            "reason": "model batch remained absent",
            "admission_attempt_path": (
                "tournament/top40-v4-r2/research-sessions/"
                "admission-attempts/team-01/discovery-04.json"
            ),
            "admission_attempt_sha256": "1" * 64,
        },
    }
    state = SimpleNamespace(
        retired={"team-01": disposition},
        records=(disposition,),
    )
    monkeypatch.setattr(orchestrator_v4.isolation_v4, "audit_surface", lambda *_args: {})
    monkeypatch.setattr(orchestrator_v4.activation_v4, "validate", lambda *_args: {})
    monkeypatch.setattr(orchestrator_v4.top40_v4, "load_config", lambda **_kwargs: {})
    monkeypatch.setattr(
        orchestrator_v4, "_close_interrupted_is_requests", lambda *_args: state
    )
    monkeypatch.setattr(
        orchestrator_v4.research_runtime_v4,
        "_phase_archive",
        lambda *_args: None,
    )
    monkeypatch.setattr(
        orchestrator_v4.research_runtime_v4,
        "validate_missing_batch_exhaustion",
        lambda *_args: (_ for _ in ()).throw(
            research_runtime_v4.ResearchRuntimeError("attempt evidence is missing")
        ),
    )
    monkeypatch.setattr(
        orchestrator_v4,
        "_write_nomination_registry",
        lambda *_args: pytest.fail("invalid terminal evidence mutated the registry"),
    )
    with pytest.raises(
        research_runtime_v4.ResearchRuntimeError, match="attempt evidence is missing"
    ):
        orchestrator_v4.close_is.__wrapped__(tmp_path)


def test_close_is_rejects_pending_successful_truncation_before_any_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    disposition = {
        "event_type": "batch_rejected",
        "payload": {
            "team_id": "team-01",
            "phase": "refinement",
            "reason": "score-blind refinement failure",
            "outbox_sha256": "1" * 64,
            "candidate_ids": [f"candidate-{number}" for number in range(9, 13)],
        },
    }
    state = SimpleNamespace(
        selection=None,
        retired={"team-01": disposition},
        nominations={},
        records=(disposition,),
        trials_by_team={"team-01": 8},
        is_successes={
            "2" * 64: {
                "payload": {"team_id": "team-01", "candidate_id": "candidate-1"}
            }
        },
    )
    monkeypatch.setattr(orchestrator_v4.isolation_v4, "audit_surface", lambda *_: {})
    monkeypatch.setattr(
        orchestrator_v4.activation_v4,
        "validate",
        lambda *_args, **_kwargs: {"record_sha256": "3" * 64},
    )
    monkeypatch.setattr(orchestrator_v4.top40_v4, "load_config", lambda **_: {})
    monkeypatch.setattr(
        orchestrator_v4, "_close_interrupted_is_requests", lambda *_: state
    )
    monkeypatch.setattr(
        orchestrator_v4, "_validate_retired_research_authorities", lambda *_: None
    )
    monkeypatch.setattr(
        orchestrator_v4,
        "_write_nomination_registry",
        lambda *_: pytest.fail("pending promotion mutated nomination registry"),
    )
    with pytest.raises(orchestrator_v4.OrchestratorError, match="broker promotes"):
        orchestrator_v4.close_is.__wrapped__(tmp_path)
    assert not (
        tmp_path / orchestrator_v4.TOP40_V4_LAYOUT.selection_freeze_path
    ).exists()
    assert not (
        tmp_path / orchestrator_v4.TOP40_V4_LAYOUT.nomination_registry_path
    ).exists()
    assert not (tmp_path / orchestrator_v4.TOP40_V4_LAYOUT.journal_path).exists()


def test_truncated_representative_ranking_charges_all_twelve_trials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    disposition = {
        "event_type": "batch_abandoned",
        "payload": {"phase": "refinement"},
    }
    state = SimpleNamespace(
        retired={"team-01": disposition},
        trials_by_team={"team-01": 8},
        is_successes={
            "1" * 64: {
                "payload": {"team_id": "team-01", "candidate_id": "candidate-a"}
            },
            "2" * 64: {
                "payload": {"team_id": "team-01", "candidate_id": "candidate-b"}
            },
        },
    )
    monkeypatch.setattr(
        orchestrator_v4,
        "_verified_summary",
        lambda _root, terminal: {
            "rank": 0
            if terminal["payload"]["candidate_id"] == "candidate-a"
            else 1
        },
    )
    observed_trials: list[int] = []

    def assess(
        summary: dict[str, int],
        _config: object,
        *,
        trial_count: int,
        neighborhood_passed: bool,
    ) -> dict[str, int]:
        assert neighborhood_passed is False
        observed_trials.append(trial_count)
        return {"rank": summary["rank"]}

    monkeypatch.setattr(orchestrator_v4.scoring_v4, "assess_is", assess)
    monkeypatch.setattr(
        orchestrator_v4.scoring_v4,
        "is_ranking_key",
        lambda selection: (selection["rank"],),
    )
    assert (
        orchestrator_v4._strongest_successful_candidate(  # noqa: SLF001
            tmp_path, state, {}, "team-01"
        )
        == "candidate-a"
    )
    assert observed_trials == [12, 12]


def test_historical_release_revalidates_terminal_batch_evidence_before_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = SimpleNamespace(retired={})
    monkeypatch.setattr(orchestrator_v4.isolation_v4, "audit_surface", lambda *_args: {})
    monkeypatch.setattr(orchestrator_v4.activation_v4, "validate", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(orchestrator_v4.top40_v4, "load_config", lambda **_kwargs: {})
    monkeypatch.setattr(orchestrator_v4.journal_v4, "read", lambda *_args: state)
    monkeypatch.setattr(
        orchestrator_v4,
        "_validate_retired_research_authorities",
        lambda *_args: (_ for _ in ()).throw(
            orchestrator_v4.OrchestratorError("terminal evidence is missing")
        ),
    )
    monkeypatch.setattr(
        orchestrator_v4,
        "_selection_freeze",
        lambda *_args: pytest.fail("historical selection opened before terminal validation"),
    )
    with pytest.raises(orchestrator_v4.OrchestratorError, match="evidence is missing"):
        orchestrator_v4.historical_release.__wrapped__(tmp_path)


def test_missing_batch_exhaustion_terminally_resolves_without_fabricated_outbox(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker_module()
    journal = tmp_path / broker.TOP40_V4_LAYOUT.journal_path
    journal.parent.mkdir(parents=True)
    broker.journal_v4.initialize(journal)
    team = tmp_path / broker.TOP40_V4_LAYOUT.team_root("team-01")
    for directory in ("candidates", "feedback", "outbox", "work"):
        (team / directory).mkdir(parents=True, exist_ok=True)
    launch_sha256 = "1" * 64
    missing = {
        "candidate_ids": [],
        "findings": ["outbox: required batch-1.json was not published"],
        "outbox_sha256": hashlib.sha256(b"").hexdigest(),
        "source_bundle_sha256s": [],
    }
    for session_number in range(4):
        research_runtime_v4._record_admission_session_issue(
            tmp_path,
            "team-01",
            "discovery",
            launch_sha256,
            session_number,
        )
        research_runtime_v4._record_admission_attempt(
            tmp_path, "team-01", "discovery", missing, repeat=True
        )

    monkeypatch.setattr(
        broker, "_restore_lane_markers_before_authority", lambda *_args: ()
    )
    monkeypatch.setattr(broker.activation_v4, "validate", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        broker.activation_v4,
        "require_completed_pretrial_recovery",
        lambda *_args: {},
    )
    monkeypatch.setattr(
        broker.orchestrator_v4.isolation_v4,
        "audit_team_surface",
        lambda *_args: {},
    )
    monkeypatch.setattr(
        broker.orchestrator_v4, "_batch_broker_frame", lambda *_args: 123
    )
    monkeypatch.setattr(
        broker.orchestrator_v4, "_write_nomination_registry", lambda *_args: None
    )
    monkeypatch.setattr(
        research_runtime_v4,
        "validate_launch_authority",
        lambda *_args: {"path": "launch.json", "sha256": launch_sha256},
    )
    monkeypatch.setattr(
        broker,
        "launch_phase",
        lambda *_args: (_ for _ in ()).throw(
            research_runtime_v4.CandidateRepairExhaustedError(
                "batch outbox remained absent after every repair"
            )
        ),
    )

    result = broker.run_team.__wrapped__(tmp_path, "team-01")
    state = broker.journal_v4.read(journal)
    assert result["terminal"] == "retired"
    assert state.trials_by_team["team-01"] == 0
    assert state.retired["team-01"]["event_type"] == "batch_abandoned"
    assert not (team / "outbox/batch-1.json").exists()
    assert (
        broker.run_team.__wrapped__(tmp_path, "team-01")["already_terminal"]
        is True
    )


def test_score_blind_refinement_inspection_includes_discovery_mechanism_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    team = tmp_path / TOP40_V4_R2_LAYOUT.team_root("team-01")
    outbox = team / "outbox/batch-2.json"
    outbox.parent.mkdir(parents=True)
    rows = [
        {
            "candidate_id": f"candidate-{number}",
            "entrypoint": f"candidates/candidate-{number}/strategy.py",
            "purpose": f"refinement {number}",
        }
        for number in range(9, 13)
    ]
    outbox.write_text(
        json.dumps(
            {"schema_version": 1, "operation": "is-batch", "requests": rows}
        )
        + "\n",
        encoding="utf-8",
    )
    prior_requests = {
        f"{number:064x}": {
            "payload": {
                "team_id": "team-01",
                "trial_number": number,
                "candidate_id": f"candidate-{number}",
                "metadata": {
                    "candidate_id": f"candidate-{number}",
                    "mechanism": "accepted discovery mechanism",
                    "tags": ["baseline"],
                },
            }
        }
        for number in range(1, 9)
    }
    monkeypatch.setattr(
        research_runtime_v4.journal_v4,
        "read",
        lambda _path: SimpleNamespace(is_requests=prior_requests),
    )
    monkeypatch.setattr(
        top40_v4, "load_config", lambda **_kwargs: SimpleNamespace(raw={})
    )
    monkeypatch.setattr(
        research_runtime_v4.runner_v4,
        "capture_source_bundle",
        lambda _root, _team_id, entrypoint: SimpleNamespace(
            candidate_root=entrypoint.rsplit("/", 1)[0],
            files=(),
            sha256=hashlib.sha256(entrypoint.encode()).hexdigest(),
        ),
    )
    monkeypatch.setattr(
        research_runtime_v4.isolation_v4,
        "validate_captured_candidate",
        lambda **_kwargs: None,
    )
    def metadata(
        _root: Path,
        _config: object,
        _team_id: str,
        entrypoint: str,
        **_kwargs: object,
    ) -> tuple[dict[str, object], str]:
        if "candidate-10/" in entrypoint:
            raise orchestrator_v4.OrchestratorError(
                "candidate metadata failed deterministic admission"
            )
        return {
            "candidate_id": entrypoint.split("/candidates/", 1)[1].split("/", 1)[0],
            "mechanism": (
                "undocumented new mechanism"
                if "candidate-9/" in entrypoint
                else "accepted discovery mechanism"
            ),
            "parent_candidate_id": None,
            "tags": ["role-check"] if "candidate-9/" in entrypoint else ["baseline"],
        }, "candidate.json"

    monkeypatch.setattr(orchestrator_v4, "_candidate_metadata", metadata)
    monkeypatch.setattr(
        research_runtime_v4,
        "_static_source_findings",
        lambda _files: (["strategy.py"], []),
    )
    monkeypatch.setattr(
        research_runtime_v4,
        "_future_invariance_evidence",
        lambda *_args, **_kwargs: {"status": "passed"},
    )

    inspection = research_runtime_v4._score_blind_batch_inspection(
        tmp_path, "team-01", "refinement", outbox
    )
    assert any(
        "descriptive mechanism variants require a current-epoch parent" in finding
        for finding in inspection["findings"]
    )
    assert any(
        "candidate metadata failed deterministic admission" in finding
        for finding in inspection["findings"]
    )
    assert len(inspection["source_bundle_sha256s"]) == 4


def test_repair_resume_detects_changed_source_with_unchanged_outbox(
    tmp_path: Path,
) -> None:
    first = {
        "candidate_ids": ["candidate-1"],
        "findings": ["candidate-1: first deterministic finding"],
        "outbox_sha256": "1" * 64,
        "source_bundle_sha256s": ["2" * 64],
    }
    second = {
        **first,
        "findings": ["candidate-1: remaining deterministic finding"],
        "source_bundle_sha256s": ["3" * 64],
    }
    original, created = research_runtime_v4._record_admission_attempt(
        tmp_path, "team-01", "discovery", first, repeat=False
    )
    changed, changed_created = research_runtime_v4._record_admission_attempt(
        tmp_path, "team-01", "discovery", second, repeat=False
    )
    repeated, repeated_created = research_runtime_v4._record_admission_attempt(
        tmp_path, "team-01", "discovery", second, repeat=False
    )
    assert created is True and original["attempt_number"] == 1
    assert changed_created is True and changed["attempt_number"] == 2
    assert repeated_created is False and repeated == changed


def test_admission_attempt_authority_rejects_links_and_unexpected_residue(
    tmp_path: Path,
) -> None:
    inspection = {
        "candidate_ids": ["candidate-1"],
        "findings": ["candidate-1: deterministic finding"],
        "outbox_sha256": "1" * 64,
        "source_bundle_sha256s": ["2" * 64],
    }
    research_runtime_v4._record_admission_attempt(
        tmp_path, "team-01", "discovery", inspection, repeat=False
    )
    directory = (
        tmp_path
        / "tournament/top40-v4-r2/research-sessions/admission-attempts/team-01"
    )
    attempt = directory / "discovery-01.json"
    alias = tmp_path / "external-attempt-alias.json"
    os.link(attempt, alias)
    with pytest.raises(research_runtime_v4.ResearchRuntimeError, match="private and regular"):
        research_runtime_v4._admission_attempts(
            tmp_path, "team-01", "discovery"
        )
    alias.unlink()
    unexpected = directory / "unexpected.json"
    unexpected.write_bytes(b"unexpected\n")
    unexpected.chmod(0o600)
    with pytest.raises(research_runtime_v4.ResearchRuntimeError, match="unexpected residue"):
        research_runtime_v4._admission_attempts(
            tmp_path, "team-01", "discovery"
        )

    symlink_root = tmp_path / "symlink-root"
    symlink_root.mkdir()
    research_runtime_v4._record_admission_attempt(
        symlink_root, "team-01", "discovery", inspection, repeat=False
    )
    category = (
        symlink_root
        / "tournament/top40-v4-r2/research-sessions/admission-attempts"
    )
    displaced = category.with_name("admission-attempts-displaced")
    category.rename(displaced)
    category.symlink_to(displaced, target_is_directory=True)
    preserved = (displaced / "team-01/discovery-01.json").read_bytes()
    with pytest.raises(
        research_runtime_v4.ResearchRuntimeError,
        match="cannot pin private admission authority directory",
    ):
        research_runtime_v4._admission_attempts(
            symlink_root, "team-01", "discovery"
        )
    assert (displaced / "team-01/discovery-01.json").read_bytes() == preserved


def test_static_semantic_subset_rejects_alias_and_helper_delegation() -> None:
    source = b"""
PACKED = 'LS'
ALIAS = PACKED
STATE = []
def hidden(context):
    STATE.append(context.decision_time)
    return ALIAS[0]
class Strategy:
    def target_weights(self, context, *, seed):
        token = hidden(context)
        return {symbol: (0.01 if token == 'L' else -0.01) for symbol in context.eligible_symbols}
def build_strategy():
    return Strategy()
"""
    item = runner_v4.source_archive_v4.SourceFile(
        path="strategy.py",
        size=len(source),
        sha256=hashlib.sha256(source).hexdigest(),
        content=source,
    )
    _executable, findings = research_runtime_v4._static_source_findings((item,))
    assert any("helper code" in finding for finding in findings)
    assert any("decision-time ordinal" in finding for finding in findings)
    assert any("bound literal lookup" in finding for finding in findings)
    assert any("forbidden state/data call append" in finding for finding in findings)


def test_static_semantic_subset_enforces_signature_and_positive_calls() -> None:
    source = b'''"""inaccessible explanation"""
ALIAS = ord
class Strategy:
    def target_weights(self, context, *, seed, cache=[]):
        cache.insert(0, __doc__)
        return {symbol: 0.01 for symbol in context.eligible_symbols}
def build_strategy():
    return Strategy()
'''
    item = runner_v4.source_archive_v4.SourceFile(
        path="strategy.py",
        size=len(source),
        sha256=hashlib.sha256(source).hexdigest(),
        content=source,
    )
    _executable, findings = research_runtime_v4._static_source_findings((item,))
    assert any("signature/defaults/decorators differ" in finding for finding in findings)
    assert any("module executable state construction" in finding for finding in findings)
    assert any("forbidden executable name access ord" in finding for finding in findings)
    assert any("executable docstring access" in finding for finding in findings)
    assert any("outside pure allowlist: insert" in finding for finding in findings)


def test_static_semantic_subset_rejects_literal_iteration_and_get() -> None:
    source = b"""
class Strategy:
    def target_weights(self, context, *, seed):
        table = {'close': 0.01}
        values = [number for number in (0.01, -0.01)]
        return {symbol: table.get('close') for symbol in context.eligible_symbols if values}
def build_strategy():
    return Strategy()
"""
    item = runner_v4.source_archive_v4.SourceFile(
        path="strategy.py",
        size=len(source),
        sha256=hashlib.sha256(source).hexdigest(),
        content=source,
    )
    _executable, findings = research_runtime_v4._static_source_findings((item,))
    assert any("nonempty literal mapping" in finding for finding in findings)
    assert any("nonempty literal sequence" in finding for finding in findings)
    assert any("outside pure allowlist: get" in finding for finding in findings)


def test_static_semantic_subset_rejects_opaque_numeric_precision() -> None:
    source = b"""
class Strategy:
    def target_weights(self, context, *, seed):
        return {symbol: 0.123456789 for symbol in context.eligible_symbols}
def build_strategy():
    return Strategy()
"""
    item = runner_v4.source_archive_v4.SourceFile(
        path="strategy.py",
        size=len(source),
        sha256=hashlib.sha256(source).hexdigest(),
        content=source,
    )
    _executable, findings = research_runtime_v4._static_source_findings((item,))
    assert any("opaque or oversized numeric" in finding for finding in findings)


def test_exact_source_future_invariance_runs_all_three_scenarios(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[pd.DataFrame] = []

    def fake_generate(
        _root: Path,
        _team_id: str,
        _entrypoint: str,
        bars: pd.DataFrame,
        _funding: pd.DataFrame,
        _membership: pd.DataFrame,
        decision_times: pd.DatetimeIndex,
        **_kwargs: object,
    ) -> pd.DataFrame:
        calls.append(bars.copy())
        return pd.DataFrame({"BTCUSDT": [0.1] * len(decision_times)}, index=decision_times)

    monkeypatch.setattr(runner_v4, "_generate_targets_in_worker", fake_generate)
    capture = SimpleNamespace(sha256="a" * 64, manifest_entries=(), files=())
    evidence = research_runtime_v4._future_invariance_evidence(
        ROOT,
        "team-01",
        "tournament/top40-v4-r2/teams/team-01/candidates/x/strategy.py",
        capture,
    )
    assert evidence["status"] == "passed"
    assert evidence["decision_count"] == 6
    assert len(calls) == 3
    assert len(calls[0]) < len(calls[1]) == len(calls[2])
    future = calls[1]["open_time"] > calls[0]["open_time"].max()
    assert not calls[1].loc[future, "close"].equals(calls[2].loc[future, "close"])


def test_causal_review_classifies_only_deterministic_candidate_execution_as_rejection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capture = SimpleNamespace(sha256="a" * 64, manifest_entries=(), files=())

    def candidate_failure(*_args: object, **_kwargs: object) -> None:
        raise runner_v4.StrategyExecutionError("candidate synthetic failure")

    monkeypatch.setattr(runner_v4, "_generate_targets_in_worker", candidate_failure)
    with pytest.raises(
        research_runtime_v4.CandidateSourceRejectedError,
        match="deterministic causal-review execution",
    ):
        research_runtime_v4._future_invariance_evidence(
            ROOT,
            "team-01",
            "tournament/top40-v4-r2/teams/team-01/candidates/x/strategy.py",
            capture,
        )

    def infrastructure_failure(*_args: object, **_kwargs: object) -> None:
        try:
            raise OSError("temporary worker storage failure")
        except OSError as exc:
            raise runner_v4.StrategySandboxError("cannot launch strategy namespace") from exc

    monkeypatch.setattr(runner_v4, "_generate_targets_in_worker", infrastructure_failure)
    with pytest.raises(runner_v4.StrategySandboxError, match="cannot launch") as caught:
        research_runtime_v4._future_invariance_evidence(
            ROOT,
            "team-01",
            "tournament/top40-v4-r2/teams/team-01/candidates/x/strategy.py",
            capture,
        )
    assert isinstance(caught.value.__cause__, OSError)


def test_direct_launcher_requires_activation_before_any_team_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse_activation(_root: Path) -> None:
        raise activation_v4.ActivationError("not activated")

    monkeypatch.setattr(activation_v4, "validate", refuse_activation)
    with pytest.raises(activation_v4.ActivationError, match="not activated"):
        research_runtime_v4.launch_team_phase.__wrapped__(
            tmp_path,
            "team-01",
            "discovery",
        )


def test_direct_launcher_requires_completed_pretrial_incident_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(activation_v4, "validate", lambda _root: {"activated": True})
    with pytest.raises(
        activation_v4.ActivationError,
        match="completed pretrial incident authority is missing",
    ):
        research_runtime_v4.launch_team_phase.__wrapped__(
            tmp_path,
            "team-01",
            "discovery",
        )


def test_direct_launcher_rejects_journal_contradictory_prior_feedback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    requests = [
        {
            "candidate_id": f"candidate-{number}",
            "entrypoint": f"candidates/candidate-{number}/strategy.py",
            "purpose": f"trial {number}",
        }
        for number in range(1, 9)
    ]
    outbox = {"schema_version": 1, "operation": "is-batch", "requests": requests}
    payload = json.dumps(outbox).encode()
    digest = hashlib.sha256(payload).hexdigest()
    archive = (
        tmp_path
        / "tournament/top40-v4-r2/research-sessions/outboxes/team-01"
        / f"discovery-{digest}.json"
    )
    archive.parent.mkdir(parents=True)
    archive.write_bytes(payload)
    archive.parent.chmod(0o700)
    archive.chmod(0o600)
    feedback = tmp_path / TOP40_V4_R2_LAYOUT.team_root("team-01") / "feedback/discovery.json"
    feedback.parent.mkdir(parents=True)
    feedback.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "tournament": TOP40_V4_R2_LAYOUT.name,
                "team_id": "team-01",
                "phase": "discovery",
                "interim_field_disclosure": False,
                "results": [None] * 8,
            }
        ),
        encoding="utf-8",
    )
    accepted: dict[str, object] = {}
    terminals: dict[str, object] = {}
    for number, request in enumerate(requests, start=1):
        request_hash = f"{number:064x}"
        accepted[request_hash] = {
            "payload": {
                "team_id": "team-01",
                "candidate_id": request["candidate_id"],
                "trial_number": number,
                "purpose": request["purpose"],
                "authority": {
                    "entrypoint": (
                        f"{TOP40_V4_R2_LAYOUT.team_root('team-01')}/{request['entrypoint']}"
                    )
                },
            }
        }
        terminals[request_hash] = {
            "event_type": "is_failed",
            "payload": {"failure": "candidate failed"},
        }
    state = SimpleNamespace(is_requests=accepted, is_terminals=terminals)
    monkeypatch.setattr(research_runtime_v4.journal_v4, "read", lambda _path: state)
    with pytest.raises(research_runtime_v4.ResearchRuntimeError, match="feedback differs"):
        research_runtime_v4._validate_prior_phase_evidence(
            tmp_path, "team-01", "discovery"
        )


@pytest.mark.parametrize("reason", ["line1\nline2", "line1\tline2", "line1\x7fline2"])
def test_retirement_reason_control_characters_fail_at_launch_and_consume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reason: str
) -> None:
    request = {"schema_version": 1, "operation": "retire", "reason": reason}
    with pytest.raises(research_runtime_v4.ResearchRuntimeError, match="retirement.*values"):
        research_runtime_v4._validate_phase_request(request, "decision")

    broker = _broker_module()
    monkeypatch.setattr(broker.activation_v4, "validate", lambda *_args, **_kwargs: {})
    with pytest.raises(broker.BrokerError, match="disabled|automatic"):
        broker.consume_decision(tmp_path, "team-01")


def test_broker_decision_rejects_wrong_schema_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker_module()
    monkeypatch.setattr(broker.activation_v4, "validate", lambda _root: {})
    request = {"schema_version": 999, "operation": "retire", "reason": "done"}
    monkeypatch.setattr(
        broker,
        "_read_request",
        lambda *_: (request, tmp_path / "decision.json", json.dumps(request).encode()),
    )
    with pytest.raises(broker.BrokerError, match="disabled|automatic"):
        broker.consume_decision(tmp_path, "team-01")


def test_legacy_broker_decision_consume_is_unconditionally_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker_module()
    monkeypatch.setattr(broker.activation_v4, "validate", lambda _root: {})
    retired: list[str] = []
    monkeypatch.setattr(
        broker.orchestrator_v4,
        "retire",
        lambda *_args, **_kwargs: retired.append("retired"),
    )
    with pytest.raises(broker.BrokerError, match="disabled|automatic"):
        broker.consume_decision(tmp_path, "team-01")
    assert retired == []


def test_completed_feedback_is_bound_to_journal_and_archived_outbox(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker_module()
    team = tmp_path / TOP40_V4_R2_LAYOUT.team_root("team-01")
    requests = []
    for number in range(1, 9):
        candidate_id = f"candidate-{number}"
        candidate = team / "candidates" / candidate_id
        candidate.mkdir(parents=True)
        (candidate / "strategy.py").write_text("VALUE = 1\n", encoding="utf-8")
        requests.append(
            {
                "candidate_id": candidate_id,
                "entrypoint": f"candidates/{candidate_id}/strategy.py",
                "purpose": f"trial {number}",
            }
        )
    outbox = {"schema_version": 1, "operation": "is-batch", "requests": requests}
    payload = json.dumps(outbox).encode()
    digest = hashlib.sha256(payload).hexdigest()
    archive = (
        tmp_path
        / "tournament/top40-v4-r2/research-sessions/outboxes/team-01"
        / f"discovery-{digest}.json"
    )
    archive.parent.mkdir(parents=True)
    archive.write_bytes(payload)
    archive.parent.chmod(0o700)
    archive.chmod(0o600)
    feedback = team / "feedback/discovery.json"
    feedback.parent.mkdir()
    feedback.write_text('{"contradictory":true}\n', encoding="utf-8")
    monkeypatch.setattr(
        broker,
        "_feedback_row",
        lambda _root, _team, candidate_id: {
            "candidate_id": candidate_id,
            "trial_number": int(candidate_id.rsplit("-", 1)[1]),
        },
    )
    with pytest.raises(broker.BrokerError, match="feedback differs"):
        broker._validate_completed_phase(tmp_path, "team-01", "discovery")


def test_launch_transition_rejects_terminal_lane(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker_module()
    state = SimpleNamespace(
        selection=None,
        nominations={"team-01": {}},
        retired={},
        trials_by_team={"team-01": 12},
    )
    monkeypatch.setattr(broker.journal_v4, "read", lambda _path: state)
    with pytest.raises(broker.BrokerError, match="terminal"):
        broker._validate_launch_transition(tmp_path, "team-01", "decision")


def test_consume_transition_rejects_out_of_phase_batch_before_evaluation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker_module()
    requests = [
        {
            "candidate_id": f"candidate-{number}",
            "entrypoint": f"candidates/candidate-{number}/strategy.py",
            "purpose": f"trial {number}",
        }
        for number in range(1, 9)
    ]
    accepted = {
        str(number): {
            "payload": {
                "team_id": "team-01",
                "candidate_id": f"old-{number}",
                "trial_number": number,
            }
        }
        for number in range(1, 9)
    }
    state = SimpleNamespace(
        selection=None,
        nominations={},
        retired={},
        trials_by_team={"team-01": 8},
        is_requests=accepted,
    )
    monkeypatch.setattr(broker.activation_v4, "validate", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        broker.orchestrator_v4,
        "preflight_is_batch",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        broker,
        "_validate_batch",
        lambda *_: (requests, tmp_path / "batch-1.json", b"{}"),
    )
    monkeypatch.setattr(broker.journal_v4, "read", lambda _path: state)
    monkeypatch.setattr(
        broker.research_runtime_v4,
        "validate_launch_authority",
        lambda *_: {},
    )
    evaluations: list[str] = []
    monkeypatch.setattr(
        broker.orchestrator_v4,
        "run_is",
        lambda *_args, **_kwargs: evaluations.append("ran"),
    )
    with pytest.raises(broker.BrokerError, match="out of phase|journal prefix"):
        broker.consume_batch(tmp_path, "team-01", "discovery")
    assert evaluations == []


def test_consume_batch_preserves_preacceptance_admission_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker_module()
    requests = [
        {
            "candidate_id": "candidate-1",
            "entrypoint": "candidates/candidate-1/strategy.py",
            "purpose": "trial 1",
        }
    ]
    monkeypatch.setattr(broker.activation_v4, "validate", lambda _root: {})
    monkeypatch.setattr(
        broker,
        "_validate_batch",
        lambda *_: (requests, tmp_path / "batch-1.json", b"{}"),
    )
    monkeypatch.setattr(broker, "_validate_consume_transition", lambda *_: None)
    monkeypatch.setattr(
        broker.research_runtime_v4, "recover_candidate_receipts", lambda *_: None
    )
    capability = object()
    monkeypatch.setattr(
        broker.orchestrator_v4,
        "preflight_is_batch",
        lambda *_args, **kwargs: None
        if kwargs.get("require_receipts") is False
        else capability,
    )
    monkeypatch.setattr(broker, "_maybe_accepted_record", lambda *_: None)

    def rejected(*_args: object, **_kwargs: object) -> None:
        raise broker.orchestrator_v4.OrchestratorError("original admission detail")

    monkeypatch.setattr(broker.orchestrator_v4, "run_is", rejected)
    with pytest.raises(
        broker.orchestrator_v4.OrchestratorError, match="original admission detail"
    ):
        broker.consume_batch(tmp_path, "team-01", "discovery")


def test_consume_batch_swallows_only_a_durable_terminal_runtime_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker_module()
    request = {
        "candidate_id": "candidate-1",
        "entrypoint": "candidates/candidate-1/strategy.py",
        "purpose": "trial 1",
    }
    monkeypatch.setattr(broker.activation_v4, "validate", lambda _root: {})
    monkeypatch.setattr(
        broker,
        "_validate_batch",
        lambda *_: ([request], tmp_path / "batch-1.json", b"{}"),
    )
    monkeypatch.setattr(broker, "_validate_consume_transition", lambda *_: None)
    monkeypatch.setattr(
        broker.research_runtime_v4, "recover_candidate_receipts", lambda *_: None
    )
    capability = object()
    monkeypatch.setattr(
        broker.orchestrator_v4,
        "preflight_is_batch",
        lambda *_args, **kwargs: None
        if kwargs.get("require_receipts") is False
        else capability,
    )
    calls = 0

    def accepted(*_args: object) -> object:
        nonlocal calls
        calls += 1
        if calls == 1:
            return None
        return (
            "a" * 64,
            {"payload": {"trial_number": 1}},
            {"event_type": "is_failed", "payload": {"failure": "runtime"}},
        )

    monkeypatch.setattr(broker, "_maybe_accepted_record", accepted)

    def failed(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("candidate runtime failure")

    monkeypatch.setattr(broker.orchestrator_v4, "run_is", failed)
    monkeypatch.setattr(
        broker,
        "_feedback_row",
        lambda *_: {"candidate_id": "candidate-1", "trial_number": 1},
    )
    monkeypatch.setattr(broker, "_write_exclusive", lambda *_: None)
    monkeypatch.setattr(broker, "_archive_outbox", lambda *_: "archive.json")
    result = broker.consume_batch(tmp_path, "team-01", "discovery")
    assert result["trials"] == 1


def test_consume_batch_reraises_when_accepted_request_has_no_terminal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker_module()
    request = {
        "candidate_id": "candidate-1",
        "entrypoint": "candidates/candidate-1/strategy.py",
        "purpose": "trial 1",
    }
    monkeypatch.setattr(broker.activation_v4, "validate", lambda _root: {})
    monkeypatch.setattr(
        broker,
        "_validate_batch",
        lambda *_: ([request], tmp_path / "batch-1.json", b"{}"),
    )
    monkeypatch.setattr(broker, "_validate_consume_transition", lambda *_: None)
    monkeypatch.setattr(
        broker.research_runtime_v4, "recover_candidate_receipts", lambda *_: None
    )
    capability = object()
    monkeypatch.setattr(
        broker.orchestrator_v4,
        "preflight_is_batch",
        lambda *_args, **kwargs: None
        if kwargs.get("require_receipts") is False
        else capability,
    )
    calls = 0

    def accepted(*_args: object) -> object:
        nonlocal calls
        calls += 1
        if calls == 1:
            return None
        return "a" * 64, {"payload": {"trial_number": 1}}, None

    monkeypatch.setattr(broker, "_maybe_accepted_record", accepted)

    def interrupted(*_args: object, **_kwargs: object) -> None:
        raise OSError("interrupted infrastructure")

    monkeypatch.setattr(broker.orchestrator_v4, "run_is", interrupted)
    with pytest.raises(OSError, match="interrupted infrastructure"):
        broker.consume_batch(tmp_path, "team-01", "discovery")


def test_consume_batch_preflight_rejection_retires_before_any_trial(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker_module()
    requests = [
        {
            "candidate_id": f"candidate-{number}",
            "entrypoint": f"candidates/candidate-{number}/strategy.py",
            "purpose": f"trial {number}",
        }
        for number in range(1, 9)
    ]
    outbox = tmp_path / "batch-1.json"
    monkeypatch.setattr(broker.activation_v4, "validate", lambda _root: {})
    monkeypatch.setattr(
        broker, "_validate_batch", lambda *_: (requests, outbox, b"{}\n")
    )
    monkeypatch.setattr(broker, "_validate_consume_transition", lambda *_: None)
    monkeypatch.setattr(
        broker.research_runtime_v4, "recover_candidate_receipts", lambda *_: None
    )

    def reject_preflight(*_args: object, **_kwargs: object) -> None:
        raise broker.orchestrator_v4.CandidateBatchRejectedError(
            "candidate-7: neighborhood coordinate mismatch"
        )

    monkeypatch.setattr(
        broker.orchestrator_v4, "preflight_is_batch", reject_preflight
    )
    retired: list[str] = []

    def retire(
        _root: Path,
        _team_id: str,
        _phase: str,
        error: orchestrator_v4.CandidateBatchRejectedError,
    ) -> dict[str, object]:
        retired.append(str(error))
        return {
            "ok": True,
            "team_id": "team-01",
            "phase": "discovery",
            "retired": True,
            "score_data_opened": False,
        }

    monkeypatch.setattr(broker, "_reject_failed_preflight", retire)
    evaluations: list[str] = []
    monkeypatch.setattr(
        broker.orchestrator_v4,
        "run_is",
        lambda *_args, **_kwargs: evaluations.append("evaluated"),
    )
    result = broker.consume_batch(tmp_path, "team-01", "discovery")
    assert result["retired"] is True
    assert result["score_data_opened"] is False
    assert len(retired) == 1
    assert evaluations == []


def test_journal_records_preacceptance_batch_rejection_without_weakening_retirement(
    tmp_path: Path,
) -> None:
    journal = tmp_path / "research-journal.jsonl"
    journal_v4.initialize(journal)
    candidate_ids = [f"candidate-{number}" for number in range(1, 9)]
    record = journal_v4.append(
        journal,
        "batch_rejected",
        {
            "team_id": "team-01",
            "phase": "discovery",
            "reason": "deterministic score-blind admission failure",
            "outbox_sha256": "1" * 64,
            "candidate_ids": candidate_ids,
        },
    )
    state = journal_v4.read(journal)
    assert state.trials_by_team["team-01"] == 0
    assert state.retired["team-01"]["record_sha256"] == record["record_sha256"]
    assert state.retired["team-01"]["event_type"] == "batch_rejected"

    second = tmp_path / "ordinary-retirement.jsonl"
    journal_v4.initialize(second)
    with pytest.raises(journal_v4.JournalError, match="retired before all twelve"):
        journal_v4.append(
            second,
            "retired",
            {"team_id": "team-01", "reason": "must remain forbidden"},
        )
    assert journal_v4.read(second).record_count == 0


def test_refinement_rejection_promotes_a_successful_discovery_representative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker_module()
    outbox = (
        tmp_path
        / broker.TOP40_V4_LAYOUT.team_root("team-01")
        / "outbox/batch-2.json"
    )
    outbox.parent.mkdir(parents=True)
    outbox.write_bytes(b'{"score_blind":"invalid-refinement"}\n')
    monkeypatch.setattr(
        broker.orchestrator_v4,
        "reject_batch_before_evaluation",
        lambda *_args: {"ok": True, "retired": True},
    )
    monkeypatch.setattr(
        broker,
        "_archive_outbox",
        lambda *_args: "research-sessions/outboxes/team-01/refinement.json",
    )
    monkeypatch.setattr(broker, "_team_has_success", lambda *_args: True)
    monkeypatch.setattr(
        broker,
        "_finalize_team_representative",
        lambda *_args: {"candidate_id": "candidate-best"},
    )
    result = broker._reject_failed_preflight(
        tmp_path,
        "team-01",
        "refinement",
        orchestrator_v4.CandidateBatchRejectedError("score-blind finding"),
    )
    assert result["retired"] is False
    assert result["research_truncated"] is True
    assert result["representative"] == {"candidate_id": "candidate-best"}


def test_successful_discovery_survives_score_blind_refinement_truncation(
    tmp_path: Path,
) -> None:
    journal = tmp_path / "research-journal.jsonl"
    journal_v4.initialize(journal)
    candidate_ids = [f"candidate-{number}" for number in range(1, 9)]
    source_hashes = [f"{number:064x}" for number in range(1, 9)]
    receipt_hashes = [f"{number + 20:064x}" for number in range(1, 9)]
    journal_v4.append(
        journal,
        "batch_preflighted",
        {
            "team_id": "team-01",
            "phase": "discovery",
            "outbox_sha256": "a" * 64,
            "candidate_ids": candidate_ids,
            "source_bundle_sha256s": source_hashes,
            "receipt_sha256s": receipt_hashes,
            "source_review_sha256s": ["b" * 64] * 8,
        },
    )
    success_record = None
    for trial_number, (candidate_id, source_sha256, receipt_sha256) in enumerate(
        zip(candidate_ids, source_hashes, receipt_hashes, strict=True), start=1
    ):
        accepted = journal_v4.append(
            journal,
            "is_accepted",
            {
                "team_id": "team-01",
                "run_id": f"team01-is-{trial_number:02d}",
                "trial_number": trial_number,
                "candidate_id": candidate_id,
                "purpose": f"discovery trial {trial_number}",
                "metadata": {},
                "authority": {
                    "entrypoint": (
                        "tournament/top40-v4-r2/teams/team-01/candidates/"
                        f"{candidate_id}/strategy.py"
                    ),
                    "source_bundle_sha256": source_sha256,
                },
                "research_session": {
                    "path": (
                        "tournament/top40-v4-r2/research-sessions/team-01/"
                        f"{source_sha256}.json"
                    ),
                    "sha256": receipt_sha256,
                    "source_bundle_sha256": source_sha256,
                },
                "output_path": f"reports-top40-v4-r2/is/team-01/trial-{trial_number}",
            },
        )
        terminal_payload = {
            "team_id": "team-01",
            "run_id": f"team01-is-{trial_number:02d}",
            "candidate_id": candidate_id,
            "request_sha256": accepted["record_sha256"],
        }
        if trial_number == 1:
            success_record = journal_v4.append(
                journal,
                "is_succeeded",
                {
                    **terminal_payload,
                    "summary_path": "reports-top40-v4-r2/is/team-01/trial-1/summary.json",
                    "summary_sha256": "c" * 64,
                },
            )
        else:
            journal_v4.append(
                journal,
                "is_failed",
                {**terminal_payload, "failure": "bounded candidate failure"},
            )
    journal_v4.append(
        journal,
        "batch_rejected",
        {
            "team_id": "team-01",
            "phase": "refinement",
            "reason": "deterministic score-blind refinement failure",
            "outbox_sha256": "d" * 64,
            "candidate_ids": [f"candidate-{number}" for number in range(9, 13)],
        },
    )
    for team_id in TOP40_V4_R2_LAYOUT.team_ids[1:]:
        journal_v4.append(
            journal,
            "batch_rejected",
            {
                "team_id": team_id,
                "phase": "discovery",
                "reason": "deterministic score-blind discovery failure",
                "outbox_sha256": hashlib.sha256(team_id.encode()).hexdigest(),
                "candidate_ids": [f"candidate-{number}" for number in range(1, 9)],
            },
        )
    state = journal_v4.read(journal)
    assert state.retired["team-01"]["payload"]["phase"] == "refinement"
    before = journal.read_bytes()
    with pytest.raises(journal_v4.JournalError, match="discarded a successful"):
        journal_v4.append(
            journal,
            "selection_frozen",
            {
                "input_head_sha256": state.head_sha256,
                "advancing": [],
                "selection_freeze_path": "tournament/top40-v4-r2/selection-freeze.json",
                "selection_freeze_sha256": "e" * 64,
            },
        )
    assert journal.read_bytes() == before
    assert success_record is not None
    journal_v4.append(
        journal,
        "nominated",
        {
            "team_id": "team-01",
            "candidate_id": "candidate-1",
            "success_record_sha256": success_record["record_sha256"],
            "certificate_path": (
                "tournament/top40-v4-r2/certificates/team-01/candidate-1.json"
            ),
            "certificate_sha256": "f" * 64,
            "nomination_path": (
                "tournament/top40-v4-r2/nominations/team-01/candidate-1.json"
            ),
            "nomination_sha256": "1" * 64,
        },
    )
    promoted = journal_v4.read(journal)
    assert promoted.trials_by_team["team-01"] == 8
    assert "team-01" not in promoted.retired
    assert promoted.nominations["team-01"]["payload"]["candidate_id"] == "candidate-1"


def test_r2_journal_refuses_a_selection_with_fewer_than_five_representatives(
    tmp_path: Path,
) -> None:
    journal = tmp_path / "research-journal.jsonl"
    journal_v4.initialize(journal)
    for team_id in TOP40_V4_R2_LAYOUT.team_ids:
        journal_v4.append(
            journal,
            "batch_rejected",
            {
                "team_id": team_id,
                "phase": "discovery",
                "reason": "deterministic score-blind admission failure",
                "outbox_sha256": hashlib.sha256(team_id.encode()).hexdigest(),
                "candidate_ids": [f"candidate-{number}" for number in range(1, 9)],
            },
        )
    state = journal_v4.read(journal)
    with pytest.raises(journal_v4.JournalError, match="five or six"):
        journal_v4.append(
            journal,
            "selection_frozen",
            {
                "input_head_sha256": state.head_sha256,
                "advancing": [],
                "selection_freeze_path": "tournament/top40-v4-r2/selection-freeze.json",
                "selection_freeze_sha256": "f" * 64,
            },
        )
    assert journal_v4.read(journal).record_count == 15


def test_r2_journal_requires_durable_whole_batch_authority_before_acceptance(
    tmp_path: Path,
) -> None:
    journal = tmp_path / "research-journal.jsonl"
    journal_v4.initialize(journal)
    source_sha256 = "3" * 64
    accepted = {
        "team_id": "team-01",
        "run_id": "team01-is-01-authority",
        "trial_number": 1,
        "candidate_id": "candidate-1",
        "purpose": "trial 1",
        "metadata": {},
        "authority": {
            "entrypoint": (
                "tournament/top40-v4-r2/teams/team-01/"
                "candidates/candidate-1/strategy.py"
            ),
            "source_bundle_sha256": source_sha256,
        },
        "research_session": {
            "path": (
                "tournament/top40-v4-r2/research-sessions/team-01/"
                f"{source_sha256}.json"
            ),
            "sha256": "4" * 64,
            "source_bundle_sha256": source_sha256,
        },
        "output_path": "reports-top40-v4-r2/is/team-01/trial-1",
    }
    with pytest.raises(journal_v4.JournalError, match="whole-batch preflight"):
        journal_v4.append(journal, "is_accepted", accepted)
    assert journal_v4.read(journal).record_count == 0

    journal_v4.append(
        journal,
        "batch_preflighted",
        {
            "team_id": "team-01",
            "phase": "discovery",
            "outbox_sha256": "5" * 64,
            "candidate_ids": [f"candidate-{number}" for number in range(1, 9)],
            "source_bundle_sha256s": [source_sha256, *["6" * 64] * 7],
            "receipt_sha256s": ["4" * 64, *["7" * 64] * 7],
            "source_review_sha256s": ["8" * 64] * 8,
        },
    )
    wrong_receipt = deepcopy(accepted)
    wrong_receipt["research_session"]["sha256"] = "8" * 64
    before = journal.read_bytes()
    with pytest.raises(journal_v4.JournalError, match="whole-batch preflight"):
        journal_v4.append(journal, "is_accepted", wrong_receipt)
    assert journal.read_bytes() == before
    journal_v4.append(journal, "is_accepted", accepted)
    assert journal_v4.read(journal).trials_by_team["team-01"] == 1


def test_run_is_rejects_post_preflight_receipt_substitution_before_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journal = tmp_path / orchestrator_v4.TOP40_V4_LAYOUT.journal_path
    journal.parent.mkdir(parents=True)
    journal_v4.initialize(journal)
    source_sha256 = "1" * 64
    receipt_sha256 = "2" * 64
    broker_frame = object()
    candidate = orchestrator_v4._BatchCandidate(
        candidate_id="candidate-1",
        entrypoint="candidates/candidate-1/strategy.py",
        purpose="trial 1",
        source_bundle_sha256=source_sha256,
        receipt_sha256=receipt_sha256,
    )
    capability = orchestrator_v4._BatchCapability(
        seal=orchestrator_v4._BATCH_CAPABILITY_SEAL,
        root=str(tmp_path.resolve()),
        team_id="team-01",
        phase="discovery",
        outbox_sha256="3" * 64,
        candidates=(candidate,),
        preflight_record_sha256="4" * 64,
        broker_frame=broker_frame,  # type: ignore[arg-type]
    )
    authority = orchestrator_v4.CandidateAuthority(
        team_id="team-01",
        candidate_id="candidate-1",
        candidate_root=(
            "tournament/top40-v4-r2/teams/team-01/candidates/candidate-1"
        ),
        entrypoint=(
            "tournament/top40-v4-r2/teams/team-01/"
            "candidates/candidate-1/strategy.py"
        ),
        source_bundle_sha256=source_sha256,
        source_archive_path="archive/candidate-1.json",
        source_archive_sha256="5" * 64,
        strategy_sha256="6" * 64,
        risk_policy_sha256="7" * 64,
        config_sha256="8" * 64,
        dependency_lock_sha256="9" * 64,
        data_manifest_sha256="a" * 64,
        evaluator_sha256="b" * 64,
    )
    monkeypatch.setattr(
        orchestrator_v4, "_batch_broker_frame", lambda *_args: broker_frame
    )
    monkeypatch.setattr(
        orchestrator_v4.isolation_v4, "audit_team_surface", lambda *_args: {}
    )
    monkeypatch.setattr(
        orchestrator_v4.activation_v4, "validate", lambda *_args, **_kwargs: {}
    )
    monkeypatch.setattr(
        orchestrator_v4.top40_v4,
        "load_config",
        lambda **_kwargs: SimpleNamespace(
            raw={"research": {"maximum_accepted_trials_per_team": 12}}
        ),
    )
    monkeypatch.setattr(
        orchestrator_v4,
        "_validated_batch_capability",
        lambda *_args, **_kwargs: candidate,
    )
    monkeypatch.setattr(
        orchestrator_v4,
        "_derive_authority",
        lambda *_args, **_kwargs: (authority, {"candidate_id": "candidate-1"}),
    )
    observed_phase: list[str | None] = []

    def substituted_receipt(
        *_args: object, expected_phase: str | None = None, **_kwargs: object
    ) -> dict[str, str]:
        observed_phase.append(expected_phase)
        return {
            "path": "replacement-receipt.json",
            "sha256": "c" * 64,
            "source_bundle_sha256": source_sha256,
        }

    monkeypatch.setattr(
        orchestrator_v4.research_runtime_v4,
        "validate_candidate_receipt",
        substituted_receipt,
    )
    monkeypatch.setattr(
        orchestrator_v4,
        "_validate_open_lane_mechanism",
        lambda *_args, **_kwargs: pytest.fail("mechanism gate reached after receipt swap"),
    )
    before = journal.read_bytes()
    with pytest.raises(orchestrator_v4.OrchestratorError, match="receipt differs"):
        orchestrator_v4.run_is.__wrapped__(
            tmp_path,
            "team-01",
            authority.entrypoint,
            purpose="trial 1",
            _batch_capability=capability,
        )
    assert observed_phase == ["discovery"]
    assert journal.read_bytes() == before
    assert not (tmp_path / orchestrator_v4.TOP40_V4_LAYOUT.reports_root / "is").exists()


def test_unauthorized_direct_and_cli_is_run_leave_pending_journal_byte_exact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    journal = tmp_path / orchestrator_v4.TOP40_V4_LAYOUT.journal_path
    journal.parent.mkdir(parents=True)
    journal_v4.initialize(journal)
    source_sha256 = "7" * 64
    journal_v4.append(
        journal,
        "batch_preflighted",
        {
            "team_id": "team-01",
            "phase": "discovery",
            "outbox_sha256": "8" * 64,
            "candidate_ids": [f"candidate-{number}" for number in range(1, 9)],
            "source_bundle_sha256s": [source_sha256, *["9" * 64] * 7],
            "receipt_sha256s": ["a" * 64, *["b" * 64] * 7],
            "source_review_sha256s": ["c" * 64] * 8,
        },
    )
    journal_v4.append(
        journal,
        "is_accepted",
        {
            "team_id": "team-01",
            "run_id": "team01-is-01-pending",
            "trial_number": 1,
            "candidate_id": "candidate-1",
            "purpose": "trial 1",
            "metadata": {},
            "authority": {
                "entrypoint": (
                    "tournament/top40-v4-r2/teams/team-01/"
                    "candidates/candidate-1/strategy.py"
                ),
                "source_bundle_sha256": source_sha256,
            },
            "research_session": {
                "path": (
                    "tournament/top40-v4-r2/research-sessions/team-01/"
                    f"{source_sha256}.json"
                ),
                "sha256": "a" * 64,
                "source_bundle_sha256": source_sha256,
            },
            "output_path": "reports-top40-v4-r2/is/team-01/pending",
        },
    )
    before = journal.read_bytes()
    with pytest.raises(orchestrator_v4.OrchestratorError, match="batch broker"):
        orchestrator_v4.run_is.__wrapped__(
            tmp_path,
            "team-01",
            (
                "tournament/top40-v4-r2/teams/team-01/"
                "candidates/candidate-2/strategy.py"
            ),
            purpose="trial 2",
        )
    assert journal.read_bytes() == before

    cli = _tournament_cli_module()
    monkeypatch.setattr(
        cli.orchestrator_v4,
        "run_is",
        lambda *_args, **_kwargs: pytest.fail("disabled CLI reached run_is"),
    )
    exit_code = cli.main(
        [
            "--root",
            str(tmp_path),
            "is-run",
            "team-01",
            "tournament/top40-v4-r2/teams/team-01/candidates/candidate-2/strategy.py",
            "--purpose",
            "trial 2",
        ]
    )
    assert exit_code == 2
    assert "batch broker" in capsys.readouterr().err
    assert journal.read_bytes() == before


def test_direct_batch_rejection_without_failed_preflight_capability_is_forbidden(
    tmp_path: Path,
) -> None:
    journal = tmp_path / orchestrator_v4.TOP40_V4_LAYOUT.journal_path
    journal.parent.mkdir(parents=True)
    journal_v4.initialize(journal)
    before = journal.read_bytes()
    error = orchestrator_v4.CandidateBatchRejectedError("caller-supplied rejection")
    with pytest.raises(orchestrator_v4.OrchestratorError, match="sealed failed-preflight"):
        orchestrator_v4.reject_batch_before_evaluation.__wrapped__(tmp_path, error)
    assert journal.read_bytes() == before


def test_direct_missing_batch_abandonment_without_broker_frame_is_forbidden(
    tmp_path: Path,
) -> None:
    journal = tmp_path / orchestrator_v4.TOP40_V4_LAYOUT.journal_path
    journal.parent.mkdir(parents=True)
    journal_v4.initialize(journal)
    before = journal.read_bytes()
    with pytest.raises(orchestrator_v4.OrchestratorError, match="canonical broker"):
        orchestrator_v4.abandon_missing_batch_before_evaluation.__wrapped__(
            tmp_path, "team-01", "discovery"
        )
    assert journal.read_bytes() == before


def test_direct_batch_preflight_cannot_issue_or_reject_authority(
    tmp_path: Path,
) -> None:
    journal = tmp_path / orchestrator_v4.TOP40_V4_LAYOUT.journal_path
    journal.parent.mkdir(parents=True)
    journal_v4.initialize(journal)
    outbox = (
        tmp_path
        / orchestrator_v4.TOP40_V4_LAYOUT.team_root("team-01")
        / "outbox/batch-1.json"
    )
    outbox.parent.mkdir(parents=True)
    outbox.write_text('{"wrong":"schema"}\n', encoding="utf-8")
    before_journal = journal.read_bytes()
    before_outbox = outbox.read_bytes()
    with pytest.raises(orchestrator_v4.OrchestratorError, match="canonical broker"):
        orchestrator_v4.preflight_is_batch.__wrapped__(
            tmp_path, "team-01", "discovery", require_receipts=False
        )
    assert journal.read_bytes() == before_journal
    assert outbox.read_bytes() == before_outbox


def test_canonical_broker_consume_frame_is_the_only_batch_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    broker = _broker_module()
    observed: list[object] = []

    class AdmissionObservedError(RuntimeError):
        pass

    def inspect_authority(
        root: Path,
        team_id: str,
        phase: str,
        **_kwargs: object,
    ) -> None:
        observed.append(orchestrator_v4._batch_broker_frame(root, team_id, phase))
        raise AdmissionObservedError

    monkeypatch.setattr(
        broker, "_restore_lane_markers_before_authority", lambda *_args: ()
    )
    monkeypatch.setattr(broker.activation_v4, "validate", lambda *_args: {})
    monkeypatch.setattr(
        broker.orchestrator_v4, "preflight_is_batch", inspect_authority
    )
    with pytest.raises(AdmissionObservedError):
        broker.consume_batch.__wrapped__(ROOT, "team-01", "discovery")
    assert len(observed) == 1


def test_preflight_classifies_malformed_and_unsafe_candidate_batches_score_blind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journal = tmp_path / orchestrator_v4.TOP40_V4_LAYOUT.journal_path
    journal.parent.mkdir(parents=True)
    journal_v4.initialize(journal)
    monkeypatch.setattr(orchestrator_v4, "_batch_broker_frame", lambda *_: 123)
    team = tmp_path / orchestrator_v4.TOP40_V4_LAYOUT.team_root("team-01")
    outbox = team / "outbox/batch-1.json"
    outbox.parent.mkdir(parents=True)
    monkeypatch.setattr(orchestrator_v4.activation_v4, "validate", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        orchestrator_v4.isolation_v4, "audit_team_surface", lambda *_: {}
    )
    monkeypatch.setattr(
        orchestrator_v4.top40_v4,
        "load_config",
        lambda **_kwargs: SimpleNamespace(raw={}),
    )
    monkeypatch.setattr(
        orchestrator_v4.research_runtime_v4, "validate_launch_authority", lambda *_: {}
    )
    outbox.write_text('{"wrong":"schema"}\n', encoding="utf-8")
    with pytest.raises(orchestrator_v4.CandidateBatchRejectedError) as malformed:
        orchestrator_v4.preflight_is_batch.__wrapped__(
            tmp_path, "team-01", "discovery", require_receipts=False
        )
    assert isinstance(
        malformed.value._capability, orchestrator_v4._BatchRejectionCapability
    )
    assert journal_v4.read(journal).record_count == 0

    requests = [
        {
            "candidate_id": f"candidate-{number}",
            "entrypoint": f"candidates/candidate-{number}/strategy.py",
            "purpose": f"trial {number}",
        }
        for number in range(1, 9)
    ]
    outbox.write_text(
        json.dumps({"schema_version": 1, "operation": "is-batch", "requests": requests}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        orchestrator_v4.runner_v4,
        "capture_source_bundle",
        lambda *_: (_ for _ in ()).throw(
            runner_v4.StrategySandboxError("unsafe candidate tree")
        ),
    )
    with pytest.raises(orchestrator_v4.CandidateBatchRejectedError, match="unsafe candidate"):
        orchestrator_v4.preflight_is_batch.__wrapped__(
            tmp_path, "team-01", "discovery", require_receipts=False
        )
    assert journal_v4.read(journal).record_count == 0


def test_preflight_receipt_failure_is_resumable_then_durably_authorizes_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journal = tmp_path / orchestrator_v4.TOP40_V4_LAYOUT.journal_path
    journal.parent.mkdir(parents=True)
    journal_v4.initialize(journal)
    monkeypatch.setattr(orchestrator_v4, "_batch_broker_frame", lambda *_: 123)
    team = tmp_path / orchestrator_v4.TOP40_V4_LAYOUT.team_root("team-01")
    outbox = team / "outbox/batch-1.json"
    outbox.parent.mkdir(parents=True)
    rows = [
        {
            "candidate_id": f"candidate-{number}",
            "entrypoint": f"candidates/candidate-{number}/strategy.py",
            "purpose": f"trial {number}",
        }
        for number in range(1, 9)
    ]
    outbox.write_text(
        json.dumps({"schema_version": 1, "operation": "is-batch", "requests": rows}),
        encoding="utf-8",
    )
    monkeypatch.setattr(orchestrator_v4.activation_v4, "validate", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        orchestrator_v4.isolation_v4, "audit_team_surface", lambda *_: {}
    )
    monkeypatch.setattr(
        orchestrator_v4.top40_v4,
        "load_config",
        lambda **_kwargs: SimpleNamespace(raw={}),
    )
    monkeypatch.setattr(
        orchestrator_v4.research_runtime_v4, "validate_launch_authority", lambda *_: {}
    )

    def capture(_root: Path, _team_id: str, entrypoint: str) -> SimpleNamespace:
        number = int(entrypoint.split("candidate-", 1)[1].split("/", 1)[0])
        return SimpleNamespace(files=(), sha256=f"{number:064x}")

    def metadata(
        _root: Path,
        _config: object,
        _team_id: str,
        entrypoint: str,
        *,
        capture: object,
    ) -> tuple[dict[str, object], str]:
        del capture
        candidate_id = entrypoint.split("/candidates/", 1)[1].split("/", 1)[0]
        return {
            "candidate_id": candidate_id,
            "mechanism": "one causal mechanism",
            "tags": ["baseline"],
        }, "candidate.json"

    monkeypatch.setattr(orchestrator_v4.runner_v4, "capture_source_bundle", capture)
    monkeypatch.setattr(orchestrator_v4, "_candidate_metadata", metadata)
    monkeypatch.setattr(
        orchestrator_v4.research_runtime_v4,
        "_static_source_findings",
        lambda _files: (["strategy.py"], []),
    )
    monkeypatch.setattr(
        orchestrator_v4.research_runtime_v4,
        "recover_candidate_receipts",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            research_runtime_v4.CandidateReceiptRejectedError(
                "existing immutable receipt differs"
            )
        ),
    )
    with pytest.raises(
        orchestrator_v4.CandidateBatchRejectedError,
        match="existing immutable receipt differs",
    ):
        orchestrator_v4.preflight_is_batch.__wrapped__(
            tmp_path, "team-01", "discovery"
        )
    assert journal_v4.read(journal).record_count == 0

    def transient_receipt_failure(*_args: object, **_kwargs: object) -> None:
        try:
            raise OSError("temporary receipt read failure")
        except OSError as exc:
            raise research_runtime_v4.ResearchRuntimeError(
                "receipt authority is unavailable"
            ) from exc

    monkeypatch.setattr(
        orchestrator_v4.research_runtime_v4,
        "recover_candidate_receipts",
        transient_receipt_failure,
    )
    with pytest.raises(
        research_runtime_v4.ResearchRuntimeError, match="receipt authority"
    ):
        orchestrator_v4.preflight_is_batch.__wrapped__(
            tmp_path, "team-01", "discovery"
        )
    assert journal_v4.read(journal).record_count == 0

    monkeypatch.setattr(
        orchestrator_v4.research_runtime_v4,
        "recover_candidate_receipts",
        lambda *_args, **_kwargs: (),
    )
    monkeypatch.setattr(
        orchestrator_v4.research_runtime_v4,
        "validate_candidate_receipt",
        lambda *_args, **_kwargs: {"sha256": "8" * 64},
    )
    monkeypatch.setattr(
        orchestrator_v4.research_runtime_v4,
        "review_candidate_source",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            research_runtime_v4.CandidateSourceRejectedError(
                "synthetic future-invariance rejection"
            )
        ),
    )
    with pytest.raises(
        orchestrator_v4.CandidateBatchRejectedError,
        match="future-invariance rejection",
    ):
        orchestrator_v4.preflight_is_batch.__wrapped__(
            tmp_path, "team-01", "discovery"
        )
    assert journal_v4.read(journal).record_count == 0

    monkeypatch.setattr(
        orchestrator_v4.research_runtime_v4,
        "review_candidate_source",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            research_runtime_v4.ResearchRuntimeError("source-review worker unavailable")
        ),
    )
    with pytest.raises(
        research_runtime_v4.ResearchRuntimeError, match="worker unavailable"
    ):
        orchestrator_v4.preflight_is_batch.__wrapped__(
            tmp_path, "team-01", "discovery"
        )
    assert journal_v4.read(journal).record_count == 0

    monkeypatch.setattr(
        orchestrator_v4.research_runtime_v4,
        "review_candidate_source",
        lambda *_args, **_kwargs: {"sha256": "9" * 64},
    )
    capability = orchestrator_v4.preflight_is_batch.__wrapped__(
        tmp_path, "team-01", "discovery"
    )
    assert isinstance(capability, orchestrator_v4._BatchCapability)
    state = journal_v4.read(journal)
    assert state.record_count == 1
    assert state.batch_preflights[("team-01", "discovery")]["record_sha256"] == (
        capability.preflight_record_sha256
    )
    repeated = orchestrator_v4.preflight_is_batch.__wrapped__(
        tmp_path, "team-01", "discovery"
    )
    assert isinstance(repeated, orchestrator_v4._BatchCapability)
    assert repeated.preflight_record_sha256 == capability.preflight_record_sha256
    assert journal_v4.read(journal).record_count == 1


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (b"not-json\n", "invalid JSON"),
        (b"{}\n", "schema differs"),
        (b'{"phase":"discovery","phase":"discovery"}\n', "duplicate key"),
        (b'{"phase":NaN}\n', "nonfinite value"),
        (
            json.dumps(
                dict.fromkeys(research_runtime_v4._RECEIPT_KEYS)  # noqa: SLF001
                | {"phase": "unknown"}
            ).encode(),
            "phase is invalid",
        ),
        (
            json.dumps(
                dict.fromkeys(research_runtime_v4._RECEIPT_KEYS)  # noqa: SLF001
                | {"phase": "refinement"}
            ).encode(),
            "another phase",
        ),
    ],
)
def test_candidate_receipt_semantic_corruption_is_explicitly_deterministic(
    tmp_path: Path,
    payload: bytes,
    expected: str,
) -> None:
    source_sha256 = "a" * 64
    relative = research_runtime_v4._receipt_relative(  # noqa: SLF001
        "team-01", source_sha256
    )
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(payload)
    path.chmod(0o600)
    with pytest.raises(
        research_runtime_v4.CandidateReceiptRejectedError, match=expected
    ):
        research_runtime_v4.validate_candidate_receipt(
            tmp_path,
            "team-01",
            "candidate-1",
            source_sha256,
            expected_phase="discovery",
        )


def test_candidate_receipt_hash_mismatch_and_immutable_conflict_are_deterministic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_sha256 = "b" * 64
    command_authority = {
        "command_sha256": "1" * 64,
        "environment_sha256": "2" * 64,
        "model": "frozen-model",
        "prompt_sha256": "3" * 64,
    }
    receipt = dict.fromkeys(research_runtime_v4._RECEIPT_KEYS)  # noqa: SLF001
    receipt.update(
        {
            **command_authority,
            "candidate_root": (
                "tournament/top40-v4-r2/teams/team-01/candidates/candidate-1"
            ),
            "disabled_capabilities": list(
                research_runtime_v4._DISABLED_FEATURES  # noqa: SLF001
            ),
            "launcher_version": research_runtime_v4.LAUNCHER_VERSION,
            "launch_authority_sha256": "4" * 64,
            "model_runtime_sha256": "5" * 64,
            "phase": "discovery",
            "profile_sha256": "6" * 64,
            "schema_version": research_runtime_v4.RECEIPT_SCHEMA_VERSION,
            "source_bundle_sha256": "c" * 64,
            "status": "passed",
            "team_id": "team-01",
            "team_kit_sha256": "7" * 64,
            "tournament": orchestrator_v4.TOP40_V4_LAYOUT.name,
        }
    )
    relative = research_runtime_v4._receipt_relative(  # noqa: SLF001
        "team-01", source_sha256
    )
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(receipt), encoding="utf-8")
    path.chmod(0o600)
    monkeypatch.setattr(
        research_runtime_v4, "_model_command_authority", lambda *_args: command_authority
    )
    monkeypatch.setattr(
        research_runtime_v4,
        "validate_launch_authority",
        lambda *_args: {"sha256": "4" * 64},
    )
    monkeypatch.setattr(
        research_runtime_v4, "model_runtime_sha256", lambda *_args: "5" * 64
    )
    monkeypatch.setattr(
        research_runtime_v4, "profile_sha256", lambda *_args: "6" * 64
    )
    monkeypatch.setattr(
        research_runtime_v4, "_team_kit_sha256", lambda *_args: "7" * 64
    )
    with pytest.raises(
        research_runtime_v4.CandidateReceiptRejectedError,
        match="source_bundle_sha256",
    ):
        research_runtime_v4.validate_candidate_receipt(
            tmp_path,
            "team-01",
            "candidate-1",
            source_sha256,
            expected_phase="discovery",
        )

    receipt.update(
        {
            "codex_version": "frozen-codex",
            "probes": {
                key: True for key in research_runtime_v4._PROBE_KEYS  # noqa: SLF001
            },
            "recorded_at_utc": "2026-08-21T12:00:00Z",
            "source_bundle_sha256": source_sha256,
        }
    )
    monkeypatch.setattr(
        research_runtime_v4, "_codex_binary", lambda: Path("/frozen/codex")
    )
    monkeypatch.setattr(
        research_runtime_v4, "_codex_version", lambda _binary: "frozen-codex"
    )
    canonical = json.dumps(
        receipt,
        allow_nan=False,
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
    ).encode("ascii") + b"\n"
    path.write_bytes(canonical)
    assert research_runtime_v4.validate_candidate_receipt(
        tmp_path,
        "team-01",
        "candidate-1",
        source_sha256,
        expected_phase="discovery",
    )["sha256"] == hashlib.sha256(canonical).hexdigest()

    noncanonical_payloads = (
        json.dumps(
            dict(reversed(tuple(receipt.items()))),
            allow_nan=False,
            ensure_ascii=True,
            indent=2,
        ).encode("ascii")
        + b"\n",
        json.dumps(
            receipt,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        + b"\n",
        canonical[:-1],
    )
    for noncanonical in noncanonical_payloads:
        path.write_bytes(noncanonical)
        with pytest.raises(
            research_runtime_v4.CandidateReceiptRejectedError,
            match="not canonical",
        ):
            research_runtime_v4.validate_candidate_receipt(
                tmp_path,
                "team-01",
                "candidate-1",
                source_sha256,
                expected_phase="discovery",
            )

    path.write_bytes(canonical)
    path.chmod(0o644)
    with pytest.raises(
        research_runtime_v4.ResearchRuntimeError, match="private regular"
    ):
        research_runtime_v4.validate_candidate_receipt(
            tmp_path,
            "team-01",
            "candidate-1",
            source_sha256,
            expected_phase="discovery",
        )
    assert path.read_bytes() == canonical
    assert stat.S_IMODE(path.stat().st_mode) == 0o644
    path.chmod(0o600)

    immutable = tmp_path / "immutable-receipt.json"
    research_runtime_v4._write_immutable(immutable, b"first\n")  # noqa: SLF001
    with pytest.raises(
        research_runtime_v4.CandidateReceiptRejectedError,
        match="already differs",
    ):
        research_runtime_v4._write_immutable(  # noqa: SLF001
            immutable,
            b"second\n",
            conflict_error=research_runtime_v4.CandidateReceiptRejectedError,
        )


def test_source_review_atomic_publish_recovers_every_private_staging_prefix(
    tmp_path: Path,
) -> None:
    source_sha256 = "d" * 64
    relative = research_runtime_v4._source_review_relative(  # noqa: SLF001
        "team-01", source_sha256
    )
    final = tmp_path / relative
    final.parent.mkdir(parents=True, mode=0o700)
    final.parent.chmod(0o700)
    final.parent.parent.chmod(0o700)
    staging = final.parent / f".{final.name}.staging"
    payload = b'{"complete":"source-review"}\n'

    # Crash after creating only a partial, unpublished staging inode.
    staging.write_bytes(payload[:7])
    staging.chmod(0o600)
    research_runtime_v4._publish_source_review_atomic(  # noqa: SLF001
        tmp_path, "team-01", source_sha256, payload
    )
    assert final.read_bytes() == payload
    assert final.stat().st_nlink == 1
    assert not staging.exists()

    # Crash after the durable no-replace link but before removing the staging name.
    final.unlink()
    staging.write_bytes(payload)
    staging.chmod(0o600)
    os.link(staging, final)
    assert final.stat().st_nlink == 2
    research_runtime_v4._publish_source_review_atomic(  # noqa: SLF001
        tmp_path, "team-01", source_sha256, b"new timestamp would differ\n"
    )
    assert final.read_bytes() == payload
    assert final.stat().st_nlink == 1
    assert not staging.exists()


def test_source_review_atomic_publish_rejects_unrelated_staging_hardlink(
    tmp_path: Path,
) -> None:
    source_sha256 = "e" * 64
    relative = research_runtime_v4._source_review_relative(  # noqa: SLF001
        "team-01", source_sha256
    )
    final = tmp_path / relative
    final.parent.mkdir(parents=True, mode=0o700)
    final.parent.chmod(0o700)
    final.parent.parent.chmod(0o700)
    staging = final.parent / f".{final.name}.staging"
    outside = tmp_path / "unrelated-private-file"
    outside.write_bytes(b"do not mutate\n")
    outside.chmod(0o600)
    os.link(outside, staging)
    before = outside.read_bytes()
    with pytest.raises(
        research_runtime_v4.ResearchRuntimeError, match="link topology is unsafe"
    ):
        research_runtime_v4._publish_source_review_atomic(  # noqa: SLF001
            tmp_path, "team-01", source_sha256, b"review\n"
        )
    assert outside.read_bytes() == before
    assert outside.stat().st_nlink == 2
    assert not final.exists()


def test_refinement_preflight_rejects_candidate_reuse_from_discovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journal = tmp_path / orchestrator_v4.TOP40_V4_LAYOUT.journal_path
    journal.parent.mkdir(parents=True)
    journal_v4.initialize(journal)
    monkeypatch.setattr(orchestrator_v4, "_batch_broker_frame", lambda *_: 123)
    discovery_ids = [f"candidate-{number}" for number in range(1, 9)]
    discovery_hashes = [f"{number:064x}" for number in range(1, 9)]
    journal_v4.append(
        journal,
        "batch_preflighted",
        {
            "team_id": "team-01",
            "phase": "discovery",
            "outbox_sha256": "b" * 64,
            "candidate_ids": discovery_ids,
            "source_bundle_sha256s": discovery_hashes,
            "receipt_sha256s": ["c" * 64] * 8,
            "source_review_sha256s": ["d" * 64] * 8,
        },
    )
    for number, (candidate_id, source_sha256) in enumerate(
        zip(discovery_ids, discovery_hashes, strict=True), start=1
    ):
        accepted = journal_v4.append(
            journal,
            "is_accepted",
            {
                "team_id": "team-01",
                "run_id": f"team01-is-{number:02d}-prefix",
                "trial_number": number,
                "candidate_id": candidate_id,
                "purpose": f"trial {number}",
                "metadata": {
                    "candidate_id": candidate_id,
                    "mechanism": "one causal mechanism",
                    "tags": ["baseline"],
                },
                "authority": {
                    "entrypoint": (
                        "tournament/top40-v4-r2/teams/team-01/"
                        f"candidates/{candidate_id}/strategy.py"
                    ),
                    "source_bundle_sha256": source_sha256,
                },
                "research_session": {
                    "path": (
                        "tournament/top40-v4-r2/research-sessions/team-01/"
                        f"{source_sha256}.json"
                    ),
                    "sha256": "c" * 64,
                    "source_bundle_sha256": source_sha256,
                },
                "output_path": f"reports-top40-v4-r2/is/team-01/trial-{number}",
            },
        )
        journal_v4.append(
            journal,
            "is_failed",
            {
                "team_id": "team-01",
                "run_id": f"team01-is-{number:02d}-prefix",
                "candidate_id": candidate_id,
                "request_sha256": accepted["record_sha256"],
                "failure": "bounded candidate failure",
            },
        )
    team = tmp_path / orchestrator_v4.TOP40_V4_LAYOUT.team_root("team-01")
    outbox = team / "outbox/batch-2.json"
    outbox.parent.mkdir(parents=True)
    rows = [
        {
            "candidate_id": candidate_id,
            "entrypoint": f"candidates/{candidate_id}/strategy.py",
            "purpose": f"refinement {number}",
        }
        for number, candidate_id in enumerate(
            ("candidate-1", "candidate-9", "candidate-10", "candidate-11"), start=1
        )
    ]
    outbox.write_text(
        json.dumps({"schema_version": 1, "operation": "is-batch", "requests": rows}),
        encoding="utf-8",
    )
    monkeypatch.setattr(orchestrator_v4.activation_v4, "validate", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        orchestrator_v4.isolation_v4, "audit_team_surface", lambda *_: {}
    )
    monkeypatch.setattr(
        orchestrator_v4.top40_v4,
        "load_config",
        lambda **_kwargs: SimpleNamespace(raw={}),
    )
    monkeypatch.setattr(
        orchestrator_v4.research_runtime_v4, "validate_launch_authority", lambda *_: {}
    )
    monkeypatch.setattr(
        orchestrator_v4.research_runtime_v4,
        "_validate_prior_phase_evidence",
        lambda *_args: None,
    )
    monkeypatch.setattr(
        orchestrator_v4.runner_v4,
        "capture_source_bundle",
        lambda *_: SimpleNamespace(files=(), sha256="d" * 64),
    )
    monkeypatch.setattr(
        orchestrator_v4,
        "_candidate_metadata",
        lambda _root, _config, _team, entrypoint, *, capture: (
            {
                "candidate_id": entrypoint.split("/candidates/", 1)[1].split("/", 1)[0],
                "mechanism": "one causal mechanism",
                "tags": ["baseline"],
            },
            "candidate.json",
        ),
    )
    monkeypatch.setattr(
        orchestrator_v4.research_runtime_v4,
        "_static_source_findings",
        lambda _files: (["strategy.py"], []),
    )
    before = journal.read_bytes()
    with pytest.raises(orchestrator_v4.CandidateBatchRejectedError, match="earlier phase"):
        orchestrator_v4.preflight_is_batch.__wrapped__(
            tmp_path, "team-01", "refinement", require_receipts=False
        )
    assert journal.read_bytes() == before
    assert ("team-01", "refinement") not in journal_v4.read(journal).batch_preflights


@pytest.mark.parametrize(
    "prior_error",
    ["prior research outbox archive is missing", "prior research feedback differs"],
)
def test_refinement_rejection_revalidates_prior_phase_before_any_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    prior_error: str,
) -> None:
    journal = tmp_path / orchestrator_v4.TOP40_V4_LAYOUT.journal_path
    journal.parent.mkdir(parents=True)
    journal_v4.initialize(journal)
    malformed = b'{"wrong":"refinement"}\n'
    outbox = (
        tmp_path
        / orchestrator_v4.TOP40_V4_LAYOUT.team_root("team-01")
        / "outbox/batch-2.json"
    )
    outbox.parent.mkdir(parents=True)
    outbox.write_bytes(malformed)
    state = SimpleNamespace(
        selection=None,
        nominations={},
        retired={},
        trials_by_team={"team-01": 8},
        is_requests={},
        is_terminals={},
        batch_preflights={},
        head_sha256=journal_v4.GENESIS_SHA256,
    )
    monkeypatch.setattr(orchestrator_v4, "_batch_broker_frame", lambda *_: 123)
    monkeypatch.setattr(
        orchestrator_v4, "_close_interrupted_is_requests", lambda *_: state
    )
    monkeypatch.setattr(orchestrator_v4.journal_v4, "read", lambda *_: state)
    monkeypatch.setattr(orchestrator_v4.activation_v4, "validate", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        orchestrator_v4.isolation_v4, "audit_team_surface", lambda *_args: {}
    )
    monkeypatch.setattr(
        orchestrator_v4.top40_v4,
        "load_config",
        lambda **_kwargs: SimpleNamespace(raw={}),
    )
    monkeypatch.setattr(
        orchestrator_v4.research_runtime_v4,
        "_validate_prior_phase_evidence",
        lambda *_args: (_ for _ in ()).throw(
            research_runtime_v4.ResearchRuntimeError(prior_error)
        ),
    )
    before = journal.read_bytes()
    with pytest.raises(research_runtime_v4.ResearchRuntimeError, match=prior_error):
        orchestrator_v4.preflight_is_batch.__wrapped__(
            tmp_path, "team-01", "refinement", require_receipts=False
        )
    assert journal.read_bytes() == before

    capability = orchestrator_v4._BatchRejectionCapability(
        seal=orchestrator_v4._BATCH_CAPABILITY_SEAL,
        root=str(tmp_path.resolve()),
        team_id="team-01",
        phase="refinement",
        outbox_sha256=hashlib.sha256(malformed).hexdigest(),
        candidate_ids=(),
        journal_head_sha256=journal_v4.GENESIS_SHA256,
        broker_frame=123,  # type: ignore[arg-type]
    )
    rejection = orchestrator_v4.CandidateBatchRejectedError(
        "malformed refinement batch", capability=capability
    )
    with pytest.raises(research_runtime_v4.ResearchRuntimeError, match=prior_error):
        orchestrator_v4.reject_batch_before_evaluation.__wrapped__(
            tmp_path, rejection
        )
    assert journal.read_bytes() == before


def test_preflighted_batch_rejects_changed_accepted_prefix_purpose_without_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journal = tmp_path / orchestrator_v4.TOP40_V4_LAYOUT.journal_path
    journal.parent.mkdir(parents=True)
    journal_v4.initialize(journal)
    monkeypatch.setattr(orchestrator_v4, "_batch_broker_frame", lambda *_: 123)
    candidate_ids = [f"candidate-{number}" for number in range(1, 9)]
    source_hashes = [f"{number:064x}" for number in range(1, 9)]
    original_rows = [
        {
            "candidate_id": candidate_id,
            "entrypoint": f"candidates/{candidate_id}/strategy.py",
            "purpose": f"trial {number}",
        }
        for number, candidate_id in enumerate(candidate_ids, start=1)
    ]
    original_payload = json.dumps(
        {"schema_version": 1, "operation": "is-batch", "requests": original_rows}
    ).encode()
    preflight = journal_v4.append(
        journal,
        "batch_preflighted",
        {
            "team_id": "team-01",
            "phase": "discovery",
            "outbox_sha256": hashlib.sha256(original_payload).hexdigest(),
            "candidate_ids": candidate_ids,
            "source_bundle_sha256s": source_hashes,
            "receipt_sha256s": ["e" * 64, *["f" * 64] * 7],
            "source_review_sha256s": ["a" * 64] * 8,
        },
    )
    accepted = journal_v4.append(
        journal,
        "is_accepted",
        {
            "team_id": "team-01",
            "run_id": "team01-is-01-prefix",
            "trial_number": 1,
            "candidate_id": "candidate-1",
            "purpose": "trial 1",
            "metadata": {
                "candidate_id": "candidate-1",
                "mechanism": "one causal mechanism",
                "tags": ["baseline"],
            },
            "authority": {
                "entrypoint": (
                    "tournament/top40-v4-r2/teams/team-01/"
                    "candidates/candidate-1/strategy.py"
                ),
                "source_bundle_sha256": source_hashes[0],
            },
            "research_session": {
                "path": (
                    "tournament/top40-v4-r2/research-sessions/team-01/"
                    f"{source_hashes[0]}.json"
                ),
                "sha256": "e" * 64,
                "source_bundle_sha256": source_hashes[0],
            },
            "output_path": "reports-top40-v4-r2/is/team-01/trial-1",
        },
    )
    journal_v4.append(
        journal,
        "is_failed",
        {
            "team_id": "team-01",
            "run_id": "team01-is-01-prefix",
            "candidate_id": "candidate-1",
            "request_sha256": accepted["record_sha256"],
            "failure": "bounded candidate failure",
        },
    )
    changed_rows = deepcopy(original_rows)
    changed_rows[0]["purpose"] = "changed after acceptance"
    team = tmp_path / orchestrator_v4.TOP40_V4_LAYOUT.team_root("team-01")
    outbox = team / "outbox/batch-1.json"
    outbox.parent.mkdir(parents=True)
    outbox.write_text(
        json.dumps({"schema_version": 1, "operation": "is-batch", "requests": changed_rows}),
        encoding="utf-8",
    )
    monkeypatch.setattr(orchestrator_v4.activation_v4, "validate", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        orchestrator_v4.isolation_v4, "audit_team_surface", lambda *_: {}
    )
    monkeypatch.setattr(
        orchestrator_v4.top40_v4,
        "load_config",
        lambda **_kwargs: SimpleNamespace(raw={}),
    )
    monkeypatch.setattr(
        orchestrator_v4.research_runtime_v4, "validate_launch_authority", lambda *_: {}
    )
    before = journal.read_bytes()
    with pytest.raises(orchestrator_v4.OrchestratorError, match="accepted batch prefix"):
        orchestrator_v4.preflight_is_batch.__wrapped__(
            tmp_path, "team-01", "discovery", require_receipts=False
        )
    assert journal.read_bytes() == before
    assert journal_v4.read(journal).batch_preflights[("team-01", "discovery")][
        "record_sha256"
    ] == preflight["record_sha256"]


def test_orchestrator_rejects_discovery_batch_at_trial_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journal = tmp_path / orchestrator_v4.TOP40_V4_LAYOUT.journal_path
    journal.parent.mkdir(parents=True)
    journal_v4.initialize(journal)
    monkeypatch.setattr(orchestrator_v4, "_batch_broker_frame", lambda *_: 123)
    monkeypatch.setattr(orchestrator_v4.activation_v4, "validate", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        orchestrator_v4.isolation_v4, "audit_team_surface", lambda *_: {}
    )
    monkeypatch.setattr(orchestrator_v4, "_write_nomination_registry", lambda *_: None)
    outbox = (
        tmp_path
        / orchestrator_v4.TOP40_V4_LAYOUT.team_root("team-01")
        / "outbox/batch-1.json"
    )
    outbox.parent.mkdir(parents=True)
    payload = b'{"invalid":"batch"}\n'
    outbox.write_bytes(payload)
    capability = orchestrator_v4._BatchRejectionCapability(
        seal=orchestrator_v4._BATCH_CAPABILITY_SEAL,
        root=str(tmp_path.resolve()),
        team_id="team-01",
        phase="discovery",
        outbox_sha256=hashlib.sha256(payload).hexdigest(),
        candidate_ids=(),
        journal_head_sha256=journal_v4.GENESIS_SHA256,
        broker_frame=123,  # type: ignore[arg-type]
    )
    error = orchestrator_v4.CandidateBatchRejectedError(
        "deterministic score-blind admission failure", capability=capability
    )
    result = orchestrator_v4.reject_batch_before_evaluation.__wrapped__(
        tmp_path,
        error,
    )
    state = journal_v4.read(journal)
    assert result["retired"] is True
    assert result["score_data_opened"] is False
    assert state.record_count == 1
    assert state.retired["team-01"]["event_type"] == "batch_rejected"


def test_run_team_crash_recovers_rejected_batch_outbox_archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker_module()
    team_id = "team-01"
    phase = "discovery"
    payload = b'{"operation":"is-batch"}\n'
    digest = hashlib.sha256(payload).hexdigest()
    outbox = (
        tmp_path
        / broker.TOP40_V4_LAYOUT.team_root(team_id)
        / "outbox"
        / "batch-1.json"
    )
    outbox.parent.mkdir(parents=True)
    outbox.write_bytes(payload)
    outbox.chmod(0o600)
    journal = tmp_path / broker.TOP40_V4_LAYOUT.journal_path
    journal.parent.mkdir(parents=True, exist_ok=True)
    broker.journal_v4.initialize(journal)
    broker.journal_v4.append(
        journal,
        "batch_rejected",
        {
            "team_id": team_id,
            "phase": phase,
            "reason": "deterministic score-blind admission failure",
            "outbox_sha256": digest,
            "candidate_ids": [f"candidate-{number}" for number in range(1, 9)],
        },
    )
    monkeypatch.setattr(broker.activation_v4, "validate", lambda _root: {})
    monkeypatch.setattr(
        broker, "_restore_lane_markers_before_authority", lambda *_: ()
    )

    result = broker.run_team.__wrapped__(tmp_path, team_id)
    archive = (
        tmp_path
        / "tournament/top40-v4-r2/research-sessions/outboxes"
        / team_id
        / f"{phase}-{digest}.json"
    )
    assert result["already_terminal"] is True
    assert not outbox.exists()
    assert archive.read_bytes() == payload


@pytest.mark.parametrize("archive_kind", ["corrupt", "symlink", "hardlink"])
def test_run_team_rejects_unsafe_rejected_batch_archive_without_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    archive_kind: str,
) -> None:
    broker = _broker_module()
    team_id = "team-01"
    phase = "discovery"
    payload = b'{"operation":"is-batch"}\n'
    digest = hashlib.sha256(payload).hexdigest()
    journal = tmp_path / broker.TOP40_V4_LAYOUT.journal_path
    journal.parent.mkdir(parents=True, exist_ok=True)
    broker.journal_v4.initialize(journal)
    broker.journal_v4.append(
        journal,
        "batch_rejected",
        {
            "team_id": team_id,
            "phase": phase,
            "reason": "deterministic score-blind admission failure",
            "outbox_sha256": digest,
            "candidate_ids": [f"candidate-{number}" for number in range(1, 9)],
        },
    )
    archive_directory = (
        tmp_path
        / "tournament/top40-v4-r2/research-sessions/outboxes"
        / team_id
    )
    archive_directory.mkdir(parents=True, mode=0o700)
    archive = archive_directory / f"{phase}-{digest}.json"
    external = tmp_path / f"outside-{archive_kind}.json"
    external.write_bytes(payload)
    external.chmod(0o600)
    if archive_kind == "corrupt":
        archive.write_bytes(b"corrupt\n")
        archive.chmod(0o600)
    elif archive_kind == "symlink":
        archive.symlink_to(external)
    else:
        os.link(external, archive)
    journal_before = journal.read_bytes()
    external_before = external.read_bytes()
    external_mode = stat.S_IMODE(external.stat().st_mode)
    monkeypatch.setattr(broker.activation_v4, "validate", lambda _root: {})
    monkeypatch.setattr(
        broker, "_restore_lane_markers_before_authority", lambda *_args: ()
    )

    with pytest.raises(broker.BrokerError, match="archive"):
        broker.run_team.__wrapped__(tmp_path, team_id)

    assert journal.read_bytes() == journal_before
    assert external.read_bytes() == external_before
    assert stat.S_IMODE(external.stat().st_mode) == external_mode
    assert os.path.lexists(archive)


@pytest.mark.parametrize("malformed_kind", ["wrong-count", "bad-purpose"])
def test_run_team_terminally_classifies_malformed_batch_after_repairs_exhausted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    malformed_kind: str,
) -> None:
    broker = _broker_module()
    journal = tmp_path / broker.TOP40_V4_LAYOUT.journal_path
    journal.parent.mkdir(parents=True)
    broker.journal_v4.initialize(journal)
    team = tmp_path / broker.TOP40_V4_LAYOUT.team_root("team-01")
    outbox = team / "outbox/batch-1.json"
    outbox.parent.mkdir(parents=True)
    rows = [
        {
            "candidate_id": f"candidate-{number}",
            "entrypoint": f"candidates/candidate-{number}/strategy.py",
            "purpose": f"trial {number}",
        }
        for number in range(1, 9)
    ]
    if malformed_kind == "wrong-count":
        rows.pop()
    else:
        rows[0]["purpose"] = "bad\ncontrol"
    payload = json.dumps(
        {"schema_version": 1, "operation": "is-batch", "requests": rows}
    ).encode() + b"\n"

    def interrupted_launch(_root: Path, _team_id: str, _phase: str) -> None:
        outbox.write_bytes(payload)
        outbox.chmod(0o600)
        raise research_runtime_v4.CandidateRepairExhaustedError(
            "published model batch remained invalid after score-blind repairs"
        )

    monkeypatch.setattr(broker, "launch_phase", interrupted_launch)
    monkeypatch.setattr(
        broker, "_restore_lane_markers_before_authority", lambda *_args: ()
    )
    monkeypatch.setattr(broker.activation_v4, "validate", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        broker.activation_v4, "require_completed_pretrial_recovery", lambda *_args: {}
    )
    monkeypatch.setattr(
        broker.orchestrator_v4.isolation_v4, "audit_team_surface", lambda *_args: {}
    )
    monkeypatch.setattr(
        broker.orchestrator_v4.top40_v4,
        "load_config",
        lambda **_kwargs: SimpleNamespace(raw={}),
    )
    monkeypatch.setattr(
        broker.orchestrator_v4.research_runtime_v4,
        "validate_launch_authority",
        lambda *_args: {},
    )
    monkeypatch.setattr(
        broker.orchestrator_v4, "_batch_broker_frame", lambda *_args: 123
    )
    monkeypatch.setattr(
        broker.orchestrator_v4, "_write_nomination_registry", lambda *_args: None
    )

    result = broker.run_team.__wrapped__(tmp_path, "team-01")
    state = broker.journal_v4.read(journal)
    terminal = state.retired["team-01"]
    assert result["terminal"] == "retired"
    assert terminal["event_type"] == "batch_rejected"
    assert state.trials_by_team["team-01"] == 0
    assert state.is_requests == {}
    assert terminal["payload"]["outbox_sha256"] == hashlib.sha256(payload).hexdigest()
    archive = (
        tmp_path
        / "tournament/top40-v4-r2/research-sessions/outboxes/team-01"
        / f"discovery-{hashlib.sha256(payload).hexdigest()}.json"
    )
    assert archive.read_bytes() == payload
    assert not outbox.exists()
    assert not (team / "feedback/discovery.json").exists()


def test_consume_batch_preflight_infrastructure_failure_is_resumable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker_module()
    request = {
        "candidate_id": "candidate-1",
        "entrypoint": "candidates/candidate-1/strategy.py",
        "purpose": "trial 1",
    }
    monkeypatch.setattr(broker.activation_v4, "validate", lambda _root: {})
    monkeypatch.setattr(
        broker,
        "_validate_batch",
        lambda *_: ([request], tmp_path / "batch-1.json", b"{}\n"),
    )
    monkeypatch.setattr(broker, "_validate_consume_transition", lambda *_: None)
    monkeypatch.setattr(
        broker.research_runtime_v4, "recover_candidate_receipts", lambda *_: None
    )
    monkeypatch.setattr(
        broker.orchestrator_v4,
        "preflight_is_batch",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            OSError("temporary preflight storage failure")
        ),
    )
    retired: list[str] = []
    monkeypatch.setattr(
        broker.orchestrator_v4,
        "reject_batch_before_evaluation",
        lambda *_args, **_kwargs: retired.append("retired"),
    )
    with pytest.raises(OSError, match="temporary preflight storage failure"):
        broker.consume_batch(tmp_path, "team-01", "discovery")
    assert retired == []


def test_runtime_decision_schema_and_automatic_selection_launch_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(research_runtime_v4.ResearchRuntimeError, match="nomination.*values"):
        research_runtime_v4._validate_phase_request(
            {
                "schema_version": 1,
                "operation": "nominate",
                "candidate_id": 123,
                "certificate_path": "work/research-certificate.json",
            },
            "decision",
        )
    state = SimpleNamespace(
        selection=None,
        nominations={"team-01": {}},
        retired={},
        trials_by_team={"team-01": 12},
    )
    monkeypatch.setattr(research_runtime_v4.journal_v4, "read", lambda _path: state)
    with pytest.raises(research_runtime_v4.ResearchRuntimeError, match="automatic"):
        research_runtime_v4._validate_runtime_launch_lifecycle(
            tmp_path, "team-01", "decision"
        )


def test_canonical_broker_refuses_a_decision_model_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker_module()
    monkeypatch.setattr(broker.activation_v4, "validate", lambda *_: {})
    launched: list[str] = []
    monkeypatch.setattr(
        broker.research_runtime_v4,
        "launch_team_phase",
        lambda _root, _team, phase: launched.append(phase),
    )
    with pytest.raises(broker.BrokerError, match="automatic"):
        inspect.unwrap(broker.launch_phase)(tmp_path, "team-01", "decision")
    assert launched == []


def test_score_blind_batch_inspection_rejects_legacy_decision_outbox_residue(
    tmp_path: Path,
) -> None:
    outbox = tmp_path / TOP40_V4_R2_LAYOUT.team_root("team-01") / "outbox"
    outbox.mkdir(parents=True)
    batch = outbox / "batch-1.json"
    batch.write_text("{}\n", encoding="utf-8")
    (outbox / "decision.json").write_text("{}\n", encoding="utf-8")
    inspection = research_runtime_v4._score_blind_batch_inspection(
        tmp_path, "team-01", "discovery", batch
    )
    assert inspection["candidate_ids"] == []
    assert inspection["findings"] == [
        "outbox: unexpected entries must be removed: decision.json"
    ]


def test_broker_lease_rejects_symlink_node(tmp_path: Path) -> None:
    broker = _broker_module()
    lock = tmp_path / "tournament/top40-v4-r2/broker.lock"
    lock.parent.mkdir(parents=True)
    target = tmp_path / "unrelated.lock"
    target.write_text("not the tournament lease\n", encoding="utf-8")
    lock.symlink_to(target)
    with pytest.raises(broker.research_runtime_v4.ResearchRuntimeError, match="lease"):
        with broker.research_runtime_v4.broker_lease(tmp_path):
            pass


def test_global_broker_lease_blocks_a_second_process(tmp_path: Path) -> None:
    broker = _broker_module()
    broker_path = str(ROOT / "scripts/top40_v4_r2_team_broker.py")
    script = f"""
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('broker_child', {broker_path!r})
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with module.research_runtime_v4.broker_lease(Path(sys.argv[1])):
    print('acquired', flush=True)
"""
    with broker.research_runtime_v4.broker_lease(tmp_path):
        child = subprocess.Popen(
            (sys.executable, "-c", script, str(tmp_path)),
            cwd=ROOT,
            env=_r2_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        time.sleep(0.2)
        assert child.poll() is None
    stdout, stderr = child.communicate(timeout=5)
    assert child.returncode == 0, stderr
    assert stdout.strip() == "acquired"


def test_r2_strongest_successful_candidate_uses_frozen_robust_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    terminals = {
        "1" * 64: {
            "payload": {"team_id": "team-01", "candidate_id": "weaker"},
            "rank": 0.4,
        },
        "2" * 64: {
            "payload": {"team_id": "team-01", "candidate_id": "stronger"},
            "rank": 0.9,
        },
    }
    state = SimpleNamespace(
        is_successes=terminals,
        trials_by_team={"team-01": 12},
        retired={},
    )
    monkeypatch.setattr(
        orchestrator_v4, "_verified_summary", lambda _root, terminal: terminal
    )

    def assess(summary: dict[str, object], *_args: object, **_kwargs: object):
        rank = float(summary["rank"])
        return {
            "ranking_vector": {
                "worst_fold_double_cost_sharpe": rank,
                "median_fold_double_cost_sharpe": rank,
                "trial_adjusted_confidence": rank,
                "gross_edge_per_turnover_bps": rank,
                "annualized_turnover": 1.0,
                "team_id": "team-01",
            }
        }

    monkeypatch.setattr(scoring_v4, "assess_is", assess)
    assert (
        orchestrator_v4._strongest_successful_candidate(
            tmp_path, state, {}, "team-01"
        )
        == "stronger"
    )


def test_r2_robust_order_ranks_missing_edge_density_last() -> None:
    common = {
        "worst_fold_double_cost_sharpe": 0.5,
        "median_fold_double_cost_sharpe": 0.5,
        "trial_adjusted_confidence": 0.9,
        "annualized_turnover": 1.0,
        "team_id": "team-01",
    }
    measured = {"ranking_vector": {**common, "gross_edge_per_turnover_bps": 10.0}}
    missing = {"ranking_vector": {**common, "gross_edge_per_turnover_bps": None}}
    assert scoring_v4.is_ranking_key(measured) < scoring_v4.is_ranking_key(missing)


def test_r2_zero_volatility_representative_remains_a_zero_weight_cash_sleeve(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    returns = {
        "team-01": pd.Series([0.0, 0.0, 0.0]),
        "team-02": pd.Series([0.0, 0.01, -0.01]),
    }
    monkeypatch.setattr(
        orchestrator_v4,
        "_daily_from_nomination",
        lambda _root, nomination: returns[str(nomination["team_id"])],
    )
    weights, cash = orchestrator_v4._capped_inverse_vol_weights(
        tmp_path,
        [{"team_id": "team-01"}, {"team_id": "team-02"}],
        0.25,
    )
    assert weights == {"team-01": 0.0, "team-02": 0.25}
    assert cash == 0.75


def test_r2_incomplete_truthful_certificate_preserves_fallback_representative(
    tmp_path: Path,
) -> None:
    tags = [
        "baseline",
        "sign-inversion",
        "formation-grid",
        "rebalance-grid",
        "control-ablation",
        "role-check",
        "local-neighborhood",
    ]
    request_hash = "a" * 64
    state = SimpleNamespace(
        is_requests={
            request_hash: {
                "payload": {
                    "team_id": "team-01",
                    "metadata": {"tags": ["baseline"]},
                }
            }
        }
    )
    relative = "tournament/top40-v4-r2/certificates/team-01/candidate.json"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "team_id": "team-01",
                "candidate_id": "candidate",
                "evidence": {
                    tag: [request_hash] if tag == "baseline" else [] for tag in tags
                },
            },
            sort_keys=True,
        )
        + "\n"
    )
    _certificate, _digest, diagnostics = orchestrator_v4._certificate(
        tmp_path,
        relative,
        state=state,
        config={"research": {"required_certificate_tags": tags}},
        team_id="team-01",
        candidate_id="candidate",
        nominated_request_hash=request_hash,
        allow_unqualified=True,
    )
    assert diagnostics["qualified"] is False
    assert diagnostics["accepted_trials_cited"] == 1
    assert diagnostics["accepted_trials_total"] == 1


def test_r2_failed_sign_inversion_is_a_truthful_qualification_shortfall(
    tmp_path: Path,
) -> None:
    baseline_hash = "a" * 64
    inversion_hash = "b" * 64
    tags = ["baseline", "sign-inversion"]

    def request(candidate_id: str, parent: str | None, request_tags: list[str]):
        return {
            "payload": {
                "team_id": "team-01",
                "candidate_id": candidate_id,
                "metadata": {
                    "parent_candidate_id": parent,
                    "mechanism": "one mechanism",
                    "formation_horizon": "30-bars",
                    "rebalance_horizon": "weekly",
                    "control_profile": "controls-off",
                    "tags": request_tags,
                },
                "authority": {"risk_policy_sha256": "c" * 64},
            }
        }

    state = SimpleNamespace(
        is_requests={
            baseline_hash: request("baseline", None, ["baseline"]),
            inversion_hash: request(
                "inversion", "baseline", ["sign-inversion"]
            ),
        },
        is_terminals={
            baseline_hash: {"event_type": "is_succeeded"},
            inversion_hash: {"event_type": "is_failed"},
        },
    )
    relative = "tournament/top40-v4-r2/certificates/team-01/candidate.json"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "team_id": "team-01",
                "candidate_id": "candidate",
                "evidence": {
                    "baseline": [baseline_hash],
                    "sign-inversion": [inversion_hash],
                },
            },
            sort_keys=True,
        )
        + "\n"
    )
    _certificate, _digest, diagnostics = orchestrator_v4._certificate(
        tmp_path,
        relative,
        state=state,
        config={"research": {"required_certificate_tags": tags}},
        team_id="team-01",
        candidate_id="candidate",
        nominated_request_hash=baseline_hash,
        allow_unqualified=True,
    )
    assert diagnostics["qualified"] is False
    assert "must have succeeded" in diagnostics["finding"]


def test_r2_retirement_is_forbidden_when_any_candidate_succeeded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "tournament/top40-v4-r2").mkdir(parents=True)
    state = SimpleNamespace(
        selection=None,
        retired={},
        nominations={},
        trials_by_team={"team-01": 12},
        is_successes={"a" * 64: {"payload": {"team_id": "team-01"}}},
    )
    monkeypatch.setattr(orchestrator_v4.isolation_v4, "audit_team_surface", lambda *_: {})
    monkeypatch.setattr(orchestrator_v4.activation_v4, "validate", lambda *_: {})
    monkeypatch.setattr(
        orchestrator_v4.top40_v4,
        "load_config",
        lambda **_kwargs: SimpleNamespace(
            raw={"research": {"minimum_accepted_trials_before_nomination": 8}}
        ),
    )
    monkeypatch.setattr(orchestrator_v4, "_close_interrupted_is_requests", lambda *_: state)
    with pytest.raises(orchestrator_v4.OrchestratorError, match="must submit"):
        inspect.unwrap(orchestrator_v4.retire)(tmp_path, "team-01", reason="done")


def test_r2_close_fills_five_with_honestly_labeled_ranked_representatives(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "tournament/top40-v4-r2").mkdir(parents=True)
    scores = {
        "team-01": 0.80,
        "team-02": 0.70,
        "team-03": 0.95,
        "team-04": 0.90,
        "team-05": 0.85,
        "team-06": 0.60,
        "team-07": 0.50,
    }
    nominations: dict[str, dict[str, object]] = {}
    summary_payload = b'{"bootstrap_probability_positive_mean":0.99}'
    summary_sha256 = hashlib.sha256(summary_payload).hexdigest()
    for team_id, score in scores.items():
        qualified = team_id in {"team-01", "team-02"}
        nomination = {
            "team_id": team_id,
            "candidate_id": f"{team_id}-representative",
            "trial_count": 12,
            "authority": {"candidate_id": f"{team_id}-representative"},
            "summary_path": f"summaries/{team_id}.json",
            "summary_sha256": summary_sha256,
            "selection": {
                "eligible": qualified,
                "ranking_vector": {
                    "worst_fold_double_cost_sharpe": score,
                    "median_fold_double_cost_sharpe": score,
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
                "nomination_sha256": hashlib.sha256(team_id.encode()).hexdigest(),
            },
            "nomination": nomination,
        }
    state = SimpleNamespace(
        selection=None,
        nominations=nominations,
        retired={
            team_id: {"event_type": "retired"}
            for team_id in TOP40_V4_R2_LAYOUT.team_ids
            if team_id not in nominations
        },
        trials_by_team={team_id: 12 for team_id in TOP40_V4_R2_LAYOUT.team_ids},
        head_sha256="a" * 64,
    )
    loaded = SimpleNamespace(
        sha256="b" * 64,
        raw={
            "selection": {
                "floors": {"minimum_field_adjusted_confidence_inclusive": 0.90},
                "ranking": {"advance_count": 6, "minimum_finalist_count": 5},
            },
            "ensemble": {
                "weight_method": "capped-inverse-is-daily-volatility",
                "minimum_constituents": 2,
                "maximum_constituent_weight": 0.25,
            },
        },
    )
    monkeypatch.setattr(orchestrator_v4.isolation_v4, "audit_surface", lambda *_: {})
    monkeypatch.setattr(
        orchestrator_v4.activation_v4,
        "validate",
        lambda *_: {"record_sha256": "c" * 64},
    )
    monkeypatch.setattr(orchestrator_v4.top40_v4, "load_config", lambda **_: loaded)
    monkeypatch.setattr(orchestrator_v4, "_close_interrupted_is_requests", lambda *_: state)
    monkeypatch.setattr(orchestrator_v4, "_validate_retired_research_authorities", lambda *_: None)
    monkeypatch.setattr(orchestrator_v4, "_write_nomination_registry", lambda *_: None)
    monkeypatch.setattr(
        orchestrator_v4,
        "_verified_nomination",
        lambda _root, record: record["nomination"],
    )
    monkeypatch.setattr(orchestrator_v4, "_stable_authority_bytes", lambda *_: summary_payload)
    monkeypatch.setattr(
        orchestrator_v4,
        "_strict_object_bytes",
        lambda *_: {"bootstrap_probability_positive_mean": 0.99},
    )
    monkeypatch.setattr(scoring_v4, "trial_adjusted_confidence", lambda *_: 0.95)
    monkeypatch.setattr(
        orchestrator_v4,
        "_capped_inverse_vol_weights",
        lambda _root, rows, _cap: (
            {
                str(row["team_id"]): 0.25 if index == 0 else 0.0
                for index, row in enumerate(rows)
            },
            0.75,
        ),
    )
    monkeypatch.setattr(
        orchestrator_v4.journal_v4,
        "append",
        lambda *_args, **_kwargs: {"record_sha256": "d" * 64},
    )
    result = inspect.unwrap(orchestrator_v4.close_is)(tmp_path)
    assert result["advancing"] == [
        "team-01",
        "team-02",
        "team-03",
        "team-04",
        "team-05",
    ]
    freeze = json.loads(
        (tmp_path / TOP40_V4_R2_LAYOUT.selection_freeze_path).read_text()
    )
    assert [row["selection_tier"] for row in freeze["advancing"]] == [
        "fully-qualified",
        "fully-qualified",
        "robust-ranked-representative",
        "robust-ranked-representative",
        "robust-ranked-representative",
    ]
    assert all(
        row["field_selection"]["eligible"] is row["fully_qualified"]
        for row in freeze["population"]
    )
    assert freeze["ensemble"]["available"] is False
    assert freeze["ensemble"]["weightable_constituents"] == 1
    assert freeze["ensemble"]["cash_weight"] == 0.75


def test_r2_close_refuses_to_fabricate_five_when_only_four_teams_succeeded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "tournament/top40-v4-r2").mkdir(parents=True)
    nominations = {
        team_id: {
            "payload": {
                "nomination_path": f"nominations/{team_id}.json",
                "nomination_sha256": hashlib.sha256(team_id.encode()).hexdigest(),
            },
            "nomination": {
                "team_id": team_id,
                "candidate_id": f"{team_id}-representative",
                "selection": {
                    "eligible": False,
                    "ranking_vector": {
                        "worst_fold_double_cost_sharpe": 0.5,
                        "median_fold_double_cost_sharpe": 0.5,
                        "trial_adjusted_confidence": 0.5,
                        "gross_edge_per_turnover_bps": 50.0,
                        "annualized_turnover": 10.0,
                        "team_id": team_id,
                    },
                },
                "summary_path": f"summaries/{team_id}.json",
                "summary_sha256": hashlib.sha256(b"summary").hexdigest(),
            },
        }
        for team_id in TOP40_V4_R2_LAYOUT.team_ids[:4]
    }
    state = SimpleNamespace(
        selection=None,
        nominations=nominations,
        retired={
            team_id: {"event_type": "retired"}
            for team_id in TOP40_V4_R2_LAYOUT.team_ids[4:]
        },
        trials_by_team={team_id: 12 for team_id in TOP40_V4_R2_LAYOUT.team_ids},
        head_sha256="a" * 64,
    )
    monkeypatch.setattr(orchestrator_v4.isolation_v4, "audit_surface", lambda *_: {})
    monkeypatch.setattr(
        orchestrator_v4.activation_v4,
        "validate",
        lambda *_: {"record_sha256": "b" * 64},
    )
    monkeypatch.setattr(
        orchestrator_v4.top40_v4,
        "load_config",
        lambda **_: SimpleNamespace(
            sha256="c" * 64,
            raw={
                "selection": {
                    "floors": {"minimum_field_adjusted_confidence_inclusive": 0.90},
                    "ranking": {"advance_count": 6, "minimum_finalist_count": 5},
                }
            },
        ),
    )
    monkeypatch.setattr(orchestrator_v4, "_close_interrupted_is_requests", lambda *_: state)
    monkeypatch.setattr(orchestrator_v4, "_validate_retired_research_authorities", lambda *_: None)
    monkeypatch.setattr(orchestrator_v4, "_write_nomination_registry", lambda *_: None)
    monkeypatch.setattr(
        orchestrator_v4,
        "_verified_nomination",
        lambda _root, record: record["nomination"],
    )
    monkeypatch.setattr(orchestrator_v4, "_stable_authority_bytes", lambda *_: b"summary")
    monkeypatch.setattr(
        orchestrator_v4,
        "_strict_object_bytes",
        lambda *_: {"bootstrap_probability_positive_mean": 0.5},
    )
    monkeypatch.setattr(scoring_v4, "trial_adjusted_confidence", lambda *_: 0.5)
    with pytest.raises(orchestrator_v4.OrchestratorError, match="fewer than five"):
        inspect.unwrap(orchestrator_v4.close_is)(tmp_path)
    assert not (tmp_path / TOP40_V4_R2_LAYOUT.selection_freeze_path).exists()
    assert not (tmp_path / TOP40_V4_R2_LAYOUT.journal_path).exists()


def test_disabled_decision_path_cannot_retire_a_successful_team(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker_module()
    monkeypatch.setattr(broker.activation_v4, "validate", lambda *_: {})
    retired: list[str] = []
    monkeypatch.setattr(
        broker.orchestrator_v4,
        "retire",
        lambda *_args, **_kwargs: retired.append("retired"),
    )
    with pytest.raises(broker.BrokerError, match="disabled|automatic"):
        broker.consume_decision(tmp_path, "team-01")
    assert retired == []


def test_broker_automatically_compiles_the_strongest_team_representative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker_module()
    outbox = tmp_path / TOP40_V4_R2_LAYOUT.team_root("team-01") / "outbox"
    outbox.mkdir(parents=True)
    (outbox / ".keep").write_text("\n", encoding="utf-8")
    state = SimpleNamespace(
        trials_by_team={"team-01": 12},
        retired={},
        is_requests={
            "a" * 64: {
                "payload": {
                    "team_id": "team-01",
                    "trial_number": 1,
                    "metadata": {"tags": ["baseline", "formation-grid"]},
                }
            },
            "b" * 64: {
                "payload": {
                    "team_id": "team-01",
                    "trial_number": 2,
                    "metadata": {"tags": ["local-neighborhood"]},
                }
            },
        },
    )
    tags = ["baseline", "formation-grid", "local-neighborhood"]
    monkeypatch.setattr(broker.journal_v4, "read", lambda *_: state)
    monkeypatch.setattr(broker, "_validate_completed_phase", lambda *_: {})
    monkeypatch.setattr(broker, "_team_has_success", lambda *_: True)
    monkeypatch.setattr(
        broker.top40_v4,
        "load_config",
        lambda **_: SimpleNamespace(
            raw={"research": {"required_certificate_tags": tags}}
        ),
    )
    monkeypatch.setattr(
        broker.orchestrator_v4,
        "_strongest_successful_candidate",
        lambda *_: "candidate-best",
    )
    monkeypatch.setattr(
        broker,
        "_accepted_record",
        lambda *_: (
            "a" * 64,
            {
                "payload": {
                    "authority": {"source_bundle_sha256": "c" * 64},
                    "trial_number": 1,
                }
            },
            {"event_type": "is_succeeded"},
        ),
    )
    reviewed: list[str] = []
    monkeypatch.setattr(
        broker.orchestrator_v4,
        "_validated_preflight_source_review",
        lambda _root, _state, **values: reviewed.append(str(values["candidate_id"])),
    )
    nominations: list[tuple[str, str]] = []

    def nominate(
        _root: Path, _team: str, candidate: str, certificate: str
    ) -> dict[str, object]:
        nominations.append((candidate, certificate))
        return {"ok": True, "team_id": "team-01", "candidate_id": candidate}

    monkeypatch.setattr(broker.orchestrator_v4, "nominate", nominate)
    result = broker._finalize_team_representative(tmp_path, "team-01")
    assert result["automatic_disposition"] is True
    assert result["selection_basis"] == "frozen-robust-is-ranking"
    assert reviewed == ["candidate-best"]
    assert nominations == [
        (
            "candidate-best",
            "tournament/top40-v4-r2/certificates/team-01/candidate-best.json",
        )
    ]
    certificate = json.loads(
        (
            tmp_path
            / "tournament/top40-v4-r2/certificates/team-01/candidate-best.json"
        ).read_text()
    )
    assert certificate["candidate_id"] == "candidate-best"
    assert certificate["evidence"] == {
        "baseline": ["a" * 64],
        "formation-grid": ["a" * 64],
        "local-neighborhood": ["b" * 64],
    }
