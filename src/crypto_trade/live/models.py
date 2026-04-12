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
