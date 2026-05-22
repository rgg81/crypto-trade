"""iter-v3/101 — ANGLE 5 — REGIME CONDITIONING + ANGLE-3 MULTIPLE-TESTING AUDIT.

TWO PURPOSES
------------
PURPOSE 1 — REGIME CONDITIONING (the brief's angle 5).
A low average within-symbol IC can still be a tradeable edge if it concentrates
in an identifiable, ex-ante-detectable regime. Angle 1 found LTC's edge lives
entirely in high-vol bars (vol_low -0.070 / vol_high +0.142). This angle does
that decomposition SYSTEMATICALLY for all 10 majors: build each major's
purged-5-fold OOF prediction (frozen 14-feature stack + /059 label), then slice
the OOF rank-IC by:
   - realized-vol terciles (range_realized_vol_50)
   - Hurst regime (hurst_100 trend vs range)
   - BTC-trend regime (btc_ret_14d up vs down)
   - ADX regime (adx_14 strong-trend vs chop)
A major with a flat near-zero IC everywhere is genuinely thin. A major with a
strong IC in ONE regime + a near-zero IC elsewhere has a regime-GATED edge
that a gate could in principle harvest — that is a different verdict from
"thin everywhere".

PURPOSE 2 — ANGLE-3 MULTIPLE-TESTING AUDIT (selection-bias correction).
Angle 3 reported the BEST within-symbol CV-IC across 13 label configs per
symbol. Best-of-13 is a multiple-comparisons trap: the max of 13 noisy
estimates is upward-biased even on a symbol with zero true signal (Bailey/
Borwein/LdP/Zhu — selecting from >= 7 backtests guarantees an inflated IS
metric). This purpose quantifies that bias HONESTLY:
   - For each symbol, take the angle-3 winning label config and SPLIT the IS
     span into 2 halves. Measure the CV-IC on half 1 (the "selection" half)
     and on half 2 (the "confirmation" half). A genuine label edge transfers:
     half-2 IC ~ half-1 IC. A selection artifact does not: half-2 IC collapses.
   - This is the IS-only analogue of an out-of-sample check. It cannot touch
     OOS (forbidden) but it CAN expose a config whose IC is a cherry-picked
     in-sample maximum.

This is EDA. No backtest, no brief, no src/ changes. IS-only.

NO-CHEATING
-----------
  - OOS_CUTOFF_MS = 1742774400000. Every row open_time < cutoff.
  - 24-month per-symbol burn-in.
  - The half-1/half-2 split is WITHIN the IS span — it is NOT the OOS split.
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
EMBARGO_CANDLES = 22
INTERVAL_MS = 8 * 60 * 60 * 1000
DATA_DIR = Path("data/features_v3")
OUT = Path("analysis/iteration_v3-101")

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
ALTCOINS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")

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

# The angle-3 winning label config per symbol (read from C4_best_label_per_symbol;
# encoded here as (kind, params) so this script is standalone). Each tuple is
# ("tb", tp, sl, timeout) or ("fwd", horizon).
ANGLE3_WINNER = {
    "BTCUSDT": ("fwd", 3),
    "ETHUSDT": ("fwd", 9),
    "LINKUSDT": ("tb", 2.0, 1.0, 12),
    "LTCUSDT": ("fwd", 9),
    "DOTUSDT": ("tb", 3.0, 1.5, 21),
    "BNBUSDT": ("tb", 2.0, 1.0, 45),
    "SOLUSDT": ("tb", 2.0, 1.0, 45),
    "XRPUSDT": ("fwd", 6),
    "DOGEUSDT": ("tb", 2.0, 1.0, 45),
    "NEARUSDT": ("tb", 3.0, 1.5, 21),
    "BCHUSDT": ("tb", 3.0, 1.5, 21),
    "LDOUSDT": ("tb", 2.0, 1.0, 30),
    "TRXUSDT": ("fwd", 3),
}


def triple_barrier_label(
    df: pd.DataFrame, tp_mult: float, sl_mult: float, timeout_candles: int
) -> np.ndarray:
    out = df.reset_index(drop=True)
    n = len(out)
    high = out["high"].to_numpy(dtype=np.float64)
    low = out["low"].to_numpy(dtype=np.float64)
    close = out["close"].to_numpy(dtype=np.float64)
    close_time = out["close_time"].to_numpy(dtype=np.int64)
    natr = out["natr_21_raw"].to_numpy(dtype=np.float64)
    timeout_ms = timeout_candles * INTERVAL_MS
    labels = np.zeros(n, dtype=np.int64)
    for i in range(n):
        entry = close[i]
        if entry <= 0:
            continue
        atr = (natr[i] / 100.0) * entry if np.isfinite(natr[i]) else entry * 0.02
        long_tp = entry + atr * tp_mult
        long_sl = entry - atr * sl_mult
        short_tp = entry - atr * tp_mult
        short_sl = entry + atr * sl_mult
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
        fwd_ret = (last_close - entry) / entry if entry != 0 else 0.0
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
    return labels


def fixed_horizon_label(df: pd.DataFrame, h: int) -> np.ndarray:
    out = df.reset_index(drop=True)
    close = out["close"].to_numpy(dtype=np.float64)
    n = len(out)
    labels = np.zeros(n, dtype=np.int64)
    for i in range(n - h):
        if close[i] > 0:
            labels[i] = 1 if close[i + h] >= close[i] else -1
    return labels


def label_for(df: pd.DataFrame, spec: tuple) -> np.ndarray:
    if spec[0] == "tb":
        return triple_barrier_label(df, spec[1], spec[2], spec[3])
    return fixed_horizon_label(df, spec[1])


def load_raw(symbol: str) -> pd.DataFrame | None:
    path = DATA_DIR / f"{symbol}_8h_features.parquet"
    if not path.exists():
        return None
    return pd.read_parquet(path).sort_values("open_time").reset_index(drop=True)


def is_mask_for(df: pd.DataFrame) -> np.ndarray:
    first_ms = int(df["open_time"].min())
    burnin_end = first_ms + TRAINING_MONTHS * 30 * 24 * 60 * 60 * 1000
    return ((df["open_time"] >= burnin_end) & (df["open_time"] < OOS_CUTOFF_MS)).to_numpy()


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


def oof_pred(d: pd.DataFrame, label_col: str) -> np.ndarray:
    X = d[list(V3_FEATURE_COLUMNS)].to_numpy(dtype=np.float64)
    y = (d[label_col].to_numpy(dtype=int) == 1).astype(int)
    oof = np.full(len(d), np.nan)
    for tr, te in purged_kfold_indices(len(d), 5, EMBARGO_CANDLES):
        if len(np.unique(y[tr])) < 2:
            continue
        m = lgb.LGBMClassifier(**LGB_PARAMS)
        m.fit(X[tr], y[tr])
        oof[te] = m.predict_proba(X[te])[:, 1]
    return oof


def cv_ic_for(d: pd.DataFrame, label_col: str) -> float:
    if len(d) < 200:
        return float("nan")
    X = d[list(V3_FEATURE_COLUMNS)].to_numpy(dtype=np.float64)
    y = (d[label_col].to_numpy(dtype=int) == 1).astype(int)
    tgt = d[label_col].to_numpy(dtype=np.float64)
    if len(np.unique(y)) < 2:
        return float("nan")
    ics: list[float] = []
    for tr, te in purged_kfold_indices(len(d), 5, EMBARGO_CANDLES):
        if len(np.unique(y[tr])) < 2 or len(te) < 30:
            continue
        m = lgb.LGBMClassifier(**LGB_PARAMS)
        m.fit(X[tr], y[tr])
        p = m.predict_proba(X[te])[:, 1]
        ic = rank_ic(p, tgt[te])
        if pd.notna(ic):
            ics.append(ic)
    return float(np.nanmean(ics)) if ics else float("nan")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/101 ANGLE 5 — REGIME CONDITIONING + ANGLE-3 MT AUDIT (IS-only)")
    print("=" * 78)

    raw: dict[str, pd.DataFrame] = {}
    for sym in EXCLUDED_MAJORS + ALTCOINS:
        df = load_raw(sym)
        if df is None:
            print(f"  {sym}: parquet missing — skipped")
            continue
        raw[sym] = df

    # ---- PURPOSE 1: regime conditioning (frozen 14-stack + /059 label) ----
    print("\nE1 — regime-conditioned OOF rank-IC (frozen 14-feature stack, "
          "/059 triple-barrier label):")
    e1_rows = []
    for sym in EXCLUDED_MAJORS:
        if sym not in raw:
            continue
        df = raw[sym]
        ism = is_mask_for(df)
        d = df.copy()
        d["lab"] = triple_barrier_label(df, 2.0, 1.0, 21)
        d = d[ism].copy()
        d = d.dropna(subset=list(V3_FEATURE_COLUMNS) + ["adx_14"]).reset_index(drop=True)
        if len(d) < 300:
            continue
        d["oof"] = oof_pred(d, "lab")
        d = d.dropna(subset=["oof"]).reset_index(drop=True)
        vt = d["range_realized_vol_50"].quantile([1 / 3, 2 / 3]).to_numpy()
        adx_med = d["adx_14"].median()
        regimes = {
            "vol_low": d["range_realized_vol_50"] <= vt[0],
            "vol_mid": (d["range_realized_vol_50"] > vt[0])
            & (d["range_realized_vol_50"] <= vt[1]),
            "vol_high": d["range_realized_vol_50"] > vt[1],
            "hurst_trend": d["hurst_100"] > 0.5,
            "hurst_range": d["hurst_100"] <= 0.5,
            "btc_up": d["btc_ret_14d"] > 0,
            "btc_down": d["btc_ret_14d"] <= 0,
            "adx_strong": d["adx_14"] > adx_med,
            "adx_chop": d["adx_14"] <= adx_med,
        }
        row = {"symbol": sym, "full_ic": round(
            rank_ic(d["oof"].to_numpy(np.float64), d["lab"].to_numpy(np.float64)), 5)}
        for name, mask in regimes.items():
            seg = d[mask]
            ic = rank_ic(
                seg["oof"].to_numpy(dtype=np.float64),
                seg["lab"].to_numpy(dtype=np.float64),
            )
            row[name] = round(ic, 5) if pd.notna(ic) else np.nan
        # the single best-and-worst regime spread
        reg_vals = {k: v for k, v in row.items()
                    if k not in ("symbol", "full_ic") and pd.notna(v)}
        row["best_regime"] = max(reg_vals, key=reg_vals.get) if reg_vals else "n/a"
        row["best_regime_ic"] = round(max(reg_vals.values()), 5) if reg_vals else np.nan
        e1_rows.append(row)
        print(
            f"  {sym:10s}: full {row['full_ic']:+.4f}  "
            f"vol[{row['vol_low']:+.3f}/{row['vol_mid']:+.3f}/{row['vol_high']:+.3f}]  "
            f"best={row['best_regime']}({row['best_regime_ic']:+.3f})"
        )
    e1 = pd.DataFrame(e1_rows)
    e1.to_csv(OUT / "E1_regime_conditioned_ic.csv", index=False)

    # ---- PURPOSE 2: angle-3 multiple-testing audit (half-1 vs half-2) ----
    print("\nE2 — angle-3 winning-label MULTIPLE-TESTING audit "
          "(IS half-1 'selection' vs half-2 'confirmation'):")
    print("     genuine label edge: half-2 IC ~ half-1 IC. selection artifact:"
          " half-2 collapses.")
    e2_rows = []
    for sym in EXCLUDED_MAJORS + ALTCOINS:
        if sym not in raw:
            continue
        df = raw[sym]
        spec = ANGLE3_WINNER[sym]
        ism = is_mask_for(df)
        d = df.copy()
        lab = label_for(df, spec)
        d["lab"] = lab
        d = d[ism].copy()
        d["lab"] = d["lab"].replace(0, np.nan)  # drop tail rows with no label
        d = d.dropna(subset=list(V3_FEATURE_COLUMNS) + ["lab"]).reset_index(drop=True)
        if len(d) < 600:
            e2_rows.append({"symbol": sym, "note": "insufficient"})
            continue
        half = len(d) // 2
        h1 = d.iloc[: half - EMBARGO_CANDLES].reset_index(drop=True)
        h2 = d.iloc[half:].reset_index(drop=True)
        ic1 = cv_ic_for(h1, "lab")
        ic2 = cv_ic_for(h2, "lab")
        spec_str = (
            f"tb_tp{spec[1]}_sl{spec[2]}_t{spec[3]}" if spec[0] == "tb"
            else f"fwd_h{spec[1]}"
        )
        decay = ic2 - ic1 if (pd.notna(ic1) and pd.notna(ic2)) else np.nan
        e2_rows.append(
            {
                "symbol": sym,
                "winning_label": spec_str,
                "ic_is_half1": round(ic1, 5) if pd.notna(ic1) else np.nan,
                "ic_is_half2": round(ic2, 5) if pd.notna(ic2) else np.nan,
                "half2_minus_half1": round(decay, 5) if pd.notna(decay) else np.nan,
                "half2_still_genuine": bool(pd.notna(ic2) and ic2 >= 0.060),
                "both_halves_positive": bool(
                    pd.notna(ic1) and pd.notna(ic2) and ic1 > 0 and ic2 > 0
                ),
            }
        )
        print(
            f"  {sym:10s} [{spec_str:18s}]: half1 {ic1:+.5f}  half2 {ic2:+.5f}  "
            f"(decay {decay:+.5f})  "
            f"{'BOTH+' if (pd.notna(ic1) and pd.notna(ic2) and ic1 > 0 and ic2 > 0) else 'NOT-both+'}"
        )
    e2 = pd.DataFrame(e2_rows)
    e2.to_csv(OUT / "E2_angle3_multiple_testing_audit.csv", index=False)

    print("\n" + "=" * 78)
    print("ANGLE 5 SUMMARY")
    print("=" * 78)
    survivors = [
        r["symbol"] for r in e2_rows
        if r.get("half2_still_genuine") and r.get("both_halves_positive")
    ]
    print(f"  majors+alts whose angle-3 winning label still clears GENUINE "
          f"(+0.060) on IS half-2 AND is positive on both halves: "
          f"{survivors if survivors else 'NONE'}")
    print("  E1 = is any major's thin full-IC actually a strong regime-gated")
    print("       edge (read best_regime_ic vs full_ic)?")
    print("  Files: E1_regime_conditioned_ic.csv,")
    print("         E2_angle3_multiple_testing_audit.csv")


if __name__ == "__main__":
    main()
