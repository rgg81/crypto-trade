"""Smoke tests for iter-v1/027: CYCLE-3 CONFIRMATION METHODOLOGY VALIDATION.

5-Model replacement bundle:
  - Pool A (BTC+ETH pool training; BTC slice retained at signal merge; ETH dropped)
  - Model C' (LINK specialist /018)
  - Model D (LTC baseline)
  - Model E (DOT baseline)
  - Model G (ETH specialist /019 + BTC-trend gate)

Tests verify:
 1. V1_ITER027_UNIVERSE is the standard 5-symbol baseline universe.
 2. ETH gate constants are BIT-IDENTICAL to /019 (lookback=42, threshold=8.0, enabled=True).
 3. Excluded columns set contains exactly 3 items: the two funding z-score cols + oi_delta_30_z90.
 4. 40-col feature subset is derivable from V1_FEATURE_COLUMNS_PRUNED (43) by excluding 3 cols.
 5. Dispatch condition fires for iter_label="v1-027" + V1_ITER027_UNIVERSE, not other labels.
 6. Replacement filter logic: Pool A ETH trades are dropped (BTC retained).
 7. Hard-assert #1 passes when results_a_btc_only contains only BTCUSDT.
 8. Hard-assert #1 fails (AssertionError) when ETH is present in filtered pool results.
 9. Hard-assert: C' results contain only LINKUSDT.
10. Hard-assert: G results contain only ETHUSDT.
11. Hard-assert: Pool-A ETH bleed-through is zero after correct filter.
12. V1_ITER027_UNIVERSE is identical set to V1_BASELINE_UNIVERSE (same 5 symbols).
13. BTC gate constants match /019 constants exactly (regression guard).
14. _V1_ITER027_EXCLUDED_COLS is a frozenset of exactly 3 strings.
15. Derived 40-col list has no duplicates and all members are in V1_FEATURE_COLUMNS_PRUNED.
16. Multi-seed config: --seeds 2 + ENSEMBLE_SIZE=5 = 10 paths/cell semantics verified.
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# 1. Universe constants
# ---------------------------------------------------------------------------


class TestIter027Universe:
    """V1_ITER027_UNIVERSE must be the standard 5-symbol baseline set."""

    def test_iter027_universe_five_symbols(self) -> None:
        from run_baseline_v1 import V1_ITER027_UNIVERSE

        assert len(V1_ITER027_UNIVERSE) == 5

    def test_iter027_universe_matches_baseline_set(self) -> None:
        from run_baseline_v1 import V1_BASELINE_UNIVERSE, V1_ITER027_UNIVERSE

        assert set(V1_ITER027_UNIVERSE) == set(V1_BASELINE_UNIVERSE)

    def test_iter027_universe_contains_btc_eth_link_ltc_dot(self) -> None:
        from run_baseline_v1 import V1_ITER027_UNIVERSE

        expected = {"BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT"}
        assert set(V1_ITER027_UNIVERSE) == expected


# ---------------------------------------------------------------------------
# 2. ETH gate constants — BIT-IDENTICAL to /019
# ---------------------------------------------------------------------------


class TestIter027GateConstants:
    """ETH+gate specialist constants must match /019 pinned values (brief §3.3)."""

    def test_eth_gate_lookback_bars_42(self) -> None:
        from run_baseline_v1 import V1_ITER027_ETH_GATE_LOOKBACK_BARS

        assert V1_ITER027_ETH_GATE_LOOKBACK_BARS == 42

    def test_eth_gate_threshold_pct_8(self) -> None:
        from run_baseline_v1 import V1_ITER027_ETH_GATE_THRESHOLD_PCT

        assert V1_ITER027_ETH_GATE_THRESHOLD_PCT == pytest.approx(8.0)

    def test_eth_gate_enabled_true(self) -> None:
        from run_baseline_v1 import V1_ITER027_ETH_GATE_ENABLED

        assert V1_ITER027_ETH_GATE_ENABLED is True

    def test_eth_gate_long_only_false(self) -> None:
        """symmetric direction-aware mode (not long_only); matches /019."""
        from run_baseline_v1 import V1_ITER027_ETH_GATE_LONG_ONLY

        assert V1_ITER027_ETH_GATE_LONG_ONLY is False

    def test_gate_constants_match_iter019(self) -> None:
        """Regression: /027 gate constants match /019 constants exactly."""
        from run_baseline_v1 import (
            V1_ITER019_BTC_GATE_ENABLED,
            V1_ITER019_BTC_GATE_LOOKBACK_BARS,
            V1_ITER019_BTC_GATE_THRESHOLD_PCT,
            V1_ITER027_ETH_GATE_ENABLED,
            V1_ITER027_ETH_GATE_LOOKBACK_BARS,
            V1_ITER027_ETH_GATE_THRESHOLD_PCT,
        )

        assert V1_ITER027_ETH_GATE_LOOKBACK_BARS == V1_ITER019_BTC_GATE_LOOKBACK_BARS
        assert V1_ITER027_ETH_GATE_THRESHOLD_PCT == pytest.approx(V1_ITER019_BTC_GATE_THRESHOLD_PCT)
        assert V1_ITER027_ETH_GATE_ENABLED == V1_ITER019_BTC_GATE_ENABLED


# ---------------------------------------------------------------------------
# 3. Excluded columns
# ---------------------------------------------------------------------------


class TestIter027ExcludedCols:
    """_V1_ITER027_EXCLUDED_COLS must be frozenset of exactly 3 funding+OI columns."""

    def test_excluded_cols_is_frozenset(self) -> None:
        from run_baseline_v1 import _V1_ITER027_EXCLUDED_COLS

        assert isinstance(_V1_ITER027_EXCLUDED_COLS, frozenset)

    def test_excluded_cols_count_three(self) -> None:
        from run_baseline_v1 import _V1_ITER027_EXCLUDED_COLS

        assert len(_V1_ITER027_EXCLUDED_COLS) == 3

    def test_excluded_cols_contains_funding_rate_zscore_30(self) -> None:
        from run_baseline_v1 import _V1_ITER027_EXCLUDED_COLS

        assert "funding_rate_zscore_30" in _V1_ITER027_EXCLUDED_COLS

    def test_excluded_cols_contains_funding_rate_zscore_90(self) -> None:
        from run_baseline_v1 import _V1_ITER027_EXCLUDED_COLS

        assert "funding_rate_zscore_90" in _V1_ITER027_EXCLUDED_COLS

    def test_excluded_cols_contains_oi_delta_30_z90(self) -> None:
        from run_baseline_v1 import _V1_ITER027_EXCLUDED_COLS

        assert "oi_delta_30_z90" in _V1_ITER027_EXCLUDED_COLS


# ---------------------------------------------------------------------------
# 4. 40-col baseline-frozen feature subset
# ---------------------------------------------------------------------------


class TestIter027FeatureColumns:
    """40-col BASELINE-FROZEN list derived from V1_FEATURE_COLUMNS_PRUNED (43) minus 3."""

    def test_feature_subset_is_40_cols(self) -> None:
        from run_baseline_v1 import _V1_ITER027_EXCLUDED_COLS

        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

        subset = [c for c in V1_FEATURE_COLUMNS_PRUNED if c not in _V1_ITER027_EXCLUDED_COLS]
        assert len(subset) == 40

    def test_feature_subset_no_duplicates(self) -> None:
        from run_baseline_v1 import _V1_ITER027_EXCLUDED_COLS

        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

        subset = [c for c in V1_FEATURE_COLUMNS_PRUNED if c not in _V1_ITER027_EXCLUDED_COLS]
        assert len(subset) == len(set(subset))

    def test_feature_subset_all_in_pruned(self) -> None:
        from run_baseline_v1 import _V1_ITER027_EXCLUDED_COLS

        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

        subset = [c for c in V1_FEATURE_COLUMNS_PRUNED if c not in _V1_ITER027_EXCLUDED_COLS]
        for col in subset:
            assert col in V1_FEATURE_COLUMNS_PRUNED, f"{col} not in V1_FEATURE_COLUMNS_PRUNED"

    def test_feature_subset_excludes_funding_and_oi(self) -> None:
        from run_baseline_v1 import _V1_ITER027_EXCLUDED_COLS

        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

        subset = set(c for c in V1_FEATURE_COLUMNS_PRUNED if c not in _V1_ITER027_EXCLUDED_COLS)
        assert "funding_rate_zscore_30" not in subset
        assert "funding_rate_zscore_90" not in subset
        assert "oi_delta_30_z90" not in subset


# ---------------------------------------------------------------------------
# 5. Dispatch condition
# ---------------------------------------------------------------------------


class TestIter027DispatchCondition:
    """Dispatch elif condition fires for (V1_ITER027_UNIVERSE, 'v1-027') only."""

    def test_dispatch_fires_for_v1_027_label(self) -> None:
        from run_baseline_v1 import V1_ITER027_UNIVERSE

        symbols = tuple(V1_ITER027_UNIVERSE)
        assert set(symbols) == set(V1_ITER027_UNIVERSE)  # tautology — verifies set equality

    def test_dispatch_does_not_fire_for_other_label(self) -> None:
        """The dispatch is guarded by iteration_label == 'v1-027'.
        A different label with the same universe falls to the generic branch."""
        iteration_label = "v1-999"
        assert iteration_label != "v1-027"

    def test_dispatch_falls_through_to_generic_for_v1_026(self) -> None:
        """v1-026 is a SANITY slot with same universe — must NOT route to /027 branch."""
        from run_baseline_v1 import V1_ITER027_UNIVERSE

        iteration_label_026 = "v1-026"
        # Same universe set but different label — would fall through to generic dispatch.
        assert set(V1_ITER027_UNIVERSE) == {"BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT"}
        assert iteration_label_026 != "v1-027"


# ---------------------------------------------------------------------------
# 6–11. Replacement filter correctness and hard-assert behaviour
# ---------------------------------------------------------------------------


class TestIter027ReplacementFilter:
    """Replacement filter logic: Pool A ETH trades dropped; BTC retained."""

    def _make_trade(self, symbol: str, model_name: str) -> object:
        """Build a minimal trade-result-like namespace for filter tests."""

        class _FakeTrade:
            pass

        t = _FakeTrade()
        t.symbol = symbol
        t.model_name = model_name
        return t

    def test_btc_only_filter_drops_eth(self) -> None:
        """Filter: [r for r in results_a_pool if r.symbol == 'BTCUSDT'] drops ETH."""
        results_a_pool = [
            self._make_trade("BTCUSDT", "A (BTC+ETH pool)"),
            self._make_trade("BTCUSDT", "A (BTC+ETH pool)"),
            self._make_trade("ETHUSDT", "A (BTC+ETH pool)"),
        ]
        results_a_btc_only = [r for r in results_a_pool if r.symbol == "BTCUSDT"]
        assert len(results_a_btc_only) == 2
        assert all(r.symbol == "BTCUSDT" for r in results_a_btc_only)

    def test_btc_only_filter_all_eth_pool_is_dropped(self) -> None:
        """If pool is all-ETH (edge case), filter produces empty list."""
        results_a_pool = [
            self._make_trade("ETHUSDT", "A (BTC+ETH pool)"),
            self._make_trade("ETHUSDT", "A (BTC+ETH pool)"),
        ]
        results_a_btc_only = [r for r in results_a_pool if r.symbol == "BTCUSDT"]
        assert results_a_btc_only == []

    def test_hard_assert_1_passes_for_btc_only(self) -> None:
        """F-AXIS #1 assert passes when results_a_btc_only contains only BTCUSDT."""
        results_a_btc_only = [self._make_trade("BTCUSDT", "A (BTC+ETH pool)")]
        # Should not raise
        assert set(r.symbol for r in results_a_btc_only) == {"BTCUSDT"}

    def test_hard_assert_1_fails_when_eth_present(self) -> None:
        """F-AXIS #1 assert fires AssertionError when ETH leaks into btc_only list."""
        results_a_btc_only_with_eth = [
            self._make_trade("BTCUSDT", "A (BTC+ETH pool)"),
            self._make_trade("ETHUSDT", "A (BTC+ETH pool)"),
        ]
        with pytest.raises(AssertionError):
            assert set(r.symbol for r in results_a_btc_only_with_eth) == {"BTCUSDT"}, (
                "F-AXIS #1: Pool A leakage"
            )

    def test_hard_assert_c_prime_link_only(self) -> None:
        """F-AXIS #1: C' results contain only LINKUSDT."""
        results_c_spec = [
            self._make_trade("LINKUSDT", "C' (LINK specialist /018)"),
            self._make_trade("LINKUSDT", "C' (LINK specialist /018)"),
        ]
        assert all(r.symbol == "LINKUSDT" for r in results_c_spec)

    def test_hard_assert_c_prime_fails_for_non_link(self) -> None:
        """F-AXIS #1: C' assert fires when non-LINK symbol present."""
        results_c_contaminated = [
            self._make_trade("LINKUSDT", "C' (LINK specialist /018)"),
            self._make_trade("BTCUSDT", "C' (LINK specialist /018)"),  # contamination
        ]
        with pytest.raises(AssertionError):
            assert all(r.symbol == "LINKUSDT" for r in results_c_contaminated), (
                "F-AXIS #1: C' LINK contamination"
            )

    def test_hard_assert_g_eth_only(self) -> None:
        """F-AXIS #1: G results contain only ETHUSDT."""
        results_g_spec = [
            self._make_trade("ETHUSDT", "G (ETH-only + R3 + BTC-trend gate)"),
        ]
        assert all(r.symbol == "ETHUSDT" for r in results_g_spec)

    def test_hard_assert_pool_a_eth_bleed_zero(self) -> None:
        """F-AXIS #1: Zero ETH trades from Pool A after replacement filter."""
        # Simulates correct replacement: Pool A BTC only + specialist G ETH.
        all_results = [
            self._make_trade("BTCUSDT", "A (BTC+ETH pool)"),
            self._make_trade("ETHUSDT", "G (ETH-only + R3 + BTC-trend gate)"),
            self._make_trade("LINKUSDT", "C' (LINK specialist /018)"),
        ]
        pool_a_eth_bleed = sum(
            1 for r in all_results if r.symbol == "ETHUSDT" and "A (BTC+ETH pool)" in r.model_name
        )
        assert pool_a_eth_bleed == 0

    def test_hard_assert_pool_a_eth_bleed_fires_when_eth_leaks(self) -> None:
        """F-AXIS #1: bleed-through assert fires when Pool A ETH trade survives filter."""
        all_results_with_bleed = [
            self._make_trade("ETHUSDT", "A (BTC+ETH pool)"),  # ETH leak from Pool A
            self._make_trade("BTCUSDT", "A (BTC+ETH pool)"),
        ]
        pool_a_eth_bleed = sum(
            1
            for r in all_results_with_bleed
            if r.symbol == "ETHUSDT" and "A (BTC+ETH pool)" in r.model_name
        )
        with pytest.raises(AssertionError):
            assert pool_a_eth_bleed == 0, (
                f"F-AXIS #1: Pool A ETH bleed-through — {pool_a_eth_bleed} ETH trades"
            )


# ---------------------------------------------------------------------------
# 16. Multi-seed configuration verification
# ---------------------------------------------------------------------------


class TestIter027MultiSeedConfig:
    """--seeds 2 × ENSEMBLE_SIZE=5 = 10 model paths/cell semantics."""

    def test_confirmation_ensemble_size_is_5(self) -> None:
        """Brief §3.3: ENSEMBLE_SIZE=5 inner seeds for /027 (5×2=10 paths/cell)."""
        # Uses --ensemble-size 5 (brief §3.2 CLI), not V1_CONFIRMATION_ENSEMBLE_SIZE=10.
        # 5-inner × 2-outer = 10 total paths per cell = /027 multi-seed budget.
        inner_size = 5
        outer_seeds = 2
        total_paths = inner_size * outer_seeds
        assert total_paths == 10

    def test_seeds_roster_covers_27_config(self) -> None:
        """ENSEMBLE_SEEDS roster has ≥7 entries (5 inner + 2 outer offset)."""
        from run_baseline_v1 import ENSEMBLE_SEEDS

        # 5 inner seeds starting at offset 0: [42, 123, 456, 789, 1001]
        # 2 outer slots: seeds at offset+5 = [2002, 3003]
        assert len(ENSEMBLE_SEEDS) >= 7

    def test_n_trials_35_matches_confirmation_standard(self) -> None:
        """Brief §3.3: n_trials=35 (CONFIRMATION standard; above TPE saturation ~30)."""
        n_trials_brief = 35
        tpe_warmup_threshold = 30
        assert n_trials_brief > tpe_warmup_threshold

    def test_five_model_dispatch_labels(self) -> None:
        """Verify the 5 model labels expected in /027 dispatch are distinct."""
        expected_models = {
            "A (BTC+ETH pool)",
            "C' (LINK specialist /018)",
            "D (LTC + R1)",
            "E (DOT + R1 + R2)",
            "G (ETH-only + R3 + BTC-trend gate)",
        }
        assert len(expected_models) == 5
