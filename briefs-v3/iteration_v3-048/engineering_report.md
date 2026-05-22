# Engineering Report — iter-v3/048

## Status: READY-FOR-CRITIC

NEGATIVE-clean — PATH C fires on BOTH IS and OOS regression criteria. IS monthly Sharpe
+0.31 vs anchor +0.75 (delta -0.43, threshold < -0.10). OOS monthly Sharpe +0.37 vs
anchor +3.53 (delta -3.15, threshold < -0.30). vol_normalized_ret_5d ranks 13-15/15
across all four symbols (bottom-two consistently with regime_momentum_signed_5d). The
new feature added no discriminative signal and degraded Optuna search quality at n_trials=35.
NEW universal engineered feature axis CLOSED for cycle 3 per pre-registered saturation rule.

The critical investigation into the n_trials=700 question resolves the iter-v3/047
misdiagnosis: the 5x OOF parquet row duplication in BOTH /047 and /048 is STRUCTURAL
(5 ensemble seeds each write trial_id 0-34 to the shared parquet with no seed column),
not caused by 5 separate process runs as the /047 engineering report claimed. n_trials=700
is the CORRECT single-run count for ENSEMBLE_SIZE=5, n_trials_per_seed=35, 4 symbols.
The /047 "multi-run-contamination" root-cause attribution was wrong; the /047 OOS
regression was driven by ordinary single-seed Optuna lottery variance across
(ALGO, LDO, TRX) independent of the BCH primitive 10 change.

---

## Headers

- Iteration: iter-v3/048
- Branch: iteration-v3/048
- Commit SHA (setup + gate + brief backfill): 4c7ff26 (HEAD at report time)
- Hardware: x86_64, 60 GB RAM, WSL2
- Wall-clock time: 1.95h (within 2h EXPLORATION hard cap)

---

## Configuration Diff vs BASELINE_V3.md and iter-v3/045 Anchor

```
BASELINE_V3.md (iter-v3/028): IS +0.51 / OOS +0.51

Changes vs iter-v3/045 anchor (the binding-constraint baseline for cycle 3):
  V3_ATR_MULTIPLIERS_PER_SYMBOL: UNCHANGED from 045
    ALGOUSDT: (2.0, 1.5) — per-symbol (iter-v3/044)
    LDOUSDT:  (2.0, 1.5) — per-symbol (iter-v3/045)
    BCHUSDT:  (2.0, 1.0) — default (reverted from iter-v3/046)
    TRXUSDT:  (2.0, 1.0) — default (unchanged)

  Carry-forward from iter-v3/047 (UNCHANGED):
    RiskV2Config.block_long_for  = ("BCHUSDT",)  # primitive 10
    RiskV2Config.block_short_for = ()

  NEW in iter-v3/048:
    V3_FEATURE_COLUMNS_TOP_N: 14 -> 15 features
      ADDED: vol_normalized_ret_5d = ret_5d / (range_realized_vol_50 + 1e-6)

V3_MODELS: (BCH, LDO, TRX, ALGO) — 4 symbols — UNCHANGED
REQUIRED_GAP: 88 = (21+1)*4 — UNCHANGED
OOS_CUTOFF_DATE: 2025-03-24 — IMMUTABLE
training_months: 24 — IMMUTABLE
ENSEMBLE_SIZE: 5 (inner ensemble, single outer seed per EXPLORATION spec)
n_trials: 35 per ensemble seed
```

---

## Key Metrics Block

| metric | iter-v3/048 IS | iter-v3/048 OOS | ratio | iter-v3/045 IS | iter-v3/045 OOS | delta vs 045 IS | delta vs 045 OOS |
|---|---|---|---|---|---|---|---|
| monthly_sharpe | +0.3118 | +0.3746 | 1.20 | +0.7459 | +3.5259 | **-0.43** | **-3.15** |
| daily_sharpe | +0.6269 | +0.5996 | 0.96 | +1.3115 | +4.2020 | -0.68 | -3.60 |
| max_drawdown | 38.04% | 19.62% | 0.52 | 66.06% | 13.26% | +28pp better IS | +6.4pp worse OOS |
| profit_factor | 1.0994 | 1.0801 | 0.98 | 1.2096 | 1.6760 | -0.11 | -0.60 |
| win_rate | 32.35% | 42.11% | 1.30 | 34.00% | 50.42% | -1.65pp | -8.31pp |
| n_trades | 204 | 95 | 0.47 | 250 | 119 | -46 | -24 |
| total_pnl | 29.13 | 10.82 | 0.37 | 75.40 | 96.99 | -46.27 | -86.17 |
| monthly_calmar | 0.7656 | 0.5512 | 0.72 | 1.1413 | 7.3128 | -0.38 | -6.76 |
| dsr | 0.0000 | — | — | 0.0000 | — | 0 | — |
| pbo | 0.1339 | — | — | 0.0782 | — | +0.056 | — |
| psr | 0.9971 | — | — | 1.0000 | — | -0.003 | — |
| n_trials | 700 | — | — | 140 | — | +560 | — |
| n_effective_trials | 18 | — | — | 19 | — | -1 | — |

Note on n_trials: 700 = 4 symbols × 5 ensemble seeds × 35 trials per seed. This is the
CORRECT single-run count for ENSEMBLE_SIZE=5. The iter-v3/045 n_trials=140 = 4 symbols
× 1 ensemble seed × 35 trials (EXPLORATION fast-mode). See n_trials Investigation below.

Comparison vs iter-v3/047 carry-forward baseline:

| metric | iter-v3/048 IS | iter-v3/047 IS | delta | iter-v3/048 OOS | iter-v3/047 OOS | delta |
|---|---|---|---|---|---|---|
| monthly_sharpe | +0.3118 | +0.4872 | -0.18 | +0.3746 | +1.1675 | -0.79 |
| n_trades | 204 | 201 | +3 | 95 | 92 | +3 |

---

## Per-Symbol Decomposition

### IS Per-Symbol

| Symbol | 045 trades | 047 trades | 048 trades | WR 048 | net_pnl_pct 048 | pct_of_total 048 |
|---|---|---|---|---|---|---|
| BCH | 94 | 50 | 57 | 42.1% | +45.72% | +4388% |
| LDO | 18 | 15 | 16 | 43.8% | +16.94% | +1626% |
| TRX | 85 | 85 | 80 | 31.2% | -24.26% | -2329% |
| ALGO | 53 | 51 | 51 | 41.2% | -37.36% | -3585% |

The per-symbol IS percentages are meaningless ratios because total_pnl is near-zero
(29.13 vs 75.40 in 045). TRX and ALGO are heavily negative IS — the new feature degraded
model quality specifically for these two symbols. BCH IS improved (primitive 10 carry-
forward keeps LONGs suppressed; 57 vs 50 in 047 indicates slight Optuna roster recovery
from the new 15th feature).

### OOS Per-Symbol

| Symbol | 045 wtd_pnl | 045 trades | 048 wtd_pnl | 048 trades | 048 WR | 048 concentration |
|---|---|---|---|---|---|---|
| ALGO | +53.12 | 22 | +16.30 | 16 | 43.8% | +150.7% |
| BCH | +11.31 | 38 | +7.88 | 22 | 45.5% | +72.8% |
| LDO | +9.34 | 13 | -25.51 | 11 | 27.3% | -235.8% |
| TRX | +23.23 | 46 | +12.14 | 46 | 43.5% | +112.3% |

OOS: LDO collapsed (-25.51 vs +9.34 in 045, -34.85 delta). ALGO dropped (-36.82 delta).
TRX dropped (-11.09 delta). BCH slightly lower (-3.43 delta). The new feature harmed
three of four OOS symbol contributions. LDO's OOS collapse is most severe (11 trades,
27.3% WR — one of the worst LDO OOS profiles in the v3 catalog). No symbol improved OOS.

---

## Feature Importance for vol_normalized_ret_5d

| Symbol | vol_normalized_ret_5d rank | importance | regime_momentum rank | importance | top:bottom ratio |
|---|---|---|---|---|---|
| BCH | **14/15** | 53.0 | 15/15 | 45.4 | 2.5x |
| LDO | **14/15** | 56.2 | 15/15 | 50.0 | 4.0x |
| TRX | **15/15** | 82.4 | 14/15 | 94.2 | 3.2x |
| ALGO | **13/15** | 96.8 | 14/15 | 74.6 | 3.7x |

vol_normalized_ret_5d consistently ranks in the bottom two features across ALL four
symbols. Pre-registered PATH B condition (rank >= 11 in ALL 4 symbols) FIRES — the model
didn't learn the feature. Combined with the IS delta < -0.10 and OOS delta < -0.30,
PATH C-clean is the primary classification.

Notable: regime_momentum_signed_5d ranks 14-15/15 in every symbol (below or equal to
vol_normalized_ret_5d). Both composed engineered features land at the bottom together.
The TRX flat importance distribution from Section 2.5 of the brief (2.5x top:bottom
ratio in 045) remains essentially unchanged in 048 (3.2x). Adding vol_normalized_ret_5d
did not break TRX's flat utilization pattern as predicted; it joined the flat tail.

Importance threshold falsifier (Section 8 PATH B): "importance >= 30 in at least 2 of 4
symbols" — all four symbols show importance > 30 (53, 56, 82, 97). This technically
passes the relaxed IC carve-out threshold, but PATH C-clean dominates on the IS and OOS
regression criteria regardless.

---

## PATH Classification

**VERDICT: NEGATIVE-clean (PATH C-clean)**

Pre-registered PATH C-clean triggers (Section 8):
- IS Sharpe delta < -0.10 vs anchor: +0.3118 - 0.7459 = **-0.43 < -0.10** FIRES
- OOS Sharpe delta < -0.30 vs anchor: +0.3746 - 3.5259 = **-3.15 < -0.30** FIRES

Pre-registered PATH C-suspicious trigger (Section 8):
- IS-OOS daily Sharpe ratio outside [0.5, 2.0]: 0.5996/0.6269 = **0.956** within band
- PATH C-suspicious DOES NOT FIRE (this is a clean regression, not a suspicious spike)

PATH C fires cleanly. The new feature degraded model quality across all symbols. Neither
an IS-collapse-with-OOS-spike pattern (iter-v3/026/027 anti-pattern) nor a mere INERT
result (flat IS, marginal OOS) — this is a genuine IS+OOS regression.

Per pre-registered action: vol_normalized_ret_5d DROPPED from V3_FEATURE_COLUMNS_TOP_N
at iter-v3/049 setup. NEW universal engineered feature axis CLOSED for cycle 3 (saturation
rule fires: 5 attempts — iter-v3/035, /043, /044 universal, and now /048). iter-v3/049
must use a different axis category per feedback_axis_saturation_predictor.md.

---

## Falsifier Check

| Falsifier | Pre-registered Threshold | Observed | Status |
|---|---|---|---|
| IS Sharpe band | [+0.85, +1.15] | +0.3118 | FAR BELOW — FIRES |
| IS Sharpe delta vs 045 | >= +0.10 | -0.43 | FALSIFIED |
| OOS Sharpe band | [+3.30, +3.85] | +0.3746 | FAR BELOW — FIRES |
| OOS Sharpe delta vs 045 | >= -0.10 | -3.15 | FALSIFIED |
| IS-OOS daily Sharpe ratio | [0.5, 2.0] | 0.956 | PASS (within band) |
| vol_normalized_ret_5d rank | <= 10 in >= 2 syms | 13-15 ALL syms | FAILS (all bottom-2) |
| IS trade count delta vs 045 | <= 15% | -18.4% | OUTSIDE BAND (see note) |
| IS trade count delta vs 047 | <= 15% (carry-forward base) | +1.5% | PASS (within band) |

Note on trade count falsifier: the -18.4% delta vs the 045 anchor includes the
primitive 10 carry-forward effect (-37 BCH LONGs removed). The proper comparator is
iter-v3/047 (which has primitive 10 already active): +3 IS trades (+1.5%). No cascade
effect from the new feature. The feature-pipeline is intact; Sub-fixes 4 and 5
assertions pass.

---

## n_trials=700 Investigation — iter-v3/047 Misdiagnosis Resolved

**Finding: n_trials=700 is the CORRECT single-run trial count for ENSEMBLE_SIZE=5.**

The iter-v3/047 engineering report (SHA `af168c4`) claimed:
- "True single-run n_trials = 140 (4 syms × 35 trials)"
- "iter-v3/047 had n_trials=700 = 5x duplicated (multi-run contamination)"
- "LightGBM OpenMP non-determinism caused cross-symbol drift across 5 runs"

This diagnosis is INCORRECT. The iter-v3/048 clean single-run (with --clean-oof, PID
38365, no prior parquet file) also shows n_trials=700 and 55.78M raw OOF rows. This
directly falsifies the 5-separate-process-runs hypothesis.

**Root cause of the 5x row duplication (structural, not contamination):**

The OOF parquet schema has no seed column: `(trial_id, symbol, train_month, fold_idx,
candle_open_time_ms, oof_return)`. The optimization loop in `lgbm.py:456-481` iterates
over `self.ensemble_seeds` (5 seeds for ENSEMBLE_SIZE=5). Each ensemble seed calls
`optimize_and_train()` with its own Optuna study and writes trial_id 0-34 to the shared
parquet via `optimization.py:425-430` (append-if-exists semantics). Since all 5 ensemble
seeds use the same local trial_id counter (0-34), the 5 seeds produce 5 identical
(trial_id, ...) key namespaces and 5x raw rows when concatenated.

Verification from parquet analysis:
- Total rows: 55,779,535
- Duplicate rows (by 5-col key): 44,618,560
- Unique rows: 11,160,975
- Duplication factor: exactly 5.00x

The unique rows equal exactly what one ensemble seed would produce:
- BCH: 53 months × 35 trials × 5 folds × 365 candles = 3,385,375 (actual: 3,385,375)
- This matches iter-v3/045 unique rows (11,155,545; 045 used ENSEMBLE_SIZE=1, no duplication)

**The true n_trials breakdown for ENSEMBLE_SIZE=5:**

```
4 symbols × 5 ensemble seeds × 35 trials per seed = 700 total optimize_and_train calls
```

This is the correct DSR n_trials denominator. iter-v3/045 used n_trials=140 because
ENSEMBLE_SIZE=1 (exploration fast-mode). iter-v3/047 and 048 both use ENSEMBLE_SIZE=5
which correctly reports n_trials=700. The dsr.json n_trials field accurately reflects
the total optimization work.

**Implications for iter-v3/047's verdict:**

The non-target symbol (ALGO, LDO, TRX) drift in iter-v3/047 was NOT caused by 5
separate process runs. The 047 OOF parquet grew from 22MB to 110MB between the start
and end of the same PID (as reported in the orchestrator's observations). This growth
pattern reflects the sequential in-process accumulation from 5 ensemble seeds × 4
symbols × 35 trials, not from multiple process invocations.

The iter-v3/047 ALGO and LDO OOS regression (-25.70 and -28.47 respectively) remains
real — it occurred in the single run that produced the final reports. However, the root
cause was NOT OOF parquet contamination from multiple runs. The true cause is:

1. **Single-seed Optuna lottery variance**: at seed=42, n_trials=35, ENSEMBLE_SIZE=5,
   the Optuna search for ALGO and LDO landed on hyperparameter configurations that
   produced lower OOS performance. This is the same mechanism as the "frozen-baseline-
   pattern" except for inversion: non-target symbols are NOT frozen — they also run
   fresh Optuna search in each EXPLORATION iteration (the brief misframed this as
   "drift" from a baseline, but it is simply each iteration's independent single-seed
   result).

2. **The --clean-oof guardrail still has engineering value**: it correctly prevents
   a scenario where an engineer re-runs the backtest multiple times (intentionally or
   accidentally) and the second run appends to the first run's OOF, which WOULD inflate
   n_trials with non-deduplication-safe data (different Optuna results from re-runs with
   different process-level non-determinism sources beyond ensemble seeds). The guardrail
   is correct but solves a different problem than what was originally diagnosed.

**Affected records:**

- iter-v3/047 Critic FINAL (SHA `785500f`): already committed. The NEGATIVE verdict
  stands on OOS delta grounds. The root-cause attribution in that review ("multi-run
  OOF contamination") needs a correction note.
- iter-v3/047 diary (SHA `ecbb25c`): already committed. The "primitive 10 is NEGATIVE
  due to multi-run stochasticity" framing should be revised to "primitive 10 is NEGATIVE
  due to single-seed Optuna lottery on non-target symbols (ALGO/LDO)."
- memory `feedback_v3_single_seed_frozen_baseline.md`: needs re-examination. Non-target
  symbols are NOT frozen at single-seed — they produce independent Optuna results per
  iteration. The claimed bit-identical pattern from iter-v3/020/021/022 may have been
  coincidental (same seed + same feature set = same Optuna trajectory IF the underlying
  data is unchanged; any feature change breaks this).
- The orchestrator should trigger memory rule updates.

---

## Seed Concentration Audit

Single outer seed (--seeds 1, ENSEMBLE_SIZE=5):

| Symbol | IS weighted_pnl | IS trades | OOS weighted_pnl | OOS trades | OOS concentration |
|---|---|---|---|---|---|
| BCH | +45.72 (net_pnl_pct) | 57 | +7.88 | 22 | +72.8% |
| LDO | +16.94 (net_pnl_pct) | 16 | -25.51 | 11 | -235.8% |
| TRX | -24.26 (net_pnl_pct) | 80 | +12.14 | 46 | +112.3% |
| ALGO | -37.36 (net_pnl_pct) | 51 | +16.30 | 16 | +150.7% |

Single outer seed only (EXPLORATION spec). Multi-seed CONFIRMATION would dissolve
the concentration and reveal whether the OOS regression is seed-specific or systematic.
At the low OOS Sharpe (+0.37), the multi-seed result would be expected to be near zero
or negative; this iteration is clearly a NEGATIVE and no multi-seed run is warranted.

---

## Label Leakage Audit

REQUIRED_GAP = 88 = (21 + 1) × 4 symbols. Unchanged from iter-v3/034 onwards.
timeout_candles = 21 (7 days × 3 candles/day at 8h). n_symbols = 4.
The gap formula (timeout_candles + 1) × n_symbols = 22 × 4 = 88. No changes to gap
parameters in iter-v3/048.

---

## Gate Efficacy Table

| Gate | Description | IS fire rate | OOS fire rate | Notes |
|---|---|---|---|---|
| Primitive 10 — BCH LONG block | block_long_for=("BCHUSDT",) | ~37/94 BCH candidates ≈ 39% | ~16/38 BCH candidates ≈ 42% | Unchanged carry-forward; BCH IS 94->57 = 37 LONGs blocked |
| BTC trend filter | BtcTrendFilterConfig(lookback=42, threshold=15%) | post-hoc | post-hoc | Unchanged |
| OOD z-score gate | zscore_threshold=2.0, 15-D Mahalanobis (UP from 14) | embedded | embedded | vol_normalized_ret_5d added to covariance space |
| ADX gate | threshold=20.0 | embedded | embedded | Unchanged |
| Per-symbol cap | enable_per_symbol_cap=False | DISABLED | DISABLED | Unchanged |
| Regime gate | enable_regime_gate=False | DISABLED | DISABLED | Unchanged |

BCH LONG block fire rate: 37 of ~94 IS candidates (39.3%) blocked. Slightly lower than
047's 41.5% because iter-v3/048 Optuna produced 57 IS BCH trades vs 047's 50, meaning
more SHORT candidates were selected alongside the same ~37 LONG blocks.

OOD gate: the 15-D covariance space (14 → 15 from vol_normalized_ret_5d addition)
showed no anomalous fire-rate shift — the new feature's distribution is similar in scale
to ret_5d, as predicted in Section 6 of the brief.

---

## Anomaly Notes

1. **LDO IS collapsed to +16.94% pnl_pct vs 045's +54.55%**: 16 trades, 43.8% WR. This
   is a material IS degradation for LDO despite no per-symbol change to LDO's config.
   The vol_normalized_ret_5d (rank 14/15, importance 56.2) likely confused Optuna's
   hyperparameter search for LDO — the new 15th feature expanded the search space without
   adding discriminative signal, causing Optuna to converge to a lower-quality region.

2. **TRX IS collapsed to -24.26% pnl_pct vs 045's -7.28%**: TRX was the primary target
   of this iteration (rank-1 feature range_realized_vol_50 used as denominator). The
   expected IS lift from vol-normalized momentum did not materialize; TRX IS worsened.
   vol_normalized_ret_5d ranked 15/15 (dead last) for TRX with importance 82.4 — the
   lowest importance among all 15 features for this symbol.

3. **IS max_drawdown improved 66% → 38%**: This is consistent with reduced total trade
   count (204 vs 250) from primitive 10 + Optuna roster drift. Fewer trades = lower
   drawdown mechanical relationship; not a signal of improved risk control.

4. **OOS 14 months clean**: all OOS months have at least 2 trades. No zero-trade months.

5. **CPCV frac_positive_paths = 0.533**: barely above 50%. The 45 return-proxy paths
   are nearly evenly split positive/negative, consistent with near-zero OOS Sharpe (+0.37).

---

## Recommendations to QR

1. **NEW universal engineered feature axis CLOSED for cycle 3.** Per pre-registered
   saturation rule (Section 8 PATH C action): cycle 3 has now accumulated 5 attempts
   on this axis (iter-v3/035, /043, /044 universal, /048). iter-v3/049 MUST use a
   different axis category. The only CONFIRMED edge ingredient in v3 history remains
   regime_momentum_signed_5d (iter-v3/025/028).

2. **vol_normalized_ret_5d MUST be DROPPED from V3_FEATURE_COLUMNS_TOP_N at iter-v3/049
   setup.** Revert to 14-feature list. Per feedback_v3_inert_features_at_higher_budget.md,
   bottom-ranked features at n_trials=35 actively harm OOS; keeping them is not neutral.

3. **iter-v3/047 misdiagnosis correction needed.** The "multi-run contamination" root
   cause was wrong. See n_trials investigation above. Specific affected artifacts:
   - iter-v3/047 Critic FINAL (SHA `785500f`): needs correction note on contamination
     framing (though NEGATIVE verdict stands on OOS delta grounds).
   - iter-v3/047 diary (SHA `ecbb25c`): "primitive 10 NEGATIVE due to multi-run
     stochasticity" should be corrected to "NEGATIVE due to single-seed lottery variance
     on non-target symbols."
   - memory `feedback_v3_single_seed_frozen_baseline.md`: needs re-examination. Non-
     target symbols produce independent Optuna results per iteration; bit-identity is
     not guaranteed and was likely coincidental in iter-v3/020/021/022.
   **The primitive 10 mechanism itself is NOT re-evaluated by this correction — it remains
   carry-forward in iter-v3/048 and should carry into iter-v3/049 and iter-v3/050
   CONFIRMATION. The mechanism worked (BCH LONG blocked IS: 37 trades, OOS: 16 trades).**

4. **iter-v3/049 axis selection candidates.** With 1 EXPLORATION slot remaining before
   iter-v3/050 CONFIRMATION, the QR should prioritize axes that have a realistic path to
   CONFIRMATION bundle membership. Given the current state:
   - The carry-forward bundle (primitive 10 + ALGO ATR + LDO ATR + regime_momentum_signed_5d)
     is the iter-v3/045 anchor with +0.7459 IS / +3.5259 OOS.
   - Per-symbol architecture remains open (feedback_v3_concentration_is_signal.md:
     universe expansion, per-symbol drawdown brake, vol-target ceiling).
   - Regime-conditional approaches were EDA-falsified in iter-v3/048 Section 2.3.
   - The QR EDA (feedback_v3_axis_selection_quant_discipline.md) must precede axis commit.

5. **--clean-oof guardrail is correctly placed but the original motivation was wrong.**
   The guardrail prevents a true multi-run contamination scenario (engineer re-runs the
   same iteration). The structural 5x duplication from ENSEMBLE_SIZE=5 is by design and
   is benign (deduplicated for any per-row analysis). No change needed to the guardrail;
   the behavior is correct.

---

## Status

OVERALL=READY-FOR-CRITIC
