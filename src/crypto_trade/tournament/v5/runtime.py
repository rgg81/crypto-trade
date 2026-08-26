"""Launching a research phase, without depending on any one agent CLI.

Earlier editions hard-wired Codex, so a change in one vendor's flag handling could take the whole
tournament down -- and did: a run was lost because ``--ignore-user-config`` was applied after the
permission overrides and the process silently rebuilt its configuration into the wrong profile.

Here the runtime is a parameter. :class:`AgentRuntime` is the whole contract, and everything the
orchestrator does is expressed against it. Two implementations ship: :class:`ClaudeCodeRuntime`,
which drives the ``claude`` CLI headlessly, and :class:`ScriptedRuntime`, which executes a plain
Python callable. The second is not a toy -- it lets the entire orchestrator, journal and selection
path be tested end to end with no model in the loop, which is what makes the readiness load
affordable to run on every change.

Three findings from probing this host shaped the design, and each is a guard rather than a comment.

**A research phase cannot be put in a network namespace.** The agent needs the network to reach its
own model API; ``unshare --net`` starves it and the process simply hangs. Network denial is
therefore *tool-level* -- withholding the search and fetch tools -- and this module says so in
:data:`NETWORK_TOOLS` instead of implying a kernel guarantee it does not have.

**A malformed permission rule fails open, silently.** ``Read(/home/x/**)`` with one leading slash
matches nothing and denies nothing; the correct form is ``Read(//home/x/**)``. There is no warning.
A rule that looks right and does nothing is the defect class this repository loses runs to, so
:func:`assert_deny_rules_are_well_formed` rejects the malformed shape outright.

**Therefore the boundary is probed live, before every phase.** :func:`boundary_probe` asks the real
runtime to attempt one permitted read and one forbidden read, and requires the first to succeed and
the second to be refused. A configuration that merely looks correct does not launch.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
import shutil
import subprocess
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from crypto_trade.tournament.v5.workspace import (
    PROBE_DIRECTORY,
    Workspace,
    clean_environment,
)

# Tools that reach the public network. Withheld from every phase except scouting.
NETWORK_TOOLS = ("WebSearch", "WebFetch")
# Tools a research phase may use. Bash is absent deliberately: it is a general-purpose escape from
# every other restriction here, and nothing a strategy author needs requires it.
RESEARCH_TOOLS = ("Read", "Write", "Edit", "Glob", "Grep")
SCOUTING_TOOLS = ("Read", "Write", "WebSearch", "WebFetch")

DEFAULT_TIMEOUT_SECONDS = 3600


class PhaseLaunchError(RuntimeError):
    """A phase could not be launched, or launched into a configuration that is not safe."""


# Absolute-path permission rules must carry a doubled leading slash. Verified on this host: the
# single-slash form matches nothing, denies nothing, and reports no error.
_WELL_FORMED_PATH_RULE = re.compile(r"^(Read|Write|Edit)\(//.+\)$")
_PATH_RULE = re.compile(r"^(Read|Write|Edit)\(")


def assert_deny_rules_are_well_formed(rules: Sequence[str]) -> None:
    """Reject a deny rule whose path form silently matches nothing.

    This exists because the failure is invisible. A rule written ``Read(/home/x/**)`` produces no
    warning, no error and no denial -- the phase runs with the boundary wide open and every
    downstream artifact looks normal. Refusing the shape is the only point at which it is cheap to
    notice.
    """

    malformed = [
        rule for rule in rules if _PATH_RULE.match(rule) and not _WELL_FORMED_PATH_RULE.match(rule)
    ]
    if malformed:
        raise PhaseLaunchError(
            "permission rules use a path form that matches nothing and denies nothing "
            f"(absolute paths need a doubled leading slash): {malformed}"
        )


def deny_rules(forbidden_roots: Sequence[str], *, network: bool) -> list[str]:
    """Build the deny list for a phase, in the form this host actually enforces."""

    rules = [
        f"Read(//{Path(root).resolve().as_posix().lstrip('/')}/**)" for root in forbidden_roots
    ]
    rules.append("Bash")
    if not network:
        rules.extend(NETWORK_TOOLS)
    assert_deny_rules_are_well_formed(rules)
    return rules


@dataclasses.dataclass(frozen=True, slots=True)
class PhaseRequest:
    """Everything needed to run one phase of one lane."""

    lane: str
    phase: str
    prompt: str
    workspace: Workspace
    forbidden_roots: tuple[str, ...]
    allowed_tools: tuple[str, ...]
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    model: str | None = None

    @property
    def network(self) -> bool:
        return self.workspace.network


@dataclasses.dataclass(frozen=True, slots=True)
class PhaseReceipt:
    """What a phase actually did. Journalled; never reconstructed from memory afterwards."""

    lane: str
    phase: str
    runtime: str
    exit_code: int
    duration_seconds: float
    timed_out: bool
    produced: Mapping[str, str]
    denials: tuple[str, ...]
    transcript_sha256: str

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    def as_dict(self) -> dict[str, object]:
        return {
            "lane": self.lane,
            "phase": self.phase,
            "runtime": self.runtime,
            "exit_code": self.exit_code,
            "duration_seconds": round(self.duration_seconds, 3),
            "timed_out": self.timed_out,
            "produced": dict(sorted(self.produced.items())),
            "denials": list(self.denials),
            "transcript_sha256": self.transcript_sha256,
        }


@runtime_checkable
class AgentRuntime(Protocol):
    """The entire dependency the orchestrator has on whatever executes a phase."""

    name: str

    def launch(self, request: PhaseRequest) -> PhaseReceipt: ...


def _produced_digests(workspace: Workspace, directory: str) -> dict[str, str]:
    target = workspace.lane / directory
    if not target.is_dir():
        return {}
    return {
        item.name: hashlib.sha256(item.read_bytes()).hexdigest()
        for item in sorted(target.iterdir())
        if item.is_file()
    }


class ClaudeCodeRuntime:
    """Drives the ``claude`` CLI headlessly, one phase per process.

    The workspace is the process's working directory, so relative paths cannot leave it, and the
    deny rules cover the roots that materialisation cannot reach. ``--no-session-persistence``
    matters more than it looks: a persisted session would carry one lane's context into the next
    launch, which is precisely the blindness the edition depends on.
    """

    name = "claude-code"

    def __init__(self, executable: str = "claude", *, settings_name: str = ".phase-settings.json"):
        resolved = shutil.which(executable)
        if resolved is None:
            raise PhaseLaunchError(f"agent runtime executable not found: {executable}")
        self.executable = resolved
        self.settings_name = settings_name

    def _settings(self, request: PhaseRequest) -> Path:
        rules = deny_rules(request.forbidden_roots, network=request.network)
        payload = {
            "permissions": {"deny": rules, "defaultMode": "acceptEdits"},
        }
        # Written outside the workspace so it is not itself readable material for the lane.
        path = request.workspace.root.parent / f"{request.workspace.root.name}{self.settings_name}"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def command(self, request: PhaseRequest, settings: Path) -> list[str]:
        command = [
            self.executable,
            "-p",
            request.prompt,
            "--settings",
            str(settings),
            "--allowedTools",
            *request.allowed_tools,
            "--permission-mode",
            "acceptEdits",
            "--no-session-persistence",
            "--output-format",
            "json",
        ]
        if request.model:
            command.extend(["--model", request.model])
        return command

    def launch(self, request: PhaseRequest) -> PhaseReceipt:
        settings = self._settings(request)
        command = self.command(request, settings)
        started = time.monotonic()
        timed_out = False
        try:
            completed = subprocess.run(  # noqa: S603 - fixed executable, no shell
                command,
                cwd=request.workspace.root,
                env=clean_environment(),
                capture_output=True,
                text=True,
                timeout=request.timeout_seconds,
                check=False,
            )
            exit_code, stdout = completed.returncode, completed.stdout
        except subprocess.TimeoutExpired as expired:
            timed_out = True
            exit_code = -1
            stdout = (expired.stdout or b"").decode("utf-8", "replace") if expired.stdout else ""

        denials: tuple[str, ...] = ()
        try:
            report = json.loads(stdout)
            denials = tuple(
                str(entry.get("tool_name", "?")) for entry in report.get("permission_denials", [])
            )
        except (json.JSONDecodeError, AttributeError):
            # A phase whose output is unparseable is still a phase that ran; the receipt records
            # what happened rather than raising, because an organizer-side parse failure must not
            # be charged to the team as a rejected trial.
            pass

        return PhaseReceipt(
            lane=request.lane,
            phase=request.phase,
            runtime=self.name,
            exit_code=exit_code,
            duration_seconds=time.monotonic() - started,
            timed_out=timed_out,
            produced=_produced_digests(request.workspace, "outbox"),
            denials=denials,
            transcript_sha256=hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
        )


class ScriptedRuntime:
    """Executes a plain callable inside the workspace. No model, fully deterministic.

    This is what makes the readiness load and the orchestrator tests runnable on every change: the
    lifecycle, journal, gates and selection can be exercised end to end in milliseconds. A defect in
    the orchestration is then a test failure rather than something discovered halfway through a
    fifty-hour run, which is how prior editions found theirs.
    """

    name = "scripted"

    def __init__(self, script: Callable[[PhaseRequest], int], *, delay: float = 0.0):
        self.script = script
        self.delay = delay

    def launch(self, request: PhaseRequest) -> PhaseReceipt:
        started = time.monotonic()
        if self.delay:
            time.sleep(self.delay)
        try:
            exit_code = int(self.script(request))
            transcript = f"scripted:{request.lane}:{request.phase}:{exit_code}"
        except Exception as error:  # noqa: BLE001 - the receipt is the report
            exit_code = 1
            transcript = f"scripted:{request.lane}:{request.phase}:error:{error}"
        return PhaseReceipt(
            lane=request.lane,
            phase=request.phase,
            runtime=self.name,
            exit_code=exit_code,
            duration_seconds=time.monotonic() - started,
            timed_out=False,
            produced=_produced_digests(request.workspace, "outbox"),
            denials=(),
            transcript_sha256=hashlib.sha256(transcript.encode("utf-8")).hexdigest(),
        )


PROBE_ALLOWED = "probe_allowed_read"
PROBE_DENIED = "probe_denied_read"
PROBE_REPORT = "boundary.txt"

_PROBE_PROMPT = (
    "Sandbox boundary self-test. For each step, attempt it, then append one line to "
    "lane/{directory}/{report} of the form 'stepN: ALLOWED' or 'stepN: DENIED'. Never copy any "
    "file content into the report. Step 1: read {inside}. Step 2: read {outside}. "
    "Continue past failures and always write the report."
)


def boundary_probe(
    runtime: AgentRuntime,
    workspace: Workspace,
    *,
    lane: str,
    inside: Path,
    outside: Path,
    forbidden_roots: Sequence[str],
    timeout_seconds: int = 300,
) -> dict[str, bool]:
    """Make the runtime demonstrate its boundary before it is trusted with a phase.

    Returns the two observed outcomes rather than a bare boolean, so a caller that fails can say
    *which* half failed. Both halves matter: a configuration that denies everything is as broken as
    one that denies nothing, and only checking the denial would call it healthy.

    The report is written to the organizer's probe directory and removed once read. A live run of
    this function found the earlier version leaving its report in ``outbox/``, where the harvest
    collected it beside a genuine submission -- an organizer artifact entering selection as though a
    team had produced it.
    """

    request = PhaseRequest(
        lane=lane,
        phase="boundary-probe",
        prompt=_PROBE_PROMPT.format(
            directory=PROBE_DIRECTORY,
            report=PROBE_REPORT,
            inside=inside.as_posix(),
            outside=outside.as_posix(),
        ),
        workspace=workspace,
        forbidden_roots=tuple(forbidden_roots),
        allowed_tools=("Read", "Write"),
        timeout_seconds=timeout_seconds,
    )
    runtime.launch(request)
    report = workspace.lane / PROBE_DIRECTORY / PROBE_REPORT
    if not report.is_file():
        raise PhaseLaunchError("boundary probe produced no report; the sandbox is not usable")
    text = report.read_text(encoding="utf-8")
    report.unlink()
    lines = {
        line.split(":", 1)[0].strip(): line.split(":", 1)[1].strip().upper()
        for line in text.splitlines()
        if ":" in line
    }
    return {
        PROBE_ALLOWED: lines.get("step1") == "ALLOWED",
        PROBE_DENIED: lines.get("step2") == "DENIED",
    }


def assert_boundary_probe_passed(observed: Mapping[str, bool]) -> None:
    """Both halves, or the phase does not launch."""

    if not observed.get(PROBE_ALLOWED):
        raise PhaseLaunchError(
            "boundary probe could not read its own workspace; the lane would starve"
        )
    if not observed.get(PROBE_DENIED):
        raise PhaseLaunchError(
            "boundary probe read outside the workspace; the deny rules are not in force"
        )


__all__ = [
    "DEFAULT_TIMEOUT_SECONDS",
    "NETWORK_TOOLS",
    "PROBE_ALLOWED",
    "PROBE_DENIED",
    "PROBE_REPORT",
    "RESEARCH_TOOLS",
    "SCOUTING_TOOLS",
    "AgentRuntime",
    "ClaudeCodeRuntime",
    "PhaseReceipt",
    "PhaseRequest",
    "PhaseLaunchError",
    "ScriptedRuntime",
    "assert_boundary_probe_passed",
    "assert_deny_rules_are_well_formed",
    "boundary_probe",
    "deny_rules",
]
