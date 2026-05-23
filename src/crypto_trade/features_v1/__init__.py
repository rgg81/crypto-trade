"""v1 feature module — refactored 2026-05-23 to mirror v2/v3 track isolation pattern.

This module is intentionally thin. The legacy ``crypto_trade.features`` package
holds the actual v1 feature implementations from the 186 historical iterations
(calendar, cross_asset, entropy_cusum, interaction, mean_reversion, momentum,
statistical, trend, volatility, volume). ``features_v1`` re-exports the
canonical feature-column list and defines v1-track constants without duplicating
the feature math.

Track isolation:
----------------
v1 (refactored) MUST NOT import from ``crypto_trade.features_v2`` or
``crypto_trade.features_v3``. The enforcement greps run at Phase 6.0 pre-flight:

    grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v1/
    grep -r "from crypto_trade.features_v3" src/crypto_trade/features_v1/

Both must return empty. Violating this rule is a hard BLOCK.

Note: ``features_v1`` IS allowed to import from the legacy ``crypto_trade.features``
parent package since the latter holds the actual v1 feature math. The legacy
package is preserved (not removed) for backward compatibility with the 186
historical iterations.
"""

from __future__ import annotations

from crypto_trade.live.models import BASELINE_FEATURE_COLUMNS, OOD_FEATURE_COLUMNS

# ---------------------------------------------------------------------------
# v1 symbol universe
# ---------------------------------------------------------------------------

# Symbols NOT allowed in v1 (refactored). These are reserved by v2 (live),
# v3 (live), or kept reserved for historical reasons (BNB).
V1_EXCLUDED_SYMBOLS: tuple[str, ...] = (
    # v2 traded (live, separate track)
    "SOLUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "NEARUSDT",
    # v3 traded (live, separate track)
    "BCHUSDT",
    "LDOUSDT",
    "TRXUSDT",
    # historical reservation (never traded, kept reserved)
    "BNBUSDT",
)

# Initial baseline universe (corrected walk-forward stats anchored to these 5
# symbols). Future v1 iterations can EXPLORE adding/swapping symbols from the
# extended pool = all Binance perpetuals minus V1_EXCLUDED_SYMBOLS.
# CONFIRMATION-MERGE updates this constant if the bundle changes universe.
V1_BASELINE_UNIVERSE: tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "DOTUSDT",
)

# ---------------------------------------------------------------------------
# v1 feature column list
# ---------------------------------------------------------------------------

# The canonical v1 feature set is the 193-column BASELINE_FEATURE_COLUMNS list
# defined in ``crypto_trade.live.models``. Re-exported here as V1_FEATURE_COLUMNS
# to match the v2/v3 naming convention. The runner uses this list to pin the
# explicit feature_columns argument to LightGbmStrategy at training time
# (NEVER pass None — column ordering matters for LightGBM colsample_bytree).
V1_FEATURE_COLUMNS: tuple[str, ...] = tuple(BASELINE_FEATURE_COLUMNS)

# Out-of-distribution detection feature subset (16 scale-invariant features
# used by the R3 Mahalanobis gate). Re-exported for v1 runner.
V1_OOD_FEATURE_COLUMNS: tuple[str, ...] = tuple(OOD_FEATURE_COLUMNS)

# ---------------------------------------------------------------------------
# Runtime audit helper
# ---------------------------------------------------------------------------


def assert_v1_universe(symbols: list[str] | tuple[str, ...]) -> None:
    """Raise AssertionError if any symbol is in V1_EXCLUDED_SYMBOLS.

    The v1 runner calls this at startup to fail loudly if a v2/v3 symbol leaks
    into v1's universe. Mirrors the v2/v3 audit pattern.
    """
    overlap = set(symbols) & set(V1_EXCLUDED_SYMBOLS)
    if overlap:
        raise AssertionError(
            f"v1 cannot trade v2/v3 symbols: {sorted(overlap)}. "
            f"V1_EXCLUDED_SYMBOLS = {V1_EXCLUDED_SYMBOLS}."
        )


__all__ = [
    "V1_EXCLUDED_SYMBOLS",
    "V1_BASELINE_UNIVERSE",
    "V1_FEATURE_COLUMNS",
    "V1_OOD_FEATURE_COLUMNS",
    "assert_v1_universe",
]
