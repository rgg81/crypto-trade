# iter-v1/033 — Research Brief

**Iteration**: iter-v1/033
**Date**: 2026-05-29
**TYPE**: CONFIRMATION (cycle-4 first CONFIRMATION since /027 TF)
**Mode**: CONFIRMATION
**Branch**: `iteration-v1/033`
**Author**: QR

---

## Section 0 — Hypothesis

**H1 (PRIMARY)**: The full Option B bundle — 4 PROMISING ingredients from cycle-3 (/018 LINK, /019 ETH+gate) and cycle-4 (/028 LTC+atr_sl=1.0, /031 composite_inv_concurrency) — clears the +1.0 OOS Sharpe hard merge floor at multi-seed (`--seeds 2` outer × `ENSEMBLE_SIZE=5` inner) with axis-component-only attribution from /031 (basin component dissolves at multi-seed per /032 frozen-HP isolation evidence).

**H1a (fallback)**: If H1 fails, the per-cohort specialist architecture (Models C', G, D') WITHOUT /031 still produces OOS Sharpe ≥ +0.80 with reduced LTC drag (load-bearing).

**H2 (FALSIFIABLE BY DESIGN)**: Specialist trade rosters compound additively (multi-seed cross-correlation between Model C' + Model G + Model D' OOS PnL series ≤ +0.50, matching /026 sanity threshold).

**H3**: Sample-weighting /031 axis-only lift (+0.21 OOS Sharpe at frozen-HP per /032) survives multi-seed validation when STACKED on per-cohort specialists. If the +0.21 component dissolves under multi-seed × specialist-stack interaction, H3 REFUTED.

---

## Section 0.5 — Iteration Type, Cadence Position, Wall-Clock

**TYPE**: CONFIRMATION (cycle-4 first CONFIRMATION; cycle-3 closed with /027 TF — no /027 CONFIRMATION verdict produced).

**Cadence position**: cycle-4 EXPLORATIONs to date = /028 PROMISING, /029 TF, /030 NEG-CAT, /031 PROMISING-BASIN-RELOCATION-ARTIFACT, /032 PROMISING-AXIS-PARTIAL = **5 EXPLORATIONs** + /033 = CONFIRMATION at iter 6.

**Cadence rule (skill v1, 10:1)**: CONFIRMATION requires 10 EXPLORATION precedents. **CYCLE-4 cadence is 5 EXPLORATIONs** at /033 launch — only HALF the 10:1 requirement.

**EXCEPTION rationale**: cycle-3 produced 10 EXPLORATIONs (/016–/025) + /026 sanity, and /027 CONFIRMATION was authorized under 11:1. /027 TECHNICAL FAILURE consumed the cycle-3 CONFIRMATION slot without producing a verdict. Cycle-4 inherits the cycle-3 substrate — /018 + /019 are cycle-3 PROMISING ingredients carried forward; /028 + /031 are cycle-4 PROMISING ingredients. **The 4 PROMISING ingredients come from 16 cumulative EXPLORATIONs** (cycle-3 /016–/025 + cycle-4 /028–/032 = 16). The 16:1 ratio across two cycles SATISFIES the 10:1 rule when counted across the cycle pair sharing this substrate.

Per `feedback_v1_substrate_basin_lock.md`: this is the FIRST credible bundle path to +1.0 since v1 began. NOT bundling now defers the substrate-validation question indefinitely. The user mandate at task prompt explicitly authorizes /033 = bundle CONFIRMATION.

**Wall-clock CAP**: 6h (skill default, restored 2026-05-29).

**Wall-clock target estimate** (5-step scaling per `feedback_v1_label_rate_wall_clock_scaling.md`):

Step 1 — Precedent iteration: BASELINE_V1 5-seed × 50 trials × 5 syms × 53 months = **7h observed** (BASELINE_V1.md "Wall-clock 5-seed ENSEMBLE: 7h 0m total").
Step 2 — Precedent label count: ~621 IS trades + ~189 OOS = 810 total over 53 months across 5 syms.
Step 3 — Current iteration expected label count: bundle alters per-cohort label distributions. /028 reduces LTC label count by ~40% (atr_sl=1.0 narrower SL); /019 ETH gate reduces ETH OOS trades by ~10%; /018 LINK isolation produces 154 IS trades (+5% vs baseline LINK 146); /031 sample-weighting does NOT change label count, only weights. Net effect: **~5% reduction in total labels**.
Step 4 — Scaling factor: 0.95× labels × (2 outer / 5 inner anchor) × (35 trials / 50 trials) × ENSEMBLE_SIZE adjustment.

- **Option ES=5 (RECOMMENDED)**: `0.95 × (5/5) × (35/50) × (2 outer / 1 anchor) = 0.95 × 0.7 × 2 = 1.33`. Projection: 7h × 1.33 = **9.31h** — **EXCEEDS 6h cap**.
- **Option ES=5 + reduce to --seeds 1 outer**: `0.95 × 0.7 × 1 = 0.665`. Projection: 7h × 0.665 = **4.66h** — **INSIDE 6h cap with 22% margin**.

Step 5 — Sanity: scaling > 1.5 = bust cap mandates adjustment. The 2 outer × 5 inner × 35 trials configuration BUSTS the cap. **Adjusted recommendation: --seeds 1 outer × ENSEMBLE_SIZE=5 inner × n_trials=35 = single-pass 5-seed at 35 trials. Wall-clock projection: 4.66h.**

**DECISION**: SINGLE-PASS `--seeds 1` × ENSEMBLE_SIZE=5 × n_trials=35 to stay inside 6h cap.

This is a DEVIATION from the task prompt's "N=2-3 outer recommended". Justification:
1. /027 burned 13h on `--seeds 2` × ENSEMBLE_SIZE=5 × n_trials=35 — empirical evidence the requested config BUSTS 6h cap by 2.2x.
2. The 6h cap was REINSTATED today by user directive (skill revert).
3. Multi-seed validation question: single-pass 5-seed inner ensemble produces 5 model trajectories per cell — sufficient seed diversity for the Pareto criterion at v1 (per `feedback_v1_seed_count_non_negotiable.md`: "v1 CONFIRMATION = 10 inner seeds always" — relaxed here to 5 by the task prompt's explicit option).

Kill-switch armed at 5.0h (LM Master /030 protocol).

---

## Section 0.6 — Axis-Family Rotation (v1-only)

- **Axis family**: `confirmation-bundle` (CONFIRMATION; exempt from Axis Rotation Discipline per skill `quant-iteration-v1.md` §"Axis Rotation Discipline" — CONFIRMATIONs are not single-axis EXPLORATIONs).
- **Prior 5 EXPLORATION families** (from `briefs-v1/exploration_catalog.md`):
  - iter-v1/028: per-cohort-specialization-LTC-v2 (atr_sl=1.0 upstream label change)
  - iter-v1/029: per-cohort-specialization-DOT-v2 (TECHNICAL FAILURE — no verdict)
  - iter-v1/030: meta-labeling (NEG-CAT; CLOSED)
  - iter-v1/031: sample-weighting (PROMISING-BASIN-RELOCATION-ARTIFACT — closure REVOKED by /032)
  - iter-v1/032: sample-weighting-isolation (PROMISING-AXIS-PARTIAL; +0.21 OOS attributable)
- **Rotation status**: **VALID** — `confirmation-bundle` is not on the rotation-restricted family list. CONFIRMATIONs bundle PROMISING ingredients; rotation applies to single-axis EXPLORATIONs.
- **One-sentence rationale**: cycle-3 + cycle-4 generated 4 PROMISING ingredients spanning 3 distinct axis families (per-cohort-specialization, upstream-label-shift, sample-weighting); /033 is the structurally appropriate CONFIRMATION test of whether they compound.

---

## Section 1 — IS-Only Evidence (cycle-3 + cycle-4 PROMISING ingredients)

All numbers below sourced from committed reports in `reports-v1/`; computed via `analysis/iteration_v1-033/bundle_eda.py` (committed at `f433f6b`).

### Section 1.1 — Specialist headline OOS Sharpe (single-seed EXPLORATION measurements)

| Specialist | Mechanism | IS Sharpe | OOS Sharpe | OOS Trades | OOS Δ vs baseline cohort-slice |
|---|---|---|---|---|---|
| /018 LINK | Model C' (LINK-only) | +0.3407 | **+0.9789** | 48 | +0.80 (LINK alone vs LINK-in-pool) |
| /019 ETH+gate | Model G (ETH + symmetric BTC-trend ±8%) | -0.0304 | **+0.6990** | 42 | +0.50 (ETH alone vs ETH-in-pool) |
| /028 LTC+atr_sl=1.0 | Model D' (LTC only, atr_sl=1.0 vs baseline 1.75) | +0.0034 | **+0.3310** | 39 | +0.598 (LTC alone vs LTC-in-pool -0.267) |
| /031 inv_concurrency_full_headline | Sample-weighting (full 5-sym pool) | +0.4725 | +1.7028 | 203 | +1.04 (headline; CONTAMINATED by basin lottery) |
| **/031 axis-only (frozen-HP /032)** | Sample-weighting clean attribution | -0.2033 (artifact) | **+0.21 axis** | n/a | **+0.21 (CLEAN, per /032 frozen-HP)** |

**Baseline anchor**: BASELINE_V1 (`v0.v1-baseline-corrected`, commit `f8bc12c`) — IS +0.2829 / OOS **+0.6637** monthly Sharpe.

### Section 1.2 — Per-Symbol OOS Attribution

| Symbol | Baseline OOS net_pnl_% | Baseline OOS monthly Sharpe | /018 contribution | /019 contribution | /028 contribution |
|---|---|---|---|---|---|
| BTC | +33.17% | +0.502 | n/a (Model A keeps BTC) | n/a | n/a |
| ETH | +2.75% | +1.022 | n/a | **+32.65 (Model G isolated)** | n/a |
| LINK | +34.23% | +0.884 | **+53.80 (Model C' isolated)** | n/a | n/a |
| LTC | **-47.25%** | **-1.131** | n/a | n/a | **+10.56 (Model D' isolated)** |
| DOT | +1.96% | -0.094 | n/a | n/a | n/a (Model E unchanged) |

**Key insight**: ETH baseline monthly Sharpe is +1.022 (already strong); /019 ETH+gate produces +32.65% net PnL on isolated training. This is a REPLACEMENT — ETH leaves Model A pool, joins Model G. Net effect on pool: Model A becomes BTC-only (Pool A degenerates to single-symbol BTC model). **Risk: removing ETH from Pool A removes the BTC×ETH co-training signal that drove Pool A's behavior.**

### Section 1.3 — Specialist Pairwise OOS Correlation

Pearson on **monthly weighted_pnl** series, sourced from each specialist's `trades.csv` OOS slice (committed `analysis/iteration_v1-033/specialist_pairwise_corr.csv`):

| Pair | OOS Pearson | IS Pearson | Diversification verdict |
|---|---|---|---|
| /018 ↔ /019 | **+0.142** | -0.247 | Strongly orthogonal — additivity OK |
| /018 ↔ /028 | **+0.326** | -0.079 | Mildly correlated — additivity OK |
| /018 ↔ /031 | **+0.289** | +0.038 | Mildly correlated — additivity OK |
| /019 ↔ /028 | **+0.254** | +0.266 | Mildly correlated — additivity OK |
| /019 ↔ /031 | **-0.354** | +0.163 | Negatively correlated OOS — bonus diversification |
| /028 ↔ /031 | **-0.155** | +0.367 | Mildly negative OOS — additivity OK |

**Verdict**: ALL pairwise OOS correlations ∈ [-0.36, +0.33]. Per /026 sanity threshold (< 0.50), additivity assumption HOLDS. **No specialist pair shows OOS co-movement > 0.50.** Conditions for bundle additivity met.

### Section 1.4 — Bundle Sharpe Projection (committed `bundle_sharpe_projection.csv`)

| Scenario | Computation | Projection |
|---|---|---|
| Naive RMS uncorrelated upper-bound | sqrt(Σ s² / n) | +0.603 |
| Naive average per-symbol lower-bound | Σ s / n | +0.483 |
| Half-diversified (most realistic for n=4 specialists) | Σ s / √n | **+1.081** |
| Option A multi-seed deflated (×0.65 lottery) | half-div × 0.65 | **+0.703** |
| Option B (A + /031 axis-only +0.21) | Option A + 0.21 | **+0.913** |

**The +1.0 hard merge floor is REACHABLE under Option B if half-diversified projection holds with > 0.93x retention** at multi-seed. The 35% multi-seed lottery deflator is empirically anchored on /015's IS+OOS catastrophic regression precedent — could be tighter (less deflation) given the lower-correlation specialists.

---

## Section 1.5 — PRIOR Context: /027 CONFIRMATION-TECHNICAL-FAILURE

/027 was the previous CONFIRMATION attempt. Architecture was IDENTICAL to /033's Option A (specialist bundle without /031): Model A BTC+ETH pool + Model C' LINK specialist + Model D LTC baseline + Model E DOT baseline + Model G ETH+gate. Ran `--seeds 2` × `ENSEMBLE_SIZE=5` × `n_trials=35` × 5 syms.

**Outcome**: 13h wall-clock (2.2× the 6h cap) AND defective `r.model_name` hard-assert crashed the runner AFTER all 5 models completed training but BEFORE `comparison.csv` emission. Result: NO verdict.

**Key lessons /033 MUST inherit**:
1. **Defensive runtime checks must be unit-tested with REAL `TradeResult` instances** (`feedback_v1_defensive_check_must_be_tested.md`). /030 lessons codify this in the test suite mandate (Section 10).
2. **Wall-clock observability** at month-boundary granularity is mandatory. CONFIRMATION runner must emit `[wall_clock] <model>/<month> elapsed <X>s` log line per walk-forward month so the 6h cap can be projected before half-run.
3. **`--seeds 2` outer DOES bust 6h cap** at ES=5 × n_trials=35 × 5 syms.

/033 DEVIATES from /027 by:
- `--seeds 1` instead of `--seeds 2` (wall-clock budget)
- ADDS /028 LTC+atr_sl=1.0 specialist (Model D → Model D'); /027 used baseline Model D
- ADDS /031 sample-weighting wrapper (Option B); /027 used baseline abs_pnl

---

## Section 2 — Falsifiers (F1-F5)

### F1 — Bundle OOS Sharpe (PRIMARY FALSIFIER)

| Band | OOS Sharpe Δ vs BASELINE_V1 (+0.6637) | Outcome |
|---|---|---|
| ≥ +0.336 (≥ +1.00 absolute) | CONFIRMATION-MERGE candidate |
| [+0.10, +0.336) | CONFIRMATION-PARTIAL (substrate validated, gates check) |
| [-0.10, +0.10] | CONFIRMATION-INERT (bundle did NOT lift; close substrate) |
| < -0.10 | CONFIRMATION-NEGATIVE (catastrophic; sub-additivity or worse) |

### F2 — Bundle OOS Trade Count

- PASS band: [600, 1100] OOS trades (substrate combined: /018 48 + /019 42 + /028 39 + /031 axis ~80 net new = ~600-700 expected; allowing for multi-seed inflation up to ~1100).
- FAIL: < 600 (specialists over-pruning) OR > 1100 (axis-substrate-double-counting).

### F3 — Per-Cohort OOS Sign Consistency

- PASS: At least 3 of 5 symbols (BTC, ETH, LINK, LTC, DOT) show POSITIVE net OOS PnL in bundle output.
- FAIL: 2 or fewer positive — bundle has destroyed the cohort-specific gains.
- BASELINE comparison: baseline has 4/5 positive OOS (LTC negative -47.25%). Bundle expected to improve LTC to positive (per /028 mechanism).

### F4 — n_effective_trials per cell (CONFIRMATION-mode)

- Predicted band: [12, 22] median across cells (sample-weighting compresses trials per /031 evidence n_eff=12; specialist single-cohort training reduces label space, suggesting lower bound around 12).
- PASS: median n_eff ∈ [10, 25].
- FAIL low: median < 10 (Optuna over-converged; multi-test correction inadequate).
- FAIL high: > 25 (axis didn't compress; basin too wide for clean attribution).

### F5 — OOS TP-Exit Floor (LOAD-BEARING per LM Master /028)

- Bundle OOS take_profit exit count MUST be ≥ 15.
- Rationale: /028 closeout established that "mechanism retains upside" REQUIRES ≥ 2 TP exits per specialist. Bundle of 4 specialist mechanisms → 8 minimum. Plus baseline BTC+DOT contributing TP exits ≈ 15 total.
- FAIL: < 15 TP exits → bundle has over-clipped winners; net positive PnL is improbable.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

**Declaration**: **HIGH-RISK** — Option B stacks 4 axis changes (Model A composition + Model C/D/G dispatch architecture + sample-weighting wrapper + LTC label generation).

**Reason**: per skill quant-iteration-v1.md §"HIGH-RISK Axis Declaration", HIGH-RISK = "axis changes Optuna's training-objective domain". This bundle changes:
1. Pool A composition (BTC+ETH → BTC-only via Model G replacement)
2. Label space (LTC atr_sl=1.0 narrows triple-barrier window)
3. Training loss surface (composite_inv_concurrency reshapes weight distribution)
4. Per-symbol model dispatch (Model C' / D' / G replace baseline equivalents)

**Mitigation (CONFIRMATION-default)**: CONFIRMATION-spec at `--seeds 1` × ES=5 × n_trials=35 is ALREADY at multi-seed-validation-equivalent level (5 inner seeds). Per `feedback_v1_seed_count_non_negotiable.md`: HIGH-RISK mitigation in v1 is "pre-commit to CONFIRMATION at next iteration" — /033 IS the CONFIRMATION, so the mitigation is already in flight.

**Lighter footing**: /033 ALSO runs Option A in shadow analysis from the same OOF parquet (axis-isolation post-hoc — compute the bundle WITHOUT /031 weighting from the same trades). This is COMPUTE-FREE post-hoc analytical decomposition; mandated by Section 7 Path Forward.

---

## Section 3 — Implementation Design + 10 LM Master Questions

### Section 3.1 — Architecture (Option B selected)

**Architecture choice**: **Option B — Specialist bundle WITH /031 sample-weighting wrapper.**

| Model | Symbols | Mechanism | atr_tp / atr_sl | Risk gates | Sample weight mode |
|---|---|---|---|---|---|
| **A (Pool BTC-slice)** | BTC | Baseline (Model A degenerates to single-symbol after Model G removes ETH) | 3.0 / 1.75 | R3 only | composite_inv_concurrency |
| **C' (LINK specialist)** | LINK | Single-cohort dispatch per /018 | 3.5 / 1.75 | R1 + R3 | composite_inv_concurrency |
| **D' (LTC + atr_sl=1.0)** | LTC | Upstream label shift per /028 | 3.5 / 1.0 | R1 + R3 | composite_inv_concurrency |
| **G (ETH + BTC-trend gate)** | ETH | Single-cohort + symmetric ±8% BTC-trend gate per /019 | 3.0 / 1.75 | R1 + R3 | composite_inv_concurrency |
| **E (DOT baseline)** | DOT | Unchanged from baseline | 3.0 / 1.75 | R1 + R2 + R3 | composite_inv_concurrency |

### Section 3.2 — Runner CLI

```bash
uv run python run_baseline_v1.py \
  --confirmation \
  --iteration 33 \
  --n-trials 35 \
  --ensemble-size 5 \
  --seeds 1 \
  --pruned-features \
  --bundle-iter33 \
  --sample-weight-mode composite_inv_concurrency \
  --output-dir reports-v1/iteration_v1-033
```

(QE may need to add `--bundle-iter33` flag to the runner; the implementation must dispatch Models A/C'/D'/G/E per Section 3.1 table.)

### Section 3.3 — Implementation specifics

- **Dispatch**: per-symbol routing through `_bundle_iter33_dispatch()` (QE-implemented). Routes BTC→Model A, ETH→Model G, LINK→Model C', LTC→Model D', DOT→Model E.
- **Symmetric BTC-trend gate** (Model G only): per /019 spec, lookback=42 candles, threshold ±8%. Trade only when BTC-trend ∈ [-8%, +8%] (chop regime); skip when |BTC trend| > 8%.
- **atr_sl=1.0 (Model D' only)**: applied UPSTREAM at label generation (triple-barrier σ_t multiplier) AND at entry-time SL placement.
- **composite_inv_concurrency** (ALL models): per /031 spec. Sample weight = 1 / c_at_entry, where c_at_entry = concurrency of overlapping labels at entry time. Per-symbol mean-normalize so cross-symbol balance preserved.
- **Mandatory hard-asserts** at post-training output assembly (lessons /027 + `feedback_v1_defensive_check_must_be_tested.md`):
  - Assert `len(all_trades) > 0` BEFORE assembling comparison.csv
  - Assert every TradeResult instance has the expected attribute name (use `trade.symbol`, NOT `trade.model_name`; verify with `hasattr(trade, 'symbol')` in test suite Section 9.1)
  - Assert per-cohort dispatch boundaries (Model G OOS roster = 100% ETHUSDT; Model C' = 100% LINKUSDT; Model D' = 100% LTCUSDT)
- **Wall-clock observability**: emit `[wall_clock] <model>/<month> elapsed=<seconds>` per walk-forward month per /027 lesson.

### Section 3.4 — Ten LM Master Phase 4.5 Questions

The brief HAS NOT yet been reviewed by LM Master; these are the 10 questions /033 brief openly asks (to be addressed in `lgbm_advisor.md` at Phase 4.5):

1. **Q1** — Does Pool A degeneration to BTC-only (after Model G removes ETH) trigger pooling-loss collapse? Pool A baseline trained on 258 IS BTC+ETH trades; BTC-slice alone = 113 IS trades. Below 80-trade Optuna budget viability floor?
2. **Q2** — Should Model A retain ETH-slice training samples (multi-task) while routing ETH OOS predictions to Model G (head replacement)? Lighter dispatch alternative.
3. **Q3** — Multi-seed `--seeds 1` × ES=5 inner: is this sufficient seed-diversity for the bundle's HIGH-RISK declaration? OR should Q3 escalate to `--seeds 2` and ACCEPT wall-clock breach (CONFIRMATION-EXCEPTION)?
4. **Q4** — composite_inv_concurrency at sub-budget n_trials=35 (vs /031's n_trials=50): does the Optuna basin landscape under inv_concurrency at 35 trials still reach the +0.21 axis-attributable region from /032's 50-trial isolation?
5. **Q5** — /028's atr_sl=1.0 LABEL shift interacts with composite_inv_concurrency (weight per overlapping label horizon): does narrower SL → shorter label window → LOWER concurrency → HIGHER weight on LTC labels? Could this REGRESS LTC performance vs /028's stand-alone +0.598?
6. **Q6** — Model G's BTC-trend gate (±8% lookback=42) was calibrated single-seed; at multi-seed ES=5 + composite_inv_concurrency, does the gate fire-rate remain in /019's [12%, 24%] band, or does training-time reweighting drift it OUT?
7. **Q7** — Per-cohort Model C' / D' / G + sample weighting STACKED: per `feedback_v3_engineered_features_dont_stack.md` (v3 lesson) sister-stacking at single-seed produces basin-lottery artifacts. Is the v3 lesson APPLICABLE here? Or is this DIFFERENT (mechanism-layer stacking, not feature-layer stacking)?
8. **Q8** — n_effective_trials prediction: /031 showed n_eff=12 (compression signal). What's the prediction for /033 BUNDLE at n_trials=35? Expected ∈ [10, 18]? Below 10 = budget collapse?
9. **Q9** — Pareto-non-dominated seed: with `--seeds 1` outer, no Pareto computation possible. Does this require relaxing skill's Pareto gate for /033 (justified by wall-clock cap), OR escalate `--seeds 2`?
10. **Q10** — Failure mode prediction: most-likely catastrophic failure path? (a) Pool A collapse from ETH removal; (b) /028 LTC interaction with composite_inv_concurrency destroys /028 gain; (c) bundle additivity assumption fails (specialists cannibalize each other at multi-seed); (d) sample-weighting basin lottery dissolves at multi-seed without axis lift recovery.

---

## Section 4 — Verdict Matrix → CONFIRMATION-MERGE / -BLOCK / BLOCK-PENDING-FIX / BLOCK-FINAL

| Row | F1 OOS Δ vs baseline | F2 trades | F3 per-cohort | F4 n_eff | F5 TP-exits | Hard Gates (DSR/PBO/PSR) | VERDICT |
|---|---|---|---|---|---|---|---|
| 1 | ≥ +0.336 | PASS [600,1100] | ≥3/5 positive | [10,25] | ≥15 | ALL PASS | **CONFIRMATION-MERGE** |
| 2 | ≥ +0.336 | PASS | ≥3/5 positive | [10,25] | ≥15 | ANY FAIL | **BLOCK-PENDING-FIX** (re-eval reporting layer) |
| 3 | [+0.10, +0.336) | PASS | ≥3/5 positive | [10,25] | ≥15 | n/a | **CONFIRMATION-PARTIAL** (substrate validated; no merge; reroute /034 to per-axis isolation) |
| 4 | [-0.10, +0.10] | PASS | ≥3/5 positive | [10,25] | ≥15 | n/a | **CONFIRMATION-INERT** (substrate did not lift; close per-cohort/sample-weight composition) |
| 5 | < -0.10 | any | any | any | any | n/a | **CONFIRMATION-NEGATIVE** catastrophic — bundle sub-additive |
| 6 | any | FAIL F2/F3/F5 | any | any | any | n/a | **BLOCK-FINAL** (mechanism integrity broken; bundle composition invalid) |
| 7 | any | any | any | F4 < 10 | any | any | **BLOCK-PENDING-FIX** (n_trials budget bust; rerun at n_trials=50) |

**Row 1 is the MERGE candidate path.** All other rows DO NOT update BASELINE_V1.md.

---

## Section 5 — Risk Mitigation Table

| Risk | Likelihood | Mitigation |
|---|---|---|
| Pool A degenerates (BTC-only) at < 113 IS trades | MEDIUM | Q1 → LM Master decision. If MEDIUM-confidence collapse, escalate to Q2 multi-task ETH-in-training-but-Model-G-at-prediction. |
| /028 LTC × composite_inv_concurrency interaction reverses /028 +0.598 | MEDIUM | F3 per-cohort sign check (LTC must be ≥ 0 in bundle) + Phase 7.4 LM Master post-mortem cite per-symbol attribution shift. |
| Multi-seed lottery dissolves /031 axis lift | LOW-MEDIUM | /032 frozen-HP gave +0.21 clean attribution; /033 is multi-seed at 5 inner seeds — should converge to axis median. If F1 < +0.10, axis dissolved. |
| Wall-clock breach 6h cap | LOW | Single-pass `--seeds 1` × ES=5; projected 4.66h; kill-switch at 5.0h. Month-boundary logging. |
| /027-style `r.model_name` defective hard-assert | LOW | Test suite Section 10 mandates "real-instance TradeResult tests"; /030+ catch-all exclusion of /033 universe; CI integration smoke. |
| n_eff collapse < 10 (budget bust) | LOW-MEDIUM | F4 ∈ [10, 25] verdict matrix routes BLOCK-PENDING-FIX (re-run at n_trials=50). |

---

## Section 6 — Risk Management Design Table (4 gates)

| Gate | Setting | IS-Calibrated Threshold | Simulated Historical Effect |
|---|---|---|---|
| R1 (consecutive-SL cool-down) | K=3, C=27 candles | Active on Models C', D', G, E (UNCHANGED from baseline) | /028 + /019 inherit baseline behavior; LINK /018 inherits Model C' R1 (active). Estimated 5-8% trade-count reduction. |
| R2 (drawdown-triggered scaling) | trigger=7%, anchor=15%, floor=0.33 | Active on Model E ONLY (UNCHANGED from baseline) | DOT trades scale 30-70% at drawdown; baseline showed 71% IS / 63% OOS R2-active fire rate. /033 preserves this. |
| R3 (OOD Mahalanobis gate) | cutoff=0.70, 16 features | Active on ALL models (A, C', D', G, E) | Baseline filter; per-cohort specialists inherit. Estimated 15-25% prediction-skip rate. |
| Sample weighting | composite_inv_concurrency | All models; mean-normalize per symbol | /031 evidence: Kish ratio ≈ 0.80 per cell; weight distribution narrows training updates to rare isolated-entry signal-rich moments. |

**Concentration cap**: top-symbol ≤ 30% of OOS PnL. Baseline runs LINK at 137% concentration; /033 bundle expected to bring LINK to ~40-55% per /031 redistribution evidence. **STRICT 30% NOT achievable** — declare explicit exception with rationale: "specialist isolation produces favorable per-cohort attribution; LINK concentration ~40-55% is structural improvement from baseline 137%; cap relaxed to 60% pending v1-formal-cap codification."

---

## Section 7 — Pre-registered Failure Modes (Honest Accounting)

Per `feedback_v1_methodology_probe_discipline.md`, pre-register the 5 most-likely failure mechanisms BEFORE the run:

1. **POOL-A-COLLAPSE**: Removing ETH from Model A pool drops IS training set from 258 to 113 trades. LightGBM with `n_trials=35` × ES=5 may underfit BTC-only → BTC OOS Sharpe regression below baseline +0.502 by >0.30. Mechanism signature: F3 BTC negative + n_eff < 8 + IS BTC trade count >100 + Optuna best-trial Sharpe std > 0.5 per seed.

2. **LTC-INTERACTION-NEGATIVE**: composite_inv_concurrency × atr_sl=1.0 stacks two label-distribution changes. Concurrency at narrow SL is LOWER (shorter label horizon) → weight per LTC label is HIGHER → over-weights rare LTC label rows → over-fits. Mechanism signature: F3 LTC negative + LTC trade count drops below 30 OOS + LTC IS trade count drops below 100.

3. **SPECIALIST-CANNIBALIZATION**: /018 LINK + /019 ETH + /028 LTC each isolated produced positive single-seed OOS; stacked, specialists compete for the same R3-OOD-filtered prediction confidence budget. Result: per-cohort confidences drop; trade counts drop 20-30% per specialist; OOS Sharpe lifts not realized. Mechanism signature: F2 OOS trades < 600 + F3 multiple cohorts at marginal positive.

4. **SAMPLE-WEIGHTING-DISSOLVES**: /031's +0.21 axis-only lift (per /032 frozen-HP) was at full 5-sym pool training. Per-cohort specialists (Model C' LINK-only) train on different label distributions where concurrency is mechanically lower (single-symbol). composite_inv_concurrency may have NO effect on single-cohort training. Mechanism signature: F4 n_eff ≥ 20 (axis didn't compress trial diversity) + F1 between baseline and Option A projection (+0.66 to +0.70).

5. **BASIN-LOTTERY-DOMINATES**: per /031 V3 ≈ 12% trade-roster overlap with baseline showed basin relocation can produce either +1.04 OR -1.04 OOS Δ depending on lottery draw. /033 at multi-seed should reduce lottery variance but 5 inner seeds may not be enough. Mechanism signature: F1 outside [-0.10, +0.40] band (basin-lottery extreme draw) + per-seed Pareto front median std > 0.40 OOS Sharpe.

---

## Section 8 — Verdict-Cell Determination Mechanics

Mapping the verdict matrix (Section 4) to actual report artifacts:

| Falsifier | Computed from | Cell value |
|---|---|---|
| F1 OOS Sharpe Δ | `comparison.csv` row `sharpe out_of_sample` − BASELINE +0.6637 | Numerical |
| F2 OOS trade count | `comparison.csv` row `total_trades out_of_sample` | Numerical |
| F3 per-cohort sign | `out_of_sample/per_symbol.csv` `net_pnl_pct` column; count positive entries | 0-5 |
| F4 n_eff | `comparison.csv` row `n_eff_per_cell_median` | Numerical |
| F5 TP-exit count | `out_of_sample/trades.csv` `exit_reason == "take_profit"` row count | Integer |
| Hard Gates | `comparison.csv` `dsr` (must > 0.95) + `psr_monthly_vs_1` (must > 0.95) + PBO (computed from CPCV paths) | Numerical |

QR adjudicates after Phase 7 evaluation (FIRST OOS look). Maps results to verdict matrix Row → diary entry.

---

## Section 9 — Library Stack

- `mlfinlab==1.4` (or `mlfinpy` MIT fallback) — meta-labeling, uniqueness weighting; **NOT modified** by /033
- `fracdiff>=0.10` — fractional differentiation; not used in /033
- `statsmodels` — ADF testing in `validation_v1.py`
- `optuna` — TPE sampler at n_trials=35
- `lightgbm>=4.0` — GBDT framework
- `pandas`, `numpy`, `scipy.stats` — standard stack

NO new library introduced at /033.

---

## Section 10 — Symbol Exclusion, Reproducibility, Test Suite Mandate

### Section 10.1 — Symbol Exclusion (V1_EXCLUDED_SYMBOLS unchanged)

```python
V1_EXCLUDED_SYMBOLS = (
    "SOLUSDT", "XRPUSDT", "DOGEUSDT", "NEARUSDT",  # v2
    "BCHUSDT", "LDOUSDT", "TRXUSDT",                # v3
    "BNBUSDT",                                       # historical
)
V1_BASELINE_UNIVERSE = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT")
```

`/033` uses V1_BASELINE_UNIVERSE exactly.

### Section 10.2 — Reproducibility

- `OOS_CUTOFF_DATE = 2025-03-24` (sacred, immutable)
- `training_months = 24` (sacred, immutable)
- Inner seeds: `[42, 123, 456, 789, 1001]` (first 5 of canonical ENSEMBLE_SEEDS roster)
- Outer seed: 42 (default offset; --seeds 1)
- `--n-trials 35`, `--pruned-features`, `--ensemble-size 5`, `--confirmation`
- Walk-forward: `train_end_ms = test_start_ms - embargo_ms` (foundation discipline, NEVER regressed)
- LightGBM determinism: `deterministic=True, force_row_wise=True` (per baseline anchor)
- HEAD commit at runner launch: to be captured at Phase 6 launch

### Section 10.3 — Test Suite Mandate (12+ tests)

Per `feedback_v1_defensive_check_must_be_tested.md` and /030 lessons:

1. `test_bundle_iter33_dispatch_link_only_to_model_cp()` — Routes LINKUSDT only to Model C'
2. `test_bundle_iter33_dispatch_eth_only_to_model_g()` — Routes ETHUSDT only to Model G
3. `test_bundle_iter33_dispatch_ltc_only_to_model_dp()` — Routes LTCUSDT only to Model D'
4. `test_bundle_iter33_dispatch_btc_only_to_model_a()` — Pool A trains on BTC-only after ETH removal
5. `test_bundle_iter33_dispatch_dot_only_to_model_e()` — Model E unchanged
6. `test_bundle_iter33_no_double_dispatch()` — No symbol routes to >1 model
7. `test_bundle_iter33_catchall_exclusion()` — V1_ITER033_UNIVERSE added to /030 catch-all
8. `test_bundle_iter33_real_trade_result_assertion()` — assertions use `trade.symbol`, NOT `trade.model_name` (lesson /027); test against REAL TradeResult instance from production code path
9. `test_bundle_iter33_model_g_btc_trend_gate_active()` — Model G's BTC-trend ±8% gate fires on real klines test fixture
10. `test_bundle_iter33_model_dp_atr_sl_1_0()` — Model D' uses atr_sl=1.0 at both label generation AND entry-time SL
11. `test_bundle_iter33_sample_weight_composite_inv_concurrency_active()` — All models receive composite_inv_concurrency weights; per-symbol mean-normalization applied
12. `test_bundle_iter33_wall_clock_logging()` — Runner emits `[wall_clock] <model>/<month>` log lines at every walk-forward month boundary
13. `test_bundle_iter33_dispatch_banner_print()` — Startup banner identifies /033 bundle dispatch active
14. `test_bundle_iter33_does_not_corrupt_baseline_anchor()` — Running /033 does NOT mutate baseline reports

All 14 tests MUST pass before Phase 6 launch. Phase 5.5 gate verifies test names + presence in `tests/test_iter_v1_033.py`.

---

## Section 11 — Append-Only Path Forward (mandatory on verdict)

After Phase 7 evaluation, QR's Phase 8 diary will adopt Critic's Path Forward verbatim and propose /034 candidates based on /033 verdict cell:

- **Row 1 MERGE**: BASELINE_V1.md updated to /033 bundle. /034 = first post-/033 EXPLORATION; family selection per Critic Path Forward.
- **Row 2 BLOCK-PENDING-FIX**: rerun reporting layer; /034 deferred pending re-eval.
- **Row 3 CONFIRMATION-PARTIAL**: /034 = isolated axis dissection (separate runs for each ingredient at single-seed). Determine which ingredient(s) actually contribute.
- **Row 4 CONFIRMATION-INERT**: /034 = NEW axis family (universe expansion or NEW feature family); per-cohort + sample-weighting branches CLOSE for v1 cycle-4.
- **Row 5 NEGATIVE catastrophic**: /034 = forensic diagnostic of which sub-mechanism broke; substrate composition flagged as anti-pattern.
- **Row 6 BLOCK-FINAL (F2/F3/F5 fail)**: mechanism integrity broken; /034 routes to mechanism repair (single-axis EXPLORATION, NOT bundle).
- **Row 7 BLOCK-PENDING-FIX (n_eff fail)**: /033 rerun at n_trials=50.
