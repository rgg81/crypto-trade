# Iteration iter-v3/061 — Diary

## Decision: INERT-AT-EXPLORATION — EXPLORATION-MERGE; TRX RiskV2 anti-Kelly axis CLOSED for cycle 1 carry-forward

iter-v3/061 is **cycle 1 EXPLORATION #2 of 10** and the **first per-symbol risk-primitive customization EXPLORATION in v3 history** (Path B: `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` per QR EDA `d198b25` + Critic /060 Rec #3). Per Critic FINAL `b20b554`: **OVERALL: EXPLORATION-MERGE — INERT-AT-EXPLORATION certified clean** (13/13 methodology checks PASS or PASS-equivalent; §11 Anti-Pattern Static Scan CLEAN; 5 Path B-specific concerns dispositioned). The IS shift -0.009 and OOS shift +0.015 vs /060 anchor sit squarely inside the cycle 1 noise band (PROMISING requires IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20). The /060 EDA Q7 Welch-t-NON-significant anti-Kelly finding was confirmed null in flight: 12 OOS floor-fired trades produced a clean 6w/6L split with +0.59 wpnl net — within the counterfactual band but Sharpe-invisible. **BASELINE_V3.md is UNCHANGED** — /059 stays canonical (CONFIRMATIONs are the only iterations that update baseline per `feedback_v3_baseline_update_policy.md`). vol_scale_floor_per_symbol code is RETAINED in the codebase (1 field + 1 lookup line; structurally isolated; backward-compatible default; near-zero revert cost).

## Section 1 — What Was Done

### EDA commit `d198b25`

`analysis/iteration_v3-061/trx_anti_kelly_diagnostic.py` produced 6 numerical tables addressing the /060 Critic Rec #3 mandate to diagnose TRX RiskV2 anti-Kelly:

- **Q1** Anti-Kelly significance: Method A (net_pnl_pct > 0) shows TRX IS win_w − loss_w = -0.061 but Welch t=-0.49 with 95% CI [-0.154, +0.088] **includes 0** — non-significant. Method B (weighted_pnl > 0, excludes BTC-killed zero-weight trades) reduces the gap to -0.034 with 95% CI [-0.130, +0.062] — still non-significant.
- **Q2** TRX weight-bucket distribution by outcome: 26.3% of wins vs 19.2% of losses fall below the wf=0.5 bucket — modest win-skew below the floor candidate.
- **Q3** TRX outcome-by-weight-bucket: counts and win rates per bucket; floor=0.5 candidate amplifies 14 IS trades (8 win, 6 loss) and an estimated 12 OOS trades.
- **Q4** Counterfactual floor sensitivity: floor=0.5 IS counterfactual wpnl Δ = +0.008; OOS counterfactual = +0.47.
- **Q5** Cross-symbol floor sensitivity (BCH+LDO non-target): zero predicted change (per-symbol dict isolation).
- **Q6** Path-decision summary: Path B (target floor=0.5 on TRX only) chosen over Path A (passive observation), C (universal floor=0.5), D (kill-symbol), E (vol-target ceiling).

### Setup commit `af92efe` (brief LOCKED)

Brief `briefs-v3/iteration_v3-061/research_brief.md` (40.5KB) LOCKED. Key sections:
- Section 0.5 TYPE = EXPLORATION (cycle 1 #2 of 10)
- Section 2 EDA narrative pointing to `d198b25` artifacts
- Section 3 substantive edits enumeration (5 items)
- Section 4 expected impact + Q4 counterfactual reference
- Section 4.3 behavioral effect predictor table
- Section 4.4 falsifier list (5 binding gates: IS Sharpe shift > -0.20; OOS Sharpe shift > -0.10; BCH IS share ≥ 80%; trade-count bands; BCH/LDO |wpnl Δ| < 1.0)
- Section 7 failure-mode probabilities (~55% INERT pre-registered as MOST-LIKELY outcome)
- Section 8 LOCKED PASS criteria with 8 hard-blocking gates

### Code commit `6910fcf`

1. `src/crypto_trade/strategies/ml/risk_v2.py:151` — `vol_scale_floor_per_symbol: dict[str, float] = field(default_factory=dict)` (new RiskV2Config field; backward-compatible default empty dict)
2. `src/crypto_trade/strategies/ml/risk_v2.py:608-610` — per-symbol floor lookup with `np.clip` applied AFTER the existing vol-scale formula, INSIDE `_vol_scale`, AFTER all kill-gates in `get_signal`. Trade-selection invariance is mechanical.
3. `run_baseline_v3.py:1489` — `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` injected at `_build_v3_model`.
4. `run_baseline_v3.py:745-752` — runtime assertion `isinstance(cfg.vol_scale_floor_per_symbol, dict)` fires per model build; cannot silently fall through.
5. `tests/strategies/ml/test_per_symbol_vol_scale_floor.py` — 3 NEW tests (default empty dict; per-symbol lookup; floor clip behavior). Test suite 34/34 PASS.
6. `ITERATION_LABEL = "v3-061"` at line 128.

### Phase 5.5 gate `17eea9a`

Phase 5.5 audit OVERALL=PASS at HEAD `17eea9a`. Re-verified: (i) walk-forward fix at `walk_forward.py:113` intact; (ii) embargo computation correct; (iii) labeling unchanged; (iv) per-symbol floor field present at risk_v2 line 151; (v) runtime assertion present at runner line 745-752; (vi) test suite 34/34. Pre-run state clean.

### Phase 6 backtest

Run command: `uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 35`. Wall-clock: **0.69h** (under 1.1h target; consistent with /060's 0.69h). PID 487310; log at `logs/iter-v3-061.log`. Engineering report at SHA `870f9f1`; Critic review at SHA `b20b554`.

---

## Section 2 — Results Table vs /060 Anchor

### Multi-anchor headline comparison

| Metric | /059 CONFIRMATION (10-seed) | /060 EXPLORATION anchor (3-seed) | **/061 (3-seed)** | Δ vs /060 |
|---|---:|---:|---:|---:|
| **IS monthly Sharpe** | +1.0894 | +0.8325 | **+0.8236** | **-0.009** (within noise band) |
| **OOS monthly Sharpe** | +0.5791 | +0.1403 | **+0.1551** | **+0.015** (within noise band) |
| IS daily Sharpe | +2.7092 | +1.7115 | +1.7028 | -0.009 |
| OOS daily Sharpe | +1.4359 | +0.3659 | +0.4050 | +0.039 |
| OOS/IS monthly ratio | 0.5316 | 0.1685 | 0.1883 | +0.020 |
| OOS MaxDD | 34.53% | 35.78% | 35.89% | +0.11pp |
| OOS Calmar | 0.6585 | 0.1537 | 0.1698 | +0.016 |
| OOS Profit Factor | 1.2107 | 1.0482 | 1.0530 | +0.005 |
| OOS Win Rate | 38.3% | 39.22% | 39.22% | 0.0pp |
| frac_positive_paths (CPCV) | 0.6444 | 0.6444 | **0.6444** | **0.000 (architecture-invariant)** |
| PBO | 0.1278 | 0.1278 | **0.1278** | **0.000 (architecture-invariant)** |
| CPCV path Sharpe Q75 | 0.8378 | 0.8378 | **0.8378** | **0.000 (architecture-invariant)** |
| PSR | 1.0000 | 0.9763 | **0.9861** | +0.010 (informational at EXPLORATION mode) |
| DSR_relative | 0.1134 | 0.0000 | 0.0000 | 0.000 (informational; carried artifact) |
| IS Trades | 171 | 159 | **159** | **0 (BCH+LDO bit-identical; TRX same count)** |
| OOS Trades | 94 | 102 | **102** | **0 (BCH+LDO bit-identical; TRX same count)** |
| IS total wpnl | 78.18 | 51.89 | **51.73** | -0.16 |
| OOS total wpnl | 22.74 | 5.50 | **6.09** | +0.59 |
| n_trials_total | 1050 | 315 | **315** | 0 |
| n_eff | 19 | 19 | 19 | 0 (architecture-invariant) |
| Wall-clock | 3.60h | 0.69h | **0.69h** | 0 (consistent) |

### Hard-blocking PASS gates (per brief Section 8 LOCKED)

| Gate | Threshold | /061 Observed | Status |
|---|---|---:|---|
| IS Sharpe shift > -0.20 | > -0.20 | **-0.009** | **PASS** (cushion +0.19) |
| OOS Sharpe shift > -0.10 | > -0.10 | **+0.015** | **PASS** (cushion +0.12) |
| BCH IS share ≥ 80% (one-sided lower; per /060 Rec #1) | ≥ 80% | **176.68%** | **PASS** |
| cpcv_frac_positive_paths ≥ 0.50 | ≥ 0.50 | **0.6444** | **PASS** (architecture-invariant) |
| BCH/LDO |IS+OOS wpnl Δ| < 1.0 (per-symbol isolation) | < 1.0 | **0.000 / 0.000** | **PASS** (bit-identical) |
| IS trade count in [128, 222] | 128-222 | **159** | **PASS** |
| OOS trade count in [66, 122] | 66-122 | **102** | **PASS** |
| ensemble_summary.json mode + size | mode="exploration", size=3 | **mode="exploration", size=3** | **PASS** |
| Tests 34/34 pass | 34/34 | **34/34** | **PASS** |

All 9 PASS gates clear with no falsifier triggered.

---

## Section 3 — Per-Symbol Decomposition + BCH/LDO Bit-Identity Proof + TRX Mechanical Floor-Fire

### IS decomposition (/060 → /061)

| Symbol | /060 IS wpnl | /061 IS wpnl | Δ | /061 trades | /061 WR |
|---|---:|---:|---:|---:|---:|
| **BCH** | **+78.3438** | **+78.3438** | **0.000000 (BIT-IDENTICAL)** | 73 | 45.2% |
| **LDO** | **-1.6640** | **-1.6640** | **0.000000 (BIT-IDENTICAL)** | 11 | 27.3% |
| **TRX** | -24.79 | **-24.95** | **-0.161** (floor-fire on 13 IS trades; 4 win / 9 loss; losses amplified slightly more than wins → modest IS regression) | 75 | 29.3% |
| **Portfolio total** | +51.89 | **+51.73** | -0.16 | 159 | 31.4% |

### OOS decomposition (/060 → /061)

| Symbol | /060 OOS wpnl | /061 OOS wpnl | Δ | /061 trades | /061 WR |
|---|---:|---:|---:|---:|---:|
| **BCH** | **+1.9077** | **+1.9077** | **0.0000 (BIT-IDENTICAL)** | 37 | 32.4% |
| **LDO** | **-19.7208** | **-19.7208** | **0.0000 (BIT-IDENTICAL)** | 11 | 18.2% |
| **TRX** | +23.31 | **+23.91** | **+0.5943** (floor-fire on 12 OOS trades; 6 win / 6 loss; win-magnitude dominates → +0.59 net wpnl) | 54 | 50.0% |
| **Portfolio total** | +5.50 | **+6.09** | +0.59 | 102 | 39.22% |

### TRX floor-fire mechanical breakdown

The vol_scale_floor=0.5 fired for TRX on exactly **12 OOS trades** (and **13 IS trades**) where the underlying atr_pct_rank_200 mapped to a weight below 0.50 under the global floor=0.3. All such trades had weight_factor lifted to exactly 0.50 in /061.

**OOS floor-fire outcome breakdown:**

| Outcome | Count | Wpnl contributions | Total wpnl |
|---|---:|---|---:|
| WIN | 6 | +0.3809, +0.0907, +0.3689, +0.2480, +0.0577, +0.2335 | **+1.3797** |
| LOSS | 6 | -0.2281, -0.0634, -0.2486, -0.0865, -0.0506, -0.1082 | **-0.7854** |
| **Net** | **12** | — | **+0.5943** |

Average weight_factor on TRX OOS trades after floor application:
- Wins (n=26): mean=0.7185
- Losses (n=28): mean=0.6532
- **Delta (wins − losses): +0.0653** — Kelly-aligned direction (reversed from /060's weak anti-Kelly under Method A)

The 6w/6L equal-split confirms the brief Section 1 "more OOS winners lifted than losers" prediction (Q2 frac_below_05: 26.3% wins vs 19.2% losses) did NOT hold — the counterfactual overpredicted the win-skew in the floor-fired bucket. Per the engineering report at `870f9f1`, this is mechanically explainable: the small sample (12 trades) is dominated by win-magnitude rather than win-count.

### Per-symbol design isolation: HELD exactly

The empirical zero-delta on BCH+LDO across both IS and OOS is the strongest possible evidence of per-symbol vol_scale_floor_per_symbol dict isolation. The `_vol_scale` method reads `self.config.vol_scale_floor_per_symbol.get(symbol, self.config.vol_scale_floor)` per-signal; the dict lookup pattern is mechanically zero-leakage by construction; the empirical verification at trade-row level confirms zero cross-symbol contamination.

### OOS concentration values

BCH 31.31% / LDO -323.64% / TRX +392.33% reflect the OOS portfolio total being near zero (+6.09 wpnl), making percentage attribution numerically unstable. Same structural dynamic was present at /060 (TRX = +423.94%). Not a bug — expected behavior when portfolio is near-zero.

---

## Section 4 — Critic Verdict Summary

Per Critic FINAL `b20b554`: **OVERALL: EXPLORATION-MERGE — INERT-AT-EXPLORATION certified clean** (13/13 methodology checks PASS or PASS-equivalent; §11 Anti-Pattern Static Scan CLEAN; 5 Path B-specific concerns dispositioned).

### Methodology checks (13 of 13 PASS or PASS-equivalent)

| Check | Status | Notes |
|---|---|---|
| 1 Look-Ahead Audit | PASS | walk_forward.py:113 fix intact; embargo 22 candles; new code path at risk_v2.py:608 is static-config (no historical-data access) |
| 2 Embargo Width | PASS | REQUIRED_GAP=66=(21+1)×3; vol_scale_floor field is post-training-time runtime config; disjoint from embargo plumbing |
| 3 Multiple-Testing Correction | PASS (informational) | All hard-blocking gates per Section 8.1 + Section 4.4 LOCKED CLEAR; DSR_relative=0.0 + Legacy DSR=0.0 + PSR=0.9861 informational per `feedback_v3_dsr_mode_artifact.md`; n_trials accounting verified (315=35×3×3) |
| 4 IC Correlation | PASS | No new features at /061; matrix identical-by-construction to /060 |
| 5 ADF Stationarity | PASS | Identical-by-construction to /060 |
| 6 Pareto Dominance | PASS | Gate 10-CPCV; frac_positive_paths 0.6444 ≥ 0.50 cleared; ensemble_summary.json mode="exploration" size=3 seeds verified |
| 7 Reproducibility | PASS | All commit SHAs verifiable; trade-math spot check on 4 OOS trades matches CSV to 4dp; Row 3 TRX SHORT wf=0.5000 (floor-fired) verified: weighted = 3.8091 × 0.5 = 1.90455 matches CSV 1.9046; BCH OOS rows BIT-IDENTICAL to /060 verified row-by-row |
| 8 Hypothesis-Implementation Alignment | PASS (with Q4 counterfactual-miss disposition) | 5 substantive edits verified; Q4 IS counterfactual +0.008 → observed -0.161 (20× miss with sign flip); NOT a methodology violation since Section 4.4 binding gate (IS Sharpe shift > -0.20) PASSES with cushion +0.19; Recommendation #3 codifies per-symbol Δ falsifier discipline for future briefs |
| 9 Symbol Exclusion | PASS | V3_EXCLUDED_SYMBOLS unchanged |
| 10 Feature Isolation | PASS | features_v3/ unchanged |
| 11 Forming-Candle | PASS | 3.2h lag at gate time |
| 12 Library Version | PASS | UNCHANGED from /060 |
| 13 Per-symbol vol_scale_floor wiring + behavioral audit (NEW Path B) | PASS | Floor clip applied AFTER existing vol-scale formula VERIFIED; no leakage to non-target symbols VERIFIED at 3 levels (dict `.get` fallback; isolation test; empirical zero-delta BCH+LDO); per-symbol config dict consistently read; code RETAIN justified (backward-compatible; small footprint; parallel to existing adx_threshold_per_symbol precedent); 6w/6L floor-fired OOS pattern + Welch-t-NON-significant from /060 Q7 confirms null hypothesis on TRX RiskV2 anti-Kelly — **TRX RiskV2 anti-Kelly axis CLOSED for cycle 1 carry-forward** |

### §11 Anti-Pattern Static Scan (A1-A13): CLEAN

A1 (train_end leak), A2 (Optuna n_jobs=2), A3 (master-data invariance), A4 (track isolation), A5/A6/A7 (identical to /060), A8 (stateful gate deadlock — Path B is STATELESS by construction), A9 (ensemble_seeds threading), A10 (feature isolation), A11 (V3_EXCLUDED_SYMBOLS), A12 (DSR/PSR granularity — flagged informational; iter-v3/062 axis addresses), A13 (written-before-read) — all PASS.

Path B-specific anti-pattern audit: No silent global-shadow on `floor` variable; no side-channel into trade selection; no interaction with disabled state primitives.

### 5 Path B-specific concerns dispositioned

1. **Trade-selection invariance**: VERIFIED at trade-row level (BCH+LDO bit-identical IS+OOS to 0.000000 floating-point precision).
2. **vol_scale_floor_per_symbol dict default safety**: VERIFIED (`field(default_factory=dict)` produces fresh per-instance empty dict; lookup pattern `dict.get(symbol, fallback)` is zero-leakage by construction).
3. **Runtime assertion teeth**: VERIFIED (`isinstance(cfg.vol_scale_floor_per_symbol, dict)` fires per model build at runner line 745-752; cannot silently fall through).
4. **Test suite coverage 34/34**: VERIFIED (3 new tests for default empty dict, per-symbol lookup, floor clip behavior; existing 31 unchanged).
5. **DSR_relative=0.0 artifact**: carried from /060; not a /061 defect; iter-v3/062 axis addresses.

### Adversarial Adjudication — Q4 counterfactual miss vs binding-gate PASS

Brief Section 2.4 Q4 IS counterfactual +0.008 → observed -0.161 wpnl. 20× magnitude miss with sign flip. **Adjudication**: NOT a methodology violation. Q4 was a partition-Method-B-restated counterfactual; not a deterministic claim. Pre-registered Section 4.4 falsifier list does NOT bound TRX IS wpnl Δ explicitly. IS Sharpe shift gate (-0.20 lower) is the binding macro-level gate at -0.009 observed — PASS with cushion +0.19. Process-level Critic Recommendation #3 codifies the per-symbol Δ band falsifier discipline for future briefs.

---

## Section 5 — PATH Classification: INERT-AT-EXPLORATION

Per the Critic taxonomy at `feedback_v3_cycle1_axis_pass_criteria.md`:

- IS Δ -0.009 within noise band [-0.10, +0.10] → INERT-AT-EXPLORATION
- OOS Δ +0.015 within noise band [-0.20, +0.20] → INERT-AT-EXPLORATION
- frac_positive_paths 0.6444 ≥ 0.50 → PASS (CPCV gate cleared)
- No methodology FAIL (13/13 PASS)
- Neither PROMISING (IS ≥ +0.10 AND OOS ≥ +0.20) nor NEGATIVE (IS < -0.10 OR OOS < -0.20)

**The TRX RiskV2 anti-Kelly axis does NOT advance to cycle 1 CONFIRMATION** at iter-v3/069 (or later). The mechanism worked mechanically (12 OOS floor-fired trades confirmed with +0.59 wpnl net positive direction) but the Sharpe-level effect (+0.015) is below the 3-seed stochastic noise floor. The pre-registered ~55% INERT probability fired as predicted in brief Section 7.

**vol_scale_floor_per_symbol code is RETAINED in the codebase**: 1 field + 1 lookup line on RiskV2Config; structurally isolated; backward-compatible default empty dict; parallel to existing `adx_threshold_per_symbol` precedent; near-zero revert cost; preserves optionality for future per-symbol risk-primitive calibration cycles. This is consistent with v3 catalog precedent for INERT-but-non-destructive code paths.

---

## Section 6 — Hypothesis Check: /060 Q7 Anti-Kelly Falsified Confirmed

### /060 Q7 EDA finding (Method A — net_pnl_pct > 0)

TRX was the ONLY symbol where average RiskV2 vol-scaling weight_factor on winning trades < average weight_factor on losing trades:

| Symbol | IS win_w − loss_w | OOS win_w − loss_w |
|---|---:|---:|
| BCH | +0.099 (Kelly-aligned) | +0.072 |
| LDO | +0.222 (strongly Kelly-aligned) | +0.189 |
| **TRX** | **-0.061 (anti-Kelly)** | **-0.014 (anti-Kelly)** |

### /061 EDA Method B re-analysis (weighted_pnl > 0; excludes BTC-killed zero-weight trades)

| Symbol | Method A gap | Method B gap | Welch t (Method B) | 95% CI (Method B) | Significant? |
|---|---:|---:|---:|---|---|
| BCH | +0.099 | +0.071 | +1.18 | [-0.047, +0.190] | NO |
| LDO | +0.222 | +0.218 | +1.05 | [-0.198, +0.633] | NO |
| **TRX** | **-0.061** | **-0.034** | **-0.49** | **[-0.130, +0.062]** | **NO** |

### /061 backtest direction (post floor=0.5 application)

| Symbol | OOS Win weight_factor | OOS Loss weight_factor | Delta (wins − losses) | Direction |
|---|---:|---:|---:|---|
| **TRX** | **0.7185** | **0.6532** | **+0.0653** | **Kelly-aligned (reversed)** |

The Method B 95% CI [-0.130, +0.062] **includes 0** — the /060 Q7 anti-Kelly finding is NON-SIGNIFICANT statistically. The /061 6w/6L floor-fired OOS split confirms the null: no Sharpe-level edge to extract from per-symbol vol_scale_floor on TRX. The "anti-Kelly" pattern was a partition-method artifact (Method A included BTC-killed zero-weight trades; Method B's clean partition collapses the apparent effect).

### Counterfactual prediction vs observed

| Metric | Q4 counterfactual prediction | Observed | Direction |
|---|---|---:|---|
| TRX IS wpnl Δ | +0.008 | -0.161 | 20× miss with sign flip — but within Section 4.4 binding gate |
| TRX OOS wpnl Δ | +0.47 | +0.59 | upper-band of [+0.3, +0.6] prediction range |
| Floor-fire trade count (OOS) | ≥ 5 | 12 | PASS (mechanically larger than predicted) |
| Floor-fire trade count (IS) | ≥ 5 | 13 | PASS |
| BCH IS wpnl Δ | 0 ± 0.5 | 0.000 | PASS (per-symbol isolation) |
| LDO IS wpnl Δ | 0 ± 0.5 | 0.000 | PASS (per-symbol isolation) |

The IS wpnl Δ counterfactual was the only material miss — a 20× magnitude miss with sign flip — but did NOT trigger any pre-registered falsifier. Per Critic Recommendation #3, the process discipline for per-symbol counterfactual EDA briefs has been formalized (see Section 9 below).

---

## Section 7 — BASELINE_V3.md Status: UNCHANGED

**Per `feedback_v3_baseline_update_policy.md` and Critic FINAL `b20b554`:** BASELINE_V3.md is NOT updated by /061.

| Reference type | Anchor | Numerical values |
|---|---|---|
| **BASELINE_V3.md** (canonical CONFIRMATION-mode) | **iter-v3/059** | **IS +1.0894 / OOS +0.5791** (10-seed unified) |
| **Cycle 1 EXPLORATION-mode anchor** (parallel reference) | **iter-v3/060** | **IS +0.8325 / OOS +0.1403** (3-seed) |
| **iter-v3/061** | INERT-AT-EXPLORATION | IS +0.8236 / OOS +0.1551 (within /060 noise band) |

The /059 tag `v0.v3-059` remains the canonical baseline tag; no new tag is issued for /061. BASELINE_V3.md content is UNCHANGED. Cycle 1 EXPLORATIONs do not update BASELINE_V3.md — only CONFIRMATIONs do per `feedback_v3_baseline_update_policy.md`. The cycle 1 CONFIRMATION at iter-v3/069 (or later) must clear /059's CONFIRMATION-mode numbers to update BASELINE_V3.md.

---

## Section 8 — Critic Recommendations Carried Forward

Per Critic FINAL `b20b554` Recommendations (3 items carried forward to cycle 1 #3+):

### Recommendation #1 — iter-v3/062 axis = DSR_relative threshold/benchmark recalibration

Carried from /059 Critic FINAL `0fc18c2` Rec #1, restated by Engineer Recommendation #1 at /061. The dsr_relative=0.0 + cpcv_path_sharpe_q75=0.838 mismatch is now a 3-iteration-stale artifact (/059, /060, /061). Address via either:

- (a) Recalibrate DSR_relative threshold from 0.95 → 0.50-0.60 under unified architecture (gate softening); OR
- (b) Reformulate the input-granularity match (annualize trade-level Sharpe OR de-annualize path Sharpe so both inputs to psr() share scale)

Per `feedback_v3_methodology_post_hoc_input_traceback.md` mandate, all DSR_relative input variables must be traced to exact runner code paths in /062 brief Section 4.4.

### Recommendation #2 — iter-v3/063 = MASS FEATURE EXPANSION

Per `feedback_v3_mass_feature_expansion.md` (updated to "CYCLE 1 #4" per the strict 10:1 cadence; previously queued as "CYCLE 5 first EXPLORATION"). Engineer Rec #2 at /061 confirmed. QR mandated to research papers/literature for production-grade features (TA-lib, microstructure, cross-asset, regime, statistical, etc.) and elevate V3_FEATURE_COLUMNS_TOP_N from 14 to TARGET 100 (50 minimum). Per Critic /060 Rec #2 emphasis that /060 anchor with 2-of-3 symbols IS-negative is fragile, structural feature expansion is the cleanest path to lifting all-symbols-IS-positive multi-seed.

### Recommendation #3 — NEW process rule: per-symbol target-axis wpnl Δ falsifier band

The /061 brief pre-registered BCH/LDO IS+OOS bands at ±1.0 wpnl but did NOT pre-register a TRX IS wpnl band — the Q4 +0.008 estimate became implicit-acceptance when observed -0.161 (20× miss with sign flip). Engineer cited "Section 4.3 falsifier band |delta| < 1.0" loosely — that band was the BCH/LDO row, not a TRX IS row. The headline Sharpe gate (IS shift > -0.20) caught the macro-level fail-safe, but the target-symbol axis was unbound.

Future per-symbol counterfactual EDA briefs (Path B/C/D/E single-symbol interventions) MUST pre-register a target-symbol-axis wpnl Δ falsifier band so the Q-counterfactual-vs-observed gap has a formal gate (not implicit acceptance). New memory rule at `feedback_v3_per_symbol_target_axis_falsifier.md` formalizes this discipline.

---

## Section 9 — Next Iteration Ideas (Cycle 1 — iter-v3/062 onward)

Per `feedback_v3_strict_10_to_1_cadence.md` and `feedback_v3_cycle1_axis_pass_criteria.md`: cycle 1 = 10 SEPARATE single-seed/3-seed EXPLORATIONs at iter-v3/060-068; iter-v3/069 = SEPARATE CONFIRMATION.

### Proposed iter-v3/062 — DSR_relative threshold/benchmark recalibration (Rec #1)

Methodology-only EXPLORATION addressing the 3-iteration-stale DSR_relative=0.0 + cpcv_q75=0.838 mismatch:

- QR-driven EDA on /059 + /060 + /061 + /050 + /028 historical reports to characterize the unified-roster Sharpe distribution under CONFIRMATION-mode
- Test reformulation candidates: (a) threshold recalibration 0.95 → 0.50-0.60; (b) input-granularity match (annualize trade-level OR de-annualize path Sharpe so both inputs to psr() share scale); (c) alternative benchmark (CPCV-Q50 or CPCV-Q60 instead of Q75)
- Per `feedback_v3_methodology_axis_integration_test.md`, end-to-end smoke test in brief Section 9 + 6th integration test in test suite REQUIRED
- Per `feedback_v3_methodology_post_hoc_input_traceback.md`, post-hoc band predictions for methodology-axis gates MUST specify exact runner code path computing each input variable + granularity (daily vs trade-level vs annualized)

### Proposed iter-v3/063 — MASS FEATURE EXPANSION (Rec #2)

Cycle 1 #4 per `feedback_v3_mass_feature_expansion.md`. QR mandated to research production-grade features:
- TA-lib library (RSI, MACD, ADX variants, OBV, Williams %R, CCI, momentum, etc.)
- Microstructure features (taker-buy-ratio, large-trade ratio, mark-vs-index basis, funding rate momentum)
- Cross-asset features (BTC dominance momentum, BTC/ETH correlation, perp-spot basis)
- Regime features (Hurst, ADF p-value, volatility regime, ATR percentile)
- Statistical features (cross-symbol correlation, conditional volatility, returns autocorrelation)
- Composed features per `feedback_v3_engineered_features_proven.md` (regime_momentum_signed_5d precedent)

Elevate V3_FEATURE_COLUMNS_TOP_N from 14 to TARGET 100 (50 minimum). Per `feedback_v3_engineered_features_dont_stack.md`, test ONE engineered feature alone at single-seed EXPLORATION (don't stack at EXPLORATION; stacking experiments deferred to multi-seed CONFIRMATION).

### Proposed iter-v3/064-068 — remaining cycle 1 EXPLORATIONs

To be determined by QR EDA-driven discipline (per `feedback_v3_axis_selection_quant_discipline.md`). Candidate axes (TBD ranking; subject to /062 + /063 outcomes):
- LDO diagnostic axis (LDO is the worst single-symbol OOS in v3 history at /060 — -19.72; 5th+ consecutive negative OOS)
- BCH-specific axis to reduce IS concentration without sacrificing BCH OOS (per /059 Critic Rec #3)
- Per-symbol risk-primitive customizations beyond vol_scale_floor (e.g., per-symbol drawdown brake stateful; orthogonal mechanisms per `feedback_v3_concentration_is_signal.md`)
- NEW labeling architecture (return-based or volatility-adjusted alternatives)
- NEW model architecture (alternative tree growth, drawdown-penalized objective)
- Universe expansion candidates subject to V3_EXCLUDED_SYMBOLS constraint

### Proposed iter-v3/069 — Cycle 1 CONFIRMATION

Multi-seed validation of cycle 1 PROMISING bundle. Spec: `--n-trials 35` per cell, ENSEMBLE_SIZE=10 (CONFIRMATION mode — no --exploration flag), full DSR/PBO/PSR re-eval. PASS gates per `feedback_v3_strict_both_is_oos_baseline.md`: BOTH IS Sharpe AND OOS Sharpe must improve over /059's +1.0894 / +0.5791 anchor; Gate 3 OOS/IS ≥ 0.5; Gate 6 PSR > 0.95; Gate 10-CPCV frac_positive_paths ≥ 0.55. 6h hard cap.

### Cycle 1 axis-PASS classification bands (per `feedback_v3_cycle1_axis_pass_criteria.md`)

- **PROMISING-AT-EXPLORATION**: IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 vs /060 anchor AND frac_positive_paths ≥ 0.50 AND no methodology FAIL
- **INERT-AT-EXPLORATION**: IS Δ within [-0.10, +0.10] OR OOS Δ within [-0.20, +0.20] — **iter-v3/061 fired here**
- **NEGATIVE-AT-EXPLORATION**: IS Δ < -0.10 OR OOS Δ < -0.20
- **CONFIRMATION re-validation requirement**: PROMISING-AT-EXPLORATION axes carry forward to cycle 1 CONFIRMATION; CONFIRMATION re-validates against /059 (NOT /060) at 10-seed mode

---

## Reproducibility

- HEAD SHA at backtest run: `17eea9a` (Phase 5.5 gate PASS)
- EDA commit SHA: `d198b25` (`analysis/iteration_v3-061/trx_anti_kelly_diagnostic.py` + 6 CSVs + `diagnostic_summary.md`)
- Setup commit SHA: `af92efe` (brief LOCKED; Path B; vol_scale_floor_per_symbol={"TRXUSDT": 0.5})
- Code commit SHA: `6910fcf` (vol_scale_floor_per_symbol field + TRX=0.5; tests 34/34)
- Phase 5.5 gate SHA: `17eea9a` (OVERALL=PASS)
- Engineering report SHA: `870f9f1` (Phase 7)
- Critic FINAL SHA: `b20b554` (EXPLORATION-MERGE — INERT-AT-EXPLORATION certified)
- Diary SHA: (this commit)
- Tag: NONE (BASELINE_V3.md UNCHANGED; /059's `v0.v3-059` remains canonical)
- Wall-clock: 0.69h (under 1.1h target; consistent with /060)
- Hardware: x86_64, 60 GB RAM, WSL2 / Linux 6.6.114.1
- Library stack: UNCHANGED from /060 (Python 3.13, lightgbm 4.6.0, optuna 4.8.0 n_jobs=1, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1)
- Run command: `uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 35`
- Active ensemble seeds: ENSEMBLE_SEEDS[0:3] = (191664963, 1662057957, 1405681631); mode="exploration"; ensemble_size=3; all lineage=outer=42
- Reports artifacts: `reports-v3/iteration_v3-061/comparison.csv`, `dsr.json`, `ensemble_summary.json`, `per_cell_pbo.csv`, `cpcv_paths.csv`, `adf_test.csv`, `ic_matrix.csv`, `trial_oof_returns.parquet`, `in_sample/`, `out_of_sample/`
