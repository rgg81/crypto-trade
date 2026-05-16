"""Adversarial unit tests for combinatorial_purged_cv embargo assertion (iter-v3/002).

Tests verify that the gap-assertion machinery in combinatorial_purged_cv
correctly rejects silently degraded gaps.  Per brief Section 3.6:

  'Calling combinatorial_purged_cv(n_samples=1000, gap=129) accepts the gap.
   Calling with gap=11 when the documented formula would produce gap=129
   raises an assertion error or a clear warning, not a silent rescaling.'

This test is the regression guard against the iter-v3/001 bug where
run_baseline_v3.py:381 silently passed gap=min(88, 11)=11 to CPCV.

iter-v3/068 Path C: CORRECT_GAP updated 66→129 (timeout 21→42 candles, 3-sym universe).
"""

from __future__ import annotations

import pytest

from crypto_trade.strategies.ml.validation_v3 import (
    REQUIRED_GAP,
    combinatorial_purged_cv,
    cpcv_walk_forward_splits,
)

# v3 documented constants
# iter-v3/076: STALE-TEST FIX. This test was set up at iter-v3/069 for a 4-symbol
# universe (BCH+LDO+TRX+ADA) but iter-v3/069 closed out reverting to the 3-symbol
# universe (ADA dropped — universe-expansion EXPLORATION failed). The constants
# below were never updated, so test_required_gap_matches_formula has been failing
# (asserting 88 while REQUIRED_GAP is 66) since /069. Corrected here to match the
# canonical BASELINE_V3 3-symbol universe: REQUIRED_GAP = (21+1)*3 = 66.
TIMEOUT_CANDLES = 21  # 10080 min / 480 min = 21 candles at 8h
N_SYMBOLS = 3  # BCH + LDO + TRX (canonical 3-symbol v3 universe; ADA dropped at /069)
CORRECT_GAP = (TIMEOUT_CANDLES + 1) * N_SYMBOLS  # 66
DEGRADED_GAP = 11  # what iter-v3/001 actually passed (bug)

N_SAMPLES = 1000  # representative IS candle count


# ---------------------------------------------------------------------------
# (a) Correct gap is accepted without error
# ---------------------------------------------------------------------------


def test_correct_gap_accepted() -> None:
    """combinatorial_purged_cv(gap=CORRECT_GAP, expected_gap=CORRECT_GAP) runs without error."""
    splits = combinatorial_purged_cv(
        n_samples=N_SAMPLES,
        n_splits=10,
        n_test_splits=2,
        gap=CORRECT_GAP,
        embargo=0,
        expected_gap=CORRECT_GAP,
    )
    assert len(splits) == 45, f"Expected 45 CPCV paths (C(10,2)), got {len(splits)}"
    for train_idx, test_idx in splits:
        assert len(train_idx) > 0, "Train set must be non-empty"
        assert len(test_idx) > 0, "Test set must be non-empty"


# ---------------------------------------------------------------------------
# (b) Degraded gap is rejected when expected_gap is specified
# ---------------------------------------------------------------------------


def test_degraded_gap_raises_assertion() -> None:
    """combinatorial_purged_cv raises AssertionError when gap=11 but expected_gap=CORRECT_GAP."""
    with pytest.raises(AssertionError) as exc_info:
        combinatorial_purged_cv(
            n_samples=N_SAMPLES,
            n_splits=10,
            n_test_splits=2,
            gap=DEGRADED_GAP,
            embargo=0,
            expected_gap=CORRECT_GAP,
        )
    # The error message should name both values for debuggability
    msg = str(exc_info.value)
    assert str(DEGRADED_GAP) in msg, f"Error message should contain degraded gap={DEGRADED_GAP}"
    assert str(CORRECT_GAP) in msg, f"Error message should contain expected gap={CORRECT_GAP}"


# ---------------------------------------------------------------------------
# (c) No expected_gap specified — gap=11 is silently accepted (backwards compat)
# ---------------------------------------------------------------------------


def test_no_expected_gap_no_assertion() -> None:
    """combinatorial_purged_cv without expected_gap accepts any gap (no assertion)."""
    # This verifies backwards compatibility — the assertion is OPT-IN
    splits = combinatorial_purged_cv(
        n_samples=N_SAMPLES,
        n_splits=10,
        n_test_splits=2,
        gap=DEGRADED_GAP,
        embargo=0,
        # expected_gap NOT passed — no assertion should fire
    )
    assert len(splits) == 45


# ---------------------------------------------------------------------------
# (d) REQUIRED_GAP constant matches the documented formula
# ---------------------------------------------------------------------------


def test_required_gap_matches_formula() -> None:
    """REQUIRED_GAP constant == (timeout_candles + 1) * n_symbols."""
    formula_gap = (TIMEOUT_CANDLES + 1) * N_SYMBOLS
    assert REQUIRED_GAP == formula_gap, (
        f"REQUIRED_GAP={REQUIRED_GAP} does not match formula "
        f"(timeout_candles+1)*n_symbols={formula_gap}. "
        "Update the REQUIRED_GAP constant or the formula."
    )
    # iter-v3/076 STALE-TEST FIX: the canonical v3 universe is 3-symbol
    # (BCH+LDO+TRX); ADA was dropped at the iter-v3/069 universe-expansion
    # closeout. REQUIRED_GAP = (timeout_candles 21 + 1) * 3 symbols = 66.
    assert REQUIRED_GAP == 66, (
        f"REQUIRED_GAP should be 66 for the canonical 3-symbol v3 universe "
        f"(BCH+LDO+TRX): (21+1)*3=66, got {REQUIRED_GAP}"
    )


# ---------------------------------------------------------------------------
# (e) cpcv_walk_forward_splits default gap asserts == REQUIRED_GAP
# ---------------------------------------------------------------------------


def test_cpcv_walk_forward_splits_correct_gap_accepted() -> None:
    """cpcv_walk_forward_splits with gap=REQUIRED_GAP runs without error."""
    splits = list(
        cpcv_walk_forward_splits(
            n_samples=N_SAMPLES,
            n_splits=10,
            n_test_splits=2,
            gap=REQUIRED_GAP,
            embargo=27,
        )
    )
    assert len(splits) == 45


def test_cpcv_walk_forward_splits_degraded_gap_raises() -> None:
    """cpcv_walk_forward_splits with gap=11 (degraded) raises AssertionError."""
    with pytest.raises(AssertionError):
        list(
            cpcv_walk_forward_splits(
                n_samples=N_SAMPLES,
                n_splits=10,
                n_test_splits=2,
                gap=DEGRADED_GAP,
                embargo=0,
            )
        )


# ---------------------------------------------------------------------------
# (f) Purge gap actually removes samples from train set
# ---------------------------------------------------------------------------


def test_gap_removes_boundary_samples() -> None:
    """With gap=20 (test-local), boundary samples adjacent to test blocks are purged from train."""
    n = 200
    gap = 20
    splits = combinatorial_purged_cv(
        n_samples=n,
        n_splits=5,
        n_test_splits=1,
        gap=gap,
        embargo=0,
        expected_gap=gap,  # self-consistent
    )
    for train_idx, test_idx in splits:
        test_min = int(test_idx.min())
        test_max = int(test_idx.max())
        train_set = set(train_idx.tolist())
        # Samples within `gap` of any test boundary must be absent from train
        for boundary_idx in range(max(0, test_min - gap), min(n, test_max + gap + 1)):
            if boundary_idx not in set(test_idx.tolist()):
                assert boundary_idx not in train_set, (
                    f"Sample {boundary_idx} is within gap={gap} of test block "
                    f"[{test_min}, {test_max}] but appears in the train set."
                )
