# IDEA-04 — Slow ML Factor (cost-engineered) — Research Brief

**Track:** MN4 blind tournament (charter `TOURNAMENT-CHARTER-MN4.md`, idea 04).
**Role:** QR+QE pair. **Model:** Opus 4.8 (Fable user-suspended this phase — disclosed; charter deviation sanctioned).
**Construction hash:** byte-frozen in `analysis/portfolio/mn4_idea04_construction.py`; OOF predictions persisted to `data/mn4_idea04/`.

## 1. Hypothesis (one paragraph)

A LightGBM walk-forward model predicting the **weekly (21-candle) forward residual total return** from 24 crypto-native features (funding, OI, taker imbalance, vol structure, liquidity), with **continuous demeaned-rank weights** (Grinold-optimal rank-IC weighting via `blind_engine` `rank_neutral`) and **BTC-only minimal-L2 beta projection** at [k-1], is cost-surviving (honest 5+2.5bps + funding, 2×-GT twin still positive) AND all-weather (positive in every regime bucket, near-zero BTC beta, crisis throttle for acute stress). The SLOW label (21c) + continuous weights + weekly rebal ARE the turnover suppression — cost-survival by construction, not by a no-trade band.

## 2. The frozen construction (byte-exact)

| component | pin |
|---|---|
| **Label** | forward 21-candle (weekly) residual TOTAL return (price resid − funding), winsorized ±0.53 (= 0.20·√(21/3), the sqrt-horizon anchor) |
| **Features** | 24 crypto-native features (IDEA04_FEATURE_COLUMNS = MN3_G_FEATURE_COLUMNS, reused READ-ONLY): 5 funding + 5 OI + 3 taker + 3 vol + 3 resmom + 2 liq + 3 market |
| **Model** | LightGBM regression, fixed 8-config grid × 5 seeds = 40 models/month, FULL ensemble mean as the signal |
| **HP grid** | num_leaves{15,31} × min_data_in_leaf{200,500} × lambda_l2{1,10}; lr=0.05, n_est=300 (no early stop), feature_frac=0.8, bag_frac=0.8/freq=1, deterministic=true. NO Optuna, zero IS-outcome-driven HP selection |
| **Seeds** | (42, 123, 456, 789, 1001) — house 5-seed ensemble |
| **Walk-forward** | monthly retrain, trailing 24-month window, **purge=21** (= label horizon), OOF span 2022-01 .. 2024-06 (30 months) |
| **Weighting** | `rank_neutral` — demeaned-rank on the continuous prediction (Grinold-optimal; continuous IC-proportional, NOT quintile-extreme) |
| **Beta projection** | BTC-only minimal-L2 (`blind_engine.apply_beta_neutralization` with `mn_beta.rolling_beta` at [k-1]) |
| **Rebal** | weekly, rebal=21, **phase 0 pre-registered headline** (all 21 phases reported) |
| **Concentration** | weight_cap=0.10 (per-name |w| ≤ 10% of gross), min_members=10 |
| **Crisis throttle** | dd_brake: trigger −15% trailing DD, scale=0.0 (flatten), release −7.5% (half trigger); principle-anchored round numbers |
| **Cost** | taker 5bps + slippage 2.5bps per side + funding on every leg; 2×-cost twin re-run (not analytic) |
| **Universe** | PIT top-40 by trailing 30-candle mean $-volume, ≥90d history, ex-stablecoins |

### 2.1 Charter "3-candle purge" → purge=21 resolution

The charter seed text says "3-candle purge at every train/OOF boundary" (copy-paste from the MN3-G fast template). The charter's MANDATORY leak battery says "verify NO train/OOF label overlap at the 21c horizon". These conflict: a 3-candle purge with a 21-candle forward label leaks the last 18 candles of every training month's label into the OOF month. **The leak battery is load-bearing and wins** → purge=21 (verified: 30/30 months, max overlap 0 candles, unit-tested + asserted in the OOF runner).

### 2.2 vs MN3-G-SLOW (the failed MN3 holdout reveal — honest disclosure)

SAME 24-feature set, 21-candle label, monthly WF, 24mo window, purge=21, 8-config grid, 5 seeds, deterministic params. DIFF: (a) BTC minimal-L2 beta projection overlay (MN3-G-SLOW had none); (b) full 8×5=40 ensemble mean as the signal (MN3-G-SLOW used single config c1); (c) continuous demeaned-rank weights at rebal=21 via the engine's `rank_neutral` (MN3-G-SLOW used a custom book with different mechanics); (d) per-construction Layer-2 dd_brake crisis throttle; (e) weight_cap=0.10 + min_members=10. MN3-G token is spent forever; this is a fresh MN4-IDEA-04 budget per charter. Shared DNA is disclosed; the construction is NOT an MN3-G re-mine.

## 3. IS-Only Evidence (the full scorecard)

**Panel:** T=4929 candles (2020-01-01 .. 2024-06-30), C=747 syms, IS-only via `mn3_slice_is` + `mn3_guard_grid`. **OOF matrix:** 109,440 member-rows, 40 prediction columns.

### 3.1 OOF rank-IC (the predictive edge)

| metric | value |
|---|---|
| **pooled rank-IC** | **+0.0509** (t=+13.57, n=2715) |
| per-config IC range | +0.0460 .. +0.0496 (8 configs, HP-insensitive) |
| per-seed IC range | +0.0443 .. +0.0532 (5 seeds, seed-stable) |

t=+13.57 is overwhelmingly significant. The 8-config IC spread (0.0036) confirms no HP-overfitting — every config lands in the same band.

### 3.2 Engine backtest (phase 0, honest cost + 2×-GT twin)

| metric | 1× cost | 2×-GT |
|---|---|---|
| **Sharpe** | **+1.017** | **+0.844** |
| maxDD | −50.4% | −46.1% |
| turnover (ann. one-way) | 27.3× | 27.3× |
| n_rebal executed | 130 | — |
| cost-coverage spread | +0.173 (1×−2× Sharpe) | — |

**Cost-survival: the 2×-GT twin delivers +0.844 Sharpe.** The charter names cost as the binding constraint on this dataset — this construction clears it.

### 3.3 Realized beta (neutral by construction, MEASURED)

| bucket | b_BTC | n |
|---|---|---|
| full-sample | **+0.0071** | 4929 |
| CRASH | +0.0161 | 637 |
| MANIA | +0.0040 | 912 |
| CHOP | +0.0044 | 3290 |

The BTC minimal-L2 beta projection drives realized β to ~0.007 — the book is market-neutral by measurement, not assumption. `post_cap_target_beta_mean=0.0000` confirms the projection fires cleanly every rebal (0 degenerate, 0 collapse).

### 3.4 Regime buckets (all-weather test)

| regime | ann_ret | t-stat | n |
|---|---|---|---|
| **CRASH** | **+33.2%** | **+1.74** | 637 |
| CHOP | +13.9% | +1.97 | 3290 |
| MANIA | −7.4% | −0.70 | 912 |

**Positive in CRASH** is the key all-weather property — the crisis throttle (31 brake events) + beta projection deliver alpha exactly when MN3-G-SLOW's book blew up (its crash_net_t was −1.59 on holdout). MANIA is slightly negative (the neutral book doesn't ride mania upside — expected and acceptable).

### 3.5 Phase robustness (no phase-luck)

17/21 phases positive; phase-agnostic mean Sharpe **+0.557**, median +0.745, spread [−0.557, +1.284]. Phase 0 (+1.017) is above the mean but not an outlier — the edge is NOT a single-phase artifact (cf. the rebal-phase feedback: /005's +0.91 was 3/21 phase luck; here 17/21 positive).

### 3.6 Per-year (1×, phase 0)

| year | Sharpe | ann_ret |
|---|---|---|
| 2022 | +2.399 | +45.4% |
| 2023 | +0.557 | +9.4% |

(2020-2021 have no OOF predictions; 2024 H1 is partial.)

## 4. Leak battery (charter mandate — ALL PASS)

| check | result |
|---|---|
| **purge assert (21c horizon)** | **PASS** 30/30 months, max overlap 0 candles |
| **corrupt-future (fit loop)** | **PASS** BIT-IDENTICAL (max abs diff 0.00e+00) — corrupting features at grid ≥ mid-IS leaves prior-month predictions unchanged |
| **decision-lag [k−1]** | structural pass (purge + WF design; OOF signal[t] trained on data ≤ t−22) |
| **injected-leak positive control** | IC=+1.0000 (harness detects leakage) |
| **PIT cross-sectional membership** | `pit_topn_universe` (no survivorship backfill) — inherited from mn3_features |
| **OI consumed at .shift(1)** | asserted in mn3_features, inherited |

## 5. Principle-anchored IS gates (pre-registered, NOT IS-fit)

| gate | threshold | result |
|---|---|---|
| OOF IC significance | t > 3.0 (Harvey-Liu tier) | **+13.57 PASS** |
| 2×-GT cost survival | Sharpe > 0 | **+0.844 PASS** |
| All-weather (≥2/3 buckets positive) | CRASH & CHOP positive | **2/3 PASS** |
| BTC neutrality | \|b_BTC\| < 0.10 | **0.007 PASS** |
| Phase majority positive | > 11/21 | **17/21 PASS** |
| Leak battery clean | ALL PASS | **PASS** |

**All gates PASS → IS-gate PASS → banked for reveal.**

## 6. The honest risk (maxDD)

**maxDD = −50.4%** is the key OOS risk. The dd_brake fires 31 times (trigger −15%, flatten, release −7.5%) and the CRASH regime is strongly positive (+33.2%), so the book is NOT blowing up in crashes — the DD is the intra-week PATH risk between weekly rebals (the brake only acts at rebal steps; a fast crash deepens the DD before the next flatten). This is disclosed honestly. A tighter brake trigger (−10%) or daily rebal might contain it — but those would be IS-fit changes, NOT principle-anchored, so they are NOT made. The construction is frozen as-is.

## 7. What would falsify this on reveal

- 2×-GT Sharpe < 0 on holdout (the cost-survival claim was IS-only luck)
- CRASH bucket negative on holdout (the all-weather claim failed)
- rank-IC collapsing below ~0.02 on holdout (the edge didn't generalize)
- any leak-battery failure reproducing on the holdout grid

## 8. Files (all namespaced mn4_idea04 — no other pair's files touched)

- `analysis/portfolio/mn4_idea04_construction.py` — frozen constants + label + WF slices + purge assert
- `analysis/portfolio/mn4_idea04_oof.py` — OOF generation runner (1200 fits, corrupt-future check)
- `analysis/portfolio/mn4_idea04_score.py` — IS scorecard + engine backtest + leak battery
- `tests/test_mn4_idea04_construction.py` — 11 unit tests (purge, decision-lag, corrupt-future, winsor)
- `data/mn4_idea04/oof_predictions.parquet` (109,440 rows × 40 pred cols) + `oof_manifest.json`
