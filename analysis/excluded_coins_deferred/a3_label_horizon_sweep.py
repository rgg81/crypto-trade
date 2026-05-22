"""iter-v3/101 — ANGLE 3 — ALTERNATIVE LABEL / HORIZON CONFIGS ON THE MAJORS.

THE QUESTION
------------
The /059 triple-barrier label (ATR TP=2.0 / SL=1.0, timeout 21 candles) was
tuned for the v3 ALTCOIN universe. The /101 first IC screen used it verbatim
and found 8 of 10 majors THIN. But the majors are not obligated to respond to
a label calibrated on a different universe — a label whose barriers and
horizon were never optimized for BTC/ETH/SOL volatility.

This angle sweeps the LABEL and the HORIZON for the majors:

  C1  TRIPLE-BARRIER BARRIER-MULTIPLE SWEEP. The within-symbol purged-5-fold
      CV rank-IC of the frozen 14-feature stack vs triple-barrier labels at
      (TP, SL) in {(1.0,1.0), (1.5,1.0), (2.0,1.0)=/059, (3.0,1.5), (2.0,2.0)}
      — per major. Does any major's headline IC improve materially under a
      different barrier geometry?

  C2  TIMEOUT SWEEP. Same metric, /059 barriers, timeout in
      {6, 12, 21=/059, 30, 45} candles — per major. Does a shorter or longer
      holding horizon surface signal the 21-candle horizon misses?

  C3  FIXED-HORIZON RETURN LABEL. Drop triple-barrier entirely; label =
      sign(forward h-candle return) for h in {3, 6, 9, 12}. The within-symbol
      CV-IC of the 14-feature stack vs this label — per major. A simple
      directional label removes the barrier-geometry confound: if the majors
      carry directional signal at ALL it should show here.

The headline comparison is always the same: does ANY label config push a
major's within-symbol CV-IC clearly above the +0.060 GENUINE band, and does
it beat that major's /059-label number? If a different label lifts (say) BTC
from -0.069 to +0.10, the /101 first screen's THIN verdict was a label
artifact. If every config keeps the majors thin, the thin signal is
label-independent — a property of 8h major prediction.

This is EDA. No backtest, no brief, no src/ changes. IS-only.

NO-CHEATING
-----------
  - OOS_CUTOFF_MS = 1742774400000. Every row open_time < cutoff.
  - 24-month per-symbol burn-in.
  - Each label variant is computed on the FULL panel (so the forward scan
    sees post-burn-in bars) then rows restricted to the IS span.
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
FEE_PCT = 0.1
EMBARGO_CANDLES = 22
INTERVAL_MS = 8 * 60 * 60 * 1000
DATA_DIR = Path("data/features_v3")
OUT = Path("analysis/iteration_v3-101")

# All 10 excluded majors + altcoin reference.
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


def triple_barrier_label(
    df: pd.DataFrame, tp_mult: float, sl_mult: float, timeout_candles: int
) -> np.ndarray:
    """Generalized triple-barrier directional label (+1/-1) for arbitrary
    (TP, SL) ATR multiples and timeout. Same first-hit logic as the /059 rule.
    """
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
    """Label = sign(forward h-candle return). +1 if fwd ret >= 0 else -1."""
    out = df.reset_index(drop=True)
    close = out["close"].to_numpy(dtype=np.float64)
    n = len(out)
    labels = np.zeros(n, dtype=np.int64)
    for i in range(n - h):
        if close[i] > 0:
            labels[i] = 1 if close[i + h] >= close[i] else -1
    return labels


def load_raw(symbol: str) -> pd.DataFrame | None:
    path = DATA_DIR / f"{symbol}_8h_features.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path).sort_values("open_time").reset_index(drop=True)
    return df


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


def cv_ic_for_label(df_is: pd.DataFrame, label: np.ndarray) -> float:
    """Within-symbol purged-5-fold CV rank-IC of the 14-feature LGB vs a
    directional label aligned to df_is's rows."""
    d = df_is.copy()
    d["lab"] = label
    d = d.dropna(subset=list(V3_FEATURE_COLUMNS)).reset_index(drop=True)
    if len(d) < 300:
        return float("nan")
    X = d[list(V3_FEATURE_COLUMNS)].to_numpy(dtype=np.float64)
    y = (d["lab"].to_numpy(dtype=int) == 1).astype(int)
    tgt = d["lab"].to_numpy(dtype=np.float64)
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
    print("iter-v3/101 ANGLE 3 — LABEL / HORIZON SWEEP ON THE MAJORS (IS-only)")
    print("=" * 78)

    universe = EXCLUDED_MAJORS + ALTCOINS
    raw: dict[str, pd.DataFrame] = {}
    for sym in universe:
        df = load_raw(sym)
        if df is None:
            print(f"  {sym}: parquet missing — skipped")
            continue
        raw[sym] = df
        print(f"  {sym:10s}: {len(df)} total rows loaded")

    # ---- C1: barrier-multiple sweep ----
    print("\nC1 — triple-barrier BARRIER-MULTIPLE sweep (within-symbol 5-fold CV-IC):")
    barrier_grid = [
        ("tp1.0_sl1.0", 1.0, 1.0, 21),
        ("tp1.5_sl1.0", 1.5, 1.0, 21),
        ("tp2.0_sl1.0_/059", 2.0, 1.0, 21),
        ("tp3.0_sl1.5", 3.0, 1.5, 21),
        ("tp2.0_sl2.0", 2.0, 2.0, 21),
    ]
    c1_rows = []
    for sym, df in raw.items():
        ism = is_mask_for(df)
        row = {"symbol": sym}
        msg_parts = []
        for name, tp, sl, to in barrier_grid:
            lab_full = triple_barrier_label(df, tp, sl, to)
            d_is = df[ism].copy()
            lab_is = lab_full[ism]
            ic = cv_ic_for_label(d_is, lab_is)
            row[name] = round(ic, 5) if pd.notna(ic) else np.nan
            msg_parts.append(f"{name.split('_')[0]}={ic:+.4f}")
        c1_rows.append(row)
        print(f"  {sym:10s}: " + "  ".join(msg_parts))
    c1 = pd.DataFrame(c1_rows)
    c1.to_csv(OUT / "C1_barrier_multiple_sweep.csv", index=False)

    # ---- C2: timeout sweep ----
    print("\nC2 — triple-barrier TIMEOUT sweep (/059 barriers TP2.0/SL1.0):")
    timeout_grid = [6, 12, 21, 30, 45]
    c2_rows = []
    for sym, df in raw.items():
        ism = is_mask_for(df)
        row = {"symbol": sym}
        msg_parts = []
        for to in timeout_grid:
            lab_full = triple_barrier_label(df, 2.0, 1.0, to)
            d_is = df[ism].copy()
            lab_is = lab_full[ism]
            ic = cv_ic_for_label(d_is, lab_is)
            row[f"timeout_{to}"] = round(ic, 5) if pd.notna(ic) else np.nan
            msg_parts.append(f"t{to}={ic:+.4f}")
        c2_rows.append(row)
        print(f"  {sym:10s}: " + "  ".join(msg_parts))
    c2 = pd.DataFrame(c2_rows)
    c2.to_csv(OUT / "C2_timeout_sweep.csv", index=False)

    # ---- C3: fixed-horizon return label ----
    print("\nC3 — FIXED-HORIZON return-sign label (no barriers):")
    horizon_grid = [3, 6, 9, 12]
    c3_rows = []
    for sym, df in raw.items():
        ism = is_mask_for(df)
        row = {"symbol": sym}
        msg_parts = []
        for h in horizon_grid:
            lab_full = fixed_horizon_label(df, h)
            d_is = df[ism].copy()
            lab_is = lab_full[ism].astype(float)
            lab_is[lab_is == 0] = np.nan  # tail rows with no h-forward bar
            ic = cv_ic_for_label(d_is.assign(_t=lab_is).dropna(subset=["_t"]),
                                 d_is.assign(_t=lab_is).dropna(subset=["_t"])["_t"].to_numpy())
            row[f"fwd_sign_{h}"] = round(ic, 5) if pd.notna(ic) else np.nan
            msg_parts.append(f"h{h}={ic:+.4f}")
        c3_rows.append(row)
        print(f"  {sym:10s}: " + "  ".join(msg_parts))
    c3 = pd.DataFrame(c3_rows)
    c3.to_csv(OUT / "C3_fixed_horizon_label.csv", index=False)

    # ---- summary: best label config per symbol ----
    print("\n" + "=" * 78)
    print("ANGLE 3 SUMMARY — best within-symbol CV-IC across ALL label configs")
    print("=" * 78)
    sum_rows = []
    for sym in raw:
        vals = []
        for tbl, cols in [
            (c1, [c for c in c1.columns if c != "symbol"]),
            (c2, [c for c in c2.columns if c != "symbol"]),
            (c3, [c for c in c3.columns if c != "symbol"]),
        ]:
            r = tbl[tbl["symbol"] == sym]
            if not r.empty:
                for c in cols:
                    v = r[c].iloc[0]
                    if pd.notna(v):
                        vals.append((c, float(v)))
        if not vals:
            continue
        best_cfg, best_ic = max(vals, key=lambda t: t[1])
        v059 = c1[c1["symbol"] == sym]["tp2.0_sl1.0_/059"]
        v059 = float(v059.iloc[0]) if not v059.empty and pd.notna(v059.iloc[0]) else np.nan
        sum_rows.append(
            {
                "symbol": sym,
                "best_label_config": best_cfg,
                "best_cv_ic": round(best_ic, 5),
                "ic_at_059_label": round(v059, 5) if pd.notna(v059) else np.nan,
                "lift_vs_059": round(best_ic - v059, 5) if pd.notna(v059) else np.nan,
                "clears_genuine_060": best_ic >= 0.060,
            }
        )
        print(
            f"  {sym:10s}: best={best_ic:+.5f} via {best_cfg:18s}  "
            f"(/059-label {v059:+.5f}, lift {best_ic - v059:+.5f})  "
            f"{'GENUINE' if best_ic >= 0.060 else 'thin'}"
        )
    s = pd.DataFrame(sum_rows)
    s.to_csv(OUT / "C4_best_label_per_symbol.csv", index=False)
    print("\n  Files: C1_barrier_multiple_sweep.csv, C2_timeout_sweep.csv,")
    print("         C3_fixed_horizon_label.csv, C4_best_label_per_symbol.csv")


if __name__ == "__main__":
    main()
