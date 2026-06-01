# iter-v1/010 — Phase 7 QR Evaluation Memo

**Date**: 2026-05-25
**QR**: claude-opus-4-7 (1M context) — quant-research-v1 mode
**Branch**: `iteration-v1/010` (HEAD `7abfbaf`)
**Axis**: R5 vol-target ceiling, uniform `vol_target_pct = 4.0%`, applied AFTER R2 in the vt_scale pipeline
**Mode**: EXPLORATION (single-seed=42, ENSEMBLE_SIZE=3, n_trials=35, ≤2h cap)

---

## 1. Final Verdict

**EXPLORATION-NEGATIVE** (subtype: `PROMISING-INERT-with-IS-basin-shift`).

Single-line rationale: the literal F1 reading (OOS Δ = -0.0283) places /010 inside the PROMISING-INERT band [-0.05, +0.05], BUT the F3 IS Δ = +0.4701 overshoots the brief Section 8 upper bound (+0.05) by 9.4× and is mechanically attributable to a single-symbol single-seed Optuna basin lottery on LTC (LTC alone moved from 6.42% → 119.84% of total IS PnL, with OOS roster overlap of just 17.1% confirming 75% of the trade-roster turnover is loss-surface re-routing rather than the gate's filtering action). The brief's Failure Mode 4 — pre-registered as the dominant downside risk — fired. The OOS literal-band-pass is a happy accident on a basin that did not generalize (LTC OOS Δ = +3.7pp from baseline, i.e., the basin found in IS produced essentially neutral OOS contribution while shifting 5/5 symbols away from their baseline rosters).

This iteration is **not** evidence that R5 vol-target proportional scaling adds OOS edge. It is evidence that, under v1 single-seed=42 EXPLORATION budget (35 trials × 3 inner seeds × 4 models × 43 monthly cells), any axis that multiplies into the position-sizing weight will reshape Optuna's loss surface enough to re-route the trade roster; whether the re-route improves OOS Sharpe is a coin flip of the basin lottery, not an effect of the gate's economic mechanism.

---

## 2. Verdict-Class Rationale

The brief's Section 8 verdict gates are **sign-asymmetric** on F3 (Critic Rec #1, formally registered below). They pre-register:

- `IS Δ < -0.10` → NEGATIVE-catastrophic-IS
- `IS Δ ∈ [-0.10, +0.05]` → PROMISING-INERT
- `IS Δ ≥ +0.05 AND OOS Δ ≥ +0.05` → PROMISING

There is **no pre-registered class** for `IS Δ > +0.05 AND OOS Δ ∈ [-0.05, +0.05]` — i.e., the case where IS overshoots its band but OOS lands inside the inert region. This is exactly the regime /010 occupies. Two competing reads exist:

| Read | Anchor | Verdict |
|---|---|---|
| Literal F1 reading | OOS Δ ∈ [-0.05, +0.05] | PROMISING-INERT |
| Mechanism reading | IS Δ overshoots; Check 6 substantive FAIL on LTC 119.84% | EXPLORATION-NEGATIVE |

Per Critic discipline ("when in doubt, FAIL"), the mechanism reading binds: the IS overshoot is structurally informative — it reveals that the gate's design (proportional scaling on position size) reshapes the loss surface enough at single-seed=42 to trigger a Failure Mode 4 basin shift. The fact that the basin shift improved IS rather than collapsing it does not make the mechanism less of a failure; it makes the lottery's payoff happen to be positive on this particular seed-draw, on this particular symbol, in this particular OOS extent. A repeat at a different seed would produce a different outcome — that is exactly what `feedback_v3_single_seed_frozen_baseline.md` documents.

The subtype `PROMISING-INERT-with-IS-basin-shift` honestly records: the OOS evidence is INERT-band-grade (no durable Sharpe lift) AND the IS evidence is a known capacity-fit-noise artifact that does not generalize. Future risk-primitive iterations that touch the position-sizing weight at single-seed should assume their IS reading is unreliable until multi-seed CONFIRMATION validates.

---

## 3. Per-Symbol IS / OOS PnL Table

From `reports-v1/iteration_v1-010/in_sample/per_symbol.csv` and `out_of_sample/per_symbol.csv` (5 symbols, IS+OOS):

### 3.1 IS (in-sample, before 2025-03-24)

| Symbol | Trades | WR | Net PnL % | Avg PnL % | pct_of_total_pnl | Baseline IS net_pnl_pct | Δ vs baseline |
|---|---|---|---|---|---|---|---|
| LTCUSDT | 110 | 47.3% | **+79.98** | +0.7271 | **+119.84%** | +3.27 | **+76.71** |
| LINKUSDT | 152 | 42.1% | +32.33 | +0.2127 | +48.44% | +72.06 | -39.73 |
| DOTUSDT | 124 | 44.4% | +17.99 | +0.1450 | +26.95% | +26.62 | -8.63 |
| ETHUSDT | 145 | 34.5% | -19.40 | -0.1338 | -29.06% | -13.70 | -5.70 |
| BTCUSDT | 132 | 36.4% | -44.16 | -0.3345 | -66.16% | -37.28 | -6.88 |
| **Portfolio** | **663** | **40.6%** | **+66.74** | **+0.1007** | — | **+50.97** | **+15.77** |

**Diagnostic**: LTC alone delivered +76.71pp of the +15.77pp portfolio improvement (4.9× the net portfolio gain — i.e., LTC overshot, and 4 of 5 symbols offset some of that overshoot back toward neutral). The non-LTC symbols collectively moved -60.94pp (net negative). This is not a "broad-based lift" pattern; it is a single-symbol IS lottery confirmed against the oracle EDA's per-symbol predictions in brief Section 2.4:

| Symbol | Oracle predicted IS Δ | Observed IS Δ | Direction |
|---|---|---|---|
| BTC | -1.66 | -6.88 | matched (more negative) |
| ETH | +7.10 | -5.70 | **INVERTED** |
| LINK | -28.62 | -39.73 | matched (more negative) |
| LTC | -12.28 | **+76.71** | **INVERTED + 6.2× magnitude** |
| DOT | -0.21 | -8.63 | matched (more negative) |

The oracle (R5 applied on the frozen baseline trade roster) predicted -35.67pp IS Δ; the observed delta is +15.77pp — a **+51.4pp swing from the oracle**, 100% attributable to LTC re-routing into a new prediction basin (WR 39.5% → 47.3%, trades 124 → 110, avg PnL 0.026% → 0.727% — 28× per-trade PnL multiplication).

### 3.2 OOS (out-of-sample, ≥ 2025-03-24)

| Symbol | Trades | WR | Net PnL % | Avg PnL % | pct_of_total_pnl | Baseline OOS net_pnl_pct | Δ vs baseline |
|---|---|---|---|---|---|---|---|
| LINKUSDT | 48 | 54.2% | +80.92 | +1.6858 | +80.88% | +34.23 | +46.69 |
| BTCUSDT | 38 | 44.7% | +44.88 | +1.1811 | +44.86% | +33.17 | +11.71 |
| DOTUSDT | 48 | 45.8% | +29.13 | +0.6069 | +29.12% | +1.96 | +27.17 |
| ETHUSDT | 39 | 38.5% | -11.36 | -0.2912 | -11.35% | +2.75 | -14.11 |
| LTCUSDT | 37 | 37.8% | **-43.52** | -1.1763 | **-43.50%** | -47.25 | +3.73 |
| **Portfolio** | **210** | **44.8%** | **+100.05** | **+0.4764** | — | **+24.87** | **+75.18** |

**Diagnostic**: the OOS picture is dramatically different from IS — LINK, BTC, and DOT all improve substantially (+46.69, +11.71, +27.17 respectively), while LTC essentially neutralizes (+3.73) and ETH degrades (-14.11). The total OOS net_pnl_pct lifts from baseline +24.87% to /010's +100.05% (+75.18pp). **Yet OOS monthly Sharpe is -0.0283 below baseline**. This apparent contradiction (more PnL, lower Sharpe) is explained by the OOS extent and trade-count expansion: baseline OOS = 189 trades, /010 OOS = 210 trades (+21 trades, +11.1% expansion); the monthly Sharpe denominator (volatility of monthly returns) widened more than the numerator (mean monthly return) — a classic "more activity, same-or-worse risk-adjusted return" pattern.

### 3.3 Per-symbol Δ summary

| Symbol | IS Δ | OOS Δ | Verdict per symbol |
|---|---|---|---|
| LTC | **+76.71** | +3.73 | IS basin lottery; OOS neutral — Failure Mode 4 fired |
| LINK | -39.73 | +46.69 | symmetric variance-flip, IS-OOS divergence |
| DOT | -8.63 | +27.17 | symmetric variance-flip, IS-OOS divergence |
| BTC | -6.88 | +11.71 | mild symmetric variance-flip |
| ETH | -5.70 | -14.11 | uniformly degraded |

**4 of 5 symbols** show IS-OOS sign-flip patterns (LTC, LINK, DOT, BTC — all flip directions between IS and OOS). This is the textbook signature of a single-seed basin lottery: the basin Optuna found at single-seed=42 over-fit IS structure that did not transfer to OOS, and individual symbols re-distributed their trade-quality assignments along orthogonal directions to the R5 mechanism. The R5 gate's economic intent (cap exposure at high-NATR entries) did NOT drive this outcome; the gate's perturbation of the loss surface did.

---

## 4. Why the R5 Proportional-Scaling Family is CLOSED at v1 Single-Seed

`feedback_v3_concentration_is_signal.md` documented at v3/020 closeout that per-symbol PnL-share caps under proportional scaling produced OOS Δ = -0.72 vs anchor (3-symbol BCH+LDO+TRX universe) and the v3 catalog axiom emerged: **proportional scaling on position size is consistently INERT-to-NEGATIVE on OOS at single-seed EXPLORATION**. The /010 result is the v1 5-symbol-universe replication of that finding:

| Universe | Catalog row | OOS Δ vs anchor | Verdict | Family closure |
|---|---|---|---|---|
| v3 BCH/LDO/TRX (3 symbols) | iter-v3/020 | -0.72 | EXPLORATION-NEGATIVE | proportional-scaling CLOSED for v3 single-seed |
| v1 BTC/ETH/LINK/LTC/DOT (5 symbols) | iter-v1/010 | -0.0283 (IS basin-shift contaminated) | EXPLORATION-NEGATIVE | proportional-scaling CLOSED for v1 single-seed |

The v1 5-symbol generalization is **weaker in magnitude** (-0.0283 vs -0.72) but **directionally identical** (proportional scaling adds no durable OOS edge), AND comes with the additional v1-specific finding that the loss-surface perturbation triggers a basin lottery (the IS overshoot is the v1-specific evidence; v3/020 at 3-symbol universe showed comparable mechanism without the basin shift confounder because the 3-symbol universe has narrower loss-surface modes).

**Catalog axiom (extending v3/020 to v1)**: proportional scaling on position-sizing weight (R5 vol-target, per-symbol PnL caps, drawdown-proportional brakes) is **INERT-or-NEGATIVE at single-seed EXPLORATION** across both v1 5-symbol and v3 3-symbol universes. The family is **CLOSED at single-seed EXPLORATION budget**; reopenable only at multi-seed CONFIRMATION (≥10 seeds + ENSEMBLE_SIZE=10) which would dissolve the basin lottery and reveal whether residual edge exists. Per HIGH-RISK pre-commit Section 2.5 of /010's brief, the PROMISING gate was not satisfied, so the tripwire correctly did NOT fire — no multi-seed re-test is committed.

**The orthogonal sister primitive — binary kill switches (state-discontinuous, not smoothly attenuating)** — remains UNUSED at v1 and is the LM Master Phase 7.4 + Critic Phase 7.5 convergent recommendation for /011.

---

## 5. Why the IS Basin Shift is Genuine Information (Not Noise)

This iteration would be uninformative if its result were "R5 mechanically fires, oracle EDA's frozen-roster prediction holds within ±10%, Optuna trade roster ~85% overlapping baseline." Instead, the actual result delivered three load-bearing pieces of evidence:

1. **The LM Master Phase 4.5 prediction of "basin shift unlikely (~10-15%) at single-seed budget" was directionally wrong by 3-4×.** LM Master Phase 7.4 explicitly admits the calibration miss and proposes a new rule (basin-shift probability HIGH at 40-60% when the axis multiplies the loss directly). This is a calibration update to the entire LM Master Phase 4.5 framework, applying to all future risk-primitive briefs.

2. **OOS roster overlap with baseline = 17.1% under a STATELESS gate firing on only 18.6% of OOS signals.** The arithmetic does not work for a "mechanical filter" interpretation: a stateless gate firing on 18.6% of signals should produce 81.4% baseline-roster-identical trades (R5 didn't fire) plus a re-routing of the 18.6% subset. Observed 17.1% baseline overlap means 75% of the OOS roster is NEW trades — Optuna found a different basin entirely. This decisively confirms that proportional-scaling primitives at single-seed are not "filter-only" interventions; they are "loss-surface-reshaping" interventions whose mechanical effect dominates over their economic intent.

3. **The LTC IS basin (WR 39.5% → 47.3%, avg PnL 28× higher) did not transfer to OOS (LTC OOS WR remains 37.8%, OOS net_pnl -43.52 vs baseline -47.25).** A genuine LTC edge discovery would have transferred at least partially to OOS. The +3.73pp OOS lift on LTC is rounding-noise versus the +76.71pp IS lift — a 4.9% transfer rate. This is the textbook capacity-fit-noise signature.

**Confirmation of LM Master Phase 7.4 calibration rule**: future Phase 4.5 advisories must default to LOW directional confidence on Optuna basin-shift events whenever (a) the runner config differs materially from the anchor's (here: /010 = 3-seed × n_trials=35 = 105 fits/cell vs baseline 5-seed × n_trials=50 = 250 fits/cell), OR (b) the axis touches the position-sizing weight. This rule is now load-bearing for /011 and all future risk-primitive briefs.

The information value of /010 is structurally distinct from a NEGATIVE-NEGATIVE compound or a NEGATIVE-catastrophic verdict: those verdicts say "the axis is broken." /010 says "the axis didn't break, but it didn't add edge either; the evaluation methodology at single-seed cannot distinguish capacity-fit-noise from genuine edge for position-sizing-weight axes." This finding sharpens the v1 EXPLORATION methodology for the next 5 risk-primitive iterations.

---

## 6. F1-F5 Verdict Matrix

Per brief Section 4 falsifier specification:

| Falsifier | Condition | Observed | Verdict | Verdict-binding? |
|---|---|---|---|---|
| **F1** (PRIMARY) | OOS Sharpe Δ ≥ -0.05 → PASS | **-0.0283** (within [-0.05, +0.05] band) | **PASS** | YES (literal) |
| **F1-catastrophic** | OOS Sharpe Δ < -0.20 → NEGATIVE-catastrophic | -0.0283 (4× above threshold) | PASS | YES |
| **F2** (BEHAVIORAL) | OOS portfolio fire rate ∈ [10%, 60%] → PASS | **18.57%** (mid-band) | **PASS** | YES |
| **F2-too-tight** | OOS fire rate > 80% → NEGATIVE-mis-calibrated | 18.57% | PASS | YES |
| **F2-too-loose** | OOS fire rate < 5% → PROMISING-INERT | 18.57% | PASS | YES |
| **F3** | IS Sharpe Δ ≥ -0.10 → PASS | **+0.4701** (overshoots +0.05 upper by 9.4×) | **AMBIGUOUS** — passes literal lower bound but no upper-bound class exists | YES (verdict-binding via Critic Rec #1 escalation; see Section 7) |
| **F4** (DEGENERATE_PREDICTOR) | 0 degenerate trades → PASS | **0 IS / 0 OOS** | **PASS** | YES |
| **F5** (DSR computable) | `n_eff_per_cell_median ≥ 4` AND `dsr_is_finite=True` AND no math-undef | n_eff_per_cell_median = **13** (well above 4); DSR = 0.0 (finite floor); PSR_monthly_vs_0 IS=0.876 / OOS=0.760; PSR_monthly_vs_1 IS=0.287 / OOS=0.353 | **PASS** | YES |
| **Trade-rate floor** | ≥10 OOS/month AND ≥130 OOS total | OOS = 210 trades; 210 / 13 months = 16.2/month | **PASS** | YES |

**Pre-registered verdict gates** (brief Section 8):
- PROMISING (F1 ≥ +0.05 AND F3 ≥ -0.05 AND F2/F4/F5 PASS): **NOT MET** (F1 = -0.0283 < +0.05)
- PROMISING-INERT (F1 ∈ [-0.05, +0.05] AND F3 ∈ [-0.10, +0.05] AND F2/F4/F5 PASS): **NOT MET** (F3 = +0.4701 > +0.05)
- NEGATIVE (F1 < -0.05 OR F3 < -0.10): **NOT MET**
- NEGATIVE-mis-calibrated (F2 OOS fire rate < 5% OR > 80%): **NOT MET**

**Verdict-gap result**: /010 falls into the unregistered region `IS Δ > +0.05 AND OOS Δ ∈ [-0.05, +0.05]`. The verdict is determined by Critic's discipline (mechanism reading binds) and Section 7 escalation below.

---

## 7. Discussion — Sign-Asymmetric Verdict Gates (Critic Rec #1)

Critic Recommendation #1 from Phase 7.5 (`briefs-v1/iteration_v1-010/review.md` §Recommendations to QR line 150):

> **Pre-register `IS Δ > +X` verdict class in brief Section 8.** /010's brief Section 8 verdict gates are sign-asymmetric — they pre-register IS Δ < -0.10 (catastrophic) and IS Δ ∈ [-0.10, +0.05] (PROMISING-INERT) but NOT IS Δ > +0.05 as a separate class. When the basin-shift goes the IS-positive direction at single-seed, the verdict has no clean home. Future risk-primitive briefs at HIGH-RISK declaration should pre-register a fourth class: "PROMISING-INERT-with-IS-overshoot" requiring multi-seed CONFIRMATION to distinguish capacity-fit-noise from genuine edge, with explicit threshold (e.g., IS Δ ∈ (+0.05, +0.30] = OVERSHOOT-FLAG, IS Δ > +0.30 = catastrophic-basin-shift). The /010 brief's Failure Mode 4 anticipated the mechanism but didn't carry it through to Section 8 verdict gates.

### 7.1 The structural defect

Brief Section 8 implicitly assumes that:
1. A negative IS deviation is the only catastrophic IS outcome (NEGATIVE-catastrophic-IS at `IS Δ < -0.10`).
2. A small IS deviation in either direction is acceptable (PROMISING-INERT at `IS Δ ∈ [-0.10, +0.05]`).
3. A positive IS deviation paired with a positive OOS deviation is the only PROMISING outcome (PROMISING at `IS Δ ≥ -0.05 AND OOS Δ ≥ +0.05`).

This taxonomy is missing a fourth case: **a large positive IS deviation paired with a neutral OOS deviation**, which is the canonical "single-seed basin lottery" signature for position-sizing-weight axes. The /010 brief's Failure Mode 4 explicitly anticipated this mechanism — `"Optuna re-optimization with scaled rewards finds new IS-overfit basin"` — but the Section 8 verdict gates did not encode a verdict-class for it.

### 7.2 Mechanism: why the IS-overshoot direction is informative

A standard "small drift" model of verdict-class boundaries assumes that IS and OOS deviations are approximately symmetric — if you draw 10 single-seed runs of the same config, the IS distribution and the OOS distribution should be centered near the oracle's prediction with bounded variance. Under this model, an IS Δ overshoot is just bad luck; it doesn't carry diagnostic weight.

The /010 evidence falsifies this model for position-sizing-weight axes:
- LTC IS net_pnl shifted from +3.27 (baseline) to +79.98 (/010) — a 24× multiplicative change, far outside any reasonable "single-seed variance" interpretation.
- LTC OOS net_pnl shifted from -47.25 (baseline) to -43.52 (/010) — a 7.9% change, within normal seed variance.
- These two shifts are **asymmetric by 3 orders of magnitude in relative terms**. A purely symmetric noise model cannot produce this pattern; it requires the mechanism to be IS-fit-specific — i.e., basin-shift.

Therefore the IS overshoot is **structurally informative**: it is a measurement signature of the basin-shift mechanism itself. Future briefs must encode this signature as a separate verdict-class, not fold it into PROMISING-INERT.

### 7.3 Recommended verdict-class extension for future briefs

The next risk-primitive brief (whether /011 R5-binary-kill or a later iteration) should add to Section 8:

```
### PROMISING-INERT-with-IS-overshoot (basin-shift candidate)
- F1: OOS Sharpe Δ ∈ [-0.05, +0.05]  (literal INERT)
- F3: IS Sharpe Δ > +0.05  AND  IS Sharpe Δ ≤ +0.30  (overshoot in candidate band)
- F2/F4/F5/trade-rate-floor: PASS
- Per-symbol concentration check: at least one symbol with pct_of_total_pnl > 80%
- Verdict subtype: EXPLORATION-NEGATIVE (PROMISING-INERT-with-IS-basin-shift) — basin-shift confirmed; OOS-band-pass is happy accident; mechanism not durable
- Resolution path: NOT a multi-seed CONFIRMATION candidate; pivot to UNUSED family

### catastrophic-basin-shift
- F3: IS Sharpe Δ > +0.30
- Resolution: NEGATIVE-catastrophic-IS-overshoot; axis CLOSED at single-seed; multi-seed only if the brief explicitly designs to test mechanism stability
```

This codification turns Critic Rec #1 into a permanent structural improvement of the v1 EXPLORATION methodology.

### 7.4 What this means for /011 brief authoring (NOT this iteration's QR work)

The /011 QR will write a brief with extended Section 8 verdict gates that pre-register the OVERSHOOT-FLAG class above. The Phase 5.5 gate will enforce inclusion. This is process-level improvement, not iteration-level retest of R5.

---

## 8. Closing — What /010 Buys for v1

Despite the EXPLORATION-NEGATIVE verdict, /010 delivers four structural assets to v1:

1. **Catalog axiom (extending v3/020)**: proportional-scaling R5 family CLOSED at v1 single-seed; future risk-primitive iterations must use STATELESS BINARY KILL primitives (state-discontinuous) OR vol-target ceilings at multi-seed only.

2. **LM Master Phase 4.5 calibration update**: basin-shift probability raised from "unlikely (~10-15%)" to HIGH (40-60%) for position-sizing-weight axes at single-seed.

3. **Critic Rec #1 codified**: brief Section 8 verdict gates must be sign-symmetric on IS Δ; PROMISING-INERT-with-IS-overshoot and catastrophic-basin-shift classes added.

4. **R5 implementation infrastructure**: `risk_r5_vol_target_enabled / risk_r5_vol_target_pct` BacktestConfig fields + `r5_natr_lookup` init + IS/OOS-split fire counter all on `iteration-v1/010` branch and tested. STAYS ON BRANCH (NO src/ trunk merge per EXPLORATION-NEGATIVE rule), but the implementation is available for the next R5-axis attempt (e.g., R5-binary-kill at /011).

The iteration is closed; the next QR (/011) will work from Critic's Path Forward (PRIMARY = R5-BINARY-KILL — NATR > 7% binary kill switch), Option 2 (TRIPLE-BARRIER σ_t SOURCE — labeling), or Option 3 (PER-CELL EARLY-STOP — methodology). Catalog row for /010 advances; tag `v0.v1-010` placed.

---

## Appendix A — Reports Schema

`reports-v1/iteration_v1-010/` contents:

| File | Purpose | Status |
|---|---|---|
| `comparison.csv` | Headline IS/OOS metrics + R5 fire rate rows | Present; r5_fire_rate row column-labels invert (Critic Check 7 defect — not verdict-binding, fix at /011) |
| `in_sample/per_symbol.csv` | Per-symbol IS attribution | Present |
| `out_of_sample/per_symbol.csv` | Per-symbol OOS attribution | Present |
| `in_sample/dsr.json` | n_eff per-cell PCA stats | Present, n_eff_per_cell_median=13 (above 4 floor) |
| `out_of_sample/dsr.json` | n_eff per-cell PCA stats (OOS) | Present |
| `*/adf_test.csv` | Stationarity tests on V1_FEATURE_COLUMNS_PRUNED | Present, 40/40 pass or declared exception |
| `*/ic_matrix.csv` | 7-family pairwise Fisher-IC | Present (carry-over from /002 post-prune state; not /010-binding) |
| `*/monthly_pnl.csv` | Monthly PnL series | Present |
| `*/daily_pnl.csv` | Daily PnL series | Present |
| `*/trades.csv` | Per-trade roster (entry/exit/weight/pnl) | Present |
| `*/per_regime.csv` | Per-regime attribution | Present |
| `*/quantstats.html` | Quantstats tearsheet | Present |
| `r5_fire_log.csv` | Per-trade NATR / r5_cap / r5_fired bool | **MISSING** (brief Section 10.3 promise; Critic Check 7 advisory defect; aggregate stdout counters cover F2 evaluation) |
| `feature_importance.csv` | Per (model, symbol, month) gain importance | **MISSING** (Phase 7.4 LM Master post-mortem flagged instrumentation gap) |

The missing files are non-blocking for the verdict but should be wired into /011 if a future R5 revival is attempted.

---

## Appendix B — Critic Check Status Summary

From `briefs-v1/iteration_v1-010/review.md`:

| Check | Status | Verdict-binding? | Notes |
|---|---|---|---|
| 1 — Look-Ahead Audit | PASS | YES | walk_forward.py:113 fix intact; R5 NATR loaded past-only |
| 2 — Embargo Width | PASS | YES | REQUIRED_GAP=110 unchanged from /008 baseline |
| 3 — Multiple-Testing Correction | FAIL-informational | NO (at EXPLORATION) | DSR=0.0, PBO null, n_eff_per_cell_min=5 LTC |
| 4 — IC Correlation | PASS-vacuous | NO (no new features) | Carry-over from /002 post-prune; 3 cross-family > 0.70 |
| 5 — ADF Stationarity | PASS | YES | 40/40 raw-α stationary or declared exception |
| 6 — Pareto + Concentration | **FAIL-substantive** | **YES** | LTC IS pct_of_total_pnl = 119.84%; OOS roster overlap 17.1% |
| 7 — Reproducibility | PASS-with-defect | NO (defect not verdict-binding) | r5_fire_rate column-label inversion + r5_fire_log.csv missing |
| 8 — Hypothesis-Implementation Alignment | PASS | YES | F1/F2 oracle close; F3 oracle inverted (basin-shift mechanism) |
| 13 — Anti-Pattern Static Scan | PASS | YES | A1-A14 clean across src/ diff |
| 14 — Axis Family Validation | PASS | YES | risk-primitive first appearance; rotation VALID |

Verdict-binding fails: Check 6 substantive (LTC concentration) is the single most decisive evidence; combined with the F3 IS-overshoot which falls in the unregistered verdict-gap region, the EXPLORATION-NEGATIVE verdict is unambiguous.

---

End of Phase 7 evaluation memo. Phase 8 deliverables (diary + catalog entry) follow.
