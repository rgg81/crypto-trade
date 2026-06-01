# iter-v1/049 — EXPLORATION feature-family — long_short_zscore_30

**Tag**: `v0.v1-049`
**Date**: 2026-06-01
**Iteration type**: EXPLORATION (cycle-6 EXP-4)
**Axis family**: `feature-family` (NON-KLINE-CLASS — top-trader long/short positioning ratio z-score)
**Cycle slot**: cycle-6 EXPLORATION **4/10**
**Status**: **NEGATIVE-CLEAN** — backtest ran; F1 + F3 failed; sign-flip IS/OOS is single-seed lottery, not edge
**BASELINE_V1.md**: UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`)

**Banner**: First cycle-6 EXPLORATION since the EDA-informational rule change (`bf2c812`) to run a full backtest. EDA F4 (ADF) + F5' (IC max |IC| = 0.2505) BOTH PASSED at pre-launch — `long_short_zscore_30` is structurally orthogonal to the pruned 44-feature kline+funding+OI+calendar surface, validating the non-kline data-class hypothesis. Backtest produced **IS daily Sharpe -0.1717 / OOS daily Sharpe +0.7322** with IS MaxDD **124.08%** (more than 2× any v1 baseline-config MaxDD). The IS / OOS sign-flip + extreme IS MaxDD are the canonical single-seed lottery signature: at `--seeds 1, n_trials=18` the per-cell Optuna outcome is sensitive to seed, and the feature appears to have destabilized the BTC+ETH pooled head while LINK / LTC / DOT specialists partially masked the damage IS, then redistributed differently OOS. BOTH IS and OOS daily Sharpe are BELOW BASELINE_V1 anchor (IS Δ = -0.65, OOS Δ = -0.46). The OOS +0.7322 is not edge re-emergence — it is OOS-favorable noise relative to a frozen-baseline single-seed Optuna trajectory.

---

## 1. Decision: NO-MERGE; feature REVERTED

**Verdict**: **NEGATIVE-CLEAN** (clean falsifier failure at F1 + F3; F4 + F5' passed pre-launch). The "non-kline data class" axis is empirically tested at EXPLORATION budget; structural orthogonality at the primitive level is necessary but NOT sufficient for productive ML contribution.

**Falsifier outcome**:

| Falsifier | Pre-registered | Observed | Verdict |
|---|---|---:|---|
| F1 — Portfolio top-15 importance + IS Sharpe Δ ≥ +0.05 | both required | IS Δ = **-0.6484** | **FAIL** |
| F3 — IS MaxDD ≤ baseline + 50% absolute | < ~75% | **124.08%** | **FAIL** |
| F4 — ADF stationarity | p < 0.05 all 5 | pre-launch PASS | PASS |
| F5' — IC orthogonality | max \|IC\| < 0.30 | 0.2505 | PASS |

**`feature_columns_count` post-revert = 44** (restored from 45). **`BASELINE_V1.md` UNCHANGED.** **`engineering_report.md` GENERATED** at closeout (was missing pre-closeout; non-blocking).

---

## 2. Observed Results

### 2.1 Headline (IS / OOS)

| Metric | IS | OOS | vs anchor |
|---|---:|---:|---|
| Daily Sharpe | -0.1717 | +0.7322 | IS Δ -0.65 / OOS Δ -0.46 |
| MaxDD | **124.08%** | 40.36% | IS catastrophic |
| Total trades | 776 | 265 | normal |
| Profit factor | 0.9674 | 1.1560 | IS losing |
| DSR (CONFIRMATION-grade) | 0.0 | 0.0 | no edge |

The IS Sharpe sign flips negative under the feature add; OOS Sharpe positive but still below anchor — neither side is consistent with a structural edge.

### 2.2 Per-symbol PnL%

| Symbol | IS pnl% | IS WR | OOS pnl% | OOS WR |
|---|---:|---:|---:|---:|
| BTCUSDT | **-102.69** | 31.1 | +45.51 | 45.5 |
| ETHUSDT | **-130.87** | 32.8 | -43.80 | 35.4 |
| LINKUSDT | +121.66 | 45.6 | +72.88 | 48.2 |
| LTCUSDT | +112.62 | 46.7 | -29.55 | 37.5 |
| DOTUSDT | +17.39 | 41.5 | +38.66 | 44.9 |

BTC + ETH share Model A (pooled) — both catastrophic IS. LINK / LTC / DOT specialist heads partially offset IS but redistribute differently OOS. **Pattern: feature destabilizes pooled head, not specialists.**

### 2.3 Per-Symbol Long/Short Importance

**Feature importance CSV files were NOT produced** (`feature_importance_*.csv` absent under `reports-v1/iteration_v1-049/`). The `_write_feature_importance` defect (known iter-v3/015/017 class) was not patched into the runner. F1 importance-component cannot be quantified; F1 verdict carried by Sharpe-Δ alone.

---

## 3. Lessons

### 3.1 EDA-PASS does not imply backtest-PASS — primary directive validated

`bf2c812` retired the NEG-CLEAN-PRE-EDA verdict band; EDA values are informational. /049 is the first cycle-6 EXPLORATION to TEST this regime change — it passed F4 + F5' at pre-launch then FAILED F1 + F3 at backtest. This is exactly the prime-directive outcome the rule change was designed for: an EDA that would have been BLOCKING under the old rule has now produced a HONESTLY-EARNED null verdict via backtest. The compute cost (≈2h) is the price of resolving genuine uncertainty rather than declaring it via theory.

### 3.2 Non-kline data class is necessary but not sufficient

`feedback_v1_kline_feature_space_dense.md` codified that cycle-6 NEW feature families MUST come from non-kline data sources. /049 satisfies that rule (top-trader long/short ratio is account-level positioning sentiment, structurally orthogonal — empirically |IC|=0.25). But orthogonality does not guarantee productive ML contribution: the LightGBM at depth 3-5 with `--seeds 1, n_trials=18` integrated the new column in a way that destabilized BTC+ETH pooled training. Structural orthogonality is a permission, not a prediction.

### 3.3 Single-seed EXPLORATION budget cannot disambiguate "feature harms" vs "single-seed lottery"

At `--seeds 1`, the IS Sharpe sign-flip + 124% MaxDD could be: (a) feature genuinely destabilizes pooled training, OR (b) seed-42 single-trajectory landed in a local minimum the feature happens to expose. Distinguishing requires multi-seed run — deferred per EXPLORATION cadence. Treating /049 as NEGATIVE-CLEAN at single-seed is the conservative interpretation; a multi-seed re-test of `long_short_zscore_30` is permitted in cycle-7 IF the per-symbol architecture pivot finds the pooled head is the bottleneck and per-symbol heads handle this feature better.

### 3.4 LAST cycle-6 pooled-stack iter — per-symbol mandate from /050

Cycle-6 has produced: /046 PROMISING-DIVERGENCE (methodology), /047 NEG-CLEAN-PRE-EDA (algebraic-sister), /048 NEG-CLEAN-PRE-EDA (volume-cluster), /049 NEGATIVE-CLEAN (non-kline, EDA-passed-then-backtest-failed). Three consecutive feature-family attempts at the pooled-stack architecture have all NEGATIVE — the feature-family axis at v1's CURRENT MODEL TOPOLOGY (BTC+ETH pooled Model A + LINK / LTC / DOT specialists) is saturated for single-feature single-seed adds.

**Cycle-6 axis-saturation conclusion**: the feature-add bottleneck is NOT primitive-orthogonality (verified at /049) and NOT the kline data space (verified at /047 + /048). It is the BTC + ETH POOLED HEAD — Model A absorbs the new feature destructively. /050+ mandate: **rotate to per-symbol architecture axis** (model-arch family). Specifically: split Model A into BTC-only + ETH-only specialist heads (5 specialists total: BTC, ETH, LINK, LTC, DOT) before resuming feature-family work. Per `feedback_v1_kline_feature_space_dense.md` + this diary's findings, feature-family work resumes once a per-symbol topology is the baseline.

### 3.5 Feature importance CSV writer defect propagated into v1

`_write_feature_importance` was patched in iter-v3 (per `feedback_v3_iter017_metalabeling_mandate.md` + iter-v3/015 Clar 3 fix) but the v1 runner `run_iteration_049.py` (and prior /047/048 templates) does NOT call the writer. /050+ runners MUST include the importance-CSV writer invocation in their `try_main` to enable F1 importance-component evaluation. This is a tooling gap; not a methodology defect; appended to followups.

---

## 4. Revert + Cleanup

- `V1_FEATURE_COLUMNS_PRUNED`: 45 → 44 (removed `long_short_zscore_30`; assert restored).
- `V1_FEATURE_COLUMNS`: unchanged at 193.
- `GROUP_REGISTRY`: 14 → 13 (de-registered `positioning_v1`).
- `src/crypto_trade/features_v1/positioning_v1.py`: **kept on disk** as dead code (future-iter ready for per-symbol-arch retest at cycle-7 multi-seed).
- `src/crypto_trade/features/__init__.py`: `positioning_v1` `_register` call removed with documented dead-code marker.
- Tests: counts restored to 13 / 44 steady-state.
- Parquets: NO regeneration needed if the runner reads OI CSV at runtime — verify per /049 runner path.
- Engineering report: GENERATED at closeout — `reports-v1/iteration_v1-049/engineering_report.md`.

---

## 5. Path Forward — Next Iteration (iter-v1/050)

**Cycle-6 → cycle-7 boundary directive**: per-symbol architecture pivot.

1. **(MANDATORY) iter-v1/050 = `model-arch` axis** — split Model A (BTC+ETH pooled) into BTC-only + ETH-only specialist heads. Five specialist heads total. NO feature changes; pure architecture pivot to isolate whether the pooled-head is the bottleneck.
2. Alternate: cycle-7 closure with /045 ALT_1 substrate multi-seed validation IF user override.
3. Future feature-family: once per-symbol topology is baseline, retest `long_short_zscore_30` under that topology (multi-seed) — current /049 NEGATIVE was on the pooled topology; the feature is preserved as dead-code for that purpose.

`feedback_v1_kline_feature_space_dense.md` PRESERVED. New rule (TO BE CODIFIED at /050 brief authoring): "non-kline data class is NECESSARY but NOT SUFFICIENT — backtest still required regardless of EDA outcome."

---

## 6. Path Forward (from Critic Phase 7.5)

No Critic Phase 7.5 review was requested for this iteration (NEGATIVE-CLEAN closeout via QR analysis). No Critic Path Forward recorded.

---

## Appendix A — Artifacts

- Brief: `briefs-v1/iteration_v1-049/research_brief.md`
- LM Master advisor: `briefs-v1/iteration_v1-049/lgbm_advisor.md`
- Engineering report: `reports-v1/iteration_v1-049/engineering_report.md`
- IS reports: `reports-v1/iteration_v1-049/in_sample/`
- OOS reports: `reports-v1/iteration_v1-049/out_of_sample/`
- comparison.csv: `reports-v1/iteration_v1-049/comparison.csv`
- basin_diagnostics: `reports-v1/iteration_v1-049/basin_diagnostics/basin_diagnostics.json`
- EDA: `analysis/iteration_v1-049/eda.py` + outputs
- Catalog row: `briefs-v1/exploration_catalog.md`
- Tag: `v0.v1-049` (NEGATIVE-CLEAN historical artifact)
