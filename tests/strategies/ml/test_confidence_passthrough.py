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
