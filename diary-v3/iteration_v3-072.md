# iter-v3/072 — Cycle 2 #2 NEGATIVE / Fixed-horizon labeling (label-execution mismatch)

**Date**: 2026-05-15
**Type**: EXPLORATION (cycle 2 #2 of 10; ALTERNATIVE LABELING axis)
**Axis**: fixed-horizon-21 return-sign label replacing ATR triple-barrier (`label_mode="fixed_horizon"`)
**Verdict**: EXPLORATION-NEGATIVE per Critic FINAL — NEGATIVE certified clean (genuine strategy property)
**Classification**: NEGATIVE per Section 8.4 disjunctive OR (both gates fire catastrophically)
**BASELINE_V3.md**: UNCHANGED (/059 canonical)

## 1. What was done

Per QR EDA-driven axis selection (`feedback_v3_axis_selection_quant_discipline.md`), cycle 2 #2 tested the alternative-labeling axis. QR EDA `5da9b1b` chose fixed-horizon-21 over distinct-feature M2 retest (funding features showed |AUC-0.5|=0.0347, far below the 0.12 bar). New `label_mode` parameter threaded through labeling.py → lgbm.py → metalabeling.py → run_baseline_v3.py (default "triple_barrier" backward-compat; v3 = "fixed_horizon"). Horizon=21 chosen so embargo (22) + REQUIRED_GAP (66) stay byte-identical.

Commit chain: EDA `5da9b1b` → setup `29ec35e` → backfill `6da9640` → impl `79990bb` → gate `f2152fd` → engineering report `bca383d` → Critic review (this commit). Wall-clock 0.66h.

## 2. Results

| Metric | /060 anchor | /072 | Δ |
|---|---|---|---|
| IS Sharpe | +0.8325 | **-0.3139** | **-1.1464** |
| OOS Sharpe | +0.1403 | **-0.6557** | **-0.7960** |
| IS PF | 1.49 | 0.90 | LOSING IS |
| OOS PF | 1.21 | 0.79 | LOSING OOS |
| IS MaxDD | 30.97% | 44.81% | +13.8% |
| OOS MaxDD | 34.53% | 58.06% | +23.5% |
| IS trades | 159 | 185 | +26 |
| OOS trades | 94 | 83 | -11 |
| frac_positive_paths | 0.6444 | 0.6444 | 0 |
| DSR_relative_B4 | n/a | 0.0000 | FAIL |
| PSR | 0.9763 | 0.0000 | -0.98 |
| PBO | 0.1278 | 0.1426 | +0.01 (still PASS) |

Per-symbol OOS: BCH -0.66 (28 tr, 35.7% WR), **LDO -32.49 (14 tr, 21.4% WR — CATASTROPHIC)**, TRX +7.22 (41 tr, 34.1% WR).

## 3. Root cause — label-execution mismatch

The fixed-horizon label trains the M1 model to predict "is the 21-candle forward return positive?" But the backtest execution STILL exits trades at TP/SL/timeout barriers (BacktestConfig stop_loss_pct=4.0, take_profit_pct=8.0). A trade can have positive 21-candle forward return YET hit SL on candle 3 → model predicts "+1" but trade closes at a loss.

The triple-barrier label is label-execution CONSISTENT by construction (it labels "did the trade hit TP before SL/timeout" — exactly what execution rewards). The fixed-horizon label DECOUPLES the model's training target from the execution reward.

**The triple-barrier path structure IS load-bearing.** This was the QR's pre-registered Section 7 NEGATIVE failure mode ("if path information was load-bearing, the M1 model will be worse") — CONFIRMED. The methodology reference (López de Prado AFML triple-barrier section) independently corroborates: fixed-horizon labels are correct ONLY when execution holds to a fixed horizon.

LDO — the axis's intended beneficiary (EDA showed LDO's triple-barrier label was 69% SL-saturated) — got CATASTROPHICALLY worse (-32.49 wpnl, 21.4% WR vs /060 -19.72, 18.2%). Sharper label-space separation did NOT translate to better trading.

## 4. Critic verdict summary

OVERALL=EXPLORATION-NEGATIVE — NEGATIVE certified clean. 8/8 Checks PASS or informational-FAIL (Check 3 DSR/PSR FAIL informational at EXPLORATION; PBO=0.1426 PASS). §11 Anti-Pattern Scan CLEAN. Foundation Audit: walk-forward fix intact, label_mode threading correct, backward-compat byte-identity verified, no look-ahead (22-candle embargo strictly exceeds 21-candle label horizon).

Adversarial questions resolved:
- GENUINE strategy property, not a label-computation bug — fixed_horizon branch verified correct
- Backward-compat byte-identity verified by code structure (fixed_horizon logic fully gated)
- No look-ahead — embargo coverage proven by arithmetic
- Single-axis confirmed — execution layer (BacktestConfig) unchanged

## 5. PATH classification

**NEGATIVE** per brief Section 8.4 LOCKED disjunctive OR. IS Δ -1.15 < -0.20 AND OOS Δ -0.80 < -0.30 — both gates fire catastrophically. Axis CLOSED.

## 6. Hypothesis check — pre-registered NEGATIVE mode fired

QR Section 7 predicted NEGATIVE 35% with the exact mechanism + metric signature (IS Sharpe down, PF down, trade count up). All three observed. Calibration was accurate on the mechanism; magnitude (IS -1.15) exceeded the predicted band.

## 7. BASELINE_V3.md status

UNCHANGED — /059 stays canonical at `v0.v3-059`. NEGATIVE does not update BASELINE_V3.

## 8. Critic Recommendations carried forward

1. **Fixed-horizon-labeling axis CLOSED** — scope is "label-execution decoupled," not "fixed-horizon" universally. A coherent fixed-horizon design needs BOTH a fixed-horizon label AND fixed-horizon execution exit — a 2-axis change requiring its own brief. Do NOT re-test fixed-horizon-label-only at a different horizon.

2. **Backward-compat tests for label-rule changes should pin a frozen golden output** (not just default ≡ explicit equivalence). Low-cost hardening for any iteration touching labeling.py.

3. **EDA label-vs-execution-consistency diagnostic mandate**: the EDA's "directional-spread" metric measured label-space quality and was a misleading PROMISING signal. Future labeling-axis EDAs MUST include a label-vs-execution-consistency diagnostic (fraction of bars where the candidate label agrees with the barrier-first-hit outcome the backtest realizes) BEFORE proposing the axis. Reframe disagreement-with-execution as a falsifier, not a feature.

## 9. Next Iteration Ideas

Cycle 2 progress: 2/10 EXPLORATIONs done.

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /071 | META-LABELING (same-feature M2) | SUSPICIOUS-OOS-DOMINANT |
| #2 | /072 | ALTERNATIVE LABELING (fixed-horizon) | NEGATIVE |
| #3 | /073 | TBD per QR EDA | — |

The labeling-architecture axis family is now substantially explored within cycle 2:
- Same-feature meta-labeling: SUSPICIOUS-OOS-DOMINANT (TRX-concentrated; LDO over-filtered)
- Fixed-horizon labeling: NEGATIVE (label-execution decoupled)

**iter-v3/073 axis candidates** (QR EDA-driven selection per `feedback_v3_axis_selection_quant_discipline.md`):
- Model architecture (XGBoost was tried at /016 — closed; other model options? GBM hyperparameter regime?)
- Distinct-feature M2 meta-labeling (Critic /071 Rec #4 — but funding features showed |AUC-0.5|=0.0347, weak; would need NEW non-funding distinct features)
- LDO universe revision (MEDIUM priority; LDO has been a structural drag through cycle 1 + cycle 2 so far)
- Triple-barrier parameter refinement that stays label-execution consistent (e.g. per-symbol barrier asymmetry calibrated to execution)
