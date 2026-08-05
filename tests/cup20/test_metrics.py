import math

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.metrics import (
    UNDEFINED_CALMAR,
    UNDEFINED_COST_SHARE,
    daily_returns,
    fold_positive_pnl_shares,
    fold_sharpes,
    holdout_folds,
    is_folds,
    max_drawdown,
    window_metrics,
)
from crypto_trade.tournament.engine_v2 import EvaluationResult


def _result(net, *, turnover=0.0, fees=0.0, slippage=0.0, price=None, funding=0.0, events=None):
    index = pd.date_range("2021-01-01T00:00:00Z", periods=len(net), freq="8h", name="timestamp")
    price_series = np.asarray(net, dtype=float) if price is None else np.asarray(price, dtype=float)
    returns = pd.DataFrame(
        {
            "net_return": np.asarray(net, dtype=float),
            "price_pnl": price_series,
            "long_price_pnl": price_series,
            "short_price_pnl": np.zeros(len(net)),
            "funding_pnl": np.full(len(net), funding, dtype=float),
            "long_funding_pnl": np.full(len(net), funding, dtype=float),
            "short_funding_pnl": np.zeros(len(net)),
            "fees": np.full(len(net), fees, dtype=float),
            "slippage": np.full(len(net), slippage, dtype=float),
            "turnover": np.full(len(net), turnover, dtype=float),
        },
        index=index,
    )
    event_frame = (
        pd.DataFrame(events)
        if events is not None
        else pd.DataFrame({"event_type": [], "notional": []})
    )
    return EvaluationResult(returns=returns, positions=pd.DataFrame(), events=event_frame)


def test_daily_returns_compound_within_each_utc_day():
    result = _result([0.01, 0.01, 0.01, -0.02, 0.0, 0.0])
    daily = daily_returns(result)
    assert len(daily) == 2
    assert daily.iloc[0] == pytest.approx(1.01**3 - 1.0)


def test_zero_variance_returns_give_zero_sharpe_not_nan():
    metrics = window_metrics(_result([0.0] * 90))
    assert metrics.net_sharpe == 0.0
    assert math.isfinite(metrics.net_sharpe)


def test_max_drawdown_is_a_positive_magnitude():
    # One move per UTC day: +10%, -20%, +5%. Drawdown is measured on the daily curve.
    bars = [0.10, 0.0, 0.0, -0.20, 0.0, 0.0, 0.05] + [0.0] * 83
    metrics = window_metrics(_result(bars))
    assert metrics.max_drawdown == pytest.approx(0.20)
    assert metrics.max_drawdown > 0.0


def test_calmar_is_zero_when_drawdown_is_zero_and_return_is_not_positive():
    assert window_metrics(_result([0.0] * 90)).calmar == 0.0


def test_gross_edge_per_turnover_is_in_basis_points():
    result = _result([0.001] * 90, turnover=0.01, price=[0.001] * 90)
    metrics = window_metrics(result)
    expected = (0.001 * 90) / (0.01 * 90) * 10_000
    assert metrics.gross_edge_bps_per_turnover == pytest.approx(expected)


def test_cost_share_uses_only_positive_gross_bars():
    result = _result([0.001, -0.002] * 45, fees=0.0001, slippage=0.0, price=[0.001, -0.002] * 45)
    metrics = window_metrics(result)
    positive_gross = 0.001 * 45
    assert metrics.cost_share_of_positive_gross == pytest.approx(0.0001 * 90 / positive_gross)


def test_trade_count_ignores_funding_and_zero_notional_rows():
    events = {
        "event_type": ["trade", "trade", "funding", "risk_reduction"],
        "notional": [100.0, -50.0, 0.0, 25.0],
    }
    metrics = window_metrics(_result([0.0] * 90, events=events))
    assert metrics.trade_count == 3


def test_top5_day_share_is_bounded_and_correct():
    values = [0.0] * 300
    for position in range(5):
        values[position * 3] = 1.0
    metrics = window_metrics(_result(values))
    assert metrics.top5_day_share == pytest.approx(1.0)


def test_is_folds_are_four_blocks_anchored_backward_from_the_cutoff():
    folds = is_folds(pd.Timestamp("2020-08-01T00:00:00Z"), pd.Timestamp("2024-08-01T00:00:00Z"))
    assert [name for name, _, _ in folds] == ["F1", "F2", "F3", "F4"]
    assert folds[0][1] == pd.Timestamp("2020-08-01T00:00:00Z")
    assert folds[0][2] == pd.Timestamp("2021-08-01T00:00:00Z")
    assert folds[-1][2] == pd.Timestamp("2024-08-01T00:00:00Z")


def test_fold_sharpes_and_shares_cover_every_named_fold():
    # Exactly the IS window, so every scored day belongs to exactly one fold and shares sum to 1.
    index = pd.date_range(
        "2020-08-01T00:00:00Z",
        "2024-08-01T00:00:00Z",
        freq="8h",
        inclusive="left",
        name="timestamp",
    )
    rng = np.random.default_rng(2)
    values = rng.normal(0.0002, 0.004, len(index))
    returns = pd.DataFrame(
        {
            "net_return": values,
            "price_pnl": values,
            "long_price_pnl": values,
            "short_price_pnl": np.zeros(len(index)),
            "funding_pnl": np.zeros(len(index)),
            "long_funding_pnl": np.zeros(len(index)),
            "short_funding_pnl": np.zeros(len(index)),
            "fees": np.zeros(len(index)),
            "slippage": np.zeros(len(index)),
            "turnover": np.zeros(len(index)),
        },
        index=index,
    )
    result = EvaluationResult(
        returns, pd.DataFrame(), pd.DataFrame({"event_type": [], "notional": []})
    )
    folds = is_folds(pd.Timestamp("2020-08-01T00:00:00Z"), pd.Timestamp("2024-08-01T00:00:00Z"))
    sharpes = fold_sharpes(result, folds)
    shares = fold_positive_pnl_shares(result, folds)
    assert set(sharpes) == {"F1", "F2", "F3", "F4"}
    assert all(math.isfinite(value) for value in sharpes.values())
    assert sum(shares.values()) == pytest.approx(1.0)


# --- Fix round 1 ---


def test_calmar_uses_a_finite_sentinel_when_drawdown_is_zero_and_return_is_positive():
    # Monotonically positive bars: equity only ever rises, so max_drawdown == 0.0 exactly while
    # annualized_return > 0.0 -- the "undefined, unbounded" branch, not the "flat" branch.
    metrics = window_metrics(_result([0.001] * 90))
    assert metrics.max_drawdown == 0.0
    assert metrics.calmar == UNDEFINED_CALMAR
    assert math.isfinite(metrics.calmar)
    # Task 10's Calmar term is 15 * clamp(calmar / 1.50); anything at or above 1.50 earns full
    # credit, so the sentinel must clear that threshold rather than silently forfeiting it.
    assert metrics.calmar > 1.50


def test_cost_share_uses_a_finite_sentinel_when_there_is_no_positive_gross_pnl():
    # All-flat bars: gross_bar is 0.0 on every row, so positive_gross == 0.0 exactly.
    metrics = window_metrics(_result([0.0] * 90))
    assert metrics.cost_share_of_positive_gross == UNDEFINED_COST_SHARE
    assert math.isfinite(metrics.cost_share_of_positive_gross)
    # max_cost_share_of_positive_gross in tournament/cup20/config.toml's [floors] table is 0.30;
    # the sentinel must land on the failing side so a book with no positive gross disqualifies.
    assert metrics.cost_share_of_positive_gross > 0.30


def test_is_folds_raises_when_the_is_window_cannot_support_four_folds():
    # A 2-year IS window: F1 and F2 would both collapse to zero width, permanently capping
    # positive_fold_count at 2 -- below the >=3 hard floor -- regardless of strategy quality.
    with pytest.raises(ValueError):
        is_folds(pd.Timestamp("2022-08-01T00:00:00Z"), pd.Timestamp("2024-08-01T00:00:00Z"))


def test_holdout_folds_raises_when_the_window_is_shorter_than_eighteen_months():
    # 14 months between start and end: H4 = [start + 18mo, end) would invert (start after end).
    with pytest.raises(ValueError):
        holdout_folds(pd.Timestamp("2024-08-01T00:00:00Z"), pd.Timestamp("2025-10-01T00:00:00Z"))


def test_annualized_return_and_volatility_match_a_known_daily_series():
    # One nonzero bar per UTC day (the other two are 0.0), so each day's compounded return equals
    # that single bar's value exactly: (1+x)*(1+0)*(1+0)-1 == x. The daily series is this list by
    # construction, independent of daily_returns()'s own grouping logic.
    day_returns = [0.05, -0.02, 0.03, 0.01, -0.015, 0.02, 0.04, 0.0, -0.01, 0.025]
    bars: list[float] = []
    for value in day_returns:
        bars.extend([value, 0.0, 0.0])
    metrics = window_metrics(_result(bars))

    values = np.array(day_returns, dtype=float)
    total_growth = float(np.prod(1.0 + values))
    years = len(values) / 365.0
    expected_return = total_growth ** (1.0 / years) - 1.0
    expected_volatility = float(np.std(values, ddof=1)) * math.sqrt(365.0)

    assert metrics.annualized_return == pytest.approx(expected_return)
    assert metrics.annualized_volatility == pytest.approx(expected_volatility)


def test_calmar_non_degenerate_branch_divides_return_by_drawdown():
    # Same bars as test_max_drawdown_is_a_positive_magnitude, whose max_drawdown == 0.20 is
    # asserted there; this test only adds the calmar = annualized_return / drawdown division.
    bars = [0.10, 0.0, 0.0, -0.20, 0.0, 0.0, 0.05] + [0.0] * 83
    metrics = window_metrics(_result(bars))

    total_growth = 1.10 * 0.80 * 1.05
    years = 30.0 / 365.0
    expected_return = total_growth ** (1.0 / years) - 1.0

    assert metrics.max_drawdown == pytest.approx(0.20)
    assert metrics.calmar == pytest.approx(expected_return / 0.20)


def test_annualized_turnover_matches_summed_turnover_over_the_window():
    metrics = window_metrics(_result([0.0] * 90, turnover=0.02))
    expected = (0.02 * 90) / (30.0 / 365.0)
    assert metrics.annualized_turnover == pytest.approx(expected)


def test_long_and_short_gross_pnl_are_independent_role_sums():
    # Distinct, non-mirrored long and short legs -- _result() forces short_price_pnl to zero, so
    # this builds the frame directly to prove the two roles are summed independently.
    index = pd.date_range("2021-01-01T00:00:00Z", periods=6, freq="8h", name="timestamp")
    long_price = np.array([0.01, 0.02, -0.005, 0.0, 0.03, -0.01])
    long_funding = np.full(6, 0.001)
    short_price = np.array([-0.02, 0.01, 0.0, -0.015, 0.02, -0.005])
    short_funding = np.full(6, -0.0005)
    returns = pd.DataFrame(
        {
            "net_return": long_price + short_price + long_funding + short_funding,
            "price_pnl": long_price + short_price,
            "long_price_pnl": long_price,
            "short_price_pnl": short_price,
            "funding_pnl": long_funding + short_funding,
            "long_funding_pnl": long_funding,
            "short_funding_pnl": short_funding,
            "fees": np.zeros(6),
            "slippage": np.zeros(6),
            "turnover": np.zeros(6),
        },
        index=index,
    )
    result = EvaluationResult(
        returns, pd.DataFrame(), pd.DataFrame({"event_type": [], "notional": []})
    )
    metrics = window_metrics(result)

    assert metrics.long_gross_pnl == pytest.approx(float(long_price.sum() + long_funding.sum()))
    assert metrics.short_gross_pnl == pytest.approx(float(short_price.sum() + short_funding.sum()))


# --- Task 10 fix round 1: max_drawdown must not fail open on ruin --------------------------
#
# A -100% day sends compounded equity to exactly zero (0/0 in the peak-to-trough ratio -> NaN,
# plus a RuntimeWarning). Anything worse than -100% sends it negative, where the ratio is
# arithmetically defined but dishonest: a negative running peak can make the formula report a
# SMALLER drawdown than an ordinary, non-ruinous loss -- exactly the fail-open a book that lost
# everything must never receive. `max_drawdown` is public (like `sharpe`, per Task 6's own
# report) and tested directly here, the same way the coordinator's own repro called it.


def test_max_drawdown_reports_the_ceiling_on_exact_total_loss():
    # A single -100% day: compounded equity hits exactly 0.0, so the ratio is 0/0.
    drawdown = max_drawdown(pd.Series([-1.0, 0.0, 0.0]))
    assert drawdown == pytest.approx(1.0)
    assert math.isfinite(drawdown)


def test_max_drawdown_reports_the_ceiling_on_worse_than_total_loss():
    # A -150% day (leveraged ruin beyond total loss): compounded equity goes negative. The bare
    # ratio formula would report 0.0 here (verified against the unpatched function before this
    # fix) -- the single worst possible answer for the single worst possible book.
    drawdown = max_drawdown(pd.Series([-1.5, 0.0, 0.0]))
    assert drawdown == pytest.approx(1.0)
    assert math.isfinite(drawdown)
    assert drawdown != 0.0


def test_window_metrics_stays_finite_through_ruin_end_to_end():
    # Not explicitly requested, but Task 13 serialises WindowMetrics as a whole, not just the
    # bare function -- confirms the fix survives daily_returns()'s compounding and calmar's own
    # division by drawdown, with nothing downstream reintroducing NaN or a RuntimeWarning.
    bars = [0.05, 0.0, 0.0, -1.5, 0.0, 0.0] + [0.0] * 84
    metrics = window_metrics(_result(bars))
    assert metrics.max_drawdown == pytest.approx(1.0)
    assert math.isfinite(metrics.max_drawdown)
    assert math.isfinite(metrics.calmar)


# --- Task 10 fix round 2: max_drawdown must anchor at inception, not the first post-return
# equity value ---------------------------------------------------------------------------------
#
# Without an inception anchor, a drawdown whose peak IS the starting capital (the very first
# return is already negative) is measured against a peak that already reflects that loss,
# understating it. A drawdown whose peak is reached mid-series (the first return is positive, or
# a later point exceeds it) is unaffected either way. All four cases are the coordinator's own
# worked examples, reproduced directly for traceability against their table.

INCEPTION_ANCHOR_CASES = [
    # returns, expected max_drawdown
    ([-0.20, 0.00, 0.00], 0.20),  # single bar: peak is inception itself; pre-fix gave 0.0
    ([-0.30, 0.50, -0.10], 0.30),  # peak is inception; pre-fix gave 0.10 -- a 3x understatement
    ([0.50, -0.40, 0.10], 0.40),  # peak set immediately by the first (positive) return: unaffected
    ([0.20, 0.10, -0.30], 0.30),  # peak set mid-series, after two positive returns: unaffected
]


@pytest.mark.parametrize(("returns", "expected"), INCEPTION_ANCHOR_CASES)
def test_max_drawdown_anchors_at_inception_capital(returns, expected):
    drawdown = max_drawdown(pd.Series(returns))
    assert drawdown == pytest.approx(expected)
    assert math.isfinite(drawdown)


def test_max_drawdown_ruin_cases_still_return_exactly_one_after_the_inception_anchor():
    # Confirms composition with fix round 1 rather than assuming it. The inception anchor keeps
    # the running peak at >= 1.0 for the WHOLE series, so the exact-ruin case (equity hits 0.0)
    # no longer even needs the explicit ruin clamp to avoid NaN -- 1 - 0/1 = 1.0 falls out of the
    # plain ratio now that the peak can never again be non-positive. The worse-than-ruin case
    # (equity goes negative) still needs the explicit clamp: without it, [-1.5, 0.0, 0.0] would
    # compute peaks = [1.0, 1.0, 1.0, 1.0] (the inception peak of 1.0 stays the running max,
    # since -0.5 never exceeds it) and 1 - (-0.5)/1.0 = 1.5 -- an even WORSE fail-open than round
    # 1's pre-fix 0.0, not a safer one. The explicit clamp is doing real, non-redundant work here.
    assert max_drawdown(pd.Series([-1.0, 0.0, 0.0])) == pytest.approx(1.0)  # exact ruin
    assert max_drawdown(pd.Series([-1.5, 0.0, 0.0])) == pytest.approx(1.0)  # worse than ruin


def test_window_metrics_reflects_the_inception_anchored_drawdown_end_to_end():
    # Not explicitly requested, but directly demonstrates the coordinator's own stated stakes: a
    # 20-point hard floor and ranking component, plus calmar's denominator. One nonzero bar per
    # UTC day, so the daily series equals the coordinator's [-0.30, +0.50, -0.10] example exactly,
    # independent of daily_returns()'s own grouping logic.
    bars = [-0.30, 0.0, 0.0, 0.50, 0.0, 0.0, -0.10] + [0.0] * 83
    metrics = window_metrics(_result(bars))
    assert metrics.max_drawdown == pytest.approx(0.30)
    assert math.isfinite(metrics.calmar)
