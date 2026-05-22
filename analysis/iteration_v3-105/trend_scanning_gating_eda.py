"""iter-v3/105 gating EDA — the trend-scanning label (Lopez de Prado, MLAM section 5.4).

Fail-fast GO/NO-GO EDA. Strictly IS-only (open_time < OOS_CUTOFF_MS). The QR does
NOT inspect post-cutoff OOS in Phases 1-5.

Three deliverables (the /104-diary pre-registered F-HORIZON / F-IC / F-RATE gates):

  T1 - the per-bar SELECTED-HORIZON distribution of the trend-scanning label.
       If it collapses to the longest grid horizon (or ~21, the incumbent timeout),
       the re-framing is a relabel of the incumbent -> F-HORIZON kill -> NO-GO.

  T2 - the 14-feature V3_FEATURE_COLUMNS feature->label Spearman IC, computed against
       (a) the NEW trend-scanning label and (b) the INCUMBENT /059 triple-barrier label.
       The genuine GO signal is a MATERIALLY HIGHER aggregate |IC| against the new label
       -- direct IS-only evidence the binding constraint is the label geometry, not the
       features. If the new-label IC is not materially higher -> F-IC kill -> NO-GO.

  T3 - IS sub-period (half + quartile) sign-stability of the per-symbol feature->label
       IC, the /103 tsrank_dispersion_ratio lesson (a half-split masks within-half flips).

  T4 - label balance + IS trade-count proxy. Trend-scanning must not collapse the
       trade rate below the bundle-level floor -> F-RATE.

The incumbent /059 triple-barrier label is reconstructed here with the EXACT production
rule -- label_trades(label_mode="triple_barrier", use_atr, atr_tp=2.0, atr_sl=1.0,
timeout=21 candles, fee_pct from the runner) -- so the IC comparison is apples-to-apples.

Run:  uv run python analysis/iteration_v3-105/trend_scanning_gating_eda.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.stats import spearmanr

from crypto_trade.config import OOS_CUTOFF_MS
from crypto_trade.features_v3 import V3_FEATURE_COLUMNS
from crypto_trade.strategies.ml.labeling import label_trades

# --- fixed v3 / iter-v3/059 production constants (NOT tuned here) ---------------
SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]
FEATURES_DIR = Path("data/features_v3")
OUT_DIR = Path("analysis/iteration_v3-105")
ATR_COLUMN = "natr_21_raw"  # run_baseline_v3.py:1871
ATR_TP, ATR_SL = 2.0, 1.0  # V3 default multipliers (BASELINE_V3.md)
INCUMBENT_TIMEOUT_CANDLES = 21  # the /059 fixed triple-barrier timeout
INTERVAL_MINUTES = 8 * 60  # 8h candle
FEE_PCT = 0.1  # label_trades default; the runner does not override it
INCUMBENT_TIMEOUT_MINUTES = INCUMBENT_TIMEOUT_CANDLES * INTERVAL_MINUTES

# --- trend-scanning grid ---------------------------------------------------------
# Fibonacci-spaced horizons spanning the incumbent: the incumbent 21-candle horizon
# is INSIDE the grid by construction, so trend-scanning collapsing to 21 is a real,
# detectable F-HORIZON outcome (it cannot be excluded a priori).
TS_HORIZON_GRID = [5, 8, 13, 21, 34]
RANDOM_SEED = 42


# =================================================================================
# Trend-scanning label (Lopez de Prado, Machine Learning for Asset Managers, sec 5.4)
# =================================================================================
def _ols_slope_tstat(y: np.ndarray) -> tuple[float, float]:
    """OLS of y on a 0..L-1 time index. Returns (slope, t-stat of slope).

    L = len(y). Strictly past-and-present only by construction at the call site:
    the caller passes y = close[t : t+h+1], i.e. the bar itself plus h forward bars.
    The t-stat is slope / SE(slope) with SE from the OLS residual variance.
    """
    n = len(y)
    if n < 3:
        return 0.0, 0.0
    x = np.arange(n, dtype=np.float64)
    x_mean = x.mean()
    y_mean = y.mean()
    sxx = np.sum((x - x_mean) ** 2)
    if sxx <= 0:
        return 0.0, 0.0
    sxy = np.sum((x - x_mean) * (y - y_mean))
    slope = sxy / sxx
    intercept = y_mean - slope * x_mean
    resid = y - (intercept + slope * x)
    dof = n - 2
    if dof <= 0:
        return 0.0, 0.0
    sigma2 = np.sum(resid ** 2) / dof
    if sigma2 <= 0:
        # perfectly linear -> infinite t; clamp to a large finite value
        return slope, np.sign(slope) * 1e6
    se_slope = np.sqrt(sigma2 / sxx)
    if se_slope <= 0:
        return slope, np.sign(slope) * 1e6
    return slope, slope / se_slope


def trend_scanning_label(
    close: np.ndarray, horizon_grid: list[int]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per-bar trend-scanning label over a horizon grid.

    For each bar t, fit an OLS linear trend over close[t : t+h] for every h in the
    grid, pick the h with the LARGEST |t-stat| of the slope, and label the bar by
    the SIGN of that slope. Returns (label, selected_horizon, selected_abs_tstat).

    label in {+1, -1, 0}: 0 only where the bar has too few forward bars for the
    smallest grid horizon (the tail warm-down) -> dropped downstream.

    Look-ahead audit: bar t's label uses close[t .. t+h_max]; this is a FORWARD
    label (it is the prediction TARGET, this is correct and required) and never
    reaches into training-feature space. The downstream IS mask uses open_time of
    the bar t itself. There is NO leakage into the feature side.
    """
    n = len(close)
    label = np.zeros(n, dtype=np.intp)
    sel_h = np.zeros(n, dtype=np.intp)
    sel_t = np.zeros(n, dtype=np.float64)
    h_max = max(horizon_grid)
    for t in range(n):
        best_abs_t = -1.0
        best_slope = 0.0
        best_h = 0
        for h in horizon_grid:
            end = t + h + 1  # bar t plus h forward bars (inclusive window)
            if end > n:
                continue
            seg = close[t:end]
            slope, tstat = _ols_slope_tstat(seg)
            abs_t = abs(tstat)
            if abs_t > best_abs_t:
                best_abs_t = abs_t
                best_slope = slope
                best_h = h
        if best_h == 0:
            continue  # no horizon fits (tail warm-down)
        sel_h[t] = best_h
        sel_t[t] = best_abs_t
        label[t] = 1 if best_slope >= 0 else -1
    _ = h_max  # documented; not otherwise needed
    return label, sel_h, sel_t


# =================================================================================
# Data loading
# =================================================================================
def load_symbol(sym: str) -> pd.DataFrame:
    """Load the v3 feature parquet for one symbol, sorted by open_time."""
    path = FEATURES_DIR / f"{sym}_8h_features.parquet"
    cols = (
        ["symbol", "open_time", "close_time", "open", "high", "low", "close", ATR_COLUMN]
        + list(V3_FEATURE_COLUMNS)
    )
    table = pq.read_table(path, columns=[c for c in cols if c is not None])
    df = table.to_pandas()
    if "symbol" not in df.columns:
        df["symbol"] = sym
    df = df.sort_values("open_time").reset_index(drop=True)
    return df


def incumbent_triple_barrier_labels(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Reconstruct the /059 production triple-barrier label for every row of df.

    EXACT production rule: label_trades(label_mode='triple_barrier', use_atr=True,
    atr_tp=2.0, atr_sl=1.0, timeout=21 candles, fee_pct=0.1). atr_values are the
    per-row ATR in PRICE units = close * natr_21_raw / 100 (the lgbm._load_atr
    convention). Returns (labels, valid_mask) where valid_mask drops the forward
    warm-down tail (rows with no full 21-candle window) by checking the realized
    label is non-pending.
    """
    close = df["close"].to_numpy(dtype=np.float64)
    natr = df[ATR_COLUMN].to_numpy(dtype=np.float64)
    atr_price = close * natr / 100.0
    n = len(df)
    cand = np.arange(n, dtype=np.intp)
    labels, _w, long_pnl, short_pnl = label_trades(
        df,
        cand,
        ATR_TP,
        ATR_SL,
        INCUMBENT_TIMEOUT_MINUTES,
        fee_pct=FEE_PCT,
        atr_values=atr_price,
        verbose=0,
    )
    # A row whose forward window runs off the end of the series is a pending/tail
    # row: label_trades still assigns it via the forward-return sign, but it does
    # not have a full 21-candle scan. Drop the last 21 rows of the symbol panel as
    # the warm-down tail so the incumbent and the trend-scanning label are compared
    # over the same effective support.
    valid = np.ones(n, dtype=bool)
    if n > INCUMBENT_TIMEOUT_CANDLES:
        valid[-INCUMBENT_TIMEOUT_CANDLES:] = False
    _ = (long_pnl, short_pnl)
    return labels, valid


# =================================================================================
# IC machinery
# =================================================================================
def feature_label_ic(
    feats: pd.DataFrame, label: np.ndarray, mask: np.ndarray
) -> dict[str, tuple[float, float]]:
    """Spearman IC of every V3 feature vs a label, over the masked rows.

    Returns {feature: (ic, p_value)}. NaN feature rows are dropped pairwise.
    """
    out: dict[str, tuple[float, float]] = {}
    lab = label[mask].astype(np.float64)
    for col in V3_FEATURE_COLUMNS:
        x = feats[col].to_numpy(dtype=np.float64)[mask]
        ok = np.isfinite(x) & np.isfinite(lab)
        if ok.sum() < 100:
            out[col] = (np.nan, np.nan)
            continue
        ic, p = spearmanr(x[ok], lab[ok])
        out[col] = (float(ic), float(p))
    return out


def quartile_sign_string(
    feats: pd.DataFrame, label: np.ndarray, mask: np.ndarray, col: str, n_bins: int
) -> str:
    """Sign string of the per-bin Spearman IC of one feature vs a label.

    Bins are chronological (the rows are already open_time-sorted). A '+'/'-'/'0'
    per bin. The /103 lesson: a half-split (n_bins=2) can mask a within-half flip;
    n_bins=4 (quartile) is the binding resolution.
    """
    idx = np.where(mask)[0]
    if len(idx) < n_bins * 50:
        return "n/a"
    chunks = np.array_split(idx, n_bins)
    signs = []
    x_all = feats[col].to_numpy(dtype=np.float64)
    lab_all = label.astype(np.float64)
    for ch in chunks:
        x = x_all[ch]
        lab = lab_all[ch]
        ok = np.isfinite(x) & np.isfinite(lab)
        if ok.sum() < 30:
            signs.append("0")
            continue
        ic, _ = spearmanr(x[ok], lab[ok])
        if not np.isfinite(ic) or abs(ic) < 1e-6:
            signs.append("0")
        else:
            signs.append("+" if ic > 0 else "-")
    return "".join(signs)


# =================================================================================
# Main
# =================================================================================
def main() -> None:
    np.random.seed(RANDOM_SEED)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print("iter-v3/105 GATING EDA — the trend-scanning label")
    print(f"OOS_CUTOFF_MS = {OOS_CUTOFF_MS}  (all measurements strictly IS-only)")
    print(f"trend-scanning horizon grid = {TS_HORIZON_GRID} candles")
    print(f"incumbent triple-barrier timeout = {INCUMBENT_TIMEOUT_CANDLES} candles")
    print("=" * 78)

    t1_rows: list[dict] = []
    t2_rows: list[dict] = []
    t3_rows: list[dict] = []
    t4_rows: list[dict] = []

    # accumulators for the cross-symbol aggregate IC
    agg_abs_ic_ts: list[float] = []
    agg_abs_ic_tb: list[float] = []

    for sym in SYMBOLS:
        df = load_symbol(sym)

        # --- trend-scanning label over the FULL series, then IS-mask --------------
        close = df["close"].to_numpy(dtype=np.float64)
        ts_label, ts_h, ts_tstat = trend_scanning_label(close, TS_HORIZON_GRID)

        # --- incumbent triple-barrier label --------------------------------------
        tb_label, tb_valid = incumbent_triple_barrier_labels(df)

        open_time = df["open_time"].to_numpy(dtype=np.int64)
        is_window = open_time < OOS_CUTOFF_MS

        # trend-scanning warm-down tail: a 0 means no horizon fit -> not a real label
        ts_has_label = ts_label != 0
        # incumbent: tb_valid drops the 21-candle warm-down tail
        # the SHARED effective IS support for the IC comparison: a row must be
        # IS-window, have a real trend-scanning label, AND be a valid (non-tail)
        # incumbent row. Comparing the two ICs on the SAME rows is the apples-to-
        # apples requirement.
        shared_is = is_window & ts_has_label & tb_valid

        n_is_total = int(is_window.sum())
        n_shared = int(shared_is.sum())

        # ---- T1: selected-horizon distribution (IS rows with a real TS label) ----
        ts_is_mask = is_window & ts_has_label
        sel_h_is = ts_h[ts_is_mask]
        h_counts = {h: int((sel_h_is == h).sum()) for h in TS_HORIZON_GRID}
        h_total = max(1, len(sel_h_is))
        h_share = {h: h_counts[h] / h_total for h in TS_HORIZON_GRID}
        # the F-HORIZON metrics: the longest-horizon share, and the incumbent-21 share
        longest_h = max(TS_HORIZON_GRID)
        for h in TS_HORIZON_GRID:
            t1_rows.append(
                {
                    "symbol": sym,
                    "horizon": h,
                    "n_bars": h_counts[h],
                    "share": round(h_share[h], 4),
                }
            )
        # entropy of the horizon distribution, normalized to [0,1]; 1.0 = uniform
        shares = np.array([h_share[h] for h in TS_HORIZON_GRID], dtype=np.float64)
        nz = shares[shares > 0]
        ent = -np.sum(nz * np.log(nz)) / np.log(len(TS_HORIZON_GRID))
        median_h = float(np.median(sel_h_is)) if len(sel_h_is) else 0.0
        mean_h = float(np.mean(sel_h_is)) if len(sel_h_is) else 0.0

        print(f"\n[{sym}] IS rows={n_is_total}  shared-support rows={n_shared}")
        print(f"  T1 selected-horizon distribution (IS):")
        for h in TS_HORIZON_GRID:
            bar = "#" * int(round(h_share[h] * 50))
            print(f"    h={h:>3}: {h_share[h]*100:6.2f}%  {bar}")
        print(
            f"    median_h={median_h:.1f}  mean_h={mean_h:.2f}  "
            f"norm_entropy={ent:.3f}  longest(h={longest_h})_share={h_share[longest_h]:.3f}"
        )

        # ---- T2: 14-feature feature->label IC: trend-scanning vs incumbent -------
        ts_ic = feature_label_ic(df, ts_label, shared_is)
        tb_ic = feature_label_ic(df, tb_label, shared_is)
        sym_abs_ts = []
        sym_abs_tb = []
        for col in V3_FEATURE_COLUMNS:
            ic_ts, p_ts = ts_ic[col]
            ic_tb, p_tb = tb_ic[col]
            t2_rows.append(
                {
                    "symbol": sym,
                    "feature": col,
                    "ic_trend_scan": round(ic_ts, 5) if np.isfinite(ic_ts) else np.nan,
                    "p_trend_scan": round(p_ts, 5) if np.isfinite(p_ts) else np.nan,
                    "ic_triple_barrier": round(ic_tb, 5) if np.isfinite(ic_tb) else np.nan,
                    "p_triple_barrier": round(p_tb, 5) if np.isfinite(p_tb) else np.nan,
                    "abs_ic_delta": (
                        round(abs(ic_ts) - abs(ic_tb), 5)
                        if np.isfinite(ic_ts) and np.isfinite(ic_tb)
                        else np.nan
                    ),
                }
            )
            if np.isfinite(ic_ts):
                sym_abs_ts.append(abs(ic_ts))
                agg_abs_ic_ts.append(abs(ic_ts))
            if np.isfinite(ic_tb):
                sym_abs_tb.append(abs(ic_tb))
                agg_abs_ic_tb.append(abs(ic_tb))
        mean_abs_ts = float(np.mean(sym_abs_ts)) if sym_abs_ts else np.nan
        mean_abs_tb = float(np.mean(sym_abs_tb)) if sym_abs_tb else np.nan
        print(
            f"  T2 mean |IC| over 14 features: trend-scan={mean_abs_ts:.5f}  "
            f"triple-barrier={mean_abs_tb:.5f}  "
            f"delta={mean_abs_ts - mean_abs_tb:+.5f}"
        )

        # ---- T3: IS sub-period sign-stability (half + quartile) -----------------
        # run on the strongest 5 trend-scanning features for this symbol
        ranked = sorted(
            [
                (col, abs(ts_ic[col][0]))
                for col in V3_FEATURE_COLUMNS
                if np.isfinite(ts_ic[col][0])
            ],
            key=lambda kv: kv[1],
            reverse=True,
        )
        for col, _absic in ranked[:5]:
            half = quartile_sign_string(df, ts_label, shared_is, col, 2)
            quart = quartile_sign_string(df, ts_label, shared_is, col, 4)
            half_tb = quartile_sign_string(df, tb_label, shared_is, col, 2)
            quart_tb = quartile_sign_string(df, tb_label, shared_is, col, 4)
            quartile_stable = len(set(quart)) == 1 and "n/a" not in quart and "0" not in quart
            t3_rows.append(
                {
                    "symbol": sym,
                    "feature": col,
                    "ts_ic_full": round(ts_ic[col][0], 5),
                    "ts_half_signs": half,
                    "ts_quartile_signs": quart,
                    "ts_quartile_stable": quartile_stable,
                    "tb_half_signs": half_tb,
                    "tb_quartile_signs": quart_tb,
                }
            )

        # ---- T4: label balance + trade-count proxy ------------------------------
        ts_lab_is = ts_label[ts_is_mask]
        tb_lab_is = tb_label[is_window & tb_valid]
        ts_long = int((ts_lab_is == 1).sum())
        ts_short = int((ts_lab_is == -1).sum())
        tb_long = int((tb_lab_is == 1).sum())
        tb_short = int((tb_lab_is == -1).sum())
        ts_n = max(1, ts_long + ts_short)
        tb_n = max(1, tb_long + tb_short)
        t4_rows.append(
            {
                "symbol": sym,
                "ts_n_labeled": ts_long + ts_short,
                "ts_long_share": round(ts_long / ts_n, 4),
                "ts_short_share": round(ts_short / ts_n, 4),
                "tb_n_labeled": tb_long + tb_short,
                "tb_long_share": round(tb_long / tb_n, 4),
                "tb_short_share": round(tb_short / tb_n, 4),
            }
        )
        print(
            f"  T4 label balance IS — trend-scan: long {ts_long/ts_n*100:.1f}% / "
            f"short {ts_short/ts_n*100:.1f}%  (n={ts_long+ts_short})  |  "
            f"triple-barrier: long {tb_long/tb_n*100:.1f}% / "
            f"short {tb_short/tb_n*100:.1f}%  (n={tb_long+tb_short})"
        )

    # --- write CSVs ---------------------------------------------------------------
    pd.DataFrame(t1_rows).to_csv(OUT_DIR / "T1_selected_horizon_distribution.csv", index=False)
    pd.DataFrame(t2_rows).to_csv(OUT_DIR / "T2_feature_label_ic_comparison.csv", index=False)
    pd.DataFrame(t3_rows).to_csv(OUT_DIR / "T3_subperiod_sign_stability.csv", index=False)
    pd.DataFrame(t4_rows).to_csv(OUT_DIR / "T4_label_balance.csv", index=False)

    # --- cross-symbol aggregate verdict ------------------------------------------
    agg_ts = float(np.mean(agg_abs_ic_ts)) if agg_abs_ic_ts else np.nan
    agg_tb = float(np.mean(agg_abs_ic_tb)) if agg_abs_ic_tb else np.nan
    agg_delta = agg_ts - agg_tb
    agg_ratio = agg_ts / agg_tb if agg_tb and np.isfinite(agg_tb) and agg_tb > 0 else np.nan

    # the F-IC GO bar: a MATERIALLY higher aggregate |IC| against the new label.
    # "Materially" pre-set here at >= +20% relative lift (ratio >= 1.20). A lift
    # below +20% but positive is the inconclusive-but-promising band.
    F_IC_GO_RATIO = 1.20

    print("\n" + "=" * 78)
    print("CROSS-SYMBOL AGGREGATE — T2 feature->label IC (the F-IC gate)")
    print(f"  mean |IC| (14 features x 3 symbols) vs trend-scanning   = {agg_ts:.5f}")
    print(f"  mean |IC| (14 features x 3 symbols) vs triple-barrier   = {agg_tb:.5f}")
    print(f"  absolute delta                                          = {agg_delta:+.5f}")
    print(f"  relative ratio (trend-scan / triple-barrier)            = {agg_ratio:.4f}")
    print(f"  F-IC GO threshold: ratio >= {F_IC_GO_RATIO:.2f}")
    print("=" * 78)

    verdict = {
        "agg_abs_ic_trend_scan": round(agg_ts, 5),
        "agg_abs_ic_triple_barrier": round(agg_tb, 5),
        "agg_abs_ic_delta": round(agg_delta, 5),
        "agg_abs_ic_ratio": round(agg_ratio, 4) if np.isfinite(agg_ratio) else np.nan,
        "f_ic_go_ratio_threshold": F_IC_GO_RATIO,
        "f_ic_gate": "GO" if (np.isfinite(agg_ratio) and agg_ratio >= F_IC_GO_RATIO)
        else ("INCONCLUSIVE" if (np.isfinite(agg_delta) and agg_delta > 0) else "NO-GO"),
    }
    pd.DataFrame([verdict]).to_csv(OUT_DIR / "T5_screen_verdict.csv", index=False)
    print(f"\nF-IC gate: {verdict['f_ic_gate']}")
    print(f"\nWrote 5 CSVs to {OUT_DIR}/")


if __name__ == "__main__":
    main()
