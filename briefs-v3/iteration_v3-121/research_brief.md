# iter-v3/121-METHODOLOGY — Research Brief (CYCLE-7 BOOTSTRAP — SINGLE-COMPONENT /116 Component A 10-seed isolation)

**Branch**: `iteration-v3/121`
**EDA cross-reference SHAs**: `52444c9` (iter-v3/116 EDA — RULE-layer `no_confirm` exit primitive)
**Setup commit SHA**: TBD (single commit per dispatch — knob flips + V3_FEATURE_COLUMNS_TOP_N revert 15 → 14)
**Iteration type**: **CYCLE-7 BOOTSTRAP / METHODOLOGY**. Analogous to iter-v3/018 BOOTSTRAP precedent (`feedback_v3_iter018_baseline_bootstrap.md`). **NOT counted toward cycle-7 10/10 EXPLORATION cadence.**
**Predecessor**: iter-v3/120 — CONFIRMATION-NO-MERGE per F3+F4 binding; Component B (C6 `ret5d_signed_tbi`) DROPPED; cycle 6 closes with 0 ingredients merged but the all-time v3 OOS monthly Sharpe (+1.6946) recorded at the bundle level. Per /120 Critic FINAL `a49dd17` + diary §9 directive, the F3-DROP branch requires standalone evaluation of Component A at full 10-seed CONFIRMATION before cycle-6 final closure.
**Authorization**: /120 brief Section 8.4 branch 3 + diary §9.1 explicitly pre-committed "/116-only re-evaluation" as a binding outcome path; /120 Critic FINAL VERDICT CONCUR on QR Round-2 Q1 + Q5 establishes /121-METHODOLOGY as authorized cycle-7 BOOTSTRAP.

---

## Section 0 — Hand-chosen Parameters Provenance

Per `feedback_v3_brief_parameter_provenance.md`: every hand-chosen parameter must name its EXPLORATION source iteration + the committed analysis table + an auditable IS-only temporal fence.

**Component A (RULE-layer `no_confirm`) — three hand-chosen scalars inherited unchanged from /116 + /120 (NO NEW parameters introduced at /121-METHODOLOGY):**

| Parameter | Value | Source iteration | EDA table | Provenance |
|---|---:|---|---|---|
| `no_confirm_trigger_atr` | **0.50** | /116 (declared) → /120 (CONFIRMATION-locked) | `analysis/iteration_v3-116/T7_early_exit_grid.csv` row `(0.50, 4)` | Hand-chosen at /116 brief Section 0. Round-number midpoint of 16-cell grid `[0.25, 0.50, 0.75, 1.00] × [2, 3, 4, 5]`. Only cell with positive IS Sharpe lift on all 3 symbols (BCH +0.1253, LDO +0.0068, TRX +0.0415). Inherited UNCHANGED at /120 + /121. |
| `no_confirm_k_candles` | **4** | /116 (declared) → /120 (CONFIRMATION-locked) | `analysis/iteration_v3-116/T7_early_exit_grid.csv` row `(0.50, 4)` | Hand-chosen at /116 brief Section 0. Roughly median holding time of static triple-barrier book (~32 hours at 8h interval) — first-third of 21-candle timeout. Inherited UNCHANGED at /120 + /121. |
| `enable_no_confirm_exit` | **True** | /120 (re-enabled) → /121 (inherited) | n/a | Re-enables /116 primitive (currently True on /120 head state, the branching head). No new hand-chosen scalar. |

**Component B — REMOVED at /121-METHODOLOGY**. Per /120 F3 pre-commitment + diary §6 Q4: Component B (C6 `ret5d_signed_tbi`) DROPPED. `V3_FEATURE_COLUMNS_TOP_N` reverts to /059's 14-feature stack. NO Component B parameters at /121.

**No NEW hand-chosen scalars at /121-METHODOLOGY.** The runner-config diff vs /120 is exactly TWO changes: (1) revert `V3_FEATURE_COLUMNS_TOP_N` 15 → 14 (drop `ret5d_signed_tbi` from index 14); (2) `ITERATION_LABEL` / `MODEL_SPECS` prefix `"v3-120"` → `"v3-121"`. Knob flips for Component A remain at /120's setting.

**Auditable temporal fence**:
- /116 EDA SHA `52444c9` — every script asserts `close_time < OOS_CUTOFF_MS = 1742774400000`.
- Per `feedback_v3_axis_selection_quant_discipline.md`, CONFIRMATION-class iterations may rely on EXPLORATION EDAs. No new EDA is mandated at /121-METHODOLOGY. The /116 EDA + the /120 engineering report's Jaccard finding (committed `briefs-v3/iteration_v3-120/qr_response.md`) constitute the QR's audit trail.

---

## Section 0.5 — Iteration Type Declaration

- **TYPE**: **CYCLE-7 BOOTSTRAP / METHODOLOGY** (NOT counted toward cycle-7 10/10 EXPLORATION cadence).
- **Precedent**: iter-v3/018 BOOTSTRAP (`feedback_v3_iter018_baseline_bootstrap.md`) — a one-time CONFIRMATION-class run executed mid-cadence to establish or revise a baseline at full multi-seed budget without consuming an EXPLORATION slot. /121 is analogous: it is the standalone 10-seed evaluation of an EXPLORATION-PROMISING-MECHANICAL primitive (Component A at /116) that the cycle-6 CONFIRMATION at /120 left unevaluated when Component B was bundled.
- **Cycle accounting**: cycle-6 closeout state (per diary §11) is "10/10 EXPLORATIONs + 1 CONFIRMATION (/120) complete; 0 ingredients merged". /121-METHODOLOGY resolves the F3-DROP attribution gap. After /121, cycle-7 begins at iter-v3/122 = EXPLORATION axis-1 (slot 1 of 10) regardless of /121 outcome.
- **Run mode**: default CONFIRMATION (NO `--exploration` flag → `ENSEMBLE_SIZE = CONFIRMATION_ENSEMBLE_SIZE = 10`).
- **Optuna budget**: `--n-trials 35` per `feedback_v3_confirmation_n_trials_35.md`. Total trials = 35 × 3 sym × 10 seeds = **1050** — same envelope as /059 + /120.
- **Wall-clock target**: ~3.0–3.6h (per /059 = 3.60h + /120 = 3.14h baselines); HARD CAP **6h** per `feedback_v3_cadence_discipline.md`.
- **Runner invocation**: `uv run python run_baseline_v3.py --n-trials 35 --clean-oof` (no `--exploration`, no `--seeds`).
- **Anchor (canonical baseline)**: `v0.v3-059` (BASELINE_V3.md) — IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791** (10-seed CONFIRMATION). BOTH-must-improve target per `feedback_v3_strict_both_is_oos_baseline.md`.
- **Cross-reference**: bundle at /120 produced IS **+0.7293** / OOS **+1.6946** (all-time v3 OOS record). /121 isolates the Component A contribution.

---

## Section 1 — Testable Hypothesis (ONE sentence)

> Component A alone (`enable_no_confirm_exit=True`, `no_confirm_trigger_atr=0.50`, `no_confirm_k_candles=4`) on /059's canonical 14-feature stack (`V3_FEATURE_COLUMNS_TOP_N` reverted from /120's 15 → 14; C6 `ret5d_signed_tbi` removed) at full 10-seed CONFIRMATION carries strictly-accretive lift on /059 — producing IS monthly Sharpe ≥ **+1.0894** AND OOS monthly Sharpe ≥ **+0.5791** (BOTH-must-improve) while clearing the F2 IS regime-cost floor (IS ≥ **+0.79**) and the hard methodology gates (PBO < 0.40, PSR > 0.95, frac_positive_paths ≥ 0.55) — OR the cycle-6 all-time OOS record at /120 was driven by the multi-mechanism interaction effect rather than Component A standalone, in which case Component A is RULE-LAYER-EVALUATED-NEGATIVE-AT-MULTISEED and cycle 6 closes with 0 ingredients merged.

---

## Section 2 — IS-Only Numerical Evidence (CROSS-REFERENCE only; NO new EDA)

Per `feedback_v3_axis_selection_quant_discipline.md`: CONFIRMATION-class iterations may rely on EXPLORATION EDAs.

### Section 2.1 — Component A source EDA (/116 SHA `52444c9`)

`analysis/iteration_v3-116/` — 10 result tables. Load-bearing tables:

| Table | Headline finding | /121 relevance |
|---|---|---|
| `T7_early_exit_grid.csv` (16 cells × 3 sym) | `(trigger=0.50, K=4)` is the only cell with positive IS Sharpe lift across all 3 symbols (BCH +0.1253, LDO +0.0068, TRX +0.0415) | Justifies the inherited `(0.50, 4)` parameters |
| `T8_cuts_losers.csv` (48 cells × 3 sym) | Static-direction counterfactual: rule cuts modestly-below-average winners-held-to-barrier (BCH +3.75%, LDO +2.90%, TRX +3.26%) NOT losers — but the EDA's static frame mis-represents the production slot-freeing-cascade mechanism (per /116 diary §2.3) | Documents the regime-cost mechanism F2 is calibrated against |
| `T4_go_nogo_verdict.csv` row C | Axis C NO-GO on formal gates; chosen on residual-uncertainty criterion | Documents /116 PROMISING-MECHANICAL classification |

### Section 2.2 — /116 EXPLORATION single-seed reference (the F2 calibration anchor)

Per /116 EXPLORATION (3-seed mode, n_trials=35) — `reports-v3/iteration_v3-116/comparison.csv`:

| Metric | /060 anchor | /116 EXPLORATION | Δ vs /060 |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.8325 | **+0.6246** | **−0.2079** |
| OOS monthly Sharpe | +0.1403 | **+1.1089** | **+0.9686** |

Component A single-seed IS-drop of **−0.21** vs /060 is the empirical anchor for the F2 +0.79 IS regime-cost floor (= /059 IS +1.0894 − 0.30; the floor doubles the single-seed drop to bound multi-seed compression risk).

### Section 2.3 — /120 bundle vs Component-A-alone — the attribution gap /121 resolves

Per /120 engineering report (`briefs-v3/iteration_v3-120/engineering_report.md`) + QR Round-2 Q3 Jaccard finding (`briefs-v3/iteration_v3-120/qr_response.md`):

| Reference | IS Sharpe | OOS Sharpe | Mode |
|---|---:|---:|---|
| /059 canonical (anchor) | +1.0894 | +0.5791 | 10-seed CONFIRMATION |
| /116 Component A (single-seed EXPLORATION) | +0.6246 | +1.1089 | 3-seed EXPLORATION (n_trials=35) |
| /119 Component B (single-seed EXPLORATION) | +0.8492 | +0.8420 | 3-seed EXPLORATION (n_trials=35) |
| /120 bundle A+B (multi-seed CONFIRMATION) | **+0.7293** | **+1.6946** | 10-seed CONFIRMATION (n_trials=35) |
| /121 Component A multi-seed (TO BE OBSERVED) | TBD | TBD | 10-seed CONFIRMATION (n_trials=35) |

**Jaccard set-comparison evidence (from /120 QR Round-2 Q3, committed `briefs-v3/iteration_v3-120/qr_response.md`)**: /120 bundle OOS trade roster vs /116-alone OOS trade roster = **Jaccard 0.48** (66 shared trades / 96 bundle OOS trades; **30 trades unique to bundle**). The bundle was NOT a near-duplicate of /116-alone; the 30 unique trades existed because the FEATURE-layer split-budget shift (Component B) opened entry decisions that the RULE-layer early-exit channel (Component A) then operated on. This is the genuine multi-mechanism interaction effect Q3 confirmed.

**/121 resolves the attribution gap empirically**: by isolating Component A at 10-seed, the result distinguishes:
- **Branch A (Component A standalone-positive)**: /121 multi-seed OOS materially clears /059 (+0.5791) at multi-seed → Component A is a viable single-mechanism strictly-accretive primitive; PARTIAL-MERGE candidate.
- **Branch B (Component A standalone-neutral-or-negative, bundle's OOS lift was interaction-driven)**: /121 multi-seed OOS at-or-below /059 → the bundle's all-time OOS record at /120 was the multi-mechanism interaction, NOT a property of Component A alone; cycle-6 closes with 0 ingredients merged.

---

## Section 3 — Proposed Changes (SINGLE-COMPONENT vs /059 canonical)

Bundle composition at /121-METHODOLOGY is **SINGLE-COMPONENT** — Component A only; Component B reverted.

### Sub-fix 1 — Component A: `no_confirm` exit primitive REMAINS enabled

`enable_no_confirm_exit=True` at `run_baseline_v3.py:2036` (the value already set at /120 head state). No additional flip — /121 inherits the bundle's runner-config Component A state.

`no_confirm_trigger_atr=0.50`, `no_confirm_k_candles=4` — inherited UNCHANGED.

Pre-flight assertions at `run_baseline_v3.py:1145–1170` + `:2950–2995` REMAIN at the /120 specification for Component A:
- Pre-flight accretion-guard expected tuple `(True, 0.50, 4)` — UNCHANGED.
- Pre-flight Component A assertion (line 2957) `enable_no_confirm_exit is True` — UNCHANGED.

### Sub-fix 2 — Component B: REVERT C6 `ret5d_signed_tbi` removal from `V3_FEATURE_COLUMNS_TOP_N`

The 15-feature `V3_FEATURE_COLUMNS_TOP_N` (with `ret5d_signed_tbi` at index 14) reverts to the 14-feature /059 anchor.

**Edit at `src/crypto_trade/features_v3/__init__.py` (line 178)**:
- REMOVE the 15th element `"ret5d_signed_tbi"` from the `V3_FEATURE_COLUMNS_TOP_N` tuple.
- New `len(V3_FEATURE_COLUMNS_TOP_N) == 14`.

**`compute_ret5d_signed_tbi` function REMAINS in `src/crypto_trade/features_v3/engineered_v3.py`** (line 834) and the call site at line 1055 (`df = compute_ret5d_signed_tbi(df)`) REMAINS. Per the /118 + /119 precedent for inert / dropped features: keep the implementation as code-museum reference but exclude from the active feature list. The export at line 1204 in `__all__` REMAINS.

Rationale: removing the function would require feature-engineering test updates and is unnecessary at a methodology-bootstrap iteration that may want to reintroduce the feature in a different stack composition in a future cycle.

### Sub-fix 3 — Update pre-flight Component B assertion (line 2983) from PRESENT to ABSENT

The /120 head state asserts `"ret5d_signed_tbi" in V3_FEATURE_COLUMNS_TOP_N`. At /121, this must INVERT to assert `"ret5d_signed_tbi" not in V3_FEATURE_COLUMNS_TOP_N`.

**Edit at `run_baseline_v3.py:2983–2996`**:
- ASSERTION `assert "ret5d_signed_tbi" in V3_FEATURE_COLUMNS_TOP_N` → `assert "ret5d_signed_tbi" not in V3_FEATURE_COLUMNS_TOP_N`.
- ASSERTION `assert len(V3_FEATURE_COLUMNS_TOP_N) == 15` → `assert len(V3_FEATURE_COLUMNS_TOP_N) == 14`.
- Update the pre-flight log message from "Component B preserved" semantics to "Component B REVERTED for /121-METHODOLOGY single-mechanism isolation" semantics.

### Sub-fix 4 — Runner setup housekeeping

- `ITERATION_LABEL` `"v3-120"` → `"v3-121"`.
- `MODEL_SPECS` prefix `"v3-120-..."` → `"v3-121-..."` (per the runner's MODEL_SPECS construction).

### Sub-fix 5 — CONFIRMATION-mode flag (no `--exploration`)

UNCHANGED from /120. Runner invocation:

```bash
uv run python run_baseline_v3.py --n-trials 35 --clean-oof
```

`ENSEMBLE_SIZE = CONFIRMATION_ENSEMBLE_SIZE = 10` (per the runner default at line 96; assertion at line 394 enforces this).

### Section 3.5 — Code-change manifest

**NO new feature implementation. NO new function. NO new test (beyond pre-flight inversion).** Only:

1. **Feature-list revert** — `V3_FEATURE_COLUMNS_TOP_N` tuple at `src/crypto_trade/features_v3/__init__.py:178` drops the 15th element `"ret5d_signed_tbi"`. New length 14.
2. **Pre-flight C6-PRESENT → C6-ABSENT inversion** — `run_baseline_v3.py:2983–2996`. Two assertion inversions + log message update.
3. **`ITERATION_LABEL` + `MODEL_SPECS` prefix update** — `"v3-120"` → `"v3-121"`.
4. **Brief commit** — this file at `briefs-v3/iteration_v3-121/research_brief.md`.

**Knobs UNCHANGED vs /059 canonical except for Sub-fixes 1–2**:
- V3_MODELS = BCHUSDT, LDOUSDT, TRXUSDT
- V3_FEATURE_COLUMNS_TOP_N (14) — REVERTED to /059 anchor (Sub-fix 2)
- ATR multipliers — (atr_tp=2.0, atr_sl=1.0); V3_ATR_MULTIPLIERS_PER_SYMBOL = {} empty
- 7-primitive RiskV2 stack — vol scaling, ADX 20.0, Hurst regime, zscore 2.0, low-vol filter, hit-rate (DISABLED), BTC trend kill (15.0%); regime gate, per-symbol cap, per-symbol drawdown brake all DISABLED
- Triple-barrier labeling — 21-candle (10080-min) timeout
- ENSEMBLE_SIZE = 10 (unified 10-seed lineage `(191664963, 1662057957, 1405681631, 942484272, 929893137, 33158374, 1465339467, 1273345680, 115579757, 1952249162)`)
- CPCV n_paths = 45, embargo = 27, REQUIRED_GAP = 66
- Walk-forward POST-FIX at `e149e9d`
- Optuna `n_jobs=1`, `colsample_bytree` Optuna-tuned (NOT hardcoded)
- Sacred constants UNCHANGED: `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24`

**Differences vs /120 setup**:
- `V3_FEATURE_COLUMNS_TOP_N` length 14 (vs 15) — Sub-fix 2.
- Pre-flight Component B assertion direction inverted — Sub-fix 3.
- ITERATION_LABEL prefix — Sub-fix 4.

---

## Section 4 — Pre-registered Falsifiers (BINDING — non-negotiable)

Five falsifiers carry forward from /120's binding pre-commitments + /116's Critic Recs. Pre-registered in numerical form; cannot be renegotiated post-hoc.

### F1 — BOTH-must-improve (BINDING — the BASELINE_V3.md update gate)

Per `feedback_v3_strict_both_is_oos_baseline.md` (RELAXED FROM `feedback_v3_baseline_update_policy.md`): BASELINE_V3.md updates ONLY if /121 multi-seed mean clears BOTH IS and OOS legs of /059.

**Numerical threshold**:
- IS multi-seed mean ≥ **+1.0894** AND
- OOS multi-seed mean ≥ **+0.5791**.

**F1 firing direction**: if EITHER leg fails (IS < +1.0894 OR OOS < +0.5791), F1 FAILS → BASELINE_V3.md UNCHANGED at /059 (irrespective of methodology gates and other falsifiers).

### F2 — IS regime-cost floor (BINDING — carried forward from /120 F4 + /116 Critic Rec 2)

Per /116 Critic Rec 2 + /120 brief Section 4 + diary §3.5 mechanism analysis (BCH IS net_pnl_pct collapsed −69.31 pct at /120 — the no_confirm rule cuts trades that would recover to TP in bear/chop regimes; this is the OOS-dual-channel-cost mechanism in the IS leg).

**Numerical threshold**: bundle multi-seed IS Sharpe ≥ **+0.79** (= /059 IS +1.0894 − 0.30).

**F2 firing direction**: if /121 multi-seed mean IS < +0.79, F2 FAILS → NO-MERGE on the IS-floor leg.

**Rationale for /059 IS − 0.30 floor (NOT the looser −0.50 = +0.59 option)**: per /120 brief Section 4 Falsifier 4. The /116 single-seed IS drop was −0.21 vs /060; doubling that to −0.30 vs /059 bounds multi-seed compression risk while retaining enough IS discipline to refuse a model where the no_confirm channel has materially broken the IS signal. **This is the floor that fired at /120 by 0.0607**; /121's empirical answer to whether Component A alone clears it is the load-bearing finding.

### F3 — Hard methodology gates (BINDING — v3 floor gates)

Per BASELINE_V3.md Code Configuration + `feedback_v3_dsr_mode_artifact.md`. Three binding methodology gates at the multi-seed unified-ensemble architecture:

| Gate | Threshold | /059 reference | /120 result |
|---|---|---:|---:|
| **PBO** (mean per-cell) | **< 0.40** | 0.1278 | 0.0957 PASS |
| **PSR** | **> 0.95** | 1.0 | 1.0 PASS |
| **frac_positive_paths** (CPCV 45 paths) | **≥ 0.55** | 0.6444 | 0.6444 PASS |

**F3 firing direction**: if ANY of {PBO ≥ 0.40, PSR ≤ 0.95, frac_positive_paths < 0.55}, F3 FAILS → NO-MERGE on methodology floor.

DSR_relative remains INFORMATIONAL ONLY per `feedback_v3_dsr_mode_artifact.md` (threshold needs cycle-1 recalibration; not binding at /121).

### F4 — Trade-rate floor (BINDING — `feedback_v3_trade_rate_floor.md`)

Per `feedback_v3_trade_rate_floor.md`: merges need ≥ 10 trades/month in OOS (≥ 130 total OOS trades).

**Numerical threshold**: /121 OOS trades aggregate ≥ **130**.

**F4 firing direction**: if /121 OOS trades < 130 → F4 FAILS (informational at /121 since /059 was 94 trades and /120 was 96; the floor has been an outstanding constraint since the v3 BASELINE was bootstrapped — applied here for completeness per the per-iteration falsifier discipline; **CARRIES FORWARD AS INFORMATIONAL** if below floor consistent with /059's outstanding-constraint status).

**Explicit clarification**: F4 is the project-level trade-rate floor inherited as a hard merge gate. At /121, if OOS trade count is below 130 BUT all other falsifiers PASS, the verdict carries the same INFORMATIONAL classification as /059 + /120 (the floor is an outstanding constraint not a mechanical /121-blocker, mirror of /059's bootstrap-level status). This does NOT renegotiate the floor — it preserves the v3 baseline rule that the floor is an outstanding constraint, NOT a /121-specific gate. If OOS trade count IS ≥ 130, F4 PASSES cleanly; the v3 baseline catalog records the constraint cleared.

### F5 — Per-symbol cascade-attribution (BINDING — carried forward from /120 F5 + /116 Critic Rec 3)

Per /116 Critic Rec 3 + /120 brief Section 4 + diary §3.6: ≥ 2 of 3 symbols positive OOS weighted_pnl Δ vs /059 baseline.

**Numerical thresholds** (per `reports-v3/iteration_v3-059/out_of_sample/per_symbol.csv`):
- BCH /059 OOS weighted_pnl = **+24.75**
- LDO /059 OOS weighted_pnl = **−6.18**
- TRX /059 OOS weighted_pnl = **+4.16**

**F5 firing condition**: < 2 of 3 symbols show positive Δ vs /059 weighted_pnl → F5 FAILS → PROMISING-FALSIFIED-AT-CONFIRMATION; NO-MERGE.

Equivalent: ≥ 2 of {BCH /121 OOS weighted_pnl > +24.75, LDO /121 OOS weighted_pnl > −6.18, TRX /121 OOS weighted_pnl > +4.16} must hold for F5 to PASS.

### Aggregate falsifier summary

The /121-METHODOLOGY iteration UPDATES BASELINE_V3.md to a Component-A-only PARTIAL-MERGE baseline ONLY IF all five falsifiers PASS at multi-seed:

| Falsifier | PASS condition |
|---|---|
| **F1 BOTH-must-improve** | /121 multi-seed IS ≥ **+1.0894** AND /121 multi-seed OOS ≥ **+0.5791** |
| **F2 IS regime-cost floor** | /121 multi-seed IS ≥ **+0.79** |
| **F3 hard methodology gates** | PBO < **0.40** AND PSR > **0.95** AND frac_positive_paths ≥ **0.55** |
| **F4 trade-rate floor** | /121 OOS trades ≥ **130** (else INFORMATIONAL carry-forward from /059 status) |
| **F5 per-symbol cascade-attribution** | ≥ 2 of 3 symbols /121 OOS weighted_pnl Δ vs /059 baseline > 0 |

If F1 FAILS while F2/F3/F5 PASS: BASELINE_V3.md UNCHANGED. The "all-time OOS record was driven by multi-mechanism interaction at /120" hypothesis is empirically RE-CONFIRMED; cycle-6 closes with 0 ingredients merged.

If F2 FAILS: no_confirm is permanently incompatible with /059 IS profile; cycle-6 closes with 0 ingredients merged; future cycles cannot bundle no_confirm.

---

## Section 5 — Risk Mitigation

Standard `feedback_v3_risk_mitigation_design.md` framework. R1–R5 UNCHANGED from /059:

- **R1 — Cool-downs**: standard /059 post-trade 2-candle cooldown; UNCHANGED. Component A's no_confirm exit triggers a normal trade close with its own subsequent cooldown — cool-down semantics preserved.
- **R2 — Drawdown scaling**: `enable_per_symbol_drawdown_brake=False` (per /054 stateful-deadlock closure). UNCHANGED.
- **R3 — OOD detection**: z-score OOD gate at threshold 2.0. UNCHANGED.
- **R4 — Vol kill-switch**: BTC trend filter at 15.0% threshold. UNCHANGED.
- **R5 — Concentration caps**: NO per-symbol PnL share caps (per `feedback_v3_concentration_is_signal.md`). UNCHANGED.

**Component-A-specific risk consideration**:

Component A's `no_confirm` exit introduces a 4th exit_reason category alongside `take_profit`, `stop_loss`, `timeout`. Per /116 EDA `T8_cuts_losers.csv` + /116 diary §2.3, the rule cuts modestly-below-average winners-held-to-barrier in IS (mean −0.84% IS, −0.80% OOS at /116 single-seed); the IS-channel cost cumulates in sustained bear/chop regimes (BCH 2022–2023). Mitigation: F2 (IS regime-cost floor +0.79) bounds the cumulative IS-channel cost; F5 (per-symbol cascade) ensures the rule does not destroy IS performance on any 2 of 3 symbols simultaneously.

Component B (C6) is REMOVED at /121. The /120 bundle's risk consideration of "FEATURE-layer redistribution may shift entry distribution into trades that no_confirm preferentially truncates" DOES NOT APPLY at /121 — Component A operates on /059's canonical 14-feature stack at the original entry distribution.

---

## Section 6 — Risk Management (Operational)

UNCHANGED from /059. Per BASELINE_V3.md:
- 7-primitive RiskV2 gate stack
- Standard CPCV with n_paths=45, embargo=27, REQUIRED_GAP=66
- Walk-forward POST-FIX at `e149e9d`
- OOF parquet guardrail `--clean-oof` flag active

No new RiskV2 primitive at /121. Component A is an exit-layer overlay on the backtest engine; no new R-layer code path.

---

## Section 7 — Pre-registered Failure Modes

Per `feedback_v3_promising_mechanical_subtype.md`. Three mutually exclusive verdict modes; each maps to the responsive falsifier:

**Mode A (CONFIRMATION-PARTIAL-MERGE — Component A standalone-positive and clears all falsifiers)**: /121 multi-seed IS ≥ +1.0894 AND OOS ≥ +0.5791. F1–F5 ALL PASS.
- **Verdict**: **PARTIAL-MERGE (RULE-layer single-mechanism)** → BASELINE_V3.md UPDATES to /121 Component-A-only baseline.
- **Cycle-6 closure**: 1 strictly-accretive primitive merged this cycle (Component A); cycle-7 axis-1 at /122 anchors against /121.
- **Probability estimate**: **~10–15%**. The BOTH-must-improve gate (F1) has been a chronic v3 obstacle since /039; only /028 has cleared it across the entire v3 history. /116 single-seed IS dropped −0.21 vs /060 anchor; the corresponding multi-seed drop vs /059 must be ≤ 0 for F1's IS leg to pass. The +0.79 IS floor (F2) is +0.30 below /059; the gap between F2 PASS and F1 PASS is +0.30 IS Sharpe — a substantial margin.

**Mode B (CONFIRMATION-NO-MERGE — F1 fails, F2 + F3 + F5 PASS — the interaction-effect-confirmed mode)**: /121 multi-seed IS ∈ [+0.79, +1.0894) AND OOS ∈ [/059 +0.5791 OR below, but materially below /120 +1.6946]. F2 + F3 + F5 PASS; F1 fails on IS leg, OR fails on OOS leg, OR fails on both.
- **Verdict**: **CONFIRMATION-NO-MERGE — Component A insufficient as single-mechanism baseline update**.
- **Mechanism interpretation**: the bundle's all-time OOS record at /120 (+1.6946) was DRIVEN BY the multi-mechanism interaction effect (Q3 Jaccard 0.48; 30 trades unique to bundle) rather than Component A alone. RE-CONFIRMS the Q3 finding.
- **Cycle-6 closure**: 0 ingredients merged. BASELINE_V3.md UNCHANGED at /059. /116 Component A remains classified PROMISING-MECHANICAL at the EXPLORATION level but does NOT clear multi-seed CONFIRMATION on /059's 14-feature stack.
- **Probability estimate**: **~50–60%** (the modal expectation). The /120 bundle's OOS lift over /116-alone single-seed (+1.6946 vs +1.1089 = +0.59) implies a non-trivial portion of the OOS performance was Component-B-driven loss-surface reorganization. At multi-seed, /116-alone is expected to compress from +1.1089 (single-seed EXPLORATION) toward a number consistent with /059's +0.5791 baseline or modestly above.

**Mode C (CONFIRMATION-NO-MERGE — F2 fails — IS regime-cost floor breach)**: /121 multi-seed IS < +0.79. Component A's IS regime-cost is more severe at multi-seed than single-seed EXPLORATION suggested.
- **Verdict**: **CONFIRMATION-NO-MERGE — no_confirm permanently incompatible with /059 IS profile**.
- **Cycle-6 closure**: 0 ingredients merged. BASELINE_V3.md UNCHANGED. Future cycles cannot bundle no_confirm without first demonstrating a structurally different (lower-cost) IS-channel formulation.
- **Probability estimate**: **~10–15%**. The /120 bundle multi-seed IS was +0.7293 — JUST BELOW the +0.79 floor (by 0.0607). Component A alone (without Component B's feature-layer loss-surface shift) may produce a different IS Sharpe at multi-seed — either above the floor (if the bundle's IS regression was Component-B-driven) or below the floor (if the IS drop is inherent to no_confirm).

**Mode D (CONFIRMATION-NO-MERGE — F3 fails — methodology gate breach)**: bundle PBO ≥ 0.40 OR PSR ≤ 0.95 OR frac_positive_paths < 0.55.
- **Verdict**: **CONFIRMATION-NO-MERGE on methodology floor**.
- **Probability estimate**: **<5%**. /059 and /120 both clear all three methodology gates cleanly; no evidence of methodology-floor risk in either reference iteration.

**Mode E (CONFIRMATION-NO-MERGE — F5 fails — per-symbol cascade collapse)**: < 2 of 3 symbols positive Δ vs /059 OOS weighted_pnl.
- **Verdict**: **CONFIRMATION-NO-MERGE — PROMISING-FALSIFIED-AT-CONFIRMATION**.
- **Probability estimate**: **~5–10%**. /116 single-seed was broad-based 3/3 positive OOS; /120 bundle was 3/3 positive OOS. The per-symbol cascade is the most robust empirical property of Component A. A single-symbol-carrier outcome at /121 multi-seed is plausible but not the modal expectation.

**Aggregate modal expectation**: **Mode B (~50–60%) is the modal verdict**. Cycle 6 most likely closes with 0 ingredients merged. The bundle's all-time OOS record at /120 (+1.6946) was a multi-mechanism interaction effect that is NOT replicated by Component A alone.

Mode A (PARTIAL-MERGE) probability of ~10–15% reflects the structural difficulty of the BOTH-must-improve gate in v3 history.

---

## Section 8 — LOCKED Acceptance Criteria (first-match-wins MERGE / NO-MERGE)

Acceptance gates are evaluated in the order below. First-match-wins; the first failed gate determines the verdict.

### 8.1 — Hard methodology gates (any FAIL → NO-MERGE)

| Gate | Threshold | /059 reference | /121 PASS condition |
|---|---|---:|---|
| Gate 5 PBO | < 0.40 | 0.1278 | /121 PBO mean < 0.40 |
| Gate 6 PSR | > 0.95 | 1.0 | /121 PSR > 0.95 |
| Gate 10-CPCV | ≥ 0.55 frac_positive_paths | 0.6444 | /121 ≥ 0.55 |
| OOS trades floor (F4) | ≥ 130 aggregate | 94 (below; outstanding constraint) | /121 ≥ 130 (else outstanding-constraint carry-forward consistent with /059 status) |
| OOS/IS Sharpe ratio (Gate 3) | ≥ 0.5 | 0.5316 | /121 ratio ≥ 0.5 (BINDING per /018 BOOTSTRAP rule) |

### 8.2 — Pre-committed falsifiers (each maps to a NO-MERGE verdict per the Section 7 mode table)

| Falsifier | PASS condition (recap) |
|---|---|
| **F1 BOTH-must-improve** | /121 multi-seed IS ≥ **+1.0894** AND OOS ≥ **+0.5791** |
| **F2 IS regime-cost floor** | /121 multi-seed IS ≥ **+0.79** |
| **F3 hard methodology gates** | PBO < 0.40 AND PSR > 0.95 AND frac_positive_paths ≥ 0.55 |
| **F4 trade-rate floor** | OOS trades ≥ 130 (else informational carry-forward) |
| **F5 per-symbol cascade** | ≥ 2 of 3 symbols /121 OOS weighted_pnl > /059 baseline (BCH > +24.75, LDO > −6.18, TRX > +4.16) |

### 8.3 — First-match-wins decision tree

```
1. If F3 hard methodology gates FAIL → NO-MERGE (methodology floor breach). BASELINE_V3.md UNCHANGED.
2. If F2 IS regime-cost floor FAILS (IS < +0.79) → CONFIRMATION-NO-MERGE (IS leg breach).
     BASELINE_V3.md UNCHANGED. Cycle-6 closes 0 ingredients merged.
     no_confirm permanently incompatible with /059 IS profile.
3. If F5 per-symbol cascade FAILS (< 2/3 positive Δ) → PROMISING-FALSIFIED-AT-CONFIRMATION; NO-MERGE.
     BASELINE_V3.md UNCHANGED. Cycle-6 closes 0 ingredients merged.
4. If F1 BOTH-must-improve FAILS while F2 + F3 + F5 PASS → CONFIRMATION-NO-MERGE.
     RE-CONFIRMS Q3 multi-mechanism interaction-effect finding from /120.
     BASELINE_V3.md UNCHANGED. Cycle-6 closes 0 ingredients merged.
     /116 Component A classified PROMISING-MECHANICAL at EXPLORATION; NOT cleared at multi-seed CONFIRMATION on /059 stack.
5. If ALL FALSIFIERS PASS (F1 + F2 + F3 + F5 ALL PASS) →
     CONFIRMATION-PARTIAL-MERGE (RULE-layer single-mechanism).
     BASELINE_V3.md UPDATES to /121 Component-A-only baseline.
     Cycle-6 closes 1 strictly-accretive primitive merged.
     Tag v0.v3-121.
```

F4 (trade-rate floor) is evaluated independently as informational; below-floor at /121 does NOT mechanically block PARTIAL-MERGE since /059's outstanding-constraint status carries forward.

### 8.4 — BASELINE_V3.md update policy

Per `feedback_v3_strict_both_is_oos_baseline.md`:
- BASELINE_V3.md updates ONLY if /121 multi-seed mean clears BOTH /059 IS (≥ +1.0894) AND /059 OOS (≥ +0.5791).
- This is F1, restated.
- If F1 fails (either leg), BASELINE_V3.md UNCHANGED — regardless of methodology gates, F2, F4, F5 status.

### 8.5 — Critic Phase 7.5 review

Per ITERATION_PLAN_8H_V3.md, the Critic's 8 mandatory checks + OVERALL=MERGE/BLOCK adjudicates after Engineer's Phase 6 commit. The Critic's OVERALL verdict is FINAL — Section 8.3's decision tree is the QR's first-match-wins read of the Phase 7 results; the Critic may OVERRIDE on substantive grounds.

---

## Section 9 — Library Stack + Reproducibility

UNCHANGED from /059 / /116 / /119 / /120:

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

Run invocation: `uv run python run_baseline_v3.py --n-trials 35 --clean-oof`.

Determinism: ENSEMBLE_SEEDS pinned to the 10-tuple `(191664963, 1662057957, 1405681631, 942484272, 929893137, 33158374, 1465339467, 1273345680, 115579757, 1952249162)` per `feedback_explicit_feature_columns.md` + BASELINE_V3.md. `V3_FEATURE_COLUMNS_TOP_N` (14 features at /121) explicit-list-pass to `LightGbmStrategy` per `feedback_explicit_feature_columns.md`.

Reproducibility stamp (to be filled by Phase 6 Engineer):
- Setup commit SHA: TBD (this commit cycle)
- Engineering report commit SHA: TBD
- `data/` extent at run time: TBD
- `reports-v3/iteration_v3-121/`: TBD

---

## Section 10 — QR Audit Trail (Phase 1-5)

### 10.1 — Why /121-METHODOLOGY exists

Per `feedback_v3_axis_selection_quant_discipline.md` (QR axis-selection discipline): /121-METHODOLOGY was **not** an ad-hoc orchestrator pick — it is a pre-committed cycle-6 outcome path established at three load-bearing commit moments.

**Provenance chain**:

1. **/120 brief Section 8.4 branch 3 (`26d99f2`)**: explicitly pre-committed "DROP Component B; re-evaluate /116-only against the same gates" as a binding outcome path. The /121-METHODOLOGY iteration IS this branch's standalone evaluation.

2. **/120 Critic FINAL (`a49dd17`) Recommendation 2**: "iter-v3/121-METHODOLOGY AUTHORIZED as cycle-7 BOOTSTRAP (analogous to iter-v3/018 BOOTSTRAP precedent; NOT counted toward cycle-7 10/10 EXPLORATION cadence)". The Critic FULLY ACCEPTED the QR Round-2 Q1 + Q5 concession framing.

3. **/120 diary §9 (`88cc966`)**: documented the spec, hypothesis, decision tree, and naming convention. Per the diary § 9.5: "/121-METHODOLOGY does NOT count toward cycle-7's 10/10 EXPLORATION cadence" + "the runner-config diff vs /059 is THREE knob flips (...) and ONE feature-set diff (revert V3_FEATURE_COLUMNS_TOP_N to 14 features per /059)".

The diary §9.2 spec is implemented verbatim in this brief (Sections 0–9 above). No deviation from the pre-committed spec.

### 10.2 — Provenance of every numerical value in Sections 1–9

| Numerical value | Source | Provenance |
|---|---|---|
| /059 IS monthly Sharpe +1.0894 | BASELINE_V3.md | Canonical anchor; tag v0.v3-059 |
| /059 OOS monthly Sharpe +0.5791 | BASELINE_V3.md | Canonical anchor; tag v0.v3-059 |
| /059 OOS/IS ratio 0.5316 | BASELINE_V3.md | Canonical anchor |
| /059 PBO 0.1278 | BASELINE_V3.md | Canonical anchor; methodology gate reference |
| /059 PSR 1.0 | BASELINE_V3.md | Canonical anchor; methodology gate reference |
| /059 frac_positive_paths 0.6444 | BASELINE_V3.md | Canonical anchor; methodology gate reference |
| /059 OOS trades 94 | BASELINE_V3.md | Canonical anchor; outstanding-constraint reference |
| /059 BCH OOS weighted_pnl +24.75 | `reports-v3/iteration_v3-059/out_of_sample/per_symbol.csv` | F5 calibration anchor |
| /059 LDO OOS weighted_pnl −6.18 | `reports-v3/iteration_v3-059/out_of_sample/per_symbol.csv` | F5 calibration anchor |
| /059 TRX OOS weighted_pnl +4.16 | `reports-v3/iteration_v3-059/out_of_sample/per_symbol.csv` | F5 calibration anchor |
| /116 IS +0.6246, OOS +1.1089 | `reports-v3/iteration_v3-116/comparison.csv` | Component A single-seed EXPLORATION reference |
| /116 IS drop −0.21 vs /060 | /116 closeout diary | F2 floor calibration anchor |
| /060 anchor IS +0.8325 | BASELINE_V3.md (/060 historical reference) | F2 floor calibration anchor |
| /119 IS +0.8492, OOS +0.8420 | `reports-v3/iteration_v3-119/comparison.csv` | Component B single-seed EXPLORATION reference (informational only at /121) |
| /120 bundle IS +0.7293, OOS +1.6946 | `reports-v3/iteration_v3-120/comparison.csv` | Multi-mechanism bundle reference for /121 attribution-gap framing |
| /120 BCH IS net_pnl_pct collapse −69.31 pct | /120 diary §3.5 | Documents F2 IS regime-cost mechanism |
| Jaccard 0.48 (/120 bundle vs /116-alone) | `briefs-v3/iteration_v3-120/qr_response.md` | Q3 multi-mechanism interaction evidence |
| 30 trades unique to bundle (/120 vs /116-alone) | `briefs-v3/iteration_v3-120/qr_response.md` | Q3 multi-mechanism interaction evidence |
| F2 IS floor +0.79 (= /059 IS − 0.30) | /120 brief Section 4 Falsifier 4 + this brief Section 4 F2 | Pre-committed; cannot be renegotiated |
| F4 trade-rate floor 130 OOS trades | `feedback_v3_trade_rate_floor.md` | Project-level rule |
| F3 PBO < 0.40 threshold | BASELINE_V3.md | v3 methodology floor |
| F3 PSR > 0.95 threshold | BASELINE_V3.md | v3 methodology floor |
| F3 frac_positive_paths ≥ 0.55 threshold | BASELINE_V3.md | v3 methodology floor (Gate 10-CPCV) |
| F1 BOTH-must-improve | `feedback_v3_strict_both_is_oos_baseline.md` | Project-level rule |

### 10.3 — What this brief does NOT contain

- NO new EDA (per `feedback_v3_axis_selection_quant_discipline.md` for CONFIRMATION-class iterations + /120 diary §9.5 explicit no-new-EDA mandate).
- NO new hand-chosen parameters (per Section 0).
- NO new feature primitives (Component B REVERTED).
- NO new code paths (only knob flips + feature-list revert).
- NO new RiskV2 primitives.
- NO new symbols, labeling primitives, candle frequencies, or model architectures.
- NO renegotiation of /120 F3 (sister-redistribution) or F4 (IS regime-cost) pre-commitments. Both fired at /120; Component B was dropped per the pre-committed decision tree.
- NO methodology innovation. /121-METHODOLOGY is purely a multi-seed re-evaluation of an EXPLORATION-PROMISING-MECHANICAL primitive that the cycle-6 CONFIRMATION at /120 left unevaluated standalone.

### 10.4 — Out-of-scope items deferred to cycle-7

- iter-v3/122 = cycle-7 EXPLORATION axis-1 from /119 diary §8.2 candidate menu (cross-asset/external feeds, longer-cadence labels, NEW model architecture, NEW symbol universe), QR-selected per `feedback_v3_axis_selection_quant_discipline.md` after /121 closes.
- Per `feedback_v3_strict_10_to_1_cadence.md`: standard 10/10 + 1 CONFIRMATION cadence resumes from /122 regardless of /121 outcome.
- /121's BASELINE_V3.md update outcome determines cycle-7 anchor:
  - IF /121 PARTIAL-MERGE → cycle-7 axis menu anchors against /121 baseline.
  - IF /121 NO-MERGE → cycle-7 axis menu anchors against /059 canonical (UNCHANGED).

---

## END OF BRIEF
