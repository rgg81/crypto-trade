# Engineering Report — iter-v3/124

## Headers

- Iteration: iter-v3/124
- Branch: iteration-v3/124
- Commit SHA: 0cded022f95ea285ea6bc27263a4d23354ed2f47
- Mode: EXPLORATION (3-seed, ensemble_size=3, seeds lineage outer=42)
- Wall-clock time: not logged (run.log absent; report written from output artefacts)
- Axis: K=63 longer-cadence labels + Branch B sqrt(3) ATR scaling (atr_tp=3.4641, atr_sl=1.7321)
- Cycle: 7 EXPLORATION slot #3 of 10

## Configuration Diff vs BASELINE_V3.md (/121)

| Parameter | /121 Baseline | /124 Value | Delta |
|---|---|---|---|
| `label_timeout_minutes` | 10080 (K=21) | **30240** (K=63) | +200% |
| `atr_tp_multiplier` | 2.0 | **3.4641** (2.0 × sqrt(3)) | +73% |
| `atr_sl_multiplier` | 1.0 | **1.7321** (1.0 × sqrt(3)) | +73% |
| `REQUIRED_GAP` (runner-local) | 66 | **192** (= (63+1) × 3) | +191% |
| `per_cell_embargo` | 22 | **64** (= 63+1) | +191% |
| `V3_FEATURE_COLUMNS_TOP_N` | 14 | 14 (reverted from /123 residue) | 0 |
| All other knobs | unchanged | unchanged | — |

## Key Metrics Block

| Metric | IS | OOS | Ratio | /121 Baseline IS | /121 Baseline OOS | IS Delta | OOS Delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| monthly_sharpe | **+0.4412** | **+0.0254** | 0.058 | +1.3108 | +0.9682 | **−0.870** | **−0.943** |
| daily_sharpe | +1.3213 | +0.0606 | 0.046 | — | — | — | — |
| max_drawdown | 41.01% | 41.93% | 1.022 | — | — | — | — |
| profit_factor | 1.2055 | 1.0092 | 0.837 | — | — | — | — |
| win_rate | 32.8% | 34.1% | 1.041 | — | — | — | — |
| n_trades | 180 | 85 | 0.472 | 173 IS | 98 OOS | +7 | −13 |
| total_pnl | 51.47 | 1.13 | 0.022 | — | — | — | — |
| monthly_calmar | 1.2549 | 0.0270 | 0.022 | — | — | — | — |
| weighted_pnl_total | 51.47 | 1.13 | 0.022 | — | — | — | — |
| dsr | 0.0 | — | — | — | — | — | — |
| pbo | 0.0649 | — | — | — | — | — | — |
| psr | **0.6068** | — | — | — | — | — | — |
| n_trials | 315 | — | — | — | — | — | — |
| n_effective_trials | 17 | — | — | — | — | — | — |

**OOS/IS ratio = 0.058 — catastrophic collapse. Both IS and OOS degraded severely vs /121.**

## Per-Symbol IS + OOS Attribution

| Symbol | IS trades | IS net_pnl_pct | IS wpnl | OOS trades | OOS net_pnl_pct | OOS wpnl |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 77 | **−47.67%** | 13.83 | 27 | +10.19% | — |
| LDOUSDT | 19 | **+31.90%** | −16.34 | 15 | −24.09% | — |
| TRXUSDT | 84 | **−5.81%** | 3.64 | 43 | +9.62% | — |

IS: BCH and TRX net_pnl_pct both negative; LDO IS positive net_pnl_pct but negative weighted_pnl (weight_factor inversion from Optuna; low-confidence trades inflated). OOS: LDO weighted_pnl = −16.34 (dominant OOS loss carrier, 15 trades at 20.0% WR). F5 universe cascade (all 3 IS net_pnl_pct negative) = NOT triggered (LDO IS +31.90%); however BCH IS (−47.67%) and TRX IS (−5.81%) both negative = 2-of-3 IS negative.

## Seed Concentration Audit

Mode: EXPLORATION 3-seed (ensemble_size=3, seeds lineage outer=42; seeds 191664963, 1662057957, 1405681631). Single-lineage compression — all 3 seeds derived from outer=42. Per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode metrics are architecture-compressed vs CONFIRMATION-mode; these numbers do NOT represent multi-seed variance. No per-seed Sharpe breakdown available in artefacts (EXPLORATION-mode does not produce pareto_front.csv per-seed rows). Max symbol concentration: OOS LDO = −1446% (OOS total wpnl = +1.13, LDO OOS wpnl = −16.34 — concentration measure distorted when total OOS is near-zero; structural artefact of catastrophic OOS collapse).

## Label Leakage Audit

- `label_timeout_minutes = 30240` (K=63 candles at 8h).
- `per_cell_embargo = compute_embargo_candles(30240, 480) = 30240 // 480 + 1 = 64` candles (21.3 days).
- Runner-local `REQUIRED_GAP = (63 + 1) × 3 = 192` candles (consistent with validation_v3.py formula; module constant remains 66 per design; runner-local override documented in Section 3.5 of brief).
- `train_end_ms = test_start_ms − embargo_ms` (walk-forward post-fix `e149e9d` intact; embargo_ms = 64 × 480 × 60_000 = 1,843,200,000 ms ≈ 21.3 days).
- IS timeout rate: 8/180 = 4.4%. Below the Branch B pre-flight band [5%, 20%] — F4 narrowly TRIGGERED (4.4% < 5.0% lower bound). Difference is small (0.6pp); mechanism: K=63 Branch B barriers at 3.46/1.73 × natr_21 are WIDER in absolute %, so timeout resolutions are slightly suppressed even at the longer horizon. Does not change the NEGATIVE-catastrophic classification.
- No OOS timeouts (0/85). No forming candles detected (trade PnL arithmetic verified clean in spot-check).

## Gate Efficacy Table

7-gate RiskV2 stack UNCHANGED from /121. No gate-level fire-rate report available in EXPLORATION-mode artefacts (per_regime.csv shows all trades classified as `unknown` regime — regime tagging operates but CPCV paths encompass all regimes combined). IS: 180 trades entered the gate stack; weight_factor=0 trades present (IS: 2 zero-weight rows observed in spot-check). OOS: 85 trades; 1 `end_of_data` exit. BTC trend alignment gate and OOD z-score gate active; no gate-specific fire counts in artefacts.

## CPCV Path Summary

45 paths from CPCV (cpcv_paths.csv, 46 rows including header):

| Metric | Value |
|---|---|
| frac_positive_paths | 0.644 (PASS — gate ≥ 0.55) |
| path_sharpe_q25 | −0.243 |
| path_sharpe_q50 | +0.335 |
| path_sharpe_q75 | +0.838 |
| PBO (per-cell mean) | 0.0649 (PASS — gate < 0.40) |
| PSR | **0.6068 (FAIL — below 0.95)** |
| DSR | 0.0 (INFORMATIONAL in EXPLORATION mode per `feedback_v3_dsr_mode_artifact.md`) |

Path distribution is bimodal: paths 0–16 (early splits) Sharpe ≈ +0.3 to +1.9; paths 17–29 (mid splits) predominantly negative (−0.37 to −1.32); paths 30–44 (late splits) mixed positive (+0.01 to +1.02). This is consistent with IS profitability being concentrated in late 2024 (Nov/Dec: +26.4 and +33.3 pnl_pct) while mid-IS periods are loss-dominated.

## Falsifier Evaluation

| Falsifier | Threshold | Observed | Verdict |
|---|---|---|---|
| F1: catastrophic IS collapse | IS monthly Sharpe Δ < −0.40 vs /121 (+1.3108) → IS < +0.9108 | IS = **+0.4412** (Δ = **−0.870**) | **TRIGGERED** |
| F2: LDO IS sample loss > 15% | AFML eff-sample loss > 15% vs K=21 | **+67.74%** (pre-flight) | TRIGGERED at EDA (pre-registered HIGH-RISK, proceeded per task spec) |
| F3: OOS MaxDD doubling | OOS MaxDD > 2 × /121 OOS MaxDD = 51.40% | OOS MaxDD = **41.93%** | NOT TRIGGERED (below threshold) |
| F4: Branch B IS timeout rate ∈ [5%, 20%] | IS timeout rate outside [5%, 20%] | IS timeout = **4.4%** | **TRIGGERED** (4.4% < 5.0% lower bound; narrowly outside) |
| F5: universe cascade (all 3 IS wpnl negative) | All 3 symbols IS weighted_pnl < 0 | BCH IS wpnl = +13.83 (positive) | NOT TRIGGERED (2-of-3 negative, not 3-of-3) |
| F6: OOS Sharpe collapse | OOS monthly Sharpe Δ < −0.40 vs /121 (+0.9682) → OOS < +0.5682 | OOS = **+0.0254** (Δ = **−0.943**) | **TRIGGERED** |

F1 and F6 both triggered with large margin. F4 narrowly triggered. F2 was pre-registered as TRIGGERED at EDA pre-flight; production confirmed the catastrophic outcome. F3 not triggered (MaxDD held below the doubling threshold). F5 not triggered (BCH OOS IS wpnl positive).

## Section 8 MERGE/NO-MERGE Classification

Pre-registered Section 8 criteria — first match:

- **NEGATIVE-catastrophic criterion 1**: IS Sharpe Δ < −0.40 vs /121 baseline (+1.3108) OR OOS Sharpe Δ < −0.40 vs /121 baseline (+0.9682). Observed: IS Δ = −0.870, OOS Δ = −0.943. **BOTH legs trigger NEGATIVE-catastrophic.**

**Classification: EXPLORATION-NEGATIVE-catastrophic.**

**Section 7 mode match**: Mode 2 (NEGATIVE-catastrophic — /068 replication) + Mode 9 (Catastrophic OOS regime collapse). Both conditions satisfied (IS Δ < −0.40 AND OOS Δ < −0.40). Mode 2 is the first match under first-match-wins.

## Mechanism Diagnosis

The K=63 + Branch B axis replicates the /068 failure mechanism at a larger scale, with the /065 MAGNITUDE-coupling component providing no rescue. The root cause is AFML sample-uniqueness loss: K=63 reduces effective IS training labels by 67% per symbol (LDO: 137 → 44 effective samples; BCH: 301 → 97; TRX: 283 → 91). At n_trials=35 Optuna sees a drastically smaller and more correlated label space — each walk-forward month's training window contains far fewer independent signals. The result is Optuna overfitting to the compressed IS label set: BCH IS net_pnl_pct collapses to −47.67% (large trades, low WR 37.7%) while OOS BCH ekes out +10.19% at only 27 trades — the IS/OOS trade divergence (77 IS vs 27 OOS) signals that the IS Optuna trajectory learned label-specific IS patterns not present in OOS. Branch B's sqrt(3) ATR scaling preserved the per-step barrier-hit probability (label SEMANTIC character), but it could not replenish the lost sample count: preserving semantics per label is irrelevant when there are too few independent labels for Optuna to converge on robust feature interactions. The IS timeout rate of 4.4% (below Branch B's predicted [5%, 20%] band) is consistent with wider barriers suppressing some timeout resolutions, but the dominant pathway to catastrophe is sample-uniqueness loss, not barrier semantics. The labeling-DURATION axis is now CLOSED bilaterally: K=42 NEGATIVE-catastrophic at /068 (IS Δ −0.35 / OOS Δ −0.48 at retained ATR vs /060) and K=63 NEGATIVE-catastrophic at /124 (IS Δ −0.870 / OOS Δ −0.943 at Branch B ATR vs /121). Both K extensions fail the same second-order mechanism at different scales.

## Anomaly Notes

- IS per_symbol `per_symbol.csv` reports trades as 19 LDO / 84 TRX / 77 BCH (total 180), but `comparison.csv` per_symbol block shows OOS LDO 15 trades, OOS BCH 27 trades, OOS TRX 43 trades (total 85). Consistent with trades.csv line count (180 IS / 85 OOS). No anomaly.
- OOS `per_symbol.csv` concentration_pct values are distorted (LDO −1446%, BCH +1224%, TRX +322%) due to OOS total weighted_pnl ≈ +1.13 (near-zero denominator). This is a display artefact of catastrophic OOS collapse, not a data pipeline error.
- Ten random OOS trade spot-check: all 10 entries show pnl − fee = net_pnl_pct and net_pnl_pct × weight_factor = weighted_pnl to within 0.001pp rounding. Trade execution math clean.
- IS monthly PnL: 38 months, 0 zero-trade months. No NaN Sharpe. IS late-2024 dominated by Nov (+26.4%) and Dec (+33.3%) — Optuna has over-fitted to these months under the compressed label regime.
- F4 narrowly TRIGGERED (4.4% IS timeout rate vs [5%, 20%] lower bound): does not change classification; NEGATIVE-catastrophic is driven by F1+F6, not F4.

## Status

OVERALL=READY-FOR-CRITIC
