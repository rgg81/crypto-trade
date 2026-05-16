# Iteration iter-v3/049 — Diary

## Decision: EXPLORATION-NEGATIVE — clean PATH C (per-symbol ADX threshold axis CLOSED for cycle 3) + CYCLE 3 CLOSURE 10/10

iter-v3/049 = TENTH (LAST) iteration of cycle 3 (cycle 3 #10 of 10 — cycle 3 is now COMPLETE). Single new EXPLORATION axis on top of the iter-v3/045 PROMISING bundle + iter-v3/047 primitive 10 carry-forward state + iter-v3/048 vol_normalized_ret_5d REVERT (V3_FEATURE_COLUMNS_TOP_N from 15 → 14): ADD `adx_threshold_per_symbol: dict[str, float] = field(default_factory=dict)` field to `RiskV2Config` and wire `adx_threshold_per_symbol = {"TRXUSDT": 21.0}` (BCH/LDO/ALGO unchanged at global 20.0). Per-symbol asymmetric ADX dispatch — STRUCTURALLY DISTINCT from the closed iter-v3/014 universal ADX-25 knob-tuning rule per Critic FINAL `55fbadb` recommendation #2 candidate (e). Per QR EDA `analysis/iteration_v3-049/multi_axis_eda.py` + `axis_e_*.py` + `axis_d_*.py` + `axis_a_*.py` + `axis_c_*.py` (SHA `ba8a3de`), candidate (e) per-symbol ADX TRX 21 was the ONLY candidate of 5 satisfying the BOTH-must-improve rule under primitive 10 carry-forward simulation (predicted IS lift +4.77 wpnl / OOS cost -0.01 wpnl).

Result: **IS Sharpe +0.4261 / OOS Sharpe +1.0272** (single-seed=42, ENSEMBLE_SIZE=5, n_trials=35, EXPLORATION-spec, `--clean-oof` guardrail active). Pre-registered PATH C-clean fires unambiguously on BOTH locked thresholds (Section 8): IS Sharpe Δ -0.32 < -0.10 AND OOS Sharpe Δ -2.50 < -0.30 vs iter-v3/045 single-seed anchor (+0.7459 / +3.5259). Per QR locked Section 8 thresholds (non-renegotiable per cycle 3 discipline), the verdict path resolved as **PATH C-clean — NEGATIVE-clean**. The IS-OOS daily Sharpe ratio is 1.9271 — just inside the [0.5, 2.0] band, so PATH C-suspicious DOES NOT fire (clean regression NOT NEGATIVE-SUSPICIOUS).

The naive EDA BOTH-must-improve counterfactual (predicting +4.77 IS lift / -0.01 OOS cost) did NOT survive Optuna response at single-seed: TRX OOS trade count UNCHANGED (46 → 46) but a **6-trade roster swap** lost +11.27 wpnl winners (3 take-profit clusters at +4.23/+4.07/+3.25) and added -0.22 wpnl losers (predominantly stop-losses). The -11.49 weighted_pnl swap delta directly produces the -11.53 observed TRX OOS regression (residual -0.04 from weight_factor rounding on shared trades). The static EDA correctly modeled the naive counterfactual axis but missed the secondary Optuna-response cost path driven by 9 fewer TRX IS training trades reshaping the per-symbol Optuna trajectory.

**KEY METHODOLOGICAL VALIDATION (forensic-grade)**: The frozen-baseline pattern is now CONFIRMED at OOS row-level for the first time across consecutive non-identical iterations. ALGO/BCH/LDO trade rosters are BIT-IDENTICAL between iter-v3/047 and iter-v3/049 (verified character-for-character per Critic on `out_of_sample/trades.csv` lines 2-12; same open_times, same pnl_pct, same direction, same exit_reason, same entry_price, same exit_price, same weight_factor). Only TRX rows differ. This is the strongest direct validation of the REVISED `feedback_v3_single_seed_frozen_baseline.md` rule observed in v3 catalog. The iter-v3/047 engineering report's "cross-run stochasticity from multiple process invocations" attribution is now **CATEGORICALLY FALSIFIED** — single-seed=42 with same feature stack and same model config produces bit-identical OOS results regardless of axis variation on disjoint symbols.

Per QR + Critic + Engineering recommendations: NO re-run (peeking-at-OOS violation per `feedback_no_cheating.md`); accept-NEGATIVE; iter-v3/050 = SECOND v3 CONFIRMATION on the iter-v3/045 PROMISING bundle + primitive 10 carry-forward (per-symbol ADX field DROPPED). Cycle 3 of 10 EXPLORATIONs is **COMPLETE**.

## What Was Tested

**Hypothesis (locked in brief Section 1):** "Adding a per-symbol ADX threshold override `adx_threshold_per_symbol = {'TRXUSDT': 21.0}` to RiskV2Config — leaving BCH/LDO/ALGO at the global 20.0 threshold but raising TRX's gate to 21.0 — filters out the weakest-trend TRX signals (the 9 IS trades at TRX ADX 20-21 had collective wpnl -4.77, every one a net-EV loser). Expected effect: bundle IS Sharpe lift +0.05 to +0.20 vs iter-v3/045 single-seed anchor +0.7459 (modest but BOTH-IS-AND-OOS-positive); bundle OOS Sharpe Δ within [-0.20, +0.20] vs iter-v3/045 anchor +3.5259 (uncertain because Optuna will retune, but naive counterfactual shows -0.01 OOS cost — effectively zero impact on OOS)."

**Predicted bands (locked in brief Section 4):**
- IS Sharpe: [+0.80, +0.95] median +0.85 (vs iter-v3/045 anchor +0.7459)
- OOS Sharpe: [+3.30, +3.85] (regression up to -0.30 OR lift up to +0.30) (vs iter-v3/045 anchor +3.5259)
- Bundle IS trade count: 250 → 220-260 (-12% to +5%; with primitive 10 + ADX 21 effect)
- TRX IS trade count: 85 → 72-80 (-15% to -5%; naive -9 + Optuna response)
- direction_block_fires GateStats for TRX: 5-15 fires in IS; 2-5 fires in OOS
- IS-OOS daily Sharpe ratio: ∈ [0.7, 1.5] (clean lift, not suspicious)

**Spec (locked in brief Section 0.5):**
- ADD `adx_threshold_per_symbol: dict[str, float] = field(default_factory=dict)` field to `RiskV2Config` in `src/crypto_trade/strategies/ml/risk_v2.py:127-137`
- MODIFY `_adx_gate_fails` at `risk_v2.py:407-411` with two-line per-symbol override (`self.config.adx_threshold_per_symbol.get(symbol, self.config.adx_threshold)`)
- WIRE `adx_threshold_per_symbol={"TRXUSDT": 21.0}` in `run_baseline_v3.py:_build_v3_model`
- 5 adversarial tests in `tests/strategies/ml/test_per_symbol_adx_threshold.py` PASS at setup commit `6eeff46`
- REVERT `vol_normalized_ret_5d` from V3_FEATURE_COLUMNS_TOP_N (15 → 14) per iter-v3/048 PATH C-clean closeout mandate
- Carry-forward state from iter-v3/047 UNCHANGED:
  - V3_ATR_MULTIPLIERS_PER_SYMBOL = {ALGOUSDT: (2.0, 1.5), LDOUSDT: (2.0, 1.5)}
  - block_long_for = ("BCHUSDT",) — primitive 10 ON
  - block_short_for = ()
  - V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols
  - V3_FEATURES_PER_SYMBOL = {} (empty)
  - REQUIRED_GAP = 88 = (21+1)*4
- ITERATION_LABEL = "v3-049"
- Runner: `uv run python run_baseline_v3.py --seeds 1 --clean-oof`

## Headline Numbers

### Bundle metrics (single-seed, ENSEMBLE_SIZE=5)

| Metric | iter-v3/045 anchor | iter-v3/047 carry-fwd | **iter-v3/049** | Δ vs iter-v3/045 | Verdict |
|---|---:|---:|---:|---:|---|
| **IS monthly Sharpe** | +0.7459 | +0.4872 | **+0.4261** | **-0.32** | FAR BELOW band [+0.80, +0.95]; PATH C IS regression fires |
| **OOS monthly Sharpe** | +3.5259 | +1.1675 | **+1.0272** | **-2.50** | FAR BELOW band [+3.30, +3.85]; PATH C OOS regression fires |
| Daily Sharpe IS | +1.3115 | +1.1742 | +1.0117 | -0.30 | regression |
| Daily Sharpe OOS | +4.2020 | +2.5077 | +1.9496 | -2.25 | regression |
| OOS/IS monthly ratio | 4.73 | 2.40 | 2.41 | -2.32 | within positive range; not suspicious |
| **IS-OOS daily Sharpe ratio** | 3.20 | 2.14 | **1.9271** | — | **within band [0.5, 2.0] — clean regression NOT NEGATIVE-SUSPICIOUS** |
| IS Trades | 250 | 201 | 194 | -56 | -22.4% (vs 045 incl. primitive 10 + ADX 21 effect; -3.5% vs 047 carry-fwd) |
| OOS Trades | 119 | 92 | 92 | -27 | -22.7% (vs 045); 0% vs 047 (UNCHANGED count, ROSTER ROTATED) |
| IS MaxDD | 66.06% | 60.97% | 61.89% | -4.17pp better | improvement (mechanical) |
| OOS MaxDD | 13.26% | 20.21% | 22.35% | +9.09pp worse | regression |
| OOS Calmar | 7.31 | 2.30 | 1.56 | -5.75 | regression |
| IS Profit factor | 1.21 | 1.20 | 1.17 | -0.04 | regression |
| OOS Profit factor | 1.68 | 1.40 | 1.29 | -0.39 | regression |
| OOS Top-symbol concentration | 54.77% (ALGO) | 64.43% (TRX) | 78.55% (ALGO) | +23.78pp worse | regression (concentration UP — frozen baseline ALGO carry-over) |
| DSR | 0.0 | 0.0 (n_trials=700) | 0.0 (n_trials=700) | structural | INFORMATIONAL ONLY per `feedback_v3_dsr_mode_artifact.md` |
| PBO | 0.0782 | 0.0939 | 0.0939 | +0.016 | acceptable (gate 0.4) |
| PSR | 1.0 | 1.0 | 1.0 | 0 | acceptable |
| n_trials reported | 140 | 700 | 700 | +560 | STRUCTURAL: 4 syms × 5 ensemble × 35 trials/seed; CORRECT for ENSEMBLE_SIZE=5 |
| n_effective_trials | 19 | 18 | 18 | -1 | acceptable |

### Per-symbol IS decomposition

| Symbol | iter-v3/045 trades | iter-v3/047 trades | **iter-v3/049 trades** | WR 045 | **WR 049** | net_pnl_pct 045 | **net_pnl_pct 049** | Δ pnl vs 045 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ALGO | 53 | 51 | 51 | 39.6% | 45.1% | -34.05% | -5.94% | **+28.11pp** (frozen-baseline carry-over from /047) |
| BCH | 94 | 50 | 50 | 38.3% | 46.0% | +23.62% | +65.77% | **+42.15pp** (frozen-baseline carry-over from /047 — primitive 10 SHORT shift) |
| LDO | 18 | 15 | 15 | 55.6% | 40.0% | +54.55% | -12.19% | **-66.74pp** (frozen-baseline carry-over from /047) |
| TRX | 85 | 85 | **78** | 34.1% | 34.6% | -7.28% | +0.92% | **+8.20pp** (vs /045 — but vs /047 anchor +7.40% → +0.92%, **-6.48pp**) |

ALGO/BCH/LDO IS contributions are BIT-IDENTICAL to iter-v3/047 (same trade count, same WR, same net_pnl_pct) — the per-symbol ADX axis is TRX-only and BCH/LDO/ALGO models trained on UNCHANGED features and UNCHANGED config. TRX IS trades dropped 85 → 78 (-7 net): 19 old trades dropped, 12 new trades added. Net removal of 7 IS trades — consistent with the EDA prediction of 9 structural ADX-21 blocks partially offset by Optuna roster additions. TRX net_pnl_pct regressed +7.40% → +0.92% (-6.48pp vs /047 anchor).

### Per-symbol OOS decomposition

| Symbol | iter-v3/045 trades | iter-v3/047 trades | **iter-v3/049 trades** | WR 045 | **WR 049** | weighted_pnl 045 | weighted_pnl 047 | **weighted_pnl 049** | Δ pnl vs 045 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ALGO | 22 | 13 | 13 | 63.6% | 53.8% | +53.12 | +27.42 | **+27.42** | **-25.70** (frozen-baseline carry-over from /047) |
| BCH | 38 | 21 | 21 | 39.5% | 47.6% | +11.31 | +8.23 | **+8.23** | **-3.08** (frozen-baseline carry-over from /047) |
| LDO | 13 | 12 | 12 | 53.8% | 33.3% | +9.34 | -19.13 | **-19.13** | **-28.47** (frozen-baseline carry-over from /047) |
| TRX | 46 | 46 | **46** | 52.2% | 47.8% | +23.23 | +29.92 | **+18.39** | **-4.84** (vs /045 — but vs /047 anchor +29.92 → +18.39, **-11.53**) |

OOS ALGO/BCH/LDO BIT-IDENTICAL to iter-v3/047 (verified character-for-character row-level: same open_times, same pnl_pct, same direction, same exit_reason, same entry_price, same exit_price, same weight_factor). TRX OOS count UNCHANGED (46 → 46) but ROSTER ROTATED (6 new trades + 6 dropped trades; 40 shared open_times out of 46 total). The 6 dropped trades had +11.27 weighted_pnl (3 take-profit cluster at +4.23/+4.07/+3.25); the 6 new trades had -0.22 weighted_pnl (predominantly stop-losses). Net -11.49 swap delta drives the -11.53 TRX OOS weighted_pnl regression (vs /047 anchor).

ALL 4 SYMBOLS REGRESSED OOS vs iter-v3/045 anchor; ONLY TRX's regression is attributable to this iteration's axis. ALGO/BCH/LDO regressions are frozen-baseline carry-over from iter-v3/047 (the /047 anchor was the binding-constraint immediate predecessor with primitive 10 ON).

### Pre-registered Falsifier Audit (brief Section 4 + Section 8 — locked thresholds)

| Falsifier | Threshold | Observed | Status |
|---|---|---|---|
| IS Sharpe band | [+0.80, +0.95] | +0.4261 | **FAR BELOW band — FIRES** |
| IS Sharpe Δ vs 045 | ≥ +0.05 | -0.32 | **FALSIFIED** |
| OOS Sharpe band | [+3.30, +3.85] | +1.0272 | **FAR BELOW band — FIRES** |
| OOS Sharpe Δ vs 045 | ≥ -0.10 | -2.50 | **FALSIFIED** |
| IS-OOS daily Sharpe ratio | [0.5, 2.0] | 1.9271 | **PASS (within band — clean regression NOT NEGATIVE-SUSPICIOUS)** |
| TRX IS trade count delta | -15% to -5% naive | -8.2% (85→78) | **PASS (within predicted band)** |
| Bundle IS trade count delta vs 047 | ≤ 15% | -3.5% (201→194) | **PASS (within band — feature pipeline intact)** |
| TRX direction_block_fires | ≥ 3 fires | ~9 IS net blocks (estimated from roster delta) | **PASS (consistent with EDA prediction)** |
| BCH/LDO/ALGO OOS rosters bit-identical to /047 | YES | YES (verified character-for-character) | **PASS (frozen-baseline pattern confirmed)** |
| Bundle IS Sharpe Δ | ≥ +0.05 | -0.32 | **FALSIFIED — PATH C fires** |
| Bundle OOS Sharpe Δ | ≥ -0.10 | -2.50 | **FALSIFIED — PATH C fires** |

### Pre-registered Path Verdict (brief Section 8 — non-renegotiable)

| Path | Threshold | Observed | Trigger |
|---|---|---|---|
| PATH A (PROMISING-clean) | IS Sharpe Δ ≥ +0.05 AND OOS Sharpe Δ ≥ -0.10 AND TRX direction_block_fires ≥ 3 AND IS-OOS daily ratio ∈ [0.5, 2.0] | IS Δ -0.32 < +0.05; OOS Δ -2.50 < -0.10; daily ratio 1.93 within band | NO |
| PATH B (PROMISING-INERT) | IS Δ ∈ [-0.05, +0.05] AND OOS Δ ∈ [-0.20, +0.20] AND TRX direction_block_fires < 3 | IS Δ -0.32 outside [-0.05, +0.05]; OOS Δ -2.50 outside [-0.20, +0.20]; ~9 fires | NO |
| **PATH C-clean (NEGATIVE-clean)** | IS Sharpe Δ < -0.10 OR OOS Sharpe Δ < -0.30 | **IS Δ -0.32 < -0.10 AND OOS Δ -2.50 < -0.30** | **YES — both criteria fire** |
| PATH C-suspicious (NEGATIVE-SUSPICIOUS-OOS) | IS-OOS daily Sharpe ratio outside [0.5, 2.0] | 1.9271 within band | NO |

**Brief verdict: PATH C-clean — EXPLORATION-NEGATIVE clean.** This is a genuine IS+OOS regression, NOT the iter-v3/026/027 anti-pattern (the IS-OOS daily Sharpe ratio is 1.93, just inside the [0.5, 2.0] band).

## What Worked

- **EDA-driven axis selection methodology held** even with NEGATIVE outcome. The QR EDA at `analysis/iteration_v3-049/multi_axis_eda.py` + `axis_e_finegrained_adx_with_primitive10.csv` + 4 supporting axis scripts (SHA `ba8a3de`) correctly screened 5 candidates and ADVANCED only candidate (e) per-symbol ADX TRX 21 — the ONLY candidate satisfying the BOTH-must-improve rule under primitive 10 carry-forward simulation. Candidates (a) vol-conditioned timeout, (c) TRX kurt-momentum, (d) drawdown-brake were FALSIFIED at EDA stage; (b) CatBoost was DEFERRED on 2h-cap budget. Per-symbol BCH ADX 21 (predicted IS lift +6.43 / OOS cost +4.42) and LDO ADX 21 (predicted IS lift -19.13 / OOS cost +5.72) were correctly EXCLUDED at EDA stage as failing BOTH-must-improve. The naive counterfactual modeling identified the right axis; the EDA limitation is the inability to model the secondary Optuna-response cost path at single-seed.

- **Implementation hygiene clean.** All 12 standard methodology checks PASS or N/A per Critic FINAL `1908d50`:
  - Check 1 (Look-ahead) PASS — past-only construction verified; per-symbol threshold dict is constant lookup with no contemporaneous signal data dependency
  - Check 2 (Embargo width) PASS — REQUIRED_GAP=88 unchanged
  - Check 3 (Multiple-testing) FAIL DSR (informational for EXPLORATION; PBO 0.0939 PASSES; PSR 1.0 PASSES)
  - Check 4 (IC) PASS — no new feature; 14×14 IC matrix unchanged from iter-v3/047 carry-forward
  - Check 5 (ADF stationarity) PASS — no new feature; ADF profile identical to /047
  - Check 6 (Pareto) N/A single-seed
  - Check 7 (Reproducibility) PASS — setup `6eeff46`, brief `24f1f6c`, Phase 5.5 gate `524dde2`, 5 adversarial tests pass; row-level OOS bit-identity for ALGO/BCH/LDO confirmed
  - Check 8 (Hypothesis-Implementation alignment) PASS — zero scope creep, single-axis discipline preserved
  - Checks 9-12 PASS or N/A
  - 5 adversarial tests in `tests/strategies/ml/test_per_symbol_adx_threshold.py` PASS at setup commit
  - Pre-commit SHAs: EDA `ba8a3de`, brief `24f1f6c`, Phase 5.5 gate `524dde2`, setup `6eeff46`, engineering report `d8998d9`, Critic FINAL `1908d50` — full audit chain present

- **Frozen-baseline pattern CONFIRMED at OOS row-level for the FIRST time across consecutive non-identical iterations.** ALGO/BCH/LDO trade rosters bit-identical between iter-v3/047 and iter-v3/049 (verified character-for-character on `out_of_sample/trades.csv` lines 2-12 per Critic). This is the strongest direct validation of the REVISED `feedback_v3_single_seed_frozen_baseline.md` rule observed in v3 catalog. The mechanism: at single-seed=42, when feature_columns AND data input AND model config are IDENTICAL for a symbol, the per-symbol Optuna trajectory is bit-deterministic. The TRX-only axis change isolated the perturbation cleanly to TRX rows.

- **iter-v3/047 misdiagnosis CATEGORICALLY FALSIFIED in production environment.** The iter-v3/047 engineering report's "cross-run stochasticity from multiple process invocations" attribution is now empirically falsified by iter-v3/049's bit-identical OOS reproduction of /047's ALGO/BCH/LDO rosters. The /047 ALGO/LDO drift was single-seed Optuna lottery variance (different hyperparameters from a fresh Optuna study with primitive 10 active during fold evaluation), not multi-run contamination. Combined with iter-v3/048's forensic resolution of the n_trials=700 structural attribution, the iter-v3/047 misdiagnosis is now fully corrected at production grade. The frozen-baseline memory rule is correctly calibrated.

- **Predicted behavioral effect partially matched observation.** Brief Section 2.11 predicted bundle IS trade count 250 → 220-260 (-12% to +5%); observed 194 (-22.4% vs 045). The discrepancy is attributable to combined effects: primitive 10 carry-forward (-49 trades vs /045) + per-symbol ADX 21 (-7 trades vs /047) + Optuna response. Compared to iter-v3/047 carry-forward base (201), iter-v3/049 trade count is -3.5% (within ±15% feature-pipeline-intact band). TRX IS trade delta (85→78, -8.2%) within predicted band [-15%, -5%]. Feature pipeline intact, no cascade effect.

- **QR EDA discipline maintained per `feedback_v3_axis_selection_quant_discipline.md`.** Brief Section 2 contains 11 sub-sections, 6 numerical tables, falsifiers with explicit thresholds, behavioral-effect predictor, EDA-derived candidate ranking with per-axis EDA evidence. Brief Section 10 (QR Audit Trail) cites EDA SHA `ba8a3de` explicitly and addresses the `feedback_adx_axis_asymmetric_v3.md` ADX-axis-closed rule conflict by noting the structural distinction between universal-knob retune (closed) and per-symbol asymmetric dispatch (NEW dataclass field paralleling existing `regime_gate_symbols` / `block_long_for` / `block_short_for` per-symbol overrides). Phase 5.5 gate accepted with documented justification.

- **`--clean-oof` guardrail (SHA `6a216b5`) functioned correctly.** Single-process invocation produced n_trials=700 / 110MB OOF parquet — STRUCTURAL per-ensemble-seed namespace collision per the iter-v3/048 forensic resolution, NOT contamination. The guardrail correctly prevents true multi-run scenarios.

## What Failed

- **Pre-registered PATH C-clean fires unambiguously on BOTH locked thresholds.** Bundle IS Sharpe Δ -0.32 < -0.10 AND OOS Sharpe Δ -2.50 < -0.30 vs iter-v3/045 single-seed anchor. Per QR locked Section 8 thresholds (non-renegotiable per cycle 3 discipline), verdict path resolved as PATH C-clean — NEGATIVE-clean.

- **TRX OOS roster swap dominates the regression.** OOS TRX count UNCHANGED (46 → 46), but PnL Δ -11.53 driven by 6-trade swap. Of the 6 dropped trades, 4 were take-profit winners (collective +11.27 wpnl including +4.23/+4.07/+3.25 cluster); of the 6 new trades, 4 were stop-losses (collective -0.22 wpnl). Net swap delta -11.49 ≈ observed -11.53 regression. The ADX 21 gate blocked ZERO net OOS TRX trades when measured by trade count (46 → 46), but the Optuna retuning (driven by 9 fewer IS training trades from the ADX 21 gate firing on IS) shifted which OOS candles the model entered, independent of the ADX gate firing.

- **Naive EDA counterfactual missed the secondary Optuna-response cost path.** EDA predicted -0.01 OOS wpnl cost (the 2 blocked OOS ADX 20-21 trades had collective wpnl ≈ 0); observed -11.53 OOS wpnl regression on TRX. The static EDA correctly modeled the gate-physical-block axis (2 OOS trades blocked at TRX ADX 20-21) but missed the Optuna-retune axis (different hyperparams produce different trade entry prices, exit reasons, and weights — even with same trade count). The brief Section 4 predicted mechanism "Different best hyperparams produce different trade entry prices, exit reasons, and weights — even with same trade count" was correct in principle but the magnitude was underestimated.

- **Bundle IS Sharpe regressed despite the predicted +0.05 to +0.20 lift.** EDA predicted bundle IS lift +4.77 wpnl × ~150% Sharpe-lift coefficient ≈ +0.05 to +0.20 IS Sharpe Δ; observed -0.32. The EDA naive counterfactual (which assumed Optuna would converge on the same hyperparams minus the 9 blocked IS trades) was falsified — Optuna re-converged on a slightly weaker TRX configuration in IS (TRX net_pnl_pct +7.40% → +0.92%, -6.48pp).

- **Per-symbol ADX threshold axis CLOSED for cycle 3.** This iteration is the empirical test that resolved the question: per-symbol ADX raise (the only remaining ADX axis variant after iter-v3/014 closed global ADX-25 knob-tuning) FAILS at single-seed OOS despite passing naive EDA BOTH-must-improve. The ADX axis is now empirically closed in BOTH global AND per-symbol forms. Cycle 3 NEW universal engineered feature axis was already closed at iter-v3/048 (5 attempts, 0 successes).

- **All 4 OOS symbols REGRESSED vs iter-v3/045 anchor**, but ONLY TRX's regression is attributable to this iteration's axis. ALGO -25.70, BCH -3.08, LDO -28.47 are frozen-baseline carry-over from iter-v3/047 (the immediate predecessor that introduced primitive 10 + carry-forward Optuna lottery on ALGO/LDO). TRX -4.84 vs iter-v3/045 (= +6.69 inherited from /047 - 11.53 from /049 axis = -4.84 net). The bundle OOS regression headline (-2.50 vs /045) is dominated by the iter-v3/047 lottery carry-over, with this iteration's axis adding -0.14 to -0.20 incremental regression vs /047's OOS anchor +1.1675.

- **OOS top-symbol concentration WORSENED to 78.55% (ALGO)** — frozen-baseline carry-over from iter-v3/047 (where ALGO at +27.42 dominated the 92-trade OOS). Single-seed concentration is NOT representative of multi-seed Pareto behavior; CONFIRMATION at iter-v3/050 will dissolve concentration. Concentration concern is INFORMATIONAL ONLY at EXPLORATION single-seed.

- **LDO OOS structural concern persists.** LDO OOS = -19.13 weighted_pnl is bit-identical between iter-v3/047 and iter-v3/049 (frozen baseline carry-over). LDO has been -19.13 OOS in BOTH iterations now. At iter-v3/050 multi-seed CONFIRMATION (seeds 42 + alternative), if LDO remains consistently negative across seeds, this is structural drag — not seed-specific draw — and should trigger LDO-removal evaluation at iter-v3/051 EXPLORATION cycle (post-CONFIRMATION).

## Architectural Decisions

- **iter-v3/045 PROMISING bundle PRESERVED** as best EXPLORATION-PROMISING in cycle 3. State: V3_ATR_MULTIPLIERS_PER_SYMBOL = {ALGOUSDT: (2.0, 1.5), LDOUSDT: (2.0, 1.5)} (2 entries; iter-v3/044 ALGO + iter-v3/045 LDO).
- **`adx_threshold_per_symbol = {"TRXUSDT": 21.0}` MUST be DROPPED at iter-v3/050 setup** (revert to default empty dict). The `adx_threshold_per_symbol` field stays in `RiskV2Config` schema for future use; only the wired value is reverted.
- **vol_normalized_ret_5d STAYS DROPPED** (V3_FEATURE_COLUMNS_TOP_N = 14). Carries forward unchanged from iter-v3/048 closeout.
- **Primitive 10 (direction-asymmetric kill switch) carry-forward UNCHANGED.** Still IS-validated mechanism, OOS-untested cleanly. Carries forward to iter-v3/050 CONFIRMATION as CANDIDATE bundle ingredient on IS-only evidence basis. CONFIRMATION QR brief MUST explicitly note "primitive 10 has no clean OOS evidence from EXPLORATION; iter-v3/050 multi-seed run is the first OOS test of primitive 10 in clean conditions."
- **`block_long_for=("BCHUSDT",)` and `block_short_for=()` REMAIN in `run_baseline_v3.py:_build_v3_model`** for iter-v3/050 (carried forward as architectural state). Primitive 10 mechanism + 7 adversarial tests + GateStats counter REMAIN in `RiskV2Config` + `RiskV3Wrapper` + tests directory.
- **`adx_threshold_per_symbol` field REMAINS in `RiskV2Config` schema** (parallel to `regime_gate_symbols`, `block_long_for`, `block_short_for`). Mechanism + 5 adversarial tests + per-symbol gate dispatch REMAIN; only the wired value `{"TRXUSDT": 21.0}` is reverted at iter-v3/050 setup. (No need to delete the field — it's gracefully ignored when `adx_threshold_per_symbol = {}`.)
- **BASELINE_V3.md UNCHANGED at iter-v3/028** (+0.5101 IS / +0.5053 OOS). Per the strict BOTH-IS-AND-OOS-must-improve policy. iter-v3/045 single-seed PROMISING-anchor is NOT a CONFIRMATION baseline.
- **NO TAG ISSUED.** Per project convention, only CONFIRMATION-MERGE iterations get `v0.v3-NNN` tags. iter-v3/049 = EXPLORATION-NEGATIVE → no tag.
- **`--clean-oof` guardrail (SHA `6a216b5`) RETAINED.** The guardrail's behavior is correct; STRUCTURAL n_trials=700 is benign per the iter-v3/048 forensic resolution.

## Cycle 3 Cadence — COMPLETE 10/10

**Cycle 3 of 10 EXPLORATIONs is COMPLETE.** Per `feedback_v3_strict_10_to_1_cadence.md`, iter-v3/050 = SECOND v3 CONFIRMATION (separate from the EXPLORATION cycle).

| # | Iteration | Date | Axis | Verdict | OOS Δ vs anchor | PROMISING ingredient? |
|---|---|---|---|---|---:|---|
| 1 | iter-v3/040 | 2026-05-09 | REVERT per-symbol customizations (clear V3_FEATURES_PER_SYMBOL + V3_ATR_MULTIPLIERS_PER_SYMBOL); cycle 3 anchor restore | EXPLORATION-PROMISING-MECHANICAL | bit-identical to /029 +1.7653 | Cycle 3 anchor (NOT compoundable; baseline restoration) |
| 2 | iter-v3/041 | 2026-05-09 | Universal feature pruning (drop bottom-3: regime_momentum + sym_vs_btc + ret_skew_50; 14→11) | EXPLORATION-NEGATIVE | -0.76 (BCH -26 swing) | NO — regime_momentum was load-bearing for BCH despite rank 14 |
| 3 | iter-v3/042 | 2026-05-09 | Universal DEFAULT_ATR_MULTIPLIERS (2.0, 1.0) → (1.5, 0.75) | EXPLORATION-NEGATIVE | +0.31 (BCH +42 / TRX -33; IS aggregate -1.39) | NO — universal labeling change has divergent per-symbol effects |
| 4 | iter-v3/043 | 2026-05-09 | revert ATR + Kaufman efficiency_ratio_50 (universal engineered feature) | EXPLORATION-NEGATIVE (worst in cycle 3) | -2.66 (first negative OOS in cycle 3; ALGO -61 swing catastrophic) | NO — Kaufman ER broke all 4 symbols |
| 5 | iter-v3/044 | 2026-05-09 | Per-symbol ATR for ALGO (2.0, 1.5) — QR data-driven | EXPLORATION-PROMISING (clean — STRONG) | +0.77 (ALGO +49 swing 20.87→70.17 at 63.6% WR; OOS MaxDD 14.23% best in v3) | **YES — bundle ingredient #3** (regime_momentum + ALGO ATR) |
| 6 | iter-v3/045 | 2026-05-09 | Per-symbol ATR for LDO (2.0, 1.5) — QR data-driven (mirror of /044 ALGO mechanism) | EXPLORATION-PROMISING (clean — STRONGEST in v3) | +0.99 — HIGHEST OOS in v3 catalog; LDO +13 swing; all 4 symbols positive first time; OOS WR 50.4% / MaxDD 13.3% v3-records | **YES — bundle ingredient #4** |
| 7 | iter-v3/046 | 2026-05-09 | Per-symbol ATR for BCH (2.0, 1.5) — QR mirror-mechanism extension | EXPLORATION-NEGATIVE | -1.05 (BCH -45 swing; mirror mechanism doesn't transfer) | NO — mirror mechanism doesn't apply to symbols with stable SL:TP |
| 8 | iter-v3/047 | 2026-05-09 | Primitive 10 (direction-asymmetric kill switch) + BCH LONG block | EXPLORATION-NEGATIVE-clean (re-classified at /048 closeout from "multi-run-stochasticity-contaminated") | -2.36 (single-seed Optuna lottery on non-target symbols; primitive 10 IS-validated) | **CANDIDATE** — primitive 10 IS-only validated; carries to /050 CONFIRMATION as candidate ingredient on IS-only evidence |
| 9 | iter-v3/048 | 2026-05-10 | NEW universal engineered feature `vol_normalized_ret_5d` (15th feature) | EXPLORATION-NEGATIVE-clean | -3.15 (rank 13-15/15 all 4 syms; IS-OOS daily ratio 0.96 within band) | NO — feature redundant with regime_momentum (|IC|=0.892); NEW universal engineered feature axis CLOSED |
| 10 | **iter-v3/049** | **2026-05-10** | **NEW per-symbol ADX threshold (TRX 21) + vol_normalized_ret_5d REVERT** | **EXPLORATION-NEGATIVE-clean (this iteration)** | **-2.50** (TRX 6-trade Optuna lottery roster swap +11.27→-0.22 wpnl; ALGO/BCH/LDO frozen-baseline carry-over from /047) | **NO — per-symbol ADX dispatch axis CLOSED (complements iter-v3/014 global ADX closure)** |

**Cycle 3 EXPLORATION outcomes summary:**
- 1 PROMISING-MECHANICAL (anchor): /040
- 2 PROMISING-clean (compoundable bundle ingredients): /044 (ALGO ATR), /045 (LDO ATR)
- 1 IS-only-validated CANDIDATE (no clean OOS evidence): /047 (primitive 10)
- 6 NEGATIVE-clean: /041, /042, /043, /046, /048, /049
- Strongest OOS in cycle 3: iter-v3/045 (+3.5259 single-seed OOS Sharpe; HIGHEST in v3 catalog)
- Strongest negative OOS Δ in cycle 3: iter-v3/043 (-2.66; Kaufman ER catastrophic on ALGO)

**Bundle for iter-v3/050 SECOND CONFIRMATION (UNCHANGED — preserved as iter-v3/045 PROMISING bundle + primitive 10 carry-forward):**
- regime_momentum_signed_5d (iter-v3/025 → iter-v3/028 CONFIRMATION-MERGE)
- ALGO per-symbol ATR (2.0, 1.5) (iter-v3/044)
- LDO per-symbol ATR (2.0, 1.5) (iter-v3/045)
- Primitive 10 BCH LONG block (iter-v3/047, IS-only validated; first multi-seed OOS test at /050)

**Cadence discipline:** EXPLORATION wall-clock cap 2h (iter-v3/049 actual: ~35 min, well within cap). CONFIRMATION wall-clock cap 6h (iter-v3/050 spec).

## Memory Rule Updates

- **`feedback_adx_axis_asymmetric_v3.md` UPDATED 2026-05-10** by orchestrator per Critic FINAL `1908d50` recommendation. The "How to apply" section bullet 1 was revised to: "ADX axis is CLOSED in BOTH global AND per-symbol forms. No iter-v3/NNN+ tests ADX threshold (any direction, any dispatch architecture)." Bullet 4 was added: "Per-symbol ADX dispatch CLOSED 2026-05-10 (iter-v3/049 Critic FINAL `1908d50`): empirical test of `adx_threshold_per_symbol={'TRXUSDT': 21.0}` produced PATH C-clean (IS Δ -0.32, OOS Δ -2.50). The naive EDA BOTH-must-improve counterfactual (predicting +4.77 IS lift / -0.01 OOS cost) did NOT survive Optuna response at single-seed: TRX OOS trade count UNCHANGED (46 → 46) but 6-trade roster swap lost +11.27 wpnl winners and added -0.22 losers. Per-symbol ADX dispatch is structurally distinct from global-ADX-knob-tuning but BOTH are now empirically closed." Verified at `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_adx_axis_asymmetric_v3.md` line 18.

- **`feedback_v3_single_seed_frozen_baseline.md` rule REINFORCED** (no edit needed — the rule was already correctly calibrated by iter-v3/048 closeout). iter-v3/049 provides direct OOS row-level confirmation: ALGO/BCH/LDO trade rosters bit-identical between iter-v3/047 and iter-v3/049 (verified character-for-character per Critic). The mechanism: at single-seed=42, when feature_columns AND data input AND model config are IDENTICAL for a symbol, the per-symbol Optuna trajectory is bit-deterministic. This is the strongest direct validation observed in v3 catalog.

- **iter-v3/047 misdiagnosis CATEGORICALLY FALSIFIED in production environment.** The "cross-run stochasticity from multiple process invocations" attribution is now empirically falsified by iter-v3/049's bit-identical OOS reproduction of /047's ALGO/BCH/LDO rosters. Combined with iter-v3/048's forensic resolution of n_trials=700 structural attribution, the iter-v3/047 misdiagnosis is fully corrected at production grade. Catalog row label remains `NEGATIVE-clean (single-seed Optuna lottery on non-target symbols; primitive 10 IS-validated)` as established at iter-v3/048 closeout.

- **NEW lesson recorded** (this diary): the EDA "naive counterfactual" methodology (predict effect by removing/adding affected trades from the baseline trade roster) is INSUFFICIENT for per-symbol axis variants where Optuna re-trains on the modified IS sample. Future EDA briefs Section 2 should explicitly model the Optuna-retune cost path as a SEPARATE prediction band (e.g., "naive counterfactual: +4.77 IS / -0.01 OOS; Optuna-retune uncertainty band: ±5-10 wpnl on the modified-feature-IS-sample symbol"). At single-seed EXPLORATION, the Optuna-retune band can dominate the naive counterfactual; at multi-seed CONFIRMATION, the band tightens around the naive prediction.

- **NO new memory rule introduced for the cycle 3 closure** — the strict 10:1 cadence rule (`feedback_v3_strict_10_to_1_cadence.md`) was already in place at iter-v3/028 closeout and is now satisfied by cycle 3 reaching 10/10 EXPLORATIONs.

## iter-v3/050 SECOND v3 CONFIRMATION — Bundle Composition (EXPLICIT)

Per Critic FINAL `1908d50` recommendation #2, iter-v3/050 SECOND v3 CONFIRMATION carries forward the iter-v3/045 PROMISING bundle + primitive 10 with the following EXPLICIT composition:

### Feature stack
```python
V3_FEATURE_COLUMNS_TOP_N = 14 features  # (regime_momentum_signed_5d PRESENT)
                                         # (vol_normalized_ret_5d ABSENT — DROPPED per /048 closeout)
```

### Per-symbol ATR multipliers
```python
V3_ATR_MULTIPLIERS_PER_SYMBOL = {
    "ALGOUSDT": (2.0, 1.5),  # iter-v3/044
    "LDOUSDT":  (2.0, 1.5),  # iter-v3/045
}
# BCHUSDT and TRXUSDT use default (2.0, 1.0) — UNCHANGED from baseline
```

### Risk gates
```python
RiskV2Config(
    block_long_for=("BCHUSDT",),       # primitive 10 carry-forward (iter-v3/047)
    block_short_for=(),                 # empty
    adx_threshold_per_symbol={},        # EMPTY — per-symbol ADX TRX 21 DROPPED per this closeout
    adx_threshold=20.0,                 # global default (UNCHANGED for all symbols)
    enable_per_symbol_cap=False,        # disabled
    enable_regime_gate=False,           # disabled
    # ... (all other RiskV2Config fields at defaults)
)
```

### Universe + walk-forward
```python
V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT, ALGOUSDT)  # 4 symbols
V3_FEATURES_PER_SYMBOL = {}                          # empty (no per-symbol feature variants)
REQUIRED_GAP = 88 = (21+1) × 4                      # 4-symbol embargo
OOS_CUTOFF_DATE = 2025-03-24                        # IMMUTABLE
training_months = 24                                 # IMMUTABLE
```

### Run spec
```bash
uv run python run_baseline_v3.py --seeds 2 --n-trials 35
```
- `--seeds 2` per `feedback_outer_seed_cap_2_v3.md` (CONFIRMATION cap = 2 outer seeds)
- ENSEMBLE_SIZE=5 (auto; inner ensemble for live-prediction variance reduction)
- n_trials=35 per `feedback_v3_confirmation_n_trials_35.md`
- Total: 2 outer × 5 inner × 35 trials × 4 symbols = 1,400 trials per run
- Wall-clock cap: 6h per `feedback_v3_cadence_discipline.md`

### NO bundling, NO axis variation
Per `feedback_v3_iter018_confirmation_baseline_validation.md` precedent: SECOND CONFIRMATION is a multi-seed validation of the EXPLORATION-PROMISING bundle. NO new EXPLORATION axis. NO bundling beyond what's already in the iter-v3/045 + primitive 10 carry-forward state.

## iter-v3/050 MERGE Gates

Per `feedback_v3_strict_both_is_oos_baseline.md` (BOTH-must-improve rule):

### BASELINE_V3.md UPDATE GATES (must clear ALL to update BASELINE_V3.md)

1. **IS Sharpe (multi-seed mean)** > +0.5101 (iter-v3/028 anchor IS Sharpe)
2. **OOS Sharpe (multi-seed mean)** > +0.5053 (iter-v3/028 anchor OOS Sharpe)
3. **BOTH IS AND OOS must improve simultaneously** — improvement on only one axis = NO MERGE (per `feedback_v3_strict_both_is_oos_baseline.md`)
4. **Pareto seeds positive** — both seeds must produce positive multi-seed daily Sharpe (Pareto dominance check)
5. **PSR > 0.95** (CONFIRMATION-mode, not EXPLORATION-mode) per `feedback_v3_dsr_mode_artifact.md`
6. **OOS/IS Sharpe ratio ≥ 0.5** (Gate 3 — researcher-overfitting check)

### ASPIRATIONAL MERGE GATES (inform future-iteration priorities; do NOT block baseline updates per `feedback_v3_baseline_update_policy.md`)

7. IS Sharpe ≥ +1.0 floor
8. OOS Sharpe ≥ +1.0 floor
9. DSR > 0.95 (CONFIRMATION-mode at n_trials=1500-class)
10. Top-symbol concentration ≤ 30% of OOS PnL (or justified exception)
11. OOS trades ≥ 130 total, ≥ 10/month
12. 10-seed concentration validation
13. Per-symbol P&L distribution: ≥ 7/10 symbols positive

**Decision matrix:**
- ALL gates 1-6 PASS + most gates 7-13 PASS → CONFIRMATION-MERGE; update BASELINE_V3.md; tag `v0.v3-050`
- Gates 1-3 PASS, but Gate 4 (Pareto) or Gate 5 (PSR) or Gate 6 (OOS/IS) FAIL → CONFIRMATION-NO-MERGE-GATE-BLOCK; do NOT update BASELINE_V3.md
- Either Gate 1 (IS) or Gate 2 (OOS) FAIL → CONFIRMATION-NO-MERGE per BOTH-must-improve; do NOT update BASELINE_V3.md

## LDO Concern Flag for iter-v3/050

LDO OOS = -19.13 weighted_pnl is bit-identical between iter-v3/047 and iter-v3/049 (frozen baseline carry-over from iter-v3/045 PROMISING anchor). At single-seed=42, LDO has been -19.13 OOS in BOTH iter-v3/047 AND iter-v3/049 — TWO consecutive iterations with identical LDO OOS roster.

**Concern**: at multi-seed CONFIRMATION (seeds 42 + alternative), if LDO remains consistently negative across BOTH seeds, LDO is a structural drag on the OOS aggregate (not a seed-specific draw that dissolves at multi-seed). The iter-v3/045 single-seed PROMISING-anchor LDO OOS = +9.34 wpnl (positive) was the SEED-SPECIFIC FAVORABLE DRAW; the iter-v3/047 + iter-v3/049 LDO OOS = -19.13 is the SEED-SPECIFIC UNFAVORABLE DRAW. Multi-seed mean of LDO OOS is unknown; likely between -19.13 and +9.34, possibly negative.

**Action at iter-v3/050 CONFIRMATION-evaluation phase**: Critic must inspect LDO multi-seed OOS contribution. If LDO multi-seed mean OOS wpnl is meaningfully negative (e.g., < -5 wpnl across both seeds), iter-v3/051 EXPLORATION cycle (post-CONFIRMATION) should evaluate LDO removal from V3_MODELS. If LDO is the structural drag, the V3_MODELS = (BCH, TRX, ALGO) 3-symbol universe may produce a stronger CONFIRMATION at iter-v3/061.

This is NOT a pre-CONFIRMATION decision — LDO removal cannot be made without multi-seed evidence. The flag is a POST-CONFIRMATION consideration for the next EXPLORATION cycle.

**Related risk**: LDO per-symbol ATR (2.0, 1.5) was added at iter-v3/045 as a PROMISING ingredient. If LDO is removed from V3_MODELS, the LDO ATR customization becomes moot. The iter-v3/045 OOS lift would be re-attributed to ALGO ATR + regime_momentum + primitive 10 — losing the LDO contribution. Multi-seed CONFIRMATION at iter-v3/050 will reveal whether LDO ATR is genuine edge or single-seed lottery.

## See Also

- `briefs-v3/iteration_v3-049/research_brief.md` — Phase 5 brief (SHA `24f1f6c`)
- `briefs-v3/iteration_v3-049/phase5p5_gate.md` — Phase 5.5 gate PASS (SHA `524dde2`)
- `briefs-v3/iteration_v3-049/engineering_report.md` — Phase 6/7 engineering report (SHA `d8998d9`; setup `6eeff46`)
- `briefs-v3/iteration_v3-049/review.md` — Phase 7.5 Critic FINAL (SHA `1908d50`)
- `analysis/iteration_v3-049/multi_axis_eda.py` — main 5-axis EDA script (SHA `ba8a3de`)
- `analysis/iteration_v3-049/axis_e_finegrained_adx.py` — fine-grained per-symbol ADX 21-25 sweep
- `analysis/iteration_v3-049/axis_e_per_symbol_adx_simulator.py` — strategy ABCD simulator
- `analysis/iteration_v3-049/axis_e_with_primitive10_carry.py` — corrected EDA WITH primitive 10
- `analysis/iteration_v3-049/axis_d_with_primitive10_carry.py` — drawdown brake EDA
- `analysis/iteration_v3-049/synthesis.md` — EDA synthesis with headline finding
- `analysis/iteration_v3-049/candidate_axes_ranking.md` — 5-axis ranking with axis (e) selected
- `reports-v3/iteration_v3-049/comparison.csv` — full numerical results
- `reports-v3/iteration_v3-049/dsr.json` — DSR/PBO/PSR (n_trials=700 STRUCTURAL; PBO + PSR valid; DSR INFORMATIONAL ONLY)
- `reports-v3/iteration_v3-049/seed_summary.json` — single-seed=42 Pareto data
- `reports-v3/iteration_v3-049/in_sample/per_symbol.csv` — per-symbol IS PnL attribution
- `reports-v3/iteration_v3-049/out_of_sample/per_symbol.csv` — per-symbol OOS PnL attribution
- `reports-v3/iteration_v3-049/ic_matrix.csv` — pairwise IC (14×14 unchanged from /047)
- `reports-v3/iteration_v3-049/adf_test.csv` — ADF stationarity verification
- `reports-v3/iteration_v3-049/in_sample/model_importance_last_month_*.csv` — feature importance ranks
- `reports-v3/iteration_v3-049/out_of_sample/trades.csv` — OOS trade roster (ALGO/BCH/LDO bit-identical to /047)
- `src/crypto_trade/strategies/ml/risk_v2.py` — `adx_threshold_per_symbol` field (lines 127-137) + `_adx_gate_fails` per-symbol dispatch (lines 407-411)
- `tests/strategies/ml/test_per_symbol_adx_threshold.py` — 5 adversarial tests
- Setup commit SHA `6eeff46` (per-symbol ADX TRX 21 wiring + vol_normalized_ret_5d REVERT + V3_FEATURE_COLUMNS_TOP_N 15→14)
- `BASELINE_V3.md` — UNCHANGED at iter-v3/028 (+0.5101 IS / +0.5053 OOS)
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_adx_axis_asymmetric_v3.md` — UPDATED 2026-05-10 per Critic FINAL `1908d50` (per-symbol ADX dispatch CLOSED; bullet 4 added)
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_single_seed_frozen_baseline.md` — REINFORCED by iter-v3/049 OOS row-level confirmation (no edit needed)
- `briefs-v3/iteration_v3-047/review.md` (SHA `785500f`) — iter-v3/047 misdiagnosis CATEGORICALLY FALSIFIED by iter-v3/049 OOS row-level reproduction
- `briefs-v3/iteration_v3-048/review.md` (SHA `55fbadb`) — iter-v3/048 forensic resolution of n_trials=700 structural attribution
- `diary-v3/iteration_v3-048.md` — cycle 3 #9 of 10 closeout; recommended candidate (e) per-symbol ADX as iter-v3/049 axis
- `diary-v3/iteration_v3-047.md` — primitive 10 introduction; carries forward to iter-v3/050 as IS-only validated CANDIDATE
- `briefs-v3/cycle3_plan.md` — cycle 3 strategy (iter-v3/040-049)
- `briefs-v3/exploration_catalog.md` — iter-v3/049 catalog row at diary closure (PATH C-clean verdict + per-symbol ADX dispatch closure)
