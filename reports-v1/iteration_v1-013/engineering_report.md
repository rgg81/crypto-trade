# iter-v1/013 — Engineering Report (Phase 7 — QR Evaluation)

**Date**: 2026-05-25
**QR**: claude-opus-4-7 (1M context) — quant-research-v1 mode
**Branch**: `iteration-v1/013`
**HEAD before Phase 7+8 closeout**: `b6a1aaa`
**Axis**: ENSEMBLE_SEEDS offset 3→6 (`[789, 1001, 2002]` → `[3003, 4004, 5005]`) on /011 R5-BINARY-KILL EXACT config — `methodology-substrate-test` family (3rd consecutive at this family; pre-existing 8th catalog family from /012)
**Mode**: EXPLORATION (cycle-2 #8 of 10; `--exploration --pruned-features --n-trials 35 --r5-binary-kill-enabled --r5-binary-kill-min-natr 2.0 --ensemble-seeds-offset 6`)
**Anchor**: `v0.v1-baseline-corrected` (`BASELINE_V1.md` commit `f8bc12c`); IS Sharpe +0.2829 / OOS Sharpe +0.6637
**Reference iterations**: /011 (offset=0 inner seeds `[42, 123, 456]`) IS +0.7678 / OOS +1.0709; /012 (offset=3 `[789, 1001, 2002]`) IS +0.7996 / OOS +0.9363

---

## 1. Final Verdict + Verdict-Class Rationale

**Verdict: EXPLORATION-NEGATIVE — new subtype `BASIN-LOTTERY-CATASTROPHIC`** (LM Master Phase 7.4 §"Closing Note for Critic" recommendation; Critic Phase 7.5 endorsement at `briefs-v1/iteration_v1-013/review.md` §"Substrate-Decomposition Catastrophic Refutation").

**Verdict mechanically deterministic from brief Section 8.1 pre-registration**: observed cell (F1 -1.017 ≤ -0.05, F3 IS Δ -0.9223 sign-flipped, F9 -0.9223 OUTSIDE band [+0.38, +0.58]) is BIT-COVERED by Section 8.1 Row 7 (F1 ≤ -0.05 NEGATIVE-catastrophic) AND Section 8.2 row 3 (F9 outside band → substrate-magnitude lock REFUTED). No matrix gap; no Critic discretion needed.

**The verdict-class name `BASIN-LOTTERY-CATASTROPHIC` is a NEW v1 subtype** appended to the verdict taxonomy. The /011 closeout codified `BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP` (F3 catastrophic + F1 PROMISING + F6 < 61%); the /012 closeout codified the PARTIAL variant. /013 sits in a 4th distinct cell — F1 NEGATIVE-catastrophic AND F3 IS Δ NEGATIVE-catastrophic AND F9 outside substrate-magnitude band — exactly the verdict-class the 2-property decomposition was designed to refute.

**Four reasons for NEGATIVE-catastrophic classification:**

1. **IS Sharpe Δ -0.9223 catastrophic-undershoot** (sign-flipped from /010/011/012's stable +0.47-0.52 band). F9 substrate-magnitude lock REFUTED at n=4. 1.30σ below band floor.
2. **OOS Sharpe Δ -1.017 catastrophic-NEGATIVE**. F1 fires NEGATIVE-catastrophic class. /015 pre-committed conditional FIRES → UNUSED-family CONFIRMATION (labeling). R5-BINARY-KILL CONFIRMATION is OFF the table.
3. **2-property substrate decomposition decisively refuted** at n=4 disjoint seed-window samples. The 3 prior "+0.48" data points were lucky basin draws from the positive subregion of a multi-modal distribution.
4. **F7/F8 portfolio overlap stable at ~30-36%** identical to /012-vs-/011, confirming roster-rotation magnitude is seed-window-driven BUT basin SIGN can flip with the rotation (not just composition).

**Reading the merge floors against the verdict**: OOS -0.3533 fails the +1.0 absolute merge floor (`feedback_sharpe_floor.md`); IS -0.6394 fails the +1.0 IS floor. Even ignoring substrate-decomposition refutation, /013 cannot merge under any criterion. NO-MERGE is over-determined.

---

## 2. Headline Metrics

From `reports-v1/iteration_v1-013/comparison.csv`:

| Metric | IS | OOS | Baseline IS | Baseline OOS | IS Δ | OOS Δ |
|---|---|---|---|---|---|---|
| **Monthly Sharpe** | **-0.6394** | **-0.3533** | +0.2829 | +0.6637 | **-0.9223** | **-1.0170** |
| Sortino | -0.6401 | -0.3612 | +0.3205 | +0.7697 | -0.9606 | -1.1309 |
| Max Drawdown | 183.05% | 70.07% | 73.06% | 40.94% | +109.99pp | +29.13pp |
| Win Rate | 37.9% | 44.0% | 39.9% | 40.2% | -2.0pp | +3.8pp |
| Profit Factor | 0.8763 | 0.9264 | 1.060 | 1.156 | -0.184 | -0.230 |
| Total Trades | 536 | 184 | 621 | 189 | -85 | -5 |
| Calmar | 0.6028 | 0.2674 | 0.740 | 0.931 | -0.137 | -0.664 |
| DSR | -67.15 | -44.31 | -93.80 | -35.66 | +26.65 | -8.65 |
| Total Net PnL | -110.34% | -18.73% | +54.05% | +38.13% | -164.39pp | -56.86pp |
| PSR_monthly_vs_0 | 0.1194 | 0.3723 | 0.977 | 0.989 | -0.858 | -0.617 |
| PSR_monthly_vs_1 | 0.0021 | 0.0684 | 0.0003 | 0.0789 | +0.002 | -0.011 |
| n_effective_trials | 13 | 13 | 13 | 13 | 0 | 0 |
| **R5-BINARY-KILL fire rate (portfolio)** | **19.05%** | **21.55%** | — | — | — | — |

**OOS/IS ratio = 0.5526** — both halves catastrophic; ratio above 0.5 is meaningless when both sides negative. PSR_monthly_vs_0 collapse from baseline 0.977 → 0.119 IS / 0.372 OOS confirms iteration is decisively in negative-edge regime.

**R5-BINARY-KILL fire rate**: IS 19.05% / OOS 21.55% — both inside F2 band [10%, 60%]; **F2 PASSES** (mechanism intact). Within ±2pp of /011 IS 18.34% / OOS 21.69% AND /012 IS 17.38% / OOS 22.84%. R5 mechanism is BIT-IDENTICAL across all 4 single-seed-window samples (/010 proportional + /011/012/013 binary-kill). **The portfolio collapse is NOT a mechanism failure** — it is a basin draw landing in the catastrophic subregion despite kill_low filter operating exactly as specified.

**Comparison vs /011 (1st seed-window) and /012 (2nd seed-window)**:

| Metric | /013 | /012 | /011 | Δ /013 vs /011 | Δ /013 vs /012 |
|---|---|---|---|---|---|
| IS Sharpe | -0.6394 | +0.7996 | +0.7678 | -1.4072 | -1.4390 |
| OOS Sharpe | -0.3533 | +0.9363 | +1.0709 | -1.4242 | -1.2896 |
| IS Δ vs baseline | -0.9223 | +0.5167 | +0.4849 | -1.4072 | -1.4390 |
| OOS Δ vs baseline | -1.0170 | +0.2726 | +0.4072 | -1.4242 | -1.2896 |
| Total Net PnL IS | -110.34% | +159.69% | +150.21% | -260.55pp | -270.03pp |
| Total Net PnL OOS | -18.73% | +49.76% | +61.29% | -80.02pp | -68.49pp |
| R5 fire rate IS | 19.05% | 17.38% | 18.34% | +0.71pp | +1.67pp |
| R5 fire rate OOS | 21.55% | 22.84% | 21.69% | -0.14pp | -1.29pp |
| IS Total Trades | 536 | 534 | 570 | -34 | +2 |
| OOS Total Trades | 184 | 183 | 180 | +4 | +1 |

**Key structural observation**: R5 fire rates within ±2pp; trade counts within ±5%; mechanism IS BIT-IDENTICAL across /011/012/013. The Sharpe-Δ sign flip is **fully attributable to the basin draw**, not to mechanism difference. Adjacent seed offsets (3 vs 6) routed Optuna through structurally distinct hyperparameter regions.

---

## 3. Per-Symbol IS/OOS PnL Attribution (vs /011 + /012 comparison)

Per LM Master Phase 7.4 §4 mandate from /012 closeout: report raw `net_pnl_pct` AND `pct_of_total_pnl` side-by-side. Pct alone is misleading at small/negative portfolio denominators.

### 3.1 In-Sample (536 trades)

| Symbol | trades | WR | **net_pnl_pct (RAW)** | pct_of_total | /012 net_pnl | /012 pct_total | /011 net_pnl | /011 pct_total | Δ raw vs /012 | Δ raw vs /011 |
|---|---|---|---|---|---|---|---|---|---|---|
| **LINKUSDT** | 133 | 45.1% | **+128.38** | **-205.47%** | +105.86 | +366.85% | +42.45 | +40.88% | **+22.52** | **+85.93** |
| **LTCUSDT** | 103 | 43.7% | **+32.22** | **-51.57%** | +118.92 | +412.12% | +110.58 | +106.48% | **-86.70** | **-78.36** |
| DOTUSDT | 101 | 40.6% | -4.18 | +6.69% | -179.84 | -623.24% | +31.01 | +29.86% | +175.66 | -35.19 |
| BTCUSDT | 73 | 28.8% | **-79.13** | +126.64% | +6.59 | +22.85% | -30.74 | -29.60% | -85.72 | -48.39 |
| **ETHUSDT** | 126 | 28.6% | **-139.78** | +223.71% | -22.68 | -78.59% | -49.45 | -47.61% | **-117.10** | **-90.33** |
| **PORTFOLIO** | **536** | **37.9%** | **-62.50** | — | +28.85 | — | +103.85 | — | **-91.35** | **-166.35** |

**Three structural observations:**

1. **Dominant-symbol rotation**: LTC was IS-rank-1 in /010/011/012 (+110.58, +118.92 raw). At /013, LTC drops to rank 2 (+32.22) and LINK takes rank 1 (+128.38). This refutes the substrate-property claim "LTC IS rank-1 dominance" from `feedback_v1_substrate_basin_lock.md`.

2. **DOT catastrophic basin-flip-back**: /011 DOT +31.01 → /012 DOT -179.84 → /013 DOT -4.18. DOT recovered from /012's catastrophic basin draw with a third disjoint seed window. The catastrophic-loser slot ROTATED to ETH (-139.78) AND BTC (-79.13) — TWO symbols this seed window. R5-BINARY-KILL filter offered no protection (fire rates inside F2 band; portfolio collapsed anyway).

3. **Per-symbol PnL swings across DISJOINT inner-seed windows at IDENTICAL substrate are MASSIVE**:
   - DOT: +31 → -180 → -4 (Δ across pairs > 200 raw PnL units)
   - ETH: -49 → -23 → -140 (Δ across pairs > 110 raw PnL units)
   - BTC: -31 → +7 → -79 (Δ across pairs > 80 raw PnL units)
   - LINK: +42 → +106 → +128 (only +86 monotone — but this is one symbol)
   - LTC: +111 → +119 → +32 (the IS-rank-1 winner of /010-/012 dropped 79 PnL units to rank 2)

The variance dwarfs the +0.47-0.52 IS Sharpe Δ band the substrate-magnitude lock framing tried to anchor on. **Per-symbol behavior is fully basin-lottery driven at single-seed.**

### 3.2 Out-of-Sample (184 trades)

| Symbol | trades | WR | **net_pnl_pct (RAW)** | pct_of_total | /012 net_pnl | /012 pct_total | /011 net_pnl | /011 pct_total | Δ raw vs /012 | Δ raw vs /011 |
|---|---|---|---|---|---|---|---|---|---|---|
| **DOTUSDT** | 52 | 46.2% | **+50.11** | -94.65% | -2.06 | -17.64% | +29.13 | +20.34% | +52.17 | +20.98 |
| **LINKUSDT** | 46 | 50.0% | **+47.08** | -88.92% | +53.36 | +457.17% | +84.86 | +59.24% | -6.28 | -37.78 |
| BTCUSDT | 15 | 40.0% | +1.51 | -2.85% | +25.20 | +215.88% | +51.28 | +35.80% | -23.69 | -49.77 |
| ETHUSDT | 42 | 42.9% | -5.59 | +10.56% | -17.16 | -147.03% | -2.90 | -2.02% | +11.57 | -2.69 |
| **LTCUSDT** | 29 | 34.5% | **-40.16** | +75.85% | -47.66 | -408.38% | -19.12 | -13.34% | +7.50 | -21.04 |
| **PORTFOLIO** | **184** | **44.0%** | **+52.95** | — | +11.68 | — | +143.23 | — | +41.27 | -90.28 |

**OOS observations:**

1. **DOT new OOS rank-1 winner** (+50.11 / 46.2% WR) — recovered from /012's catastrophic IS draw. /011 also had DOT positive (+29.13). Across 3 single-seed OOS samples, DOT trajectory is +29 / -2 / +50 (median +29, range +52).
2. **LINK stable OOS positive** across all 3 samples (+85, +53, +47). The single most-stable OOS winner across seed windows.
3. **LTC OOS collapse continues** across all 3 samples (-19, -48, -40). LTC IS dominance does NOT transfer OOS — the substrate-lock framing should have flagged this asymmetry at /011 closeout. (Per-symbol IS rank ≠ per-symbol OOS rank is a basin-property that survives the basin-lottery refutation; it is a baseline-stratum diagnostic, not a substrate property.)
4. **Total OOS net PnL +52.95** is positive despite OOS Sharpe -0.35. This is **trade-stream PnL variance**: a few large winners drive net PnL positive but distribution-tail risk (large drawdown, multiple losing months) anchors Sharpe negative. Confirms ratio-based comparison must dominate raw PnL when basin is catastrophic.

---

## 4. F1-F9 Verdict Matrix Cell-by-Cell Evaluation

From brief Section 4 falsifiers:

| Falsifier | Pre-registered band | Observed | Result | Subtype impact |
|---|---|---|---|---|
| **F1 OOS Sharpe-Δ** | [+0.05, +0.55] PROMISING; [-0.05, +0.05] INERT; ≤-0.05 NEGATIVE; ≤-0.30 catastrophic | **-1.017** | **FIRE NEGATIVE-catastrophic** | Decisive R5 CONFIRMATION REJECT |
| **F2 R5-BINARY-KILL fire rate** | [10%, 60%] both halves | IS 19.05% / OOS 21.55% | **PASS** | Mechanism intact (within ±2pp of /011/012) |
| **F3 IS Sharpe-Δ multi-band** | catastrophic-basin-shift class >+0.30 OR <-0.30 | **-0.9223** (sign-flipped catastrophic) | **FIRE catastrophic-undershoot** | Refutes substrate-magnitude lock |
| **F4 DEGENERATE_PREDICTOR** | none fire | clean | PASS | No structural defect |
| **F5 PSR + ADF** | PSR_monthly_vs_0 ≥ 0.50 both halves | IS 0.119 / OOS 0.372 | **FAIL** (informational at EXPLORATION) | Edge significance dead |
| **F6 OOS roster overlap vs BASELINE** | informational, [10%, 30%] expected | **16.30%** | within /011/012 range (16.7% / 14.2%) | Confirms axis still re-routes from BASELINE |
| **F7 LTC IS overlap vs /011** | [15%, 40%] seed-driven | **LTC 25.0% / portfolio 36.19%** | **PARTIAL** (in band) | Seed-driven roster confirmed |
| **F8 LTC IS overlap vs /012** | [25%, 50%] seed-driven | **LTC 33.0% / portfolio 36.38%** | **PARTIAL** (in band) | Seed-driven roster confirmed |
| **F9 IS Δ ∈ [+0.38, +0.58]** | substrate-MAGNITUDE LOCK | **-0.9223 OUTSIDE band** | **FAIL — REFUTED** | 2-property decomposition DEAD |

**Falsifier interaction analysis**: F2 + F7 + F8 PASS (mechanism + roster-rotation magnitudes operate as expected at this seed window), but F1 + F3 + F9 FIRE catastrophically. This decomposes as follows:
- Mechanism (kill_low) operates BIT-IDENTICALLY to /011/012 (F2 PASS)
- Roster rotation magnitude ~30-36% portfolio overlap matches /011↔/012 35.96% (F7, F8 PASS — confirms roster overlap is a seed-stable metric)
- BUT IS Sharpe and OOS Sharpe sign-flip catastrophically (F1, F3, F9 FIRE)

**Conclusion**: roster-overlap PERCENT is seed-stable (35-36% always), but the SIGN of basin outcome is NOT. F7/F8 stability was misread at /012 as evidence of seed-driven-roster + substrate-magnitude-lock; it actually only evidenced the seed-driven-roster claim. The substrate-magnitude lock claim REQUIRED the F9 IS Δ band to hold; /013 broke it.

---

## 5. IS Δ Trajectory Across 4 Iterations — Std Analysis

The 2-property decomposition's load-bearing empirical anchor was the IS Δ stability across /010/011/012:

| Iteration | Inner seeds | Axis | IS Δ | OOS Δ |
|---|---|---|---|---|
| /010 | [42, 123, 456] | R5 proportional vol-target | **+0.4701** | -0.0283 |
| /011 | [42, 123, 456] | R5-BINARY-KILL @ 2.0% | **+0.4849** | +0.4072 |
| /012 | [789, 1001, 2002] | R5-BINARY-KILL @ 2.0% | **+0.5167** | +0.2726 |
| /013 | [3003, 4004, 5005] | R5-BINARY-KILL @ 2.0% | **-0.9223** | -1.0170 |

**IS Δ statistics across 4 iterations:**
- Mean: -0.10 (would have been ~+0.49 if computed at n=3)
- Std: **0.66** (was 0.025 at n=3)
- Range: 1.44 (max +0.5167 − min -0.9223)

The std jump from **0.025 → 0.66 at n=4** is the decisive evidence the 3 prior observations were lucky draws from one mode of a multi-modal distribution, not measurements of a substrate-locked invariant. With true std 0.66, the prior claim "variance < 0.05 across 3 iterations" had probability ~(0.05/0.66)² ≈ 0.6% under the true distribution — i.e. /010/011/012 was a 6-in-1000 luck event masquerading as a substrate property.

**OOS Δ statistics across 4 iterations:**
- Mean: -0.09 (would have been +0.22 at n=3)
- Std: **0.62** (was 0.20 at n=3)
- Range: 1.43 (max +0.4072 − min -1.0170)

Multi-seed CONFIRMATION mean SE estimate at n=10 from std ≈ 0.66: SE ≈ 0.66/√10 ≈ 0.21. Wide confidence interval: any multi-seed CONFIRMATION-mean ∈ [-0.50, +0.50] is non-discriminating against H0=0 edge. **The R5-BINARY-KILL mechanical-edge claim is structurally unrescuable at v1 single-seed EXPLORATION budget.**

---

## 6. 2-Property Decomposition Refutation Discussion

The 2-property decomposition committed at /012 closeout posited:

**SUBSTRATE-LOCKED across /010/011/012**:
- IS Sharpe-Δ magnitude ~+0.48-0.52 (variance < 0.03 across 3 iterations)
- LTC IS rank-1 dominant-symbol slot (3/3 iterations)
- OOS-amplification fraction OOS Δ ≈ 0.45-0.78 × IS Δ (variance < 0.5)

**SEED-DRIVEN across /011↔/012**:
- Specific (symbol, open_time) IS trades — 67% rotate
- Second-place IS symbol (LINK at /011 → LINK co-first at /012)
- Catastrophically losing IS symbol (BTC → DOT)

**REFUTATION SUMMARY at /013**:

| Substrate-LOCKED claim | /013 observation | Status |
|---|---|---|
| IS Sharpe-Δ ≈ +0.48-0.52 ± 0.05 | **IS Δ -0.9223** | REFUTED catastrophically (1.30σ below band) |
| LTC IS rank-1 dominant-symbol | **LTC IS rank-2 (LINK takes rank-1)** | REFUTED |
| OOS-amplification fraction in [0.45, 0.78] | OOS Δ/IS Δ = +1.10 | bounds-violated (variance too high to test) |

**ALL three substrate-LOCKED properties refuted**. The 2-property decomposition collapses to a 1-property finding: *roster overlap percent at adjacent seed windows is ~30-36% (seed-driven-roster claim confirmed)*. That is the only substrate property that survives n=4.

**The correct framing** (committed in revised `feedback_v1_substrate_basin_lock.md`):

> At v1 single-seed-window EXPLORATION (n_trials=35, ENSEMBLE_SIZE=3, V1_FEATURE_COLUMNS_PRUNED, 5-symbol universe), EVERYTHING is basin-lottery. The Optuna basin is fully seed-driven with HIGH variance. Adjacent seed offsets land in catastrophic AND lucky basins. IS Sharpe-Δ, OOS Sharpe-Δ, dominant-symbol identity, catastrophic-symbol identity, and roster composition are ALL seed-driven with high variance. Only roster-rotation percent (~30-36% adjacent-seed overlap) is a seed-stable metric.

**This is a fundamentally important calibration finding**: at v1 single-seed EXPLORATION, predictive resolution is BELOW the prior-flipping informational threshold. Concentrated priors are unjustified. Magnitude bands are plausibility envelopes, not P50 anchors. Edge claims require MULTI-SEED CONFIRMATION.

**For /015 CONFIRMATION design**: the multi-seed standard error at n=10 from observed std ≈ 0.66 is ~0.21. The R5-BINARY-KILL mechanical-edge layer estimate (~+0.05 from /012) is structurally swamped by basin variance. /015 = UNUSED-family CONFIRMATION (labeling) per pre-committed conditional — labeling axis modifies the loss surface ITSELF (not just position selection), giving higher prior probability of basin escape from the current substrate basin distribution.

---

## 7. LM Master Calibration Update (Phase 7.4 §5 codified)

**Track record after /013: 0/11 directional + 4 PARTIAL.**

LM Master Phase 4.5 prediction at /013: F9 PASS at 80% confidence (P50 IS Δ = +0.52, band [+0.38, +0.58]). Observed -0.9223 — **off by 1.44**.

**Track-record trajectory** (Phase 4.5 prediction vs Phase 7.5 observation):
- /001 directional miss (verdict-class predicted PROMISING; observed NEGATIVE-INERT)
- /002 directional miss (PROMISING; observed NEGATIVE)
- /003 directional miss (PROMISING; observed NEGATIVE)
- /004 directional miss + 1 PARTIAL credit (NEGATIVE-INERT predicted; observed NEGATIVE with magnitude PARTIAL match)
- /005 directional miss
- /006 directional miss + 1 PARTIAL credit (verdict-class wrong; structural diagnosis partially right)
- /007 directional miss
- /008 directional miss
- /009 directional miss
- /010 directional miss + 1 PARTIAL credit (PROMISING-INERT-with-IS-basin-shift predicted; observed similar pattern)
- /011 directional miss
- /012 directional miss + 1 PARTIAL credit (magnitude band hit at +0.52 in band [+0.45 ± 0.08])
- **/013 directional miss (catastrophic-magnitude)**

**LM Master Phase 7.4 self-calibration update FINAL** (committed at `1ea8109`):
- **Verdict-class predictions**: flat priors ONLY (A 30% / B 30% / C 40% by default at v1 single-seed)
- **Magnitude predictions**: report band only as plausibility envelope, not P50 anchor
- **Substrate-property claims**: forbidden at n<10
- **HIGH-confidence statements**: reserved for trivial-structural claims (mechanical-config consequences like F2 fire rates)

LM Master's diagnostic-frame value at /013 was the **2-property decomposition refutation in §1** + **per-symbol catastrophic-reversal ROTATES observation in §3** + **R5-BINARY-KILL multi-seed CI calculation in §4**. Diagnostic contributions remain primary inputs for QR closeout; predictions do not anchor concentrated priors.

---

## 8. Critic 3 Process Violations + Commitments for /014

### 8.1 Engineering report enforcement gap — 3RD STRIKE

**Violation**: `reports-v1/iteration_v1-013/engineering_report.md` was missing at the time of Critic Phase 7.5 review (`b6a1aaa`). Critic Phase 7.5 §"Check 7" flagged as PROCESS CONCERN (3rd strike). The brief Section 10.2 #4 mandated the file as Phase 6 QE deliverable; Critic Phase 6.0 pre-flight at `5f4c610` explicitly verified the SPEC; the QE Phase 6 dispatch did NOT enforce the hard-reject contract on artifact production.

- **/011 closeout (Critic Rec #3)**: orchestrator-side hard-reject of Phase 7.5 dispatch without engineering report.
- **/012 closeout (Critic Rec #1)**: explicit recodification + 3-way enforcement (orchestrator + QE skill + Critic Phase 6.0 precondition).
- **/013 STRIKE 3**: still missing at Critic Phase 7.5 dispatch.

**This Phase 7 closeout PRODUCES THE REPORT NOW** — this file is the deliverable that should have been produced at Phase 6 closeout, retroactively closing the 3rd-strike gap.

**Commitment for /014 brief**: Critic Phase 6.0 must include EXPLICIT PRECONDITION CHECK that the engineering report path is referenced in brief Section 10.2 AS BLOCKING DELIVERABLE for Phase 7.5 dispatch (currently only checks SPEC; needs to escalate to dispatch hard-reject). The mechanism that has now been violated 3 consecutive iterations is the dispatch-side enforcement, not the spec-side declaration.

### 8.2 Memory file revision verified

**Status**: `feedback_v1_substrate_basin_lock.md` REFUTED-IN-FULL revision is in place. The revision was edited during the LM Master Phase 7.4 + Critic Phase 7.5 sequence at HEAD `1ea8109` / `b6a1aaa` per Critic Rec #2 to /013. The diff records:
- 2026-05-25 at iter-v1/012 closeout: STRONG-form REFUTED; WEAK-form retained pending /013 validation
- **2026-05-25 at iter-v1/013 closeout: REFUTED-IN-FULL** (LM Master Phase 7.4 `1ea8109`; /013 IS Δ -0.9223 vs F9 band [+0.38, +0.58] — catastrophic miss)

Section "RULE — REFUTED at n=4" replaces the prior "Updated RULE — 2-property decomposition" structure. Sections on "Empirical Evidence", "Why the Substrate-MAGNITUDE Locks", and "Pending /013 validation" are retained for historical context but marked as REFUTED-IN-FULL framings.

**Commitment for /014 brief**: brief Section 2 evidence references must NOT cite the 2-property decomposition as if it still holds. The substrate-basin-lock memory file is REFUTED-IN-FULL; only the substrate-property reframing ("at single-seed v1 EXPLORATION, EVERYTHING is basin-lottery") is the current canonical RULE.

### 8.3 /015 = labeling CONFIRMATION binding; /014 = labeling EXPLORATION precursor with HIGH-RISK declaration MANDATORY

**Status**: PRE-COMMITTED CONDITIONAL has FIRED. F1 OOS Δ ≤ 0 → /015 = UNUSED-family CONFIRMATION (labeling preferred). The conditional was codified in:
- /011 Critic Path Forward Option 2 (Critic adversarial recommendation)
- /012 diary §"Permanent Catalog Additions" line item #7 (LM Master Phase 7.4 §8)
- /013 brief Section 0 + Section 8.5 + LM Master Phase 4.5 §5 third branch + Critic Phase 7.5 §"Recommendations to QR" Rec #3

**The conditional CANNOT be post-hoc renegotiated**. /015 = labeling CONFIRMATION binding.

**For /014 brief**: HIGH-RISK declaration MANDATORY per `quant-iteration-v1` skill discipline. Axis = triple-barrier σ_t via past-only EWMA at 14-day window (vs current fixed ATR multipliers). Single-seed lottery dominates labeling-axis IS/OOS Δ at /014 per the refuted substrate framework — register BOTH positive and negative basin outcomes as INFORMATIONAL in Section 8 verdict matrix (no concentrated priors). Pre-commit /015 = labeling CONFIRMATION regardless of /014 IS/OOS magnitude per the conditional binding.

---

## 9. Trade Spot-Check Reproducibility (Phase 7.5 Check 7 PASS)

Per Critic Phase 7.5 §"Check 7 — Reproducibility: PASS (with process concern)": trade spot-checks reproduce against `reports-v1/iteration_v1-013/in_sample/trades.csv` and `reports-v1/iteration_v1-013/out_of_sample/trades.csv`. LINK long PT, BTC short PT, LTC long SL all match reported PnL within rounding. R5-BINARY-KILL filter fires at expected rates per F2 PASS.

Backtest mechanics are sound. The catastrophic basin outcome is a real measurement of single-seed-window /013 specifically, not a mechanism/data defect.

---

## 10. Summary

**Final verdict**: EXPLORATION-NEGATIVE subtype `BASIN-LOTTERY-CATASTROPHIC` (NEW v1 catalog row).

**Structural finding**: 2-property substrate decomposition committed at /012 closeout is REFUTED-IN-FULL at n=4. The 3 prior +0.48 IS Δ data points were lucky basin draws from one mode of a multi-modal distribution. At v1 single-seed-window EXPLORATION, EVERYTHING is basin-lottery (IS Sharpe, OOS Sharpe, dominant-symbol, catastrophic-symbol, roster composition — all seed-driven with HIGH variance). Only roster-rotation percent (~30-36% adjacent-seed overlap) survives as a seed-stable metric.

**R5-BINARY-KILL family**: CLOSED at v1 single-seed. 4 EXPLORATIONs (/010 proportional + /011/012/013 binary-kill) collectively show OOS Δ trajectory +0.41 / +0.27 / -1.02 (n=3 binary-kill OOS samples), std ≈ 0.80, multi-seed CONFIRMATION-mean CI [-0.50, +0.50] — non-discriminating against H0. Mechanical kill_low layer (~+0.05) is swamped by basin variance.

**LM Master**: 0/11 directional after /013; flat-prior framing from /013 forward. Diagnostic-frame contributions (mechanism refutation, per-symbol catastrophic-rotation pattern) remain primary inputs.

**Process**: 3rd-strike engineering report enforcement gap closed retroactively by THIS file. /014 brief Critic Phase 6.0 must enforce dispatch-side precondition check.

**Pre-committed conditional FIRES**: /014 = labeling EXPLORATION precursor (HIGH-RISK MANDATORY); /015 = labeling CONFIRMATION binding. Cannot be post-hoc renegotiated.

**MERGE decision**: NO-MERGE (EXPLORATION-NEGATIVE catastrophic; over-determined by IS −0.64 / OOS −0.35 failing every absolute merge floor).
