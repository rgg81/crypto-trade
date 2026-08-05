"""Tests for the CUP-20 neighbourhood declaration and per-metric median scoring."""

import json

import pytest

from crypto_trade.cup20.neighbourhood import (
    NeighbourhoodDeclaration,
    load_declaration,
    median_metrics,
    positive_point_fraction,
)


def _declaration(nominee=None, points=None, coordinates=("lookback", "threshold")):
    nominee = nominee or {"lookback": 60.0, "threshold": 1.0}
    if points is None:
        points = [
            {"lookback": 40.0, "threshold": 1.0},
            {"lookback": 80.0, "threshold": 1.0},
            {"lookback": 60.0, "threshold": 0.8},
            {"lookback": 60.0, "threshold": 1.2},
            {"lookback": 40.0, "threshold": 0.8},
            {"lookback": 80.0, "threshold": 1.2},
        ]
    return NeighbourhoodDeclaration(
        nominee=nominee, points=tuple(points), coordinates=tuple(coordinates)
    )


# --- brief Step 1, verbatim -------------------------------------------------


def test_valid_declaration_passes():
    _declaration().validate()


def test_all_points_includes_the_nominee_exactly_once():
    declaration = _declaration()
    assert len(declaration.all_points()) == 7
    assert declaration.all_points()[0] == declaration.nominee


def test_too_few_points_is_rejected():
    with pytest.raises(ValueError, match="at least"):
        _declaration(points=[{"lookback": 40.0, "threshold": 1.0}]).validate()


def test_coordinate_without_an_upward_variation_is_rejected():
    points = [
        {"lookback": 40.0, "threshold": 1.0},
        {"lookback": 30.0, "threshold": 1.0},
        {"lookback": 60.0, "threshold": 0.8},
        {"lookback": 60.0, "threshold": 1.2},
        {"lookback": 50.0, "threshold": 0.9},
        {"lookback": 20.0, "threshold": 1.1},
    ]
    with pytest.raises(ValueError, match="lookback"):
        _declaration(points=points).validate()


def test_unknown_coordinate_in_a_point_is_rejected():
    points = [
        {"lookback": 40.0, "threshold": 1.0, "sneaky": 1.0},
        {"lookback": 80.0, "threshold": 1.0},
        {"lookback": 60.0, "threshold": 0.8},
        {"lookback": 60.0, "threshold": 1.2},
        {"lookback": 40.0, "threshold": 0.8},
        {"lookback": 80.0, "threshold": 1.2},
    ]
    with pytest.raises(ValueError, match="sneaky"):
        _declaration(points=points).validate()


def test_median_is_computed_per_metric_independently():
    per_point = [
        {"net_sharpe": 1.0, "max_drawdown": 0.30},
        {"net_sharpe": 2.0, "max_drawdown": 0.20},
        {"net_sharpe": 3.0, "max_drawdown": 0.10},
    ]
    assert median_metrics(per_point) == {"net_sharpe": 2.0, "max_drawdown": 0.20}


def test_median_requires_every_point_to_report_the_same_metrics():
    with pytest.raises(ValueError):
        median_metrics([{"a": 1.0}, {"b": 2.0}])


def test_positive_point_fraction_requires_both_return_and_double_cost_sharpe():
    per_point = [
        {"annualized_return": 0.1, "double_cost_sharpe": 0.6},
        {"annualized_return": 0.1, "double_cost_sharpe": -0.1},
        {"annualized_return": -0.1, "double_cost_sharpe": 0.6},
        {"annualized_return": 0.2, "double_cost_sharpe": 0.9},
    ]
    assert positive_point_fraction(per_point) == 0.5


def test_load_declaration_round_trips(tmp_path):
    declaration = _declaration()
    path = tmp_path / "neighbourhood.json"
    path.write_text(
        json.dumps(
            {
                "nominee": dict(declaration.nominee),
                "points": [dict(point) for point in declaration.points],
                "coordinates": list(declaration.coordinates),
            }
        )
    )
    assert load_declaration(path).nominee == declaration.nominee


# --- additional coverage: every remaining raise path, individually ---------
#
# The task instructions call this out explicitly: every `raise` in this module
# needs its own test, covered one at a time so a broken `or`/`and` can't hide
# behind a neighbour's coverage. The brief's 9 tests above reach 5 of the 9
# `raise` statements (too-few-points, unknown-coordinate, no-upward-variation,
# mismatched-metric-keys, and -- only as a side effect of non-empty fixtures,
# not directly -- the two "requires at least one point" guards). The rest are
# added here, plus boundary/formula pins that isolate exactly what a
# regression would have to break to slip through.


def test_empty_coordinates_is_rejected():
    with pytest.raises(ValueError, match="at least one coordinate"):
        _declaration(coordinates=()).validate()


def test_point_count_floor_is_exactly_seven_at_two_coordinates():
    # One point below the default declaration's 7 (5 neighbourhood + nominee,
    # vs. the default's 6 + nominee). Together with test_valid_declaration_passes
    # (which is exactly at 7), this pins the `<` boundary precisely -- the
    # brief's own too-few-points test uses a single point, nowhere near it.
    points = [
        {"lookback": 40.0, "threshold": 1.0},
        {"lookback": 80.0, "threshold": 1.0},
        {"lookback": 60.0, "threshold": 0.8},
        {"lookback": 60.0, "threshold": 1.2},
        {"lookback": 40.0, "threshold": 0.8},
    ]
    with pytest.raises(ValueError, match="at least 7"):
        _declaration(points=points).validate()


def test_omitted_coordinate_in_a_point_is_rejected():
    points = [
        {"lookback": 40.0},
        {"lookback": 80.0, "threshold": 1.0},
        {"lookback": 60.0, "threshold": 0.8},
        {"lookback": 60.0, "threshold": 1.2},
        {"lookback": 40.0, "threshold": 0.8},
        {"lookback": 80.0, "threshold": 1.2},
    ]
    with pytest.raises(ValueError, match="threshold"):
        _declaration(points=points).validate()


def test_nominee_itself_is_checked_for_missing_coordinates():
    # all_points() puts the nominee first, and the key-coverage loop walks
    # all_points(), not just self.points -- the declared surface includes the
    # nominee. This pins that the nominee is not a silent exception to the
    # "no omitted coordinates" contract.
    with pytest.raises(ValueError, match="threshold"):
        _declaration(nominee={"lookback": 60.0}).validate()


def test_coordinate_without_a_downward_variation_is_rejected():
    # Mirror of the brief's upward-variation test: every neighbourhood value
    # is >= the nominee, so "lookback" has upward evidence but no downward
    # evidence at all.
    points = [
        {"lookback": 90.0, "threshold": 1.0},
        {"lookback": 100.0, "threshold": 1.0},
        {"lookback": 60.0, "threshold": 0.8},
        {"lookback": 60.0, "threshold": 1.2},
        {"lookback": 70.0, "threshold": 0.9},
        {"lookback": 120.0, "threshold": 1.1},
    ]
    with pytest.raises(ValueError, match="no material downward variation"):
        _declaration(points=points).validate()


def _scaled_points(magnitudes):
    return [
        {"a": float(m), "b": float(m), "c": float(m), "d": float(m)}
        for signed in magnitudes
        for m in (signed,)
    ]


def test_minimum_points_scales_with_coordinate_count():
    # 2*4+1 = 9 exceeds the flat floor of 7 -- this declaration has exactly 9
    # points (nominee + 8) and must pass, proving the 2k+1 term actually
    # binds once k is large enough, not just the hardcoded 7.
    nominee = {"a": 0.0, "b": 0.0, "c": 0.0, "d": 0.0}
    points = _scaled_points([1, -1, 2, -2, 3, -3, 4, -4])
    _declaration(nominee=nominee, points=points, coordinates=("a", "b", "c", "d")).validate()


def test_minimum_points_scales_with_coordinate_count_below_floor():
    # One point short of the 9 required for k=4. The flat floor of 7 would
    # wrongly accept this (8 >= 7); only a correct 2*len(coordinates)+1 term
    # catches it -- a test written only at k=2 (where 2k+1=5 < 7 always
    # loses to the flat floor) could never distinguish a broken "2*k" or a
    # missing "+1" from a correct one.
    nominee = {"a": 0.0, "b": 0.0, "c": 0.0, "d": 0.0}
    points = _scaled_points([1, -1, 2, -2, 3, -3, 4])
    with pytest.raises(ValueError, match="at least 9"):
        _declaration(nominee=nominee, points=points, coordinates=("a", "b", "c", "d")).validate()


def test_validate_honours_a_custom_minimum_points_argument():
    # The default declaration has exactly 7 points, which clears the default
    # floor (max(7, 2*2+1)=7) but not a caller-supplied stricter one -- this
    # proves minimum_points is actually threaded into the comparison, not
    # ignored in favour of the hardcoded default.
    with pytest.raises(ValueError, match="at least 9"):
        _declaration().validate(minimum_points=9)


def test_median_metrics_requires_at_least_one_point():
    with pytest.raises(ValueError, match="at least one point"):
        median_metrics([])


def test_positive_point_fraction_requires_at_least_one_point():
    with pytest.raises(ValueError, match="at least one point"):
        positive_point_fraction([])


# --- NaN fail-open regression --------------------------------------------
#
# Context item (b): `x > k` and `x < k` are both False when `x` is NaN. The
# brief's direction check is phrased as "does ANY declared value strictly
# exceed/undercut the nominee" (`any(value > centre ...)` /
# `any(value < centre ...)`), which is already NaN-safe *for this exact
# phrasing*: a NaN can never itself satisfy a strict comparison, so it can
# never manufacture false upward or downward evidence on its own -- real
# evidence is still required from a real value. That safety is a property of
# this specific any-of-strict-comparison formulation, not of "direction
# checks" in general: a superficially equivalent De Morgan rewrite
# (`not all(value <= centre ...)`) would flip an unrelated NaN into a false
# positive, because `NaN <= centre` is *also* False. These tests pin the
# current, correct behaviour so a refactor toward that rewrite is caught.
# Same reasoning for positive_point_fraction: `value > 0.0` is False for
# NaN, so a NaN metric is correctly excluded, not counted as passing.


def test_upward_check_ignores_a_nan_coordinate_value():
    # Every real "lookback" value is below the nominee (60); the one point
    # that could otherwise supply upward evidence is NaN instead of a real
    # number above 60. If NaN were (wrongly) treated as satisfying the
    # upward comparison, this would pass; it must still raise.
    points = [
        {"lookback": 40.0, "threshold": 0.8},
        {"lookback": 45.0, "threshold": 1.2},
        {"lookback": 50.0, "threshold": 0.9},
        {"lookback": 55.0, "threshold": 1.1},
        {"lookback": 58.0, "threshold": 0.85},
        {"lookback": float("nan"), "threshold": 1.15},
    ]
    with pytest.raises(ValueError, match="no material upward variation"):
        _declaration(points=points).validate()


def test_downward_check_ignores_a_nan_coordinate_value():
    # Mirror of the above: every real "lookback" value is above the nominee,
    # and the only point that could supply downward evidence is NaN.
    points = [
        {"lookback": 62.0, "threshold": 0.8},
        {"lookback": 65.0, "threshold": 1.2},
        {"lookback": 70.0, "threshold": 0.9},
        {"lookback": 75.0, "threshold": 1.1},
        {"lookback": 80.0, "threshold": 0.85},
        {"lookback": float("nan"), "threshold": 1.15},
    ]
    with pytest.raises(ValueError, match="no material downward variation"):
        _declaration(points=points).validate()


def test_positive_point_fraction_excludes_nan_annualized_return():
    per_point = [
        {"annualized_return": float("nan"), "double_cost_sharpe": 0.6},
        {"annualized_return": 0.1, "double_cost_sharpe": 0.5},
    ]
    assert positive_point_fraction(per_point) == 0.5


def test_positive_point_fraction_excludes_nan_double_cost_sharpe():
    per_point = [
        {"annualized_return": 0.2, "double_cost_sharpe": float("nan")},
        {"annualized_return": 0.1, "double_cost_sharpe": 0.5},
    ]
    assert positive_point_fraction(per_point) == 0.5


# --- anti-vacuous strength ---------------------------------------------------


def test_median_of_an_even_number_of_points_averages_the_middle_two():
    # The brief's own median test only ever uses 3 (odd) points. statistics
    # .median averages the two middle values for an even-length input; a
    # naive "pick index len//2" or "index (len-1)//2" implementation would
    # return 3.0 or 2.0 here, neither of which is 2.5.
    per_point = [
        {"net_sharpe": 1.0},
        {"net_sharpe": 2.0},
        {"net_sharpe": 3.0},
        {"net_sharpe": 4.0},
    ]
    assert median_metrics(per_point) == {"net_sharpe": 2.5}


def test_median_is_not_dominated_by_a_single_outstanding_point():
    # The whole point of the module (see the module docstring and the task's
    # WHY section): a nominated point is the max of a noisy draw, upward
    # biased by construction. A neighbourhood containing one outstanding
    # value and several ordinary ones must score at the ordinary level, not
    # the outstanding one -- otherwise median scoring buys nothing over just
    # reporting the nominee's own metric.
    per_point = [
        {"net_sharpe": 0.9},
        {"net_sharpe": 1.0},
        {"net_sharpe": 0.95},
        {"net_sharpe": 1.05},
        {"net_sharpe": 5.0},
    ]
    result = median_metrics(per_point)
    assert result["net_sharpe"] == 1.0
    assert result["net_sharpe"] != 5.0


def test_load_declaration_propagates_validation_errors(tmp_path):
    # load_declaration must actually call validate(), not just parse and
    # construct -- a declaration that is well-formed JSON but an invalid
    # neighbourhood (too few points here) must still raise.
    path = tmp_path / "bad_neighbourhood.json"
    path.write_text(
        json.dumps(
            {
                "nominee": {"lookback": 60.0, "threshold": 1.0},
                "points": [{"lookback": 40.0, "threshold": 1.0}],
                "coordinates": ["lookback", "threshold"],
            }
        )
    )
    with pytest.raises(ValueError, match="at least"):
        load_declaration(path)


# --- fix round 1: padding, epsilon "variation", and a bare KeyError --------
#
# Reviewer finding: validate() accepted adversarial neighbourhoods that
# defeat the stated purpose of every one of its existing gates without
# tripping any of them -- padding with duplicate points (including copies of
# the nominee itself) satisfies the point-count floor and, since the
# direction check only asks whether *any* point lies on each side, can leave
# the direction check satisfied too while contributing zero real information
# and pulling the median toward whichever value is repeated. A separate
# finding: the strict above/below check had no materiality floor, so an
# epsilon nudge satisfied "strictly above/below" while exploring nothing.


def test_duplicate_neighbourhood_points_are_rejected():
    # 6 points collapsing to 2 distinct values (3 copies each). Both values
    # individually supply real, material direction -- this fixture is
    # otherwise a fully valid declaration -- so this isolates the
    # distinctness gate specifically, not a side effect of some other check.
    points = [
        {"lookback": 80.0, "threshold": 1.2},
        {"lookback": 80.0, "threshold": 1.2},
        {"lookback": 80.0, "threshold": 1.2},
        {"lookback": 40.0, "threshold": 0.8},
        {"lookback": 40.0, "threshold": 0.8},
        {"lookback": 40.0, "threshold": 0.8},
    ]
    with pytest.raises(ValueError, match="duplicates another declared point"):
        _declaration(points=points).validate()


def test_neighbourhood_points_that_duplicate_the_nominee_are_rejected():
    # 4 of 6 points are literal copies of the nominee -- pads the count floor
    # exactly like the case above, and would silently drag any median toward
    # the nominee's own metric if it were allowed through.
    points = [
        {"lookback": 60.0, "threshold": 1.0},
        {"lookback": 60.0, "threshold": 1.0},
        {"lookback": 60.0, "threshold": 1.0},
        {"lookback": 60.0, "threshold": 1.0},
        {"lookback": 80.0, "threshold": 1.2},
        {"lookback": 40.0, "threshold": 0.8},
    ]
    with pytest.raises(ValueError, match="duplicates the nominee"):
        _declaration(points=points).validate()


def test_distinctness_is_checked_on_the_full_coordinate_vector_not_one_axis():
    # Every "lookback" value here repeats at least once (80, 80, 40, 40) and
    # every "threshold" value repeats at least once (1.2, 1.3, 0.8, 0.7, 0.8,
    # 1.2) -- deliberately, so a distinctness check that (wrongly) compared
    # only one coordinate at a time would find a "duplicate" somewhere here.
    # All 6 points are nonetheless distinct as FULL (lookback, threshold)
    # vectors, so a correct implementation must accept this; this is not the
    # same fixture as test_valid_declaration_passes, which only has this
    # property incidentally rather than by deliberate, exhaustive design.
    points = [
        {"lookback": 80.0, "threshold": 1.2},
        {"lookback": 80.0, "threshold": 1.3},
        {"lookback": 40.0, "threshold": 0.8},
        {"lookback": 40.0, "threshold": 0.7},
        {"lookback": 90.0, "threshold": 0.8},
        {"lookback": 30.0, "threshold": 1.2},
    ]
    _declaration(points=points).validate()


def test_coordinate_with_epsilon_variation_in_one_direction_is_rejected():
    # Material upward (delta=20-40 on a 60-nominee, far above the 3.0 floor)
    # but only an epsilon downward (delta=1e-6) -- the asymmetric case a team
    # would actually try: keep the direction that helps and barely touch the
    # other one to satisfy the letter of "both directions" without really
    # exploring it.
    points = [
        {"lookback": 80.0, "threshold": 1.2},
        {"lookback": 60.0 - 1e-6, "threshold": 0.8},
        {"lookback": 90.0, "threshold": 1.1},
        {"lookback": 70.0, "threshold": 0.9},
        {"lookback": 100.0, "threshold": 1.15},
        {"lookback": 65.0, "threshold": 0.85},
    ]
    with pytest.raises(ValueError, match="no material downward variation"):
        _declaration(points=points).validate()


def test_material_variation_exactly_at_the_five_percent_threshold_is_accepted():
    # The rule is ">=", inclusive. 63.0 is exactly 3.0 above the 60.0
    # nominee, and 0.05 * 60.0 == 3.0 exactly in IEEE-754 double (verified by
    # hand before writing this test -- 60 and 0.05 do not round awkwardly
    # here, unlike some nominee/threshold combinations). It is deliberately
    # the *only* point above the nominee, so if the boundary were exclusive
    # (">") instead of inclusive (">="), this would fail "no material upward
    # variation" and the whole declaration would be rejected.
    points = [
        {"lookback": 63.0, "threshold": 1.3},
        {"lookback": 40.0, "threshold": 0.7},
        {"lookback": 45.0, "threshold": 1.2},
        {"lookback": 50.0, "threshold": 0.8},
        {"lookback": 55.0, "threshold": 1.15},
        {"lookback": 58.0, "threshold": 0.85},
    ]
    _declaration(points=points).validate()


def test_positive_point_fraction_raises_value_error_for_a_point_missing_annualized_return():
    # neighbourhood.py previously subscripted point["annualized_return"]
    # directly, so a missing key raised a bare KeyError -- this module's
    # convention (and the global "fail closed with a clear ValueError")
    # requires ValueError instead. pytest.raises(ValueError) does not catch
    # KeyError, so this test would fail with an uncaught KeyError against the
    # pre-fix implementation.
    per_point = [
        {"annualized_return": 0.1, "double_cost_sharpe": 0.5},
        {"double_cost_sharpe": 0.5},
    ]
    with pytest.raises(ValueError, match="annualized_return"):
        positive_point_fraction(per_point)


def test_positive_point_fraction_raises_value_error_for_a_point_missing_double_cost_sharpe():
    per_point = [
        {"annualized_return": 0.1, "double_cost_sharpe": 0.5},
        {"annualized_return": 0.2},
    ]
    with pytest.raises(ValueError, match="double_cost_sharpe"):
        positive_point_fraction(per_point)
