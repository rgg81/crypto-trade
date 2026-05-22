"""iter-v3/102 — EDA Script 3: multivariate held-out-tail horse race + selection.

THE DECISIVE TEST
-----------------
IC (Script 1) and sign-stability (Script 2) are SCREENS — they say which alphas
carry a univariate directional signal that is sign-stable and non-redundant.
They do NOT say whether ADDING the alpha to the 14-feature stack lifts the
PER-SYMBOL MODEL's predictive power.  /096/097/098 proved IS-CV-IC rank does not
predict OOS.  The OOS-robust selection statistic is a NESTED-WALK-FORWARD
HELD-OUT-TAIL test (the /098 methodology):

  For each candidate set S = BASE + one alpha:
    - the held-out tail = the last 6 IS months, sliced into 6 expanding folds;
    - fold k is scored by a LightGBM trained ONLY on rows before fold k's start
      minus a 22-candle embargo purge (no fold sees its own future);
    - dShACC(S)  = paired (per row, pooled across symbols) held-out-tail
                   barrier-label ACCURACY of S minus BASE, with a block-bootstrap
                   95% CI (block = 21-bar label horizon — the /096 discipline);
    - dPnL(S)    = paired held-out-tail SUM-OF-LABELED-PnL lift (economic proxy);
    - importance = the alpha's multivariate gain-importance share on a full-IS
                   fit (the feedback_v3_inert_features_at_higher_budget INERT
                   screen — an INERT feature added at higher budget HARMS OOS).

  This is a Phase-1-style EDA, BUT NOTE: per the dispatch, /102 proceeds to a
  Phase-6 backtest unless the deep EDA conclusively proves the axis DEAD.  The
  horse race is therefore a SELECTION + a sanity GO-band, not a hard GO/NO-GO
  kill: an inconclusive-but-not-dead result still proceeds to the backtest with
  the single best-ranked alpha as the /102 axis.

SELECTION RULE (one alpha; per feedback_v3_engineered_features_dont_stack.md)
-----------------------------------------------------------------------------
The /102 axis adds EXACTLY ONE alpha to V3_FEATURE_COLUMNS.  The selected alpha
is the one maximizing a composite SCORE that rewards:
   (a) held-out-tail dShACC mean  (the OOS-robust predictive lift),
   (b) dShACC CI lower bound      (statistical support — the /096 discipline),
   (c) multivariate importance share above uniform parity (non-INERT),
   (d) Script-1 mean |IC| and Script-2 sign-stability (the screens).
Ties broken toward LOWER incumbent redundancy (cleaner orthogonality).

NO-CHEATING
-----------
- OOS_CUTOFF_MS = 1742774400000.  The "held-out tail" is the last 6 IS months —
  still strictly inside IS (open_time < OOS_CUTOFF_MS).  Real OOS NEVER touched.
- Label + burn-in identical to labeling.py / Scripts 1-2.

RUN:  uv run python analysis/iteration_v3-102/alpha_horserace_eda.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import lightgbm as lgb
except ImportError:  # pragma: no cover
    print("lightgbm not importable", file=sys.stderr)
    raise

sys.path.insert(0, str(Path(__file__).resolve().parent))
from alpha_ic_eda import (  # noqa: E402
    OOS_CUTOFF_MS,
    SYMBOLS,
    TRAINING_MONTHS,
    load_full_panel,
    triple_barrier_label,
)
from alpha_lib import ALPHA_NOTES, ALPHA_REGISTRY  # noqa: E402
from alpha_redundancy_eda import V3_FEATURE_COLUMNS  # noqa: E402

OUT = Path("analysis/iteration_v3-102")
MS_PER_DAY = 24 * 60 * 60 * 1000
TAIL_MONTHS = 6
N_WF_FOLDS = 6
EMBARGO_CANDLES = 22  # 10080 // 480 + 1 — purge each fold boundary
BLOCK_BARS = 21  # bootstrap block = the label horizon
BOOT_RESAMPLES = 2000
RNG_SEED = 42

# Modest depth-5 tree, matching v3's depth-3-5 regime (the /098 EDA params).
LGB_PARAMS = dict(
    objective="binary",
    n_estimators=200,
    num_leaves=31,
    max_depth=5,
    learning_rate=0.05,
    min_child_samples=40,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    random_state=RNG_SEED,
    verbose=-1,
    n_jobs=2,
)


def build_is_panel(symbol: str) -> pd.DataFrame:
    """Rebuild a symbol's IS panel with all alphas + incumbents + label, drop
    rows with any NaN in the BASE features or the label PnL."""
    full = load_full_panel(symbol)
    for name, fn in ALPHA_REGISTRY.items():
        full[name] = fn(full).astype(float)
    full = triple_barrier_label(full)
    first_ms = int(full["open_time"].min())
    burnin_end = first_ms + TRAINING_MONTHS * 30 * MS_PER_DAY
    is_mask = (full["open_time"] >= burnin_end) & (full["open_time"] < OOS_CUTOFF_MS)
    isd = full[is_mask].copy().reset_index(drop=True)
    isd["symbol"] = symbol
    isd["y"] = (isd["tb_label"] == 1).astype(int)
    return isd


def nested_walkforward_eval(
    panel: pd.DataFrame, feat_cols: list[str]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Nested expanding-window walk-forward over the held-out tail.

    Returns (pred-side-correct, predicted-side PnL, n) aligned over tail rows.
    Fold k trained on rows < fold-start minus the embargo purge.  Strictly IS.
    """
    panel = panel.sort_values("open_time").reset_index(drop=True)
    last_t = int(panel["open_time"].max())
    tail_start = last_t - TAIL_MONTHS * 30 * MS_PER_DAY
    tail_idx = np.where((panel["open_time"] >= tail_start).to_numpy())[0]
    if len(tail_idx) < N_WF_FOLDS * 8:
        return np.array([]), np.array([]), np.array([])

    X_all = panel[feat_cols].to_numpy(dtype=np.float64)
    y_all = panel["y"].to_numpy(dtype=int)
    tgt_all = panel["tb_label"].to_numpy(dtype=np.float64)
    pnl_all = panel["tb_pnl"].to_numpy(dtype=np.float64)

    corrects, sidepnls = [], []
    for fold in np.array_split(tail_idx, N_WF_FOLDS):
        if len(fold) == 0:
            continue
        train_hi = max(0, int(fold[0]) - EMBARGO_CANDLES)
        tr = np.arange(0, train_hi)
        if len(tr) < 100 or len(np.unique(y_all[tr])) < 2:
            continue
        model = lgb.LGBMClassifier(**LGB_PARAMS)
        model.fit(X_all[tr], y_all[tr])
        p = model.predict_proba(X_all[fold])[:, 1]
        pred_side = np.where(p >= 0.5, 1.0, -1.0)
        corrects.append((pred_side == tgt_all[fold]).astype(np.float64))
        # pred-side PnL: tb_pnl if pred agrees with the label side, else -tb_pnl
        sidepnls.append(np.where(pred_side == tgt_all[fold], pnl_all[fold], -pnl_all[fold]))
    if not corrects:
        return np.array([]), np.array([]), np.array([])
    c = np.concatenate(corrects)
    s = np.concatenate(sidepnls)
    return c, s, np.array([len(c)])


def block_bootstrap_ci(
    diffs: np.ndarray, block: int, n_boot: int, seed: int
) -> tuple[float, float, float]:
    """Block-bootstrap 95% CI of the mean of `diffs` (contiguous blocks)."""
    diffs = diffs[np.isfinite(diffs)]
    n = len(diffs)
    if n < block * 2:
        m = float(np.mean(diffs)) if n else float("nan")
        return m, float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / block))
    pool = np.arange(0, n - block + 1)
    means = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.choice(pool, size=n_blocks, replace=True)
        sample = np.concatenate([diffs[s : s + block] for s in starts])[:n]
        means[b] = sample.mean()
    return (
        float(np.mean(diffs)),
        float(np.percentile(means, 2.5)),
        float(np.percentile(means, 97.5)),
    )


def importance_share(panel: pd.DataFrame, feat_cols: list[str], new_col: str) -> float:
    """Multivariate gain-importance share of `new_col` on a full-IS fit."""
    X = panel[feat_cols].to_numpy(dtype=np.float64)
    y = panel["y"].to_numpy(dtype=int)
    if len(np.unique(y)) < 2:
        return float("nan")
    model = lgb.LGBMClassifier(**LGB_PARAMS)
    model.fit(X, y)
    gains = np.asarray(model.booster_.feature_importance(importance_type="gain"))
    total = gains.sum()
    if total <= 0:
        return float("nan")
    return float(gains[feat_cols.index(new_col)] / total)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/102 EDA Script 3 — multivariate held-out-tail horse race")
    print(f"OOS_CUTOFF_MS = {OOS_CUTOFF_MS}; held-out tail = last {TAIL_MONTHS} "
          f"IS months ({N_WF_FOLDS} expanding folds, {EMBARGO_CANDLES}-candle "
          f"embargo).  Strictly IS.")
    print("=" * 78)

    alpha_names = list(ALPHA_REGISTRY.keys())
    base = list(V3_FEATURE_COLUMNS)
    need_cols = base + alpha_names + ["tb_pnl"]

    panels = {}
    for sym in SYMBOLS:
        d = build_is_panel(sym)
        d = d.dropna(subset=need_cols).reset_index(drop=True)
        panels[sym] = d
        print(f"  {sym}: {len(d)} IS rows after dropna over BASE+alphas+label")

    # ---- BASE held-out-tail performance (the control) ----
    base_correct, base_pnl = {}, {}
    for sym in SYMBOLS:
        c, s, _ = nested_walkforward_eval(panels[sym], base)
        base_correct[sym], base_pnl[sym] = c, s
    base_acc = np.concatenate([base_correct[s] for s in SYMBOLS])
    print(f"\n  BASE held-out-tail accuracy (pooled): "
          f"{base_acc.mean():.4f}  over {len(base_acc)} tail rows")

    # ---- T6: per-alpha horse race vs BASE ----
    print("\nT6 — per-alpha held-out-tail lift over BASE (block-bootstrap CI):")
    t6_rows = []
    cand_correct, cand_pnl = {}, {}
    for name in alpha_names:
        fcols = base + [name]
        ac, ap = {}, {}
        for sym in SYMBOLS:
            c, s, _ = nested_walkforward_eval(panels[sym], fcols)
            ac[sym], ap[sym] = c, s
        cand_correct[name], cand_pnl[name] = ac, ap
        # paired diffs vs BASE, pooled across symbols
        acc_d, pnl_d = [], []
        ok = True
        for sym in SYMBOLS:
            cb, cs = base_correct[sym], ac[sym]
            pb, ps = base_pnl[sym], ap[sym]
            if len(cb) == 0 or len(cs) == 0 or len(cb) != len(cs):
                ok = False
                break
            acc_d.append(cs - cb)
            pnl_d.append(ps - pb)
        if not ok:
            t6_rows.append(
                {"alpha": name, "dShACC_mean": np.nan, "dShACC_ci_lo": np.nan,
                 "dShACC_ci_hi": np.nan, "dPnL_mean": np.nan,
                 "importance_share": np.nan, "n_tail_rows": 0}
            )
            continue
        acc_d = np.concatenate(acc_d)
        pnl_d = np.concatenate(pnl_d)
        acc_m, acc_lo, acc_hi = block_bootstrap_ci(
            acc_d, BLOCK_BARS, BOOT_RESAMPLES, RNG_SEED
        )
        pnl_m, _, _ = block_bootstrap_ci(
            pnl_d, BLOCK_BARS, BOOT_RESAMPLES, RNG_SEED + 1
        )
        # importance share: mean across symbols
        shares = []
        for sym in SYMBOLS:
            sh = importance_share(panels[sym], fcols, name)
            if pd.notna(sh):
                shares.append(sh)
        imp = float(np.mean(shares)) if shares else float("nan")
        t6_rows.append(
            {
                "alpha": name,
                "dShACC_mean": round(acc_m, 5),
                "dShACC_ci_lo": round(acc_lo, 5),
                "dShACC_ci_hi": round(acc_hi, 5),
                "dPnL_mean": round(pnl_m, 4),
                "importance_share": round(imp, 4),
                "n_tail_rows": len(acc_d),
            }
        )
    t6 = pd.DataFrame(t6_rows)
    # uniform-parity importance share for a 15-feature stack
    parity = 1.0 / (len(base) + 1)
    t6["importance_above_parity"] = t6["importance_share"] > parity
    t6 = t6.sort_values("dShACC_mean", ascending=False, na_position="last")
    t6.to_csv(OUT / "T6_horserace.csv", index=False)
    print(t6.to_string(index=False))
    print(f"\n  uniform-parity importance share (15-feature stack) = "
          f"{parity:.4f}.  importance_above_parity True => the tree allocates "
          f"more than its fair share of split gain to the alpha (non-INERT).")

    # ---- T7: composite score + final single-alpha selection ----
    print("\nT7 — composite SCORE and final /102 single-alpha selection:")
    # pull Script-1 IC + Script-2 sign-stability + Script-2 redundancy
    t2 = pd.read_csv(OUT / "T2_alpha_label_ic.csv")
    t4 = pd.read_csv(OUT / "T4_ic_sign_stability.csv")
    t5 = pd.read_csv(OUT / "T5_redundancy_vs_incumbents.csv")
    ic_map = dict(zip(t2["alpha"], t2["mean_abs_ic"]))
    signcons_map = dict(zip(t2["alpha"], t2["sign_consistent_3sym"]))
    stable_map = dict(zip(t4["alpha"], t4["sign_stable_frac"]))
    redund_map = dict(zip(t5["alpha"], t5["max_abs_ic_vs_incumbent"]))

    t7_rows = []
    for _, r in t6.iterrows():
        name = r["alpha"]
        dshacc = r["dShACC_mean"]
        ci_lo = r["dShACC_ci_lo"]
        imp = r["importance_share"]
        ic = ic_map.get(name, np.nan)
        stable = stable_map.get(name, np.nan)
        redund = redund_map.get(name, np.nan)
        sign_cons = bool(signcons_map.get(name, False))
        if pd.isna(dshacc):
            score = np.nan
        else:
            # composite — each term is on its own natural scale; the held-out
            # accuracy lift dominates (it is the OOS-robust statistic), the
            # screens are tie-breakers.
            score = (
                100.0 * dshacc  # OOS-robust held-out-tail accuracy lift
                + 50.0 * max(ci_lo, -0.05)  # statistical support (floored)
                + 10.0 * (imp - parity if pd.notna(imp) else 0.0)  # non-INERT
                + 20.0 * (ic if pd.notna(ic) else 0.0)  # univariate IC screen
                + 1.0 * (stable if pd.notna(stable) else 0.0)  # sign-stability
                + (0.3 if sign_cons else 0.0)  # 3-symbol IC sign consistency
            )
        t7_rows.append(
            {
                "alpha": name,
                "note": ALPHA_NOTES[name],
                "dShACC_mean": dshacc,
                "dShACC_ci_lo": ci_lo,
                "dPnL_mean": r["dPnL_mean"],
                "importance_share": imp,
                "above_parity": bool(r["importance_above_parity"])
                if pd.notna(r["importance_above_parity"])
                else False,
                "mean_abs_ic": ic,
                "ic_sign_consistent_3sym": sign_cons,
                "ic_sign_stable_frac": stable,
                "redundancy_max_ic": redund,
                "composite_score": round(score, 4)
                if pd.notna(score)
                else np.nan,
            }
        )
    t7 = pd.DataFrame(t7_rows).sort_values(
        "composite_score", ascending=False, na_position="last"
    )
    t7.to_csv(OUT / "T7_selection.csv", index=False)
    print(t7.to_string(index=False))

    winner = t7.iloc[0]
    print("\n" + "=" * 78)
    print(f"/102 SELECTED AXIS ALPHA: {winner['alpha']}")
    print(f"  {ALPHA_NOTES[winner['alpha']]}")
    print(f"  held-out-tail dShACC mean = {winner['dShACC_mean']}  "
          f"(CI lo {winner['dShACC_ci_lo']})")
    print(f"  multivariate importance share = {winner['importance_share']}  "
          f"(parity {parity:.4f}; above_parity={winner['above_parity']})")
    print(f"  Script-1 mean |IC| = {winner['mean_abs_ic']}  "
          f"(3-sym sign-consistent={winner['ic_sign_consistent_3sym']})")
    print(f"  Script-2 IC sign-stable frac = {winner['ic_sign_stable_frac']}")
    print(f"  redundancy max |IC| vs 14 incumbents = "
          f"{winner['redundancy_max_ic']}")
    print("=" * 78)
    print("Script 3 done.  Outputs: T6_horserace.csv, T7_selection.csv")


if __name__ == "__main__":
    main()
