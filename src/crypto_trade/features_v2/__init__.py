"""v2 feature registry and orchestrator — diversification track.

Isolated from ``crypto_trade.features`` (the v1 package). v2 code must NEVER
import from the v1 package; the first-iteration QE audit greps for such imports.

Groups in the v2 registry:

- ``regime`` — Hurst, ATR percentile ranks, BB width rank, CUSUM reset count,
  and the ``natr_21_raw`` helper column used by the shared labeling code
- ``tail_risk`` — rolling skew/kurt, range-based realized vol, max drawdown
- ``price_efficient_vol`` — Parkinson, Garman-Klass, Rogers-Satchell estimators
- ``momentum_accel`` — momentum acceleration, vol-normalized EMA spread, return autocorr
- ``volume_micro`` — VWAP deviation, volume CV, OBV slope, HL range ratio, close-in-range
- ``fracdiff`` — fractionally differentiated log close/volume (AFML Ch. 5)

Feature columns used by the LightGBM model are listed in ``V2_FEATURE_COLUMNS``
below. That list EXCLUDES ``natr_21_raw`` (which is only read by the labeling
code via ``LightGbmStrategy.atr_column``) so the model never sees a raw ATR.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from crypto_trade.features_v2.cross_btc import add_cross_btc_features
from crypto_trade.features_v2.cross_v2sym import add_cross_v2sym_features
from crypto_trade.features_v2.fracdiff_v2 import add_fracdiff_features
from crypto_trade.features_v2.microstructure_v2 import add_microstructure_v2_features
from crypto_trade.features_v2.momentum_accel import add_momentum_accel_features
from crypto_trade.features_v2.price_efficient_vol import add_price_efficient_vol_features
from crypto_trade.features_v2.regime import add_regime_features
from crypto_trade.features_v2.tail_risk import add_tail_risk_features
from crypto_trade.features_v2.volume_micro import add_volume_micro_features
from crypto_trade.kline_array import load_kline_array
from crypto_trade.storage import csv_path

GROUP_REGISTRY: dict[str, Callable[[pd.DataFrame], pd.DataFrame]] = {
    "regime": add_regime_features,
    "tail_risk": add_tail_risk_features,
    "price_efficient_vol": add_price_efficient_vol_features,
    "momentum_accel": add_momentum_accel_features,
    "volume_micro": add_volume_micro_features,
    "fracdiff": add_fracdiff_features,
    "cross_btc": add_cross_btc_features,  # iter-v2/026: BTC cross-asset features
    "microstructure_v2": add_microstructure_v2_features,  # iter-v2/039
    "cross_v2sym": add_cross_v2sym_features,  # iter-v2/043: relative strength within v2 universe
}

V2_FEATURE_COLUMNS: tuple[str, ...] = (
    # Regime
    "hurst_100",
    "hurst_200",
    "hurst_diff_100_50",
    "atr_pct_rank_200",
    "atr_pct_rank_500",
    "atr_pct_rank_1000",
    "bb_width_pct_rank_100",
    "cusum_reset_count_200",
    # Tail risk
    "ret_skew_50",
    "ret_skew_100",
    "ret_skew_200",
    "ret_kurt_50",
    "ret_kurt_200",
    "range_realized_vol_50",
    "max_dd_window_50",
    # Efficient OHLC vol
    "parkinson_vol_20",
    "parkinson_vol_50",
    "garman_klass_vol_20",
    "rogers_satchell_vol_20",
    "parkinson_gk_ratio_20",
    # Momentum acceleration
    "mom_accel_5_20",
    "mom_accel_20_100",
    "ema_spread_atr_20",
    "ret_autocorr_lag1_50",
    "ret_autocorr_lag5_50",
    # Volume microstructure
    "vwap_dev_20",
    "vwap_dev_50",
    "volume_mom_ratio_20",
    "volume_cv_50",
    "obv_slope_50",
    "hl_range_ratio_20",
    "close_pos_in_range_20",
    "close_pos_in_range_50",
    # Fracdiff
    "fracdiff_logclose_d04",
    "fracdiff_logvolume_d04",
    # BTC cross-asset
    "btc_ret_3d",
    "btc_ret_7d",
    "btc_ret_14d",
    "btc_vol_14d",
    "sym_vs_btc_ret_7d",
    # iter-v2/043 cross-v2sym features REMOVED — IS −70%, OOS −69%.
    # Module stays in registry but features excluded from V2_FEATURE_COLUMNS.
)
"""The 35 features fed to the LightGBM model in iter-v2/001.

``natr_21_raw`` is intentionally absent — it lives in the parquet as a
labeling helper only.
"""

V2_NON_FEATURE_COLUMNS: tuple[str, ...] = ("natr_21_raw",)
"""Columns computed by the v2 feature pipeline that are NOT used as model inputs.

These exist for compatibility with the shared labeling code. ``LightGbmStrategy``
accesses ``natr_21_raw`` via its ``atr_column`` parameter to compute ATR-scaled
triple-barrier labels, but the model never trains on the raw ATR value.
"""


def list_groups() -> list[str]:
    return sorted(GROUP_REGISTRY.keys())


def generate_features_v2(df: pd.DataFrame, groups: list[str] | None = None) -> pd.DataFrame:
    """Run the selected v2 feature groups on *df* and return the augmented frame."""
    if groups is None:
        groups = list(GROUP_REGISTRY.keys())
    for group_name in groups:
        fn = GROUP_REGISTRY[group_name]
        df = fn(df)
        df = df.copy()
    return df


def process_symbol_v2(
    symbol: str,
    interval: str,
    data_dir: str,
    output_dir: str,
    start_ms: int | None = None,
    end_ms: int | None = None,
) -> tuple[str, int, int]:
    """Load klines for *symbol*, run the full v2 feature pipeline, write parquet.

    Returns ``(symbol, n_rows, n_feature_columns)``.
    """
    path = csv_path(Path(data_dir), symbol, interval)
    ka = load_kline_array(path)
    if len(ka) == 0:
        return (symbol, 0, 0)

    if start_ms is not None or end_ms is not None:
        ka = ka.time_slice(start_ms, end_ms)
    if len(ka) == 0:
        return (symbol, 0, 0)

    df = ka.df.copy()
    df["symbol"] = symbol  # iter-v2/043: needed for cross_v2sym features
    before_cols = set(df.columns)
    df = generate_features_v2(df, list(GROUP_REGISTRY.keys()))
    added = [c for c in df.columns if c not in before_cols]

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    out_path = out / f"{symbol}_{interval}_features.parquet"
    df.to_parquet(out_path, index=False)

    return (symbol, len(df), len(added))


def run_features_v2(
    symbols: list[str],
    interval: str,
    data_dir: str,
    output_dir: str,
    start_ms: int | None = None,
    end_ms: int | None = None,
    workers: int = 1,
) -> list[tuple[str, int, int]]:
    """Batch generate v2 features across *symbols* with optional multiprocessing."""
    results: list[tuple[str, int, int]] = []
    if workers <= 1:
        for symbol in tqdm(symbols, desc="v2 features", unit="sym"):
            results.append(
                process_symbol_v2(symbol, interval, data_dir, output_dir, start_ms, end_ms)
            )
        return results

    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = {
            ex.submit(process_symbol_v2, s, interval, data_dir, output_dir, start_ms, end_ms): s
            for s in symbols
        }
        for fut in tqdm(as_completed(futures), total=len(futures), desc="v2 features", unit="sym"):
            results.append(fut.result())
    return results


__all__ = [
    "GROUP_REGISTRY",
    "V2_FEATURE_COLUMNS",
    "V2_NON_FEATURE_COLUMNS",
    "generate_features_v2",
    "list_groups",
    "process_symbol_v2",
    "run_features_v2",
]
