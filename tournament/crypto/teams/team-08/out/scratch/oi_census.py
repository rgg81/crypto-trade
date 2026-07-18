"""e04 — OI coverage census + artifact scan (NO Sharpe computed anywhere).

Fixes active_lo and the A2 median-filter decision per pre-registered rules.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament")
sys.path.insert(0, str(ROOT / "analysis"))

from portfolio_tournament import engine as te  # noqa: E402

OUT = ROOT / "tournament/crypto/teams/team-08/out/scratch"
M = 9
ZWIN, ZMINP = 90, 45


def main() -> None:
    pn, aux, scoring = te.load_is_panels()
    elig = aux["eligibility"]
    oi = aux["oi"].where(aux["oi"] > 0)
    oiv = aux["oi_value"].where(aux["oi_value"] > 0)

    log_oi = np.log(oi)
    dlog1 = log_oi.diff()  # bar-to-bar, for the artifact scan
    doi = log_oi - log_oi.shift(M)
    zden = doi.rolling(ZWIN, min_periods=ZMINP).std()
    sig_valid = doi.notna() & zden.notna()

    n_elig = elig.sum(axis=1)
    n_oi = (elig & oi.notna()).sum(axis=1)
    n_sig = (elig & sig_valid).sum(axis=1)

    q = pd.DataFrame({"elig": n_elig, "oi_valid": n_oi, "sig_valid": n_sig})
    qq = q.groupby(q.index.to_period("Q")).median()
    print("=== quarterly MEDIAN counts (eligible / +OI-valid / +signal-valid) ===")
    print(qq.to_string())

    # active_lo: trailing 84-candle median of signal-valid count >= 10
    roll_med = n_sig.rolling(84).median()
    ok = roll_med[roll_med >= 10]
    active_lo = str(ok.index[0]) if len(ok) else None
    n_active_months = (
        len(pd.period_range(ok.index[0].to_period("M"), pd.Period("2024-06", "M"), freq="M"))
        if len(ok)
        else 0
    )
    print(f"\nactive_lo (rule: trailing 84c median sig_valid >= 10): {active_lo}")
    print(f"active window months (to 2024-06 incl): {n_active_months}")

    # artifact scan on eligible cells only (dead-name garbage excluded)
    d = dlog1.where(elig)
    dv = d.stack().dropna()
    frac_05 = float((dv.abs() > 0.5).mean())
    frac_02 = float((dv.abs() > 0.2).mean())
    print(f"\nartifact scan (eligible cells): n={len(dv)}")
    print(f"frac |dlogOI| > 0.5 = {frac_05:.5f}   frac > 0.2 = {frac_02:.5f}")
    worst = dv.abs().sort_values(ascending=False).head(15)
    print("worst 15 one-bar |dlogOI| (date, sym, |d|):")
    for (ts, sym), v in worst.items():
        print(f"  {ts}  {sym:14} {v:.2f}")
    median_filter = frac_05 > 0.005
    print(f"\nA2 rule: median_filter = {median_filter} (threshold 0.5%)")

    # oi vs oi_value equivalence
    mism = (oi.notna() != oiv.notna()) & elig
    print(f"\noi vs oi_value availability mismatch cells (eligible): {int(mism.sum().sum())}")

    res = {
        "active_lo": active_lo,
        "active_months": n_active_months,
        "frac_dlog_gt_05": frac_05,
        "frac_dlog_gt_02": frac_02,
        "median_filter": bool(median_filter),
        "quarterly": {str(k): [float(x) for x in v] for k, v in qq.iterrows()},
    }
    (OUT / "results_e04.json").write_text(json.dumps(res, indent=2) + "\n")
    print(f"\nwrote {OUT / 'results_e04.json'}")


if __name__ == "__main__":
    main()
