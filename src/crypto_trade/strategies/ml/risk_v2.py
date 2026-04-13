"""v2 risk-management layer — ``RiskV2Wrapper`` around any Strategy.

Gates each inner-strategy signal through a cascade of checks BEFORE the order
reaches the backtest engine. The cascade is designed to detect the failure
mode the user called out: the model running in a market regime it was not
trained on. When a gate fires, the signal is either killed (direction=0) or
scaled down via ``weight``.

MVP gates (iter-v2/001):

1. Feature z-score OOD alert — for each v2 feature, compare current value to
   the IS-window rolling mean/std. If any ``|z| > zscore_threshold``, kill.
2. Hurst regime check — if current ``hurst_100`` lies outside the training
   window's 5th/95th percentile band, kill.
3. ADX gate — compute ADX on the fly from OHLC during ``compute_features``;
   if below ``adx_threshold``, kill. Rationale: a momentum learner is
   miscalibrated in ranging regimes, so skip the signal entirely.
4. Volatility-adjusted position sizing — scale signal weight by
   ``1 - atr_pct_rank_200`` clipped to ``[vol_scale_floor, vol_scale_ceiling]``.
   When current ATR percentile is high, position size shrinks.

Deferred primitives (iter-v2/002+): drawdown brake, BTC contagion circuit
breaker, isolation-forest anomaly, liquidity floor.

The wrapper is stateful but deterministic: the training-window feature
statistics and ADX series are computed once in ``compute_features`` and never
updated during the backtest. This matches v1's snapshot discipline and keeps
the gates reproducible across seeds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np
import pandas as pd

from crypto_trade.backtest_models import Signal
from crypto_trade.config import OOS_CUTOFF_MS
from crypto_trade.features_v2 import V2_FEATURE_COLUMNS
from crypto_trade.strategies import NO_SIGNAL


class _InnerStrategy(Protocol):
    def compute_features(self, master: pd.DataFrame) -> None: ...
    def get_signal(self, symbol: str, open_time: int) -> Signal: ...
    def skip(self) -> None: ...


@dataclass(frozen=True)
class RiskV2Config:
    """Knobs for the v2 risk layer. All thresholds are tunable per iteration."""

    # Vol-adjusted sizing — scale weight by (1 - atr_pct_rank_200) clipped to [floor, ceiling]
    vol_scale_floor: float = 0.3
    vol_scale_ceiling: float = 1.0

    # ADX gate — kill if ADX < threshold
    adx_threshold: float = 20.0
    adx_period: int = 14

    # Hurst regime check — training window percentile band
    hurst_lower_pct: float = 0.05
    hurst_upper_pct: float = 0.95

    # Feature z-score OOD alert — kill if any feature |z| exceeds threshold
    zscore_threshold: float = 3.0

    # Gate enables (iter-v2/002+ will toggle deferred primitives on)
    enable_vol_scaling: bool = True
    enable_adx_gate: bool = True
    enable_hurst_check: bool = True
    enable_zscore_ood: bool = True

    # Deferred primitives — defaults to off, iter-v2/002+
    enable_drawdown_brake: bool = False
    enable_btc_contagion: bool = False
    enable_isolation_forest: bool = False
    enable_liquidity_floor: bool = False


@dataclass
class GateStats:
    """Per-symbol gate efficacy counters. Reported by the engineering report."""

    signals_seen: int = 0
    killed_by_zscore: int = 0
    killed_by_hurst: int = 0
    killed_by_adx: int = 0
    vol_scaled_signals: int = 0
    vol_scale_sum: float = 0.0

    def vol_scale_mean(self) -> float:
        return self.vol_scale_sum / self.vol_scaled_signals if self.vol_scaled_signals else 1.0


class RiskV2Wrapper:
    """Wrap an inner strategy and enforce the v2 risk-layer gates on each signal.

    The wrapper participates in the ``Strategy`` protocol (``compute_features``,
    ``get_signal``, ``skip``) and transparently delegates to the inner strategy.

    Parameters
    ----------
    inner
        Underlying strategy (typically ``LightGbmStrategy``).
    config
        Risk-layer configuration.
    """

    def __init__(self, inner: _InnerStrategy, config: RiskV2Config) -> None:
        self.inner = inner
        self.config = config
        # Per-symbol training stats and lookup tables, populated in compute_features
        self._feature_mean: dict[str, pd.Series] = {}
        self._feature_std: dict[str, pd.Series] = {}
        self._hurst_lower: dict[str, float] = {}
        self._hurst_upper: dict[str, float] = {}
        # Per-(symbol, open_time) feature + ADX lookups — numpy arrays + searchsorted index
        self._lookup: dict[str, dict[str, np.ndarray]] = {}
        self._gate_stats: dict[str, GateStats] = {}

    # ------------------------------------------------------------------
    # Strategy protocol
    # ------------------------------------------------------------------
    def compute_features(self, master: pd.DataFrame) -> None:
        """Delegate to the inner strategy, then snapshot per-symbol feature stats."""
        self.inner.compute_features(master)
        self._build_lookups(master)

    def skip(self) -> None:
        self.inner.skip()

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        sig = self.inner.get_signal(symbol, open_time)
        if sig.direction == 0:
            return sig

        stats = self._gate_stats.setdefault(symbol, GateStats())
        stats.signals_seen += 1

        row = self._row_for(symbol, open_time)
        if row is None:
            return sig  # no feature row — let the inner strategy's own gates handle it

        # 1. Feature z-score OOD
        if self.config.enable_zscore_ood and self._zscore_ood(symbol, row):
            stats.killed_by_zscore += 1
            return NO_SIGNAL

        # 2. Hurst regime check
        if self.config.enable_hurst_check and self._hurst_ood(symbol, row):
            stats.killed_by_hurst += 1
            return NO_SIGNAL

        # 3. ADX gate
        if self.config.enable_adx_gate and self._adx_gate_fails(symbol, open_time):
            stats.killed_by_adx += 1
            return NO_SIGNAL

        # 4. Vol-adjusted sizing
        scale = 1.0
        if self.config.enable_vol_scaling:
            scale = self._vol_scale(symbol, row)
            stats.vol_scaled_signals += 1
            stats.vol_scale_sum += scale

        new_weight = max(1, int(round(sig.weight * scale)))
        return Signal(
            direction=sig.direction,
            weight=new_weight,
            tp_pct=sig.tp_pct,
            sl_pct=sig.sl_pct,
        )

    # ------------------------------------------------------------------
    # Lookup construction
    # ------------------------------------------------------------------
    def _build_lookups(self, master: pd.DataFrame) -> None:
        """Load v2 features and compute ADX per symbol, indexed by (symbol, open_time)."""
        from pathlib import Path

        import pyarrow.parquet as pq

        features_dir = getattr(self.inner, "features_dir", "data/features_v2")
        interval = getattr(self.inner, "_interval", "8h")

        symbols = list(pd.unique(master["symbol"]))
        for sym in symbols:
            path = Path(features_dir) / f"{sym}_{interval}_features.parquet"
            if not path.exists():
                continue

            needed = ["open_time", "high", "low", "close", "hurst_100", *V2_FEATURE_COLUMNS]
            needed = list(dict.fromkeys(needed))  # dedup, preserve order
            table = pq.read_table(path, columns=needed).to_pandas()
            table = table.sort_values("open_time").reset_index(drop=True)

            # Training-window = IS (open_time < OOS_CUTOFF_MS)
            is_mask = table["open_time"] < OOS_CUTOFF_MS
            is_df = table.loc[is_mask, list(V2_FEATURE_COLUMNS)]

            # Snapshot feature mean/std over the IS window (drop NaN per column)
            self._feature_mean[sym] = is_df.mean(skipna=True)
            self._feature_std[sym] = is_df.std(skipna=True).replace(0, np.nan)

            # Hurst percentile band over IS window
            hurst_is = table.loc[is_mask, "hurst_100"].dropna().to_numpy()
            if len(hurst_is) > 10:
                self._hurst_lower[sym] = float(
                    np.quantile(hurst_is, self.config.hurst_lower_pct)
                )
                self._hurst_upper[sym] = float(
                    np.quantile(hurst_is, self.config.hurst_upper_pct)
                )
            else:
                # Not enough data — disable Hurst gate for this symbol
                self._hurst_lower[sym] = -np.inf
                self._hurst_upper[sym] = np.inf

            # Compute ADX for the full series (IS + OOS) — same indicator v1's trend uses
            adx_arr = _compute_adx(
                table["high"].to_numpy(),
                table["low"].to_numpy(),
                table["close"].to_numpy(),
                period=self.config.adx_period,
            )

            # Build lookup table: open_time sorted, columns aligned
            self._lookup[sym] = {
                "open_time": table["open_time"].to_numpy(dtype=np.int64),
                "adx": adx_arr,
                "atr_pct_rank_200": table["atr_pct_rank_200"].to_numpy(),
                "hurst_100": table["hurst_100"].to_numpy(),
                "features": table[list(V2_FEATURE_COLUMNS)].to_numpy(),
            }

    # ------------------------------------------------------------------
    # Gate helpers
    # ------------------------------------------------------------------
    def _row_for(self, symbol: str, open_time: int) -> dict | None:
        lk = self._lookup.get(symbol)
        if lk is None:
            return None
        times = lk["open_time"]
        idx = int(np.searchsorted(times, open_time))
        if idx >= len(times) or int(times[idx]) != open_time:
            return None
        return {
            "idx": idx,
            "adx": float(lk["adx"][idx]) if not np.isnan(lk["adx"][idx]) else np.nan,
            "atr_pct_rank_200": float(lk["atr_pct_rank_200"][idx]),
            "hurst_100": float(lk["hurst_100"][idx]),
            "features": lk["features"][idx],
        }

    def _zscore_ood(self, symbol: str, row: dict) -> bool:
        mean = self._feature_mean.get(symbol)
        std = self._feature_std.get(symbol)
        if mean is None or std is None:
            return False
        x = row["features"]
        mu = mean.to_numpy()
        sd = std.to_numpy()
        # Skip features where std is NaN (no variance in IS) — treat as in-distribution
        with np.errstate(invalid="ignore", divide="ignore"):
            z = np.abs((x - mu) / sd)
        z = np.where(np.isnan(sd) | np.isnan(x), 0.0, z)
        return bool(np.nanmax(z) > self.config.zscore_threshold)

    def _hurst_ood(self, symbol: str, row: dict) -> bool:
        h = row["hurst_100"]
        if not np.isfinite(h):
            return False
        lo = self._hurst_lower.get(symbol, -np.inf)
        hi = self._hurst_upper.get(symbol, np.inf)
        return h < lo or h > hi

    def _adx_gate_fails(self, symbol: str, open_time: int) -> bool:
        lk = self._lookup.get(symbol)
        if lk is None:
            return False
        times = lk["open_time"]
        idx = int(np.searchsorted(times, open_time))
        if idx >= len(times) or int(times[idx]) != open_time:
            return False
        adx = float(lk["adx"][idx])
        if not np.isfinite(adx):
            return False
        return adx < self.config.adx_threshold

    def _vol_scale(self, symbol: str, row: dict) -> float:
        atr_pct = row["atr_pct_rank_200"]
        if not np.isfinite(atr_pct):
            return 1.0
        # Inverse-linear sizing: high vol percentile → smaller scale
        raw = 1.0 - atr_pct
        return float(
            np.clip(raw, self.config.vol_scale_floor, self.config.vol_scale_ceiling)
        )

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def gate_stats_summary(self) -> dict[str, dict[str, float]]:
        """Return per-symbol gate efficacy counters for the engineering report."""
        out: dict[str, dict[str, float]] = {}
        for sym, s in self._gate_stats.items():
            out[sym] = {
                "signals_seen": s.signals_seen,
                "killed_by_zscore": s.killed_by_zscore,
                "killed_by_hurst": s.killed_by_hurst,
                "killed_by_adx": s.killed_by_adx,
                "kill_rate": (
                    (s.killed_by_zscore + s.killed_by_hurst + s.killed_by_adx)
                    / s.signals_seen
                    if s.signals_seen
                    else 0.0
                ),
                "vol_scaled_signals": s.vol_scaled_signals,
                "mean_vol_scale": s.vol_scale_mean(),
            }
        return out


# ---------------------------------------------------------------------------
# ADX computation — inline so v2 doesn't depend on pandas-ta or v1 trend.py
# ---------------------------------------------------------------------------


def _compute_adx(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    period: int = 14,
) -> np.ndarray:
    """Average Directional Index (Wilder smoothing).

    Returns NaN for the first ``2*period`` bars while the smoothing warms up.
    """
    n = len(high)
    if n < 2 * period + 1:
        return np.full(n, np.nan)

    up_move = np.diff(high, prepend=high[0])
    down_move = np.diff(-low, prepend=-low[0])
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    prev_close = np.concatenate([[close[0]], close[:-1]])
    tr = np.maximum.reduce([high - low, np.abs(high - prev_close), np.abs(low - prev_close)])

    # Wilder smoothing (EMA with alpha = 1/period)
    def _wilder(series: np.ndarray) -> np.ndarray:
        out = np.full_like(series, np.nan, dtype=np.float64)
        if n < period:
            return out
        out[period - 1] = np.sum(series[:period])
        for i in range(period, n):
            out[i] = out[i - 1] - (out[i - 1] / period) + series[i]
        return out

    atr_w = _wilder(tr)
    plus_dm_w = _wilder(plus_dm)
    minus_dm_w = _wilder(minus_dm)

    with np.errstate(invalid="ignore", divide="ignore"):
        plus_di = 100.0 * plus_dm_w / atr_w
        minus_di = 100.0 * minus_dm_w / atr_w
        dx = 100.0 * np.abs(plus_di - minus_di) / (plus_di + minus_di)

    adx = np.full(n, np.nan, dtype=np.float64)
    # Smooth DX with Wilder's method, first valid at index 2*period - 1
    first_valid = 2 * period - 1
    if first_valid < n:
        adx[first_valid] = np.nanmean(dx[period - 1 : first_valid + 1])
        for i in range(first_valid + 1, n):
            if not np.isnan(dx[i]) and not np.isnan(adx[i - 1]):
                adx[i] = ((adx[i - 1] * (period - 1)) + dx[i]) / period
    return adx


__all__ = ["RiskV2Config", "RiskV2Wrapper", "GateStats"]
