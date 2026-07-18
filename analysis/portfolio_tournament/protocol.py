"""Strategy loading + submission freeze/verification for crypto-cup-01.

A team submission is its ENTIRE source bundle (every ``*.py`` under the team dir, ``out/``
excluded). ``submission.json`` binds SHA-256 per source file; ``check_submission_shas``
re-hashes before any canonical rerun, so post-freeze mutation is mechanically impossible
to sneak past the leaderboard.
"""

from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from portfolio_tournament import constants as tc  # noqa: E402


class SubmissionError(RuntimeError):
    """Submission contract violation (missing entrypoint, SHA mismatch, bad signature)."""


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def strategy_sources(team_dir: Path) -> dict[str, str]:
    """{relative_path: sha256} over every .py in the team dir (out/ artifacts excluded)."""
    team_dir = Path(team_dir)
    out: dict[str, str] = {}
    for p in sorted(team_dir.rglob("*.py")):
        rel = p.relative_to(team_dir)
        if rel.parts[0] in ("out", "__pycache__"):
            continue
        out[str(rel)] = _sha256_bytes(p.read_bytes())
    return out


def purge_team_modules() -> None:
    """Drop every cached module whose file lives under a tournament team dir — prevents
    helper-name collisions (two teams' ``helpers.py``) and forces fresh state per load."""
    for name, mod in list(sys.modules.items()):
        f = getattr(mod, "__file__", None)
        if f and f"{tc.TOURNAMENT_ROOT.name}" in f and "/teams/" in f:
            del sys.modules[name]


def load_strategy(team_dir: Path):
    """Fresh-load ``strategy.py`` from a team dir; validates the entrypoint signature.

    The evaluator package dir is put on sys.path so team code can ``import teamlib`` (the
    only whitelisted non-numeric import — the harness scan enforces the whitelist).
    """
    team_dir = Path(team_dir)
    entry = team_dir / "strategy.py"
    if not entry.exists():
        raise SubmissionError(f"{team_dir.name}: missing strategy.py")
    purge_team_modules()
    for p in (str(team_dir), str(_HERE)):
        if p not in sys.path:
            sys.path.insert(0, p)
    mod_name = f"crypto_cup_{team_dir.name.replace('-', '_')}_strategy"
    sys.modules.pop(mod_name, None)
    spec = importlib.util.spec_from_file_location(mod_name, entry)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    fn = getattr(mod, "build_raw_weights", None)
    if not callable(fn):
        raise SubmissionError(f"{team_dir.name}: strategy.py lacks build_raw_weights()")
    n_params = len(
        [
            p
            for p in inspect.signature(fn).parameters.values()
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        ]
    )
    if n_params != 2:
        raise SubmissionError(
            f"{team_dir.name}: build_raw_weights must take exactly (pn, aux); got {n_params}"
        )
    return mod


def write_submission(
    team_dir: Path,
    *,
    family_id: str,
    reported: dict,
    net_is_csv_sha256: str,
    harness: str,
) -> dict:
    """Freeze record — SHAs computed HERE from the bundle on disk; metrics passed in must
    come straight from ``out/is_metrics.json`` (the CLI enforces that wiring)."""
    team_dir = Path(team_dir)
    sub = {
        "schema": 1,
        "team_id": team_dir.name,
        "family_id": family_id,
        "sources_sha256": strategy_sources(team_dir),
        "reported": reported,
        "net_is_csv_sha256": net_is_csv_sha256,
        "harness": harness,
        "frozen_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    (team_dir / "submission.json").write_text(json.dumps(sub, indent=2, sort_keys=True) + "\n")
    return sub


def read_submission(team_dir: Path) -> dict:
    p = Path(team_dir) / "submission.json"
    if not p.exists():
        raise SubmissionError(f"{Path(team_dir).name}: no submission.json (not frozen)")
    return json.loads(p.read_text())


def check_submission_shas(team_dir: Path) -> dict:
    """Re-hash the bundle against submission.json; raise on ANY drift (post-freeze mutation)."""
    sub = read_submission(team_dir)
    now = strategy_sources(team_dir)
    frozen = sub["sources_sha256"]
    if now != frozen:
        changed = sorted(
            set(now) ^ set(frozen) | {k for k in set(now) & set(frozen) if now[k] != frozen[k]}
        )
        raise SubmissionError(f"{Path(team_dir).name}: post-freeze mutation in {changed}")
    return sub


def approved_families(registry_path: Path = tc.REGISTRY_PATH) -> dict[tuple[str, str], str]:
    """{(team_id, family_id): last status} from the append-only registry."""
    out: dict[tuple[str, str], str] = {}
    if not Path(registry_path).exists():
        return out
    for line in Path(registry_path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        e = json.loads(line)
        out[(e["team_id"], e["family_id"])] = e["status"]
    return out


def require_approved_family(
    team_id: str, family_id: str, registry_path: Path = tc.REGISTRY_PATH
) -> None:
    """Freeze-time gate (tradfi Critic recommendation #1): the family must be registry-approved."""
    status = approved_families(registry_path).get((team_id, family_id))
    if status != "approved":
        raise SubmissionError(
            f"{team_id}: family {family_id!r} is not APPROVED in the registry "
            f"(status={status!r}) — register/approve it before freezing"
        )
