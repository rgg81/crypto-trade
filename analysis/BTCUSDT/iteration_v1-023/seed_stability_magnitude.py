"""IS-ONLY: the SEED-STABILITY question + the incremental-information test — iter-v1/023 (BTCUSDT).

The task hypothesis was: a magnitude-prediction-driven SELECTION would be LESS seed-dependent than the
directional model's selection, and would therefore survive K=20 where directional timing collapses.

Two findings from the companion scripts reframe this:
  1. The deployable magnitude SELECTION is a PAST-ONLY vol-state quantile rule — DETERMINISTIC, no
     model, no seed (exactly like the iter-020 strength gate). So selection-by-magnitude has ZERO seed
     variance BY CONSTRUCTION. The "less seed-dependent than the model" claim is trivially true but
     VACUOUS: it's the same deterministic-selection footing iter-020 already has. The K=20 lottery in
     iter-016/021 came from the MODEL doing timing/sizing on selected rows, not from selection.
  2. The binding constraint is direction-correctness: IC(vol_state, trend-state-PnL) INVERTS in the
     most-recent IS sub-periods (24-06 -0.21, 24-12 -0.45) while the strength state stays positive.

This script makes the seed-stability comparison CONCRETE and tests whether magnitude adds incremental
information OVER the incumbent strength gate (the only way it could be worth a new model role):
  (a) SEED-STABILITY of the SELECTION SET: for a magnitude-MODEL (predict whether |fwd move| exceeds a
      threshold) vs a direction-MODEL (the iter-016 collapsed approach), how much does the SELECTED-row
      set vary across seeds? We proxy each "model" by training-window-bootstrapped univariate-rank
      selectors and measure the Jaccard of selected rows across bootstrap resamples. If magnitude
      selection is bootstrap-stable (high Jaccard) and direction selection is not, the hypothesis has
      mechanistic support — but it must STILL clear the direction-correctness test to be tradeable.
  (b) INCREMENTAL test: does the magnitude state pick PROFITABLE trend-state trades that the strength
      gate MISSES? Decompose the union book A_OR_B into the rows ONLY-B selects and ask if those rows
      are net-positive and recent-stable. If the only-B rows are net-negative in recent sub-periods,
      magnitude adds nothing tradeable beyond strength.

OOS-VIGILANCE (HARD): strict IS filter + leak-guard assert; past-only states; bootstrap resamples
within the IS window only; OOS never read. `src/`+runner+OOS UNTOUCHED.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-023/seed_stability_magnitude.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000
SYMBOL = "BTCUSDT"
PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-023"

N_LABEL = 42
BARS_PER_YEAR = 365.0 * 3.0
SUBPERIOD_DAYS = 182.5
MIN_SUB_TRADES = 8
SMA_WIN = 200
ATR_WIN = 14
RT_COST = 0.14
MAG_COLS = ("vol_natr_7", "vol_garman_klass_20", "vol_parkinson_20", "vol_bb_bandwidth_30")
N_BOOT = 20  # bootstrap resamples to proxy "seeds"
SELECT_FRAC = 0.50  # top-half selection


def fwd_log_return(close, n):
    out = np.full(len(close), np.nan)
    for i in range(len(close) - n):
        if close[i] > 0 and close[i + n] > 0:
            out[i] = np.log(close[i + n] / close[i])
    return out


def subperiod_bounds(ot_days):
    t0, t1 = ot_days.min(), ot_days.max()
    edges, edge = [], t0
    while edge < t1:
        edges.append((edge, edge + SUBPERIOD_DAYS))
        edge += SUBPERIOD_DAYS
    return edges


def ann_sharpe(r, tpy):
    r = r[np.isfinite(r)]
    if len(r) < 3 or np.std(r, ddof=1) == 0:
        return np.nan
    return float(np.mean(r) / np.std(r, ddof=1) * np.sqrt(tpy))


def composite_vol_rank(df):
    n = len(df)
    ranks = np.full((len(MAG_COLS), n), np.nan)
    for j, col in enumerate(MAG_COLS):
        x = df[col].to_numpy(float)
        pr = np.full(n, np.nan)
        fi = np.where(np.isfinite(x))[0]
        for k, t in enumerate(fi):
            pr[t] = 0.5 if k == 0 else float(np.mean(x[fi[:k]] <= x[t]))
        ranks[j] = pr
    return np.nanmean(ranks, axis=0)


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(PARQUET)
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"

    close = df["close"].to_numpy(float)
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    ot_days = df["open_time"].to_numpy(float) / 86400_000.0
    y = fwd_log_return(close, N_LABEL)
    yabs = np.abs(y)
    tpy = BARS_PER_YEAR / N_LABEL
    bounds = subperiod_bounds(ot_days)
    sub_labels = [str(pd.to_datetime(lo * 86400_000, unit="ms").date()) for lo, _ in bounds]

    cp = pd.Series(close).shift(1).to_numpy()
    sma = pd.Series(close).rolling(SMA_WIN).mean().shift(1).to_numpy()
    tr = np.maximum(high - low, np.maximum(np.abs(high - cp), np.abs(low - cp)))
    atr = pd.Series(tr).rolling(ATR_WIN).mean().shift(1).to_numpy()
    strength = np.abs((cp - sma) / np.where(atr > 0, atr, np.nan))
    dir_ts = np.where(cp > sma, 1.0, -1.0)
    pnl = dir_ts * y - (RT_COST / 100.0)
    ts_pnl_signed = dir_ts * y

    vol_rank = composite_vol_rank(df)
    base = (np.isfinite(y) & np.isfinite(sma) & np.isfinite(cp)
            & np.isfinite(vol_rank) & np.isfinite(strength))
    idx = np.where(base)[0]

    # ---------------------------------------------------------------------------
    # (a) SEED-STABILITY proxy: Jaccard of the SELECTED-row set across bootstrap "seeds".
    #     magnitude SELECTOR = top-SELECT_FRAC by a bootstrap-fit linear combo of MAG_COLS predicting
    #     |fwd move|. direction SELECTOR = top-SELECT_FRAC by a bootstrap-fit linear combo of the same
    #     vol cols predicting SIGNED fwd return (the thing the iter-016 model tried to learn). Compare
    #     how much the selected set jitters across bootstrap resamples.
    # ---------------------------------------------------------------------------
    feat = np.column_stack([df[c].to_numpy(float) for c in MAG_COLS])
    fin = base & np.all(np.isfinite(feat), axis=1) & np.isfinite(yabs) & np.isfinite(y)
    fidx = np.where(fin)[0]
    Xz = np.full_like(feat, np.nan)
    for j in range(feat.shape[1]):
        col = feat[:, j]
        mu, sd = np.nanmean(col[fin]), np.nanstd(col[fin])
        Xz[:, j] = (col - mu) / (sd if sd > 0 else 1.0)

    def boot_selectors(target):
        """Return list of selected-row index-sets, one per bootstrap seed."""
        sets = []
        Xf = Xz[fidx]
        tf = target[fidx]
        ntop = int(SELECT_FRAC * len(fidx))
        for seed in range(N_BOOT):
            rng = np.random.default_rng(1000 + seed)
            bs = rng.integers(0, len(fidx), len(fidx))
            Xb, tb = Xf[bs], tf[bs]
            # OLS coefs (closed form); tiny ridge for stability
            A = Xb.T @ Xb + 1e-6 * np.eye(Xb.shape[1])
            coef = np.linalg.solve(A, Xb.T @ tb)
            score = Xf @ coef
            top = set(fidx[np.argsort(score)[-ntop:]].tolist())
            sets.append(top)
        return sets

    def mean_jaccard(sets):
        js = []
        for i in range(len(sets)):
            for k in range(i + 1, len(sets)):
                a, b = sets[i], sets[k]
                u = len(a | b)
                js.append(len(a & b) / u if u else np.nan)
        return float(np.nanmean(js))

    mag_sets = boot_selectors(yabs)        # magnitude model (predict |move|)
    dir_sets = boot_selectors(y)           # direction model (predict signed return)
    j_mag = mean_jaccard(mag_sets)
    j_dir = mean_jaccard(dir_sets)

    print(f"IS rows {len(df)}  N={N_LABEL}(14d)  bootstrap seeds={N_BOOT}  select_frac={SELECT_FRAC}")
    print("=" * 120)
    print("(a) SEED-STABILITY of the SELECTED-ROW SET (mean pairwise Jaccard across bootstrap seeds):")
    print(f"  magnitude selector (predict |fwd move|) : Jaccard = {j_mag:.3f}   "
          f"(higher = more seed-stable selection)")
    print(f"  direction selector (predict signed ret) : Jaccard = {j_dir:.3f}")
    print(f"  -> magnitude selection is {'MORE' if j_mag > j_dir else 'NOT MORE'} seed-stable "
          f"than direction selection (Δ={j_mag-j_dir:+.3f}).")
    print("  NOTE: the DEPLOYABLE magnitude rule is a past-only QUANTILE (deterministic, Jaccard=1.0 "
          "across seeds) — this bootstrap proxy speaks to a magnitude-MODEL; the quantile rule is even "
          "more stable. Seed-stability of selection is NOT the binding constraint (see b).")

    # ---------------------------------------------------------------------------
    # (b) INCREMENTAL test: rows ONLY the magnitude gate selects (B and not A). Are they tradeable?
    # ---------------------------------------------------------------------------
    def past_only_q(x, q):
        thr = np.full(len(x), np.nan)
        ri = np.arange(len(x))
        for lo, hi in bounds:
            tm = (ot_days >= lo) & (ot_days < hi)
            if tm.sum() == 0:
                continue
            cut = int(ri[tm].min()) - N_LABEL
            if cut < SMA_WIN + ATR_WIN:
                continue
            past = x[:cut]
            past = past[np.isfinite(past)]
            if len(past) >= 50:
                thr[ri[tm]] = float(np.quantile(past, q))
        return thr

    thr_str = past_only_q(strength, 0.40)
    thr_mag = past_only_q(vol_rank, 0.50)
    fire_A = base & np.isfinite(thr_str) & (strength >= thr_str)
    fire_B = base & np.isfinite(thr_mag) & (vol_rank >= thr_mag)
    only_B = fire_B & ~fire_A     # magnitude selects, strength does NOT
    only_A = fire_A & ~fire_B
    both = fire_A & fire_B

    def book_stab(fire):
        sh = []
        for lo, hi in bounds:
            m = (ot_days >= lo) & (ot_days < hi) & fire & np.isfinite(pnl)
            arr = pnl[m]
            sh.append(ann_sharpe(arr, tpy) if int(np.isfinite(arr).sum()) >= MIN_SUB_TRADES else np.nan)
        s = np.array(sh, float)
        valid = s[np.isfinite(s)]
        rec = [v for v in reversed(s) if np.isfinite(v)]
        allt = pnl[fire & np.isfinite(pnl)]
        return dict(full=ann_sharpe(allt, tpy), frac_pos=float(np.mean(valid > 0)) if len(valid) else np.nan,
                    recent3=float(np.mean(rec[:3])) if len(rec) >= 3 else np.nan,
                    trades=int(len(allt)), wr=float(np.mean(allt > 0)) if len(allt) else np.nan,
                    mret=float(np.mean(allt) * 100) if len(allt) else np.nan, per_sub=s)

    print("\n" + "=" * 120)
    print("(b) INCREMENTAL — what does the magnitude gate ADD over the strength gate? (book stability)")
    print(f"  {'subset':24s} {'full':>8s} {'frac_pos':>9s} {'recent3':>8s} {'trades':>7s} {'WR':>6s} {'mret%':>7s}")
    rows = []
    for name, fire in [("only_A (strength only)", only_A), ("only_B (magnitude only)", only_B),
                       ("both (A & B)", both)]:
        b = book_stab(fire)
        print(f"  {name:24s} {b['full']:+8.3f} {b['frac_pos']:9.3f} {b['recent3']:+8.3f} "
              f"{b['trades']:7d} {b['wr']:6.3f} {b['mret']:+7.3f}")
        rec = dict(subset=name, full=round(b['full'], 4), frac_pos=round(b['frac_pos'], 3),
                   recent3=round(b['recent3'], 3), trades=b['trades'], wr=round(b['wr'], 4),
                   mret_pct=round(b['mret'], 4))
        for i, lab in enumerate(sub_labels):
            rec[f"sharpe_{lab}"] = round(float(b['per_sub'][i]), 3) if np.isfinite(b['per_sub'][i]) else np.nan
        rows.append(rec)
    rows.append(dict(subset="jaccard_magnitude_selector", full=round(j_mag, 4)))
    rows.append(dict(subset="jaccard_direction_selector", full=round(j_dir, 4)))
    pd.DataFrame(rows).to_csv(OUTDIR / "seed_stability_magnitude.csv", index=False)
    print(f"\nWrote: {OUTDIR / 'seed_stability_magnitude.csv'}")

    print("\n" + "=" * 120)
    print("INTERPRETATION:")
    onlyB = book_stab(only_B)
    print(f"  only-B (rows magnitude adds over strength): recent3={onlyB['recent3']:+.3f}, "
          f"full={onlyB['full']:+.3f}, WR={onlyB['wr']:.3f}.")
    print("  If only-B recent3 <= 0, the magnitude gate adds NO tradeable, recent-stable rows beyond")
    print("  the strength gate -> magnitude does not rescue OOS robustness (the binding constraint is")
    print("  the deterministic DIRECTION, which magnitude selection cannot improve in the recent regime).")


if __name__ == "__main__":
    main()
