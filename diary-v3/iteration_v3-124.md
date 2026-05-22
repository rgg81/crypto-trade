# iter-v3/124 — Cycle-7 slot 3 — EXPLORATION-NEGATIVE-catastrophic / labeling-DURATION axis CLOSED bilaterally

**Date**: 2026-05-20
**Type**: EXPLORATION (cycle-7 slot 3 of 10; single-axis coupled: `label_timeout_minutes` 10080 → 30240 (K=21 → K=63) + Branch B `atr_tp_multiplier` 2.0 → 3.4641 + `atr_sl_multiplier` 1.0 → 1.7321 at sqrt(K) random-walk variance preservation; runner-local `REQUIRED_GAP` 66 → 192)
**Axis**: NON-FEATURE TRAIN-TIME labeling DURATION axis (axis-3 in cycle-7 menu); first revisit since /068 NEGATIVE-catastrophic at K=42 retained-ATR
**Verdict**: EXPLORATION-NEGATIVE-catastrophic per Critic FINAL `b222749`
**Classification**: NEGATIVE-catastrophic — IS Sharpe Δ −0.870 vs /121 multi-seed baseline AND OOS Sharpe Δ −0.943 (BOTH legs > 2× the −0.40 catastrophic threshold; first-match-wins selects criterion 1 NEGATIVE-catastrophic deterministically)
**BASELINE_V3.md**: UNCHANGED (/121 canonical at `v0.v3-121`)

## 1. What was done

QR-led EDA at `e814bb2` adjudicated Branch B (sqrt(K) ATR scaling) over Branch A (retained K=21 ATR) per T4 random-walk variance derivation: at K=63 with retained +2.0/-1.0 ATR, the barriers compress to 0.25σ in K=63 σ-units (vs the K=21 baseline 0.44σ) — LABEL SEMANTIC SHIFT toward early-barrier-hit random-walk crossings. Branch B preserves K=21 σ-unit barrier height (0.44σ in both K=21 and K=63 σ-units) by scaling barriers proportionally to sqrt(3) ≈ 1.7321.

EDA T2 pre-flagged F2 BINDING falsifier TRIGGERED at pre-flight: LDO AFML effective sample size loss +67.74% vs K=21 (137 → 44 effective samples per WF month). BCH +67.77% (301 → 97); TRX +67.74% (283 → 91). Per task spec, F2 BINDING but proceeded with brief Section 6 explicit address of HIGH-RISK posture.

Commit chain: EDA `e814bb2` → brief `393c5d4` → phase 5.5 gate `19cff59` → setup `0efcd2d` (label_timeout_minutes 10080→30240; DEFAULT_ATR_MULTIPLIERS (2.0,1.0)→(3.4641,1.7321); REQUIRED_GAP runner-local override 66→192) → 3 pre-flight fix commits (`42a2780`, `be785d5`, `0cded02` — ATR-assertion update, config-accretion alignment, feature-count fix removing stale /123 residue) → engineering `35d2305` → Critic FINAL `b222749`. Wall-clock not logged in artefacts (run.log absent — see Section 7.2 process note).

Files changed: `run_baseline_v3.py` (ITERATION_LABEL "v3-124"; BacktestConfig.timeout_minutes + common_kwargs label_timeout_minutes 10080→30240; `_verify_model_config` + `_verify_timeout_consistency` hardcoded assertions updated; runner-local REQUIRED_GAP override 192); `src/crypto_trade/features_v3/__init__.py` (DEFAULT_ATR_MULTIPLIERS (2.0,1.0)→(3.4641,1.7321); V3_FEATURE_COLUMNS_TOP_N reverted 15→14 per /123 closure); `tests/strategies/ml/test_label_timeout_minutes.py` + `tests/strategies/ml/test_cpcv_embargo_assert.py` (assertions updated for K=63 / per_cell_embargo=64 / REQUIRED_GAP=192).

No feature changes, risk-gate changes, ensemble changes, walk-forward changes, or universe changes. /116 no_confirm STAYS ENABLED; /119 C6 STAYS BANNED; /122 eth_ret_3d + /123 eth_vs_sym_rv_50 STAY REMOVED.

## 2. Results

| Metric | /121 BASELINE (multi-seed) | /124 (3-seed EXPLORATION) | Δ vs /121 |
|---|---:|---:|---:|
| IS monthly Sharpe | +1.3108 | **+0.4412** | **−0.8696** |
| OOS monthly Sharpe | +0.9682 | **+0.0254** | **−0.9428** |
| IS MaxDD | 26.38% | 41.01% | +14.63pp |
| OOS MaxDD | 25.70% | 41.93% | +16.23pp |
| IS trades | 173 | 180 | +7 |
| OOS trades | 98 | 85 | −13 |
| OOS/IS Sharpe ratio | 0.7386 | **0.0575** | −0.681 |
| PSR | 1.0 | **0.6068** | **−0.39** (the corroborating signal that the /121 lift is genuinely lost at K=63, not just architecture-mode compressed) |
| PBO | 0.1278 | 0.0649 | −0.063 (PASS by gate but informational) |
| frac_positive_paths | 0.6444 | 0.6444 | 0.000 |

Per-symbol IS attribution (from `in_sample/per_symbol.csv`):
- BCHUSDT: 77 IS trades, 37.7% WR, net_pnl_pct **−47.67%** (Δ vs /121: collapsed; was strong contributor)
- LDOUSDT: 19 IS trades, 36.8% WR, net_pnl_pct +31.90% (but weighted_pnl = −16.34 — low-confidence trades over-weighted by Optuna; the per_symbol.csv `pct_of_total_pnl` = −147.87% is a structural artifact of weighted_pnl sign-inversion)
- TRXUSDT: 84 IS trades, 35.7% WR, net_pnl_pct **−5.81%** (drag; was small positive contributor at /121)

Per-symbol OOS attribution (from `out_of_sample/per_symbol.csv`):
- BCHUSDT: 27 OOS trades, 33.3% WR, net_pnl_pct **+10.19%**
- TRXUSDT: 43 OOS trades, 39.5% WR, net_pnl_pct **+9.62%**
- LDOUSDT: 15 OOS trades, 20.0% WR, net_pnl_pct **−24.09%** (dominant OOS loss carrier; per_symbol concentration_pct = −1446% artifact of OOS aggregate weighted_pnl ≈ +1.13 near-zero denominator)

F5 universe-cascade NOT triggered at 3-of-3 IS-negative-weighted_pnl threshold (BCH IS wpnl = +13.83 positive); HOWEVER 2-of-3 IS net_pnl_pct negative (BCH −47.67% + TRX −5.81%). The Critic engineering report Section 11 classifies this as "broad-based-IS-collapse" mechanism distinguishable from a single-symbol carrier failure.

## 3. Mechanism: AFML sample-uniqueness loss dominates Branch B's barrier semantic preservation

The K=63 axis replicates the /068 K=42 failure mechanism at a LARGER scale, with Branch B's MAGNITUDE scaling providing NO rescue. Root cause:

**AFML sample-uniqueness loss at +67%** (per EDA T3 + T2): K=63 reduces effective IS training labels by 67% per symbol (LDO 137→44, BCH 301→97, TRX 283→91). At n_trials=35 Optuna sees a drastically smaller and more correlated label space — each walk-forward month's training window contains far fewer independent signals.

**Optuna overfits the compressed IS label set**: BCH IS net_pnl_pct collapses to −47.67% with WR 37.7% on 77 IS trades; OOS BCH ekes out +10.19% on only 27 trades — the IS/OOS trade ratio (77/27 = 2.85) and IS/OOS PnL sign-flip signal that the IS Optuna trajectory learned label-specific patterns NOT present in OOS.

**Branch B's sqrt(3) ATR scaling preserved per-step barrier semantics but couldn't replenish sample count**: IS timeout rate of 4.4% (vs K=21's 9.2%) confirms wider barriers suppressed timeouts as designed — the LABEL SEMANTIC CHARACTER is preserved per-label. F4 narrowly TRIGGERED at 4.4% < 5% pre-flight lower bound (0.6pp miss; informational, not classification-driver). Preserving per-label semantics does NOT compensate for too-few independent labels: trees at depth 3-5 require independent training signal density that K=63 destroys at the AFML uniqueness layer.

**The /065 MAGNITUDE-coupling residual risk MATERIALIZED as predicted**: Branch B inherited the /065 SL-widening risk (1.0 → 1.73 = +73%, larger than /065's +50%). The mechanism that broke /065 at multi-seed CONFIRMATION (longer-hold of adverse trades — IS Sharpe collapse −0.97) reappears here at single-seed EXPLORATION — Branch B's proportional barrier scaling did NOT mitigate (the magnitude leg dominates at K=63).

## 4. The labeling-DURATION axis CLOSED bilaterally — two K extensions, two failure modes, one root cause

The labeling-DURATION axis is now CLOSED bilaterally on TWO independent EXPLORATION attempts spanning two ATR-scaling regimes:

| Iter | K (timeout candles) | ATR scaling | REQUIRED_GAP | Anchor | IS Δ | OOS Δ | Verdict |
|---|---:|---|---:|---|---:|---:|---|
| /068 | K=42 | Retained (+2.0, −1.0) | 129 | /060 (IS +0.8236 / OOS +0.2078 current-code) | **−0.35** | **−0.48** | NEGATIVE-catastrophic |
| **/124** | **K=63** | Branch B (sqrt(3) scaled: +3.4641, −1.7321) | **192** | /121 (IS +1.3108 / OOS +0.9682) | **−0.870** | **−0.943** | **NEGATIVE-catastrophic** |

**Two failure modes, one root cause**: /068 at K=42 retained ATR (label SEMANTIC SHIFT: same +1/−1 labels at K=21 vs K=42 encode different real-world events because barrier σ-units compress) — IS Δ −0.35 / OOS Δ −0.48. /124 at K=63 Branch B sqrt(K) ATR (label SEMANTIC PRESERVATION: barriers scaled to preserve K=21 σ-units in K=63 σ-units) — IS Δ −0.870 / OOS Δ −0.943, materially WORSE despite the cleaner design.

The root cause that BOTH share: **AFML sample-uniqueness loss is the dominant pathway to catastrophe, not barrier semantics**. /068 at K=42 saw +51% effective sample loss; /124 at K=63 sees +67% effective sample loss. Both compress Optuna's effective training-label diversity, both produce IS-overfit + OOS-collapse. Branch B's sqrt(K) ATR design controls for the second-order LABEL SEMANTIC SHIFT risk — and confirms that even when controlled, the first-order AFML uniqueness loss is structural.

**The axis is bilaterally CLOSED** — at any K > K=21 in the BCH/LDO/TRX 8h universe with /121's 14-feature stack and n_trials=35 Optuna budget, the AFML uniqueness loss penalty dominates whatever signal extension a longer horizon could reveal. K=84 (a third sub-option in the brief) would only intensify the penalty at +75% sample loss (per EDA T3) and is forbidden a priori without a STRUCTURALLY DIFFERENT design that addresses the uniqueness loss mechanism (e.g., expanded training universe to recover sample density, sparse-label-aware ensemble, or fundamental re-architecture of the label generation pipeline). Cycle 7 cannot retry this axis.

## 5. Critic verdict summary

OVERALL = **EXPLORATION-NEGATIVE-catastrophic**. Zero clarifications raised (catastrophic verdict unambiguous via first-match-wins). 7 of 8 checks PASS + 1 N/A:

- **Check 1 (look-ahead)**: PASS. K=63 horizon is TRAIN-TIME labeling parameter; walk-forward post-fix at `walk_forward.py:113` intact (`train_end_ms = test_start_ms − embargo_ms`; embargo_ms = 64 × 480 × 60_000 ≈ 21.3 days). Branch B ATR multipliers applied at label-generation time using past-only natr_21. Trade arithmetic spot-check clean.
- **Check 2 (embargo)**: PASS. REQUIRED_GAP = 192 = (63+1)×3 (runner-local override per /068 precedent; validation_v3.py constant stays at 66). Per-cell embargo 64 candles (21.3 days). Symmetric application verified.
- **Check 3 (multiple-testing)**: SPLIT (informational for EXPLORATION). DSR=0.0 informational, PSR=0.6068 (below 0.95), PBO=0.0649 PASS, frac_positive_paths=0.644 PASS. **The PSR collapse /121 1.0 → /124 0.6068 is itself a clean corroborating negative signal**: the /121 lift is GENUINELY LOST at K=63, not just architecture-mode compressed.
- **Check 4 (IC)**: PASS by carry-forward. No new features; V3_FEATURE_COLUMNS_TOP_N reverted 15 → 14. Engineered-feature carve-out intact.
- **Check 5 (ADF)**: PASS by carry-forward. 14-feature stack identical to /121.
- **Check 6 (Pareto)**: N/A (single-seed 3-seed-lineage EXPLORATION).
- **Check 7 (reproducibility)**: PASS. ITERATION_LABEL=v3-124 verified; explicit `feature_columns`; pre-flight assertions PASS; `_verify_timeout_consistency` asserts BacktestConfig.timeout_minutes == LightGbmStrategy.label_timeout_minutes == 30240.
- **Check 8 (alignment)**: PASS. Brief Section 3.5 changes implemented exactly; single-axis discipline holds (coupled DURATION+MAGNITUDE is methodologically ONE axis per random-walk variance derivation).

## 6. PATH classification

**NEGATIVE-catastrophic** per Section 8 first-match. IS Sharpe Δ −0.870 (> 2× the −0.40 catastrophic-IS-collapse threshold) AND OOS Sharpe Δ −0.943 (> 2× the −0.40 catastrophic-OOS-collapse threshold) — BOTH legs trigger NEGATIVE-catastrophic with large margin. F1 and F6 both TRIGGERED. F4 narrowly TRIGGERED (4.4% IS timeout rate vs [5%, 20%] band lower bound; informational; does not change classification). F2 was pre-registered as TRIGGERED at EDA pre-flight; production confirmed the catastrophic outcome. F3 NOT TRIGGERED (OOS MaxDD held below the doubling threshold at 41.93% vs threshold 51.40%). F5 NOT TRIGGERED at the strict 3-of-3 IS-wpnl-negative gate (BCH IS wpnl positive); however 2-of-3 IS net_pnl_pct negative is the structural "broad-based-IS-collapse" mechanism class identified at /123.

The K=63 axis at Branch B does NOT promote any PROMISING-class subtype — the OOS collapse to +0.0254 is genuine (not the /122 single-seed loss-surface artifact that masqueraded as PROMISING-OOS-lift, nor the /123 regime-classifier artifact). PSR drops from /121's 1.0 to /124's 0.6068 — corroborating the catastrophic verdict.

## 7. Hypothesis check and process notes

### 7.1 Hypothesis falsified

Brief Section 1 hypothesis: "Extending the labeling horizon K=21 → K=63 (3× forward scan) with PROPORTIONAL ATR barrier scaling at sqrt(K) carries incremental directional signal beyond the /121 baseline by allowing the model to learn predictors of MEDIUM-TERM directional moves." **FALSIFIED.** The K=63 horizon extension under preserved label semantics does NOT reveal incremental signal — the AFML sample-uniqueness loss dominates Optuna's ability to extract any incremental signal benefit from the longer horizon.

The K=63 Branch B widened-envelope prediction (IS Δ [−0.50, +0.50] per /068 widening mandate; OOS Δ [−0.50, +0.50]) was BREACHED on the lower bound on both legs: IS observed −0.870 (1.74× the lower bound), OOS observed −0.943 (1.89× the lower bound). Future labeling-DURATION axes (if any in a different universe/architecture) should pre-register an even wider envelope of IS Δ [−1.50, +0.50] / OOS Δ [−1.50, +0.50] given the /068 + /124 evidence base.

### 7.2 Process note — run.log missing

Engineering report Section "Headers" notes `Wall-clock time: not logged (run.log absent; report written from output artefacts)`. The run.log missing is anomalous (prior iterations have it); engineering proceeded from `comparison.csv` + `dsr.json` + `ensemble_summary.json` + `in_sample/`+`out_of_sample/` trade-level artefacts which were complete. No methodology impact. Memory note for future iterations: confirm `run.log` is written at backtest start before clean-up.

## 8. BASELINE_V3.md status

UNCHANGED — /121 stays canonical at `v0.v3-121` (IS +1.3108 / OOS +0.9682). Per `feedback_v3_strict_both_is_oos_baseline.md`, BASELINE_V3.md updates ONLY when CONFIRMATION beats prior baseline on BOTH IS Sharpe AND OOS Sharpe (multi-seed mean). /124 is EXPLORATION-class (not CONFIRMATION) AND was NEGATIVE-catastrophic on both legs — no baseline update is even logically eligible.

## 9. Next-iteration ideas — cycle-7 axis menu state + /125 axis recommendation

### 9.1 Cycle-7 axis menu state after /124

| Axis | State | Reason |
|---|---|---|
| 1 — Cross-asset OHLCV | **CLOSED** | 6 consecutive failures (/082 + /085 + /086 + /119 C6 + /122 + /123) per `feedback_v3_cross_asset_ohlcv_closed.md` |
| 2 — Non-LightGBM model classes | LOCKED OUT (per cycle-5 finding) | /109 saturated representational-capacity axis at 8h; non-LightGBM model architectures at /016 (XGBoost) + /088-091 (LGBMRanker cross-sectional) all failed |
| 3 — Longer-cadence labels (labeling-DURATION) | **CLOSED BILATERALLY** (this iteration) | /068 NEGATIVE-catastrophic at K=42 retained ATR + /124 NEGATIVE-catastrophic at K=63 Branch B sqrt(K) ATR — AFML sample-uniqueness loss is dominant pathway regardless of barrier semantics |
| 4 — NEW symbol universe variants | LOCKED OUT (per cycle-1-6 results) | HBAR+AVAX /021 NEG; FIL /083 NEG; GALA+MANA+SAND /087 NEG; ADA /069 NEG; CRV+AAVE+GRT+ADA /110-111 NEG; ADA-replace-LDO /078 SUSPICIOUS-OOS-DOMINANT (universe-swap factor-loading via added-symbol roster) — universe expansion broadly closed |
| 5 — Creative out-of-box (per-symbol drawdown brake at closed-loop simulator layer) | **OPEN** (CRITIC PRIORITY 1 for /125) | Recommended by /123 Critic Rec 3 + /124 Critic Rec 1; requires deadlock-impossibility proof per `feedback_v3_oracle_eda_validity.md` |
| 6 — NEW engineered features at strict pairwise-IC gate (< 0.40) | OPEN (CRITIC PRIORITY 2) | Limited to FUNDING/OI/MICROSTRUCTURE/CROSS-ASSET-NON-OHLCV families (cross-asset OHLCV CLOSED). EDA pre-registers |IC| < 0.40 falsifier against all 14 existing features |
| 7 — RiskV2 untested gate configurations | OPEN (CRITIC PRIORITY 3) | Specific untested gate-threshold combos (vol_scale_floor_per_symbol changes; per-symbol ADX overrides at LDO-only) |

### 9.2 Severely constrained axis menu — 5 remaining slots after /124

Cycle-7 has 7 remaining slots (/125-/131) before /132 CONFIRMATION. With axes 1+2+3+4 closed/locked-out, the remaining axis menu is THIN:
- Axis 5 (creative out-of-box): the BEST candidate for the highest-priority slot — addresses a structural drag (BCH 95.76% top-symbol share at /121) with auditable closed-loop discipline
- Axis 6 (NEW engineered features at strict IC gate): high-risk per /122/123 RECURRENCE pattern (off-the-shelf features at IC-spanning by incumbents); requires conditional orthogonality + per-symbol broad-based-IS-positive-Δ EDA discipline
- Axis 7 (RiskV2 gate configurations): lowest priority because knob-tuning is closed for ADX, z-score, BTC band — only untested combinations remain

If all 5+6+7 are exhausted in /125-/131 with NEGATIVE outcomes, cycle 7 closes with a thin axis menu and the cycle-7 CONFIRMATION /132 will be a baseline RE-VALIDATION of /121 (analogous to /081 for cycle 2 and /092 for cycle 3 — multi-seed re-validation of the canonical config with NO new ingredient to bundle). The structural finding would then mirror cycles 2+3+6's pattern: the BCH/LDO/TRX 8h universe with /121's 14-feature stack and LightGBM at depth 3-5 is saturated against conventional axis families.

### 9.3 Recommended /125 axis — Critic Priority 1: per-symbol drawdown brake at closed-loop simulator layer

Per /124 Critic Rec 1 + /123 Critic Rec 3 + `feedback_v3_oracle_eda_validity.md`:

**Spec**: per-symbol drawdown brake — when a symbol's per-symbol cumulative weighted_pnl drawdown from running peak exceeds threshold X% (calibration sub-axis), throttle position scaling for that symbol to floor F (typically 0.33-0.50) until cumulative weighted_pnl recovers within hysteresis band Y% above brake-trigger. Universe-cascade kill-switch fallback if all 3 symbols brake simultaneously (deadlock prevention).

**Mandatory EDA gates per `feedback_v3_oracle_eda_validity.md`**:
1. Closed-loop simulator showing brake transitions ON/OFF correctly through ≥2 hysteresis cycles in IS data
2. Brief Section 2 explicit deadlock-impossibility proof: at any state (symbol_brake_state ∈ {ON, OFF} per symbol; portfolio_kill_switch ∈ {ON, OFF}), the next bar's decision algorithm cannot enter a state where ALL THREE symbols are brake-ON AND portfolio is kill-switch-ON with no path back to OFF. (The /054 brake entered permanent deadlock because BCH+LDO brake-ON at OOS-start → no trades → no state update → frozen.)
3. Pre-register hysteresis-cycle count and brake-trigger frequency from closed-loop simulation; falsifier-triggered if production hysteresis cycle count deviates > 2× from simulator prediction

**Rationale for highest priority**:
1. /124 Critic Rec 1 + /123 Critic Rec 3 both elevate this to highest priority
2. Symbol-level concentration is a structural drag since /121 (BCH 95.76% top-symbol share — well above the 30% cycle-7 outstanding constraint)
3. Closed-loop discipline is auditable and not knob-tuning (per `feedback_v3_structural_over_knob_exploration.md`)
4. Differs structurally from /020's NEGATIVE-clean PATH C per-symbol PnL share cap (proportional scaling, deterministic at trade-level Optuna re-tuning to compensate) — drawdown brake is BINARY ON/OFF on STATEFUL persistent state, qualifies under `feedback_v3_concentration_is_signal.md` permitted "per-symbol drawdown brake (loss-stop semantics)" orthogonal mechanism

**Alternative if creative out-of-box not viable**: defer to Critic Priority 2 (NEW engineered features at strict pairwise-IC gate) with restriction to non-OHLCV-cross-asset feature families (funding/OI/microstructure with conditional orthogonality + broad-based IS-Δ EDA discipline).

---

**Catalog entry appended** to `briefs-v3/exploration_catalog.md`:

```
| iter-v3/124 | 2026-05-20 | cycle-7 axis-3 longer-cadence labels K=63 + Branch B sqrt(3) ATR | -0.8696 | -0.9428 | EXPLORATION-NEGATIVE-catastrophic | NO |
```

**Tag**: `v0.v3-124`. Does NOT supersede `v0.v3-121` as canonical.

**Memory updates**: APPEND cycle-7 slot 3 catastrophic outcome + axis exhaustion summary to `project_v3_cycle7_setup.md`; UPDATE `feedback_v3_promising_feature_mechanical.md` cross-references (no new feedback file — the labeling-DURATION axis closure is structurally captured by appending to `project_v3_cycle7_setup.md` since the closure is scope-bounded to cycle-7 axis-3 in the current universe/architecture, and the cross-iteration K-extension closure rationale is anchored at this diary Section 4).
