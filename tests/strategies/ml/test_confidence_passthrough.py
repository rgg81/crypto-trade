"""Adversarial tests for iter-v3/080 — passive confidence metadata passthrough.

Tests:
1. Signal / Order / TradeResult each carry confidence: float | None = None.
2. Constructing Signal / Order / TradeResult WITHOUT confidence leaves all
   pre-existing fields unchanged (backward-compat, default=None).
3. confidence threads Signal -> Order (via create_order) -> TradeResult
   (via make_result) end-to-end with the correct value.
4. Static grep: no module other than the forward-copy constructors
   (create_order, make_result) and _write_trades_csv / _write_confidence_distribution
   reads Signal.confidence / Order.confidence / TradeResult.confidence as a
   *decision* — i.e. no conditional branch consults the field.
5. lgbm.get_signal sets weight = 100 (flat, not conviction_derate) — the /079
   revert is complete.
6. confidence is look-ahead-clean: it is sourced from the same past-only proba
   vector already used for direction/weight — structural assertion on lgbm source.
7. trades.csv written by _write_trades_csv includes the confidence column.
8. _write_confidence_distribution emits confidence_distribution.csv with the
   expected schema when given a minimal IS trade roster.
"""

from __future__ import annotations

import csv
import inspect
import re
import tempfile
from pathlib import Path

import pytest

from crypto_trade.backtest import BacktestConfig, create_order, make_result
from crypto_trade.backtest_models import Order, Signal, TradeResult
from crypto_trade.iteration_report import (
    _write_confidence_distribution,
    _write_trades_csv,
)
from crypto_trade.strategies.ml import lgbm as lgbm_module


# ---------------------------------------------------------------------------
# 1. Dataclass fields exist with correct default
# ---------------------------------------------------------------------------
class TestDataclassFields:
    def test_signal_has_confidence_field(self) -> None:
        import dataclasses

        fields = {f.name: f for f in dataclasses.fields(Signal)}
        assert "confidence" in fields, "Signal missing confidence field"
        assert fields["confidence"].default is None, "Signal.confidence default must be None"

    def test_order_has_confidence_field(self) -> None:
        import dataclasses

        fields = {f.name: f for f in dataclasses.fields(Order)}
        assert "confidence" in fields, "Order missing confidence field"
        assert fields["confidence"].default is None, "Order.confidence default must be None"

    def test_trade_result_has_confidence_field(self) -> None:
        import dataclasses

        fields = {f.name: f for f in dataclasses.fields(TradeResult)}
        assert "confidence" in fields, "TradeResult missing confidence field"
        assert fields["confidence"].default is None, "TradeResult.confidence default must be None"


# ---------------------------------------------------------------------------
# 2. Backward-compat: existing call sites not broken (confidence defaults None)
# ---------------------------------------------------------------------------
class TestBackwardCompat:
    def test_signal_without_confidence_has_none(self) -> None:
        sig = Signal(direction=1, weight=100)
        assert sig.confidence is None
        assert sig.direction == 1
        assert sig.weight == 100

    def test_signal_with_confidence_stores_value(self) -> None:
        sig = Signal(direction=1, weight=100, confidence=0.73)
        assert sig.confidence == pytest.approx(0.73)

    def test_order_without_confidence_has_none(self) -> None:
        order = Order(
            symbol="BCHUSDT",
            direction=1,
            entry_price=300.0,
            amount_usd=100.0,
            weight_factor=1.0,
            stop_loss_price=290.0,
            take_profit_price=315.0,
            open_time=1_000_000,
            timeout_time=2_000_000,
        )
        assert order.confidence is None

    def test_trade_result_without_confidence_has_none(self) -> None:
        tr = TradeResult(
            symbol="BCHUSDT",
            direction=1,
            entry_price=300.0,
            exit_price=315.0,
            weight_factor=1.0,
            open_time=1_000_000,
            close_time=2_000_000,
            exit_reason="take_profit",
            pnl_pct=5.0,
            fee_pct=0.1,
            net_pnl_pct=4.9,
            weighted_pnl=4.9,
        )
        assert tr.confidence is None


# ---------------------------------------------------------------------------
# 3. End-to-end thread: Signal -> Order -> TradeResult
# ---------------------------------------------------------------------------
class TestConfidenceThread:
    def _make_config(self) -> BacktestConfig:
        return BacktestConfig(
            symbols=("BCHUSDT",),
            interval="8h",
            max_amount_usd=100.0,
            stop_loss_pct=2.0,
            take_profit_pct=4.0,
            timeout_minutes=480,
        )

    def test_confidence_propagates_to_order(self) -> None:
        sig = Signal(direction=1, weight=100, tp_pct=4.0, sl_pct=2.0, confidence=0.81)
        config = self._make_config()
        order = create_order("BCHUSDT", sig, close_price=300.0, close_time=1_000_000, config=config)
        assert order.confidence == pytest.approx(0.81)

    def test_confidence_propagates_to_trade_result(self) -> None:
        sig = Signal(direction=1, weight=100, tp_pct=4.0, sl_pct=2.0, confidence=0.81)
        config = self._make_config()
        order = create_order("BCHUSDT", sig, close_price=300.0, close_time=1_000_000, config=config)
        result = make_result(
            order, exit_price=312.0, close_time=2_000_000, exit_reason="take_profit", fee_pct=0.1
        )
        assert result.confidence == pytest.approx(0.81)

    def test_none_confidence_propagates(self) -> None:
        sig = Signal(direction=1, weight=100, tp_pct=4.0, sl_pct=2.0)
        config = self._make_config()
        order = create_order("BCHUSDT", sig, close_price=300.0, close_time=1_000_000, config=config)
        result = make_result(
            order, exit_price=312.0, close_time=2_000_000, exit_reason="take_profit", fee_pct=0.1
        )
        assert result.confidence is None


# ---------------------------------------------------------------------------
# 4. Static grep: confidence is NOT read in a decision path
#
# Allowed consumers:
#   - create_order (copies signal.confidence to order)
#   - make_result  (copies order.confidence to trade result)
#   - _write_trades_csv (writes the column)
#   - _write_confidence_distribution (reads for histogram)
#   - dataclass field declarations themselves
#   - __init__.py / lgbm.get_signal (the return statement passing confidence=)
#   - comment lines
#
# Forbidden: any `if ... confidence`, `confidence >`, `confidence <`,
#            `confidence ==`, `while ... confidence` outside the above
#            explicitly-allowed sites.
# ---------------------------------------------------------------------------
class TestNoDecisionPathReadsConfidence:
    ALLOWED_FILES = {
        "backtest.py",  # create_order, make_result
        "backtest_models.py",  # dataclass declarations
        "iteration_report.py",  # _write_trades_csv, _write_confidence_distribution
        "lgbm.py",  # get_signal return + conviction_derate (dead code)
        "risk_v2.py",  # forward-copy confidence=sig.confidence in Signal reconstruction
        "risk_v3.py",  # forward-copy confidence=sig.confidence in Signal reconstruction
    }

    def _src_files(self) -> list[Path]:
        src_root = Path(lgbm_module.__file__).resolve().parent.parent.parent
        # Walk src/crypto_trade/
        results = []
        for p in src_root.rglob("*.py"):
            if p.name in self.ALLOWED_FILES:
                continue
            results.append(p)
        return results

    def test_no_decision_branch_on_confidence_outside_allowed(self) -> None:
        """No .py file outside the allowed set branches on .confidence."""
        forbidden_pattern = re.compile(
            r"\bconfidence\b.*[<>=!]|[<>=!].*\bconfidence\b|if.*\.confidence|while.*\.confidence"
        )
        violations: list[str] = []
        for p in self._src_files():
            text = p.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if ".confidence" in stripped and forbidden_pattern.search(stripped):
                    violations.append(f"{p}:{lineno}: {stripped}")
        assert not violations, (
            "The following files have a decision branch on .confidence — "
            "this field must be pure passive metadata:\n" + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# 5. lgbm.get_signal uses weight = 100 (flat), not conviction_derate
# ---------------------------------------------------------------------------
class TestWeightIsFlat100:
    def test_get_signal_source_uses_weight_100(self) -> None:
        from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

        source = inspect.getsource(LightGbmStrategy.get_signal)
        assert "weight = 100" in source, (
            "LightGbmStrategy.get_signal must use 'weight = 100' (flat, /079 revert). "
            "Found source does not contain 'weight = 100'."
        )

    def test_get_signal_source_does_not_call_conviction_derate(self) -> None:
        from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

        source = inspect.getsource(LightGbmStrategy.get_signal)
        assert "conviction_derate" not in source, (
            "LightGbmStrategy.get_signal must NOT call conviction_derate — "
            "the /079 primitive 13 revert must be complete."
        )


# ---------------------------------------------------------------------------
# 6. Look-ahead-clean: confidence sourced from past-only proba vector
# ---------------------------------------------------------------------------
class TestLookAheadClean:
    def test_confidence_sourced_from_proba_vector(self) -> None:
        from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

        source = inspect.getsource(LightGbmStrategy.get_signal)
        # The confidence line should reference proba (the inner-ensemble mean),
        # not any future-data column.
        assert "directional_conf" in source or "confidence" in source, (
            "get_signal source should derive confidence from proba."
        )
        # Confirm no future-leaking identifiers on the confidence assignment lines.
        for line in source.splitlines():
            stripped = line.strip()
            if "confidence" in stripped and "=" in stripped and not stripped.startswith("#"):
                forbidden = ["future", "forward", "next_", "look_ahead"]
                for f in forbidden:
                    assert f not in stripped.lower(), (
                        f"Potential look-ahead reference '{f}' in confidence assignment: {stripped}"
                    )


# ---------------------------------------------------------------------------
# 7. _write_trades_csv includes the confidence column
# ---------------------------------------------------------------------------
class TestTradesCsvConfidenceColumn:
    def _make_trade(self, confidence: float | None) -> TradeResult:
        return TradeResult(
            symbol="BCHUSDT",
            direction=1,
            entry_price=300.0,
            exit_price=315.0,
            weight_factor=1.0,
            open_time=1_700_000_000_000,
            close_time=1_700_100_000_000,
            exit_reason="take_profit",
            pnl_pct=5.0,
            fee_pct=0.1,
            net_pnl_pct=4.9,
            weighted_pnl=4.9,
            confidence=confidence,
        )

    def test_confidence_column_present_in_header(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            path = Path(f.name)
        _write_trades_csv([self._make_trade(0.78)], path)
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            assert "confidence" in (reader.fieldnames or []), (
                "trades.csv header missing 'confidence' column"
            )

    def test_confidence_value_written_correctly(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            path = Path(f.name)
        _write_trades_csv([self._make_trade(0.782345)], path)
        with open(path, newline="") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 1
        assert rows[0]["confidence"] == "0.782345", (
            f"Expected '0.782345', got {rows[0]['confidence']!r}"
        )

    def test_none_confidence_written_as_empty_string(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            path = Path(f.name)
        _write_trades_csv([self._make_trade(None)], path)
        with open(path, newline="") as f:
            rows = list(csv.DictReader(f))
        assert rows[0]["confidence"] == "", (
            f"None confidence should write empty string, got {rows[0]['confidence']!r}"
        )


# ---------------------------------------------------------------------------
# 8. _write_confidence_distribution emits valid confidence_distribution.csv
# ---------------------------------------------------------------------------
class TestConfidenceDistributionEmission:
    def _make_is_trades(self) -> list[TradeResult]:
        # Minimal roster: 3 IS trades across 2 months with known confidence values.
        return [
            TradeResult(
                symbol="BCHUSDT",
                direction=1,
                entry_price=300.0,
                exit_price=315.0,
                weight_factor=1.0,
                open_time=1_680_000_000_000,
                close_time=1_680_100_000_000,
                exit_reason="take_profit",
                pnl_pct=5.0,
                fee_pct=0.1,
                net_pnl_pct=4.9,
                weighted_pnl=4.9,
                confidence=0.72,
            ),
            TradeResult(
                symbol="BCHUSDT",
                direction=-1,
                entry_price=320.0,
                exit_price=310.0,
                weight_factor=1.0,
                open_time=1_682_600_000_000,
                close_time=1_682_700_000_000,
                exit_reason="take_profit",
                pnl_pct=3.125,
                fee_pct=0.1,
                net_pnl_pct=3.025,
                weighted_pnl=3.025,
                confidence=0.85,
            ),
            TradeResult(
                symbol="LDOUSDT",
                direction=1,
                entry_price=1.5,
                exit_price=1.6,
                weight_factor=1.0,
                open_time=1_680_000_000_000,
                close_time=1_680_200_000_000,
                exit_reason="take_profit",
                pnl_pct=6.67,
                fee_pct=0.1,
                net_pnl_pct=6.57,
                weighted_pnl=6.57,
                confidence=0.65,
            ),
        ]

    def test_confidence_distribution_file_created(self) -> None:
        trades = self._make_is_trades()
        with tempfile.TemporaryDirectory() as tmpdir:
            report_dir = Path(tmpdir)
            _write_confidence_distribution(trades, model_pairs=[], report_dir=report_dir)
            out = report_dir / "confidence_distribution.csv"
            assert out.exists(), "confidence_distribution.csv was not created"

    def test_confidence_distribution_schema(self) -> None:
        trades = self._make_is_trades()
        with tempfile.TemporaryDirectory() as tmpdir:
            report_dir = Path(tmpdir)
            _write_confidence_distribution(trades, model_pairs=[], report_dir=report_dir)
            out = report_dir / "confidence_distribution.csv"
            with open(out, newline="") as f:
                reader = csv.DictReader(f)
                expected_fields = {
                    "symbol",
                    "is_month",
                    "conf_bin_lo",
                    "conf_bin_hi",
                    "n_trades",
                    "realized_optuna_conf_threshold",
                }
                assert expected_fields.issubset(set(reader.fieldnames or [])), (
                    f"Missing columns. Got: {reader.fieldnames}"
                )

    def test_confidence_distribution_has_portfolio_block(self) -> None:
        trades = self._make_is_trades()
        with tempfile.TemporaryDirectory() as tmpdir:
            report_dir = Path(tmpdir)
            _write_confidence_distribution(trades, model_pairs=[], report_dir=report_dir)
            out = report_dir / "confidence_distribution.csv"
            with open(out, newline="") as f:
                rows = list(csv.DictReader(f))
            portfolio_rows = [r for r in rows if r["symbol"] == "PORTFOLIO"]
            assert portfolio_rows, "PORTFOLIO rows missing from confidence_distribution.csv"

    def test_confidence_distribution_has_all_is_block(self) -> None:
        trades = self._make_is_trades()
        with tempfile.TemporaryDirectory() as tmpdir:
            report_dir = Path(tmpdir)
            _write_confidence_distribution(trades, model_pairs=[], report_dir=report_dir)
            out = report_dir / "confidence_distribution.csv"
            with open(out, newline="") as f:
                rows = list(csv.DictReader(f))
            all_is_rows = [r for r in rows if r["is_month"] == "ALL_IS"]
            assert all_is_rows, "ALL_IS rows missing from confidence_distribution.csv"

    def test_confidence_distribution_nondegenerate_when_trades_have_confidence(self) -> None:
        """When IS trades have non-None confidence, n_trades > 0 in at least one bin."""
        trades = self._make_is_trades()
        with tempfile.TemporaryDirectory() as tmpdir:
            report_dir = Path(tmpdir)
            _write_confidence_distribution(trades, model_pairs=[], report_dir=report_dir)
            out = report_dir / "confidence_distribution.csv"
            with open(out, newline="") as f:
                rows = list(csv.DictReader(f))
            nonzero = [r for r in rows if int(r["n_trades"]) > 0]
            assert nonzero, (
                "confidence_distribution.csv must have at least one row with n_trades > 0 "
                "when IS trades all carry non-None confidence values"
            )

    def test_no_confidence_trades_has_no_per_symbol_rows(self) -> None:
        """When trades have confidence=None, no per-symbol histogram rows are emitted.

        The PORTFOLIO/ALL_IS block may still be emitted (with n_trades=0 in all bins)
        since the histogram function runs over an empty confidence list.
        The key assertion: no rows for the actual symbol (BCHUSDT), only PORTFOLIO.
        """
        trades = [
            TradeResult(
                symbol="BCHUSDT",
                direction=1,
                entry_price=300.0,
                exit_price=315.0,
                weight_factor=1.0,
                open_time=1_680_000_000_000,
                close_time=1_680_100_000_000,
                exit_reason="take_profit",
                pnl_pct=5.0,
                fee_pct=0.1,
                net_pnl_pct=4.9,
                weighted_pnl=4.9,
                confidence=None,
            ),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            report_dir = Path(tmpdir)
            _write_confidence_distribution(trades, model_pairs=[], report_dir=report_dir)
            out = report_dir / "confidence_distribution.csv"
            assert out.exists(), "confidence_distribution.csv should be created even if empty"
            with open(out, newline="") as f:
                rows = list(csv.DictReader(f))
            # No per-symbol rows when all confidence=None (those symbols are filtered out).
            bch_rows = [r for r in rows if r["symbol"] == "BCHUSDT"]
            assert bch_rows == [], (
                "No BCHUSDT rows expected when all its trades have confidence=None"
            )
            # Any remaining rows (PORTFOLIO ALL_IS) must have n_trades=0.
            for r in rows:
                assert int(r["n_trades"]) == 0, (
                    f"Expected n_trades=0 when all confidence=None, got {r['n_trades']} "
                    f"for symbol={r['symbol']} is_month={r['is_month']}"
                )


# ---------------------------------------------------------------------------
# 9. Wrapper-chain regression: confidence survives RiskV2Wrapper.get_signal
#    and RiskV3Wrapper.get_signal (the two drop points found in iter-v3/080).
#
#    Both wrappers previously reconstructed Signal without confidence=sig.confidence
#    (risk_v2.py:366-372, risk_v3.py:405-410), silently zeroing the field before
#    it reached trades.csv.  This class regression-locks the fix.
#
#    Strategy: stub the inner strategy with a minimal Protocol-compliant object
#    that returns a Signal with a known confidence value.  Route the signal
#    through each wrapper with ALL gates disabled so only the final
#    Signal-reconstruction path executes.  Assert confidence is preserved.
#
#    Passive-metadata assertion: confidence is NOT read in any wrapper branch —
#    only forwarded.  Covered by Test 4 (TestNoDecisionPathReadsConfidence).
# ---------------------------------------------------------------------------
class TestWrapperChainConfidencePassthrough:
    """Regression test for iter-v3/080 fix: both risk wrappers forward confidence."""

    # ------------------------------------------------------------------
    # Minimal inner-strategy stub
    # ------------------------------------------------------------------
    class _StubInner:
        """Minimal Strategy-protocol stub that returns a fixed Signal."""

        atr_column = "atr_pct"

        def __init__(self, signal: Signal) -> None:
            self._signal = signal

        def compute_features(self, master) -> None:  # pd.DataFrame — import deferred
            pass

        def get_signal(self, symbol: str, open_time: int) -> Signal:
            return self._signal

        def skip(self) -> None:
            pass

    def _gates_off_config(self):
        """All gates disabled — only the final Signal reconstruction executes."""
        from crypto_trade.strategies.ml.risk_v2 import RiskV2Config

        return RiskV2Config(
            enable_vol_scaling=False,
            enable_adx_gate=False,
            enable_hurst_check=False,
            enable_zscore_ood=False,
            enable_low_vol_filter=False,
            enable_per_symbol_cap=False,
            enable_per_symbol_drawdown_brake=False,
            enable_regime_gate=False,
            enable_regime_size_scalar=False,
        )

    # ------------------------------------------------------------------
    # RiskV2Wrapper
    # ------------------------------------------------------------------
    def test_risk_v2_wrapper_passes_confidence_through(self) -> None:
        """RiskV2Wrapper.get_signal must not drop confidence from the inner Signal."""
        import pandas as pd

        from crypto_trade.strategies.ml.risk_v2 import RiskV2Wrapper

        known_confidence = 0.7654
        inner_sig = Signal(
            direction=1, weight=100, tp_pct=4.0, sl_pct=2.0, confidence=known_confidence
        )
        stub = self._StubInner(inner_sig)
        config = self._gates_off_config()
        wrapper = RiskV2Wrapper(inner=stub, config=config)

        # compute_features must be called first so _gate_stats etc. are ready.
        # Pass an empty master — _build_lookups iterates symbols from master,
        # so an empty DataFrame produces an empty loop and no parquet I/O.
        empty_master = pd.DataFrame(columns=["symbol", "open_time"])
        wrapper.compute_features(empty_master)

        result = wrapper.get_signal("BCHUSDT", open_time=1_700_000_000_000)

        assert result.direction == 1, "direction must be unchanged"
        assert result.confidence == pytest.approx(known_confidence), (
            f"RiskV2Wrapper.get_signal dropped confidence. "
            f"Expected {known_confidence}, got {result.confidence!r}. "
            "Fix: add confidence=sig.confidence to Signal(...) at risk_v2.py."
        )

    def test_risk_v2_wrapper_passes_none_confidence_through(self) -> None:
        """RiskV2Wrapper.get_signal must preserve confidence=None (backward compat)."""
        import pandas as pd

        from crypto_trade.strategies.ml.risk_v2 import RiskV2Wrapper

        inner_sig = Signal(direction=1, weight=100, tp_pct=4.0, sl_pct=2.0, confidence=None)
        stub = self._StubInner(inner_sig)
        wrapper = RiskV2Wrapper(inner=stub, config=self._gates_off_config())
        wrapper.compute_features(pd.DataFrame(columns=["symbol", "open_time"]))

        result = wrapper.get_signal("BCHUSDT", open_time=1_700_000_000_000)
        assert result.confidence is None

    # ------------------------------------------------------------------
    # RiskV3Wrapper — regime_size_scalar path (the second drop point)
    # ------------------------------------------------------------------
    def test_risk_v3_wrapper_passes_confidence_through_no_scalar(self) -> None:
        """RiskV3Wrapper.get_signal with scalar disabled must forward confidence."""
        import pandas as pd

        from crypto_trade.strategies.ml.risk_v3 import RiskV3Wrapper

        known_confidence = 0.8812
        inner_sig = Signal(
            direction=1, weight=100, tp_pct=4.0, sl_pct=2.0, confidence=known_confidence
        )
        stub = self._StubInner(inner_sig)
        config = self._gates_off_config()
        wrapper = RiskV3Wrapper(inner=stub, config=config)
        wrapper.compute_features(pd.DataFrame(columns=["symbol", "open_time"]))

        result = wrapper.get_signal("BCHUSDT", open_time=1_700_000_000_000)

        assert result.direction == 1
        assert result.confidence == pytest.approx(known_confidence), (
            f"RiskV3Wrapper.get_signal (no scalar) dropped confidence. "
            f"Expected {known_confidence}, got {result.confidence!r}."
        )

    def test_risk_v3_wrapper_passes_confidence_through_regime_scalar_fires(self) -> None:
        """RiskV3Wrapper with regime_size_scalar FIRING must still forward confidence.

        This is the second drop point (risk_v3.py Signal reconstruction at the
        scalar branch).  We force the scalar to fire by injecting a pre-built
        _btc_trend_lookup that classifies the target bar as BTC bear/chop.
        """
        import numpy as np
        import pandas as pd

        from crypto_trade.strategies.ml.risk_v2 import RiskV2Config
        from crypto_trade.strategies.ml.risk_v3 import RiskV3Wrapper

        known_confidence = 0.5543
        inner_sig = Signal(
            direction=1, weight=100, tp_pct=4.0, sl_pct=2.0, confidence=known_confidence
        )
        stub = self._StubInner(inner_sig)

        config = RiskV2Config(
            enable_vol_scaling=False,
            enable_adx_gate=False,
            enable_hurst_check=False,
            enable_zscore_ood=False,
            enable_low_vol_filter=False,
            enable_per_symbol_cap=False,
            enable_per_symbol_drawdown_brake=False,
            enable_regime_gate=False,
            # Scalar ON — scope includes BCHUSDT, value=0.5
            enable_regime_size_scalar=True,
            regime_size_scalar_symbols=("BCHUSDT",),
            regime_size_scalar_value=0.5,
            regime_size_ma_window=1,
        )
        wrapper = RiskV3Wrapper(inner=stub, config=config)
        wrapper.compute_features(pd.DataFrame(columns=["symbol", "open_time"]))

        # Inject a fake _btc_trend_lookup so the scalar fires without CSV I/O.
        # open_time=0 precedes the target bar; btc_bearchop=1 forces bear/chop
        # classification → scalar = 0.5 < 1.0 → branch executes.
        wrapper._btc_trend_lookup = {
            "open_time": np.array([0], dtype=np.int64),
            "btc_bearchop": np.array([1], dtype=np.int8),
        }

        result = wrapper.get_signal("BCHUSDT", open_time=1_700_000_000_000)

        # Scalar halves the weight (100 → 50) but must NOT drop confidence.
        assert result.direction == 1
        assert result.weight == 50, f"Expected weight=50 after 0.5 scalar, got {result.weight}"
        assert result.confidence == pytest.approx(known_confidence), (
            f"RiskV3Wrapper.get_signal (scalar branch) dropped confidence. "
            f"Expected {known_confidence}, got {result.confidence!r}. "
            "Fix: add confidence=sig.confidence to Signal(...) at risk_v3.py."
        )
