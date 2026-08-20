from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
import os
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
        activation_v4.top40_v4,
        "load_config",
        lambda **_kwargs: SimpleNamespace(raw={}, sha256="5" * 64),
    )


def test_r2_layout_has_fifteen_fresh_lanes_and_six_finalists() -> None:
    assert TOP40_V4_R2_LAYOUT.team_ids == tuple(
        f"team-{number:02d}" for number in range(1, 16)
    )
    assert TOP40_V4_R2_LAYOUT.advance_count == 6
    assert TOP40_V4_R2_LAYOUT.tournament_root == "tournament/top40-v4-r2"
    assert TOP40_V4_R2_LAYOUT.reports_root == "reports-top40-v4-r2"


def test_r2_config_uses_open_lanes_and_july_inclusive_holdout() -> None:
    config = _config()
    assert config["teams"] == list(TOP40_V4_R2_LAYOUT.team_ids)
    assert set(config["mandates"].values()) == {"open-independent-mechanism"}
    assert config["selection"]["ranking"]["advance_count"] == 6
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
orchestrator_v4._validate_exact_sign_inversions(None, None, requests, evidence)
frames['i'] = baseline_targets
try:
    orchestrator_v4._validate_exact_sign_inversions(None, None, requests, evidence)
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
        "launcher_version": "top40-v4-r2-research-runtime-v8",
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
    launch.write_bytes(b"current launch authority fixture\n")
    calls: list[tuple[Path, str, str]] = []

    def validate_current(root: str | Path, team_id: str, phase: str) -> dict[str, str]:
        calls.append((Path(root), team_id, phase))
        return {"path": str(launch), "sha256": hashlib.sha256(launch.read_bytes()).hexdigest()}

    monkeypatch.setattr(research_runtime_v4, "validate_launch_authority", validate_current)
    assert activation_v4.pretrial_recovery_pending(tmp_path) is False
    assert activation_v4.require_completed_pretrial_recovery(tmp_path)["results_reused"] is False
    assert calls == [
        (tmp_path, "team-01", "discovery"),
        (tmp_path, "team-01", "discovery"),
    ]

    def reject_current(_root: str | Path, _team_id: str, _phase: str) -> None:
        raise research_runtime_v4.ResearchRuntimeError("invalid current fixture")

    monkeypatch.setattr(research_runtime_v4, "validate_launch_authority", reject_current)
    assert activation_v4.pretrial_recovery_pending(tmp_path) is True
    with pytest.raises(activation_v4.ActivationError, match="launch authority is not current"):
        activation_v4.require_completed_pretrial_recovery(tmp_path)


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
            "authorized prompt",
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
            "authorized prompt",
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
    monkeypatch.setattr(broker.activation_v4, "validate", lambda _root: {})
    monkeypatch.setattr(broker, "_validate_decision_transition", lambda *_: None)
    monkeypatch.setattr(
        broker,
        "_read_request",
        lambda *_: (request, tmp_path / "decision.json", json.dumps(request).encode()),
    )
    with pytest.raises(broker.BrokerError, match="retirement reason"):
        broker.consume_decision(tmp_path, "team-01")


def test_broker_decision_rejects_wrong_schema_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker_module()
    monkeypatch.setattr(broker.activation_v4, "validate", lambda _root: {})
    monkeypatch.setattr(broker, "_validate_decision_transition", lambda *_: None)
    request = {"schema_version": 999, "operation": "retire", "reason": "done"}
    monkeypatch.setattr(
        broker,
        "_read_request",
        lambda *_: (request, tmp_path / "decision.json", json.dumps(request).encode()),
    )
    with pytest.raises(broker.BrokerError, match="schema_version"):
        broker.consume_decision(tmp_path, "team-01")


def test_broker_source_review_rejection_terminally_retires_lane(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker_module()
    monkeypatch.setattr(broker.activation_v4, "validate", lambda _root: {})
    monkeypatch.setattr(broker, "_validate_decision_transition", lambda *_: None)
    request = {
        "schema_version": 1,
        "operation": "nominate",
        "candidate_id": "candidate",
        "certificate_path": "work/research-certificate.json",
    }
    monkeypatch.setattr(
        broker,
        "_read_request",
        lambda *_: (request, tmp_path / "decision.json", json.dumps(request).encode()),
    )
    monkeypatch.setattr(
        broker,
        "_accepted_record",
        lambda *_: (
            "a" * 64,
            {"payload": {"authority": {"source_bundle_sha256": "b" * 64}}},
            {"event_type": "is_succeeded"},
        ),
    )
    monkeypatch.setattr(
        broker.research_runtime_v4,
        "review_candidate_source",
        lambda *_: (_ for _ in ()).throw(
            broker.research_runtime_v4.CandidateSourceRejectedError(
                "causal gate rejected"
            )
        ),
    )
    retired: list[str] = []

    def retire(_root: Path, _team_id: str, *, reason: str) -> dict[str, object]:
        retired.append(reason)
        return {"ok": True, "team_id": "team-01"}

    monkeypatch.setattr(broker.orchestrator_v4, "retire", retire)
    monkeypatch.setattr(broker, "_archive_outbox", lambda *_: "archive.json")
    result = broker.consume_decision(tmp_path, "team-01")
    assert result["nomination_rejected"] is True
    assert len(retired) == 1


def test_broker_decision_types_and_transient_failures_are_resumable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broker = _broker_module()
    monkeypatch.setattr(broker.activation_v4, "validate", lambda _root: {})
    monkeypatch.setattr(broker, "_validate_decision_transition", lambda *_: None)
    malformed = {"schema_version": 1, "operation": "retire", "reason": 123}
    monkeypatch.setattr(
        broker,
        "_read_request",
        lambda *_: (malformed, tmp_path / "decision.json", json.dumps(malformed).encode()),
    )
    with pytest.raises(broker.BrokerError, match="reason"):
        broker.consume_decision(tmp_path, "team-01")

    request = {
        "schema_version": 1,
        "operation": "nominate",
        "candidate_id": "candidate",
        "certificate_path": "work/research-certificate.json",
    }
    monkeypatch.setattr(
        broker,
        "_read_request",
        lambda *_: (request, tmp_path / "decision.json", json.dumps(request).encode()),
    )
    monkeypatch.setattr(
        broker,
        "_accepted_record",
        lambda *_: (
            "a" * 64,
            {"payload": {"authority": {"source_bundle_sha256": "b" * 64}}},
            {"event_type": "is_succeeded"},
        ),
    )
    monkeypatch.setattr(
        broker.research_runtime_v4,
        "review_candidate_source",
        lambda *_: (_ for _ in ()).throw(OSError("temporary storage interruption")),
    )
    retired: list[str] = []
    monkeypatch.setattr(
        broker.orchestrator_v4,
        "retire",
        lambda *_args, **_kwargs: retired.append("retired"),
    )
    with pytest.raises(OSError, match="temporary"):
        broker.consume_decision(tmp_path, "team-01")
    assert retired == []

    def wrapped_storage_failure(*_args: object) -> None:
        try:
            raise OSError("wrapped temporary storage interruption")
        except OSError as exc:
            raise broker.research_runtime_v4.ResearchRuntimeError(
                "cannot read research authority safely"
            ) from exc

    monkeypatch.setattr(
        broker.research_runtime_v4,
        "review_candidate_source",
        wrapped_storage_failure,
    )
    with pytest.raises(broker.research_runtime_v4.ResearchRuntimeError, match="authority"):
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
    monkeypatch.setattr(broker.activation_v4, "validate", lambda _root: {})
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


def test_runtime_decision_schema_and_terminal_launch_fail_closed(
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
    with pytest.raises(research_runtime_v4.ResearchRuntimeError, match="terminal"):
        research_runtime_v4._validate_runtime_launch_lifecycle(
            tmp_path, "team-01", "decision"
        )


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
