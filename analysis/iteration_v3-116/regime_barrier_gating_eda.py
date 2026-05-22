"""iter-v3/116 — regime-conditioned exit-barrier architecture — Phase-1 GO/NO-GO EDA.

Tests the cycle-6 EXPLORATION-slot-#7 axis: a regime-conditioned asymmetric exit barrier
— the v3-canonical triple-barrier label estimand kept, but the (tp_mult, sl_mult) ATR
multipliers made a function of the ENTRY-BAR regime state instead of the static 2.0/1.0.

This EDA re-resolves the existing /059 IS trade-candle outcomes under candidate barrier
geometries directly on the 8h OHLCV path — no model retrain, no backtest. A barrier
change only changes how a trade RESOLVES, never the entry or the model. So the EDA holds
every IS entry fixed (symbol, direction, entry candle) and walks the path under candidate
(tp,sl) pairs. Same /107 / /115 counterfactual machinery.

All tables strictly IS-only (close_time < OOS_CUTOFF_MS = 2025-03-24).

  T1  Regime buckets + per-bucket OPTIMAL barrier geometry — g1.
        For each symbol and each conditioning variable (hurst_100 regime indicator,
        realized-vol z-score), bucket the IS entry candles into 3 quantile buckets
        (q33 / q67 interior edges). For each bucket, sweep a (tp_mult, sl_mult) grid and
        find the geometry that maximizes the bucket's monthly Sharpe on the model's
        actual direction calls (proxied by the static-2:1 label direction). g1 PASSES
        if the per-bucket optimal geometry MATERIALLY DIFFERS across buckets (the optimum
        is not the same (tp,sl) cell in every bucket) on >= 2/3 symbols. If every bucket
        wants the same geometry, regime-conditioning is a no-op global knob.

  T2  Regime-conditioned schedule counterfactual vs static 2:1 — g2.
        Build a per-entry-candle barrier schedule: each entry takes its OWN regime
        bucket's T1-optimal (tp,sl). Re-resolve the whole IS book with that per-entry
        schedule, holding the static-2:1 direction fixed. Compare the conditioned book's
        per-symbol monthly Sharpe against the static-2:1 book's. g2 PASSES if the
        conditioned schedule beats static 2:1 on >= 2/3 symbols AND the worst symbol does
        not regress below a pre-set floor (anchor - 0.30).
        IMPORTANT — this is an IS-OPTIMIZED upper bound: the per-bucket optima T1 picked
        are chosen ON the same IS panel T2 evaluates. T2 is the design ceiling; T3 tests
        whether it survives placebo + out-of-fold. Reported honestly as IS-optimized.

  T3  Robustness — g3.
        (a) Regime-shuffle PLACEBO: re-assign each entry a RANDOM bucket (same bucket-size
            marginal), re-pick per-bucket optima on the shuffled buckets, re-resolve.
            If the conditioned schedule beats static 2:1 just as much under SHUFFLED
            buckets, the T2 "win" is grid-search overfitting, not regime signal.
            g3a PASSES if the real-bucket conditioned advantage materially exceeds the
            shuffled-bucket advantage (real_adv - shuffle_adv >= +0.15 on >= 2/3 symbols).
        (b) Out-of-fold STABILITY: split each symbol's IS months into an early half
            (fold A) and a late half (fold B). Pick the per-bucket optima on fold A;
            apply that fold-A schedule to fold B; check it still beats static 2:1 on
            fold B. g3b PASSES if the fold-A schedule beats static 2:1 on fold B on
            >= 2/3 symbols (the per-bucket optimum is a stable property, not a fold
            artifact).

PRE-REGISTERED GO RULE (regime_barrier_synthesis.py T4):
  GO  iff  g1 (per-bucket optima materially differ)
           AND g2 (conditioned schedule beats static 2:1 IS-optimized)
           AND g3 (g3a placebo-robust AND g3b out-of-fold-stable).
  Per THE PRIME DIRECTIVE the EDA NEVER terminates the iteration — a NO-GO sharpens the
  brief's pre-registered failure mode and the backtest still runs. The GO/NO-GO verdict
  only sets the brief's modal prediction and the Section-7/8 pre-registration.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import (  # noqa: E402
    ATR_SL_MULT,
    ATR_TP_MULT,
    OOS_CUTOFF_MS,
    SYMBOLS,
    V3_FEATURE_COLUMNS,
    bucket_by_quantile,
    directed_outcome,
    load_symbol_8h,
    monthly_sharpe,
    realvol_zscore,
    resolve_triple_barrier,
)

OUT = Path(__file__).resolve().parent

# (tp_mult, sl_mult) grid swept per regime bucket. Spans the v3 dead-path knobs as
# subgrid points: (2.0,1.0)=/059 anchor, (2.0,1.5)=/065 widening, (1.5,0.75)=/042
# tightening — so the EDA can see whether any regime bucket actually wants one of them.
TP_GRID = [1.0, 1.5, 2.0, 2.5, 3.0]
SL_GRID = [0.5, 0.75, 1.0, 1.5, 2.0]
GRID = [(tp, sl) for tp in TP_GRID for sl in SL_GRID]

N_BUCKETS = 3  # q33 / q67 -> 3 regime buckets
MIN_BUCKET_CANDLES = 60  # a bucket below this is too thin for a stable monthly Sharpe
SHUFFLE_SEED = 116
N_SHUFFLE = 50  # placebo shuffles


# --------------------------------------------------------------------------
# Resolve the FULL grid once per symbol — every (tp,sl) cell's long/short PnL.
# Cached so T1/T2/T3 reuse it without re-walking the OHLCV path.
# --------------------------------------------------------------------------
def resolve_grid(df: pd.DataFrame) -> dict[tuple[float, float], pd.DataFrame]:
    """Resolve every (tp,sl) grid cell for one symbol's IS panel.

    Returns {(tp,sl): resolved_df}. Each resolved_df carries tb_long_pnl_pct /
    tb_short_pnl_pct / tb_label for that geometry.
    """
    cache: dict[tuple[float, float], pd.DataFrame] = {}
    for tp, sl in GRID:
        cache[(tp, sl)] = resolve_triple_barrier(df, tp, sl)
    return cache


def static_direction(grid_cache: dict[tuple[float, float], pd.DataFrame]) -> np.ndarray:
    """The /059 model's direction proxy = the static-2:1 triple-barrier label direction.

    The /059 model is TRAINED on the static-2:1 label, so the static-2:1 label's
    better-side direction is the cleanest zero-foresight proxy for the direction the
    production model calls. The EDA holds THIS direction fixed and varies only the
    barrier geometry — a pure execution-geometry counterfactual (the /115 T3 design).
    """
    anchor = grid_cache[(ATR_TP_MULT, ATR_SL_MULT)]
    return anchor["tb_label"].to_numpy(dtype=np.int64)


# --------------------------------------------------------------------------
# T1 — regime buckets + per-bucket optimal geometry
# --------------------------------------------------------------------------
def conditioning_variable(df: pd.DataFrame, name: str) -> np.ndarray:
    """Return the conditioning-variable series, past-only / look-ahead-clean.

    hurst_100             — a /059 feature; the bar-close Hurst regime indicator. It is a
                            decision-time feature already in the production model, so it
                            is available at entry with no look-ahead.
    realvol_z             — past-only rolling z-score of range_realized_vol_50 (a /059
                            feature); the .shift(1) excludes the entry candle's own
                            realized vol from its own normalization.
    """
    if name == "hurst_100":
        return df["hurst_100"].to_numpy(dtype=np.float64)
    if name == "realvol_z":
        return realvol_zscore(df, lookback=50)
    raise ValueError(name)


def best_geometry_for_mask(
    grid_cache: dict[tuple[float, float], pd.DataFrame],
    direction: np.ndarray,
    open_time: np.ndarray,
    mask: np.ndarray,
) -> tuple[tuple[float, float], float, float]:
    """Find the (tp,sl) cell maximizing the masked subset's monthly Sharpe.

    direction is held FIXED across all cells (the static-2:1 direction proxy). Returns
    (best_cell, best_monthly_sharpe, static_monthly_sharpe_for_same_mask).
    """
    static_out = directed_outcome(grid_cache[(ATR_TP_MULT, ATR_SL_MULT)], direction)
    static_sh = monthly_sharpe(static_out[mask], open_time[mask])
    best_cell = (ATR_TP_MULT, ATR_SL_MULT)
    best_sh = static_sh if np.isfinite(static_sh) else -1e9
    for cell, resolved in grid_cache.items():
        out = directed_outcome(resolved, direction)
        sh = monthly_sharpe(out[mask], open_time[mask])
        if np.isfinite(sh) and sh > best_sh:
            best_sh = sh
            best_cell = cell
    return best_cell, best_sh, static_sh


def t1_regime_buckets() -> pd.DataFrame:
    """T1 — per-bucket optimal barrier geometry, per symbol per conditioning variable."""
    rows = []
    for sym in SYMBOLS:
        df = load_symbol_8h(sym, is_only=True)
        grid_cache = resolve_grid(df)
        direction = static_direction(grid_cache)
        open_time = df["open_time"].to_numpy(dtype=np.int64)
        valid = grid_cache[(ATR_TP_MULT, ATR_SL_MULT)]["tb_valid"].to_numpy(dtype=bool)

        for cond_name in ("hurst_100", "realvol_z"):
            cvar = conditioning_variable(df, cond_name)
            usable = valid & np.isfinite(cvar)
            cv_use = cvar[usable]
            if len(cv_use) < N_BUCKETS * MIN_BUCKET_CANDLES:
                continue
            edges = list(np.quantile(cv_use, [1 / 3, 2 / 3]))
            buckets = bucket_by_quantile(cvar, edges)
            for b in range(N_BUCKETS):
                mask = usable & (buckets == b)
                n = int(mask.sum())
                if n < MIN_BUCKET_CANDLES:
                    rows.append(
                        {
                            "symbol": sym,
                            "cond_var": cond_name,
                            "bucket": b,
                            "n_candles": n,
                            "edge_lo": edges[b - 1] if b > 0 else -np.inf,
                            "edge_hi": edges[b] if b < N_BUCKETS - 1 else np.inf,
                            "best_tp": np.nan,
                            "best_sl": np.nan,
                            "best_monthly_sharpe": np.nan,
                            "static_monthly_sharpe": np.nan,
                            "sharpe_lift_vs_static": np.nan,
                            "note": "bucket too thin",
                        }
                    )
                    continue
                best_cell, best_sh, static_sh = best_geometry_for_mask(
                    grid_cache, direction, open_time, mask
                )
                rows.append(
                    {
                        "symbol": sym,
                        "cond_var": cond_name,
                        "bucket": b,
                        "n_candles": n,
                        "edge_lo": edges[b - 1] if b > 0 else -np.inf,
                        "edge_hi": edges[b] if b < N_BUCKETS - 1 else np.inf,
                        "best_tp": best_cell[0],
                        "best_sl": best_cell[1],
                        "best_monthly_sharpe": round(best_sh, 4),
                        "static_monthly_sharpe": round(static_sh, 4)
                        if np.isfinite(static_sh)
                        else np.nan,
                        "sharpe_lift_vs_static": round(best_sh - static_sh, 4)
                        if np.isfinite(static_sh)
                        else np.nan,
                        "note": "",
                    }
                )
    return pd.DataFrame(rows)


def t1_g1_verdict(t1: pd.DataFrame) -> pd.DataFrame:
    """g1 — do the per-bucket optimal geometries materially differ across buckets?"""
    rows = []
    for (sym, cond), grp in t1.groupby(["symbol", "cond_var"]):
        valid = grp.dropna(subset=["best_tp", "best_sl"])
        if len(valid) < 2:
            rows.append(
                {
                    "symbol": sym,
                    "cond_var": cond,
                    "n_buckets_resolved": len(valid),
                    "distinct_geometries": np.nan,
                    "max_tp_spread": np.nan,
                    "max_sl_spread": np.nan,
                    "g1_differs": False,
                    "note": "too few resolvable buckets",
                }
            )
            continue
        cells = set(zip(valid["best_tp"], valid["best_sl"]))
        tp_spread = valid["best_tp"].max() - valid["best_tp"].min()
        sl_spread = valid["best_sl"].max() - valid["best_sl"].min()
        # "materially differs" = >=2 distinct optimal cells AND the reward:risk ratio
        # (tp/sl) spans a real range, OR a tp/sl absolute spread of >= one grid step.
        differs = len(cells) >= 2 and (tp_spread >= 0.5 or sl_spread >= 0.25)
        rows.append(
            {
                "symbol": sym,
                "cond_var": cond,
                "n_buckets_resolved": len(valid),
                "distinct_geometries": len(cells),
                "max_tp_spread": round(tp_spread, 4),
                "max_sl_spread": round(sl_spread, 4),
                "g1_differs": bool(differs),
                "note": "",
            }
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# T2 — regime-conditioned schedule counterfactual vs static 2:1
# --------------------------------------------------------------------------
def conditioned_outcome(
    df: pd.DataFrame,
    grid_cache: dict[tuple[float, float], pd.DataFrame],
    direction: np.ndarray,
    buckets: np.ndarray,
    bucket_optima: dict[int, tuple[float, float]],
) -> np.ndarray:
    """Per-entry-candle conditioned outcome — each entry uses its bucket's optimal (tp,sl).

    For bucket b, every entry in b uses bucket_optima[b]'s resolved long/short PnL.
    Entries with bucket == -1 (NaN conditioning var) fall back to the static 2:1 cell.
    """
    n = len(df)
    out = np.full(n, np.nan)
    fallback = directed_outcome(grid_cache[(ATR_TP_MULT, ATR_SL_MULT)], direction)
    out[:] = fallback  # default = static for unbucketed entries
    for b, cell in bucket_optima.items():
        sel = buckets == b
        if not sel.any():
            continue
        cell_out = directed_outcome(grid_cache[cell], direction)
        out[sel] = cell_out[sel]
    return out


def t2_conditioned_vs_static(t1: pd.DataFrame) -> pd.DataFrame:
    """T2 — conditioned-schedule per-symbol monthly Sharpe vs static 2:1 (IS-optimized)."""
    rows = []
    for sym in SYMBOLS:
        df = load_symbol_8h(sym, is_only=True)
        grid_cache = resolve_grid(df)
        direction = static_direction(grid_cache)
        open_time = df["open_time"].to_numpy(dtype=np.int64)
        valid = grid_cache[(ATR_TP_MULT, ATR_SL_MULT)]["tb_valid"].to_numpy(dtype=bool)
        static_out = directed_outcome(grid_cache[(ATR_TP_MULT, ATR_SL_MULT)], direction)
        static_sh = monthly_sharpe(static_out[valid], open_time[valid])

        for cond_name in ("hurst_100", "realvol_z"):
            sub = t1[(t1["symbol"] == sym) & (t1["cond_var"] == cond_name)]
            sub = sub.dropna(subset=["best_tp", "best_sl"])
            if len(sub) < 2:
                continue
            cvar = conditioning_variable(df, cond_name)
            usable = valid & np.isfinite(cvar)
            cv_use = cvar[usable]
            edges = list(np.quantile(cv_use, [1 / 3, 2 / 3]))
            buckets = bucket_by_quantile(cvar, edges)
            bucket_optima = {
                int(r.bucket): (float(r.best_tp), float(r.best_sl))
                for r in sub.itertuples()
            }
            cond_out = conditioned_outcome(
                df, grid_cache, direction, buckets, bucket_optima
            )
            cond_sh = monthly_sharpe(cond_out[usable], open_time[usable])
            # static restricted to the SAME usable mask for an apples-to-apples delta
            static_sh_usable = monthly_sharpe(static_out[usable], open_time[usable])
            rows.append(
                {
                    "symbol": sym,
                    "cond_var": cond_name,
                    "n_entries": int(usable.sum()),
                    "static_2to1_monthly_sharpe": round(static_sh_usable, 4),
                    "conditioned_monthly_sharpe": round(cond_sh, 4),
                    "sharpe_lift": round(cond_sh - static_sh_usable, 4)
                    if np.isfinite(cond_sh) and np.isfinite(static_sh_usable)
                    else np.nan,
                    "static_full_panel_sharpe": round(static_sh, 4),
                }
            )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# T3 — robustness: (a) regime-shuffle placebo, (b) out-of-fold stability
# --------------------------------------------------------------------------
def t3a_shuffle_placebo(t2: pd.DataFrame) -> pd.DataFrame:
    """T3a — regime-shuffle placebo: does conditioning on RANDOM buckets help as much?"""
    rng = np.random.default_rng(SHUFFLE_SEED)
    rows = []
    for sym in SYMBOLS:
        df = load_symbol_8h(sym, is_only=True)
        grid_cache = resolve_grid(df)
        direction = static_direction(grid_cache)
        open_time = df["open_time"].to_numpy(dtype=np.int64)
        valid = grid_cache[(ATR_TP_MULT, ATR_SL_MULT)]["tb_valid"].to_numpy(dtype=bool)
        static_out = directed_outcome(grid_cache[(ATR_TP_MULT, ATR_SL_MULT)], direction)

        for cond_name in ("hurst_100", "realvol_z"):
            t2row = t2[(t2["symbol"] == sym) & (t2["cond_var"] == cond_name)]
            if t2row.empty or not np.isfinite(t2row["sharpe_lift"].iloc[0]):
                continue
            real_lift = float(t2row["sharpe_lift"].iloc[0])
            cvar = conditioning_variable(df, cond_name)
            usable = valid & np.isfinite(cvar)
            cv_use = cvar[usable]
            edges = list(np.quantile(cv_use, [1 / 3, 2 / 3]))
            real_buckets = bucket_by_quantile(cvar, edges)
            static_sh_usable = monthly_sharpe(static_out[usable], open_time[usable])

            shuffle_lifts = []
            usable_idx = np.where(usable)[0]
            real_b_usable = real_buckets[usable_idx]
            for _ in range(N_SHUFFLE):
                # shuffle preserves the per-bucket SIZE marginal — permute bucket labels
                perm = rng.permutation(real_b_usable)
                shuf_buckets = np.full(len(df), -1, dtype=np.int64)
                shuf_buckets[usable_idx] = perm
                # re-pick per-bucket optima on the SHUFFLED buckets
                shuf_optima = {}
                for b in range(N_BUCKETS):
                    mask = (shuf_buckets == b) & usable
                    if mask.sum() < MIN_BUCKET_CANDLES:
                        shuf_optima[b] = (ATR_TP_MULT, ATR_SL_MULT)
                        continue
                    best_cell, _, _ = best_geometry_for_mask(
                        grid_cache, direction, open_time, mask
                    )
                    shuf_optima[b] = best_cell
                shuf_out = conditioned_outcome(
                    df, grid_cache, direction, shuf_buckets, shuf_optima
                )
                shuf_sh = monthly_sharpe(shuf_out[usable], open_time[usable])
                if np.isfinite(shuf_sh) and np.isfinite(static_sh_usable):
                    shuffle_lifts.append(shuf_sh - static_sh_usable)
            shuffle_lifts = np.array(shuffle_lifts)
            mean_shuf = float(np.mean(shuffle_lifts)) if len(shuffle_lifts) else np.nan
            q95_shuf = (
                float(np.quantile(shuffle_lifts, 0.95))
                if len(shuffle_lifts)
                else np.nan
            )
            rows.append(
                {
                    "symbol": sym,
                    "cond_var": cond_name,
                    "real_lift": round(real_lift, 4),
                    "shuffle_mean_lift": round(mean_shuf, 4),
                    "shuffle_q95_lift": round(q95_shuf, 4),
                    "real_minus_shuffle_mean": round(real_lift - mean_shuf, 4)
                    if np.isfinite(mean_shuf)
                    else np.nan,
                    "real_beats_shuffle_q95": bool(
                        np.isfinite(q95_shuf) and real_lift > q95_shuf
                    ),
                }
            )
    return pd.DataFrame(rows)


def t3b_out_of_fold(t2: pd.DataFrame) -> pd.DataFrame:
    """T3b — out-of-fold stability: fold-A-picked schedule applied to fold B."""
    rows = []
    for sym in SYMBOLS:
        df = load_symbol_8h(sym, is_only=True)
        grid_cache = resolve_grid(df)
        direction = static_direction(grid_cache)
        open_time = df["open_time"].to_numpy(dtype=np.int64)
        valid = grid_cache[(ATR_TP_MULT, ATR_SL_MULT)]["tb_valid"].to_numpy(dtype=bool)
        static_out = directed_outcome(grid_cache[(ATR_TP_MULT, ATR_SL_MULT)], direction)

        months = pd.to_datetime(open_time, unit="ms", utc=True).tz_localize(None).to_period("M")
        months_arr = np.asarray(months)
        uniq_months = sorted(set(months_arr[valid]))
        if len(uniq_months) < 12:
            continue
        mid = uniq_months[len(uniq_months) // 2]
        fold_a = months_arr <= mid
        fold_b = months_arr > mid

        for cond_name in ("hurst_100", "realvol_z"):
            t2row = t2[(t2["symbol"] == sym) & (t2["cond_var"] == cond_name)]
            if t2row.empty:
                continue
            cvar = conditioning_variable(df, cond_name)
            usable = valid & np.isfinite(cvar)
            # edges fitted on fold A only (no fold-B leakage into the bucketing)
            cv_a = cvar[usable & fold_a]
            if len(cv_a) < N_BUCKETS * MIN_BUCKET_CANDLES:
                continue
            edges_a = list(np.quantile(cv_a, [1 / 3, 2 / 3]))
            buckets = bucket_by_quantile(cvar, edges_a)
            # per-bucket optima picked on fold A only
            fold_a_optima = {}
            for b in range(N_BUCKETS):
                mask_a = (buckets == b) & usable & fold_a
                if mask_a.sum() < MIN_BUCKET_CANDLES:
                    fold_a_optima[b] = (ATR_TP_MULT, ATR_SL_MULT)
                    continue
                best_cell, _, _ = best_geometry_for_mask(
                    grid_cache, direction, open_time, mask_a
                )
                fold_a_optima[b] = best_cell
            # apply the fold-A schedule to fold B
            cond_out = conditioned_outcome(
                df, grid_cache, direction, buckets, fold_a_optima
            )
            mask_b = usable & fold_b
            cond_sh_b = monthly_sharpe(cond_out[mask_b], open_time[mask_b])
            static_sh_b = monthly_sharpe(static_out[mask_b], open_time[mask_b])
            rows.append(
                {
                    "symbol": sym,
                    "cond_var": cond_name,
                    "fold_b_n_entries": int(mask_b.sum()),
                    "fold_b_static_sharpe": round(static_sh_b, 4)
                    if np.isfinite(static_sh_b)
                    else np.nan,
                    "fold_b_conditioned_sharpe": round(cond_sh_b, 4)
                    if np.isfinite(cond_sh_b)
                    else np.nan,
                    "fold_b_lift": round(cond_sh_b - static_sh_b, 4)
                    if np.isfinite(cond_sh_b) and np.isfinite(static_sh_b)
                    else np.nan,
                    "fold_a_schedule_helps_fold_b": bool(
                        np.isfinite(cond_sh_b)
                        and np.isfinite(static_sh_b)
                        and cond_sh_b > static_sh_b
                    ),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    print("=" * 78)
    print("iter-v3/116 — regime-conditioned exit-barrier — Phase-1 GO/NO-GO gating EDA")
    print(f"OOS cutoff (IMMUTABLE): {OOS_CUTOFF_MS} (2025-03-24) — IS-only")
    print(f"grid: {len(GRID)} (tp,sl) cells; {N_BUCKETS} regime buckets per symbol")
    print(f"V3_FEATURE_COLUMNS unchanged ({len(V3_FEATURE_COLUMNS)}) — EXIT-LAYER axis")
    print("=" * 78)

    print("\n[T1] regime buckets + per-bucket optimal geometry ...")
    t1 = t1_regime_buckets()
    t1.to_csv(OUT / "T1_regime_bucket_optima.csv", index=False)
    print(t1.to_string(index=False))

    g1 = t1_g1_verdict(t1)
    g1.to_csv(OUT / "T1b_g1_geometry_differs.csv", index=False)
    print("\n[g1] per-bucket optimal geometry differs?")
    print(g1.to_string(index=False))

    print("\n[T2] regime-conditioned schedule vs static 2:1 (IS-optimized ceiling) ...")
    t2 = t2_conditioned_vs_static(t1)
    t2.to_csv(OUT / "T2_conditioned_vs_static.csv", index=False)
    print(t2.to_string(index=False))

    print("\n[T3a] regime-shuffle placebo ...")
    t3a = t3a_shuffle_placebo(t2)
    t3a.to_csv(OUT / "T3a_shuffle_placebo.csv", index=False)
    print(t3a.to_string(index=False))

    print("\n[T3b] out-of-fold stability ...")
    t3b = t3b_out_of_fold(t2)
    t3b.to_csv(OUT / "T3b_out_of_fold.csv", index=False)
    print(t3b.to_string(index=False))

    print("\nEDA tables written to analysis/iteration_v3-116/. Run synthesis next.")


if __name__ == "__main__":
    main()
