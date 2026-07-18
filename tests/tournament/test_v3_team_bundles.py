from __future__ import annotations

import importlib.util
import inspect
import json
import sys
from pathlib import Path

from crypto_trade.tournament.risk_policy import load_risk_policy


ROOT = Path(__file__).parents[2]
TEAM_ROOT = ROOT / "tournament/top40-v3/teams"
TEAM_IDS = tuple(f"team-{number:02d}" for number in range(1, 11))


def _config(team_id: str) -> dict[str, object]:
    payload = json.loads((TEAM_ROOT / team_id / "frozen_config.json").read_text())
    assert isinstance(payload, dict)
    return payload


def test_all_ten_executable_bundles_have_unique_v3_identity_and_valid_risk() -> None:
    candidate_ids: set[str] = set()
    for team_id in TEAM_IDS:
        team_dir = TEAM_ROOT / team_id
        assert team_dir.is_dir() and not team_dir.is_symlink()
        config = _config(team_id)
        assert config["artifact"] == "frozen_reference_config"
        assert config["candidate_status"] == "transparent_baseline_not_yet_evaluated"
        assert config["team_id"] == team_id
        assert config["seed"] == 20260718
        assert config["schema_version"] == 1
        assert config["implementation"] == {
            "build_factory": "build_strategy",
            "entrypoint": "strategy.py",
            "stateful": False,
        }
        candidate_id = config["candidate_id"]
        assert isinstance(candidate_id, str) and candidate_id not in candidate_ids
        candidate_ids.add(candidate_id)

        risk_binding = config["risk_policy"]
        assert isinstance(risk_binding, dict)
        assert risk_binding["path"] == "risk_policy.json"
        policy = load_risk_policy(team_dir / "risk_policy.json")
        assert policy.policy_id == risk_binding["policy_id"]


def test_all_strategy_factories_expose_the_keyword_only_seed_protocol() -> None:
    for team_id in TEAM_IDS:
        path = TEAM_ROOT / team_id / "strategy.py"
        module_name = f"_top40_v3_bundle_{team_id.replace('-', '_')}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
            strategy = module.build_strategy()
            signature = inspect.signature(strategy.target_weights)
            assert tuple(signature.parameters) == ("context", "seed")
            assert signature.parameters["seed"].kind is inspect.Parameter.KEYWORD_ONLY
        finally:
            sys.modules.pop(module_name, None)
