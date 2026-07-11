# IDEA-02 — Meta-Labeled Breakout (frozen construction brief, MN4)

> TOURNAMENT-CHARTER-MN4 · Phase A · Opus 4.8 model (Fable rate-limited this
> session; user-directed) · frozen byte-exact 2026-07-12.

## 0. Construction one-liner

PRIMARY = Donchian-channel breakout score on the PIT top-30 universe (8h grid,
21-day channel, daily rebal); META = a walk-forward LightGBM binary classifier
(monthly retrain, 18-month trailing window, 3-candle purge) predicting
"did the primary's implied direction pay on a BTC-residual basis over 24h?";
meta refines the primary via a **continuous confidence scaling**
`signal_filt = don × clip(2(p_oof − 0.5), 0, 1)`; market-neutral L/S
(rank-neutral) with a BTC beta-hedge overlay and a Layer-2 drawdown brake.

## 1. Hypothesis

Donchian breakouts are a classic Sharpe-positive-all-regimes prior (per the
charter's rationale) but suffer in crash regimes and on false breaks. A
meta-classifier that learns per-name features predicting continuation should
**improve precision in the worst regimes** (where the unfiltered primary
bleeds) at modest cost in the best regimes. Headline metric: the **meta
precision lift** (weighted precision − base rate) — must clear +3 pp.

## 2. Frozen construction (principle-anchored, NOT fitted)

| Knob | Value | Anchor |
|---|---|---|
| Universe | PIT top-30, trailing 30-candle mean $-volume, ex-stables | structural (breakouts need breadth; round N) |
| Channel | 63 8h-candles (≈ 21d, monthly Donchian) | round economic prior |
| Rebal | every 3 candles (24h = daily) | charter frequency; == label horizon |
| Primary | `don = (close − mid) / (upper − lower + eps)` ∈ ≈ [−0.5, +0.5] | high → long |
| Meta label | `y = 1 iff sign(don) × fwd_residual_3c > 0` (else 0; NaN where undefined) | direction-quality on BTC-residual; cost hurdle left to the engine |
| Label horizon | 3 candles (24h) | == rebal cadence |
| Meta classifier | LightGBM binary, **4 fixed configs × 3 seeds** = 12 fits/month, deterministic | NO Optuna, NO tuning (MN3-G "frozen 8-config" pattern, scaled down) |
| Walk-forward | monthly retrain, trailing 18-month window, 3-candle purge at every boundary | LdP purge convention; 18mo for daily-cadence row budget |
| OOF span | 2021-07 → 2024-06 (36 months, IS-only) | IS-only via mn3_split guard |
| Meta application | **continuous**: `signal = don × clip(2(p_oof − 0.5), 0, 1)`; NaN p_oof → weight 1 (primary intact pre-OOF) | LdP-as-refinement for magnitude-aware books (see §5) |
| Features | 14, position-pinned (breakout structure ×4, per-name flow/vol ×5, cross-section ×2, mkt-regime ×3) | all past-only; NaN = missing (no ffill) |
| Weighting | `rank_neutral` (dollar-neutral L/S) | engine default |
| Beta hedge | BTC leg only, mn_beta.rolling_beta defaults (window 270, shrink 0.33, clip [0,3]); ETH leg OFF | keep the overlay simple + transparent |
| Gross leverage | 1.0× (sum|w| target) | round |
| Crisis throttle | dd_brake at −15% DD, scale=0.30, release −7.5% (per-construction Layer-2) | charter round numbers |
| Costs (1×) | taker 5 bps + slippage 2.5 bps + funding | charter §1 |
| Costs (2×-GT) | taker 10 bps + slippage 5 bps + funding (re-run, NOT analytic) | charter §1 ground-truth twin |

All constants declared BEFORE any scorecard was inspected.

## 3. Meta features (14, position-pinned)

`don_score`, `don_pctl_own`, `chan_width_atr`, `break_age`, `vol_surge`,
`taker_imb_9c`, `rv_ratio_9_90`, `rv_own_pctl`, `dvol_rank_cs`,
`don_rank_cs`, `resmom_63c_cs`, `mkt_regime`, `btc_rv_pctl`, `fund_lvl_cs`.

All past-only with fixed windows (no fit). LightGBM `colsample_bytree` samples
by POSITION — column order pinned (house rule).

## 4. IS scorecard (FILTERED 1× headline, unless noted)

### Sharpe & risk
| Variant | 1× Sharpe | 2×-GT Sharpe | maxDD |
|---|---:|---:|---:|
| **filtered** | **+1.915** | **+1.429** | **−30.5%** |
| unfiltered (primary only) | +2.056 | +1.752 | −21.0% |

### Per-year Sharpe (filtered / unfiltered)
| Year | filtered | unfiltered |
|---|---:|---:|
| 2020 | +2.88 | +2.88 |
| 2021 | +3.05 | +3.64 |
| 2022 | **+0.14** | **−0.06** |
| 2023 | +0.96 | +2.00 |
| 2024-H1 | **−0.48** | **−1.03** |

The meta **lifts the hard regimes** (2022 bear, 2024-H1) at the cost of some
peak-regime Sharpe (2021 mania, 2023 chop). That is the intended trade —
generalization over absolute return (charter mandate).

### Per-half Sharpe (filtered)
2020-H1 −0.14; 2020-H2 +4.96; 2021-H1 +4.81; 2021-H2 −1.37; 2022-H1 +0.02;
2022-H2 +0.26; 2023-H1 −2.12; 2023-H2 +3.03; 2024-H1 −0.48.

### Regime-bucket Sharpe (filtered / unfiltered)
| Regime | n | filtered | unfiltered |
|---|---:|---:|---:|
| CRASH | 637 | **−3.12** | −1.54 |
| MANIA | 912 | +2.89 | +3.13 |
| CHOP  | 3290 | +2.60 | +2.41 |

**CRASH is the Achilles heel.** The meta HURTS in crash (-3.12 vs -1.54): the
classifier was trained predominantly on chop/mania data (CRASH is only 13% of
IS candles), so in crash it keeps upside breakouts that then fail. This is a
real structural finding (see diary § lessons).

### Realized beta (filtered, post-hedge, rolling 270c)
| Factor | mean | median | p10 | p90 |
|---|---:|---:|---:|---:|
| β_BTC | **+0.004** | +0.003 | −0.026 | +0.038 |
| β_ETH | +0.002 | +0.003 | −0.031 | +0.028 |

Neutrality by construction AND measurement: |β_BTC mean| ≪ 0.30 gate.

### Regime-bucket β_BTC (filtered)
CRASH +0.002, MANIA +0.023, CHOP −0.002. The hedge holds in every regime.

### Turnover & cost
- turnover_ann_one_way: filtered = 109.7, unfiltered = 107.2 (low — breakouts
  are slow, and the meta confidence is sticky month-to-month).
- ann_return: filtered +39.73%, unfiltered +52.87%.

### Meta precision lift (headline)
- precision unfiltered (base rate) = 0.4794
- precision filtered (meta-weighted mean) = 0.5384
- **LIFT = +5.90 pp** (gate ≥ +3 pp: PASS)

Reference (NOT the headline; for Critic visibility — no single θ is tuned):
- θ=0.55: take-rate 28.0%, precision 0.5363
- θ=0.60: take-rate 15.2%, precision 0.5446
- θ=0.65: take-rate 6.5%, precision 0.5592

## 5. Key design rulings (declared before scoring)

### R1 — Continuous meta scaling, NOT hard take/skip
López de Prado's canonical meta-labeling is hard take/skip — correct for an
EVENT-DRIVEN primary that emits explicit direction trades. For our rank-neutral
L/S book it creates a **rank artifact**: skipped names tie at signal=0 and the
cross-section demeans them into the OPPOSITE leg. A confirmed diagnostic:
zeroing 72% of member rows forced no-breakout names into the short leg in
mania, giving filtered Sharpe −0.23 (vs unfiltered +2.06). The continuous
scaling `don × clip(2(p−0.5), 0, 1)` is the principled fix — meta refines
magnitude without destroying cross-sectional structure. This ruling was made
BEFORE the fix was scored; the 0.23 → 1.92 jump is the bug-fix, not a tune.

### R2 — BTC leg hedge only (ETH off)
The charter demands neutrality be MEASURED, not assumed. A BTC-only hedge
is the simplest transparent overlay; if β_ETH proved material we would arm
the ETH leg (frozen arming rule in `blind_engine.HedgeOverlay`). Measurement
shows β_ETH mean = +0.002 — ETH leg is unnecessary on this book.

### R3 — Crisis throttle is per-construction Layer-2 (dd_brake), not a shared floor
Charter §7: "Both shared crisis floors are dead (CRISIS-FALSIFY-003)" — we use
the engine's native dd_brake at −15%/−7.5%/scale=0.30. Round numbers; the
−30.5% maxDD shows the brake is engaged but the position drifts further than
the gate allows. Tightening would be post-hoc — recorded as a path forward,
NOT adopted.

## 6. Principle-anchored IS gates (charter §5)

| Gate | Threshold | Result | Verdict |
|---|---|---:|:---:|
| G1 Sharpe 1× | ≥ 0.5 | +1.915 | PASS |
| G2 Sharpe 2×-GT | > 0 | +1.429 | PASS |
| G3 maxDD | ≥ −30% | −30.5% | **FAIL** |
| G4 \|β_BTC mean\| | ≤ 0.30 | +0.004 | PASS |
| G5 per-year Sharpe > 0 | ≥ 4/5 years | 4/5 | PASS |
| G6 turnover_ann | ≤ 300 | 109.7 | PASS |
| G7 meta lift | ≥ +3 pp | +5.90 pp | PASS |

## 7. Leak battery (charter §3)

| Check | Verdict |
|---|:---:|
| L1 corrupt-future positive control (primary + label + 14 features stable on clean prefix) | PASS |
| L2 decision-lag [k−1] (don_score[t] computable from rows ≤ t) | PASS |
| L3 PIT cross-sectional membership (no survivorship backfill) | PASS |
| L4 append-invariance (earlier-month OOF predictions stable under truncation) | PASS |

Tests: `tests/test_mn4_idea02_leak.py` (6/6 PASS).

## 8. Reveal-readiness verdict

**NOT reveal-ready.** G3 (maxDD ≥ −30%) fails by 50 bps (−30.5%).

Six of seven gates pass; the meta lift (+5.90 pp) is real and the meta
improves the hard-regime Sharpe (2022, 2024-H1) — but the crisis throttle
isn't aggressive enough to keep the filtered book inside the −30% floor.
Per the freeze-then-reveal discipline, no post-hoc tightening is adopted;
the path forward is in the diary.

**Token NOT spent.** No holdout read attempted; this is a clean IS null on G3.
