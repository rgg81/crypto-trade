"""iter-v3/122 — ADF stationarity audit for ETH cross-asset feature candidates.

Per BASELINE_V3.md MERGE gates: "ADF p < 0.05 on every feature (or explicit
'regime indicator' justification in brief Section 4)". This script tests the
4 ETH-derived candidates for stationarity on each of BCHUSDT / LDOUSDT /
TRXUSDT IS-only panels.

ETH features are log-returns or vol-differentials, which are structurally
stationary by construction (log-returns ~ stationary; vol-diffs are
differences of stationary processes). The ADF test should be decisive.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

from _shared import CANDIDATE_NAMES, SYMBOLS, build_labeled_panel  # noqa: E402


def main() -> None:
    panels = {sym: build_labeled_panel(sym) for sym in SYMBOLS}
    rows = []
    for cand in CANDIDATE_NAMES:
        for sym in SYMBOLS:
            x = panels[sym][cand].dropna().to_numpy(dtype="float64")
            if len(x) < 100:
                rows.append({"candidate": cand, "symbol": sym, "n": len(x),
                             "adf_stat": np.nan, "p_value": np.nan,
                             "stationary": False})
                continue
            try:
                adf_stat, p_value, *_ = adfuller(x, regression="c", autolag="AIC")
            except Exception as e:
                rows.append({"candidate": cand, "symbol": sym, "n": len(x),
                             "adf_stat": np.nan, "p_value": np.nan,
                             "stationary": False, "err": str(e)})
                continue
            rows.append({
                "candidate": cand,
                "symbol": sym,
                "n": int(len(x)),
                "adf_stat": round(float(adf_stat), 3),
                "p_value": round(float(p_value), 6),
                "stationary": bool(p_value < 0.05),
            })
    df = pd.DataFrame(rows)
    df.to_csv(THIS_DIR / "T8_adf_stationarity.csv", index=False)
    print(df.to_string(index=False))
    n_pass = int(df["stationary"].sum())
    n_total = len(df)
    print(f"\n[ADF audit] {n_pass}/{n_total} (symbol, candidate) cells PASS p<0.05")


if __name__ == "__main__":
    main()
