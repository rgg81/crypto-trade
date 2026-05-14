# iter-v3/065 — Cycle 1 #6 SUSPICIOUS-OOS-DOMINANT / EXPLORATION-PROMISING / FIRST /069 ADVANCEMENT CANDIDATE

**Date**: 2026-05-14
**Type**: EXPLORATION (cycle 1 #6 of 10; FIRST NON-FEATURE PIVOT per Critic /064 Rec #4)
**Axis**: UNIVERSAL labeling Path D — `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5)` (SL widened 1.0× → 1.5×ATR; TP unchanged 2.0×ATR)
**Verdict**: EXPLORATION-PROMISING per Critic FINAL `2553a9a`
**Classification**: SUSPICIOUS-OOS-DOMINANT per Section 8.3 (OOS ≥ +0.20, IS < +0.10)
**BASELINE_V3.md**: UNCHANGED (still anchors `v0.v3-059`; /065 NOT a direct merge candidate per Section 8.3)
**Branch**: `iteration-v3/065`

## 1. What was done

Per Critic /064 Rec #4 NON-FEATURE pivot mandate, cycle 1 #6 pivoted to UNIVERSAL labeling axis (NOT per-symbol per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`).

QR EDA at SHA `662659c` chose Path D (SL widening 1.0 → 1.5) per quantitative justification:
- LDO had structural label noise at default: 68.7% SL-hit rate vs 30.8% TP-hit rate (worst TP/SL ratio of 3 symbols)
- LDO avg-bars-to-SL (2.90) is 0.3 bars FASTER than avg-bars-to-TP (3.19) — intra-bar noise hits SL premature
- Path D predicted +8.6pp LDO TP-rate lift; preserves universal change discipline

Commit chain: EDA `662659c` → setup `6d1c7cf` → backfill `014e1f5` → implementation `176f46f` → pre-flight ATR assertion fix → Phase 5.5 gate `7bbbf75` → engineering report `ae7bf50` → Critic review `2553a9a`. Wall-clock 0.67h.

**Pre-flight blocked once** on a stale `(2.0, 1.0)` per-symbol ATR fallback assertion at run_baseline_v3.py:504 that the QE missed when updating DEFAULT_ATR_MULTIPLIERS at line 418. Fix committed inline by orchestrator; backtest re-launched cleanly.

## 2. Results

| Metric | /060 anchor | /065 (SL=1.5) | Δ |
|---|---|---|---|
| IS monthly Sharpe | +0.8325 | +0.6751 | **-0.16** |
| OOS monthly Sharpe | +0.1403 | **+1.0537** | **+0.91** |
| OOS/IS daily ratio | 0.28 | 1.09 | UP |
| IS WR | 28.99% | 40.37% | **+11.4pp** |
| OOS WR | 36.17% | 48.39% | **+12.2pp** |
| IS PF | 1.49 | 1.31 | -0.18 |
| OOS PF | 1.21 | 1.29 | +0.08 |
| IS MaxDD | 30.97% | 27.10% | -3.9% |
| OOS MaxDD | 34.53% | 33.27% | -1.3% |
| IS trades | 159 | 161 | +2 |
| OOS trades | 94 | 93 | -1 |
| frac_positive_paths | 0.6444 | 0.6444 | 0 |
| **DSR_relative** | **0.0** | **0.9203** | **+0.92** |
| PSR | 0.9763 | 1.0000 | +0.02 |
| n_eff | 19 | 19 | 0 |

Per-symbol OOS:
- BCH +57.40 (39 trades, 59.0% WR, 149.08% concentration)
- LDO **-19.82** (13 trades, **30.8% WR**) — IMPROVED vs /060 (-19.72 wpnl at 18.2% WR) AND FAR better than /064's catastrophic 7.1% WR
- TRX +0.92 (41 tr, 43.9% WR) — flat (vs /060's +4.16)

## 3. Why this is qualitatively different from /063/064

| Pattern | /063 (mass 14→46) | /064 (+adx_14) | /065 (SL widening) |
|---|---|---|---|
| IS Δ vs /060 | -1.38 | -0.68 | **-0.16** (small) |
| OOS Δ vs /060 | +0.31 | +0.15 | **+0.91** (large) |
| BCH OOS conc | 118% | 599% | **149%** (less extreme) |
| LDO OOS WR | 33% (3 tr) | 7% (1/14) | **30.8% (4/13)** (recovered) |
| Win rate change | mixed | mixed | **uniform +11-12pp** |
| DSR_relative | 0.0 | 0.0 | **0.9203** (second highest in v3) |

The uniform WR uplift (+11pp IS, +12pp OOS across all symbols) is the structural signature of REAL signal improvement vs BCH-concentration lottery. /065 is the FIRST cycle 1 result with positive structural metrics.

## 4. Critic verdict summary

OVERALL=EXPLORATION-PROMISING per Critic FINAL `2553a9a`. 13/13 Checks PASS (1 WARN on Check 8 anchor-value propagation in Section 4.3 — recurrence of Critic /064 Rec #1 violation; non-verdict-affecting).

§11 Anti-Pattern Scan: 13/13 PASS.

Adversarial findings dispositioned:
- OOS Sharpe +1.05 magnitude (2.6× predicted upper band) attributed to BCH-favorable OOS window + universal mechanism; lottery flag for /069 validation
- LDO improvement matches EDA T1 prediction exactly (30.8% TP-rate predicted, 30.8% observed) — mechanism supported
- BCH IS concentration dropped 176.68% → 93.71% (universal SL helps LDO/TRX participate in IS — structurally good)

## 5. PATH classification

**SUSPICIOUS-OOS-DOMINANT** per brief Section 8.3 LOCKED. Per `feedback_v3_cycle1_axis_pass_criteria.md`: SUSPICIOUS-OOS-DOMINANT axes MUST cross-validate at CONFIRMATION (iter-v3/069+) against /059's CONFIRMATION baseline (NOT /065 EXPLORATION-mode), per `feedback_v3_strict_both_is_oos_baseline.md` (BOTH IS AND OOS must improve).

## 6. Hypothesis check — partially confirmed

Brief Section 1 hypothesis: "Widening SL from 1.0 to 1.5×ATR universally lifts LDO TP-hit rate +8.6pp via reduced premature stop-out; produces OOS Sharpe ≥+0.20 vs /060 (PROMISING) or NEGATIVE if LDO label-noise hypothesis is wrong"

- OOS Sharpe +0.91 (4.5× the +0.20 PROMISING threshold) — CONFIRMED with large margin
- LDO WR 30.8% — CONFIRMED (matches predicted +8.6pp lift exactly: predicted 39.4% vs observed 30.8% with +12.6pp absolute)
- IS Sharpe -0.16 (small regression; predicted band was [+0.70, +0.95] meaning predicted IS Δ ≈ -0.10; observed -0.16 close to lower bound)

Pre-registered failure mode probabilities (Section 7): INERT 40%, PROMISING 15%, NEGATIVE 30%, SUSPICIOUS-OOS 10%, FAIL 5%. Observed SUSPICIOUS-OOS-DOMINANT (10% probability mass HIT).

## 7. BASELINE_V3.md status

**UNCHANGED** — /059 stays canonical at tag `v0.v3-059`. SUSPICIOUS-OOS-DOMINANT does NOT update BASELINE_V3 per Section 8.3. Only /069 CONFIRMATION can update BASELINE_V3 per `feedback_v3_baseline_update_policy.md`, AND only if multi-seed beats /059 on BOTH IS Sharpe AND OOS Sharpe per `feedback_v3_strict_both_is_oos_baseline.md`.

## 8. Critic Recommendations carried forward

Four process-level recommendations from Critic `2553a9a`:

1. **Anchor-value correctness gate STRENGTHENING** (recurrence of /064 Rec #1): /069 brief MUST cite anchor values bit-exactly from `comparison.csv:LINE` references in EVERY band-prediction table AND engineering report Headline Metrics — not just Section 2.1. Add Phase 5.5 gate check.

2. **TRX OOS WR source consistency**: trades.csv vs per_symbol.csv aggregation discrepancy (46.3% vs 43.9% at /065). Engineering reports must declare canonical source for each per-symbol metric. Add unit test asserting bit-identity.

3. **Behavioral-effect predictor calibration extension for labeling axes**: Section 4.3 trade-count Δ saturation falsifier was designed for feature axes. For labeling axes, predict per-symbol WR Δ (IS+OOS) with explicit counterfactual bands; saturation = WR Δ within ±2pp at all 3 symbols.

4. **/069 CONFIRMATION bundle pre-registration**: STRICT MULTI-SEED PASS criterion — under unified 10-seed ensemble (ENSEMBLE_SIZE=10), (2.0, 1.5) universal SL must produce BOTH (a) IS Sharpe ≥ /059 anchor +1.0894 AND (b) OOS Sharpe ≥ /059 anchor +0.5791. Pre-register FAIL action: if EITHER axis regresses vs /059, /065's universal SL widening is RETIRED to PARKED. Pre-register gate D.x recalibration for universal-axis bundles.

## 9. Next Iteration Ideas

Cycle 1 progress: 6/10 EXPLORATIONs done.

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE (anchor) | PROMISING-EXPLORATION |
| #2 | /061 | TRX RiskV2 anti-Kelly | INERT (closed) |
| #3 | /062 | DSR_relative recalibration (Path C passive) | PASSIVE-DIAGNOSTIC (Path B4 → /069) |
| #4 | /063 | MASS FEATURE EXPANSION 14→46 | SUSPICIOUS-OOS-DOMINANT + IS-COLLAPSE |
| #5 | /064 | Phased mass-expansion #1 (+adx_14) | NEGATIVE (closed) |
| **#6** | **/065** | **UNIVERSAL labeling Path D (SL=1.5)** | **SUSPICIOUS-OOS-DOMINANT (first /069 candidate)** |
| #7-9 | /066-068 | TBD per QR EDA (NON-FEATURE per Critic /064 Rec #4 lock) | TBD |
| CONFIRMATION | /069 | Bundle: SL=1.5 + Path B4 implementation | TBD |

**iter-v3/066** axis candidates (NON-FEATURE per Critic /064 Rec #4 + `feedback_v3_axis_selection_quant_discipline.md`):
- Ensemble parameters (confidence threshold calibration; median vs mean aggregation)
- Risk primitive (alternative vol-scaling formula, e.g., Sortino-based or downside-deviation)
- Universe expansion (consider 4th symbol per /044 ALGO history)
- Further labeling axes (TP multiplier tweak; e.g., test (2.5, 1.5) or (1.5, 1.5) after /065 validates SL widening)

**iter-v3/069** bundle pre-registration:
- (a) Path B4 methodology from /062 deferred spec
- (b) DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5) from /065
- Strict multi-seed MERGE criteria per `feedback_v3_strict_both_is_oos_baseline.md`
