"""v1 validation module — refactored 2026-05-23.

Provides CPCV (Combinatorial Purged Cross-Validation), DSR (Deflated Sharpe
Ratio), PBO (Probability of Backtest Overfitting), PSR (Probabilistic Sharpe
Ratio), and n_effective_trials computations for the refactored v1 track.

The mathematical implementations are identical to validation_v3.py — these
functions are universal across v1/v3 (and would work for v2 if v2 invoked
them). validation_v1 re-exports validation_v3's public API as a thin shim and
overrides only the v1-specific constants (notably REQUIRED_GAP, which is
``(timeout_candles + 1) × n_symbols`` and depends on the active universe).

Track isolation:
----------------
validation_v1 MUST NOT import from ``features_v2`` or ``features_v3``. It IS
allowed to import from ``validation_v3`` because the math is shared
infrastructure, not feature/track logic. The Critic's Check 13 anti-pattern
scan grep-checks for cross-track FEATURE imports, not cross-track validation
imports.

V1-specific constants:
----------------------
For the v1 BASELINE_V1.md universe (BTC, ETH, LINK, LTC, DOT — 5 symbols,
21-bar label timeout in candles), REQUIRED_GAP = (21+1) * 5 = 110.

For an iter-v1/NNN that changes the universe size, REQUIRED_GAP recomputes
per ``(timeout_candles + 1) × len(active_universe)``. The runner derives
this dynamically; the constant below is the BASELINE_V1.md default.
"""

from __future__ import annotations

from crypto_trade.strategies.ml.validation_v3 import (
    PBOResult,
    cpcv_paths_from_splits,
    n_effective_trials,
    pbo_from_cpcv,
    psr,
)
from crypto_trade.strategies.ml.validation_v3 import (
    combinatorial_purged_cv as _combinatorial_purged_cv_v3,
)
from crypto_trade.strategies.ml.validation_v3 import (
    cpcv_walk_forward_splits as _cpcv_walk_forward_splits_v3,
)
from crypto_trade.strategies.ml.validation_v3 import (
    deflated_sharpe_ratio_v3 as _deflated_sharpe_ratio_v3,
)

# ---------------------------------------------------------------------------
# v1 REQUIRED_GAP — derived dynamically from active universe size at runtime;
# the constant below is the BASELINE_V1.md default (5-symbol, 21-bar timeout).
# ---------------------------------------------------------------------------

#: Default v1 CPCV purge gap for BASELINE_V1.md universe.
#: Formula: (timeout_candles + 1) × n_symbols
#: For BASELINE_V1 (BTC, ETH, LINK, LTC, DOT, 21-bar timeout): (21+1) * 5 = 110.
REQUIRED_GAP: int = (21 + 1) * 5  # 110

# ---------------------------------------------------------------------------
# Re-exports (math is universal — no v1-specific overrides needed for these)
# ---------------------------------------------------------------------------

# v1 invokes the v3 math under the v1 REQUIRED_GAP at runtime.
combinatorial_purged_cv = _combinatorial_purged_cv_v3
cpcv_walk_forward_splits = _cpcv_walk_forward_splits_v3
deflated_sharpe_ratio_v1 = _deflated_sharpe_ratio_v3  # v1 alias for v3 implementation

# Note: when the runner invokes these with a v1-specific gap, the v3
# functions accept the gap as a parameter — there's no hardcoded v3
# universe size inside the math. The REQUIRED_GAP constant exported here
# is the BASELINE_V1.md default; the runner overrides for universe-changing
# iterations.

__all__ = [
    "REQUIRED_GAP",
    "PBOResult",
    "combinatorial_purged_cv",
    "cpcv_paths_from_splits",
    "cpcv_walk_forward_splits",
    "deflated_sharpe_ratio_v1",
    "n_effective_trials",
    "pbo_from_cpcv",
    "psr",
]
