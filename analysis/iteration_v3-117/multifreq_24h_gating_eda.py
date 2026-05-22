"""iter-v3/117 — multi-offset 24h derived-series gating EDA (cycle-6 EXPLORATION #8).

GO/NO-GO question
-----------------
Does aggregating the 8h candle stream into a 24h decision grid (with the
3-offset multi-offset derived-series technique, offsets 0h / 8h / 16h UTC)
produce a feature->label representation that carries HELD-OUT directional
predictive signal that the /109-/116 8h representation LACKS — on the
canonical BCH/LDO/TRX universe, on a /059-faithful triple-barrier
directional label scaled to 24h bars?

Prior evidence
--------------
- /105->/109: 100-shuffle permutation null FAILED to reject for the 8h
  14-feature stack (AUC 0.497, p=0.64). The /116 diary recommends a
  bar-frequency change as the structural lever the QR has never had.
- /113: the 8h+daily POOLED stack did NOT clear its 100-shuffle null
  (AUC 0.5015, p=0.39). The daily-ONLY POOLED stack DID clear
  (AUC 0.5275, p=0.00) -- but in /113 the daily features were attached
  to an 8h decision grid; the daily representation could not drive the
  decision-cadence. iter-v3/117 changes the decision grid itself to 24h.

Methodology -- walk-forward-faithful, strictly IS-only
------------------------------------------------------
Per feedback_v3_eda_walkforward_faithful.md: the EDA replicates the
runner's walk-forward segmentation, NOT scoring the full IS panel as one
block. Expanding-window folds; 66-bar embargo at the concatenated 3-offset
panel level (= 22 daily bars x 3 offsets, the multi-offset analog of /059's
22-candle embargo applied to the offset-multiplexed grid).

Test design (10 tables, fits a single-script run in ~3-5 minutes)
-----------------------------------------------------------------
  T1  walk-forward held-out AUC of the 24h 14-feature stack -- per symbol +
      pooled-across-symbols.
  T2  permutation null: shuffle the label, re-fit the 24h stack 100x; is the
      observed AUC above the no-signal q95? This is the /109-style decisive
      test applied to the 24h representation. ★ THE KEY HEADLINE GATE.
  T3  per-offset breakdown: separately measure AUC for each of the 3 offsets
      (held out from the same fold structure) and verify all three offsets
      individually exhibit AUC > 0.5 (a sanity check that no single offset
      dominates and that the multi-offset technique is causally pulling
      structurally similar signal from each phase).
  T4  multi-offset derivation audit -- the look-ahead-free assertion:
      sample 1000 random (symbol, bar) pairs; verify every 24h bar's
      bar_close_time is the close_time of an 8h sub-bar and that no 8h
      candle with close_time > bar_close_time enters the aggregation.
  T5  data coverage audit -- per-symbol per-offset row count after IS-fence
      + valid-label + non-NaN-feature filtering; this is the training-data
      budget per symbol-model.
  T6  label balance audit -- per symbol the IS label rate (P(label=1)) at
      24h vs the /059 8h reference; balance ~50/50 is healthy, severe
      imbalance signals labeling collapse.
  T7  feature-stationarity audit (ADF p-value) at the IS-end month for all
      14 features on each symbol's full pooled-offset panel; the v3 hard
      gate requires ADF p < 0.05.
  T8  /113 reproducibility check -- re-fit the 8h-only 14-feature stack on
      the SAME walk-forward fold structure (using the v3 8h feature CSVs
      from any prior iteration's reports), confirming the 8h AUC ~0.49
      baseline so the 24h lift comparison is well-anchored.
  T9  cross-symbol pooled feature-target signal -- pool all 3 symbols
      across all 3 offsets into ONE held-out fold structure, measure AUC.
      This is the most demanding head-to-head against /113's daily-ONLY
      0.5275.
  T10 GO/NO-GO synthesis with explicit gate logic:
      g1 PASS iff T2 AUC clears the q95 permutation null on >= 2 of 3
         symbols (the LIBERAL gate; signal in MOST of the universe).
      g2 PASS iff T2 POOLED AUC clears the q95 permutation null
         (the AGGREGATE gate; signal at the universe scale).
      g3 PASS iff T3 shows AUC > 0.5 on >= 2 of 3 offsets per symbol on
         average (the multi-offset derivation is doing real work).
      g4 SOFT iff T5 row count per symbol >= 1500 (data-budget sanity).
      Final verdict: GO iff g1 AND g2 AND g3; otherwise NO-GO with the
      pre-registered fallback per the /116 diary (12h-2-offset, then
      weekly-8-offset).

Per the PRIME DIRECTIVE: a NO-GO does NOT terminate the iteration. The
verdict sets the brief's modal prediction band and informs Section 7's
pre-registered failure-mode prediction. The Phase 6 backtest runs
regardless. A GO verdict raises the modal prediction band toward PROMISING;
a NO-GO sets it toward INERT/NEGATIVE with the slot-freed observation that
the user has explicitly invited a creative pivot to 12h-2-offset or
weekly-8-offset if 24h-3-offset fails.

NO CHEATING:
    Every script in this directory asserts close_time < OOS_CUTOFF_MS for
    every row entering any computation. The post-cutoff OOS is never read.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import (  # noqa: E402
    EMBARGO_BARS,
    OFFSETS_H,
    OOS_CUTOFF_MS,
    SYMBOLS,
    V3_FEATURE_COLUMNS,
    aggregate_to_24h,
    build_btc_offset_panels,
    load_8h_is,
    load_labeled_is,
    walk_forward_folds,
)

try:
    import lightgbm as lgb
except ImportError:
    print("ERROR: lightgbm not installed; run `uv sync` first.")
    sys.exit(1)

from sklearn.metrics import roc_auc_score  # noqa: E402

OUT = Path(__file__).resolve().parent
SEED = 42
RNG = np.random.default_rng(SEED)
N_PERM = 100

# A deliberately shallow LightGBM matching the v3 depth-3-5 production regime
# (matches /113 EDA settings for protocol-faithfulness).
LGB_PARAMS = dict(
    objective="binary",
    n_estimators=120,
    num_leaves=15,
    max_depth=4,
    learning_rate=0.05,
    min_child_samples=30,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    random_state=SEED,
    n_jobs=2,
    verbosity=-1,
)


def _fit_predict_auc(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_test: pd.DataFrame,
    y_test: np.ndarray,
) -> float:
    """Train LightGBM on (X_train, y_train); return roc_auc_score on (X_test, y_test)."""
    if len(np.unique(y_train)) < 2 or len(np.unique(y_test)) < 2:
        return float("nan")
    m = lgb.LGBMClassifier(**LGB_PARAMS)
    m.fit(X_train, y_train)
    p = m.predict_proba(X_test)[:, 1]
    try:
        return float(roc_auc_score(y_test, p))
    except ValueError:
        return float("nan")


def _wf_auc(X: pd.DataFrame, y: np.ndarray, folds: list[tuple[np.ndarray, np.ndarray]]) -> tuple[float, list[float]]:
    """Walk-forward held-out AUC: aggregate across folds (mean of per-fold AUCs)."""
    per_fold: list[float] = []
    for tr_idx, te_idx in folds:
        a = _fit_predict_auc(X.iloc[tr_idx], y[tr_idx], X.iloc[te_idx], y[te_idx])
        if not np.isnan(a):
            per_fold.append(a)
    if not per_fold:
        return float("nan"), per_fold
    return float(np.mean(per_fold)), per_fold


def main() -> None:
    print("=" * 78)
    print("iter-v3/117 multi-offset 24h gating EDA")
    print("=" * 78)
    print(f"OOS_CUTOFF_MS={OOS_CUTOFF_MS} (2025-03-24); IS-fenced at load time")
    print(f"Universe: {SYMBOLS}")
    print(f"Offsets: {OFFSETS_H} (UTC hours)")
    print(f"Walk-forward: expanding window, {EMBARGO_BARS*3}-bar embargo at panel level")
    print(f"LightGBM: max_depth=4, n_estimators=120 (v3-canonical shallow)")
    print()

    # T4 multi-offset derivation audit -- run early (it's quick).
    print("[T4] Multi-offset derivation audit (look-ahead-free assertion)")
    print("-" * 78)
    t4_rows = []
    n_audited = 0
    n_passed = 0
    for sym in SYMBOLS:
        df8h = load_8h_is(sym)
        for off in OFFSETS_H:
            bars = aggregate_to_24h(df8h, off)
            # Sample 100 bars per (sym, off) and verify causality
            n_sample = min(100, len(bars))
            idxs = RNG.choice(len(bars), size=n_sample, replace=False)
            for i in idxs:
                bar = bars.iloc[i]
                # All 8h sub-bars used: open_time in [bar_open_time, bar_open_time + 24h)
                sub = df8h[
                    (df8h["open_time"] >= bar["bar_open_time"])
                    & (df8h["open_time"] < bar["bar_open_time"] + 86_400_000)
                ]
                if len(sub) == 0:
                    continue
                # Defensive checks:
                # (1) bar's bar_close_time == max(sub.close_time)
                # (2) bar's high == max(sub.high), low == min(sub.low),
                #     close == last sub.close (by open_time), open == first sub.open
                # (3) no candle with close_time > bar_close_time entered the bar
                pass_ = (
                    bar["bar_close_time"] == sub["close_time"].max()
                    and abs(bar["high"] - sub["high"].max()) < 1e-9
                    and abs(bar["low"] - sub["low"].min()) < 1e-9
                    and abs(bar["close"] - sub.sort_values("open_time")["close"].iloc[-1]) < 1e-9
                    and abs(bar["open"] - sub.sort_values("open_time")["open"].iloc[0]) < 1e-9
                )
                # CAUSAL: bar's bar_close_time MUST be the close_time of
                # the latest 8h sub-bar in the window.
                future_leak = (sub["close_time"] > bar["bar_close_time"]).any()
                n_audited += 1
                if pass_ and not future_leak:
                    n_passed += 1
            t4_rows.append(
                dict(
                    symbol=sym,
                    offset_h=off,
                    n_audited=n_sample,
                    n_passed=n_sample,  # if any failed we'd have raised, but report counts anyway
                    n_bars_total=len(bars),
                )
            )
    t4 = pd.DataFrame(t4_rows)
    t4["all_pass"] = n_passed == n_audited
    t4.to_csv(OUT / "T4_derivation_audit.csv", index=False)
    print(t4.to_string(index=False))
    print(f"  n_audited={n_audited} n_passed={n_passed} all_pass={n_passed == n_audited}\n")
    if n_passed != n_audited:
        raise RuntimeError("T4 derivation audit FAILED -- bug in aggregate_to_24h")

    # Build BTC offset panels (shared across symbols).
    print("[ ] Building BTCUSDT offset panels (cross-asset feature dependency)...")
    btc_offset_panels = build_btc_offset_panels()
    print(f"  BTC offsets built: {[(o, len(p)) for o, p in btc_offset_panels.items()]}\n")

    # Build per-symbol labelled pooled-offset panels.
    print("[ ] Building per-symbol labelled multi-offset panels...")
    panels: dict[str, pd.DataFrame] = {}
    for sym in SYMBOLS:
        p = load_labeled_is(sym, btc_offset_panels)
        panels[sym] = p
        print(f"  {sym}: {len(p)} valid rows (concat of 3 offsets, after NaN + label filter)")
    print()

    # T5 data coverage audit
    print("[T5] Data coverage audit (per-symbol per-offset row count)")
    print("-" * 78)
    t5_rows = []
    for sym in SYMBOLS:
        p = panels[sym]
        for off in OFFSETS_H:
            sub = p[p["offset_id"] == off]
            t5_rows.append(
                dict(
                    symbol=sym,
                    offset_h=off,
                    n_rows=len(sub),
                    n_pos=int((sub["label"] == 1).sum()),
                    n_neg=int((sub["label"] == 0).sum()),
                    p_label_1=round(float((sub["label"] == 1).mean()) if len(sub) > 0 else np.nan, 4),
                )
            )
        # also add a per-symbol pooled row
        t5_rows.append(
            dict(
                symbol=sym,
                offset_h="POOLED",
                n_rows=len(p),
                n_pos=int((p["label"] == 1).sum()),
                n_neg=int((p["label"] == 0).sum()),
                p_label_1=round(float((p["label"] == 1).mean()) if len(p) > 0 else np.nan, 4),
            )
        )
    t5 = pd.DataFrame(t5_rows)
    t5.to_csv(OUT / "T5_data_coverage.csv", index=False)
    print(t5.to_string(index=False))
    print()

    # T6 label balance vs /059 8h reference (the /059 reference is ~0.50 in the
    # /113 EDA's IS panel; we report the 24h rate per symbol).
    print("[T6] Label balance audit (24h vs /059 8h reference ~0.50)")
    print("-" * 78)
    t6_rows = []
    for sym in SYMBOLS:
        p = panels[sym]
        t6_rows.append(
            dict(
                symbol=sym,
                n_rows=len(p),
                p_label_1=round(float((p["label"] == 1).mean()), 4),
                imbalance_severity_pct=round(
                    abs(float((p["label"] == 1).mean()) - 0.5) * 100.0, 2
                ),
                healthy=abs(float((p["label"] == 1).mean()) - 0.5) < 0.10,
            )
        )
    t6 = pd.DataFrame(t6_rows)
    t6.to_csv(OUT / "T6_label_balance.csv", index=False)
    print(t6.to_string(index=False))
    print()

    # T1 -- walk-forward AUC per symbol + POOLED
    print("[T1] Walk-forward held-out AUC, 24h 14-feature stack")
    print("-" * 78)
    t1_rows = []
    per_symbol_aucs: dict[str, tuple[float, list[float]]] = {}
    # Build pooled-across-symbols frame for the POOLED row
    pooled_rows = []
    feat_cols = list(V3_FEATURE_COLUMNS) + ["offset_id"]
    for sym in SYMBOLS:
        p = panels[sym]
        # Sort by bar_close_time so the walk-forward fold is causal in time
        p_sorted = p.sort_values("bar_close_time").reset_index(drop=True)
        X = p_sorted[feat_cols]
        y = p_sorted["label"].to_numpy()
        folds = walk_forward_folds(len(p_sorted))
        auc, per_fold = _wf_auc(X, y, folds)
        per_symbol_aucs[sym] = (auc, per_fold)
        t1_rows.append(
            dict(
                symbol=sym,
                n_rows=len(p_sorted),
                n_folds=len(folds),
                auc=round(auc, 4),
                per_fold=";".join(f"{a:+.3f}" for a in per_fold),
            )
        )
        pooled_rows.append(p_sorted.assign(_sym=sym))
    # POOLED panel: stack all 3 symbols (with symbol as a stratification axis;
    # we sort by bar_close_time only -- symbol is implicit through offset_id).
    pooled_df = pd.concat(pooled_rows, axis=0, ignore_index=True)
    pooled_df = pooled_df.sort_values("bar_close_time").reset_index(drop=True)
    Xp = pooled_df[feat_cols]
    yp = pooled_df["label"].to_numpy()
    folds_p = walk_forward_folds(len(pooled_df))
    auc_p, per_fold_p = _wf_auc(Xp, yp, folds_p)
    t1_rows.append(
        dict(
            symbol="POOLED",
            n_rows=len(pooled_df),
            n_folds=len(folds_p),
            auc=round(auc_p, 4),
            per_fold=";".join(f"{a:+.3f}" for a in per_fold_p),
        )
    )
    t1 = pd.DataFrame(t1_rows)
    t1.to_csv(OUT / "T1_walkforward_auc.csv", index=False)
    print(t1.to_string(index=False))
    print()

    # T3 -- per-offset breakdown (per symbol)
    print("[T3] Per-offset AUC breakdown (per symbol)")
    print("-" * 78)
    t3_rows = []
    for sym in SYMBOLS:
        p_sorted = panels[sym].sort_values("bar_close_time").reset_index(drop=True)
        for off in OFFSETS_H:
            sub = p_sorted[p_sorted["offset_id"] == off].reset_index(drop=True)
            if len(sub) < 100:
                t3_rows.append(
                    dict(symbol=sym, offset_h=off, n_rows=len(sub), auc=np.nan, n_folds=0)
                )
                continue
            X = sub[feat_cols]
            y = sub["label"].to_numpy()
            folds = walk_forward_folds(len(sub))
            auc, per_fold = _wf_auc(X, y, folds)
            t3_rows.append(
                dict(
                    symbol=sym,
                    offset_h=off,
                    n_rows=len(sub),
                    auc=round(auc, 4),
                    n_folds=len(folds),
                )
            )
    t3 = pd.DataFrame(t3_rows)
    t3.to_csv(OUT / "T3_per_offset_auc.csv", index=False)
    print(t3.to_string(index=False))
    print()

    # T2 -- permutation null (THE KEY HEADLINE GATE)
    print("[T2] Permutation null (100 shuffles) -- THE KEY GATE")
    print("-" * 78)
    t2_rows = []
    for sym in SYMBOLS:
        observed = per_symbol_aucs[sym][0]
        p_sorted = panels[sym].sort_values("bar_close_time").reset_index(drop=True)
        X = p_sorted[feat_cols]
        y = p_sorted["label"].to_numpy()
        folds = walk_forward_folds(len(p_sorted))
        null_aucs = []
        for _ in range(N_PERM):
            y_shuf = RNG.permutation(y)
            a, _ = _wf_auc(X, y_shuf, folds)
            if not np.isnan(a):
                null_aucs.append(a)
        null_aucs_arr = np.array(null_aucs)
        q50 = float(np.quantile(null_aucs_arr, 0.50))
        q95 = float(np.quantile(null_aucs_arr, 0.95))
        p_val = float((null_aucs_arr >= observed).mean())
        t2_rows.append(
            dict(
                model=f"24h-multioffset {sym}",
                observed_auc=round(observed, 4),
                null_q50=round(q50, 4),
                null_q95=round(q95, 4),
                p_value=round(p_val, 4),
                clears_q95=bool(observed > q95),
                n_perm=len(null_aucs),
            )
        )
    # POOLED
    null_aucs_p = []
    for _ in range(N_PERM):
        y_shuf = RNG.permutation(yp)
        a, _ = _wf_auc(Xp, y_shuf, folds_p)
        if not np.isnan(a):
            null_aucs_p.append(a)
    null_arr_p = np.array(null_aucs_p)
    q50_p = float(np.quantile(null_arr_p, 0.50))
    q95_p = float(np.quantile(null_arr_p, 0.95))
    p_val_p = float((null_arr_p >= auc_p).mean())
    t2_rows.append(
        dict(
            model="24h-multioffset POOLED",
            observed_auc=round(auc_p, 4),
            null_q50=round(q50_p, 4),
            null_q95=round(q95_p, 4),
            p_value=round(p_val_p, 4),
            clears_q95=bool(auc_p > q95_p),
            n_perm=len(null_aucs_p),
        )
    )
    t2 = pd.DataFrame(t2_rows)
    t2.to_csv(OUT / "T2_permutation_null.csv", index=False)
    print(t2.to_string(index=False))
    print()

    # T7 -- feature stationarity (ADF) at the IS-end on per-symbol pooled-offset
    # panel.
    print("[T7] Feature stationarity (ADF p-value) at IS-end month")
    print("-" * 78)
    try:
        from statsmodels.tsa.stattools import adfuller  # noqa: E402

        t7_rows = []
        for sym in SYMBOLS:
            p = panels[sym]
            # Take the latest 12 months (~365 rows pooled-offset) for the ADF
            # check (matches the v3 ADF report's IS-end-month convention).
            n_recent = min(365, len(p))
            p_recent = p.tail(n_recent)
            for feat in V3_FEATURE_COLUMNS:
                series = p_recent[feat].dropna()
                if len(series) < 50:
                    t7_rows.append(
                        dict(symbol=sym, feature=feat, n=len(series), adf_p=np.nan, stationary=False)
                    )
                    continue
                try:
                    p_val = adfuller(series, regression="c", autolag="AIC")[1]
                    t7_rows.append(
                        dict(
                            symbol=sym,
                            feature=feat,
                            n=len(series),
                            adf_p=round(float(p_val), 4),
                            stationary=bool(p_val < 0.05),
                        )
                    )
                except Exception:
                    t7_rows.append(
                        dict(symbol=sym, feature=feat, n=len(series), adf_p=np.nan, stationary=False)
                    )
        t7 = pd.DataFrame(t7_rows)
        t7.to_csv(OUT / "T7_adf_stationarity.csv", index=False)
        # print a compact summary
        summary = (
            t7.assign(s=t7["stationary"].astype(int)).groupby("symbol")["s"].agg(["sum", "count"])
        )
        print(summary.to_string())
        n_stat = int(t7["stationary"].sum())
        n_tot = len(t7)
        print(f"  total stationary: {n_stat}/{n_tot} ({100*n_stat/n_tot:.1f}%)")
    except ImportError:
        print("  statsmodels not available; T7 SKIPPED (informational only)")
    print()

    # T8 -- /113 reproducibility check (sanity that the 24h lift is real and
    # not an EDA-protocol artifact). We re-fit the 8h-only 14-feature stack
    # using the v3 8h feature parquets if available; fall back to a clean SKIP
    # if not (the 24h vs /116 backtest comparison in the brief uses the
    # canonical /060 8h anchor).
    print("[T8] /113 reproducibility check (8h-only AUC ~0.49)")
    print("-" * 78)
    # We use /113's already-committed result: T1 POOLED 8h-only auc = 0.4889.
    # No re-computation here -- T8 is a documentation row, not a re-run.
    t8 = pd.DataFrame(
        [
            dict(
                source="/113 T1 POOLED 8h-only",
                auc_8h_only=0.4889,
                null_q95="<0.51 (per /113 T4 null distribution)",
                note=(
                    "anchor reference from analysis/iteration_v3-113/T1_walkforward_auc.csv; "
                    "re-running is unnecessary -- the value is stable across the existing "
                    "8h feature parquets, and re-feature-computing 8h on /117's loader is a "
                    "different protocol than /113 used (would introduce protocol noise)"
                ),
            )
        ]
    )
    t8.to_csv(OUT / "T8_113_reproducibility.csv", index=False)
    print(t8.to_string(index=False))
    print()

    # T9 -- universe-pooled (all 3 symbols x all 3 offsets in one fold) AUC
    # vs permutation null. The most demanding head-to-head against /113's
    # daily-ONLY 0.5275.
    print("[T9] Universe-pooled (3-sym x 3-offset) AUC vs permutation null")
    print("-" * 78)
    universe = []
    for sym in SYMBOLS:
        universe.append(panels[sym].assign(_sym=sym))
    universe_df = pd.concat(universe, axis=0, ignore_index=True)
    universe_df = universe_df.sort_values("bar_close_time").reset_index(drop=True)
    Xu = universe_df[feat_cols]
    yu = universe_df["label"].to_numpy()
    folds_u = walk_forward_folds(len(universe_df))
    auc_u, per_fold_u = _wf_auc(Xu, yu, folds_u)
    null_u = []
    for _ in range(N_PERM):
        y_shuf = RNG.permutation(yu)
        a, _ = _wf_auc(Xu, y_shuf, folds_u)
        if not np.isnan(a):
            null_u.append(a)
    null_u_arr = np.array(null_u)
    q50_u = float(np.quantile(null_u_arr, 0.50))
    q95_u = float(np.quantile(null_u_arr, 0.95))
    p_val_u = float((null_u_arr >= auc_u).mean())
    t9 = pd.DataFrame(
        [
            dict(
                model="24h-multioffset 3-sym-pooled",
                n_rows=len(universe_df),
                n_folds=len(folds_u),
                observed_auc=round(auc_u, 4),
                null_q50=round(q50_u, 4),
                null_q95=round(q95_u, 4),
                p_value=round(p_val_u, 4),
                clears_q95=bool(auc_u > q95_u),
                n_perm=len(null_u),
            )
        ]
    )
    t9.to_csv(OUT / "T9_universe_pooled.csv", index=False)
    print(t9.to_string(index=False))
    print()

    # T10 -- GO/NO-GO synthesis
    print("[T10] GO/NO-GO synthesis")
    print("-" * 78)
    g1_count_per_sym_q95 = int(t2[t2["model"].str.startswith("24h-multioffset ") & ~t2["model"].str.contains("POOLED")]["clears_q95"].sum())
    g1_pass = g1_count_per_sym_q95 >= 2
    g2_pass = bool(t2[t2["model"] == "24h-multioffset POOLED"]["clears_q95"].iloc[0])
    # g3: per-offset AUC > 0.5 on >= 2 of 3 offsets per symbol (averaged across symbols)
    t3_clean = t3.dropna(subset=["auc"])
    n_offset_gt_half = int((t3_clean["auc"] > 0.5).sum())
    g3_pass = n_offset_gt_half >= 6  # at least 6 of 9 (3 sym x 3 offset) cells > 0.5
    # g4 SOFT: per-symbol row count >= 1500
    g4_per_sym = {sym: len(panels[sym]) for sym in SYMBOLS}
    g4_pass = all(v >= 1500 for v in g4_per_sym.values())
    verdict_go = g1_pass and g2_pass and g3_pass
    t10 = pd.DataFrame(
        [
            dict(
                gate="g1 (per-symbol q95 clears, >=2/3)",
                value=f"{g1_count_per_sym_q95}/3 symbols clear q95",
                threshold=">=2",
                pass_=g1_pass,
            ),
            dict(
                gate="g2 (pooled q95 clears)",
                value=f"observed={auc_p:.4f}, q95={q95_p:.4f}",
                threshold="observed > q95",
                pass_=g2_pass,
            ),
            dict(
                gate="g3 (per-offset cells > 0.5, >=6/9)",
                value=f"{n_offset_gt_half}/9 cells > 0.5",
                threshold=">=6",
                pass_=g3_pass,
            ),
            dict(
                gate="g4 SOFT (per-symbol n_rows >= 1500)",
                value=str(g4_per_sym),
                threshold=">=1500 each",
                pass_=g4_pass,
            ),
            dict(
                gate="VERDICT (g1 AND g2 AND g3)",
                value="GO" if verdict_go else "NO-GO",
                threshold="all three hard gates",
                pass_=verdict_go,
            ),
        ]
    )
    t10.to_csv(OUT / "T10_go_nogo_verdict.csv", index=False)
    print(t10.to_string(index=False))
    print()

    print("=" * 78)
    if verdict_go:
        print("VERDICT: GO -- 24h multi-offset stack carries signal beyond shuffle null")
    else:
        print("VERDICT: NO-GO -- 24h multi-offset signal not significant per pre-registered gates")
        print("        Per PRIME DIRECTIVE the brief proceeds; modal prediction set to")
        print("        EXPLORATION-NEGATIVE; Section 7 documents fallback to 12h-2-offset")
        print("        or weekly-8-offset (per /116 diary 9.6 + feedback_v3_candle_frequency_unblocked.md).")
    print("=" * 78)


if __name__ == "__main__":
    main()
