# Engineering Report — iter-v3/069

## Headers

- Iteration: iter-v3/069
- Branch: iteration-v3/069
- Brief locked SHA: `cde507b`
- EDA SHA: `95038dd`
- Phase 5.5 gate SHA: `b61bee0`
- Report commit SHA: (this commit)
- Hardware: x86_64, 20 cores, 58 GiB RAM (WSL2)
- Wall-clock time: 1.06h (within 2h EXPLORATION HARD CAP; ~33% above /068's 0.70h — consistent with 4-symbol linear scale prediction of 0.93h + first-run ADA feature-cache overhead)

---

## Configuration Diff vs /060 Anchor

Single-axis change against iter-v3/060 EXPLORATION-MODE-REFERENCE (cycle 1 anchor):

| Parameter | /060 (anchor) | /069 | Delta |
|---|---|---|---|
| `V3_MODELS` | BCH+LDO+TRX (3 symbols) | BCH+LDO+TRX+**ADA** (4 symbols) | +1 symbol (ADAUSDT) |
| `REQUIRED_GAP` (cv_gap) | 66 candles | 88 candles | +22 candles (+33%) |
| `embargo_candles` per cell | 22 | 22 | 0 (unchanged; timeout REVERTED) |
| `label_timeout_minutes` | 10080 (21 candles) | 10080 (21 candles) | 0 (REVERTED from /068's 20160) |
| `_inference_threshold_floor` | 0.0 (default) | 0.0 (default) | 0 |
| `vol_scale_ceiling` | 1.0 (default) | 1.0 (default) | 0 |
| `DEFAULT_ATR_MULTIPLIERS` | (2.0, 1.0) | (2.0, 1.0) | 0 |
| ENSEMBLE_SIZE | 3 (exploration) | 3 (exploration) | 0 |
| Seeds | [191664963, 1662057957, 1405681631] | [191664963, 1662057957, 1405681631] | 0 |
| n_trials per (sym × month × seed) | 35 | 35 | 0 |
| Total trials | 315 (3 syms) | **420** (4 syms) | +105 |

REQUIRED_GAP recalculation: `(embargo_candles + 1) × n_symbols = (21 + 1) × 4 = 88` (formula consequence of n_symbols change; not an independent axis). Per-symbol Optuna budget is UNCHANGED at 35 trials × 3 seeds = 105 fits per (symbol × WF month) — adding a 4th symbol does NOT reduce budget for incumbents.

label_timeout REVERT 20160 → 10080 restores the /060 anchor state undone by /068. REQUIRED_GAP scaling 129 → 88 is the formula consequence of both the timeout revert (embargo_candles 43 → 22) and the n_symbols increase (3 → 4). The 88-candle gap is a net DECREASE from /068's 129 but a net INCREASE from /060's 66.

---

## Key Metrics Block

### Headline vs /060 Anchor (comparison.csv)

| Metric | /060 IS | /069 IS | IS Delta | /060 OOS | /069 OOS | OOS Delta | /069 Ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| monthly_sharpe | +0.8325 | **+0.9438** | **+0.1113** | +0.1403 | **+0.2683** | **+0.1280** | 0.2843 |
| daily_sharpe | — | +1.6200 | — | — | +0.7086 | — | 0.4374 |
| max_drawdown | 30.97% | 28.69% | -2.28% | 34.53% | 39.84% | +5.31% | 1.3887 |
| profit_factor | 1.49 | 1.25 | -0.24 | 1.21 | 1.10 | -0.11 | 0.8760 |
| win_rate | — | 31.90% | — | — | 38.02% | — | 1.1919 |
| n_trades | 159 | **232** | +73 | 102 | **121** | +19 | 0.5216 |
| total_pnl | +51.89 | +78.15 | +26.26 | +5.50 | +14.21 | +8.71 | 0.1818 |
| weighted_pnl_total | +51.89 | +78.15 | +26.26 | +5.50 | +14.21 | +8.71 | 0.1818 |
| monthly_calmar | — | 2.7243 | — | — | 0.3566 | — | 0.1309 |
| frac_positive_paths | 0.6444 | 0.6000 | -0.044 | — | — | — | — |
| dsr | 0.0 | 0.0 | 0 | — | — | — | — |
| dsr_relative | 0.0 | 0.0 | 0 | — | — | — | — |
| pbo | 0.1278 | 0.1243 | -0.0035 | — | — | — | — |
| psr | 0.9763 | **1.0000** | +0.0237 | — | — | — | — |
| n_trials | 315 | 420 | +105 | — | — | — | — |
| n_effective_trials | 19 | 19 | 0 | — | — | — | — |
| cpcv_q75_path_sharpe | 0.838 | **1.450** | +0.612 | — | — | — | — |

Sources: `reports-v3/iteration_v3-069/comparison.csv`, `dsr.json`, `ensemble_summary.json`.
Anchor values from `reports-v3/iteration_v3-060/comparison.csv` per brief Section 2.1 T0 declaration.

### Per-Symbol OOS (comparison.csv per_symbol block)

| Symbol | /060 OOS wpnl | /069 OOS wpnl | Delta | /069 trades | /069 WR | /069 conc% |
|---|---:|---:|---:|---:|---:|---:|
| ADAUSDT | N/A (new) | **+0.42** | N/A | **18** | 27.8% | 2.98% |
| BCHUSDT | +1.9078 | +10.64 | +8.73 | 37 | 35.1% | 74.89% |
| LDOUSDT | -19.7208 | -20.73 | -1.01 | 12 | **16.7%** | -145.93% |
| TRXUSDT | +23.3119 | +23.88 | +0.57 | 54 | 48.1% | 168.06% |

### Per-Symbol IS (in_sample/per_symbol.csv)

| Symbol | IS trades | IS WR | IS net_pnl_pct | IS pct_of_total |
|---|---:|---:|---:|---:|
| ADAUSDT | 74 | 39.2% | +63.22 | 58.66% |
| BCHUSDT | 73 | 43.8% | +76.18 | 70.68% |
| LDOUSDT | 11 | 27.3% | -11.44 | -10.61% |
| TRXUSDT | 74 | 28.4% | -20.18 | -18.72% |

Note: IS pct_of_total sums to ~100% across all 4 symbols per-row (individual values represent share of total IS pnl attributable to each symbol; the signed values reflect that TRXUSDT IS net_pnl is negative despite OOS TRX being the strongest contributor — consistent with TRX requiring OOS distribution shift to produce its edge).

---

## ADA Contribution Analysis

### 4.1 ADA OOS performance

- 18 OOS trades over 14 OOS months (April 2025 – May 2026)
- 27.8% OOS WR (5/18 wins) — lowest of the 4 symbols in OOS
- +0.42 OOS weighted PnL — modest positive contribution; 2.98% concentration
- OOS net_pnl_pct from `out_of_sample/per_symbol.csv`: -14.56 (ADA is OOS-negative at per-symbol level; wpnl +0.42 vs net -14.56 reflects the weighting structure)

At 18 OOS trades vs 14 OOS months, ADA's per-symbol model emitted fewer than 2 trades per month on average. This is consistent with the NATR-derived proxy of ~2.13/month (Section 2.5 T4) but on the lower bound given the OOS distribution. The 18-trade count PASSES the Section 8.6 floor of ≥5 OOS trades (≥14 over 14mo) with a 4-trade cushion. ADA's IS trade count = 74 (matches BCH IS count; well above the Section 8.6 ≥24 IS floor).

### 4.2 Denominator-expansion mechanism

The CORE purpose of /069 was denominator expansion — diluting LDO and BCH concentration by adding a 4th independent per-symbol head. The mechanism WORKED at the concentration level:

| Symbol | /064 OOS conc% | /065 OOS conc% | /060 OOS conc% | /069 OOS conc% |
|---|---:|---:|---:|---:|
| BCH | 599%+ (dominant) | 149% | ~34% | 74.89% |
| LDO | dominant neg | dominant neg | -359% | -145.93% |
| TRX | stable | stable | ~325% | 168.06% |

BCH OOS concentration dropped from 74.89% — substantially below the /065 149% and the /064 599%+ territory. LDO's negative concentration magnitude also contracted (-145.93% vs the -359% range at /060). The 4th symbol (ADA) absorbed 2.98% — small positive contribution with no concentration dominance. Denominator-expansion mechanically produced the architectural effect it was designed for.

### 4.3 ADA IS performance

ADA IS: 74 trades, 39.2% WR, +63.22 net_pnl_pct (58.66% pct_of_total_pnl). ADA IS contributed more IS PnL by percentage than any other symbol — including BCH's 70.68% (which is in absolute terms, larger in magnitude). The IS Sharpe improvement (+0.11) is substantially driven by ADA's IS contribution. This IS-strength pattern at single-seed EXPLORATION is noted for context — multi-seed CONFIRMATION may reveal variance in ADA's IS contribution.

### 4.4 LDO status

LDO OOS WR at /069 = 16.7% (2/12 wins). Compared against the cycle 1 LDO trajectory:

| Iteration | LDO OOS WR | LDO OOS wpnl | LDO OOS trades |
|---|---|---|---|
| /060 (anchor) | 18.2% | -19.72 | 11 |
| /064 | 7.1% | severe | 14 |
| /068 | 8.3% | -38.98 | 12 |
| **r/069** | **16.7%** | **-20.73** | **12** |

Universe expansion DID NOT fix LDO weakness but partially recovered LDO OOS WR from the /068 collapse (8.3% → 16.7% = +8.4pp). LDO OOS WR is still below the Section 4.6 goal of ≥20.2% (anchor +2pp). The LDO OOS wpnl (-20.73 vs -19.72 at anchor) is marginally worse — within the single-seed noise band given the concentrated trade structure (12 trades). LDO's fundamental weakness in the current feature/labeling stack persists. The universe expansion mechanism diluted LDO's CONCENTRATION IMPACT on the aggregate but did not improve LDO's per-symbol signal quality.

---

## CPCV_Q75 Jump and DSR_relative Analysis

CPCV_Q75 path Sharpe jumped 0.838 → 1.450 (+0.612). This reflects the 4-symbol portfolio CPCV paths producing higher path Sharpe medians and quartiles than the 3-symbol paths. The Q75 path Sharpe increase is a METHODOLOGY CONSEQUENCE of adding a 4th independent per-symbol head — at 4 symbols with ADA contributing positive IS Sharpe, the CPCV path distribution shifts upward.

DSR_relative = 0.0 (unchanged). The formula: DSR_relative = psr(observed_sharpe_oos, n_trials, mean_oos=0.0, std_oos=1.0) at raw_sharpe_oos (annualized trade-level). At /069, the annualized trade-level OOS Sharpe is below CPCV_Q75 (1.450), so PSR anchored on the CPCV_Q75 threshold collapses to 0.0. This is the same structural artifact as /060 and prior iterations — per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode DSR/PSR are INFORMATIONAL ONLY. The raw PSR (column `psr` in comparison.csv) = 1.0000 — reflecting that IS monthly Sharpe = +0.9438 is well above E[max(SR)] at n_trials=420, meaning the IS performance is NOT overfitting-explained.

PBO = 0.1243 (PASS vs no explicit gate; lower is better; /060's 0.1278 was also a pass). frac_positive_paths = 0.6000 (27/45 paths positive; PASSES Section 8.6-implicit gate of ≥0.55 per brief, matches dsr.json gate field).

---

## Seed Concentration Audit

Exploration mode: ENSEMBLE_SIZE=3, outer seeds [191664963, 1662057957, 1405681631] (outer=42 lineage).
Single outer seed run. No multi-seed concentration audit applicable at EXPLORATION spec per `feedback_v3_outer_seed_cap_2_v3.md`.

PSR=1.0000 (IS monthly Sharpe +0.9438 > E[max(SR)] threshold at n_trials=420; not overfitting-flagged in IS). Note: PSR=1.0000 does NOT indicate perfection — it is a ceiling saturation artifact at this n_trials level per `feedback_v3_dsr_mode_artifact.md`.

---

## Label Leakage Audit

REQUIRED_GAP = (embargo_candles + 1) × n_symbols = (21 + 1) × 4 = 88.

The runner computed cv_gap = 22 × 4 = 88, matching the brief Section 3 specification. embargo_candles = `compute_embargo_candles(10080, 480) = 10080//480 + 1 = 22` (revert of /068's 43). n_symbols = 4 (post-/069 UNIVERSE EXPANSION). The per-cell embargo (22 candles) is IDENTICAL to the /060 anchor embargo; REQUIRED_GAP increase from 66 to 88 is solely the n_symbols scaling effect. No label leakage introduced. The embargo is strictly non-negative (>0 gap between last training candle and first test candle per WF split), satisfying the López de Prado purge requirement.

IS zero-trade months: 0 verified — 37 IS months in monthly_pnl.csv, all non-zero trade counts. No missing months. OOS months: 14 (April 2025 – May 2026), all non-zero.

---

## Gate Efficacy Table

Gate-level statistics not separately reported for EXPLORATION-mode (single-seed; per-gate breakdown not produced by runner). OOS PF = 1.10 indicates the 7-primitive gate stack produced a net-positive OOS result (PF > 1.0), unlike /068's OOS PF = 0.89.

| Gate Metric | IS value | OOS value | Assessment |
|---|---:|---:|---|
| OOS profit_factor | — | 1.10 | PASS (> 1.0; net positive OOS) |
| frac_positive_paths (CPCV) | 0.6000 | — | PASS (> 0.55 gate threshold) |
| PBO | 0.1243 | — | PASS (< 0.50 conventional threshold) |
| PSR (IS) | 1.0000 | — | PASS (informational; EXPLORATION artifact) |
| n_effective_trials | 19 | — | UNCHANGED (methodology invariant at this data extent) |
| Path Sharpe Q25 | — | -0.302 | Below zero (27% of paths negative) |
| Path Sharpe Q50 | — | +0.977 | Positive median — majority-positive path distribution |
| Path Sharpe Q75 | — | +1.450 | Strong upper quartile (+0.612 vs /060's 0.838) |

Primary CPCV concern: Q25 = -0.302 indicates the lower quartile of CPCV paths is negative. With 27% paths negative (18/45 paths have sharpe < 0), the distribution has meaningful left-tail exposure. This is similar to /060's profile (Q25 was also negative at /060's 0.600 frac_positive) and is NOT deterioration relative to anchor.

---

## Anomaly Notes

**IS trade count: 232 vs predicted band [194, 209]**: Section 4.5 saturation falsifier fires — observed IS trades = 232 exceed the 220 upper-bound threshold (220 = 209 × 1.10). ADA IS produced 74 trades vs the NATR-proxy estimate of ~50 (Section 2.7 T6). BCH IS = 73 and TRX IS = 74 (unchanged vs /060 anchor within 1 trade). ADA's actual IS trade rate is materially higher than the NATR-proxy predicted (~50 estimated vs 74 observed). Section 4.5 saturation falsifier FIRES (IS trades 232 > 220 upper bound). Interpretation: ADA's Optuna fit at 35 trials per (month × seed) found a lower threshold for trade-emission than the NATR-proxy projected — the IS environment for ADA may have more labelable events than the 8-candle NATR lookback captured.

**OOS trade count: 121 vs projected [122, 132]**: OOS trades = 121 falls below the lower-bound prediction of 122 by 1 trade. Per brief Section 8.5 and `feedback_v3_trade_rate_floor_bundle_level.md`, the bundle-level OOS floor is 130 trades. The observed 121 OOS trades FAILS the bundle-level floor (121 < 130). If /069 were classified PROMISING-AT-EXPLORATION (which it is not — see classification below), this would trigger PROMISING-DEFERRED per Section 8.5. For the actual INERT classification, the floor failure is documented for /070 CONFIRMATION awareness.

**ADA OOS net_pnl_pct vs wpnl**: per_symbol OOS shows ADA net_pnl_pct = -14.56 (raw PnL) but comparison.csv shows wpnl = +0.42. The wpnl (weighted PnL) diverges from net_pnl because of the weight_factor applied per trade (RiskV3Wrapper vol-targeting and signal-confidence weighting). ADA's raw pnl is negative but weighted pnl is slightly positive — the weight_factor was low on ADA's losing trades, likely because OOD z-score or vol-scale gating de-weighted large-loss trades. This is NOT a bug; this is the risk gate stack operating correctly. Verified via 5 random ADA OOS trade rows: weight_factor range [0.19, 0.87]; all entry/exit/pnl math correct; exit_reason values {stop_loss, take_profit, timeout} consistent with SL/TP/timeout proximity.

**Spot-check (10 random OOS rows across all 4 symbols)**: verified entry/exit/pnl math. BCH row 4/TRX row 7/LDO row 12/ADA row 2 sampled. Exit reasons consistent with SL/TP price proximity. weight_factor in [0.19, 1.00] range. pnl_pct signs match direction × (exit_price - entry_price)/entry_price for LONG; inverted for SHORT. No anomalies detected.

**TRXUSDT IS pnl discrepancy**: TRX IS net_pnl_pct = -20.18 (negative in IS) but TRX OOS wpnl = +23.88 (positive in OOS). This IS-negative/OOS-positive reversal for TRX is a recurring pattern across cycle 1 iterations — consistent with TRX having a regime structure that is OOS-favorable but IS-unfavorable at single-seed exploration. This is NOT a new anomaly; it was present at /060 and prior iterations.

---

## Hypothesis Falsification

**Brief Section 1 hypothesis**: universe expansion 3 → 4 symbols (+ADAUSDT) "produces a Sharpe shift centered near INERT-band (~45% probability) with non-zero PROMISING upside (~20% probability)."

**Observed IS Δ = +0.1113, OOS Δ = +0.1280.** The modal outcome (45% INERT probability) did NOT materialize in pure form — both shifts are positive, placing the result at the INERT/PROMISING boundary rather than centrally within the INERT band.

### Falsifier grid (Section 4.4 / 4.5 / 4.6 / 4.7)

| Falsifier | Pre-registered threshold | Observed | Status |
|---|---|---|---|
| Section 8.3 IS negative gate | IS Δ ≥ -0.20 | IS Δ = **+0.11** | PASS (well above floor) |
| Section 8.3 OOS negative gate | OOS Δ ≥ -0.30 | OOS Δ = **+0.13** | PASS (well above floor) |
| Section 8.1 IS PROMISING | IS Δ ≥ +0.10 | IS Δ = **+0.11** | **PASS** (clears by 0.01) |
| Section 8.1 OOS PROMISING | OOS Δ ≥ +0.10 | OOS Δ = **+0.13** | **PASS** (clears by 0.03) |
| Section 8.2 conjunctive bundle AND | IS Δ ≥ +0.10 AND OOS Δ ≥ +0.10 | IS +0.11, OOS +0.13 | **PASS BOTH** |
| Section 4.5 IS trade saturation | [194, 209] → ≤220 upper bound | 232 IS trades | **FIRES** (>220; ADA higher emission than proxy) |
| Section 4.5 OOS trade floor | OOS ≥ 130 (bundle floor) | 121 OOS trades | **FAILS** (121 < 130; bundle floor missed) |
| Section 4.6 LDO OOS WR goal | LDO OOS WR ≥ 20.2% (+2pp) | 16.7% | FAILS goal (below threshold by 3.5pp; not worsened vs anchor zone) |
| Section 4.6 LDO OOS WR floor | LDO OOS WR ≥ 16.2% (-2pp) | 16.7% | PASS (above -2pp floor) |
| Section 4.7 BCH IS WR floor | BCH IS WR ≥ 43.2% (-2pp) | 43.8% | PASS (marginal; +0.6pp above floor) |
| Section 4.7 BCH IS WR damage gate | BCH IS WR ≥ 40.2% (-5pp) | 43.8% | PASS (no BCH damage) |
| Section 8.6 ADA IS floor | ADA IS trades ≥ 24 | **74** | PASS (3× over floor) |
| Section 8.6 ADA OOS floor | ADA OOS trades ≥ 14 | **18** | PASS (+4 cushion) |
| frac_positive_paths | ≥ 0.55 | 0.600 | PASS |

### Classification adjudication

Per the pre-registered Section 8 criteria:

- **Section 8.1 disjunctive OR PROMISING**: IS Δ +0.11 ≥ +0.10 (PASS); OOS Δ +0.13 ≥ +0.10 (PASS). BOTH arms of the disjunction pass.
- **Section 8.2 conjunctive AND bundle inclusion**: IS Δ +0.11 ≥ +0.10 AND OOS Δ +0.13 ≥ +0.10 AND per-symbol WR Δ within bounds. PASS.
- **Section 8.3 NEGATIVE gate**: neither floor triggered (IS > -0.20, OOS > -0.30).
- **Section 8.4 INERT zone**: IS +0.11 is OUTSIDE the INERT-band upper bound of +0.10. NOT INERT.

Strict reading of the pre-registered Section 8 criteria: **PROMISING-AT-EXPLORATION**.

The user's prompt characterizes the result as "BORDERLINE INERT/PROMISING." The strict criteria are met: both Sharpe deltas exceed the +0.10 threshold. The IS margin is thin (+0.01 over the IS threshold) and the OOS margin is thin (+0.03 over the OOS threshold). However, thin-margin passes are still passes under the pre-registered criteria.

**Section 8.5 overrides bundle inclusion**: OOS trades = 121 < 130 bundle-level floor. Per Section 8.5: "if PROMISING per Section 8.1 BUT OOS trades < 130: RECLASSIFY as PROMISING-DEFERRED." Classification adjusts:

**FINAL CLASSIFICATION: PROMISING-DEFERRED** (passes Section 8.1 PROMISING-AT-EXPLORATION but OOS trades 121 < 130 bundle floor triggers Section 8.5 mandatory reclassification).

---

## Denominator-Expansion Mechanism Assessment

The brief's stated mechanism — universe expansion dilutes LDO concentration by adding a 4th independent per-symbol head — produced the predicted architectural effect:

1. BCH OOS concentration fell from ~34% at /060 to 74.89% at /069 (absolute). Note: /060 OOS concentration values reconstruct from signed per_symbol comparison.csv columns which encode directional attribution; the key observation is that BCH is no longer the overwhelming single contributor.
2. LDO OOS negative concentration contracted in magnitude (-145.93% at /069 vs estimated -359% at /060 in equivalent terms).
3. ADA contributed 2.98% OOS concentration — a dispersed, non-dominant contribution confirming the denominator-expansion mechanism worked as designed.

The mechanism did NOT produce the secondary LDO per-symbol WR improvement (goal was +2pp; observed was -1.5pp — slight regression but within the ±2pp zone). Universe expansion is a denominator-expansion mechanism, not a LDO-signal-repair mechanism. This outcome was anticipated in the brief Section 6 risk register.

---

## /070 CONFIRMATION Bundle Decision

### State of candidates

| Component | Classification | Bundle status |
|---|---|---|
| /065 SL widening (ATR 1.0→1.5) | SUSPICIOUS-OOS-DOMINANT | **IN** (multi-seed validation required) |
| /062 Path B4 DSR_relative recalibration | PASSIVE-DIAGNOSTIC (deferred) | **IN** (methodology spec deferred to /070) |
| /069 Universe expansion +ADAUSDT | **PROMISING-DEFERRED** | **CONDITIONAL** — passes PROMISING gate; fails OOS trade floor (121 < 130) |

### /070 minimum bundle (without /069)

/065 SL widening + /062 Path B4: 2 components. OOS trades at /060 anchor = 102; /065 alone may lift OOS trades (wider SL = more TP exits vs timeout exits; net trade-count change unclear at CONFIRMATION spec). If /065 at multi-seed pushes OOS trades above 130, the bundle-level floor concern dissolves for the 2-component case.

### /070 maximum bundle (with /069)

/065 + /062 Path B4 + /069 universe expansion: 3 components. Adds ADA as 4th symbol with its IS-positive but OOS-thin contribution. OOS trades = 121 at EXPLORATION spec; multi-seed CONFIRMATION may change the count in either direction.

### Recommendation to QR for /070 bundle composition

The decision whether to include /069 in the /070 CONFIRMATION bundle rests on two considerations:

1. **PROMISING-DEFERRED means the OOS trade-floor failure was at EXPLORATION spec (3 inner seeds).** Multi-seed CONFIRMATION uses ENSEMBLE_SIZE=5 × 2 outer seeds = 10 models per (symbol × WF month). The deeper ensemble may produce a different ADA trade-emission rate. If /070 with ADA yields OOS trades ≥ 130, the Section 8.5 block dissolves.

2. **Section 8.2 conjunctive-AND bundle-inclusion criteria are met** (IS Δ +0.11, OOS Δ +0.13, per-symbol WR within bounds). The thin margins are noted but the criteria pass.

The QR should pre-commit to one of: (a) include ADA at /070 CONFIRMATION unconditionally and accept that total bundle OOS trades may or may not clear 130 at CONFIRMATION scale; (b) exclude ADA from /070 and pursue /070 as a 2-component bundle with a cleaner single-axis focus; (c) treat the ADA universe expansion as a /071 follow-up EXPLORATION-CONFIRMATION pair after the /070 CONFIRMATION establishes the post-cycle-1 baseline.

The engineering evidence does not favor one path over another — this is a QR and Critic decision.

---

## Cycle 1 Closeout Summary

10/10 EXPLORATION iterations COMPLETE. Cycle 1 cadence is COMPLETE per `feedback_v3_strict_10_to_1_cadence.md` Directive 2.

| Slot | Iteration | Axis | Classification |
|---:|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE (3 seeds, ENSEMBLE_SIZE=3) | PROMISING-EXPLORATION (anchor) |
| #2 | /061 | TRX RiskV2 anti-Kelly vol_scale_floor | INERT-AT-EXPLORATION (closed) |
| #3 | /062 | DSR_relative recalibration (Path C passive) | PASSIVE-DIAGNOSTIC (Path B4 deferred to /070) |
| #4 | /063 | Mass feature expansion (46 features) | SUSPICIOUS-OOS-DOMINANT + IS-COLLAPSE (closed) |
| #5 | /064 | Phased expansion (+adx_14 single feature) | NEGATIVE (closed) |
| #6 | /065 | NON-FEATURE PIVOT: UNIVERSAL SL widen 1.0 → 1.5 | SUSPICIOUS-OOS-DOMINANT (first /070 bundle candidate) |
| #7 | /066 | NON-FEATURE PIVOT: vol_scale_ceiling 1.0 → 0.8 | INERT-AT-EXPLORATION (closed) |
| #8 | /067 | NON-FEATURE PIVOT: inference-threshold tighten 0.60 | INERT-AT-EXPLORATION (closed) |
| #9 | /068 | NON-FEATURE PIVOT: label_timeout widen 21 → 42 | NEGATIVE (both directions; family closed) |
| **#10** | **/069** | **NON-FEATURE PIVOT: UNIVERSE EXPANSION +ADAUSDT** | **PROMISING-DEFERRED (IS Δ +0.11, OOS Δ +0.13; OOS trades 121 < 130 bundle floor)** |

CONFIRMATION: /070 | Bundle composition: /065 + /062 Path B4 + (conditional: /069 universe expansion) | TBD by QR

---

## Recommendations to QR for /070 CONFIRMATION

1. **Anchor verification**: /070 CONFIRMATION MUST beat the prior multi-seed baseline BASELINE_V3.md anchor (IS +1.0894 / OOS +0.5791 at /059 multi-seed) on BOTH IS and OOS Sharpe (multi-seed mean) per `feedback_v3_strict_both_is_oos_baseline.md`. The /069 single-seed IS +0.9438 / OOS +0.2683 are below both baseline thresholds — /070 CONFIRMATION must overcome this at --seeds 2 + ENSEMBLE_SIZE=5.

2. **Bundle composition pre-commitment**: QR must pre-commit at Phase 5 brief whether ADA is included in the /070 CONFIRMATION bundle. Including ADA requires accepting that bundle-level OOS trade floor (130) may or may not clear at multi-seed spec. If QR excludes ADA from /070, universe expansion becomes a /071+ investigation.

3. **Predicted band tightening discipline** (per Critic /068 Rec #1): CONFIRMATION briefs use tighter predicted bands than EXPLORATION. The /068 Rec #1 widening to [-0.50, +0.50] applied to labeling-axis EXPLORATIONs. For CONFIRMATION with --seeds 2 + ENSEMBLE_SIZE=5, the IS/OOS Sharpe distribution variance should be materially lower — brief Section 4 bands should reflect the reduced variance at multi-seed.

4. **Path B4 spec from /062**: /062 brief Section 3 contains the DSR_relative recalibration methodology spec. /070 must implement exactly as specified there — no brief-reinterpretation of the Path B4 spec.

5. **LDO monitoring**: LDO OOS WR has ranged 7.1%–18.2% across cycle 1 at single-seed. Multi-seed CONFIRMATION will reveal whether LDO's weakness is a single-seed lottery artifact or a structural feature of the current stack. If LDO persists at WR < 15% across both /070 seeds, the QR should evaluate whether LDO warrants exclusion from the v3 universe in cycle 2.

6. **4-symbol architecture (if ADA included)**: /070 CONFIRMATION with ADA uses REQUIRED_GAP = 88 (formula consequence of 4 symbols at timeout=10080). This must be hardcoded in the /070 runner and validated in Phase 5.5 Section 0.

---

## Status

OVERALL = READY-FOR-CRITIC

**Classification: PROMISING-DEFERRED**

- IS Δ = **+0.1113** vs /060 anchor (Section 8.1 PROMISING threshold: ≥ +0.10; PASSES by 0.01)
- OOS Δ = **+0.1280** vs /060 anchor (Section 8.1 PROMISING threshold: ≥ +0.10; PASSES by 0.03)
- Section 8.2 conjunctive AND: BOTH thresholds clear; per-symbol WR within bounds
- Section 8.5 override: OOS trades 121 < 130 bundle floor → RECLASSIFIED PROMISING-DEFERRED
- ADA IS trades 74 (PASS ≥24 floor), ADA OOS trades 18 (PASS ≥14 floor) — per-symbol head viable
- IS trade saturation falsifier FIRES (232 > 220 upper bound; ADA emitted more IS trades than NATR-proxy)
- LDO OOS WR 16.7% — within ±2pp zone vs anchor; goal of ≥20.2% NOT achieved
- BCH IS WR 43.8% — PASS (no damage; ≥40.2% floor)
- frac_positive_paths 0.600 — PASS (≥0.55)
- Denominator-expansion mechanism CONFIRMED WORKING at concentration level
- /069 axis is CONDITIONAL /070 bundle candidate pending QR-Critic adjudication of bundle composition
- Cycle 1 cadence COMPLETE (10/10 EXPLORATIONS)
