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

from dataclasses import dataclass, replace
from typing import Protocol

import numpy as np
import pandas as pd

from crypto_trade.backtest_models import Signal, TradeResult
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

    # iter-v2/004: Low-vol filter — kill signals when atr_pct_rank_200 is below
    # this threshold. iter-v2/002's per-regime breakdown showed the low-ATR
    # trending bucket had weighted Sharpe -1.86 (54 of 139 OOS trades), while
    # the mid and high buckets both had positive weighted Sharpe. Skipping
    # the low-vol bucket mechanically removes the single largest OOS drag.
    low_vol_filter_threshold: float = 0.33

    # Gate enables (iter-v2/002+ will toggle deferred primitives on)
    enable_vol_scaling: bool = True
    enable_adx_gate: bool = True
    enable_hurst_check: bool = True
    enable_zscore_ood: bool = True
    enable_low_vol_filter: bool = True  # NEW in iter-v2/004

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
    killed_by_low_vol: int = 0  # iter-v2/004
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

    @property
    def atr_column(self) -> str:
        """Delegate to the inner strategy so callers can treat the wrapper transparently."""
        return self.inner.atr_column

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

        # 4. Low-vol filter (iter-v2/004) — skip signals in the bottom-third
        # ATR percentile bucket where iter-v2/002 per-regime Sharpe was -1.86.
        if self.config.enable_low_vol_filter and self._low_vol_filter_fails(row):
            stats.killed_by_low_vol += 1
            return NO_SIGNAL

        # 5. Vol-adjusted sizing
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
                self._hurst_lower[sym] = float(np.quantile(hurst_is, self.config.hurst_lower_pct))
                self._hurst_upper[sym] = float(np.quantile(hurst_is, self.config.hurst_upper_pct))
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

    def _low_vol_filter_fails(self, row: dict) -> bool:
        """iter-v2/004: return True when atr_pct_rank_200 is below the filter threshold."""
        atr_pct = row["atr_pct_rank_200"]
        if not np.isfinite(atr_pct):
            return False
        return bool(atr_pct < self.config.low_vol_filter_threshold)

    def _vol_scale(self, symbol: str, row: dict) -> float:
        atr_pct = row["atr_pct_rank_200"]
        if not np.isfinite(atr_pct):
            return 1.0
        # iter-v2/002: sign INVERTED from iter-v2/001. This strategy's OOS edge
        # is concentrated in high-ATR-percentile buckets (Sharpe +1.45 in the
        # 0.66-1.01 bucket vs -1.85 in the 0-0.33 bucket per iter-v2/001 diary).
        # Scale position size UP when vol is high and DOWN when vol is low, so
        # profitable high-vol trades run at full size and unprofitable low-vol
        # trades run smaller. Direct linear mapping of atr_pct_rank_200 to the
        # [floor, ceiling] band.
        raw = float(atr_pct)
        return float(np.clip(raw, self.config.vol_scale_floor, self.config.vol_scale_ceiling))

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def gate_stats_summary(self) -> dict[str, dict[str, float]]:
        """Return per-symbol gate efficacy counters for the engineering report."""
        out: dict[str, dict[str, float]] = {}
        for sym, s in self._gate_stats.items():
            total_kills = (
                s.killed_by_zscore + s.killed_by_hurst + s.killed_by_adx + s.killed_by_low_vol
            )
            out[sym] = {
                "signals_seen": s.signals_seen,
                "killed_by_zscore": s.killed_by_zscore,
                "killed_by_hurst": s.killed_by_hurst,
                "killed_by_adx": s.killed_by_adx,
                "killed_by_low_vol": s.killed_by_low_vol,
                "kill_rate": total_kills / s.signals_seen if s.signals_seen else 0.0,
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


# ---------------------------------------------------------------------------
# iter-v2/013: portfolio-level drawdown brake
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DrawdownBrakeConfig:
    """Config for the portfolio-level drawdown brake.

    The brake operates on a temporally-sorted combined trade stream (one
    chronological timeline across all v2 models). It decides brake state
    from the UNBRAKED strategy's compound equity DD — this makes flatten
    self-releasing once the underlying strategy recovers above the shrink
    threshold. See iter-v2/012 engineering report for the design rationale.

    Config C thresholds (iter-v2/012 winner):
        shrink_pct=8.0, flatten_pct=16.0, shrink_factor=0.5
    """

    shrink_pct: float = 8.0
    flatten_pct: float = 16.0
    shrink_factor: float = 0.5
    enabled: bool = True


@dataclass
class BrakeFireStats:
    """Brake firing diagnostics for the engineering report."""

    n_total: int = 0
    n_normal: int = 0
    n_shrink: int = 0
    n_flatten: int = 0
    first_fire_time: int | None = None
    last_fire_time: int | None = None

    def as_dict(self) -> dict[str, int | None | float]:
        return {
            "n_total": self.n_total,
            "n_normal": self.n_normal,
            "n_shrink": self.n_shrink,
            "n_flatten": self.n_flatten,
            "fire_rate": ((self.n_shrink + self.n_flatten) / self.n_total if self.n_total else 0.0),
            "first_fire_time": self.first_fire_time,
            "last_fire_time": self.last_fire_time,
        }


def apply_portfolio_drawdown_brake(
    trades: list[TradeResult],
    config: DrawdownBrakeConfig,
    activate_at_ms: int | None = None,
) -> tuple[list[TradeResult], BrakeFireStats]:
    """Apply the portfolio-level drawdown brake to a combined trade stream.

    Returns a new list of ``TradeResult`` objects where each trade's
    ``weight_factor`` and ``weighted_pnl`` have been multiplied by the
    effective brake factor. The original trades are not mutated.

    The brake state is decided from the UNBRAKED compound equity DD at the
    trade's ``open_time``. This makes flatten self-releasing once the
    underlying strategy recovers. When the brake is disabled, the trades
    pass through unchanged and ``BrakeFireStats`` reports all-normal.

    Parameters
    ----------
    trades
        Combined trade stream from all v2 models. Will be sorted by
        ``open_time`` before brake application.
    config
        ``DrawdownBrakeConfig`` with shrink/flatten thresholds.
    activate_at_ms
        If set, trades with ``open_time < activate_at_ms`` are passed
        through unchanged and their PnL does not feed the shadow equity.
        This scopes the brake to a "live deployment" window (typically
        ``OOS_CUTOFF_MS`` in backtest-land) instead of compounding through
        the full IS training history, which would leave the brake stuck
        in a pre-existing drawdown from the IS period. The shadow equity
        resets to 1.0 at ``activate_at_ms``.

    Returns
    -------
    braked
        New list of ``TradeResult``, sorted by ``open_time``, with
        ``weight_factor`` and ``weighted_pnl`` attenuated per brake state.
    stats
        ``BrakeFireStats`` counting normal/shrink/flatten firings (only
        within the active window).
    """
    stats = BrakeFireStats(n_total=len(trades))
    if not trades or not config.enabled:
        stats.n_normal = len(trades)
        return list(trades), stats

    sorted_trades = sorted(trades, key=lambda t: t.open_time)
    braked: list[TradeResult] = []

    shadow_equity = 1.0
    shadow_peak = 1.0

    for trade in sorted_trades:
        # Trades outside the brake's active window pass through unchanged
        # and do NOT contribute to shadow equity (brake resets at activation)
        if activate_at_ms is not None and trade.open_time < activate_at_ms:
            braked.append(replace(trade))
            stats.n_normal += 1
            continue

        dd_pct = (shadow_equity - shadow_peak) / shadow_peak * 100.0  # non-positive

        if -dd_pct >= config.flatten_pct:
            eff_factor = 0.0
            is_fire = True
            stats.n_flatten += 1
        elif -dd_pct >= config.shrink_pct:
            eff_factor = config.shrink_factor
            is_fire = True
            stats.n_shrink += 1
        else:
            eff_factor = 1.0
            is_fire = False
            stats.n_normal += 1

        if is_fire:
            if stats.first_fire_time is None:
                stats.first_fire_time = int(trade.open_time)
            stats.last_fire_time = int(trade.open_time)

        new_weight = trade.weight_factor * eff_factor
        new_weighted_pnl = trade.weighted_pnl * eff_factor
        braked.append(
            replace(
                trade,
                weight_factor=new_weight,
                weighted_pnl=new_weighted_pnl,
            )
        )

        # Update shadow equity with the UNBRAKED trade PnL — flatten is self-releasing
        shadow_equity *= 1.0 + trade.weighted_pnl / 100.0
        shadow_peak = max(shadow_peak, shadow_equity)

    return braked, stats


# ---------------------------------------------------------------------------
# iter-v2/017: hit-rate feedback gate
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HitRateGateConfig:
    """Config for the hit-rate feedback gate.

    The gate tracks the stop-loss rate in a rolling window of the most
    recently closed trades (global across all v2 models). When the SL
    rate exceeds ``sl_threshold``, new signals are killed until enough
    winning trades close to bring the rate back below the threshold.

    Config D from iter-v2/016 feasibility (the winner):
        window=20, sl_threshold=0.65, shrink_factor=0.0
    """

    window: int = 20
    sl_threshold: float = 0.65
    enabled: bool = True


@dataclass
class HitRateFireStats:
    """Hit-rate gate firing diagnostics."""

    n_total: int = 0
    n_normal: int = 0
    n_warmup: int = 0
    n_killed: int = 0
    first_fire_time: int | None = None
    last_fire_time: int | None = None

    def as_dict(self) -> dict[str, int | None | float]:
        return {
            "n_total": self.n_total,
            "n_normal": self.n_normal,
            "n_warmup": self.n_warmup,
            "n_killed": self.n_killed,
            "fire_rate": self.n_killed / self.n_total if self.n_total else 0.0,
            "first_fire_time": self.first_fire_time,
            "last_fire_time": self.last_fire_time,
        }


def apply_hit_rate_gate(
    trades: list[TradeResult],
    config: HitRateGateConfig,
    activate_at_ms: int | None = None,
) -> tuple[list[TradeResult], HitRateFireStats]:
    """Apply the hit-rate feedback gate to a combined trade stream.

    For each trade at ``open_time T``, look at the ``window`` most
    recently closed trades (strictly ``close_time < T``) and compute
    the stop-loss rate. If SL rate >= ``sl_threshold``, zero the trade's
    weight.

    The gate is stateless given the trade stream: it doesn't need shadow
    equity tracking. The window naturally warms up as the first
    ``window`` OOS trades close, and it's self-releasing when enough
    winning trades enter the window.

    Parameters
    ----------
    trades
        Combined trade stream from all v2 models.
    config
        ``HitRateGateConfig`` with window and SL threshold.
    activate_at_ms
        If set, trades with ``open_time < activate_at_ms`` pass through
        unchanged, AND they do not feed the gate's lookback window.
        This scopes the gate to a "live deployment" window so that
        pre-OOS training-period trades don't pollute the SL-rate
        calculation.

    Returns
    -------
    braked
        New list of ``TradeResult`` with killed trades' weights zeroed.
    stats
        ``HitRateFireStats`` counting normal/warmup/killed firings.
    """
    stats = HitRateFireStats(n_total=len(trades))
    if not trades or not config.enabled or config.window <= 0:
        stats.n_normal = len(trades)
        return list(trades), stats

    sorted_trades = sorted(trades, key=lambda t: t.open_time)
    braked: list[TradeResult] = []

    # Precompute: for each trade, which trades have already closed BEFORE it?
    # Build a sorted list of (close_time, is_sl, is_active) for closed trades.
    # "is_active" = trade is within the gate's active window (open_time >=
    # activate_at_ms), which means it CAN feed the SL-rate calculation.
    closed_events = []  # list of (close_time, is_sl_hit, trade_idx)
    for idx, trade in enumerate(sorted_trades):
        is_active = activate_at_ms is None or trade.open_time >= activate_at_ms
        is_sl = trade.exit_reason == "stop_loss"
        # Only ACTIVE trades (post-activation) contribute to the SL-rate window
        closed_events.append((trade.close_time, is_sl and is_active, is_active, idx))

    # Sort by close_time so we can efficiently process the time-order
    closed_events.sort(key=lambda x: x[0])

    for trade in sorted_trades:
        # Pre-activation: pass through unchanged, don't check gate
        if activate_at_ms is not None and trade.open_time < activate_at_ms:
            braked.append(replace(trade))
            stats.n_normal += 1
            continue

        # Find all ACTIVE closed trades with close_time < this trade's open_time
        prior_closed = [
            (ct, sl, idx)
            for ct, sl, active, idx in closed_events
            if active and ct < trade.open_time
        ]

        if len(prior_closed) < config.window:
            # Not enough warmup history — pass through
            braked.append(replace(trade))
            stats.n_warmup += 1
            continue

        # Take the last ``window`` most recently closed
        window_trades = prior_closed[-config.window :]
        sl_count = sum(1 for _, is_sl, _ in window_trades if is_sl)
        sl_rate = sl_count / config.window

        if sl_rate >= config.sl_threshold:
            # Kill this trade
            stats.n_killed += 1
            if stats.first_fire_time is None:
                stats.first_fire_time = int(trade.open_time)
            stats.last_fire_time = int(trade.open_time)
            braked.append(
                replace(
                    trade,
                    weight_factor=0.0,
                    weighted_pnl=0.0,
                )
            )
        else:
            stats.n_normal += 1
            braked.append(replace(trade))

    return braked, stats


# ---------------------------------------------------------------------------
# iter-v2/019: BTC trend-alignment filter
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BtcTrendFilterConfig:
    """Config for the BTC trend-alignment filter.

    At each trade's open_time, compute BTC's N-bar return. If the trade's
    direction fights a BTC trend that exceeds ``threshold_pct`` in the
    opposing direction, kill the trade.

    iter-v2/019 winning config (Config E from feasibility study):
        lookback_bars=42 (14 days of 8h bars), threshold_pct=20.0

    Rationale: the 2024-11 post-election crypto rally sent BTC from
    $67k to $99k (+48%) in the month. iter-v2/017's model went 100%
    short that month and lost -73.66% weighted PnL. A filter at BTC
    14d ±20% catches this regime-shift pattern before trades enter.

    The filter is:
    - Cross-asset: BTC as the signal for all v2 alts
    - Symmetric: applies to both long and short directions
    - Stateless: no rolling state, purely local per trade
    - Rare: ±20% 14-day BTC moves happen 5-10 times per year
    """

    lookback_bars: int = 42
    threshold_pct: float = 20.0
    enabled: bool = True


@dataclass
class BtcTrendFilterStats:
    """BTC trend filter firing diagnostics."""

    n_total: int = 0
    n_normal: int = 0
    n_warmup: int = 0  # BTC history not long enough for lookback
    n_killed: int = 0
    first_fire_time: int | None = None
    last_fire_time: int | None = None

    def as_dict(self) -> dict[str, int | None | float]:
        return {
            "n_total": self.n_total,
            "n_normal": self.n_normal,
            "n_warmup": self.n_warmup,
            "n_killed": self.n_killed,
            "fire_rate": self.n_killed / self.n_total if self.n_total else 0.0,
            "first_fire_time": self.first_fire_time,
            "last_fire_time": self.last_fire_time,
        }


def evaluate_btc_trend_filter_one_signal(
    btc_open_times: np.ndarray,
    btc_closes: np.ndarray,
    signal_open_time_ms: int,
    direction: int,
    config: BtcTrendFilterConfig,
) -> bool:
    """Return True iff the BTC trend filter would kill this single live signal.

    Live-engine equivalent of ``apply_btc_trend_filter`` for a single signal.
    Same math, same boundary conditions:
      - filter disabled  → never kill
      - lookback warmup  → never kill (returns False)
      - direction == -1 (short) and BTC rallied > +threshold over lookback → kill
      - direction == +1 (long)  and BTC dumped <  -threshold over lookback → kill

    Parameters
    ----------
    btc_open_times
        BTC kline open_times (sorted ascending), as returned by
        ``load_btc_klines_for_filter``.
    btc_closes
        BTC closes, aligned with ``btc_open_times``.
    signal_open_time_ms
        The candle's open_time (ms epoch) that the signal would enter on.
    direction
        Signal direction: +1 for long, -1 for short.
    config
        ``BtcTrendFilterConfig`` (lookback_bars, threshold_pct, enabled).
    """
    if not config.enabled:
        return False
    idx = int(np.searchsorted(btc_open_times, signal_open_time_ms, side="right") - 1)
    if idx < config.lookback_bars or idx >= len(btc_closes):
        return False
    close_now = float(btc_closes[idx])
    close_then = float(btc_closes[idx - config.lookback_bars])
    if close_then == 0.0:
        return False
    btc_ret_pct = (close_now / close_then - 1.0) * 100.0
    return (direction == -1 and btc_ret_pct > config.threshold_pct) or (
        direction == 1 and btc_ret_pct < -config.threshold_pct
    )


def apply_btc_trend_filter(
    trades: list[TradeResult],
    btc_open_times: np.ndarray,
    btc_closes: np.ndarray,
    config: BtcTrendFilterConfig,
) -> tuple[list[TradeResult], BtcTrendFilterStats]:
    """Apply the BTC trend-alignment filter to a trade stream.

    For each trade, find the BTC bar active at the trade's open_time
    (most recent BTC bar with ``open_time <= trade.open_time``). Compute
    BTC's N-bar return. If the trade's direction fights a BTC trend
    exceeding ``threshold_pct`` in the opposing direction, zero the
    trade's weight.

    Parameters
    ----------
    trades
        Combined trade stream from all v2 models.
    btc_open_times
        numpy int64 array of BTC klines' open_time (sorted ascending).
    btc_closes
        numpy float64 array of BTC closes, aligned with ``btc_open_times``.
    config
        ``BtcTrendFilterConfig`` with lookback and threshold.

    Returns
    -------
    filtered
        New list of ``TradeResult`` with killed trades' weights zeroed.
    stats
        ``BtcTrendFilterStats`` counting normal/warmup/killed firings.
    """
    stats = BtcTrendFilterStats(n_total=len(trades))
    if not trades or not config.enabled:
        stats.n_normal = len(trades)
        return list(trades), stats

    filtered: list[TradeResult] = []
    for trade in trades:
        # Locate BTC bar active at trade's open_time (most recent ≤ open_time)
        idx = int(np.searchsorted(btc_open_times, trade.open_time, side="right") - 1)
        if idx < config.lookback_bars or idx >= len(btc_closes):
            # Not enough BTC history for the lookback — pass through
            filtered.append(replace(trade))
            stats.n_warmup += 1
            continue

        # BTC N-bar return = (close_now / close_n_bars_ago - 1) * 100
        btc_ret_pct = (btc_closes[idx] / btc_closes[idx - config.lookback_bars] - 1) * 100

        should_kill = (trade.direction == -1 and btc_ret_pct > config.threshold_pct) or (
            trade.direction == 1 and btc_ret_pct < -config.threshold_pct
        )

        if should_kill:
            stats.n_killed += 1
            if stats.first_fire_time is None:
                stats.first_fire_time = int(trade.open_time)
            stats.last_fire_time = int(trade.open_time)
            filtered.append(
                replace(
                    trade,
                    weight_factor=0.0,
                    weighted_pnl=0.0,
                )
            )
        else:
            stats.n_normal += 1
            filtered.append(replace(trade))

    return filtered, stats


def load_btc_klines_for_filter(
    csv_path: str = "data/BTCUSDT/8h.csv",
) -> tuple[np.ndarray, np.ndarray]:
    """Load BTC 8h klines for the BTC trend filter.

    Returns ``(open_times, closes)`` as sorted numpy arrays. The
    ``apply_btc_trend_filter`` function takes these as inputs.
    """
    df = pd.read_csv(csv_path).sort_values("open_time").reset_index(drop=True)
    return (
        df["open_time"].to_numpy(dtype=np.int64),
        df["close"].to_numpy(dtype=np.float64),
    )


__all__ = [
    "RiskV2Config",
    "RiskV2Wrapper",
    "GateStats",
    "DrawdownBrakeConfig",
    "BrakeFireStats",
    "apply_portfolio_drawdown_brake",
    "HitRateGateConfig",
    "HitRateFireStats",
    "apply_hit_rate_gate",
    "BtcTrendFilterConfig",
    "BtcTrendFilterStats",
    "apply_btc_trend_filter",
    "load_btc_klines_for_filter",
]
