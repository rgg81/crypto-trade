"""iter-v3/107 gating-EDA script 2 — counterfactual exit re-resolution.

DECISIVE TEST 2 of 2. NO model retrain.

Hold the /059-baseline IS ENTRIES fixed (same symbol, direction, entry_price,
entry candle). Re-resolve each trade's EXIT on the 8h OHLCV path under
candidate exit designs vs the incumbent static triple-barrier, and compute
the counterfactual IS win-rate, profit factor, and monthly Sharpe.

A material IS Sharpe + win-rate lift over the static triple-barrier = GO.
No lift / a degradation = NULL-AT-EDA (the exit re-architecture does not help).

----------------------------------------------------------------------------
EXIT DESIGNS COMPARED (all CAUSAL — bar t uses only OHLCV path <= t):

  S  STATIC      incumbent — 2.0-ATR TP / 1.0-ATR SL / 21-candle timeout.
                 Reproduced here as the control; must match the /059 roster.

  Candidate trailing / dynamic designs (TP and 21-candle timeout retained;
  only the STOP becomes dynamic — a trailing stop can only exit EARLIER than
  the timeout, so the label/forward horizon is UNCHANGED):

  A  BE@1.0      breakeven move: once MFE >= 1.0 ATR, stop -> entry price.
                 Pure giveback elimination — converts a give-back loser to a
                 0-PnL scratch (minus 2x fee). Initial stop stays at 1.0 ATR.

  B  BE@0.75     same, armed earlier at 0.75 ATR.

  C  TRAIL@1.0/1.0   chandelier trail: once MFE >= 1.0 ATR (arm), stop trails
                 1.0 ATR behind the favorable extreme. Before arming, stop is
                 the static 1.0 ATR.

  D  TRAIL@1.25/0.75 arm later (1.25 ATR), trail tighter (0.75 ATR behind
                 extreme) — locks in more once a real move develops.

  E  BE@1.0+TRAIL@1.5/1.0  hybrid: breakeven at 1.0 ATR, THEN once MFE>=1.5
                 ATR switch to a 1.0-ATR chandelier trail. Two-stage.

----------------------------------------------------------------------------
8h INTRA-BAR PATH MODEL — honest, conservative ordering.
A single 8h candle is O/H/L/C; the true intra-bar path is unknown. For each
bar we resolve barrier/trail hits with a fixed CONSERVATIVE rule:
  * if BOTH the stop and the TP lie inside [low, high] of the same bar, the
    STOP is assumed hit first (adverse-first) — never optimistic.
  * the trailing stop is updated using the bar EXTREME, but a hit is tested
    against the stop level that was in force AT BAR OPEN (the trail ratchet
    from THIS bar's extreme cannot retroactively rescue THIS bar) — strictly
    causal, no within-bar look-ahead.
  * gap-through is honored: fill at the actual open if the bar opens beyond
    the level (matches the /059 SL-trade MAE ~1.7 ATR overshoot).
Fees: 0.10% round trip (V3 fee_pct=0.10, same as the /059 roster).

NO CHEATING: IS-only. Every trade asserted open_time < OOS_CUTOFF_MS.
OHLCV bars read only from entry candle to the 21-candle timeout candle —
no post-cutoff data, no post-timeout data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000
ATR_SL_MULT = 1.0
ATR_TP_MULT = 2.0
TIMEOUT_CANDLES = 21
FEE_PCT = 0.10  # round-trip, matches /059 fee_pct column
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
TRADES_CSV = "reports-v3/iteration_v3-059/in_sample/trades.csv"
BAR_MS = 8 * 3600 * 1000


def load_ohlcv(symbol: str) -> pd.DataFrame:
    df = pd.read_csv(f"data/{symbol}/8h.csv")
    return df[["open_time", "open", "high", "low", "close"]].sort_values(
        "open_time"
    ).reset_index(drop=True)


def resolve_exit(path: pd.DataFrame, entry: float, atr: float, direction: int,
                 design: str) -> tuple[float, str]:
    """Re-resolve one trade's exit on the 8h path. Returns (raw_pnl_pct, reason).

    raw_pnl_pct excludes fees (fees applied uniformly downstream).
    `path` is the bars from entry candle .. timeout candle inclusive.
    All decisions causal: the stop in force during bar i was fixed by bars < i.
    """
    tp = entry + direction * ATR_TP_MULT * atr
    stop = entry - direction * ATR_SL_MULT * atr  # initial static stop
    mfe = 0.0           # favorable excursion so far, ATR units (causal)
    armed_be = False    # breakeven move done
    armed_trail = False # trailing engaged

    # design params
    be_arm = {"A": 1.0, "B": 0.75, "E": 1.0}.get(design)
    trail_arm = {"C": 1.0, "D": 1.25, "E": 1.5}.get(design)
    trail_dist = {"C": 1.0, "D": 0.75, "E": 1.0}.get(design)

    for i in range(len(path)):
        bar = path.iloc[i]
        o, h, lo = float(bar["open"]), float(bar["high"]), float(bar["low"])

        # --- causal hit test: stop in force was set by PRIOR bars ---
        if direction == 1:
            # gap-through stop at open
            if o <= stop:
                return (o / entry - 1.0) * 100.0, "stop_dynamic"
            hit_stop = lo <= stop
            hit_tp = h >= tp
            if hit_stop:  # adverse-first conservative rule
                fill = min(stop, o)
                return (fill / entry - 1.0) * 100.0, "stop_dynamic"
            if hit_tp:
                fill = tp if o < tp else o
                return (fill / entry - 1.0) * 100.0, "take_profit"
        else:
            if o >= stop:
                return (entry / o - 1.0) * 100.0, "stop_dynamic"
            hit_stop = h >= stop
            hit_tp = lo <= tp
            if hit_stop:
                fill = max(stop, o)
                return (entry / fill - 1.0) * 100.0, "stop_dynamic"
            if hit_tp:
                fill = tp if o > tp else o
                return (entry / fill - 1.0) * 100.0, "take_profit"

        # --- end-of-bar: update MFE and ratchet the stop for NEXT bar ---
        if direction == 1:
            mfe = max(mfe, (h - entry) / atr)
        else:
            mfe = max(mfe, (entry - lo) / atr)

        if be_arm is not None and not armed_be and mfe >= be_arm:
            # breakeven move: stop -> entry (only ever tightens)
            stop = (entry if direction == 1 and entry > stop
                    else entry if direction == -1 and entry < stop
                    else stop)
            armed_be = True
        if trail_arm is not None and mfe >= trail_arm:
            armed_trail = True
        if armed_trail:
            if direction == 1:
                fav_ext = entry + mfe * atr
                new_stop = fav_ext - trail_dist * atr
                stop = max(stop, new_stop)  # trail only tightens
            else:
                fav_ext = entry - mfe * atr
                new_stop = fav_ext + trail_dist * atr
                stop = min(stop, new_stop)

    # timeout — exit at the close of the last (21st) candle
    last_close = float(path.iloc[-1]["close"])
    if direction == 1:
        return (last_close / entry - 1.0) * 100.0, "timeout"
    return (entry / last_close - 1.0) * 100.0, "timeout"


def monthly_sharpe(trades: pd.DataFrame) -> float:
    """Monthly Sharpe on weighted_pnl aggregated by calendar month (v3 metric)."""
    t = trades.copy()
    t["month"] = pd.to_datetime(t["close_time"], unit="ms").dt.to_period("M")
    m = t.groupby("month")["wpnl_cf"].sum()
    if m.std(ddof=1) == 0 or len(m) < 2:
        return 0.0
    return float(m.mean() / m.std(ddof=1) * np.sqrt(12))


def main() -> None:
    trades = pd.read_csv(TRADES_CSV)
    assert (trades["open_time"] < OOS_CUTOFF_MS).all(), "IS-only invariant violated"
    ohlcv = {s: load_ohlcv(s) for s in SYMBOLS}
    print(f"Loaded {len(trades)} /059 IS trades; IS-only OK\n")

    designs = ["S", "A", "B", "C", "D", "E"]
    names = {
        "S": "STATIC (incumbent)", "A": "BE@1.0", "B": "BE@0.75",
        "C": "TRAIL@1.0/1.0", "D": "TRAIL@1.25/0.75", "E": "BE1.0+TRAIL1.5/1.0",
    }
    summary = []
    per_trade_all = {}

    for design in designs:
        recs = []
        for _, row in trades.iterrows():
            entry = float(row["entry_price"])
            atr = abs(entry - float(row["stop_loss_price"])) / ATR_SL_MULT
            direction = int(row["direction"])
            wf = float(row["weight_factor"])
            ot = int(row["open_time"])
            path = ohlcv[row["symbol"]]
            seg = path[
                (path["open_time"] >= ot)
                & (path["open_time"] <= ot + TIMEOUT_CANDLES * BAR_MS)
            ].head(TIMEOUT_CANDLES + 1)
            if atr <= 0 or seg.empty:
                raw, reason = float(row["pnl_pct"]), row["exit_reason"]
            else:
                raw, reason = resolve_exit(seg, entry, atr, direction, design)
            net = raw - FEE_PCT
            recs.append({
                "symbol": row["symbol"], "close_time": int(row["close_time"]),
                "net_pnl_cf": net, "wpnl_cf": net * wf,
                "reason_cf": reason, "win_cf": net > 0,
                "orig_win": float(row["net_pnl_pct"]) > 0,
            })
        cf = pd.DataFrame(recs)
        per_trade_all[design] = cf

        wr = 100.0 * cf["win_cf"].mean()
        gp = cf.loc[cf["net_pnl_cf"] > 0, "net_pnl_cf"].sum()
        gl = -cf.loc[cf["net_pnl_cf"] < 0, "net_pnl_cf"].sum()
        pf = gp / gl if gl > 0 else float("inf")
        sh = monthly_sharpe(cf)
        tot = cf["wpnl_cf"].sum()
        rc = cf["reason_cf"].value_counts().to_dict()
        summary.append({
            "design": design, "name": names[design],
            "win_rate": round(wr, 1), "profit_factor": round(pf, 3),
            "monthly_sharpe": round(sh, 4), "total_wpnl": round(tot, 2),
            "n_tp": rc.get("take_profit", 0),
            "n_stop": rc.get("stop_dynamic", 0) + rc.get("stop_loss", 0),
            "n_timeout": rc.get("timeout", 0),
        })

    summ = pd.DataFrame(summary)
    summ.to_csv("analysis/iteration_v3-107/T5_exit_counterfactual.csv", index=False)

    print("=== T5: COUNTERFACTUAL IS METRICS — exit designs vs static ===")
    print(summ.to_string(index=False))

    base = summ[summ["design"] == "S"].iloc[0]
    print(f"\n  STATIC control: WR {base['win_rate']}%  Sharpe "
          f"{base['monthly_sharpe']}  PF {base['profit_factor']}")
    print(f"  /059 reported : WR 33.3%       Sharpe 1.0894    PF 1.4949")
    print("  (control should track /059; residual = 8h intra-bar path model)\n")

    print("  Deltas vs STATIC control:")
    for _, r in summ[summ["design"] != "S"].iterrows():
        d_wr = r["win_rate"] - base["win_rate"]
        d_sh = r["monthly_sharpe"] - base["monthly_sharpe"]
        d_pf = r["profit_factor"] - base["profit_factor"]
        print(f"    {r['design']} {r['name']:22s}: "
              f"dWR {d_wr:+5.1f}pp  dSharpe {d_sh:+7.4f}  dPF {d_pf:+7.3f}")

    # ---- T6: loser-conversion accounting on the best design --------------
    best = summ[summ["design"] != "S"].sort_values(
        "monthly_sharpe", ascending=False).iloc[0]
    bd = best["design"]
    print(f"\n=== T6: LOSER-CONVERSION ACCOUNTING — best design = {bd} "
          f"({best['name']}) ===")
    cf = per_trade_all[bd]
    sc = per_trade_all["S"]
    flip_w = int(((~sc["win_cf"]) & cf["win_cf"]).sum())
    flip_l = int((sc["win_cf"] & (~cf["win_cf"])).sum())
    print(f"  static losers -> {bd} winners (rescued)  : {flip_w}")
    print(f"  static winners -> {bd} losers  (clipped)  : {flip_l}")
    print(f"  net win-count change                      : {flip_w - flip_l:+d}")
    conv = pd.DataFrame({
        "metric": ["static_loser_to_cf_winner", "static_winner_to_cf_loser",
                   "net_win_count_change"],
        "value": [flip_w, flip_l, flip_w - flip_l],
    })
    conv.to_csv("analysis/iteration_v3-107/T6_loser_conversion.csv", index=False)

    # ---- T7: per-symbol Sharpe under best design -------------------------
    print(f"\n=== T7: PER-SYMBOL counterfactual (design {bd}) vs static ===")
    rows = []
    for sym in SYMBOLS:
        s_s = monthly_sharpe(sc[sc["symbol"] == sym])
        s_c = monthly_sharpe(cf[cf["symbol"] == sym])
        w_s = sc.loc[sc["symbol"] == sym, "wpnl_cf"].sum()
        w_c = cf.loc[cf["symbol"] == sym, "wpnl_cf"].sum()
        rows.append({"symbol": sym, "static_sharpe": round(s_s, 4),
                     "cf_sharpe": round(s_c, 4),
                     "static_wpnl": round(w_s, 2), "cf_wpnl": round(w_c, 2)})
        print(f"  {sym}: Sharpe {s_s:+.4f} -> {s_c:+.4f}   "
              f"wpnl {w_s:+.2f} -> {w_c:+.2f}")
    pd.DataFrame(rows).to_csv(
        "analysis/iteration_v3-107/T7_per_symbol_cf.csv", index=False)


if __name__ == "__main__":
    main()
