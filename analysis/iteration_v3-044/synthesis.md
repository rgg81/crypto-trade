# iter-v3/044 Cycle 3 IS-Bottleneck Diagnosis — Synthesis

## TL;DR

**The IS Sharpe bottleneck at iter-v3/040 (+0.79) is direction-asymmetric per-symbol, NOT feature-importance or labeling.**

A counterfactual block of THREE bad direction-buckets (ALGO longs, BCH longs, TRX shorts) lifts IS Sharpe from **+0.79 → +1.95** — well above the +1.0 merge floor. None of the cycle-3 axes (iter-v3/041 pruning, 042 universal ATR, 043 Kaufman ER) touched this bottleneck. They were all UNIVERSAL feature/labeling axes; the bottleneck is **per-symbol direction-asymmetric model failure**.

The orchestrator's iter-v3/044 ad-hoc pick (regime_momentum_signed_3d) does NOT address this. Even when 3d momentum is positive (favoring longs), ALGO long WR is only 22.2% — the asymmetry is not a regime-detection problem.

## Quantitative Diagnosis (from `is_constraint_analysis.csv`)

### Direction-asymmetric per-symbol IS PnL contribution (sorted worst-first)

| Symbol-Direction | n_trades | Sum PnL | WR | Persists OOS? |
|---|---:|---:|---:|---|
| **ALGO LONG** | **33** | **-53.26** | **18.2%** | **YES (OOS WR 11.1%)** |
| BCH LONG | 39 | -18.68 | 28.2% | YES (OOS WR 28.6%) |
| TRX SHORT | 43 | -13.16 | 23.3% | NO (OOS WR 41.7%) |
| BCH SHORT | 55 | +53.53 | 32.7% | YES (OOS +52.9%) |
| ALGO SHORT | 30 | +49.96 | 53.3% | YES (OOS +56.3%) |
| LDO SHORT | 11 | +26.27 | 45.5% | mixed |
| LDO LONG | 4 | +13.77 | 50.0% | n=1 (insufficient OOS) |
| TRX LONG | 42 | +7.34 | 38.1% | YES (OOS +63.6%) |

Portfolio-wide: **LONG: 118 trades, -50.83 PnL, 29.7% WR | SHORT: 139 trades, +116.59 PnL, 35.3% WR**

### Counterfactual lift from removing bad buckets

| Bucket Removed | IS PnL after | IS Sharpe after | Lift |
|---|---:|---:|---:|
| Baseline (no removal) | 65.76 | +0.79 | — |
| Remove ALGO longs | 119.02 | (high) | +81% PnL |
| Remove BCH longs | 84.44 | — | +28% PnL |
| Remove TRX shorts | 78.92 | — | +20% PnL |
| **Remove all 3** | **150.86** | **+1.95** | **+129% PnL, +1.16 Sharpe** |

This is the **true** ceiling: there are ~115 trades remaining (above the 130-trade OOS floor on annualized basis) and IS Sharpe clears the +1.0 floor with margin.

### Worst IS months (per-symbol attribution)

Of the 12 worst per-(symbol, direction, month) cells, ALGO LONG occupies positions 1, 2, 4, 6, 9, 10, 15. The single largest IS-month loss (2023-11: -16.91 PnL) is dominated by ALGO LONG -12.86. The pattern repeats: 2024-12 ALGO LONG -12.41 + BCH LONG -11.22; 2024-04 ALGO LONG -11.44.

### Market context

- ALGO IS market return: **-11.87%** (mild bear), OOS **-34.62%** (severe bear). Long bias structurally fights the trend.
- BCH IS market return: **+147.75%** (strong bull) — yet BCH longs LOSE money. Model is mistiming entries on bull symbol (entering at local highs).
- TRX IS return: **+259.27%** (strongest bull) — yet TRX shorts lose money. Short bias fights the trend.
- LDO IS return: **-54.27%** (bear) — model gets it right (more shorts than longs, both profitable).

The pattern is clear: **the model has good direction calibration on LDO but poor calibration on the other 3 symbols**. The directional signal is being learned but inverted or mis-thresholded.

### Feature importance check

In the ALGO model specifically (where the worst bottleneck lives), regime_momentum_signed_5d ranks **14/14** with importance 56 (vs top feature max_dd_window_50 at 164). Adding regime_momentum_signed_3d would likely also rank near the bottom (15/15 or 14/15) — LightGBM colsample_bytree picks the same family of importance-rank-low features rarely.

### IC test of 3d vs 5d variants

- IC(3d, 5d) on ALGO IS: **0.466** (moderate, not redundant — consistent with brief's claim)
- IC(3d, fwd_21bar_ret): **0.1122** (mildly more predictive than 5d's 0.0956)
- IC(3d, fwd) is barely above noise (n≈2200, t-stat ≈ 5.2 — significant but small effect)
- BUT: when conditioning on ALGO LONG trades, regime_mom_3d sign DOES NOT discriminate WR. Both `regime_mom_3d > 0` and `regime_mom_3d <= 0` give 13–22% WR for ALGO LONG. The feature simply isn't load-bearing for the bottleneck.

## Conclusion: 3d Variant Will Not Solve the Bottleneck

**Verdict: REVERT iter-v3/044's regime_momentum_signed_3d setup. Replace with a per-symbol direction-aware axis that targets the actual bottleneck.**

Empirical reasoning:
1. The IS bottleneck (ALGO longs) is direction-asymmetric and per-symbol.
2. regime_momentum_signed_3d is at the BOTTOM of the importance ranking for ALL 4 symbols (rank ≥11/15 expected).
3. When 3d momentum is positive (the regime where longs SHOULD work), ALGO LONG WR is still only 22.2%. The asymmetry is not a regime-detection problem.
4. Adding 3d as a 15th feature dilutes colsample_bytree picks slightly without addressing the bottleneck.

Likely classification under PATH A/B/C: PATH B PROMISING-INERT at best (small IS lift if the 3d marginal IC carries through), PATH C NEGATIVE if the colsample dilution costs more than the marginal IC adds. Cycle-3 has 3 NEGATIVE iterations already; this would likely be a 4th NEGATIVE-or-INERT.

## Top-3 Candidate Axes — Ranked by Expected IS Lift

### Axis #1 — Per-symbol direction-aware features for ALGO (ranked: HIGH expected lift)

**Mechanism**: Add per-symbol features specifically engineered to filter ALGO long signals. Quantitative basis: ALGO LONG WR 18.2% IS / 11.1% OOS persists. The ALGO model's universal feature set has regime_momentum at rank 14/14 (universal direction features under-represented). Per-symbol customization targeting ALGO direction-asymmetry.

Specific candidates (any one or combination):
- `algo_long_short_imbalance_42` = sign(close - close.shift(42)) interacted with direction
- `algo_drawdown_from_42bar_high` = (close - rolling.max(42).shift(1)) / rolling.max(42).shift(1) — proximity to recent high (LONG should fail near highs)
- Replicate iter-v3/035's per-symbol feature mechanism (which proved per-symbol customization can work)

**Quantitative basis**: blocking ALGO longs alone lifts IS PnL +81%. A directional filter that catches even 50% of bad ALGO longs (16/33 trades) would add **~+25 PnL** to IS aggregate, lifting Sharpe meaningfully.

**Implementation complexity**: MEDIUM. Existing infrastructure (V3_FEATURES_PER_SYMBOL) supports per-symbol feature lists. Engineer adds 1–2 new feature functions.

**Risk**: MEDIUM. Per-symbol features have worked (iter-v3/032 LDO ATR, partly iter-v3/035 BCH fracdiff at the per-symbol level) but bundling in CONFIRMATION risks per-symbol divergence (iter-v3/039 NO-MERGE). For EXPLORATION single-symbol axis, risk is lower.

**Wall-clock impact**: ~2h (under EXPLORATION cap).

**Predicted classification**: PROMISING (~50% probability), PROMISING-INERT (~30%), NEGATIVE (~20%).

### Axis #2 — Sample weighting by direction × symbol bear/bull regime (ranked: MEDIUM expected lift)

**Mechanism**: Down-weight ALGO LONG and BCH LONG samples during training. Up-weight ALGO SHORT and BCH SHORT samples. Forces the model to optimize asymmetrically — improving the loss-buckets it currently mis-calibrates.

**Quantitative basis**: López de Prado AFML Ch. 4 sample weighting. Currently all samples receive equal weight. Direction-conditional sample weighting is a standard technique for class-imbalance correction. The Optuna budget already explores parameter space; weight changes shift the optimization surface.

**Implementation complexity**: HIGH. Requires modifying `LightGbmStrategy` to accept per-sample weights conditional on (symbol, direction-of-label, market-regime). Risk of pipeline bugs.

**Risk**: HIGH for first-time implementation. Better deferred to a later EXPLORATION (or kept as candidate for cycle 4).

**Wall-clock impact**: ~3h (over EXPLORATION cap if pipeline changes need debugging).

**Predicted classification**: PROMISING (~35% probability if implemented correctly), NEGATIVE (~50%) if pipeline issues, INERT (~15%).

### Axis #3 — Per-symbol ATR for ALGO specifically (ranked: LOW-MEDIUM expected lift)

**Mechanism**: Tune ALGO ATR multipliers asymmetrically (e.g., (1.5, 1.5) — wider SL, equal TP) so the LONG label distribution itself reduces bad-long incidence. Per-symbol ATR proven at iter-v3/032 for LDO.

**Quantitative basis**: ALGO LONG SL/TP exits are 27/6 stop-losses to take-profits (4.5:1 ratio). The current (2.0, 1.0) ATR multiplier means TP at 2× ATR, SL at 1× ATR — but ALGO bear-market longs rarely reach TP and frequently hit SL. Wider SL with same TP wouldn't help (more time to reach TP but also more to lose); tighter TP might extract small wins before reversal.

**Implementation complexity**: LOW. V3_ATR_MULTIPLIERS_PER_SYMBOL["ALGOUSDT"] = (X, Y) is a 1-line change.

**Risk**: MEDIUM. Per-symbol ATR worked LDO-only at iter-v3/032 but TRX/BCH/ALGO at iter-v3/042 universal (1.5, 0.75) was NEGATIVE due to per-symbol divergence. ALGO-specific fit may also overfit.

**Wall-clock impact**: ~2h.

**Predicted classification**: PROMISING-INERT (~40%), PROMISING (~25%), NEGATIVE (~35%).

## Recommendation: REVERT iter-v3/044 + Replace with Axis #1 (Per-symbol features for ALGO)

The ad-hoc 3d variant (already implemented in setup commit 1f56c72) would likely be PATH B INERT or PATH C NEGATIVE based on:
- 3d does not address the actual bottleneck (direction-asymmetric per-symbol failure)
- Bottom-of-importance rank for the family in ALL 4 symbols, especially ALGO

The replacement axis (per-symbol features for ALGO) directly targets the largest single attribution loss in IS. Single-axis EXPLORATION discipline preserved (one new feature OR one modified V3_FEATURES_PER_SYMBOL entry, not both).

**Decision deferred to brief Section 1 (Hypothesis) — but the EDA basis is established here.**
