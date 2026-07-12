# REVEAL-04 — Slow ML Factor (MN4-04): HOLDOUT FAIL, crash edge INVERTED

**Token:** MN4-04 (ONE authorized holdout look, now spent). **Window:** [2024-07-01, 2026-07-01). **Model:** Opus 4.8 (Fable user-suspended; disclosed). **Result:** **FAIL** — frozen construction trapped flat by the dd_brake; diagnostic (no brake) shows the underlying alpha INVERTED (Sharpe −0.76, crash edge +33% IS → −192% holdout).

**Spend marker:** `data/mn4_reveal/spend_MN4-04.json`. **Do NOT edit REVEAL-LEDGER.md** (orchestrator consolidates). **Quantstats tearsheets:** `reports-portfolio-mn4/quantstats_IDEA-04_IS.html` (IS, 1643 daily returns) + `reports-portfolio-mn4/quantstats_IDEA-04_HOLDOUT.html` (holdout, 730 daily returns).

## Construction one-liner (frozen, byte-exact Phase-A)

LightGBM walk-forward (monthly, 24mo window, 8×5 grid, purge=21) predicting the 21-candle forward residual total return from 24 crypto-native features; continuous demeaned-rank weights + BTC minimal-L2 beta projection; weekly rebal=21 phase 0; dd_brake crisis throttle (−15%/flat/−7.5%); honest 5+2.5bps + funding + 2×-GT twin. **NO construction change, NO re-gating.**

## Authorization note

Phase-B orchestrator directive + user mandate ("hold out all strategies") overrides the Phase-A IS-only guard. Panel clipped to grid_ms < 2026-07-01; Stage-3 data NEVER read. Walk-forward OOF retrain continued INTO the holdout (each holdout month trained on trailing 24 months of IS + earlier-holdout data, past-only). Phase A IS OOF predictions reused bit-exact; 24 holdout months freshly trained (24 × 40 = 960 new LightGBM fits, purge=21 asserted).

---

## THE HOLDOUT SCORECARD

### Two engine variants (the dd_brake flaw required both)

The frozen construction includes a dd_brake with scale=0.0 (flatten) + recovery at −7.5%. This is a **one-way door**: once DD breaches −15%, the book flattens; flat positions generate zero returns; equity freezes; the −7.5% recovery condition can NEVER trigger. The IS backtest's "31 braked rebals" was ONE sustained brake period (the IS Sharpe +1.017 came entirely from the pre-brake period). The brake was still engaged at the IS→holdout boundary, so **the frozen construction is flat for the ENTIRE holdout** — zero returns, zero turnover, zero everything.

To isolate the signal from the risk-layer flaw, I ran a **DIAGNOSTIC variant (B) with the dd_brake OFF** — the same signal, same weights, same beta projection, same costs, just no crisis throttle. This is the clean read of whether the alpha generalized.

| metric | (A) frozen+brake | (B) diagnostic/no-brake | IS Phase-A (no-brake equiv.) |
|---|---|---|---|
| **Sharpe 1×** | **NaN (flat)** | **−0.756** | +1.017 |
| **Sharpe 2×-GT** | **NaN (flat)** | **−0.880** | +0.844 |
| **maxDD** | 0.0% | **−66.0%** | −50.4% |
| ann_return | 0.0% | −30.4% | — |
| ann_vol | 0.0% | 40.2% | — |
| **b_BTC** (holdout) | 0.000 | +0.0192 | +0.0071 |
| crash b_BTC | 0.000 | +0.0501 | +0.0161 |
| mania b_BTC | 0.000 | **−0.1645** | +0.0040 |

### Per-half path (diagnostic B, 1× cost)

| half | Sharpe | ann_ret | n |
|---|---|---|---|
| 2024-H2 | −0.120 | −2.5% | 552 |
| 2025-H1 | **−1.227** | **−46.6%** | 543 |
| 2025-H2 | **−2.075** | **−64.4%** | 552 |
| 2026-H1 | −0.131 | −7.9% | 543 |

The book bled steadily through 2025, with the worst half being 2025-H2 (Sharpe −2.08). The edge was absent from the very start of the holdout (2024-H2 already slightly negative).

### Regime buckets (diagnostic B, 1× cost) — THE CRASH INVERSION

| regime | holdout ann_ret | holdout t | IS ann_ret (Phase-A) | IS t |
|---|---|---|---|---|
| **CRASH** | **−192.4%** | **−1.79** | **+33.2%** | **+1.74** |
| CHOP | −3.6% | −0.12 | +13.9% | +1.97 |
| MANIA | −76.6% | −0.89 | −7.4% | −0.70 |

**The crash edge INVERTED.** IS: +33.2% (t=+1.74). Holdout: −192.4% (t=−1.79). This is the exact inversion pattern the coordinator flagged for MN3-G-SLOW (IS crash t+11 → holdout t−2.87). The same crypto-native features + 21c label that made money in IS crashes LOST catastrophically in holdout crashes.

### Holdout OOF rank-IC (signal quality — independent of the book/risk layer)

| metric | holdout | IS (Phase-A) |
|---|---|---|
| **pooled rank-IC** | **+0.0507** | +0.0509 |
| t-stat | +11.79 | +13.57 |
| n | 2169 | 2715 |

**The IC HELD.** The signal's cross-sectional rank correlation with the 21-candle forward residual return is virtually identical between IS (+0.0509) and holdout (+0.0507). The LightGBM model still correctly ranks coins by forward residual return on unseen data.

---

## Gate verdicts (frozen Phase-A thresholds, mechanical)

| gate | threshold | holdout value | verdict |
|---|---|---|---|
| OOF IC significance | t > 3.0 | t = +11.79 | **PASS** |
| 2×-GT cost survival | Sharpe > 0 | NaN (flat, brake trap) | **FAIL** |
| ≥2/3 regime buckets positive | CRASH & CHOP positive | 0/3 (flat) | **FAIL** |
| BTC neutrality | \|b_BTC\| < 0.10 | 0.000 (flat) | PASS (trivially) |
| **OVERALL (frozen A)** | | | **FAIL** |

Even on the diagnostic (B), every gate fails: 2×-GT Sharpe = −0.880 < 0; CRASH = −192% and CHOP = −3.6% → 0/3 buckets positive. The construction is closed.

---

## HONEST generalization read (no spin)

**The signal's cross-sectional IC generalized (+0.05 IS → +0.05 holdout, t=+11.8). The book did NOT.** This is the most puzzling and important finding: the LightGBM model still correctly ranks coins by forward 21-candle residual return on data it never saw, yet a book that longs the high-ranked and shorts the low-ranked LOSES 30% annualized. Three factors explain the disconnect:

1. **Crash inversion.** The crash regime drove the catastrophe (−192% annualized in 270 crash candles). In IS, the signal correctly identified which coins would resiliently residualize in crashes; in holdout crashes (2025-H1/H2), the SAME signal's high-ranked coins cratered harder than the low-ranked ones. The cross-sectional structure of crash resilience INVERTED between the IS regime (2020–2024 retail-dominated) and the holdout regime (2024–2026 ETF/institutional-dominated). The +0.05 IC masks this because the IC is averaged across ALL candles (crash is only 270 of 2169 scored candles; the IC is positive in chop, which dominates the average).

2. **MANIA negative beta drift.** The diagnostic shows mania_b_BTC = −0.165 — the book was net-SHORT BTC beta during manias (the beta projection fought the mania upside). In IS this was a feature (neutral in mania = acceptable); in holdout's strong BTC rallies it was a steady drag.

3. **The dd_brake flaw compounded the failure.** The frozen construction's brake fires once and permanently traps the book flat (scale=0.0 with recovery at −7.5% is a one-way door — flat equity can't recover). The IS Sharpe +1.017 was a PRE-BRAKE artifact; the brake fired late in IS and stayed engaged through the entire holdout. The frozen construction scored 0% everywhere — the FAIL is mechanical, but even without the flaw (diagnostic B), the Sharpe is −0.76.

**Bottom line on the crash edge: it INVERTED, not held.** This is the same inversion that killed MN3-G-SLOW on this exact window, confirming (not refuting) the coordinator's structural prior: the crypto-native residual-alpha signal at the 8h/weekly cadence has a regime-dependent cross-sectional structure that does NOT generalize from the 2020–2024 IS to the 2024–2026 holdout. The shared DNA with MN3-G-SLOW (same 24 features + 21c label) doomed this construction to the same failure mode, despite the structural improvements (BTC beta overlay, full ensemble, continuous weights). The cost-engineering worked (IS was cost-surviving); the signal generalization did not.

**What I would NOT conclude:** that ML factor signals are dead in crypto. The IC DID generalize (+0.05, t=+11.8). The failure is in the BOOK-LEVEL extraction (the long-short spread inverted in crashes), not the cross-sectional ranking. A different book construction (e.g., regime-conditioned weighting, or trading the IC via options/spacing rather than equal-rank demeaned weights) might extract the edge. But that is a DIFFERENT construction — this one is closed.

---

## Files

- `analysis/portfolio/mn4_idea04_reveal.py` — reveal runner (frozen + diagnostic variants)
- `data/mn4_reveal/spend_MN4-04.json` — spend marker
- `data/mn4_idea04/holdout_oof.parquet` — cached holdout OOF predictions (24 months)
- `reports-portfolio-mn4/quantstats_IDEA-04_IS.html` — IS tearsheet (1643 daily returns)
- `reports-portfolio-mn4/quantstats_IDEA-04_HOLDOUT.html` — holdout tearsheet (730 daily returns)
- `logs/mn4_idea04_reveal3.log` — full execution log
