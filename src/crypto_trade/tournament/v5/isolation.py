"""Permission profiles for the two Top-40 V5 research phases.

V5 gives each lane a networked scouting phase so teams can research the professional literature
rather than reinvent a mechanism from nothing. That introduces the one combination earlier editions
never had to reason about: a process with **both** internet access and a filesystem inside the
tournament.

The rule that makes it safe is that those two never overlap. The scouting profile has the network
and no evaluation surface; the offline profile has the evaluation surface and no network. Neither
can carry anything out.

Concretely, the scouting profile deliberately does **not** mount the team root. The offline profile
mounts it whole -- which necessarily includes ``feedback/`` -- and a networked process able to read
lane-local evaluation results is an exfiltration channel regardless of anyone's intent. Scouting
therefore mounts three named briefing files and a scratch directory, and nothing else.

The invariants below are asserted rather than described. ``assert_profile_invariants`` is called by
the launcher before every phase, so a profile that drifts into overlapping the wrong surface fails
at launch instead of silently working.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

OFFLINE_PROFILE_NAME = "top40-v5-offline-team"
SCOUTING_PROFILE_NAME = "top40-v5-scouting-team"

SCOUTING_PHASE = "scouting"
RESEARCH_PHASES = ("discovery", "refinement", "decision")

READ = "read"
WRITE = "write"

# Capabilities disabled in every phase. A research lane has no business driving a browser, spawning
# sub-agents, or loading plugins, and each of those is a path around the filesystem profile.
_DISABLED_ALWAYS = (
    "apps",
    "auth_elicitation",
    "browser_use",
    "browser_use_external",
    "browser_use_full_cdp_access",
    "computer_use",
    "hooks",
    "image_generation",
    "in_app_browser",
    "multi_agent",
    "multi_agent_v2",
    "plugin_sharing",
    "plugins",
    "recommended_plugins",
    "remote_plugin",
    "skill_search",
    "tool_call_mcp_elicitation",
)

# Disabled offline, permitted while scouting -- it is the entire point of that phase.
_WEB_SEARCH_CAPABILITY = "standalone_web_search"

# Lane subdirectories that carry evaluation state. A networked process must not be able to read any
# of them, so the scouting mount is checked against this list rather than against a remembered rule.
EVALUATION_SURFACE = ("feedback", "candidates", "outbox", "work")

# The only lane files a scouting process may read: its access policy, its brief, and its mandate.
SCOUTING_READABLE_FILES = ("ACCESS-POLICY.json", "TEAM-BRIEF.md", "SCOUTING-BRIEF.md")


class IsolationError(RuntimeError):
    """A permission profile does not satisfy an invariant the edition depends on."""


@dataclasses.dataclass(frozen=True, slots=True)
class PermissionProfile:
    name: str
    phase: str
    filesystem: Mapping[str, str]
    network_enabled: bool
    web_search: bool
    disabled_capabilities: tuple[str, ...]

    def readable(self) -> tuple[str, ...]:
        return tuple(
            sorted(path for path, mode in self.filesystem.items() if mode in (READ, WRITE))
        )

    def writable(self) -> tuple[str, ...]:
        return tuple(sorted(path for path, mode in self.filesystem.items() if mode == WRITE))

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "phase": self.phase,
            "filesystem": dict(sorted(self.filesystem.items())),
            "network": {"enabled": self.network_enabled},
            "web_search": self.web_search,
            "disabled_capabilities": list(self.disabled_capabilities),
        }

    def sha256(self) -> str:
        payload = json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


def _lane(root: Path, team_root: str) -> Path:
    return (root / team_root).resolve()


def offline_profile(
    root: str | Path, team_root: str, kit_root: str, *, toolchain_root: str | Path
) -> PermissionProfile:
    """The research clean room: the whole lane, and no network."""

    resolved = Path(root).resolve()
    lane = _lane(resolved, team_root)
    filesystem = {
        ":minimal": READ,
        str(Path(toolchain_root).resolve()): READ,
        str((resolved / kit_root).resolve()): READ,
        str(lane): READ,
        str(lane / "candidates"): WRITE,
        str(lane / "outbox"): WRITE,
        str(lane / "work"): WRITE,
    }
    return PermissionProfile(
        name=OFFLINE_PROFILE_NAME,
        phase="research",
        filesystem=dict(sorted(filesystem.items())),
        network_enabled=False,
        web_search=False,
        disabled_capabilities=(*_DISABLED_ALWAYS, _WEB_SEARCH_CAPABILITY),
    )


def scouting_profile(
    root: str | Path, team_root: str, kit_root: str, *, toolchain_root: str | Path
) -> PermissionProfile:
    """The networked literature phase: no evaluation surface, and no market data.

    Note what is absent. The lane root is not mounted, so ``feedback/`` cannot be read; the
    candidate and outbox directories are not writable, so a networked session cannot author
    executable source or a broker request. It gets three briefing files and a scratch directory.
    """

    resolved = Path(root).resolve()
    lane = _lane(resolved, team_root)
    filesystem: dict[str, str] = {
        ":minimal": READ,
        str(Path(toolchain_root).resolve()): READ,
        str((resolved / kit_root).resolve()): READ,
        str(lane / "scouting"): WRITE,
    }
    for name in SCOUTING_READABLE_FILES:
        filesystem[str(lane / name)] = READ
    return PermissionProfile(
        name=SCOUTING_PROFILE_NAME,
        phase=SCOUTING_PHASE,
        filesystem=dict(sorted(filesystem.items())),
        network_enabled=True,
        web_search=True,
        disabled_capabilities=_DISABLED_ALWAYS,
    )


def _covers(mounted: str, target: Path) -> bool:
    if mounted.startswith(":"):
        return False
    try:
        target.relative_to(Path(mounted))
    except ValueError:
        return False
    return True


def assert_profile_invariants(
    profile: PermissionProfile,
    *,
    root: str | Path,
    team_root: str,
    forbidden_roots: Sequence[str] = (),
) -> None:
    """Check the properties the edition depends on, at launch, every time.

    A described invariant is one nobody re-checks after the next refactor.
    """

    resolved = Path(root).resolve()
    lane = _lane(resolved, team_root)

    if profile.network_enabled and profile.phase != SCOUTING_PHASE:
        raise IsolationError(f"{profile.name} enables the network outside the scouting phase")
    if profile.web_search and not profile.network_enabled:
        raise IsolationError(f"{profile.name} enables web search without the network")

    if profile.network_enabled:
        for surface in EVALUATION_SURFACE:
            target = lane / surface
            for mounted in profile.filesystem:
                if _covers(mounted, target):
                    raise IsolationError(
                        f"{profile.name} has the network and can reach {surface}/ via {mounted}; "
                        "a networked process must not see lane evaluation state"
                    )
        if str(lane) in profile.filesystem:
            raise IsolationError(
                f"{profile.name} mounts the lane root, which necessarily includes feedback/"
            )

    for forbidden in forbidden_roots:
        target = (resolved / forbidden).resolve()
        for mounted in profile.filesystem:
            if _covers(mounted, target):
                raise IsolationError(f"{profile.name} can reach forbidden root {forbidden}")

    for path in profile.writable():
        if not _covers(str(lane), Path(path)) and Path(path) != lane:
            raise IsolationError(f"{profile.name} may write outside its own lane: {path}")

    missing = set(_DISABLED_ALWAYS) - set(profile.disabled_capabilities)
    if missing:
        raise IsolationError(f"{profile.name} leaves capabilities enabled: {sorted(missing)}")


def assert_phases_are_separated(scouting: PermissionProfile, offline: PermissionProfile) -> None:
    """The network and the evaluation surface must never be held by the same process."""

    if scouting.network_enabled and offline.network_enabled:
        raise IsolationError("both phases have the network")
    if not scouting.network_enabled:
        raise IsolationError("the scouting phase has no network and cannot do its job")
    shared_writes = set(scouting.writable()) & set(offline.writable())
    if shared_writes:
        raise IsolationError(
            f"the networked phase shares a write surface with the research phase: "
            f"{sorted(shared_writes)}"
        )


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def codex_arguments(profile: PermissionProfile) -> list[str]:
    """Render the profile as Codex ``-c`` overrides.

    Ordering matters and is not cosmetic: a prior edition lost a whole run because
    ``--ignore-user-config`` was applied *after* the permission overrides, so the process rebuilt
    its configuration and entered read-only instead of the named profile. The launcher places the
    strict-config flags before every override for that reason.
    """

    entries = ",".join(
        f"{_toml_string(path)}={_toml_string(mode)}"
        for path, mode in sorted(profile.filesystem.items())
    )
    arguments = [
        "-c",
        f"default_permissions={_toml_string(profile.name)}",
        "-c",
        f"permissions.{profile.name}.filesystem={{{entries}}}",
        "-c",
        f"permissions.{profile.name}.network.enabled="
        f"{'true' if profile.network_enabled else 'false'}",
        "-c",
        'approval_policy="never"',
        "-c",
        "allow_login_shell=false",
        "-c",
        "project_doc_max_bytes=0",
        "-c",
        "project_root_markers=[]",
    ]
    for capability in profile.disabled_capabilities:
        arguments.extend(["--disable", capability])
    return arguments


def expected_probe_keys(profile: PermissionProfile) -> frozenset[str]:
    """Probes a live profile must pass before a phase may launch."""

    common = {
        "allowed_reads",
        "denied_reads",
        "cross_lane_write_denied",
        "own_lane_write_allowed",
        "host_process_hidden",
        "host_skill_roots_denied",
        "skill_catalog_empty",
    }
    if profile.network_enabled:
        return frozenset(common | {"network_allowed", "evaluation_surface_denied"})
    return frozenset(common | {"network_denied"})


__all__ = [
    "EVALUATION_SURFACE",
    "OFFLINE_PROFILE_NAME",
    "RESEARCH_PHASES",
    "SCOUTING_PHASE",
    "SCOUTING_PROFILE_NAME",
    "SCOUTING_READABLE_FILES",
    "IsolationError",
    "PermissionProfile",
    "assert_phases_are_separated",
    "assert_profile_invariants",
    "codex_arguments",
    "expected_probe_keys",
    "offline_profile",
    "scouting_profile",
]
