"""iter-v1/031 EDA — sample-weighting COMPOSITE (AFML Ch.4 §4.6).

GOAL
----
Test whether the COMPOSITE weight

    weight_t = triple_uniqueness_t × inverse_concurrency_t

carries information ORTHOGONAL to its two sub-components when computed on the
v1 baseline IS labels. /016 closed `uniqueness_only` because at v1's dense-
label regime uniqueness collapses to ~1/avg_overlap_count = near-constant
(Spearman 0.997 with uniform). The composite multiplies that by a SECOND
mechanism — peak-concurrency normalization — which is mathematically distinct
and may have non-degenerate ordering.

If the composite Spearman against EITHER sub-component exceeds 0.95, the axis
is empirically degenerate (no new information; collapses to the closed
`uniqueness_only` axis from /016). If both Spearmans are < 0.95, the axis is
orthogonal and worth running.

AFML Ch.4 §4.6 definitions (López de Prado 2018):
- "triple_uniqueness" = `compute_sample_uniqueness` (this is the AFML Ch.4 §4.5
  formula already in `labeling.py:11-109`): uniqueness_i = mean(1/c_t) over
  candles in label window [t_i, t_i+timeout].
- "inverse_concurrency" = 1 - (concurrency_t / max_concurrency), where
  concurrency_t = the count of overlapping label windows AT the entry bar
  (NOT the avg over the window). This is a SCALAR per-bar mapping that
  normalizes peak label-overlap, distinct from the in-window-mean used by
  triple_uniqueness.

The composite weight_t = uniqueness × inverse_concurrency is then renormalized
to sum to n (so Kish n_eff has the same denominator).

IS-ONLY. No model training. Just labeling + statistical characterization.

OUTPUT
------
- weight_distribution.csv: distribution of composite weights (percentiles per symbol)
- spearman_orthogonality.csv: per (symbol) Spearman composite vs uniqueness, composite vs inverse_concurrency, uniqueness vs inverse_concurrency
- concurrency_profile.csv: per (symbol, month) concurrency mean/max and inverse_concurrency mean
- composite_summary.csv: overall composite weight summary stats + verdict
- per_month_kish.csv: per (symbol, month) Kish n_eff under uniform / uniqueness_only / composite
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Repo paths
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

# Baseline ATR-labeling params (matches run_baseline_v1 model A; per-symbol
# multipliers differ but the composite formula is symbol-invariant).
ATR_TP_MULT = 2.9
ATR_SL_MULT = 1.45  # /016 used 1.5; baseline_v1 uses 1.45 — use baseline value
LABEL_TIMEOUT_MIN = 10080  # 7 days = 21 candles at 8h
INTERVAL_MINUTES = 480
TIMEOUT_CANDLES = LABEL_TIMEOUT_MIN // INTERVAL_MINUTES
FEE_PCT = 0.1
ATR_PERIOD = 14


def _compute_atr(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    period: int = ATR_PERIOD,
) -> np.ndarray:
    """Wilder-ATR; caller is responsible for past-only shift."""
    n = len(high)
    tr = np.zeros(n, dtype=np.float64)
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        h_l = high[i] - low[i]
        h_pc = abs(high[i] - close[i - 1])
        l_pc = abs(low[i] - close[i - 1])
        tr[i] = max(h_l, h_pc, l_pc)
    atr = np.full(n, np.nan, dtype=np.float64)
    atr[period - 1] = tr[:period].mean()
    for i in range(period, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def _load_symbol(symbol: str) -> pd.DataFrame:
    path = REPO / "data" / symbol / "8h.csv"
    df = pd.read_csv(path)
    df["symbol"] = symbol
    df["open_time"] = df["open_time"].astype(np.int64)
    df["close_time"] = df["close_time"].astype(np.int64)
    df = df.sort_values("open_time").reset_index(drop=True)
    # Compute ATR (raw past-N) then SHIFT 1 for past-only.
    atr_raw = _compute_atr(
        df["high"].to_numpy(dtype=np.float64),
        df["low"].to_numpy(dtype=np.float64),
        df["close"].to_numpy(dtype=np.float64),
    )
    # Past-only shift one bar.
    atr_pastonly = np.full_like(atr_raw, np.nan)
    atr_pastonly[1:] = atr_raw[:-1]
    df["atr"] = atr_pastonly
    return df


def _build_master(universe: tuple[str, ...]) -> pd.DataFrame:
    frames = [_load_symbol(sym) for sym in universe]
    master = pd.concat(frames, ignore_index=True)
    master = master.sort_values(["open_time", "symbol"]).reset_index(drop=True)
    return master


def _compute_concurrency_at_entry(
    candidate_indices: np.ndarray,
    timeout_minutes: int,
    open_time_arr: np.ndarray,
    sym_arr: np.ndarray,
) -> np.ndarray:
    """Compute concurrency AT THE ENTRY BAR (NOT averaged over the window).

    For each candidate i with entry bar t_i, count how many OTHER label windows
    [t_j, t_j + timeout] contain t_i, restricted to the same symbol.
    Returns the count (including self -> minimum value is 1).

    This is the AFML Ch.4 §4.6 c_{t_i} = count of label windows active AT the
    entry bar — a scalar mapping per candidate, distinct from triple_uniqueness
    which averages 1/c over candles in the label's window.

    Sweep-line over events (same vectorized style as compute_sample_uniqueness).
    """
    n = len(candidate_indices)
    if n == 0:
        return np.array([], dtype=np.float64)

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

        # Events: +1 at start, -1 at end+1
        events = np.concatenate([starts, ends + 1])
        event_vals = np.concatenate([np.ones(m), -np.ones(m)])
        order = np.argsort(events, kind="mergesort")
        events_s = events[order]
        event_vals_s = event_vals[order]
        cum = np.cumsum(event_vals_s)

        # For each candidate's entry t_i, look up c_{t_i} = active count AT t_i.
        # active at t_i = cum at last event <= t_i.
        idx_at = np.searchsorted(events_s, starts, side="right") - 1
        c_at_entry = np.zeros(m, dtype=np.float64)
        valid = idx_at >= 0
        c_at_entry[valid] = cum[idx_at[valid]]
        # The candidate's own window starts AT t_i (event +1 fires at t_i),
        # so c_at_entry already includes self → minimum 1.
        c_at_entry = np.maximum(c_at_entry, 1.0)

        concurrency[ci_arr] = c_at_entry

    return concurrency


def _build_label_set_for_symbol(
    master: pd.DataFrame,
    symbol: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Build the IS-only candidate label set for one symbol.

    Returns:
        candidate_indices: int array of positions in master
        train_labels: triple-barrier labels {1, -1}
        train_weights: baseline abs_pnl weights (matches label_trades default)
        long_pnls, short_pnls: per-direction PnLs
        atr_values: ATR-at-entry per candidate (for inspection)
    """
    sym_mask = (master["symbol"].to_numpy() == symbol) & (
        master["open_time"].to_numpy() < OOS_CUTOFF_MS
    )
    # Drop NaN-ATR rows (first 13 ATR-warmup bars per symbol).
    atr_full = master["atr"].to_numpy()
    valid_atr = ~np.isnan(atr_full)
    candidate_mask = sym_mask & valid_atr
    candidate_indices = np.where(candidate_mask)[0]

    atr_arr = master["atr"].to_numpy()
    train_labels, train_weights, long_pnls, short_pnls = label_trades(
        master,
        candidate_indices,
        ATR_TP_MULT,
        ATR_SL_MULT,
        LABEL_TIMEOUT_MIN,
        fee_pct=FEE_PCT,
        atr_values=atr_arr,
        interval_minutes=INTERVAL_MINUTES,
    )

    return (
        candidate_indices,
        train_labels,
        train_weights,
        long_pnls,
        short_pnls,
        atr_arr[candidate_indices],
    )


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Spearman ρ via numpy ranking. Handles ties via average rank."""
    if len(a) == 0 or len(b) == 0:
        return float("nan")

    def rankavg(x: np.ndarray) -> np.ndarray:
        order = np.argsort(x, kind="mergesort")
        ranks = np.empty_like(order, dtype=np.float64)
        ranks[order] = np.arange(len(x), dtype=np.float64)
        # Average rank for ties.
        df = pd.Series(x).rank(method="average").to_numpy()
        return df

    ra = rankavg(a).astype(np.float64).copy()
    rb = rankavg(b).astype(np.float64).copy()
    ra = ra - ra.mean()
    rb = rb - rb.mean()
    denom = (np.sqrt((ra * ra).sum()) * np.sqrt((rb * rb).sum())) or 1.0
    return float((ra * rb).sum() / denom)


def _month_str(open_ms: int) -> str:
    ts = pd.Timestamp(open_ms, unit="ms", tz="UTC")
    return f"{ts.year:04d}-{ts.month:02d}"


def main() -> None:
    print("=" * 80)
    print("iter-v1/031 EDA — sample-weighting COMPOSITE (AFML Ch.4 §4.6)")
    print("=" * 80)
    print(f"Universe: {V1_BASELINE_UNIVERSE}")
    print(f"OOS_CUTOFF_MS = {OOS_CUTOFF_MS} (IS-only)")
    print(f"Label params: atr_tp={ATR_TP_MULT}, atr_sl={ATR_SL_MULT}, "
          f"timeout={LABEL_TIMEOUT_MIN}min ({TIMEOUT_CANDLES} candles)")
    print()

    master = _build_master(V1_BASELINE_UNIVERSE)
    open_time_arr = master["open_time"].to_numpy(dtype=np.int64)
    sym_arr = master["symbol"].to_numpy()

    # Per-symbol output rows.
    per_symbol_rows: list[dict] = []
    spearman_rows: list[dict] = []
    weight_distribution_rows: list[dict] = []
    per_month_kish_rows: list[dict] = []

    # Aggregate composite across all symbols for portfolio-level summary.
    all_uniq_rows: list[np.ndarray] = []
    all_inv_conc_rows: list[np.ndarray] = []
    all_composite_raw_rows: list[np.ndarray] = []
    all_baseline_w_rows: list[np.ndarray] = []
    all_sym_tags: list[np.ndarray] = []

    for sym in V1_BASELINE_UNIVERSE:
        print(f"--- {sym} ---")
        (
            cand_idx,
            train_labels,
            train_weights_baseline,
            _long,
            _short,
            atr_at_entry,
        ) = _build_label_set_for_symbol(master, sym)
        if len(cand_idx) == 0:
            print(f"  (no candidates)")
            continue

        # AFML triple_uniqueness via production function.
        uniq = compute_sample_uniqueness(
            cand_idx, LABEL_TIMEOUT_MIN, open_time_arr, sym_arr
        )

        # AFML inverse_concurrency: 1 - c_t / max(c_t)
        c_at_entry = _compute_concurrency_at_entry(
            cand_idx, LABEL_TIMEOUT_MIN, open_time_arr, sym_arr
        )
        max_conc = float(c_at_entry.max()) if len(c_at_entry) else 1.0
        inv_conc = 1.0 - (c_at_entry / max_conc)
        # Avoid 0 at the peak-concurrency bar (would zero out the composite).
        # Floor at a small positive value so the composite preserves a baseline
        # weight at the peak — interpretable as "near-zero but non-zero".
        inv_conc_floor = np.maximum(inv_conc, 0.01)

        # COMPOSITE per AFML Ch.4 §4.6.
        composite_raw = uniq * inv_conc_floor
        # Renormalize so mean weight = 1 (preserves total influence; Kish has
        # a fair denominator).
        composite = composite_raw * (len(composite_raw) / composite_raw.sum())

        # Sub-component ranks for orthogonality check.
        rho_comp_uniq = _spearman(composite, uniq)
        rho_comp_invconc = _spearman(composite, inv_conc)
        rho_uniq_invconc = _spearman(uniq, inv_conc)
        rho_comp_baseline = _spearman(composite, train_weights_baseline)
        rho_uniq_baseline = _spearman(uniq, train_weights_baseline)

        # Per-month Kish n_eff (composite, uniform, uniqueness_only, baseline).
        months = np.array([_month_str(t) for t in open_time_arr[cand_idx]])
        unique_months = sorted(set(months))
        for mo in unique_months:
            mask = months == mo
            n = int(mask.sum())
            if n < 5:
                continue
            for label, w in [
                ("baseline_abs_pnl", train_weights_baseline[mask]),
                ("uniform", np.ones(n)),
                ("uniqueness_only", uniq[mask]),
                ("composite", composite[mask]),
            ]:
                w_sum = w.sum()
                if w_sum <= 0:
                    kish = 0.0
                else:
                    kish = float((w_sum) ** 2 / (w * w).sum())
                per_month_kish_rows.append({
                    "symbol": sym,
                    "month": mo,
                    "mode": label,
                    "n_actual": n,
                    "kish_n_eff": kish,
                    "kish_ratio": kish / n,
                })

        # Weight distribution percentiles (per symbol).
        for mode_name, w in [
            ("baseline_abs_pnl", train_weights_baseline),
            ("uniqueness_only", uniq),
            ("composite", composite),
        ]:
            wn = w / w.mean() if w.mean() > 0 else w
            weight_distribution_rows.append({
                "symbol": sym,
                "mode": mode_name,
                "n": len(w),
                "min_norm": float(wn.min()),
                "p05_norm": float(np.percentile(wn, 5)),
                "p25_norm": float(np.percentile(wn, 25)),
                "p50_norm": float(np.percentile(wn, 50)),
                "p75_norm": float(np.percentile(wn, 75)),
                "p95_norm": float(np.percentile(wn, 95)),
                "max_norm": float(wn.max()),
                "frac_below_0p5": float((wn < 0.5).mean()),
                "frac_above_0p9": float((wn > 0.9).mean()),
            })

        # Concurrency profile + bar-level diagnostics.
        per_symbol_rows.append({
            "symbol": sym,
            "n_candidates": int(len(cand_idx)),
            "uniqueness_mean": float(uniq.mean()),
            "uniqueness_std": float(uniq.std()),
            "concurrency_mean": float(c_at_entry.mean()),
            "concurrency_max": float(max_conc),
            "concurrency_p95": float(np.percentile(c_at_entry, 95)),
            "inv_conc_mean": float(inv_conc.mean()),
            "inv_conc_std": float(inv_conc.std()),
            "composite_mean": float(composite.mean()),
            "composite_std": float(composite.std()),
            "composite_min": float(composite.min()),
            "composite_max": float(composite.max()),
            "frac_composite_below_0p5": float((composite < 0.5).mean()),
            "frac_composite_above_0p9_below_1p1": float(
                ((composite >= 0.9) & (composite <= 1.1)).mean()
            ),
            "frac_composite_above_1p5": float((composite > 1.5).mean()),
            "frac_concurrency_eq_max": float((c_at_entry == max_conc).mean()),
            "frac_concurrency_ge_p95_band": float(
                (c_at_entry >= np.percentile(c_at_entry, 95)).mean()
            ),
        })

        spearman_rows.append({
            "symbol": sym,
            "rho_composite_vs_uniqueness": rho_comp_uniq,
            "rho_composite_vs_inv_concurrency": rho_comp_invconc,
            "rho_uniqueness_vs_inv_concurrency": rho_uniq_invconc,
            "rho_composite_vs_baseline_abs_pnl": rho_comp_baseline,
            "rho_uniqueness_vs_baseline_abs_pnl": rho_uniq_baseline,
            "verdict_orthogonal_to_uniqueness": rho_comp_uniq < 0.95,
            "verdict_orthogonal_to_inv_conc": rho_comp_invconc < 0.95,
        })

        all_uniq_rows.append(uniq)
        all_inv_conc_rows.append(inv_conc)
        all_composite_raw_rows.append(composite)
        all_baseline_w_rows.append(train_weights_baseline)
        all_sym_tags.append(np.array([sym] * len(uniq)))

        print(f"  n_candidates = {len(cand_idx)}")
        print(f"  uniqueness:    mean={uniq.mean():.4f}  std={uniq.std():.4f}  "
              f"min={uniq.min():.4f}  max={uniq.max():.4f}")
        print(f"  concurrency:   mean={c_at_entry.mean():.2f}  max={max_conc:.0f}  "
              f"p95={np.percentile(c_at_entry, 95):.1f}")
        print(f"  inv_conc:      mean={inv_conc.mean():.4f}  std={inv_conc.std():.4f}")
        print(f"  composite:     mean={composite.mean():.4f}  std={composite.std():.4f}")
        print(f"  Spearman composite vs uniqueness     = {rho_comp_uniq:.4f}")
        print(f"  Spearman composite vs inv_concurrency = {rho_comp_invconc:.4f}")
        print(f"  Spearman uniqueness vs inv_conc       = {rho_uniq_invconc:.4f}")
        print(f"  Spearman composite vs baseline abs_pnl = {rho_comp_baseline:.4f}")
        print()

    # Portfolio-level Spearman across pooled candidates.
    pooled_uniq = np.concatenate(all_uniq_rows)
    pooled_inv_conc = np.concatenate(all_inv_conc_rows)
    pooled_composite = np.concatenate(all_composite_raw_rows)
    pooled_baseline = np.concatenate(all_baseline_w_rows)

    rho_port_comp_uniq = _spearman(pooled_composite, pooled_uniq)
    rho_port_comp_invconc = _spearman(pooled_composite, pooled_inv_conc)
    rho_port_uniq_invconc = _spearman(pooled_uniq, pooled_inv_conc)
    rho_port_comp_baseline = _spearman(pooled_composite, pooled_baseline)

    spearman_rows.append({
        "symbol": "PORTFOLIO_POOLED",
        "rho_composite_vs_uniqueness": rho_port_comp_uniq,
        "rho_composite_vs_inv_concurrency": rho_port_comp_invconc,
        "rho_uniqueness_vs_inv_concurrency": rho_port_uniq_invconc,
        "rho_composite_vs_baseline_abs_pnl": rho_port_comp_baseline,
        "rho_uniqueness_vs_baseline_abs_pnl": _spearman(pooled_uniq, pooled_baseline),
        "verdict_orthogonal_to_uniqueness": rho_port_comp_uniq < 0.95,
        "verdict_orthogonal_to_inv_conc": rho_port_comp_invconc < 0.95,
    })

    # Composite summary verdict.
    composite_summary = {
        "n_total_candidates": int(len(pooled_composite)),
        "rho_portfolio_composite_vs_uniqueness": rho_port_comp_uniq,
        "rho_portfolio_composite_vs_inv_concurrency": rho_port_comp_invconc,
        "rho_portfolio_composite_vs_baseline_abs_pnl": rho_port_comp_baseline,
        "verdict_axis_orthogonal": (
            rho_port_comp_uniq < 0.95 and rho_port_comp_invconc < 0.95
        ),
        "frac_composite_below_0p5": float((pooled_composite < 0.5).mean()),
        "frac_composite_above_1p5": float((pooled_composite > 1.5).mean()),
        "composite_mean": float(pooled_composite.mean()),
        "composite_std": float(pooled_composite.std()),
        "composite_min": float(pooled_composite.min()),
        "composite_max": float(pooled_composite.max()),
        "concurrency_max_overall": float(np.concatenate(
            [_compute_concurrency_at_entry(  # type: ignore[arg-type]
                np.where(
                    (master["symbol"].to_numpy() == sym)
                    & (master["open_time"].to_numpy() < OOS_CUTOFF_MS)
                    & ~np.isnan(master["atr"].to_numpy())
                )[0],
                LABEL_TIMEOUT_MIN, open_time_arr, sym_arr
            ) for sym in V1_BASELINE_UNIVERSE]
        ).max()),
    }

    # Write CSVs.
    pd.DataFrame(per_symbol_rows).to_csv(OUTPUT_DIR / "concurrency_profile.csv", index=False)
    pd.DataFrame(spearman_rows).to_csv(OUTPUT_DIR / "spearman_orthogonality.csv", index=False)
    pd.DataFrame(weight_distribution_rows).to_csv(
        OUTPUT_DIR / "weight_distribution.csv", index=False
    )
    pd.DataFrame(per_month_kish_rows).to_csv(
        OUTPUT_DIR / "per_month_kish.csv", index=False
    )
    pd.DataFrame([composite_summary]).to_csv(
        OUTPUT_DIR / "composite_summary.csv", index=False
    )

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"n total IS candidates (pooled): {composite_summary['n_total_candidates']}")
    print(f"composite mean = {composite_summary['composite_mean']:.4f} "
          f"(target 1.0 under mean-normalization)")
    print(f"composite std  = {composite_summary['composite_std']:.4f}")
    print(f"composite min/max = {composite_summary['composite_min']:.4f} / "
          f"{composite_summary['composite_max']:.4f}")
    print()
    print("ORTHOGONALITY VERDICT (portfolio-pooled Spearman):")
    print(f"  composite vs uniqueness        = {rho_port_comp_uniq:.4f}  "
          f"(< 0.95 = orthogonal: {rho_port_comp_uniq < 0.95})")
    print(f"  composite vs inverse_conc      = {rho_port_comp_invconc:.4f}  "
          f"(< 0.95 = orthogonal: {rho_port_comp_invconc < 0.95})")
    print(f"  uniqueness vs inverse_conc     = {rho_port_uniq_invconc:.4f}")
    print(f"  composite vs baseline abs_pnl  = {rho_port_comp_baseline:.4f}")
    print()
    print(f"AXIS VERDICT: orthogonal = {composite_summary['verdict_axis_orthogonal']} "
          f"(both sub-component Spearmans < 0.95)")
    print()
    print(f"Composite weight share at low end:  frac < 0.5 = "
          f"{composite_summary['frac_composite_below_0p5']:.4f}")
    print(f"Composite weight share at high end: frac > 1.5 = "
          f"{composite_summary['frac_composite_above_1p5']:.4f}")
    print()
    print("Outputs written to:")
    for f in sorted(OUTPUT_DIR.glob("*.csv")):
        print(f"  {f.relative_to(REPO)}")


if __name__ == "__main__":
    main()
