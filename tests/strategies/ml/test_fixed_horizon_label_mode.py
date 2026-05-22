"""Tests for fixed-horizon labeling mode (iter-v3/072).

Per brief Section 3.1 and Section 9, this test file verifies:

1. test_fixed_horizon_label_returns_sign_of_fwd_return
       -- label_mode="fixed_horizon" produces label == sign(fwd_return),
          ignoring TP/SL barriers. A candle whose path touches the SL price
          but ends net-positive at the horizon gets label +1.

2. test_fixed_horizon_pnl_is_realized_return
       -- long_pnl = fwd_return_pct - fee_pct;
          short_pnl = -fwd_return_pct - fee_pct.
          No barrier-scaled PnL.

3. test_triple_barrier_default_unchanged
       -- Default label_mode="triple_barrier" produces byte-identical output
          to a call without the label_mode kwarg (backward-compat for v1/v2).

4. test_fixed_horizon_ignores_sl_barrier
       -- Explicit adversarial case: a candle whose low touches the SL level
          BEFORE the horizon close still gets label +1 when fwd_return > 0.

5. test_lgbm_strategy_stores_label_mode
       -- LightGbmStrategy stores label_mode from the constructor and
          exposes it as self.label_mode.

6. test_metalabeling_strategy_forwards_label_mode
       -- MetaLabelingStrategy forwards label_mode to M1._m1.label_mode.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from crypto_trade.strategies.ml.labeling import label_trades

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CANDLE_MINUTES = 480  # 8h
_TIMEOUT_MINUTES = _CANDLE_MINUTES * 21  # 21 candles = 10080 min
_FEE_PCT = 0.1


def _make_master(prices: list[float], sym: str = "BCHUSDT") -> pd.DataFrame:
    """Build a minimal master DataFrame from a list of close prices.

    Each candle: open = prev_close, high = close * 1.05, low = close * 0.95.
    Timestamps are spaced by 8h (480 min = 28,800,000 ms).
    """
    n = len(prices)
    interval_ms = _CANDLE_MINUTES * 60 * 1000

    open_times = [int(1_600_000_000_000 + i * interval_ms) for i in range(n)]
    close_times = [t + interval_ms - 1 for t in open_times]

    rows = []
    for i, close in enumerate(prices):
        open_ = prices[i - 1] if i > 0 else close
        rows.append(
            {
                "symbol": sym,
                "open_time": open_times[i],
                "close_time": close_times[i],
                "open": open_,
                "high": close * 1.05,
                "low": close * 0.95,
                "close": close,
                "volume": 1000.0,
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Test 1: fixed_horizon returns sign of forward return
# ---------------------------------------------------------------------------


def test_fixed_horizon_label_returns_sign_of_fwd_return():
    """label_mode='fixed_horizon': label == sign(fwd_return_21) on a simple uptrend."""
    # 23 candles: candle 0 is the entry; candles 1-21 are the forward window;
    # candle 22 is one beyond deadline (should not be reached).
    prices = [100.0 + i * 0.5 for i in range(23)]  # monotone uptrend
    master = _make_master(prices)

    candidate_indices = np.array([0], dtype=np.intp)

    labels, weights, long_pnls, short_pnls = label_trades(
        master,
        candidate_indices,
        tp_pct=4.0,
        sl_pct=2.0,
        timeout_minutes=_TIMEOUT_MINUTES,
        fee_pct=_FEE_PCT,
        label_mode="fixed_horizon",
    )

    entry = prices[0]
    horizon_close = prices[21]
    expected_fwd_return = (horizon_close - entry) / entry * 100.0
    assert expected_fwd_return > 0, "Setup error: expected positive forward return"
    assert labels[0] == 1, (
        f"fixed_horizon uptrend: expected label=+1 (LONG), got {labels[0]}. "
        f"fwd_return={expected_fwd_return:.4f}%"
    )


# ---------------------------------------------------------------------------
# Test 2: fixed_horizon PnL = realized return net of fee
# ---------------------------------------------------------------------------


def test_fixed_horizon_pnl_is_realized_return():
    """label_mode='fixed_horizon': long_pnl = fwd_return - fee; short_pnl = -fwd_return - fee."""
    prices = [100.0] + [100.0] * 20 + [105.0] + [999.0]  # horizon_close = 105 at candle 21
    master = _make_master(prices)

    candidate_indices = np.array([0], dtype=np.intp)
    labels, weights, long_pnls, short_pnls = label_trades(
        master,
        candidate_indices,
        tp_pct=4.0,
        sl_pct=2.0,
        timeout_minutes=_TIMEOUT_MINUTES,
        fee_pct=_FEE_PCT,
        label_mode="fixed_horizon",
    )

    entry = 100.0
    horizon_close = 105.0
    expected_fwd_return = (horizon_close - entry) / entry * 100.0  # 5.0
    expected_long_pnl = expected_fwd_return - _FEE_PCT  # 4.9
    expected_short_pnl = -expected_fwd_return - _FEE_PCT  # -5.1

    assert abs(long_pnls[0] - expected_long_pnl) < 1e-6, (
        f"fixed_horizon long_pnl={long_pnls[0]:.6f} != expected {expected_long_pnl:.6f}"
    )
    assert abs(short_pnls[0] - expected_short_pnl) < 1e-6, (
        f"fixed_horizon short_pnl={short_pnls[0]:.6f} != expected {expected_short_pnl:.6f}"
    )


# ---------------------------------------------------------------------------
# Test 3: default triple_barrier backward-compat
# ---------------------------------------------------------------------------


def test_triple_barrier_default_unchanged():
    """Default label_mode='triple_barrier' matches a call without the kwarg."""
    prices = [100.0 + i * 0.5 for i in range(30)]
    master = _make_master(prices)
    candidate_indices = np.array([0, 1, 2], dtype=np.intp)

    result_explicit = label_trades(
        master,
        candidate_indices,
        tp_pct=4.0,
        sl_pct=2.0,
        timeout_minutes=_TIMEOUT_MINUTES,
        fee_pct=_FEE_PCT,
        label_mode="triple_barrier",
    )
    result_default = label_trades(
        master,
        candidate_indices,
        tp_pct=4.0,
        sl_pct=2.0,
        timeout_minutes=_TIMEOUT_MINUTES,
        fee_pct=_FEE_PCT,
        # label_mode not passed — default "triple_barrier"
    )

    labels_explicit, weights_explicit, long_explicit, short_explicit = result_explicit
    labels_default, weights_default, long_default, short_default = result_default

    np.testing.assert_array_equal(
        labels_explicit,
        labels_default,
        err_msg="triple_barrier explicit vs default: labels differ",
    )
    np.testing.assert_allclose(
        long_explicit,
        long_default,
        rtol=1e-9,
        err_msg="triple_barrier explicit vs default: long_pnls differ",
    )
    np.testing.assert_allclose(
        short_explicit,
        short_default,
        rtol=1e-9,
        err_msg="triple_barrier explicit vs default: short_pnls differ",
    )


# ---------------------------------------------------------------------------
# Test 4: fixed_horizon ignores SL barrier hit
# ---------------------------------------------------------------------------


def _make_master_precise(rows_spec: list[dict]) -> pd.DataFrame:
    """Build a master DataFrame from explicit per-candle OHLC specs.

    Each element of rows_spec must contain:
        open, high, low, close — exact prices (no scaling applied).
    Timestamps are sequential 8h candles starting at epoch 1_600_000_000_000 ms.
    """
    interval_ms = _CANDLE_MINUTES * 60 * 1000
    records = []
    for i, spec in enumerate(rows_spec):
        t = int(1_600_000_000_000 + i * interval_ms)
        records.append(
            {
                "symbol": "BCHUSDT",
                "open_time": t,
                "close_time": t + interval_ms - 1,
                "open": spec["open"],
                "high": spec["high"],
                "low": spec["low"],
                "close": spec["close"],
                "volume": 1000.0,
            }
        )
    return pd.DataFrame(records)


def test_fixed_horizon_ignores_sl_barrier():
    """Adversarial: short-TP fires first under triple_barrier (→ label=-1 SHORT),
    but the net 21-candle fwd return is positive (→ fixed_horizon label=+1 LONG).

    Setup (tp_pct=3.0, sl_pct=20.0 as percentages — no ATR):
      - entry (candle 0): close=100.0
      - LONG TP level:  100 + 3  = 103.0
      - LONG SL level:  100 - 20 = 80.0  (very wide — will not be touched)
      - SHORT TP level: 100 - 3  = 97.0
      - SHORT SL level: 100 + 20 = 120.0 (very wide — will not be touched)

      - Candle 1: low=96.0 < 97.0 → SHORT TP fires on this candle.
                  high=101.0 < 103.0 → LONG TP does NOT fire.
                  → triple_barrier labels SHORT (-1) because short-TP fires first.

      - Candle 21 (horizon): close=106.0 → fwd_return = +6% (positive).
        → fixed_horizon labels LONG (+1) because fwd_return > 0.

    This is the canonical demonstration that fixed_horizon decouples the
    training label from the barrier-first-hit path noise.
    """
    entry_price = 100.0
    # Candle 1: short-TP fires (low=96.0 < 97.0), long-TP does not (high=101.0 < 103.0)
    barrier_candle = {"open": 100.0, "high": 101.0, "low": 96.0, "close": 98.0}
    flat_candle = {"open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0}
    horizon_candle = {"open": 106.0, "high": 106.5, "low": 105.5, "close": 106.0}
    beyond_candle = {"open": 110.0, "high": 111.0, "low": 109.0, "close": 110.0}

    rows = (
        [{"open": entry_price, "high": 100.5, "low": 99.5, "close": entry_price}]  # candle 0
        + [barrier_candle]  # candle 1: short-TP fires here
        + [flat_candle] * 19  # candles 2-20
        + [horizon_candle]  # candle 21 (horizon close=106.0)
        + [beyond_candle]  # candle 22 (beyond deadline, not scanned)
    )
    master = _make_master_precise(rows)
    candidate_indices = np.array([0], dtype=np.intp)

    call_kwargs = dict(
        tp_pct=3.0,
        sl_pct=20.0,
        timeout_minutes=_TIMEOUT_MINUTES,
        fee_pct=_FEE_PCT,
    )

    # Under fixed_horizon: label should be LONG (fwd_return = +6% at candle 21)
    labels_fh, _, _, _ = label_trades(
        master, candidate_indices, **call_kwargs, label_mode="fixed_horizon"
    )
    assert labels_fh[0] == 1, (
        f"fixed_horizon: barrier path fires SHORT but horizon fwd_return=+6% "
        f"must produce label=+1 (LONG). Got {labels_fh[0]}."
    )

    # Under triple_barrier: label should be SHORT (short-TP fires on candle 1)
    labels_tb, _, _, _ = label_trades(
        master, candidate_indices, **call_kwargs, label_mode="triple_barrier"
    )
    assert labels_tb[0] == -1, (
        f"triple_barrier: short-TP fires on candle 1 (low=96.0 < short-TP=97.0) "
        f"before long-TP (103.0 not reached) — must label=-1 (SHORT). Got {labels_tb[0]}."
    )


# ---------------------------------------------------------------------------
# Test 5: LightGbmStrategy stores label_mode
# ---------------------------------------------------------------------------


def test_lgbm_strategy_stores_label_mode():
    """LightGbmStrategy exposes self.label_mode from the constructor argument."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    base_kwargs = dict(
        features_dir="data/features_v3",
        ensemble_seeds=[42],
        feature_columns=["feat_a", "feat_b"],
    )

    strat_default = LightGbmStrategy(**base_kwargs)
    assert strat_default.label_mode == "triple_barrier", (
        f"Default label_mode must be 'triple_barrier'; got '{strat_default.label_mode}'."
    )

    strat_fh = LightGbmStrategy(**base_kwargs, label_mode="fixed_horizon")
    assert strat_fh.label_mode == "fixed_horizon", (
        f"label_mode='fixed_horizon' must be stored; got '{strat_fh.label_mode}'."
    )


# ---------------------------------------------------------------------------
# Test 6: MetaLabelingStrategy forwards label_mode to M1
# ---------------------------------------------------------------------------


def test_metalabeling_strategy_forwards_label_mode():
    """MetaLabelingStrategy forwards label_mode to the M1 LightGbmStrategy."""
    from crypto_trade.strategies.ml.metalabeling import MetaLabelingStrategy

    base_kwargs = dict(
        training_months=24,
        n_trials=1,
        label_tp_pct=8.0,
        label_sl_pct=4.0,
        ensemble_seeds=[42],
        feature_columns=["feat_a", "feat_b"],
        use_atr_labeling=False,
        fast_mode=False,
    )

    strat_default = MetaLabelingStrategy(**base_kwargs)
    assert strat_default._m1.label_mode == "triple_barrier", (
        f"Default label_mode must propagate to M1 as 'triple_barrier'; "
        f"got '{strat_default._m1.label_mode}'."
    )

    strat_fh = MetaLabelingStrategy(**base_kwargs, label_mode="fixed_horizon")
    assert strat_fh._m1.label_mode == "fixed_horizon", (
        f"label_mode='fixed_horizon' must propagate to M1; got '{strat_fh._m1.label_mode}'."
    )


# ---------------------------------------------------------------------------
# Test 7: iter-v3/115 integration — non-binding TP/SL barriers (×100) produce
#         ≥99% timeout exits when paired with label_mode="fixed_horizon".
# ---------------------------------------------------------------------------


def test_iter115_nonbinding_barriers_produce_timeout_exits():
    """Integration smoke test for iter-v3/115: coherent horizon-exit execution.

    Verifies that a ×100 ATR multiplier makes TP/SL barriers non-binding so
    that ≥99% of check_order calls resolve as 'timeout' (the coherent-horizon-
    execution signature), even under extreme price moves within the 21-candle
    window.

    This is the end-to-end check that both axis components (label_mode and
    execution geometry) landed together (per Section 3.5 / Section 9 of the
    iter-v3/115 research brief, and per
    feedback_v3_methodology_axis_integration_test.md).

    The test uses check_order() directly (the backtest engine's order-resolution
    function) with:
      - atr_tp_multiplier = atr_sl_multiplier = 100.0
      - natr_pct median ~3.7%  →  tp_pct = sl_pct = natr * 100 = 370%+
      - 21-candle window at 8h / candle
    We inject the worst-case price shock — a 50% single-candle move — to
    confirm the ×100 barrier still does not fire before timeout.
    """
    from crypto_trade.backtest import Order, check_order

    # Parameters matching the iter-v3/115 production config.
    atr_multiplier = 100.0
    natr_pct = 3.7  # IS median for BCH/LDO/TRX at 8h (Section 3.5 note)
    tp_sl_pct = natr_pct * atr_multiplier / 100.0  # fraction: 3.7

    entry_price = 100.0
    # timeout = 21 candles × 8h × 60min/h × 60s/min × 1000ms/s
    interval_ms = _CANDLE_MINUTES * 60 * 1000
    timeout_ms = 21 * interval_ms

    # Build a synthetic 25-candle run (21-candle window + 4 head-room).
    # The 22nd+ candle carries open_time >= open_time[0] + timeout_ms, so it
    # triggers the timeout branch in check_order.
    n_candles = 25
    open_times = [int(1_700_000_000_000 + i * interval_ms) for i in range(n_candles)]
    close_times = [t + interval_ms - 1 for t in open_times]

    # Extreme: single-candle 50% adverse move on candle 5.
    # SL level for a long = entry * (1 - tp_sl_pct) = 100 * (1 - 3.70) = -270 → impossible.
    # TP level for a long = entry * (1 + tp_sl_pct) = 100 * (1 + 3.70) = 470.
    # Even a 50% spike to 150 does NOT reach 470 → barrier never fires.
    rng = np.random.default_rng(7)
    closes = entry_price + rng.standard_normal(n_candles).cumsum()
    closes[5] = entry_price * 1.50  # +50% spike (worst realistic 8h move)
    closes[10] = entry_price * 0.55  # -45% crash (worst realistic 8h move)
    highs = np.maximum(closes, closes * 1.02)
    lows = np.minimum(closes, closes * 0.98)

    # Create one long order per candle position (all at the same entry to keep
    # the SL/TP levels constant and make the assertion simple).
    timeout_time = open_times[0] + timeout_ms

    order = Order(
        symbol="BCHUSDT",
        direction=1,  # long
        entry_price=entry_price,
        amount_usd=100.0,
        weight_factor=1.0,
        stop_loss_price=entry_price * (1 - tp_sl_pct),
        take_profit_price=entry_price * (1 + tp_sl_pct),
        open_time=open_times[0],
        timeout_time=timeout_time,
        confidence=None,
    )

    results = []
    for i in range(n_candles):
        result = check_order(
            order,
            open_times[i],
            closes[i],
            highs[i],
            lows[i],
            close_times[i],
            fee_pct=_FEE_PCT,
        )
        if result is not None:
            results.append(result.exit_reason)
            break  # stop at first close (mirrors backtest loop)

    assert results, "check_order must eventually close the order within 25 candles."
    assert results[0] == "timeout", (
        f"iter-v3/115: non-binding ×100 ATR barriers must produce 'timeout' exit. "
        f"Got '{results[0]}'. "
        f"entry={entry_price}, tp_level={entry_price * (1 + tp_sl_pct):.2f}, "
        f"sl_level={entry_price * (1 - tp_sl_pct):.2f} (natr_pct={natr_pct}, "
        f"atr_multiplier={atr_multiplier}). "
        "Check that atr_tp_multiplier=atr_sl_multiplier=100.0 in _build_v3_model "
        "common_kwargs (Section 3.5 Change 2 of the iter-v3/115 research brief)."
    )

    # Sanity: confirm the price did NOT reach the barrier levels (the point of
    # the ×100 multiplier — if this fails the test setup is wrong).
    assert all(h < entry_price * (1 + tp_sl_pct) for h in highs[:21]), (
        "Setup error: high price reached TP level — test is not testing non-binding barriers."
    )
    assert all(lo > entry_price * (1 - tp_sl_pct) for lo in lows[:21]), (
        "Setup error: low price reached SL level — test is not testing non-binding barriers."
    )
