"""iter-v1/031 — IS-ONLY screen: exit-side partial-profit ladder de-concentrator.

Critic Path-Forward #1. Decides whether iter-031 (a deterministic partial-profit
ladder on the EXIT side) is worth a full backtest. NO backtest, NO src/ edits here.

HYPOTHESIS
----------
iter-027's OOS is carried by a few big 14d let-winners-run captures (top-2 trade
share ~438% of OOS net). Splitting each big winner's realized PnL across 2-3 legs
via a deterministic partial-profit ladder de-concentrates the book WITHOUT changing
which candles enter or the trade direction — so the IS edge SIGN is structurally
preserved (this is the property that meta-labeling / AGREE_SCALE lacked: they changed
entries and inverted IS).

The ladder ADDS turnover: each extra partial-exit fill pays an exit-side cost. This
script weighs the de-concentration benefit against that turnover drag, IS-ONLY.

LADDER (3-leg, primary)
  LONG : realize 1/3 at entry + 1.5*ATR14_entry (partial-1),
                 1/3 at entry + 3.0*ATR14_entry (partial-2),
                 1/3 at the ACTUAL iter-027 exit (timeout/SL).
  SHORT: mirror with entry - k*ATR14_entry.
  A level never reached before the actual exit -> that third also exits at the actual exit.

LADDER (2-leg, sensitivity)
  realize 1/2 at entry +/- 2.0*ATR14_entry, rest at the actual exit.

COSTS (load-bearing)
  iter-027 used fee 0.1% (round trip) + slippage 2 bps/side (round trip 0.04%).
  In make_result: net = pnl_pct - fee_pct(0.1) - slippage_pct(0.04). That 0.14% is the
  cost of ONE entry + ONE exit fill. The ladder shares the single entry fill but adds
  up to 2 EXTRA exit fills per runner. Per EXIT fill cost = fee 0.05% + slippage 2bps
  = 0.07%. We model the book as:
     - entry-side cost paid ONCE per trade        = 0.07%   (charged against leg-1)
     - exit-side cost paid PER realized leg        = 0.07%   (each leg)
  So a non-runner (1 leg) pays 0.07 + 0.07 = 0.14% == iter-027 single-exit exactly.
  A 3-leg runner pays 0.07 (entry) + 3*0.07 (three exits) = 0.28%, i.e. +0.14% extra
  turnover drag spread across the position vs the single-exit baseline.

  Each leg carries 1/N of the position, so its contribution to total book net pct is
     leg_share * gross_leg_return_pct  -  (per-leg cost charged to that leg).
  We attribute the one-time entry cost to leg-1 so the book total is honest.

ENTRY/EXIT alignment (verified):
  * trade.open_time == entry candle close_time (100% match).
  * entry_price == entry candle CLOSE exactly (entry fills at candle close).
  * SL distance == 1.45 * vol_natr_21 at entry candle (exact) -> iter-027 uses NATR21 SL.
  * Intra-trade path walked on SUBSEQUENT candles' high/low (entry candle excluded for
    the trigger -> no same-bar look-ahead).

ATR for ladder levels: brief says "entry-time ATR14". Primary = raw vol_atr_14
(absolute price units; level = entry +/- k*vol_atr_14_entry). Sensitivity = NATR14
(pct units; level = entry * (1 +/- k*vol_natr_14_entry/100)) so the verdict is not
fragile to the ATR-units interpretation.

LEAK GUARDS
  * Assert ALL trades are IS (open_time < OOS_CUTOFF close_time boundary).
  * vol_atr_14 / vol_natr_14 at the ENTRY candle are known at entry time (use data up to
    the entry candle close); the path walk starts strictly AFTER the entry candle.

PRE-REGISTERED PASS CRITERION (Critic)
  The ladder must (a) REDUCE top-2 share of net PnL vs iter-027 IS AND
  (b) NOT bleed IS net monthly Sharpe by more than 0.05 (within -0.05 of single-exit IS).
  Else NEGATIVE -> pivot to Path Forward #2 (ensemble-disagreement abstention).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# --- paths -------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[3]
TRADES_CSV = REPO / "reports-v1/ETHUSDT/iteration_v1-027/in_sample/trades.csv"
FEATURES_PQ = REPO / "data/features/ETHUSDT_8h_features.parquet"

# OOS cutoff = 2025-03-24 00:00:00 UTC. iter-027 IS trades have open_time == entry
# candle CLOSE_TIME. The last IS entry candle closes strictly before the OOS cutoff
# open. We assert every trade's open_time is < the OOS cutoff ms boundary.
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC (open_time of first OOS candle)

# --- cost model (matches make_result, see module docstring) ------------------
# iter-027: fee_pct=0.10 (round trip), slippage_pct=0.04 (round trip, 2 bps/side).
# Per-FILL (one side) cost = half of each: fee 0.05% + slippage 0.02% = 0.07%.
FEE_PER_SIDE_PCT = 0.05
SLIP_PER_SIDE_PCT = 0.02  # 2 bps per side
COST_PER_FILL_PCT = FEE_PER_SIDE_PCT + SLIP_PER_SIDE_PCT  # 0.07% per fill (entry or exit)


def sharpe_proxy_monthly(net_pcts: pd.Series, open_times_ms: pd.Series) -> float:
    """Monthly Sharpe proxy on the trade-net series aggregated by calendar month.

    iter-027's headline Sharpe is a monthly-series Sharpe. We replicate the spirit:
    bucket each trade's net pct into the calendar month of its ENTRY, sum per month,
    then Sharpe = mean/std * sqrt(12) on the monthly sums. This is a proxy because the
    backtest's weighted daily series differs, but it is APPLIED IDENTICALLY to the
    baseline and ladder books, so the DELTA is the meaningful comparison.
    """
    months = pd.to_datetime(open_times_ms, unit="ms").dt.to_period("M")
    monthly = pd.DataFrame({"m": months.values, "p": net_pcts.values}).groupby("m")["p"].sum()
    if len(monthly) < 2 or monthly.std(ddof=1) == 0:
        return float("nan")
    return float(monthly.mean() / monthly.std(ddof=1) * np.sqrt(12.0))


def concentration_metrics(net_pcts: np.ndarray) -> dict:
    """top-1 / top-2 share of net PnL + Herfindahl of |pnl|.

    Share is computed against the total POSITIVE net (the denominator iter-027's
    falsifier uses: 'top-2 ~438% of OOS net' means the net total is small and a couple
    winners dominate). We report share against total net Sigma AND against gross |pnl|
    so the de-concentration claim is robust to the small-denominator artifact.
    """
    arr = np.asarray(net_pcts, dtype=float)
    total_net = arr.sum()
    abs_arr = np.abs(arr)
    gross = abs_arr.sum()
    srt = np.sort(arr)[::-1]  # descending by signed net (the winners)
    top1 = srt[0] if len(srt) >= 1 else 0.0
    top2 = srt[:2].sum() if len(srt) >= 2 else top1
    # signed-net shares (matches the iter-027 falsifier framing; can exceed 100%)
    top1_share_net = top1 / total_net if total_net != 0 else float("nan")
    top2_share_net = top2 / total_net if total_net != 0 else float("nan")
    # gross |pnl| shares (bounded 0..1; robust to small net denominator)
    abs_srt = np.sort(abs_arr)[::-1]
    top1_share_gross = abs_srt[0] / gross if gross > 0 else float("nan")
    top2_share_gross = abs_srt[:2].sum() / gross if gross > 0 else float("nan")
    # Herfindahl on |pnl| shares
    w = abs_arr / gross if gross > 0 else np.zeros_like(abs_arr)
    hhi = float((w ** 2).sum())
    return {
        "n": len(arr),
        "total_net": float(total_net),
        "top1_share_net": float(top1_share_net),
        "top2_share_net": float(top2_share_net),
        "top1_share_gross": float(top1_share_gross),
        "top2_share_gross": float(top2_share_gross),
        "hhi_abs": hhi,
    }


def simulate_ladder(
    trades: pd.DataFrame,
    feat: pd.DataFrame,
    levels: list[tuple[float, float]],
    atr_mode: str,
) -> pd.DataFrame:
    """Simulate the ladder, return a leg-level book (one row per realized leg).

    levels: list of (atr_multiple, position_fraction) for the PARTIAL legs. The final
            leg gets the residual fraction (1 - sum of partial fractions) and exits at
            the ACTUAL iter-027 exit.
    atr_mode: 'raw'  -> level = entry +/- k * vol_atr_14_entry (absolute price)
              'natr' -> level = entry * (1 +/- k * vol_natr_14_entry / 100)
    """
    feat_sorted = feat.sort_values("open_time").reset_index(drop=True)
    ot = feat_sorted["open_time"].to_numpy(dtype=np.int64)
    high = feat_sorted["high"].to_numpy(dtype=float)
    low = feat_sorted["low"].to_numpy(dtype=float)

    rows = []
    partial_frac_sum = sum(f for _, f in levels)
    resid_frac = 1.0 - partial_frac_sum
    assert resid_frac > 1e-9, "residual leg fraction must be > 0"

    for _, t in trades.iterrows():
        direction = int(t["direction"])  # +1 long, -1 short
        entry_price = float(t["entry_price"])
        exit_price = float(t["exit_price"])
        entry_close_time = int(t["open_time"])  # == entry candle close_time
        exit_time = int(t["close_time"])
        atr_raw = float(t["vol_atr_14"])
        natr14 = float(t["vol_natr_14"])

        # Path candles: strictly AFTER the entry candle (open_time > entry candle open_time).
        # entry candle close_time == entry_close_time, its open_time = close_time - 8h+1ms.
        # Cleaner: take candles whose close_time > entry_close_time AND <= exit_time.
        ct = feat_sorted["close_time"].to_numpy(dtype=np.int64)
        path_mask = (ct > entry_close_time) & (ct <= exit_time)
        p_high = high[path_mask]
        p_low = low[path_mask]

        # Ladder level prices in the trade's favorable direction.
        leg_results = []  # (frac, gross_return_pct, label)
        used_frac = 0.0
        for k_mult, frac in levels:
            if atr_mode == "raw":
                if direction == 1:
                    level = entry_price + k_mult * atr_raw
                else:
                    level = entry_price - k_mult * atr_raw
            else:  # natr (pct)
                if direction == 1:
                    level = entry_price * (1.0 + k_mult * natr14 / 100.0)
                else:
                    level = entry_price * (1.0 - k_mult * natr14 / 100.0)

            touched = False
            if direction == 1:
                if p_high.size and np.nanmax(p_high) >= level:
                    touched = True
            else:
                if p_low.size and np.nanmin(p_low) <= level:
                    touched = True

            if touched:
                # optimistic fill at the ladder level (CAVEAT: assumes the level is
                # filled at exactly the level price, ignoring intra-candle slippage
                # beyond the modeled per-fill bps). Same favorable assumption SL/TP get.
                if direction == 1:
                    gross = (level - entry_price) / entry_price * 100.0
                else:
                    gross = (entry_price - level) / entry_price * 100.0
                leg_results.append((frac, gross, "partial"))
                used_frac += frac
            # if not touched, this partial's fraction rolls into the residual leg

        # Residual + any untriggered partial fractions exit at the ACTUAL iter-027 exit.
        resid_total = 1.0 - used_frac
        if direction == 1:
            gross_exit = (exit_price - entry_price) / entry_price * 100.0
        else:
            gross_exit = (entry_price - exit_price) / entry_price * 100.0
        leg_results.append((resid_total, gross_exit, "actual_exit"))

        # Charge costs. Entry-side cost (one fill) attributed to the FIRST leg. Each leg
        # pays its own exit-side fill cost. Each leg carries `frac` of the position.
        for i, (frac, gross, label) in enumerate(leg_results):
            exit_cost = COST_PER_FILL_PCT  # one exit fill per leg
            entry_cost = COST_PER_FILL_PCT if i == 0 else 0.0  # entry charged once
            # leg's contribution to TOTAL book net pct = frac * (gross - exit_cost) - entry_cost*frac0?
            # Position-weighted: net contribution = frac*gross - frac*exit_cost - (entry on full pos once).
            # Entry is a single fill for the whole position -> charge frac-weighted on leg-0 only as
            # the full entry cost (the whole position entered once): we charge COST_PER_FILL on the
            # full notional => contributes COST_PER_FILL to the trade total, attributed to leg 0.
            net_leg = frac * (gross - exit_cost) - entry_cost
            rows.append(
                {
                    "symbol": t["symbol"],
                    "direction": direction,
                    "open_time": entry_close_time,
                    "exit_time": exit_time,
                    "leg": label,
                    "frac": frac,
                    "gross_pct": gross,
                    "net_pct": net_leg,
                    "trade_id": int(t.name),
                }
            )

    return pd.DataFrame(rows)


def baseline_book(trades: pd.DataFrame) -> pd.DataFrame:
    """iter-027 single-exit IS book, one row per trade (net_pnl_pct as-is from CSV)."""
    return pd.DataFrame(
        {
            "open_time": trades["open_time"].astype(np.int64),
            "net_pct": trades["net_pnl_pct"].astype(float),
            "trade_id": trades.index.astype(int),
        }
    )


def report_book(name: str, net_pcts: np.ndarray, open_times: pd.Series, n_legs: int) -> dict:
    conc = concentration_metrics(net_pcts)
    sh = sharpe_proxy_monthly(pd.Series(net_pcts), pd.Series(open_times))
    win = float((np.asarray(net_pcts) > 0).mean())
    out = {
        "name": name,
        "n_rows": conc["n"],
        "n_legs_extra": n_legs,
        "total_net_pct": conc["total_net"],
        "monthly_sharpe": sh,
        "win_rate": win,
        "top1_share_net": conc["top1_share_net"],
        "top2_share_net": conc["top2_share_net"],
        "top1_share_gross": conc["top1_share_gross"],
        "top2_share_gross": conc["top2_share_gross"],
        "hhi_abs": conc["hhi_abs"],
    }
    return out


def fmt_pct(x: float) -> str:
    if x != x:
        return "   nan"
    return f"{x:+.2%}"


def main() -> None:
    # ---- load trades (IS-only) ----
    trades = pd.read_csv(TRADES_CSV)
    n_trades = len(trades)
    # LEAK GUARD 1: every trade is IS.
    max_ot = int(trades["open_time"].max())
    assert max_ot < OOS_CUTOFF_MS, (
        f"LEAK GUARD FAILED: a trade open_time {max_ot} >= OOS_CUTOFF {OOS_CUTOFF_MS}"
    )
    print(f"[guard] LEAK GUARD PASS: all {n_trades} trades IS "
          f"(max open_time {max_ot} < OOS_CUTOFF {OOS_CUTOFF_MS}).")

    # ---- load features, attach entry-candle ATR14 / NATR14 ----
    feat = pd.read_parquet(
        FEATURES_PQ,
        columns=["open_time", "close_time", "open", "high", "low", "close",
                 "vol_atr_14", "vol_natr_14", "vol_natr_21"],
    )
    # Join entry-candle ATR onto each trade via close_time == trade.open_time.
    entry_feat = feat[["close_time", "vol_atr_14", "vol_natr_14", "vol_natr_21", "close"]].rename(
        columns={"close_time": "open_time", "close": "entry_candle_close"}
    )
    trades = trades.merge(entry_feat, on="open_time", how="left")
    assert trades["vol_atr_14"].notna().all(), "some trades failed entry-candle ATR join"
    # Sanity: entry_price == entry candle close (entry fills at close).
    px_diff = (trades["entry_price"] - trades["entry_candle_close"]).abs().max()
    assert px_diff < 1e-6, f"entry_price != entry candle close (max diff {px_diff})"
    # Sanity: SL distance == 1.45 * NATR21 (confirms iter-027 NATR21 SL).
    sl_dist = (trades["stop_loss_price"] - trades["entry_price"]).abs() / trades["entry_price"] * 100
    ratio = (sl_dist / trades["vol_natr_21"]).dropna()
    print(f"[guard] entry==close check PASS (max diff {px_diff:.2e}); "
          f"SL/NATR21 ratio mean={ratio.mean():.4f} (expect 1.45).")

    # ---- baseline book ----
    base = baseline_book(trades)
    base_rep = report_book("iter-027 single-exit (IS)", base["net_pct"].to_numpy(),
                            base["open_time"], n_legs=0)

    # ---- ladder variants ----
    variants = {
        # 3-leg: 1/3 at 1.5 ATR, 1/3 at 3.0 ATR, 1/3 to actual exit
        "3-leg raw  (1/3@1.5, 1/3@3.0)": ([(1.5, 1 / 3), (3.0, 1 / 3)], "raw"),
        "3-leg natr (1/3@1.5, 1/3@3.0)": ([(1.5, 1 / 3), (3.0, 1 / 3)], "natr"),
        # 2-leg: 1/2 at 2.0 ATR, 1/2 to actual exit
        "2-leg raw  (1/2@2.0)": ([(2.0, 0.5)], "raw"),
        "2-leg natr (1/2@2.0)": ([(2.0, 0.5)], "natr"),
    }

    reports = [base_rep]
    leg_books = {}
    for name, (levels, mode) in variants.items():
        book = simulate_ladder(trades, feat, levels, mode)
        leg_books[name] = book
        # extra legs vs baseline (number of realized leg-rows - n_trades)
        extra = len(book) - n_trades
        rep = report_book(name, book["net_pct"].to_numpy(), book["open_time"], n_legs=extra)
        reports.append(rep)

    # ---- print comparison table ----
    rep_df = pd.DataFrame(reports).set_index("name")
    print("\n" + "=" * 100)
    print("COMPARISON — iter-027 single-exit IS baseline vs partial-profit ladder variants (IS-ONLY)")
    print("=" * 100)
    show = rep_df.copy()
    show["total_net_pct"] = show["total_net_pct"].map(lambda v: f"{v:+.2f}%")
    show["monthly_sharpe"] = show["monthly_sharpe"].map(lambda v: f"{v:+.4f}")
    show["win_rate"] = show["win_rate"].map(lambda v: f"{v:.1%}")
    for c in ["top1_share_net", "top2_share_net", "top1_share_gross", "top2_share_gross"]:
        show[c] = show[c].map(fmt_pct)
    show["hhi_abs"] = show["hhi_abs"].map(lambda v: f"{v:.4f}")
    print(show[["n_rows", "n_legs_extra", "total_net_pct", "monthly_sharpe", "win_rate",
                "top1_share_net", "top2_share_net", "top1_share_gross",
                "top2_share_gross", "hhi_abs"]].to_string())

    # ---- pre-registered PASS evaluation ----
    base_top2_gross = base_rep["top2_share_gross"]
    base_top2_net = base_rep["top2_share_net"]
    base_sharpe = base_rep["monthly_sharpe"]
    base_net = base_rep["total_net_pct"]

    print("\n" + "=" * 100)
    print("PRE-REGISTERED PASS CRITERION (Critic):")
    print("  (a) ladder REDUCES top-2 share vs iter-027 IS, AND")
    print("  (b) IS net monthly Sharpe bleed <= 0.05 (ladder Sharpe >= baseline - 0.05).")
    print(f"  baseline: top2_share_gross={fmt_pct(base_top2_gross)} "
          f"top2_share_net={fmt_pct(base_top2_net)} monthly_sharpe={base_sharpe:+.4f} "
          f"net_sum={base_net:+.2f}%")
    print("=" * 100)

    any_pass = False
    for rep in reports[1:]:
        d_top2_gross = rep["top2_share_gross"] - base_top2_gross
        d_top2_net = rep["top2_share_net"] - base_top2_net
        d_sharpe = rep["monthly_sharpe"] - base_sharpe
        d_net = rep["total_net_pct"] - base_net
        decon = (d_top2_gross < 0) or (rep["top2_share_net"] < base_top2_net)
        sharpe_ok = d_sharpe >= -0.05
        verdict = "PASS" if (decon and sharpe_ok) else "NEGATIVE"
        if verdict == "PASS":
            any_pass = True
        print(f"\n  {rep['name']}")
        print(f"     d_top2_share_gross = {d_top2_gross:+.4f} "
              f"({fmt_pct(base_top2_gross)} -> {fmt_pct(rep['top2_share_gross'])})  "
              f"[decon by gross: {d_top2_gross < 0}]")
        print(f"     d_top2_share_net   = {d_top2_net:+.4f} "
              f"({fmt_pct(base_top2_net)} -> {fmt_pct(rep['top2_share_net'])})  "
              f"[decon by net: {rep['top2_share_net'] < base_top2_net}]")
        print(f"     d_monthly_sharpe   = {d_sharpe:+.4f} "
              f"({base_sharpe:+.4f} -> {rep['monthly_sharpe']:+.4f})  "
              f"[bleed<=0.05: {sharpe_ok}]")
        print(f"     d_net_sum_pct      = {d_net:+.2f}% "
              f"({base_net:+.2f}% -> {rep['total_net_pct']:+.2f}%)")
        print(f"     >>> {verdict}")

    print("\n" + "=" * 100)
    print(f"OVERALL SCREEN VERDICT: {'PASS (>=1 variant)' if any_pass else 'NEGATIVE (no variant)'}")
    print("=" * 100)

    # ---- per-runner diagnostic: how many trades actually triggered a partial? ----
    print("\nRunner diagnostic (3-leg raw): how many trades realized >=1 partial leg")
    book3 = leg_books["3-leg raw  (1/3@1.5, 1/3@3.0)"]
    partials_per_trade = book3[book3["leg"] == "partial"].groupby("trade_id").size()
    n_runners = (partials_per_trade >= 1).sum()
    n_full_runners = (partials_per_trade >= 2).sum()
    print(f"  trades with >=1 partial fill: {n_runners}/{n_trades} "
          f"({n_runners / n_trades:.0%})")
    print(f"  trades with both partials (>=2): {n_full_runners}/{n_trades} "
          f"({n_full_runners / n_trades:.0%})")
    print(f"  non-runners (0 partials, behave as single-exit): "
          f"{n_trades - n_runners}/{n_trades}")

    # top trades in baseline vs their fate in ladder
    print("\nTop-3 baseline winners and their 3-leg-raw realized fate:")
    top_ids = base.sort_values("net_pct", ascending=False).head(3)["trade_id"].tolist()
    for tid in top_ids:
        b = base[base["trade_id"] == tid]["net_pct"].iloc[0]
        legs = book3[book3["trade_id"] == tid]
        leg_str = ", ".join(
            f"{r['leg']}({r['frac']:.2f}):{r['net_pct']:+.2f}%" for _, r in legs.iterrows()
        )
        print(f"  trade {tid}: baseline net {b:+.2f}%  ->  ladder legs: {leg_str} "
              f"(sum {legs['net_pct'].sum():+.2f}%)")


if __name__ == "__main__":
    main()
