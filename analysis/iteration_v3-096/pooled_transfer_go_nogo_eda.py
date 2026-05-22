"""iter-v3/096 — Phase-1 FAIL-FAST GO/NO-GO EDA — POOLED CROSS-SYMBOL MODEL.

THE AXIS UNDER TEST
-------------------
Every v3 architecture in cycles 1-4 trains a SEPARATE per-symbol LightGBM
(one for BCH, one for LDO, one for TRX) on the per-symbol triple-barrier
label.  The single architecture v3 has NEVER tried is a POOLED model — one
LightGBM trained on the concatenated BCH+LDO+TRX sample (v1's Model A
construction: BTC+ETH pooled, proven to work in v1).  Pooling ~triples the
training rows per model (the textbook fix for the IS-overfitting root cause
the /088 closeout named).

THE DECISIVE PREMISE — and why this axis is cheaply EDA-gateable
----------------------------------------------------------------
Pooling only adds signal if the three symbols share a TRANSFERABLE
feature->label relationship.  If a model trained on symbols {A,B}
generalizes to held-out symbol {C}, the pooled training rows are genuine
extra signal.  If cross-symbol transfer collapses to ~0 — i.e. each
symbol's feature->label map is idiosyncratic — then pooling just averages
three unrelated signals into mush, and a pooled model is foreseeably
NEGATIVE.  That question is answerable WITHOUT a backtest:

  Leave-One-Symbol-Out (LOSO) cross-symbol transfer test.
  For each held-out symbol C:
    - train a LightGBM on the OTHER TWO symbols' IS bars
    - measure rank-IC of its prediction vs the realized triple-barrier
      directional outcome on C's IS bars (data the model never saw,
      and a SYMBOL the model never saw).
  Compare against the WITHIN-symbol benchmark (5-fold purged CV IC on the
  symbol's own bars) — the per-symbol architecture's own signal level.

GO / NO-GO  (pre-registered, decided BEFORE running)
----------------------------------------------------
  T5 headline = mean LOSO cross-symbol transfer rank-IC across the 3
  held-out symbols, measured against the triple-barrier directional label.

  GO   if T5 >= +0.030 AND >= 2 of 3 held-out symbols have transfer IC > 0
       AND the transfer-IC sign is consistent (all same sign).
       Rationale: a pooled model needs the cross-symbol map to carry
       genuine, sign-consistent directional content.  +0.030 is a low bar
       (the within-symbol benchmark is the reference) — but it must be
       POSITIVE and CONSISTENT, not noise around zero.

  NO-GO if T5 < +0.030, OR transfer IC flips sign across symbols, OR
       the transfer IC is a large negative-fraction of the within-symbol
       benchmark (the symbols actively mislead each other).

NO-CHEATING
-----------
  - OOS_CUTOFF_MS = 1742774400000 (2025-03-24).  EVERY row used here has
    open_time < OOS_CUTOFF_MS.  OOS is NEVER touched.
  - 24-month listing burn-in dropped per symbol (matches the runner's
    per-symbol warmup; a pooled IS-eval window cannot include a symbol's
    pre-warmup bars).
  - The triple-barrier label is computed with the EXACT /059 production
    params: ATR multipliers (2.0, 1.0), timeout 10080 min = 21 candles,
    fee 0.1%, label_mode triple_barrier — replicated from
    src/crypto_trade/strategies/ml/labeling.py:label_trades.
  - The 14-feature stack is V3_FEATURE_COLUMNS (the /059 anchor).
  - Purged 5-fold CV with a 22-candle embargo for the within-symbol
    benchmark (no label-window leakage).

This is a Phase-1 GO/NO-GO.  NO-GO -> STOP at the EDA (no brief, no runner,
no backtest) — the fail-fast win.  GO -> proceed to Phases 2-5.
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

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 — IMMUTABLE
TRAINING_MONTHS = 24
TIMEOUT_MIN = 10080  # 21 candles at 8h
TP_MULT = 2.0
SL_MULT = 1.0
FEE_PCT = 0.1
EMBARGO_CANDLES = 22  # 10080 // 480 + 1
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
DATA_DIR = Path("data/features_v3")
OUT = Path("analysis/iteration_v3-096")

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

# Pre-registered GO thresholds
GO_T5_MIN = 0.030
GO_MIN_POSITIVE_SYMBOLS = 2


# ---------------------------------------------------------------------------
# Triple-barrier labeling — faithful replication of labeling.py:label_trades
# ---------------------------------------------------------------------------
def triple_barrier_label(df: pd.DataFrame) -> pd.DataFrame:
    """Return df with added columns: tb_label (1 long / -1 short), tb_pnl.

    Replicates the /059 production triple-barrier rule for a single symbol:
      - ATR distance: TP = 2.0*ATR, SL = 1.0*ATR  (ATR in price units)
      - timeout 21 candles
      - label = side whose TP is hit first; if neither TP, sign of fwd return
      - tb_pnl = realized net-of-fee PnL of the labeled side
    natr_21_raw is NATR-as-percentage -> ATR_price = natr/100 * close.
    """
    out = df.reset_index(drop=True).copy()
    n = len(out)
    high = out["high"].to_numpy(dtype=np.float64)
    low = out["low"].to_numpy(dtype=np.float64)
    close = out["close"].to_numpy(dtype=np.float64)
    close_time = out["close_time"].to_numpy(dtype=np.int64)
    natr = out["natr_21_raw"].to_numpy(dtype=np.float64)
    timeout_ms = TIMEOUT_MIN * 60 * 1000

    labels = np.zeros(n, dtype=np.int64)
    pnls = np.full(n, np.nan, dtype=np.float64)

    for i in range(n):
        entry = close[i]
        if entry <= 0:
            continue
        atr = (natr[i] / 100.0) * entry if np.isfinite(natr[i]) else entry * 0.02
        tp_dist = atr * TP_MULT
        sl_dist = atr * SL_MULT
        long_tp = entry + tp_dist
        long_sl = entry - sl_dist
        short_tp = entry - tp_dist
        short_sl = entry + sl_dist
        deadline = close_time[i] + timeout_ms

        long_result = 0  # 0 pending, 1 tp, -1 sl, -2 timeout
        short_result = 0
        long_step = -1
        short_step = -1
        last_close = entry

        j = i + 1
        while j < n:
            if close_time[j] > deadline:
                if long_result == 0:
                    long_result, long_step = -2, j
                if short_result == 0:
                    short_result, short_step = -2, j
                break
            h, lo = high[j], low[j]
            last_close = close[j]
            if long_result == 0:
                if lo <= long_sl:
                    long_result, long_step = -1, j
                elif h >= long_tp:
                    long_result, long_step = 1, j
            if short_result == 0:
                if h >= short_sl:
                    short_result, short_step = -1, j
                elif lo <= short_tp:
                    short_result, short_step = 1, j
            if long_result != 0 and short_result != 0:
                break
            j += 1
        else:
            if long_result == 0:
                long_result, long_step = -2, n
            if short_result == 0:
                short_result, short_step = -2, n

        fwd_ret = (last_close - entry) / entry * 100.0 if entry != 0 else 0.0
        tp_pnl_pct = tp_dist / entry * 100.0
        sl_pnl_pct = sl_dist / entry * 100.0

        def side_pnl(result: int, signed_fwd: float) -> float:
            if result == 1:
                return tp_pnl_pct - FEE_PCT
            if result == -1:
                return -sl_pnl_pct - FEE_PCT
            return signed_fwd - FEE_PCT

        long_pnl = side_pnl(long_result, fwd_ret)
        short_pnl = side_pnl(short_result, -fwd_ret)

        long_tp_hit = long_result == 1
        short_tp_hit = short_result == 1
        if long_tp_hit and not short_tp_hit:
            lab = 1
        elif short_tp_hit and not long_tp_hit:
            lab = -1
        elif long_tp_hit and short_tp_hit:
            lab = 1 if long_step <= short_step else -1
        else:
            lab = 1 if fwd_ret >= 0 else -1

        labels[i] = lab
        pnls[i] = long_pnl if lab == 1 else short_pnl

    out["tb_label"] = labels
    out["tb_pnl"] = pnls
    return out


def load_symbol_is(symbol: str) -> pd.DataFrame:
    """Load a symbol's IS feature parquet, apply 24-month listing burn-in,
    restrict strictly to open_time < OOS_CUTOFF_MS, compute the label."""
    df = pd.read_parquet(DATA_DIR / f"{symbol}_8h_features.parquet")
    df = df.sort_values("open_time").reset_index(drop=True)
    # 24-month listing burn-in: drop the first 24 months of the symbol's life
    first_ms = int(df["open_time"].min())
    burnin_end = first_ms + TRAINING_MONTHS * 30 * 24 * 60 * 60 * 1000
    # Label needs the forward window; compute the label on the FULL panel
    # so the forward scan can see post-burnin bars, then keep only:
    #   open_time >= burnin_end  (24-month warmup)  AND
    #   open_time <  OOS_CUTOFF_MS  (IS only — no OOS leak)
    df = triple_barrier_label(df)
    is_mask = (df["open_time"] >= burnin_end) & (df["open_time"] < OOS_CUTOFF_MS)
    isd = df[is_mask].copy()
    isd["symbol"] = symbol
    return isd


def rank_ic(pred: np.ndarray, target: np.ndarray) -> float:
    """Spearman rank-IC between prediction and target."""
    if len(pred) < 30:
        return float("nan")
    s1 = pd.Series(pred).rank()
    s2 = pd.Series(target).rank()
    c = s1.corr(s2)
    return float(c) if pd.notna(c) else float("nan")


def purged_kfold_indices(n: int, k: int, embargo: int):
    """Yield (train_idx, test_idx) for a purged k-fold over a single
    time-ordered symbol — embargo rows dropped from BOTH sides of each
    test fold so no training label's 21-bar forward window overlaps a
    test row."""
    fold_sizes = np.full(k, n // k, dtype=int)
    fold_sizes[: n % k] += 1
    current = 0
    bounds = []
    for fs in fold_sizes:
        bounds.append((current, current + fs))
        current += fs
    for lo, hi in bounds:
        test_idx = np.arange(lo, hi)
        train_mask = np.ones(n, dtype=bool)
        train_mask[max(0, lo - embargo) : min(n, hi + embargo)] = False
        train_idx = np.where(train_mask)[0]
        yield train_idx, test_idx


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
    random_state=42,
    verbose=-1,
    n_jobs=2,
)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/096 Phase-1 GO/NO-GO EDA — POOLED CROSS-SYMBOL MODEL")
    print("Decisive premise: does the feature->label map TRANSFER across BCH/LDO/TRX?")
    print(f"OOS_CUTOFF_MS = {OOS_CUTOFF_MS} (2025-03-24) — every row IS-only")
    print("=" * 78)

    # ---- load all 3 symbols' IS data ----
    panels: dict[str, pd.DataFrame] = {}
    t1_rows = []
    for sym in SYMBOLS:
        d = load_symbol_is(sym)
        # binary target: 1 if long label, 0 if short label
        d["y"] = (d["tb_label"] == 1).astype(int)
        d = d.dropna(subset=list(V3_FEATURE_COLUMNS) + ["tb_pnl"]).reset_index(drop=True)
        panels[sym] = d
        t1_rows.append(
            {
                "symbol": sym,
                "is_rows": len(d),
                "is_first": str(pd.to_datetime(d["open_time"].min(), unit="ms").date()),
                "is_last": str(pd.to_datetime(d["open_time"].max(), unit="ms").date()),
                "long_label_frac": round(float(d["y"].mean()), 4),
                "mean_tb_pnl": round(float(d["tb_pnl"].mean()), 4),
            }
        )
    t1 = pd.DataFrame(t1_rows)
    t1.to_csv(OUT / "T1_is_panel_summary.csv", index=False)
    print("\nT1 — IS panel summary (per symbol, post-24mo-burnin, IS-only):")
    print(t1.to_string(index=False))

    # ---- T2: WITHIN-symbol benchmark — purged 5-fold CV rank-IC ----
    # This is the per-symbol architecture's own signal level — the reference
    # the cross-symbol transfer IC must be compared against.
    print("\nT2 — WITHIN-symbol benchmark (purged 5-fold CV rank-IC vs tb_label):")
    t2_rows = []
    within_ic: dict[str, float] = {}
    for sym in SYMBOLS:
        d = panels[sym]
        X = d[list(V3_FEATURE_COLUMNS)].to_numpy(dtype=np.float64)
        y = d["y"].to_numpy(dtype=int)
        tgt = d["tb_label"].to_numpy(dtype=np.float64)  # +1/-1 directional
        fold_ics = []
        for tr, te in purged_kfold_indices(len(d), 5, EMBARGO_CANDLES):
            if len(np.unique(y[tr])) < 2:
                continue
            model = lgb.LGBMClassifier(**LGB_PARAMS)
            model.fit(X[tr], y[tr])
            p = model.predict_proba(X[te])[:, 1]
            fold_ics.append(rank_ic(p, tgt[te]))
        ic = float(np.nanmean(fold_ics)) if fold_ics else float("nan")
        within_ic[sym] = ic
        t2_rows.append(
            {
                "symbol": sym,
                "within_cv_rank_ic": round(ic, 5),
                "n_folds": len(fold_ics),
            }
        )
        print(f"  {sym}: within-symbol CV rank-IC = {ic:+.5f}")
    t2 = pd.DataFrame(t2_rows)
    t2.to_csv(OUT / "T2_within_symbol_benchmark.csv", index=False)
    within_mean = float(np.nanmean(list(within_ic.values())))
    print(f"  -> within-symbol mean rank-IC = {within_mean:+.5f}")

    # ---- T3: LOSO cross-symbol TRANSFER — the headline test ----
    # Train on the OTHER 2 symbols' IS bars; predict the held-out symbol's
    # IS bars (a symbol AND rows the model never saw).  The transfer IC is
    # genuine cross-symbol generalization — exactly what a pooled model relies
    # on to convert 2x extra training rows into extra signal.
    print("\nT3 — LEAVE-ONE-SYMBOL-OUT cross-symbol TRANSFER rank-IC (the headline):")
    t3_rows = []
    transfer_ic: dict[str, float] = {}
    for held in SYMBOLS:
        train_syms = [s for s in SYMBOLS if s != held]
        train_df = pd.concat([panels[s] for s in train_syms], ignore_index=True)
        Xtr = train_df[list(V3_FEATURE_COLUMNS)].to_numpy(dtype=np.float64)
        ytr = train_df["y"].to_numpy(dtype=int)
        d_held = panels[held]
        Xte = d_held[list(V3_FEATURE_COLUMNS)].to_numpy(dtype=np.float64)
        tgt = d_held["tb_label"].to_numpy(dtype=np.float64)
        model = lgb.LGBMClassifier(**LGB_PARAMS)
        model.fit(Xtr, ytr)
        p = model.predict_proba(Xte)[:, 1]
        ic = rank_ic(p, tgt)
        transfer_ic[held] = ic
        retention = (ic / within_ic[held]) if within_ic[held] not in (0.0,) else float("nan")
        t3_rows.append(
            {
                "held_out_symbol": held,
                "trained_on": "+".join(s.replace("USDT", "") for s in train_syms),
                "transfer_rank_ic": round(ic, 5),
                "within_symbol_ic": round(within_ic[held], 5),
                "transfer_retention_pct": round(retention, 4),
            }
        )
        print(
            f"  hold {held}: transfer IC = {ic:+.5f} "
            f"(within = {within_ic[held]:+.5f}, retention = {retention:+.2%})"
        )
    t3 = pd.DataFrame(t3_rows)
    t3.to_csv(OUT / "T3_loso_transfer_ic.csv", index=False)
    t5_headline = float(np.nanmean(list(transfer_ic.values())))
    n_positive = sum(1 for v in transfer_ic.values() if v > 0)
    signs = {np.sign(v) for v in transfer_ic.values() if pd.notna(v) and v != 0}
    sign_consistent = len(signs) <= 1

    # ---- T4: per-feature cross-symbol IC-sign consistency ----
    # If individual features' univariate IC vs tb_label flip sign across
    # symbols, the pooled model is fed contradictory training signal —
    # the iter-v3/094 sign-inconsistency failure mode.  Diagnostic only.
    print("\nT4 — per-feature univariate IC sign consistency across symbols (diagnostic):")
    t4_rows = []
    for feat in V3_FEATURE_COLUMNS:
        ics = {}
        for sym in SYMBOLS:
            d = panels[sym]
            ics[sym] = rank_ic(
                d[feat].to_numpy(dtype=np.float64),
                d["tb_label"].to_numpy(dtype=np.float64),
            )
        vals = [ics[s] for s in SYMBOLS]
        feat_signs = {np.sign(v) for v in vals if pd.notna(v) and v != 0}
        t4_rows.append(
            {
                "feature": feat,
                "ic_BCH": round(ics["BCHUSDT"], 5),
                "ic_LDO": round(ics["LDOUSDT"], 5),
                "ic_TRX": round(ics["TRXUSDT"], 5),
                "sign_consistent": len(feat_signs) <= 1,
            }
        )
    t4 = pd.DataFrame(t4_rows)
    t4.to_csv(OUT / "T4_feature_sign_consistency.csv", index=False)
    n_consistent = int(t4["sign_consistent"].sum())
    print(t4.to_string(index=False))
    print(
        f"  -> {n_consistent}/{len(V3_FEATURE_COLUMNS)} features have "
        f"sign-consistent univariate IC across all 3 symbols"
    )

    # ---- GO / NO-GO verdict ----
    go_ic = t5_headline >= GO_T5_MIN
    go_breadth = n_positive >= GO_MIN_POSITIVE_SYMBOLS
    go_sign = sign_consistent
    verdict_go = go_ic and go_breadth and go_sign

    t5 = pd.DataFrame(
        [
            {"metric": "T5_headline_mean_transfer_ic", "value": round(t5_headline, 5)},
            {"metric": "within_symbol_mean_ic", "value": round(within_mean, 5)},
            {"metric": "n_positive_transfer_symbols", "value": n_positive},
            {"metric": "transfer_sign_consistent", "value": sign_consistent},
            {"metric": "GO_threshold_T5_min", "value": GO_T5_MIN},
            {"metric": "GO_threshold_min_positive", "value": GO_MIN_POSITIVE_SYMBOLS},
            {"metric": "VERDICT_GO", "value": verdict_go},
        ]
    )
    t5.to_csv(OUT / "T5_go_nogo_summary.csv", index=False)

    print("\n" + "=" * 78)
    print("GO / NO-GO VERDICT")
    print("=" * 78)
    print(f"  T5 headline (mean LOSO cross-symbol transfer IC) : {t5_headline:+.5f}")
    print(f"  within-symbol benchmark mean IC                  : {within_mean:+.5f}")
    print(f"  positive-transfer symbols                        : {n_positive}/3")
    print(f"  transfer-IC sign consistent across symbols       : {sign_consistent}")
    print(f"  feature-level sign-consistent                    : {n_consistent}/14")
    print("  ----")
    print(f"  gate 1  T5 >= {GO_T5_MIN}            : {'PASS' if go_ic else 'FAIL'}")
    print(f"  gate 2  >= {GO_MIN_POSITIVE_SYMBOLS} positive symbols  : {'PASS' if go_breadth else 'FAIL'}")
    print(f"  gate 3  transfer-IC sign consistent : {'PASS' if go_sign else 'FAIL'}")
    print("  ----")
    print(f"  VERDICT: {'GO' if verdict_go else 'NO-GO'}")
    print("=" * 78)


if __name__ == "__main__":
    main()
