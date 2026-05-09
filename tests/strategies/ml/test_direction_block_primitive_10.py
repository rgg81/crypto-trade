"""Adversarial tests for the direction-asymmetric kill switch (iter-v3/047, primitive 10).

Tests per iter-v3/047 brief Section 3 Sub-fix 4 mandatory adversarial test:
  - LONG-direction signal blocked when symbol in block_long_for; SHORT passes through.
  - SHORT-direction signal blocked when symbol in block_short_for; LONG passes through.
  - Symbols NOT in block_long_for / block_short_for are unaffected.
  - NO_SIGNAL passes through unchanged regardless of block_long_for / block_short_for.
  - Counter (direction_block_fires) increments correctly.
  - Default config (block_long_for=(), block_short_for=()) preserves v1/v2/v3-prior behavior.
  - Test uses a deterministic mock LightGbmStrategy that returns fixed signals; no
    LightGBM training, no parquet I/O.

Fixture rationale:
  Real LightGbmStrategy + RiskV3Wrapper end-to-end test would require parquet features,
  trained models, and feature lookups — none of which are needed to validate primitive 10's
  signal-suppression behavior. We mock the inner strategy to expose the primitive in
  isolation. RiskV2Wrapper.get_signal calls inner.get_signal first, then runs gates;
  RiskV3Wrapper.get_signal applies primitive 9 first, then super().get_signal, then
  primitive 10. We disable all RiskV2 gates and primitive 9 to isolate primitive 10.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from crypto_trade.strategies import NO_SIGNAL, Signal
from crypto_trade.strategies.ml.risk_v2 import RiskV2Config
from crypto_trade.strategies.ml.risk_v3 import RiskV3Wrapper


@dataclass
class _MockInnerStrategy:
    """Deterministic inner strategy returning a configurable signal sequence.

    Used to isolate primitive 10's behavior without requiring LightGBM training or
    feature lookups. The mock implements the minimum Strategy protocol: get_signal,
    compute_features (no-op), skip (no-op), and the atr_column attribute that
    RiskV2Wrapper.atr_column delegates to.
    """

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


def _make_wrapper(
    *,
    block_long_for: tuple[str, ...] = (),
    block_short_for: tuple[str, ...] = (),
    signals: dict[tuple[str, int], Signal] | None = None,
) -> RiskV3Wrapper:
    """Construct a RiskV3Wrapper with all RiskV2 gates DISABLED so primitive 10 is
    the only effective filter (besides primitive 9, also disabled by default)."""
    cfg = RiskV2Config(
        # All RiskV2 gates disabled — primitive 10 is the only effective filter.
        enable_vol_scaling=False,
        enable_adx_gate=False,
        enable_hurst_check=False,
        enable_zscore_ood=False,
        enable_low_vol_filter=False,
        enable_per_symbol_cap=False,
        enable_regime_gate=False,
        # Primitive 10 is exercised by the test:
        block_long_for=block_long_for,
        block_short_for=block_short_for,
    )
    inner = _MockInnerStrategy(signals=signals or {})
    return RiskV3Wrapper(inner, cfg)


# ---------------------------------------------------------------------------
# Test 1: BCH LONG blocked, BCH SHORT passes through
# ---------------------------------------------------------------------------


def test_primitive_10_block_long_for_bch():
    """When block_long_for=("BCHUSDT",): BCH LONG → NO_SIGNAL; BCH SHORT → preserved."""
    open_time = 1_700_000_000_000
    bch_long = Signal(direction=1, weight=10, tp_pct=8.0, sl_pct=4.0)
    bch_short = Signal(direction=-1, weight=10, tp_pct=8.0, sl_pct=4.0)

    wrapper = _make_wrapper(
        block_long_for=("BCHUSDT",),
        signals={
            ("BCHUSDT", open_time): bch_long,
            ("BCHUSDT", open_time + 1): bch_short,
        },
    )

    result_long = wrapper.get_signal("BCHUSDT", open_time)
    result_short = wrapper.get_signal("BCHUSDT", open_time + 1)

    assert result_long.direction == 0, (
        f"BCH LONG must be blocked (direction=0); got direction={result_long.direction}. "
        "iter-v3/047 primitive 10: block_long_for=('BCHUSDT',) MUST suppress all BCH LONGs."
    )
    assert result_short.direction == -1, (
        f"BCH SHORT must pass through (direction=-1); got direction={result_short.direction}. "
        "iter-v3/047 primitive 10: block_long_for does NOT affect SHORT signals."
    )
    assert result_short.weight == bch_short.weight, (
        f"BCH SHORT weight must be preserved (no vol-scaling); got {result_short.weight}."
    )


# ---------------------------------------------------------------------------
# Test 2: Symbol NOT in block_long_for is completely unaffected
# ---------------------------------------------------------------------------


def test_primitive_10_other_symbol_not_blocked():
    """ALGO LONG must pass through when block_long_for=("BCHUSDT",) (ALGO not in list)."""
    open_time = 1_700_000_000_000
    algo_long = Signal(direction=1, weight=10, tp_pct=8.0, sl_pct=4.0)
    algo_short = Signal(direction=-1, weight=10, tp_pct=8.0, sl_pct=4.0)

    wrapper = _make_wrapper(
        block_long_for=("BCHUSDT",),
        signals={
            ("ALGOUSDT", open_time): algo_long,
            ("ALGOUSDT", open_time + 1): algo_short,
        },
    )

    result_long = wrapper.get_signal("ALGOUSDT", open_time)
    result_short = wrapper.get_signal("ALGOUSDT", open_time + 1)

    assert result_long.direction == 1, (
        "ALGO LONG must NOT be blocked when block_long_for=('BCHUSDT',). "
        f"Got direction={result_long.direction}."
    )
    assert result_short.direction == -1, (
        "ALGO SHORT must NOT be blocked when block_long_for=('BCHUSDT',). "
        f"Got direction={result_short.direction}."
    )


# ---------------------------------------------------------------------------
# Test 3: Default config (no blocks) preserves v1/v2/v3-prior behavior
# ---------------------------------------------------------------------------


def test_primitive_10_default_no_block():
    """When block_long_for=() and block_short_for=(): all signals pass through."""
    open_time = 1_700_000_000_000
    long_sig = Signal(direction=1, weight=10, tp_pct=8.0, sl_pct=4.0)
    short_sig = Signal(direction=-1, weight=10, tp_pct=8.0, sl_pct=4.0)

    wrapper = _make_wrapper(
        block_long_for=(),  # Default — no blocks
        block_short_for=(),
        signals={
            ("BCHUSDT", open_time): long_sig,
            ("BCHUSDT", open_time + 1): short_sig,
            ("ALGOUSDT", open_time): long_sig,
            ("ALGOUSDT", open_time + 1): short_sig,
        },
    )

    assert wrapper.get_signal("BCHUSDT", open_time).direction == 1, (
        "Default config (no blocks): BCH LONG must pass through."
    )
    assert wrapper.get_signal("BCHUSDT", open_time + 1).direction == -1, (
        "Default config (no blocks): BCH SHORT must pass through."
    )
    assert wrapper.get_signal("ALGOUSDT", open_time).direction == 1, (
        "Default config (no blocks): ALGO LONG must pass through."
    )
    assert wrapper.get_signal("ALGOUSDT", open_time + 1).direction == -1, (
        "Default config (no blocks): ALGO SHORT must pass through."
    )


# ---------------------------------------------------------------------------
# Test 4: NO_SIGNAL passes through regardless of block configuration
# ---------------------------------------------------------------------------


def test_primitive_10_no_signal_passes_through():
    """Inner returns NO_SIGNAL: primitive 10 should not increment counter or alter result."""
    open_time = 1_700_000_000_000

    wrapper = _make_wrapper(
        block_long_for=("BCHUSDT",),
        signals={
            ("BCHUSDT", open_time): NO_SIGNAL,  # Inner says no
        },
    )

    result = wrapper.get_signal("BCHUSDT", open_time)
    assert result.direction == 0, "NO_SIGNAL must pass through unchanged (direction=0)."

    # Counter must NOT increment for inner-NO_SIGNAL cases (no direction was blocked)
    summary = wrapper.gate_stats_summary()
    bch_stats = summary.get("BCHUSDT", {})
    assert bch_stats.get("direction_block_fires", 0) == 0, (
        "direction_block_fires must NOT increment when inner returns NO_SIGNAL. "
        f"Got {bch_stats.get('direction_block_fires', 0)}."
    )


# ---------------------------------------------------------------------------
# Test 5: Counter increments correctly
# ---------------------------------------------------------------------------


def test_primitive_10_counter_increments():
    """direction_block_fires counter increments by 1 per blocked signal."""
    base_time = 1_700_000_000_000
    long_sig = Signal(direction=1, weight=10, tp_pct=8.0, sl_pct=4.0)

    # 3 BCH LONGs (all should be blocked) + 2 BCH SHORTs (none blocked) +
    # 2 ALGO LONGs (none blocked).
    signals: dict[tuple[str, int], Signal] = {}
    for i in range(3):
        signals[("BCHUSDT", base_time + i)] = long_sig
    for i in range(2):
        signals[("BCHUSDT", base_time + 100 + i)] = Signal(
            direction=-1, weight=10, tp_pct=8.0, sl_pct=4.0
        )
    for i in range(2):
        signals[("ALGOUSDT", base_time + 200 + i)] = long_sig

    wrapper = _make_wrapper(
        block_long_for=("BCHUSDT",),
        signals=signals,
    )

    # Process all signals
    for sym, ot in signals:
        wrapper.get_signal(sym, ot)

    summary = wrapper.gate_stats_summary()
    bch_fires = summary.get("BCHUSDT", {}).get("direction_block_fires", 0)
    algo_fires = summary.get("ALGOUSDT", {}).get("direction_block_fires", 0)

    assert bch_fires == 3, (
        f"direction_block_fires for BCHUSDT: expected 3, got {bch_fires}. "
        "Counter should fire once per blocked LONG. (3 LONGs blocked, 2 SHORTs passed.)"
    )
    assert algo_fires == 0, (
        f"direction_block_fires for ALGOUSDT: expected 0, got {algo_fires}. "
        "ALGO is not in block_long_for; counter must not fire."
    )


# ---------------------------------------------------------------------------
# Test 6: block_short_for symmetry (sanity — even though unused at iter-v3/047)
# ---------------------------------------------------------------------------


def test_primitive_10_block_short_for_symmetry():
    """block_short_for=('BCHUSDT',): BCH SHORT → NO_SIGNAL; BCH LONG → preserved.

    iter-v3/047 sets block_short_for=() because BCH SHORT is the positive contributor.
    But the symmetric mechanism MUST work — other symbols/iterations may use it.
    """
    open_time = 1_700_000_000_000
    long_sig = Signal(direction=1, weight=10, tp_pct=8.0, sl_pct=4.0)
    short_sig = Signal(direction=-1, weight=10, tp_pct=8.0, sl_pct=4.0)

    wrapper = _make_wrapper(
        block_short_for=("BCHUSDT",),  # Block SHORTs instead
        signals={
            ("BCHUSDT", open_time): long_sig,
            ("BCHUSDT", open_time + 1): short_sig,
        },
    )

    result_long = wrapper.get_signal("BCHUSDT", open_time)
    result_short = wrapper.get_signal("BCHUSDT", open_time + 1)

    assert result_long.direction == 1, (
        f"With block_short_for=('BCHUSDT',): BCH LONG must pass through; "
        f"got direction={result_long.direction}."
    )
    assert result_short.direction == 0, (
        f"With block_short_for=('BCHUSDT',): BCH SHORT must be blocked; "
        f"got direction={result_short.direction}."
    )


# ---------------------------------------------------------------------------
# Test 7: gate_stats_summary contains the new direction_block_fires field
# ---------------------------------------------------------------------------


def test_primitive_10_summary_field_present():
    """gate_stats_summary() output must include 'direction_block_fires' for every
    symbol that has been processed."""
    open_time = 1_700_000_000_000
    long_sig = Signal(direction=1, weight=10, tp_pct=8.0, sl_pct=4.0)

    wrapper = _make_wrapper(
        block_long_for=("BCHUSDT",),
        signals={("BCHUSDT", open_time): long_sig},
    )

    wrapper.get_signal("BCHUSDT", open_time)
    summary = wrapper.gate_stats_summary()

    assert "BCHUSDT" in summary, "BCHUSDT must appear in gate_stats_summary."
    assert "direction_block_fires" in summary["BCHUSDT"], (
        "direction_block_fires field MUST be present in gate_stats_summary['BCHUSDT'] "
        "(added at iter-v3/047 primitive 10). "
        f"Available fields: {list(summary['BCHUSDT'].keys())}."
    )
    # Also verify primitive 9's regime_gate_fires field still present (regression check)
    assert "regime_gate_fires" in summary["BCHUSDT"], (
        "regime_gate_fires field (iter-v3/022 primitive 9) MUST still be present "
        "in gate_stats_summary."
    )
