"""Tests for primitive 12 — BTC-trend-regime position-SIZE de-rate scalar (iter-v3/075).

Per research brief iteration_v3-075 Section 3.1 #7. Covers:
  - The BTC bull/bear-chop trend classifier (_build_btc_trend_lookup) — past-only.
  - The de-rate scalar fires for in-scope symbols only and never for out-of-scope.
  - The de-rate scales WEIGHT only (direction / tp / sl unchanged) — holding-time-
    ORTHOGONAL.
  - enable_regime_size_scalar=False is byte-identical to the no-scalar path.
  - RiskV2Config.__post_init__ validation of regime_size_scalar_value.
  - End-to-end RiskV3Wrapper smoke test: in-scope symbols de-rated, BCH unchanged,
    gate_stats_summary reports a non-zero regime_size_scalar_fires.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.backtest_models import Signal
from crypto_trade.strategies import NO_SIGNAL
from crypto_trade.strategies.ml.risk_v2 import RiskV2Config
from crypto_trade.strategies.ml.risk_v3 import RiskV3Wrapper, _build_btc_trend_lookup

BAR_MS = 28_800_000  # 8 hours in milliseconds


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_btc_csv(tmp_path: Path, closes: list[float]) -> Path:
    """Write a synthetic BTC 8h CSV with specified close prices."""
    n = len(closes)
    start_ms = 1_600_000_000_000
    open_times = [start_ms + i * BAR_MS for i in range(n)]
    df = pd.DataFrame({"open_time": open_times, "close": closes})
    p = tmp_path / "BTCUSDT" / "8h.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)
    return p


class _StubInner:
    """Minimal inner strategy stub — emits a fixed LONG signal of weight 10."""

    def __init__(self) -> None:
        self.features_dir = "data/features_v3"
        self._interval = "8h"

    def compute_features(self, master: pd.DataFrame) -> None:  # noqa: ARG002
        return None

    def skip(self) -> None:
        return None

    def get_signal(self, symbol: str, open_time: int) -> Signal:  # noqa: ARG002
        return Signal(direction=1, weight=10, tp_pct=8.0, sl_pct=4.0)


def _wrapper_with_trend_lookup(
    config: RiskV2Config, btc_csv: Path, ma_window: int = 20
) -> RiskV3Wrapper:
    """Build a RiskV3Wrapper and inject the BTC trend lookup directly.

    Bypasses _build_lookups (which needs feature parquets) — primitive 12's
    get_signal path only depends on _btc_trend_lookup, so injecting it directly
    is a faithful unit-level fixture.
    """
    w = RiskV3Wrapper(_StubInner(), config)
    w._btc_trend_lookup = _build_btc_trend_lookup(btc_csv, ma_window=ma_window)
    return w


# ---------------------------------------------------------------------------
# Test 1 — BTC trend classifier is past-only
# ---------------------------------------------------------------------------
def test_btc_trend_classifier_past_only(tmp_path: Path) -> None:
    """A price drop at bar t must NOT flag bar t bear/chop — only bar t+1 onward.

    Fixture: 60 bars climbing then a sharp drop at bar 40. With SMA window 20,
    bar 40's own close is excluded from its classification (close.shift(1)).
    """
    closes = [100.0 + i for i in range(40)]  # rising 100..139
    closes += [60.0] * 20  # sharp drop to 60 from bar 40
    csv = _make_btc_csv(tmp_path, closes)
    lookup = _build_btc_trend_lookup(csv, ma_window=20)
    flag = lookup["btc_bearchop"]

    # Bar 40 (the drop bar itself): classification uses close[20..39] (all rising,
    # shifted) — close[39]=139 is above its SMA → bull (0). The drop at bar 40 is
    # NOT visible to bar 40.
    assert flag[40] == 0, "drop bar 40 must not flag itself bear/chop (past-only)"
    # By bar 45 the dropped closes are in the shifted SMA window → bear/chop (1).
    assert flag[45] == 1, "bar 45 should be bear/chop (the drop is now in the past window)"


def test_btc_trend_classifier_warmup_is_bull(tmp_path: Path) -> None:
    """Warm-up bars (SMA undefined) are classified bull (0) — no de-rate where undefined."""
    closes = [100.0] * 30
    csv = _make_btc_csv(tmp_path, closes)
    lookup = _build_btc_trend_lookup(csv, ma_window=20)
    # First ~20 bars: SMA NaN → filled to 0 (bull).
    assert lookup["btc_bearchop"][0] == 0
    assert lookup["btc_bearchop"][5] == 0


# ---------------------------------------------------------------------------
# Test 2 — the scalar fires for in-scope symbols only
# ---------------------------------------------------------------------------
def test_scalar_fires_for_in_scope_symbol_only(tmp_path: Path) -> None:
    """De-rate applies to LDO/TRX (in scope) but never to BCH (out of scope)."""
    # Falling prices → bear/chop after warm-up.
    closes = [200.0 - i for i in range(60)]
    csv = _make_btc_csv(tmp_path, closes)
    cfg = RiskV2Config(
        # disable feature-dependent gates so the stub (no feature row) passes cleanly
        enable_zscore_ood=False,
        enable_hurst_check=False,
        enable_adx_gate=False,
        enable_low_vol_filter=False,
        enable_vol_scaling=False,
        enable_regime_size_scalar=True,
        regime_size_scalar_symbols=("LDOUSDT", "TRXUSDT"),
        regime_size_scalar_value=0.50,
        regime_size_ma_window=20,
    )
    w = _wrapper_with_trend_lookup(cfg, csv, ma_window=20)

    # A bar well past warm-up and in the falling (bear/chop) regime.
    bar_time = int(w._btc_trend_lookup["open_time"][55])
    # Confirm the fixture bar is actually classified bear/chop.
    assert w._btc_trend_lookup["btc_bearchop"][54] == 1

    trx_sig = w.get_signal("TRXUSDT", bar_time)
    ldo_sig = w.get_signal("LDOUSDT", bar_time)
    bch_sig = w.get_signal("BCHUSDT", bar_time)

    # In-scope symbols: weight de-rated from 10 → round(10 * 0.5) = 5.
    assert trx_sig.weight == 5, f"TRX weight should be de-rated to 5, got {trx_sig.weight}"
    assert ldo_sig.weight == 5, f"LDO weight should be de-rated to 5, got {ldo_sig.weight}"
    # Out-of-scope BCH: weight UNCHANGED at 10.
    assert bch_sig.weight == 10, f"BCH weight must be unchanged at 10, got {bch_sig.weight}"
    # Direction / tp / sl preserved for the de-rated signals (holding-time-orthogonal).
    assert trx_sig.direction == 1
    assert trx_sig.tp_pct == 8.0
    assert trx_sig.sl_pct == 4.0


def test_scalar_does_not_fire_in_bull_regime(tmp_path: Path) -> None:
    """In a BTC bull trend state, the scalar does NOT de-rate even in-scope symbols."""
    closes = [100.0 + i for i in range(60)]  # rising → bull
    csv = _make_btc_csv(tmp_path, closes)
    cfg = RiskV2Config(
        enable_zscore_ood=False,
        enable_hurst_check=False,
        enable_adx_gate=False,
        enable_low_vol_filter=False,
        enable_vol_scaling=False,
        enable_regime_size_scalar=True,
        regime_size_scalar_symbols=("LDOUSDT", "TRXUSDT"),
        regime_size_scalar_value=0.50,
        regime_size_ma_window=20,
    )
    w = _wrapper_with_trend_lookup(cfg, csv, ma_window=20)
    bar_time = int(w._btc_trend_lookup["open_time"][55])
    assert w._btc_trend_lookup["btc_bearchop"][54] == 0  # bull
    trx_sig = w.get_signal("TRXUSDT", bar_time)
    assert trx_sig.weight == 10, "weight must be unchanged in a BTC bull regime"


# ---------------------------------------------------------------------------
# Test 3 — disabled scalar is byte-identical to the no-scalar path
# ---------------------------------------------------------------------------
def test_disabled_scalar_is_passthrough() -> None:
    """enable_regime_size_scalar=False → wrapper weight identical to inner.

    With the scalar disabled, _build_lookups never builds _btc_trend_lookup, so
    get_signal must pass the inner weight through unchanged regardless of regime.
    """
    cfg = RiskV2Config(
        enable_zscore_ood=False,
        enable_hurst_check=False,
        enable_adx_gate=False,
        enable_low_vol_filter=False,
        enable_vol_scaling=False,
        enable_regime_size_scalar=False,  # OFF
        regime_size_scalar_symbols=("LDOUSDT", "TRXUSDT"),
        regime_size_scalar_value=0.50,
    )
    w = RiskV3Wrapper(_StubInner(), cfg)
    # No _btc_trend_lookup built (scalar disabled). get_signal must pass weight through.
    bar_time = 1_600_000_000_000 + 55 * BAR_MS
    trx_sig = w.get_signal("TRXUSDT", bar_time)
    assert trx_sig.weight == 10, "disabled scalar must leave weight unchanged"


def test_no_signal_not_promoted_by_scalar(tmp_path: Path) -> None:
    """A NO_SIGNAL from the inner cascade is never turned into a trade by the scalar."""

    class _NoSignalInner(_StubInner):
        def get_signal(self, symbol: str, open_time: int) -> Signal:  # noqa: ARG002
            return NO_SIGNAL

    closes = [200.0 - i for i in range(60)]
    csv = _make_btc_csv(tmp_path, closes)
    cfg = RiskV2Config(
        enable_zscore_ood=False,
        enable_hurst_check=False,
        enable_adx_gate=False,
        enable_low_vol_filter=False,
        enable_vol_scaling=False,
        enable_regime_size_scalar=True,
        regime_size_scalar_symbols=("TRXUSDT",),
        regime_size_scalar_value=0.50,
        regime_size_ma_window=20,
    )
    w = RiskV3Wrapper(_NoSignalInner(), cfg)
    w._btc_trend_lookup = _build_btc_trend_lookup(csv, ma_window=20)
    bar_time = int(w._btc_trend_lookup["open_time"][55])
    sig = w.get_signal("TRXUSDT", bar_time)
    assert sig.direction == 0, "NO_SIGNAL must stay NO_SIGNAL — the scalar never promotes it"


# ---------------------------------------------------------------------------
# Test 4 — config validation
# ---------------------------------------------------------------------------
def test_config_rejects_out_of_range_scalar() -> None:
    """regime_size_scalar_value outside (0, 1] raises in __post_init__."""
    with pytest.raises(ValueError, match="regime_size_scalar"):
        RiskV2Config(enable_regime_size_scalar=True, regime_size_scalar_value=0.0)
    with pytest.raises(ValueError, match="regime_size_scalar"):
        RiskV2Config(enable_regime_size_scalar=True, regime_size_scalar_value=1.5)
    with pytest.raises(ValueError, match="regime_size_ma_window"):
        RiskV2Config(
            enable_regime_size_scalar=True,
            regime_size_scalar_value=0.5,
            regime_size_ma_window=0,
        )
    # Valid config does not raise.
    RiskV2Config(
        enable_regime_size_scalar=True,
        regime_size_scalar_value=0.50,
        regime_size_ma_window=270,
    )


# ---------------------------------------------------------------------------
# Test 5 — end-to-end smoke: gate_stats_summary reports fires
# ---------------------------------------------------------------------------
def test_gate_stats_summary_reports_scalar_fires(tmp_path: Path) -> None:
    """A de-rated signal increments regime_size_scalar_fires; gate_stats_summary
    exposes it. BCH (out of scope) has zero fires."""
    closes = [200.0 - i for i in range(60)]  # bear/chop
    csv = _make_btc_csv(tmp_path, closes)
    cfg = RiskV2Config(
        enable_zscore_ood=False,
        enable_hurst_check=False,
        enable_adx_gate=False,
        enable_low_vol_filter=False,
        enable_vol_scaling=False,
        enable_regime_size_scalar=True,
        regime_size_scalar_symbols=("LDOUSDT", "TRXUSDT"),
        regime_size_scalar_value=0.50,
        regime_size_ma_window=20,
    )
    w = _wrapper_with_trend_lookup(cfg, csv, ma_window=20)
    # Fire TRX over several bear/chop bars.
    for i in (50, 52, 54, 56):
        w.get_signal("TRXUSDT", int(w._btc_trend_lookup["open_time"][i]))
    # Fire BCH (out of scope) over the same bars.
    for i in (50, 52, 54, 56):
        w.get_signal("BCHUSDT", int(w._btc_trend_lookup["open_time"][i]))

    summary = w.gate_stats_summary()
    assert summary["TRXUSDT"]["regime_size_scalar_fires"] == 4, "TRX should record 4 scalar fires"
    # BCH is out of scope — the scalar never fires for it.
    assert summary["BCHUSDT"]["regime_size_scalar_fires"] == 0, (
        "BCH (out of scope) must record 0 scalar fires"
    )
    assert "regime_size_scalar_fire_rate" in summary["TRXUSDT"]


def test_btc_trend_lookup_matches_eda_contract(tmp_path: Path) -> None:
    """The risk_v3 _build_btc_trend_lookup must match the EDA's classifier
    contract: close.shift(1) then rolling SMA; bear/chop = shifted close < SMA."""
    closes = [100.0, 101.0, 102.0, 103.0, 104.0, 90.0, 89.0, 88.0, 87.0, 86.0]
    csv = _make_btc_csv(tmp_path, closes)
    lookup = _build_btc_trend_lookup(csv, ma_window=3)
    # Replicate the EDA arithmetic independently.
    s = pd.Series(closes)
    shifted = s.shift(1)
    sma = shifted.rolling(3, min_periods=3).mean()
    expected = (shifted < sma).astype("Int64").fillna(0).astype(np.int8).to_numpy()
    np.testing.assert_array_equal(lookup["btc_bearchop"], expected)
