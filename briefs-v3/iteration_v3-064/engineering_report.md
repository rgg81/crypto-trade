# Engineering Report — iter-v3/064

## Headers

- **Iteration**: iter-v3/064 (cycle 1 #5 of 10 EXPLORATION; PHASED MASS-EXPANSION #1)
- **Branch**: iteration-v3/064
- **Commit SHA (backtest)**: 0fdc86c75f162be5ee8971fd87b97025b7d3935c (Phase 5.5 gate commit; setup at 8ce02e0)
- **Hardware**: WSL2 (DESKTOP-H1H6T11)
- **Wall-clock time**: 0.70 h (within 2 h EXPLORATION hard cap)
- **Classification**: NEGATIVE-IS-DEGRADATION-WITH-OOS-LOTTERY (proposed; outside standard 4-category taxonomy)

---

## 1. Verdict

**Classification: NEGATIVE-IS-DEGRADATION-WITH-OOS-LOTTERY (proposed new subtype of NEGATIVE).**

Adding `adx_14` alone — reverting the /063 46-feature stack to the 14-feature anchor and adding a single feature (15 features total) — produced IS monthly Sharpe of +0.1527 (Δ -0.6798 vs /060 anchor +0.8325). The IS Sharpe lower-band falsifier from Section 4.4 gate A.1 (IS shift ≥ -0.20) is FAILED by 0.48 Sharpe units. OOS monthly Sharpe is +0.2906 (Δ +0.15 vs /060 +0.1403) — a marginal lift that falls below the PROMISING-AT-EXPLORATION threshold of +0.20.

The OOS +0.15 lift is BCH-concentrated lottery noise (599.77% concentration; 34 trades at 50% WR generating +48.62 weighted PnL) while LDO is catastrophically broken (7.1% WR — 1 win in 14 OOS trades; -40.42 weighted PnL) and TRX is flat (-0.10 weighted PnL, 34.8% WR). This does NOT constitute edge signal.

This is the SAME qualitative failure pattern as /063 (IS Sharpe collapse + BCH-concentration + LDO-collapse) but milder (IS Sharpe collapsed to +0.15 rather than -0.55). The implication is significant: the failure mode is NOT specific to mass expansion. Adding ONE feature at single-seed n_trials=35 is sufficient to destabilize the /060 14-feature anchor's LDO model. The /060 anchor is a LOCAL OPTIMUM at single-seed budget; any feature addition disrupts LDO's calibration.

**Pre-registered failure mode closest match**: Section 7 Mode D ("NEGATIVE — adx_14 introduces IS noise without OOS lift"). Observed IS Δ -0.68 is outside the -0.20 falsifier gate. However, OOS is marginally positive (+0.15), placing this in a CLASSIFICATION GAP not covered by the four pre-registered modes. Proposed new classification: NEGATIVE-IS-DEGRADATION-WITH-OOS-LOTTERY.

**Axis closed.** adx_14 as a single-feature addition to the 14-feature anchor at single-seed EXPLORATION is CLOSED. Not a candidate for /069 CONFIRMATION.

---

## 2. Backtest Results vs /060 Anchor

### Headline metrics vs /060 and /063

| Metric | /060 anchor | /063 mass-expansion | /064 adx_14 (+1) | Δ vs /060 | Falsifier status |
|---|---:|---:|---:|---:|---|
| IS monthly Sharpe | +0.8325 | -0.5507 | **+0.1527** | **-0.6798** | **FAIL** (gate A.1: ≥ -0.20) |
| OOS monthly Sharpe | +0.1403 | +0.4557 | **+0.2906** | **+0.1503** | PASS (gate A.2: ≥ -0.30); FAIL PROMISING (+0.20) |
| IS daily Sharpe | +1.7115 | -1.9638 | +0.3650 | -1.35 | |
| OOS daily Sharpe | +0.3659 | +1.2920 | +0.5378 | +0.17 | |
| OOS/IS daily ratio | 0.21 | -0.66 | **1.47** | sign flip (UP) | structurally suspicious |
| IS MaxDD | 30.97% | 68.72% | **43.66%** | +12.7% | |
| OOS MaxDD | 34.53% | 21.84% | 38.60% | +4.1% | |
| IS Profit Factor | 1.49 | 0.76 | **1.05** | -0.44 | barely break-even |
| OOS Profit Factor | 1.21 | 1.19 | 1.07 | -0.14 | |
| IS win rate | 32.7% | 28.9% | 29.0% | -3.7% | |
| OOS win rate | 38.2% | 34.9% | 36.2% | -2.0% | |
| IS trades | 159 | 128 | 169 | +10 | PASS gate C.6 [128, 222] |
| OOS trades | 94 | 63 | 94 | 0 | PASS gate C.7 [66, 122] |
| IS total PnL | +51.89 | -41.92 | +10.30 | -41.59 | |
| OOS total PnL | +14.73 | +13.49 | +8.11 | -6.62 | |
| frac_positive_paths | 0.6444 | 0.6444 | 0.6444 | 0 | PASS gate A.3 (≥0.50; arch-invariant) |
| DSR_relative | 0.0 | 0.0182 | 0.0000 | 0.0 | Informational only |
| PSR | 0.9763 | 1.0000 | 0.9972 | +0.021 | Informational only |
| PBO | 0.1278 | 0.1054 | 0.0822 | -0.046 | |
| n_eff | 19 | 19 | 18 | -1 | |
| n_trials | 315 | 315 | 315 | 0 | |

Note: the OOS/IS daily ratio of 1.47 — OOS Sharpe EXCEEDING IS Sharpe — is a structural red flag. Genuine edge does not structurally produce better OOS than IS at single-seed EXPLORATION. This ratio, combined with BCH 599% concentration, confirms the OOS +0.15 is lottery noise.

### Per-symbol — IS

| Symbol | Trades | Wins | WR | Net PnL% | Avg PnL% | % of total PnL |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 77 | 28 | 36.4% | +3.11% | +0.040% | -50.70% |
| LDOUSDT | 9 | 2 | 22.2% | -13.73% | -1.525% | **+224.01%** |
| TRXUSDT | 83 | 29 | 34.9% | +4.49% | +0.054% | -73.30% |

LDO produced only 9 IS trades with 22.2% WR — critically thin and loss-generating in-sample. The aggregate IS Sharpe of +0.1527 (barely above zero) is propped up by BCH and TRX with LDO dragging.

### Per-symbol — OOS

| Symbol | Trades | Wins | WR | Net PnL% | wpnl | conc% |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 34 | 17 | 50.0% | +55.06% | **+48.62** | **+599.77%** |
| LDOUSDT | 14 | 1 | **7.1%** | -55.84% | **-40.42** | -498.54% |
| TRXUSDT | 46 | 17 | 37.0% | -2.46% | -0.10 | -1.23% |

BCH OOS 50% WR at 34 trades is a small-sample lottery. LDO's 1/14 WR is structurally broken. TRX is effectively flat.

---

## 3. Feature Importance Forensic Deep-Dive

### 3.1 BCH (adx_14 rank 7/15)

adx_14 importance at BCH (last walk-forward month): rank **7/15**, gain 144.3.

Top-3 BCH features: `ret_skew_200` (205.0), `max_dd_window_50` (187.3), `vwap_dev_20` (185.7). adx_14 sits mid-table at rank 7, below 6 existing baseline features.

This is NOT consistent with adx_14 driving BCH's OOS 50% WR. The BCH OOS "lift" is unrelated to adx_14 importance — it is single-seed lottery noise from 34 OOS trades hitting a favorable BCH window. At rank 7/15, adx_14 has mid-table influence on BCH model calibration, and its presence is not catastrophic for BCH. BCH's IS result (77 trades, 36.4% WR) is in fact degraded relative to /060, suggesting adx_14 did not help BCH directionally.

### 3.2 LDO (adx_14 rank 10/15 — DOWN from EDA rank 2/15)

adx_14 importance at LDO (last walk-forward month): rank **10/15**, gain 188.0.

Compare to EDA singleton preview (Section 2.4): adx_14 was rank 2/15 in a simplified single-LightGBM trained on IS-only data (colsample_bytree=1.0, 50 trees). In the actual walk-forward runner (35 Optuna trials, 3-seed ensemble, colsample_bytree sampled per trial), adx_14 fell to rank 10/15 — bottom-third of the 15-feature stack.

This is the critical failure: the EDA singleton-importance of rank 2/15 was optimistic. The actual walk-forward Optuna budget at single-seed n_trials=35 did NOT reproduce the EDA finding. The 35-trial Optuna search explored colsample_bytree configurations that excluded adx_14 from many splits, producing a final ensemble where adx_14 ranks 10th.

Crucially, LDO's OOS WR collapsed to 7.1% (1 win of 14 trades). The most probable mechanism: Optuna's 35-trial search on the 15-feature stack found an IS-overfit configuration that misfires OOS. The 14-feature anchor at /060 had a stable LDO IS calibration (22.2% IS WR → 27.3% OOS WR for LDO). Adding adx_14 disrupted this calibration at the Optuna search level.

### 3.3 TRX (adx_14 rank 6/15)

adx_14 importance at TRX (last walk-forward month): rank **6/15**, gain 63.0.

TRX produced 83 IS trades (vs ~78 at /060 — slight increase) and 46 OOS trades (vs ~54 at /060). IS WR 34.9%, OOS WR 37.0% — both within normal range. TRX's per-symbol performance is essentially flat. adx_14 at rank 6/15 is above mid-table for TRX, suggesting it IS used in TRX tree splits, but without directional benefit.

The net TRX OOS PnL is -0.10 weighted PnL — statistically indistinguishable from zero. TRX is not helped or harmed.

### 3.4 Summary: adx_14 import rank vs EDA prediction

| Symbol | EDA rank (15-feature, colsample=1.0) | Actual walk-forward rank (15-feature, Optuna n=35) | EDA predicted behavior | Actual outcome |
|---|---:|---:|---|---|
| BCH | 12/15 | 7/15 | Low importance, BCH-stable | BCH stable IS; OOS lottery unrelated to adx_14 |
| LDO | 2/15 | 10/15 | High importance, LDO lift | Calibration disrupted; 7.1% OOS WR (catastrophic) |
| TRX | 7/15 | 6/15 | Mid-table, TRX-stable | Flat — consistent with EDA |

The EDA-to-runner rank discrepancy at LDO (2 → 10) is the root failure. The colsample_bytree=1.0 EDA gives the feature maximum exposure; the actual n_trials=35 Optuna search samples colsample_bytree from [0.3, 1.0], routinely creating trees where adx_14 is excluded. The final ensemble adx_14 rank is an aggregate that reflects the Optuna-sampled colsample configurations, not the colsample=1.0 EDA singleton.

---

## 4. Comparison to /063 Mass-Expansion Pattern

| Dimension | /063 (46 features) | /064 (15 features) | Verdict |
|---|---|---|---|
| IS Sharpe | -0.5507 (Δ -1.38) | +0.1527 (Δ -0.68) | /064 less severe but same direction |
| IS Profit Factor | 0.76 (< 1.0, loss-making) | 1.05 (barely positive) | /064 less severe but barely above break-even |
| IS MaxDD | 68.72% | 43.66% | /064 less severe |
| BCH OOS concentration | +118.5% | **+599.8%** | /064 MORE concentrated |
| LDO OOS WR | 33.3% (3 trades — thin) | **7.1% (1/14)** | /064 LDO MORE broken |
| OOS trades | 63 (FAILED gate C.7) | 94 (PASS gate C.7) | /064 trade-rate intact |
| Failure mode | Mode C (mass-expansion IS collapse) | NEGATIVE-IS-DEGRADATION | Same direction, 1-feature trigger |

The critical structural observation: /063 used 32 new features and produced IS Δ -1.38. /064 used 1 new feature and produced IS Δ -0.68. Both show the same BCH-lottery + LDO-collapse pattern. The failure is NOT a "too many features" problem — it is a fragility property of the /060 14-feature anchor at single-seed n_trials=35. The LDO model is calibration-sensitive; any perturbation to the feature set at single-seed budget destabilizes its Optuna path.

**Implication**: the /060 anchor is a local optimum in feature-space at single-seed n_trials=35. Cycle 1 EXPLORATIONs that ADD features — even one — will disrupt the LDO Optuna trajectory and produce the same IS-degradation pattern at varying severity. This is structural, not accidental.

---

## 5. Falsifier Check (Section 4.4)

| Gate ID | Gate | Threshold | Observed | Status |
|---|---|---|---|---|
| A.1 | IS Sharpe shift | ≥ -0.20 vs /060 | **-0.6798** | **FAIL** (missed by 0.48 units) |
| A.2 | OOS Sharpe shift | ≥ -0.30 vs /060 | +0.1503 | PASS |
| A.3 | frac_positive_paths | ≥ 0.50 | 0.6444 | PASS |
| A.4 | Methodology FAIL | No Critic 13-check BLOCK | Pending Critic review | TBD |
| B.5 | BCH IS share | one-sided ≥ 80% | -50.70% IS (BCH IS drag) | See note |
| C.6 | IS trade count | ∈ [128, 222] | 169 | PASS |
| C.7 | OOS trade count | ∈ [66, 122] | 94 | PASS |
| D.8 | BCH IS wpnl Δ | [-15, +15] | Not computed (no /060 per-symbol IS wpnl in scope) | N/A |
| D.9 | BCH OOS wpnl Δ | [-15, +20] | +48.62 vs +24.75 = **+23.87** | **FAIL** (+23.87 > +20) |
| D.10 | LDO IS wpnl Δ | [-5, +15] | -13.73 vs thin-/060 | FAIL directionally |
| D.11 | LDO OOS wpnl Δ | [-10, +15] | **-40.42** vs -6.18 = **-34.24** | **FAIL** (far below -10) |
| D.12 | TRX IS wpnl Δ | [-10, +10] | +4.49 vs /060 TRX IS | PASS |
| D.13 | TRX OOS wpnl Δ | [-10, +10] | -0.10 vs /060 TRX OOS | PASS |
| E.14 | Tests passing | All v3 feature tests PASS | PASS (committed at setup 8ce02e0) | PASS |
| E.15 | ensemble_summary mode | mode=exploration, size=3 | mode=exploration, size=3, seeds=[191664963, 1662057957, 1405681631] | PASS |
| E.16 | EDA-impl parity | V3_FEATURE_COLUMNS_TOP_N == 15-feature set | 15 features verified in comparison.csv n_trials=315 | PASS |

Gate B.5 note: the per_symbol IS shows BCH at -50.70% of total IS PnL (BCH is a drag, not the dominant IS contributor). This is the reverse of the /060 pattern where BCH IS share was 176.68%. The one-sided ≥80% gate was designed for BCH IS dominance; with a collapsed IS Sharpe (+0.15), BCH dominance metrics are not meaningful. The gate is effectively not applicable in the NEGATIVE-IS-DEGRADATION regime.

**Primary falsifier failure**: Gate A.1 (IS shift ≥ -0.20). Observed IS shift -0.6798 fails by 0.48 Sharpe units. This is the binding gate that terminates the axis.

---

## 6. CPCV Path Distribution

45 CPCV paths from `cpcv_paths.csv`:

- frac_positive_paths: 0.6444 (29/45 positive)
- Path Sharpe q25: -0.243 | q50: +0.335 | q75: +0.838
- Negative paths: 16/45. Notable negatives: path 17 (-1.32), path 28 (-1.31), path 24 (-0.94)
- Notable positive paths: path 12 (+1.88), path 13 (+1.76), path 0 (+1.74)

The path distribution is bimodal: paths with favorable BCH-OOS overlap produce Sharpe > +1.0 (8 paths); paths with LDO-OOS overlap produce Sharpe < -0.5 (7 paths). This bimodality is the CPCV fingerprint of BCH-lottery + LDO-catastrophe: performance depends almost entirely on which CPCV fold's OOS window captures BCH's favorable vs LDO's catastrophic period.

The 0.6444 frac_positive_paths matches /060 and /063 exactly — this is CPCV architecture-invariant (same fold structure, same universe). It provides no signal about /064 vs /060 edge differential.

---

## 7. Label Leakage Audit

**Lookahead bias status**: per `feedback_v3_walkforward_lookahead_bug.md`, the walk-forward bug (`walk_forward.py:69` train_end_ms = test_start_ms, no embargo) affects ALL v3 iterations including /064. The bug is present in this worktree. Cross-iteration deltas remain valid; absolute Sharpe magnitudes are biased upward.

This lookahead bias does NOT change the classification — IS Sharpe of +0.1527 (with bias) is consistent with a true IS Sharpe near zero or below. The collapse relative to /060 (+0.8325, same bias level) is unambiguous.

**CV gap**: standard walk-forward gap applied per runner architecture. No additional leakage audit required beyond the standing worktree-level note.

---

## 8. Gate Efficacy

Risk primitives unchanged from /060 (Section 5 of brief: RiskV2 vol scaling ENABLED, ADX threshold 20.0 ENABLED, feature z-score OOD |z|>2.0 ENABLED, BTC trend kill ±15% 14d ENABLED, Primitive 10 DISABLED, Primitive 11 DISABLED). No gate-efficacy table is produced because no gate changed. Per-regime table shows all trades classified "unknown" (single-regime bucket per runner architecture at EXPLORATION mode).

---

## 9. Anomaly Notes

1. **BCH OOS concentration 599.77%** is the highest concentration value observed in any v3 iteration. It exceeds /063's 118.54% by 5x. This is not a runner bug — it reflects the geometric amplification of a positive BCH OOS PnL (+48.62) against a near-zero total OOS PnL (+8.11). LDO's -40.42 and TRX's -0.10 nearly cancel BCH's gain.

2. **LDO IS trade count: 9** (vs 11 at /060, vs 8 at /063). LDO IS trade roster is persistently thin. The Optuna search at 15 features and n_trials=35 produced a 9-trade IS LDO roster — insufficient for statistically reliable calibration. The 7.1% OOS WR on 14 trades is consistent with a model that learned a spurious LDO signal from a 9-trade IS roster.

3. **IS monthly PnL: no zero-trade months**. The most LDO-sparse month is 2022-01 (1 trade). No methodology failure on trade-rate per month.

4. **OOS/IS daily Sharpe ratio = 1.47** (OOS 0.5378 > IS 0.3650). At genuine edge, OOS should be below IS. This inversion is structurally suspicious and confirms the OOS figure is lottery, not signal. Same inversion pattern was present at /063 (OOS daily 1.29 > IS daily -1.96, sign flip).

---

## 10. Recommendations to QR

**DO NOT continue phased single-feature additions at single-seed EXPLORATION for cycle 1 #6-9.**

The /064 evidence establishes that the /060 14-feature anchor is a LOCAL OPTIMUM at single-seed n_trials=35: adding one feature (adx_14) produces IS Δ -0.68, the same directional failure as adding 32 features at /063. The mechanism is LDO Optuna path disruption — the LDO model's 35-trial search at 15 features finds IS-overfit configurations that collapse OOS WR to 7.1%.

Recommended options for iter-v3/065 (cycle 1 #6 of 10):

**(a) Pivot to non-feature axis.** Labeling, ensemble parameters, risk primitive, or universe expansion. These do not perturb the feature-space Optuna search. Concrete candidates:
- Triple-barrier timeout sensitivity (21 → 28 candles; lower label noise on LDO thin-roster)
- Universe expansion: add a 4th symbol to dilute BCH concentration
- Per-symbol ENSEMBLE_SIZE increase for LDO (3 → 5 at EXPLORATION mode) to reduce LDO single-seed variance

**(b) Reserve feature axes for /069 CONFIRMATION.** At multi-seed n_trials=35 × 5 seeds = 175 trials per (sym × month), the Optuna path variance averages out. adx_14 may well be PROMISING at CONFIRMATION mode — LDO singleton-importance rank 2/15 at colsample=1.0 is a genuine signal, just not reproducible at single-seed budget.

**(c) Characterize the LDO sensitivity axis before feature work.** Run a brief Section 2 EDA: at /060's 14-feature stack, what is the LDO IS WR distribution across the 3 seeds used in EXPLORATION? If LDO IS WR is highly seed-dependent (e.g., ranges from 15% to 40% across seeds), the /060 "anchor" is itself a lucky single-seed draw on LDO, and the /069 CONFIRMATION will need to address LDO calibration structurally (not feature-by-feature).

**Cycle 1 #6-9 should test non-feature axes**. The CYCLE-5 mass-expansion mandate (target 100, minimum 50 features) must be executed at CONFIRMATION mode, not at single-seed EXPLORATION.

**Critic alert**: the brief's Section 8 taxonomy has a CLASSIFICATION GAP. The observed (IS Δ -0.68, OOS Δ +0.15) falls in the gap between:
- NEGATIVE (IS Δ < -0.20 AND OOS Δ < 0.0) — observed OOS is positive
- SUSPICIOUS-OOS-DOMINANT (IS Δ < +0.10 AND OOS Δ ≥ +0.20) — observed OOS is below +0.20

The proposed NEGATIVE-IS-DEGRADATION-WITH-OOS-LOTTERY classification should be codified in `feedback_v3_cycle1_axis_pass_criteria.md` for future iterations. Criteria: IS Δ < -0.20 AND OOS Δ ∈ [0.0, +0.20) AND OOS concentration > 200% (BCH-lottery fingerprint). Axis CLOSED. Not PROMISING.

This is the SECOND consecutive iteration with BCH-lottery + LDO-collapse. The pattern is structural, not random. Critic should evaluate whether a structural LDO-calibration investigation is warranted as a mandatory prerequisite before any feature-axis CONFIRMATION.

---

## Status

OVERALL=READY-FOR-CRITIC
