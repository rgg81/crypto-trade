# Engineering Report — iter-v3/052

## Status: READY-FOR-CRITIC

**PATH C-suspicious (NEGATIVE-SUSPICIOUS-OOS)** — IS-OOS daily Sharpe ratio = 2.3267,
outside the pre-registered [0.5, 2.0] band (Section 8, PATH C-suspicious trigger:
"IS-OOS daily Sharpe ratio outside [0.5, 2.0]"). Pre-registered consequence: CLOSE 3d
UNIVERSAL axis; document anti-pattern at single-seed engineered feature SWAP; pivot to
/053 axis.

The OOS monthly Sharpe of +1.4295 is a strong apparent result (Δ +0.924 vs /028 baseline,
Δ +0.840 vs /051 immediate prior). However, the 2.33 daily ratio is the structural
diagnostic: the v3 methodology flags suspicious-OOS when OOS daily Sharpe materially
exceeds IS daily Sharpe on a ratio basis. The OOS lift is produced almost entirely by
single-seed=42 lottery on a 93-trade OOS sample (BCH 39 trades + TRX 40 trades + LDO 14
trades). regime_momentum_signed_3d ranks 14/15 (BCH), 15/15 (LDO), 15/15 (TRX),
15/15 (portfolio) — dead-last or near-dead-last across all symbols. The 3d variant was
NOT learned decisively by Optuna at n_trials=35 single-seed; the OOS lift is attributable
to Optuna hyperparameter draws on the 14 base features (BCH and TRX ran 0 trades vs
seed=42 frozen-baseline lottery), not to the 3d feature's signal contribution.

This verdict is mechanically determined by the pre-registered Section 8 PATH C-suspicious
trigger. There is no post-hoc discretion: the 2.3267 ratio is above 2.0. The QR pre-registered
"CLOSE 3d UNIVERSAL axis" as the action. The sole mitigating factor is the `feedback_v3_engineered_feature_pivot.md`
carve-out, which relaxes the STRICT IC gate for composed features to importance ≥ 30 threshold
— but that carve-out addresses the IC gate specifically, NOT the IS-OOS daily ratio band gate.
The carve-out does not apply to PATH C-suspicious. The regime_momentum_signed_3d UNIVERSAL
axis is CLOSED for cycle 4 per pre-registration.

---

## Headers

- Iteration: iter-v3/052
- Branch: iteration-v3/052
- Setup commit SHA: 4cf49e5
- Brief PIVOT SHA: 41ff0b8
- Head SHA at report time: 9cb4344
- Hardware: x86_64, 60 GB RAM, WSL2
- Wall-clock time: 1.25h (within 2h EXPLORATION cap)

---

## Configuration Diff vs BASELINE_V3.md

```
BASELINE_V3.md anchor (iter-v3/028): IS +0.5101 / OOS +0.5053 (multi-seed mean)

CARRY-FORWARD (system-level mandate from feedback_v3_per_symbol_lifts_oos_breaks_is.md,
applied at iter-v3/051 REVERT, UNCHANGED at /052):
  V3_MODELS: BCH + LDO + TRX (3 symbols — ALGO REVERTED at /051)
  V3_ATR_MULTIPLIERS_PER_SYMBOL: {} EMPTY (cleared LDO 2.0/1.5 + ALGO from /051 REVERT)
  block_long_for: () EMPTY (cleared BCH LONG block from iter-v3/047 primitive 10)
  REQUIRED_GAP: 66 = (21+1)*3 (3-sym universe; UNCHANGED from /051)

SINGLE NEW AXIS (iter-v3/052 axis under test):
  V3_FEATURE_COLUMNS_TOP_N: 15 features — SWAP 15th element:
    DROP fracdiff_d05_close (was /051 addition; PARKED per /051 NULL-RESULT closeout)
    ADD regime_momentum_signed_3d (= ret_3d × sign(hurst_100 − 0.5); reactivated from
    dead code at engineered_v3.py:330-376; 1 dispatch line added)
  compute_fracdiff_d05_close: RETAINED in dispatch (inert column; zero revert cost)
  fracdiff tests (5): RETAINED as dead-code coverage

UNCHANGED from /051 head:
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
| monthly_sharpe | +0.5161 | +1.4295 | 2.7699 |
| daily_sharpe | +1.1692 | +2.7204 | **2.3267** |
| max_drawdown | 32.58% | 30.42% | 0.9336 |
| profit_factor | 1.1854 | 1.4173 | 1.1957 |
| win_rate | 30.32% | 46.24% | 1.5250 |
| n_trades | 188 | 93 | 0.4947 |
| total_pnl | 37.83 | 44.80 | 1.1842 |
| monthly_calmar | 1.1611 | 1.4728 | 1.2685 |
| dsr | 0.000 | — | — |
| pbo | 0.1090 | — | — |
| psr | 1.0000 | — | — |
| n_trials | 525 | — | — |
| n_effective_trials | 19 | — | — |

### Delta vs BASELINE_V3.md (iter-v3/028 multi-seed mean reference)

| Metric | iter-v3/052 (1-seed) | iter-v3/028 baseline | Delta | PATH Gate |
|---|---:|---:|---:|---|
| IS monthly_sharpe | +0.5161 | +0.5101 | **+0.0060** | PATH A requires Δ ≥ +0.05 — MISS by 0.044 |
| OOS monthly_sharpe | +1.4295 | +0.5053 | **+0.9242** | Strong apparent lift |
| IS-OOS daily Sharpe ratio | 2.3267 | — | — | **OUTSIDE [0.5, 2.0] → PATH C-suspicious FIRES** |

### Delta vs iter-v3/051 (post-REVERT single-seed comparator)

| Metric | iter-v3/051 (1-seed) | iter-v3/052 (1-seed) | Delta |
|---|---:|---:|---:|
| IS monthly_sharpe | +0.4506 | +0.5161 | **+0.0655** |
| OOS monthly_sharpe | +0.5891 | +1.4295 | **+0.8404** |
| IS-OOS daily Sharpe ratio | 1.1478 | **2.3267** | +1.179 (exits band) |
| IS trades | 178 | 188 | +5.6% |
| OOS trades | 96 | 93 | -3.1% |

---

## regime_momentum_signed_3d Importance Investigation

### Importance Rank Per Symbol

| Symbol | 3d rank | 3d importance | 5d rank | 5d importance | PATH B threshold (≥14 ALL syms) |
|---|---:|---:|---:|---:|---|
| BCH | **14 / 15** | 42.6 | 11 / 15 | 57.0 | FIRES (14 ≥ 14) |
| LDO | **15 / 15** | 101.2 | 13 / 15 | 142.4 | FIRES (15 ≥ 14) |
| TRX | **15 / 15** | 39.0 | 12 / 15 | 80.8 | FIRES (15 ≥ 14) |
| Portfolio | **15 / 15** | 182.8 | 13 / 15 | 280.2 | FIRES |

regime_momentum_signed_3d is dead-last (15/15) at LDO, TRX, and portfolio; second-to-last at BCH
(14/15). The PATH B INERT threshold (rank ≥ 14/15 in ALL 3 symbols) fires across the board.
However, the PATH B FULL trigger also requires |OOS Δ| ≤ 0.30 — and OOS Δ = +0.924 violates
that condition. This confirms PATH B is not the operative path; the feature's failure to be
learned (rank ≥ 14 all syms) combined with the anomalous OOS spike maps to PATH C-suspicious,
not PATH B.

### Stacking with regime_momentum_signed_5d

Runtime ic_matrix.csv confirms:
- 3d vs 5d IC (pooled IS): **0.4446** — within the [0.43, 0.47] range predicted by the brief EDA.
- 3d vs vwap_dev_20 IC (pooled IS): **0.4983** — below 0.70 strict gate.

The moderate IC with 5d (0.44) did not prevent the stacking interaction from occurring.
At n_trials=35 single-seed, Optuna chose hyperparameter configurations that favored the
existing 5d feature over 3d for split allocation, as evidenced by 5d ranking consistently
above 3d at all 3 symbols. The 5d sister maintained its rank (11/15 BCH, 13/15 LDO, 12/15
TRX) while 3d was pushed to dead-last. This is the sister-stacking-displacement pattern: the
tree model allocates colsample budget to 5d over 3d because they target similar signal
dimensions and 5d has longer lookback (smoothing more noise in the 24-month IS window at
35 Optuna trials).

Comparison of 3d vs 5d ranks at /052 vs /051:

| Symbol | 5d rank at /051 | 5d rank at /052 | 3d rank at /052 |
|---|---:|---:|---:|
| BCH | 14 / 15 | 11 / 15 | 14 / 15 |
| LDO | 15 / 15 | 13 / 15 | 15 / 15 |
| TRX | 12 / 15 | 12 / 15 | 15 / 15 |
| Portfolio | 15 / 15 | 13 / 15 | 15 / 15 |

The 5d feature rose from 14-15/15 at /051 to 11-13/15 at /052, suggesting Optuna at /052
found better configurations for 5d when it no longer competed with fracdiff (which was also
in the bottom tier at /051). The 3d feature was inserted at the 15th slot and was immediately
pushed to dead-last or near-dead-last. Sister-stacking displacement: 5d recovered signal rank
and 3d was assigned the residual importance budget.

---

## IS-OOS Daily Ratio Analysis

### Observed: 2.3267 vs Pre-Registered Band [0.5, 2.0]

The ratio is 2.3267 — above the pre-registered upper bound of 2.0 by 0.327. The brief
Section 8 PATH C-suspicious trigger is explicit: "IS-OOS daily Sharpe ratio outside [0.5,
2.0] band." This fires.

The `feedback_v3_engineered_feature_pivot.md` carve-out relaxes the STRICT IC gate for
composed Category-2 features (replacing importance ≥ 30 threshold for the IC check). That
carve-out is specific to the IC collinearity gate and does not modify the IS-OOS daily
Sharpe ratio band gate. The carve-out text states: "Strict |IC|<0.50 gate is INAPPROPRIATE
for Category 2 composed features; replace with importance ≥ 30 threshold." The ratio band
is a separate falsifier with no carve-out.

**Why the ratio fired at 2.33 despite a "clean" IS-OOS monthly pattern at /051 (1.148):**

At /051, the IS-OOS monthly ratio was also reversed (OOS +0.5891 > IS +0.4506, monthly ratio
1.307), and the daily ratio was 1.148 — within band. At /052, the OOS daily Sharpe jumped to
+2.7204 while IS daily Sharpe rose more modestly to +1.1692. The OOS trades are 93 over ~14
months (6.6 trades/month), and the OOS daily Sharpe = 2.72 is produced by a highly clustered
OOS win streak concentrated in Q2-Q3 2025 (May +19.47%, Jul +9.96%, Jun +9.37%). The monthly
Sharpe of +1.43 aggregates these spikes; the daily Sharpe is more sensitive to the clustering,
yielding the elevated ratio.

The BCH OOS concentration (39 trades, 46.2% WR, +33.42 wpnl, 74.58% concentration) and TRX
OOS (40 trades, 52.5% WR, +25.35 wpnl, 56.58% concentration) drove the Q2-Q3 2025 cluster.
This is a single-seed=42 lottery effect on the frozen BCH and TRX baselines — the 3d feature
change at /052 vs /051 produced only 5 additional IS trades (+5.6%), and OOS fell by 3 trades
(-3.1%), yet the OOS monthly Sharpe jumped +0.84. The OOS lift is attributable to a different
Optuna hyperparameter draw on the 14 base features, not to regime_momentum_signed_3d's signal.

---

## LDO Behavior

LDO OOS performance:
- weighted_pnl: **-13.96** (vs /051: -17.44; slight improvement of +3.48 units)
- trades: 14 (vs /051: 13 — one additional trade)
- win rate: 28.6% (vs /051: 23.1% — slight improvement)
- concentration_pct: -31.16% (vs /051: -100.07% — materially less drag)

LDO OOS weighted_pnl is still negative at -13.96, but the OOS total weighted_pnl has expanded
to +44.80 (vs /051: +17.43), so LDO's -31.16% concentration share is a smaller fraction of
a larger positive total. The slight LDO improvement vs /051 is within single-seed Optuna noise;
it does not represent a structural shift in LDO's signal quality.

IS LDO comparison:
- iter-v3/051 IS: 11 trades, 27.3% WR, net_pnl_pct = -5.99% (drag metric), wpnl-derived
  share +36.78% (contributor per brief Section 2.8 EDA)
- iter-v3/052 IS: 15 trades, 40.0% WR, net_pnl_pct = +24.34%, pct_of_total_pnl = +61.26%

At /052, LDO IS is positive on both raw and weighted metrics — a reversion relative to /051.
The IS WR rose from 27.3% to 40.0% across 15 trades. This is consistent with the SWAP from
fracdiff (which partially overlapped LDO's feature space at IC 0.7381 EDA-level) to regime_momentum_signed_3d
(which has lower IC with the existing feature stack). The SWAP reduced signal confusion for LDO
IS; however the OOS drag persists (LDO OOS WR 28.6%). LDO's structural OOS problem is
independent of the 15th feature slot content.

---

## OOS Lift Attribution

The OOS Sharpe of +1.4295 is a strong apparent result. Attribution analysis:

**Factor 1 — frozen-baseline lottery (primary)**: The established `feedback_v3_single_seed_frozen_baseline.md`
pattern documents that non-target frozen symbols produce BIT-IDENTICAL OOS results at single-seed=42
across consecutive EXPLORATIONs. At /052, the SWAP of the 15th feature affected all 3 symbols
(since V3_FEATURE_COLUMNS_TOP_N is universal), meaning BCH and TRX WERE retrained with the new
feature. The frozen-baseline mechanism does NOT directly apply when the target-symbol scope is
universal. However, the regime_momentum_signed_3d ranks at dead-last (14-15/15) across all 3
symbols indicates Optuna minimized 3d's role in the tree structure; the hyperparameter region
Optuna converged to at /052 is effectively the same signal space as /051 (14-feature effective
stack, with 3d receiving negligible split budget). The OOS result is therefore driven by a DIFFERENT
Optuna hyperparameter draw on the same 14 base features, not by the 3d feature.

**Factor 2 — IS trade count difference (+5.6%)**: IS trades increased from 178 to 188 (+10 trades).
The behavioral-effect predictor predicted -13% to +12% IS trade change, and +5.6% is within band.
However, the increase is modest; it reflects a slightly different signal threshold from Optuna
re-tuning, not a structural shift from the 3d feature itself.

**Factor 3 — OOS trade count difference (-3.1%)**: OOS trades fell from 96 to 93 (-3 trades). The
OOS Sharpe rose +0.84 on 3 fewer trades. This is a quality-over-quantity shift that can arise from
a more favorable hyperparameter draw on BCH and TRX win rates (BCH OOS WR 46.2% vs /051 43.2%;
TRX OOS WR 52.5% vs /051 41.3%). The 11-point TRX WR improvement from 41.3% to 52.5% across 40
trades is the dominant driver of the OOS Sharpe spike.

**Conclusion**: The OOS lift is attributable to a favorable Optuna hyperparameter draw on BCH and
TRX — most prominently the TRX OOS WR jump from 41.3% to 52.5% — rather than to regime_momentum_signed_3d's
signal. The 3d feature's dead-last importance (15/15 at TRX) confirms it did not contribute to the
TRX signal improvement; Optuna found a better BCH/TRX configuration on the 14-feature base stack.
This interpretation is the ONLY mechanistically consistent explanation given 3d's 15/15 TRX rank.

---

## Per-Symbol Decomposition

### IS Per-Symbol

| Symbol | trades | win_rate | net_pnl_pct | avg_pnl_pct | pct_of_total_IS_pnl |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 97 | 39.2% | +24.81% | +0.256% | **+62.46%** |
| LDOUSDT | 15 | 40.0% | +24.34% | +1.623% | **+61.26%** |
| TRXUSDT | 76 | 32.9% | -9.42% | -0.124% | **-23.72%** |

At /052, TRX IS is negative (-9.42% net_pnl) and LDO IS recovered to positive (+24.34%). BCH IS
is broadly stable. BCH + LDO carry IS PnL; TRX is an IS drag. This is a reversal of /051's pattern
(BCH dominant, LDO IS drag). The IS reallocation reflects the different Optuna draw at /052 after
the feature SWAP; no structural interpretation should be placed on single-seed per-symbol IS splits.

### OOS Per-Symbol

| Symbol | trades | win_rate | net_pnl_pct | avg_pnl_pct | weighted_pnl | concentration_pct |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 39 | 46.2% | +41.06% | +1.053% | **+33.42** | **+74.58%** |
| TRXUSDT | 40 | 52.5% | +32.31% | +0.808% | **+25.35** | **+56.58%** |
| LDOUSDT | 14 | 28.6% | -18.66% | -1.333% | **-13.96** | **-31.16%** |

TRX OOS WR of 52.5% is the highest in the v3 iter-v3/051+ comparison history. BCH OOS WR 46.2%
is also elevated vs /051 (43.2%). LDO OOS WR 28.6% is marginally improved vs /051 (23.1%) but
still firmly in the below-50% drag territory. The BCH + TRX lottery win rates are the primary
driver of the OOS Sharpe spike.

---

## OOS Monthly Profile

| Month | trades | pnl_pct | Status |
|---|---:|---:|---|
| 2025-04 | 7 | +0.31% | Positive |
| 2025-05 | 7 | **+19.47%** | Positive (large) |
| 2025-06 | 8 | +9.37% | Positive |
| 2025-07 | 11 | +9.96% | Positive |
| 2025-08 | 11 | **-13.52%** | Negative (worst month) |
| 2025-09 | 7 | +4.60% | Positive |
| 2025-10 | 13 | -6.44% | Negative |
| 2025-11 | 8 | +4.18% | Positive |
| 2025-12 | 3 | +4.11% | Positive |
| 2026-01 | 2 | +3.70% | Positive |
| 2026-02 | 4 | -2.44% | Negative |
| 2026-03 | 6 | +4.10% | Positive |
| 2026-04 | 3 | +0.91% | Positive |
| 2026-05 | 3 | +6.50% | Positive |

Positive months: 11 of 14 (78.6%). Negative months: 3 of 14 (vs /051: 5 of 14). The Q2-Q3 2025
cluster of positive months (May +19.47%, Jun +9.37%, Jul +9.96%) is the dominant OOS driver —
three consecutive positive months accounting for +38.80% PnL. The worst month is 2025-08 at
-13.52%. 2026 (Jan-May) is uniformly low-trade (2-6 trades/month) and mostly positive, suggesting
the 3-symbol universe has fewer candidates per month in recent OOS extension.

---

## Falsifier Check (per brief Section 8 pre-registered criteria)

| Falsifier | Threshold | Observed | Fired? |
|---|---|---|---|
| PATH A: IS Δ ≥ +0.05 | IS Δ ≥ +0.05 | IS Δ = +0.0060 | PATH A IS condition MISS — NOT TRIGGERED |
| PATH A: OOS Δ ≥ -0.20 | OOS Δ ≥ -0.20 | OOS Δ = +0.924 | PASS (but PATH A requires both conditions) |
| PATH A: IS-OOS daily ratio ∈ [0.5, 2.0] | [0.5, 2.0] | 2.3267 | FAIL — PATH A not available |
| PATH A: 3d rank ≤ 10/15 in ≥1 sym | ≤ 10/15 | min rank = 14/15 | FAIL — PATH A not available |
| PATH B: rank ≥ 14/15 ALL 3 syms | ≥ 14/15 all | BCH 14, LDO 15, TRX 15 | FIRES (rank condition) |
| PATH B: \|IS Δ\| ≤ 0.10 | ≤ 0.10 | +0.006 | PASS |
| PATH B: \|OOS Δ\| ≤ 0.30 | ≤ 0.30 | +0.924 | FAIL — PATH B OOS condition MISS |
| PATH C-clean: IS Δ < -0.10 | < -0.10 | +0.006 | NOT FIRED |
| PATH C-clean: OOS Δ < -0.30 | < -0.30 | +0.924 | NOT FIRED |
| **PATH C-suspicious: IS-OOS daily ratio outside [0.5, 2.0]** | outside [0.5, 2.0] | **2.3267** | **FIRES** |
| PATH D: OOS Δ ∈ (-0.20, +0.20) | (-0.20, +0.20) | +0.924 | NOT FIRED |

**PATH C-suspicious FIRES** (single trigger, mechanically deterministic). No other path's
conditions are fully met:
- PATH A: IS Δ = +0.006 fails the ≥ +0.05 condition AND the ratio band condition AND the rank ≤ 10 condition.
- PATH B: |OOS Δ| = +0.924 fails the ≤ 0.30 condition (despite rank condition firing).
- PATH C-clean: IS Δ and OOS Δ are both positive.
- PATH D: OOS Δ = +0.924 exits the (-0.20, +0.20) no-man's-land.

The result is in a unique state: a LARGE positive OOS Sharpe (+1.43, Δ +0.924 vs anchor) combined
with a dead-last feature importance (15/15 TRX, 15/15 LDO, 14/15 BCH) and IS-OOS daily ratio
above the band. This is the clearest possible manifestation of the PATH C-suspicious anti-pattern:
OOS spike without corresponding IS lift or feature learning, caused by single-seed=42 Optuna
hyperparameter lottery on the 14 base features.

---

## CPCV Analysis

45 paths generated (REQUIRED_GAP = 66, n_paths=45, 3-symbol universe; UNCHANGED from /051).

| Statistic | iter-v3/052 | iter-v3/051 (reference) |
|---|---:|---:|
| Paths positive | 29 of 45 (64.4%) | 29 of 45 (64.4%) |
| Median path Sharpe | +0.3351 | +0.3350 |
| PBO (per-cell mean) | 0.1090 | 0.1168 |
| Q25 path Sharpe | -0.243 | -0.243 |
| Q75 path Sharpe | +0.838 | +0.884 |

The CPCV statistics are essentially identical between /051 and /052. This confirms the swap of
the 15th feature (fracdiff → 3d) produced no structural change in the path-level generalization
distribution. The OOS monthly Sharpe lift (+0.84) is not reflected in CPCV paths (the 45 paths
sample the IS+OOS period, not exclusively the OOS window; path Sharpes reflect the combined
window where IS carries more weight). PBO = 0.1090 is well below 0.40 threshold (PASS). The
CPCV profile confirms the IS-OOS daily ratio spike is an OOS-window-specific artifact, not a
broadly distributed cross-path improvement.

---

## Label Leakage Audit

REQUIRED_GAP = 66 = (21 + 1) × 3 symbols (UNCHANGED from /051).
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
| BTC trend filter | lookback=42, threshold=15% | embedded | 33 trades killed | BTC-killed OOS = 33 (from seed_summary.json); ~26% of OOS candidates |
| OOD z-score gate | zscore_threshold=2.0, 15-D space | embedded | embedded | 15-D dimension UNCHANGED (SWAP preserves count) |
| ADX gate | threshold=20.0 global; per-symbol={} | embedded | embedded | No per-symbol override at /052 |
| Primitive 10 — BCH direction block | block_long_for=() | 0% | 0% | REVERTED at /051; UNCHANGED at /052; code path preserved |
| Per-symbol ATR | DEFAULT (2.0, 1.0) all syms | embedded | embedded | All syms at default per /051 REVERT; UNCHANGED at /052 |
| Per-symbol cap | enable_per_symbol_cap=False | DISABLED | DISABLED | Closed per iter-v3/020 |
| Regime gate | enable_regime_gate=False | DISABLED | DISABLED | Closed per iter-v3/022 |

BTC trend filter killed 33 OOS trades at /052 vs 32 at /051 — essentially identical, consistent
with the 3-symbol universe producing ~25-26% OOS candidate kill rate regardless of the 15th feature
slot content.

---

## Seed Concentration Audit

Single-seed EXPLORATION (1 outer seed, seed=42).

| Metric | Value |
|---|---:|
| OOS monthly Sharpe | +1.4295 |
| OOS max_dd | 30.42% |
| OOS calmar | 1.4728 |
| OOS trades | 93 |
| max_concentration_pct (OOS per seed_summary) | 56.86% |
| BTC killed OOS | 33 |

seed_summary.json reports max_concentration_pct = 56.86% (lower than comparison.csv's 74.58% for
BCH; the difference is between per-symbol trade-count concentration vs per-symbol wpnl concentration).
BCH wpnl concentration of 74.58% remains elevated in the 3-symbol universe, consistent with prior
v3 iterations. 93 OOS trades across 14 months = 6.6 trades/month; within the expected range for
3-symbol 8h cadence.

---

## Pathway Classification Verdict

**PATH C-suspicious (NEGATIVE-SUSPICIOUS-OOS)**

Pre-registered consequence (brief Section 8, PATH C-suspicious row):
> "CLOSE 3d UNIVERSAL axis; document anti-pattern at single-seed engineered feature SWAP; pivot to /053 axis."

The pre-registration is unconditional: the ratio band trigger fires and closes the axis. There is
no carve-out for engineered features in the PATH C-suspicious definition. The `feedback_v3_engineered_feature_pivot.md`
carve-out applies exclusively to the IC gate (relaxing strict |IC|<0.50 to importance ≥ 30 for
Category-2 composed features). The PATH C-suspicious ratio-band gate has no published carve-out.

**regime_momentum_signed_3d UNIVERSAL axis: CLOSED for cycle 4** per pre-registration.

The 3d feature ranks dead-last or near-dead-last across all 3 symbols and portfolio — the same
INERT signal pattern as fracdiff at /051 (ranks 11-13/15) but worse (ranks 14-15/15). Stacking
two sister features (3d + 5d) at IC=0.44 created a sister-displacement effect: 5d recovered
rank (from 14-15/15 at /051 to 11-13/15 at /052) while 3d was pushed to dead-last. The OOS
spike is attributable to a favorable single-seed=42 hyperparameter draw on BCH+TRX, not to the
3d feature's signal.

---

## Anomaly Notes

1. **TRX OOS WR jump (41.3% → 52.5%)**: 40 OOS trades with 52.5% WR is unusually high for TRX
   in v3 history. The jump of +11.2 percentage points relative to /051 on the same trade count
   is a single-seed Optuna draw artifact. No structural investigation warranted; TRX frozen-baseline
   pattern would persist at next EXPLORATION if the non-TRX axis is under test.

2. **IS TRX negative (-23.72% pct_of_total)**: TRX IS WR = 32.9%, net_pnl = -9.42% across 76
   trades. This is the mirror of the OOS TRX improvement — IS compression for TRX, OOS spike
   for TRX. The ratio dynamic: Optuna found a hyperparameter region at /052 that produces better
   OOS TRX but worse IS TRX. This directly generates the elevated IS-OOS daily ratio.

3. **IS LDO recovery (WR 27.3% → 40.0%)**: LDO IS WR recovered at /052 (15 trades, 40.0% WR,
   +24.34% net_pnl) vs /051 (11 trades, 27.3% WR, -5.99%). The recovery is driven by the fracdiff
   SWAP: the /051 EDA documented IC(fracdiff, vwap_dev_20) = 0.7381 for LDO specifically, causing
   collinearity confusion. Removing fracdiff improved LDO IS signal capture, consistent with the
   /052 SWAP rationale. However, the LDO OOS WR (28.6%) did not recover proportionally, confirming
   that LDO's OOS issue is in the OOS signal environment (2025 declining-LDO regime), not in feature
   collinearity.

4. **CPCV identity with /051**: identical positive path count (29/45), identical median and Q25
   (four decimal places). This is notable: the SWAP of the 15th feature in a 15-feature space
   produced zero detectable shift in the CPCV path distribution, even though the OOS monthly Sharpe
   jumped +0.84. CPCV paths sample the full IS+OOS window; the OOS spike is localized to the OOS
   months and does not shift the cross-path distribution.

5. **3d IC with vwap_dev_20 (runtime: 0.498 vs EDA: 0.619 BCH-level)**: The runtime pooled-IS
   IC (0.498) is lower than the EDA per-symbol BCH estimate (0.6192). Same pooling dynamic as
   fracdiff at /051 (EDA LDO 0.7381 → runtime pooled 0.118). The pooled IC averages across all 3
   symbols and the full rolling IS window, not the per-symbol max. The strict gate at 0.70 was
   correctly applied at EDA-level as a conservative check; runtime confirms it remains below 0.70.

---

## Recommendations to QR for Phase 7 / iter-v3/053

1. **PATH C-suspicious is the pre-registered verdict (no QR discretion on path classification)**:
   The IS-OOS daily ratio = 2.3267 mechanically fires PATH C-suspicious per brief Section 8. The
   QR's Phase 7 classification is PATH C-suspicious — regime_momentum_signed_3d UNIVERSAL axis
   CLOSED. The cadence record should note: both the 3d and 5d regime_momentum variants have now
   been tested at universal scope; the axis family is exhausted in the UNIVERSAL application at
   single-seed single-feature EXPLORATION spec.

2. **Sister-stacking insight for cycle 4 #3**: The stacking pattern (5d recovers rank when fracdiff
   removed; 3d pushed to dead-last when added alongside 5d) suggests the regime_momentum family
   at n_trials=35 single-seed operates as a "one-slot" signal: only one regime_momentum variant
   can be learned at a time. Multi-seed CONFIRMATION is the appropriate venue for testing both
   variants simultaneously (larger Optuna budget can disentangle the two time-scales). Cycle 4 #3
   at /053 should be a DIFFERENT feature family entirely.

3. **Next priority for cycle 4 #3**: Per the /051 EDA synthesis.md §c2, the Candidate 3 axis
   (after 3d is consumed at /052) is `hurst_drift_50_200` — a longer-horizon regime persistence
   indicator with univariate signal confirmed in the same /051 EDA. The /051 brief Section 7 also
   pre-registered "pivot to hurst_drift_50_200" as the PATH B action for /052; since PATH C-suspicious
   fires (stronger than PATH B), the same pivot action applies. QR should verify the hurst_drift_50_200
   axis with a fresh EDA script before committing the /053 setup.

4. **LDO OOS structural issue is deferred (NOT an /053 axis)**: The /052 QR EDA at SHA `0a10581`
   confirmed that LDO removal triggers PATH C-suspicious by construction (2-sym counterfactual:
   IS Δ -0.16, daily ratio 3.58). This analysis was conducted at the /051 trade roster. The /052
   trade roster shows LDO IS is now positive (+61.26% pct_of_total at IS). The LDO removal EDA
   would need to be re-run on the /052 roster to be current; however the fundamental anti-pattern
   (universe shrinkage from 3→2 symbols = PATH C-suspicious trajectory) is likely structural.
   LDO removal is deferred to multi-seed CONFIRMATION where single-seed lottery artifacts dissolve.

5. **Cycle 4 cadence**: iter-v3/052 is cycle 4 #2 of 10 EXPLORATIONs. 8 more EXPLORATIONs remain
   before the cycle 4 CONFIRMATION (iter-v3/061 per feedback_v3_strict_10_to_1_cadence.md). The
   regime_momentum family (3d CLOSED, 5d already in baseline) is exhausted at universal EXPLORATION
   scope. Cycle 4 #3 should target a NEW feature family (Category 1 structural axis per
   feedback_v3_structural_over_knob_exploration.md).

---

## Status

OVERALL=READY-FOR-CRITIC
