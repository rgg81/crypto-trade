# iter-v1/029 — Phase 4 Complete (Pre-LM Master)

**Date**: 2026-05-28
**Phase**: 1-4 complete; Phase 4.5 LM Master dispatch pending
**Cycle**: 4, EXPLORATION iteration 2/10
**Anchor**: BASELINE_V1.md `v0.v1-baseline-corrected` (`f8bc12c`) — IS Sharpe +0.2829, OOS Sharpe +0.6637

---

## Phase 1 — EDA Summary

**DOT cohort pre-classification result: `POSITIVE_EVERYWHERE`** — with material caveats (see §1.5).

Numerical evidence (from `analysis/iteration_v1-029/dot_classification.csv`,
produced by `dot_cohort_classification.py`):

| Metric | DOT IS | DOT OOS | Rule | Status |
|---|---|---|---|---|
| Net PnL | **+26.62%** | **+1.96%** | Both > 0 | POSITIVE_EVERYWHERE ✓ |
| Win rate | 41.9% | 39.1% | — | within 3pp |
| Per-trade Sharpe | +0.0398 | +0.0053 | — | OOS edge essentially zero |
| OOS/IS Sharpe ratio | — | **+0.1332** | ≥ 0.5 | **FAIL** (edge-erosion regime) |
| Trades | 93 | 46 | — | — |
| Avg PnL z-score | +0.384 | +0.036 | — | OOS direction noise |

**Why POSITIVE_EVERYWHERE wins despite low OOS/IS ratio**: classification is defined
by sign-of-net-PnL across IS+OOS. DOT does NOT meet the catastrophic OOS criterion
(would require OOS < 0 net). OOS/IS ratio < 0.5 indicates EDGE EROSION, not REGIME
FLIP. By the brief's strict mapping (POSITIVE_EVERYWHERE → pure isolation), DOT
routes to pure isolation mechanism — mirroring LINK /018 +0.80 PROMISING precedent.

### §1.5 — Structural CAVEATS to the POSITIVE_EVERYWHERE label

The classification headline conceals **THREE structural drag patterns** that
LightGBM Master Phase 4.5 must adjudicate against pure isolation:

**Caveat 1 — IS direction asymmetry (LONG-dominant)**:
- IS longs: +25.39% / 56 tr / WR 42.9% / per-trade Sharpe +0.064
- IS shorts: +1.24% / 37 tr / WR 40.5% / per-trade Sharpe +0.005
- LONG side generated 95% of IS net PnL. Model E learned a LONG-biased decision boundary.

**Caveat 2 — OOS direction REVERSAL (SHORT-dominant)**:
- OOS longs: **-1.60% / 20 tr / WR 35.0%** / per-trade Sharpe -0.009
- OOS shorts: **+3.56% / 26 tr / WR 42.3%** / per-trade Sharpe +0.018
- Signs differ. |Δ| = 5.17pp (right at the 5pp asymmetry threshold).
- This is a TEXTBOOK directional regime flip: the LONG edge collapsed; shorts
  carried the tiny +1.96% net PnL.

**Caveat 3 — BTC-trend bucket signature for LONGS shows COUNTER-TREND drag**:
- OOS DOT longs in weak-up BTC (0% < btc_ret_42 < +8%): **-8.47% / 7 tr / WR 28.6%**
  (catastrophic — should be with-trend, instead net negative)
- OOS DOT longs in weak-down BTC (-8% ≤ btc_ret_42 < 0%): +14.07% / 6 tr / WR 33.3%
  (contrarian wins in weak BTC decline)
- OOS DOT longs in strong-down BTC (< -8%): -5.80% / 5 tr (counter-trend down)
- OOS DOT shorts in strong-up BTC (≥ +8%): +5.59% / 7 tr / WR 42.9% (counter-trend short)

The OOS LONG basin is **counter-trend in BTC-up regimes**, mirroring the /019 ETH
diagnosis pattern.

**Caveat 4 — H1/H2 IS regime instability**:
- IS H1 (months 1-15): **-18.19% / 59 trades** (catastrophic first half)
- IS H2 (months 16-30): **+44.82% / 34 trades** (massive recovery)
- DOT had a HUGE regime shift WITHIN IS — the +26.62% net PnL is dominated
  by the H2 recovery; if a /029 train run lands in H1's market regime, it
  could face catastrophic OOS even from pure isolation.

### §1.6 — Why classification still routes to POSITIVE_EVERYWHERE / pure isolation

Per the brief's strict mapping:
- DOT does not fit ASYMMETRIC_ROTATION (would require IS positive AND OOS catastrophic).
- DOT does not fit COUNTER-TREND OOS DRAG strictly (would require IS positive AND
  OOS catastrophic with direction asymmetry — DOT's OOS net is +1.96%, not catastrophic).
- DOT fits POSITIVE_EVERYWHERE at sign-level even with edge erosion.

The brief's mechanism mapping for POSITIVE_EVERYWHERE = pure isolation (atr_sl=1.75,
atr_tp=3.5, R1+R3 ON, R2 OFF as mandated in standard constraints — and matching
Model E baseline ATR config). **LM Master Phase 4.5 must adjudicate whether the
direction-asymmetry caveats warrant deviating from this mechanism.**

---

## Phase 2 — Labeling Decisions

**Standard cycle-4 baseline labeling — NO deviation per standard constraints**:
- Triple-barrier with σ_t EWMA 14d (cycle-2 baseline)
- `atr_tp_multiplier = 3.5` (UNCHANGED — matches Model E baseline)
- `atr_sl_multiplier = 1.75` (UNCHANGED — POSITIVE_EVERYWHERE mechanism per brief mandate)
- 21-bar timeout (UNCHANGED — 7 days at 8h)
- Labeling embargo at walk-forward boundary (`walk_forward.py:113` fix; foundation discipline)

Rationale: DOT routes to pure isolation per cohort classification; matching baseline
Model E ATR config means the only axis perturbation is COHORT (universe contraction
to DOT-only), not LABELING. This mirrors LINK /018 approach (pure-isolation reference
for POSITIVE_EVERYWHERE class).

---

## Phase 3 — Symbol Selection / Universe

**Universe: `V1_ITER029_UNIVERSE = ("DOTUSDT",)`** — single-cohort isolation.

The cohort-isolation pattern follows cycle-3 EXPLORATION precedents:
- /018: LINK-only → PROMISING +0.80 OOS Δ (POSITIVE_EVERYWHERE cohort)
- /019: ETH-only + symmetric BTC gate → PROMISING +0.50 OOS Δ (COUNTER-TREND cohort)
- /020: BTC-only pure → NEG-CAT -1.83 OOS Δ (ASYMMETRIC_ROTATION cohort)
- /022: LTC-only + asymmetric long-suppress gate → NEG-CAT -1.17 OOS Δ (ASYMMETRIC_ROTATION cohort)
- /028: LTC-only + atr_sl=1.0 → PROMISING +0.598 OOS Δ (refined SATURATION rule)

**DOT is the LAST untested single-cohort in v1 baseline universe** (BTC+ETH live as Model A pooled).

Implementation: a new `V1_ITER029_UNIVERSE = ("DOTUSDT",)` constant in
`src/crypto_trade/features_v1/__init__.py`, plus a guarded `elif` branch in
`run_baseline_v1.py` mirroring the /028 pattern but invoking Model E (DOT + R1 + R2)
with atr_tp=3.5 / atr_sl=1.75 against DOTUSDT only.

Cross-asset features (BTCUSDT klines) still required for the cross-feature
generation — DOTUSDT klines drive the trade roster, BTC klines drive cross-features.

---

## Phase 4 — Feature Design

**Feature set: `V1_FEATURE_COLUMNS_PRUNED` (43 cols)** — UNCHANGED from /028 baseline.

NO new features added. The axis variation is COHORT, NOT feature-family. Per
v1 Axis Rotation Discipline, the per-cohort-specialization-DOT axis sits in the
`universe` family (same as /018-/022-/028 cohort isolation pattern).

Active feature columns are pinned to `list(V1_FEATURE_COLUMNS_PRUNED)` at the
`LightGbmStrategy` call site (mandatory per `feedback_explicit_feature_columns.md`).

### Phase 4 — Design summary for LM Master Phase 4.5 dispatch

| Dimension | Value | Rationale |
|---|---|---|
| Cohort | DOTUSDT only | Last untested v1 single-cohort; POSITIVE_EVERYWHERE class per Phase 1 |
| Classification | POSITIVE_EVERYWHERE | Sign-level both samples positive; OOS/IS ratio caveats noted §1.5 |
| Mechanism | Pure isolation (mirrors /018 LINK) | Brief strict mapping; LM Master can adjudicate deviation |
| `atr_tp_multiplier` | 3.5 | Model E baseline UNCHANGED |
| `atr_sl_multiplier` | 1.75 | Model E baseline UNCHANGED — pure isolation mandate |
| Risk: R1 (consecutive-SL cooldown) | ON | Mirrors /028; Model E baseline has R1 |
| Risk: R2 (drawdown brake) | **OFF** | Brief mandate ("R2 OFF" in standard constraints); deviation from Model E baseline |
| Risk: R3 (OOD Mahalanobis) | ON | Project-wide always-on |
| Feature set | V1_FEATURE_COLUMNS_PRUNED (43 cols) | UNCHANGED from /028 |
| Labels | Triple-barrier σ_t EWMA 14d | UNCHANGED — cycle-2 baseline |
| Timeout | 21 bars (7 days at 8h) | UNCHANGED |
| Optuna | n_trials=18, ENSEMBLE_SIZE=3 | v1 EXPLORATION (per standard constraints) |
| Seed | 42 (single-seed) | v1 EXPLORATION standard |
| Wall-clock cap | 2h HARD | v1 EXPLORATION cadence discipline |

### KEY DEVIATION FROM Model E BASELINE: R2 OFF

The Model E baseline includes R2 (drawdown-triggered position scaling). The
standard constraints in the /029 brief mandate **R2 OFF**. This is a non-trivial
deviation — R2 was the only Model-specific risk gate beyond R1 in v0.186; turning
it off for DOT-only specialist is a single-axis change vs Model E.

**LM Master Phase 4.5 attention point**: is "pure isolation per LINK /018 model"
equivalent to "Model E baseline minus R2"? LINK /018 used Model C semantics (R1+R3,
no R2). DOT /029 with R2 OFF matches LINK /018 risk-layer pattern. This is
consistent with pure-isolation interpretation but worth confirming.

---

## Pre-Phase-4.5 Questions for LM Master

1. **Mechanism revision** — given §1.5 caveats (direction asymmetry + BTC-trend
   long-counter-trend pattern), should /029 stay at pure isolation (atr_sl=1.75)
   or pivot to a hybrid:
     (a) pure isolation + asymmetric long-suppress BTC gate (kill DOT longs when
         btc_ret_42 < -threshold OR btc_ret_42 in weak-up bucket)?
     (b) pure isolation + tighter atr_sl=1.0 (apply /028 LTC lesson defensively)?
     (c) hold at pure isolation per brief strict mapping — accept that OOS edge
         erosion may dominate?

2. **R2 OFF confirmation** — the brief mandates R2 OFF for /029. Model E
   baseline includes R2 (DD trigger=7%, anchor=15%, floor=0.33). Should R2 stay
   ON to defend against the H1-style catastrophic IS regime (in case /029 train
   window hits a similar drawdown phase)?

3. **n_trials/ensemble_size** — the brief specifies ENSEMBLE_SIZE=3, n_trials=18,
   single-seed=42, 2h cap. /028 used ENSEMBLE_SIZE=10, n_trials=35 (per LM Master
   §1 reframing) and still completed in 30 min. Should /029 elevate to /028's
   variance budget given the DOT cohort's IS regime instability?

4. **F-AXIS pre-registration** — what predicted bands does LM Master recommend for:
     - F-AXIS #1: DOTUSDT-only dispatch (binary PASS, no other symbols in trades.csv)
     - F-AXIS #2: IS [60, 130] / OOS [25, 55] trade band (DOT baseline 93 IS / 46 OOS;
       pure isolation may compress trade count)
     - F-AXIS #3: SL fire-rate at OOS (baseline 56.5%; pure isolation expected
       similar)
     - F-AXIS #4: n_eff at ENSEMBLE_SIZE=3 / n_trials=18 (expected [3,5] modal 4?)
     - F-AXIS #5: OOS direction balance — is /029 expected to RECOVER the IS LONG
       bias (i.e., OOS LONG share returns to ~60% from current 43%) or shift toward
       OOS SHORT-dominated regime?

5. **Verdict-class priors** — given DOT's classification (POSITIVE_EVERYWHERE with
   direction-asymmetry caveats), what tail-probability split does LM Master
   recommend across:
     - PROMISING
     - PROMISING-INERT-FAV
     - INERT
     - NEG-clean
     - NEG-CAT

6. **Per-cohort SATURATION coverage finalization** — /029 closes the cycle-4
   per-cohort-specialization coverage pass (LINK /018 ✓ POSITIVE_EVERYWHERE,
   ETH /019 ✓ COUNTER-TREND, BTC /020 ✗ ASYMMETRIC_ROTATION-no-fix, LTC /022 ✗
   ASYMMETRIC_ROTATION-pre-entry-gate-fail, LTC /028 ✓ ASYMMETRIC_ROTATION-
   atr_sl-label-shift, DOT /029 = LAST). What does LM Master forecast for the
   /030+ next-axis pivot if /029 outcomes match each tail (PROMISING vs INERT
   vs NEG)?

---

## Path Forward (Phase 4.5 dispatch)

Orchestrator dispatches LightGBM Master agent for Phase 4.5 advisory. LM Master
reads:
- BASELINE_V1.md (current v1 baseline + DOT per-symbol attribution)
- This file (`phase4_complete.md`)
- `analysis/iteration_v1-029/*.csv` (DOT classification + BTC trend buckets)
- `briefs-v1/iteration_v1-028/lgbm_advisor.md` (Phase 4.5 + Phase 7.4)
- `diary-v1/iteration_v1-022.md` (LTC ASYMMETRIC_ROTATION analog reference)
- Last 3 v1 diaries (/025, /027, prior iterations)

LM Master returns `briefs-v1/iteration_v1-029/lgbm_advisor.md` (Phase 4.5 section).
QR resumes Phase 5 (brief authoring), referencing LM Master Section 3 to address
each recommendation (Adopted / Modified / Rejected).

---

## Artifact paths (committed)

```
analysis/iteration_v1-029/
├── dot_cohort_classification.py    [script]
├── dot_classification.csv          [summary row]
├── dot_direction_split.csv         [per-direction × IS/OOS]
├── dot_monthly_pnl.csv             [per-month IS+OOS]
├── dot_exit_reasons.csv            [exit reason distribution]
└── dot_btc_trend_bucket.csv        [direction × BTC trend bucket]

briefs-v1/iteration_v1-029/
└── phase4_complete.md              [THIS FILE]
```
