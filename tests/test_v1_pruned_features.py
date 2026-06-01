"""Tests for iter-v1/002 pruned feature set + runner flags + Optuna bounds profile.

Covers:
- V1_FEATURE_COLUMNS_PRUNED has exactly 44 elements
  * iter-v1/002: 40 core features (IC-pruned from 193 baseline)
  * iter-v1/023: +2 funding features (funding_rate_zscore_30/90) → 42
  * iter-v1/025: +1 OI delta feature (oi_delta_30_z90) → 43
  * iter-v1/034: +1 basis_zscore_30 → 44
  * iter-v1/040: SWAP basis_zscore_30 → regime_momentum_signed_5d (still 44)
- V1_FEATURE_COLUMNS is unchanged (still 193 columns)
- V1_OOD_FEATURE_COLUMNS is NOT a subset of V1_FEATURE_COLUMNS_PRUNED
  (verifies R3 runtime decoupling design — 13/16 OOD features live OUTSIDE
  the pruned set but are still loaded from parquet via the ood_features arg)
- LM Master swap applied (mom_mom_5 absent, stat_kurtosis_20 present)
- Pruned set is alphabetically sorted (required for deterministic column ordering)
- --pruned-features CLI flag toggles feature_columns to V1_FEATURE_COLUMNS_PRUNED
- Optuna bounds profile "v1_pruned" applies tighter bounds vs "default"

Run:
    uv run pytest tests/test_v1_pruned_features.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestV1FeatureColumnsPruned:
    """Unit tests for V1_FEATURE_COLUMNS_PRUNED constant."""

    def test_pruned_set_has_exactly_43_features(self) -> None:
        # iter-v1/002: 40 core IC-pruned features.
        # iter-v1/023: +2 funding features → 42.
        # iter-v1/025: +1 OI delta feature → 43.
        # iter-v1/034: +1 basis_zscore_30 → 44.
        # iter-v1/040: SWAP basis_zscore_30 → regime_momentum_signed_5d (still 44).
        # iter-v1/049: +1 long_short_zscore_30 → 45.
        # iter-v1/050: +1 dot_vs_btc_ret_ratio_30 → 46.
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

        assert len(V1_FEATURE_COLUMNS_PRUNED) == 46, (
            f"Expected 46 features; got {len(V1_FEATURE_COLUMNS_PRUNED)}"
        )

    def test_all_43_are_in_baseline_feature_columns_or_v1_extensions(self) -> None:
        # iter-v1/023/025 added funding + OI features that are NOT in the 193-col
        # V1_FEATURE_COLUMNS baseline (those are v1-specific extensions).
        # iter-v1/034 added basis_zscore_30; iter-v1/040 replaced it with
        # regime_momentum_signed_5d (also a v1 extension — composed feature).
        # Verify the 40 core features ARE in the baseline; allow the 5 v1 extensions.
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS, V1_FEATURE_COLUMNS_PRUNED

        baseline_set = set(V1_FEATURE_COLUMNS)
        v1_extensions = {
            "funding_rate_zscore_30",
            "funding_rate_zscore_90",
            "oi_delta_30_z90",
            "basis_zscore_30",  # iter-v1/034 (retired in /040 but kept here for clarity)
            "regime_momentum_signed_5d",  # iter-v1/040: composed feature
            "long_short_zscore_30",  # iter-v1/049: top-trader long/short ratio z-score
            "dot_vs_btc_ret_ratio_30",  # iter-v1/050: DOT cross-BTC idiosyncratic ratio
        }
        for feat in V1_FEATURE_COLUMNS_PRUNED:
            assert feat in baseline_set or feat in v1_extensions, (
                f"Pruned feature '{feat}' not found in V1_FEATURE_COLUMNS (193 baseline) "
                f"or v1 extensions {v1_extensions}."
            )

    def test_v1_feature_columns_still_has_193_features(self) -> None:
        """V1_FEATURE_COLUMNS must NOT be modified — only an additional constant was added."""
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS

        assert len(V1_FEATURE_COLUMNS) == 193, (
            f"V1_FEATURE_COLUMNS was modified (got {len(V1_FEATURE_COLUMNS)}, expected 193). "
            "The pruned set must be an ADDITIONAL constant; do NOT modify the 193-col baseline."
        )

    def test_ood_feature_columns_not_subset_of_pruned(self) -> None:
        """V1_OOD_FEATURE_COLUMNS must NOT be a subset of V1_FEATURE_COLUMNS_PRUNED.

        Only 3 of 16 OOD features overlap with the pruned set. The remaining 13
        are loaded from the full parquet column set at runtime (lgbm.py:576 reads
        from train_feat_df.columns, which is the full parquet, NOT the 40-pruned
        feature_columns). This test guards against accidentally running R3 OOD
        with a reduced covariance matrix.
        """
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED, V1_OOD_FEATURE_COLUMNS

        pruned_set = set(V1_FEATURE_COLUMNS_PRUNED)
        ood_set = set(V1_OOD_FEATURE_COLUMNS)

        # At most 3 overlap (stat_return_5, mr_rsi_extreme_14, vol_volume_pctchg_5)
        overlap = ood_set & pruned_set
        assert len(V1_OOD_FEATURE_COLUMNS) == 16, (
            f"V1_OOD_FEATURE_COLUMNS should have 16 features; got {len(V1_OOD_FEATURE_COLUMNS)}"
        )
        # The OOD set is NOT fully contained in the pruned set — guards R3 decoupling
        assert not ood_set.issubset(pruned_set), (
            "V1_OOD_FEATURE_COLUMNS is a subset of V1_FEATURE_COLUMNS_PRUNED. "
            "R3 Mahalanobis OOD operates on 16 scale-invariant features, only 3 of "
            "which are in the pruned set. The 13 others must come from the full parquet. "
            f"Overlap found: {sorted(overlap)}"
        )
        # Specific overlap count (informational — catches accidental OOD list changes)
        assert len(overlap) <= 5, (
            f"Expected at most 5 OOD features in the pruned set; "
            f"got {len(overlap)}: {sorted(overlap)}"
        )

    def test_lm_master_swap_applied_correctly(self) -> None:
        """LM Master Phase 4.5 swap: drop mom_mom_5, add stat_kurtosis_20."""
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

        pruned_set = set(V1_FEATURE_COLUMNS_PRUNED)

        # mom_mom_5 must be absent (dropped per swap)
        assert "mom_mom_5" not in pruned_set, (
            "mom_mom_5 should have been dropped by the LM Master Phase 4.5 swap. "
            "stat_return_5 + mom_roc_10 already cover the short-momentum kernel."
        )

        # stat_kurtosis_20 must be present (added per swap)
        assert "stat_kurtosis_20" in pruned_set, (
            "stat_kurtosis_20 should have been added by the LM Master Phase 4.5 swap. "
            "It fills the 4th-moment (tail-fatness) gap in the statistical family."
        )

    def test_pruned_set_is_alphabetically_sorted(self) -> None:
        """Alphabetical sort ensures deterministic column ordering for LightGBM colsample_bytree."""
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

        assert list(V1_FEATURE_COLUMNS_PRUNED) == sorted(V1_FEATURE_COLUMNS_PRUNED), (
            "V1_FEATURE_COLUMNS_PRUNED must be alphabetically sorted. "
            "Column ordering determines LightGBM's colsample_bytree sampling positions."
        )

    def test_pruned_set_exported_in_all(self) -> None:
        """V1_FEATURE_COLUMNS_PRUNED must appear in features_v1.__all__."""
        import crypto_trade.features_v1 as mod

        assert "V1_FEATURE_COLUMNS_PRUNED" in mod.__all__, (
            "V1_FEATURE_COLUMNS_PRUNED must be listed in features_v1.__all__ "
            "so the runner can import it by name."
        )

    def test_pruned_set_no_duplicates(self) -> None:
        """No feature should appear twice in the pruned set."""
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

        seen: set[str] = set()
        duplicates: list[str] = []
        for feat in V1_FEATURE_COLUMNS_PRUNED:
            if feat in seen:
                duplicates.append(feat)
            seen.add(feat)
        assert not duplicates, (
            f"Duplicate features found in V1_FEATURE_COLUMNS_PRUNED: {duplicates}"
        )


class TestPrunedFeaturesCliFlag:
    """Verify --pruned-features flag wiring in run_baseline_v1.py."""

    def _parse_and_resolve_features(self, argv: list[str]) -> dict:
        """Parse argv and resolve feature_columns / bounds_profile as main() would.

        Returns dict with resolved feature_columns (list) and bounds_profile (str).
        """
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--iteration", type=int, default=None)
        parser.add_argument("--baseline-mode", action="store_true")
        parser.add_argument("--exploration", action="store_true")
        parser.add_argument("--confirmation", action="store_true")
        parser.add_argument("--n-trials", type=int, default=35)
        parser.add_argument("--ensemble-size", type=int, default=None)
        parser.add_argument("--symbols", type=str, default=None)
        parser.add_argument("--pruned-features", action="store_true")
        args = parser.parse_args(argv)

        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS, V1_FEATURE_COLUMNS_PRUNED

        if getattr(args, "pruned_features", False):
            feature_columns = list(V1_FEATURE_COLUMNS_PRUNED)
            bounds_profile = "v1_pruned"
        else:
            feature_columns = list(V1_FEATURE_COLUMNS)
            bounds_profile = "default"

        return {"feature_columns": feature_columns, "bounds_profile": bounds_profile}

    def test_default_uses_193_feature_columns(self) -> None:
        """Without --pruned-features, feature_columns defaults to V1_FEATURE_COLUMNS (193)."""
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS

        result = self._parse_and_resolve_features(["--exploration", "--iteration", "2"])
        assert len(result["feature_columns"]) == len(V1_FEATURE_COLUMNS)
        assert result["bounds_profile"] == "default"

    def test_pruned_features_flag_gives_43_columns(self) -> None:
        """--pruned-features activates V1_FEATURE_COLUMNS_PRUNED (46 cols after iter-v1/050)."""
        result = self._parse_and_resolve_features(
            ["--exploration", "--iteration", "2", "--pruned-features"]
        )
        assert len(result["feature_columns"]) == 46
        assert result["bounds_profile"] == "v1_pruned"

    def test_pruned_features_and_v1_feature_columns_are_disjoint_in_count(self) -> None:
        """--pruned-features gives 40 cols; default gives 193 — never equal."""
        result_pruned = self._parse_and_resolve_features(
            ["--exploration", "--iteration", "2", "--pruned-features"]
        )
        result_default = self._parse_and_resolve_features(["--exploration", "--iteration", "2"])
        assert len(result_pruned["feature_columns"]) != len(result_default["feature_columns"])


class TestOptunaBoundsProfile:
    """Verify bounds_profile="v1_pruned" applies tighter Optuna hyperparameter bounds."""

    def test_v1_pruned_num_leaves_upper_is_63(self) -> None:
        """LM Master Rec #1: num_leaves upper bound 127 → 63 for v1_pruned."""

        import numpy as np

        from crypto_trade.strategies.ml.optimization import _objective

        # Build a minimal trial mock that records suggest_int calls
        captured: dict[str, dict] = {}

        class MockStudy:
            user_attrs = {"fast_mode": False}

        class MockTrial:
            study = MockStudy()
            number = 0

            def suggest_float(self, name, low, high, **kwargs):
                return (low + high) / 2

            def suggest_int(self, name, low, high, **kwargs):
                captured[name] = {"low": low, "high": high}
                return (low + high) // 2

        trial = MockTrial()

        # Minimal arrays to keep the objective from erroring on fold splits
        n = 50
        rng = np.random.default_rng(42)
        features = rng.standard_normal((n, 3))
        labels = rng.choice([-1, 1], size=n)
        weights = np.ones(n)
        long_pnls = rng.standard_normal(n)
        short_pnls = rng.standard_normal(n)

        try:
            _objective(
                trial,
                features,
                labels,
                weights,
                long_pnls,
                short_pnls,
                ["f0", "f1", "f2"],
                cv_splits=2,
                seed=42,
                bounds_profile="v1_pruned",
            )
        except Exception:
            pass  # We only need the suggest_int calls captured before any error

        assert "num_leaves" in captured, "num_leaves not captured by mock trial"
        assert captured["num_leaves"]["high"] == 63, (
            f"Expected num_leaves upper=63 for v1_pruned; got {captured['num_leaves']['high']}"
        )

    def test_default_profile_num_leaves_upper_is_127(self) -> None:
        """Default profile keeps num_leaves upper bound at 127."""
        import numpy as np

        from crypto_trade.strategies.ml.optimization import _objective

        captured: dict[str, dict] = {}

        class MockStudy:
            user_attrs = {"fast_mode": False}

        class MockTrial:
            study = MockStudy()
            number = 0

            def suggest_float(self, name, low, high, **kwargs):
                return (low + high) / 2

            def suggest_int(self, name, low, high, **kwargs):
                captured[name] = {"low": low, "high": high}
                return (low + high) // 2

        trial = MockTrial()

        n = 50
        rng = np.random.default_rng(42)
        features = rng.standard_normal((n, 3))
        labels = rng.choice([-1, 1], size=n)
        weights = np.ones(n)
        long_pnls = rng.standard_normal(n)
        short_pnls = rng.standard_normal(n)

        try:
            _objective(
                trial,
                features,
                labels,
                weights,
                long_pnls,
                short_pnls,
                ["f0", "f1", "f2"],
                cv_splits=2,
                seed=42,
                bounds_profile="default",
            )
        except Exception:
            pass

        assert "num_leaves" in captured
        assert captured["num_leaves"]["high"] == 127, (
            f"Expected num_leaves upper=127 for default; got {captured['num_leaves']['high']}"
        )

    def test_v1_pruned_min_child_samples_lower_is_20(self) -> None:
        """LM Master Rec #3: min_child_samples lower bound 5 → 20 for v1_pruned."""
        import numpy as np

        from crypto_trade.strategies.ml.optimization import _objective

        captured: dict[str, dict] = {}

        class MockStudy:
            user_attrs = {"fast_mode": False}

        class MockTrial:
            study = MockStudy()
            number = 0

            def suggest_float(self, name, low, high, **kwargs):
                return (low + high) / 2

            def suggest_int(self, name, low, high, **kwargs):
                captured[name] = {"low": low, "high": high}
                return (low + high) // 2

        trial = MockTrial()

        n = 50
        rng = np.random.default_rng(42)
        features = rng.standard_normal((n, 3))
        labels = rng.choice([-1, 1], size=n)
        weights = np.ones(n)
        long_pnls = rng.standard_normal(n)
        short_pnls = rng.standard_normal(n)

        try:
            _objective(
                trial,
                features,
                labels,
                weights,
                long_pnls,
                short_pnls,
                ["f0", "f1", "f2"],
                cv_splits=2,
                seed=42,
                bounds_profile="v1_pruned",
            )
        except Exception:
            pass

        assert "min_child_samples" in captured
        assert captured["min_child_samples"]["low"] == 20, (
            f"Expected min_child_samples lower=20 for v1_pruned; "
            f"got {captured['min_child_samples']['low']}"
        )

    def test_lgbm_strategy_accepts_bounds_profile(self) -> None:
        """LightGbmStrategy.__init__ accepts bounds_profile kwarg without raising."""
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED, V1_OOD_FEATURE_COLUMNS
        from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

        # Should not raise — this tests the parameter is wired into the constructor
        strategy = LightGbmStrategy(
            training_months=24,
            n_trials=1,
            cv_splits=2,
            label_tp_pct=8.0,
            label_sl_pct=4.0,
            label_timeout_minutes=10080,
            fee_pct=0.1,
            features_dir="data/features",
            verbose=0,
            atr_tp_multiplier=2.9,
            atr_sl_multiplier=1.45,
            use_atr_labeling=True,
            ensemble_seeds=[42],
            feature_columns=list(V1_FEATURE_COLUMNS_PRUNED),
            ood_enabled=True,
            ood_features=list(V1_OOD_FEATURE_COLUMNS),
            ood_cutoff_pct=0.70,
            bounds_profile="v1_pruned",
        )
        assert strategy._bounds_profile == "v1_pruned"

    def test_lgbm_strategy_default_bounds_profile_is_default(self) -> None:
        """LightGbmStrategy defaults to 'default' bounds_profile (backward-compat)."""
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS
        from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

        strategy = LightGbmStrategy(
            training_months=24,
            n_trials=1,
            cv_splits=2,
            label_tp_pct=8.0,
            label_sl_pct=4.0,
            label_timeout_minutes=10080,
            fee_pct=0.1,
            features_dir="data/features",
            verbose=0,
            ensemble_seeds=[42],
            feature_columns=list(V1_FEATURE_COLUMNS)[:10],
        )
        assert strategy._bounds_profile == "default"
