"""iter-v3/102 — EDA Script 2: IC sign-stability + redundancy vs the 14 incumbents.

DELIVERABLE
-----------
For the v3-portable formulaic-alpha basket, STRICTLY IS-ONLY:
  T4  IC sign-stability across IS SUB-PERIODS.  The IS window is split into 4
      contiguous thirds-of-equal-rows per symbol; the directional IC is
      recomputed per sub-period.  A robust alpha keeps the SAME IC SIGN across
      sub-periods (a sign-flipping alpha is regime-conditioned noise — the /101
      F5 lesson: a feature can lift OOS by loading a regime factor, not signal).
  T5  Redundancy vs the 14 incumbent V3_FEATURE_COLUMNS.  Per (alpha, incumbent)
      max |Spearman| over pooled IS rows.  The v3 feature-family gate is
      |IC| < 0.70 (ITERATION_PLAN_8H_V3.md Critic Check 4).  An alpha that
      correlates >= 0.70 with an incumbent is redundant — it would steal
      colsample_bytree picks without adding signal (iter-v3/070's exact
      failure: a candidate correlated to an existing feature wastes splits).
      NOTE: for an ENGINEERED Category-2 composed alpha the |IC| carve-out
      applies (feedback_v3_engineered_feature_pivot.md) — flagged in the table.

NO-CHEATING
-----------
- OOS_CUTOFF_MS = 1742774400000.  Every row is IS-only (open_time < cutoff).
- The label + burn-in are identical to Script 1 / labeling.py.

RUN:  uv run python analysis/iteration_v3-102/alpha_redundancy_eda.py
      (requires Script 1's panels; this script rebuilds them — self-contained.)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from alpha_ic_eda import (  # noqa: E402
    OOS_CUTOFF_MS,
    SYMBOLS,
    TRAINING_MONTHS,
    load_full_panel,
    triple_barrier_label,
)
from alpha_lib import ALPHA_NOTES, ALPHA_REGISTRY  # noqa: E402

OUT = Path("analysis/iteration_v3-102")
MS_PER_DAY = 24 * 60 * 60 * 1000
N_SUBPERIODS = 4

# The 14 incumbent V3_FEATURE_COLUMNS (/059 anchor) — the redundancy reference.
V3_FEATURE_COLUMNS = (
    "max_dd_window_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
    "regime_momentum_signed_5d",
)

# ENGINEERED Category-2 alphas — |IC| carve-out applies (importance gate, not IC).
ENGINEERED_ALPHAS = {"alpha053_regime_signed"}

IC_REDUNDANCY_GATE = 0.70  # ITERATION_PLAN_8H_V3.md Critic Check 4


def build_is_panel(symbol: str) -> pd.DataFrame:
    """Rebuild a symbol's IS panel with all alphas + incumbents + label."""
    full = load_full_panel(symbol)
    for name, fn in ALPHA_REGISTRY.items():
        full[name] = fn(full).astype(float)
    full = triple_barrier_label(full)
    first_ms = int(full["open_time"].min())
    burnin_end = first_ms + TRAINING_MONTHS * 30 * MS_PER_DAY
    is_mask = (full["open_time"] >= burnin_end) & (full["open_time"] < OOS_CUTOFF_MS)
    isd = full[is_mask].copy().reset_index(drop=True)
    isd["symbol"] = symbol
    return isd


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/102 EDA Script 2 — IC sign-stability + redundancy")
    print(f"OOS_CUTOFF_MS = {OOS_CUTOFF_MS} (2025-03-24) — every row IS-only")
    print("=" * 78)

    alpha_names = list(ALPHA_REGISTRY.keys())
    panels = {sym: build_is_panel(sym) for sym in SYMBOLS}

    # ---- T4: IC sign-stability across IS sub-periods ----
    print(f"\nT4 — directional-IC sign-stability across {N_SUBPERIODS} IS "
          f"sub-periods (per symbol; equal-row contiguous splits):")
    t4_rows = []
    for name in alpha_names:
        # per symbol: list of sub-period IC signs
        all_signs = []
        per_sym_detail = {}
        for sym in SYMBOLS:
            d = panels[sym].sort_values("open_time").reset_index(drop=True)
            chunks = np.array_split(np.arange(len(d)), N_SUBPERIODS)
            sub_ics = []
            for ch in chunks:
                sub = d.iloc[ch]
                a = sub[name]
                lab = sub["tb_label"].astype(float)
                valid = a.notna() & lab.notna() & np.isfinite(a)
                if int(valid.sum()) < 50 or a[valid].nunique() < 5:
                    sub_ics.append(np.nan)
                    continue
                ic = a[valid].rank().corr(lab[valid].rank())
                sub_ics.append(ic)
            per_sym_detail[sym] = sub_ics
            for v in sub_ics:
                if pd.notna(v) and abs(v) > 1e-6:
                    all_signs.append(np.sign(v))
        # fraction of (symbol x sub-period) cells whose IC sign equals the
        # overall-most-common sign
        if all_signs:
            pos = sum(1 for s in all_signs if s > 0)
            neg = len(all_signs) - pos
            dominant = 1.0 if pos >= neg else -1.0
            stable_frac = max(pos, neg) / len(all_signs)
        else:
            dominant, stable_frac = np.nan, np.nan
        t4_rows.append(
            {
                "alpha": name,
                "BCH_subperiod_ic": [
                    round(v, 3) if pd.notna(v) else None
                    for v in per_sym_detail["BCHUSDT"]
                ],
                "LDO_subperiod_ic": [
                    round(v, 3) if pd.notna(v) else None
                    for v in per_sym_detail["LDOUSDT"]
                ],
                "TRX_subperiod_ic": [
                    round(v, 3) if pd.notna(v) else None
                    for v in per_sym_detail["TRXUSDT"]
                ],
                "dominant_sign": dominant,
                "sign_stable_frac": round(stable_frac, 3)
                if pd.notna(stable_frac)
                else np.nan,
            }
        )
    t4 = pd.DataFrame(t4_rows).sort_values(
        "sign_stable_frac", ascending=False, na_position="last"
    )
    t4.to_csv(OUT / "T4_ic_sign_stability.csv", index=False)
    print(t4.to_string(index=False))
    print(
        "\n  sign_stable_frac = fraction of the 12 (3-symbol x 4-subperiod) IC "
        "cells sharing the dominant sign.  >= 0.75 = robust; ~0.50 = a "
        "regime-conditioned coin-flip (the /101 F5 fragility pattern)."
    )

    # ---- T5: redundancy vs the 14 incumbent V3_FEATURE_COLUMNS ----
    print("\nT5 — alpha redundancy vs the 14 incumbent V3_FEATURE_COLUMNS")
    print(f"  (max |Spearman| over pooled IS rows; gate < {IC_REDUNDANCY_GATE}):")
    pooled = pd.concat(panels.values(), ignore_index=True)
    t5_rows = []
    for name in alpha_names:
        mx, arg = 0.0, ""
        a_rank = pooled[name].rank()
        for inc in V3_FEATURE_COLUMNS:
            if inc not in pooled.columns:
                continue
            c = a_rank.corr(pooled[inc].rank())
            if pd.notna(c) and abs(c) > mx:
                mx, arg = abs(c), inc
        is_engineered = name in ENGINEERED_ALPHAS
        # gate: strict |IC| for raw alphas; carve-out (always "pass") for
        # ENGINEERED Category-2 composed alphas — flagged.
        gate_pass = (mx < IC_REDUNDANCY_GATE) or is_engineered
        t5_rows.append(
            {
                "alpha": name,
                "note": ALPHA_NOTES[name],
                "max_abs_ic_vs_incumbent": round(mx, 4),
                "argmax_incumbent": arg,
                "is_engineered_carveout": is_engineered,
                "redundancy_gate_pass": gate_pass,
            }
        )
    t5 = pd.DataFrame(t5_rows).sort_values("max_abs_ic_vs_incumbent")
    t5.to_csv(OUT / "T5_redundancy_vs_incumbents.csv", index=False)
    print(t5.to_string(index=False))
    n_redundant = int((~t5["redundancy_gate_pass"]).sum())
    print(
        f"\n  -> {n_redundant}/{len(t5)} alphas FAIL the |IC| < "
        f"{IC_REDUNDANCY_GATE} redundancy gate.  A redundant alpha would steal "
        f"colsample_bytree picks from an incumbent without adding signal "
        f"(iter-v3/070's exact failure mode)."
    )

    print("\n" + "=" * 78)
    print("Script 2 done.  Outputs: T4_ic_sign_stability.csv, "
          "T5_redundancy_vs_incumbents.csv")
    print("Next: alpha_horserace_eda.py (multivariate held-out-tail horse race "
          "+ final single-alpha selection).")
    print("=" * 78)


if __name__ == "__main__":
    main()
