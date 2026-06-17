"""IS-ONLY: does a VOLATILITY-MAGNITUDE-selected book beat the iter-020 conviction-gate book on
cross-IS-sub-period STABILITY? — iter-v1/023 (BTCUSDT).

CAMPAIGN WALL (triply-confirmed iter-016/021/022): any mechanism that makes the OOS edge ride the
model's SEED-VARYING directional TIMING/SELECTION is a K=5 lottery that collapses at K=20. Only the
DETERMINISTIC parts generalize — the stateless 200-SMA trend-state direction, and the IS-calibrated
conviction gate (|close-SMA200|/ATR >= q quantile).

FE iter-014 finding (the one untried lever): the VOLATILITY-MAGNITUDE signal on BTC 8h is sub-period
STABLE. vol_natr_7 has IC vs |forward move| of +0.220 (vs +0.047 vs signed); vol_garman_klass_20 IC
vs |fwd| +0.233; frac_same_sign up to 1.00. BTC has a learnable, generalizing signal about HOW BIG
the next move is — just not reliably WHICH WAY.

THE iter-023 HYPOTHESIS (tested here, IS-only):
  Keep the DETERMINISTIC 200-SMA trend-state direction. Replace the conviction gate's SELECTION role
  with a VOLATILITY-MAGNITUDE selection: trade the trend-state direction only on candles whose
  PAST-ONLY volatility-magnitude state is HIGH (predicts a large |move| ahead). Two questions:
    Q1. Is the magnitude-selected book MORE sub-period-stable than the iter-020 conviction-gate book?
    Q2 (in seed_stability_magnitude.py). Is the magnitude SELECTION less seed-dependent than the
        directional model's selection?

WHY THIS COULD GENERALIZE WHERE direction/timing tuning didn't:
  - The selection is a PAST-ONLY stateless vol-state rank (NO model, NO seed) — deterministic like the
    trend-state direction. So the SELECTION cannot introduce a seed-lottery (unlike the conviction
    gate which selects via the seed-varying model |signal|... actually the iter-020 gate is ALSO
    deterministic — see note). The magnitude SELECTION just picks DIFFERENT candles than the
    conviction gate: high-coming-vol candles, where the trend-state direction has a bigger |move| to
    capture. Whether that book is more sub-period-stable is the empirical question.

NOTE on the iter-020 conviction gate: it gates on |close-SMA200|/ATR (trend STRENGTH, past-only,
deterministic) — so the iter-020 SELECTION is already deterministic. The K=20 lottery in iter-016/021
came from the MODEL deciding timing/sizing on the gated rows. iter-020 tamed it by making BOTH the
direction (trend-state) AND the gate (strength quantile) deterministic; the model only sizes. This
script compares two DETERMINISTIC selection rules head-to-head on sub-period stability:
    A = iter-020 trend-STRENGTH gate  (|close-SMA200|/ATR >= q)         [the incumbent]
    B = volatility-MAGNITUDE gate     (vol-state rank >= q)              [the iter-023 candidate]
    A+B, A-only, B-only overlap, and a B-SIZED variant (size by predicted magnitude).
Both ride the SAME deterministic trend-state direction; both are model-free for selection; the only
difference is WHICH candles are selected. If B is more sub-period-stable than A, the magnitude signal
genuinely thickens/robustifies the book. If not, the FE's stable magnitude signal does NOT translate
into a more-stable tradeable book — an honest NULL.

OOS-VIGILANCE (HARD): strict `open_time < OOS_CUTOFF_MS` filter + leak-guard assert BEFORE any forward
quantity; `.shift(1)` past-only SMA/ATR/vol-state; per-sub-period selection quantile trained on PAST
rows only (purged by N_LABEL); OOS never read. `src/` + runner + OOS UNTOUCHED.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-023/magnitude_selected_book.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24
SYMBOL = "BTCUSDT"
PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-023"

N_LABEL = 42  # fixed_horizon 14d — the iter-020 baseline label
BARS_PER_YEAR = 365.0 * 3.0  # 8h candles
SUBPERIOD_DAYS = 182.5  # ~6 months -> 11 IS sub-periods
MIN_SUB_TRADES = 8
SMA_WIN = 200  # trend-state direction (deterministic)
ATR_WIN = 14  # conviction-gate normalizer
RT_COST = 0.14  # round-trip fee 0.1% + 2bps/side slippage ~ 0.14% (matches iter-018 proxy)

# iter-020 conviction-gate quantile (the incumbent SELECTION).
Q_STRENGTH = 0.40
# Magnitude-gate quantile sweep (chosen by IS sub-period stability only).
Q_MAG_SWEEP = (0.40, 0.50, 0.60)
# The vol-magnitude state proxies (FE iter-014 stable cluster; all past-only in parquet).
# We use a COMPOSITE rank to be robust (cluster-17 is one axis dressed many ways).
MAG_COLS = ("vol_natr_7", "vol_garman_klass_20", "vol_parkinson_20", "vol_bb_bandwidth_30")


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
        edges.append((edge, edge + SUBPERIOD_DAYS))
        edge += SUBPERIOD_DAYS
    return edges


def ann_sharpe(r: np.ndarray, tpy: float) -> float:
    r = r[np.isfinite(r)]
    if len(r) < 3 or np.std(r, ddof=1) == 0:
        return np.nan
    return float(np.mean(r) / np.std(r, ddof=1) * np.sqrt(tpy))


def stability(pnl: np.ndarray, fire: np.ndarray, ot_days, bounds, tpy, size=None) -> dict:
    """Per-sub-period annualized Sharpe of the selected (optionally sized) book."""
    w = np.ones_like(pnl) if size is None else size
    sh = []
    for lo, hi in bounds:
        m = (ot_days >= lo) & (ot_days < hi) & fire & np.isfinite(pnl)
        arr = (pnl * w)[m]
        sh.append(ann_sharpe(arr, tpy) if int(np.isfinite(arr).sum()) >= MIN_SUB_TRADES else np.nan)
    s = np.array(sh, float)
    valid = s[np.isfinite(s)]
    recent_list = [v for v in reversed(s) if np.isfinite(v)]
    allt = (pnl * w)[fire & np.isfinite(pnl)]
    return dict(
        per_sub=[round(float(x), 3) if np.isfinite(x) else np.nan for x in s],
        full=round(ann_sharpe(allt, tpy), 4) if len(allt) else np.nan,
        frac_pos=round(float(np.mean(valid > 0)), 3) if len(valid) else np.nan,
        dispersion=round(float(np.std(valid, ddof=1)), 4) if len(valid) > 1 else np.nan,
        worst=round(float(np.min(valid)), 4) if len(valid) else np.nan,
        recent1=round(float(recent_list[0]), 3) if len(recent_list) >= 1 else np.nan,
        recent2=round(float(np.mean(recent_list[:2])), 3) if len(recent_list) >= 2 else np.nan,
        recent3=round(float(np.mean(recent_list[:3])), 3) if len(recent_list) >= 3 else np.nan,
        n_pos=int(np.sum(valid > 0)), n_scored=int(len(valid)),
        n_trades=int(np.isfinite((pnl)[fire]).sum()),
        win_rate=round(float(np.mean((pnl)[fire & np.isfinite(pnl)] > 0)), 4) if len(allt) else np.nan,
        mean_ret_pct=round(float(np.mean(allt) * 100.0), 4) if len(allt) else np.nan,
    )


def past_only_quantile_threshold(x, ot_days, bounds, q):
    """Per-sub-period q-quantile of x from PAST rows only (purged by N_LABEL). Same construction as
    the iter-018/020 conviction-gate threshold (deterministic, no model, no seed, no OOS)."""
    thr = np.full(len(x), np.nan)
    row_idx = np.arange(len(x))
    for lo, hi in bounds:
        tm = (ot_days >= lo) & (ot_days < hi)
        if tm.sum() == 0:
            continue
        cut = int(row_idx[tm].min()) - N_LABEL
        if cut < SMA_WIN + ATR_WIN:
            continue
        past = x[:cut]
        past = past[np.isfinite(past)]
        if len(past) < 50:
            continue
        thr[row_idx[tm]] = float(np.quantile(past, q))
    return thr


def composite_vol_rank(df: pd.DataFrame) -> np.ndarray:
    """Past-only composite volatility-magnitude STATE = mean of per-column expanding ranks.
    Each column is already past-only (features_v1). We additionally use an EXPANDING percentile rank
    (rank of x[t] among x[:t]) so the magnitude STATE is comparable across regimes and uses NO future
    info. Returns the composite in [0,1]; high = coming-vol-high regime."""
    n = len(df)
    ranks = np.full((len(MAG_COLS), n), np.nan)
    for j, col in enumerate(MAG_COLS):
        x = df[col].to_numpy(float)
        # expanding percentile rank, past-only: pr[t] = (#{i<t : x[i] <= x[t]}) / t
        order = pd.Series(x)
        # use expanding rank via argsort-free cumulative count; vectorized approximation:
        pr = np.full(n, np.nan)
        # past-only expanding rank is O(n^2) naive; use a running sorted list would be ideal but n=5727
        # is fine with a simple cumulative approach on ranks within an expanding window in chunks.
        finite_idx = np.where(np.isfinite(x))[0]
        for k, t in enumerate(finite_idx):
            if k == 0:
                pr[t] = 0.5
                continue
            prev = x[finite_idx[:k]]
            pr[t] = float(np.mean(prev <= x[t]))
        ranks[j] = pr
    return np.nanmean(ranks, axis=0)


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(PARQUET)
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"

    close = df["close"].to_numpy(float)
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    ot_days = df["open_time"].to_numpy(float) / 86400_000.0
    y = fwd_log_return(close, N_LABEL)
    tpy = BARS_PER_YEAR / N_LABEL
    bounds = subperiod_bounds(ot_days)
    sub_labels = [str(pd.to_datetime(lo * 86400_000, unit="ms").date()) for lo, _ in bounds]

    # --- deterministic trend-state direction + conviction-gate strength (iter-020 incumbent) ---
    cp = pd.Series(close).shift(1).to_numpy()
    sma = pd.Series(close).rolling(SMA_WIN).mean().shift(1).to_numpy()
    tr = np.maximum(high - low, np.maximum(np.abs(high - cp), np.abs(low - cp)))
    atr = pd.Series(tr).rolling(ATR_WIN).mean().shift(1).to_numpy()
    dist_atr = (cp - sma) / np.where(atr > 0, atr, np.nan)  # signed trend strength, past-only
    absd = np.abs(dist_atr)
    dir_ts = np.where(cp > sma, 1.0, -1.0)  # DETERMINISTIC direction

    base = np.isfinite(y) & np.isfinite(sma) & np.isfinite(cp) & np.isfinite(dist_atr)
    pnl = dir_ts * y - (RT_COST / 100.0)

    # --- SELECTION rule A: iter-020 conviction (trend-strength) gate ---
    thr_str = past_only_quantile_threshold(absd, ot_days, bounds, Q_STRENGTH)
    fire_A = base & np.isfinite(thr_str) & (absd >= thr_str)

    # --- SELECTION rule B: volatility-MAGNITUDE gate (the iter-023 candidate) ---
    vol_rank = composite_vol_rank(df)  # past-only composite vol-state in [0,1]
    base = base & np.isfinite(vol_rank)

    books: dict[str, dict] = {}
    books["A_strength_gate_q40 (iter-020 incumbent)"] = stability(pnl, fire_A, ot_days, bounds, tpy)
    books["ALL_trend_state (no gate)"] = stability(pnl, base, ot_days, bounds, tpy)

    fire_B_by_q = {}
    for q in Q_MAG_SWEEP:
        thr_mag = past_only_quantile_threshold(vol_rank, ot_days, bounds, q)
        fire_B = base & np.isfinite(thr_mag) & (vol_rank >= thr_mag)
        fire_B_by_q[q] = fire_B
        books[f"B_magnitude_gate_q{int(q*100)}"] = stability(pnl, fire_B, ot_days, bounds, tpy)

    # B-SIZED: trade trend-state on high-magnitude candles, SIZED by predicted magnitude (vol_rank
    # mapped to [0.33, 1.0], the let-winners-run sizing floor used by iter-020 R2). Sized variant at
    # the median magnitude gate.
    thr_mag50 = past_only_quantile_threshold(vol_rank, ot_days, bounds, 0.50)
    fire_B50 = base & np.isfinite(thr_mag50) & (vol_rank >= thr_mag50)
    size_mag = 0.33 + 0.67 * np.clip(vol_rank, 0.0, 1.0)
    books["B_magnitude_q50_SIZED_by_mag"] = stability(pnl, fire_B50, ot_days, bounds, tpy, size=size_mag)

    # A AND B (intersection): high-strength AND high-coming-vol — the "best of both" deterministic book.
    fire_AB = fire_A & fire_B_by_q[0.50]
    books["A_AND_B (strength & magnitude)"] = stability(pnl, fire_AB, ot_days, bounds, tpy)
    # A OR B: thickens the book (union).
    fire_AorB = fire_A | fire_B_by_q[0.50]
    books["A_OR_B (strength | magnitude)"] = stability(pnl, fire_AorB, ot_days, bounds, tpy)

    # --- report ---
    print(f"IS rows {len(df)}  N={N_LABEL}(14d)  SMA{SMA_WIN} ATR{ATR_WIN}  RT={RT_COST}%  "
          f"sub-periods={len(bounds)}")
    print(f"MAG composite cols: {MAG_COLS}")
    print("=" * 132)
    print(f"{'book':40s} {'full':>8s} {'fpos':>5s} {'disp':>7s} {'worst':>7s} "
          f"{'rec1':>6s} {'rec2':>6s} {'rec3':>6s} {'npos':>6s} {'trades':>7s} {'WR':>7s} {'mret%':>7s}")
    for name, b in books.items():
        print(f"{name:40s} {b['full']!s:>8} {b['frac_pos']!s:>5} {b['dispersion']!s:>7} "
              f"{b['worst']!s:>7} {b['recent1']!s:>6} {b['recent2']!s:>6} {b['recent3']!s:>6} "
              f"{str(b['n_pos'])+'/'+str(b['n_scored']):>6} {b['n_trades']!s:>7} "
              f"{b['win_rate']!s:>7} {b['mean_ret_pct']!s:>7}")

    print("\n" + "=" * 132)
    print("PER-SUB-PERIOD NET ANNUALIZED SHARPE  (last col = most-recent IS sub-period, the OOS-proxy):")
    print("  " + f"{'book':40s} " + " ".join(f"{lab[2:7]:>7s}" for lab in sub_labels))
    for name, b in books.items():
        cells = [f"{v:+7.2f}" if (v is not None and np.isfinite(v)) else f"{'·':>7s}"
                 for v in b["per_sub"]]
        print(f"  {name:40s} " + " ".join(cells))

    out = []
    for name, b in books.items():
        rec = dict(book=name, **{k: v for k, v in b.items() if k != "per_sub"})
        for i, lab in enumerate(sub_labels):
            rec[f"sharpe_{lab}"] = b["per_sub"][i]
        out.append(rec)
    pd.DataFrame(out).to_csv(OUTDIR / "magnitude_selected_book.csv", index=False)
    print(f"\nWrote: {OUTDIR / 'magnitude_selected_book.csv'}")

    # --- VERDICT scaffold (stability comparison A vs B) ---
    A = books["A_strength_gate_q40 (iter-020 incumbent)"]
    print("\n" + "=" * 132)
    print("STABILITY VERDICT (IS-only) — magnitude gate (B) vs incumbent strength gate (A):")
    print(f"  A (strength q40): full={A['full']} frac_pos={A['frac_pos']} disp={A['dispersion']} "
          f"worst={A['worst']} recent3={A['recent3']} trades={A['n_trades']}")
    for q in Q_MAG_SWEEP:
        B = books[f"B_magnitude_gate_q{int(q*100)}"]
        better = []
        if np.isfinite(B["frac_pos"]) and np.isfinite(A["frac_pos"]) and B["frac_pos"] >= A["frac_pos"]:
            better.append("frac_pos")
        if np.isfinite(B["dispersion"]) and np.isfinite(A["dispersion"]) and B["dispersion"] <= A["dispersion"]:
            better.append("dispersion")
        if np.isfinite(B["worst"]) and np.isfinite(A["worst"]) and B["worst"] >= A["worst"]:
            better.append("worst")
        if np.isfinite(B["recent3"]) and np.isfinite(A["recent3"]) and B["recent3"] >= A["recent3"]:
            better.append("recent3")
        print(f"  B (magnitude q{int(q*100)}): full={B['full']} frac_pos={B['frac_pos']} "
              f"disp={B['dispersion']} worst={B['worst']} recent3={B['recent3']} trades={B['n_trades']}  "
              f"-> B better on: {better if better else 'NONE'}")


if __name__ == "__main__":
    main()
