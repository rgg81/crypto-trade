# LightGBM Master Advisor — iter-v1/050 — Phase 4.5 (Pre-Design)

## Context Read

- Track: v1; cycle-6 EXP-5 under per-symbol regime-specialist mandate (2026-06-01, 2-cycle minimum)
- Cohort: **single-symbol DOT (DOTUSDT)**. BASELINE_V1 DOT IS Sharpe **-1.23** (WORST of 5). 93 IS trades.
- NEW feature: `dot_vs_btc_ret_ratio_30` (DOT/BTC 30d return ratio, z-scored 90 bars; clipped ±10; DOT-only)
- NEW post-prediction risk gate: skip DOT signal if `btc_realized_vol_30 > q75_IS` AND `pred_proba < 0.55`
- Optuna: n_trials=18, single seed=42, ENSEMBLE_SIZE=3 (EXPLORATION standard)
- Feature stack: V1_FEATURE_COLUMNS_PRUNED 45 → 46 cols

## Single-Symbol DOT Training — ML Perspective

DOT-only training has narrower regime coverage than pool-A pooled training. ~93 IS trades total / ~12-20 IS months means n_eff per CV fold is small. LightGBM's depth-3 split-finding will be data-hungry — `min_data_in_leaf` ∈ [20, 500] upper bound may bind. Watch for saturation.

The DOT cohort historically has been chop-heavy with vol-spike tail events. The regime gate specifically targets the catastrophic-tail mode (BTC vol spike → DOT correlation goes to 1 → DOT inherits BTC's drawdown WITHOUT independent edge). Conditional on vol-spike regime, DOT's idiosyncratic signal degrades to zero — gate IS the edge.

## Top 3 Recommendations

### 1. The regime gate IS the load-bearing change — feature is the supporting cast
The new feature `dot_vs_btc_ret_ratio_30` is theoretically clean (captures DOT's residual after BTC market beta) but historically composed-feature additions have mostly been INERT in v1 (rank 18-25 of 45). The regime gate, by contrast, has MECHANICAL effect: skip trades in vol-spike regime → IS Sharpe lifts even without new signal (trade-set restriction is the only mechanism).

**Expected F1 verdict drivers**:
- Gate fire rate ~15-30% of OOS trades in vol-spike regimes
- IS Sharpe lift +0.5 to +1.5 mechanically (drop the bad trades)
- Feature importance rank: 25-35 of 46 (mid-table, single-seed under-reading)

If verdict is PROMISING-SPECIALIST-CANDIDATE: attribution analysis MUST disambiguate feature contribution vs gate contribution. The trade-count drop is the diagnostic.

### 2. Watch for trade-rate floor failure
DOT-only with regime gate could drop below the 50 IS / 10 OOS floor. If gate fire rate 30%+ on a 93-trade IS roster, you may end up with 60-65 IS trades — borderline.

**Mitigation**: log the gate fire rate per-regime AND per-window in comparison.csv. If IS trades < 50, verdict downgrades to "trade-rate fail" regardless of Sharpe lift.

### 3. Single-seed=42 lottery risk on small cohort
DOT has fewer trades per CV fold than pooled-A. n_eff is small. Single-seed could land in a favorable basin and overstate the lift. The /046 / /045 BLOCK lesson applies: PROMISING at single-seed must be multi-seed-validated before MERGE consideration.

**Pre-register**: if /050 PROMISING, /051 OR /054 MUST be multi-seed re-validation of /050's exact config at seeds [123, 456, 789].

## Prior Distribution (8 verdict bands)

| Band | Prior | Reasoning |
|---|---|---|
| UNIVERSAL | 3% | Hard to flip DOT positive AND maintain trade-rate AND multi-seed |
| REGIME-SPECIALIST-IS | **30%** | Single-seed PROMISING with vol-spike-regime gate is the modal good outcome |
| REGIME-SPECIALIST-OOS | 5% | OOS-only without IS is unlikely |
| TAIL-CONTROL | 12% | Gate could be informational only — fires but no edge improvement |
| EXPLORATION-PROMISING | **25%** | Partial lift (IS Δ +0.5 to +1.0 without full positive flip) |
| TRUE-NEG | 10% | Feature + gate genuinely useless on DOT |
| NEGATIVE-no-effect | 10% | Single-seed under-reads moderate signal |
| LEARNED-NEG | 5% | Gate cuts the wrong trades; IS regresses |

**Modal MEAN = REGIME-SPECIALIST-IS (30%) + EXPLORATION-PROMISING (25%) = 55% positive prior.** Driven by the gate's mechanical IS Sharpe lift on a -1.23 baseline.

## Risk Flags

1. **Cross-asset OHLCV precedent**: v3 closed at 6 failures (`feedback_v3_cross_asset_ohlcv_closed`). v1 with DOT-specific idiosyncratic ratio is technically NEW class but related. Watch for "looks-good-IS-collapses-OOS" pattern.
2. **q75 leakage**: regime gate's `q75_IS` MUST be computed from training-only BTC data, not full dataset. Critic Check A will verify.
3. **Single-symbol cohort instability**: 93 trades / 18-month windows may not have ALL regimes represented in IS. Per-regime breakdown may have null cells.

## What I Did NOT Recommend

- No companion feature beyond `dot_vs_btc_ret_ratio_30` (single-feature-at-a-time discipline)
- No HP search-space change (frozen vs /049)
- No ENSEMBLE_SIZE bump from 3 (EXPLORATION budget)
- No multi-seed at /050 (defer to /051+ if PROMISING)

## Closing Note

**Confidence: MEDIUM-HIGH** on the regime gate's mechanical lift. **Confidence: LOW** on the feature's pure contribution.

The genuine question /050 should answer: **does dropping vol-spike-regime DOT trades flip DOT IS positive?** If yes, /055 CONFIRMATION assembles regime-gated specialists across symbols. If no, the regime-gate axis is closed for DOT and /051+ pivots to BTC.

**Single most important point**: report gate fire rate per-regime + per-window in comparison.csv. The attribution (feature vs gate) hinges on this metric.

— Phase 4.5 advisor authored 2026-06-01 (materialized by orchestrator from structured priors)
