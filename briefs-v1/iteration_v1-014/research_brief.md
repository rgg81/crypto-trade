# iter-v1/014 — Research Brief

**Date**: 2026-05-25
**QR**: claude-opus-4-7 (1M context) — quant-research-v1 mode
**Mode**: EXPLORATION (single-seed-window, ENSEMBLE_SIZE=3, n_trials=35, ≤2h cap)
**Axis**: triple-barrier σ_t source — past-only EWMA at 14-day window, replacing fixed-fraction ATR multipliers; `labeling` family (UNUSED in cycle-2 since /004 cycle-1)
**Branch**: `iteration-v1/014`

---

## Section 0 — Iteration Pre-Header

### 0.1 Anchor

`v0.v1-baseline-corrected` (`BASELINE_V1.md` commit `f8bc12c`)
- IS monthly Sharpe **+0.2829**, OOS monthly Sharpe **+0.6637**
- IS trades 621, OOS trades 189
- 5-seed v1-baseline-corrected ensemble (`[42, 123, 456, 789, 1001]`)
- UNCHANGED post-/010/011/012/013 (all closed EXPLORATION-NEGATIVE)

### 0.2 Mode

**EXPLORATION** (cycle-2 #9 of 10; pre-committed per /013 closeout)
- `--exploration --pruned-features --n-trials 35` (canonical v1 EXPLORATION budget)
- ENSEMBLE_SIZE = 3 (canonical offset=0 seeds `[42, 123, 456]`)
- **NEW labeling-mode CLI flags** for past-only EWMA σ_t-scaled barriers (Section 10)
- R5-BINARY-KILL **DISABLED** for /014 — axis isolation (Section 3)
- ≤2h wall-clock cap

### 0.3 Iteration label

`v1-014`

### 0.4 Determinism note

Inner seeds revert to canonical offset=0 `[42, 123, 456]`. The /011-/013 substrate-test series ran at offsets 0/3/6 with R5-BINARY-KILL enabled; /014 reverts BOTH the seed window AND R5 to the BASELINE config and changes ONE axis only — the labeling σ_t source. This makes /014's IS/OOS Δ comparable directly to BASELINE_V1, NOT to /011-/013 (which were tracking a different mechanism on top of BASELINE).

The new flag `--label-sigma-source ewma14d` selects the EWMA-σ_t-scaled barriers in `LightGbmStrategy`. When the flag is omitted (every prior call and every future call without it), the runner produces BIT-IDENTICAL labels to the 186-history v1 stack and to BASELINE_V1. Backward compatibility preserved by default.

### 0.5 Cadence position

**Cycle-2 EXPLORATION #9 of 10**.

Cycle-2 catalog: /006 (universe, NEG+DEGEN), /007 (feature-family composed, NEG-NEG), /008 (methodology PROMISING-METHODOLOGY), /009 (feature-family delete, NEG-NEG), /010 (risk-primitive proportional R5, NEG-INERT-with-IS-basin-shift), /011 (risk-primitive binary-kill R5, NEG-catastrophic-basin-shift), /012 (methodology-substrate-test offset=3, NEG-PARTIAL-DISSOLUTION), /013 (methodology-substrate-test offset=6, NEG-BASIN-LOTTERY-CATASTROPHIC).

/015 = labeling CONFIRMATION binding regardless of /014 magnitude (PRE-COMMITTED per /013 Critic Phase 7.5 Path Forward Option 1 + LM Master Phase 7.4 §6 + /013 diary item #7; cannot be post-hoc renegotiated). /014 is the EXPLORATION precursor required by 10:1 cadence discipline to legitimize /015.

### 0.6 Architecture-Family Justification (v1-only)

- **Axis family**: **`labeling`** — UNUSED in cycle-2 (last labeling iteration was /004 in cycle-1, which was a per-leg bounds knob, not a label-mode change; this is the FIRST genuine label-distribution change since the v1 refactor)
- **Prior 5 EXPLORATION families** (from `briefs-v1/exploration_catalog.md`):
  - iter-v1/009: `feature-family`
  - iter-v1/010: `risk-primitive`
  - iter-v1/011: `risk-primitive`
  - iter-v1/012: `methodology-substrate-test`
  - iter-v1/013: `methodology-substrate-test`
- **Rotation status**: **VALID** — `labeling` is DIFFERENT from every member of the prior-5 window. The 5-of-5 saturation rule (Phase 5.5 BLOCK if last 5 same-family) is irrelevant; even the looser "if last 3 are same-family, next must rotate" v3-analog rule is satisfied (last 2 are `methodology-substrate-test`; `labeling` is different from both).
- **One-sentence rationale**: /014 is the first genuine UNUSED-family EXPLORATION in cycle-2 since /008 — five iterations since the last new-family axis. Per `feedback_v1_methodology_probe_discipline.md` (user feedback 2026-05-25), methodology probes consumed cycle-2's epistemic budget without edge-finding; /014 pivots decisively to a label-distribution change (replacing fixed-fraction ATR multipliers with past-only EWMA σ_t-scaled barriers at 14-day window), which CHANGES the LightGBM loss surface itself (per-cell labels, weights, and Optuna training objective all shift) instead of changing the optimization route through a fixed surface (the substrate-test failure mode).

---

## Section 1 — Hypothesis

**At v1 EXPLORATION budget (n_trials=35 + ENSEMBLE_SIZE=3 + V1_FEATURE_COLUMNS_PRUNED + R5 DISABLED + offset=0 seeds), replacing the current fixed-fraction ATR-scaled triple-barrier (`atr_tp=2.9/3.5, atr_sl=1.45/1.75` × `NATR_21 × close`) with past-only EWMA σ_t-scaled barriers at 14-day half-life (k_tp=1.06 × σ_t × √21 × close; k_sl=0.53 × σ_t × √21 × close) changes the per-cell IS label distribution and the resulting Optuna loss surface. The hypothesis is FLAT-prior (33% positive / 33% null / 34% negative) per LM Master /013 Phase 7.4 §5 calibration mandate for v1 single-seed EXPLORATION.**

This is a GENUINE basin-shift experiment, not a substrate-test or knob-tweak. Two structural reasons the loss surface materially shifts:

1. **σ_t is the std of close-to-close log-returns; NATR_21 is the average high-low range / close.** These measure different aspects of volatility. EDA Section 2.2 shows per-symbol p10/p90 ratio range of [0.66, 1.47] — meaning the per-row barrier signal changes by ±40-50% in tail rows even at portfolio-median calibration. Per-cell label resolution (TP vs SL vs timeout) will reroute for those rows, producing a different label distribution per (model, month) cell.

2. **σ_t is regime-adaptive within-symbol; NATR_21 lags via the 21-period rolling-window high-low spread.** EWMA at 14-day half-life is more responsive in low-vol regimes (sub-day decay) and equally responsive in high-vol regimes (the EWMA absorbs the shock at the same speed NATR does). The resulting per-row barrier signal differs predictably across the σ_t terciles per Section 2.3.

### Falsifier-decoupled hypothesis structure

Three orthogonal falsifier branches:
- **F-AXIS (mechanical)**: the σ_t labeling mechanism functions correctly — predicted exit-mix shifts in the direction predicted by EDA (F7/F8-NEW falsifiers). If F-AXIS fails, the σ_t mechanism wiring is broken.
- **F1 (OOS Δ)**: the loss-surface change produces OOS edge above mechanical noise — flat-prior; predicted band [-0.30, +0.30] per LM Master flat-prior rule.
- **F3 (IS Δ)**: the loss-surface change produces IS basin-shift above mechanical noise — flat-prior; predicted band [-0.30, +0.30].

### Why this is the right experiment NOW (cycle-2 #9 of 10)

Three structural reasons:

1. **PRE-COMMITTED BINDING**: per /013 Critic Phase 7.5 Path Forward Option 1 + LM Master /013 Phase 7.4 §6 + /013 brief Section 11 + /013 diary item #7, /014 = labeling EXPLORATION precursor; cannot be renegotiated. /015 = labeling CONFIRMATION fires regardless of /014's verdict.

2. **CYCLE-2 EPISTEMIC RECOVERY**: /012 + /013 consumed 2 of cycle-2's 10 slots on methodology probes — per `feedback_v1_methodology_probe_discipline.md` the cycle-2 methodology budget is exhausted. Pivoting to UNUSED-family `labeling` at /014 is the only way to recover information-density at the remaining 2 slots before /015 CONFIRMATION.

3. **STRUCTURAL ORTHOGONALITY**: every prior cycle-2 EXPLORATION axis (universe re-screening, composed features, feature deletion, risk-primitive R5 in two forms, seed-window shifts) operated ON TOP of the same label distribution. /014 is the first axis that changes the LightGBM training-objective DIRECTLY — the labels themselves are different per (model, month, candle) cell. This is the highest-prior basin-escape probability remaining at cycle-2's budget.

---

## Section 2 — IS-Only Evidence (numerical tables)

EDA committed at commit `cafad3d` (`feat(iter-v1/014): EDA scripts for EWMA σ_t calibration`). Two scripts:
- `analysis/iteration_v1-014/sigma_calibration.py` — per-symbol σ_t distribution + k_tp/k_sl calibration
- `analysis/iteration_v1-014/regime_barrier_analysis.py` — regime-conditional barrier comparison + predicted barrier-hit distribution

All EDA filtered to `open_time < 2025-03-24` (IS only). OOS rows masked before any computation.

### 2.1 Per-symbol σ_t distribution (past-only EWMA log-return std, half-life=42 candles ≈ 14 days)

From `analysis/iteration_v1-014/sigma_calibration.csv` (per-candle decimal log-return std):

| Symbol | n_IS | σ_t p10 | σ_t p25 | σ_t p50 | σ_t p75 | σ_t p90 |
|---|---|---|---|---|---|---|
| BTCUSDT | 5707 | 0.00930 | 0.01233 | 0.01607 | 0.02123 | 0.02873 |
| ETHUSDT | 5707 | 0.01163 | 0.01587 | 0.02070 | 0.02710 | 0.03517 |
| LINKUSDT | 5658 | 0.01581 | 0.02184 | 0.02930 | 0.03922 | 0.05082 |
| LTCUSDT | 5667 | 0.01278 | 0.01791 | 0.02496 | 0.03402 | 0.04611 |
| DOTUSDT | 5005 | 0.01521 | 0.02112 | 0.02839 | 0.03762 | 0.04959 |

Per-symbol σ_t at p50 ≈ 1.6%-3.0% per-candle (single-candle log-return std). Annualized via √(3 × 365) ≈ 33.2 → σ_annual ≈ 53%-100% — consistent with crypto-vol regime.

### 2.2 Per-symbol NATR_21 distribution (current barrier source, % of close)

| Symbol | NATR_21 p10 | NATR_21 p25 | NATR_21 p50 | NATR_21 p75 | NATR_21 p90 |
|---|---|---|---|---|---|
| BTCUSDT | 1.396 | 1.745 | 2.458 | 3.501 | 4.715 |
| ETHUSDT | 1.747 | 2.226 | 3.137 | 4.470 | 5.756 |
| LINKUSDT | 2.530 | 3.086 | 4.398 | 6.247 | 8.075 |
| LTCUSDT | 2.084 | 2.640 | 3.695 | 5.367 | 7.453 |
| DOTUSDT | 2.587 | 3.121 | 4.151 | 5.633 | 7.388 |

### 2.3 Calibration result — k_tp / k_sl matching portfolio-median barrier distance

Per-symbol suggested k values (computed by matching median EWMA barrier to median ATR-current barrier; full table in `sigma_calibration.csv`):

| Symbol | suggested k_tp local | suggested k_sl local |
|---|---|---|
| BTCUSDT | 0.968 | 0.484 |
| ETHUSDT | 0.959 | 0.480 |
| LINKUSDT | 1.146 | 0.573 |
| LTCUSDT | 1.131 | 0.565 |
| DOTUSDT | 1.117 | 0.558 |

Volume-weighted portfolio mean: **k_tp = 1.06, k_sl = 0.53**. Per-symbol median: k_tp = 1.12, k_sl = 0.56.

ADOPTED for /014: **k_tp = 1.06, k_sl = 0.53** (portfolio-mean weighting smooths outliers; per-symbol-median alternative would shift barriers tighter for BTC/ETH by 5-6%, wider for alts by 5%).

### 2.4 EWMA/ATR barrier-distance ratio distribution per symbol

From `analysis/iteration_v1-014/regime_summary.csv`:

| Symbol | ratio p10 | ratio p25 | ratio p50 | ratio p75 | ratio p90 |
|---|---|---|---|---|---|
| BTCUSDT | 0.819 | 0.974 | 1.132 | 1.287 | 1.471 |
| ETHUSDT | 0.813 | 0.952 | 1.109 | 1.302 | 1.456 |
| LINKUSDT | 0.670 | 0.787 | 0.922 | 1.053 | 1.176 |
| LTCUSDT | 0.657 | 0.781 | 0.924 | 1.067 | 1.212 |
| DOTUSDT | 0.694 | 0.810 | 0.940 | 1.071 | 1.202 |

**Observed asymmetry**: BTC/ETH EWMA barriers SHIFT WIDER than NATR_21-based barriers (median ratio ~1.11-1.13). LINK/LTC/DOT EWMA barriers SHIFT TIGHTER (median ratio ~0.92-0.94). Per-row variance (p10/p90) of 30-50% — meaningful row-level reroute.

**Interpretation**: NATR_21 (range-based) versus σ_t (return-std-based) are linearly correlated within-symbol BUT with different per-symbol means. The asymmetry between BTC/ETH (NATR underestimates return-vol) and LINK/LTC/DOT (NATR overestimates return-vol) is the load-bearing mechanical effect of /014.

### 2.5 Per-regime barrier distance comparison (σ_t terciles per-symbol)

From `analysis/iteration_v1-014/regime_barriers.csv`:

| Symbol | Regime | n | cur TP p50 | ewma TP p50 | ratio TP p50 |
|---|---|---|---|---|---|
| BTCUSDT | low | 1902 | 5.06% | 5.91% | 1.145 |
| BTCUSDT | normal | 1903 | 7.00% | 7.81% | 1.134 |
| BTCUSDT | high | 1902 | 10.15% | 10.99% | 1.111 |
| LINKUSDT | low | 1886 | 10.80% | 10.45% | 0.943 |
| LINKUSDT | normal | 1886 | 15.71% | 14.23% | 0.910 |
| LINKUSDT | high | 1886 | 21.87% | 19.37% | 0.913 |

**Honest EDA finding**: σ_t and NATR_21 are tightly collinear within-symbol — per-regime ratios are nearly CONSTANT (BTC: 1.14/1.13/1.11; LINK: 0.94/0.91/0.91). The "regime adaptivity" story is WEAKER than initially hypothesized at brief draft. The dominant mechanical effect is the per-symbol LEVEL OFFSET (BTC/ETH wider barriers; alts tighter), not per-regime adaptivity.

This is honestly reported — the hypothesis is REVISED to "per-symbol level offset changes the loss surface via re-weighted label distribution" rather than "regime adaptivity escapes basin lottery."

### 2.6 Predicted barrier-hit distribution (IS, ALL candidate rows simulated forward)

From `analysis/iteration_v1-014/regime_report.md`, per-symbol LONG-side exit mix (all IS candidate candles, NOT the trade roster):

| Symbol | scheme | TP% | SL% | TO% |
|---|---|---|---|---|
| BTCUSDT | CUR | 28.1% | 54.5% | 17.4% |
| BTCUSDT | EWMA | 26.2% | 51.2% | 22.6% |
| ETHUSDT | CUR | 27.9% | 54.3% | 17.8% |
| ETHUSDT | EWMA | 27.3% | 52.2% | 20.5% |
| LINKUSDT | CUR | 22.8% | 50.0% | 27.2% |
| LINKUSDT | EWMA | 25.6% | 54.5% | 19.9% |
| LTCUSDT | CUR | 22.5% | 49.7% | 27.8% |
| LTCUSDT | EWMA | 24.1% | 53.3% | 22.5% |
| DOTUSDT | CUR | 20.4% | 53.4% | 26.2% |
| DOTUSDT | EWMA | 22.0% | 57.0% | 21.0% |

**Predicted mechanical signature** (F7-NEW falsifier):
- BTC/ETH: TO% INCREASES (17.4→22.6 / 17.8→20.5) and TP/SL DECREASES (wider EWMA barriers ⇒ fewer barrier hits)
- LINK/LTC/DOT: TO% DECREASES (27.2→19.9 / 27.8→22.5 / 26.2→21.0) and TP/SL INCREASES (tighter EWMA barriers ⇒ more barrier hits)

The portfolio-level direction is OPPOSITE across the two symbol clusters — a clear mechanical fingerprint.

### 2.7 Predicted IS trade count under /014 EWMA scheme

Baseline IS trade count: **621** (from `reports-v1/iteration_v1-baseline/comparison.csv`).

The trade count emerges from (LightGBM signal generation × barrier-hit confirmation × R3/R5 gating). Barriers affect:
- WHICH entries become labeled training samples (via label resolution)
- WHICH trade exits get realized at execution (via barrier-first-hit detection)

At calibrated k_tp / k_sl with median barrier ≈ current median per symbol, predicted IS trade count is **within ±25% of 621 (range [466, 776])**. F8-NEW mechanical falsifier triggers OUTSIDE this band.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

- **Declaration**: **HIGH-RISK**
- **Reason**: /014 CHANGES the LightGBM training objective domain. Specifically:
  1. The per-(model, month, candle) labels can flip class (TP vs SL vs timeout vs neutral) depending on which barrier the realized forward path hits first under the new σ_t-scaled distance.
  2. The per-sample weights (which are `abs(labeled_pnl)` per `labeling.py:471`) shift in proportion to the new barrier distance — barrier-distance defines the magnitude of the labeled PnL.
  3. The per-cell training distribution that Optuna optimizes over is different. Loss surface shifts → Optuna basin draw is sampled from a different multi-modal distribution than baseline.
- **Mitigation (HIGH-RISK pre-commit per /005 rule + `quant-iteration-v1` skill)**: **PRE-COMMIT TO /015 CONFIRMATION REGARDLESS OF /014 IS/OOS MAGNITUDE.** This is binding per /013 closeout (LM Master Phase 7.4 §6 + Critic Phase 7.5 Path Forward Option 1 + /013 diary item #7). Even if /014 produces EXPLORATION-NEGATIVE-catastrophic verdict, /015 = labeling CONFIRMATION still fires (multi-seed dissolution will give the multi-seed CI for the labeling-axis OOS Δ).
- **Per-iteration single-seed lottery expectation**: per LM Master /013 Phase 7.4 §5 calibration, at v1 single-seed EXPLORATION budget, ANY axis at single-seed produces IS Δ within [-1.0, +0.5] with high variance; OOS Δ within [-1.0, +0.5] with high variance. /014 is no exception. Single-seed magnitude is plausibility envelope, NOT P50 anchor. Verdict-class is governed by FLAT prior.

### Rationale for HIGH-RISK declaration

Per `feedback_v1_substrate_basin_lock.md` (REFUTED-IN-FULL revision at /013 closeout): "At v1 single-seed-window EXPLORATION, EVERYTHING is basin-lottery." A label-distribution change is the LARGEST possible loss-surface intervention available without changing the symbol universe or model architecture — it CAN escape basin lottery, but it also CAN land in a catastrophic basin.

The HIGH-RISK pre-commit tripwire correctly DID NOT fire at /010/011/012/013 (all NORMAL-RISK). /014 is the first cycle-2 HIGH-RISK declaration. The tripwire is /015 CONFIRMATION as the binding fallback — even if /014 fires catastrophic, the multi-seed CONFIRMATION measurement at /015 is what determines whether labeling is a real edge ingredient or not.

---

## Section 3 — Proposed Changes (incorporating Critic /013 Process Recommendations)

### 3.1 Code changes (src/ + runner)

Three changes vs /013's branch:

1. **`src/crypto_trade/strategies/ml/labeling.py`** — add a new `sigma_source` parameter to `label_trades()` that accepts `"natr"` (default; current behavior, BIT-IDENTICAL to baseline) OR `"ewma14d"` (NEW past-only EWMA σ_t at 14-day half-life). Implementation per Section 10.

2. **`src/crypto_trade/strategies/ml/lgbm.py`** — add `sigma_source` and `sigma_k_tp` / `sigma_k_sl` parameters to `LightGbmStrategy.__init__()`. When `sigma_source="ewma14d"`, compute per-row past-only EWMA σ_t at lazy training time using the master DataFrame's close column; pass to `label_trades()` as the new `sigma_values` argument. The new path is wired through `_load_atr_for_master()` → `_load_sigma_for_master()` dispatch when `sigma_source="ewma14d"`.

3. **`run_baseline_v1.py`** — add CLI flags `--label-sigma-source {natr,ewma14d}` (default `natr` for BIT-IDENTICAL backward compatibility), `--label-sigma-k-tp 1.06`, `--label-sigma-k-sl 0.53`. Plumbed through to `run_model()` → `LightGbmStrategy(...)`. R5-BINARY-KILL disabled at /014 invocation (axis isolation).

### 3.2 LM Master Phase 4.5 recommendation response (anticipated)

Phase 4.5 fires SEPARATELY at /014 dispatch. The brief is QR Phase 5 output and pre-dates the Phase 4.5 advisory. Section 3 will be UPDATED post-Phase 4.5 with explicit LM Master recommendation responses per the v1 skill discipline. Anticipated LM Master recommendations per /013 Phase 7.4 §5 (FLAT-prior FINAL calibration rule):

- **Probable LM Master Rec #1**: "Pre-register FLAT priors for verdict-class at v1 single-seed EXPLORATION (33/33/34); HIGH-RISK declaration mandatory" — pre-adopted (Sections 1, 2.5 explicit).
- **Probable LM Master Rec #2**: "Calibration of k_tp / k_sl per portfolio-median match; per-symbol-mean weighting reasonable; do NOT use per-symbol-local k (defeats axis-isolation by introducing 5 nuisance hyperparameters)" — pre-adopted (Section 2.3 chose portfolio-mean k_tp=1.06, k_sl=0.53).
- **Probable LM Master Rec #3**: "F-AXIS mechanical falsifier (predicted exit-mix direction) is the critical attribution falsifier — if it fails, the σ_t mechanism is broken and F1/F3 results are not attributable to the labeling axis" — pre-adopted (Section 4 F7-NEW + F8-NEW).
- **Probable LM Master Rec #4**: "At single-seed and HIGH-RISK, MULTI-SEED CONFIRMATION at /015 is the binding measurement; /014 single-seed verdict is plausibility-envelope-only" — pre-adopted (Section 2.5 + Section 6 explicit).

If LM Master Phase 4.5 Rec materially diverges from the above, the brief Section 3 will be UPDATED in a separate commit (per v1 skill Section 0.6 + 3.6).

### 3.3 Critic /013 Process Recommendations — ADOPTED EXPLICITLY

Per `briefs-v1/iteration_v1-013/review.md` §"Recommendations to QR":

#### Rec #1 — Engineering report 3rd-strike dispatch-side enforcement

**Critic /013 Rec text**: "Engineering report deliverable enforcement gap (3rd strike): `reports-v1/iteration_v1-013/engineering_report.md` missing despite brief mandate + Critic /012 Rec #2 + critic_preflight.md acceptance. /011 and /012 produced it. Future iterations: Critic Phase 6.0 explicit precondition check (currently only checks SPEC, not produced artifact). For /014, escalate to Critic Phase 7.5 dispatch hard-reject if missing."

**/014 Adoption**:
- Brief Section 10.2 below declares the engineering report at `reports-v1/iteration_v1-014/engineering_report.md` AS A BLOCKING DELIVERABLE for Phase 7.5 dispatch (NOT a Phase 7 carry-forward). Phase 5.5 gate enforces file existence after Phase 6 closeout.
- Critic Phase 6.0 pre-flight MUST verify the brief Section 10.2 includes the blocking-deliverable language.
- Critic Phase 7.5 dispatch is hard-rejected if `engineering_report.md` is missing from `reports-v1/iteration_v1-014/`. Orchestrator escalation point: any Phase 7.5 invocation requires file existence pre-check.

#### Rec #2 — Memory file `feedback_v1_substrate_basin_lock.md` REFUTED-IN-FULL — acknowledged

**Critic /013 Rec text**: "Substrate-decomposition memory file update: `feedback_v1_substrate_basin_lock.md` marked REFUTED-IN-FULL at n=4 per LM Master Phase 7.4 §2 commitment. Future v1 EXPLORATION briefs must not cite the decomposition as if it still holds."

**/014 Adoption**:
- Brief does NOT cite the 2-property decomposition as if it holds. Section 1 + Section 5 use FLAT priors only per LM Master /013 Phase 7.4 §5 FINAL calibration rule.
- Section 2.5 + Section 6 reference the REFUTED-IN-FULL memory revision explicitly.
- Substrate-property claims at n<10 are FORBIDDEN per memory revision; the brief makes no such claims.

#### Rec #3 — Pre-committed /015 labeling CONFIRMATION binding — acknowledged

**Critic /013 Rec text**: "PRE-COMMITTED CONDITIONAL FIRES — /015 axis LOCKED as labeling CONFIRMATION: F1 OOS Δ ≤ 0 (observed -1.017) → /015 = UNUSED-family CONFIRMATION (labeling). Conditional binding; cannot be post-hoc renegotiated. /014 MUST be labeling EXPLORATION precursor with HIGH-RISK declaration to legitimize /015 by 10:1 cadence."

**/014 Adoption**:
- /014 axis = labeling triple-barrier σ_t source via past-only EWMA at 14-day window. Sections 0.6, 1, 2.5, 11 all confirm.
- HIGH-RISK declaration in Section 2.5. Mitigation = pre-commit /015 = labeling CONFIRMATION regardless of /014 magnitude.
- /015 axis is BINDING — cannot be renegotiated by any /014 outcome.

### 3.4 Runner invocation

```bash
uv run python run_baseline_v1.py \
    --exploration \
    --iteration 14 \
    --pruned-features \
    --n-trials 35 \
    --label-sigma-source ewma14d \
    --label-sigma-k-tp 1.06 \
    --label-sigma-k-sl 0.53 \
    --label-sigma-halflife-days 14
```

R5-BINARY-KILL and R5 proportional vol-target are OMITTED (default disabled per runner; axis isolation — /014 tests labeling, not R5). `ensemble_seeds_offset=0` (default; canonical `[42, 123, 456]`).

### 3.5 Expected wall-clock budget

Same compute footprint as /011-/013 plus one-time per-row σ_t computation overhead (vectorized EWMA in `_load_sigma_for_master()`; estimated <5s additional per model). Predicted wall-clock: 75-95 min. ≤2h cap is safe.

---

## Section 4 — Falsifiers (F1-F9 inheritance + F7-NEW / F8-NEW)

Eight falsifiers; F1-F6 inherited (re-numbered with explicit pre-registered numerical conditions); F7/F8/F9 from /013 are RETIRED (substrate-decomp REFUTED; no longer applicable); F7-NEW + F8-NEW are mechanical attribution falsifiers for the σ_t axis.

### F1 — OOS Sharpe-Δ vs BASELINE (FLAT prior)

- **Condition**: OOS Sharpe Δ = (OOS Sharpe iter-v1/014) - (OOS Sharpe BASELINE +0.6637)
- **PROMISING** (single-seed): Δ ∈ [+0.05, +0.55] — magnitude plausibility band; advances /015 evidence
- **NULL / INERT**: Δ ∈ [-0.05, +0.05] — within noise band
- **NEGATIVE**: Δ ∈ [-0.30, -0.05] — labeling axis hurts under single-seed lottery
- **NEGATIVE-catastrophic**: Δ < -0.30 — basin draw catastrophic at single-seed; still proceed to /015 CONFIRMATION
- **NEGATIVE-numerical-boundary**: Δ ∈ (-0.07, -0.03) — boundary; require seed-determinism audit at /015

### F2 — Trade count (mechanical sanity)

- **Condition**: |IS_trades - 621| ≤ 0.25 × 621 → IS_trades ∈ [466, 776]
- **PASS**: in band — labels resolve at calibrated barrier widths
- **FAIL-MISCALIBRATION**: outside band — σ_t scheme mis-calibrated OR wiring defect; verdict deferred to F-AXIS

### F3 — IS Sharpe-Δ vs BASELINE (FLAT prior)

- **Condition**: IS Sharpe Δ = (IS Sharpe iter-v1/014) - (IS Sharpe BASELINE +0.2829)
- **PROMISING** (single-seed): Δ ∈ [+0.10, +0.60] — basin shifts positively
- **NULL / INERT**: Δ ∈ [-0.10, +0.10]
- **NEGATIVE**: Δ ∈ [-0.30, -0.10]
- **NEGATIVE-catastrophic**: Δ < -0.30 — basin draw catastrophic

### F4 — DEGENERATE_PREDICTOR detector

- **Condition**: per `validation_v1.detect_degenerate_predictor()` — fire if any model has >99% single-direction prediction OR >95% identical probability output
- **PASS**: no fire (expected — labeling axis produces well-distributed labels)
- **FAIL**: fire — verdict immediately NEGATIVE-degenerate (mechanism produces trivial predictor)

### F5 — PSR (informational at EXPLORATION; not gating)

- **Condition**: PSR_monthly_vs_0 ≥ 0.50 both IS and OOS
- **PASS**: positive-edge regime
- **FAIL**: negative-edge regime — informational only at EXPLORATION

### F6 — OOS roster overlap with BASELINE (informational)

- **Condition**: 100% × (trades_in_BASELINE ∩ trades_in_iter014) / max(trades_in_iter014, 1)
- **Expected band**: [50%, 75%] — labels change ⇒ rosters partially differ but model still selects from similar high-conviction candidates
- **Outside band**: WIDE diagnostic input for Phase 7.4 LM Master post-mortem

### F7-NEW — Per-symbol barrier-hit distribution change (MECHANICAL ATTRIBUTION)

- **Predicted direction** (from EDA Section 2.6):
  - BTC + ETH (Model A): TO% INCREASES vs baseline; TP/SL DECREASES (wider EWMA barriers ⇒ fewer barrier hits)
  - LINK + LTC + DOT (Models C, D, E): TO% DECREASES vs baseline; TP/SL INCREASES (tighter EWMA barriers ⇒ more barrier hits)
- **Diagnostic table at Phase 6 closeout** (engineering report MUST include): per-symbol IS exit-mix comparison (TP% / SL% / TO%) vs baseline
- **PASS** (axis-attribution): observed direction MATCHES predicted direction for all 5 symbols (BTC/ETH up TO, LINK/LTC/DOT down TO)
- **PARTIAL** (axis-attribution): 3-4 of 5 symbols match
- **FAIL** (axis-attribution): 2 or fewer of 5 symbols match — σ_t MECHANISM IS NOT WORKING as designed; F1/F3 not attributable to labeling axis (likely wiring defect)

### F8-NEW — Total IS trade count within ±25% of baseline (calibration falsifier)

- **Condition**: IS_trades_iter014 ∈ [466, 776] (621 ± 25%)
- **PASS**: well-calibrated barriers
- **FAIL**: barriers too tight (more hits, fewer timeouts surface as more trades) OR too loose (fewer hits, fewer trades pass model confidence threshold and timeout-resolution)

### F9 — RETIRED (substrate-magnitude lock REFUTED at /013; no longer applicable)

The substrate-magnitude band [+0.38, +0.58] from /011-/013 is dead. /014 makes NO substrate-magnitude claim per `feedback_v1_substrate_basin_lock.md` REFUTED-IN-FULL revision.

---

## Section 5 — Predicted Outcomes (FLAT-Prior Pre-Registration)

Per LM Master /013 Phase 7.4 §5 FINAL calibration rule, FLAT priors only at v1 single-seed EXPLORATION. Predicted distribution of F1 OOS Δ:

| Outcome class | Predicted band | Pre-registered probability |
|---|---|---|
| F1 PROMISING (positive OOS basin draw) | [+0.05, +0.55] | 33% |
| F1 NULL / INERT (basin lands within noise) | [-0.05, +0.05] | 33% |
| F1 NEGATIVE (negative OOS basin draw) | [-0.55, -0.05] | 34% |

F3 pre-registration mirrors F1 with adjusted band: PROMISING ∈ [+0.10, +0.60]; NULL ∈ [-0.10, +0.10]; NEGATIVE ∈ [-0.60, -0.10].

**No P50 anchor** per FINAL calibration rule. Magnitude bands are plausibility envelopes derived from /011-/013 observed single-seed Sharpe-Δ range; they DO NOT encode a P50 prediction.

### Cell-pre-registration matrix (F1 × F3 × F-AXIS)

8-cell deterministic matrix (per Critic /012 Rec #1 mandate):

| Cell | F1 | F3 | F7-NEW / F8-NEW | Verdict-class |
|---|---|---|---|---|
| 1 | PROMISING | PROMISING | PASS | **EXPLORATION-PROMISING (labeling axis advances /015 evidence)** |
| 2 | PROMISING | NULL/NEGATIVE | PASS | **EXPLORATION-PROMISING-PARTIAL (basin partially transfers OOS only — caution for /015)** |
| 3 | NULL | NULL | PASS | **EXPLORATION-NULL-CLEAN (labeling change had no edge-effect; informational input for /015 design)** |
| 4 | NULL | PROMISING | PASS | **EXPLORATION-NEGATIVE-IS-OVERFIT (IS basin shifted, did not transfer; classic single-seed lottery)** |
| 5 | NEGATIVE | NEGATIVE | PASS | **EXPLORATION-NEGATIVE (catastrophic basin draw; informational; /015 still fires per pre-commit)** |
| 6 | NEGATIVE | PROMISING | PASS | **EXPLORATION-NEGATIVE-IS-OVERFIT (sister to cell 4 but more extreme)** |
| 7 | any | any | FAIL | **EXPLORATION-NEGATIVE-WIRING (σ_t mechanism not working; engineering investigation needed)** |
| 8 | any | any | F2 FAIL (calibration) | **EXPLORATION-NEGATIVE-MISCALIBRATED (k_tp / k_sl wrong; rerun at adjusted k at /015)** |

Cells 1, 2 are PROMISING (advance to /015 with stronger evidence). Cells 3-6 are NEGATIVE/NULL but /015 still fires per HIGH-RISK pre-commit. Cells 7-8 are WIRING/CALIBRATION defects requiring fix-then-re-run path; if confirmed at Phase 7.5, BLOCK-PENDING-FIX verdict with one rerun chance.

---

## Section 6 — What Could Falsify the Hypothesis (Pre-Registered Tripwires)

### 6.1 Tripwire: F7-NEW barrier-hit distribution FAIL

If observed per-symbol exit-mix does NOT match the predicted direction (BTC/ETH TO% up; LINK/LTC/DOT TO% down) for 3+ symbols, the σ_t mechanism is not functioning correctly. Verdict immediately = EXPLORATION-NEGATIVE-WIRING (cell 7). Phase 7.4 LM Master post-mortem investigates root cause.

### 6.2 Tripwire: F8-NEW calibration FAIL

If IS_trades outside [466, 776], the barriers are mis-calibrated. Verdict = EXPLORATION-NEGATIVE-MISCALIBRATED (cell 8). The /015 CONFIRMATION still fires (binding pre-commit) but at adjusted k_tp / k_sl based on /014's observed median ratio.

### 6.3 Tripwire: HIGH-RISK pre-commit fires

This is the FIRST cycle-2 HIGH-RISK declaration. The mitigation /015 = labeling CONFIRMATION binding regardless of /014 magnitude is the pre-commit. If /014 produces NEGATIVE-catastrophic (cell 5), /015 STILL FIRES with multi-seed dissolution evaluating the true mechanical layer.

### 6.4 Tripwire: methodology-probe re-introduction

Per `feedback_v1_methodology_probe_discipline.md`, cycle-2's methodology-probe budget is EXHAUSTED. /014 is NOT a methodology probe; it is a genuine labeling axis. If at /014 closeout the Critic/QR/LM Master 3-way convergence proposes another methodology probe at /014 brief → BLOCK at Phase 5.5 gate.

---

## Section 7 — Failure Modes

Per LM Master /013 Phase 7.4 §5 ("at v1 single-seed EXPLORATION, EVERYTHING is basin-lottery"):

1. **Basin lottery at single-seed**: 33-34% probability of negative basin draw regardless of mechanism. This is the dominant failure mode at /014. Mitigation: /015 CONFIRMATION multi-seed dissolution (binding).

2. **Mis-calibration**: k_tp=1.06, k_sl=0.53 calibrated against portfolio-median ATR barrier. If the median is not representative (e.g., heavy-tail dominance per-symbol), per-symbol trade counts shift more than the portfolio aggregate suggests. F8-NEW catches.

3. **σ_t lookahead risk**: EWMA σ_t at candle t MUST be computed from returns observed at t-1 or earlier. Implementation uses `pd.Series.ewm(halflife=42, adjust=False).mean()` on log-returns, then SHIFT BY 1 to enforce strict past-only. Phase 6.0 Critic pre-flight verifies the shift is present in `lgbm.py`'s new code path. Static scan for `shift(1)` or equivalent index offset MUST PASS.

4. **σ_t and NATR_21 collinearity** (EDA Section 2.5): the regime-conditional ratio is nearly constant within-symbol — the mechanism's "regime adaptivity" story is weaker than initially hypothesized. The dominant mechanical effect is the per-symbol level offset (BTC/ETH wider; alts tighter). This is honest finding; if the basin-shift comes ONLY from per-symbol level offset, /015 multi-seed mean may be small (per-symbol-mean-axis is sister to per-cell-hyperparameter axis tested at /005, also single-seed flat).

5. **R5 disabled at /014 vs R5-BINARY-KILL at /011-/013**: /014's IS/OOS Δ is comparable to BASELINE not to /011-/013. The /015 CONFIRMATION will pair the labeling axis with whatever R5 state is operative at CONFIRMATION (likely R5 disabled per /013 catalog axiom that R5 family is CLOSED at v1 single-seed). Comparability between /014 and /015 is preserved.

---

## Section 8 — Verdict Gates (per Critic /010 Rec #1 sign-symmetric + Critic /012 Rec #1 complete matrix)

### 8.1 Cell pre-registration (8-cell matrix from Section 5)

Already enumerated in Section 5. Reproduced here as the binding verdict-mapping table:

| Cell | F1 OOS Δ band | F3 IS Δ band | F7-NEW | F8-NEW | Verdict class |
|---|---|---|---|---|---|
| 1 PROMISING | [+0.05, +0.55] | [+0.10, +0.60] | PASS | PASS | EXPLORATION-PROMISING |
| 2 PROMISING-PARTIAL | [+0.05, +0.55] | [-0.10, +0.10] or [-0.60, -0.10] | PASS | PASS | EXPLORATION-PROMISING-PARTIAL |
| 3 NULL-CLEAN | [-0.05, +0.05] | [-0.10, +0.10] | PASS | PASS | EXPLORATION-NULL-CLEAN |
| 4 NEGATIVE-IS-OVERFIT | [-0.05, +0.05] | [+0.10, +0.60] | PASS | PASS | EXPLORATION-NEGATIVE-IS-OVERFIT |
| 5 NEGATIVE | [-0.55, -0.05] | [-0.60, -0.10] | PASS | PASS | EXPLORATION-NEGATIVE |
| 6 NEGATIVE-IS-OVERFIT-EXTREME | [-0.55, -0.05] | [+0.10, +0.60] | PASS | PASS | EXPLORATION-NEGATIVE-IS-OVERFIT-EXTREME |
| 7 WIRING | any | any | FAIL | — | EXPLORATION-NEGATIVE-WIRING |
| 8 MISCALIBRATED | any | any | — | FAIL | EXPLORATION-NEGATIVE-MISCALIBRATED |

Boundary cells:
- F1 ∈ (+0.03, +0.07) → "F1 numerical-boundary"; Critic seed-determinism audit at /014 closeout BEFORE /015 axis is finalized
- F3 ∈ (+0.07, +0.13) OR (-0.13, -0.07) → "F3 numerical-boundary"; same audit
- F2 trade count ∈ (455, 466) OR (776, 787) → "F2 numerical-boundary"; same audit

### 8.2 Verdict resolution rule

Verdict = first cell that matches observed (F1, F3, F7-NEW, F8-NEW). Cells 7-8 OVERRIDE 1-6 (mechanical failures dominate edge-claim falsifiers).

If observed value falls in a numerical-boundary range, Critic Phase 7.5 declares "boundary verdict requires seed-determinism audit"; QR may not pre-commit to a /015 axis until audit resolves.

### 8.3 Hard merge gates (informational for /014 EXPLORATION)

Inherited from BASELINE_V1.md §"Hard Merge Floors":
- IS Sharpe > 1.0 (BASELINE +0.2829; /014 single-seed magnitude band [-0.6, +0.9]; very unlikely to clear)
- OOS Sharpe > 1.0 (BASELINE +0.6637; /014 plausibility band [+0.0, +1.2]; possible but not pre-committed)
- DSR > 0.95, PBO < 0.4, PSR > 0.95 — informational at EXPLORATION
- Top-symbol concentration ≤ 30% — informational at EXPLORATION

EXPLORATION never merges. /015 CONFIRMATION evaluates merge floors with multi-seed dissolution.

---

## Section 9 — Library Stack (mandatory per /009 closeout amendment)

- `numpy>=1.24` — array ops (already installed)
- `pandas>=2.0` — `ewm(halflife=N, adjust=False)` for past-only EWMA std (already installed)
- `pyarrow>=14` — parquet I/O (already installed)
- `lightgbm==4.x` — unchanged (no version pin change at /014)
- `optuna>=3.5` — unchanged
- `statsmodels>=0.14` — `adfuller` for Critic Check 5 ADF stationarity on labels (already installed)

No new dependencies. Pandas `ewm()` is the standard implementation; mathematically equivalent to:
```
alpha = 1 - exp(-ln(2) / halflife)
ewma_var_t = alpha × return_t^2 + (1-alpha) × ewma_var_{t-1}
```
Numerical equivalence with `pandas` checked via the EDA script (`compute_ewma_sigma_per_candle` is a thin wrapper around `pd.Series.ewm(halflife=42, adjust=False).mean()`).

---

## Section 10 — Implementation Spec (QE Deliverables)

### 10.1 Source files to modify

#### `src/crypto_trade/strategies/ml/labeling.py`

Add `sigma_values: np.ndarray | None = None` and `sigma_k_tp: float | None = None`, `sigma_k_sl: float | None = None` to `label_trades()` signature. When ALL THREE are provided (replacing the existing `atr_values` path):
- For each candidate row, compute barrier distance using:
  ```
  tp_dist_pct_decimal = sigma_k_tp × sigma_values[idx] × sqrt(timeout_candles)
  sl_dist_pct_decimal = sigma_k_sl × sigma_values[idx] × sqrt(timeout_candles)
  tp_dist_price = entry × tp_dist_pct_decimal
  sl_dist_price = entry × sl_dist_pct_decimal
  ```
- The rest of the triple-barrier scan (look-forward, first-hit detection) is BIT-IDENTICAL to the existing path.
- When `sigma_values is None`, the function path is BIT-IDENTICAL to /013's. Backward compatibility preserved.

#### `src/crypto_trade/strategies/ml/lgbm.py`

Add to `LightGbmStrategy.__init__()` (alongside `atr_tp_multiplier`, `atr_sl_multiplier`):
- `sigma_source: str = "natr"` (default — current NATR path)
- `sigma_k_tp: float | None = None`
- `sigma_k_sl: float | None = None`
- `sigma_halflife_candles: int = 42` (= 14 days × 3 candles/day)

When `sigma_source == "ewma14d"`:
- In `compute_features()` (after `self._label_atr_values = self._load_atr_for_master()`): compute `self._label_sigma_values = self._load_sigma_for_master()` instead.
- New method `_load_sigma_for_master()`: per-symbol vectorized EWMA on log-returns of close, half-life=`sigma_halflife_candles`, shift by 1 candle for strict past-only. Returns array aligned with master rows.
- In `_train_for_month()` and `predict()` label-call paths: pass `sigma_values=self._label_sigma_values, sigma_k_tp=self.sigma_k_tp, sigma_k_sl=self.sigma_k_sl` to `label_trades()` instead of `atr_values=...`.

When `sigma_source == "natr"` (default): BIT-IDENTICAL behavior to /013. Backward compatibility preserved.

#### `run_baseline_v1.py`

Add CLI flags:
- `--label-sigma-source` (choices: `natr`, `ewma14d`; default: `natr`)
- `--label-sigma-k-tp` (default: 1.06)
- `--label-sigma-k-sl` (default: 0.53)
- `--label-sigma-halflife-days` (default: 14)

Plumb through `run_model()` → `LightGbmStrategy(...)` constructor. When `--label-sigma-source ewma14d`:
- `sigma_source="ewma14d"`, `sigma_k_tp=<flag>`, `sigma_k_sl=<flag>`, `sigma_halflife_candles=<flag_days> × 3`
- `atr_tp_multiplier` and `atr_sl_multiplier` are STILL passed (they remain runtime-active for SL/TP price computation at execution time per `backtest.py:799`) — `lgbm.py` reads from sigma-derived barriers ONLY in `_train_for_month()`'s `label_trades()` call. The execution-side barrier is unchanged.

WAIT — this needs CLARIFICATION. The current ATR-multiplier path is used in TWO PLACES:
1. **Label generation** (`_train_for_month()` → `label_trades(atr_values=...)`) — defines TP/SL distance used to label training samples.
2. **Execution barrier** (`backtest.py:799` reads `atr_tp_multiplier` from strategy config; live trade enters at signal and exits at `entry × (1 + atr_tp_mult × NATR_14 / 100)`).

For /014 axis isolation, we need BOTH places to use σ_t-scaled barriers — otherwise labels say "barrier hit at 5% TP" but execution says "barrier hit at 7% TP", creating inconsistency.

**RESOLUTION**: /014 modifies the execution-side barrier ALSO when `sigma_source="ewma14d"`. Implementation:
- `LightGbmStrategy._compute_trade_barriers_for_signal()` (or wherever execution barriers are computed; QE to verify the exact call site) reads `self.sigma_source`. When `ewma14d`, returns sigma-derived TP/SL distance instead of NATR-derived.
- The `backtest.py:799` call path uses the strategy's barrier-distance computation; the strategy's behavior changes, the backtest engine is unchanged.
- QE Phase 6 implementation MUST verify both label-time AND execution-time barriers use the same scheme (a "barrier-source consistency" assertion in `LightGbmStrategy.__init__()`).

### 10.2 Required artifacts (BLOCKING for Phase 7.5 dispatch — Critic /013 Rec #1 dispatch-side enforcement)

QE produces in Phase 6 closeout:
1. `reports-v1/iteration_v1-014/comparison.csv` — same schema as baseline
2. `reports-v1/iteration_v1-014/in_sample/` + `out_of_sample/` directories with full reports
3. `reports-v1/iteration_v1-014/per_symbol.csv` — per-symbol exit-mix breakdown (TP/SL/TO counts) for both IS and OOS (NEW — F7-NEW falsifier diagnostic)
4. **`reports-v1/iteration_v1-014/engineering_report.md`** — **BLOCKING deliverable for Phase 7.5 dispatch**. Contains:
   - Wall-clock breakdown per model (A, C, D, E)
   - Per-model σ_t distribution sanity check (p10/p50/p90)
   - Per-symbol exit-mix comparison vs baseline (F7-NEW table)
   - F8-NEW total IS/OOS trade count vs predicted band
   - σ_t lookahead audit (manual or programmatic: shift-by-1 evidence)
   - Any defects encountered

Phase 5.5 gate (Engineer) AND Phase 6.0 pre-flight (Critic) BOTH verify that the brief Section 10.2 language declares engineering_report.md as BLOCKING DELIVERABLE. Phase 7.5 dispatch is hard-rejected if the file is missing — this is the 3rd-strike enforcement codification.

### 10.3 Test suite additions

- `tests/test_labeling.py::test_label_trades_sigma_source_ewma14d` — given a synthetic sigma_values array, verify barrier distances are `k × sigma × sqrt(21)` to 1e-6 tolerance.
- `tests/test_lgbm.py::test_sigma_source_ewma14d_backward_compat` — when `sigma_source="natr"`, output is BIT-IDENTICAL to the pre-/014 codebase (no regression).
- `tests/test_lgbm.py::test_sigma_source_ewma14d_past_only` — synthetic master with known sigma trajectory; verify the sigma at candle t equals the EWMA computed from candles ≤ t-1 (no lookahead).

All 3 tests MUST PASS before Phase 7.5 dispatch.

---

## Section 11 — Alternates Conditional on /014 Outcome

Per Critic /013 Path Forward Option 1 (PRE-COMMITTED) + reserve options:

### Option 1 (PRIMARY, PRE-COMMITTED): /015 = labeling CONFIRMATION

**Binding regardless of /014 verdict**. Multi-seed dissolution at ENSEMBLE_SIZE=10 + n_trials=35, with the EWMA σ_t labeling axis ACTIVE. Tests whether the labeling-axis OOS Δ at multi-seed mean is materially different from BASELINE_V1 OOS +0.6637.

- If /014 = PROMISING (cell 1 or 2): /015 confirms or refutes at multi-seed; first labeling-axis edge ingredient potentially merges to BASELINE_V1.md per `feedback_v3_baseline_update_policy.md`.
- If /014 = NULL or NEGATIVE (cells 3-6): /015 still fires; multi-seed mean ≈ 0 vs BASELINE confirms labeling is NULL at multi-seed.
- If /014 = WIRING / MISCALIBRATED (cells 7-8): /014 BLOCK-PENDING-FIX rerun, then /015 = labeling CONFIRMATION at FIXED config.

### Option 2 (RESERVE conditional on /014 = NEGATIVE-catastrophic + /015 NULL): re-grid k_tp / k_sl

If /014 catastrophic AND /015 multi-seed mean is null, the calibrated k_tp=1.06 / k_sl=0.53 might be wrong even at portfolio-median match. Re-grid at (k_tp, k_sl) ∈ {(0.8, 0.4), (1.3, 0.65), (1.5, 0.75)} as a /017+ post-CONFIRMATION axis (if cycle-2 catalog allows).

### Option 3 (RESERVE if labeling family CLOSED): pivot to UNUSED-UNUSED family

Per axis taxonomy: `universe` (UNUSED in cycle-2 since /006) or `model-arch` (UNUSED in cycle-2). Reserved for /017+ if labeling axis confirmed-null at /015. Critic /013 Path Forward Option 2 (universe equal-weight + LTC cap) and Option 3 (XGBoost head-to-head) are candidates.

---

## Section 12 — Catalog Closeout Plan

At /014 closeout:

1. **EXPLORATION catalog append**: one-line entry in `briefs-v1/exploration_catalog.md` per the standard schema.
2. **Diary**: `diary-v1/iteration_v1-014.md` with verdict + headline metrics + lessons + permanent additions.
3. **Tag**: `v0.v1-014` after Phase 8 closeout (per `feedback_always_document.md` discipline).
4. **NO trunk merge** unless verdict is PROMISING AND src/ changes are strictly accretive (engineering report + new code path; default `sigma_source="natr"` BIT-IDENTICAL preserves backward compatibility, so the new code path COULD merge to main as infrastructure regardless of edge outcome — but per cycle-2 history, no EXPLORATION has merged src/ to main; this brief defers the merge decision to Phase 8 diary).
5. **Permanent additions** (if applicable): update `feedback_v1_substrate_basin_lock.md` only if /014 produces a definitive falsification or confirmation of any remaining sub-claim; per the REFUTED-IN-FULL revision, no remaining claims to refute.
6. **PRE-COMMITTED CONDITIONAL CARRY-FORWARD**: /015 = labeling CONFIRMATION; cannot be renegotiated.

---

## Section 13 — Phase 5.5 Self-Check

QR self-audits this brief against the v1 skill's Phase 5.5 gate checklist:

| Section requirement | Status | Notes |
|---|---|---|
| 0 — Iteration pre-header (anchor, mode, label, determinism, cadence, axis family) | PRESENT | |
| 0.5 — Cadence position (cycle-N + EXPLORATION #N/10) | PRESENT | cycle-2 #9/10 |
| 0.6 — Architecture-family justification (v1-only) | PRESENT | labeling UNUSED in cycle-2; rotation VALID |
| 1 — Hypothesis (single sentence + structure) | PRESENT | FLAT prior 33/33/34 |
| 2 — IS-only evidence (numerical tables from committed analysis scripts) | PRESENT | 7 sub-sections; scripts at `analysis/iteration_v1-014/` |
| 2.5 — HIGH-RISK Axis Declaration (v1-only) | PRESENT | HIGH-RISK; mitigation = /015 CONFIRMATION pre-commit |
| 3 — Proposed Changes (src/ + LM Master + Critic recs) | PRESENT | Critic /013 Recs #1-3 adopted explicitly |
| 4 — Falsifiers (numerical conditions) | PRESENT | F1-F8 incl. F7-NEW + F8-NEW + F9 retired |
| 5 — Predicted outcomes (per-cell pre-registration) | PRESENT | 8-cell matrix |
| 6 — What could falsify | PRESENT | 4 tripwires |
| 7 — Failure modes | PRESENT | 5 modes |
| 8 — Verdict gates (sign-symmetric on F3; complete F1×F3×F-axis matrix) | PRESENT | Section 8.1 8-cell binding table |
| 9 — Library stack | PRESENT | No new deps |
| 10 — Implementation spec for QE | PRESENT | src/ files + tests + BLOCKING engineering_report.md |
| 11 — Alternates | PRESENT | 3 options |
| 12 — Catalog closeout plan | PRESENT | |
| 13 — Phase 5.5 self-check | PRESENT | this section |
| Methodology-probe check | PASS | /014 is NOT a methodology probe — genuine labeling axis change |
| LM Master Phase 4.5 placeholder | PRESENT | Section 3.2; brief will be UPDATED post-Phase 4.5 if recommendations diverge |
| Engineering report BLOCKING declaration | PRESENT | Section 10.2 |

Self-check: **PASS**. Brief is complete per v1 skill discipline. Phase 5.5 gate (Engineer) and Phase 6.0 pre-flight (Critic) should both verify against this checklist.
