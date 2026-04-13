"""v2 risk-management layer — iter-v2/001 will implement.

``RiskV2Wrapper`` wraps a trained strategy (typically ``LightGbmStrategy``) and
gates each signal through regime, volatility, and out-of-distribution checks
*before* the order reaches the backtest engine. The wrapper is the primary
defence against the failure mode the user called out: a model running in a
market regime it was never trained on.

MVP gates (enabled in iter-v2/001):

1. Volatility-adjusted position sizing — scale weight inversely with ATR percentile
2. ADX gate — kill signals when ADX < threshold (ranging regime untrained)
3. Hurst regime check — kill when current Hurst outside training 5/95 percentile
4. Feature z-score OOD alert — kill when any feature |z| > 3 vs training stats

Deferred to iter-v2/002-003:
- Drawdown brake (portfolio-level DD > 5% → shrink; > 10% → flatten)
- BTC contagion circuit breaker (BTC 1h return < -5% → kill all alt positions)
- Isolation Forest anomaly scoring (unsupervised OOD)
- Liquidity floor (spread/volume thresholds)

See ``.claude/commands/quant-iteration-v2.md`` §13 for the full rationale and
the Section 6 (Risk Management Design) brief schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RiskV2Config:
    """Knobs for the v2 risk layer. All thresholds are tunable per iteration."""

    # Vol-adjusted sizing
    vol_scale_floor: float = 0.3
    vol_scale_ceiling: float = 1.0
    # ADX gate
    adx_threshold: float = 20.0
    # Hurst regime check
    hurst_lower_pct: float = 0.05
    hurst_upper_pct: float = 0.95
    # Feature z-score OOD alert
    zscore_threshold: float = 3.0
    # Which gates are active (iter-v2/002+ will flip these on one at a time)
    enable_vol_scaling: bool = True
    enable_adx_gate: bool = True
    enable_hurst_check: bool = True
    enable_zscore_ood: bool = True
    # Reserved for deferred primitives
    enable_drawdown_brake: bool = False
    enable_btc_contagion: bool = False
    enable_isolation_forest: bool = False
    enable_liquidity_floor: bool = False
    # Future: per-feature training stats — populated by compute_features()
    feature_stats: dict[str, dict[str, float]] = field(default_factory=dict)


class RiskV2Wrapper:
    """Wraps an inner strategy and enforces the v2 risk layer on each signal.

    iter-v2/001 implements the MVP gates. The scaffold here establishes the
    interface so the runner can import it cleanly.
    """

    def __init__(self, inner: Any, config: RiskV2Config) -> None:
        self.inner = inner
        self.config = config
        self.training_feature_stats: dict[str, dict[str, float]] | None = None

    def compute_features(self, master: Any) -> None:
        """Delegate feature computation; then snapshot training-window feature stats."""
        raise NotImplementedError(
            "iter-v2/001 implements the feature stat snapshot; scaffold stub"
        )

    def get_signal(self, symbol: str, open_time: int) -> Any:
        """Request signal from inner strategy, then apply risk gates."""
        raise NotImplementedError(
            "iter-v2/001 implements the risk gates; scaffold stub"
        )

    def skip(self, symbol: str, open_time: int) -> bool:
        """Pass-through to the inner strategy's skip predicate."""
        raise NotImplementedError(
            "iter-v2/001 wires skip() delegation; scaffold stub"
        )


__all__ = ["RiskV2Config", "RiskV2Wrapper"]
