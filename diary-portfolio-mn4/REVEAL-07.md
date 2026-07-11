# MN4 IDEA-07 — Phase B HOLDOUT REVEAL

**Token**: MN4-07 (ONE authorized look; spent irreversibly).
**Window**: [2024-07-01, 2026-07-01) — sealed 2-year holdout.
**Authorization**: orchestrator Phase-B directive + user "hold out all strategies" mandate. Overrides Phase-A IS-only.
**Construction**: FROZEN byte-exact Phase-A (REVERSAL_LAG=30/10d, REBAL=21/weekly, dispersion gate q=0.50 coverage-anchored, crisis 0.5× in CRASH, BTC beta-hedge, rank-neutral, 5+2.5bps+funding). NO changes, NO re-gating.
**Model**: Opus 4.8 (Fable suspended; user-directed per charter).

---

## Holdout headline

| Metric | 1× cost | 2×-GT cost |
|---|---|---|
| **Sharpe** | **−1.6825** | **−1.7361** |
| maxDD | **−90.07%** | −90.65% |
| annReturn | −66.58% | — |
| annVol | 54.7% | — |
| turnover (ann) | 40.96 | — |
| win_rate | 23.1% | — |
| n_periods | 2189 (8h candles) | — |

---

## Per-half path (net, 1×)

| 2024-H2 | 2025-H1 | 2025-H2 | 2026-H1 |
|---|---|---|---|
| −1.165 | −0.943 | **−2.969** | −1.800 |

Every half negative. 2025-H2 is the worst (the late-2025 deleveraging/crash window is deeply hostile to reversal).

---

## Regime buckets (1×, holdout)

| Bucket | n (8h) | Sharpe | meanRet/rebal |
|---|---|---|---|
| CRASH | 269 | **−1.769** | −0.0495% |
| MANIA | 109 | **−2.184** | −0.1021% |
| CHOP | 1811 | **−1.674** | −0.0880% |

No regime works. MANIA is the worst (−2.18) — the 2024-H2/2025 mania runs straight through the reversal book.

---

## Realized betas (post-hedge, holdout)

- **β_BTC: +0.142** (worse than IS +0.091 — the BTC hedge is less effective on the holdout).
- **β_ETH: +0.088**.
- CRASH net (n=12 weekly rebals): +0.0999%/rebal (thin sample; the weekly-cadence CRASH bucket has only 12 rebals).
- CHOP β_BTC: +0.165 (n=87 weekly rebals — the residual BTC exposure is concentrated in chop).

The hedge overlay does NOT fully cancel the BTC beta on the holdout — the rolling-beta estimate (270-candle OLS, IS-calibrated) undersizes the hedge leg as the holdout's BTC-reversal relationship shifts.

---

## Cost coverage (2×-GT vs 1×)

- Sharpe degradation 1×→2×: −1.68 → −1.74 (−0.05 Sharpe). The book is cost-robust in the sense that cost is NOT the binding constraint — there is no gross edge to survive cost. The price-only PnL is negative before any cost.

---

## Gate-by-gate verdict (principle-anchored, NOT re-gated)

| Gate | Holdout value | Threshold | Verdict |
|---|---|---|---|
| Sharpe 1× > 0 (edge exists) | −1.6825 | > 0.00 | **FAIL** |
| Sharpe 2×-GT > 0 (cost-surviving) | −1.7361 | > 0.00 | **FAIL** |
| maxDD > −50% (controlled risk) | −0.9007 | > −0.50 | **FAIL** |
| CRASH-bucket Sharpe ≥ 0 (all-weather) | −1.7689 | ≥ 0.00 | **FAIL** |
| MANIA-bucket Sharpe ≥ 0 (all-weather) | −2.1837 | ≥ 0.00 | **FAIL** |
| CHOP-bucket Sharpe ≥ 0 (all-weather) | −1.6736 | ≥ 0.00 | **FAIL** |

**OVERALL VERDICT: FAIL** (0/6 gates pass). Construction CLOSED. No rescue, no second reveal.

---

## HONEST generalization read

**The IS null generalizes — and deepens.** The construction had IS Sharpe −1.01 (price-only −0.28, no tradable edge even at zero cost); the holdout delivers Sharpe −1.68. Every metric deteriorated: maxDD deepened (−85% → −90%), all three regime buckets worsened (CRASH −0.23 → −1.77, MANIA −0.69 → −2.18, CHOP −1.28 → −1.67), and every half-year is negative. The single IS-regime that was marginal (CRASH Sharpe +0.25 at daily — the one place reversal had a pulse) is deeply negative on the holdout (−1.77). The beta-hedge's residual BTC exposure grew (β_BTC +0.09 → +0.14). There is no edge to decay, invert, or hold — the construction bleeds cost + funding on a signal with negative gross expected return in every window tested. The mechanism diagnosed in Phase A (close-to-close IC ≠ open-to-open PnL; dispersion gate backwards for crypto) is confirmed out-of-sample: the reversal anomaly does not exist as a tradable edge on crypto top-20 perps. This is the methodology working exactly as intended — a clean null, honestly reported, with zero holdout reads before the authorized reveal.

---

## IS vs holdout comparison

| Metric | IS (frozen) | Holdout | Delta |
|---|---|---|---|
| Sharpe 1× | −1.0148 | −1.6825 | −0.67 (worse) |
| Sharpe 2×-GT | −1.1010 | −1.7361 | −0.64 (worse) |
| maxDD | −85.14% | −90.07% | −4.9pp (worse) |
| turnover | 39.97 | 40.96 | +1.0 (stable) |
| β_BTC (post-hedge) | +0.091 | +0.142 | +0.05 (worse) |
| CRASH Sharpe | −0.226 | −1.769 | −1.54 (worse) |
| MANIA Sharpe | −0.691 | −2.184 | −1.49 (worse) |

The construction is CONSISTENTLY negative — no regime-flip, no edge emergence, no surprise. The holdout is worse than IS, which is the expected outcome for a negative-edge signal facing a more trending holdout period (2024-Q4 mania, 2025 chop/crash).

---

## Spend marker

`data/mn4_reveal/spend_MN4-07.json` — written. Token MN4-07 spent irreversibly.

---

## Files

- Reveal runner: `analysis/portfolio/mn4_idea07_reveal.py`
- Spend marker: `data/mn4_reveal/spend_MN4-07.json`
- This diary: `diary-portfolio-mn4/REVEAL-07.md`
- Frozen construction (unchanged): `analysis/portfolio/mn4_idea07_reversal.py`
- Phase-A brief: `briefs-portfolio-mn4/IDEA-07.md`
- Phase-A diary: `diary-portfolio-mn4/IDEA-07.md`
