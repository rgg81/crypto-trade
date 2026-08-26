"""A team's feedback packet must be a function of visible days only.

The evaluator runs the whole development window continuously, because carried positions, funding
and forced exits are path-dependent and cannot be skipped. The split is therefore an operation on
the scoring index, and the failure mode is doing it in one place and forgetting it in another. The
central test here perturbs sealed-block returns arbitrarily and asserts the packet's bytes do not
move.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament.v5 import gates, metrics, sealed

START = pd.Timestamp("2021-01-04", tz="UTC")
DAYS = 400


def _returns_frame(seed: int = 5, drift: float = 0.0006) -> pd.DataFrame:
    generator = np.random.default_rng(seed)
    index = pd.date_range(START, periods=DAYS * 3, freq="8h", tz="UTC")
    size = len(index)
    frame = pd.DataFrame(
        {
            "net_return": generator.normal(drift / 3.0, 0.004, size=size),
            "price_pnl": generator.normal(drift / 3.0, 0.004, size=size),
            "funding_pnl": np.full(size, 1e-6),
            "fees": np.full(size, 2e-5),
            "slippage": np.full(size, 1e-5),
            "turnover": np.full(size, 0.05),
            "gross_exposure": np.full(size, 0.6),
            "long_exposure": np.full(size, 0.3),
            "short_exposure": np.full(size, 0.3),
            "submitted_effective_breadth": np.full(size, 11.0),
            "submitted_gross_exposure": np.full(size, 0.55),
            "risk_unit_binding": np.array(["target"] * size, dtype=object),
        },
        index=index,
    )
    return frame


class _Result:
    def __init__(self, returns: pd.DataFrame, ruined_at=None) -> None:
        self.returns = returns
        self.events = pd.DataFrame(
            {
                "symbol": ["AAAUSDT", "BBBUSDT", "CCCUSDT"],
                "event_type": ["trade", "trade", "trade"],
                "notional": [100.0, 90.0, 80.0],
            }
        )
        self.ruined_at = ruined_at


def _partition() -> sealed.SealedPartition:
    index = pd.date_range(START, periods=DAYS, freq="D", tz="UTC")
    blocks = sealed.sealed_blocks(
        start=START,
        end_exclusive=START + pd.Timedelta(days=DAYS),
        block_days=45,
        stride=7,
        residues=(1, 4),
        interleaved_count=1,
        terminal_block=True,
    )
    return sealed.partition(index, blocks, purge_days=5, embargo_days=10)


def _summarise(result: _Result, index: pd.DatetimeIndex, trial_count: int = 1):
    daily = metrics.daily_returns(result.returns)
    return metrics.summarize(
        result,
        index,
        double_cost_returns=daily * 0.9,
        triple_cost_returns=daily * 0.8,
        trial_count=trial_count,
        trial_sharpe_dispersion=0.5,
    )


# -- the invariant the sealed design rests on --------------------------------------------------


def test_the_team_packet_is_invariant_to_sealed_block_returns() -> None:
    """Perturb only sealed days; the visible packet's bytes must not move."""

    partition = _partition()
    baseline = _returns_frame()
    perturbed = baseline.copy()
    sealed_bars = perturbed.index.floor("D").isin(partition.sealed)
    perturbed.loc[sealed_bars, "net_return"] += 0.05
    perturbed.loc[sealed_bars, "price_pnl"] += 0.05

    first = _summarise(_Result(baseline), partition.visible)
    second = _summarise(_Result(perturbed), partition.visible)
    assert first.canonical_json() == second.canonical_json()


def test_the_sealed_packet_does_move_when_sealed_returns_move() -> None:
    """Mutation: were the sealed summary also blind, the perturbation test would prove nothing."""

    partition = _partition()
    baseline = _returns_frame()
    perturbed = baseline.copy()
    sealed_bars = perturbed.index.floor("D").isin(partition.sealed)
    perturbed.loc[sealed_bars, "net_return"] += 0.05

    first = _summarise(_Result(baseline), partition.sealed)
    second = _summarise(_Result(perturbed), partition.sealed)
    assert first.canonical_json() != second.canonical_json()


def test_the_two_windows_do_not_overlap() -> None:
    partition = _partition()
    visible = _summarise(_Result(_returns_frame()), partition.visible)
    sealed_packet = _summarise(_Result(_returns_frame()), partition.sealed)
    assert visible.days + sealed_packet.days <= DAYS
    assert partition.visible.intersection(partition.sealed).empty


def test_summarising_an_empty_window_is_refused() -> None:
    """'No days' and 'a window of zero length' must not silently produce a packet."""

    with pytest.raises(metrics.MetricsError, match="empty window"):
        _summarise(_Result(_returns_frame()), pd.DatetimeIndex([], tz="UTC"))


def test_a_window_with_no_evaluated_bars_is_refused() -> None:
    far = pd.date_range("2035-01-01", periods=10, freq="D", tz="UTC")
    with pytest.raises(metrics.MetricsError, match="no evaluated bars"):
        _summarise(_Result(_returns_frame()), far)


# -- what the packet measures ------------------------------------------------------------------


def test_bar_returns_are_compounded_into_days() -> None:
    """Every threshold in this edition is stated in daily-annualised terms."""

    frame = _returns_frame()
    daily = metrics.daily_returns(frame)
    assert len(daily) == DAYS
    assert daily.index.freqstr.startswith("D")


def test_exposure_shares_are_measured_on_exposure_not_pnl() -> None:
    """V4-R2 required the long side to have made money, which is a performance test wearing a
    structure test's clothes, and left 27 of 94 trials structurally one-sided."""

    frame = _returns_frame()
    frame["short_exposure"] = 0.0
    packet = _summarise(_Result(frame), _partition().visible)
    assert packet.long_exposure_share == pytest.approx(1.0)
    assert packet.short_exposure_share == pytest.approx(0.0)


def test_a_ruined_run_is_reported_as_ruined() -> None:
    result = _Result(_returns_frame(), ruined_at=START + pd.Timedelta(days=30))
    assert _summarise(result, _partition().visible).ruined is True


def test_evidence_is_built_from_the_packet_rather_than_a_caller() -> None:
    """A caller that could hand-set a statistical field could pass a gate by assertion."""

    packet = _summarise(_Result(_returns_frame()), _partition().visible)
    evidence = metrics.evidence_from_packet(
        packet, accepted_trials=12, source_review_passed=True, invariance_suite_passed=True
    )
    assert evidence.deflated_sharpe_probability == packet.deflated_sharpe_probability
    assert evidence.median_effective_breadth == packet.median_effective_breadth
    assert evidence.realized_annual_volatility == packet.annualised_volatility


def test_every_evidence_field_is_populated_from_somewhere() -> None:
    """The dataclass has no defaults, so a missing field is a TypeError -- this pins that the
    packet actually supplies all of them."""

    packet = _summarise(_Result(_returns_frame()), _partition().visible)
    evidence = metrics.evidence_from_packet(
        packet, accepted_trials=12, source_review_passed=True, invariance_suite_passed=True
    )
    assert isinstance(evidence, gates.SelectionEvidence)


def test_sealed_evidence_carries_a_trial_count_of_one() -> None:
    """The search ran on visible data; holding the blocks out is already the correction."""

    assert metrics.SEALED_TRIALS == 1
    lightly = _summarise(_Result(_returns_frame()), _partition().sealed, trial_count=1)
    heavily = _summarise(_Result(_returns_frame()), _partition().sealed, trial_count=12)
    assert lightly.deflated_sharpe_probability > heavily.deflated_sharpe_probability


# -- disclosure ---------------------------------------------------------------------------------


def test_team_feedback_is_an_allowlist() -> None:
    """Forgetting to allow a field costs a team information; forgetting to deny one costs the
    edition its blindness. The default must fall on the safe side."""

    packet = _summarise(_Result(_returns_frame()), _partition().visible)
    allowed = ["net_sharpe", "annualised_turnover", "median_effective_breadth"]
    feedback = metrics.team_feedback(packet, allowed)
    assert set(feedback) == set(allowed)
    assert "deflated_sharpe_probability" not in feedback


def test_a_feedback_allowlist_naming_an_unknown_field_is_refused() -> None:
    packet = _summarise(_Result(_returns_frame()), _partition().visible)
    with pytest.raises(metrics.MetricsError, match="does not have"):
        metrics.team_feedback(packet, ["a_field_that_was_renamed"])


def test_the_deletion_profile_needs_a_long_enough_series() -> None:
    short = pd.Series(np.zeros(20), index=pd.date_range(START, periods=20, freq="D", tz="UTC"))
    with pytest.raises(metrics.MetricsError, match="too short"):
        metrics.deletion_profile_p05(short)
