from __future__ import annotations

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


def test_open_lane_allows_exactly_one_explicit_mechanism_pivot() -> None:
    script = """
from types import SimpleNamespace
from crypto_trade.tournament import orchestrator_v4

def record(mechanism, tags):
    return {'payload': {'team_id': 'team-01', 'metadata': {
        'mechanism': mechanism, 'tags': tags,
    }}}

first = SimpleNamespace(is_requests={})
orchestrator_v4._validate_open_lane_mechanism(
    first, team_id='team-01', metadata={'mechanism': 'alpha', 'tags': ['baseline']}
)
history = SimpleNamespace(is_requests={'a': record('alpha', ['baseline'])})
try:
    orchestrator_v4._validate_open_lane_mechanism(
        history, team_id='team-01', metadata={'mechanism': 'beta', 'tags': ['baseline']}
    )
except orchestrator_v4.OrchestratorError:
    pass
else:
    raise AssertionError('untagged pivot was accepted')
orchestrator_v4._validate_open_lane_mechanism(
    history,
    team_id='team-01',
    metadata={'mechanism': 'beta', 'tags': ['mechanism-pivot']},
)
used = SimpleNamespace(is_requests={
    'a': record('alpha', ['baseline']),
    'b': record('beta', ['mechanism-pivot']),
})
try:
    orchestrator_v4._validate_open_lane_mechanism(
        used,
        team_id='team-01',
        metadata={'mechanism': 'gamma', 'tags': ['mechanism-pivot']},
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
