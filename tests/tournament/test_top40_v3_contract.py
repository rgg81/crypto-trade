from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from crypto_trade.tournament.layout_v3 import TOP40_V3_LAYOUT
from crypto_trade.tournament.top40_v3 import (
    TEAM_IDS,
    _validate_config,
    load_config,
    new_run_state,
    validate_run_state,
)

ROOT = Path(__file__).parents[2]
CONFIG_PATH = ROOT / "tournament/top40-v3/config.toml"
CREATED = "2026-07-18T12:00:00+00:00"
HASH_A = "a" * 64
HASH_B = "b" * 64


def _config():
    return load_config(CONFIG_PATH)


def _set(raw: dict[str, object], path: tuple[str, ...], value: object) -> None:
    target = raw
    for key in path[:-1]:
        child = target[key]
        assert isinstance(child, dict)
        target = child
    target[path[-1]] = value


def _probe_lock(candidate: str, digest: str, round_name: str) -> dict[str, str]:
    return {
        "candidate_id": candidate,
        "sha256": digest,
        "locked_at_utc": CREATED,
        "round": round_name,
    }


def test_loads_current_v3_contract_with_fresh_layout_and_exact_limits():
    config = _config()

    assert TEAM_IDS == tuple(f"team-{number:02d}" for number in range(1, 11))
    assert config.opening_probe_limit == 3
    assert config.comeback_probe_limit == 2
    assert config.total_probe_limit == 5
    assert config.raw["labs"]["strategy_seed"] == 20260718
    assert TOP40_V3_LAYOUT.tournament_root == "tournament/top40-v3"
    assert TOP40_V3_LAYOUT.reports_root == "reports-top40-v3"
    assert config.raw["paths"]["snapshot_dir"] == "data/top40/snapshot-v1"
    assert config.raw["paths"]["shared_snapshot_manifest"] == "tournament/top40/data_manifest.json"


@pytest.mark.parametrize(
    ("path", "value", "message"),
    (
        (("name",), "quant-portfolio-blind-top40-v2", "identity"),
        (("teams",), ["team-01"], "ten-team"),
        (("splits", "validation", "start"), "2022-07-02T00:00:00Z", "four exact windows"),
        (("paths", "organizer_lab_journal"), "tournament/top40-v2/lab.jsonl", "fresh V3 write path"),
        (("universe", "a6_authority", "policy_sha256"), "0" * 64, "A6 pure-crypto"),
        (("universe", "a6_authority", "audit_dependency_sha256"), "0" * 64, "A6 pure-crypto"),
        (("universe", "a6_authority", "audit_report_sha256"), "0" * 64, "A6 pure-crypto"),
        (("execution", "taker_fee_bps_per_side"), 0.0, "execution contract"),
        (("labs", "strategy_seed"), 1, "strategy seed"),
        (("validation", "maximum_opening_probes_per_team"), 4, "opening probe"),
        (("validation", "maximum_comeback_probes_per_eligible_team"), 1, "comeback probe"),
        (("candidate", "readiness", "minimum_train_double_cost_sharpe_exclusive"), -1.0, "positive train"),
        (("candidate", "readiness", "minimum_validation_annualized_return_exclusive"), -1.0, "positive validation"),
        (("candidate", "nominee_must_pass_public_core"), False, "nominee public-core"),
        (("qualification", "public", "core", "minimum_net_sharpe_inclusive"), 0.5, "public performance"),
        (("ranking", "robustness", "formula"), "net_sharpe", "robustness formula"),
        (("ranking", "robustness", "advance_count"), 5, "top-four"),
        (("diagnostics", "veto"), True, "diagnostic non-veto"),
        (("qualification", "private", "minimum_annualized_return_exclusive"), -1.0, "positive private"),
        (("qualification", "private", "maximum_drawdown_inclusive"), 0.5, "private drawdown"),
        (("final_oos", "observations_per_finalist"), 2, "single final observation"),
    ),
)
def test_config_drift_fails_closed(path, value, message):
    raw = deepcopy(_config().raw)
    assert isinstance(raw, dict)
    _set(raw, path, value)

    with pytest.raises(ValueError, match=message):
        _validate_config(raw)


def test_complete_semantic_contract_rejects_unexpected_policy_drift():
    raw = deepcopy(_config().raw)
    raw["activation"]["unexpected_switch"] = True

    with pytest.raises(ValueError, match="complete frozen semantic contract"):
        _validate_config(raw)


def test_loader_rejects_a_config_outside_the_v3_layout(tmp_path):
    wrong = tmp_path / "config.toml"
    wrong.write_bytes(CONFIG_PATH.read_bytes())

    with pytest.raises(ValueError, match="canonical V3 layout"):
        load_config(wrong)


def test_new_state_is_fresh_and_tracks_ten_independent_teams():
    config = _config()
    state = new_run_state(config, created_at_utc=CREATED)
    validate_run_state(state, config)

    assert state["phase"] == "policy_defined"
    assert tuple(state["teams"]) == TEAM_IDS
    assert all(value is None for value in state["locks"].values())
    for team in state["teams"].values():
        assert team["lab_run_count"] == 0
        assert team["validation_probe_count"] == 0
        assert team["nomination_count"] == 0
        assert team["probe_locks"] == []
        assert team["nominee_lock"] is None


def test_state_accepts_bound_opening_comeback_and_nomination_counters():
    config = _config()
    state = new_run_state(config, created_at_utc=CREATED)
    team = state["teams"]["team-01"]
    team["lab_run_count"] = 7
    team["material_trial_count"] = 6
    team["opening_probe_count"] = 1
    team["comeback_probe_count"] = 1
    team["validation_probe_count"] = 2
    team["probe_locks"] = [
        _probe_lock("candidate-a", HASH_A, "opening"),
        _probe_lock("candidate-b", HASH_B, "comeback"),
    ]
    team["nomination_count"] = 1
    team["nominee_lock"] = {
        "candidate_id": "candidate-b",
        "sha256": HASH_B,
        "locked_at_utc": CREATED,
    }
    team["private_run_count"] = 1
    team["final_oos_observation_count"] = 1

    validate_run_state(state, config)


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("extra_top_level", "invalid schema"),
        ("wrong_config_hash", "current V3 config"),
        ("opening_over_limit", "opening_probe_count"),
        ("comeback_over_limit", "comeback_probe_count"),
        ("total_mismatch", "does not equal"),
        ("unbound_nominee", "not bound to a consumed probe"),
        ("final_without_private", "final observation without a private run"),
    ),
)
def test_run_state_drift_fails_closed(mutation, message):
    config = _config()
    state = new_run_state(config, created_at_utc=CREATED)
    team = state["teams"]["team-01"]

    if mutation == "extra_top_level":
        state["legacy_state"] = {}
    elif mutation == "wrong_config_hash":
        state["config_sha256"] = "0" * 64
    elif mutation == "opening_over_limit":
        team["opening_probe_count"] = 4
    elif mutation == "comeback_over_limit":
        team["comeback_probe_count"] = 3
    elif mutation == "total_mismatch":
        team["validation_probe_count"] = 1
    elif mutation == "unbound_nominee":
        team["nomination_count"] = 1
        team["nominee_lock"] = {
            "candidate_id": "never-probed",
            "sha256": HASH_A,
            "locked_at_utc": CREATED,
        }
    elif mutation == "final_without_private":
        team["final_oos_observation_count"] = 1

    with pytest.raises(ValueError, match=message):
        validate_run_state(state, config)


def test_contract_has_no_import_of_predecessor_state_module():
    source = (ROOT / TOP40_V3_LAYOUT.contract_source).read_text(encoding="utf-8")
    assert "from crypto_trade.tournament.top40_v2" not in source
    assert "import crypto_trade.tournament.top40_v2" not in source
