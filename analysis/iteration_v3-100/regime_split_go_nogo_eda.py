"""iter-v3/100 — Phase-1 FAIL-FAST GO/NO-GO EDA.

AXIS: a per-symbol two-expert REGIME-SWITCHING MIXTURE — separate LightGBM
models trained on the trending vs mean-reverting regime sub-samples of each
symbol's IS data (a past-only Hurst/ADX regime split), with the live model
selected by the contemporaneous past-only regime.

DECISIVE PREMISE under test
---------------------------
Do the trending vs mean-reverting regime sub-samples carry GENUINELY
DIFFERENT, SEPARATELY-LEARNABLE feature->label structure — enough that two
regime-specialist experts would beat the single /059 model?

NON-CIRCULAR, OOS-ROBUST METHODOLOGY
------------------------------------
/096/097 proved IS-CV-IC does NOT predict OOS. So this EDA is NOT a naive
IS-CV-IC ranking. The load-bearing test is a HELD-OUT-FOLD HORSE RACE:

  expanding-window walk-forward over the last K one-month IS folds; for each
  fold, train (a) ONE pooled LightGBM on ALL prior IS candles and (b) TWO
  regime-expert LightGBMs each on the prior IS candles of ONE regime; then on
  the held-out fold, route each candle to its regime expert and compare the
  MIXTURE's directional skill against the POOLED model's. The regime label at
  decision time is PAST-ONLY (Hurst/ADX, computed at the candle close); each
  fold's model sees ONLY candles strictly before it.

A two-expert mixture is worth building ONLY if the mixture genuinely beats
the pooled model OUT-OF-WINDOW. If the sub-samples carry the same
feature->label map, splitting the training set merely halves each expert's
data and the mixture loses.

PRE-REGISTERED GATES (the GO rule is g1 AND g2 AND g3 AND g4)
------------------------------------------------------------
  g1 SEPARABILITY  — pooled fraction of IS candles in the minority regime
                     >= 0.20 (both regimes must be materially populated;
                     a 95/5 split means one expert has no data).
  g2 STRUCTURE-DIFF — the two regimes' feature->label maps are GENUINELY
                     DIFFERENT: a held-out cross-regime degradation test.
                     Train an expert on regime-A candles, score it on
                     regime-A vs regime-B held-out candles; if the map is
                     the same, A-expert scores B equally well. Gate on the
                     pooled cross-regime AUC GAP >= 0.04 (own-regime minus
                     other-regime held-out AUC).
  g3 MIXTURE-LIFT  — the load-bearing gate. The two-expert MIXTURE's
                     held-out-fold directional accuracy minus the POOLED
                     model's, paired across folds and symbols, mean > 0
                     AND the block-bootstrap 95% CI lower bound > 0.
  g4 MIXTURE-PNL   — the mixture's held-out-fold net-PnL-of-the-predicted-
                     side minus the pooled model's, mean > 0. A skill lift
                     that does not convert to PnL is not actionable.

If g3 (the decisive gate) fails OR its CI straddles zero, a two-expert
regime mixture offers no learnable lift -> NO-GO, STOP at the EDA.

DISCIPLINE
----------
- IS-ONLY: every candle used has open_time < OOS_CUTOFF_MS = 1742774400000
  (2025-03-24). The real OOS is never touched.
- Labels replicate labeling.py:label_trades EXACTLY — ATR triple-barrier,
  TP=2.0*ATR, SL=1.0*ATR (atr_column natr_21_raw), timeout 10080 min
  (21 candles at 8h), fee 0.1%.
- The model family is LightGBM — the exact learner the v3 primary uses.
- Significance is a candle-level BLOCK bootstrap, block = the 21-bar label
  horizon (the /096 overlapping-triple-barrier serial-dependence discipline).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from crypto_trade.strategies.ml.labeling import label_trades  # noqa: E402

OUT = Path(__file__).resolve().parent
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC — IMMUTABLE
SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]
FEATURES_DIR = REPO / "data" / "features_v3"

# --- /059 labeling params (faithful to run_baseline_v3.py + lgbm.py) ---
ATR_TP_MULT = 2.0
ATR_SL_MULT = 1.0
TIMEOUT_MIN = 10080  # 21 candles at 8h
FEE_PCT = 0.1
ATR_COLUMN = "natr_21_raw"

# --- the 14-feature /059 stack (V3_FEATURE_COLUMNS_TOP_N) ---
FEATURES = [
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
]

# --- EDA controls ---
N_FOLDS = 8  # last 8 one-month IS folds (held-out horse race)
TRAIN_BURN_MONTHS = 24  # mirror TRAINING_MONTHS — drop the first 24mo burn-in
BOOTSTRAP_N = 2000
BLOCK_BARS = 21  # = the triple-barrier label horizon
RNG = np.random.default_rng(42)

# --- gate thresholds (pre-registered) ---
G1_MIN_MINORITY_FRAC = 0.20
G2_MIN_AUC_GAP = 0.04
G3_DECISIVE = True  # mixture-lift mean > 0 AND CI lower bound > 0

# LightGBM params — modest, mirrors a v3 per-symbol model's scale.
LGB_PARAMS = dict(
    objective="binary",
    n_estimators=120,
    num_leaves=15,
    max_depth=4,
    learning_rate=0.05,
    min_child_samples=20,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    verbose=-1,
    n_jobs=2,
)


def log(msg: str) -> None:
    print(msg, flush=True)


def load_symbol(sym: str) -> pd.DataFrame:
    """Load a v3 feature parquet, IS-only, sorted by open_time."""
    df = pd.read_parquet(FEATURES_DIR / f"{sym}_8h_features.parquet")
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy()
    df = df.sort_values("open_time").reset_index(drop=True)
    df["symbol"] = sym
    return df


def build_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Replicate the /059 ATR triple-barrier label exactly via label_trades.

    Adds: label (1 long / -1 short), long_pnl, short_pnl, best_edge
    (max of the two net directional PnLs — > 0 iff a tradeable edge exists).
    """
    master = df[
        ["symbol", "open_time", "close_time", "open", "high", "low", "close"]
    ].copy()
    for c in ("open", "high", "low", "close"):
        master[c] = master[c].astype(float)
    n = len(master)
    cand = np.arange(n, dtype=np.intp)

    # ATR in price units = close * natr_21_raw / 100  (mirrors lgbm._load_atr_for_master)
    natr = df[ATR_COLUMN].to_numpy(dtype=np.float64)
    atr_values = master["close"].to_numpy(dtype=np.float64) * natr / 100.0

    labels, _weights, long_pnls, short_pnls = label_trades(
        master,
        cand,
        tp_pct=ATR_TP_MULT,
        sl_pct=ATR_SL_MULT,
        timeout_minutes=TIMEOUT_MIN,
        fee_pct=FEE_PCT,
        atr_values=atr_values,
        label_mode="triple_barrier",
    )
    out = df.copy()
    out["label"] = labels
    out["long_pnl"] = long_pnls
    out["short_pnl"] = short_pnls
    out["best_edge"] = np.maximum(long_pnls, short_pnls)
    # binary target for the directional classifier: 1 if label==1 (long) else 0
    out["y"] = (labels == 1).astype(int)
    return out


def assign_regime(df: pd.DataFrame) -> pd.Series:
    """PAST-ONLY trending vs mean-reverting regime label at the candle close.

    Regime is determined by two past-only fields already in the v3 parquet:
      - hurst_100: rescaled-range Hurst over the trailing 100 bars. > 0.5 =>
        persistent/trending; < 0.5 => anti-persistent/mean-reverting.
      - adx_14: Wilder ADX over 14 bars. High ADX => directional trend.

    A candle is TRENDING (regime=1) iff hurst_100 > 0.5 AND adx_14 >= the
    symbol's IS-median ADX (a conjunctive trend filter). Else MEAN-REVERTING
    (regime=0). The Hurst/ADX columns are computed from trailing windows only
    (regime_v3._rolling_hurst uses values[i-window:i]; adx_14 is a Wilder
    smoothing of past bars) — NO look-ahead. The IS-median ADX threshold is
    itself computed on IS-only candles, used as a fixed split point; this is
    a characterization choice, not a tuned hyperparameter.
    """
    hurst = df["hurst_100"].to_numpy(dtype=np.float64)
    adx = df["adx_14"].to_numpy(dtype=np.float64)
    adx_med = np.nanmedian(adx)
    trending = (hurst > 0.5) & (adx >= adx_med)
    return pd.Series(np.where(trending, 1, 0), index=df.index, name="regime")


def month_key(open_time_ms: np.ndarray) -> np.ndarray:
    """Year*100 + month integer key from epoch-ms open_time."""
    ts = pd.to_datetime(open_time_ms, unit="ms")
    return (ts.year * 100 + ts.month).to_numpy()


def fit_lgb(X: np.ndarray, y: np.ndarray):
    """Fit a LightGBM binary classifier; return the fitted model or None."""
    from lightgbm import LGBMClassifier

    if len(np.unique(y)) < 2 or len(y) < 40:
        return None
    m = LGBMClassifier(**LGB_PARAMS, random_state=42)
    m.fit(X, y)
    return m


def auc(y_true: np.ndarray, score: np.ndarray) -> float:
    """ROC AUC; NaN if a single class is present."""
    from sklearn.metrics import roc_auc_score

    if len(np.unique(y_true)) < 2:
        return float("nan")
    return float(roc_auc_score(y_true, score))


def block_bootstrap_ci(values: np.ndarray, block: int, n: int) -> tuple[float, float]:
    """Block-bootstrap 95% CI of the mean (block preserves serial dependence)."""
    values = np.asarray(values, dtype=np.float64)
    values = values[~np.isnan(values)]
    if len(values) < block + 1:
        if len(values) == 0:
            return (float("nan"), float("nan"))
        return (float(values.min()), float(values.max()))
    n_obs = len(values)
    n_blocks = int(np.ceil(n_obs / block))
    means = np.empty(n, dtype=np.float64)
    max_start = n_obs - block
    for b in range(n):
        starts = RNG.integers(0, max_start + 1, size=n_blocks)
        samp = np.concatenate([values[s : s + block] for s in starts])[:n_obs]
        means[b] = samp.mean()
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def main() -> None:
    log("=" * 78)
    log("iter-v3/100 Phase-1 GO/NO-GO EDA — regime-switching two-expert mixture")
    log("=" * 78)

    # ---- Load + label + regime-tag, IS-only ----
    data: dict[str, pd.DataFrame] = {}
    for sym in SYMBOLS:
        df = load_symbol(sym)
        df = build_labels(df)
        df["regime"] = assign_regime(df)
        # need all features present + a defined regime + a defined label
        need = FEATURES + ["regime", "y", "best_edge", "long_pnl", "short_pnl", "open_time"]
        df = df.dropna(subset=[c for c in need if c in df.columns]).reset_index(drop=True)
        data[sym] = df
        log(
            f"  {sym}: {len(df)} IS labeled candles "
            f"(open_time < {OOS_CUTOFF_MS}); "
            f"trending {int((df['regime'] == 1).sum())} / "
            f"mean-rev {int((df['regime'] == 0).sum())}"
        )

    # =====================================================================
    # T1 — SEPARABILITY: regime population balance (gate g1)
    # =====================================================================
    log("\n[T1] Regime separability — minority-regime fraction per symbol")
    t1_rows = []
    for sym in SYMBOLS:
        df = data[sym]
        n = len(df)
        n_trend = int((df["regime"] == 1).sum())
        n_mr = n - n_trend
        minority_frac = min(n_trend, n_mr) / n if n else 0.0
        t1_rows.append(
            dict(
                symbol=sym,
                n=n,
                n_trending=n_trend,
                n_mean_rev=n_mr,
                trending_frac=round(n_trend / n, 4) if n else 0.0,
                minority_frac=round(minority_frac, 4),
            )
        )
        log(
            f"  {sym}: trending {n_trend} ({n_trend / n:.1%}) | "
            f"mean-rev {n_mr} ({n_mr / n:.1%}) | minority_frac {minority_frac:.4f}"
        )
    t1 = pd.DataFrame(t1_rows)
    pooled_minority = float(
        min(t1["n_trending"].sum(), t1["n_mean_rev"].sum()) / t1["n"].sum()
    )
    g1_pass = pooled_minority >= G1_MIN_MINORITY_FRAC
    log(f"  POOLED minority_frac = {pooled_minority:.4f}  (gate g1 >= {G1_MIN_MINORITY_FRAC})")
    t1.to_csv(OUT / "T1_regime_separability.csv", index=False)

    # =====================================================================
    # T2 — STRUCTURE-DIFF: cross-regime held-out degradation (gate g2)
    # For each fold: train an expert on regime-A prior candles, score it on
    # held-out regime-A vs held-out regime-B candles. If the feature->label
    # map is the SAME, the A-expert scores B equally well (gap ~ 0). A large
    # own-minus-other AUC gap means the regimes carry different structure.
    # =====================================================================
    log("\n[T2] Cross-regime structure difference — held-out own vs other AUC")
    t2_rows = []
    for sym in SYMBOLS:
        df = data[sym]
        mk = month_key(df["open_time"].to_numpy())
        months = np.array(sorted(np.unique(mk)))
        if len(months) <= TRAIN_BURN_MONTHS + 1:
            log(f"  {sym}: insufficient months ({len(months)}) — skipped")
            continue
        fold_months = months[-N_FOLDS:]
        Xall = df[FEATURES].to_numpy(dtype=np.float64)
        yall = df["y"].to_numpy()
        reg = df["regime"].to_numpy()
        for fm in fold_months:
            tr = mk < fm
            te = mk == fm
            if tr.sum() < 200 or te.sum() < 10:
                continue
            for reg_a, reg_name in ((1, "trending"), (0, "mean_rev")):
                tr_a = tr & (reg == reg_a)
                m_a = fit_lgb(Xall[tr_a], yall[tr_a])
                if m_a is None:
                    continue
                te_own = te & (reg == reg_a)
                te_oth = te & (reg != reg_a)
                if te_own.sum() < 8 or te_oth.sum() < 8:
                    continue
                s_own = m_a.predict_proba(Xall[te_own])[:, 1]
                s_oth = m_a.predict_proba(Xall[te_oth])[:, 1]
                a_own = auc(yall[te_own], s_own)
                a_oth = auc(yall[te_oth], s_oth)
                if np.isnan(a_own) or np.isnan(a_oth):
                    continue
                t2_rows.append(
                    dict(
                        symbol=sym,
                        fold_month=int(fm),
                        expert_regime=reg_name,
                        n_train_regime=int(tr_a.sum()),
                        auc_own_regime=round(a_own, 4),
                        auc_other_regime=round(a_oth, 4),
                        auc_gap=round(a_own - a_oth, 4),
                    )
                )
    t2 = pd.DataFrame(t2_rows)
    t2.to_csv(OUT / "T2_cross_regime_structure.csv", index=False)
    if len(t2):
        mean_gap = float(t2["auc_gap"].mean())
        log(
            f"  fold-expert observations: {len(t2)} | "
            f"mean own-minus-other AUC gap = {mean_gap:+.4f}"
        )
        for sym in SYMBOLS:
            sub = t2[t2["symbol"] == sym]
            if len(sub):
                log(f"    {sym}: mean gap {sub['auc_gap'].mean():+.4f} (n={len(sub)})")
    else:
        mean_gap = float("nan")
        log("  no valid cross-regime observations")
    g2_pass = (not np.isnan(mean_gap)) and mean_gap >= G2_MIN_AUC_GAP

    # =====================================================================
    # T3 — MIXTURE HORSE RACE (gates g3, g4): the load-bearing test.
    # For each held-out month fold: train ONE pooled model on all prior IS
    # candles, and TWO regime-expert models each on the prior IS candles of
    # one regime. On the held-out fold, route each candle to its regime
    # expert (the mixture); compare mixture vs pooled on directional
    # accuracy and net PnL of the predicted side. PAST-ONLY routing: the
    # regime label is computed at the candle close from trailing windows.
    # =====================================================================
    log("\n[T3] Mixture horse race — two-expert mixture vs single pooled model")
    t3_rows = []
    for sym in SYMBOLS:
        df = data[sym]
        mk = month_key(df["open_time"].to_numpy())
        months = np.array(sorted(np.unique(mk)))
        if len(months) <= TRAIN_BURN_MONTHS + 1:
            continue
        fold_months = months[-N_FOLDS:]
        Xall = df[FEATURES].to_numpy(dtype=np.float64)
        yall = df["y"].to_numpy()
        reg = df["regime"].to_numpy()
        long_pnl = df["long_pnl"].to_numpy()
        short_pnl = df["short_pnl"].to_numpy()
        for fm in fold_months:
            tr = mk < fm
            te = mk == fm
            if tr.sum() < 300 or te.sum() < 15:
                continue
            # --- pooled model ---
            m_pool = fit_lgb(Xall[tr], yall[tr])
            if m_pool is None:
                continue
            # --- two regime experts ---
            experts: dict[int, object] = {}
            for reg_v in (0, 1):
                tr_r = tr & (reg == reg_v)
                experts[reg_v] = fit_lgb(Xall[tr_r], yall[tr_r])
            # need BOTH experts to exist for an honest mixture comparison
            if experts[0] is None or experts[1] is None:
                continue
            te_idx = np.where(te)[0]
            # pooled predictions
            pool_score = m_pool.predict_proba(Xall[te_idx])[:, 1]
            # mixture predictions: route each candle to its regime expert
            mix_score = np.empty(len(te_idx), dtype=np.float64)
            for k, gi in enumerate(te_idx):
                ex = experts[int(reg[gi])]
                mix_score[k] = ex.predict_proba(Xall[gi : gi + 1])[:, 1][0]
            y_te = yall[te_idx]
            pool_pred = (pool_score >= 0.5).astype(int)  # 1=long, 0=short
            mix_pred = (mix_score >= 0.5).astype(int)
            # directional accuracy
            pool_acc = float((pool_pred == y_te).mean())
            mix_acc = float((mix_pred == y_te).mean())
            # net PnL of the predicted side
            pl = long_pnl[te_idx]
            ps = short_pnl[te_idx]
            pool_pnl = float(np.where(pool_pred == 1, pl, ps).mean())
            mix_pnl = float(np.where(mix_pred == 1, pl, ps).mean())
            t3_rows.append(
                dict(
                    symbol=sym,
                    fold_month=int(fm),
                    n_test=int(len(te_idx)),
                    pool_acc=round(pool_acc, 4),
                    mix_acc=round(mix_acc, 4),
                    acc_lift=round(mix_acc - pool_acc, 4),
                    pool_pnl=round(pool_pnl, 4),
                    mix_pnl=round(mix_pnl, 4),
                    pnl_lift=round(mix_pnl - pool_pnl, 4),
                )
            )
    t3 = pd.DataFrame(t3_rows)
    t3.to_csv(OUT / "T3_mixture_horse_race.csv", index=False)
    if len(t3):
        acc_lift_mean = float(t3["acc_lift"].mean())
        pnl_lift_mean = float(t3["pnl_lift"].mean())
        log(
            f"  fold observations: {len(t3)} "
            f"({t3.groupby('symbol').size().to_dict()})"
        )
        log(
            f"  POOLED  : mean held-out acc {t3['pool_acc'].mean():.4f} | "
            f"mean side-PnL {t3['pool_pnl'].mean():+.4f}"
        )
        log(
            f"  MIXTURE : mean held-out acc {t3['mix_acc'].mean():.4f} | "
            f"mean side-PnL {t3['mix_pnl'].mean():+.4f}"
        )
        log(
            f"  LIFT (mixture - pooled): acc {acc_lift_mean:+.4f} | "
            f"PnL {pnl_lift_mean:+.4f}"
        )
        for sym in SYMBOLS:
            sub = t3[t3["symbol"] == sym]
            if len(sub):
                log(
                    f"    {sym}: acc_lift {sub['acc_lift'].mean():+.4f} | "
                    f"pnl_lift {sub['pnl_lift'].mean():+.4f} (n={len(sub)})"
                )
    else:
        acc_lift_mean = float("nan")
        pnl_lift_mean = float("nan")
        log("  no valid mixture-vs-pooled fold observations")

    # block-bootstrap CI on the per-fold accuracy lift (g3 decisive gate)
    if len(t3):
        ci_lo, ci_hi = block_bootstrap_ci(
            t3["acc_lift"].to_numpy(), BLOCK_BARS, BOOTSTRAP_N
        )
    else:
        ci_lo, ci_hi = float("nan"), float("nan")
    log(
        f"\n[T3-CI] acc_lift block-bootstrap 95% CI = "
        f"[{ci_lo:+.4f}, {ci_hi:+.4f}]  (block={BLOCK_BARS} bars, "
        f"{BOOTSTRAP_N} resamples)"
    )
    pd.DataFrame(
        [
            dict(
                metric="acc_lift",
                mean=round(acc_lift_mean, 5) if not np.isnan(acc_lift_mean) else None,
                ci_lo=round(ci_lo, 5) if not np.isnan(ci_lo) else None,
                ci_hi=round(ci_hi, 5) if not np.isnan(ci_hi) else None,
            )
        ]
    ).to_csv(OUT / "T3_bootstrap_ci.csv", index=False)

    g3_pass = (
        (not np.isnan(acc_lift_mean))
        and acc_lift_mean > 0.0
        and (not np.isnan(ci_lo))
        and ci_lo > 0.0
    )
    g4_pass = (not np.isnan(pnl_lift_mean)) and pnl_lift_mean > 0.0

    # =====================================================================
    # T4 — VERDICT
    # =====================================================================
    log("\n" + "=" * 78)
    log("[T4] GO/NO-GO VERDICT")
    log("=" * 78)
    verdict_rows = [
        dict(
            gate="g1_separability",
            statistic="pooled minority-regime fraction",
            threshold=f">= {G1_MIN_MINORITY_FRAC}",
            value=round(pooled_minority, 4),
            verdict="PASS" if g1_pass else "FAIL",
        ),
        dict(
            gate="g2_structure_diff",
            statistic="mean own-minus-other-regime held-out AUC gap",
            threshold=f">= {G2_MIN_AUC_GAP}",
            value=round(mean_gap, 4) if not np.isnan(mean_gap) else None,
            verdict="PASS" if g2_pass else "FAIL",
        ),
        dict(
            gate="g3_mixture_lift",
            statistic="mixture-minus-pooled held-out acc lift (mean; CI lo > 0)",
            threshold="mean > 0 AND CI_lo > 0",
            value=round(acc_lift_mean, 4) if not np.isnan(acc_lift_mean) else None,
            verdict="PASS" if g3_pass else "FAIL",
        ),
        dict(
            gate="g4_mixture_pnl",
            statistic="mixture-minus-pooled held-out side-PnL lift (mean)",
            threshold="mean > 0",
            value=round(pnl_lift_mean, 4) if not np.isnan(pnl_lift_mean) else None,
            verdict="PASS" if g4_pass else "FAIL",
        ),
    ]
    verdict = pd.DataFrame(verdict_rows)
    for _, r in verdict.iterrows():
        log(
            f"  {r['gate']:<22} {str(r['value']):>10}  "
            f"(need {r['threshold']})  -> {r['verdict']}"
        )

    go = g1_pass and g2_pass and g3_pass and g4_pass
    decision = "GO" if go else "NO-GO"
    log("")
    log(f"  GO rule = g1 AND g2 AND g3 AND g4   ->   DECISION: {decision}")
    if not go:
        decisive = []
        if not g3_pass:
            decisive.append("g3 (mixture-lift — the decisive gate)")
        if not g1_pass:
            decisive.append("g1 (separability)")
        if not g2_pass:
            decisive.append("g2 (structure-diff)")
        if not g4_pass:
            decisive.append("g4 (mixture-PnL)")
        log(f"  binding failure(s): {', '.join(decisive)}")
    verdict_out = verdict.copy()
    verdict_out["decision"] = decision
    verdict_out.to_csv(OUT / "T4_go_nogo_verdict.csv", index=False)
    log("\n  artifacts: T1_regime_separability.csv  T2_cross_regime_structure.csv")
    log("             T3_mixture_horse_race.csv  T3_bootstrap_ci.csv")
    log("             T4_go_nogo_verdict.csv")
    log("=" * 78)


if __name__ == "__main__":
    main()
