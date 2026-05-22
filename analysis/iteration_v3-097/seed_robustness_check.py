"""iter-v3/097 — T6 SEED-ROBUSTNESS companion check — IS-only.

Re-runs the headline within-symbol purged-5-fold-CV rank-IC (the screen's T2
metric) for the top tier of candidates under 4 LightGBM seeds (42, 7, 99,
2024).  Purpose: confirm the GENUINE-SIGNAL / THIN-SIGNAL split found by
symbol_universe_screen_eda.py is a property of the symbols, NOT a single-seed
lottery — the iter-v3/036/079 single-seed-lottery failure mode must not
contaminate a universe RE-SELECTION.

PASS criterion (per-symbol): the GENUINE pair must clear the +0.040 thin-band
ceiling on ALL 4 seeds; the THIN pair (BCH/TRX) must stay below the +0.040
ceiling on ALL 4 seeds.  If the ranking inverts under any seed, the screen is
not safe to act on.

NO CHEATING: IS-only (open_time < OOS_CUTOFF_MS), 24-month burn-in, the /059
production triple-barrier label — all inherited from
symbol_universe_screen_eda.py (imported, not re-implemented).

Writes: analysis/iteration_v3-097/T6_seed_robustness.csv
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import lightgbm as lgb
except ImportError:  # pragma: no cover
    raise

# Import the screen module (the labeling + CV machinery — single source).
_SPEC = importlib.util.spec_from_file_location(
    "screen", Path(__file__).parent / "symbol_universe_screen_eda.py"
)
assert _SPEC is not None and _SPEC.loader is not None
screen = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(screen)

OUT = Path("analysis/iteration_v3-097")
SEEDS = (42, 7, 99, 2024)
THIN_FLOOR = 0.040  # the screen's THIN_IC_MAX
# top tier = the 2 GENUINE + 3 BORDERLINE + the 2 legacy THIN symbols
TOP_TIER = (
    "LDOUSDT",
    "GALAUSDT",
    "AAVEUSDT",
    "EOSUSDT",
    "ADAUSDT",
    "BCHUSDT",
    "TRXUSDT",
)


def cv_ic_for_seed(d: pd.DataFrame, seed: int) -> float:
    """Within-symbol purged-5-fold-CV rank-IC at a given LightGBM seed."""
    X = d[list(screen.V3_FEATURE_COLUMNS)].to_numpy(dtype=np.float64)
    y = d["y"].to_numpy(dtype=int)
    tgt = d["tb_label"].to_numpy(dtype=np.float64)
    params = dict(screen.LGB_PARAMS)
    params["random_state"] = seed
    fold_ics: list[float] = []
    for tr, te in screen.purged_kfold_indices(len(d), 5, screen.EMBARGO_CANDLES):
        if len(np.unique(y[tr])) < 2 or len(te) < 30:
            continue
        model = lgb.LGBMClassifier(**params)
        model.fit(X[tr], y[tr])
        ic = screen.rank_ic(model.predict_proba(X[te])[:, 1], tgt[te])
        if pd.notna(ic):
            fold_ics.append(ic)
    return float(np.nanmean(fold_ics)) if fold_ics else float("nan")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/097 T6 — SEED-ROBUSTNESS of the within-symbol CV-IC screen")
    print(f"  seeds = {SEEDS}; thin-band ceiling = +{THIN_FLOOR}")
    print("=" * 78)
    rows = []
    for sym in TOP_TIER:
        d = screen.load_symbol_is(sym)
        if d is None:
            print(f"  {sym}: parquet missing — skipped")
            continue
        d["y"] = (d["tb_label"] == 1).astype(int)
        d = d.dropna(
            subset=list(screen.V3_FEATURE_COLUMNS) + ["tb_pnl"]
        ).reset_index(drop=True)
        seed_ics = np.array([cv_ic_for_seed(d, sd) for sd in SEEDS])
        rows.append(
            {
                "symbol": sym,
                "cv_ic_seed42": round(seed_ics[0], 5),
                "cv_ic_seed7": round(seed_ics[1], 5),
                "cv_ic_seed99": round(seed_ics[2], 5),
                "cv_ic_seed2024": round(seed_ics[3], 5),
                "cv_ic_seed_mean": round(float(seed_ics.mean()), 5),
                "cv_ic_seed_std": round(float(seed_ics.std()), 5),
                "all_seeds_above_thin_floor": bool((seed_ics > THIN_FLOOR).all()),
                "all_seeds_below_thin_floor": bool((seed_ics < THIN_FLOOR).all()),
            }
        )
        print(
            f"  {sym:10s}: seeds = "
            f"[{seed_ics[0]:+.4f},{seed_ics[1]:+.4f},"
            f"{seed_ics[2]:+.4f},{seed_ics[3]:+.4f}]  "
            f"mean {seed_ics.mean():+.4f} std {seed_ics.std():.4f}"
        )
    t6 = pd.DataFrame(rows)
    t6.to_csv(OUT / "T6_seed_robustness.csv", index=False)
    print("\nT6 written to T6_seed_robustness.csv")
    genuine_stable = t6[t6["all_seeds_above_thin_floor"]]["symbol"].tolist()
    thin_stable = t6[t6["all_seeds_below_thin_floor"]]["symbol"].tolist()
    print(f"  seed-stable ABOVE +{THIN_FLOOR} (all 4 seeds): {genuine_stable}")
    print(f"  seed-stable BELOW +{THIN_FLOOR} (all 4 seeds): {thin_stable}")
    print("=" * 78)


if __name__ == "__main__":
    main()
