# LightGBM Master Advisor — iter-v1/052 — Phase 4.5 (Pre-Design)

## Context Read

- Track: v1; cycle-6 EXP-7/10 — first BTC-specialist EXPLORATION
- Cohort: single-symbol BTC (BTCUSDT); BASELINE_V1 BTC IS Sharpe −0.85; 113 IS trades / 36 OOS trades
- Axis: `feature-family` — ADD `btc_funding_rate_8h_impulse` + `btc_funding_spread_30_90`
  (both non-OHLCV-derived, funding-rate primitive class; 46 → 48 cols)
- Precedent: /051 PROMISING-PARTIAL-CONFIRMED on DOT (multi-seed mean IS Δ +0.9945).
  DOT is in roster. Per-symbol architecture mandate from /049 closeout is ACTIVE.
- Seeds: single-seed=42 (EXPLORATION cadence per brief template; multi-seed mandatory
  only on PROMISING closeout per LM Master Rec 3 pre-registration pattern at /050)
- Feature stack: `V1_FEATURE_COLUMNS_PRUNED` 46 → 48 cols after additions

---

## ML Perspective

BTC IS Sharpe −0.85 is the worst per-symbol baseline in the v1 universe (worse than DOT −1.23
is only because DOT counts per specialist head; BTC-only specialist IS Sharpe ≈ −0.85 for the
subset of 113 Model A trades attributable to BTC). With 113 IS trades the sample is borderline
for LightGBM's depth-3/4 tree estimation — the flip-positive threshold is IS Δ ≥ +0.85 (i.e.
IS Sharpe > 0.0) which requires the new features to contribute on almost every trade.

**Orthogonality argument.** Both new features derive from `funding_rate` (already present as
`funding_rate_zscore_30` and `funding_rate_zscore_90`). They are algebraically dependent on
the same primitive — the impulse is a rolling-std-normalized first difference, the spread is
the zscore_30 minus zscore_90. The EDA-informational rule (`bf2c812`) means IC against
existing columns does NOT gate the backtest, but the correlation structure is still ML-relevant:
LightGBM at n_trials=18 with `colsample_bytree` sampling will encounter all three funding
features in the same candidate split set; the marginal columns land in the model only if they
explain variance NOT already captured by the parent features.

**Mechanism differentiation.** Despite shared primitive, the two new features target distinct
regimes:
- `btc_funding_rate_8h_impulse` is a **shock detector** — spikes when funding rate changes
  faster than its 90-bar rolling std (carry-trade unwind signal per BIS WP 1087 2025).
  Effective in volatile, crowded-carry environments.
- `btc_funding_spread_30_90` is a **term-structure slope indicator** — positive when
  short-term funding premium exceeds long-term expectation (divergence = sentiment heating).
  Effective in slowly-building positioning phases, not spikes.

The two mechanisms are complementary: impulse fires infrequently but sharply; spread is
smoother and more regime-persistent. Adding both simultaneously is within the single-feature
discipline IF they are treated as a single compound axis (same primitive class, complementary
transforms). LM Master flags this as an ACCEPTABLE compound if brief Section 3 commits to
keeping both or reverting both (no partial-revert).

---

## Top 3 Recommendations

### Rec 1 — Treat impulse + spread as one indivisible axis; pre-register both-or-neither revert rule

The two features are algebraically derived from the same `funding_rate` primitive. Adding one
without the other leaves a partial axis that is harder to attribute at closeout. Brief Section 3
MUST declare: "if backtest closes NEGATIVE, BOTH features are reverted; no partial keep is
permitted." This prevents post-hoc rationalization where one feature is kept because OOS
happened to be positive despite IS Sharpe miss.

Attribution check at closeout: compare `btc_funding_rate_8h_impulse` importance rank vs
`btc_funding_spread_30_90` importance rank in the IS feature_importance.csv. If one ranks
outside top-20 and the other is top-5, the attribution diverges and a follow-up single-feature
EXPLORATION at /053 or /054 is warranted (NOT a free-form keep decision at /052 closeout).

### Rec 2 — Monitor trade-rate floor with extra vigilance; BTC IS 113 trades is borderline

BASELINE_V1 Model A (BTC+ETH pooled) generated 113 BTC trades in IS (36 OOS). Under the
BTC-only specialist architecture at /052, the walk-forward training window and labeler config
are identical, but the LightGBM head sees ONLY BTC rows. Two risks:

a) **R3 OOD gate**: if the BTC-only R3 gate calibrates its covariance on a smaller feature
   space, the Mahalanobis cutoff could eliminate a disproportionate share of BTC trades.
   Pre-register: IS BTC trades ≥ 50 as gate pass; < 50 = trade-rate FAIL regardless of IS
   Sharpe.

b) **HP regularization side-effect**: at n_trials=18 with 48 features, Optuna will sample
   regularization hyperparameters (min_child_samples, lambda_l1, lambda_l2) that may impose
   higher pruning on a small-cohort single-symbol head vs the pooled Model A. Pre-register in
   brief Section 5 the observed IS trade count and flag if it drops below 80 (early warning
   before the 50-floor is hit).

### Rec 3 — Run single-seed=42 first; defer multi-seed conditional on PROMISING closeout

The cycle-6 EXPLORATION cadence is single-seed. Given BTC's negative IS history and the
algebraic overlap with existing funding features, multi-seed validation at /052 itself is
premature. The correct gate:
- If /052 closes PROMISING (IS Δ ≥ +0.50 OR IS Sharpe flips positive): MANDATE multi-seed
  re-validation at /053 using seeds [123, 456, 789] (disjoint from seed=42 inner pool).
- If /052 closes NEGATIVE-CLEAN or LEARNED-NEG: revert both features; route /053 per
  orchestrator (LTC-specialist or ETH-specialist by cadence).
- If /052 closes NEGATIVE-NO-EFFECT: revert both features (importance < top-20 on both);
  log pattern match to /049 (pooled-head inert) for meta-level diagnostics.

This conditional structure was proven effective at /050→/051 (DOT specialist). Adopting
it now is the correct prior-informed discipline, not conservatism.

---

## Prior Distribution (8 bands)

| Verdict | Probability | Rationale |
|---|---|---|
| PROMISING (IS Δ ≥ +0.50, Sharpe flip) | **35%** (MODAL) | BTC funding edge documented in BIS WP 1087 2025; impulse + spread are non-OHLCV at primitive class; BTC-only cohort eliminates pooled-head destructive integration mode from /049 |
| NEGATIVE-no-effect (importance < top-20, flat Sharpe) | **30%** | Algebraic overlap with existing `funding_rate_zscore_30/90` leaves minimal marginal IC at colsample_bytree; at n_trials=18 the Optuna search may not allocate splits to correlated relatives |
| NEGATIVE-clean (importance PASS but IS Δ < −0.05) | **15%** | Small cohort (113 IS trades) at depth-3/4 with 48 features; Optuna regularization may impose high min_child_samples eliminating BTC signal |
| LEARNED-NEG (IS Sharpe appears positive but OOS collapses > −0.50) | **10%** | Funding-rate impulse is a discontinuous feature (most bars near-zero, rare spike events); LightGBM may overfit the IS spike events that do not recur OOS |
| PROMISING-PARTIAL (IS Δ ∈ [+0.05, +0.50)) | **5%** | Marginal lift below flip-positive threshold; possible if spread lands but impulse is INERT |
| Other (crash / MaxDD explosion / data bug) | **5%** | Funding cache miss or std=0 division edge case in impulse formula |

---

## Risk Flags

**Flag A — Algebraic overlap with existing funding features.** `btc_funding_rate_8h_impulse`
is a function of `funding_rate.diff()` and `funding_rate.rolling(90).std()`. Both primitive
inputs are already partially captured by `funding_rate_zscore_30` and `funding_rate_zscore_90`.
IC between the new features and the existing ones is expected ~0.30–0.45. Under the EDA-
informational rule this does NOT block the backtest, but the ML implication is that Optuna at
n_trials=18 may route all split budget to the existing features and treat the new columns as
redundant. Feature importance rank is the diagnostic: top-15 = learned, outside top-24 = INERT.

**Flag B — `rolling(90).std()` denominator zero-crossing risk.** At the very start of the IS
window (first 90 bars of 2023-03-24 onward), the 90-bar rolling std is undefined or near-zero.
The formula `fr_diff / fr_diff.rolling(90).std()` will produce NaN or inf for the first ~90
bars. The feature engineer MUST add `np.where(std > 1e-8, fr_diff / std, 0.0)` or equivalent
guard. Brief Section 3 must confirm this edge case is handled; QE must verify in code review.

**Flag C — Single-seed=42 EXPLORATION reads as favorable or unfavorable basin for BTC.**
BTC at seed=42 produced the canonical Model A result. Under a BTC-ONLY head at seed=42, the
Optuna trajectory is different — seed=42 initializes the LightGBM inner ensemble with the same
seed but trains on a smaller single-symbol dataset. The per-seed IS result is NOT comparable to
/050 DOT seed=42. Do not interpret a /052 NEGATIVE result at seed=42 as "BTC is fundamentally
negative" — that requires multi-seed confirmation per the /050→/051 precedent.

**Flag D — BTC-only R3 calibration.** Model A calibrated R3 on the BTC+ETH feature
distribution (258 combined rows per walk-forward train cell). A BTC-only head calibrates R3
on ~113 rows per cell. The Mahalanobis covariance estimate is noisier at smaller N; if the R3
cutoff=0.70 is retained unchanged, BTC-only R3 may over-fire (too many OOD rejections) or
under-fire (noisy covariance admits OOD samples). Brief Section 6 must note the R3
recalibration risk; if fire rate IS > 40%, the R3 cutoff is likely miscalibrated for the
smaller cohort.

---

## Closing

This is the first BTC-specialist EXPLORATION in cycle-6. The per-symbol architecture pivot
from /049 closeout has already paid off at DOT (/050 PROMISING-PARTIAL, /051 PARTIAL-CONFIRMED).
BTC is the largest negative drag in BASELINE_V1 IS (−37.28% net PnL). The funding-impulse +
funding-spread axis is the most academically-grounded non-OHLCV feature class available for
BTC in the cycle-6 feature-family rotation (BIS WP 1087 2025; Adrian/Brunnermeier liquidity
spiral framework; structurally orthogonal to LINK/LTC/DOT feature choices).

The MODAL verdict is PROMISING at 35%, meaning a BTC-specialist head with funding features
is expected to flip IS Sharpe positive in slightly over a third of single-seed runs. The
NEGATIVE-no-effect at 30% is the second-most-likely outcome and is not a design failure —
it would confirm that funding impulse collapses to the existing zscore features at LightGBM
depth-3/4 under colsample_bytree, which is itself a useful empirical result for cycle-7.

Proceed with single-seed=42. Multi-seed conditional on PROMISING closeout per Rec 3.
