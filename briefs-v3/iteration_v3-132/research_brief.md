# iter-v3/132 — Research Brief (CYCLE-7 CONFIRMATION — MULTI-SEED VALIDATION of /121-canonical; NOT bundle assembly)

**Branch**: `iteration-v3/132`
**EDA cross-reference SHAs**: N/A — NO new EDA per `feedback_v3_axis_selection_quant_discipline.md` (CONFIRMATION-class iterations may rely on prior EDAs); the /121 architecture is the well-characterized canonical baseline established at SHA `b0576df` (BASELINE_V3.md update commit) + tag `v0.v3-121`.
**Setup commit SHA**: TBD (single Engineer setup commit — ITERATION_LABEL flip + pre-flight assertion housekeeping; ZERO new feature implementation, ZERO new gate, ZERO knob change vs /121 head)
**Iteration type**: **CYCLE-7 CONFIRMATION (slot 11 — MULTI-SEED VALIDATION of /121-canonical)**. NOT bundle assembly. NOT a methodology bootstrap. NOT counted toward cycle-8 10/10 EXPLORATION cadence.
**Predecessor**: iter-v3/131 — CYCLE-7 CLOSURE-RECONCILIATION memo (commit `2d4f367`, tag `v0.v3-131`). No backtest, no axis variation. The /131 closure-reconciliation Section 5 LOCKED the /132 spec; this brief implements that LOCKED spec verbatim.
**Authorization**: (i) /130 Critic FINAL `d33cc2e` Recommendation 2 — "/132 = MULTI-SEED VALIDATION of /121-canonical, NOT bundle assembly"; (ii) `feedback_v3_strict_10_to_1_cadence.md` — STRICT 10:1 cadence with separate CONFIRMATION (cannot collapse the 10th EXPLORATION into the CONFIRMATION); (iii) `feedback_v3_iter018_baseline_bootstrap.md` — re-validation precedent at cycle boundaries; (iv) /131 closure-reconciliation memo Section 5 LOCKED spec.

---

## Section 0 — Hand-chosen Parameters Provenance

Per `feedback_v3_brief_parameter_provenance.md`: every hand-chosen parameter must name its EXPLORATION source iteration + the committed analysis table + an auditable IS-only temporal fence.

**ZERO new hand-chosen parameters at /132.** The /132 configuration is BIT-IDENTICAL to /121's canonical configuration (per BASELINE_V3.md Code Configuration section at SHA `b0576df`). All parameters carry forward unchanged:

| Parameter | Value | Source iteration | EDA table | Provenance |
|---|---:|---|---|---|
| `no_confirm_trigger_atr` | **0.50** | /116 EDA → /120 CONFIRMATION → /121 MERGED canonical | `analysis/iteration_v3-116/T7_early_exit_grid.csv` row `(0.50, 4)` | Hand-chosen at /116; only cell with positive IS Sharpe lift on all 3 symbols; UNCHANGED at /120 + /121 + /132. |
| `no_confirm_k_candles` | **4** | /116 EDA → /120 CONFIRMATION → /121 MERGED canonical | `analysis/iteration_v3-116/T7_early_exit_grid.csv` row `(0.50, 4)` | Hand-chosen at /116; first-third of 21-candle timeout; UNCHANGED through /121 + /132. |
| `enable_no_confirm_exit` | **True** | /120 (re-enabled) → /121 MERGED → /132 inherited | n/a | Inherited from /121 canonical state. No new hand-chosen scalar. |
| `enable_per_symbol_drawdown_brake` | **False** | /127 (axis CLOSED — NEGATIVE-catastrophic at 9/9 cycle-7 binding) | `feedback_v3_concentration_is_signal.md` + /127 closeout | REVERT preserved from /129 + /130. |
| `enable_per_symbol_drawdown_scaling` | **False** | /129 (axis CLOSED — NEGATIVE-catastrophic) | /129 closeout + `feedback_v3_optuna_trajectory_shift_finding.md` | REVERT preserved from /130. |
| Bar-interval | **8h** | /121 canonical baseline (REVERT from /130's 4h) | /130 closeout — bar-interval axis CLOSED at NEGATIVE-catastrophic IS −2.61 (worst in v3 history) | REVERT preserved at /132; features cache at `data/features_v3/` (NOT `data/features_v3_4h/`). |

**Auditable temporal fence**:
- All canonical /121 source EDAs (notably /116 SHA `52444c9`) assert `close_time < OOS_CUTOFF_MS = 1742774400000`.
- Per `feedback_v3_axis_selection_quant_discipline.md`, CONFIRMATION-class re-validation iterations may rely on prior EDAs. NO new EDA is mandated at /132.
- The /131 closure-reconciliation memo (Section 5.4 pre-launch checks) constitutes the QR's audit trail for the parameter inheritance.

---

## Section 0.5 — Iteration Type Declaration

- **TYPE**: **CYCLE-7 CONFIRMATION (slot 11 — MULTI-SEED VALIDATION of /121-canonical)**.
- **Cycle accounting**: cycle-7 EXPLORATION cadence COMPLETE — 10 EXPLORATIONs at /122–/131 (per `feedback_v3_strict_10_to_1_cadence.md` STRICT 10:1 rule).
  - **10 EXPLORATION precedents** (cycle-7 catalog at /131 closure-reconciliation Section 1.1):

    | Slot | Iter | Axis class | IS Δ vs /121 | OOS Δ vs /121 | Verdict |
    |---:|---|---|---:|---:|---|
    | 1 | /122 | cross-asset (eth_ret_3d) | −0.34 | +0.20 | NEGATIVE-INERT |
    | 2 | /123 | cross-asset (eth_vs_sym_rv_50) | −1.73 | +0.79 | NEGATIVE-catastrophic |
    | 3 | /124 | longer-cadence labels K=63 + sqrt(3) ATR | −0.87 | −0.94 | NEGATIVE-catastrophic |
    | 4 | /125 | WILD V3_MODELS ATOM/RUNE/UNI | −1.25 | −0.86 | NEGATIVE-catastrophic |
    | 5 | /126 | multi-frequency d24_ret_autocorr_lag1_50 | −1.21 | −1.08 | NEGATIVE-catastrophic |
    | 6 | /127 | per-symbol drawdown brake (binary kill) | −0.52 | +0.03 | NEGATIVE-catastrophic |
    | 7 | /128 | WILD 6-symbol sector-pure L1 universe | −1.73 | +1.17 | NEGATIVE-catastrophic |
    | 8 | /129 | continuous position-size scaling at drawdown | −0.64 | +0.001 | NEGATIVE-catastrophic |
    | 9 | /130 | 4h bar-interval (BCH/LDO/TRX preserved) | **−2.61** | −0.64 | NEGATIVE-catastrophic (worst IS in v3 history) |
    | 10 | /131 | CLOSURE-RECONCILIATION (NO backtest, NO axis) | n/a | n/a | CLOSURE-RECONCILIATION memo |

  - **Empirical record**: 8/9 NEGATIVE-catastrophic + 1/9 NEGATIVE-INERT + 0/9 PROMISING across 4 structurally distinct axis classes. ZERO PROMISING components to bundle.
- **CONFIRMATION role**: per /131 closure-reconciliation Section 5 LOCKED spec, /132 is the BASELINE RE-VALIDATION analog of /018 BOOTSTRAP-CONFIRMATION at the /059 RE-ANCHOR — NOT bundle assembly. The well-characterized /121 canonical architecture is re-evaluated at the same unified 10-seed CONFIRMATION budget that produced /121's headline metrics. The /132 purpose is to confirm /121 is reproducible under current code state (post /127 brake infrastructure + /129 continuous-scaling primitive + /130 bar-interval support + ITERATION_LABEL updates + _TeeLogger run.log wrap merged across cycle-7).
- **Run mode**: default CONFIRMATION (NO `--exploration` flag → `ENSEMBLE_SIZE = CONFIRMATION_ENSEMBLE_SIZE = 10`).
- **Optuna budget**: `--n-trials 35` per `feedback_v3_confirmation_n_trials_35.md`. Total trials = 35 × 3 sym × 10 seeds = **1050** — same envelope as /059 + /120 + /121.
- **Wall-clock target**: ~3.2h (per /121 = 3.21h baseline); HARD CAP **6h** per `feedback_v3_cadence_discipline.md`.
- **Runner invocation**: per /131 closure-reconciliation memo Section 5.1 — `uv run python run_baseline_v3.py --confirmation --n-trials 35 --clean-oof --seeds 2` (5 inner × 2 outer via unified-seed-lineage; the `--seeds 2` flag selects the 2-outer-seed lineage decomposition while the unified 10-seed ensemble remains the validation surface).
- **Anchor (current canonical baseline)**: `v0.v3-121` (BASELINE_V3.md SHA `b0576df`) — IS monthly Sharpe **+1.3108** / OOS monthly Sharpe **+0.9682** (10-seed unified CONFIRMATION). BOTH-must-improve target per `feedback_v3_strict_both_is_oos_baseline.md` — but with the explicit /131-LOCKED LOOSE TOLERANCE per Section 5.3.

---

## Section 1 — Testable Hypothesis (ONE sentence)

> The /121 canonical architecture (BCH/LDO/TRX universe + 14-feature V3_FEATURE_COLUMNS_TOP_N + ATR (2.0, 1.0) triple-barrier K=21 + `enable_no_confirm_exit=True (trigger_atr=0.50, k_candles=4)` + 7-primitive RiskV2 + per-symbol drawdown brake/scaling DISABLED + 8h bar-interval) re-validates at multi-seed unified 10-seed CONFIRMATION budget under current code state (post /127 + /129 + /130 infrastructure merges) — producing multi-seed mean IS monthly Sharpe ≥ **+1.0** AND OOS monthly Sharpe ≥ **+0.8** while clearing the hard methodology gates (PSR > 0.95, frac_positive_paths ≥ 0.55, PBO < 0.40) — OR the /121 baseline has materially regressed under code-state drift across cycle-7, in which case /132 fires CONFIRMATION-RE-ANCHOR and BASELINE_V3.md is downgraded.

---

## Section 2 — IS-Only Numerical Evidence (CROSS-REFERENCE only; NO new EDA)

Per `feedback_v3_axis_selection_quant_discipline.md`: CONFIRMATION-class re-validation iterations may rely on prior EDAs and prior CONFIRMATION metrics.

### Section 2.1 — /121 canonical baseline metrics (the re-validation target)

From BASELINE_V3.md Headline Metrics + Per-Symbol Attribution (SHA `b0576df`; tag `v0.v3-121`):

| Metric | /059 prior canonical | /121 current canonical | Δ vs /059 |
|---|---:|---:|---:|
| IS monthly Sharpe | +1.0894 | **+1.3108** | **+0.2214** |
| OOS monthly Sharpe | +0.5791 | **+0.9682** | **+0.3891** |
| OOS/IS monthly Sharpe ratio | 0.5316 | **0.7386** | +0.2070 |
| IS Trades | 171 | 173 | +2 |
| OOS Trades | 94 | 98 | +4 |
| IS MaxDD | 30.97% | **26.38%** | −4.59pp |
| OOS MaxDD | 34.53% | **25.70%** | −8.83pp |
| OOS Calmar | 0.6585 | **1.4843** | +0.83 |
| frac_positive_paths (CPCV 45) | 0.6444 | **0.6444** | IDENTICAL |
| PBO mean | 0.1278 | **0.1278** | IDENTICAL |
| PSR | 1.0 | 1.0 | UNCHANGED |
| CPCV path Sharpe Q75 | 0.8378 | **0.8378** | IDENTICAL |
| n_trials total | 1050 | 1050 | UNCHANGED |
| Wall-clock | 3.60h | 3.21h | comparable |

The /121 IS lift +0.22 + OOS lift +0.39 = the cycle-6 closure event (first BASELINE_V3.md update since 2026-05-13). Per BASELINE_V3.md: "first cycle-6 strictly-accretive ingredient" — Component A (`no_confirm` RULE-layer exit primitive) standalone at 10-seed CONFIRMATION.

### Section 2.2 — /121 per-symbol attribution (the F5-analog evidence)

From BASELINE_V3.md Per-Symbol Attribution + `reports-v3/iteration_v3-121/out_of_sample/per_symbol.csv`:

| Symbol | OOS weighted_pnl /121 | OOS weighted_pnl /059 | Δ vs /059 | OOS n_trades | OOS WR | concentration_pct |
|---|---:|---:|---:|---:|---:|---:|
| BCH | **+35.83** | +24.75 | **+11.08** | 35 | 48.6% | 93.92% (driver; broad-based lift) |
| TRX | **+5.21** | +4.16 | **+1.04** | 51 | 43.1% | 13.65% (WR climbed +1.4pp) |
| LDO | **−2.89** | −6.18 | **+3.29** | 12 | 25.0% | −7.57% (still OOS-negative but materially closer to neutral) |

**3/3 symbols positive OOS Δ vs /059 at /121** — broad-based cycle-6 closure event.

### Section 2.3 — Cycle-7 EXPLORATION catalog summary (the empirical no-bundling justification)

From /131 closure-reconciliation Section 1.1 + Section 2.2-2.4: 8/9 cycle-7 EXPLORATIONs NEGATIVE-catastrophic + 1/9 NEGATIVE-INERT across 4 structurally distinct axis classes (cross-asset features, longer-cadence labels, universe substitution, multi-frequency features, RISK-PRIMITIVE binary/continuous, sector-pure universe, 4h bar-interval). ZERO PROMISING components to bundle. /131 closure-reconciliation Section 5 LOCKED /132 as MULTI-SEED VALIDATION (NOT bundle assembly).

### Section 2.4 — Code-state drift accounting (across /122–/131)

Per /131 closure-reconciliation memo Section 5.3 — between /121 CONFIRMATION-MERGE (2026-05-20, SHA `b0576df`, tag `v0.v3-121`) and /132 start (today), the worktree has merged the following infrastructure across cycle-7:

| Source iter | Infrastructure merged | DISABLED at /132? |
|---|---|---|
| /127 | RiskV2 per-symbol drawdown brake (binary kill) | YES — `enable_per_symbol_drawdown_brake=False` |
| /129 | RiskV2 per-symbol drawdown scaling (continuous 0-1 ramp) | YES — `enable_per_symbol_drawdown_scaling=False` |
| /130 | Bar-interval 4h support (`FEATURES_DIR_4H`, `label_timeout_minutes=5040` plumbing) | YES — bar-interval=8h, features cache `data/features_v3/`, `label_timeout_minutes=10080` |
| /130 | `_TeeLogger` run.log capture wrap | LEAVE ENABLED (Engineer instrumentation; metric-neutral) |
| /122-/131 | ITERATION_LABEL = "v3-NNN" prefix updates | UPDATE to "v3-132" |
| Various | Test additions (no behavioral change to backtest) | LEAVE ENABLED |

While all /127/129/130 features are DISABLED at /132, the runner code path has changed enough that exact reproduction (bit-identical) is not expected. This is the rationale for the /131-LOCKED LOOSE TOLERANCE (Section 4 F1 below): multi-seed mean IS ≥ +1.0 AND OOS ≥ +0.8, allowing up to −0.31 IS slippage and −0.17 OOS slippage from /121's exact CONFIRMATION reproduction.

---

## Section 3 — Proposed Changes (BASELINE RE-VALIDATION vs /121 canonical)

Bundle composition at /132 is **ZERO-COMPONENT vs /121 canonical** — NO new feature, NO new gate, NO knob flip vs the /121 head state. The /132 setup is a pure ITERATION_LABEL update + pre-flight verification.

### Sub-fix 1 — `ITERATION_LABEL` + `MODEL_SPECS` prefix update

`ITERATION_LABEL` `"v3-131"` (or whatever the most-recent head value is) → `"v3-132"`. `MODEL_SPECS` prefix `"v3-NNN-..."` → `"v3-132-..."` (per the runner's MODEL_SPECS construction).

### Sub-fix 2 — Verify all /127/129/130 features are DISABLED

Per /131 closure-reconciliation memo Section 5.4 pre-launch checks 4, 5, 6:
- `enable_per_symbol_drawdown_brake=False` (REVERT preserved from /129 + /130)
- `enable_per_symbol_drawdown_scaling=False` (REVERT preserved from /130)
- Bar-interval is 8h; features cache at `data/features_v3/` (NOT `data/features_v3_4h/`); `label_timeout_minutes=10080` (NOT 5040)

If any of these is NOT in the disabled/reverted state at the /131 head, the Engineer must flip it as part of the /132 setup commit BEFORE launching the backtest.

### Sub-fix 3 — Verify Component A (`no_confirm`) parameters at /121 canonical state

Per /131 closure-reconciliation memo Section 5.4 pre-launch check 3:
- `enable_no_confirm_exit=True` at `run_baseline_v3.py` (carried from /121)
- `no_confirm_trigger_atr=0.50` (carried from /116 → /121)
- `no_confirm_k_candles=4` (carried from /116 → /121)
- Pre-flight accretion-guard expected tuple `(True, 0.50, 4)` — UNCHANGED from /121.

### Sub-fix 4 — Verify V3_FEATURE_COLUMNS_TOP_N at 14 features

Per /131 closure-reconciliation memo Section 5.4 pre-launch check 2:
- `len(V3_FEATURE_COLUMNS_TOP_N) == 14` (the /121 canonical 14-feature stack: `max_dd_window_50, ema_spread_atr_20, ret_kurt_50, ret_skew_200, range_realized_vol_50, hurst_diff_100_50, ret_kurt_200, hurst_100, btc_ret_14d, ret_skew_50, vwap_dev_20, ret_autocorr_lag1_50, sym_vs_btc_ret_7d, regime_momentum_signed_5d`).
- Confirm C3 removal, eth_ret_3d removal (/122 REVERT), eth_vs_sym_rv_50 removal (/123 REVERT), d24_ret_autocorr_lag1_50 removal (/126 REVERT) are all in place.

### Sub-fix 5 — Verify V3_MODELS universe at BCH/LDO/TRX

Per /131 closure-reconciliation memo Section 5.4 pre-launch check 1:
- `V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT)` (the /121 canonical 3-symbol universe).
- Confirm /125 REVERT (ATOM/RUNE/UNI removed) and /128 REVERT (6-symbol L1 sector-pure universe removed) are both in place.

### Sub-fix 6 — Verify CPCV + REQUIRED_GAP infrastructure

Per /131 closure-reconciliation memo Section 5.4 pre-launch check 7:
- `REQUIRED_GAP = 66 = (21 + 1) × 3` (the /121 canonical purge gap for 3-symbol × 21-candle-timeout architecture).
- CPCV n_paths=45, embargo=27 (UNCHANGED from /121).

### Sub-fix 7 — CONFIRMATION-mode flag (no `--exploration`)

Per /131 closure-reconciliation memo Section 5.1 — runner invocation:

```bash
uv run python run_baseline_v3.py --confirmation --n-trials 35 --clean-oof --seeds 2
```

`ENSEMBLE_SIZE = CONFIRMATION_ENSEMBLE_SIZE = 10` (5 inner × 2 outer via unified-seed-lineage). The `--seeds 2` flag selects the 2-outer-seed lineage decomposition. The `--clean-oof` flag preserves the per `feedback_v3_oof_parquet_guardrail.md` runner robustness.

### Section 3.5 — Code-change manifest

**NO new feature implementation. NO new function. NO new test. NO new gate. NO knob flip vs /121 head state.** Only:

1. **`ITERATION_LABEL` + `MODEL_SPECS` prefix update** — `"v3-NNN"` → `"v3-132"`.
2. **Pre-flight VERIFY commit** — confirm all 12 pre-launch checks in /131 Section 5.4 PASS in source at HEAD; if any FAIL, flip to /121 canonical state.
3. **Brief commit** — this file at `briefs-v3/iteration_v3-132/research_brief.md`.

**Knobs UNCHANGED vs /121 canonical** (per Sub-fixes 2-6):
- V3_MODELS = BCHUSDT, LDOUSDT, TRXUSDT
- V3_FEATURE_COLUMNS_TOP_N (14 features) — UNCHANGED at /121 anchor
- ATR multipliers — (atr_tp=2.0, atr_sl=1.0); V3_ATR_MULTIPLIERS_PER_SYMBOL = {} empty
- 7-primitive RiskV2 stack — vol scaling, ADX 20.0, Hurst regime, zscore 2.0, low-vol filter, hit-rate (DISABLED), BTC trend kill (15.0%); regime gate, per-symbol cap, per-symbol drawdown brake, per-symbol drawdown scaling all DISABLED
- Triple-barrier labeling — 21-candle (10080-min) timeout
- `no_confirm` RULE-layer primitive: `enable_no_confirm_exit=True`, `no_confirm_trigger_atr=0.50`, `no_confirm_k_candles=4`
- ENSEMBLE_SIZE = 10 (unified 10-seed lineage `(191664963, 1662057957, 1405681631, 942484272, 929893137, 33158374, 1465339467, 1273345680, 115579757, 1952249162)`)
- CPCV n_paths = 45, embargo = 27, REQUIRED_GAP = 66
- Walk-forward POST-FIX at `e149e9d`
- Optuna `n_jobs=1`, `colsample_bytree` Optuna-tuned
- Sacred constants UNCHANGED: `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24`
- Bar-interval = 8h (REVERT from /130's 4h carried forward)

**Differences vs /131 head state**: ITERATION_LABEL prefix only. Any other knob deviation indicates code-state drift and MUST be flipped to the /121 canonical specification as part of /132 setup (per /131 Section 5.4 pre-launch verification gate).

---

## Section 4 — Pre-registered Falsifiers (BINDING — non-negotiable)

Two falsifier groups locked at /131 closure-reconciliation memo Section 5.2:
- F1 (loose-tolerance BOTH-must-improve) — the /121 re-validation gate, with explicit slack for code-state drift
- F2 (hard methodology gates) — the v3 floor gates (PSR, frac_positive_paths, PBO)

Pre-registered in numerical form per the orchestrator's task statement; cannot be renegotiated post-hoc.

### F1 — Loose-tolerance BOTH-must-improve (BINDING — the /121 re-validation gate)

Per /131 closure-reconciliation memo Section 5.2 + Section 5.3 LOCKED tolerance: BASELINE_V3.md re-validates at /121 ONLY IF /132 multi-seed mean clears BOTH the loose-tolerance IS and OOS thresholds.

**Numerical thresholds**:
- IS multi-seed mean ≥ **+1.0** AND
- OOS multi-seed mean ≥ **+0.8**.

**F1 firing direction**:
- If BOTH thresholds clear → F1 PASSES → /121 architecture is reproducible under current code state → BASELINE_V3.md UNCHANGED at /121 canonical → CONFIRMATION-VALIDATION-PASS.
- If EITHER threshold fails (IS < +1.0 OR OOS < +0.8) → F1 FAILS → CONFIRMATION-RE-ANCHOR diary → investigate code-state drift across /122–/131; potentially downgrade BASELINE_V3.md.

**Rationale for loose tolerance** (per /131 memo Section 5.3): /121 multi-seed mean was IS +1.3108 / OOS +0.9682. The F1 threshold IS +1.0 allows up to −0.31 IS slippage; OOS +0.8 allows up to −0.17 OOS slippage. This provides sufficient buffer for incidental code drift (the /127 brake infrastructure + /129 continuous-scaling primitive + /130 bar-interval support + ITERATION_LABEL plumbing + _TeeLogger run.log wrap merged across cycle-7) WHILE NOT MASKING material regression. The loose tolerance is the explicit operationalization of "/121 reproducibility under current code state, not bit-identical replication" per Critic FINAL `d33cc2e` Recommendation 2.

### F2 — Hard methodology gates (BINDING — v3 floor gates)

Per BASELINE_V3.md Code Configuration + `feedback_v3_dsr_mode_artifact.md`. Three binding methodology gates at the multi-seed unified-ensemble architecture:

| Gate | Threshold | /121 reference | /132 PASS condition |
|---|---|---:|---|
| **PSR** | **> 0.95** | 1.0 | /132 PSR > 0.95 |
| **frac_positive_paths** (CPCV 45 paths) | **≥ 0.55** | 0.6444 | /132 ≥ 0.55 |
| **PBO** (mean per-cell) | **< 0.40** | 0.1278 | /132 PBO mean < 0.40 |

**F2 firing direction**: if ANY of {PBO ≥ 0.40, PSR ≤ 0.95, frac_positive_paths < 0.55}, F2 FAILS → CONFIRMATION-RE-ANCHOR diary on methodology floor.

DSR_relative remains INFORMATIONAL ONLY per `feedback_v3_dsr_mode_artifact.md`. Per BASELINE_V3.md headline metrics, /121 carries `dsr_relative_b4 = 1.0` (Path B4 corrected formulation); the /132 result will be reported alongside for catalog continuity but is NOT a binding gate at this iteration.

### Aggregate falsifier summary

The /132 iteration RE-VALIDATES the /121 canonical baseline ONLY IF both F1 AND F2 PASS at multi-seed:

| Falsifier | PASS condition |
|---|---|
| **F1 loose-tolerance BOTH-must-improve** | /132 multi-seed mean IS ≥ **+1.0** AND OOS ≥ **+0.8** |
| **F2 hard methodology gates** | PSR > **0.95** AND frac_positive_paths ≥ **0.55** AND PBO < **0.40** |

If F1 PASSES and F2 PASSES → BASELINE_V3.md UNCHANGED at /121 canonical; CONFIRMATION-VALIDATION-PASS diary; cycle-7 closes at /121 baseline; cycle-8 design begins from /121 with the cohort-AND-frequency-shape constraint binding (per /131 memo Section 2 + 8).

If F1 FAILS OR F2 FAILS → CONFIRMATION-RE-ANCHOR diary (analog of /018 BOOTSTRAP-CONFIRMATION); investigate code-state drift; potentially downgrade BASELINE_V3.md if multi-seed mean falls materially below /121 ADJUSTED reference (IS ≈ +1.06 / OOS ≈ +0.85 per /131 Section 5.3 adjusted bounds).

---

## Section 5 — Risk Mitigation

Standard `feedback_v3_risk_mitigation_design.md` framework. R1–R5 UNCHANGED from /121 canonical:

- **R1 — Cool-downs**: standard /121 post-trade 2-candle cooldown; UNCHANGED. The `no_confirm` exit triggers a normal trade close with its own subsequent cooldown — cool-down semantics preserved.
- **R2 — Drawdown scaling**: `enable_per_symbol_drawdown_brake=False` (per /054 stateful-deadlock closure + /127 cycle-7 NEGATIVE-catastrophic). `enable_per_symbol_drawdown_scaling=False` (per /129 cycle-7 NEGATIVE-catastrophic). UNCHANGED at /132.
- **R3 — OOD detection**: z-score OOD gate at threshold 2.0. UNCHANGED.
- **R4 — Vol kill-switch**: BTC trend filter at 15.0% threshold. UNCHANGED.
- **R5 — Concentration caps**: NO per-symbol PnL share caps (per `feedback_v3_concentration_is_signal.md`). UNCHANGED. /121 OOS concentration at BCH 93.92% reflects the broad-based cycle-6 closure event lift; not a /132-specific risk.

**/132-specific risk consideration**:

This is a BASELINE RE-VALIDATION iteration — there is no new primitive being introduced and no new risk to mitigate beyond the standard /121 canonical risk envelope. The /132 risk profile is BIT-IDENTICAL to /121's at the methodology level. The only operational risk is **code-state drift detection**: if /127/129/130 infrastructure unintentionally affects the /132 trade roster (e.g., a per-symbol drawdown brake code path is reachable even with the flag DISABLED), the /132 result will be measurably below /121 — which F1 catches at the +1.0/+0.8 thresholds. F1 is the primary risk-mitigation gate for this iteration.

---

## Section 6 — Risk Management (Operational)

UNCHANGED from /121 canonical. Per BASELINE_V3.md:
- 7-primitive RiskV2 gate stack at /121 specification
- Standard CPCV with n_paths=45, embargo=27, REQUIRED_GAP=66
- Walk-forward POST-FIX at `e149e9d` (carries forward from /058 RE-ANCHOR #1)
- OOF parquet guardrail `--clean-oof` flag active
- _TeeLogger run.log capture inherited from /130 (metric-neutral instrumentation)

No new RiskV2 primitive at /132. /132 is the multi-seed re-validation of the /121 canonical operational risk profile.

---

## Section 7 — Pre-registered Failure Modes

Per `feedback_v3_promising_mechanical_subtype.md` + /131 closure-reconciliation memo Section 5.2. Three mutually exclusive verdict modes; each maps to the responsive falsifier:

**Mode A (CONFIRMATION-VALIDATION-PASS — /121 reproduces under current code state)**: /132 multi-seed mean IS ≥ +1.0 AND OOS ≥ +0.8 AND all methodology gates PASS (F1 + F2 both PASS).
- **Verdict**: **CONFIRMATION-VALIDATION-PASS** → BASELINE_V3.md UNCHANGED at /121 canonical (`v0.v3-121`).
- **Cycle-7 closure**: cycle-7 closes at /121 baseline; 9 NEGATIVE EXPLORATIONs + 1 closure-reconciliation + 1 re-validation; ZERO ingredients merged this cycle.
- **Tag**: `v0.v3-132` set on the /132 closeout commit, marking the cycle-7 closure milestone.
- **Cycle-8 design**: begins from /121 with the cohort-AND-frequency-shape constraint binding (per /131 memo Section 8). Brief Section 0.6 "Architecture-Family Justification" mandatory at cycle-8 first EXPLORATION.
- **Probability estimate**: **~70%**. The modal expectation. /121 architecture is the well-characterized canonical baseline; the disabled /127/129/130 infrastructure should not affect trade roster materially given they're flag-gated. The loose tolerance F1 (+1.0/+0.8 vs /121's +1.31/+0.97) absorbs incidental code drift.

**Mode B (CONFIRMATION-RE-ANCHOR — F1 fails on either leg, F2 PASSES)**: /132 multi-seed mean IS < +1.0 OR OOS < +0.8, but methodology gates F2 all PASS.
- **Verdict**: **CONFIRMATION-RE-ANCHOR** — /121 baseline has materially regressed under code-state drift.
- **Action**: file RE-ANCHOR diary; investigate code-state drift across /122–/131 to identify the regression source (likely candidates: /127 brake code path side-effect, /129 continuous-scaling code path side-effect, /130 bar-interval plumbing side-effect, _TeeLogger numerical side-effect, ITERATION_LABEL parsing side-effect, package version drift).
- **BASELINE_V3.md action**: if /132 multi-seed mean falls materially below /121 ADJUSTED reference (IS ≈ +1.06 / OOS ≈ +0.85), downgrade BASELINE_V3.md to /132's measured values; if /132 falls between the loose-tolerance F1 thresholds (IS < +1.0 OR OOS < +0.8) but at-or-above the ADJUSTED reference, keep BASELINE_V3.md at /121 with the regression documented as a Reproducibility Stamp section note.
- **Cycle-8 design**: requires resolving the regression before proposing axes; cycle-8 first EXPLORATION cannot launch until the code-state drift root cause is identified and the /132 RE-ANCHOR verdict is reconciled.
- **Probability estimate**: **~20%**. Plausible but not modal. The /127/129/130 features are flag-gated; default-DISABLED state should preserve /121 trade roster. The non-zero probability reflects the ~5+ infrastructure changes across cycle-7 (any one of which could have an unintended side-effect at the runner-config level).

**Mode C (CONFIRMATION-RE-ANCHOR — F2 fails methodology floor)**: PBO ≥ 0.40 OR PSR ≤ 0.95 OR frac_positive_paths < 0.55.
- **Verdict**: **CONFIRMATION-RE-ANCHOR on methodology floor**.
- **Action**: file RE-ANCHOR diary on methodology floor; investigate CPCV/PBO/PSR computation drift (less likely than F1 regression since these are architecture-independent quantities under the unified 10-seed ensemble).
- **BASELINE_V3.md action**: downgrade BASELINE_V3.md to reflect /132 methodology measurement (methodology gates are foundational; if they don't hold, prior /121 results are also implicitly questionable).
- **Probability estimate**: **<5%**. /121 cleared all three methodology gates with significant margin (PBO 0.1278 vs 0.40 threshold; PSR 1.0 vs 0.95; frac_positive_paths 0.6444 vs 0.55). The methodology computation is largely architecture-independent under unified 10-seed; regression here would imply a deep code-path corruption.

**Mode D (PARTIAL-PASS — F1 PASSES on one leg only)**: /132 multi-seed mean IS ≥ +1.0 XOR OOS ≥ +0.8 (one passes, the other fails).
- **Verdict**: **CONFIRMATION-RE-ANCHOR-PARTIAL** — investigate axis-asymmetric drift.
- **Action**: file RE-ANCHOR-PARTIAL diary; investigate which leg failed and whether the failure pattern correlates with any specific cycle-7 infrastructure change. If IS only fails → likely related to training-time code path (Optuna/feature computation/labeling). If OOS only fails → likely related to test-time code path (RiskV2 gate evaluation/risk primitive interaction).
- **BASELINE_V3.md action**: keep at /121 with the partial-pass documented; cycle-8 design must address the asymmetric drift.
- **Probability estimate**: **~5%**. Possible but not modal. Asymmetric drift would imply a code-path side-effect that only activates in one of the IS/OOS evaluation windows.

**Aggregate modal expectation**: **Mode A (~70%) is the modal verdict**. /121 architecture should re-validate cleanly under current code state; the loose-tolerance F1 absorbs incidental code drift; the cycle-7 infrastructure is flag-gated to DISABLED. Mode B (~20%) reflects realistic infrastructure-side-effect uncertainty given 5+ merged changes across cycle-7. Mode C + D (~5% each) reflect deeper-corruption tails.

---

## Section 8 — LOCKED Acceptance Criteria (first-match-wins MERGE / NO-MERGE)

Acceptance gates are evaluated in the order below. First-match-wins; the first failed gate determines the verdict.

### 8.1 — Hard methodology gates (any FAIL → CONFIRMATION-RE-ANCHOR on methodology floor)

| Gate | Threshold | /121 reference | /132 PASS condition |
|---|---|---:|---|
| Gate 5 PBO | < 0.40 | 0.1278 | /132 PBO mean < 0.40 |
| Gate 6 PSR | > 0.95 | 1.0 | /132 PSR > 0.95 |
| Gate 10-CPCV | ≥ 0.55 frac_positive_paths | 0.6444 | /132 ≥ 0.55 |
| OOS/IS Sharpe ratio (Gate 3) | ≥ 0.5 | 0.7386 | /132 ratio ≥ 0.5 |

### 8.2 — Pre-committed falsifiers (each maps to a CONFIRMATION verdict per the Section 7 mode table)

| Falsifier | PASS condition (recap) |
|---|---|
| **F1 loose-tolerance BOTH-must-improve** | /132 multi-seed IS ≥ **+1.0** AND OOS ≥ **+0.8** |
| **F2 hard methodology gates** | PBO < 0.40 AND PSR > 0.95 AND frac_positive_paths ≥ 0.55 |

### 8.3 — First-match-wins decision tree

```
1. If F2 hard methodology gates FAIL → CONFIRMATION-RE-ANCHOR (methodology floor breach).
     Mode C. Investigate CPCV/PBO/PSR computation drift.
     BASELINE_V3.md DOWNGRADE candidate.
2. If F1 loose-tolerance BOTH-must-improve FAILS on EITHER leg →
     Sub-branch:
     a. If BOTH legs fail (IS < +1.0 AND OOS < +0.8) → CONFIRMATION-RE-ANCHOR (Mode B).
          Investigate code-state drift across /127/129/130 infrastructure.
          BASELINE_V3.md DOWNGRADE candidate; cycle-8 design blocked.
     b. If ONE leg fails (IS XOR OOS below threshold) → CONFIRMATION-RE-ANCHOR-PARTIAL (Mode D).
          Investigate asymmetric code-path side-effect.
          BASELINE_V3.md UNCHANGED but partial-pass documented; cycle-8 design must address.
3. If F1 PASSES BOTH LEGS AND F2 PASSES →
     CONFIRMATION-VALIDATION-PASS (Mode A).
     /121 architecture re-validated.
     BASELINE_V3.md UNCHANGED at /121 canonical (`v0.v3-121`).
     Tag v0.v3-132.
     Cycle-7 closes at /121 baseline; ZERO ingredients merged this cycle.
     Cycle-8 design begins from /121 with cohort-AND-frequency-shape constraint binding.
```

### 8.4 — BASELINE_V3.md update policy

Per `feedback_v3_strict_both_is_oos_baseline.md` + /131 closure-reconciliation memo Section 5.2:
- **BASELINE_V3.md is UNCHANGED at /121 on Mode A PASS** (this is the RE-VALIDATION case — not a new MERGE candidate; no STRICTLY-BETTER claim to make over /121).
- **BASELINE_V3.md DOWNGRADE on Mode B FAIL** (only if /132 multi-seed mean falls materially below /121 ADJUSTED reference IS ≈ +1.06 / OOS ≈ +0.85 per /131 Section 5.3).
- **BASELINE_V3.md UNCHANGED on Mode B borderline FAIL** (if /132 falls between the loose-tolerance F1 thresholds but at-or-above the ADJUSTED reference): keep /121 baseline with regression documented as Reproducibility Stamp note.
- **BASELINE_V3.md DOWNGRADE on Mode C FAIL** (methodology gates are foundational).
- **BASELINE_V3.md UNCHANGED on Mode D PARTIAL** with partial-pass documented.

Aspirational hard merge gates (Sharpe ≥ +1.0 floors at /121 already cleared, DSR > 0.95 informational, top-symbol ≤ 30%, OOS trades ≥ 130) inform future-iteration priorities but do NOT block /132 re-validation pass per `feedback_v3_baseline_update_policy.md` (the relaxed policy: hard-blocking gates retained are Gate 3, Gate 6, Gate 10).

### 8.5 — Critic Phase 7.5 review

Per ITERATION_PLAN_8H_V3.md, the Critic's 8 mandatory checks + OVERALL=MERGE/BLOCK adjudicates after Engineer's Phase 6 commit. The Critic's OVERALL verdict is FINAL — Section 8.3's decision tree is the QR's first-match-wins read of the Phase 7 results; the Critic may OVERRIDE on substantive grounds.

**Critic check focus areas at /132 (re-validation context)**:
- Check 1 (Look-Ahead): verify walk-forward POST-FIX at `e149e9d` is preserved at /132 head; verify NO new code path violates past-only discipline (the /127/129/130 infrastructure being DISABLED reduces but does not eliminate the surface area).
- Check 2 (Embargo): verify CPCV embargo=27 candles + REQUIRED_GAP=66 unchanged from /121.
- Check 3 (DSR/PBO/PSR): verify methodology gate computation under unified architecture is bit-identical to /121's; flag any drift in cell-level invariants (PBO 0.1278, frac_positive_paths 0.6444 from /121 baseline).
- Check 4 (IC): N/A — no new feature at /132.
- Check 5 (ADF): N/A — no new feature at /132.
- Check 6 (Pareto): verify multi-seed Pareto frontier shape vs /121's; flag any seed-dominance pattern that did not appear at /121.
- Check 7 (Reproducibility): verify the /121 → /132 hand-off chain via Reproducibility Stamp (this brief SHA + setup commit SHA + engineering report SHA + reports-v3/iteration_v3-132/ presence).
- Check 8 (Hypothesis-Implementation Alignment): verify the /132 hypothesis (Section 1) is the literal RE-VALIDATION operationalization, NOT a re-framing toward bundle assembly.

---

## Section 9 — Library Stack + Reproducibility

UNCHANGED from /121 canonical:

- `lightgbm == 4.6.0`
- `optuna == 4.8.0`
- `numpy == 2.2.6`
- `pandas == 3.0.0`
- `scikit-learn == 1.8.0`
- `scipy == 1.17.0`
- `statsmodels == 0.14.6`
- `pyarrow == 23.0.1`
- `mlfinlab == 1.4` (primary)
- `pypbo`
- `fracdiff >= 0.10`

Run invocation: `uv run python run_baseline_v3.py --confirmation --n-trials 35 --clean-oof --seeds 2`.

Determinism: ENSEMBLE_SEEDS pinned to the 10-tuple `(191664963, 1662057957, 1405681631, 942484272, 929893137, 33158374, 1465339467, 1273345680, 115579757, 1952249162)` per `feedback_explicit_feature_columns.md` + BASELINE_V3.md. `V3_FEATURE_COLUMNS_TOP_N` (14 features at /121 canonical) explicit-list-pass to `LightGbmStrategy` per `feedback_explicit_feature_columns.md`.

Reproducibility stamp (to be filled by Phase 6 Engineer):
- Setup commit SHA: TBD (this commit cycle — ITERATION_LABEL flip + pre-flight verification)
- Brief SHA: TBD (this brief)
- Engineering report commit SHA: TBD (Phase 6)
- Critic FINAL SHA: TBD (Phase 7.5)
- `data/` extent at run time: TBD
- `reports-v3/iteration_v3-132/`: TBD
- BASELINE_V3.md update SHA: N/A on Mode A PASS (UNCHANGED at /121); TBD on Mode B/C/D
- Tag: `v0.v3-132` set on /132 closeout commit (cycle-7 closure milestone)
- Wall-clock: TBD (target ~3.2h per /121; HARD CAP 6h)
- Hardware: WSL2 Linux 6.6.114.1-microsoft-standard-WSL2

---

## Section 10 — QR Audit Trail (Phase 1-5)

### 10.1 — Why /132 exists and what it is NOT

Per /131 closure-reconciliation memo Section 5 + /130 Critic FINAL `d33cc2e` Recommendation 2: /132 is the MULTI-SEED VALIDATION of /121-canonical, NOT bundle assembly. The /131 closure-reconciliation memo (commit `2d4f367`, tag `v0.v3-131`) LOCKED the /132 spec; this brief implements that LOCKED spec verbatim.

**/132 IS**:
- A pure baseline RE-VALIDATION of the /121 canonical architecture at the same unified 10-seed CONFIRMATION budget that produced /121's headline metrics.
- The cycle-7 closure event — slot 11 of cycle-7 per the /131 closure-reconciliation memo + `feedback_v3_strict_10_to_1_cadence.md` STRICT 10:1 cadence with separate CONFIRMATION.
- A reproducibility test for /121 under current code state (post /127 brake + /129 continuous-scaling + /130 bar-interval support + ITERATION_LABEL + _TeeLogger infrastructure merged across cycle-7).
- The cycle-7 closeout decision point: PASS → cycle-7 closes at /121 with ZERO ingredients merged; FAIL → cycle-7 closes with a CONFIRMATION-RE-ANCHOR diary + investigation of code-state drift.

**/132 IS NOT**:
- A bundle assembly of any /122–/131 cycle-7 EXPLORATION components. Per /131 closure-reconciliation memo Section 1.1: 8/9 NEGATIVE-catastrophic + 1/9 NEGATIVE-INERT + 0/9 PROMISING. ZERO components to bundle.
- A new axis exploration. Per `feedback_v3_strict_10_to_1_cadence.md`: cycle-7 EXPLORATION cadence COMPLETE at /131 closure-reconciliation memo; cycle-8 EXPLORATION begins at iter-v3/133 (slot 1 of cycle-8).
- A baseline-improvement candidate. There is no STRICTLY-BETTER claim being made over /121; the goal is reproducibility verification, not edge accretion.
- A methodology innovation. The methodology stack (CPCV, PBO, PSR, DSR_relative_b4) is UNCHANGED from /121.

### 10.2 — Provenance of every numerical value in Sections 1-9

| Numerical value | Source | Provenance |
|---|---|---|
| /121 IS monthly Sharpe +1.3108 | BASELINE_V3.md (SHA `b0576df`) | Current canonical anchor; tag v0.v3-121 |
| /121 OOS monthly Sharpe +0.9682 | BASELINE_V3.md | Current canonical anchor |
| /121 OOS/IS ratio 0.7386 | BASELINE_V3.md | Current canonical reference |
| /121 PBO 0.1278 | BASELINE_V3.md | Methodology gate reference |
| /121 PSR 1.0 | BASELINE_V3.md | Methodology gate reference |
| /121 frac_positive_paths 0.6444 | BASELINE_V3.md | Methodology gate reference |
| /121 OOS trades 98 | BASELINE_V3.md | Trade-rate informational reference |
| /121 IS MaxDD 26.38% | BASELINE_V3.md | Risk envelope reference |
| /121 OOS MaxDD 25.70% | BASELINE_V3.md | Risk envelope reference |
| /121 OOS Calmar 1.4843 | BASELINE_V3.md | Risk-adjusted return reference |
| /121 BCH OOS weighted_pnl +35.83 | BASELINE_V3.md + `reports-v3/iteration_v3-121/out_of_sample/per_symbol.csv` | F5-analog per-symbol reference |
| /121 LDO OOS weighted_pnl −2.89 | BASELINE_V3.md + per_symbol.csv | F5-analog per-symbol reference |
| /121 TRX OOS weighted_pnl +5.21 | BASELINE_V3.md + per_symbol.csv | F5-analog per-symbol reference |
| /059 anchor IS +1.0894, OOS +0.5791 | BASELINE_V3.md (prior canonical retired 2026-05-20) | Cycle-6 closure event Δ reference |
| F1 loose-tolerance IS ≥ +1.0 | /131 closure-reconciliation memo Section 5.2 + 5.3 | Pre-committed; cannot be renegotiated |
| F1 loose-tolerance OOS ≥ +0.8 | /131 closure-reconciliation memo Section 5.2 + 5.3 | Pre-committed; cannot be renegotiated |
| F1 IS slippage budget −0.31 | /131 closure-reconciliation memo Section 5.3 | = +1.3108 − +1.0 = +0.31 slippage allowance |
| F1 OOS slippage budget −0.17 | /131 closure-reconciliation memo Section 5.3 | = +0.9682 − +0.8 = +0.17 slippage allowance |
| F2 PBO < 0.40 threshold | BASELINE_V3.md | v3 methodology floor |
| F2 PSR > 0.95 threshold | BASELINE_V3.md | v3 methodology floor |
| F2 frac_positive_paths ≥ 0.55 threshold | BASELINE_V3.md | v3 methodology floor (Gate 10-CPCV) |
| /121 ADJUSTED IS ≈ +1.06 | /131 closure-reconciliation memo Section 5.3 | Material-regression downgrade reference |
| /121 ADJUSTED OOS ≈ +0.85 | /131 closure-reconciliation memo Section 5.3 | Material-regression downgrade reference |
| Cycle-7 EXPLORATION catalog (8/9 catastrophic + 1/9 INERT) | /131 closure-reconciliation memo Section 1.1 | Empirical no-bundling justification |
| /116 source SHA `52444c9` | BASELINE_V3.md Reproducibility Stamp inherited infrastructure | Component A source EDA reference |
| /121 baseline update SHA `b0576df` | BASELINE_V3.md Reproducibility Stamp | Current canonical anchor commit |
| /121 tag `v0.v3-121` | BASELINE_V3.md Baseline History | Current canonical anchor tag |
| /131 closure-reconciliation commit `2d4f367` | git log + this brief's predecessor declaration | Pre-/132 anchor commit |
| /131 tag `v0.v3-131` | git tag --list | Pre-/132 anchor tag |
| /130 Critic FINAL SHA `d33cc2e` | git log + /131 closure-reconciliation memo authorization section | /132 spec authorization commit |
| Cycle-7 catastrophic IS Δ −2.61 at /130 | /131 closure-reconciliation memo Section 1.1 + 2.2 | Bar-interval axis CLOSED reference |
| BASELINE_V3.md update policy (relaxed) | `feedback_v3_baseline_update_policy.md` | Hard-blocking gates: Gate 3, 6, 10 only |
| STRICT 10:1 cadence | `feedback_v3_strict_10_to_1_cadence.md` | Cycle-7 closure structure |

### 10.3 — What this brief does NOT contain

- NO new EDA (per `feedback_v3_axis_selection_quant_discipline.md` for CONFIRMATION-class re-validation iterations + /131 closure-reconciliation memo Section 5 LOCKED no-new-EDA mandate).
- NO new hand-chosen parameters (per Section 0).
- NO new feature primitives.
- NO new code paths (only ITERATION_LABEL flip + pre-flight verification).
- NO new RiskV2 primitives.
- NO new symbols, labeling primitives, candle frequencies (8h carries forward), or model architectures.
- NO renegotiation of /131 closure-reconciliation memo Section 5 LOCKED spec or /130 Critic FINAL `d33cc2e` Recommendation 2.
- NO methodology innovation. /132 is purely a multi-seed RE-VALIDATION of /121 canonical.
- NO bundle assembly. Per /131 closure-reconciliation memo Section 1.1: 0 PROMISING cycle-7 components to bundle.
- NO STRICTLY-BETTER claim over /121. The goal is reproducibility verification, not edge accretion.

### 10.4 — Out-of-scope items deferred to cycle-8

- iter-v3/133 = cycle-8 EXPLORATION axis-1, QR-selected per `feedback_v3_axis_selection_quant_discipline.md` after /132 closes.
- Per `feedback_v3_strict_10_to_1_cadence.md`: standard 10/10 + 1 CONFIRMATION cadence resumes from /133 regardless of /132 outcome (Mode A PASS = clean cycle-8 start; Mode B/C/D RE-ANCHOR = cycle-8 axis briefing blocked until regression resolved).
- Per /131 closure-reconciliation memo Section 8: cycle-8 axis menu structurally reformulates post-/132. The cohort-AND-frequency-shape terminal finding sets binding constraints:
  - Mandatory brief Section 0.6 "Architecture-Family Justification" at cycle-8 first EXPLORATION arguing why the proposed axis is NOT in any of the 3 closed channels (cohort-shape, frequency-shape, Optuna-trajectory-shift).
  - Viable cycle-8 axis families: WHOLLY-NEW model architecture at CONFIRMATION budget; WHOLLY-NEW labeling architecture at CONFIRMATION budget; CONFIRMATION-budget-first design (process innovation breaking the 10:1 cadence's implicit single-seed-EXPLORATION assumption); explicit acknowledgment that /121 is practical edge ceiling under current workflow.
- /132's BASELINE_V3.md update outcome determines cycle-8 anchor:
  - IF /132 Mode A PASS → cycle-8 axis menu anchors against /121 canonical (UNCHANGED).
  - IF /132 Mode B/C DOWNGRADE → cycle-8 axis menu anchors against the new (downgraded) /132 baseline; cycle-8 first EXPLORATION must address the regression root cause.
  - IF /132 Mode D PARTIAL → cycle-8 axis menu anchors against /121 canonical but with the partial-pass regression documented as an outstanding constraint.

---

## END OF BRIEF
