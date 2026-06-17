"""IS-ONLY: is the trend-STRENGTH gate's benefit ASYMMETRIC by side? — iter-v1/018 (BTCUSDT).

asymmetric_design_candidates.py found:
  - the SHORT-favoring asymmetry (the OOS observation) has NO IS support: short-and-flat loses on IS
    (full -0.58, frac_pos 0.27, recent3 -0.70); long-and-flat dominates (full +0.98). The OOS "shorts
    generalize" is an OOS artifact, NOT an IS-stable edge.
  - BUT a crypto-native CONVICTION filter (Cd: trade only when |close-SMA200| in ATR units >= past-only
    median = strong-trend regime) is the best IS candidate: full +1.21, frac_pos 0.70, recent3 +2.09,
    WR 56%, mret +2.90%/trade, dispersion 2.33 (< either bare leg).

This script asks the genuinely-asymmetric, IS-only question the iteration is about:
   Does the strength gate help the LONG leg and the SHORT leg DIFFERENTLY? i.e. is the IS-stable
   improvement an ASYMMETRIC (side-differentiated) mechanism, or symmetric?
   And: is there a strength*side interaction that is IS-sub-period stable AND beats the symmetric
   strength gate?

We decompose Cd into LONG-strong / SHORT-strong / and test asymmetric strength THRESHOLDS by side
(a stricter conviction bar on one side than the other), all calibrated on IS sub-period stability only.

We also sanity-check Cd's RECENT robustness: recent-1, recent-2, recent-3 averages, and the count of
positive sub-periods, to confirm it is not a single-window artifact (the trap that killed the
short-favoring story).

OOS-VIGILANCE (HARD): strict IS filter + leak-guard assert BEFORE forward quantities; `.shift(1)`
past-only SMA/ATR; per-sub-period strength threshold trained on PAST rows only (purged by N_LABEL);
OOS never read. `src/` + runner + OOS UNTOUCHED. All thresholds chosen on IS sub-period stability only.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-018/strength_gate_by_side.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000
SYMBOL = "BTCUSDT"
PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-018"

N_LABEL = 42
BARS_PER_YEAR = 365.0 * 3.0
SUBPERIOD_DAYS = 182.5
MIN_SUB_TRADES = 8
SMA_WIN = 200
ATR_WIN = 14
RT_COST = 0.14


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
    recent_list = [v for v in reversed(s) if np.isfinite(v)]
    allt = pnl[fire & np.isfinite(pnl)]
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
        n_trades=int(len(allt)),
        win_rate=round(float(np.mean(allt > 0)), 4) if len(allt) else np.nan,
        mean_ret_pct=round(float(np.mean(allt) * 100.0), 4) if len(allt) else np.nan,
    )


def past_only_strength_threshold(absdist, ot_days, bounds, q):
    """Per-sub-period |dist_atr| q-quantile from PAST rows only (purged by N_LABEL)."""
    thr = np.full(len(absdist), np.nan)
    row_idx = np.arange(len(absdist))
    for lo, hi in bounds:
        tm = (ot_days >= lo) & (ot_days < hi)
        if tm.sum() == 0:
            continue
        cut = int(row_idx[tm].min()) - N_LABEL
        if cut < SMA_WIN + ATR_WIN:
            continue
        past = absdist[:cut]
        past = past[np.isfinite(past)]
        if len(past) < 50:
            continue
        thr[row_idx[tm]] = float(np.quantile(past, q))
    return thr


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

    cp = pd.Series(close).shift(1).to_numpy()
    sma = pd.Series(close).rolling(SMA_WIN).mean().shift(1).to_numpy()
    tr = np.maximum(high - low,
                    np.maximum(np.abs(high - cp), np.abs(low - cp)))
    atr = pd.Series(tr).rolling(ATR_WIN).mean().shift(1).to_numpy()
    dist_atr = (cp - sma) / np.where(atr > 0, atr, np.nan)  # signed trend strength, past-only
    absd = np.abs(dist_atr)

    base = np.isfinite(y) & np.isfinite(sma) & np.isfinite(cp) & np.isfinite(dist_atr)
    dir_ts = np.where(cp > sma, 1.0, -1.0)

    def net(direction):
        return direction * y - (RT_COST / 100.0)
    pnl = net(dir_ts)

    thr50 = past_only_strength_threshold(absd, ot_days, bounds, 0.50)
    strong = base & np.isfinite(thr50) & (absd >= thr50)

    is_long = dir_ts > 0
    is_short = dir_ts < 0

    books = {
        "Cd_strong_BOTH": stability(pnl, strong, ot_days, bounds, tpy),
        "Cd_strong_LONG": stability(pnl, strong & is_long, ot_days, bounds, tpy),
        "Cd_strong_SHORT": stability(pnl, strong & is_short, ot_days, bounds, tpy),
        "weak_BOTH": stability(pnl, base & np.isfinite(thr50) & (absd < thr50), ot_days, bounds, tpy),
        "weak_LONG": stability(pnl, base & np.isfinite(thr50) & (absd < thr50) & is_long, ot_days, bounds, tpy),
        "weak_SHORT": stability(pnl, base & np.isfinite(thr50) & (absd < thr50) & is_short, ot_days, bounds, tpy),
    }

    # asymmetric strength threshold: strict conviction on the WEAKER leg, lenient on the stronger.
    # The strength quantile per side is chosen by IS sub-period stability (swept below).
    thr30 = past_only_strength_threshold(absd, ot_days, bounds, 0.30)
    thr70 = past_only_strength_threshold(absd, ot_days, bounds, 0.70)
    # Variant E1: LONG needs only weak conviction (q30), SHORT needs strong conviction (q70).
    fire_e1 = base & ((is_long & (absd >= thr30)) | (is_short & (absd >= thr70)))
    # Variant E2: mirror — LONG needs strong (q70), SHORT needs weak (q30).
    fire_e2 = base & ((is_long & (absd >= thr70)) | (is_short & (absd >= thr30)))
    books["E1_long_lenient_short_strict"] = stability(pnl, fire_e1, ot_days, bounds, tpy)
    books["E2_long_strict_short_lenient"] = stability(pnl, fire_e2, ot_days, bounds, tpy)

    print(f"IS rows {len(df)}  N={N_LABEL}(14d) SMA{SMA_WIN} ATR{ATR_WIN} RT={RT_COST}%  "
          f"strong_q=0.50  long_frac(strong)={(strong&is_long).sum()/max(strong.sum(),1):.2f}")
    print("=" * 126)
    print(f"{'book':32s} {'full':>8s} {'fpos':>5s} {'disp':>7s} {'worst':>7s} "
          f"{'rec1':>6s} {'rec2':>6s} {'rec3':>6s} {'npos':>5s} {'trades':>7s} {'WR':>6s} {'mret%':>7s}")
    for name, b in books.items():
        print(f"{name:32s} {b['full']!s:>8} {b['frac_pos']!s:>5} {b['dispersion']!s:>7} "
              f"{b['worst']!s:>7} {b['recent1']!s:>6} {b['recent2']!s:>6} {b['recent3']!s:>6} "
              f"{str(b['n_pos'])+'/'+str(b['n_scored']):>5} {b['n_trades']!s:>7} "
              f"{b['win_rate']!s:>6} {b['mean_ret_pct']!s:>7}")

    print("\n" + "=" * 126)
    print("PER-SUB-PERIOD NET ANNUALIZED SHARPE  (last col = most-recent IS sub-period):")
    print("  " + f"{'book':32s} " + " ".join(f"{lab[2:7]:>7s}" for lab in sub_labels))
    for name, b in books.items():
        cells = [f"{v:+7.2f}" if (v is not None and np.isfinite(v)) else f"{'·':>7s}"
                 for v in b["per_sub"]]
        print(f"  {name:32s} " + " ".join(cells))

    out = []
    for name, b in books.items():
        rec = dict(book=name, **{k: v for k, v in b.items() if k != "per_sub"})
        for i, lab in enumerate(sub_labels):
            rec[f"sharpe_{lab}"] = b["per_sub"][i]
        out.append(rec)
    pd.DataFrame(out).to_csv(OUTDIR / "strength_gate_by_side.csv", index=False)
    print(f"\nWrote: {OUTDIR / 'strength_gate_by_side.csv'}")

    print("\n" + "=" * 126)
    print("ASYMMETRY-WITHIN-STRENGTH VERDICT (IS-only):")
    bl, bs = books["Cd_strong_LONG"], books["Cd_strong_SHORT"]
    print(f"  strong-LONG : full={bl['full']} frac_pos={bl['frac_pos']} recent3={bl['recent3']} "
          f"npos={bl['n_pos']}/{bl['n_scored']} WR={bl['win_rate']}")
    print(f"  strong-SHORT: full={bs['full']} frac_pos={bs['frac_pos']} recent3={bs['recent3']} "
          f"npos={bs['n_pos']}/{bs['n_scored']} WR={bs['win_rate']}")
    bd, e1, e2 = books["Cd_strong_BOTH"], books["E1_long_lenient_short_strict"], books["E2_long_strict_short_lenient"]
    print(f"\n  Cd_strong_BOTH (symmetric strength gate): full={bd['full']} frac_pos={bd['frac_pos']} "
          f"recent3={bd['recent3']} n_pos={bd['n_pos']}/{bd['n_scored']} trades={bd['n_trades']}")
    print(f"  E1 (long lenient / short strict): full={e1['full']} frac_pos={e1['frac_pos']} "
          f"recent3={e1['recent3']} trades={e1['n_trades']}")
    print(f"  E2 (long strict / short lenient): full={e2['full']} frac_pos={e2['frac_pos']} "
          f"recent3={e2['recent3']} trades={e2['n_trades']}")
    best = max(books.items(), key=lambda kv: (kv[1]['full'] if np.isfinite(kv[1]['full']) else -9))
    print(f"\n  Best full-IS book: {best[0]} (full={best[1]['full']}, frac_pos={best[1]['frac_pos']}, "
          f"recent3={best[1]['recent3']}, trades={best[1]['n_trades']})")


if __name__ == "__main__":
    main()
