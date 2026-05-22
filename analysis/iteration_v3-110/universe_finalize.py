"""iter-v3/110 EDA — universe finalization: the candidate-set bake-off.

The signal screen (T1-T3), the construction screen (T4-T6), and the
2:1-barrier gated book (T7-T8) converge on a clear ordering — but two
candidate v3 universes deserve a head-to-head before the brief locks one:

  U_A — CRV + AAVE + GRT          (3 symbols, ALL novel, same count as the
                                   incumbent; ADA dropped for dead-path
                                   caution — ADA is a v2 dead-path note and
                                   a closed v3 swap candidate /078)
  U_B — CRV + AAVE + GRT + ADA    (4 symbols, the T8 leave-one-out winner
                                   top5_minus_GALA; ADA carries fresh
                                   5-seed positive evidence in THIS EDA)

This script reads the committed T7 per-symbol books and reports both
universes' aggregate IS-only gated books side-by-side with the incumbent, so
the brief picks on numbers. It also reports the per-symbol signal-vs-null
margin so the brief can state honestly how thin the edge is.

Outputs:
  T9_final_bakeoff.csv  — U_A vs U_B vs incumbent, aggregate gated book
  T10_signal_margin.csv — per-symbol AUC margin over the permutation q95 floor

NO CHEATING — reads only IS-only artifacts; OOS never touched.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import lightgbm as lgb  # noqa: E402

from _shared import (  # noqa: E402
    INCUMBENTS,
    V3_FEATURE_COLUMNS,
    load_labeled_symbol,
    make_walk_forward_folds,
)

OUT = Path(__file__).resolve().parent
SEEDS = (42, 123, 456, 789, 1001)
GATE_PCTILE = 0.30
LGB_PARAMS = dict(
    objective="binary", num_leaves=15, max_depth=4, learning_rate=0.05,
    n_estimators=200, subsample=0.8, colsample_bytree=1.0,
    min_child_samples=20, reg_lambda=1.0, verbosity=-1,
)

U_A = ["CRVUSDT", "AAVEUSDT", "GRTUSDT"]
U_B = ["CRVUSDT", "AAVEUSDT", "GRTUSDT", "ADAUSDT"]
ALL_NEEDED = sorted(set(U_A) | set(U_B) | set(INCUMBENTS))


def gated_trades(sym: str) -> pd.DataFrame:
    """Barrier-faithful gated-tail trade frame for one symbol (close_time, pnl)."""
    df = load_labeled_symbol(sym)
    folds = make_walk_forward_folds(df, n_folds=8)
    X_all = df[V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
    y_all = (df["label"].to_numpy() > 0).astype(np.int64)
    long_pnl = df["long_pnl"].to_numpy(dtype=np.float64)
    short_pnl = df["short_pnl"].to_numpy(dtype=np.float64)
    ct = df["close_time"].to_numpy(dtype=np.int64)
    trades = []
    for tr_idx, te_idx in folds:
        X_tr, y_tr = X_all[tr_idx], y_all[tr_idx]
        if len(np.unique(y_tr)) < 2:
            continue
        probas = []
        for sd in SEEDS:
            params = dict(LGB_PARAMS)
            params["random_state"] = sd
            m = lgb.LGBMClassifier(**params)
            m.fit(X_tr, y_tr)
            probas.append(m.predict_proba(X_all[te_idx])[:, 1])
        proba = np.mean(probas, axis=0)
        hi = np.quantile(proba, 1.0 - GATE_PCTILE)
        lo = np.quantile(proba, GATE_PCTILE)
        for k, gi in enumerate(te_idx):
            if proba[k] >= hi:
                trades.append({"close_time": ct[gi], "pnl": long_pnl[gi]})
            elif proba[k] <= lo:
                trades.append({"close_time": ct[gi], "pnl": short_pnl[gi]})
    return pd.DataFrame(trades)


def book_metrics(syms: list[str], frames: dict[str, pd.DataFrame], name: str) -> dict:
    allt = pd.concat([frames[s] for s in syms], ignore_index=True)
    pnl = allt["pnl"].to_numpy()
    wins = int(np.sum(pnl > 0))
    nn = len(pnl)
    gw = float(np.sum(pnl[pnl > 0]))
    gl = float(-np.sum(pnl[pnl < 0]))
    pf = gw / gl if gl > 0 else np.nan
    allt["month"] = pd.to_datetime(allt["close_time"], unit="ms").dt.to_period("M")
    monthly = allt.groupby("month")["pnl"].sum()
    m_sharpe = (
        float(monthly.mean() / monthly.std() * np.sqrt(12))
        if monthly.std() > 1e-9 else np.nan
    )
    # per-symbol concentration of total PnL
    psum = {s: float(frames[s]["pnl"].sum()) for s in syms}
    tot = sum(psum.values())
    top_share = (
        max(abs(v) for v in psum.values()) / abs(tot) * 100.0
        if abs(tot) > 1e-9 else np.nan
    )
    return {
        "universe": name,
        "symbols": "+".join(s.replace("USDT", "") for s in syms),
        "n_symbols": len(syms),
        "n_trades": nn,
        "win_rate": round(wins / nn, 4),
        "total_pnl": round(tot, 2),
        "profit_factor": round(pf, 4) if not np.isnan(pf) else np.nan,
        "monthly_sharpe_proxy": round(m_sharpe, 4) if not np.isnan(m_sharpe) else np.nan,
        "top_symbol_pnl_share_pct": round(top_share, 1) if not np.isnan(top_share) else np.nan,
        "n_months": int(monthly.shape[0]),
    }


def main() -> None:
    frames: dict[str, pd.DataFrame] = {}
    for i, sym in enumerate(ALL_NEEDED, 1):
        print(f"[{i}/{len(ALL_NEEDED)}] gated trades {sym} ...", flush=True)
        frames[sym] = gated_trades(sym)

    t9 = pd.DataFrame([
        book_metrics(list(INCUMBENTS), frames, "incumbent_BCH_LDO_TRX"),
        book_metrics(U_A, frames, "U_A_CRV_AAVE_GRT"),
        book_metrics(U_B, frames, "U_B_CRV_AAVE_GRT_ADA"),
    ])
    t9.to_csv(OUT / "T9_final_bakeoff.csv", index=False)

    # T10 — per-symbol signal margin over the permutation q95 no-signal floor
    t1 = pd.read_csv(OUT / "T1_per_symbol_signal.csv")
    relevant = sorted(set(U_A) | set(U_B) | set(INCUMBENTS))
    t10 = t1[t1["symbol"].isin(relevant)][
        ["symbol", "is_incumbent", "mean_fold_auc", "perm_null_q50",
         "perm_null_q95", "perm_p_value", "pos_folds_of_8", "SIGNAL_GO"]
    ].copy()
    t10["auc_margin_over_q95"] = (t10["mean_fold_auc"] - t10["perm_null_q95"]).round(4)
    t10["auc_margin_over_q50"] = (t10["mean_fold_auc"] - t10["perm_null_q50"]).round(4)
    t10 = t10.sort_values("auc_margin_over_q50", ascending=False)
    t10.to_csv(OUT / "T10_signal_margin.csv", index=False)

    print("\n=== T9 final universe bake-off (IS-only, gated, 2:1-barrier book) ===")
    print(t9.to_string(index=False))
    print("\n=== T10 per-symbol signal margin over the permutation no-signal floor ===")
    print(t10.to_string(index=False))


if __name__ == "__main__":
    main()
