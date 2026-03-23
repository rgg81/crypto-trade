from __future__ import annotations

from crypto_trade.backtest_models import Signal, Strategy

# ---------------------------------------------------------------------------
# Sentinel for "no signal"
# ---------------------------------------------------------------------------

NO_SIGNAL = Signal(direction=0, weight=0)

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

STRATEGY_REGISTRY: dict[str, type] = {}


def _register(name: str, cls: type) -> None:
    STRATEGY_REGISTRY[name] = cls


def get_strategy(name: str, params: dict[str, str] | None = None) -> Strategy:
    """Instantiate a strategy by CLI name, optionally passing keyword params."""
    if name not in STRATEGY_REGISTRY:
        raise KeyError(f"Unknown strategy: {name!r}. Available: {list_strategies()}")
    cls = STRATEGY_REGISTRY[name]
    if params:
        converted: dict[str, int | float | str] = {}
        for k, v in params.items():
            try:
                converted[k] = int(v)
            except ValueError:
                try:
                    converted[k] = float(v)
                except ValueError:
                    converted[k] = v
        return cls(**converted)  # type: ignore[return-value]
    return cls()  # type: ignore[return-value]


def list_strategies() -> list[str]:
    return sorted(STRATEGY_REGISTRY.keys())


# ---------------------------------------------------------------------------
# Auto-register all strategies on import
# ---------------------------------------------------------------------------

from crypto_trade.strategies.filters.adaptive_range_spike_filter import (  # noqa: E402
    AdaptiveRangeSpikeFilter,
)
from crypto_trade.strategies.filters.range_spike_filter import RangeSpikeFilter  # noqa: E402
from crypto_trade.strategies.filters.volume_filter import VolumeFilter  # noqa: E402
from crypto_trade.strategies.indicator.bb_squeeze import BbSqueezeStrategy  # noqa: E402
from crypto_trade.strategies.indicator.rsi_bb import RsiBbStrategy  # noqa: E402
from crypto_trade.strategies.ml.lgbm import (  # noqa: E402
    LightGbmStrategy,
)
from crypto_trade.strategies.price_action.consecutive_continuation import (  # noqa: E402
    ConsecutiveContinuationStrategy,
)
from crypto_trade.strategies.price_action.consecutive_reversal import (  # noqa: E402
    ConsecutiveReversalStrategy,
)
from crypto_trade.strategies.price_action.follow_leader import (  # noqa: E402
    FollowLeaderStrategy,
)
from crypto_trade.strategies.price_action.gap_fill import GapFillStrategy  # noqa: E402
from crypto_trade.strategies.price_action.inside_bar import InsideBarStrategy  # noqa: E402
from crypto_trade.strategies.price_action.mean_reversion import (  # noqa: E402
    MeanReversionStrategy,
)
from crypto_trade.strategies.price_action.momentum import MomentumStrategy  # noqa: E402
from crypto_trade.strategies.price_action.wick_rejection import (  # noqa: E402
    WickRejectionStrategy,
)

_register("momentum", MomentumStrategy)
_register("mean_reversion", MeanReversionStrategy)
_register("wick_rejection", WickRejectionStrategy)
_register("inside_bar", InsideBarStrategy)
_register("gap_fill", GapFillStrategy)
_register("consecutive_continuation", ConsecutiveContinuationStrategy)
_register("consecutive_reversal", ConsecutiveReversalStrategy)
_register("follow_leader", FollowLeaderStrategy)
_register("rsi_bb", RsiBbStrategy)
_register("bb_squeeze", BbSqueezeStrategy)
_register("adaptive_range_spike_filter", AdaptiveRangeSpikeFilter)
_register("range_spike_filter", RangeSpikeFilter)
_register("volume_filter", VolumeFilter)
_register("lgbm", LightGbmStrategy)

__all__ = [
    "NO_SIGNAL",
    "STRATEGY_REGISTRY",
    "AdaptiveRangeSpikeFilter",
    "BbSqueezeStrategy",
    "ConsecutiveContinuationStrategy",
    "ConsecutiveReversalStrategy",
    "FollowLeaderStrategy",
    "GapFillStrategy",
    "InsideBarStrategy",
    "MeanReversionStrategy",
    "MomentumStrategy",
    "RangeSpikeFilter",
    "LightGbmStrategy",
    "RsiBbStrategy",
    "VolumeFilter",
    "WickRejectionStrategy",
    "get_strategy",
    "list_strategies",
]
