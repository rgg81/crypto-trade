"""CARRY ENHANCEMENT — EXPLORATION: attack the SHORT-LEG squeeze drag (IS-ONLY).

DIAGNOSIS (analysis/carry_enh_common leg decomposition, IS 2020-03 .. 2025-03):
  - LONG  leg price PnL = +309% IS  (hero: longing low/negative-funding crowded-shorts grinds up)
  - SHORT leg price PnL =  -53% IS  (the drag: shorting crowded-long high-funding coins -> they
    squeeze UP). Funding income is huge on both legs; the NET is dragged by this short-leg squeeze.

So the highest-value, crypto-native enhancements improve the SHORT-leg SELECTION or hedge its
squeeze risk. We hold the LONG leg fixed (it works) and test orthogonal short-leg ideas, scored
IS-ONLY (gauntlet: never select on OOS). Every signal is past-only (<= close[t]).

ENHANCEMENTS (each ONE orthogonal change vs the verified baseline; long leg always untouched):

  A. FUNDING-Z RANK — rank short candidates by funding *z-score* (funding elevated vs the coin's own
     90-candle history) instead of raw level. Hypothesis: an ACUTE funding spike (high z) is the
     short-squeeze precursor; persistent-but-not-spiking crowding is safer to short. (rank axis)

  B. FUNDING PERSISTENCE RANK — rank by trailing funding * fraction-of-window-same-sign. Hypothesis:
     STABLE durable crowding (persistent positive funding) is structural and grinds; a transient
     funding blip is noise/squeeze-prone. Reward persistence. (rank axis)

  C. SQUEEZE-MOMENTUM GUARD — drop from the SHORT pool any coin already running UP hard over the
     trailing ~3d (top-quantile recent momentum). Crypto-native "don't short a coin mid-squeeze".
     (short-leg gate axis)

  D. TAKER-IMBALANCE GUARD — drop from the SHORT pool coins with the most extreme trailing taker-BUY
     dominance (aggressive buyers piling in = late crowded longs = squeeze fuel). Broad-universe
     positioning proxy (taker_buy_quote/quote_volume, available for every coin). (short-leg gate)

  E. SQUEEZE-MOMENTUM SOFT RE-RANK — within the top-FRAC short pool, keep only the safest 60% by
     LOWEST recent momentum (soft version of C; preserves trade count better). (short-leg re-rank)

Each is scored IS-only with the funding/price leg decomposition. CONFIRMATION reveals OOS.
"""

from __future__ import annotations

import sys

import pandas as pd

sys.path.insert(0, "analysis")
import broad_carry as bc  # noqa: E402
import carry_enh_common as ce  # noqa: E402


def pctl_mask(signal: pd.DataFrame, q: float, elig: pd.DataFrame) -> pd.DataFrame:
    """Per-row boolean: True where signal is in the top-q quantile AMONG eligible coins (past-only
    signal, cross-sectional quantile computed per row -> no look-ahead, no global stat)."""
    s = signal.where(elig)
    thr = s.quantile(q, axis=1)
    return s.ge(thr, axis=0).fillna(False)


def main() -> None:
    coins = bc.load_universe()
    pan = ce.panels(coins)
    print(f"CARRY SHORT-LEG SQUEEZE ENHANCEMENTS (realistic engine, {len(coins)} coins, "
          f"M={ce.M_FUND}, FRAC={ce.FRAC}, min_history={ce.MIN_HISTORY})")
    print("  ALL numbers IS-ONLY (2020 .. 2025-03-24). OOS revealed only at CONFIRMATION.\n")

    # eligibility panel (for cross-sectional quantile masks) — must match build_enh's elig exactly
    _, _, _, elig = ce.base_eligibility(pan, ce.M_FUND, ce.MIN_HISTORY)

    # ---- BASELINE (verified == broad_carry) ----
    b_book, b_w = ce.build_enh(coins, pan=pan)
    rb = ce.is_report("BASELINE (rank=raw funding)", b_book, b_w)
    ce.print_report(rb)
    print()

    rows = [rb]

    # ---- A. funding-Z rank ----
    fz = ce.signal_funding_z(pan, m_fund=ce.M_FUND, z_win=90)
    a_book, a_w = ce.build_enh(coins, pan=pan, rank_signal=fz)
    rows.append(ce.is_report("A. funding-Z rank (z_win=90)", a_book, a_w))
    ce.print_report(rows[-1])
    print()

    # ---- B. funding persistence rank ----
    fp = ce.signal_funding_persistence(pan, m_fund=ce.M_FUND, win=90)
    b2_book, b2_w = ce.build_enh(coins, pan=pan, rank_signal=fp)
    rows.append(ce.is_report("B. funding-persistence rank (win=90)", b2_book, b2_w))
    ce.print_report(rows[-1])
    print()

    # ---- C. squeeze-momentum HARD guard (drop short candidates in top-q recent momentum) ----
    for win, q in [(9, 0.80), (9, 0.90), (3, 0.90)]:
        mom = ce.signal_squeeze_momentum(pan, win=win)
        guard = pctl_mask(mom, q, elig)
        c_book, c_w = ce.build_enh(coins, pan=pan, short_guard=guard)
        rows.append(ce.is_report(f"C. mom-guard win={win} drop>q{int(q*100)}", c_book, c_w))
        ce.print_report(rows[-1])
        print()

    # ---- D. taker-imbalance guard (drop short candidates in top-q taker-buy dominance) ----
    for win, q in [(9, 0.80), (9, 0.90)]:
        tk = ce.signal_taker_imbalance(pan, win=win)
        guard = pctl_mask(tk, q, elig)
        d_book, d_w = ce.build_enh(coins, pan=pan, short_guard=guard)
        rows.append(ce.is_report(f"D. taker-guard win={win} drop>q{int(q*100)}", d_book, d_w))
        ce.print_report(rows[-1])
        print()

    # ---- E. squeeze-momentum SOFT re-rank (keep safest keep_frac by low momentum) ----
    for keep in [0.6, 0.75]:
        mom = ce.signal_squeeze_momentum(pan, win=9)
        e_book, e_w = ce.build_enh(coins, pan=pan, short_demote_score=mom, short_keep_frac=keep)
        rows.append(ce.is_report(f"E. mom soft re-rank keep={keep}", e_book, e_w))
        ce.print_report(rows[-1])
        print()

    # ---- summary table sorted by IS net Sharpe (IS-only ranking is the gauntlet rule) ----
    df = pd.DataFrame(rows).set_index("label")
    df = df.sort_values("is_net_sh", ascending=False)
    print("=== IS-ONLY RANKING (gauntlet: select on IS, reveal OOS only at CONFIRMATION) ===")
    show = df[["is_net_sh", "is_net_total", "is_maxdd", "is_short_price", "is_fund_t",
               "is_turnover"]].copy()
    show.columns = ["IS_net_Sh", "IS_net_%", "IS_maxDD", "IS_short_price", "fund_t", "turnover"]
    show["IS_net_%"] *= 100
    show["IS_maxDD"] *= 100
    show["IS_short_price"] *= 100
    with pd.option_context("display.width", 140, "display.float_format", lambda v: f"{v:+.2f}"):
        print(show.to_string())
    df.to_csv("analysis/carry_enh_squeeze_results.csv")
    print("\n  wrote analysis/carry_enh_squeeze_results.csv")


if __name__ == "__main__":
    main()
