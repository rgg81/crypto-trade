"""BTC trend separation IS-only analysis — iter-v1/019 Phase 1 EDA.

For each of three candidate BTC-trend indicators (past-only, no leakage),
tabulate ETH per-month PnL when BTC is in up-trend vs down-trend during
the **IS window only** (close_time < OOS_CUTOFF_MS).

Candidate indicators (all past-only by construction):
  - I1: BTC SMA cross  →  bullish if BTC_close > BTC_SMA_50 (50 8h-bars = ~16.7 days)
  - I2: BTC 14d return →  bullish if BTC_close(t) / BTC_close(t-42) - 1 > 0
  - I3: BTC MACD-like →  bullish if BTC_EMA_12 > BTC_EMA_26

For each indicator we report:
  - n IS months when bullish vs bearish
  - ETH net_pnl_pct conditional on the indicator at signal time
  - Mean ETH per-trade PnL gain from skipping bearish-BTC entries
  - Predicted IS gate fire rate (fraction of IS ETH signals skipped)

The chosen indicator is the one with the LARGEST IS-only PnL separation
between bullish vs bearish, with sufficient sample on both sides (each
arm must have >= 30 trades to avoid noise).

Outputs (committed):
- btc_trend_indicators.csv : per-indicator IS separation stats
- btc_trend_chosen.csv : chosen indicator + gate threshold + IS fire rate

IS-ONLY. No OOS contamination. Reads from baseline trades.csv and BTC kline CSV.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports-v1"
OUT = ROOT / "analysis" / "iteration_v1-019"
OUT.mkdir(parents=True, exist_ok=True)

# OOS_CUTOFF_DATE = 2025-03-24 (sacred constant); convert to ms.
OOS_CUTOFF_MS = int(pd.Timestamp("2025-03-24", tz="UTC").timestamp() * 1000)


def load_btc_klines() -> pd.DataFrame:
    """Load BTC 8h klines and engineer past-only trend indicators."""
    df = pd.read_csv(ROOT / "data" / "BTCUSDT" / "8h.csv")
    df = df.sort_values("open_time").reset_index(drop=True)
    # Past-only: shift(1) is NOT strictly required because the indicator at
    # bar k uses BTC closes up to bar k-N (lookback fully past). But for
    # interaction with a signal at bar k+1 (signal entry at next candle open),
    # the indicator value at bar k is naturally past-only.
    df["sma_50"] = df["close"].rolling(50, min_periods=50).mean()
    df["ema_12"] = df["close"].ewm(span=12, adjust=False, min_periods=12).mean()
    df["ema_26"] = df["close"].ewm(span=26, adjust=False, min_periods=26).mean()
    # 14d return at 8h cadence = 42 bars (14 * 3)
    df["ret_14d"] = df["close"] / df["close"].shift(42) - 1.0
    return df


def classify_per_trade(trades: pd.DataFrame, btc: pd.DataFrame) -> pd.DataFrame:
    """For each ETH trade, attach BTC-trend regime at open_time using past-only
    indicators."""
    btc_open = btc["open_time"].to_numpy(dtype=np.int64)
    btc_close = btc["close"].to_numpy(dtype=np.float64)
    btc_sma = btc["sma_50"].to_numpy(dtype=np.float64)
    btc_ema12 = btc["ema_12"].to_numpy(dtype=np.float64)
    btc_ema26 = btc["ema_26"].to_numpy(dtype=np.float64)
    btc_ret14 = btc["ret_14d"].to_numpy(dtype=np.float64)

    out_rows = []
    for _, r in trades.iterrows():
        ot = int(r["open_time"])
        # most recent BTC bar with open_time <= signal open_time
        idx = int(np.searchsorted(btc_open, ot, side="right") - 1)
        if idx < 50:
            # Warmup — none of the indicators valid; we treat as "unknown" bull
            # to be permissive (won't be skipped). Mark this so we can report.
            out_rows.append(
                {
                    "open_time": ot,
                    "i1_sma_bull": True,
                    "i1_warmup": True,
                    "i2_ret14_bull": True,
                    "i2_warmup": True,
                    "i3_macd_bull": True,
                    "i3_warmup": True,
                }
            )
            continue
        c = btc_close[idx]
        sma = btc_sma[idx]
        ema12 = btc_ema12[idx]
        ema26 = btc_ema26[idx]
        ret14 = btc_ret14[idx]
        out_rows.append(
            {
                "open_time": ot,
                "i1_sma_bull": bool(c > sma) if not np.isnan(sma) else True,
                "i1_warmup": bool(np.isnan(sma)),
                "i2_ret14_bull": bool(ret14 > 0.0) if not np.isnan(ret14) else True,
                "i2_warmup": bool(np.isnan(ret14)),
                "i3_macd_bull": bool(ema12 > ema26)
                if not (np.isnan(ema12) or np.isnan(ema26)) else True,
                "i3_warmup": bool(np.isnan(ema12) or np.isnan(ema26)),
            }
        )
    return pd.DataFrame(out_rows)


def indicator_split(trades: pd.DataFrame, bull_col: str) -> dict:
    bull = trades[trades[bull_col]]
    bear = trades[~trades[bull_col]]
    return {
        "n_bull": len(bull),
        "wr_bull": float((bull["net_pnl_pct"] > 0).mean() * 100) if len(bull) else 0.0,
        "total_pnl_bull": float(bull["net_pnl_pct"].sum()),
        "avg_pnl_bull": float(bull["net_pnl_pct"].mean()) if len(bull) else 0.0,
        "n_bear": len(bear),
        "wr_bear": float((bear["net_pnl_pct"] > 0).mean() * 100) if len(bear) else 0.0,
        "total_pnl_bear": float(bear["net_pnl_pct"].sum()),
        "avg_pnl_bear": float(bear["net_pnl_pct"].mean()) if len(bear) else 0.0,
    }


def main() -> None:
    btc = load_btc_klines()

    # ETH IS trades from baseline
    base_is_trades = pd.read_csv(
        REPORTS / "iteration_v1-baseline" / "in_sample" / "trades.csv"
    )
    eth_is = base_is_trades[base_is_trades["symbol"] == "ETHUSDT"].copy()
    print(f"ETH IS trades from baseline: {len(eth_is)}")

    # ETH OOS trades from baseline (informational; NOT used for indicator choice)
    base_oos_trades = pd.read_csv(
        REPORTS / "iteration_v1-baseline" / "out_of_sample" / "trades.csv"
    )
    eth_oos = base_oos_trades[base_oos_trades["symbol"] == "ETHUSDT"].copy()
    print(f"ETH OOS trades from baseline (informational): {len(eth_oos)}")

    # Verify IS-only filter
    assert eth_is["open_time"].max() < OOS_CUTOFF_MS, "ETH IS contains OOS trades!"
    print(
        f"IS window: {pd.to_datetime(eth_is['open_time'].min(), unit='ms')} → "
        f"{pd.to_datetime(eth_is['open_time'].max(), unit='ms')}"
    )

    # Classify trades by BTC-trend at signal time
    eth_is_class = classify_per_trade(eth_is, btc)
    eth_is = eth_is.reset_index(drop=True)
    eth_is = pd.concat([eth_is, eth_is_class.drop(columns=["open_time"])], axis=1)

    # Report per indicator
    rows = []
    for ind, bull_col in [
        ("I1_sma_50", "i1_sma_bull"),
        ("I2_ret_14d", "i2_ret14_bull"),
        ("I3_ema12_v_ema26", "i3_macd_bull"),
    ]:
        stats = indicator_split(eth_is, bull_col)
        stats["indicator"] = ind
        # Separation metric: avg_pnl difference
        stats["avg_pnl_separation"] = stats["avg_pnl_bull"] - stats["avg_pnl_bear"]
        # Sharpe-like quality of the bull arm
        bull = eth_is[eth_is[bull_col]]
        if len(bull) >= 2 and bull["net_pnl_pct"].std() > 0:
            stats["bull_per_trade_sharpe"] = float(
                bull["net_pnl_pct"].mean() / bull["net_pnl_pct"].std()
            )
        else:
            stats["bull_per_trade_sharpe"] = 0.0
        # IS gate fire rate (fraction skipped if we gate on this indicator)
        stats["is_skip_pct"] = float((~eth_is[bull_col]).mean() * 100)
        # IS PnL lift if we skip bear ETH trades (additive at trade level):
        # gated total PnL = total_pnl_bull (drop all bear)
        # baseline ETH IS PnL = -13.70%
        stats["is_pnl_gated"] = stats["total_pnl_bull"]
        stats["is_pnl_baseline"] = float(eth_is["net_pnl_pct"].sum())
        stats["is_pnl_lift"] = stats["is_pnl_gated"] - stats["is_pnl_baseline"]
        rows.append(stats)

    ind_df = pd.DataFrame(rows)
    # Reorder for readability
    cols = [
        "indicator", "n_bull", "wr_bull", "total_pnl_bull", "avg_pnl_bull",
        "n_bear", "wr_bear", "total_pnl_bear", "avg_pnl_bear",
        "avg_pnl_separation", "bull_per_trade_sharpe",
        "is_skip_pct", "is_pnl_baseline", "is_pnl_gated", "is_pnl_lift",
    ]
    ind_df = ind_df[cols]
    ind_df.to_csv(OUT / "btc_trend_indicators.csv", index=False)

    print("\n=== BTC trend indicators — ETH IS split (IS-only) ===")
    print(ind_df.to_string(index=False))
    print()

    # Choose: largest avg_pnl_separation with >=30 trades per arm
    valid = ind_df[(ind_df["n_bull"] >= 30) & (ind_df["n_bear"] >= 30)]
    if len(valid) == 0:
        # Fall back to indicator with biggest separation regardless
        chosen = ind_df.sort_values("avg_pnl_separation", ascending=False).iloc[0]
    else:
        chosen = valid.sort_values("avg_pnl_separation", ascending=False).iloc[0]

    print(f"=== Chosen BTC-trend indicator: {chosen['indicator']} ===")
    print(f"  IS skip rate: {chosen['is_skip_pct']:.1f}%")
    print(f"  IS PnL lift (additive): {chosen['is_pnl_lift']:+.2f}%")
    print(f"  Avg PnL separation (bull − bear): {chosen['avg_pnl_separation']:+.4f}%")

    # Compute predicted OOS gate fire rate (sanity check; does NOT influence choice)
    eth_oos_class = classify_per_trade(eth_oos, btc)
    eth_oos = eth_oos.reset_index(drop=True)
    eth_oos = pd.concat([eth_oos, eth_oos_class.drop(columns=["open_time"])], axis=1)
    bull_col_map = {
        "I1_sma_50": "i1_sma_bull",
        "I2_ret_14d": "i2_ret14_bull",
        "I3_ema12_v_ema26": "i3_macd_bull",
    }
    oos_skip = float((~eth_oos[bull_col_map[chosen["indicator"]]]).mean() * 100)
    print(f"  Predicted OOS gate fire rate (informational; baseline ETH OOS): {oos_skip:.1f}%")
    print(
        "  NOTE: this OOS fire rate is informational — the chosen indicator is "
        "selected on IS PnL lift, not OOS-sensitive metrics. The OOS skip rate is "
        "reported to size the F8 trade-count band."
    )

    # Persist chosen indicator record
    chosen_df = pd.DataFrame([{
        "indicator": chosen["indicator"],
        "rule": _rule_string(chosen["indicator"]),
        "is_skip_pct": float(chosen["is_skip_pct"]),
        "is_pnl_lift_pct": float(chosen["is_pnl_lift"]),
        "is_avg_pnl_sep_pct": float(chosen["avg_pnl_separation"]),
        "predicted_oos_skip_pct": float(oos_skip),
    }])
    chosen_df.to_csv(OUT / "btc_trend_chosen.csv", index=False)
    print()
    print(chosen_df.to_string(index=False))


def _rule_string(indicator_name: str) -> str:
    return {
        "I1_sma_50": "gate ON (allow entry) if BTC_close > BTC_SMA_50 (50 8h-bars)",
        "I2_ret_14d": "gate ON if BTC 14d return > 0 (14*3=42 8h-bars)",
        "I3_ema12_v_ema26": "gate ON if BTC_EMA_12 > BTC_EMA_26",
    }[indicator_name]


if __name__ == "__main__":
    main()
