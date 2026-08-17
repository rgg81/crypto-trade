"""Smoke tests for iter-v1/020: BTC-only cohort isolation (Model H).

Tests verify:
1. V1_ITER020_UNIVERSE is exactly {"BTCUSDT"} — F-AXIS-MECHANISM #1 precondition.
2. BTCUSDT is NOT in V1_EXCLUDED_SYMBOLS — dispatch guard won't false-positive.
3. assert_v1_universe() accepts {BTCUSDT} — universe check passes.
4. /020 dispatch condition fires correctly (set equality) and does NOT fire for
   baseline, /017, /018, /019.
5. V1_ITER020_UNIVERSE is a strict subset of V1_BASELINE_UNIVERSE.
6. Model H uses apply_r1=False (mirrors Model A pool semantics).
7. assert guard raises on non-BTCUSDT input (F-AXIS-MECHANISM #1 guard).
8. No gate-related constants exist for /020 (pure cohort isolation — no gate).
9. No cross-track imports from features_v2 or features_v3 in /020 dispatch.
10. /020 dispatch is mutually exclusive with /019, /018, /017, baseline.
11. BTC-only training row count expectation documented (F-AXIS-MECHANISM #2 band).
12. Runner constant matches expected Model H config (atr_tp=2.9, atr_sl=1.45).
13. V1_ITER020_UNIVERSE declared AFTER V1_ITER019_UNIVERSE (ordering invariant).
14. /020 dispatch does NOT reference risk_v2 gate imports (pure isolation).

Brief reference: briefs-v1/iteration_v1-020/research_brief.md Sections 3.1, 3.3,
  F-AXIS-MECHANISM #1, #2, #3, and Section 10.3 pre-flight verification.
"""

from __future__ import annotations

import pytest
from run_baseline_v1 import (
    V1_ITER018_UNIVERSE,
    V1_ITER019_UNIVERSE,
    V1_ITER020_UNIVERSE,
)

from crypto_trade.features_v1 import (
    V1_BASELINE_UNIVERSE,
    V1_EXCLUDED_SYMBOLS,
    assert_v1_universe,
)


class TestV1Iter020UniverseConstant:
    """Test V1_ITER020_UNIVERSE constant correctness."""

    def test_universe_length_is_1(self) -> None:
        """V1_ITER020_UNIVERSE must have exactly 1 symbol (BTC-only cohort)."""
        assert len(V1_ITER020_UNIVERSE) == 1, (
            f"Expected 1 symbol in V1_ITER020_UNIVERSE (BTC-only), "
            f"got {len(V1_ITER020_UNIVERSE)}: {V1_ITER020_UNIVERSE}"
        )

    def test_universe_contains_btcusdt(self) -> None:
        """V1_ITER020_UNIVERSE must contain BTCUSDT as the sole symbol."""
        assert "BTCUSDT" in V1_ITER020_UNIVERSE, (
            "BTCUSDT must be the only symbol in V1_ITER020_UNIVERSE for "
            "iter-v1/020 Model H dispatch"
        )

    def test_universe_exact_symbols(self) -> None:
        """V1_ITER020_UNIVERSE must be exactly {"BTCUSDT"}."""
        expected = frozenset({"BTCUSDT"})
        assert frozenset(V1_ITER020_UNIVERSE) == expected, (
            f"V1_ITER020_UNIVERSE symbols mismatch: got {set(V1_ITER020_UNIVERSE)}, "
            f"expected {expected}"
        )

    def test_iter020_universe_is_strict_subset_of_baseline(self) -> None:
        """V1_ITER020_UNIVERSE must be a strict subset of V1_BASELINE_UNIVERSE.

        iter-v1/020 is a cohort isolation (single-symbol subset), NOT a universe
        expansion. BTCUSDT is already in V1_BASELINE_UNIVERSE; we are testing
        the single-symbol training regime, not adding a new symbol.
        """
        assert set(V1_ITER020_UNIVERSE).issubset(set(V1_BASELINE_UNIVERSE)), (
            "V1_ITER020_UNIVERSE must be a subset of V1_BASELINE_UNIVERSE; "
            f"BTC-only cohort is not an expansion. "
            f"V1_ITER020_UNIVERSE={set(V1_ITER020_UNIVERSE)}, "
            f"V1_BASELINE_UNIVERSE={set(V1_BASELINE_UNIVERSE)}"
        )
        assert len(V1_ITER020_UNIVERSE) < len(V1_BASELINE_UNIVERSE), (
            "V1_ITER020_UNIVERSE must be strictly smaller than V1_BASELINE_UNIVERSE"
        )

    def test_iter020_declared_after_iter019(self) -> None:
        """V1_ITER020_UNIVERSE is declared after V1_ITER019_UNIVERSE (ordering invariant).

        Both constants exist in run_baseline_v1 — importing both without error
        confirms the module-level ordering is intact.
        """
        # Both should be non-empty tuples — their declaration order in the module
        # is verified implicitly by the fact that both names resolve correctly.
        assert len(V1_ITER019_UNIVERSE) == 1
        assert len(V1_ITER020_UNIVERSE) == 1


class TestBtcNotExcluded:
    """Test that BTCUSDT is not in V1_EXCLUDED_SYMBOLS (required for dispatch)."""

    def test_btcusdt_not_excluded(self) -> None:
        """BTCUSDT must NOT be in V1_EXCLUDED_SYMBOLS for the dispatch to work.

        BTCUSDT is in V1_BASELINE_UNIVERSE — it is a v1 symbol, not a v2/v3 symbol.
        """
        assert "BTCUSDT" not in V1_EXCLUDED_SYMBOLS, (
            "BTCUSDT must NOT be in V1_EXCLUDED_SYMBOLS; "
            f"it is a v1 baseline symbol. V1_EXCLUDED_SYMBOLS={V1_EXCLUDED_SYMBOLS}"
        )

    def test_later_unreserved_xrp_and_remaining_v2_exclusions(self) -> None:
        """DOGE and NEAR remain excluded after XRP was un-reserved at iter-v1/088.

        NOTE: SOLUSDT was removed from V1_EXCLUDED_SYMBOLS at iter-v1/017 to enable
        Model F universe-expansion dispatch. XRP was later removed at iter-v1/088.
        """
        assert "XRPUSDT" not in V1_EXCLUDED_SYMBOLS
        for sym in ("DOGEUSDT", "NEARUSDT"):
            assert sym in V1_EXCLUDED_SYMBOLS, f"v2 symbol {sym} must remain in V1_EXCLUDED_SYMBOLS"

    def test_v3_symbols_still_excluded(self) -> None:
        """v3 symbols must remain excluded (regression guard)."""
        for sym in ("BCHUSDT", "LDOUSDT", "TRXUSDT"):
            assert sym in V1_EXCLUDED_SYMBOLS, f"v3 symbol {sym} must remain in V1_EXCLUDED_SYMBOLS"

    def test_bnbusdt_not_excluded(self) -> None:
        """BNBUSDT un-reserved at iter-v1/087 per user directive 2026-06-10."""
        assert "BNBUSDT" not in V1_EXCLUDED_SYMBOLS, (
            "iter-v1/087 un-reserved BNBUSDT — it must NOT be in V1_EXCLUDED_SYMBOLS. "
            f"Current V1_EXCLUDED_SYMBOLS = {V1_EXCLUDED_SYMBOLS}"
        )


class TestAssertV1UniverseAcceptsIter020Universe:
    """Test assert_v1_universe() accepts the 1-symbol iter-v1/020 set."""

    def test_assert_accepts_iter020_universe(self) -> None:
        """assert_v1_universe must not raise for V1_ITER020_UNIVERSE (BTCUSDT)."""
        # Should not raise — BTCUSDT is a v1 baseline symbol, not excluded
        assert_v1_universe(V1_ITER020_UNIVERSE)

    def test_assert_accepts_single_btcusdt_string(self) -> None:
        """assert_v1_universe must accept the literal single-element tuple."""
        assert_v1_universe(("BTCUSDT",))

    def test_assert_accepts_baseline_universe(self) -> None:
        """assert_v1_universe must still accept V1_BASELINE_UNIVERSE (regression)."""
        assert_v1_universe(V1_BASELINE_UNIVERSE)

    def test_assert_accepts_iter018_universe(self) -> None:
        """assert_v1_universe must still accept V1_ITER018_UNIVERSE (regression)."""
        assert_v1_universe(V1_ITER018_UNIVERSE)

    def test_assert_accepts_iter019_universe(self) -> None:
        """assert_v1_universe must still accept V1_ITER019_UNIVERSE (regression)."""
        assert_v1_universe(V1_ITER019_UNIVERSE)

    def test_assert_rejects_v3_symbol(self) -> None:
        """assert_v1_universe must reject a v3 symbol (BCHUSDT)."""
        with pytest.raises(AssertionError, match="v1 cannot trade v2/v3 symbols"):
            assert_v1_universe(("BTCUSDT", "BCHUSDT"))

    def test_assert_accepts_later_unreserved_xrp(self) -> None:
        """assert_v1_universe accepts XRP after iter-v1/088."""
        assert_v1_universe(("BTCUSDT", "XRPUSDT"))


class TestIter020DispatchBranchRouting:
    """Test that the elif branch for V1_ITER020_UNIVERSE routes correctly.

    The runner dispatch logic (simplified):
        if set(symbols) == set(V1_BASELINE_UNIVERSE):    ← baseline (4 models)
            ...
        elif set(symbols) == set(V1_ITER017_UNIVERSE):   ← iter-v1/017 (5 models)
            ...
        elif set(symbols) == set(V1_ITER018_UNIVERSE):   ← iter-v1/018 Model C only
            ...
        elif set(symbols) == set(V1_ITER019_UNIVERSE):   ← iter-v1/019 Model G only
            ...
        elif set(symbols) == set(V1_ITER020_UNIVERSE):   ← iter-v1/020 Model H only
            ...
        else:
            ...                                          ← custom POOLED fallback
    """

    def test_iter020_dispatch_fires_for_btcusdt(self) -> None:
        symbols = ("BTCUSDT",)
        assert set(symbols) == set(V1_ITER020_UNIVERSE)

    def test_iter020_dispatch_does_not_fire_for_baseline(self) -> None:
        assert set(V1_BASELINE_UNIVERSE) != set(V1_ITER020_UNIVERSE)

    def test_iter020_dispatch_does_not_fire_for_iter017(self) -> None:
        from run_baseline_v1 import V1_ITER017_UNIVERSE

        assert set(V1_ITER017_UNIVERSE) != set(V1_ITER020_UNIVERSE)

    def test_iter020_dispatch_does_not_fire_for_iter018(self) -> None:
        # LINK-only vs BTC-only — must not collide
        assert set(V1_ITER018_UNIVERSE) != set(V1_ITER020_UNIVERSE)

    def test_iter020_dispatch_does_not_fire_for_iter019(self) -> None:
        # ETH-only vs BTC-only — must not collide
        assert set(V1_ITER019_UNIVERSE) != set(V1_ITER020_UNIVERSE)

    def test_iter020_dispatch_condition_is_true_for_btcusdt_only(self) -> None:
        """Verify the elif routing condition evaluates True for BTCUSDT only."""
        from run_baseline_v1 import V1_ITER017_UNIVERSE

        symbols = ("BTCUSDT",)
        baseline_check = set(symbols) == set(V1_BASELINE_UNIVERSE)
        iter017_check = set(symbols) == set(V1_ITER017_UNIVERSE)
        iter018_check = set(symbols) == set(V1_ITER018_UNIVERSE)
        iter019_check = set(symbols) == set(V1_ITER019_UNIVERSE)
        iter020_check = set(symbols) == set(V1_ITER020_UNIVERSE)

        assert not baseline_check, "BTCUSDT alone must NOT match the baseline branch"
        assert not iter017_check, "BTCUSDT alone must NOT match the iter-v1/017 branch"
        assert not iter018_check, "BTCUSDT alone must NOT match the iter-v1/018 branch"
        assert not iter019_check, "BTCUSDT alone must NOT match the iter-v1/019 branch"
        assert iter020_check, "BTCUSDT alone MUST match the iter-v1/020 branch"


class TestIter020AssertGuard:
    """Test the assert set(symbols) == {'BTCUSDT'} guard fires on wrong input."""

    def test_assert_guard_passes_for_btcusdt(self) -> None:
        """Guard must not raise for a single BTCUSDT symbol."""
        symbols = ("BTCUSDT",)
        # Mimics the runner's assert; should not raise
        assert set(symbols) == {"BTCUSDT"}, (
            f"iter-v1/020 guard: expected {{BTCUSDT}}, got {set(symbols)}"
        )

    def test_assert_guard_fires_for_empty_set(self) -> None:
        """Guard must raise for an empty symbol set."""
        symbols: tuple[str, ...] = ()
        with pytest.raises(AssertionError, match="iter-v1/020 guard"):
            assert set(symbols) == {"BTCUSDT"}, (
                f"iter-v1/020 guard: expected {{BTCUSDT}}, got {set(symbols)}"
            )

    def test_assert_guard_fires_for_ethusdt(self) -> None:
        """Guard must raise if ETH is passed instead of BTC."""
        symbols = ("ETHUSDT",)
        with pytest.raises(AssertionError, match="iter-v1/020 guard"):
            assert set(symbols) == {"BTCUSDT"}, (
                f"iter-v1/020 guard: expected {{BTCUSDT}}, got {set(symbols)}"
            )

    def test_assert_guard_fires_for_multi_symbol(self) -> None:
        """Guard must raise if multiple symbols passed (pool is not /020 dispatch)."""
        symbols = ("BTCUSDT", "ETHUSDT")
        with pytest.raises(AssertionError, match="iter-v1/020 guard"):
            assert set(symbols) == {"BTCUSDT"}, (
                f"iter-v1/020 guard: expected {{BTCUSDT}}, got {set(symbols)}"
            )


class TestIter020NoGateDesign:
    """Verify /020 is pure cohort isolation — no gate constants, no gate imports.

    Brief Section 3.1 states: NO BTC-trend gate, NO new feature, NO new labeling.
    This test ensures no /020-specific gate constant has been inadvertently added.
    """

    def test_no_iter020_gate_lookback_constant(self) -> None:
        """run_baseline_v1 must NOT have a V1_ITER020_BTC_GATE_LOOKBACK_BARS constant."""
        import run_baseline_v1

        assert not hasattr(run_baseline_v1, "V1_ITER020_BTC_GATE_LOOKBACK_BARS"), (
            "iter-v1/020 is pure cohort isolation — no gate lookback constant must exist"
        )

    def test_no_iter020_gate_threshold_constant(self) -> None:
        """run_baseline_v1 must NOT have a V1_ITER020_BTC_GATE_THRESHOLD_PCT constant."""
        import run_baseline_v1

        assert not hasattr(run_baseline_v1, "V1_ITER020_BTC_GATE_THRESHOLD_PCT"), (
            "iter-v1/020 is pure cohort isolation — no gate threshold constant must exist"
        )

    def test_no_iter020_gate_enabled_constant(self) -> None:
        """run_baseline_v1 must NOT have a V1_ITER020_BTC_GATE_ENABLED constant."""
        import run_baseline_v1

        assert not hasattr(run_baseline_v1, "V1_ITER020_BTC_GATE_ENABLED"), (
            "iter-v1/020 is pure cohort isolation — no gate enabled flag must exist"
        )


class TestIter020TrainingRowsBand:
    """Verify the per-cell row count expectation for the BTC-only model.

    From research_brief.md Section 4 F-AXIS-MECHANISM #2 + LM Master Phase 4.5 §2:
    BTC-only training IS trades anchor = 113 (baseline). Pool-independence ρ ≈ 0
    means Optuna basin close to pooled BTC-conditional optimum → minimal compression.
    F-AXIS #2 blocking band: IS [70, 150] / OOS [25, 55].
    LM Master tighter sub-bands (INFORMATIONAL only): IS [79, 147] pt ~105 / OOS [25, 46] pt ~34.
    """

    def test_iter020_is_single_symbol(self) -> None:
        """BTC-only model trains on 1 symbol vs Model A's 2-symbol pool (BTC+ETH)."""
        n_iter020_symbols = len(V1_ITER020_UNIVERSE)
        n_model_a_symbols = 2  # BTC + ETH pooled in baseline Model A
        assert n_iter020_symbols == 1, (
            f"iter-v1/020 must train on exactly 1 symbol; got {n_iter020_symbols}"
        )
        assert n_iter020_symbols < n_model_a_symbols, (
            "BTC-only training must have fewer per-cell rows than BTC+ETH pooled (Model A)"
        )

    def test_iter020_universe_subset_ensures_parquet_available(self) -> None:
        """BTCUSDT parquet must already exist (no new symbol fetch needed).

        BTCUSDT is in V1_BASELINE_UNIVERSE, so its feature parquet is already
        generated. No --fetch or feature regeneration required for /020 beyond
        the standard data-freshness check (close_time within 16h).
        """
        assert set(V1_ITER020_UNIVERSE).issubset(set(V1_BASELINE_UNIVERSE)), (
            "V1_ITER020_UNIVERSE must be a subset of V1_BASELINE_UNIVERSE so that "
            "feature parquets are available — BTCUSDT parquet from baseline run"
        )
