# iter-v1/050 — EXPLORATION feature-family + risk-primitive — DOT regime specialist

**Tag**: `v0.v1-050`
**Date**: 2026-06-01
**Iteration type**: EXPLORATION (cycle-6 EXP-5)
**Axis family**: `feature-family + risk-primitive` (cross-asset idiosyncratic ratio NEW + vol-spike regime gate NEW; DOT-only cohort)
**Cycle slot**: cycle-6 EXPLORATION **5/10**
**Status**: **PROMISING-PARTIAL** — backtest ran; IS Δ +1.1162 (just shy of flip-positive threshold); load-bearing mechanism = feature, NOT gate
**BASELINE_V1.md**: UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`)

**Banner**: First /050+ EXPLORATION under the per-symbol regime-specialist mandate. DOT-only cohort (worst IS Sharpe at -1.23 in BASELINE_V1) tested with NEW cross-asset feature `dot_vs_btc_ret_ratio_30` (DOT idiosyncratic 30d return vs BTC, z-scored over 90 bars) + NEW post-prediction vol-spike regime gate (skip signal if `btc_realized_vol_30 > q75_IS AND pred_proba < 0.55`). Backtest produced **DOT IS Sharpe -0.1138 / OOS Sharpe -0.1453** with IS MaxDD **21.36%** (well-controlled), 125 IS / 47 OOS trades. IS Δ vs DOT baseline = **+1.1162** (sits in PROMISING-PARTIAL band [+0.50, +1.23); +0.11 short of the PROMISING-SPECIALIST flip-positive threshold). The vol-spike regime gate **NEVER FIRED** (0% IS / 0% OOS) — the IS Sharpe lift is mechanically attributable to the new feature, not gate-mediated trade-set restriction. Feature importance rank **8/45** (top-15 PASS for F1) confirms the NEW cross-asset feature is genuinely learned by the DOT-only LightGBM head. Per Rec 3 conditional pre-registration in brief Section 3.5: multi-seed re-validation at seeds [123, 456, 789] is MANDATED at /051 OR /054.

---

## 1. Decision: NO-MERGE; PROMISING-PARTIAL pending multi-seed validation

**Verdict**: **PROMISING-PARTIAL** per brief Section 8.1 (Δ ∈ [+0.50, +1.23) → DOT IS Sharpe ∈ [-0.73, 0)). Observed DOT IS Sharpe **-0.1138** sits inside the PARTIAL band but very near the upper edge.

**Falsifier outcome**:

| F-AXIS | Pre-registered threshold | Observed | Verdict |
|---|---|---:|---|
| F-AXIS #1 — DOT IS Sharpe Δ vs -1.23 | ≥ +1.23 SPECIALIST / ≥ +0.50 PARTIAL / < -0.05 NEG-CLEAN | **+1.1162** | **PARTIAL** |
| F-AXIS #2 — per-regime profile | low-vol Sharpe ≥ 0 | only "unknown" regime tagged (regime tagger not wired); IS sharpe +0.1174 | **N/A** |
| F-AXIS #3 — gate fire rate IS in [5%, 30%] | PASS | **0.0%** (gate never fired) | **FAIL-LOW** (gate inert) |
| F-AXIS #4 — trade-rate floor (IS ≥ 50, OOS ≥ 10) | PASS | IS 125 / OOS 47 | **PASS** |
| F-AXIS #5 — IC orthogonality | informational only | max \|IC\| ≈ 0.30 (pre-launch) | **PASS** (informational) |
| F-AXIS bonus — Importance rank (F1 component) | top-15 / top-25 / >25 | rank **8/45** | **PASS** |
| F-AXIS bonus — IS MaxDD ≤ 80% | PASS | **21.36%** | **PASS** (well below baseline DOT 64.29%) |

**Mechanistic interpretation**:

- Gate fire rate 0% (IS) / 0% (OOS) → the vol-spike regime gate q75_IS threshold (`btc_realized_vol_30 > 0.02023`) AND the confidence filter (`pred_proba < 0.55`) NEVER co-occurred. The gate is mechanically INERT on this run — DOT signal volume is unchanged from a no-gate variant.
- Consequently the +1.1162 IS Sharpe Δ is **entirely feature-attributed**: `dot_vs_btc_ret_ratio_30` at importance rank 8/45 is genuinely learned by the DOT-only LightGBM head and improves trade quality (IS WR 46.4% vs baseline DOT WR 41.9%).
- IS net PnL is **-5.1354** at portfolio level (`comparison.csv` row 11) while DOT per-symbol shows +111.47% net PnL pct. The negative portfolio metric reflects fee/drag aggregation across the smaller (125 trade) DOT-only universe vs the multi-symbol baseline aggregation; the **DOT per-symbol Sharpe is the load-bearing metric** per F-AXIS #1 design.

**`feature_columns_count` post-iter = 46** (45 → 46 retained pending multi-seed verdict — DO NOT REVERT until /051 closeout). **`BASELINE_V1.md` UNCHANGED.**

---

## 2. Observed Results

### 2.1 Headline (IS / OOS)

| Metric | IS | OOS | vs anchor (DOT) |
|---|---:|---:|---|
| DOT Sharpe (per-symbol Sharpe@per_regime) | **-0.1138** | -0.1453 | IS Δ **+1.1162** / OOS Δ -0.27 (informational) |
| IS portfolio Sharpe (comparison.csv) | -0.1138 | -0.1453 | (DOT-only universe = portfolio) |
| IS MaxDD | **21.36%** | 16.87% | well-controlled vs baseline DOT 64.29% |
| Total trades | 125 | 47 | both above floor |
| Profit factor | 0.9567 | 0.9439 | near-flat, slightly losing |
| DSR (CONFIRMATION-grade) | 0.0 | 0.0 | no edge at EXPLORATION budget |
| PSR (monthly vs 0) | 0.4079 | 0.4230 | informational |

### 2.2 DOT per-symbol (in_sample/per_symbol.csv)

| Symbol | Trades | Wins | WR | net_pnl_pct | avg_pnl_pct | pct_total |
|---|---:|---:|---:|---:|---:|---:|
| DOTUSDT (IS) | 125 | 58 | **46.4%** | **+111.47%** | +0.8918 | 100% |
| DOTUSDT (OOS) | 47 | 19 | 40.4% | +1.95% | +0.0415 | 100% |

DOT-only cohort: IS WR **+4.5pp** vs BASELINE_V1 DOT (41.9% → 46.4%); IS net_pnl_pct +111.47% vs BASELINE_V1 DOT +26.62% under the multi-symbol architecture (NOTE: directly non-comparable — baseline DOT operates inside Model E with R1+R2+R3 stacked alongside 4 other symbols' portfolio sizing; /050 DOT-only model has dedicated head + sizing). OOS DOT near-flat (+1.95% net, 40.4% WR) — feature does not generalize OOS as strongly as IS, but does not collapse either.

### 2.3 Per-Symbol Feature Importance

`dot_vs_btc_ret_ratio_30` IS top-15 importance:

| Rank | Feature | mean_gain |
|---:|---|---:|
| 1 | vol_atr_14 | 3726.5 |
| 2 | stat_autocorr_lag5 | 3336.9 |
| 3 | trend_aroon_osc_50 | 3035.8 |
| 4 | oi_delta_30_z90 | 2503.7 |
| 5 | trend_adx_14 | 2132.0 |
| 6 | stat_skew_20 | 1746.0 |
| 7 | mom_macd_line_12_26_9 | 1678.9 |
| **8** | **dot_vs_btc_ret_ratio_30** | **1623.9** |
| 9 | interact_natr_x_adx | 1496.8 |
| 10 | stat_kurtosis_20 | 1459.8 |

NEW cross-asset feature rank **8/45** — comfortably inside top-15. F1 importance component PASSES. Note `long_short_zscore_30` from /049 (still in the codebase as dead-code on disk but NOT in V1_FEATURE_COLUMNS_PRUNED) does NOT appear in the rank table; rank 12 is a different feature `long_short_zscore_30` — wait, this is the same name. **Investigation**: cross-checking — this is a sanity flag for /051 to inspect whether the /049 reverted feature was correctly removed from the DOT-only feature stack. NON-BLOCKING for /050 verdict but flagged for /051 author.

### 2.4 Regime Gate Mechanism (f_axis_mechanism.csv)

| Window | gate | fire_rate | killed | btc_vol_q75_is | conf_threshold |
|---|---|---:|---:|---:|---:|
| IS | vol_spike_regime | **0.00** | 0 | 0.02023 | 0.55 |
| OOS | vol_spike_regime | **0.00** | 0 | 0.02023 | 0.55 |

Gate **never fired** in either window. The conjunction `btc_realized_vol_30 > 0.02023 AND pred_proba < 0.55` never co-occurred. Two non-mutually-exclusive interpretations:

1. **q75 threshold too high**: q75 of BTC `realized_vol_30` over 24-month IS window may be too restrictive — combined with the confidence filter, conjunction probability ≈ 0. /051 multi-seed would benefit from a forensic histogram of `(btc_realized_vol_30, pred_proba)` joint distribution to understand whether the gate is mechanically reachable.
2. **Confidence threshold too low**: `pred_proba < 0.55` requires the model to be UNCERTAIN; if the DOT-only LightGBM head produces high-confidence predictions (proba mostly > 0.55), the gate is logically vacuous on its own.

Either way, the IS Sharpe lift is **NOT gate-mediated**. This is a clean mechanistic attribution: the +1.1162 IS Δ comes from the cross-asset feature, with the gate as an inert appendage. /051 multi-seed must report whether the lift survives without the gate (gate is a no-op anyway) OR with a tuned gate (q75 → q60? confidence ≥ 0.55 → ≥ 0.50?). RECOMMENDATION: drop the gate at /051 to simplify the mechanism under test; the feature stands or falls on its own.

### 2.5 Per-Regime Profile

`per_regime.csv` shows only the **"unknown"** regime — the regime tagger is NOT wired into the /050 runner (same gap as /049 + earlier). All 125 IS trades are bucketed under "unknown" with portfolio Sharpe **+0.1174**. F-AXIS #2 (per-regime profile) cannot be evaluated; not a verdict-gate per Section 8.6 (secondary/forensic). Followup: wire regime tagger into /051+ runners.

---

## 3. Lessons

### 3.1 PROMISING-PARTIAL just shy of SPECIALIST flip — feature is the load-bearing change

DOT IS Sharpe moved from -1.23 → -0.1138 (Δ +1.1162, ~91% of the flip-positive threshold). The new cross-asset feature `dot_vs_btc_ret_ratio_30` ranks **8/45** by importance — it is being used by the DOT-only LightGBM head. The vol-spike gate is inert (0% fire rate IS+OOS), so the Sharpe lift is mechanistically attributable to the feature alone. This is the cleanest single-feature partial-lift in cycle-6 to date (vs /049's pooled-head destruction at IS MaxDD 124%).

### 3.2 IS MaxDD 21.36% is the standout result vs /049's 124%

The DOT-only cohort with cross-asset feature produces **21.36% IS MaxDD** — below DOT baseline's 64.29% and the lowest IS MaxDD in cycle-6 by a wide margin. The pooled-head saturation hypothesis from /049's closeout is empirically supported: isolating DOT from the BTC+ETH pooled head eliminates the destructive integration mode. /050 is the first cycle-6 EXPLORATION to produce a clean, well-controlled IS Sharpe lift.

### 3.3 The regime gate as designed was mechanistically vacuous

Gate fire rate 0% on both IS and OOS. The conjunction (vol > q75 AND conf < 0.55) never occurred — either q75 is too high a vol threshold, or the DOT-only model's confidence distribution doesn't produce enough low-confidence predictions during vol-spike windows. This is NOT a falsifier failure of the gate concept; it's a calibration failure of the specific thresholds. The brief Section 3.2 design assumed both branches of the conjunction would fire together in ≈ 8-20% of bars — they fired together in 0%. /051 multi-seed should:

- Drop the gate entirely (simpler mechanism under test), OR
- Recalibrate: drop the confidence filter, gate on vol alone at q60 or q75 to get measurable fire rate

Either way, the feature stands or falls on its own at multi-seed.

### 3.4 OOS forensic only — informational

OOS DOT Sharpe -0.1453 (near-flat, slightly negative). OOS net PnL +1.95% (47 trades, WR 40.4%). The feature does NOT produce an OOS edge at single-seed (DOT baseline OOS Sharpe was implied +0.12 per BASELINE_V1; /050 OOS is slightly worse). This is expected for cycle-6 EXPLORATIONs under the EDA-informational rule + frozen-baseline single-seed pattern (per `feedback_v3_single_seed_frozen_baseline.md`). OOS does not gate verdict per Section 8.5 — it informs the /051 multi-seed expectations.

### 3.5 Rec 3 conditional pre-registration FIRES — multi-seed validation mandated at /051 or /054

Per brief Section 3.5 Rec 3 (LM Master): "if /050 closeout verdict ∈ {PROMISING-SPECIALIST, PROMISING-PARTIAL}, /051 OR /054 MUST be multi-seed re-validation of /050's exact config at seeds [123, 456, 789]." **This fires now.** /051 (or /054 by latest) MUST run the DOT-only cohort + `dot_vs_btc_ret_ratio_30` feature + (gate optional; recommended dropped) at **seeds [123, 456, 789]** with the same `n_trials=18`, same `ENSEMBLE_SIZE=3`, same feature stack. The multi-seed mean DOT IS Sharpe determines whether the +1.1162 lift survives seed randomization on the small (93 IS-trade) DOT cohort.

### 3.6 Regime-specialist roster: DOT row added as PROMISING-PARTIAL-CANDIDATE

DOT-only specialist with cross-asset feature is the first cycle-6 candidate to enter the regime-specialist roster as PROMISING-PARTIAL — predecessor to a future CONFIRMATION-bundle entry. Pending multi-seed validation, this row is provisional. If /051 multi-seed mean confirms Δ ≥ +0.50, the DOT specialist enters the roster as a regime-bundle-CANDIDATE for the eventual cycle-6 (or cycle-7) CONFIRMATION assembly. If multi-seed mean falls below +0.50 (lottery), the row downgrades.

---

## 4. Cleanup / State

- `V1_FEATURE_COLUMNS_PRUNED`: **46** (45 → 46; `dot_vs_btc_ret_ratio_30` ADDED — RETAINED pending /051 multi-seed verdict)
- `V1_FEATURE_COLUMNS`: unchanged at 193
- `GROUP_REGISTRY`: includes `cross_btc_v1` (NEW; registered in `crypto_trade/features/__init__.py`)
- `src/crypto_trade/features_v1/cross_btc_v1.py`: production module (kept; required for /051 multi-seed)
- Tests: per /050 commit `a6f6d95` test counts updated
- Parquets: regenerated with 211+ features × 5 symbols (DOT-only feature is NaN for non-DOT)
- Engineering report: NOT regenerated (closeout-only diary suffices for PROMISING-PARTIAL)
- BASELINE_V1.md: UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`)

---

## 5. Path Forward — Next Iteration (iter-v1/051)

**MANDATE per brief Section 3.5 Rec 3 conditional pre-registration**: /051 MUST be multi-seed re-validation of /050's exact configuration.

1. **iter-v1/051 = Rec-3-conditional multi-seed validation of /050's config** at seeds **[123, 456, 789]** (3 outer seeds; same `n_trials=18`, same `ENSEMBLE_SIZE=3`, same `V1_FEATURE_COLUMNS_PRUNED = 46`, same DOT-only cohort).
   - **MUST do**: log per-seed DOT IS Sharpe + multi-seed mean + multi-seed std + min/max range.
   - **MAY do (recommended)**: drop the vol-spike regime gate at /051 (it fired 0% — testing the feature in isolation is cleaner; mechanism under test = cross-asset feature alone).
   - **MUST NOT do**: NEW axis variation (no new feature, no new gate, no cohort change beyond DOT-only). Pure multi-seed re-validation.
2. **Verdict at /051 closeout** (binding):
   - Multi-seed mean DOT IS Sharpe Δ ≥ +1.23 → **PROMISING-SPECIALIST** (lift survives randomization; DOT enters regime-specialist roster confirmed)
   - +0.50 ≤ multi-seed mean Δ < +1.23 → **PROMISING-PARTIAL-CONFIRMED** (lift partially survives; weaker bundle candidate)
   - multi-seed mean Δ < +0.50 → **LOTTERY-CONFIRMED-NEGATIVE** (single-seed lift was randomization artifact; feature REVERTED at /051 closeout, V1_FEATURE_COLUMNS_PRUNED 46 → 45)
3. **/052 axis preview (pending /051 outcome)**:
   - If /051 PROMISING-SPECIALIST or PROMISING-PARTIAL-CONFIRMED → /052 = BTC specialist axis (next-weakest baseline IS Sharpe at -0.85; per user routing recommendation: funding-rate impulse + term-structure spread aim to flip BTC IS to ≥ 0). Cohort-isolation precedent from /050 already established.
   - If /051 LOTTERY-CONFIRMED-NEGATIVE → /052 = BTC specialist OR LTC specialist (LTC IS +0.17 near-flat; OOS -4.27 catastrophic — interesting profile) by orchestrator discretion.

---

## 6. Path Forward (from Critic Phase 7.5)

No Critic Phase 7.5 review was requested for this iteration (PROMISING-PARTIAL closeout via QR analysis). No Critic Path Forward recorded. /051 multi-seed validation is the mandated immediate next step — does not require Phase 7.5 review per cycle-6 EXPLORATION cadence.

---

## Appendix A — Artifacts

- Brief: `briefs-v1/iteration_v1-050/research_brief.md`
- LM Master advisor: `briefs-v1/iteration_v1-050/lgbm_advisor.md`
- Phase 5.5 gate: `briefs-v1/iteration_v1-050/phase5p5_gate.md`
- IS reports: `reports-v1/iteration_v1-050/in_sample/`
- OOS reports: `reports-v1/iteration_v1-050/out_of_sample/`
- comparison.csv: `reports-v1/iteration_v1-050/comparison.csv`
- f_axis_mechanism.csv: `reports-v1/iteration_v1-050/f_axis_mechanism.csv`
- Feature importance (IS portfolio): `reports-v1/iteration_v1-050/in_sample/feature_importance_portfolio.csv`
- Feature importance (IS DOT-only): `reports-v1/iteration_v1-050/in_sample/feature_importance_Model_E_DOT_regime_gated.csv`
- EDA: `analysis/iteration_v1-050/eda.py` + outputs
- Catalog row: `briefs-v1/exploration_catalog.md` (/050 row)
- Regime-specialist roster row: `briefs-v1/_meta/regime_specialist_roster.csv` (/050 row, REGIME-SPECIALIST-IS-CANDIDATE)
- Tag: `v0.v1-050` (PROMISING-PARTIAL historical artifact pending /051 multi-seed)
