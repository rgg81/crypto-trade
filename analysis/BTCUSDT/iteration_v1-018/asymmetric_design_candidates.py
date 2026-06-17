"""IS-ONLY test of asymmetric design candidates vs the symmetric trend-state book — iter-v1/018 (BTCUSDT).

CONTEXT (from asymmetry_subperiod_decomposition.py, IS-only):
  - LONG leg : full +0.98, frac_pos 0.73, WR 54%, mret +2.39%/trade  -> the IS money-maker, broadly
               stable across sub-periods, BUT most-recent IS sub-period RECENT = -0.74 (one weak window).
  - SHORT leg: full -0.58, frac_pos 0.27, WR 43%, mret -1.39%/trade -> a NET LOSER across IS, positive
               in only 3/11 sub-periods, BUT most-recent IS sub-period RECENT = +3.16.
  => The OOS observation ("shorts generalize, longs don't") is the OPPOSITE of the IS full-period
     ranking. The short leg's apparent strength is concentrated in the SINGLE most-recent IS window.

This raises the precise non-cheating question: is there ANY asymmetric framing that is IS-SUB-PERIOD
STABLE (not just strong in one window)? We test the three task candidates + one crypto-native variant,
IS-only, and report per-sub-period stability + RECENT for each. We DO NOT use the OOS at all; the
calibration of every threshold below is on IS sub-period behaviour only.

Candidates (all built on the same SMA200 trend-state + 14d let-run + honest cost machinery):
  C0  SYMMETRIC          : iter-016 BOOK2 (anchor) — long above SMA200, short below.
  Ca  ASYM-THRESHOLD     : require STRONGER confirmation to go LONG than SHORT. Long only when
                            close_prev > SMA200*(1+band) AND 7-candle momentum > 0; short when
                            close_prev < SMA200 (unchanged). Bands swept on IS sub-period stability.
  Cb  SHORT-AND-FLAT     : trade trend-state SHORTS; stay FLAT above SMA200 (no long). Tests whether
                            dropping longs is IS-justified or just fits the OOS correction.
  Cc  LONG-AND-FLAT      : the MIRROR control — trade trend-state LONGS; stay FLAT below SMA200 (no
                            short). If Cc dominates Cb on IS sub-period stability, the SHORT-favoring
                            asymmetry is an OOS artifact and the IS-honest asymmetry is the OPPOSITE.
  Cd  TREND-STRENGTH-GATE: crypto-native — size/trade by trend STRENGTH (distance from SMA200 in ATR
                            units), symmetric in DIRECTION but conditioning on regime conviction.
                            Tests whether the instability is a STRENGTH-regime effect, not a side effect.

OOS-VIGILANCE (HARD): strict `open_time < OOS_CUTOFF_MS` filter + leak-guard assert BEFORE any forward
quantity; forward N-return AFTER the filter; SMA/ATR/momentum `.shift(1)` past-only; OOS never read.
Every band/threshold is chosen by IS sub-period stability ONLY. `src/` + runner + OOS UNTOUCHED.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-018/asymmetric_design_candidates.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24
SYMBOL = "BTCUSDT"
PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-018"

N_LABEL = 42
BARS_PER_YEAR = 365.0 * 3.0
SUBPERIOD_DAYS = 182.5
MIN_SUB_TRADES = 8
SMA_WIN = 200
RT_COST = 0.14
MOM_WIN = 21        # 7d momentum lookback for the asym-long confirmation (past-only)
ATR_WIN = 14


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


def stability(pnl, fire, ot_days, bounds, tpy):
    sh = []
    for lo, hi in bounds:
        m = (ot_days >= lo) & (ot_days < hi) & fire & np.isfinite(pnl)
        arr = pnl[m]
        sh.append(ann_sharpe(arr, tpy) if len(arr) >= MIN_SUB_TRADES else np.nan)
    s = np.array(sh, float)
    valid = s[np.isfinite(s)]
    recent = next((v for v in reversed(s) if np.isfinite(v)), np.nan)
    allt = pnl[fire & np.isfinite(pnl)]
    # recent-3 average: robustness of the OOS-fingerprint beyond a single window
    recent3 = [v for v in reversed(s) if np.isfinite(v)][:3]
    return dict(
        per_sub=[round(float(x), 3) if np.isfinite(x) else np.nan for x in s],
        full=round(ann_sharpe(allt, tpy), 4) if len(allt) else np.nan,
        frac_pos=round(float(np.mean(valid > 0)), 3) if len(valid) else np.nan,
        dispersion=round(float(np.std(valid, ddof=1)), 4) if len(valid) > 1 else np.nan,
        worst=round(float(np.min(valid)), 4) if len(valid) else np.nan,
        recent=round(float(recent), 4) if np.isfinite(recent) else np.nan,
        recent3=round(float(np.mean(recent3)), 4) if recent3 else np.nan,
        n_scored=int(len(valid)),
        n_trades=int(len(allt)),
        win_rate=round(float(np.mean(allt > 0)), 4) if len(allt) else np.nan,
        mean_ret_pct=round(float(np.mean(allt) * 100.0), 4) if len(allt) else np.nan,
    )


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
    tpy = BARS_PER_YEAR / N_LABEL
    bounds = subperiod_bounds(ot_days)
    sub_labels = [str(pd.to_datetime(lo * 86400_000, unit="ms").date()) for lo, _ in bounds]

    # past-only primitives
    cp = pd.Series(close).shift(1).to_numpy()
    sma = pd.Series(close).rolling(SMA_WIN).mean().shift(1).to_numpy()
    mom = (pd.Series(close).shift(1) / pd.Series(close).shift(1 + MOM_WIN) - 1.0).to_numpy()  # 7d mom, past-only
    # past-only ATR (Wilder-ish simple): mean true range over ATR_WIN, shifted
    tr = np.maximum(high - low,
                    np.maximum(np.abs(high - pd.Series(close).shift(1).to_numpy()),
                               np.abs(low - pd.Series(close).shift(1).to_numpy())))
    atr = pd.Series(tr).rolling(ATR_WIN).mean().shift(1).to_numpy()
    dist_atr = (cp - sma) / np.where(atr > 0, atr, np.nan)  # signed trend strength in ATR units, past-only

    base = np.isfinite(y) & np.isfinite(sma) & np.isfinite(cp)

    def net(direction):
        return direction * y - (RT_COST / 100.0)

    # C0 symmetric
    dir0 = np.where(cp > sma, 1.0, -1.0)
    pnl0 = net(dir0)
    c0 = stability(pnl0, base, ot_days, bounds, tpy)

    # Ca asym-threshold: long needs close>SMA*(1+band) AND mom>0; short = close<SMA (full short)
    #   bands chosen by IS sub-period stability sweep below.
    band_grid = [0.00, 0.02, 0.04, 0.06]
    ca_variants = {}
    for band in band_grid:
        long_ok = (cp > sma * (1.0 + band)) & (mom > 0)
        dir_a = np.where(long_ok, 1.0, np.where(cp < sma, -1.0, 0.0))  # 0 = flat (between bands / mom<0)
        fire_a = base & (dir_a != 0) & np.isfinite(mom)
        ca_variants[band] = stability(net(dir_a), fire_a, ot_days, bounds, tpy)

    # Cb short-and-flat: short below SMA, FLAT above (no long)
    dir_b = np.where(cp < sma, -1.0, 0.0)
    fire_b = base & (dir_b != 0)
    cb = stability(net(dir_b), fire_b, ot_days, bounds, tpy)

    # Cc long-and-flat (mirror control): long above SMA, FLAT below (no short)
    dir_c = np.where(cp > sma, 1.0, 0.0)
    fire_c = base & (dir_c != 0)
    cc = stability(net(dir_c), fire_c, ot_days, bounds, tpy)

    # Cd trend-strength gate: symmetric direction but only trade when |dist_atr| >= past-only median
    #   (strong-trend regime). Tests whether weak-trend rows are the instability source.
    thr = np.full(len(df), np.nan)
    row_idx = np.arange(len(df))
    for lo, hi in bounds:
        tm = (ot_days >= lo) & (ot_days < hi)
        if tm.sum() == 0:
            continue
        first_i = int(row_idx[tm].min())
        cut = first_i - N_LABEL
        if cut < SMA_WIN + ATR_WIN:
            continue
        past = np.abs(dist_atr[:cut])
        past = past[np.isfinite(past)]
        if len(past) < 50:
            continue
        thr[row_idx[tm]] = float(np.quantile(past, 0.50))
    strong = np.isfinite(dist_atr) & np.isfinite(thr) & (np.abs(dist_atr) >= thr)
    dir_d = np.where(cp > sma, 1.0, -1.0)
    fire_d = base & strong
    cd = stability(net(dir_d), fire_d, ot_days, bounds, tpy)

    # ---- report ----
    print(f"IS rows {len(df)}  sub-periods {len(bounds)}  N={N_LABEL}(14d)  SMA{SMA_WIN}  "
          f"RT={RT_COST}%  MOM_WIN={MOM_WIN}  ATR_WIN={ATR_WIN}")
    print("=" * 124)

    def show(name, b):
        print(f"{name:26s} {b['full']!s:>8} {b['frac_pos']!s:>5} {b['dispersion']!s:>7} "
              f"{b['worst']!s:>8} {b['recent']!s:>8} {b['recent3']!s:>8} {b['n_trades']!s:>7} "
              f"{b['win_rate']!s:>6} {b['mean_ret_pct']!s:>7}")

    print(f"{'candidate':26s} {'full':>8s} {'fpos':>5s} {'disp':>7s} {'worst':>8s} "
          f"{'RECENT':>8s} {'RECENT3':>8s} {'trades':>7s} {'WR':>6s} {'mret%':>7s}")
    show("C0_symmetric", c0)
    for band in band_grid:
        show(f"Ca_asymThr_band{band:.2f}", ca_variants[band])
    show("Cb_short_and_flat", cb)
    show("Cc_long_and_flat", cc)
    show("Cd_trendStrength_gate", cd)

    all_books = [("C0_symmetric", c0), ("Cb_short_and_flat", cb), ("Cc_long_and_flat", cc),
                 ("Cd_trendStrength_gate", cd)] + \
                [(f"Ca_asymThr_band{b:.2f}", ca_variants[b]) for b in band_grid]

    print("\n" + "=" * 124)
    print("PER-SUB-PERIOD NET ANNUALIZED SHARPE  (last col = most-recent IS sub-period):")
    print("  " + f"{'candidate':26s} " + " ".join(f"{lab[2:7]:>7s}" for lab in sub_labels))
    for name, b in all_books:
        cells = [f"{v:+7.2f}" if (v is not None and np.isfinite(v)) else f"{'·':>7s}"
                 for v in b["per_sub"]]
        print(f"  {name:26s} " + " ".join(cells))

    # persist
    out = []
    for name, b in all_books:
        rec = dict(candidate=name, **{k: v for k, v in b.items() if k != "per_sub"})
        for i, lab in enumerate(sub_labels):
            rec[f"sharpe_{lab}"] = b["per_sub"][i]
        out.append(rec)
    pd.DataFrame(out).to_csv(OUTDIR / "asymmetric_design_candidates.csv", index=False)
    print(f"\nWrote: {OUTDIR / 'asymmetric_design_candidates.csv'}")

    # ---- automatic verdict ----
    print("\n" + "=" * 124)
    print("DESIGN VERDICT (IS-only). A candidate is IS-SUB-PERIOD-STABLE if frac_pos>=0.6 AND "
          "recent3>0 AND full>C0.full.")
    def stable(b):
        return (np.isfinite(b['frac_pos']) and b['frac_pos'] >= 0.6
                and np.isfinite(b['recent3']) and b['recent3'] > 0
                and np.isfinite(b['full']) and b['full'] > c0['full'])
    for name, b in all_books:
        verdict = "STABLE & beats C0" if stable(b) else "not better than C0"
        print(f"  {name:26s} full={b['full']:>7}  frac_pos={b['frac_pos']}  "
              f"recent3={b['recent3']}  -> {verdict}")
    print("\n  KEY CONTRAST  Cb (short-and-flat) vs Cc (long-and-flat):")
    print(f"    Cb full={cb['full']} frac_pos={cb['frac_pos']} recent3={cb['recent3']} WR={cb['win_rate']}")
    print(f"    Cc full={cc['full']} frac_pos={cc['frac_pos']} recent3={cc['recent3']} WR={cc['win_rate']}")
    if (np.isfinite(cc['full']) and np.isfinite(cb['full']) and cc['full'] > cb['full']
            and cc['frac_pos'] >= cb['frac_pos']):
        print("    => On IS, LONG-and-flat DOMINATES short-and-flat. The SHORT-favoring asymmetry is "
              "an OOS artifact, NOT IS-stable. Dropping longs forfeits the IS money-maker.")
    else:
        print("    => short-and-flat competitive/superior on IS -> short-favoring asymmetry has IS support.")


if __name__ == "__main__":
    main()
