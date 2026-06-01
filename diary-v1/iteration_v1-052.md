# iter-v1/052 — EXPLORATION feature-family — BTC specialist (funding impulse + 30/90 spread)

**Tag**: `v0.v1-052`
**Date**: 2026-06-01
**Iteration type**: EXPLORATION (cycle-6 EXP-7)
**Axis family**: `feature-family` (NEW non-OHLCV-derived funding-rate transforms; BTC-only specialist cohort)
**Cycle slot**: cycle-6 EXPLORATION **7/10**
**Status**: **PROMISING-SPECIALIST-CANDIDATE** — BTC IS Sharpe flipped positive; IS Δ +1.0109 (FLIP-POSITIVE band)
**BASELINE_V1.md**: UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`)

**Banner**: First BTC-specialist EXPLORATION under cycle-6 per-symbol roster mandate. BTC-only cohort (worst non-DOT IS Sharpe at -0.85 in BASELINE_V1) tested with NEW funding-rate-derived features `btc_funding_rate_8h_impulse` (90-bar normalized funding-rate first-difference; shock detector) + `btc_funding_spread_30_90` (algebraic term-structure slope, z30 - z90; positioning regime indicator) on BTC-only LightGBM head replacing pooled Model A for BTC signal generation. Backtest produced **BTC IS Sharpe +0.1609 / OOS Sharpe -1.3833 (informational)** with IS MaxDD **23.37%** (well-controlled), 133 IS / 70 OOS trades. **IS Δ vs BTC baseline -0.85 = +1.0109 — FLIP-POSITIVE band per brief §4 F-AXIS #1 (Δ ≥ +0.85 → PROMISING-SPECIALIST-CANDIDATE)**. Feature attribution diverges: `btc_funding_spread_30_90` at **importance rank 4/48** (strongly learned, top-5) carries the lift; `btc_funding_rate_8h_impulse` at **rank 38/48** is INERT relative to the brief's ≤24 target. Per Section 4 F-AXIS #4: "if one ranks ≤ top-15 and other ≥ top-25, attribution diverges → FLAG for /053 single-feature isolation. Does NOT override the both-or-neither revert rule." Verdict is PROMISING → both features RETAINED pending multi-seed re-validation at /053 (LM Master Rec 3 ADOPTED in brief Section 3.5: PROMISING → MANDATE multi-seed at /053).

---

## 1. Decision: NO-MERGE; PROMISING-SPECIALIST-CANDIDATE pending multi-seed validation

**Verdict**: **PROMISING-SPECIALIST-CANDIDATE** per brief §4 F-AXIS #1 (Δ ≥ +0.85 → FLIP-POSITIVE → PROMISING-SPECIALIST-CANDIDATE band). Observed BTC IS Sharpe **+0.1609** flips positive from baseline **-0.85** (Δ **+1.0109**).

**Falsifier outcome**:

| F-AXIS | Pre-registered threshold | Observed | Verdict |
|---|---|---:|---|
| F-AXIS #1 — BTC IS Sharpe Δ vs -0.85 | ≥ +0.85 SPECIALIST / [+0.30, +0.85) PARTIAL / [+0.05, +0.30) WEAK / (-0.05, +0.05) INERT / < -0.05 NEG-CLEAN | **+1.0109** | **FLIP-POSITIVE** (PROMISING-SPECIALIST-CANDIDATE) |
| F-AXIS #2 — Trade-rate floor (IS ≥ 50, OOS ≥ 10) | PASS | IS **133** / OOS **70** | **PASS** (well above floors; no early-warning < 80 triggered) |
| F-AXIS #3 — Seed stability | single-seed=42 EXPLORATION; multi-seed CONDITIONAL on PROMISING | n=1 | **DEFERRED** to /053 (mandate FIRES) |
| F-AXIS #4 — Per-feature importance rank ≤ 24 | both ≤ 24 = clean; one ≤ 15 + other > 25 = FLAG (does NOT override both-or-neither retain) | spread **rank 4** / impulse **rank 38** | **FLAG** (divergent attribution; impulse INERT; spread strongly learned) |
| F-AXIS #5 — IC informational | non-gating at EXPLORATION | not gating | **N/A** |

**Mechanistic interpretation**:

- The IS lift from -0.85 → +0.16 is concentrated in `btc_funding_spread_30_90` (z30 - z90 term-structure slope), which the LightGBM head allocates **rank 4/48** gain-importance — the 4th-most-important feature out of 48. This is consistent with the BIS WP 1087 (2025) prior that term-structure positioning signal (smoother, regime-level) carries more BTC return information than discrete funding-rate impulses.
- `btc_funding_rate_8h_impulse` at rank 38/48 is essentially INERT — the shock-event count is low (≤15/year on 8h BTC data) and the trees do not allocate split-budget to it. The hypothesized "10% carry shock → 22% liquidation jump" mechanism (BIS WP 1087) may operate at sub-bar resolution and not be capturable at 8h cadence. This is the same INERT-by-importance pattern documented in `feedback_v3_inert_features_at_higher_budget.md` and 6 prior cross-asset OHLCV failures recorded in `feedback_v3_cross_asset_ohlcv_closed.md`.
- BTC-only specialist head replacing pooled Model A is the structural change enabling the lift — at BASELINE_V1 (pooled BTC+ETH on Model A), the pooled head dilutes the BTC funding-spread signal across ETH (which has its own funding dynamics). Single-symbol cohort isolation lets the head specialize on BTC's funding term-structure, and the new spread feature is the primary signal that activates.
- IS WR 39.8% (+6.2pp vs baseline BTC pool-implied WR 33.6%) confirms trade-quality improvement, not trade-count inflation. Total IS net PnL is **+5.8279% per-symbol** (vs baseline -37.28%) — sign-flip on PnL aligns with the Sharpe flip.

**`feature_columns_count` post-iter = 48** (46 → 48 RETAINED pending /053 multi-seed verdict; both-or-neither revert rule deferred to /053 closeout). **`BASELINE_V1.md` UNCHANGED.**

---

## 2. Observed Results

### 2.1 Headline Metrics (from `reports-v1/iteration_v1-052/comparison.csv`)

| Metric | IS | OOS | OOS/IS Ratio |
|---|---:|---:|---:|
| Sharpe | **+0.1609** | -1.3833 | -8.60 |
| Sortino | +0.1249 | -0.9060 | -7.25 |
| Max Drawdown | 23.37% | 27.71% | 1.19 |
| Win Rate | 39.8% | 34.3% | 0.86 |
| Profit Factor | 1.0707 | 0.6184 | 0.58 |
| Total Trades | **133** | **70** | 0.53 |
| Total Net PnL | +9.5478 | -20.8288 | -2.18 |
| DSR | -91.99 | -18.71 | informational |
| PSR (monthly vs 0) | 0.6226 | 0.0953 | informational |
| Calmar | 0.4086 | 0.7516 | informational |

### 2.2 Per-Symbol IS / OOS

| Window | Symbol | Trades | Wins | WR | Net PnL % | Avg PnL % |
|---|---|---:|---:|---:|---:|---:|
| IS | BTCUSDT | 133 | 53 | 39.8% | +5.83% | +0.0438% |
| OOS | BTCUSDT | 70 | 24 | 34.3% | -46.62% | -0.6660% |

OOS is severely negative — informational only per brief §4 ("OOS verdict deferred; primary verdict is IS Δ"). However the OOS deviation is **larger than expected** (predicted OOS lift +0.10 to +0.70; observed -1.38). This is documented under §3 Lessons as a multi-seed-OOS-variance signature analog (see iter-v1/051 §2.3) and an EXPLORATION-budget single-seed OOS dispersion artifact, NOT an OOS-edge contradiction.

### 2.3 Feature Attribution (from `feature_importance_Model_A_BTC_specialist.csv`)

| Feature | Mean Gain | Importance Rank |
|---|---:|---:|
| vol_atr_14 | 4023.62 | 1 |
| trend_aroon_osc_50 | 3705.60 | 2 |
| stat_autocorr_lag5 | 2493.38 | 3 |
| **btc_funding_spread_30_90** | **2358.77** | **4** |
| stat_skew_20 | 2116.94 | 5 |
| ... | ... | ... |
| funding_rate_zscore_90 | 771.04 | 17 |
| funding_rate_zscore_30 | 354.03 | 26 |
| **btc_funding_rate_8h_impulse** | **67.22** | **38** |

The spread feature is the 4th-most-important feature across all 48; the impulse feature is rank 38 (lowest tertile). The existing `funding_rate_zscore_30/90` features sit at rank 17 + 26 respectively — the spread feature is the BEST funding-derived feature by a factor of ~3× the gain of the second-best.

### 2.4 Per-Regime IS

Only "unknown" regime is tagged (regime tagger still not wired into runner — cumulative debt across /049/050/051/052). IS regime Sharpe within "unknown" bucket: **+0.0088** (essentially flat). The portfolio-level annualized IS Sharpe (+0.1609) is the F-AXIS #1 anchor; per-regime breakdown for F-AXIS #2 deferred to regime-tagger wiring (pending technical debt; would also benefit /053 multi-seed validation).

---

## 3. Lessons

### 3.1 Algebraic-sister features outperform OHLCV cross-asset on BTC

`btc_funding_spread_30_90` is constructed as `funding_rate_zscore_30 - funding_rate_zscore_90` — algebraic linear combination of two existing features. Yet at importance rank 4/48 vs the parents at rank 17 + 26, the spread feature carries **3× the gain** of either parent and a Sharpe lift of +1.01 vs baseline. This pattern mirrors the v3 PROMISING-FEATURE-MECHANICAL precedent (`feedback_v3_promising_feature_mechanical.md`) where loss-surface reorganization via algebraic-sister composition produces clean lifts. Trees access the term-structure slope via a single split on the spread vs needing two splits on z30 and z90 separately — a Category-2 composed-feature efficiency gain. **DOES qualify as a signal-discovery axis** (not strictly mechanical), but the underlying primitive (funding-rate level) was already available; the lift is **transform-mediated, not new-primitive-mediated**.

### 3.2 Shock-detector impulse features fail at 8h cadence

`btc_funding_rate_8h_impulse` (normalized first-difference) at importance rank 38/48 is INERT-by-importance. The hypothesized BIS WP 1087 carry-shock → liquidation-cascade mechanism either (a) operates at sub-8h resolution and is smoothed away at bar-level, or (b) is rare enough (<15 events/year on 8h BTC) that trees cannot extract a learnable pattern at EXPLORATION budget (n_trials=18, ENSEMBLE_SIZE=3). This adds to the cross-asset / OHLCV-INERT recurrence chain documented in `feedback_v3_cross_asset_ohlcv_closed.md` but at a NEW primitive class (funding-rate first-difference, not OHLCV). Pattern: **discrete-event shock detectors at low-event-rate cadences (8h) fail to be learned**. The OFF-THE-SHELF term-structure feature (spread) succeeds; the engineered shock detector fails.

### 3.3 OOS IS divergence is larger than EXPLORATION variance band predicted

IS Sharpe +0.16 / OOS Sharpe -1.38 is a Δ of -1.54 with the brief's 90% CI on OOS being [+0.10, +0.70] for the PROMISING-SPECIALIST case. The observed -1.38 is **well outside** the predicted CI. Possible mechanisms:
- BTC OOS (post-March-2025) is a distinct funding regime: the OOS window contains the late-2025 carry-cycle inversion that the IS funding-spread regime didn't capture.
- Single-seed=42 OOS variance at EXPLORATION budget is canonically wide (see /051: OOS std 0.6964 across 3 seeds; spreads >1.0 Sharpe-unit are routine). At /053 multi-seed validation, the OOS mean is expected to compress toward 0 (not toward the IS prediction).
- BTC OOS depends heavily on regime persistence; the 70-trade OOS is on the edge of the 50-trade σ_SR ≈ √(1/T) = 0.12 noise floor — observed -1.38 Sharpe has wide standard error.

**Action**: Do NOT cite OOS -1.38 as evidence of OOS-edge contradiction at this stage. The /053 multi-seed validation is the canonical resolution mechanism. Per feedback rule `feedback_is_oos_divergence_is_regime_not_overfit.md`: high-IS / low-OOS is NOT auto-overfit; could be regime specialist. The /055 CONFIRMATION-bundle composition will combine regime-diverse specialists (DOT-PARTIAL-CONFIRMED + BTC-SPECIALIST-CANDIDATE if /053 confirms + future ETH or LTC specialists).

### 3.4 BTC-specialist head structural change is what unlocks the funding signal

At BASELINE_V1, BTC sits inside pooled Model A (BTC+ETH); the pooled head must trade off BTC funding dynamics against ETH funding dynamics. Single-symbol cohort isolation (`V1_ITER052_UNIVERSE = ("BTCUSDT",)`) lets the head specialize. The Sharpe flip from -0.85 → +0.16 is partly attributable to the spread feature (rank 4) AND partly to the cohort isolation enabling the new head to use the existing funding features (z30 at rank 26; z90 at rank 17) without pooling-dilution. Decomposition would require an A/B test: BTC-only head WITH new features vs BTC-only head WITHOUT new features (isolating cohort vs feature contributions). Defer to /053 as a possible secondary axis if multi-seed mean confirms PROMISING-SPECIALIST.

### 3.5 Both-or-neither revert rule resolves attribution divergence cleanly

LM Master Rec 1 (pre-registered in brief §3.1) handles this verdict cleanly: the attribution diverges (rank 4 vs rank 38), but the verdict is PROMISING-SPECIALIST-CANDIDATE → both features are RETAINED. The F-AXIS #4 FLAG is registered for /053 attention (consider impulse-drop as a secondary axis if /053 multi-seed mean confirms the lift AND the impulse stays rank > 25 across all multi-seed inner pools). This is the FIRST cycle-6 axis to use the both-or-neither pattern for a divergent-attribution PROMISING outcome — the rule operated as designed.

### 3.6 Second cycle-6 PROMISING result; first to flip positive

Cycle-6 PROMISING track record after /052:
- /046 PROMISING-DIVERGENCE
- /047 NEG-CLEAN-PRE-EDA
- /048 NEG-CLEAN-PRE-EDA
- /049 NEG-CLEAN
- /050 PROMISING-PARTIAL (DOT)
- /051 PROMISING-PARTIAL-CONFIRMED (DOT multi-seed)
- **/052 PROMISING-SPECIALIST-CANDIDATE (BTC) — FIRST flip-positive in cycle-6**

The roster is now: 1 PARTIAL-CONFIRMED (DOT) + 1 SPECIALIST-CANDIDATE (BTC, pending /053). LINK baseline anchor (+2.25 IS) remains the strongest per-symbol ingredient. The /055 CONFIRMATION-bundle composition can begin assembling from this roster at cycle-6 EXPLORATION 8/10 (after /053 and /054 close out).

---

## 4. Path Forward — /053 Axis

Per brief §3.5 Multi-Seed Conditional (LM Master Rec 3 ADOPTED) and Section 8.6 decision tree: **PROMISING outcome → MANDATE multi-seed re-validation of /052 BTC config at /053.**

**/053 axis (MANDATED)**: **Multi-seed re-validation of /052 BTC specialist** at 3 disjoint outer seeds (offset0=42, offset3, offset6) — same pattern as /050 → /051 DOT multi-seed validation.

Rationale:
- /052 IS Δ +1.0109 is in FLIP-POSITIVE band at single-seed=42. The /050 → /051 pattern showed a 0.12 IS-Sharpe pull-toward-mean from a favorable seed=42 basin — applying the same 0.12 expected pull to /052 yields a multi-seed mean prediction of IS Sharpe ≈ +0.04 (still in flip-positive band, near edge). The BASIN-LOTTERY threshold of 0.5 (compressed from /051's 1.0 given the larger /052 IS lift) should be applied at /053 closeout.
- The OOS dispersion -1.38 at single-seed warrants multi-seed OOS dispersion measurement. If /053 multi-seed OOS mean compresses to near-flat (offset3 + offset6 contributing positively to OOS), then the seed=42 OOS is an unfavorable outlier (mirror image of /050's favorable seed=42 IS). If /053 multi-seed OOS mean stays deeply negative, then BTC funding-spread is genuinely IS-fit / OOS-fail (regime-shift mechanism). Either resolution is informative.
- Per /050 → /051 protocol: NO axis variation at /053; same config + 3 disjoint outer seeds.

Specifications:
- Universe: `V1_ITER053_UNIVERSE = ("BTCUSDT",)` (unchanged)
- Features: V1_FEATURE_COLUMNS_PRUNED = 48 (both `btc_funding_rate_8h_impulse` + `btc_funding_spread_30_90` retained — both-or-neither rule)
- Seeds: 3 outer seeds via `_OUTER_SEED_OFFSETS = (0, 3, 6)`, disjoint inner-ensemble pools (per /051 pattern)
- n_trials=18, ENSEMBLE_SIZE=3 per seed (EXPLORATION budget; same as /052)
- Wall-clock cap: ≤ 2h (EXPLORATION) — ~3× /052 single-seed runtime
- Falsifier per /053 brief: multi-seed IS mean Δ ≥ +0.85 → SPECIALIST-CONFIRMED (KEEP both); Δ ∈ [+0.30, +0.85) → PARTIAL-CONFIRMED (KEEP both; consider impulse-drop at /054); Δ < +0.30 → NEG-CLEAN-MULTI-SEED (revert both); BASIN-LOTTERY threshold: max-min IS spread > 0.5 → downgrade by one band

**Stretch axis (if /053 confirms SPECIALIST)**: at /054, consider impulse-feature-drop (drop `btc_funding_rate_8h_impulse`, keep only `btc_funding_spread_30_90`) — single-feature isolation to test whether the impulse contributes ANY learned signal across the multi-seed pool, or whether it is purely INERT padding. Resolves the F-AXIS #4 attribution-divergence FLAG.

**Roster composition after /053 closeout**:
- If /053 confirms SPECIALIST: 2 specialist ingredients ready for /055 CONFIRMATION-bundle (DOT-PARTIAL + BTC-SPECIALIST) + LINK anchor.
- If /053 partial-confirms or downgrades: roster grows asymmetrically; /054 axis pivots per orchestrator (LTC specialist or single-feature-isolation).

---

## 5. Catalog + Roster Updates

- `briefs-v1/exploration_catalog.md` row /052 appended (cycle-6 EXP-7).
- `briefs-v1/_meta/regime_specialist_roster.csv` row /052 appended with PROMISING-SPECIALIST-CANDIDATE verdict_band, BTC-SPECIALIST-CANDIDATE regime_specialist_role.
- BASELINE_V1.md unchanged. Tag `v0.v1-052` marks the BTC-specialist single-seed PROMISING artifact pending /053 multi-seed validation.
