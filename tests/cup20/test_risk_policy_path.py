"""The declared-risk-policy path, and the section 4 caps that run after the common risk unit.

Two gaps this file closes.

**``risk_policy`` had never been executed by a test.** It appeared zero times in ``tests/cup20``,
yet it is the path every real candidate takes: a team ships ``risk_policy.json`` alongside
``strategy.py`` (charter section 11), and ``run_candidate`` threads it into both evaluator passes.
So the tests below run a candidate with a non-trivial declared policy end to end and assert on
WHERE the policy actually bit -- which boundaries it braked, which symbols it stopped, which
orders it vetoed, and which book's state it fired off.

**``s_t > 1`` crashed the second pass.** ``evaluate_targets`` does not cap a target row, it
REJECTS one, and nothing between the risk unit and the evaluator applied the section 4 caps that
section 4 says are "Applied after the common risk unit". Any book whose trailing gross volatility
sat under the 10% target therefore raised ``gross exposure ... exceeds cap``. That is the ordinary
case, not an edge: on the low-volatility fixture below the scalar exceeds 1 at 269 of 300
boundaries and pins to its 3.0 ceiling.

**On what these tests pin about section 6.** The charter's step 4 reads "Executed weights = s_t x
unscaled weights", where step 2 defines the unscaled book as the policy-applied one. The code
instead applies ``s_t`` to the pre-policy normalised weights and re-evaluates the policy against
the scaled book. That divergence is NOT closed here, because it cannot be: three of the six
declarable primitives are order-level and have no representation in target-weight space -- see
``test_almost_every_policy_fill_lands_where_there_is_no_target_row_to_carry_it`` and
``test_the_policy_vetoes_orders_which_no_weight_can_express``, which exist precisely to keep that
finding standing as executable evidence rather than prose in a report. What the tests DO pin is
the consequence, so that it can never change silently: a declared brake fires off the executed
book's own drawdown, and on this fixture that means it engages at 91 boundaries instead of 155.
"""

import dataclasses

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.metrics import is_folds
from crypto_trade.cup20.runner import (
    apply_exposure_caps,
    decision_grid,
    normalise_unit_gross,
    run_candidate,
)
from crypto_trade.cup20.scored_metrics import assemble_scored_metrics
from crypto_trade.cup20.snapshot import Snapshot
from crypto_trade.tournament.engine_v2 import EvaluatorConfig
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN
from crypto_trade.tournament.risk_policy import risk_policy_from_dict

SYMBOLS = ("AUSDT", "BUSDT", "CUSDT")
START = pd.Timestamp("2021-01-01T00:00:00Z")
BARS = 300

# max_symbol_exposure=0.50 rather than the production 0.20, for the reason documented at length in
# test_runner.py: this fixture spreads 3 symbols (equal weight 1/3) where production spreads 20
# (~0.05), and at 0.20 the evaluator would reject every row outright. It stays strictly below the
# 1.0 gross cap so the symbol cap remains capable of binding rather than algebraically inert.
CONFIG = EvaluatorConfig(
    interval_hours=8,
    initial_equity=100_000.0,
    taker_fee_bps_per_side=5.0,
    slippage_bps_per_side=2.5,
    max_gross_exposure=1.0,
    max_abs_net_exposure=1.0,
    max_symbol_exposure=0.50,
    max_bar_participation=0.001,
)
# lookback_days=10 rather than the frozen 90 so the scalar starts varying after 30 bars instead of
# 270, which is what makes a 300-bar fixture able to exercise the risk unit at all. The frozen 90
# is pinned separately by test_runner.py's config test; nothing here depends on its value.
RISK_UNIT = {"target_annualized_volatility": 0.10, "lookback_days": 10}


def _snapshot(per_bar_sigma: float, drift: np.ndarray, seed: int) -> tuple[Snapshot, pd.Index]:
    times = pd.date_range(START, periods=BARS, freq="8h")
    rng = np.random.default_rng(seed)
    rows: list[pd.DataFrame] = []
    prices: dict[str, np.ndarray] = {}
    for symbol in SYMBOLS:
        price = 100.0 * np.cumprod(1.0 + drift + rng.normal(0.0, per_bar_sigma, BARS))
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
                    # Deliberately enormous, so the participation cap never binds and every
                    # partial fill below is attributable to the policy's own turnover limit.
                    "quote_volume": 1e10,
                }
            )
        )
    bars = pd.concat(rows, ignore_index=True)
    funding = pd.DataFrame(
        {
            "funding_time": np.tile(times, len(SYMBOLS)),
            "symbol": np.repeat(list(SYMBOLS), BARS),
            "funding_rate": 0.0,
            "mark_price": np.concatenate([prices[symbol] for symbol in SYMBOLS]),
        }
    )
    marks = bars[["open_time", "symbol", "open"]].rename(
        columns={"open_time": "mark_time", "open": "mark_price"}
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": [times[0]] * len(SYMBOLS),
            "symbol": list(SYMBOLS),
            "liquidity_rank": list(range(1, len(SYMBOLS) + 1)),
            "trailing_quote_volume": [1e10] * len(SYMBOLS),
        }
    )
    metadata = pd.DataFrame({"symbol": list(SYMBOLS), "contract_type": "PERPETUAL"})
    return (
        Snapshot(bars, funding, marks, membership, metadata, manifest_sha256="risk-policy-test"),
        times,
    )


_THIRD = BARS // 3
DRAWDOWN_DRIFT = np.concatenate(
    [
        np.full(_THIRD, 0.0010),
        np.full(_THIRD, -0.0035),  # the loss regime the declared brake has to notice
        np.full(BARS - 2 * _THIRD, 0.0010),
    ]
)
FLAT_DRIFT = np.full(BARS, 0.0002)

DRAWDOWN_SNAPSHOT, TIMES = _snapshot(0.012, DRAWDOWN_DRIFT, seed=11)
QUIET_SNAPSHOT, _ = _snapshot(0.0020, FLAT_DRIFT, seed=7)
GRID = decision_grid(TIMES[0], TIMES[-1])


class ConstantLong:
    """Equal-weight long in every eligible symbol, rebalanced at every boundary."""

    def target_weights(self, context, *, seed):
        if not context.eligible_symbols:
            return {}
        weight = 1.0 / len(context.eligible_symbols)
        return {symbol: weight for symbol in context.eligible_symbols}


class SparseLong:
    """Rebalances every sixth boundary and holds in between, like a real weekly-ish mandate.

    Sparseness is the point, not decoration: it is what makes the policy the only thing trading at
    five out of every six boundaries, and therefore what exposes that the policy's actions live in
    quantity space with no target row to carry them.
    """

    def target_weights(self, context, *, seed):
        step = int((context.decision_time - START) / pd.Timedelta(hours=8))
        if step % 6 != 0 or not context.eligible_symbols:
            return None
        weight = 1.0 / len(context.eligible_symbols)
        return {symbol: weight for symbol in context.eligible_symbols}


def _policy(**overrides):
    declaration = {
        "schema_version": 1,
        "policy_id": "declared-brake",
        "same_boundary_reentry": False,
        "volatility_target": {
            "enabled": False,
            "lookback_days": 10,
            "annualized_target": 0.20,
            "minimum_scale": 0.25,
            "maximum_scale": 1.0,
        },
        "drawdown_brakes": [{"drawdown": 0.15, "gross_scale": 0.40}],
        "position_stop": {"enabled": False, "loss_fraction": 0.15, "cooldown_bars": 3},
        "time_stop": {"enabled": False, "maximum_holding_bars": 30, "cooldown_bars": 1},
        "turnover_limit": {"enabled": False, "maximum_one_way_turnover": 1.0},
        "side_scaling": {"long_scale": 1.0, "short_scale": 1.0},
    }
    declaration.update(overrides)
    return risk_policy_from_dict(declaration)


BRAKE_POLICY = _policy()
FULL_POLICY = _policy(
    policy_id="declared-full",
    volatility_target={
        "enabled": True,
        "lookback_days": 5,
        "annualized_target": 0.15,
        "minimum_scale": 0.25,
        "maximum_scale": 1.0,
    },
    drawdown_brakes=[{"drawdown": 0.08, "gross_scale": 0.50}],
    position_stop={"enabled": True, "loss_fraction": 0.10, "cooldown_bars": 4},
    time_stop={"enabled": True, "maximum_holding_bars": 20, "cooldown_bars": 2},
    turnover_limit={"enabled": True, "maximum_one_way_turnover": 0.20},
    side_scaling={"long_scale": 0.90, "short_scale": 1.0},
)


def _run(strategy, snapshot, policy):
    return run_candidate(
        strategy,
        snapshot,
        decision_times=GRID,
        seed=1,
        config=CONFIG,
        risk_unit=RISK_UNIT,
        risk_policy=policy,
    )


# Four shared runs rather than one per test: each is four evaluator passes over 300 bars.
BRAKE_RUN = _run(ConstantLong(), DRAWDOWN_SNAPSHOT, BRAKE_POLICY)
NO_POLICY_RUN = _run(ConstantLong(), DRAWDOWN_SNAPSHOT, None)
QUIET_RUN = _run(ConstantLong(), QUIET_SNAPSHOT, BRAKE_POLICY)
FULL_RUN = _run(SparseLong(), DRAWDOWN_SNAPSHOT, FULL_POLICY)

WEIGHTS = list(SYMBOLS)


def _gross(frame: pd.DataFrame) -> pd.Series:
    return frame[WEIGHTS].abs().sum(axis=1)


def _equity_drawdown(returns: pd.DataFrame) -> float:
    curve = np.concatenate(([CONFIG.initial_equity], returns["equity"].to_numpy(dtype=float)))
    return float(np.max(1.0 - curve / np.maximum.accumulate(curve)))


def _braked(returns: pd.DataFrame) -> pd.Index:
    return returns.index[returns["risk_policy_gross_scale"] < 1.0]


# --- the fixture premises, asserted before anything relies on them ---------------------------


def test_the_fixtures_exercise_the_scalar_in_both_directions():
    """Not vacuous: a fixture whose scalar never leaves 1.0 cannot detect anything below."""
    drawdown_scalars = BRAKE_RUN.risk_scalars
    assert (drawdown_scalars < 1.0).any(), "no boundary where the risk unit shrinks the book"
    assert (drawdown_scalars > 1.0).any(), "no boundary where the risk unit would grow the book"
    quiet_scalars = QUIET_RUN.risk_scalars
    assert (quiet_scalars > 1.0).sum() > BARS // 2, "the quiet book must mostly want to scale UP"
    assert quiet_scalars.max() == pytest.approx(3.0), "the quiet book must reach the 3.0 ceiling"


def test_the_declared_brake_actually_engages_on_this_fixture():
    """Also not vacuous: a policy that never fires would make everything below trivially true."""
    assert len(_braked(BRAKE_RUN.unscaled.returns)) > 0
    assert len(_braked(BRAKE_RUN.results[1].returns)) > 0
    assert _equity_drawdown(BRAKE_RUN.unscaled.returns) > 0.15


# --- section 4 caps, applied after the common risk unit ---------------------------------------


def test_a_low_volatility_book_completes_instead_of_crashing_the_second_pass():
    """The regression. Before the caps were applied this raised ``gross exposure ... exceeds cap``.

    ``s_t = clamp(0.10 / sigma_t, 0.20, 3.0)`` exceeds 1 whenever trailing gross volatility is
    under the target, and ``_validate_weight_limits`` rejects rather than caps, so the run died at
    the first such boundary. Section 6's low-volatility paragraph shows scoring-then-disqualifying
    was always the intent: it concludes such a book "is disqualified rather than rewarded for being
    small" by the 0.06 realised-volatility floor, which requires the run to finish.
    """
    assert sorted(QUIET_RUN.results) == [1, 2, 3]
    for multiplier in (1, 2, 3):
        assert len(QUIET_RUN.results[multiplier].returns) == BARS - 1
    # And the risk unit really did want to lever it up past the cap at those boundaries.
    wanted = QUIET_RUN.risk_scalars * _gross(QUIET_RUN.targets)
    assert (wanted > CONFIG.max_gross_exposure).sum() > BARS // 2


def test_the_executed_weights_respect_every_section_4_cap():
    for run in (BRAKE_RUN, QUIET_RUN, FULL_RUN):
        executed = run.scaled_targets[WEIGHTS]
        assert (executed.abs().sum(axis=1) <= CONFIG.max_gross_exposure + 1e-12).all()
        assert (executed.sum(axis=1).abs() <= CONFIG.max_abs_net_exposure + 1e-12).all()
        assert (executed.abs().max(axis=1) <= CONFIG.max_symbol_exposure + 1e-12).all()


def test_the_cap_reduces_only_and_never_levers_a_small_book_up():
    """Mutation this catches: seeding the scale with ``ceiling / magnitude`` instead of 1.0, which
    would scale an under-exposed row UP to the cap and manufacture leverage the charter forbids."""
    targets = pd.DataFrame(
        {"AUSDT": [0.05, 0.02], "BUSDT": [-0.05, 0.01], REBALANCE_INSTRUCTION_COLUMN: [True, True]},
        index=pd.date_range(START, periods=2, freq="8h"),
    )
    pd.testing.assert_frame_equal(apply_exposure_caps(targets, CONFIG), targets)


@pytest.mark.parametrize(
    ("row", "expected_scale", "which"),
    [
        # gross 1.60, net 0.00, largest 0.80 -> gross binds at 1.0/1.60
        ({"AUSDT": 0.80, "BUSDT": -0.80}, 1.0 / 1.60, "gross"),
        # gross 0.90, net 0.90, largest 0.45 -> nothing binds under a 1.0 net cap...
        ({"AUSDT": 0.45, "BUSDT": 0.45}, 1.0, "none"),
        # gross 0.60, net 0.00, largest 0.30 -> nothing binds
        ({"AUSDT": 0.30, "BUSDT": -0.30}, 1.0, "none-again"),
    ],
)
def test_the_gross_cap_binds_independently(row, expected_scale, which):
    targets = pd.DataFrame(
        {**{k: [v] for k, v in row.items()}, REBALANCE_INSTRUCTION_COLUMN: [True]},
        index=pd.date_range(START, periods=1, freq="8h"),
    )
    capped = apply_exposure_caps(targets, CONFIG)
    for symbol, value in row.items():
        assert capped[symbol].iloc[0] == pytest.approx(value * expected_scale), which


def test_the_net_cap_binds_independently():
    """A row inside the gross and symbol caps but outside the net cap is still scaled.

    Mutation this catches: dropping the ``max_abs_net_exposure`` term from the cap. CUP-20's own
    config sets net == gross == 1.0, where the net term is algebraically inert, so this uses a
    tighter net cap to keep the term testable at all.
    """
    tight = EvaluatorConfig(
        interval_hours=8,
        initial_equity=100_000.0,
        taker_fee_bps_per_side=5.0,
        slippage_bps_per_side=2.5,
        max_gross_exposure=1.0,
        max_abs_net_exposure=0.40,
        max_symbol_exposure=0.50,
        max_bar_participation=0.001,
    )
    targets = pd.DataFrame(
        {"AUSDT": [0.45], "BUSDT": [0.45], REBALANCE_INSTRUCTION_COLUMN: [True]},
        index=pd.date_range(START, periods=1, freq="8h"),
    )
    capped = apply_exposure_caps(targets, tight)
    assert capped[["AUSDT", "BUSDT"]].sum(axis=1).iloc[0] == pytest.approx(0.40)
    assert capped["AUSDT"].iloc[0] == pytest.approx(0.45 * 0.40 / 0.90)


def test_the_symbol_cap_binds_independently():
    """Mutation this catches: dropping the ``max_symbol_exposure`` term. Gross 0.70 and net 0.10
    are both inside their caps here; only the 0.60 single-symbol leg is not."""
    targets = pd.DataFrame(
        {"AUSDT": [0.60], "BUSDT": [-0.10], REBALANCE_INSTRUCTION_COLUMN: [True]},
        index=pd.date_range(START, periods=1, freq="8h"),
    )
    capped = apply_exposure_caps(targets, CONFIG)
    assert capped["AUSDT"].iloc[0] == pytest.approx(CONFIG.max_symbol_exposure)
    assert capped["BUSDT"].iloc[0] == pytest.approx(-0.10 * CONFIG.max_symbol_exposure / 0.60)


def test_the_tightest_of_several_simultaneously_breached_caps_wins():
    """One uniform scale, chosen as the minimum, so satisfying one cap cannot leave another broken.
    Gross 1.40 wants 0.714; the 0.90 leg against a 0.50 symbol cap wants 0.556 -- the latter must
    win, and the result must satisfy both."""
    targets = pd.DataFrame(
        {"AUSDT": [0.90], "BUSDT": [-0.50], REBALANCE_INSTRUCTION_COLUMN: [True]},
        index=pd.date_range(START, periods=1, freq="8h"),
    )
    capped = apply_exposure_caps(targets, CONFIG)
    assert capped["AUSDT"].iloc[0] == pytest.approx(CONFIG.max_symbol_exposure)
    assert capped[["AUSDT", "BUSDT"]].abs().sum(axis=1).iloc[0] <= CONFIG.max_gross_exposure


def test_a_non_finite_weight_raises_rather_than_slipping_through_the_caps():
    """No fail-open on NaN. Mutation this catches: removing the ``np.isfinite`` guard -- ``nan >
    ceiling`` is False, so a NaN row would be declared inside every cap and handed to the
    evaluator, surfacing one pass later as an unattributed non-finite-target error."""
    targets = pd.DataFrame(
        {"AUSDT": [np.nan], "BUSDT": [0.5], REBALANCE_INSTRUCTION_COLUMN: [True]},
        index=pd.date_range(START, periods=1, freq="8h"),
    )
    with pytest.raises(ValueError, match="non-finite"):
        apply_exposure_caps(targets, CONFIG)


def test_an_infinite_weight_raises_too():
    targets = pd.DataFrame(
        {"AUSDT": [np.inf], "BUSDT": [0.5], REBALANCE_INSTRUCTION_COLUMN: [True]},
        index=pd.date_range(START, periods=1, freq="8h"),
    )
    with pytest.raises(ValueError, match="non-finite"):
        apply_exposure_caps(targets, CONFIG)


def test_the_caps_preserve_the_rebalance_instruction_column_and_its_dtype():
    targets = pd.DataFrame(
        {
            "AUSDT": [0.80, 0.10],
            "BUSDT": [-0.80, 0.10],
            REBALANCE_INSTRUCTION_COLUMN: [True, False],
        },
        index=pd.date_range(START, periods=2, freq="8h"),
    )
    capped = apply_exposure_caps(targets, CONFIG)
    assert capped[REBALANCE_INSTRUCTION_COLUMN].dtype == bool
    assert list(capped[REBALANCE_INSTRUCTION_COLUMN]) == [True, False]
    assert list(capped.columns) == list(targets.columns)


def test_a_frame_with_no_weight_columns_is_returned_unchanged():
    targets = pd.DataFrame(
        {REBALANCE_INSTRUCTION_COLUMN: [True]}, index=pd.date_range(START, periods=1, freq="8h")
    )
    pd.testing.assert_frame_equal(apply_exposure_caps(targets, CONFIG), targets)


def test_the_unscaled_reference_book_is_deliberately_not_capped():
    """The asymmetry is the point, not an oversight.

    Section 4 puts the caps "after the common risk unit", so they belong to the executed weights.
    ``s_t`` is the ORGANISER's multiplier and the organiser caps its own output; a team whose own
    normalised weights breach the per-symbol cap has broken the execution contract and still gets
    the evaluator's hard raise rather than a silent trim. Mutation this catches: applying the caps
    to ``targets`` as well, which would convert that contract breach into a quiet rescale -- and
    which this test detects because the run must still RAISE.
    """
    # The premise: the normalised weights this fixture produces really do breach the cap used here.
    normalised = normalise_unit_gross(
        pd.DataFrame(
            {symbol: [1.0] for symbol in SYMBOLS} | {REBALANCE_INSTRUCTION_COLUMN: [True]},
            index=pd.date_range(START, periods=1, freq="8h"),
        )
    )
    too_tight = dataclasses.replace(CONFIG, max_symbol_exposure=0.25)
    assert normalised["AUSDT"].iloc[0] == pytest.approx(1.0 / len(SYMBOLS))
    assert normalised["AUSDT"].iloc[0] > too_tight.max_symbol_exposure

    with pytest.raises(ValueError, match="symbol exposure"):
        run_candidate(
            ConstantLong(),
            DRAWDOWN_SNAPSHOT,
            decision_times=GRID,
            seed=1,
            config=too_tight,
            risk_unit=RISK_UNIT,
            risk_policy=BRAKE_POLICY,
        )


# --- where the declared policy actually bit ----------------------------------------------------


def test_the_policy_is_evaluated_in_both_passes_not_only_the_reference_pass():
    for returns in (BRAKE_RUN.unscaled.returns, *(r.returns for r in BRAKE_RUN.results.values())):
        assert (returns["risk_policy_id"] == "declared-brake").all()
        assert "risk_policy_gross_scale" in returns.columns


def test_the_declared_brake_fires_off_the_book_it_is_evaluated_against():
    """The section 6 divergence, pinned as behaviour.

    The charter's step 4 makes ``s_t`` multiply the POLICY'S OUTPUT, which would leave the brake
    watching the unscaled book. The evaluator instead runs the policy inside each pass, off that
    pass's own equity path -- there is only one equity path per pass, and the drawdown the policy
    reads is that pass's. Asserted directly: the drawdown each pass's policy saw equals the
    drawdown of that pass's own equity curve, and does not equal the other's.
    """
    reference, executed = BRAKE_RUN.unscaled.returns, BRAKE_RUN.results[1].returns
    reference_drawdown = _equity_drawdown(reference)
    executed_drawdown = _equity_drawdown(executed)

    assert reference["risk_policy_drawdown"].max() == pytest.approx(reference_drawdown, abs=1e-9)
    assert executed["risk_policy_drawdown"].max() == pytest.approx(executed_drawdown, abs=1e-9)
    # Two genuinely different books, or the equality above would be uninformative.
    assert reference_drawdown != pytest.approx(executed_drawdown, abs=1e-3)
    assert executed["risk_policy_drawdown"].max() != pytest.approx(reference_drawdown, abs=1e-3)


def test_scaling_before_the_policy_changes_how_often_the_declared_brake_engages():
    """The material consequence: the same declaration brakes a different number of times.

    On this fixture the reference book crosses the declared 0.15 threshold at 155 boundaries and
    the executed book at 91 -- the common risk unit shrank the executed book, so the team's own
    brake had less to react to. Asserted as a strict inequality plus a materiality margin rather
    than as the two literals, so the test states the DIRECTION of the effect rather than pinning
    an arbitrary fixture number.
    """
    reference_brakes = _braked(BRAKE_RUN.unscaled.returns)
    executed_brakes = _braked(BRAKE_RUN.results[1].returns)
    assert len(executed_brakes) < len(reference_brakes)
    assert len(reference_brakes) - len(executed_brakes) > 0.20 * len(reference_brakes)
    # And it starts later, because the executed book takes longer to reach the threshold.
    assert executed_brakes[0] > reference_brakes[0]


def test_the_policy_gross_scale_takes_exactly_the_declared_value_when_it_engages():
    """Not merely "something below 1": the declared 0.40 and nothing else."""
    executed = BRAKE_RUN.results[1].returns
    engaged = executed.loc[_braked(executed), "risk_policy_gross_scale"]
    assert len(engaged) > 0
    assert set(np.round(engaged.to_numpy(dtype=float), 12)) == {0.40}
    assert set(executed["risk_policy_reasons"]) == {"", "drawdown_brake"}


def test_a_brake_that_never_triggers_leaves_the_book_alone():
    """The negative control for the brake itself: a threshold the book never reaches must produce
    a gross scale pinned at 1.0 and no policy fills at all. Mutation this catches: a brake whose
    comparison is inverted, or one that fires unconditionally."""
    quiet = QUIET_RUN.results[1].returns
    assert _equity_drawdown(quiet) < 0.15
    assert (quiet["risk_policy_gross_scale"] == 1.0).all()
    events = QUIET_RUN.results[1].events
    assert not (events["event_type"] == "risk_policy_action").any()


def test_the_policy_is_not_silently_ignored():
    """The proof that every assertion in this file has teeth.

    If ``run_candidate`` dropped ``risk_policy`` on the floor, the evaluator would emit no
    ``risk_policy_*`` columns and no policy events at all -- so this file would fail with a
    ``KeyError`` on nearly every test rather than passing vacuously. Both halves are asserted here:
    the columns exist under a policy and do NOT exist without one, and the two books differ.
    """
    with_policy = BRAKE_RUN.results[1].returns
    without_policy = NO_POLICY_RUN.results[1].returns
    assert "risk_policy_gross_scale" in with_policy.columns
    assert "risk_policy_gross_scale" not in without_policy.columns
    assert "risk_policy_drawdown" not in without_policy.columns

    policy_events = BRAKE_RUN.results[1].events["event_type"]
    plain_events = NO_POLICY_RUN.results[1].events["event_type"]
    assert (policy_events == "risk_policy_action").sum() > 0
    assert (plain_events == "risk_policy_action").sum() == 0

    # And the declaration changed the book, not merely its bookkeeping.
    assert float(with_policy["equity"].iloc[-1]) != pytest.approx(
        float(without_policy["equity"].iloc[-1]), rel=1e-3
    )
    # Materially different, but deliberately NOT asserted as "the brake reduced drawdown":
    # it does not, on this fixture. The brake cuts gross to 0.40 during the loss regime and is
    # still engaged through the recovery, so the braked book climbs back more slowly and ends
    # with the LARGER peak-to-trough (0.189 against 0.144). A test that assumed the comforting
    # direction would have encoded a false belief about what a drawdown brake does.
    assert _equity_drawdown(with_policy) != pytest.approx(
        _equity_drawdown(without_policy), abs=1e-3
    )


def test_the_declared_policy_reaches_the_metric_vector_the_tournament_is_decided_on():
    """End to end: the policy is not just visible in the evaluator's diagnostics, it moves the
    numbers the floors and the ranking read."""
    window = (TIMES[0], TIMES[0] + pd.DateOffset(years=4))
    folds = is_folds(*window)
    with_policy = assemble_scored_metrics(
        BRAKE_RUN, is_start=window[0], is_end=window[1], folds=folds
    )
    without_policy = assemble_scored_metrics(
        NO_POLICY_RUN, is_start=window[0], is_end=window[1], folds=folds
    )
    moved = [key for key in with_policy if with_policy[key] != without_policy[key]]
    assert "max_drawdown" in moved
    assert "net_sharpe" in moved
    assert len(moved) >= 10, moved


# --- the primitives that make section 6's literal step 4 unimplementable ------------------------


def _events(run, event_type):
    events = run.results[1].events
    return events[events["event_type"] == event_type]


def test_every_declared_primitive_fires_end_to_end():
    """A "non-trivial declared policy" has to be shown to be non-trivial. All five gross-scale and
    per-symbol families appear in the reasons the evaluator attributed to real fills."""
    reasons = _events(FULL_RUN, "risk_policy_action")["reason"]
    fired = {part for reason in reasons for part in str(reason).split("+")}
    assert {"drawdown_brake", "volatility_target", "position_stop", "time_stop"} <= fired
    assert len(_events(FULL_RUN, "risk_policy_block")) > 0


def test_the_policy_vetoes_orders_which_no_weight_can_express():
    """A cooldown block zeroes the team's requested DELTA and leaves the carried quantity in place.

    There is no target weight that means "hold this one symbol while retargeting the others" --
    the protocol's rebalance instruction is a row-level Boolean, not a per-symbol one. This is the
    first of the three reasons the post-policy book cannot be replayed as weights.
    """
    blocks = _events(FULL_RUN, "risk_policy_block")
    assert len(blocks) > 0
    assert set(blocks["reason"]) <= {"cooldown", "same_boundary_reentry"}
    # A block is only emitted when the team actually wanted a non-zero position there, so each of
    # these is a real order the policy refused.
    assert blocks["symbol"].isin(SYMBOLS).all()


def test_almost_every_policy_fill_lands_where_there_is_no_target_row_to_carry_it():
    """The second reason. A sparse mandate rebalances at 50 of 299 boundaries; the policy trades at
    far more than that, and those fills are quantity deltas against carried positions with no
    target row to attach a weight to. Reconstructing them as weights would require synthesising an
    explicit rebalance row at every boundary, which turns a sparse book into a dense one and
    changes its turnover, its costs and therefore its result."""
    explicit = set(
        FULL_RUN.scaled_targets.index[
            FULL_RUN.scaled_targets[REBALANCE_INSTRUCTION_COLUMN].astype(bool)
        ]
    )
    assert 0 < len(explicit) < len(FULL_RUN.scaled_targets)
    actions = _events(FULL_RUN, "risk_policy_action")
    off_row = actions[~actions["timestamp"].isin(explicit)]
    assert len(off_row) > 0.75 * len(actions)


def test_the_turnover_limit_partially_fills_rather_than_rescaling_a_weight():
    """The third reason. The limit caps the SUM of order notional at a boundary and prorates what
    is left across the requested orders, so what a symbol ends up holding depends on the distance
    from its current position -- a quantity fact, not a weight."""
    assert float(FULL_RUN.results[1].returns["unfilled_notional"].sum()) > 0.0
    assert float(FULL_RUN.results[1].returns["risk_policy_turnover"].sum()) > 0.0


def test_the_positions_frame_is_not_a_target_and_cannot_stand_in_for_one():
    """Why the obvious reconstruction shortcut does not work either: ``positions`` is recorded
    after execution, after the central exposure-cap pass, and normalised by post-cost equity, so
    it carries price drift the policy never targeted."""
    positions = FULL_RUN.results[1].positions
    gross = positions.abs().sum(axis=1)
    held = gross[gross > 0.0]
    assert len(held) > 0
    # If these were targets they would sit on the small set of levels the policy's gross scales
    # produce; instead they drift continuously.
    assert held.round(6).nunique() > 0.5 * len(held)
