# MN4 IDEA-06 — REVEAL (Phase-B holdout scorecard)

**Construction one-liner.** Walk-forward (monthly, 24mo trailing, purge=1) 8-config × 5-seed LightGBM regression ensemble predicting next-candle funding rate `funding[t+1]` from 24 frozen crypto-native features; FROZEN signal = `-pred_mean` (cross-sectional rank on predicted funding level); rank-neutral dollar-neutral book, daily rebal (rebal=3), gross 1.0, per-name cap 0.10, BTC+ETH HedgeOverlay, Layer-2 crisis throttle (gross_scalar 0.3 in CRASH), honest cost 5+2.5bps+funding with a 2×-GT twin. **Byte-exact Phase-A frozen construction re-run over the holdout.**

**Authorization.** Token MN4-06 spent. One authorized holdout read on `[2024-07-01, 2026-07-01)` per orchestrator Phase-B directive + user "reveal all 10" mandate. No reads past 2026-07-01. The mn3_guard is bypassed for this one reveal (orchestrator directive replaces the token check); the fit-loop corrupt-future leak check runs and is BIT-IDENTICAL.

**Model.** Opus 4.8 (Fable rate-limited / user-suspended this phase; per charter directive).

**Files.** `analysis/portfolio/mn4_idea06_reveal.py` (frozen construction re-run on holdout); `data/mn4_idea06/reveal_oof_predictions.parquet` (87,600 rows, 40 pred cols); `data/mn4_idea06/reveal_scorecard.json`; `data/mn4_reveal/spend_MN4-06.json`. No git commits.

---

## Holdout headline

| Metric | 1× cost (5+2.5bps+funding) | 2×-GT (10+5bps+funding) |
|---|---|---|
| **Sharpe** | **+1.598** | **+1.130** |
| Ann return | +67.16% | +41.14% |
| MaxDD | −28.41% | −33.67% |
| Turnover / yr | 219.0 | — |
| Win rate | 45.81% | — |
| n candles | 2190 (2 years) | — |

**Counterfactual (no-throttle, 1×):** Sharpe +1.885, ann +95.80%, maxDD −28.41%. **The crisis throttle HURT on holdout (ΔSharpe = −0.287)** — the inverse of IS where it helped (+0.146). This is the first red flag that the holdout regime is structurally different from IS.

### Per-half path (net, 1×)
| Half | n | Sharpe | Ann | mean/candle |
|---|---|---|---|---|
| 2024-H2 | 551 | **+1.18** | +21.27% | +1.90e-4 |
| 2025-H1 | 543 | **+1.16** | +50.25% | +4.47e-4 |
| 2025-H2 | 552 | **+1.59** | +54.17% | +4.36e-4 |
| 2026-H1 | 542 | **+2.34** | +163.91% | +9.83e-4 |

Every half is positive AND the path is monotonically IMPROVING through 2026-H1. No half is near zero.

### Regime buckets (holdout)
| Bucket | n | frac | Sharpe | mean/candle | β_BTC |
|---|---|---|---|---|---|
| CRASH | 246 | 11.2% | **+4.41** | +7.17e-4 | +0.007 |
| MANIA | 109 | 5.0% | **+4.39** | +1.15e-3 | +0.011 |
| CHOP | 1744 | 79.7% | **+1.33** | +4.70e-4 | −0.027 |

Every bucket is positive. But CRASH and MANIA have small samples (n=246, n=109) — the +4.4 Sharpes there are noise-amplified. The 80%-of-candles CHOP Sharpe of +1.33 is the reliable core.

### Neutrality (post-hedge) + cost
- Rolling β_BTC (270c post-hedge): mean **−0.016**, median −0.015.
- Rolling β_ETH (270c post-hedge): mean −0.001.
- Hedge: 0 skipped rebals, **80 ETH-armed rebals** (ETH leg fired; IS had 0 — another regime tell).
- Turnover/candle = 0.2000 (1× one-way; **higher than IS 0.12**); cost/candle = 1.50e-4.
- Net alpha/candle = **+5.12e-4** (vs IS −7e-6); funding flow/candle = **−4.63e-4** (income, **4.4× the IS +1.06e-4 income**).

### Prediction quality (holdout)
| Metric | Holdout | IS (Phase A) |
|---|---|---|
| Pooled IC | **0.3954** | 0.3715 |
| Pooled R² | 0.2490 | 0.1777 |
| Persistence baseline IC | 0.5389 | 0.5158 |
| Δ (model − persistence) | −0.1435 | −0.1443 |
| Per-year IC | 2024: 0.513 / 2025: 0.352 / 2026: 0.294 | 2022: 0.414 / 2023: 0.292 / 2024: 0.419 |
| Per-regime IC | CRASH 0.288 / MANIA 0.393 / CHOP 0.355 | CRASH 0.413 / MANIA 0.402 / CHOP 0.308 |

**The model's IC is stable across IS/holdout** (0.37 → 0.40), and the persistence baseline still dominates in both periods (0.52 → 0.54). The model's predictive quality is NOT the source of the holdout flip — it's the funding/price regime that changed.

### Leak battery (holdout fit loop)
- Corrupt-future positive control on the 960-fit holdout loop: corrupting grid ≥ 6024 (month 2025-07) → predictions for prior month 2025-06 are **BIT-IDENTICAL** (max abs diff 0.00e+00). The fit loop cannot see future-feature corruption through the purge=1 + trailing-window isolation.
- Decision-lag honored: training data for each holdout month ends at `b_idx - 1 - 1` (purge=1); predictions are genuinely out-of-sample per month.
- Feature pipeline is the frozen MN3-G builder (unit-tested for past-only in Phase A); the label (`forward_funding_label` k=1) is unit-tested for corrupt-future isolation.
- Sealed-holdout boundary verified: panel clipped at `MN3_HOLDOUT_END_MS` (2026-07-01 exclusive); no reads past it.

---

## Gate verdict (FROZEN thresholds, no re-gating)

| Gate | Threshold | Holdout value | Verdict | IS value |
|---|---|---|---|---|
| G1 prediction IC | ≥ 0.20 | **0.3954** | **PASS** | 0.3715 PASS |
| G2 1× Sharpe | ≥ 0.30 | **+1.598** | **PASS** | −0.044 FAIL |
| G3 \|β_BTC\| post-hedge | ≤ 0.35 | **0.016** | **PASS** | 0.008 PASS |
| G4 CRASH mean/candle | ≥ −5e-5 | **+7.17e-4** | **PASS** | −9.99e-5 FAIL |

**HOLDOUT VERDICT: PASS (4 of 4 gates).** Stage-3 paper-trade eligible per charter mechanics.

**Spend marker:** `data/mn4_reveal/spend_MN4-06.json` = `{"token":"MN4-06","result":"PASS","holdout_sharpe_2x":1.130,"holdout_maxdd":-0.2841}`.

---

## HONEST generalization read (no spin)

**The edge INVERTED, not held.** IS Sharpe was −0.044 (cost-killed carry proxy that bled in trends); holdout Sharpe is +1.598 (the same book earned +67% annualized). The CRASH bucket flipped from −1.57 to +4.41; MANIA from −1.48 to +4.39; the crisis throttle went from helping (+0.146) to hurting (−0.287). This is not the profile of a strategy that "generalized" — it's the profile of a strategy whose PnL is dominated by a regime covariate that flipped between IS and holdout.

**The mechanism is a funding-regime shift, not model generalization.** I verified the funding-rate distribution on top-40 universe members:

| | IS (2020-01 → 2024-06) | HOLDOUT (2024-07 → 2026-06) |
|---|---|---|
| mean funding | +6.92e-5 (longs pay shorts) | **−3.56e-4 (shorts pay longs)** |
| median funding | +1.00e-4 | +3.18e-5 |
| std funding | 1.27e-3 | **3.45e-3 (2.7× higher)** |
| mean abs funding | 2.97e-4 | **5.25e-4 (1.77× higher)** |
| frac funding > 0 | 63.5% | 57.0% |

The holdout funding regime was (a) **negative on average** (aggregate shorts paying longs — a bear/liquidation signature), (b) **2.7× more volatile**, and (c) **1.77× larger in absolute carry**. The book's funding income per candle rose 4.4× (from +1.06e-4 IS to +4.63e-4 holdout). And with aggregate funding negative, the LONG leg EARNED carry in holdout (longs of negative-funding names receive from shorts), whereas in IS (positive aggregate) the long leg PAID. That single sign flip roughly doubles the per-candle carry income.

**The model is still a worse carry proxy than raw current funding.** Persistence baseline IC was 0.5389 on holdout vs the model's 0.3954 — the Δ (−0.14) is identical to IS (−0.14). Ranking on `-pred_mean` approximates ranking on `-cur_fund` with noise. The holdout PASS is therefore **a carry-trade regime win that the model captures incidentally, not a funding-prediction alpha.** A raw-carry book (rank on `-cur_fund`) would very likely have scored even higher on holdout (the persistence baseline dominates the model on the level). The model's predicted-CHANGE IC of 0.39 is real but — as in IS — too small to harvest at daily cadence against taker+slip+funding cost (the change-signal IS sensitivity was Sharpe −1.53; not re-run on holdout per the one-look rule).

**Two structural red flags the Critic should weigh:**

1. **Regime-coupled PnL.** The book's edge is a leveraged bet on "crowded longs correct." In the IS bull/mania periods (2020-2021, 2024-H1) that bet bled; in the holdout's bear/volatile/liquidation-heavy period it printed. The "winner in EVERY market condition" charter bar is not met — the IS demonstrated large losses in IS-regime MANIA/CRASH (−1.5 Sharpe each), and the holdout's per-bucket Sharpes rest on small CRASH/MANIA samples (n=246, n=109). The 80%-occupancy CHOP Sharpe of +1.33 is the only reliable number; the headline +1.60 is propped up by a handful of favorable regime candles.

2. **Multiplicity / "one of 10" prior.** The charter says "expect most of the 10 to fail." A single PASS out of 10 independent reveals at the +1.6 Sharpe level on a 2-year holdout is exactly the false-positive rate a 10-idea tournament produces (Bonferroni: at 10 trials the Sharpe haircut is meaningful; a raw 1.6 is consistent with a lucky trial). The fact that the PASS is on a strategy whose IS was a clean FAIL (−0.044) — i.e., a strategy that underperformed its own persistence baseline — is a strong tell that this is a regime artifact, not a discoverable edge. The Critic's multiple-testing correction across the tournament should be the adjudicator here.

**What I did NOT do.** I did not re-gate, re-fit, or adjust any threshold. The frozen Phase-A gates are scored verbatim. The one-look discipline holds — no variant was tried on the holdout. The holdout PASS is honest; the question is whether it's *genuine* or *regime-coupled carry*, and the evidence above points hard at the latter.

**Bottom line.** The frozen gates PASS on holdout (4/4). The holdout Sharpe of +1.598 is a real number on the sealed 2-year window. But the IS→holdout inversion is driven by a funding-regime shift (positive → negative aggregate funding; 2.7× vol increase), not by model generalization — the model's IC was stable and still underperformed the persistence baseline in both periods. This is a **regime-dependent PASS of a carry-like book**, not an all-weather generalizer. The Critic should treat it as a candidate that requires multiple-testing correction and should NOT be considered a deployable generalizer on the strength of this single reveal alone.

---

## IS vs HOLDOUT summary table

| Metric | IS (Phase A) | HOLDOUT (Phase B) | Δ |
|---|---|---|---|
| 1× Sharpe | −0.044 | +1.598 | +1.642 |
| 2×-GT Sharpe | −0.606 | +1.130 | +1.736 |
| maxDD | −32.70% | −28.41% | +4.3pp |
| ann return | −2.26% | +67.16% | +69.4pp |
| Turnover/yr | 131.8 | 219.0 | +66% |
| CRASH Sharpe | −1.57 | +4.41 | +5.98 |
| MANIA Sharpe | −1.48 | +4.39 | +5.87 |
| CHOP Sharpe | +0.35 | +1.33 | +0.98 |
| throttle ΔSharpe | +0.146 | −0.287 | flipped |
| β_BTC post-hedge | +0.008 | −0.016 | stable, both ~0 |
| ETH-armed rebals | 0 | 80 | regime tell |
| funding flow/candle | −1.06e-4 (income) | −4.63e-4 (income) | 4.4× income |
| Model IC | 0.3715 | 0.3954 | stable |
| Persistence IC | 0.5158 | 0.5389 | stable (still beats model) |
| Aggregate funding mean | +6.92e-5 | −3.56e-4 | sign flip |
| Aggregate funding std | 1.27e-3 | 3.45e-3 | 2.7× |
