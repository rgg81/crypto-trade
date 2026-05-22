# iter-v3/066 — Research Brief

**Branch**: `iteration-v3/066`
**EDA SHA**: `1d75cb0`
**Setup commit SHA**: (this commit, LOCKED)
**Iteration type**: EXPLORATION (cycle 1 #7 of 10; NON-FEATURE PIVOT CONTINUATION per Critic /064 Rec #4; RISK PRIMITIVE axis)
**Axis**: UNIVERSAL vol-scale ceiling — `RiskV2Config.vol_scale_ceiling` default 1.0 → 0.8 (Path E0.8 per EDA)

---

## Section 0 — Data Split Declaration

**UNCHANGED.** OOS_CUTOFF_DATE = `2025-03-24` (IMMUTABLE; sacred constant per `feedback_no_cheating.md`). Training window = 24 months walk-forward (IMMUTABLE per `feedback_training_window.md`). Symbol universe = BCHUSDT, LDOUSDT, TRXUSDT (3 symbols, UNCHANGED from /051 SYSTEM-LEVEL REVERT). Feature universe = 14 V3_FEATURE_COLUMNS (UNCHANGED post-/064 revert at commit `04080c4`).

## Section 0.5 — Iteration Type Declaration

**TYPE**: EXPLORATION.

- **Cycle 1 EXPLORATION slot**: #7 of 10 (post /058 RE-ANCHOR + /059 RE-ANCHOR #2; cycle counting per BASELINE_V3.md /059).
- **Sub-type**: **NON-FEATURE PIVOT CONTINUATION — RISK PRIMITIVE axis**. Per Critic /064 Rec #4 NON-FEATURE pivot mandate (LOCKED for /065-/068 per `feedback_v3_iter064_process_lessons.md` Rule 5). /065 chose UNIVERSAL labeling axis (PROMISING — SUSPICIOUS-OOS-DOMINANT); /066 pivots to UNIVERSAL RISK PRIMITIVE axis for structural orthogonality at /069 CONFIRMATION bundling.
- **Run mode**: `--exploration` (ENSEMBLE_SIZE=3, seeds from outer=42 lineage subset [191664963, 1662057957, 1405681631]).
- **Optuna budget**: `--n-trials 35` per (symbol × walk-forward month × seed). Total trials = 35 × 3 × 3 = 315 (matches /060-/065 EXPLORATION-mode budget).
- **Wall-clock target**: ~1.1h (within 2h EXPLORATION HARD CAP per `feedback_v3_cadence_discipline.md`).

**Cycle 1 catalog status before /066**:

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE (anchor) | PROMISING-EXPLORATION |
| #2 | /061 | TRX RiskV2 anti-Kelly (Path B vol_scale_floor) | INERT-AT-EXPLORATION (closed) |
| #3 | /062 | DSR_relative recalibration (Path C passive) | PASSIVE-DIAGNOSTIC (Path B4 deferred to /069) |
| #4 | /063 | MASS FEATURE EXPANSION (Path B 46 features) | SUSPICIOUS-OOS-DOMINANT + IS-COLLAPSE (closed) |
| #5 | /064 | Phased mass-expansion #1 (+adx_14) | NEGATIVE (closed) |
| #6 | /065 | NON-FEATURE PIVOT: UNIVERSAL SL widen 1.0 → 1.5 (Path D) | SUSPICIOUS-OOS-DOMINANT (first /069 candidate) |
| **#7** | **/066** | **NON-FEATURE PIVOT cont: UNIVERSAL vol_scale_ceiling 1.0 → 0.8 (Path E0.8)** | TBD |
| #8-9 | /067-068 | TBD per QR EDA | TBD |
| CONFIRMATION | /069 | Bundle: SL=1.5 + (Path E0.8 if PROMISING) + Path B4 implementation | TBD |

**Why NON-FEATURE pivot continuation + RISK PRIMITIVE axis now**:

1. **Critic /064 Rec #4 directive (binding through /068)**: NON-FEATURE axis pivot mandated after /060 14-feature anchor classified as LOCAL OPTIMUM at single-seed n_trials=35.

2. **Cycle 1 bundle diversity at /069 CONFIRMATION**: /065's PROMISING-class labeling axis is the first /069 advancement candidate. A SECOND independent PROMISING-class component from a structurally distinct axis (risk primitive) strengthens the /069 bundle by reducing single-axis dependence. Per Critic /065 Rec #4 bundle pre-registration: /069 CONFIRMATION evaluates the BUNDLE, not each axis in isolation.

3. **Risk primitive is mechanistically orthogonal to labeling axis** (T6 verified at EDA SHA `1d75cb0`):
   - /065 labeling axis: TRAIN-TIME label generation; `Signal(.tp_pct, .sl_pct)` change
   - /066 risk primitive axis: INFERENCE-TIME weight modifier; `Signal(.weight)` change
   - Separate code paths (`labeling.py` vs `risk_v2.py`); separate execution-time state

4. **Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`** (system-level confirmed across 2 CONFIRMATIONs at /039 + /050): per-symbol customizations break IS aggregate at multi-seed. UNIVERSAL risk primitive is the structurally safe alternative.

5. **Per `feedback_v3_oracle_eda_validity.md` (iter-v3/054 closeout)**: stateful risk gates (drawdown brake, DSR kill switch) have deadlock risk and ORACLE EDA cannot test them. STATELESS risk primitives (vol-scale floor, vol-scale ceiling) ARE ORACLE-testable. Path E (universal vol_scale_ceiling) is STATELESS.

## Section 1 — Testable Hypothesis (ONE sentence)

> UNIVERSAL vol-scale ceiling tightening from `RiskV2Config.vol_scale_ceiling=1.0` to `0.8` produces ≥+0.10 IS Sharpe AND ≥+0.20 OOS Sharpe vs /060 baseline (IS +0.8325 / OOS +0.1403) primarily via LDO anti-Kelly correction (6 of 11 LDO OOS trades at wf≥0.8; OOS wpnl -19.72 driven by over-confident high-weight trades) while accepting modest TRX OOS Kelly cost (TRX is Kelly-aligned at high wf), with ORACLE first-order prediction IS Δ +0.008 / OOS Δ +0.022 (sign-aligned positive, sub-band magnitude → most likely INERT-AT-EXPLORATION classification, with PROMISING upside if Optuna second-order re-converges favorably under tighter weight bound).

## Section 2 — Numerical EDA Tables (EDA SHA `1d75cb0`)

EDA committed at SHA `1d75cb0` (`analysis/iteration_v3-066/risk_primitive_eda.py`). Produces 7 tables (T0-T6). Anchor = iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403; 3-seed lineage subset of /059's unified 10-seed mass). **NOT iter-v3/065** (parallel SUSPICIOUS-OOS-DOMINANT candidate, not new anchor; per /065 closeout BASELINE_V3.md remains anchored at /059).

### Section 2.1 — T0 Anchor-value declaration (RECURRENCE flag from /065 Rec #1)

| metric | value | source (file:line) |
|---|---:|---|
| monthly_sharpe_in_sample | **+0.8325** | `reports-v3/iteration_v3-060/comparison.csv:2` |
| monthly_sharpe_out_of_sample | **+0.1403** | `reports-v3/iteration_v3-060/comparison.csv:2` |
| n_trades_in_sample | **159** | `reports-v3/iteration_v3-060/comparison.csv:7` |
| n_trades_out_of_sample | **102** | `reports-v3/iteration_v3-060/comparison.csv:7` |
| weighted_pnl_total_in_sample | **+51.8906** | `reports-v3/iteration_v3-060/comparison.csv:10` |
| weighted_pnl_total_out_of_sample | **+5.4989** | `reports-v3/iteration_v3-060/comparison.csv:10` |
| BCH_OOS_weighted_pnl | **+1.9078** | `reports-v3/iteration_v3-060/comparison.csv:18` |
| LDO_OOS_weighted_pnl | **-19.7208** | `reports-v3/iteration_v3-060/comparison.csv:19` |
| TRX_OOS_weighted_pnl | **+23.3119** | `reports-v3/iteration_v3-060/comparison.csv:20` |
| frac_positive_paths_cpcv | **0.6444** | BASELINE_V3.md Headline Metrics (CPCV invariant across architectures) |

These are the BIT-EXACT /060 anchor values per Phase 5.5 anchor-value correctness gate (Rule 1 of `feedback_v3_iter064_process_lessons.md`; RECURRENCE flag from /065 Critic Rec #1). Brief Section 4 falsifier bands reference these. All anchor citations in subsequent Section 4 tables MUST match T0 byte-exactly.

### Section 2.2 — T1 Current 7-primitive risk gate inventory

Production state at /065 (RiskV2Config in `run_baseline_v3.py:1377-1419`):

| ID | Primitive | Formula | Current Config | Category |
|---:|---|---|---|---|
| 0 | Vol scaling (weight_factor) | `clip(atr_pct_rank_200, floor, ceiling)` | floor=0.3 (TRX 0.5), ceiling=1.0 (universal) | WEIGHTING (multiplicative) |
| 1 | Feature z-score OOD | abs(z) > threshold | zscore_threshold=2.0 | BINARY KILL (universal) |
| 2 | Hurst regime check | hurst_100 outside [Q05, Q95] IS | enabled (per /022 close) | BINARY KILL (universal) |
| 3 | ADX gate | ADX_14 < threshold | adx_threshold=20.0 (TRX 21 dropped /050) | BINARY KILL (universal) |
| 4 | Low-vol filter | atr_pct_rank_200 < 0.33 | enabled (iter-v2/004) | BINARY KILL (universal) |
| 5 | Per-symbol PnL cap | scaled_weight if share > cap | enable_per_symbol_cap=False (CLOSED /020) | WEIGHTING (proportional) |
| 6 | Regime-conditional kill (primitive 9) | BTC dd_30d > 20% OR vol_z > 1.5 | enable_regime_gate=False (CLOSED /023) | BINARY KILL (per-symbol scope) |
| 7 | Direction-asymmetric kill (primitive 10) | kill if direction in block_list | block_long_for=() (CLOSED /051 SYSTEM REVERT) | BINARY KILL (per-symbol) |
| 8 | Per-symbol drawdown brake (primitive 11) | pause when 30d dd >= threshold | enable_per_symbol_drawdown_brake=False (CLOSED /054) | STATEFUL KILL |
| 9 | BTC trend filter (post-trade) | kill if fights 14d BTC trend > 15% | BTC_TREND_CONFIG.threshold_pct=15.0 enabled | BINARY KILL (post-trade, universal) |

**Active universal weight modifiers**: ONLY primitive 0 (vol scaling). Ceiling is the unmodified slot — currently 1.0 (`risk_v2.py:58`) — no prior EXPLORATION has tested ceiling tightening.

**Per-symbol overrides currently active** (per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` system-level constraint): only `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` from /061. iter-v3/066 does NOT add per-symbol overrides; preserves universal discipline.

### Section 2.3 — T2 /060 weight_factor distribution per (split, symbol)

| split | symbol | n_total | n_killed (wf=0) | n at floor (wf=0.3) | n in (0.3, 0.4) | n in [0.4, 0.8) | n in [0.8, 1.0) | n at ceiling (wf=1.0) | wpnl_total |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| IS | BCHUSDT | 73 | 13 | 0 | 7 | 29 | 20 | 4 | +78.34 |
| IS | LDOUSDT | 11 | 1 | 0 | 2 | 4 | 2 | 2 | -1.66 |
| IS | TRXUSDT | 75 | 12 | 0 | 6 | 27 | 27 | 3 | -24.79 |
| OOS | BCHUSDT | 37 | 2 | 0 | 5 | 15 | 15 | 0 | +1.91 |
| OOS | LDOUSDT | 11 | 0 | 0 | 0 | 5 | 5 | **1** | **-19.72** |
| OOS | TRXUSDT | 54 | 3 | 0 | 5 | 26 | 19 | 1 | +23.31 |

**Reading**:
- **NO trades sit at exactly wf=0.3** in /060 — atr_pct_rank_200 distribution rarely hits the floor; weight_factor in /060 is dominated by raw `atr_pct_rank_200` clipped only at ceiling=1.0 (4 IS BCH + 3 IS TRX hit ceiling; 1 OOS LDO + 1 OOS TRX hit ceiling).
- **LDO OOS concentration above wf=0.8**: 6 of 11 LDO OOS trades (54.5%) at high weight; LDO OOS wpnl = -19.72 — these high-weight trades are anti-Kelly (over-confident in volatile regime where LDO's model failed OOS).
- **BCH OOS at high weight**: 15 of 37 (40.5%) ≥0.8 wf; BCH OOS wpnl = +1.91 (small positive; high-weight contribution mixed).
- **TRX OOS at high weight**: 20 of 54 (37.0%) ≥0.8 wf; TRX OOS wpnl = +23.31 — high-weight trades are Kelly-aligned (winners get amplified).

The LDO OOS pattern is the structural target of Path E: cap LDO high-confidence trades that are systematically wrong in OOS regime.

### Section 2.4 — T3 Path counterfactuals (per Path, per symbol)

ORACLE counterfactual on /060 trade roster (held fixed; universal change does not regenerate trade emission):

| split | path | BCH wpnl Δ | LDO wpnl Δ | TRX wpnl Δ | TOTAL wpnl Δ |
|---|---|---:|---:|---:|---:|
| IS | B_floor_0.4 | +0.09 | -0.37 | -0.03 | **-0.31** |
| IS | B_floor_0.5 | +1.58 | -2.08 | -0.16 | **-0.67** |
| IS | E_ceiling_0.8 | **-9.40** | +3.69 | +1.79 | **-3.92** |
| IS | E_ceiling_0.7 | -17.33 | +3.57 | +3.75 | -10.01 |
| OOS | B_floor_0.4 | +0.25 | 0.00 | +0.02 | **+0.27** |
| OOS | B_floor_0.5 | +0.50 | -0.79 | +0.59 | **+0.30** |
| OOS | E_ceiling_0.8 | -0.87 | **+2.66** | -1.51 | **+0.29** |
| OOS | E_ceiling_0.7 | -2.11 | +4.47 | -3.33 | -0.97 |

**Reading**:
- Path B0.4: smallest disruption (IS Δ -0.31, OOS Δ +0.27); LDO IS mild damage (-0.37 wpnl).
- Path B0.5: bigger LDO IS damage (-2.08 wpnl from Kelly-aligned LDO mid-weight winners getting penalized).
- **Path E0.8: LDO anti-Kelly correction** (LDO OOS Δ +2.66 wpnl from capping 6 high-wf losers) AND IS OOS gains (+1.79 wpnl from Kelly-aligned high-wf BCH trades). NET OOS portfolio gain.
- Path E0.7: ORACLE FAIL — IS Δ -10.01 catastrophic (BCH IS loses 17 wpnl from over-aggressive ceiling). Excluded.

### Section 2.5 — T4 Path ORACLE monthly Sharpe Δ (HEADLINE metric)

| split | path | sharpe_baseline_060 | sharpe_counterfactual | sharpe_Δ |
|---|---|---:|---:|---:|
| IS | B_floor_0.4 | +0.8325 | +0.8268 | -0.0057 |
| IS | B_floor_0.5 | +0.8325 | +0.8142 | -0.0183 |
| IS | **E_ceiling_0.8** | +0.8325 | **+0.8409** | **+0.0084** |
| IS | E_ceiling_0.7 | +0.8325 | +0.8004 | -0.0321 |
| OOS | B_floor_0.4 | +0.1403 | +0.1462 | +0.0060 |
| OOS | B_floor_0.5 | +0.1403 | +0.1436 | +0.0034 |
| OOS | **E_ceiling_0.8** | +0.1403 | **+0.1623** | **+0.0221** |
| OOS | E_ceiling_0.7 | +0.1403 | +0.1397 | -0.0005 |

**Reading**:
- **Only Path E0.8 has SIGN-ALIGNED POSITIVE ΔSharpe** (IS +0.008, OOS +0.022).
- ORACLE ΔSharpe magnitudes are SMALL (all within ±0.04). This reflects vol-scaling's structural property: capping reduces mean wpnl AND std proportionally — the dominant first-order effect is partial cancellation in the Sharpe ratio.
- This means **most likely classification at single-seed n_trials=35 = INERT-AT-EXPLORATION** (axis-PASS thresholds: IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 — neither met by ORACLE).
- BUT: ORACLE is a FIRST-ORDER predictor. Optuna at production may converge to different hyperparameters under tighter weight bound (e.g., model may emit signals more conservatively when high-confidence regions are capped). Second-order effect not modeled by ORACLE.

### Section 2.6 — T5 Path selection summary + scoring

| Path | IS Sharpe Δ ORACLE | OOS Sharpe Δ ORACLE | Sign-aligned + | Magnitude in band ±0.30 | Implementation cost (axes) | Methodology pass |
|---|---:|---:|:-:|:-:|---:|:-:|
| A_sortino_vol_scaling | N/A | N/A | NO | NO | 2 | FAIL |
| B_floor_0.4 | -0.006 | +0.006 | NO | YES | 1 | PASS |
| B_floor_0.5 | -0.018 | +0.003 | NO | YES | 1 | PASS |
| C_confidence_weighted_vol_scaling | N/A | N/A | NO | NO | 2 | FAIL |
| D_dsr_based_kill_switch | N/A | N/A | NO | NO | 1 | FAIL |
| **E_ceiling_0.8** | **+0.008** | **+0.022** | **YES** | **YES** | **1** | **PASS** |
| E_ceiling_0.7 | -0.032 | -0.001 | NO | YES | 1 | PASS-but-NEGATIVE-Δ |

**Path eliminations**:
- **Path A (Sortino-based vol scaling)** OUT: requires NEW feature column (`downside_dev_pct_rank_200`) AND risk_v2 logic change — 2-axis change violates `feedback_v3_engineered_features_dont_stack.md` single-axis discipline. Implementation cost = 2 axes.
- **Path C (confidence-weighted vol scaling)** OUT: requires Signal interface change (add `confidence` field — currently absent) AND risk_v2 logic change — 2-axis change. Implementation cost = 2 axes.
- **Path D (DSR-based kill switch)** OUT: STATEFUL gate updating on signal-emission. Per `feedback_v3_oracle_eda_validity.md` (established iter-v3/054 closeout): ORACLE EDA on prior trade roster is INVALID for stateful primitives. Risk of deadlock identical to iter-v3/054 brake (BCH+LDO brake-ON at OOS-start → no trades → no state update → frozen). Methodology fail.

**Path E0.8 quantitative justification (the QR selection)**:
1. **Only Path with sign-aligned POSITIVE ORACLE ΔSharpe** on both IS and OOS axes
2. **LDO OOS anti-Kelly correction** is the primary mechanism: 6 of 11 LDO OOS trades at wf≥0.8 with collective OOS wpnl heavily contributing to LDO's -19.72 OOS deficit; capping LDO high-wf trades gives +2.66 wpnl Δ
3. **BCH OOS limited damage** (-0.87 wpnl): only 15 of 35 BCH OOS trades at wf≥0.8; BCH OOS at /060 is near-zero (+1.91 wpnl) so symmetric ceiling impact is small
4. **TRX OOS modest cost** (-1.51 wpnl): TRX is the Kelly-aligned high-wf winner — universal change accepts this cost vs per-symbol asymmetry per system-level rule
5. **NET portfolio OOS** = +2.66 LDO + -0.87 BCH + -1.51 TRX = +0.28 wpnl (small positive)
6. **Single-axis change** (RiskV2Config.vol_scale_ceiling: 1.0 → 0.8 default; one explicit kwarg)
7. **Universal** (preserves IS aggregate per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`)
8. **Mechanistically ORTHOGONAL** to /065 SL widening axis (T6 verified)
9. **STATELESS** — ORACLE EDA validity confirmed per `feedback_v3_oracle_eda_validity.md`
10. **Anti-snooping note**: universal `vol_scale_ceiling=0.8` has NEVER been tested. /061 tested per-symbol vol_scale_floor; /066 tests universal vol_scale_ceiling — orthogonal mechanism.

### Section 2.7 — T6 Cross-axis orthogonality with iter-v3/065

| Check | iter-v3/065 (SL widening) | iter-v3/066 (vol-scale ceiling) | Isolated? |
|---|---|---|:-:|
| Code path | `src/crypto_trade/strategies/ml/labeling.py::label_trades` | `src/crypto_trade/strategies/ml/risk_v2.py::_vol_scale` | YES |
| Execution-time state | TRAIN-TIME label generation (atr_tp_multiplier, atr_sl_multiplier) | INFERENCE-TIME weight modifier (vol_scale_floor, vol_scale_ceiling) | YES |
| Signal field touched | `Signal(.tp_pct, .sl_pct)` | `Signal(.weight)` | YES |
| Trade roster emission | CHANGES roster (wider SL = some prior SL-hits become TP/timeout) | DOES NOT change roster (only weight applied to surviving trades) | YES |
| Optuna search-space coupling | Label distribution shift → TPE explores different model regions | Weight distribution shift → TPE explores different confidence regions | NO (second-order at /069 bundle) |
| Single-axis at /066 | (UNCHANGED at /066) DEFAULT_ATR_MULTIPLIERS reverts to (2.0, 1.0) | (CHANGED at /066) RiskV2Config.vol_scale_ceiling 1.0 → 0.8 | YES |
| Bundle at /069 | /065 SL=1.5 + /066 ceiling=0.8 (if PROMISING) — multi-seed | (bundled by design) | NO (bundled) |

**Verdict**: First-order MECHANISTICALLY ORTHOGONAL. Second-order Optuna coupling exists but is captured at /069 CONFIRMATION bundle. **iter-v3/066 reverts /065's DEFAULT_ATR_MULTIPLIERS=(2.0, 1.5) back to (2.0, 1.0)** so the single varied axis is the vol_scale_ceiling change.

### Section 2.8 — Anchor declaration

**Anchor**: iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403). **NOT iter-v3/065** (parallel SUSPICIOUS-OOS-DOMINANT candidate; not new anchor). Per `feedback_v3_cycle1_axis_pass_criteria.md`: cycle 1 EXPLORATIONs anchor on /060 (3-seed lineage subset of /059 10-seed CONFIRMATION); CONFIRMATION-mode delta vs /059 is evaluated only at /069 CONFIRMATION.

BASELINE_V3.md remains anchored at `v0.v3-059` per `feedback_v3_baseline_update_policy.md`.

### Section 2.9 — Summary

- Path E0.8 is the QR-selected risk-primitive axis per quantitative ORACLE analysis.
- ORACLE first-order predictor: IS Sharpe Δ +0.008, OOS Sharpe Δ +0.022 — sign-aligned positive but BELOW the PROMISING-AT-EXPLORATION thresholds (IS ≥ +0.10, OOS ≥ +0.20).
- Most likely classification = INERT-AT-EXPLORATION (per Section 7 calibrated probabilities).
- PROMISING upside exists via Optuna second-order re-convergence under tighter weight bound.
- Cross-axis orthogonality with /065 verified.

## Section 3 — Proposed Changes (enumerated)

### Sub-fix 1 — RiskV2Config.vol_scale_ceiling parameter override

**ONE substantive change**. Universal `vol_scale_ceiling` lowered from 1.0 to 0.8.

File: `run_baseline_v3.py` (in `_build_v3_model`, around line 1419 inside the `RiskV2Config(...)` call):

```python
# BEFORE — no explicit vol_scale_ceiling (defaults to 1.0 per risk_v2.py:58)
# After
vol_scale_ceiling=0.8,  # iter-v3/066: UNIVERSAL ceiling tightening 1.0 → 0.8 per Path E0.8 EDA SHA 1d75cb0
```

**Why this is the ONE change**: per `feedback_v3_engineered_features_dont_stack.md` single-axis EXPLORATION discipline. The `vol_scale_ceiling` is a SINGLE parameter in `RiskV2Config`. It applies UNIVERSALLY to BCH+LDO+TRX (no per-symbol override). `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` from /061 remains untouched (preserves iter-v3/061 intervention isolated from /066 axis).

**Why not change floor or other primitives**: per EDA T5, Path E0.8 is the only ORACLE sign-aligned positive Path. Path B (floor lift) variants show sign-conflict and small magnitudes; Path E0.7 shows ORACLE FAIL on IS axis. Combining ceiling + floor would be 2-axis variation forbidden under `feedback_v3_engineered_features_dont_stack.md`.

### Sub-fix 2 — DEFAULT_ATR_MULTIPLIERS REVERT to (2.0, 1.0)

iter-v3/065 set `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5)`. iter-v3/066 REVERTS this back to `(2.0, 1.0)` so the SINGLE varied axis vs /060 is `vol_scale_ceiling`.

File: `src/crypto_trade/features_v3/__init__.py` line 222

```python
# Before (iter-v3/065 state)
DEFAULT_ATR_MULTIPLIERS: tuple[float, float] = (2.0, 1.5)

# After (iter-v3/066 — revert /065's universal SL widening to isolate /066 axis)
DEFAULT_ATR_MULTIPLIERS: tuple[float, float] = (2.0, 1.0)
```

**Rationale**: per Section 2.7 T6 cross-axis orthogonality check and `feedback_v3_engineered_features_dont_stack.md` single-axis discipline. /065 is evaluated at /069 bundle CONFIRMATION; /066 must isolate its axis from /065.

### Sub-fix 3 — ITERATION_LABEL bump

File: `run_baseline_v3.py` line 128

```python
# Before
ITERATION_LABEL = "v3-065"

# After
ITERATION_LABEL = "v3-066"
```

### Sub-fix 4 — Test assertion updates

iter-v3/065 added test assertions for `DEFAULT_ATR_MULTIPLIERS == (2.0, 1.5)`. With the revert at Sub-fix 2, these assertions must revert to `(2.0, 1.0)`:

| File | Current assertion (post-/065) | New assertion |
|---|---|---|
| `tests/features_v3/test_features_for_symbol.py:285` | `DEFAULT_ATR_MULTIPLIERS == (2.0, 1.5)` | `DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0)` |
| `tests/features_v3/test_atr_multipliers_for_symbol.py:31,38` | `DEFAULT_ATR_MULTIPLIERS == (2.0, 1.5)` | `DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0)` |

Update docstrings + assertion messages to reference iter-v3/066 axis isolation rationale.

### Sub-fix 5 — Runner consistency assertion revert

iter-v3/065 set the runtime assertion at `run_baseline_v3.py:413-420` to expect `(2.0, 1.5)`. Revert to `(2.0, 1.0)`:

```python
# Before (iter-v3/065 state)
if DEFAULT_ATR_MULTIPLIERS != (2.0, 1.5):
    raise RuntimeError(...)

# After (iter-v3/066 — revert)
if DEFAULT_ATR_MULTIPLIERS != (2.0, 1.0):
    raise RuntimeError(
        f"DEFAULT_ATR_MULTIPLIERS = {DEFAULT_ATR_MULTIPLIERS} — expected (2.0, 1.0). "
        "iter-v3/066 axis isolation: /065's universal SL widening (2.0, 1.5) reverts "
        "to /060 baseline labeling (2.0, 1.0) so the single varied axis at /066 is "
        "RiskV2Config.vol_scale_ceiling=0.8 (Path E0.8 per EDA SHA 1d75cb0). "
        "/065 axis is bundled at /069 CONFIRMATION."
    )
```

### Sub-fix 6 — RiskV2Config vol_scale_ceiling assertion (new runtime gate)

Add a Phase 5.5-aligned runtime assertion mirroring the existing per-symbol `vol_scale_floor_per_symbol` check at `run_baseline_v3.py:663-688`:

```python
# After the existing vol_scale_floor_per_symbol check at line 688, add:
expected_ceiling = 0.8
if not hasattr(p13_strat_check, "config"):
    raise RuntimeError(
        "RiskV3Wrapper has no config attribute; cannot verify vol_scale_ceiling. "
        "expected RiskV3Wrapper. iter-v3/066: vol_scale_ceiling check requires "
        "RiskV3Wrapper around LightGbmStrategy."
    )
if p13_strat_check.config.vol_scale_ceiling != expected_ceiling:
    raise RuntimeError(
        f"RiskV2Config.vol_scale_ceiling = {p13_strat_check.config.vol_scale_ceiling} — "
        f"expected {expected_ceiling}. iter-v3/066 Path E0.8: universal ceiling "
        f"1.0 → 0.8 per EDA SHA 1d75cb0. "
        f"Set vol_scale_ceiling=0.8 in RiskV2Config init in _build_v3_model."
    )
print(
    f"  Universal vol_scale_ceiling (iter-v3/066): {expected_ceiling} "
    f"(Path E0.8 universal tightening from 1.0)"
)
```

### Sub-fix 7 — Parquet regeneration

**NOT required.** `atr_pct_rank_200` column is pre-computed in parquet (per `features_v3/__init__.py`); the ceiling change is consumed at INFERENCE time inside `risk_v2.py::_vol_scale`. No new feature columns; no parquet regen.

### Sub-fix 8 — ENSEMBLE_SIZE assertion

**UNCHANGED**. EXPLORATION_ENSEMBLE_SIZE=3, CONFIRMATION_ENSEMBLE_SIZE=10 (per Phase B-3 unified architecture). /066 runs with `--exploration` (ENSEMBLE_SIZE=3).

### Sub-fix 9 — V3_FEATURE_COLUMNS_TOP_N

**UNCHANGED**. Stays at 14 features post-/064 revert (commit `04080c4`). NON-FEATURE axis means feature universe is held constant.

## Section 4 — Predicted Bands + Falsifiers

### Section 4.1 — Headline Sharpe prediction (single-seed EXPLORATION mode)

| Metric | /060 anchor | Predicted /066 | Predicted Δ band |
|---|---:|---:|---|
| IS monthly Sharpe | +0.8325 | +0.65 to +1.00 | Δ ∈ [-0.20, +0.17] |
| OOS monthly Sharpe | +0.1403 | -0.20 to +0.45 | Δ ∈ [-0.34, +0.31] |
| OOS/IS daily ratio | 0.21 | 0.10 to 0.55 | within [0.10, 0.55] |
| IS trades | ~159 | 130 to 200 | Δ ∈ [-30, +40] |
| OOS trades | ~102 | 85 to 125 | Δ ∈ [-17, +23] |
| frac_positive_paths | 0.6444 | 0.50 to 0.75 | architecture-invariant ≥0.50 |
| BCH IS share | ~95% (/060) | 70% to 150% | one-sided ≥ 80% per Critic /060 Rec #1 |

**Rationale for band widths**: this is a UNIVERSAL RISK PRIMITIVE CHANGE (non-feature axis, non-labeling axis). Historical precedents:
- iter-v3/061 per-symbol vol_scale_floor (TRX 0.3→0.5): INERT-AT-EXPLORATION. The per-symbol axis had stronger ORACLE prediction than /066's universal ceiling; INERT was the outcome.
- iter-v3/041 universal feature pruning (drop-bottom-3): NEGATIVE; broke BCH -26 swing. But pruning is a structural feature change; vol-scale ceiling is a weighting change with smaller mechanism.
- /066 ORACLE first-order: IS Δ +0.008, OOS Δ +0.022 (small positive).
- Band widths are SLIGHTLY WIDER than ORACLE prediction (±0.20 IS, ±0.34 OOS) to account for:
  1. Optuna second-order TPE re-convergence under tighter weight space (potential PROMISING upside)
  2. 3-seed averaging variance noise floor (per `feedback_v3_cycle1_axis_pass_criteria.md` 3-seed variance ~±0.26 IS / ±0.44 OOS)
  3. Compounding small Sharpe shifts via monthly aggregation variance

### Section 4.2 — BCH IS sensitivity prediction (per /059 Critic Rec #3 carry-forward)

BCH IS share at /060 was 176.68% (3-seed averaging structurally amplified BCH's IS dominance vs LDO+TRX). The one-sided ≥80% gate applies per `feedback_v3_cycle1_axis_pass_criteria.md` Rec #1.

Universal vol_scale_ceiling tightening (1.0 → 0.8) is expected to:
- DAMPEN BCH high-confidence IS trades (BCH IS has 24 of 73 trades ≥0.8 wf — 4 at ceiling exactly)
- ORACLE BCH IS wpnl Δ = -9.40 wpnl (out of +78.34 total BCH IS wpnl); BCH IS still strongly positive
- BCH IS share should hold but may shift down from 176% to 100-150% range
- LDO IS share will likely lift (LDO ORACLE IS Δ = +3.69 wpnl out of -1.66 IS wpnl — could push LDO from net-negative to net-positive IS)
- TRX IS share will lift (TRX ORACLE IS Δ = +1.79 wpnl out of -24.79 IS wpnl)

**Predicted BCH IS share at /066**: 70% to 150% (one-sided ≥ 80% gate cleared in expectation; band wider than baseline because universal weighting change reshuffles per-symbol contributions).

### Section 4.3 — Behavioral effect predictor (per `feedback_v3_axis_saturation_predictor.md` + Critic /065 Rec #3 calibration)

**Predicted trade-count change** (vol_scale_ceiling does NOT change trade emission — only weight applied):

| Symbol | IS trades /060 | IS trades /066 predicted | OOS trades /060 | OOS trades /066 predicted |
|---|---:|---:|---:|---:|
| BCH | 73 | 65-85 (similar; Optuna second-order may shift confidence threshold) | 37 | 30-45 |
| LDO | 11 | 10-18 (similar) | 11 | 9-15 |
| TRX | 75 | 65-90 (similar; possible small Optuna shift) | 54 | 45-65 |
| **Total** | **159** | **[140, 193]** | **102** | **[84, 125]** |

**Behavioral-effect rationale**: vol_scale_ceiling tightens the upper bound on weight_factor but does NOT change the trade emission decision (direction or weight 100). The decision-stage code path (`LightGbmStrategy.get_signal`) is unchanged; the inference-stage code path (`RiskV2Wrapper._vol_scale`) is the only modified component. Therefore trade COUNT should be approximately invariant under Path E0.8.

**Per Critic /065 Rec #3 calibration for non-feature WEIGHTING axes**: predict per-symbol WR Δ within ±2pp (saturation falsifier for non-feature axes). Vol_scale_ceiling does not affect direction prediction; per-symbol WR should be approximately invariant.

| Symbol | IS WR /060 | OOS WR /060 | Predicted /066 WR Δ (IS) | Predicted /066 WR Δ (OOS) |
|---|---:|---:|---:|---:|
| BCH | 45.2% | 32.4% | ±2pp (saturation band) | ±2pp |
| LDO | 27.3% | 18.2% | ±2pp | ±2pp |
| TRX | 29.3% | 50.0% | ±2pp | ±2pp |

**Saturation falsifier (per `feedback_v3_axis_saturation_predictor.md` non-feature-axis extension)**: if per-symbol WR Δ is within ±2pp at all 3 symbols AND total trade count Δ within ±5%, the axis is INERT-AT-EXPLORATION (the weighting change had no effective downstream behavioral impact on trade selection).

### Section 4.4 — Pre-registered FALSIFIER bands (BINDING GATES)

All anchor references per Section 2.1 T0 declarations:

| Gate ID | Gate | Threshold | Action if FAIL |
|---|---|---|---|
| **A.1** | IS Sharpe shift | ≥ -0.20 vs /060 (i.e., IS ≥ +0.6325) | FAIL → NEGATIVE / IS-COLLAPSE |
| **A.2** | OOS Sharpe shift | ≥ -0.30 vs /060 (i.e., OOS ≥ -0.1597) | FAIL → NEGATIVE / OOS-NEGATIVE |
| **A.3** | frac_positive_paths | ≥ 0.50 | FAIL → methodology FAIL (CPCV degenerate) |
| **A.4** | No methodology FAIL | Critic 13 checks + §11 anti-pattern scan | FAIL → BLOCK |
| **B.5** | BCH IS share | one-sided ≥ 80% (per Critic /060 Rec #1) | FAIL → BCH collapse warning |
| **C.6** | IS trade count | ∈ [100, 250] | FAIL → trade-rate floor violation |
| **C.7** | OOS trade count | ∈ [60, 130] | FAIL → trade-rate floor violation |
| **D.8** | BCH IS wpnl Δ | within [-20, +10] vs /060 (+78.34 anchor; ORACLE -9.40 — allow modest IS dampening) | FAIL → BCH IS regression |
| **D.9** | BCH OOS wpnl Δ | within [-5, +5] vs /060 (+1.9078 anchor) | FAIL → BCH OOS regression |
| **D.10** | LDO IS wpnl Δ | within [-5, +20] vs /060 (-1.66 anchor; target lift) | FAIL → LDO IS regression |
| **D.11** | LDO OOS wpnl Δ | within [-5, +15] vs /060 (-19.7208 anchor; target LIFT per anti-Kelly correction) | FAIL → LDO OOS collapse |
| **D.12** | TRX IS wpnl Δ | within [-15, +15] vs /060 (-24.79 anchor) | FAIL → TRX IS regression |
| **D.13** | TRX OOS wpnl Δ | within [-10, +5] vs /060 (+23.3119 anchor; modest cost expected) | FAIL → TRX OOS regression |
| **D.14** | Saturation falsifier: per-symbol WR Δ | within ±2pp for ALL 3 symbols (IS+OOS) AND total trades Δ within ±5% | If ALL within band → INERT-AT-EXPLORATION (informational; not a FAIL — the weighting change had no behavioral impact) |
| **E.15** | All v3 risk_v2 + features_v3 tests passing | All `pytest tests/strategies/ml/test_per_symbol_vol_scale_floor.py tests/features_v3/ -v` PASS | FAIL → BLOCK |
| **E.16** | ensemble_summary | mode=exploration, size=3 | FAIL → mode-flag wiring bug |
| **E.17** | EDA-implementation parity | `risk_cfg.vol_scale_ceiling == 0.8` AND `DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0)` at runtime | FAIL → process violation |

**Notes on falsifier bands**:
- Gates A.1 (IS ≥ -0.20) and A.2 (OOS ≥ -0.30) are the LOCKED Section 8.4 disjunctive-OR NEGATIVE thresholds per `feedback_v3_cycle1_axis_pass_criteria.md`. Either single-gate FAIL → NEGATIVE classification.
- Gate D.11 targets LDO OOS LIFT (anti-Kelly correction mechanism); ORACLE predicts +2.66 wpnl Δ. The band [-5, +15] allows modest LDO OOS regression while requiring no catastrophic LDO OOS collapse beyond -5 wpnl.
- Gate D.14 is the BEHAVIORAL EFFECT SATURATION FALSIFIER per Critic /065 Rec #3 calibration for non-feature WEIGHTING axes. If saturation fires (all WR within ±2pp + total trades within ±5%), classification = INERT-AT-EXPLORATION (informational only, NOT a FAIL — INERT is a legitimate cycle 1 outcome per `feedback_v3_cycle1_axis_pass_criteria.md`).

### Section 4.5 — Anti-stacking check

Per `feedback_v3_engineered_features_dont_stack.md`: /066 changes ONE axis (RiskV2Config.vol_scale_ceiling). No engineered features added. No same-family features stacked. **iter-v3/065's DEFAULT_ATR_MULTIPLIERS=(2.0, 1.5) is REVERTED to (2.0, 1.0) at /066** to isolate the single varied axis. Single-axis EXPLORATION at single-seed mode is LEGITIMATE.

## Section 5 — Risk Mitigation

**UNCHANGED stack** (carry-forward from /060 anchor, EXCEPT for /066's single substantive change):

| Primitive | Status | Source |
|---|---|---|
| Vol scaling (RiskV2) - **CEILING CHANGED** | ENABLED, ceiling 1.0 → **0.8** universal | iter-v3/066 (this brief) Path E0.8 per EDA SHA 1d75cb0 |
| ADX threshold (global 20.0) | ENABLED | iter-v3/050 closeout (per-symbol cleared) |
| Hurst regime gate | DISABLED | iter-v3/022 (closed) |
| Feature z-score OOD (\|z\|>2.0) | ENABLED | iter-v3/011 |
| Low-vol filter | ENABLED | carry-forward |
| Hit-rate gate | DISABLED | OOS-only; not active |
| BTC trend kill (±15%, 14d) | ENABLED | iter-v3/051 reverted to no-block; threshold=15% |
| Per-symbol PnL cap (primitive 8) | DISABLED | iter-v3/020 PATH C closeout |
| Primitive 9 (regime-conditional kill) | DISABLED | iter-v3/023 (closed) |
| Primitive 10 (direction-asymmetric kill) | DISABLED | iter-v3/051 SYSTEM-LEVEL REVERT |
| Primitive 11 (per-symbol drawdown brake) | DISABLED | iter-v3/054 closeout (CLOSED-mechanism) |
| Per-symbol vol_scale_floor | ENABLED (iter-v3/061: TRX 0.5; BCH/LDO 0.3) | preserved at /066 (orthogonal axis from /066's ceiling change) |
| **Universal vol_scale_ceiling** | CHANGED (1.0 → 0.8) | **iter-v3/066 this brief** |

**Risk primitive axis is orthogonal to ALL other primitives at /066** (T1 inventory + T6 orthogonality verified). No primitive-cascade interaction risk.

## Section 6 — Risk Management

**CHANGED (single substantive change)**: `RiskV2Config.vol_scale_ceiling` 1.0 → 0.8. All 3 symbols (BCH/LDO/TRX) consume the new universal ceiling. No per-symbol override added.

`vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` from iter-v3/061 REMAINS UNCHANGED — orthogonal axis from /066's ceiling change.

DEFAULT_ATR_MULTIPLIERS REVERTS to (2.0, 1.0) per axis isolation discipline (Sub-fix 2).

Triple-barrier labeling timeout UNCHANGED: 21 candles (10080 minutes). Cooldown UNCHANGED: 4 candles post-trade. Fee UNCHANGED: 0.1% per leg.

**Translated to live trading**: live engine's effective `weight_factor` per trade is capped at 0.8 of base sizing (down from 1.0). Trades with `atr_pct_rank_200 ≥ 0.8` are sized at 0.8 instead of their raw atr_pct (which could be up to 1.0). Per-trade position sizing for high-vol regime trades reduces by up to 20%. Combined with `vol_scale_floor=0.3` (or 0.5 for TRX), the effective vol-scale band becomes [0.3, 0.8] universal / [0.5, 0.8] for TRX.

## Section 7 — Pre-registered Failure-Mode Prediction

Per Rule 3 of `feedback_v3_iter064_process_lessons.md`: single-axis non-feature changes at single-seed n_trials=35 weight NEGATIVE ≥25%. Calibrated per Critic /064 Rec #3 + /065 Rec #3.

| Mode | Description | Probability | Expected metrics |
|---|---|---:|---|
| **INERT** | Universal ceiling tightening produces shifts within ±band; trade-count + WR saturation falsifier fires (D.14); LightGBM compensates Optuna search around new weight bound | ~50% | IS Δ ∈ [-0.10, +0.10], OOS Δ ∈ [-0.20, +0.20]; D.14 saturation fires |
| **PROMISING** | LDO anti-Kelly correction outweighs TRX Kelly cost at multi-Optuna-trial level; Optuna second-order TPE re-converges favorably | ~15% | IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 |
| **SUSPICIOUS-OOS-DOMINANT** | Single-seed lottery: OOS spikes (LDO recovery + favorable BCH/TRX OOS roster shift) while IS stays flat or regresses | ~10% | IS Δ < +0.10, OOS Δ ≥ +0.20 |
| **NEGATIVE** | Universal ceiling overcuts BCH/TRX Kelly-aligned high-confidence wins; IS Sharpe shifts down; OOS may also regress under Optuna TPE divergence | ~25% | IS Δ < -0.20 OR OOS Δ < -0.30 |

Probabilities per orchestrator-mandated distribution:
- INERT ~50% (most likely; ORACLE Sharpe Δ within ±0.04 — predicted INERT)
- PROMISING ~15%
- SUSPICIOUS-OOS-DOMINANT ~10%
- NEGATIVE ~25% (Rule 3 calibration: single-axis at single-seed n_trials=35 has documented Optuna-overfit risk)

**Why INERT is most likely (50%)**: ORACLE first-order Sharpe Δ is +0.008 IS / +0.022 OOS — both BELOW the noise band magnitude of ±0.10 IS / ±0.20 OOS for 3-seed averaging. LightGBM at depth-3-5 with n_trials=35 will likely converge to similar Sharpe via different hyperparameter regions in response to weight-distribution shift. Mean reverter to /060 anchor in expectation.

**Why NEGATIVE is 25% (calibrated UP per Rule 3)**: Universal weight-distribution changes at single-seed are sensitive — iter-v3/041 (universal pruning) and iter-v3/042 (universal ATR) both produced NEGATIVE. The OPPOSITE direction here (ceiling tightening, not feature reduction) may also fail if Optuna TPE diverges from /060's hyperparameter neighborhood. BCH+TRX Kelly-aligned high-confidence trades getting dampened is a structural mechanism for NEGATIVE.

**Why PROMISING is only 15% (constrained UP-bound per Rule 3)**: per `feedback_v3_iter064_process_lessons.md` Rule 3 — PROMISING probability max 25% for single-axis EXPLORATIONs at single-seed n_trials=35. ORACLE prediction is positive but sub-band; PROMISING requires Optuna to discover signal beyond first-order ORACLE prediction.

## Section 8 — LOCKED Acceptance / Path Criteria

Per `feedback_v3_cycle1_axis_pass_criteria.md`:

### Section 8.1 — PROMISING-AT-EXPLORATION (advances to /069 CONFIRMATION as candidate)

ALL of:
- **A.1** IS Sharpe shift ≥ +0.10 vs /060 (IS ≥ +0.9325)
- **A.2** OOS Sharpe shift ≥ +0.20 vs /060 (OOS ≥ +0.3403)
- **A.3** frac_positive_paths ≥ 0.50
- **A.4** No methodology FAIL (Critic 13 checks + §11 anti-pattern scan)
- **B.5** BCH IS share ≥ 80% (one-sided per Critic /060 Rec #1)
- **C.6** IS trade count ∈ [100, 250]
- **C.7** OOS trade count ∈ [60, 130]
- **D.8-D.13** Per-symbol wpnl Δ bands all within range
- **E.15-E.17** Test pass + ensemble_summary + EDA-implementation parity gates PASS

### Section 8.2 — INERT-AT-EXPLORATION

- IS Δ within [-0.10, +0.10] OR OOS Δ within [-0.20, +0.20] (noise-band)
- AND no methodology FAIL
- AND/OR D.14 saturation falsifier fires (per-symbol WR Δ within ±2pp + total trades Δ within ±5%)
- Axis CLOSED for current cycle; not re-evaluated.

### Section 8.3 — SUSPICIOUS-OOS-DOMINANT

- IS Δ < +0.10 (i.e., INSIDE noise band or NEGATIVE)
- AND OOS Δ ≥ +0.20
- Axis CLOSED-PENDING-CONFIRMATION; does NOT advance to /069 as PROMISING but logged as parallel /069 advancement candidate.

### Section 8.4 — NEGATIVE (disjunctive OR per `feedback_v3_iter064_process_lessons.md` Rule 4)

- IS Δ < -0.20 **OR** OOS Δ < -0.30 (either gate FAIL)
- AND no methodology FAIL
- Axis CLOSED. Universal vol_scale_ceiling=0.8 placed on PARKED list with rationale.

### Section 8.5 — NEGATIVE-SUSPICIOUS-OOS-NEGATIVE (rare)

- IS Δ < -0.20 AND OOS Δ < -0.20
- Axis CLOSED. Strong evidence against universal ceiling tightening.

### Section 8.6 — Methodology FAIL

- Any Critic 13-check BLOCK fires
- Iteration is INVALID; not classifiable as PROMISING/INERT/NEGATIVE.

## Section 9 — Library Stack + Reproducibility

**UNCHANGED**:
- Python 3.13, uv environment, LightGBM (`lightgbm` package), pandas, pyarrow, statsmodels.
- ATR computation at `src/crypto_trade/features_v3/regime_v3.py:135` (`natr_21_raw` column; past-only Wilder 21-period; no change to formula).
- ATR percentile rank computation: `atr_pct_rank_200` is pre-computed in parquet (per `features_v3/__init__.py:89`); read by RiskV2Wrapper at inference.
- Vol-scale formula at `src/crypto_trade/strategies/ml/risk_v2.py:594-610`:
  ```python
  def _vol_scale(self, symbol: str, row: dict) -> float:
      atr_pct = row["atr_pct_rank_200"]
      if not np.isfinite(atr_pct):
          return 1.0
      floor = self.config.vol_scale_floor_per_symbol.get(symbol, self.config.vol_scale_floor)
      raw = float(atr_pct)
      return float(np.clip(raw, floor, self.config.vol_scale_ceiling))
  ```
  iter-v3/066 changes `self.config.vol_scale_ceiling` from default 1.0 to 0.8 (the explicit kwarg in RiskV2Config init). No code logic change in `_vol_scale` itself.
- ENSEMBLE_SEEDS[0:3] = (191664963, 1662057957, 1405681631) — outer=42 lineage subset for EXPLORATION mode.

**Reproducibility stamp**:
- EDA SHA: `1d75cb0` (`analysis/iteration_v3-066/risk_primitive_eda.py`)
- Setup commit SHA: (this commit, LOCKED)
- ITERATION_LABEL: `"v3-066"`
- RiskV2Config.vol_scale_ceiling at runtime: **0.8** (changed from 1.0)
- RiskV2Config.vol_scale_floor: 0.3 universal (unchanged)
- RiskV2Config.vol_scale_floor_per_symbol: {"TRXUSDT": 0.5} (unchanged from /061)
- DEFAULT_ATR_MULTIPLIERS at runtime: (2.0, 1.0) (REVERTED from /065's (2.0, 1.5))
- V3_ATR_MULTIPLIERS_PER_SYMBOL: {} (empty — preserved)
- Parquet data: `data/features_v3/{BCHUSDT,LDOUSDT,TRXUSDT}_8h_features.parquet` (no regen needed)

### Integration test (per `feedback_v3_methodology_axis_integration_test.md`)

The RiskV2Config.vol_scale_ceiling edit is consumed by:
1. `run_baseline_v3.py::_build_v3_model` — `RiskV2Config(vol_scale_ceiling=0.8, ...)` per Sub-fix 1
2. `run_baseline_v3.py::_verify_*` runtime assertion — `vol_scale_ceiling == 0.8` per Sub-fix 6
3. `src/crypto_trade/strategies/ml/risk_v2.py::_vol_scale` (line 610) — `np.clip(raw, floor, self.config.vol_scale_ceiling)`
4. `tests/strategies/ml/test_per_symbol_vol_scale_floor.py` (existing) — already parameterized over `vol_scale_ceiling`; runs PASS with 0.8

A smoke test consists of running:
```bash
uv run pytest tests/strategies/ml/test_per_symbol_vol_scale_floor.py tests/features_v3/ -v
```
and confirming all tests PASS with the new (2.0, 1.0) `DEFAULT_ATR_MULTIPLIERS` + the runtime `vol_scale_ceiling=0.8` configuration.

## Section 10 — QR Audit Trail

**Why this axis (UNIVERSAL vol_scale_ceiling tightening, Path E0.8)**:

1. **Critic /064 Rec #4 binding directive** (locked for /065-/068): NON-FEATURE axis pivot mandated after /060 14-feature anchor classified as LOCAL OPTIMUM at single-seed n_trials=35 (per Rule 5 of `feedback_v3_iter064_process_lessons.md`). Feature-axis EXPLORATIONs at this budget cannot productively escape.

2. **Orchestrator autopilot decision 2026-05-14**: cycle 1 #7 axis CATEGORY locked at RISK PRIMITIVE for /069 CONFIRMATION bundle structural diversity. /065's labeling axis was the first PROMISING-class survivor; a non-labeling PROMISING-class component would strengthen the /069 bundle by reducing single-axis dependence. Risk primitive is mechanistically orthogonal to labeling at the implementation level (T6 verified).

3. **QR EDA SHA `1d75cb0`** produced 7 tables that quantitatively support Path E0.8 over Paths A/B/C/D:
   - **T0**: anchor-value declaration (per Critic /064 Rec #1 + /065 Rec #1 RECURRENCE flag).
   - **T1**: current 7-primitive risk gate inventory documenting universal weight-modifier slots; vol_scale_ceiling=1.0 (universal) had NEVER been tested.
   - **T2**: /060 weight_factor distribution per (split, symbol) showing LDO OOS anti-Kelly concentration (6 of 11 trades at wf≥0.8 contributing to -19.72 OOS wpnl).
   - **T3**: per-Path counterfactual wpnl Δ across IS+OOS+per-symbol — Path E0.8 LDO OOS Δ +2.66 wpnl (anti-Kelly correction); NET OOS portfolio Δ +0.29.
   - **T4**: per-Path ORACLE monthly Sharpe Δ HEADLINE — Path E0.8 IS Δ +0.0084, OOS Δ +0.0221 (only sign-aligned positive).
   - **T5**: Path selection summary scoring 7 candidates with quantitative + methodology gates.
   - **T6**: cross-axis orthogonality with /065 labeling axis — 6/7 checks ISOLATED at first order.

4. **Path E0.8 selection rationale (quantitative)**:
   - Only Path with sign-aligned POSITIVE ORACLE ΔSharpe (IS +0.008, OOS +0.022)
   - LDO OOS anti-Kelly correction: ORACLE +2.66 wpnl Δ from capping 6 high-wf losers
   - BCH OOS limited damage (-0.87 wpnl)
   - TRX OOS modest Kelly cost (-1.51 wpnl); accepted under universal change discipline
   - NET portfolio OOS Δ = +0.28 wpnl
   - Single-axis change (RiskV2Config.vol_scale_ceiling: 1.0 → 0.8)
   - Universal (preserves IS aggregate per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`)
   - STATELESS (ORACLE EDA valid per `feedback_v3_oracle_eda_validity.md`)
   - Mechanistically ORTHOGONAL to /065 labeling axis (T6 verified)
   - Anti-snooping: universal `vol_scale_ceiling=0.8` has NEVER been tested

5. **Methodology compliance**:
   - `feedback_v3_axis_selection_quant_discipline.md`: EDA committed BEFORE brief (SHA `1d75cb0` precedes setup commit).
   - `feedback_v3_oracle_eda_validity.md`: ORACLE valid for STATELESS primitive (vol_scale_ceiling); Path D (stateful) excluded.
   - `feedback_v3_engineered_features_dont_stack.md`: single-axis EXPLORATION (ONE substantive change — vol_scale_ceiling); Paths A and C (2-axis) excluded.
   - `feedback_v3_per_symbol_lifts_oos_breaks_is.md`: UNIVERSAL change (no new per-symbol override).
   - `feedback_v3_cycle1_axis_pass_criteria.md`: PASS thresholds (IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 vs /060) explicit at Section 8.1.
   - `feedback_v3_iter064_process_lessons.md` Rule 1 (anchor-value correctness gate; RECURRENCE flag /065): T0 references /060 anchor values with bit-exact `comparison.csv:LINE` refs.
   - `feedback_v3_iter064_process_lessons.md` Rule 3 (probability calibration): Section 7 NEGATIVE=25%, INERT=50%, PROMISING=15%, SUSPICIOUS-OOS=10%.
   - `feedback_v3_iter064_process_lessons.md` Rule 4 (Section 8 disjunctive OR): Section 8.4 NEGATIVE LOCKED as disjunctive OR.
   - `feedback_v3_axis_saturation_predictor.md`: Section 4.3 behavioral-effect predictor present with quantitative trade-count + per-symbol WR Δ bands; Gate D.14 saturation falsifier.
   - `feedback_v3_dsr_mode_artifact.md`: DSR_relative INFORMATIONAL ONLY at /066 EXPLORATION mode.

6. **EDA-implementation parity (per Critic /063 Rec #2)**: V3_FEATURE_COLUMNS_TOP_N UNCHANGED (14 features); DEFAULT_ATR_MULTIPLIERS reverted to (2.0, 1.0); RiskV2Config.vol_scale_ceiling=0.8 is the ONE change. Phase 5.5 gate asserts BOTH conditions at runtime per Sub-fix 5+6.

7. **Cross-axis orthogonality with iter-v3/065** (T6 verification):
   - /065 axis: TRAIN-TIME label generation (atr_tp_multiplier, atr_sl_multiplier)
   - /066 axis: INFERENCE-TIME weight modifier (vol_scale_ceiling)
   - Separate modules: `labeling.py` vs `risk_v2.py`
   - Separate Signal fields: `tp_pct/sl_pct` vs `weight`
   - At /066: /065's DEFAULT_ATR_MULTIPLIERS=(2.0, 1.5) REVERTED to (2.0, 1.0) — /065 axis tested separately
   - At /069 CONFIRMATION: /065 + /066 (if PROMISING) bundled at multi-seed — second-order Optuna coupling captured

8. **Cannot be retroactively renegotiated**. Established at brief LOCK (setup commit).

---

**Setup commit SHA**: (this commit, LOCKED)

**Reading order for Engineer (Phase 6)**:
1. Verify branch `iteration-v3/066`; pull SHA `1d75cb0` (EDA).
2. Apply Sub-fixes 1-6: 
   - `RiskV2Config(vol_scale_ceiling=0.8, ...)` in `_build_v3_model` (run_baseline_v3.py)
   - `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)` in `src/crypto_trade/features_v3/__init__.py` (REVERT /065)
   - `ITERATION_LABEL = "v3-066"`
   - test assertion updates `(2.0, 1.5)` → `(2.0, 1.0)`
   - runner runtime assertion update for `DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0)`
   - new runtime assertion `vol_scale_ceiling == 0.8`
3. Run `uv run pytest tests/strategies/ml/test_per_symbol_vol_scale_floor.py tests/features_v3/ -v` to confirm test PASS.
4. Run `uv run python run_baseline_v3.py --clean-oof --exploration --n-trials 35` (Phase 6 backtest).
5. Wall-clock target ~1.1h; HARD CAP 2h per `feedback_v3_cadence_discipline.md`.
6. Engineering report covers Section 8 LOCKED criteria evaluation (PASS/FAIL on each gate A.1–E.17) for Critic Phase 7.5.
