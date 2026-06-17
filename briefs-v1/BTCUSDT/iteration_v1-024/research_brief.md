# Research Brief — iter-v1/024 (BTCUSDT) — Phases 1-2 (exogenous-stress KILL-SWITCH, IS-ONLY)

**Author:** Quant Researcher (crypto-markets). **Symbol:** BTCUSDT. **Interval:** 8h (sacred).
**Scope:** Phase 1-2 — a DETERMINISTIC exogenous-stress regime KILL-SWITCH on the iter-020 trend-state
book (binary: FLAT in stress regimes, no seed-varying trades, no magnitude sizing). IS-ONLY.
**Objective:** SHARPE via GENERALIZATION (both-positive first, then OOS; never overfit OOS).

## VERDICT: HONEST NULL — no exogenous-stress kill-switch ROBUSTLY lifts recent-sub-period stability. The single PLATEAU candidate (high realized-vol NATR z-state) is a thin-recent-slice CURVE-FIT — the exact iter-011 fragile-gate fingerprint — and is NEGATIVE on the grid-free last-IS-year. This comprehensively EXHAUSTS the BTC OOS-strengthening space; recommend consolidating iter-020 as the BTC baseline and extending the deterministic stack to the other coins.

The hypothesis — that turning the trend-state book OFF in crypto-native exogenous-stress regimes
(high realized-vol, funding-crowding, funding-flip, OI-unwind) removes the direction-whipsaw losses and
lifts recent-sub-period stability — was tested rigorously, IS-only, across three committed
cutoff-asserted scripts (10 candidate regimes × 6 thresholds = 60 kill-switch configs, plus a full
fragility decomposition and a grid-robustness control). **Every angle converges on a null.** I
recommend NOT implementing this axis.

This null is EARNED (60 backtested IS-only kill configs + a fragility control that caught a curve-fit
the threshold-plateau scan alone would have passed), not declared. It is the task's pre-registered
campaign-closing outcome: "if NO exogenous-stress kill-switch robustly lifts recent stability → this
exhausts the BTC OOS-strengthening space; consolidate iter-020 and extend to the other coins."

---

## All numbers from committed IS-only scripts (cutoff-asserted, past-only)
- `analysis/BTCUSDT/iteration_v1-024/exogenous_kill_switch.py` → `exogenous_kill_switch.csv` + `kill_switch_plateau_summary.csv`
- `analysis/BTCUSDT/iteration_v1-024/kill_decomposition.py` → `kill_decomposition.csv`
- `analysis/BTCUSDT/iteration_v1-024/grid_robustness.py` → `grid_robustness.csv`

Each hard-filters `open_time < OOS_CUTOFF_MS = 1742774400000` (2025-03-24) and asserts
`df["open_time"].max() < OOS_CUTOFF_MS` BEFORE any forward quantity. Forward log-return computed AFTER
the IS filter. SMA200/ATR14 `.shift(1)` past-only; the stress signal read at `t-1` via `.shift(1)`;
per-sub-period stress cut quantiles trained on PAST rows only (purged by N_LABEL=42). OOS rows never
read. `src/`, runner, OOS UNTOUCHED. IS window 2020-01..2025-03, 5727 8h candles, 11 ~6-month
sub-periods. RT cost 0.14% (fee 0.1% + 2bps/side slippage). Deployed label = fixed_horizon N=42 (14d),
the iter-020 baseline label. The kill-regime + threshold were chosen on the PLATEAU evidence (mid-band
q0.80), NOT by what helps OOS.

---

## The hypothesis (precise, as tasked)
1. KEEP the iter-020 stack verbatim: deterministic 200-SMA trend-state direction + strength-conviction
   gate (`|close-SMA200|/ATR14 ≥ q40`, past-only). The incumbent book = `fire_A`.
2. ADD a binary, deterministic, exogenous-stress KILL-SWITCH: at decision time `t`, if
   `STRESS(t-1) == True` → FLAT (skip); else trade the iter-020 stack. The kill is purely SUBTRACTIVE
   (`fire_kill = fire_A & ~stress`) — it can NEVER add a trade, so unlike iter-021 (funding-readmit,
   ADDED trades → K=20 lottery) it cannot re-introduce the seed lottery.
3. Claim to test: killing trades in the stress regime LIFTS the trend-state book's recent-sub-period
   stability (the OOS-proxy) ROBUSTLY — across a threshold PLATEAU, sign-consistent across multiple
   sub-periods — distinguishing it from the iter-011 fragile bull/bear gate.

Candidate exogenous-stress regimes (all past-only parquet columns): realized-vol state
(`vol_state_z_natr_30`, `vol_natr_7`, `vol_range_spike_24/72`), funding crowding
(`|funding_rate_zscore_30|`, `|funding_rate_zscore_90|`), funding flip (`|btc_funding_rate_8h_impulse|`),
OI build/unwind (`|oi_delta_30_z90|`, `|btc_oi_delta_5_z30|`, `|oi_price_divergence_30|`).

---

## Why it's a NULL — three decisive IS-only findings

### (1) Of 10 candidate regimes, only 1 even shows a recent3 PLATEAU; the rest are NO-LIFT or knife-edge
`exogenous_kill_switch.py`. Incumbent iter-020 book (trend-state dir + strength gate q40, NO kill):
full IS Sharpe +1.00, frac_pos 0.70, recent3 **+1.864**. Plateau summary (lift = how many of 6 cut
quantiles give a positive recent3 delta vs incumbent):

| candidate regime | lift_cuts/6 | best (cut, dRecent3) | verdict |
|---|:--:|---|---|
| **RVOL: high realized-vol NATR z-state** | **6/6** | (0.80, **+0.785**) | **PLATEAU** |
| RVOL: high NATR-7 | 6/6 | (0.80, +0.192) | plateau (tiny) |
| RVOL: high range-spike-72 | 4/6 | (0.75, +0.197) | plateau (tiny) |
| OI: extreme \|OI-price divergence\| | 4/6 | (0.85, +0.371) | plateau |
| FUND: extreme \|funding z30\| | 2/6 | (0.70, +0.497) | partial |
| FUND: large \|funding impulse\| | 1/6 | (0.80, +0.225) | KNIFE-EDGE |
| OI: extreme \|OI-delta-5 z30\| | 1/6 | (0.85, +0.123) | KNIFE-EDGE |
| RVOL: high range-spike-24 | 0/6 | (—, −0.188) | NO-LIFT |
| FUND: extreme \|funding z90\| | 0/6 | (—, −0.045) | NO-LIFT |
| OI: extreme \|OI-delta z90\| | 0/6 | (—, −0.278) | NO-LIFT (HARMS) |

Only `vol_state_z_natr_30` (high realized-vol NATR z-state) shows a materially-positive plateau
(+0.62 to +0.785 across the 0.70-0.80 band, tapering to +0.04 at q0.95 as fewer candles are killed).
This is the SOLE candidate that survives to the fragility control. The funding and OI families are
mostly NO-LIFT or knife-edge — they do NOT remove the whipsaw losses.

### (2) The ONE plateau candidate is a thin-recent-slice CURVE-FIT — the iter-011 fragility fingerprint
`kill_decomposition.py` (the iter-011 control; `vol_state_z_natr_30 ≥ q0.80`, the mid-band plateau cut).
Per-sub-period decomposition exposes that the +0.785 recent3 lift is ENTIRELY one thin sub-period:

| test | result | reads as |
|---|---|---|
| **Q1 sign-consistency** | of 10 sub-periods where the kill removes ≥1 trade, **5 improve / 5 worsen** | COIN-FLIP, not a generalizing edge |
| **Q3 killed-trade edge** | REMOVED trades: Sharpe **+1.26**, WR 0.634, mean PnL **+2.88%**; RETAINED: Sharpe +0.94, WR 0.526, mean +2.27% | the kill removes the BEST trades, not losers — UN-principled |
| **Q4 curve-fit-by-proxy** | recent3 lift +0.785 with all sub-periods → **+0.005** when the single most-recent sub-period is dropped | the entire benefit IS one sub-period |
| Q4 recent2 | lift +1.188 → **+0.111** dropping the last sub-period | same collapse |
| negative-sub-period rescue | the kill does NOT rescue any of the incumbent's 3 negative sub-periods (21-07 −0.01, 22-07 +0.03, 22-12 −0.12) | no whipsaw-loss removal where it matters |

The 24-12 sub-period has only **21 incumbent trades** (it is the truncated final IS slice — the 14d
label needs forward data before the OOS cutoff). The kill removes 5 of those 21, swinging that thin
slice from +3.18 to +5.32 (dS +2.13), which alone drives the recent3 average up by +0.78. This is
mechanically identical to the iter-011 failure: a benefit that lives in the single most-recent
(thinnest) slice, vanishing the moment that slice is removed — OOS-curve-fitting by proxy.

**Crypto-native mechanism (why removing high-RVOL candles HURTS, not helps):** on BTC 8h, high
realized-vol clusters in BOTH directions — corrections AND strong trend-persistence/reflexive
breakouts. The let-winners-run trend-state book makes its BIGGEST gains in the high-vol candles (the
removed trades net +2.88% vs +2.27% retained). Killing the high-vol state throws away the
let-winners-run upside. It is the WRONG direction for this strategy — the kill removes signal, not noise.

### (3) The plateau is grid-dependent and the kill is NEGATIVE on the grid-free last-IS-year
`grid_robustness.py` (the control's control). The "plateau" dissolves under any reasonable robustness check:

| robustness test | inc_recent3 | kill_recent3 | delta | reads as |
|---|---:|---:|---:|---|
| 4-month sub-period grid | −0.295 | +1.027 | +1.322 | grid-dependent |
| **6-month grid (headline)** | +1.864 | +2.649 | +0.785 | the apparent plateau |
| 9-month sub-period grid | +0.784 | +0.817 | **+0.033** | lift ~gone |
| 6mo grid, min_sub_trades=25 (drops thin 24-12) | +1.522 | +1.527 | **+0.005** | lift IS the thin slice |
| 6mo grid, min_sub_trades=50 | +1.522 | +1.527 | **+0.005** | confirmed |
| **last-IS-year 2024-03→2025-03 (grid-free)** | **+0.455** | **+0.314** | **−0.142** | kill is WORSE |

- The recent3 lift ranges +0.033 to +1.322 purely by changing the (arbitrary) sub-period length — a
  genuine kill would be grid-invariant. It collapses to +0.005 the moment the 21-trade slice is floored out.
- The decisive honest recency test is the **grid-free last-IS-year** (2024-03-24..2025-03-24, the
  cleanest pre-cutoff OOS-proxy): the kill makes the book **WORSE** (Sharpe +0.455 → +0.314, d −0.142),
  and the trades it removes over that year are net-WINNERS (mean +2.32%, Sharpe +0.805). On the actual
  most-OOS-relevant IS window, the high-RVOL kill destroys edge.

---

## Distinguishing this from a genuine kill (the iter-011 test, applied and FAILED)
The task demanded I prove this is GENUINELY different from the iter-011 fragile gate, not just another
recent-regime curve-fit. Applying the three pre-registered criteria:

| criterion for a genuine kill | result | pass? |
|---|---|:--:|
| (a) lifts recent-sub-period Sharpe | +0.785 on 6mo grid — but +0.005 floored, −0.142 grid-free | **FAIL** |
| (b) across a threshold PLATEAU (not knife-edge) | apparent 6/6-cut plateau, BUT grid-dependent (0.033–1.322) and thin-slice-driven | **FAIL** |
| (c) sign-consistent across MULTIPLE sub-periods | 5/10 coin-flip; benefit is the single thinnest slice | **FAIL** |

It fails all three. The apparent threshold-plateau (a) was a real but MISLEADING signal: it survived
the cut-quantile sweep because every cut still includes the dominant thin 24-12 slice. The fragility
control (sub-period grid + thin-slice floor + grid-free last-IS-year) is what exposed it — exactly the
iter-011 lesson institutionalized. This is the iter-011 fragile gate in new (exogenous-stress) clothes.

---

## Conclusion: the BTC OOS-strengthening space is comprehensively exhausted
The binding constraint remains DIRECTION-CORRECTNESS at the 14d horizon: the deterministic 200-SMA
trend-state direction whipsaws in the 2025-26 OOS regime, and **no IS-identifiable exogenous-stress
regime cleanly separates the whipsaw-losing candles from the trend-persistence-winning ones.** High
realized-vol — the most promising candidate — contains BOTH (the let-winners-run book's biggest wins
AND its corrections), so killing it removes signal. Funding-crowding, funding-flip, and OI-unwind
regimes show no robust recent lift at all.

Comprehensive BTC OOS-strengthening map (iter-005→024), every lever now tested IS-only:
features (orthogonal NULL) · label-mode (fixed_horizon = the IS unlock) · horizon (boosts IS, not OOS)
· direction source (stateless trend-state = the both-positive unlock, iter-020 MERGE) · conviction gate
(iter-020 MERGE) · risk/de-lever (R2 keeper; trend-scale failed) · funding-readmit (K=5 lottery,
collapsed K=20, iter-022) · non-directional magnitude SELECTION (iter-023 NULL) · **exogenous-stress
KILL-SWITCH (this NULL — adding/removing on regime both fail because the constraint is the deterministic
direction, which no exogenous regime cleanly predicts).** Both the ADD axis (iter-021/023) and the
SUBTRACT axis (iter-024) are now closed. iter-020 (IS +0.37 / OOS +0.09, both-positive) is the robust
CEILING of the directional trend-following approach on BTC.

---

## Pre-registered FALSIFIER (this NULL is overturned only if)
A backtest of the `vol_state_z_natr_30 ≥ q0.80` kill-switch on the iter-020 stack at K=20 produces:
(i) a last-IS-year Sharpe ≥ the ungated incumbent's +0.455, AND (ii) OOS Sharpe > 0 AND ≥ iter-020's
+0.09, AND (iii) the OOS lift NOT carried by ≤2 trades of a single month. I predict it will NOT: the
kill is data-deterministic (no model, no seed), it is −0.142 on the grid-free last-IS-year, and it
removes net-WINNER trades (the let-winners-run upside lives in high-vol candles). Spending K=20 compute
on this is NOT recommended.

## Recommended next axis — CONSOLIDATE iter-020 + extend to the other coins
1. **Accept iter-020 as the robust BTC baseline.** Three independent OOS-strengthening axes
   (funding-readmit iter-022, magnitude iter-023, exogenous kill iter-024) now confirm the thin
   both-positive OOS is INTRINSIC to the BTC let-winners-run trend-follower — every attempt to broaden
   or robustify it hits the lottery wall (added trades) or the regime/curve-fit wall (regime gates).
   The BTC OOS-strengthening space is comprehensively mapped and exhausted.
2. **Extend the proven deterministic stack to the other coins** (user: "we will work with the others
   soon"): trend-state direction (200-SMA, stateless) + strength-conviction gate (q40, past-only) +
   fixed_horizon N=42 label + the iter-020 risk stack (R2 brake / R3 OOD / R5 vol-target), per-symbol
   IS-calibrated. The mechanism may generalize BETTER on a coin whose 2025-26 OOS regime is less
   correction-dominated than BTC's (the BTC OOS is a single adverse trend-direction regime; a coin
   with more two-sided OOS regime variety gives the both-positive coherence a fairer test). This is a
   genuinely different bet — not more BTC knob-tuning — and is the highest-expected-value next step.

## Risk note
No merge candidate proposed (NULL), so no Risk Mitigation section is required this iteration. If the
falsifier backtest is run despite the prediction, it inherits iter-020's risk stack (R2 brake / R3 OOD /
R5 vol-target) unchanged — but I do NOT recommend spending the compute.
