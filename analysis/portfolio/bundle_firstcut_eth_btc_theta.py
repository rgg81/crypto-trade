"""iter-v1 PORTFOLIO BUNDLE — first cut (ETH + BTC + THETA), 2026-06-18.

Demonstrates the portfolio-level breadth payoff of the 3 both-positive v1 baselines:
  ETH  iter-034 (deterministic core)      — strong, trend-favorable
  BTC  iter-020 (model-gated)             — modest
  THETA iter-047 (deterministic core)     — LOW-CORRELATION diversifier (0.65 vs BTC/ETH)

Method (parity-clean: each coin's single-symbol strategy runs INDEPENDENTLY; the portfolio is the
capital-weighted SUM of the independent coins' PnL — no post-trade netting):
  - per-coin MONTHLY net PnL (sum of trade net_pnl_pct by close-month)
  - weights: EQUAL and INVERSE-VOL (IS-only: w ∝ 1/std(IS monthly PnL))   [IS-only, no OOS leak]
  - portfolio monthly PnL = Σ_coin w_coin · coin_monthly ; Sharpe = mean/std·√12 at OOS_CUTOFF

RESULT (official merged baselines):
  single OOS monthly Sharpe: ETH +0.82, BTC +0.45, THETA +0.74
  OOS monthly-return correlation: ETH-BTC 0.25, ETH-THETA -0.05 (!), BTC-THETA 0.39
  PORTFOLIO equal-weight:  IS +0.66 / OOS +1.04   <- beats every single coin
  PORTFOLIO inverse-vol:   IS +0.66 / OOS +1.02
  => genuine diversification benefit (portfolio OOS > best single +0.82); THETA's low/negative
     correlation to ETH is the key driver. The 3-coin portfolio crosses OOS Sharpe 1.0.

CAVEATS (load-bearing):
  - This is a SIMPLE monthly-sum aggregation of net_pnl_pct (NOT the baselines' weighted/vol-tgt
    series), so the absolute monthly Sharpes differ from the baseline-doc headline numbers; the
    RELATIVE finding (portfolio > single coins) is the robust point.
  - OOS is ~15 months (15 data points) -> the +1.04 has WIDE error bars; the durable claim is the
    diversification DIRECTION (portfolio Sharpe > single), not the exact magnitude.
  - FIRST CUT: a proper BUNDLE merge needs the structured assembly per the bundle rules
    (committed IS-only weight_calibration.py, Section-11 parity statement, no-coin-overlap assertion
    [auto-satisfied: ETH/BTC/THETA disjoint], full portfolio backtest).
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

OOS_CUTOFF = pd.Timestamp("2025-03-24")
COINS = {
    "ETH": "reports-v1/ETHUSDT/iteration_v1-034",
    "BTC": "reports-v1/BTCUSDT/iteration_v1-020",
    "THETA": "reports-v1/THETAUSDT/iteration_v1-047",
}


def monthly(path: str) -> pd.Series | None:
    frames = []
    for sub in ("in_sample", "out_of_sample"):
        p = f"{path}/{sub}/trades.csv"
        if not os.path.exists(p):
            continue
        d = pd.read_csv(p)
        tcol = "close_time" if "close_time" in d.columns else "open_time"
        pcol = "net_pnl_pct" if "net_pnl_pct" in d.columns else "pnl_pct"
        d["m"] = pd.to_datetime(d[tcol], unit="ms").dt.to_period("M")
        frames.append(d[["m", pcol]].rename(columns={pcol: "pnl"}))
    if not frames:
        return None
    return pd.concat(frames).groupby("m")["pnl"].sum()


def sharpe(x: pd.Series) -> float:
    x = x[x.notna()]
    return x.mean() / x.std() * np.sqrt(12) if len(x) > 1 and x.std() > 0 else float("nan")


def main() -> None:
    series = {c: monthly(p) for c, p in COINS.items() if os.path.isdir(p)}
    m = pd.DataFrame(series).fillna(0.0)
    m.index = m.index.to_timestamp()
    is_m, oos_m = m[m.index < OOS_CUTOFF], m[m.index >= OOS_CUTOFF]
    for c in m.columns:
        print(f"{c}: IS={sharpe(is_m[c]):+.2f} OOS={sharpe(oos_m[c]):+.2f}")
    print("OOS corr:\n", oos_m.corr().round(2).to_string())
    ivol = {c: 1 / is_m[c].std() for c in m.columns}
    sv = sum(ivol.values())
    ivol = {c: v / sv for c, v in ivol.items()}
    for name, w in [("EQUAL", {c: 1 / len(m.columns) for c in m.columns}), ("INV-VOL", ivol)]:
        pis = sum(w[c] * is_m[c] for c in m.columns)
        poos = sum(w[c] * oos_m[c] for c in m.columns)
        print(f"PORTFOLIO {name}: IS={sharpe(pis):+.2f} OOS={sharpe(poos):+.2f}")


if __name__ == "__main__":
    main()
