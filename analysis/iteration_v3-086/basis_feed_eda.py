"""iter-v3/086 — Cycle-3 EXPLORATION #5 EDA — the COMMITTED AXIS: a NEW
crypto-native data feed (perp-spot BASIS), IS-only.

WHY A NEW DATA FEED.  Cycle 3 is 4/10 with 0 clean PROMISING.  The v3 funding
axis is a 5-data-point CLOSED verdict (/019/023/024/082/085) — closed across BOTH
direct-feature and composed-sign-switch constructions.  /085 Critic Rec #4: the
highest-value untried structural axis is a NEW crypto-native data feed.  Every v3
feature to date is derived from OHLCV or the funding rate; the basis brings in a
genuinely new economic primitive.

WHY BASIS, NOT OPEN INTEREST.  History depth is the binding constraint.  The v3 IS
window runs from each symbol's earliest perp 8h data to 2025-03-24:
    BCH perp 2020-01-01  (IS 5727 rows)
    TRX perp 2020-01-15  (IS 5669 rows)
    LDO perp 2022-09-22  (IS 2741 rows)
The Binance /futures/data/openInterestHist API returns ONLY the last ~30 days
(VERIFIED: oldest row 2026-04-17; explicit 2021 startTime → "parameter invalid").
The data.binance.vision OI metrics archives (daily/metrics/) start ~2021-12 for
BCH/TRX (VERIFIED: 2021-09 → HTTP 404, 2021-12 → HTTP 200) — they MISS ~2 years of
the BCH/TRX IS window (~62% of BCH/TRX IS rows would be NaN).  OI is UNUSABLE.

The perp-spot BASIS is computable from data v3 already has (perp 8h klines) PLUS
spot 8h klines, and spot klines have FULL IS depth (VERIFIED on
data.binance.vision: BCH spot from 2019-11-28, TRX from 2018-06-11, LDO from
2022-05-09 — every symbol's spot covers its perp IS window).  Basis is the only
candidate feed with adequate history.

THE FEED + FEATURES.  Basis(t) = (perp_close[t] - spot_close[t]) / spot_close[t]
— the perp-spot premium, the canonical sentiment/carry primitive of a perpetual
market.  Persistent positive basis = leveraged-long crowding; the premium index
trades FASTER than the funding clamp (funding settles every 8h on a lag, the
premium reprices continuously).  This EDA validates a 3-feature basis family:
    basis_zscore_30     — 30-bar (10-day) past-only z-score of basis
    basis_momentum_3    — basis[t] - basis[t-3] (premium building / unwinding)
    basis_extreme_flag  — sign-persistence: sign(basis).shift(1).rolling(9).mean()

PAST-ONLY / REPORTING-LAG.  perp_close[t] and spot_close[t] both settle AT candle
close_time(t).  The basis(t) is therefore knowable at bar t CLOSE, NOT at bar t
open.  Every basis feature is computed on basis.shift(1) — bar t's decision uses
basis[t-1] and earlier ONLY (the previous fully-closed candle).  This is STRICTER
than the funding convention (funding broadcasts ~5 min before settlement, so
funding_rate[t] is knowable at bar t open; basis needs both closes, so it lags one
full candle).  Verified in Section "PAST-ONLY AUDIT" below.

NO CHEATING:
  - IS data only (open_time < OOS_CUTOFF_DATE 2025-03-24).  OOS never loaded.
  - OOS_CUTOFF_DATE / training_months not read as tunables, not modified.
  - All basis features are PAST-ONLY (basis.shift(1) — strict one-candle lag).
  - The 70/30 incremental-info split is chronological WITHIN the IS window — an
    EDA generalisation probe, not the production walk-forward.
  - NO design parameter is selected on any metric: the basis z-score window (30)
    is fixed a-priori at the funding-settlement-cycle convention (30 8h-candles =
    10 days, identical to funding_v3.py FUNDING_ZSCORE_WINDOW); the momentum lag
    (3) and the sign-persistence window (9) are fixed a-priori at the established
    /082 funding-family construction (funding_momentum_3 / funding_sign_persist_9).
    No window is swept; no candidate is ranked on an IS or OOS metric.

Run:  uv run python analysis/iteration_v3-086/basis_feed_eda.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

OOS_CUTOFF_MS = int(pd.Timestamp("2025-03-24", tz="UTC").timestamp() * 1000)
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
OUT_DIR = Path("analysis/iteration_v3-086")

# --- a-priori fixed feature parameters (NOT swept, NOT tuned) ---------------
BASIS_Z_WINDOW = 30   # = funding_v3.py FUNDING_ZSCORE_WINDOW (10 days @ 8h)
BASIS_MOM_LAG = 3     # = /082 funding_momentum_3 construction
BASIS_SIGN_WINDOW = 9  # = /082 funding_sign_persist_9 construction
Z_CLIP = 10.0         # = funding_v3.py ZSCORE_CLIP (LightGBM-stability clip)

# 14-feature /059 anchor stack (BASELINE_V3.md) — for orthogonality + incremental.
ANCHOR_14 = (
    "max_dd_window_50", "ema_spread_atr_20", "ret_kurt_50", "ret_skew_200",
    "range_realized_vol_50", "hurst_diff_100_50", "ret_kurt_200", "hurst_100",
    "btc_ret_14d", "ret_skew_50", "vwap_dev_20", "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d", "regime_momentum_signed_5d",
)

# Triple-barrier label parameters — the /059-canonical ATR multipliers + timeout.
ATR_TP_MULT = 2.0
ATR_SL_MULT = 1.0
TIMEOUT_CANDLES = 21


# ---------------------------------------------------------------------------
# Basis-feature construction (PAST-ONLY)
# ---------------------------------------------------------------------------
def compute_basis_features(perp: pd.DataFrame, spot: pd.DataFrame) -> pd.DataFrame:
    """Build the 3-feature basis family on a perp frame, merging spot close.

    Basis(t) = (perp_close[t] - spot_close[t]) / spot_close[t].  Both closes
    settle at candle close_time(t) — basis(t) is knowable only at bar t CLOSE.
    Every feature is computed on basis.shift(1): a strict one-candle lag, so
    bar t's feature uses basis[t-1] and earlier ONLY.
    """
    df = perp[["open_time", "close"]].copy()
    df = df.rename(columns={"close": "perp_close"})
    sp = spot[["open_time", "close"]].rename(columns={"close": "spot_close"})
    df = df.merge(sp, on="open_time", how="left")

    # raw basis — knowable at candle CLOSE (both closes settle at close_time)
    basis = (df["perp_close"] - df["spot_close"]) / df["spot_close"]
    df["basis_raw"] = basis

    # PAST-ONLY: shift basis by one full candle before ALL downstream stats.
    b = basis.shift(1)

    # F1 — basis_zscore_30 : 30-bar past-only z-score
    rmean = b.rolling(BASIS_Z_WINDOW, min_periods=BASIS_Z_WINDOW).mean()
    rstd = b.rolling(BASIS_Z_WINDOW, min_periods=BASIS_Z_WINDOW).std(ddof=1)
    z = (b - rmean) / rstd.replace(0, np.nan)
    df["basis_zscore_30"] = z.clip(-Z_CLIP, Z_CLIP)

    # F2 — basis_momentum_3 : 3-bar change of (already-lagged) basis
    df["basis_momentum_3"] = b - b.shift(BASIS_MOM_LAG)

    # F3 — basis_extreme_flag : sign-persistence over 9 bars of lagged basis
    df["basis_extreme_flag"] = np.sign(b).rolling(BASIS_SIGN_WINDOW,
                                                  min_periods=BASIS_SIGN_WINDOW).mean()
    return df


# ---------------------------------------------------------------------------
# Triple-barrier directional label (self-contained replication)
# ---------------------------------------------------------------------------
def triple_barrier_label(df: pd.DataFrame) -> np.ndarray:
    """Directional triple-barrier label: +1 if long-PnL > short-PnL else -1.

    ATR(14)-scaled TP/SL barriers, 21-candle timeout — the /059-canonical
    labeling.  The label at bar t scans FORWARD (t+1 .. t+21); it is the target
    of the IC analysis, not a feature.  Returns NaN for the trailing 21 bars.
    """
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    close = df["close"].to_numpy(float)
    n = len(close)

    # ATR(14) — Wilder true range, simple 14-bar mean (EDA-grade).
    prev_close = np.concatenate([[close[0]], close[:-1]])
    tr = np.maximum.reduce([
        high - low, np.abs(high - prev_close), np.abs(low - prev_close)
    ])
    atr = pd.Series(tr).rolling(14, min_periods=14).mean().to_numpy()

    label = np.full(n, np.nan)
    for t in range(n - TIMEOUT_CANDLES):
        a = atr[t]
        if not np.isfinite(a) or a <= 0:
            continue
        entry = close[t]
        tp_up = entry + ATR_TP_MULT * a
        sl_dn = entry - ATR_SL_MULT * a
        tp_dn = entry - ATR_TP_MULT * a
        sl_up = entry + ATR_SL_MULT * a
        long_pnl = short_pnl = None
        for k in range(t + 1, t + 1 + TIMEOUT_CANDLES):
            if long_pnl is None:
                if high[k] >= tp_up:
                    long_pnl = ATR_TP_MULT * a / entry
                elif low[k] <= sl_dn:
                    long_pnl = -ATR_SL_MULT * a / entry
            if short_pnl is None:
                if low[k] <= tp_dn:
                    short_pnl = ATR_TP_MULT * a / entry
                elif high[k] >= sl_up:
                    short_pnl = -ATR_SL_MULT * a / entry
            if long_pnl is not None and short_pnl is not None:
                break
        if long_pnl is None:
            long_pnl = (close[t + TIMEOUT_CANDLES] - entry) / entry
        if short_pnl is None:
            short_pnl = (entry - close[t + TIMEOUT_CANDLES]) / entry
        label[t] = 1.0 if long_pnl > short_pnl else -1.0
    return label


def _load(sym: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    perp = pd.read_csv(f"data/{sym}/8h.csv").sort_values("open_time")
    spot = pd.read_csv(f"data/spot/{sym}/8h.csv").sort_values("open_time")
    return perp.reset_index(drop=True), spot.reset_index(drop=True)


# Groups (from features_v3.GROUP_REGISTRY) that the 14 anchors come from.
_ANCHOR_GROUPS = ("regime", "tail_risk", "momentum_accel", "cross_btc",
                  "volume_micro", "engineered_v3")


def _anchor_features(sym: str) -> pd.DataFrame:
    """Compute the 14 /059-anchor features in-script via features_v3.GROUP_REGISTRY.

    The v3 feature parquets are not pre-generated in this worktree (per
    feedback_data_staleness_per_worktree.md each worktree generates its own; the
    runner does this internally in Phase 6).  For the EDA we compute the anchor
    features with the EXACT registry the runner uses — track-isolated, no v1/v2
    imports — so the orthogonality / incremental tests are on the production
    feature definitions, not a re-implementation.
    """
    from crypto_trade.features_v3 import GROUP_REGISTRY

    df = pd.read_csv(f"data/{sym}/8h.csv").sort_values("open_time").reset_index(drop=True)
    df["symbol"] = sym
    for g in _ANCHOR_GROUPS:
        df = GROUP_REGISTRY[g](df)
    keep = ["open_time", *[c for c in ANCHOR_14 if c in df.columns]]
    return df[keep].copy()


# ---------------------------------------------------------------------------
# T0 — coverage / non-degeneracy
# ---------------------------------------------------------------------------
def t0_coverage() -> pd.DataFrame:
    rows = []
    for sym in SYMBOLS:
        perp, spot = _load(sym)
        bf = compute_basis_features(perp, spot)
        is_mask = bf["open_time"] < OOS_CUTOFF_MS
        bis = bf[is_mask]
        perp_is = (perp["open_time"] < OOS_CUTOFF_MS).sum()
        # spot-merge coverage on the IS perp rows
        spot_matched = bis["spot_close"].notna().mean()
        rows.append({
            "symbol": sym,
            "perp_IS_rows": int(perp_is),
            "spot_merge_coverage": round(float(spot_matched), 4),
            "basis_raw_mean_bps": round(float(bis["basis_raw"].mean() * 1e4), 2),
            "basis_raw_std_bps": round(float(bis["basis_raw"].std() * 1e4), 2),
            "basis_z30_coverage": round(float(bis["basis_zscore_30"].notna().mean()), 4),
            "basis_mom3_coverage": round(float(bis["basis_momentum_3"].notna().mean()), 4),
            "basis_flag_coverage": round(float(bis["basis_extreme_flag"].notna().mean()), 4),
            "basis_z30_unique": int(bis["basis_zscore_30"].round(4).nunique()),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# T1 — feature -> label IC (Spearman), per symbol
# ---------------------------------------------------------------------------
def t1_ic() -> pd.DataFrame:
    rows = []
    for sym in SYMBOLS:
        perp, spot = _load(sym)
        bf = compute_basis_features(perp, spot)
        label = triple_barrier_label(perp)
        is_mask = (bf["open_time"] < OOS_CUTOFF_MS).to_numpy()
        for feat in ("basis_zscore_30", "basis_momentum_3", "basis_extreme_flag"):
            x = bf[feat].to_numpy(float)
            m = is_mask & np.isfinite(x) & np.isfinite(label)
            if m.sum() < 50:
                rows.append({"symbol": sym, "feature": feat, "n": int(m.sum()),
                             "spearman_ic": np.nan, "abs_ic": np.nan})
                continue
            ic, _ = spearmanr(x[m], label[m])
            rows.append({"symbol": sym, "feature": feat, "n": int(m.sum()),
                         "spearman_ic": round(float(ic), 4),
                         "abs_ic": round(abs(float(ic)), 4)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# T2 — orthogonality vs the 14 anchors (max |Pearson IC|)
# ---------------------------------------------------------------------------
def t2_orthogonality() -> pd.DataFrame:
    rows = []
    for sym in SYMBOLS:
        perp, spot = _load(sym)
        bf = compute_basis_features(perp, spot)
        adf = _anchor_features(sym)
        merged = bf.merge(adf, on="open_time", how="inner")
        is_mask = merged["open_time"] < OOS_CUTOFF_MS
        mis = merged[is_mask]
        for feat in ("basis_zscore_30", "basis_momentum_3", "basis_extreme_flag"):
            best_ic, best_anchor = 0.0, ""
            x = mis[feat]
            for anc in ANCHOR_14:
                pair = pd.concat([x, mis[anc]], axis=1).dropna()
                if len(pair) < 50:
                    continue
                ic = pair.iloc[:, 0].corr(pair.iloc[:, 1])
                if np.isfinite(ic) and abs(ic) > abs(best_ic):
                    best_ic, best_anchor = ic, anc
            rows.append({"symbol": sym, "feature": feat,
                         "max_abs_ic_vs_anchors": round(abs(best_ic), 4),
                         "argmax_anchor": best_anchor})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# T3 — incremental information: 14 vs 14+basis, chronological IS 70/30
# ---------------------------------------------------------------------------
def t3_incremental() -> pd.DataFrame:
    try:
        import lightgbm as lgb
    except ImportError:
        return pd.DataFrame([{"note": "lightgbm unavailable"}])

    rows = []
    for sym in SYMBOLS:
        perp, spot = _load(sym)
        bf = compute_basis_features(perp, spot)
        label = triple_barrier_label(perp)
        adf = _anchor_features(sym)
        bf = bf.assign(_label=label)
        merged = bf.merge(adf, on="open_time", how="inner")
        merged = merged[merged["open_time"] < OOS_CUTOFF_MS].copy()
        basis_cols = ["basis_zscore_30", "basis_momentum_3", "basis_extreme_flag"]
        merged = merged.dropna(subset=[*ANCHOR_14, *basis_cols, "_label"])
        if len(merged) < 200:
            rows.append({"symbol": sym, "note": f"too few IS rows ({len(merged)})"})
            continue
        merged = merged.sort_values("open_time").reset_index(drop=True)
        split = int(len(merged) * 0.70)
        y = ((merged["_label"] + 1) / 2).astype(int)  # {-1,1} -> {0,1}
        y_tr, y_te = y.iloc[:split], y.iloc[split:]

        params = dict(objective="binary", num_leaves=15, max_depth=4,
                      learning_rate=0.05, n_estimators=120, min_child_samples=20,
                      subsample=0.8, colsample_bytree=0.8, random_state=42,
                      verbosity=-1)

        def _acc(cols: list[str]) -> float:
            xt = merged[cols].iloc[:split]
            xv = merged[cols].iloc[split:]
            mdl = lgb.LGBMClassifier(**params).fit(xt, y_tr)
            return float((mdl.predict(xv) == y_te.to_numpy()).mean())

        acc_base = _acc(list(ANCHOR_14))
        acc_full = _acc([*ANCHOR_14, *basis_cols])
        rows.append({
            "symbol": sym, "n_IS": len(merged), "test_n": len(y_te),
            "base_rate": round(float(max(y_te.mean(), 1 - y_te.mean())), 4),
            "acc_14": round(acc_base, 4),
            "acc_14_plus_basis": round(acc_full, 4),
            "delta": round(acc_full - acc_base, 4),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# T4 — past-only audit (spike-perturbation, in-script)
# ---------------------------------------------------------------------------
def t4_past_only_audit() -> pd.DataFrame:
    """Perturb perp_close at bar K; assert basis features at bars < K unchanged.

    basis(t) uses perp_close[t] + spot_close[t]; features use basis.shift(1).
    A spike at bar K can affect bar K (K in its own basis) and bars > K (the
    shifted window sees K from K+1), NEVER bars < K.
    """
    rows = []
    for sym in SYMBOLS:
        perp, spot = _load(sym)
        base = compute_basis_features(perp, spot)
        k = min(400, len(perp) - 1)
        pert = perp.copy()
        pert.loc[k, "close"] = float(pert.loc[k, "close"]) * 1.5  # +50% spike
        pf = compute_basis_features(pert, spot)
        for feat in ("basis_zscore_30", "basis_momentum_3", "basis_extreme_flag"):
            b0 = base[feat].to_numpy()[:k]
            b1 = pf[feat].to_numpy()[:k]
            both_nan = np.isnan(b0) & np.isnan(b1)
            identical = bool(np.all(both_nan | (b0 == b1)))
            rows.append({"symbol": sym, "feature": feat, "perturb_bar": k,
                         "bars_before_K_identical": identical})
    return pd.DataFrame(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 72)
    print("iter-v3/086 EDA — perp-spot BASIS feed (IS-only)")
    print("=" * 72)

    t0 = t0_coverage()
    print("\n--- T0 coverage / non-degeneracy ---")
    print(t0.to_string(index=False))
    t0.to_csv(OUT_DIR / "t0_coverage.csv", index=False)

    t1 = t1_ic()
    print("\n--- T1 feature -> triple-barrier-label Spearman IC (IS) ---")
    print(t1.to_string(index=False))
    t1.to_csv(OUT_DIR / "t1_feature_label_ic.csv", index=False)

    t2 = t2_orthogonality()
    print("\n--- T2 orthogonality vs the 14 anchors (max |Pearson IC|) ---")
    print(t2.to_string(index=False))
    t2.to_csv(OUT_DIR / "t2_orthogonality.csv", index=False)

    t3 = t3_incremental()
    print("\n--- T3 incremental info: 14 vs 14+basis (chronological IS 70/30) ---")
    print(t3.to_string(index=False))
    t3.to_csv(OUT_DIR / "t3_incremental.csv", index=False)

    t4 = t4_past_only_audit()
    print("\n--- T4 past-only audit (spike-perturbation) ---")
    print(t4.to_string(index=False))
    t4.to_csv(OUT_DIR / "t4_past_only_audit.csv", index=False)

    print("\n" + "=" * 72)
    print("CSVs written to analysis/iteration_v3-086/")
    print("=" * 72)


if __name__ == "__main__":
    main()
