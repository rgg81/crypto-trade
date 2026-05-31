"""iter-v1/037 EDA — IS-only Sortino vs Sharpe diagnostic per cohort.

Reads reports-v1/iteration_v1-baseline/in_sample/trades.csv and computes,
for each Model cohort (A=BTC+ETH, C=LINK, D=LTC, E=DOT), the trade-level:

  - Sharpe   = mean(pnl_pct) / std(pnl_pct)
  - Sortino  = mean(pnl_pct) / std(pnl_pct[pnl_pct<0])
  - Skew, downside fraction, downside std vs total std ratio

Mechanically tells us how MUCH Sortino reweighting could change Optuna's
basin selection — if Sortino/Sharpe ≈ 1.0 (symmetric distribution), no
meaningful gradient change; if Sortino/Sharpe ≈ 2.0+ (heavy left tail),
the loss-surface gradient shifts substantially.

Writes: sortino_vs_sharpe.csv
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd

REPORT_ROOT = Path(__file__).resolve().parents[2]
IS_TRADES = REPORT_ROOT / "reports-v1" / "iteration_v1-baseline" / "in_sample" / "trades.csv"
OUT_CSV = Path(__file__).parent / "sortino_vs_sharpe.csv"

COHORT_MAP = {
    "Model_A_pool": ("BTCUSDT", "ETHUSDT"),
    "Model_C_LINK": ("LINKUSDT",),
    "Model_D_LTC": ("LTCUSDT",),
    "Model_E_DOT": ("DOTUSDT",),
}


def compute_metrics(pnls: np.ndarray) -> dict:
    n = len(pnls)
    if n < 2:
        return dict(
            n=n,
            mean=float("nan"),
            std=float("nan"),
            down_std=float("nan"),
            sharpe=float("nan"),
            sortino=float("nan"),
            ratio=float("nan"),
            down_frac=float("nan"),
            skew=float("nan"),
        )
    mean = float(pnls.mean())
    std = float(pnls.std(ddof=0))
    downside = pnls[pnls < 0]
    down_std = float(downside.std(ddof=0)) if len(downside) > 1 else float("nan")
    sharpe = mean / std if std > 0 else float("nan")
    sortino = mean / down_std if down_std and down_std > 0 else float("nan")
    ratio = (sortino / sharpe) if (sharpe and not np.isnan(sortino)) else float("nan")
    down_frac = len(downside) / n
    # skew via pandas (Fisher)
    skew = float(pd.Series(pnls).skew())
    return dict(
        n=n,
        mean=mean,
        std=std,
        down_std=down_std,
        sharpe=sharpe,
        sortino=sortino,
        ratio=ratio,
        down_frac=down_frac,
        skew=skew,
    )


def main() -> None:
    df = pd.read_csv(IS_TRADES)
    # Identify per-trade pnl column: pnl_pct preferred, fall back to weighted
    if "pnl_pct" in df.columns:
        pnl_col = "pnl_pct"
    elif "pnl_pct_net" in df.columns:
        pnl_col = "pnl_pct_net"
    else:
        # use weighted_pnl normalized by typical position size
        pnl_col = "weighted_pnl"
    print(f"[iter-v1/037 EDA] IS trades: {len(df)} rows, pnl col = {pnl_col!r}")
    print(f"[iter-v1/037 EDA] cols: {list(df.columns)[:12]}...")

    rows = []
    # Portfolio-level
    rows.append({"cohort": "PORTFOLIO", **compute_metrics(df[pnl_col].dropna().to_numpy())})

    # Per cohort
    for cohort, syms in COHORT_MAP.items():
        sub = df[df["symbol"].isin(syms)]
        rows.append({"cohort": cohort, **compute_metrics(sub[pnl_col].dropna().to_numpy())})

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"[iter-v1/037 EDA] wrote {OUT_CSV.name}")
    # Pretty print
    fmt = lambda x: f"{x:+.4f}" if isinstance(x, float) and not np.isnan(x) else "  nan"
    print(f"\n{'cohort':<18} {'n':>5} {'mean':>10} {'std':>10} {'down_std':>10} "
          f"{'sharpe':>9} {'sortino':>9} {'ratio':>7} {'down_frac':>10} {'skew':>8}")
    for r in rows:
        print(
            f"{r['cohort']:<18} {r['n']:>5} {fmt(r['mean']):>10} {fmt(r['std']):>10} "
            f"{fmt(r['down_std']):>10} {fmt(r['sharpe']):>9} {fmt(r['sortino']):>9} "
            f"{fmt(r['ratio']):>7} {fmt(r['down_frac']):>10} {fmt(r['skew']):>8}"
        )


if __name__ == "__main__":
    main()
