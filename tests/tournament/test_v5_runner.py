"""The visible/sealed split as a file boundary, not a filter.

The metrics tests prove the *packet* is invariant to sealed returns. These prove the same of the
artifact that actually reaches a team -- the bytes written to the visible reports root -- because
that is the thing a leak would travel through.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament.v5 import gates, metrics, runner, sealed

START = pd.Timestamp("2021-01-04", tz="UTC")
DAYS = 400

THRESHOLDS = gates.GateThresholds(
    minimum_mean_gross_exposure=0.30,
    minimum_median_effective_breadth=6.0,
    minimum_breadth_pass_fraction=0.80,
    minimum_active_bar_fraction=0.80,
    minimum_side_exposure_share=0.20,
    volatility_band=(0.02, 0.40),
    maximum_risk_unit_capped_fraction=0.50,
    minimum_annualised_turnover=4.0,
    maximum_annualised_turnover=90.0,
    minimum_gross_edge_bps_per_turnover=20.0,
    maximum_cost_share_of_positive_gross=0.50,
    minimum_positive_fold_fraction=0.60,
    minimum_deflated_sharpe_probability=0.70,
    maximum_vol_normalised_drawdown=0.25,
    maximum_top_symbol_gross_pnl_share=0.40,
    minimum_deletion_profile_p05_sharpe=0.0,
    minimum_accepted_trials=8,
)


def _returns_frame(seed: int = 5, drift: float = 0.0006) -> pd.DataFrame:
    generator = np.random.default_rng(seed)
    index = pd.date_range(START, periods=DAYS * 3, freq="8h", tz="UTC")
    size = len(index)
    return pd.DataFrame(
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


def _ladder(frame: pd.DataFrame) -> runner.CostLadder:
    """A ladder built from one frame, with each rung independently degraded.

    Real ladders come from three evaluator runs; here the rungs only need to differ so that a test
    can tell which one a statistic came from.
    """

    def degrade(multiple: float) -> _Result:
        scaled = frame.copy()
        scaled["net_return"] = scaled["net_return"] - 0.00002 * (multiple - 1.0)
        return _Result(scaled)

    return runner.CostLadder(base=degrade(1.0), double=degrade(2.0), triple=degrade(3.0))


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


def _development(tmp_path, frame: pd.DataFrame, part: sealed.SealedPartition):
    return runner.run_development_trial(
        _ladder(frame),
        part.visible,
        THRESHOLDS,
        team_id="team-03",
        trial_id="t01",
        reports_root=tmp_path / "is",
        trial_count=12,
        trial_sharpe_dispersion=0.5,
        accepted_trials=12,
        source_review_passed=True,
        invariance_suite_passed=True,
    )


def _sealed(tmp_path, frame: pd.DataFrame, part: sealed.SealedPartition):
    return runner.run_sealed_confirmation(
        _ladder(frame),
        part.sealed,
        THRESHOLDS,
        team_id="team-03",
        candidate_id="c01",
        private_root=tmp_path / "private" / "sealed",
        accepted_trials=12,
        source_review_passed=True,
        invariance_suite_passed=True,
    )


# -- the property the whole edition rests on ----------------------------------------------------


def test_the_published_visible_artifact_does_not_move_when_sealed_returns_move(tmp_path):
    """Perturb only sealed days, then compare the bytes a team would read.

    Asserted on the written file rather than the in-memory packet: the artifact is what a lane
    actually receives, and a leak that only appeared during serialisation would pass a test of the
    object and still reach the team.
    """

    part = _partition()
    frame = _returns_frame()
    baseline = _development(tmp_path / "a", frame, part)

    perturbed = frame.copy()
    sealed_bars = perturbed.index.floor("D").isin(part.sealed)
    perturbed.loc[sealed_bars, "net_return"] += 0.05
    moved = _development(tmp_path / "b", perturbed, part)

    assert baseline.artifact_path.read_bytes() == moved.artifact_path.read_bytes()
    assert baseline.feedback == moved.feedback


def test_the_sealed_artifact_does_move_when_sealed_returns_move(tmp_path):
    """Companion to the test above. Were both blind, the first would prove nothing."""

    part = _partition()
    frame = _returns_frame()
    baseline = _sealed(tmp_path / "a", frame, part)

    perturbed = frame.copy()
    sealed_bars = perturbed.index.floor("D").isin(part.sealed)
    perturbed.loc[sealed_bars, "net_return"] += 0.05
    moved = _sealed(tmp_path / "b", perturbed, part)

    assert baseline.packet.net_sharpe != moved.packet.net_sharpe


def test_overlapping_windows_are_refused_before_anything_is_scored():
    index = pd.date_range(START, periods=30, freq="D", tz="UTC")

    runner.assert_windows_are_disjoint(index[:10], index[20:])
    with pytest.raises(runner.RunnerError, match="overlap"):
        runner.assert_windows_are_disjoint(index[:15], index[10:])


def test_the_real_schedule_produces_disjoint_windows():
    part = _partition()

    runner.assert_windows_are_disjoint(part.visible, part.sealed)


# -- the disclosure boundary --------------------------------------------------------------------


def test_the_team_never_receives_a_field_outside_the_allowlist(tmp_path):
    """An allowlist, so a field added to the packet later is withheld by default."""

    trial = _development(tmp_path, _returns_frame(), _partition())

    assert set(trial.feedback) == set(runner.TEAM_VISIBLE_FIELDS)
    for withheld in ("deflated_sharpe_probability", "deletion_profile_p05_sharpe"):
        assert withheld in trial.packet.as_dict()
        assert withheld not in trial.feedback


def test_a_sealed_artifact_in_the_visible_root_is_detected(tmp_path):
    """Checked by looking. The roots are only disjoint while nobody writes to the wrong one."""

    visible = tmp_path / "is"
    visible.mkdir()
    (visible / "team-03.t01.json").write_text("{}", encoding="utf-8")
    runner.assert_no_sealed_artifact_is_visible(visible)

    (visible / "team-03.c01.sealed.json").write_text("{}", encoding="utf-8")
    with pytest.raises(runner.RunnerError, match="sealed artifacts"):
        runner.assert_no_sealed_artifact_is_visible(visible)


def test_the_two_stages_write_to_different_roots(tmp_path):
    part, frame = _partition(), _returns_frame()

    development = _development(tmp_path, frame, part)
    confirmation = _sealed(tmp_path, frame, part)

    assert development.artifact_path.parent != confirmation.artifact_path.parent
    runner.assert_no_sealed_artifact_is_visible(development.artifact_path.parent)


# -- what each stage is entitled to conclude ----------------------------------------------------


def test_development_enforces_structure_and_only_reports_performance(tmp_path):
    """Twelve feedback-driven trials make a development Sharpe a statement about a search.

    Every floor set in the repository admitted zero of V4-R9's ninety-four measured trials;
    enforcing performance here is how a field ends up empty and a fallback ends up choosing.
    """

    trial = _development(tmp_path, _returns_frame(), _partition())

    assert set(trial.assessment.enforced) & set(gates.DEGENERACY_GATES)
    assert not set(trial.assessment.enforced) & set(gates.PERFORMANCE_GATES)
    assert set(trial.assessment.reported) == set(gates.PERFORMANCE_GATES)


def test_the_sealed_stage_enforces_everything(tmp_path):
    confirmation = _sealed(tmp_path, _returns_frame(), _partition())

    assert set(confirmation.assessment.enforced) >= set(gates.PERFORMANCE_GATES)
    assert confirmation.assessment.reported == ()


def test_the_sealed_stage_carries_a_trial_count_of_one(tmp_path):
    """The search happened on visible data the sealed blocks never saw, so holding them out is
    already the correction. Deflating again by the team's trial count charges it twice, and costs
    more than half the power at a true Sharpe of 1.0.

    Both comparisons hold the **window** fixed and vary only the trial count. Comparing the sealed
    result against the development one would vary the window at the same time, and any difference
    could then be attributed to either -- the same confound that made an earlier universe fixture in
    this build prove nothing about the rule it was written to test.
    """

    part, frame = _partition(), _returns_frame()
    ladder = _ladder(frame)

    def deflation(trial_count: int) -> float:
        packet = metrics.summarize(
            ladder.base,
            part.sealed,
            double_cost_returns=ladder.daily("double"),
            triple_cost_returns=ladder.daily("triple"),
            trial_count=trial_count,
            trial_sharpe_dispersion=0.5,
            breadth_floor=THRESHOLDS.minimum_median_effective_breadth,
        )
        return packet.deflated_sharpe_probability

    assert deflation(1) > deflation(12)
    assert _sealed(tmp_path, frame, part).packet.deflated_sharpe_probability == deflation(1)


def test_a_degenerate_book_is_scored_and_refused_rather_than_raising(tmp_path):
    """A rejection is an outcome that consumes a trial, not an exception that unwinds the run."""

    frame = _returns_frame()
    frame["submitted_effective_breadth"] = 1.05
    frame["submitted_gross_exposure"] = 0.03
    frame["gross_exposure"] = 0.03

    trial = _development(tmp_path, frame, _partition())

    assert not trial.admitted
    assert trial.packet.days > 0
    assert trial.artifact_path.is_file()
    # Named explicitly: "some gate failed" would also pass if an unrelated one broke.
    assert {"effective_breadth", "mean_gross_exposure"} <= set(trial.assessment.failures())


def test_the_published_artifact_records_the_gate_outcome(tmp_path):
    trial = _development(tmp_path, _returns_frame(), _partition())

    payload = json.loads(trial.artifact_path.read_text(encoding="utf-8"))
    assert payload["team_id"] == "team-03"
    assert payload["stage"] == gates.DEVELOPMENT_STAGE
    assert payload["admitted"] is trial.admitted
    assert set(payload["gates"]) == set(gates.ALL_GATES)


def test_the_cost_ladder_keeps_three_independent_rungs():
    """Never one run rescaled: costs interact with the participation cap and with forced exits, so
    a book that survives arithmetically can still die when the costs are really charged."""

    ladder = _ladder(_returns_frame())

    assert not ladder.daily("base").equals(ladder.daily("double"))
    assert not ladder.daily("double").equals(ladder.daily("triple"))
