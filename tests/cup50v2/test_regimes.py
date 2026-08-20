"""Regime labelling and the regime term.

A half-year calendar fold mixes bull, bear and chop, so a lane can be carried through a fold by one
kind of month and still be helpless in another. The tournament exists to find a book that survives
all three, so the score prices the worst *regime*, not only the worst stretch of calendar.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup50v2.config import OOS_END, OOS_START, active_policy
from crypto_trade.cup50v2.regimes import (
    RegimePolicy,
    equal_weight_member_index,
    monthly_regime_labels,
)
from crypto_trade.cup50v2.scoring import score_in_sample_point, score_point, score_window

POLICY = active_policy()


def _panel(monthly_returns: dict[str, float], symbols=("AUSDT", "BUSDT")) -> tuple:
    """Build bars and membership whose equal-weight index delivers the requested monthly returns."""
    rows, roster = [], []
    level = 100.0
    for month, target in monthly_returns.items():
        start = pd.Timestamp(f"{month}-01T00:00:00Z")
        end = start + pd.offsets.MonthBegin(1)
        times = pd.date_range(start, end, freq="8h", inclusive="left", tz="UTC")
        step = (1.0 + target) ** (1.0 / len(times))
        for time in times:
            level *= step
            for symbol in symbols:
                rows.append([time, symbol, level])
        for symbol in symbols:
            roster.append([start, symbol])
    bars = pd.DataFrame(rows, columns=["open_time", "symbol", "close"])
    membership = pd.DataFrame(roster, columns=["reconstitution_time", "symbol"])
    return bars, membership


def test_months_are_labelled_from_the_equal_weight_member_index() -> None:
    bars, membership = _panel({"2024-01": 0.0, "2024-02": 0.25, "2024-03": -0.30, "2024-04": 0.02})
    labels = monthly_regime_labels(bars, membership, policy=POLICY.regimes)
    assert labels == {"2024-02": "bull", "2024-03": "bear", "2024-04": "chop"}


def test_a_partial_first_month_is_dropped() -> None:
    """The split starts mid-March; a part-month return is not comparable with a whole one."""
    bars, membership = _panel({"2024-01": 0.5, "2024-02": 0.0})
    late = bars["open_time"] >= pd.Timestamp("2024-01-20T00:00:00Z")
    labels = monthly_regime_labels(bars[late], membership, policy=POLICY.regimes)
    assert "2024-01" not in labels


def test_only_members_in_force_enter_the_index() -> None:
    bars, membership = _panel({"2024-01": 0.0, "2024-02": 0.20}, symbols=("AUSDT", "BUSDT"))
    doubled = bars.copy()
    outsider = doubled["symbol"] == "BUSDT"
    doubled.loc[outsider, "close"] = doubled.loc[outsider, "close"] * 10.0
    members_only = membership[membership["symbol"] == "AUSDT"]

    index = equal_weight_member_index(doubled, members_only)
    reference = equal_weight_member_index(bars[bars["symbol"] == "AUSDT"], members_only)
    pd.testing.assert_series_equal(index, reference)


def _returns(by_regime: dict[str, float], labels: dict[str, str]) -> pd.DataFrame:
    index = pd.date_range(OOS_START, OOS_END, freq="D", inclusive="left")
    values = [by_regime[labels[day.strftime("%Y-%m")]] for day in index]
    return pd.DataFrame(
        {"net_return": values, "gross_return": values, "gross_exposure": 0.9}, index=index
    )


def _rotating_labels() -> dict[str, str]:
    months = pd.date_range(OOS_START, OOS_END, freq="MS", inclusive="left")
    order = ("bull", "bear", "chop")
    return {month.strftime("%Y-%m"): order[position % 3] for position, month in enumerate(months)}


def test_the_regime_term_prices_the_weakest_market_state() -> None:
    labels = _rotating_labels()
    even = _returns({"bull": 0.0006, "bear": 0.0006, "chop": 0.0006}, labels)
    lopsided = _returns({"bull": 0.0026, "bear": -0.0008, "chop": 0.0006}, labels)

    even_point = score_point({cost: even for cost in (1, 2, 3)}, regime_labels=labels)
    lopsided_point = score_point({cost: lopsided for cost in (1, 2, 3)}, regime_labels=labels)

    # The lopsided book earns more in total, and still scores worse, because one market state
    # carries it and another would have ruined it.
    assert lopsided["net_return"].sum() > even["net_return"].sum()
    assert lopsided_point.regime < even_point.regime
    assert lopsided_point.score < even_point.score
    assert set(even_point.regime_scores) == {"bull", "bear", "chop"}


def test_a_regime_too_thin_to_measure_is_dropped_not_scored() -> None:
    labels = _rotating_labels()
    months = sorted(labels)
    for month in months[1:]:
        labels[month] = "bull" if labels[month] == "chop" else labels[month]
    labels[months[0]] = "chop"  # one month of chop, far below the minimum
    frame = _returns({"bull": 0.0004, "bear": 0.0002, "chop": 0.0004}, labels)

    point = score_point({cost: frame for cost in (1, 2, 3)}, regime_labels=labels)

    assert "chop" not in point.regime_scores
    assert set(point.regime_scores) == {"bull", "bear"}


def test_regime_weights_renormalise_when_a_regime_is_absent() -> None:
    labels = {
        month.strftime("%Y-%m"): ("bull" if position % 2 else "bear")
        for position, month in enumerate(
            pd.date_range(OOS_START, OOS_END, freq="MS", inclusive="left")
        )
    }
    frame = _returns({"bull": 0.0008, "bear": 0.0002, "chop": 0.0}, labels)
    point = score_point({cost: frame for cost in (1, 2, 3)}, regime_labels=labels)

    weights = POLICY.regimes.weights[:2]
    ordered = sorted(point.regime_scores.values())
    expected = sum(w * v for w, v in zip(weights, ordered, strict=True)) / sum(weights)
    assert point.regime == pytest.approx(expected)


def test_the_point_is_the_declared_blend_of_folds_regimes_and_the_whole_path() -> None:
    labels = _rotating_labels()
    frame = _returns({"bull": 0.0009, "bear": -0.0002, "chop": 0.0003}, labels)
    point = score_point({cost: frame for cost in (1, 2, 3)}, regime_labels=labels)
    scoring = POLICY.scoring
    assert point.score == pytest.approx(
        scoring.generalization_weight * point.generalization
        + scoring.regime_weight * point.regime
        + scoring.all_window_weight * point.all_window
    )


def test_the_in_sample_point_uses_its_own_folds_and_window() -> None:
    index = pd.date_range("2021-03-15T00:00:00Z", OOS_START, freq="D", inclusive="left")
    generator = np.random.default_rng(5)
    values = generator.normal(0.0005, 0.004, size=len(index))
    frame = pd.DataFrame(
        {"net_return": values, "gross_return": values, "gross_exposure": 0.9}, index=index
    )
    labels = {
        month.strftime("%Y-%m"): ("bull", "bear", "chop")[position % 3]
        for position, month in enumerate(
            pd.date_range("2021-04-01T00:00:00Z", OOS_START, freq="MS", inclusive="left")
        )
    }
    point = score_in_sample_point({cost: frame for cost in (1, 2, 3)}, regime_labels=labels)
    assert set(point.fold_scores) == {"I1", "I2", "I3", "I4", "I5", "I6"}
    assert 0.0 < point.score <= 100.0

    # The sealed folds see none of this window, so they can only report failure.
    sealed = score_point({cost: frame for cost in (1, 2, 3)}, regime_labels=labels)
    assert sealed.score < point.score


def test_scoring_a_window_rejects_a_fold_weight_of_the_wrong_length() -> None:
    labels = _rotating_labels()
    frame = _returns({"bull": 0.0004, "bear": 0.0004, "chop": 0.0004}, labels)
    with pytest.raises(ValueError):
        score_window(
            {cost: frame for cost in (1, 2, 3)},
            window=(OOS_START, OOS_END),
            folds=tuple(zip(("F1",), (OOS_START,), (OOS_END,))),
            fold_weights=(0.4, 0.6),
            regime_labels=labels,
        )


def test_a_declared_threshold_change_moves_the_labels() -> None:
    bars, membership = _panel({"2024-01": 0.0, "2024-02": 0.12})
    strict = RegimePolicy(
        bull_threshold=0.20, bear_threshold=-0.20, minimum_days=60, weights=(0.5, 0.3, 0.2)
    )
    assert monthly_regime_labels(bars, membership, policy=POLICY.regimes)["2024-02"] == "bull"
    assert monthly_regime_labels(bars, membership, policy=strict)["2024-02"] == "chop"


def test_labels_travel_inside_the_snapshot_and_the_split_censors_the_sealed_side(
    tmp_path,
) -> None:
    """A sealed month's label is a sealed fact, and the two halves cannot disagree."""
    from crypto_trade.cup50v2.snapshot import (
        load_snapshot,
        stitch_snapshots,
        write_split_snapshots,
        write_team_visible_snapshot,
    )

    is_start = pd.Timestamp("2024-01-01T00:00:00Z")
    split = pd.Timestamp("2024-04-01T00:00:00Z")
    end = pd.Timestamp("2024-07-01T00:00:00Z")
    monthly = {
        "2024-01": 0.0,
        "2024-02": 0.30,
        "2024-03": -0.30,
        "2024-04": 0.30,
        "2024-05": -0.30,
        "2024-06": 0.01,
    }
    bars, membership = _panel(monthly, symbols=("AUSDT",))
    bars["close_time"] = bars["open_time"] + pd.Timedelta(hours=8) - pd.Timedelta(milliseconds=1)
    bars["open"] = bars["close"]
    bars["quote_volume"] = 1e9
    membership["liquidity_rank"] = 1
    membership["median_daily_quote_volume"] = 1e9
    funding = pd.DataFrame(
        {
            "funding_time": bars["open_time"],
            "symbol": bars["symbol"],
            "funding_rate": 0.0,
            "mark_price": bars["close"],
        }
    )
    marks = pd.DataFrame(
        {"mark_time": bars["open_time"], "symbol": bars["symbol"], "mark_price": bars["close"]}
    )
    metadata = pd.DataFrame({"symbol": ["AUSDT"], "onboard_date": [is_start]})

    write_split_snapshots(
        bars,
        funding,
        marks,
        membership,
        metadata,
        is_root=tmp_path / "is",
        sealed_root=tmp_path / "sealed",
        is_start=is_start,
        oos_start=split,
        oos_end=end,
    )
    research = load_snapshot(tmp_path / "is")
    sealed = load_snapshot(tmp_path / "sealed")

    assert research.regime_labels == {"2024-02": "bull", "2024-03": "bear"}
    assert sealed.regime_labels == {"2024-04": "bull", "2024-05": "bear", "2024-06": "chop"}
    assert not set(research.regime_labels) & set(sealed.regime_labels)
    assert stitch_snapshots(research, sealed).regime_labels == {
        **research.regime_labels,
        **sealed.regime_labels,
    }

    write_team_visible_snapshot(research, root=tmp_path / "team")
    exported = json.loads((tmp_path / "team" / "manifest.json").read_text())
    assert exported["regime_labels"] == research.regime_labels
    assert not set(exported["regime_labels"]) & set(sealed.regime_labels)
