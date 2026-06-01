"""iter-v1/031 EDA-2 — Composite weighting VARIANTS investigation.

CRITICAL FINDING from `sample_weighting_composite_eda.py`:
- v1's dense-label regime gives EVERY bar concurrency ∈ [21, 22] AT entry
  (timeout = 21 candles, label entry is at every bar → near-saturation overlap).
- inverse_concurrency `1 - c_t/max_c` is ≈ 0 for 99.9% of bars and exactly 0
  at the peak, floored to 0.01.
- Composite = uniq × inv_conc has 99.94% of weight at ≈ 1.0 (after renorm)
  and 0.06% extreme spikes (up to 264×).
- PER-SYMBOL Spearman composite vs uniqueness = 1.000 (the rare "low
  concurrency" bars happen to BE the rare "high uniqueness" bars → perfect
  rank tie within symbol).

This means the LITERAL AFML §4.6 formula is empirically DEGENERATE at v1 8h
candles + 21-candle timeout. The portfolio Spearman = 0.30 only because
per-symbol uniqueness magnitudes shift the pooled ranks.

For /031 to ALSO not collapse to the /016 `uniqueness_only` axis (which has
Per-symbol Spearman 1.000 with composite — identical ordering within symbol),
we need a NON-DEGENERATE composite definition.

ALTERNATIVE COMPOSITES TESTED:
1. AFML literal: uniq × (1 - c/max(c))                       [DEGENERATE]
2. AFML smoothed: uniq × (1/c) where c = concurrency at entry  [check]
3. AFML capped: uniq × clip(1 - c/p95(c), 0.05, 1)             [check]
4. Window-mean inverse-concurrency: uniq × mean(1/c_t) over WINDOW (= uniq squared)
5. ABS-PNL × UNIQUENESS hybrid: abs_pnl × uniq (preserves outlier upweight)
6. ABS-PNL × INVERSE-CONCURRENCY hybrid: abs_pnl × (1/c_at_entry)
7. SQRT(uniqueness) × abs_pnl: dampen abs_pnl outliers slightly
8. INVERSE_CONCURRENCY ONLY: 1/c_at_entry alone (no uniqueness mult)

For each variant, compute:
- Per-symbol Spearman vs baseline abs_pnl, vs uniqueness, vs uniform
- Portfolio-pooled Spearman vs baseline abs_pnl, vs uniqueness
- Kish n_eff ratio distribution
- Weight distribution (percentiles)

Goal: identify variants that are GENUINELY ORTHOGONAL (both PER-SYMBOL and
POOLED Spearman < 0.90 vs baseline AND vs uniqueness_only).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from crypto_trade.config import OOS_CUTOFF_MS  # noqa: E402
from crypto_trade.features_v1 import V1_BASELINE_UNIVERSE  # noqa: E402
from crypto_trade.strategies.ml.labeling import (  # noqa: E402
    compute_sample_uniqueness,
    label_trades,
)

OUTPUT_DIR = Path(__file__).parent
OUTPUT_DIR.mkdir(exist_ok=True)

ATR_TP_MULT = 2.9
ATR_SL_MULT = 1.45
LABEL_TIMEOUT_MIN = 10080
INTERVAL_MINUTES = 480
FEE_PCT = 0.1
ATR_PERIOD = 14


def _compute_atr(high, low, close, period=ATR_PERIOD):
    n = len(high)
    tr = np.zeros(n, dtype=np.float64)
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        tr[i] = max(
            high[i] - low[i],
            abs(high[i] - close[i - 1]),
            abs(low[i] - close[i - 1]),
        )
    atr = np.full(n, np.nan, dtype=np.float64)
    atr[period - 1] = tr[:period].mean()
    for i in range(period, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def _load_symbol(symbol):
    path = REPO / "data" / symbol / "8h.csv"
    df = pd.read_csv(path)
    df["symbol"] = symbol
    df["open_time"] = df["open_time"].astype(np.int64)
    df["close_time"] = df["close_time"].astype(np.int64)
    df = df.sort_values("open_time").reset_index(drop=True)
    atr_raw = _compute_atr(
        df["high"].to_numpy(dtype=np.float64),
        df["low"].to_numpy(dtype=np.float64),
        df["close"].to_numpy(dtype=np.float64),
    )
    atr_pastonly = np.full_like(atr_raw, np.nan)
    atr_pastonly[1:] = atr_raw[:-1]
    df["atr"] = atr_pastonly
    return df


def _compute_concurrency_at_entry(
    candidate_indices, timeout_minutes, open_time_arr, sym_arr
):
    n = len(candidate_indices)
    timeout_ms = timeout_minutes * 60 * 1000
    concurrency = np.zeros(n, dtype=np.float64)
    sym_groups: dict[str, list[int]] = {}
    for ci, idx in enumerate(candidate_indices):
        sym = str(sym_arr[idx])
        sym_groups.setdefault(sym, []).append(ci)
    for sym, ci_list in sym_groups.items():
        m = len(ci_list)
        ci_arr = np.array(ci_list)
        starts = open_time_arr[candidate_indices[ci_arr]].astype(np.int64)
        ends = starts + timeout_ms
        events = np.concatenate([starts, ends + 1])
        event_vals = np.concatenate([np.ones(m), -np.ones(m)])
        order = np.argsort(events, kind="mergesort")
        events_s = events[order]
        event_vals_s = event_vals[order]
        cum = np.cumsum(event_vals_s)
        idx_at = np.searchsorted(events_s, starts, side="right") - 1
        c_at = np.zeros(m, dtype=np.float64)
        valid = idx_at >= 0
        c_at[valid] = cum[idx_at[valid]]
        c_at = np.maximum(c_at, 1.0)
        concurrency[ci_arr] = c_at
    return concurrency


def _spearman(a, b):
    if len(a) == 0:
        return float("nan")
    ra = pd.Series(a).rank(method="average").to_numpy().astype(np.float64).copy()
    rb = pd.Series(b).rank(method="average").to_numpy().astype(np.float64).copy()
    ra = ra - ra.mean()
    rb = rb - rb.mean()
    denom = (np.sqrt((ra * ra).sum()) * np.sqrt((rb * rb).sum())) or 1.0
    return float((ra * rb).sum() / denom)


def _renorm(w):
    """Renormalize so mean = 1."""
    m = w.mean()
    if m <= 0:
        return w
    return w * (len(w) / w.sum())


def _kish(w):
    if w.sum() <= 0:
        return 0.0
    return float(w.sum() ** 2 / (w * w).sum())


def main():
    print("=" * 88)
    print("iter-v1/031 EDA-2 — COMPOSITE VARIANTS")
    print("=" * 88)

    frames = [_load_symbol(sym) for sym in V1_BASELINE_UNIVERSE]
    master = pd.concat(frames, ignore_index=True)
    master = master.sort_values(["open_time", "symbol"]).reset_index(drop=True)
    open_time_arr = master["open_time"].to_numpy(dtype=np.int64)
    sym_arr = master["symbol"].to_numpy()
    atr_arr = master["atr"].to_numpy()

    rows: list[dict] = []

    # Pooled per-variant arrays for portfolio Spearman.
    pooled = {"uniform": [], "uniqueness_only": [], "baseline_abs_pnl": []}
    variant_names = [
        "afml_literal",
        "afml_inverse_c",
        "afml_capped_p95",
        "abs_pnl_x_uniq",
        "abs_pnl_x_inv_c",
        "sqrt_uniq_x_abs_pnl",
        "inv_concurrency_only",
        "log_inv_c",
    ]
    for v in variant_names:
        pooled[v] = []

    for sym in V1_BASELINE_UNIVERSE:
        sym_mask = (master["symbol"].to_numpy() == sym) & (
            master["open_time"].to_numpy() < OOS_CUTOFF_MS
        )
        valid_atr = ~np.isnan(atr_arr)
        cand_mask = sym_mask & valid_atr
        cand_idx = np.where(cand_mask)[0]
        if len(cand_idx) == 0:
            continue

        train_labels, train_weights_baseline, _, _ = label_trades(
            master,
            cand_idx,
            ATR_TP_MULT,
            ATR_SL_MULT,
            LABEL_TIMEOUT_MIN,
            fee_pct=FEE_PCT,
            atr_values=atr_arr,
            interval_minutes=INTERVAL_MINUTES,
        )

        uniq = compute_sample_uniqueness(
            cand_idx, LABEL_TIMEOUT_MIN, open_time_arr, sym_arr
        )
        c_at = _compute_concurrency_at_entry(
            cand_idx, LABEL_TIMEOUT_MIN, open_time_arr, sym_arr
        )
        max_c = float(c_at.max())
        p95_c = float(np.percentile(c_at, 95))

        variants = {
            # 1. AFML literal (= what we computed before; degenerate)
            "afml_literal": _renorm(
                uniq * np.maximum(1.0 - c_at / max_c, 0.01)
            ),
            # 2. AFML inverse-c: uniq × (1/c)
            "afml_inverse_c": _renorm(uniq * (1.0 / c_at)),
            # 3. AFML capped at p95: uniq × clip(1 - c/p95, 0.05, 1)
            "afml_capped_p95": _renorm(
                uniq * np.clip(1.0 - c_at / p95_c, 0.05, 1.0)
            ),
            # 4. ABS_PNL × UNIQ
            "abs_pnl_x_uniq": _renorm(train_weights_baseline * uniq),
            # 5. ABS_PNL × INV_C (1/c at entry)
            "abs_pnl_x_inv_c": _renorm(train_weights_baseline * (1.0 / c_at)),
            # 6. sqrt(uniq) × abs_pnl
            "sqrt_uniq_x_abs_pnl": _renorm(
                np.sqrt(uniq) * train_weights_baseline
            ),
            # 7. Inverse concurrency only (no uniqueness mult)
            "inv_concurrency_only": _renorm(1.0 / c_at),
            # 8. log(1+1/c) — smoother gradient
            "log_inv_c": _renorm(np.log1p(1.0 / c_at)),
        }

        baseline_w = train_weights_baseline
        uniform_w = np.ones(len(cand_idx))
        uniqonly_w = uniq

        for vname, w in variants.items():
            row = {
                "symbol": sym,
                "variant": vname,
                "n": len(w),
                "mean": float(w.mean()),
                "std": float(w.std()),
                "min": float(w.min()),
                "p05": float(np.percentile(w, 5)),
                "p50": float(np.percentile(w, 50)),
                "p95": float(np.percentile(w, 95)),
                "max": float(w.max()),
                "kish_n_eff": _kish(w),
                "kish_ratio": _kish(w) / len(w),
                "rho_vs_baseline_abs_pnl": _spearman(w, baseline_w),
                "rho_vs_uniqueness_only": _spearman(w, uniqonly_w),
                "rho_vs_uniform": float("nan"),  # uniform = const → undefined
                "frac_below_0p5_norm": float((w < 0.5).mean()),
                "frac_above_1p5_norm": float((w > 1.5).mean()),
                "frac_above_3x_norm": float((w > 3.0).mean()),
            }
            rows.append(row)

        # Append per-symbol arrays to pooled aggregators.
        pooled["uniform"].append(uniform_w)
        pooled["uniqueness_only"].append(uniqonly_w)
        pooled["baseline_abs_pnl"].append(baseline_w)
        for vname, w in variants.items():
            pooled[vname].append(w)

    # Portfolio-pooled Spearman per variant.
    pooled_arrays = {k: np.concatenate(v) for k, v in pooled.items() if len(v) > 0}
    portfolio_rows = []
    for vname in variant_names:
        if vname not in pooled_arrays:
            continue
        w = pooled_arrays[vname]
        portfolio_rows.append({
            "variant": vname,
            "n_pooled": int(len(w)),
            "rho_pooled_vs_baseline_abs_pnl": _spearman(
                w, pooled_arrays["baseline_abs_pnl"]
            ),
            "rho_pooled_vs_uniqueness_only": _spearman(
                w, pooled_arrays["uniqueness_only"]
            ),
            "mean": float(w.mean()),
            "std": float(w.std()),
            "min": float(w.min()),
            "max": float(w.max()),
            "kish_n_eff_pooled": _kish(w),
            "kish_ratio_pooled": _kish(w) / len(w),
            "frac_below_0p5": float((w < 0.5).mean()),
            "frac_above_1p5": float((w > 1.5).mean()),
        })

    per_symbol_df = pd.DataFrame(rows)
    portfolio_df = pd.DataFrame(portfolio_rows)

    per_symbol_df.to_csv(OUTPUT_DIR / "composite_variants_per_symbol.csv", index=False)
    portfolio_df.to_csv(OUTPUT_DIR / "composite_variants_portfolio.csv", index=False)

    print()
    print("PER-SYMBOL Spearman (composite vs baseline / uniqueness)")
    print("-" * 88)
    # Show condensed table: pivot mean over symbols for each variant.
    agg_per_sym = per_symbol_df.groupby("variant").agg(
        rho_baseline_mean=("rho_vs_baseline_abs_pnl", "mean"),
        rho_baseline_min=("rho_vs_baseline_abs_pnl", "min"),
        rho_baseline_max=("rho_vs_baseline_abs_pnl", "max"),
        rho_uniqonly_mean=("rho_vs_uniqueness_only", "mean"),
        rho_uniqonly_min=("rho_vs_uniqueness_only", "min"),
        rho_uniqonly_max=("rho_vs_uniqueness_only", "max"),
        kish_ratio_mean=("kish_ratio", "mean"),
        kish_ratio_min=("kish_ratio", "min"),
    ).reset_index()
    print(agg_per_sym.to_string(index=False))

    print()
    print("PORTFOLIO-POOLED Spearman")
    print("-" * 88)
    print(portfolio_df.to_string(index=False))

    print()
    print("AXIS-VALIDITY CHECK (variant valid if Spearman < 0.90 vs BOTH "
          "baseline AND uniqueness_only on per-symbol AND pooled):")
    print("-" * 88)
    for _, row in portfolio_df.iterrows():
        v = row["variant"]
        sym_stat = agg_per_sym[agg_per_sym["variant"] == v].iloc[0]
        sym_baseline_max = sym_stat["rho_baseline_max"]
        sym_uniq_max = sym_stat["rho_uniqonly_max"]
        pool_baseline = row["rho_pooled_vs_baseline_abs_pnl"]
        pool_uniq = row["rho_pooled_vs_uniqueness_only"]
        valid = (
            abs(sym_baseline_max) < 0.90
            and abs(sym_uniq_max) < 0.90
            and abs(pool_baseline) < 0.90
            and abs(pool_uniq) < 0.90
        )
        print(
            f"  {v:24s}  per-sym ρ_baseline max={sym_baseline_max:+.3f}  "
            f"per-sym ρ_uniqonly max={sym_uniq_max:+.3f}  "
            f"pooled ρ_baseline={pool_baseline:+.3f}  "
            f"pooled ρ_uniqonly={pool_uniq:+.3f}  "
            f"VALID={valid}"
        )

    print()
    print("Outputs:")
    for f in [
        OUTPUT_DIR / "composite_variants_per_symbol.csv",
        OUTPUT_DIR / "composite_variants_portfolio.csv",
    ]:
        print(f"  {f.relative_to(REPO)}")


if __name__ == "__main__":
    main()
