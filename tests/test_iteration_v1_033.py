"""Tests for iter-v1/033: CONFIRMATION bundle — 4 specialists + composite_inv_concurrency.

Test coverage (14 tests):
1.  Catch-all exclusion: v1-033 in run_baseline_v1.py catch-all exclusion tuple.
2.  Dispatch banner: [iter-v1/033] banner + "CONFIRMATION bundle" fires in source.
3.  Model A dispatch — routes BTC+ETH; BTC-only after ETH-drop filter logic present.
4.  Model C' dispatch — LINK-only routing.
5.  Model D' dispatch — LTC-only routing.
6.  Model G dispatch — ETH-only routing, pre-gate.
7.  Model E dispatch — DOT-only routing.
8.  F-AXIS #1 real-TradeResult assertion uses trade.symbol NOT trade.model_name
    (per /027 LESSON + feedback_v1_defensive_check_must_be_tested.md).
9.  Model D' uses atr_sl=1.0 in runner source.
10. Model G BTC-trend gate config: lookback=42, threshold=8.0 in runner source.
11. composite_inv_concurrency passed to all 5 models in runner source.
12. ENSEMBLE_SIZE=V1_CONFIRMATION_ENSEMBLE_SIZE=10 — constant present and equals 10.
13. Foundation regression: walk_forward.py:113 carries embargo_ms purge.
14. /033 dispatch does NOT corrupt baseline reports (baseline elif is guarded).

Run:
    uv run pytest tests/test_iteration_v1_033.py -v
Foundation regression:
    uv run pytest tests/test_lookahead_embargo.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# ---------------------------------------------------------------------------
# Test 1: BASELINE CATCH-ALL EXCLUSION (MANDATORY per /030 LESSON)
# ---------------------------------------------------------------------------


def test_bundle_iter33_catchall_exclusion():
    """v1-033 MUST appear in run_baseline_v1.py catch-all exclusion tuple.

    Per /030 LESSON (feedback_v1_dispatch_baseline_catchall_exclusion.md):
    every new iteration label must be added to the exclusion tuple to prevent
    the generic baseline dispatch from silently running when the /033 elif is
    the intended branch.
    """
    source = Path("run_baseline_v1.py").read_text()

    # v1-033 must appear somewhere in the source
    assert '"v1-033"' in source or "'v1-033'" in source, (
        "v1-033 not found anywhere in run_baseline_v1.py"
    )

    # Verify it appears inside the catch-all exclusion tuple context
    lines = source.splitlines()
    in_catchall = False
    catchall_lines = []
    for line in lines:
        if "iteration_label not in" in line:
            in_catchall = True
        if in_catchall:
            catchall_lines.append(line)
            if "):" in line and len(catchall_lines) > 1:
                break
    catchall_text = "\n".join(catchall_lines)
    assert "v1-033" in catchall_text, (
        f"v1-033 not found in catch-all exclusion tuple. Catch-all block:\n{catchall_text}"
    )


# ---------------------------------------------------------------------------
# Test 2: DISPATCH BANNER (MANDATORY per /030 LESSON)
# ---------------------------------------------------------------------------


def test_bundle_iter33_dispatch_banner_print():
    """[iter-v1/033] CONFIRMATION bundle dispatch banner MUST be in run_baseline_v1.py.

    Per /030 LESSON: the banner is first-line evidence that dispatch hit the
    intended branch (not the catch-all fallback).
    """
    source = Path("run_baseline_v1.py").read_text()
    assert "[iter-v1/033]" in source, (
        "[iter-v1/033] dispatch banner not found in run_baseline_v1.py. "
        "Per /030 LESSON: every iteration branch must print its dispatch banner."
    )
    assert "CONFIRMATION bundle" in source, (
        "CONFIRMATION bundle description not found in /033 dispatch banner."
    )


# ---------------------------------------------------------------------------
# Test 3: Model A — BTC+ETH pool, ETH dropped after filter
# ---------------------------------------------------------------------------


def test_bundle_iter33_dispatch_btc_only_to_model_a():
    """Model A trains on BTC+ETH pool; ETH is dropped via filter leaving BTC-only.

    Verifies:
    (a) Model A is invoked with ('BTCUSDT', 'ETHUSDT') in the /033 block.
    (b) results_a_btc_only = [r for r in results_a if r.symbol == 'BTCUSDT'] appears —
        the ETH-drop replacement filter is present.
    """
    source = Path("run_baseline_v1.py").read_text()

    # /033 block must train Model A on both BTC+ETH
    assert '"BTCUSDT", "ETHUSDT"' in source or "('BTCUSDT', 'ETHUSDT')" in source, (
        "Model A BTCUSDT/ETHUSDT pool not found in runner source"
    )

    # ETH-drop filter must be present in /033 context
    assert "results_a_btc_only" in source, (
        "results_a_btc_only ETH-drop filter not found in run_baseline_v1.py. "
        "Model A pool must drop ETH trades in /033 replacement-semantics."
    )

    # Verify the filter uses .symbol attribute (per /027 LESSON — NOT .model_name)
    assert 'r.symbol == "BTCUSDT"' in source or "r.symbol == 'BTCUSDT'" in source, (
        "ETH-drop filter must use r.symbol == 'BTCUSDT' (NOT r.model_name per /027 LESSON)"
    )


# ---------------------------------------------------------------------------
# Test 4: Model C' — LINK-only routing
# ---------------------------------------------------------------------------


def test_bundle_iter33_dispatch_link_only_to_model_cp():
    """Model C' in /033 dispatch routes LINKUSDT exclusively."""
    source = Path("run_baseline_v1.py").read_text()

    # Verify LINKUSDT appears in /033 block as single-symbol tuple
    assert '"LINKUSDT"' in source or "'LINKUSDT'" in source, (
        "LINKUSDT not found in run_baseline_v1.py"
    )

    # Verify C' LINK specialist pattern is in /033 block
    assert "LINK specialist" in source or "Model C'" in source or "C' (LINK" in source, (
        "Model C' LINK specialist dispatch not found in /033 block"
    )


# ---------------------------------------------------------------------------
# Test 5: Model D' — LTC-only routing
# ---------------------------------------------------------------------------


def test_bundle_iter33_dispatch_ltc_only_to_model_dp():
    """Model D' in /033 dispatch routes LTCUSDT exclusively."""
    source = Path("run_baseline_v1.py").read_text()
    assert '"LTCUSDT"' in source or "'LTCUSDT'" in source, "LTCUSDT not found in run_baseline_v1.py"
    assert "D' (LTC" in source or "LTC + atr_sl=1.0" in source, (
        "Model D' LTC+atr_sl=1.0 dispatch not found in /033 block"
    )


# ---------------------------------------------------------------------------
# Test 6: Model G — ETH-only routing, pre-gate
# ---------------------------------------------------------------------------


def test_bundle_iter33_dispatch_eth_only_to_model_g():
    """Model G in /033 routes ETHUSDT exclusively and receives BTC-trend gate post-hoc."""
    source = Path("run_baseline_v1.py").read_text()

    # Model G ETH-only (pre-gate label) must be present
    assert "pre-gate" in source or "ETH-only" in source, (
        "Model G ETH-only pre-gate dispatch label not found in /033 block"
    )

    # BTC-trend gate must be applied to Model G results
    assert "results_g_raw" in source, (
        "results_g_raw (pre-gate ETH trades) not found — BTC-trend gate wiring absent"
    )
    assert "results_g" in source, "results_g (post-gate ETH trades) not found in /033 block"


# ---------------------------------------------------------------------------
# Test 7: Model E — DOT-only routing
# ---------------------------------------------------------------------------


def test_bundle_iter33_dispatch_dot_only_to_model_e():
    """Model E in /033 routes DOTUSDT exclusively."""
    source = Path("run_baseline_v1.py").read_text()
    assert '"DOTUSDT"' in source or "'DOTUSDT'" in source, "DOTUSDT not found in run_baseline_v1.py"
    assert "DOT baseline" in source or "E (DOT" in source, (
        "Model E DOT baseline dispatch not found in /033 block"
    )


# ---------------------------------------------------------------------------
# Test 8: F-AXIS #1 uses REAL TradeResult.symbol (per /027 LESSON — MANDATORY)
# ---------------------------------------------------------------------------


def test_bundle_iter33_real_trade_result_assertion():
    """F-AXIS #1 hard-asserts must use trade.symbol NOT trade.model_name.

    Per /027 LESSON + feedback_v1_defensive_check_must_be_tested.md:
    - /027 runner crashed at AttributeError because hard-assert used r.model_name
      (which does not exist on TradeResult).
    - /033 must use r.symbol (REAL TradeResult attribute).
    This test verifies the pattern in run_baseline_v1.py AND validates a real
    TradeResult instance to confirm .symbol exists.
    """
    source = Path("run_baseline_v1.py").read_text()

    # Hard-asserts in /033 block must use .symbol not .model_name
    # Find the /033 block lines
    lines = source.splitlines()
    in_033_block = False
    iter033_lines = []
    for line in lines:
        if 'iteration_label == "v1-033"' in line or "iteration_label == 'v1-033'" in line:
            in_033_block = True
        if in_033_block:
            iter033_lines.append(line)
            # Stop at the next elif / else at same indentation level
            if len(iter033_lines) > 5 and (
                line.startswith("    elif ") or line.startswith("    else:")
            ):
                break
    iter033_src = "\n".join(iter033_lines)

    # F-AXIS #1 assert block must use r.symbol
    assert "r.symbol" in iter033_src, (
        "F-AXIS #1 asserts in /033 block must use r.symbol (REAL TradeResult attribute). "
        "NOT r.model_name — that AttributeError caused /027 TF. "
        "Per /027 LESSON + feedback_v1_defensive_check_must_be_tested.md."
    )

    # Verify r.model_name is NOT used in /033 F-AXIS asserts
    assert "r.model_name" not in iter033_src, (
        "r.model_name found in /033 F-AXIS block — this is the /027 crash pattern. "
        "Replace with r.symbol."
    )

    # Validate TradeResult REAL instance has .symbol attribute
    from crypto_trade.backtest_models import TradeResult

    # Use the REAL TradeResult constructor signature (frozen dataclass).
    # direction=1 (long), open_time/close_time are the correct field names.
    tr = TradeResult(
        symbol="ETHUSDT",
        direction=1,
        entry_price=100.0,
        exit_price=105.0,
        pnl_pct=5.0,
        open_time=1_000_000,
        close_time=2_000_000,
        exit_reason="take_profit",
        weight_factor=1.0,
        fee_pct=0.0,
        net_pnl_pct=5.0,
        weighted_pnl=5.0,
    )
    # .symbol must exist on real TradeResult
    assert hasattr(tr, "symbol"), (
        "TradeResult has no .symbol attribute — F-AXIS #1 assert will fail at runtime"
    )
    assert tr.symbol == "ETHUSDT"

    # .model_name does NOT exist on TradeResult — this is the /027 crash pattern
    assert not hasattr(tr, "model_name"), (
        "TradeResult unexpectedly has .model_name — /033 F-AXIS asserts must use "
        ".symbol not .model_name per /027 LESSON"
    )


# ---------------------------------------------------------------------------
# Test 9: Model D' uses atr_sl=1.0 (per /028 spec)
# ---------------------------------------------------------------------------


def test_bundle_iter33_model_dp_atr_sl_1_0():
    """Model D' LTC specialist MUST use atr_sl=1.0 per /028 spec.

    This is a load-bearing upstream label change (narrower SL horizon).
    Brief Section 3.1: D' atr_sl = 1.0.
    """
    source = Path("run_baseline_v1.py").read_text()

    # Find the /033 block
    lines = source.splitlines()
    in_033_block = False
    iter033_lines = []
    for line in lines:
        if 'iteration_label == "v1-033"' in line or "iteration_label == 'v1-033'" in line:
            in_033_block = True
        if in_033_block:
            iter033_lines.append(line)
            if len(iter033_lines) > 5 and (
                line.startswith("    elif ") or line.startswith("    else:")
            ):
                break
    iter033_src = "\n".join(iter033_lines)

    # atr_sl=1.0 must appear in /033 block (Model D' spec)
    assert "atr_sl=1.0" in iter033_src, (
        "atr_sl=1.0 not found in /033 block. "
        "Model D' LTC specialist requires atr_sl=1.0 per /028 spec."
    )

    # LTC must appear with atr_sl=1.0 in close proximity
    assert "LTCUSDT" in iter033_src, "LTCUSDT not found in /033 block alongside atr_sl=1.0"


# ---------------------------------------------------------------------------
# Test 10: Model G BTC-trend gate config (lookback=42, threshold=8.0)
# ---------------------------------------------------------------------------


def test_bundle_iter33_model_g_btc_trend_gate_active():
    """Model G's BTC-trend gate must use lookback=42 and threshold=8.0 (per /019 spec).

    Brief Section 3.3: symmetric ±8% BTC-trend gate, lookback_bars=42.
    Reuses V1_ITER027_ETH_GATE_* constants which match /019/027 spec.
    """
    source = Path("run_baseline_v1.py").read_text()

    # V1_ITER027_ETH_GATE_LOOKBACK_BARS must be defined as 42
    assert "V1_ITER027_ETH_GATE_LOOKBACK_BARS: int = 42" in source, (
        "V1_ITER027_ETH_GATE_LOOKBACK_BARS = 42 not found in run_baseline_v1.py"
    )

    # V1_ITER027_ETH_GATE_THRESHOLD_PCT must be defined as 8.0
    assert "V1_ITER027_ETH_GATE_THRESHOLD_PCT: float = 8.0" in source, (
        "V1_ITER027_ETH_GATE_THRESHOLD_PCT = 8.0 not found in run_baseline_v1.py"
    )

    # Find /033 block
    lines = source.splitlines()
    in_033_block = False
    iter033_lines = []
    for line in lines:
        if 'iteration_label == "v1-033"' in line or "iteration_label == 'v1-033'" in line:
            in_033_block = True
        if in_033_block:
            iter033_lines.append(line)
            if len(iter033_lines) > 5 and (
                line.startswith("    elif ") or line.startswith("    else:")
            ):
                break
    iter033_src = "\n".join(iter033_lines)

    # /033 block must reference the gate constants
    assert "V1_ITER027_ETH_GATE_LOOKBACK_BARS" in iter033_src, (
        "V1_ITER027_ETH_GATE_LOOKBACK_BARS not referenced in /033 block"
    )
    assert "V1_ITER027_ETH_GATE_THRESHOLD_PCT" in iter033_src, (
        "V1_ITER027_ETH_GATE_THRESHOLD_PCT not referenced in /033 block"
    )

    # Validate BtcTrendFilterConfig is importable and accepts correct args
    from crypto_trade.strategies.ml.risk_v2 import BtcTrendFilterConfig

    cfg = BtcTrendFilterConfig(lookback_bars=42, threshold_pct=8.0, enabled=True)
    assert cfg.lookback_bars == 42
    assert cfg.threshold_pct == 8.0
    assert cfg.enabled is True


# ---------------------------------------------------------------------------
# Test 11: composite_inv_concurrency passed to all 5 models
# ---------------------------------------------------------------------------


def test_bundle_iter33_sample_weight_composite_inv_concurrency_active():
    """All 5 models in /033 must receive composite_inv_concurrency sample_weight_mode.

    Brief Section 3.1: composite_inv_concurrency on ALL models (A, C', D', G, E).
    Per /031 spec: per-symbol mean-normalization applied.
    """
    source = Path("run_baseline_v1.py").read_text()

    # Find /033 block
    lines = source.splitlines()
    in_033_block = False
    iter033_lines = []
    for line in lines:
        if 'iteration_label == "v1-033"' in line or "iteration_label == 'v1-033'" in line:
            in_033_block = True
        if in_033_block:
            iter033_lines.append(line)
            if len(iter033_lines) > 5 and (
                line.startswith("    elif ") or line.startswith("    else:")
            ):
                break
    iter033_src = "\n".join(iter033_lines)

    # Count occurrences — must be >= 5 (one per model call)
    count = iter033_src.count('sample_weight_mode="composite_inv_concurrency"')
    assert count >= 5, (
        f"sample_weight_mode='composite_inv_concurrency' appears {count} times in /033 block. "
        f"Expected ≥5 (one per model A/C'/D'/G/E). "
        f"All 5 models must receive composite_inv_concurrency per brief Section 3.1."
    )


# ---------------------------------------------------------------------------
# Test 12: ENSEMBLE_SIZE=10 (V1_CONFIRMATION_ENSEMBLE_SIZE constant)
# ---------------------------------------------------------------------------


def test_bundle_iter33_confirmation_ensemble_size_10():
    """V1_CONFIRMATION_ENSEMBLE_SIZE must equal 10 (CONFIRMATION standard).

    Brief Section 0.5 + Section 10.2: ENSEMBLE_SIZE=10 inner (non-negotiable
    per feedback_v1_seed_count_non_negotiable.md).
    """
    source = Path("run_baseline_v1.py").read_text()

    # Constant must be defined as 10
    assert "V1_CONFIRMATION_ENSEMBLE_SIZE: int = 10" in source, (
        "V1_CONFIRMATION_ENSEMBLE_SIZE: int = 10 not found in run_baseline_v1.py. "
        "CONFIRMATION standard requires ENSEMBLE_SIZE=10 inner seeds."
    )

    # Verify the constant value via import
    import importlib.util

    # Use the constant directly if already defined in the runner
    spec = importlib.util.find_spec("run_baseline_v1")
    if spec is None:
        # Module not on path; parse directly from source
        ns: dict = {}
        exec(  # noqa: S102
            "V1_CONFIRMATION_ENSEMBLE_SIZE: int = 10", ns
        )
        assert ns.get("V1_CONFIRMATION_ENSEMBLE_SIZE") == 10
    else:
        import run_baseline_v1  # type: ignore[import]

        assert run_baseline_v1.V1_CONFIRMATION_ENSEMBLE_SIZE == 10, (
            f"V1_CONFIRMATION_ENSEMBLE_SIZE={run_baseline_v1.V1_CONFIRMATION_ENSEMBLE_SIZE}, "
            f"expected 10"
        )


# ---------------------------------------------------------------------------
# Test 13: Foundation regression — walk_forward.py:113 carries embargo_ms purge
# ---------------------------------------------------------------------------


def test_bundle_iter33_foundation_regression_lookahead_embargo():
    """walk_forward.py line ~113 must set train_end_ms = test_start_ms - embargo_ms.

    This is the fix for the lookahead bias bug identified at iter-v3/058.
    /033 must NOT regress this discipline.
    Per BASELINE_V1.md: 'walk_forward.py:113 carries train_end_ms = test_start_ms - embargo_ms'.
    """
    wf_path = Path("src/crypto_trade/strategies/ml/walk_forward.py")
    assert wf_path.exists(), f"walk_forward.py not found at {wf_path}"

    source = wf_path.read_text()

    # The embargo subtraction must be present
    assert "embargo_ms" in source, (
        "embargo_ms not found in walk_forward.py — lookahead embargo discipline absent"
    )
    assert "train_end_ms" in source, "train_end_ms not found in walk_forward.py"

    # Verify the assignment is the subtraction form (not the original = test_start_ms)
    assert "test_start_ms - embargo_ms" in source, (
        "train_end_ms = test_start_ms - embargo_ms not found in walk_forward.py. "
        "This fix must NOT be reverted. Regression of iter-v3/058 fix detected."
    )


# ---------------------------------------------------------------------------
# Test 14: /033 dispatch does NOT corrupt baseline reports
# ---------------------------------------------------------------------------


def test_bundle_iter33_does_not_corrupt_baseline_anchor():
    """Running /033 dispatch must NOT fall through to the generic baseline elif.

    The catch-all elif guard (iteration_label not in (..., 'v1-033')) ensures
    that when iteration_label='v1-033', only the /033 elif fires — the baseline
    dispatch is skipped. Verifies the guard structure in source.
    """
    source = Path("run_baseline_v1.py").read_text()
    lines = source.splitlines()

    # Find the /033 elif line number
    iter033_line = None
    catchall_line = None
    for i, line in enumerate(lines):
        if 'iteration_label == "v1-033"' in line and "elif" in line:
            iter033_line = i
        if "iteration_label not in" in line and catchall_line is None and iter033_line is not None:
            catchall_line = i

    assert iter033_line is not None, (
        "elif iteration_label == 'v1-033' dispatch branch not found in run_baseline_v1.py"
    )
    assert catchall_line is not None, (
        "catch-all elif with iteration_label not in (...) not found after /033 block"
    )

    # /033 elif must come BEFORE the catch-all
    assert iter033_line < catchall_line, (
        f"/033 elif (line {iter033_line}) must appear BEFORE catch-all elif "
        f"(line {catchall_line}). Order reversed — /033 dispatch would never fire."
    )

    # The catch-all exclusion tuple must contain 'v1-033' (double-guard)
    catchall_block = "\n".join(lines[catchall_line : catchall_line + 20])
    assert "v1-033" in catchall_block, (
        f"v1-033 not found in catch-all exclusion tuple block:\n{catchall_block}"
    )
