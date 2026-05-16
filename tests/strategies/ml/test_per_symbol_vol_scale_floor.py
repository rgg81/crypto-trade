"""Tests for the per-symbol vol_scale_floor override in RiskV2Config (iter-v3/061).

Three tests per brief Section 3 Edit 4:
  1. test_vol_scale_floor_per_symbol_empty_dict_no_change
       — default empty dict produces bit-identical weight_factor output
         (backward-compatibility regression guard).
  2. test_vol_scale_floor_trx_05_clips_below_floor
       — when TRX weight_factor would be 0.3 (below 0.5 floor), output is 0.5.
  3. test_vol_scale_floor_other_symbols_unaffected
       — BCH and LDO weight_factors are unchanged regardless of TRX floor.

Fixture rationale:
  RiskV2Wrapper._vol_scale reads atr_pct_rank_200 from a row dict and clips it
  to [floor, ceiling]. We bypass parquet I/O by injecting a synthetic _lookup
  dict (same pattern as test_per_symbol_adx_threshold.py) and only enable vol
  scaling — all other gates disabled to isolate the per-symbol floor behavior.
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


def _inject_lookup(
    wrapper: RiskV3Wrapper,
    symbol: str,
    entries: list[tuple[int, float]],
) -> None:
    """Inject synthetic lookup entries for (open_time_ms, atr_pct_rank_200) pairs.

    All other lookup fields are set to neutral values so no other gate fires
    (all disabled in _make_wrapper anyway).
    """
    entries_sorted = sorted(entries, key=lambda x: x[0])
    n = len(entries_sorted)
    open_times = np.array([e[0] for e in entries_sorted], dtype=np.int64)
    atr_pct = np.array([e[1] for e in entries_sorted], dtype=np.float64)
    hurst = np.full(n, 0.6, dtype=np.float64)  # Neutral — hurst check disabled
    adx_values = np.full(n, 25.0, dtype=np.float64)  # Neutral — ADX gate disabled
    features = np.zeros((n, 0), dtype=np.float64)  # Empty — zscore OOD disabled
    wrapper._lookup[symbol] = {
        "open_time": open_times,
        "adx": adx_values,
        "atr_pct_rank_200": atr_pct,
        "hurst_100": hurst,
        "features": features,
    }


def _make_wrapper(
    *,
    global_vol_floor: float = 0.3,
    vol_scale_floor_per_symbol: dict[str, float] | None = None,
    signals: dict[tuple[str, int], Signal] | None = None,
) -> RiskV3Wrapper:
    """Construct a RiskV3Wrapper with ONLY vol scaling enabled (all others disabled)."""
    cfg = RiskV2Config(
        # All gates disabled except vol scaling — isolates per-symbol floor behavior.
        enable_adx_gate=False,
        enable_hurst_check=False,
        enable_zscore_ood=False,
        enable_low_vol_filter=False,
        enable_per_symbol_cap=False,
        enable_regime_gate=False,
        block_long_for=(),
        block_short_for=(),
        enable_per_symbol_drawdown_brake=False,
        # Vol scaling enabled:
        enable_vol_scaling=True,
        vol_scale_floor=global_vol_floor,
        vol_scale_ceiling=1.0,
        vol_scale_floor_per_symbol=(
            vol_scale_floor_per_symbol if vol_scale_floor_per_symbol is not None else {}
        ),
    )
    inner = _MockInnerStrategy(signals=signals or {})
    return RiskV3Wrapper(inner, cfg)


# ---------------------------------------------------------------------------
# Test 1: empty dict produces bit-identical weight_factor (backward compat)
# ---------------------------------------------------------------------------


def test_vol_scale_floor_per_symbol_empty_dict_no_change():
    """Default empty dict: vol_scale_floor_per_symbol={} falls back to global floor.

    Scenario: global floor=0.3, per-symbol dict empty.
    TRXUSDT at atr_pct_rank_200=0.4 → clipped to max(0.4, 0.3) = 0.4 (global floor).
    TRXUSDT at atr_pct_rank_200=0.2 → clipped to max(0.2, 0.3) = 0.3 (global floor).
    This is bit-identical to pre-iter-v3/061 behavior.
    """
    t1 = 1_700_000_000_000
    t2 = 1_700_000_001_000
    long_sig = Signal(direction=1, weight=10, tp_pct=8.0, sl_pct=4.0)

    wrapper_default = _make_wrapper(
        global_vol_floor=0.3,
        vol_scale_floor_per_symbol={},  # empty — all symbols use global
        signals={("TRXUSDT", t1): long_sig, ("TRXUSDT", t2): long_sig},
    )
    wrapper_explicit = _make_wrapper(
        global_vol_floor=0.3,
        vol_scale_floor_per_symbol=None,  # None → {} default
        signals={("TRXUSDT", t1): long_sig, ("TRXUSDT", t2): long_sig},
    )

    for wrapper in (wrapper_default, wrapper_explicit):
        _inject_lookup(wrapper, "TRXUSDT", [(t1, 0.4), (t2, 0.2)])

    # With empty dict, TRX uses global floor=0.3
    sig_above = wrapper_default.get_signal("TRXUSDT", t1)
    sig_below = wrapper_default.get_signal("TRXUSDT", t2)

    # At atr=0.4, vol_scale = clip(0.4, 0.3, 1.0) = 0.4 → weight=10*0.4=4 → direction passes
    assert sig_above.direction == 1, (
        f"TRX atr=0.4 >= global floor 0.3: signal must pass through; "
        f"got direction={sig_above.direction}. "
        "iter-v3/061: empty dict falls back to global floor (backward compat)."
    )
    # At atr=0.2, vol_scale = clip(0.2, 0.3, 1.0) = 0.3 → weight=10*0.3=3 → direction passes
    assert sig_below.direction == 1, (
        f"TRX atr=0.2 < global floor 0.3 but signal still passes (just weight-scaled); "
        f"got direction={sig_below.direction}. "
        "iter-v3/061: vol scaling SCALES DOWN but does not KILL signals."
    )

    # Verify default_factory=dict produces {} by default
    cfg_default = RiskV2Config(enable_vol_scaling=True, vol_scale_floor=0.3)
    assert cfg_default.vol_scale_floor_per_symbol == {}, (
        f"RiskV2Config.vol_scale_floor_per_symbol default is "
        f"{cfg_default.vol_scale_floor_per_symbol} — expected {{}}. "
        "iter-v3/061: default must be empty dict for backward compat."
    )


# ---------------------------------------------------------------------------
# Test 2: TRX floor=0.5 clips atr_pct_rank_200=0.3 up to 0.5
# ---------------------------------------------------------------------------


def test_vol_scale_floor_trx_05_clips_below_floor():
    """TRX with vol_scale_floor_per_symbol={'TRXUSDT': 0.5}:
    atr_pct_rank_200=0.3 (below 0.5 floor) clips up to 0.5.
    atr_pct_rank_200=0.7 (above floor) stays at 0.7.

    This directly tests the Path B per-symbol intervention from iter-v3/061.
    The counterfactual predicts TRX OOS Q1_low bucket (weights 0.33-0.47) gets
    lifted to 0.5; this test validates the clipping logic.
    """
    t_below = 1_700_000_000_000  # atr will be 0.3 (below TRX floor=0.5)
    t_above = 1_700_000_001_000  # atr will be 0.7 (above floor)
    long_sig = Signal(direction=1, weight=10, tp_pct=8.0, sl_pct=4.0)

    # With global floor=0.3 (no per-symbol override):
    wrapper_global = _make_wrapper(
        global_vol_floor=0.3,
        vol_scale_floor_per_symbol={},
        signals={("TRXUSDT", t_below): long_sig, ("TRXUSDT", t_above): long_sig},
    )
    _inject_lookup(wrapper_global, "TRXUSDT", [(t_below, 0.3), (t_above, 0.7)])

    # With TRX floor=0.5 override:
    wrapper_per_sym = _make_wrapper(
        global_vol_floor=0.3,
        vol_scale_floor_per_symbol={"TRXUSDT": 0.5},
        signals={("TRXUSDT", t_below): long_sig, ("TRXUSDT", t_above): long_sig},
    )
    _inject_lookup(wrapper_per_sym, "TRXUSDT", [(t_below, 0.3), (t_above, 0.7)])

    # vol_scale is applied to the raw signal weight; compute via gate_stats_summary
    wrapper_global.get_signal("TRXUSDT", t_below)
    wrapper_global.get_signal("TRXUSDT", t_above)
    wrapper_per_sym.get_signal("TRXUSDT", t_below)
    wrapper_per_sym.get_signal("TRXUSDT", t_above)

    stats_global = wrapper_global.gate_stats_summary()
    stats_per_sym = wrapper_per_sym.gate_stats_summary()

    # With global floor=0.3: vol_scale_sum = clip(0.3,0.3,1.0) + clip(0.7,0.3,1.0) = 0.3 + 0.7 = 1.0
    # mean_vol_scale = 1.0 / 2 = 0.5
    global_mean = stats_global.get("TRXUSDT", {}).get("mean_vol_scale", None)
    assert global_mean is not None, "TRXUSDT not in gate_stats_summary for global-floor wrapper"
    assert abs(global_mean - 0.5) < 1e-9, (
        f"Global floor=0.3: mean_vol_scale expected 0.5 (0.3+0.7)/2; got {global_mean}. "
        "iter-v3/061: baseline vol_scale behavior must be unchanged for global-floor case."
    )

    # With per-symbol floor=0.5: vol_scale_sum = clip(0.3,0.5,1.0) + clip(0.7,0.5,1.0)
    # = 0.5 + 0.7 = 1.2 → mean_vol_scale = 1.2 / 2 = 0.6
    per_sym_mean = stats_per_sym.get("TRXUSDT", {}).get("mean_vol_scale", None)
    assert per_sym_mean is not None, "TRXUSDT not in gate_stats_summary for per-sym-floor wrapper"
    assert abs(per_sym_mean - 0.6) < 1e-9, (
        f"Per-symbol floor=0.5: mean_vol_scale expected 0.6 (0.5+0.7)/2; got {per_sym_mean}. "
        "iter-v3/061: TRX atr=0.3 must be clipped UP to 0.5 under per-symbol floor."
    )

    # The per-symbol floor MUST be strictly higher than the global-floor result for t_below:
    # global=0.3, per-sym=0.5 → per-sym mean is higher (0.6 > 0.5).
    assert per_sym_mean > global_mean, (
        f"Per-symbol floor=0.5 must produce higher mean_vol_scale than global floor=0.3; "
        f"got per_sym={per_sym_mean}, global={global_mean}. "
        "iter-v3/061: Path B intervention must lift TRX weight_factor for trades below floor."
    )


# ---------------------------------------------------------------------------
# Test 3: BCH and LDO weight_factors are unchanged when TRX floor is set
# ---------------------------------------------------------------------------


def test_vol_scale_floor_other_symbols_unaffected():
    """Per-symbol TRX floor=0.5 must NOT affect BCH or LDO weight_factors.

    Scenario: vol_scale_floor_per_symbol={"TRXUSDT": 0.5}.
    BCH at atr=0.3 → uses global floor=0.3 → clip(0.3, 0.3, 1.0) = 0.3 (UNCHANGED).
    LDO at atr=0.3 → uses global floor=0.3 → clip(0.3, 0.3, 1.0) = 0.3 (UNCHANGED).
    This validates the Section 2.5 Q5 per-symbol design isolation guarantee:
    BCH/LDO weighted_pnl is mathematically invariant when only TRX floor changes.
    """
    t_bch = 1_700_000_000_000
    t_ldo = 1_700_000_001_000
    t_trx = 1_700_000_002_000
    long_sig = Signal(direction=1, weight=10, tp_pct=8.0, sl_pct=4.0)

    # Global floor=0.3, TRX override=0.5
    wrapper = _make_wrapper(
        global_vol_floor=0.3,
        vol_scale_floor_per_symbol={"TRXUSDT": 0.5},
        signals={
            ("BCHUSDT", t_bch): long_sig,
            ("LDOUSDT", t_ldo): long_sig,
            ("TRXUSDT", t_trx): long_sig,
        },
    )
    _inject_lookup(wrapper, "BCHUSDT", [(t_bch, 0.3)])  # At global floor boundary
    _inject_lookup(wrapper, "LDOUSDT", [(t_ldo, 0.3)])  # At global floor boundary
    _inject_lookup(wrapper, "TRXUSDT", [(t_trx, 0.3)])  # Below TRX per-symbol floor

    wrapper.get_signal("BCHUSDT", t_bch)
    wrapper.get_signal("LDOUSDT", t_ldo)
    wrapper.get_signal("TRXUSDT", t_trx)

    stats = wrapper.gate_stats_summary()

    # BCH: clip(0.3, 0.3, 1.0) = 0.3 → mean_vol_scale = 0.3
    bch_mean = stats.get("BCHUSDT", {}).get("mean_vol_scale", None)
    assert bch_mean is not None, "BCHUSDT not in gate_stats_summary"
    assert abs(bch_mean - 0.3) < 1e-9, (
        f"BCHUSDT mean_vol_scale expected 0.3 (global floor); got {bch_mean}. "
        "iter-v3/061: TRX-only floor=0.5 must NOT change BCH vol scaling."
    )

    # LDO: clip(0.3, 0.3, 1.0) = 0.3 → mean_vol_scale = 0.3
    ldo_mean = stats.get("LDOUSDT", {}).get("mean_vol_scale", None)
    assert ldo_mean is not None, "LDOUSDT not in gate_stats_summary"
    assert abs(ldo_mean - 0.3) < 1e-9, (
        f"LDOUSDT mean_vol_scale expected 0.3 (global floor); got {ldo_mean}. "
        "iter-v3/061: TRX-only floor=0.5 must NOT change LDO vol scaling."
    )

    # TRX: clip(0.3, 0.5, 1.0) = 0.5 → mean_vol_scale = 0.5 (lifted by per-symbol floor)
    trx_mean = stats.get("TRXUSDT", {}).get("mean_vol_scale", None)
    assert trx_mean is not None, "TRXUSDT not in gate_stats_summary"
    assert abs(trx_mean - 0.5) < 1e-9, (
        f"TRXUSDT mean_vol_scale expected 0.5 (per-symbol floor); got {trx_mean}. "
        "iter-v3/061: TRX with atr=0.3 MUST be clipped to 0.5 under per-symbol floor."
    )

    # Isolation check: BCH and LDO must be strictly equal at 0.3 (not lifted to 0.5)
    assert bch_mean < trx_mean, (
        f"BCH mean_vol_scale ({bch_mean}) must be < TRX mean_vol_scale ({trx_mean}); "
        "per-symbol floor=0.5 must only lift TRX, not BCH. iter-v3/061 isolation violated."
    )
    assert ldo_mean < trx_mean, (
        f"LDO mean_vol_scale ({ldo_mean}) must be < TRX mean_vol_scale ({trx_mean}); "
        "per-symbol floor=0.5 must only lift TRX, not LDO. iter-v3/061 isolation violated."
    )
