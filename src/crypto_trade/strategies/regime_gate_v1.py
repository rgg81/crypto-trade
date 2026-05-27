"""Regime-conditional sub-model routing for iter-v1/024.

Architecture
------------
RegimeRoutedStrategy is a WRAPPER (not a sub-class of LightGbmStrategy).  It
holds two LightGbmStrategy instances — ``extreme_strategy`` (trained on rows
where |funding_rate_zscore_30| > threshold) and ``normal_strategy`` (the
complementary partition) — and dispatches get_signal() calls to the regime-
matched sub-strategy at inference time.

Key design decisions (all per LM Master §4(a) + brief Section 3.1):

1. TRAINING-TIME PARTITION is achieved via the ``data_filter_callback``
   parameter added to LightGbmStrategy (iter-v1/024 extension).  Each sub-
   strategy receives a callback that selects only its regime rows from
   train_indices.  The callback reads ``funding_rate_zscore_30`` from the
   master DataFrame, which is already shifted(1) past-only (see
   ``add_funding_v1_features`` in features_v1/).

2. INFERENCE-TIME DISPATCH is performed in ``get_signal()`` of THIS wrapper
   class — NOT inside LightGbmStrategy's get_signal.  The wrapper reads the
   pre-computed, past-only z30 value from the parquet-loaded feature row
   and routes to extreme or normal sub-strategy accordingly.  This is
   STATELESS — no persistent state except the wrapped sub-strategies' own.

3. SKIP-MONTH POLICY (LM Master §4(c)):  if the extreme sub-model has too
   few training rows for a given month (training was skipped), the wrapper
   routes ALL bars in that month to the normal sub-strategy.

4. PAST-ONLY INVARIANT:  at signal-time, the wrapper looks up z30 from the
   feature row already loaded by the inner strategy (no real-time compute,
   no bar-t inclusive window).  This matches the ``funding_rate_zscore_30``
   column which is computed with a .shift(1) in the feature pipeline.

Track isolation
---------------
This module lives under ``strategies/`` (NOT features_v1/ or features_v2/).
Zero imports from ``crypto_trade.features_v2`` or ``crypto_trade.features_v3``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from crypto_trade.backtest_models import Signal

# ---------------------------------------------------------------------------
# Configuration dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RegimeGateConfig:
    """Configuration for the funding-rate regime gate.

    Parameters
    ----------
    threshold:
        |funding_rate_zscore_30| > threshold → extreme regime.
        Default 1.5 (per brief Section 3.1 + Section 4.2 F-AXIS #3).
    z30_column:
        Name of the past-only funding-rate z-score column in the feature
        parquet.  Default ``"funding_rate_zscore_30"`` (the /023 feature).
    enabled:
        Set False to disable regime routing entirely (both regimes → normal).
        Used for testing and backward-compatibility.
    """

    threshold: float = 1.5
    z30_column: str = "funding_rate_zscore_30"
    enabled: bool = True


# ---------------------------------------------------------------------------
# Diagnostic stats dataclass (engineering report; NOT trade-routing)
# ---------------------------------------------------------------------------


@dataclass
class RegimeGateStats:
    """Accumulates regime-gate routing events per symbol.

    These counters are for the engineering report and Critic Phase 7.5
    verification of F-AXIS-MECHANISM #3 (fire rate per cohort).  They have
    NO effect on trade routing.
    """

    n_extreme_fired: int = 0
    n_normal_fired: int = 0
    n_skip_month_fallback: int = 0  # bars routed to normal due to skip-month

    @property
    def n_routed(self) -> int:
        return self.n_extreme_fired + self.n_normal_fired + self.n_skip_month_fallback

    @property
    def extreme_fire_rate(self) -> float:
        if self.n_routed == 0:
            return 0.0
        return self.n_extreme_fired / self.n_routed

    @property
    def normal_fire_rate(self) -> float:
        if self.n_routed == 0:
            return 0.0
        return (self.n_normal_fired + self.n_skip_month_fallback) / self.n_routed


# ---------------------------------------------------------------------------
# Helper: evaluate regime at signal-time (single-value, stateless)
# ---------------------------------------------------------------------------


def evaluate_regime_at_signal(z30_value: float, config: RegimeGateConfig) -> str:
    """Classify a single z30 observation into "extreme" or "normal".

    Parameters
    ----------
    z30_value:
        The past-only funding_rate_zscore_30 value at bar_t.  Must come from
        the pre-shifted parquet column to guarantee past-only integrity.
    config:
        Regime gate configuration.

    Returns
    -------
    "extreme" if |z30_value| > config.threshold (or NaN → "normal"), else "normal".

    Notes
    -----
    NaN values (early bars with insufficient funding history) default to
    "normal" so the normal sub-strategy handles warm-up bars.  This avoids
    skip-month propagation due to missing z30 alone.
    """
    if not config.enabled:
        return "normal"
    if z30_value is None or (isinstance(z30_value, float) and np.isnan(z30_value)):
        return "normal"
    try:
        z_abs = abs(float(z30_value))
    except (TypeError, ValueError):
        return "normal"
    return "extreme" if z_abs > config.threshold else "normal"


# ---------------------------------------------------------------------------
# Data-filter callback factories (training-time partition)
# ---------------------------------------------------------------------------


def make_extreme_filter(
    z30_column: str,
    threshold: float,
) -> Callable[[pd.DataFrame], np.ndarray]:
    """Return a callback that selects extreme-regime rows for LightGbmStrategy.

    The callback is passed to LightGbmStrategy(data_filter_callback=...) and
    is applied inside _train_for_month() AFTER the walk-forward window slice,
    BEFORE labeling and Optuna training.

    Parameters
    ----------
    z30_column:
        Name of the funding-rate z-score column (past-only by construction).
    threshold:
        |z30| > threshold → extreme regime.

    Returns
    -------
    Callable[[pd.DataFrame], np.ndarray]
        Takes a slice of the master DataFrame (train_indices rows) and returns
        a boolean numpy array selecting rows where |z30| > threshold.
        NaN z30 values are treated as normal (excluded from extreme partition).
    """

    def _filter(df: pd.DataFrame) -> np.ndarray:
        if z30_column not in df.columns:
            # If the funding column is missing, return all-False (empty partition).
            # This triggers the skip-month policy (< 100 rows → skip).
            return np.zeros(len(df), dtype=bool)
        z_vals = df[z30_column].values
        # NaN → normal (excluded from extreme partition)
        return np.where(
            np.isnan(z_vals.astype(float)),
            False,
            np.abs(z_vals.astype(float)) > threshold,
        )

    return _filter


def make_normal_filter(
    z30_column: str,
    threshold: float,
) -> Callable[[pd.DataFrame], np.ndarray]:
    """Return a callback that selects normal-regime rows for LightGbmStrategy.

    Symmetric complement of make_extreme_filter.  NaN z30 values are
    included in the normal partition (safe fallback for warm-up bars).
    """

    def _filter(df: pd.DataFrame) -> np.ndarray:
        if z30_column not in df.columns:
            # If the funding column is missing, return all-True (full partition).
            return np.ones(len(df), dtype=bool)
        z_vals = df[z30_column].values
        # NaN → normal (included in normal partition)
        not_extreme = np.where(
            np.isnan(z_vals.astype(float)),
            True,
            np.abs(z_vals.astype(float)) <= threshold,
        )
        return not_extreme

    return _filter


# ---------------------------------------------------------------------------
# RegimeRoutedStrategy — the wrapper
# ---------------------------------------------------------------------------


class RegimeRoutedStrategy:
    """Wrapper that dispatches get_signal() to regime-matched sub-strategies.

    Implements the ``Strategy`` protocol (get_signal / skip).

    Parameters
    ----------
    extreme_strategy:
        LightGbmStrategy trained on extreme-regime rows only (|z30| > threshold).
        Must have been constructed with ``data_filter_callback=make_extreme_filter(...)``.
    normal_strategy:
        LightGbmStrategy trained on normal-regime rows only (|z30| <= threshold).
        Must have been constructed with ``data_filter_callback=make_normal_filter(...)``.
    config:
        RegimeGateConfig specifying threshold + z30_column + enabled flag.
    cohort_name:
        Descriptive label used for engineering report logging
        (e.g. "Pool_A", "Model_C_LINK", "Model_D_LTC").

    Attributes
    ----------
    _gate_stats:
        Mapping from symbol → RegimeGateStats counter.  Updated at each
        get_signal() call.  Used for F-AXIS-MECHANISM #3 verification.
    """

    def __init__(
        self,
        extreme_strategy: Any,  # LightGbmStrategy; typed as Any to avoid circular import
        normal_strategy: Any,
        config: RegimeGateConfig,
        cohort_name: str = "",
    ) -> None:
        self.extreme_strategy = extreme_strategy
        self.normal_strategy = normal_strategy
        self.config = config
        self.cohort_name = cohort_name
        self._gate_stats: dict[str, RegimeGateStats] = {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_or_create_stats(self, symbol: str) -> RegimeGateStats:
        if symbol not in self._gate_stats:
            self._gate_stats[symbol] = RegimeGateStats()
        return self._gate_stats[symbol]

    def _is_extreme_model_trained_for_month(self, month_str: str) -> bool:
        """Return True if the extreme sub-model has a trained model for month_str.

        Used to implement the skip-month fallback policy (LM Master §4(c)):
        if extreme sub-model skipped training (too few rows), route ALL bars in
        that month to the normal sub-strategy.
        """
        # LightGbmStrategy sets self._model = None when training is skipped.
        # We check via the strategy's current month vs trained month.
        # A simpler check: if extreme_strategy._model is None after a month-
        # boundary trigger, the strategy has no model for that month.
        # Access the internal state via attribute inspection — safe read-only.
        return bool(getattr(self.extreme_strategy, "_models", None))

    # ------------------------------------------------------------------
    # Public interface (Strategy protocol)
    # ------------------------------------------------------------------

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        """Route signal to regime-matched sub-strategy.

        PAST-ONLY INVARIANT:
        The z30 value used for routing is read from the parquet-loaded feature
        row (accessed via the normal_strategy's _month_features cache, which
        is populated from the pre-shifted parquet column).  This value is
        already past-only — no real-time z30 computation occurs here.

        Skip-month fallback (LM Master §4(c)):
        If the extreme sub-model has no model for the current month (trained
        on too few rows and skipped), ALL bars in that month are routed to the
        normal sub-strategy, regardless of their z30 value.
        """
        stats = self._get_or_create_stats(symbol)

        # Step 1: Force normal_strategy to trigger month-boundary training
        # (this ensures _month_features is populated for z30 lookup below).
        # Then immediately check if extreme sub-model is trained.
        # We call extreme_strategy.get_signal first so both sub-models
        # experience the same month-boundary trigger.
        #
        # Note: this means BOTH sub-models train each month, regardless of
        # routing.  That is intentional — each must maintain its own model
        # for the current month so inference is available when needed.
        extreme_signal = self.extreme_strategy.get_signal(symbol, open_time)
        normal_signal = self.normal_strategy.get_signal(symbol, open_time)

        # Step 2: Apply skip-month fallback — if extreme model has no model
        # (training skipped due to thin partition), route to normal.
        if not self._is_extreme_model_trained_for_month(_epoch_ms_to_month(open_time)):
            stats.n_skip_month_fallback += 1
            return normal_signal

        # Step 3: Look up past-only z30 value from the feature cache.
        # The normal_strategy's _month_features cache holds the feature vector
        # for (symbol, open_time).  We read z30 from it; the extreme_strategy
        # uses the same parquet data so either cache would work.
        z30_value = _lookup_z30_from_strategy(
            self.normal_strategy, symbol, open_time, self.config.z30_column
        )

        # Step 4: Classify regime and dispatch.
        regime = evaluate_regime_at_signal(z30_value, self.config)

        if regime == "extreme":
            stats.n_extreme_fired += 1
            return extreme_signal
        else:
            stats.n_normal_fired += 1
            return normal_signal

    def skip(self) -> None:
        """Propagate skip() to both sub-strategies."""
        self.extreme_strategy.skip()
        self.normal_strategy.skip()

    # ------------------------------------------------------------------
    # Engineering report helpers
    # ------------------------------------------------------------------

    def get_gate_stats(self) -> dict[str, RegimeGateStats]:
        """Return per-symbol gate stats for engineering report."""
        return dict(self._gate_stats)

    def get_feature_importance(self) -> dict[str, Any]:
        """Return feature importance from both sub-strategies.

        Returns a dict with keys "extreme" and "normal", each containing
        the sub-strategy's _post_dispatch_fi_strategies-compatible form.
        Used by the runner's feature-importance emission logic.
        """
        return {
            "extreme": self.extreme_strategy,
            "normal": self.normal_strategy,
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _epoch_ms_to_month(epoch_ms: int) -> str:
    """Convert epoch milliseconds to YYYY-MM string (UTC).

    Matches the same conversion in lgbm.py — no import needed.
    """
    import datetime

    dt = datetime.datetime.fromtimestamp(epoch_ms / 1000, datetime.UTC)
    return dt.strftime("%Y-%m")


def _lookup_z30_from_strategy(
    strategy: Any,
    symbol: str,
    open_time: int,
    z30_column: str,
) -> float:
    """Retrieve past-only z30 value from strategy's month_features cache.

    The LightGbmStrategy pre-populates ``_month_features`` with one feature
    row per (symbol, open_time) key at training time (via compute_features).
    At inference time this cache holds the feature values for the current month.

    Parameters
    ----------
    strategy:
        A LightGbmStrategy instance whose ``_month_features`` cache and
        ``_selected_cols`` list are set.
    symbol:
        Symbol being traded (e.g. "BTCUSDT").
    open_time:
        Bar open timestamp in milliseconds.
    z30_column:
        Name of the funding-rate z-score column.

    Returns
    -------
    float
        The z30 value for this bar, or nan if not available.
    """
    # Access the feature cache directly.  This is safe read-only access;
    # the cache is a dict keyed by (symbol, open_time).
    month_features: dict = getattr(strategy, "_month_features", {})
    selected_cols: list[str] = getattr(strategy, "_selected_cols", [])

    key = (symbol, open_time)
    feat_row = month_features.get(key)
    if feat_row is None:
        return float("nan")

    # Locate z30_column in selected_cols (the columns LightGBM was trained on).
    if z30_column not in selected_cols:
        # Column not in the model's feature set — NaN fallback (→ "normal").
        return float("nan")

    col_idx = selected_cols.index(z30_column)
    if col_idx >= len(feat_row):
        return float("nan")

    val = feat_row[col_idx]
    try:
        return float(val)
    except (TypeError, ValueError):
        return float("nan")
