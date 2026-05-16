"""Validation EDA — does primitive 9 universal regime gate (TRX) hurt TRX LONG?

Key question: if primitive 9 enable_regime_gate=True + regime_gate_symbols=("TRXUSDT",)
fires in stressed regimes (BTC drawdown > 20% OR BTC vol z-score > 1.5), does it
PRESERVE TRX LONG edge or HURT it?

EDA stratifies TRX trades by:
1. Direction (LONG vs SHORT)
2. BTC regime at trade open_time (stressed vs healthy by IS-90/95-pct thresholds)

Regime classification:
- Stressed: BTC 30d drawdown > 20% OR BTC 14d log-return std z-score > 1.5
- Healthy:  not stressed

Outputs:
- regime_validation.csv (per-trade regime tag + per-direction-per-regime breakdown)
- (extends synthesis.md with regime stratification table)

Reads BTC daily close from data/BTCUSDT/8h.csv to compute regime at each trade open_time.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/home/roberto/crypto-trade/.worktrees/quant-research")
ANALYSIS_DIR = REPO / "analysis" / "iteration_v3-048"

ITER045_IS = REPO / "reports-v3" / "iteration_v3-045" / "in_sample" / "trades.csv"
ITER045_OOS = REPO / "reports-v3" / "iteration_v3-045" / "out_of_sample" / "trades.csv"
BTC_CSV = REPO / "data" / "BTCUSDT" / "8h.csv"

DD_LOOKBACK = 90  # bars (30 days at 8h)
VOL_LOOKBACK = 90
DD_THRESHOLD_PCT = 20.0
VOL_ZSCORE_THRESHOLD = 1.5


def build_btc_regime_lookup() -> pd.DataFrame:
    """Build per-bar BTC regime classification (stressed vs healthy).
    Past-only via shift(1).
    """
    df = pd.read_csv(BTC_CSV, usecols=["open_time", "close"])
    df = df.sort_values("open_time").reset_index(drop=True)
    df["close"] = df["close"].astype(float)

    # Drawdown 30d
    close_shifted = df["close"].shift(1)
    rolling_max = close_shifted.rolling(window=DD_LOOKBACK, min_periods=1).max()
    df["drawdown_pct"] = (close_shifted - rolling_max) / rolling_max * 100.0

    # Vol z-score 30d
    df["log_ret"] = np.log(df["close"] / df["close"].shift(1))
    logret_shifted = df["log_ret"].shift(1)
    rolling_std = logret_shifted.rolling(window=VOL_LOOKBACK, min_periods=2).std()
    expanding_mean = rolling_std.expanding(min_periods=10).mean()
    expanding_std = rolling_std.expanding(min_periods=10).std().replace(0.0, np.nan)
    df["vol_zscore"] = (rolling_std - expanding_mean) / expanding_std

    # Regime tag
    df["dd_fires"] = df["drawdown_pct"].abs() > DD_THRESHOLD_PCT
    df["vol_fires"] = df["vol_zscore"].abs() > VOL_ZSCORE_THRESHOLD
    df["regime_stressed"] = df["dd_fires"] | df["vol_fires"]

    return df[["open_time", "drawdown_pct", "vol_zscore", "regime_stressed"]]


def tag_trades_with_regime(trades_path: Path, regime_lookup: pd.DataFrame) -> pd.DataFrame:
    """For each trade, find the regime classification at the trade open_time
    (using the most recent BTC bar with open_time STRICTLY LESS THAN trade open_time)."""
    trades = pd.read_csv(trades_path)

    # Sort lookup
    btc_times = regime_lookup["open_time"].to_numpy(dtype=np.int64)
    regime_stressed_arr = regime_lookup["regime_stressed"].to_numpy(dtype=bool)
    dd_arr = regime_lookup["drawdown_pct"].to_numpy(dtype=np.float64)
    vz_arr = regime_lookup["vol_zscore"].to_numpy(dtype=np.float64)

    regime_at_trade = []
    dd_at_trade = []
    vz_at_trade = []
    for ot in trades["open_time"]:
        idx = int(np.searchsorted(btc_times, int(ot), side="left")) - 1
        if idx < 0:
            regime_at_trade.append(False)
            dd_at_trade.append(np.nan)
            vz_at_trade.append(np.nan)
        else:
            regime_at_trade.append(bool(regime_stressed_arr[idx]))
            dd_at_trade.append(float(dd_arr[idx]))
            vz_at_trade.append(float(vz_arr[idx]))

    trades["regime_stressed"] = regime_at_trade
    trades["btc_dd_pct_at_trade"] = dd_at_trade
    trades["btc_vol_z_at_trade"] = vz_at_trade
    trades["dir_label"] = trades["direction"].map({1: "LONG", -1: "SHORT"})
    return trades


def trx_per_direction_per_regime(trades: pd.DataFrame, label: str) -> pd.DataFrame:
    """TRX trades stratified by direction × regime."""
    sub = trades[trades["symbol"] == "TRXUSDT"].copy()
    rows = []
    for d_label in ("LONG", "SHORT"):
        for regime in (False, True):
            d = sub[(sub["dir_label"] == d_label) & (sub["regime_stressed"] == regime)]
            n = len(d)
            regime_label = "STRESSED" if regime else "HEALTHY"
            rows.append(
                {
                    "label": label,
                    "axis": "TRX_dir_regime",
                    "direction": d_label,
                    "regime": regime_label,
                    "n_trades": n,
                    "wins": int((d["net_pnl_pct"] > 0).sum()),
                    "win_rate_pct": (
                        round((d["net_pnl_pct"] > 0).mean() * 100, 2) if n else 0.0
                    ),
                    "net_pnl_pct_sum": round(d["net_pnl_pct"].sum(), 4),
                    "weighted_pnl_sum": round(d["weighted_pnl"].sum(), 4),
                    "avg_pnl_pct": round(d["net_pnl_pct"].mean(), 4) if n else 0.0,
                }
            )
    return pd.DataFrame(rows)


def all_symbols_regime_distribution(trades: pd.DataFrame, label: str) -> pd.DataFrame:
    """All symbols × regime distribution — sanity check on regime fire rate."""
    rows = []
    for sym in ("BCHUSDT", "TRXUSDT", "LDOUSDT", "ALGOUSDT"):
        sub = trades[trades["symbol"] == sym]
        n_total = len(sub)
        n_stressed = int(sub["regime_stressed"].sum())
        rows.append(
            {
                "label": label,
                "axis": "regime_fire_rate",
                "symbol": sym,
                "n_total": n_total,
                "n_stressed": n_stressed,
                "stressed_fire_rate_pct": (
                    round(n_stressed / n_total * 100, 2) if n_total else 0.0
                ),
            }
        )
    return pd.DataFrame(rows)


def counterfactual_regime_block_trx_only(trades: pd.DataFrame, label: str) -> pd.DataFrame:
    """Counterfactual: bundle PnL with TRX trades blocked in stressed regimes (universal,
    both directions). This is what primitive 9 does naively.
    """
    rows = []
    bundle_total = trades["weighted_pnl"].sum()
    trx_blocked = trades[
        (trades["symbol"] == "TRXUSDT") & (trades["regime_stressed"])
    ]
    trx_blocked_weighted = trx_blocked["weighted_pnl"].sum()
    rows.append(
        {
            "label": label,
            "axis": "cf_regime_block_TRX_universal",
            "metric": "bundle_total_weighted_pnl",
            "value": round(bundle_total, 4),
        }
    )
    rows.append(
        {
            "label": label,
            "axis": "cf_regime_block_TRX_universal",
            "metric": "TRX_stressed_blocked_weighted_pnl",
            "value": round(trx_blocked_weighted, 4),
        }
    )
    rows.append(
        {
            "label": label,
            "axis": "cf_regime_block_TRX_universal",
            "metric": "TRX_stressed_blocked_n_trades",
            "value": len(trx_blocked),
        }
    )
    rows.append(
        {
            "label": label,
            "axis": "cf_regime_block_TRX_universal",
            "metric": "delta_from_blocking_TRX_stressed_universal",
            "value": round(-trx_blocked_weighted, 4),
        }
    )

    # Sub-stratification: how much of trx_blocked is LONG vs SHORT?
    trx_long_blocked = trx_blocked[trx_blocked["direction"] == 1]
    trx_short_blocked = trx_blocked[trx_blocked["direction"] == -1]
    rows.append(
        {
            "label": label,
            "axis": "cf_regime_block_TRX_universal",
            "metric": "TRX_LONG_stressed_blocked_n_trades",
            "value": len(trx_long_blocked),
        }
    )
    rows.append(
        {
            "label": label,
            "axis": "cf_regime_block_TRX_universal",
            "metric": "TRX_LONG_stressed_blocked_weighted_pnl",
            "value": round(trx_long_blocked["weighted_pnl"].sum(), 4),
        }
    )
    rows.append(
        {
            "label": label,
            "axis": "cf_regime_block_TRX_universal",
            "metric": "TRX_SHORT_stressed_blocked_n_trades",
            "value": len(trx_short_blocked),
        }
    )
    rows.append(
        {
            "label": label,
            "axis": "cf_regime_block_TRX_universal",
            "metric": "TRX_SHORT_stressed_blocked_weighted_pnl",
            "value": round(trx_short_blocked["weighted_pnl"].sum(), 4),
        }
    )
    return pd.DataFrame(rows)


def main() -> int:
    print("=" * 78)
    print("Regime gate validation — primitive 9 TRX-universal vs direction-aware")
    print("=" * 78)

    if not BTC_CSV.exists():
        print(f"ERROR: {BTC_CSV} does not exist")
        return 1

    print(f"\nBuilding BTC regime lookup (DD>{DD_THRESHOLD_PCT}% OR |vol_z|>{VOL_ZSCORE_THRESHOLD})...")
    regime_lookup = build_btc_regime_lookup()
    n_total_btc = len(regime_lookup)
    n_stressed_btc = int(regime_lookup["regime_stressed"].sum())
    print(
        f"  Total BTC bars: {n_total_btc}; stressed: {n_stressed_btc} "
        f"({round(n_stressed_btc / n_total_btc * 100, 2)}%)"
    )

    print("\n[1] Tagging iter-v3/045 IS trades with regime...")
    is_trades = tag_trades_with_regime(ITER045_IS, regime_lookup)
    print(
        f"  IS trades tagged: {len(is_trades)}; "
        f"stressed regime: {int(is_trades['regime_stressed'].sum())} "
        f"({round(is_trades['regime_stressed'].mean() * 100, 2)}%)"
    )

    print("\n[2] Tagging iter-v3/045 OOS trades with regime...")
    oos_trades = tag_trades_with_regime(ITER045_OOS, regime_lookup)
    print(
        f"  OOS trades tagged: {len(oos_trades)}; "
        f"stressed regime: {int(oos_trades['regime_stressed'].sum())} "
        f"({round(oos_trades['regime_stressed'].mean() * 100, 2)}%)"
    )

    print("\n[3] All-symbols regime fire rate (IS):")
    all_sym_is = all_symbols_regime_distribution(is_trades, "iter-v3/045 IS")
    print(all_sym_is.to_string(index=False))

    print("\n[3b] All-symbols regime fire rate (OOS):")
    all_sym_oos = all_symbols_regime_distribution(oos_trades, "iter-v3/045 OOS")
    print(all_sym_oos.to_string(index=False))

    print("\n[4] TRX direction × regime (IS) — does P9 universal hurt TRX LONG?")
    trx_dir_regime_is = trx_per_direction_per_regime(is_trades, "iter-v3/045 IS")
    print(trx_dir_regime_is.to_string(index=False))

    print("\n[4b] TRX direction × regime (OOS) — does P9 universal hurt TRX OOS?")
    trx_dir_regime_oos = trx_per_direction_per_regime(oos_trades, "iter-v3/045 OOS")
    print(trx_dir_regime_oos.to_string(index=False))

    print("\n[5] Counterfactual — primitive 9 universal TRX regime block (IS):")
    cf_is = counterfactual_regime_block_trx_only(is_trades, "iter-v3/045 IS")
    print(cf_is.to_string(index=False))

    print("\n[5b] Counterfactual — primitive 9 universal TRX regime block (OOS):")
    cf_oos = counterfactual_regime_block_trx_only(oos_trades, "iter-v3/045 OOS")
    print(cf_oos.to_string(index=False))

    # Persist all tables
    all_tables = {
        "1_btc_regime_summary": pd.DataFrame(
            [
                {
                    "metric": "n_total_btc_bars",
                    "value": n_total_btc,
                },
                {
                    "metric": "n_stressed_btc_bars",
                    "value": n_stressed_btc,
                },
                {
                    "metric": "stressed_fire_rate_pct",
                    "value": round(n_stressed_btc / n_total_btc * 100, 4),
                },
                {
                    "metric": "DD_threshold_pct",
                    "value": DD_THRESHOLD_PCT,
                },
                {
                    "metric": "vol_zscore_threshold",
                    "value": VOL_ZSCORE_THRESHOLD,
                },
            ]
        ),
        "3_all_symbols_regime_fire_rate_is": all_sym_is,
        "3b_all_symbols_regime_fire_rate_oos": all_sym_oos,
        "4_trx_direction_regime_is": trx_dir_regime_is,
        "4b_trx_direction_regime_oos": trx_dir_regime_oos,
        "5_counterfactual_p9_universal_is": cf_is,
        "5b_counterfactual_p9_universal_oos": cf_oos,
    }

    out_csv = ANALYSIS_DIR / "regime_validation.csv"
    with out_csv.open("w") as f:
        for name, df in all_tables.items():
            f.write(f"# {name}\n")
            df.to_csv(f, index=False)
            f.write("\n")
    print(f"\nWrote: {out_csv}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
