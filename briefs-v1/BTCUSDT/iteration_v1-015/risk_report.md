# Risk Report — iter-v1/015 (BTCUSDT) — Phase 4.7 (Risk-method exploration, IS-only)

**Author:** Risk Engineer (RE), crypto-trade v1 single-symbol track. **Symbol:** BTCUSDT.
**Interval:** 8h (sacred). **Objective: SHARPE (risk-adjusted), NOT absolute return, NOT B&H.**
**Base strategy:** iter-010 (19-col HYBRID, fixed_horizon N=9 / 3d, let-winners-run execution:
`atr_sl=1.45`, TP non-binding, 9-candle timeout). IS Sharpe +0.39 (backtest), OOS −1.48.
**Mandate (user 2026-06-16 "grind it, try different risk methods"):** explore DIFFERENT risk /
sizing / exit methods toward a **both-positive** profile (IS > 0 AND OOS > 0), IS-only-calibrated.
**Do-not-repeat:** the iter-012 trend-scale de-lever FAILED because the OOS losses are WITHIN the
up-trend regime (the IS-bull edge inverts to OOS-bull) — the 200-SMA-slope regime label is the
WRONG discriminator. So every method here is **regime-label-AGNOSTIC**.

All numbers come from committed, re-runnable, **IS-ONLY** scripts under
`analysis/BTCUSDT/iteration_v1-015/`. Each hard-filters `open_time < OOS_CUTOFF_MS = 1742774400000`
(2025-03-24) via `load_is_frame()` (`_harness.py`), which asserts `df["open_time"].max() <
OOS_CUTOFF_MS` BEFORE any forward quantity. The expanding monthly walk-forward trains only on
candles strictly before each test window minus `EMBARGO_C = N+3 = 12` candles (≥ the N=9 horizon).
All risk state is path-only / past-only. **No OOS row is ever read.** Knowing "iter-010 OOS = −1.48"
was the MOTIVATING fact; nothing here is fit/selected against OOS.

| script | role | outputs |
|---|---|---|
| `_harness.py` | shared IS-only WF (returns direction + **prediction margin**) + let-run book + pooled-Sharpe/DD | — |
| `probe_a_conviction.py` | conviction-based sizing (user candidate #1) | `conviction_deciles.csv`, `conviction_subperiod.csv`, `conviction_sizing_sweep.csv`, `conviction_seed_robust.csv` |
| `probe_b_drawdown_brake.py` | **R2 drawdown brake** (user candidate #2) | `drawdown_brake_grid.csv`, `drawdown_brake_subperiod.csv`, `drawdown_brake_seed_robust.csv` |
| `probe_b2_control.py` | R2-vs-flat-cut control (the metric-trap guard) | `drawdown_brake_vs_flat.csv` |
| `probe_c_stress_and_combo.py` | SL-multiple sweep (candidate #3) + combo + stress matrix | `sl_multiple_sweep.csv`, `combo.csv`, `slippage_stress.csv` |

> **Metric note (load-bearing — carried from iter-012):** the metric here is **POOLED annualized
> Sharpe of size-weighted per-trade returns** + **additive max-drawdown (cum-pct points)**, NOT
> per-sub-period Sharpe (which is invariant to a within-window size multiplier — the iter-012
> lesson, why the trend-scale looked dead on the wrong metric). The pooled-Sharpe **baseline of the
> let-run book is +1.87** (per-trade pooled, seed 42); this is a DIFFERENT, larger number than the
> diary-010 **+0.39 time-series-daily backtest Sharpe** — they are not comparable in level, only in
> DELTA. QR/QE: judge the merge on the real backtest's daily Sharpe; the pooled numbers here are
> **direction-and-relative-magnitude** evidence (campaign proxy-overprediction lesson applies).

---

## 0. Headline finding (read this first)

I evaluated all four user-suggested methods on IS evidence and **pick the R2 drawdown brake
(currently OFF) as the single recommended primitive.** It is the only method that (a) is structurally
incapable of the iter-012 regime mistake (it reads REALIZED equity drawdown, never a regime label),
(b) delivers a large, seed-robust, cost-robust pooled-Sharpe lift that I proved is **genuinely
path-dependent** (not a disguised flat size cut — the metric-trap guard, §3), and (c) sharply bounds
the tail (worst trade −37%, worst day −38%) — the exact OOS-robustness property the OOS-bleed needs.

**R2 drawdown brake — `trigger=20, anchor=80, floor=0.20` (additive cum-pct-point units):**
- **pooled IS Sharpe +1.87 → +2.58** (Δ **+0.71**, seed-robust: all 5 seeds, mean +0.705, min +0.655);
- **max-DD 306 → 119 cum-pct points (−61%)**, all 5 seeds reduce (mean −61%);
- **the lift is PATH-DEPENDENT, not a size cut**: a flat multiplier of R2's own average size (0.435×)
  gives Sharpe Δ **+0.000** vs baseline (Sharpe is scale-invariant) — the **entire +0.71 lift comes
  from R2 de-levering DURING drawdowns and restoring size during recoveries** (§3, the decisive control);
- **tail bounded**: worst single trade −15.9% → −10.1% (+37%), worst single day −43.0% → −26.8% (+38%);
- **cost-robust and GROWING under stress**: Sharpe lift +0.715 / +0.716 / +0.769 at slippage
  {2, 4, 8} bps/side; at the 2-bps/side merge assumption IS Sharpe +1.63 → +2.34;
- **trade count UNCHANGED** (sizing only; floor 0.20 > 0 → no trade is gated). Trade-rate = iter-010's.

**This uses the EXISTING `risk_drawdown_*` BacktestConfig fields — minimal wiring (flip a flag +
4 numbers). Flagged §6.** The conviction-sizing and tighter-stop methods were measured and REJECTED
as primary (§2, §5.C1); details + honest negatives below.

**The honest OOS claim (§7 falsifier):** R2 cannot turn a negative OOS edge positive — it de-levers
AFTER a drawdown begins, so it bounds the DEPTH and continuation of the OOS bleed, it does not
pre-empt the first leg. The diary-010 OOS loss was a SUSTAINED bleed (negative in 11/16 months, two
big early losses) — precisely the drawdown shape R2 catches. Realistic prediction: R2 substantially
**bounds OOS drawdown and lifts OOS Sharpe toward 0** (the deep, persistent OOS bleed is exactly
where the brake de-levers hardest); whether it crosses to OOS-positive is the genuine test.

---

## 1. Method inventory + why three of four are rejected as primary

| method | mechanism | reads regime label? | IS verdict | role |
|---|---|---|---|---|
| **R2 drawdown brake** | de-lever after equity falls below running peak | **NO (path-only)** | **+0.71 Sharpe, −61% DD, path-dependent (§3)** | **RECOMMENDED PRIMARY** |
| Conviction sizing | size ∝ \|model forecast\| percentile | NO (model score) | +0.07 Sharpe, −28% DD; **does NOT fix sub-period inversion**; tilts MORE long/bull | rejected as primary (§2) |
| Tighter/vol stop | shrink `atr_sl` below 1.45 | NO (exit) | **1.45 already optimal**; tighter cuts winners > tail benefit (§5.C1) | rejected (keep 1.45) |
| NATR/vol KILL | binary entry skip in extreme/dead vol | NO (vol state) | not pursued — the vol-spike replay (§5.C3b) shows hi-NATR trades are NET-POSITIVE IS (net +193, WR 0.52); killing them removes edge, not loss | rejected (no IS basis) |

The NATR-kill is rejected on direct IS evidence: the top-10%-NATR entry candles are the book's
*best* trades (net +193, WR 0.524), not its losses — a vol-kill would curve-fit away edge. R2 instead
**de-levers** those vol-spike trades to ~0.45× only WHEN the book is already in drawdown, keeping
their upside when it is not.

---

## 2. Probe A — conviction sizing (user candidate #1): real DD control, NOT a generalization fix

`probe_a_conviction.py`. The model's prediction MAGNITUDE (\|forecast forward-return\|) is its own
conviction proxy. **IS evidence that conviction carries edge** (`conviction_deciles.csv`, seed 42):

| decile | n | WR | mean net | pooled Sharpe | frac_long | frac_bull |
|---:|---:|---:|---:|---:|---:|---:|
| 0 (lo) | 462 | 0.457 | −0.114 | −0.289 | 0.474 | 0.491 |
| 6 | 461 | 0.473 | +0.560 | +1.180 | 0.549 | 0.568 |
| 9 (hi) | 461 | 0.536 | +0.828 | +1.152 | **0.751** | **0.640** |

Top-vs-bottom-quartile mean-net is positive for **all 5 seeds** (mean +0.647, min +0.383,
`conviction_seed_robust.csv`) — conviction genuinely ranks trade quality IS. Conviction-proportional
sizing (floor 0.35) lifts pooled Sharpe +1.87 → +1.94 and cuts max-DD 306 → 223 (−28%)
(`conviction_sizing_sweep.csv`).

**WHY REJECTED AS PRIMARY — two honest IS red flags:**
1. **It does NOT fix the sub-period inversion** (`conviction_subperiod.csv`): the top-conviction
   quartile is net-positive in **6/9** sub-periods vs **7/9** for the full book — conviction does NOT
   concentrate in the stable sub-periods, and the recurring-negative windows (2022-01, 2022-07,
   2024-07) stay negative in the high-conviction subset. Conviction is a quality rank, not a
   generalization filter.
2. **It tilts the book MORE long / MORE bull (the iter-012 inversion direction).** High-conviction
   trades are 75% long / 64% bull (deciles 8–9) vs ~50%/55% baseline. Since iter-012 proved the
   IS-bull longs are exactly what INVERTS OOS, conviction sizing would **up-weight the trades most
   prone to the OOS inversion.** corr(conviction, bull_regime)=+0.085 is weak, so it is not fatal —
   but it points the wrong way for OOS robustness.

**Verdict:** conviction is a clean **DD-control** (−28%) and a real IS quality signal, but it is NOT
an OOS-generalization fix and it tilts toward the inverting trades. **Keep as an optional secondary
(§5.C2 combo), not the primary.** The combo (R2 + conviction) cuts DD slightly more (119 → 100) but
at a Sharpe and total-return cost (2.58 → 2.47, total 1212 → 957) — R2 alone dominates.

---

## 3. Probe B + B2 — R2 drawdown brake: the recommended primitive (and the metric-trap guard)

`probe_b_drawdown_brake.py` simulates the EXISTING R2 primitive faithfully: walk the chronological
trade stream, maintain cumulative weighted PnL + running peak, scale each NEW trade by a linear
factor 1.0 (at `trigger` DD) → `floor` (at `anchor` DD). Strictly causal: trade k's scale uses only
trades < k. Units are **additive cum-pct points** (matching the backtest's `weighted_pnl` accounting;
the book is additive, no compounding base).

**Grid (seed 42, `drawdown_brake_grid.csv`) — chosen config maximizes DD-cut s.t. Sharpe ≥ baseline:**

| trigger | anchor | floor | pooled Sharpe | maxDD | DD red. | fire rate | avg scale |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.0 (OFF) | — | — | +1.870 | 306.0 | — | 0.000 | 1.000 |
| **20** | **80** | **0.20** | **+2.581** | **118.6** | **−61.2%** | 0.891 | 0.435 |
| 40 | 80 | 0.20 | +2.450 | 123.3 | −59.7% | 0.795 | 0.455 |
| 20 | 120 | 0.20 | +2.389 | 141.9 | −53.6% | 0.882 | 0.532 |
| 20 | 80 | 0.33 | +2.538 | 148.2 | −51.6% | 0.885 | 0.524 |
| 20 | 80 | 0.50 | +2.397 | 187.5 | −38.7% | 0.877 | 0.644 |

**Seed robustness (`drawdown_brake_seed_robust.csv`), chosen config:** Sharpe Δ mean **+0.705**
(min +0.655, **all 5 ≥ 0**); max-DD reduction mean **−61.2%** (all 5 reduce). Per-seed lift spread
0.077 (≪ 0.30 basin-lottery threshold) — structural, not a draw artifact.

### 3.1 The METRIC-TRAP GUARD (the load-bearing methodological check)

The chosen R2 fires at ~89% with avg scale ~0.435 — so it is *mostly* a global size cut. A global
constant size cut leaves pooled Sharpe UNCHANGED (Sharpe is scale-invariant) but mechanically shrinks
*additive* DD. So I must prove the **+0.71 Sharpe lift is genuinely path-dependent**, not an artifact
of a smaller book. `probe_b2_control.py` compares R2 against a FLAT multiplier equal to R2's own
realized average scale (same average size, NO path-dependence), on the identical trade stream:

| seed | base Sharpe | R2 Sharpe | FLAT Sharpe | **R2 − FLAT** | R2 DD vs FLAT DD |
|---:|---:|---:|---:|---:|---:|
| 42 | 1.870 | 2.581 | 1.870 | **+0.711** | −11.0% |
| 123 | 1.752 | 2.408 | 1.752 | **+0.655** | −10.0% |
| 456 | 1.544 | 2.250 | 1.544 | **+0.706** | +3.4% |
| 789 | 1.663 | 2.395 | 1.663 | **+0.732** | −14.2% |
| 1001 | 1.785 | 2.508 | 1.785 | **+0.723** | −6.1% |

**Reads (decisive):**
- **FLAT − BASELINE = +0.000** (all seeds): a same-average-size flat cut does NOT move pooled Sharpe.
  This confirms Sharpe scale-invariance AND validates the harness.
- **R2 − FLAT = +0.705** (all seeds): the **entire +0.71 lift is path-dependence** — R2 cuts size
  during drawdowns and restores it during recoveries. This is a GENUINE risk mechanism, NOT the
  iter-012 metric trap and NOT a disguised global de-lever.
- **R2 cuts max-DD −7.6% MORE than a same-average-size flat cut** (4/5 seeds) — a real additional DD
  edge beyond the size reduction.

### 3.2 Where the brake fires — regime-AGNOSTIC by construction

`drawdown_brake_subperiod.csv`: avg brake scale in NEGATIVE sub-periods 0.384 vs POSITIVE 0.431 — it
de-levers somewhat harder in the loss windows, but crucially it fires across ALL sub-periods (66–100%)
because it reads only realized equity drawdown, never the 200-SMA regime. **This is exactly the
property that makes it immune to the iter-012 failure:** iter-012 cut size in down-trends and the OOS
losses were in up-trends, so it protected nothing. R2 cuts size wherever the book is bleeding —
up-trend, down-trend, or chop. If the OOS bleed recurs (it did, 11/16 months), R2 de-levers into it
regardless of what regime label the down-leg carries.

---

## 4. Kelly sizing derivation (4.7b)

iter-010 let-run IS profile: WR ≈ 0.434, payoff b = avg-win / |avg-loss| ≈ 1.41 (diary-010).
Symmetric-Kelly edge fraction: `f* = W − (1−W)/b = 0.434 − 0.566/1.41 = 0.033` (full-Kelly 3.3%).
The blended edge is THIN, and the let-run book is positively skewed (naive Kelly fragile), so a
**¼-Kelly posture (≈ 0.008)** is the conservative reading. **The R2 brake IS a path-conditional Kelly
fraction:** full size while the book is at/near its equity peak (edge realizing) → floor 0.20 in deep
drawdown (edge has stopped paying — Kelly says cut). It does NOT change the `max_amount_usd` /
`weight_factor` base sizing (keep iter-010); it modulates exposure within it. **Do NOT add an
absolute global Kelly cap** — the thin blended edge means a global cap would over-shrink the regimes
where the edge is realizing; R2's path-conditional cut is the correct expression of Kelly here
(cut after losses, not pre-emptively).

---

## 5. Stress matrix (4.7c)

### C1. Stop-loss multiple sweep (`sl_multiple_sweep.csv`, seed 42) — candidate #3, REJECTED

| atr_sl | WR | pooled Sharpe | maxDD | worst trade | SL-exit frac | total ret |
|---:|---:|---:|---:|---:|---:|---:|
| 1.00 | 0.384 | +1.159 | 282.7 | −11.00 | 0.550 | 799.7 |
| 1.25 | 0.431 | +1.510 | 293.9 | −13.73 | 0.454 | 1107.2 |
| **1.45 (incumbent)** | 0.458 | **+1.870** | 306.0 | −15.88 | 0.388 | 1409.8 |
| 1.75 | 0.481 | +1.842 | 411.5 | −17.63 | 0.311 | 1438.9 |
| 2.00 | 0.492 | +1.746 | 447.3 | −19.66 | 0.261 | 1392.5 |

**`atr_sl=1.45` is already the pooled-Sharpe optimum.** Tighter stops DO cap the tail (worst −13.7 /
−11.0) and cut DD slightly, but they truncate too many would-be winners (WR 0.46 → 0.38, total
1410 → 800), dropping Sharpe to +1.16/+1.51. **Keep the incumbent SL.** The R2 brake bounds the tail
(−37%, §C3b) far more cheaply than a tighter global stop — by cutting SIZE during drawdowns rather
than cutting every trade's stop distance.

### C2. Combo — R2 alone vs stacked (`combo.csv`, seed 42)

| config | pooled Sharpe | maxDD | total ret |
|---|---:|---:|---:|
| baseline | +1.870 | 306.0 | 1409.8 |
| **R2 only** | **+2.581** | 118.6 | 1211.7 |
| conviction only (floor .35) | +1.941 | 223.3 | 1108.5 |
| R2 + conviction | +2.470 | 100.2 | 956.5 |

R2 alone dominates on Sharpe and total return; the combo cuts a bit more DD (119 → 100) at a Sharpe
and return cost. **Recommend R2 alone for the EXPLORATION screen** (cleaner attribution, fewer knobs);
conviction-stacking can be revisited at CONFIRMATION if R2 alone is OOS-promising and more DD-cut is
wanted.

### C3a. Slippage cost-stress (`slippage_stress.csv`) — PRE-REGISTERED merge assumption

| slippage bps/side | RT drag % | Sharpe OFF | Sharpe ON | Sharpe Δ | maxDD OFF | maxDD ON |
|---:|---:|---:|---:|---:|---:|---:|
| **2.0 (merge)** | 0.04 | +1.626 | +2.341 | **+0.715** | 341.3 | 125.3 |
| 4.0 (2×) | 0.08 | +1.381 | +2.097 | **+0.716** | 376.7 | 131.8 |
| 8.0 (4×) | 0.16 | +0.891 | +1.660 | **+0.769** | 447.3 | 147.9 |

**Pre-registered merge cost assumption: `slippage_bps_per_side = 2.0` (round-trip 0.04%, v1
standard).** The R2 lift is robust and GROWS under cost stress (+0.715 → +0.769) — de-levering the
drawdown periods (SL-heavy, give more back to slippage) saves disproportionately more when slippage
is higher. Re-run the K=5 screen also at 4 bps/side; the lift must stay positive at both.

### C3b. Tail-loss + vol-spike replay (chosen R2)

- **Worst single trade:** OFF −15.88% → ON −10.06% (**+37%** tail reduction).
- **Worst single day:** OFF −42.95% → ON −26.79% (**+38%** tail reduction).
- **Vol-spike replay** (top-10% NATR entry candles, n=462): OFF net +193.3, WR 0.524 → ON net +173.6;
  R2 de-levers the vol-spike trades to avg 0.45× **only when the book is in drawdown**, retaining
  most of their (positive) edge. This is why a binary NATR-kill is the wrong tool: hi-vol entries are
  the book's BEST trades IS, not its losses.

### OOD / Mahalanobis note (4.7c)

The recurring-negative IS sub-periods (2022-H1/H2 = LUNA/3AC/FTX, 2025-Q1 correction) are the
highest-dispersion, most-out-of-distribution windows for a bull-trained model. R2 de-levers into them
**because they produce equity drawdown**, not because of any covariance distance — a path-only proxy
that is structurally aligned with the R3 OOD intent (cut size when far from the training distribution)
while being immune to the regime-label error. R2 does NOT concentrate PnL in OOD pockets; it does the
opposite. R3 (OOD Mahalanobis) stays ON at its training-window-recomputed default — no change.

---

## 6. RISK-CONFIG SPEC (pre-registered) — the deliverable

**Primitive:** R2 drawdown brake — a path-only, regime-AGNOSTIC, per-strategy cumulative-equity
de-lever. **Uses the EXISTING `risk_drawdown_*` BacktestConfig fields (currently OFF).**

**WIRING FLAG: EXISTING KNOB — minimal wiring.** Unlike iter-012 (which needed a NEW primitive +
init lookup + LiveConfig parity), R2 is already plumbed end-to-end (`backtest.py` vt_scale pipeline,
live engine `_rebuild_risk_state` R2 per-model cum-weighted-PnL + running peak — see CLAUDE.md
seed-live-db). **QE only needs to set the config values; no new field, no init lookup, no new wiring.**

| `BacktestConfig` field | iter-010 (current) | **iter-015 recommended** |
|---|---|---|
| `risk_drawdown_scale_enabled` | `False` | **`True`** |
| `risk_drawdown_trigger_pct` | 10.0 | **see units note below** |
| `risk_drawdown_scale_floor` | 0.33 | **0.20** |
| `risk_drawdown_scale_anchor_pct` | 30.0 | **see units note below** |

**UNITS NOTE — the one thing QE/QR must reconcile (flagged, not assumed):** my IS simulation
calibrated the trigger/anchor in **additive cum-pct points** (trigger=20, anchor=80) because the
backtest book is additive (`weighted_pnl`, no compounding base). The live `risk_drawdown_*_pct`
fields are **percent-of-peak-equity**. I deliberately did NOT guess the conversion — it depends on
the deployed equity base (`max_amount_usd` × leverage) and the backtest's weighted-PnL-to-percent
mapping, which is QE's domain (`backtest.py` R2 implementation). **My pre-registered, unit-robust
calibration is the RELATIVE shape, which QE should preserve under whatever unit the field actually
consumes:**
- **floor = 0.20** (de-lever to 20% size at deep drawdown) — unit-independent, use as-is.
- **trigger : anchor : baseline-maxDD ≈ 20 : 80 : 306 ≈ 0.065 : 0.26 : 1.0** of the book's IS
  baseline max-drawdown. I.e. **start braking at ~6–7% of baseline-maxDD of drawdown, reach the floor
  at ~26%.** QE: express trigger/anchor as that fraction of whatever DD unit `risk_drawdown_*_pct`
  consumes (if the field is % of an equity base where baseline maxDD ≈ X%, set trigger ≈ 0.065·X,
  anchor ≈ 0.26·X). **The grid (§3) is flat-topped around the chosen point** (trigger 20–40, anchor
  80–120 all give Sharpe +2.39 to +2.58, DD −50 to −61%) so a modest unit-conversion error stays in
  the good region — this is deliberately NOT a knife-edge optimum.

**Predicted IS effect (DIRECTION + RELATIVE-MAGNITUDE, per the campaign proxy lesson):** pooled IS
Sharpe lift **≈ +0.7** (seed-robust, all 5 seeds), **max-DD −≈60%**, worst trade/day **−≈37/38%**,
**trade count UNCHANGED**. Translated to the backtest's time-series-daily Sharpe (the merge metric):
**direction-positive lift + large DD cut**; the +0.39 IS daily Sharpe should rise and the 16.3% IS
max-DD should fall materially.

**Trade-rate:** UNCHANGED from iter-010 (R2 scales size, floor 0.20 > 0 → no trade gated). IS
~91/mo (pooled); OOS = iter-010's 98 trades (≥50 specialist floor, PASS).

**Composition:** R2 multiplies `vt_scale` and composes with R5 vol-target / vol_ceiling (all factors
≤ 1.0, conservative-stacking) — the established pattern. Leave R1/R3/R5 at their iter-010 settings.

### Pre-registered both-positive COHERENCE FALSIFIER (NEGATIVE verdict if ANY holds)

1. **Confirmation K=5 IS daily Sharpe does NOT rise vs the iter-010 K=5 no-R2 run** (the pooled
   +0.7 lift fails to materialize as ANY positive IS daily-Sharpe lift in the real backtest).
2. **K=5 per-seed IS Sharpe-lift spread > 0.30** (basin-lottery: the IS-proxy spread was 0.077; a
   real spread > 0.30 means the lift is a draw artifact, not structural).
3. **Fewer than 4/5 K=5 seeds show a positive IS Sharpe lift** vs the no-R2 run.
4. **IS max-DD does NOT fall** (the primitive's core promise — cut drawdown — unmet in the real run).
5. **Trade count changes > 1% ON vs OFF** (R2 leaked into entry logic — it must scale size only;
   any count change is a wiring defect / unit error).
6. **COHERENCE (the prize):** if BOTH the K=5 IS daily Sharpe AND OOS daily Sharpe are positive,
   this is the campaign's first both-positive config and the path-only-brake thesis is CONFIRMED. If
   OOS stays negative WHILE the IS lift + DD-cut hold, R2 is validated as a risk control (it bounded
   drawdown and lifted pooled risk-adjusted return as designed) but the OOS bleed arrived deeper /
   more front-loaded than the brake could neutralize — report as **PARTIAL (risk-accretive,
   regime-limited)**, NOT a primitive failure. The falsifier targets R2's IS-measurable claims
   (Sharpe lift + DD cut + tail cut + trade-count invariance), which are seed-robust — not a forced
   OOS-positive.

### Kill-switch (mid-flight)
Abort the K=5 run if the R2 fire-counter shows the brake firing with the trade COUNT diverging ON vs
OFF (entry-logic leak / unit blow-up), or if K=5 mean IS daily Sharpe < iter-010's no-R2 mean (the
lift inverted — wiring or unit-conversion defect; re-check the units-note conversion first).

---

## 7. Honest assessment — can this plausibly close the OOS gap?

**Yes, partially, and it is the best available lever — but I will not overclaim.** The iter-012
diagnosis stands: the directional model's IS-bull long edge inverts OOS-bull, and NO sizing primitive
can flip a negative directional edge into a positive one. What R2 CAN do, that iter-012's regime
de-lever could not:
- **iter-012 cut size by regime LABEL and the OOS losses were in the "good" regime → it protected
  nothing.** R2 cuts size by REALIZED drawdown, so it de-levers into the OOS bleed *wherever it
  occurs* — and the OOS bleed (diary-010: 11/16 negative months, two big early losses) is a sustained
  drawdown, exactly the shape R2 catches.
- R2 **bounds** the OOS drawdown (the −61% IS DD cut + −37/38% tail cut are the strongest evidence)
  and should lift the OOS Sharpe toward 0 by shrinking exposure during the persistent down-leg.

**The realistic both-positive odds are MODERATE, not high.** R2 reacts AFTER drawdown begins, so a
front-loaded OOS shock (the 2025-04 / 2025-06 early losses) takes the first leg at near-full size
before the brake engages. The most likely outcome is **PARTIAL: a much smaller, drawdown-bounded OOS
loss (Sharpe materially less negative, possibly near 0) with the IS lift + DD-cut intact** — which is
itself the track's stated win condition ("a strategy that earns less than B&H but with controlled
drawdown is the WIN"). If it crosses to OOS-positive, it is the campaign's first both-positive config.
Either way it is a genuinely DIFFERENT, structurally-sound risk method that does not repeat the
iter-012 mistake — and it is nearly free to wire (existing knob). **Recommend it for the K=5 screen.**

---

## 8. Handoff to Quant Research

QR may adopt, modify, or reject. **My recommendation: ADOPT the R2 drawdown brake at the §6 RELATIVE
calibration (floor 0.20; trigger ≈ 6.5% / anchor ≈ 26% of baseline-maxDD) for a K=5 EXPLORATION
screen on the iter-010 N=9 let-run config.** Rationale: (1) it is the ONLY user-suggested method that
is structurally immune to the iter-012 regime mistake (path-only, never reads a regime label); (2)
the +0.7 Sharpe lift is PROVEN path-dependent (§3 control), not a metric trap; (3) it bounds the tail
−37/38% — the OOS-robustness property the sustained OOS bleed needs; (4) it is an EXISTING knob —
minimal wiring vs iter-012's new primitive. **Caveats QR must fold in:** (a) the trigger/anchor
**UNIT conversion** (additive cum-pct points → the live `_pct` field) is QE's call — I pre-registered
the unit-robust RELATIVE shape (§6 units note), QR must require QE to preserve it, not the literal
20/80; (b) judge the merge on the real backtest's DAILY Sharpe, not my pooled numbers (proxy-direction
only); (c) the honest claim is PARTIAL (drawdown-bounded smaller OOS loss), not a guaranteed
both-positive (§7) — pre-register the §6 falsifier, which targets R2's IS-measurable claims, not a
forced OOS-positive; (d) conviction sizing (§2) and tighter stops (§5.C1) were measured and rejected
as primary — do not re-litigate them as the lever.

---

## Appendix — methodology / OOS-vigilance attestation

- All scripts read the IS frame ONLY via `_harness.load_is_frame()`, which hard-filters
  `open_time < OOS_CUTOFF_MS = 1742774400000` and asserts `df["open_time"].max() < OOS_CUTOFF_MS`
  BEFORE any forward computation. OOS rows are never read. Knowing iter-010 OOS = −1.48 informed the
  QUESTION; the R2 trigger/anchor/floor were calibrated ENTIRELY on IS pooled-Sharpe + DD + the
  path-dependence control.
- The expanding monthly walk-forward trains only on candles strictly before each test window minus
  `EMBARGO_C = N+3 = 12` candles (≥ the N=9 label horizon); the forward label is purged at the test
  boundary. The let-run trade reproduces iter-009/010/011/012 verbatim (enter at close; exit at
  min{SL 1.45·ATR adverse, 9-candle timeout}; TP non-binding; 0.1% fee; ATR = close·vol_natr_21/100).
- The R2 brake is strictly path-only: trade k's scale uses cumulative weighted PnL through trade
  k−1 only. The flat control (§3) confirms the lift is path-dependence, not a global size cut.
- The LightGBM read is a faithful DIRECTION + relative-conviction proxy of the deployed bagged
  specialist; magnitudes are relative ranking signals, not point backtest forecasts (campaign
  proxy-overprediction lesson — the +0.7 pooled-Sharpe lift is a direction-positive prediction).
- Scripts re-runnable; lint clean modulo the idiomatic uppercase design-matrix (`X`) + the
  trigger/anchor/floor calibration constants + docstring/comment line-length carve-out, consistent
  with the iter-008/009/010/011/012 convention.
