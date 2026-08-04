from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.config import load_config
from crypto_trade.cup20.risk_unit import common_risk_scalars
from crypto_trade.cup20.runner import (
    CandidateRun,
    decision_grid,
    evaluator_config,
    normalise_unit_gross,
    run_candidate,
)
from crypto_trade.cup20.snapshot import Snapshot
from crypto_trade.tournament.engine_v2 import EvaluatorConfig
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN

CONFIG_PATH = Path("tournament/cup20/config.toml")


class ConstantLong:
    """Hold an equal-weight long book in every eligible symbol."""

    def target_weights(self, context, *, seed):
        if not context.eligible_symbols:
            return {}
        weight = 1.0 / len(context.eligible_symbols)
        return {symbol: weight for symbol in context.eligible_symbols}


class PeekingStrategy:
    """Records how many bar rows it can see at each decision."""

    def __init__(self):
        self.max_close_times = []

    def target_weights(self, context, *, seed):
        latest = max(
            (frame["open_time"].max() for frame in context.bars.values() if len(frame)),
            default=None,
        )
        self.max_close_times.append(latest)
        return None


def _snapshot(days=120, symbols=("AUSDT", "BUSDT", "CUSDT")):
    times = pd.date_range("2021-01-01T00:00:00Z", periods=days * 3, freq="8h")
    rng = np.random.default_rng(5)
    rows = []
    prices: dict[str, np.ndarray] = {}
    for symbol in symbols:
        price = 100.0 * np.cumprod(1.0 + rng.normal(0.0, 0.01, len(times)))
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
    # NOTE: the evaluator's ``_normalise_funding`` requires a ``mark_price`` column (used to price
    # funding cashflows) in addition to ``funding_time``/``symbol``/``funding_rate``. Reuse each
    # symbol's own open price series so funding cashflows are priced consistently with the bars.
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
    return Snapshot(bars, funding, marks, membership, metadata, manifest_sha256="test")


def _finer_cadence_snapshot(periods=200, symbols=("AUSDT", "BUSDT")):
    """Bars every 4h -- finer than the frozen 8h risk-unit ``interval_hours``."""
    times = pd.date_range("2021-01-01T00:00:00Z", periods=periods, freq="4h")
    rng = np.random.default_rng(9)
    rows = []
    prices: dict[str, np.ndarray] = {}
    for symbol in symbols:
        price = 100.0 * np.cumprod(1.0 + rng.normal(0.0, 0.01, len(times)))
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
    return Snapshot(bars, funding, marks, membership, metadata, manifest_sha256="test-4h")


def test_decision_grid_is_eight_hourly_and_half_open():
    grid = decision_grid(pd.Timestamp("2021-01-01T00:00:00Z"), pd.Timestamp("2021-01-02T00:00:00Z"))
    assert grid[0] == pd.Timestamp("2021-01-01T00:00:00Z")
    assert grid[-1] == pd.Timestamp("2021-01-01T16:00:00Z")
    assert len(grid) == 3


def test_decision_grid_is_empty_when_start_does_not_precede_end():
    # Pins the full half-open [start, end) contract at every boundary case, including the
    # degenerate start == end point that fix-round 2 corrected (pd.date_range's own
    # inclusive="left" does not drop that coincident point on its own; see the fix-round-2 report
    # section for the empirical trace on this environment's pandas 3.0.0).
    x = pd.Timestamp("2021-01-01T00:00:00Z")
    assert decision_grid(x, x) == ()
    assert decision_grid(x + pd.Timedelta(hours=8), x) == ()  # start > end: already correct
    assert decision_grid(x, x + pd.Timedelta(hours=8)) == (x,)  # endpoint excluded
    assert decision_grid(x, x + pd.Timedelta(hours=4)) == (x,)  # non-grid-aligned end excludes too


def test_normalise_unit_gross_scales_rows_to_unit_absolute_sum():
    index = pd.date_range("2021-01-01T00:00:00Z", periods=3, freq="8h")
    targets = pd.DataFrame(
        {
            "AUSDT": [2.0, 0.0, -1.0],
            "BUSDT": [-2.0, 0.0, 3.0],
            REBALANCE_INSTRUCTION_COLUMN: [True, True, True],
        },
        index=index,
    )
    result = normalise_unit_gross(targets)
    assert result.loc[index[0], "AUSDT"] == pytest.approx(0.5)
    assert result.loc[index[1]].drop(REBALANCE_INSTRUCTION_COLUMN).abs().sum() == 0.0
    assert result.loc[index[2]].drop(REBALANCE_INSTRUCTION_COLUMN).abs().sum() == pytest.approx(1.0)


def test_run_candidate_produces_all_three_cost_levels():
    snapshot = _snapshot()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    # NOTE: max_symbol_exposure is overridden alongside gross/net for the same reason those two
    # already are here -- see "Fixture-config adaptation" in the task report. Left at its class
    # default (0.10) it would reject ConstantLong's 1/3 per-symbol weight on this 3-symbol
    # fixture outright (a hard raise from the evaluator's _validate_weight_limits, not a scale).
    # It is set to 0.5, not 1.0 == max_gross_exposure: since abs(weight).max() <= abs(weight).sum()
    # always holds, a symbol cap equal to (or above) the gross cap can never independently fire --
    # it would be algebraically inert, not merely loose. 0.5 stays comfortably above 1/3 (this
    # fixture's 3-symbol equal weight) and 1/2 (the 2-symbol _finer_cadence_snapshot fixture used
    # below), while remaining strictly below the 1.0 gross cap so the check stays capable of
    # binding. It is still far above the real production value of 0.20 -- production spreads 20
    # symbols (equal weight ~0.05), this fixture spreads 2-3. This same 0.5 literal is used at
    # every ConstantLong call site in this file for consistency.
    run = run_candidate(
        ConstantLong(),
        snapshot,
        decision_times=grid,
        seed=42,
        config=EvaluatorConfig(
            max_gross_exposure=1.0, max_abs_net_exposure=1.0, max_symbol_exposure=0.5
        ),
        risk_unit={"target_annualized_volatility": 0.10, "lookback_days": 90},
    )
    assert isinstance(run, CandidateRun)
    assert sorted(run.results) == [1, 2, 3]
    for multiplier in (1, 2, 3):
        assert not run.results[multiplier].returns.empty


def test_higher_cost_multiplier_never_improves_net_return():
    snapshot = _snapshot()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    # NOTE: max_symbol_exposure=0.5 -- see test_run_candidate_produces_all_three_cost_levels.
    run = run_candidate(
        ConstantLong(),
        snapshot,
        decision_times=grid,
        seed=42,
        config=EvaluatorConfig(
            max_gross_exposure=1.0, max_abs_net_exposure=1.0, max_symbol_exposure=0.5
        ),
        risk_unit={"target_annualized_volatility": 0.10, "lookback_days": 90},
    )
    totals = {
        multiplier: (1.0 + result.returns["net_return"]).prod()
        for multiplier, result in run.results.items()
    }
    assert totals[1] >= totals[2] >= totals[3]


def test_strategy_never_sees_a_bar_at_or_after_its_decision_time():
    snapshot = _snapshot()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    strategy = PeekingStrategy()
    run_candidate(
        strategy,
        snapshot,
        decision_times=grid,
        seed=1,
        config=EvaluatorConfig(max_gross_exposure=1.0, max_abs_net_exposure=1.0),
        risk_unit={"target_annualized_volatility": 0.10, "lookback_days": 90},
    )
    for decision, latest in zip(grid, strategy.max_close_times):
        if latest is not None:
            # A bar opening at ``latest`` closes at ``latest + 8h`` and may equal the decision.
            assert latest + pd.Timedelta(hours=8) <= decision


# --- Additions beyond the brief's Step 1 tests -----------------------------------------------
#
# The brief's own Step 1 tests do not exercise ``evaluator_config`` at all, and cover only the
# happy path of ``run_candidate``. Two constraints were carried forward from Task 4's review as
# this runner's responsibility -- gross-not-net sourcing of the risk scalar, and the
# ``interval_hours``/``decision_times`` invariants ``common_risk_scalars`` deliberately does not
# check -- plus the frozen ``[execution]``-table wiring and the determinism contract from the
# global constraints. These tests hold the runner to those explicitly-assigned responsibilities.


def test_evaluator_config_builds_from_the_frozen_execution_table():
    loaded = load_config(CONFIG_PATH)
    config = evaluator_config(loaded.raw["execution"])
    assert config.interval_hours == 8
    assert config.initial_equity == 100_000.0
    assert config.taker_fee_bps_per_side == 5.0
    assert config.slippage_bps_per_side == 2.5
    assert config.max_gross_exposure == 1.0
    assert config.max_abs_net_exposure == 1.0
    assert config.max_symbol_exposure == 0.20
    assert config.max_bar_participation == 0.001
    config.validate()  # must not raise

    # The whole reason CUP-20 must build via this function rather than ``EvaluatorConfig()``:
    # the dataclass's own defaults would silently cap directional mandates at quarter-net.
    defaults = EvaluatorConfig()
    assert config.max_abs_net_exposure != defaults.max_abs_net_exposure
    assert config.max_symbol_exposure != defaults.max_symbol_exposure


def test_run_candidate_rejects_duplicate_decision_times():
    snapshot = _snapshot()
    times = list(decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max()))
    times[1] = times[0]
    with pytest.raises(ValueError, match="duplicate"):
        run_candidate(
            ConstantLong(),
            snapshot,
            decision_times=times,
            seed=42,
            config=EvaluatorConfig(max_gross_exposure=1.0, max_abs_net_exposure=1.0),
            risk_unit={"target_annualized_volatility": 0.10, "lookback_days": 90},
        )


def test_run_candidate_rejects_unsorted_decision_times():
    snapshot = _snapshot()
    times = list(decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max()))
    times[0], times[2] = times[2], times[0]
    with pytest.raises(ValueError, match="sorted"):
        run_candidate(
            ConstantLong(),
            snapshot,
            decision_times=times,
            seed=42,
            config=EvaluatorConfig(max_gross_exposure=1.0, max_abs_net_exposure=1.0),
            risk_unit={"target_annualized_volatility": 0.10, "lookback_days": 90},
        )


def test_run_candidate_rejects_empty_decision_times():
    # Reproduces the empty-grid scenario: decision_grid(start, start) is empty. Since fix-round 2,
    # decision_grid honours its documented half-open [start, end) contract at every boundary,
    # including this degenerate start == end point (see
    # test_decision_grid_is_empty_when_start_does_not_precede_end and the fix-round-2 report
    # section), so this is now the simplest construction of an empty grid. Without
    # run_candidate's explicit guard, an empty decision_times would previously pass
    # sortedness/duplicate checks vacuously and blow up several calls later as an opaque
    # KeyError('price_pnl') once run_candidate indexed the unscaled book's columnless return
    # frame -- not a helpful failure for the point where the caller's mistake occurred.
    snapshot = _snapshot()
    start = snapshot.bars["open_time"].min()
    empty_grid = decision_grid(start, start)
    assert empty_grid == ()
    with pytest.raises(ValueError, match="empty"):
        run_candidate(
            ConstantLong(),
            snapshot,
            decision_times=empty_grid,
            seed=42,
            config=EvaluatorConfig(max_gross_exposure=1.0, max_abs_net_exposure=1.0),
            risk_unit={"target_annualized_volatility": 0.10, "lookback_days": 90},
        )


def test_run_candidate_rejects_interval_hours_that_do_not_match_bar_cadence():
    # Decision boundaries every 8h, declared ``interval_hours=8``, but the underlying bars (and
    # therefore the evaluator's actual per-bar return series) are spaced every 4h. Nothing in
    # ``common_risk_scalars`` itself can notice this -- it trusts the ``interval_hours`` it is
    # told -- so the runner must catch it before deriving a silently mis-annualised risk unit.
    snapshot = _finer_cadence_snapshot()
    grid = decision_grid(
        snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max(), interval_hours=8
    )
    with pytest.raises(ValueError, match="cadence"):
        run_candidate(
            ConstantLong(),
            snapshot,
            decision_times=grid,
            seed=42,
            config=EvaluatorConfig(
                interval_hours=8,
                max_gross_exposure=1.0,
                max_abs_net_exposure=1.0,
                # 0.5 -- see test_run_candidate_produces_all_three_cost_levels; this fixture's
                # 2-symbol ConstantLong weight (1/2 = 0.5) is exactly why 0.5, not something
                # tighter, was chosen as the one shared literal.
                max_symbol_exposure=0.5,
            ),
            risk_unit={"target_annualized_volatility": 0.10, "lookback_days": 90},
        )


def test_risk_scalars_are_derived_from_gross_not_net_returns():
    snapshot = _snapshot()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    risk_unit = {"target_annualized_volatility": 0.10, "lookback_days": 90}
    config = EvaluatorConfig(
        max_gross_exposure=1.0, max_abs_net_exposure=1.0, max_symbol_exposure=0.5
    )
    run = run_candidate(
        ConstantLong(),
        snapshot,
        decision_times=grid,
        seed=42,
        config=config,
        risk_unit=risk_unit,
    )
    returns = run.unscaled.returns
    gross = returns["price_pnl"] + returns["funding_pnl"]
    costs = returns["fees"] + returns["slippage"]

    # This fixture must actually incur trading costs, or gross vs. net would be a vacuous
    # distinction: by construction of the evaluator, net_return == gross - fees - slippage.
    assert costs.sum() > 0.0
    pd.testing.assert_series_equal(
        gross - returns["net_return"], costs, check_exact=False, atol=1e-9, check_names=False
    )

    expected_from_gross = common_risk_scalars(
        gross,
        list(run.targets.index),
        target_annualized_volatility=risk_unit["target_annualized_volatility"],
        lookback_days=risk_unit["lookback_days"],
        interval_hours=config.interval_hours,
    )
    pd.testing.assert_series_equal(run.risk_scalars, expected_from_gross)


def test_unscaled_pass_evaluates_the_unscaled_book_separately_from_the_scaled_book():
    snapshot = _snapshot()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    run = run_candidate(
        ConstantLong(),
        snapshot,
        decision_times=grid,
        seed=42,
        config=EvaluatorConfig(
            max_gross_exposure=1.0, max_abs_net_exposure=1.0, max_symbol_exposure=0.5
        ),
        risk_unit={"target_annualized_volatility": 0.10, "lookback_days": 90},
    )
    # Not vacuous: some decisions must actually be rescaled away from 1.0, or the scaled and
    # unscaled books would be indistinguishable by construction of this fixture.
    assert (run.risk_scalars != 1.0).any()
    assert not run.targets.drop(columns=[REBALANCE_INSTRUCTION_COLUMN]).equals(
        run.scaled_targets.drop(columns=[REBALANCE_INSTRUCTION_COLUMN])
    )
    assert not run.unscaled.returns["gross_exposure"].equals(
        run.results[1].returns["gross_exposure"]
    )


def test_run_candidate_is_deterministic():
    snapshot = _snapshot()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    kwargs = dict(
        decision_times=grid,
        seed=42,
        config=EvaluatorConfig(
            max_gross_exposure=1.0, max_abs_net_exposure=1.0, max_symbol_exposure=0.5
        ),
        risk_unit={"target_annualized_volatility": 0.10, "lookback_days": 90},
    )
    first = run_candidate(ConstantLong(), snapshot, **kwargs)
    second = run_candidate(ConstantLong(), snapshot, **kwargs)
    pd.testing.assert_frame_equal(first.targets, second.targets)
    pd.testing.assert_frame_equal(first.scaled_targets, second.scaled_targets)
    pd.testing.assert_series_equal(first.risk_scalars, second.risk_scalars)
    for multiplier in (1, 2, 3):
        pd.testing.assert_frame_equal(
            first.results[multiplier].returns, second.results[multiplier].returns
        )
