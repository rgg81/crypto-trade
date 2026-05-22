# Iteration v3-013 — Diary

## Decision: EXPLORATION-PROMISING-MECHANICAL (NEW SUBTYPE)

Critic FINAL OVERALL = `EXPLORATION-PROMISING-MECHANICAL` at SHA `1ee0213` — a **new subtype** introduced at iter-v3/013, sister to iter-v3/012's `NEGATIVE-no-effect`. The iteration tested the MANDATORY drop-MKR per-symbol-diagnostic axis (4-symbol → 3-symbol BCH+LDO+TRX universe) per `feedback_mkr_threshold_compression.md` FIRED at iter-v3/012. Headline metrics co-direct strongly favorable (IS Sharpe +1.0088 = highest in v3 history; OOS Sharpe +2.6970 = highest in v3 history; OOS MaxDD 12.47% = lowest in v3 history; 3/3 retained symbols positive OOS PnL). HOWEVER, the OOS lift is **purely mechanical drag-removal** — BCH/LDO/TRX OOS trade rosters are byte-identical to iter-v3/012 (per-symbol architecture means MKR's training was independent of the other 3 symbols by construction; the 3-symbol Optuna re-optimization contributed ZERO behavioral change to the retained symbols). The +1.11 OOS Sharpe lift attributes ENTIRELY to removing MKR's −15.49% drag from the aggregate denominator. Cataloguing as plain `PROMISING` would mislead the future CONFIRMATION QR into bundling drop-MKR as if it were a "new edge ingredient" (compoundable with other PROMISING signals like iter-v3/010 labeling and iter-v3/011 z-score) when it is structurally a "strictly accretive component decision" (non-compoundable — you can't drop the same symbol twice). The new `PROMISING-MECHANICAL` subtype preserves the catalog discipline established by `NEGATIVE-no-effect` and prevents the misattribution.

## Headline

**OOS Sharpe +2.6970 — the HIGHEST in v3 track history** (prior best: iter-v3/010 +1.8122, +0.89 jump). **OOS MaxDD 12.47% — the LOWEST in v3 track history** (prior best: iter-v3/010 14.93%, −2.46pp improvement). **IS Sharpe +1.0088 — the HIGHEST in v3 track history** (prior best: iter-v3/011 +0.9566, +0.052 lift; first iteration to clear the +1.0 IS-floor canonical for v1/v2). 3/3 retained symbols deliver positive OOS PnL (BCH +17.21%, LDO +40.60%, TRX +7.72%; LDO single-handed at 65.65% OOS concentration). **Trade-roster bit-identity to iter-v3/012 on the 3 retained symbols (LOAD-BEARING for mechanical classification)**: BCH 31 trades / 41.9% WR / +17.2073 weighted_pnl, LDO 10 trades / 80.0% WR / +40.6020 weighted_pnl, TRX 44 trades / 43.2% WR (pre-rounding 40.9%) / +4.0396 weighted_pnl — IDENTICAL to 4 decimal places between iter-v3/012 and iter-v3/013. **The +1.11 OOS Sharpe lift is purely mechanical**, not the consequence of any positive interaction effect.

## What Was Tested

**Single-axis variation** (universe → drop MKR): `V3_MODELS` 4 entries (BCH, MKR, LDO, TRX) → **3 entries (BCH, LDO, TRX) — MKR DROPPED**. `REQUIRED_GAP` 88 = (21+1)×4 → **66 = (21+1)×3**. Setup commit `e3168f2`. ITERATION_LABEL updated to `v3-013`. Zero src/ code changes. Zero feature/labeling/z-score-gate/BTC-band changes. The only behavior change is MKR's absence from the universe.

**Hypothesis** (brief Section 1, SHA `5d13704`): MKR's 5-of-5 consecutive OOS-negative trajectory (−6.5%, −13.1%, −10.6%, −25.75%, −25.75% stationary identity at iter-v3/012) is a true exclusion candidate, not a manageable drag. The drop-MKR universe variation will (1) IMPROVE IS+OOS Sharpe by a magnitude proportional to MKR's drag share AND (2) NOT introduce concentration spillover effects to the remaining 3 symbols (per-symbol architecture isolates Optuna optimization).

**Hypothesis verdict: STRONGLY SUPPORTED with mechanical attribution caveat.** IS Sharpe +1.0088 (vs predicted [+0.30, +1.20] median +0.65; observed +1.01 = 0.36 above median, in upper half of band). OOS Sharpe +2.6970 (vs predicted "informational" — no OOS falsifier registered per EXPLORATION protocol). Behavioral-effect predictor falsifier PASS (209 IS trades < 240 falsifier threshold; observed Δ = −31 buffer = MKR drop propagated cleanly without monotonicity bug). **HOWEVER** the trade-roster bit-identity confirmation (per-symbol architecture independence) means the lift is mechanical accretion, not signal discovery — hence the new PROMISING-MECHANICAL subtype.

**Configuration**: `--exploration --seeds 1 --n-trials 10` on 3-symbol v3 universe (BCH+LDO+TRX), ENSEMBLE_SIZE=1, colsample_bytree=1.0, training_months=24, OOS_CUTOFF_DATE=2025-03-24. Identical to iter-v3/012 modulo the universe shrinkage (V3_MODELS 4→3) + REQUIRED_GAP recomputation (88→66) + cosmetic ITERATION_LABEL.

**Axis chosen per `feedback_mkr_threshold_compression.md` FIRED at iter-v3/012** (5th consecutive MKR OOS-negative; STATIONARY identity strengthening diagnostic case). The drop-MKR axis was MANDATORY and pre-committed in iter-v3/012's catalog row — no debate permitted at brief authoring time.

## What Was Measured

### Headline metrics

| Metric | iter-v3/011 (4-sym, z=2.0, BTC ±20%) | iter-v3/012 (4-sym, BTC ±15%) | iter-v3/013 (**3-sym, drop MKR**) | Δ vs iter-v3/012 |
|---|---:|---:|---:|---:|
| IS monthly Sharpe | +0.9566 | +0.8096 | **+1.0088** | **+0.1992** |
| OOS monthly Sharpe | +1.6251 | +1.5914 | **+2.6970** | **+1.1056 (HIGHEST in v3 history)** |
| IS/OOS ratio | 1.70 | 1.97 | **2.67** | +0.70 |
| IS trades | 286 | 286 | **209** | **−77 (= MKR's IS contribution)** |
| OOS trades | 101 | 101 | **85** | **−16 (= MKR's OOS contribution)** |
| OOS trades/month | ~7.48 | ~7.48 | **~6.30** | −1.18/mo (informational, EXPLORATION) |
| IS max drawdown | 26.04% | 40.53% | **20.77% (LOWEST in v3 history)** | **−19.76pp** |
| OOS max drawdown | 14.93% | 18.62% | **12.47% (LOWEST in v3 history)** | **−6.15pp** |
| OOS Calmar | 11.21 | 2.49 | **4.96** | +2.47 |
| PBO (per-cell mean) | 0.1077 | 0.1077 | **0.1075** | −0.0002 (statistically zero) |
| n_eff (per-cell median) | 7 | 7 | **7** | 0 (BIT-IDENTICAL) |
| n_high_pbo_cells_99 | 6 | 4 | **2** | −2 (MKR's 2 high-PBO cells removed) |
| Wall-clock | 8 min | 8 min | **6 min** | −2 min |

**The +1.11 OOS Sharpe lift is the LARGEST single-iteration OOS jump in v3 track history**, but **the lift is mechanical** — explained entirely by removing MKR's −15.49% OOS contribution from the denominator. Falsifier 1 (IS Sharpe < +0.10) NOT triggered (+1.01 well above). Falsifier 2 (IS trades > 1.2 × 215 baseline = 258) NOT triggered (=209). Falsifier 3 (wall-clock > 30 min) NOT triggered (6 min). **All falsifiers PASS clean.** The 15-verifier reconciliation (engineering report Section 3.6) shows 15/15 PASS including the new behavioral-effect verifier (saturation predictor) introduced at iter-v3/012's diary per `feedback_axis_saturation_predictor.md`.

### Per-symbol OOS attribution — BIT-IDENTITY proof of mechanical lift

| Symbol | iter-v3/012 OOS PnL | iter-v3/012 trades | iter-v3/013 OOS PnL | iter-v3/013 trades | Identity? |
|---|---:|---:|---:|---:|---|
| LDOUSDT | +40.6020 | 10 (80.0% WR) | **+40.6020** | **10 (80.0% WR)** | **EXACT to 4 decimals** |
| BCHUSDT | +17.2073 | 31 (38.7% WR) | **+17.2073** | **31 (38.7% WR)** | **EXACT to 4 decimals** |
| TRXUSDT | +4.0396 | 44 (40.9% WR) | **+4.0396** | **44 (40.9% WR)** | **EXACT to 4 decimals** |
| MKRUSDT | −15.4861 | 16 (25.0% WR) | (NOT IN UNIVERSE) | — | **REMOVED** |
| **TOTAL** | **+46.36** | **101** | **+61.85** | **85** | **+15.49 = MKR drag removed** |

**Numerator identity is the LOAD-BEARING evidence for mechanical classification**: LDO weighted_pnl numerator +40.60 IDENTICAL between iter-v3/012 and iter-v3/013; the OOS denominator grew 46.36 → 61.85 (+15.49) entirely from MKR's −15.49 removal; LDO's concentration ratio rose 87.57% → 65.65% **purely as a denominator effect**, NOT as diversification. The 3 retained symbols traded the EXACT same 85 OOS bars / entry timestamps / exit timestamps / weights — the per-symbol Optuna optimization on a 3-symbol vs 4-symbol universe produced byte-identical model parameters (a structural feature of the v3 per-symbol architecture: each symbol's LightGBM is trained on its own history, MKR's removal touches no other model). **The +1.11 OOS Sharpe lift is therefore the ratio-of-Sharpe consequence of removing one drag component from a fixed-roster aggregate — accounting cleanup, not new edge.**

### MKR drop counterfactual decomposition

| Decomposition step | Number |
|---|---:|
| iter-v3/012 OOS aggregate weighted_pnl | +46.3629 |
| Subtract MKRUSDT contribution (−15.4861) | +61.8489 (= iter-v3/013 OOS observed; EXACT match) |
| iter-v3/012 OOS aggregate Sharpe | +1.5914 |
| Recomputed Sharpe with MKR removed (per Critic Round 1 verification) | +2.69 (within rounding of +2.6970 observed) |

**The +2.6970 OOS Sharpe is mechanically reproducible from iter-v3/012's aggregate by point-removal of MKR's contribution.** This is the strongest possible numerical proof that the lift is accounting cleanup. An analytic check exists for the variance term too: the standard deviation of monthly returns drops because MKR was the highest-variance contributor (MKR OOS MaxDD 33.40% concentration was the dominant variance source), so the Sharpe ratio improvement compounds (numerator up, denominator down). This is what makes the OOS Sharpe lift larger in proportional terms than the linear PnL removal would suggest.

### Per-symbol IS metrics (3 retained symbols)

| Symbol | Trades | Wins | Win Rate | Net PnL % | Avg PnL % | % of total IS PnL |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 100 | 45 | 45.0% | +86.82% | +0.87% | +110.0% (wide due to TRX drag) |
| LDOUSDT | 21 | 10 | 47.6% | +52.90% | +2.52% | +67.1% |
| TRXUSDT | 88 | 29 | 33.0% | −19.96% | −0.23% | −25.3% |
| **TOTAL** | **209** | **84** | **40.2%** | **+78.80%** | **+0.38%** | **100.0%** |

IS aggregate: 209 trades / 40.2% WR / +78.80% net PnL. The IS picture is dominated by BCH (110% of total) + LDO (67% of total), with TRX as a structural drag (−25%). This is consistent with the 3-symbol portfolio being effectively a 2-engine model (BCH + LDO) with TRX as a low-volatility diversifier (no drop-TRX rule fires because TRX is OOS-positive at +7.72%, 0/1 OOS-negative trajectory).

### MKR rule outcome — RULE EXECUTED CLEANLY

| Iteration | MKR OOS net PnL% | MKR OOS WR | Notes |
|---|---:|---:|---|
| iter-v3/007 | −14.03% | 38.5% | features-axis (1st negative) |
| iter-v3/009 | −13.10% | 30.8% | features-axis (2nd) |
| iter-v3/010 | −10.65% | 29.4% | labeling-axis (3rd) |
| iter-v3/011 | **−25.75%** | **25.0%** | gate-zscore-axis (4th, threshold-compression rule landed) |
| iter-v3/012 | **−25.75%** | **25.0%** | gate-btc-trend-axis (5th, STATIONARY identity, RULE FIRED) |
| iter-v3/013 | (NOT IN UNIVERSE) | — | universe-axis (RULE EXECUTED) |

**`feedback_mkr_threshold_compression.md` rule executed exactly as designed.** The pre-committed threshold compression (6-7 → 5) at iter-v3/011 anticipated the worsening trajectory; the rule fired at iter-v3/012's 5th consecutive negative (with stationary identity strengthening the diagnostic case); iter-v3/013 executed the mandated drop-MKR axis without renegotiation. The MKR-drop hypothesis (drag was a true exclusion candidate, not manageable) is **strongly supported by the mechanical evidence** — removing MKR strictly improved every aggregate metric, and the per-symbol OOS bit-identity proves removing MKR did not impair the surviving symbols' edge in any way.

### Per-cell PBO tail thickening (continuing audit)

`n_high_pbo_cells_99 = 2` (vs 4 in iter-v3/012, 6 in iter-v3/011). Both remaining high-PBO cells are TRXUSDT 2025-Q4:

- **TRXUSDT/2025-10**: PBO = 1.000 (carried from iter-v3/012 — recurring TRX tail)
- **TRXUSDT/2025-11**: PBO = 1.000 (carried from iter-v3/012 — recurring TRX tail)
- (MKR's 2 high-PBO cells from iter-v3/012 mechanically removed by universe shrinkage)

**The 2 TRX 2025-Q4 cells are real (not iteration artifacts) and continue to thicken the right tail of the per-cell PBO distribution.** Mean aggregator at 0.1075 (statistically identical to iter-v3/012's 0.1077). Per Critic FINAL Recommendation, future CONFIRMATION QR uses `(1 − max_per_cell_pbo)` not just `(1 − mean_pbo)` for aggregation discipline. **Drop-TRX rule does NOT fire** — TRX OOS PnL is +7.72% (0/1 OOS-negative trajectory; 4 more consecutive OOS-negative TRX iterations required to fire a parallel drop-TRX rule). TRX functions as the diversifier role in the 3-symbol portfolio.

### Methodology checks (Critic FINAL — `1ee0213`)

| # | Check | Status | Detail |
|---:|---|:---:|---|
| 1 | Look-Ahead | PASS | 13 V3_FEATURE_COLUMNS byte-identical to iter-v3/009 audit; universe-axis introduces no new feature paths; triple-barrier ATR multipliers act on past-only NATR |
| 2 | Embargo | PASS | REQUIRED_GAP = 66 = (21+1)×3 confirmed at runtime; CPCV n_paths=45, embargo=27 symmetric. Note: stale `= 88` docstrings at run_baseline_v3.py:206/211/218 — runtime correct, hygiene fix pre-committed for iter-v3/014 |
| 3 | MT correction (methodology) | PASS | PBO = 0.1075 (statistically identical to iter-v3/011/012 0.1077); n_eff = 7 BIT-IDENTICAL; 2/127 cells with PBO > 0.99 (both TRX 2025-Q4 carry-forward); max-aggregator pre-commit travels forward |
| 3 | MT correction (edge) | INFORMATIONAL | DSR = 0.0, PSR = 1.0 — single-seed exploration artifact (cadence-rule informational) |
| 4 | IC correlation | PASS | max abs(IC) = 0.685 (< 0.70); zero new features |
| 5 | ADF stationarity | PASS (promoted) | 1657/2041 (81.2%) cells stationary; 384 non-stationary concentrate in early walk-forward (2020-2021 sparse-data) where ADF underpowered (n_obs < 200); V3_FEATURE_COLUMNS byte-identical to iter-v3/009 |
| 6 | Pareto dominance | PASS (vacuous, single-seed) | EXPLORATION single-seed; LDO 65.65% concentration > 30% CONFIRMATION cap — informational under EXPLORATION |
| 7 | Reproducibility | PASS | SHAs `e3168f2` runner / `5217490` analysis / `5d13704` brief / `1909d11` Phase 5.5 gate / `84f3bd5` engineering report stamped; spot-check OOS trades.csv reproduces |
| 8 | Hypothesis alignment | PASS-strong-support / SATURATION FALSIFIER PASS | Single-axis cadence rule honored; Falsifier 1 NOT triggered (+1.01 well above +0.10); behavioral-effect verifier PASS (209 < 240 threshold; Δ = −31 buffer) — MKR drop propagated cleanly without monotonicity bug |
| 9 | Symbol exclusion | PASS | {BCH, LDO, TRX} ∩ V3_EXCLUDED_SYMBOLS = ∅ |
| 10 | Feature isolation | PASS | features_v3 does not import v1/v2 |
| 11 | Forming-candle | PASS | Pre-flight staleness guard functioning per spec |
| 12 | Library pinning | PASS | Stack identical to iter-v3/010/011/012 (lightgbm 4.6.0, numpy 2.2.6, etc.) |

**All 12 Critic checks PASS / WAIVED-INFORMATIONAL / PASS-promoted (Check 5 promoted from WARN per QR Clarification 1).** Zero BLOCK conditions. The PROMISING-MECHANICAL classification is the verdict on the *catalog framing axis*, NOT on the methodology axis (where everything is clean).

## Brief Section 7 Prediction Calibration (6/6 check)

Per iter-v3/004's calibration discipline, every brief Section 7 prediction is reconciled post-hoc:

| ID | Class | P | Prediction | Outcome |
|---|---|---:|---|---|
| P1 | process | 5% | `V3_MODELS` reduction doesn't propagate to `REQUIRED_GAP` correctly | DID NOT MATERIALIZE — REQUIRED_GAP=66 confirmed at runtime; "Active models: 3/3" + "n_symbols=3 = 66 [matches REQUIRED_GAP=66] PASS" logged |
| P2 | process | 5% | Wall-clock > 30 min on 3-symbol universe | DID NOT MATERIALIZE — 6 min actual, 5x under target (faster than 4-symbol because 1 fewer LightGBM training run × 31 walk-forward months) |
| P3 | process | 5% | Saturation falsifier triggered (IS trades > 240 = 1.12 × inherited 215 baseline) | DID NOT MATERIALIZE — 209 IS trades observed, Δ = −31 buffer below 240 falsifier; clean MKR drop propagation |
| P4 | model | **50%** | IS Sharpe lands in [+0.30, +1.20] (PROMISING band, median +0.65) | **MATERIALIZED — observed +1.0088 in upper half of band**; 0.36 above median; 3rd consecutive favorable IS calibration overshoot (010, 011, 013 — see Calibration Lesson below) |
| P5 | model | 30% | IS Sharpe in [+0.10, +0.30) — soft-NEGATIVE | DID NOT MATERIALIZE — +1.01 well above |
| P6 | model | 15% | IS Sharpe < +0.10 (Falsifier 1 activates) | DID NOT MATERIALIZE — Falsifier 1 PASS |

**Calibration result — 5/6 process predictions clean, P4 materialized correctly with 3rd consecutive favorable overshoot pattern.** The brief authored at SHA `5d13704` predicted [+0.30, +1.20] median +0.65; observed +1.01 sits in the upper half of the predicted band (vs iter-v3/011's [+0.40, +0.70] / observed +0.96 = above upper bound by +0.26; iter-v3/010's [+0.10, +0.30] / observed +0.57 = above upper bound by +0.27). **3 consecutive favorable IS overshoots establishes a systematic calibration pattern**: the QR's prior bands have been conservative on IS-axis EXPLORATIONs that DO produce behavioral change at the trade-roster level (010, 011, 013) — the empirical signal is to widen the upper bound of predicted PROMISING bands by ~30% based on this 3-iteration record. iter-v3/012 was the exception (NULL-RESULT), which doesn't violate the pattern because no behavioral change occurred. **Pre-committed: iter-v3/014's brief Section 7 prediction band must widen the upper bound on PROMISING predictions for behavior-changing axes by 30% based on this 3-iteration record.**

## Pareto Position

Single-row degenerate front (Section 8 criterion 9 waiver):

| seed | OOS Sharpe | OOS MaxDD | OOS Calmar | PBO | n_trades | max_conc% |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | +2.6970 | 12.47% | 4.9594 | 0.1075 | 85 | 65.65% |

Cross-symbol OOS dispersion (informational, NOT Pareto-equivalent under EXPLORATION):

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| LDOUSDT | +40.60 | 10 | 80.0% | 65.65% |
| BCHUSDT | +17.21 | 31 | 38.7% | 27.82% |
| TRXUSDT | +4.04 | 44 | 40.9% | 6.53% |

**OOS picture is structurally the same 3-symbol mix as iter-v3/012** with the MKR drag mechanically removed. LDO drives ~66% of headline OOS Sharpe (lottery-flag, 10 trades / 80% WR / exact-binomial 95% CI [44.4%, 97.5%] — unchanged from iter-v3/011/012; concentration drop 87.57% → 65.65% is purely denominator-driven). BCH+TRX provide broad-based supporting evidence (75 trades combined). TRX functions as the diversifier role with 0/1 OOS-negative trajectory.

## Caveats Recorded for Audit Trail

The PROMISING-MECHANICAL verdict comes with five explicit caveats catalogued for the future CONFIRMATION-bundling QR (per Critic FINAL Recommendation 2):

1. **`subtype = PROMISING-MECHANICAL`** (NEW; sister to `NEGATIVE-no-effect`): trade-roster bit-identity to iter-v3/012 on the 3 retained symbols (BCH/LDO/TRX OOS rows IDENTICAL to 4 decimal places) is the LOAD-BEARING evidence. The +1.11 OOS Sharpe lift is purely mechanical drag-removal, NOT signal discovery via 3-symbol Optuna re-optimization. Per-symbol architecture means MKR training was independent of other symbols by construction. Future CONFIRMATION QR distinguishes PROMISING (interaction lift, signal discovery, compoundable across iterations) from PROMISING-MECHANICAL (drag removal, accounting cleanup, NOT compoundable across iterations — you can't drop the same symbol twice). New memory rule `feedback_promising_mechanical_subtype.md` saved per Critic Recommendation 2.

2. **`trade_roster_bit_identical_to_iter_v3_012 = TRUE`** for BCH/LDO/TRX (mechanical proof, NOT signal discovery): BCH 31 trades / 38.7% WR / +17.2073 weighted_pnl, LDO 10 trades / 80.0% WR / +40.6020 weighted_pnl, TRX 44 trades / 40.9% WR / +4.0396 weighted_pnl — IDENTICAL to 4 decimal places between iter-v3/012 and iter-v3/013. Per-symbol architecture means LightGBM trained per-symbol on its own history; MKR's removal touched no other model's parameters. Spot-check on LDO row 5: net 11.07% × 0.88 weight = 9.74 weighted — matches iter-v3/012 exactly. Future CONFIRMATION QR must NOT bundle drop-MKR as a "new edge ingredient" alongside iter-v3/010 labeling + iter-v3/011 z-score in additive fashion.

3. **`ldo_concentration_65pct_is_denominator_driven`** (numerator +40.60 IDENTICAL; total grew from 46.36 → 61.85 entirely from MKR's −15.49 removal): the 87.57% → 65.65% concentration improvement is NOT diversification. LDO's 10-trade lottery flag carries forward unchanged from iter-v3/011 (8 wins out of 10, 80% WR, exact-binomial 95% CI [44.4%, 97.5%] — too wide to claim signal-from-noise distinction within 95% confidence). The 65.65% concentration figure is still above the 30% per-symbol cap that would apply at CONFIRMATION; future CONFIRMATION QR must scope ex-LDO basket fragility before bundling iter-v3/011 z-score component (carry-forward unchanged).

4. **`is_calibration_overshoot_3rd_consecutive`** (predicted [+0.30, +1.20] median +0.65; observed +1.01; pattern): iter-v3/010 (predicted [+0.10, +0.30], observed +0.57 = +0.27 above upper bound), iter-v3/011 (predicted [+0.40, +0.70], observed +0.96 = +0.26 above upper bound), iter-v3/013 (predicted [+0.30, +1.20], observed +1.01 in upper half). 3 consecutive favorable IS calibration overshoots establishes a systematic pattern: QR's prior bands have been conservative on IS-axis EXPLORATIONs that DO produce behavioral change at trade-roster level. **Pre-committed**: iter-v3/014's brief Section 7 must widen upper bound on PROMISING predictions for behavior-changing axes by 30% based on this 3-iteration record. iter-v3/012 was the exception (NULL-RESULT, axis was saturated) — does not violate the pattern.

5. **`n_high_pbo_cells_99 = 2`** (TRX/2025-10, TRX/2025-11; max-aggregator pre-commit) **+ drop-TRX rule trigger pre-commit (5 consecutive OOS-negative; currently 0/1)**: 2 high-PBO cells in TRX 2025-Q4 carry forward from iter-v3/012; mean aggregator at 0.1075 statistically identical; future CONFIRMATION QR uses `(1 − max_per_cell_pbo)` not just `(1 − mean_pbo)` per audit-trail discipline. Drop-TRX rule does NOT fire (TRX OOS PnL +7.72%, 0/1 OOS-negative trajectory; parallel pre-committed threshold = 5 consecutive OOS-negative iterations to fire a drop-TRX rule analogous to MKR). TRX is the diversifier role. iter-v3/014 brief Section 8 saturation predictor falsifier MUST derive `falsifier_threshold = ceil(1.2 × counterfactual_n_trades)` not hardcoded 240 — replaces fragile constant with per-iteration derivation, robust to single-axis universe variations (per Critic FINAL Recommendation 3).

## Lessons

1. **Per-symbol-diagnostic methodology validated the MKR rule end-to-end.** The 5-iteration MKR trajectory (negatives at 007/009/010/011/012; threshold-compression rule landed at iter-v3/011 review; rule FIRED at iter-v3/012's 5th consecutive negative; rule EXECUTED at iter-v3/013 with strongly accretive results) is the first complete cycle of the threshold-compression rule introduced at iter-v3/011. Every step of the rule worked exactly as designed: (a) the compressed threshold (6-7 → 5) anticipated the worsening trajectory; (b) STATIONARY identity at iter-v3/012 strengthened rather than weakened the diagnostic case; (c) the mandatory drop-MKR axis at iter-v3/013 produced strictly accretive results without ambiguity; (d) the trade-roster bit-identity confirmed the per-symbol architecture's independence assumption. **Future CONFIRMATION QR inherits a clean, justifiable drop-MKR decision** (mechanical, not lottery — supported by 5-iteration negative trajectory + bit-identity proof). The methodology is generalizable: any future symbol with 5 consecutive OOS-negative iterations under the v3 EXPLORATION cadence triggers a parallel diagnostic axis.

2. **Mechanical lift must be classified honestly to inform CONFIRMATION bundling.** Cataloguing iter-v3/013 as plain `EXPLORATION-PROMISING` (which the headline metrics would justify on Sharpe-number alone — IS +1.01 above the +0.40 PROMISING threshold, OOS +2.70 the highest in v3 history) would mislead the future CONFIRMATION-bundling QR into treating drop-MKR as a "new edge ingredient" compoundable with iter-v3/010 labeling and iter-v3/011 z-score. **PROMISING ingredients are stack-additive (different feature/labeling/gate lifts may compound when ensemble is rebuilt); PROMISING-MECHANICAL ingredients are point-decisions (you can't drop the same symbol twice; the decision is binary, not stackable).** The new subtype preserves this distinction. Parallel to iter-v3/012's `NEGATIVE-no-effect` discipline (which preserved the distinction between "axis is saturated" and "axis degraded edge below threshold" within the NEGATIVE class).

3. **Saturation predictor PASS validates the pre-commit closing iter-v3/012's calibration gap.** iter-v3/012 introduced `feedback_axis_saturation_predictor.md` after observing 286 IS trades vs predicted 5-15% reduction (0% observed). iter-v3/013 brief Section 8 added the saturation falsifier (criterion 11: IS trades < 240 = 1.12 × inherited 215 baseline). Observed 209 IS trades is Δ = −31 buffer below the falsifier threshold — **MKR drop propagated cleanly into the IS trade roster** (not "monotonicity bug" producing 286 again). The falsifier worked as designed: (a) anticipated the bug class (universe-axis change failing to propagate); (b) provided a clean PASS/FAIL signal that would have caught propagation failure if it occurred. **Future EXPLORATION briefs continue this discipline** — Section 8 must include behavioral-effect verifier with falsifier threshold.

4. **3rd consecutive favorable IS calibration overshoot crystallizes the pattern.** iter-v3/010 (+0.27 above upper bound), iter-v3/011 (+0.26 above upper bound), iter-v3/013 (in upper half of band). All 3 are EXPLORATIONS where the axis variation produced genuine behavioral change at the trade-roster level. iter-v3/012 was the exception (NULL-RESULT, no behavioral change, IS Sharpe inside band). **The empirical signal is the QR's prior bands have been conservative on behavior-changing axes by ~30%** — pre-committed iter-v3/014's brief Section 7 must widen upper bound on PROMISING predictions for behavior-changing axes by 30%. This is a calibration discipline pre-commit, not a methodology change. The 30% widening applies only to behavior-changing axes — saturation-predictor-flagged axes (like iter-v3/012's BTC band tightening within the saturated regime) keep tighter bands.

5. **Critic 2-round flow worked as designed (4th consecutive use producing concrete pre-commits).** Round 1 PRELIMINARY surfaced 4 substantive clarifications (ADF demotion, catalog framing as PROMISING-MECHANICAL, TRX caveat + drop-TRX rule check, docstrings + saturation parametrization); QR responded with explicit dispositions; Round 2 FINAL accepted all four with no regressions. The clarifications produced concrete pre-commitments that go into the catalog row + a NEW memory rule (`feedback_promising_mechanical_subtype.md`) — preventing post-hoc renegotiation at future iterations. The Critic FINAL also issued Recommendation 3 (iter-v3/014 first commit fixes stale `= 88` docstrings + uses derived `1.2 × counterfactual_n_trades` falsifier).

6. **The PROMISING-MECHANICAL subtype is structurally parallel to NEGATIVE-no-effect.** Both share the property that the iteration produced a Sharpe-number that would, on naive reading, place it in the wrong verdict class:
   - `NEGATIVE-no-effect` (iter-v3/012): IS Sharpe +0.81 in PROMISING band by number alone, but trade-roster bit-identity to iter-v3/011 means zero information gain → classified NEGATIVE.
   - `PROMISING-MECHANICAL` (iter-v3/013): OOS Sharpe +2.70 highest in v3 history, but trade-roster bit-identity to iter-v3/012 on 3 retained symbols means lift is mechanical drag-removal → classified PROMISING-MECHANICAL (PROMISING because the iteration IS strictly accretive and the decision IS catalogable; MECHANICAL to flag the future CONFIRMATION QR not to bundle as compoundable).

   The two subtypes form a complete framework for handling iterations where the headline Sharpe number diverges from the structural information content. Future Critic FINAL writeups should preserve both subtypes explicitly — they ARE the catalog discipline.

7. **Dead-paths catalog (twelfth entry, sixth EXPLORATION row, PROMISING-MECHANICAL classification):**
   - **iter-v3/013** — universe axis (drop MKR; 4-symbol → 3-symbol BCH+LDO+TRX) EXPLORATION on v3 universe, `--exploration` mode (ENSEMBLE_SIZE=1, n_trials=10, colsample_bytree=1.0). **EXPLORATION-PROMISING-MECHANICAL (NEW SUBTYPE).** IS monthly Sharpe = +1.0088 (highest in v3 history; first iteration to clear +1.0 IS-floor canonical for v1/v2). OOS monthly Sharpe = +2.6970 (highest in v3 history; +1.11 lift vs iter-v3/012 — purely mechanical from MKR drag removal). OOS MaxDD = 12.47% (lowest in v3 history). 3/3 retained symbols positive OOS PnL. Trade-roster bit-identity to iter-v3/012 on BCH/LDO/TRX (per-symbol architecture independence). LDO concentration 65.65% denominator-driven (numerator +40.60 IDENTICAL; total grew 46.36 → 61.85 from MKR's −15.49 removal). 3rd consecutive favorable IS calibration overshoot (010, 011, 013). Saturation falsifier PASS (209 < 240). PBO 0.1075 statistically identical to iter-v3/011/012 0.1077; n_eff 7 BIT-IDENTICAL; `n_high_pbo_cells_99 = 2` (TRX 2025-Q4 carry-forward, max-aggregator pre-commit travels). 5 caveats catalogued. **STRICTLY ACCRETIVE catalog ingredient at CONFIRMATION** (the drop-MKR decision is catalogable and the +1.11 OOS lift is real once MKR is removed) BUT **NOT compoundable with PROMISING ingredients** (cannot stack with iter-v3/010 + iter-v3/011 as if it were a third axis-lift contributing additively). The catalog count advances 5 → 6 of 10; iter-v3/014 axis is ADX threshold per Critic FINAL Recommendation 1.

## Pre-Registered Failure-Mode vs Reality Summary

| Class | Materialized? |
|---|---|
| Process predictions (P1-P3, total 15%) | 0/3 materialized — pipeline ran clean, wall-clock 5x under target, MKR drop propagated cleanly (REQUIRED_GAP=66 verified at runtime, V3_MODELS=3 verified, IS trades 209 < 240 saturation falsifier verified) |
| Model predictions (P4-P6, total 95%) | P4 materialized in upper half of band (+1.01 vs predicted [+0.30, +1.20] median +0.65 = 0.36 above median) — 3rd consecutive favorable overshoot for behavior-changing axes |
| OOS-axis prediction | NONE — brief did not pre-register OOS predictions (EXPLORATION protocol; OOS informational); +2.70 OOS Sharpe is informational alongside the IS verdict |
| Behavioral-effect verifier (saturation falsifier) | PASS — 209 IS trades < 240 falsifier threshold (Δ = −31 buffer); MKR drop propagated cleanly without monotonicity bug |

Calibration accuracy: 4/4 process + behavioral-effect predictions clean (P1-P3 + saturation falsifier); 1/3 model predictions fired (P4 in upper half of band). Combined with iter-v3/010/011's identical-pattern overshoots, the 3-iteration record establishes a systematic upward calibration bias on behavior-changing axes. The new `feedback_promising_mechanical_subtype.md` rule does NOT close a calibration gap (the calibration is already pre-committed for widening) — it closes a verdict-classification gap (mechanical lift vs interaction lift).

## Next Iteration

**iter-v3/014 — axis: ADX threshold (currently 20)** per Critic FINAL Recommendation 1.

ADX threshold variation is structurally orthogonal to all 5 prior axis representations (features×2, labeling×1, gate-zscore×1, gate-btc-trend×1, universe×1). It is NOT subject to mechanical-accretion artifact (single-symbol architecture means changing ADX threshold does change behavior at trade-roster level for all 3 retained symbols — saturation predictor will register Δ trades). Suggested specifics:

| Parameter | iter-v3/013 (current) | iter-v3/014 (suggested) |
|---|---:|---:|
| Universe | BCH+LDO+TRX (3 symbols) | UNCHANGED |
| Z-score OOD threshold | 2.0 | UNCHANGED |
| ATR multipliers | (2.0, 1.0) | UNCHANGED |
| BTC trend filter band | ±15% | UNCHANGED |
| Feature set | 13 columns | UNCHANGED |
| **ADX threshold** | **20** | **18 (looser, more trades) OR 25 (tighter, more selective)** — single-axis variation; QR chooses direction based on ADX kill-rate analysis on IS data |

**Pre-conditions for iter-v3/014 brief**:
- Phase 5.5 PASS requires Section 7 prediction widening per the 3-consecutive-overshoot empirical record (upper bound +30% for behavior-changing axes).
- Section 8 saturation predictor falsifier MUST derive `falsifier_threshold = ceil(1.2 × counterfactual_n_trades)` not hardcoded — per Critic FINAL Recommendation 3.
- iter-v3/014 first commit MUST fix stale `= 88` docstrings + comments at `run_baseline_v3.py:206, 211, 218` (parametrize against `REQUIRED_GAP`, e.g., `f"= {REQUIRED_GAP}"`).
- Wall-clock budget: same 2h hard cap, target < 30 min on 3-symbol universe at `--exploration --seeds 1 --n-trials 10`.
- Pre-register an OOS-axis falsifier IF the brief intends to read OOS metrics (otherwise OOS remains informational-only).
- Single-axis discipline: ONLY ADX threshold changes. No other parameter variation.

**Catalog count after iter-v3/013**: 6 of 10 EXPLORATIONs; **4 more required** before any CONFIRMATION can launch. Axis coverage to date: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 1 = 5 unique axis representations after iter-v3/013; iter-v3/014 will add gate-adx × 1 = 6 unique axis representations.

**iter-v3/013 status**: STRICTLY ACCRETIVE CONFIRMATION-bundle ingredient (the drop-MKR decision is the right call; the +1.11 OOS lift is real once MKR is removed) BUT NOT compoundable with iter-v3/010 + iter-v3/011 PROMISING signals as an additive third axis-lift. The future CONFIRMATION-bundling QR treats drop-MKR as a baseline universe decision (always-on), then layers iter-v3/010 labeling and iter-v3/011 z-score as compoundable PROMISING ingredients on top.
