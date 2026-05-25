---
iteration: iter-v1/013
date: 2026-05-25
verdict: EXPLORATION-NEGATIVE
subtype: BASIN-LOTTERY-CATASTROPHIC (NEW v1 catalog row; LM Master Phase 7.4 recommendation + Critic Phase 7.5 endorsement)
axis_family: methodology-substrate-test (3rd consecutive at pre-existing 8th family from /012; NOT a new family declaration)
axis: ENSEMBLE_SEEDS offset 3→6 ([789, 1001, 2002] → [3003, 4004, 5005]) on /011 R5-BINARY-KILL EXACT config
cadence_position: cycle-2 EXPLORATION #8 of 10
anchor: v0.v1-baseline-corrected (BASELINE_V1.md commit f8bc12c)
merge_decision: NO-MERGE (EXPLORATION-NEGATIVE catastrophic; over-determined — IS -0.6394 / OOS -0.3533 fail all absolute floors; 2-property substrate decomposition REFUTED-IN-FULL)
---

# Iteration iter-v1/013 — Diary

## One-Line Outcome

ENSEMBLE_SEEDS offset=6 (`[3003, 4004, 5005]`) on /011's BIT-IDENTICAL R5-BINARY-KILL config produced **IS Δ -0.9223** (catastrophic sign-flip; 1.30σ below F9 substrate-magnitude band [+0.38, +0.58]) + **OOS Δ -1.017** (catastrophic NEGATIVE; over-determined NO-MERGE) + **F7/F8 portfolio overlap 36.19% / 36.38%** (PARTIAL bands, seed-driven-roster confirmed) — **2-property substrate decomposition REFUTED-IN-FULL** at n=4; std jumps 0.025 → 0.66; the 3 prior +0.48 IS Δ data points were lucky basin draws from one mode of a multi-modal distribution.

## Outcome Summary — 2-Property Substrate Decomposition REFUTED

The key structural finding of /013 is the **decisive refutation** of the 2-property decomposition committed at /012 closeout. The decomposition posited:

**SUBSTRATE-LOCKED across /010/011/012 (DEAD claims after /013)**:
- ~~IS Sharpe-Δ magnitude ~+0.48-0.52 (variance < 0.03 across 3 iterations)~~ → REFUTED: /013 IS Δ -0.9223; n=4 std 0.66; 1.30σ band miss
- ~~LTC IS rank-1 dominant-symbol slot (3/3 iterations)~~ → REFUTED: /013 LTC IS rank-2 (LINK takes rank-1)
- ~~OOS-amplification fraction OOS Δ ≈ 0.45-0.78 × IS Δ~~ → bounds-violated (OOS Δ -1.017 / IS Δ -0.9223 = +1.10 ratio with both halves negative)

**SEED-DRIVEN (confirmed)**:
- Specific (symbol, open_time) trades: 64% rotate (F7 portfolio /011 36.19%; F8 portfolio /012 36.38%)
- Per-symbol catastrophic-loser identity ROTATES across seed windows (/011 BTC modest, /012 DOT catastrophic, /013 ETH+BTC catastrophic — TWO symbols this draw)
- Dominant IS winner ROTATES (LTC at /010/011/012 → LINK at /013)

**Refined framing (REPLACES strict 2-property decomposition)**: at v1 single-seed-window EXPLORATION (n_trials=35, ENSEMBLE_SIZE=3, V1_FEATURE_COLUMNS_PRUNED, 5-symbol universe), **EVERYTHING is basin-lottery**. IS Sharpe-Δ, OOS Sharpe-Δ, dominant-symbol identity, catastrophic-symbol identity, and roster composition are ALL seed-driven with HIGH variance. Only roster-rotation percent (~30-36% adjacent-seed overlap) is a seed-stable metric.

## Headline Metrics + Per-Symbol Decomposition

From `reports-v1/iteration_v1-013/comparison.csv`:

| Metric | IS | OOS | Baseline IS | Baseline OOS | IS Δ | OOS Δ |
|---|---|---|---|---|---|---|
| **Monthly Sharpe** | **-0.6394** | **-0.3533** | +0.2829 | +0.6637 | **-0.9223** | **-1.0170** |
| Sortino | -0.6401 | -0.3612 | +0.3205 | +0.7697 | -0.9606 | -1.1309 |
| Max Drawdown | 183.05% | 70.07% | 73.06% | 40.94% | +109.99pp | +29.13pp |
| Win Rate | 37.9% | 44.0% | 39.9% | 40.2% | -2.0pp | +3.8pp |
| Profit Factor | 0.8763 | 0.9264 | 1.060 | 1.156 | -0.184 | -0.230 |
| Total Trades | 536 | 184 | 621 | 189 | -85 | -5 |
| Total Net PnL | -110.34% | -18.73% | +54.05% | +38.13% | -164.39pp | -56.86pp |
| PSR_monthly_vs_0 | 0.1194 | 0.3723 | 0.977 | 0.989 | -0.858 | -0.617 |
| **R5-BINARY-KILL fire rate** | **19.05%** | **21.55%** | — | — | — | — |

**R5-BINARY-KILL mechanism intact (F2 PASS)**: fire rate within ±2pp of /011 (IS 18.34% / OOS 21.69%) and /012 (IS 17.38% / OOS 22.84%). Portfolio collapse is **basin-lottery draw**, not mechanism failure.

### Per-Symbol IS (536 trades, all per /013 reports)

| Symbol | trades | WR | net_pnl | /012 raw PnL | /011 raw PnL | Notes |
|---|---|---|---|---|---|---|
| **LINKUSDT** | 133 | 45.1% | **+128.38** | +105.86 | +42.45 | NEW IS rank-1 (LTC dominance lost) |
| LTCUSDT | 103 | 43.7% | +32.22 | +118.92 | +110.58 | LOST IS rank-1 dominance |
| DOTUSDT | 101 | 40.6% | -4.18 | -179.84 | +31.01 | recovered from /012 catastrophic |
| **BTCUSDT** | 73 | 28.8% | **-79.13** | +6.59 | -30.74 | catastrophic this seed window |
| **ETHUSDT** | 126 | 28.6% | **-139.78** | -22.68 | -49.45 | CATASTROPHIC this seed window |
| **PORTFOLIO** | **536** | **37.9%** | **-62.50** | +28.85 | +103.85 | Catastrophic collapse |

### Per-Symbol OOS (184 trades)

| Symbol | trades | WR | net_pnl | /012 raw PnL | /011 raw PnL | Notes |
|---|---|---|---|---|---|---|
| **DOTUSDT** | 52 | 46.2% | **+50.11** | -2.06 | +29.13 | NEW OOS rank-1 |
| LINKUSDT | 46 | 50.0% | +47.08 | +53.36 | +84.86 | stable OOS winner across 3 samples |
| BTCUSDT | 15 | 40.0% | +1.51 | +25.20 | +51.28 | OOS positive across all 3 samples |
| ETHUSDT | 42 | 42.9% | -5.59 | -17.16 | -2.90 | OOS negative across 2/3 samples |
| LTCUSDT | 29 | 34.5% | -40.16 | -47.66 | -19.12 | LTC OOS collapse across all 3 samples |
| **PORTFOLIO** | **184** | **44.0%** | **+52.95** | +11.68 | +143.23 | OOS net PnL positive, Sharpe negative (variance pattern) |

**Per-symbol PnL swings across DISJOINT seed windows at IDENTICAL substrate are MASSIVE**:
- DOT IS: +31 → -180 → -4 (range >200 raw PnL units)
- ETH IS: -49 → -23 → -140 (range >110 raw PnL units)
- BTC IS: -31 → +7 → -79 (range >80 raw PnL units)

This variance dwarfs the +0.47-0.52 IS Sharpe Δ band the substrate-magnitude lock framing tried to anchor on.

## IS Δ Trajectory Across 4 Iterations + Std Analysis

| Iteration | Inner seeds | Axis | IS Δ | OOS Δ |
|---|---|---|---|---|
| /010 | [42, 123, 456] | R5 proportional vol-target | **+0.4701** | -0.0283 |
| /011 | [42, 123, 456] | R5-BINARY-KILL @ 2.0% | **+0.4849** | +0.4072 |
| /012 | [789, 1001, 2002] | R5-BINARY-KILL @ 2.0% | **+0.5167** | +0.2726 |
| **/013** | **[3003, 4004, 5005]** | **R5-BINARY-KILL @ 2.0%** | **-0.9223** | **-1.0170** |

**IS Δ statistics:**
- At n=3: mean +0.49, std 0.025, range 0.047 — "substrate-locked"
- At n=4: mean -0.10, std **0.66**, range **1.44** — multi-modal

With true std ≈ 0.66, the prior claim "variance < 0.05 across 3 iterations" had probability ~(0.05/0.66)² ≈ **0.6%** under the true distribution — i.e. /010/011/012 was a 6-in-1000 luck event masquerading as a substrate property.

**R5-BINARY-KILL OOS Δ across 4 single-seed-window samples** (3 binary-kill: /011, /012, /013):
- Naive mean OOS Δ ≈ **-0.11**; std ≈ 0.80
- Multi-seed CONFIRMATION at n=10 standard error: 0.80/√10 ≈ 0.25
- Multi-seed CI estimate: **[-0.50, +0.50]** — non-discriminating against H0=0 mechanical edge
- Mechanical kill_low layer (~+0.05 estimate from /012) is **structurally swamped** by basin variance

## LM Master Phase 4.5 Substrate-Magnitude Lock Prediction CATASTROPHICALLY REFUTED

LM Master Phase 4.5 (`briefs-v1/iteration_v1-013/lgbm_advisor.md`):

> **My credibility-stake bet**: F9 PASS at **80% confidence** (P50 IS Δ = +0.52, band [+0.38, +0.58]).
> **Observed**: IS Δ -0.9223 — **off by 1.44**.

Phase 4.5 prediction REFUTED catastrophically. Magnitude was off by 1.44 in the WRONG direction; verdict-class was off (PROMISING-PARTIAL prediction → NEGATIVE-catastrophic observed).

**LM Master Phase 7.4 §5 calibration FINAL** (committed at `1ea8109`):
- Track record: **0/11 directional + 4 PARTIAL**
- **Verdict-class predictions**: flat priors ONLY at v1 single-seed EXPLORATION
- **Magnitude predictions**: report band only as plausibility envelope, not P50 anchor
- **Substrate-property claims**: **FORBIDDEN at n<10**
- HIGH-confidence statements: reserved for trivial-structural claims (e.g. F2 fire rate in [16%, 24%])

LM Master's load-bearing diagnostic value at /013: 2-property decomposition refutation in §1, per-symbol catastrophic-rotation observation in §3, R5-BINARY-KILL multi-seed CI calculation in §4. Diagnostic-frame contributions remain primary inputs; concentrated priors do not earn credibility at v1 single-seed.

## 5 LESSONS for v1 Cycle-2 Catalog

### LESSON #1: At v1 single-seed EXPLORATION, EVERYTHING is basin-lottery

The /011 closeout's strict substrate-lock claim (`feedback_v1_substrate_basin_lock.md`) and /012 closeout's 2-property refinement are BOTH refuted-in-full at /013. Adjacent seed offsets land in catastrophic AND lucky basins. IS Sharpe-Δ, OOS Sharpe-Δ, dominant-symbol identity, catastrophic-symbol identity, and roster composition are ALL seed-driven with HIGH variance. Only roster-rotation PERCENT (~30-36% adjacent-seed overlap) survives as a seed-stable metric.

**Generalization**: future v1 cycle-2 EXPLORATION briefs MUST use flat priors for verdict-class predictions; magnitude bands are plausibility envelopes, not P50 anchors. **No verdict-class predictions at concentrated priors.**

### LESSON #2: n=3 lucky draws can look like a substrate property; n=4 exposes the multi-modal distribution

The /010/011/012 sequence had IS Δ +0.4701 / +0.4849 / +0.5167 with variance < 0.03. This looked like a stable substrate signature. /013 added a 4th data point at -0.9223 — completely refuting the framing. The 6-in-1000 luck probability of the prior cluster reveals the true distribution as multi-modal with adjacent seed offsets sampling distinct basins.

**Generalization**: substrate-property claims at n<10 are forbidden in `feedback_v1_substrate_basin_lock.md` revision. **Anything observable above seed-window variance requires MULTI-SEED CONFIRMATION to attribute.** Single-seed EXPLORATION IS/OOS Δ values are basin-lottery draws, not edge measurements.

### LESSON #3: Methodology-probe iterations consume EXPLORATION budget without edge-finding

User feedback at /013 launch (codified in memory `feedback_v1_methodology_probe_discipline.md`): substrate-test iterations are methodology probes, not genuine edge-finding. /012 + /013 consumed 2 of cycle-2's 10 EXPLORATION slots on substrate probes; in retrospect, pivoting earlier to labeling axis (Critic /011 Path Forward Option 2) would have been more productive — the empirical refutation of substrate-lock at /013 settles the question, but a single methodology probe at /012 would have been sufficient to flag the cluster-luck risk.

**Generalization**: methodology probes cap at 1 per cycle. Cycle-2 has spent its methodology-probe budget (/008 PCA methodology + /012 substrate-test + /013 substrate-test exhausts it). Cycle-3 starts with a fresh methodology-probe budget.

### LESSON #4: Engineering report enforcement gap is now 3rd strike — Critic Phase 6.0 dispatch-side precondition required

3 consecutive iterations have produced engineering reports retroactively at QR Phase 7 closeout instead of at QE Phase 6 closeout:
- **/011 Critic Rec #3**: orchestrator-side hard-reject of Phase 7.5 dispatch without engineering report
- **/012 Critic Rec #1**: 3-way enforcement (orchestrator + QE skill + Critic Phase 6.0 precondition)
- **/013 STRIKE 3**: Critic Phase 7.5 §"Check 7" PROCESS CONCERN

The mechanism that has been violated 3 consecutive iterations is the **dispatch-side enforcement**, not the spec-side declaration. Critic Phase 6.0 currently verifies the brief Section 10.2 #4 SPEC is present; needs to escalate to dispatch HARD-REJECT precondition that BLOCKS Phase 7.5 if the artifact path is missing at the time of Critic dispatch.

**Commitment for /014**: Critic Phase 6.0 must include EXPLICIT PRECONDITION CHECK that the engineering report is referenced in brief Section 10.2 AS BLOCKING DELIVERABLE for Phase 7.5 dispatch.

### LESSON #5: R5-BINARY-KILL family CLOSED at v1 single-seed

4 EXPLORATIONs (/010 proportional R5 + /011/012/013 binary-kill R5) collectively show basin-lottery dominates mechanical filter:
- Mechanical kill_low layer estimate ~+0.05 OOS Δ (from /012 §1)
- Basin variance std ≈ 0.80 across 3 binary-kill OOS samples
- Multi-seed CONFIRMATION n=10 standard error ≈ 0.25
- Multi-seed CI estimate [-0.50, +0.50] — non-discriminating against H0=0

R5-BINARY-KILL family is structurally **unrescuable at v1 single-seed EXPLORATION budget**. Future cycle-2 EXPLORATIONs CANNOT select R5-BINARY-KILL or any R5 variant (proportional, binary-kill at any threshold). /015 pivots to UNUSED-family (labeling) per pre-committed conditional.

**Generalization**: at single-seed v1 EXPLORATION, any axis (R5 proportional, R5 binary-kill at HIGH threshold, R5 binary-kill at LOW threshold, seed-shift on same config) produces an IS Δ in the range [-1.0, +0.5] with high variance. Verdict-class is **overdetermined by the basin draw, not the axis mechanism**. Edge claims at single-seed are non-attributable.

## Critic Path Forward Summary (Option 1 labeling PRE-COMMITTED for /014)

From `briefs-v1/iteration_v1-013/review.md` §"Path Forward (mandatory on EXPLORATION-NEGATIVE)":

Pre-committed conditional locks /014 as labeling EXPLORATION precursor. UNUSED families in cycle-2: labeling, universe, model-arch.

### Option 1 — labeling triple-barrier σ_t via past-only EWMA at 14-day window — **PRE-COMMITTED for /014**

- **Family**: `labeling` (UNUSED in cycle-2; last used /004 in cycle-1)
- **Axis**: replace fixed-fraction ATR multipliers with past-only EWMA σ_t-scaled barriers (14-day EWMA window for σ_t)
- **Rationale**: changes per-cell IS label distribution → different LightGBM loss surface → potentially genuine basin-shift edge OR null OR negative
- **HIGH-RISK declaration MANDATORY** (label distribution change is HIGH-RISK per /005 rule and `quant-iteration-v1` skill discipline)
- **Mitigation**: pre-commit /015 = labeling CONFIRMATION regardless of /014 IS/OOS magnitude; brief Section 8 must register BOTH positive and negative basin outcomes as informational; pre-register expectation that single-seed lottery dominates labeling-axis IS/OOS Δ at /014

### Option 2 (RESERVE) — universe equal-weight portfolio with LTC weight cap at 25%

- **Family**: `universe` (UNUSED in cycle-2 since /006)
- **Axis**: equal-weight portfolio with LTC weight cap at 25%
- **Rationale**: tests whether basin-lottery is partly concentration artifact
- **NORMAL-RISK** with mitigation simulated effect required
- RESERVE only if /014 labeling EXPLORATION produces NEGATIVE-catastrophic and cycle-2 needs structural-axis breakout

### Option 3 (RESERVE) — model-arch XGBoost head-to-head on V1_FEATURE_COLUMNS_PRUNED

- **Family**: `model-arch` (UNUSED in cycle-2)
- **Axis**: XGBoost head-to-head with depth-wise growth at n_trials=35
- **Rationale**: v3 precedent at /016 was NEGATIVE clean at n_trials=10; v1 at n_trials=35 materially changes applicability. Structural orthogonality test
- RESERVE only if Options 1 + 2 produce NEGATIVE-catastrophic

**QR Phase 8 SELECTION**: **Option 1 (PRE-COMMITTED — cannot be renegotiated)** — /014 = labeling triple-barrier σ_t via past-only EWMA at 14-day window; HIGH-RISK declaration MANDATORY; /015 = labeling CONFIRMATION binding regardless of /014 magnitude.

## Cycle-2 Cadence Status

| Iteration | Family | Verdict |
|---|---|---|
| /006 | universe | EXPLORATION-NEGATIVE (DEGENERATE_PREDICTOR) |
| /007 | feature-family | EXPLORATION-NEGATIVE (NEGATIVE-NEGATIVE compound) |
| /008 | methodology | EXPLORATION-PROMISING-METHODOLOGY |
| /009 | feature-family | EXPLORATION-NEGATIVE (NEGATIVE-NEGATIVE compound) |
| /010 | risk-primitive | EXPLORATION-NEGATIVE (PROMISING-INERT-with-IS-basin-shift) |
| /011 | risk-primitive (binary-kill subtype) | EXPLORATION-NEGATIVE (catastrophic-basin-shift) |
| /012 | methodology-substrate-test (NEW 8th family) | EXPLORATION-NEGATIVE (BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP-PARTIAL) |
| **/013** | **methodology-substrate-test (3rd consecutive at 8th family)** | **EXPLORATION-NEGATIVE (BASIN-LOTTERY-CATASTROPHIC)** |

**Cycle-2 EXPLORATION count after /013: 8 of 10.** CONFIRMATION-eligible at /015 (2 more EXPLORATIONs required before CONFIRMATION can launch). /014 fills the 9th slot; /015 = labeling CONFIRMATION fills the 10:1 CONFIRMATION position.

**Cycle-2 verdict distribution after /013**: 0 pure PROMISING / 1 PROMISING-METHODOLOGY (non-compoundable, from /008) / 7 NEGATIVE. **No edge ingredient bundled yet.** /013's basin-lottery refutation is NOT an edge ingredient but a STRUCTURAL CALIBRATION input for /015 CONFIRMATION design (multi-seed dissolution n=10 expected SE ≈ 0.25 from observed single-seed std ≈ 0.66).

**HIGH-RISK pre-commit tripwire**: /013 declared NORMAL-RISK; no pre-commit tripwire. The discipline is battle-tested across /003-/012's 9 consecutive correct non-firings (~54h cumulative compute saved). /013's NORMAL-RISK declaration was correct — the substrate test did not change Optuna's training-objective domain; only RNG-init differs from /011/012.

## Permanent Catalog Additions (from /013 closeout)

1. **`feedback_v1_substrate_basin_lock.md` REFUTED-IN-FULL revision** (committed by LM Master Phase 7.4 + Critic Phase 7.5 at HEAD `1ea8109` / `b6a1aaa`):
   - RULE replaced: "At v1 single-seed-window EXPLORATION, EVERYTHING is basin-lottery" (NOT 2-property decomposition)
   - 4 data points: IS Δ +0.4701 / +0.4849 / +0.5167 / **-0.9223** (std jumps 0.025 → 0.66 at n=4)
   - "How to Apply (FINAL)": 5 rules including flat-prior mandate, multi-seed mandate for attribution, R5-BINARY-KILL family CLOSED at v1 single-seed, no substrate-property claims at n<10

2. **NEW v1 verdict subtype `BASIN-LOTTERY-CATASTROPHIC`** (LM Master Phase 7.4 §"Closing Note for Critic" recommendation; Critic Phase 7.5 endorsement at `briefs-v1/iteration_v1-013/review.md`). Applies to {F1 NEGATIVE-catastrophic, F3 IS Δ catastrophic-undershoot sign-flipped, F9 outside substrate-magnitude band} cell. Adds to existing v1 subtypes (`catastrophic-basin-shift`, `BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP`, `BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP-PARTIAL`).

3. **Engineering report dispatch-side hard-reject enforcement (3RD STRIKE codification)**: future /014 brief Critic Phase 6.0 MUST include EXPLICIT PRECONDITION CHECK that the engineering report path is referenced in brief Section 10.2 AS BLOCKING DELIVERABLE for Phase 7.5 dispatch. The mechanism that has now been violated 3 consecutive iterations is the dispatch-side enforcement, not the spec-side declaration.

4. **LM Master FLAT-prior rule for v1 single-seed EXPLORATION FINAL** (LM Master Phase 7.4 §5 self-calibration):
   - Verdict-class predictions: flat priors ONLY (A 30% / B 30% / C 40% by default at v1 single-seed)
   - Magnitude predictions: report band only as plausibility envelope, not P50 anchor
   - Substrate-property claims: FORBIDDEN at n<10
   - HIGH-confidence statements: reserved for trivial-structural claims (mechanical-config consequences like F2 fire rates)

5. **Methodology-probe discipline cap codified** (per `feedback_v1_methodology_probe_discipline.md` from /013 launch user feedback): methodology probes cap at 1 per cycle. Cycle-2 has spent its methodology-probe budget (/008 PCA methodology + /012 substrate-test + /013 substrate-test). Cycle-3 starts with a fresh budget.

6. **R5-BINARY-KILL family CLOSED at v1 single-seed EXPLORATION budget**: 4 EXPLORATIONs (/010 proportional, /011 binary-kill, /012 binary-kill offset=3, /013 binary-kill offset=6) collectively show OOS Δ trajectory +0.41 / +0.27 / -1.02 with std ≈ 0.80; multi-seed CI [-0.50, +0.50] non-discriminating against H0=0 mechanical edge. Future cycle-2 + cycle-3 EXPLORATIONs CANNOT select R5-BINARY-KILL or any R5 variant.

7. **/014 + /015 PRE-COMMITTED**: /014 = labeling EXPLORATION precursor (triple-barrier σ_t via past-only EWMA at 14-day window; HIGH-RISK declaration MANDATORY); /015 = labeling CONFIRMATION binding regardless of /014 IS/OOS magnitude. Cannot be post-hoc renegotiated.

## Reflection on User Feedback (Codified in `feedback_v1_methodology_probe_discipline.md`)

User feedback at /013 launch (2026-05-25, before backtest dispatched): "substrate-test iterations are methodology probes, not genuine edge-finding. Future iterations should default back to genuine new-axis EXPLORATIONs. /013 proceeds per user directive but the orchestrator should keep that in mind."

In retrospect, the user feedback is **decisively validated** by /013's outcome:
- /012 substrate-test PARTIAL (substrate-magnitude lock WEAK form retained; STRONG form refuted)
- /013 substrate-test confirmed-refutation (substrate-magnitude lock fully dead at n=4)
- **2 EXPLORATION slots consumed (/012 + /013)** on what could have been a SINGLE methodology probe + immediate pivot to labeling

The "n=3 lucky draws → n=4 refutation" lesson IS a real epistemic contribution — confirming the user feedback that more methodology probes have diminishing marginal value vs UNUSED-family EXPLORATION. The orchestrator should have caught the duplicate methodology-probe risk at /013 brief Phase 5.5 gate, but the Axis Rotation Discipline (5-of-5 strict window) is too narrow to catch 2-of-2 same-family methodology probes.

**Generalization codified at `feedback_v1_methodology_probe_discipline.md`**: methodology probes cap at 1 per cycle. Phase 5.5 gate audit checklist now includes "methodology probe in current cycle?" check; flagged second methodology probe in same cycle is BLOCKED unless QR + Critic + LM Master 3-way convergence on incremental value.

The orchestrator did execute /013 per user directive ("continue but keep that in mind"), and the outcome strongly affirms the user's prior expectation. The cycle-2 EXPLORATION budget is now structured to pivot decisively to labeling at /014 + /015, recovering from the methodology-probe overuse.

## Files & Commits on Branch

- Branch: `iteration-v1/013` from `iter-v1/012` closeout commit (tag `v0.v1-012`)
- HEAD before Phase 7+8: `b6a1aaa` (Critic Phase 7.5 review)

Commits in this iteration (pre-closeout):
- `c18e734` — QR Phases 1-5 + substrate-test 3rd seed sample + brief
- `5c1e5a4` — LM Master Phase 4.5 pre-design advisory
- `f82584e` — phase 5.5 gate PASS
- `5f4c610` — Critic Phase 6.0 pre-flight PASS
- (Backtest run; comparison.csv + reports artifacts in `reports-v1/iteration_v1-013/`)
- `1ea8109` — LM Master Phase 7.4 post-mortem + F7/F8 artifact + REFUTED-IN-FULL memory revision
- `b6a1aaa` — Phase 7.5 Critic review — EXPLORATION-NEGATIVE BASIN-LOTTERY-CATASTROPHIC
- `234be14` — QR Phase 7 evaluation + engineering report (3rd-strike fix)
- (Phase 8 closeout commit on this iteration)

Trunk merge: **NONE**. EXPLORATION-NEGATIVE catastrophic never merges to main.

Tag: `v0.v1-013` (applied after this Phase 8 closeout).
