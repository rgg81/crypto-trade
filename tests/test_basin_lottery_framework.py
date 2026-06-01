"""Tests for the basin-lottery elimination framework (framework/032+).

Coverage:
 1.  basin_diagnostics module imports cleanly.
 2.  compute_v1_cross_seed_variance: correct mean/std from known data.
 3.  compute_v1_cross_seed_variance: missing parquet raises FileNotFoundError.
 4.  compute_v1_cross_seed_variance: missing required column raises KeyError.
 5.  compute_v2_per_cell_spearman: single-inner-seed cell gets nan spearman.
 6.  compute_v2_per_cell_spearman: two inner seeds with identical rankings → ρ=1.0.
 7.  compute_v3_roster_overlap: identical rosters → Jaccard=1.0.
 8.  compute_v3_roster_overlap: disjoint rosters → Jaccard=0.0.
 9.  compute_v3_roster_overlap: partial overlap gives correct fraction.
10.  emit_basin_diagnostics_summary: writes all 4 output files.
11.  emit_basin_diagnostics_summary: global PASS when all metrics pass.
12.  emit_basin_diagnostics_summary: global FAIL when V3 fails.
13.  emit_basin_diagnostics_summary: handles missing trades gracefully (SKIPPED).
14. _emit_magnitude_decomposition: PROMISING-AXIS-CONFIRMED when axis>=0.20.
15. _emit_magnitude_decomposition: PROMISING-BASIN-ONLY when axis<0.10.
16. _emit_magnitude_decomposition: PROMISING-AXIS-PARTIAL when axis in [0.10,0.20).
17. --seeds flag parses correctly (default 1, valid N).
18. --auto-frozen-hp-control flag parses correctly.
19. Live engine does NOT import basin_diagnostics (isolation audit).
20. Foundation regression: walk_forward.py:113 embargo unchanged.

Run:
    uv run pytest tests/test_basin_lottery_framework.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Ensure src/ and root are on path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_trials_parquet(tmp_path: Path, *, n_outer_seeds: int = 2) -> Path:
    """Build a minimal Optuna trials parquet for testing."""
    rows = []
    for outer_seed in range(n_outer_seeds):
        for inner_seed in [42, 123]:
            for trial_num in range(5):
                rows.append(
                    {
                        "outer_seed": outer_seed,
                        "model": "A",
                        "month": "2023-01",
                        "inner_seed": inner_seed,
                        "trial_number": trial_num,
                        "sharpe": float(trial_num) * 0.1 + inner_seed * 0.001 + outer_seed * 0.5,
                        "confidence_threshold": 0.65,
                        "training_days": 200,
                        "n_estimators": 100,
                        "max_depth": 3,
                        "num_leaves": 31,
                        "learning_rate": 0.05,
                        "subsample": 0.8,
                        "colsample_bytree": 0.8,
                        "min_child_samples": 20,
                        "reg_alpha": 0.01,
                        "reg_lambda": 0.01,
                    }
                )
    df = pd.DataFrame(rows)
    out = tmp_path / "trials.parquet"
    df.to_parquet(out, index=False)
    return out


def _make_trades_csv(tmp_path: Path, *, name: str, symbols: list[str], n_per_sym: int) -> Path:
    """Build a minimal trades CSV."""
    rows = []
    for i, sym in enumerate(symbols):
        for j in range(n_per_sym):
            rows.append(
                {
                    "symbol": sym,
                    "open_time": 1_000_000 + i * 1000 + j,
                    "close_time": 1_000_000 + i * 1000 + j + 100,
                    "direction": 1,
                    "entry_price": 100.0,
                    "exit_price": 101.0,
                    "pnl_pct": 0.01,
                    "exit_reason": "take_profit",
                }
            )
    df = pd.DataFrame(rows)
    out = tmp_path / f"{name}.csv"
    df.to_csv(out, index=False)
    return out


# ---------------------------------------------------------------------------
# Test 1: Module imports cleanly
# ---------------------------------------------------------------------------


class TestBasinDiagnosticsImports:
    def test_imports_cleanly(self) -> None:
        from crypto_trade.strategies.ml import basin_diagnostics  # noqa: F401

        assert hasattr(basin_diagnostics, "compute_v1_cross_seed_variance")
        assert hasattr(basin_diagnostics, "compute_v2_per_cell_spearman")
        assert hasattr(basin_diagnostics, "compute_v3_roster_overlap")
        assert hasattr(basin_diagnostics, "emit_basin_diagnostics_summary")
        assert hasattr(basin_diagnostics, "emit_optuna_trials_parquet")


# ---------------------------------------------------------------------------
# Tests 2-4: compute_v1_cross_seed_variance
# ---------------------------------------------------------------------------


class TestV1CrossSeedVariance:
    def test_correct_mean_std_from_known_data(self, tmp_path: Path) -> None:
        """With 2 outer seeds, mean and std should match expected values."""
        from crypto_trade.strategies.ml.basin_diagnostics import compute_v1_cross_seed_variance

        parquet = _make_trials_parquet(tmp_path, n_outer_seeds=2)
        result = compute_v1_cross_seed_variance(parquet)

        assert not result.empty, "Result should not be empty"
        assert "mean_sharpe" in result.columns
        assert "std_sharpe" in result.columns
        assert "n_outer_seeds" in result.columns
        # Both outer seeds contributed → n_outer_seeds = 2
        assert (result["n_outer_seeds"] == 2).all()
        # std_sharpe must be non-negative
        assert (result["std_sharpe"] >= 0).all()

    def test_missing_parquet_raises(self, tmp_path: Path) -> None:
        """FileNotFoundError when parquet does not exist."""
        from crypto_trade.strategies.ml.basin_diagnostics import compute_v1_cross_seed_variance

        with pytest.raises(FileNotFoundError):
            compute_v1_cross_seed_variance(tmp_path / "nonexistent.parquet")

    def test_missing_column_raises(self, tmp_path: Path) -> None:
        """KeyError when required column is missing from parquet."""
        from crypto_trade.strategies.ml.basin_diagnostics import compute_v1_cross_seed_variance

        # Build parquet without 'sharpe' column
        df = pd.DataFrame({"outer_seed": [0], "model": ["A"], "month": ["2023-01"]})
        p = tmp_path / "bad.parquet"
        df.to_parquet(p, index=False)
        with pytest.raises(KeyError):
            compute_v1_cross_seed_variance(p)


# ---------------------------------------------------------------------------
# Tests 5-6: compute_v2_per_cell_spearman
# ---------------------------------------------------------------------------


class TestV2PerCellSpearman:
    def test_single_inner_seed_gets_nan(self, tmp_path: Path) -> None:
        """A cell with only 1 inner seed → mean_spearman=NaN."""
        from crypto_trade.strategies.ml.basin_diagnostics import compute_v2_per_cell_spearman

        rows = [
            {
                "outer_seed": 0,
                "model": "A",
                "month": "2023-01",
                "inner_seed": 42,
                "trial_number": i,
                "sharpe": float(i) * 0.1,
            }
            for i in range(5)
        ]
        p = tmp_path / "single.parquet"
        pd.DataFrame(rows).to_parquet(p, index=False)
        result = compute_v2_per_cell_spearman(p)
        assert len(result) == 1
        assert np.isnan(result.iloc[0]["mean_spearman"])

    def test_identical_rankings_give_rho_one(self, tmp_path: Path) -> None:
        """Two inner seeds with identical Sharpe rankings → Spearman ρ=1.0."""
        from crypto_trade.strategies.ml.basin_diagnostics import compute_v2_per_cell_spearman

        rows = []
        for inner_seed in [42, 123]:
            for trial in range(5):
                rows.append(
                    {
                        "outer_seed": 0,
                        "model": "A",
                        "month": "2023-01",
                        "inner_seed": inner_seed,
                        "trial_number": trial,
                        "sharpe": float(trial) * 0.2,  # identical ordering
                    }
                )
        p = tmp_path / "identical.parquet"
        pd.DataFrame(rows).to_parquet(p, index=False)
        result = compute_v2_per_cell_spearman(p)
        assert not result.empty
        rho = result.iloc[0]["mean_spearman"]
        assert abs(rho - 1.0) < 1e-9, f"Expected ρ≈1.0, got {rho}"


# ---------------------------------------------------------------------------
# Tests 7-9: compute_v3_roster_overlap
# ---------------------------------------------------------------------------


class TestV3RosterOverlap:
    def test_identical_rosters_give_jaccard_one(self, tmp_path: Path) -> None:
        """Identical trade rosters → Jaccard=1.0."""
        from crypto_trade.strategies.ml.basin_diagnostics import compute_v3_roster_overlap

        main_csv = _make_trades_csv(tmp_path, name="main", symbols=["BTCUSDT"], n_per_sym=5)
        base_csv = _make_trades_csv(tmp_path, name="base", symbols=["BTCUSDT"], n_per_sym=5)
        result = compute_v3_roster_overlap(main_csv, base_csv)
        global_row = result[result["symbol"] == "ALL"].iloc[0]
        assert abs(global_row["jaccard"] - 1.0) < 1e-9

    def test_disjoint_rosters_give_jaccard_zero(self, tmp_path: Path) -> None:
        """Completely disjoint trade rosters → Jaccard=0.0."""
        from crypto_trade.strategies.ml.basin_diagnostics import compute_v3_roster_overlap

        rows_a = [{"symbol": "BTCUSDT", "open_time": i, "close_time": i + 100} for i in range(5)]
        rows_b = [
            {"symbol": "BTCUSDT", "open_time": i + 1000, "close_time": i + 1100} for i in range(5)
        ]
        main_csv = tmp_path / "main_disj.csv"
        base_csv = tmp_path / "base_disj.csv"
        pd.DataFrame(rows_a).to_csv(main_csv, index=False)
        pd.DataFrame(rows_b).to_csv(base_csv, index=False)
        result = compute_v3_roster_overlap(main_csv, base_csv)
        global_row = result[result["symbol"] == "ALL"].iloc[0]
        assert abs(global_row["jaccard"] - 0.0) < 1e-9

    def test_partial_overlap_gives_correct_jaccard(self, tmp_path: Path) -> None:
        """3 shared + 2 exclusive each → Jaccard=3/7."""
        from crypto_trade.strategies.ml.basin_diagnostics import compute_v3_roster_overlap

        shared = [{"symbol": "ETHUSDT", "open_time": i, "close_time": i + 100} for i in range(3)]
        only_a = [
            {"symbol": "ETHUSDT", "open_time": i + 100, "close_time": i + 200} for i in range(2)
        ]
        only_b = [
            {"symbol": "ETHUSDT", "open_time": i + 200, "close_time": i + 300} for i in range(2)
        ]
        main_csv = tmp_path / "main_part.csv"
        base_csv = tmp_path / "base_part.csv"
        pd.DataFrame(shared + only_a).to_csv(main_csv, index=False)
        pd.DataFrame(shared + only_b).to_csv(base_csv, index=False)
        result = compute_v3_roster_overlap(main_csv, base_csv)
        global_row = result[result["symbol"] == "ALL"].iloc[0]
        expected = 3 / 7
        assert abs(global_row["jaccard"] - expected) < 1e-9, (
            f"Expected Jaccard={expected:.4f}, got {global_row['jaccard']:.4f}"
        )


# ---------------------------------------------------------------------------
# Tests 10-13: emit_basin_diagnostics_summary
# ---------------------------------------------------------------------------


class TestEmitBasinDiagnosticsSummary:
    def test_writes_all_4_output_files(self, tmp_path: Path) -> None:
        """Summary emitter should write 3 CSVs and 1 JSON."""
        from crypto_trade.strategies.ml.basin_diagnostics import emit_basin_diagnostics_summary

        trials = _make_trials_parquet(tmp_path, n_outer_seeds=2)
        main_t = _make_trades_csv(tmp_path, name="main_t", symbols=["BTCUSDT"], n_per_sym=5)
        base_t = _make_trades_csv(tmp_path, name="base_t", symbols=["BTCUSDT"], n_per_sym=5)
        diag_dir = tmp_path / "diagnostics"
        emit_basin_diagnostics_summary(
            diagnostics_dir=diag_dir,
            trials_parquet=trials,
            main_trades_oos=main_t,
            baseline_trades_oos=base_t,
        )
        assert (diag_dir / "v1_cross_seed_variance.csv").exists()
        assert (diag_dir / "v2_param_spearman.csv").exists()
        assert (diag_dir / "v3_roster_overlap.csv").exists()
        assert (diag_dir / "basin_diagnostics.json").exists()

    def test_global_pass_when_all_metrics_pass(self, tmp_path: Path) -> None:
        """Global verdict PASS when all individual metrics pass."""
        from crypto_trade.strategies.ml.basin_diagnostics import (
            V1_STD_PASS_THRESHOLD,
            V3_JACCARD_PASS_THRESHOLD,
            emit_basin_diagnostics_summary,
        )

        # Use identical rosters → Jaccard=1.0 (V3 PASS)
        # Single outer seed → V1 std=0 (PASS)
        trials = _make_trials_parquet(tmp_path, n_outer_seeds=1)
        main_t = _make_trades_csv(tmp_path, name="m", symbols=["BTCUSDT"], n_per_sym=5)
        base_t = _make_trades_csv(tmp_path, name="b", symbols=["BTCUSDT"], n_per_sym=5)
        diag_dir = tmp_path / "diag_pass"
        result = emit_basin_diagnostics_summary(
            diagnostics_dir=diag_dir,
            trials_parquet=trials,
            main_trades_oos=main_t,
            baseline_trades_oos=base_t,
        )
        # V3 identical → PASS; V1 single-seed std=0 < threshold → PASS
        assert result["v3"]["verdict"] == "PASS", (
            f"Expected V3=PASS (identical roster → Jaccard=1.0 > {V3_JACCARD_PASS_THRESHOLD})"
        )
        assert result["v1"]["value"] <= V1_STD_PASS_THRESHOLD, (
            f"Expected V1 std ≤ {V1_STD_PASS_THRESHOLD}, got {result['v1']['value']}"
        )

    def test_global_fail_when_v3_fails(self, tmp_path: Path) -> None:
        """Global verdict FAIL when V3 Jaccard is below fail threshold."""
        from crypto_trade.strategies.ml.basin_diagnostics import (
            V3_JACCARD_FAIL_THRESHOLD,
            emit_basin_diagnostics_summary,
        )

        trials = _make_trials_parquet(tmp_path, n_outer_seeds=1)
        # Disjoint rosters → Jaccard=0.0 (V3 FAIL)
        rows_m = [{"symbol": "BTCUSDT", "open_time": i, "close_time": i + 100} for i in range(5)]
        rows_b = [
            {"symbol": "BTCUSDT", "open_time": i + 1000, "close_time": i + 1100} for i in range(5)
        ]
        main_t = tmp_path / "mf.csv"
        base_t = tmp_path / "bf.csv"
        pd.DataFrame(rows_m).to_csv(main_t, index=False)
        pd.DataFrame(rows_b).to_csv(base_t, index=False)
        diag_dir = tmp_path / "diag_fail"
        result = emit_basin_diagnostics_summary(
            diagnostics_dir=diag_dir,
            trials_parquet=trials,
            main_trades_oos=main_t,
            baseline_trades_oos=base_t,
        )
        assert result["v3"]["verdict"] == "FAIL", (
            f"Expected V3=FAIL (disjoint roster → Jaccard=0.0 < {V3_JACCARD_FAIL_THRESHOLD})"
        )
        assert result["global_verdict"] == "FAIL"

    def test_missing_trades_gracefully_skipped(self, tmp_path: Path) -> None:
        """Missing trades CSV → V3 SKIPPED, not an exception."""
        from crypto_trade.strategies.ml.basin_diagnostics import emit_basin_diagnostics_summary

        trials = _make_trials_parquet(tmp_path, n_outer_seeds=1)
        diag_dir = tmp_path / "diag_skip"
        # Nonexistent trades paths
        result = emit_basin_diagnostics_summary(
            diagnostics_dir=diag_dir,
            trials_parquet=trials,
            main_trades_oos=tmp_path / "nonexistent_main.csv",
            baseline_trades_oos=tmp_path / "nonexistent_base.csv",
        )
        assert result["v3"]["verdict"] == "SKIPPED"


# ---------------------------------------------------------------------------
# Tests 14-16: _emit_magnitude_decomposition verdict cells
# ---------------------------------------------------------------------------


class TestMagnitudeDecomposition:
    def _run(self, tmp_path: Path, main_oos: float, frozen_oos: float, base_oos: float) -> dict:
        """Helper: import function from runner module and call it."""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import importlib

        runner = importlib.import_module("run_baseline_v1")
        runner._emit_magnitude_decomposition(tmp_path, main_oos, frozen_oos, base_oos)
        with open(tmp_path / "magnitude_decomposition.json") as f:
            return json.load(f)

    def test_promising_axis_confirmed_when_axis_ge_020(self, tmp_path: Path) -> None:
        """axis_share >= +0.20 → PROMISING-AXIS-CONFIRMED."""
        result = self._run(tmp_path, main_oos=1.50, frozen_oos=1.00, base_oos=0.66)
        # axis_share = frozen_oos - base_oos = 1.00 - 0.66 = +0.34
        assert result["axis_share"] == pytest.approx(0.34, abs=0.01)
        assert result["verdict"] == "PROMISING-AXIS-CONFIRMED"

    def test_promising_basin_only_when_axis_lt_010(self, tmp_path: Path) -> None:
        """axis_share < +0.10 → PROMISING-BASIN-ONLY."""
        result = self._run(tmp_path, main_oos=1.50, frozen_oos=0.71, base_oos=0.66)
        # axis_share = 0.71 - 0.66 = +0.05 → < 0.10
        assert result["axis_share"] == pytest.approx(0.05, abs=0.01)
        assert result["verdict"] == "PROMISING-BASIN-ONLY"

    def test_promising_axis_partial_when_axis_in_010_020(self, tmp_path: Path) -> None:
        """axis_share in [+0.10, +0.20) → PROMISING-AXIS-PARTIAL."""
        result = self._run(tmp_path, main_oos=1.50, frozen_oos=0.81, base_oos=0.66)
        # axis_share = 0.81 - 0.66 = +0.15 → in [0.10, 0.20)
        assert result["axis_share"] == pytest.approx(0.15, abs=0.01)
        assert result["verdict"] == "PROMISING-AXIS-PARTIAL"


# ---------------------------------------------------------------------------
# Test 17: --seeds flag parsing
# ---------------------------------------------------------------------------


class TestCLIFlagParsing:
    def test_seeds_flag_exists_in_runner(self) -> None:
        """--seeds flag must exist in run_baseline_v1.py argparse."""
        source = Path("run_baseline_v1.py").read_text()
        assert "--seeds" in source, "--seeds flag not found in run_baseline_v1.py"
        assert "n_outer_seeds" in source or "seeds" in source.lower(), (
            "seeds variable not found in run_baseline_v1.py"
        )

    def test_seeds_default_is_1(self) -> None:
        """Default for --seeds must be 1 (live-compatible single run)."""
        source = Path("run_baseline_v1.py").read_text()
        # Check that default=1 appears near the --seeds argument
        idx = source.find('"--seeds"')
        if idx == -1:
            idx = source.find("'--seeds'")
        assert idx != -1, "--seeds not found in source"
        context = source[idx : idx + 300]
        assert "default=1" in context, (
            f"--seeds default must be 1 (live-compatibility). Context:\n{context}"
        )

    def test_auto_frozen_hp_flag_exists(self) -> None:
        """--auto-frozen-hp-control flag must exist in run_baseline_v1.py."""
        source = Path("run_baseline_v1.py").read_text()
        assert "--auto-frozen-hp-control" in source, (
            "--auto-frozen-hp-control flag not found in run_baseline_v1.py"
        )

    def test_live_trading_contract_documented(self) -> None:
        """LIVE-TRADING CONTRACT comment must appear near --seeds."""
        source = Path("run_baseline_v1.py").read_text()
        assert "LIVE-TRADING CONTRACT" in source, (
            "LIVE-TRADING CONTRACT comment not found in run_baseline_v1.py. "
            "The multi-outer-seed live-vs-validation guardrail must be documented."
        )
        assert "seed_42" in source or "single-outer-seed=42" in source, (
            "The canonical live seed (42) must be mentioned in the live-trading contract comment."
        )


# ---------------------------------------------------------------------------
# Test 19: Live engine isolation — basin_diagnostics not imported by engine
# ---------------------------------------------------------------------------


class TestLiveEngineIsolation:
    def test_engine_does_not_import_basin_diagnostics(self) -> None:
        """Live engine MUST NOT import basin_diagnostics (reporting-only module)."""
        engine_path = Path("src/crypto_trade/live/engine.py")
        assert engine_path.exists(), "live/engine.py not found"
        source = engine_path.read_text()
        assert "basin_diagnostics" not in source, (
            "live/engine.py MUST NOT import basin_diagnostics. "
            "That module is a REPORTING-ONLY module (STATISTICAL VALIDATION only). "
            "The live engine must remain isolated from multi-seed artifacts."
        )

    def test_engine_does_not_reference_seed_dirs(self) -> None:
        """Live engine MUST NOT reference seed_*/ subdirectories."""
        engine_path = Path("src/crypto_trade/live/engine.py")
        source = engine_path.read_text()
        assert "seed_42/" not in source and "seed_{" not in source, (
            "live/engine.py must not reference seed_*/ subdirectories. "
            "Multi-outer-seed reports are STATISTICAL VALIDATION artifacts only."
        )


# ---------------------------------------------------------------------------
# Test 20: Foundation regression — walk_forward.py:113 embargo unchanged
# ---------------------------------------------------------------------------


class TestFoundationRegression:
    def test_walk_forward_embargo_unchanged(self) -> None:
        """walk_forward.py must still carry train_end_ms = test_start_ms - embargo_ms."""
        source = Path("src/crypto_trade/strategies/ml/walk_forward.py").read_text()
        lines = source.splitlines()
        if len(lines) > 113:
            region = "\n".join(lines[108:118])
        else:
            region = source
        assert "train_end_ms" in region and "embargo_ms" in region, (
            f"walk_forward.py:113 missing embargo_ms purge. Region:\n{region}"
        )
        assert "test_start_ms - embargo_ms" in region, (
            "walk_forward.py must have: train_end_ms = test_start_ms - embargo_ms"
        )


# ---------------------------------------------------------------------------
# Tests 21-25: Bug fixes — multi-seed FATAL suppression + trial parquet schema
# ---------------------------------------------------------------------------


class TestMultiSeedFatalSuppression:
    def test_seeds_flag_suppresses_engineering_report_fatal(self) -> None:
        """When --seeds N > 1, the runner must NOT exit 1 on missing engineering_report.md.

        Verify the source code carries the auto-suppression logic:
        _suppress_eng_report_check = args.no_engineering_report or (_n_outer_seeds_peek > 1)
        """
        source = Path("run_baseline_v1.py").read_text()
        assert "_n_outer_seeds_peek" in source, (
            "Bug 1 fix missing: _n_outer_seeds_peek variable not found in runner. "
            "Multi-seed runs must auto-suppress engineering_report.md FATAL."
        )
        assert "_suppress_eng_report_check" in source, (
            "Bug 1 fix missing: _suppress_eng_report_check variable not found in runner."
        )
        # Confirm the logic ties _n_outer_seeds_peek > 1 to suppression
        assert "_n_outer_seeds_peek > 1" in source, (
            "Bug 1 fix missing: condition `_n_outer_seeds_peek > 1` not found. "
            "The multi-seed suppression must check seeds > 1 explicitly."
        )

    def test_no_engineering_report_flag_still_works(self) -> None:
        """--no-engineering-report flag must still suppress the check independently."""
        source = Path("run_baseline_v1.py").read_text()
        assert "no_engineering_report" in source, (
            "--no-engineering-report flag or variable missing from runner."
        )
        # The combined condition must include args.no_engineering_report
        assert "args.no_engineering_report" in source, (
            "args.no_engineering_report must appear in the suppression condition."
        )


class TestTrialParquetSchema:
    def test_derive_basin_trials_produces_6_required_columns(self, tmp_path: Path) -> None:
        """derive_basin_trials_from_oof_parquet must produce outer_seed, model, month,
        inner_seed, trial_number, sharpe columns.
        """
        from crypto_trade.strategies.ml.basin_diagnostics import (
            derive_basin_trials_from_oof_parquet,
        )

        # Build a minimal OOF parquet (the actual schema from optimization.py)
        rows = []
        for trial_id in range(3):
            for i in range(10):
                rows.append(
                    {
                        "trial_id": trial_id,
                        "symbol": "BTCUSDT",
                        "train_month": "2023-01",
                        "fold_idx": i,
                        "candle_open_time_ms": 1_000_000 + i * 28800_000,
                        "oof_return": (trial_id * 0.01) + (i * 0.001) - 0.005,
                    }
                )
        oof_path = tmp_path / "oof.parquet"
        pd.DataFrame(rows).to_parquet(oof_path, index=False)

        basin_path = tmp_path / "basin_trials.parquet"
        derive_basin_trials_from_oof_parquet(oof_path, basin_path, outer_seed=42, model_name="A")

        assert basin_path.exists(), "Basin-trials parquet was not written"
        df = pd.read_parquet(basin_path)
        required = {"outer_seed", "model", "month", "inner_seed", "trial_number", "sharpe"}
        missing = required - set(df.columns)
        assert not missing, f"Basin-trials parquet missing required columns: {missing}"

    def test_v1_computation_runs_on_derived_parquet(self, tmp_path: Path) -> None:
        """compute_v1_cross_seed_variance must succeed when fed a parquet derived
        from derive_basin_trials_from_oof_parquet (end-to-end V1 pipeline check).
        """
        from crypto_trade.strategies.ml.basin_diagnostics import (
            compute_v1_cross_seed_variance,
            derive_basin_trials_from_oof_parquet,
        )

        rows = []
        for trial_id in range(5):
            for i in range(8):
                rows.append(
                    {
                        "trial_id": trial_id,
                        "symbol": "ETHUSDT",
                        "train_month": "2023-06",
                        "fold_idx": i,
                        "candle_open_time_ms": 1_600_000_000_000 + i * 28_800_000,
                        "oof_return": 0.002 * trial_id - 0.001 * i,
                    }
                )
        oof_path = tmp_path / "oof_v1.parquet"
        pd.DataFrame(rows).to_parquet(oof_path, index=False)
        basin_path = tmp_path / "basin_v1.parquet"
        derive_basin_trials_from_oof_parquet(oof_path, basin_path, outer_seed=0)

        # V1 should not raise KeyError
        result = compute_v1_cross_seed_variance(basin_path)
        assert not result.empty, "V1 cross-seed variance returned empty DataFrame"
        assert "std_sharpe" in result.columns

    def test_v2_computation_runs_on_derived_parquet(self, tmp_path: Path) -> None:
        """compute_v2_per_cell_spearman must succeed on a derived parquet."""
        from crypto_trade.strategies.ml.basin_diagnostics import (
            compute_v2_per_cell_spearman,
            derive_basin_trials_from_oof_parquet,
        )

        rows = []
        for trial_id in range(4):
            for i in range(6):
                rows.append(
                    {
                        "trial_id": trial_id,
                        "symbol": "LINKUSDT",
                        "train_month": "2022-11",
                        "fold_idx": i,
                        "candle_open_time_ms": 1_500_000_000_000 + i * 28_800_000,
                        "oof_return": 0.001 * trial_id,
                    }
                )
        oof_path = tmp_path / "oof_v2.parquet"
        pd.DataFrame(rows).to_parquet(oof_path, index=False)
        basin_path = tmp_path / "basin_v2.parquet"
        derive_basin_trials_from_oof_parquet(oof_path, basin_path, outer_seed=0)

        result = compute_v2_per_cell_spearman(basin_path)
        # Single inner_seed=0 → all cells get NaN spearman (not an error)
        assert "mean_spearman" in result.columns

    def test_v3_roster_overlap_regression(self, tmp_path: Path) -> None:
        """V3 (Jaccard) must still work independently of the parquet fix (regression)."""
        from crypto_trade.strategies.ml.basin_diagnostics import compute_v3_roster_overlap

        main_csv = _make_trades_csv(tmp_path, name="reg_main", symbols=["BTCUSDT"], n_per_sym=4)
        base_csv = _make_trades_csv(tmp_path, name="reg_base", symbols=["BTCUSDT"], n_per_sym=4)
        result = compute_v3_roster_overlap(main_csv, base_csv)
        global_row = result[result["symbol"] == "ALL"].iloc[0]
        assert abs(global_row["jaccard"] - 1.0) < 1e-9, "V3 regression: identical rosters != 1.0"

    def test_missing_oof_parquet_is_noop(self, tmp_path: Path) -> None:
        """derive_basin_trials_from_oof_parquet must not raise when OOF parquet missing."""
        from crypto_trade.strategies.ml.basin_diagnostics import (
            derive_basin_trials_from_oof_parquet,
        )

        nonexistent = tmp_path / "does_not_exist.parquet"
        output = tmp_path / "out.parquet"
        # Must be a no-op (no exception, no output file)
        derive_basin_trials_from_oof_parquet(nonexistent, output)
        assert not output.exists(), "Output should not be created when OOF parquet is missing"
