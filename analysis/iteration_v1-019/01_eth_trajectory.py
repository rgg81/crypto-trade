"""ETH OOS trajectory analysis — iter-v1/019 Phase 1 EDA.

iter-v1/019 = ETH-only with stateless BTC-trend regime gate
(per-cohort-specialization-ETH; NEW 10th axis family).

Goal of this script:
1. Document ETH per-iteration IS/OOS PnL across baseline + /014/015/016/017.
2. Establish anchor: ETH-in-pool IS Sharpe and OOS Sharpe (single-symbol
   monthly aggregation from baseline trades).
3. Inspect ETH OOS monthly distribution — identify catastrophic regimes
   (concentrated bear months vs spread-out drag).

Outputs (committed under analysis/iteration_v1-019/):
- eth_oos_trajectory.csv : per-iteration ETH OOS net_pnl / WR / trade count
- eth_monthly_oos_baseline.csv : ETH per-month OOS PnL (baseline reproduction)
- eth_per_symbol_baseline.csv : ETH IS + OOS row from baseline per_symbol

NO TRAINING. NO MODEL FIT. Pure descriptive analysis. IS-only and
already-published-OOS reading from committed reports.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports-v1"
OUT = ROOT / "analysis" / "iteration_v1-019"
OUT.mkdir(parents=True, exist_ok=True)


def annualized_monthly_sharpe(pnl_pct: pd.Series, close_ms: pd.Series) -> tuple[float, int]:
    if len(pnl_pct) == 0:
        return 0.0, 0
    dt = pd.to_datetime(close_ms, unit="ms")
    s = pd.Series(pnl_pct.values, index=dt)
    monthly = s.resample("ME").sum()
    if len(monthly) < 2 or monthly.std() == 0:
        return 0.0, len(monthly)
    return float(monthly.mean() / monthly.std() * math.sqrt(12)), len(monthly)


def load_iter_eth(iter_label: str) -> dict | None:
    """Read per_symbol.csv for one iteration's IS and OOS halves, return ETH row."""
    base = REPORTS / f"iteration_v1-{iter_label}"
    is_path = base / "in_sample" / "per_symbol.csv"
    oos_path = base / "out_of_sample" / "per_symbol.csv"
    if not is_path.exists() or not oos_path.exists():
        return None
    is_df = pd.read_csv(is_path)
    oos_df = pd.read_csv(oos_path)
    eth_is = is_df[is_df["symbol"] == "ETHUSDT"]
    eth_oos = oos_df[oos_df["symbol"] == "ETHUSDT"]
    if eth_is.empty or eth_oos.empty:
        return None
    return {
        "iter": iter_label,
        "eth_is_trades": int(eth_is.iloc[0]["trades"]),
        "eth_is_wr": float(eth_is.iloc[0]["win_rate"]),
        "eth_is_net_pnl_pct": float(eth_is.iloc[0]["net_pnl_pct"]),
        "eth_is_avg_pnl_pct": float(eth_is.iloc[0]["avg_pnl_pct"]),
        "eth_oos_trades": int(eth_oos.iloc[0]["trades"]),
        "eth_oos_wr": float(eth_oos.iloc[0]["win_rate"]),
        "eth_oos_net_pnl_pct": float(eth_oos.iloc[0]["net_pnl_pct"]),
        "eth_oos_avg_pnl_pct": float(eth_oos.iloc[0]["avg_pnl_pct"]),
    }


def main() -> None:
    iters = ["baseline", "014", "015", "016", "017"]
    rows = []
    for iter_label in iters:
        r = load_iter_eth(iter_label)
        if r is not None:
            rows.append(r)

    traj = pd.DataFrame(rows)
    traj.to_csv(OUT / "eth_oos_trajectory.csv", index=False)
    print("=== ETH IS/OOS trajectory across baseline + /014-/017 ===")
    print(traj.to_string(index=False))
    print()

    n_pos_is = (traj["eth_is_net_pnl_pct"] > 0).sum()
    n_pos_oos = (traj["eth_oos_net_pnl_pct"] > 0).sum()
    print(f"ETH IS positive iterations: {n_pos_is}/{len(traj)}")
    print(f"ETH OOS positive iterations: {n_pos_oos}/{len(traj)}")
    print(
        f"ETH OOS net_pnl mean: {traj['eth_oos_net_pnl_pct'].mean():.2f}%, "
        f"std: {traj['eth_oos_net_pnl_pct'].std():.2f}%, "
        f"range [{traj['eth_oos_net_pnl_pct'].min():.2f}, "
        f"{traj['eth_oos_net_pnl_pct'].max():.2f}]"
    )
    print()

    # --- Baseline ETH monthly OOS breakdown (regime concentration check) ---
    base_trades_path = REPORTS / "iteration_v1-baseline" / "out_of_sample" / "trades.csv"
    base_trades = pd.read_csv(base_trades_path)
    eth_trades = base_trades[base_trades["symbol"] == "ETHUSDT"].copy()
    eth_trades["close_ts"] = pd.to_datetime(eth_trades["close_time"], unit="ms")
    eth_trades["year_month"] = eth_trades["close_ts"].dt.to_period("M")

    monthly = eth_trades.groupby("year_month").agg(
        n=("net_pnl_pct", "size"),
        wins=("net_pnl_pct", lambda s: (s > 0).sum()),
        net_pnl=("net_pnl_pct", "sum"),
        avg_pnl=("net_pnl_pct", "mean"),
    ).reset_index()
    monthly["year_month"] = monthly["year_month"].astype(str)
    monthly.to_csv(OUT / "eth_monthly_oos_baseline.csv", index=False)
    print("=== ETH OOS monthly distribution (baseline; 46 trades) ===")
    print(monthly.to_string(index=False))
    print()

    # --- Compute ETH-alone IS/OOS Sharpe (monthly) for F1/F3 anchor ---
    base_is_path = REPORTS / "iteration_v1-baseline" / "in_sample" / "trades.csv"
    base_is = pd.read_csv(base_is_path)
    eth_is_trades = base_is[base_is["symbol"] == "ETHUSDT"].copy()

    eth_is_sharpe, eth_is_nm = annualized_monthly_sharpe(
        eth_is_trades["net_pnl_pct"], eth_is_trades["close_time"]
    )
    eth_oos_sharpe, eth_oos_nm = annualized_monthly_sharpe(
        eth_trades["net_pnl_pct"], eth_trades["close_time"]
    )

    anchor = pd.DataFrame(
        [
            {"split": "IS", "n_trades": len(eth_is_trades),
             "n_months": eth_is_nm, "monthly_sharpe": eth_is_sharpe},
            {"split": "OOS", "n_trades": len(eth_trades),
             "n_months": eth_oos_nm, "monthly_sharpe": eth_oos_sharpe},
        ]
    )
    anchor.to_csv(OUT / "eth_per_symbol_baseline.csv", index=False)
    print("=== ETH-alone IS/OOS monthly Sharpe (F1/F3 anchors) ===")
    print(anchor.to_string(index=False))
    print()
    print("**F3 anchor (ETH-in-pool IS monthly Sharpe)**:", round(eth_is_sharpe, 4))
    print("**F1 anchor (ETH-in-pool OOS monthly Sharpe)**:", round(eth_oos_sharpe, 4))


if __name__ == "__main__":
    main()
