"""Data models for the live trading module.

Baseline v186 configuration: 4-model portfolio (A: BTC+ETH, C: LINK, D: LTC,
E: DOT) with per-symbol volatility targeting, 5-seed LightGBM ensembles,
and risk mitigations R1 (consecutive-SL cool-down), R2 (drawdown scaling),
and R3 (OOD Mahalanobis gate).
"""

from __future__ import annotations

import functools
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from crypto_trade.strategies.ml.risk_v2 import RiskV2Config

# Iter 186: 16-feature scale-invariant subset used for R3 Mahalanobis OOD
# distance. Kept separate from BASELINE_FEATURE_COLUMNS (which is the
# 193-feature prediction set) because OOD requires a curated subset of
# scale-invariant features — including raw price/SMA-level features in the
# covariance would let cross-year price drift dominate the distance.
OOD_FEATURE_COLUMNS: tuple[str, ...] = (
    "stat_return_1",
    "stat_return_2",
    "stat_return_5",
    "stat_return_10",
    "mr_rsi_extreme_7",
    "mr_rsi_extreme_14",
    "mr_rsi_extreme_21",
    "mr_bb_pctb_10",
    "mr_bb_pctb_20",
    "mom_stoch_k_5",
    "mom_stoch_k_9",
    "vol_atr_5",
    "vol_atr_7",
    "vol_bb_bandwidth_10",
    "vol_volume_pctchg_5",
    "vol_volume_pctchg_10",
)


@dataclass(frozen=True)
class ModelConfig:
    """Per-model configuration — mirrors run_baseline_v186.py:run_model args."""

    name: str  # "A", "C", "D", "E"
    symbols: tuple[str, ...]  # ("BTCUSDT", "ETHUSDT") or single-symbol tuple
    use_atr_labeling: bool
    atr_tp_multiplier: float  # 2.9 (A) or 3.5 (C/D/E)
    atr_sl_multiplier: float  # 1.45 (A) or 1.75 (C/D/E)
    # Iter 173: R1 consecutive-SL cool-down. None ⇒ disabled (Model A).
    risk_consecutive_sl_limit: int | None = None
    risk_consecutive_sl_cooldown_candles: int = 0
    # Iter 176: R2 drawdown-triggered position scaling. False ⇒ disabled.
    risk_drawdown_scale_enabled: bool = False
    risk_drawdown_trigger_pct: float = 7.0
    risk_drawdown_scale_anchor_pct: float = 15.0
    risk_drawdown_scale_floor: float = 0.33
    # Iter 186: R3 OOD Mahalanobis gate (per-model, uniform in v0.186).
    ood_enabled: bool = True
    ood_features: tuple[str, ...] = OOD_FEATURE_COLUMNS
    ood_cutoff_pct: float = 0.70
    # Per-model overrides for v1+v2 coexistence.
    # None ⇒ fall back to LiveConfig (preserves v1 bit-identical behavior).
    feature_columns: tuple[str, ...] | None = None
    features_dir: Path | None = None
    atr_column: str | None = None
    cooldown_candles: int | None = None
    vol_targeting: bool | None = None
    ensemble_seeds: tuple[int, ...] | None = None
    risk_wrapper: Literal["none", "v2"] = "none"
    risk_v2_config: "RiskV2Config | None" = None


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

# Iter 189: BASELINE_FEATURE_COLUMNS + BTC cross-asset features (7 features).
# These expose BTC's regime/momentum/vol state to every symbol's model, including
# BTC itself (xbtc of BTC = BTC's own recent state, not leakage).
XBTC_FEATURE_COLUMNS: tuple[str, ...] = (
    "xbtc_return_1",
    "xbtc_return_3",
    "xbtc_return_8",
    "xbtc_natr_14",
    "xbtc_natr_21",
    "xbtc_rsi_14",
    "xbtc_adx_14",
)
BASELINE_PLUS_XBTC_FEATURE_COLUMNS: tuple[str, ...] = (
    *BASELINE_FEATURE_COLUMNS,
    *XBTC_FEATURE_COLUMNS,
)

# Baseline v186 model definitions: 4 models, R1 on C/D/E, R2 on E, R3 on all.
BASELINE_MODELS = (
    ModelConfig(
        name="A",
        symbols=("BTCUSDT", "ETHUSDT"),
        use_atr_labeling=True,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        # No R1/R2 on Model A — IS analysis showed mean-reverting WR at
        # streak length >= 3 (iter 173 finding).
    ),
    ModelConfig(
        name="C",
        symbols=("LINKUSDT",),
        use_atr_labeling=True,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
        risk_consecutive_sl_limit=3,
        risk_consecutive_sl_cooldown_candles=27,
    ),
    ModelConfig(
        name="D",
        symbols=("LTCUSDT",),  # iter 165: changed from BNBUSDT to LTCUSDT
        use_atr_labeling=True,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
        risk_consecutive_sl_limit=3,
        risk_consecutive_sl_cooldown_candles=27,
    ),
    ModelConfig(
        name="E",
        symbols=("DOTUSDT",),  # iter 176: new model
        use_atr_labeling=True,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
        risk_consecutive_sl_limit=3,
        risk_consecutive_sl_cooldown_candles=27,
        risk_drawdown_scale_enabled=True,
        risk_drawdown_trigger_pct=7.0,
        risk_drawdown_scale_anchor_pct=15.0,
        risk_drawdown_scale_floor=0.33,
    ),
)


# v2 baseline (iter-v2/069): 4 individual models on the diversification universe.
# Each model wraps its inner LightGbmStrategy with RiskV2Wrapper. Mirrors
# V2_MODELS in run_baseline_v2.py.
V2_EXCLUDED_SYMBOLS: tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "BNBUSDT",
)


def _build_v2_baseline_models() -> tuple[ModelConfig, ...]:
    """Construct V2_BASELINE_MODELS lazily so the import-time module load
    doesn't pull in features_v2 / risk_v2 (heavy deps) for every consumer."""
    from crypto_trade.features_v2 import V2_FEATURE_COLUMNS
    from crypto_trade.strategies.ml.risk_v2 import RiskV2Config

    return tuple(
        ModelConfig(
            name=f"V2-{sym.replace('USDT', '')}",
            symbols=(sym,),
            use_atr_labeling=True,
            atr_tp_multiplier=2.9,
            atr_sl_multiplier=1.45,
            atr_column="natr_21_raw",
            feature_columns=V2_FEATURE_COLUMNS,
            features_dir=Path("data/features_v2"),
            cooldown_candles=4,
            vol_targeting=False,
            ood_enabled=False,  # v2 z-score OOD lives in RiskV2Wrapper, not LGBM
            risk_wrapper="v2",
            risk_v2_config=RiskV2Config(zscore_threshold=2.5),
        )
        for sym in ("DOGEUSDT", "SOLUSDT", "XRPUSDT", "NEARUSDT")
    )


V2_BASELINE_MODELS: tuple[ModelConfig, ...] = _build_v2_baseline_models()
COMBINED_MODELS: tuple[ModelConfig, ...] = BASELINE_MODELS + V2_BASELINE_MODELS


@dataclass(frozen=True)
class LiveConfig:
    """Configuration for the live trading engine.

    Defaults match baseline v186 (run_baseline_v186.py).

    R1 (consecutive-SL cooldown), R2 (drawdown scaling), R3 (OOD gate)
    are configured per-model on ModelConfig, not here.
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
    # Testnet mode: when True, signed calls go to auth_base_url passed at
    # LiveEngine construction (typically https://testnet.binancefuture.com)
    # while kline fetches stay on base_url. Distinct from dry_run — testnet
    # IS live trading, just on Binance's test exchange. CLI enforces
    # testnet ⇒ dry_run=False at the `--testnet` flag handler.
    testnet: bool = False
    # Catch-up window. 90 days covers VT's 45-day rolling window plus
    # buffer so position sizing converges to backtest values before any
    # trade ships. Pass None to keep the legacy previous-calendar-month
    # behavior (used by old scripts that relied on _previous_month_start_ms).
    catch_up_lookback_days: int | None = 90

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


# Paper-trade prefixes used by db_seeder, engine catch-up, and OrderManager
# in dry-run mode. A real Binance order ID is always a numeric string.
_PAPER_PREFIXES: tuple[str, ...] = ("SEEDED", "DRY-", "CATCHUP-")


def is_paper_trade(trade: LiveTrade) -> bool:
    """True if the trade was NOT opened against the Binance exchange.

    Paper trade entry_order_id shapes:
      - None              — pre-cutoff seeded closed trade (db_seeder)
      - "SEEDED"          — seeded open trade spanning the as-of cutoff
      - "DRY-<8hex>"      — opened by OrderManager.open_trade in dry-run
      - "CATCHUP-<8hex>"  — opened by engine._catch_up_model

    Numeric strings (Binance order IDs) and the empty string are treated as
    real. Empty string can only arise from a Binance API anomaly; treating
    it as real keeps the failure mode loud rather than silently classifying
    a possibly-real trade as paper.
    """
    oid = trade.entry_order_id
    if oid is None:
        return True
    return oid.startswith(_PAPER_PREFIXES)
