# iter-v3/085 — Research Brief — NEW funding-regime-conditioned ENGINEERED feature (cycle-3 EXPLORATION #4)

**Iteration**: iter-v3/085 — cycle 3 EXPLORATION #4 of 10
**Branch**: `iteration-v3/085` (off the /084 closeout merge `54ad544`)
**Author**: QR (autopilot)
**Date**: 2026-05-16

---

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` — UNCHANGED, IMMUTABLE. Verified in `src/crypto_trade/config.py`.
- `training_months = 24` — UNCHANGED, IMMUTABLE.
- **IS window**: earliest available 8h data per symbol → 2025-03-24. BCH/TRX span ≈ 62 months of IS history; LDO ≈ 30 months (the youngest symbol — see Section 2 T-LDO).
- **OOS window**: 2025-03-24 → present (current data extent ≈ 2026-05-16).
- The walk-forward / CPCV backtest runs continuously over IS+OOS; the reporting layer splits at `OOS_CUTOFF_DATE`. The QR sees OOS only in Phase 7. No `start_time` trim, no date-range cherry-pick.

## Section 0.5 — Iteration Type Declaration

**TYPE: EXPLORATION.** Single-axis variation: ONE new Category-2 composed feature appended to `V3_FEATURE_COLUMNS_TOP_N` (count 14 → 15). EXPLORATION-mode 3-seed (`--exploration` → `EXPLORATION_ENSEMBLE_SIZE = 3`, seed slice `ENSEMBLE_SEEDS[0:3]`), `--n-trials 35`. Wall-clock budget HARD CAP **2h** (estimate ≈ 0.7h — Section 3.6). This is an EXPLORATION, not a CONFIRMATION: the cycle-3 plan reserves CONFIRMATION for iter-v3/092; /085 is EXPLORATION #4 of the strict 10:1 cadence.

## Section 1 — Hypothesis

A composed feature `funding_regime_momentum_5d = regime_momentum_signed_5d × sign(funding_z_30)` — momentum sign-switched by the prevailing funding-crowding regime — gives the per-symbol LightGBM a funding×momentum interaction it cannot compose at depth 4, improving IS edge: momentum into a crowded long is exhaustion (fade), momentum into a crowded short is a squeeze setup (follow), and raw momentum cannot encode that conditioning.

## Section 2 — IS-Only Numerical Evidence

All tables from the committed EDA scripts in `analysis/iteration_v3-085/` (EDA SHA recorded in Section 10). **Every script reads IS data only** (`open_time < OOS_CUTOFF_MS`); OOS is never loaded. Triple-barrier labels use the production labeler `label_trades` with `(2.0, 1.0)` ATR multipliers + 21-candle (10080-min) timeout — the /059-canonical labeling.

### 2.0 — Why the axis is NOT a multi-symbol-pooled model (the orchestrator's lead candidate, EDA-FALSIFIED)

The /084 closeout and the orchestrator's dispatch steered Direction 3 — a multi-symbol-pooled model. Per `feedback_v3_axis_selection_quant_discipline.md` the QR makes the axis call with committed EDA. iter-v3/085 ran **three** IS-only EDA probes against the pooled model and **all three falsified it**:

| EDA probe | Script | Result | Verdict |
|---|---|---|---|
| Naive pool — leave-one-symbol-out transfer | `pooled_model_cross_symbol_structure.py` | mean cross-symbol transfer lift **−0.0188** (worse than majority-class base rate); 1/3 symbols positive; only **7/14** features sign-agree on feature→label IC across symbols | NOT SUPPORTED |
| Pooled + `symbol_id` categorical dummy | `pooled_with_symbol_dummy.py` | pooled+dummy **−0.0124** vs per-symbol baseline; **breaks BCH** (acc 0.5216 → 0.4802, Δ −0.0414); `symbol_id` importance only 3.39% — the depth-4 tree barely conditions on symbol | NOT SUPPORTED |
| LDO-only donor augmentation (selective pool) | `ldo_donor_augmentation.py` | best donor config (incl. 0.3-weight down-weighting) **−0.0013 BELOW** LDO's per-symbol baseline | NOT SUPPORTED |

The mechanism: BCH carries ≈96% of v3 IS PnL (BASELINE_V3.md per-symbol attribution), and its feature→label map is symbol-specific. A pooled model averages BCH's edge against TRX's *opposite-signed* feature relationships — a pool that breaks BCH collapses the headline IS Sharpe (the `feedback_v3_strict_both_is_oos_baseline.md` BOTH-must-improve failure). The runner *can* support pooling (the v1 Model A precedent `run_baseline_v186.py:97` pools BTC+ETH; `LightGbmStrategy` natively carries `_sym_arr` and `cv_gap = embargo_candles × n_symbols`) — so this is a **signal falsification, not a feasibility one**. Direction 3 is closed for v3 by this EDA. The QR Audit Trail (Section 10) documents the supersession.

### 2.1 — T1: Engineered feature vs triple-barrier label — Spearman IC (IS-only)

From `part4_t1_engineered_ic.csv` (`funding_regime_engineered_feature.py`):

| Symbol | IC(engineered, label) | IC(raw `regime_momentum_signed_5d`, label) | \|IC\| gain |
|---|---:|---:|---:|
| BCHUSDT | **+0.0193** | −0.0059 | **+0.0134** |
| LDOUSDT | **+0.0285** | −0.0870 | −0.0585 |
| TRXUSDT | −0.0345 | −0.0305 | +0.0039 |

The engineered feature **\|IC\|-gains on 2/3 symbols** vs the raw primitive, and on BCH/LDO the IC **flips sign** — the funding-conditioning is not a cosmetic rescale; it changes the directional relationship to the label. (LDO's raw-primitive \|IC\| is large only because LDO's raw momentum is a strong *wrong-direction* signal; the funding-conditioned variant is a smaller but *correctly-signed* +0.0285.)

### 2.2 — T2: Orthogonality vs the 14-feature stack (Category-2 IC check)

From `part4_t2_orthogonality.csv`:

| Symbol | \|IC\| vs `regime_momentum_signed_5d` (the primitive) | max \|IC\| vs the full 14-stack | nearest feature |
|---|---:|---:|---:|
| BCHUSDT | 0.0134 | 0.0720 | ret_kurt_200 |
| LDOUSDT | 0.0799 | 0.1139 | ema_spread_atr_20 |
| TRXUSDT | 0.0125 | 0.1936 | range_realized_vol_50 |

**Worst max \|IC\| vs the stack = 0.1936** — far below the 0.70 hard gate AND below the 0.50 strict target. Critically, the engineered feature is **near-orthogonal to its own primitive** (max 0.0799) — it does NOT repackage `regime_momentum_signed_5d`. This avoids the iter-v3/070 trap (a feature that correlates with an existing feature and steals `colsample_bytree` picks). Per the `feedback_v3_engineered_feature_pivot.md` Category-2 carve-out the IC gate is informational for composed features; here the feature passes the *strict* gate anyway — a stronger result.

### 2.3 — T3: Incremental-information test — 14 vs 15 features (chronological IS 70/30 split)

From `part4_t3_incremental.csv` — a quick per-symbol LightGBM, 14 features vs 14 + the engineered feature, chronological IS-only 70/30 split:

| Symbol | base rate | acc (14 feat) | acc (15 feat) | accuracy lift | engineered importance share | engineered rank /15 |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 0.5127 | 0.5216 | 0.5074 | −0.0142 | 0.017 | 15/15 |
| LDOUSDT | 0.5195 | 0.5359 | 0.5296 | −0.0063 | 0.053 | 12/15 |
| TRXUSDT | 0.5536 | 0.4626 | 0.4782 | **+0.0156** | 0.021 | 15/15 |

**This is the load-bearing — and honest — table.** A quick fixed-hyperparameter LightGBM at no Optuna budget ranks the engineered feature 14.0/15 mean (12/15 on LDO, 15/15 on BCH/TRX) with mean accuracy lift −0.0016. This is the documented NEW-feature low-budget signature (`feedback_v3_exploration_n_trials_35.md`: NEW features rank near-last in quick probes because TPE/feature-selection cannot surface them without an Optuna search). It is NOT a falsification of the axis — it is the *reason* the EXPLORATION run (35 Optuna trials × 3-seed ensemble) is the actual test. The PROVEN-PROMISING iter-v3/025 feature `regime_momentum_signed_5d` would have shown the same weak signature in an identical quick probe. The brief reports this honestly and Section 7 pre-registers PROMISING-INERT as the single most-likely outcome (≈45%) precisely because of this table.

### 2.4 — T4: Funding-regime coverage (the engineered feature is non-degenerate)

From `part4_t4_funding_coverage.csv`:

| Symbol | funding_z_30 coverage | frac funding_z > 0 | frac funding_z < 0 |
|---|---:|---:|---:|
| BCHUSDT | 100.00% | 50.42% | 42.21% |
| LDOUSDT | 100.00% | 58.61% | 35.86% |
| TRXUSDT | 100.00% | 56.83% | 41.86% |

Funding data is **complete (100% coverage)** for all 3 v3 symbols (`data/funding_rates/{BCH,LDO,TRX}USDT.csv` — 7021 / 3998 / 6941 rows). The funding-z sign is **genuinely two-sided** (35–58% each side) — the sign-switch fires in both directions across the IS window; the engineered feature is not a degenerate constant.

### 2.5 — T-LDO: the structural context (the IS-data fact that frames v3's fragility)

From `pooled_model_cross_symbol_structure.py` Q1 + a directional-edge probe:

| Symbol | IS span (months) | IS labelable rows | label long-share | mean realized PnL of the labeled side |
|---|---:|---:|---:|---:|
| BCHUSDT | 62.7 | 5627 | 48.6% | +4.02 |
| LDOUSDT | **30.0** | **2641** | 50.0% | +4.54 |
| TRXUSDT | 62.2 | 5569 | 54.7% | +3.18 |

LDO has only 30 months of IS history against `training_months = 24` — its walk-forward gets ≈6 testable IS cells. This is recorded as the IS-data root of LDO's chronic weakness (BASELINE_V3.md: LDO OOS WR 25.0%). It is NOT the /085 axis (`training_months` is immutable; the pooled-donor fix to LDO scarcity was EDA-falsified in T-pool above) — it is the context that motivates a feature-construction axis over an architecture axis.

## Section 3 — Proposed Changes

### 3.1 The single axis — one NEW Category-2 composed feature

`V3_FEATURE_COLUMNS_TOP_N` grows 14 → 15 by appending exactly one feature:

```
funding_regime_momentum_5d  =  regime_momentum_signed_5d  ×  sign(funding_z_30)
```

where `funding_z_30` is the 30-period (10-day, = 30 8h funding-settlement cycles) z-score of the past-only funding rate:

```
funding_z_30[t] = ( funding_rate[t] − mean(funding_rate.shift(1), 30) )
                  / ( std(funding_rate.shift(1), 30) + 1e-9 )
sign(funding_z_30)  ∈ {−1, 0, +1}   (0 → NaN-propagated, no signal)
```

The 30-candle funding window is **fixed a-priori** at the funding-settlement-cycle convention (30 × 8h = 10 days) — it is NOT swept on any metric. Single-feature, single-axis: nothing else changes (no labeling change, no symbol change, no risk-gate change, no model-architecture change, no seed change). Per `feedback_v3_engineered_features_dont_stack.md`, exactly ONE engineered feature is added at single-seed EXPLORATION — no same-family or cross-family stacking.

### 3.2 Why this is a Category-2 composed feature (the iter-v3/025 carve-out applies)

`funding_regime_momentum_5d` is a composed/interaction feature in the exact sense of `regime_momentum_signed_5d` (`ret_5d × sign(hurst_100 − 0.5)`) — a primitive sign-switched by a regime indicator. Per `feedback_v3_engineered_feature_pivot.md`: for Category-2 features the IC hard gate is **informational**; the binding gate is **importance rank ≤10 AND absolute importance ≥30 for ≥1 symbol** (the incremental-information test). Section 8 LOCKS the PATH taxonomy on that basis. Engineered composed features are the one PROVEN-PROMISING v3 axis post-bootstrap (`feedback_v3_engineered_features_proven.md`, iter-v3/025: IS +0.50 / OOS +0.84) — /085 is squarely in the recommended family.

### 3.3 Why this is DIFFERENT from the CLOSED v3 funding axis

The v3 funding axis is CLOSED at 4 data points (/019/023/024/082; BASELINE_V3.md Dead Ideas). **Every one of those fed funding as a DIRECT model feature** — `funding_rate_zscore_30` (a Category-1 standalone z-score), `btc_funding_rate_zscore_30` (the BTC cross-asset variant), and the /082 4-channel family (`funding_sign_persist_9`, `funding_momentum_3`, `funding_accel_3`, `funding_price_divergence_6`). All were INERT-by-importance because the model never split on raw funding.

iter-v3/085 does **not** feed funding as a model feature at all. The funding rate enters ONLY as a `sign()` switch *inside* a composed feature — it conditions *what raw momentum means*, it is never a column the tree can split on directly. This is a Category-2 composed construction (the carve-out family), structurally distinct from the closed Category-1 funding-as-direct-feature axis. The closed literal-name bans (`funding_rate_zscore_30`, `btc_funding_rate_zscore_30`) are untouched and stay enforced — `funding_regime_momentum_5d` is a different column with a different construction. The Phase 5.5 gate must adjudicate this differentiation (it is the cycle-3-plan-mandated funding-differentiation analysis, the analogue of the /082 brief Section 3.4).

### 3.4 Look-ahead discipline (Critic Check 1)

The engineered feature is past-only by construction:
- `regime_momentum_signed_5d` is already a verified past-only column (`engineered_v3.py:compute_regime_momentum_signed_5d` — `ret_5d` uses `log_close.shift(15)`, `hurst_100` is a trailing 100-bar window).
- `funding_rate[t]` settled at candle `open_time` and is broadcast ≈5 min before the 8h boundary — knowable at bar t open (the identical convention `funding_v3.py` already uses and `test_funding_v3.py` enforces).
- `funding_z_30` applies `funding_rate.shift(1)` before the 30-bar rolling mean/std, so bar t's own settlement never enters its own z-score window.
- `funding_regime_momentum_5d[t]` = (past-only momentum at t) × sign(past-only funding-z at t) — an element-wise product of two past-only series.
- The QE must add a spike-perturbation test (`test_engineered_v3.py` or `test_funding_family_v3.py` pattern): perturb `funding_rate[k]` by a large value, assert `funding_regime_momentum_5d` is unchanged at all bars `< k`.

### 3.5 Engineering checklist for Phase 6 (feasibility — CONTAINED, no new fetcher)

The implementation is a contained feature addition — **no new data feed, no new fetcher**. The `data/funding_rates/<SYMBOL>.csv` cache already exists for all 3 v3 symbols (built at iter-v3/019, refreshed; 100% coverage per T4). Steps:

1. Add `compute_funding_regime_momentum_5d(df, funding_df)` to `src/crypto_trade/features_v3/engineered_v3.py` — model it on `compute_regime_momentum_signed_5d` for the composed-feature pattern and on `compute_funding_family`'s funding-merge + `.shift(1)` discipline for the funding-z leg. The function reads the per-symbol funding CSV (the `add_funding_family_v3_features` entry-point pattern) and depends on `regime_momentum_signed_5d` being upstream in `GROUP_REGISTRY` (it is — `engineered_v3` group).
2. Register the `funding_regime_momentum_5d` column in the appropriate `GROUP_REGISTRY` entry (the `engineered_v3` group, AFTER `regime_momentum_signed_5d`; insertion order matters per the `engineered_v3.py` module docstring).
3. Append `funding_regime_momentum_5d` to `V3_FEATURE_COLUMNS_TOP_N` in `src/crypto_trade/features_v3/__init__.py` (count 14 → 15). `features_for_symbol(sym)` returns 15 for all 3 symbols.
4. `run_baseline_v3.py`: `ITERATION_LABEL → "v3-085"`; the runner pre-flight assertions that count `V3_FEATURE_COLUMNS_TOP_N` (currently `== 14`) update to `== 15` and assert the new column name by literal. `REQUIRED_GAP` stays `66 = (21+1)×3` (universe count unchanged).
5. **Config-accretion pre-flight** (the `_canonical_v059` 11-knob check): the 11 RiskV3-config knobs stay /059-canonical (untouched by a feature axis). The feature axis is /085's declared single change — it is NOT a RiskV3 config knob, so it does not appear in the `_canonical_v059` table; the table stays as-is and still guards a /061-style accretion. Carve-out documentation: the `V3_FEATURE_COLUMNS_TOP_N` 14→15 change is /085's declared axis (recorded in the runner comment block + this brief).
6. Regenerate the 3 v3 feature parquets (`crypto-trade features --track v3` — or the runner's `_generate_v3_features`) so the new column is materialized.
7. Tests: a past-only spike-perturbation test for the new feature; update `tests/strategies/ml/test_*` and any `V3_FEATURE_COLUMNS` count assertion 14→15. Per the cycle-3 plan, run `uv run pytest` on affected dirs.
8. Run: `uv run python run_baseline_v3.py --exploration --n-trials 35` (single-axis EXPLORATION mode; `--clean-oof` per the OOF guardrail).

### 3.6 Wall-clock estimate

/082 (a 4-feature funding-family addition, 14→18, EXPLORATION 3-seed, n_trials=35) ran **0.74h**; /084 (3-symbol, 14-feature, EXPLORATION 3-seed) ran **0.70h**. /085 adds ONE feature (14→15) — a smaller delta than /082's four. Estimate **≈ 0.7h**, well within the 2h EXPLORATION HARD CAP.

## Section 4 — Expected OOS Impact

### 4.1 The two anchors (MANDATORY — Critic /084 Recommendation #2)

**ANCHOR 1 — the EXPLORATION-MODE-REFERENCE = iter-v3/084: IS monthly Sharpe +0.8325 / OOS monthly Sharpe +0.3322 (3-seed EXPLORATION-mode, current data).** iter-v3/085's single-axis Δ is classified against THIS anchor. /085 runs 3-seed EXPLORATION-mode — it is architecturally matched to /084's 3-seed reference.

**ANCHOR 2 — the /059 CONFIRMATION baseline = IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791 (10-seed CONFIRMATION-mode, tag `v0.v3-059`).** RESERVED for the iter-v3/092 CONFIRMATION ONLY. /085's EXPLORATION delta is **NOT** computed against this number — a 3-seed EXPLORATION run vs a 10-seed CONFIRMATION number is a ≈0.26-IS architecture mismatch, the exact /082/083 error the /084 closeout corrected (BASELINE_V3.md "EXPLORATION-vs-CONFIRMATION architecture-gap finding").

### 4.2 Predicted impact (vs ANCHOR 1, the /084 EXPLORATION-MODE-REFERENCE)

Predicted IS monthly Sharpe Δ: **+0.05 ± 0.20** (central estimate small-positive; the T3 quick-probe weakness caps the upside, the T1/T2 orthogonal-and-correctly-signed IC supports a non-negative central estimate). Predicted OOS monthly Sharpe Δ: **+0.00 ± 0.30** (a feature axis touches no barrier — see 4.3; no directional OOS prediction). These are *estimates*; the falsifier band below is the *gate* (per `feedback_v3_per_symbol_target_axis_falsifier.md`, predictions and falsifiers must reference different numbers).

### 4.3 Falsifier (LOCKED) + holding-time / roster-composition predictor

**Holding-time predictor.** `funding_regime_momentum_5d` is a pure model FEATURE — it touches no SL, no TP, no timeout, no labeling. By the iter-v3/076 mechanism it CANNOT extend holding time via barrier mechanics. The full-roster mean/median trade-duration Δ is predicted **≈ 0.0 candles** (any change is via trade SELECTION, not barrier extension).

**The /076 trade-selection sub-channel falsifier (LOCKED).** A feature axis can still load the IS/OOS regime factor by SELECTING longer-held trades (the /076 mechanism). Pre-registered sub-channel falsifier: on the /084-anchor OOS roster diff, **the mean trade duration of the trades /085 ADDS minus the trades it REMOVES must be ≤ +1.0 candle**. If the added set skews > +1.0 candle longer-held than the removed set, the regime factor is loaded via selection → SUSPICIOUS (Section 8.3).

**Headline falsifier (LOCKED).** If IS monthly Sharpe Δ vs ANCHOR 1 < **−0.10**, the hypothesis is rejected as NEGATIVE (the engineered feature harms via expanded overfit space — `feedback_v3_inert_features_at_higher_budget.md` PATH C).

### 4.4 OOS/IS ratio SUSPICIOUS gate (LOCKED — `feedback_v3_oos_is_ratio_gate.md`)

Pre-registered, ratio computed against /085's own IS and OOS:
- **OOS/IS monthly Sharpe ratio > 3.0 → SUSPICIOUS**, regardless of absolute OOS magnitude.
- **OOS-DOMINANT sub-mode → SUSPICIOUS**: IS Δ < 0 (vs ANCHOR 1) AND OOS Δ ≥ +0.20 (vs ANCHOR 1) — the /078/082 signature.

## Section 5 — Risk Mitigation

The 7-primitive v3 risk-gate stack is UNCHANGED (BTC trend kill, vol scaling, ADX, Hurst regime, feature z-score OOD, low-vol filter, hit-rate [disabled]). /085 adds no risk primitive — it is a single feature axis, single-axis discipline. The risk relevant to /085:
- **Overfit-via-feature-expansion** (R-feature): the dominant risk. Mitigation — the feature is Category-2 composed (orthogonal to the stack, T2) so it does not duplicate an existing split dimension; the single-feature discipline keeps the Optuna search-space expansion minimal (one column, vs /082's four); the EXPLORATION 3-seed ensemble averages over 3 models. Simulated historical effect: /082 (4 funding features) produced no IS damage (IS Δ −0.0118) — a single composed feature is a smaller perturbation; the headline falsifier (IS Δ < −0.10 → NEGATIVE) is the catch.
- **Look-ahead via the funding leg** (R-leakage): mitigated by the `.shift(1)` discipline (3.4) + the mandatory spike-perturbation test.
- The feature z-score OOD gate (primitive 5) already guards against the new feature taking extreme out-of-distribution values at predict time — no new OOD wiring needed.

## Section 6 — Risk Management Design

v3's 7-primitive gate stack, all /059-canonical, none changed by /085:

| # | Primitive | Status at /085 | Fire-rate expectation |
|---|---|---|---|
| 1 | BTC trend kill (±15%, 14d) | unchanged | as /084 |
| 2 | Vol scaling | unchanged | as /084 |
| 3 | ADX threshold (20.0) | unchanged | as /084 |
| 4 | Hurst regime | unchanged | as /084 |
| 5 | Feature z-score OOD (2.0) | unchanged — also covers the new feature | marginal increase possible (one more feature in the z-score vector) |
| 6 | Low-vol filter | unchanged | as /084 |
| 7 | Hit-rate gate | DISABLED (as /059) | n/a |

Regime coverage: the new feature is itself a regime-conditioning device (funding-crowding regime) — it adds regime-awareness to the *model*, complementary to the gate stack's regime gates. No gate fire-rate is expected to move materially (a feature change does not change the gate inputs except the OOD z-score vector, where one added orthogonal feature is a minor perturbation).

## Section 7 — Pre-Registered Failure-Mode Prediction

iter-v3/085 most plausibly fails as **PROMISING-INERT** — the engineered feature is added but the depth-4 LightGBM, even with 35 Optuna trials, ranks it ≥14/15 by importance and the headline IS Sharpe Δ stays inside the ±0.10 noise band. The Section 2.3 T3 quick-probe is the explicit warning: at no Optuna budget the feature ranked 14.0/15 mean with mean accuracy lift −0.0016. The Optuna search may surface it (the iter-v3/025 PROVEN feature also looked weak in a quick probe) — but the base rate says a NEW feature at single-seed EXPLORATION most often ranks near-last (`feedback_v3_exploration_n_trials_35.md`; /015/019/082 all hit it). If PROMISING-INERT fires, the verdict is non-advancing and the feature is dropped per `feedback_v3_inert_features_at_higher_budget.md` (an INERT feature is not carried forward and not retested at higher budget).

The second failure mode is **SUSPICIOUS-OOS-DOMINANT** (≈20%): the feature is INERT-by-importance but its addition perturbs the Optuna hyperparameter search along an uninformative dimension; on the 3-seed draw the perturbed hyperparameters' OOS realization catches the v3 OOS uptrend (the /082 mechanism exactly — IS flat, OOS soars, OOS/IS ratio elevated or the OOS-DOMINANT sub-mode fires). The Section 4.4 ratio gate + OOS-DOMINANT sub-mode is the detector. The third mode is **NEGATIVE** (≈15%): the feature actively harms IS by expanding the overfit space (`feedback_v3_inert_features_at_higher_budget.md` PATH C — the iter-v3/023 pattern). The residual is **PROMISING** (≈20%): the funding×momentum interaction is genuine and the Optuna search surfaces it (rank ≤10, importance ≥30, IS Δ ≥ +0.10) — the iter-v3/025 outcome. The probabilities (≈45 INERT / ≈20 SUSPICIOUS / ≈15 NEGATIVE / ≈20 PROMISING) are honest: the central forecast leans INERT because the T3 quick-probe evidence and the cycle-1+2+3 NEW-feature track record both point there; the brief does not float PROMISING above what the marginal-but-positive T1/T2 evidence supports.

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (LOCKED classification taxonomy)

Anchor for all Δ: **ANCHOR 1 — the /084 EXPLORATION-MODE-REFERENCE, IS +0.8325 / OOS +0.3322.** Disjunctive precedence, first match canonical: **SUSPICIOUS → NEGATIVE → PROMISING → INERT → NULL-RESULT.** This is a Category-2 composed-feature axis — the `feedback_v3_engineered_feature_pivot.md` carve-out governs (IC gate informational; importance-rank gate binding).

### 8.1 PROMISING
IS monthly Sharpe Δ ≥ **+0.10** vs ANCHOR 1 **AND** OOS monthly Sharpe Δ ≥ **−0.10** vs ANCHOR 1 **AND** CPCV `frac_positive_paths` ≥ 0.50 **AND** NOT SUSPICIOUS **AND** the engineered feature ranks **≤ 10 of 15** by importance with absolute importance **≥ 30** for **≥ 1 symbol** (the Category-2 incremental-information gate). All five required.

### 8.2 NEGATIVE
IS monthly Sharpe Δ < **−0.10** vs ANCHOR 1 **OR** OOS monthly Sharpe Δ < **−0.20** vs ANCHOR 1 (and NOT SUSPICIOUS).

### 8.3 SUSPICIOUS (disjunctive precedence — fires before PROMISING)
ANY of: (a) OOS/IS monthly Sharpe ratio > **3.0**; (b) **OOS-DOMINANT sub-mode** — IS Δ < 0 AND OOS Δ ≥ +0.20 vs ANCHOR 1; (c) the /076 **trade-selection sub-channel** — the added-vs-removed OOS-roster mean-duration gap > **+1.0 candle**.

### 8.4 INERT (Category-2 PATH B — PROMISING-INERT)
Both IS Δ and OOS Δ inside the noise bands (IS Δ ∈ [−0.10, +0.10] AND OOS Δ ∈ [−0.20, +0.20]) **OR** the engineered feature ranks ≥ 14/15 by importance across ≥ 2 of 3 symbols. Non-advancing; the feature is dropped at the /086 setup.

### 8.5 NULL-RESULT
The /085 trade roster is bit-identical to the /084 roster (no behavioral effect). Listed for taxonomy completeness — a 15th feature the model uses at all is not bit-identical; near-impossible here.

**MERGE/advancement rule.** Only a **PROMISING** /085 advances to the iter-v3/092 CONFIRMATION bundle as an edge ingredient. SUSPICIOUS / NEGATIVE / INERT / NULL-RESULT are all non-advancing. An EXPLORATION never updates BASELINE_V3.md regardless.

## Section 9 — Library Stack Declaration

No new libraries. The /059-canonical stack, pinned: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1. The engineered feature is pure numpy/pandas arithmetic — no `mlfinlab`/`fracdiff`/`pypbo` dependency. The EDA scripts use `lightgbm`, `numpy`, `pandas`, `pyarrow`, `scipy.stats` — all already pinned.

## Section 10 — QR Audit Trail (literature-research path + axis supersession)

**The orchestrator's steer and the QR override (`feedback_v3_axis_selection_quant_discipline.md`).** The /084 closeout and the orchestrator dispatch named Direction 3 (a multi-symbol-pooled model) as /085's lead candidate. The QR is required to make the final axis call with committed EDA. iter-v3/085 ran three IS-only EDA probes against the pooled model — `pooled_model_cross_symbol_structure.py` (naive pool), `pooled_with_symbol_dummy.py` (pool + symbol_id), `ldo_donor_augmentation.py` (LDO-only donor augmentation) — and **all three falsified it** (Section 2.0). The pooled-model axis is therefore SUPERSEDED by EDA, not by orchestrator preference. The runner *can* support pooling (the v1 Model A precedent, `LightGbmStrategy`'s native `_sym_arr` handling) — this was a signal falsification, not a feasibility one. The QR then committed the funding-regime engineered-feature axis, EDA-grounded in `funding_regime_engineered_feature.py`.

**Literature-research path (the cycle-3 research mandate, `feedback_v3_bold_research_mandate.md`).** WebSearch/WebFetch consulted in Phases 1–4:
- **Cakici, Shahzad, Będowska-Sójka, Zaremba — "Machine Learning and the Cross-Section of Cryptocurrency Returns"** (SSRN 4295427; *International Review of Financial Analysis* 94, 2024). Establishes that ML works on the crypto cross-section but **simple models prevail and the benefit of model complexity is limited** — and that crypto alphas come from long trades that persist. This evidence cuts *against* a complex pooled-panel model and *toward* a targeted feature improvement on the existing per-symbol architecture.
- **Gu, Kelly, Xiu — "Empirical Asset Pricing via Machine Learning"** (NBER w25398). The canonical pooled-cross-section ML methodology — one model on the pooled panel of all assets. It is the *reference design* for Direction 3; the iter-v3/085 EDA tested whether v3's specific 3-symbol cross-section has the shared structure the Gu/Kelly/Xiu design requires, and found it does not (only 7/14 features sign-agree; cross-symbol transfer lift is negative).
- **BIS Working Paper 1087, "Crypto carry" (2025)** — funding/carry shocks predict liquidation jumps; funding regimes encode positioning crowding. This motivates the funding-crowding-regime conditioning that the /085 engineered feature applies (funding as a regime sign-switch, not a direct feature).
- The bias-variance literature (Gu/Kelly/Xiu §; standard pooled-OLS panel theory) — pooling reduces variance via more rows but introduces bias when the pooled units have heterogeneous data-generating processes. v3's BCH/LDO/TRX have heterogeneous feature→label maps (Section 2.0) → the pooling bias dominates.

**Selection criteria — from "literature says X" to "the /085 axis is Y".** (1) The pooled-panel literature (Gu/Kelly/Xiu) is the natural Direction-3 design — the QR tested it with EDA and the v3 cross-section failed the shared-structure precondition. (2) Cakici et al. — "simple models prevail" — argues against adding complexity (a pooled panel) and for a targeted feature on the existing simple per-symbol models. (3) BIS WP 1087 — funding-crowding is a real crypto-native regime signal — but the closed v3 funding axis proved funding-as-direct-feature is INERT; the literature-consistent move is funding as a *regime conditioner inside a composed feature*, which is the `feedback_v3_engineered_feature_pivot.md` Category-2 family (the one PROVEN-PROMISING v3 axis). The /085 axis — `funding_regime_momentum_5d` — is the intersection of those three findings.

**EDA SHA**: `5264091` — `analysis/iteration_v3-085/pooled_model_cross_symbol_structure.py`, `pooled_with_symbol_dummy.py`, `ldo_donor_augmentation.py`, `funding_regime_engineered_feature.py`.
**Brief SHA**: `<BRIEF_SHA>` (backfilled by the immediately-following commit).
**Setup SHA**: `<SETUP_SHA>` (backfilled at setup).
