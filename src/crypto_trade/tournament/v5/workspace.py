"""Materialised team workspaces: deny by absence rather than by policy.

Earlier editions left every file in the repository and relied on the agent runtime's permission
rules to refuse the forbidden ones. That is deny-by-policy, and it fails open: V4-R2 lost an entire
run when a Codex skill catalogue became readable inside all fifteen lanes, because the files were
present and the policy did not cover them.

A materialised workspace inverts that. Before a phase runs, the organizer copies **only** the
permitted bytes into a fresh directory, and the process runs with that directory as its world. A
peer lane, a prior edition, the market snapshot and the repository history are not denied — they are
not there. No policy failure can expose a file that was never copied.

What this does and does not guarantee, stated plainly, because the distinction is the whole point:

* **Prevention, verified.** Network denial for research phases comes from a network namespace, which
  is enforced by the kernel. A process inside it cannot open a socket, whatever it intends.
* **Prevention, structural.** Relative paths cannot leave the workspace, and the forbidden files do
  not exist inside it. This is what materialisation buys.
* **Detection, not prevention.** An absolute path out of the workspace remains readable on this
  host, because bind mounts and chroot are unavailable inside an unprivileged user namespace here.
  :func:`audit_workspace` therefore checks the harvested artifacts for references outside the lane,
  and the honest statement is CUP-20's: a clean audit means the mechanical checks found no evidence
  of a read, not that no read occurred.

The runtime is a parameter, not a dependency. Nothing in this module knows which agent CLI executes
inside the workspace.
"""

from __future__ import annotations

import dataclasses
import hashlib
import os
import re
import shutil
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

WORKSPACE_KIT = "team-kit"
WORKSPACE_LANE = "lane"

# Subdirectories a research phase may write into, created empty in every workspace.
LANE_WRITABLE = ("candidates", "outbox", "work")
# The scouting phase gets exactly one, and no evaluation surface at all.
SCOUTING_WRITABLE = ("scouting",)


class WorkspaceError(RuntimeError):
    """A workspace could not be materialised, or its contents are not what was declared."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclasses.dataclass(frozen=True, slots=True)
class Workspace:
    """A materialised, self-contained world for one phase of one lane."""

    root: Path
    lane: Path
    kit: Path
    phase: str
    network: bool
    manifest: Mapping[str, str]

    def relative(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def as_dict(self) -> dict[str, object]:
        return {
            "phase": self.phase,
            "network": self.network,
            "file_count": len(self.manifest),
            "manifest_sha256": hashlib.sha256(
                "\n".join(
                    f"{name}:{digest}" for name, digest in sorted(self.manifest.items())
                ).encode("utf-8")
            ).hexdigest(),
        }


def _copy_into(source: Path, destination: Path, manifest: dict[str, str], root: Path) -> None:
    if source.is_dir():
        for child in sorted(source.rglob("*")):
            if child.is_dir() or child.is_symlink():
                continue
            target = destination / child.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(child, target)
            manifest[target.relative_to(root).as_posix()] = _sha256(target)
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    manifest[destination.relative_to(root).as_posix()] = _sha256(destination)


def materialise(
    destination: str | Path,
    *,
    phase: str,
    kit_source: str | Path,
    lane_files: Mapping[str, str | Path],
    writable: Sequence[str],
    network: bool,
) -> Workspace:
    """Build a fresh workspace containing exactly the permitted bytes.

    ``lane_files`` maps a name inside the lane to the file it is copied from, so a caller has to
    name every readable file individually. Handing over a directory would let whatever happens to
    be inside it enter the lane, which is the accident that leaked a skill catalogue into fifteen
    lanes in a prior edition.
    """

    root = Path(destination).resolve()
    if root.exists() and any(root.iterdir()):
        raise WorkspaceError(f"workspace destination is not empty: {root}")
    if any(Path(name).is_absolute() or ".." in Path(name).parts for name in lane_files):
        raise WorkspaceError("lane file names must be relative and must not traverse upward")

    lane = root / WORKSPACE_LANE
    kit = root / WORKSPACE_KIT
    lane.mkdir(parents=True, exist_ok=True)
    kit.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, str] = {}
    _copy_into(Path(kit_source).resolve(), kit, manifest, root)
    for name, source in lane_files.items():
        _copy_into(Path(source).resolve(), lane / name, manifest, root)
    for name in writable:
        (lane / name).mkdir(parents=True, exist_ok=True)

    return Workspace(root=root, lane=lane, kit=kit, phase=phase, network=network, manifest=manifest)


def harvest(
    workspace: Workspace, directory: str, *, expected: Iterable[str] = ()
) -> dict[str, bytes]:
    """Read the artifacts a phase produced, and nothing else.

    Only files directly inside the named lane subdirectory are returned. A phase that wrote
    somewhere unexpected produces nothing here rather than silently contributing it.
    """

    source = workspace.lane / directory
    if not source.is_dir():
        raise WorkspaceError(f"workspace has no {directory}/ to harvest")
    produced = {
        item.name: item.read_bytes()
        for item in sorted(source.iterdir())
        if item.is_file() and not item.is_symlink()
    }
    missing = [name for name in expected if name not in produced]
    if missing:
        raise WorkspaceError(f"phase did not produce required artifacts: {missing}")
    return produced


def assert_workspace_excludes(workspace: Workspace, forbidden: Sequence[str]) -> None:
    """No forbidden name may appear anywhere in the materialised tree.

    Checked after materialising rather than trusted: the point of deny-by-absence is that it can
    be verified by looking, which deny-by-policy never can.
    """

    present = {Path(name).name for name in workspace.manifest}
    offending = sorted(set(forbidden) & present)
    if offending:
        raise WorkspaceError(f"workspace contains forbidden files: {offending}")


_ABSOLUTE_PATH = re.compile(rb"(?:/[A-Za-z0-9._-]+){2,}")


def audit_workspace(
    workspace: Workspace, produced: Mapping[str, bytes], *, forbidden_roots: Sequence[str]
) -> list[str]:
    """Look for references that would only make sense if something outside had been read.

    This is **detection, not prevention**. On this host an absolute path out of the workspace stays
    readable, because bind mounts and chroot are unavailable in an unprivileged user namespace. A
    clean result means the mechanical checks found no evidence of a read, not that none occurred --
    the same caveat CUP-20 recorded about its own sealed-window review.
    """

    findings: list[str] = []
    for name, payload in sorted(produced.items()):
        for root in forbidden_roots:
            if root.encode("utf-8") in payload:
                findings.append(f"{name}: references forbidden root {root}")
        for match in _ABSOLUTE_PATH.findall(payload):
            candidate = match.decode("utf-8", "replace")
            if candidate.startswith(str(workspace.root)):
                continue
            if any(candidate.startswith(root) for root in ("/usr", "/lib", "/bin", "/etc")):
                continue
            findings.append(f"{name}: absolute path outside the workspace: {candidate}")
    return sorted(set(findings))


def network_isolated_command(command: Sequence[str], *, network: bool) -> list[str]:
    """Wrap a command so a research phase genuinely cannot open a socket.

    ``unshare --net`` places the process in an empty network namespace, which the kernel enforces;
    it is the one part of this design that is prevention rather than detection. The scouting phase
    is deliberately not wrapped -- reaching the public literature is the entire point of it.
    """

    if network:
        return list(command)
    return ["unshare", "--user", "--map-root-user", "--net", *command]


def clean_environment(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    """A minimal environment. Whatever is not passed cannot be read from the parent's."""

    keep = ("PATH", "HOME", "LANG", "LC_ALL", "TERM", "TMPDIR")
    environment = {name: os.environ[name] for name in keep if name in os.environ}
    # Single-threaded numerics keep an evaluation reproducible across hosts.
    for variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        environment[variable] = "1"
    environment.update(extra or {})
    return environment


__all__ = [
    "LANE_WRITABLE",
    "SCOUTING_WRITABLE",
    "WORKSPACE_KIT",
    "WORKSPACE_LANE",
    "Workspace",
    "WorkspaceError",
    "assert_workspace_excludes",
    "audit_workspace",
    "clean_environment",
    "harvest",
    "materialise",
    "network_isolated_command",
]
