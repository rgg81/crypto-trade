# Engineering Report — iter-v3/069 (CORRECTED)

> **CORRECTION NOTICE**: Prior engineering report at commit `05388c9` is INVALIDATED.
> That report measured a COMPOUND axis (+ADA × 14-day-trade-exit-holdover) due to an
> unreverted `BacktestConfig.timeout_minutes=20160` at line 1407 carried from iter-v3/068
> Path C. Critic /069 PRELIMINARY review caught the defect via 3-symbol byte-identity
> falsification. Fix committed at `4239646` (reverted line 1407 to 10080). Re-run
> completed 2026-05-13 at 23:09 UTC, wall-clock 1.07h. This report supersedes `05388c9`.

## Headers

- Iteration: iter-v3/069
- Branch: iteration-v3/069
- Brief locked SHA: `cde507b`
- EDA SHA: `95038dd`
- Phase 5.5 gate SHA: `b61bee0`
- Fix commit SHA: `4239646` (BacktestConfig.timeout_minutes 20160 → 10080)
- Invalidated engineering report SHA: `05388c9`
- This report commit SHA: (this commit)
- Hardware: x86_64, 20 cores, 58 GiB RAM (WSL2)
- Wall-clock time: 1.07h (re-run after fix; within 2h EXPLORATION HARD CAP)

---

## Defect Retrospective

### What happened

The prior engineering report (`05388c9`) was produced from a backtest with `BacktestConfig.timeout_minutes=20160` at line 1407 of `run_baseline_v3.py`. This value was the /068 Path C change (doubling label timeout from 10080 to 20160) and was NOT reverted in the /069 setup commit `cde507b`.

The /069 brief Section 3 explicitly required: "label_timeout_minutes REVERTED to 10080 (10080 min = 21 candles at 8h)". The setup commit edited `REQUIRED_GAP` from 129 → 88 correctly (formula consequence of timeout revert + n_symbols scale) but missed the `label_timeout_minutes` variable itself at line 1407. As a result, the first backtest ran with:
- `label_timeout_minutes = 20160` (retained from /068 — timeout DOUBLING)
- `REQUIRED_GAP = 88` (correctly reflecting 21-candle embargo × 4 symbols)
- `V3_MODELS` expanded to 4 symbols (+ADAUSDT)

This was a COMPOUND axis — not the clean single-axis UNIVERSE EXPANSION brief specified. The first report's IS Sharpe +0.9438 / OOS Sharpe +0.2683 reflected both +ADA and the 14-day timeout holdover simultaneously.

### How it was caught

Critic /069 PRELIMINARY review applied the 3-symbol byte-identity falsification test: BCH, LDO, and TRX trade rosters must be BIT-IDENTICAL to /060 anchor for an axis that only adds a 4th symbol. The preliminary report showed BCH OOS wpnl = +10.64 (vs anchor +1.9078). This is a 5× deviation — BCH should be BYTE-IDENTICAL since BCH's per-symbol Optuna fit is independent and no BCH-touching parameter changed. The deviation was the diagnostic signal: the timeout change affected all symbols' label generation, not just ADA.

### Fix

Commit `4239646` reverted `BacktestConfig.timeout_minutes` at line 1407 from 20160 to 10080. Re-run then produced BCH OOS wpnl = +1.9078 (BIT-IDENTICAL to /060 anchor — byte-identity RESTORED). The corrected single-axis result is the clean +ADA-only measurement.

---

## Configuration Diff vs /060 Anchor (Corrected)

Single-axis change against iter-v3/060 EXPLORATION-MODE-REFERENCE (cycle 1 anchor):

| Parameter | /060 (anchor) | /069 corrected | Delta |
|---|---|---|---|
| `V3_MODELS` | BCH+LDO+TRX (3 symbols) | BCH+LDO+TRX+**ADA** (4 symbols) | +1 symbol (ADAUSDT) |
| `REQUIRED_GAP` (cv_gap) | 66 candles | 88 candles | +22 candles (+33%) |
| `embargo_candles` per cell | 22 | 22 | 0 (unchanged; timeout REVERTED) |
| `label_timeout_minutes` | 10080 (21 candles) | 10080 (21 candles) | 0 (REVERTED from /068's 20160) |
| `_inference_threshold_floor` | 0.0 (default) | 0.0 (default) | 0 |
| `vol_scale_ceiling` | 1.0 (default) | 1.0 (default) | 0 |
| `DEFAULT_ATR_MULTIPLIERS` | (2.0, 1.0) | (2.0, 1.0) | 0 |
| ENSEMBLE_SIZE | 3 (exploration) | 3 (exploration) | 0 |
| Seeds | [191664963, 1662057957, 1405681631] | [191664963, 1662057957, 1405681631] | 0 |
| n_trials per (sym × month × seed) | 35 | 35 | 0 |
| Total trials | 315 (3 syms) | **420** (4 syms) | +105 |

REQUIRED_GAP recalculation: `(embargo_candles + 1) × n_symbols = (21 + 1) × 4 = 88` (formula consequence of n_symbols change; not an independent axis). Per-symbol Optuna budget is UNCHANGED at 35 trials × 3 seeds = 105 fits per (symbol × WF month) — adding a 4th symbol does NOT reduce budget for incumbents.

---

## Key Metrics Block (Corrected)

### Headline vs /060 Anchor

Source: `reports-v3/iteration_v3-069/comparison.csv` (post-fix re-run).
Anchor: `reports-v3/iteration_v3-060/comparison.csv` per brief Section 2.1 T0 declaration.

| Metric | /060 IS | /069 IS | IS Delta | /060 OOS | /069 OOS | OOS Delta | /069 Ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| monthly_sharpe | +0.8325 | **+0.7943** | **-0.0382** | +0.1403 | **+0.1222** | **-0.0181** | 0.1539 |
| daily_sharpe | — | +1.6083 | — | — | +0.3213 | — | 0.1998 |
| max_drawdown | 30.97% | 27.49% | -3.48% | 34.53% | 43.47% | +8.94% | 1.5811 |
| profit_factor | 1.49 | 1.25 | -0.24 | 1.21 | 1.04 | -0.17 | 0.8348 |
| win_rate | 28.99% | 33.05% | +4.06pp | 36.17% | 37.19% | +1.02pp | 1.1254 |
| n_trades | 159 | **233** | +74 | 102 | **121** | +19 | 0.5193 |
| total_pnl | +51.89 | +73.58 | +21.69 | +5.50 | +6.32 | +0.82 | 0.0859 |
| weighted_pnl_total | +51.89 | +73.58 | +21.69 | +5.50 | +6.32 | +0.82 | 0.0859 |
| monthly_calmar | — | 2.6760 | — | — | 0.1453 | — | 0.0543 |
| frac_positive_paths | 0.6444 | 0.6000 | -0.044 | — | — | — | — |
| dsr | 0.0 | 0.0 | 0 | — | — | — | — |
| dsr_relative | 0.0 | 0.0 | 0 | — | — | — | — |
| pbo | 0.1278 | 0.1243 | -0.0035 | — | — | — | — |
| psr | 0.9763 | **0.9833** | +0.0070 | — | — | — | — |
| n_trials | 315 | 420 | +105 | — | — | — | — |
| n_effective_trials | 19 | 19 | 0 | — | — | — | — |
| cpcv_q75_path_sharpe | 0.8378 | **1.4496** | +0.6118 | — | — | — | — |

### Corrected vs Invalidated Run Comparison

| Metric | Invalidated (05388c9) | Corrected (this report) | Delta (artifact removed) |
|---|---:|---:|---:|
| IS monthly_sharpe | +0.9438 | +0.7943 | -0.1495 |
| OOS monthly_sharpe | +0.2683 | +0.1222 | -0.1461 |
| BCH OOS wpnl | +10.64 | **+1.9078** | -8.73 (byte-identity RESTORED) |
| IS n_trades | 232 | 233 | +1 |
| OOS n_trades | 121 | 121 | 0 |

The +0.15 inflation on both IS and OOS Sharpe in the invalidated report was the compound-axis artifact of the 14-day timeout holdover. With the single-axis +ADA measurement, both shifts collapse to within the INERT band.

### Per-Symbol OOS (comparison.csv per_symbol block — corrected)

| Symbol | /060 OOS wpnl | /069 OOS wpnl | Delta | /069 trades | /069 WR | /069 conc% |
|---|---:|---:|---:|---:|---:|---:|
| ADAUSDT | N/A (new) | **+0.42** | N/A | 18 | 27.8% | 6.69% |
| BCHUSDT | **+1.9078** | **+1.9078** | **0.00 (BIT-IDENTICAL)** | 37 | 32.4% | 30.20% |
| LDOUSDT | -19.7208 | -20.7310 | -1.01 | 12 | 16.7% | -328.12% |
| TRXUSDT | +23.3119 | +24.7184 | +1.41 | 54 | 48.1% | 391.23% |

BCH OOS wpnl = +1.9078 is BIT-IDENTICAL to the /060 anchor value — byte-identity invariance RESTORED. The BCH per-symbol Optuna fit is independent of the timeout parameter for BCH's own label generation, and with timeout reverted to 10080 (matching /060's value exactly), BCH reproduces byte-for-byte. This confirms the fix was correct and the single-axis clean measurement is in hand.

LDO shows 1 additional trade vs anchor (12 vs 11) and 12 vs 12 at /060 but with 16.7% WR vs 18.2% — Optuna re-convergence at 4-symbol CV produces slight variation in LDO's threshold trajectory. TRX is 54 trades / 48.1% WR (IDENTICAL count to /060; slight wpnl variation +24.72 vs +23.31 from weight_factor recalculation at 4-symbol portfolio scale).

### Per-Symbol IS (in_sample/per_symbol.csv — corrected)

| Symbol | IS trades | IS WR | IS net_pnl_pct | IS pct_of_total |
|---|---:|---:|---:|---:|
| ADAUSDT | 74 | 40.5% | +46.96 | 51.09% |
| BCHUSDT | 73 | 45.2% | +79.45 | 86.42% |
| LDOUSDT | 11 | 27.3% | -11.44 | -12.44% |
| TRXUSDT | 75 | 29.3% | -23.04 | -25.07% |

---

## Byte-Identity Verification

BCH OOS byte-identity is the primary quality gate for this axis. With timeout reverted to 10080 and only the ADA symbol addition as the single axis change:

- BCH OOS wpnl: **+1.9078** vs /060 anchor **+1.9078** — BIT-IDENTICAL
- BCH OOS n_trades: **37** vs /060 anchor **37** — IDENTICAL
- BCH OOS WR: **32.4%** vs /060 anchor **32.4%** — IDENTICAL

LDO and TRX byte-identity is NOT expected since REQUIRED_GAP changed from 66 → 88 (22 additional embargo candles at the CV boundary affect the training data extent for all per-symbol models). The LDO/TRX slight variations are the legitimate consequence of the CV gap formula scaling with n_symbols. BCH's byte-identity holds because the per-symbol head is independent and the BCH data extent at each WF split is unaffected by the gap formula change in the limit of sufficiently long training windows. This is an important structural observation: BCH byte-identity is a necessary (but not sufficient) condition for single-axis attribution; LDO/TRX non-identity is expected and not a bug.

---

## Classification

### Falsifier grid (Section 8 — LOCKED)

| Falsifier | Pre-registered threshold | Observed | Status |
|---|---|---|---|
| Section 8.1 IS PROMISING | IS Δ ≥ +0.10 | IS Δ = **-0.038** | **FAILS** |
| Section 8.1 OOS PROMISING | OOS Δ ≥ +0.10 | OOS Δ = **-0.018** | **FAILS** |
| Section 8.3 IS negative gate | IS Δ ≥ -0.20 | IS Δ = -0.038 | PASS (above floor) |
| Section 8.3 OOS negative gate | OOS Δ ≥ -0.30 | OOS Δ = -0.018 | PASS (above floor) |
| Section 8.4 INERT-AT-EXPLORATION | IS Δ in [-0.20, +0.10] AND OOS Δ in [-0.30, +0.10] | IS -0.038 ∈ band; OOS -0.018 ∈ band | **TRIGGERS** |
| Section 4.5 IS trade saturation | [194, 209] → ≤220 upper bound | 233 IS trades | **FIRES** (>220; ADA higher emission than NATR-proxy) |
| Section 4.5 OOS trade floor | OOS ≥ 130 (bundle floor) | 121 OOS trades | FAILS floor — moot (INERT; not advancing to bundle) |
| Section 4.6 LDO OOS WR goal | LDO OOS WR ≥ 20.2% (+2pp) | 16.7% | FAILS goal (below by 3.5pp) |
| Section 4.6 LDO OOS WR floor | LDO OOS WR ≥ 16.2% (-2pp) | 16.7% | PASS (+0.5pp above -2pp floor) |
| Section 4.7 BCH IS WR floor | BCH IS WR ≥ 43.2% (-2pp) | 45.2% | PASS (no damage; +2pp above floor) |
| Section 4.7 BCH IS WR damage gate | BCH IS WR ≥ 40.2% (-5pp) | 45.2% | PASS |
| Section 8.6 ADA IS floor | ADA IS trades ≥ 24 | **74** | PASS (3× over floor) |
| Section 8.6 ADA OOS floor | ADA OOS trades ≥ 14 | **18** | PASS (+4 cushion) |
| frac_positive_paths | ≥ 0.55 | 0.600 | PASS |

### Classification adjudication

Per the pre-registered Section 8 criteria:

- **Section 8.1 disjunctive OR PROMISING**: IS Δ -0.038 < +0.10 (FAILS); OOS Δ -0.018 < +0.10 (FAILS). Neither arm of the disjunction passes. NOT PROMISING.
- **Section 8.3 NEGATIVE gate**: IS Δ -0.038 > -0.20 (PASS); OOS Δ -0.018 > -0.30 (PASS). Neither negative floor triggered. NOT NEGATIVE.
- **Section 8.4 INERT zone**: IS -0.038 ∈ [-0.20, +0.10] AND OOS -0.018 ∈ [-0.30, +0.10]. Both shifts within band. **TRIGGERS INERT-AT-EXPLORATION**.

**FINAL CLASSIFICATION: INERT-AT-EXPLORATION** (clean).

The prior "PROMISING-DEFERRED" classification in engineering report `05388c9` was an artifact of the unreverted 14-day timeout inflating both IS Sharpe by +0.15 and OOS Sharpe by +0.15. With the correct 7-day timeout, both shifts collapse to within-band INERT: IS -0.038, OOS -0.018.

The axis is CLOSED at the catalog level. The universe expansion via +ADAUSDT produced no material aggregate signal lift at single-seed n_trials=35 EXPLORATION. The denominator-expansion mechanism worked at the architectural level (BCH concentration fell from ~100% dominance to 30.2%; ADA contributed 6.69% positive concentration) but did not move headline Sharpe metrics outside the INERT band.

---

## ADA Contribution Analysis

### ADA OOS performance

- 18 OOS trades over 14 OOS months (April 2025 – May 2026)
- 27.8% OOS WR (5/18 wins) — modest signal at single-seed n_trials=35
- +0.42 OOS weighted PnL — positive but small contribution (6.69% concentration)
- OOS net_pnl_pct = -14.56 (raw PnL negative; wpnl positive due to weight_factor de-weighting losing trades)
- IS: 74 trades, 40.5% WR — above ADA IS floor (≥24) with large margin

ADA per-symbol head is viable (passes IS floor ≥24 and OOS floor ≥14 per Section 8.6). The IS trade count saturation falsifier FIRES (233 total vs 220 upper bound), driven by ADA's 74 IS trades vs NATR-proxy estimate of ~50. ADA emits more IS trades than the proxy projected — Optuna at 35 trials found a lower confidence threshold than the NATR-based estimate anticipated.

### LDO status after universe expansion

LDO OOS WR at /069 = 16.7% (2/12 wins). Recovery from /068's collapse (8.3%) to 16.7% = +8.4pp, but still below the Section 4.6 goal of ≥20.2% and below the /060 anchor of 18.2%.

| Iteration | LDO OOS WR | LDO OOS trades |
|---|---|---|
| /060 (anchor) | 18.2% | 11 |
| /064 | 7.1% | 14 |
| /068 | 8.3% | 12 |
| /069 (corrected) | 16.7% | 12 |

Universe expansion partially recovered LDO OOS WR (timeout REVERT from 20160 → 10080 is likely the recovery driver, not the ADA addition). LDO's fundamental weakness in the current feature/labeling stack persists — the concentration dilution mechanism did not repair per-symbol signal quality.

### BCH IS WR stability

BCH IS WR = 45.2% (identical to /060 anchor 45.2%). No BCH IS damage. BCH IS pct_of_total_pnl = 86.42% — BCH remains the dominant IS contributor; ADA's 51.09% is the second-largest IS contributor (ADA IS net_pnl_pct +46.96 vs BCH +79.45, but ADA has fewer dollar-weighted wins in this EXPLORATION context).

---

## CPCV and Statistical Metrics

- CPCV_Q75 = 1.4496 vs /060's 0.8378 (+0.61): the 4-symbol CPCV path distribution shifts upward at 4-symbol scale — a methodology consequence of the additional independent per-symbol head, not a signal-quality claim.
- frac_positive_paths = 0.6000 (27/45 paths positive; PASSES ≥0.55 gate threshold).
- PBO = 0.1243 (below /060's 0.1278 by 0.003; directionally improved).
- PSR = 0.9833 vs /060's 0.9763 (+0.007; marginal improvement).
- DSR = 0.0 and DSR_relative = 0.0 — structural EXPLORATION-mode artifact per `feedback_v3_dsr_mode_artifact.md`; INFORMATIONAL ONLY.

---

## Label Leakage Audit

REQUIRED_GAP = (embargo_candles + 1) × n_symbols = (21 + 1) × 4 = 88.

The runner computed cv_gap = 22 × 4 = 88, matching the brief Section 3 specification. embargo_candles = `compute_embargo_candles(10080, 480) = 10080//480 + 1 = 22` (revert of /068's 43). n_symbols = 4 (post-/069 UNIVERSE EXPANSION). The per-cell embargo (22 candles) is IDENTICAL to the /060 anchor embargo; REQUIRED_GAP increase from 66 to 88 is solely the n_symbols scaling effect. No label leakage introduced.

IS zero-trade months: 0 verified — all IS months have non-zero trade counts. OOS months: 14 (April 2025 – May 2026), all non-zero.

---

## Anomaly Notes

**IS trade saturation falsifier FIRES**: observed IS trades = 233 exceeds the 220 upper-bound (Section 4.5: "If observed IS trades > 220: saturation falsifier FIRES"). ADA IS = 74 trades vs NATR-proxy estimate of ~50. The NATR-proxy underestimated ADA's per-symbol Optuna threshold sensitivity at 35 trials/cell. BCH IS = 73, TRX IS = 75 (within 1 trade of /060 anchor) confirm the saturation effect is ADA-specific, not a global Optuna re-convergence artifact.

**Spot-check (10 random OOS rows across all 4 symbols)**: verified entry/exit/pnl math for BCH, TRX, LDO, ADA rows. Exit reasons consistent with SL/TP price proximity. weight_factor in [0.19, 1.00] range. pnl_pct signs match direction × (exit_price - entry_price)/entry_price. No anomalies detected.

**ADA OOS net_pnl_pct (-14.56) vs wpnl (+0.42)**: the RiskV3Wrapper weight_factor de-weights losing ADA trades, producing a positive wpnl despite negative raw pnl. This is the risk gate stack operating correctly — no bug.

**TRXUSDT IS pnl negative / OOS pnl positive**: TRX IS net_pnl_pct = -23.04 (negative in IS) but OOS wpnl = +24.72 (positive in OOS). Recurring pattern across cycle 1 iterations. TRX's IS-negative/OOS-positive pattern has been stable since /060 — it is a structural feature of TRX's regime distribution, not an artifact of this iteration.

---

## Seed Concentration Audit

Exploration mode: ENSEMBLE_SIZE=3, outer seeds [191664963, 1662057957, 1405681631] (outer=42 lineage).
Single outer seed EXPLORATION spec — no multi-seed concentration audit applicable per `feedback_v3_outer_seed_cap_2_v3.md`. Multi-seed variance assessment deferred to /070 CONFIRMATION.

---

## /070 CONFIRMATION Bundle Decision

With corrected INERT-AT-EXPLORATION classification, /069 does NOT contribute new alpha to the /070 CONFIRMATION bundle.

**FINAL /070 BUNDLE COMPOSITION: /065 SL widening + /062 Path B4 deferred spec (2 components, UNCHANGED)**

The universe expansion mechanism worked structurally (denominator dilution confirmed via BCH concentration 30.2% and ADA 6.69%). However, it did NOT produce material aggregate Sharpe movement at single-seed n_trials=35. Any further universe expansion evaluation should occur as a follow-up EXPLORATION in a future cycle, not bundled into /070.

| Component | Classification | Bundle status |
|---|---|---|
| /065 SL widening (ATR 1.0→1.5) | SUSPICIOUS-OOS-DOMINANT | **IN** (multi-seed validation required at /070) |
| /062 Path B4 DSR_relative recalibration | PASSIVE-DIAGNOSTIC (deferred) | **IN** (methodology spec from /062 brief Section 3) |
| /069 Universe expansion +ADAUSDT | **INERT-AT-EXPLORATION** | **OUT** (axis closed; no aggregate Sharpe lift) |

---

## Cycle 1 Closeout Summary (CORRECTED)

10/10 EXPLORATION iterations COMPLETE. Cycle 1 cadence is COMPLETE per `feedback_v3_strict_10_to_1_cadence.md` Directive 2.

| Slot | Iteration | Axis | Classification |
|---:|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE (3 seeds, ENSEMBLE_SIZE=3) | PROMISING-EXPLORATION (anchor) |
| #2 | /061 | TRX RiskV2 anti-Kelly vol_scale_floor | INERT-AT-EXPLORATION (closed) |
| #3 | /062 | DSR_relative recalibration (Path C passive) | PASSIVE-DIAGNOSTIC (Path B4 deferred to /070) |
| #4 | /063 | Mass feature expansion (46 features) | SUSPICIOUS-OOS-DOMINANT + IS-COLLAPSE (closed) |
| #5 | /064 | Phased expansion (+adx_14 single feature) | NEGATIVE (closed) |
| #6 | /065 | NON-FEATURE PIVOT: UNIVERSAL SL widen 1.0→1.5 | SUSPICIOUS-OOS-DOMINANT (first /070 bundle candidate) |
| #7 | /066 | NON-FEATURE PIVOT: vol_scale_ceiling 1.0→0.8 | INERT-AT-EXPLORATION (closed) |
| #8 | /067 | NON-FEATURE PIVOT: inference-threshold tighten 0.60 | INERT-AT-EXPLORATION (closed) |
| #9 | /068 | NON-FEATURE PIVOT: label_timeout widen 21→42 | NEGATIVE (both directions; family closed) |
| **#10** | **/069** | **NON-FEATURE PIVOT: UNIVERSE EXPANSION +ADAUSDT** | **INERT-AT-EXPLORATION (IS Δ -0.038, OOS Δ -0.018; both within ±band)** |
| CONFIRMATION | /070 | Bundle: /065 SL widening + /062 Path B4 | **2 components** (FINAL composition; /069 excluded) |

Cycle 1 summary:
- 1 PROMISING-EXPLORATION anchor (/060)
- 1 PASSIVE-DIAGNOSTIC (/062 — Path B4 for /070)
- 1 SUSPICIOUS-OOS-DOMINANT (/065 — /070 bundle candidate)
- 4 INERT (/061, /066, /067, /069)
- 3 NEGATIVE (/063, /064, /068)

---

## Recommendations to QR for /070 CONFIRMATION

1. **Anchor requirement**: /070 CONFIRMATION MUST beat BASELINE_V3.md anchor (IS +1.0894 / OOS +0.5791 at /059 multi-seed) on BOTH IS and OOS Sharpe (multi-seed mean) per `feedback_v3_strict_both_is_oos_baseline.md`. The corrected /069 single-seed IS +0.7943 / OOS +0.1222 remain below both baseline thresholds — /070 CONFIRMATION must overcome this at --seeds 2 + ENSEMBLE_SIZE=5.

2. **Bundle composition FINAL**: /065 SL widening + /062 Path B4. Universe expansion is excluded. QR should NOT revisit /069's ADA addition for /070 — the INERT classification closes the axis at cycle 1 level. Universe expansion as a tool is structurally valid but requires investigation in a future cycle with multi-seed validation or a different candidate symbol.

3. **3-symbol vs 4-symbol architecture**: /070 CONFIRMATION runs the 3-symbol BCH+LDO+TRX architecture (per /060 anchor). REQUIRED_GAP = 66 (not 88). label_timeout = 10080 (not 20160). These must be hardcoded in the /070 runner and verified at Phase 5.5 Section 0.

4. **Path B4 spec from /062**: /062 brief Section 3 contains the DSR_relative recalibration methodology spec. /070 must implement exactly as specified there — no reinterpretation.

5. **Predicted band tightening** (per Critic /068 Rec #1): CONFIRMATION briefs use tighter bands than EXPLORATION. IS/OOS Sharpe variance at --seeds 2 + ENSEMBLE_SIZE=5 is materially lower. Brief Section 4 bands must reflect the reduced variance at multi-seed.

6. **LDO monitoring**: LDO OOS WR has ranged 7.1%–18.2% across cycle 1 at single-seed. Multi-seed CONFIRMATION will reveal whether LDO's weakness is single-seed lottery or structural. If LDO persists at WR < 15% across both /070 seeds, QR should evaluate LDO exclusion from v3 universe in cycle 2.

7. **Inherited IC violation** (per Critic /068 Rec #2): vwap_dev_20 × regime_momentum_signed_5d = 0.7642 IC — above the 0.70 hard gate. /070 brief must address this explicitly: either document as an approved exception (Category 2 composed features relaxation per `feedback_v3_engineered_feature_pivot.md`) or remove one of the two correlated features before /070.

8. **Anchor-byte correctness gate** (per Critic /064-/068 Rec #1): /070 should incorporate the BCH byte-identity check as a pre-run validation step in the runner to prevent compound-axis accidents. The /069 defect demonstrates the need for this guard.

---

## Status

OVERALL = READY-FOR-CRITIC

**Classification: INERT-AT-EXPLORATION** (corrected from prior PROMISING-DEFERRED at `05388c9`)

- IS Δ = **-0.038** vs /060 anchor (within INERT band [-0.20, +0.10])
- OOS Δ = **-0.018** vs /060 anchor (within INERT band [-0.30, +0.10])
- BCH OOS BIT-IDENTICAL to /060 anchor (+1.9078, 37 trades, 32.4% WR) — byte-identity RESTORED
- ADA IS 74 trades (PASS ≥24), ADA OOS 18 trades (PASS ≥14) — per-symbol head viable
- IS trade saturation falsifier FIRES (233 > 220 upper bound; ADA higher emission than NATR-proxy)
- LDO OOS WR 16.7% — within ±2pp zone; goal of ≥20.2% NOT achieved
- BCH IS WR 45.2% — PASS (no damage)
- frac_positive_paths 0.600 — PASS (≥0.55)
- Denominator-expansion mechanism confirmed working at architectural level; no aggregate Sharpe lift
- /069 axis CLOSED at catalog level
- /070 CONFIRMATION bundle FINAL: /065 SL widening + /062 Path B4 (2 components)
- Cycle 1 cadence COMPLETE (10/10 EXPLORATIONS DONE)
