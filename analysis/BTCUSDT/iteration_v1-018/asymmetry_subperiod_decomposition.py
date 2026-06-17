"""IS-ONLY long/short asymmetry decomposition of the trend-state book — iter-v1/018 (BTCUSDT).

PURPOSE
-------
iter-016 found the stateless 200-SMA trend-state direction (long above SMA200, short below, all
past-only) is the only direction source whose MOST-RECENT IS sub-period is positive. iter-017 (K=20
CONFIRMATION) revealed the both-positive was a basin-lottery, AND diagnosed an ASYMMETRY in the OOS:
  - trend-state SHORT side partially generalizes (OOS shorts net +6.5% even at K=20);
  - trend-state LONG side does NOT generalize (OOS longs -14%, WR 21%).

That asymmetry is an OOS observation — we MAY NOT design a rule to fit it. The CREATIVE,
NON-CHEATING question this script answers, IS-ONLY:

   Does the trend-state book's LONG side and SHORT side have DIFFERENT sub-period-stability
   fingerprints WITHIN the in-sample window? If shorts are IS-sub-period-stable (sign-consistent,
   positive frac, positive RECENT) and longs are IS-sub-period-UNSTABLE, an asymmetric design is
   JUSTIFIED ON IS ALONE — independent of, and predictive of, the OOS asymmetry.

   If the long side is ALSO IS-sub-period-stable (positive RECENT, decent frac_pos), then dropping
   or de-weighting longs would FORFEIT a real IS edge and would only be fitting the OOS correction
   -> HONEST NULL, report it.

We reuse the iter-016 design-decision machinery VERBATIM (purged/embargoed walk-forward, sub-period
bounds, net-per-trade, the SMA200 trend-state rule, honest RT cost) and add a SIDE split.

Books reported, each split into FULL / LONG-only / SHORT-only:
  BOOK_SYM    = symmetric trend-state (iter-016 BOOK2): long above SMA200, short below.
We then characterise, per IS sub-period: Sharpe, win-rate, mean-ret/trade, n_trades, for the
LONG-leg and the SHORT-leg SEPARATELY, plus dispersion / frac_pos / RECENT for each leg.

OOS-VIGILANCE (HARD): strict `open_time < OOS_CUTOFF_MS` filter + leak-guard assert BEFORE any
forward quantity; forward N-return computed AFTER the filter; SMA via `.shift(1)` past-only; OOS
never read. `src/` + runner + OOS UNTOUCHED. No quantity in this script is calibrated on OOS — the
OOS asymmetry from diary-017 is the MOTIVATION, not an input.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-018/asymmetry_subperiod_decomposition.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24
SYMBOL = "BTCUSDT"
PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-018"

N_LABEL = 42                 # 14d let-winners-run horizon (campaign keeper)
BARS_PER_YEAR = 365.0 * 3.0
SUBPERIOD_DAYS = 182.5       # ~6-month IS sub-periods (iter-011/016 lens)
MIN_SUB_TRADES = 8
SMA_WIN = 200                # crypto-canonical, mid-plateau per iter-016 probe
RT_COST = 0.14               # honest round-trip cost % (0.1% fee + 0.04% slippage)


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


def leg_stability(per_trade, fire, ot_days, bounds, tpy):
    """Per-sub-period Sharpe / WR / mean-ret / count for a given firing mask."""
    sh, wr, mret, nts = [], [], [], []
    for lo, hi in bounds:
        m = (ot_days >= lo) & (ot_days < hi) & fire & np.isfinite(per_trade)
        arr = per_trade[m]
        if len(arr) >= MIN_SUB_TRADES:
            sh.append(ann_sharpe(arr, tpy))
            wr.append(float(np.mean(arr > 0)))
            mret.append(float(np.mean(arr) * 100.0))
        else:
            sh.append(np.nan)
            wr.append(np.nan)
            mret.append(np.nan)
        nts.append(int(len(arr)))
    s = np.array(sh, float)
    valid = s[np.isfinite(s)]
    recent = next((v for v in reversed(s) if np.isfinite(v)), np.nan)
    allt = per_trade[fire & np.isfinite(per_trade)]
    return dict(
        per_sub=[round(float(x), 3) if np.isfinite(x) else np.nan for x in s],
        per_sub_wr=[round(float(x), 3) if np.isfinite(x) else np.nan for x in wr],
        per_sub_mret=[round(float(x), 3) if np.isfinite(x) else np.nan for x in mret],
        per_sub_n=nts,
        full=round(ann_sharpe(allt, tpy), 4) if len(allt) else np.nan,
        frac_pos=round(float(np.mean(valid > 0)), 3) if len(valid) else np.nan,
        dispersion=round(float(np.std(valid, ddof=1)), 4) if len(valid) > 1 else np.nan,
        worst=round(float(np.min(valid)), 4) if len(valid) else np.nan,
        recent=round(float(recent), 4) if np.isfinite(recent) else np.nan,
        n_scored=int(len(valid)),
        n_trades=int(len(allt)),
        win_rate=round(float(np.mean(allt > 0)), 4) if len(allt) else np.nan,
        mean_ret_pct=round(float(np.mean(allt) * 100.0), 4) if len(allt) else np.nan,
    )


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df_full = pd.read_parquet(PARQUET)
    df = df_full[df_full["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"

    close = df["close"].to_numpy(float)
    ot_days = df["open_time"].to_numpy(float) / 86400_000.0
    y = fwd_log_return(close, N_LABEL)        # signed forward N-return, AFTER the IS filter
    tpy = BARS_PER_YEAR / N_LABEL

    bounds = subperiod_bounds(ot_days)
    sub_labels = [str(pd.to_datetime(lo * 86400_000, unit="ms").date()) for lo, _ in bounds]

    # trend-state direction (stateless, past-only): +1 long above SMA200, -1 short below.
    cp = pd.Series(close).shift(1).to_numpy()
    sma = pd.Series(close).rolling(SMA_WIN).mean().shift(1).to_numpy()
    ts_dir = np.where(np.isfinite(sma) & np.isfinite(cp),
                      np.where(cp > sma, 1.0, -1.0), np.nan)

    base = np.isfinite(y) & np.isfinite(ts_dir)

    def net_per_trade(direction: np.ndarray) -> np.ndarray:
        return direction * y - (RT_COST / 100.0)

    pnl_sym = net_per_trade(ts_dir)

    is_long = base & (ts_dir > 0)
    is_short = base & (ts_dir < 0)

    leg_full = leg_stability(pnl_sym, base, ot_days, bounds, tpy)
    leg_long = leg_stability(pnl_sym, is_long, ot_days, bounds, tpy)
    leg_short = leg_stability(pnl_sym, is_short, ot_days, bounds, tpy)

    print(f"IS rows {len(df)}  sub-periods {len(bounds)}  N={N_LABEL}(14d)  SMA{SMA_WIN}  "
          f"RT_cost={RT_COST}%  trades/yr~{tpy:.1f}")
    print(f"trend-state long candles={int(is_long.sum())}  short candles={int(is_short.sum())}  "
          f"(long frac={is_long.sum()/max(base.sum(),1):.2f})")
    print("=" * 120)

    rows = [("FULL_symmetric", leg_full), ("LONG_leg_only", leg_long), ("SHORT_leg_only", leg_short)]
    print(f"{'book':18s} {'full':>7s} {'fpos':>5s} {'disp':>7s} {'worst':>8s} "
          f"{'RECENT':>8s} {'trades':>7s} {'WR':>6s} {'mret%':>7s} {'n_scored':>8s}")
    for name, b in rows:
        print(f"{name:18s} {b['full']!s:>7} {b['frac_pos']!s:>5} {b['dispersion']!s:>7} "
              f"{b['worst']!s:>8} {b['recent']!s:>8} {b['n_trades']!s:>7} "
              f"{b['win_rate']!s:>6} {b['mean_ret_pct']!s:>7} {b['n_scored']!s:>8}")

    print("\n" + "=" * 120)
    print("PER-SUB-PERIOD NET ANNUALIZED SHARPE  (last col = most-recent IS sub-period = OOS fingerprint):")
    print("  " + f"{'leg':18s} " + " ".join(f"{lab[2:7]:>7s}" for lab in sub_labels))
    for name, b in rows:
        cells = [f"{v:+7.2f}" if (v is not None and np.isfinite(v)) else f"{'·':>7s}"
                 for v in b["per_sub"]]
        print(f"  {name:18s} " + " ".join(cells))

    print("\nPER-SUB-PERIOD WIN-RATE  (long vs short leg):")
    print("  " + f"{'leg':18s} " + " ".join(f"{lab[2:7]:>7s}" for lab in sub_labels))
    for name, b in [("LONG_leg_only", leg_long), ("SHORT_leg_only", leg_short)]:
        cells = [f"{v*100:6.1f}%" if (v is not None and np.isfinite(v)) else f"{'·':>7s}"
                 for v in b["per_sub_wr"]]
        print(f"  {name:18s} " + " ".join(cells))

    print("\nPER-SUB-PERIOD TRADE COUNT  (long vs short leg):")
    print("  " + f"{'leg':18s} " + " ".join(f"{lab[2:7]:>7s}" for lab in sub_labels))
    for name, b in [("LONG_leg_only", leg_long), ("SHORT_leg_only", leg_short)]:
        cells = [f"{n:>7d}" for n in b["per_sub_n"]]
        print(f"  {name:18s} " + " ".join(cells))

    # ---- persist ----
    out = []
    for name, b in rows:
        rec = dict(book=name, **{k: v for k, v in b.items()
                                 if k not in ("per_sub", "per_sub_wr", "per_sub_mret", "per_sub_n")})
        for i, lab in enumerate(sub_labels):
            rec[f"sharpe_{lab}"] = b["per_sub"][i]
            rec[f"wr_{lab}"] = b["per_sub_wr"][i]
            rec[f"n_{lab}"] = b["per_sub_n"][i]
        out.append(rec)
    pd.DataFrame(out).to_csv(OUTDIR / "asymmetry_subperiod_decomposition.csv", index=False)
    print(f"\nWrote: {OUTDIR / 'asymmetry_subperiod_decomposition.csv'}")

    # ---- automatic asymmetry verdict ----
    print("\n" + "=" * 120)
    print("ASYMMETRY VERDICT (IS-only — is the short leg MORE sub-period-stable than the long leg?):")
    print(f"  LONG  leg : full={leg_long['full']}  frac_pos={leg_long['frac_pos']}  "
          f"disp={leg_long['dispersion']}  RECENT={leg_long['recent']}  WR={leg_long['win_rate']}")
    print(f"  SHORT leg : full={leg_short['full']}  frac_pos={leg_short['frac_pos']}  "
          f"disp={leg_short['dispersion']}  RECENT={leg_short['recent']}  WR={leg_short['win_rate']}")
    short_stable = (np.isfinite(leg_short['recent']) and leg_short['recent'] > 0
                    and np.isfinite(leg_short['frac_pos']) and leg_short['frac_pos'] >= 0.6)
    long_unstable = (not (np.isfinite(leg_long['recent']) and leg_long['recent'] > 0
                          and np.isfinite(leg_long['frac_pos']) and leg_long['frac_pos'] >= 0.6))
    print(f"\n  short_IS_stable={short_stable}  long_IS_unstable={long_unstable}")
    if short_stable and long_unstable:
        print("  => ASYMMETRY IS IS-JUSTIFIED: short leg stable, long leg unstable -> asymmetric "
              "design warranted (NOT an OOS artifact).")
    elif short_stable and not long_unstable:
        print("  => BOTH legs IS-stable -> dropping/de-weighting longs would FORFEIT a real IS edge "
              "-> HONEST NULL (asymmetry is an OOS-only artifact).")
    else:
        print("  => short leg NOT IS-stable -> asymmetric short-favoring design has NO IS support "
              "-> HONEST NULL.")


if __name__ == "__main__":
    main()
