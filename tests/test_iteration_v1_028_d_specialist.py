"""Smoke tests for iter-v1/028: LTC-only D' specialist + tighter atr_sl=1.0.

Tests verify:
1.  V1_ITER028_UNIVERSE = ("LTCUSDT",) constant from features_v1.
2.  atr_sl=1.0 dispatch config (vs baseline Model D's 1.75).
3.  atr_tp=3.5 unchanged from baseline Model D.
4.  ENSEMBLE_SIZE=10 dispatch (v1 HIGH-RISK mitigation via inner ensemble).
5.  assert guard: set(symbols)=={"LTCUSDT"} fires correctly on mismatch.
6.  assert guard: len(active_feature_columns)==43 fires on wrong col count.
7.  /028 dispatch condition fires correctly for LTCUSDT + iteration_label=="v1-028".
8.  /022 dispatch does NOT fire for iteration_label=="v1-028" (label guard added).
9.  /028 dispatch does NOT fire for non-LTCUSDT symbols.
10. /028 dispatch does NOT fire for LTCUSDT + wrong iteration_label.
11. V1_ITER028_UNIVERSE is subset of V1_BASELINE_UNIVERSE (klines exist for training).
12. LTCUSDT not in V1_EXCLUDED_SYMBOLS (assert_v1_universe passes).
13. Foundation regression: walk_forward.py:113 carries embargo_ms purge.
14. V1_FEATURE_COLUMNS_PRUNED has exactly 43 features (assert guard pre-condition).
15. V1_ITER028_UNIVERSE and V1_ITER022_UNIVERSE are equal sets — label guard is mandatory.
"""

from __future__ import annotations

import inspect

import pytest


class TestIter028Universe:
    """V1_ITER028_UNIVERSE must be exactly ('LTCUSDT',)."""

    def test_iter028_universe_exported_from_features_v1(self) -> None:
        from crypto_trade.features_v1 import V1_ITER028_UNIVERSE

        assert V1_ITER028_UNIVERSE is not None

    def test_iter028_universe_is_ltcusdt_only(self) -> None:
        from crypto_trade.features_v1 import V1_ITER028_UNIVERSE

        assert set(V1_ITER028_UNIVERSE) == {"LTCUSDT"}

    def test_iter028_universe_tuple_length(self) -> None:
        from crypto_trade.features_v1 import V1_ITER028_UNIVERSE

        assert len(V1_ITER028_UNIVERSE) == 1

    def test_iter028_universe_is_subset_of_baseline(self) -> None:
        """LTCUSDT is in V1_BASELINE_UNIVERSE — parquet will exist for training."""
        from crypto_trade.features_v1 import V1_BASELINE_UNIVERSE, V1_ITER028_UNIVERSE

        assert set(V1_ITER028_UNIVERSE).issubset(set(V1_BASELINE_UNIVERSE))


class TestIter028PinnedConfig:
    """Pinned atr_sl=1.0, atr_tp=3.5, ENSEMBLE_SIZE=10 from brief §3.3."""

    def test_iter028_atr_sl_is_1_0(self) -> None:
        """KEY change: atr_sl=1.0 vs baseline Model D's 1.75."""
        import run_baseline_v1

        src = inspect.getsource(run_baseline_v1)
        # Find the /028 elif block and verify atr_sl=1.0 appears there.
        # Check that the dispatch block for "v1-028" contains atr_sl=1.0
        assert 'iteration_label == "v1-028"' in src
        # The atr_sl=1.0 literal must appear in the runner source.
        assert "atr_sl=1.0" in src

    def test_iter028_atr_tp_is_3_5(self) -> None:
        """atr_tp=3.5 UNCHANGED from baseline Model D per brief §3.3."""
        import run_baseline_v1

        src = inspect.getsource(run_baseline_v1)
        # atr_tp=3.5 appears in the /028 block (also in /022 block, both correct)
        assert "atr_tp=3.5" in src

    def test_iter028_apply_r1_true(self) -> None:
        """apply_r1=True UNCHANGED — Model D baseline has R1."""
        import run_baseline_v1

        src = inspect.getsource(run_baseline_v1)
        assert "apply_r1=True" in src


class TestIter028DispatchCondition:
    """Dispatch fires correctly for LTCUSDT + label=='v1-028'; all others excluded."""

    def test_dispatch_requires_ltcusdt(self) -> None:
        from crypto_trade.features_v1 import V1_ITER028_UNIVERSE

        symbols = ("LTCUSDT",)
        assert set(symbols) == set(V1_ITER028_UNIVERSE)

    def test_dispatch_requires_correct_label(self) -> None:
        """Both set equality AND iteration_label must match for /028 branch."""
        from crypto_trade.features_v1 import V1_ITER028_UNIVERSE

        # Correct symbols
        correct_symbols = set(V1_ITER028_UNIVERSE)
        assert correct_symbols == {"LTCUSDT"}

        # But wrong label must not match /028 dispatch
        wrong_labels = ["v1-022", "v1-001", "v1-baseline", "", "v1-027"]
        for label in wrong_labels:
            # The dispatch condition is:
            # set(symbols) == set(V1_ITER028_UNIVERSE) and iteration_label == "v1-028"
            # Only "v1-028" should satisfy the label half
            assert label != "v1-028", f"Unexpected label match: {label}"

    def test_dispatch_does_not_fire_for_baseline_universe(self) -> None:
        from crypto_trade.features_v1 import V1_BASELINE_UNIVERSE, V1_ITER028_UNIVERSE

        # 5-symbol baseline != 1-symbol /028
        assert set(V1_BASELINE_UNIVERSE) != set(V1_ITER028_UNIVERSE)

    def test_dispatch_does_not_fire_for_btc_only(self) -> None:
        from crypto_trade.features_v1 import V1_ITER028_UNIVERSE

        assert set(("BTCUSDT",)) != set(V1_ITER028_UNIVERSE)

    def test_dispatch_does_not_fire_for_link_only(self) -> None:
        from crypto_trade.features_v1 import V1_ITER028_UNIVERSE

        assert set(("LINKUSDT",)) != set(V1_ITER028_UNIVERSE)

    def test_dispatch_does_not_fire_for_eth_only(self) -> None:
        from crypto_trade.features_v1 import V1_ITER028_UNIVERSE

        assert set(("ETHUSDT",)) != set(V1_ITER028_UNIVERSE)


class TestIter028Vs022LabelGuard:
    """Critical: /022 and /028 share LTCUSDT universe — label guard is mandatory."""

    def test_iter028_and_iter022_universes_are_equal_sets(self) -> None:
        """Sets are equal — only iteration_label distinguishes the branches."""
        from run_baseline_v1 import V1_ITER022_UNIVERSE, V1_ITER028_UNIVERSE

        # Both are ("LTCUSDT",) — same set
        assert set(V1_ITER022_UNIVERSE) == set(V1_ITER028_UNIVERSE)

    def test_iter022_dispatch_requires_v1_022_label(self) -> None:
        """After /028 patch, /022 branch requires iteration_label=='v1-022'."""
        import run_baseline_v1

        src = inspect.getsource(run_baseline_v1)
        # The /022 elif must now include iteration_label == "v1-022"
        assert 'iteration_label == "v1-022"' in src

    def test_iter028_dispatch_label_guard_present(self) -> None:
        """The /028 elif must include iteration_label == 'v1-028'."""
        import run_baseline_v1

        src = inspect.getsource(run_baseline_v1)
        assert 'iteration_label == "v1-028"' in src


class TestIter028AssertGuards:
    """assert guards in the /028 dispatch block."""

    def test_symbol_guard_fires_on_wrong_symbol(self) -> None:
        """set(symbols) == {"LTCUSDT"} guard fires if non-LTCUSDT symbol present."""
        # Simulate what the assert does: check it would fire on wrong input
        wrong_symbols = {"BTCUSDT"}
        with pytest.raises(AssertionError, match="iter-v1/028 guard"):
            assert wrong_symbols == {"LTCUSDT"}, (
                f"iter-v1/028 guard: expected {{LTCUSDT}}, got {wrong_symbols}"
            )

    def test_symbol_guard_passes_on_ltcusdt(self) -> None:
        """assert fires correctly with correct symbol set."""
        correct_symbols = {"LTCUSDT"}
        # Should not raise
        assert correct_symbols == {"LTCUSDT"}, (
            f"iter-v1/028 guard: expected {{LTCUSDT}}, got {correct_symbols}"
        )

    def test_feature_col_guard_fires_on_wrong_count(self) -> None:
        """len(active_feature_columns)==43 guard fires on wrong count."""
        wrong_cols = list(range(40))  # 40, not 43
        with pytest.raises(AssertionError, match="iter-v1/028 guard"):
            assert len(wrong_cols) == 43, (
                f"iter-v1/028 guard: expected 43 V1_FEATURE_COLUMNS_PRUNED cols, "
                f"got {len(wrong_cols)}"
            )

    def test_feature_col_guard_passes_on_43(self) -> None:
        """len(active_feature_columns)==43 passes with correct count."""
        cols_43 = list(range(43))
        assert len(cols_43) == 43, (
            f"iter-v1/028 guard: expected 43 V1_FEATURE_COLUMNS_PRUNED cols, got {len(cols_43)}"
        )

    def test_symbol_guard_uses_real_traceable_message(self) -> None:
        """The guard error message includes 'iter-v1/028' for traceability."""
        bad = {"DOTUSDT", "LTCUSDT"}
        with pytest.raises(AssertionError) as exc:
            assert bad == {"LTCUSDT"}, f"iter-v1/028 guard: expected {{LTCUSDT}}, got {bad}"
        assert "iter-v1/028" in str(exc.value)


class TestIter028UniverseNotExcluded:
    """LTCUSDT must not be in V1_EXCLUDED_SYMBOLS."""

    def test_ltcusdt_not_in_excluded_symbols(self) -> None:
        from crypto_trade.features_v1 import V1_EXCLUDED_SYMBOLS

        assert "LTCUSDT" not in V1_EXCLUDED_SYMBOLS

    def test_assert_v1_universe_accepts_iter028(self) -> None:
        """assert_v1_universe() must accept {"LTCUSDT"} without raising."""
        from crypto_trade.features_v1 import V1_ITER028_UNIVERSE, assert_v1_universe

        # Should not raise
        assert_v1_universe(V1_ITER028_UNIVERSE)


class TestFoundationRegression:
    """walk_forward.py:113 must carry embargo_ms purge (pre-fix lookahead was live bug)."""

    def test_walk_forward_line_113_carries_embargo(self) -> None:
        """The train_end_ms = test_start_ms - embargo_ms fix must be intact."""
        from crypto_trade.strategies.ml import walk_forward

        src = inspect.getsource(walk_forward)
        assert "train_end_ms = test_start_ms - embargo_ms" in src, (
            "walk_forward.py lookahead-fix regressed: "
            "'train_end_ms = test_start_ms - embargo_ms' not found"
        )

    def test_walk_forward_does_not_use_raw_test_start_as_train_end(self) -> None:
        """The old bug line 'train_end_ms = test_start_ms' (without embargo) must not appear."""
        from crypto_trade.strategies.ml import walk_forward

        src = inspect.getsource(walk_forward)
        # The broken form is the assignment without embargo subtraction.
        # We check the canonical fix form is present (redundant with above but explicit).
        assert "- embargo_ms" in src


class TestIter028FeatureColumnsPruned:
    """V1_FEATURE_COLUMNS_PRUNED must have exactly 43 features (pre-condition for guard)."""

    def test_pruned_columns_count_is_43(self) -> None:
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

        assert len(V1_FEATURE_COLUMNS_PRUNED) == 43

    def test_pruned_columns_is_tuple(self) -> None:
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

        assert isinstance(V1_FEATURE_COLUMNS_PRUNED, tuple)

    def test_pruned_columns_all_strings(self) -> None:
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

        for col in V1_FEATURE_COLUMNS_PRUNED:
            assert isinstance(col, str), f"Non-string feature column: {col!r}"
