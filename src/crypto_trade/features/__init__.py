"""Feature engineering registry, orchestrator, and parallel runner."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from crypto_trade.kline_array import load_kline_array
from crypto_trade.storage import csv_path

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

GROUP_REGISTRY: dict[str, Callable[[pd.DataFrame], pd.DataFrame]] = {}


def _register(name: str, fn: Callable[[pd.DataFrame], pd.DataFrame]) -> None:
    GROUP_REGISTRY[name] = fn


def list_groups() -> list[str]:
    return sorted(GROUP_REGISTRY.keys())


# ---------------------------------------------------------------------------
# Feature generation
# ---------------------------------------------------------------------------


def generate_features(
    df: pd.DataFrame,
    groups: list[str],
) -> pd.DataFrame:
    """Run selected feature groups on a DataFrame, returning it with new columns."""
    for group_name in groups:
        fn = GROUP_REGISTRY[group_name]
        df = fn(df)
        # Defragment after each group so the next group (and pandas-ta internals)
        # don't trigger PerformanceWarning on the accumulated columns.
        df = df.copy()
    return df


# ---------------------------------------------------------------------------
# Per-symbol processing (top-level function for pickling in multiprocessing)
# ---------------------------------------------------------------------------


def process_symbol(
    symbol: str,
    interval: str,
    data_dir: str,
    groups: list[str],
    start_ms: int | None,
    end_ms: int | None,
    output_dir: str,
    output_format: str = "csv",
) -> tuple[str, int, int]:
    """Load kline data, generate features, write output. Returns (symbol, n_rows, n_features)."""
    path = csv_path(Path(data_dir), symbol, interval)
    ka = load_kline_array(path)

    if len(ka) == 0:
        return (symbol, 0, 0)

    if start_ms is not None or end_ms is not None:
        ka = ka.time_slice(start_ms, end_ms)

    if len(ka) == 0:
        return (symbol, 0, 0)

    df = ka.df.copy()
    # iter-v1/023: ensure symbol column is set so feature groups that need it
    # (e.g. funding_v1 reads data/funding_rates/<symbol>.csv) can resolve it.
    if "symbol" not in df.columns:
        df["symbol"] = symbol
    original_cols = set(df.columns)

    df = generate_features(df, groups)

    new_cols = [c for c in df.columns if c not in original_cols]
    n_features = len(new_cols)
    n_rows = len(df)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if output_format == "parquet":
        from crypto_trade.feature_store import write_parquet

        out_path = out_dir / f"{symbol}_{interval}_features.parquet"
        write_parquet(df, out_path)
    else:
        out_path = out_dir / f"{symbol}_{interval}_features.csv"
        df.to_csv(out_path, index=False)

    return (symbol, n_rows, n_features)


# ---------------------------------------------------------------------------
# CLI orchestrator
# ---------------------------------------------------------------------------


def run_features(
    symbols: list[str],
    interval: str,
    data_dir: str,
    groups: list[str],
    start_ms: int | None,
    end_ms: int | None,
    output_dir: str,
    workers: int = 1,
    output_format: str = "csv",
) -> list[tuple[str, int, int]]:
    """Run feature generation for all symbols, with optional parallelism."""
    results: list[tuple[str, int, int]] = []

    if workers <= 1:
        # Sequential with progress
        for symbol in tqdm(symbols, desc="Processing", unit="sym"):
            result = process_symbol(
                symbol, interval, data_dir, groups, start_ms, end_ms, output_dir, output_format
            )
            results.append(result)
    else:
        # Parallel
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    process_symbol,
                    symbol,
                    interval,
                    data_dir,
                    groups,
                    start_ms,
                    end_ms,
                    output_dir,
                    output_format,
                ): symbol
                for symbol in symbols
            }
            for future in tqdm(
                as_completed(futures), total=len(futures), desc="Processing", unit="sym"
            ):
                result = future.result()
                results.append(result)

    return results


# ---------------------------------------------------------------------------
# Auto-register all feature groups on import
# ---------------------------------------------------------------------------

from crypto_trade.features.calendar import add_calendar_features  # noqa: E402
from crypto_trade.features.entropy_cusum import add_entropy_cusum_features  # noqa: E402
from crypto_trade.features.interaction import add_interaction_features  # noqa: E402
from crypto_trade.features.mean_reversion import add_mean_reversion_features  # noqa: E402
from crypto_trade.features.momentum import add_momentum_features  # noqa: E402
from crypto_trade.features.statistical import add_statistical_features  # noqa: E402
from crypto_trade.features.trend import add_trend_features  # noqa: E402
from crypto_trade.features.volatility import add_volatility_features  # noqa: E402
from crypto_trade.features.volume import add_volume_features  # noqa: E402

# iter-v1/034: basis (perp-spot) z-score feature family.
# Mirrors the funding_v1 / open_interest_v1 pattern: add_basis_v1_features lives in
# features_v1/ (v1 track), called here via the legacy features registry so
# that `uv run crypto-trade features --track v1 --groups basis_v1` writes
# basis_zscore_30 to the v1 parquets.
from crypto_trade.features_v1.basis_v1 import (  # noqa: E402
    add_basis_v1_features as _add_basis_v1_features,
)

# iter-v1/023: funding-rate z-score feature family.
# The wrapper preserves track isolation: add_funding_v1_features lives in
# features_v1/ (v1 track), called here via the legacy features registry so
# that `uv run crypto-trade features --track v1 --groups funding_v1` writes
# funding_rate_zscore_30 + funding_rate_zscore_90 to the v1 parquets.
from crypto_trade.features_v1.funding_v1 import (  # noqa: E402
    add_funding_v1_features as _add_funding_v1_features,
)

# iter-v1/025: open-interest delta z-score feature family.
# Mirrors the funding_v1 pattern: add_oi_delta_v1_features lives in
# features_v1/ (v1 track), called here via the legacy features registry so
# that `uv run crypto-trade features --track v1 --groups open_interest_v1` writes
# oi_delta_30_z90 to the v1 parquets.
from crypto_trade.features_v1.open_interest_v1 import (  # noqa: E402
    add_oi_delta_v1_features as _add_oi_delta_v1_features,
)

_register("momentum", add_momentum_features)
_register("volatility", add_volatility_features)
_register("trend", add_trend_features)
_register("volume", add_volume_features)
_register("mean_reversion", add_mean_reversion_features)
_register("statistical", add_statistical_features)
_register("interaction", add_interaction_features)
_register("calendar", add_calendar_features)
_register("entropy_cusum", add_entropy_cusum_features)
_register("funding_v1", _add_funding_v1_features)  # iter-v1/023
_register("open_interest_v1", _add_oi_delta_v1_features)  # iter-v1/025
_register("basis_v1", _add_basis_v1_features)  # iter-v1/034

# iter-v1/040: composed feature family (regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5)).
# BYTE-FOR-BYTE Hurst math from features_v3/regime_v3.py; v1-track-isolated (no cross-track import).
# Registered here so `uv run crypto-trade features --track v1 --groups composed_v1` writes
# regime_momentum_signed_5d to v1 parquets.
from crypto_trade.features_v1.composed_v1 import (  # noqa: E402
    add_composed_v1_features as _add_composed_v1_features,
)

_register("composed_v1", _add_composed_v1_features)  # iter-v1/040

# iter-v1/047: statistical higher-moment feature family (skew_zscore_21) was REVERTED
# at closeout (NEG-CLEAN-PRE-EDA: pre-launch F5 IC orthogonality gate FAILED at
# |IC|=0.8132 vs stat_skew_20; ABORT threshold 0.60). The statistical_v1 module file
# is kept on disk (clean code, future-iter ready for non-skew higher-moment primitives)
# but is intentionally NOT registered in GROUP_REGISTRY — `crypto-trade features` will
# not write skew_zscore_21 to v1 parquets.

__all__ = [
    "GROUP_REGISTRY",
    "generate_features",
    "list_groups",
    "process_symbol",
    "run_features",
]
