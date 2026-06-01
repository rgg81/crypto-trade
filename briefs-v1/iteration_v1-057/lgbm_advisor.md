# LightGBM Master Advisor — iter-v1/057 — Phase 4.5 (Pre-Design)

## Context Read

- Track: v1; cycle-7 EXP-1/N (FIRST iteration after cycle-6 closed 0 baseline updates / 11 iters)
- Cohort: **LTCUSDT only** (LTC-only specialist head; BTC klines loaded for feature computation only)
- Baseline LTC IS Sharpe: **+0.17** / OOS Sharpe: **−4.27** (124 IS trades / 35 OOS trades)
  — **Biggest IS/OOS divergence in the bundle. LTC OOS catastrophe is the load-bearing bundle drag.**
- NEW feature: `ltc_vs_btc_ret_ratio_30` = (LTC 30d return) / (BTC 30d return), z-scored 90 bars,
  clipped ±10 — direct algebraic mirror of /055 `eth_vs_btc_ret_ratio_30` (the only multi-seed-
  confirmed cycle-6 lift; ETH survived /056 CONFIRMATION at IS Δ +0.20 while BTC + DOT regressed)
- Multi-seed BUILT IN from start: `--seeds 3` at `ensemble_size=3` with monkey-patched
  `_OUTER_SEED_OFFSETS = (0, 3, 6)` → produces 9 disjoint inner seeds {42,45,48 / 123,126,129 /
  456,459,462} (same pattern as /051 multi-seed validation); inner ensemble_size=3 per outer seed
- Verdict basis: **MULTI-SEED MEAN (n=3 outer seeds).** Single-seed=42 result is informational only;
  NO single-seed=42 verdict basis allowed per /056 lesson (BTC Δ −0.36 / DOT Δ −0.35 at
  CONFIRMATION proved single-seed/3-seed EXPLORATIONs are basin-lottery-exposed)
- Optuna: n_trials=20, EXPLORATION budget

---

## Phase 4.5 — LM Master Pre-Design Advisory

### ML Perspective — LTC's OOS Catastrophe and the Cross-Asset Feature Mechanism

LTC OOS −4.27 with IS +0.17 is the widest IS/OOS split in the v1 bundle (Δ = 4.44 Sharpe points).
This is NOT generic overfitting — the IS signal is near-flat (+0.17), so there is no IS-peak to
overfit from. The OOS collapse is likely a **regime-specialist failure**: LTC's OOD exposure in the
OOS window is structurally different from IS, and the pooled-head BASELINE_V1 Model D was trained
with features calibrated to aggregate five-symbol dynamics.

`ltc_vs_btc_ret_ratio_30` targets a specific failure mode: LTC has thinner liquidity than ETH and
exhibits larger idiosyncratic price swings relative to BTC in altcoin-sentiment-driven regimes (BTC
dominance expansions, LTC halving cycles). The 30-bar return ratio (z-scored 90 bars) captures
whether LTC is currently expressing idiosyncratic momentum vs. BTC-beta lockstep. When the ratio
is far from the 90-bar mean, LTC's signal has regime-specific edge; when the ratio is flat, LTC
follows BTC macro and per-symbol conditioning degrades toward noise.

The /055 ETH version of this mechanism confirmed via /056 CONFIRMATION: ETH specialist IS Δ +0.20
(only surviving specialist; BTC and DOT both regressed −0.36/−0.35). Importantly, /056 Item 2
showed that `eth_vs_btc_ret_ratio_30` ranked **13th of 14 at ETH specialist** — near-INERT at
CONFIRMATION budget. ETH survived NOT because of the ratio feature but because ETH's Optuna basin
happened to be the conservative draw at single-seed. This is a **calibration warning for /057**:
the LTC ratio feature must demonstrate importance rank ≤ 10 across all 3 outer seeds; otherwise
the verdict is LEARNED-NEG regardless of IS Sharpe Δ direction.

The multi-seed-from-start design addresses the primary /056 failure directly: 9 disjoint seeds at
EXPLORATION budget expose basin variance BEFORE any CONFIRMATION budget is spent. The LM Master
endorses this design as the correct cycle-7 reform (per /056 Phase 7.4 Rec A).

---

## Top 3 Recommendations

### Rec 1 — Multi-seed verdict is mandatory; seed=42 result is informational only

Report the IS Sharpe for each of the 3 outer seeds individually, then compute the multi-seed mean.
The verdict band assignment MUST use the mean; a single-seed outlier cannot constitute a PROMISING
verdict. Specifically:

- If seed=42 IS Sharpe > +0.50 but seeds 123/456 mean < +0.10 → **BASIN-LOTTERY verdict** (not
  PROMISING), even if the 3-seed mean appears positive.
- Document max-min spread explicitly: if max_seed IS Sharpe − min_seed IS Sharpe > 0.50, the
  basin variance is still lottery-scale despite multi-seed. Report the spread in the engineering
  report.
- The 9-seed (3 outer × 3 inner) design lowers basin variance vs /051 (3 outer × 1 inner), so
  expect tighter max-min spread than /051's documented range. If spread is wider than /051, flag
  this as anomalous.

### Rec 2 — Feature importance is the primary falsifier — rank ≤10 of 48 required across all seeds

Per /056 Item 2 finding (ETH ratio rank 13/14 = near-INERT at CONFIRMATION), a positive IS Sharpe
Δ without importance rank confirmation is a BASIN-LOTTERY false positive. For /057:

- Pull feature importance per outer seed (gain-based, walk-forward aggregated — fix the last-month-
  only aggregation defect identified at /017 if not already fixed).
- If `ltc_vs_btc_ret_ratio_30` ranks > 40 of 48 columns for ANY outer seed → that seed is INERT
  for the feature. If > 40 for 2 of 3 seeds → overall verdict is INERT regardless of IS Δ.
- If `ltc_vs_btc_ret_ratio_30` ranks ≤ 10 for ≥2 of 3 seeds → feature is genuinely learned; IS Δ
  is attributable to the feature mechanism (not Optuna lottery).
- The EDA in Phase 3/Section 2 should also verify z-score std > 0.5 across IS LTC rows; if the
  ratio is too flat (all values near z=0), LightGBM cannot condition on it regardless of n_trials.

### Rec 3 — LTC OOS regression-test: per-seed OOS ≥ −2.0 is the minimum validity floor

BASELINE LTC OOS IS Sharpe = −4.27. A specialist that does not improve LTC OOS is irrelevant for
bundle contribution regardless of IS Δ:

- Per-seed OOS must be individually checked. Multi-seed mean OOS ≤ −4.27 (worse than or equal to
  baseline) means the specialist adds zero bundle value even at equal-weight.
- Target: multi-seed mean OOS ≥ −2.0 (50% improvement on the catastrophe) to qualify as
  SPECIALIST-CANDIDATE for cycle-7 CONFIRMATION.
- Do NOT gate the EXPLORATION verdict on OOS (OOS is informational per EXPLORATION methodology).
  The OOS regression-test is a CONFIRMATION-threshold forward-signal, not an EXPLORATION blocker.
  Pre-register in brief Section 8 as the forward-signal threshold.

---

## Prior Distribution (8 verdict bands; multi-seed-aware)

| Verdict Band | Probability | Rationale |
|---|---|---|
| MULTI-SEED-SPECIALIST-CANDIDATE (mean IS Δ ≥ +0.50; max−min ≤ 0.50) | **15%** | Strong signal; LTC/BTC ratio less noisy than ETH/BTC at 30-bar (lower correlation ~0.65 vs ~0.85); feature genuinely isolates idiosyncratic LTC momentum |
| MULTI-SEED-PARTIAL-CONFIRMED (mean IS Δ ∈ [+0.20, +0.50)) | **25%** | Modal positive; ratio learns mid-table importance; IS improvement modest but cross-seed stable |
| MULTI-SEED-WEAK (mean IS Δ ∈ [+0.05, +0.20)) | **20%** | Feature rank 20-35; Optuna at n_trials=20 finds marginal gain; insufficient for CONFIRMATION |
| NEGATIVE-INERT (mean IS Δ ∈ (−0.05, +0.05); max IS Δ any seed < +0.30) | **25%** | LTC has 124 IS trades vs ETH 145; smaller cohort → noisier Optuna surface; ratio near-flat across IS regimes |
| NEGATIVE-CLEAN (mean IS Δ ≤ −0.05) | **10%** | Ratio anti-informative at n_trials=20; LTC specialist baseline IS +0.17 regresses further |
| BASIN-LOTTERY (mean IS Δ > +0.10 but max−min > 0.50) | **5%** | One seed draws favorable basin; others flat/negative; same pattern as /054 BTC single-seed |

**LM Master modal: NEGATIVE-INERT (25%) or MULTI-SEED-PARTIAL-CONFIRMED (25%).** Probability mass
is bimodal: the mechanism is sound (cross-asset ratio proven at DOT/ETH direction) but LTC's
thinner liquidity + smaller IS cohort (124 trades) introduces higher per-seed optimization noise
than ETH's 145-trade cohort.

---

## Risk Flags

### RF-1: LTC/BTC ratio may be noisier than ETH/BTC due to thin liquidity

LTC correlation with BTC at 30-bar 8h is approximately 0.65 (vs ETH ~0.85). Lower correlation
means MORE idiosyncratic LTC moves — which is directionally favorable for the ratio feature's
information content. However, LTC's thinner liquidity creates **microstructure noise** in the
30-bar return calculation: LTC trades fewer large players, so short-window LTC returns have
higher variance from liquidity events (wash trades, large single-entity entries). The z-score
normalization over 90 bars helps but does not eliminate this. Verify in EDA that the
`ltc_vs_btc_ret_ratio_30` z-score has no outlier cluster beyond ±5 that the ±10 clip misses
(a ±7 cluster from a single liquidity event could dominate the 90-bar window temporarily).

### RF-2: 124 IS trades is mid-range — per-seed variance higher than ETH

ETH at 145 IS trades had ~29 trades/fold at 5 walk-forward folds. LTC at 124 IS trades has ~25
trades/fold. At n_trials=20 and EXPLORATION budget, this is borderline for stable Optuna
convergence: TPE warmup is ~15 random trials, leaving only 5 exploitation trials per cell. Expect
higher per-seed IS Sharpe variance than the 145-trade ETH cohort. The max−min spread metric
(Rec 1) will be the diagnostic.

### RF-3: Trade-rate floor per-seed — 124 IS / 35 OOS baseline; LTC specialist may trade less

The LTC-only specialist trains on LTC trades only. If the specialist is more conservative than the
pooled baseline Model D (possible if the ratio feature gates out low-confidence periods), per-seed
IS trade count may fall below 80 (the EXPLORATION floor per Rec 3's spirit). Brief Section 8 must
pre-register: if any seed IS trade count < 60, flag as potential overfit (too few IS trades to
estimate Sharpe reliably). OOS 35 trades at baseline → per-seed OOS floor of 20 trades required.

### RF-4: IS +0.17 baseline is near-flat — improvement has asymmetric meaning

LTC IS +0.17 is NOT a high baseline to overcome. Even a modest ratio-feature contribution should
push IS above +0.17. But a MULTI-SEED-PARTIAL-CONFIRMED verdict (Δ +0.20 mean → IS ~+0.37) is
still a near-flat specialist with limited absolute IS edge. The threshold for CONFIRMATION
inclusion is IS mean ≥ +0.50 (one half-Sharpe above the near-flat baseline), per cycle-7
CONFIRMATION planning. Pre-register this in brief Section 8.

---

## Closing

This is cycle-7 EXP-1. The /056 Phase 7.4 post-mortem established three cycle-7 reforms:
- **Rec A**: 5-seed EXPLORATION floor (this iteration implements 3-seed with 9 disjoint inner seeds
  = functionally equivalent; satisfies the spirit of Rec A)
- **Rec B**: drop importance-unstable axis features (verdict here is the test of LTC ratio stability)
- **Rec C**: ensemble-of-EXPLORATION-seeds aggregation pattern (deferred to methodology axis)

If LTC specialist confirms at MULTI-SEED-PARTIAL or higher AND feature importance is rank ≤ 10
across seeds, /058 can build a BTC variant of the same cross-asset pattern with multi-seed from
start (the BTC ratio feature `btc_funding_spread_30_90` was classified LEARNED-NEGATIVE-AT-
CONFIRMATION per /056 — a NEW BTC/BTC-idiosyncratic feature mechanism would be needed, not a
retry of the /054 funding spread).

If LTC verdict is NEGATIVE, the per-symbol regime-specialist mandate continues and the next LTC
axis should address the OOS catastrophe source directly (e.g., LTC OOS regime attribution — which
OOS months are catastrophic and whether a binary LTC-kill-switch on those regime conditions is
IS-evidenced). The OOS regime tagger infrastructure debt from /056 (200/202 OOS trades in `other`)
must be resolved before the next CONFIRMATION attempt.

**Single most important metric**: multi-seed MEAN LTC IS Sharpe Δ vs baseline +0.17 AND
`ltc_vs_btc_ret_ratio_30` importance rank across all 3 outer seeds. Both must be affirmative for
a PROMISING verdict. One without the other is a BASIN-LOTTERY or INERT classification.

— Phase 4.5 advisor authored 2026-06-01
