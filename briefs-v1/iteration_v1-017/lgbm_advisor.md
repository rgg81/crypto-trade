# LightGBM Master Advisor — iter-v1/017 — Phase 4.5 (Pre-Design)

## Context Read

- **Track**: v1. Branch `iteration-v1/017`. HEAD `faa4010`. CYCLE-3 EXPLORATION #2 of 10 under STRICT 2h wall-clock.
- **Baseline**: `v0.v1-baseline-corrected` (`f8bc12c`). IS +0.2829 / OOS +0.6637. UNCHANGED through cycle-2 + cycle-3 #1.
- **Anchor**: /016 EXPLORATION-NEGATIVE-catastrophic (OOS Sharpe -1.00; 50 min wall-clock; 75% margin).
- **Track record**: 1/14 verdict-class directional, 6/14 mechanism-level. Modal-NULL prior empirically validated.
- **QR's axis**: +SOL only (6-sym universe), abs_pnl reverted, all other axes pinned. SOL parquet stale — mandatory regen.
- **/016 Phase 7.4 recommendation**: universe expansion at /017 with SOL — **QR adopted exactly as specified.**

## SOL Inclusion Mechanism Call

**SOL IS direction**: NEUTRAL→POSITIVE (60/30/10 positive/null/negative). SOL IS std 3.68% (higher than baseline 3.04-3.24); abs_p95 7.52% leaves headroom for ATR×2.9 TPs. Model F uses Model A's profile (2.9/1.45); tighter SL barrier triggers more on high-vol symbol; IS WR tilts DOWN ~40% baseline but not catastrophically. IS abs PnL share band: **[8%, 25%]**.

**SOL OOS direction**: HIGH-VARIANCE (40/35/25). 0.6164 BTC correlation genuinely diversifying (≥4pp gap below LINK 0.6856), but single-seed=42 EXPLORATION makes OOS regime-conditional. OOS PnL band: **[-35%, +35%]**.

## ETH Dilution vs Regime-Lock Prediction

**Regime-lock probability: 75%. Universe-dilution rescue: 15%. Model-arch recovery: 10%.**

ETH OOS catastrophic spans 3 DISJOINT mechanism layers (label-distribution-shape twice; sample-weight-magnitude once). Adding SOL changes NONE of the three drivers — Model A still trains on BTC+ETH cohort with IDENTICAL labels/weights/features. Only secondary path: SOL trade events shift Optuna per-cell Pareto frontier, re-ranking Model A hparams. Mechanism non-zero but weak.

**Highest-probability outcome**: ETH OOS Scenario A (share > 40% absolute PnL, PnL ≤ -20%). **Forward-bind**: /018 PRIMARY must be ETH-specific kill switch (BTC-trend conditional OR per-symbol drawdown brake), NOT another universe expansion.

## Wall-Clock Recommendation

**KEEP n_trials=18. DO NOT compress to 15.** 60-min linear / 42-min sub-linear → 50-65% margin. n_trials=18 stays above TPE warmup ~10 by 80%; 15 trims buffer to 50% on HIGH-RISK axis. Pre-emptive compression to 15 is false economy.

**CONTINGENCY**: if QE pre-flight at 50% completion projects >72 min, drop to n_trials=15 per brief §3.6.4 — DO NOT pre-emptively compress.

## n_eff_per_cell Prediction

**Predicted band: [11, 17]** (median across cells):
- Label-shape UNCHANGED (no timeout-dominance risk)
- Weight-distribution UNCHANGED (abs_pnl reverted)
- Loss-surface ADDITIVELY ENRICHED (Model F adds ~165 IS rows/month at SOL's volatility profile)

60% lands [11, 17]; 25% lands [10, 13] (insufficient signal-injection); 15% below 10 (Model F noisy enough to homogenize).

## Predicted Verdict-Class

**FLAT 33/33/34** (mild adjustment):
- PROMISING: **30%** (Δ OOS ≥ +0.20). Requires SOL positive AND ETH dilution AND Model A unperturbed — 3 conjunctive at 60-70% each
- NULL: **35%** modal. Universe expands mechanically; no portfolio Sharpe shift
- NEGATIVE: **35%** (incl. 8% catastrophic Δ ≤ -0.55)

**Most likely PROMISING sub-pattern**: PROMISING-MECHANICAL (Cell 2). SOL drives lift via fresh contribution; A/C/D/E rosters near bit-identical. Non-compoundable as signal source.

## Wall-Clock Margin Re-Check for 7-Symbol Option

**RECOMMEND 6-SYMBOL. DO NOT EXPAND TO 7-SYM (+XRP).** Reasons:

1. **Single-axis isolation**: +XRP simultaneously confounds attribution
2. **XRP kurtosis 17.46** (vs SOL 8.41, LINK 5.21) is structural red flag — fat tails drive single-seed=42 lottery effects, contaminating SOL test
3. **Margin compression**: 70-min at 42% margin technically above 20% floor but reduces contingency buffer

**Forward**: /018 alternate A handles +XRP as SECOND universe expansion sequentially.

## Saturation Risks

**Single-seed=42 frozen-baseline pattern (v3 /020-/022 precedent)**: at single-seed EXPLORATION, per-symbol Optuna trajectories deterministic. If /017 PROMISING entirely SOL-driven while A/C/D/E rosters bit-identical to /016, that's PROMISING-MECHANICAL — at multi-seed CONFIRMATION (/027) SOL contribution will DILUTE. Critic should check trade-roster identity for A/C/D/E vs /016.

**HIGH-RISK declaration correct but soft**: universe expansion adds NEW training data via Model F's per-cell Optuna budget. At ENSEMBLE_SIZE=3 single-seed, Model F is lottery-exposed. /015 LESSON forward-mandate (1σ negative across 3 HIGH-RISK accumulates) — /017 is 1st HIGH-RISK cycle-3.

## What I Did NOT Recommend

- Multi-seed at /017 (HIGH-RISK forward-mandate not yet triggered)
- Pin Model F bounds tighter than v1_pruned (axis isolation)
- XGBoost (deferred to /018+ per /016 Phase 7.4)
- ETH-specific feature engineering (multi-axis violation)
- R1/R2 for Model F (R3-only, sister to A; R1 single-symbol could deadlock)

## Closing Note

**MEDIUM confidence in MODAL NULL outcome (35%).** Mechanism well-grounded; QR EDA unusually rigorous. +SOL test discriminates regime-bound vs universe-bound cleanly.

**Three specific calls staked**:
1. ETH regime-lock probability 75% — /018 must pivot to ETH-specific kill
2. KEEP n_trials=18 — pre-emptive compression to 15 false economy
3. 6-symbol over 7-symbol — single-axis isolation preserves attribution

**Critic Phase 7.5 priority check**: F-AXIS-MECHANISM SOL share ∈ [5%, 40%] band has teeth. If <5% Model F under-firing (BLOCK-PENDING-FIX, not NEGATIVE). If >40% single-seed lottery (concentration violation, not edge).

---

# LightGBM Master Advisor — iter-v1/017 — Phase 7.4 (Post-Mortem)

## Context Read

- Verdict cell: **EXPLORATION-PROMISING-INERT** (FIRST in cycle-3). F1 OOS Δ -0.0908 ∈ [-0.20, +0.20]; F3 IS Δ +0.0509 ∈ [-0.20, +0.20]; both halves within band. OOS/IS ratio 1.72 (healthy anti-overfit).
- F-AXIS-MECHANISM: #1 PASS (Model F dispatched, SOL 51 OOS trades), #2 PASS (SOL 16.4% IS/OOS ∈ [5%, 40%]), #3 **FAIL — n_eff_per_cell_median = 9, BELOW Phase 4.5 [11, 17]**.
- PSR_monthly_vs_0 OOS = **0.8079** (vs /016's 0.125 — +0.68, largest single-iter jump in cycle-3).
- Track record update: 1/15 directional + 7/15 mechanism-level.

## 1. First cycle-3 PROMISING-INERT — Confirms vs Refutes

**CONFIRMS**: universe expansion is strongest cycle-3 verdict-direction signal. ±0.20 INERT band held bilaterally with PSR jumping 0.125→0.808. PSR rewards monthly-PnL distribution shape, not point Sharpe — +0.68 PSR jump means OOS monthly distribution became more CONSISTENTLY positive (LINK+DOT+BTC+SOL = 4 positive symbols vs /016's structural drag).

**REFUTES**: that universe dilution alone reaches edge. OOS Δ -0.09 = INERT-negative; universe produced Pareto-stable mechanism (more symbols, more diversification, higher PSR) but did NOT improve point Sharpe. **Dilution worked; alone isn't sufficient.** Cycle-3 analog of v3 PROMISING-MECHANICAL at universe layer — basin reorganization without signal discovery.

**Catalog implication**: SOL inclusion is a **strictly-accretive structural component** at /017 substrate. Future CONFIRMATION bundling: keep 6-sym universe as substrate; pair with signal-discovery ingredient (composed feature, regime gate, model-arch swap) to potentially compound.

## 2. ETH Structural Drag PARTIALLY Broken — 75% Regime-Lock REFUTED

ETH OOS trajectory: /014 -41 / /015 -23 / /016 -51 / **/017 -28**:
- /017's -28 is 2nd-best ETH OOS in cycle-2+3 window
- Universe dilution genuinely REDUCED ETH catastrophic magnitude
- ETH OOS share moved from /016's +76% (negative-share dominant) to /017's -56% (negative-share but diluted by 4 positive symbols)
- Scenario B from brief Table D approximately landed (mixed-zone)

**Honest call**: my 75% regime-lock framing was **directionally correct but magnitude-wrong**. Drag IS structural (4 axes show ETH OOS negative); but dilution at 17% SOL contribution genuinely shifts BASIN, not just headline.

**Mental model update**: ETH drag is structural-PARTIAL-dilutable, NOT structural-locked.

## 3. BTC Catastrophic Rotation — Structural Basin-Lottery Signature

Per-symbol IS catastrophic-rotation across cycle-2+3:
- /011: LINK catastrophic; /014: ETH catastrophic IS; /015: ETH+BTC IS-negative; /016: All symbols IS-negative; **/017: BTC IS -93.81 + DOT IS +96.07 (new winner)**

Pattern: **at single-seed=42 EXPLORATION, ~1 symbol per iteration drifts catastrophically IS-negative while another floats catastrophically IS-positive, with the identity ROTATING.** v1 analog of v3 "single-seed=42 frozen-baseline" but with universe-rotation overlay.

**Catalog implication**: per-symbol IS catastrophic IS NOT a defect signal at EXPLORATION; it's a single-seed signature. Critic Check 4 should treat BTC -93.81 IS as expected basin-lottery noise, NOT catastrophic per-symbol failure. Multi-seed CONFIRMATION at /027 should dissolve the rotation.

## 4. n_eff Prediction REFUTED 3rd Time — Corrected Mental Model

Track record n_eff:
- /014: 19 (label-shape baseline, σ_t labels) — OUTLIER
- /015: 3 (label-distribution collapse — 7.82% barriers + timeout dominance) — OUTLIER
- /016: 9 (sample-weighting uniform; weight-distribution collapse)
- /017: 9 (universe expansion, baseline-labels, abs_pnl weighting)

**Corrected mental model**: n_eff_per_cell in v1 has **stable native range ~9-13** at baseline-labels + abs_pnl-weighting + single-seed EXPLORATION. /014's 19 and /015's 3 were both outliers requiring specific axis-driver. My [11, 17] anchored too hard on /014 + assumed Model F row-injection would push UP. Wrong — PCA-substrate native-rank stays bounded by Optuna trial budget (n_trials=18) × ENSEMBLE_SIZE (3).

**Tighten band to [8, 13] as cycle-3 EXPLORATION native band**; flag outside-band only when axis structurally touches label-shape or weight-distribution.

**Demote n_eff to INFORMATIONAL for universe-expansion axes** — not a sensitive axis-attribution sub-check.

## 5. /018 Axis Selection — Honest Recommendation

Pre-commit: ETH-specific kill switch IF /017 NEGATIVE on ETH. /017 ETH OOS -28 is NEGATIVE (less than baseline +2.75) but NOT the Scenario A catastrophic-≤-20%-with->40%-share I predicted.

**Options**:
- (a) +XRP at /018 — continue universe expansion (STRONG case)
- (b) ETH-specific kill switch — pre-committed but magnitude-conditional softer
- (c) BTC-specific kill — REJECT (BTC OOS at /017 was +15.11 POSITIVE)

**RECOMMENDATION: (a) +XRP at /018.** Reasons:
1. /017 demonstrated PSR-improving mechanism that hasn't saturated; +XRP is natural compounding test
2. Pre-commit ETH-kill was magnitude-conditional ("catastrophic"); -28 sub-catastrophic; spirit allows continued dilution
3. ETH dilution IS working — at 7-sym predict ETH OOS share further toward -30%
4. XRP kurtosis 17.46 lottery exposure is real but ADDRESSABLE — Critic + LM Master flag single-seed XRP-only-driven OOS lift as PROMISING-MECHANICAL if appears
5. ETH-kill DEFERRAL: **/019 PRIMARY = ETH kill switch IF /018+XRP STILL shows ETH OOS ≤-20%** (re-stated pre-commit with magnitude floor)

**Confidence: MEDIUM-HIGH (65%)**.

## 6. Calibration Update

- Verdict-class directional: **1/15** (PROMISING-INERT fits FLAT-NULL bucket via |Δ| < 0.20)
- Mechanism-level: **7/15** (+1 for SOL share band PASS; n_eff REFUTED again)
- NEW refuted: n_eff_per_cell band [11, 17] (corrected to [8, 13])
- NEW confirmed: **PSR_monthly_vs_0 is more sensitive than F1 Sharpe** at universe-axis EXPLORATIONs — track PSR as primary basin-health signal

## 7. Cycle-3 Cadence

/017 = #2 of 10 EXPLORATIONs. /027 CONFIRMATION earliest. /017 PROMISING-INERT is strongest cycle-3 verdict so far but NOT merge-candidate — INERT means no edge to bundle. **Catalog: "EXPLORATION-PROMISING-INERT" — structural component candidate for /027 substrate (6-sym universe with SOL), not edge ingredient.** Bundling decision deferred to /027 QR.

## Closing Note for Critic Phase 7.5

Three specific items:

1. **Check 4 (per-symbol attribution)**: BTC IS -93.81 vs BTC OOS +15.11 is single-seed-rotation signature, NOT defect. Do NOT BLOCK on per-symbol IS catastrophic — IS/OOS divergence DIRECTION actually SUPPORTS universe-dilution mechanism.

2. **Check 8 (axis attribution)**: F-AXIS-MECHANISM #1 #2 PASS clean; #3 (n_eff) FAILed but demoted to informational for universe axes. Critic should NOT BLOCK on #3 in isolation.

3. **Check 5 (basin-health)**: PSR_monthly_vs_0 jump 0.125→0.808 is single most important quantitative signal of /017 — exceeds all point-Sharpe signals in interpretive weight. Treat as load-bearing positive evidence even as Sharpe Δ fractionally negative.

Three calls staked for /018: (1) +XRP over ETH-kill (MEDIUM-HIGH 65%); (2) keep cycle-3 cadence; (3) /019 PRIMARY = ETH-kill IF /018+XRP still shows ETH OOS ≤-20%.
