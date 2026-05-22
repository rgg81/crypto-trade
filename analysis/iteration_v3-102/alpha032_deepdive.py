"""iter-v3/102 — EDA Script 4: alpha032 deep-dive (per-symbol + ADF + warm-up).

The /102 axis is alpha032 (selected by Script 3's horse race).  This script
characterizes alpha032 specifically, IS-ONLY, for the brief's Section 2/4/7:
  T8  Per-symbol held-out-tail decomposition: does the +0.01373 pooled dShACC
      lift come from all three symbols, or is it a one-symbol artifact (the
      /101 fragility lesson — BCH carries 95.76% of IS PnL)?
  T9  ADF stationarity of alpha032 per symbol (v3 hard gate: ADF p < 0.05 or an
      explicit regime-indicator justification — ITERATION_PLAN_8H_V3.md).
  T10 Warm-up / coverage: first valid bar, NaN count — confirms the warm-up is
      absorbed by the 24-month IS window.

alpha032 (Kakushadze Alpha#32, per-symbol port):
  scale((sum(close,7)/7 - close)) + 20*scale(correlation(vwap, delay(close,5), 230))
  Per-symbol port: scale() -> causal scale_ts (trailing-100-bar mean-abs
  normalization).  Term 1 = a fast 7-bar mean-reversion gap.  Term 2 = a slow
  230-bar correlation of vwap with the 5-bar-lagged close (a vwap/price
  lead-lag).  Both terms time-series on the asset's own series.

NO-CHEATING: OOS_CUTOFF_MS = 1742774400000; every row IS-only.

RUN:  uv run python analysis/iteration_v3-102/alpha032_deepdive.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller

try:
    import lightgbm as lgb
except ImportError:  # pragma: no cover
    raise

sys.path.insert(0, str(Path(__file__).resolve().parent))
from alpha_horserace_eda import (  # noqa: E402
    EMBARGO_CANDLES,
    LGB_PARAMS,
    N_WF_FOLDS,
    TAIL_MONTHS,
    build_is_panel,
)
from alpha_ic_eda import SYMBOLS  # noqa: E402
from alpha_lib import alpha032  # noqa: E402
from alpha_redundancy_eda import V3_FEATURE_COLUMNS  # noqa: E402

OUT = Path("analysis/iteration_v3-102")
MS_PER_DAY = 24 * 60 * 60 * 1000


def per_symbol_tail_eval(panel: pd.DataFrame, feat_cols: list[str]) -> dict:
    """Held-out-tail nested-walk-forward eval — return per-symbol accuracy and
    pred-side PnL sum for one symbol's panel."""
    panel = panel.sort_values("open_time").reset_index(drop=True)
    last_t = int(panel["open_time"].max())
    tail_start = last_t - TAIL_MONTHS * 30 * MS_PER_DAY
    tail_idx = np.where((panel["open_time"] >= tail_start).to_numpy())[0]
    if len(tail_idx) < N_WF_FOLDS * 8:
        return {"acc": np.nan, "pnl": np.nan, "n": 0}
    X = panel[feat_cols].to_numpy(dtype=np.float64)
    y = panel["y"].to_numpy(dtype=int)
    tgt = panel["tb_label"].to_numpy(dtype=np.float64)
    pnl = panel["tb_pnl"].to_numpy(dtype=np.float64)
    corr, sp = [], []
    for fold in np.array_split(tail_idx, N_WF_FOLDS):
        if len(fold) == 0:
            continue
        train_hi = max(0, int(fold[0]) - EMBARGO_CANDLES)
        tr = np.arange(0, train_hi)
        if len(tr) < 100 or len(np.unique(y[tr])) < 2:
            continue
        m = lgb.LGBMClassifier(**LGB_PARAMS)
        m.fit(X[tr], y[tr])
        p = m.predict_proba(X[fold])[:, 1]
        side = np.where(p >= 0.5, 1.0, -1.0)
        corr.append((side == tgt[fold]).astype(np.float64))
        sp.append(np.where(side == tgt[fold], pnl[fold], -pnl[fold]))
    if not corr:
        return {"acc": np.nan, "pnl": np.nan, "n": 0}
    c = np.concatenate(corr)
    s = np.concatenate(sp)
    return {"acc": float(c.mean()), "pnl": float(np.nansum(s)), "n": len(c)}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/102 EDA Script 4 — alpha032 deep-dive (IS-only)")
    print("=" * 78)

    base = list(V3_FEATURE_COLUMNS)
    cand = base + ["alpha032"]
    need = base + ["alpha032", "tb_pnl"]
    panels = {}
    for sym in SYMBOLS:
        d = build_is_panel(sym)
        d = d.dropna(subset=need).reset_index(drop=True)
        panels[sym] = d

    # ---- T8: per-symbol held-out-tail decomposition ----
    print("\nT8 — alpha032 per-symbol held-out-tail lift (BASE vs BASE+alpha032):")
    t8_rows = []
    for sym in SYMBOLS:
        b = per_symbol_tail_eval(panels[sym], base)
        c = per_symbol_tail_eval(panels[sym], cand)
        t8_rows.append(
            {
                "symbol": sym,
                "tail_n": c["n"],
                "BASE_acc": round(b["acc"], 4) if pd.notna(b["acc"]) else np.nan,
                "alpha032_acc": round(c["acc"], 4)
                if pd.notna(c["acc"])
                else np.nan,
                "d_acc": round(c["acc"] - b["acc"], 4)
                if pd.notna(c["acc"]) and pd.notna(b["acc"])
                else np.nan,
                "BASE_pnl": round(b["pnl"], 3) if pd.notna(b["pnl"]) else np.nan,
                "alpha032_pnl": round(c["pnl"], 3)
                if pd.notna(c["pnl"])
                else np.nan,
                "d_pnl": round(c["pnl"] - b["pnl"], 3)
                if pd.notna(c["pnl"]) and pd.notna(b["pnl"])
                else np.nan,
            }
        )
    t8 = pd.DataFrame(t8_rows)
    t8.to_csv(OUT / "T8_alpha032_per_symbol.csv", index=False)
    print(t8.to_string(index=False))
    n_pos = int((t8["d_acc"] > 0).sum())
    print(f"\n  -> {n_pos}/3 symbols show a positive held-out-tail accuracy "
          f"lift.  3/3 = robust; 1/3 = a one-symbol artifact (fragility flag).")

    # ---- T9: ADF stationarity per symbol ----
    print("\nT9 — alpha032 ADF stationarity per symbol (v3 gate: p < 0.05):")
    t9_rows = []
    for sym in SYMBOLS:
        d = panels[sym]
        series = d["alpha032"].replace([np.inf, -np.inf], np.nan).dropna()
        if len(series) < 50:
            t9_rows.append({"symbol": sym, "adf_stat": np.nan, "adf_p": np.nan,
                            "stationary": False, "n_obs": len(series)})
            continue
        stat, pval = adfuller(series.to_numpy(), autolag="AIC")[:2]
        t9_rows.append(
            {
                "symbol": sym,
                "adf_stat": round(float(stat), 4),
                "adf_p": round(float(pval), 6),
                "stationary": bool(pval < 0.05),
                "n_obs": len(series),
            }
        )
    t9 = pd.DataFrame(t9_rows)
    t9.to_csv(OUT / "T9_alpha032_adf.csv", index=False)
    print(t9.to_string(index=False))
    n_stat = int(t9["stationary"].sum())
    print(f"\n  -> alpha032 is ADF-stationary in {n_stat}/3 symbols.")

    # ---- T10: warm-up / coverage ----
    print("\nT10 — alpha032 warm-up / coverage (full panel, pre-IS-mask):")
    t10_rows = []
    for sym in SYMBOLS:
        full = pd.read_parquet(
            Path("data/features_v3") / f"{sym}_8h_features.parquet"
        ).sort_values("open_time").reset_index(drop=True)
        a = alpha032(full)
        first_valid = int(a.notna().to_numpy().argmax()) if a.notna().any() else -1
        t10_rows.append(
            {
                "symbol": sym,
                "panel_rows": len(full),
                "first_valid_bar": first_valid,
                "first_valid_days": round(first_valid * 8 / 24, 1),
                "nan_count": int(a.isna().sum()),
            }
        )
    t10 = pd.DataFrame(t10_rows)
    t10.to_csv(OUT / "T10_alpha032_warmup.csv", index=False)
    print(t10.to_string(index=False))
    print("\n  alpha032's longest window is the 230-bar correlation; first "
          "valid bar ~= 230 (~77 days) — easily absorbed by the 24-month IS "
          "warm-up.")

    print("\n" + "=" * 78)
    print("Script 4 done.  Outputs: T8_alpha032_per_symbol.csv, "
          "T9_alpha032_adf.csv, T10_alpha032_warmup.csv")
    print("=" * 78)


if __name__ == "__main__":
    main()
