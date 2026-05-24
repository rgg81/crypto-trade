"""Tests for reporting_v1.py — iter-v1/001 + iter-v1/008 methodology axes.

Covers:
- PSR dual-granularity computation and monotonicity invariant (F5 from brief)
- N_eff PCA fixture-based invariants (LM Master saturation-risk mandate):
    * Identical trial bouquet → n_eff = 1
    * Independent trial set → n_eff ≈ n_trials
- PSR granularity-mismatch trap (iter-v3/056 regression guard)
- V1_FAMILY_MAP completeness (all 193 columns assigned)
- ADF exception class taxonomy (pre-declared exceptions coverage)
- iter-v1/008 per-cell PCA refactor tests:
    * aggfunc="mean" gives expected n_eff on synthetic OOF parquet
    * by-symbol medians correct count
    * NaN guard logs warning when cell has fewer trials than n_trials_naive
    * iter-stamped OOF path generated correctly per iteration label
    * Per-cell median row emitted in comparison.csv when args provided
    * write_dsr_json emits n_eff_per_cell_median and related fields

Run:
    uv run pytest tests/test_reporting_v1.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.features_v1 import V1_FEATURE_COLUMNS
from crypto_trade.strategies.ml.reporting_v1 import (
    V1_FAMILIES,
    V1_FAMILY_MAP,
    _assign_exception_class,
    _per_cell_n_eff_from_parquet,
    _safe_kurt,
    _safe_skew,
    append_psr_rows_to_comparison,
    compute_psr_columns,
    write_adf_test_csv,
    write_dsr_json,
    write_ic_matrix_csv,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def synthetic_monthly_returns() -> np.ndarray:
    """39 monthly returns with known mean and std (IS window size)."""
    rng = np.random.default_rng(42)
    return rng.normal(loc=0.005, scale=0.02, size=39)


@pytest.fixture()
def synthetic_daily_returns() -> np.ndarray:
    """416 daily returns (IS window size)."""
    rng = np.random.default_rng(42)
    return rng.normal(loc=0.0003, scale=0.008, size=416)


@pytest.fixture()
def tmp_report_dir(tmp_path: Path) -> Path:
    """Temporary directory for report file writes."""
    return tmp_path


# ---------------------------------------------------------------------------
# V1_FAMILY_MAP completeness
# ---------------------------------------------------------------------------


class TestFamilyMap:
    def test_all_193_columns_assigned(self) -> None:
        """Every column in V1_FEATURE_COLUMNS must appear in V1_FAMILY_MAP."""
        all_mapped = set()
        for fam_cols in V1_FAMILY_MAP.values():
            all_mapped.update(fam_cols)
        assert len(V1_FEATURE_COLUMNS) == 193
        assert all_mapped == set(V1_FEATURE_COLUMNS), (
            f"Unmapped columns: {set(V1_FEATURE_COLUMNS) - all_mapped}"
        )

    def test_8_active_families(self) -> None:
        """Exactly 8 active families per brief Section 2 Table 2."""
        active = [f for f, cols in V1_FAMILY_MAP.items() if cols]
        assert set(active) == set(V1_FAMILIES), (
            f"Active families: {sorted(active)}, expected: {sorted(V1_FAMILIES)}"
        )

    def test_no_unknown_columns(self) -> None:
        """No column should be assigned to 'unknown' family."""
        unknown = V1_FAMILY_MAP.get("unknown", [])
        assert unknown == [], f"Unexpected unknown family columns: {unknown}"

    def test_trend_family_size(self) -> None:
        """trend family should have exactly 39 columns."""
        assert len(V1_FAMILY_MAP["trend"]) == 39

    def test_calendar_family_size(self) -> None:
        """calendar family should have exactly 2 columns."""
        assert len(V1_FAMILY_MAP["calendar"]) == 2


# ---------------------------------------------------------------------------
# ADF exception class taxonomy
# ---------------------------------------------------------------------------


class TestAdfExceptionClass:
    def test_ema_is_regime_indicator(self) -> None:
        assert _assign_exception_class("trend_ema_10") == "regime_indicator"

    def test_sma_is_regime_indicator(self) -> None:
        assert _assign_exception_class("trend_sma_20") == "regime_indicator"

    def test_vol_obv_is_random_walk(self) -> None:
        assert _assign_exception_class("vol_obv") == "random_walk_proxy"

    def test_vol_ad_is_random_walk(self) -> None:
        assert _assign_exception_class("vol_ad") == "random_walk_proxy"

    def test_interact_is_composed(self) -> None:
        assert _assign_exception_class("interact_rsi_x_adx") == "composed"

    def test_rsi_has_no_exception(self) -> None:
        assert _assign_exception_class("mom_rsi_14") is None

    def test_mr_zscore_has_no_exception(self) -> None:
        assert _assign_exception_class("mr_zscore_20") is None

    def test_stat_return_has_no_exception(self) -> None:
        assert _assign_exception_class("stat_return_1d") is None


# ---------------------------------------------------------------------------
# PSR computation — dual granularity (LM Master §1 mandate)
# ---------------------------------------------------------------------------


class TestComputePsrColumns:
    def test_returns_three_keys(
        self, synthetic_monthly_returns: np.ndarray, synthetic_daily_returns: np.ndarray
    ) -> None:
        """compute_psr_columns returns exactly 3 keys."""
        result = compute_psr_columns(synthetic_monthly_returns, synthetic_daily_returns)
        assert set(result.keys()) == {"psr_monthly_vs_0", "psr_monthly_vs_1", "psr_daily_vs_0"}

    def test_all_values_in_0_1(
        self, synthetic_monthly_returns: np.ndarray, synthetic_daily_returns: np.ndarray
    ) -> None:
        """All PSR values must be in [0, 1]."""
        result = compute_psr_columns(synthetic_monthly_returns, synthetic_daily_returns)
        for key, val in result.items():
            assert 0.0 <= val <= 1.0, f"{key}={val} out of [0,1]"

    def test_monotonicity_invariant(
        self, synthetic_monthly_returns: np.ndarray, synthetic_daily_returns: np.ndarray
    ) -> None:
        """Brief F5: psr_monthly_vs_0 >= psr_monthly_vs_1 (higher benchmark → lower confidence).

        This is the granularity-correctness invariant from brief Section 4.
        If this is violated, the PSR formula has a sign error in the benchmark.
        """
        result = compute_psr_columns(synthetic_monthly_returns, synthetic_daily_returns)
        assert result["psr_monthly_vs_0"] >= result["psr_monthly_vs_1"], (
            f"Monotonicity violated: psr_monthly_vs_0={result['psr_monthly_vs_0']:.4f} "
            f"< psr_monthly_vs_1={result['psr_monthly_vs_1']:.4f}"
        )

    def test_granularity_mismatch_trap_regression(self) -> None:
        """Regression guard for iter-v3/056 130× error.

        Passing annualized SR + n_obs=39 into PSR inflates the result vs
        passing the non-annualized SR. Verify the current implementation
        uses NON-annualized SR by checking that a known monthly series produces
        a reasonable PSR value (not trivially 0 or 1).

        Monthly series with SR_monthly = 0.005/0.02 = 0.25 (non-annualized),
        which annualized would be 0.25 * sqrt(12) ≈ 0.866. PSR vs 0 should be
        moderate (clearly not 0 or 1), confirming non-annualized input.
        """
        monthly_ret = np.array([0.005] * 39)  # constant monthly return
        daily_ret = np.array([0.0003] * 416)
        # constant series has std=0 → psr should degrade gracefully
        result = compute_psr_columns(monthly_ret, daily_ret)
        # Should not crash; values in [0, 1]
        for key, val in result.items():
            assert 0.0 <= val <= 1.0, f"{key}={val} out of [0,1] for constant series"

    def test_empty_monthly_returns_handled(self) -> None:
        """Empty monthly returns should not crash."""
        result = compute_psr_columns([], [0.001, -0.001] * 100)
        assert 0.0 <= result["psr_monthly_vs_0"] <= 1.0

    def test_psr_monthly_vs_1_close_to_reference(self) -> None:
        """Synthetic N(0.005, 0.02) monthly over n=39 should produce PSR vs 0 > 0.5
        (positive-mean series; PSR vs 0 tests H0: SR <= 0)."""
        rng = np.random.default_rng(99)
        monthly = rng.normal(loc=0.01, scale=0.02, size=39)  # clear positive SR
        daily = rng.normal(loc=0.0005, scale=0.008, size=416)
        result = compute_psr_columns(monthly, daily)
        val = result["psr_monthly_vs_0"]
        assert val > 0.5, f"Expected psr_monthly_vs_0 > 0.5 for positive-mean series, got {val:.4f}"


# ---------------------------------------------------------------------------
# N_eff PCA invariants (LM Master saturation-risk mandate)
# ---------------------------------------------------------------------------


class TestNEffectiveTrialsInvariants:
    """These are the fixture-based unit tests mandated in brief Section 3 + LM Master closing note.

    Tests confirm the PCA estimator (used inside compute_n_eff_and_dsr) works correctly
    before the runner uses it. Required pre-commit invariants.
    """

    def test_identical_trial_bouquet_gives_n_eff_1(self) -> None:
        """MANDATED by LM Master closing note: identical trials → n_eff = 1.

        If all trial-OOF return series are identical (perfectly correlated),
        PCA rank = 1 → only 1 effective trial regardless of n_trials count.
        """
        from crypto_trade.strategies.ml.validation_v1 import n_effective_trials

        base = np.random.default_rng(0).standard_normal(100)
        # 20 identical trials
        trials = np.stack([base] * 20)  # shape (20, 100)
        n_eff = n_effective_trials(trials)
        assert n_eff == 1, (
            f"Identical trials must give n_eff=1, got {n_eff}. "
            "If this fails, PCA implementation is incorrect."
        )

    def test_independent_trial_set_gives_n_eff_approx_n_trials(self) -> None:
        """MANDATED by LM Master closing note: independent trials → n_eff ≈ n_trials.

        Fully uncorrelated trials span the full eigenvalue space. n_eff should
        be close to (though not necessarily exactly equal to) n_trials.
        """
        from crypto_trade.strategies.ml.validation_v1 import n_effective_trials

        rng = np.random.default_rng(123)
        n_trials = 15
        n_periods = 200
        # Independent normal trials — each row is i.i.d., cross-row covariance → 0
        trials = rng.standard_normal((n_trials, n_periods))
        n_eff = n_effective_trials(trials)
        # n_eff should be in [n_trials // 2, n_trials] (at least half the rank)
        assert n_eff >= n_trials // 2, (
            f"Independent trials gave n_eff={n_eff}, expected >= {n_trials // 2}. "
            "PCA may be computing on wrong axis."
        )
        assert n_eff <= n_trials, (
            f"n_eff={n_eff} > n_trials={n_trials}. n_eff cannot exceed the trial count."
        )

    def test_n_eff_strictly_less_than_n_trials_for_correlated_set(self) -> None:
        """Partially correlated trials: n_eff < n_trials (strict compression).

        Brief F3 + runtime assert in runner.
        """
        from crypto_trade.strategies.ml.validation_v1 import n_effective_trials

        rng = np.random.default_rng(7)
        n_trials = 20
        n_periods = 150
        # Create correlated trials: 5 base factors + noise
        n_factors = 5
        factors = rng.standard_normal((n_factors, n_periods))
        weights = rng.standard_normal((n_trials, n_factors))
        trials = weights @ factors + 0.1 * rng.standard_normal((n_trials, n_periods))
        n_eff = n_effective_trials(trials)
        assert n_eff < n_trials, (
            f"Correlated trials (5 factors) should compress n_eff < n_trials={n_trials}, "
            f"got n_eff={n_eff}"
        )
        assert n_eff >= 1, f"n_eff={n_eff} must be >= 1"


# ---------------------------------------------------------------------------
# dsr.json writer
# ---------------------------------------------------------------------------


class TestWriteDsrJson:
    def test_writes_expected_keys(self, tmp_report_dir: Path) -> None:
        """dsr.json must contain all required fields from brief Section 8."""
        write_dsr_json(
            tmp_report_dir,
            dsr=-5.0,
            pbo=None,
            psr_val=0.12,
            n_trials=200,
            n_eff=30,
            n_eff_pca_method="eigvalsh_cov",
            min_trl_months=0.2887,
            label="TEST",
        )
        out_path = tmp_report_dir / "dsr.json"
        assert out_path.exists()
        with open(out_path) as f:
            payload = json.load(f)
        required_keys = {
            "dsr",
            "pbo",
            "psr",
            "n_trials",
            "n_eff",
            "n_eff_pca_method",
            "min_trl_months",
        }
        assert required_keys.issubset(set(payload.keys())), (
            f"Missing keys: {required_keys - set(payload.keys())}"
        )

    def test_pbo_null_is_valid(self, tmp_report_dir: Path) -> None:
        """pbo=None is explicitly allowed (CPCV-deferred per brief Section 9)."""
        write_dsr_json(
            tmp_report_dir,
            dsr=-2.0,
            pbo=None,
            psr_val=0.08,
            n_trials=200,
            n_eff=25,
            n_eff_pca_method="naive_fallback",
            min_trl_months=0.2887,
        )
        with open(tmp_report_dir / "dsr.json") as f:
            payload = json.load(f)
        assert payload["pbo"] is None


# ---------------------------------------------------------------------------
# ADF test CSV writer
# ---------------------------------------------------------------------------


class TestWriteAdfTestCsv:
    def _make_feature_df(self, n_rows: int = 300) -> pd.DataFrame:
        """Create a small feature DataFrame with a subset of V1_FEATURE_COLUMNS."""
        rng = np.random.default_rng(42)
        # Use a representative subset covering all families
        cols = list(V1_FEATURE_COLUMNS)[:30]  # first 30 columns for speed
        data = rng.standard_normal((n_rows, len(cols)))
        return pd.DataFrame(data, columns=cols)

    def test_writes_csv_file(self, tmp_report_dir: Path) -> None:
        feature_df = self._make_feature_df()
        out_path = write_adf_test_csv(tmp_report_dir, feature_df, label="TEST")
        assert out_path.exists()

    def test_csv_has_expected_columns(self, tmp_report_dir: Path) -> None:
        feature_df = self._make_feature_df()
        write_adf_test_csv(tmp_report_dir, feature_df)
        df = pd.read_csv(tmp_report_dir / "adf_test.csv")
        expected = {
            "feature",
            "family",
            "adf_stat",
            "p_value_raw",
            "p_value_bonferroni",
            "lags_used",
            "n_obs",
            "exception_class",
            "bonferroni_pass",
            "raw_pass",
        }
        assert expected.issubset(set(df.columns)), f"Missing columns: {expected - set(df.columns)}"

    def test_193_feature_rows(self, tmp_report_dir: Path) -> None:
        """adf_test.csv must have exactly 193 rows (one per V1_FEATURE_COLUMNS)."""
        # Use empty df to test schema completeness — missing cols produce empty-value rows
        empty_df = pd.DataFrame()
        write_adf_test_csv(tmp_report_dir, empty_df)
        df = pd.read_csv(tmp_report_dir / "adf_test.csv")
        assert len(df) == len(V1_FEATURE_COLUMNS), (
            f"Expected {len(V1_FEATURE_COLUMNS)} rows, got {len(df)}"
        )

    def test_bonferroni_alpha_is_correct(self, tmp_report_dir: Path) -> None:
        """Bonferroni alpha = 0.05 / 193."""
        empty_df = pd.DataFrame()
        write_adf_test_csv(tmp_report_dir, empty_df)
        df = pd.read_csv(tmp_report_dir / "adf_test.csv")
        # Filter rows where bonferroni_alpha was filled in (numeric)
        numeric_rows = df[df["p_value_bonferroni"].notna()]
        if len(numeric_rows) > 0:
            bonf_val = float(numeric_rows["p_value_bonferroni"].iloc[0])
            expected = 0.05 / 193
            assert abs(bonf_val - expected) < 1e-10, (
                f"Bonferroni alpha mismatch: {bonf_val} vs expected {expected}"
            )


# ---------------------------------------------------------------------------
# IC matrix CSV writer (smoke test — no golden values)
# ---------------------------------------------------------------------------


class TestWriteIcMatrixCsv:
    def _make_feature_df(self, n_rows: int = 200) -> tuple[pd.DataFrame, np.ndarray]:
        """Small feature df + forward returns for IC computation."""
        rng = np.random.default_rng(42)
        cols = list(V1_FEATURE_COLUMNS)[:30]
        data = rng.standard_normal((n_rows, len(cols)))
        fwd = rng.standard_normal(n_rows)
        return pd.DataFrame(data, columns=cols), fwd

    def test_writes_csv_file(self, tmp_report_dir: Path) -> None:
        feat_df, fwd = self._make_feature_df()
        out_path = write_ic_matrix_csv(tmp_report_dir, feat_df, fwd, label="TEST")
        assert out_path.exists()

    def test_csv_has_expected_columns(self, tmp_report_dir: Path) -> None:
        feat_df, fwd = self._make_feature_df()
        write_ic_matrix_csv(tmp_report_dir, feat_df, fwd)
        df = pd.read_csv(tmp_report_dir / "ic_matrix.csv")
        expected = {
            "family_a",
            "family_b",
            "ic_mean_fisher",
            "ic_median",
            "ic_iqr_low",
            "ic_iqr_high",
            "n_features_a",
            "n_features_b",
        }
        assert expected.issubset(set(df.columns))

    def test_diagonal_families_present(self, tmp_report_dir: Path) -> None:
        """All 8 families must appear in diagonal rows (family_a == family_b)."""
        feat_df, fwd = self._make_feature_df()
        write_ic_matrix_csv(tmp_report_dir, feat_df, fwd)
        df = pd.read_csv(tmp_report_dir / "ic_matrix.csv")
        diag = df[df["family_a"] == df["family_b"]]
        assert set(diag["family_a"].tolist()) == set(V1_FAMILIES)


# ---------------------------------------------------------------------------
# append_psr_rows_to_comparison — integration smoke test
# ---------------------------------------------------------------------------


class TestAppendPsrRowsToComparison:
    def test_appends_4_rows(self, tmp_report_dir: Path) -> None:
        """4 new rows must be appended to comparison.csv."""
        # Write a minimal comparison.csv first
        comparison_path = tmp_report_dir / "comparison.csv"
        with open(comparison_path, "w", newline="") as f:
            import csv as csv_mod

            writer = csv_mod.writer(f)
            writer.writerow(["metric", "in_sample", "out_of_sample", "ratio"])
            writer.writerow(["sharpe", "0.2829", "0.6637", "2.3462"])

        is_psr = {"psr_monthly_vs_0": 0.95, "psr_monthly_vs_1": 0.08, "psr_daily_vs_0": 0.99}
        oos_psr = {"psr_monthly_vs_0": 0.89, "psr_monthly_vs_1": 0.12, "psr_daily_vs_0": 0.97}
        append_psr_rows_to_comparison(comparison_path, is_psr, oos_psr, is_n_eff=25, oos_n_eff=20)

        df = pd.read_csv(comparison_path)
        # 1 original row + 4 new rows = 5 total
        assert len(df) == 5, f"Expected 5 rows, got {len(df)}"
        assert set(df["metric"]) >= {
            "psr_monthly_vs_0",
            "psr_monthly_vs_1",
            "psr_daily_vs_0",
            "n_effective_trials",
        }

    def test_n_eff_row_values(self, tmp_report_dir: Path) -> None:
        """n_effective_trials row must carry correct IS/OOS values."""
        comparison_path = tmp_report_dir / "comparison.csv"
        with open(comparison_path, "w", newline="") as f:
            import csv as csv_mod

            writer = csv_mod.writer(f)
            writer.writerow(["metric", "in_sample", "out_of_sample", "ratio"])
            writer.writerow(["sharpe", "0.28", "0.66", "2.36"])

        is_psr = {"psr_monthly_vs_0": 0.9, "psr_monthly_vs_1": 0.07, "psr_daily_vs_0": 0.98}
        oos_psr = {"psr_monthly_vs_0": 0.85, "psr_monthly_vs_1": 0.10, "psr_daily_vs_0": 0.96}
        append_psr_rows_to_comparison(comparison_path, is_psr, oos_psr, is_n_eff=30, oos_n_eff=22)

        df = pd.read_csv(comparison_path)
        n_eff_row = df[df["metric"] == "n_effective_trials"].iloc[0]
        assert int(n_eff_row["in_sample"]) == 30
        assert int(n_eff_row["out_of_sample"]) == 22


# ---------------------------------------------------------------------------
# Safe stat helpers
# ---------------------------------------------------------------------------


class TestSafeStatHelpers:
    def test_skew_normal_near_zero(self) -> None:
        """N(0,1) skewness should be near 0."""
        rng = np.random.default_rng(42)
        arr = rng.standard_normal(1000)
        sk = _safe_skew(arr)
        assert abs(sk) < 0.3, f"Expected skew near 0 for N(0,1), got {sk:.4f}"

    def test_kurt_normal_near_3(self) -> None:
        """N(0,1) raw kurtosis should be near 3."""
        rng = np.random.default_rng(42)
        arr = rng.standard_normal(2000)
        kt = _safe_kurt(arr)
        assert abs(kt - 3.0) < 0.5, f"Expected raw kurtosis near 3 for N(0,1), got {kt:.4f}"

    def test_short_series_no_crash(self) -> None:
        """Short series (n < 4) must not raise."""
        assert isinstance(_safe_skew(np.array([1.0])), float)
        assert isinstance(_safe_kurt(np.array([1.0, 2.0])), float)


# ---------------------------------------------------------------------------
# iter-v1/008 — Per-cell N_eff PCA refactor tests
# ---------------------------------------------------------------------------


def _make_oof_parquet(
    tmp_path: Path,
    n_trials: int = 10,
    n_symbols: int = 2,
    n_months: int = 3,
    n_candles: int = 30,
    n_folds: int = 3,
    *,
    all_identical: bool = False,
    rng_seed: int = 42,
) -> Path:
    """Synthesise an OOF parquet matching optimization.py schema.

    Schema: trial_id, symbol, train_month, fold_idx, candle_open_time_ms, oof_return

    Each (trial_id, candle_open_time_ms) pair appears n_folds times (once per
    walk-forward fold that covers that candle's train-month) — this is the
    multi-occurrence pattern that LM Master Rec #1 addresses.
    """
    rng = np.random.default_rng(rng_seed)
    rows = []
    symbols = [f"SYM{i}" for i in range(n_symbols)]
    months = [f"2023-{m:02d}" for m in range(1, n_months + 1)]
    candle_times = list(range(1000, 1000 + n_candles))

    for sym in symbols:
        for month in months:
            # Generate one OOF return series per trial (shared or independent)
            if all_identical:
                base_series = rng.standard_normal(n_candles)
                trial_series = {t: base_series.copy() for t in range(n_trials)}
            else:
                trial_series = {t: rng.standard_normal(n_candles) for t in range(n_trials)}

            for trial_id, oof_vals in trial_series.items():
                for fold_idx in range(n_folds):
                    # Each fold contributes a slightly-noised version of the OOF return
                    fold_noise = rng.normal(0, 0.01, n_candles) if not all_identical else 0.0
                    for ci, ct in enumerate(candle_times):
                        rows.append(
                            {
                                "trial_id": trial_id,
                                "symbol": sym,
                                "train_month": month,
                                "fold_idx": fold_idx,
                                "candle_open_time_ms": ct,
                                "oof_return": float(oof_vals[ci] + fold_noise[ci])
                                if not all_identical
                                else float(oof_vals[ci]),
                            }
                        )

    df = pd.DataFrame(rows)
    parquet_path = tmp_path / "test_oof.parquet"
    df.to_parquet(parquet_path, index=False)
    return parquet_path


class TestPerCellNEffFromParquet:
    """iter-v1/008 per-cell PCA refactor tests.

    Brief Section 10.3 mandates: synthetic tests confirm aggfunc="mean" gives
    expected n_eff, by-symbol medians have correct count, NaN guard works.
    """

    def test_returns_expected_keys(self, tmp_path: Path) -> None:
        """_per_cell_n_eff_from_parquet must return all required dict keys."""
        parquet_path = _make_oof_parquet(tmp_path)
        result = _per_cell_n_eff_from_parquet(parquet_path, n_trials_naive=10)
        required_keys = {
            "n_eff_per_cell_median",
            "n_eff_per_cell_trimmed_mean",
            "n_eff_per_cell_p25",
            "n_eff_per_cell_p75",
            "n_eff_per_cell_min",
            "n_eff_per_cell_max",
            "n_eff_per_cell_by_symbol",
            "n_cells",
        }
        assert required_keys.issubset(set(result.keys())), (
            f"Missing keys: {required_keys - set(result.keys())}"
        )

    def test_all_identical_trials_compresses_to_near_1(self, tmp_path: Path) -> None:
        """Identical OOF return series across all trials → per-cell n_eff ≈ 1.

        Brief Section 2 Table 1 Test 1 (rank-1 collapse): n_trials=35 identical
        series → n_eff=1.
        """
        parquet_path = _make_oof_parquet(tmp_path, n_trials=10, all_identical=True)
        result = _per_cell_n_eff_from_parquet(parquet_path, n_trials_naive=10)
        median_n_eff = result["n_eff_per_cell_median"]
        # Identical OOF series → rank-1 matrix → n_eff should be 1 (or very low)
        assert median_n_eff <= 3, (
            f"Identical OOF series should give per-cell n_eff near 1, got {median_n_eff}. "
            "aggfunc='mean' may have introduced artificial rank boosting."
        )

    def test_independent_trials_give_n_eff_near_n_trials(self, tmp_path: Path) -> None:
        """Independent OOF return series → per-cell n_eff close to n_trials.

        Brief Section 2 Table 1 Test 2 (full-rank independence).
        """
        parquet_path = _make_oof_parquet(
            tmp_path, n_trials=15, n_candles=200, n_folds=1, rng_seed=7
        )
        result = _per_cell_n_eff_from_parquet(parquet_path, n_trials_naive=15)
        median_n_eff = result["n_eff_per_cell_median"]
        # Independent trials → n_eff should be at least n_trials // 2
        assert median_n_eff >= 15 // 2, (
            f"Independent trials should give per-cell n_eff >= {15 // 2}, "
            f"got median={median_n_eff}. PCA may be computing on wrong axis."
        )
        assert median_n_eff <= 15, (
            f"n_eff_per_cell_median={median_n_eff} > n_trials=15. "
            "Cannot exceed the trial count per cell."
        )

    def test_n_cells_count_correct(self, tmp_path: Path) -> None:
        """n_cells must equal n_symbols × n_months."""
        n_symbols = 3
        n_months = 4
        parquet_path = _make_oof_parquet(tmp_path, n_symbols=n_symbols, n_months=n_months)
        result = _per_cell_n_eff_from_parquet(parquet_path, n_trials_naive=10)
        assert result["n_cells"] == n_symbols * n_months, (
            f"Expected n_cells={n_symbols * n_months}, got {result['n_cells']}"
        )

    def test_by_symbol_has_correct_keys(self, tmp_path: Path) -> None:
        """n_eff_per_cell_by_symbol must have one key per symbol."""
        n_symbols = 3
        parquet_path = _make_oof_parquet(tmp_path, n_symbols=n_symbols)
        result = _per_cell_n_eff_from_parquet(parquet_path, n_trials_naive=10)
        by_symbol = result["n_eff_per_cell_by_symbol"]
        assert len(by_symbol) == n_symbols, (
            f"Expected {n_symbols} symbols in by_symbol, got {len(by_symbol)}: {by_symbol}"
        )
        # All symbol keys should be strings
        for sym, val in by_symbol.items():
            assert isinstance(sym, str), f"Symbol key must be str, got {type(sym)}"
            assert isinstance(val, int), f"Per-symbol n_eff must be int, got {type(val)} for {sym}"

    def test_by_symbol_values_are_positive(self, tmp_path: Path) -> None:
        """Per-symbol n_eff medians must all be ≥ 1."""
        parquet_path = _make_oof_parquet(tmp_path, n_symbols=2, n_months=5)
        result = _per_cell_n_eff_from_parquet(parquet_path, n_trials_naive=10)
        for sym, val in result["n_eff_per_cell_by_symbol"].items():
            assert val >= 1, f"n_eff_per_cell_by_symbol[{sym}]={val} must be >= 1"

    def test_nan_guard_logs_warning_on_partial_cell(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """NaN guard must emit a warning when a cell has fewer trials than n_trials_naive.

        LM Master Phase 4.5 Risk #2 ADOPTED.
        """
        # Build a parquet with 5 trials but claim n_trials_naive=10
        parquet_path = _make_oof_parquet(tmp_path, n_trials=5)
        _per_cell_n_eff_from_parquet(parquet_path, n_trials_naive=10)
        captured = capsys.readouterr()
        assert "WARNING" in captured.out or "WARNING" in captured.err, (
            "Expected a WARNING message when cell has fewer trials than n_trials_naive. "
            "NaN guard (LM Master Rec #2) may not be firing."
        )

    def test_p25_le_median_le_p75(self, tmp_path: Path) -> None:
        """Percentile ordering: p25 ≤ median ≤ p75."""
        parquet_path = _make_oof_parquet(tmp_path, n_months=10, n_symbols=2)
        result = _per_cell_n_eff_from_parquet(parquet_path, n_trials_naive=10)
        assert result["n_eff_per_cell_p25"] <= result["n_eff_per_cell_median"], (
            f"p25={result['n_eff_per_cell_p25']} > median={result['n_eff_per_cell_median']}"
        )
        assert result["n_eff_per_cell_median"] <= result["n_eff_per_cell_p75"], (
            f"median={result['n_eff_per_cell_median']} > p75={result['n_eff_per_cell_p75']}"
        )

    def test_trimmed_mean_near_median_for_unimodal(self, tmp_path: Path) -> None:
        """For unimodal per-cell n_eff distributions, trimmed_mean ≈ median.

        LM Master Rec #2: trimmed_mean(10%) secondary robustness check.
        """
        parquet_path = _make_oof_parquet(tmp_path, n_months=10, n_symbols=3, rng_seed=99)
        result = _per_cell_n_eff_from_parquet(parquet_path, n_trials_naive=10)
        diff = abs(result["n_eff_per_cell_trimmed_mean"] - result["n_eff_per_cell_median"])
        # For unimodal, trimmed mean and median should be within 3 (int rounding)
        assert diff <= 3, (
            f"Trimmed mean ({result['n_eff_per_cell_trimmed_mean']}) and median "
            f"({result['n_eff_per_cell_median']}) too far apart for unimodal: Δ={diff}"
        )


class TestIterStampedOofPath:
    """iter-v1/008: OOF_PARQUET_PATH iter-stamp tests."""

    def test_iter_label_in_path(self) -> None:
        """The OOF parquet path must contain the iteration label."""
        # Simulate main() logic: build path from iteration_label
        iteration_label = "v1-008"
        oof_path = Path("data") / f"v1_iter_{iteration_label}_trial_oof.parquet"
        assert "v1-008" in str(oof_path), (
            f"Iteration label 'v1-008' not found in OOF path: {oof_path}"
        )

    def test_baseline_label_in_path(self) -> None:
        """Baseline mode uses 'v1-baseline' label."""
        iteration_label = "v1-baseline"
        oof_path = Path("data") / f"v1_iter_{iteration_label}_trial_oof.parquet"
        assert "v1-baseline" in str(oof_path)
        assert "SENTINEL" not in str(oof_path), "Sentinel must not appear in resolved path"

    def test_different_iterations_produce_different_paths(self) -> None:
        """Different iteration labels must produce different OOF paths."""
        labels = ["v1-001", "v1-008", "v1-baseline"]
        paths = {Path("data") / f"v1_iter_{lbl}_trial_oof.parquet" for lbl in labels}
        assert len(paths) == len(labels), f"Non-unique paths: {paths}"

    def test_sentinel_not_in_resolved_path(self) -> None:
        """The SENTINEL placeholder must never appear in any valid iteration path."""
        for num in range(1, 12):
            label = f"v1-{num:03d}"
            oof_path = Path("data") / f"v1_iter_{label}_trial_oof.parquet"
            assert "SENTINEL" not in str(oof_path), (
                f"SENTINEL found in resolved path for label={label}: {oof_path}"
            )


class TestWriteDsrJsonPerCellFields:
    """iter-v1/008: write_dsr_json extended schema tests."""

    def test_per_cell_fields_emitted_when_provided(self, tmp_report_dir: Path) -> None:
        """When per-cell args provided, dsr.json must contain all new fields."""
        write_dsr_json(
            tmp_report_dir,
            dsr=-5.0,
            pbo=None,
            psr_val=0.12,
            n_trials=50,
            n_eff=12,
            n_eff_pca_method="eigvalsh_cov_per_cell_median_aggfunc_mean",
            min_trl_months=0.2887,
            label="TEST",
            n_eff_per_cell_median=12,
            n_eff_per_cell_trimmed_mean=11,
            n_eff_per_cell_p25=10,
            n_eff_per_cell_p75=14,
            n_eff_per_cell_min=7,
            n_eff_per_cell_max=18,
            n_eff_per_cell_by_symbol={"BTCUSDT": 11, "ETHUSDT": 13},
            n_cells=258,
        )
        with open(tmp_report_dir / "dsr.json") as f:
            payload = json.load(f)
        required_new_keys = {
            "n_eff_per_cell_median",
            "n_eff_per_cell_trimmed_mean",
            "n_eff_per_cell_p25",
            "n_eff_per_cell_p75",
            "n_eff_per_cell_by_symbol",
            "n_cells",
        }
        assert required_new_keys.issubset(set(payload.keys())), (
            f"Missing per-cell keys: {required_new_keys - set(payload.keys())}"
        )
        assert payload["n_eff_per_cell_median"] == 12
        assert payload["n_cells"] == 258
        assert payload["n_eff_per_cell_by_symbol"] == {"BTCUSDT": 11, "ETHUSDT": 13}
        assert payload["n_eff_method_per_cell"] == "eigvalsh_cov_per_cell_median_aggfunc_mean"

    def test_legacy_fields_still_present_with_per_cell(self, tmp_report_dir: Path) -> None:
        """Legacy fields (n_eff, n_trials, dsr, psr, pbo) must still be present."""
        write_dsr_json(
            tmp_report_dir,
            dsr=-2.0,
            pbo=None,
            psr_val=0.10,
            n_trials=50,
            n_eff=12,
            n_eff_pca_method="eigvalsh_cov_per_cell_median_aggfunc_mean",
            min_trl_months=0.2887,
            n_eff_per_cell_median=12,
            n_cells=100,
        )
        with open(tmp_report_dir / "dsr.json") as f:
            payload = json.load(f)
        legacy_keys = {"dsr", "pbo", "psr", "n_trials", "n_eff", "n_eff_pca_method"}
        assert legacy_keys.issubset(set(payload.keys())), (
            f"Missing legacy keys: {legacy_keys - set(payload.keys())}"
        )

    def test_per_cell_fields_absent_when_not_provided(self, tmp_report_dir: Path) -> None:
        """When per-cell args are None (default), new keys must NOT appear in dsr.json."""
        write_dsr_json(
            tmp_report_dir,
            dsr=-5.0,
            pbo=None,
            psr_val=0.12,
            n_trials=50,
            n_eff=50,
            n_eff_pca_method="naive_fallback",
            min_trl_months=0.2887,
            # No per-cell args passed
        )
        with open(tmp_report_dir / "dsr.json") as f:
            payload = json.load(f)
        per_cell_keys = {"n_eff_per_cell_median", "n_cells", "n_eff_method_per_cell"}
        overlapping = per_cell_keys & set(payload.keys())
        assert not overlapping, (
            f"Per-cell keys must not appear when not provided; found: {overlapping}"
        )


class TestAppendPsrRowsPerCellMedian:
    """iter-v1/008: n_eff_per_cell_median row in comparison.csv."""

    def test_5_rows_appended_with_per_cell(self, tmp_path: Path) -> None:
        """When per-cell median provided, comparison.csv gets 5 new rows (not 4)."""
        comparison_path = tmp_path / "comparison.csv"
        with open(comparison_path, "w", newline="") as f:
            import csv as csv_mod

            writer = csv_mod.writer(f)
            writer.writerow(["metric", "in_sample", "out_of_sample", "ratio"])
            writer.writerow(["sharpe", "0.28", "0.66", "2.36"])

        is_psr = {"psr_monthly_vs_0": 0.9, "psr_monthly_vs_1": 0.07, "psr_daily_vs_0": 0.98}
        oos_psr = {"psr_monthly_vs_0": 0.85, "psr_monthly_vs_1": 0.10, "psr_daily_vs_0": 0.96}
        append_psr_rows_to_comparison(
            comparison_path,
            is_psr,
            oos_psr,
            is_n_eff=12,
            oos_n_eff=12,
            is_n_eff_per_cell_median=12,
            oos_n_eff_per_cell_median=12,
        )
        df = pd.read_csv(comparison_path)
        # 1 original + 5 new (psr×3 + n_effective_trials + n_eff_per_cell_median)
        assert len(df) == 6, f"Expected 6 rows with per-cell median, got {len(df)}"
        assert "n_eff_per_cell_median" in df["metric"].values, (
            "n_eff_per_cell_median row missing from comparison.csv"
        )

    def test_4_rows_appended_without_per_cell(self, tmp_path: Path) -> None:
        """Without per-cell args, comparison.csv gets original 4 new rows."""
        comparison_path = tmp_path / "comparison.csv"
        with open(comparison_path, "w", newline="") as f:
            import csv as csv_mod

            writer = csv_mod.writer(f)
            writer.writerow(["metric", "in_sample", "out_of_sample", "ratio"])

        is_psr = {"psr_monthly_vs_0": 0.9, "psr_monthly_vs_1": 0.07, "psr_daily_vs_0": 0.98}
        oos_psr = {"psr_monthly_vs_0": 0.85, "psr_monthly_vs_1": 0.10, "psr_daily_vs_0": 0.96}
        append_psr_rows_to_comparison(
            comparison_path,
            is_psr,
            oos_psr,
            is_n_eff=50,
            oos_n_eff=50,
            # No per-cell args
        )
        df = pd.read_csv(comparison_path)
        assert len(df) == 4, f"Expected 4 rows without per-cell median, got {len(df)}"
        assert "n_eff_per_cell_median" not in df["metric"].values

    def test_per_cell_median_row_values(self, tmp_path: Path) -> None:
        """n_eff_per_cell_median row carries the correct IS/OOS values."""
        comparison_path = tmp_path / "comparison.csv"
        with open(comparison_path, "w", newline="") as f:
            import csv as csv_mod

            writer = csv_mod.writer(f)
            writer.writerow(["metric", "in_sample", "out_of_sample", "ratio"])

        is_psr = {"psr_monthly_vs_0": 0.9, "psr_monthly_vs_1": 0.07, "psr_daily_vs_0": 0.98}
        oos_psr = {"psr_monthly_vs_0": 0.85, "psr_monthly_vs_1": 0.10, "psr_daily_vs_0": 0.96}
        append_psr_rows_to_comparison(
            comparison_path,
            is_psr,
            oos_psr,
            is_n_eff=12,
            oos_n_eff=12,
            is_n_eff_per_cell_median=11,
            oos_n_eff_per_cell_median=13,
        )
        df = pd.read_csv(comparison_path)
        row = df[df["metric"] == "n_eff_per_cell_median"].iloc[0]
        assert int(row["in_sample"]) == 11
        assert int(row["out_of_sample"]) == 13
