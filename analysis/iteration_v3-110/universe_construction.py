"""iter-v3/110 gating EDA — universe construction: tradeable edge + diversification.

The signal screen (symbol_signal_screen.py, T1-T3) measures the BROAD-population
feature->label AUC per symbol. That is necessary but not sufficient to pick a
v3 universe — the v3 backtest does not trade every candle, it trades the GATED
TAIL (the candles a confidence threshold clears). And a universe must be
DIVERSIFIED — three highly-correlated symbols give breadth ~1, not ~3
(Grinold-Kahn: IR = IC * sqrt(breadth)).

This script answers the two remaining universe-construction questions, IS-only:

  C1 — per-symbol GATED-TAIL directional hit rate. For each symbol, take the
       walk-forward 5-seed LightGBM proba, select the top/bottom confidence
       tail (the candles a v3-style threshold would actually trade), and
       measure the directional hit rate on that gated subset. /109 R1 showed
       BCH/LDO/TRX's gated tail hits BELOW 50% — this re-runs that test for
       every candidate so the universe is picked on TRADEABLE edge, not just
       broad AUC.
  C2 — cross-symbol diversification. Pairwise correlation of the per-symbol
       directional best-edge series (a strategy-PnL proxy). A good v3 universe
       has LOW pairwise PnL-proxy correlation.

Outputs:
  T4_gated_tail_edge.csv     — per-symbol gated-tail hit rate + edge proxy
  T5_pnl_correlation.csv     — pairwise PnL-proxy correlation matrix (long form)
  T6_universe_recommendation.csv — the final scored ranking + recommended set

NO CHEATING — every feature row has close_time < OOS_CUTOFF_MS; the post-cutoff
OOS is never read.
"""

from __future__ import annotations

import sys
import warnings
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import lightgbm as lgb  # noqa: E402

from _shared import (  # noqa: E402
    CANDIDATE_SYMBOLS,
    INCUMBENTS,
    V3_FEATURE_COLUMNS,
    load_labeled_symbol,
    make_walk_forward_folds,
)

OUT = Path(__file__).resolve().parent
SEEDS = (42, 123, 456, 789, 1001)

LGB_PARAMS = dict(
    objective="binary",
    num_leaves=15,
    max_depth=4,
    learning_rate=0.05,
    n_estimators=200,
    subsample=0.8,
    colsample_bytree=1.0,
    min_child_samples=20,
    reg_lambda=1.0,
    verbosity=-1,
)
# the v3 backtest trades a confidence tail — emulate it with a percentile gate.
GATE_PCTILE = 0.30  # trade the 30% most-confident candles per side


def _wf_proba(df: pd.DataFrame) -> pd.DataFrame:
    """Walk-forward 5-seed LightGBM out-of-fold proba for one symbol.

    Returns the held-out rows with columns: proba, label, best_edge, dir_real,
    close_time. dir_real = signed PnL of the better direction.
    """
    folds = make_walk_forward_folds(df, n_folds=8)
    X_all = df[V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
    y_all = (df["label"].to_numpy() > 0).astype(np.int64)
    best_edge = df["best_edge"].to_numpy(dtype=np.float64)
    ct = df["close_time"].to_numpy(dtype=np.int64)

    out_rows = []
    for tr_idx, te_idx in folds:
        X_tr, y_tr = X_all[tr_idx], y_all[tr_idx]
        X_te = X_all[te_idx]
        if len(np.unique(y_tr)) < 2:
            continue
        seed_probas = []
        for sd in SEEDS:
            params = dict(LGB_PARAMS)
            params["random_state"] = sd
            m = lgb.LGBMClassifier(**params)
            m.fit(X_tr, y_tr)
            seed_probas.append(m.predict_proba(X_te)[:, 1])
        proba = np.mean(seed_probas, axis=0)
        for k, gi in enumerate(te_idx):
            dir_real = best_edge[gi] if y_all[gi] > 0 else -best_edge[gi]
            out_rows.append(
                {
                    "close_time": ct[gi],
                    "proba": proba[k],
                    "label": int(y_all[gi]),
                    "best_edge": best_edge[gi],
                    "dir_real": dir_real,
                }
            )
    return pd.DataFrame(out_rows)


def gated_tail_edge(sym: str, proba_df: pd.DataFrame) -> dict:
    """C1 — gated-tail directional hit rate + edge for one symbol.

    The v3 model bets long when proba is high, short when proba is low. The
    gated tail = the candles whose proba is in the top/bottom GATE_PCTILE.
    The directional call is HIT if the bet's direction matches the label.
    """
    if len(proba_df) == 0:
        return {"symbol": sym, "n_gated": 0}
    p = proba_df["proba"].to_numpy()
    lab = proba_df["label"].to_numpy()  # 1 = long was best
    hi = np.quantile(p, 1.0 - GATE_PCTILE)
    lo = np.quantile(p, GATE_PCTILE)
    long_mask = p >= hi  # model bets long
    short_mask = p <= lo  # model bets short

    # directional call: long bet is correct if label==1; short bet if label==0
    long_hits = int(np.sum(lab[long_mask] == 1))
    short_hits = int(np.sum(lab[short_mask] == 0))
    n_long = int(np.sum(long_mask))
    n_short = int(np.sum(short_mask))
    n_gated = n_long + n_short
    hits = long_hits + short_hits
    hit_rate = hits / n_gated if n_gated else np.nan

    # realized directional edge on the gated tail: the model's bet PnL.
    # long bet -> +best_edge if label==1 else the realized loss; emulate the
    # 2:1-barrier book via the dir_real column already signed by the BEST dir,
    # so the model's BET pnl = dir_real if the bet matches the best dir, else
    # the mirror. Cleaner: bet_pnl = +long_pnl-proxy. We use dir_real * bet_sign
    # is wrong; instead compute from label agreement:
    de = proba_df["dir_real"].to_numpy()  # PnL of the BEST direction (signed)
    # the model's bet pnl: if it bets the best direction it earns dir_real,
    # otherwise it earns the opposite leg. dir_real already encodes the best.
    # bet correct  -> earns roughly +|edge|;  bet wrong -> earns -|edge|.
    edge_mag = np.abs(de)
    long_bet_pnl = np.where(lab[long_mask] == 1, edge_mag[long_mask], -edge_mag[long_mask])
    short_bet_pnl = np.where(lab[short_mask] == 0, edge_mag[short_mask], -edge_mag[short_mask])
    gated_pnl = np.concatenate([long_bet_pnl, short_bet_pnl]) if n_gated else np.array([])
    mean_gated_pnl = float(np.mean(gated_pnl)) if n_gated else np.nan

    # binomial p-value vs random (one-sided, hit_rate > 0.5)
    from scipy.stats import binomtest

    if n_gated:
        binom_p = float(binomtest(hits, n_gated, 0.5, alternative="greater").pvalue)
    else:
        binom_p = np.nan

    return {
        "symbol": sym,
        "n_gated": n_gated,
        "gated_hit_rate": round(hit_rate, 4) if n_gated else np.nan,
        "hit_minus_50": round(hit_rate - 0.5, 4) if n_gated else np.nan,
        "binom_p_vs_random": round(binom_p, 4) if n_gated else np.nan,
        "mean_gated_bet_pnl": round(mean_gated_pnl, 4) if n_gated else np.nan,
        "is_incumbent": sym in INCUMBENTS,
    }


def main() -> None:
    # ---- compute walk-forward proba once per symbol -------------------------
    proba_by_sym: dict[str, pd.DataFrame] = {}
    edge_series: dict[str, pd.Series] = {}
    n = len(CANDIDATE_SYMBOLS)
    for i, sym in enumerate(CANDIDATE_SYMBOLS, 1):
        print(f"[{i}/{n}] walk-forward proba {sym} ...", flush=True)
        df = load_labeled_symbol(sym)
        pdf = _wf_proba(df)
        proba_by_sym[sym] = pdf
        # PnL-proxy series indexed by close_time for the correlation screen.
        # Use the FULL IS best_edge series (label-implied directional edge) —
        # a model-free strategy-PnL proxy that does not depend on a trained
        # model, so the correlation reflects the symbol's intrinsic return
        # co-movement, not a seed artifact.
        s = df.set_index("close_time")["best_edge"]
        edge_series[sym] = s

    # ---- C1 — gated-tail edge ----------------------------------------------
    t4_rows = [gated_tail_edge(s, proba_by_sym[s]) for s in CANDIDATE_SYMBOLS]
    t4 = pd.DataFrame(t4_rows).sort_values("gated_hit_rate", ascending=False)
    t4.to_csv(OUT / "T4_gated_tail_edge.csv", index=False)

    # ---- C2 — pairwise PnL-proxy correlation -------------------------------
    edge_df = pd.DataFrame(edge_series).sort_index()
    corr_rows = []
    for a, b in combinations(CANDIDATE_SYMBOLS, 2):
        pair = edge_df[[a, b]].dropna()
        if len(pair) < 100:
            rho = np.nan
        else:
            rho = float(pair[a].corr(pair[b]))
        corr_rows.append({"sym_a": a, "sym_b": b, "pnl_proxy_corr": round(rho, 4)})
    t5 = pd.DataFrame(corr_rows)
    t5.to_csv(OUT / "T5_pnl_correlation.csv", index=False)

    # ---- T6 — final scored ranking -----------------------------------------
    # combine the signal screen (T1) + gated-tail edge (T4) into one score.
    t1 = pd.read_csv(OUT / "T1_per_symbol_signal.csv")
    merged = t1.merge(
        t4[["symbol", "n_gated", "gated_hit_rate", "binom_p_vs_random",
            "mean_gated_bet_pnl"]],
        on="symbol",
        how="left",
    )
    # composite score: standardized rank of (mean_fold_auc) + (gated_hit_rate)
    # + (-perm_p) — higher is better. Pure ranking, no magic weights.
    for col, asc in [("mean_fold_auc", False), ("gated_hit_rate", False),
                     ("perm_p_value", True)]:
        merged[f"rk_{col}"] = merged[col].rank(ascending=asc)
    merged["composite_score"] = (
        merged["rk_mean_fold_auc"]
        + merged["rk_gated_hit_rate"]
        + merged["rk_perm_p_value"]
    )
    merged = merged.sort_values("composite_score", ascending=False).reset_index(drop=True)
    merged["final_rank"] = np.arange(1, len(merged) + 1)

    # mean pairwise PnL-proxy correlation of the top-6 (diversification check)
    top6 = list(merged.head(6)["symbol"])
    sub = t5[(t5["sym_a"].isin(top6)) & (t5["sym_b"].isin(top6))]
    mean_corr_top6 = float(sub["pnl_proxy_corr"].mean())

    cols = [
        "final_rank", "symbol", "is_incumbent", "mean_fold_auc", "perm_p_value",
        "SIGNAL_GO", "gated_hit_rate", "binom_p_vs_random", "mean_gated_bet_pnl",
        "composite_score",
    ]
    merged[cols].to_csv(OUT / "T6_universe_recommendation.csv", index=False)

    print("\n=== T4 gated-tail directional hit rate (sorted) ===")
    print(t4[
        ["symbol", "is_incumbent", "n_gated", "gated_hit_rate", "hit_minus_50",
         "binom_p_vs_random", "mean_gated_bet_pnl"]
    ].to_string(index=False))

    print("\n=== T6 final composite ranking ===")
    print(merged[cols].to_string(index=False))
    print(f"\nMean pairwise PnL-proxy correlation of top-6 = {mean_corr_top6:.4f}")
    inc_corr = t5[(t5["sym_a"].isin(INCUMBENTS)) & (t5["sym_b"].isin(INCUMBENTS))]
    print(
        f"Incumbent (BCH/LDO/TRX) mean pairwise PnL-proxy correlation = "
        f"{inc_corr['pnl_proxy_corr'].mean():.4f}"
    )


if __name__ == "__main__":
    main()
