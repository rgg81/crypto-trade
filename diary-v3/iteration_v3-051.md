# Iteration iter-v3/051 — Diary

## Decision: EXPLORATION-NULL-RESULT — fracdiff_d05_close UNIVERSAL learned (ranks 11-12/15) but NO IS lift; cycle 4 #1 of 10; LDO structural drag CONFIRMED at FULL REVERT

iter-v3/051 = **FIRST EXPLORATION of cycle 4** post-iter-v3/050 CONFIRMATION-NO-MERGE-revert. Cycle 4 #1 of 10. Single new axis under test: ADD `fracdiff_d05_close` to `V3_FEATURE_COLUMNS_TOP_N` (14 → 15) at universal scope — broadcast to all 3 symbols (BCH, LDO, TRX) — alongside SYSTEM-LEVEL REVERT to iter-v3/028 architecture (V3_MODELS = 3-sym; V3_ATR_MULTIPLIERS_PER_SYMBOL = {}; block_long_for = (); REQUIRED_GAP = 66 = (21+1)×3) mandated by `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10 with second-cycle confirmation. Run spec: `--seeds 1 --n-trials 35 --clean-oof` (EXPLORATION-spec; 525 total Optuna trials = 3 syms × 5 inner × 35).

Result: **IS single-seed Sharpe +0.4506 / OOS single-seed Sharpe +0.5891 (seed 42).** Per the brief Section 8 pre-registered 4-path criteria, NONE of the 4 LOCKED paths cleanly fires:
- PATH A (PROMISING-clean): requires IS Δ ≥ +0.05 AND OOS Δ ≥ -0.20; observed IS Δ = -0.0595 — **FAIL on IS axis**.
- PATH B (PROMISING-INERT): requires rank > 13/15 in ALL 3 syms; observed BCH=12, LDO=11, TRX=11 — **FAIL (feature LEARNED)**.
- PATH C-clean (NEGATIVE-clean): requires IS Δ < -0.10 OR OOS Δ < -0.30; observed IS Δ = -0.0595 (> -0.10), OOS Δ = +0.0838 (> -0.30) — **FAIL on both**.
- PATH C-suspicious (NEGATIVE-SUSPICIOUS-OOS): requires IS-OOS daily ratio outside [0.5, 2.0]; observed 1.148 — **FAIL (in band)**.

Per Critic FINAL `32cc46f`, the observed IS Δ = -0.0595 sits in the **no-man's-land between PATH A's +0.05 ceiling and PATH C-clean's -0.10 floor** — a methodological defect in the brief's pre-registration. Critic adjudication: **EXPLORATION-NULL-RESULT** — fracdiff was learned (ranks 11-12 across 3 symbols), but produced no IS lift; OOS lift +0.08 is within single-seed=42 lottery noise (frozen-baseline caveat per `feedback_v3_single_seed_frozen_baseline.md`); neither mapping to PROMISING-MARGINAL (would inflate cycle 4 PROMISING count spuriously) nor to NEGATIVE-MARGINAL (would close fracdiff axis prematurely) is honest. EXPLORATION-NULL-RESULT is the most accurate classification.

**CRITICAL FINDING (independent of fracdiff axis):** LDO OOS weighted_pnl = **-17.44** at FULL REVERT to iter-v3/028 architecture (default ATR (2.0, 1.0); no primitive 10; no per-symbol customization). LDO IS PnL share = **-14.96%** of total IS PnL (11 trades, 27.3% WR, -5.99% net_pnl_pct). LDO OOS WR = **23.1%** (3 wins / 13 trades over ~14 months). **This is the 3-symbol /028-architecture result with NO per-symbol customizations applied** — LDO is producing persistently negative OOS independent of any customization layer. The prior /050 EDA Axis A rejection of LDO removal (IS Δ -0.015 at /050 config) is now SUPERSEDED: at /051 /028-reverted config, LDO IS is also negative. **iter-v3/052 axis = LDO removal investigation** (HIGH-priority cycle 4 #2 per Critic FINAL `32cc46f` rec #1).

Wall-clock: 1.28h (well within 2h EXPLORATION cap). 12/12 standard methodology checks PASS (look-ahead, embargo, IC, ADF, hypothesis-implementation alignment, library pinning, etc.) per Critic FINAL `32cc46f`. No tag issued (EXPLORATION).

## What Was Tested

**Hypothesis (locked in brief Section 1):** "Adding `fracdiff_d05_close` to `V3_FEATURE_COLUMNS_TOP_N` at universal scope (14 → 15) — alongside system-level REVERT of per-symbol customizations to iter-v3/028 architecture — provides a NEW universal stationary engineered feature with mean-reversion signal (univariate Spearman ρ ∈ [-0.068, -0.038] significant at p<0.05 across all 4 symbols). Expected bundle IS Sharpe lift +0.05 to +0.30 vs iter-v3/028 baseline reference +0.5101; bundle OOS Sharpe Δ within [-0.20, +0.30] vs /028 anchor +0.5053."

**Predicted bands (brief Section 4):**
- IS Sharpe: lift to [+0.46, +0.81] (Δ ∈ [+0.05, +0.30] vs +0.5101 anchor)
- OOS Sharpe: range [+0.30, +0.80] (Δ ∈ [-0.20, +0.30] vs +0.5053 anchor)
- fracdiff importance rank: top-10 to top-12 in 15-feature stack (PATH B INERT threshold > 13/15)
- IS-OOS daily Sharpe ratio: ∈ [0.5, 2.0] (PATH C-suspicious threshold outside band)

**Spec (locked in brief Section 0.5; setup commit SHA `c0ebe21`):**
- ITERATION_LABEL = "v3-051"
- V3_FEATURE_COLUMNS_TOP_N = 15 features (ADD fracdiff_d05_close as 15th)
- V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols (DROP ALGO per /050 cycle 3 REVERT)
- V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (CLEAR ALGO 2.0/1.5 + LDO 2.0/1.5)
- block_long_for = () (CLEAR BCH LONG block from /047 primitive 10)
- REQUIRED_GAP = 66 = (21+1)×3 (RECOMPUTE from 88 = (21+1)×4 for 3-sym universe)
- regime_momentum_signed_5d PRESERVED (iter-v3/028 edge ingredient)
- adx_threshold_per_symbol = {} (UNCHANGED)
- 5 adversarial tests in `tests/features_v3/test_fracdiff_d05_universal.py` PASS
- Runner: `uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof`
- ENSEMBLE_SIZE = 5 (auto inner ensemble); outer_seeds = 1 (EXPLORATION-spec)
- Wall-clock: 1.28h (within 2h cap)
- Total Optuna trials: 525 = 3 syms × 5 inner × 35

## Headline Numbers

### Single-seed primary (comparison.csv + seed_summary.json; seed 42 only)

| Metric | iter-v3/028 BASELINE (multi-seed mean) | iter-v3/050 multi-seed mean (CONFIRMATION-NO-MERGE) | **iter-v3/051 (1-seed)** | Δ vs iter-v3/028 | Δ vs iter-v3/050 multi-seed (caveat: 1-seed vs 2-seed) |
|---|---:|---:|---:|---:|---:|
| **IS monthly Sharpe** | +0.5101 | +0.3189 | **+0.4506** | **-0.0595** | **+0.1317** |
| **OOS monthly Sharpe** | +0.5053 | +0.7404 | **+0.5891** | **+0.0838** | **-0.1513** |
| IS-OOS daily Sharpe ratio | 0.99 | 2.32 | **1.148** | within band [0.5, 2.0] | -1.17 |
| IS Trades | 156 (mean) | 282.5 (mean) | 178 | +22 (+14.1%) | -104.5 |
| OOS Trades | 95 (mean) | 93.5 (mean) | 96 | +1 | +2.5 |
| IS MaxDD | 41.43% | 60.97% | 37.37% | -4.1pp better | -23.6pp better |
| OOS MaxDD | 23.53% | 27.83% | 32.75% | +9.2pp worse | +4.9pp worse |
| OOS Calmar | 0.92 | 1.29 | 0.53 | -0.39 | -0.76 |
| OOS Top concentration | 76.47% (TRX) | 43.64% (mean) | 67.65% (BCH) | -8.8pp better | +24.0pp worse |
| DSR | 0.0 (structural at /028 multi-seed) | 0.0 (structural) | 0.0 (structural at n_trials=525) | structural artifact | structural |
| PBO | 0.1243 | 0.0939 | **0.1168** | +0.04 | +0.02 |
| PSR | 1.0 | 1.0 | **1.0** | saturation | saturation |
| n_trials | 1050 | 1400 | 525 | EXPLORATION spec | EXPLORATION spec |
| n_eff | 19 | 18 | 19 | within range | within range |

**Single-seed vs multi-seed comparison caveat**: iter-v3/051 is single-seed=42 EXPLORATION-spec; iter-v3/050 was 2-seed CONFIRMATION-spec; iter-v3/028 was 2-seed CONFIRMATION-spec. The IS Δ +0.13 vs /050 multi-seed mean is largely the seed-42 lottery (iter-v3/050 seed 42 IS = +0.4872 vs seed 123 IS = +0.1506; mean +0.3189). The OOS Δ -0.15 vs /050 multi-seed mean is also seed-42 specific (iter-v3/050 seed 42 OOS = +1.1659 was the lottery winner). The cleaner comparison is iter-v3/051 vs the /028 multi-seed anchor (Δ -0.06 IS / +0.08 OOS), since that's the proper REVERT baseline.

### Per-symbol decomposition (seed 42)

**IS per-symbol:**

| Symbol | trades | win_rate | net_pnl_pct | avg_pnl_pct | pct_of_total_IS_pnl |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 90 | 43.3% | +41.70% | +0.463% | **+104.05%** |
| TRXUSDT | 77 | 35.1% | +4.37% | +0.057% | +10.91% |
| LDOUSDT | 11 | 27.3% | -5.99% | -0.545% | **-14.96%** |

BCH carries 104% of IS PnL; TRX marginally positive (+11%); **LDO is IS-negative at -14.96%** (11 IS trades, 27.3% WR). The 3-symbol IS Sharpe of +0.4506 is almost entirely BCH-driven.

**OOS per-symbol:**

| Symbol | trades | win_rate | weighted_pnl | net_pnl_pct | pct_of_total_OOS_pnl | concentration_pct |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 37 | 43.2% | +23.59 | +31.14% | **+160.32%** | +135.36% |
| TRXUSDT | 46 | 41.3% | +11.28 | +10.85% | +55.85% | +64.71% |
| LDOUSDT | 13 | 23.1% | **-17.44** | -22.57% | **-116.17%** | **-100.07%** |

BCH drives 160% of OOS PnL (+23.59 wpnl). TRX positive (+11.28 wpnl). **LDO cancels -116% of OOS PnL at -17.44 weighted_pnl** (13 trades, 23.1% WR — far below random walk 50%). The +0.5891 OOS Sharpe is the residual after LDO's drag on BCH+TRX combined performance.

### §8 Pre-registered Path Verdict (mechanical, non-renegotiable)

| Path | Trigger | Observed | Fired? |
|---|---|---|---|
| PATH A (PROMISING-clean) | IS Δ ≥ +0.05 AND OOS Δ ≥ -0.20 AND rank ≤ 12 in ≥1 sym | IS Δ = -0.0595 < +0.05 → IS axis FAIL | NO |
| PATH B (PROMISING-INERT) | rank > 13/15 in ALL 3 syms AND IS Δ ∈ [-0.10, +0.05] | BCH=12, LDO=11, TRX=11 (LEARNED) | NO |
| PATH C-clean (NEGATIVE-clean) | IS Δ < -0.10 OR OOS Δ < -0.30 | IS Δ = -0.0595 (> -0.10); OOS Δ = +0.0838 (> -0.30) | NO |
| PATH C-suspicious (NEGATIVE-SUSPICIOUS-OOS) | IS-OOS daily ratio outside [0.5, 2.0] | 1.148 (in band) | NO |
| **(Critic adjudication)** | **No pre-registered path fires; brief defect** | **fracdiff LEARNED but no IS lift** | **EXPLORATION-NULL-RESULT** |

## Why NULL-RESULT (Critic adjudication, FINAL SHA `32cc46f`)

The four LOCKED pre-registration paths leave a no-man's-land for IS Δ ∈ (-0.10, +0.05) with feature LEARNED — the exact region the iter-v3/051 result landed. The Critic's adjudication rationale:

1. **OOS Δ +0.08 is within single-seed=42 lottery noise.** BCH OOS +23.59 and LDO OOS -17.44 may be deterministic at seed 42 regardless of axis change (per `feedback_v3_single_seed_frozen_baseline.md`). The OOS lift cannot be cleanly attributed to fracdiff.
2. **IS Δ -0.06 indicates fracdiff did NOT lift IS Sharpe** — the central prediction of the brief's hypothesis (predicted lift +0.05 to +0.30). The hypothesis is falsified on IS axis.
3. **fracdiff was LEARNED** (ranks 11-12/15 across 3 per-symbol models; portfolio rank 13/15). Not INERT in the PATH B sense.
4. **Classification options considered:**
   - PROMISING-MARGINAL would inflate the cycle 4 PROMISING ingredients count spuriously (PATH A clearly failed).
   - NEGATIVE-MARGINAL would close the fracdiff axis prematurely (PATH C-clean clearly failed).
   - EXPLORATION-NULL-RESULT is the most honest: feature learned, no IS lift, OOS lift within lottery noise.

**Mechanism (Critic Adversarial Finding #3):** fracdiff_d05_close marginally outranks regime_momentum_signed_5d at ALL 3 symbols and portfolio (BCH: 54.0 vs 47.6; LDO: 109.4 vs 101.0; TRX: 91.0 vs 89.0; portfolio: 254.4 vs 237.6). Both features rank in bottom tier. Pairwise IC = 0.148 (very low). The model gave both features roughly equal low split-budget priority. fracdiff did not displace existing features (low IC) but did consume scarce split budget without contributing independent edge — a "moderate signal strength, redundant" pattern consistent with no IS lift.

## Brief Pre-Registration Defect (Recommendation: Add PATH D NULL-RESULT to future briefs)

The brief's pre-registered Section 8 contains a methodological defect that should be corrected for cycle 4 #2 onward. The 4 LOCKED paths leave a no-man's-land that exactly accommodates the iter-v3/051 outcome:

| Path | IS Δ requirement | OOS Δ requirement | Feature learned? | Coverage |
|---|---|---|---|---|
| PATH A (PROMISING-clean) | ≥ +0.05 | ≥ -0.20 | implicit YES (rank ≤ 12 in ≥1 sym) | Strict lift |
| PATH B (PROMISING-INERT) | ∈ [-0.10, +0.05] | — | NO (rank > 13 all syms) | INERT |
| PATH C-clean (NEGATIVE) | < -0.10 OR | OR OOS Δ < -0.30 | implicit YES | Hard regression |
| PATH C-suspicious | any | any | — | Out-of-band ratio |

The gap: **IS Δ ∈ (-0.10, +0.05) AND OOS Δ ∈ (-0.30, +0.20) AND feature LEARNED** has no pre-registered path. The iter-v3/051 result (IS Δ = -0.0595; OOS Δ = +0.0838; ranks 11-12) lands exactly in this gap.

**Critic FINAL `32cc46f` Recommendation #3**: Future EXPLORATION brief Section 8 must include 5th explicit BORDERLINE/NULL-RESULT path. Suggested formulation:

```
PATH D (EXPLORATION-NULL-RESULT):
  IS Δ ∈ (-0.10, +0.05)
  AND OOS Δ ∈ (-0.20, +0.20)
  AND feature LEARNED (rank ≤ 12 in ≥1 sym)
  → classify as null result; drop axis from V3_FEATURE_COLUMNS_TOP_N at NEXT setup;
    PARK feature (do NOT mark CLOSED); retain compute function as dead code at zero
    revert cost; may be retested under different conditions (per-symbol scoping,
    n_trials=50+, multi-seed) if cycle PROMISING ingredients accumulate.
```

This path covers the conservative-noise case where the feature signal is real (univariate ρ significant at p<0.05; ADF stationary; importance LEARNED) but does not produce decisive IS lift at single-seed n_trials=35. The PATH D classification protects against both (a) spurious PROMISING inflation and (b) premature axis closure.

The QR is responsible for adding PATH D pre-registration to the iter-v3/052 brief.

## fracdiff_d05_close Fate: PARKED (not CLOSED)

Per Critic FINAL `32cc46f` Recommendation #2:

**Action at iter-v3/052 setup:**
- DROP `fracdiff_d05_close` from `V3_FEATURE_COLUMNS_TOP_N` (15 → 14).
- RETAIN `compute_fracdiff_d05_close` function (`src/crypto_trade/features_v3/engineered_v3.py:264-327`) as dead code at zero revert cost.
- RETAIN 5 adversarial tests in `tests/features_v3/test_fracdiff_d05_universal.py`.

**Status: PARKED (not CLOSED).** Rationale:
- Feature LEARNED (ranks 11-12 across 3 symbols, portfolio rank 13).
- ADF stationary (p=0.0 for BCH+LDO; p=0.003 for TRX).
- Univariate signal real (|ρ| = 0.038 to 0.051, all p<0.05).
- No IS lift at single-seed n_trials=35 universal scope.
- Future conditions where retest is justified:
  - Per-symbol scoping (e.g., LDO-only or BCH-only fracdiff_d05_close), since per-symbol IC analysis showed strongest correlation at LDO.
  - n_trials=50+ Optuna budget at single-seed (the IS shortfall may reflect search noise rather than absence of signal).
  - Multi-seed CONFIRMATION as a bundle ingredient (if cycle 4 cumulative PROMISING ingredients warrant CONFIRMATION-test inclusion).

Keeping the compute function and tests preserves zero-cost retest capability. The feature's compute path is unconditionally executed at parquet-generation time; only its inclusion in `V3_FEATURE_COLUMNS_TOP_N` is removed.

**Closing the axis prematurely would be wrong**: the feature passed all pre-flight gates (ADF stationarity, univariate Spearman, importance rank LEARNED), and the IS shortfall (-0.06 vs predicted +0.05 to +0.30 lift) is within single-seed n_trials=35 noise. The "moderate signal strength, redundant" pattern (Critic finding #3) suggests the feature competes with rather than complements regime_momentum_signed_5d; a per-symbol scoping might bypass this redundancy.

## iter-v3/035 BCH-only fracdiff precedent FALSIFIED in clean conditions

The brief cited iter-v3/035 BCH-only PROMISING (BCH OOS +37.98 single-seed swing) as basis for the universal-scope retest hypothesis. **This precedent does NOT generalize** — confirmed in Critic FINAL `32cc46f` Adversarial Finding #1:

| Iteration | Scope | IS Sharpe | OOS Sharpe | IS-OOS daily ratio | Classification (post-/050 taxonomy) |
|---|---|---:|---:|---:|---|
| iter-v3/034 | universal-scope (4-sym) | -0.16 | +1.77 | 10.82× | **PATH C-suspicious** (anti-pattern) |
| iter-v3/035 | BCH-only per-symbol | -0.10 | +2.85 | 27.88× | **PATH C-suspicious** (anti-pattern) |
| **iter-v3/051** | **universal-scope (3-sym REVERT)** | **+0.4506** | **+0.5891** | **1.148** | **NULL-RESULT (clean conditions)** |

Both iter-v3/034 and iter-v3/035 produced their headline OOS lifts via the **PATH C-suspicious** asymmetric pattern that `feedback_v3_engineered_features_dont_stack.md` (2026-05-08) and `feedback_v3_per_symbol_lifts_oos_breaks_is.md` (UPDATED 2026-05-10) explicitly identify as Optuna-lottery artifact, NOT signal. The cited "PROMISING precedent" was anchored on stale interpretation under earlier (less rigorous) classification criteria.

iter-v3/051's universal-scope test at /028-reverted architecture (with IS-OOS daily ratio = 1.148 IN BAND) gives the **cleanest fracdiff result in v3 history** — and the answer is: feature LEARNED, no IS lift. The /035 BCH-only +37.98 OOS swing precedent is FALSIFIED in clean conditions. fracdiff_d05_close at universal scope does not lift IS Sharpe above /028 anchor at single-seed n_trials=35.

This is a useful negative result: it cleanly removes a hypothesis from the EXPLORATION queue (universal-scope fracdiff is not a quick win at single-seed) and clarifies the conditions under which the feature might still contribute (per-symbol scoping; multi-seed CONFIRMATION as bundle ingredient).

## LDO Structural Drag CONFIRMED at FULL REVERT — iter-v3/052 axis

This is the **central finding of iter-v3/051 closeout** independent of the fracdiff axis.

### LDO OOS history at seed 42

| Iteration | LDO config | LDO OOS wpnl | LDO OOS trades | LDO OOS WR | Notes |
|---|---|---:|---:|---:|---|
| iter-v3/047 | ATR (2.0, 1.5) + primitive 10 | -17.44 | — | — | Frozen-baseline first observation |
| iter-v3/049 | ATR (2.0, 1.5) + primitive 10 | -17.44 | — | — | Bit-identical to /047 (frozen baseline) |
| iter-v3/050 (seed 42) | ATR (2.0, 1.5) + primitive 10 | -19.13 | 12 | 33.3% | Multi-seed CONFIRMATION; seed 42 row |
| **iter-v3/051** | **DEFAULT ATR (2.0, 1.0) + NO primitive 10** | **-17.44** | **13** | **23.1%** | **FULL REVERT** |

**The /051 result is decisive**: LDO OOS = -17.44 weighted_pnl AFTER FULL REVERT to /028 architecture. All per-symbol customizations (LDO ATR widening 2.0/1.5 from /045; BCH LONG block from /047; ALGO from /033) REMOVED. The default 3-sym /028 configuration STILL produces persistently negative LDO OOS.

### LDO IS at FULL REVERT (NEW EVIDENCE — supersedes /050 EDA Axis A)

The prior /051 EDA Axis A rejected LDO removal on the axis of IS-Δ for the /050 config (axis_a_ldo_attribution.csv showed IS Δ -0.015 from removing LDO at /050; LDO IS contribution near-zero at /050 config). **The /051 result changes the calculus**:

| Window | Symbol | trades | WR | net_pnl_pct | avg_pnl_pct | IS PnL share |
|---|---|---:|---:|---:|---:|---:|
| IS | LDOUSDT | 11 | 27.3% | -5.99% | -0.545% | **-14.96%** |
| OOS | LDOUSDT | 13 | 23.1% | -22.57% | -1.736% | **-116.17%** |

LDO IS is also negative at /028-reverted config (-14.96% IS PnL share). The "IS-positive ATR customization" claimed at iter-v3/045 (the original /045 PROMISING bundle ingredient) appears to have been **single-seed=42 favorable Optuna draw**; at iter-v3/051 (default ATR, different Optuna trajectory) LDO IS is also negative.

A 23.1% OOS win rate from 13 trades over ~14 months is **far below random walk 50%** — this reflects a signal generator producing directionally wrong predictions for LDO in the OOS period. The frozen-baseline pattern (-17.44 OOS bit-identical at seed 42 across /047, /049, /051) plus the negative IS contribution at /051 default config jointly demonstrate that LDO's signal generator has a structural problem in v3 architecture, not a customization-layer problem.

### iter-v3/052 axis = LDO removal investigation (HIGH-priority cycle 4 #2)

Per Critic FINAL `32cc46f` Recommendation #1:

**EDA priorities for iter-v3/052** (mandatory before brief write per `feedback_v3_axis_selection_quant_discipline.md`):

1. **Quantify LDO IS+OOS PnL contribution at iter-v3/051 baseline.**
   - Source: `reports-v3/iteration_v3-051/in_sample/per_symbol.csv` (LDO IS PnL share = -14.96%) + `reports-v3/iteration_v3-051/out_of_sample/per_symbol.csv` (LDO OOS share = -116.17%).
2. **2-sym BCH+TRX vs 3-sym BCH+LDO+TRX IS aggregate Sharpe** at iter-v3/051 multi-month walk-forward (using iter-v3/051 trade roster as starting state; counterfactual remove LDO trades and re-compute aggregate IS Sharpe).
3. **If LDO removal lifts BOTH IS and OOS at single-seed → PROMISING-clean for /052 axis.**
4. **Fresh EDA on /051 trade roster** supersedes /050 EDA (LDO calculus changed: at /050 LDO IS contribution was near-zero +0.85; at /051 LDO IS contribution is -14.96% — clear drag).

The /051 setup REVERT to /028 architecture provides the cleanest possible LDO-removal counterfactual: no per-symbol customizations to confound, default ATR for all symbols, no primitive 10 to remove specific BCH trades. This is the ideal baseline for the LDO removal hypothesis test.

## REVERT Mechanism Verification

The system-level REVERT successfully restored iter-v3/028 architecture. Verification table per Critic FINAL `32cc46f`:

| Dimension | Expected (iter-v3/028 reference) | Observed iter-v3/051 | Status |
|---|---|---|---|
| V3_MODELS | 3 symbols (BCH, LDO, TRX) | 3 symbols — confirmed | PASS |
| V3_ATR_MULTIPLIERS_PER_SYMBOL | {} empty | {} empty — confirmed | PASS |
| block_long_for | () empty | () empty — confirmed | PASS |
| REQUIRED_GAP | 66 = (21+1)×3 | 66 — confirmed | PASS |
| n_trials | 35 (EXPLORATION default) | 525 total = 3×5×35 | PASS |
| IS monthly_sharpe (single-seed band) | ≈ [+0.40, +0.65] | +0.4506 | WITHIN range (lower portion) |
| OOS monthly_sharpe (single-seed band) | ≈ [+0.30, +0.80] | +0.5891 | WITHIN range (mid-portion) |
| IS trades (multi-seed ref /028 = 156) | 130-200 predicted | 178 (+14.1% vs ref) | WITHIN range |
| OOS trades (multi-seed ref /028 = 95) | 70-110 predicted | 96 | WITHIN range |
| OOS max_dd | — | 32.75% (vs /028 23.53% multi-seed mean) | Slight elevation (single-seed lottery) |

The /051 single-seed result (IS +0.4506 / OOS +0.5891) lands in the predicted /028 single-seed band [+0.40, +0.65] IS / [+0.30, +0.80] OOS. The REVERT mechanically worked as designed; fracdiff did not add lift. This is mechanistically clean evidence: the REVERT successfully removed cycle 3 customizations and restored /028-architecture starting state.

## What Worked

- **Methodology of the run is clean.** All 12 standard methodology checks PASS per Critic FINAL `32cc46f`:
  - Check 1 (Look-ahead audit) PASS — `compute_fracdiff_d05_close` (`engineered_v3.py:264-327`) uses Fixed-Width Window FFD with no look-ahead. 5 adversarial tests in `test_fracdiff_d05_universal.py` verify per-bar t's output uses only `close[t-k]` data.
  - Check 2 (Embargo width) PASS — REQUIRED_GAP correctly recomputed (66 = (21+1)×3) per universe contraction 4→3.
  - Check 3 (Multiple-testing) EXPLORATION-INFORMATIONAL — DSR=0.0 structural artifact at n_trials=525 per `feedback_v3_dsr_mode_artifact.md`; PBO 0.1168 PASS; PSR 1.0 PASS.
  - Check 4 (IC) PASS — pooled cross-symbol max |IC| = 0.1803 (fracdiff vs range_realized_vol_50), well below 0.70 strict gate. Per-symbol IS-subset extreme (LDO 0.7381 with vwap_dev_20) dissolved at pooled level.
  - Check 5 (ADF stationarity) PASS — BCH p=0.0, LDO p=0.0, TRX p=0.003 (all clear 0.05 by wide margins).
  - Check 6 (Pareto) PASS (single-seed trivially non-dominated; lottery caveat applies).
  - Check 7 (Reproducibility) PASS — setup SHA `c0ebe21`, ITERATION_LABEL "v3-051", explicit feature_columns, PnL spot-check verified.
  - Check 8 (Hypothesis-Implementation alignment) PASS (hypothesis tested; brief pre-registration defect noted separately).
  - Checks 9-12 PASS or N/A.

- **fracdiff_d05_close was LEARNED.** Ranks 11-12/15 across 3 per-symbol models (BCH 12, LDO 11, TRX 11); portfolio rank 13. PATH B (PROMISING-INERT requiring rank > 13 in ALL 3 syms) conclusively NOT triggered. The feature has signal — just not enough to lift IS at single-seed n_trials=35 universal scope.

- **REVERT mechanism worked as designed.** Single-seed IS +0.4506 / OOS +0.5891 lands in the predicted /028 single-seed band [+0.40, +0.65] / [+0.30, +0.80]. Mechanistically clean evidence that the REVERT removed cycle 3 customizations cleanly.

- **PBO 0.1168 PASS** (threshold 0.40). frac_positive_paths = 64.4% — mild improvement vs iter-v3/050's 53.3%, reflecting that the 3-symbol REVERT produces more consistent path-level generalization than the 4-symbol cycle 3 universe. Roughly comparable to iter-v3/028 baseline level (first successful CONFIRMATION).

- **Wall-clock 1.28h** (within 2h EXPLORATION cap; well under the cap).

- **LDO structural drag investigation provides high-quality evidence for iter-v3/052 axis.** The /051 result resolves an ambiguity that /050 EDA could not (LDO IS contribution was near-zero +0.85 at /050; at /051 default config it's clearly negative -14.96%). iter-v3/052 has a clean, EDA-evidenced axis to investigate.

## What Failed

- **Pre-registered hypothesis FALSIFIED on IS axis.** Brief Section 1 predicted IS Sharpe lift +0.05 to +0.30 vs +0.5101 anchor; observed Δ = -0.0595 (below the lower band by 0.11). Universal-scope fracdiff_d05_close addition does NOT lift IS Sharpe at single-seed n_trials=35.

- **No pre-registered path cleanly fires** (brief Section 8 defect). Result landed in no-man's-land between PATH A (+0.05 ceiling) and PATH C-clean (-0.10 floor). Critic adjudicated as EXPLORATION-NULL-RESULT.

- **iter-v3/035 BCH-only fracdiff +37.98 OOS swing precedent FALSIFIED.** Reclassified as PATH C-suspicious anti-pattern (IS-OOS daily ratio 27.88×) — Optuna lottery artifact, not signal. The universal-scope retest in clean conditions (IS-OOS ratio 1.148 in band) produced no IS lift.

- **regime_momentum_signed_5d signal at bottom of importance distribution** (BCH 14/15, LDO 15/15, TRX 12/15, portfolio 15/15). The iter-v3/028 edge ingredient remains at the bottom of the importance distribution across all per-symbol models even after the 3-symbol REVERT (which the /050 closeout hypothesized might "recover" the signal). Recovery did not occur. This adds urgency to the cycle 4 priority of investigating regime_momentum's signal strength (Critic /050 rec #4).

- **fracdiff and regime_momentum compete for split budget** (Critic Adversarial Finding #3). fracdiff outranks regime_momentum at ALL 3 symbols and portfolio (margins narrow: 54.0 vs 47.6 BCH; 109.4 vs 101.0 LDO; 91.0 vs 89.0 TRX; 254.4 vs 237.6 portfolio). Both features rank in bottom tier with pairwise IC = 0.148 (low). Partial collinearity suggests fracdiff captures a similar "price-path memory" signal to regime_momentum and the two features cannibalize each other for low-priority split budget — not orthogonal information dimensions.

- **OOS daily Sharpe (1.1116) exceeds IS daily Sharpe (0.9685)** at ratio 1.148. Not suspicious (within [0.5, 2.0] band), but unusual: reflects OOS window containing a favorable BCH period (Q2 2025 large positive months: Apr +4.91%, May +11.51%, Jun +14.36%) inflating OOS daily Sharpe.

- **OOS top concentration 67.65%** (BCH dominant; well above 30% aspirational gate). Expected for the 3-symbol universe; consistent with /028 baseline's 76.47%.

- **Brief pre-registration defect** — Section 8's 4 LOCKED paths left a no-man's-land for IS Δ ∈ (-0.10, +0.05) + OOS Δ ∈ (-0.30, +0.20) + feature LEARNED. Critic FINAL `32cc46f` recommends adding PATH D (EXPLORATION-NULL-RESULT) to future EXPLORATION briefs (carry-forward responsibility to iter-v3/052 QR).

## CPCV Analysis

45 paths generated (REQUIRED_GAP = 66; 3-symbol universe).

| Statistic | Value |
|---|---:|
| Paths positive | 29 of 45 (64.4%) |
| Median path Sharpe | +0.335 |
| PBO (per-cell mean) | 0.1168 |
| frac_positive_paths | 0.644 |
| Q25 path Sharpe | -0.243 |
| Q75 path Sharpe | +0.884 |

PBO = 0.1168 well below 0.40 threshold (PASS). frac_positive_paths = 64.4% mild improvement vs iter-v3/050's 53.3%. The 3-symbol CPCV roughly comparable to iter-v3/028 baseline level (first successful CONFIRMATION). CPCV signal is mildly constructive despite the IS Sharpe shortfall.

## Gate Efficacy Table

| Gate | Parameter | Behavior at /051 |
|---|---|---|
| BTC trend filter | lookback=42, threshold=15% | 32 OOS trades killed (~25% of candidates) |
| OOD z-score gate | zscore_threshold=2.0, **15-D space** (UP from 14-D) | embedded; new dimension fracdiff_d05_close |
| ADX gate | threshold=20.0 global; per-symbol={} | embedded |
| Primitive 10 — BCH direction block | block_long_for=() | REVERTED; gate in code but not firing |
| Per-symbol ATR | DEFAULT (2.0, 1.0) all syms | embedded |
| Per-symbol cap | enable_per_symbol_cap=False | DISABLED (CLOSED per /020) |
| Regime gate | enable_regime_gate=False | DISABLED (CLOSED per /022) |

BTC trend killed 32 OOS trades (~25% of candidates) — consistent with prior v3 iterations.

## Bundle Status Update

- **BASELINE_V3.md UNCHANGED at iter-v3/028** (+0.5101 IS / +0.5053 OOS; SHA `b0576df`). iter-v3/051 is EXPLORATION; no MERGE gate evaluation.
- **iter-v3/028 architecture RESTORED as starting point for cycle 4 EXPLORATIONs**:
  - V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols
  - V3_ATR_MULTIPLIERS_PER_SYMBOL = {} empty
  - block_long_for = () empty
  - V3_FEATURE_COLUMNS_TOP_N = 14 features (regime_momentum_signed_5d PRESERVED; fracdiff_d05_close to be DROPPED at /052 setup)
- **fracdiff_d05_close PARKED (not CLOSED).** Drop from `V3_FEATURE_COLUMNS_TOP_N` at iter-v3/052 setup (15 → 14). Retain `compute_fracdiff_d05_close` (`engineered_v3.py:264-327`) as dead code at zero revert cost. Retain 5 adversarial tests (`tests/features_v3/test_fracdiff_d05_universal.py`). Future retest conditions: per-symbol scoping; n_trials=50+; multi-seed CONFIRMATION as bundle ingredient.
- **ALGO dropped from V3_MODELS** — REVERT to 3-sym universe per system-level mandate (`feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10). ALGO code path infrastructure remains.
- **Primitive 10 (`block_long_for`) PRESERVED as code infrastructure** — mechanism + 7 adversarial tests + GateStats counter REMAIN. Wired value `("BCHUSDT",)` REVERTED to `()` at /051 setup per system-level REVERT.
- **regime_momentum_signed_5d PRESERVED** in `V3_FEATURE_COLUMNS_TOP_N` (iter-v3/028 edge ingredient). Importance rank at /051 portfolio = 15/15 (dead last); BCH 14/15; LDO 15/15; TRX 12/15. The signal weakness across the 3-symbol REVERT did NOT recover — adding cycle 4 priority for regime_momentum investigation.
- **Per-symbol architecture (V3_FEATURES_PER_SYMBOL + V3_ATR_MULTIPLIERS_PER_SYMBOL) PRESERVED as code infrastructure** — validated at multi-seed; no architectural defects. Future cycles may use the infrastructure with IS-axis discipline.
- **NO TAG ISSUED.** EXPLORATION; only CONFIRMATION-MERGE iterations get `v0.v3-NNN` tags.

## Cycle 4 Cadence: 1/10 EXPLORATIONs advanced

Per `feedback_v3_strict_10_to_1_cadence.md`:

- **Cycle 4 begins at iter-v3/051 = #1 of 10 EXPLORATIONs** (this iteration).
- **Cycle 4 CONFIRMATION at iter-v3/061** (SEPARATE single-seed iter-v3/060 first; do NOT collapse the 10th EXPLORATION into CONFIRMATION).
- **9 more EXPLORATIONs remain** before cycle 4 CONFIRMATION: iter-v3/052 through iter-v3/060.
- **Cadence wall-clock caps**: EXPLORATION 2h, CONFIRMATION 6h. iter-v3/051 actual: 1.28h within cap.
- **Cycle 4 hypothesis** (carry-forward from /050 closeout): "lift IS Sharpe to ≥ +0.5101 (BASELINE_V3.md update gate floor) while preserving OOS Sharpe ≥ +0.5053 via UNIVERSAL axes (per-symbol customizations rejected at bundle level)." iter-v3/051 result: IS +0.4506 < +0.5101 → cycle 4 hypothesis NOT YET satisfied; 9 EXPLORATIONs remaining.

## iter-v3/052 EDA Priorities (per Critic FINAL `32cc46f` Recommendation #1)

iter-v3/052 axis = **LDO removal investigation** (HIGH-priority cycle 4 #2).

Per `feedback_v3_axis_selection_quant_discipline.md`, the QR must produce numerical tables in `analysis/iteration_v3-052/*.py` with EDA-derived numerical evidence BEFORE locking the brief. EDA priorities:

### EDA Axis 1 — Quantify LDO contribution at iter-v3/051 baseline

- LDO IS PnL share at /051: -14.96% (source: `reports-v3/iteration_v3-051/in_sample/per_symbol.csv`).
- LDO OOS weighted_pnl at /051: -17.44 (source: `reports-v3/iteration_v3-051/out_of_sample/per_symbol.csv`).
- LDO OOS WR at /051: 23.1% (3 wins / 13 trades; far below random walk 50%).
- Frozen-baseline pattern: -17.44 OOS bit-identical at seed 42 across iter-v3/047, /049, /051 — LDO seed-42 Optuna trajectory is deterministic at REVERT configurations.

### EDA Axis 2 — 2-sym BCH+TRX vs 3-sym BCH+LDO+TRX counterfactual

- Source data: iter-v3/051 trade rosters (`reports-v3/iteration_v3-051/in_sample/trades.csv` + `out_of_sample/trades.csv`).
- Counterfactual: REMOVE LDO trades and re-compute aggregate IS Sharpe + OOS Sharpe at the 2-sym (BCH+TRX) baseline.
- Predicted: IS Sharpe lifts ~+0.05 to +0.15 from LDO IS regression removal; OOS Sharpe lifts ~+0.10 to +0.30 from LDO OOS drag removal.
- If LDO removal lifts BOTH IS and OOS at single-seed → **PROMISING-clean** candidate for iter-v3/052 axis.

### EDA Axis 3 — REQUIRED_GAP recompute

- 2-sym universe: REQUIRED_GAP = 44 = (21+1)×2 (recompute from 66 = (21+1)×3 for 3-sym).
- CPCV path generation adjusts accordingly.

### EDA Axis 4 — V3_MODELS dispatch

- Setup commit must update `V3_MODELS = (BCHUSDT, TRXUSDT)` (drop LDOUSDT).
- ITERATION_LABEL = "v3-052".
- Drop fracdiff_d05_close from `V3_FEATURE_COLUMNS_TOP_N` (15 → 14; per /051 closeout).

### EDA Axis 5 — Fresh EDA supersedes /050 EDA

- The /050 EDA Axis A rejection (LDO IS Δ -0.015 at /050 config) is SUPERSEDED by /051 evidence (LDO IS Δ -14.96% PnL share at /028-reverted config).
- Brief Section 2 must contain numerical tables comparing the 2-sym vs 3-sym counterfactual at /051 trade-roster level.

### Pre-registration tightening

iter-v3/052 brief Section 8 must include PATH D (EXPLORATION-NULL-RESULT) per Critic FINAL `32cc46f` Recommendation #3:

```
PATH D (EXPLORATION-NULL-RESULT):
  IS Δ ∈ (-0.10, +0.05)
  AND OOS Δ ∈ (-0.20, +0.20)
  AND axis-relevant feature/symbol LEARNED (importance rank ≤ 12 in ≥1 sym
    OR trades produced)
  → classify as null result; drop axis from V3_FEATURE_COLUMNS_TOP_N or
    V3_MODELS at NEXT setup; PARK (do NOT mark CLOSED); retain code at
    zero revert cost.
```

## Memory Rule Updates

- **NO new memory rule introduced.** `feedback_v3_per_symbol_lifts_oos_breaks_is.md` (UPDATED 2026-05-10 at /050 closeout) governed the system-level REVERT and fired correctly. `feedback_v3_axis_selection_quant_discipline.md` governed the EDA-driven axis selection at /051 (QR EDA at SHA `290f37b` produced 3 scripts ranking 4 candidate axes; fracdiff_d05_close UNIVERSAL was selected). `feedback_v3_exploration_n_trials_35.md` governed n_trials=35 default. `feedback_v3_single_seed_frozen_baseline.md` governed the single-seed=42 lottery caveat applied to the OOS Δ interpretation. `feedback_v3_dsr_mode_artifact.md` governed the EXPLORATION-INFORMATIONAL DSR interpretation. `feedback_v3_engineered_feature_pivot.md` governed the Category 2 IC carve-out.

- **`feedback_v3_strict_10_to_1_cadence.md` advances 1/10** for cycle 4. iter-v3/051 is cycle 4 #1; 9 more EXPLORATIONs needed before iter-v3/061 CONFIRMATION.

- **Brief pre-registration tightening recommendation** (Critic FINAL `32cc46f` rec #3): add PATH D (EXPLORATION-NULL-RESULT) to future EXPLORATION brief Section 8. NOT a new memory rule (no orchestrator update of `feedback_*.md` required); rather, a carry-forward action item for iter-v3/052 QR to include in the brief template.

## Architectural Decisions

- **BASELINE_V3.md UNCHANGED at iter-v3/028** (+0.5101 IS / +0.5053 OOS; SHA `b0576df`). EXPLORATION; no MERGE gate evaluation.
- **iter-v3/028 architecture RESTORED** as cycle 4 starting baseline (V3_MODELS = 3-sym; V3_ATR_MULTIPLIERS_PER_SYMBOL = {}; block_long_for = (); REQUIRED_GAP = 66).
- **fracdiff_d05_close PARKED (not CLOSED).** Drop from `V3_FEATURE_COLUMNS_TOP_N` at /052 setup; retain compute function + tests as dead code at zero revert cost.
- **ALGO dropped from V3_MODELS** at /051 setup REVERT (system-level mandate from `feedback_v3_per_symbol_lifts_oos_breaks_is.md`).
- **Primitive 10 (`block_long_for`) wired value REVERTED to `()`** at /051 setup; mechanism + tests + GateStats counter PRESERVED as code.
- **Per-symbol architecture (V3_FEATURES_PER_SYMBOL + V3_ATR_MULTIPLIERS_PER_SYMBOL) PRESERVED as code infrastructure** — validated at multi-seed (/050); no architectural defects. Future cycles may use with IS-axis discipline.
- **regime_momentum_signed_5d PRESERVED** as iter-v3/028 edge ingredient in `V3_FEATURE_COLUMNS_TOP_N`. Signal weakness at /051 (rank 15/15 portfolio) adds urgency to investigation but the feature is NOT under test at /051.
- **`--clean-oof` guardrail RETAINED** (SHA `6a216b5`). Behavior correct at /051.
- **NO TAG ISSUED.** EXPLORATION; only CONFIRMATION-MERGE iterations get `v0.v3-NNN` tags.

## See Also

- `briefs-v3/iteration_v3-051/research_brief.md` — Phase 5 brief (SHA `6697f95`)
- `briefs-v3/iteration_v3-051/phase5p5_gate.md` — Phase 5.5 gate PASS (SHA `1236e3c`)
- `briefs-v3/iteration_v3-051/engineering_report.md` — Phase 6/7 engineering report (SHA `13a6ec5`; EXPLORATION-NEGATIVE-BORDERLINE classification)
- `briefs-v3/iteration_v3-051/review.md` — Phase 7.5 Critic FINAL (SHA `32cc46f`; EXPLORATION-NULL-RESULT)
- `reports-v3/iteration_v3-051/comparison.csv` — primary numerical results (single-seed)
- `reports-v3/iteration_v3-051/seed_summary.json` — per-seed data (1 outer seed)
- `reports-v3/iteration_v3-051/dsr.json` — DSR/PBO/PSR/n_eff (n_trials=525 EXPLORATION-spec)
- `reports-v3/iteration_v3-051/per_cell_pbo.csv` — per-cell PBO
- `reports-v3/iteration_v3-051/cpcv_paths.csv` — CPCV path data (45 paths)
- `reports-v3/iteration_v3-051/ic_matrix.csv` — fracdiff vs existing 14 features (max |IC|=0.1803 pooled)
- `reports-v3/iteration_v3-051/adf_test.csv` — fracdiff ADF stationarity per symbol
- `reports-v3/iteration_v3-051/in_sample/per_symbol.csv` — IS per-symbol PnL attribution
- `reports-v3/iteration_v3-051/out_of_sample/per_symbol.csv` — OOS per-symbol PnL attribution
- `reports-v3/iteration_v3-051/in_sample/model_importance_last_month_*.csv` — feature importance per symbol + portfolio (fracdiff ranks 11-12 + portfolio 13)
- `reports-v3/iteration_v3-051/in_sample/trades.csv` + `out_of_sample/trades.csv` — trade rosters
- `analysis/iteration_v3-051/synthesis.md` + `candidate_axes_ranking.md` (SHA `290f37b`) — EDA ranking of 4 candidate axes
- `analysis/iteration_v3-051/axis_a_ldo_attribution.csv` — LDO removal rejection at /050 config (SUPERSEDED by /051 evidence)
- `analysis/iteration_v3-051/axis_c_fracdiff_adf.csv` — fracdiff ADF stationarity per symbol (pre-flight)
- `analysis/iteration_v3-051/axis_c_fracdiff_per_sym_ic.csv` — fracdiff per-symbol IC matrix (carve-out evaluation)
- `analysis/iteration_v3-051/axis_c_fracdiff_univariate.csv` — fracdiff univariate Spearman ρ per symbol
- `src/crypto_trade/features_v3/engineered_v3.py` (lines 264-327) — `compute_fracdiff_d05_close` FFD implementation
- `src/crypto_trade/features_v3/__init__.py` — V3_FEATURE_COLUMNS_TOP_N (15 elements at /051; revert to 14 at /052)
- `run_baseline_v3.py` — ITERATION_LABEL "v3-051"; V3_MODELS 3-sym; block_long_for=()
- `validation_v3.py` — REQUIRED_GAP=66 (recomputed for 3-sym universe)
- `tests/features_v3/test_fracdiff_d05_universal.py` — 5 adversarial tests (PASS; retain at /052 as dead-code coverage)
- `BASELINE_V3.md` — UNCHANGED at iter-v3/028 (+0.5101 IS / +0.5053 OOS)
- Setup commit SHA `c0ebe21` — V3_FEATURE_COLUMNS_TOP_N=15 + system-level REVERT
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_per_symbol_lifts_oos_breaks_is.md` — UPDATED 2026-05-10; governed /051 system-level REVERT
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_axis_selection_quant_discipline.md` — governed /051 EDA-driven axis selection
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_exploration_n_trials_35.md` — governed n_trials=35 default
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_single_seed_frozen_baseline.md` — governed single-seed=42 lottery caveat
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_dsr_mode_artifact.md` — governed EXPLORATION-INFORMATIONAL DSR interpretation
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_engineered_feature_pivot.md` — governed Category 2 IC carve-out
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_strict_10_to_1_cadence.md` — cycle 4 cadence 1/10 advanced
- `diary-v3/iteration_v3-050.md` — immediate predecessor (CONFIRMATION-NO-MERGE-revert; cycle 3 closeout)
- `diary-v3/iteration_v3-049.md` — cycle 3 #10 of 10 closeout
- `diary-v3/iteration_v3-047.md` — primitive 10 introduction (REVERTED at /051)
- `diary-v3/iteration_v3-045.md` — LDO per-symbol ATR (2.0, 1.5) PROMISING-anchor (RETIRED at /050; per-symbol customization REVERTED at /051)
- `diary-v3/iteration_v3-035.md` — BCH-only fracdiff +37.98 OOS precedent (FALSIFIED at /051 in clean conditions)
- `diary-v3/iteration_v3-028.md` — first CONFIRMATION-MERGE (BASELINE_V3.md anchor)
- `briefs-v3/exploration_catalog.md` — iter-v3/051 catalog row at diary closure (EXPLORATION-NULL-RESULT verdict)
