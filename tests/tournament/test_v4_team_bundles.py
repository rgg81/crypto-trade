from __future__ import annotations

import ast
from pathlib import Path

from crypto_trade.tournament import orchestrator_v4, runner_v4, top40_v4
from crypto_trade.tournament.layout_v4 import TOP40_V4_LAYOUT
from crypto_trade.tournament.risk_policy import load_risk_policy

ROOT = Path(__file__).resolve().parents[2]
TEAM_ROOT = ROOT / TOP40_V4_LAYOUT.tournament_root / "teams"


def test_all_twelve_lanes_have_one_valid_baseline_bundle() -> None:
    loaded = top40_v4.load_config(root=ROOT)
    candidate_ids: set[str] = set()
    policy_ids: set[str] = set()
    for team_id in TOP40_V4_LAYOUT.team_ids:
        candidates = sorted((TEAM_ROOT / team_id / "candidates").glob("*/strategy.py"))
        assert candidates
        baselines = 0
        for strategy_path in candidates:
            entrypoint = strategy_path.relative_to(ROOT).as_posix()
            metadata, _relative = orchestrator_v4._candidate_metadata(
                ROOT, loaded.raw, team_id, entrypoint
            )
            baselines += "baseline" in metadata["tags"]
            assert metadata["candidate_id"] not in candidate_ids
            candidate_ids.add(metadata["candidate_id"])
            capture = runner_v4.capture_source_bundle(ROOT, team_id, entrypoint)
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
    for team_id in TOP40_V4_LAYOUT.team_ids:
        for path in sorted((TEAM_ROOT / team_id / "candidates").glob("*/strategy.py")):
            # Activation must never import untrusted team code in the organizer process. The
            # actual factory and protocol are exercised only inside runner_v4's sealed worker.
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
