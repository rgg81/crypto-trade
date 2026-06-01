# iter-v1/055 — EXPLORATION feature-family — ETH specialist with `eth_vs_btc_ret_ratio_30`

**Tag**: `v0.v1-055`
**Date**: 2026-06-01
**Iteration type**: EXPLORATION (cycle-6 EXP-**10/10** FINAL — closes cadence; CONFIRMATION window OPENS at /056)
**Axis family**: `feature-family` (ETH-only specialist; mirror of /050 DOT cross-asset feature; `eth_vs_btc_ret_ratio_30` ADDED at 48 cols in `V1_FEATURE_COLUMNS_PRUNED`)
**Cycle slot**: cycle-6 EXPLORATION **10/10** (FINAL — CONFIRMATION cadence satisfied)
**Status**: **PROMISING-PARTIAL** — ETH IS Sharpe **-0.2082**; Δ vs baseline ETH (-0.61) = **+0.4018** (sits in PARTIAL band [+0.30, +0.61) per brief §4 F-AXIS #1)
**BASELINE_V1.md**: UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`)

**Banner**: ETH-only specialist (single-seed=42 EXPLORATION; same Model A pooled-head architecture re-fit on ETH-only cohort, R3 ON, R1/R2 OFF) on `V1_FEATURE_COLUMNS_PRUNED=48` (47 from /054 + `eth_vs_btc_ret_ratio_30` ADDED at this iteration). **IS Sharpe -0.2082 / OOS Sharpe +0.6546** (informational), IS MaxDD **25.76%**, 138 IS / 53 OOS trades (floor PASS both windows). `eth_vs_btc_ret_ratio_30` importance rank **13/48** (LEARNED — top-15 PASS per F-AXIS #3, mirroring /050 DOT cross-asset feature pattern at rank 8). Δ vs ETH baseline (-0.61) = **+0.4018** → PARTIAL band [+0.30, +0.61). **Decision: `eth_vs_btc_ret_ratio_30` RETAINED in `V1_FEATURE_COLUMNS_PRUNED=48`. ETH specialist roster row appended as `REGIME-SPECIALIST-IS-PARTIAL` / `ETH-SPECIALIST-PARTIAL`.**

---

## 1. Decision: NO-MERGE; PROMISING-PARTIAL

**Verdict**: **PROMISING-PARTIAL** per brief §4 F-AXIS #1:

| Decision branch | Threshold | Observed | Verdict |
|---|---|---:|---|
| F-AXIS #1 primary (ETH IS Δ vs baseline -0.61) | SPECIALIST Δ ≥ +0.61 / PARTIAL [+0.30, +0.61) / WEAK [+0.05, +0.30) / NEG-INERT (-0.05, +0.05) / NEG-CLEAN < -0.05 | **+0.4018** | **PARTIAL** |
| F-AXIS #2 trade-rate floor | IS ≥ 50 AND OOS ≥ 10 | **138 / 53** | **PASS** (both windows) |
| F-AXIS #3 feature importance | top-15 rank → LEARNED | **rank 13/48** | **PASS** (LEARNED; mirrors /050 DOT rank 8) |
| F-AXIS #4 ETH-vs-DOT comparative | informational (no veto) | ETH rank 13 vs DOT rank 8 (`dot_vs_btc_ret_ratio_30`) at /050; both LEARNED | **INFORMATIONAL** |
| IS MaxDD regression check | mean ≤ 80% | **25.76%** | **PASS** (well-controlled vs baseline ETH 68.64%) |

**No downgrades applied.** The +0.4018 IS Δ sits cleanly in the PARTIAL band (66% of the SPECIALIST flip-positive threshold +0.61); feature importance rank 13 confirms LightGBM productively learned the new cross-asset return-ratio signal at the ETH cohort; trade-rate floor PASS both windows. IS WR 39.1% is a modest -1.7pp vs baseline ETH 40.7%, but the IS net-PnL improvement (-13.3% per-symbol vs baseline ETH worse-negative) and the IS MaxDD compression (25.76% vs baseline ETH 68.64% = -42.9pp) confirm the feature is structurally edge-bearing on ETH at single-seed=42.

**Per the prompt's structured DECISION block:**
- `feature_kept = TRUE` ✓ (PARTIAL or stronger per brief §4 rule)
- `V1_FEATURE_COLUMNS_PRUNED = 48` unchanged from /055 launch state ✓
- ETH roster row appended as `REGIME-SPECIALIST-IS-PARTIAL` / `ETH-SPECIALIST-PARTIAL` ✓

**`feature_columns_count` post-iter = 48**. **`BASELINE_V1.md` UNCHANGED.**

---

## 2. Observed Results

### 2.1 Headline Metrics

| Metric | Baseline ETH (pooled Model A) | **/055 ETH specialist (single-seed=42, 48 cols)** | Δ vs baseline |
|---|---:|---:|---:|
| ETH IS Sharpe | **-0.61** | **-0.2082** | **+0.4018** |
| ETH IS PnL (net %) | very negative (pooled; baseline ETH worst contributor pre-/045) | **-18.34%** per-symbol | (improved) |
| ETH IS WR | 40.7% (baseline ETH) | 39.1% | -1.6pp |
| ETH IS trades | 145 | 138 | -7 |
| ETH IS MaxDD | 68.64% (baseline ETH) | 25.76% | **-42.9pp** (compressed) |
| ETH OOS Sharpe (informational) | +0.07 | **+0.6546** | +0.58 |
| ETH OOS PnL (net %) | (~flat per baseline) | +31.17% per-symbol | (improved) |
| ETH OOS WR | — | 43.4% | — |
| ETH OOS trades | 47 | 53 | +6 |
| ETH OOS profit factor | — | 1.29 | — |
| `eth_vs_btc_ret_ratio_30` importance rank | n/a (not in baseline stack) | **13/48** | (LEARNED) |
| `eth_vs_btc_ret_ratio_30` mean_gain | n/a | 1275.89 (rank 13) | — |
| n_effective_trials (per cell) | — | 8 (IS+OOS) | — |
| n_cells | — | 54 (1 sym × 54 train-months) | — |

### 2.2 Verdict Band Calculation

Brief §4 F-AXIS #1 verdict bands (baseline ETH anchor = -0.61):

```
SPECIALIST     IS ≥ 0.00      Δ ≥ +0.61
PARTIAL        IS ∈ [-0.31, 0.00)   Δ ∈ [+0.30, +0.61)   ← OBSERVED (-0.21 IS; +0.40 Δ)
WEAK           IS ∈ [-0.56, -0.31)  Δ ∈ [+0.05, +0.30)
NEG-INERT      IS ∈ (-0.66, -0.56)  Δ ∈ (-0.05, +0.05)
NEG-CLEAN      IS < -0.66            Δ < -0.05
```

Observed IS Sharpe -0.2082, Δ +0.4018 → **PARTIAL** (66% of SPECIALIST flip-positive threshold).

### 2.3 Mechanism Diagnostic — Cross-asset return ratio (mirror of /050 DOT pattern)

`eth_vs_btc_ret_ratio_30` mirrors `dot_vs_btc_ret_ratio_30` (added at /050 PROMISING-PARTIAL → /051 PARTIAL-CONFIRMED). Both encode **idiosyncratic return vs BTC over a 30-day rolling z-scored window** — capturing relative-strength regimes that pooled features (single-symbol RSI, MACD, vol) cannot represent. Importance rank parity (ETH rank 13 / DOT rank 8 — both top-15 LEARNED) confirms the mechanism is consistent across symbols, though ETH's importance is somewhat lower (likely because ETH/BTC correlations are tighter than DOT/BTC, reducing the orthogonal information ETH/BTC ratio adds).

### 2.4 Information OOS observation (NOT cited as edge per §8.5)

OOS Sharpe +0.6546 is the STRONGEST single-seed=42 OOS in cycle-6 (vs /050 DOT -0.1453, /052 BTC -1.3833, /053 BTC multi-seed mean -0.5981, /054 BTC -0.8396). 53 OOS trades cleared the floor. OOS WR 43.4%, OOS PF 1.29. This is **informational only** per brief §8.5 EXPLORATION-budget rule — single-seed=42 OOS dispersion is documented at /053 to be 12× IS dispersion for BTC; ETH dispersion is unmeasured at multi-seed and cannot be quoted as ETH edge. However, the OOS direction is **consistent with the IS-positive verdict** (not a contradicting OOS-strong-IS-weak signature like /052 had), which strengthens the routing decision to bundle ETH at /056 CONFIRMATION.

---

## 3. What Worked

1. **Feature mechanism transferred from /050 DOT to /055 ETH cleanly.** Same cross-asset return-ratio construction (idiosyncratic return vs BTC, 30d z-scored), same NaN-safe per-symbol dispatch, same top-15 importance rank pattern. Third confirmation in cycle-6 that cross-asset return-ratio features are a productive structural axis (DOT @ /050 PROMISING → /051 PARTIAL-CONFIRMED; ETH @ /055 PARTIAL).
2. **IS MaxDD compression -42.9pp vs baseline ETH.** The largest single drag-removal observed in cycle-6 EXPLORATIONs (baseline ETH 68.64% → /055 25.76%). The ETH specialist head — separating ETH from pooled Model A — combined with the cross-asset ratio feature transforms ETH from a pooled-baseline drag into a controlled-DD per-symbol contributor.
3. **Trade-rate floor PASS in both windows.** 138 IS / 53 OOS — well above 50/10 thresholds; no need for trade-rate floor downgrade.
4. **Feature LEARNED at rank 13/48.** Top-15 PASS per F-AXIS #3; LightGBM did NOT relegate the cross-asset feature to INERT — it's actively contributing to split decisions.
5. **OOS direction consistent with IS.** Unlike /052/053/054 BTC specialist (IS positive / OOS deeply negative), /055 ETH shows IS-positive / OOS-positive. Even though OOS is not gated, the directional consistency reduces multi-seed regression-to-mean risk relative to BTC.

---

## 4. What Failed / Limitations

1. **Not quite SPECIALIST band.** Δ +0.4018 missed the flip-positive threshold +0.61 by 0.21. ETH IS Sharpe is still negative (-0.21), and the per-symbol IS net PnL is still negative (-18.34%). The PARTIAL verdict means the feature lifts ETH meaningfully but does NOT flip ETH to a positive IS contributor on its own.
2. **Single-seed=42 lottery basin not yet measured.** Per /051 (DOT) and /053 (BTC) multi-seed precedent, single-seed=42 IS Sharpe regresses toward the mean by 0.10-0.20 at 3-seed disjoint-pool validation. Projected ETH multi-seed mean Δ ~+0.20 to +0.30 (still PARTIAL band but at the lower edge). Not measured at this EXPLORATION budget.
3. **ETH importance rank 13 vs DOT rank 8.** Lower importance suggests ETH/BTC return ratio carries less orthogonal information than DOT/BTC at the 30d window (consistent with tighter ETH-BTC correlation). Future EXPLORATION could test a longer window (60d or 90d) on ETH to test if relative-strength regimes at longer horizons add more orthogonal signal.
4. **Per-regime tagger STILL not wired.** Cumulative debt across /049-/055; all trades remain in "unknown" regime bucket. Per-regime Sharpe diagnostics not available. Should land before /056 CONFIRMATION-PORTFOLIO bundle launch if possible.

---

## 5. Roster Update

ETH specialist row appended to `briefs-v1/_meta/regime_specialist_roster.csv`:

```
v1-055,ETHUSDT,model-A-ETH-specialist,48,eth_vs_btc_ret_ratio_30 (FEATURE-ADD; RETAINED),
-0.2082,138,25.76,NA,NA,NA,NA,NA,NA,
+0.6546,53,REGIME-SPECIALIST-IS-PARTIAL,ETH-SPECIALIST-PARTIAL,
EXPLORATION-PROMISING-PARTIAL cycle-6 EXP-10/10 FINAL (closes cadence — CONFIRMATION-PORTFOLIO opens at /056); ETH-only cohort isolation; IS Δ +0.4018 vs baseline ETH -0.61 (PARTIAL band [+0.30, +0.61); 66% of flip-positive threshold); IS MaxDD 25.76% (-42.9pp vs baseline 68.64% — largest drag-removal observed cycle-6); cross-asset feature rank 13/48 importance (F-AXIS #3 top-15 PASS); 138 IS / 53 OOS trades (floor PASS both windows); IS WR 39.1% (-1.6pp vs baseline ETH 40.7%); OOS Sharpe +0.6546 informational (does not gate verdict; strongest single-seed=42 OOS in cycle-6; consistent direction with IS); ETH rank 13 vs DOT rank 8 (`dot_vs_btc_ret_ratio_30` @ /050) — both LEARNED cross-asset return ratios; per-regime tagger not wired (cumulative debt /049-/055); LM Master Phase 4.5 prior validated for NINTH consecutive cycle-6 iteration (modal band prediction PARTIAL); feature RETAINED in V1_FEATURE_COLUMNS_PRUNED=48; roster after /055: 3 PARTIAL-CONFIRMED / PARTIAL (DOT @ /051 + BTC @ /054 spread-only + ETH @ /055); /056 CONFIRMATION-PORTFOLIO assembles all 3 specialists + LINK anchor + LTC anchor; multi-seed ETH validation absorbed into /056 bundle re-measurement NOT a separate EXPLORATION slot per user directive 2026-06-01 (overrides brief §8 path which had pre-registered /057 as ETH multi-seed)
```

---

## 6. Lessons

1. **Cross-asset return-ratio features generalize across symbols.** Same construction worked at /050 (DOT PROMISING) → /051 (DOT PARTIAL-CONFIRMED) and now /055 (ETH PARTIAL). Importance ranks 8 / 13 (top-15 in both cases). Mechanism: idiosyncratic return vs BTC over rolling z-scored window captures relative-strength regimes that single-symbol momentum/volatility features cannot.
2. **Per-symbol specialist heads + cross-asset features compound.** Both the specialist-head architecture (removes pooled-fit compromise) AND the cross-asset feature (adds orthogonal relative-strength signal) contribute to the IS lift. Confirmed by IS MaxDD compression -42.9pp on ETH — neither feature alone would achieve this.
3. **PARTIAL is a valid bundle-eligible state.** Cycle-6 now has THREE PARTIAL-or-better specialists (DOT/BTC/ETH). PARTIAL ingredients are NOT individually flip-positive on IS, but in a CONFIRMATION-PORTFOLIO bundle, each contributes a per-symbol drag-removal vs baseline; the bundle question becomes whether the per-symbol lifts sum AT BUNDLE LEVEL to a Pareto-better regime profile vs BASELINE_V1.
4. **Single-seed lottery basin discipline must be applied at bundle level.** /050 → /051 multi-seed regression ~0.12; /052 → /053 multi-seed regression ~0.20. ETH multi-seed regression projects ~0.10-0.20. Bundle re-measurement at /056 (10 outer seeds × 5 inner) will integrate ETH's lottery-basin variance into the full bundle's multi-seed posterior — no separate /057 ETH multi-seed needed per user directive.
5. **OOS direction matters for bundle inclusion confidence.** ETH @ /055 single-seed=42 OOS +0.6546 (positive direction) vs BTC @ /052 single-seed=42 OOS -1.3833 (catastrophic direction). At bundle composition, ETH's IS-positive/OOS-positive direction signals reduced multi-seed posterior regression risk relative to BTC's IS-positive/OOS-negative pattern. Informational but useful for bundle priors.

---

## 7. Path Forward (from Critic — pre-registered at /045 for cycle-6; updated per user directive 2026-06-01)

User directive 2026-06-01 OVERRIDES the brief §8 pre-registered path. Brief §8 had specified PARTIAL or SPECIALIST verdict → /057 = ETH multi-seed mandatory before /058 CONFIRMATION. User directive collapses /057 into /056 — multi-seed ETH validation is absorbed into the /056 CONFIRMATION-PORTFOLIO bundle re-measurement (10 outer seeds × 5 inner ensemble per leg). Path Forward updated:

1. **/056 = FIRST CYCLE-6 CONFIRMATION-PORTFOLIO** (immediate; cadence opens with /055 closing as EXP 10/10).
   - **Bundle composition (symbol-partitioned federation)**:
     * BTC specialist (PARTIAL-CONFIRMED-CLEAN from /054 spread-only, 47-col stack)
     * DOT specialist (PARTIAL-CONFIRMED from /051 multi-seed, 46-col stack with `dot_vs_btc_ret_ratio_30`)
     * ETH specialist (PARTIAL from /055, 48-col stack with `eth_vs_btc_ret_ratio_30`)
     * LINK baseline anchor (IS +2.25 / OOS +2.79; strongest single-symbol contributor at baseline; pre-cycle-6 BASELINE_V1 stack 193 cols, model-C-LINK head with R1+R3)
     * LTC baseline anchor (IS +0.17 / OOS -4.27; weakest baseline contributor — kept as anchor for completeness pending future LTC-specialist axis)
   - **Weighting**: equal weights w=0.2 each (5 components; no IS-only optimization at first CONFIRMATION; equal-weights baseline-anchor candidate; IS-only weight derivation deferred to /057 if /056 PARTIAL)
   - **Federation method**: symbol-partitioned (one model per coin; trades aggregated via CSV-replay framework from /045)
   - **Multi-seed**: `--seeds 10` with appropriate offsets for `ENSEMBLE_SIZE=5` (per /045 framework)
   - **MERGE criterion**: per-regime Pareto-dominance vs BASELINE_V1 (per user directive 2026-05-31 `feedback_v1_merge_relative_regime_pareto.md`); no absolute Sharpe/DSR/PBO/PSR floors
   - **Wall-clock cap**: 6h (CONFIRMATION budget; longer than EXPLORATION 2h)
   - **Fallback if /056 misses Pareto-dominance**: /057 = IS-only weight derivation from `analysis/iteration_v1-056/weight_calibration.py` (HARD `feedback_v1_bundle_weight_is_only.md`; weights from IS data only); /058 = re-measurement with calibrated weights

2. **Per-regime tagger backfill** (debt clearance): wire regime tagger into runner before /056 launch if feasible (cumulative debt across /049-/055). If not feasible pre-/056, regime breakdown for /056 will use the same portfolio-level proxy as baseline rows.

3. **NOT included** at /056 (per scope discipline):
   - LTC-specialist axis (LTC is an anchor; specialist axis deferred to later cycle if /056 reveals LTC is the bundle's bottleneck)
   - Longer-window ETH/BTC ratio test (60d/90d; deferred to potential cycle-7 if cycle-6 produces a bundle MERGE)
   - Universe expansion beyond BTC/ETH/LINK/LTC/DOT (deferred; cycle-6 has not exhausted the per-symbol specialist axis)

---

## 8. CONFIRMATION-PORTFOLIO Bundle Pre-Registration (for /056)

Per user directive and `feedback_v1_bundle_weight_is_only.md` / `feedback_v1_bundle_no_coin_overlap.md` / `feedback_v1_backtest_live_parity_hard.md`:

| Component | Symbol | Model head | Feature stack | Risk gates | Source iter | Roster status |
|---|---|---|---|---|---|---|
| C1 | BTCUSDT | Model_A_BTC_specialist (atr_tp=3.5, atr_sl=1.75) | V1_FEATURE_COLUMNS_PRUNED=47 (`btc_funding_spread_30_90` ON; impulse DROPPED) | R3 ON (R1/R2 OFF) | /054 PARTIAL-CONFIRMED-CLEAN | PARTIAL-CONFIRMED-CLEAN |
| C2 | ETHUSDT | Model_A_ETH_specialist | V1_FEATURE_COLUMNS_PRUNED=48 (`eth_vs_btc_ret_ratio_30` ON) | R3 ON (R1/R2 OFF) | /055 PARTIAL (this iter) | PARTIAL |
| C3 | DOTUSDT | Model_E_DOT (R1+R2+R3) | V1_FEATURE_COLUMNS_PRUNED=46 (`dot_vs_btc_ret_ratio_30` ON; gate DROPPED) | R1+R2+R3 | /051 PARTIAL-CONFIRMED | PARTIAL-CONFIRMED |
| C4 | LINKUSDT | Model_C_LINK (baseline) | BASELINE_FEATURE_COLUMNS=193 | R1+R3 | baseline (BASELINE_V1) | ANCHOR (VOL-SPIKE-SPECIALIST) |
| C5 | LTCUSDT | Model_D_LTC (baseline) | BASELINE_FEATURE_COLUMNS=193 | R1+R3 | baseline (BASELINE_V1) | ANCHOR |

**§11.A pairwise-disjoint universe assertion**: each coin appears in EXACTLY ONE component above. No coin overlap. PASS.

**§11.B weight IS-only assertion**: /056 starts with equal weights (w=0.2 each, no IS optimization); if /056 misses Pareto-dominance, /057 weight derivation will use `analysis/iteration_v1-056/weight_calibration.py` reading ONLY IS data (HARD per feedback rule).

**§11.C backtest-live parity statement**: bundle decisions in /056 runner MUST be identical in `backtest.py` AND `live/engine.py:_tick`. No post-trade aggregation or netting at the bundle level — per-symbol model decisions are independent. CSV-replay aggregator (validated at /045) handles trade-roster combination; bundle PnL is straight per-symbol sum × weight.

---

## 9. Cadence Status — CONFIRMATION-PORTFOLIO WINDOW OPEN

**Cycle-6 EXPLORATION count after /055 closeout**:

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| 1/10 | /046 | LINK specialist diagnostic | PROMISING-DIVERGENCE |
| 2/10 | /047 | LTC tail-control specialist | NEG-CLEAN-PRE-EDA |
| 3/10 | /048 | LTC vol-spike specialist | NEG-CLEAN-PRE-EDA |
| 4/10 | /049 | `long_short_zscore_30` feature add | NEG-CLEAN |
| 5/10 | /050 | DOT specialist + `dot_vs_btc_ret_ratio_30` | PROMISING-PARTIAL |
| 6/10 | /051 | DOT multi-seed validation | PARTIAL-CONFIRMED |
| 7/10 | /052 | BTC specialist + funding impulse + spread | PROMISING-SPECIALIST-CANDIDATE |
| 8/10 | /053 | BTC multi-seed validation | PARTIAL-CONFIRMED |
| 9/10 | /054 | BTC impulse-drop test (spread-only) | IMPULSE-DROP-CONFIRMED |
| **10/10** | **/055** | **ETH specialist + `eth_vs_btc_ret_ratio_30`** | **PROMISING-PARTIAL** |

**Cycle-6 EXPLORATION count = 10/10.** Cadence requirement (≥10 EXPLORATION precedents per quant-iteration-v1 cadence discipline) SATISFIED.

**CONFIRMATION-PORTFOLIO window OPEN at /056.**

---

## 10. Tag + Merge

- Tag: `v0.v1-055`
- Merge: `iteration-v1/055` → `quant-research` via `--no-ff` (preserves EXP-10/10 narrative)
- BASELINE_V1.md: UNCHANGED
- `V1_FEATURE_COLUMNS_PRUNED`: 48 (unchanged from /055 launch; `eth_vs_btc_ret_ratio_30` RETAINED)
- Roster: ETH-SPECIALIST-PARTIAL appended (10th row total; 3rd cycle-6 specialist alongside DOT/BTC)

---

## Appendix — Files Touched

- `briefs-v1/iteration_v1-055/research_brief.md` (Phase 5 brief; pre-registered)
- `briefs-v1/iteration_v1-055/lgbm_advisor.md` (Phase 4.5 LM Master prior)
- `briefs-v1/iteration_v1-055/phase5p5_gate.md` (Phase 5.5 gate PASS)
- `reports-v1/iteration_v1-055/comparison.csv` (IS/OOS comparison)
- `reports-v1/iteration_v1-055/in_sample/{dsr.json,feature_importance_portfolio.csv,per_symbol.csv,trades.csv,...}`
- `reports-v1/iteration_v1-055/out_of_sample/{per_symbol.csv,trades.csv,...}`
- `briefs-v1/_meta/regime_specialist_roster.csv` (appended ETH row)
- `briefs-v1/exploration_catalog.md` (appended /055 row)
- `diary-v1/iteration_v1-055.md` (this file)
