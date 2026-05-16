# Iteration iter-v3/050 — Diary

## Decision: CONFIRMATION-NO-MERGE-revert — BOTH-must-improve gate FAILS on IS axis (-0.19 regression); cycle 3 COMPLETE; per-symbol-customization anti-pattern SYSTEM-LEVEL CONFIRMED across 2 cycles

iter-v3/050 = **SECOND v3 CONFIRMATION** post-iter-v3/028 BASELINE_V3.md (THIRD in v3 history after iter-v3/018 BOOTSTRAP and iter-v3/039 NO-MERGE). Multi-seed validation of the cycle 3 best PROMISING bundle: V3_FEATURE_COLUMNS_TOP_N=14 (regime_momentum_signed_5d PRESENT; vol_normalized_ret_5d ABSENT per /048 closeout); V3_ATR_MULTIPLIERS_PER_SYMBOL={ALGOUSDT: (2.0, 1.5), LDOUSDT: (2.0, 1.5)} (per /044 + /045 PROMISING); RiskV2Config(block_long_for=("BCHUSDT",)) primitive 10 carry-forward (per /047 IS-only-validated CANDIDATE; first multi-seed OOS test in clean conditions); adx_threshold_per_symbol={} (per /049 closeout — TRX 21 DROPPED). Run spec: `--seeds 2 --n-trials 35` (CONFIRMATION-spec; 1400 total Optuna trials = 4 syms × 5 inner × 2 outer × 35).

Result: **IS multi-seed mean Sharpe +0.3189 / OOS multi-seed mean Sharpe +0.7404.** Per the strict BOTH-must-improve rule (`feedback_v3_strict_both_is_oos_baseline.md` 2026-05-09 directive at iter-v3/039 closeout), the BASELINE_V3.md update gate requires BOTH IS AND OOS multi-seed mean Sharpe to beat the iter-v3/028 anchor (+0.5101 IS / +0.5053 OOS). iter-v3/050 satisfies this on the OOS axis (Δ +0.235) but FAILS on the IS axis (Δ -0.19 regression). Per the locked Section 8 mechanical criteria, verdict path resolved as **CONFIRMATION-NO-MERGE-revert** — `BASELINE_V3.md UNCHANGED at iter-v3/028`.

The OOS Sharpe of +0.7404 is the second-highest multi-seed OOS reading in v3 history (after iter-v3/039's +1.4650, which also failed BOTH-must-improve). However the IS axis regression is the binding constraint per the strict version of the policy: **OOS-only improvement with IS regression = NO MERGE.**

**SYSTEM-LEVEL CONFIRMATION**: iter-v3/039 (cycle 2 CONFIRMATION, IS -0.59 / OOS +0.96, NO MERGE) and iter-v3/050 (cycle 3 CONFIRMATION, IS -0.19 / OOS +0.235, NO MERGE) both bundle per-symbol customizations and both produce the SAME asymmetric IS-regression-OOS-improvement pattern. The "suspicious-OOS-divergence" pattern observed at single-seed EXPLORATIONs iter-v3/026/027/030/034/036/037 PERSISTS at multi-seed across TWO INDEPENDENT CYCLES. The pattern is no longer a hypothesis — it is a system-level constraint. Memory rule `feedback_v3_per_symbol_lifts_oos_breaks_is.md` updated by orchestrator with second-cycle confirmation.

Per Critic FINAL `b6339c5`, all 12 standard methodology checks PASS (look-ahead, embargo, IC, ADF, hypothesis-implementation alignment, library pinning, etc.); all 3 hard-blocking gates (Gate 3 OOS/IS ratio 2.32, Gate 6 PSR 1.0, Gate 10 Pareto both seeds positive) PASS. The NO-MERGE decision is driven exclusively by the BASELINE_V3.md update gate (IS regression), not by hard-blocking gate failure or methodology defect. The iteration is a CLEAN scientific result: hypothesis was specific, testable, falsifiable; the test fired and the answer is "NO."

Per `feedback_v3_strict_10_to_1_cadence.md`: **cycle 3 closure is COMPLETE** with NO-MERGE. iter-v3/051 begins cycle 4 = #1 of 10 EXPLORATIONs; iter-v3/061 = cycle 4 CONFIRMATION.

## What Was Tested

**Hypothesis (locked in brief Section 1):** "The cycle 3 best PROMISING bundle (regime_momentum_signed_5d + ALGO/LDO per-symbol ATR (2.0, 1.5) + primitive 10 BCH LONG block) PRESERVES IS lift AND OOS lift at multi-seed `--seeds 2`, satisfying the BASELINE_V3.md update gate (BOTH IS AND OOS multi-seed mean > iter-v3/028 anchor +0.5101 / +0.5053)."

**Predicted bands (locked in brief Section 4):**
- IS Sharpe: [+0.40, +0.65] median +0.52 (vs iter-v3/028 anchor +0.5101)
- OOS Sharpe: [+0.55, +1.50] median +1.00 (vs iter-v3/028 anchor +0.5053)
- Bundle OOS trade count: 90-130 (target ≥130 floor)
- IS-OOS daily Sharpe ratio: ∈ [0.5, 2.5] (clean lift, not pathological)
- Top-symbol concentration: 35-65% (likely above 30% aspirational gate)

**Spec (locked in brief Section 0.5; setup commit SHA `45ddb0f`):**
- ITERATION_LABEL = "v3-050"
- DROP `adx_threshold_per_symbol={"TRXUSDT": 21.0}` → `adx_threshold_per_symbol={}` per Critic FINAL `1908d50` rec #2
- KEEP V3_ATR_MULTIPLIERS_PER_SYMBOL = {ALGOUSDT: (2.0, 1.5), LDOUSDT: (2.0, 1.5)} (carry-forward from /045)
- KEEP RiskV2Config(block_long_for=("BCHUSDT",)) primitive 10 (carry-forward from /047)
- KEEP V3_FEATURE_COLUMNS_TOP_N = 14 (regime_momentum_signed_5d PRESENT; vol_normalized_ret_5d ABSENT)
- V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT, ALGOUSDT) — 4 symbols (UNCHANGED)
- REQUIRED_GAP = 88 = (21+1) × 4 (UNCHANGED)
- Runner: `uv run python run_baseline_v3.py --seeds 2 --n-trials 35 --clean-oof`
- ENSEMBLE_SIZE = 5 (auto for non-exploration mode)
- 5 adversarial tests in `tests/strategies/ml/test_per_symbol_adx_threshold.py` PASS (empty dict default-behavior preserved)
- Wall-clock: 5.05h (within 6h CONFIRMATION cap)
- Total Optuna trials: 1400 = 4 syms × 5 inner × 2 outer × 35

## Headline Numbers

### Multi-seed primary (comparison.csv + seed_summary.json)

| Metric | iter-v3/028 BASELINE | iter-v3/045 single-seed anchor | **iter-v3/050 multi-seed mean** | Δ vs iter-v3/028 | Compression vs /045 |
|---|---:|---:|---:|---:|---:|
| **IS monthly Sharpe (multi-seed mean)** | +0.5101 | +0.7459 | **+0.3189** | **-0.1912** | **-57.3% compression** |
| **OOS monthly Sharpe (multi-seed mean)** | +0.5053 | +3.5259 | **+0.7404** | **+0.2351** | **-79.0% compression** |
| OOS/IS Sharpe ratio | 0.99 | 4.73 | **2.32** | +1.33 | within band |
| IS Trades (mean) | 182 | 250 | 282.5 | +100 | n/a (mean of 2 seeds) |
| OOS Trades (per seed) | 96 / 91 | 119 | 93 / 94 | -3/+3 | comparable |
| OOS Trades (mean) | 93.5 | 119 | 93.5 | 0 | comparable |
| IS MaxDD (seed 42) | 41.43% | 66.06% | 60.97% | +19.5pp worse | improvement vs /045 |
| OOS MaxDD (mean) | 23.53% | 13.26% | 27.83% | +4.3pp worse | regression vs /045 |
| OOS Calmar (mean) | 0.9229 | 7.31 | **1.2911** | +0.37 | improvement vs /028 |
| OOS Top-symbol concentration (mean) | 76.47% | 54.77% (ALGO) | **43.64%** | -32.8pp better | improvement vs /028 |
| DSR | 0.0 | 0.0 | 0.0 | structural | structural at v3 trade volume |
| PBO mean | 0.1243 | 0.0782 | **0.0939** | -0.03 | within tolerance |
| PSR | 1.0 | 1.0 | **1.0** | saturation | saturation |
| n_trials | 1050 | 140 (single-seed EXPLORATION) | 1400 | +350 | CONFIRMATION-spec |
| n_eff | 19 | 19 | 18 | -1 | acceptable |

### Per-seed Pareto Front (BOTH SEEDS POSITIVE — Gate 10 PASS)

| Outer Seed | IS Sharpe | OOS Sharpe | OOS MaxDD | OOS Calmar | OOS Trades | Top OOS Conc |
|---|---:|---:|---:|---:|---:|---:|
| 42 | +0.4872 | **+1.1659** | 20.21% | 2.2944 | 93 | 45.68% |
| 123 | +0.1506 | +0.3149 | 35.45% | 0.2878 | 94 | 41.59% |
| **Mean** | **+0.3189** | **+0.7404** | 27.83% | 1.2911 | 93.5 | 43.64% |
| **Ratio 42/123** | 3.23× | **3.70×** | 0.57 | 7.97× | 1.01× | 1.10× |

Seed 42 is a clear lottery winner: 3.70× higher OOS Sharpe than seed 123 at trade-count parity (93 vs 94), 7.97× higher Calmar, ~15pp lower max drawdown. Trade count parity rules out path-level randomness in label/feature pipeline; the difference is entirely Optuna chosen hyperparameters at n_trials=35 per cell. **The 3.70× inter-seed dispersion is ~2× MORE dispersed than iter-v3/028's 1.72× ratio (+0.5053 / +0.8691 → 1.72×). At the iter-v3/028 robustness benchmark, iter-v3/050 fails by a factor of 2.**

### Per-symbol decomposition (seed 42 primary)

**IS per-symbol (seed 42):**

| Symbol | trades | win_rate | net_pnl_pct | pct_of_total |
|---|---:|---:|---:|---:|
| BCHUSDT | 50 | 46.0% | +65.77% | +119.5% |
| TRXUSDT | 85 | 35.3% | +7.40% | +13.4% |
| ALGOUSDT | 51 | 45.1% | -5.94% | -10.8% |
| LDOUSDT | 15 | 40.0% | -12.19% | -22.1% |

IS: BCH carries 119.5% of total IS PnL. ALGO and LDO are IS-negative (-10.8% / -22.1%). TRX is marginally positive. The IS Sharpe of +0.4872 (seed 42) is held up by BCH alone.

**OOS per-symbol (seed 42):**

| Symbol | trades | win_rate | weighted_pnl | concentration_pct |
|---|---:|---:|---:|---:|
| TRXUSDT | 46 | 54.3% | +29.92 | +64.53% |
| ALGOUSDT | 14 | 50.0% | +27.35 | +58.99% |
| BCHUSDT | 21 | 47.6% | +8.23 | +17.74% |
| LDOUSDT | 12 | 33.3% | **-19.13** | **-41.27%** |

OOS: TRX and ALGO are the positive contributors (+57 wpnl combined). LDO is the structural drag at -19.13 weighted_pnl (33.3% WR). BCH is mildly positive (+8.23). LDO's -41.27% OOS concentration depresses the multi-seed mean.

### §8 Pre-registered Verdict (mechanical, non-renegotiable)

| Path | Threshold | Observed | Trigger |
|---|---|---|---|
| CONFIRMATION-MERGE-FULL | All 10 gates including aspirational ≥+1.0 floors | IS +0.32 < +1.0 (gate 1 FAIL); OOS +0.74 < +1.0 (gate 2 FAIL) | NO |
| CONFIRMATION-MERGE-BOOTSTRAP-style | BOTH IS+OOS > /028 anchor AND hard-blocking gates 3, 6, 10 PASS | IS +0.32 < +0.5101 (BASELINE update gate FAIL on IS axis) | NO |
| **CONFIRMATION-NO-MERGE-revert** | IS multi-seed mean ≤ /028 anchor OR OOS ≤ /028 anchor OR hard-blocking gate fail | **IS +0.32 ≤ +0.5101 → BASELINE update gate FAILS on IS axis** | **YES** |

## MERGE Gate Evaluation (per brief Section 8 LOCKED criteria)

### BASELINE_V3.md update gate (BOTH-must-improve per `feedback_v3_strict_both_is_oos_baseline.md`)

| Axis | iter-v3/050 multi-seed mean | iter-v3/028 anchor | Δ | Gate Result |
|---|---:|---:|---:|---|
| IS monthly_sharpe | **+0.3189** | +0.5101 | **-0.1912** | **FAIL** |
| OOS monthly_sharpe | **+0.7404** | +0.5053 | +0.2351 | PASS |

**RESULT: BASELINE_V3.md UPDATE BLOCKED.** IS regression of -0.19 fails the BOTH-must-improve rule regardless of OOS improvement. SAME asymmetric failure pattern as iter-v3/039.

### Hard-blocking gates (Gates 3, 6, 10)

| Gate | Threshold | Observed | Status |
|---|---|---|---|
| Gate 3: OOS/IS Sharpe ratio ≥ 0.5 | ≥ 0.5 | 0.7404 / 0.3189 = **2.32** | **PASS** |
| Gate 6: PSR > 0.95 | > 0.95 | **1.0000** | **PASS** |
| Gate 10: BOTH outer seeds Sharpe > 0 | both > 0 | seed 42: +1.1659 / seed 123: +0.3149 | **PASS** |

All 3 hard-blocking gates PASS. The NO-MERGE decision is driven exclusively by the BASELINE_V3.md update gate (IS regression).

### Aspirational gates (informational only per `feedback_v3_baseline_update_policy.md`)

| Gate | Threshold | Observed | Status |
|---|---|---|---|
| Gate 1: IS Sharpe ≥ +1.0 | ≥ 1.0 | +0.32 (mean) | FAIL (informational) |
| Gate 2: OOS Sharpe ≥ +1.0 | ≥ 1.0 | +0.74 (mean) | FAIL (informational) |
| Gate 4: DSR > 0.95 | > 0.95 | 0.0 | FAIL (structural at v3 trade volume) |
| Gate 5: PBO mean < 0.4 | < 0.4 | 0.0939 | PASS |
| Gate 7: Top-symbol concentration ≤ 30% | ≤ 30% | TRX 64.53% (seed 42); 43.64% mean | FAIL (informational) |
| Gate 8: Bundle OOS trades ≥ 130 | ≥ 130 | 187 aggregate (per-seed: 93 / 94) | PASS at aggregate; per-seed FAIL |
| Gate 9: 10-seed pre-MERGE concentration validation | mean>0, ≥7/10 | NOT RUN | NOT TRIGGERED (per Critic recommendation; gate only fires if main 2-seed clears BOTH-must-improve) |

**3 PASS / 4 FAIL of 7 aspirational gates evaluated.** Per `feedback_v3_baseline_update_policy.md` 2026-05-08 directive, aspirational gate failures inform future-iteration priorities but do NOT block baseline updates. The binding constraint for iter-v3/050 is the BASELINE_V3.md update gate (IS regression), NOT aspirational gate failures.

## What Worked

- **Methodology of the run is clean.** All 12 standard methodology checks PASS per Critic FINAL `b6339c5`:
  - Check 1 (Look-ahead) PASS — single-kwarg DROP introduces NO new look-ahead surface; trade-row PnL spot-check on row 100 (TRX SL) and row 102 (BCH TP) matches CSV
  - Check 2 (Embargo width) PASS — REQUIRED_GAP=88 unchanged
  - Check 3 (Multiple-testing) MIXED — DSR 0.0 FAIL structural at n_trials=1400 (same root cause as iter-v3/018/028/039); PBO 0.0939 PASS; PSR 1.0 PASS
  - Check 4 (IC) PASS — composed-feature carve-out for regime_momentum (max |IC|=0.7790 with vwap_dev_20)
  - Check 5 (ADF stationarity) PASS — identical to iter-v3/028 audit (1803/2198 cells stationary)
  - Check 6 (Pareto) PASS — both outer seeds Sharpe > 0
  - Check 7 (Reproducibility) PASS — setup `45ddb0f`, brief `acc6baf`, engineering report `56c671b`, Critic FINAL `b6339c5`; full audit chain present
  - Check 8 (Hypothesis-Implementation alignment) PASS — bundle correctly applied; hypothesis FALSIFIED on IS axis (clean scientific result)
  - Checks 9-12 PASS or N/A
  - Track isolation: ZERO matches for `from crypto_trade.features` or `features_v2` in `features_v3/`
  - Forming-candle audit: PASS (data freshness re-fetched at Phase 5.5)

- **OOS multi-seed Sharpe +0.74 is the second-highest in v3 history** (after iter-v3/039's +1.47). This confirms the v3 architecture (4-symbol BCH+LDO+TRX+ALGO, regime_momentum, per-symbol ATR + primitive 10) CAN clear the iter-v3/028 OOS anchor at multi-seed CONFIRMATION-spec.

- **OOS top-symbol concentration substantially improved.** Multi-seed mean 43.64% vs iter-v3/028's 76.47% — a 32.8pp improvement driven by 4-symbol diversification (ALGO addition at iter-v3/033 distributing PnL across 4 symbols instead of 3). Still above the 30% aspirational gate, but materially closer.

- **OOS Calmar improved.** Multi-seed mean 1.29 vs iter-v3/028's 0.92 — a +0.37 Calmar lift (driven by seed 42's strong 2.29).

- **OOS trade count improved.** Aggregate 187 trades (vs iter-v3/028's 187.5 mean = 96+91); per-seed 93/94 vs /028's 96/91 (comparable).

- **Both Pareto seeds positive (+1.1659 and +0.3149).** Gate 10 PASS — methodological bright spot.

- **The brief's calibration was accurate.** Brief Section 7 P6 pre-registered the "iter-v3/039 anti-pattern" at P=25% as the DOMINANT failure mode. Brief Section 4.2 predicted IS multi-seed mean ∈ [+0.40, +0.65] median +0.52, OOS ∈ [+0.55, +1.50] median +1.00. Observed: IS +0.3189 (slightly BELOW lower band; -0.0811 outside), OOS +0.7404 (within band). The QR's brief is methodologically sound; the bundle itself is the problem, not the prediction.

- **Per-symbol architecture validated as CODE INFRASTRUCTURE.** V3_FEATURES_PER_SYMBOL + V3_ATR_MULTIPLIERS_PER_SYMBOL run cleanly at multi-seed, deterministic with seeds, reproducible, with no cross-symbol contamination. Architecture is KEPT for future cycles.

- **Adversarial test suite preserved.** 5 per_symbol_adx tests PASS with empty dict default-behavior preserved (`test_default_empty_dict_preserves_v3_prior_behavior`); 7 primitive 10 tests PASS; 5 per_symbol_atr tests PASS. The `adx_threshold_per_symbol` field stays in `RiskV2Config` schema for future use.

## What Failed

- **Pre-registered BASELINE_V3.md update gate FAILS on IS axis.** IS multi-seed mean Sharpe +0.3189 < +0.5101 (iter-v3/028 anchor). Per `feedback_v3_strict_both_is_oos_baseline.md` BOTH-must-improve rule (locked Section 8 thresholds non-renegotiable post-hoc), verdict path resolved as CONFIRMATION-NO-MERGE-revert.

- **The cycle 3 PROMISING bundle compressed -57.3% IS / -79.0% OOS at multi-seed validation.** Three EXPLORATION-PROMISING ingredients (ALGO ATR per /044, LDO ATR per /045, primitive 10 BCH LONG block per /047) individually cleared their EXPLORATION PATH-A gates at single-seed but COLLECTIVELY FAILED to produce a multi-seed IS improvement at CONFIRMATION. The compounding of three PROMISING ingredients did NOT produce an additive multi-seed lift; the ingredients appear to be correlated with the seed-42 Optuna draw rather than with structural signal.

- **Inter-seed dispersion ratio 3.70× is ~2× MORE dispersed than iter-v3/028's 1.72× ratio.** This is the diagnostic of a lottery-driven CONFIRMATION — the model has not found robust, reproducible hyperparams. A robust configuration would show seed 42 / seed 123 OOS Sharpe ratio of 1.0–2.0× max; iter-v3/050 at 3.70× indicates Optuna's per-seed hyperparameter trajectories are NOT converging to a robust signal-driven configuration. Trade count parity (93 vs 94) rules out path-level randomness in the label or feature pipeline.

- **LDO is the structural drag** — frozen-baseline pattern at OOS-row level. LDO OOS = -19.13 weighted_pnl, 12 trades, 33.3% WR at seed 42 — BIT-IDENTICAL to iter-v3/047 (-19.13) and iter-v3/049 (-19.13). **Three consecutive single-seed=42 anchorings show LDO is the structural drag.** The per-symbol ATR (2.0, 1.5) for LDO from iter-v3/045 is an IS-positive customization (when measured at iter-v3/045 single-seed) that does NOT translate to OOS at the portfolio level when the binding-constraint anchor moves to /047 + /049 + /050. LDO has now produced negative OOS in EVERY single-seed=42 iteration since iter-v3/047. The iter-v3/045 LDO OOS = +9.34 wpnl was the SEED-SPECIFIC FAVORABLE DRAW; at multi-seed, LDO's structural OOS contribution is -19 wpnl persistent.

- **regime_momentum_signed_5d ranks 14/14 portfolio AND 14/14 LDO** — the confirmed edge ingredient from iter-v3/025/028 is now the LEAST-IMPORTANT feature at both portfolio and LDO levels. Per-symbol ranks: ALGO 13/14 (importance 103.4 vs rank 1's 287.6), BCH 11/14 (90.6 vs 180.4), LDO 14/14 (48.2 vs 144.6), TRX 11/14 (128.4 vs 229.4). After universe expansion to 4 symbols (ALGO added at iter-v3/033), the feature's signal is no longer a top contributor — possibly diluted by ALGO's universe inclusion or by the per-symbol customizations crowding out the universal signal.

- **All 4 OOS symbols regressed vs iter-v3/045 single-seed anchor** at seed 42: ALGO 53.12 → 27.35 (-25.77), BCH 11.31 → 8.23 (-3.08), LDO 9.34 → -19.13 (-28.47), TRX 23.23 → 29.92 (+6.69 only). Net OOS PnL regression -50.6 wpnl across 4 symbols vs /045 single-seed.

- **Aspirational gate failures persist.** Gate 1 (IS ≥ +1.0) FAIL at +0.32. Gate 2 (OOS ≥ +1.0) FAIL at +0.74. Gate 4 (DSR > 0.95) FAIL at 0.0 (structural at v3 trade volume; same root cause as iter-v3/018/028/039 — required SR ≈ 3.5 at n_trials=1400, observed annualized ≈ 1.5-2.0). Gate 7 (concentration ≤ 30%) FAIL at TRX 64.53% (seed 42) / 43.64% (mean). Gate 8 (OOS trades ≥ 130) FAIL per-seed (93 / 94); PASS aggregate (187).

## System-Level Confirmation: Per-Symbol-Customization Anti-Pattern Across 2 Cycles

This is the **central methodological finding of iter-v3/050 closeout**.

### Cross-cycle CONFIRMATION pattern table

| Dimension | iter-v3/039 (cycle 2 CONFIRMATION) | iter-v3/050 (cycle 3 CONFIRMATION) |
|---|---|---|
| Bundle composition | per-symbol customizations: BCH-only fracdiff_d05_close + LDO-only ATR (1.5, 0.75) | per-symbol customizations: ALGO+LDO per-symbol ATR (2.0, 1.5) + primitive 10 BCH LONG block |
| Single-seed anchor (best EXPLORATION PROMISING) | iter-v3/035 IS +0.75 / OOS +2.85 | iter-v3/045 IS +0.75 / OOS +3.53 |
| Multi-seed mean IS Sharpe | -0.0800 (vs /028 +0.5101) | +0.3189 (vs /028 +0.5101) |
| Multi-seed mean OOS Sharpe | +1.4650 (vs /028 +0.5053) | +0.7404 (vs /028 +0.5053) |
| IS Δ vs /028 | **-0.59 (regression)** | **-0.19 (regression)** |
| OOS Δ vs /028 | +0.96 (improvement) | +0.235 (improvement) |
| BOTH-must-improve gate | FAIL (IS axis) | FAIL (IS axis) |
| Verdict | NO MERGE | NO MERGE |
| Asymmetric pattern | OOS↑ + IS↓ | OOS↑ + IS↓ (SAME) |
| Hard-blocking gates | All PASS | All PASS |
| Inter-seed dispersion ratio | 2.77× (1.47/0.53) | 3.70× (1.17/0.31) — WORSE |

**Both CONFIRMATIONs bundle per-symbol customizations and both produce the same asymmetric IS-regression-OOS-improvement pattern.** Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` (established at iter-v3/039 closeout): the suspicious-OOS-divergence pattern PERSISTS at multi-seed across two cycles. The pattern is no longer a hypothesis; it is a **system-level constraint**.

### Memory rule update

Memory rule `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED by orchestrator with second-cycle confirmation. The original rule (established at iter-v3/039 closeout 2026-05-09) cited a single multi-seed observation; the rule now cites TWO INDEPENDENT CYCLES with consistent pattern. Future per-symbol customization additions (per-symbol features, per-symbol labels, per-symbol risk gates) MUST clear IS-axis pre-validation (paired bootstrap CV or IS-only test) BEFORE inclusion in any CONFIRMATION bundle. Per-symbol architecture is INFRASTRUCTURE (KEEP); per-symbol customizations need IS-axis discipline (REJECT bundle assemblies that violate this).

### Mechanism (now confirmed across 2 cycles)

Per-symbol customizations (per-symbol ATR widening, per-symbol fracdiff features, direction-asymmetric kill switches like primitive 10) systematically lift OOS aggregate via specific symbol-regime alignments while reducing IS aggregate via training-window misalignment. The single-seed Optuna draw at PROMISING-anchor-time happens to align IS and OOS for the same symbol; at multi-seed, the alignment dissolves and the asymmetric pattern emerges. The 2-seed mean is dominated by the lottery seed (seed 42 in /050; seed 42 in /039), making the ratio measurement particularly fragile.

## Seed Dispersion Concern: 3.70× vs iter-v3/028's 1.72×

The seed 42 / seed 123 OOS Sharpe ratio of **3.70× is ~2× MORE dispersed than iter-v3/028's 1.72× benchmark**. At iter-v3/028 (first successful CONFIRMATION post-bootstrap), Pareto seeds were +0.5053 / +0.8691 (ratio 1.72×). At iter-v3/050, Pareto seeds are +1.1659 / +0.3149 (ratio 3.70×).

| Reference | Seed 42 OOS | Seed 123 OOS | Ratio | Diagnosis |
|---|---:|---:|---:|---|
| iter-v3/018 BOOTSTRAP | +0.234 | +0.539 | 2.30× | n/a |
| iter-v3/028 baseline | +0.5053 | +0.8691 | 1.72× | robust signal-driven |
| iter-v3/039 NO-MERGE | +1.4650 | +0.5290 | 2.77× | lottery-driven |
| **iter-v3/050 NO-MERGE** | **+1.1659** | **+0.3149** | **3.70×** | **most lottery-driven in v3 history** |

Trade count parity (93 vs 94) rules out path-level randomness in the label or feature pipeline; the difference is entirely in Optuna chosen hyperparameters (which alter the signal threshold and thereby which individual candles trigger entries). A robust configuration would show seed 42 / seed 123 ratio of 1.0–2.0× max; iter-v3/050 at 3.70× is the diagnostic of a lottery-driven CONFIRMATION — the model has not found robust, reproducible hyperparams.

This is consistent with `feedback_v3_per_symbol_lifts_oos_breaks_is.md`: per-symbol customizations introduce single-seed-specific Optuna trajectories, so seed-to-seed dispersion increases when the bundle is assembled. The 2× dispersion increase from /028 to /050 is mechanistic evidence of the per-symbol-customization pathology.

## LDO Structural Drag: Frozen Baseline Across iter-v3/047 + /049 + /050 (Seed 42)

LDO OOS = -19.13 weighted_pnl, 12 trades, 33.3% WR at seed 42 — **BIT-IDENTICAL across THREE consecutive iterations** (iter-v3/047, /049, /050). Per `feedback_v3_single_seed_frozen_baseline.md` (REINFORCED at iter-v3/049 closeout with OOS row-level confirmation): when feature_columns AND data input AND model config are IDENTICAL for a symbol at single-seed=42, the per-symbol Optuna trajectory is bit-deterministic.

LDO's feature stack and ATR multipliers (2.0, 1.5) are IDENTICAL in all three iterations:
- iter-v3/047 (Critic FINAL `785500f`): LDO OOS = -19.13 wpnl, 12 trades, 33.3% WR (verified)
- iter-v3/049 (Critic FINAL `1908d50`): LDO OOS = -19.13 wpnl, 12 trades, 33.3% WR (verified character-for-character bit-identical)
- iter-v3/050 (Critic FINAL `b6339c5`, seed 42): LDO OOS = -19.13 wpnl, 12 trades, 33.3% WR (verified)

The iter-v3/045 single-seed PROMISING-anchor LDO OOS = +9.34 wpnl was the SEED-SPECIFIC FAVORABLE DRAW; at multi-seed CONFIRMATION (and at all carry-forward single-seed=42 iterations from /047 onward), LDO's structural OOS contribution is -19 wpnl persistent. The multi-seed mean of LDO OOS at iter-v3/050 is unknown for seed 123 (per-symbol disaggregation is in `out_of_sample/per_symbol.csv` for the combined-seed projection), but the combined OOS Sharpe collapse at seed 123 (+0.3149 vs +1.1659 at seed 42) suggests seed 123 also struggled with LDO or another symbol.

**Action**: iter-v3/051 EDA must investigate LDO removal as the FIRST cycle 4 EXPLORATION axis. Per Critic FINAL `b6339c5` recommendation #2: "iter-v3/051 EDA must investigate LDO removal. LDO has produced negative OOS in EVERY single-seed iteration since iter-v3/047 (-19.13 frozen baseline at seed 42). LDO's IS-positive ATR customization (2.0, 1.5) is the iter-v3/045 PROMISING ingredient that does NOT survive multi-seed validation at OOS. iter-v3/051 EDA should produce numerical tables comparing 3-symbol BCH+TRX+ALGO vs 4-symbol BCH+LDO+TRX+ALGO at IS-only baseline."

## Bundle Status Update

- **BASELINE_V3.md UNCHANGED at iter-v3/028** (+0.5101 IS / +0.5053 OOS; SHA `b0576df`). Per `feedback_v3_strict_both_is_oos_baseline.md` BOTH-must-improve rule.
- **iter-v3/045 single-seed +0.7459 IS / +3.5259 OOS RETIRED as "lottery winner"** — multi-seed compression -57.3% IS / -79.0% OOS proves the single-seed peak was not edge but Optuna lottery. The iter-v3/045 PROMISING bundle composition is no longer the "best EXPLORATION-PROMISING" record carried forward; it is now a CLOSED experimental result. iter-v3/049 head (with primitive 10 carry-forward but adx_threshold_per_symbol DROPPED) remains the formal "best EXPLORATION-PROMISING" reference, but the cycle 4 starting point should be a per-symbol-customization REVERT.
- **NO TAG ISSUED.** Per project convention, only CONFIRMATION-MERGE iterations get `v0.v3-NNN` tags. iter-v3/050 = CONFIRMATION-NO-MERGE → no tag.
- **`adx_threshold_per_symbol` field PRESERVED in `RiskV2Config` schema** (paralleling `regime_gate_symbols`, `block_long_for`, `block_short_for`); only the wired value `{"TRXUSDT": 21.0}` was DROPPED at iter-v3/049 closeout.
- **Primitive 10 (block_long_for=("BCHUSDT",)) PRESERVED** as code infrastructure — the mechanism + 7 adversarial tests + GateStats counter REMAIN. Multi-seed evidence at iter-v3/050 does not falsify the mechanism; primitive 10 contributed to seed 42's strong OOS but not to seed 123's. The CANDIDATE bundle ingredient is now in the same epistemic state as ALGO+LDO per-symbol ATR: IS-validated at single-seed, OOS-suspect at multi-seed.
- **regime_momentum_signed_5d (V3_FEATURE_COLUMNS_TOP_N 14th feature) PRESERVED** in BASELINE_V3.md baseline state. Despite ranking 14/14 at portfolio level in iter-v3/050, the feature is the iter-v3/028-validated edge ingredient and was NOT the axis under test.
- **Per-symbol architecture (V3_FEATURES_PER_SYMBOL + V3_ATR_MULTIPLIERS_PER_SYMBOL) PRESERVED as code infrastructure.** Validated at multi-seed; no architectural defects. Future cycles may use the infrastructure with IS-axis discipline.

## Cycle 3 Retrospective — 10 EXPLORATIONs + 1 CONFIRMATION (COMPLETE)

| # | Iteration | Date | Axis | Verdict | OOS Δ vs anchor | PROMISING ingredient? | Status post-/050 |
|---|---|---|---|---|---:|---|---|
| 1 | iter-v3/040 | 2026-05-09 | REVERT per-symbol customizations; cycle 3 anchor restore | EXPLORATION-PROMISING-MECHANICAL | bit-identical to /029 +1.7653 | Anchor (NOT compoundable; baseline restoration) | Closed (mechanical) |
| 2 | iter-v3/041 | 2026-05-09 | Universal feature pruning (drop bottom-3: regime_momentum + sym_vs_btc + ret_skew_50; 14→11) | EXPLORATION-NEGATIVE | -0.76 (BCH -26 swing) | NO — regime_momentum was load-bearing for BCH despite rank 14 | CLOSED |
| 3 | iter-v3/042 | 2026-05-09 | Universal DEFAULT_ATR_MULTIPLIERS (2.0, 1.0) → (1.5, 0.75) | EXPLORATION-NEGATIVE | +0.31 (IS aggregate -1.39) | NO — universal labeling change has divergent per-symbol effects | CLOSED |
| 4 | iter-v3/043 | 2026-05-09 | revert ATR + Kaufman efficiency_ratio_50 (universal engineered feature) | EXPLORATION-NEGATIVE (worst in cycle 3) | -2.66 (ALGO -61 swing catastrophic) | NO — Kaufman ER broke all 4 symbols | CLOSED |
| 5 | iter-v3/044 | 2026-05-09 | Per-symbol ATR for ALGO (2.0, 1.5) — QR data-driven | EXPLORATION-PROMISING (clean — STRONG) | +0.77 (ALGO +49 swing 20.87→70.17 at 63.6% WR; OOS MaxDD 14.23% best in v3) | YES — bundle ingredient #2 | CLOSED at /050 (multi-seed compression) |
| 6 | iter-v3/045 | 2026-05-09 | Per-symbol ATR for LDO (2.0, 1.5) — QR mirror-mechanism extension | EXPLORATION-PROMISING (clean — STRONGEST in v3) | +0.99 — HIGHEST OOS in v3 catalog; LDO +13 swing | YES — bundle ingredient #3 | CLOSED at /050 (multi-seed compression; LDO structural drag) |
| 7 | iter-v3/046 | 2026-05-09 | Per-symbol ATR for BCH (2.0, 1.5) — QR mirror-mechanism extension | EXPLORATION-NEGATIVE | -1.05 (BCH -45 swing; mirror mechanism doesn't transfer) | NO — mirror doesn't apply to symbols with stable SL:TP | CLOSED |
| 8 | iter-v3/047 | 2026-05-09 | Primitive 10 (direction-asymmetric kill switch) + BCH LONG block | EXPLORATION-NEGATIVE-clean (re-classified at /048 closeout) | -2.36 (single-seed Optuna lottery on non-target symbols; primitive 10 IS-validated) | CANDIDATE — primitive 10 IS-only validated | CLOSED at /050 (multi-seed compression) |
| 9 | iter-v3/048 | 2026-05-10 | NEW universal engineered feature `vol_normalized_ret_5d` (15th feature) | EXPLORATION-NEGATIVE-clean | -3.15 (rank 13-15/15 all 4 syms; INERT-OVERFIT) | NO — feature redundant with regime_momentum (|IC|=0.892) | CLOSED |
| 10 | iter-v3/049 | 2026-05-10 | NEW per-symbol ADX threshold (TRX 21) + vol_normalized_ret_5d REVERT | EXPLORATION-NEGATIVE-clean | -2.50 (TRX 6-trade Optuna lottery roster swap) | NO — per-symbol ADX dispatch axis CLOSED | CLOSED (ADX axis CLOSED in BOTH global AND per-symbol forms) |
| **CONF** | **iter-v3/050** | **2026-05-10** | **SECOND v3 CONFIRMATION on cycle 3 best PROMISING bundle (regime_momentum + ALGO/LDO ATR + primitive 10)** | **CONFIRMATION-NO-MERGE-revert** | **+0.235 vs /028 BUT IS Δ -0.19 fails BOTH-must-improve** | **NO — bundle assembly REJECTED at multi-seed** | **CLOSED (per-symbol customization stacking AT CONFIRMATION CONFIRMED ANTI-PATTERN)** |

### Cycle 3 EXPLORATION outcomes summary

- 1 PROMISING-MECHANICAL (anchor): /040
- 2 PROMISING-clean (single-seed compoundable bundle ingredients): /044 (ALGO ATR), /045 (LDO ATR)
- 1 IS-only-validated CANDIDATE (no clean OOS evidence at single-seed; primitive 10): /047
- 6 NEGATIVE-clean: /041, /042, /043, /046, /048, /049
- Strongest OOS in cycle 3 (single-seed): iter-v3/045 (+3.5259 — RETIRED as lottery winner at /050 multi-seed)
- Strongest negative OOS Δ in cycle 3: iter-v3/043 (-2.66; Kaufman ER catastrophic on ALGO)
- **CONFIRMATION outcome: NO MERGE (cycle 3 PROMISING bundle compressed -57.3% IS / -79.0% OOS at multi-seed)**

### What was LEARNED in cycle 3

1. **Per-symbol customization stacking at CONFIRMATION FAILS the BOTH-must-improve rule** — confirmed across 2 independent cycles. The per-symbol customizations introduce single-seed-specific Optuna trajectories that compress severely at multi-seed (Δ-57 to -79% from single-seed peak to multi-seed mean).
2. **Single-seed +3.53 OOS at iter-v3/045 was a lottery winner** — multi-seed compression at /050 to +0.74 falsifies the headline.
3. **LDO is a structural drag at multi-seed despite IS-positive per-symbol ATR customization at single-seed.** Frozen-baseline pattern at OOS-row level confirmed across 3 consecutive iterations (/047, /049, /050).
4. **Universal feature additions (vol_normalized_ret_5d at /048) FAIL when redundant with existing features** — |IC|=0.892 with regime_momentum_signed_5d killed the addition.
5. **Knob axes (ADX, ATR multipliers, z-score) saturated** — universal-knob retunes deliver flat-to-negative deltas; ADX axis CLOSED in BOTH global AND per-symbol forms.
6. **Mirror-mechanism extension fails for stable-SL:TP symbols** — per-symbol ATR mechanism worked for ALGO/LDO (PROMISING at single-seed) but broke BCH (NEGATIVE at /046).
7. **EDA-driven axis selection methodology HOLDS** even with NEGATIVE outcomes — QR EDA at /049 correctly screened 5 candidates and identified the right axis; the failure was Optuna re-tune cost path that single-seed EDA cannot model.

### What is CLOSED for cycle 4

- per-symbol ADX threshold (iter-v3/049; ADX axis CLOSED in BOTH global AND per-symbol forms per `feedback_adx_axis_asymmetric_v3.md`)
- vol_normalized_ret_5d (iter-v3/048; INERT-OVERFIT; redundant with regime_momentum)
- per-symbol ATR for BCH (iter-v3/046; mirror mechanism doesn't transfer)
- Universal feature pruning to <14 features (iter-v3/041; regime_momentum load-bearing despite rank 14)
- Universal DEFAULT_ATR_MULTIPLIERS retune (iter-v3/042; divergent per-symbol effects)
- Kaufman efficiency_ratio_50 (iter-v3/043; broke all 4 symbols)
- **Per-symbol customization stacking AT CONFIRMATION** (now confirmed across 2 cycles; structural anti-pattern per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`)

## Cycle 4 Priorities (per Critic FINAL `b6339c5` recommendations)

Per `feedback_v3_strict_10_to_1_cadence.md`: cycle 4 begins at iter-v3/051 = #1 of 10 EXPLORATIONs; iter-v3/061 = cycle 4 CONFIRMATION (SEPARATE single-seed iter-v3/060 first, then multi-seed iter-v3/061 — do NOT collapse).

### HIGH-priority axes (cycle 4)

1. **NEW universal engineered features** (composed Category 2; per `feedback_v3_engineered_features_proven.md`):
   - `fracdiff_d05_close` for ALL 4 symbols (universal scope; iter-v3/035 used BCH-only — universal scope unstested at multi-seed)
   - `hurst_drift_50_200` (composed: hurst_100 minus hurst_200, signal-strength delta)
   - `regime_momentum_signed_3d` retest at universal scope (3d horizon vs 5d; orthogonal time-scale variant of the proven /028 ingredient)

2. **3-symbol universe restoration WITHOUT ALGO** (test if regime_momentum_signed_5d recovers):
   - Hypothesis: regime_momentum's rank 14/14 at portfolio level in /050 may be due to ALGO universe inclusion diluting the signal
   - Test: V3_MODELS = (BCH, LDO, TRX) — restore iter-v3/028 universe; check whether regime_momentum's per-symbol importance recovers
   - Note: LDO removal is a competing axis per recommendation #2 below; the QR must rank these against each other in iter-v3/051 EDA

3. **DSR gate reformulation** (deferred from /028 + /039 + /050):
   - DSR=0.0 has been structural for 3 consecutive CONFIRMATIONs; required SR ≈ 3.5 at n_trials=1400 vs observed annualized ≈ 1.5-2.0
   - Either reformulate to `DSR > 0` (positive deflation only) or cap n_trials at the level where the gate becomes feasible
   - Brief should propose specific reformulation with mathematical justification

### MEDIUM-priority axes (cycle 4)

4. **regime_momentum_signed_5d feature importance investigation** (rank-14/14 portfolio):
   - Why is the iter-v3/028 edge ingredient now bottom-rank? Is it the 4-symbol universe expansion (ALGO addition) or the per-symbol customizations crowding it out?
   - This investigation overlaps with axis #2 above (3-symbol restoration tests the universe-expansion hypothesis directly)

5. **NEW model architecture retest** (per iter-v3/016 NOT-CLOSED-for-all-configs caveat):
   - CatBoost head-to-head (deferred at iter-v3/049 due to 2h cap)
   - XGBoost variant with Sharpe-objective Optuna, drawdown-penalized loss, lossguide growth (configurations NOT tested at iter-v3/016)

### LOW-priority axes (CLOSED — do NOT re-test)

6. **CLOSED axes inherited from cycle 3 + earlier**:
   - per-symbol ADX threshold (CLOSED in BOTH global AND per-symbol forms — `feedback_adx_axis_asymmetric_v3.md`)
   - vol_normalized_ret_5d (INERT-OVERFIT)
   - BCH per-symbol ATR (mirror mechanism doesn't transfer)
   - Universal labeling-multiplier knobs (saturated)
   - Universe expansion (HBAR+AVAX CLOSED at iter-v3/021)
   - **Per-symbol customization stacking AT CONFIRMATION** (now confirmed across 2 cycles; structural anti-pattern)
   - Per-symbol PnL share caps (CLOSED at iter-v3/020 — concentration is signal not risk)
   - Funding rate family (PERMANENTLY CLOSED across 3 EXPLORATION data points: /019, /023, /024)
   - Engineered feature stacking at single-seed (CLOSED at /026/027 — DON'T STACK linearly at single-seed)

## iter-v3/051 EDA Priorities (per Critic FINAL `b6339c5` recommendations #2 + #3)

iter-v3/051 must investigate THREE EDA-driven axes BEFORE selecting the cycle 4 starting hypothesis. Per `feedback_v3_axis_selection_quant_discipline.md`, the QR must produce numerical tables in `analysis/iteration_v3-051/*.py` with EDA-derived numerical evidence BEFORE locking the brief Section 3.

### EDA Axis A — LDO Removal Investigation

Hypothesis: LDO has produced negative OOS in EVERY single-seed=42 iteration since iter-v3/047 (-19.13 frozen baseline). LDO's IS-positive ATR customization (2.0, 1.5) is the iter-v3/045 PROMISING ingredient that does NOT survive multi-seed validation at OOS. Removing LDO from V3_MODELS may produce a stronger CONFIRMATION at iter-v3/061.

EDA must produce:
- IS-only baseline comparison: 3-symbol BCH+TRX+ALGO vs 4-symbol BCH+LDO+TRX+ALGO
- LDO trade-roster IS distribution analysis (IS WR, IS PnL, IS Sharpe contribution)
- LDO importance rank in 3-sym restored regime_momentum context
- Predicted multi-seed-mean OOS Sharpe lift if LDO removed (counterfactual)

### EDA Axis B — Per-symbol Customization REVERT

Hypothesis: Per Critic FINAL `bdd6fc2` (iter-v3/039 review.md) recommendation #1: "REVERT per-symbol customizations" should be the cycle 4 starting hypothesis. SAME recommendation re-issued by Critic FINAL `b6339c5` (iter-v3/050) recommendation #3.

EDA must produce 4-axis ranking against the iter-v3/050 multi-seed mean baseline:
- (a) LDO removal alone (V3_MODELS → 3 symbols, KEEP per-symbol ATR for ALGO + primitive 10)
- (b) per-symbol ATR ALGO+LDO REVERT alone (V3_ATR_MULTIPLIERS_PER_SYMBOL → empty, KEEP V3_MODELS, KEEP primitive 10)
- (c) primitive 10 BCH LONG block REVERT alone (block_long_for → empty, KEEP V3_MODELS, KEEP per-symbol ATR for ALGO+LDO)
- (d) full per-symbol REVERT (V3_ATR_MULTIPLIERS_PER_SYMBOL → empty, block_long_for → empty, KEEP V3_MODELS = 4 symbols → return to iter-v3/028 architecture exactly)

Each axis must include:
- Counterfactual IS Sharpe estimate (using IS-only data, not multi-seed)
- Counterfactual OOS Sharpe range (from iter-v3/028/049 IS data)
- Predicted Optuna-retune cost path (`feedback_v3_per_symbol_lifts_oos_breaks_is.md` mechanism)
- Behavioral-effect predictor: estimated trade-count change

### EDA Axis C — NEW Universal Engineered Feature Candidate Selection

Hypothesis: Cycle 3 closed several universal feature additions (vol_normalized_ret_5d at /048; Kaufman ER at /043). NEW candidates for cycle 4 must avoid the |IC| > 0.5 redundancy pitfall.

EDA must screen 3-5 candidates (e.g., `fracdiff_d05_close` universal, `hurst_drift_50_200`, `regime_momentum_signed_3d`, `vwap_deviation_zscore_30`, `sym_vs_btc_corr_30d`) with:
- |IC| matrix vs existing 14 features (carve-out for Category 2 composed per `feedback_v3_engineered_feature_pivot.md`)
- Importance prediction (where would the candidate rank? must clear ≥30 importance threshold)
- Per-symbol IC heterogeneity (does the feature correlate across all 4 symbols?)
- ADF stationarity check (rolling monthly p<0.05)

The QR must rank EDA Axes A/B/C against each other and select the strongest single axis for iter-v3/051. The selected axis becomes the iter-v3/051 hypothesis; the other 2 axes are queued for iter-v3/052+ EXPLORATIONs.

## Memory Rule Updates

- **`feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10** by orchestrator (post-Critic FINAL `b6339c5`). Original rule at iter-v3/039 closeout cited single-cycle multi-seed observation; updated rule cites TWO INDEPENDENT CYCLES (iter-v3/039 cycle 2 + iter-v3/050 cycle 3) with consistent asymmetric IS-regression-OOS-improvement pattern. The rule is no longer a hypothesis; it is a SYSTEM-LEVEL CONSTRAINT. Future per-symbol customization additions MUST clear IS-axis pre-validation BEFORE inclusion in any CONFIRMATION bundle.

- **`feedback_v3_single_seed_frozen_baseline.md` REINFORCED at iter-v3/050** (no edit needed — rule already correctly calibrated). LDO OOS = -19.13 weighted_pnl bit-identical for the THIRD consecutive iteration at single-seed=42 (across iter-v3/047, /049, /050). The frozen-baseline pattern is now empirically confirmed at OOS-row level across 3 consecutive non-identical iterations on disjoint axes.

- **NO new memory rule introduced.** The strict 10:1 cadence rule (`feedback_v3_strict_10_to_1_cadence.md`) was already in place; cycle 3 satisfaction (10 EXPLORATIONs + 1 CONFIRMATION) closes cleanly. The strict BOTH-must-improve baseline rule (`feedback_v3_strict_both_is_oos_baseline.md`) was already in place and fired correctly. The QR axis selection discipline rule (`feedback_v3_axis_selection_quant_discipline.md`) was already in place and is carried forward to iter-v3/051.

## Architectural Decisions

- **BASELINE_V3.md UNCHANGED at iter-v3/028** (+0.5101 IS / +0.5053 OOS; SHA `b0576df`). Per `feedback_v3_strict_both_is_oos_baseline.md` BOTH-must-improve rule.
- **iter-v3/045 single-seed +3.53 OOS RETIRED as "lottery winner"** — no longer the formal "best EXPLORATION-PROMISING" carry-forward record.
- **Cycle 3 PROMISING bundle (regime_momentum + ALGO+LDO per-symbol ATR + primitive 10) REJECTED** at multi-seed CONFIRMATION. Bundle assembly fails the BOTH-must-improve rule.
- **V3_FEATURE_COLUMNS_TOP_N = 14 PRESERVED** (regime_momentum_signed_5d carry-forward from iter-v3/028 BASELINE).
- **V3_ATR_MULTIPLIERS_PER_SYMBOL + V3_FEATURES_PER_SYMBOL infrastructure PRESERVED** as code (validated at multi-seed; no architectural defects). Future cycles may use the infrastructure with IS-axis discipline.
- **`adx_threshold_per_symbol` field PRESERVED in `RiskV2Config` schema** (paralleling `regime_gate_symbols`, `block_long_for`, `block_short_for`); only the wired value (DROPPED at iter-v3/049 closeout) remains empty.
- **Primitive 10 (block_long_for=("BCHUSDT",)) PRESERVED as code infrastructure** — mechanism + 7 adversarial tests + GateStats counter REMAIN. Multi-seed evidence at /050 does not falsify the primitive's existence; it only fails to validate the bundle assembly.
- **`--clean-oof` guardrail RETAINED** (SHA `6a216b5`). The guardrail's behavior is correct; STRUCTURAL n_trials=1400 at multi-seed CONFIRMATION is benign per the iter-v3/048 forensic resolution.
- **NO TAG ISSUED.** Per project convention, only CONFIRMATION-MERGE iterations get `v0.v3-NNN` tags.

## Cadence: Cycle 3 COMPLETE 11/11 (10 EXPLORATIONs + 1 CONFIRMATION); Cycle 4 begins iter-v3/051

Per `feedback_v3_strict_10_to_1_cadence.md`:

- **Cycle 3 of 10 EXPLORATIONs is COMPLETE** (iter-v3/040 through /049)
- **Cycle 3 CONFIRMATION COMPLETE** at iter-v3/050 (NO MERGE; BASELINE_V3.md UNCHANGED at iter-v3/028)
- **Cycle 4 begins at iter-v3/051 = #1 of 10 EXPLORATIONs**
- **Cycle 4 CONFIRMATION at iter-v3/061** (SEPARATE single-seed iter-v3/060 first, then multi-seed iter-v3/061; do NOT collapse)
- **Cadence wall-clock caps**: EXPLORATION 2h, CONFIRMATION 6h (iter-v3/050 actual: 5.05h, within cap)
- **Cycle 4 CONFIRMATION axes**: TBD pending cycle 4 EXPLORATION outcomes; cycle 4 hypothesis is "lift IS Sharpe to ≥ +0.5101 (BASELINE_V3.md update gate floor) while preserving OOS Sharpe ≥ +0.5053" via UNIVERSAL axes (per-symbol customizations rejected at bundle level)

## See Also

- `briefs-v3/iteration_v3-050/research_brief.md` — Phase 5 brief (SHA `acc6baf`; 787 lines)
- `briefs-v3/iteration_v3-050/phase5p5_gate.md` — Phase 5.5 gate PASS (SHA `45ddb0f`)
- `briefs-v3/iteration_v3-050/engineering_report.md` — Phase 6/7 engineering report (SHA `56c671b`; CONFIRMATION-NO-MERGE classification)
- `briefs-v3/iteration_v3-050/review.md` — Phase 7.5 Critic FINAL (SHA `b6339c5`; CONFIRMATION-NO-MERGE-revert)
- `reports-v3/iteration_v3-050/comparison.csv` — full numerical results (seed 42 primary projection)
- `reports-v3/iteration_v3-050/seed_summary.json` — per-seed Pareto data (both seeds)
- `reports-v3/iteration_v3-050/dsr.json` — DSR/PBO/PSR/n_eff (n_trials=1400 multi-seed CONFIRMATION-spec)
- `reports-v3/iteration_v3-050/pareto_front.csv` — multi-seed Pareto dump
- `reports-v3/iteration_v3-050/per_cell_pbo.csv` — per-cell PBO (174 cells)
- `reports-v3/iteration_v3-050/cpcv_paths.csv` — CPCV path data (45 paths)
- `reports-v3/iteration_v3-050/in_sample/per_symbol.csv` — per-symbol IS PnL attribution
- `reports-v3/iteration_v3-050/out_of_sample/per_symbol.csv` — per-symbol OOS PnL attribution
- `reports-v3/iteration_v3-050/in_sample/trades.csv` + `out_of_sample/trades.csv` — trade rosters (rows spot-checked)
- `reports-v3/iteration_v3-050/in_sample/model_importance_last_month_*.csv` — feature importance per symbol
- `BASELINE_V3.md` — UNCHANGED at iter-v3/028 (+0.5101 IS / +0.5053 OOS; SHA `b0576df`)
- Setup commit SHA `45ddb0f` — DROP adx_threshold_per_symbol + ITERATION_LABEL=v3-050
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_per_symbol_lifts_oos_breaks_is.md` — UPDATED 2026-05-10 with second-cycle confirmation (system-level constraint)
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_single_seed_frozen_baseline.md` — REINFORCED at iter-v3/050 (3rd consecutive LDO OOS bit-identity)
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_strict_both_is_oos_baseline.md` — fired correctly at iter-v3/050 (NO MERGE per BOTH-must-improve)
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_strict_10_to_1_cadence.md` — cycle 3 closed cleanly (10 EXPLORATIONs + 1 CONFIRMATION)
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_axis_selection_quant_discipline.md` — carry-forward to iter-v3/051 EDA
- `diary-v3/iteration_v3-028.md` — first CONFIRMATION-MERGE (BOOTSTRAP precedent; established BASELINE_V3.md anchor)
- `diary-v3/iteration_v3-039.md` — first CONFIRMATION-NO-MERGE (cycle 2; established `feedback_v3_strict_both_is_oos_baseline.md` rule)
- `diary-v3/iteration_v3-049.md` — cycle 3 #10 of 10 closeout; per-symbol ADX axis CLOSED
- `diary-v3/iteration_v3-047.md` — primitive 10 introduction; carried forward to iter-v3/050 as IS-only validated CANDIDATE
- `briefs-v3/cycle3_plan.md` — cycle 3 strategy (iter-v3/040-050)
- `briefs-v3/exploration_catalog.md` — iter-v3/050 catalog row at diary closure (CONFIRMATION-NO-MERGE-revert verdict; cycle 4 priorities established)
