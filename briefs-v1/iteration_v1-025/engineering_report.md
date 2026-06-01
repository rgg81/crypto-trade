# Engineering Report — iter-v1/025

## 1. Headers

- **Iteration**: iter-v1/025
- **Track**: v1 (refactored)
- **Branch**: `iteration-v1/025`
- **Backtest commit SHA**: `94fb3e1` (code committed before backtest run)
- **Current HEAD**: `501e1e7` (Phase 7.5 Critic review)
- **Hardware**: WSL2 / x86-64 CPU / local machine
- **Wall-clock time (backtest only)**: ~45 min (OI data fetch was ~60 min prior, not counted in backtest clock)
- **Cadence position**: Cycle-3 EXPLORATION #10/10 — LAST EXPLORATION before /027 CONFIRMATION
- **Note**: This engineering report is produced retrospectively as part of BLOCK-PENDING-FIX remediation per Critic Phase 7.5 ruling.

---

## 2. Configuration Diff vs Baseline

| Parameter | BASELINE_V1.md | iter-v1/025 |
|---|---|---|
| Iteration label | v1-baseline | v1-025 |
| Feature columns | V1_FEATURE_COLUMNS_PRUNED (42 cols) | V1_FEATURE_COLUMNS_PRUNED (43 cols; +oi_delta_30_z90) |
| Universe | V1_BASELINE_UNIVERSE (5 sym) | V1_BASELINE_UNIVERSE (5 sym) — UNCHANGED |
| Seeds | single-seed=42 | single-seed=42 — UNCHANGED |
| ENSEMBLE_SIZE | 3 | 3 — UNCHANGED |
| n_trials | 18 | 18 — UNCHANGED |
| OOS_CUTOFF_DATE | 2025-03-24 | 2025-03-24 — UNCHANGED (SACRED) |
| training_months | 24 | 24 — UNCHANGED (SACRED) |
| New module | — | `src/crypto_trade/features_v1/open_interest_v1.py` |
| New data source | — | `data/open_interest/{SYM}/8h.csv` for 5 symbols |
| skip-month policy | — | NaN fraction > 50% in oi_delta_30_z90 → skip symbol for that month |

---

## 3. Key Metrics Block

| Metric | IS | OOS | Ratio | Note |
|---|---|---|---|---|
| sharpe | +0.3327 | -0.7353 | -2.21 | F1 OOS Δ = **-1.40** (NEG-CAT threshold ≤ -0.55) |
| sortino | +0.3394 | -0.8540 | -2.52 | |
| max_drawdown | 72.75% | 63.88% | 0.88 | |
| win_rate | 40.6% | 36.0% | 0.89 | |
| profit_factor | 1.0774 | 0.8653 | 0.80 | |
| total_trades | 498 | 261 | 0.52 | IS within [400,850] PASS; OOS within [120,280] PASS |
| calmar_ratio | 0.6654 | 0.6378 | 0.96 | |
| dsr | 0.0 | -35.17 | — | EXPLORATION budget; DSR informational only |
| total_net_pnl | +48.41 | -40.75 | -0.84 | |
| psr_monthly_vs_1 | 0.1437 | 0.0549 | 0.38 | EXPLORATION budget; informational only |
| n_effective_trials | 9 | 9 | 1.00 | Within [5,10] band — PASS |
| r5_fire_rate_is | 0.0 | 0.0 | — | No R5 triggers |

**F1 OOS Δ = -0.7353 - 0.6637 (anchor) = -1.40 → NEGATIVE-CATASTROPHIC (NEG-CAT threshold ≤ -0.55)**

---

## 4. F-AXIS Mechanism Table (5 axes)

### F-AXIS #1 — DUAL GATE (rank + gain share + breadth check)

| Cohort | oi_delta_30_z90 rank | gain share | rank ≤14/43 PASS | gain ≥4.0% PASS | breadth ≤20/43 PASS |
|---|---|---|---|---|---|
| Pool A (BTC+ETH+LINK+LTC+DOT) | **4** | **7.49%** | PASS | PASS | PASS |
| Model C (LINK only) | **5** | **6.39%** | PASS | PASS | PASS |
| Model D (LTC only) | **5** | **8.00%** | PASS | PASS | PASS |
| Model E (DOT only) | **4** | **7.69%** | PASS | PASS | PASS |
| Portfolio aggregate | 4 | 7.49% | PASS | PASS | PASS |

**DUAL GATE verdict: PASS 4/4 cohorts ALL THREE sub-gates.**
**Breadth check (rank ≤20/43 on ≥3 cohorts): PASS (4/4 cohorts rank ≤5).**
**Overall F-AXIS #1: PROMISING-clean — feature was LEARNED above parity, breadth-uniform across all cohorts.**

Note: F-AXIS #1 PASS with F1 OOS Δ -1.40 produces **LEARNED-NEGATIVE-CATASTROPHIC** verdict. Per pre-registered Section 8 Row 7, F1 magnitude OVERRIDES F-AXIS #1 classification.

### F-AXIS #2 — Trade count

| Split | Actual | Band | Verdict |
|---|---|---|---|
| IS | 498 | [400, 850] | PASS |
| OOS | 261 | [120, 280] | PASS |

### F-AXIS #3 — OI delta orthogonality vs funding family (IS)

| OI feature | Funding feature | IS IC (Spearman) | Threshold | Verdict |
|---|---|---|---|---|
| oi_delta_30_z90 | funding_rate_zscore_30 | +0.135 | < 0.5 | PASS |
| oi_delta_30_z90 | funding_rate_zscore_90 | +0.056 | < 0.5 | PASS |

Max |IC| = 0.135 << 0.5. **F-AXIS #3: PASS (OI is orthogonal to funding family).**

OOS IC reconfirmation (from `oos_ic_matrix.csv`):
| OI feature | Funding feature | OOS IC | Verdict |
|---|---|---|---|
| oi_delta_30_z90 | funding_rate_zscore_30 | +0.117 | PASS |
| oi_delta_30_z90 | funding_rate_zscore_90 | +0.202 | PASS |

Max OOS |IC| = 0.202 << 0.5. **Orthogonality holds OOS.**

### F-AXIS #4 — n_eff per cell

| Metric | Value | Band | Verdict |
|---|---|---|---|
| n_eff_per_cell_median | 9 | [5, 10] | PASS |
| n_eff_per_cell_by_sym (BTC) | 9 | [5, 10] | PASS |
| n_eff_per_cell_by_sym (ETH) | 9 | [5, 10] | PASS |
| n_eff_per_cell_by_sym (LINK) | 9 | [5, 10] | PASS |
| n_eff_per_cell_by_sym (LTC) | 9 | [5, 10] | PASS |
| n_eff_per_cell_by_sym (DOT) | 10 | [5, 10] | PASS |

**F-AXIS #4: PASS. n_eff modal = 9 matches /023 modal; 43-feature column expansion had no degeneracy effect.**

### F-AXIS #5 — ADF stationarity of oi_delta_30_z90

oi_delta_30_z90 ADF p ≈ 0.0000 (strongly stationary by design — 90-bar z-score normalization). The feature does not appear in `in_sample/adf_test.csv` because the ADF runner only processes features present in the base parquet file; oi_delta_30_z90 is injected at runner time and was not captured in the ADF batch. Evidence of stationarity:
- Brief Section 2.7: ADF p ≈ 0.0000 on BTC IS-only series
- z-score construction guarantees stationarity by differencing and normalizing raw OI level

**F-AXIS #5: PASS (by construction + BTC IS-only ADF confirmation).**

---

## 5. Implementation Summary

**New files created at commit `2ab3a30`:**
- `src/crypto_trade/features_v1/open_interest_v1.py` — `add_oi_delta_v1_features()` function; 30-bar OI delta + 90-bar z-score; clip [-10, +10]; past-only `.shift(lookback)` + `.shift(1)` on rolling stats (no look-ahead)
- `tests/test_open_interest_v1.py` — 4 mandated regression tests (lines 120/163/232/261 per Critic Phase 7.5 Check 1 verification)

**Modified at `2ab3a30` + `30fafb9` (BLOCK D1+D2 fix):**
- `src/crypto_trade/features_v1/__init__.py` — `GROUP_REGISTRY` entry for `open_interest_v1` group
- `run_baseline_v1.py` — `/025` dispatch branch; `V1_FEATURE_COLUMNS_PRUNED` 42 → 43 (added `oi_delta_30_z90`); `nan_skip_columns` plumbing for skip-month policy; pre-flight HARD BLOCK assertion on OI coverage

**Data fetch:**
- `data/open_interest/{BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT}/8h.csv` fetched prior to Phase 6 launch (~60 min, not counted in backtest clock)
- OI coverage: 5/5 symbols PASS ≥1000 IS rows (see `oi_coverage_check.csv`)

---

## 6. Wall-Clock Breakdown

| Phase | Duration |
|---|---|
| OI data fetch (ETH/LINK/LTC/DOT) | ~60 min (PRIOR to backtest; not in backtest clock) |
| Phase 6.0 pre-flight (BLOCK D1+D2 found and fixed) | ~20 min |
| Backtest run (Optuna + walk-forward) | ~45 min |
| Total backtest clock | ~45 min |
| 2h HARD CAP status | PASS (well within cap) |

---

## 7. Test Outputs

```
uv run pytest tests/test_open_interest_v1.py -v
```
- 4 mandated regression tests: PASS
- 83 total v1 tests: PASS (no regressions)
- Lint: `uv run ruff check . && uv run ruff format .` — PASS (N806 lint fix at commit `1ce0b2d`)

---

## 8. Anomaly Notes

**(a) OI fetch duration exceeded brief estimate:**
Brief Section 0.7 estimated 35-45 min total. The OI data fetch for 4 symbols (ETH/LINK/LTC/DOT) took ~60 min — approximately 15 min per symbol via Binance REST API pagination. This pre-fetch was NOT included in the 2h HARD CAP count (it ran before Phase 6 launch). Wall-clock budget for Phase 6 proper was well within cap.

**(b) ALL 4 cohorts DUAL GATE PROMISING-clean BUT F1 OOS Δ = -1.40 — NEW LEARNED-NEGATIVE-CATASTROPHIC subtype:**
This is the first LEARNED-NEGATIVE-CATASTROPHIC instance in v1 cycle-3 history. All prior LEARNED-NEGATIVE verdicts (/023) were NEG-clean (Δ ∈ [-0.55, -0.10)); /025 simultaneously clears DUAL GATE breadth across 4/4 cohorts AND produces OOS Δ -1.40 (worst-ever single-seed v1 loss after /022 -1.17). Mechanism: OI feature at rank 4/43 (top basin cluster) concentrates 7.5% of all split gain; when the Q5 strong-positive OI regime (OOS concentrated in bearish 2025-Q2/Q3 altcoin period) collapses, the narrow basin relocates and drags all 4 top features with it.

**(c) Brief ORACLE EDA misidentified load-bearing IS band:**
Brief Section 2.6 identified Q4 mild-positive (z90 ∈ [+0.29, +0.95], Sharpe-proxy +1.68) as the primary signal. Actual IS trade attribution (from `oracle_q4_oos_attribution.csv`) shows Q1 neg-extreme (IS PnL +31.44, n=102) was the primary IS profit basin, NOT Q4 (IS PnL +0.78, n=107). EDA used distribution-level forward-return regression, not realized trade attribution — the model concentrated IS trades differently from the EDA quintile pattern.

**(d) LM Master Phase 7.4 §1(B) Q1 OOS figure discrepancy:**
LM Master Post-Mortem cited Q1 OOS PnL = -30.78 (sign-flip). Actual trade-attribution join produces Q1 OOS PnL = +24.63 (POSITIVE — no sign-flip). The discrepancy arises because LM Master analysis used IS-EDA regime windows (aggregate forward-return by z90 bin) rather than realized-trade join. Q5 collapse figure (-56.41 LM vs -54.84 actual) is consistent. Q3_mid is the dominant OOS loss channel (-57.44 from 55 trades) — not Q1. See `oracle_q4_oos_attribution.csv` for full reconciliation.

**(e) LM Master §4 /027 bundle LOCKED recommendation — ADOPTED:**
/027 CONFIRMATION is locked to 2-specialist bundle: Pool baseline (FROZEN, no OI/funding) + LINK specialist + ETH+gate specialist. OI delta EXCLUDED. Target +1.10 to +1.30 OOS Sharpe at multi-seed. Cross-correlation pre-validation MANDATORY.

---

## 9. OI Coverage Audit (per brief Section 3.6 HARD BLOCK)

From `oi_coverage_check.csv`:

| Symbol | Status | IS rows | IS coverage | HARD BLOCK |
|---|---|---|---|---|
| BTCUSDT | PRESENT | 4,994 | 87.2% | PASS |
| ETHUSDT | PRESENT | 3,626 | 63.3% | PASS |
| LINKUSDT | PRESENT | 3,626 | 63.9% | PASS |
| LTCUSDT | PRESENT | 3,626 | 63.8% | PASS |
| DOTUSDT | PRESENT | 3,626 | 72.2% | PASS |

**5/5 symbols PASS ≥1000 IS rows. HARD BLOCK requirement (≥3/5): PASS.**

The 2020-01 → 2020-09 NaN window for BTC/ETH/LINK/LTC (pre-OI archive start) was handled by skip-month policy per brief Section 3.6. No symbol was skipped in the final backtest for this reason — by the time the 90-bar z-score window becomes valid (2020-09 + 90 bars = 2021-07 approx), the training data is rich enough to include all symbols.

---

## 10. Per-Fold Feature Importance

From `in_sample/feature_importance_per_fold.csv`:

Per-fold rank stability of oi_delta_30_z90 **cannot be reconstructed retrospectively** from the /025 run. The runner outputs aggregated feature importance across all walk-forward months; the per-fold (per-month) importance log was not enabled in the /025 dispatch. Aggregate ranks from `feature_importance_*.csv` are:

| Cohort | Aggregate rank / 43 | Gain share |
|---|---|---|
| Pool A | 4 | 7.49% |
| Model C (LINK) | 5 | 6.39% |
| Model D (LTC) | 5 | 8.00% |
| Model E (DOT) | 4 | 7.69% |

These are cross-fold averages. Per LM Master §5(b), std-of-rank across folds > 8 would trigger PROMISING-FEATURE-MECHANICAL classification — this diagnostic is **deferred** to /026 or /027 if per-fold logging is enabled in future runners. The uniform breadth across 4 cohorts (rank 4-5) suggests the feature is consistently mid-table, but intra-fold variance is unknown.

---

## 11. Gate Efficacy Table

No R5 gates fired in IS or OOS (r5_fire_rate_is = 0.0; r5_fire_rate_oos = 0.0). The OI addition did not modify gate thresholds or eligibility criteria; all v1 baseline gates are UNCHANGED at /025.

---

## Status

OVERALL=READY-FOR-CRITIC (BLOCK-PENDING-FIX retrospective remediation complete)

**Empirical verdict (pre-registered per Section 8):**
**EXPLORATION-NEGATIVE-CATASTROPHIC — LEARNED-NEGATIVE-CATASTROPHIC subtype (NEW)**

- F1 OOS Δ = -1.40 (NEG-CAT band ≤ -0.55)
- F-AXIS #1 DUAL GATE PASS 4/4 cohorts (feature LEARNED uniformly)
- F-AXIS #1 PASS + F1 NEG-CAT = LEARNED-NEGATIVE-CATASTROPHIC per Section 4 verdict matrix
- /027 bundle: 2-specialist LOCKED (Pool baseline + LINK + ETH+gate); OI delta EXCLUDED
- Multi-seed mandate: ACTIVE for /027 HIGH-RISK (HIGH-RISK count ≥ 3 in cycle-3)
