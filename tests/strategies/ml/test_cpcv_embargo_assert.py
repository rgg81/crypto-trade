"""Adversarial unit tests for combinatorial_purged_cv embargo assertion (iter-v3/002).

Tests verify that the gap-assertion machinery in combinatorial_purged_cv
correctly rejects silently degraded gaps.  Per brief Section 3.6:

  'Calling combinatorial_purged_cv(n_samples=1000, gap=129) accepts the gap.
   Calling with gap=11 when the documented formula would produce gap=129
   raises an assertion error or a clear warning, not a silent rescaling.'

This test is the regression guard against the iter-v3/001 bug where
run_baseline_v3.py:381 silently passed gap=min(88, 11)=11 to CPCV.

iter-v3/068 Path C: CORRECT_GAP updated 66→129 (timeout 21→42 candles, 3-sym universe).
iter-v3/069: CORRECT_GAP REVERTED 129→66 (K=21 restored, 3-sym BCH/LDO/TRX universe).
iter-v3/124: CORRECT_GAP updated 66→192 (K=63 longer-cadence labels; runner-local override;
  validation_v3.REQUIRED_GAP stays at 66 — the K=21 8h baseline constant).
  Formula: (timeout_candles + 1) * n_symbols = (63 + 1) * 3 = 192.
iter-v3/128: cardinality-6 override 132 = (21+1)*6 (6-symbol WILD L1 universe).
  validation_v3.REQUIRED_GAP stays at 66 (the 3-symbol module constant, unchanged).
"""

from __future__ import annotations

import pytest

from crypto_trade.strategies.ml.validation_v3 import (
    REQUIRED_GAP,
    combinatorial_purged_cv,
    cpcv_walk_forward_splits,
)

# v3 documented constants
# iter-v3/110 (cycle-6 EXPLORATION #1) — symbol universe replacement
# BCH/LDO/TRX → CRV/AAVE/GRT/ADA (4 symbols). REQUIRED_GAP recomputed 66 → 88.
# iter-v3/111 — Critic-mandated clean re-test under triple_barrier label.
# Universe unchanged (CRV/AAVE/GRT/ADA, 4 symbols). REQUIRED_GAP = 88.
# iter-v3/112 — POOLED architecture. Universe REVERTS CRV/AAVE/GRT/ADA → BCH/LDO/TRX.
# REQUIRED_GAP reverts 88 → 66 = (21+1)*3 (3-symbol BCH/LDO/TRX canonical universe).
# iter-v3/124 — K=63 longer-cadence labels axis. CORRECT_GAP = (63+1)*3 = 192.
# validation_v3.REQUIRED_GAP stays at 66 (K=21 8h baseline); runner-local override = 192.
# iter-v3/128 — 6-symbol sector-pure L1 universe. CARDINALITY_6_GAP = (21+1)*6 = 132.
# validation_v3.REQUIRED_GAP stays at 66 (3-symbol module constant, NOT changed at /128).
TIMEOUT_CANDLES = 63  # 30240 min / 480 min = 63 candles at 8h (iter-v3/124 K=63 axis)
N_SYMBOLS = 3  # BCH/LDO/TRX (iter-v3/112 revert to /059-canonical 3-symbol universe)
CORRECT_GAP = (TIMEOUT_CANDLES + 1) * N_SYMBOLS  # 192 = (63+1)*3
DEGRADED_GAP = 11  # what iter-v3/001 actually passed (bug)

# iter-v3/128: cardinality-6 gap constant for the new 6-symbol universe
N_SYMBOLS_128 = 6  # ATOM/RUNE/AVAX/HBAR/ICP/ALGO (iter-v3/128 sector-pure L1)
TIMEOUT_CANDLES_K21 = 21  # K=21 at 8h (unchanged from /121-canonical)
CARDINALITY_6_GAP = (TIMEOUT_CANDLES_K21 + 1) * N_SYMBOLS_128  # 132 = (21+1)*6

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
    """REQUIRED_GAP constant == (K=21 timeout_candles + 1) * n_symbols = 66.

    iter-v3/124: validation_v3.REQUIRED_GAP stays at 66 (the K=21 8h baseline constant).
    The runner-local CORRECT_GAP = 192 = (63+1)*3 is the /124 override — NOT the module constant.
    These are two different quantities: REQUIRED_GAP is the module default; CORRECT_GAP is the
    /124-specific runner-local value that the runner passes to CV functions.
    """
    # REQUIRED_GAP constant stays at 66 — K=21 baseline, NOT updated for K=63.
    assert REQUIRED_GAP == 66, (
        f"REQUIRED_GAP should be 66 for the iter-v3/112 BCH/LDO/TRX 3-symbol v3 "
        f"universe at K=21: (21+1)*3=66, got {REQUIRED_GAP}. "
        "validation_v3.REQUIRED_GAP is NOT changed at iter-v3/124 — runner-local override is 192."
    )
    # The runner-local CORRECT_GAP for /124 (K=63):
    assert CORRECT_GAP == 192, (
        f"CORRECT_GAP should be 192 = (63+1)*3 for iter-v3/124 K=63 axis. Got {CORRECT_GAP}."
    )
    # Verify the CORRECT_GAP formula is consistent with TIMEOUT_CANDLES:
    formula_gap = (TIMEOUT_CANDLES + 1) * N_SYMBOLS
    assert CORRECT_GAP == formula_gap, (
        f"CORRECT_GAP={CORRECT_GAP} does not match formula "
        f"(TIMEOUT_CANDLES+1)*N_SYMBOLS = ({TIMEOUT_CANDLES}+1)*{N_SYMBOLS} = {formula_gap}."
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


# ---------------------------------------------------------------------------
# (g) iter-v3/128: cardinality-6 gap 132 = (21+1)*6 is accepted and formula is correct
# ---------------------------------------------------------------------------


def test_cardinality_6_gap_accepted() -> None:
    """iter-v3/128: combinatorial_purged_cv(gap=132) with expected_gap=132 runs without error.

    CARDINALITY_6_GAP = (21+1)*6 = 132. This is the runner-local override for the
    6-symbol sector-pure L1 universe (ATOM/RUNE/AVAX/HBAR/ICP/ALGO).
    validation_v3.REQUIRED_GAP stays at 66 — the 3-symbol module constant.
    """
    splits = combinatorial_purged_cv(
        n_samples=N_SAMPLES,
        n_splits=10,
        n_test_splits=2,
        gap=CARDINALITY_6_GAP,
        embargo=0,
        expected_gap=CARDINALITY_6_GAP,
    )
    assert len(splits) == 45, f"Expected 45 CPCV paths (C(10,2)), got {len(splits)}"


def test_cardinality_6_gap_formula() -> None:
    """iter-v3/128: CARDINALITY_6_GAP formula (21+1)*6 = 132 is correct.

    Verifies the runner-local override formula matches the expected value.
    The formula follows the established pattern: (timeout_candles + 1) * n_symbols.
    At K=21 and n_symbols=6: (21+1)*6 = 132.
    """
    assert CARDINALITY_6_GAP == 132, (
        f"CARDINALITY_6_GAP = {CARDINALITY_6_GAP} — expected 132. "
        "Formula: (TIMEOUT_CANDLES_K21+1)*N_SYMBOLS_128 = (21+1)*6 = 132. "
        "iter-v3/128 runner-local override for 6-symbol sector-pure L1 universe."
    )
    # REQUIRED_GAP module constant stays at 66 (3-symbol baseline, NOT changed)
    assert REQUIRED_GAP == 66, (
        f"REQUIRED_GAP = {REQUIRED_GAP} — expected 66 (3-symbol baseline constant). "
        "validation_v3.REQUIRED_GAP must NOT be changed for iter-v3/128. "
        "Use runner-local override 132 at the CV-call site."
    )
    # The override is exactly double the module constant (6 vs 3 symbols)
    assert CARDINALITY_6_GAP == REQUIRED_GAP * 2, (
        f"CARDINALITY_6_GAP ({CARDINALITY_6_GAP}) should be 2× REQUIRED_GAP ({REQUIRED_GAP}) "
        "since cardinality doubled from 3 to 6."
    )
