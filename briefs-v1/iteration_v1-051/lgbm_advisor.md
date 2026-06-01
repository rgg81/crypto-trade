# LightGBM Master Advisor — iter-v1/051 — Phase 4.5 (Pre-Design)

## Context Read

- Track: v1; cycle-6 EXP-6 — multi-seed re-validation of iter-v1/050 PROMISING-PARTIAL
- Cohort: single-symbol DOT (DOTUSDT); /050 IS Sharpe Δ +1.1162 vs DOT baseline
- Axis: VALIDATION sub-type — same feature (`dot_vs_btc_ret_ratio_30`), same cohort, drop
  vol-spike regime gate (0% fire rate in /050 IS and OOS — mechanically INERT)
- Seeds: --seeds 4 (outer seed offsets 0/5/10/15 from ENSEMBLE_SEEDS roster)
- Feature stack: V1_FEATURE_COLUMNS_PRUNED unchanged at 46 cols
- Same n_trials=18, ENSEMBLE_SIZE=3 as /050 (apples-to-apples comparison)

---

## ML Perspective

Per-seed stability is the load-bearing metric for multi-seed validation, not the mean alone.

With DOT's small IS cohort (~125 trades at /050), the n_trials=18 Optuna budget sits near TPE
warm-up saturation (~15-20 random trials before exploitation starts). This means each outer seed
run is partially determined by its random warm-up phase — per-seed IS Sharpe could span
±0.5 to ±1.0 around the mean even with genuine signal.

The actionable threshold:
- **Mean IS Δ ≥ +0.50 with max-min stability ≤ +1.0** → feature is genuine signal
- Mean IS Δ < +0.50 → LOTTERY-CONFIRMED-NEGATIVE; /050 was a favorable basin at seed=42
- Max-min > +1.0 even with positive mean → BASIN-LOTTERY; signal not reliable for CONFIRMATION

Outer seed 0 (offset=0) maps to ENSEMBLE_SEEDS starting at index 0 (= canonical seeds
[42, 123, 456]) — this should closely replicate /050's single-seed result (within Optuna
stochasticity at n_trials=18). If it diverges by more than ±0.10, there is an implementation
error.

---

## Top 3 Recommendations

### Rec 1 — Log per-seed individual IS/OOS Sharpe; variance is more diagnostic than mean

The runner already emits per-seed outputs. For brief Section 2, QR must produce a table:

| seed_offset | IS Sharpe | IS Δ | OOS Sharpe | OOS Δ | IS trades |
|---|---|---|---|---|---|

The coefficient of variation (std / |mean|) across seeds IS the signal-reliability test. Mean
lift of +0.70 with std of +0.60 is less convincing than mean +0.55 with std of +0.10.

### Rec 2 — Watch for seed=42 outlier (BASIN-LOTTERY fingerprint)

If seeds [5, 10, 15 offsets] produce mean IS Δ < +0.50 while seed offset 0 stayed at +1.12,
that is the BASIN-LOTTERY fingerprint from /013 + /026 history: Optuna at n_trials=18 on a
small cohort can find a lucky local optimum at the canonical seed that does not generalize.

Pre-register F2 falsifier: if max per-seed IS Δ - min per-seed IS Δ > +1.0 → BASIN-LOTTERY
regardless of mean. The QR should check whether the outlier seed is offset=0.

### Rec 3 — Trade-rate floor at mean: if any single seed has < 40 IS trades, investigate

Average IS trade count across the 4 seeds; if any single seed has < 40 IS trades, that seed's
Optuna run may have found a precision-maximizing solution that simply fires rarely. A Sharpe
from 38 trades is not the same distribution as one from 125 trades. Flag, do not auto-discard
— but note in Section 2.

---

## Prior Distribution (5 outcome bands)

| Band | Prior | Trigger |
|---|---|---|
| PROMISING-SPECIALIST-CONFIRMED | 25% | Mean IS Δ ≥ +1.23; all seeds ≥ +0.70 |
| PROMISING-PARTIAL-CONFIRMED | 30% MODAL | Mean IS Δ ∈ [+0.50, +1.23); stability max-min ≤ +1.0 |
| LOTTERY-CONFIRMED-NEGATIVE | 25% | Mean IS Δ < +0.50 (seed=42 was favorable basin) |
| BASIN-LOTTERY | 15% | High stability variance max-min > +1.0; signal unreliable |
| REGRESSION | 5% | Mean IS Δ < 0; seeds actively harm DOT |

**Modal outcome: PROMISING-PARTIAL-CONFIRMED (30%).** Feature importance rank 8/45 at /050
suggests real split-budget allocation, not a noise-fit artifact. But single-seed at n_trials=18
on a small cohort has sufficient noise to place LOTTERY-CONFIRMED-NEGATIVE as the second most
likely outcome (25%). The BASIN-LOTTERY risk is real: DOT's thin per-fold coverage amplifies
seed sensitivity.

---

## Risk Flags

- Single-seed Optuna at n_trials=18 has high variance; per-seed IS Sharpe Δ from -0.3 to +0.3
  relative to the mean is normal Monte Carlo noise — not a flag by itself
- The QUESTION is whether the mean lift > +0.50 clears the noise floor, not whether every
  individual seed is positive
- Outer seed offsets [5, 10, 15] use inner ensemble seeds [2002, 3003, 4004], [4004, 5005, 6006],
  [6006, 7007, 8008] — these have never run on the DOT-only single-cohort setting; treat their
  outputs as draws from an unknown prior

---

## What I Do NOT Recommend

- No HP changes: this is a seed-validation run, HP search space must be identical to /050
- No seed-conditional Optuna budget tweaks: adjusting n_trials per seed destroys the
  apples-to-apples comparison and introduces a confound into the multi-seed mean
- No feature changes: any addition or removal destroys the comparison baseline
- No new risk gate: the vol-spike gate was INERT (0% fire rate); adding a replacement is a
  /052+ axis decision, not part of /051's validation mandate

---

## Closing

The multi-seed mean Δ ≥ +0.50 is the cleanest test of /050's signal validity.
PROMISING-PARTIAL-CONFIRMED at /051 → DOT enters the /055 CONFIRMATION roster.

— Phase 4.5 advisor authored 2026-06-01 (iteration-v1/051 multi-seed re-validation framing)
