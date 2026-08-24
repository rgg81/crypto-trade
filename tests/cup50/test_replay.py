from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup50.availability import UnavailabilityWindow
from crypto_trade.cup50.replay import (
    REBALANCE_COLUMN,
    ExecutionConfig,
    _evaluate_targets_reference,
    _prepare_execution,
    apply_strategy_parameters,
    evaluate_targets,
    generate_targets,
    require_execution_coverage,
    run_candidate,
    scored_returns,
)
from crypto_trade.cup50.snapshot import Snapshot


class RecordingStrategy:
    def __init__(self) -> None:
        self.contexts = []

    def target_weights(self, context, *, seed):
        self.contexts.append(context)
        return {"AUSDT": 0.2} if len(self.contexts) == 1 else None


class NoInputStrategy(RecordingStrategy):
    uses_bars = False
    uses_funding = False

    def target_weights(self, context, *, seed):
        self.contexts.append(context)
        return {}


def _snapshot() -> Snapshot:
    first = pd.Timestamp("2024-01-01T00:00:00Z")
    bars = pd.DataFrame(
        [
            [
                first - pd.Timedelta(hours=8),
                first - pd.Timedelta(milliseconds=1),
                "AUSDT",
                99,
                100,
                1e9,
            ],
            [
                first,
                first + pd.Timedelta(hours=8) - pd.Timedelta(milliseconds=1),
                "AUSDT",
                100,
                101,
                1e9,
            ],
            [
                first + pd.Timedelta(hours=8),
                first + pd.Timedelta(hours=16) - pd.Timedelta(milliseconds=1),
                "AUSDT",
                101,
                102,
                1e9,
            ],
        ],
        columns=["open_time", "close_time", "symbol", "open", "close", "quote_volume"],
    )
    funding = pd.DataFrame(
        [
            [first, "AUSDT", 0.01, 100.0],
            [first + pd.Timedelta(hours=8), "AUSDT", 0.01, 101.0],
            [first + pd.Timedelta(hours=16), "AUSDT", 0.01, 102.0],
        ],
        columns=["funding_time", "symbol", "funding_rate", "mark_price"],
    )
    marks = pd.DataFrame(
        [
            [first, "AUSDT", 100.0],
            [first + pd.Timedelta(hours=8), "AUSDT", 101.0],
            [first + pd.Timedelta(hours=16), "AUSDT", 102.0],
        ],
        columns=["mark_time", "symbol", "mark_price"],
    )
    membership = pd.DataFrame(
        [[first, "AUSDT", 1, 1000.0]],
        columns=[
            "reconstitution_time",
            "symbol",
            "liquidity_rank",
            "median_daily_quote_volume",
        ],
    )
    return Snapshot(
        bars,
        funding,
        marks,
        membership,
        pd.DataFrame({"symbol": ["AUSDT"]}),
        "x" * 64,
        first,
        first + pd.Timedelta(hours=16),
        True,
    )


def test_context_is_strict_and_hides_transaction_open() -> None:
    snapshot = _snapshot()
    strategy = RecordingStrategy()
    times = pd.date_range(snapshot.window_start, snapshot.window_end, freq="8h", inclusive="left")
    generate_targets(
        strategy,
        bars=snapshot.bars,
        funding=snapshot.funding,
        auxiliary={},
        membership=snapshot.membership,
        decision_times=times,
        seed=1,
    )
    first = strategy.contexts[0]
    assert (first.bars["AUSDT"]["close_time"] < first.decision_time).all()
    assert "open" not in first.bars["AUSDT"]
    assert first.funding.empty  # settlement at t is not strategy-visible
    assert "mark_price" not in strategy.contexts[1].funding


def test_context_is_limited_to_trailing_180_complete_days() -> None:
    snapshot = _snapshot()
    decision = snapshot.window_start
    old_open = decision - pd.Timedelta(days=181)
    old = snapshot.bars.iloc[[0]].copy()
    old["open_time"] = old_open
    old["close_time"] = old_open + pd.Timedelta(hours=8) - pd.Timedelta(milliseconds=1)
    snapshot = dataclasses.replace(
        snapshot, bars=pd.concat([old, snapshot.bars], ignore_index=True)
    )
    strategy = RecordingStrategy()

    generate_targets(
        strategy,
        bars=snapshot.bars,
        funding=snapshot.funding,
        auxiliary={},
        membership=snapshot.membership,
        decision_times=[decision],
        seed=1,
    )

    visible = strategy.contexts[0].bars["AUSDT"]
    assert (visible["close_time"] >= decision - pd.Timedelta(days=180)).all()


def test_mechanism_inapplicable_inputs_can_be_declared_empty() -> None:
    snapshot = _snapshot()
    strategy = NoInputStrategy()
    generate_targets(
        strategy,
        bars=snapshot.bars,
        funding=snapshot.funding,
        auxiliary={},
        membership=snapshot.membership,
        decision_times=[snapshot.window_start],
        seed=1,
    )
    assert strategy.contexts[0].bars == {}
    assert strategy.contexts[0].funding.empty


def test_right_closed_funding_and_continuous_state() -> None:
    snapshot = _snapshot()
    strategy = RecordingStrategy()
    replay = run_candidate(
        strategy,
        snapshot=snapshot,
        start=snapshot.window_start,
        end=snapshot.window_end,
        seed=1,
        terminal=False,
    )
    result = replay.costs[1]
    # Funding at the left boundary is excluded; the right-boundary settlement is included.
    assert result.returns.iloc[0]["funding_return"] < 0
    assert result.final_state.quantities["AUSDT"] > 0
    assert len(result.returns) == 2
    holdout_start = snapshot.window_start + pd.Timedelta(hours=8)
    holdout = scored_returns(result, holdout_start, snapshot.window_end)
    assert list(holdout.index) == [holdout_start]
    # The settlement exactly at holdout_start was charged to the preceding row, never this one.
    assert result.returns.iloc[0]["right_boundary"] == holdout_start


def test_subsecond_funding_jitter_is_attributed_to_canonical_right_boundary() -> None:
    snapshot = _snapshot()
    boundary = snapshot.window_start + pd.Timedelta(hours=8)
    snapshot.funding.loc[1, "funding_time"] = boundary + pd.Timedelta(milliseconds=12)
    snapshot.funding["settlement_time"] = pd.to_datetime(
        snapshot.funding["funding_time"], utc=True
    ).dt.floor("h")
    replay = run_candidate(
        RecordingStrategy(),
        snapshot=snapshot,
        start=snapshot.window_start,
        end=snapshot.window_end,
        seed=1,
    )
    assert replay.costs[1].returns.iloc[0]["funding_return"] < 0


def test_audited_midweek_unavailability_settles_at_preceding_close() -> None:
    snapshot = _snapshot()
    boundary = snapshot.window_start + pd.Timedelta(hours=8)
    extra_bars = snapshot.bars.copy()
    extra_bars["symbol"] = "BUSDT"
    extra_marks = snapshot.mark_prices.copy()
    extra_marks["symbol"] = "BUSDT"
    snapshot = dataclasses.replace(
        snapshot,
        bars=pd.concat([snapshot.bars, extra_bars], ignore_index=True),
        mark_prices=pd.concat([snapshot.mark_prices, extra_marks], ignore_index=True),
    )
    audit = (
        UnavailabilityWindow(
            symbol="AUSDT",
            start=boundary,
            end=snapshot.window_end,
            reason="checksum-verified test cessation",
            settlement_price=101.0,
        ),
    )
    # A zero-trade placeholder does not make the contract executable. The terminal mark remains
    # available after the contract returns, so terminal semantic coverage is still independently
    # testable.
    snapshot.bars.loc[snapshot.bars["open_time"] == boundary, "quote_volume"] = 0.0
    snapshot.mark_prices.drop(
        snapshot.mark_prices.index[snapshot.mark_prices["mark_time"] == boundary], inplace=True
    )
    decisions = pd.date_range(
        snapshot.window_start, snapshot.window_end, freq="8h", inclusive="left"
    )
    require_execution_coverage(snapshot, decisions, unavailability=audit)
    strategy = RecordingStrategy()
    replay = run_candidate(
        strategy,
        snapshot=snapshot,
        start=snapshot.window_start,
        end=snapshot.window_end,
        unavailability=audit,
    )
    result = replay.costs[1]
    settlement = result.events.loc[
        result.events["event_type"] == "unavailability_settlement"
    ]
    assert len(settlement) == 1
    settlement = settlement.iloc[0]
    assert settlement["timestamp"] == boundary
    assert settlement["notional"] < 0
    assert result.events["notional"].notna().all()
    assert result.final_state.quantities == {}
    assert result.returns.iloc[0]["turnover"] > result.returns.iloc[1]["turnover"]
    assert strategy.contexts[1].eligible_symbols == ()


def test_unaudited_missing_transaction_bar_still_fails_readiness() -> None:
    snapshot = _snapshot()
    boundary = snapshot.window_start + pd.Timedelta(hours=8)
    snapshot.bars.drop(snapshot.bars.index[snapshot.bars["open_time"] == boundary], inplace=True)
    decisions = pd.date_range(
        snapshot.window_start, snapshot.window_end, freq="8h", inclusive="left"
    )
    with pytest.raises(ValueError, match="execution coverage failure"):
        require_execution_coverage(snapshot, decisions)


def test_future_value_corruption_is_inert_at_a_frozen_replay_cutoff() -> None:
    clean = _snapshot()
    future = clean.window_end + pd.Timedelta(hours=8)
    corrupted = Snapshot(
        pd.concat(
            [
                clean.bars,
                pd.DataFrame(
                    [[future, future + pd.Timedelta(hours=8), "AUSDT", np.nan, np.nan, np.nan]],
                    columns=clean.bars.columns,
                ),
            ],
            ignore_index=True,
        ),
        pd.concat(
            [
                clean.funding,
                pd.DataFrame([[future, "AUSDT", np.nan, np.nan]], columns=clean.funding.columns),
            ],
            ignore_index=True,
        ),
        pd.concat(
            [
                clean.mark_prices,
                pd.DataFrame([[future, "AUSDT", np.nan]], columns=clean.mark_prices.columns),
            ],
            ignore_index=True,
        ),
        clean.membership,
        clean.contract_metadata,
        clean.manifest_sha256,
        clean.window_start,
        clean.window_end,
        clean.sealed,
    )
    expected = run_candidate(
        RecordingStrategy(), snapshot=clean, start=clean.window_start, end=clean.window_end
    )
    observed = run_candidate(
        RecordingStrategy(), snapshot=corrupted, start=clean.window_start, end=clean.window_end
    )
    for cost in (1, 2, 3):
        pd.testing.assert_frame_equal(
            expected.costs[cost].returns, observed.costs[cost].returns, check_exact=True
        )


def test_post_launch_member_cannot_change_pre_activation_reduction_width() -> None:
    baseline = _snapshot()
    first = baseline.window_start
    activation = first + pd.Timedelta(hours=8)
    append_start = first + pd.Timedelta(hours=1)
    new_symbol = "0NEWUSDT"
    new_bars = baseline.bars.copy()
    new_bars["symbol"] = new_symbol
    new_marks = baseline.mark_prices.copy()
    new_marks["symbol"] = new_symbol
    appended = dataclasses.replace(
        baseline,
        bars=pd.concat([baseline.bars, new_bars], ignore_index=True),
        mark_prices=pd.concat([baseline.mark_prices, new_marks], ignore_index=True),
        membership=pd.concat(
            [
                baseline.membership,
                pd.DataFrame(
                    [[activation, new_symbol, 1, 2000.0]],
                    columns=baseline.membership.columns,
                ),
            ],
            ignore_index=True,
        ),
    )
    decisions = pd.date_range(first, baseline.window_end, freq="8h", inclusive="left")
    targets = pd.DataFrame(
        {
            new_symbol: [0.0, 0.1],
            "AUSDT": [0.2, 0.1],
            REBALANCE_COLUMN: [True, True],
        },
        index=decisions,
    )

    prepared = _prepare_execution(
        targets,
        snapshot=appended,
        config=ExecutionConfig(),
        unavailability=(),
        append_invariant_start=append_start,
    )
    new_position = prepared.symbol_positions[new_symbol]
    old_position = prepared.symbol_positions["AUSDT"]

    assert prepared.reduction_active[:, new_position].tolist() == [False, True]
    assert prepared.reduction_active[:, old_position].tolist() == [True, True]
    result = evaluate_targets(
        targets,
        snapshot=appended,
        cost_multiplier=1.0,
        append_invariant_start=append_start,
    )
    assert new_symbol not in result.events.loc[
        result.events["timestamp"] < activation, "symbol"
    ].tolist()
    assert new_symbol in result.events.loc[
        result.events["timestamp"] == activation, "symbol"
    ].tolist()


def test_nonterminal_split_and_stitched_execution_are_bit_exact() -> None:
    snapshot = _snapshot()
    decisions = pd.date_range(
        snapshot.window_start, snapshot.window_end, freq="8h", inclusive="left"
    )
    targets = generate_targets(
        RecordingStrategy(),
        bars=snapshot.bars,
        funding=snapshot.funding,
        auxiliary={},
        membership=snapshot.membership,
        decision_times=decisions,
        seed=1,
    )
    monolithic = evaluate_targets(targets, snapshot=snapshot, cost_multiplier=1.0)
    left = evaluate_targets(targets.iloc[:1], snapshot=snapshot, cost_multiplier=1.0)
    right = evaluate_targets(
        targets.iloc[1:],
        snapshot=snapshot,
        cost_multiplier=1.0,
        initial_state=left.final_state,
    )

    pd.testing.assert_frame_equal(
        monolithic.returns,
        pd.concat([left.returns, right.returns]),
        check_exact=True,
    )
    pd.testing.assert_frame_equal(
        monolithic.events.reset_index(drop=True),
        pd.concat([left.events, right.events], ignore_index=True),
        check_exact=True,
    )
    assert monolithic.final_state == right.final_state


def test_array_executor_is_bit_exact_to_frozen_reference_and_can_suppress_events() -> None:
    snapshot = _snapshot()
    decisions = pd.date_range(
        snapshot.window_start, snapshot.window_end, freq="8h", inclusive="left"
    )
    targets = generate_targets(
        RecordingStrategy(),
        bars=snapshot.bars,
        funding=snapshot.funding,
        auxiliary={},
        membership=snapshot.membership,
        decision_times=decisions,
        seed=1,
    )
    for cost in (0.0, 1.0, 2.0, 3.0):
        reference = _evaluate_targets_reference(
            targets, snapshot=snapshot, cost_multiplier=cost
        )
        observed = evaluate_targets(targets, snapshot=snapshot, cost_multiplier=cost)
        pd.testing.assert_frame_equal(observed.returns, reference.returns, check_exact=True)
        pd.testing.assert_frame_equal(observed.events, reference.events, check_exact=True)
        assert observed.final_state == reference.final_state

        suppressed = evaluate_targets(
            targets, snapshot=snapshot, cost_multiplier=cost, record_events=False
        )
        pd.testing.assert_frame_equal(suppressed.returns, reference.returns, check_exact=True)
        assert suppressed.events.empty
        assert suppressed.final_state == reference.final_state


def test_participation_limited_deleveraging_is_not_a_candidate_failure() -> None:
    snapshot = _snapshot()
    snapshot.funding.loc[1, "funding_rate"] = 0.75
    snapshot.bars.loc[snapshot.bars["open_time"] == snapshot.window_start, "quote_volume"] = 1e9
    snapshot.bars.loc[
        snapshot.bars["open_time"] == snapshot.window_start + pd.Timedelta(hours=8),
        "quote_volume",
    ] = 0.0
    decisions = pd.date_range(
        snapshot.window_start, snapshot.window_end, freq="8h", inclusive="left"
    )
    targets = pd.DataFrame(
        {
            "AUSDT": [1.0, np.nan],
            REBALANCE_COLUMN: [True, False],
        },
        index=decisions,
    )
    result = evaluate_targets(targets, snapshot=snapshot, cost_multiplier=0.0)

    # The second boundary has no executable capacity. The target cap remains binding on requests,
    # while an organizer-owned, participation-limited carried position is allowed to work down on
    # later boundaries instead of incorrectly disqualifying the strategy.
    assert result.returns.iloc[1]["gross_exposure"] > 0.20
    assert result.returns.iloc[1]["turnover"] == 0.0


def test_carried_post_exit_position_settles_at_last_verified_close() -> None:
    snapshot = _snapshot()
    first = snapshot.window_start
    third = first + pd.Timedelta(hours=16)
    b_rows = []
    for offset, symbol, open_price, close_price, volume in (
        (0, "BUSDT", 10.0, 10.0, 1e9),
        (8, "BUSDT", 10.0, 10.0, 1e9),
        (16, "BUSDT", 10.0, 10.0, 1e9),
    ):
        opened = first + pd.Timedelta(hours=offset)
        b_rows.append(
            [
                opened,
                opened + pd.Timedelta(hours=8) - pd.Timedelta(milliseconds=1),
                symbol,
                open_price,
                close_price,
                volume,
            ]
        )
    bars = pd.concat(
        [
            snapshot.bars,
            pd.DataFrame(b_rows, columns=snapshot.bars.columns),
        ],
        ignore_index=True,
    )
    # A remains tradable for one boundary after leaving the roster, but there is no capacity to
    # complete the organizer-owned liquidation before its final archived transaction bar.
    bars.loc[
        bars["symbol"].eq("AUSDT") & bars["open_time"].eq(first + pd.Timedelta(hours=8)),
        "quote_volume",
    ] = 1.0
    placeholder = snapshot.bars.loc[
        snapshot.bars["symbol"].eq("AUSDT")
        & snapshot.bars["open_time"].eq(first + pd.Timedelta(hours=8))
    ].copy()
    placeholder["open_time"] = third
    placeholder["close_time"] = third + pd.Timedelta(hours=8) - pd.Timedelta(milliseconds=1)
    placeholder["open"] = placeholder["close"]
    placeholder["quote_volume"] = 0.0
    bars = pd.concat([bars, placeholder], ignore_index=True)
    marks = pd.concat(
        [
            snapshot.mark_prices,
            pd.DataFrame(
                [[first, "BUSDT", 10.0], [first + pd.Timedelta(hours=8), "BUSDT", 10.0]],
                columns=snapshot.mark_prices.columns,
            ),
        ],
        ignore_index=True,
    )
    membership = pd.DataFrame(
        [
            [first, "AUSDT", 1, 1000.0],
            [first, "BUSDT", 2, 900.0],
            [first + pd.Timedelta(hours=8), "BUSDT", 1, 900.0],
        ],
        columns=snapshot.membership.columns,
    )
    carried = dataclasses.replace(
        snapshot,
        bars=bars,
        mark_prices=marks,
        membership=membership,
        window_end=third,
    )
    decisions = pd.date_range(first, third, freq="8h", inclusive="left")
    targets = pd.DataFrame(
        {
            "AUSDT": [0.2, np.nan],
            "BUSDT": [0.0, np.nan],
            REBALANCE_COLUMN: [True, False],
        },
        index=decisions,
    )

    reference = _evaluate_targets_reference(targets, snapshot=carried, cost_multiplier=1.0)
    observed = evaluate_targets(targets, snapshot=carried, cost_multiplier=1.0)

    pd.testing.assert_frame_equal(observed.returns, reference.returns, check_exact=True)
    pd.testing.assert_frame_equal(observed.events, reference.events, check_exact=True)
    assert observed.final_state.quantities == {}
    settlement = observed.events.loc[
        observed.events["event_type"].eq("unavailability_settlement")
    ]
    assert settlement["symbol"].tolist() == ["AUSDT"]
    assert settlement["timestamp"].tolist() == [third]


def test_full_flat_target_path_has_exact_zero_execution_result() -> None:
    snapshot = _snapshot()
    strategy = NoInputStrategy()
    replay = run_candidate(
        strategy,
        snapshot=snapshot,
        start=snapshot.window_start,
        end=snapshot.window_end,
    )
    for result in replay.costs.values():
        assert len(result.returns) == 2
        assert (result.returns["net_return"] == 0.0).all()
        assert result.final_state.quantities == {}


def test_strategy_parameters_preserve_integer_dimensions_and_reject_unknowns() -> None:
    strategy = RecordingStrategy()
    strategy.lookback = 10
    apply_strategy_parameters(strategy, {"lookback": 12.0})
    assert strategy.lookback == 12
    assert isinstance(strategy.lookback, int)
    with pytest.raises(ValueError, match="not a strategy attribute"):
        apply_strategy_parameters(strategy, {"missing": 1})
    with pytest.raises(ValueError, match="fractional"):
        apply_strategy_parameters(strategy, {"lookback": 12.5})
