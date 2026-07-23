"""Immutable authority loader for the Top40 V4-R1 Team 09 winner.

The tournament candidate remains the canonical signal implementation.  Research and live
entrypoints load that exact file only after checking the hashes recorded by the atomic OOS
release.  There is deliberately no second copy of the signal math in ``src/``.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

from crypto_trade.tournament.protocol import TargetStrategy
from crypto_trade.tournament.risk_policy import RiskPolicy, load_risk_policy

TEAM_ID = "team-09"
CANDIDATE_ID = "t09-flow-pressure-long-confirm-voltarget-only-v1"
STRATEGY_SHA256 = "4956e77bc29297904cbe95a800933407172b4c8a15a4267c0fc0eaa72919ff2c"
RISK_POLICY_SHA256 = "8b096e1a959ee24e98a33505670c41716945c10e05f6524767a0d2ebbf1eb472"
SOURCE_BUNDLE_SHA256 = "512dd7a86720cc056774542ccdba9e49423e6c8374a71e9602265d20c5b76512"
SOURCE_ARCHIVE_SHA256 = "bb6a9c2938bd385aea2492752eddc11786a08d7dad4e4748ed4e505d14811b19"
DATA_MANIFEST_SHA256 = "077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3"
DEPENDENCY_LOCK_SHA256 = (
    "869cd3380346a9c9a219fc762868e23cd494a18e22dd9b314ba18621d991faa5"
)
EVALUATOR_AUTHORITY_SHA256 = (
    "59d169a8d47669253162feef4f01ead699d6fc072a878c5a3c3a6fbe144f3633"
)
PURE_CRYPTO_POLICY_SHA256 = (
    "2c7fb0ff593d06c323517e60df4b28ab9387a2df580b83f82f65ef71c91fc350"
)
PURE_CRYPTO_MODULE_SHA256 = (
    "fc93c0f26dcbf6304abe028736693ab2bee7430a56c14a8547defff472008192"
)
README_SHA256 = "75bb84ce690c9afb0ea98ee9b0dcd867757f8599ed98db825c7230bffb1a2dfd"
CANDIDATE_METADATA_SHA256 = (
    "16beb6fd7ef7401e35a00405616baa1100c49e3e6fbfdd4e8eaa17e2e0f110ce"
)

# Golden continuous replay artifacts from the one-shot historical release.
GOLDEN_TARGETS_SHA256 = "c17b1fe392bc527bab14c46020ce5516fd31eddcb828f868bcbe016605d5bdbc"
GOLDEN_POSITIONS_SHA256 = "1de088875ad9bab7dcbf659a70b9917b4a9a3d6cdf3237b5b83f0fd1467d868b"
GOLDEN_BAR_RETURNS_SHA256 = "deffd95aa6d09ba0a4dede606524c2124775a4cadc0313482685601be707c9bc"
GOLDEN_DAILY_RETURNS_SHA256 = (
    "293de262b29c6a7b6d81e9800cbc054caf2d0794bb94b5d1c1f349313bbb33fe"
)

_EVALUATOR_AUTHORITY_PATHS = (
    "src/crypto_trade/tournament/top40_v4.py",
    "src/crypto_trade/tournament/_strategy_worker_v4.py",
    "src/crypto_trade/tournament/amendment_integrity_v2.py",
    "src/crypto_trade/tournament/runner_v4.py",
    "src/crypto_trade/tournament/engine_v2.py",
    "src/crypto_trade/tournament/layout_v4.py",
    "src/crypto_trade/tournament/metrics_v3.py",
    "src/crypto_trade/tournament/protocol.py",
    "src/crypto_trade/tournament/pure_crypto_universe_v6.py",
    "src/crypto_trade/tournament/risk_policy.py",
    "src/crypto_trade/tournament/scoring_v4.py",
    "src/crypto_trade/tournament/source_archive_v4.py",
)
_DEPLOYMENT_BUNDLE_PATHS = (
    ".agents/skills/team09-monitor/SKILL.md",
    ".agents/skills/team09-monitor/agents/openai.yaml",
    ".claude/commands/team09-monitor.md",
    ".claude/skills/team09-monitor/SKILL.md",
    ".claude/skills/team09-monitor/agents/openai.yaml",
    "run_team09_paper.py",
    "scripts/team09_backtest.py",
    "scripts/team09_paper_digest.py",
    "scripts/team09_paper_healthcheck.py",
    "scripts/team09_paper_watchdog.sh",
    "src/crypto_trade/backtest_report.py",
    "src/crypto_trade/team09/__init__.py",
    "src/crypto_trade/team09/authority.py",
    "src/crypto_trade/team09/backtest.py",
    "src/crypto_trade/team09/live.py",
    "src/crypto_trade/team09/live_data.py",
    "src/crypto_trade/team09/report.py",
)


def repository_root() -> Path:
    """Return the worktree root containing ``src/crypto_trade``."""

    return Path(__file__).resolve().parents[3]


def candidate_root(root: str | Path | None = None) -> Path:
    base = Path(root).resolve() if root is not None else repository_root()
    return (
        base
        / "tournament"
        / "top40-v4-r1"
        / "teams"
        / TEAM_ID
        / "candidates"
        / CANDIDATE_ID
    )


def release_team_root(root: str | Path | None = None) -> Path:
    base = Path(root).resolve() if root is not None else repository_root()
    return base / "reports-top40-v4-r1" / "historical-oos" / "teams" / TEAM_ID


def snapshot_root(root: str | Path | None = None) -> Path:
    base = Path(root).resolve() if root is not None else repository_root()
    return base / "data" / "top40" / "snapshot-v1"


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def deployment_bundle_sha256(root: str | Path | None = None) -> str:
    """Hash every Team 09 adapter/report/monitor byte used by the deployed desk."""

    base = Path(root).resolve() if root is not None else repository_root()
    entries = {
        relative: sha256_file(base / relative)
        for relative in _DEPLOYMENT_BUNDLE_PATHS
    }
    return hashlib.sha256(
        json.dumps(
            entries,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


@dataclasses.dataclass(frozen=True)
class FrozenAuthority:
    candidate_id: str
    strategy_path: Path
    strategy_sha256: str
    risk_policy_path: Path
    risk_policy_sha256: str
    source_archive_path: Path
    source_archive_sha256: str
    source_archive_present: bool
    source_bundle_sha256: str
    dependency_lock_sha256: str
    data_manifest_sha256: str
    evaluator_authority_sha256: str
    pure_crypto_policy_sha256: str


def verify_frozen_authority(root: str | Path | None = None) -> FrozenAuthority:
    """Fail closed unless every locally load-bearing frozen identity is intact."""

    base = Path(root).resolve() if root is not None else repository_root()
    candidate = candidate_root(base)
    strategy = candidate / "strategy.py"
    risk_policy = candidate / "risk_policy.json"
    readme = candidate / "README.md"
    candidate_metadata = candidate / "candidate.json"
    dependency_lock = base / "uv.lock"
    archive = (
        base
        / "reports-top40-v4-r1"
        / "source-archives"
        / "sha256"
        / f"{SOURCE_ARCHIVE_SHA256}.json"
    )
    required = (
        strategy,
        risk_policy,
        readme,
        candidate_metadata,
        archive,
        dependency_lock,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Team 09 frozen authority is incomplete: {missing}")

    actual_strategy = sha256_file(strategy)
    actual_policy = sha256_file(risk_policy)
    actual_readme = sha256_file(readme)
    actual_candidate_metadata = sha256_file(candidate_metadata)
    actual_dependency_lock = sha256_file(dependency_lock)
    archive_present = archive.is_file()
    actual_archive = sha256_file(archive)
    evaluator_authority = {
        relative: sha256_file(base / relative) for relative in _EVALUATOR_AUTHORITY_PATHS
    }
    evaluator_sha256 = hashlib.sha256(
        json.dumps(
            evaluator_authority,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    mismatches: list[str] = []
    if actual_strategy != STRATEGY_SHA256:
        mismatches.append(f"strategy {actual_strategy} != {STRATEGY_SHA256}")
    if actual_policy != RISK_POLICY_SHA256:
        mismatches.append(f"risk policy {actual_policy} != {RISK_POLICY_SHA256}")
    if actual_readme != README_SHA256:
        mismatches.append(f"README {actual_readme} != {README_SHA256}")
    if actual_candidate_metadata != CANDIDATE_METADATA_SHA256:
        mismatches.append(
            f"candidate metadata {actual_candidate_metadata} != {CANDIDATE_METADATA_SHA256}"
        )
    if actual_dependency_lock != DEPENDENCY_LOCK_SHA256:
        mismatches.append(
            f"dependency lock {actual_dependency_lock} != {DEPENDENCY_LOCK_SHA256}"
        )
    if actual_archive != SOURCE_ARCHIVE_SHA256:
        mismatches.append(f"source archive {actual_archive} != {SOURCE_ARCHIVE_SHA256}")
    if evaluator_sha256 != EVALUATOR_AUTHORITY_SHA256:
        mismatches.append(
            f"evaluator authority {evaluator_sha256} != {EVALUATOR_AUTHORITY_SHA256}"
        )
    pure_crypto_module = evaluator_authority[
        "src/crypto_trade/tournament/pure_crypto_universe_v6.py"
    ]
    if pure_crypto_module != PURE_CRYPTO_MODULE_SHA256:
        mismatches.append(
            f"pure-crypto module {pure_crypto_module} != {PURE_CRYPTO_MODULE_SHA256}"
        )

    source_entries = [
        {"path": "README.md", "size": readme.stat().st_size, "sha256": actual_readme},
        {
            "path": "candidate.json",
            "size": candidate_metadata.stat().st_size,
            "sha256": actual_candidate_metadata,
        },
        {
            "path": "risk_policy.json",
            "size": risk_policy.stat().st_size,
            "sha256": actual_policy,
        },
        {"path": "strategy.py", "size": strategy.stat().st_size, "sha256": actual_strategy},
    ]
    source_payload = json.dumps(
        source_entries,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    actual_source_bundle = hashlib.sha256(source_payload).hexdigest()
    if actual_source_bundle != SOURCE_BUNDLE_SHA256:
        mismatches.append(
            f"source bundle {actual_source_bundle} != {SOURCE_BUNDLE_SHA256}"
        )
    archive_payload = json.loads(archive.read_text(encoding="utf-8"))
    if archive_payload.get("source_bundle_sha256") != SOURCE_BUNDLE_SHA256:
        mismatches.append("source archive carries the wrong source_bundle_sha256")
    if mismatches:
        raise RuntimeError("Team 09 frozen-authority drift: " + "; ".join(mismatches))

    return FrozenAuthority(
        candidate_id=CANDIDATE_ID,
        strategy_path=strategy,
        strategy_sha256=actual_strategy,
        risk_policy_path=risk_policy,
        risk_policy_sha256=actual_policy,
        source_archive_path=archive,
        source_archive_sha256=actual_archive,
        source_archive_present=archive_present,
        source_bundle_sha256=SOURCE_BUNDLE_SHA256,
        dependency_lock_sha256=actual_dependency_lock,
        data_manifest_sha256=DATA_MANIFEST_SHA256,
        evaluator_authority_sha256=evaluator_sha256,
        pure_crypto_policy_sha256=PURE_CRYPTO_POLICY_SHA256,
    )


def _load_strategy_module(authority: FrozenAuthority) -> ModuleType:
    module_name = f"_crypto_trade_frozen_team09_{authority.strategy_sha256[:16]}"
    # Always create a clean module.  Stateful strategy instances must never leak between replays.
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, authority.strategy_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load frozen Team 09 strategy: {authority.strategy_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


def build_frozen_strategy(root: str | Path | None = None) -> TargetStrategy:
    authority = verify_frozen_authority(root)
    module = _load_strategy_module(authority)
    factory = getattr(module, "build_strategy", None)
    if not callable(factory):
        raise TypeError("frozen Team 09 strategy has no callable build_strategy()")
    strategy = factory()
    if not callable(getattr(strategy, "target_weights", None)):
        raise TypeError("frozen Team 09 build_strategy() returned an invalid strategy")
    return strategy


def load_frozen_risk_policy(root: str | Path | None = None) -> RiskPolicy:
    authority = verify_frozen_authority(root)
    return load_risk_policy(authority.risk_policy_path)
