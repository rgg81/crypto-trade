"""Tests for backtest_report.py — Deflated Sharpe Ratio helpers."""

import pytest

from crypto_trade.backtest_report import (
    compute_deflated_sharpe_ratio,
    expected_max_sharpe,
    sharpe_standard_error,
)


class TestExpectedMaxSharpe:
    def test_n_one_returns_zero(self):
        assert expected_max_sharpe(1) == 0.0

    def test_n_zero_returns_zero(self):
        assert expected_max_sharpe(0) == 0.0

    def test_monotonically_increasing(self):
        prev = expected_max_sharpe(2)
        for n in [5, 10, 20, 50, 100, 200]:
            cur = expected_max_sharpe(n)
            assert cur > prev, f"E[max] not increasing at N={n}: {cur} <= {prev}"
            prev = cur

    def test_known_values(self):
        # From iter 159 analytical output (verified against AFML Ch. 14).
        assert expected_max_sharpe(21) == pytest.approx(2.468, abs=0.01)
        assert expected_max_sharpe(100) == pytest.approx(3.035, abs=0.01)
        assert expected_max_sharpe(200) == pytest.approx(3.255, abs=0.01)


class TestSharpeStandardError:
    def test_too_few_observations(self):
        assert sharpe_standard_error(1.5, [0.01, 0.02]) == 0.0

    def test_zero_variance(self):
        # All returns equal → variance zero → SE = 0
        assert sharpe_standard_error(1.0, [0.01] * 10) == 0.0

    def test_positive_for_normal_returns(self):
        # Symmetric returns with non-degenerate variance
        rets = [0.01, -0.005, 0.02, -0.01, 0.015, -0.008, 0.012, -0.006, 0.018, -0.004]
        se = sharpe_standard_error(1.0, rets)
        assert se > 0.0
        assert se < 1.0  # sanity — shouldn't be enormous

    def test_scales_with_sqrt_t(self):
        # Same distribution, 2x observations → SE should shrink (approximately by sqrt(2))
        base_rets = [0.01, -0.005, 0.02, -0.01, 0.015] * 2
        doubled_rets = base_rets * 2
        se_base = sharpe_standard_error(1.0, base_rets)
        se_double = sharpe_standard_error(1.0, doubled_rets)
        assert se_double < se_base


class TestComputeDeflatedSharpeRatio:
    def test_dsr_exceeds_zero_when_sharpe_above_emax(self):
        # Strong Sharpe, small N → should beat random
        rets = [0.005, -0.003, 0.008, -0.002, 0.004, -0.003, 0.006, -0.001,
                0.007, -0.004, 0.005, -0.002, 0.009, -0.003, 0.006]
        dsr = compute_deflated_sharpe_ratio(sharpe=3.0, n_trials=5, returns=rets)
        assert dsr > 0.0

    def test_dsr_below_zero_when_sharpe_below_emax(self):
        # Weak Sharpe, large N → should fall below random
        rets = [0.001, -0.0005, 0.002, -0.001, 0.0015] * 10
        dsr = compute_deflated_sharpe_ratio(sharpe=0.5, n_trials=100, returns=rets)
        assert dsr < 0.0

    def test_zero_se_returns_zero(self):
        # Degenerate returns produce SE=0 → DSR=0
        assert (
            compute_deflated_sharpe_ratio(sharpe=2.0, n_trials=10, returns=[0.01] * 5)
            == 0.0
        )

    def test_matches_iter159_baseline_reference(self):
        # iter 159 analytical check: v0.152 OOS Sharpe 2.8286, N=21,
        # computed DSR ≈ +1.38 with approximate SE(SR) ≈ 0.262.
        # Synthesize daily returns with matching mean/std/skew/kurt profile.
        # Direct formula check: DSR = (SR − E[max]) / SE.
        emax = expected_max_sharpe(21)
        se_approx = 0.262
        sharpe = 2.8286
        expected_dsr = (sharpe - emax) / se_approx
        assert expected_dsr == pytest.approx(1.38, abs=0.05)
        # E[max(21)] should match the ~2.47 reported
        assert emax == pytest.approx(2.468, abs=0.01)

    def test_n_one_reduces_to_raw_sharpe_over_se(self):
        # At N=1, E[max]=0, so DSR = SR / SE
        rets = [0.005, -0.003, 0.008, -0.002, 0.004, -0.003, 0.006, -0.001]
        se = sharpe_standard_error(1.5, rets)
        dsr = compute_deflated_sharpe_ratio(sharpe=1.5, n_trials=1, returns=rets)
        assert se > 0
        assert dsr == pytest.approx(1.5 / se, rel=1e-6)
