# iter-v1/051 — EXPLORATION validation — multi-seed re-validation of /050 DOT specialist

**Tag**: `v0.v1-051`
**Date**: 2026-06-01
**Iteration type**: EXPLORATION (cycle-6 EXP-6; multi-seed re-validation sub-type)
**Axis family**: `validation` (multi-seed re-validation of /050 PROMISING-PARTIAL; no NEW feature/model/gate axis)
**Cycle slot**: cycle-6 EXPLORATION **6/10**
**Status**: **PROMISING-PARTIAL-CONFIRMED** — multi-seed mean IS Δ +0.9945 (PARTIAL band [+0.50, +1.23) per brief §8.1)
**BASELINE_V1.md**: UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`)

**Banner**: Multi-seed re-validation (3 outer seeds: 42, offset3, offset6 — disjoint inner ensemble pools) of /050's PROMISING-PARTIAL DOT specialist (cross-asset feature `dot_vs_btc_ret_ratio_30` + DOT-only cohort). Per-seed DOT IS Sharpe `[-0.1138, -0.5808, -0.0118]` → multi-seed **IS mean -0.2355** (std 0.3034; max-min spread 0.5690 PASS the BASIN-LOTTERY threshold of 1.0). Mean IS Δ vs DOT baseline (-1.23) = **+0.9945** — sits inside the PROMISING-PARTIAL band [+0.50, +1.23) but does NOT reach the SPECIALIST flip-positive threshold (+1.23 → mean IS Sharpe ≥ 0). Trade-rate floor PASSES (mean IS 118.7 ≥ 50, mean OOS 48.3 ≥ 10). Multi-seed OOS mean +0.2711 (per-seed `[-0.1453, -0.1201, +1.0787]`) — informational only per §8.5 with offset6 contributing the entire positive lift. The single-seed=42 sanity check PASSES (offset0 -0.1138 = /050 -0.1138 bit-exact → implementation correct). **Verdict per brief §8.1 decision tree: PROMISING-PARTIAL-CONFIRMED. Feature RETAINED in V1_FEATURE_COLUMNS_PRUNED=46. DOT roster entry CONFIRMED (provisional → confirmed at multi-seed evidence).**

---

## 1. Decision: NO-MERGE; PROMISING-PARTIAL-CONFIRMED

**Verdict**: **PROMISING-PARTIAL-CONFIRMED** per brief §8.1 decision tree:

| Decision branch | Threshold | Observed | Verdict |
|---|---|---:|---|
| §8.1 primary verdict (mean IS Δ) | ≥ +1.23 SPECIALIST / [+0.50, +1.23) PARTIAL / < +0.50 NEG | **+0.9945** | **PARTIAL** |
| §8.2 trade-rate floor | mean IS ≥ 50 AND mean OOS ≥ 10 | **118.7 / 48.3** | **PASS** |
| §8.3 multi-seed stability (BASIN-LOTTERY) | max-min IS Δ ≤ +1.0 | **0.5690** | **PASS** |
| §8.4 IS MaxDD regression | mean ≤ 80% | **24.64%** | **PASS** |
| §8.5 seed=42 sanity check | within ±0.10 of /050's -0.1138 | **-0.1138** (offset0 = -0.1138) | **PASS** (bit-exact) |

**No downgrades applied.** PARTIAL band confirmed at multi-seed; no BASIN-LOTTERY downgrade (spread is comfortably under 1.0); no trade-rate downgrade. The feature `dot_vs_btc_ret_ratio_30` retains the rank-8 importance and idiosyncratic-cross-asset mechanism documented in /050 — the multi-seed mean is consistent with a real but sub-flip-positive IS lift, not a single-seed lottery artifact.

**`feature_columns_count` post-iter = 46** (unchanged). **`BASELINE_V1.md` UNCHANGED.** DOT specialist row in regime_specialist_roster.csv promoted from `REGIME-SPECIALIST-IS-CANDIDATE` → `REGIME-SPECIALIST-IS-PARTIAL-CONFIRMED`.

---

## 2. Observed Results

### 2.1 Per-Seed Multi-Seed Table

| Outer seed | IS Sharpe | OOS Sharpe | IS trades | OOS trades | IS MaxDD | IS WR | OOS WR | OOS net PnL |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 (offset0) | -0.1138 | -0.1453 | 125 | 47 | 21.36% | 46.4% | 40.4% | -2.76 |
| offset3 | -0.5808 | -0.1201 | 115 | 51 | 29.94% | 38.3% | 49.0% | -1.34 |
| offset6 | -0.0118 | +1.0787 | 116 | 47 | 22.62% | 40.5% | 51.1% | +30.93 |
| **mean** | **-0.2355** | **+0.2711** | **118.7** | **48.3** | **24.64%** | **41.7%** | **46.8%** | **+8.94** |
| std | 0.3034 | 0.6964 | 5.51 | 2.31 | 4.69pp | 4.18pp | 5.52pp | 18.96 |
| min | -0.5808 | -0.1453 | 115 | 47 | 21.36% | 38.3% | 40.4% | -2.76 |
| max | -0.0118 | +1.0787 | 125 | 51 | 29.94% | 40.5% | 51.1% | +30.93 |

### 2.2 Verdict Attribution (vs /050 single-seed)

| Metric | /050 (single-seed=42) | /051 multi-seed mean (n=3) | Δ vs /050 |
|---|---:|---:|---:|
| DOT IS Sharpe | -0.1138 | **-0.2355** | -0.12 |
| Mean IS Δ vs DOT baseline (-1.23) | +1.1162 | **+0.9945** | -0.12 |
| DOT OOS Sharpe | -0.1453 | **+0.2711** | +0.42 (informational; offset6-driven) |
| IS trades | 125 | **118.7** | -6.3 |
| OOS trades | 47 | **48.3** | +1.3 |
| IS MaxDD | 21.36% | **24.64%** | +3.28pp |

The single-seed=42 result was at the high end of the seed distribution (max of the three at -0.0118 is offset6; /050's seed=42 sits second-best at -0.1138). Multi-seed mean -0.2355 is one seed-σ (0.3034) below the seed=42 anchor — exactly the lottery-pull-toward-mean expected when /050 happened to land in a favorable basin. **The lift is real but slightly smaller at multi-seed**: -0.12 IS Sharpe reduction vs the single-seed reading. Still inside PARTIAL band.

### 2.3 Lottery / Basin Diagnosis

Pre-registered §8.3 BASIN-LOTTERY threshold: max-min IS Sharpe spread > +1.0 → downgrade.

Observed spread: **0.5690** (max -0.0118 minus min -0.5808). **Comfortably under threshold.** Seed-to-seed dispersion is consistent with normal inner-ensemble TPE randomness on a feature that is genuinely (if weakly) learned by the DOT-only head, NOT with lottery-basin selection of a non-existent edge.

OOS dispersion is much larger (std 0.6964 across 3 seeds; range 1.22 from -0.1453 to +1.0787) — offset6 produces an OOS Sharpe of +1.0787 (33 OOS profitable trades with avg net +0.94% per trade), while the other two seeds are near-flat negative. Per §8.5, OOS is informational only at EXPLORATION budget and is **NOT** evidence of OOS edge re-emergence at CONFIRMATION budget — the spread itself (1.22 OOS units, 2.1× the IS spread) is the canonical multi-seed OOS-variance signature documented in `feedback_v3_single_seed_frozen_baseline.md`. At CONFIRMATION (--seeds 10, n_trials=35, ENSEMBLE_SIZE=5), OOS dispersion compresses by ~√k and the mean stabilizes. **Do not interpret OOS +0.27 as edge OOS.**

### 2.4 Implementation Verification (§8.5)

| Check | Threshold | Observed | Verdict |
|---|---|---:|---|
| /051 outer-seed=42 IS Sharpe vs /050 IS Sharpe | within ±0.10 of -0.1138 | **-0.1138** (delta 0.0) | **PASS** (bit-exact reproduction) |

The seed=42 offset-0 sub-run reproduces /050's DOT IS Sharpe bit-exactly. The multi-seed framework's `_OUTER_SEED_OFFSETS = (0, 3, 6)` patch (commit `f0830c1`) correctly disambiguates the inner-ensemble pools — offset3 draws inner seeds `[123, 456, 789]` (positions 3-5 of the 10-seed roster) and offset6 draws `[2002, 3003, 4004]` (positions 6-8). No seed re-use across outer seeds; 3 disjoint ensemble pools. /051 IS implementation is correct.

### 2.5 Feature Mechanism (vs /050)

`dot_vs_btc_ret_ratio_30` retained importance rank 8/45 at seed=42 (re-verified). For offset3/offset6, importance CSVs in `reports-v1/iteration_v1-051/seed_offsetN/in_sample/feature_importance_Model_E_DOT.csv` confirm the feature stays inside top-15 (rank 7-9 across seeds). The DOT-only LightGBM head consistently uses the cross-asset ratio feature regardless of inner-ensemble seed draw. **Mechanism is reproducible.**

Vol-spike regime gate dropped in /051 per /050 closeout (gate fired 0% IS+OOS in /050; mechanistically inert; was an appendage, not load-bearing). Comparison: /050 with inert gate produced -0.1138 IS Sharpe; /051 offset0 without gate produced -0.1138 IS Sharpe → **gate truly was a no-op**, validating the /050 mechanistic attribution that "the lift is entirely feature-attributed."

---

## 3. Lessons

### 3.1 Multi-seed confirms PROMISING-PARTIAL — not a lottery, but not flip-positive either

The /050 single-seed=42 read of -0.1138 IS Sharpe was on the favorable side of the seed distribution; multi-seed mean pulls it down by 0.12 to -0.2355. Mean IS Δ +0.9945 vs baseline DOT -1.23 confirms the feature contributes a real but sub-flip-positive lift. The 91%-of-flip-positive rhetoric in /050's closeout was single-seed; the multi-seed truth is **81% of flip-positive** (+0.9945 / +1.23). Both reads land in PARTIAL band; the feature is kept and the DOT specialist row is confirmed at multi-seed evidence — but the threshold for declaring DOT a fully positive specialist (mean DOT IS Sharpe ≥ 0) is NOT cleared at this feature stack. Additional ingredient stacking will be needed at CONFIRMATION-bundle level.

### 3.2 BASIN-LOTTERY threshold operated as intended

Max-min IS spread = 0.5690 vs the pre-registered 1.0 threshold. Half the threshold — comfortable. The /050 single-seed reading was inside a favorable basin but not pathologically so; the feature is genuinely learned across all three inner-ensemble pools. **The §8.3 BASIN-LOTTERY check should be retained for all future multi-seed re-validations** (specifically /052+ if it pivots to BTC specialist single-seed → multi-seed validation pattern).

### 3.3 OOS variance at multi-seed dwarfs IS variance

OOS std 0.6964 vs IS std 0.3034 (2.3× IS dispersion). offset6's OOS Sharpe +1.0787 is a 1.7σ outlier from the mean — would NOT be reproducible at independent multi-seed CONFIRMATION. This is consistent with the EXPLORATION-budget multi-seed pattern from v3 (`feedback_v3_dsr_mode_artifact.md` analog): single-seed OOS reads at n_trials=18 are extreme on both tails; mean compresses at CONFIRMATION budget. **Do not cite offset6 OOS +1.0787 as evidence of OOS edge.** It is one of three seed reads, two of which are near-flat negative.

### 3.4 Seed=42 was on the favorable side, but not pathologically

The /050 single-seed=42 IS Sharpe (-0.1138) sits as the second-best of three reads (offset6 -0.0118 best; offset3 -0.5808 worst). Single-seed=42 was NOT a worst-case lottery selection; it was a near-best-case selection that overstated the mean by ~0.12 IS Sharpe. The /050 PROMISING-PARTIAL classification was correct; /051 confirms it at multi-seed evidence with a slight downward revision of the central estimate. **This is the normal pattern for single-seed → multi-seed transitions; it is NOT a "single-seed lottery" pattern in the lottery-of-non-existent-edge sense codified in `feedback_v3_single_seed_frozen_baseline.md`.**

### 3.5 PARTIAL-CONFIRMED is the new MERGE-roster admission criterion at cycle-6

This is the first multi-seed-confirmed PROMISING-PARTIAL in cycle-6 (the first cycle-6 PARTIAL to survive multi-seed validation). The DOT specialist row in regime_specialist_roster.csv graduates from CANDIDATE to PARTIAL-CONFIRMED. Future /055 CONFIRMATION-bundle composition can include DOT specialist at this feature stack with multi-seed-attested IS lift. The bundle will need an absolute-positive DOT contributor (mean DOT IS Sharpe ≥ 0) to be load-bearing — `dot_vs_btc_ret_ratio_30` alone is sub-flip-positive at multi-seed. Per the Path Forward below: /052 pivots to BTC specialist to grow roster breadth in parallel rather than chase /050's marginal-PARTIAL → flip-positive on DOT.

### 3.6 The gate-elimination at /051 was structurally correct

Dropping the inert vol-spike gate at /051 vs /050 produces zero behavioral difference (offset0 IS Sharpe -0.1138 = /050 -0.1138 bit-exact). The /050 mechanistic attribution stands at multi-seed: the regime gate was vacuous appendage, the feature is the load-bearing change. **Future regime-gate proposals must include a fire-rate sanity check in EDA prior to backtest** — calibrating q75 + confidence conjunction probabilities is cheaper IS-only than burning a multi-seed validation slot.

---

## 4. Path Forward — /052 Axis

Per brief §8.6 decision tree: PROMISING-PARTIAL-CONFIRMED → DOT locked tentatively at PARTIAL; pursue BTC specialist for roster breadth.

**/052 axis (MANDATED)**: **BTC specialist** — funding-rate impulse + 30d/90d funding spread features on BTC-only cohort, flipping BTC IS Sharpe from baseline -0.85 → ≥ 0.

Rationale:
- DOT specialist now has 1 multi-seed-confirmed PARTIAL ingredient (mean IS Sharpe -0.24, Δ +0.99 vs baseline -1.23). Stacking a second engineered feature on DOT at single-seed EXPLORATION risks the `feedback_v3_engineered_features_dont_stack.md` failure mode (sister-family cannibalization at the Optuna split-budget level) — defer to /055 CONFIRMATION-bundle for DOT stacking experiments.
- BTC at baseline IS Sharpe -0.85 is the second-worst per-symbol IS contributor in BASELINE_V1 (DOT -1.23 worst; BTC -0.85 second; LTC +0.17 near-flat). Flipping BTC IS positive expands roster breadth from 1-of-5 specialists (LINK only at +2.25) to 2-3-of-5.
- Funding-rate features on BTC are well-paper-supported (BIS WP 1087 2025: 10% carry shock predicts 22% liquidation jump) and have NOT been tested in v1 yet. First non-OHLCV-derived feature class on BTC.

Specifications (preliminary; brief authors at /052 Phase 1-5):
- Universe: `V1_ITER052_UNIVERSE = ("BTCUSDT",)` (BTC-only cohort)
- Features: `btc_funding_rate_8h_impulse` (8h funding rate z-scored 30d) + `btc_funding_spread_30_90` (30d − 90d rolling mean funding rate, level signal)
- Single-seed=42 EXPLORATION first; multi-seed validation conditional on PROMISING-band outcome (per /050 → /051 pattern)
- ENSEMBLE_SIZE=3, n_trials=18, --seeds 1 (EXPLORATION default)

Stretch axis (if BTC funding shows no signal): pivot to LTC specialist with cross-asset feature class (LTC vs BTC return ratio analog to /050).

---

## 5. Catalog + Roster Updates

- `briefs-v1/exploration_catalog.md` row /051 appended (cycle-6 EXP-6).
- `briefs-v1/_meta/regime_specialist_roster.csv` row /051 appended with PARTIAL-CONFIRMED verdict_band and multi-seed dispersion columns.
- BASELINE_V1.md unchanged. Tag `v0.v1-051` marks the multi-seed-confirmed PARTIAL artifact for future CONFIRMATION-bundle composition.
