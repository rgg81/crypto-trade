"""CARRY ENHANCEMENT — EXPLORATION: REGIME-condition the short leg (the squeeze is alt-rally beta).

DIAGNOSIS (carry_enh_squeeze + carry_enh_beta, IS-only):
  - Short-leg name selection is UNIMPROVABLE: momentum/funding-z/taker guards WORSEN short price;
    wider short and inverse-vol worsen it too; a static index hedge barely moves it. The funding
    income (+94% short) and price loss (-54% short) are TWO SIDES OF THE SAME crowded-long trade.
  - But the worst short-price candles cluster in BROAD ALT-RALLY windows. So the one lever the data
    supports is TIMING the short gross by a PAST-ONLY market-breadth regime, not picking names.

ENHANCEMENT (one orthogonal change; long leg untouched):
  J. ALT-RALLY BRAKE — compute a past-only cross-sectional BREADTH signal: the fraction of eligible
     coins whose trailing N-candle return is positive (an alt-rally thermometer ending at close[t]).
     When breadth is in a hot regime (> threshold), SCALE DOWN the short leg by a factor s in (0,1)
     for the next candle (keep the long leg full). When cool, run the full symmetric book. The
     breadth signal and its threshold are chosen IS-ONLY. Tests: does down-weighting the short
     during broad rallies cut the squeeze drag without sacrificing the funding income?

  K. CONTROL — random/sign-shuffled brake (brake fires on a coin-flip with the same average duty
     cycle) to confirm any J lift is REGIME skill, not just "less short on average" (null #5).

Everything past-only (<= close[t]); fills open[t+1]; real funding; 0.07%/side cost. IS-ONLY.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis")
import broad_carry as bc  # noqa: E402
import carry_enh_common as ce  # noqa: E402
import pair_engine as pe  # noqa: E402


def breadth_signal(pan: dict, elig: pd.DataFrame, win: int = 9) -> pd.Series:
    """Past-only alt-rally thermometer: fraction of ELIGIBLE coins with positive trailing-win return
    (close[t]/close[t-win]-1 > 0), per row. High = broad rally = short-squeeze regime."""
    close = pan["close"]
    tret = close / close.shift(win) - 1.0
    up = (tret > 0).where(elig)
    return up.sum(axis=1) / elig.sum(axis=1).replace(0, np.nan)


def build_braked(coins: dict, pan: dict, brake: pd.Series, short_scale: float
                 ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Baseline book, but on rows where brake==True multiply the SHORT leg weights by short_scale
    (long leg unchanged). Past-only brake (decided at close[t], applied to the t+1 hold)."""
    ftrail, ret, fund_earn, elig = ce.base_eligibility(pan, ce.M_FUND, ce.MIN_HISTORY)
    opens = pan["open"]
    sc_np = ftrail.to_numpy(dtype=float)
    el_np = (elig & ftrail.notna()).to_numpy()
    ret_np = ret.to_numpy(dtype=float)
    fe_np = fund_earn.to_numpy(dtype=float)
    # brake is datetime-indexed; align positionally to the ms-indexed ftrail rows (same order/len)
    brake_dt = pd.Series(brake.to_numpy(), index=pd.to_datetime(opens.index, unit="ms"))
    brake_np = brake_dt.fillna(False).to_numpy().astype(bool)
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
        sscale = short_scale if brake_np[i] else 1.0
        w[i, shorts] = -sscale / k
        ls[i, longs] = 1.0
        ls[i, shorts] = -1.0
    # reuse the beta module's _finish for the decomposition
    import carry_enh_beta as cb
    return cb._finish(w, ls, ret_np, fe_np, opens)


def main() -> None:
    coins = bc.load_universe()
    pan = ce.panels(coins)
    _, _, _, elig = ce.base_eligibility(pan, ce.M_FUND, ce.MIN_HISTORY)
    print(f"CARRY ALT-RALLY-BRAKE ENHANCEMENT (realistic engine, {len(coins)} coins). IS-ONLY.\n")

    rows = []
    b_book, b_w = ce.build_enh(coins, pan=pan)
    rows.append(ce.is_report("BASELINE (no brake)", b_book, b_w))
    ce.print_report(rows[-1])
    print()

    # J. alt-rally brake — IS-only grid over (breadth window, hot threshold, short scale)
    best = None
    for win in [9, 21]:
        breadth = breadth_signal(pan, elig, win=win)
        # threshold from IS breadth distribution ONLY (no OOS leak)
        bidx = pd.to_datetime(pan["open"].index, unit="ms")
        breadth.index = bidx
        is_b = breadth[breadth.index < pe.OOS_CUTOFF]
        for q in [0.70, 0.80, 0.90]:
            thr = is_b.quantile(q)
            brake = breadth > thr
            duty = float(brake[brake.index < pe.OOS_CUTOFF].mean())
            for ss in [0.0, 0.5]:
                book, w = build_braked(coins, pan, brake, ss)
                r = ce.is_report(f"J. brake win={win} q{int(q*100)} scale={ss} "
                                 f"(duty={duty:.0%})", book, w)
                rows.append(r)
                ce.print_report(r)
                print()
                if best is None or r["is_net_sh"] > best[0]:
                    best = (r["is_net_sh"], win, q, ss, thr, duty)

    # K. null control — random brake matched to the best J duty cycle (same avg short reduction)
    if best is not None:
        _, win, q, ss, thr, duty = best
        rng = np.random.default_rng(0)
        bidx = pd.to_datetime(pan["open"].index, unit="ms")
        rand_brake = pd.Series(rng.random(len(bidx)) < duty, index=bidx)
        book, w = build_braked(coins, pan, rand_brake, ss)
        r = ce.is_report(f"K. NULL random brake duty={duty:.0%} scale={ss}", book, w)
        rows.append(r)
        ce.print_report(r)
        print()

    df = pd.DataFrame(rows).set_index("label").sort_values("is_net_sh", ascending=False)
    print("=== IS-ONLY RANKING (select on IS; OOS revealed at CONFIRMATION) ===")
    show = df[["is_net_sh", "is_net_total", "is_maxdd", "is_short_price", "is_fund_sh",
               "is_turnover"]].copy()
    show.columns = ["IS_net_Sh", "IS_net_%", "IS_maxDD", "IS_short_px", "IS_fund_Sh", "turnover"]
    for c in ["IS_net_%", "IS_maxDD", "IS_short_px"]:
        show[c] *= 100
    with pd.option_context("display.width", 160, "display.float_format", lambda v: f"{v:+.2f}"):
        print(show.to_string())
    df.to_csv("analysis/carry_enh_regime_results.csv")
    print("\n  wrote analysis/carry_enh_regime_results.csv")


if __name__ == "__main__":
    main()
