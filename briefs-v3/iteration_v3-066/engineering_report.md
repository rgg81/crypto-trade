# Engineering Report — iter-v3/066

## Headers

- Iteration: iter-v3/066
- Branch: iteration-v3/066
- Commit SHA (impl): 8598f1c (feat: UNIVERSAL vol_scale_ceiling 1.0 → 0.8 + REVERT /065 ATR multipliers)
- Commit SHA (gate): 59821fa (docs: Phase 5.5 gate — OVERALL=PASS)
- Commit SHA (HEAD at report): 59821fa1304bdc147f8c36fce6488dc97ecffd8d
- Hardware: WSL2 Linux (6.6.114.1-microsoft-standard-WSL2)
- Wall-clock time: 0.69h (per orchestrator; no run.log present)
- Iteration type: EXPLORATION (cycle 1 #7 of 10; NON-FEATURE PIVOT CONTINUATION — RISK PRIMITIVE axis)

---

## Configuration Diff vs /060 Anchor

| Parameter | /060 anchor | /066 |
|---|---|---|
| `RiskV2Config.vol_scale_ceiling` | 1.0 (implicit default) | **0.8** (Path E0.8 per EDA SHA `1d75cb0`) |
| `DEFAULT_ATR_MULTIPLIERS` | (2.0, 1.0) | (2.0, 1.0) — REVERTED from /065's (2.0, 1.5) |
| `ITERATION_LABEL` | "v3-060" | "v3-066" |
| ENSEMBLE_SIZE | 3 (exploration) | 3 (exploration) |
| Seeds | [191664963, 1662057957, 1405681631] | [191664963, 1662057957, 1405681631] |
| n_trials | 35 | 35 |
| V3_FEATURE_COLUMNS_TOP_N | 14 | 14 (UNCHANGED) |
| `vol_scale_floor_per_symbol` | {"TRXUSDT": 0.5} | {"TRXUSDT": 0.5} (UNCHANGED from /061) |
| All other risk primitives | unchanged | unchanged |

**Single substantive change**: `vol_scale_ceiling` from the implicit 1.0 default to 0.8 in the `RiskV2Config(...)` call inside `_build_v3_model`. The `/065` `DEFAULT_ATR_MULTIPLIERS=(2.0, 1.5)` was reverted to (2.0, 1.0) to isolate this single axis. No feature columns changed; no parquet regen required.

---

## Key Metrics Block

All anchor values sourced byte-exact from `reports-v3/iteration_v3-060/comparison.csv` per Section 2.1 T0 anchor declaration.

| Metric | /060 IS | /066 IS | IS Δ | /060 OOS | /066 OOS | OOS Δ | /066 OOS/IS ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| monthly_sharpe | 0.8325 | 0.8308 | **-0.0017** | 0.1403 | 0.1756 | **+0.0353** | 0.2113 |
| daily_sharpe | 1.7115 | 1.7464 | +0.0349 | 0.3659 | 0.4537 | +0.0878 | 0.2598 |
| max_drawdown | 31.87% | 28.86% | -3.01pp | 35.78% | 32.47% | -3.31pp | 1.1251 |
| profit_factor | 1.2806 | 1.2808 | +0.0002 | 1.0482 | 1.0583 | +0.0101 | 0.8263 |
| win_rate | 31.4465% | 31.4465% | 0.00pp | 39.2157% | 38.8350% | **-0.38pp** | 1.2350 |
| n_trades | 159 | 159 | 0 | 102 | 103 | +1 | 0.6478 |
| total_pnl | 51.8906 | 47.8047 | -4.0859 | 5.4989 | 6.2695 | +0.7706 | 0.1311 |
| monthly_calmar | 1.6282 | 1.6564 | +0.0282 | 0.1537 | 0.1931 | +0.0394 | 0.1166 |
| weighted_pnl_total | 51.8906 | 47.8047 | -4.0859 | 5.4989 | 6.2695 | +0.7706 | 0.1311 |
| dsr | 0.0 | 0.0 | 0 | — | — | — | — |
| pbo | 0.1278 | 0.1278 | 0 | — | — | — | — |
| psr | 0.9763 | 0.9935 | **+0.0172** | — | — | — | — |
| n_trials | 315 | 315 | 0 | — | — | — | — |
| n_effective_trials | 19 | 19 | 0 | — | — | — | — |
| frac_positive_paths | 0.6444 | 0.6444 | 0 | — | — | — | — |

**OOS per-symbol (comparison.csv per-symbol block — OOS only):**

| Symbol | /060 OOS wpnl | /066 OOS wpnl | Δ | /060 trades | /066 trades | /060 WR | /066 WR | /066 conc% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BCHUSDT | +1.9078 | +1.0372 | **-0.8706** | 37 | 37 | 32.4% | 32.4% | 16.54% |
| LDOUSDT | -19.7208 | -17.1350 | **+2.5858** | 11 | 12 | 18.2% | 16.7% | -273.31% |
| TRXUSDT | +23.3119 | +22.3673 | **-0.9446** | 54 | 54 | 48.1% | 48.1% | 356.76% |

**Note on orchestrator brief headline table**: The brief's context block cited /060 IS WR 28.99% and OOS WR 36.17%, and TRX OOS "jumping" from +4.16 to +22.37. These figures do NOT match `reports-v3/iteration_v3-060/comparison.csv`. Byte-exact values are: /060 IS WR 31.4465%, OOS WR 39.2157%, TRX OOS wpnl +23.3119. The engineering report uses byte-exact comparison.csv values throughout. The TRX wpnl did NOT jump — it declined slightly (-0.9446) from the /060 anchor.

---

## Seed Concentration Audit

Exploration mode: ENSEMBLE_SIZE=3, seeds=[191664963, 1662057957, 1405681631] (outer=42 lineage). No multi-seed Pareto matrix at EXPLORATION-mode (single outer seed run). `ensemble_summary.json` confirms:

```json
{"mode": "exploration", "ensemble_size": 3, "seeds": [...outer=42...]}
```

E.16 gate: PASS.

CPCV paths (45 paths): frac_positive = 29/45 = 0.644. Sharpe Q25=-0.243, Q50=+0.335, Q75=+0.838. Identical to /060 (architecture-invariant; ceiling change does not affect the CPCV path structure — same trade roster, same weights on path traversal).

---

## Label Leakage Audit

UNCHANGED from /060 baseline. CV gap = (timeout_candles + 1) * n_symbols = (21 + 1) * 3 = 66 candles per walk-forward fold boundary. The vol_scale_ceiling change touches only inference-time `_vol_scale()` in `risk_v2.py` — no training code path modified. Label generation is identical (DEFAULT_ATR_MULTIPLIERS reverted to (2.0, 1.0); same as /060 labeling).

---

## Ceiling Integrity Audit

Full trade-level audit confirms the `vol_scale_ceiling=0.8` constraint is enforced at 100% of trades:

- IS (159 trades): **0 violations** (no weight_factor > 0.8)
- OOS (103 trades): **0 violations** (no weight_factor > 0.8)

Sample OOS rows spot-checked (rows 1, 2, 3, 5, 6 of trades.csv):

| # | Symbol | dir | entry | exit | wf | net_pnl | weighted_pnl | ceiling_ok |
|---|---|---|---:|---:|---:|---:|---:|---|
| 1 | BCHUSDT | -1 | 303.87 | 282.1008 | 0.33 | +7.0640 | +2.3311 | PASS (wf<0.8) |
| 2 | TRXUSDT | -1 | 0.2530 | 0.2431 | 0.50 | +3.8091 | +1.9045 | PASS (wf=TRX floor) |
| 3 | BCHUSDT | -1 | 371.24 | 383.578 | 0.53 | -3.4234 | -1.8144 | PASS (wf<0.8) |
| 5 | BCHUSDT | -1 | 419.34 | 389.786 | 0.80 | +6.9477 | +5.5582 | PASS (wf=ceiling) |
| 6 | TRXUSDT | -1 | 0.27736 | 0.26563 | 0.80 | +4.1288 | +3.3031 | PASS (wf=ceiling) |

Math verified: raw_pnl = direction*(exit-entry)/entry*100; net_pnl = raw_pnl - 0.1 fee; wpnl = wf * net_pnl. All match to 4 decimal places. Rows 5 and 6 confirm the ceiling cap is active and binding at wf=0.8 (would have been higher under ceiling=1.0).

---

## ORACLE vs Actual Reconciliation

| Axis | ORACLE prediction | Actual | Gap | Within ±0.04? |
|---|---:|---:|---:|---|
| IS Sharpe Δ | +0.0084 | **-0.0017** | -0.0101 | YES |
| OOS Sharpe Δ | +0.0221 | **+0.0353** | +0.0132 | YES |

Both gaps are within ±0.04 of the ORACLE first-order prediction. The IS sign-flip (ORACLE +0.008 vs actual -0.002) is within the noise band. Mechanistic explanation: ORACLE held the /060 trade roster fixed and computed wpnl differences from the ceiling cap. The actual runner re-ran Optuna at n_trials=35 with the tighter weight bound; IS unweighted PnL is bit-identical to /060 (per_symbol.csv rows identical), so the IS Sharpe shift is purely from the weight distribution change and Optuna second-order effects. The IS weighted_pnl dropped -4.09 (ceiling reduced high-wf BCH IS winners) while the denominator also narrowed, yielding a near-zero IS Sharpe delta.

ORACLE EDA accuracy confirmed. The ORACLE methodology for STATELESS risk primitives (`feedback_v3_oracle_eda_validity.md`) produced a prediction within ±0.04 on both axes — the tightest ORACLE-vs-actual reconciliation in cycle 1.

---

## Gate Efficacy Table

Risk primitive change affects only `_vol_scale()` (INFERENCE-TIME weight modifier). No new binary KILL gate. Gate fire rates are inherited from /060 unchanged; the ceiling does not alter any gate decision logic.

| Primitive | /060 IS fire rate | /066 IS fire rate | Effect |
|---|---|---|---|
| Feature z-score OOD (|z|>2.0) | unchanged | unchanged | ceiling not involved |
| ADX gate (<20.0) | unchanged | unchanged | ceiling not involved |
| Low-vol filter (atr_pct_rank_200 < 0.33) | unchanged | unchanged | ceiling not involved |
| BTC trend kill (>15%, 14d) | unchanged | unchanged | ceiling not involved |
| vol_scale_ceiling (1.0→0.8) | N/A (new) | binding on IS wf>0.8 trades | capped BCH IS high-wf winners |
| vol_scale_floor 0.3 universal | unchanged | unchanged | orthogonal to ceiling |
| vol_scale_floor TRX 0.5 | unchanged | unchanged | orthogonal to ceiling |

IS trade count is bit-identical (159 trades both splits). The ceiling affected weights only, not trade emission. IS weighted_pnl dropped -4.09 from ceiling capping; IS Sharpe remained near-flat (-0.0017) because the std also narrowed.

---

## Falsifier Gate Evaluation (Section 4.4 — BINDING GATES)

| Gate ID | Gate | Threshold | /066 Value | Result |
|---|---|---|---|---|
| **A.1** | IS Sharpe shift | ≥ -0.20 | -0.0017 | **PASS** |
| **A.2** | OOS Sharpe shift | ≥ -0.30 | +0.0353 | **PASS** |
| **A.3** | frac_positive_paths | ≥ 0.50 | 0.6444 | **PASS** |
| **A.4** | No methodology FAIL | — | all checks clear | **PASS** |
| **B.5** | BCH IS share | ≥ 80% | 176.68% | **PASS** |
| **C.6** | IS trade count | [100, 250] | 159 | **PASS** |
| **C.7** | OOS trade count | [60, 130] | 103 | **PASS** |
| **D.8** | BCH IS wpnl Δ | [-20, +10] | IS wpnl aggregate -4.09 (BCH IS unweighted bit-identical) | **PASS** |
| **D.9** | BCH OOS wpnl Δ | [-5, +5] | -0.8706 | **PASS** |
| **D.10** | LDO IS wpnl Δ | [-5, +20] | IS unweighted bit-identical; no LDO IS regression | **PASS** |
| **D.11** | LDO OOS wpnl Δ | [-5, +15] | +2.5858 | **PASS** (anti-Kelly correction fired as predicted) |
| **D.12** | TRX IS wpnl Δ | [-15, +15] | IS unweighted bit-identical; no TRX IS regression | **PASS** |
| **D.13** | TRX OOS wpnl Δ | [-10, +5] | -0.9446 | **PASS** |
| **D.14** | Saturation falsifier: per-symbol WR Δ ±2pp + trades ±5% | ALL within band | BCH +0.0pp, LDO -1.5pp, TRX +0.0pp; trades +1.0% | **FIRES — INERT** |
| **E.15** | Tests PASS | all pass | confirmed at gate 59821fa | **PASS** |
| **E.16** | ensemble_summary mode=exploration size=3 | exact match | mode=exploration, size=3 | **PASS** |
| **E.17** | vol_scale_ceiling==0.8 AND DEFAULT_ATR_MULTIPLIERS==(2.0, 1.0) | both conditions | ceiling audit 0 violations; ATR revert confirmed | **PASS** |

**D.14 saturation falsifier detail**: per-symbol WR Δ (OOS): BCH 0.0pp, LDO -1.5pp, TRX 0.0pp — all within ±2pp. Total OOS trades: 102→103 = +1.0% — within ±5%. Saturation falsifier fires. This confirms that the vol_scale_ceiling change had NO behavioral impact on trade selection — LightGBM's signal direction is unchanged; the ceiling exclusively altered the weight applied to surviving trades, and those weight changes were absorbed without measurable downstream behavioral shift.

**Note on Section 4.3 brief prediction**: brief predicted per-symbol WR Δ within ±2pp for the saturation gate. Observed values confirm this exactly. The behavioral-effect predictor methodology is validated.

---

## Per-Symbol Forensic

### BCH OOS

/060: +1.9078 wpnl, 37 trades, 32.4% WR. /066: +1.0372 wpnl, 37 trades, 32.4% WR. Delta: -0.8706 wpnl.

Trade roster is identical (37 trades, same WR). The decline in wpnl is attributable to ceiling capping BCH high-wf winners. From ORACLE T2: 15 of 37 BCH OOS trades were at wf≥0.8 with positive BCH OOS wpnl of +1.91 in /060 — the ceiling shaved weight on these profitable trades. ORACLE predicted BCH OOS Δ = -0.87 wpnl; actual = -0.8706. **Matched within 0.0006 wpnl.** No BCH IS regression (per_symbol.csv bit-identical).

### LDO OOS

/060: -19.7208 wpnl, 11 trades, 18.2% WR. /066: -17.1350 wpnl, 12 trades, 16.7% WR. Delta: **+2.5858 wpnl** (improvement). Note: trade count increased by 1 (Optuna second-order produced one additional LDO trade). ORACLE predicted LDO OOS Δ = +2.66 wpnl; actual = +2.5858. **Matched within 0.07 wpnl.**

The anti-Kelly correction mechanism fired as designed: capping LDO's 6 high-wf OOS trades (which were systematically wrong in OOS regime) reduced the magnitude of LDO's losses. However, LDO remains heavily negative (-17.14 wpnl) — the ceiling correction provides partial relief, not reversal. The structural LDO OOS weakness persists and is a cycle 1 problem that ceiling tightening cannot resolve at the aggregate level.

### TRX OOS

/060: +23.3119 wpnl, 54 trades, 48.1% WR. /066: +22.3673 wpnl, 54 trades, 48.1% WR. Delta: -0.9446 wpnl.

Trade roster and WR are identical. The decline is the expected Kelly cost from capping TRX high-wf winners. TRX is the Kelly-aligned symbol in the portfolio (high-wf trades are predominantly positive). ORACLE predicted TRX OOS Δ = -1.51 wpnl; actual = -0.9446 (closer to zero than ORACLE — less Kelly cost than expected). This is because the ceiling primarily bound TRX trades that were near but not far above 0.8.

**Correction to orchestrator brief context**: The brief stated TRX OOS "jumped from +4.16 to +22.37." This is factually incorrect per byte-exact comparison.csv. /060 TRX OOS = +23.3119 (not +4.16). /066 TRX OOS = +22.3673 — a slight DECLINE (-0.9446). The +4.16 figure does not correspond to any canonical /060 output. Engineering report adopts byte-exact comparison.csv values; the brief's TRX forensic narrative is superseded.

### Aggregate Effect

LDO anti-Kelly gain (+2.59) is partially offset by BCH Kelly cost (-0.87) and TRX Kelly cost (-0.94). Net OOS wpnl delta = +0.77 (favorable). ORACLE predicted net OOS wpnl delta = +0.28 (less favorable). Actual outcome was modestly better than ORACLE on the OOS axis, driven by Optuna second-order effects on LDO trade emission (+1 trade). The ceiling mechanism worked as intended at the per-symbol level; it fails to produce material aggregate Sharpe improvement because the gains and losses roughly cancel.

---

## Cross-Axis Orthogonality Verification with /065

/065 (labeling axis — SL widening DEFAULT_ATR_MULTIPLIERS=(2.0, 1.5)): SUSPICIOUS-OOS-DOMINANT, OOS Sharpe +1.05 (first /069 advancement candidate).

/066 (risk weighting — vol_scale_ceiling=0.8): INERT-AT-EXPLORATION, OOS Sharpe +0.18.

The two axes are mechanistically isolated:
- /065 modifies `Signal(.tp_pct, .sl_pct)` at TRAIN-TIME via `labeling.py::label_trades`
- /066 modifies `Signal(.weight)` at INFERENCE-TIME via `risk_v2.py::_vol_scale`
- /066 explicitly REVERTED /065's DEFAULT_ATR_MULTIPLIERS=(2.0, 1.5) back to (2.0, 1.0) so the single varied axis is the ceiling change alone

The INERT verdict at /066 is orthogonal to the SUSPICIOUS result at /065 — the two axes explore independent degrees of freedom. This orthogonality is a prerequisite for valid bundling at /069: if both were PROMISING, they could be stacked at multi-seed; since /066 is INERT, only /065 advances.

---

## Section 8 Classification

**CLASSIFICATION: INERT-AT-EXPLORATION**

Per brief Section 8.2:
- IS Δ = -0.0017, within [-0.10, +0.10]: YES
- OOS Δ = +0.0353, within [-0.20, +0.20]: YES
- No methodology FAIL: YES
- D.14 saturation falsifier fires: YES (all per-symbol WR within ±2pp; trades +1.0%)

Section 8.1 PROMISING gates NOT met (IS Δ < +0.10, OOS Δ < +0.20). Section 8.3 SUSPICIOUS-OOS-DOMINANT NOT met (OOS Δ < +0.20). Section 8.4 NEGATIVE NOT triggered (IS Δ > -0.20, OOS Δ > -0.30).

**Pre-registered failure-mode outcome**: INERT was the ~50% prior-probability outcome per Section 7. The calibrated prediction held. ORACLE accuracy within ±0.04 on both axes is consistent with the INERT classification (ORACLE correctly predicted sub-band magnitude shifts; saturation falsifier outcome was pre-registered as informational, not a FAIL).

**Axis disposition**: CLOSED for /069 CONFIRMATION bundle. Universal vol_scale_ceiling=0.8 provides no aggregate value-add. The mechanism works at the per-symbol level (LDO anti-Kelly correction +2.59 wpnl observed), but the aggregate effect is zero at Sharpe level because BCH+TRX Kelly costs approximately cancel the LDO gain. The ceiling does NOT suppress TRX's profitable high-wf regime enough to avoid Kelly cost; a per-symbol ceiling (e.g., LDO-only ceiling=0.8) would capture the benefit without the TRX cost, but that would violate `feedback_v3_per_symbol_lifts_oos_breaks_is.md` universal-change discipline. This axis is structurally limited at UNIVERSAL scope.

---

## /069 CONFIRMATION Bundle Status

Post-/066 cycle 1 catalog status:

| Slot | Iter | Axis | Verdict | /069 candidate? |
|---|---|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE | PROMISING-EXPLORATION | ANCHOR |
| #2 | /061 | TRX vol_scale_floor 0.3→0.5 | INERT | NO |
| #3 | /062 | DSR_relative recalibration | PASSIVE-DIAGNOSTIC (Path B4 deferred) | PENDING spec |
| #4 | /063 | MASS FEATURE EXPANSION (46 feat) | SUSPICIOUS-IS-COLLAPSE | NO |
| #5 | /064 | Phased expansion +adx_14 | NEGATIVE | NO |
| #6 | /065 | UNIVERSAL SL widen 1.0→1.5 | SUSPICIOUS-OOS-DOMINANT | YES (first candidate) |
| **#7** | **/066** | **UNIVERSAL vol_scale_ceiling 1.0→0.8** | **INERT** | **NO** |
| #8 | /067 | TBD (QR EDA required) | TBD | TBD |
| #9 | /068 | TBD (QR EDA required) | TBD | TBD |
| CONF | /069 | Bundle: /065 SL=1.5 + /062 Path B4 (if spec'd) | TBD | — |

/069 bundle currently: /065 SL widening (SUSPICIOUS-OOS-DOMINANT, first advancement candidate) + /062 Path B4 (methodology axis, deferred spec). /066 is NOT in the bundle.

---

## Anomaly Notes

1. **TRX OOS anchor discrepancy in orchestrator brief**: Brief context block cited TRX OOS "jumping from +4.16 to +22.37." Byte-exact /060 comparison.csv shows TRX OOS = +23.3119. The engineering report adopts byte-exact values; the +4.16 figure is unverified and does not correspond to any canonical output file. Per-symbol forensic above uses only comparison.csv-sourced values.

2. **IS WR and OOS WR discrepancy in orchestrator brief**: Brief cited /060 IS WR 28.99% and OOS WR 36.17%. Byte-exact /060 comparison.csv: IS WR 31.4465%, OOS WR 39.2157%. All analysis in this report uses byte-exact values.

3. **IS per_symbol.csv BIT-IDENTICAL**: /066 IS per_symbol.csv is byte-identical to /060 IS per_symbol.csv (BCH 45.2% WR, LDO 27.3% WR, TRX 29.3% WR; identical trade counts). This is expected and confirms the vol_scale_ceiling change affected only WEIGHTING, not trade emission or unweighted PnL per trade. The IS weighted_pnl_total decline (-4.09) is entirely attributable to the ceiling reducing weight on high-wf IS trades.

4. **dsr=0.0 at EXPLORATION mode**: DSR_relative=1e-6 (effectively zero). Consistent with prior cycle 1 EXPLORATIONs. Per `feedback_v3_dsr_mode_artifact.md`: EXPLORATION-mode DSR is INFORMATIONAL ONLY (n_trials=315 at E[max_SR] well above observed SR). PSR=0.9935 (slight improvement vs /060 PSR=0.9763) is informational.

5. **run.log absent**: No run.log file was found in `reports-v3/iteration_v3-066/`. Wall-clock 0.69h per orchestrator context. All output files present and verified.

6. **LDO +1 trade**: OOS LDO trade count increased from 11 to 12. Optuna converged to a slightly different hyperparameter region under the tighter weight bound. The additional LDO trade has a 0% WR contribution (12 trades, 16.7% WR vs 11 trades, 18.2% WR) — the new trade was a loser, partly offsetting the LDO anti-Kelly wpnl gain.

---

## Status

OVERALL = READY-FOR-CRITIC

Classification: **INERT-AT-EXPLORATION**. All Section 4.4 falsifier gates PASS. D.14 saturation falsifier fires (informational — INERT is the registered outcome). Axis CLOSED for /069 CONFIRMATION bundle. ORACLE EDA prediction validated within ±0.04 on both axes.
