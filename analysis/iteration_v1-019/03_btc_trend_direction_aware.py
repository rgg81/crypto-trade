"""Direction-aware BTC-trend gate IS-only analysis — iter-v1/019 Phase 1 EDA.

Script 02 showed that a SYMMETRIC BTC-trend gate (skip ETH entries when BTC
is in downtrend) does NOT cleanly separate ETH-good from ETH-bad trades at IS:
all three indicators flagged "bear-BTC ETH trades are LESS BAD than bull-BTC".

Reframe the hypothesis: a DIRECTION-AWARE gate that kills **counter-trend
ETH trades** at large BTC moves (v2/019's pattern). The IS evidence we need is:

  For each of 3 indicators:
    - ETH long trades  +  BTC up-trend  →  expected POSITIVE (trend alignment)
    - ETH long trades  +  BTC down-trend → expected NEGATIVE (counter-trend; kill)
    - ETH short trades +  BTC down-trend → expected POSITIVE (trend alignment)
    - ETH short trades +  BTC up-trend  →  expected NEGATIVE (counter-trend; kill)

Plus a strength variant — only kill at LARGE BTC moves (|BTC 14d ret| > X%) to
avoid over-skipping (cf. v2/019 uses ±20% threshold; for v1's ETH-only with
default ATR×2.0/1.0 SL on 8h cadence we may need a lower threshold).

Outputs (committed):
- btc_trend_direction_aware.csv : 4 cells × 3 indicators IS split
- btc_trend_direction_aware_thresholds.csv : same but with threshold sweep
- btc_trend_chosen_gate.csv : recommended gate spec for /019 brief Section 3
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports-v1"
OUT = ROOT / "analysis" / "iteration_v1-019"
OUT.mkdir(parents=True, exist_ok=True)

OOS_CUTOFF_MS = int(pd.Timestamp("2025-03-24", tz="UTC").timestamp() * 1000)


def load_btc_klines() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data" / "BTCUSDT" / "8h.csv")
    df = df.sort_values("open_time").reset_index(drop=True)
    df["sma_50"] = df["close"].rolling(50, min_periods=50).mean()
    df["ema_12"] = df["close"].ewm(span=12, adjust=False, min_periods=12).mean()
    df["ema_26"] = df["close"].ewm(span=26, adjust=False, min_periods=26).mean()
    df["ret_14d"] = df["close"] / df["close"].shift(42) - 1.0
    return df


def attach_btc_features(trades: pd.DataFrame, btc: pd.DataFrame) -> pd.DataFrame:
    out = trades.reset_index(drop=True).copy()
    btc_open = btc["open_time"].to_numpy(dtype=np.int64)
    rec = []
    for _, r in out.iterrows():
        ot = int(r["open_time"])
        idx = int(np.searchsorted(btc_open, ot, side="right") - 1)
        if idx < 50:
            rec.append({"sma_bull": True, "ret14": 0.0, "macd_bull": True, "warmup": True})
            continue
        sma = float(btc["sma_50"].iloc[idx])
        ret14 = float(btc["ret_14d"].iloc[idx])
        ema12 = float(btc["ema_12"].iloc[idx])
        ema26 = float(btc["ema_26"].iloc[idx])
        close = float(btc["close"].iloc[idx])
        rec.append(
            {
                "sma_bull": close > sma if not np.isnan(sma) else True,
                "ret14": ret14 if not np.isnan(ret14) else 0.0,
                "macd_bull": (ema12 > ema26)
                if not (np.isnan(ema12) or np.isnan(ema26)) else True,
                "warmup": False,
            }
        )
    return pd.concat([out, pd.DataFrame(rec)], axis=1)


def direction_aware_split(trades: pd.DataFrame, bull_col: str) -> pd.DataFrame:
    """Split into 4 cells: (direction, btc_bull) → stats."""
    rows = []
    for direction in (1, -1):
        for btc_bull in (True, False):
            sub = trades[(trades["direction"] == direction) & (trades[bull_col] == btc_bull)]
            rows.append(
                {
                    "direction": "long" if direction == 1 else "short",
                    "btc_bull": btc_bull,
                    "label": f"{'long' if direction == 1 else 'short'}_btc{'+' if btc_bull else '-'}",
                    "n": len(sub),
                    "wr_pct": float((sub["net_pnl_pct"] > 0).mean() * 100) if len(sub) else 0.0,
                    "total_pnl_pct": float(sub["net_pnl_pct"].sum()),
                    "avg_pnl_pct": float(sub["net_pnl_pct"].mean()) if len(sub) else 0.0,
                }
            )
    return pd.DataFrame(rows)


def gate_pnl_sim(trades: pd.DataFrame, kill_mask: pd.Series) -> dict:
    """Simulate the gate: trades for which kill_mask=True are removed.

    Returns net_pnl_pct gated, lift vs baseline, skip rate.
    """
    baseline = float(trades["net_pnl_pct"].sum())
    survived = trades[~kill_mask]
    gated = float(survived["net_pnl_pct"].sum())
    return {
        "n_total": len(trades),
        "n_skipped": int(kill_mask.sum()),
        "skip_pct": float(kill_mask.mean() * 100),
        "baseline_pnl_pct": baseline,
        "gated_pnl_pct": gated,
        "lift_pct": gated - baseline,
    }


def main() -> None:
    btc = load_btc_klines()
    base_is_trades = pd.read_csv(REPORTS / "iteration_v1-baseline" / "in_sample" / "trades.csv")
    eth_is = base_is_trades[base_is_trades["symbol"] == "ETHUSDT"].copy()
    eth_is = attach_btc_features(eth_is, btc)
    assert eth_is["open_time"].max() < OOS_CUTOFF_MS

    print(f"ETH IS trades: {len(eth_is)}")
    print(f"  longs: {(eth_is['direction'] == 1).sum()}")
    print(f"  shorts: {(eth_is['direction'] == -1).sum()}")

    # --- 4-cell split per indicator (no threshold gate yet) ---
    out_rows = []
    for ind, bull_col in [
        ("I1_sma_50", "sma_bull"),
        ("I3_ema12_v_ema26", "macd_bull"),
    ]:
        df = direction_aware_split(eth_is, bull_col)
        df["indicator"] = ind
        out_rows.append(df)
    # I2 is threshold-based — handle separately
    for ind_label, threshold in [
        ("I2_ret_14d_>0", 0.0),
        ("I2_ret_14d_>5%", 0.05),
        ("I2_ret_14d_>10%", 0.10),
        ("I2_ret_14d_>20%", 0.20),
    ]:
        eth_is[f"ret14_bull_{ind_label}"] = eth_is["ret14"] > threshold
        df = direction_aware_split(eth_is, f"ret14_bull_{ind_label}")
        df["indicator"] = ind_label
        out_rows.append(df)
    da = pd.concat(out_rows, ignore_index=True)
    da = da[["indicator", "direction", "btc_bull", "label",
             "n", "wr_pct", "total_pnl_pct", "avg_pnl_pct"]]
    da.to_csv(OUT / "btc_trend_direction_aware.csv", index=False)

    print("\n=== Direction-aware 4-cell split per indicator (IS-only) ===")
    for ind in da["indicator"].unique():
        print(f"\n--- {ind} ---")
        sub = da[da["indicator"] == ind]
        print(sub.to_string(index=False))

    # --- Gate simulation: kill counter-trend ETH trades ---
    # Counter-trend definitions:
    #   - long-counter-trend: ETH long but BTC indicator BEARISH (mismatch)
    #   - short-counter-trend: ETH short but BTC indicator BULLISH (mismatch)
    print("\n=== Gate simulation: KILL counter-trend ETH (IS-only) ===")
    sim_rows = []
    indicator_specs = [
        ("I1_sma_50", "sma_bull"),
        ("I3_ema12_v_ema26", "macd_bull"),
        ("I2_ret_14d_>0", "ret14_bull_I2_ret_14d_>0"),
        ("I2_ret_14d_>5%", "ret14_bull_I2_ret_14d_>5%"),
        ("I2_ret_14d_>10%", "ret14_bull_I2_ret_14d_>10%"),
    ]
    for ind, bull_col in indicator_specs:
        # Symmetric counter-trend kill: long+bear OR short+bull
        kill = (
            ((eth_is["direction"] == 1) & (~eth_is[bull_col])) |
            ((eth_is["direction"] == -1) & (eth_is[bull_col]))
        )
        sim = gate_pnl_sim(eth_is, kill)
        sim["indicator"] = ind
        sim["gate_mode"] = "kill_counter_trend"
        # Compute per-trade WR for the gated stream
        survived = eth_is[~kill]
        if len(survived):
            sim["gated_wr_pct"] = float((survived["net_pnl_pct"] > 0).mean() * 100)
            sim["gated_avg_pnl"] = float(survived["net_pnl_pct"].mean())
        else:
            sim["gated_wr_pct"] = 0.0
            sim["gated_avg_pnl"] = 0.0
        sim_rows.append(sim)

    # Additionally: kill only TRADES THAT FIGHT a LARGE BTC trend (v2/019-style)
    for thr_label, threshold in [("v2_clone_>20%", 0.20), ("medium_>10%", 0.10),
                                   ("light_>5%", 0.05)]:
        # Long+BTC -threshold (dumped past threshold), or Short+BTC +threshold (rallied)
        kill = (
            ((eth_is["direction"] == 1) & (eth_is["ret14"] < -threshold)) |
            ((eth_is["direction"] == -1) & (eth_is["ret14"] > threshold))
        )
        sim = gate_pnl_sim(eth_is, kill)
        sim["indicator"] = f"I2_threshold_{thr_label}"
        sim["gate_mode"] = "kill_large_counter_move"
        survived = eth_is[~kill]
        if len(survived):
            sim["gated_wr_pct"] = float((survived["net_pnl_pct"] > 0).mean() * 100)
            sim["gated_avg_pnl"] = float(survived["net_pnl_pct"].mean())
        else:
            sim["gated_wr_pct"] = 0.0
            sim["gated_avg_pnl"] = 0.0
        sim_rows.append(sim)

    sim_df = pd.DataFrame(sim_rows)[
        ["indicator", "gate_mode", "n_total", "n_skipped", "skip_pct",
         "baseline_pnl_pct", "gated_pnl_pct", "lift_pct",
         "gated_wr_pct", "gated_avg_pnl"]
    ]
    sim_df.to_csv(OUT / "btc_trend_gate_simulation.csv", index=False)
    print(sim_df.to_string(index=False))

    # --- Choose best gate ---
    # Selection criterion: highest IS PnL lift WITH skip rate <= 50%
    # (avoid over-skipping; need enough OOS trade-rate floor margin)
    feasible = sim_df[sim_df["skip_pct"] <= 50.0]
    if len(feasible) == 0:
        chosen = sim_df.sort_values("lift_pct", ascending=False).iloc[0]
    else:
        chosen = feasible.sort_values("lift_pct", ascending=False).iloc[0]

    print(f"\n=== Chosen gate for /019 brief Section 3 ===")
    print(chosen.to_dict())
    chosen_df = pd.DataFrame([chosen.to_dict()])
    chosen_df.to_csv(OUT / "btc_trend_chosen_gate.csv", index=False)


if __name__ == "__main__":
    main()
