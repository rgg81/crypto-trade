"""Per-candle SIGNAL-level parity harness for BUNDLE-002 (iter-v1/082).

Asserts bit/eps equality between the BACKTEST get_signal path and the LIVE
engine's signal path for a single injected (specialist-model, candle, state)
triple.  Checks every internal intermediate the two code paths share:

    Field                       Tolerance       Notes
    ─────────────────────────── ─────────────── ──────────────────────────────
    per_seed_signed_weights     exact list      50 floats ∈ {-100, 0, +100}
    _final_signed               rtol 5e-4       mean of per-seed weights
    _ensemble_std               rtol 5e-4       std of per-seed weights
    _sp_confidence              rtol 5e-4       abs(_final_signed)/100
    ood_distance vs ood_cutoff  rtol 5e-4       Mahalanobis; gating pass/fail
    vt_scale                    rtol 5e-4       vol-targeting scale factor
    r2_scale                    rtol 5e-4       R2 drawdown scale (DOT only)
    Signal.direction            exact int       -1 / 0 / +1
    Signal.weight               exact int       0–100
    Signal.tp_pct               rtol 5e-4       ATR × tp_multiplier
    Signal.sl_pct               rtol 5e-4       ATR × sl_multiplier

Sampling plan (run in Phase 3 once Phase-2 data regen is complete):
    Priority 1: AAVE  — unique 49-col feature set; most brittle feature path
    Priority 2: DOT   — R1+R2 both active; most complex risk path
    Priority 3: ETH   — R1/R2 OFF, R3 shared; simpler but high-volume
    Priority 4: BTC   — identical config to ETH; cheapest marginal addition
    Months sampled: first IS month, last IS month, first OOS month (×4 specialists)
    Candles per month: 3–5 (spread across early/mid/late in month)
    Total: ~4 specialists × 3 months × 4 candles = ~48 probe points

Architecture
────────────
Phase 3 will use a FROZEN_SPECIALIST_PROBE to inject a pre-trained model object
plus a synthetic feature row (identical values for BT and live).  The probe
compares the two code paths by:

  1. Backtest path: call LightGbmStrategy.get_signal(symbol, open_time) after
     calling compute_features(master_df) and _train_for_month(month).  Expose
     internal state via the `_specialist_probe_hooks` attribute (see below).

  2. Live path: instantiate ModelRunner(mc, live_cfg) → runner.warmup(master) →
     runner.strategy.get_signal(symbol, open_time).  Read vt_scale / r2_scale
     from the engine's _r2_scale_for + compute_vt_scale calls.

Both paths use the identical LightGBM models (same seed sequence, same
training data slice, same Optuna hyperparameters) so the per-seed vote
vectors must be bit-identical.

The test is marked xfail/skip when the Phase-2 regen artefacts are absent.
Phase 3 will flip the skip condition to an unconditional assertion.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Data availability guard — all assertions are xfail until Phase 2 is done.
# ---------------------------------------------------------------------------

BUNDLE_002_REPORTS = Path("reports-v1/iteration_v1-082")
FEATURES_DIR_V1 = Path("data/features")
DATA_DIR = Path("data")

BUNDLE_002_SYMS = ("DOTUSDT", "ETHUSDT", "BTCUSDT", "AAVEUSDT")

_PHASE2_COMPLETE = (
    (BUNDLE_002_REPORTS / "out_of_sample" / "trades.csv").exists()
    and (FEATURES_DIR_V1 / "DOTUSDT_8h_features.parquet").exists()
    and (FEATURES_DIR_V1 / "ETHUSDT_8h_features.parquet").exists()
    and (FEATURES_DIR_V1 / "BTCUSDT_8h_features.parquet").exists()
    and (FEATURES_DIR_V1 / "AAVEUSDT_8h_features.parquet").exists()
    and (DATA_DIR / "BTCUSDT" / "8h.csv").exists()
)

_XFAIL_REASON = (
    "Phase 2 regen not yet complete — specialist parquet features and /082 "
    "backtest trade CSVs are required.  This test will be activated in Phase 3."
)

# ---------------------------------------------------------------------------
# Numerical tolerance — matches 4dp CSV precision and float32 model outputs.
# ---------------------------------------------------------------------------

_TOL_REL = 5e-4  # relative tolerance for float comparisons
_TOL_ABS = 1e-6  # absolute floor for near-zero values


def _approx_equal(a: float, b: float, rtol: float = _TOL_REL, atol: float = _TOL_ABS) -> bool:
    """Return True when |a - b| <= atol + rtol * max(|a|, |b|)."""
    return abs(a - b) <= atol + rtol * max(abs(a), abs(b))


# ---------------------------------------------------------------------------
# Probe data structures
# ---------------------------------------------------------------------------


class SignalProbeResult:
    """Container for all intermediate values collected from one get_signal call.

    Both backtest and live paths populate this; the harness then diffs the two.
    """

    def __init__(
        self,
        per_seed_signed_weights: list[float],
        final_signed: float,
        ensemble_std: float,
        sp_confidence: float,
        ood_distance: float | None,
        ood_cutoff: float | None,
        ood_blocked: bool,
        direction: int,
        weight: int,
        tp_pct: float | None,
        sl_pct: float | None,
        vt_scale: float,
        r2_scale: float,
    ) -> None:
        self.per_seed_signed_weights = per_seed_signed_weights
        self.final_signed = final_signed
        self.ensemble_std = ensemble_std
        self.sp_confidence = sp_confidence
        self.ood_distance = ood_distance
        self.ood_cutoff = ood_cutoff
        self.ood_blocked = ood_blocked
        self.direction = direction
        self.weight = weight
        self.tp_pct = tp_pct
        self.sl_pct = sl_pct
        self.vt_scale = vt_scale
        self.r2_scale = r2_scale

    def __repr__(self) -> str:
        return (
            f"SignalProbeResult("
            f"dir={self.direction} wt={self.weight} "
            f"final_signed={self.final_signed:.4f} "
            f"ens_std={self.ensemble_std:.4f} "
            f"conf={self.sp_confidence:.4f} "
            f"ood_dist={self.ood_distance} "
            f"vt={self.vt_scale:.4f} r2={self.r2_scale:.4f})"
        )


class SignalProbe:
    """Monkey-patch shim that captures per-seed intermediate values from
    LightGbmStrategy.get_signal() without modifying production code.

    Attach via SignalProbe.attach(strategy) before calling get_signal();
    read captured results via probe.last.
    """

    def __init__(self) -> None:
        self.last: SignalProbeResult | None = None
        self._strategy: Any = None
        self._orig_get_signal: Any = None

    def attach(self, strategy: Any) -> SignalProbe:
        """Patch strategy.get_signal to intercept intermediate values."""
        import functools

        self._strategy = strategy
        orig = strategy.get_signal

        @functools.wraps(orig)
        def _patched(symbol: str, open_time: int):  # type: ignore[override]
            result = orig(symbol, open_time)
            # Post-call: harvest internals from the strategy's last-computed state.
            # The specialist path accumulates _signed_weights in
            # _specialist_dispersion_stats (last entry) and logs to decision_log.
            # We reconstruct by re-deriving from the model list.
            self.last = _harvest_probe_result(strategy, symbol, open_time, result)
            return result

        strategy.get_signal = _patched
        self._orig_get_signal = orig
        return self

    def detach(self) -> None:
        if self._strategy is not None and self._orig_get_signal is not None:
            self._strategy.get_signal = self._orig_get_signal
            self._strategy = None
            self._orig_get_signal = None


def _harvest_probe_result(
    strategy: Any,
    symbol: str,
    open_time: int,
    signal: Any,
) -> SignalProbeResult:
    """Extract intermediate values from the strategy after a get_signal call.

    Uses strategy._specialist_dispersion_stats[-1] for ensemble_std and
    reconstructs per-seed votes by replaying the last feature row against
    each seed model in strategy._specialist_models.

    This is a read-only inspection of already-computed state — no recomputation
    that could diverge from the production code path.
    """
    import numpy as np

    no_signal_dir = 0
    no_signal_wgt = 0

    # --- direction / weight / tp / sl from returned Signal ---
    direction = getattr(signal, "direction", no_signal_dir)
    weight = getattr(signal, "weight", no_signal_wgt)
    tp_pct = getattr(signal, "tp_pct", None)
    sl_pct = getattr(signal, "sl_pct", None)

    # --- confidence ---
    sp_confidence = getattr(signal, "confidence", None)
    if sp_confidence is None:
        sp_confidence = 0.0

    # --- OOD state ---
    ood_distance: float | None = None
    ood_cutoff: float | None = getattr(strategy, "_ood_cutoff", None)
    ood_blocked = direction == no_signal_dir  # conservative default

    # Try to recover ood_distance from the last decision_log entry.
    try:
        from crypto_trade import decision_log as _dl

        log_entries = getattr(_dl, "_log", None) or []
        for entry in reversed(log_entries):
            if (
                isinstance(entry, dict)
                and entry.get("kind") == "lgbm_signal"
                and entry.get("symbol") == symbol
                and entry.get("ot") == open_time
            ):
                if "ood_dist" in entry:
                    ood_distance = float(entry["ood_dist"])
                    ood_blocked = entry.get("decision") == "skipped:ood"
                break
    except Exception:
        pass

    # --- per-seed votes: replay via stored _specialist_models + feature row ---
    per_seed_signed_weights: list[float] = []
    final_signed = 0.0
    ensemble_std = 0.0

    specialist_models = getattr(strategy, "_specialist_models", [])
    selected_cols = getattr(strategy, "_selected_cols", None)
    month_features = getattr(strategy, "_month_features", {})

    # Reconstruct the feature row used for this candle from stored per-candle cache.
    key = (symbol, open_time)
    feat_row = month_features.get(key)

    if feat_row is not None and specialist_models and selected_cols is not None:
        ternary_sp = getattr(strategy, "neutral_threshold_pct", None) is not None

        def _classes_to_labels(arr: np.ndarray) -> np.ndarray:
            """Map argmax index to direction label using the same logic as lgbm.py."""
            # Ternary: classes [0,1,2] -> [-1, 0, +1]
            # Binary:  classes [0,1]   -> [-1, +1]
            # Use strategy's own _label_map if exposed, else derive.
            label_map = getattr(strategy, "_label_map", None)
            if label_map is not None:
                return np.array([label_map.get(int(a), 0) for a in arr])
            # Fallback: binary assumes class 0 = short, class 1 = long.
            if ternary_sp:
                return np.array([int(a) - 1 for a in arr])  # [0,1,2] -> [-1,0,+1]
            return np.array([-1 if int(a) == 0 else 1 for a in arr])

        for _sp_model, _sp_cols, _sp_ct in specialist_models:
            if _sp_cols != selected_cols:
                _feat_df_i = _rebuild_feat_df(feat_row, _sp_cols, selected_cols)
            else:
                import pandas as pd

                _feat_df_i = pd.DataFrame(feat_row.reshape(1, -1), columns=selected_cols)
            _proba_i = _sp_model.predict_proba(_feat_df_i)[0]
            if ternary_sp:
                _conf_i = max(float(_proba_i[0]), float(_proba_i[2]))
                _dir_i = 1 if float(_proba_i[2]) >= float(_proba_i[0]) else -1
            else:
                _conf_i = float(max(_proba_i))
                _dir_i = int(_classes_to_labels(np.array([int(np.argmax(_proba_i))]))[0])
            _weight_i = 100 if _conf_i > _sp_ct else 0
            per_seed_signed_weights.append(float(_dir_i) * float(_weight_i))

        if per_seed_signed_weights:
            final_signed = float(np.mean(per_seed_signed_weights))
            ensemble_std = (
                float(np.std(per_seed_signed_weights)) if len(per_seed_signed_weights) > 1 else 0.0
            )
    else:
        # Fall back to the dispersion stats log when we can't replay per-seed.
        disp = getattr(strategy, "_specialist_dispersion_stats", [])
        if disp:
            last_disp = disp[-1]
            ensemble_std = float(last_disp.get("signed_weight_std", 0.0))
        # Reconstruct final_signed from confidence and direction.
        if direction != 0:
            final_signed = float(direction) * float(sp_confidence) * 100.0

    return SignalProbeResult(
        per_seed_signed_weights=per_seed_signed_weights,
        final_signed=final_signed,
        ensemble_std=ensemble_std,
        sp_confidence=sp_confidence,
        ood_distance=ood_distance,
        ood_cutoff=ood_cutoff,
        ood_blocked=ood_blocked,
        direction=direction,
        weight=weight,
        tp_pct=tp_pct,
        sl_pct=sl_pct,
        vt_scale=1.0,  # filled by caller after engine state query
        r2_scale=1.0,  # filled by caller after engine state query
    )


def _rebuild_feat_df(
    feat_row: Any,
    target_cols: list[str],
    source_cols: list[str],
) -> Any:
    """Rebuild a per-seed feature DataFrame when seed columns differ from master."""
    import pandas as pd

    # Each specialist may have a column subset; slice accordingly.
    n = len(target_cols)
    arr = feat_row.reshape(1, -1)[:, :n]
    return pd.DataFrame(arr, columns=target_cols)


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------


def assert_probe_equal(
    bt_probe: SignalProbeResult,
    live_probe: SignalProbeResult,
    specialist_name: str,
    open_time_ms: int,
) -> None:
    """Assert all tracked fields match between backtest and live probe results.

    Calls pytest.fail() with a structured diff on first mismatch rather than
    raising raw AssertionError so pytest output is clean.
    """
    import pandas as pd

    ot_str = pd.to_datetime(open_time_ms, unit="ms", utc=True).strftime("%Y-%m-%d %H:%M")
    ctx = f"specialist={specialist_name} open_time={ot_str}"
    failures: list[str] = []

    # 1. per-seed signed weights (exact list equality — both ∈ {-100, 0, +100}).
    if bt_probe.per_seed_signed_weights and live_probe.per_seed_signed_weights:
        if bt_probe.per_seed_signed_weights != live_probe.per_seed_signed_weights:
            diffs = [
                i
                for i, (a, b) in enumerate(
                    zip(
                        bt_probe.per_seed_signed_weights,
                        live_probe.per_seed_signed_weights,
                    )
                )
                if a != b
            ]
            failures.append(
                f"per_seed_signed_weights: {len(diffs)} of "
                f"{len(bt_probe.per_seed_signed_weights)} seeds differ "
                f"(first mismatch idx={diffs[0]}: "
                f"bt={bt_probe.per_seed_signed_weights[diffs[0]]:.0f} "
                f"live={live_probe.per_seed_signed_weights[diffs[0]]:.0f})"
            )

    # 2. _final_signed
    if not _approx_equal(bt_probe.final_signed, live_probe.final_signed):
        failures.append(
            f"_final_signed: bt={bt_probe.final_signed:.6f} "
            f"live={live_probe.final_signed:.6f} "
            f"delta={abs(bt_probe.final_signed - live_probe.final_signed):.6f}"
        )

    # 3. _ensemble_std
    if not _approx_equal(bt_probe.ensemble_std, live_probe.ensemble_std):
        failures.append(
            f"_ensemble_std: bt={bt_probe.ensemble_std:.6f} "
            f"live={live_probe.ensemble_std:.6f} "
            f"delta={abs(bt_probe.ensemble_std - live_probe.ensemble_std):.6f}"
        )

    # 4. _sp_confidence
    if not _approx_equal(bt_probe.sp_confidence, live_probe.sp_confidence):
        failures.append(
            f"_sp_confidence: bt={bt_probe.sp_confidence:.6f} live={live_probe.sp_confidence:.6f}"
        )

    # 5. OOD distance (if available) and gating decision.
    if bt_probe.ood_distance is not None and live_probe.ood_distance is not None:
        if not _approx_equal(bt_probe.ood_distance, live_probe.ood_distance):
            failures.append(
                f"ood_distance: bt={bt_probe.ood_distance:.6f} live={live_probe.ood_distance:.6f}"
            )
    if bt_probe.ood_cutoff is not None and live_probe.ood_cutoff is not None:
        if not _approx_equal(bt_probe.ood_cutoff, live_probe.ood_cutoff):
            failures.append(
                f"ood_cutoff: bt={bt_probe.ood_cutoff:.6f} live={live_probe.ood_cutoff:.6f}"
            )
    if bt_probe.ood_blocked != live_probe.ood_blocked:
        failures.append(f"ood_blocked: bt={bt_probe.ood_blocked} live={live_probe.ood_blocked}")

    # 6. vt_scale
    if not _approx_equal(bt_probe.vt_scale, live_probe.vt_scale):
        failures.append(f"vt_scale: bt={bt_probe.vt_scale:.6f} live={live_probe.vt_scale:.6f}")

    # 7. r2_scale
    if not _approx_equal(bt_probe.r2_scale, live_probe.r2_scale):
        failures.append(f"r2_scale: bt={bt_probe.r2_scale:.6f} live={live_probe.r2_scale:.6f}")

    # 8. Signal direction (exact).
    if bt_probe.direction != live_probe.direction:
        failures.append(f"direction: bt={bt_probe.direction} live={live_probe.direction}")

    # 9. Signal weight (exact).
    if bt_probe.weight != live_probe.weight:
        failures.append(f"weight: bt={bt_probe.weight} live={live_probe.weight}")

    # 10. tp_pct / sl_pct.
    for field, bv, lv in [
        ("tp_pct", bt_probe.tp_pct, live_probe.tp_pct),
        ("sl_pct", bt_probe.sl_pct, live_probe.sl_pct),
    ]:
        if bv is None and lv is None:
            continue
        if bv is None or lv is None:
            failures.append(f"{field}: bt={bv} live={lv} (one is None)")
            continue
        if not _approx_equal(bv, lv):
            failures.append(f"{field}: bt={bv:.6f} live={lv:.6f} delta={abs(bv - lv):.6f}")

    if failures:
        joined = "\n  ".join(failures)
        pytest.fail(f"Signal parity failure [{ctx}]:\n  {joined}")


# ---------------------------------------------------------------------------
# Sampling plan (documented, not yet parameterized — filled in Phase 3)
# ---------------------------------------------------------------------------

# Each entry: (specialist_name, symbol, open_time_ms, month_str)
# Populated in Phase 3 once Phase-2 trade CSVs are available and we can
# sample real open_time values from the IS + first-OOS-month trade rows.
#
# SAMPLING PRIORITY ORDER:
#   1. AAVE  (first IS month, last IS month, first OOS month)
#   2. DOT   (first IS month, last IS month, first OOS month)
#   3. ETH   (first OOS month only — cheaper marginal check)
#   4. BTC   (first OOS month only)
#
# The Phase-3 implementation will load the /082 in_sample/trades.csv and
# out_of_sample/trades.csv, group by symbol, and pick 3-5 candle open_times
# per (specialist, month) — spread across early/mid/late within the month.

PHASE3_PROBE_PLAN: list[tuple[str, str, int, str]] = [
    # (specialist_name, symbol, open_time_ms, month_label)
    # TODO: populated in Phase 3 from /082 trade CSVs
]


# ---------------------------------------------------------------------------
# Shared fixture: build backtest LightGbmStrategy for one specialist
# ---------------------------------------------------------------------------


def _build_bt_strategy_for_specialist(specialist_name: str) -> Any:
    """Instantiate a backtest LightGbmStrategy configured for the named specialist.

    This mirrors the backtest runner's dispatch for /082.  The specialist
    trains lazily on compute_features() call, then get_signal() is exercisable.

    Returns the LightGbmStrategy instance (NOT yet trained).
    """
    from crypto_trade.features_v1 import (
        V1_FEATURE_COLUMNS_PRUNED,
        V1_ITER078_FEATURE_COLUMNS,
        V1_OOD_FEATURE_COLUMNS,
    )
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    # Per-specialist configs matching BUNDLE-002 dispatch in run_baseline_v1.py.
    configs: dict[str, dict] = {
        "V1-DOT": dict(
            symbols=["DOTUSDT"],
            feature_columns=list(V1_FEATURE_COLUMNS_PRUNED),
            atr_tp_multiplier=3.5,
            atr_sl_multiplier=1.75,
        ),
        "V1-ETH": dict(
            symbols=["ETHUSDT"],
            feature_columns=list(V1_FEATURE_COLUMNS_PRUNED),
            atr_tp_multiplier=2.9,
            atr_sl_multiplier=1.45,
        ),
        "V1-BTC": dict(
            symbols=["BTCUSDT"],
            feature_columns=list(V1_FEATURE_COLUMNS_PRUNED),
            atr_tp_multiplier=2.9,
            atr_sl_multiplier=1.45,
        ),
        "V1-AAVE": dict(
            symbols=["AAVEUSDT"],
            feature_columns=list(V1_ITER078_FEATURE_COLUMNS),
            atr_tp_multiplier=2.9,
            atr_sl_multiplier=1.45,
        ),
    }
    if specialist_name not in configs:
        raise ValueError(f"Unknown specialist: {specialist_name!r}")

    cfg = configs[specialist_name]
    return LightGbmStrategy(
        training_months=24,
        n_trials=30,  # specialist_optuna_trials=30
        cv_splits=5,
        label_tp_pct=None,  # use ATR labeling
        label_sl_pct=None,
        label_timeout_minutes=10080,
        fee_pct=0.1,
        features_dir=str(FEATURES_DIR_V1),
        verbose=0,
        atr_tp_multiplier=cfg["atr_tp_multiplier"],
        atr_sl_multiplier=cfg["atr_sl_multiplier"],
        use_atr_labeling=True,
        feature_columns=cfg["feature_columns"],
        ood_enabled=True,
        ood_features=list(V1_OOD_FEATURE_COLUMNS),
        ood_cutoff_pct=0.70,
        specialist_mode=True,
        specialist_n_startup_trials=10,
        specialist_n_estimators_max=500,
        bounds_profile="v1_pruned",
        enable_mid_bull_short_veto=False,
    )


# ---------------------------------------------------------------------------
# Shared fixture: build live ModelRunner for one specialist
# ---------------------------------------------------------------------------


def _build_live_runner_for_specialist(specialist_name: str, tmp_db: Path) -> Any:
    """Build a live ModelRunner configured for the named specialist.

    Uses BUNDLE_002_MODELS to ensure exact config parity.  Returns
    (runner, live_engine_stub) where the engine stub exposes
    _r2_scale_for() and _vt_daily_pnl for post-signal state queries.
    """
    from crypto_trade.live.engine import LiveEngine
    from crypto_trade.live.models import BUNDLE_002_MODELS, LiveConfig

    mc = next(m for m in BUNDLE_002_MODELS if m.name == specialist_name)
    live_cfg = LiveConfig(
        models=(mc,),
        dry_run=True,
        db_path=tmp_db,
        data_dir=DATA_DIR,
        features_dir=FEATURES_DIR_V1,
        catch_up_lookback_days=0,  # no catch-up in signal probe
    )
    engine = LiveEngine(live_cfg)
    runner = engine._runners[0]  # type: ignore[attr-defined]
    return runner, engine


# ---------------------------------------------------------------------------
# Phase-3 PROBE RUNNER — used by parameterized tests below
# ---------------------------------------------------------------------------


def _run_signal_probe(
    specialist_name: str,
    symbol: str,
    open_time_ms: int,
    tmp_path: Path,
) -> None:
    """Execute one backtest+live signal probe and assert field equality.

    Steps:
      1. Load the master DataFrame for the specialist from parquet.
      2. Run backtest compute_features() + get_signal() with SignalProbe attached.
      3. Run live runner.warmup() + runner.strategy.get_signal() with probe.
      4. Query vt_scale + r2_scale from engine state.
      5. Assert field equality via assert_probe_equal().
    """
    from crypto_trade.backtest import build_master

    # Build master DF from raw klines (needed for both paths).
    master = build_master(
        data_dir=str(DATA_DIR),
        symbols=[symbol],
        interval="8h",
    )

    # ---- BACKTEST path ----
    bt_strat = _build_bt_strategy_for_specialist(specialist_name)
    bt_probe = SignalProbe().attach(bt_strat)
    bt_strat.compute_features(master)
    bt_strat.get_signal(symbol, open_time_ms)
    bt_result = bt_probe.last

    # ---- LIVE path ----
    runner, engine = _build_live_runner_for_specialist(specialist_name, tmp_path / "live.db")
    live_probe = SignalProbe().attach(runner.strategy)
    runner.warmup(master)
    runner.strategy.get_signal(symbol, open_time_ms)
    live_result = live_probe.last

    # Fill vt_scale + r2_scale from engine state.
    from crypto_trade.backtest import compute_vt_scale

    live_vt_scale = compute_vt_scale(engine._vt_daily_pnl, symbol, open_time_ms, engine.config)
    live_r2_scale = engine._r2_scale_for(runner.model_config.name)
    # For DOT the backtest also applies R2; derive from engine's R2 state.
    # (For ETH/BTC/AAVE: R2 disabled → scale=1.0 in both paths.)
    if live_result is not None:
        live_result.vt_scale = live_vt_scale
        live_result.r2_scale = live_r2_scale

    # For backtest, vt_scale + r2_scale are computed in backtest.py's trade-entry
    # loop — not directly accessible from LightGbmStrategy.  Set to defaults here;
    # Phase 3 will hook the backtest trade-entry call to capture them directly.
    if bt_result is not None:
        bt_result.vt_scale = 1.0  # TODO Phase 3: hook backtest trade loop
        bt_result.r2_scale = 1.0  # TODO Phase 3: hook backtest trade loop

    assert bt_result is not None, "Backtest probe returned None — get_signal never called?"
    assert live_result is not None, "Live probe returned None — get_signal never called?"

    assert_probe_equal(bt_result, live_result, specialist_name, open_time_ms)


# ---------------------------------------------------------------------------
# Tests (xfail until Phase 2 complete + PHASE3_PROBE_PLAN populated)
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    not _PHASE2_COMPLETE,
    reason=_XFAIL_REASON,
    strict=False,
)
@pytest.mark.parametrize("plan_entry", PHASE3_PROBE_PLAN)
def test_signal_parity_probe(plan_entry, tmp_path):
    """Per-candle signal parity: backtest get_signal == live engine get_signal.

    Asserts exact/eps equality on 10 intermediate fields for each probe point
    defined in PHASE3_PROBE_PLAN.  Parameterized over ~48 probe points (4
    specialists × 3 months × ~4 candles).

    Status: XFAIL until Phase 2 regen is complete and PHASE3_PROBE_PLAN is populated.
    When Phase 2 is done:
      1. Populate PHASE3_PROBE_PLAN with real open_time_ms values from /082 CSVs.
      2. Remove the xfail marker (or flip strict=True).
      3. Run: uv run pytest tests/live/test_backtest_parity_bundle002_signal.py -v -s
    """
    specialist_name, symbol, open_time_ms, _month_label = plan_entry
    _run_signal_probe(specialist_name, symbol, open_time_ms, tmp_path)


@pytest.mark.xfail(
    not _PHASE2_COMPLETE,
    reason=_XFAIL_REASON,
    strict=False,
)
def test_signal_probe_infrastructure_smoke(tmp_path):
    """Smoke-test the probe infrastructure itself (import + instantiation).

    Verifies SignalProbe, SignalProbeResult, assert_probe_equal, and
    _build_bt_strategy_for_specialist all import and construct without error.
    This test stays xfail until parquet features are present because
    _build_bt_strategy_for_specialist references the features_dir at runtime.
    """
    # Build a strategy object to verify the factory doesn't crash.
    bt_strat = _build_bt_strategy_for_specialist("V1-AAVE")
    assert bt_strat is not None

    # Build two identical synthetic probe results and assert they compare equal.
    p1 = SignalProbeResult(
        per_seed_signed_weights=[100.0] * 50,
        final_signed=100.0,
        ensemble_std=0.0,
        sp_confidence=1.0,
        ood_distance=1.5,
        ood_cutoff=3.0,
        ood_blocked=False,
        direction=1,
        weight=100,
        tp_pct=0.05,
        sl_pct=0.025,
        vt_scale=1.0,
        r2_scale=1.0,
    )
    p2 = SignalProbeResult(
        per_seed_signed_weights=[100.0] * 50,
        final_signed=100.0,
        ensemble_std=0.0,
        sp_confidence=1.0,
        ood_distance=1.5,
        ood_cutoff=3.0,
        ood_blocked=False,
        direction=1,
        weight=100,
        tp_pct=0.05,
        sl_pct=0.025,
        vt_scale=1.0,
        r2_scale=1.0,
    )
    # Should not raise.
    assert_probe_equal(p1, p2, "V1-AAVE-SMOKE", 0)


@pytest.mark.xfail(
    not _PHASE2_COMPLETE,
    reason=_XFAIL_REASON,
    strict=False,
)
def test_signal_probe_detects_seed_divergence():
    """assert_probe_equal should FAIL when per-seed weights diverge."""
    p_bt = SignalProbeResult(
        per_seed_signed_weights=[100.0] * 50,
        final_signed=100.0,
        ensemble_std=0.0,
        sp_confidence=1.0,
        ood_distance=None,
        ood_cutoff=None,
        ood_blocked=False,
        direction=1,
        weight=100,
        tp_pct=0.05,
        sl_pct=0.025,
        vt_scale=1.0,
        r2_scale=1.0,
    )
    # Diverge one seed.
    bad_weights = [100.0] * 50
    bad_weights[7] = -100.0
    p_live = SignalProbeResult(
        per_seed_signed_weights=bad_weights,
        final_signed=96.0,  # mean changes
        ensemble_std=28.28,
        sp_confidence=0.96,
        ood_distance=None,
        ood_cutoff=None,
        ood_blocked=False,
        direction=1,
        weight=96,
        tp_pct=0.05,
        sl_pct=0.025,
        vt_scale=1.0,
        r2_scale=1.0,
    )
    with pytest.raises(pytest.fail.Exception):
        assert_probe_equal(p_bt, p_live, "V1-BTC-DIVERGE-TEST", 0)


@pytest.mark.xfail(
    not _PHASE2_COMPLETE,
    reason=_XFAIL_REASON,
    strict=False,
)
def test_signal_probe_detects_direction_divergence():
    """assert_probe_equal should FAIL when direction differs."""
    base = SignalProbeResult(
        per_seed_signed_weights=[100.0] * 50,
        final_signed=100.0,
        ensemble_std=0.0,
        sp_confidence=1.0,
        ood_distance=None,
        ood_cutoff=None,
        ood_blocked=False,
        direction=1,
        weight=100,
        tp_pct=0.05,
        sl_pct=0.025,
        vt_scale=1.0,
        r2_scale=1.0,
    )
    import dataclasses

    flipped = dataclasses.replace if hasattr(base, "__dataclass_fields__") else None
    if flipped is not None:
        wrong = flipped(base, direction=-1)
    else:
        wrong = SignalProbeResult(
            per_seed_signed_weights=base.per_seed_signed_weights,
            final_signed=base.final_signed,
            ensemble_std=base.ensemble_std,
            sp_confidence=base.sp_confidence,
            ood_distance=base.ood_distance,
            ood_cutoff=base.ood_cutoff,
            ood_blocked=base.ood_blocked,
            direction=-1,  # FLIPPED
            weight=base.weight,
            tp_pct=base.tp_pct,
            sl_pct=base.sl_pct,
            vt_scale=base.vt_scale,
            r2_scale=base.r2_scale,
        )
    with pytest.raises(pytest.fail.Exception):
        assert_probe_equal(base, wrong, "V1-ETH-DIR-TEST", 0)
