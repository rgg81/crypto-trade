# iter-v1/043 — EDA Findings

**Iteration**: iter-v1/043 (cycle-5 EXPLORATION 10 of 10 — FINAL pre-/044 CONFIRMATION)
**TYPE**: EXPLORATION (LINK-only per-cohort isolation; diagnostic for /044 substrate composition)
**Date**: 2026-05-31
**Author**: QR (autopilot)

---

## Section 1 — Headline Prediction

| Quantity | Value | Source |
|---|---|---|
| LINK-only intrinsic OOS monthly Sharpe (from /036 trade roster) | **+1.2321** | `analysis/iteration_v1-043/eda.py` |
| /036 portfolio OOS Sharpe (LINK+DOT) | +1.7465 | `reports-v1/iteration_v1-036/comparison.csv` |
| Intrinsic Δ vs /036 | **−0.5144** | derived |
| **/043 prediction central** | **+1.23** | intrinsic anchor |
| **/043 prediction band** | **[+0.83, +1.53]** | ±0.30 Optuna-drift / DOT-correlation envelope |
| **/043 Δ vs /036 central** | **−0.51** | regression-toward-intrinsic |
| /018 LINK-only σ_t triple-barrier reference | +0.9789 | `reports-v1/iteration_v1-018/comparison.csv` |
| /018 brief task-text claim of "+1.46" | **REFUTED** (actual +0.9789) | brief Section 5 anchor correction |

**Modal verdict**: /043 lands in the **PROMISING-LOWER band (Δ ∈ [−0.5, 0))** with 55% probability.

---

## Section 2 — Method

LINK-only monthly Sharpe was reconstructed from /036's OOS `trades.csv` by:

1. Filtering `symbol == 'LINKUSDT'` (52 trades, 55.8% WR, +108.9066 net PnL%)
2. Bucketing trades by close-month → 15 months (2025-03 → 2026-05)
3. Computing `mean(monthly_pnl_pct) / std(monthly_pnl_pct) × √12`

Result: mean monthly PnL +7.26%, std monthly PnL 20.41%, **monthly Sharpe = +1.2321**.

This is the **isolated-LINK Sharpe** — what /036's LINK leg would have produced if it had been the only symbol in a single-cohort backtest (same Optuna trajectory, same labels, same features). It is the **intrinsic anchor** for /043's prediction because:

- Same labels (trend-scanning)
- Same features (44-col pruned set + regime_momentum_signed_5d)
- Same single seed (42)
- Same n_trials budget direction

What changes at /043:
- Optuna optimizes against **LINK-only objective** (not LINK+DOT combined) → expect trajectory drift ±0.30 either direction
- `ENSEMBLE_SIZE=3` at /043 vs effective ENSEMBLE_SIZE=5 at /036's 5-model-per-cohort pipeline → mild shrinkage
- No DOT-correlation diversification term in portfolio σ → already captured in LINK-only intrinsic

---

## Section 3 — Monthly Distribution (LINK-only subset of /036 OOS)

| Month | PnL % | Trades |
|---|---|---|
| 2025-03 | +10.02 | 1 |
| 2025-04 | −23.54 | 4 |
| 2025-05 | −16.07 | 4 |
| 2025-06 | +5.62 | 2 |
| 2025-07 | −11.75 | 5 |
| 2025-08 | **+54.02** | 4 |
| 2025-09 | −0.24 | 4 |
| 2025-10 | +24.51 | 4 |
| 2025-11 | +39.67 | 4 |
| 2025-12 | +3.64 | 3 |
| 2026-01 | −0.12 | 5 |
| 2026-02 | +4.10 | 1 |
| 2026-03 | −7.48 | 3 |
| 2026-04 | +15.67 | 5 |
| 2026-05 | +10.86 | 3 |

Bimodal distribution: 6 months negative (max −23.54%), 9 months positive (max +54.02%). The Sharpe is single-handedly dominated by 2025-08 / 2025-11 winning streaks; the 2025-Q2 drawdown (April + May) is a tail-risk that diversification with DOT would have damped in /036.

**Implication**: removing DOT exposes the LINK-only tail. Even if Optuna at /043 finds an equally-good signal, the portfolio σ is structurally HIGHER without DOT damping → expected /043 Sharpe ≤ intrinsic +1.23, drifting toward +1.0 floor.

---

## Section 4 — F1 Modal Band Prediction (3-scenario routing)

| Scenario | Probability | /043 OOS Sharpe Band | Δ vs /036 | /044 Routing Implication |
|---|---|---|---|---|
| **A: LOAD-BEARING-LINK** (Optuna at single-cohort objective finds cleaner trajectory than /036's joint optimization; matches or beats portfolio +1.7465) | **20%** | [+1.45, +2.05] | ≥ 0 | **/044-A pivots to LINK-only specialist** (NARROWER substrate; DOT was diluting). Higher concentration risk but cleaner Sharpe. |
| **B: PAIRING-PARTIAL** (LINK retains intrinsic ~+1.23 ±0.30; DOT-correlation diversification was contributing ~0.50 Sharpe at portfolio level) | **55%** | [+0.83, +1.40] | [−0.90, −0.35) | **/044-A stays /036 LINK+DOT substrate**. Diary records that LINK contributes most of the OOS edge but DOT is risk-diversifying co-trader. Per-cohort isolation FAILS to improve on /036; substrate composition is load-bearing. |
| **C: LINK-DEPENDS-ON-DOT** (Optuna at LINK-only over-fits to LINK noise; cross-cohort regime correlation was disciplining the trees) | **25%** | [−0.50, +0.83] | < −0.90 | **/044-A bundled** with strict LINK+DOT pairing constraint; substrate composition CRITICAL. Single-cohort isolation refuted as architectural primitive. |

### Probability rationale

- **Scenario A: 20%.** /018 precedent shows LINK-only with σ_t triple-barrier produced +0.98 vs LINK-in-pool +0.34 (Δ +0.64) — a clear "single-cohort beats pool" pattern. This supports A. However /018's mechanism (σ_t labels behave fundamentally differently per-symbol; pool damps signal) MAY NOT transfer to trend-scanning labels (which are already per-symbol-localized via inner ATR sigma). Limited to 20% as a result.
- **Scenario B: 55%.** Modal. The intrinsic LINK-only +1.23 with ±0.30 Optuna drift puts /043 squarely in this band. The 15-month subset Sharpe construction directly maps onto /043's expected geometry. Removing DOT shrinks portfolio σ benefit; cleaner Optuna trajectory at single-cohort partially compensates. Net ≈ intrinsic.
- **Scenario C: 25%.** Tail risk. Single-seed=42 at n_trials=18 is the lowest budget in v1 cycle-5; small ENSEMBLE_SIZE=3 means high single-seed variance. If Optuna picks an unlucky region (the 2025-Q2 drawdown amplifier), /043 could land NEG. The 2026-01 / 2026-03 negative months in LINK-only suggest there are configurations where LINK fails for sustained windows.

---

## Section 5 — Anchor Correction (Task-Text Audit)

The QR task text stated: "/018 LINK-only specialist precedent at /018 — was PROMISING-CLEAN at OOS Sharpe +1.46". **This is incorrect.**

Verified from `reports-v1/iteration_v1-018/comparison.csv`:
- /018 OOS Sharpe: **+0.9789** (not +1.46)
- /018 OOS trades: 48
- /018 OOS net PnL%: +39.42
- /018 OOS WR: 50.0%

Verified from `briefs-v1/iteration_v1-018/review.md`:
- Critic F1 verdict: Δ vs LINK-in-pool +0.16 → **INERT band**, not PROMISING
- Overall: EXPLORATION-PROMISING **favorable-INERT side** (not PROMISING-CLEAN)

**Implication**: the /018 precedent supports Scenario A directionally (Δ vs LINK-in-pool was POSITIVE, +0.16) but the magnitude is much smaller than the task text implied. This lowers Scenario A probability from a naive 35-40% to the 20% used above.

Additionally, /018 used **σ_t triple-barrier labels with the OLD 40-col pruned feature set** (regime_momentum_signed_5d not yet introduced at /025). /043 uses **trend-scanning labels with the NEW 44-col pruned set**. Two structural differences mean /018 is a directional precedent only, not a numerical anchor — only the LINK-subset of /036 is a numerical anchor.

---

## Section 6 — Acknowledged Limitations

1. **Single-month subset Sharpe** approximates portfolio-style Sharpe at LINK-only weight; the actual /043 backtest at LightGBM-with-trend-scanning-objective may pick a slightly different trade roster than /036's LINK subset, drifting +/− from intrinsic.
2. **15-month OOS** has wide Sharpe CI: 95% CI on +1.23 is roughly [+0.4, +2.0] using `σ_SR ≈ √(1/T) ≈ 0.26` adjustment.
3. **/043 uses --pruned-features** (44 cols incl regime_momentum_signed_5d). This matches /036, so subset Sharpe transfer is clean. If features changed, transfer would be invalid.
4. Single seed=42 means single-seed variance fully propagates. Multi-seed (deferred to /044-A CONFIRMATION) will regress toward whichever side of the trade-roster diversity the seed sampled.

---

## Section 7 — Predicted /044 Routing Decision Tree

Based on /043 OOS Sharpe outcome:

```
IF /043 OOS Sharpe ≥ +1.45:
   → Scenario A confirmed
   → /044-A CONFIRMATION = LINK-ONLY specialist (multi-seed)
   → Drop DOT from substrate; concentration risk noted

ELIF /043 OOS Sharpe ∈ [+0.80, +1.45):
   → Scenario B confirmed
   → /044-A CONFIRMATION = /036 LINK+DOT trend-scan substrate (multi-seed)
   → Diary documents per-cohort attribution: LINK is the load-bearing signal,
     DOT provides risk-diversification at portfolio σ level

ELIF /043 OOS Sharpe ∈ [+0.0, +0.80):
   → Scenario B-low confirmed
   → /044-A CONFIRMATION = /036 substrate but with revised expected
     contribution split (DOT is providing ≥0.50 Sharpe via diversification)

ELIF /043 OOS Sharpe < 0:
   → Scenario C confirmed
   → /044-A CONFIRMATION = /036 substrate FORCED PAIR (substrate composition
     is the load-bearing primitive; LINK alone insufficient)
```

**Most likely (55% probability): /043 OOS Sharpe lands in [+0.83, +1.40], confirming /044-A stays /036 LINK+DOT.**
