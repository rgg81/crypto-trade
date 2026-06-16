"""IS-ONLY sub-period stability test of a PREDICTED-MAGNITUDE entry gate on a directional book — iter-v1/016 (BTCUSDT).

CAMPAIGN CONTEXT (the pivot rationale)
--------------------------------------
The DIRECTIONAL approach is exhausted on BTC 8h (diary-v1/009..015). The IS directional edge is
strong (IS Sharpe up to +0.88 at the 14d let-winners-run horizon) but OVERFITS: the IS-bull longs
INVERT to OOS-bull (within-regime, seed-deterministic; diary-012), so the OOS directional Sharpe is
structurally negative (-1.18) at EVERY horizon. No overlay flips the SIGN (de-lever iter-012 failed;
R2 brake iter-015 cut OOS loss magnitude 80% but left Sharpe sign unchanged — sizing preserves the
ratio).

The ONE thing the iter-014 Feature Engineer screen proved is sub-period-STABLE and GENERALIZABLE is
the VOLATILITY-MAGNITUDE signal: IC vs |forward move| up to +0.22, sign-consistent across up to
100% of IS sub-periods (vol_natr_7 frac_same_sign 1.00; vol_garman_klass_20 IC_|fwd| +0.233). BTC
8h has a learnable, generalizable signal about HOW BIG the next move is — just not reliably WHICH WAY.

THE QUESTION THIS SCRIPT ANSWERS (IS-ONLY)
------------------------------------------
Framing 1 (magnitude-gated directional): keep a direction rule, but only ENTER when the model
predicts a LARGE |move| (the stable signal). Edge = timing big moves, not picking direction. Does
gating entries on predicted-magnitude lift the directional book's edge in a way that is SUB-PERIOD
STABLE (the iter-011/014 generalization lens)?

The decisive contrast is NOT "does gating raise the full-IS Sharpe" (that is a peak-IS metric the
campaign has shown is a trap). It is: does gating make the per-sub-period edge MORE STABLE — higher
frac of positive sub-periods, lower dispersion, and crucially a LESS-NEGATIVE most-recent sub-period
(the 2025-Q1 row that iter-011 showed pre-prints OOS)? A magnitude gate that helps OOS must move
those stability statistics in the right direction, because the gate's INPUT (vol-magnitude) is the
only thing on BTC 8h that is cross-regime stable.

WHAT THIS SCRIPT DOES (IS-ONLY, walk-forward, past-only)
--------------------------------------------------------
1. Build the directional book proxy at the campaign's N=42 (14d) let-winners-run horizon: direction
   = sign of the realized N-candle-forward log return; per-trade signed return = that forward return
   (this is the let-winners-run / fixed_horizon mechanism the engine implements — the model targets
   sign(fwd_N), the trade earns the forward move). This is the SAME proxy iter-011/014 used; it is a
   faithful, fast stand-in for the bagged specialist whose sub-period stability ranking matched the
   real backtest in every prior screen (iter-011/014).
2. Build a PREDICTED-MAGNITUDE gate with NO look-ahead: a purged, embargoed, walk-forward LightGBM
   REGRESSOR trained ONLY on candles strictly before each ~6-month test sub-period (minus an embargo
   >= label horizon), on the FE's stable vol-magnitude CORE features, predicting |forward N-return|.
   At each test candle the gate fires (allows the trade) iff predicted |move| >= a past-only
   percentile threshold of the TRAINING-window predictions (so the threshold itself uses no future
   data and no test-window data). Quantile grid {p50, p60, p70} = "trade only the top 50/40/30% of
   candles by predicted magnitude".
3. Compare UNGATED vs GATED on the cross-sub-period STABILITY metrics that predict OOS generalization:
   per-sub-period annualized Sharpe, frac_pos sub-periods, dispersion, worst sub-period, and the
   MOST-RECENT sub-period (the OOS-fragility fingerprint). Also reports trade-count retention so a
   gate that "wins" only by trading 5 candles is exposed.
4. Also runs a NAIVE-VOL-GATE baseline (gate on raw vol_natr_7 percentile, no model) to separate
   "the model adds value" from "any vol filter helps".

OOS-VIGILANCE (HARD)
--------------------
- Strict `open_time < OOS_CUTOFF_MS = 1742774400000` (2025-03-24) filter + leak-guard assert BEFORE
  any forward quantity is computed.
- Forward N-return computed AFTER the IS filter (tail rows NaN-mask — no OOS candle is in the frame).
- The magnitude regressor trains ONLY on rows whose open_time is strictly before each test
  sub-period start minus an embargo of N_LABEL candles (>= the label horizon). The percentile gate
  threshold is computed from TRAINING-window predictions only. Nothing is fit/selected/calibrated
  against OOS; OOS rows are never read. Features are read as-is (already past-only by features_v1).
- `src/`, the runner, and OOS are UNTOUCHED.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-016/magnitude_gate_subperiod_stability.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24
SYMBOL = "BTCUSDT"
PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-016"

N_LABEL = 42  # 14d let-winners-run horizon — the campaign's strongest IS base (iter-013 IS +0.88)
BARS_PER_YEAR = 365.0 * 3.0  # 8h candles -> 3/day
SUBPERIOD_DAYS = 182.5  # ~6 months
MIN_SUB_TRADES = 8  # require >= this many gated trades in a sub-period to score its Sharpe
EMBARGO = N_LABEL  # >= label horizon, both-sides purge handled by strict train<test-start filter

# FE iter-014 IS-VALIDATED stable vol-magnitude CORE (cluster-17 representatives across windows).
# These are the features whose IC vs |forward move| is 4-5x their IC vs signed return and are
# sign-consistent across up to 100% of IS sub-periods. This is the gate model's input.
MAG_CORE: tuple[str, ...] = (
    "vol_natr_7",
    "vol_natr_14",
    "vol_garman_klass_10",
    "vol_garman_klass_20",
    "vol_parkinson_10",
    "vol_parkinson_20",
    "vol_bb_bandwidth_20",
    "vol_bb_bandwidth_30",
    "vol_atr_14",
    "vol_hist_20",
    "vol_range_spike_72",
    "interact_natr_x_adx",
)

GATE_QUANTILES = (0.50, 0.60, 0.70)  # trade top 50% / 40% / 30% by predicted magnitude


def fwd_log_return(close: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(close), np.nan)
    for i in range(len(close) - n):
        if close[i] > 0 and close[i + n] > 0:
            out[i] = np.log(close[i + n] / close[i])
    return out


def subperiod_bounds(ot_days: np.ndarray) -> list[tuple[float, float]]:
    t0, t1 = ot_days.min(), ot_days.max()
    edges, edge = [], t0
    while edge < t1:
        hi = edge + SUBPERIOD_DAYS
        edges.append((edge, hi))
        edge = hi
    return edges


def ann_sharpe(per_trade: np.ndarray, trades_per_year: float) -> float:
    """Annualized Sharpe of a per-trade signed-return series.

    Scaled to per-trade frequency so gated/ungated books with different trade counts are comparable.
    """
    r = per_trade[np.isfinite(per_trade)]
    if len(r) < 3 or np.std(r, ddof=1) == 0:
        return np.nan
    return float(np.mean(r) / np.std(r, ddof=1) * np.sqrt(trades_per_year))


def walk_forward_mag_predictions(
    df: pd.DataFrame,
    bounds: list[tuple[float, float]],
    ot_days: np.ndarray,
    abs_y: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Purged/embargoed walk-forward predictions of |forward N-return| + per-row train-window p-thresholds.

    For each ~6-month test sub-period [lo, hi): train a LightGBM regressor on ALL rows whose
    open_time is strictly before (lo - EMBARGO candles) with a finite |fwd| label, predict on the
    test rows. Returns (pred_abs, train_pred_q) where train_pred_q[gi] holds, for each quantile in
    GATE_QUANTILES, the percentile of TRAINING-window predictions (past-only threshold).
    """
    import lightgbm as lgb

    X = df[list(MAG_CORE)].to_numpy(float)
    n = len(df)
    pred = np.full(n, np.nan)
    # per-row, per-quantile training threshold (so the gate uses no future/test data for its cutoff)
    thr = {q: np.full(n, np.nan) for q in GATE_QUANTILES}

    # candle index per row for embargo arithmetic (rows are time-sorted single-symbol)
    row_idx = np.arange(n)
    for lo, hi in bounds:
        test_mask = (ot_days >= lo) & (ot_days < hi)
        if test_mask.sum() == 0:
            continue
        first_test_i = int(row_idx[test_mask].min())
        train_cut_i = first_test_i - EMBARGO  # strict past + embargo >= label horizon
        if train_cut_i < 200:  # need a minimum training history
            continue
        train_mask = (row_idx < train_cut_i) & np.isfinite(abs_y) & np.isfinite(X).all(axis=1)
        if train_mask.sum() < 200:
            continue
        Xtr, ytr = X[train_mask], abs_y[train_mask]
        model = lgb.LGBMRegressor(
            n_estimators=200,
            num_leaves=31,
            max_depth=5,
            learning_rate=0.05,
            min_child_samples=30,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_lambda=1.0,
            random_state=42,
            verbose=-1,
        )
        model.fit(Xtr, ytr)
        # training-window predictions define the past-only gate thresholds
        tr_pred = model.predict(Xtr)
        # test predictions
        test_rows = row_idx[test_mask]
        Xte = X[test_rows]
        ok = np.isfinite(Xte).all(axis=1)
        te_pred = np.full(len(test_rows), np.nan)
        if ok.sum() > 0:
            te_pred[ok] = model.predict(Xte[ok])
        pred[test_rows] = te_pred
        for q in GATE_QUANTILES:
            thr[q][test_rows] = float(np.quantile(tr_pred, q))
    return pred, thr


def stability_stats(per_trade_by_sub: list[np.ndarray], sub_labels: list[str]) -> dict:
    sharpes = []
    for arr in per_trade_by_sub:
        valid = arr[np.isfinite(arr)]
        if len(valid) >= MIN_SUB_TRADES:
            # per-trade frequency in THIS sub-period ~ trades per sub-period scaled to year
            tpy = BARS_PER_YEAR / max(N_LABEL, 1)  # let-run holds ~N_LABEL candles per trade
            sharpes.append(ann_sharpe(valid, tpy))
        else:
            sharpes.append(np.nan)
    s = np.array(sharpes, float)
    valid = s[np.isfinite(s)]
    if len(valid) == 0:
        return dict(per_sub=dict(zip(sub_labels, sharpes, strict=True)),
                    frac_pos=np.nan, dispersion=np.nan, worst=np.nan, recent=np.nan, n_scored=0)
    recent = next((v for v in reversed(s) if np.isfinite(v)), np.nan)
    return dict(
        per_sub=dict(zip(sub_labels, [round(float(x), 4) if np.isfinite(x) else np.nan for x in s],
                         strict=True)),
        frac_pos=round(float(np.mean(valid > 0)), 3),
        dispersion=round(float(np.std(valid, ddof=1)) if len(valid) > 1 else 0.0, 4),
        worst=round(float(np.min(valid)), 4),
        recent=round(float(recent), 4) if np.isfinite(recent) else np.nan,
        n_scored=int(len(valid)),
    )


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df_full = pd.read_parquet(PARQUET)
    df = df_full[df_full["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"

    miss = [c for c in MAG_CORE if c not in df.columns]
    assert not miss, f"missing magnitude-core columns: {miss}"

    close = df["close"].to_numpy(float)
    ot_days = df["open_time"].to_numpy(float) / 86400_000.0
    y = fwd_log_return(close, N_LABEL)       # signed forward N-return (computed AFTER IS filter)
    abs_y = np.abs(y)                        # magnitude target for the gate model
    direction = np.where(np.isfinite(y), np.sign(y), np.nan)  # let-run direction proxy
    per_trade_signed = y.copy()              # let-winners-run: trade earns the forward move

    bounds = subperiod_bounds(ot_days)
    sub_labels = [str(pd.to_datetime(lo * 86400_000, unit="ms").date()) for lo, _ in bounds]
    print(f"IS rows: {len(df)}  span days: {round(ot_days.max() - ot_days.min())}  "
          f"sub-periods ({len(bounds)}): {sub_labels}")
    print(f"horizon N={N_LABEL} (14d let-winners-run)  embargo={EMBARGO} candles  "
          f"magnitude-core feats: {len(MAG_CORE)}")
    print("=" * 118)

    # ---- walk-forward predicted-magnitude (NO look-ahead) ----
    pred_abs, thr = walk_forward_mag_predictions(df, bounds, ot_days, abs_y)
    n_pred = int(np.isfinite(pred_abs).sum())
    print(f"walk-forward magnitude predictions made on {n_pred} test rows "
          f"(rows before the first scoreable test window have no model and are excluded).")

    # ---- per-sub-period UNGATED book (all candles with a finite forward move) ----
    def sub_arrays(fire_mask: np.ndarray) -> list[np.ndarray]:
        out = []
        for lo, hi in bounds:
            m = (ot_days >= lo) & (ot_days < hi) & fire_mask & np.isfinite(per_trade_signed)
            out.append(per_trade_signed[m])
        return out

    # Restrict ALL books to rows where a walk-forward prediction exists, so ungated vs gated are
    # measured on the SAME candle universe (apples-to-apples; no free lunch from extra early candles).
    scoreable = np.isfinite(pred_abs) & np.isfinite(per_trade_signed) & np.isfinite(direction)

    ungated = stability_stats(sub_arrays(scoreable), sub_labels)

    # ---- gated books: model-predicted magnitude >= past-only training-window percentile ----
    gated_results = {}
    for q in GATE_QUANTILES:
        fire = scoreable & (pred_abs >= thr[q])
        gated_results[q] = stability_stats(sub_arrays(fire), sub_labels)
        gated_results[q]["n_trades"] = int(fire.sum())
        gated_results[q]["retention"] = round(int(fire.sum()) / max(int(scoreable.sum()), 1), 3)

    # ---- NAIVE vol gate (raw vol_natr_7 percentile, no model) for the same quantiles ----
    natr = df["vol_natr_7"].to_numpy(float)
    naive_results = {}
    for q in GATE_QUANTILES:
        # past-only naive threshold: use an EXPANDING-window quantile so no future data leaks
        thr_naive = np.full(len(df), np.nan)
        for lo, hi in bounds:
            test_mask = (ot_days >= lo) & (ot_days < hi)
            if test_mask.sum() == 0:
                continue
            row_idx = np.arange(len(df))
            first_test_i = int(row_idx[test_mask].min())
            past = natr[: max(first_test_i - EMBARGO, 0)]
            past = past[np.isfinite(past)]
            if len(past) < 200:
                continue
            thr_naive[test_mask] = float(np.quantile(past, q))
        fire = scoreable & np.isfinite(thr_naive) & (natr >= thr_naive)
        naive_results[q] = stability_stats(sub_arrays(fire), sub_labels)
        naive_results[q]["n_trades"] = int(fire.sum())
        naive_results[q]["retention"] = round(int(fire.sum()) / max(int(scoreable.sum()), 1), 3)

    # ---- print headline stability comparison ----
    def fmt(d: dict, label: str, extra: str = "") -> None:
        print(f"  {label:34s} frac_pos={d['frac_pos']!s:>5}  disp={d['dispersion']!s:>7}  "
              f"worst={d['worst']!s:>8}  RECENT={d['recent']!s:>8}  n_scored={d['n_scored']}{extra}")

    print("\nSUB-PERIOD STABILITY — ungated directional book (same candle universe):")
    fmt(ungated, "UNGATED (all predicted candles)")

    print("\nMODEL-PREDICTED-MAGNITUDE GATE (trade only high predicted |move| candles):")
    for q in GATE_QUANTILES:
        d = gated_results[q]
        fmt(d, f"GATE p{int(q*100)} (top {int((1-q)*100)}% |move|)",
            f"  trades={d['n_trades']}  retention={d['retention']}")

    print("\nNAIVE VOL GATE (raw vol_natr_7 percentile, no model) — control:")
    for q in GATE_QUANTILES:
        d = naive_results[q]
        fmt(d, f"NAIVE p{int(q*100)}",
            f"  trades={d['n_trades']}  retention={d['retention']}")

    # ---- per-sub-period detail table (the OOS-fragility fingerprint is the LAST column) ----
    print("\n" + "=" * 118)
    print("PER-SUB-PERIOD ANNUALIZED SHARPE (last column = most-recent IS sub-period = OOS fingerprint):")
    hdr = "  " + f"{'book':30s} " + " ".join(f"{lab[2:7]:>7s}" for lab in sub_labels)
    print(hdr)

    def row(d: dict, label: str) -> None:
        cells = []
        for lab in sub_labels:
            v = d["per_sub"].get(lab, np.nan)
            cells.append(f"{v:+7.2f}" if (v is not None and np.isfinite(v)) else f"{'·':>7s}")
        print(f"  {label:30s} " + " ".join(cells))

    row(ungated, "UNGATED")
    for q in GATE_QUANTILES:
        row(gated_results[q], f"GATE p{int(q*100)}")
    for q in GATE_QUANTILES:
        row(naive_results[q], f"NAIVE p{int(q*100)}")

    # ---- write CSV ----
    out_rows = []
    for name, d, q in (
        [("ungated", ungated, None)]
        + [(f"model_gate_p{int(q*100)}", gated_results[q], q) for q in GATE_QUANTILES]
        + [(f"naive_gate_p{int(q*100)}", naive_results[q], q) for q in GATE_QUANTILES]
    ):
        rec = dict(
            book=name, quantile=q, frac_pos=d["frac_pos"], dispersion=d["dispersion"],
            worst_sub=d["worst"], recent_sub=d["recent"], n_scored=d["n_scored"],
            n_trades=d.get("n_trades"), retention=d.get("retention"),
        )
        for lab in sub_labels:
            rec[f"sharpe_{lab}"] = d["per_sub"].get(lab, np.nan)
        out_rows.append(rec)
    res = pd.DataFrame(out_rows)
    res.to_csv(OUTDIR / "magnitude_gate_subperiod_stability.csv", index=False)
    print(f"\nWrote: {OUTDIR / 'magnitude_gate_subperiod_stability.csv'}")

    # ---- interpretation guard (printed, NOT a gate) ----
    print("\n" + "=" * 118)
    print("READ: a magnitude gate that PREDICTS OOS generalization must, vs UNGATED, (a) RAISE")
    print("frac_pos, (b) LOWER dispersion, and (c) make RECENT (last column) LESS NEGATIVE — while")
    print("retaining enough trades (retention >= ~0.3) to be a real strategy. If the MODEL gate")
    print("beats the NAIVE gate on RECENT, the learned magnitude adds value beyond a raw vol filter.")


if __name__ == "__main__":
    main()
