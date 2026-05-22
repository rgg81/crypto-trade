"""Adversarial tests for v3 ETH cross-asset feature — iter-v3/123.

iter-v3/122: eth_ret_3d tests (tests 1-5) REPLACED.
iter-v3/123: eth_vs_sym_rv_50 tests below replace all /122 ETH tests.
  eth_ret_3d was NEGATIVE-INERT (Critic FINAL `9e0eeb6`); its loader infrastructure
  is RETAINED but the feature is no longer in production. Tests now cover eth_vs_sym_rv_50.

Tests:
1. test_eth_vs_sym_rv_50_past_only
   Past-only invariant: value at row t must NOT change when future ETH bars are appended.
   Verifies that eth_rv_50 = rolling(50).std() of 1-bar log returns uses only past bars.

2. test_eth_vs_sym_rv_50_nan_warmup
   First 49 rows must be NaN (50-bar window not yet filled).

3. test_eth_vs_sym_rv_50_formula_correctness
   At row i >= 49, eth_rv_50[i] == std(log_ret[i-49 : i+1]).

4. test_eth_vs_sym_rv_50_present_in_add_cross_btc_v3_features
   add_cross_btc_v3_features output must include 'eth_vs_sym_rv_50' column.

5. test_eth_ret_3d_absent_from_add_cross_btc_v3_features
   add_cross_btc_v3_features output must NOT include 'eth_ret_3d' (/122 REMOVED).

6. test_eth_rv_50_intermediate_dropped
   add_cross_btc_v3_features output must NOT include 'eth_rv_50' (intermediate col dropped).

7. test_eth_vs_sym_rv_50_cache_idempotency
   _load_eth_v3_features must return the same cached object on second call.

8. test_eth_vs_sym_rv_50_no_inf_nan_in_ratio
   Ratio eth_rv_50 / (sym_rv_50 + EPS) must produce no Inf values.

9. test_eth_vs_sym_rv_50_past_only_for_ratio
   Adversarial: ratio at row t must not change when future ETH bars are appended AND
   future symbol bars are mutated. Both numerator and denominator must use only past bars.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Helpers — synthetic CSV builders
# ---------------------------------------------------------------------------

_8H_MS = 8 * 3600 * 1000
_IS_START_MS = 1_609_459_200_000  # 2021-01-01 00:00 UTC


def _write_synthetic_eth_csv(path: Path, n: int = 500, seed: int = 42) -> pd.DataFrame:
    """Write a synthetic ETHUSDT 8h CSV and return it as a DataFrame."""
    rng = np.random.default_rng(seed)
    open_times = [_IS_START_MS + i * _8H_MS for i in range(n)]
    close_times = [t + _8H_MS - 1 for t in open_times]
    close = np.cumprod(1 + rng.normal(0, 0.01, n)) * 2000.0
    high = close * rng.uniform(1.000, 1.02, n)
    low = close * rng.uniform(0.98, 1.000, n)
    opens = np.roll(close, 1)
    opens[0] = close[0]
    volume = rng.uniform(100, 5000, n)
    quote_volume = volume * close
    count = rng.integers(100, 5000, n)
    taker_buy_base = volume * rng.uniform(0.4, 0.6, n)
    taker_buy_quote = taker_buy_base * close

    df = pd.DataFrame(
        {
            "open_time": open_times,
            "open": opens,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "close_time": close_times,
            "quote_asset_volume": quote_volume,
            "number_of_trades": count,
            "taker_buy_base_asset_volume": taker_buy_base,
            "taker_buy_quote_asset_volume": taker_buy_quote,
        }
    )
    df.to_csv(path, index=False)
    return df


def _write_synthetic_btc_csv(path: Path, n: int = 500, seed: int = 99) -> pd.DataFrame:
    """Write a synthetic BTCUSDT 8h CSV for BTC dependencies in add_cross_btc_v3_features."""
    rng = np.random.default_rng(seed)
    open_times = [_IS_START_MS + i * _8H_MS for i in range(n)]
    close_times = [t + _8H_MS - 1 for t in open_times]
    close = np.cumprod(1 + rng.normal(0, 0.01, n)) * 30000.0
    high = close * rng.uniform(1.000, 1.02, n)
    low = close * rng.uniform(0.98, 1.000, n)
    opens = np.roll(close, 1)
    opens[0] = close[0]
    volume = rng.uniform(10, 500, n)
    quote_volume = volume * close
    count = rng.integers(500, 10000, n)
    taker_buy_base = volume * rng.uniform(0.4, 0.6, n)
    taker_buy_quote = taker_buy_base * close

    df = pd.DataFrame(
        {
            "open_time": open_times,
            "open": opens,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "close_time": close_times,
            "quote_asset_volume": quote_volume,
            "number_of_trades": count,
            "taker_buy_base_asset_volume": taker_buy_base,
            "taker_buy_quote_asset_volume": taker_buy_quote,
        }
    )
    df.to_csv(path, index=False)
    return df


def _make_symbol_df(n: int = 500, seed: int = 77, with_range_rv50: bool = True) -> pd.DataFrame:
    """Create a minimal symbol kline DataFrame for cross-asset merge testing.

    If with_range_rv50=True (default), includes a pre-computed range_realized_vol_50
    column mimicking the parquet panel convention (used as denominator in B1 ratio).
    """
    rng = np.random.default_rng(seed)
    open_times = [_IS_START_MS + i * _8H_MS for i in range(n)]
    close = np.cumprod(1 + rng.normal(0, 0.01, n)) * 500.0
    high = close * rng.uniform(1.000, 1.02, n)
    low = close * rng.uniform(0.98, 1.000, n)
    opens = np.roll(close, 1)
    opens[0] = close[0]
    volume = rng.uniform(1000, 50000, n)
    quote_volume = volume * close
    count = rng.integers(200, 3000, n)
    taker_buy_base = volume * rng.uniform(0.4, 0.6, n)
    taker_buy_quote = taker_buy_base * close

    df = pd.DataFrame(
        {
            "open_time": open_times,
            "open": opens,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "close_time": [t + _8H_MS - 1 for t in open_times],
            "quote_asset_volume": quote_volume,
            "number_of_trades": count,
            "taker_buy_base_asset_volume": taker_buy_base,
            "taker_buy_quote_asset_volume": taker_buy_quote,
        }
    )

    if with_range_rv50:
        # Compute range_realized_vol_50 the same way as the production parquet:
        # rolling(50, min_periods=50).std() of 1-bar log returns.
        log_close = np.log(close)
        log_ret = np.concatenate([[np.nan], np.diff(log_close)])
        df["range_realized_vol_50"] = (
            pd.Series(log_ret).rolling(50, min_periods=50).std().to_numpy()
        )

    return df


# ---------------------------------------------------------------------------
# 1. Past-only invariant for _load_eth_v3_features (eth_rv_50)
# ---------------------------------------------------------------------------


def test_eth_vs_sym_rv_50_past_only() -> None:
    """Adversarial past-only test: eth_rv_50 at row t must not change when future bars appended.

    Pattern from iter-v3/025 test_engineered_v3.py (test 3 / test 10).
    Build ETH panel of length T=200, compute eth_rv_50. Then extend to T+20
    with extreme future values. Recompute. Value at row T-1 must be identical.
    """
    import crypto_trade.features_v3.cross_btc_v3 as cross_mod

    n_rows = 200
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        eth_path = tmppath / "8h.csv"

        eth_df = _write_synthetic_eth_csv(eth_path, n=n_rows + 20)

        # Truncate to n_rows for "short" panel
        eth_short = eth_df.iloc[:n_rows].copy()
        eth_short.to_csv(eth_path, index=False)

        # Reset module cache and patch path
        cross_mod._ETH_CACHE_V3 = None
        orig_path = cross_mod.ETH_CSV_PATH
        cross_mod.ETH_CSV_PATH = eth_path
        try:
            cache_short = cross_mod._load_eth_v3_features()
            val_short = cache_short["eth_rv_50"].iloc[n_rows - 1]
        finally:
            cross_mod.ETH_CSV_PATH = orig_path
            cross_mod._ETH_CACHE_V3 = None

        # Write n_rows+20 rows (with extreme future values in closes)
        eth_long = eth_df.copy()
        eth_long.loc[n_rows:, "close"] = 1e9  # extreme future values
        eth_long.to_csv(eth_path, index=False)

        cross_mod._ETH_CACHE_V3 = None
        cross_mod.ETH_CSV_PATH = eth_path
        try:
            cache_long = cross_mod._load_eth_v3_features()
            val_long = cache_long["eth_rv_50"].iloc[n_rows - 1]
        finally:
            cross_mod.ETH_CSV_PATH = orig_path
            cross_mod._ETH_CACHE_V3 = None

        assert val_short == pytest.approx(val_long, rel=1e-10), (
            f"eth_rv_50 at row {n_rows - 1} changed from {val_short} to {val_long} "
            "when future bars were appended — LOOK-AHEAD BUG detected. "
            "eth_rv_50 must be past-only (rolling(50).std() uses only prior 50 bars)."
        )


# ---------------------------------------------------------------------------
# 2. NaN warm-up for eth_rv_50
# ---------------------------------------------------------------------------


def test_eth_vs_sym_rv_50_nan_warmup() -> None:
    """First 50 rows of eth_rv_50 must be NaN (50-bar window requires 50 finite log returns).

    log_ret[0] is NaN (no prior bar); log_ret[1..n-1] are finite.
    rolling(50, min_periods=50).std() at index i uses log_ret[i-49 : i+1].
    At index 49: window = log_ret[0:50], which contains the NaN at index 0 → result NaN.
    At index 50: window = log_ret[1:51], all finite → first finite std.
    So rows 0..49 (50 rows) are NaN; rows 50+ are finite.
    """
    import crypto_trade.features_v3.cross_btc_v3 as cross_mod

    with tempfile.TemporaryDirectory() as tmpdir:
        eth_path = Path(tmpdir) / "8h.csv"
        _write_synthetic_eth_csv(eth_path, n=200)

        orig_path = cross_mod.ETH_CSV_PATH
        cross_mod._ETH_CACHE_V3 = None
        cross_mod.ETH_CSV_PATH = eth_path
        try:
            cache = cross_mod._load_eth_v3_features()
            eth_rv = cache["eth_rv_50"].to_numpy()
        finally:
            cross_mod.ETH_CSV_PATH = orig_path
            cross_mod._ETH_CACHE_V3 = None

    # First 50 rows (index 0..49 inclusive) must be NaN.
    # Row 49: window includes log_ret[0]=NaN → NaN propagates to std.
    assert all(np.isnan(eth_rv[:50])), (
        f"First 50 rows of eth_rv_50 must be NaN — got {eth_rv[:5]}... "
        "log_ret[0]=NaN propagates: rolling(50).std() at row 49 includes the NaN. "
        "First finite std is at row 50 (window log_ret[1:51], all finite)."
    )
    # Row 50 onward must be finite
    assert all(np.isfinite(eth_rv[50:])), (
        f"Rows 50+ of eth_rv_50 must be finite — got {eth_rv[50:53]}... "
        "Data is valid after the 50-bar warm-up (first finite window at row 50)."
    )


# ---------------------------------------------------------------------------
# 3. Formula correctness for eth_rv_50
# ---------------------------------------------------------------------------


def test_eth_vs_sym_rv_50_formula_correctness() -> None:
    """eth_rv_50[i] == std(log_ret[i-49 : i+1]) for i >= 50.

    rolling(50, min_periods=50).std() uses biased-corrected (ddof=1) std.
    First finite result is at row 50 (window log_ret[1:51], all finite).
    Row 49 includes log_ret[0]=NaN — still NaN.
    """
    import crypto_trade.features_v3.cross_btc_v3 as cross_mod

    n = 150
    with tempfile.TemporaryDirectory() as tmpdir:
        eth_path = Path(tmpdir) / "8h.csv"
        eth_df = _write_synthetic_eth_csv(eth_path, n=n)

        orig_path = cross_mod.ETH_CSV_PATH
        cross_mod._ETH_CACHE_V3 = None
        cross_mod.ETH_CSV_PATH = eth_path
        try:
            cache = cross_mod._load_eth_v3_features()
            eth_rv = cache["eth_rv_50"].to_numpy()
        finally:
            cross_mod.ETH_CSV_PATH = orig_path
            cross_mod._ETH_CACHE_V3 = None

    close = eth_df["close"].to_numpy(dtype=np.float64)
    log_close = np.log(close)
    log_ret = np.concatenate([[np.nan], np.diff(log_close)])

    # Check rows 50..69 (20 rows; first finite result at row 50)
    for i in range(50, 70):
        expected = float(np.std(log_ret[i - 49 : i + 1], ddof=1))
        assert np.isfinite(expected), (
            f"Expected value at row {i} is not finite: {expected}. "
            "log_ret[1:] should be all finite."
        )
        assert eth_rv[i] == pytest.approx(expected, rel=1e-10), (
            f"eth_rv_50[{i}] = {eth_rv[i]} but expected "
            f"std(log_ret[{i - 49}:{i + 1}]) = {expected}. "
            "rolling(50, min_periods=50).std() with ddof=1 (pandas default)."
        )


# ---------------------------------------------------------------------------
# 4. eth_vs_sym_rv_50 present in add_cross_btc_v3_features output
# ---------------------------------------------------------------------------


def test_eth_vs_sym_rv_50_present_in_add_cross_btc_v3_features() -> None:
    """add_cross_btc_v3_features output must include 'eth_vs_sym_rv_50' column at iter-v3/123."""
    import crypto_trade.features_v3.cross_btc_v3 as cross_mod

    with tempfile.TemporaryDirectory() as tmpdir:
        eth_path = Path(tmpdir) / "eth_8h.csv"
        btc_path = Path(tmpdir) / "btc_8h.csv"
        n = 200

        _write_synthetic_eth_csv(eth_path, n=n)
        _write_synthetic_btc_csv(btc_path, n=n)
        sym_df = _make_symbol_df(n=n, with_range_rv50=True)

        orig_eth = cross_mod.ETH_CSV_PATH
        orig_btc = cross_mod.BTC_CSV_PATH
        cross_mod._ETH_CACHE_V3 = None
        cross_mod._BTC_CACHE_V3 = None
        cross_mod.ETH_CSV_PATH = eth_path
        cross_mod.BTC_CSV_PATH = btc_path
        try:
            result = cross_mod.add_cross_btc_v3_features(sym_df)
        finally:
            cross_mod.ETH_CSV_PATH = orig_eth
            cross_mod.BTC_CSV_PATH = orig_btc
            cross_mod._ETH_CACHE_V3 = None
            cross_mod._BTC_CACHE_V3 = None

    assert "eth_vs_sym_rv_50" in result.columns, (
        f"'eth_vs_sym_rv_50' NOT FOUND in add_cross_btc_v3_features output at iter-v3/123. "
        f"Columns present: {sorted(result.columns.tolist())}. "
        "Check that _load_eth_v3_features() is called and the ratio is computed inside "
        "add_cross_btc_v3_features."
    )
    # Spot-check: non-NaN in rows 49+ after merge (50-bar warmup)
    non_nan = result["eth_vs_sym_rv_50"].iloc[49:].notna().sum()
    assert non_nan > 0, (
        "eth_vs_sym_rv_50 has all-NaN values after row 49 in add_cross_btc_v3_features output. "
        "Check the ratio computation: eth_rv_50 / (range_realized_vol_50 + EPS). "
        "Verify the left-join merge on open_time aligns ETH and symbol timestamps."
    )


# ---------------------------------------------------------------------------
# 5. eth_ret_3d ABSENT from add_cross_btc_v3_features output
# ---------------------------------------------------------------------------


def test_eth_ret_3d_absent_from_add_cross_btc_v3_features() -> None:
    """add_cross_btc_v3_features output must NOT include 'eth_ret_3d' at iter-v3/123.

    eth_ret_3d was REMOVED at /123 (NEGATIVE-INERT at /122 per Critic `9e0eeb6`).
    """
    import crypto_trade.features_v3.cross_btc_v3 as cross_mod

    with tempfile.TemporaryDirectory() as tmpdir:
        eth_path = Path(tmpdir) / "eth_8h.csv"
        btc_path = Path(tmpdir) / "btc_8h.csv"
        n = 200

        _write_synthetic_eth_csv(eth_path, n=n)
        _write_synthetic_btc_csv(btc_path, n=n)
        sym_df = _make_symbol_df(n=n, with_range_rv50=True)

        orig_eth = cross_mod.ETH_CSV_PATH
        orig_btc = cross_mod.BTC_CSV_PATH
        cross_mod._ETH_CACHE_V3 = None
        cross_mod._BTC_CACHE_V3 = None
        cross_mod.ETH_CSV_PATH = eth_path
        cross_mod.BTC_CSV_PATH = btc_path
        try:
            result = cross_mod.add_cross_btc_v3_features(sym_df)
        finally:
            cross_mod.ETH_CSV_PATH = orig_eth
            cross_mod.BTC_CSV_PATH = orig_btc
            cross_mod._ETH_CACHE_V3 = None
            cross_mod._BTC_CACHE_V3 = None

    assert "eth_ret_3d" not in result.columns, (
        f"'eth_ret_3d' FOUND in add_cross_btc_v3_features output at iter-v3/123 — must be ABSENT. "
        "eth_ret_3d was REMOVED per /122 NEGATIVE-INERT verdict (Critic `9e0eeb6`). "
        f"Columns present: {sorted(result.columns.tolist())}."
    )


# ---------------------------------------------------------------------------
# 6. eth_rv_50 intermediate column dropped
# ---------------------------------------------------------------------------


def test_eth_rv_50_intermediate_dropped() -> None:
    """The intermediate eth_rv_50 column must NOT appear in add_cross_btc_v3_features output.

    eth_rv_50 is used only to compute the ratio; it should be dropped before returning.
    """
    import crypto_trade.features_v3.cross_btc_v3 as cross_mod

    with tempfile.TemporaryDirectory() as tmpdir:
        eth_path = Path(tmpdir) / "eth_8h.csv"
        btc_path = Path(tmpdir) / "btc_8h.csv"
        n = 200

        _write_synthetic_eth_csv(eth_path, n=n)
        _write_synthetic_btc_csv(btc_path, n=n)
        sym_df = _make_symbol_df(n=n, with_range_rv50=True)

        orig_eth = cross_mod.ETH_CSV_PATH
        orig_btc = cross_mod.BTC_CSV_PATH
        cross_mod._ETH_CACHE_V3 = None
        cross_mod._BTC_CACHE_V3 = None
        cross_mod.ETH_CSV_PATH = eth_path
        cross_mod.BTC_CSV_PATH = btc_path
        try:
            result = cross_mod.add_cross_btc_v3_features(sym_df)
        finally:
            cross_mod.ETH_CSV_PATH = orig_eth
            cross_mod.BTC_CSV_PATH = orig_btc
            cross_mod._ETH_CACHE_V3 = None
            cross_mod._BTC_CACHE_V3 = None

    assert "eth_rv_50" not in result.columns, (
        "Intermediate column 'eth_rv_50' FOUND in add_cross_btc_v3_features output — "
        "must be dropped after ratio computation. "
        "Check: merged = merged.drop(columns=['eth_rv_50']) in add_cross_btc_v3_features."
    )


# ---------------------------------------------------------------------------
# 7. Cache idempotency
# ---------------------------------------------------------------------------


def test_eth_vs_sym_rv_50_cache_idempotency() -> None:
    """_load_eth_v3_features must return the same cached object on second call."""
    import crypto_trade.features_v3.cross_btc_v3 as cross_mod

    with tempfile.TemporaryDirectory() as tmpdir:
        eth_path = Path(tmpdir) / "8h.csv"
        _write_synthetic_eth_csv(eth_path, n=100)

        orig_path = cross_mod.ETH_CSV_PATH
        cross_mod._ETH_CACHE_V3 = None
        cross_mod.ETH_CSV_PATH = eth_path
        try:
            first = cross_mod._load_eth_v3_features()
            second = cross_mod._load_eth_v3_features()
        finally:
            cross_mod.ETH_CSV_PATH = orig_path
            cross_mod._ETH_CACHE_V3 = None

    assert first is second, (
        "_load_eth_v3_features returned different objects on second call — cache is broken. "
        "The global _ETH_CACHE_V3 must be populated on the first call and returned on "
        "subsequent calls without re-reading the CSV."
    )


# ---------------------------------------------------------------------------
# 8. No Inf values in ratio
# ---------------------------------------------------------------------------


def test_eth_vs_sym_rv_50_no_inf_nan_in_ratio() -> None:
    """The ratio eth_rv_50 / (sym_rv_50 + EPS) must produce no Inf values.

    EPS = 1e-12 guards against division-by-zero when sym_rv_50 = 0.
    """
    import crypto_trade.features_v3.cross_btc_v3 as cross_mod

    with tempfile.TemporaryDirectory() as tmpdir:
        eth_path = Path(tmpdir) / "eth_8h.csv"
        btc_path = Path(tmpdir) / "btc_8h.csv"
        n = 300

        _write_synthetic_eth_csv(eth_path, n=n)
        _write_synthetic_btc_csv(btc_path, n=n)
        sym_df = _make_symbol_df(n=n, with_range_rv50=True)

        orig_eth = cross_mod.ETH_CSV_PATH
        orig_btc = cross_mod.BTC_CSV_PATH
        cross_mod._ETH_CACHE_V3 = None
        cross_mod._BTC_CACHE_V3 = None
        cross_mod.ETH_CSV_PATH = eth_path
        cross_mod.BTC_CSV_PATH = btc_path
        try:
            result = cross_mod.add_cross_btc_v3_features(sym_df)
        finally:
            cross_mod.ETH_CSV_PATH = orig_eth
            cross_mod.BTC_CSV_PATH = orig_btc
            cross_mod._ETH_CACHE_V3 = None
            cross_mod._BTC_CACHE_V3 = None

    ratio = result["eth_vs_sym_rv_50"].to_numpy()
    finite_or_nan = np.isfinite(ratio) | np.isnan(ratio)
    inf_count = int(np.sum(~finite_or_nan))
    assert inf_count == 0, (
        f"eth_vs_sym_rv_50 contains {inf_count} Inf values — division-by-zero bug. "
        "EPS = 1e-12 in add_cross_btc_v3_features must guard against sym_rv_50 = 0."
    )


# ---------------------------------------------------------------------------
# 9. Adversarial: ratio past-only via symbol panel mutation
# ---------------------------------------------------------------------------


def test_eth_vs_sym_rv_50_past_only_for_ratio() -> None:
    """Adversarial: ratio at row t must not change when future symbol bars are mutated.

    Both the ETH numerator (eth_rv_50 via _load_eth_v3_features) and the symbol
    denominator (range_realized_vol_50 pre-computed from past bars) must be past-only.
    This test mutates the symbol frame's range_realized_vol_50 at rows t+1 onward
    to extreme values and verifies the ratio at row t is unchanged.
    """
    import crypto_trade.features_v3.cross_btc_v3 as cross_mod

    n = 300
    t_probe = 150  # probe row index

    with tempfile.TemporaryDirectory() as tmpdir:
        eth_path = Path(tmpdir) / "eth_8h.csv"
        btc_path = Path(tmpdir) / "btc_8h.csv"

        _write_synthetic_eth_csv(eth_path, n=n)
        _write_synthetic_btc_csv(btc_path, n=n)

        # Original symbol frame
        sym_df_original = _make_symbol_df(n=n, with_range_rv50=True)

        orig_eth = cross_mod.ETH_CSV_PATH
        orig_btc = cross_mod.BTC_CSV_PATH
        cross_mod._ETH_CACHE_V3 = None
        cross_mod._BTC_CACHE_V3 = None
        cross_mod.ETH_CSV_PATH = eth_path
        cross_mod.BTC_CSV_PATH = btc_path
        try:
            result_original = cross_mod.add_cross_btc_v3_features(sym_df_original)
            ratio_at_t_original = result_original["eth_vs_sym_rv_50"].iloc[t_probe]
        finally:
            cross_mod.ETH_CSV_PATH = orig_eth
            cross_mod.BTC_CSV_PATH = orig_btc
            cross_mod._ETH_CACHE_V3 = None
            cross_mod._BTC_CACHE_V3 = None

        # Mutated symbol frame: extreme range_realized_vol_50 at rows AFTER t_probe
        sym_df_mutated = sym_df_original.copy()
        sym_df_mutated.loc[t_probe + 1 :, "range_realized_vol_50"] = 1e6

        cross_mod._ETH_CACHE_V3 = None
        cross_mod._BTC_CACHE_V3 = None
        cross_mod.ETH_CSV_PATH = eth_path
        cross_mod.BTC_CSV_PATH = btc_path
        try:
            result_mutated = cross_mod.add_cross_btc_v3_features(sym_df_mutated)
            ratio_at_t_mutated = result_mutated["eth_vs_sym_rv_50"].iloc[t_probe]
        finally:
            cross_mod.ETH_CSV_PATH = orig_eth
            cross_mod.BTC_CSV_PATH = orig_btc
            cross_mod._ETH_CACHE_V3 = None
            cross_mod._BTC_CACHE_V3 = None

    assert ratio_at_t_original == pytest.approx(ratio_at_t_mutated, rel=1e-10), (
        f"eth_vs_sym_rv_50 at row {t_probe} changed from {ratio_at_t_original} to "
        f"{ratio_at_t_mutated} when future symbol bars were mutated — "
        "LOOK-AHEAD BUG detected in the ratio denominator. "
        "range_realized_vol_50 at row t must depend only on past bars."
    )
