# Iteration iter-v3/056 — Diary

## Decision: EXPLORATION-NEGATIVE (PATH C-clean primary; PATH E co-fires 6th consecutive)

iter-v3/056 = **cycle 4 #6 of 10** EXPLORATIONs post-iter-v3/050 NO-MERGE CONFIRMATION. **Axis** (mandated at /055 Critic FINAL SHA `6083b30` Recommendation #1 + /055 diary closeout): **A2 — DSR gate reformulation (methodology-only) — CARRY-FORWARD with 2-line bug fix**. The /055 write-before-read defect at `run_baseline_v3.py:2181-2196` (file-read of `cpcv_paths.csv` before its line-2295 write) is replaced by direct access to the in-memory `flat_path_sharpes` array (line 2090). A 6th adversarial integration test was added per `feedback_v3_methodology_axis_integration_test.md` (created at /055 closeout). Strategy substrate unchanged: V3_MODELS = (BCH+LDO+TRX), V3_FEATURE_COLUMNS_TOP_N = 14, regime_momentum_signed_5d preserved, enable_per_symbol_drawdown_brake = False, REQUIRED_GAP = 66. Run spec: `--seeds 1 --n-trials 35 --clean-oof`.

Result: **IS single-seed Sharpe +0.5101 / OOS single-seed Sharpe +0.5053 (seed 42); BIT-IDENTICAL to iter-v3/028 single-seed=42 and to /055 across IS/OOS Sharpe, IS trades (182), OOS trades (96), per-symbol IS+OOS attribution to 4 decimal places.** **The bug fix landed correctly**: `cpcv_path_sharpe_q75 = 0.8378` (was 0.0 BUG in /055) and `dsr_relative = 0.0044` (was 1.0 BUG in /055) — both non-degenerate, both gate-operative. **But the observed DSR_relative = 0.0044 falls 0.58 below the pre-registered PATH A trigger band [0.50, 0.65]** (recalibrated at /056 brief from /055 Engineer post-hoc 0.5798). PATH C-clean fires unambiguously on band miss. PATH E (CPCV-INVARIANT NULL) co-fires — CPCV 29/45 positive, median +0.3351, Q25 -0.243, Q75 +0.838 bit-identical to /051-/055 (6th consecutive).

Per Critic FINAL `677acc0`:

- PATH A (PROMISING-clean): all conditions hold EXCEPT DSR_relative OOS = 0.0044 (out-of-band by -0.58) → NO
- PATH B (PROMISING-INERT): N/A for methodology axes → NO
- **PATH C-clean (DSR_relative out-of-band)**: 0.0044 vs predicted [0.50, 0.65] → **FIRES UNAMBIGUOUSLY**
- PATH C-clean (bug fix not landed): q75=0.8378 ≠ 0; dsr_relative=0.0044 ≠ psr=1.0 → NO (bug fix LANDED)
- PATH C-clean (strategy unintentionally changed): bit-identical to /055 → NO
- PATH C-suspicious (IS-OOS daily ratio outside [0.5, 2.0]): ratio = 1.295 → NO
- **PATH E (CPCV-INVARIANT NULL)**: 29/45 ✓; +0.3351 ✓; -0.243 ✓; +0.838 ✓ → **FIRES (6th consecutive)**

**Primary classification: PATH C-clean (band miss; predicted post-hoc estimate was built on wrong input granularity). Co-firing: PATH E (6th consecutive).** Per Section 8 outcome rule: "Methodology axis advances iff outcome ∈ {PATH A, PATH E}". PATH A did NOT fire (band miss). **A2 axis does NOT advance — substantively CLOSED at cycle 4.**

Wall-clock: ~2.0h backtest (within 2h EXPLORATION cap; concurrent with other runs). 11/12 standard methodology checks evaluated per Critic FINAL (look-ahead PASS, embargo PASS, **multiple-testing-correction Check 3 FAIL** as expected — DSR_relative gate operative but produces 0.0044 ≈ legacy DSR=0; PBO PASS at 0.1243; IC carry-forward PASS, ADF inherited PASS, Pareto WARN single-seed degenerate, reproducibility PASS, hypothesis-implementation alignment PASS — bug fix verified at lines 2183-2188 with /055 BUG signature `cpcv_paths_csv = REPORTS_DIR` returning ZERO MATCHES, symbol exclusion PASS, feature isolation PASS, forming-candle inherited PASS, library-pinning PASS). No tag issued (EXPLORATION).

## What Was Tested

**Hypothesis (locked in brief Section 1, SHA `4bbcf23`):** "FIXING the `cpcv_path_sharpe_q75` computation at `run_baseline_v3.py:2181-2196` (replace file-read with in-memory `flat_path_sharpes` array) produces non-degenerate DSR_relative value in the recalibrated PATH A band [0.50, 0.65] derived from /055 Engineer post-hoc estimate 0.5798. Strategy substrate UNCHANGED at bit-identical-to-/055 (= /028 single-seed=42). New integration test asserts `cpcv_path_sharpe_q75 > 0 AND dsr_relative != psr`."

**Predicted bands (brief Section 1 + Section 8):**
- IS Sharpe: +0.5101 ± 0.005 (predicted bit-identical to /055 = /028)
- OOS Sharpe: +0.5053 ± 0.005 (predicted bit-identical to /055 = /028)
- IS trades 182 ± 1; OOS trades 96 ± 1
- **DSR_relative OOS: [0.50, 0.65]** (recalibrated centered on /055 post-hoc 0.5798)
- cpcv_path_sharpe_q75: 0.8378 ± 0.005 (matching cycle-4 STRUCTURAL CONSTANT)
- CPCV positive paths: 29/45 (PATH E expected)
- CPCV median Sharpe: +0.3351 ± 0.0005 (PATH E expected to 4 decimals)

**Predicted path classification (brief Section 8):** PATH A: 75% / PATH C-clean (band miss): 10% / PATH C-clean (bug not fixed): 5% / PATH C-suspicious: 5% / PATH E: 95% (co-firing with PATH A or PATH C). The PATH C-clean (band miss) 10% probability ANTICIPATED the post-hoc input-granularity risk — but underweighted it. It fired at 100%.

**Spec (locked in brief Section 0.5; setup commit SHA `fc8ee98`):**
- ITERATION_LABEL = "v3-056"
- V3_FEATURE_COLUMNS_TOP_N = 14 features UNCHANGED from /055
- V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols UNCHANGED
- enable_per_symbol_drawdown_brake = False UNCHANGED
- REQUIRED_GAP = 66 UNCHANGED
- regime_momentum_signed_5d PRESERVED
- **AXIS CHANGE**: `run_baseline_v3.py:2181-2196` rewritten — `cpcv_path_sharpe_q75 = float(np.percentile(flat_path_sharpes, 75)) if len(flat_path_sharpes) >= 4 else 0.0` (in-memory, not file-read)
- **6th integration test** in `tests/strategies/ml/test_validation_v3_psr_relative.py` mirroring runner's post-fix code path
- Runner: `uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof`
- ENSEMBLE_SIZE = 5 (auto inner); outer_seeds = 1 (EXPLORATION-spec)
- Total Optuna trials: 525 = 3 syms × 5 inner × 35

## Headline Numbers

### Single-seed primary (comparison.csv + seed_summary.json; seed 42 only)

| Metric | iter-v3/028 BASELINE (multi-seed mean) | iter-v3/055 (1-seed) | **iter-v3/056 (1-seed)** | Δ vs /055 | Δ vs /028 (single-seed=42) |
|---|---:|---:|---:|---:|---:|
| **IS monthly Sharpe** | +0.5101 | +0.5101 | **+0.5101** | **+0.0000** | **+0.0000 (BIT-IDENTICAL)** |
| **OOS monthly Sharpe** | +0.5053 | +0.5053 | **+0.5053** | **+0.0000** | **+0.0000 (BIT-IDENTICAL)** |
| IS daily Sharpe | — | +1.3383 | **+1.3383** | 0.0000 | — |
| OOS daily Sharpe | — | +1.0340 | **+1.0340** | 0.0000 | — |
| IS-OOS daily ratio | 0.99 | 1.295 (in-band) | **1.295 (in-band)** | 0.0000 | within [0.5, 2.0] |
| IS Trades | 156 (mean) | 182 | **182** | 0 | +26 vs mean (bit-identical to seed=42) |
| OOS Trades | 95 (mean) | 96 | **96** | 0 | +1 vs mean (bit-identical to seed=42) |
| IS MaxDD | 41.43% | 41.43% | **41.43%** | 0.0 | identical |
| OOS MaxDD | 23.53% | 22.97% | **22.97%** | 0.0 | -0.56pp better |
| OOS Calmar | 0.92 | 0.7159 | **0.7159** | 0.0000 | -0.20 |
| profit_factor OOS | — | 1.1451 | **1.1451** | 0.0000 | — |
| **DSR (legacy)** | 0.0 (structural) | 0.0 (structural) | **0.0** (structural at n_trials=525) | 0.0 | identical |
| **DSR_relative** | n/a | **1.0 (BUG)** | **0.0044 (FIXED; FAIL vs 0.95)** | **bug FIXED** | new field operative |
| **cpcv_path_sharpe_q75** | n/a | **0.0 (BUG)** | **0.8378 (FIXED)** | **bug FIXED** | new field operative |
| PBO | 0.1243 | 0.1243 | **0.1243** | 0.0000 | identical |
| PSR (legacy) | 1.0 | 1.0 | **1.0** | 0.0000 | identical |
| frac_positive_paths | 0.644 | 0.644 | **0.644** | identical | identical |
| Median path Sharpe | +0.335 | +0.3351 | **+0.3351** | identical (4 dp) | identical (4 dp) |
| Q75 path Sharpe | — | +0.838 | **+0.838** | identical (4 dp) | identical (4 dp) |
| Q25 path Sharpe | — | -0.243 | **-0.243** | identical | identical (4 dp) |
| n_trials | 1050 | 525 | **525** | identical | EXPLORATION spec |
| n_eff | 19 | 19 | **19** | identical | identical (CYCLE-4 CONSTANT) |

**Critical observation #1 (BUG FIX LANDED):** The /055 write-before-read defect is GONE. `cpcv_path_sharpe_q75 = 0.837759` (matches the correct percentile to 4 decimals; not 0.0); `dsr_relative = 0.004399` (non-degenerate; not 1.0 ≡ psr). Run-log confirms `[dsr_relative] CPCV path Q75 Sharpe = 0.8378 (from 45 in-memory paths)` — the in-memory branch fires, not the fallback. Critic Check 8 verified at runtime: `grep -q "cpcv_paths_csv = REPORTS_DIR" run_baseline_v3.py` returns ZERO MATCHES (the /055 BUG signature is eliminated). 6 integration test functions in `test_validation_v3_psr_relative.py` (5 unit + 1 new integration at line 118 mirroring runner's exact post-fix code path) PASS.

**Critical observation #2 (PATH C-clean BAND MISS):** Brief predicted DSR_relative OOS in [0.50, 0.65] (centered on /055 Engineer post-hoc 0.5798). Observed DSR_relative = 0.0044. Delta: **-0.58 below band**. The gate IS wired correctly; the band was mis-specified at /055 post-hoc time. Root cause is methodological, not implementation: see "Why EXPLORATION-NEGATIVE" below.

**Critical observation #3 (BIT-IDENTITY to /055 = /028):** /056 reproduces /055 single-seed=42 strategy EXACTLY at every numerical metric: IS monthly Sharpe +0.5101, OOS monthly Sharpe +0.5053, IS 182 trades, OOS 96 trades, per-symbol IS+OOS attribution (BCH 86/36, TRX 85/46, LDO 11/14) to 4 decimal places. The bug fix was localized to post-hoc DSR_relative computation; no path through trade-generation, signal-emission, or feature-engineering was touched. This is the expected secondary hypothesis outcome.

**Critical observation #4 (PATH E firing — 6th consecutive bit-identical CPCV):** CPCV stats 29/45 positive, median +0.3351, Q25 -0.243, Q75 +0.838 — bit-identical to /051/052/053/054/055 to 4 decimals. PATH E pre-registered at 95% in brief Section 8 fired exactly. Methodology-only axes cannot shift CPCV by construction. **The 6-iteration invariance is now the strongest possible evidence that the (BCH+LDO+TRX, 8h, 14-feature stack, ENSEMBLE_SIZE=5, n_trials=35) tuple anchors the CPCV path-Sharpe distribution as a structural constant invariant to ALL axes tested in cycle 4.**

### Per-symbol decomposition (seed 42; bit-identical to /055 and /028)

**IS per-symbol (182 IS trades):**

| Symbol | trades | win_rate | net_pnl_pct | pct_of_total_IS_pnl |
|---|---:|---:|---:|---:|
| BCHUSDT | 86 | 43.0% | +67.59% | +84.03% |
| TRXUSDT | 85 | 35.3% | +7.40% | +9.20% |
| LDOUSDT | 11 | 36.4% | +5.45% | +6.77% |

**OOS per-symbol (96 OOS trades):**

| Symbol | trades | win_rate | weighted_pnl | concentration_pct |
|---|---:|---:|---:|---:|
| BCHUSDT | 36 | 38.9% | +8.5797 | +52.16% |
| LDOUSDT | 14 | 21.4% | -22.0502 | -134.07% |
| TRXUSDT | 46 | 54.3% | +29.9178 | +181.90% |

Bit-identical to /055 and /028 single-seed=42 to 4 decimal places. weighted_pnl_total spot-check (8.5797 - 22.0502 + 29.9178 = 16.4473) reconciles to comparison.csv OOS total_pnl (16.4473) — Critic Check 7 PASS.

### §8 Pre-registered Path Verdict (mechanical, non-renegotiable)

| Path | Trigger | Observed | Fired? |
|---|---|---|---|
| PATH A (PROMISING-clean) | All bands hold incl. DSR_relative OOS in [0.50, 0.65] AND cpcv_path_sharpe_q75 = 0.8378 ± 0.005 | All conditions hold EXCEPT DSR_relative OOS = 0.0044 (-0.58 below band) | NO — band miss |
| PATH B (PROMISING-INERT) | N/A for methodology axes | — | NO |
| **PATH C-clean (DSR_relative out-of-band)** | DSR_relative OOS outside [0.50, 0.65] | 0.0044 (delta -0.58) | **YES — PRIMARY** |
| PATH C-clean (bug fix not landed) | cpcv_path_sharpe_q75 = 0.0 OR dsr_relative = psr | q75 = 0.8378; dsr_relative = 0.0044 ≠ psr = 1.0 | NO — bug fix LANDED |
| PATH C-clean (strategy unintentionally changed) | IS/OOS Sharpe Δ vs /055 > ±0.05 | Bit-identical to /055 | NO |
| PATH C-suspicious | IS-OOS daily ratio outside [0.5, 2.0] | 1.295 within band | NO |
| Saturation falsifier | Strategy roster perturbation observed | Bit-identical to /055 trade roster | NO |
| **PATH E (CPCV-INVARIANT NULL)** | CPCV stats bit-identical to /051-/055 | 29/45 ✓; +0.3351 ✓; -0.243 ✓; +0.838 ✓ | **YES — 6th consecutive** |

**Primary classification: PATH C-clean (band miss; predicted band recalibration based on wrong-granularity input). Co-firing: PATH E (CPCV-INVARIANT NULL on strategy substrate; 6th consecutive).**

## Why EXPLORATION-NEGATIVE — Post-Hoc Input Granularity Mismatch

### The bug fix IS correct

The /055 write-before-read defect is gone:
- Verified at `run_baseline_v3.py:2183-2188`: in-memory `flat_path_sharpes` access, not file-read
- /055 BUG signature `cpcv_paths_csv = REPORTS_DIR` returns ZERO MATCHES
- `dsr.json` contains non-degenerate `cpcv_path_sharpe_q75 = 0.837759` AND `dsr_relative = 0.004399`
- 6 integration tests PASS (5 unit + 1 new integration mirroring runner's post-fix code path)

The gate is **operative**. It evaluates. It produces a non-degenerate value. The reformulation works mechanically as designed.

### The band was wrong, not the gate

The /055 Engineering report SHA `6dc8256` computed a post-hoc estimate of DSR_relative = 0.5798 to recalibrate the /056 brief Section 8 PATH A band [0.50, 0.65]. That post-hoc estimate plugged `raw_sharpe_oos = 0.8591` into `psr()` — the **annualized daily Sharpe** computed from `mean(daily_returns) / std(daily_returns) * sqrt(252)` over 88 daily observations.

But `validation_v3.py:psr()` is called from `run_baseline_v3.py` with `raw_sharpe_oos = mean(oos_wp) / std(oos_wp) * sqrt(len(oos_wp))` — the **trade-level Sharpe** computed over 96 OOS trade weighted-PnL values. For cycle-4's baseline:
- mean(oos_wp) ≈ 16.4473 / 96 ≈ 0.171
- Resulting trade-level raw_sharpe_oos ≈ **0.55**

Plugging the correct input into the gate:

```
z = (0.55 - 0.8378) / sqrt((1 - 0 + (3-1)/4 × 0.55²) / 95) ≈ -0.288 / 0.110 = -2.62
DSR_relative = Phi(-2.62) = 0.0044
```

This matches the observed 0.0044 to 4 decimal places. The post-hoc estimate was off by ~130× in PSR space because of input-granularity mismatch:

| Sharpe variant | Aggregation | n_obs | Value | Used by |
|---|---|---:|---:|---|
| Daily Sharpe (annualized) | time-series, 8h bars | 252 equivalent | 0.8591 | /055 post-hoc (WRONG input) |
| **Trade-level Sharpe** | **per-trade weighted_pnl** | **96 trades** | **~0.55** | **psr() runner call-site (CORRECT)** |

The post-hoc prediction was wrong, not the gate implementation.

### A2 axis substantively CLOSED for cycle 4

At v3 single-seed EXPLORATION with n_trades=96, trade-level SR ≈ 0.55, CPCV Q75 = 0.838, the gate FAILS at 0.0044 — correct discrimination behavior. **But indistinguishable from legacy DSR = 0 in informational content.** EDA `synthesis.md` (SHA `a71b2e5`) Section R5 established that only /039 OOS (+1.573) and /052 OOS (+1.385; PATH C-suspicious) PASS R5 across 13 v3 IS+OOS splits — both high-OOS-Sharpe iterations. **Cycle-4 baseline at SR ≈ 0.55 sits in the FAIL region structurally. No methodology reformulation rescues this at single-seed EXPLORATION scale.**

The R5 gate at EXPLORATION-spec is effectively a **binary step function**:
- Strategy materially beats CPCV Q75 (SR > 0.84): DSR_relative ≈ 1.0
- Strategy does NOT beat CPCV Q75 (SR < 0.84): DSR_relative ≈ 0.004

At single-seed EXPLORATION with n_trades=96 and n_eff=19, the gate provides the same binary information as "did OOS trade-level Sharpe beat Q75 = 0.84?" — readable directly from comparison.csv. **The axis is substantively closed.** The gate may provide more graduation at iter-v3/061 CONFIRMATION (multi-seed, n_trials=1500) IF a bundle produces an OOS iteration that genuinely beats the CPCV Q75. Until then, no further A2 EXPLORATION is justified.

### PATH E firing — 6th consecutive CPCV bit-identical iteration

Six consecutive cycle-4 EXPLORATIONs (/051-/056) produce bit-identical CPCV distributions: 29/45 positive, median +0.3351, Q25 -0.243, Q75 +0.838 (to 4 decimal places). Methodology-only changes (DSR_relative wiring at /055 + /056), risk-gate primitive additions/disables (drawdown brake /054), feature swap/add/drop (fracdiff /051, regime_momentum_3d /052, hurst_drift /053+/054 revert), and post-hoc computation extensions ALL leave the CPCV invariant at single-seed EXPLORATION-spec. **The CPCV path-Sharpe distribution is anchored EXCLUSIVELY by the (base 14-feature stack × walk-forward schedule × model architecture × ENSEMBLE_SIZE × seed) tuple, INVARIANT to ANY axis that does not directly perturb that tuple.**

Cycle-5 axes (iter-v3/062-/071) must change at least one of: base 14-feature stack composition (≥3-feature delta) / universe (3-sym → 4+) / model architecture / n_trials / ENSEMBLE_SIZE to break the determinism. Per `feedback_v3_mass_feature_expansion.md` queued for /062, cycle 5 should combine multiple structural shifts simultaneously.

## Memory Rule Updates

### NEW (orchestrator-applied at Critic FINAL SHA `677acc0`)

- **`feedback_v3_methodology_post_hoc_input_traceback.md` CREATED 2026-05-12** — Establishes: For ALL methodology-axis briefs (DSR/PSR variants, new derived metrics, gate threshold recalibrations) that pre-register Section 8 PATH A trigger bands based on post-hoc computations, the brief Section 8 band specification subsection MUST trace each gate input variable to its exact runner code path (file:line where set) AND specify granularity (per-trade vs per-day vs annualized). If a statistic exists at multiple granularities, the brief MUST state which the gate function consumes. The /055-Engineer-/056-brief chain failed exactly here: post-hoc plugged annualized daily SR into psr() but runner uses trade-level SR; 130× error in PSR space. Phase 5.5 gate enforcement: methodology-axis briefs without input-granularity traceback per gate input variable = BLOCK at gate. Sister rule to `feedback_v3_methodology_axis_integration_test.md` (integration test coverage at runner call-site) — both address the runner-call-site boundary where math correctness ≠ semantic correctness.

### Carried forward / referenced

- **`feedback_v3_methodology_axis_integration_test.md` FIRED at /056** — created at /055 closeout; mandate satisfied at /056 brief Section 9 Pre-flight checklist + 6th integration test addition at `tests/strategies/ml/test_validation_v3_psr_relative.py:line 118`. Phase 5.5 gate verified the integration test exercises runner's exact post-fix code path; gate PASSED.
- **`feedback_v3_no_cheating.md` ENFORCED** — re-run after observing 0.0044 vs predicted [0.50, 0.65] is FORBIDDEN; /056 verdict is final on artifact at SHA `fc8ee98`.
- **`feedback_v3_oracle_eda_validity.md` UNCHANGED** at /056 — applies to STATEFUL gate axes; /056 axis classified STATELESS (DSR_relative is per-cell post-hoc computation; no signal-emission feedback) per brief Section 10.2 — rule satisfied trivially.
- **`feedback_v3_axis_selection_quant_discipline.md` fired at /056** — QR EDA at SHA `a71b2e5` REUSED from /055 (theoretical basis unchanged; only implementation needed fix). Critic FINAL Adversarial Finding #4 confirmed the methodology axis is sound.
- **`feedback_v3_strict_10_to_1_cadence.md` advances 6/10** for cycle 4. iter-v3/056 is cycle 4 #6; 4 more EXPLORATIONs needed before iter-v3/061 CONFIRMATION.
- **`feedback_v3_dsr_mode_artifact.md` REFERENCED** — DSR_relative at single-seed EXPLORATION confirmed as binary step function (≈1.0 if beats CPCV Q75, ≈0.0044 if not) per /056 observation. Per the rule's "EXPLORATION-mode DSR/PSR are regime-specific artifacts" precedent, DSR_relative at /056 EXPLORATION-spec is INFORMATIONAL ONLY — gate will operationally evaluate at iter-v3/061 CONFIRMATION (multi-seed, n_trials=1500).
- **`feedback_v3_concentration_is_signal.md` UNCHANGED** at /056 — per-symbol drawdown brake DISABLED architecturally per /054 closeout; CLOSED in PRINCIPLE.
- **`feedback_v3_structural_over_knob_exploration.md` REFERENCED** — methodology axis ranked Category 5+ (gate-threshold interpretation; not primary structural axis). /056 axis acknowledged at /055 closeout as ≤2h methodology-only contribution to cycle-4 CONFIRMATION viability, NOT a CPCV-shifting axis. PATH E firing 6/6 cycle-4 EXPLORATIONs confirms the rule.
- **`feedback_risk_mitigation_design.md` REFERENCED** — brief Section 5 included methodology-axis risk profile + simulated historical effect across 13 prior iterations; mandate satisfied.
- **`feedback_axis_saturation_predictor.md` PARTIALLY FIRED** — brief Section 4.4 included behavioral effect predictor (predicted ZERO trade roster perturbation; observed ZERO perturbation BIT-IDENTICAL to /055 = /028 single-seed=42). Saturation falsifier did NOT fire (strategy clean).
- **`feedback_v3_mass_feature_expansion.md` queued for /062** — cycle-5 structural shift mandate stands per PATH E 6th-consecutive firing.

## Cycle 4 Cadence: 6/10 EXPLORATIONs Advanced

Per `feedback_v3_strict_10_to_1_cadence.md`:

- **Cycle 4 #1 of 10 = iter-v3/051** (fracdiff_d05_close ADD UNIVERSAL; EXPLORATION-NULL-RESULT PATH D; PARKED)
- **Cycle 4 #2 of 10 = iter-v3/052** (regime_momentum_signed_3d SWAP UNIVERSAL; EXPLORATION-NEGATIVE PATH C-suspicious; CLOSED)
- **Cycle 4 #3 of 10 = iter-v3/053** (hurst_drift_50_200 SWAP UNIVERSAL; EXPLORATION-NULL-RESULT PATH D; PARKED — LR-PF methodology refined)
- **Cycle 4 #4 of 10 = iter-v3/054** (per-symbol drawdown brake NEW RiskV2 primitive 11 + REVERT hurst_drift; EXPLORATION-NEGATIVE PATH C-clean + PATH C-suspicious + Saturation + PATH E; brake axis CLOSED + entire "NEW risk primitive" axis family CLOSED at single-seed EXPLORATION; ORACLE EDA methodology defect; `feedback_v3_oracle_eda_validity.md` CREATED)
- **Cycle 4 #5 of 10 = iter-v3/055** (A2 DSR gate reformulation methodology-only; EXPLORATION-NEGATIVE PATH C-clean on DSR_relative bug + PATH E 5th consecutive; A2 axis methodologically sound but implementation broken at integration boundary; carry-forward to /056 with 2-line fix; `feedback_v3_methodology_axis_integration_test.md` CREATED)
- **Cycle 4 #6 of 10 = iter-v3/056** (THIS — A2 DSR gate reformulation CARRY-FORWARD with bug fix; **EXPLORATION-NEGATIVE PATH C-clean band miss + PATH E 6th consecutive**; bug fix landed correctly but predicted band based on wrong-granularity input; A2 axis substantively CLOSED at cycle 4; `feedback_v3_methodology_post_hoc_input_traceback.md` CREATED)
- **Cycle 4 #7-#10 = iter-v3/057-iter-v3/060** (TBD — /057 axis: A4 base-stack reordering OR NEW feature family per QR EDA-driven choice)
- **Cycle 4 CONFIRMATION at iter-v3/061** (SEPARATE single-seed iter-v3/060 first; do NOT collapse the 10th EXPLORATION into CONFIRMATION per `feedback_v3_strict_10_to_1_cadence.md`)
- **4 more EXPLORATIONs remain** before cycle 4 CONFIRMATION: iter-v3/057 through iter-v3/060
- **Cadence wall-clock caps**: EXPLORATION 2h, CONFIRMATION 6h. iter-v3/056 actual: ~2.0h backtest within 2h cap (concurrent with other runs).

**Cycle 4 cumulative score: 0 PROMISING-clean / 1 PROMISING-INERT (N/A risk primitives) / 2 NULL-RESULT / 3 NEGATIVE / 0 axes-advance after 6 of 10 EXPLORATIONs.** The structural finding (CPCV-determinism + n_eff=19 + integration-test methodology rule + post-hoc input-traceback methodology rule) remains the primary cycle-4 contribution; NO axis has advanced. PATH E 6-consecutive firing forces cycle-5 mass feature expansion at iter-v3/062.

## iter-v3/057 PROMOTED Axis

Per Critic FINAL `677acc0` Recommendation #1 + Engineering report Section "Recommendations to QR for /057":

### A2 DSR reformulation: SUBSTANTIVELY CLOSED for cycle 4

The R5 reformulation is mechanically correct, theoretically rigorous (Bailey-LdP 2014 + AFML Ch. 14), and now correctly wired after the /056 bug fix. But at v3 single-seed EXPLORATION regime (n_trades=96, trade-level SR ≈ 0.55, CPCV Q75 = 0.838 → PSR z = -2.62 → Phi(-2.62) = 0.0044), the gate produces values indistinguishable from legacy DSR = 0.0. No further A2 EXPLORATION is justified until iter-v3/061 CONFIRMATION evaluates the reformulated gate at multi-seed (n_trials=1500) — IF a bundle produces an OOS iteration that genuinely beats the CPCV Q75.

### PROMOTED for /057: A4 base-stack reordering OR NEW feature family (QR EDA-driven choice)

**Option 1 — A4 base-stack feature reordering:**
- Remove the weakest base-stack feature (by importance rank) and evaluate IS/OOS sensitivity
- Only remaining viable cycle-4 structural axis that has not been tested
- EDA required at brief Section 2: per-feature drop-one importance/IC/ADF analysis on the 14-feature stack (already partially available from /051-/056 adf_test.csv and ic_matrix.csv)
- Identify bottom-1 or bottom-2 candidates for removal
- Conservative — addresses cycle-4 structural finding marginally; would NOT shift CPCV by ≥3-feature delta

**Option 2 — NEW feature family (HIGH priority per cycle-4 axis priorities):**
- Pivot to NEW structural feature family (OI, funding rates at different lookback, basis, alternative microstructure)
- Priority-1 axis in post-/050 roadmap; was preempted by A2 DSR work
- EDA required: candidate feature definition + univariate IC + cluster-IC against base-14 + ADF stationarity check
- Bold — would advance toward cycle-5 mass feature expansion mandate (`feedback_v3_mass_feature_expansion.md`); still constrained to 14 → 15 features at /057 EXPLORATION (single-axis)

**Decision criterion for /057 QR brief:** Per `feedback_v3_axis_selection_quant_discipline.md`, QR must produce committed `analysis/iteration_v3-057/*.py` EDA with numerical 2-option ranking BEFORE locking brief Section 1 axis. Orchestrator may suggest but cannot commit setup without QR backing. Brief Section 10 must include rationale for the choice.

**Why A2 is NOT carry-forward:** The mechanical and theoretical correctness of R5 is now established. The gate evaluates. It produces non-degenerate values. The signal is absent in the trade distribution at v3's single-seed EXPLORATION regime, not the gate mechanics. Further A2 carry-forward would require either: (a) a structural axis that lifts trade-level SR above CPCV Q75, OR (b) waiting for /061 CONFIRMATION multi-seed evaluation. (a) is what A4/NEW feature axis attempts at /057. (b) is the appointed evaluation venue.

**Cycle-5 (iter-v3/062-/071) preview:** Per PATH E 6-consecutive firing, cycle-5 axes MUST combine structural shifts to break CPCV determinism: base 14-feature stack composition (≥3-feature delta) AND/OR universe (3-sym → 4+) AND/OR model architecture AND/OR n_trials AND/OR ENSEMBLE_SIZE. Per `feedback_v3_mass_feature_expansion.md` queued at /062, mass feature expansion (≥5-feature delta) is the structural shift needed.
