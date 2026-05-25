# iter-v1/010 — Research Brief

**Date**: 2026-05-25
**QR**: claude-opus-4-7 (1M context) — quant-research-v1 mode
**Mode**: EXPLORATION (single-seed, ENSEMBLE_SIZE=3, n_trials=35, ≤2h cap)
**Axis**: R5 vol-target ceiling per symbol — `risk-primitive` family
**Branch**: `iteration-v1/010`

---

## Section 0 — Iteration Pre-Header

### 0.1 Anchor
`v0.v1-baseline-corrected` (`BASELINE_V1.md` commit `f8bc12c`)
- IS monthly Sharpe **+0.2829**, OOS monthly Sharpe **+0.6637**
- IS trades 621, OOS trades 189
- 5-seed v1-baseline-corrected ensemble (`[42, 123, 456, 789, 1001]`)

### 0.2 Mode
**EXPLORATION** (cycle-2, post-/009 closeout)
- `--exploration --seeds 1 --n-trials 35` (canonical v1 EXPLORATION knobs)
- ENSEMBLE_SIZE = 3 (single outer seed × 3 inner seed from `[42, 123, 456]`)
- ≤2h wall-clock cap (NON-NEGOTIABLE per /005 closeout 10:1 cadence discipline)

### 0.3 Iteration label
`v1-010`

### 0.4 Determinism note
R5 is purely deterministic given NATR_14 feature parquet. Same data extent → same baseline-OFF trade roster (F1 sanity check). With R5 ON, trade roster will differ but reproducibly.

### 0.5 Cadence position
**Cycle-2 EXPLORATION #5** (of 10-EXPLORATION cycle since /002 baseline-set).

Cycle-2 catalog: /006 (universe, NEGATIVE+DEGENERATE), /007 (feature-family composed, NEGATIVE-NEGATIVE), /008 (methodology, PROMISING-METHODOLOGY), /009 (feature-family deletion, NEGATIVE-NEGATIVE). /010 = 5th EXPLORATION in cycle-2.

Next CONFIRMATION cannot fire until 10 cycle-2 EXPLORATIONs accumulate (currently 5; /010 = 5 of 10).

### 0.6 Architecture-Family Justification (v1-only)

- **Axis family**: `risk-primitive`
- **Prior 5 EXPLORATION families** (from `briefs-v1/exploration_catalog.md`):
  - iter-v1/005: `hyperparameter-region`
  - iter-v1/006: `universe`
  - iter-v1/007: `feature-family`
  - iter-v1/008: `methodology`
  - iter-v1/009: `feature-family`
- **Rotation status**: **VALID** — `risk-primitive` is UNUSED across v1 cycle-1 + cycle-2 to date (this is the FIRST appearance of the family in the v1 catalog). Distinct from each of the prior 5; majority of prior 5 are NOT same-family with `risk-primitive`.
- **One-sentence rationale**: After cycle-2's 4 prior EXPLORATIONs (universe + 2× feature-family + methodology) exhausted the cheap structural axes, the LM Master /009 Phase 7.4 PRIMARY recommendation + Critic /009 Path Forward #1 + QR /009 Phase 8 selection 3-way-converged on UNUSED `risk-primitive` as the only remaining family that operates orthogonally to model-prediction-layer mechanisms (R5 acts at position-sizing layer downstream of all current axes).

---

## Section 1 — Hypothesis

**R5 vol-target ceiling reduces portfolio drawdown by capping position size at high-volatility entries, where Optuna's loss-surface fit is most overfit to IS noise.**

The hypothesis has three parts:

1. **Mechanism**: at high NATR_14 entries (top quartile, NATR > ~5%), position size from `signal.weight × vt_scale` may produce trades with absolute risk (entry-to-SL distance × position size) above the safe band. R5 caps position size at `min(1.0, vol_target_pct / NATR_14)` — a multiplicative reduction that becomes active only when NATR_14 > vol_target_pct.

2. **Predicted effect**: portfolio variance reduction at modest mean-cap (0.95 IS / 0.98 OOS at calibrated 4.0%) — small enough to NOT eliminate the LINK + BTC OOS edge (BASELINE_V1.md per-symbol attribution: LINK +34.23%, BTC +33.17%, both at < p75 NATR), but cuts the LINK + LTC IS overshoots and the most extreme-vol OOS losers.

3. **Expected outcome class**: PROMISING-INERT to marginal-NEGATIVE band. Oracle EDA predicts OOS Δ ∈ [-0.05, +0.02] at vol_target = 4.0%. R5 is honestly a variance-reducer, NOT an edge-generator. The case for /010 is structural orthogonality + risk-management cleanliness, NOT Sharpe-uplift maximization.

**Falsifies**: the `feedback_v3_concentration_is_signal.md` proportional-scaling lesson (v3/020) generalizes universally — i.e., that proportional-vol caps ALWAYS reduce OOS Sharpe regardless of universe size and architecture.

**Confirms**: per-symbol NATR distributions can be exploited at position-sizing layer if the calibration is tuned to the universe's NATR p75 (not p50).

---

## Section 2 — IS-Only Evidence (numerical tables)

### 2.1 Per-symbol IS NATR_14 distribution

From `analysis/iteration_v1-010/per_symbol_is_natr14_distribution.csv` (5,012-5,714 IS candles per symbol, computed from feature parquets, IS-only filter `open_time < OOS_CUTOFF_MS`):

| Symbol | n_candles | mean | p10 | p25 | **p50** | p75 | p90 | p95 |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 5714 | 2.75 | 1.45 | 1.85 | **2.44** | 3.25 | 4.26 | 5.35 |
| ETHUSDT | 5714 | 3.57 | 1.83 | 2.39 | **3.13** | 4.18 | 5.53 | 7.08 |
| LINKUSDT | 5665 | 4.91 | 2.69 | 3.38 | **4.35** | 5.76 | 7.67 | 9.24 |
| LTCUSDT | 5674 | 4.13 | 2.12 | 2.73 | **3.65** | 4.94 | 6.65 | 7.91 |
| DOTUSDT | 5012 | 4.60 | 2.24 | 2.93 | **4.12** | 5.49 | 7.44 | 9.09 |

Universe p50 average: 3.5%. Universe p75 average: 4.7%. Universe p90 average: 6.3%.

### 2.2 Trade-level fire rate on baseline roster (oracle, STATELESS gate per /054)

From `analysis/iteration_v1-010/trade_level_fire_rate_simulated.csv` — fire rate = fraction of baseline trades with `R5_cap < 1.0`:

| vol_target | IS portfolio fire | OOS portfolio fire | IS mean cap | OOS mean cap | F2 band ∈ [10%, 60%]? |
|---|---|---|---|---|---|
| 2.0% | 85.2% | 82.0% | 0.686 | 0.715 | OUT (over) |
| 2.5% | 66.6% | 64.6% | 0.798 | 0.829 | OUT (over) |
| 3.0% | 48.4% | 45.0% | 0.874 | 0.907 | IN |
| 3.5% | 35.0% | 27.5% | 0.923 | 0.954 | IN |
| **4.0%** | **22.6%** | **15.3%** | **0.954** | **0.977** | **IN — calibrated optimum** |
| 4.25% | 18.4% | 11.6% | 0.964 | 0.983 | IN (edge of band) |
| 4.5% | 14.7% | 7.9% | 0.971 | 0.988 | OUT (under, OOS) |

### 2.3 Oracle Sharpe-delta simulation (STATELESS-gate-VALID per /054)

From `analysis/iteration_v1-010/simulated_sharpe_delta_oracle.csv`:

| vol_target | IS Δ oracle | OOS Δ oracle | F1 (OOS Δ ≥ -0.05) | F3 (IS Δ ≥ -0.10) |
|---|---|---|---|---|
| 2.0% | -0.100 | -0.051 | FAIL (margin -0.001) | FAIL exactly |
| 2.5% | -0.086 | -0.050 | FAIL (boundary) | PASS |
| 3.0% | -0.082 | -0.042 | PASS | PASS |
| 3.5% | -0.071 | -0.027 | PASS | PASS |
| **4.0%** | **-0.056** | **-0.020** | **PASS comfortably** | **PASS comfortably** |
| 4.25% | -0.048 | -0.015 | PASS comfortably | PASS comfortably |

Oracle EDA caveat per /054: R5 is STATELESS, so oracle on baseline roster is methodologically VALID. **But oracle assumes Optuna's hyperparameter selection is FROZEN.** Actual /010 backtest re-runs Optuna with R5-scaled rewards — real OOS Δ may diverge from oracle by ±20% on absolute terms (LM Master /005-/009 calibration: their P10/P90 width has been ±2× wider than design, codified in /007 closeout).

### 2.4 Per-symbol PnL impact at vol_target = 4.0% (oracle)

From `trade_level_fire_rate_simulated.csv`:

| Symbol | IS wpnl baseline | IS wpnl R5 oracle | IS wpnl Δ | OOS wpnl baseline | OOS wpnl R5 oracle | OOS wpnl Δ |
|---|---|---|---|---|---|---|
| BTCUSDT | -15.03 | -16.69 | -1.66 | +13.65 | +13.51 | -0.14 |
| ETHUSDT | -15.97 | -8.87 | +7.10 | +32.21 | +29.81 | -2.40 |
| LINKUSDT | +96.40 | +67.78 | -28.62 | +21.34 | +18.84 | -2.50 |
| LTCUSDT | +2.24 | -10.04 | -12.28 | -28.21 | -27.21 | +1.00 |
| DOTUSDT | -16.19 | -16.40 | -0.21 | -0.86 | -3.95 | -3.09 |
| **Portfolio** | **+51.45** | **+15.78** | **-35.67** | **+38.13** | **+30.99** | **-7.14** |

**Mechanism observed**: R5 cuts LINK's IS PnL by ~30% (its top-positive contributor) and improves ETH by +7.10. LTC's wpnl is mildly NEGATIVE in oracle. Net portfolio IS oracle is +15.78 vs +51.45 baseline — variance-reducer signature, not edge-maker.

### 2.5 HIGH-RISK Axis Declaration (v1-only)

- **Declaration**: **HIGH-RISK**
- **Reason**: R5 multiplies into `weight_factor` which scales `weighted_pnl` which is the SAME quantity Optuna's CV scoring sees in its `mean_oos_sharpe` objective via the lgbm CV labels (triple-barrier hits multiplied by trade weight). R5 changes the Optuna training-objective domain → HIGH-RISK by v1 catalog definition.
- **Mitigation (HIGH-RISK with OPT-IN multi-seed; lighter footing than v3)**: pre-commit to /011 multi-seed CONFIRMATION IF /010 verdict is PROMISING. If /010 is NEGATIVE / NEGATIVE-NEGATIVE / PROMISING-INERT, /011 reverts to next axis from Critic Path Forward and R5 is recorded as single-seed-tested (not multi-seed-promised).
- **6-HIGH-RISK-in-a-row context**: /005-/009 were all HIGH-RISK; all NEGATIVE (5 in a row); /010 is 6th-consecutive HIGH-RISK. The "3+ HIGH-RISK with >1σ negative deltas → mandatory multi-seed" rule (`feedback_high_risk_multi_seed.md`) would have fired by now — but per /009 closeout discipline, the rule fires for SAME-axis HIGH-RISK consecutive (none of /005-/009 are the same axis as /010). /010 family `risk-primitive` is structurally novel; single-seed is justified.

---

## Section 3 — Proposed Changes (with LM Master responses)

### 3.1 src/ changes

**3-file diff (~19 lines net new)**:

1. **`src/crypto_trade/backtest_models.py`**: add 2 fields to `BacktestConfig`:
   ```python
   # Risk mitigation R5 (iter-v1/010): per-symbol vol-target ceiling.
   # Caps weight_factor at min(1.0, risk_r5_vol_target_pct / max(NATR_14, 0.01)).
   # Applied AFTER R2 in the vt_scale pipeline. Default disabled — restoring
   # risk_r5_vol_target_enabled=False preserves byte-identical legacy behavior.
   risk_r5_vol_target_enabled: bool = False
   risk_r5_vol_target_pct: float = 4.0
   ```

2. **`src/crypto_trade/backtest.py`**: load `r5_natr_lookup: dict[(str, int), float]` at backtest init (one parquet read per symbol; mirrors `vt_per_sym_daily` loading discipline at L≈100-120); insert R5 block after R2 at line 388, before `create_order`. Implementation skeleton:
   ```python
   # After existing R2 block (line 388):
   if config.risk_r5_vol_target_enabled:
       natr = r5_natr_lookup.get((sym, ot), float("nan"))
       if not math.isnan(natr):
           r5_scale = min(1.0, float(config.risk_r5_vol_target_pct) / max(natr, 0.01))
           vt_scale = vt_scale * r5_scale
   ```

3. **`run_baseline_v1.py`**: add 2 keyword args to BacktestConfig construction in `run_model`:
   ```python
   risk_r5_vol_target_enabled=True,
   risk_r5_vol_target_pct=4.0,
   ```
   Applied to all 4 models (A pooled, C LINK, D LTC, E DOT) — R5 is universal exposure ceiling per /009 closeout 3-way convergence.

### 3.2 LM Master /009 Phase 7.4 PRIMARY recommendation response

Per `briefs-v1/iteration_v1-009/lgbm_advisor.md` Phase 7.4 §"PRIMARY recommendation":

> **R5 vol-target ceiling** preferred over R4 concentration cap per v3/020 finding... 2h cap; LM Master MEDIUM confidence + LOW default cycle-2

**Response**: **ADOPTED** verbatim as /010 PRIMARY axis. Family `risk-primitive` declared in Section 0.6. vol_target_pct revised from "2.5% (mid of crypto realized NATR range)" → **4.0%** per Phase 1 EDA calibration (Section 2.1-2.3 evidence). The revision is a sharpening of LM Master's intent, not a rejection — LM Master's 2.5% was a back-of-envelope estimate; EDA computed actual per-symbol distributions and identified 4.0% as the in-band optimum.

**No Phase 4.5 LM Master dispatch for /010**: per /008 closeout discipline (when prior closeout's Phase 7.4 emits a HIGH-conviction PRIMARY recommendation, the QR can skip Phase 4.5 dispatch and proceed directly to brief authoring). LM Master will engage in Phase 7.4 (post-mortem) per standard cycle.

### 3.3 Critic /009 Path Forward response

Per `1df8bd3 docs(iter-v1/009)` catalog row Path Forward:

> iter-v1/010 PRIMARY = risk-primitive UNUSED family (R5 vol-target ceiling preferred per v3/020 finding); ≤2h cap; ... SECONDARY = methodology /008-style debt

**Response**:
- **PRIMARY (R5) ADOPTED** as /010 sole axis per Section 3.1.
- **SECONDARY (methodology debt) REJECTED**: N_eff PCA refactor was CLOSED at /008. No methodology debt remains. Per /008 closeout, methodology axis is dormant until a new defect surfaces.

### 3.4 Hyperparameter and search-space — UNCHANGED

- `bounds_profile=v1_pruned` (same as /002+ default)
- `n_trials=35` (canonical v1 EXPLORATION)
- `ENSEMBLE_SIZE=3` (single outer seed × 3 inner)
- `feature_columns=V1_FEATURE_COLUMNS_PRUNED` (40 columns — same as /008-/009)
- `cv_splits=5`, `embargo` formula unchanged
- ATR mults `atr_tp=3.5, atr_sl=1.75` (all models)
- R1 mults / cooldown unchanged

The ONLY axis change is the BacktestConfig R5 enable + threshold.

---

## Section 4 — Falsifiers and Behavioral Predictors

Each falsifier has an EXPLICIT numerical condition that fires on backtest report data. F2 includes a brief Section 4 behavioral-effect predictor.

### F1 (PRIMARY) — Portfolio OOS Sharpe Δ
- **Condition**: `(/010 OOS monthly Sharpe) - (BASELINE_V1 OOS monthly Sharpe +0.6637) < -0.05`
- **Verdict if fires**: NEGATIVE
- **Catastrophic threshold**: `Δ < -0.20` triggers NEGATIVE-catastrophic
- **Oracle prediction**: -0.02 (within tolerance; the experiment's main uncertainty is Optuna re-optimization deviation from oracle)

### F2 (BEHAVIORAL — Phase 1 predictor) — R5 fire rate (% of trades with cap < 1.0)
- **Condition**: per-symbol R5 fire rate band check.
  - **Calibration miss-too-tight**: portfolio OOS fire rate > 80% — R5 acts as constant brake, not ceiling
  - **Calibration miss-too-loose**: portfolio OOS fire rate < 5% — R5 effectively inactive
- **Verdict if fires**: NEGATIVE-mis-calibrated
- **Reasonable activation band**: portfolio OOS fire rate ∈ [10%, 60%]
- **Oracle prediction**: 15.3% (mid-band; cap fires modestly)
- **Pre-registered Phase 1 evidence**: `analysis/iteration_v1-010/trade_level_fire_rate_simulated.csv` row `half=OOS, symbol=PORTFOLIO, vol_target_pct=4.0` shows oracle fire rate 15.3% — within band.

### F3 — IS Sharpe Δ catastrophic check
- **Condition**: `(/010 IS monthly Sharpe) - (BASELINE_V1 IS monthly Sharpe +0.2829) < -0.10`
- **Verdict if fires**: NEGATIVE-catastrophic (independent of F1)
- **Oracle prediction**: -0.056 (within tolerance)

### F4 — DEGENERATE_PREDICTOR check (added at /008)
- **Condition**: any per-cell DEGENERATE_PREDICTOR fire in the /010 reports per `validation_v1.detect_degenerate_predictor` (defined at /008 closeout)
- **Verdict if fires**: NEGATIVE-data-integrity OR NEGATIVE-feature-leakage (per detector subtype)
- **Oracle prediction**: 0 fires — R5 is a position-sizing primitive, not a feature or label-modifying primitive

### F5 — DSR computable per /008 refactor
- **Condition**: `dsr.json` exists with `n_eff_per_cell_median ≥ 4` AND `dsr_is_finite=True` AND no math-undefined values
- **Verdict if fires**: NEGATIVE-methodology-regression
- **Oracle prediction**: PASS (no methodology change between /008 baseline and /010)

---

## Section 5 — Expected OOS Impact

### 5.1 Predicted Sharpe delta band (with epistemic humility)

| Range | OOS Sharpe Δ | Interpretation | Confidence |
|---|---|---|---|
| P10 | -0.10 | Worse than oracle by 5×; Optuna re-optimizes to overfit IS into R5-scaled basin | LOW |
| P25 | -0.05 | F1 boundary; NEGATIVE marginal | LOW-MED |
| P50 | -0.02 | Tracks oracle (15.3% fire rate confirms expected behavior) | MED |
| P75 | +0.02 | Optuna substitutes high-vol-low-quality with low-vol-high-quality entries | LOW-MED |
| P90 | +0.10 | Variance reduction + edge preservation (textbook risk-management win) | LOW |

**Wide band (~0.20 P10-P90 spread)** reflects LM Master /005-/009 calibration drift (their P10/P90 width has been 2× the design width in 3 of 5 prior iterations).

### 5.2 Most likely verdict: **PROMISING-INERT to marginal-NEGATIVE**

Per oracle EDA (Section 2.3): OOS Δ_oracle = -0.020 at vol_target=4.0%. If Optuna re-optimization stays in the same neighborhood of hyperparameter space, the verdict is **PROMISING-INERT** (PROMISING-class outcome where the cap mechanically fires but produces neutral-to-slightly-negative Sharpe delta).

Less likely: **PROMISING** (OOS Δ > +0.05; requires Optuna to actively substitute entries) — would imply the model adapts to scaled rewards by selecting fewer-but-better entries. This is the v3 "ENSEMBLE_SIZE=3 + Optuna re-opt may not converge to new optimum at 35 trials × 1 seed" risk.

### 5.3 Counter-evidence (mandatory per Section 7 of skill template)

Three arguments AGAINST /010 yielding any positive OOS:

1. **`feedback_v3_concentration_is_signal.md` v3/020 finding**: proportional scaling at single-seed CONSISTENTLY reduces OOS Sharpe across 3 prior tests in v3 because Optuna's reward surface compresses around fewer trades. R5 = proportional scaling = same primitive. v1 may inherit the lesson.

2. **Capacity-fit-noise at single-seed=42 (per /005 closeout)**: with the loss surface now reshaped by R5 scaling, single-seed Optuna may explore an IS-overfit basin that scores well on the R5-scaled IS Sharpe but generalizes worse OOS.

3. **Baseline LINK concentration is the OOS edge**: per BASELINE_V1.md per-symbol attribution, LINK at +34.23% OOS net_pnl is THE top contributor. R5 cuts LINK position size disproportionately (LINK has highest NATR in the universe). The Section 2.4 oracle shows LINK OOS Δ = -2.50pp under R5 — that's 11% reduction in LINK's OOS edge. This may not be made up by ETH gains (ETH OOS Δ = -2.40 oracle).

These counter-arguments are NOT defeaters — they sharpen the falsifier F1 boundary. The experiment runs precisely BECAUSE the answer is uncertain.

---

## Section 6 — Risk Mitigation (required per merge-candidate skill rule)

R5 itself IS the risk mitigation. The /010 brief is risk-Mitigation-by-design; this section addresses interactions with existing R1/R2/R3 layers and risk-of-the-experiment.

### 6.1 R5 ↔ R2 interaction (Model E only)

Model E uses R2 (drawdown-triggered scaling, trigger=7%, anchor=15%, floor=0.33). When R2 is firing (BASELINE_V1.md: 71% IS / 63% OOS at Model E with mean weight 0.330), R5 multiplies the already-reduced weight. Worst-case double-attenuation:
- R2 floor 0.33 × R5 worst-case (high NATR on DOT, p99 NATR_14 = 13.4%): R5 = min(1.0, 4.0/13.4) = 0.298
- Joint weight = 0.33 × 0.298 = **0.098** — minimum position size of ~10% baseline

This is **acceptable**: 10% position size at vol-spike entries is conservative-but-not-zero risk-off. Brief Section 7 Failure Mode 3 acknowledges this.

### 6.2 R5 ↔ R1 interaction (Models C, D, E)

R1 (consecutive-SL cooldown, K=3, C=27 candles) is BINARY (entry blocked, weight unchanged when not blocked). No multiplicative interaction with R5. Orthogonal layers.

### 6.3 R5 ↔ R3 interaction (ALL models)

R3 (OOD Mahalanobis gate, 70th-percentile cutoff) is BINARY (entry rejected pre-signal). Operates BEFORE Optuna prediction. R5 operates AFTER signal. Orthogonal layers.

### 6.4 IS-calibrated thresholds (mandatory per `feedback_risk_mitigation_design.md`)

- `risk_r5_vol_target_pct = 4.0` — calibrated from Phase 1.1-1.4 IS-only NATR distributions; chosen as in-band optimum from F2-band check; consistent with universe p75 ≈ 4.7% (capping at p75-ish).
- F2 mis-calibration tripwire: fire rate band [10%, 60%] OOS — falsifier F2.

### 6.5 Simulated historical effect on past iterations

The R5 oracle on the baseline trade roster (Section 2.4) shows what /010 would do if Optuna's hyperparameters were FROZEN at the baseline run. The simulation is honestly NEGATIVE oracle, so /010 must justify itself either as:
- (a) An accepted small Sharpe-degradation tradeoff for variance reduction (max drawdown reduction would be an alternative gate, but not in current /010 falsifier set), OR
- (b) An empirical test of whether Optuna re-optimization can produce a NEGATIVE → POSITIVE flip when reward surface changes.

This brief presents BOTH cases honestly. The experiment is being run BECAUSE the oracle is at the boundary; an unambiguous oracle (very positive or very negative) would not justify running.

### 6.6 Kill-switch criteria (mandatory)

If any of the following fire mid-flight, the iteration is killed:
- IS Sharpe < -0.50 in first month of monthly walk-forward (would indicate catastrophic Optuna miss) — KILLED
- DEGENERATE_PREDICTOR fires in first 4 monthly cells (Models A + C + D + E first month) — KILLED, data integrity defect
- Optuna stalls (no successful trial in any (model, month, seed) cell > 5 min) — KILLED, infrastructure defect

Per /008 design, the v1 runner emits monthly progress; the QE can intervene if the runner's first-month outputs already exhibit one of the above.

---

## Section 7 — Failure Modes (mandatory per skill brief template)

### Failure Mode 1 — R5 cap too tight (mis-calibration to high firing)
- **Mechanism**: vol_target_pct < universe mean p50 NATR_14 (~3.5%). Cap fires constantly, becomes a constant brake not a ceiling. Trade economics distorted.
- **Detection**: F2 fire rate > 80% (portfolio OOS).
- **Verdict**: NEGATIVE-mis-calibrated.
- **Pre-emptive defense**: vol_target_pct = 4.0% calibrated to fire at ~15% OOS — well below 80% tripwire.

### Failure Mode 2 — R5 cap too loose (no effect / PROMISING-INERT)
- **Mechanism**: vol_target_pct > universe p95 NATR_14 (~8%). Cap fires rarely (< 5% trades). Inactive.
- **Detection**: F2 fire rate < 5% (portfolio OOS).
- **Verdict**: PROMISING-INERT (no effective intervention).
- **Pre-emptive defense**: vol_target_pct = 4.0% predicted fire rate 15.3% — comfortably above 5% floor.

### Failure Mode 3 — R5 × R2 double-attenuation on Model E
- **Mechanism**: when R2 already at floor 0.33 + R5 at extreme cap 0.30, joint weight ≈ 0.10. Position size cut by 90%.
- **Detection**: Model E OOS trade counts < 30 (vs baseline 46) suggests excessive zero-weighting.
- **Verdict**: NEGATIVE-Model-E-overrestriction.
- **Pre-emptive defense**: Section 6.1 documents this is acceptable; falsifier F2 fire rate check covers it indirectly.

### Failure Mode 4 — Optuna re-optimization with scaled rewards finds new IS-overfit basin
- **Mechanism**: per /005 capacity-fit-noise lesson, single-seed=42 Optuna can fit IS into a different basin when reward distribution changes. R5 changes reward distribution → may produce IS Sharpe overshoot + OOS catastrophic.
- **Detection**: F1 NEGATIVE-catastrophic (-0.20) + F3 simultaneous (IS Δ very NEGATIVE) → catastrophic-both.
- **Verdict**: NEGATIVE-NEGATIVE compound.
- **Pre-emptive defense**: single-seed=42 + ENSEMBLE_SIZE=3 at EXPLORATION is the canonical v1 cycle-2 spec; mitigation is /011 multi-seed CONFIRMATION IF /010 PROMISING per HIGH-RISK Section 2.5 pre-commit.

### Failure Mode 5 — R5 cuts LINK position size disproportionately, removes top OOS contributor
- **Mechanism**: BASELINE_V1.md LINK = +34.23% OOS (137.7% of denominator). LINK has highest NATR_14 (p50 = 4.35%). R5 fires most often on LINK → cuts LINK position size more than any other symbol → cuts the strongest OOS edge contributor most.
- **Detection**: per-symbol OOS LINK net_pnl < baseline by > 20%.
- **Verdict**: NEGATIVE-edge-source-erosion.
- **Oracle prediction**: LINK OOS Δ = -2.50pp (11% reduction in LINK's OOS edge).
- **Counter-pre-emption**: this IS the central tension of /010. If R5 reduces LINK by less than overall variance reduction, R5 is Pareto-positive. If R5 reduces LINK by more, R5 is Pareto-negative.

---

## Section 8 — Verdict Gates

### PROMISING (favorable, advances to /011 CONFIRMATION consideration)
- F1: OOS Sharpe Δ ≥ +0.05 (strict; not just "neutral")
- F3: IS Sharpe Δ ≥ -0.05
- F2: portfolio OOS fire rate ∈ [10%, 60%]
- F4: 0 DEGENERATE_PREDICTOR fires
- F5: DSR mathematically computable (n_eff_per_cell_median ≥ 4)
- Trade-rate floor: ≥ 10 OOS/month, ≥ 130 OOS total

### PROMISING-INERT (cap fires mechanically but Sharpe-neutral)
- F1: OOS Sharpe Δ ∈ [-0.05, +0.05]
- F3: IS Sharpe Δ ∈ [-0.10, +0.05]
- F2: portfolio OOS fire rate ∈ [10%, 60%]
- F4: 0 DEGENERATE_PREDICTOR fires
- F5: DSR computable
- Trade-rate floor: ≥ 10 OOS/month, ≥ 130 OOS total

### NEGATIVE (any single failure of F1/F3/F4/F5 below PROMISING-INERT band)
- F1: OOS Sharpe Δ < -0.05 → NEGATIVE
- F1 catastrophic: OOS Sharpe Δ < -0.20 → NEGATIVE-catastrophic
- F3: IS Sharpe Δ < -0.10 → NEGATIVE-catastrophic-IS (independent of F1)
- F4 fires: NEGATIVE-data-integrity (subtype per detector)
- F5 fires: NEGATIVE-methodology-regression

### NEGATIVE-NEGATIVE compound (per /007 + /009 cycle-2 pattern)
- Both F1 < -0.05 AND F3 < -0.10 simultaneously → NEGATIVE-NEGATIVE compound, classify as cycle-2 pattern-continuation (3rd occurrence after /007 + /009)

### NEGATIVE-mis-calibrated (F2 boundary)
- F2 portfolio OOS fire rate < 5% OR > 80% → NEGATIVE-mis-calibrated, regardless of F1/F3

### PROMISING tripwire commitment (per Section 2.5)
- If verdict = PROMISING, /011 launches as multi-seed CONFIRMATION at ENSEMBLE_SIZE=10 + 10-seed validation per the HIGH-RISK pre-commit at Section 2.5

---

## Section 9 — Library Stack Declaration (mandatory per /009 closeout amendment)

The /010 backtest uses the following libraries — pinned by `pyproject.toml` and `uv.lock` at branch HEAD:

- **lightgbm** — exact pin from `uv.lock`
- **optuna** — exact pin
- **pandas** + **pyarrow** — for feature parquet IO
- **numpy** — for R5 cap computation
- **scikit-learn** — for OOD Mahalanobis gate (R3) and PCA in dsr.json
- **statsmodels** — for ADF tests in /008 reporting
- **scipy** — for PSR/DSR computation
- **pandas-ta** — for vol_natr_14 feature (already in baseline; no new dep)

**No new dependencies introduced.** The R5 implementation uses only `numpy` (already in stack) and `math` (stdlib). The NATR_14 column is loaded from the same feature parquets the strategy already loads.

---

## Section 10 — Implementation Spec (for QE Phase 6)

### 10.1 src/ diff summary (verbatim spec for QE)

1. **`src/crypto_trade/backtest_models.py`**: insert AFTER line 76 (after `risk_drawdown_scale_anchor_pct`):
   ```python
   # Risk mitigation R5 (iter-v1/010): per-symbol vol-target ceiling.
   # When enabled, scales weight_factor by min(1.0, risk_r5_vol_target_pct /
   # max(NATR_14, 0.01)). NATR_14 is read from per-symbol feature parquet at
   # backtest init. Applied AFTER R2 in the vt_scale pipeline. Default
   # disabled — restoring risk_r5_vol_target_enabled=False preserves
   # byte-identical legacy behavior on all iterations through /009.
   risk_r5_vol_target_enabled: bool = False
   risk_r5_vol_target_pct: float = 4.0
   ```

2. **`src/crypto_trade/backtest.py`**:
   - Build `r5_natr_lookup: dict[tuple[str, int], float]` at backtest init (around the existing per-symbol data loading; suggested location L≈100-150 — mirror `vt_per_sym_daily` discipline). Code skeleton (QE finalizes):
     ```python
     r5_natr_lookup: dict[tuple[str, int], float] = {}
     if config.risk_r5_vol_target_enabled:
         from pyarrow.parquet import read_table  # noqa: PLC0415
         for sym in config.symbols:
             feat_path = Path("data") / "features" / f"{sym}_{config.interval}_features.parquet"
             if feat_path.exists():
                 tab = read_table(feat_path, columns=["open_time", "vol_natr_14"])
                 ots = tab.column("open_time").to_numpy()
                 natrs = tab.column("vol_natr_14").to_numpy()
                 mask = ~np.isnan(natrs)
                 for ot, natr in zip(ots[mask], natrs[mask], strict=True):
                     r5_natr_lookup[(sym, int(ot))] = float(natr)
     ```
   - Insert R5 block after R2 (after current line 388):
     ```python
     # R5 — vol-target ceiling (iter-v1/010; ALL MODELS)
     if config.risk_r5_vol_target_enabled:
         natr = r5_natr_lookup.get((sym, int(ot)), float("nan"))
         if not math.isnan(natr):
             r5_scale = min(1.0, float(config.risk_r5_vol_target_pct) / max(natr, 0.01))
             vt_scale = vt_scale * r5_scale
     ```
   - Add `r5_natr_lookup_fires` counter for observability (analogous to risk_v2's `drawdown_brake_fires`) — write to reports' run.log:
     ```python
     # At backtest end:
     if config.risk_r5_vol_target_enabled:
         print(f"R5 fired on {r5_fires} of {n_total_signals} signals ({100*r5_fires/n_total_signals:.1f}%)")
     ```

3. **`run_baseline_v1.py`**: at L≈164-185 (inside `run_model`, BacktestConfig construction), append 2 fields:
   ```python
   risk_r5_vol_target_enabled=True,
   risk_r5_vol_target_pct=4.0,
   ```

### 10.2 Tests (Phase 6 QE deliverable)

`tests/test_iteration_v1_010_r5.py` covers:

1. **R5 OFF parity**: BacktestConfig with `risk_r5_vol_target_enabled=False` produces byte-identical trade roster vs baseline (sanity)
2. **R5 ON cap math**: synthetic 1-trade config; assert `weight_factor == vt_scale * min(1.0, 4.0/natr)` for known NATR value
3. **R5 ON boundary**: `vol_target_pct = NATR_14 exact` produces `r5_scale = 1.0` (no cap)
4. **R5 ON missing NATR**: when `(sym, ot)` not in `r5_natr_lookup`, R5 skips (no nan propagation; weight_factor unchanged)
5. **R5 × R2 multiplicative**: assert `vt_scale * r2_scale * r5_scale == joint_weight` for synthetic case
6. **DEGENERATE_PREDICTOR detector** (per /008): runs on /010 reports

### 10.3 Reports schema (no changes vs /008-/009)

`reports-v1/iteration_v1-010/` produces:
- `comparison.csv` (10 rows + 1 new row "r5_fire_rate_oos")
- `in_sample/` and `out_of_sample/` with full v1 report stack
- `dsr.json` per /008 schema (n_eff_per_cell_median + degenerate detector)
- IS+OOS adf_test.csv, ic_matrix.csv, per_symbol.csv, per_regime.csv, trades.csv, daily_pnl.csv, monthly_pnl.csv, quantstats.html
- ADD: `r5_fire_log.csv` (per-trade NATR_14, r5_cap_applied, r5_fired_bool) for forensic checks

### 10.4 Wall-clock estimate

Same as /008-/009: ~75-90 min single-seed × 4 models × 35 trials × 5 inner CV splits. R5 adds < 1% overhead (one dict lookup per signal). Within ≤ 2h cap.

### 10.5 Configuration single-source-of-truth

The `vol_target_pct = 4.0` value lives in ONE place: `BacktestConfig.risk_r5_vol_target_pct` default + `run_baseline_v1.py:run_model` literal. No other configuration file (or `live/models.py`) need touch for EXPLORATION — live wiring is CONFIRMATION-spec only.

---

## Section 11 — Alternate Designs (for Critic 6.0 review)

The brief Section 2 evidence converged on `vol_target_pct = 4.0` as the primary calibration. If Critic 6.0 disagrees on the calibration choice, the next-best fallback values are:

| Alternate | vol_target | OOS oracle Δ | OOS fire rate | Justification |
|---|---|---|---|---|
| **PRIMARY** | **4.0%** | **-0.020** | **15.3%** | **calibrated optimum; F2-band-center; conservative ceiling** |
| Alt-1 | 3.5% | -0.027 | 27.5% | more activity; F2 still in band; slightly more aggressive |
| Alt-2 | 4.25% | -0.015 | 11.6% | more conservative; F2 edge of band but still in |

The brief does NOT propose a grid sweep — that would require multiple Optuna runs and exceed the ≤2h EXPLORATION cap. /010 commits to vol_target = 4.0%. If /010 is PROMISING, /011 CONFIRMATION can include vol_target ∈ {3.5, 4.0, 4.25} as a 3-point ablation.

---

## Section 12 — Catalog Closeout Plan

If /010 outcome:

- **PROMISING**: catalog entry `risk-primitive` / `EXPLORATION-PROMISING` → /011 = multi-seed CONFIRMATION of R5 at vol_target=4.0 per Section 2.5 HIGH-RISK pre-commit.
- **PROMISING-INERT**: catalog entry `risk-primitive` / `EXPLORATION-PROMISING-INERT` → axis CLOSED at single-seed EXPLORATION; /011 pivots to next UNUSED axis (model-arch ensembling at fewer outer seeds OR labeling triple-barrier σ_t source OR new feature-family at multi-seed).
- **NEGATIVE / NEGATIVE-NEGATIVE**: catalog entry `risk-primitive` / `EXPLORATION-NEGATIVE` → axis NOT closed (R5 design space larger than vol-target ceiling; binary kill switches and per-symbol regime-conditional caps remain unexplored).
- **NEGATIVE-mis-calibrated**: vol_target re-calibration EXPLORATION at /011 with vol_target ∈ {3.0, 5.0, 6.0} candidates per Section 11 — same risk-primitive family but different parameter region.

In all cases the next /011 brief Section 0.6 declares rotation status: NEGATIVE = rotation valid since UNUSED families still exist; PROMISING-INERT = rotation valid; PROMISING = same family at CONFIRMATION which is exempt from rotation.

---

## Section 13 — Phase 5.5 Gate Self-Check

QR self-attestation of 11 mandatory sections (per `quant-iteration-v1.md` Phase 5.5):

- [x] Section 0 (subsections 0.1-0.6) — anchor, mode, label, determinism, cadence, axis-family
- [x] Section 1 — hypothesis
- [x] Section 2 — IS-only evidence with numerical tables (4 tables × 5-7 rows each)
- [x] Section 2.5 — HIGH-RISK axis declaration
- [x] Section 3 — proposed changes + LM Master responses + Critic responses
- [x] Section 4 — falsifiers (F1-F5) including behavioral F2 with explicit numerical pre-registration
- [x] Section 5 — expected OOS impact + counter-evidence
- [x] Section 6 — risk mitigation (R5 interactions; IS-calibrated thresholds; kill-switch)
- [x] Section 7 — failure modes (5 modes)
- [x] Section 8 — verdict gates (PROMISING / PROMISING-INERT / NEGATIVE / NEGATIVE-NEGATIVE / NEGATIVE-mis-calibrated)
- [x] Section 9 — library stack declaration
- [x] Section 10 — implementation spec for QE
- [x] Section 11 — alternate designs (for Critic 6.0)
- [x] Section 12 — catalog closeout plan
- [x] Section 13 — Phase 5.5 self-check (this)

Cadence count check (per skill): cycle-2 = 5 of 10 EXPLORATIONs. /010 is EXPLORATION mode (not CONFIRMATION); cadence rule satisfied (no 10-EXPLORATION prerequisite for EXPLORATION).

Axis Rotation Discipline check: prior 5 = `hyperparameter-region, universe, feature-family, methodology, feature-family`. None of these are `risk-primitive`. Rotation VALID per Section 0.6.

LM Master /009 Phase 7.4 PRIMARY recommendation: ADOPTED at Section 3.2 (R5 vol-target ceiling) with vol_target_pct revised from 2.5% → 4.0% per Section 2 EDA calibration — explicit response logged.

Critic /009 Path Forward #1 (PRIMARY R5): ADOPTED at Section 3.3 — explicit response logged.

DEGENERATE_PREDICTOR detector check: /010 runs the /008 detector by inheritance; F4 falsifier presence verified.
