"""Reproducible source archives and the blindness pre-flight scan."""

from __future__ import annotations

import ast
import hashlib
import json
import math
import re
import tarfile
from pathlib import Path

from crypto_trade.cup20.neighbourhood import NeighbourhoodDeclaration

FORBIDDEN_PATTERNS: tuple[str, ...] = (
    # Sealed and organiser-only surfaces.
    r"data/cup20/sealed",
    r"tournament/cup20/private",
    r"reports-cup20/holdout",
    # Prior-tournament evidence of any kind.
    r"crypto_trade\.tournament\.top40",
    r"tournament/top40",
    r"reports-top40",
    r"tournament/crypto/results",
    r"diary-portfolio-mn",
    # Any calendar date on or after the IS cutoff of 2024-08-01.
    r"(?<!\d)2024-(?:0[89]|1[0-2])-\d{2}",
    r"(?<!\d)20(?:2[5-9]|[3-9]\d)-\d{2}-\d{2}",
)
_COMPILED = tuple((pattern, re.compile(pattern)) for pattern in FORBIDDEN_PATTERNS)
_SCANNED_SUFFIXES = frozenset({".py", ".toml", ".json", ".md", ".cfg", ".txt", ".yaml", ".yml"})
_TEAM_DIRECTORY = re.compile(r"tournament/cup20/teams/(team-\d{2})")

# ast.parse can fail on genuinely malformed team source (bad syntax, a stray null byte, an invalid
# encoding). The global contract is "failures are violation strings, not raises" -- team code is
# untrusted, so a team that ships something unparseable must fail the check, not crash the caller.
_UNPARSEABLE_SOURCE_ERRORS: tuple[type[Exception], ...] = (SyntaxError, ValueError, UnicodeError)


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


def _numeric(node: ast.AST) -> float | None:
    """A literal's numeric value, or ``None`` if it is not a plain (optionally negated) number."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        if isinstance(node.value, bool):
            return None
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _numeric(node.operand)
        return None if inner is None else -inner
    return None


def _record_numeric_assign(node: ast.Assign | ast.AnnAssign, found: dict[str, float]) -> None:
    """Record a plain or annotated assignment's target(s), if its value is a plain numeric literal.

    Assigns into ``found`` (does not use ``setdefault``): a later assignment overwrites an earlier
    one, matching what straight-line top-to-bottom execution actually leaves bound in the
    namespace. A first-wins rule would let a team put a favourable, declared-nominee-matching value
    first and a different, real operative value afterwards, and have the check see only the decoy.
    """
    if isinstance(node, ast.AnnAssign) and node.value is None:
        return
    value = _numeric(node.value)
    if value is None:
        return
    targets: list[ast.expr] = node.targets if isinstance(node, ast.Assign) else [node.target]
    for target in targets:
        if isinstance(target, ast.Name):
            found[target.id] = value


def _numeric_keyword_defaults(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, float]:
    """Numeric keyword defaults on one function's own signature (not the defaults of any callee)."""
    args = node.args
    names = [arg.arg for arg in args.args + args.kwonlyargs]
    defaults = list(args.defaults) + list(args.kw_defaults)
    found: dict[str, float] = {}
    for name, default in zip(names[-len(defaults) :] if defaults else [], defaults):
        if default is None:
            continue
        value = _numeric(default)
        if value is not None:
            found[name] = value
    return found


def _frozen_numeric_parameters(path: Path) -> dict[str, float]:
    """Collect numeric parameters from a frozen entrypoint by parsing, never importing.

    Team code is untrusted and must never execute during verification, so this uses ``ast`` and is
    scoped STRICTLY to module level: a direct module-level assignment or annotated assignment, a
    numeric keyword default on a module-level function, or -- for a dataclass-field-style
    declaration -- a class attribute default or a method's keyword default, for a class defined
    directly at module level. Nothing nested one scope deeper than that is material: not a local
    variable inside a function body, not an assignment guarded by a module-level
    ``if``/``for``/``while``/``try``, and not a class or function defined inside another function.
    A scan that walked every nested scope (e.g. via ``ast.walk``) would let a team plant a
    same-named decoy assignment anywhere in the file -- including inside a branch that can never
    execute -- and have it accepted as if it were a real, governing parameter of the strategy.
    """
    tree = ast.parse(path.read_text())
    found: dict[str, float] = {}
    for statement in tree.body:
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            _record_numeric_assign(statement, found)
        elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found.update(_numeric_keyword_defaults(statement))
        elif isinstance(statement, ast.ClassDef):
            for member in statement.body:
                if isinstance(member, (ast.Assign, ast.AnnAssign)):
                    _record_numeric_assign(member, found)
                elif isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    found.update(_numeric_keyword_defaults(member))
    return found


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
    """
    entry = Path(source_root) / entrypoint
    if not entry.is_file():
        return (f"{entrypoint}:missing-entrypoint",)
    try:
        parameters = _frozen_numeric_parameters(entry)
    except _UNPARSEABLE_SOURCE_ERRORS:
        return (f"{entrypoint}:unparseable-source",)
    violations: list[str] = []
    for coordinate in declaration.coordinates:
        if coordinate not in parameters:
            violations.append(f"{entrypoint}:{coordinate}:absent-from-frozen-source")
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
        frozen = parameters[coordinate]
        if not math.isclose(declared, frozen, rel_tol=1e-9, abs_tol=1e-12):
            violations.append(
                f"{entrypoint}:{coordinate}:nominee-{declared}-differs-from-frozen-{frozen}"
            )
    return tuple(violations)


def _line_violations(relative: str, text: str, line_number: int, team_id: str | None) -> list[str]:
    """Every forbidden-pattern / foreign-team-directory hit in one piece of text.

    Shared between the path-identity check and the line-content check below, so a forbidden
    reference is caught the same way regardless of whether a team typed it into a line of source or
    spelled it into a directory or file name instead.
    """
    found: list[str] = []
    for pattern, compiled in _COMPILED:
        if compiled.search(text):
            found.append(f"{relative}:{line_number}:{pattern}")
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
    cannot slip through), and the line-by-line content of every file whose extension marks it as
    text worth reading.

    A symlink anywhere in the tree is always a violation in its own right, regardless of its
    target or where it points: ``bundle_digest``/``archive_directory`` exclude symlinks entirely
    rather than dereferencing them (see ``_files``), so an unflagged symlink would be a file that is
    materially "present" in the working tree yet invisible to both the archive and the digest --
    and its target never has to appear as text anywhere this scan looks in order to affect what the
    team's strategy sees at runtime.

    Known, disclosed limitation: this is a static, line-based regex scan of literal source text. It
    does not evaluate expressions, so a forbidden string built at parse-time by concatenation (e.g.
    ``"data/cup20/" + "sealed"``) or by any other computed construction will not match, and content
    inside a file extension outside ``_SCANNED_SUFFIXES`` is not read at all (though its path is
    still checked, per the paragraph above). This is acceptable because blindness is enforced
    primarily by absence -- the sealed rows are simply never present in a team's data directory --
    and this scan is a second, disclosed-imperfect layer on top of that, not the only one.
    """
    root = Path(source_root).resolve()
    violations: list[str] = []
    for path in sorted(entry for entry in root.rglob("*") if entry.is_symlink()):
        relative = path.relative_to(root).as_posix()
        violations.append(f"{relative}:0:symlink-not-allowed")
    for path in _files(root):
        relative = path.relative_to(root).as_posix()
        violations.extend(_line_violations(relative, relative, 0, team_id))
        if path.suffix not in _SCANNED_SUFFIXES:
            continue
        for number, line in enumerate(path.read_text(errors="replace").splitlines(), start=1):
            violations.extend(_line_violations(relative, line, number, team_id))
    return tuple(violations)
