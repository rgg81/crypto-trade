"""Materialise one declared neighbourhood point as a real, hashable variant of the frozen source.

Section 7.2 scores a team on the per-metric median across its declared neighbourhood, so the
neighbourhood has to be *run* -- which means running the frozen candidate at coordinate values it
does not itself carry. The obvious implementation, "import the module and then set its constants",
is unsound and was rejected for that reason: a module-level constant is read at import time into
default arguments, class attributes, closures and precomputed tables, so assigning to the module
attribute afterwards changes a name nothing looks at again. The sweep would run the nominee seven
times, report a perfect plateau, and mean nothing.

**The coordinate rule is what makes a sound mechanism possible.** Playbook section 6.1 requires
every coordinate to be a module-level numeric constant in ``strategy.py``, named identically to the
coordinate, with exactly one value. A point is therefore materialisable by *textual substitution*:
rewrite exactly those numeric literals, write the result to a new directory, and import that file.
No monkeypatching, no post-import mutation, and every point is a real file with its own digest.

What this module guarantees, and how each guarantee is checked rather than asserted:

1. **The variant differs from the nominee only in the declared coordinates.** Both files are parsed
   with :func:`~crypto_trade.cup20.archive.module_level_numeric_assignments` -- the same single
   traversal the coordinate rule is verified by -- and each coordinate literal's byte span is
   replaced with one sentinel byte in *both*. The two blanked texts must then be byte-identical.
   That is a proof, not a promise: it says the files agree byte for byte everywhere outside the
   coordinate literals, and that the literals sit at the same structural sites. A substitution that
   touched a comment, moved a line, changed an unrelated constant, or edited the wrong occurrence
   all fail it.
2. **The variant's constants are the point's constants.** The parsed constant table of the variant
   must equal the nominee's at every non-coordinate name and equal the declared point at every
   coordinate name. This is an independent check at a different level: check 1 compares bytes,
   this one compares what a parser makes of them.
3. **The nominee point runs the frozen bytes.** The nominee is not substituted at all -- its
   directory is copied verbatim, and :func:`materialise_point` requires the copy's bundle digest to
   equal the frozen candidate's.

The third guarantee -- that the variant really *executes* with the substituted value rather than
the nominee's -- cannot be established by reading files, so it is not attempted here. It is checked
at run time, in the worker process that imports the variant, by
:func:`crypto_trade.cup20.sweep.evaluate_materialised_point`.
"""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import math
import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path

# Private, and imported rather than reimplemented for the same reason ``harness`` imports
# ``_material_sides``: these three are the coordinate rule's own limits -- the size cap that runs
# before ``ast.parse`` is ever called on untrusted team source, and the error set that makes an
# unparseable entrypoint a refusal instead of a traceback. A second copy here could disagree with
# the copy ``verify_neighbourhood_coordinates`` uses, which would mean a file the verifier refused
# to parse being parsed anyway by the rewriter.
from crypto_trade.cup20.archive import (
    _MAX_ENTRYPOINT_BYTES,
    _UNPARSEABLE_SOURCE_ERRORS,
    _numeric,
    bundle_digest,
    module_level_numeric_assignments,
    verify_neighbourhood_coordinates,
)
from crypto_trade.cup20.neighbourhood import NeighbourhoodDeclaration
from crypto_trade.cup20.trials import ENTRYPOINT

_BLANK = "\x00"
"""What a coordinate literal is replaced by when proving two files differ only there.

One byte, the same in both files, so the two blanked texts realign regardless of how much longer or
shorter the substituted literal is. It cannot occur in the surrounding source: ``ast.parse`` rejects
a null byte in a source string, so a file containing one is refused as unparseable long before it
reaches here.
"""


class CoordinateSubstitutionError(RuntimeError):
    """A declared coordinate cannot be substituted into the frozen source."""


class VariantIntegrityError(RuntimeError):
    """A materialised point is not the frozen source with only its coordinates moved."""


def _parse(source: str, *, label: str) -> ast.Module:
    """Parse team source under the same guards the coordinate check parses it under."""
    if len(source.encode("utf-8")) > _MAX_ENTRYPOINT_BYTES:
        raise CoordinateSubstitutionError(f"{label}: entrypoint is larger than the frozen cap")
    try:
        return ast.parse(source)
    except _UNPARSEABLE_SOURCE_ERRORS as failure:
        raise CoordinateSubstitutionError(f"{label}: entrypoint is unparseable: {failure!r}") from (
            failure
        )


def _is_integer_literal(node: ast.expr) -> bool:
    """Whether this literal was written as an ``int`` rather than a ``float``.

    Preserved so substituting a point's own value back into the source reproduces the source: a
    neighbourhood declaration round-trips through JSON as ``float``, so ``FORMATION_BARS = 30``
    would come back as ``30.0`` and every variant would differ from the nominee in a way that has
    nothing to do with the coordinate being explored.
    """
    inner = node
    while isinstance(inner, ast.UnaryOp) and isinstance(inner.op, ast.USub):
        inner = inner.operand
    return isinstance(inner, ast.Constant) and isinstance(inner.value, int)


def _literal_text(node: ast.expr, value: float) -> str:
    """The replacement literal for one coordinate site."""
    if not math.isfinite(value):
        raise CoordinateSubstitutionError(
            f"a coordinate value must be finite, got {value!r}; a non-finite coordinate is not a "
            "point on any surface"
        )
    if _is_integer_literal(node) and float(value).is_integer():
        return str(int(value))
    return repr(float(value))


@dataclasses.dataclass(frozen=True, slots=True)
class _Edit:
    """One literal's byte span on one line, and what replaces it."""

    lineno: int
    start: int
    end: int
    text: str


def _coordinate_edits(
    source: str, coordinates: Sequence[str], render: object, *, label: str
) -> list[_Edit]:
    """Locate every module-level literal site for every declared coordinate.

    ``render`` is called as ``render(name, node)`` and returns the replacement text, so blanking
    (the proof) and substituting (the materialisation) walk the identical site list. A coordinate
    with no site, or whose literal spans more than one line, is refused rather than skipped: a
    skipped site is a point that silently stayed at the nominee's value.
    """
    tree = _parse(source, label=label)
    assignments = module_level_numeric_assignments(tree.body)
    edits: list[_Edit] = []
    for name in coordinates:
        nodes = assignments.get(name)
        if not nodes:
            raise CoordinateSubstitutionError(
                f"{label}: {name} is not a module-level numeric constant in {ENTRYPOINT}; every "
                "neighbourhood coordinate must be one (playbook section 6.1)"
            )
        for node in nodes:
            if node.end_lineno != node.lineno:
                raise CoordinateSubstitutionError(
                    f"{label}: {name}'s value spans lines {node.lineno}-{node.end_lineno}. A "
                    "coordinate must be a single-line numeric literal so the sweep can rewrite it "
                    "without touching anything else."
                )
            edits.append(
                _Edit(
                    lineno=int(node.lineno),
                    start=int(node.col_offset),
                    end=int(node.end_col_offset or node.col_offset),
                    text=str(render(name, node)),  # type: ignore[operator]
                )
            )
    return edits


def _apply(source: str, edits: Sequence[_Edit], *, label: str) -> str:
    """Rewrite every edited span, right to left so earlier spans keep their offsets.

    ``ast`` reports ``col_offset`` as a UTF-8 BYTE offset into the line, not a character index, so
    the splice is done on encoded bytes. On an ASCII file the two agree; on a file carrying a
    non-ASCII comment or docstring before a coordinate they do not, and slicing the ``str`` would
    cut the literal in the wrong place.
    """
    lines = [line.encode("utf-8") for line in source.splitlines(keepends=True)]
    for edit in sorted(edits, key=lambda item: (item.lineno, item.start), reverse=True):
        if not 1 <= edit.lineno <= len(lines):
            raise CoordinateSubstitutionError(f"{label}: line {edit.lineno} is out of range")
        line = lines[edit.lineno - 1]
        if not 0 <= edit.start <= edit.end <= len(line):
            raise CoordinateSubstitutionError(
                f"{label}: byte span [{edit.start}, {edit.end}) is out of range on line "
                f"{edit.lineno}"
            )
        lines[edit.lineno - 1] = line[: edit.start] + edit.text.encode("utf-8") + line[edit.end :]
    return b"".join(lines).decode("utf-8")


def substitute_coordinates(source: str, point: Mapping[str, float]) -> str:
    """The frozen source with every declared coordinate's literal rewritten to this point's value.

    Nothing else is touched -- not the surrounding expression, not a same-named constant inside a
    function or class body (which the coordinate rule already refuses to count), not a comment that
    happens to contain the number.
    """
    coordinates = tuple(point)
    edits = _coordinate_edits(
        source,
        coordinates,
        lambda name, node: _literal_text(node, float(point[name])),
        label="variant",
    )
    return _apply(source, edits, label="variant")


def _blanked(source: str, coordinates: Sequence[str], *, label: str) -> str:
    edits = _coordinate_edits(source, coordinates, lambda name, node: _BLANK, label=label)
    return _apply(source, edits, label=label)


def verify_variant_differs_only_in_coordinates(
    nominee_source: str, variant_source: str, coordinates: Sequence[str]
) -> None:
    """Prove, at the byte level, that the only difference is the coordinate literals.

    Each file's own coordinate literals are located in that file and replaced by the same single
    sentinel byte. Whatever remains is everything the file says that is not a coordinate value --
    including whitespace, comments, every other constant and the position of every line. The two
    remainders must be identical.

    This catches the substitution defects that would otherwise be invisible: an edit applied at the
    wrong offset, an occurrence missed (leaving the point at the nominee's value), an extra
    occurrence rewritten, or a rewrite that changed the file's structure rather than one literal.
    """
    if _blanked(nominee_source, coordinates, label="nominee") != _blanked(
        variant_source, coordinates, label="variant"
    ):
        raise VariantIntegrityError(
            "the materialised point differs from the frozen source outside its declared "
            "coordinates. Only the declared coordinate literals may move; nothing was evaluated."
        )


def _constant_table(source: str, *, label: str) -> dict[str, set[float]]:
    return {
        name: {value for value in (_numeric(node) for node in nodes) if value is not None}
        for name, nodes in module_level_numeric_assignments(
            _parse(source, label=label).body
        ).items()
    }


def verify_variant_constants(
    nominee_source: str, variant_source: str, point: Mapping[str, float]
) -> None:
    """Prove, at the parsed level, that the variant's constants are exactly this point's.

    Independent of the byte proof and deliberately redundant with it: the byte proof says nothing
    outside the coordinate spans moved, this says what a parser now reads *inside* them. A
    substitution that produced a syntactically valid literal of the wrong value passes the first
    and fails this one.
    """
    before = _constant_table(nominee_source, label="nominee")
    after = _constant_table(variant_source, label="variant")
    if set(before) != set(after):
        raise VariantIntegrityError(
            "the materialised point declares a different set of module-level numeric constants "
            f"than the frozen source: {sorted(set(after) ^ set(before))}"
        )
    for name, values in before.items():
        expected = {float(point[name])} if name in point else values
        if after[name] != expected:
            raise VariantIntegrityError(
                f"{name} is {sorted(after[name])} in the materialised point but should be "
                f"{sorted(expected)}"
            )


@dataclasses.dataclass(frozen=True, slots=True)
class MaterialisedPoint:
    """One neighbourhood point, written to disk as a complete candidate directory."""

    label: str
    is_nominee: bool
    coordinates: Mapping[str, float]
    root: Path
    entrypoint_sha256: str
    bundle_sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "is_nominee": self.is_nominee,
            "coordinates": {name: float(value) for name, value in sorted(self.coordinates.items())},
            "entrypoint_sha256": self.entrypoint_sha256,
            "bundle_sha256": self.bundle_sha256,
        }


def _copy_candidate(source_root: Path, destination: Path, entrypoint_source: str) -> None:
    """Copy the candidate directory byte for byte, with ``strategy.py`` replaced.

    Everything else travels: ``risk_policy.json`` is what the run is evaluated under, and a helper
    module beside the entrypoint can carry the whole mechanism. Symlinks and ``__pycache__`` are
    excluded, matching ``archive._files`` exactly, so the copy's ``bundle_digest`` is comparable
    with the frozen candidate's.
    """
    destination.mkdir(parents=True, exist_ok=False)
    for path in sorted(source_root.rglob("*")):
        if not path.is_file() or path.is_symlink() or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(source_root)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if relative.as_posix() == ENTRYPOINT:
            target.write_text(entrypoint_source)
        else:
            shutil.copyfile(path, target)


def materialise_point(
    candidate_root: str | Path,
    destination: str | Path,
    *,
    declaration: NeighbourhoodDeclaration,
    point: Mapping[str, float],
    is_nominee: bool,
    label: str,
) -> MaterialisedPoint:
    """Write one neighbourhood point as a candidate directory, and prove what it is.

    The nominee is **not** substituted. Its directory is copied verbatim and the copy's bundle
    digest is required to equal the frozen candidate's, so the nominee point provably runs the
    frozen bytes rather than a re-rendering of them -- which also means the nominee's vector out of
    a sweep is directly comparable with the same candidate's vector out of
    ``scripts/cup20_evaluate.py``.
    """
    root = Path(candidate_root)
    entry = root / ENTRYPOINT
    if not entry.is_file():
        raise CoordinateSubstitutionError(f"{entry} does not exist")
    nominee_source = entry.read_text()
    variant_source = nominee_source if is_nominee else substitute_coordinates(nominee_source, point)
    verify_variant_differs_only_in_coordinates(
        nominee_source, variant_source, declaration.coordinates
    )
    verify_variant_constants(nominee_source, variant_source, point)

    target = Path(destination)
    _copy_candidate(root, target, variant_source)
    digest = bundle_digest(target)
    if is_nominee and digest != bundle_digest(root):
        raise VariantIntegrityError(
            "the nominee point is not a byte-for-byte copy of the frozen candidate directory"
        )
    return MaterialisedPoint(
        label=label,
        is_nominee=is_nominee,
        coordinates={name: float(value) for name, value in point.items()},
        root=target,
        entrypoint_sha256=hashlib.sha256((target / ENTRYPOINT).read_bytes()).hexdigest(),
        bundle_sha256=digest,
    )


def point_label(index: int, point: Mapping[str, float], *, is_nominee: bool) -> str:
    """A short, stable name for one point: its index and its coordinates."""
    body = " ".join(f"{name}={float(point[name]):g}" for name in sorted(point))
    return f"{'nominee' if is_nominee else f'point-{index}'}  {body}"


def dry_run_materialisation(
    candidate_root: str | Path, declaration: NeighbourhoodDeclaration
) -> tuple[str, ...]:
    """Everything :func:`materialise_point` would refuse, without writing anything or running.

    Called by the free ``--check`` mode so a coordinate that verifies against the frozen source but
    cannot be *rewritten* in it -- a literal split across lines, say -- is found before a trial is
    spent rather than after.
    """
    root = Path(candidate_root)
    entry = root / ENTRYPOINT
    if not entry.is_file():
        return (f"{ENTRYPOINT}:missing-entrypoint",)
    try:
        nominee_source = entry.read_text()
    except (OSError, UnicodeError) as failure:
        return (f"{ENTRYPOINT}:unreadable-entrypoint:{failure!r}",)
    violations: list[str] = []
    for index, point in enumerate(declaration.all_points()):
        is_nominee = index == 0
        try:
            variant = (
                nominee_source if is_nominee else substitute_coordinates(nominee_source, point)
            )
            verify_variant_differs_only_in_coordinates(
                nominee_source, variant, declaration.coordinates
            )
            verify_variant_constants(nominee_source, variant, point)
        except (CoordinateSubstitutionError, VariantIntegrityError) as failure:
            violations.append(f"{point_label(index, point, is_nominee=is_nominee)}: {failure}")
    return tuple(violations)


def verify_declaration_or_refuse(
    candidate_root: str | Path, declaration: NeighbourhoodDeclaration
) -> None:
    """Every section 5/6.1 rule, checked before anything costs anything. Raises on the first fail.

    ``NeighbourhoodDeclaration.validate`` has already run inside ``load_declaration`` (point count,
    distinctness on the full coordinate vector, material variation above and below every
    coordinate, finite values). What is added here is the half that needs the frozen source: the
    coordinate-to-constant correspondence including the nominee's value equalling the frozen
    constant, and that every point can actually be materialised out of it.
    """
    coordinate_violations = verify_neighbourhood_coordinates(candidate_root, declaration)
    if coordinate_violations:
        listed = "\n".join(f"    {entry}" for entry in coordinate_violations)
        raise VariantIntegrityError(
            "the declared neighbourhood does not satisfy the coordinate rule (playbook section "
            f"6.1):\n{listed}\nNothing was evaluated."
        )
    substitution_violations = dry_run_materialisation(candidate_root, declaration)
    if substitution_violations:
        listed = "\n".join(f"    {entry}" for entry in substitution_violations)
        raise VariantIntegrityError(
            f"the declared neighbourhood cannot be materialised from the frozen source:\n{listed}\n"
            "Nothing was evaluated."
        )
