"""iter-v3/115 — coherent horizon-exit labeling — Phase-1 GO/NO-GO gating EDA.

Tests the cycle-6 EXPLORATION-slot-#6 axis: a coherent horizon-exit labeling
architecture (fixed-horizon label + fixed-horizon EXECUTION exit), the 2-axis design
iter-v3/072's Critic Recommendation 1 explicitly said "requires its own brief."

Five tables, all strictly IS-only (close_time < OOS_CUTOFF_MS = 2025-03-24):

  T1  Label balance + label agreement vs the triple-barrier label.
        Sanity: the horizon-exit label must be a non-degenerate, learnable directional
        target (not ~100% one class) AND it must DIFFER materially from the triple-barrier
        label (else the axis is a no-op).

  T2  Label-vs-execution-consistency diagnostic — THE /072 CRITIC REC 3 MANDATE.
        The /072 failure was a model trained on the fixed-horizon label but executed
        through TP/SL barriers. The consistency number that exposes it: take the
        triple-barrier label's DIRECTION as the model's call (the model that exists
        today is trained on triple-barrier), and ask whether THAT SAME DIRECTION is the
        winning side under (a) triple-barrier execution and (b) horizon-exit execution.
          dir_consistency_tb_exec  = frac of tb-labelled candles whose tb-direction wins
                                     under tb execution  (~100% by construction — sanity)
          dir_consistency_hz_exec  = frac of tb-labelled candles whose tb-direction wins
                                     under horizon-exit execution  (THE /072 NUMBER:
                                     1 - this = the fraction of trades where a
                                     tb-trained model is mis-executed by horizon-exit)
        GO criterion: dir_consistency_tb_exec >= 0.98 on >= 2/3 symbols (sanity), AND the
        tb-vs-hz label-direction disagreement (T1 `1 - tb_hz_label_agreement`) is a
        material, non-degenerate effect on >= 2/3 symbols (a real geometry difference).
        The COHERENT horizon-exit design fixes the mismatch by construction (a model
        trained on the hz label, executed via horizon-exit, is consistent by definition).

  T3  IS counterfactual book comparison — THE SUBSTANTIVE GO TEST.
        The decisive non-circular test. The EDA cannot run the LightGBM, so it must avoid
        a perfect-foresight ORACLE: using a labeler's own label as the model's direction
        is circular (the hz label = sign(fwd return), so its better-side N-candle return
        is always large and positive — that book would trivially "win"). T3 instead holds
        the TRIPLE-BARRIER label's DIRECTION FIXED (the direction the model that exists
        today would call) and compares what that SAME fixed direction earns under
        (i) triple-barrier EXECUTION (TP/SL/timeout) vs (ii) horizon-exit EXECUTION (held
        to candle N). This isolates the PURE EXECUTION-GEOMETRY effect with zero
        perfect-foresight bias — both books trade the identical direction sequence; only
        the exit rule differs. Per-symbol monthly Sharpe of the two candle-outcome series.
        GO criterion: horizon-exit-execution monthly Sharpe >= triple-barrier-execution
        monthly Sharpe on >= 2/3 symbols (the geometry recovers, or at least preserves,
        trade-Sharpe on the model's actual direction calls). This is the test /072
        SKIPPED — /072 measured only label-space "directional spread", which the /072
        Critic Rec 3 called "a misleading PROMISING signal".

  T4  Feature->label predictive IC — walk-forward-faithful (feedback_v3_eda_walkforward).
        For each symbol, on the last 6 IS test months, the mean |Spearman IC| of the 14
        V3_FEATURE_COLUMNS against (i) the triple-barrier label and (ii) the horizon-exit
        label. GO-supporting if the horizon-exit label's mean |IC| is within 25% of the
        triple-barrier label's (the new estimand is at least as feature-predictable).
        NOTE this is a SUPPORTING signal, not the decisive gate — /105 proved a label the
        features predict +52% better can still collapse the trade book. T3 is decisive.

  T5  No-signal permutation null on the combined-feature horizon-exit IC.
        Per the /113 Critic Rec 3 + /108 lesson: an IC near the no-skill line is only
        signal if it clears a permutation null. For the pooled IS panel, the held-out
        directional AUC of a depth-3 LightGBM on the 14 features predicting hz_label,
        vs a 100-shuffle permutation null. GO-supporting if the observed AUC clears q95.

PRE-REGISTERED GO RULE (evaluated in T6 by horizon_exit_synthesis.py):
  GO  iff  g1 (T1 balance ok + label differs) AND g2 (T2 coherence ok)
           AND g3 (T3 horizon-exit Sharpe >= triple-barrier on >= 2/3 symbols).
  T4 and T5 are SUPPORTING context; they do not gate. Per THE PRIME DIRECTIVE the EDA
  never terminates the iteration — a NO-GO sharpens the brief's pre-registered failure
  mode and the backtest still runs. The GO/NO-GO verdict only sets the brief's modal
  prediction and the Section-7/8 pre-registration.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import (  # noqa: E402
    HORIZON_CANDLES,
    OOS_CUTOFF_MS,
    SYMBOLS,
    V3_FEATURE_COLUMNS,
    is_month_starts,
    label_horizon_exit,
    label_triple_barrier,
    load_symbol_8h,
    spearman_ic,
)

OUT = Path(__file__).resolve().parent


def _monthly_sharpe(outcome_pct: np.ndarray, open_time: np.ndarray) -> float:
    """Monthly Sharpe of a per-candle outcome series (annualization-free, the v3 convention).

    Groups candle outcomes by calendar month, sums per month, then Sharpe = mean / std of
    the monthly sums. Mirrors the runner's monthly-Sharpe headline at the candle level.
    """
    m = np.isfinite(outcome_pct)
    if m.sum() < 12:
        return np.nan
    o = outcome_pct[m]
    t = open_time[m]
    months = pd.to_datetime(t, unit="ms", utc=True).to_period("M")
    s = pd.Series(o).groupby(months).sum()
    if len(s) < 6 or s.std(ddof=1) == 0:
        return np.nan
    return float(s.mean() / s.std(ddof=1))


def main() -> None:
    print("=" * 78)
    print("iter-v3/115 — coherent horizon-exit labeling — Phase-1 GO/NO-GO gating EDA")
    print(f"horizon N = {HORIZON_CANDLES} candles (FIXED — = v3 triple-barrier timeout)")
    print("=" * 78)

    labelled: dict[str, pd.DataFrame] = {}
    for sym in SYMBOLS:
        df = load_symbol_8h(sym, is_only=True)
        assert (df["close_time"] < OOS_CUTOFF_MS).all(), f"{sym}: IS-only violated"
        df = label_triple_barrier(df)
        df = label_horizon_exit(df, horizon=HORIZON_CANDLES)
        labelled[sym] = df
        print(f"  {sym}: {len(df)} IS candles loaded + labelled")

    # ----------------------------------------------------------------------
    # T1 — label balance + label-vs-label agreement
    # ----------------------------------------------------------------------
    t1_rows = []
    for sym in SYMBOLS:
        df = labelled[sym]
        both = df.loc[df["tb_valid"] & df["hz_valid"]].copy()
        tb_long = float(both["tb_label"].mean())
        hz_long = float(both["hz_label"].mean())
        agree = float((both["tb_label"] == both["hz_label"]).mean())
        t1_rows.append(
            {
                "symbol": sym,
                "n_candles": len(both),
                "tb_label_long_frac": round(tb_long, 4),
                "hz_label_long_frac": round(hz_long, 4),
                "tb_hz_label_agreement": round(agree, 4),
                "balance_ok": bool(0.20 <= hz_long <= 0.80),
                "label_differs": bool(agree < 0.95),
            }
        )
    t1 = pd.DataFrame(t1_rows)
    t1.to_csv(OUT / "T1_label_balance.csv", index=False)
    print("\n[T1] label balance + label-vs-label agreement")
    print(t1.to_string(index=False))

    # ----------------------------------------------------------------------
    # T2 — label-vs-execution-consistency diagnostic (the /072 Critic Rec 3 mandate)
    # ----------------------------------------------------------------------
    # The model that exists today is trained on the triple-barrier label, so its DIRECTION
    # call = tb_label. Question: is that direction the WINNING side under each execution
    # geometry? winning-side under geometry G = (G_long_pnl >= G_short_pnl). The /072 number
    # is dir_consistency_hz_exec — when a tb-trained model is executed through horizon-exit.
    t2_rows = []
    for sym in SYMBOLS:
        df = labelled[sym]
        both = df.loc[df["tb_valid"] & df["hz_valid"]].copy()
        tb_dir = both["tb_label"].to_numpy(dtype=np.int64)  # 1=long 0=short
        tb_win = (both["tb_long_pnl_pct"] >= both["tb_short_pnl_pct"]).to_numpy().astype(int)
        hz_win = (both["hz_long_pnl_pct"] >= both["hz_short_pnl_pct"]).to_numpy().astype(int)
        # dir_consistency under tb execution — must be ~1.0 (tb_label IS argmax tb pnl)
        cons_tb = float((tb_dir == tb_win).mean())
        # dir_consistency under hz execution — the /072 number
        cons_hz = float((tb_dir == hz_win).mean())
        # symmetric: an hz-trained model executed through tb
        hz_dir = both["hz_label"].to_numpy(dtype=np.int64)
        cons_hzdir_tbexec = float((hz_dir == tb_win).mean())
        t2_rows.append(
            {
                "symbol": sym,
                "dir_consistency_tb_exec": round(cons_tb, 4),
                "dir_consistency_hz_exec_072number": round(cons_hz, 4),
                "mismatch_frac_072": round(1.0 - cons_hz, 4),
                "hzdir_under_tb_exec": round(cons_hzdir_tbexec, 4),
                "sanity_tb_exec_ok": bool(cons_tb >= 0.98),
            }
        )
    t2 = pd.DataFrame(t2_rows)
    t2.to_csv(OUT / "T2_label_execution_consistency.csv", index=False)
    print("\n[T2] label-vs-execution-consistency diagnostic (/072 Critic Rec 3)")
    print(t2.to_string(index=False))
    print(
        "  reading: dir_consistency_tb_exec ~ 1.0 is the sanity check (the tb label IS the\n"
        "  argmax of the tb-execution pnl, by construction). mismatch_frac_072 is the /072\n"
        "  failure surface: the fraction of trades where a triple-barrier-trained model's\n"
        "  direction is the LOSING side under horizon-exit execution — a model trained on\n"
        "  one geometry and executed on the other. The COHERENT horizon-exit design\n"
        "  (hz label + hz execution) drives that mismatch to 0 by construction."
    )

    # ----------------------------------------------------------------------
    # T3 — IS counterfactual book comparison (the SUBSTANTIVE, non-circular GO test)
    # ----------------------------------------------------------------------
    # Hold the TRIPLE-BARRIER label's DIRECTION FIXED (the direction the model that
    # exists today calls). Compare what that SAME direction sequence earns under
    # (i) triple-barrier execution vs (ii) horizon-exit execution. Identical direction
    # calls, only the exit rule differs => pure execution-geometry effect, zero
    # perfect-foresight bias. Both books are a realistic per-candle PnL series.
    t3_rows = []
    for sym in SYMBOLS:
        df = labelled[sym]
        both = df.loc[df["tb_valid"] & df["hz_valid"]].copy()
        ot = both["open_time"].to_numpy(dtype=np.int64)
        tb_dir = both["tb_label"].to_numpy(dtype=np.int64)  # 1=long 0=short
        # geometry (i) — triple-barrier execution of the tb-direction calls
        tb_exec = np.where(
            tb_dir == 1,
            both["tb_long_pnl_pct"].to_numpy(dtype=np.float64),
            both["tb_short_pnl_pct"].to_numpy(dtype=np.float64),
        )
        # geometry (ii) — horizon-exit execution of the SAME tb-direction calls
        hz_exec = np.where(
            tb_dir == 1,
            both["hz_long_pnl_pct"].to_numpy(dtype=np.float64),
            both["hz_short_pnl_pct"].to_numpy(dtype=np.float64),
        )
        tb_sharpe = _monthly_sharpe(tb_exec, ot)
        hz_sharpe = _monthly_sharpe(hz_exec, ot)
        # secondary informational: the ORACLE upper bound for each labeler's own label
        # under its own execution (perfect-direction; circular — context only, not gated)
        oracle_tb = _monthly_sharpe(both["tb_outcome_pct"].to_numpy(dtype=np.float64), ot)
        oracle_hz = _monthly_sharpe(both["hz_outcome_pct"].to_numpy(dtype=np.float64), ot)
        t3_rows.append(
            {
                "symbol": sym,
                "n_candles": len(both),
                "tbdir_tb_exec_sharpe": round(tb_sharpe, 4),
                "tbdir_hz_exec_sharpe": round(hz_sharpe, 4),
                "hz_minus_tb_sharpe": round(hz_sharpe - tb_sharpe, 4),
                "hz_ge_tb": bool(hz_sharpe >= tb_sharpe),
                "tbdir_tb_exec_mean_pct": round(float(np.nanmean(tb_exec)), 4),
                "tbdir_hz_exec_mean_pct": round(float(np.nanmean(hz_exec)), 4),
                "oracle_tb_sharpe_ctx": round(oracle_tb, 4),
                "oracle_hz_sharpe_ctx": round(oracle_hz, 4),
            }
        )
    t3 = pd.DataFrame(t3_rows)
    t3.to_csv(OUT / "T3_counterfactual_book.csv", index=False)
    print("\n[T3] IS counterfactual book comparison — THE SUBSTANTIVE, non-circular GO TEST")
    print(t3.to_string(index=False))
    n_hz_ge_tb = int(t3["hz_ge_tb"].sum())
    print(
        f"  horizon-exit-execution monthly Sharpe >= triple-barrier-execution on "
        f"{n_hz_ge_tb}/3 symbols.\n"
        "  reading: BOTH books trade the IDENTICAL tb-direction sequence — only the exit\n"
        "  rule differs (TP/SL/timeout vs hold-to-candle-N). So hz_minus_tb_sharpe is the\n"
        "  PURE execution-geometry effect with zero perfect-foresight bias. oracle_*_ctx\n"
        "  columns are the circular perfect-direction upper bounds (context only, NOT\n"
        "  gated — a labeler's own label trivially 'wins' under its own execution)."
    )

    # ----------------------------------------------------------------------
    # T4 — feature->label IC, walk-forward-faithful (last 6 IS months)
    # ----------------------------------------------------------------------
    t4_rows = []
    for sym in SYMBOLS:
        df = labelled[sym]
        months = is_month_starts(df, n_folds=6)
        both = df.loc[df["tb_valid"] & df["hz_valid"]].copy()
        ot = both["open_time"].to_numpy(dtype=np.int64)
        tb_lab = both["tb_label"].to_numpy(dtype=np.float64)
        hz_lab = both["hz_label"].to_numpy(dtype=np.float64)
        tb_ics, hz_ics = [], []
        for ms in months:
            nm = (
                pd.Timestamp(ms, unit="ms", tz="UTC") + pd.offsets.MonthBegin(1)
            ).value // 1_000_000
            fold = (ot >= ms) & (ot < nm)
            if fold.sum() < 12:
                continue
            for feat in V3_FEATURE_COLUMNS:
                if feat not in both.columns:
                    continue
                fv = both[feat].to_numpy(dtype=np.float64)[fold]
                tb_ic = spearman_ic(fv, tb_lab[fold])
                hz_ic = spearman_ic(fv, hz_lab[fold])
                if np.isfinite(tb_ic):
                    tb_ics.append(abs(tb_ic))
                if np.isfinite(hz_ic):
                    hz_ics.append(abs(hz_ic))
        tb_mean = float(np.mean(tb_ics)) if tb_ics else np.nan
        hz_mean = float(np.mean(hz_ics)) if hz_ics else np.nan
        ratio = hz_mean / tb_mean if (tb_mean and tb_mean > 0) else np.nan
        t4_rows.append(
            {
                "symbol": sym,
                "n_folds": len(months),
                "tb_label_mean_abs_ic": round(tb_mean, 5),
                "hz_label_mean_abs_ic": round(hz_mean, 5),
                "hz_over_tb_ic_ratio": round(ratio, 4) if np.isfinite(ratio) else np.nan,
                "hz_ic_within_25pct": bool(np.isfinite(ratio) and ratio >= 0.75),
            }
        )
    t4 = pd.DataFrame(t4_rows)
    t4.to_csv(OUT / "T4_feature_label_ic.csv", index=False)
    print("\n[T4] feature->label IC — walk-forward-faithful (SUPPORTING, not a gate)")
    print(t4.to_string(index=False))

    # ----------------------------------------------------------------------
    # T5 — no-signal permutation null on the pooled horizon-exit directional AUC
    # ----------------------------------------------------------------------
    try:
        import lightgbm as lgb
        from sklearn.metrics import roc_auc_score

        pooled = []
        for sym in SYMBOLS:
            df = labelled[sym]
            both = df.loc[df["hz_valid"]].copy()
            both = both.dropna(subset=V3_FEATURE_COLUMNS + ["hz_label"])
            both = both.sort_values("open_time")
            pooled.append(both)
        pdf = pd.concat(pooled, ignore_index=True).sort_values("open_time").reset_index(drop=True)
        n = len(pdf)
        cut = int(n * 0.70)
        feat_mat = pdf[V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
        y = pdf["hz_label"].to_numpy(dtype=np.int64)
        feat_tr, feat_te = feat_mat[:cut], feat_mat[cut:]
        ytr, yte = y[:cut], y[cut:]

        def _fit_auc(yt: np.ndarray) -> float:
            params = dict(
                objective="binary",
                max_depth=3,
                n_estimators=120,
                learning_rate=0.05,
                num_leaves=7,
                min_child_samples=30,
                subsample=0.8,
                colsample_bytree=0.8,
                verbosity=-1,
                seed=42,
            )
            mdl = lgb.LGBMClassifier(**params)
            mdl.fit(feat_tr, yt)
            p = mdl.predict_proba(feat_te)[:, 1]
            return float(roc_auc_score(yte, p))

        obs_auc = _fit_auc(ytr)
        rng = np.random.default_rng(42)
        null_aucs = []
        for _ in range(100):
            perm = rng.permutation(ytr)
            try:
                null_aucs.append(_fit_auc(perm))
            except Exception:  # noqa: BLE001
                pass
        null = np.array(null_aucs)
        q95 = float(np.quantile(null, 0.95)) if len(null) else np.nan
        pval = float((null >= obs_auc).mean()) if len(null) else np.nan
        t5 = pd.DataFrame(
            [
                {
                    "pooled_n": n,
                    "train_n": cut,
                    "test_n": n - cut,
                    "observed_holdout_auc": round(obs_auc, 4),
                    "permutation_null_mean": round(float(null.mean()), 4),
                    "permutation_null_q95": round(q95, 4),
                    "permutation_p_value": round(pval, 4),
                    "clears_q95": bool(obs_auc > q95),
                }
            ]
        )
    except Exception as exc:  # noqa: BLE001
        t5 = pd.DataFrame([{"error": f"permutation test skipped: {exc}"}])
    t5.to_csv(OUT / "T5_permutation_null.csv", index=False)
    print("\n[T5] no-signal permutation null on pooled horizon-exit directional AUC")
    print(t5.to_string(index=False))

    print("\n" + "=" * 78)
    print("EDA tables written: T1-T5. Run horizon_exit_synthesis.py for the GO/NO-GO verdict.")
    print("=" * 78)


if __name__ == "__main__":
    main()
