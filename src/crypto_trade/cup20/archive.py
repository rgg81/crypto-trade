"""Reproducible source archives and the blindness pre-flight scan."""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
import math
import os
import re
import tarfile
from collections.abc import Sequence
from pathlib import Path

from crypto_trade.cup20.neighbourhood import NeighbourhoodDeclaration

FORBIDDEN_PATTERNS: tuple[str, ...] = (
    # Sealed and organiser-only surfaces.
    r"data/cup20/sealed",
    r"data/cup20/acquisition",
    r"tournament/cup20/private",
    # The WHOLE reports tree, not just its holdout subdirectory. Nothing under reports-cup20/ is a
    # team input -- a team's only market inputs are the rows the runner streams to it out of
    # data/cup20/is/ -- and the tree carries organiser artifacts derived across BOTH sides of the
    # cutoff. The acquisition's own common BTC report (daily returns and regime labels through the
    # sealed window's last day) was tracked here and matched no pattern while only the holdout
    # subdirectory was named.
    r"reports-cup20",
    # The tripwire planted inside the sealed tree (crypto_trade.cup20.quarantine.CANARY_FILENAME).
    # Its NAME appearing anywhere in a team's files means the sealed directory was at least listed;
    # its CONTENT carries a token that is matched separately, by value, because the token is never
    # committed and so cannot be a literal here. A test asserts this pattern still matches the
    # canary's filename, so the two cannot drift apart.
    r"HOLDOUT-CANARY-DO-NOT-READ",
    # Prior-tournament evidence of any kind.
    r"crypto_trade\.tournament\.top40",
    r"tournament/top40",
    r"reports-top40",
    r"tournament/crypto/results",
    r"diary-portfolio-mn",
    # Any calendar date STRICTLY AFTER the IS cutoff -- 2024-08-02 onward.
    #
    # The cutoff instant itself is 2024-08-01T00:00:00Z, and the IS window is the half-open
    # [IS_START, 2024-08-01): the cutoff is the first EXCLUDED instant, so the literal `2024-08-01`
    # describes only where the visible data stops. It reveals nothing about the holdout, and it is
    # universally disclosed -- the charter's window table, `config.toml`'s `is_end` AND
    # `sealed_start`, and the playbook all print it. Decisively, the organiser's own harness prints
    # it into every packet it writes into a team's workspace: `CoachingPacket.render` emits
    # `window [<is_start>, 2024-08-01 00:00:00+00:00)` and a fold line ending `F4 [.., 2024-08-01)`,
    # and `as_dict` carries both as JSON. Matching it made the organiser hand each team a file that
    # tripped the team's own blindness scan, so `2024-08-01` is permitted and 2024-08-02 onward is
    # not. `SEALED_START` is the same instant as `IS_END` and is therefore permitted in that guise
    # too; `SEALED_END` (2026-08-01) is genuinely post-cutoff and stays caught by the pattern below.
    #
    # `08-(?!01(?!\d))` is what carves the single day out: it permits `01` only when no digit
    # follows, so every suffixed form of the boundary that is really a date -- `2024-08-01Z`,
    # `2024-08-01T00:00:00Z`, `2024-08-01 00:00:00+00:00` -- is permitted, while a digit-extended
    # `2024-08-012` is still refused rather than being read as the permitted day plus noise.
    #
    # Scope, stated so it is not quietly widened later: this rule matches hyphenated ISO-8601
    # calendar dates and nothing else, exactly as it did before. Compact `20240801` forms and epoch
    # millisecond literals were never matched and still are not -- the `(?<!\d)` guard exists
    # precisely to keep the scan out of long digit runs. Adding compact 8-digit dates would be a
    # different control with its own false positives: `config.toml` already carries
    # `bootstrap_seed = 20260804`, a legitimate public scalar that such a pattern would accuse.
    # Blindness is enforced primarily by absence (the sealed rows are simply not in a team's data
    # directory); this scan is a disclosed-imperfect second layer, not the guarantee.
    r"(?<!\d)2024-(?:08-(?!01(?!\d))|(?:09|1[0-2])-)\d{2}",
    r"(?<!\d)20(?:2[5-9]|[3-9]\d)-\d{2}-\d{2}",
)
_COMPILED = tuple((pattern, re.compile(pattern)) for pattern in FORBIDDEN_PATTERNS)
_TEAM_DIRECTORY = re.compile(r"tournament/cup20/teams/(team-\d{2})")

# Content scanning has no extension allowlist: path.read_text(errors="replace") already tolerates
# non-UTF8 bytes, so restricting *which* files get their content read bought no safety, only a
# blind spot. This cap exists purely so a large, legitimate data/model file cannot make the scan
# pathologically slow -- not to exempt any kind of file's content from being read. Path/filename
# scanning (see scan_for_blindness_violations) is unaffected: it is always cheap, regardless of
# a file's size, and always runs.
_MAX_CONTENT_SCAN_BYTES = 262_144  # 256 KiB -- generous for any real source or config file.

# The frozen entrypoint is parsed, and ast.parse's own C-implemented parser can exhaust the Python
# call stack or available memory on a pathologically large or pathologically nested source file --
# confirmed directly: an elif chain of a few thousand branches, well under a megabyte, raises
# RecursionError or MemoryError depending on exactly how deep it goes. Team code is untrusted and
# this check's whole job is resisting a team, so a competing team has direct incentive to submit a
# file engineered to crash the check itself as a cheap denial of service. This cap is a fast,
# cheap first line of defence -- reject before ever calling ast.parse -- not a complete guarantee
# by itself (see _UNPARSEABLE_SOURCE_ERRORS and _MAX_EXPRESSION_DEPTH below for the rest).
_MAX_ENTRYPOINT_BYTES = 262_144  # 256 KiB -- generous for a single frozen strategy file.

# A depth guard for the two places this module recurses over an EXPRESSION tree rather than a
# statement list (chained unary negation in _numeric; nested tuple-unpacking targets in
# _record_numeric_target). Both are attacker-cheap: a single `-` character or a single-element
# tuple nesting level costs about one byte per recursion level, so a modest file can nest either
# far past any real Python recursion limit long before _MAX_ENTRYPOINT_BYTES would reject it on
# size alone. 20 is far beyond anything a human would plausibly write by hand.
_MAX_EXPRESSION_DEPTH = 20

# ast.parse can fail on genuinely malformed team source (bad syntax, a stray null byte, an invalid
# encoding) or on pathologically large/nested source that exhausts the interpreter's call stack or
# memory (RecursionError, MemoryError -- see _MAX_ENTRYPOINT_BYTES above). The global contract is
# "failures are violation strings, not raises" -- team code is untrusted, so a team that ships
# something unparseable, or something engineered to make parsing itself blow up, must fail the
# check, not crash the caller.
_UNPARSEABLE_SOURCE_ERRORS: tuple[type[Exception], ...] = (
    SyntaxError,
    ValueError,
    UnicodeError,
    RecursionError,
    MemoryError,
)


def _files(source_root: Path) -> list[Path]:
    """Every regular file in the tree, sorted for deterministic iteration.

    Symlinks are excluded outright, never dereferenced. ``archive.gettarinfo`` (used by
    ``archive_directory``) records a symlink as a link, not a copy of its target's bytes -- so
    dereferencing here for the digest while the tar stores only a link target would let the
    recorded digest and what the archive actually, durably contains silently diverge (the target
    can move, change or vanish after archiving). Excluding symlinks makes both functions agree:
    neither hashes nor archives them. ``scan_for_blindness_violations`` separately reports the mere
    presence of any symlink as a violation in its own right -- see its docstring.
    """
    return sorted(
        path
        for path in source_root.rglob("*")
        if path.is_file() and not path.is_symlink() and "__pycache__" not in path.parts
    )


def bundle_digest(source_root: str | Path) -> str:
    """Digest file names and bytes into one reproducible bundle identity."""
    root = Path(source_root).resolve()
    digest = hashlib.sha256()
    for path in _files(root):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\x00")
        digest.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii"))
        digest.update(b"\x00")
    return digest.hexdigest()


def archive_directory(source_root: str | Path, destination_root: str | Path) -> str:
    """Write a deterministic tar of the source tree, named by its bundle digest."""
    root = Path(source_root).resolve()
    destination = Path(destination_root)
    destination.mkdir(parents=True, exist_ok=True)
    digest = bundle_digest(root)
    archive_path = destination / f"{digest}.tar"
    with tarfile.open(archive_path, "w", format=tarfile.PAX_FORMAT) as archive:
        for path in _files(root):
            info = archive.gettarinfo(str(path), arcname=path.relative_to(root).as_posix())
            info.mtime = 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mode = 0o644
            with path.open("rb") as handle:
                archive.addfile(info, handle)
    sidecar = {
        "bundle_sha256": digest,
        "files": [path.relative_to(root).as_posix() for path in _files(root)],
    }
    (destination / f"{digest}.json").write_text(
        json.dumps(sidecar, indent=2, sort_keys=True) + "\n"
    )
    return digest


def _numeric(node: ast.AST, depth: int = 0) -> float | None:
    """A literal's numeric value, or ``None`` if it is not a plain (optionally negated) number.

    ``depth`` guards the ``UnaryOp`` recursion (chained negation, e.g. ``----5``) against
    adversarial nesting: past ``_MAX_EXPRESSION_DEPTH``, this gives up and reports not-numeric
    rather than recursing further -- a real literal is never nested anywhere near that deep.
    """
    if depth > _MAX_EXPRESSION_DEPTH:
        return None
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        if isinstance(node.value, bool):
            return None
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _numeric(node.operand, depth + 1)
        return None if inner is None else -inner
    return None


def _record_numeric_target(
    target: ast.expr, value: ast.expr, found: dict[str, list[ast.expr]], depth: int = 0
) -> None:
    """Record ``target <- value`` for a plain ``Name`` target with a numeric-literal value, or,
    for a ``Tuple`` target paired with a same-length ``Tuple`` value, recurse elementwise (this
    also naturally covers a nested tuple pattern, since each element pairing is the same rule
    applied again). Appends the value NODE to the list of sites seen for that name -- see
    ``module_level_numeric_assignments`` for why the node and not just its value, and
    ``_collect_from_statements`` for why every site is kept rather than one overwritten value.

    ``depth`` guards the ``Tuple`` recursion against adversarial nesting (thousands of
    single-element nested tuples), the same concern and the same bound as ``_numeric``'s own
    ``UnaryOp`` guard.

    Any other shape -- a length-mismatched tuple, a starred target, an attribute or subscript
    target -- is silently skipped rather than guessed at: a shape this function does not
    confidently understand must never risk attributing the wrong value to a name. Reporting a
    coordinate absent is always safer than reporting a wrong one.
    """
    if depth > _MAX_EXPRESSION_DEPTH:
        return
    if isinstance(target, ast.Name):
        if _numeric(value) is not None:
            found.setdefault(target.id, []).append(value)
    elif (
        isinstance(target, ast.Tuple)
        and isinstance(value, ast.Tuple)
        and len(target.elts) == len(value.elts)
    ):
        for element_target, element_value in zip(target.elts, value.elts):
            _record_numeric_target(element_target, element_value, found, depth + 1)


def _record_numeric_assign(
    node: ast.Assign | ast.AnnAssign, found: dict[str, list[ast.expr]]
) -> None:
    """Record a module-level plain or annotated assignment's target(s), including tuple/multiple-
    target unpacking."""
    if isinstance(node, ast.AnnAssign):
        if node.value is not None:
            _record_numeric_target(node.target, node.value, found)
        return
    for target in node.targets:
        _record_numeric_target(target, node.value, found)


def _ordered_children(statement: ast.stmt) -> list[ast.stmt]:
    """This statement's own nested statement lists, concatenated in natural top-to-bottom source
    order: ``body``, then each ``except`` handler's body in order, then ``orelse``, then
    ``finalbody``. That is the order real execution would encounter them in, for whichever single
    path actually runs. Returns an empty list for anything this module does not recurse into -- a
    ``FunctionDef``/``AsyncFunctionDef``/``ClassDef`` scope boundary, or a statement with no nested
    block at all.
    """
    if isinstance(statement, (ast.If, ast.For, ast.While)):
        return [*statement.body, *statement.orelse]
    if isinstance(statement, ast.With):
        return list(statement.body)
    if isinstance(statement, ast.Try):
        handler_statements = [inner for handler in statement.handlers for inner in handler.body]
        return [*statement.body, *handler_statements, *statement.orelse, *statement.finalbody]
    return []


def module_level_numeric_assignments(
    statements: Sequence[ast.stmt],
) -> dict[str, list[ast.expr]]:
    """Every module-level numeric-literal assignment SITE, as ``name -> [value nodes]``.

    This is the single traversal the coordinate rule is defined by. Two callers read it and they
    must never disagree: :func:`verify_neighbourhood_coordinates` decides whether a coordinate is a
    module-level numeric constant with exactly one value, and
    :mod:`crypto_trade.cup20.variants` rewrites those same literals to materialise a neighbourhood
    point. If the verifier and the rewriter each walked the tree their own way, the sweep could
    substitute somewhere the verifier never looked (a point that silently is not the point it
    claims to be) or fail to substitute somewhere it did (a point that silently is the nominee).
    Returning the value NODES rather than their values is what lets the rewriter edit exactly the
    byte spans the verifier read, so the two are the same set by construction rather than by
    agreement.

    Which sites count is documented on :func:`_collect_from_statements`: module-level control flow
    is descended into, function and class bodies never are. Order is source order within each name,
    which is what makes a substitution plan reproducible.
    """
    found: dict[str, list[ast.expr]] = {}
    stack: list[ast.stmt] = list(reversed(list(statements)))
    while stack:
        statement = stack.pop()
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            _record_numeric_assign(statement, found)
        else:
            stack.extend(reversed(_ordered_children(statement)))
    return found


def _collect_from_statements(statements: Sequence[ast.stmt]) -> dict[str, set[float]]:
    """Collect every DISTINCT numeric value assigned to each module-level name.

    Recurses through module-level control flow -- ``if``/``for``/``while``/``with``/``try`` and
    their ``else``/``finally``/``except`` bodies (see ``_ordered_children``) -- because a name
    assigned there genuinely is a module-level name: the statement is bound as part of ordinary
    module load, not as a variable scoped to a function or method call. (Whether a *particular*
    branch runs on any given import is not something a static parse can decide without executing
    team code, which it must never do; treating every syntactically reachable module-level
    assignment as a candidate is the fail-safe direction.)

    Never recurses into a ``FunctionDef``, ``AsyncFunctionDef`` or ``ClassDef`` body: a
    function-local variable or a class attribute is not a module-level parameter. Refusing to look
    there is what eliminates cross-scope name collisions entirely -- a class attribute that happens
    to share a real module-level constant's name can no longer interact with it at all.

    Returns a mapping from name to the SET of distinct numeric values it was assigned anywhere at
    module scope, not a single "winning" value. A name assigned the same value more than once
    collapses to a single-element set (no conflict); a name assigned two or more DIFFERENT values
    -- by plain reassignment, or across mutually exclusive branches -- has a multi-element set. A
    team can plant a decoy value in a branch that never actually runs (e.g. an ``if``/``else``
    where the condition is always true) just as easily as in the branch that does; "whichever was
    assigned last, textually" is not a reliable signal for what the frozen code actually does, so
    the caller (``verify_neighbourhood_coordinates``) treats more than one distinct value as an
    unresolvable conflict rather than picking one.

    Implemented iteratively with an explicit work stack, not by calling itself: an ``elif`` chain
    is represented as nested ``If.orelse``, not extra source indentation, so ordinary Python
    recursion depth limits do not bound how deep it can go -- a team-supplied file a few thousand
    branches long is well within a modest byte budget and previously raised an uncaught
    ``RecursionError`` through this exact function. The stack is pushed and popped in a way that
    preserves the same left-to-right, depth-first order plain recursion would visit statements in
    (each container's children are pushed, reversed, onto the top of the stack, so they are
    processed immediately -- before whatever sibling statements were already queued below).

    Derived from :func:`module_level_numeric_assignments` rather than walking the tree a second
    time, so "the sites the verifier reads" and "the sites the sweep rewrites" cannot drift apart.
    ``_numeric`` is guaranteed non-``None`` on every recorded node -- that is the filter under
    which the node was recorded at all.
    """
    return {
        name: {value for value in (_numeric(node) for node in nodes) if value is not None}
        for name, nodes in module_level_numeric_assignments(statements).items()
    }


def _frozen_numeric_parameters(path: Path) -> dict[str, set[float]]:
    """Collect module-level numeric constants from a frozen entrypoint by parsing, never importing.

    Team code is untrusted and must never execute during verification, so this uses ``ast``. A
    coordinate must be a module-level numeric constant: a plain or annotated assignment (including
    tuple/multiple-target unpacking) reachable from the module's top level through control flow
    alone, never through a function or class boundary (see ``_collect_from_statements``, which also
    documents why the return type is a set of values per name rather than one).

    Function keyword defaults and class attributes are deliberately NOT collected, even though an
    earlier version of this module supported both. Two reasons converged on dropping them rather
    than fixing them: (1) a class attribute sharing a module-level constant's name collided with it
    in a flat dict keyed only by bare name -- an unrelated class defining its own, differently-
    valued attribute of the same name could silently overwrite (or be overwritten by) the real
    module-level value, manufacturing a false "differs from frozen source" report against a team
    that had declared the objectively correct value; (2) the keyword-default collector's alignment
    of ``ast.arguments.defaults`` against parameter names broke -- not merely omitted a parameter,
    but MISATTRIBUTED one parameter's default value to a different parameter's name -- for any
    signature mixing positional-only parameters with defaults and ordinary ones (e.g.
    ``def f(a=1, /, b=2)``), again producing a false "differs from frozen source" report against a
    correct nominee. A function parameter's default and a class's own attribute are, in real Python
    semantics, never a bare module-level name in the first place -- ``lookback`` inside
    ``def f(lookback=60)`` is not a name in the module's namespace at all, only a parameter of
    ``f`` -- so treating a coordinate declared against one of these as material was already a
    stretch beyond "module-level numeric constant." A team whose real, governing values live only
    behind a keyword default or a class attribute is reported absent under the current rule; the
    honest fix on the team's side is to expose the value as a plain module-level constant, which is
    also the shape most legibly "the frozen code actually does."
    """
    tree = ast.parse(path.read_text())
    return _collect_from_statements(tree.body)


def verify_neighbourhood_coordinates(
    source_root: str | Path,
    declaration: NeighbourhoodDeclaration,
    *,
    entrypoint: str = "strategy.py",
) -> tuple[str, ...]:
    """Check every declared coordinate is a real numeric parameter of the frozen source.

    Design spec section 7.2 requires that every coordinate map to an identically named numeric
    material parameter in the frozen source. Internal self-consistency is not enough: without this,
    a team can declare a fictional coordinate, satisfy every other gate, and claim a plateau across
    a surface it never explored. Requiring the nominee's value to match the frozen source also
    forces the nominated point to be what the frozen code actually does.

    A coordinate must have exactly one numeric value at module scope. A name assigned two or more
    genuinely DIFFERENT values -- by plain reassignment, or across mutually exclusive branches such
    as an ``if``/``else`` -- is reported as a conflict, never silently resolved to either one:
    "textually last" is not a reliable signal for what the frozen code actually does (deciding
    which branch a real interpreter would take means evaluating the condition, i.e. executing team
    code, which this function must never do), so a team could otherwise plant a decoy value in
    whichever branch is written last and have it accepted over the value the code actually uses.
    Assigning the same value more than once is fine and is not a conflict.
    """
    entry = Path(source_root) / entrypoint
    if not entry.is_file():
        return (f"{entrypoint}:missing-entrypoint",)
    if entry.stat().st_size > _MAX_ENTRYPOINT_BYTES:
        return (f"{entrypoint}:entrypoint-too-large",)
    try:
        parameters = _frozen_numeric_parameters(entry)
    except _UNPARSEABLE_SOURCE_ERRORS:
        return (f"{entrypoint}:unparseable-source",)
    violations: list[str] = []
    for coordinate in declaration.coordinates:
        values = parameters.get(coordinate)
        if not values:
            violations.append(f"{entrypoint}:{coordinate}:absent-from-frozen-source")
            continue
        if len(values) > 1:
            conflicting = "-vs-".join(str(value) for value in sorted(values))
            violations.append(
                f"{entrypoint}:{coordinate}:conflicting-module-level-values-{conflicting}"
            )
            continue
        if coordinate not in declaration.nominee:
            # NeighbourhoodDeclaration.validate() would normally catch this (the nominee must
            # declare exactly the coordinate set) -- but validate() is opt-in, not enforced by the
            # dataclass itself, and this function must not assume its caller already ran it. A bare
            # `declaration.nominee[coordinate]` subscript here would raise an uncaught KeyError,
            # the same defect class Task 8's own review caught in positive_point_fraction.
            violations.append(f"{entrypoint}:{coordinate}:nominee-missing-declared-coordinate")
            continue
        declared = float(declaration.nominee[coordinate])
        (frozen,) = values  # exactly one element, guaranteed by the len(values) > 1 branch above
        if not math.isclose(declared, frozen, rel_tol=1e-9, abs_tol=1e-12):
            violations.append(
                f"{entrypoint}:{coordinate}:nominee-{declared}-differs-from-frozen-{frozen}"
            )
    return tuple(violations)


def _line_violations(
    relative: str,
    text: str,
    line_number: int,
    team_id: str | None,
    *,
    extra: tuple[tuple[str, re.Pattern[str]], ...] = (),
    tokens: tuple[str, ...] = (),
) -> list[str]:
    """Every forbidden-pattern / foreign-team-directory hit in one piece of text.

    Shared between the path-identity check and the line-content check below, so a forbidden
    reference is caught the same way regardless of whether a team typed it into a line of source or
    spelled it into a directory or file name instead.

    ``extra`` carries patterns that cannot be frozen into ``FORBIDDEN_PATTERNS`` because they are
    only known at review time -- above all the quarantine root, which is chosen when the tournament
    starts. ``tokens`` carries literal strings matched by value rather than as regexes: the sealed
    tree's canary token is high-entropy, is never committed, and would be neither expressible nor
    safe to write down here.
    """
    found: list[str] = []
    for pattern, compiled in _COMPILED + extra:
        if compiled.search(text):
            found.append(f"{relative}:{line_number}:{pattern}")
    for token in tokens:
        if token and token in text:
            found.append(f"{relative}:{line_number}:sealed-canary-token")
    for match in _TEAM_DIRECTORY.finditer(text):
        if match.group(1) != team_id:
            found.append(f"{relative}:{line_number}:foreign-team-directory")
    return found


def scan_for_blindness_violations(
    source_root: str | Path, *, team_id: str | None = None
) -> tuple[str, ...]:
    """Report every forbidden reference in a team's frozen source tree.

    A team may name its own directory; naming any other team's directory is a violation. Every
    forbidden pattern and the foreign-team-directory check run against two independent surfaces:
    each scanned file's OWN relative path (line number ``0`` in the reported violation -- so a
    forbidden reference spelled into a directory or file name, not typed into a line of source,
    cannot slip through), and the line-by-line content of every file, regardless of extension, up
    to ``_MAX_CONTENT_SCAN_BYTES`` (a size cap, not an extension allowlist -- content is read with
    ``errors="replace"`` and already tolerates non-UTF8 bytes, so restricting *which* extensions
    got read was never a safety measure, only a self-imposed blind spot; the cap exists solely so a
    large, legitimate data or model file cannot make the scan pathologically slow).

    A symlink anywhere in the tree is always a violation in its own right, regardless of its
    target or where it points: ``bundle_digest``/``archive_directory`` exclude symlinks entirely
    rather than dereferencing them (see ``_files``), so an unflagged symlink would be a file that is
    materially "present" in the working tree yet invisible to both the archive and the digest --
    and its target never has to appear as text anywhere this scan looks in order to affect what the
    team's strategy sees at runtime.

    Known, disclosed limitation: this is a static, line-based regex scan of literal source text. It
    does not evaluate expressions, so a forbidden string built at parse-time by concatenation (e.g.
    ``"data/cup20/" + "sealed"``) or by any other computed construction will not match -- closing
    this would need AST constant-folding over ``BinOp`` chains, and f-strings/``%``-formatting would
    stay open regardless. This is acceptable because blindness is enforced primarily by absence --
    the sealed rows are simply never present in a team's data directory -- and this scan is a
    second, disclosed-imperfect layer on top of that, not the only one.
    """
    root = Path(source_root).resolve()
    violations: list[str] = []
    for path in sorted(entry for entry in root.rglob("*") if entry.is_symlink()):
        relative = path.relative_to(root).as_posix()
        violations.append(f"{relative}:0:symlink-not-allowed")
    for path in _files(root):
        relative = path.relative_to(root).as_posix()
        violations.extend(_line_violations(relative, relative, 0, team_id))
        if path.stat().st_size > _MAX_CONTENT_SCAN_BYTES:
            continue
        for number, line in enumerate(path.read_text(errors="replace").splitlines(), start=1):
            violations.extend(_line_violations(relative, line, number, team_id))
    return tuple(violations)


# A team's WORKSPACE is not a frozen archive: it legitimately holds research notebooks, cached
# frames, plots and logs, several of which are far larger than any source file. The frozen-archive
# cap would therefore skip a lot of a real workspace, so the workspace scan reads much more before
# it gives up -- and, unlike the archive scan, it REPORTS whatever it could not read instead of
# passing over it silently. An unreadable file in a submission is an organiser decision, not an
# exemption the tool grants on its own.
_MAX_WORKSPACE_CONTENT_BYTES = 8_388_608  # 8 MiB


@dataclasses.dataclass(frozen=True, slots=True)
class WorkspaceScan:
    """What a workspace scan found, and what it could not look at.

    ``violations`` is the verdict; ``unscanned`` is the disclosed hole in it. A review that reads
    only ``violations`` and ignores a non-empty ``unscanned`` has checked less than it thinks.
    """

    root: str
    violations: tuple[str, ...]
    unscanned: tuple[str, ...]
    files_scanned: int

    @property
    def clean(self) -> bool:
        """No violations AND nothing left unread. Both, deliberately."""
        return not self.violations and not self.unscanned


def scan_workspace_for_blindness_violations(
    workspace_root: str | Path,
    *,
    team_id: str | None = None,
    canary_tokens: Sequence[str] = (),
    extra_patterns: Sequence[str] = (),
    max_content_bytes: int = _MAX_WORKSPACE_CONTENT_BYTES,
) -> WorkspaceScan:
    """Scan a team's ENTIRE working directory, not just the archive it chose to freeze.

    :func:`scan_for_blindness_violations` reads a frozen candidate bundle -- the handful of files a
    team nominated. That is the right surface for a pre-flight gate and the wrong one for an
    integrity review: a team that opened the sealed snapshot and left the evidence in
    ``research/scratch.md``, a notebook cell, a ``.pyc`` or a shell log has left the archive
    entirely clean. This scans everything under ``workspace_root`` instead, so the question becomes
    "is there evidence anywhere in this team's tree" rather than "is there evidence in the files
    they handed in".

    What is scanned, and what is not:

    * **Every regular file**, with no extension allowlist and no directory exclusions --
      ``__pycache__`` included, which the archive scan skips as derived. A team can delete a ``.py``
      and keep its ``.pyc``, and the forbidden string survives in the compiled constant pool;
      content is read with ``errors="replace"`` so binary files are searched as text rather than
      skipped.
    * **Both surfaces** of every file, exactly as the archive scan does: the file's own relative
      path (reported at line ``0``) and its content line by line.
    * **Symlinks** are reported as violations in their own right AND their target text is scanned,
      so a link pointing at ``../../../data/cup20/sealed`` is named twice -- once as a symlink,
      once as the specific prohibited path. This is the cheapest evasion available and the archive
      scan can only see the first half of it, because a symlink never reaches the archive.
    * **Canary tokens** are matched by value. A token planted inside the sealed tree that turns up
      in a workspace file is the strongest single piece of evidence this scan can produce.
    * **Files larger than ``max_content_bytes``** have their PATH scanned but not their content,
      and every one is listed in ``unscanned``. Nothing is skipped for being the wrong kind of
      file; the only reason content goes unread is size, and the reviewer is told which files and
      how big.

    Its limits are the archive scan's limits, and they are not fixed here: this is a literal
    string search, so a forbidden reference assembled at runtime by concatenation or formatting
    does not match, and a team that read the sealed data and wrote down only conclusions leaves
    nothing to find. That is why quarantine, not scanning, is the load-bearing control for the
    research phase.
    """
    root = Path(workspace_root).resolve()
    extra = tuple((pattern, re.compile(pattern)) for pattern in extra_patterns)
    tokens = tuple(canary_tokens)
    violations: list[str] = []
    unscanned: list[str] = []
    scanned = 0

    for path in sorted(entry for entry in root.rglob("*") if entry.is_symlink()):
        relative = path.relative_to(root).as_posix()
        violations.append(f"{relative}:0:symlink-not-allowed")
        violations.extend(
            _line_violations(relative, relative, 0, team_id, extra=extra, tokens=tokens)
        )
        try:
            target = os.readlink(path)
        except OSError:  # pragma: no cover - readlink on an entry is_symlink() just confirmed
            target = ""
        if target:
            violations.extend(
                _line_violations(relative, target, 0, team_id, extra=extra, tokens=tokens)
            )

    for path in sorted(
        entry for entry in root.rglob("*") if entry.is_file() and not entry.is_symlink()
    ):
        relative = path.relative_to(root).as_posix()
        scanned += 1
        violations.extend(
            _line_violations(relative, relative, 0, team_id, extra=extra, tokens=tokens)
        )
        size = path.stat().st_size
        if size > max_content_bytes:
            unscanned.append(f"{relative}:{size}")
            continue
        for number, line in enumerate(path.read_text(errors="replace").splitlines(), start=1):
            violations.extend(
                _line_violations(relative, line, number, team_id, extra=extra, tokens=tokens)
            )

    return WorkspaceScan(
        root=str(root),
        violations=tuple(violations),
        unscanned=tuple(unscanned),
        files_scanned=scanned,
    )
