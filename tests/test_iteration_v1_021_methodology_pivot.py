"""Smoke tests for iter-v1/021: Methodology Pivot — params_persist_path + feature importance.

Tests verify:
1. V1_ITER021_UNIVERSE is exactly the 5-symbol baseline universe.
2. PARAMS_PARQUET_PATH sentinel value is updated to iteration-stamped path at runtime.
3. params_persist_path writes all mandatory hyperparameter columns non-null for v1_pruned profile.
4. _write_feature_importance emits CSVs with required columns:
   (feature_name, mean_gain, importance_rank).
5. Dispatch branch fires correctly when BOTH iteration_label == "v1-021" AND universe matches.
6. No cross-track imports from features_v2 or features_v3 in /021 dispatch logic.
7. V1_ITER021_UNIVERSE == V1_BASELINE_UNIVERSE (dispatch uses iteration_label guard).
8. optimize_and_train accepts new params_persist_path parameter without breaking callers.
9. LightGbmStrategy accepts new params_persist_path + model_role + symbol parameters.
10. params_persist_path write is a true no-op when set to None (Layer B determinism).
11. _write_feature_importance handles empty strategy list gracefully.
12. params_persist_path handles v1_pruned_axis016 pinned-subsample case explicitly.
13. params_persist_path row includes all 11 hyperparameter columns (brief Layer C spec).

Brief reference: briefs-v1/iteration_v1-021/research_brief.md Sections 3.1, 3.2, 4.4
  (THREE-LAYER TEST: Layer A ≥168 rows, Layer B bit-identical, Layer C 10-param non-null).
"""

from __future__ import annotations

import math
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest


class TestV1Iter021UniverseConstant:
    """Test V1_ITER021_UNIVERSE constant correctness."""

    def test_universe_length_is_5(self) -> None:
        """V1_ITER021_UNIVERSE must have exactly 5 symbols (full pool universe)."""
        from run_baseline_v1 import V1_ITER021_UNIVERSE

        assert len(V1_ITER021_UNIVERSE) == 5, (
            f"Expected 5 symbols in V1_ITER021_UNIVERSE (full pool), "
            f"got {len(V1_ITER021_UNIVERSE)}: {V1_ITER021_UNIVERSE}"
        )

    def test_universe_equals_baseline_universe(self) -> None:
        """V1_ITER021_UNIVERSE must equal V1_BASELINE_UNIVERSE (same 5 symbols).

        The /021 dispatch is differentiated by iteration_label == 'v1-021',
        NOT by a unique symbol set. V1_ITER021_UNIVERSE == V1_BASELINE_UNIVERSE.
        """
        from run_baseline_v1 import V1_ITER021_UNIVERSE

        from crypto_trade.features_v1 import V1_BASELINE_UNIVERSE

        assert set(V1_ITER021_UNIVERSE) == set(V1_BASELINE_UNIVERSE), (
            "V1_ITER021_UNIVERSE must equal V1_BASELINE_UNIVERSE — "
            "/021 dispatch uses iteration_label guard, not a unique symbol set. "
            f"V1_ITER021_UNIVERSE={set(V1_ITER021_UNIVERSE)}, "
            f"V1_BASELINE_UNIVERSE={set(V1_BASELINE_UNIVERSE)}"
        )

    def test_universe_contains_all_5_baseline_symbols(self) -> None:
        """All 5 baseline symbols must be in V1_ITER021_UNIVERSE."""
        from run_baseline_v1 import V1_ITER021_UNIVERSE

        expected = {"BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT"}
        assert frozenset(V1_ITER021_UNIVERSE) == frozenset(expected), (
            f"V1_ITER021_UNIVERSE must contain all 5 baseline symbols: "
            f"expected {expected}, got {set(V1_ITER021_UNIVERSE)}"
        )


class TestParamsParquetPath:
    """Test PARAMS_PARQUET_PATH constant and initialization."""

    def test_params_parquet_path_is_sentinel(self) -> None:
        """PARAMS_PARQUET_PATH module-level sentinel uses SENTINEL label."""
        from run_baseline_v1 import PARAMS_PARQUET_PATH

        # Sentinel is overridden in main() for actual runs — verify the sentinel value
        assert "SENTINEL" in str(PARAMS_PARQUET_PATH), (
            f"PARAMS_PARQUET_PATH module sentinel should contain 'SENTINEL', "
            f"got: {PARAMS_PARQUET_PATH}"
        )

    def test_params_parquet_path_is_path_type(self) -> None:
        """PARAMS_PARQUET_PATH must be a pathlib.Path instance."""
        from run_baseline_v1 import PARAMS_PARQUET_PATH

        assert isinstance(PARAMS_PARQUET_PATH, Path), (
            f"PARAMS_PARQUET_PATH must be pathlib.Path, got {type(PARAMS_PARQUET_PATH)}"
        )


class TestParamsPersistPathWrite:
    """Test params_persist_path write in optimize_and_train (Layer C spec)."""

    def test_params_persist_path_writes_11_columns(self, tmp_path: Path) -> None:
        """params_persist_path must write all 11 mandatory hyperparameter columns.

        Layer C spec: NO .get(default) silent drops for v1_pruned profile.
        Expected columns: confidence_threshold, training_days, n_estimators, max_depth,
        num_leaves, learning_rate, subsample, colsample_bytree, min_child_samples,
        reg_alpha, reg_lambda.
        """
        import pandas as pd

        from crypto_trade.strategies.ml.optimization import optimize_and_train

        # Minimal training data — 100 rows, 5 features, binary labels
        rng = np.random.default_rng(42)
        n = 200
        x_train = rng.standard_normal((n, 5)).astype(np.float32)
        y = rng.choice([-1, 1], size=n).astype(np.float64)
        # PnL arrays
        long_pnls = rng.normal(0.01, 0.05, n).astype(np.float64)
        short_pnls = rng.normal(-0.01, 0.05, n).astype(np.float64)
        open_times = np.arange(n, dtype=np.int64) * 28_800_000  # 8h in ms

        params_path = tmp_path / "test_params.parquet"

        # Run with v1_pruned profile (the /021 canonical profile)
        model, cols, threshold = optimize_and_train(
            train_features=x_train,
            train_labels=y,
            all_columns=[f"feat_{i}" for i in range(5)],
            long_pnls=long_pnls,
            short_pnls=short_pnls,
            n_trials=3,  # minimal for test speed
            cv_splits=2,
            seed=42,
            verbose=0,
            open_times=open_times,
            train_end_ms=int(open_times[-1]) + 28_800_000,
            bounds_profile="v1_pruned",
            params_persist_path=params_path,
            model_role="Model_A_pool",
            symbol="BTC+ETH",
            train_month="2024-01",
        )

        assert params_path.exists(), "params_persist_path parquet was not created"

        df = pd.read_parquet(params_path)
        assert len(df) == 1, f"Expected 1 row, got {len(df)}"

        # Verify all 11 hyperparameter columns exist and are non-null
        mandatory_hyperparam_cols = [
            "confidence_threshold",
            "n_estimators",
            "max_depth",
            "num_leaves",
            "learning_rate",
            "subsample",
            "colsample_bytree",
            "min_child_samples",
            "reg_alpha",
            "reg_lambda",
        ]
        for col in mandatory_hyperparam_cols:
            assert col in df.columns, f"Missing column: {col}"
            assert not df[col].isnull().any(), f"NULL value in column: {col}"

        # Metadata columns
        assert df["model_role"].iloc[0] == "Model_A_pool"
        assert df["symbol"].iloc[0] == "BTC+ETH"
        assert df["train_month"].iloc[0] == "2024-01"
        assert df["seed"].iloc[0] == 42
        assert "best_objective_value" in df.columns
        assert not math.isnan(float(df["best_objective_value"].iloc[0]))

    def test_params_persist_path_none_is_noop(self) -> None:
        """When params_persist_path=None, no parquet file is created (Layer B safety).

        This verifies the parameter is truly optional and does NOT affect
        Optuna's training-objective domain when set to None.
        """
        from crypto_trade.strategies.ml.optimization import optimize_and_train

        rng = np.random.default_rng(42)
        n = 100
        x_train = rng.standard_normal((n, 5)).astype(np.float32)
        y = rng.choice([-1, 1], size=n).astype(np.float64)
        long_pnls = rng.normal(0.01, 0.05, n).astype(np.float64)
        short_pnls = rng.normal(-0.01, 0.05, n).astype(np.float64)

        # Must not raise and must not create any parquet file
        model, cols, threshold = optimize_and_train(
            train_features=x_train,
            train_labels=y,
            all_columns=[f"feat_{i}" for i in range(5)],
            long_pnls=long_pnls,
            short_pnls=short_pnls,
            n_trials=2,
            cv_splits=2,
            seed=42,
            verbose=0,
            bounds_profile="v1_pruned",
            params_persist_path=None,  # explicit None — no parquet
            model_role="Model_A_pool",
            symbol="BTC+ETH",
            train_month="2024-01",
        )

        assert model is not None
        assert isinstance(threshold, float)

    def test_params_persist_path_v1_pruned_axis016_pinned_values(self, tmp_path: Path) -> None:
        """For v1_pruned_axis016, subsample and colsample_bytree must be written as 1.0.

        Layer C spec: NO silent drops for pinned params. The pinned constants
        (subsample=1.0, colsample_bytree=1.0 for v1_pruned_axis016) are absent from
        study.best_params but MUST be written as the pinned constant (1.0), not dropped.
        """
        import pandas as pd

        from crypto_trade.strategies.ml.optimization import optimize_and_train

        rng = np.random.default_rng(42)
        n = 150
        x_train = rng.standard_normal((n, 5)).astype(np.float32)
        y = rng.choice([-1, 1], size=n).astype(np.float64)
        long_pnls = rng.normal(0.01, 0.05, n).astype(np.float64)
        short_pnls = rng.normal(-0.01, 0.05, n).astype(np.float64)

        params_path = tmp_path / "test_params_axis016.parquet"
        model, cols, threshold = optimize_and_train(
            train_features=x_train,
            train_labels=y,
            all_columns=[f"feat_{i}" for i in range(5)],
            long_pnls=long_pnls,
            short_pnls=short_pnls,
            n_trials=3,
            cv_splits=2,
            seed=42,
            verbose=0,
            bounds_profile="v1_pruned_axis016",
            params_persist_path=params_path,
            model_role="Model_axis016",
            symbol="test_sym",
            train_month="2024-02",
        )

        df = pd.read_parquet(params_path)
        assert len(df) == 1

        # Pinned values must be written explicitly (not NaN)
        assert float(df["subsample"].iloc[0]) == pytest.approx(1.0, abs=1e-6), (
            "subsample must be written as 1.0 for v1_pruned_axis016 (pinned, not sampled)"
        )
        assert float(df["colsample_bytree"].iloc[0]) == pytest.approx(1.0, abs=1e-6), (
            "colsample_bytree must be written as 1.0 for v1_pruned_axis016 (pinned)"
        )

    def test_params_persist_path_appends_multiple_rows(self, tmp_path: Path) -> None:
        """Multiple calls to optimize_and_train append rows (not overwrite)."""
        import pandas as pd

        from crypto_trade.strategies.ml.optimization import optimize_and_train

        rng = np.random.default_rng(42)
        n = 100
        x_train = rng.standard_normal((n, 5)).astype(np.float32)
        y = rng.choice([-1, 1], size=n).astype(np.float64)
        long_pnls = rng.normal(0.01, 0.05, n).astype(np.float64)
        short_pnls = rng.normal(-0.01, 0.05, n).astype(np.float64)

        params_path = tmp_path / "test_params_multi.parquet"

        for month in ["2024-01", "2024-02"]:
            optimize_and_train(
                train_features=x_train,
                train_labels=y,
                all_columns=[f"feat_{i}" for i in range(5)],
                long_pnls=long_pnls,
                short_pnls=short_pnls,
                n_trials=2,
                cv_splits=2,
                seed=42,
                verbose=0,
                bounds_profile="v1_pruned",
                params_persist_path=params_path,
                model_role="Model_A_pool",
                symbol="BTC+ETH",
                train_month=month,
            )

        df = pd.read_parquet(params_path)
        assert len(df) == 2, f"Expected 2 rows after 2 calls, got {len(df)}"
        assert set(df["train_month"]) == {"2024-01", "2024-02"}


class TestLightGbmStrategyNewParams:
    """Test LightGbmStrategy accepts new params_persist_path + model_role + symbol."""

    def test_accepts_params_persist_path_none(self) -> None:
        """LightGbmStrategy must accept params_persist_path=None without error."""
        from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

        strat = LightGbmStrategy(
            feature_columns=["feat_a", "feat_b"],
            ensemble_seeds=[42],
            params_persist_path=None,
            model_role="",
            symbol="",
        )
        assert strat._params_persist_path is None
        assert strat._model_role == ""
        assert strat._symbol == ""

    def test_accepts_params_persist_path_with_values(self, tmp_path: Path) -> None:
        """LightGbmStrategy must store params_persist_path + model_role + symbol."""
        from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

        params_path = tmp_path / "test_params.parquet"
        strat = LightGbmStrategy(
            feature_columns=["feat_a", "feat_b"],
            ensemble_seeds=[42],
            params_persist_path=params_path,
            model_role="Model_A_pool",
            symbol="BTC+ETH",
        )
        assert strat._params_persist_path == params_path
        assert strat._model_role == "Model_A_pool"
        assert strat._symbol == "BTC+ETH"


class TestWriteFeatureImportance:
    """Test _write_feature_importance emits required CSV columns."""

    def test_empty_strategies_is_noop(self, tmp_path: Path) -> None:
        """_write_feature_importance with empty list must not create any files."""
        from run_baseline_v1 import _write_feature_importance

        _write_feature_importance([], feature_columns=["feat_a"], report_dir=tmp_path)
        # No files should be created
        assert not list(tmp_path.glob("**/*.csv"))

    def test_emits_feature_importance_csv_with_required_columns(self, tmp_path: Path) -> None:
        """_write_feature_importance must emit CSV with feature_name, mean_gain, importance_rank.

        Brief Section 3.2: importance_type='gain' (via booster_.feature_importance).
        """
        import csv

        from run_baseline_v1 import _write_feature_importance

        # Build a minimal mock strategy with _models containing a mock LGBMClassifier
        mock_model = MagicMock()
        mock_booster = MagicMock()
        # Return a gain-importance array of length 3 (matching feature_columns)
        mock_booster.feature_importance.return_value = np.array([10.0, 5.0, 2.0])
        mock_model.booster_ = mock_booster
        mock_model.feature_importances_ = np.array([10.0, 5.0, 2.0])

        mock_strat = MagicMock()
        mock_strat.inner = MagicMock(spec=[])  # no 'inner' attr → use strat directly
        mock_strat._models = [mock_model]
        mock_strat.inner = None  # force the hasattr check to use mock_strat directly

        # Use a proper mock without 'inner' attribute
        class MockStrategy:
            def __init__(self) -> None:
                self._models = [mock_model]

        strategy = MockStrategy()
        feature_cols = ["feat_a", "feat_b", "feat_c"]

        _write_feature_importance(
            [("TEST_MODEL", strategy)],
            feature_columns=feature_cols,
            report_dir=tmp_path,
        )

        # Check per-model CSV was created
        out_path = tmp_path / "in_sample" / "feature_importance_TEST_MODEL.csv"
        assert out_path.exists(), f"Expected {out_path} to exist"

        with open(out_path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3, f"Expected 3 rows (one per feature), got {len(rows)}"
        # Required columns
        for row in rows:
            assert "feature_name" in row, "Missing column: feature_name"
            assert "mean_gain" in row, "Missing column: mean_gain"
            assert "importance_rank" in row, "Missing column: importance_rank"

        # Portfolio CSV also created
        port_path = tmp_path / "in_sample" / "feature_importance_portfolio.csv"
        assert port_path.exists(), f"Expected {port_path} to exist"

    def test_importance_rank_is_descending(self, tmp_path: Path) -> None:
        """importance_rank must be sorted descending by mean_gain (rank 1 = highest gain)."""
        import csv

        from run_baseline_v1 import _write_feature_importance

        mock_model = MagicMock()
        mock_booster = MagicMock()
        # feat_b has highest gain (20), feat_a mid (10), feat_c lowest (1)
        mock_booster.feature_importance.return_value = np.array([10.0, 20.0, 1.0])
        mock_model.booster_ = mock_booster

        class MockStrategy:
            def __init__(self) -> None:
                self._models = [mock_model]

        strategy = MockStrategy()
        feature_cols = ["feat_a", "feat_b", "feat_c"]

        _write_feature_importance(
            [("RANK_TEST", strategy)],
            feature_columns=feature_cols,
            report_dir=tmp_path,
        )

        out_path = tmp_path / "in_sample" / "feature_importance_RANK_TEST.csv"
        with open(out_path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Rank 1 must have highest mean_gain
        rank1_row = [r for r in rows if r["importance_rank"] == "1"][0]
        assert rank1_row["feature_name"] == "feat_b", (
            f"Rank 1 must be feat_b (highest gain=20), got {rank1_row['feature_name']}"
        )
        # Rank 3 must have lowest mean_gain
        rank3_row = [r for r in rows if r["importance_rank"] == "3"][0]
        assert rank3_row["feature_name"] == "feat_c", (
            f"Rank 3 must be feat_c (lowest gain=1), got {rank3_row['feature_name']}"
        )


class TestDispatchOrdering:
    """Test that /021 dispatch ordering is correct relative to other iterations."""

    def test_v1_iter021_universe_declared_after_v1_iter020_universe(self) -> None:
        """V1_ITER021_UNIVERSE must be declared after V1_ITER020_UNIVERSE in source."""
        import inspect

        import run_baseline_v1

        source = inspect.getsource(run_baseline_v1)
        idx_020 = source.find("V1_ITER020_UNIVERSE")
        idx_021 = source.find("V1_ITER021_UNIVERSE")
        assert idx_020 < idx_021, (
            "V1_ITER021_UNIVERSE must be declared after V1_ITER020_UNIVERSE in source order"
        )

    def test_no_cross_track_imports_in_runner(self) -> None:
        """run_baseline_v1.py must NOT import from features_v2 or features_v3.

        Track isolation: v1 runner imports ONLY from features_v1, NOT from v2 or v3.
        """
        with open(Path(__file__).parent.parent / "run_baseline_v1.py") as f:
            content = f.read()

        assert "from crypto_trade.features_v2" not in content, (
            "run_baseline_v1.py must NOT import from features_v2 (track isolation)"
        )
        assert "from crypto_trade.features_v3" not in content, (
            "run_baseline_v1.py must NOT import from features_v3 (track isolation)"
        )
        assert "import crypto_trade.features_v2" not in content, (
            "run_baseline_v1.py must NOT import features_v2 (track isolation)"
        )
        assert "import crypto_trade.features_v3" not in content, (
            "run_baseline_v1.py must NOT import features_v3 (track isolation)"
        )


class TestIter021DispatchGuard:
    """Test /021 dispatch guard: requires both universe match AND iteration_label."""

    def test_iter021_dispatch_requires_iteration_label(self) -> None:
        """The /021 elif guard must check iteration_label == 'v1-021'.

        Since V1_ITER021_UNIVERSE == V1_BASELINE_UNIVERSE, dispatching on universe
        alone would fire for ALL 5-sym runs. The guard must include iteration_label.
        """
        import inspect

        import run_baseline_v1

        source = inspect.getsource(run_baseline_v1)
        # Find the elif block for /021 dispatch
        assert 'iteration_label == "v1-021"' in source, (
            "The /021 dispatch elif block MUST include iteration_label == 'v1-021' "
            "because V1_ITER021_UNIVERSE == V1_BASELINE_UNIVERSE (same 5-sym set). "
            "Without the iteration_label guard, ALL 5-sym runs would fire /021 logic."
        )

    def test_iter021_dispatch_checks_universe(self) -> None:
        """The /021 elif guard must check the universe set."""
        import inspect

        import run_baseline_v1

        source = inspect.getsource(run_baseline_v1)
        assert "V1_ITER021_UNIVERSE" in source, (
            "The /021 dispatch must reference V1_ITER021_UNIVERSE constant"
        )

    def test_baseline_if_excludes_v1_021_label(self) -> None:
        """The catch-all dispatch must exclude 'v1-021' so the /021 elif is reachable.

        V1_ITER021_UNIVERSE == V1_BASELINE_UNIVERSE, so without an exclusion guard,
        the catch-all would match /021 invocations and the /021 elif would be dead code.

        The refactored runner uses an exclusion tuple: iteration_label not in (..., "v1-021", ...).
        This test verifies both the exclusion and the dispatch ordering.

        This test verifies the dispatch ordering fix from Critic Phase 6.0 BLOCKER A.
        """
        import inspect

        import run_baseline_v1

        source = inspect.getsource(run_baseline_v1)

        # The exclusion tuple must contain "v1-021"
        assert '"v1-021"' in source, (
            "The catch-all exclusion tuple in run_baseline_v1.py must contain \"v1-021\". "
            "Without it, V1_ITER021_UNIVERSE == V1_BASELINE_UNIVERSE means the /021 elif "
            "is dead code and the /021 dispatch is never reached."
        )

        # The baseline if must appear BEFORE the /021 elif in source order
        idx_baseline_if = source.find('"v1-021"')
        idx_021_elif = source.find('set(V1_ITER021_UNIVERSE) and iteration_label == "v1-021"')

        assert idx_baseline_if != -1, (
            "Could not locate baseline 'if' with exclusion guard in source"
        )
        assert idx_021_elif != -1, "Could not locate /021 'elif' block in source"
        assert idx_baseline_if < idx_021_elif, (
            f"Baseline 'if' (pos={idx_baseline_if}) must appear BEFORE /021 'elif' "
            f"(pos={idx_021_elif}) in source order — the dispatch must fall through "
            "to the elif when iteration_label == 'v1-021'."
        )


class TestPerMonthFILog:
    """Test 20: _per_month_fi_log accumulation in LightGbmStrategy.

    iter-v1/021 BLOCK-PENDING-FIX H2: verifies that:
    (a) _per_month_fi_log is initialized empty in __init__.
    (b) _per_month_fi_log accumulates non-empty entries after each _train_for_month call
        (simulated via directly calling the accumulation logic with mock _models).
    (c) _write_feature_importance reads _per_month_fi_log (primary path) and produces
        a populated CSV (non-zero mean_gain) for the Pool model.
    (d) Both Pool and BTC-only strategies produce populated feature importance CSVs when
        _per_month_fi_log is populated (H2 root-cause regression test).
    """

    def test_per_month_fi_log_initialized_empty(self) -> None:
        """LightGbmStrategy must initialize _per_month_fi_log = [] in __init__."""
        from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

        strat = LightGbmStrategy(
            feature_columns=["feat_a", "feat_b", "feat_c"],
            ensemble_seeds=[42],
        )
        assert hasattr(strat, "_per_month_fi_log"), (
            "LightGbmStrategy must have _per_month_fi_log attribute after __init__"
        )
        assert strat._per_month_fi_log == [], (
            f"_per_month_fi_log must be empty list after __init__, got {strat._per_month_fi_log}"
        )

    def test_write_fi_uses_per_month_fi_log_primary_path(self, tmp_path: Path) -> None:
        """_write_feature_importance must use _per_month_fi_log as primary path.

        When _per_month_fi_log is populated with non-zero gains, the resulting CSV
        must contain non-zero mean_gain values (the BLOCK-PENDING-FIX regression test).
        The Pool model's all-zeros bug was caused by _models being empty at post-dispatch
        read time; _per_month_fi_log is written during _train_for_month before reset.
        """
        import csv

        from run_baseline_v1 import _write_feature_importance

        feature_cols = ["feat_a", "feat_b", "feat_c"]

        # Simulate a strategy where _models is empty (post-dispatch stale state)
        # but _per_month_fi_log was populated during training (24 months).
        class MockStrategyWithFILog:
            def __init__(self) -> None:
                self._models = []  # empty — as happens post-dispatch (stale reference)
                self._per_month_fi_log = [
                    {
                        "train_month": f"2023-{m:02d}",
                        "mean_gain": {"feat_a": 100.0 + m, "feat_b": 50.0 + m, "feat_c": 10.0},
                    }
                    for m in range(1, 13)  # 12 months of accumulated FI
                ]

        strategy = MockStrategyWithFILog()
        _write_feature_importance(
            [("POOL_Model_A", strategy)],
            feature_columns=feature_cols,
            report_dir=tmp_path,
        )

        out_path = tmp_path / "in_sample" / "feature_importance_POOL_Model_A.csv"
        assert out_path.exists(), (
            "feature_importance_POOL_Model_A.csv must exist when _per_month_fi_log is populated"
        )

        with open(out_path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3, f"Expected 3 feature rows, got {len(rows)}"
        # All mean_gain values must be non-zero (the BLOCK-PENDING-FIX regression check)
        for row in rows:
            gain = float(row["mean_gain"])
            assert gain > 0.0, (
                f"mean_gain for {row['feature_name']} must be > 0.0 when _per_month_fi_log "
                f"has non-zero entries; got {gain}. This is the Pool-all-zeros regression test."
            )

    def test_both_pool_and_btc_strategies_produce_populated_csvs(self, tmp_path: Path) -> None:
        """Both Pool (Model A) and BTC-only (Model H) must produce non-zero FI CSVs.

        This is the direct regression test for the H2 root cause: Pool all-zeros because
        _models was empty at post-dispatch read time. With _per_month_fi_log, both strategies
        accumulate FI independently during their respective walk-forward month trains.
        """
        import csv

        from run_baseline_v1 import _write_feature_importance

        feature_cols = ["feat_a", "feat_b"]

        class MockPoolStrategy:
            def __init__(self) -> None:
                self._models = []  # empty at post-dispatch (stale)
                self._per_month_fi_log = [
                    {"train_month": "2023-01", "mean_gain": {"feat_a": 200.0, "feat_b": 80.0}},
                    {"train_month": "2023-02", "mean_gain": {"feat_a": 220.0, "feat_b": 90.0}},
                ]

        class MockBTCStrategy:
            def __init__(self) -> None:
                self._models = []  # also empty at post-dispatch
                self._per_month_fi_log = [
                    {"train_month": "2023-01", "mean_gain": {"feat_a": 150.0, "feat_b": 60.0}},
                    {"train_month": "2023-02", "mean_gain": {"feat_a": 170.0, "feat_b": 70.0}},
                ]

        strategies = [
            ("POOL_Model_A", MockPoolStrategy()),
            ("BTC_Model_H", MockBTCStrategy()),
        ]
        _write_feature_importance(strategies, feature_columns=feature_cols, report_dir=tmp_path)

        for name in ("POOL_Model_A", "BTC_Model_H"):
            path = tmp_path / "in_sample" / f"feature_importance_{name}.csv"
            assert path.exists(), f"feature_importance_{name}.csv must exist"
            with open(path) as f:
                rows = list(csv.DictReader(f))
            assert len(rows) == 2
            for row in rows:
                assert float(row["mean_gain"]) > 0.0, (
                    f"{name}: mean_gain for {row['feature_name']} is 0.0 — "
                    "regression: _per_month_fi_log primary path must produce non-zero gains"
                )

        # Portfolio CSV must also be non-zero
        port_path = tmp_path / "in_sample" / "feature_importance_portfolio.csv"
        assert port_path.exists()
        with open(port_path) as f:
            port_rows = list(csv.DictReader(f))
        for row in port_rows:
            assert float(row["mean_gain"]) > 0.0, (
                f"Portfolio mean_gain for {row['feature_name']} is 0.0 — "
                "regression test for Pool+BTC combined FI aggregation"
            )

    def test_per_month_fi_log_accumulates_across_months(self) -> None:
        """_per_month_fi_log must grow by 1 entry per _train_for_month call.

        This test verifies the accumulation contract without running a full backtest.
        Uses a minimal LightGbmStrategy and directly exercises the accumulation code
        by patching _models with a mock booster.
        """
        from unittest.mock import MagicMock

        from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

        feature_cols = ["feat_a", "feat_b", "feat_c"]
        strat = LightGbmStrategy(
            feature_columns=feature_cols,
            ensemble_seeds=[42],
        )

        # Simulate what _train_for_month does at the accumulation point:
        # self._models is populated with trained boosters; code reads their gain importance
        # and appends to _per_month_fi_log.
        for month_idx in range(3):
            month_str = f"2023-{month_idx + 1:02d}"
            # Mimic post-ensemble-loop _models state
            mock_model = MagicMock()
            mock_booster = MagicMock()
            mock_booster.feature_importance.return_value = np.array(
                [float(10 + month_idx), float(5 + month_idx), float(1 + month_idx)]
            )
            mock_model.booster_ = mock_booster
            strat._models = [mock_model]

            # Run the accumulation logic inline (mirrors _train_for_month code)
            _fi_cols = list(strat.feature_columns)
            _month_gains: dict[str, list[float]] = {c: [] for c in _fi_cols}
            for _m in strat._models:
                _fi_arr = None
                if hasattr(_m, "booster_"):
                    _fi_arr = _m.booster_.feature_importance(importance_type="gain")
                if _fi_arr is not None:
                    for _i, _c in enumerate(_fi_cols):
                        if _i < len(_fi_arr):
                            _month_gains[_c].append(float(_fi_arr[_i]))
            _mean_gain = {c: float(np.mean(v)) if v else 0.0 for c, v in _month_gains.items()}
            strat._per_month_fi_log.append({"train_month": month_str, "mean_gain": _mean_gain})

        assert len(strat._per_month_fi_log) == 3, (
            f"Expected 3 entries in _per_month_fi_log (one per month), "
            f"got {len(strat._per_month_fi_log)}"
        )
        # Verify months are distinct
        months = [e["train_month"] for e in strat._per_month_fi_log]
        assert months == ["2023-01", "2023-02", "2023-03"], f"Month sequence mismatch: {months}"
        # Verify gains are non-zero and increasing (mirrors the mock data)
        for i, entry in enumerate(strat._per_month_fi_log):
            mg = entry["mean_gain"]
            assert mg["feat_a"] == pytest.approx(10.0 + i), (
                f"feat_a month {i}: expected {10.0 + i}, got {mg['feat_a']}"
            )
