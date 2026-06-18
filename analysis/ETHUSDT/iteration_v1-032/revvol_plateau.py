"""iter-v1/032 (ETHUSDT) — FINAL decisive probe: high-vol-conditioned reversion plateau.

Two crypto-native signals survived the deep dive:
  - high-vol (natr>=q60) conditioned price-z fade: +0.26 (2023:+5.19 but 2024:-0.56)
  - rev_extension_z_3>=1.5 fade: +0.51 (2024:+1.50, 2025:+0.77, but 2023:-0.75; k-neighbor non-robust)
Both are crypto-mechanism-consistent: reversion snapbacks live in HIGH-VOL / liquidation regimes.
This probe asks the decisive question for a BREADTH backtest: is there a (trigger x vol-gate x N)
NEIGHBORHOOD (plateau) that is positive AND has NON-NEGATIVE 2023 AND 2024 AND 2025 (the OOS-adjacent
years that killed every other edge)? If yes -> credible breadth candidate. If no -> honest NEGATIVE,
the high-frequency ETH edge does not generalize and we recommend the fallback.

Grid: trigger in {rev_extension_z_3, price-z-vs-SMA10} x vol-gate natr>=q in {none,40,60} x
threshold k x hold N. Robustness = min Sharpe over the (k,N) neighborhood AND min yearly Sharpe
over {2022,2023,2024} (the recent IS years).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from _common import OOS_CUTOFF_MS, load_full_for_label_horizon  # noqa: E402

ROUND_TRIP_COST = 2 * (0.001 + 0.0002)
CANDLES_PER_MONTH = 91.0


def ann_sharpe(p, npy):
    p = np.asarray(p, float)
    if len(p) < 2 or p.std(ddof=1) == 0:
        return 0.0
    return float(p.mean() / p.std(ddof=1) * np.sqrt(npy))


def fwd(close, n):
    out = np.full(len(close), np.nan)
    out[: len(close) - n] = close[n:] / close[: len(close) - n] - 1.0
    return out


def nonoverlap(idx, n):
    kept, le = [], -1
    for i in idx:
        if i > le:
            kept.append(i)
            le = i + n
    return np.array(kept, int)


def run(df, mask, direction, n):
    close = df["close"].to_numpy(float)
    ot = df["open_time"].to_numpy()
    fr = fwd(close, n)
    otf = np.full(len(df), np.inf)
    otf[: len(df) - n] = ot[n:]
    hs = (ot < OOS_CUTOFF_MS) & (otf < OOS_CUTOFF_MS)
    cand = np.where(mask & hs & np.isfinite(fr) & np.isfinite(direction))[0]
    if len(cand) == 0:
        return None
    sel = nonoverlap(cand, n)
    if len(sel) < 30:
        return None
    d, raw = direction[sel], fr[sel]
    pnl = d * raw - ROUND_TRIP_COST
    assert ot[sel].max() < OOS_CUTOFF_MS and otf[sel].max() < OOS_CUTOFF_MS
    spm = (ot[sel].max() - ot[sel].min()) / (1000 * 60 * 60 * 8 * CANDLES_PER_MONTH)
    yr = pd.to_datetime(ot[sel], unit="ms").year
    ysh = {}
    for y in (2022, 2023, 2024):
        m = yr == y
        if m.sum() >= 5:
            spm_y = (ot[sel][m].max() - ot[sel][m].min()) / (1000 * 60 * 60 * 8 * CANDLES_PER_MONTH)
            ysh[y] = ann_sharpe(pnl[m], len(pnl[m]) / max(spm_y / 12.0, 1e-9))
        else:
            ysh[y] = np.nan
    g = np.abs(pnl)
    return {
        "events": len(sel),
        "sharpe": ann_sharpe(pnl, len(sel) / max(spm / 12.0, 1e-9)),
        "win": float((pnl > 0).mean()),
        "net": float(pnl.sum()) * 100,
        "top2": float(np.sort(g)[::-1][:2].sum() / g.sum()) if g.sum() > 0 else np.nan,
        "y22": ysh[2022],
        "y23": ysh[2023],
        "y24": ysh[2024],
    }


def main():
    df = load_full_for_label_horizon().sort_values("open_time").reset_index(drop=True)
    s = pd.Series(df["close"].to_numpy(float))
    log = []

    def p(x=""):
        print(x)
        log.append(str(x))

    # primitives
    sma10 = s.rolling(10).mean()
    sd10 = s.rolling(10).std(ddof=0)
    pricez = ((s - sma10) / sd10).shift(1).to_numpy()
    rev = df["rev_extension_z_3"].shift(1).to_numpy() if "rev_extension_z_3" in df else None
    hl = df["high"] - df["low"]
    hc = (df["high"] - s.shift(1)).abs()
    lc = (df["low"] - s.shift(1)).abs()
    atr14 = pd.concat([hl, hc, lc], axis=1).max(axis=1).rolling(14).mean()
    natr = (atr14 / s).shift(1).to_numpy()
    is_mask = df["open_time"].to_numpy() < OOS_CUTOFF_MS

    p("=" * 96)
    p("iter-v1/032 — FINAL: high-vol-conditioned reversion plateau search")
    p("PASS = positive Sharpe AND non-negative 2022 AND 2023 AND 2024 (OOS-adjacent recent years)")
    p("=" * 96)

    triggers = {"pricez": pricez}
    if rev is not None:
        triggers["rev_ext"] = rev

    candidates = []
    for tname, trig in triggers.items():
        for volq in (None, 0.40, 0.60):
            if volq is None:
                vg = np.ones(len(df), bool)
                vlabel = "novol"
            else:
                thr = np.nanquantile(natr[is_mask & np.isfinite(natr)], volq)
                vg = natr >= thr
                vlabel = f"natr>=q{int(volq * 100)}"
            for k in (1.0, 1.5, 2.0):
                for n in (2, 3, 4, 6):
                    mask = (np.abs(trig) >= k) & vg
                    r = run(df, mask, -np.sign(trig), n)
                    if r is None:
                        continue
                    r["cfg"] = f"{tname}|{vlabel}|k{k}|N{n}"
                    candidates.append(r)

    cdf = pd.DataFrame(candidates).sort_values("sharpe", ascending=False).reset_index(drop=True)
    cdf.to_csv(Path(__file__).parent / "revvol_plateau.csv", index=False)

    p("\nTOP 20 by IS Sharpe (events>=30, net):")
    p(
        f"  {'cfg':32s} {'ev':>5s} {'win':>5s} {'shrp':>6s} {'net%':>7s} {'top2':>6s} "
        f"{'22':>6s} {'23':>6s} {'24':>6s}"
    )
    for _, r in cdf.head(20).iterrows():
        p(
            f"  {r['cfg']:32s} {int(r['events']):5d} {r['win']:.3f} {r['sharpe']:+.3f} "
            f"{r['net']:+7.1f} {r['top2']:.4f} {r['y22']:+.2f} {r['y23']:+.2f} {r['y24']:+.2f}"
        )

    p("\nPASS set (Sharpe>0 AND y22>=-0.10 AND y23>=-0.10 AND y24>=-0.10 AND events>=164):")
    passed = cdf[
        (cdf["sharpe"] > 0)
        & (cdf["y22"] >= -0.10)
        & (cdf["y23"] >= -0.10)
        & (cdf["y24"] >= -0.10)
        & (cdf["events"] >= 164)
    ]
    if len(passed):
        for _, r in passed.iterrows():
            p(
                f"  PASS: {r['cfg']} ev={int(r['events'])} sharpe={r['sharpe']:+.3f} "
                f"win={r['win']:.3f} top2={r['top2']:.4f} 22/23/24={r['y22']:+.2f}/{r['y23']:+.2f}/{r['y24']:+.2f}"
            )
    else:
        p("  *** NONE PASS *** — no high-frequency reversion cell is positive with non-negative")
        p("  recent (2022-2024) years at breadth scale. The high-frequency ETH edge does NOT have")
        p("  a robust, OOS-adjacent-stable plateau. Honest NEGATIVE for the breadth premise.")
        # show the least-bad: max over min(y22,y23,y24) among Sharpe>0, events>=100
        sub = cdf[(cdf["sharpe"] > 0) & (cdf["events"] >= 100)].copy()
        if len(sub):
            sub["worst_recent"] = sub[["y22", "y23", "y24"]].min(axis=1)
            sub = sub.sort_values("worst_recent", ascending=False)
            p("\n  least-bad (max of min recent-year Sharpe, Sharpe>0, events>=100):")
            for _, r in sub.head(5).iterrows():
                p(
                    f"    {r['cfg']} ev={int(r['events'])} sharpe={r['sharpe']:+.3f} "
                    f"worst_recent={r['worst_recent']:+.3f} (22/23/24={r['y22']:+.2f}/{r['y23']:+.2f}/{r['y24']:+.2f})"
                )

    (Path(__file__).parent / "revvol_plateau_output.txt").write_text("\n".join(log))
    print("\n[written] revvol_plateau.csv + revvol_plateau_output.txt")


if __name__ == "__main__":
    main()
