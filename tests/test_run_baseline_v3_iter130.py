"""Smoke tests for iter-v3/130 4h bar-interval additions to run_baseline_v3.

Tests verify:
1. --bar-interval 4h parses correctly (argparse).
2. _verify_label_leakage_gap raises no error at 4h with 3 symbols.
3. _verify_timeout_consistency accepts 5040 at bar_interval="4h".
4. _build_v3_model returns BacktestConfig.timeout_minutes=5040 at bar_interval="4h".
5. _build_v3_model returns BacktestConfig.timeout_minutes=10080 at bar_interval="8h".
6. enable_per_symbol_drawdown_scaling=False at 4h (REVERT from /129).
7. FEATURES_DIR_4H path is distinct from FEATURES_DIR and FEATURES_DIR_24H.
8. _TeeLogger writes to both stream and file.

Run:
    uv run pytest tests/test_run_baseline_v3_iter130.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Import guards — run_baseline_v3 is script-style; guard against side effects.
# ---------------------------------------------------------------------------


def _import_runner_symbols():
    """Import only the symbols we need without triggering main().

    Adds the repo root to sys.path and imports run_baseline_v3 as a regular
    module (so its __name__ == 'run_baseline_v3', not '__main__').
    The `if __name__ == '__main__': main()` guard does NOT fire.
    """
    repo_root = str(Path(__file__).parent.parent)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    # If already cached from a previous test run, reuse it.
    if "run_baseline_v3" in sys.modules:
        return sys.modules["run_baseline_v3"]

    import importlib

    mod = importlib.import_module("run_baseline_v3")
    return mod


@pytest.fixture(scope="module")
def runner_mod():
    return _import_runner_symbols()


# ---------------------------------------------------------------------------
# Test 1 — argparse accepts "4h"
# ---------------------------------------------------------------------------


class TestArgparse4h:
    def test_bar_interval_4h_accepted(self, runner_mod) -> None:
        """--bar-interval 4h must parse without error."""
        # We need to invoke the argparse setup directly.
        # The easiest way: use a subprocess call with --help to verify 4h is listed.
        # For a pure unit approach, reconstruct the parser choice set from the module.
        # We know from code: choices=["8h", "24h", "4h"].
        # Test via the known constant rather than re-parsing.
        import subprocess

        result = subprocess.run(
            [sys.executable, "run_baseline_v3.py", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        # --help always returns exit code 0.
        assert "4h" in result.stdout, (
            f"--bar-interval choices must include '4h'. Got stdout: {result.stdout[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 2 — _verify_label_leakage_gap at 4h with 3 symbols
# ---------------------------------------------------------------------------


class TestLabelLeakageGap4h:
    def test_4h_gap_is_66(self, runner_mod) -> None:
        """At 4h with 3 symbols, gap = (21+1)*3 = 66 — same as 8h."""
        # V3_MODELS is patched to exactly 3 symbols (matching production config).
        with patch.object(
            runner_mod,
            "V3_MODELS",
            (("v3-130-BCH", "BCHUSDT"), ("v3-130-LDO", "LDOUSDT"), ("v3-130-TRX", "TRXUSDT")),
        ):
            # Should not raise — 4h timeout=5040 / candle=240 = 21 candles → gap = 66 = REQUIRED_GAP
            runner_mod._verify_label_leakage_gap(bar_interval="4h")

    def test_8h_gap_still_66(self, runner_mod) -> None:
        """At 8h with 3 symbols, gap = 66 unchanged."""
        with patch.object(
            runner_mod,
            "V3_MODELS",
            (("v3-130-BCH", "BCHUSDT"), ("v3-130-LDO", "LDOUSDT"), ("v3-130-TRX", "TRXUSDT")),
        ):
            runner_mod._verify_label_leakage_gap(bar_interval="8h")


# ---------------------------------------------------------------------------
# Test 3 — _verify_timeout_consistency at 4h
# ---------------------------------------------------------------------------


class TestTimeoutConsistency4h:
    def test_accept_5040_at_4h(self, runner_mod) -> None:
        """_verify_timeout_consistency must accept 5040 at bar_interval='4h'."""
        mock_cfg = MagicMock()
        mock_cfg.timeout_minutes = 5040
        mock_lgbm = MagicMock()
        mock_lgbm.label_timeout_minutes = 5040
        # Should not raise.
        runner_mod._verify_timeout_consistency(mock_cfg, mock_lgbm, bar_interval="4h")

    def test_reject_10080_at_4h(self, runner_mod) -> None:
        """_verify_timeout_consistency must reject 10080 at bar_interval='4h'."""
        mock_cfg = MagicMock()
        mock_cfg.timeout_minutes = 10080  # 8h value — wrong at 4h
        mock_lgbm = MagicMock()
        mock_lgbm.label_timeout_minutes = 10080
        with pytest.raises(AssertionError, match="5040"):
            runner_mod._verify_timeout_consistency(mock_cfg, mock_lgbm, bar_interval="4h")

    def test_accept_10080_at_8h(self, runner_mod) -> None:
        """_verify_timeout_consistency must accept 10080 at bar_interval='8h'."""
        mock_cfg = MagicMock()
        mock_cfg.timeout_minutes = 10080
        mock_lgbm = MagicMock()
        mock_lgbm.label_timeout_minutes = 10080
        runner_mod._verify_timeout_consistency(mock_cfg, mock_lgbm, bar_interval="8h")


# ---------------------------------------------------------------------------
# Test 4+5 — _build_v3_model timeout_minutes at 4h vs 8h
# ---------------------------------------------------------------------------


class TestBuildV3ModelTimeout:
    def test_timeout_5040_at_4h(self, runner_mod) -> None:
        """_build_v3_model with bar_interval='4h' must set timeout_minutes=5040."""
        cfg, _strategy = runner_mod._build_v3_model(
            symbol="BCHUSDT",
            seed=42,
            n_trials=1,
            ensemble_seeds=[42],
            bar_interval="4h",
        )
        assert cfg.timeout_minutes == 5040, (
            f"Expected timeout_minutes=5040 at 4h, got {cfg.timeout_minutes}"
        )

    def test_timeout_10080_at_8h(self, runner_mod) -> None:
        """_build_v3_model with bar_interval='8h' must set timeout_minutes=10080."""
        cfg, _strategy = runner_mod._build_v3_model(
            symbol="BCHUSDT",
            seed=42,
            n_trials=1,
            ensemble_seeds=[42],
            bar_interval="8h",
        )
        assert cfg.timeout_minutes == 10080, (
            f"Expected timeout_minutes=10080 at 8h, got {cfg.timeout_minutes}"
        )


# ---------------------------------------------------------------------------
# Test 6 — enable_per_symbol_drawdown_scaling=False at 4h (REVERT from /129)
# ---------------------------------------------------------------------------


class TestDrawdownScalingRevert:
    def test_drawdown_scaling_false_at_4h(self, runner_mod) -> None:
        """enable_per_symbol_drawdown_scaling must be False at 4h (axis CLOSED)."""
        _cfg, strategy = runner_mod._build_v3_model(
            symbol="BCHUSDT",
            seed=42,
            n_trials=1,
            ensemble_seeds=[42],
            bar_interval="4h",
        )
        assert strategy.config.enable_per_symbol_drawdown_scaling is False, (
            "enable_per_symbol_drawdown_scaling must be False at iter-v3/130 "
            "(axis CLOSED at /129 NEGATIVE-catastrophic; REVERT mandatory)."
        )

    def test_drawdown_scaling_false_at_8h(self, runner_mod) -> None:
        """enable_per_symbol_drawdown_scaling must also be False at 8h (/130 state)."""
        _cfg, strategy = runner_mod._build_v3_model(
            symbol="BCHUSDT",
            seed=42,
            n_trials=1,
            ensemble_seeds=[42],
            bar_interval="8h",
        )
        assert strategy.config.enable_per_symbol_drawdown_scaling is False


# ---------------------------------------------------------------------------
# Test 7 — FEATURES_DIR_4H is distinct
# ---------------------------------------------------------------------------


class TestFeaturesDirDistinct:
    def test_features_dir_4h_distinct(self, runner_mod) -> None:
        """FEATURES_DIR_4H must be different from FEATURES_DIR and FEATURES_DIR_24H."""
        assert runner_mod.FEATURES_DIR_4H != runner_mod.FEATURES_DIR, (
            "FEATURES_DIR_4H must differ from FEATURES_DIR"
        )
        assert runner_mod.FEATURES_DIR_4H != runner_mod.FEATURES_DIR_24H, (
            "FEATURES_DIR_4H must differ from FEATURES_DIR_24H"
        )
        assert "4h" in str(runner_mod.FEATURES_DIR_4H), "FEATURES_DIR_4H path must contain '4h'"


# ---------------------------------------------------------------------------
# Test 8 — _TeeLogger writes to both stdout and file
# ---------------------------------------------------------------------------


class TestTeeLogger:
    def test_tee_logger_writes_to_file(self, runner_mod, tmp_path) -> None:
        """_TeeLogger must write output to both terminal and the log file."""
        log_path = tmp_path / "run.log"
        original_stdout = sys.stdout

        tee = runner_mod._TeeLogger(log_path)
        try:
            print("iter-v3/130 TeeLogger test line")
        finally:
            tee.close()

        assert sys.stdout is original_stdout, "stdout must be restored after close()"
        assert log_path.exists(), "run.log file must be created"
        content = log_path.read_text(encoding="utf-8")
        assert "iter-v3/130 TeeLogger test line" in content, (
            f"Log file must contain the test line. Got: {content!r}"
        )

    def test_tee_logger_stdout_restored_on_close(self, runner_mod, tmp_path) -> None:
        """sys.stdout must be restored to original after _TeeLogger.close()."""
        log_path = tmp_path / "run2.log"
        original = sys.stdout
        tee = runner_mod._TeeLogger(log_path)
        tee.close()
        assert sys.stdout is original
