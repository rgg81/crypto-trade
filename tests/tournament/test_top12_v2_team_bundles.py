from __future__ import annotations

import ast
import json
from pathlib import Path

from crypto_trade.tournament import orchestrator_top12_v2, runner_top12_v2, top12_v2
from crypto_trade.tournament.layout_top12_v2 import TOP12_V2_LAYOUT
from crypto_trade.tournament.risk_policy import load_risk_policy

ROOT = Path(__file__).resolve().parents[2]
TEAM_ROOT = ROOT / TOP12_V2_LAYOUT.tournament_root / "teams"


def test_mechanism_registry_has_twelve_distinct_economic_lanes() -> None:
    registry = json.loads(
        (
            ROOT
            / TOP12_V2_LAYOUT.tournament_root
            / "ORCHESTRATOR-MECHANISM-REGISTRY.json"
        ).read_text(encoding="utf-8")
    )
    loaded = top12_v2.load_config(root=ROOT)
    teams = registry["teams"]
    assert registry["visibility"] == "organizer-only-forbidden-to-teams"
    assert len(registry["forbidden_prior_oos_families"]) >= 3
    assert len(
        {row["fingerprint"] for row in registry["forbidden_prior_oos_families"]}
    ) == len(registry["forbidden_prior_oos_families"])
    assert set(teams) == set(TOP12_V2_LAYOUT.team_ids)
    assert {team_id: row["mandate"] for team_id, row in teams.items()} == dict(
        loaded.raw["mandates"]
    )
    assert len({row["mandate"] for row in teams.values()}) == 12
    assert len({row["economic_payoff"] for row in teams.values()}) == 12
    assert len({row["primary_structure"] for row in teams.values()}) == 12


def test_all_twelve_lanes_have_one_valid_baseline_bundle() -> None:
    loaded = top12_v2.load_config(root=ROOT)
    candidate_ids: set[str] = set()
    policy_ids: set[str] = set()
    for team_id in TOP12_V2_LAYOUT.team_ids:
        candidates = sorted((TEAM_ROOT / team_id / "candidates").glob("*/strategy.py"))
        assert candidates
        baselines = 0
        for strategy_path in candidates:
            entrypoint = strategy_path.relative_to(ROOT).as_posix()
            metadata, _relative = orchestrator_top12_v2._candidate_metadata(
                ROOT, loaded.raw, team_id, entrypoint
            )
            baselines += "baseline" in metadata["tags"]
            assert metadata["candidate_id"] not in candidate_ids
            candidate_ids.add(metadata["candidate_id"])
            capture = runner_top12_v2.capture_source_bundle(ROOT, team_id, entrypoint)
            assert capture.entrypoint == "strategy.py"
            assert {item.path for item in capture.files} >= {
                "README.md",
                "candidate.json",
                "risk_policy.json",
                "strategy.py",
            }
            policy = load_risk_policy(strategy_path.parent / "risk_policy.json")
            assert policy.policy_id not in policy_ids
            policy_ids.add(policy.policy_id)
        assert baselines >= 1


def test_all_strategy_factories_implement_keyword_only_seed_protocol() -> None:
    for team_id in TOP12_V2_LAYOUT.team_ids:
        for path in sorted((TEAM_ROOT / team_id / "candidates").glob("*/strategy.py")):
            # Activation must never import untrusted team code in the organizer process. The
            # actual factory and protocol are exercised only inside runner_top12_v2's sealed worker.
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            factories = [
                node
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == "build_strategy"
            ]
            assert len(factories) == 1
            factory = factories[0]
            assert isinstance(factory, ast.FunctionDef)
            assert not factory.args.posonlyargs
            assert not factory.args.args
            assert factory.args.vararg is None
            assert not factory.args.kwonlyargs
            assert factory.args.kwarg is None

            methods = [
                node
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == "target_weights"
            ]
            assert len(methods) == 1
            method = methods[0]
            assert isinstance(method, ast.FunctionDef)
            assert [argument.arg for argument in method.args.args] == ["self", "context"]
            assert method.args.vararg is None
            assert [argument.arg for argument in method.args.kwonlyargs] == ["seed"]
            assert method.args.kwarg is None
