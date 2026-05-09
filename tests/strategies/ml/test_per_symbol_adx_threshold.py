"""Adversarial tests for the per-symbol ADX threshold override (iter-v3/049).

Tests per iter-v3/049 brief Section 3 Sub-fix 6 mandatory adversarial tests:
  1. Unspecified symbol falls back to global adx_threshold.
  2. Specified symbol uses per-symbol threshold, NOT global.
  3. Empty dict (default) preserves v1/v2/v3-prior behavior for all symbols.
  4. Multiple per-symbol thresholds work correctly (each symbol uses its own value;
     non-listed symbols use global).
  5. killed_by_adx counter increments on per-symbol threshold kill (re-uses existing
     GateStats counter — not a new counter).

Fixture rationale:
  RiskV2Wrapper._adx_gate_fails reads ADX from self._lookup (precomputed during
  compute_features). We use a deterministic mock that injects the lookup directly
  to bypass parquet I/O. The _MockInnerStrategy from test_direction_block_primitive_10.py
  serves as the inner strategy; all RiskV2 gates except ADX are disabled to isolate
  the per-symbol ADX behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from crypto_trade.strategies import NO_SIGNAL, Signal
from crypto_trade.strategies.ml.risk_v2 import RiskV2Config
from crypto_trade.strategies.ml.risk_v3 import RiskV3Wrapper


@dataclass
class _MockInnerStrategy:
    """Deterministic inner strategy returning a configurable signal sequence."""

    signals: dict[tuple[str, int], Signal] = field(default_factory=dict)
    atr_column: str = "natr_21_raw"
    features_dir: str = "data/features_v3"
    _interval: str = "8h"

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        return self.signals.get((symbol, open_time), NO_SIGNAL)

    def compute_features(self, master: pd.DataFrame) -> None:
        pass

    def skip(self) -> None:
        pass


def _inject_adx_lookup(
    wrapper: RiskV3Wrapper,
    symbol: str,
    entries: list[tuple[int, float]],
) -> None:
    """Inject synthetic ADX lookup entries directly into the wrapper's _lookup dict.

    Parameters
    ----------
    wrapper
        The RiskV3Wrapper to inject into.
    symbol
        The symbol to inject.
    entries
        List of (open_time_ms, adx_value) pairs. Will be sorted by open_time to
        satisfy np.searchsorted's requirement for a sorted array.

    This bypasses compute_features (which would need parquet I/O) and lets us test
    the ADX gate logic with known ADX values at specific (symbol, open_time) pairs.

    _row_for also requires atr_pct_rank_200, hurst_100, and features arrays.
    We inject neutral values (0.5 atr_pct, 0.5 hurst, zeros features) so those
    gates don't fire (they are all disabled in _make_wrapper anyway).
    """
    entries_sorted = sorted(entries, key=lambda x: x[0])
    n = len(entries_sorted)
    open_times = np.array([e[0] for e in entries_sorted], dtype=np.int64)
    adx_values = np.array([e[1] for e in entries_sorted], dtype=np.float64)
    # Neutral values for other lookup fields (atr_pct_rank_200, hurst_100 are
    # not used by ADX gate; all other gates are disabled in _make_wrapper).
    atr_pct = np.full(n, 0.5, dtype=np.float64)
    hurst = np.full(n, 0.5, dtype=np.float64)
    # features: shape (n, 0) — empty feature matrix (zscore OOD disabled in tests)
    features = np.zeros((n, 0), dtype=np.float64)
    wrapper._lookup[symbol] = {
        "open_time": open_times,
        "adx": adx_values,
        "atr_pct_rank_200": atr_pct,
        "hurst_100": hurst,
        "features": features,
    }


def _make_wrapper(
    *,
    global_adx_threshold: float = 20.0,
    adx_threshold_per_symbol: dict[str, float] | None = None,
    signals: dict[tuple[str, int], Signal] | None = None,
) -> RiskV3Wrapper:
    """Construct a RiskV3Wrapper with ONLY the ADX gate enabled (all others disabled)."""
    cfg = RiskV2Config(
        # All gates disabled except ADX — isolates per-symbol ADX override behavior.
        enable_vol_scaling=False,
        enable_hurst_check=False,
        enable_zscore_ood=False,
        enable_low_vol_filter=False,
        enable_per_symbol_cap=False,
        enable_regime_gate=False,
        block_long_for=(),
        block_short_for=(),
        # ADX gate enabled:
        enable_adx_gate=True,
        adx_threshold=global_adx_threshold,
        adx_threshold_per_symbol=(
            adx_threshold_per_symbol if adx_threshold_per_symbol is not None else {}
        ),
    )
    inner = _MockInnerStrategy(signals=signals or {})
    return RiskV3Wrapper(inner, cfg)


# ---------------------------------------------------------------------------
# Test 1: Unspecified symbol falls back to global adx_threshold
# ---------------------------------------------------------------------------


def test_unspecified_symbol_uses_global_threshold():
    """Symbol not in adx_threshold_per_symbol dict must use global adx_threshold.

    Scenario: global=20.0, per-symbol dict empty.
    ALGOUSDT at ADX=19.5 → gate kills (19.5 < 20.0 global).
    ALGOUSDT at ADX=20.5 → gate passes (20.5 >= 20.0 global).
    """
    open_time_low = 1_700_000_000_000
    open_time_high = 1_700_000_001_000
    long_sig = Signal(direction=1, weight=10, tp_pct=8.0, sl_pct=4.0)

    wrapper = _make_wrapper(
        global_adx_threshold=20.0,
        adx_threshold_per_symbol={},  # Empty dict — all symbols use global
        signals={
            ("ALGOUSDT", open_time_low): long_sig,
            ("ALGOUSDT", open_time_high): long_sig,
        },
    )
    _inject_adx_lookup(wrapper, "ALGOUSDT", [(open_time_low, 19.5), (open_time_high, 20.5)])

    result_low = wrapper.get_signal("ALGOUSDT", open_time_low)
    result_high = wrapper.get_signal("ALGOUSDT", open_time_high)

    assert result_low.direction == 0, (
        f"ADX=19.5 < global 20.0 → signal MUST be killed (direction=0); "
        f"got direction={result_low.direction}. "
        "iter-v3/049: empty per-symbol dict falls back to global threshold."
    )
    assert result_high.direction == 1, (
        f"ADX=20.5 >= global 20.0 → signal MUST pass through (direction=1); "
        f"got direction={result_high.direction}. "
        "iter-v3/049: empty per-symbol dict falls back to global threshold."
    )


# ---------------------------------------------------------------------------
# Test 2: Specified symbol uses per-symbol threshold, NOT global
# ---------------------------------------------------------------------------


def test_per_symbol_threshold_overrides_global():
    """Symbol in adx_threshold_per_symbol dict uses per-symbol value, not global.

    Scenario: global=20.0, {"TRXUSDT": 21.0}.
    TRXUSDT at ADX=20.5:
      - With per-symbol threshold 21.0: 20.5 < 21.0 → gate kills (direction=0).
      - Without per-symbol (global 20.0 only): 20.5 >= 20.0 → would pass.
    TRXUSDT at ADX=21.5:
      - With per-symbol threshold 21.0: 21.5 >= 21.0 → gate passes (direction=1).
    """
    open_time_between = 1_700_000_000_000  # ADX between global(20) and per-symbol(21)
    open_time_above = 1_700_000_001_000  # ADX above per-symbol(21)
    long_sig = Signal(direction=1, weight=10, tp_pct=8.0, sl_pct=4.0)

    wrapper = _make_wrapper(
        global_adx_threshold=20.0,
        adx_threshold_per_symbol={"TRXUSDT": 21.0},
        signals={
            ("TRXUSDT", open_time_between): long_sig,
            ("TRXUSDT", open_time_above): long_sig,
        },
    )
    _inject_adx_lookup(wrapper, "TRXUSDT", [(open_time_between, 20.5), (open_time_above, 21.5)])

    result_between = wrapper.get_signal("TRXUSDT", open_time_between)
    result_above = wrapper.get_signal("TRXUSDT", open_time_above)

    assert result_between.direction == 0, (
        f"TRXUSDT ADX=20.5: per-symbol threshold 21.0 → 20.5 < 21.0 → MUST be killed; "
        f"got direction={result_between.direction}. "
        "iter-v3/049: per-symbol threshold MUST override global (global 20.0 would pass)."
    )
    assert result_above.direction == 1, (
        f"TRXUSDT ADX=21.5: per-symbol threshold 21.0 → 21.5 >= 21.0 → MUST pass; "
        f"got direction={result_above.direction}. "
        "iter-v3/049: ADX above per-symbol threshold must pass through."
    )


# ---------------------------------------------------------------------------
# Test 3: Default empty dict preserves v1/v2/v3-prior behavior
# ---------------------------------------------------------------------------


def test_default_empty_dict_preserves_prior_behavior():
    """RiskV2Config() with default adx_threshold_per_symbol={}:
    all symbols use global threshold exactly as before iter-v3/049.

    Verifies backward-compatibility regression: the new field MUST have empty-dict
    semantics that are bit-identical to the pre-iter-v3/049 behavior.
    """
    open_time = 1_700_000_000_000
    long_sig = Signal(direction=1, weight=10, tp_pct=8.0, sl_pct=4.0)

    # Verify default_factory=dict produces {} by default
    cfg = RiskV2Config(
        enable_vol_scaling=False,
        enable_hurst_check=False,
        enable_zscore_ood=False,
        enable_low_vol_filter=False,
        enable_adx_gate=True,
        adx_threshold=20.0,
        # adx_threshold_per_symbol not specified → should default to {}
    )
    assert cfg.adx_threshold_per_symbol == {}, (
        f"RiskV2Config.adx_threshold_per_symbol default is {cfg.adx_threshold_per_symbol} "
        "— expected empty dict {{}}. iter-v3/049: default empty dict MUST preserve "
        "v1/v2/v3-prior behavior."
    )

    # With default empty dict: global 20.0 applies to all symbols
    wrapper = _make_wrapper(
        global_adx_threshold=20.0,
        adx_threshold_per_symbol={},
        signals={
            ("BCHUSDT", open_time): long_sig,
            ("TRXUSDT", open_time): long_sig,
            ("LDOUSDT", open_time): long_sig,
            ("ALGOUSDT", open_time): long_sig,
        },
    )
    for sym in ("BCHUSDT", "TRXUSDT", "LDOUSDT", "ALGOUSDT"):
        _inject_adx_lookup(wrapper, sym, [(open_time, 20.5)])  # ADX above global 20.0
        result = wrapper.get_signal(sym, open_time)
        assert result.direction == 1, (
            f"{sym} ADX=20.5 >= global 20.0: MUST pass through (direction=1); "
            f"got direction={result.direction}. iter-v3/049: default empty dict "
            "preserves prior behavior — no per-symbol override active."
        )


# ---------------------------------------------------------------------------
# Test 4: Multiple per-symbol thresholds work correctly
# ---------------------------------------------------------------------------


def test_multiple_per_symbol_thresholds():
    """Dict with multiple entries: each symbol uses its own value; non-listed use global.

    Scenario: global=20.0, {"TRXUSDT": 21.0, "ALGOUSDT": 22.0}.
    TRXUSDT at ADX=20.5 → per-symbol 21.0: 20.5 < 21.0 → kill.
    ALGOUSDT at ADX=21.5 → per-symbol 22.0: 21.5 < 22.0 → kill.
    BCHUSDT at ADX=20.5 → no per-symbol → global 20.0: 20.5 >= 20.0 → pass.
    LDOUSDT at ADX=19.5 → no per-symbol → global 20.0: 19.5 < 20.0 → kill.
    """
    base_time = 1_700_000_000_000
    long_sig = Signal(direction=1, weight=10, tp_pct=8.0, sl_pct=4.0)

    wrapper = _make_wrapper(
        global_adx_threshold=20.0,
        adx_threshold_per_symbol={"TRXUSDT": 21.0, "ALGOUSDT": 22.0},
        signals={
            ("TRXUSDT", base_time): long_sig,
            ("ALGOUSDT", base_time + 1): long_sig,
            ("BCHUSDT", base_time + 2): long_sig,
            ("LDOUSDT", base_time + 3): long_sig,
        },
    )
    _inject_adx_lookup(wrapper, "TRXUSDT", [(base_time, 20.5)])
    _inject_adx_lookup(wrapper, "ALGOUSDT", [(base_time + 1, 21.5)])
    _inject_adx_lookup(wrapper, "BCHUSDT", [(base_time + 2, 20.5)])
    _inject_adx_lookup(wrapper, "LDOUSDT", [(base_time + 3, 19.5)])

    trx_result = wrapper.get_signal("TRXUSDT", base_time)
    algo_result = wrapper.get_signal("ALGOUSDT", base_time + 1)
    bch_result = wrapper.get_signal("BCHUSDT", base_time + 2)
    ldo_result = wrapper.get_signal("LDOUSDT", base_time + 3)

    assert trx_result.direction == 0, (
        f"TRXUSDT ADX=20.5 < per-symbol 21.0 → MUST be killed; "
        f"got direction={trx_result.direction}."
    )
    assert algo_result.direction == 0, (
        f"ALGOUSDT ADX=21.5 < per-symbol 22.0 → MUST be killed; "
        f"got direction={algo_result.direction}."
    )
    assert bch_result.direction == 1, (
        f"BCHUSDT ADX=20.5 >= global 20.0 (no per-symbol) → MUST pass; "
        f"got direction={bch_result.direction}."
    )
    assert ldo_result.direction == 0, (
        f"LDOUSDT ADX=19.5 < global 20.0 (no per-symbol) → MUST be killed; "
        f"got direction={ldo_result.direction}."
    )


# ---------------------------------------------------------------------------
# Test 5: killed_by_adx counter increments on per-symbol threshold kill
# ---------------------------------------------------------------------------


def test_gate_stats_counter_increments_on_per_symbol_kill():
    """When per-symbol threshold kills a signal, killed_by_adx counter increments.

    The per-symbol ADX override REUSES the existing killed_by_adx counter (not a
    new separate counter) — the gate logic is identical, just the threshold lookup
    changes. Per iter-v3/049 brief Section 3 Sub-fix 6.
    """
    base_time = 1_700_000_000_000
    long_sig = Signal(direction=1, weight=10, tp_pct=8.0, sl_pct=4.0)

    # TRXUSDT: per-symbol threshold 21.0; 2 kills (ADX < 21.0) + 1 pass (ADX >= 21.0).
    # BCHUSDT: no per-symbol; 1 kill (ADX < global 20.0) + 1 pass (ADX >= 20.0).
    wrapper = _make_wrapper(
        global_adx_threshold=20.0,
        adx_threshold_per_symbol={"TRXUSDT": 21.0},
        signals={
            ("TRXUSDT", base_time): long_sig,  # ADX=20.3: per-sym 21 → kill
            ("TRXUSDT", base_time + 1): long_sig,  # ADX=20.8: per-sym 21 → kill
            ("TRXUSDT", base_time + 2): long_sig,  # ADX=21.5: per-sym 21 → pass
            ("BCHUSDT", base_time + 3): long_sig,  # ADX=19.5: global 20 → kill
            ("BCHUSDT", base_time + 4): long_sig,  # ADX=20.5: global 20 → pass
        },
    )
    _inject_adx_lookup(
        wrapper, "TRXUSDT", [(base_time, 20.3), (base_time + 1, 20.8), (base_time + 2, 21.5)]
    )
    _inject_adx_lookup(wrapper, "BCHUSDT", [(base_time + 3, 19.5), (base_time + 4, 20.5)])

    # Process all signals
    wrapper.get_signal("TRXUSDT", base_time)
    wrapper.get_signal("TRXUSDT", base_time + 1)
    wrapper.get_signal("TRXUSDT", base_time + 2)
    wrapper.get_signal("BCHUSDT", base_time + 3)
    wrapper.get_signal("BCHUSDT", base_time + 4)

    summary = wrapper.gate_stats_summary()
    trx_kills = summary.get("TRXUSDT", {}).get("killed_by_adx", 0)
    bch_kills = summary.get("BCHUSDT", {}).get("killed_by_adx", 0)

    assert trx_kills == 2, (
        f"TRXUSDT killed_by_adx: expected 2 (ADX 20.3 + 20.8 both < per-symbol 21.0); "
        f"got {trx_kills}. iter-v3/049: per-symbol threshold reuses killed_by_adx counter."
    )
    assert bch_kills == 1, (
        f"BCHUSDT killed_by_adx: expected 1 (ADX 19.5 < global 20.0); "
        f"got {bch_kills}. iter-v3/049: non-listed symbol still uses global threshold."
    )
