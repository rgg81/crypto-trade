"""iter-v1/028 Phase 2 — Seed-robustness + threshold-selection integrity of the M2 lift.

Two checks, both IS-only:
  (1) SEED ROBUSTNESS: re-run the purged-CV OOF M2 across 10 seeds; report the spread of the
      filtered (thr=0.45) book's per-trade Sharpe + win-rate. A real edge is seed-stable; a
      lottery is not. (mirrors the project's K=20 bagging philosophy at the M2 layer.)
  (2) THRESHOLD INTEGRITY: the 0.45 threshold must be picked from TRAIN folds only, never the
      held-out test fold. Re-do the CV nesting the threshold choice inside each train fold
      (choose the train-fold F1-optimal threshold) and apply it to the test fold. Report the
      resulting book. If the lift survives nested threshold selection, the 0.45 result is not
      a threshold-snoop artifact.

Outputs: metalabel_seed_robustness.csv + metalabel_nested_threshold.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.metrics import f1_score

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    OOS_CUTOFF_MS,
    annualized_sharpe_from_trade_pnls,
    concentration_stats,
    load_full_for_label_horizon,
    trend_state_dir,
    trend_strength_atr_norm,
)
from metalabel_precision_cv import (  # noqa: E402
    HORIZON,
    M2_FEATURES,
    TRADES_PER_YEAR,
    purged_kfold_indices,
    realized_net_14d,
)

OUT = Path(__file__).parent


def build_sample(full):
    ts = trend_state_dir(full, 200).astype(int)
    strength = trend_strength_atr_norm(full, 200, 14).values
    is_mask = full["open_time"].values < OOS_CUTOFF_MS
    q40 = np.nanquantile(strength[is_mask & np.isfinite(strength)], 0.40)
    fut_open = pd.Series(full["open_time"].values).shift(-HORIZON).values
    horizon_safe = (full["open_time"].values < OOS_CUTOFF_MS) & (fut_open < OOS_CUTOFF_MS)
    conv = np.isfinite(strength) & (strength >= q40)
    entry = np.where(is_mask & horizon_safe & conv & (ts != 0))[0]
    entry = entry[entry >= 200]
    feat = full.loc[entry, M2_FEATURES].copy()
    valid = feat.notna().all(axis=1).values
    entry = entry[valid]
    feat = feat[valid].reset_index(drop=True)
    dirs = ts[entry]
    net = realized_net_14d(full, entry, dirs)
    y = (net > 0).astype(int)
    return feat.values, y, net


def oof_for_seed(X, y, seed):
    n = len(y)
    gap = HORIZON
    embargo = max(1, int(0.01 * n))
    oof = np.full(n, np.nan)
    for tr, te in purged_kfold_indices(n, k=5, gap=gap, embargo=embargo):
        if len(np.unique(y[tr])) < 2:
            continue
        clf = LGBMClassifier(
            n_estimators=200, max_depth=3, num_leaves=15, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.7, min_child_samples=20,
            reg_alpha=0.1, reg_lambda=0.1, random_state=seed, verbosity=-1,
            scale_pos_weight=float((y[tr] == 0).sum()) / max(1, (y[tr] == 1).sum()),
        )
        clf.fit(X[tr], y[tr])
        oof[te] = clf.predict_proba(X[te])[:, 1]
    return oof


def main() -> None:
    full = load_full_for_label_horizon()
    X, y, net = build_sample(full)
    print(f"IS sample n={len(y)} base WR={y.mean():.3f}")

    # (1) Seed robustness at fixed thr=0.45
    seeds = list(range(42, 52))
    rows = []
    for s in seeds:
        oof = oof_for_seed(X, y, s)
        ok = ~np.isnan(oof)
        keep = ok & (oof >= 0.45)
        cs = concentration_stats(net[keep])
        rows.append({
            "seed": s, "n_kept": int(keep.sum()), "win_rate": cs["win_rate"],
            "per_trade_sharpe_ann": annualized_sharpe_from_trade_pnls(net[keep], TRADES_PER_YEAR),
            "top2_share_of_net": cs["top2_share_of_net"],
        })
    rob = pd.DataFrame(rows)
    rob.to_csv(OUT / "metalabel_seed_robustness.csv", index=False)
    pd.set_option("display.width", 200); pd.set_option("display.max_columns", 20)
    print("\n=== (1) M2 seed robustness (thr=0.45, 10 seeds) ===")
    print(rob.to_string(index=False))
    print(f"\nSharpe: mean={rob.per_trade_sharpe_ann.mean():.3f} "
          f"std={rob.per_trade_sharpe_ann.std():.3f} "
          f"min={rob.per_trade_sharpe_ann.min():.3f} "
          f">0 in {(rob.per_trade_sharpe_ann>0).sum()}/10 seeds")
    print(f"WR: mean={rob.win_rate.mean():.3f} std={rob.win_rate.std():.4f}")

    # (2) Nested threshold selection: choose threshold per train fold (max F1), apply to test fold.
    n = len(y)
    gap = HORIZON
    embargo = max(1, int(0.01 * n))
    test_kept_net = []
    chosen_thrs = []
    for tr, te in purged_kfold_indices(n, k=5, gap=gap, embargo=embargo):
        if len(np.unique(y[tr])) < 2:
            continue
        clf = LGBMClassifier(
            n_estimators=200, max_depth=3, num_leaves=15, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.7, min_child_samples=20,
            reg_alpha=0.1, reg_lambda=0.1, random_state=42, verbosity=-1,
            scale_pos_weight=float((y[tr] == 0).sum()) / max(1, (y[tr] == 1).sum()),
        )
        clf.fit(X[tr], y[tr])
        p_tr = clf.predict_proba(X[tr])[:, 1]
        # pick threshold on TRAIN fold maximizing F1 (proxy for precision-recall balance)
        best_t, best_f1 = 0.5, -1
        for t in np.arange(0.40, 0.66, 0.05):
            f1 = f1_score(y[tr], (p_tr >= t).astype(int), zero_division=0)
            if f1 > best_f1:
                best_f1, best_t = f1, t
        chosen_thrs.append(best_t)
        p_te = clf.predict_proba(X[te])[:, 1]
        keep = p_te >= best_t
        test_kept_net.append(net[te][keep])
    nested = np.concatenate(test_kept_net) if test_kept_net else np.array([])
    cs = concentration_stats(nested)
    nt = pd.DataFrame([{
        "book": "M2_nested_train_threshold",
        "mean_chosen_thr": float(np.mean(chosen_thrs)),
        "n_kept": cs["n_trades"], "win_rate": cs["win_rate"],
        "per_trade_sharpe_ann": annualized_sharpe_from_trade_pnls(nested, TRADES_PER_YEAR),
        "top2_share_of_net": cs["top2_share_of_net"],
    }])
    nt.to_csv(OUT / "metalabel_nested_threshold.csv", index=False)
    print("\n=== (2) Nested train-fold threshold selection (no test-fold snoop) ===")
    print(nt.to_string(index=False))


if __name__ == "__main__":
    main()
