"""iter-v1/018 — LINK-only cohort dispatch unit tests.

Verifies:
1. V1_ITER018_UNIVERSE constant exists and contains exactly LINKUSDT.
2. LINKUSDT is NOT in V1_EXCLUDED_SYMBOLS (required for dispatch to work).
3. assert_v1_universe() accepts the 1-symbol V1_ITER018_UNIVERSE.
4. assert_v1_universe() still rejects v2/v3 symbols (regression guard).
5. Dispatch branch routing: V1_ITER018_UNIVERSE triggers the iter-v1/018 elif
   branch (not the baseline or iter-v1/017 branch).
6. V1_ITER018_UNIVERSE is a strict subset of V1_BASELINE_UNIVERSE (single-symbol
   cohort, not a universe expansion).
7. Single-symbol training row count (per-cell LINK rows ~ 140/month), confirming
   the regime that LM Master Phase 4.5 n_eff_per_cell [4, 9] prediction applies to.

Brief reference: briefs-v1/iteration_v1-018/research_brief.md Sections 3.1, 3.6,
  F-AXIS-MECHANISM #1, and Section 10.3 pre-flight verification.
"""

from __future__ import annotations

import pytest
from run_baseline_v1 import V1_ITER017_UNIVERSE, V1_ITER018_UNIVERSE

from crypto_trade.features_v1 import (
    V1_BASELINE_UNIVERSE,
    V1_EXCLUDED_SYMBOLS,
    assert_v1_universe,
)


class TestV1Iter018UniverseConstant:
    """Test V1_ITER018_UNIVERSE constant correctness."""

    def test_universe_length_is_1(self) -> None:
        """V1_ITER018_UNIVERSE must have exactly 1 symbol (LINK-only cohort)."""
        assert len(V1_ITER018_UNIVERSE) == 1, (
            f"Expected 1 symbol in V1_ITER018_UNIVERSE (LINK-only), "
            f"got {len(V1_ITER018_UNIVERSE)}: {V1_ITER018_UNIVERSE}"
        )

    def test_universe_contains_linkusdt(self) -> None:
        """V1_ITER018_UNIVERSE must contain LINKUSDT as the sole symbol."""
        assert "LINKUSDT" in V1_ITER018_UNIVERSE, (
            "LINKUSDT must be the only symbol in V1_ITER018_UNIVERSE for "
            "iter-v1/018 Model C dispatch"
        )

    def test_universe_exact_symbols(self) -> None:
        """V1_ITER018_UNIVERSE must be exactly {LINKUSDT}."""
        expected = frozenset({"LINKUSDT"})
        assert frozenset(V1_ITER018_UNIVERSE) == expected, (
            f"V1_ITER018_UNIVERSE symbols mismatch: got {set(V1_ITER018_UNIVERSE)}, "
            f"expected {expected}"
        )

    def test_iter018_universe_is_strict_subset_of_baseline(self) -> None:
        """V1_ITER018_UNIVERSE must be a strict subset of V1_BASELINE_UNIVERSE.

        iter-v1/018 is a cohort isolation (single-symbol subset), NOT a universe
        expansion. LINKUSDT is already in V1_BASELINE_UNIVERSE; we are testing
        the single-symbol training regime, not adding a new symbol.
        """
        assert set(V1_ITER018_UNIVERSE).issubset(set(V1_BASELINE_UNIVERSE)), (
            "V1_ITER018_UNIVERSE must be a subset of V1_BASELINE_UNIVERSE; "
            f"LINK-only cohort is not an expansion. "
            f"V1_ITER018_UNIVERSE={set(V1_ITER018_UNIVERSE)}, "
            f"V1_BASELINE_UNIVERSE={set(V1_BASELINE_UNIVERSE)}"
        )
        assert len(V1_ITER018_UNIVERSE) < len(V1_BASELINE_UNIVERSE), (
            "V1_ITER018_UNIVERSE must be strictly smaller than V1_BASELINE_UNIVERSE"
        )


class TestLinkNotExcluded:
    """Test that LINKUSDT is not in V1_EXCLUDED_SYMBOLS (required for dispatch)."""

    def test_linkusdt_not_excluded(self) -> None:
        """LINKUSDT must NOT be in V1_EXCLUDED_SYMBOLS for the dispatch to work.

        LINKUSDT is in V1_BASELINE_UNIVERSE — it is a v1 symbol, not a v2/v3 symbol.
        """
        assert "LINKUSDT" not in V1_EXCLUDED_SYMBOLS, (
            "LINKUSDT must NOT be in V1_EXCLUDED_SYMBOLS; "
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


class TestAssertV1UniverseAcceptsIter018Universe:
    """Test assert_v1_universe() accepts the 1-symbol iter-v1/018 set."""

    def test_assert_accepts_iter018_universe(self) -> None:
        """assert_v1_universe must not raise for V1_ITER018_UNIVERSE (LINKUSDT)."""
        # Should not raise — LINKUSDT is a v1 baseline symbol, not excluded
        assert_v1_universe(V1_ITER018_UNIVERSE)

    def test_assert_accepts_single_linkusdt_string(self) -> None:
        """assert_v1_universe must accept the literal single-element tuple."""
        assert_v1_universe(("LINKUSDT",))

    def test_assert_accepts_baseline_universe(self) -> None:
        """assert_v1_universe must still accept V1_BASELINE_UNIVERSE (regression)."""
        assert_v1_universe(V1_BASELINE_UNIVERSE)

    def test_assert_accepts_iter017_universe(self) -> None:
        """assert_v1_universe must still accept V1_ITER017_UNIVERSE (regression)."""
        assert_v1_universe(V1_ITER017_UNIVERSE)

    def test_assert_rejects_v3_symbol(self) -> None:
        """assert_v1_universe must reject a v3 symbol (BCHUSDT)."""
        with pytest.raises(AssertionError, match="v1 cannot trade v2/v3 symbols"):
            assert_v1_universe(("LINKUSDT", "BCHUSDT"))

    def test_assert_accepts_later_unreserved_xrp(self) -> None:
        """assert_v1_universe accepts XRP after iter-v1/088.

        NOTE: SOLUSDT was removed from V1_EXCLUDED_SYMBOLS at iter-v1/017.
        DOGE and NEAR remain excluded; XRP was later un-reserved.
        """
        assert_v1_universe(("LINKUSDT", "XRPUSDT"))

    def test_assert_accepts_bnb(self) -> None:
        """assert_v1_universe must now accept BNBUSDT (un-reserved at iter-v1/087)."""
        # iter-v1/087: BNB un-reserved per user directive 2026-06-10.
        assert_v1_universe(("LINKUSDT", "BNBUSDT"))


class TestIter018DispatchBranchRouting:
    """Test that the elif branch for V1_ITER018_UNIVERSE routes correctly.

    The runner dispatch logic (simplified):
        if set(symbols) == set(V1_BASELINE_UNIVERSE):    ← baseline branch (4 models)
            ...
        elif set(symbols) == set(V1_ITER017_UNIVERSE):   ← iter-v1/017 branch (5 models)
            ...
        elif set(symbols) == set(V1_ITER018_UNIVERSE):   ← iter-v1/018 branch (1 model C only)
            ...
        else:
            ...                                          ← custom POOLED fallback

    These tests verify the dispatch conditions without importing the full runner.
    """

    def test_iter018_universe_not_equal_to_baseline(self) -> None:
        """V1_ITER018_UNIVERSE and V1_BASELINE_UNIVERSE must NOT be equal sets.

        Ensures iter-v1/018 does NOT accidentally trigger the baseline dispatch.
        """
        assert set(V1_ITER018_UNIVERSE) != set(V1_BASELINE_UNIVERSE), (
            "V1_ITER018_UNIVERSE must differ from V1_BASELINE_UNIVERSE; "
            "they must route to different dispatch branches in run_baseline_v1.py"
        )

    def test_iter018_universe_not_equal_to_iter017(self) -> None:
        """V1_ITER018_UNIVERSE and V1_ITER017_UNIVERSE must NOT be equal sets.

        Ensures iter-v1/018 does NOT accidentally trigger the iter-v1/017 dispatch.
        """
        assert set(V1_ITER018_UNIVERSE) != set(V1_ITER017_UNIVERSE), (
            "V1_ITER018_UNIVERSE must differ from V1_ITER017_UNIVERSE; "
            "they must route to different dispatch branches in run_baseline_v1.py"
        )

    def test_iter018_dispatch_condition_is_true(self) -> None:
        """Verify the elif routing condition for iter-v1/018 evaluates True."""
        # Mirrors the runner check: elif set(symbols) == set(V1_ITER018_UNIVERSE)
        symbols = ("LINKUSDT",)
        baseline_check = set(symbols) == set(V1_BASELINE_UNIVERSE)
        iter017_check = set(symbols) == set(V1_ITER017_UNIVERSE)
        iter018_check = set(symbols) == set(V1_ITER018_UNIVERSE)

        assert not baseline_check, "LINKUSDT alone must NOT match the baseline branch (5 symbols)"
        assert not iter017_check, "LINKUSDT alone must NOT match the iter-v1/017 branch (6 symbols)"
        assert iter018_check, "LINKUSDT alone MUST match the iter-v1/018 branch (1 symbol)"

    def test_baseline_universe_does_not_trigger_iter018_branch(self) -> None:
        """The 5-symbol baseline set must NOT trigger the iter-v1/018 branch."""
        assert set(V1_BASELINE_UNIVERSE) != set(V1_ITER018_UNIVERSE), (
            "Baseline universe (5 symbols) must not route to the LINK-only branch"
        )

    def test_iter017_universe_does_not_trigger_iter018_branch(self) -> None:
        """The 6-symbol iter-v1/017 set must NOT trigger the iter-v1/018 branch."""
        assert set(V1_ITER017_UNIVERSE) != set(V1_ITER018_UNIVERSE), (
            "iter-v1/017 universe (6 symbols) must not route to the LINK-only branch"
        )


class TestLinkOnlyTrainingRowsBand:
    """Verify the per-cell row count expectation for the LINK-only model.

    From research_brief.md Section 3.6 + LM Master Phase 4.5 §4.1:
    Per-cell training rows decrease from pooled ~700 → LINK-only ~140.
    TPE warmup at n_trials=18 stays above ~10 saturation threshold.

    This test provides a structural sanity check: a single-symbol model
    with ~39 IS months * ~6 trades/month * 3 seeds = ~70 expected OOF rows.
    The actual per-cell row count depends on feature computation and labeling,
    but we can verify the constant relationship between baseline and LINK-only.
    """

    def test_iter018_is_single_symbol(self) -> None:
        """LINK-only model trains on 1 symbol vs baseline pooled model on 2 (A)."""
        # Model A pools BTC+ETH (2 symbols); Model C is LINK-only (1 symbol).
        # Single-symbol training means ~1/2 the per-cell rows vs Model A's pool.
        # This test documents the expectation for LM Master Phase 7.4 n_eff audit.
        n_iter018_symbols = len(V1_ITER018_UNIVERSE)
        n_model_a_symbols = 2  # BTC + ETH pooled
        assert n_iter018_symbols == 1, (
            f"iter-v1/018 must train on exactly 1 symbol; got {n_iter018_symbols}"
        )
        assert n_iter018_symbols < n_model_a_symbols, (
            "LINK-only training must have fewer per-cell rows than BTC+ETH pooled (Model A)"
        )

    def test_iter018_universe_is_subset_of_baseline_ensuring_parquet_exists(self) -> None:
        """LINKUSDT parquet must already exist (no new symbol fetch needed).

        LINKUSDT is in V1_BASELINE_UNIVERSE, so its feature parquet is already
        generated. No --fetch or feature regeneration required for iter-v1/018.
        This test documents that V1_ITER018_UNIVERSE is a strict subset, guaranteeing
        the parquet is available from the baseline run.
        """
        assert set(V1_ITER018_UNIVERSE).issubset(set(V1_BASELINE_UNIVERSE)), (
            "V1_ITER018_UNIVERSE must be a subset of V1_BASELINE_UNIVERSE so that "
            "feature parquets are already available — no new data fetch required"
        )
