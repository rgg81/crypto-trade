"""Tests for iter-v1/063 methodology reporting graceful-skip-on-missing-OOF.

Covers:
- _run_methodology_reporting does NOT raise AssertionError when OOF parquet is missing.
- A WARNING line is printed when OOF parquet is None.
- A WARNING line is printed when OOF parquet path does not exist.
- Execution continues past the OOF check (function returns without raising).

The patch is in run_baseline_v1._run_methodology_reporting around the block
that previously did `assert oof_parquet_path is not None and Path(...).exists()`.
specialist_mode iterations produce ONE aggregated backtest from 50 seeds, so
oof_persist_path is never wired — the parquet is structurally absent.  The new
behaviour skips DSR/PBO/PSR and continues to ADF + IC.

Brief reference: iter-v1/063 post-backtest crash fix (oof_persist_path not wired).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_minimal_trade_result(open_time_ms: int, pnl: float = 10.0) -> Any:
    """Return a minimal TradeResult-like object sufficient for _run_methodology_reporting."""
    obj = MagicMock()
    obj.open_time = open_time_ms
    obj.pnl = pnl
    return obj


# ---------------------------------------------------------------------------
# Tests — Patch 1: graceful skip on missing OOF
# ---------------------------------------------------------------------------


def test_methodology_reporting_skip_when_oof_is_none(
    tmp_path: Path, capsys: Any
) -> None:
    """_run_methodology_reporting does not raise when oof_parquet_path=None."""
    from run_baseline_v1 import _run_methodology_reporting

    # Create minimal directory structure that the function tries to read.
    is_dir = tmp_path / "in_sample"
    oos_dir = tmp_path / "out_of_sample"
    iter_dir = tmp_path
    is_dir.mkdir()
    oos_dir.mkdir()

    # We need to stub out all the helpers that touch the filesystem.
    # The function will early-return after printing the warning, before any of
    # the heavy computation runs.  Patch the two leaf-level helpers so they
    # return no-op results without needing actual parquet files.
    with (
        patch("run_baseline_v1._load_features_for_adf_ic", return_value=None),
        patch("run_baseline_v1._compute_forward_returns", return_value=None),
        patch("run_baseline_v1.write_adf_test_csv"),
        patch("run_baseline_v1.write_ic_matrix_csv"),
    ):
        # Should NOT raise even though oof_parquet_path=None.
        _run_methodology_reporting(
            all_results=[],
            iter_dir=iter_dir,
            is_dir=is_dir,
            oos_dir=oos_dir,
            n_trials=30,
            symbols=("BTCUSDT",),
            features_dir=str(tmp_path),
            interval="8h",
            oof_parquet_path=None,
        )

    captured = capsys.readouterr()
    assert "WARNING" in captured.out, (
        "Expected a WARNING line when oof_parquet_path=None; got:\n" + captured.out
    )
    assert "DSR/PBO/PSR skipped" in captured.out, (
        "Expected 'DSR/PBO/PSR skipped' in WARNING output; got:\n" + captured.out
    )


def test_methodology_reporting_skip_when_oof_path_missing(
    tmp_path: Path, capsys: Any
) -> None:
    """_run_methodology_reporting does not raise when oof_parquet_path points to missing file."""
    from run_baseline_v1 import _run_methodology_reporting

    is_dir = tmp_path / "in_sample"
    oos_dir = tmp_path / "out_of_sample"
    iter_dir = tmp_path
    is_dir.mkdir()
    oos_dir.mkdir()

    nonexistent_path = tmp_path / "oof_data.parquet"
    assert not nonexistent_path.exists(), "Test setup: path must not exist"

    with (
        patch("run_baseline_v1._load_features_for_adf_ic", return_value=None),
        patch("run_baseline_v1._compute_forward_returns", return_value=None),
        patch("run_baseline_v1.write_adf_test_csv"),
        patch("run_baseline_v1.write_ic_matrix_csv"),
    ):
        _run_methodology_reporting(
            all_results=[],
            iter_dir=iter_dir,
            is_dir=is_dir,
            oos_dir=oos_dir,
            n_trials=30,
            symbols=("BTCUSDT",),
            features_dir=str(tmp_path),
            interval="8h",
            oof_parquet_path=nonexistent_path,
        )

    captured = capsys.readouterr()
    assert "WARNING" in captured.out, (
        "Expected a WARNING line when oof parquet path does not exist; got:\n" + captured.out
    )
    assert "DSR/PBO/PSR skipped" in captured.out, (
        "Expected 'DSR/PBO/PSR skipped' in WARNING output; got:\n" + captured.out
    )


def test_methodology_reporting_no_assertion_error_on_missing_oof(
    tmp_path: Path,
) -> None:
    """Regression: the old assert would crash after backtest completes — ensure it's gone."""
    from run_baseline_v1 import _run_methodology_reporting

    is_dir = tmp_path / "in_sample"
    oos_dir = tmp_path / "out_of_sample"
    iter_dir = tmp_path
    is_dir.mkdir()
    oos_dir.mkdir()

    ghost_path = tmp_path / "ghost.parquet"

    with (
        patch("run_baseline_v1._load_features_for_adf_ic", return_value=None),
        patch("run_baseline_v1._compute_forward_returns", return_value=None),
        patch("run_baseline_v1.write_adf_test_csv"),
        patch("run_baseline_v1.write_ic_matrix_csv"),
    ):
        try:
            _run_methodology_reporting(
                all_results=[],
                iter_dir=iter_dir,
                is_dir=is_dir,
                oos_dir=oos_dir,
                n_trials=30,
                symbols=("BTCUSDT",),
                features_dir=str(tmp_path),
                interval="8h",
                oof_parquet_path=ghost_path,
            )
        except AssertionError as exc:
            raise AssertionError(
                "AssertionError was raised — the graceful-skip patch was not applied correctly"
            ) from exc
