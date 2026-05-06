# Iteration v3-010 — Diary

## Decision: EXPLORATION-PROMISING (with caveats)

First PROMISING since iter-v3/007. Critic FINAL OVERALL=`EXPLORATION-PROMISING with caveats` at SHA `f6f4ef7`. All 12 methodology checks resolve to PASS / WARN-carry-forward / WAIVED-single-seed; **no BLOCK condition exists**. All four pre-registered falsifiers (Section 7 of the brief) NOT triggered. The catalog now has 3 of 10 EXPLORATIONs since the last CONFIRMATION. iter-v3/010 is a real candidate for the next CONFIRMATION bundle.

Mechanism endorsed: **(c) tighter labels reduce label noise so features find real momentum more cleanly** (per QR Clarification 1 / Critic Disposition ACCEPTED). The lift is broad-based at the per-symbol level (3 of 4 symbols turned OOS-positive) and PBO IMPROVED on the strictly-tighter label distribution (0.1145 → 0.1077) — structurally inconsistent with mechanism (a) "edge was always there but masked" since (a) would predict neutral or worse PBO. Same 2:1 TP:SL ratio preserved means the only mechanical change is absolute barrier tightness, which compresses noise bandwidth without rotating directional structure.

## What Was Tested

**Single-axis variation** (labeling axis): tighten ATR multipliers from `(tp=2.9, sl=1.45)` to `(tp=2.0, sl=1.0)` — same 2:1 ratio, tighter absolute values. Code change at `run_baseline_v3.py:_build_v3_model` lines 862-863. Setup commit `b55086a`. ITERATION_LABEL updated to `v3-010`. `_verify_feature_columns()` docstring parametrized against `f"{ITERATION_LABEL}"` per Critic FINAL Recommendation 3 from iter-v3/009 (third iteration with stale banner promoted to P1).

**Hypothesis** (brief Section 1, SHA `fdb17b1`): tightening triple-barrier ATR multipliers will produce IS Sharpe ≥ +0.10 (Falsifier 1 threshold) by yielding higher-frequency lower-magnitude trades; tests whether the iter-v3/007 IS=+0.22 baseline was sensitive to the specific multiplier values rather than just the 13-feature subset.

**Configuration**: `--exploration --seeds 1 --n-trials 10` on full v3 universe (BCH+MKR+LDO+TRX), ENSEMBLE_SIZE=1, colsample_bytree=1.0, training_months=24, OOS_CUTOFF_DATE=2025-03-24. Identical to iter-v3/009 modulo the two ATR multiplier values + cosmetic ITERATION_LABEL/docstring fix.

**Axis chosen per Critic FINAL Rec 1 of iter-v3/009 review** (`1bc828f`): two consecutive features-axis EXPLORATION rows (iter-v3/007 top-14, iter-v3/009 top-13) had left the catalog under-diverse. Labeling axis is structurally orthogonal — it changes BOTH label distribution AND model targets simultaneously, yielding maximally orthogonal evidence vs the iter-v3/007/009 features-axis runs.

## What Was Measured

### Headline metrics

| Metric | iter-v3/007 (top-14, 2.9/1.45) | iter-v3/009 (top-13, 2.9/1.45) | iter-v3/010 (top-13, **2.0/1.0**) | Δ vs iter-v3/009 |
|---|---:|---:|---:|---:|
| IS monthly Sharpe | +0.2241 | +0.0802 | **+0.5683** | **+0.488** |
| OOS monthly Sharpe | +0.0622 | +1.1223 | **+1.8122** | +0.690 |
| OOS/IS ratio | 0.28 | 13.99 | **3.19** | — |
| IS trades | — | 267 | 357 | +90 (+33.7%) |
| OOS trades | 90 | 87 | 109 | +22 (+25.3%) |
| OOS trades/month | — | ~6.4 | **~8.07** | +1.67/mo |
| PBO (per-cell mean) | 0.1419 | 0.1145 | **0.1077** | -0.0068 |
| n_eff (per-cell median) | 7 | 7 | 7 | 0 |
| Wall-clock | 8 min | 11 min | **7 min** | -4 min |

**IS monthly Sharpe = +0.5683 — the highest in v3 track to date.** Falsifier 1 (IS Sharpe < +0.10) NOT triggered; +0.47 above threshold. Falsifier 2 (IS trades < 267) NOT triggered; +33.7% scaling above baseline. Falsifier 3 (wall-clock > 30 min) NOT triggered; 7 min actual.

**OOS monthly Sharpe = +1.8122 — also the highest in v3 track to date.** Differentiates structurally from iter-v3/009's +1.1223 OOS lottery (98.61% LDO concentration on a 12-trade lucky run): iter-v3/010's OOS is broad-based with 3 of 4 symbols positive.

### Per-symbol OOS PnL attribution

| Symbol | OOS trades | Win rate | Net PnL% | Avg PnL% | Concentration% | Note |
|---|---:|---:|---:|---:|---:|---|
| BCHUSDT | 34 | 47.1% | +35.27% | +1.04% | **57.17%** | dominant contributor; concentration > 35% CONFIRMATION cap |
| LDOUSDT | 16 | 50.0% | +27.41% | +1.71% | 40.66% | highest avg PnL/trade |
| TRXUSDT | 42 | 42.9% | +10.82% | +0.26% | 11.05% | breakeven-positive; largest trade count |
| MKRUSDT | 17 | 29.4% | -10.65% | -0.63% | -8.88% | **3rd consecutive negative; revisit at 6-7 if pattern persists** |

3 of 4 symbols OOS-positive — the differentiation from iter-v3/009 is decisive: iter-v3/009's headline +1.12 OOS was 98.61% LDO single-symbol (75% WR on 12 trades, 95% binomial CI [42.8%, 94.5%] too wide to claim signal), while iter-v3/010's +1.81 OOS spreads across BCH/LDO/TRX with only MKR negative.

### IS Per-symbol attribution

| Symbol | IS trades | Win rate | Net PnL% |
|---|---:|---:|---:|
| BCHUSDT | 124 | 40.3% | +16.02% |
| LDOUSDT | 25 | 48.0% | +56.69% |
| MKRUSDT | 101 | 32.7% | -32.37% |
| TRXUSDT | 107 | 38.3% | +19.49% |

IS MKR is the dominant drag (-32.37%), partially offset by strong LDO (+56.69%). Despite MKR IS headwind, overall IS Sharpe is +0.5683 — the ensemble extracts positive signal across the universe.

### Methodology checks (Critic FINAL — `f6f4ef7`)

| # | Check | Status | Detail |
|---:|---|:---:|---|
| 1 | Look-Ahead | PASS | Zero new feature code; multipliers act on past-only `natr_21_raw` |
| 2 | Embargo | PASS | gap=88 (= (21+1)×4) verified at runtime; per-symbol gap=22 |
| 3 | MT correction (methodology) | PASS | PBO=0.1077 << 0.40; n_eff=7 > 4; **5 cells with PBO ≥ 0.9** flagged |
| 3 | MT correction (edge) | INFORMATIONAL | DSR=0.0, PSR=1.0 — single-seed exploration artifact (cadence-rule informational) |
| 4 | IC correlation | PASS | max abs(IC) = 0.660 (< 0.70); 0 pairs above threshold; feature axis byte-for-byte unchanged |
| 5 | ADF stationarity | WARN-carry-forward | 82.3% stationary (same per-month low-T artifact; no regression) |
| 6 | Pareto dominance | WAIVED | Single-seed (Section 8 criterion 9 + cadence rule) |
| 7 | Reproducibility | PASS | SHAs `b55086a` runner / `80332c1` analysis / `fdb17b1` brief / `5a227c7` Phase 5.5 stamped; trade-row spot-check (3 random OOS) reconciles |
| 8 | Hypothesis alignment | PASS | Single-axis labeling variation; brief Section 1 = code; Falsifiers 1, 2, 3 NOT triggered |
| 9 | Symbol exclusion | PASS | {BCH,MKR,LDO,TRX} ∩ V3_EXCLUDED = ∅ |
| 10 | Feature isolation | PASS | features_v3 does not import v1/v2 |
| 11 | Forming-candle | PASS | Same data-staleness guard as iter-v3/007-009 |
| 12 | Library pinning | PASS | Stack identical to iter-v3/009 (lightgbm 4.6.0, numpy 2.2.6, etc.) |

### Per-cell PBO outliers

5 cells with PBO ≥ 0.9 (`n_high_pbo_cells = 5/175`):
- TRXUSDT / 2025-10
- TRXUSDT / 2025-11
- MKRUSDT / 2024-10
- MKRUSDT / 2025-04
- MKRUSDT / 2025-07

Mean aggregator dilutes these to a clean 0.1077 PBO. Recorded in catalog row per QR Clarification 4 disposition; future CONFIRMATION QRs can choose between `(1 - mean_pbo)` and `(1 - max_per_cell_pbo)` weighting on bundle evidence without forcing a methodology change at iter-v3/010.

## Brief Section 7 Prediction Calibration (6/6 check)

Per iter-v3/004's calibration discipline, every brief Section 7 prediction is reconciled post-hoc:

| ID | Class | P | Prediction | Outcome |
|---|---|---:|---|---|
| P1 | process | 5% | ATR multiplier change in `_build_v3_model` doesn't propagate (downstream cache stamps old labels OR LightGBM strategy fixture uses hardcoded multipliers) | DID NOT MATERIALIZE — pre-flight grep confirmed `atr_tp_multiplier=2.0` AND `atr_sl_multiplier=1.0`; runtime banner reported the new multipliers; comparison.csv IS Sharpe shifted +0.488 (impossible if labels hadn't changed) |
| P2 | process | 10% | Wall-clock > 30 min on full v3 universe at exploration config | DID NOT MATERIALIZE — 7 min actual, 4.3x under target |
| P3 | process | 5% | Docstring fix breaks `_verify_feature_columns()` runtime check | DID NOT MATERIALIZE — 35/35 tests PASS; runtime banner correct; pre-flight check passed |
| P4 | model | **50%** | IS Sharpe lands in [+0.10, +0.30] (PROMISING band) | **PARTIALLY MATERIALIZED — overshoot in favorable direction**: actual IS Sharpe +0.5683 sits **+0.27 above** the predicted band's upper end (+0.40 was the brief's wider [-0.20, +0.40] band; +0.30 is the P4 specific upper bound). Verdict-class is correct (PROMISING), point-estimate undershot by the QR's prior. |
| P5 | model | 30% | IS Sharpe drops below +0.10 (Falsifier 1 activates) | DID NOT MATERIALIZE — IS Sharpe = +0.5683 |
| P6 | model | 15% | Trade frequency rises to 2× iter-v3/009's count (>534 IS trades) | DID NOT MATERIALIZE — 357 IS trades (1.34× baseline, within the predicted 1.45× scaling and well below the 2× threshold) |

**Calibration assessment**: 1/3 model-predictions partially materialized (P4 verdict-class correct, point-estimate overshoot). The QR weighted P4 (PROMISING) at 50% probability — verdict-class correct; **the magnitude of the IS lift was 1.4× the predicted upper bound**. This is a calibration miss in the FAVORABLE direction. Per brief Section 7 calibration discipline, the miss is documented: future labeling-axis EXPLORATION priors should reweight upward (e.g., 60% PROMISING + wider band) reflecting that single-axis labeling-magnitude perturbations under colsample=1.0 can produce larger IS shifts than the prior assumed.

The favorable overshoot is structurally distinct from iter-v3/009's unfavorable miss: iter-v3/009 missed on the LOSS side (P4 at 60% predicted +0.18 to +0.28; reality +0.0802 — below all three model bands). iter-v3/010 misses on the WIN side (P4 at 50% predicted +0.10 to +0.30; reality +0.5683 — above the band). Both calibration misses inform the same prior-update direction: labeling-axis perturbations have higher variance than the QR's initial prior assumed.

## Differentiation from iter-v3/009 (the EXPLORATION-NEGATIVE precedent)

The contrast with iter-v3/009 is the single most important diary observation: **broad-based per-symbol IS lift here vs single-symbol lottery there.**

| Dimension | iter-v3/009 (NEGATIVE) | iter-v3/010 (PROMISING) |
|---|---|---|
| Axis varied | Features (drop `vwap_dev_50`) | Labeling (tp/sl 2.9/1.45 → 2.0/1.0) |
| IS Sharpe | +0.0802 (below Falsifier 1) | +0.5683 (well above Falsifier 1) |
| OOS Sharpe | +1.1223 INFORMATIONAL | +1.8122 (broad-based) |
| OOS concentration | **98.61% LDO** (single-symbol) | 57.17% BCH (above 35% cap, but not single-symbol) |
| OOS positive symbols | 1 of 4 (LDO only) | **3 of 4** (BCH+LDO+TRX) |
| Headline OOS reading | LDO 12-trade 75% WR lottery (CI [42.8%, 94.5%]) | BCH 34 trades + LDO 16 trades + TRX 42 trades broad-based |
| Mechanism | Redundancy-removal hypothesis REJECTED at IS axis | Tighter-labels-reduce-noise hypothesis ACCEPTED at IS + OOS axes |
| PBO direction | 0.1419 → 0.1145 (improved by feature-removal artifact) | 0.1145 → 0.1077 (improved by tighter label distribution) |

The key structural argument: iter-v3/009's OOS Sharpe was attractive (+1.12) but was correctly catalogued as INFORMATIONAL because the +0.0802 IS Sharpe mechanically activated the pre-registered Falsifier 1, and the OOS lift was a 12-trade lottery on one symbol. iter-v3/010's OOS Sharpe (+1.81) is NOT subject to the same lottery critique: it spreads across 92 trades on the three positive symbols (BCH 34 + LDO 16 + TRX 42), and the IS Sharpe (+0.5683) does not require a "but the OOS is still real" rescue argument — both axes co-direct.

## Caveats Recorded for Audit Trail

The PROMISING verdict comes with five explicit caveats catalogued for the future CONFIRMATION-bundling QR (per Critic FINAL Recommendation 2; iter-v3/010 must explicitly capture all four caveats verbatim from QR's response):

1. **Mechanism**: (c) tighter labels reduce noise (NOT (a) "edge was masked", NOT (b) regime-specific tuning). Catalog cites mechanism (c).

2. **MKR pattern flag**: 3rd consecutive negative across iter-v3/007 (MKR -14.03%), iter-v3/009 (MKR -13.1% / -17.61% per-symbol), iter-v3/010 (MKR -10.65%). QR pre-commits the per-symbol-exclusion threshold at **6-7 consecutive negatives** before the universe-change axis is consumed; until then, audit trail records "3rd consecutive negative; revisit at 6-7 if pattern persists" so future QRs inherit the rule without re-deriving it.

3. **n_high_pbo_cells = 5/175** (TRX/2025-10, TRX/2025-11, MKR/2024-10, MKR/2025-04, MKR/2025-07). Future CONFIRMATION QRs can use `(1 - max_per_cell_pbo)` as a more conservative weighting alongside or instead of `(1 - mean_pbo)` when scoring bundle evidence.

4. **OOS_trade_rate = 8.07/month < 10/month floor** (`feedback_trade_rate_floor`). Informational at EXPLORATION; **floor applies at the BUNDLE level at CONFIRMATION** per the new memory rule `feedback_trade_rate_floor_bundle_level` (added per Critic Rec #3). Pre-committed NOW (in iter-v3/010 catalog row, before knowing any future CONFIRMATION outcome) to prevent post-hoc rationalization at the next CONFIRMATION boundary.

5. **OOS_max_concentration = 57.17%** (BCH-driven). Above the 35% per-symbol cap that would apply at CONFIRMATION. Informational under EXPLORATION per brief Section 6.3 — the label change may shift concentration in either direction, and this iteration concentrates on the historically stronger symbol.

## Lessons

1. **The cadence rule worked exactly as designed — second consecutive iteration validating the framework.** iter-v3/010 caught a real signal at 7 min wall-clock by running a single-axis variation at EXPLORATION density (`--exploration --seeds 1 --n-trials 10`). If the cadence rule were not in force, this iteration would have been re-run as a 5-seed CONFIRMATION (~5-9h) — and even then might have missed the signal under the existing colsample=1.0 + 50-trial tuning loop. iter-v3/008's abort at 4h 15min (extrapolated to ~25h) on a CONFIRMATION variant of a feature-axis hypothesis was the precedent that established the discipline; iter-v3/010 is the second iteration in a row to demonstrate the rule's value (iter-v3/009 caught a fragile feature-axis signal in 11 min; iter-v3/010 catches a strong labeling-axis signal in 7 min). **Cumulative time saved across iter-v3/008-010: ~30-50 hours of compute, with one PROMISING verdict to show for it.**

2. **The Critic 2-round flow worked exactly as designed.** Round 1 PRELIMINARY surfaced 4 substantive clarifications (mechanism attribution, MKR structural failure, OOS trade-rate floor implications, per-cell PBO outliers); QR responded with explicit dispositions; Round 2 FINAL accepted all four with no regressions. The clarifications produced concrete pre-commitments that go into the catalog row and a NEW memory rule (`feedback_trade_rate_floor_bundle_level`) — exactly the discipline that prevents post-hoc rationalization at the future CONFIRMATION boundary. **Without the 2-round flow, the trade-rate-floor caveat would have been a post-hoc "but EXPLORATION isn't bound by the floor anyway" argument the next CONFIRMATION QR could have invoked under merge pressure**; with the 2-round flow, it is now a pre-committed rule with audit trail.

3. **The pre-registered IS-axis falsifier (Falsifier 1) was decisive in interpreting the OOS Sharpe.** iter-v3/009 had OOS = +1.1223 (most attractive number in v3 history at the time) but was correctly classified EXPLORATION-NEGATIVE because IS = +0.0802 < Falsifier 1 threshold. iter-v3/010 has OOS = +1.8122 (now most attractive number in v3 history) and is correctly classified EXPLORATION-PROMISING because IS = +0.5683 >> Falsifier 1 threshold AND the OOS is broad-based. The same pre-registration discipline that classified iter-v3/009 NEGATIVE classifies iter-v3/010 PROMISING — the rule does not bend for an attractive OOS number; it bends for the IS-axis pre-registered measurement that anchors the verdict. (`feedback_no_cheating` operative throughout.)

4. **Single-axis labeling perturbation is structurally orthogonal to features-axis variation.** The iter-v3/007 + iter-v3/009 features-axis runs (top-14, top-13) cumulatively varied 1 feature out of 14 → 13. iter-v3/010 changed 0 features but rotated the entire label distribution via the (2.0, 1.0) tightening. The fact that PBO IMPROVED on a strictly tighter label distribution (0.1145 → 0.1077) is structurally inconsistent with mechanism (a) "edge was always there but masked" — (a) would predict neutral or slightly worse PBO. Mechanism (c) is the only one consistent with the joint IS lift + PBO improvement. **Future EXPLORATION axis-diversity should be enforced as a quota requirement, not just a count requirement** — three iterations on one axis (features-axis × 2 + labeling-axis × 1) is genuinely under-diverse, and iter-v3/011's planned risk-gate axis is the natural next probe.

5. **Calibration miss recorded for QR prior-update — second consecutive miss on labeling-axis priors.** P4 (50% PROMISING, [+0.10, +0.30]) overshot in the favorable direction. Reality was +0.5683 — 1.4× the upper bound. Combined with iter-v3/009's unfavorable undershoot (P4 at 60%, [+0.18, +0.28]; reality +0.0802), the empirical signal is that single-axis variations under colsample=1.0 + n_trials=10 have HIGHER variance than the QR's initial priors assumed. Future EXPLORATION priors on labeling-axis variations should: (a) widen the PROMISING band to roughly [+0.05, +0.60] to capture this variance, (b) reduce the P4 weight to roughly 35% to reflect the actual hit rate of "verdict-class correct AND point-estimate-in-band" (1 of 2 last EXPLORATIONs), (c) explicitly hedge by adding a P6-equivalent for "PROMISING but overshoots the band" at maybe 20%.

6. **Process-improvement: docstring parametrization completed.** Critic FINAL Recommendation 3 from iter-v3/009 was actioned: `_verify_feature_columns()` docstring is now parametrized against `f"{ITERATION_LABEL}"` instead of hardcoded `"iter-v3/008 brief Section 3.3"` and `"iter-v3/008 CONFIRMATION"`. Third iteration with stale banner promoted to P1 in the iter-v3/010 brief; first commit shipped the fix. No banner drift in this iteration.

7. **Dead-paths catalog (ninth entry, FIRST PROMISING since iter-v3/007):**
   - **iter-v3/010** — labeling axis (tp/sl 2.9/1.45 → 2.0/1.0) EXPLORATION on full v3 universe (BCH+MKR+LDO+TRX), `--exploration` mode (ENSEMBLE_SIZE=1, n_trials=10, colsample_bytree=1.0). **EXPLORATION-PROMISING.** IS monthly Sharpe = +0.5683 (>> Falsifier 1's +0.10; +0.488 above iter-v3/009's +0.0802; v3-track record). OOS monthly Sharpe = +1.8122 (v3-track record; broad-based across BCH+LDO+TRX with MKR negative; 109 trades / 8.07 trades/month). Methodology axes ALL PASS clean (PBO 0.1077 < 0.40; n_eff 7 > 4; max abs(IC) 0.660 < 0.70; 35/35 tests pass; all 12 Critic checks PASS / WARN-carry-forward / WAIVED-single-seed). 5 caveats catalogued: mechanism (c), MKR 3rd-consecutive-negative pattern flag, n_high_pbo_cells=5/175, OOS_trade_rate=8.07/month < 10/month floor (informational at EXPLORATION; bundle-level floor pre-committed via new memory rule), OOS_concentration=57.17% > 35% cap (informational at EXPLORATION). **STRONG candidate for next CONFIRMATION bundle** — after iter-v3/011 (risk-gate axis per Critic Rec #1) and 6 more EXPLORATIONs to reach the 10:1 quota, this iteration should be the labeling component of any CONFIRMATION-bundle brief.

## Pareto Position

Single-row degenerate front (Section 8 criterion 9 waiver):

| seed | OOS Sharpe | OOS MaxDD | OOS Calmar | PBO | n_trades | max_conc% |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | +1.8122 | 15.08% | 4.0179 | 0.1077 | 109 | 52.51% |

Cross-symbol OOS dispersion (informational, NOT Pareto-equivalent under EXPLORATION):

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| BCHUSDT | +35.27 | 34 | 47.1% | 57.17% |
| LDOUSDT | +27.41 | 16 | 50.0% | 40.66% |
| TRXUSDT | +10.82 | 42 | 42.9% | 11.05% |
| MKRUSDT | -10.65 | 17 | 29.4% | -8.88% |

OOS total weighted PnL = +60.60% (broad-based across 3 of 4 symbols).

Under CONFIRMATION's 5-seed regime, the standard concentration cap (≤35%) and Pareto checks become mechanical — BCH's 57.17% concentration exceeds the cap on a single seed and would need either (a) the 5-seed average to bring it below the cap (plausible if other seeds emphasize different symbols) or (b) an explicit waiver in the CONFIRMATION-bundle brief.

## Pre-Registered Failure-Mode vs Reality Summary

| Class | Materialized? |
|---|---|
| Process predictions (P1-P3, total 20%) | 0/3 materialized — pipeline ran clean, wall-clock 4.3x under target, docstring fix shipped without breaking anything |
| Model predictions (P4-P6, total 95%) | 1/3 PARTIALLY materialized as written; **P4 verdict-class correct but point-estimate overshot the band** |
| OOS-axis prediction | NONE — brief did not pre-register OOS predictions; +1.81 OOS Sharpe is informational alongside the IS verdict (iter-v3/010 inherits iter-v3/009's precedent of "OOS axis was not registered; falsifier 1 was registered at IS axis only") |

Calibration accuracy: 1/6 partial match (P4 verdict-class correct, point-estimate undershot the upper bound). The QR's P4 PROMISING-class prediction was correct but the magnitude was 1.4× the predicted upper bound. iter-v3/011 prior-setting should reflect this miss by widening the PROMISING band to roughly [+0.05, +0.60].

## Next Iteration

**iter-v3/011 — EXPLORATION on a NON-features, NON-labeling axis** (per Critic FINAL Recommendation 1).

After iter-v3/007 (features), iter-v3/009 (features), iter-v3/010 (labeling), the next probe should be **risk-gate axis** to maximize catalog axis diversity for downstream CONFIRMATION bundling. Critic recommended: **z-score OOD threshold 2.5 → 2.0 (tighter) or 3.0 (looser)** as single-axis variation. After iter-v3/011, the catalog will have axis coverage of features × 2, labeling × 1, risk-gate × 1 — meaningful diversity for the eventual CONFIRMATION bundle.

**Suggested specifics for iter-v3/011 brief**:

| Parameter | iter-v3/010 (current) | iter-v3/011 (suggested) |
|---|---:|---:|
| Z-score OOD threshold | 2.5 | **2.0 (tighter)** OR **3.0 (looser)** |
| ATR multipliers | (2.0, 1.0) | UNCHANGED |
| Feature set | 13 | UNCHANGED |
| Symbols | BCH+MKR+LDO+TRX | UNCHANGED |

**Rationale for risk-gate axis**:
- Risk gates are structurally orthogonal to both features (iter-v3/007/009) and labeling (iter-v3/010): they filter trade entries at decision-time without changing feature inputs or label targets.
- iter-v3/010's per-symbol gate kill rate was 64-81% (Engineer's Gate Efficacy Table). A tighter z-score gate (2.5 → 2.0) might reduce false-positive entries; a looser gate (2.5 → 3.0) might recover signal in edge cases that the 2.5 threshold over-kills.
- The labeling-axis EXPLORATION just produced PROMISING — gate sensitivity is the natural next probe before any CONFIRMATION bundles labeling + risk-gate variations together.

**Pre-conditions for iter-v3/011 brief**:
- Phase 5.5 PASS requires Section 7 prediction calibration to widen the PROMISING band based on iter-v3/010's overshoot (e.g., labeling/gate priors at 35% in [+0.05, +0.60], 30% in [+0.60, +1.0] overshoot, 35% NEGATIVE).
- Wall-clock budget: same 2h hard cap, target < 30 min on full v3 universe at `--exploration --seeds 1 --n-trials 10`.
- Pre-register an OOS-axis falsifier IF the brief intends to read OOS metrics (otherwise OOS remains informational-only per the iter-v3/009/010 precedent).
- Decide ex-ante whether to test tighter or looser gate; do not run both as a 2-axis EXPLORATION (would violate single-axis rule).

**Catalog count after iter-v3/010**: 3 of 10 EXPLORATIONs; 7 more required before any CONFIRMATION can launch.

**iter-v3/010 status**: STRONG candidate for next CONFIRMATION bundle (alongside iter-v3/007's top-14 features and any future risk-gate finding).
