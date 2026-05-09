"""v3 risk wrapper — overrides RiskV2Wrapper._build_lookups to use V3_FEATURE_COLUMNS.

iter-v3/001: V3_FEATURE_COLUMNS renames two fracdiff columns:
  fracdiff_logclose_d04  -> fracdiff_logclose_dstat
  fracdiff_logvolume_d04 -> fracdiff_logvolume_dstat

RiskV2Wrapper._build_lookups hardcodes V2_FEATURE_COLUMNS for z-score OOD.
RiskV3Wrapper overrides that single method to use V3_FEATURE_COLUMNS instead,
keeping all other gate logic identical.

iter-v3/022: adds primitive 9 — regime-conditional kill switch on TRX.
_build_lookups now also populates _btc_regime_lookup (per-bar BTC drawdown_30d
and vol_zscore_30d, computed PAST-ONLY with strict open_time < t discipline).
get_signal is overridden to apply the regime gate before handing off to the
inherited gate cascade (gates 1-6).

Past-only contract:
  - BTC drawdown_30d at bar t = (close[t-1] - max(close[t-90:t-1])) / max(...)
    using .shift(1) so bar t CANNOT see its own close.
  - BTC vol_zscore_30d at bar t = (logret_std_30[t-1] - expanding_mean) / expanding_std
    where the expanding window uses only rows with open_time < t.open_time.
  - The lookup is keyed by BTC open_time; at get_signal time we find the most
    recent BTC bar strictly BEFORE the symbol's bar open_time.

Track isolation: MUST NOT import from crypto_trade.features or
crypto_trade.features_v2.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.config import OOS_CUTOFF_MS
from crypto_trade.features_v3 import V3_FEATURE_COLUMNS
from crypto_trade.strategies import NO_SIGNAL
from crypto_trade.strategies.ml.risk_v2 import GateStats, RiskV2Wrapper, _compute_adx


def _build_btc_regime_lookup(
    btc_csv_path: Path,
    dd_lookback_bars: int = 90,
    vol_lookback_bars: int = 90,
) -> dict[str, np.ndarray]:
    """Build per-bar BTC drawdown_30d and vol_zscore_30d arrays (past-only).

    Parameters
    ----------
    btc_csv_path
        Path to data/BTCUSDT/8h.csv.
    dd_lookback_bars
        Rolling window in bars for drawdown (90 bars = 30 days at 8h).
    vol_lookback_bars
        Rolling window in bars for volatility z-score (90 bars = 30 days).

    Returns
    -------
    dict with keys:
        "open_time"     np.ndarray[int64]  — BTC bar open_times, sorted asc.
        "drawdown_pct"  np.ndarray[float]  — rolling DD%, past-only via shift(1).
        "vol_zscore"    np.ndarray[float]  — vol z-score, past-only via shift(1).

    Past-only discipline (verified by adversarial test test_regime_gate.py):
        drawdown at bar t uses close prices from [t-lookback : t-1] only.
        vol_zscore at bar t uses log-return std from [t-lookback : t-1] only.
        Both use .shift(1) so bar t's own close is NEVER included.
    """
    df = pd.read_csv(btc_csv_path, usecols=["open_time", "close"])
    df = df.sort_values("open_time").reset_index(drop=True)
    df["close"] = df["close"].astype(float)

    # Log returns — one period
    df["log_ret"] = np.log(df["close"] / df["close"].shift(1))

    # --- Rolling drawdown (past-only via shift(1)) ---
    # Shift close by 1 so at bar t we see close[t-1..t-lookback]
    close_shifted = df["close"].shift(1)
    # Rolling max over lookback_bars of the shifted series
    rolling_max = close_shifted.rolling(window=dd_lookback_bars, min_periods=1).max()
    # Drawdown = (close_shifted - rolling_max) / rolling_max  (negative when falling)
    df["drawdown_pct"] = (close_shifted - rolling_max) / rolling_max * 100.0

    # --- Rolling vol z-score (past-only via shift(1)) ---
    # Compute rolling 30-day log-return std (shifted — only past bars contribute)
    logret_shifted = df["log_ret"].shift(1)
    rolling_std = logret_shifted.rolling(window=vol_lookback_bars, min_periods=2).std()

    # Expanding IS-mean and IS-std of the rolling_std series (calibrated on the
    # IS window only, but applied globally for a conservative OOS estimate).
    # We use all available history as expanding window — the EDA uses an
    # IS-only expanding window but here we apply conservatively to full series.
    expanding_mean = rolling_std.expanding(min_periods=10).mean()
    expanding_std = rolling_std.expanding(min_periods=10).std().replace(0.0, np.nan)

    df["vol_zscore"] = (rolling_std - expanding_mean) / expanding_std

    return {
        "open_time": df["open_time"].to_numpy(dtype=np.int64),
        "drawdown_pct": df["drawdown_pct"].to_numpy(dtype=np.float64),
        "vol_zscore": df["vol_zscore"].to_numpy(dtype=np.float64),
    }


class RiskV3Wrapper(RiskV2Wrapper):
    """v3 variant of RiskV2Wrapper that uses V3_FEATURE_COLUMNS for z-score OOD.

    Identical to RiskV2Wrapper in all gate logic. Only _build_lookups is
    overridden to read the v3 parquet schema (fracdiff_logclose_dstat instead
    of fracdiff_logclose_d04).

    iter-v3/022: adds primitive 9 (regime-conditional kill switch).
    _build_lookups also populates _btc_regime_lookup.
    get_signal checks the regime gate for symbols in config.regime_gate_symbols
    before delegating to the inherited gate cascade.
    """

    def __init__(self, inner, config) -> None:  # type: ignore[override]
        super().__init__(inner, config)
        # iter-v3/022: BTC regime lookup — populated in _build_lookups
        self._btc_regime_lookup: dict[str, np.ndarray] | None = None

    def _build_lookups(self, master: pd.DataFrame) -> None:
        """Load v3 features and compute ADX per symbol — v3 parquet schema.

        Overrides RiskV2Wrapper._build_lookups to use V3_FEATURE_COLUMNS.
        Also builds BTC regime lookup (iter-v3/022 primitive 9) when
        config.enable_regime_gate is True.
        """
        import pyarrow.parquet as pq  # noqa: PLC0415

        features_dir = getattr(self.inner, "features_dir", "data/features_v3")
        interval = getattr(self.inner, "_interval", "8h")

        symbols = list(pd.unique(master["symbol"]))
        for sym in symbols:
            path = Path(features_dir) / f"{sym}_{interval}_features.parquet"
            if not path.exists():
                continue

            # atr_pct_rank_200 is always needed for the vol-scaling and low-vol
            # gates (primitives 1 and 5 in the 7-primitive table), regardless of
            # whether it appears in V3_FEATURE_COLUMNS.  When V3_FEATURE_COLUMNS
            # is the top-14 subset (iter-v3/007+) atr_pct_rank_200 is NOT in the
            # training feature list but MUST still be loaded from the parquet as a
            # gate input.  See brief iter-v3/007 Section 3.4.
            needed = [
                "open_time",
                "high",
                "low",
                "close",
                "hurst_100",
                "atr_pct_rank_200",  # gate primitive — independent of V3_FEATURE_COLUMNS
                *V3_FEATURE_COLUMNS,
            ]
            needed = list(dict.fromkeys(needed))  # dedup, preserve order
            table = pq.read_table(path, columns=needed).to_pandas()
            table = table.sort_values("open_time").reset_index(drop=True)

            # Training-window = IS (open_time < OOS_CUTOFF_MS)
            is_mask = table["open_time"] < OOS_CUTOFF_MS
            is_df = table.loc[is_mask, list(V3_FEATURE_COLUMNS)]

            # Snapshot feature mean/std over IS window
            self._feature_mean[sym] = is_df.mean(skipna=True)
            self._feature_std[sym] = is_df.std(skipna=True).replace(0, np.nan)

            # Hurst percentile band over IS window
            hurst_is = table.loc[is_mask, "hurst_100"].dropna().to_numpy()
            if len(hurst_is) > 10:
                self._hurst_lower[sym] = float(np.quantile(hurst_is, self.config.hurst_lower_pct))
                self._hurst_upper[sym] = float(np.quantile(hurst_is, self.config.hurst_upper_pct))
            else:
                self._hurst_lower[sym] = -np.inf
                self._hurst_upper[sym] = np.inf

            # Compute ADX for the full series (IS + OOS)
            adx_arr = _compute_adx(
                table["high"].to_numpy(),
                table["low"].to_numpy(),
                table["close"].to_numpy(),
                period=self.config.adx_period,
            )

            # Build lookup table indexed by open_time
            self._lookup[sym] = {
                "open_time": table["open_time"].to_numpy(dtype=np.int64),
                "adx": adx_arr,
                "atr_pct_rank_200": table["atr_pct_rank_200"].to_numpy(),
                "hurst_100": table["hurst_100"].to_numpy(),
                "features": table[list(V3_FEATURE_COLUMNS)].to_numpy(),
            }

        # iter-v3/022: build BTC regime lookup (primitive 9) if enabled.
        # Uses data/BTCUSDT/8h.csv — same source as the BTC trend filter.
        # Built once per compute_features call (once per retraining month).
        if self.config.enable_regime_gate and self.config.regime_gate_symbols:
            btc_csv = Path("data") / "BTCUSDT" / "8h.csv"
            if btc_csv.exists():
                self._btc_regime_lookup = _build_btc_regime_lookup(
                    btc_csv,
                    dd_lookback_bars=self.config.regime_dd_lookback_bars,
                    vol_lookback_bars=self.config.regime_vol_lookback_bars,
                )

    def _regime_gate_fires(self, symbol: str, open_time_ms: int) -> bool:
        """iter-v3/022 primitive 9: return True if regime-gate should kill this signal.

        Past-only: find the most recent BTC bar with open_time STRICTLY LESS THAN
        the symbol's open_time.  The BTC bar at open_time == symbol's open_time is
        excluded (past-only discipline — the gate cannot see the current bar).

        Returns False (gate does not fire) when:
          - symbol not in regime_gate_symbols
          - BTC lookup not built (CSV missing)
          - No BTC bar precedes open_time_ms
          - drawdown / vol_zscore is NaN (warmup period)
        """
        if symbol not in self.config.regime_gate_symbols:
            return False
        if self._btc_regime_lookup is None:
            return False

        btc_times = self._btc_regime_lookup["open_time"]
        # searchsorted 'left' gives insertion point for open_time_ms.
        # idx-1 = last bar with open_time STRICTLY LESS than open_time_ms.
        # This is the past-only contract: current bar t is excluded.
        idx = int(np.searchsorted(btc_times, open_time_ms, side="left")) - 1
        if idx < 0:
            return False  # No past BTC bar — no data to gate on

        dd = self._btc_regime_lookup["drawdown_pct"][idx]
        vz = self._btc_regime_lookup["vol_zscore"][idx]

        if not np.isfinite(dd) or not np.isfinite(vz):
            return False  # NaN in warmup period — don't gate

        # Gate fires on OR condition: DD exceeds threshold OR |vol_z| exceeds threshold.
        # Note: drawdown_pct is negative (e.g. -26.3%), so we compare abs value.
        dd_fires = abs(dd) > self.config.regime_dd_threshold_pct
        vol_z_fires = abs(vz) > self.config.regime_vol_zscore_threshold
        return dd_fires or vol_z_fires

    def get_signal(self, symbol: str, open_time: int):  # type: ignore[override]
        """Override to apply regime gate (primitive 9) and direction-block (primitive 10)
        on top of the inherited gate cascade.

        Order:
          1. primitive 9 (regime gate; iter-v3/022) — fires BEFORE inner inference.
             A regime-stress bar produces NO_SIGNAL without ever consulting the model.
          2. primitive 10 (direction block; iter-v3/047) — fires AFTER inner inference.
             We need to know the direction the model picked, so the inner.get_signal
             call must complete first. Then if the picked direction is in the
             configured block list for this symbol, we suppress to NO_SIGNAL.
          3. Inherited gates 1-8 (RiskV2Wrapper) — applied to all surviving signals.

        Both new primitives default off (enable_regime_gate=False; block_long_for=();
        block_short_for=()) so v1/v2/v3-prior behavior is preserved.
        """
        # Regime gate fires FIRST — before ANY other gate including inner strategy.
        # This matches the EDA's per-bar candidate-signal suppression design:
        # by killing the signal before Optuna sees it, the training-data distribution
        # shifts to remove regime-stress bars from the optimization landscape.
        if self.config.enable_regime_gate and symbol in self.config.regime_gate_symbols:
            if self._regime_gate_fires(symbol, open_time):
                stats = self._gate_stats.setdefault(symbol, GateStats())
                stats.regime_gate_fires += 1
                return NO_SIGNAL

        # Inherited gate cascade (computes inner.get_signal first, then applies gates 1-8).
        sig = super().get_signal(symbol, open_time)

        # iter-v3/047: primitive 10 — direction-asymmetric kill switch.
        # Applied AFTER the inherited cascade so the inner strategy's signal direction
        # is known. Any non-NO_SIGNAL whose direction matches the block list is suppressed.
        # The check is against the FINAL (post-gate) direction so it composes cleanly with
        # vol-scaling (which only changes weight, not direction).
        if sig.direction == 1 and symbol in self.config.block_long_for:
            stats = self._gate_stats.setdefault(symbol, GateStats())
            stats.direction_block_fires += 1
            return NO_SIGNAL
        if sig.direction == -1 and symbol in self.config.block_short_for:
            stats = self._gate_stats.setdefault(symbol, GateStats())
            stats.direction_block_fires += 1
            return NO_SIGNAL

        return sig

    def gate_stats_summary(self) -> dict[str, dict[str, float]]:
        """Extend parent summary with regime_gate_fires (iter-v3/022) +
        direction_block_fires (iter-v3/047) counters."""
        out = super().gate_stats_summary()
        for sym, s in self._gate_stats.items():
            out[sym]["regime_gate_fires"] = s.regime_gate_fires
            out[sym]["direction_block_fires"] = s.direction_block_fires
            total_seen = s.signals_seen
            out[sym]["regime_gate_fire_rate"] = (
                s.regime_gate_fires / total_seen if total_seen else 0.0
            )
        return out


__all__ = ["RiskV3Wrapper"]
