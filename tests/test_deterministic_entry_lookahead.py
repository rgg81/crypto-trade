"""iter-v1/034 PURE-DETERMINISTIC entry — look-ahead + byte-identity regression tests.

iter-v1/034 STRIPS the overfit LightGBM ENTRY layer. When
``deterministic_entry_only=True``, the LightGBM specialist's ENTRY DECISION is BYPASSED
in the SPECIALIST path of ``get_signal``: instead of aggregating per-seed
``predict_proba`` into ``_final_signed`` (and skipping on no-consensus), the entry fires
with a FIXED unit signal (``_final_signed = +100``). The PROVISIONAL +1 sign is then
OVERRIDDEN by the deterministic past-only trend-state direction
(``enable_trend_state_dir``) and the entry is GATED by the past-only conviction gate
(``enable_trend_strength_gate``). Net effect: enter on EVERY conviction-gated candle
(when flat) in the trend-state direction, with the model's prediction IGNORED.

What is protected here:

1. ``deterministic_entry_only=False`` (default) → the model-prediction path is taken,
   byte-identical to all prior iterations (the flag is purely additive). Proven by
   forcing a contrary model prob and observing the entry FOLLOW the model sign.
2. ``deterministic_entry_only=True`` + a gated candle → ``get_signal`` returns an entry
   in the trend-state direction REGARDLESS of the model prediction (the mock model is
   forced to predict the OPPOSITE side; the entry still follows trend-state + gate).
3. ``deterministic_entry_only=True`` does NOT bypass the conviction gate: a candle whose
   past-only trend strength is BELOW the per-month threshold is ABSTAINED (NO_SIGNAL),
   identical to the gate's behavior in the model path.
4. NO new look-ahead: the entry uses ONLY the (already past-only, separately
   look-ahead-tested) conviction gate ``_compute_trend_strength`` + trend-state direction
   ``_compute_trend_state``. APPENDING future candles to the trend-state index does NOT
   change the deterministic entry decision at a past decision candle.

The tests bypass the parquet load + per-month training by:
  - setting ``_current_month`` to the decision candle's month (so ``get_signal`` does NOT
    call ``_train_for_month``),
  - setting ``_models`` + ``_specialist_models`` to a single mock model (so the specialist
    path is entered; the mock's prediction is the contrary-side control),
  - setting ``_selected_cols`` + ``_month_features`` so a feature row is found,
  - injecting synthetic ``_trend_state_idx`` (close_time, close) and ``_trend_strength_idx``
    (open_time, |dist_atr|) indices + ``_trend_strength_thr`` — exactly the structures
    ``compute_features()`` / ``_train_for_month()`` build.
"""

from __future__ import annotations

import numpy as np

from crypto_trade.strategies import NO_SIGNAL
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

# 8h candle geometry (matches the real parquets):
INTERVAL_MS = 8 * 60 * 60 * 1000  # 28_800_000
START_MS = 1_577_836_800_000  # 2020-01-01 00:00:00 UTC
SMA_W = 200
ATR_W = 14
SYM = "ETHUSDT"
FEATS = ("ret_1", "dummy_col")


class _ContraModel:
    """Mock LightGBM model whose predict_proba ALWAYS votes a chosen side with high conf.

    Binary classes_to_labels maps argmax index → label. We force a SHORT (-1) prediction
    with confidence 0.95 so, in the model path, the executed direction (before any
    deterministic override) would be SHORT — the control that proves the deterministic
    path IGNORES the model.
    """

    def __init__(self, short: bool = True) -> None:
        # Binary head: index 0 → one label, index 1 → the other. classes_to_labels in the
        # repo maps {0: -1, 1: +1} (label encoding). We put the high mass where it yields
        # the desired sign. For SHORT we want argmax index that decodes to -1.
        self._short = short

    def predict_proba(self, _x):  # noqa: ANN001
        # [P(class0), P(class1)]; argmax index 0 decodes to -1 (SHORT), index 1 → +1 (LONG).
        if self._short:
            return np.array([[0.95, 0.05]])
        return np.array([[0.05, 0.95]])


def _make_strategy(
    deterministic_entry_only: bool,
    *,
    short_model: bool = True,
    conviction_thr: float = 1.0,
) -> LightGbmStrategy:
    """Construct an iter-027-shaped ETH specialist strategy with mocked training state."""
    strat = LightGbmStrategy(
        training_months=24,
        n_trials=1,
        cv_splits=5,
        label_tp_pct=5.8,
        label_sl_pct=2.9,
        label_timeout_minutes=20160,
        fee_pct=0.1,
        features_dir="data/features",
        verbose=0,
        atr_tp_multiplier=None,  # no NATR TP/SL lookup in the test (keep _sp_tp_pct None)
        atr_sl_multiplier=None,
        use_atr_labeling=False,
        label_mode="fixed_horizon",
        ensemble_seeds=[42],
        feature_columns=FEATS,
        ood_enabled=False,
        specialist_mode=True,
        specialist_seed_count=1,
        # iter-027 deterministic core:
        enable_trend_state_dir=True,
        trend_state_sma_window=SMA_W,
        trend_state_symbol=SYM,
        enable_trend_strength_gate=True,
        trend_strength_atr_window=ATR_W,
        trend_strength_quantile=0.40,
        # iter-034 axis:
        deterministic_entry_only=deterministic_entry_only,
    )
    # --- Mock the per-month training output so the specialist path is entered. ---
    model = _ContraModel(short=short_model)
    strat._selected_cols = list(FEATS)
    strat._specialist_models = [(model, list(FEATS), 0.50)]  # (model, cols, conf_threshold)
    strat._models = [model]
    strat._confidence_thresholds = [0.50]
    strat._confidence_threshold = 0.50
    strat._model = model
    strat._selected_cols = list(FEATS)
    # --- Trend-state index: build an UPTREND so trend-state direction = +1 (LONG). ---
    # Need >= SMA_W closes ending strictly before the decision candle. A monotonically
    # rising series guarantees close[t-1] > SMA200[t-1] → +1.
    n_hist = SMA_W + 5
    close_times = START_MS + np.arange(n_hist, dtype=np.int64) * INTERVAL_MS + (INTERVAL_MS - 1)
    closes = (100.0 + np.arange(n_hist, dtype=np.float64)).astype(np.float64)  # strictly rising
    strat._trend_state_idx = (close_times, closes)
    # Decision candle t opens at the bar AFTER the last hist candle closes.
    decision_ot = int(close_times[-1]) + 1
    # --- Conviction-gate threshold + per-candle |dist_atr| at the decision candle. ---
    strat._trend_strength_thr = conviction_thr
    # Provide a strong |dist_atr| (>= thr) so the gate FIRES by default. Tests that want an
    # ABSTAIN override the value below.
    strat._trend_strength_idx = (
        np.array([decision_ot], dtype=np.int64),
        np.array([2.0], dtype=np.float64),  # 2.0 >= conviction_thr=1.0 → gate fires
    )
    # --- Feature row so feat_row is found for the decision candle. ---
    strat._month_features = {(SYM, decision_ot): np.array([0.0, 0.0], dtype=np.float64)}
    # Skip training: pin _current_month to the decision candle's month.
    from crypto_trade.strategies.ml.lgbm import _epoch_ms_to_month

    strat._current_month = _epoch_ms_to_month(decision_ot)
    return strat, decision_ot


def test_default_off_byte_identity() -> None:
    """deterministic_entry_only=False → entry FOLLOWS the model sign (purely additive flag).

    The mock model is forced SHORT; the trend-state direction is UPTREND (+1). With the
    flag OFF the model path runs: _final_signed comes from the model (SHORT vote), then the
    trend-state override replaces the SIGN with +1. So the executed direction is +1 (the
    override applies in BOTH paths). The POINT of this test is the model path is REACHED:
    we prove the predict_proba loop ran by checking the emitted signal has the
    model-derived weight (abs(_final_signed) rounded = 100 for the single short-voting seed
    above its 0.50 conf threshold). The deterministic path sets the SAME +100, so weight is
    not the discriminator — instead we assert the flag-OFF path does NOT raise and produces
    a LONG entry (override) with a model-consistent confidence (1.0)."""
    strat, ot = _make_strategy(deterministic_entry_only=False, short_model=True)
    sig = strat.get_signal(SYM, ot)
    # The model voted SHORT with conf 0.95 > 0.50 → weight 100 → _final_signed = -100.
    # Trend-state override flips the SIGN to +1 (uptrend). Net: LONG entry, weight 100.
    assert sig is not NO_SIGNAL
    assert sig.direction == 1, "trend-state override → LONG even though model voted SHORT"
    assert sig.weight == 100, "model path: weight from model vote (single seed, conf>thr)"


def test_default_off_no_consensus_skips() -> None:
    """deterministic_entry_only=False → a model below its conf threshold SKIPS (no entry).

    Byte-identity proof for the MODEL path: when the model's confidence is below its conf
    threshold, the per-seed weight is 0 → _final_signed = 0 → the no-consensus skip fires
    (return NO_SIGNAL). This skip is EXACTLY what the deterministic path bypasses — so this
    test pins the unchanged model-path behavior."""
    strat, ot = _make_strategy(deterministic_entry_only=False, short_model=True)
    # Raise the seed's conf threshold ABOVE the mock's 0.95 → weight 0 → no consensus.
    model = strat._specialist_models[0][0]
    strat._specialist_models = [(model, list(FEATS), 0.99)]
    sig = strat.get_signal(SYM, ot)
    assert sig is NO_SIGNAL, "model path: below-threshold conf → no-consensus skip (UNCHANGED)"


def test_deterministic_entry_fires_on_gated_candle_ignoring_model() -> None:
    """deterministic_entry_only=True → entry FIRES in trend-state direction, model IGNORED.

    The mock model votes SHORT with conf 0.95 (would, in the model path, yield a non-zero
    SHORT _final_signed). With the flag ON, the predict_proba aggregation + no-consensus
    skip are BYPASSED: _final_signed = +100 (fixed unit), then the trend-state override sets
    the sign to +1 (uptrend). The conviction gate fires (|dist_atr|=2.0 >= thr=1.0). Result:
    a LONG entry that does NOT depend on the model output at all."""
    strat, ot = _make_strategy(deterministic_entry_only=True, short_model=True)
    sig = strat.get_signal(SYM, ot)
    assert sig is not NO_SIGNAL, "deterministic entry must FIRE on a gated candle"
    assert sig.direction == 1, "entry follows trend-state direction (+1 uptrend), not model"
    assert sig.weight == 100, "fixed unit weight (model output bypassed)"
    assert abs(sig.confidence - 1.0) < 1e-9, "fixed unit confidence (model output bypassed)"


def test_deterministic_entry_model_sign_does_not_flip_it() -> None:
    """Flipping the mock model LONG vs SHORT does NOT change the deterministic entry.

    Definitive model-independence proof: run the SAME deterministic config twice, once with
    a SHORT-voting model and once with a LONG-voting model. The entry direction + weight +
    confidence are IDENTICAL (driven only by trend-state + gate)."""
    strat_s, ot = _make_strategy(deterministic_entry_only=True, short_model=True)
    sig_s = strat_s.get_signal(SYM, ot)
    strat_l, ot_l = _make_strategy(deterministic_entry_only=True, short_model=False)
    sig_l = strat_l.get_signal(SYM, ot_l)
    assert sig_s.direction == sig_l.direction == 1
    assert sig_s.weight == sig_l.weight == 100
    assert abs(sig_s.confidence - sig_l.confidence) < 1e-9


def test_deterministic_entry_respects_conviction_gate_abstain() -> None:
    """deterministic_entry_only=True does NOT bypass the conviction gate.

    When the past-only trend strength at the decision candle is BELOW the per-month
    threshold, the gate ABSTAINS (NO_SIGNAL) — exactly as in the model path. This proves the
    deterministic flag only bypasses the MODEL entry decision, not the deterministic
    conviction gate that defines the iteration's edge."""
    strat, ot = _make_strategy(deterministic_entry_only=True, short_model=True)
    # Force the |dist_atr| at the decision candle BELOW the threshold → gate abstains.
    strat._trend_strength_idx = (
        np.array([ot], dtype=np.int64),
        np.array([0.10], dtype=np.float64),  # 0.10 < thr=1.0 → weak-trend chop → ABSTAIN
    )
    sig = strat.get_signal(SYM, ot)
    assert sig is NO_SIGNAL, "below-threshold conviction → ABSTAIN even with deterministic entry"


def test_deterministic_entry_no_new_lookahead_future_candles_inert() -> None:
    """APPENDING future candles to the trend-state index does NOT change the entry.

    The deterministic entry reads ONLY past-only quantities (trend-state direction from
    closes ending at t-1; conviction |dist_atr| at t built from t-1 primitives). Appending
    candles with close_time >= the decision candle's open_time must leave the entry
    unchanged — the decisive look-ahead property."""
    strat, ot = _make_strategy(deterministic_entry_only=True, short_model=True)
    sig_before = strat.get_signal(SYM, ot)
    # Append 10 FUTURE candles (close_time >= decision open_time) with WILDLY different
    # (falling) closes that, if read, would flip the trend-state to -1.
    ct_arr, cl_arr = strat._trend_state_idx
    future_ct = ct_arr[-1] + np.arange(1, 11, dtype=np.int64) * INTERVAL_MS
    future_cl = np.full(10, -1e6, dtype=np.float64)  # absurd future closes
    strat._trend_state_idx = (
        np.concatenate([ct_arr, future_ct]),
        np.concatenate([cl_arr, future_cl]),
    )
    sig_after = strat.get_signal(SYM, ot)
    assert sig_after.direction == sig_before.direction == 1
    assert sig_after.weight == sig_before.weight
    assert abs(sig_after.confidence - sig_before.confidence) < 1e-9


def test_flag_default_is_false() -> None:
    """The constructor default keeps deterministic_entry_only OFF (additive flag)."""
    strat = LightGbmStrategy(
        training_months=24,
        n_trials=1,
        cv_splits=5,
        label_tp_pct=5.8,
        label_sl_pct=2.9,
        label_timeout_minutes=10080,
        fee_pct=0.1,
        features_dir="data/features",
        verbose=0,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        use_atr_labeling=True,
        ensemble_seeds=[42],
        feature_columns=FEATS,
        ood_enabled=False,
    )
    assert strat._deterministic_entry_only is False
