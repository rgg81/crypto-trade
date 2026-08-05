"""A scored vector must be able to say which stage produced it, and the adjudicators must check.

The defect this file exists to close: ``adjudicate_holdout_candidate`` could not verify its own
window or its own folds. A caller that assembled the IN-SAMPLE window with the IN-SAMPLE folds --
an internally consistent, perfectly well-formed vector -- and handed it to the holdout adjudicator
would have section 8's five eligibility conditions and the ranking score ``G`` evaluated over four
years of research data. Every value finite, every key present, no exception anywhere, and a wrong
verdict published as the tournament's result.

The tiling check in ``assemble_scored_metrics`` cannot see this. It catches holdout folds against
the in-sample window (they do not tile it), which is the *other* half of the mistake; the half
above tiles perfectly. So the fix has to travel with the numbers, and every test here is written
so that deleting the provenance check makes it fail.
"""

import math

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.adjudication import adjudicate_candidate, adjudicate_holdout_candidate
from crypto_trade.cup20.config import IS_END, SEALED_END, SEALED_START, load_config
from crypto_trade.cup20.metrics import holdout_folds, is_folds
from crypto_trade.cup20.runner import CandidateRun
from crypto_trade.cup20.scored_metrics import (
    ASSEMBLED_METRIC_KEYS,
    STAGE_HOLDOUT,
    STAGE_IN_SAMPLE,
    MetricProvenance,
    ScoredVector,
    assemble_scored_metrics,
    neighbourhood_median,
)
from crypto_trade.tournament.engine_v2 import EvaluationResult

CONFIG = load_config("tournament/cup20/config.toml").raw
IS_START = pd.Timestamp("2020-08-01T00:00:00Z")


def _result(index: pd.DatetimeIndex, *, drift: float, seed: int) -> EvaluationResult:
    """One book over ``index``. Shape copied from ``window_metrics``' own contract."""
    rng = np.random.default_rng(seed)
    net = drift + rng.normal(0.0, 0.010, len(index))
    fee, slippage = 0.00005, 0.00002
    price = net + fee + slippage
    returns = pd.DataFrame(
        {
            "net_return": net,
            "price_pnl": price,
            "long_price_pnl": price * 0.65,
            "short_price_pnl": price * 0.35,
            "funding_pnl": np.zeros(len(index)),
            "long_funding_pnl": np.zeros(len(index)),
            "short_funding_pnl": np.zeros(len(index)),
            "fees": np.full(len(index), fee),
            "slippage": np.full(len(index), slippage),
            "turnover": np.full(len(index), 0.004),
        },
        index=index,
    )
    events = pd.DataFrame({"event_type": ["trade"] * 900, "notional": [100.0] * 900})
    return EvaluationResult(returns=returns, positions=pd.DataFrame(), events=events)


def _run(start: pd.Timestamp, end: pd.Timestamp, *, seed: int = 7) -> CandidateRun:
    index = pd.date_range(start, end, freq="8h", inclusive="left", name="timestamp")
    return CandidateRun(
        targets=pd.DataFrame(),
        scaled_targets=pd.DataFrame(),
        risk_scalars=pd.Series(dtype=float),
        unscaled=_result(index, drift=0.0004, seed=seed),
        results={
            1: _result(index, drift=0.00045, seed=seed),
            2: _result(index, drift=0.00035, seed=seed + 1),
            3: _result(index, drift=0.00025, seed=seed + 2),
        },
    )


IS_RUN = _run(IS_START, IS_END)
SEALED_RUN = _run(SEALED_START, SEALED_END, seed=31)


def _in_sample() -> ScoredVector:
    return assemble_scored_metrics(IS_RUN, stage=STAGE_IN_SAMPLE, is_start=IS_START, is_end=IS_END)


def _holdout() -> ScoredVector:
    return assemble_scored_metrics(
        SEALED_RUN, stage=STAGE_HOLDOUT, is_start=SEALED_START, is_end=SEALED_END
    )


# --- the fixture, without which every assertion below is vacuous --------------------------------


def test_both_stages_assemble_the_identical_key_set():
    # This is exactly why shape checking cannot tell them apart, and therefore why the provenance
    # check is not redundant with the `ASSEMBLED_METRIC_KEYS` check that runs beside it.
    assert set(_in_sample()) == ASSEMBLED_METRIC_KEYS == set(_holdout())


def test_a_scored_vector_is_an_ordinary_mapping_to_every_consumer():
    scored = _in_sample()
    assert scored["net_sharpe"] == pytest.approx(dict(scored)["net_sharpe"])
    assert len(scored) == len(ASSEMBLED_METRIC_KEYS)
    assert "net_sharpe" in scored
    assert scored == dict(scored)
    assert "in_sample" in repr(scored)


# --- provenance is recorded ---------------------------------------------------------------------


def test_an_in_sample_assembly_records_its_stage_window_and_folds():
    provenance = _in_sample().provenance
    assert provenance.stage == STAGE_IN_SAMPLE
    assert (provenance.window_start, provenance.window_end) == (IS_START, IS_END)
    assert provenance.folds == is_folds(IS_START, IS_END)
    assert "F1,F2,F3,F4" in provenance.describe()


def test_a_holdout_assembly_records_its_stage_window_and_folds():
    provenance = _holdout().provenance
    assert provenance.stage == STAGE_HOLDOUT
    assert (provenance.window_start, provenance.window_end) == (SEALED_START, SEALED_END)
    assert provenance.folds == holdout_folds(SEALED_START, SEALED_END)
    assert "H1,H2,H3,H4" in provenance.describe()


def test_each_stage_defaults_to_its_own_fold_construction():
    # Without this, `folds=None` would mean "in-sample folds" for the holdout too, and the sealed
    # window would be scored on four blocks that do not tile it.
    assert _in_sample().provenance.folds[0][0] == "F1"
    assert _holdout().provenance.folds[0][0] == "H1"


# --- the assembly refuses a window that is not the stage's ---------------------------------------


def test_assembly_rejects_an_unknown_stage():
    with pytest.raises(ValueError, match="stage must be one of"):
        assemble_scored_metrics(IS_RUN, stage="oos", is_start=IS_START, is_end=IS_END)


def test_a_holdout_assembly_must_cover_exactly_the_sealed_window():
    with pytest.raises(ValueError, match="must cover exactly the sealed window"):
        assemble_scored_metrics(
            IS_RUN,
            stage=STAGE_HOLDOUT,
            is_start=SEALED_START,
            is_end=SEALED_END - pd.DateOffset(months=1),
        )


def test_a_holdout_assembly_starting_early_is_rejected():
    with pytest.raises(ValueError, match="must cover exactly the sealed window"):
        assemble_scored_metrics(IS_RUN, stage=STAGE_HOLDOUT, is_start=IS_START, is_end=SEALED_END)


def test_an_in_sample_assembly_may_not_reach_past_the_cutoff():
    with pytest.raises(ValueError, match="reaches into the sealed side"):
        assemble_scored_metrics(
            IS_RUN,
            stage=STAGE_IN_SAMPLE,
            is_start=IS_START,
            is_end=IS_END + pd.Timedelta(days=1),
        )


def test_an_in_sample_assembly_that_stops_short_of_the_cutoff_is_allowed():
    # The IS window's START is computed at snapshot build, so short windows are legitimate; only
    # the END is frozen. Asserting the permissive direction keeps the check above from being read
    # as pinning both ends.
    early = IS_END - pd.DateOffset(years=4)
    scored = assemble_scored_metrics(
        _run(early, IS_END - pd.DateOffset(months=6)),
        stage=STAGE_IN_SAMPLE,
        is_start=early,
        is_end=IS_END - pd.DateOffset(months=6),
    )
    assert scored.provenance.window_end == IS_END - pd.DateOffset(months=6)


def test_the_folds_override_must_equal_the_canonical_construction():
    shifted = tuple((name, start, end) for name, start, end in is_folds(IS_START, IS_END))
    relabelled = (("X1", *shifted[0][1:]), *shifted[1:])
    with pytest.raises(ValueError, match="must use the folds the charter states"):
        assemble_scored_metrics(
            IS_RUN, stage=STAGE_IN_SAMPLE, is_start=IS_START, is_end=IS_END, folds=relabelled
        )


def test_the_canonical_folds_override_is_accepted():
    # Not vacuous: the test above must fail for the LABEL, not because any override is refused.
    scored = assemble_scored_metrics(
        IS_RUN,
        stage=STAGE_IN_SAMPLE,
        is_start=IS_START,
        is_end=IS_END,
        folds=is_folds(IS_START, IS_END),
    )
    assert scored.provenance.folds == is_folds(IS_START, IS_END)


# --- the adjudicators refuse the other stage ------------------------------------------------------

HOLDOUT = CONFIG["holdout"]


def _adjudicate_holdout(scored):
    return adjudicate_holdout_candidate(
        scored,
        team_id="team-01",
        candidate_id="c1",
        holdout=HOLDOUT,
        trial_adjusted_confidence=0.97,
        nominated_point_double_cost_return=0.11,
    )


def _adjudicate_in_sample(scored):
    return adjudicate_candidate(
        scored,
        team_id="team-01",
        candidate_id="c1",
        floors=CONFIG["floors"],
        statistics_config=CONFIG["statistics"],
        research_config=CONFIG["research"],
        declared_roles=("long", "short"),
        sign_inversion_passes_core=False,
        neighbourhood_positive_fraction=0.86,
        trial_adjusted_confidence=0.97,
        drawdown_floor=float(CONFIG["floors"]["max_drawdown"]),
    )


def test_the_holdout_adjudicator_refuses_an_in_sample_vector():
    """The defect, directly: the wrong four years, scored as the holdout, caught by name."""
    with pytest.raises(ValueError, match="assembled for the 'in_sample' stage"):
        _adjudicate_holdout(_in_sample())


def test_the_in_sample_adjudicator_refuses_a_holdout_vector():
    with pytest.raises(ValueError, match="assembled for the 'holdout' stage"):
        _adjudicate_in_sample(_holdout())


def test_each_adjudicator_accepts_its_own_stage():
    # Not vacuous: without this, an adjudicator that refused EVERYTHING would pass both tests
    # above while making the tournament unrunnable.
    assert _adjudicate_holdout(_holdout()).team_id == "team-01"
    assert _adjudicate_in_sample(_in_sample()).team_id == "team-01"


def test_the_verdict_carries_the_provenance_forward_for_the_record():
    verdict = _adjudicate_holdout(_holdout())
    assert verdict.scored.provenance.stage == STAGE_HOLDOUT


@pytest.mark.parametrize("adjudicate", [_adjudicate_holdout, _adjudicate_in_sample])
def test_both_adjudicators_refuse_a_bare_mapping(adjudicate):
    # Fail-closed: a hand-built dict may well hold the right numbers, but it makes no claim about
    # where they came from, and an unverifiable claim is refused rather than assumed correct.
    with pytest.raises(ValueError, match="carries no provenance"):
        adjudicate(dict(_holdout()))


def test_the_missing_key_check_still_runs_before_the_provenance_check():
    # Ordering matters for the error a caller actually sees: a vector missing half its keys is a
    # different mistake from one assembled for the wrong stage, and should be named as such.
    partial = {key: 0.5 for key in sorted(ASSEMBLED_METRIC_KEYS)[:5]}
    with pytest.raises(ValueError, match="is missing"):
        _adjudicate_holdout(partial)


# --- provenance survives the neighbourhood median -------------------------------------------------


def test_the_neighbourhood_median_keeps_the_shared_provenance():
    points = [_holdout(), _holdout(), _holdout()]
    median = neighbourhood_median(points)
    assert isinstance(median, ScoredVector)
    assert median.provenance == points[0].provenance
    assert _adjudicate_holdout(median).team_id == "team-01"


def test_the_neighbourhood_median_still_fails_closed_on_a_non_finite_point():
    # The provenance work must not have disturbed the NaN guard that every hard floor depends on.
    good = _holdout()
    bad = ScoredVector(dict(good) | {"net_sharpe": math.nan}, good.provenance)
    assert math.isnan(neighbourhood_median([good, bad, good])["net_sharpe"])


def test_a_neighbourhood_mixing_two_stages_is_refused():
    with pytest.raises(ValueError, match="disagree about their provenance"):
        neighbourhood_median([_holdout(), _in_sample()])


def test_a_neighbourhood_mixing_provenance_with_bare_mappings_is_refused():
    # The fail-open this closes: silently dropping the one provenance present would hand the
    # adjudicator a bare mapping and turn a wrong-stage error into a missing-provenance one.
    with pytest.raises(ValueError, match="carry provenance; a neighbourhood is assembled"):
        neighbourhood_median([_holdout(), dict(_holdout())])


def test_a_neighbourhood_of_bare_mappings_still_medians_to_a_bare_mapping():
    # Backwards compatible on purpose -- and harmless, because both adjudicators reject the result.
    median = neighbourhood_median([dict(_holdout()), dict(_holdout())])
    assert not isinstance(median, ScoredVector)


def test_two_provenances_over_the_same_stage_and_window_are_interchangeable():
    # Provenance equality must be by VALUE; distinct-but-equal objects are one neighbourhood.
    first = _holdout()
    second = ScoredVector(
        dict(first),
        MetricProvenance(
            stage=STAGE_HOLDOUT,
            window_start=SEALED_START,
            window_end=SEALED_END,
            folds=holdout_folds(SEALED_START, SEALED_END),
        ),
    )
    assert first.provenance is not second.provenance
    assert isinstance(neighbourhood_median([first, second]), ScoredVector)
