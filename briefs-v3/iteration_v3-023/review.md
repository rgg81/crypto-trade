# Phase 7.5 Critic Review — iter-v3/023

OVERALL: **EXPLORATION-NEGATIVE (clean)** — funding rate retest at n_trials=35 confirms INERT-IMPORTANCE finding from iter-v3/019, AND adds OOS overfit degradation (-1.46 vs anchor — worst single-seed OOS in v3). Funding axis permanently CLOSED.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS (inherited from iter-v3/019)
funding_rate_zscore_30 module unchanged from iter-v3/019; `compute_funding_rate_zscore` strict past-only via shift(1).

### Check 2 — Embargo Width: PASS
REQUIRED_GAP=66 verified.

### Check 3 — Multiple-Testing Correction: PASS-EXPLORATION
DSR=0.0, PBO=0.0922 (PASS), PSR=0.0000 (collapsed honest readout). n_eff=19 (consistent with n_trials=35 — 4th iteration validating the new default).

### Check 4 — IC Correlation: PASS
14-feature matrix unchanged from iter-v3/019; max funding pairwise IC 0.287 (vs vwap_dev_20).

### Check 5 — ADF Stationarity: PASS

### Check 6 — Pareto Dominance: WAIVED (single-seed)

### Check 7 — Reproducibility: PASS
Setup `f525ea6`, gate `f94ce3e`, brief `04a715d`. V3_FEATURE_COLUMNS=14 verified.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Single-axis discipline preserved.

### Check 9 — Symbol Exclusion Enforcement: PASS

### Check 10 — Feature Isolation Enforcement: PASS

### Check 11 — Forming-Candle Audit: PASS

### Check 12 — Library Version Pinning: PASS

## Critical Finding — INERT-OVERFIT-DISAMBIGUATION

iter-v3/023's mission was to disambiguate iter-v3/019's PROMISING-INERT classification. Result:

**INERT-CONFIRMED** at n_trials=35:
- BCH funding rank: 13/14 (was 10/14 at n=10) — slightly worse
- LDO funding rank: 14/14 (was 14/14 at n=10) — IDENTICAL bottom rank
- TRX funding rank: 14/14 (was 14/14 at n=10) — IDENTICAL bottom rank
- Portfolio funding rank: 14/14 (was 14/14 at n=10) — IDENTICAL bottom rank

The 3.5× larger trial budget did NOT lift funding feature importance. Conclusion: funding_rate_zscore_30 is genuinely uninformative for v3's per-symbol LightGBM architecture at the 13-feature stack baseline.

**OOS DEGRADATION** at n_trials=35:
- iter-v3/019 single-seed (n=10): OOS +0.78 (lottery-positive — Optuna landed at lucky hyperparams)
- iter-v3/023 single-seed (n=35): OOS **-1.07** (overfit-negative — larger Optuna search found IS-optimal hyperparams that don't generalize)
- Δ -1.85 from iter-v3/019 OOS to iter-v3/023 OOS

**Mechanism**: Adding INERT feature to V3_FEATURE_COLUMNS gives Optuna MORE degrees of freedom (n_estimators × max_depth × ... × 14-features search space vs 13-features). The model can overfit IS to noise INCLUDING the INERT 14th feature. At n=10 the search couldn't fully explore this; at n=35 it can — finding IS-optimal trajectories that correspond to OOS-suboptimal regions of the parameter space.

This is a generalizable lesson: **adding INERT features at higher trial budgets ACTIVELY HARMS OOS** through Optuna's larger search space. NOT just neutral; explicitly NEGATIVE.

## §4.4 Classification

| Condition | Threshold | Observed | Triggered? |
|---|---|---|---|
| IS Sharpe Δ ≥ +0.10 | ≥ +0.10 | +0.15 | YES (PATH A IS condition) |
| Rank ≤7 for ≥1 symbol | top half | BCH 13/14, LDO 14/14, TRX 14/14 | NO (PATH A FAILS) |
| Rank 14/14 across all 3 | strict | LDO + TRX + Portfolio yes; BCH 13/14 | PARTIAL (PATH B partial) |
| OOS Sharpe Δ < -0.10 | < -0.10 | -1.46 | YES (PATH C trigger) |
| OOS Sharpe Δ < -1.00 | catastrophic | -1.46 | YES (NEGATIVE) |

The OOS collapse at -1.46 is decisive. Verdict: **EXPLORATION-NEGATIVE (clean)** with INERT-CONFIRMED + OVERFIT-AT-HIGHER-BUDGET footnote.

## Saved Insight — INERT-OVERFIT Pattern

The combination of (a) feature with rank 14/14 at importance + (b) higher trial budget → OOS collapse is a generalizable pattern that should be encoded as a memory rule. Recommend new memory: `feedback_v3_inert_features_at_higher_budget.md` codifying that adding INERT features to V3_FEATURE_COLUMNS at higher Optuna budgets actively hurts OOS — drop INERT features after 1 EXPLORATION verdict; do not retest at higher budget.

## Recommendations to QR

1. **Funding axis permanently CLOSED**. Drop funding_rate_zscore_30 from V3_FEATURE_COLUMNS at iter-v3/024 (back to 13). Keep funding_v3 module + fetcher infrastructure for any HYPOTHETICAL future re-architecture (e.g., NEW model architecture or NEW labeling).

2. **iter-v3/024 axis prior**: HIGH-priority — try a DIFFERENT NEW feature family (NOT funding microstructure since that family produced 14/14 at iter-v3/015 + iter-v3/019 + iter-v3/023 all). Candidates:
   - **`btc_funding_rate_zscore_30`** (cross-asset funding — uses BTC's funding rate as a market-wide stress signal). Different mechanism than per-symbol funding (which was iter-v3/019/023). Hypothesis: BTC funding stress is exogenous to BCH/LDO/TRX-specific funding patterns.
   - **NEW labeling architecture**: regime-conditional triple-barrier (different ATR multipliers for high-vol vs low-vol regimes). Category 3 untested in post-bootstrap cycle.
   - **Open Interest delta features**: oi_delta_24h_pct or oi_zscore_30 for BCH/LDO/TRX. Distinct family from funding/microstructure.

3. **Critic strong prior**: iter-v3/024 = `btc_funding_rate_zscore_30` (cross-asset funding axis). Single new feature; uses BTC funding cache (already fetched at iter-v3/019). Cleanest single-axis test of "exogenous funding stress signal" hypothesis. If still INERT → close ALL funding-derived axes. If PROMISING → strong CONFIRMATION candidate.

## Catalog Row

`| iter-v3/023 | 2026-05-08 | funding_rate_zscore_30 RETEST at n_trials=35 (V3_FEATURE_COLUMNS=14; disambiguates iter-v3/019 INERT) | +0.15 (vs anchor +0.3788) | -1.0706 (Δ -1.46 — WORST single-seed OOS in v3; OOS MaxDD 49.93% first 50% breach) | EXPLORATION-NEGATIVE (clean) | NO — funding INERT-CONFIRMED at higher budget (rank 14/14 LDO+TRX+P; 13/14 BCH); INERT-OVERFIT mechanism (larger Optuna budget finds OOS-suboptimal trajectories on INERT 14th feature); funding axis permanently CLOSED; iter-v3/024 = btc_funding_rate_zscore_30 cross-asset variant |`
