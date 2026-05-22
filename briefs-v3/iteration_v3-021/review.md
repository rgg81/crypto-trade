# Phase 7.5 Critic Review — iter-v3/021

OVERALL: EXPLORATION-NEGATIVE (clean) — universe expansion (HBAR+AVAX) failed; both new symbols are net drag IS+OOS. Methodology checks 1-12 PASS. Saturation falsifier FIRES (IS trades 311 > 269 upper band).

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
13 V3_FEATURE_COLUMNS unchanged from iter-v3/018; HBAR + AVAX features regenerated via existing `features_v3` module (past-only by inheritance). Funding rate fetcher writes per-symbol `data/funding_rates/<SYM>.csv` cache; new symbols' funding histories integrated cleanly. Triple-barrier labeling unchanged.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP updated 66 → 110 = (21+1)×5. Runtime assertion `_verify_label_leakage_gap()` confirmed at run.log. Symmetric purge propagated to CPCV.

### Check 3 — Multiple-Testing Correction: PASS-EXPLORATION (informational)
DSR=0.0, PBO=0.107 (PASS < 0.40), PSR=0.0001 (collapsed — honest readout at n_trials=175, expected behavior given negative observed Sharpe). n_eff=19 maintained from iter-v3/020 (consistent with n_trials=35 default per `feedback_v3_exploration_n_trials_35.md`).

### Check 4 — IC Correlation: PASS
ic_matrix.csv 13×13 unchanged from iter-v3/018 baseline (no new features added, only universe expansion). Max |IC| 0.685 inherited.

### Check 5 — ADF Stationarity: PASS
HBAR + AVAX features stationary at end-of-training-window per adf_test.csv. Earlier-month False entries are warm-up artifacts (consistent with all v3 iterations).

### Check 6 — Pareto Dominance: WAIVED (single-seed)

### Check 7 — Reproducibility: PASS
Setup `6446d5d`, gate `61f1b35`, brief `6b84934`, EDA `a360251`. V3_MODELS=5 verified; REQUIRED_GAP=110 verified; ITERATION_LABEL=v3-021 verified.

### Check 8 — Hypothesis-Implementation Alignment: PASS-WITH-FALSIFIER-FIRED
Single-axis discipline preserved (universe expansion only; cap disabled per Critic Rec from iter-v3/020). Hypothesis predicted IS trade band [186, 269]; observed 311 — **saturation falsifier FIRES** by 42 trades over upper bound. The axis effect was larger than predicted: 5-symbol universe produced MORE trade surface than the 3-sym × (5/3) proportional estimate, but all excess trades are unprofitable.

### Check 9 — Symbol Exclusion Enforcement: PASS
{BCH, LDO, TRX, HBAR, AVAX} ∩ V3_EXCLUDED_SYMBOLS = ∅.

### Check 10 — Feature Isolation Enforcement: PASS

### Check 11 — Forming-Candle Audit: PASS
Pre-flight staleness guard fired clean (HBAR+AVAX 2.9h lag, well under 16h threshold).

### Check 12 — Library Version Pinning: PASS
sklearn pinned >=1.8,<1.9.

## §4.4 Row 5 Verification

| Condition | Threshold | Observed | Triggered? |
|---|---|---|---|
| IS Sharpe Δ < -0.10 | < -0.10 | -0.06 | NO |
| OOS Sharpe < anchor -0.10 (+0.2869) | < +0.2869 | -0.4380 | YES (massively) |
| Non-bit-identical roster | 5 ≠ 3 | universe size changed | YES |
| Saturation falsifier (IS in [186, 269]) | within band | 311 | FIRES (over upper) |

Verdict triggers via OOS Sharpe collapse condition (worst in v3 catalog at -0.83 vs anchor) + roster non-identity. Saturation falsifier fires on UPPER bound — the new symbols added MORE trade surface than predicted, all unprofitable.

**Verdict: EXPLORATION-NEGATIVE (clean)**.

## Mechanism Analysis (concur with QE engineering report)

EDA's "lowest mean |corr|" metric (HBAR 0.41, AVAX 0.50) captured **price-level return diversity**, NOT **signal diversity in the 13-feature statistical-moments space**. The 13-feature stack identified existing-symbol patterns; HBAR + AVAX have different mid-cap altcoin return regimes that LightGBM at n_trials=35 split 5 ways cannot fit.

Per-symbol IS PnL: BCH +38.4% / LDO +41.9% / TRX -19.3% / HBAR **-36.5%** / AVAX **-49.2%**. The 2 new symbols ALONE drag the portfolio by -85.7% IS PnL — even with BCH+LDO's strong contributions, total IS PnL is +35.1% (vs anchor +94.2% at iter-v3/019). This is signal dilution, not diversification.

## Recommendations to QR (iter-v3/022 axis)

Three options ranked by priority:

1. **HIGH — TRX/2022-Q4 regime gate (MEDIUM #4 from `feedback_v3_iter019_axis_priorities.md`, ELEVATED)**: addresses one of the BASELINE_V3.md outstanding constraints (PBO max=1.0 on TRX/2022-10, TRX/2023-01 — FTX/LUNA crash regime). A regime-aware kill switch (e.g., kill TRX trades when BTC_drawdown_30d > 30%) is a SURGICAL fix vs the universe-expansion blanket. This was MEDIUM priority but iter-v3/021's NEGATIVE outcome elevates structural-fix axes over speculative-axis tries.

2. **MEDIUM — Funding rate retest at n_trials=35**: iter-v3/019 funding_rate_zscore_30 was PROMISING-INERT at n_trials=10. The new EXPLORATION default is n_trials=35 (PRELIMINARY-VALIDATED by iter-v3/020 + iter-v3/021). A retest could disambiguate "feature was genuinely INERT" vs "n_trials=10 budget couldn't surface signal." If PROMISING at n_trials=35 → strong CONFIRMATION candidate.

3. **LOW — Alternative universe (ATOM, FIL, ALGO)**: same axis as iter-v3/021. Risk: the failure mode here was model-arch + signal-diversity mismatch, not symbol-specific. Different symbols may produce identical NEGATIVE pattern. Defer.

**Critic prior**: iter-v3/022 = TRX/2022-Q4 regime gate (option 1). This is a SURGICAL structural fix that addresses outstanding BASELINE_V3.md constraint #5 (PBO max). Defending the catalog discipline that ALL outstanding-constraint axes should be tested before any retesting.

## Catalog Row Recommendation

`| iter-v3/021 | 2026-05-07 | NEW universe expansion: V3_MODELS 3→5 (+HBAR +AVAX) (HIGH-priority axis #2b) | -0.06 (vs iter-v3/018 anchor +0.3788) | -0.4380 (Δ -0.83 — WORST OOS in v3 catalog; saturation falsifier FIRES at 311 IS trades) | EXPLORATION-NEGATIVE (clean) | NO — HBAR + AVAX both drag (-36.5% / -49.2% IS PnL); EDA correlation captured price diversity not signal diversity; iter-v3/022 = TRX/2022-Q4 regime gate (axis #4) |`
