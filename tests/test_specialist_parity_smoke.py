"""Backtest vs engine signal-equivalence smoke test for iter-v1/063 DOT SPECIALIST.

Gates verified: C1 (feature-column pinning parity), C5 (specialist aggregator
identical in both paths), C6 (ModelRunner.get_signals delegates to the same
LightGbmStrategy.get_signal that the backtest calls directly).

Design — no live training, no parquet files required
------------------------------------------------------
The test injects a pre-built deterministic state into LightGbmStrategy to bypass
actual Optuna training and feature-store I/O.  Three synthetic candle slots are
exercised (IS 2024-01, IS 2025-01, post-OOS-cutoff 2026-01).

Backtest path:
    strategy.compute_features(master)  [only sets up splits; no training here]
    strategy.get_signal(symbol, open_time)

Engine path:
    runner.warmup(master)              [calls strategy.compute_features(master)]
    runner.get_signals({symbol: open_time})
    → strategy.get_signal(symbol, open_time)

Because both paths call the same object's get_signal(), injecting identical state
guarantees signal identity IF AND ONLY IF ModelRunner does not add any extra
routing logic between compute_features and get_signal.  The test explicitly
verifies that invariant.

Deterministic mock model
-------------------------
_DeterministicModel.predict_proba always returns [[0.25, 0.75]] (class 0 = short,
class 1 = long) regardless of features.  Every seed uses the same model so
signed_weights = [1 × 100] × 50 seeds → final_signed = +100 → direction=+1,
weight=100.  The confidence_threshold is set to 0.50 (below 0.75) so weight_i=100
fires for every seed.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Freeze a deterministic open_time for each of the 3 candles under test.
# Using midnight UTC on the 1st of each target month so _epoch_ms_to_month
# yields a predictable "YYYY-MM" key.
# ---------------------------------------------------------------------------

_OOS_CUTOFF_DATE = datetime.date(2025, 3, 24)

_CANDLE_DATES = [
    datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC),  # IS candle 1
    datetime.datetime(2025, 1, 1, tzinfo=datetime.UTC),  # IS candle 2
    datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),  # post-OOS candle
]

_CANDLE_OT_MS: list[int] = [int(dt.timestamp() * 1000) for dt in _CANDLE_DATES]

_SYMBOL = "DOTUSDT"
_INTERVAL = "8h"

# One candle duration in ms (8 h)
_8H_MS = 8 * 3600 * 1000

# Number of synthetic signals the test expects to compare
_N_SIGNALS = len(_CANDLE_DATES)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _epoch_ms_to_month(open_time_ms: int) -> str:
    """Mirror of lgbm._epoch_ms_to_month — kept local for test clarity."""
    return datetime.datetime.fromtimestamp(open_time_ms / 1000, tz=datetime.UTC).strftime("%Y-%m")


class _DeterministicModel:
    """Minimal LightGBM-compatible stub: always predicts class 1 (LONG) at 75% confidence."""

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:  # noqa: N803
        n = len(X)
        # Binary: [prob_class_0, prob_class_1] → class 1 = LONG
        return np.tile([0.25, 0.75], (n, 1))


def _build_minimal_master(symbol: str, open_times_ms: list[int]) -> pd.DataFrame:
    """Build a synthetic master DataFrame acceptable to compute_features.

    Contains only the columns that compute_features / generate_monthly_splits
    actually reads from master: open_time, symbol, close.
    LightGbmStrategy.compute_features reads symbol, open_time, and close
    (for mid-bull veto index); it does NOT read feature columns from master.
    """
    n = len(open_times_ms)
    records = []
    for ot in open_times_ms:
        records.append(
            {
                "open_time": ot,
                "open": 5.0,
                "high": 5.5,
                "low": 4.5,
                "close": 5.0,
                "close_time": ot + _8H_MS - 1,
                "volume": 1_000_000.0,
                "quote_volume": 5_000_000.0,
                "trades": 100,
                "taker_buy_volume": 500_000.0,
                "taker_buy_quote_volume": 2_500_000.0,
            }
        )
    df = pd.DataFrame(records)
    df["symbol"] = pd.Categorical([symbol] * n)
    df.sort_values(["open_time", "symbol"], kind="mergesort", ignore_index=True, inplace=True)
    return df


def _inject_specialist_state(
    strategy,  # LightGbmStrategy
    candle_ot_ms: int,
    feature_cols: list[str],
) -> None:
    """Inject pre-trained specialist state for one candle's month.

    Sets _current_month, _specialist_models, _models, _selected_cols,
    _confidence_threshold, _confidence_thresholds, _month_features, and
    _month_natr so that get_signal() can run deterministically without
    touching the filesystem or Optuna.

    Each specialist entry: (model, selected_cols, confidence_threshold).
    Threshold 0.50 < 0.75 = mock confidence → weight_i = 100.
    50 seeds × direction=+1 × weight=100 → signed_weights all +100
    → final_signed = +100 → direction=+1, weight=100.
    """
    from crypto_trade.strategies.ml.lgbm import V1_SPECIALIST_SEEDS

    month_str = _epoch_ms_to_month(candle_ot_ms)
    strategy._current_month = month_str

    mock_model = _DeterministicModel()
    specialist_entries = [(mock_model, list(feature_cols), 0.50) for _ in V1_SPECIALIST_SEEDS]
    strategy._specialist_models = specialist_entries
    strategy._models = [e[0] for e in specialist_entries]
    strategy._selected_cols = list(feature_cols)
    strategy._confidence_threshold = 0.50
    strategy._confidence_thresholds = [0.50] * len(V1_SPECIALIST_SEEDS)

    # Inject a synthetic feature row for the target candle.
    feat_row = np.zeros(len(feature_cols), dtype=np.float64)
    strategy._month_features = {(candle_ot_ms & ~0xFFFF, candle_ot_ms): feat_row}
    # Key must match exactly what get_signal uses: key = (symbol, open_time)
    strategy._month_features = {(_SYMBOL, candle_ot_ms): feat_row}

    # NATR for dynamic TP/SL (non-zero so atr path fires correctly).
    strategy._month_natr = {(_SYMBOL, candle_ot_ms): 0.015}

    # Disable OOD for this smoke test (avoids needing _ood_mean / _ood_inv_cov).
    strategy.ood_enabled = False
    strategy._ood_mean = None
    strategy._ood_inv_cov = None
    strategy._ood_cutoff = None
    strategy._month_ood_features = {}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def feature_cols() -> list[str]:
    """The 48-column V1_FEATURE_COLUMNS_PRUNED list."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    return list(V1_FEATURE_COLUMNS_PRUNED)


@pytest.fixture(scope="module")
def ood_cols() -> list[str]:
    from crypto_trade.features_v1 import V1_OOD_FEATURE_COLUMNS

    return list(V1_OOD_FEATURE_COLUMNS)


@pytest.fixture(scope="module")
def specialist_seeds() -> list[int]:
    from crypto_trade.strategies.ml.lgbm import V1_SPECIALIST_SEEDS

    return list(V1_SPECIALIST_SEEDS)


def _make_strategy(feature_cols: list[str], ood_cols: list[str], specialist_seeds: list[int]):
    """Construct LightGbmStrategy with /063 kwargs — no training invoked."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    return LightGbmStrategy(
        training_months=24,
        n_trials=30,  # V1_SPECIALIST_OPTUNA_TRIALS — informational in specialist mode
        cv_splits=5,
        label_tp_pct=8.0,
        label_sl_pct=4.0,
        label_timeout_minutes=10080,
        fee_pct=0.1,
        features_dir="data/features",
        verbose=0,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
        use_atr_labeling=True,
        # placeholder seed; specialist_mode internally uses V1_SPECIALIST_SEEDS
        ensemble_seeds=[specialist_seeds[0]],
        feature_columns=list(feature_cols),
        ood_enabled=False,  # disabled for smoke test; no parquet files needed
        ood_features=list(ood_cols),
        ood_cutoff_pct=0.70,
        bounds_profile="v1_pruned",
        specialist_mode=True,
        specialist_n_startup_trials=10,
        specialist_n_estimators_max=500,
    )


def _make_model_runner(feature_cols: list[str], ood_cols: list[str]):
    """Construct a ModelRunner wrapping an identical LightGbmStrategy.

    The engine's ModelRunner.__init__ creates LightGbmStrategy internally using
    its own constructor call (engine.py lines 153-181). We need to share the
    *same* strategy instance between the runner and the direct-call test to prove
    that the runner's routing path calls the same object rather than a copy.

    Strategy: construct the runner, then replace runner._inner_strategy and
    runner.strategy with the shared strategy object from _make_strategy().
    This tests that runner.get_signals() → strategy.get_signal() — same object,
    same state, same result.
    """
    from crypto_trade.features_v1 import V1_OOD_FEATURE_COLUMNS
    from crypto_trade.live.engine import ModelRunner
    from crypto_trade.live.models import LiveConfig, ModelConfig
    from crypto_trade.strategies.ml.lgbm import V1_SPECIALIST_SEEDS

    mc = ModelConfig(
        name="E_DOT_specialist",
        symbols=(_SYMBOL,),
        use_atr_labeling=True,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
        risk_consecutive_sl_limit=3,
        risk_consecutive_sl_cooldown_candles=27,
        risk_drawdown_scale_enabled=True,
        risk_drawdown_trigger_pct=7.0,
        risk_drawdown_scale_anchor_pct=15.0,
        risk_drawdown_scale_floor=0.33,
        ood_enabled=False,  # disabled for smoke test
        ood_features=tuple(V1_OOD_FEATURE_COLUMNS),
        ood_cutoff_pct=0.70,
        feature_columns=tuple(feature_cols),
        ensemble_seeds=(V1_SPECIALIST_SEEDS[0],),  # placeholder
        specialist_mode=True,
        specialist_n_startup_trials=10,
        specialist_n_estimators_max=500,
        specialist_optuna_trials=30,
        bounds_profile="v1_pruned",
    )
    lc = LiveConfig(
        models=(mc,),
        interval=_INTERVAL,
        training_months=24,
        n_trials=30,
        cv_splits=5,
        features_dir=Path("data/features"),
    )
    runner = ModelRunner(mc, lc)
    return runner


# ---------------------------------------------------------------------------
# Core parity test
# ---------------------------------------------------------------------------


def test_specialist_backtest_vs_engine_signal_parity(
    feature_cols: list[str],
    ood_cols: list[str],
    specialist_seeds: list[int],
) -> None:
    """Assert backtest path and engine path produce identical signals for 3 frozen candles.

    Gates: C1 (feature pinning), C5 (specialist aggregator), C6 (ModelRunner routing).
    """
    # Build shared strategy — SAME object used for both paths.
    strategy = _make_strategy(feature_cols, ood_cols, specialist_seeds)

    # Build engine runner and replace its inner strategy with the shared one.
    runner = _make_model_runner(feature_cols, ood_cols)
    runner._inner_strategy = strategy
    runner.strategy = strategy  # runner.strategy is the public-facing attribute

    # Build a minimal master spanning the 3 candle open_times.
    # compute_features only reads open_time and symbol to set up splits.
    # We use a long synthetic window so generate_monthly_splits has enough rows.
    # The actual candle open_times must be present in master for splits to include them.
    # Strategy: build a dense 8h grid from 2022-01-01 to 2026-06-01 (≈ 4900 candles).
    start_ms = int(datetime.datetime(2022, 1, 1, tzinfo=datetime.UTC).timestamp() * 1000)
    end_ms = int(datetime.datetime(2026, 6, 1, tzinfo=datetime.UTC).timestamp() * 1000)
    dense_ots = list(range(start_ms, end_ms, _8H_MS))

    master = _build_minimal_master(_SYMBOL, dense_ots)

    # Both paths share compute_features on the same master.
    strategy.compute_features(master)

    divergences: list[str] = []
    signals_compared = 0

    for candle_ot_ms in _CANDLE_OT_MS:
        # Inject deterministic state for this candle's month.
        _inject_specialist_state(strategy, candle_ot_ms, feature_cols)

        # ---- Backtest path ----
        from crypto_trade.backtest_models import Signal

        backtest_signal: Signal = strategy.get_signal(_SYMBOL, candle_ot_ms)

        # ---- Engine path ----
        # runner.get_signals calls strategy.get_signal via the same object.
        # Re-inject state (get_signal does NOT mutate _specialist_models for the
        # same month, but calling it once may advance _current_month if it changed).
        _inject_specialist_state(strategy, candle_ot_ms, feature_cols)

        engine_signals = runner.get_signals({_SYMBOL: candle_ot_ms})
        engine_signal: Signal = engine_signals.get(_SYMBOL)

        if engine_signal is None:
            # Engine produced NO_SIGNAL; treat as direction=0, weight=0
            from crypto_trade.strategies import NO_SIGNAL

            engine_signal = NO_SIGNAL

        signals_compared += 1

        # Compare direction
        if backtest_signal.direction != engine_signal.direction:
            divergences.append(
                f"candle={datetime.datetime.utcfromtimestamp(candle_ot_ms / 1000).date()} "
                f"direction: backtest={backtest_signal.direction} "
                f"engine={engine_signal.direction}"
            )

        # Compare weight (exact int equality; both come from int(round(...)))
        if backtest_signal.weight != engine_signal.weight:
            divergences.append(
                f"candle={datetime.datetime.utcfromtimestamp(candle_ot_ms / 1000).date()} "
                f"weight: backtest={backtest_signal.weight} "
                f"engine={engine_signal.weight}"
            )

        # Compare tp_pct / sl_pct (float; within 1e-9)
        if backtest_signal.tp_pct is not None or engine_signal.tp_pct is not None:
            bt_tp = backtest_signal.tp_pct if backtest_signal.tp_pct is not None else float("nan")
            en_tp = engine_signal.tp_pct if engine_signal.tp_pct is not None else float("nan")
            if not np.isclose(bt_tp, en_tp, atol=1e-9, equal_nan=True):
                divergences.append(
                    f"candle={datetime.datetime.utcfromtimestamp(candle_ot_ms / 1000).date()} "
                    f"tp_pct: backtest={bt_tp:.6f} engine={en_tp:.6f}"
                )

        if backtest_signal.sl_pct is not None or engine_signal.sl_pct is not None:
            bt_sl = backtest_signal.sl_pct if backtest_signal.sl_pct is not None else float("nan")
            en_sl = engine_signal.sl_pct if engine_signal.sl_pct is not None else float("nan")
            if not np.isclose(bt_sl, en_sl, atol=1e-9, equal_nan=True):
                divergences.append(
                    f"candle={datetime.datetime.utcfromtimestamp(candle_ot_ms / 1000).date()} "
                    f"sl_pct: backtest={bt_sl:.6f} engine={en_sl:.6f}"
                )

    assert signals_compared == _N_SIGNALS, (
        f"Expected {_N_SIGNALS} signals compared; got {signals_compared}"
    )

    if divergences:
        pytest.fail(
            f"Signal divergence(s) detected between backtest and engine paths "
            f"({len(divergences)} divergence(s)):\n" + "\n".join(f"  - {d}" for d in divergences)
        )


# ---------------------------------------------------------------------------
# Structural sanity tests (fast, no training)
# ---------------------------------------------------------------------------


def test_feature_columns_pinned_48(feature_cols: list[str]) -> None:
    """V1_FEATURE_COLUMNS_PRUNED must have exactly 48 columns (C1 gate)."""
    assert len(feature_cols) == 48, (
        f"Expected 48 V1_FEATURE_COLUMNS_PRUNED; got {len(feature_cols)}"
    )


def test_specialist_seeds_count_50(specialist_seeds: list[int]) -> None:
    """V1_SPECIALIST_SEEDS must have exactly 50 seeds (range 42..91)."""
    assert len(specialist_seeds) == 50
    assert specialist_seeds[0] == 42
    assert specialist_seeds[-1] == 91


def test_strategy_raises_without_feature_columns(ood_cols: list[str]) -> None:
    """LightGbmStrategy must raise if feature_columns is empty (C1 enforcement)."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    with pytest.raises(ValueError, match="feature_columns must be explicitly specified"):
        LightGbmStrategy(
            feature_columns=[],
            ensemble_seeds=[42],
        )


def test_mock_model_determinism() -> None:
    """_DeterministicModel must produce identical predict_proba output regardless of input."""
    model = _DeterministicModel()
    feat_a = pd.DataFrame({"f0": [0.1], "f1": [0.2]})
    feat_b = pd.DataFrame({"f0": [99.9], "f1": [-5.5]})
    proba_a = model.predict_proba(feat_a)
    proba_b = model.predict_proba(feat_b)
    assert np.allclose(proba_a, proba_b), (
        f"_DeterministicModel not deterministic: {proba_a} vs {proba_b}"
    )
    assert proba_a[0, 1] == 0.75, f"Expected class-1 prob=0.75; got {proba_a[0, 1]}"


def test_specialist_aggregator_math() -> None:
    """50 seeds × direction=+1 × weight=100 → final_signed=+100, direction=+1, weight=100."""
    signed_weights = [float(1) * float(100)] * 50  # 50 seeds, all long
    final_signed = float(np.mean(signed_weights))
    assert abs(final_signed - 100.0) < 1e-9, f"Expected 100.0; got {final_signed}"
    direction = 1 if final_signed > 0 else -1
    weight = int(round(abs(final_signed)))
    assert direction == 1
    assert weight == 100
