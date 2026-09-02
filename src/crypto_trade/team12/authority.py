"""Immutable authority loader for the Top-12 V2 Team 12 winner.

The tournament candidate remains the canonical signal implementation.  Research and live
entrypoints load that exact file only after checking the hashes recorded by the atomic OOS
release.  There is deliberately no second copy of the signal math in ``src/``.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

from crypto_trade.tournament.protocol import TargetStrategy
from crypto_trade.tournament.risk_policy import RiskPolicy, load_risk_policy

TEAM_ID = "team-12"
CANDIDATE_ID = "t12-nbh-center-v1"
STRATEGY_SHA256 = "5402b7d63ae582e58d725722d40ebdc64425a1a069600025c6c044248d804dc4"
RISK_POLICY_SHA256 = "2e422a2f0678725d46811d47a93d6c2e1c867615df6f71d12f86a3c819417685"
SOURCE_BUNDLE_SHA256 = "0aecfcc623649f338dbfcdcbc490a06ba9ac6c7dd9301ca2fc36eee13a0d2636"
SOURCE_ARCHIVE_SHA256 = "f127903fc5a9b0db129e4a9dc5709a59b2275f049179bcc96c939061396c5217"
DATA_MANIFEST_SHA256 = "0ced737d1ee62f5a45470c7e363510d4e30aa5a9eb98f82cd17df94caac31198"
DEPENDENCY_LOCK_SHA256 = (
    "869cd3380346a9c9a219fc762868e23cd494a18e22dd9b314ba18621d991faa5"
)
EVALUATOR_AUTHORITY_SHA256 = (
    "c2a314c7209ac8d06574da6533028dc2fd31914e7c08047dbea09290c0c7668a"
)
PURE_CRYPTO_POLICY_SHA256 = (
    "9459e7dd55bdee32fa4b949db9c219473cb82b8889ed185de5cbe57975d67345"
)
PURE_CRYPTO_MODULE_SHA256 = (
    "fc93c0f26dcbf6304abe028736693ab2bee7430a56c14a8547defff472008192"
)
README_SHA256 = "72e7aa58a5a42f5510e6febe127cf8f46b286cc7ed6144fef6a83427d3a15bf5"
CANDIDATE_METADATA_SHA256 = (
    "29140a2211f67be25e20f717fb701f53f3d4161455d87c56f5c604c0f08323dd"
)

# Golden continuous replay artifacts from the one-shot historical release.
GOLDEN_TARGETS_SHA256 = "6d5a03a851bfcf341657d618232789f3c4474ce2e03e8c11032192420923b182"
GOLDEN_POSITIONS_SHA256 = "862ddbf4aff8a24bf415019b1ed86050b7fbc110bc58ef97616d6e9395da4d9a"
GOLDEN_BAR_RETURNS_SHA256 = "5ac0f2bff972c5a500ffa4449aa1252eb47962795c6b2b32bbfb0d74c45a4347"
GOLDEN_DAILY_RETURNS_SHA256 = (
    "936be2d939ef88e7e8e3fe24dc9ec07dd4e3ab8847a0b5984a20926d324e4745"
)

_EVALUATOR_AUTHORITY_PATHS = (
    "src/crypto_trade/tournament/top12_v2.py",
    "src/crypto_trade/tournament/_strategy_worker_v4.py",
    "src/crypto_trade/tournament/amendment_integrity_v2.py",
    "src/crypto_trade/tournament/runner_top12_v2.py",
    "src/crypto_trade/tournament/engine_v2.py",
    "src/crypto_trade/tournament/layout_top12_v2.py",
    "src/crypto_trade/tournament/metrics_v3.py",
    "src/crypto_trade/tournament/protocol.py",
    "src/crypto_trade/tournament/pure_crypto_universe_v6.py",
    "src/crypto_trade/tournament/risk_policy.py",
    "src/crypto_trade/tournament/scoring_top12_v2.py",
    "src/crypto_trade/tournament/source_archive_top12_v2.py",
    "src/crypto_trade/tournament/top12_universe_v1.py",
)
_DEPLOYMENT_BUNDLE_PATHS = (
    ".agents/skills/team12-monitor/SKILL.md",
    ".agents/skills/team12-monitor/agents/openai.yaml",
    "run_team12_paper.py",
    "scripts/team12_backtest.py",
    "scripts/team12_paper_digest.py",
    "scripts/team12_paper_healthcheck.py",
    "scripts/team12_paper_watchdog.sh",
    "src/crypto_trade/backtest_report.py",
    "src/crypto_trade/team12/__init__.py",
    "src/crypto_trade/team12/authority.py",
    "src/crypto_trade/team12/backtest.py",
    "src/crypto_trade/team12/live.py",
    "src/crypto_trade/team12/live_data.py",
    "src/crypto_trade/team12/report.py",
)
DEPLOYMENT_MANIFEST_RELATIVE_PATH = (
    "tournament/top12-v2/team12-deployment-manifest.json"
)


def repository_root() -> Path:
    """Return the worktree root containing ``src/crypto_trade``."""

    return Path(__file__).resolve().parents[3]


def candidate_root(root: str | Path | None = None) -> Path:
    base = Path(root).resolve() if root is not None else repository_root()
    return (
        base
        / "tournament"
        / "top12-v2"
        / "teams"
        / TEAM_ID
        / "candidates"
        / CANDIDATE_ID
    )


def release_team_root(root: str | Path | None = None) -> Path:
    base = Path(root).resolve() if root is not None else repository_root()
    return (
        base
        / "reports-top12-v2"
        / "amendment-0001"
        / "historical-oos"
        / "teams"
        / TEAM_ID
    )


def snapshot_root(root: str | Path | None = None) -> Path:
    base = Path(root).resolve() if root is not None else repository_root()
    return base / "data" / "top12" / "snapshot-v1"


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bundle_digest(entries: dict[str, str]) -> str:
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
class DeploymentAuthority:
    bundle_sha256: str
    manifest_sha256: str
    git_commit: str


def _git_output(base: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ("git", "-C", str(base), *arguments),
        check=False,
        capture_output=True,
    )
    if completed.returncode:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Team 12 Git authority check failed: {detail}")
    return completed.stdout


def verify_deployment_authority(
    root: str | Path | None = None,
) -> DeploymentAuthority:
    """Bind every deployment adapter and monitor byte to a committed manifest."""

    base = Path(root).resolve() if root is not None else repository_root()
    manifest_path = base / DEPLOYMENT_MANIFEST_RELATIVE_PATH
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"Team 12 deployment manifest is missing: {manifest_path}"
        )
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError("Team 12 deployment manifest is malformed") from exc
    expected_top_level = {"schema_version", "candidate_id", "files"}
    if not isinstance(payload, dict) or set(payload) != expected_top_level:
        raise RuntimeError("Team 12 deployment manifest has an invalid schema")
    if payload["schema_version"] != "team12-deployment-authority-v1":
        raise RuntimeError("Team 12 deployment manifest has an unknown version")
    if payload["candidate_id"] != CANDIDATE_ID:
        raise RuntimeError("Team 12 deployment manifest names the wrong candidate")
    file_entries = payload["files"]
    if not isinstance(file_entries, list):
        raise RuntimeError("Team 12 deployment manifest files must be a list")

    expected_paths = set(_DEPLOYMENT_BUNDLE_PATHS)
    observed_paths: set[str] = set()
    hashes: dict[str, str] = {}
    mismatches: list[str] = []
    for entry in file_entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256", "size"}:
            raise RuntimeError("Team 12 deployment manifest has an invalid file entry")
        relative = entry["path"]
        expected_hash = entry["sha256"]
        expected_size = entry["size"]
        if (
            not isinstance(relative, str)
            or not isinstance(expected_hash, str)
            or len(expected_hash) != 64
            or not isinstance(expected_size, int)
            or isinstance(expected_size, bool)
            or expected_size < 0
        ):
            raise RuntimeError("Team 12 deployment manifest file metadata is invalid")
        if relative in observed_paths:
            raise RuntimeError(f"duplicate Team 12 deployment path: {relative}")
        observed_paths.add(relative)
        if relative not in expected_paths:
            mismatches.append(f"unexpected path {relative}")
            continue
        path = base / relative
        if not path.is_file():
            mismatches.append(f"missing path {relative}")
            continue
        actual_size = path.stat().st_size
        actual_hash = sha256_file(path)
        hashes[relative] = actual_hash
        if actual_size != expected_size:
            mismatches.append(f"{relative} size {actual_size} != {expected_size}")
        if actual_hash != expected_hash:
            mismatches.append(f"{relative} sha256 {actual_hash} != {expected_hash}")
    for missing in sorted(expected_paths - observed_paths):
        mismatches.append(f"manifest omits {missing}")
    if mismatches:
        raise RuntimeError("Team 12 deployment-authority drift: " + "; ".join(mismatches))

    committed_manifest = _git_output(
        base,
        "show",
        f"HEAD:{DEPLOYMENT_MANIFEST_RELATIVE_PATH}",
    )
    working_manifest = manifest_path.read_bytes()
    if committed_manifest != working_manifest:
        raise RuntimeError(
            "Team 12 deployment manifest differs from the committed HEAD version"
        )
    manifest_commit = (
        _git_output(
            base,
            "log",
            "-1",
            "--format=%H",
            "--",
            DEPLOYMENT_MANIFEST_RELATIVE_PATH,
        )
        .decode("ascii")
        .strip()
    )
    if len(manifest_commit) != 40:
        raise RuntimeError("Team 12 deployment manifest has no Git commit anchor")
    return DeploymentAuthority(
        bundle_sha256=_bundle_digest(hashes),
        manifest_sha256=hashlib.sha256(working_manifest).hexdigest(),
        git_commit=manifest_commit,
    )


def deployment_bundle_sha256(root: str | Path | None = None) -> str:
    """Return the verified, Git-anchored deployment bundle identity."""

    return verify_deployment_authority(root).bundle_sha256


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
    deployment_bundle_sha256: str
    deployment_manifest_sha256: str
    deployment_git_commit: str


def verify_frozen_authority(root: str | Path | None = None) -> FrozenAuthority:
    """Fail closed unless every locally load-bearing frozen identity is intact."""

    base = Path(root).resolve() if root is not None else repository_root()
    deployment = verify_deployment_authority(base)
    candidate = candidate_root(base)
    strategy = candidate / "strategy.py"
    risk_policy = candidate / "risk_policy.json"
    readme = candidate / "README.md"
    candidate_metadata = candidate / "candidate.json"
    dependency_lock = base / "uv.lock"
    archive = (
        base
        / "reports-top12-v2"
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
        raise FileNotFoundError(f"Team 12 frozen authority is incomplete: {missing}")

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
        raise RuntimeError("Team 12 frozen-authority drift: " + "; ".join(mismatches))

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
        deployment_bundle_sha256=deployment.bundle_sha256,
        deployment_manifest_sha256=deployment.manifest_sha256,
        deployment_git_commit=deployment.git_commit,
    )


def _load_strategy_module(authority: FrozenAuthority) -> ModuleType:
    module_name = f"_crypto_trade_frozen_team12_{authority.strategy_sha256[:16]}"
    # Always create a clean module.  Stateful strategy instances must never leak between replays.
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, authority.strategy_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load frozen Team 12 strategy: {authority.strategy_path}")
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
        raise TypeError("frozen Team 12 strategy has no callable build_strategy()")
    strategy = factory()
    if not callable(getattr(strategy, "target_weights", None)):
        raise TypeError("frozen Team 12 build_strategy() returned an invalid strategy")
    return strategy


def load_frozen_risk_policy(root: str | Path | None = None) -> RiskPolicy:
    authority = verify_frozen_authority(root)
    return load_risk_policy(authority.risk_policy_path)
