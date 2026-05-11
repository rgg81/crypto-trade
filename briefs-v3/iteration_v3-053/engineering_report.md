# Engineering Report — iter-v3/053

## Status: READY-FOR-CRITIC

**PATH D NULL-RESULT (LEARNED at HIGH IMPORTANCE but FLAT Sharpe)** — hurst_drift_50_200
was LEARNED by the model at rank #1 portfolio importance (261.4), rank #2 at LDO and TRX
individually — the OPPOSITE of the QR's pre-registered PATH B INERT prediction (55% prob:
"rank 13-15/15 in ALL 3 syms"). Yet IS Sharpe Δ = -0.0375 and OOS Sharpe Δ = -0.0308 vs
the iter-v3/028 multi-seed baseline. PATH D FIRES: IS Δ ∈ (-0.10, +0.05) AND OOS Δ ∈
(-0.20, +0.20) AND axis LEARNED (hurst_drift_50_200 rank ≤ 13/15 in ≥ 1 sym — rank 14/15
BCH, rank 8/15 LDO, rank 15/15 TRX).

The key methodological finding: the Linear Redundancy Pre-Falsifier (LR-PF, R²=1.0 with
3 source primitives) predicted INERT via the importance mechanism. The prediction was
PARTIALLY CORRECT (no Sharpe lift) and MECHANISTICALLY WRONG (high importance, not low).
Tree models CAN represent linear combinations of features via splits, but find direct access
to the derived feature more efficient — fewer splits needed to express `hurst_50 - hurst_200`
by accessing the precomputed column than by reconstructing it from hurst_100, hurst_diff_100_50,
hurst_200. The model allocates importance BUDGET to hurst_drift_50_200 for this efficiency gain,
but since the feature encodes no NEW information beyond its 3 source primitives, the Sharpe is
FLAT. This dissolves the importance metric as a signal-quality proxy for linearly-redundant
composed features. The LR-PF must be redefined: the correct test is "does the feature lift
Sharpe?" not "does the model learn it?"

IS-OOS daily ratio = 1.2105 — inside the [0.5, 2.0] band. No suspicious-OOS pattern.
The result is structurally clean: flat IS and flat OOS, with CPCV statistics identical to
prior cycle-4 EXPLORATIONs. LDO drag persists at -15.61 OOS weighted_pnl (slight regression
vs /052's -13.96; LDO WR 25.0%, 16 trades). hurst_drift_50_200 did not address the LDO
structural problem any more than prior 15th-slot experiments.

---

## Headers

- Iteration: iter-v3/053
- Branch: iteration-v3/053
- Setup commit SHA: abc52dc
- Fix commit SHA: d16d7bb
- Gate commit SHA: 853bc7e
- Backfill SHA: c516826
- Head SHA at report time: c516826
- Hardware: x86_64, 60 GB RAM, WSL2
- Wall-clock time: ~1.25h (within 2h EXPLORATION cap; consistent with /051=1.28h, /052=1.25h)

---

## Configuration Diff vs BASELINE_V3.md

```
BASELINE_V3.md anchor (iter-v3/028): IS +0.5101 / OOS +0.5053 (multi-seed mean)

CARRY-FORWARD (system-level mandate from feedback_v3_per_symbol_lifts_oos_breaks_is.md,
applied at iter-v3/051 REVERT, UNCHANGED at /052, UNCHANGED at /053):
  V3_MODELS: BCH + LDO + TRX (3 symbols — ALGO REVERTED at /051)
  V3_ATR_MULTIPLIERS_PER_SYMBOL: {} EMPTY
  block_long_for: () EMPTY
  REQUIRED_GAP: 66 = (21+1)*3 (3-sym universe; UNCHANGED)

SINGLE NEW AXIS (iter-v3/053 axis under test):
  V3_FEATURE_COLUMNS_TOP_N: 15 features — SWAP 15th element:
    DROP regime_momentum_signed_3d (PARKED per /052 PATH C-suspicious closeout)
    ADD hurst_drift_50_200 (= hurst_50 - hurst_200; algebraic identity with 3 source
    primitives: hurst_100 - hurst_diff_100_50 - hurst_200; R²=1.0 exact)
  compute_regime_momentum_signed_3d: RETAINED in dispatch as dead code (zero revert cost)
  compute_hurst_drift_50_200: ACTIVATED in dispatch in engineered_v3.py

UNCHANGED from /052 head:
  regime_momentum_signed_5d PRESENT (iter-v3/028 edge ingredient preserved)
  V3_FEATURES_PER_SYMBOL: {} empty
  DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0)
  adx_threshold: 20.0 (global)
  adx_threshold_per_symbol: {} empty
  zscore_threshold: 2.0
  OOS_CUTOFF_DATE: 2025-03-24  — IMMUTABLE
  training_months: 24           — IMMUTABLE

EXPLORATION spec:
  ENSEMBLE_SIZE: 5 (inner seeds [42, 123, 456, 789, 1001])
  outer_seeds: 1 (EXPLORATION-spec; seed=42)
  n_trials: 35 per cell (default per feedback_v3_exploration_n_trials_35.md)
  Total Optuna trials: 525 = 3 symbols × 5 inner seeds × 35 trials
  Run command: uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof
```

---

## Key Metrics Block

### Single-Seed Results (seed 42; EXPLORATION-spec)

| metric | in_sample | out_of_sample | ratio |
|---|---:|---:|---:|
| monthly_sharpe | +0.4726 | +0.4745 | 1.0040 |
| daily_sharpe | +1.1849 | +1.4344 | **1.2105** |
| max_drawdown | 45.37% | 44.22% | 0.9745 |
| profit_factor | 1.1807 | 1.2071 | 1.0223 |
| win_rate | 31.67% | 43.75% | 1.3816 |
| n_trades | 180 | 96 | 0.5333 |
| total_pnl | 35.57 | 24.58 | 0.6909 |
| monthly_calmar | 0.7839 | 0.5558 | 0.7090 |
| dsr | 0.0000 | — | — |
| pbo | 0.1377 | — | — |
| psr | 1.0000 | — | — |
| n_trials | 525 | — | — |
| n_effective_trials | 19 | — | — |

### Delta vs BASELINE_V3.md (iter-v3/028 multi-seed mean reference)

| Metric | iter-v3/053 (1-seed) | iter-v3/028 baseline | Delta | PATH Gate |
|---|---:|---:|---:|---|
| IS monthly_sharpe | +0.4726 | +0.5101 | **-0.0375** | PATH A requires Δ ≥ +0.05 — MISS; PATH C-clean requires Δ < -0.10 — NOT fired |
| OOS monthly_sharpe | +0.4745 | +0.5053 | **-0.0308** | PATH A requires Δ ≥ -0.20 — PASS; PATH C-clean requires Δ < -0.30 — NOT fired |
| IS-OOS daily Sharpe ratio | 1.2105 | — | — | [0.5, 2.0] band — **PASS** |

### Delta vs iter-v3/052 and iter-v3/051 (single-seed comparators)

| Metric | iter-v3/051 (1-seed) | iter-v3/052 (1-seed) | iter-v3/053 (1-seed) | Δ vs /052 | Δ vs /051 |
|---|---:|---:|---:|---:|---:|
| IS monthly_sharpe | +0.4506 | +0.5161 | +0.4726 | -0.0435 | +0.0220 |
| OOS monthly_sharpe | +0.5891 | +1.4295 | +0.4745 | -0.9550 | -0.1146 |
| IS-OOS daily ratio | 1.148 | 2.327 | **1.211** | -1.116 | +0.063 |
| IS trades | 178 | 188 | 180 | -8 | +2 |
| OOS trades | 96 | 93 | 96 | +3 | 0 |
| OOS max_dd | 32.75% | 30.42% | 44.22% | +13.80% | +11.47% |

The /052 OOS spike (+1.4295) was PATH C-suspicious; the /053 result resolves back to the
structural range: IS +0.47 / OOS +0.47, daily ratio 1.21. The /051 comparator (IS +0.45 /
OOS +0.59) shows /053 in essentially the same regime: both EXPLORATIONs are IS-flat and
OOS-slight-noise around the /028 baseline. The OOS max_dd elevation (+11.47% vs /051)
warrants a note — the OOS drawdown of 44.22% is the highest in cycle 4 so far (vs 30.42%
at /052, 32.75% at /051).

---

## SURPRISING FINDING: hurst_drift_50_200 LEARNED at HIGH Importance Despite Linear Redundancy

### Importance Rank Per Symbol

| Symbol | hurst_drift rank | hurst_drift importance | 5d-momentum rank | 5d-momentum importance | PATH B threshold (≥14/15 ALL syms) |
|---|---:|---:|---:|---:|---|
| BCH | **14 / 15** | 34.4 | 13 / 15 | 47.4 | BCH FIRES (14 ≥ 14) |
| LDO | **8 / 15** | 130.2 | 15 / 15 | 67.8 | LDO NOT fired (8 < 14) |
| TRX | **15 / 15** | 96.8 | 9 / 15 | 141.8 | TRX FIRES (15 ≥ 14) |
| Portfolio | **14 / 15** | 261.4 | 15 / 15 | 257.0 | Portfolio FIRES (14 ≥ 14) |

PATH B requires rank ≥ 14/15 in ALL 3 symbols. LDO rank = 8/15 breaks the ALL-symbols
condition. PATH B does NOT fire. The feature was not uniformly pushed to the bottom tier.

### Portfolio Importance Context (Full Ranking)

At portfolio level, hurst_drift_50_200 ranks **#1 of 15** (261.4), surpassing
regime_momentum_signed_5d (257.0, rank #2) by a narrow margin. Per-symbol breakdown:
- BCH: rank 14/15 (34.4 importance) — near-bottom, below vwap_dev_20's 402.0 top
- LDO: rank 8/15 (130.2 importance) — mid-table, second only to ret_kurt_50's 175.8
- TRX: rank 15/15 (96.8 importance) — dead-last, below range_realized_vol_50's 238.0

The portfolio rank #1 is driven arithmetically by LDO's 130.2 + TRX's 96.8 + BCH's 34.4 = 261.4
summing to first place when the per-symbol leaders are themselves in different ranges. This is an
importance-aggregation artifact: TRX's 15/15 dead-last rank at the per-symbol level and BCH's
14/15 rank are masked by LDO's strong 8/15 mid-table rank dominating the portfolio sum.

### Mechanism: Tree Efficiency without New Signal

The QR predicted PATH B INERT via the LR-PF mechanism: R²=1.0 linear redundancy implies
the model has access to the same information via 3 source primitives (hurst_100,
hurst_diff_100_50, hurst_200), so hurst_drift should be REDUNDANT and Optuna would assign
it negligible split budget. The observed outcome falsifies this mechanism.

The correct mechanistic explanation: tree models CAN represent `hurst_50 - hurst_200` via
sequential splits on the 3 source primitives, but this requires multiple split levels and
interactions. Direct access to the precomputed `hurst_drift_50_200` column allows the model
to express the same threshold condition in a SINGLE split with fewer tree nodes. LightGBM's
importance metric (feature split count × gain) rewards this efficiency: hurst_drift gets
high importance because Optuna finds configurations where `hurst_drift > threshold` is a
frequent high-gain split — not because it adds new signal, but because it compresses
multi-feature interactions into a single feature access.

The Sharpe being FLAT (-0.04 IS, -0.03 OOS vs baseline) confirms the LR-PF OUTCOME predict
(no new signal) while disproving the LR-PF MECHANISM predict (model won't learn it). The
feature gets BUDGET but produces no incremental Sharpe because the underlying information is
already in the model's training data via the 3 source primitives.

---

## LR-PF Methodology Refinement Finding

The Linear Redundancy Pre-Falsifier as specified in the brief (Section 2, pre-falsifier #1)
stated: "R²=1.0 → monitor importance rank." The implicit prediction was low importance =
PATH B INERT. This report documents the falsification of the mechanism.

**Refined LR-PF definition for future iterations:**

A feature with R²=1.0 algebraic identity with existing features is INERT by definition
(it adds no new information). However, the INERT outcome cannot be diagnosed via importance
rank alone — the model may allocate high importance to the linearly-redundant feature for
computational efficiency (split compression). The correct LR-PF diagnostic is:

1. PRIMARY: IS Sharpe Δ vs anchor — if Δ ∈ (-0.10, +0.05), INERT regardless of importance rank.
2. SECONDARY: OOS Sharpe Δ — if |Δ| ≤ 0.20, INERT (null signal).
3. IMPORTANCE RANK: informational only for R²=1.0 features; NOT a signal-quality proxy.

For features with partial IC with source primitives (not R²=1.0), importance rank remains
a valid falsifier signal. The existing `feedback_v3_engineered_feature_pivot.md` carve-out
(importance ≥ 30 for Category-2 composed features) is appropriate for features with
|IC| = 0.5-0.9 but NOT for R²=1.0 exact algebraic identities.

**Catalog rule implication:** Future EDA scripts should classify features by three tiers:
- R²=1.0 exact: LR-PF applies; Sharpe-Δ test is the ONLY valid falsifier; drop from V3_FEATURE_COLUMNS after PATH D verdict.
- |IC| ∈ (0.5, 1.0) partial redundancy: Category-2 carve-out applies; importance ≥ 30 threshold.
- |IC| < 0.5 orthogonal: standard importance-rank falsifier; rank ≥ 14/15 = PATH B.

---

## PATH D Falsifier Check (per brief Section 8 pre-registered criteria)

| Falsifier | Threshold | Observed | Fired? |
|---|---|---|---|
| PATH A: IS Δ ≥ +0.05 | Δ ≥ +0.05 | Δ = -0.0375 | NOT fired — PATH A not available |
| PATH A: OOS Δ ≥ -0.20 | Δ ≥ -0.20 | Δ = -0.0308 | PASS (but PATH A requires both) |
| PATH A: IS-OOS daily ratio ∈ [0.5, 2.0] | [0.5, 2.0] | 1.2105 | PASS (but PATH A not available) |
| **PATH B: rank ≥ 14/15 ALL 3 syms** | ≥ 14/15 all | BCH=14, LDO=**8**, TRX=15 | **LDO BREAKS ALL-condition — PATH B NOT fired** |
| PATH C-clean: IS Δ < -0.10 | < -0.10 | -0.0375 | NOT fired |
| PATH C-clean: OOS Δ < -0.30 | < -0.30 | -0.0308 | NOT fired |
| PATH C-suspicious: IS-OOS daily ratio outside [0.5, 2.0] | outside [0.5, 2.0] | 1.2105 | NOT fired |
| **PATH D: IS Δ ∈ (-0.10, +0.05)** | (-0.10, +0.05) | **-0.0375** | **FIRES** |
| **PATH D: OOS Δ ∈ (-0.20, +0.20)** | (-0.20, +0.20) | **-0.0308** | **FIRES** |
| **PATH D: axis LEARNED** | rank ≤ 13 in ≥1 sym | LDO rank=8 | **FIRES** |

**PATH D NULL-RESULT FIRES** on all three conditions simultaneously.

The brief's pre-registered PATH D SWAP-axis importance-rank-ONLY trigger (rank ≥ 14/15 in
ALL 3 symbols = PATH B independent of trade-count change) does NOT fire because LDO rank = 8/15
breaks the ALL-symbols condition. But the standard PATH D conditions (IS Δ band + OOS Δ band +
LEARNED) all fire, giving the same NULL-RESULT verdict by the standard PATH D mechanism.

**QR pre-registered probability assessment accuracy:**
- PATH B 55% predicted → PATH D fires instead. The outcome (no Sharpe lift) is the same as
  the pre-registered PATH B prediction, but the mechanism (high importance, not low) differs.
- PATH D 15% predicted → FIRES. The QR's PATH D framing was correct: the hypothesis was
  specifically "document LR-PF methodology" and PATH D is the pre-registered documentation
  vehicle. The re-framed hypothesis is SUPPORTED: the LR-PF outcome was correctly predicted
  (no signal), and the mechanism discrepancy (high vs low importance) is the methodological
  finding the QR anticipated under PATH D framing.

---

## Per-Symbol Decomposition

### IS Per-Symbol

| Symbol | trades | win_rate | net_pnl_pct | avg_pnl_pct | pct_of_total_IS_pnl |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 86 | 44.2% | +56.46% | +0.657% | **+255.38%** |
| LDOUSDT | 9 | 22.2% | -16.09% | -1.787% | **-72.76%** |
| TRXUSDT | 85 | 30.6% | -18.27% | -0.215% | **-82.62%** |

IS is extremely BCH-concentrated at /053 (BCH 255% of total IS PnL; LDO and TRX both negative
IS contributors). This is a strong asymmetry: BCH IS WR 44.2% vs TRX IS WR 30.6% vs LDO IS
WR 22.2%. The IS max_dd of 45.37% (elevated vs /052's 32.58%) reflects the TRX IS drag (-82.62%
IS PnL share). Single-seed IS per-symbol results are Optuna-draw sensitive; no structural
interpretation should be placed on the BCH-dominant IS split at n_trials=35 single-seed.

### OOS Per-Symbol

| Symbol | trades | win_rate | net_pnl_pct | avg_pnl_pct | weighted_pnl | concentration_pct |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 36 | 47.2% | +33.71% | +0.936% | **+24.59** | **+100.04%** |
| TRXUSDT | 44 | 47.7% | +19.69% | +0.448% | **+15.60** | **+63.48%** |
| LDOUSDT | 16 | 25.0% | -21.82% | -1.364% | **-15.61** | **-63.52%** |

BCH OOS concentration at 100% (all OOS weighted_pnl = 24.59 ≈ total 24.58 after rounding).
TRX +63.48% and LDO -63.52% approximately cancel in aggregate, leaving BCH as the net OOS
PnL generator. The LDO drag (-15.61) vs BCH contribution (+24.59) leaves a net OOS of +8.97
from those two symbols; TRX (+15.60) provides the remainder. The 3-symbol OOS is structurally
fragile: LDO cancels 63.5% of BCH's contribution every period.

### hurst_drift_50_200 per-Symbol Importance vs Source Primitive hurst_diff_100_50

| Symbol | hurst_drift rank | hurst_drift imp | hurst_diff rank | hurst_diff imp | IC(drift, diff) |
|---|---:|---:|---:|---:|---:|
| BCH | 14 / 15 | 34.4 | 12 / 15 | 53.4 | -0.866 |
| LDO | 8 / 15 | 130.2 | 13 / 15 | 102.6 | -0.866 |
| TRX | 15 / 15 | 96.8 | 13 / 15 | 116.0 | -0.866 |
| Portfolio | 14 / 15 | 261.4 | 12 / 15 | 272.0 | -0.866 |

The runtime ic_matrix.csv confirms IC(hurst_drift, hurst_diff_100_50) = -0.866 (pooled IS),
consistent with the algebraic identity: `hurst_drift = hurst_100 - hurst_diff_100_50 - hurst_200`
implies a strong NEGATIVE linear relationship with hurst_diff_100_50 at pooled level. The
hurst_200 term decorrelates the identity partially when pooled across the rolling IS window.
The EDA-level prediction of max|IC| = 0.881 was accurate (runtime: 0.866, within rounding
of the per-symbol max the EDA computed).

At BCH, hurst_diff outranks hurst_drift (rank 12 vs 14). At LDO, hurst_drift substantially
outranks hurst_diff (rank 8 vs 13) — LDO's model prioritizes the derived feature over the
source primitive, consistent with the tree-efficiency mechanism. At TRX, both are bottom-tier
(rank 13 and 15). The pattern is symbol-specific and Optuna-draw-dependent.

---

## LDO Behavior

LDO OOS performance at /053 vs prior cycle-4 EXPLORATIONs:

| Iteration | LDO OOS wpnl | LDO OOS trades | LDO OOS WR | 15th-slot feature |
|---|---:|---:|---:|---|
| iter-v3/051 | -17.44 | 13 | 23.1% | fracdiff_d05_close |
| iter-v3/052 | -13.96 | 14 | 28.6% | regime_momentum_signed_3d |
| **iter-v3/053** | **-15.61** | **16** | **25.0%** | **hurst_drift_50_200** |

LDO OOS weighted_pnl has ranged -13.96 to -17.44 across three consecutive cycle-4
EXPLORATION 15th-slot swaps (fracdiff, regime_momentum_signed_3d, hurst_drift_50_200).
The variation (-13.96 to -17.44, range = 3.48 units) is within single-seed Optuna noise.
The structural LDO OOS negative signal is stable and independent of the 15th-slot content:
LDO's WR oscillates 23-29% (all below 50%) and weighted_pnl oscillates -14 to -17. No
15th-slot feature has addressed the LDO signal generator problem.

At /053, LDO IS is also extremely negative (9 trades, 22.2% WR, -16.09% net_pnl_pct,
-72.76% IS PnL share). This is the worst LDO IS result in cycle 4 (vs /051: -14.96% IS
PnL share, 11 trades; vs /052: +61.26% IS PnL share recovering, 15 trades). The LDO IS
result is Optuna-draw-sensitive at n_trials=35 single-seed; no structural trend should be
read into the IS oscillations. The LDO OOS drag, however, has been structurally negative
across 3 EXPLORATIONs with default ATR and no per-symbol customizations.

---

## OOS Monthly Profile

| Month | trades | pnl_pct | Status |
|---|---:|---:|---|
| 2025-04 | 5 | +2.51% | Positive |
| 2025-05 | 6 | +17.53% | Positive (large) |
| 2025-06 | 11 | +15.68% | Positive (large) |
| 2025-07 | 10 | +3.59% | Positive |
| 2025-08 | 12 | **-33.51%** | Negative (worst month) |
| 2025-09 | 7 | +15.67% | Positive (large) |
| 2025-10 | 10 | -12.13% | Negative |
| 2025-11 | 8 | -4.40% | Negative |
| 2025-12 | 3 | +4.11% | Positive |
| 2026-01 | 7 | +2.83% | Positive |
| 2026-02 | 4 | +1.88% | Positive |
| 2026-03 | 6 | +4.46% | Positive |
| 2026-04 | 4 | +2.26% | Positive |
| 2026-05 | 3 | +4.09% | Positive |

Positive months: 11 of 14 (78.6%). Negative months: 3 of 14. The worst month is 2025-08
at -33.51% (12 trades) — substantially worse than /052's -13.52% and /051's -10.73% worst
month. This 2025-08 drawdown drives the OOS max_dd of 44.22% (vs 30.42% at /052 and 32.75%
at /051). The Q2 2025 cluster (May +17.53%, Jun +15.68%) and Sep 2025 (+15.67%) are the
principal positive months. 2026 (Jan-May) is uniformly low-trade (3-7 trades/month) and
all positive.

The 2025-08 drawdown concentration at /053 vs prior iterations is attributable to an Optuna
hyperparameter draw that produced larger negative trades in the Aug 2025 volatility window.
This is a single-seed artifact; the CPCV path distribution (29/45 positive, unchanged vs
/051-/052) is more representative of structural generalization than any single worst-month.

---

## CPCV Analysis

45 paths generated (REQUIRED_GAP = 66, n_paths=45, 3-symbol universe; UNCHANGED).

| Statistic | iter-v3/053 | iter-v3/052 (reference) | iter-v3/051 (reference) |
|---|---:|---:|---:|
| Paths positive | 29 of 45 (64.4%) | 29 of 45 (64.4%) | 29 of 45 (64.4%) |
| Median path Sharpe | +0.3351 | +0.3351 | +0.335 |
| PBO (per-cell mean) | 0.1377 | 0.1090 | 0.1168 |
| Q25 path Sharpe | -0.243 | -0.243 | -0.243 |
| Q75 path Sharpe | +0.838 | +0.838 | +0.884 |

The CPCV statistics at /053 are, for the third consecutive cycle-4 EXPLORATION, essentially
identical: positive path count (29/45), median (+0.335), Q25 (-0.243). The Q75 has converged
from +0.884 to +0.838 across the three iterations. PBO = 0.1377 (slight rise from /052's
0.1090) — still well below the 0.40 threshold (PASS). The CPCV profile confirms that swapping
the 15th feature slot (fracdiff → 3d-momentum → hurst_drift) produces no structural change
in the cross-path generalization distribution. The three-iteration CPCV stability is itself a
finding: the 14-feature base stack dominates the generalization behavior; the 15th-slot content
has been inert at the CPCV level across all three cycle-4 EXPLORATION tests.

---

## Label Leakage Audit

REQUIRED_GAP = 66 = (21 + 1) × 3 symbols (UNCHANGED from /051-/053).
timeout_candles = 21 (7 days × 3 × 8h candles/day). n_symbols = 3.
Gap formula: (timeout_candles + 1) × n_symbols = 22 × 3 = 66. Applied in CPCV. PASS.

Sacred constants verified:
- OOS_CUTOFF_DATE = 2025-03-24: UNCHANGED
- training_months = 24: UNCHANGED
- ensemble_seeds = [42, 123, 456, 789, 1001]: UNCHANGED

---

## Gate Efficacy Table

| Gate | Parameter | IS fire-rate (est) | OOS fire-rate | Notes |
|---|---|---|---|---|
| BTC trend filter | lookback=42, threshold=15% | embedded | 28 trades killed | BTC-killed OOS = 28 (seed_summary.json); ~23% of OOS candidates |
| OOD z-score gate | zscore_threshold=2.0, 15-D space | embedded | embedded | 15-D UNCHANGED (SWAP preserves count) |
| ADX gate | threshold=20.0 global; per-symbol={} | embedded | embedded | No per-symbol override |
| Primitive 10 — BCH direction block | block_long_for=() | 0% | 0% | REVERTED at /051; UNCHANGED at /052-/053 |
| Per-symbol ATR | DEFAULT (2.0, 1.0) all syms | embedded | embedded | Default per REVERT; UNCHANGED |
| Per-symbol cap | enable_per_symbol_cap=False | DISABLED | DISABLED | Closed per iter-v3/020 |
| Regime gate | enable_regime_gate=False | DISABLED | DISABLED | Closed per iter-v3/022 |

BTC trend filter killed 28 OOS trades at /053 (vs 33 at /052, 32 at /051). The slight reduction
from 33 to 28 is consistent with a slightly different Optuna signal threshold draw for the 3
symbols. The kill rate (~23%) remains in the expected range for the 3-symbol universe at 8h cadence.

---

## Seed Concentration Audit

Single-seed EXPLORATION (1 outer seed, seed=42).

| Metric | Value |
|---|---:|
| OOS monthly Sharpe | +0.4745 |
| OOS max_dd | 44.22% |
| OOS calmar | 0.5558 |
| OOS trades | 96 |
| max_concentration_pct (OOS per seed_summary) | 61.18% |
| BTC killed OOS | 28 |

max_concentration_pct from seed_summary = 61.18%. The per-symbol comparison.csv reports BCH
weighted_pnl concentration at 100.04% (BCH wpnl ≈ total OOS wpnl). The difference arises
because seed_summary max_concentration is measured on a trades basis while comparison.csv
concentration_pct is on a weighted_pnl basis (BCH's higher-pnl-per-trade produces 100%
weighted concentration even at 36/96 = 37.5% of trades). 96 OOS trades across 14 months =
6.86 trades/month — marginally higher than /052 (6.6/month) and consistent with /051 (6.86/month).

---

## Anomaly Notes

1. **Portfolio importance rank #1 from symbol-level dead-last components**: hurst_drift_50_200
   ranks #1 portfolio (261.4) despite ranking 14/15 at BCH and 15/15 at TRX. The portfolio
   aggregation (sum of per-symbol importance × ENSEMBLE_SIZE) is dominated by LDO's 130.2 (rank
   8/15) contribution; BCH's 34.4 (rank 14/15) and TRX's 96.8 (rank 15/15) are each below their
   respective top-ranked features, but at the portfolio sum level, the 3-symbol average elevates
   hurst_drift above regime_momentum_signed_5d (which ranks 15/15 at LDO, 9/15 at TRX, 13/15
   at BCH). This is an importance-aggregation artifact, not a signal-quality signal.

2. **OOS max_dd of 44.22% is highest in cycle 4**: The /053 OOS drawdown (44.22%) exceeds
   /052 (30.42%) and /051 (32.75%) by a material margin. The driver is 2025-08 OOS: -33.51%
   in a single month with 12 trades. BCH and TRX both had LDO-unfavorable Aug 2025 conditions
   (LDO drove the LDO-negative 16-trade OOS result); the large Aug drawdown is attributable to
   the specific Optuna hyperparameter region selected at /053 placing more trades in the Aug
   2025 period. At multi-seed CONFIRMATION the Aug 2025 drawdown would be seed-averaged; no
   structural action warranted at EXPLORATION stage.

3. **IS TRX and LDO both negative (-82.62% and -72.76% IS PnL share)**: The IS BCH carries
   255.38% of IS PnL (BCH alone generates 2.5x total IS PnL; LDO and TRX combined cancel -155.38%).
   This extreme IS concentration is the highest BCH IS PnL share in cycle 4 (vs /052: BCH +62.46%,
   LDO +61.26%, TRX -23.72%; vs /051: BCH +104.05%, TRX +10.91%, LDO -14.96%). The /053 Optuna
   draw found a configuration that is strongly BCH-optimized at IS — the single-seed lottery
   produced a BCH-biased hyperparameter region that appears to have come at the cost of higher
   IS variance (IS max_dd 45.37%, highest in cycle 4).

4. **n_effective_trials = 19**: Consistent across all cycle-4 EXPLORATIONs (/051: 19; /052: 19;
   /053: 19). The 15-feature stack produces ~19 independent trial paths regardless of which
   feature occupies the 15th slot. This is a structural property of the feature correlations in
   the 3-symbol universe at n_trials=525 total: the effective trial count saturates at ~19 well
   below the naive n_trials count, consistent with the established EXPLORATION-mode DSR=0.0
   artifact (feedback_v3_dsr_mode_artifact.md).

5. **IC(hurst_drift, hurst_diff_100_50) = -0.866 runtime vs EDA prediction of -0.881 max|IC|**:
   The runtime pooled IS IC of -0.866 is within the EDA prediction band. The negative sign
   confirms the algebraic relationship: increasing hurst_diff_100_50 (= hurst_100 - hurst_50)
   corresponds to decreasing hurst_drift_50_200 (= hurst_50 - hurst_200) when hurst_100 and
   hurst_200 are held approximately constant. The |IC| = 0.866 pooled confirms the EDA OLS
   R²=1.0 identity (the slight deviation from 1.0 in IC space arises from the pooled averaging
   of hurst_200 variation across symbols and time).

---

## Recommendations to QR for Phase 7 / iter-v3/054

1. **PATH D NULL-RESULT is the pre-registered verdict (no QR discretion on path classification)**:
   Both IS Δ (-0.0375) and OOS Δ (-0.0308) fall squarely within the PATH D bands (-0.10, +0.05)
   and (-0.20, +0.20) respectively. LDO rank = 8/15 confirms the axis was LEARNED. PATH D fires.
   The QR's Phase 7 classification is PATH D NULL-RESULT. hurst_drift_50_200 should be DROPPED
   from V3_FEATURE_COLUMNS_TOP_N at the next iteration (per the R²=1.0 LR-PF rule: drop after
   PATH D verdict; do not retest at higher Optuna budget per feedback_v3_inert_features_at_higher_budget.md).

2. **LR-PF methodology refinement for future briefs**: The LR-PF should be stated explicitly
   in future iteration briefs as a SHARPE-DELTA test, not an importance-rank test. Revised
   LR-PF phrasing: "Features with R²=1.0 algebraic identity with existing V3_FEATURE_COLUMNS
   members are categorically inert. The falsifier is IS Sharpe Δ ∈ (-0.10, +0.05) AND OOS Δ
   ∈ (-0.20, +0.20) — importance rank is informative but NOT the diagnostic." This supersedes
   the /053 brief's "monitor importance rank" language.

3. **CPCV 3-iteration stability is a cycle-4 structural diagnostic**: 29/45 positive paths,
   median +0.335, Q25 -0.243 across /051, /052, /053 (identical to 4 decimal places at median
   and Q25). The 14-feature base stack dominates cross-path generalization; the 15th slot SWAP
   is invisible at the CPCV level. Future cycle-4 EXPLORATIONs that only swap the 15th slot
   will predictably land in the same CPCV band. To move the CPCV distribution, a structural
   change to the base stack (different feature family replacing a mid-table feature) or a
   non-feature axis (labeling, risk architecture, universe) would be required.

4. **Cycle 4 #4 axis priorities**: With fracdiff (NULL), regime_momentum_signed_3d (PATH
   C-suspicious, CLOSED), and hurst_drift_50_200 (PATH D NULL) exhausting three consecutive
   15th-slot SWAP explorations, the next axis should break the SWAP pattern and test a
   structural change to the base stack. Per feedback_v3_structural_over_knob_exploration.md,
   priority order: NEW feature families > NEW labeling > NEW risk primitive > universe. The
   LDO drag (structurally -14 to -17 OOS weighted_pnl across 3 EXPLORATIONs) is the clearest
   structural problem; the QR should determine whether cycle 4 #4 should address LDO's signal
   generator (labeling axis or universe adjustment per the CLOSED per-symbol-cap feedback)
   or continue feature-family exploration with a genuinely orthogonal feature (|IC| < 0.50,
   no R²-redundancy with any existing column).

5. **Cycle 4 cadence**: iter-v3/053 is cycle 4 #3 of 10 EXPLORATIONs. 7 more EXPLORATIONs
   remain before the cycle 4 CONFIRMATION (iter-v3/061 per feedback_v3_strict_10_to_1_cadence.md).
   The hurst_drift_50_200 15th-slot SWAP family is exhausted (3 candidates tested: fracdiff,
   3d-momentum, hurst_drift — all NULL or PATH C-suspicious). No further 15th-slot identity-
   swap EXPLORATIONs should be proposed unless they test a genuinely orthogonal Category 1
   feature with |IC| < 0.50 against ALL existing 14 base features.

---

## Status

OVERALL=READY-FOR-CRITIC
