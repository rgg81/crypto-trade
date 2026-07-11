# IDEA-02 — Meta-Labeled Breakout (Phase-B REVEAL, MN4)

> Token **MN4-02** spent. Window `[2024-07-01, 2026-07-01)` — ONE authorized
reveal (orchestrator Phase-B directive + user 'hold out all strategies').
Construction frozen byte-exact from Phase A. Model: Opus 4.8.


## Construction one-liner (frozen)

Donchian breakout primary (21-day channel, PIT top-30) + LightGBM meta-classifier
(4 cfg × 3 seeds, monthly walk-forward, 18-month trailing window, 3-candle purge)
predicting per-name 24h direction-quality on a BTC-residual basis; meta refines
via continuous scaling `signal = don × clip(2(p_oof − 0.5), 0, 1)`; rank-neutral
L/S with BTC-only beta hedge + dd_brake crisis throttle (-15% / -7.5% / scale 0.30).


## Holdout verdict: **FAIL** (5/7 gates)


## Holdout scorecard

Decision rows scored: 2189 (8h candles, half-open `[2024-07-01, 2026-07-01)`).


### Sharpe / risk (holdout-only)

| Variant | 1× Sharpe | 2×-GT Sharpe | maxDD | turnover_ann | ann_return |
|---|---:|---:|---:|---:|---:|
| **filtered** | **+0.909** | **+0.151** | **-33.0%** | 123.5 | +35.24% |
| unfiltered | +0.487 | +0.966 | -36.6% | 85.8 | +10.30% |

### Per-half path (holdout)

| Half | filtered | unfiltered |
|---|---:|---:|
| 2024-H2 | -1.72 | +0.80 |
| 2025-H1 | +1.65 | +0.06 |
| 2025-H2 | +2.14 | +1.43 |
| 2026-H1 | -1.39 | +0.21 |

### Regime buckets (holdout)

| Regime | n | filtered Sharpe | unfiltered Sharpe | β_BTC bucket |
|---|---:|---:|---:|---:|
| CRASH | 269 | -5.92 | -2.44 | -0.012 |
| MANIA | 109 | -2.85 | +4.11 | -0.021 |
| CHOP | 1811 | +1.40 | +0.77 | -0.011 |

### Realized beta

| Factor | mean | median | p10 | p90 |
|---|---:|---:|---:|---:|
| β_BTC (rolling 270c, full panel) | -0.007 | -0.011 | -0.046 | +0.021 |
| β_ETH (rolling 270c, full panel) | -0.003 | -0.004 | -0.027 | +0.019 |

Single-window OLS over holdout rows: β_BTC = **-0.003**, β_ETH = **+0.005**.


### Meta precision (holdout rows)

- base rate = 0.4782
- weighted (continuous meta scaling) = 0.5152
- **lift = +3.70 pp** over 58125 member rows


### Cost coverage

- 1× cost drag (turnover × 7.5 bps) ≈ 9.26% vs ann_return +35.24%
- 2×-GT cost drag (turnover × 15 bps) ≈ 18.53% vs 2×-GT ann_return +1.01%
- Sharpe retention (2×-GT / 1×) = 0.17

Cost-survival is borderline: doubling cost collapses ann_return from +35.2% to
+1.0% — more than the 9.3pp of extra direct drag, because the higher cost path
engages the dd_brake at different points and compounds along a materially
different equity trajectory. 2×-GT Sharpe +0.151 is positive but barely.


## Gate verdicts (frozen Phase-A thresholds, holdout realization)

| Gate | Threshold | Holdout | Verdict |
|---|---|---:|:---:|
| G1 Sharpe 1× >= 0.5 | (frozen) | +0.909 | PASS |
| G2 Sharpe 2×-GT > 0 | (frozen) | +0.151 | PASS |
| G3 maxDD >= -30% | (frozen) | -33.0% | FAIL |
| G4 |beta_BTC holdout| <= 0.30 | (frozen) | -0.003 | PASS |
| G5 per-half Sharpe > 0 in >= 4/4 | (frozen) | 2/4 | FAIL |
| G6 turnover_ann <= 300 | (frozen) | 123.5 | PASS |
| G7 meta lift >= +3pp | (frozen) | +3.70pp | PASS |

**5/7 gates pass → verdict: FAIL.**


## Honest generalization read

**IS → Holdout comparison.** Filtered Sharpe 1× went +1.92 (IS) → +0.91 (holdout); 2×-GT +1.43 → +0.15; maxDD -30.5% → -33.0%; meta lift +5.90pp → +3.70pp; CRASH-bucket Sharpe -3.12 → -5.92.

The edge **decayed but survived**: Sharpe 1× +0.91 (IS +1.92) — positive but materially lower.
The meta-precision lift **held direction** (+3.70pp on holdout vs +5.90pp on IS) — the meta-classifier's directional value is real, not an IS artifact.
The IS-flagged CRASH-bucket weakness (-3.12 IS) realized at -5.92 on the holdout — **the warned crash weakness materialized** — the regime-agnostic meta's structural limitation (CRASH is rare in training; upside breakouts kept in crash then fail) persisted out-of-sample.
maxDD -33.0% breached the -30% gate (IS was -30.5%) — the crisis throttle was insufficient out-of-sample as well as in-.
Per-half path (filtered): 2024-H2=-1.72, 2025-H1=+1.65, 2025-H2=+2.14, 2026-H1=-1.39.
Overall: the construction does not clear all pre-registered gates on the holdout — the value is the structural finding (meta generalizes directionally; the regime-conditional weakness is real), not a deployable book.


## Files

- Spend marker: `data/mn4_reveal/spend_MN4-02.json`
- Phase-A brief: `briefs-portfolio-mn4/IDEA-02.md`
- Phase-A diary: `diary-portfolio-mn4/IDEA-02.md`
- This reveal: `diary-portfolio-mn4/REVEAL-02.md`
- Reveal runner: `analysis/portfolio/mn4_idea02_reveal.py`
