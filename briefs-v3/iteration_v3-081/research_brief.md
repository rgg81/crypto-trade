# iter-v3/081 — Research Brief (CYCLE 2 CONFIRMATION)

**Branch**: `iteration-v3/081`
**EDA SHA**: `be0ccf5` (the `analysis/iteration_v3-081/baseline_integrity_audit.py` commit)
**Setup commit SHA**: `TBD` (backfilled into Section 10 at Phase 5.5)
**Iteration type**: CYCLE 2 CONFIRMATION (NOT EXPLORATION) — the SEPARATE CONFIRMATION after the strict 10:1 cadence (cycle 2 = EXPLORATIONs /071-/080, then 1 SEPARATE CONFIRMATION /081)
**Bundle**: NONE — cycle 2 produced 0 clean PROMISING across all 10 EXPLORATIONs. /081 is a multi-seed RE-VALIDATION of the canonical /059 configuration, analogous to cycle 1's /070 CONFIRMATION (also NO-MERGE).

---

## Section 0 — Data Split Declaration

**UNCHANGED.** Sacred constants per `feedback_no_cheating.md` (the v3 NO-CHEATING absolute rules):

```
OOS_CUTOFF_DATE  = 2025-03-24       # IMMUTABLE — never changes
training_months  = 24                # IMMUTABLE — never changes
ENSEMBLE_SIZE    = 10                # CONFIRMATION mode (unified 10-seed, Phase B-3)
ENSEMBLE_SEEDS   = (191664963, 1662057957, 1405681631, 942484272, 929893137,
                    33158374, 1465339467, 1273345680, 115579757, 1952249162)
n_trials         = 35                # default for CONFIRMATION (feedback_v3_confirmation_n_trials_35.md)
colsample_bytree = Optuna-tuned      # NOT hardcoded 1.0
```

- **IS window**: earliest available data → 2025-03-24 (the walk-forward / CPCV backtest runs on ALL data; the reporting layer splits at `OOS_CUTOFF_DATE`).
- **OOS window**: 2025-03-24 → present (≈14+ OOS months at run time; grows monotonically with calendar date).
- Symbol universe = BCHUSDT, LDOUSDT, TRXUSDT (3 symbols — `V3_MODELS` UNCHANGED from /059).
- Feature universe = the 14 `V3_FEATURE_COLUMNS_TOP_N` features (UNCHANGED from /059 / the /028 spec).
- `start_time` is NOT trimmed; no date-range is cherry-picked; no trade is post-hoc filtered; no parameter is tuned on OOS.

The QR has seen ONLY IS data and ALREADY-PUBLISHED report CSVs during Phases 1-5. The /081 OOS results are seen for the first time in Phase 7.

## Section 0.5 — Iteration Type Declaration

**TYPE**: **CYCLE 2 CONFIRMATION (NOT EXPLORATION)**.

- **Cycle 2 cadence**: COMPLETE per `feedback_v3_strict_10_to_1_cadence.md` — 10 SEPARATE EXPLORATIONs /071-/080, then 1 SEPARATE CONFIRMATION /081. The 10th EXPLORATION (/080) was NOT collapsed into /081 (it was a separate single-seed PASSIVE-DIAGNOSTIC).
- **Run mode**: DEFAULT CONFIRMATION (NO `--exploration` flag → `ENSEMBLE_SIZE=10` unified architecture per `feedback_v3_unified_10seed_baseline.md`).
- **Optuna budget**: `--n-trials 35` per (symbol × walk-forward month × seed). Total = 35 × 3 sym × 10 seeds = 1050 trials (identical to /059).
- **Wall-clock**: HARD CAP 6h per `feedback_v3_cadence_discipline.md` (/059 ran 3.60h; /070 ran 3.13h — expect ~3.5h).

### Section 0.5.1 — Cadence verification (Phase 5.5 will check this)

The 10 cycle-2 EXPLORATION precedents since the cycle-1 CONFIRMATION (/070), per `briefs-v3/exploration_catalog.md` and the /080 diary Section 11:

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /071 | META-LABELING (same-feature M2 take/skip) | SUSPICIOUS-OOS-DOMINANT |
| #2 | /072 | ALTERNATIVE LABELING (fixed-horizon-21) | NEGATIVE |
| #3 | /073 | PER-SYMBOL LABELING (per-symbol triple-barrier asymmetry) | SUSPICIOUS-OOS-DOMINANT |
| #4 | /074 | NEW RISK PRIMITIVE (regime-conditional kill switch, primitive 9) | INERT-AT-EXPLORATION |
| #5 | /075 | NEW RISK PRIMITIVE (BTC-trend-regime position-SIZE de-rate, primitive 12) | INERT-AT-EXPLORATION |
| #6 | /076 | NEW FEATURE (`range_efficiency_50`, Kaufman path efficiency) | SUSPICIOUS-OOS-DOMINANT |
| #7 | /077 | PASSIVE-DIAGNOSTIC (`conditional_orthogonality.csv` + `range_efficiency_50` revert) | INERT-AT-EXPLORATION |
| #8 | /078 | UNIVERSE REVISION (replace LDOUSDT with ADAUSDT) | SUSPICIOUS-OOS-DOMINANT |
| #9 | /079 | NEW RISK PRIMITIVE (conviction-weighted per-trade sizing, primitive 13) | NULL-RESULT (behavioral saturation) |
| #10 | /080 | PASSIVE-DIAGNOSTIC (persist per-trade `confidence` + `confidence_distribution.csv`) | NULL-RESULT (bit-identical roster) |

**10/10 cycle-2 EXPLORATIONs COMPLETE. 0 clean PROMISING.** 4 SUSPICIOUS-OOS-DOMINANT (/071, /073, /076, /078), 1 NEGATIVE (/072), 3 INERT (/074, /075, /077), 2 NULL-RESULT (/079, /080).

### Section 0.5.2 — Why /081 is a RE-VALIDATION, not an edge-bundle CONFIRMATION

A standard CONFIRMATION is a *bundle* of the cycle's PROMISING EXPLORATION findings (`feedback_v3_cadence_discipline.md` rule 4). **Cycle 2 produced no PROMISING findings — there is no edge ingredient to bundle.** This is the exact situation cycle 1 hit at /070 (cycle 1 also produced no bundle-able edge; its 2-component bundle of the only non-anchor advancement candidates was SUSPICIOUS-OOS-DOMINANT NO-MERGE — `project_v3_cycle1_outcome.md`).

Per the /080 diary Section 11 and the /080 Critic Recommendation #1: "/081 is a /059-baseline multi-seed re-validation: a `--seeds 2` run of the canonical /059 configuration to confirm BASELINE_V3.md's IS +1.0894 / OOS +0.5791 still reproduces under the current code state." This brief executes exactly that.

The justification for the type choice (the 1-2 sentence Phase-5.5 requirement): **/081 is a CONFIRMATION because the cycle-2 cadence is complete (10/10) and the canonical config must be re-validated at multi-seed CONFIRMATION rigor; it is a re-validation rather than a bundle because cycle 2 produced zero PROMISING edge ingredients to bundle.**

## Section 1 — Testable Hypothesis (ONE sentence)

> The genuine /059 canonical configuration — the 14-`V3_FEATURE_COLUMNS_TOP_N` stack on BCH/LDO/TRX with the /059 risk stack and `vol_scale_floor_per_symbol` reverted to `{}` (the illegitimate iter-v3/061 accretion removed) — re-run at unified 10-seed CONFIRMATION mode reproduces `BASELINE_V3.md`'s /059 numbers (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791) within a ±0.20 monthly-Sharpe tolerance on BOTH axes, in which case /059 is CONFIRMED and `BASELINE_V3.md` is UNCHANGED; if /081 drifts beyond ±0.20 on either axis, the re-anchor decision follows `feedback_v3_baseline_update_policy.md` + `feedback_v3_strict_both_is_oos_baseline.md` (RE-ANCHOR only on a BOTH-IS-AND-OOS improvement; otherwise /059 stays canonical with a staleness note).

## Section 2 — IS-Only Numerical Evidence (EDA SHA `be0ccf5`)

EDA committed at SHA `be0ccf5` — `analysis/iteration_v3-081/baseline_integrity_audit.py` produces 4 tables. The audit is a git-archaeology / measurement-integrity audit: it reads git history, the /059 setup commit `20095a8`, the current `run_baseline_v3.py`, and the ALREADY-PUBLISHED `comparison.csv` files. It computes no new backtest, touches no sacred constant, and tunes nothing.

### Section 2.1 — The load-bearing question: is the iter-v3/061 TRX vol-floor legitimate?

`BASELINE_V3.md` anchors /059 (IS +1.0894 / OOS +0.5791, tag `v0.v3-059`), established at the iter-v3/058 RE-ANCHOR architecture and the /059 setup commit `20095a8` — **before cycle 1's iter-v3/061**. The current `run_baseline_v3.py:1700` carries `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}`. iter-v3/077 (the PASSIVE-DIAGNOSTIC) found this floor injects a deterministic **−0.0089 IS drift** into the current-code /060-config (it floors 13 IS TRX `weight_factor` values at 0.5). Section 2 establishes whether this floor is a legitimate part of the canonical config or illegitimate accretion that /081 must revert.

### Section 2.2 — T1: Accretion ledger (`analysis/iteration_v3-081/T1_accretion_ledger.csv`)

A diff of every behavior-affecting config knob between the /059 setup commit `20095a8` and current HEAD. 9 knobs audited. Headline:

| config_knob | value at /059 (20095a8) | value at HEAD | behavior_class | verdict |
|---|---|---|---|---|
| `vol_scale_floor_per_symbol` | `{}` (absent) | `{"TRXUSDT": 0.5}` | BEHAVIOR-AFFECTING | **ILLEGITIMATE ACCRETION — /081 REVERTS to `{}`** |
| `DEFAULT_ATR_MULTIPLIERS` | `(2.0, 1.0)` | `(2.0, 1.0)` | BEHAVIOR-AFFECTING | CLEAN — /065 widening reverted at /070 (commit `8bdf392`); HEAD == /059 |
| `V3_ATR_MULTIPLIERS_PER_SYMBOL` | `{}` (empty) | `{}` (empty) | BEHAVIOR-AFFECTING | CLEAN — /073 per-symbol reverted at /074; HEAD == /059 |
| `V3_MODELS` (universe) | BCH/LDO/TRX | BCH/LDO/TRX | BEHAVIOR-AFFECTING | CLEAN — /069 +ADA and /078 LDO→ADA both reverted; HEAD == /059 |
| `enable_per_symbol_cap` | False | False | GATED-OFF | CLEAN — `max_per_symbol_pnl_share=0.40` is dead config behind a False flag |
| `enable_regime_gate` / `enable_regime_size_scalar` | False / False | False / False | GATED-OFF | CLEAN — primitives 9 & 12 reverted OFF at /075/077 |
| `label_mode` / `label_timeout_minutes` | triple_barrier / 10080 | triple_barrier / 10080 | BEHAVIOR-AFFECTING | CLEAN — /072 fixed-horizon and /068 timeout both reverted |
| `inference_threshold_floor` | 0.0 (default) | 0.0 (default) | BEHAVIOR-AFFECTING | CLEAN — /067 floor=0.60 reverted at /068 |
| `conditional_orthogonality.csv` / `confidence` column | absent | present | **PASSIVE (NOT behavior-affecting)** | CLEAN-PASSIVE — /077+/080 report tooling; /080 Critic verified the roster is bit-identical with these present; KEEP |

**T1 result: exactly ONE illegitimate accretion** — `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}`. Every other behavior-affecting axis tested during cycles 1-2 was explicitly reverted at its EXPLORATION/CONFIRMATION closeout (the v3 anti-drift discipline of `feedback_no_cheating.md` was correctly applied — except for this one line). The PASSIVE report-emission additions (`conditional_orthogonality.csv`, the `confidence` column) are NOT behavior-affecting and are kept.

### Section 2.3 — T2: iter-v3/061 vol-floor provenance (`analysis/iteration_v3-081/T2_vol_floor_provenance.csv`)

The lifecycle of the /061 floor, traced from git history. 9 lifecycle questions. Headline:

| lifecycle question | finding |
|---|---|
| iteration type | EXPLORATION (cycle 1 #2 of 10) — brief Section 0.5 `TYPE=EXPLORATION` |
| verdict | **INERT-AT-EXPLORATION** (IS Δ −0.009 / OOS Δ +0.015 vs /060 anchor — inside the noise band; NOT even PROMISING) |
| feat commit in git | YES — `6910fcf` `feat(iter-v3/061): per-symbol vol_scale_floor — TRX=0.5 (Path B)` |
| `v0.v3-061` tag exists | **NO** — `git tag -l v0.v3-*` returns only `{018, 028, 058, 059}` |
| carried by a CONFIRMATION-MERGE | **NO** — cycle 1's only CONFIRMATION (/070) was SUSPICIOUS-OOS-DOMINANT NO-MERGE; the /070 bundle was `{/065 SL widening, /062 Path B4}` — the /061 floor was NOT a bundle component (it was INERT, not advanceable) |
| /061 diary's own statement | verbatim: "BASELINE_V3.md is UNCHANGED — /059 stays canonical (CONFIRMATIONs are the only iterations that update baseline...)" |
| why the code persisted | the /061 closeout reverted the *intent* but not the *runner config line*: it kept the `RiskV2Config` field + lookup (the mechanism — harmless) AND silently left the `_build_v3_model` config line `{"TRXUSDT": 0.5}` active; EXPLORATIONs /062-/080 each varied ONE OTHER axis and never touched the floor line, so it rode forward 19 iterations |
| did /070 CONFIRMATION measure with the floor active | **YES** — `git show aab9347:run_baseline_v3.py` (the /070 setup commit) contains the floor; the /070 CONFIRMATION did NOT measure the genuine /059 config either |
| **VERDICT** | **ILLEGITIMATE ACCRETION — /081 REVERTS** |

The binding rule is `feedback_v3_cadence_discipline.md` rule 5: *"Only CONFIRMATION-MERGE updates BASELINE_V3.md. EXPLORATION-PROMISING is a forward-pointer, not a baseline change."* iter-v3/061 was an EXPLORATION, was only INERT (not even PROMISING), was never tagged, and was never carried by a CONFIRMATION-MERGE. By the v3 governance model, the canonical config is defined by the last CONFIRMATION-MERGE (/059). An EXPLORATION axis that persisted in the active runner config is illegitimate accretion — exactly the class of drift `feedback_no_cheating.md` anti-drift discipline exists to prevent.

**Corollary (material): /081 is the FIRST CONFIRMATION-class run since /059 itself to measure the genuine /059 canonical config.** Cycle 1's /070 CONFIRMATION ran with the /061 floor active. /081, after reverting the floor, restores the true /059 measurement.

### Section 2.4 — T3: Anchor reconciliation (`analysis/iteration_v3-081/T3_anchor_reconciliation.csv`)

Two anchors are in play and they are DIFFERENT objects — this table makes explicit which one /081 reproduces:

| config object | ensemble architecture | /061 vol-floor present | IS monthly Sharpe | OOS monthly Sharpe | role for /081 |
|---|---|---|---:|---:|---|
| **/059 BASELINE_V3 canonical CONFIRMATION** | unified 10-seed | **ABSENT** (20095a8 has 0 references) | **+1.0894** | **+0.5791** | **THE /081 TARGET** |
| /077 (current-code /060-config, EXPLORATION) | 3-seed | PRESENT | +0.8236 | +0.2078 | NOT the target — EXPLORATION-mode AND carries the floor |
| /080 (current-code /060-config, EXPLORATION) | 3-seed | PRESENT | +0.8236 | +0.2908 | NOT the target — same as /077 |

**Critical distinction**: the /077//080 numbers (the "current-code /060-config baseline" from the iter-v3/077 anchor-staleness finding) are an **EXPLORATION-mode (3-seed)** reference that ALSO carries the /061 floor. They are NOT the /059 CONFIRMATION config and NOT the /081 target. /081 reproduces the /059 CONFIRMATION config: unified **10-seed**, **NO** vol-floor. The /081 setup reverts the floor; the /081 run uses 10-seed CONFIRMATION mode. The EXPLORATION-MODE-REFERENCE anchor (`feedback_v3_exploration_anchor_staleness.md`) is an intra-cycle delta anchor only and never feeds a CONFIRMATION gate.

### Section 2.5 — T4: Re-validation decision (`analysis/iteration_v3-081/T4_revalidation_decision.csv`)

The /081 config decision and the Section 8 re-validation logic inputs — 12 decision items. The config is forced by the T1/T2 audit: the legitimate /059 canonical config, with the one revert. Detail in Section 3 (config) and Section 8 (LOCKED logic).

### Section 2.6 — Inherited IC declaration (carry-forward; no feature change at /081)

/081 makes NO feature change — the 14-feature stack is byte-identical to /059. The known inherited Category-2 composed-feature correlation `vwap_dev_20 × regime_momentum_signed_5d ≈ 0.78` is carried forward under the `feedback_v3_engineered_feature_pivot.md` carve-out (composed features mechanically correlate with their primitives; the gate is importance ≥ 30, not |IC| < 0.70 — both features clear the importance threshold per the /070 brief Section 2.6). No new feature family is introduced, so the new-vs-existing IC gate (Critic Check 4) is not triggered.

## Section 3 — Proposed Changes (enumerated)

### Sub-fix 1 — REVERT the iter-v3/061 illegitimate accretion: `vol_scale_floor_per_symbol` → `{}`

File: `run_baseline_v3.py` — the `_build_v3_model` `RiskV2Config(...)` block (currently line ~1700).

```python
# Before (current HEAD — illegitimate iter-v3/061 EXPLORATION accretion)
vol_scale_floor_per_symbol={"TRXUSDT": 0.5},

# After (/081 — REVERT to the genuine /059 canonical config)
vol_scale_floor_per_symbol={},
```

Equivalently: delete the line (the `RiskV2Config` field default is `field(default_factory=dict)` → `{}`). The brief specifies passing the explicit `{}` to keep the runner self-documenting and to leave an in-code provenance comment recording the /081 revert and its rationale.

**This is a measurement-integrity revert, NOT a new axis.** It removes a never-merged EXPLORATION axis so /081 measures the genuine /059 canonical config that `BASELINE_V3.md` documents. It mirrors the iter-v3/070-closeout precedent exactly: at /070's closeout, the rejected /065 SL-widening component was reverted via `revert(iter-v3/070): DEFAULT_ATR_MULTIPLIERS (2.0,1.5)->(2.0,1.0)` (commit `8bdf392`). /081 does the analogous thing for the /061 floor.

The `RiskV2Config.vol_scale_floor_per_symbol` FIELD and the `_vol_scale` per-symbol lookup in `risk_v2.py` **STAY** — they are a backward-compatible mechanism (`field(default_factory=dict)`, empty by default → bit-identical to pre-/061 behavior). Reverting the runner config to `{}` exercises that default. The mechanism's unit tests (`tests/strategies/ml/test_per_symbol_vol_scale_floor.py`) construct their own `RiskV2Config` with explicit dicts and do NOT call `_build_v3_model` — they test the mechanism, stay valid, and need no change.

### Sub-fix 2 — Runner pre-flight assertion update

File: `run_baseline_v3.py` — the `iter-v3/061` pre-flight assertion block (currently lines ~778-805).

```python
# Before (current HEAD)
expected_floor_dict: dict[str, float] = {"TRXUSDT": 0.5}

# After (/081)
expected_floor_dict: dict[str, float] = {}
```

The assertion logic (build a TRX `RiskV3Wrapper`, assert `config.vol_scale_floor_per_symbol == expected_floor_dict`) STAYS — it now asserts the floor is the genuine /059 empty `{}`. Update the surrounding comment and the `print(...)` confirmation line to record that /081 reverted the /061 accretion (TRX back to the global `0.3` floor like BCH/LDO).

### Sub-fix 3 — ITERATION_LABEL bump

File: `run_baseline_v3.py` line ~131.

```python
# Before
ITERATION_LABEL = "v3-080"
# After
ITERATION_LABEL = "v3-081"
```

### Sub-fix 4 — Existing test file updates

Audit and update any test that asserts the runner's `_build_v3_model` produces `vol_scale_floor_per_symbol == {"TRXUSDT": 0.5}`:

| File | Current expectation | New expectation | Note |
|---|---|---|---|
| `tests/strategies/ml/test_per_symbol_vol_scale_floor.py` | constructs its own `RiskV2Config` with explicit `{"TRXUSDT": 0.5}` / `{}` dicts; does NOT call `_build_v3_model` | **NO CHANGE** | Tests the MECHANISM (the field + the `_vol_scale` lookup), not the runner config. The mechanism is unchanged. Stays valid. |
| any test invoking `_build_v3_model` + asserting the floor dict | `{"TRXUSDT": 0.5}` | `{}` | The Engineer greps `_build_v3_model` + `vol_scale_floor` across `tests/` at Phase 5.5 and updates any runner-config assertion to `{}`. |

The Engineer runs `grep -rn "vol_scale_floor_per_symbol" tests/` at Phase 5.5; the only current match is `test_per_symbol_vol_scale_floor.py` (mechanism test — no change). If the grep surfaces a new runner-config assertion, update it to `{}`.

### Sub-fix 5 — NO other changes

- **Features**: UNCHANGED — the 14-feature `V3_FEATURE_COLUMNS_TOP_N` stack (T1 confirmed HEAD == /059; no feature drift).
- **Universe**: UNCHANGED — BCH/LDO/TRX (T1 confirmed HEAD == /059).
- **Labeling**: UNCHANGED — triple-barrier ATR (2.0, 1.0) universal, 21-candle timeout (T1 confirmed HEAD == /059).
- **Risk stack**: UNCHANGED except Sub-fix 1 — the 7-primitive stack at the /059 spec.
- **ENSEMBLE / seeds / n_trials**: UNCHANGED from /059 — 10-seed unified, n_trials=35.
- **NO new edge axis.** Cycle 2 produced no PROMISING ingredient; /081 introduces nothing new. /081's only change vs current HEAD is removing the /061 accretion.
- **NO parquet regeneration** — no feature column changes.

### Sub-fix 6 — Run command (CLI)

```bash
uv run python run_baseline_v3.py --clean-oof
```

NO `--exploration` flag → `ENSEMBLE_SIZE=10` unified CONFIRMATION architecture. `--seeds 2` MAY be passed (it is deprecated under the unified architecture per `feedback_v3_unified_10seed_baseline.md` — the runner logs a warning and ignores the value); the canonical command omits it. `--clean-oof` per `feedback_v3_oof_parquet_guardrail.md`.

## Section 4 — Expected OOS Impact + Falsifiers

### Section 4.1 — Headline prediction (unified 10-seed CONFIRMATION mode)

/081 re-runs /059's exact architecture and config (post-revert). The expectation is **reproduction of /059 within tolerance**, not a lift — there is no edge axis.

| Metric | /059 anchor | /081 predicted lower | /081 predicted upper | Re-validation interpretation |
|---|---:|---:|---:|---|
| IS monthly Sharpe | **+1.0894** | +0.89 | +1.29 | within ±0.20 → CONFIRMED |
| OOS monthly Sharpe | **+0.5791** | +0.38 | +0.78 | within ±0.20 → CONFIRMED |
| OOS/IS monthly Sharpe ratio | 0.5316 | 0.40 | 0.85 | Gate 3 floor ≥ 0.50 |
| IS trades | 171 | 155 | 185 | tracking |
| OOS trades | 94 | 90 | 130 | tracking (anchor 94 is below the 130 floor — informational) |
| PBO mean | 0.1278 | 0.10 | 0.18 | Gate 5 < 0.40 (cell-level invariant — expect ≈ 0.1278) |
| frac_positive_paths (CPCV) | 0.6444 | 0.60 | 0.70 | Gate 10-CPCV ≥ 0.55 (CPCV is architecture-invariant — expect ≈ 0.6444) |
| PSR (legacy) | 1.0 | 0.99 | 1.0 | Gate 6 > 0.95 (n_trials=1050 saturation) |

**Rationale for the ±0.20 monthly-Sharpe band**:

1. **IS axis — pure Optuna run-to-run stochasticity.** The IS window is fixed by `OOS_CUTOFF_DATE`, so it has NO data-extent channel. The only source of IS drift is that Optuna's TPE sampler at n_trials=35 explores the hyperparameter space stochastically run-to-run. Reverting the /061 vol-floor mechanically *removes* the −0.0089 IS drift the /077 EDA isolated — so /081's IS, vs the /060-config-with-floor, recovers that. Net IS-vs-/059 expectation is near zero; ±0.20 is a conservative band.

2. **OOS axis — Optuna stochasticity + a POSITIVE data-extent drift.** iter-v3/077 quantified the /060-config OOS data-extent drift at **+0.0675** over a horizon comparable to /059→/081. /081 fetches even more OOS data (≈2 additional calendar months of OOS beyond /059's fetch), so any OOS drift is expected in the POSITIVE direction. The ±0.20 band brackets this.

3. **The /081 config is bit-identical to /059's config (post-revert).** /081 is not a new strategy — it is /059's strategy re-measured. A reproduction inside ±0.20 on both axes is the expected and most-likely outcome.

### Section 4.2 — Per-symbol expectation

| Symbol | /059 OOS weighted_pnl | /081 expectation | Note |
|---|---:|---|---|
| BCH | +24.75 | reproduce ± data-extent | BCH IS concentration 95.76% remains the structural fragility flag — carried into cycle 3 |
| TRX | +4.16 | small POSITIVE shift expected | reverting the /061 floor *lowers* TRX `weight_factor` on 13 trades back to the global `0.3` floor; the /061 EDA found this is a near-zero IS effect (+0.008 wpnl) and a non-significant OOS effect — the revert moves TRX *back to* the /059 measurement |
| LDO | −6.18 | reproduce ± data-extent | LDO directional weakness remains unresolved — carried into cycle 3 |

The vol-floor revert affects ONLY TRX (the floor dict was TRX-only); BCH and LDO `weight_factor` values are mathematically invariant to the revert (per the /061 EDA Q5 isolation check). The revert moves the measured config from "/059 + /061 floor" back to genuine "/059".

### Section 4.3 — Behavioral-effect predictor (`feedback_v3_axis_saturation_predictor.md`)

The /081 "change" is the removal of the /061 vol-floor. Its behavioral effect, relative to the current-code-with-floor state: it un-floors 13 IS TRX `weight_factor` values (from `0.5` back to their natural `[0.3, 0.5)` vol-scaled values) and the corresponding OOS TRX floored trades. Relative to /059 itself, the effect is **zero** — /059 never had the floor.

**Falsifier**: if the /081 trade roster is NOT measurably different from a current-code-with-floor run on the SAME 13 TRX trades' `weight_factor` values, the revert did not take effect (a wiring failure) → BLOCK. Pre-registered prediction: 13 IS TRX `weight_factor` values shift down off the `0.5` floor; BCH/LDO `weight_factor` values are bit-identical to a with-floor run.

### Section 4.4 — Supplemental SUSPICIOUS gate (`feedback_v3_oos_is_ratio_gate.md`)

Per the mandatory cycle-2+ rule: **OOS/IS monthly Sharpe ratio > 3.0 → SUSPICIOUS** (using the canonical within-iteration `comparison.csv` `monthly_sharpe` ratio definition). Healthy band ≈ [0.5, 2.0]. The /059 anchor ratio is 0.5316 (IS-dominant — within the healthy band's lower region). /081 reproduces /059's config, so the ratio is expected ≈ 0.40–0.85. A ratio > 3.0 would indicate the re-validation surfaced a regime-exposed measurement and would be flagged SUSPICIOUS regardless of absolute OOS Sharpe. This gate is pre-registered and LOCKED.

### Section 4.5 — Pre-registered FALSIFIER bands (BINDING)

| Gate ID | Gate | Threshold | Action if FAIL |
|---|---|---|---|
| **G.1** | IS monthly Sharpe within ±0.20 of +1.0894 | reproduction band | outside → drift; route to Section 8 re-anchor logic |
| **G.2** | OOS monthly Sharpe within ±0.20 of +0.5791 | reproduction band | outside → drift; route to Section 8 re-anchor logic |
| **G.3** | OOS/IS Sharpe ratio | ≥ 0.50 (Gate 3 — hard-blocking) | FAIL → no RE-ANCHOR even on a BOTH-improve result |
| **G.4** | frac_positive_paths (CPCV) | ≥ 0.55 (Gate 10-CPCV — hard-blocking) | FAIL → no RE-ANCHOR |
| **G.5** | PBO mean | < 0.40 (Gate 5) | FAIL → methodology BLOCK |
| **G.6** | PSR (legacy) | > 0.95 (Gate 6 — hard-blocking) | FAIL → no RE-ANCHOR |
| **G.7** | OOS/IS ratio NOT SUSPICIOUS | ratio ≤ 3.0 (`feedback_v3_oos_is_ratio_gate.md`) | ratio > 3.0 → SUSPICIOUS |
| **G.8** | vol-floor revert took effect | `_build_v3_model` produces `vol_scale_floor_per_symbol == {}`; runner pre-flight assertion PASSES | FAIL → wiring BLOCK |
| **G.9** | All v3 tests pass | full `uv run pytest` green | FAIL → BLOCK |
| **G.10** | ensemble_summary | `mode=confirmation`, `ensemble_size=10` | FAIL → mode-flag wiring BLOCK |
| **G.11** | Anchor-byte gate | `ITERATION_LABEL == "v3-081"`; `vol_scale_floor_per_symbol == {}`; `DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0)`; `V3_MODELS` = 3 sym; `OOS_CUTOFF_DATE`/`training_months` immutable | FAIL → process-integrity BLOCK |

Falsifier for the hypothesis: if /081 IS or OOS monthly Sharpe falls OUTSIDE ±0.20 of the /059 anchor, the "reproduces within tolerance" hypothesis is rejected and the re-anchor branch (Section 8.2) fires.

## Section 5 — Risk Mitigation

**UNCHANGED 7-primitive stack** (the genuine /059 risk stack — the /081 revert restores it exactly):

| Primitive | Status at /081 | Source |
|---|---|---|
| BTC trend kill (±15%, 14d lookback) | ENABLED | iter-v3/051 (no-block; threshold 15%) |
| Vol scaling (RiskV2; floor `0.3`, ceiling `1.0`) | ENABLED — **global `0.3` floor for ALL 3 symbols** (the /081 revert removes the TRX-specific `0.5` override) | /059 canonical; restored by Sub-fix 1 |
| ADX threshold (global 20.0) | ENABLED | iter-v3/050 closeout (per-symbol ADX dict empty) |
| Hurst regime gate | DISABLED | iter-v3/022 (closed) |
| Feature z-score OOD (\|z\| > 2.0) | ENABLED | iter-v3/011 |
| Low-vol filter | ENABLED | carry-forward |
| Hit-rate gate | DISABLED | OOS-only; not active |
| Primitive 9 (regime-conditional kill switch) | DISABLED | iter-v3/074 closeout (CLOSED across 2 data points) |
| Primitive 11 (per-symbol drawdown brake) | DISABLED | iter-v3/054 closeout (CLOSED-mechanism) |
| Primitive 12 (BTC-trend-regime size de-rate) | DISABLED | iter-v3/075 closeout (INERT; reverted) |
| Per-symbol PnL-share cap | DISABLED | iter-v3/020 closeout (`enable_per_symbol_cap=False`) |

**The /081 revert is itself a risk-mitigation correction**: it removes a per-symbol vol-floor that was raising TRX position sizing (floor `0.3` → `0.5`) above the canonical /059 level. Reverting it returns TRX to the same `0.3` global vol-scale floor as BCH and LDO — the calibrated /059 risk posture. The simulated historical effect (from the iter-v3/061 EDA Q4 counterfactual): on 13 IS TRX trades the floor's effect was a near-zero +0.008 IS weighted_pnl; on the OOS side a non-significant +0.47 weighted_pnl. Removing the floor un-does both — moving TRX back to the /059 measurement, which is the intent.

No NEW risk primitive is added at /081 — a CONFIRMATION validates, it does not explore. The risk stack /081 measures IS the /059 risk stack.

## Section 6 — Risk Management Design

**UNCHANGED from /059** except the Sub-fix 1 revert.

- **Triple-barrier labeling**: TP = 2.0×ATR_at_entry, SL = 1.0×ATR_at_entry, 21-candle (10080-min / 8h) timeout — `DEFAULT_ATR_MULTIPLIERS=(2.0,1.0)`, `V3_ATR_MULTIPLIERS_PER_SYMBOL={}` (universal — all 3 symbols).
- **Position sizing**: vol-scaled `weight_factor` = clip(`1 - atr_pct_rank_200`, floor, ceiling). Post-revert: floor `0.3`, ceiling `1.0`, GLOBAL for all 3 symbols (TRX no longer floored at `0.5`).
- **Cooldown**: 4 candles (32h) post-trade — UNCHANGED.
- **Fee**: 0.1% per leg — UNCHANGED.
- **CPCV**: n_paths=45, embargo=27, `REQUIRED_GAP=66 = (21+1)×3` — UNCHANGED (3-symbol universe).
- **Walk-forward embargo (POST-FIX)**: `compute_embargo_candles(10080, 480) = 22` candles; `train_end_ms = test_start_ms − embargo_ms`; single source of truth shared with `lgbm._train_for_month()`. The walk-forward lookahead bug is FIXED in this worktree (commit `e149e9d`, the iter-v3/058 RE-ANCHOR — verified by every Critic /074-/080; per `feedback_v3_walkforward_lookahead_bug.md` the brief MUST NOT cite the bug as live).

**Fire-rate / regime coverage**: /081 reproduces /059's gate fire-rates by construction (same gates, same thresholds). The one delta — the TRX vol-floor revert — slightly lowers TRX `weight_factor` on the 13 previously-floored trades; it changes no gate's *fire* decision (vol scaling scales weight, it does not kill signals). Gate fire-rates are otherwise /059-identical.

## Section 7 — Pre-Registered Failure-Mode Prediction

/081 is a re-validation of /059's exact config (post-revert). The "failure modes" are re-validation outcomes, not edge-axis failures.

| Mode | Description | Probability | Expected metrics |
|---|---|---:|---|
| **CONFIRMED** | /081 reproduces /059 within ±0.20 on BOTH IS and OOS monthly Sharpe; all hard-blocking gates PASS; `BASELINE_V3.md` UNCHANGED | **~62%** | IS Δ ∈ [−0.20,+0.20] AND OOS Δ ∈ [−0.20,+0.20] vs /059 |
| **RE-ANCHOR-UP** | /081 drifts beyond ±0.20 and BEATS /059 on BOTH axes (most plausibly OOS data-extent growth lifting both); `BASELINE_V3.md` ratchets to /081 | **~16%** | IS Δ > +0.20 AND OOS Δ > +0.20 |
| **DRIFT-NO-ANCHOR (mixed)** | /081 drifts beyond ±0.20 on one or both axes but does NOT improve BOTH (e.g. OOS up, IS down — Optuna stochasticity); `BASELINE_V3.md` UNCHANGED with a staleness note | **~17%** | one axis outside ±0.20 without a BOTH-improve |
| **METHODOLOGY-FAIL** | a hard-blocking gate FAILs (Gate 3 / 6 / 10-CPCV) OR a Critic BLOCK OR the vol-floor revert wiring fails OR a SUSPICIOUS ratio | **~5%** | gate FAIL or Critic BLOCK |

**The single most plausible way /081 "fails"** (most-plausible failure narrative, per the Section-7 mandate): a **mixed drift** — the OOS Sharpe lifts beyond +0.78 because ≈2 extra calendar months of OOS uptrend data inflate it (the /077 +0.0675 data-extent mechanism, amplified by a longer horizon), while the IS Sharpe drifts down past +0.89 purely from Optuna TPE landing on a different-but-IS-equivalent hyperparameter basin run-to-run. This is the cycle-1 `feedback_v3_strict_both_is_oos_baseline.md` pattern (the /039 / /070 IS-down/OOS-up signature) reappearing as pure measurement noise rather than an axis effect. The gates catch it: `feedback_v3_strict_both_is_oos_baseline.md` BOTH-must-improve means a mixed drift does NOT re-anchor — /059 stays canonical with a staleness note, and the IS drift is recorded as Optuna run-to-run variance (a known, non-axis effect). What this looks like in metrics: OOS monthly Sharpe ≈ +0.85–1.05, IS monthly Sharpe ≈ +0.80–0.89, OOS/IS ratio rising toward ≈ 1.0–1.3 (still well under the 3.0 SUSPICIOUS gate). The Phase 8 diary verifies this prediction against the actual /081 outcome.

A secondary failure mode worth pre-registering: the vol-floor revert is a one-line change with a runner pre-flight assertion guarding it (Sub-fix 2) — if the Engineer reverts the config line but not the assertion (or vice versa), the run aborts at pre-flight. That is a caught failure (BLOCK at Phase 6 pre-flight), not a silent corruption. The Phase 5.5 gate verifies both the config line AND the assertion are reverted consistently.

## Section 8 — Pre-Registered MERGE/NO-MERGE + Re-Validation/Re-Anchor Criteria (LOCKED)

Cycle 2 produced **0 PROMISING edge ingredients** — **there is NO edge to MERGE regardless of the /081 outcome.** The only LOCKED decision is CONFIRM vs RE-ANCHOR of the /059 baseline numbers. All thresholds below are LOCKED at brief LOCK (the setup commit) and cannot be retroactively renegotiated per `feedback_v3_axis_selection_quant_discipline.md`.

### Section 8.1 — CONFIRMED (the expected outcome) → `BASELINE_V3.md` UNCHANGED

ALL of:
- **G.1** IS monthly Sharpe ∈ [+0.8894, +1.2894] (i.e. within ±0.20 of /059's +1.0894).
- **G.2** OOS monthly Sharpe ∈ [+0.3791, +0.7791] (i.e. within ±0.20 of /059's +0.5791).
- **G.3** OOS/IS monthly Sharpe ratio ≥ 0.50.
- **G.4** frac_positive_paths (CPCV) ≥ 0.55.
- **G.5** PBO mean < 0.40.
- **G.6** PSR (legacy) > 0.95.
- **G.7** OOS/IS monthly Sharpe ratio ≤ 3.0 (not SUSPICIOUS).
- **G.8-G.11** process gates (vol-floor revert effective; tests green; `mode=confirmation`/`size=10`; anchor-byte).

→ **/059 is CONFIRMED.** `BASELINE_V3.md` is UNCHANGED — /059 stays canonical at tag `v0.v3-059`. **No new tag.** The diary records that the /081 cycle-2 CONFIRMATION re-validated the genuine /059 canonical config (post the /061-accretion revert) and reproduced the /059 numbers within tolerance — and that the runner's illegitimate /061 vol-floor accretion was removed (a permanent measurement-integrity correction). Diary outcome label: **CONFIRMATION-REVALIDATE (no baseline change)** — by direct analogy to cycle 1's /070 NO-MERGE re-validation.

### Section 8.2 — DRIFT → re-anchor decision per `feedback_v3_baseline_update_policy.md` + `feedback_v3_strict_both_is_oos_baseline.md`

If /081 falls OUTSIDE the ±0.20 band on EITHER axis (G.1 or G.2 fails):

**8.2(a) — RE-ANCHOR-UP**: IF /081 IS monthly Sharpe > +1.0894 **AND** /081 OOS monthly Sharpe > +0.5791 (BEATS /059 on BOTH axes — `feedback_v3_strict_both_is_oos_baseline.md` BOTH-must-improve) **AND** all hard-blocking gates PASS (G.3 OOS/IS ≥ 0.50; G.6 PSR > 0.95; G.4 frac_positive_paths ≥ 0.55) **AND** G.7 not SUSPICIOUS → `BASELINE_V3.md` **RE-ANCHORS** to the /081 numbers; new tag `v0.v3-081` issued; the aspirational MERGE-gate failures (IS/OOS ≥ +1.0 floors, top-symbol ≤ 30%, OOS trades ≥ 130, legacy DSR > 0.95) are recorded as outstanding constraints but do NOT block the ratchet (same policy as /059's own RE-ANCHOR per `feedback_v3_baseline_update_policy.md`). This is a legitimate baseline ratchet driven by OOS data-extent growth, NOT an edge claim — /081 still bundles no edge.

**8.2(b) — DRIFT-NO-ANCHOR**: IF /081 drifts beyond ±0.20 on one or both axes but does NOT beat /059 on BOTH (OOS-only improvement with IS regression, or IS-only improvement with OOS regression, or any single-axis regression) → `BASELINE_V3.md` is **UNCHANGED**; /059 stays canonical at `v0.v3-081` is NOT issued; a staleness note is added to `BASELINE_V3.md` Measurement Discipline recording the observed /081 drift and its decomposition (Optuna run-to-run variance on IS; data-extent on OOS). This is the cycle-1 `/039`/`/070` IS-down/OOS-up precedent: OOS-only improvement with IS regression = NO baseline update.

### Section 8.3 — METHODOLOGY-FAIL → iteration INVALID

- Any Critic Phase-7.5 BLOCK (look-ahead, embargo, IC, ADF, hypothesis-implementation alignment, etc.).
- ANY of G.8-G.11 process gates FAIL (vol-floor revert ineffective; tests red; wrong `mode`/`size`; anchor-byte mismatch).
- A hard-blocking gate (G.3 OOS/IS ≥ 0.50, G.6 PSR > 0.95, G.4 frac_positive_paths ≥ 0.55) FAILs → no RE-ANCHOR is possible even on a BOTH-improve result; `BASELINE_V3.md` UNCHANGED; the failure is recorded.
- → Iteration is INVALID; not classifiable as CONFIRMED / RE-ANCHOR / DRIFT. A methodology root-cause fix becomes a NEW iter-v3/082.

### Section 8.4 — There is NO MERGE path

For absolute clarity: cycle 2 produced 0 PROMISING. /081 carries no edge ingredient. **No /081 outcome results in an edge "MERGE."** The outcomes are CONFIRMED (8.1), RE-ANCHOR-UP (8.2a — a data-extent ratchet, not an edge merge), DRIFT-NO-ANCHOR (8.2b), or METHODOLOGY-FAIL (8.3). The `BASELINE_V3.md`-update question is purely "do the /059 numbers stand, or does the canonical config's measurement ratchet on data growth" — never "did a new edge merge."

### Section 8.5 — `BASELINE_V3.md` edits regardless of outcome

Regardless of CONFIRMED / RE-ANCHOR / DRIFT:
- `BASELINE_V3.md` "Code Configuration" MUST be updated to record that `vol_scale_floor_per_symbol` is `{}` (the genuine /059 value) and that the iter-v3/061 accretion was reverted at /081 — this is a permanent measurement-integrity correction that persists independent of the headline outcome.
- The Measurement Discipline section MUST record the /081 re-validation result and (if DRIFT) the drift decomposition.

## Section 9 — Library Stack + Reproducibility

### Section 9.1 — Library versions (UNCHANGED from /059 — pinned)

- Python 3.13
- lightgbm 4.6.0
- optuna 4.8.0 (`n_jobs=1` — per `feedback_v3_unified_10seed_baseline.md` Phase A revert; `n_jobs=2` caused 5× GIL slowdown)
- numpy 2.2.6
- pandas 3.0.0
- scikit-learn 1.8.0
- scipy 1.17.0
- statsmodels 0.14.6
- pyarrow 23.0.1

No fallback libraries are used (`mlfinlab`/`mlfinpy`/`pypbo`/`fracdiff` were the iter-v3/001 methodology-stack deps; the v3 CPCV/PBO/PSR implementation is in-tree at `validation_v3.py` and is UNCHANGED at /081).

### Section 9.2 — No new integration test required

/081 adds NO new methodology field, NO new computed column, NO new feature, NO new risk primitive. The `feedback_v3_methodology_axis_integration_test.md` mandate (a 6th integration test + end-to-end smoke test for methodology-only axes that ADD computed fields) does NOT apply — /081 *removes* an EXPLORATION accretion and changes no output schema. The existing test suite (incl. `test_per_symbol_vol_scale_floor.py`, which still validates the per-symbol-floor MECHANISM) provides full coverage. The Engineer runs `uv run pytest` and confirms green.

### Section 9.3 — Data freshness pre-flight (Phase 6 mandatory)

Per the `BASELINE_V3.md` Data Extent Rule: every `data/<SYMBOL>/8h.csv` must have `close_time` within 16h of measurement time. The Engineer's Phase-6 pre-flight verifies BCH/LDO/TRX freshness and re-fetches via `uv run crypto-trade fetch --interval 8h --symbols BCHUSDT,LDOUSDT,TRXUSDT` if stale, then regenerates v3 features. The forming-candle filter (`fetcher.py: if k.close_time < now_ms`) is non-negotiable.

### Section 9.4 — Reproducibility stamp

- EDA SHA: `be0ccf5` (`analysis/iteration_v3-081/baseline_integrity_audit.py`)
- Setup commit SHA: `TBD` (this commit — backfilled into Section 10 at Phase 5.5)
- `ITERATION_LABEL`: `"v3-081"`
- `vol_scale_floor_per_symbol` at runtime: `{}` (the /081 revert — genuine /059 value)
- `DEFAULT_ATR_MULTIPLIERS` at runtime: `(2.0, 1.0)`
- `V3_ATR_MULTIPLIERS_PER_SYMBOL`: `{}` (empty — universal)
- `V3_MODELS`: BCHUSDT, LDOUSDT, TRXUSDT (3 symbols)
- `REQUIRED_GAP`: 66 = (21+1)×3
- `ENSEMBLE_SIZE`: 10 (CONFIRMATION mode)
- `ENSEMBLE_SEEDS`: full 10-tuple unified
- `n_trials`: 35 default
- Run command: `uv run python run_baseline_v3.py --clean-oof` (no `--exploration`)
- Hardware: x86_64, 60 GB RAM, WSL2 / Linux 6.6.114.1
- Wall-clock cap: 6h (`feedback_v3_cadence_discipline.md`)

### Section 9.5 — Pre-flight checks (Phase 5.5 mandatory)

- [ ] EDA committed — `analysis/iteration_v3-081/baseline_integrity_audit.py` + the 4 CSVs (T1-T4)
- [ ] Brief Section 2 cites the T1-T4 tables with concrete numbers
- [ ] Sub-fix 1 applied: `_build_v3_model` `vol_scale_floor_per_symbol={}` — TO BE VERIFIED at Phase 5.5
- [ ] Sub-fix 2 applied: runner pre-flight assertion `expected_floor_dict = {}` — TO BE VERIFIED (consistency with Sub-fix 1)
- [ ] Sub-fix 3 applied: `ITERATION_LABEL == "v3-081"` — TO BE VERIFIED
- [ ] Sub-fix 4: `grep -rn "vol_scale_floor_per_symbol" tests/` — any `_build_v3_model` runner-config assertion updated to `{}` — TO BE VERIFIED
- [ ] `uv run pytest` green — TO BE VERIFIED at Phase 5.5 (on affected dirs) and Phase 6 (full)
- [ ] Cadence: 10 cycle-2 EXPLORATION precedents /071-/080 listed (Section 0.5.1) — Phase 5.5 verifies count ≥ 10
- [ ] `--exploration` flag ABSENT from the run command (CONFIRMATION mode)
- [ ] Sacred constants untouched: `OOS_CUTOFF_DATE=2025-03-24`, `training_months=24`

## Section 10 — QR Audit Trail

### Section 10.1 — Why a re-validation, and why this config

Per `feedback_v3_axis_selection_quant_discipline.md`: axis/config selection must be QR-EDA-driven with a committed `analysis/` script.

1. **Why /081 is a re-validation, not a bundle**: cycle 2's 10 EXPLORATIONs (/071-/080) produced 0 clean PROMISING (Section 0.5.1). A CONFIRMATION bundles PROMISING findings (`feedback_v3_cadence_discipline.md` rule 4) — there are none. Cycle 1's /070 hit the identical situation and was a NO-MERGE re-validation of /059. /081 follows the /070 precedent and the /080 Critic Rec #1 directive verbatim.

2. **Why the config is the legitimate /059 canonical config (with the one revert)**: the `analysis/iteration_v3-081/baseline_integrity_audit.py` EDA (T1-T4) audited every behavior-affecting config knob between the /059 setup commit `20095a8` and HEAD. Exactly ONE is illegitimate accretion — `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` from the INERT, never-merged iter-v3/061 EXPLORATION. /081 reverts it. Every other axis tested in cycles 1-2 was already reverted at its closeout (HEAD == /059 on all other knobs). The config /081 runs is therefore the genuine /059 canonical config.

3. **Why /081 is the FIRST genuine /059 re-measurement**: cycle 1's /070 CONFIRMATION also ran with the /061 floor active (T2 row 8 — `git show aab9347:run_baseline_v3.py` carries it). /081, post-revert, is the first CONFIRMATION-class run since /059 itself to measure the true /059 canonical config.

### Section 10.2 — Memory-rule compliance

- **`feedback_v3_strict_10_to_1_cadence.md`**: /081 is the SEPARATE CONFIRMATION after 10 SEPARATE EXPLORATIONs (/071-/080); the 10th EXPLORATION (/080) was NOT collapsed into /081.
- **`feedback_v3_cadence_discipline.md`**: CONFIRMATION mode, `--seeds 2` (deprecated/ignored under unified arch), `--n-trials 35`, 6h HARD CAP, ≥10 EXPLORATION precedents.
- **`feedback_v3_confirmation_n_trials_35.md`**: `--n-trials 35`.
- **`feedback_v3_unified_10seed_baseline.md`**: `ENSEMBLE_SIZE=10` unified, DEFAULT mode (no `--exploration`), single deterministic trade roster, full 10-tuple `ENSEMBLE_SEEDS`.
- **`feedback_v3_baseline_update_policy.md`**: Section 8.2 re-anchor logic — STRICTLY-BETTER on BOTH IS+OOS; hard-blocking Gates 3/6/10-CPCV; aspirational gates inform priorities but do not block a ratchet.
- **`feedback_v3_strict_both_is_oos_baseline.md`**: Section 8.2 — RE-ANCHOR only on a BOTH-IS-AND-OOS improvement; OOS-only improvement with IS regression = NO baseline update.
- **`feedback_v3_exploration_anchor_staleness.md`**: Section 2.4 — the /077//080 "current-code /060-config" numbers are an EXPLORATION-MODE-REFERENCE (3-seed, and they carry the /061 floor); they are NOT the /081 CONFIRMATION target. The /059 CONFIRMATION anchor is unaffected by EXPLORATION-MODE-REFERENCE staleness.
- **`feedback_v3_walkforward_lookahead_bug.md`**: the bug is FIXED (commit `e149e9d`, /058 RE-ANCHOR); the brief does NOT cite it as live (Section 6).
- **`feedback_no_cheating.md`**: sacred constants immutable (Section 0); the Sub-fix 1 revert is the anti-drift discipline being APPLIED (removing an un-reverted EXPLORATION axis), not violated.
- **`feedback_v3_oos_is_ratio_gate.md`**: Section 4.4 + Gate G.7 — OOS/IS ratio > 3.0 → SUSPICIOUS, pre-registered.
- **`feedback_v3_axis_saturation_predictor.md`**: Section 4.3 — behavioral-effect predictor with a falsifier.
- **`feedback_v3_axis_selection_quant_discipline.md`**: the config decision is QR-EDA-driven (`baseline_integrity_audit.py` committed before the brief LOCK).
- **`feedback_v3_engineered_feature_pivot.md`**: Section 2.6 — inherited Category-2 IC carve-out documented; no feature change at /081.

### Section 10.3 — /080 Critic Recommendations addressed

The /080 closeout (Critic FINAL `35fc6de`) carried 3 recommendations to /081:
1. **Rec #1 ("/081 is a /059-baseline multi-seed re-validation; pre-register the re-validation branch; carry the 3 standing constraints into cycle 3")** — ADDRESSED: Section 0.5.2 + Section 1 + Section 8 pre-register the re-validation explicitly; the 3 standing constraints (LDO directional weakness; BCH ~96% IS-PnL concentration; the bull-month entry-discrimination drag) are carried to the Section 11 cycle-3 forward pointer.
2. **Rec #2 + Rec #3 (cycle-3 conviction-derate re-attempt — place `C_REF` against the per-trade `confidence` column; first prove a materially-populated below-threshold band exists)** — these are cycle-3 EXPLORATION concerns, recorded in Section 11 for the cycle-3 agenda; the conviction-derate axis remains PARKED. /081 is a CONFIRMATION and introduces no new axis.

### Section 10.4 — Cannot be retroactively renegotiated

Section 8 LOCKED (CONFIRM ±0.20 both axes; RE-ANCHOR BOTH-improve; hard-blocking Gates 3/6/10-CPCV). Section 7 probability calibration LOCKED. Section 4 falsifier bands LOCKED. Section 3 config (the genuine /059 canonical config with `vol_scale_floor_per_symbol` reverted to `{}`) LOCKED. Established at brief LOCK (the setup commit).

---

## Section 11 — Forward Pointer (cycle 3)

Per `feedback_v3_bold_research_mandate.md` (user directive 2026-05-16): cycle 3 must be substantially BOLDER than cycle 2. Cycle 2's 0/10-clean-PROMISING record is the direct evidence — the conservative axis families (gate-threshold knobs, risk primitives, single-symbol swaps, labeling tweaks, instrumentation) are exhausted against the narrow 3-symbol BCH/LDO/TRX universe. The detailed cycle-3 agenda is authored at the /081 CONFIRMATION closeout; the direction (from the /080 diary):

1. **Genuine literature + crypto-native-alpha research** — funding rates (8h-cycle aligned), open interest dynamics, basis / cross-exchange premium, liquidation cascades, on-chain flow — NEW feature *families*, not knob-tweaks.
2. **Aggressive symbol-universe exploration** — v3 has been locked to BCH/LDO/TRX for the entirety of cycles 1+2; the allowed universe is far wider (excludes only v1/v2 symbols + MKR). BCH's ~96% IS-PnL dominance is itself evidence a 3-symbol universe is structurally fragile.
3. **Bold structural axes** — NEW crypto-native feature families, NEW model architectures, multi-symbol-pooled models.

The 3 standing unresolved constraints carried into cycle 3: **(a) LDO directional weakness** (LDO dragged every cycle-1 and cycle-2 iteration); **(b) BCH ~96% IS-PnL concentration fragility**; **(c) the bull-month entry-discrimination drag** (the /077 reframing — IS_BULL Sharpe +0.4100 / 33% positive vs IS_BEAR_CHOP +1.2909 / 47% positive).

---

**Setup commit SHA**: `TBD` (this commit)

**Reading order for Engineer (Phase 6)**:
1. Verify branch `iteration-v3/081`; pull the EDA SHA (`analysis/iteration_v3-081/baseline_integrity_audit.py`).
2. Apply Sub-fixes 1-4: `vol_scale_floor_per_symbol={}` in `_build_v3_model`; runner pre-flight assertion `expected_floor_dict={}`; `ITERATION_LABEL="v3-081"`; `grep -rn "vol_scale_floor_per_symbol" tests/` and update any `_build_v3_model` runner-config assertion to `{}`.
3. Run `uv run pytest` — confirm green (incl. `test_per_symbol_vol_scale_floor.py` — the MECHANISM test, unchanged).
4. Data-freshness pre-flight on BCH/LDO/TRX (Section 9.3); re-fetch + regenerate features if stale.
5. Run `uv run python run_baseline_v3.py --clean-oof` (Phase 6 backtest; CONFIRMATION mode — NO `--exploration`).
6. Wall-clock target ~3.5h; HARD CAP 6h per `feedback_v3_cadence_discipline.md`.
7. Engineering report covers the Section 8 LOCKED criteria (CONFIRMED / RE-ANCHOR-UP / DRIFT-NO-ANCHOR / METHODOLOGY-FAIL), each gate G.1-G.11 PASS/FAIL, and the vol-floor revert effectiveness check (G.8), for the Critic Phase 7.5.
