"""iter-v3/123 — ADF stationarity audit for the 4 ETH/sym vol-ratio candidates.

ADF test on each (candidate, symbol) cell at the FINAL IS month (closest to
OOS_CUTOFF_DATE = 2025-03-24). PASS at p<0.05 — the v3 mandatory stationarity gate.

The Critic Check 5 at Phase 7.5 will read this CSV (T8_adf_stationarity.csv).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

from _shared import (  # noqa: E402
    CANDIDATE_NAMES,
    SYMBOLS,
    build_labeled_panel,
)


def main() -> None:
    print("[iter-v3/123 ADF] Stationarity audit start")
    panels = {sym: build_labeled_panel(sym) for sym in SYMBOLS}

    rows = []
    for cand in CANDIDATE_NAMES:
        for sym in SYMBOLS:
            panel = panels[sym]
            # Use the final 2000 IS rows for ADF (last IS year ~ 2024-03-2025-03 at 8h)
            tail = panel[cand].tail(2000).dropna().to_numpy(dtype=np.float64)
            if len(tail) < 100:
                rows.append({"candidate": cand, "symbol": sym, "adf_stat": np.nan,
                             "p_value": np.nan, "n": len(tail), "verdict": "INSUFFICIENT"})
                continue
            try:
                from statsmodels.tsa.stattools import adfuller
                stat, p, *_ = adfuller(tail, regression="c", autolag="AIC")
                verdict = "PASS" if p < 0.05 else "FAIL"
                rows.append(
                    {
                        "candidate": cand,
                        "symbol": sym,
                        "adf_stat": round(float(stat), 4),
                        "p_value": round(float(p), 6),
                        "n": len(tail),
                        "verdict": verdict,
                    }
                )
            except Exception as e:
                rows.append({"candidate": cand, "symbol": sym, "adf_stat": np.nan,
                             "p_value": np.nan, "n": len(tail), "verdict": f"ERR:{e}"})

    df = pd.DataFrame(rows)
    df.to_csv(THIS_DIR / "T8_adf_stationarity.csv", index=False)
    print(f"[ADF] Wrote stationarity audit ({len(df)} rows) -> T8_adf_stationarity.csv")
    print("\n[T8 summary]")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
