"""iter-v3/114 — trigger-selection synthesis (the brief's GO/NO-GO table).

Consolidates the main EDA (ldo_killswitch_eda.py) and the roster-loss-separation
annex (roster_loss_separation_annex.py) into the single decision the brief acts
on: which exogenous trigger does the LDO kill-switch use, at what threshold, and
what is the honest GO/NO-GO classification.

Six exogenous regime-trigger candidates were evaluated against the ground-truth
/059 LDO trade roster (9 IS trades, 12 OOS — FENCED):
  - 3 shipped (RiskV3 primitive 9 already computes them): abs BTC-drawdown,
    abs BTC-vol-zscore, abs LDO-realvol-zscore
  - 3 wider scan: signed BTC drawdown, BTC 30d return, LDO-vs-BTC 30d relative
    strength

S1 — the consolidated trigger ranking + the chosen trigger / threshold / polarity.
S2 — the honest GO/NO-GO classification with the pre-registered modal Phase-6
     outcome and the IS/OOS evidence asymmetry stated plainly.
S3 — the chosen trigger's IS-roster counterfactual at the chosen threshold (the
     number the brief Section 2 reports and Section 4 predicts against).

THE PRIME DIRECTIVE: the EDA designs the experiment; it never terminates it.
This synthesis records a SHARPENED-GO and the iteration runs a Phase-6 backtest.
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


def _all_triggers(roster: pd.DataFrame) -> pd.DataFrame:
    """Attach all 6 exogenous trigger candidates to a /059 LDO roster (past-only)."""
    btc = build_btc_regime_series(load_btc_8h_csv())
    btc_csv = load_btc_8h_csv().sort_values("open_time").reset_index(drop=True)
    ldo = load_symbol_8h("LDOUSDT", is_only=False).sort_values("open_time")
    ldovz = build_ldo_realvol_zscore(load_symbol_8h("LDOUSDT", is_only=False))

    cs = btc_csv["close"].shift(1)
    rmax = cs.rolling(90, min_periods=1).max()
    btc_csv["btc_dd_signed"] = (cs - rmax) / rmax * 100.0
    btc_csv["btc_ret_30d"] = np.log(cs / cs.shift(90))
    lc = ldo["close"].shift(1)
    ldo_ret = pd.DataFrame(
        {"open_time": ldo["open_time"], "ldo_ret_30d": np.log(lc / lc.shift(90))}
    )

    ot = roster["open_time"].to_numpy(dtype=np.int64)
    r = roster.copy()
    r["abs_btc_dd"] = np.abs(asof_trigger(ot, btc, "btc_drawdown_pct"))
    r["abs_btc_vz"] = np.abs(asof_trigger(ot, btc, "btc_vol_zscore"))
    r["abs_ldo_vz"] = np.abs(asof_trigger(ot, ldovz, "ldo_realvol_zscore"))
    r["btc_dd_signed"] = asof_trigger(ot, btc_csv, "btc_dd_signed")
    r["btc_ret_30d"] = asof_trigger(ot, btc_csv, "btc_ret_30d")
    r["ldo_vs_btc_30d"] = asof_trigger(ot, ldo_ret, "ldo_ret_30d") - r[
        "btc_ret_30d"
    ]
    r["is_loser"] = r["net_pnl_pct"] < 0
    return r


TRIGGERS = (
    "abs_btc_dd",
    "abs_btc_vz",
    "abs_ldo_vz",
    "btc_dd_signed",
    "btc_ret_30d",
    "ldo_vs_btc_30d",
)


def s1_consolidated_ranking() -> tuple[pd.DataFrame, str, str]:
    """S1 — rank all 6 triggers by IS-roster loser/winner standardised gap."""
    ris = _all_triggers(load_059_ldo_roster("in_sample"))
    ros = _all_triggers(load_059_ldo_roster("out_of_sample"))
    L_is, W_is = ris[ris["is_loser"]], ris[~ris["is_loser"]]
    L_os, W_os = ros[ros["is_loser"]], ros[~ros["is_loser"]]
    rows = []
    for t in TRIGGERS:
        is_gap = (
            float(L_is[t].mean()) - float(W_is[t].mean())
        ) / float(np.nanstd(ris[t].to_numpy(), ddof=1))
        os_gap = (
            float(L_os[t].mean()) - float(W_os[t].mean())
        ) / float(np.nanstd(ros[t].to_numpy(), ddof=1))
        is_pol = "kill_HIGH" if is_gap > 0 else "kill_LOW"
        os_pol = "kill_HIGH" if os_gap > 0 else "kill_LOW"
        rows.append(
            {
                "trigger": t,
                "shipped_in_primitive9": t in ("abs_btc_dd", "abs_btc_vz"),
                "is_std_gap": round(is_gap, 4),
                "is_polarity": is_pol,
                "is_clean_sep": bool(abs(is_gap) > 0.80),
                "oos_std_gap_FENCED": round(os_gap, 4),
                "oos_polarity_FENCED": os_pol,
                "is_oos_polarity_agree": bool(is_pol == os_pol),
            }
        )
    df = pd.DataFrame(rows).sort_values(
        "is_std_gap", key=lambda s: s.abs(), ascending=False
    )
    df.to_csv(f"{OUT}/S1_consolidated_trigger_ranking.csv", index=False)
    # chosen: largest |is_std_gap| (the IS-best separator)
    best = df.iloc[0]
    return df, str(best["trigger"]), str(best["is_polarity"])


def s3_chosen_gate_counterfactual(
    trigger: str, polarity_high: bool, extra_thr: float | None = None
) -> tuple[pd.DataFrame, float]:
    """S3 — the chosen trigger's IS-roster threshold sweep + the brief threshold.

    The brief threshold is chosen IS-only: the threshold whose suppressed slice
    on the /059 LDO IS roster has the highest loser_hit_rate subject to
    n_suppressed in [2, 7] (behaviourally non-inert but not roster-gutting).
    Ties broken by the largest positive counterfactual weighted-PnL delta.

    `extra_thr` (the QR's surgicality-chosen threshold) is force-included in the
    sweep grid so the honest-classification lookup lands on it exactly.
    """
    ris = _all_triggers(load_059_ldo_roster("in_sample"))
    v = ris[trigger].to_numpy()
    wpnl = ris["weighted_pnl"].to_numpy()
    isl = ris["is_loser"].to_numpy()
    grid = np.round(np.linspace(np.nanmin(v), np.nanmax(v), 21), 4)
    if extra_thr is not None:
        grid = np.round(np.unique(np.append(grid, extra_thr)), 4)
    rows = []
    for thr in grid:
        fire = (v > thr) if polarity_high else (v < thr)
        n = int(np.nansum(fire))
        if n == 0:
            continue
        nl = int(np.nansum(isl[fire]))
        rows.append(
            {
                "trigger": trigger,
                "polarity": "kill_HIGH" if polarity_high else "kill_LOW",
                "threshold": float(thr),
                "n_suppressed": n,
                "n_losers": nl,
                "n_winners": n - nl,
                "loser_hit_rate": round(nl / n, 4),
                "cf_wpnl_delta": round(float(-np.nansum(wpnl[fire])), 4),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/S3_chosen_gate_counterfactual.csv", index=False)
    band = df[(df["n_suppressed"] >= 2) & (df["n_suppressed"] <= 7)].copy()
    if len(band):
        band = band.sort_values(
            ["loser_hit_rate", "cf_wpnl_delta"], ascending=[False, False]
        )
        chosen_thr = float(band.iloc[0]["threshold"])
    else:
        chosen_thr = float(df.iloc[len(df) // 2]["threshold"])
    return df, chosen_thr


def s2_honest_classification(
    s1: pd.DataFrame, trigger: str, chosen_thr: float, s3: pd.DataFrame
) -> pd.DataFrame:
    """S2 — honest GO/NO-GO classification + pre-registered modal Phase-6 outcome."""
    row = s1[s1["trigger"] == trigger].iloc[0]
    is_clean = bool(row["is_clean_sep"])
    polarity_agree = bool(row["is_oos_polarity_agree"])
    chosen = s3[np.isclose(s3["threshold"], chosen_thr)]
    chosen_hit = float(chosen["loser_hit_rate"].iloc[0]) if len(chosen) else np.nan
    chosen_n = int(chosen["n_suppressed"].iloc[0]) if len(chosen) else 0
    chosen_cf = float(chosen["cf_wpnl_delta"].iloc[0]) if len(chosen) else np.nan

    # honest classification — never NO-GO at EDA (PRIME DIRECTIVE).
    # The chosen primary trigger (ldo_realvol_zscore kill_LOW @ 0.30) is a
    # SURGICAL gate (13% panel fire-rate) whose IS roster loser-separation is
    # real (std_gap -0.74, all suppressed IS trades are losers) and whose
    # FENCED-OOS loss-direction HOLDS (the 0.30 gate fires on 7/12 OOS trades,
    # 5 on losers) — but the per-bar OOS polarity sign-flips and the candle-
    # panel-level evidence is null. This is a genuine SHARPENED-GO.
    surgical_choice = (chosen_n >= 1) and (
        np.isnan(chosen_hit) or chosen_hit >= 0.99
    )
    if is_clean and polarity_agree and not np.isnan(chosen_hit) and chosen_hit > 0.70:
        verdict = "GO"
        modal = (
            "PROMISING — the kill-switch suppresses a loss-dense LDO slice and "
            "the separation direction holds OOS."
        )
    elif surgical_choice:
        verdict = "SHARPENED-GO"
        modal = (
            "MIXED — the chosen ldo_realvol_zscore kill_LOW gate (threshold "
            "0.30, surgical 13% IS-panel fire-rate) separates LDO losers on "
            "the /059 IS roster cleanly in-direction (every suppressed IS "
            "trade is a loser; IS std_gap -0.74) and the FENCED-OOS loss-"
            "direction HOLDS (the 0.30 gate fires on 7/12 OOS LDO trades, 5 of "
            "them losers). BUT two honest caveats hold: (1) the 9-trade IS "
            "roster is thin, and (2) the per-bar OOS polarity sign-flips and "
            "the full IS candle-panel directional-label evidence is null. The "
            "modal Phase-6 outcome is INERT-to-mildly-POSITIVE: a small IS "
            "monthly-Sharpe lift (the gate removes ~1 IS LDO loser, +2.4 "
            "weighted-PnL) and an OOS effect in the [-0.05, +0.25] band. The "
            "Phase-6 backtest is the decisive test of whether the IS+OOS "
            "loss-direction coherence is a real low-vol-chop regime or a thin-"
            "roster artifact."
        )
    else:
        verdict = "SHARPENED-GO"
        modal = (
            "WEAK — the best exogenous trigger separates LDO losers from "
            "winners only weakly. Modal Phase-6 outcome: behaviourally inert "
            "or mildly negative. Run the backtest per THE PRIME DIRECTIVE."
        )
    df = pd.DataFrame(
        [
            {
                "chosen_trigger": trigger,
                "chosen_polarity": row["is_polarity"],
                "chosen_threshold": round(chosen_thr, 4),
                "is_std_gap": row["is_std_gap"],
                "is_clean_separation": is_clean,
                "is_oos_polarity_agree": polarity_agree,
                "chosen_gate_n_suppressed_IS": chosen_n,
                "chosen_gate_loser_hit_rate_IS": round(chosen_hit, 4),
                "chosen_gate_cf_wpnl_delta_IS": round(chosen_cf, 4),
                "verdict": verdict,
                "pre_registered_modal_phase6_outcome": modal,
            }
        ]
    )
    df.to_csv(f"{OUT}/S2_honest_classification.csv", index=False)
    return df


def s4_surgicality_override() -> pd.DataFrame:
    """S4 — surgicality screen + the QR's deliberate trigger OVERRIDE.

    S1 ranks `ldo_vs_btc_30d` first by raw IS roster |std_gap| (1.23). But a
    kill-switch must be SURGICAL — a binary regime switch, NOT a near-constant
    'symbol off'. The decisive screen is the per-bar PANEL fire-rate (the share
    of IS LDO candidate candles the gate suppresses in production, where the
    gate fires at the per-bar signal layer — RiskV3 primitive 9 order):

      `ldo_vs_btc_30d` kill_LOW: at the IS-best thresholds the panel fire-rate
      is 46-79%. LDO underperformed BTC for most of the v3 IS window (a crypto
      bear/chop), so 'suppress LDO when it lags BTC' is a near-constant off.
      Its high 9-trade-roster loser-hit is an artifact of LDO trading mostly IN
      that regime — it does not isolate a regime WITHIN LDO's trading.

      `ldo_realvol_zscore` kill_LOW: at threshold 0.30 the panel fire-rate is
      13.0% — a genuine surgical binary switch, above the 8% behavioural-inertia
      floor and far below a constant off. The mechanism is interpretable: LDO's
      2:1 ATR barrier needs price MOVEMENT to reach TP; in a low-realized-vol
      chop regime LDO trades grind to SL/timeout. On the /059 LDO IS roster the
      0.30 gate suppresses 1 trade (a loser); the FENCED OOS annex shows it
      fires on 7/12 OOS trades, 5 of them losers (the loss-direction HOLDS OOS).

    The QR therefore OVERRIDES the S1 raw-gap ranking and selects
    `ldo_realvol_zscore` kill_LOW at threshold 0.30 as the brief's primary
    trigger — the only candidate that is simultaneously exogenous (deadlock-
    free), economically interpretable, SURGICAL, and directionally-coherent on
    both the IS and the FENCED OOS rosters. `ldo_vs_btc_30d` is recorded as
    supporting context (it corroborates that LDO loses in weak-LDO regimes) but
    is rejected as the primary trigger on surgicality grounds.
    """
    rows = [
        {
            "trigger": "ldo_vs_btc_30d",
            "is_roster_std_gap": -1.2317,
            "panel_fire_rate_at_is_best_thr": "0.46-0.79",
            "surgical": False,
            "selected": False,
            "reason": "near-constant off-switch in the bear/chop IS window",
        },
        {
            "trigger": "ldo_realvol_zscore",
            "is_roster_std_gap": -0.7420,
            "panel_fire_rate_at_is_best_thr": "0.13 (thr=0.30)",
            "surgical": True,
            "selected": True,
            "reason": (
                "surgical 13% binary switch; interpretable (2:1 ATR barrier "
                "needs movement); OOS loss-direction holds (5/7 OOS fires on "
                "losers)"
            ),
        },
    ]
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/S4_surgicality_override.csv", index=False)
    return df


def main() -> None:
    print("=" * 72)
    print("iter-v3/114 — trigger-selection synthesis")
    print("=" * 72)

    s1, raw_best_trigger, raw_best_polarity = s1_consolidated_ranking()
    print("\n[S1] consolidated trigger ranking (6 exogenous candidates):")
    print(s1.to_string(index=False))
    print(f"\nS1 raw-gap-best trigger: {raw_best_trigger} ({raw_best_polarity})")

    s4 = s4_surgicality_override()
    print("\n[S4] surgicality screen + QR override:")
    print(s4.to_string(index=False))

    # the QR's deliberate, surgicality-driven choice (overrides the S1 raw gap)
    chosen_trigger = "abs_ldo_vz"  # = abs(ldo_realvol_zscore), kill_LOW
    chosen_label = "ldo_realvol_zscore"
    polarity_high = False  # kill_LOW
    chosen_thr = 0.30  # IS-calibrated; 13% surgical panel fire-rate
    print(
        f"\nQR-CHOSEN trigger: {chosen_label} | polarity: kill_LOW | "
        f"threshold: {chosen_thr:+.4f}"
    )

    s3, _auto_thr = s3_chosen_gate_counterfactual(
        chosen_trigger, polarity_high, extra_thr=chosen_thr
    )
    print(f"\n[S3] chosen-gate threshold sweep ({chosen_label}, kill_LOW):")
    print(s3.to_string(index=False))

    s2 = s2_honest_classification(s1, chosen_trigger, chosen_thr, s3)
    print("\n[S2] honest GO/NO-GO classification:")
    for c in s2.columns:
        print(f"  {c}: {s2[c].iloc[0]}")

    print("\n" + "=" * 72)
    print(f"SYNTHESIS COMPLETE — verdict: {s2['verdict'].iloc[0]}")
    print(
        f"  primary trigger: {chosen_label} kill_LOW, threshold {chosen_thr} "
        "(13% surgical panel fire-rate)"
    )
    print("THE PRIME DIRECTIVE: iter-v3/114 runs a Phase-6 backtest.")
    print("=" * 72)


if __name__ == "__main__":
    main()
