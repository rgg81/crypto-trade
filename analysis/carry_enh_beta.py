"""CARRY ENHANCEMENT — EXPLORATION: the short-leg drag is BROAD BETA, not a name-picking problem.

DIAGNOSIS (analysis/carry_enh_squeeze + the concentration probe, IS-only):
  - Name-level squeeze-avoidance FAILS: funding-z rank, momentum guards and taker-flow guards all
    leave the short price WORSE or unchanged. The squeeze is NOT a few avoidable names.
  - The short-price loss is DIFFUSE: worst 1% of candles = only 12% of the negative short PnL; short
    price is positive 65% of months; the worst days cluster in BROAD ALT-RALLY windows (May'21,
    Jan'21, May'22 bounce). => short-leg drag is a MARKET-BETA / alt-beta exposure, not a tail.

So the right crypto-native attack is on the BOOK's net beta, not name selection. Three orthogonal
beta-level ideas, all past-only, long leg's selection untouched, scored IS-ONLY:

  F. ASYMMETRIC LEGS — short a WIDER fraction than we long (e.g. short 0.35 / long 0.25). More short
     names => the per-name squeeze is diversified and each short name's notional smaller, while we
     keep the full long-leg edge. Tests whether spreading the short reduces the beta drag.

  G. SHORT-LEG INVERSE-VOL WEIGHTING — within the short pool, weight 1/sigma (trailing 30-candle
     realized vol). The squeeze MAGNITUDE scales with a coin's vol; down-weighting the most volatile
     shorts caps each squeeze's contribution. Long leg stays equal-weight. (gross renormalized)

  H. BETA HEDGE (residual market-neutralization) — the book is constructed dollar-neutral but the
     SHORT side is higher-beta than the LONG side (hot vs cold alts), so net beta is NEGATIVE in
     alt rallies. Add a small static long-index overlay (equal-weight basket of eligible coins)
     sized to a grid of h in {0.05..0.20} of gross, to neutralize the residual short beta. Past-only
     (the overlay return uses the same next-bar-open convention). h chosen IS-only.

Every signal <= close[t]; fills open[t+1]; real funding; 0.07%/side cost. OOS at CONFIRMATION.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis")
import broad_carry as bc  # noqa: E402
import carry_enh_common as ce  # noqa: E402
import pair_engine as pe  # noqa: E402


def build_asym(coins: dict, pan: dict, long_frac: float, short_frac: float
               ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Asymmetric legs: long bottom long_frac, short top short_frac (each leg dollar-normalized so
    the book stays dollar-neutral: +1 across longs, -1 across shorts). Past-only, baseline rank."""
    ftrail, ret, fund_earn, elig = ce.base_eligibility(pan, ce.M_FUND, ce.MIN_HISTORY)
    opens = pan["open"]
    sc_np = ftrail.to_numpy(dtype=float)
    el_np = (elig & ftrail.notna()).to_numpy()
    ret_np = ret.to_numpy(dtype=float)
    fe_np = fund_earn.to_numpy(dtype=float)
    n_rows, n_cols = sc_np.shape
    w = np.zeros_like(sc_np)
    ls = np.zeros((n_rows, n_cols))
    for i in range(n_rows):
        ecols = np.where(el_np[i])[0]
        if len(ecols) < 4:
            continue
        order = ecols[np.argsort(sc_np[i, ecols])]
        kl = int(len(ecols) * long_frac)
        ks = int(len(ecols) * short_frac)
        if kl < 1 or ks < 1:
            continue
        longs, shorts = order[:kl], order[-ks:]
        w[i, longs] = 1.0 / kl
        w[i, shorts] = -1.0 / ks
        ls[i, longs] = 1.0
        ls[i, shorts] = -1.0
    return _finish(w, ls, ret_np, fe_np, opens)


def build_invvol(coins: dict, pan: dict, vol_win: int = 30
                 ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Short leg inverse-vol weighted; long leg equal-weight. Each leg dollar-normalized. Past-only:
    vol = trailing realized vol of close-to-close returns over vol_win, ending at close[t]."""
    ftrail, ret, fund_earn, elig = ce.base_eligibility(pan, ce.M_FUND, ce.MIN_HISTORY)
    opens, close = pan["open"], pan["close"]
    cret = close.pct_change()
    vol = cret.rolling(vol_win).std().shift(1)          # past-only (ends at close[t-1])
    sc_np = ftrail.to_numpy(dtype=float)
    el_np = (elig & ftrail.notna() & vol.notna() & (vol > 0)).to_numpy()
    vol_np = vol.to_numpy(dtype=float)
    ret_np = ret.to_numpy(dtype=float)
    fe_np = fund_earn.to_numpy(dtype=float)
    n_rows, n_cols = sc_np.shape
    w = np.zeros_like(sc_np)
    ls = np.zeros((n_rows, n_cols))
    for i in range(n_rows):
        ecols = np.where(el_np[i])[0]
        if len(ecols) < 4:
            continue
        order = ecols[np.argsort(sc_np[i, ecols])]
        k = int(len(ecols) * ce.FRAC)
        if k < 1:
            continue
        longs, shorts = order[:k], order[-k:]
        w[i, longs] = 1.0 / k
        iv = 1.0 / vol_np[i, shorts]
        w[i, shorts] = -iv / iv.sum()                   # inverse-vol, dollar-normalized to -1
        ls[i, longs] = 1.0
        ls[i, shorts] = -1.0
    return _finish(w, ls, ret_np, fe_np, opens)


def build_beta_hedge(coins: dict, pan: dict, h: float
                     ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Baseline book + a static long-index overlay of weight h (fraction of gross=1) spread
    equal-weight across the SAME eligible universe each row. Neutralizes residual short beta.
    Past-only; overlay earns the next-bar-open price return + its funding (longs pay funding)."""
    ftrail, ret, fund_earn, elig = ce.base_eligibility(pan, ce.M_FUND, ce.MIN_HISTORY)
    opens = pan["open"]
    sc_np = ftrail.to_numpy(dtype=float)
    el_np = (elig & ftrail.notna()).to_numpy()
    ret_np = ret.to_numpy(dtype=float)
    fe_np = fund_earn.to_numpy(dtype=float)
    n_rows, n_cols = sc_np.shape
    w = np.zeros_like(sc_np)
    ls = np.zeros((n_rows, n_cols))
    for i in range(n_rows):
        ecols = np.where(el_np[i])[0]
        if len(ecols) < 4:
            continue
        order = ecols[np.argsort(sc_np[i, ecols])]
        k = int(len(ecols) * ce.FRAC)
        if k < 1:
            continue
        longs, shorts = order[:k], order[-k:]
        w[i, longs] += 1.0 / k
        w[i, shorts] += -1.0 / k
        ls[i, longs] = 1.0
        ls[i, shorts] = -1.0
        # long-index overlay: equal-weight long across all eligible, total notional h
        w[i, ecols] += h / len(ecols)
    return _finish(w, ls, ret_np, fe_np, opens)


def _finish(w, ls, ret_np, fe_np, opens) -> tuple[pd.DataFrame, pd.DataFrame]:
    n_cols = w.shape[1]
    price = (w * np.nan_to_num(ret_np)).sum(axis=1)
    funding = -(w * np.nan_to_num(fe_np)).sum(axis=1)
    cost = pe.COST_SIDE * np.abs(w - np.vstack([np.zeros(n_cols), w[:-1]])).sum(axis=1)
    long_mask, short_mask = (ls > 0), (ls < 0)
    lp = (np.where(long_mask, w, 0) * np.nan_to_num(ret_np)).sum(axis=1)
    spx = (np.where(short_mask, w, 0) * np.nan_to_num(ret_np)).sum(axis=1)
    lf = -(np.where(long_mask, w, 0) * np.nan_to_num(fe_np)).sum(axis=1)
    sf = -(np.where(short_mask, w, 0) * np.nan_to_num(fe_np)).sum(axis=1)
    idx = pd.to_datetime(opens.index, unit="ms")
    book = pd.DataFrame(
        {"net": price + funding - cost, "price": price, "funding": funding, "cost": cost,
         "long_price": lp, "short_price": spx, "long_funding": lf, "short_funding": sf}, index=idx)
    wdf = pd.DataFrame(w, index=idx, columns=opens.columns)
    return book.dropna(subset=["net"]), wdf.loc[book.dropna(subset=["net"]).index]


def main() -> None:
    coins = bc.load_universe()
    pan = ce.panels(coins)
    print(f"CARRY BETA-LEVEL ENHANCEMENTS (realistic engine, {len(coins)} coins). IS-ONLY.\n")

    rows = []
    b_book, b_w = ce.build_enh(coins, pan=pan)
    rows.append(ce.is_report("BASELINE (sym legs, eq-weight)", b_book, b_w))
    ce.print_report(rows[-1])
    print()

    # F. asymmetric legs (wider short)
    for lf, sf in [(0.25, 0.35), (0.25, 0.40), (0.20, 0.35)]:
        book, w = build_asym(coins, pan, lf, sf)
        rows.append(ce.is_report(f"F. asym long={lf} short={sf}", book, w))
        ce.print_report(rows[-1])
        print()

    # G. short-leg inverse-vol
    for vw in [30, 60]:
        book, w = build_invvol(coins, pan, vol_win=vw)
        rows.append(ce.is_report(f"G. short inv-vol win={vw}", book, w))
        ce.print_report(rows[-1])
        print()

    # H. beta hedge overlay (grid; IS-only)
    for h in [0.05, 0.10, 0.15, 0.20]:
        book, w = build_beta_hedge(coins, pan, h)
        rows.append(ce.is_report(f"H. beta-hedge h={h}", book, w))
        ce.print_report(rows[-1])
        print()

    df = pd.DataFrame(rows).set_index("label").sort_values("is_net_sh", ascending=False)
    print("=== IS-ONLY RANKING (select on IS; OOS revealed at CONFIRMATION) ===")
    show = df[["is_net_sh", "is_net_total", "is_maxdd", "is_short_price", "is_long_price",
               "is_fund_t", "is_turnover"]].copy()
    show.columns = ["IS_net_Sh", "IS_net_%", "IS_maxDD", "IS_short_px", "IS_long_px",
                    "fund_t", "turnover"]
    for c in ["IS_net_%", "IS_maxDD", "IS_short_px", "IS_long_px"]:
        show[c] *= 100
    with pd.option_context("display.width", 160, "display.float_format", lambda v: f"{v:+.2f}"):
        print(show.to_string())
    df.to_csv("analysis/carry_enh_beta_results.csv")
    print("\n  wrote analysis/carry_enh_beta_results.csv")


if __name__ == "__main__":
    main()
