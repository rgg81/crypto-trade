"""The declared-neighbourhood sweep: what it materialises, what it refuses, and what it scores.

The sweep is the only place the number a team is actually ranked on comes from, so the mutations
that matter are the ones that would let it produce a plausible number that means nothing:

* **a variant that is not a variant.** If substitution silently failed -- wrong offset, wrong
  occurrence, an import that resolved to a cached module -- the sweep would run the nominee seven
  times, report a perfect plateau, and look better than a real one. Every test below that touches
  substitution is aimed at that single failure, at three levels: bytes, parsed constants, and the
  value the imported module actually bound.
* **a variant that changed something else.** Rewriting a comment, a docstring number, a class
  attribute or an unrelated constant would make the "point" a different strategy rather than the
  same strategy at a different coordinate.
* **scoring the nominee instead of the median.** The nominee is the maximum of a noisy surface;
  reporting it as the score is the exact bias section 7.2 exists to remove.
* **a neighbourhood that fails validation costing a trial.** The budget is twelve and there is no
  refund, so an unswept-able declaration has to be refused at the journal append.
* **fail-open on NaN.** ``statistics.median`` sorts, and NaN has no ordering, so one unusable point
  can hand back a finite, plausible median.
"""

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.config import IS_END, load_config
from crypto_trade.cup20.harness import check_candidate, load_team_module
from crypto_trade.cup20.neighbourhood import NeighbourhoodDeclaration, load_declaration
from crypto_trade.cup20.snapshot import load_snapshot
from crypto_trade.cup20.sweep import (
    UNMEASURED_BY_A_SWEEP,
    PointJob,
    PointOutcome,
    SweepError,
    _bound_coordinate_values,
    default_workers,
    evaluate_materialised_point,
    inert_points,
    load_neighbourhood,
    materialise_neighbourhood,
    median_bootstrap_fraction,
    run_neighbourhood_sweep,
)
from crypto_trade.cup20.variants import (
    CoordinateSubstitutionError,
    VariantIntegrityError,
    dry_run_materialisation,
    materialise_point,
    substitute_coordinates,
    verify_declaration_or_refuse,
    verify_variant_constants,
    verify_variant_differs_only_in_coordinates,
)
from crypto_trade.tournament.data import sha256_manifest

CONFIG_PATH = Path("tournament/cup20/config.toml")
CONFIG = load_config(CONFIG_PATH)
RAW = CONFIG.raw

MINIMAL_RISK_POLICY = {
    "schema_version": 1,
    "policy_id": "sweep-test",
    "same_boundary_reentry": True,
    "volatility_target": {
        "enabled": False,
        "lookback_days": 30,
        "annualized_target": 0.10,
        "minimum_scale": 0.5,
        "maximum_scale": 1.0,
    },
    "drawdown_brakes": [],
    "position_stop": {"enabled": False, "loss_fraction": 0.5, "cooldown_bars": 0},
    "time_stop": {"enabled": False, "maximum_holding_bars": 10, "cooldown_bars": 0},
    "turnover_limit": {"enabled": False, "maximum_one_way_turnover": 1.0},
    "side_scaling": {"long_scale": 1.0, "short_scale": 1.0},
}

# The coordinate genuinely governs behaviour: FORMATION_BARS is read into a DEFAULT ARGUMENT at
# import time, which is precisely the shape "set the module constant after importing" would fail
# to change. If the sweep were unsound, every point would trade the nominee's 30-bar signal.
CANDIDATE_SOURCE = '''"""A momentum book. The number 30 is in this docstring and must not move."""

FORMATION_BARS = 30
ENTRY_THRESHOLD = 0.50
UNRELATED = 30


def _horizon(lookback=FORMATION_BARS, threshold=ENTRY_THRESHOLD):
    """Default arguments bind at IMPORT time. This is the shape a post-import assignment misses."""
    return lookback, threshold


class Book:
    FORMATION_BARS = 999  # a class attribute of the same name: never a coordinate

    def __init__(self):
        self.lookback, self.threshold = _horizon()

    def target_weights(self, context, *, seed):
        if context.decision_time.weekday() != 0 or context.decision_time.hour != 0:
            return None
        scores = {}
        for symbol, frame in context.bars.items():
            closes = frame["close"].to_numpy(dtype=float)
            if len(closes) <= self.lookback:
                continue
            scores[symbol] = closes[-1] / closes[-1 - self.lookback] - 1.0
        chosen = {s: v for s, v in scores.items() if abs(v) > self.threshold * 0.01}
        if not chosen:
            return {}
        weight = 1.0 / len(chosen)
        return {s: (weight if v > 0 else -weight) for s, v in chosen.items()}


def build_strategy():
    return Book()
'''

NEIGHBOURHOOD = {
    "coordinates": ["FORMATION_BARS", "ENTRY_THRESHOLD"],
    "nominee": {"FORMATION_BARS": 30, "ENTRY_THRESHOLD": 0.50},
    "points": [
        {"FORMATION_BARS": 24, "ENTRY_THRESHOLD": 0.50},
        {"FORMATION_BARS": 36, "ENTRY_THRESHOLD": 0.50},
        {"FORMATION_BARS": 30, "ENTRY_THRESHOLD": 0.40},
        {"FORMATION_BARS": 30, "ENTRY_THRESHOLD": 0.60},
        {"FORMATION_BARS": 24, "ENTRY_THRESHOLD": 0.40},
        {"FORMATION_BARS": 36, "ENTRY_THRESHOLD": 0.60},
    ],
}


def _declaration(payload=None) -> NeighbourhoodDeclaration:
    body = NEIGHBOURHOOD if payload is None else payload
    return NeighbourhoodDeclaration(
        nominee={k: float(v) for k, v in body["nominee"].items()},
        points=tuple({k: float(v) for k, v in point.items()} for point in body["points"]),
        coordinates=tuple(body["coordinates"]),
    )


def _write_candidate(workspace: Path, *, source=CANDIDATE_SOURCE, neighbourhood=NEIGHBOURHOOD):
    candidate = workspace / "candidates" / "baseline"
    candidate.mkdir(parents=True)
    (candidate / "strategy.py").write_text(source)
    (candidate / "risk_policy.json").write_text(json.dumps(MINIMAL_RISK_POLICY))
    if neighbourhood is not None:
        (candidate / "neighbourhood.json").write_text(json.dumps(neighbourhood))
    return candidate


# --- substitution: the mechanism, at the byte level ----------------------------------------------


def test_substitution_moves_the_coordinate_and_nothing_that_merely_looks_like_it():
    """Kills the mutation: a textual search-and-replace on the number, or on the name.

    ``30`` also appears in the module docstring, in ``UNRELATED``, and as a class attribute
    ``Book.FORMATION_BARS = 999`` shares the coordinate's NAME. Only the module-level
    ``FORMATION_BARS`` assignment may move. A regex over the source moves the docstring; a
    name-keyed rewrite that did not respect scope moves the class attribute.
    """
    variant = substitute_coordinates(
        CANDIDATE_SOURCE, {"FORMATION_BARS": 24.0, "ENTRY_THRESHOLD": 0.6}
    )
    assert "\nFORMATION_BARS = 24\n" in variant
    assert "\nENTRY_THRESHOLD = 0.6\n" in variant
    assert "The number 30 is in this docstring" in variant
    assert "\nUNRELATED = 30\n" in variant
    assert "FORMATION_BARS = 999" in variant


def test_an_integer_coordinate_stays_an_integer_literal():
    """Kills the mutation: rendering every value with ``repr(float(...))``.

    A declaration round-trips through JSON as a float, so 24 arrives as ``24.0``. Writing
    ``FORMATION_BARS = 24.0`` into source that said ``30`` is a second, undeclared difference
    between the variant and the nominee -- an int became a float -- and a strategy that indexes
    ``closes[-1 - self.lookback]`` would then raise on it.
    """
    variant = substitute_coordinates(CANDIDATE_SOURCE, {"FORMATION_BARS": 24.0})
    assert "FORMATION_BARS = 24\n" in variant
    assert "24.0" not in variant


def test_a_negative_coordinate_round_trips_through_its_own_sign():
    source = "SKEW = -1.5\n\n\ndef build_strategy():\n    return None\n"
    assert "SKEW = -2.25\n" in substitute_coordinates(source, {"SKEW": -2.25})
    assert "SKEW = 0.75\n" in substitute_coordinates(source, {"SKEW": 0.75})


def test_a_coordinate_in_a_module_level_branch_is_substituted_at_every_site():
    """Kills the mutation: rewriting only the first occurrence.

    The coordinate rule permits the same value assigned more than once (only DIFFERENT values are
    a conflict). Leaving a second site at the nominee's value would make the executed constant
    depend on which branch ran -- and one of the two candidate points would silently be the
    nominee.
    """
    source = "if True:\n    LOOKBACK = 10\nelse:\n    LOOKBACK = 10\n"
    variant = substitute_coordinates(source, {"LOOKBACK": 20.0})
    assert variant.count("LOOKBACK = 20") == 2
    assert "LOOKBACK = 10" not in variant


def test_a_unicode_comment_before_the_coordinate_does_not_shift_the_edit():
    """Kills the mutation: slicing the line as ``str`` rather than as UTF-8 bytes.

    ``ast`` reports ``col_offset`` as a byte offset. On a line carrying a multi-byte character
    before the literal, a character-indexed splice cuts in the wrong place -- and the result may
    still parse, silently producing a different number.
    """
    source = "PARAM = 5  # café ☕\nEDGE = 7  # naïve\n"
    variant = substitute_coordinates(source, {"EDGE": 9.0})
    assert variant == "PARAM = 5  # café ☕\nEDGE = 9  # naïve\n"


def test_substituting_the_nominee_s_own_values_reproduces_the_frozen_source():
    """Kills the mutation: a substitution that perturbs the file even at the nominee's own point."""
    variant = substitute_coordinates(
        CANDIDATE_SOURCE, {"FORMATION_BARS": 30.0, "ENTRY_THRESHOLD": 0.50}
    )
    # 0.50 renders as 0.5, which is why the nominee point is COPIED rather than substituted; what
    # must hold is that the difference is confined to the coordinate literals.
    verify_variant_differs_only_in_coordinates(
        CANDIDATE_SOURCE, variant, ("FORMATION_BARS", "ENTRY_THRESHOLD")
    )
    verify_variant_constants(
        CANDIDATE_SOURCE, variant, {"FORMATION_BARS": 30.0, "ENTRY_THRESHOLD": 0.50}
    )


@pytest.mark.parametrize(
    ("tampered", "reason"),
    [
        (CANDIDATE_SOURCE.replace("UNRELATED = 30", "UNRELATED = 31"), "another constant moved"),
        (CANDIDATE_SOURCE.replace("must not move", "moved"), "a comment moved"),
        (
            CANDIDATE_SOURCE.replace("FORMATION_BARS = 30", "FORMATION_BARS = 30\nEXTRA = 1"),
            "a line was added",
        ),
        (
            CANDIDATE_SOURCE.replace("FORMATION_BARS = 999", "FORMATION_BARS = 998"),
            "a class attribute moved",
        ),
    ],
)
def test_the_byte_proof_rejects_a_variant_that_changed_anything_else(tampered, reason):
    """Kills the mutation: trusting the substitution instead of proving it.

    Each of these is a file that would run, produce numbers, and be reported as "the same strategy
    at a different coordinate" -- while actually being a different strategy.
    """
    with pytest.raises(VariantIntegrityError, match="outside its declared coordinates"):
        verify_variant_differs_only_in_coordinates(
            CANDIDATE_SOURCE, tampered, ("FORMATION_BARS", "ENTRY_THRESHOLD")
        )


def test_the_constant_proof_rejects_a_variant_whose_coordinate_is_the_wrong_value():
    """Kills the mutation: a substitution that wrote a valid literal of the wrong number.

    The byte proof cannot see this -- the difference IS inside the coordinate span, which is
    exactly where it is allowed to be. This is the second, independent level.
    """
    variant = substitute_coordinates(CANDIDATE_SOURCE, {"FORMATION_BARS": 24.0})
    with pytest.raises(VariantIntegrityError, match="FORMATION_BARS"):
        verify_variant_constants(CANDIDATE_SOURCE, variant, {"FORMATION_BARS": 36.0})


def test_the_constant_proof_rejects_a_variant_that_gained_or_lost_a_constant():
    variant = CANDIDATE_SOURCE + "\nSNEAKY = 1\n"
    with pytest.raises(VariantIntegrityError, match="different set of module-level"):
        verify_variant_constants(CANDIDATE_SOURCE, variant, {"FORMATION_BARS": 30.0})


@pytest.mark.parametrize(
    ("source", "coordinate", "fragment"),
    [
        ("def f():\n    LOOKBACK = 5\n", "LOOKBACK", "not a module-level numeric constant"),
        ("class C:\n    LOOKBACK = 5\n", "LOOKBACK", "not a module-level numeric constant"),
        ("LOOKBACK = 5 + 0\n", "LOOKBACK", "not a module-level numeric constant"),
        ("LOOKBACK = (\n    5\n) + 0\n", "LOOKBACK", "not a module-level numeric constant"),
        ("LOOKBACK = 5\n", "MISSING", "not a module-level numeric constant"),
    ],
)
def test_an_unsubstitutable_coordinate_is_refused_by_name(source, coordinate, fragment):
    """Kills the mutation: skipping a coordinate the rewriter cannot find.

    A skipped coordinate is a point that silently stayed at the nominee's value, which is the
    single defect that would make a whole sweep meaningless while looking perfect.
    """
    with pytest.raises(CoordinateSubstitutionError, match=fragment):
        substitute_coordinates(source, {coordinate: 9.0})


def test_a_multi_line_literal_is_refused_rather_than_spliced():
    """Kills the mutation: splicing a span whose start and end are on different lines.

    ``LOOKBACK = -\\\n    5`` is one ``UnaryOp`` node covering two lines. Editing it by
    ``[col_offset:end_col_offset]`` on the FIRST line would cut somewhere arbitrary.
    """
    source = "LOOKBACK = -\\\n    5\n"
    with pytest.raises(CoordinateSubstitutionError, match="spans lines"):
        substitute_coordinates(source, {"LOOKBACK": 9.0})


def test_a_non_finite_coordinate_value_is_refused():
    with pytest.raises(CoordinateSubstitutionError, match="must be finite"):
        substitute_coordinates("LOOKBACK = 5\n", {"LOOKBACK": float("nan")})


def test_unparseable_and_oversized_team_source_are_refusals_not_tracebacks():
    with pytest.raises(CoordinateSubstitutionError, match="unparseable"):
        substitute_coordinates("def (:\n", {"X": 1.0})
    with pytest.raises(CoordinateSubstitutionError, match="larger than the frozen cap"):
        substitute_coordinates("X = 1\n# " + "a" * 300_000 + "\n", {"X": 2.0})


# --- materialisation on disk ---------------------------------------------------------------------


def test_the_nominee_point_is_the_frozen_directory_byte_for_byte(tmp_path):
    """Kills the mutation: re-rendering the nominee through the substituter.

    ``ENTRY_THRESHOLD = 0.50`` would come back as ``0.5``: harmless to behaviour, fatal to the one
    cross-check that proves the sweep is the organiser's pipeline -- that the nominee's vector out
    of a sweep equals the same candidate's vector out of ``cup20_evaluate.py``, which runs the
    frozen bytes.
    """
    candidate = _write_candidate(tmp_path / "team-01")
    declaration = _declaration()
    point = materialise_point(
        candidate,
        tmp_path / "sweep" / "point-00",
        declaration=declaration,
        point=declaration.nominee,
        is_nominee=True,
        label="nominee",
    )
    assert (point.root / "strategy.py").read_bytes() == (candidate / "strategy.py").read_bytes()
    assert (point.root / "risk_policy.json").read_bytes() == (
        candidate / "risk_policy.json"
    ).read_bytes()


def test_every_materialised_point_is_a_distinct_file_with_a_distinct_digest(tmp_path):
    """Kills the mutation that would be invisible in the numbers: seven copies of one point.

    A sweep that ran the nominee seven times reports a flawless plateau. Distinct digests are the
    cheapest evidence that the seven files are seven files.
    """
    candidate = _write_candidate(tmp_path / "team-01")
    points = materialise_neighbourhood(candidate, tmp_path / "sweep", _declaration())
    assert len(points) == 7
    assert points[0].is_nominee and not any(p.is_nominee for p in points[1:])
    assert len({p.entrypoint_sha256 for p in points}) == 7
    assert len({p.root for p in points}) == 7


def test_a_materialised_point_carries_the_whole_candidate_directory(tmp_path):
    """Kills the mutation: copying only ``strategy.py``.

    ``risk_policy.json`` is what the run is evaluated under, and a helper module beside the
    entrypoint can carry the whole mechanism.
    """
    workspace = tmp_path / "team-01"
    candidate = _write_candidate(workspace)
    (candidate / "helper.py").write_text("SCALE = 2.0\n")
    points = materialise_neighbourhood(candidate, tmp_path / "sweep", _declaration())
    for point in points:
        assert (point.root / "risk_policy.json").is_file()
        assert (point.root / "helper.py").read_text() == "SCALE = 2.0\n"


def test_the_materialised_variant_really_executes_with_the_substituted_constant(tmp_path):
    """Kills THE mutation this whole module exists to prevent: a point that ran as the nominee.

    Files are not evidence about what an interpreter bound. This imports each materialised variant
    and reads the constant back out of the executed module's namespace -- and also reads it out of
    the DEFAULT ARGUMENT the class captured at import time, which is the exact place "assign the
    module constant after importing" would have left at 30 for every point.
    """
    candidate = _write_candidate(tmp_path / "team-01")
    points = materialise_neighbourhood(candidate, tmp_path / "sweep", _declaration())
    bound = []
    for point in points:
        module = load_team_module(point.root)
        assert _bound_coordinate_values(module, point.coordinates) == pytest.approx(
            dict(point.coordinates)
        )
        strategy = module.build_strategy()
        bound.append((strategy.lookback, strategy.threshold))
    assert bound[0] == (30, 0.50)
    assert sorted(set(bound)) == [
        (24, 0.40),
        (24, 0.50),
        (30, 0.40),
        (30, 0.50),
        (30, 0.60),
        (36, 0.50),
        (36, 0.60),
    ]


def test_the_runtime_check_refuses_a_module_that_bound_a_different_value():
    """Kills the mutation: trusting the file and never reading the module back.

    This is what catches a stale ``__pycache__``, a copy that did not land, an import that
    resolved elsewhere, or a module that rebinds its own constant during import.
    """

    class Module:
        FORMATION_BARS = 30.0

    with pytest.raises(SweepError, match="is not the point that was declared"):
        _bound_coordinate_values(Module(), {"FORMATION_BARS": 24.0})


def test_the_runtime_check_refuses_a_coordinate_that_is_not_bound_at_all():
    class Module:
        pass

    with pytest.raises(SweepError, match="not bound after importing"):
        _bound_coordinate_values(Module(), {"FORMATION_BARS": 24.0})


def test_the_runtime_check_refuses_a_coordinate_that_is_not_a_number():
    class Module:
        FORMATION_BARS = True

    with pytest.raises(SweepError, match="not a number"):
        _bound_coordinate_values(Module(), {"FORMATION_BARS": 1.0})


def test_a_worker_refuses_a_variant_whose_bytes_changed_after_materialisation(tmp_path):
    """Kills the mutation: dropping the digest re-check inside the worker.

    Between the parent proving what a variant is and the worker executing it, the file is only as
    trustworthy as the filesystem. The worker hashes it again before importing.
    """
    candidate = _write_candidate(tmp_path / "team-01")
    points = materialise_neighbourhood(candidate, tmp_path / "sweep", _declaration())
    target = points[1]
    (target.root / "strategy.py").write_text(CANDIDATE_SOURCE)
    job = PointJob(
        label=target.label,
        is_nominee=False,
        coordinates=dict(target.coordinates),
        root=str(target.root),
        entrypoint_sha256=target.entrypoint_sha256,
        snapshot_root="unused",
        config_path=str(CONFIG_PATH),
        seed=1,
        is_start=str(IS_END),
    )
    with pytest.raises(SweepError, match="the file changed between materialisation and execution"):
        evaluate_materialised_point(job)


# --- declaration validation, before anything costs anything --------------------------------------


@pytest.mark.parametrize(
    ("mutate", "fragment"),
    [
        (lambda body: body | {"points": body["points"][:4]}, "needs at least 7 points"),
        (
            lambda body: body | {"points": [*body["points"][:5], body["points"][0]]},
            "duplicates another declared point",
        ),
        (
            lambda body: body | {"points": [*body["points"][:5], dict(body["nominee"])]},
            "duplicates the nominee",
        ),
        (
            # Both points that carried an upward ENTRY_THRESHOLD variation replaced by an epsilon
            # nudge: strictly above the nominee, and an exploration of nothing.
            lambda body: (
                body
                | {
                    "points": [
                        {"FORMATION_BARS": 24, "ENTRY_THRESHOLD": 0.50},
                        {"FORMATION_BARS": 36, "ENTRY_THRESHOLD": 0.50},
                        {"FORMATION_BARS": 30, "ENTRY_THRESHOLD": 0.40},
                        {"FORMATION_BARS": 30, "ENTRY_THRESHOLD": 0.5001},
                        {"FORMATION_BARS": 24, "ENTRY_THRESHOLD": 0.40},
                        {"FORMATION_BARS": 36, "ENTRY_THRESHOLD": 0.5001},
                    ]
                }
            ),
            "no material upward variation",
        ),
        (
            lambda body: (
                body
                | {
                    "points": [
                        {"FORMATION_BARS": 36, "ENTRY_THRESHOLD": 0.50},
                        {"FORMATION_BARS": 36, "ENTRY_THRESHOLD": 0.40},
                        {"FORMATION_BARS": 36, "ENTRY_THRESHOLD": 0.60},
                        {"FORMATION_BARS": 42, "ENTRY_THRESHOLD": 0.50},
                        {"FORMATION_BARS": 42, "ENTRY_THRESHOLD": 0.40},
                        {"FORMATION_BARS": 42, "ENTRY_THRESHOLD": 0.60},
                    ]
                }
            ),
            "no material downward variation",
        ),
        (
            lambda body: body | {"points": [{"FORMATION_BARS": 24}, *body["points"][1:]]},
            "omits coordinates",
        ),
        (
            lambda body: (
                body | {"points": [{**body["points"][0], "GHOST": 1.0}, *body["points"][1:]]}
            ),
            "unknown coordinates",
        ),
        (
            lambda body: (
                body
                | {
                    "points": [
                        {"FORMATION_BARS": float("nan"), "ENTRY_THRESHOLD": 0.5},
                        *body["points"][1:],
                    ]
                }
            ),
            "non-finite value",
        ),
    ],
)
def test_every_declaration_rule_refuses_on_its_own(tmp_path, mutate, fragment):
    """Kills the mutation: one broad "the neighbourhood is invalid" check.

    Each rule closes a different lever on the median. Padding one side of the nominee moves it;
    an epsilon variation explores nothing; a NaN coordinate slips past every comparison because
    every IEEE-754 comparison with NaN is False.
    """
    path = tmp_path / "neighbourhood.json"
    path.write_text(json.dumps(mutate(dict(NEIGHBOURHOOD))))
    with pytest.raises(ValueError, match=fragment):
        load_declaration(path)


def test_a_missing_neighbourhood_is_refused_by_name(tmp_path):
    candidate = _write_candidate(tmp_path / "team-01", neighbourhood=None)
    with pytest.raises(VariantIntegrityError, match="does not exist"):
        load_neighbourhood(candidate)


@pytest.mark.parametrize(
    ("source", "fragment"),
    [
        (
            CANDIDATE_SOURCE.replace("FORMATION_BARS = 30", "FORMATION_BARS = 31"),
            "differs-from-frozen",
        ),
        (
            CANDIDATE_SOURCE.replace(
                "FORMATION_BARS = 30", "FORMATION_BARS = 30\nif True:\n    FORMATION_BARS = 7"
            ),
            "conflicting-module-level-values",
        ),
        (
            CANDIDATE_SOURCE.replace("\nFORMATION_BARS = 30\n", "\n"),
            "absent-from-frozen-source",
        ),
    ],
)
def test_the_coordinate_rule_is_enforced_before_a_point_is_materialised(tmp_path, source, fragment):
    candidate = _write_candidate(tmp_path / "team-01", source=source)
    with pytest.raises(VariantIntegrityError, match=fragment):
        verify_declaration_or_refuse(candidate, _declaration())


_SPLIT_LITERAL_SOURCE = (
    "SKEW = -\\\n    1.5\n\n\n"
    "class Book:\n"
    "    def target_weights(self, context, *, seed):\n"
    "        return None\n\n\n"
    "def build_strategy():\n    return Book()\n"
)
_SPLIT_LITERAL_NEIGHBOURHOOD = {
    "coordinates": ["SKEW"],
    "nominee": {"SKEW": -1.5},
    "points": [
        {"SKEW": -1.0},
        {"SKEW": -2.0},
        {"SKEW": -0.5},
        {"SKEW": -2.5},
        {"SKEW": -0.25},
        {"SKEW": -3.0},
    ],
}


def test_a_coordinate_that_verifies_but_cannot_be_rewritten_is_caught_before_the_sweep(tmp_path):
    """Kills the mutation: assuming the coordinate rule implies substitutability.

    These are two different questions and exactly one shape separates them. ``SKEW = -\\<newline>
    1.5`` is a ``UnaryOp`` whose value node genuinely spans two lines: ``_numeric`` reads it as
    -1.5 so the coordinate rule PASSES, while a splice by ``[col_offset:end_col_offset]`` on the
    first line would cut at an arbitrary position. Without the dry run, a team would discover this
    only after its neighbourhood trial had been spent.
    """
    candidate = _write_candidate(
        tmp_path / "team-01",
        source=_SPLIT_LITERAL_SOURCE,
        neighbourhood=_SPLIT_LITERAL_NEIGHBOURHOOD,
    )
    declaration = _declaration(_SPLIT_LITERAL_NEIGHBOURHOOD)
    from crypto_trade.cup20.archive import verify_neighbourhood_coordinates

    assert verify_neighbourhood_coordinates(candidate, declaration) == ()
    violations = dry_run_materialisation(candidate, declaration)
    assert len(violations) == 7
    assert all("spans lines" in entry for entry in violations)
    with pytest.raises(VariantIntegrityError, match="cannot be materialised"):
        verify_declaration_or_refuse(candidate, declaration)


def test_the_free_check_reports_the_substitution_dry_run(tmp_path):
    """Kills the mutation: leaving the dry run out of ``--check``, so a team pays a trial to find
    a coordinate that cannot be rewritten."""
    workspace = tmp_path / "team-01"
    candidate = _write_candidate(workspace)
    report = check_candidate(
        candidate_root=candidate,
        workspace_root=workspace,
        team_id="team-01",
        candidate_id="baseline",
        source_sha256="a" * 64,
    )
    assert report.ok
    assert report.neighbourhood_points == 7
    assert report.substitution_violations == ()
    assert "sweep materialisation  ok" in report.render()

    broken = tmp_path / "team-02"
    broken_candidate = _write_candidate(
        broken,
        source=_SPLIT_LITERAL_SOURCE,
        neighbourhood=_SPLIT_LITERAL_NEIGHBOURHOOD,
    )
    failed = check_candidate(
        candidate_root=broken_candidate,
        workspace_root=broken,
        team_id="team-02",
        candidate_id="baseline",
        source_sha256="a" * 64,
    )
    assert not failed.ok
    assert failed.substitution_violations
    assert "VIOLATIONS" in failed.render()


# --- the median, and what it must not fail open on ------------------------------------------------


def test_the_median_bootstrap_fraction_is_the_per_point_median():
    outcomes = [_outcome(value) for value in (0.10, 0.90, 0.50)]
    assert median_bootstrap_fraction(outcomes) == pytest.approx(0.50)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_one_unusable_point_makes_the_neighbourhood_bootstrap_nan(bad):
    """Kills the mutation: ``statistics.median`` over a list containing NaN.

    NaN has no ordering, so ``nan < x`` and ``x < nan`` are both False and the sorted run puts it
    wherever the sort algorithm happens to. The median comes back finite and plausible with a
    non-number behind it -- and the confidence floor is the one term whose whole job is to
    penalise.
    """
    for order in ([bad, 0.9, 0.9], [0.9, bad, 0.9], [0.9, 0.9, bad]):
        outcomes = [_outcome(value) for value in order]
        assert math.isnan(median_bootstrap_fraction(outcomes)), order


def test_the_median_bootstrap_fraction_requires_a_point():
    with pytest.raises(ValueError, match="at least one point"):
        median_bootstrap_fraction([])


def _scored_outcome(label: str, sharpe: float, drawdown: float, *, nominee: bool = False):
    """A point carrying a real metric vector, so inertness is decidable from it."""
    return PointOutcome(
        label=label,
        is_nominee=nominee,
        coordinates={},
        entrypoint_sha256="a" * 64,
        bound_constants={},
        scored={"net_sharpe": sharpe, "max_drawdown": drawdown},  # type: ignore[arg-type]
        bootstrap_positive_fraction=0.99,
        cost_levels={},
        fold_sharpes={},
        exposure_caps={},
        risk_scalars={},
        observed_roles=(),
        seconds=0.0,
    )


def test_a_point_reproducing_the_nominee_exactly_is_inert():
    """The quantised-coordinate exploit: a declared variation that lands in the same cell.

    ``round(n * fraction)`` over twenty names moves the *coordinate* by the required 5% and the
    *book* not at all, so the point sits on the nominee and drags the median onto the peak.
    """
    outcomes = [
        _scored_outcome("nominee", 1.10, 0.12, nominee=True),
        _scored_outcome("SLEEVE_FRACTION=0.27", 1.10, 0.12),
        _scored_outcome("SLEEVE_FRACTION=0.33", 0.94, 0.15),
    ]
    assert inert_points(outcomes) == ("SLEEVE_FRACTION=0.27",)


def test_a_point_differing_in_any_single_metric_is_not_inert():
    """Kills the mutation: comparing one headline metric instead of the whole vector.

    A coordinate can leave Sharpe untouched to the last bit and still change the drawdown -- that
    is a book that moved, and the point is a real observation.
    """
    outcomes = [
        _scored_outcome("nominee", 1.10, 0.12, nominee=True),
        _scored_outcome("moved_drawdown_only", 1.10, 0.13),
    ]
    assert inert_points(outcomes) == ()


def test_two_nan_metrics_count_as_the_same_measurement():
    """Kills the mutation: bare ``==`` on a vector carrying NaN.

    ``nan != nan``, so a naive comparison calls two identical unusable runs *different* and lets
    the most degenerate neighbourhood of all -- every point unusable -- pass as exploration.
    """
    outcomes = [
        _scored_outcome("nominee", math.nan, 0.12, nominee=True),
        _scored_outcome("also_nan", math.nan, 0.12),
    ]
    assert inert_points(outcomes) == ("also_nan",)


def test_inertness_is_never_concluded_from_an_absence_of_metrics():
    """An empty vector holds every dimension constant, which is not the same as measuring no change.

    ``all()`` over no keys is True. Since this verdict voids a team's sweep, it must never rest on
    a comparison that did not happen.
    """
    assert inert_points([_outcome(0.99), _outcome(0.99)]) == ()


def test_the_nominee_is_never_its_own_inert_point():
    assert inert_points([_scored_outcome("nominee", 1.10, 0.12, nominee=True)]) == ()


def _outcome(bootstrap: float) -> PointOutcome:
    return PointOutcome(
        label="x",
        is_nominee=False,
        coordinates={},
        entrypoint_sha256="a" * 64,
        bound_constants={},
        scored={},  # type: ignore[arg-type]
        bootstrap_positive_fraction=bootstrap,
        cost_levels={},
        fold_sharpes={},
        exposure_caps={},
        risk_scalars={},
        observed_roles=(),
        seconds=0.0,
    )


def test_the_worker_default_never_exceeds_the_point_count():
    """Kills the mutation: a default that helps itself to every core.

    Phase 1 runs twelve teams against one machine; a sweep that took twenty workers would slow
    eleven other teams down while its own seven points queued anyway.
    """
    assert default_workers(1) == 1
    assert default_workers(2) == 2
    assert 1 <= default_workers(7) <= 4
    assert 1 <= default_workers(64) <= 4


@pytest.mark.parametrize("workers", [0, -1])
def test_a_non_positive_worker_count_is_refused(workers):
    """Kills the mutation: ``max_workers=0``, which ``ProcessPoolExecutor`` raises on much later
    and with a message about a pool rather than about an argument the caller passed."""
    from crypto_trade.cup20.sweep import _run_jobs

    with pytest.raises(ValueError, match="workers must be at least 1"):
        _run_jobs([], workers=workers)


# --- one real sweep, end to end -------------------------------------------------------------------


def _write_snapshot(root: Path, *, days: int = 1097, symbols=("AUSDT", "BUSDT")) -> Path:
    """A synthetic in-sample snapshot ON DISK, because every worker loads it from a path."""
    root.mkdir(parents=True, exist_ok=True)
    periods = days * 3
    times = pd.date_range(end=IS_END - pd.Timedelta(hours=8), periods=periods, freq="8h")
    generator = np.random.default_rng(11)
    rows = []
    prices: dict[str, np.ndarray] = {}
    for index, symbol in enumerate(symbols):
        steps = generator.normal(0.0004 * (1 if index % 2 == 0 else -1), 0.01, periods)
        price = 100.0 * np.cumprod(1.0 + steps)
        prices[symbol] = price
        rows.append(
            pd.DataFrame(
                {
                    "open_time": times,
                    "symbol": symbol,
                    "open": price,
                    "high": price * 1.01,
                    "low": price * 0.99,
                    "close": price,
                    "volume": 1e6,
                    "quote_volume": 1e8,
                }
            )
        )
    bars = pd.concat(rows, ignore_index=True)
    funding = pd.DataFrame(
        {
            "funding_time": np.tile(times, len(symbols)),
            "symbol": np.repeat(list(symbols), len(times)),
            "funding_rate": 0.0001,
            "mark_price": np.concatenate([prices[symbol] for symbol in symbols]),
        }
    )
    marks = bars[["open_time", "symbol", "open"]].rename(
        columns={"open_time": "mark_time", "open": "mark_price"}
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": [times[0]] * len(symbols),
            "symbol": list(symbols),
            "liquidity_rank": list(range(1, len(symbols) + 1)),
            "trailing_quote_volume": [1e8] * len(symbols),
        }
    )
    metadata = pd.DataFrame({"symbol": list(symbols), "contract_type": "PERPETUAL"})
    frames = {
        "bars": bars,
        "funding": funding,
        "mark_prices": marks,
        "membership": membership,
        "contract_metadata": metadata,
    }
    for name, frame in frames.items():
        frame.to_parquet(root / f"{name}.parquet", index=False)
    names = ["bars", "funding", "mark_prices", "membership", "contract_metadata"]
    digest, entries = sha256_manifest([root / f"{n}.parquet" for n in names], root=root)
    (root / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "manifest_sha256": digest,
                "window_start": str(times[0]),
                "window_end": str(IS_END),
                "files": entries,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return root


@pytest.fixture(scope="module")
def real_sweep(tmp_path_factory):
    """One REAL seven-point sweep on a synthetic snapshot, at more than one worker.

    Everything that can be pinned in milliseconds is pinned above. What is left here is only what
    needs real runs: seven separately materialised files, seven separately spawned interpreters, a
    real median across them, a real ``positive_point_fraction``, and the real gate vector.
    """
    root = tmp_path_factory.mktemp("cup20-sweep")
    snapshot_root = _write_snapshot(root / "snapshot")
    workspace = root / "team-01"
    candidate = _write_candidate(workspace)
    snapshot = load_snapshot(snapshot_root)
    is_start = pd.Timestamp(snapshot.bars["open_time"].min())
    return run_neighbourhood_sweep(
        raw=RAW,
        config_path=CONFIG_PATH,
        snapshot_root=snapshot_root,
        snapshot_sha256=snapshot.manifest_sha256,
        candidate_root=candidate,
        workspace_root=workspace,
        sweep_root=root / "variants",
        team_id="team-01",
        candidate_id="baseline",
        seed=20240101,
        declared_roles=("long", "short"),
        trial_sequence=5,
        accepted_trials=5,
        source_sha256="a" * 64,
        is_start=is_start,
        workers=3,
    )


def test_the_sweep_ran_every_declared_point_including_the_nominee(real_sweep):
    assert len(real_sweep.outcomes) == 7
    assert real_sweep.outcomes[0].is_nominee
    assert real_sweep.outcomes[0].coordinates == {"FORMATION_BARS": 30.0, "ENTRY_THRESHOLD": 0.5}


def test_every_point_actually_bound_its_own_coordinates(real_sweep):
    """Kills the mutation: seven runs of the nominee.

    Each worker read the constants back out of its own imported module; those values travel in the
    packet. Seven distinct coordinate vectors mean seven distinct executions.
    """
    bound = {tuple(sorted(o.bound_constants.items())) for o in real_sweep.outcomes}
    assert len(bound) == 7
    for outcome in real_sweep.outcomes:
        assert outcome.bound_constants == pytest.approx(dict(outcome.coordinates))


def test_the_points_produced_genuinely_different_books(real_sweep):
    """Kills the mutation that every other check would still pass: a coordinate that is bound
    correctly and read by nothing.

    If the sweep were sound but the coordinate inert, the metric vectors would be identical and the
    plateau would be a tautology rather than a finding. This candidate's coordinate governs its
    formation horizon and its selectivity, so the trade counts must differ.
    """
    trades = {outcome.scored["trade_count"] for outcome in real_sweep.outcomes}
    assert len(trades) > 1


def test_the_score_is_the_median_and_the_nominee_is_marked_as_not_the_score(real_sweep):
    """Kills the mutation section 7.2 exists to prevent: reporting the nominated point."""
    for key in real_sweep.median:
        values = sorted(float(o.scored[key]) for o in real_sweep.outcomes)
        assert real_sweep.median[key] == pytest.approx(values[len(values) // 2])
    text = real_sweep.render()
    assert "YOUR SCORE" in text
    assert "the per-metric MEDIAN" in text
    assert "This is NOT your score" in text
    payload = real_sweep.as_dict()
    assert payload["score_is_the_neighbourhood_median"] is True
    assert set(payload["nominee_diagnostic_only"]) == set(payload["median"])


def test_the_sweep_reports_the_positive_point_fraction_against_the_seventy_percent_floor(
    real_sweep,
):
    assert 0.0 <= real_sweep.positive_point_fraction <= 1.0
    assert real_sweep.positive_point_fraction_floor == pytest.approx(0.70)
    expected = sum(
        1
        for outcome in real_sweep.outcomes
        if outcome.scored["annualized_return"] > 0.0 and outcome.scored["double_cost_sharpe"] > 0.0
    ) / len(real_sweep.outcomes)
    assert real_sweep.positive_point_fraction == pytest.approx(expected)
    detail = next(d for d in real_sweep.gate_details if d.name == "neighbourhood_positive_fraction")
    assert detail.measured, "a sweep MEASURES this gate; that is half of why it exists"
    assert detail.observed == pytest.approx(real_sweep.positive_point_fraction)
    assert detail.floor == pytest.approx(0.70)
    # Kills the mutation the single-point packet's own note would otherwise carry into the sweep:
    # "assumed; a single point cannot measure a neighbourhood" attached to a MEASURED value tells a
    # team the number it is failing on was invented by the harness. Same defect class as an
    # assumption rendered as a finding, in the other direction.
    assert "assumed" not in detail.note
    assert "assumed" not in real_sweep.render()


def test_the_sweep_still_never_prints_qualified(real_sweep):
    """Kills the mutation: treating a measured neighbourhood as a complete verdict.

    The sign inversion is a separate trial, so the sweep is supplied its answer at a passing value
    and must subtract it again.
    """
    assert "QUALIFIED" not in real_sweep.verdict.upper().replace("NOT QUALIFIED", "")
    assert real_sweep.unmeasured_gates == UNMEASURED_BY_A_SWEEP
    unmeasured = {d.name for d in real_sweep.gate_details if not d.measured}
    assert unmeasured == set(UNMEASURED_BY_A_SWEEP)
    assert not set(real_sweep.measured_failures) & set(UNMEASURED_BY_A_SWEEP)


def test_the_sweep_carries_each_point_s_executed_file_digest(real_sweep):
    digests = [outcome.entrypoint_sha256 for outcome in real_sweep.outcomes]
    assert len(set(digests)) == 7
    assert all(len(digest) == 64 for digest in digests)
    assert all(digest in real_sweep.render() for digest in digests)


def test_the_sweep_packet_renders_and_serialises(real_sweep):
    json.dumps(real_sweep.as_dict(), allow_nan=False)
    text = real_sweep.render()
    assert "neighbourhood sweep" in text
    assert "trial-adjusted confidence" in text
    assert f"{len(real_sweep.outcomes)} including the nominee" in text


def test_the_answer_does_not_depend_on_how_many_workers_ran_it(tmp_path_factory, real_sweep):
    """Kills the mutation that makes parallelism unsound: state shared between points.

    Parallelism is only worth having if it is the same answer. A worker that reused an interpreter,
    a snapshot object mutated by one point and read by the next, or a seed derived from a worker
    index would all show up here as a different median.
    """
    root = tmp_path_factory.mktemp("cup20-sweep-serial")
    snapshot_root = _write_snapshot(root / "snapshot")
    workspace = root / "team-01"
    candidate = _write_candidate(workspace)
    snapshot = load_snapshot(snapshot_root)
    serial = run_neighbourhood_sweep(
        raw=RAW,
        config_path=CONFIG_PATH,
        snapshot_root=snapshot_root,
        snapshot_sha256=snapshot.manifest_sha256,
        candidate_root=candidate,
        workspace_root=workspace,
        sweep_root=root / "variants",
        team_id="team-01",
        candidate_id="baseline",
        seed=20240101,
        declared_roles=("long", "short"),
        trial_sequence=5,
        accepted_trials=5,
        source_sha256="a" * 64,
        is_start=pd.Timestamp(snapshot.bars["open_time"].min()),
        workers=2,
    )
    assert dict(serial.median) == pytest.approx(dict(real_sweep.median))
    assert serial.positive_point_fraction == real_sweep.positive_point_fraction
    assert [o.entrypoint_sha256 for o in serial.outcomes] == [
        o.entrypoint_sha256 for o in real_sweep.outcomes
    ]


def test_a_point_that_fails_names_the_point_rather_than_losing_the_sweep(tmp_path):
    """Kills the mutation: a bare traceback out of a pool, which names a future and not a point."""
    workspace = tmp_path / "team-01"
    candidate = _write_candidate(
        workspace,
        source=CANDIDATE_SOURCE.replace(
            "def build_strategy():", "raise RuntimeError('boom')\n\n\ndef build_strategy():"
        ),
    )
    with pytest.raises(SweepError, match="did not complete"):
        run_neighbourhood_sweep(
            raw=RAW,
            config_path=CONFIG_PATH,
            snapshot_root=str(tmp_path / "missing-snapshot"),
            snapshot_sha256="a" * 64,
            candidate_root=candidate,
            workspace_root=workspace,
            sweep_root=tmp_path / "variants",
            team_id="team-01",
            candidate_id="baseline",
            seed=1,
            declared_roles=("long",),
            trial_sequence=1,
            accepted_trials=1,
            source_sha256="a" * 64,
            is_start=pd.Timestamp("2020-08-17T00:00:00Z"),
            workers=2,
        )


def test_the_blindness_scan_runs_before_any_point_is_materialised(tmp_path):
    """Kills the mutation: scanning after the sweep, or not at all.

    The sweep imports team code seven times. A scan that ran afterwards would report on a tree the
    imported code had already had seven chances to rewrite.
    """
    from crypto_trade.cup20.harness import BlindnessViolationError

    workspace = tmp_path / "team-01"
    candidate = _write_candidate(workspace)
    (workspace / "research").mkdir()
    (workspace / "research" / "notes.md").write_text("data/cup20/sealed\n")
    sweep_root = tmp_path / "variants"
    with pytest.raises(BlindnessViolationError, match="data/cup20/sealed"):
        run_neighbourhood_sweep(
            raw=RAW,
            config_path=CONFIG_PATH,
            snapshot_root=str(tmp_path / "missing"),
            snapshot_sha256="a" * 64,
            candidate_root=candidate,
            workspace_root=workspace,
            sweep_root=sweep_root,
            team_id="team-01",
            candidate_id="baseline",
            seed=1,
            declared_roles=("long",),
            trial_sequence=1,
            accepted_trials=1,
            source_sha256="a" * 64,
            is_start=pd.Timestamp("2020-08-17T00:00:00Z"),
            workers=1,
        )
    assert not sweep_root.exists(), "points were materialised before the workspace was scanned"


def test_the_assumed_note_still_appears_when_the_gate_is_genuinely_unmeasured():
    """The other half of the same rule: a single point must still say the value was assumed.

    Kills the mutation of removing the note outright rather than making it conditional, which would
    let ``cup20_evaluate.py``'s single-point packet print a bare ``1.000000  required >= 0.7``
    against a gate marked ``----``, with nothing saying the 1.0 was supplied by the harness.
    """
    from crypto_trade.cup20.harness import gate_details
    from crypto_trade.cup20.scored_metrics import ASSEMBLED_METRIC_KEYS

    scored = dict.fromkeys(ASSEMBLED_METRIC_KEYS, 0.5)
    for unmeasured, expected in ((("neighbourhood_positive_fraction",), True), ((), False)):
        detail = gate_details(
            {"neighbourhood_positive_fraction": True},
            scored,
            floors=RAW["floors"],
            statistics_config=RAW["statistics"],
            research_config=RAW["research"],
            declared_roles=("long",),
            observed_roles=("long",),
            neighbourhood_positive_fraction=1.0,
            confidence=1.0,
            unmeasured=unmeasured,
        )[0]
        assert ("assumed" in detail.note) is expected
