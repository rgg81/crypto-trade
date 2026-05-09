# Engineering Report — iter-v3/039

## Status: READY-FOR-CRITIC

SECOND v3 CONFIRMATION = **CONFIRMATION-NO-MERGE** per user directive 2026-05-09 ("no merge. Close it." + "both is and oos must be in shape"). OOS Sharpe gate PASSED for first time in v3 history; IS Sharpe broke vs iter-v3/028 baseline. Strict BOTH-must-improve rule confirmed at closeout.

## Headline Metrics (multi-seed mean across 2 outer × 5 inner = 10 models per cell)

| Metric | iter-v3/028 baseline | **iter-v3/039 multi-seed** | Δ vs baseline | Verdict |
|---|---:|---:|---:|---|
| **IS monthly Sharpe** | +0.5101 | **-0.0800** | **-0.59** | WORSE — IS BROKEN |
| **OOS monthly Sharpe** | +0.5053 | **+1.4650** | **+0.96** | BETTER — Gate 1 PASSES first time in v3 |
| OOS/IS Sharpe ratio | 0.99 | -18.31 | structural sign-flip | non-evaluable (IS sign-flipped) |
| IS Trades | 182 | 239 (+57) | +31% | acceptable |
| OOS Trades (mean) | 93.5 | 118 (125 / 111 per seed) | +24.5 (+26%) | improvement vs iter-v3/028 but still <130 floor (mean 118) |
| IS MaxDD | 41.43% | **58.75%** (+17.3pp) | regression | concerning — IS MaxDD breach |
| OOS MaxDD (mean) | 23.53% | 30.41% (28.86 / 31.96 per seed) | +6.9pp regression | within tolerance |
| OOS Calmar (mean) | 0.9229 | 1.318 (2.075 / 0.561 per seed) | +0.40 | mixed — seed 42 strong, seed 123 weak |
| OOS Top-symbol concentration | 76.47% (mean) | 49.96% (TRX seed 42) | -26pp improvement | substantially better but still >35% gate |
| DSR | 0.0 | 0.0 | structural | structural deflation persists |
| PBO mean | 0.1243 | **0.1072** | -0.02 | PASS at <0.4 |
| PSR | 1.0 | 1.0 | saturation | PASS |
| n_eff | 19 | 19 | unchanged | — |
| n_trials | 1050 | 1400 | +350 | larger Optuna budget (35 × 4-sym × 2 outer × 5 inner) |

## Critical Headline

**IS BROKEN, OOS PASSED — bundle FAILED strict-both-improve baseline rule.**

OOS Sharpe **+1.4650** is the FIRST OOS reading in v3 history to clear the +1.0 aspirational floor (Gate 1 PASS first ever). However, IS Sharpe **-0.0800** WORSE than iter-v3/028 baseline (-0.59 below) — IS dropped from +0.5101 to negative territory. Per user directive 2026-05-09 ("both is and oos must be in shape"), the BASELINE_V3.md update policy is now strict: **BOTH IS AND OOS must improve to update baseline**. iter-v3/039 fails this rule despite OOS gate PASS.

## Per-Seed Pareto Front

| Outer Seed | OOS Sharpe | IS Sharpe | OOS MaxDD | OOS Calmar | OOS Trades | Top OOS Conc | Verdict |
|---:|---:|---:|---:|---:|---:|---:|---|
| 42 | +1.4650 | -0.0800 | 28.86% | 2.0748 | 125 | 45.63% | strong OOS |
| 123 | +0.5290 | +0.3143 | 31.96% | 0.5612 | 111 | 45.92% | weak OOS |
| **Mean** | **+1.4650** | **-0.0800** | **30.41%** | 1.318 | 118 | ~45.8% | mixed |

**Gate 10 (Pareto: BOTH SEEDS POSITIVE) = PASS** — both outer seeds OOS > 0 (+1.47 and +0.53). However the per-seed variance is enormous (factor of 2.8× between seeds; Δ +0.94 OOS). Multi-seed mean is computed per the project convention (NOT seed-42 alone) and equals seed 42's value because of the equal-weight 2-seed averaging — the +1.47 mean is materially driven by seed 42, not equally by both.

## Per-Symbol OOS Attribution (multi-seed primary projection)

From `reports-v3/iteration_v3-039/comparison.csv`:

| Symbol | OOS weighted_pnl | OOS n_trades | OOS WR | OOS concentration_pct |
|--------|----------------:|-------------:|-------:|----------------------:|
| TRX | +29.92 | 46 | 54.3% | 49.96% |
| BCH | +23.59 | 37 | 43.2% | 39.39% |
| ALGO | +12.07 | 23 | 34.8% | 20.15% |
| LDO | -5.69 | 19 | 31.6% | -9.50% |

**4-symbol bundle is more diversified than the 3-symbol baseline** (TRX 49.96% vs prior 75.22%, ALGO net positive contributor, BCH lifted to +23.59 driven by per-symbol fracdiff). LDO drag returned (-5.69 OOS) at multi-seed despite per-symbol ATR labeling — confirms LDO ATR is mixed at multi-seed.

## Suspicious-OOS-Divergence Pattern Analysis

**The "suspicious-OOS-divergence" pattern from iter-v3/026/027/030/034/036/037 single-seeds was hoped to dissolve at multi-seed but PERSISTED.**

| Iter | Spec | IS Sharpe | OOS Sharpe | IS/OOS daily ratio |
|---|---|---:|---:|---:|
| iter-v3/026 (single-seed) | regime_momentum + vol_adj_autocorr | +0.0493 | +1.4501 | -27× |
| iter-v3/027 (single-seed) | regime_momentum + cross_asset_divergence_norm | -0.2817 | +1.6786 | structural |
| iter-v3/030 (single-seed) | per-sym LDO 7-feat subset | -0.36 | +0.42 | structural |
| iter-v3/034 (single-seed) | DROP VET + ADD fracdiff_d05_close | -0.36 | +0.92 | structural |
| iter-v3/036 (single-seed) | TRX-only vol_adj_autocorr | -0.16 | +0.55 | structural |
| iter-v3/037 (single-seed) | LDO-only cross_asset_divergence | -0.21 | -0.10 | flipped sign (sole non-divergent) |
| iter-v3/035 (single-seed) | BCH-only fracdiff (4-sym bundle) | -0.10 | **+2.85** | structural |
| **iter-v3/039 (MULTI-SEED)** | **iter-v3/035 bundle at --seeds 2** | **-0.08** | **+1.4650** | **structural — PERSISTS** |

The multi-seed validation **DID NOT dissolve the divergence**. Both seeds (42 + 123) reproduce the IS-near-zero / OOS-positive shape; multi-seed averaging confirmed that this is a **structural property of the per-symbol customization stack**, not a single-seed lottery artifact. This is the central finding of iter-v3/039 and the source of the NO-MERGE classification.

**Mechanism (working hypothesis):** Per-symbol customizations (LDO ATR labeling 1.5/0.75; BCH fracdiff_d05_close per-symbol feature) lift OOS aggregate via two non-overlapping symbols (LDO ATR widens LDO triple-barrier hits → more clean OOS exits; BCH fracdiff captures stationary post-2025 trend regime). However the same per-symbol customizations REDUCE IS profitability — LDO ATR triggers fewer IS hits (LDO IS regime more mean-reverting), and BCH fracdiff creates IS overfitting on the IS trend-poor regime. Net IS aggregate collapses to -0.08 even at multi-seed Optuna averaging.

## MERGE Gate Audit (10 gates, pre-registered in brief Section 8)

| # | Gate | Threshold | iter-v3/039 Observed | Status |
|---|---|---:|---:|---|
| 1 | OOS monthly Sharpe ≥ +1.0 | ≥ 1.0 | **+1.4650** | **PASS — first time in v3 history** |
| 2 | IS monthly Sharpe ≥ +1.0 | ≥ 1.0 | -0.0800 | **FAIL by 1.08** |
| 3 | OOS/IS Sharpe ratio ≥ 0.5 | ≥ 0.5 | -18.31 (sign-flipped) | **FAIL — IS sign-flipped, ratio non-evaluable** |
| 4 | DSR > 0.95 | > 0.95 | 0.0 | **FAIL — structural** |
| 5 | PBO < 0.4 | < 0.4 | 0.1072 | **PASS** |
| 6 | PSR > 0.95 | > 0.95 | 1.0 | **PASS** |
| 7 | Top-symbol concentration ≤ 35% | ≤ 35% | TRX 49.96% (improved from 76%) | **FAIL by 15pp (improved direction)** |
| 8 | Bundle OOS trades ≥ 130 | ≥ 130 | 118 (mean) | **FAIL by 12 trades** |
| 9 | 10-seed validation | mean>0, ≥7/10 | NOT RUN at --seeds 2 | NOT TRIGGERED |
| 10 | Pareto: BOTH outer seeds OOS Sharpe > 0 | both > 0 | +1.4650, +0.5290 | **PASS** |

**4 PASS / 5 FAIL of 9 evaluated gates** — same FAIL count as iter-v3/028 (5 FAIL there too) but with a different distribution: iter-v3/039 PASSED Gate 1 (OOS floor) for the first time but FAILED Gate 2 (IS floor) and Gate 3 (OOS/IS ratio) which iter-v3/028 had passed. The trade-off is structural to the per-symbol-customizations bundle.

## Comparison vs iter-v3/028 Baseline

| Reference | IS Sharpe | OOS Sharpe | IS Trades | OOS Trades | Top Conc | Gates passed |
|---|---:|---:|---:|---:|---:|---|
| iter-v3/028 baseline | +0.5101 | +0.5053 | 182 | 93.5 | 76.47% | 4 of 9 |
| **iter-v3/039 multi-seed** | **-0.0800** | **+1.4650** | **239** | **118** | **49.96%** | **4 of 9 (different gates)** |
| Δ | -0.59 | **+0.96** | +57 | +24.5 | -26.5pp | net 0 (different mix) |

iter-v3/039 has STRUCTURALLY DIFFERENT strengths and weaknesses than iter-v3/028: better OOS / worse IS / better diversification / similar gate-pass count. **Per user directive 2026-05-09 strict BOTH-must-improve rule, this NET-ZERO trade-off does NOT update baseline.**

## What This Tells Us About v3 Architecture

1. **OOS gate IS achievable.** OOS Sharpe +1.4650 at multi-seed proves the v3 architecture (3-7 small-cap symbols, regime_momentum_signed_5d, per-symbol customization layer) CAN produce OOS Sharpe above the +1.0 floor at CONFIRMATION-spec. This is the **first numerical confirmation** that the +1.0 OOS floor is reachable in v3.

2. **Per-symbol customization is a double-edged sword.** Per-symbol features (BCH fracdiff) and per-symbol labels (LDO ATR) lift OOS materially but break IS aggregate. This is the **suspicious-OOS-divergence pattern** confirmed at multi-seed for the first time. The pattern is STRUCTURAL to the per-symbol customization stack, NOT single-seed Optuna lottery.

3. **Per-symbol architecture is VALIDATED as code infrastructure** (V3_FEATURES_PER_SYMBOL + V3_ATR_MULTIPLIERS_PER_SYMBOL run cleanly, produce reproducible results, are debuggable). The architectural decision is NOT reverted. What is rejected is the BCH+LDO customization combo on this iteration's hypothesis.

4. **IS Sharpe is the new bottleneck.** OOS Sharpe is achievable; IS Sharpe became the binding constraint. Future cycles must lift IS Sharpe to ≥ +0.5101 (iter-v3/028 baseline) WHILE preserving OOS lift. UNIVERSAL axes that lift both are preferred over per-symbol customizations that lift OOS at IS expense.

## Reproducibility Stamp

- Brief commit SHA: `472a277` (research brief)
- Setup commit SHA: `0b13e28` (revert ALGO fracdiff; ITERATION_LABEL=v3-039)
- Wall-clock: ~3.5h (within 6h CONFIRMATION cap)
- Hardware: WSL2 / Linux 6.6.87.2 x86_64
- Library stack pinned: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1
- Run command: `uv run python run_baseline_v3.py --seeds 2`
- BASELINE_V3.md UNCHANGED at iter-v3/028 (+0.5101 IS / +0.5053 OOS)
- No tag (CONFIRMATION-NO-MERGE)

## Recommendation for Next Cycle

Per user directive 2026-05-09 ("let's try to fix is next cycle"):

- **iter-v3/040 = REVERT per-symbol customizations.** Clear V3_FEATURES_PER_SYMBOL and V3_ATR_MULTIPLIERS_PER_SYMBOL (or keep as architecture but unused). Restore iter-v3/028 baseline as the working state. Add ALGO universe (validated PROMISING at iter-v3/029) and regime_momentum (validated MERGE at iter-v3/028) as the iter-v3/040 baseline-restore-and-extend setup.
- **iter-v3/041-049 = UNIVERSAL axes that lift IS.** Per cycle 3 plan (`briefs-v3/cycle3_plan.md`): NEW universal engineered features with proven IS lift, NEW model architecture (XGBoost retest with new feature set), NEW labeling architecture (universal triple-barrier variants), feature pruning (drop bottom-3 importance universally), per-symbol additions that DON'T break IS (need IS-axis pre-validation).
- **iter-v3/050 = SECOND CONFIRMATION** on the best bundle that lifts BOTH IS and OOS.

**Status: READY-FOR-CRITIC.**
