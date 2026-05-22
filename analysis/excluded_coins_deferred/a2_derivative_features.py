"""iter-v3/101 — ANGLE 2 — DERIVATIVE / MICROSTRUCTURE FEATURES ON THE MAJORS.

THE BIG UNTESTED ANGLE
----------------------
The /101 first IC screen tested ONE config — the frozen 14-feature
V3_FEATURE_COLUMNS stack (all OHLCV-derived: returns, Hurst, skew/kurt,
vwap-dev, etc.) — vs the /059 triple-barrier label. That stack contains ZERO
derivative features.

The liquid majors' genuine structural advantage over the thin altcoins is
their DEEP, liquid derivatives markets: funding rates, perp-spot basis, open
interest. The /086/093 conclusion was that 7 crypto-native feed families were
INERT-by-importance on thin altcoins (BCH/LDO/TRX). But that is an ALTCOIN
finding — funding rate on BTC/ETH/SOL is a real, economically meaningful,
mean-reverting cost-of-leverage signal, and the basis is its tradeable proxy.
The /086 verdict explicitly never tested derivatives on the deep-market
universe.

The v3 feature parquets ALREADY carry the derivative features (computed by
features_v3/__init__.py): funding_rate_zscore_30, funding_momentum_3,
funding_accel_3, funding_sign_persist_9, funding_price_divergence_6,
btc_funding_rate_zscore_30, basis_zscore_30, basis_momentum_3,
basis_extreme_flag. This angle measures their predictive content on the
majors at the EDA level.

WHAT THIS ANGLE MEASURES
------------------------
  B1  Univariate rank-IC of EACH derivative feature vs the /059 triple-barrier
      directional label AND vs the forward 1/3/9-candle return — per major.
      Sign-consistency across 3 IS thirds. This finds whether ANY single
      derivative feature carries directional content on the deep markets.

  B2  WITHIN-symbol purged-5-fold-CV rank-IC of a DERIVATIVES-ONLY LightGBM
      (the 9 derivative features above) vs the triple-barrier label — per
      major. Directly comparable to the /101 14-feature-stack screen: does a
      derivatives-only model beat the OHLCV-stack THIN result?

  B3  AUGMENTED stack — the 14 OHLCV features + the 9 derivative features (23
      total) — within-symbol CV-IC per major. Does ADDING derivatives to the
      frozen stack lift the headline IC vs the /101 14-feature number? This is
      the directly actionable test: it is the exact feature set a real
      iter-v3/101 backtest would use.

  B4  FUNDING-EXTREME conditional return. Funding theory says when funding is
      very positive (longs crowded, expensive) forward returns mean-revert
      DOWN; very negative funding -> revert UP. Bucket each major's bars by
      funding_rate_zscore_30 decile and report the mean forward 3-candle
      return per decile. A monotone decreasing pattern = a real, simple,
      economically-grounded edge that does NOT need a tree to exploit.

This is EDA. No backtest, no brief, no src/ changes. IS-only.

NO-CHEATING
-----------
  - OOS_CUTOFF_MS = 1742774400000. Every row open_time < cutoff.
  - 24-month per-symbol burn-in.
  - /059 production triple-barrier label, byte-identical to the /101 screen.
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

OOS_CUTOFF_MS = 1742774400000
TRAINING_MONTHS = 24
TIMEOUT_MIN = 10080
TP_MULT = 2.0
SL_MULT = 1.0
FEE_PCT = 0.1
EMBARGO_CANDLES = 22
DATA_DIR = Path("data/features_v3")
OUT = Path("analysis/iteration_v3-101")

# The 10 v3-excluded liquid majors.
EXCLUDED_MAJORS = (
    "BTCUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "DOTUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "NEARUSDT",
)
# v3's altcoin core — comparison baseline.
ALTCOINS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")

# The /059 14-feature OHLCV stack.
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

# The derivative / microstructure features present in the v3 parquets.
DERIV_FEATURES = (
    "funding_rate_zscore_30",
    "funding_momentum_3",
    "funding_accel_3",
    "funding_sign_persist_9",
    "funding_price_divergence_6",
    "btc_funding_rate_zscore_30",
    "basis_zscore_30",
    "basis_momentum_3",
    "basis_extreme_flag",
)

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


def triple_barrier_label(df: pd.DataFrame) -> pd.DataFrame:
    out = df.reset_index(drop=True).copy()
    n = len(out)
    high = out["high"].to_numpy(dtype=np.float64)
    low = out["low"].to_numpy(dtype=np.float64)
    close = out["close"].to_numpy(dtype=np.float64)
    close_time = out["close_time"].to_numpy(dtype=np.int64)
    natr = out["natr_21_raw"].to_numpy(dtype=np.float64)
    timeout_ms = TIMEOUT_MIN * 60 * 1000
    labels = np.zeros(n, dtype=np.int64)
    for i in range(n):
        entry = close[i]
        if entry <= 0:
            continue
        atr = (natr[i] / 100.0) * entry if np.isfinite(natr[i]) else entry * 0.02
        long_tp = entry + atr * TP_MULT
        long_sl = entry - atr * SL_MULT
        short_tp = entry - atr * TP_MULT
        short_sl = entry + atr * SL_MULT
        deadline = close_time[i] + timeout_ms
        long_result = short_result = 0
        long_step = short_step = -1
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
                long_result = -2
            if short_result == 0:
                short_result = -2
        fwd_ret = (last_close - entry) / entry * 100.0 if entry != 0 else 0.0
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
    out["tb_label"] = labels
    return out


def add_fwd_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Add forward 1/3/9-candle simple returns (look-ahead-safe: the value at
    bar i is the return from i's close to i+h's close — used only as a TARGET,
    never as a feature)."""
    out = df.copy()
    close = out["close"].to_numpy(dtype=np.float64)
    for h in (1, 3, 9):
        fwd = np.full(len(out), np.nan)
        for i in range(len(out) - h):
            if close[i] > 0:
                fwd[i] = (close[i + h] - close[i]) / close[i] * 100.0
        out[f"fwd_ret_{h}"] = fwd
    return out


def load_symbol_is(symbol: str) -> pd.DataFrame | None:
    path = DATA_DIR / f"{symbol}_8h_features.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path).sort_values("open_time").reset_index(drop=True)
    first_ms = int(df["open_time"].min())
    burnin_end = first_ms + TRAINING_MONTHS * 30 * 24 * 60 * 60 * 1000
    df = triple_barrier_label(df)
    df = add_fwd_returns(df)
    is_mask = (df["open_time"] >= burnin_end) & (df["open_time"] < OOS_CUTOFF_MS)
    isd = df[is_mask].copy()
    isd["symbol"] = symbol
    isd["y"] = (isd["tb_label"] == 1).astype(int)
    return isd.reset_index(drop=True)


def rank_ic(pred: np.ndarray, target: np.ndarray) -> float:
    mask = np.isfinite(pred) & np.isfinite(target)
    if mask.sum() < 30:
        return float("nan")
    c = pd.Series(pred[mask]).rank().corr(pd.Series(target[mask]).rank())
    return float(c) if pd.notna(c) else float("nan")


def purged_kfold_indices(n: int, k: int, embargo: int):
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
        yield np.where(train_mask)[0], test_idx


def cv_ic(d: pd.DataFrame, feats: tuple[str, ...]) -> tuple[float, int]:
    sub = d.dropna(subset=list(feats)).reset_index(drop=True)
    if len(sub) < 200:
        return float("nan"), 0
    X = sub[list(feats)].to_numpy(dtype=np.float64)
    y = sub["y"].to_numpy(dtype=int)
    tgt = sub["tb_label"].to_numpy(dtype=np.float64)
    ics: list[float] = []
    for tr, te in purged_kfold_indices(len(sub), 5, EMBARGO_CANDLES):
        if len(np.unique(y[tr])) < 2 or len(te) < 30:
            continue
        m = lgb.LGBMClassifier(**LGB_PARAMS)
        m.fit(X[tr], y[tr])
        p = m.predict_proba(X[te])[:, 1]
        ic = rank_ic(p, tgt[te])
        if pd.notna(ic):
            ics.append(ic)
    return (float(np.nanmean(ics)) if ics else float("nan")), len(ics)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/101 ANGLE 2 — DERIVATIVE FEATURES ON THE MAJORS (IS-only)")
    print("=" * 78)

    panels: dict[str, pd.DataFrame] = {}
    for sym in EXCLUDED_MAJORS + ALTCOINS:
        d = load_symbol_is(sym)
        if d is None:
            print(f"  {sym}: parquet missing — skipped")
            continue
        # require derivative features to be present
        cov = d[list(DERIV_FEATURES)].notna().mean().min()
        if cov < 0.5:
            print(f"  {sym}: derivative-feature coverage {cov:.2f} < 0.5 — skipped")
            continue
        panels[sym] = d
        print(f"  {sym:10s}: {len(d):5d} IS rows, deriv-feature min-coverage {cov:.3f}")

    # ---- B1: univariate IC of each derivative feature ----
    print("\nB1 — univariate rank-IC of each derivative feature "
          "(vs triple-barrier label + fwd_ret_3):")
    b1_rows = []
    for sym, d in panels.items():
        n = len(d)
        bounds = [(0, n // 3), (n // 3, 2 * n // 3), (2 * n // 3, n)]
        for feat in DERIV_FEATURES:
            if feat not in d.columns:
                continue
            fv = d[feat].to_numpy(dtype=np.float64)
            ic_tb = rank_ic(fv, d["tb_label"].to_numpy(dtype=np.float64))
            ic_fwd = rank_ic(fv, d["fwd_ret_3"].to_numpy(dtype=np.float64))
            third_ics = []
            for lo, hi in bounds:
                seg = d.iloc[lo:hi]
                third_ics.append(
                    rank_ic(
                        seg[feat].to_numpy(dtype=np.float64),
                        seg["tb_label"].to_numpy(dtype=np.float64),
                    )
                )
            signs = {np.sign(v) for v in third_ics if pd.notna(v) and abs(v) > 0.02}
            b1_rows.append(
                {
                    "symbol": sym,
                    "feature": feat,
                    "ic_vs_tb_label": round(ic_tb, 5) if pd.notna(ic_tb) else np.nan,
                    "ic_vs_fwd_ret_3": round(ic_fwd, 5) if pd.notna(ic_fwd) else np.nan,
                    "third_1": round(third_ics[0], 5) if pd.notna(third_ics[0]) else np.nan,
                    "third_2": round(third_ics[1], 5) if pd.notna(third_ics[1]) else np.nan,
                    "third_3": round(third_ics[2], 5) if pd.notna(third_ics[2]) else np.nan,
                    "sign_stable": len(signs) <= 1,
                }
            )
    b1 = pd.DataFrame(b1_rows)
    b1.to_csv(OUT / "B1_deriv_univariate_ic.csv", index=False)
    # print the strongest |ic_vs_tb_label| per symbol
    for sym in panels:
        s = b1[b1["symbol"] == sym].copy()
        s["abs_ic"] = s["ic_vs_tb_label"].abs()
        top = s.nlargest(2, "abs_ic")
        msg = "  ".join(
            f"{r['feature']}={r['ic_vs_tb_label']:+.4f}"
            f"({'stable' if r['sign_stable'] else 'FLIP'})"
            for _, r in top.iterrows()
        )
        print(f"  {sym:10s} top-2: {msg}")

    # ---- B2: derivatives-ONLY model CV-IC ----
    print("\nB2 — DERIVATIVES-ONLY LightGBM within-symbol 5-fold CV rank-IC:")
    b2_rows = []
    for sym, d in panels.items():
        ic, nf = cv_ic(d, DERIV_FEATURES)
        b2_rows.append(
            {"symbol": sym, "deriv_only_cv_ic": round(ic, 5), "n_folds": nf}
        )
        print(f"  {sym:10s}: deriv-only CV-IC = {ic:+.5f}  ({nf} folds)")
    b2 = pd.DataFrame(b2_rows).sort_values(
        "deriv_only_cv_ic", ascending=False, na_position="last"
    )
    b2.to_csv(OUT / "B2_deriv_only_cv_ic.csv", index=False)

    # ---- B3: augmented (14 OHLCV + 9 deriv) CV-IC vs 14-only ----
    print("\nB3 — AUGMENTED stack (14 OHLCV + 9 deriv = 23) vs 14-only CV-IC:")
    b3_rows = []
    aug = V3_FEATURE_COLUMNS + DERIV_FEATURES
    for sym, d in panels.items():
        ic14, _ = cv_ic(d, V3_FEATURE_COLUMNS)
        ic23, nf = cv_ic(d, aug)
        delta = ic23 - ic14 if (pd.notna(ic23) and pd.notna(ic14)) else np.nan
        b3_rows.append(
            {
                "symbol": sym,
                "cv_ic_14_ohlcv": round(ic14, 5) if pd.notna(ic14) else np.nan,
                "cv_ic_23_augmented": round(ic23, 5) if pd.notna(ic23) else np.nan,
                "delta_ic": round(delta, 5) if pd.notna(delta) else np.nan,
                "n_folds": nf,
            }
        )
        print(
            f"  {sym:10s}: 14-only {ic14:+.5f}  ->  23-aug {ic23:+.5f}  "
            f"(delta {delta:+.5f})"
        )
    b3 = pd.DataFrame(b3_rows).sort_values(
        "cv_ic_23_augmented", ascending=False, na_position="last"
    )
    b3.to_csv(OUT / "B3_augmented_vs_ohlcv_cv_ic.csv", index=False)

    # ---- B4: funding-extreme conditional forward return ----
    print("\nB4 — forward 3-candle return by funding_rate_zscore_30 decile")
    print("     (funding theory: high funding -> revert DOWN; monotone decreasing"
          " = real edge):")
    b4_rows = []
    for sym, d in panels.items():
        sub = d.dropna(subset=["funding_rate_zscore_30", "fwd_ret_3"]).copy()
        if len(sub) < 300:
            continue
        sub["fz_decile"] = pd.qcut(
            sub["funding_rate_zscore_30"], 10, labels=False, duplicates="drop"
        )
        grp = sub.groupby("fz_decile")["fwd_ret_3"].agg(["mean", "count"])
        # monotonicity: Spearman of decile index vs mean fwd ret
        mono = rank_ic(
            grp.index.to_numpy(dtype=np.float64),
            grp["mean"].to_numpy(dtype=np.float64),
        )
        d1 = float(grp["mean"].iloc[0]) if len(grp) else np.nan
        d10 = float(grp["mean"].iloc[-1]) if len(grp) else np.nan
        b4_rows.append(
            {
                "symbol": sym,
                "n": len(sub),
                "fwd_ret_lowest_funding_decile": round(d1, 4),
                "fwd_ret_highest_funding_decile": round(d10, 4),
                "spread_low_minus_high": round(d1 - d10, 4),
                "decile_monotonicity_ic": round(mono, 4) if pd.notna(mono) else np.nan,
            }
        )
        print(
            f"  {sym:10s}: low-funding-decile fwd3 {d1:+.4f}%  "
            f"high-funding-decile {d10:+.4f}%  spread {d1 - d10:+.4f}%  "
            f"monotonicity-IC {mono:+.3f}"
        )
    b4 = pd.DataFrame(b4_rows)
    b4.to_csv(OUT / "B4_funding_extreme_conditional_return.csv", index=False)

    print("\n" + "=" * 78)
    print("ANGLE 2 SUMMARY")
    print("=" * 78)
    best_deriv = b2.iloc[0] if not b2.empty else None
    if best_deriv is not None:
        print(f"  best derivatives-only CV-IC: {best_deriv['symbol']} "
              f"{best_deriv['deriv_only_cv_ic']:+.5f}")
    pos_delta = b3[b3["delta_ic"] > 0.01]["symbol"].tolist()
    print(f"  majors where augmenting with derivatives lifts CV-IC by >+0.01: "
          f"{pos_delta if pos_delta else 'NONE'}")
    print("  Files: B1_deriv_univariate_ic.csv, B2_deriv_only_cv_ic.csv,")
    print("         B3_augmented_vs_ohlcv_cv_ic.csv,")
    print("         B4_funding_extreme_conditional_return.csv")


if __name__ == "__main__":
    main()
