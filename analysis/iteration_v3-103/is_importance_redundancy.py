"""iter-v3/103 — EDA Script 3: IS-fold LightGBM importance + incumbent redundancy.

This is the DECISIVE IS-predictive test. The /102 failure was an importance
failure: alpha032 was LEARNED (BCH rank 8/15) and using it COLLAPSED the
multi-seed IS fit. The held-out-tail accuracy proxy could not see that. This
script asks the two questions that DO predict the multi-seed IS fit:

  T5  REDUNDANCY — pairwise |Spearman| of every surviving candidate vs the 14
      incumbent V3_FEATURE_COLUMNS, STRICTLY IS-ONLY. Gate: max |IC| < 0.70
      (the v3 hard redundancy gate, Critic Check 4). A candidate that is a
      near-duplicate of an incumbent steals colsample_bytree picks (the
      iter-v3/070 / iter-v3/023 mechanism) and harms the fit.

  T6  IS-FOLD IMPORTANCE — for each symbol, fit a LightGBM (depth-4, the v3
      architecture) on the IS panel with the 14 incumbents + the candidate as
      the 15th column, using a chronological IS train/validation split (the IS
      window is split 70/30; NO post-cutoff data, NO leakage). Report the
      candidate's gain-importance rank among 15 and its gain-importance share.
      If the candidate ranks last (15/15) or below 1/15 = 6.67% parity share in
      all symbols it is INERT (the /019/082/085/086 pattern — the model declines
      to use it, the headline barely moves). If it is LEARNED but the IS
      validation logloss WORSENS vs the 14-feature model, it is the /102
      IS-collapse pattern. Either way the importance + IS-validation-delta is
      the direct predictor of the multi-seed Optuna IS fit — NOT a held-out-tail
      accuracy statistic.

NO-CHEATING
-----------
OOS_CUTOFF_MS = 1742774400000 (2025-03-24). The LightGBM is trained AND
validated entirely within the IS window (a chronological 70/30 split of the
post-burn-in IS rows). The post-cutoff OOS is NEVER read. The triple-barrier
label is built on the full panel then IS-masked (the production-faithful
forward scan, identical to Scripts 2). This is an IN-SAMPLE diagnostic — its
job is to predict the IS fit, not to forecast OOS.

RUN:  uv run python analysis/iteration_v3-103/is_importance_redundancy.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from candidate_lib import CANDIDATE_REGISTRY  # noqa: E402
from is_predictive_screen import (  # noqa: E402
    MS_PER_DAY,
    OOS_CUTOFF_MS,
    SYMBOLS,
    TRAINING_MONTHS,
    load_full_panel,
    triple_barrier_label,
)

OUT = Path("analysis/iteration_v3-103")

# The 14 incumbent V3_FEATURE_COLUMNS (BASELINE_V3.md /059 — exact list/order).
V3_INCUMBENTS = (
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

# Candidates that passed the quartile sign-stability screen on the IS-engine
# symbols (BCH + TRX). Per the screen, only argmax_pullback_signed_20 holds one
# IC sign across all 4 BCH quartiles AND all 4 TRX quartiles; corr_gated_
# momentum_5d is the runner-up (BCH stable, TRX flips once). Both are carried
# into the importance test so the verdict is not single-candidate.
CANDIDATES_TO_TEST = ("argmax_pullback_signed_20", "corr_gated_momentum_5d")


def is_panel(symbol: str) -> pd.DataFrame:
    """Return the post-burn-in IS panel for a symbol with all candidates + the
    /059 triple-barrier label. IS-only."""
    full = load_full_panel(symbol)
    for name, (fn, _note) in CANDIDATE_REGISTRY.items():
        full[name] = fn(full).astype(float)
    full = triple_barrier_label(full)
    first_ms = int(full["open_time"].min())
    burnin_end = first_ms + TRAINING_MONTHS * 30 * MS_PER_DAY
    is_mask = (full["open_time"] >= burnin_end) & (full["open_time"] < OOS_CUTOFF_MS)
    return full[is_mask].copy().reset_index(drop=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/103 EDA Script 3 — IS-fold importance + incumbent redundancy")
    print(f"OOS_CUTOFF_MS = {OOS_CUTOFF_MS} (2025-03-24) — train + validate IS-only")
    print("=" * 78)

    panels = {sym: is_panel(sym) for sym in SYMBOLS}

    # ---- T5: redundancy vs the 14 incumbents (IS-only) ----------------------
    print("\nT5 — candidate vs incumbent pairwise |Spearman| (IS-only); gate max|IC| < 0.70:")
    t5_rows = []
    for cand in CANDIDATES_TO_TEST:
        for sym in SYMBOLS:
            d = panels[sym]
            cser = d[cand]
            for inc in V3_INCUMBENTS:
                if inc not in d.columns:
                    continue
                iser = d[inc].astype(float)
                valid = cser.notna() & iser.notna() & np.isfinite(cser) & np.isfinite(iser)
                if valid.sum() < 100:
                    continue
                ic = abs(cser[valid].rank().corr(iser[valid].rank()))
                t5_rows.append(
                    {"candidate": cand, "symbol": sym, "incumbent": inc, "abs_ic": round(ic, 4)}
                )
    t5 = pd.DataFrame(t5_rows)
    t5.to_csv(OUT / "T5_incumbent_redundancy.csv", index=False)
    for cand in CANDIDATES_TO_TEST:
        sub = t5[t5["candidate"] == cand]
        worst = sub.loc[sub["abs_ic"].idxmax()]
        print(
            f"  {cand:32s}  max|IC|={worst['abs_ic']:.4f}  "
            f"(vs {worst['incumbent']} on {worst['symbol']})  "
            f"-> {'PASS' if worst['abs_ic'] < 0.70 else 'FAIL'} the <0.70 gate"
        )

    # ---- T6: IS-fold LightGBM gain-importance (14 incumbents + candidate) ----
    print("\nT6 — IS-fold LightGBM gain-importance rank of the candidate among 15:")
    print("  depth-4 LightGBM, chronological 70/30 IS train/val split, IS-only.")
    print("  Also: IS-val binary-logloss WITH vs WITHOUT the candidate (15 vs 14 feat).")
    t6_rows = []
    for cand in CANDIDATES_TO_TEST:
        for sym in SYMBOLS:
            d = panels[sym]
            feats14 = [c for c in V3_INCUMBENTS if c in d.columns]
            feats15 = feats14 + [cand]
            # binary target: long(+1)->1, short(-1)->0  (direction classifier proxy)
            y = (d["tb_label"] == 1).astype(int)
            # chronological 70/30 IS split — no shuffling, no post-cutoff data
            split = int(len(d) * 0.70)
            tr = slice(0, split)
            va = slice(split, len(d))
            params = dict(
                objective="binary",
                metric="binary_logloss",
                num_leaves=15,  # depth-4 equivalent
                max_depth=4,
                learning_rate=0.05,
                min_child_samples=20,
                subsample=0.8,
                colsample_bytree=0.8,
                verbose=-1,
                seed=42,
            )

            def _fit_logloss(feature_list: list[str]) -> tuple[lgb.Booster, float]:
                xt = d[feature_list].iloc[tr]
                xv = d[feature_list].iloc[va]
                yt = y.iloc[tr]
                yv = y.iloc[va]
                dtr = lgb.Dataset(xt, label=yt)
                dva = lgb.Dataset(xv, label=yv, reference=dtr)
                booster = lgb.train(
                    params,
                    dtr,
                    num_boost_round=300,
                    valid_sets=[dva],
                    callbacks=[lgb.early_stopping(40, verbose=False)],
                )
                pred = booster.predict(xv)
                eps = 1e-15
                pred = np.clip(pred, eps, 1 - eps)
                ll = float(-np.mean(yv * np.log(pred) + (1 - yv) * np.log(1 - pred)))
                return booster, ll

            booster15, ll15 = _fit_logloss(feats15)
            _booster14, ll14 = _fit_logloss(feats14)

            gains = booster15.feature_importance(importance_type="gain")
            names = booster15.feature_name()
            gain_map = dict(zip(names, gains, strict=True))
            total = float(sum(gains)) or 1.0
            cand_gain = float(gain_map.get(cand, 0.0))
            order = sorted(gain_map.items(), key=lambda kv: kv[1], reverse=True)
            rank = [n for n, _g in order].index(cand) + 1
            t6_rows.append(
                {
                    "candidate": cand,
                    "symbol": sym,
                    "gain_rank_of_15": rank,
                    "gain_share_pct": round(100.0 * cand_gain / total, 3),
                    "parity_share_pct": round(100.0 / 15.0, 3),
                    "above_parity": cand_gain / total > 1.0 / 15.0,
                    "isval_logloss_15feat": round(ll15, 5),
                    "isval_logloss_14feat": round(ll14, 5),
                    "logloss_delta_15_minus_14": round(ll15 - ll14, 5),
                    "is_fit_improved": ll15 < ll14,
                }
            )
    t6 = pd.DataFrame(t6_rows)
    t6.to_csv(OUT / "T6_isfold_importance.csv", index=False)
    print(t6.to_string(index=False))

    # ---- verdict ------------------------------------------------------------
    print("\n" + "=" * 78)
    print("IS-FOLD IMPORTANCE VERDICT:")
    for cand in CANDIDATES_TO_TEST:
        sub = t6[t6["candidate"] == cand]
        n_above_parity = int(sub["above_parity"].sum())
        n_improved = int(sub["is_fit_improved"].sum())
        worst_rank = int(sub["gain_rank_of_15"].max())
        print(
            f"  {cand:32s}  above-parity {n_above_parity}/3 syms  "
            f"IS-fit-improved {n_improved}/3 syms  worst rank {worst_rank}/15"
        )
        # A candidate is IS-predictive-GO only if it is above parity in >=2 syms
        # AND the IS-val logloss improves in >=2 syms.
        go = n_above_parity >= 2 and n_improved >= 2
        print(f"  {'':32s}  -> {'IS-PREDICTIVE GO' if go else 'NOT IS-predictive (INERT or IS-harmful)'}")
    print("=" * 78)


if __name__ == "__main__":
    main()
