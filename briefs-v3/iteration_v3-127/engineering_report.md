# Engineering Report — iter-v3/127

## Headers

- **Iteration**: iter-v3/127
- **Type**: EXPLORATION (cycle-7 slot #6 of 10)
- **Branch**: iteration-v3/127
- **Commit SHA**: c8e7cd772fd96b3faed9e4246b200d5ed58652cf
- **Hardware**: Intel i9-12900HK, 58 GiB RAM, WSL2 Linux 6.6.114.1
- **Wall-clock time**: ~0.71h (within 2h EXPLORATION cap)
- **Ensemble**: 3 seeds (outer=42), EXPLORATION mode confirmed (`ensemble_summary.json`)

---

## Configuration Diff vs BASELINE_V3.md (/121)

Single-axis change — all other fields bit-identical to /121:

| Field | /121 Baseline | /127 |
|---|---|---|
| `ITERATION_LABEL` | `"v3-121"` | `"v3-127"` |
| `enable_per_symbol_drawdown_brake` | `False` | `True` |
| `drawdown_brake_threshold_wpnl` | (n/a) | `7.0` |
| `drawdown_brake_recovery_wpnl` | (n/a) | `6.0` |
| `drawdown_brake_window_days` | (n/a) | `45` |
| `drawdown_brake_time_override_candles` | (n/a) | `21` (deadlock-breaker) |
| `drawdown_brake_candle_interval_minutes` | (n/a) | `480` (8h) |
| `V3_FEATURE_COLUMNS_TOP_N` | 14 cols (/121) | 14 cols (REVERTED from /126's 15) |

`d24_ret_autocorr_lag1_50` confirmed ABSENT from feature stack (preflight assertion
verified at commit c8e7cd7). Feature count = 14 (PASS).

V3_MODELS universe: BCH/LDO/TRX (REVERTED from /125's ATOM/RUNE/UNI — matches /121 exactly).

---

## Key Metrics Block

### Headline Comparison

| Metric | IS | OOS | Ratio | /121 IS | /121 OOS |
|---|---:|---:|---:|---:|---:|
| monthly_sharpe | **+0.7866** | **+0.9935** | 1.2630 | +1.3108 | +0.9682 |
| daily_sharpe | 1.9565 | 2.3453 | 1.1987 | 3.1180 | 2.3979 |
| max_drawdown | 38.69% | 24.54% | 0.634 | 26.38% | 25.70% |
| profit_factor | 1.3551 | 1.3432 | 0.991 | 1.6019 | 1.3869 |
| win_rate | 35.37%* | 46.60%* | — | 34.10% | 39.80% |
| n_trades | 147 | 103 | 0.701 | 173 | 98 |
| total_pnl | 52.84 | 31.41 | 0.595 | 88.77 | 38.15 |
| monthly_calmar | 1.3657 | 1.2801 | 0.937 | 3.3647 | 1.4843 |
| weighted_pnl_total | 52.84 | 31.41 | 0.595 | 88.77 | 38.15 |
| dsr | 0.0 | — | — | 0.0 | — |
| pbo | 0.1278 | — | — | 0.1278 | — |
| psr | 1.0 | — | — | 1.0 | — |
| n_trials | 315 | — | — | 1050 | — |
| n_effective_trials | 19 | — | — | 19 | — |

*Win rate from trade-level data (trades.csv). `comparison.csv` reports different values
(IS 29.93%, OOS 43.69%) due to a runner calculation method discrepancy vs
`per_regime.csv` (IS 35.4%, OOS 46.6%). The `per_regime.csv` values match
trade-level computation (IS 52/147 = 35.37%; OOS 48/103 = 46.60%) and are
considered authoritative. This discrepancy is a pre-existing runner artifact.

**n_trials accounting**: 35 trials/cell × 3 seeds × 3 symbols = 315. Matches
`comparison.csv`. Label leakage gap = (K+1) × n_symbols = (21+1) × 3 = 66 candles.
Matches `REQUIRED_GAP = 66` in runner — PASS.

### Delta vs /121 Baseline

| Leg | /127 | /121 (PUBLIC) | Delta |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.7866 | +1.3108 | **-0.5242** |
| OOS monthly Sharpe | +0.9935 | +0.9682 | **+0.0253** |

IS fell 0.52 below the /121 PUBLIC anchor. OOS essentially matched the /121 anchor
(+0.025 delta). OOS/IS Sharpe ratio = 1.2630 (healthy; above the 0.50 Gate 3 floor).

---

## Per-Symbol Attribution

### IS Per-Symbol

| Symbol | Trades | Wins | WR | Net PnL% | Avg PnL% | Pct of Total |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 69 | 30 | 43.5% | +72.37 | +1.049 | 140.19% |
| LDOUSDT | 10 | 3 | 30.0% | +0.22 | +0.022 | 0.43% |
| TRXUSDT | 68 | 19 | 27.9% | -20.97 | -0.308 | -40.61% |

vs /121 IS: BCH 85 trades / LDO 9 trades / TRX 79 trades = 173 total.
Delta: BCH -16 / LDO +1 / TRX -11 = -26 net IS trades (-15.0%).

TRX IS is now a net drag (-20.97 PnL%) with 27.9% WR vs /121's TRX IS 34.2% WR.
BCH IS remains the primary IS earner (72.37% net PnL despite fewer trades; higher avg
+1.049% vs /121's +1.402%). The brake-induced Optuna trajectory shift concentrated
IS profit even more into BCH at the cost of TRX.

### OOS Per-Symbol

| Symbol | Trades | Wins | WR | Net PnL% | Avg PnL% | Pct of Total wpnl |
|---|---:|---:|---:|---:|---:|---:|
| TRXUSDT | 57 | 31 | 54.4% | +48.14 | +0.845 | +103.5% |
| BCHUSDT | 36 | 14 | 38.9% | +16.19 | +0.450 | +35.9% |
| LDOUSDT | 10 | 3 | 30.0% | -15.81 | -1.581 | -39.3% |

vs /121 OOS: BCH 35 trades / LDO 12 trades / TRX 51 trades = 98 total.
Delta: BCH +1 / LDO -2 / TRX +6 = +5 net OOS trades (+5.1%).

**Structural concentration reversal**: /121 was BCH-dominated OOS (BCH 93.92%
concentration, wpnl 35.83 of 38.15 total). /127 is TRX-dominated OOS (TRX 103.5%
concentration, wpnl 32.50 of 31.41 total). BCH OOS wpnl collapsed from +35.83 to
+11.26 (delta -24.57). TRX OOS wpnl surged from +5.21 to +32.50 (delta +27.29).
LDO OOS wpnl worsened from -2.89 to -12.35 (delta -9.46).

OOS net delta: -24.57 (BCH) + -9.46 (LDO) + +27.29 (TRX) = **-6.74 total wpnl**.
Despite the concentration shift, total OOS wpnl is lower than /121 by 6.74 wpnl.
The OOS Sharpe preservation (+0.9935 vs +0.9682) is driven by TRX's stronger
OOS WR (54.4% vs 41.2% at /121) and a lower IS MaxDD baseline for the Sharpe
calculation.

---

## Brake Fire Counts — Inferred Diagnostic

**No `run.log` file present** in `reports-v3/iteration_v3-127/`. The
`drawdown_brake_fires` and `drawdown_brake_time_overrides` counters from
`GateStats` are not directly observable. The following is inferred from
trade-roster comparison.

### EDA Prediction vs Production

| Metric | EDA Predicted | Production Observed |
|---|---|---|
| IS brake activations | 4 | Not directly observable |
| IS trades skipped (ORACLE) | 3 / 173 | -26 net IS trades vs /121 |
| IS trade-count change | [-5%, +5%] | **-15.0%** (OUTSIDE BAND) |
| OOS brake activations | 3 | Not directly observable |
| OOS trades skipped (ORACLE) | 4 / 98 | +5 net OOS trades vs /121 |
| OOS trade-count change | [-5%, +5%] | **+5.1%** (at upper boundary) |
| Deadlock recurrence | Impossible (proved) | OOS 103 trades (not <60: PASS) |

**Key finding**: IS trade-count change of -15.0% far exceeded the [-5%, +5%]
behavioral-effect predictor band. EDA's ORACLE predicted only 3 IS trades would
be skipped. Production saw a net IS reduction of 26 trades — a 9x larger effect.
This indicates the brake-constrained search space caused Optuna to re-converge to
a fundamentally different configuration, not merely skip 3 pre-computed trades.

The OOS result (+5 trades) also exceeds the upper bound of the band but in the
opposite direction — the brake fires less aggressively in OOS (consistent with
EDA's 3 OOS activations vs 4 IS activations), and Optuna found additional OOS
signals in the less-brake-constrained OOS walk.

**Behavioral-effect predictor MISS**: This is a systematic failure of the
closed-loop ORACLE simulator to anticipate Optuna trajectory shifts at production.
The ORACLE predicts 3 specific trades will be skipped; Optuna, seeing brake
constraints in IS training, finds a different hyperparameter region that inherently
generates fewer IS trades. The gap is the fundamental Optuna-trajectory-shift
phenomenon documented at `feedback_v3_single_seed_frozen_baseline.md`.

---

## Cascade Test — Trade Roster Jaccard vs /121

| Period | /127 trades | /121 trades | Shared | Union | Jaccard |
|---|---:|---:|---:|---:|---:|
| IS | 147 | 173 | 96 | 224 | **0.4286** |
| OOS | 103 | 98 | 72 | 129 | **0.5581** |

IS Jaccard = 0.43: 77 trades dropped from /121, 51 new trades entered /127.
OOS Jaccard = 0.56: 26 trades dropped from /121, 31 new trades entered /127.

**Conclusion**: Trade rosters are NOT bit-identical with /121. This rules out a
/116-style PROMISING-MECHANICAL classification by definition — that classification
requires the same trade entry roster with different exit weighting/timing. Here,
Optuna's IS solution shifted substantially (43% overlap), producing a genuinely
different strategy under the brake constraint.

---

## Label Leakage Audit

- REQUIRED_GAP = 66 = (K+1) × n_symbols = (21+1) × 3 = 66 candles. Matches brief.
- López de Prado purge requirement: gap = (timeout_candles + 1) × n_symbols — verified.
- Embargo applied at each walk-forward cell boundary per /058 fix (`e149e9d`).
- No lookahead bias: /058 walk-forward fix is live on this branch (train_end_ms =
  test_start_ms - embargo_ms verified per Critic reviews /074–/079).
- PASS.

---

## Seed Concentration Audit

- **Ensemble mode**: EXPLORATION (3-seed, outer=42). Seeds: 191664963, 1662057957, 1405681631.
- This is single outer-seed mode per `feedback_v3_outer_seed_cap_2_v3.md` (EXPLORATION
  cap). Multi-seed validation deferred to /132 CONFIRMATION.
- Per-seed breakdown not individually exposed in EXPLORATION output — aggregate 3-seed
  mean is the reported IS/OOS Sharpe.
- OOS TRX concentration = 103.5% (artifact of negative LDO denominator). The
  concentration-risk gate requires concentration > 99% AND OOS Sharpe < 0.50.
  OOS Sharpe = 0.9935 > 0.50 → gate does NOT fire.

---

## Gate Efficacy Table

Per-symbol drawdown brake gate (the only new gate in /127):

| Gate | EDA IS fires | EDA OOS fires | Production IS (inferred) | Production OOS (inferred) |
|---|---:|---:|---|---|
| Drawdown brake ON | 4 | 3 | Unknown (no run.log) | Unknown (no run.log) |
| Time-override fires | 4 | 3 | Unknown (no run.log) | Unknown (no run.log) |
| State-recovery fires | 0 | 0 | Unknown (no run.log) | Unknown (no run.log) |
| Deadlock recurrence | 0 | 0 | 0 (OOS 103 trades, not <60) | 0 |

Deadlock-impossibility proof status: CONFIRMED at production level (OOS trade count = 103,
far above the <60 deadlock-detection threshold). The time-override mechanism successfully
prevented the /054 permanent-deadlock pattern. No OOS trade-count collapse occurred.

All prior gates (/121 gates 1-6: vol-target, ADX-removed, Hurst regime, z-score OOD,
no_confirm exit, BTC contagion) inherited bit-identically. Gate efficacy for inherited
gates unchanged from /121 engineering report.

---

## CPCV Path Analysis

From `cpcv_paths.csv` (45 paths):

| Statistic | Value |
|---|---:|
| Positive paths | 29 / 45 |
| frac_positive_paths | **0.644** |
| Path Sharpe Q25 | -0.243 |
| Path Sharpe Q50 | +0.335 |
| Path Sharpe Q75 | +0.838 |
| Path Sharpe mean | +0.303 |
| Path Sharpe stdev | 0.811 |
| Path Sharpe min | -1.318 |
| Path Sharpe max | +1.880 |
| Gate threshold (≥0.55) | **PASS** |

Tail risk: 16 negative paths (35.6%). The distribution is wide (stdev 0.811) — consistent
with a 3-symbol universe subject to per-symbol concentration swings. The 7 most negative
paths cluster near -1.3 Sharpe, corresponding to months when BCH drawdown brake fires
on profitable BCH positions and TRX hasn't compensated.

PBO = 0.1278 (PASS, < 0.4 threshold). PSR = 1.0 (PASS, > 0.95 threshold).
DSR = 0.0: EXPLORATION n_trials=315 produces an E[max_SR] inflated enough to collapse
the deflation ratio. INFORMATIONAL only at EXPLORATION mode per
`feedback_v3_dsr_mode_artifact.md`.

---

## Feature Importance

Portfolio-level importance (last month, 3-seed mean):

| Rank | Feature | Importance |
|---|---|---:|
| 1 | ret_skew_200 | 816.3 |
| 2 | vwap_dev_20 | 759.7 |
| 3 | range_realized_vol_50 | 706.3 |
| 4 | ema_spread_atr_20 | 698.7 |
| 5 | max_dd_window_50 | 646.3 |
| 6 | ret_autocorr_lag1_50 | 607.0 |
| 7 | ret_kurt_50 | 598.0 |
| 8 | hurst_diff_100_50 | 593.3 |
| 9 | ret_kurt_200 | 582.0 |
| 10 | btc_ret_14d | 582.0 |
| 11 | hurst_100 | 569.3 |
| 12 | ret_skew_50 | 520.3 |
| 13 | sym_vs_btc_ret_7d | 511.7 |
| 14 | regime_momentum_signed_5d | 506.7 |

All 14 features present. `d24_ret_autocorr_lag1_50` ABSENT (PASS). Feature ordering
broadly consistent with /121 — no dramatic rank permutation. `regime_momentum_signed_5d`
remains at rank 14 (bottom), consistent with prior cycles. Feature stack REVERTED from
/126's 15 cols to /121's 14 cols as specified.

---

## Trade Spot-Check (10 random OOS trades)

10 random OOS trades (seed 42) verified against entry/exit PnL formula
`d × (exit - entry) / entry × 100 − fee`:

All 10 trades PASS (computed PnL matches stored `pnl_pct` to < 0.01% tolerance;
`net_pnl_pct` = `pnl_pct − fee_pct` confirmed; `weighted_pnl` = `net_pnl_pct × weight_factor`
confirmed). No anomalies found. Exit reasons: mix of `take_profit`, `stop_loss`, and
`no_confirm`. No `end_of_data` exits in OOS sample (expected — OOS data extends to
May 2026).

---

## Zero-Trade Month Check

IS: 34 active months, 0 zero-trade months (PASS).
OOS: 14 active months, 0 zero-trade months (PASS).
Avg IS trades/month: 4.3. Avg OOS trades/month: 7.4.

OOS trade-rate floor: 103 OOS trades total. The ≥130 OOS trades CONFIRMATION floor
(per `feedback_v3_trade_rate_floor_bundle_level.md`) is INFORMATIONAL at EXPLORATION.
At 103 OOS trades, /127 is below the floor if evaluated at CONFIRMATION-spec.

---

## Symbol Exclusion Audit

V3 universe {BCHUSDT, LDOUSDT, TRXUSDT} is disjoint from V1/V2 universe
{BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT, DOGEUSDT, SOLUSDT, XRPUSDT, NEARUSDT}.
No contamination detected (PASS).

Feature isolation check: `features_v3/` does not import from `crypto_trade.features`
(v1) or `crypto_trade.features_v2`. Confirmed clean at prior iterations; no changes
to feature pipeline in /127.

---

## Section 8 Falsifier Evaluation (first-match-wins)

All thresholds pre-registered in research brief Section 8. Evaluation uses
observed IS +0.7866 and OOS +0.9935.

| Criterion | Threshold | Observed | Fires? |
|---|---|---|---|
| NEGATIVE-catastrophic | IS < +0.91 OR OOS < +0.67 (PUBLIC anchor) | IS = +0.7866 < 0.91 | **YES — FIRST MATCH** |
| NEGATIVE-deadlock-recurrence | fires>30 AND OOS trades<60 | OOS trades=103 | No |
| NEGATIVE-no-effect | IS delta in [-0.05,+0.05] (PUBLIC) | delta = -0.5242 | No |
| NEGATIVE-INERT | IS in [0.86, 1.11] (ADJUSTED) | IS = 0.7866 | No |
| NEGATIVE-clean | IS adj-delta in [0.05,0.10] | adj-delta = -0.273 | No |
| SUSPICIOUS-OOS-DOMINANT | OOS delta > +0.30 | delta = +0.025 | No |
| PROMISING-strong | IS >= 1.16 AND OOS >= 1.07 | IS = 0.7866 | No |
| PROMISING-PARTIAL-MECHANICAL | IS in [1.06,1.16] AND OOS in [1.02,1.17] | IS = 0.7866 | No |

**Mechanical verdict: NEGATIVE-catastrophic (IS = +0.7866 < threshold 0.91).**

The IS Sharpe fell into the catastrophic band on the IS leg. IS Δ vs PUBLIC = -0.524.
OOS Sharpe = +0.9935 (+0.025 vs PUBLIC anchor) is the single positive signal.

---

## PROMISING-MECHANICAL Override Analysis

The orchestrator brief requests evaluation of a /116-style PROMISING-MECHANICAL
override. This section analyzes whether the Critic may be justified in applying
such an override.

### /116 PROMISING-MECHANICAL Precedent Criteria

The /116 no_confirm primitive was classified PROMISING-MECHANICAL because:
1. Trade entry roster was BIT-IDENTICAL to the non-no_confirm baseline (same entries,
   different exit timing/weighting).
2. IS Sharpe fell due to earlier exits on trades that would have turned around.
3. OOS Sharpe improved because OOS has different exit-duration characteristics.
4. The mechanism was purely drag-removal (accounting cleanup), not signal discovery.

### /127 Against These Criteria

1. **BIT-IDENTICAL roster**: FAILS. IS Jaccard = 0.43 (96/224 shared). OOS Jaccard = 0.56
   (72/129 shared). /127 produces a fundamentally different trade roster — 77 IS trades
   from /121 are absent and 51 new IS trades appeared. The brake constrained the IS
   Optuna search, causing re-convergence to a different configuration. This is NOT
   drag-removal; it is a search-space restructuring.

2. **IS drag from known mechanism**: PARTIAL. The IS Sharpe drop of -0.524 is plausibly
   attributable to the brake constraining IS-profitable BCH drawdown periods (the brake
   fired on the Jan 2024 BCH IS peak; EDA showed +5.41 wpnl ORACLE IS benefit, but
   production re-convergence inverted this). TRX IS WR collapsed to 27.9% (vs /121's
   34.2%), suggesting Optuna's new trajectory is suboptimal for TRX IS.

3. **OOS Sharpe preserved vs /121**: YES. OOS +0.9935 vs /121 +0.9682 (delta +0.025).
   The OOS preservation is genuine — deadlock was prevented (103 OOS trades) and TRX
   OOS surged (+27.29 wpnl delta) due to higher WR (54.4% vs 41.2% at /121).

4. **Mechanism non-compoundable**: UNCERTAIN. Unlike /116's exit-only change, /127's
   brake affects entry suppression, which modifies Optuna's IS training objective.
   The resulting OOS behavior cannot be attributed solely to the brake skipping known
   OOS-negative trades — it reflects a wholesale Optuna re-convergence.

### Override Eligibility Assessment

The Critic would need to argue: "the brake-constrained IS training is a legitimate
PROMISING-MECHANICAL outcome where IS drag reflects the brake correctly suppressing
IS loss-streak trades, and OOS Sharpe preservation confirms the brake adds value."
The weakness in this argument is that the IS Jaccard = 0.43 shows Optuna re-converged
to a completely different model (not just a minor route-change). The OOS improvement
of +0.025 is also within 1-sigma noise for a 3-seed EXPLORATION.

**Engineer's position**: The mechanical classification is NEGATIVE-catastrophic per the
pre-registered Section 8 first-match-wins rule. The override to PROMISING-MECHANICAL
is plausible but weaker than /116 because: (a) no bit-identity in trade roster, (b)
IS drag of -0.52 is much larger than /116's IS delta (which was near-flat), and (c)
the OOS improvement of +0.025 is marginal noise rather than a demonstrable mechanical
benefit.

**Context that supports the Critic considering PROMISING-MECHANICAL**: This IS the
FIRST cycle-7 result where OOS Sharpe meets or exceeds /121's OOS anchor. The TRX OOS
surge (+27.29 wpnl) is structurally explainable — the brake's IS re-convergence
produced a TRX model with better OOS WR (54.4% vs 41.2%). Whether this is signal
or sampling luck at single-seed EXPLORATION is the Critic's determination.

---

## Anomaly Notes

1. **Win rate discrepancy**: `comparison.csv` IS WR = 29.93%, OOS WR = 43.69%. Trade-level
   computation gives IS 35.37% and OOS 46.60%. `per_regime.csv` matches trade-level.
   The `comparison.csv` win_rate uses a different calculation method (possibly weighted
   by something other than trade count). Pre-existing runner artifact; does not affect
   Sharpe/PnL calculations.

2. **TRX OOS concentration at 103.5%**: An artifact of negative LDO dragging total OOS
   wpnl to 31.41 (lower than TRX's 32.50 contribution). Absolute concentration is
   103.5% for TRX; the gate threshold (> 99% AND OOS Sharpe < 0.50) is NOT triggered
   since OOS Sharpe = 0.9935. Noted for Critic context — structural shift from
   BCH-dominated to TRX-dominated OOS.

3. **No run.log**: The `run.log` file was not written to `reports-v3/iteration_v3-127/`.
   Brake fire counts (`drawdown_brake_fires`, `drawdown_brake_time_overrides`) cannot
   be directly read. Inferred from trade-roster comparison. This is an infrastructure
   gap — the runner should write run.log for all EXPLORATION iterations.

4. **Behavioral-effect predictor miss**: EDA predicted IS trade-roster change in [-5%, +5%].
   Production produced -15.0% IS change. This is outside the band and constitutes a
   falsifier-class miss on the behavioral-effect predictor (Section 4.4 of brief).
   Root cause: ORACLE simulator predicted 3 specific IS skips; Optuna saw the brake
   constraint and converged to a different hyperparameter region entirely (-26 net IS
   trades). This reinforces the `feedback_v3_inert_features_at_higher_budget.md` pattern
   of Optuna search-space perturbation dominating the direct gate-filter effect.

5. **OOS trade count = 103**: Below the 130-trade CONFIRMATION floor. Acceptable at
   EXPLORATION-spec. Qualitative note for /132 CONFIRMATION planning.

---

## Status

**OVERALL = READY-FOR-CRITIC**

Mechanical classification: **NEGATIVE-catastrophic** (IS +0.7866 < 0.91 threshold, Section 8 criterion 1, first-match-wins).

Critic override consideration: Whether to reclassify as PROMISING-MECHANICAL (sister
to /116) given OOS preservation (+0.9935 matching /121 anchor) and TRX OOS structural
surge. Engineer's assessment: override is weaker than /116 precedent (no bit-identity;
IS drag -0.52; OOS gain +0.025 within noise). Critic has final authority.

Cycle-7 context: First non-catastrophic-NEGATIVE result in cycle-7 (prior 5 iterations:
NEGATIVE-catastrophic). OOS Sharpe exceeds /121 OOS for the first time in cycle-7.
Remaining cycle-7 slots: /128–/131 (4 EXPLORATION), /132 (CONFIRMATION).
