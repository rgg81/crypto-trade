"""iter-v3/114 — roster-level loss-separation ANNEX (the sharpening pass).

The main EDA (ldo_killswitch_eda.py) measured trigger separation on the FULL IS
LDO candle panel using a candle-outcome metric (better-of-long/short net PnL).
That metric is ~98% positive by construction — the better SIDE is almost always
in profit — so it cannot expose where the kill-switch should fire: it measures
"which direction was right", not "did the model's chosen trade lose money".

This annex does the analysis the kill-switch axis actually requires: it measures
whether an exogenous regime trigger separates the model's LOSING LDO trades from
its WINNING LDO trades, evaluated on the GROUND-TRUTH /059 LDO trade rosters
(9 IS trades, 12 OOS trades — read with actual net_pnl_pct and exit_reason).

This is the decisive GO/NO-GO evidence for the brief. It is honest about a
discouraging finding: per THE PRIME DIRECTIVE the EDA designs the sharpest
experiment, it does NOT terminate the iteration — but the brief must pre-register
the modal outcome the EDA points to.

Annex tables:
  A1  Per-trigger loser-vs-winner separation on the /059 LDO IS roster — every
      candidate trigger (BTC-DD, BTC-vol-z, LDO-realvol-z), both polarities
      (kill HIGH-trigger / kill LOW-trigger).
  A2  Per-trigger loser-vs-winner separation on the /059 LDO OOS roster (a
      FENCED feasibility annex — coverage / direction sizing only, NOT tuning).
  A3  Best-available gate sweep: for the IS-best trigger+polarity, sweep the
      threshold and tabulate the IS-roster counterfactual weighted-PnL delta
      (= -sum wpnl of suppressed trades), the n losers vs n winners suppressed,
      and the loser-hit-rate of the suppressed slice.
  A4  Honest verdict: does ANY exogenous trigger cleanly flag LDO's losing
      trades? Pre-register the modal Phase-6 outcome.
  A5  A wider exogenous-regime scan — calendar/regime variables beyond the three
      shipped triggers (BTC return sign, LDO vs BTC relative strength, BTC-DD
      direction) — to make the no-signal finding robust and not an artifact of
      three trigger choices.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from _shared import (
    asof_trigger,
    build_btc_regime_series,
    build_ldo_realvol_zscore,
    load_059_ldo_roster,
    load_btc_8h_csv,
    load_symbol_8h,
)

OUT = str(Path(__file__).resolve().parent)


def _attach_triggers(roster: pd.DataFrame) -> pd.DataFrame:
    """Attach all candidate exogenous triggers to a /059 LDO roster, past-only."""
    btc = build_btc_regime_series(load_btc_8h_csv())
    ldovz = build_ldo_realvol_zscore(load_symbol_8h("LDOUSDT", is_only=False))
    ot = roster["open_time"].to_numpy(dtype=np.int64)
    r = roster.copy()
    r["btc_dd"] = np.abs(asof_trigger(ot, btc, "btc_drawdown_pct"))
    r["btc_vz"] = np.abs(asof_trigger(ot, btc, "btc_vol_zscore"))
    r["ldo_vz"] = np.abs(asof_trigger(ot, ldovz, "ldo_realvol_zscore"))
    r["is_loser"] = r["net_pnl_pct"] < 0
    return r


def a1_is_roster_separation() -> tuple[pd.DataFrame, str, float]:
    """A1 — loser-vs-winner separation on the 9-trade /059 LDO IS roster.

    For each trigger, compare its value on losing trades vs winning trades. A
    trigger is useful for a HIGH-kill gate iff losers carry a HIGHER trigger
    value than winners (so a HIGH threshold suppresses losers preferentially).
    The separation_dir column records which polarity (if either) is correct.

    Returns the table plus the IS-best (trigger, polarity) pick: the trigger
    whose loser-mean / winner-mean gap, in the correct polarity, is largest in
    standardised units.
    """
    roster = _attach_triggers(load_059_ldo_roster("in_sample"))
    losers = roster[roster["is_loser"]]
    winners = roster[~roster["is_loser"]]
    rows = []
    for trig in ("btc_dd", "btc_vz", "ldo_vz"):
        lv = losers[trig].to_numpy()
        wv = winners[trig].to_numpy()
        l_mean, w_mean = float(np.nanmean(lv)), float(np.nanmean(wv))
        pooled_sd = float(np.nanstd(roster[trig].to_numpy(), ddof=1))
        std_gap = (l_mean - w_mean) / pooled_sd if pooled_sd else np.nan
        # HIGH-kill useful iff losers > winners; LOW-kill useful iff losers < winners
        if l_mean > w_mean:
            polarity = "kill_HIGH"
            useful = True
        elif l_mean < w_mean:
            polarity = "kill_LOW"
            useful = True
        else:
            polarity = "none"
            useful = False
        rows.append(
            {
                "trigger": trig,
                "n_losers": len(losers),
                "n_winners": len(winners),
                "loser_mean": round(l_mean, 4),
                "winner_mean": round(w_mean, 4),
                "loser_range": f"{np.nanmin(lv):.3f}-{np.nanmax(lv):.3f}",
                "winner_range": f"{np.nanmin(wv):.3f}-{np.nanmax(wv):.3f}",
                "std_gap": round(std_gap, 4) if np.isfinite(std_gap) else np.nan,
                "correct_polarity": polarity,
                "useful_direction": useful,
                "ranges_overlap": bool(
                    np.nanmax(lv) >= np.nanmin(wv)
                    and np.nanmax(wv) >= np.nanmin(lv)
                ),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/A1_is_roster_loser_separation.csv", index=False)
    # IS-best: largest |std_gap| in the useful direction
    usable = df[df["useful_direction"]].copy()
    usable["abs_gap"] = usable["std_gap"].abs()
    best = usable.sort_values("abs_gap", ascending=False).iloc[0]
    return df, str(best["trigger"]), float(best["std_gap"])


def a2_oos_roster_separation() -> pd.DataFrame:
    """A2 — FENCED loser-vs-winner separation on the 12-trade /059 LDO OOS
    roster. Coverage / direction sizing ONLY: confirms whether the IS-derived
    separation direction even holds OOS, so the brief Section 7 can pre-register
    honestly. NOT used to tune any threshold (the threshold is IS-only)."""
    roster = _attach_triggers(load_059_ldo_roster("out_of_sample"))
    losers = roster[roster["is_loser"]]
    winners = roster[~roster["is_loser"]]
    rows = []
    for trig in ("btc_dd", "btc_vz", "ldo_vz"):
        l_mean = float(np.nanmean(losers[trig].to_numpy()))
        w_mean = float(np.nanmean(winners[trig].to_numpy()))
        rows.append(
            {
                "trigger": trig,
                "n_oos_losers": len(losers),
                "n_oos_winners": len(winners),
                "oos_loser_mean": round(l_mean, 4),
                "oos_winner_mean": round(w_mean, 4),
                "oos_polarity": "kill_HIGH"
                if l_mean > w_mean
                else ("kill_LOW" if l_mean < w_mean else "none"),
                "note": "FENCED — OOS coverage/direction sizing only, not tuning",
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/A2_oos_roster_loser_separation_FENCED.csv", index=False)
    return df


def a3_best_gate_sweep(trigger: str, polarity_high: bool) -> pd.DataFrame:
    """A3 — threshold sweep of the IS-best trigger on the /059 LDO IS roster.

    For a grid of trigger thresholds, suppress the trades the gate would kill
    (HIGH-kill: trigger > thr; LOW-kill: trigger < thr) and tabulate the
    counterfactual IS weighted-PnL delta and the loser-hit-rate. A useful gate
    has a POSITIVE counterfactual delta (it removes net loss) AND a high
    loser-hit-rate (it suppresses losers, not winners)."""
    roster = _attach_triggers(load_059_ldo_roster("in_sample"))
    v = roster[trigger].to_numpy()
    wpnl = roster["weighted_pnl"].to_numpy()
    is_loser = roster["is_loser"].to_numpy()
    grid = np.round(np.linspace(np.nanmin(v), np.nanmax(v), 13), 4)
    rows = []
    for thr in grid:
        fire = (v > thr) if polarity_high else (v < thr)
        n_fire = int(np.nansum(fire))
        if n_fire == 0:
            rows.append(
                {
                    "trigger": trigger,
                    "polarity": "kill_HIGH" if polarity_high else "kill_LOW",
                    "threshold": float(thr),
                    "n_suppressed": 0,
                    "n_losers_suppressed": 0,
                    "n_winners_suppressed": 0,
                    "loser_hit_rate": np.nan,
                    "cf_wpnl_delta": 0.0,
                }
            )
            continue
        supp_wpnl = wpnl[fire]
        supp_loser = is_loser[fire]
        rows.append(
            {
                "trigger": trigger,
                "polarity": "kill_HIGH" if polarity_high else "kill_LOW",
                "threshold": float(thr),
                "n_suppressed": n_fire,
                "n_losers_suppressed": int(np.nansum(supp_loser)),
                "n_winners_suppressed": int(n_fire - np.nansum(supp_loser)),
                "loser_hit_rate": round(float(np.nansum(supp_loser) / n_fire), 4),
                "cf_wpnl_delta": round(float(-np.nansum(supp_wpnl)), 4),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/A3_best_gate_threshold_sweep.csv", index=False)
    return df


def a5_wider_regime_scan() -> pd.DataFrame:
    """A5 — wider exogenous-regime scan on the /059 LDO IS roster.

    To make the no-signal finding robust (not an artifact of three trigger
    choices), test additional exogenous regime variables. Each is a function of
    BTC/LDO price only — exogenous to LDO trade outcomes, hence deadlock-free:
        btc_dd_signed   — signed BTC drawdown (not abs): is LDO worse in deep
                          BTC drawdowns specifically?
        btc_ret_30d     — BTC 30-day log return: bull vs bear BTC backdrop.
        ldo_vs_btc_30d  — LDO 30-day return minus BTC 30-day return: LDO
                          relative strength.

    For each, the loser-mean vs winner-mean gap. If NONE of the 3 shipped + 3
    wider = 6 exogenous regime variables separates LDO losers from winners, the
    finding "no exogenous regime flags LDO losses" is robust.
    """
    roster = load_059_ldo_roster("in_sample")
    btc_csv = load_btc_8h_csv()
    ldo = load_symbol_8h("LDOUSDT", is_only=False).sort_values("open_time")

    # signed BTC drawdown (past-only)
    btc = btc_csv.sort_values("open_time").reset_index(drop=True)
    cs = btc["close"].shift(1)
    rmax = cs.rolling(90, min_periods=1).max()
    btc["btc_dd_signed"] = (cs - rmax) / rmax * 100.0
    # BTC 30d log return (past-only: close[t-1] vs close[t-91])
    btc["btc_ret_30d"] = np.log(cs / cs.shift(90))
    # LDO 30d log return (past-only)
    lc = ldo["close"].shift(1)
    ldo_ret = pd.DataFrame(
        {"open_time": ldo["open_time"], "ldo_ret_30d": np.log(lc / lc.shift(90))}
    )

    ot = roster["open_time"].to_numpy(dtype=np.int64)
    r = roster.copy()
    r["btc_dd_signed"] = asof_trigger(ot, btc, "btc_dd_signed")
    r["btc_ret_30d"] = asof_trigger(ot, btc, "btc_ret_30d")
    ldo_r = asof_trigger(ot, ldo_ret, "ldo_ret_30d")
    r["ldo_vs_btc_30d"] = ldo_r - r["btc_ret_30d"]
    r["is_loser"] = r["net_pnl_pct"] < 0

    losers = r[r["is_loser"]]
    winners = r[~r["is_loser"]]
    rows = []
    for trig in ("btc_dd_signed", "btc_ret_30d", "ldo_vs_btc_30d"):
        l_mean = float(np.nanmean(losers[trig].to_numpy()))
        w_mean = float(np.nanmean(winners[trig].to_numpy()))
        pooled_sd = float(np.nanstd(r[trig].to_numpy(), ddof=1))
        std_gap = (l_mean - w_mean) / pooled_sd if pooled_sd else np.nan
        rows.append(
            {
                "regime_variable": trig,
                "loser_mean": round(l_mean, 4),
                "winner_mean": round(w_mean, 4),
                "std_gap": round(std_gap, 4) if np.isfinite(std_gap) else np.nan,
                "separates_clean": bool(
                    np.isfinite(std_gap) and abs(std_gap) > 0.80
                ),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/A5_wider_regime_scan.csv", index=False)
    return df


def a4_honest_verdict(
    a1: pd.DataFrame,
    a3: pd.DataFrame,
    a5: pd.DataFrame,
    is_best_trigger: str,
    is_best_gap: float,
) -> pd.DataFrame:
    """A4 — honest GO/NO-GO verdict synthesis + pre-registered modal outcome.

    A clean GO requires an exogenous trigger that:
      (i)  separates LDO losers from winners on the IS roster with |std_gap| >
           0.80 (a non-trivial standardised separation), AND
      (ii) at some threshold, has loser_hit_rate > 0.60 with a POSITIVE
           counterfactual IS weighted-PnL delta.

    If no trigger clears (i)+(ii), the EDA finding is: NO exogenous regime
    cleanly flags LDO's losing trades. Per THE PRIME DIRECTIVE the iteration
    STILL runs a Phase-6 backtest — but the brief must pre-register the modal
    outcome as INERT/NEGATIVE (the gate either does not fire on real LDO trades,
    or fires indiscriminately on winners and losers alike).
    """
    # best clean separation across all 6 exogenous variables
    a1_best = a1["std_gap"].abs().max()
    a5_best = a5["std_gap"].abs().max()
    any_clean_sep = bool(
        (a1["std_gap"].abs() > 0.80).any() or (a5["std_gap"].abs() > 0.80).any()
    )
    # best loser-hit gate from A3
    a3_pos = a3[(a3["cf_wpnl_delta"] > 0) & (a3["n_suppressed"] > 0)]
    best_loser_hit = (
        float(a3_pos["loser_hit_rate"].max()) if len(a3_pos) else 0.0
    )
    clean_go = any_clean_sep and best_loser_hit > 0.60

    if clean_go:
        verdict = "GO"
        modal = "PROMISING — gate suppresses a loss-dense LDO slice"
    elif a1_best > 0.40 or a5_best > 0.40:
        # a weak-but-present separation — run the backtest as the decisive test
        verdict = "SHARPENED-GO"
        modal = (
            "INERT-or-NEGATIVE — the strongest exogenous trigger separates "
            "LDO losers from winners only weakly (|std_gap| < 0.80); the gate "
            "will fire on few real LDO trades and may catch winners too. The "
            "Phase-6 backtest is the decisive test."
        )
    else:
        verdict = "WEAK-GO"
        modal = (
            "INERT — no exogenous regime variable (6 tested) separates LDO "
            "losers from winners; the IS-calibrated gate fires on ~0 real LDO "
            "trades. Modal Phase-6 outcome: behaviourally inert (LDO IS roster "
            "unchanged). Run the backtest per THE PRIME DIRECTIVE."
        )
    df = pd.DataFrame(
        [
            {
                "is_best_trigger": is_best_trigger,
                "is_best_std_gap": round(is_best_gap, 4),
                "best_abs_std_gap_3_shipped": round(float(a1_best), 4),
                "best_abs_std_gap_3_wider": round(float(a5_best), 4),
                "any_clean_separation_gt_0p80": any_clean_sep,
                "best_loser_hit_rate_positive_cf": round(best_loser_hit, 4),
                "verdict": verdict,
                "pre_registered_modal_outcome": modal,
            }
        ]
    )
    df.to_csv(f"{OUT}/A4_honest_verdict.csv", index=False)
    return df


def main() -> None:
    print("=" * 72)
    print("iter-v3/114 — roster-level loss-separation ANNEX (the sharpening)")
    print("=" * 72)

    a1, is_best_trigger, is_best_gap = a1_is_roster_separation()
    print("\n[A1] /059 LDO IS roster — loser vs winner trigger separation:")
    print(a1.to_string(index=False))
    print(f"\nIS-best trigger: {is_best_trigger} (std_gap {is_best_gap:+.4f})")
    polarity_high = (
        a1[a1["trigger"] == is_best_trigger]["correct_polarity"].iloc[0]
        == "kill_HIGH"
    )
    print(f"correct polarity: {'kill_HIGH' if polarity_high else 'kill_LOW'}")

    a2 = a2_oos_roster_separation()
    print("\n[A2] /059 LDO OOS roster — FENCED loser/winner direction sizing:")
    print(a2.to_string(index=False))

    a3 = a3_best_gate_sweep(is_best_trigger, polarity_high)
    print(f"\n[A3] best-gate threshold sweep ({is_best_trigger}, "
          f"{'kill_HIGH' if polarity_high else 'kill_LOW'}):")
    print(a3.to_string(index=False))

    a5 = a5_wider_regime_scan()
    print("\n[A5] wider exogenous-regime scan (3 more variables):")
    print(a5.to_string(index=False))

    a4 = a4_honest_verdict(a1, a3, a5, is_best_trigger, is_best_gap)
    print("\n[A4] honest verdict:")
    for c in a4.columns:
        print(f"  {c}: {a4[c].iloc[0]}")

    print("\n" + "=" * 72)
    print(f"ANNEX COMPLETE — verdict: {a4['verdict'].iloc[0]}")
    print("=" * 72)


if __name__ == "__main__":
    main()
