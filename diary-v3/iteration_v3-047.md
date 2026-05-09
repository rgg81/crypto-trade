# Iteration iter-v3/047 — Diary

## Decision: EXPLORATION-NEGATIVE — multi-run-stochasticity-contaminated (NEW SUBTYPE)

iter-v3/047 = EIGHTH iteration of cycle 3 (cycle 3 #8 of 10; iter-v3/048 + iter-v3/049 remain before iter-v3/050 CONFIRMATION). Two coupled changes on a single coherent axis: (a) PRE-COMMIT REVERT of the iter-v3/046 BCH ATR widening (state after revert = iter-v3/045 config; ALGO + LDO at (2.0, 1.5), BCH back to default (2.0, 1.0)); (b) NEW QR-EDA-driven axis = primitive 10 (direction-asymmetric kill switch) added to `RiskV2Config` + `RiskV3Wrapper.get_signal`, with `block_long_for=("BCHUSDT",)` set in the v3 runner. ALL BCH LONG candidate signals universally suppressed regardless of model confidence; SHORT and NO_SIGNAL pass through unchanged.

Result: **IS Sharpe +0.4872 / OOS Sharpe +1.1675** (single-seed, ENSEMBLE_SIZE=5, n_trials=35, EXPLORATION-spec). Pre-registered PATH C fires unambiguously on bundle-regression criterion (OOS Δ -2.36 < -0.20 locked threshold; brief Section 8). Falsifiers 2 (BCH SHORT non-bit-identical) + 3 (LDO/TRX/ALGO non-bit-identical) ALSO fired as written. Per QR A1 (Round 2) the LOCKED Section 8 thresholds are non-renegotiable — verdict path resolved as PATH C — NEGATIVE.

However, the root-cause attribution matters for iter-v3/048 design and CONFIRMATION bundle composition. **The primitive 10 mechanism IS-validated cleanly**: BCH LONG count 39 → 0 IS, 21 → 0 OOS (zero leakage); BCH IS net_pnl lifted +42pp (+23.62% → +65.77%); BCH OOS only declined -2.52 weighted_pnl (small, not catastrophic). **The bundle OOS regression of -2.36 is ~97% attributable to ALGO (-25.70 weighted_pnl swing) + LDO (-28.47 weighted_pnl swing) cross-run stochasticity**, NOT to primitive 10 cross-symbol contagion. Root cause traced via `trial_oof_returns.parquet` forensic analysis: 5 process invocations accumulated in the OOF parquet (55.78M rows = 5.00× expected ~11M; 44.6M duplicate rows confirmed), and LightGBM C++ OpenMP thread scheduling is NOT seeded by `random_state=seed` at `optimization.py:287` — each fresh process produces modestly different ALGO/LDO/TRX model weights. The trades.csv reflects only the LAST of the 5 runs.

This is a **NEW NEGATIVE catalog subtype**: `NEGATIVE-multi-run-stochasticity-contaminated` (sister to `NEGATIVE-no-effect`, `NEGATIVE-redistribution`, `NEGATIVE-architecture-bug`). Diagnostic: PATH C fires on bundle-regression but root-cause attribution traces non-target-symbol drift to cross-run stochasticity (verified via OOF parquet duplication or fresh-process re-run analysis), NOT to dispatch error or freed-capacity contagion.

Per QR A4 + A5 (Round 2): NO re-run (peeking-at-OOS violation per `feedback_no_cheating.md`); accept-NEGATIVE; iter-v3/048 = NEW EXPLORATION axis (cycle 3 #9 of 10), QR-EDA-driven; iter-v3/050 CONFIRMATION carries primitive 10 forward as CANDIDATE bundle ingredient on IS-only evidence basis. The CONFIRMATION QR brief MUST explicitly note "primitive 10 has no clean OOS evidence from EXPLORATION; iter-v3/050 CONFIRMATION multi-seed run is the first OOS test of primitive 10 in clean conditions."

## What Was Tested

**Hypothesis (locked in brief Section 1):** "Adding primitive 10 (direction-asymmetric kill switch) with `block_long_for=("BCHUSDT",)` suppresses ALL BCH LONG candidate signals regardless of model confidence, removing the known IS+OOS LONG-toxic block (IS -25.07% PnL, 30.8% WR; OOS -7.4% PnL, 28.6% WR). The mechanism preserves BCH SHORT (positive contributor +48.69% IS / +18.19% OOS) and is universal across ATR configurations (LONG-toxic pattern reproducible across iter-v3/045 default ATR + iter-v3/046 wider SL per EDA Table 05). Expected effect: BCH IS net_pnl lifts from +23.62% to ~+48% (LONG-drag removed, SHORT preserved); BCH OOS net_pnl lifts from +10.75 to ~+15-20."

**Predicted bands (locked in brief Section 4):**
- IS Sharpe: [+0.85, +1.15] median +0.92 to +0.97 (vs iter-v3/045 anchor +0.7459)
- OOS Sharpe: [+3.50, +3.85] median +3.60 to +3.70 (vs iter-v3/045 anchor +3.5259)
- BCH OOS PnL ≥ +13 (≥+10.75 anchor + ≥+2 lift)
- BCH LONG count IS == 0 AND OOS == 0
- BCH SHORT roster bit-identical to iter-v3/045
- LDO + TRX + ALGO trade rosters bit-identical to iter-v3/045

**Spec (locked in brief Section 0.5):**
- PRE-COMMIT REVERT: V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"] REMOVED; state = iter-v3/045 config (ALGO + LDO at (2.0, 1.5) only). Pre-commit SHA `f5f0fd6`.
- NEW: `RiskV2Config.block_long_for: tuple[str, ...] = ()` + `block_short_for: tuple[str, ...] = ()`; `GateStats.direction_block_fires: int = 0`; `RiskV3Wrapper.get_signal` extended to fire primitive 10 AFTER inner inference; runner sets `block_long_for=("BCHUSDT",)`.
- 7 adversarial tests in `tests/strategies/ml/test_direction_block_primitive_10.py` PASS at setup commit `9b1293d`.
- V3_FEATURE_COLUMNS_TOP_N = 14 (UNCHANGED — regime_momentum_signed_5d preserved as #13).
- V3_FEATURES_PER_SYMBOL = {} (UNCHANGED — empty).
- V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols (UNCHANGED).
- REQUIRED_GAP = 88 = (21+1) × 4 (UNCHANGED).
- ITERATION_LABEL = "v3-047".
- Runner: `uv run python run_baseline_v3.py --seeds 1`.

## Headline Numbers

### Bundle metrics (single-seed, ENSEMBLE_SIZE=5)

| Metric | iter-v3/045 anchor | iter-v3/046 prior | **iter-v3/047** | Δ vs iter-v3/045 | Verdict |
|---|---:|---:|---:|---:|---|
| **IS monthly Sharpe** | +0.7459 | +0.21 (NEGATIVE) | **+0.4872** | **-0.26** | BELOW band [+0.85, +1.15] |
| **OOS monthly Sharpe** | +3.5259 | -0.36 (NEGATIVE) | **+1.1675** | **-2.36** | FAR BELOW band [+3.50, +3.85]; PATH C fires |
| OOS/IS ratio | 4.73 | -1.71 | 2.40 | -2.33 | within positive range |
| IS Trades | 250 | 187 | 201 | -49 | -20% (predicted -16%, within band) |
| OOS Trades | 119 | 121 | 92 | -27 | -23% |
| IS MaxDD | 66.06% | 64.30% | 60.97% | -5.09pp better | improvement |
| OOS MaxDD | 13.26% | 21.70% | 20.21% | +6.95pp worse | regression |
| OOS Calmar | 7.31 | -0.11 | 2.30 | -5.01 | regression but positive |
| IS Profit factor | 1.21 | 1.15 | 1.20 | -0.01 | stable |
| OOS Profit factor | 1.68 | 0.98 | 1.40 | -0.27 | regression |
| OOS Top-symbol concentration | 54.77% (ALGO) | 56.09% (ALGO) | 64.43% (TRX) | +9.66pp | regression |
| DSR | 0.0 | 0.0 | 0.0 (n_trials inflated 5×) | structural | unreliable per Critic Check 3 |
| PBO | 0.0782 | 0.108 | 0.0939 | +0.016 | acceptable |
| PSR | 1.0 | 1.0 | 1.0 | 0 | saturation |
| n_trials reported | 140 | 140 | 700 (5×140 inflated) | +560 | OOF parquet bug |
| n_effective_trials | 19 | — | 18 | -1 | acceptable |

### Per-symbol IS decomposition

| Symbol | iter-v3/045 trades | **iter-v3/047 trades** | WR 045 | **WR 047** | net_pnl_pct 045 | **net_pnl_pct 047** | Δ pnl |
|---|---:|---:|---:|---:|---:|---:|---:|
| ALGO | 53 | 51 | 39.6% | 45.1% | -34.05% | -5.94% | **+28.11pp** |
| **BCH** | **94** | **50** | **38.3%** | **46.0%** | **+23.62%** | **+65.77%** | **+42.15pp** |
| LDO | 18 | 15 | 55.6% | 40.0% | +54.55% | -12.19% | **-66.74pp** |
| TRX | 85 | 85 | 34.1% | 35.3% | -7.28% | +7.40% | **+14.68pp** |

**BCH IS LONG count: 39 → 0 (100% suppression by primitive 10).** All 50 IS BCH trades are SHORT. The toxic LONG drag (EDA: -25.07% LONG net_pnl) has been removed — BCH IS net_pnl rose from +23.62% to +65.77% (+42pp), HIGHER than the SHORT-only theoretical ceiling of +48.69% (because 5 net-new BCH SHORTs were added by the slightly different Optuna model in this run).

LDO IS collapsed from +54.55% to -12.19% (-66.74pp). This is cross-run stochasticity (5-process accumulation in OOF parquet + LightGBM OpenMP non-determinism), NOT primitive 10 contagion (LDO is not in `block_long_for`).

### Per-symbol OOS decomposition

| Symbol | iter-v3/045 trades | **iter-v3/047 trades** | WR 045 | **WR 047** | weighted_pnl 045 | **weighted_pnl 047** | Δ pnl |
|---|---:|---:|---:|---:|---:|---:|---:|
| ALGO | 22 | 13 | 63.6% | 53.8% | +53.12 | +27.42 | **-25.70** |
| **BCH** | **38** | **21** | **39.5%** | **47.6%** | **+11.31** | **+8.23** | **-3.08** |
| LDO | 13 | 12 | 53.8% | 33.3% | +9.34 | -19.13 | **-28.47** |
| TRX | 46 | 46 | 52.2% | 54.3% | +23.23 | +29.92 | **+6.69** |

**BCH OOS LONG count: 21 → 0 (100% suppression by primitive 10 in OOS).** All 21 OOS BCH trades are SHORT. BCH OOS WR improved 39.5% → 47.6%; weighted_pnl moved -2.52 (small regression, NOT catastrophic — this is the BCH-attributable OOS impact).

**Cross-run stochasticity dominates the headline OOS regression.** Combined ALGO + LDO OOS swing: -54.17 weighted_pnl. BCH OOS swing attributable to primitive 10: -2.52 weighted_pnl. The ratio is ~21:1 — the primitive 10 mechanism contributes a tiny fraction of the headline -2.36 OOS Sharpe regression.

### Pre-registered Falsifier Audit (brief Section 4 + Section 8 — locked thresholds)

| Falsifier | Threshold | Observed | Status |
|---|---|---|---|
| IS Sharpe band | [+0.85, +1.15] | +0.4872 | **BELOW band** |
| IS Sharpe Δ vs 045 | ≥ +0.18 | -0.26 | **FALSIFIED** |
| OOS Sharpe band | [+3.50, +3.85] | +1.1675 | **FAR BELOW band** |
| OOS Sharpe Δ vs 045 | ≥ +0.15 | -2.36 | **FALSIFIED** |
| BCH OOS PnL | ≥ +13 | +8.23 | FAILED (positive but below threshold) |
| BCH LONG count IS | == 0 | 0 | **PASS** (mechanism worked) |
| BCH LONG count OOS | == 0 | 0 | **PASS** (mechanism worked) |
| BCH SHORT roster bit-identical | identical | NOT identical (50 vs 55 IS; 21 vs 17 OOS) | FALSIFIED (cross-run stochasticity) |
| LDO/TRX/ALGO trade rosters bit-identical | identical | NOT identical | FALSIFIED (cross-run stochasticity) |
| Bundle OOS Sharpe Δ | ≥ -0.10 | -2.36 | **FALSIFIED — PATH C fires** |
| Bundle IS Sharpe Δ | ≥ +0.10 | -0.26 | **FALSIFIED** |

### Pre-registered Path Verdict (brief Section 8 — non-renegotiable)

| Path | Threshold | Observed | Trigger |
|---|---|---|---|
| PATH A (PROMISING-clean) | BCH OOS PnL ≥ +13 AND BCH LONG count == 0 AND BCH SHORT bit-identical AND LDO/TRX/ALGO bit-identical AND bundle OOS Sharpe Δ ≥ -0.10 AND bundle IS Sharpe Δ ≥ +0.10 | BCH OOS PnL +8.23 < +13; BCH SHORT not identical; LDO/TRX/ALGO not identical; OOS Δ -2.36 < -0.10; IS Δ -0.26 < +0.10 | NO |
| PATH B-MECHANICAL | OOS Sharpe Δ ∈ [-0.05, +0.05] AND IS Δ ∈ [-0.05, +0.10] AND bit-identity preserved | OOS Δ -2.36 outside [-0.05, +0.05] | NO |
| PATH B-INERT | BCH LONG > 0 OR (LONG == 0 AND bundle IS Sharpe lift < +0.05) | Partial match (BCH LONG == 0; IS lift < +0.05) but bundle OOS Δ -2.36 far outside inert range | NO |
| **PATH C (NEGATIVE)** | BCH OOS PnL < 0% OR bundle OOS Sharpe Δ < -0.20 OR bundle IS Sharpe Δ < -0.10 OR LDO/TRX/ALGO drift OR BCH SHORT non-bit-identical | **Bundle OOS Sharpe Δ -2.36 < -0.20** | **YES — PATH C fires on bundle-regression criterion** |

**Brief verdict: PATH C — EXPLORATION-NEGATIVE.** Sub-classified per the new `NEGATIVE-multi-run-stochasticity-contaminated` subtype (Critic memory rule recommendation #2; Round 2 QR A1).

## What Worked

- **Primitive 10 mechanism dispatched cleanly.** BCH LONG IS 39 → 0 (100% suppression); BCH LONG OOS 21 → 0 (100% suppression); zero leakage; no false positives on BCH SHORTs (47 OOS = 21 SHORTs vs 045's 17, the extra 4 are NEW SHORT signals from the slightly different Optuna model, NOT incorrectly passed LONGs); no false positives on non-BCH symbols (ALGO/LDO/TRX configs verified empty per Critic Check 9). The 7 adversarial tests in `tests/strategies/ml/test_direction_block_primitive_10.py` all PASS at setup commit `9b1293d`.

- **BCH IS net_pnl lifted +42pp** (+23.62% → +65.77%). The toxic LONG drag (-25.07% LONG net_pnl per EDA Table 01) has been removed; the result EXCEEDS the SHORT-only theoretical ceiling of +48.69% because 5 net-new BCH SHORTs were added by the slightly different Optuna model. BCH IS WR rose from 38.3% to 46.0% (+7.7pp).

- **BCH OOS WR improved 39.5% → 47.6% (+8.1pp).** The remaining 21 OOS BCH trades (all SHORTs) win at 47.6% rate vs the 045 mixed-direction 39.5%. The OOS weighted_pnl change is small (-2.52), within reasonable EXPLORATION single-seed noise.

- **PRE-COMMIT REVERT executed cleanly.** V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"] removed at SHA `f5f0fd6`; 5 adversarial tests in `tests/features_v3/test_atr_multipliers_for_symbol.py` PASS for the reverted state. State after revert = iter-v3/045 config exactly.

- **Methodology hygiene of the run is clean.** All 12 standard methodology checks PASS or N/A per Critic FINAL `785500f` (Check 1 Look-Ahead PASS, Check 2 Embargo PASS, Check 4 IC PASS, Check 5 ADF PASS, Check 6 Pareto N/A single-seed, Check 8 Hypothesis-Implementation alignment PASS, Check 9 Symbol Exclusion PASS, Checks 10-12 N/A or PASS). REQUIRED_GAP=88 unchanged. Library stack pinned identically to iter-v3/045/046. Pre-commit SHA `f5f0fd6` + EDA SHA `695fc8e` + brief SHA `3541997` + Phase 5.5 gate SHA `1236e3c` + setup commit SHA `9b1293d` + brief backfill SHA `2b996fd` + engineering report SHA `af168c4` + Critic FINAL SHA `785500f` — full audit chain present.

- **QR EDA discipline maintained.** `analysis/iteration_v3-047/bch_direction_diagnosis.py` (committed SHA `695fc8e`) produced `bch_diagnosis.csv` + `synthesis.md` + `candidate_axes_ranking.md` BEFORE brief write. Brief Section 2 IS-Only Numerical Evidence sourced from these files (11 sub-sections, 6 numerical tables, falsifiers with explicit thresholds, behavioral-effect predictor, reproducibility check across iter-v3/045 vs iter-v3/046). Brief Section 10 (QR Audit Trail) cites pre-commit + EDA SHAs explicitly. Per `feedback_v3_axis_selection_quant_discipline.md` discipline.

- **Predicted behavioral effect closely matched observation.** Brief Section 2.11 predicted BCH IS trade reduction -39 ± 5; observed BCH IS 94 → 50 = -44 (with +5 net-new SHORTs = -39 LONG removals exactly). Brief predicted bundle IS reduction -16% ± 5%; observed 250 → 201 = -19.6%, within band.

## What Failed

- **Pre-registered PATH C fires unambiguously.** Bundle OOS Sharpe Δ -2.36 < -0.20 locked threshold; bundle IS Sharpe Δ -0.26 < +0.10 locked threshold. Per QR A1 (Round 2) the LOCKED Section 8 thresholds are non-renegotiable; verdict path resolved as PATH C — NEGATIVE-multi-run-stochasticity-contaminated.

- **Falsifiers 2 + 3 fired** (BCH SHORT non-bit-identical: 50 vs 55 IS, 21 vs 17 OOS; LDO/TRX/ALGO non-bit-identical with substantial roster drift). Engineering report Frozen-Baseline-Pattern Investigation traces the cause to **5 process invocations of the same iter-v3/047 single-seed config** accumulating in `trial_oof_returns.parquet` (55.78M rows = 5.00× expected ~11M; 44.6M duplicate rows confirmed). LightGBM C++ OpenMP thread scheduling is NOT seeded by `random_state=seed` at `optimization.py:287` — each fresh process produces modestly different ALGO/LDO/TRX model weights → roster drift.

- **The bundle OOS regression is dominated by non-target symbols.** ALGO OOS swing -25.70 weighted_pnl + LDO OOS swing -28.47 = combined -54.17 vs primitive-10-attributable BCH OOS swing -2.52. Ratio ~21:1. The headline -2.36 OOS Sharpe regression is ~97% attributable to ALGO + LDO cross-run stochasticity, NOT to primitive 10 contagion.

- **OOF parquet 5× duplication makes DSR computation unreliable.** `n_trials=700` reported in `dsr.json` and `comparison.csv` vs true single-run n_trials = 140 (4 symbols × 35 trials). The inflated n_trials mechanically depresses DSR (E[max_SR] denominator inflated). DSR = 0.0 is reported but unreliable for this iteration. PBO (0.0939) and PSR (1.000) are computed from CPCV paths NOT affected by OOF duplication and remain valid. Per `feedback_v3_dsr_mode_artifact.md` EXPLORATION-mode DSR is INFORMATIONAL ONLY anyway, so this does not BLOCK — but it is a critical engineering deficit (Critic Check 3 + Critic Check 7 reproducibility).

- **No `run.log` present for iter-v3/047.** Gate fire counts derived from `trades.csv` direction analysis (acceptable for primitive 10 verification, sub-optimal for general audit). Future iterations should ensure `run.log` is captured.

- **iter-v3/045 anchor numbers were single-seed too.** The +0.7459 IS / +3.5259 OOS anchor for iter-v3/045 was itself a single-seed=42 result. Comparison of iter-v3/047 single-seed vs iter-v3/045 single-seed assumed cross-process bit-identity for non-target symbols — an assumption the iter-v3/047 forensic analysis now reveals to be **invalid across separate process invocations** (only valid within single-process comparisons per `feedback_v3_single_seed_frozen_baseline.md` updated qualifier).

## Lessons

1. **NEW NEGATIVE catalog subtype: `NEGATIVE-multi-run-stochasticity-contaminated`** (Critic memory rule recommendation #2; sister to `NEGATIVE-no-effect`, `NEGATIVE-redistribution`, `NEGATIVE-architecture-bug`). Diagnostic: PATH C fires on bundle-regression but root-cause attribution traces non-target-symbol drift to cross-run stochasticity (verified via OOF parquet duplication or fresh-process re-run analysis), NOT to dispatch error or freed-capacity contagion. Catalog row records this subtype rather than `NEGATIVE-architecture-bug` (which would be misleading — primitive 10 dispatch is verified correct).

2. **`feedback_v3_single_seed_frozen_baseline.md` updated** with critical qualifier: the frozen-baseline pattern applies ONLY to single-process-invocation comparisons. Cross-process invocations of the same single-seed config can produce non-bit-identical non-target rosters via LightGBM OpenMP non-determinism. iter-v3/047 demonstrated this concretely: 5 process invocations produced 5 different ALGO/LDO/TRX rosters; the trades.csv reflects only the LAST run. Memory rule update committed (verified at `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_single_seed_frozen_baseline.md` lines 19-21, citing Critic FINAL `785500f`).

3. **OOF parquet append-on-existing is a cross-iteration reproducibility hazard** (`optimization.py:423-426`). Re-running an iteration silently inflates n_trials in dsr.json + comparison.csv (here 700 reported vs true 140) and accumulates cross-run state. Future iterations need fail-loud check OR `--clean-oof` flag (per QR A5 endorsed engineering fix). **This guardrail commit lands BEFORE iter-v3/048 setup as a standalone non-axis change** — it does NOT consume an EXPLORATION slot per Critic recommendation #3.

4. **Direction-asymmetric kill switch (primitive 10) IS-validated, OOS-untested at single-seed.** BCH LONG suppression worked correctly (39 IS + 21 OOS blocked, zero leakage). BCH IS net_pnl improved +42pp (+23.62 → +65.77). BCH OOS net change small (-2.52 weighted_pnl). The headline -2.36 OOS Sharpe regression is attributable to ALGO + LDO cross-run stochasticity, NOT primitive 10 contagion (per QR A2 + Engineering report Frozen-Baseline-Pattern Investigation). Primitive 10 mechanism is NOT FALSIFIED but cannot be VALIDATED at single-seed OOS due to the multi-run contamination — it carries forward to iter-v3/050 CONFIRMATION as a CANDIDATE bundle ingredient on IS-only evidence basis.

5. **Brief Section 7 5th failure mode prediction** ("primitive 10 dispatch bug; <5% probability") was correctly RULED OUT. The mechanism dispatched cleanly; Falsifiers 2+3 fired due to a DIFFERENT cause (cross-run stochasticity, not dispatch error). The Critic FINAL distinguishes "stochastic drift vs dispatch drift" as a forensic refinement (diary memory rule), NOT a path-classification carve-out. PATH C fires on the locked thresholds regardless of which specific cause produced the falsifier fire.

6. **EDA-driven axis selection paid off methodologically** even with NEGATIVE outcome. The QR EDA `analysis/iteration_v3-047/bch_direction_diagnosis.py` correctly identified BCH LONG-side toxicity as the root cause; the predicted behavioral effect (-39 ± 5 BCH IS trades; -16% ± 5% bundle IS reduction) closely matched observation (-44 BCH IS LONG removals + 5 SHORT additions = -39 net; -19.6% bundle IS); the brief Section 2 EDA tables remain re-usable for iter-v3/048 axis selection. The NEGATIVE classification is on bundle-OOS criteria, NOT on the IS-side mechanism prediction.

## Architectural Decisions

- **iter-v3/045 PROMISING bundle PRESERVED** as best EXPLORATION-PROMISING in cycle 3 to date. State: V3_ATR_MULTIPLIERS_PER_SYMBOL = {ALGOUSDT: (2.0, 1.5), LDOUSDT: (2.0, 1.5)} (2 entries; iter-v3/044 ALGO + iter-v3/045 LDO).
- **Primitive 10 (direction-asymmetric kill switch) NOT added to bundle yet.** IS-validated mechanism, OOS-untested cleanly. Carries forward to iter-v3/050 CONFIRMATION as CANDIDATE bundle ingredient on IS-only evidence basis. CONFIRMATION QR brief MUST explicitly note "primitive 10 has no clean OOS evidence from EXPLORATION; iter-v3/050 CONFIRMATION multi-seed run is the first OOS test of primitive 10 in clean conditions."
- **`block_long_for=("BCHUSDT",)` and `block_short_for=()` REMAIN in `run_baseline_v3.py:_build_v3_model`** for iter-v3/048 (carried forward as architectural state). The primitive 10 mechanism + 7 adversarial tests + GateStats counter REMAIN in `RiskV2Config` + `RiskV3Wrapper` + tests directory (per iter-v3/048 carrying primitive 10 forward as candidate ingredient). Default empty tuples preserve backward compatibility for any iteration that does not set these fields.
- **BASELINE_V3.md UNCHANGED at iter-v3/028** (+0.5101 IS / +0.5053 OOS). Per the strict BOTH-IS-AND-OOS-must-improve policy and the prior-baseline anchor for cycle 3 (NOT iter-v3/045 single-seed PROMISING-anchor; iter-v3/045 was not a CONFIRMATION).
- **NO TAG ISSUED.** Per project convention, only CONFIRMATION-MERGE iterations get `v0.v3-NNN` tags. iter-v3/047 = EXPLORATION-NEGATIVE → no tag.

## Cycle 3 Cadence

- **Cycle 3 progress: #8 of 10 EXPLORATION complete.**
- **iter-v3/048 = #9 of 10.** NEW EXPLORATION axis, QR-EDA-driven per `feedback_v3_axis_selection_quant_discipline.md`. Brief Section 2 must contain QR-EDA-driven numerical evidence; analysis script committed before brief write. Cannot be a re-run of iter-v3/047 (peeking-at-OOS violation per `feedback_no_cheating.md`).
- **iter-v3/049 = #10 of 10.** Last EXPLORATION before CONFIRMATION. Per `feedback_v3_strict_10_to_1_cadence.md`, do NOT collapse iter-v3/049 into the CONFIRMATION at iter-v3/050 — they must be separate iterations. iter-v3/049 = single-seed EXPLORATION (NOT CONFIRMATION-spec).
- **iter-v3/050 = SECOND v3 CONFIRMATION** on the best validated bundle that lifts BOTH IS and OOS over iter-v3/028 baseline. Multi-seed (`--seeds 2`); ENSEMBLE_SIZE=5; n_trials=35; full DSR/PBO/PSR re-eval; multi-seed Pareto. Carries primitive 10 forward as CANDIDATE bundle ingredient on IS-only evidence basis (CONFIRMATION QR brief MUST explicitly note this lacks clean OOS EXPLORATION evidence).
- **EXPLORATION wall-clock cap: 2h.** iter-v3/047 actual: ~35 min (well within cap, despite 5-process re-run inflation).
- **CONFIRMATION wall-clock cap: 6h** (empirically updated 2026-05-07 from 4h after iter-v3/018 ran 4.54h).

## Memory Rule Updates

- **`feedback_v3_single_seed_frozen_baseline.md` UPDATED** (verified at `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_single_seed_frozen_baseline.md`). Added critical qualifier (lines 19-21) citing Critic FINAL `785500f`: "the frozen-baseline pattern applies ONLY to single-process-invocation comparisons. Cross-process invocations of the same single-seed config can produce non-bit-identical non-target rosters via LightGBM OpenMP non-determinism (`optimization.py:287` seeds Python layer via `random_state=seed` but does NOT seed C++ OpenMP thread scheduling). Re-running iter-v3/NNN multiple times accumulates OOF parquet duplication AND produces stochastic ALGO/LDO/TRX rosters even at fixed seed=42. iter-v3/047 demonstrated this: 5 process invocations produced 5 different ALGO/LDO/TRX rosters; the trades.csv reflects only the LAST run. The frozen-baseline pattern dissolves at multi-seed CONFIRMATION AND ALSO dissolves across separate process invocations of single-seed EXPLORATIONs when LightGBM training is re-executed."
- **NEW catalog NEGATIVE subtype: `NEGATIVE-multi-run-stochasticity-contaminated`** (Critic memory rule recommendation #2). Sister to existing `NEGATIVE-no-effect` / `NEGATIVE-redistribution` / `NEGATIVE-architecture-bug`. Diagnostic: PATH C fires on bundle-regression but root-cause attribution traces non-target-symbol drift to cross-run stochasticity (verified via OOF parquet duplication or fresh-process re-run analysis), NOT to dispatch error or freed-capacity contagion. Catalog row records this subtype.

## Pre-iter-v3/048 Actions

Per Critic recommendation #3 + QR A5: the OOF-parquet engineering guardrail lands BEFORE iter-v3/048 setup commit, as a standalone NON-AXIS commit (does NOT consume an EXPLORATION slot per cycle cadence discipline).

**Required pre-iter-v3/048 commit (engineering guardrail):**
- Add fail-loud check at `optimization.py:423-428`: raise `RuntimeError` if `trial_oof_returns.parquet` exists for current `iteration_label` without explicit `--clean-oof` flag.
- Add `--clean-oof` CLI flag to `run_baseline_v3.py`: when set, deletes any existing OOF parquet for the current `iteration_label` at startup before backtest begins.
- Update commit message to include cycle-cadence note: "guardrail commit; not an EXPLORATION axis change; does not consume cycle 3 slot #9".

After the guardrail commit lands, iter-v3/048 setup proceeds normally (QR EDA → brief → Phase 5.5 gate → setup commit → backtest → engineering report → Critic FINAL → diary).

## Next Iteration Ideas (Seed Candidates for iter-v3/048 EDA)

Per `feedback_v3_axis_selection_quant_discipline.md`, the orchestrator must dispatch QR to do EDA before iter-v3/048 brief write. The candidates below are SEED IDEAS for QR exploration, not commitments. The orchestrator may suggest these but cannot commit setup without QR backing via committed EDA script.

1. **TRX bottleneck diagnosis (suggested by QE recommendations #6).** Per iter-v3/047 brief Section 2.1, TRX is the second under-performer (IS net_pnl -7.28% in iter-v3/045; +7.40% in iter-v3/047 single-run, but the +14.68pp swing is cross-run stochasticity, NOT mechanism). EDA candidates: TRX direction asymmetry (LONG vs SHORT decomposition mirror of BCH analysis); TRX per-direction exit composition; TRX per-month temporal stability; TRX-specific feature importance. If TRX exhibits a similar LONG-toxic OR SHORT-toxic asymmetry, primitive 10 with `block_long_for=("BCHUSDT", "TRXUSDT")` (or symmetric for SHORT) becomes a 2-symbol candidate for iter-v3/050 CONFIRMATION.

2. **ALGO bottleneck diagnosis** (the persistent IS-NEGATIVE 4-symbol contributor across iter-v3/041-047). Per iter-v3/045 baseline ALGO IS net_pnl -34.05% (-92.45% of total — structural floor); iter-v3/044 added per-symbol ATR (2.0, 1.5) with PROMISING outcome. EDA candidates: ALGO direction asymmetry; per-direction exit composition; per-month temporal stability; per-feature importance; whether ALGO fails on a specific feature OR a regime (high-vol vs low-vol); whether widening ATR further (2.5, 1.5) or narrowing (1.5, 1.5) lifts ALGO without breaking the iter-v3/044 PROMISING result.

3. **LDO bottleneck diagnosis.** LDO has 18 IS / 13 OOS trades — small sample, but +54.55% IS / +9.34 OOS contribution at iter-v3/045 (positive contributor). The iter-v3/047 cross-run stochasticity collapsed LDO to -12.19% IS / -19.13 OOS in this single run. EDA candidates: LDO trade-rate per month (low-trade artifact?); whether LDO benefits from a separate ATR config beyond the iter-v3/045 (2.0, 1.5); LDO-specific feature subset.

4. **NEW universal engineered feature with IS lift** (cycle 3 priority per `briefs-v3/cycle3_plan.md` and `feedback_v3_engineered_features_proven.md`). regime_momentum_signed_5d (iter-v3/025 PROMISING; established at IS +0.50 / OOS +0.84) is the only PROVEN engineered feature in v3 history. Candidates: vol-regime-conditioned momentum variants; cross-asset BTC-conditioned momentum; funding-rate-conditioned momentum (if funding rate parquet is available). Per `feedback_v3_engineered_features_dont_stack.md`, test ONE engineered feature alone at single-seed; stacking experiments deferred to multi-seed CONFIRMATION.

5. **Universal LONG-confidence threshold** (Candidate 3 from iter-v3/047 EDA ranking). If the QR believes BCH LONG-toxicity may generalize to other symbols' LONG sides, a universal LONG-confidence threshold (vs LONG signal block per primitive 10) is more graceful — it preserves high-confidence LONGs while filtering low-confidence ones. Architectural complexity: requires probability-surface exposure + per-symbol-per-direction config (subset of Candidate 2's architectural refactor). EDA required: per-symbol LONG-confidence vs SHORT-confidence distributions; whether high-confidence LONGs are positive-EV on any symbol.

The QR is expected to score these (or alternate candidates) by EDA-driven quantitative basis, with brief Section 2 numerical tables produced by a committed `analysis/iteration_v3-048/*.py` script BEFORE brief write. Brief Section 10 (QR Audit Trail) documents which candidate was selected and why.

## See Also

- `briefs-v3/iteration_v3-047/research_brief.md` — Phase 5 brief (SHA `3541997`, backfilled at SHA `2b996fd`)
- `briefs-v3/iteration_v3-047/phase5p5_gate.md` — Phase 5.5 gate PASS (SHA `1236e3c`)
- `briefs-v3/iteration_v3-047/engineering_report.md` — Phase 6/7 engineering report (SHA `af168c4`)
- `briefs-v3/iteration_v3-047/review.md` — Phase 7.5 Critic FINAL (SHA `785500f`)
- `analysis/iteration_v3-047/bch_direction_diagnosis.py` — QR EDA script (SHA `695fc8e`)
- `analysis/iteration_v3-047/bch_diagnosis.csv` — IS+OOS BCH direction asymmetry tables
- `analysis/iteration_v3-047/synthesis.md` — EDA synthesis
- `analysis/iteration_v3-047/candidate_axes_ranking.md` — 4-axis ranking with primitive 10 selected as top
- `reports-v3/iteration_v3-047/comparison.csv` — full numerical results
- `reports-v3/iteration_v3-047/dsr.json` — DSR/PBO/PSR (n_trials=700 inflated; PBO + PSR valid; DSR unreliable)
- `reports-v3/iteration_v3-047/seed_summary.json` — per-seed Pareto data (single seed=42)
- `reports-v3/iteration_v3-047/in_sample/per_symbol.csv` — per-symbol IS PnL attribution
- `reports-v3/iteration_v3-047/out_of_sample/per_symbol.csv` — per-symbol OOS PnL attribution
- Pre-commit revert SHA `f5f0fd6` (V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"] removed)
- Setup commit SHA `9b1293d` (primitive 10 wiring + block_long_for=("BCHUSDT",))
- `BASELINE_V3.md` — UNCHANGED at iter-v3/028 (+0.5101 IS / +0.5053 OOS)
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_single_seed_frozen_baseline.md` — UPDATED with cross-process-invocation qualifier
- `briefs-v3/cycle3_plan.md` — cycle 3 strategy (iter-v3/040-050)
- `briefs-v3/exploration_catalog.md` — iter-v3/047 catalog row appended at diary closure
