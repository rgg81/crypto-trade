"""Data models for the live trading module.

Baseline v152 configuration: 3-model portfolio (A: BTC+ETH, C: LINK, D: BNB)
with per-symbol volatility targeting and 5-seed LightGBM ensembles.
"""

from __future__ import annotations

import functools
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class ModelConfig:
    """Per-model configuration — mirrors run_baseline_v152.py:run_model args."""

    name: str  # "A", "C", "D"
    symbols: tuple[str, ...]  # ("BTCUSDT", "ETHUSDT") or ("LINKUSDT",)
    use_atr_labeling: bool
    atr_tp_multiplier: float  # 2.9 (A) or 3.5 (C/D)
    atr_sl_multiplier: float  # 1.45 (A) or 1.75 (C/D)


# Static feature list for baseline v152: 193 features.
# Excludes iter-162 entropy/CUSUM additions (evaluated in iter-163 as catastrophic).
# This list is the single source of truth — used by both live engine and baseline runner.
BASELINE_FEATURE_COLUMNS: tuple[str, ...] = (
    "cal_dow_norm",
    "cal_hour_norm",
    "interact_natr_x_adx",
    "interact_ret1_x_natr",
    "interact_ret1_x_ret3",
    "interact_rsi_x_adx",
    "interact_rsi_x_natr",
    "interact_stoch_x_adx",
    "mom_macd_hist_12_26_9",
    "mom_macd_hist_5_13_3",
    "mom_macd_hist_8_21_5",
    "mom_macd_line_12_26_9",
    "mom_macd_line_5_13_3",
    "mom_macd_line_8_21_5",
    "mom_macd_signal_12_26_9",
    "mom_macd_signal_5_13_3",
    "mom_macd_signal_8_21_5",
    "mom_mom_10",
    "mom_mom_15",
    "mom_mom_20",
    "mom_mom_5",
    "mom_roc_10",
    "mom_roc_15",
    "mom_roc_20",
    "mom_roc_3",
    "mom_roc_30",
    "mom_roc_5",
    "mom_rsi_14",
    "mom_rsi_21",
    "mom_rsi_30",
    "mom_rsi_5",
    "mom_rsi_7",
    "mom_rsi_9",
    "mom_stoch_d_14",
    "mom_stoch_d_21",
    "mom_stoch_d_5",
    "mom_stoch_d_9",
    "mom_stoch_k_14",
    "mom_stoch_k_21",
    "mom_stoch_k_5",
    "mom_stoch_k_9",
    "mom_willr_14",
    "mom_willr_21",
    "mom_willr_7",
    "mr_bb_pctb_10",
    "mr_bb_pctb_15",
    "mr_bb_pctb_20",
    "mr_bb_pctb_30",
    "mr_dist_sma_10",
    "mr_dist_sma_20",
    "mr_dist_sma_50",
    "mr_dist_vwap",
    "mr_pct_from_high_10",
    "mr_pct_from_high_100",
    "mr_pct_from_high_20",
    "mr_pct_from_high_5",
    "mr_pct_from_high_50",
    "mr_pct_from_low_10",
    "mr_pct_from_low_100",
    "mr_pct_from_low_20",
    "mr_pct_from_low_5",
    "mr_pct_from_low_50",
    "mr_rsi_extreme_14",
    "mr_rsi_extreme_21",
    "mr_rsi_extreme_7",
    "mr_zscore_10",
    "mr_zscore_100",
    "mr_zscore_20",
    "mr_zscore_30",
    "mr_zscore_50",
    "stat_autocorr_lag1",
    "stat_autocorr_lag10",
    "stat_autocorr_lag5",
    "stat_kurtosis_10",
    "stat_kurtosis_20",
    "stat_kurtosis_30",
    "stat_kurtosis_50",
    "stat_log_return_1",
    "stat_log_return_10",
    "stat_log_return_20",
    "stat_log_return_3",
    "stat_log_return_5",
    "stat_return_1",
    "stat_return_10",
    "stat_return_15",
    "stat_return_2",
    "stat_return_20",
    "stat_return_3",
    "stat_return_30",
    "stat_return_5",
    "stat_skew_10",
    "stat_skew_20",
    "stat_skew_30",
    "stat_skew_50",
    "trend_adx_14",
    "trend_adx_21",
    "trend_adx_7",
    "trend_aroon_down_14",
    "trend_aroon_down_25",
    "trend_aroon_down_50",
    "trend_aroon_osc_14",
    "trend_aroon_osc_25",
    "trend_aroon_osc_50",
    "trend_aroon_up_14",
    "trend_aroon_up_25",
    "trend_aroon_up_50",
    "trend_ema_100",
    "trend_ema_12",
    "trend_ema_21",
    "trend_ema_5",
    "trend_ema_50",
    "trend_ema_9",
    "trend_ema_cross_12_50",
    "trend_ema_cross_5_12",
    "trend_ema_cross_9_21",
    "trend_minus_di_14",
    "trend_minus_di_21",
    "trend_minus_di_7",
    "trend_plus_di_14",
    "trend_plus_di_21",
    "trend_plus_di_7",
    "trend_psar_af",
    "trend_psar_dir",
    "trend_sma_10",
    "trend_sma_100",
    "trend_sma_20",
    "trend_sma_50",
    "trend_sma_cross_10_50",
    "trend_sma_cross_20_100",
    "trend_sma_cross_20_50",
    "trend_supertrend_10_2",
    "trend_supertrend_14_3",
    "trend_supertrend_7_3",
    "vol_ad",
    "vol_atr_10",
    "vol_atr_14",
    "vol_atr_21",
    "vol_atr_5",
    "vol_atr_7",
    "vol_bb_bandwidth_10",
    "vol_bb_bandwidth_15",
    "vol_bb_bandwidth_20",
    "vol_bb_bandwidth_30",
    "vol_bb_pctb_10",
    "vol_bb_pctb_15",
    "vol_bb_pctb_20",
    "vol_bb_pctb_30",
    "vol_cmf_10",
    "vol_cmf_14",
    "vol_cmf_20",
    "vol_garman_klass_10",
    "vol_garman_klass_20",
    "vol_garman_klass_30",
    "vol_garman_klass_50",
    "vol_hist_10",
    "vol_hist_20",
    "vol_hist_30",
    "vol_hist_5",
    "vol_hist_50",
    "vol_mfi_10",
    "vol_mfi_14",
    "vol_mfi_21",
    "vol_mfi_7",
    "vol_natr_14",
    "vol_natr_21",
    "vol_natr_7",
    "vol_obv",
    "vol_parkinson_10",
    "vol_parkinson_20",
    "vol_parkinson_30",
    "vol_parkinson_50",
    "vol_range_spike_12",
    "vol_range_spike_24",
    "vol_range_spike_36",
    "vol_range_spike_48",
    "vol_range_spike_72",
    "vol_range_spike_96",
    "vol_taker_buy_ratio",
    "vol_taker_buy_ratio_sma_10",
    "vol_taker_buy_ratio_sma_20",
    "vol_taker_buy_ratio_sma_5",
    "vol_taker_buy_ratio_sma_50",
    "vol_volume_pctchg_10",
    "vol_volume_pctchg_15",
    "vol_volume_pctchg_20",
    "vol_volume_pctchg_3",
    "vol_volume_pctchg_30",
    "vol_volume_pctchg_5",
    "vol_volume_rel_10",
    "vol_volume_rel_20",
    "vol_volume_rel_5",
    "vol_volume_rel_50",
    "vol_vwap",
)

# Baseline v152 model definitions
BASELINE_MODELS = (
    ModelConfig(
        name="A",
        symbols=("BTCUSDT", "ETHUSDT"),
        use_atr_labeling=True,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
    ),
    ModelConfig(
        name="C",
        symbols=("LINKUSDT",),
        use_atr_labeling=True,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
    ),
    ModelConfig(
        name="D",
        symbols=("BNBUSDT",),
        use_atr_labeling=True,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
    ),
)


@dataclass(frozen=True)
class LiveConfig:
    """Configuration for the live trading engine.

    Defaults match baseline v152 (run_baseline_v152.py).
    """

    models: tuple[ModelConfig, ...] = BASELINE_MODELS
    interval: str = "8h"
    max_amount_usd: float = 1000.0
    stop_loss_pct: float = 4.0
    take_profit_pct: float = 8.0
    timeout_minutes: int = 10080  # 7 days
    fee_pct: float = 0.1
    cooldown_candles: int = 2
    leverage: int = 1
    # Vol targeting (iter 152)
    vol_targeting: bool = True
    vt_target_vol: float = 0.3
    vt_lookback_days: int = 45
    vt_min_scale: float = 0.33
    vt_max_scale: float = 2.0
    vt_min_history: int = 5
    # LightGBM shared
    training_months: int = 24
    n_trials: int = 50
    cv_splits: int = 5
    ensemble_seeds: tuple[int, ...] = (42, 123, 456, 789, 1001)
    # Paths
    data_dir: Path = Path("data")
    features_dir: Path = Path("data/features")
    feature_groups: tuple[str, ...] = ("all",)
    db_path: Path = Path("data/live.db")
    # Engine
    poll_interval_seconds: float = 30.0
    dry_run: bool = True

    @functools.cached_property
    def all_symbols(self) -> tuple[str, ...]:
        """Deduplicated list of all symbols across all models."""
        seen: dict[str, None] = {}
        for mc in self.models:
            for s in mc.symbols:
                seen[s] = None
        return tuple(seen)


def _new_id() -> str:
    return uuid.uuid4().hex[:16]


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class LiveTrade:
    """Mutable trade record — updated as trade progresses through lifecycle."""

    id: str = field(default_factory=_new_id)
    model_name: str = ""  # "A", "C", "D"
    symbol: str = ""
    direction: int = 0  # 1=long, -1=short
    entry_price: float = 0.0
    amount_usd: float = 0.0
    weight_factor: float = 1.0
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    open_time: int = 0  # epoch ms
    timeout_time: int = 0  # epoch ms
    signal_time: int = 0  # candle open_time that generated signal
    status: str = "open"  # "open" | "closed"
    entry_order_id: str | None = None
    sl_order_id: str | None = None
    tp_order_id: str | None = None
    exit_price: float | None = None
    exit_time: int | None = None
    exit_reason: str | None = None  # "stop_loss"|"take_profit"|"timeout"|"reconciled"
    created_at: str = field(default_factory=_now_iso)
