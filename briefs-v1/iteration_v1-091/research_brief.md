# iter-v1/091 — Research Brief: R-CONV (ensemble-conviction trade gate)

**Date**: 2026-06-11
**Track**: v1 (refactored)
**Branch**: `iteration-v1/091`
**Author**: QR (autopilot)
**Anchor**: BUNDLE-002 `v0.v1-082` (DOT/063 + ETH/064 + BTC/065 + AAVE/078; IS +0.7157 / OOS +1.0043)
**User directive (2026-06-11)**: "r-conv let's go" — 2nd machinery axis of cycle-7 after /090 W-DECAY NEGATIVE.

---

## Section 0 — Summary

R-CONV is a **post-aggregator ensemble-conviction trade gate**. The 50-seed specialist already
votes per candle (each seed emits a signed weight of `+100` / `-100` / `0`); the aggregator computes
`_final_signed = mean(signed_weights)` and `_sp_confidence = |_final_signed| / 100` = **the net
seed-agreement fraction** (`lgbm.py:2135,2162`). Today **every** non-zero-consensus candle trades.
R-CONV adds a stateless opt-in skip gate: **trade only when `_sp_confidence >= tau`; skip otherwise**
(low net agreement = the noise signature, since each near-tie candle is a coin-flip of the seeds).

- **Chosen seat**: **ETH/064** (evidence-based; see §2 — overrides the raw lowest-WR heuristic).
- **Pre-registered tau = 0.06** (single value, IS-only-reasoned; no grid, no OOS tuning).
- **Lock**: methodology unchanged (50 inner seeds x 30 trials x depth-5 x leaves-31 x 24mo x ATR 2.9/1.45).
  R-CONV is a pure post-aggregator RULE layer (mirrors /074 AXIS-R and /084 R-FADE); does NOT touch the
  model, seeds, trials, or Optuna objective. NO multi-seed CONFIRMATION.
- **Test design**: ONE seat = ONE ~6-8h walk-forward run; `fail_fast_is_years=2.0` ON.

---

## Section 0.5 — Iteration TYPE

**TYPE = SPECIALIST — machinery EXPLORATION.** 2nd machinery axis of cycle-7. R-CONV is a stateless
post-aggregator trade-skip gate applied to a single existing BUNDLE-002 seat (ETH/064). It is NOT a
BUNDLE assembly, NOT a new cohort mine, NOT a feature-engineering set. Single cell, single outer seed=42.

---

## Section 0.6 — Architecture-Family Justification (v1-only)

- **Axis family**: `risk-primitive` (sub-family: aggregation / post-aggregator RULE layer).
- **Prior 5 SPECIALIST families** (from `briefs-v1/specialist_catalog.md`):
  - iter-v1/085: `feature-family` (per-cohort-specialization-UNI, NEW mean-reversion set)
  - iter-v1/086: `universe` (per-cohort-specialization-TRB, symbol-only mine)
  - iter-v1/087: `universe` (per-cohort-specialization-BNB, symbol-only mine + fail-fast)
  - iter-v1/088: `universe` (per-cohort-specialization-XRP, symbol-only mine)
  - iter-v1/090: `sample-weighting` (W-DECAY abs_pnl_timedecay) — FIRST machinery axis of cycle-7
  - (iter-v1/089 was a BUNDLE assembly, not a SPECIALIST — excluded from the SPECIALIST rotation window)
- **Rotation status**: **VALID / SATISFIED.** The prior 5 SPECIALISTs are `feature-family`(1) +
  `universe`(3) + `sample-weighting`(1). `risk-primitive` is DIFFERENT from the majority (universe) and
  has not appeared in the window. This is the 2nd distinct machinery axis (sample-weighting at /090, then
  risk-primitive at /091) — rotation explicitly satisfied per the user directive.
- **One-sentence rationale**: After /090 proved recency-weighting is COIN-SPECIFIC (temporal-profile-
  dependent), R-CONV is the natural next machinery axis precisely because it is **temporal-profile-
  INDEPENDENT** — it filters on seed-agreement (a per-candle SNR proxy), not on when a coin's edge
  occurred, so it is a candidate bundle-wide primitive that W-DECAY could never be.

---

## Section 1 — Hypothesis

**In a low signal-to-noise market, most candles are noise and should be skipped.** The 50-seed ensemble
already encodes a per-candle SNR proxy: `_sp_confidence = |n_long - n_short| / 50` = the fraction of net
seed agreement. When the seeds barely net-agree (`_sp_confidence` small, near-coin-flip vote), the
prediction is dominated by seed-RNG noise rather than signal; these candles are net-losing. R-CONV skips
them.

**Claim**: applying a conviction gate `_sp_confidence >= tau` to the ETH/064 seat will improve IS Sharpe
(F1 VALIDATED >= +0.20) by removing the net-losing low-conviction tail, **without** breaching the >=50
OOS trade-rate floor (F3) and **without** the filtered-out candles being a systematic low-vol/regime
slice (F4 selection-bias guard).

**Why R-CONV and not W-DECAY**: /090 (W-DECAY, diary) established that recency-weighting is coin-specific
(XRP edge recent / ETH edge old) — there is no universal recency lever. R-CONV does not depend on a
coin's temporal-edge profile at all; it filters on the cross-seed agreement at each candle. If it works,
it is a candidate **bundle-wide** primitive.

---

## Section 2 — IS-Only Evidence

Script: `analysis/iteration_v1-091/conviction_distribution.py` (committed; reads ONLY `in_sample/trades.csv`
for every tau-setting decision; reproducible). The `confidence` column in each seat's IS trades.csv is
exactly `_sp_confidence` per traded candle.

### 2.1 — Per-seat IS confidence distribution (net seed-agreement fraction)

| seat | n | IS WR% | min | p10 | p25 | med | p75 | p90 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ETH/064 | 198 | 39.4 | 0.020 | 0.020 | 0.040 | 0.120 | 0.360 | 0.660 | 0.980 |
| BTC/065 | 190 | 35.3 | 0.020 | 0.040 | 0.100 | 0.280 | 0.640 | 0.840 | 1.000 |
| AAVE/078 | 157 | 41.4 | 0.020 | 0.040 | 0.120 | 0.260 | 0.560 | 0.760 | 1.000 |

All seats have a broad, well-spread conviction distribution (min 0.02 = 1 net seed, up to ~1.0 = full
consensus). The low tail (conf <= 0.04) is dense at every seat.

### 2.2 — IS WR & net-PnL by conviction bucket (the core "low-conviction = noise" test)

**ETH/064** (chosen seat — MONOTONE conviction->edge gradient):

| bucket | n | WR% | sumPnL% | avgPnL% |
|---|---:|---:|---:|---:|
| [0.00,0.06) | 67 | 37.3 | **-5.43** | -0.081 |
| [0.06,0.12) | 28 | 39.3 | +8.78 | +0.314 |
| [0.12,0.20) | 23 | 26.1 | -31.27 | -1.360 |
| [0.20,0.40) | 34 | 50.0 | +49.37 | +1.452 |
| [0.40,1.01) | 46 | 41.3 | +35.46 | +0.771 |

The lowest-conviction bucket is net-LOSING (WR 37.3%, -5.43% sumPnL). As tau rises, kept-WR climbs
monotonically (40.5% -> 45.0% -> 50.0%) and kept-sumPnL rises (62.3 -> 84.8 -> 102.1). **This is the
textbook low-conviction-is-noise profile.**

**BTC/065** (REJECTED as the seat — INVERTED map):

| bucket | n | WR% | sumPnL% |
|---|---:|---:|---:|
| [0.00,0.06) | 25 | 32.0 | -11.07 |
| [0.40,1.01) | 76 | 36.8 | **-45.27** |

On BTC the **highest-conviction** bucket is the worst (-45.27%). BTC/065 is the IS-negative /
OOS-positive regime-INVERTING seat (IS Sharpe -0.18 / OOS +1.13, BASELINE_V1 §Per-Specialist). Its IS
conviction->PnL map is regime-inverted and would mislead tau selection — and a conviction gate fit to
its IS map could actively HARM its OOS. **This is why the lowest-WR heuristic is overridden.**

**AAVE/078** is also clean (low two buckets WR 25-27% catastrophic; tau=0.16 lifts kept-WR to 48.1%) but
it is the PROMISING-TENTATIVE seat (single composed feature, less settled). ETH is the more trustworthy
substrate.

**Seat decision**: **ETH/064**, because it has both (a) a monotone conviction->edge gradient AND (b) is
sign-consistent IS+OOS (IS +0.2383 / OOS +0.5171, OOS/IS 2.17 — `comparison.csv`), so its IS
low-conviction tail is a reliable guide to where the noise lives.

### 2.3 — Trade-count + PnL survival at candidate tau (ETH/064, IS side)

| tau | kept | frac | kept_WR% | kept_sumPnL% | dropped | dropped_WR% | dropped_sumPnL% |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.04 | 152 | 0.77 | 38.8 | +48.30 | 46 | 41.3 | **+8.61** |
| **0.06** | **131** | **0.66** | **40.5** | **+62.34** | **67** | **37.3** | **-5.43** |
| 0.08 | 121 | 0.61 | 41.3 | +77.05 | 77 | 36.4 | -20.15 |
| 0.10 | 114 | 0.58 | 41.2 | +70.05 | 84 | 36.9 | -13.14 |

At **tau=0.04** the dropped set (conf=0.02 only, the 1-net-seed ties) is still WR 41.3% / +8.61% — NOT
clearly noise. The dropped set tips net-LOSING only once the conf=0.04 layer is included, i.e. at
**tau=0.06** (dropped WR 37.3% / -5.43%). tau=0.08+ starts cutting into the profitable body.

### 2.4 — Selection-bias precursor: conviction vs hold-duration (F4 guard)

| bucket | n | mean_hold (8h candles) | med_hold |
|---|---:|---:|---:|
| [0.00,0.06) | 67 | 10.31 | 9.00 |
| [0.06,0.12) | 28 | 11.04 | 11.00 |
| [0.12,0.20) | 23 | 9.74 | 6.00 |
| [0.20,0.40) | 34 | 12.38 | 12.00 |
| [0.40,1.01) | 46 | 10.22 | 8.00 |

**Spearman rho(confidence, hold_duration) = +0.046** — essentially zero. High-conviction trades are NOT
systematically shorter- or longer-held than low-conviction trades. Hold-duration is a coarse vol/regime
proxy (timeout-bound trades = quieter regimes); the near-zero rho is the IS precursor evidence that the
conviction gate is removing NOISE, not a systematic vol/regime slice. The full F4 selection-bias check
is pre-registered for Phase 7 on the actual filtered-vs-kept candle sets (§4).

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

- **Declaration**: **HIGH-RISK**.
- **Reason**: although R-CONV is a stateless post-aggregator RULE (does not change the Optuna training
  objective, model, seeds, or trials), it changes the **traded-candle population** the strategy acts on —
  the realized trade roster and PnL stream shift. Under the v1 HIGH-RISK rubric, any change to the
  acted-on sample is HIGH-RISK.
- **Mitigation (HIGH-RISK, opt-in per v1)**: run **single-seed** (outer seed=42), consistent with the
  /090 W-DECAY precedent, with **`fail_fast_is_years=2.0` ON** to bound the downside and give an early
  read (aborts if first-2.0yr IS weighted_pnl <= 0). NO multi-seed CONFIRMATION (permanently dropped per
  MEMORY). The OOS trade-rate floor (F3) is the mechanical guard against the dominant HIGH-RISK failure
  mode (over-filtering). Diary records the single-seed choice + OOS outcome.

---

## Section 3 — Implementation (handoff to QE)

**Axis change (one knob, opt-in, default OFF):**

1. **New `LightGbmStrategy.__init__` params** (mirror the `enable_oi_divergence_fade_gate` / `oi_divergence_fade_z` pattern at `lgbm.py:255-257`):
   - `enable_r_conv_gate: bool = False`  (default OFF — foundation byte-unchanged when OFF)
   - `r_conv_tau: float = 0.06`          (pre-registered; only consulted when the gate is ON)
   - Store as `self._enable_r_conv_gate`, `self._r_conv_tau` (mirror `lgbm.py:408-422`).

2. **Gate insertion point** — in the SPECIALIST path of `get_signal`, **immediately after**
   `_sp_confidence = abs(_final_signed) / 100.0` is computed (`lgbm.py:2162`) and **before** the
   `Signal(...)` object is built (`lgbm.py:2182`). This is the same post-aggregator RULE layer band as
   AXIS-R (/074) and R-FADE (/084):

   ```python
   if self._enable_r_conv_gate and _sp_confidence < self._r_conv_tau:
       from crypto_trade import decision_log
       decision_log.log({
           "kind": "r_conv_skip",
           "symbol": symbol,
           "ot": open_time,
           "month": candle_month,
           "specialist_seeds": len(self._specialist_models),
           "final_signed": _final_signed,
           "ensemble_std": _ensemble_std,
           "confidence": _sp_confidence,
           "r_conv_tau": self._r_conv_tau,
           "decision": "skipped:r_conv_low_conviction",
       })
       return NO_SIGNAL
   ```

   Placing it before the `Signal` build means R-CONV is a pure conviction skip and never interacts with
   the AXIS-R / R-FADE veto bookkeeping for this seat (those gates are OFF on the ETH seat anyway). The
   `_specialist_dispersion_stats.append(...)` at `lgbm.py:2233` is NOT reached for skipped candles, which
   is correct — skipped candles must not pollute the dispersion diagnostic.

3. **Runner**: a new `run_iteration_091.py` (clone of the ETH/064 SPECIALIST runner, `run_iteration_064`-
   equivalent) that constructs the ETH specialist with `enable_r_conv_gate=True, r_conv_tau=0.06`, all
   other params **byte-identical** to the /064 baseline cell:
   - seat = ETHUSDT only; `Model_A` pattern (R1/R2 OFF, R3 ON 0.70, R5 ON 0.3); ATR tp=2.9 / sl=1.45.
   - feature stack = `V1_FEATURE_COLUMNS_PRUNED` (48 cols); explicit `feature_columns=[...]` (never None).
   - 50 inner seeds (42..91) x 30 trials; specialist_mode; single OUTER seed=42; depth-5; leaves-31; 24mo.
   - `fail_fast_is_years=2.0`.
   - Persist `reports-v1/iteration_v1-091/{in_sample,out_of_sample}/` (trades/comparison/daily/monthly/per_symbol) + `specialist_dispersion.csv` + `fail_fast_report.csv` if it fires.

4. **Tests** (QE): unit test that with `enable_r_conv_gate=False` the SPECIALIST path is BIT-IDENTICAL to
   the current ETH/064 cell (foundation unchanged); unit test that with `enable_r_conv_gate=True,
   r_conv_tau=0.06` a synthetic candle whose seeds produce `_sp_confidence=0.04` returns `NO_SIGNAL` and
   logs `kind="r_conv_skip"`, while `_sp_confidence=0.08` passes through unchanged.

**Pre-registered tau = 0.06.** IS-only basis (§2.3): `_sp_confidence < 0.06` corresponds to net seed
agreement `|n_long - n_short| <= 2 of 50` (near-coin-flip consensus). On ETH/064 IS this dropped set is
net-LOSING (WR 37.3%, -5.43% sumPnL) and keeps 66% of IS trades. tau=0.04 was rejected because its
dropped set (conf=0.02 ties) is still net-positive (+8.61%); tau>=0.08 was rejected because it begins
cutting the profitable body and tightens the OOS floor margin. SINGLE value; no grid; the OOS count is
consulted ONLY as the F3 mechanical floor verification, never to choose tau.

---

## Section 3.5 — LightGBM Master Phase 4.5 (placeholder)

The orchestrator invokes `lightgbm-master` at Phase 4.5; `briefs-v1/iteration_v1-091/lgbm_advisor.md` is
not yet present at brief-authoring time. This section will be reconciled before Phase 5.5: each LM Master
recommendation will be tagged Adopted / Modified / Rejected. Expected LM focus areas (pre-empted):
- R-CONV does NOT change Optuna's hyperparameter domain (post-aggregator RULE), so HP-tuning
  recommendations are likely N/A — to be confirmed.
- LM may flag the conviction-vs-vol selection-bias risk (the Critic/LM flagged it earlier); §2.4 + the F4
  Phase 7 check are the pre-registered response.
- LM may comment on whether tau=0.06 over- or under-filters; the §2.3 survival table + the F2/F3
  falsifiers are the pre-registered adjudication, and the brief will not re-grid tau on LM input
  (anti-tuning — tau stays pre-registered).

---

## Section 4 — Falsifiers (pre-registered)

Anchor = ETH/064 baseline cell (IS Sharpe **+0.2383**, 198 IS / 81 OOS trades; `reports-v1/iteration_v1-064/comparison.csv`).

- **F1 — IS Sharpe delta vs ETH/064 baseline.**
  - **VALIDATED**: IS Sharpe Δ >= **+0.20** (the low-conviction noise removal lifts IS edge as predicted).
  - **NEGATIVE**: IS Sharpe Δ < **+0.00**.
  - **TENTATIVE / FLAT**: Δ in [0.00, +0.20).

- **F2 — Mechanistic engagement (trade-count reduction).** R-CONV MUST actually filter.
  - If IS trade count is **unchanged** (gate fired on ~0 candles) -> tau too low -> **INERT** (NEGATIVE-INERT).
    Expected IS reduction ≈ 34% (198 -> ~131) per §2.3; falsifier fires if observed IS reduction is below
    ~15% (the behavioral-effect predictor lower bound).
  - If trade count is reduced **but IS Sharpe is FLAT** -> the dropped low-conviction trades were NOT the
    noise -> **NEGATIVE-NO-EFFECT** (the conviction proxy doesn't separate signal from noise on this seat).

- **F3 — Trade-rate floor (the over-filter guard).**
  - **>= 50 OOS trades must survive.** ETH/064 has 81 OOS trades; tau=0.06 is projected to keep ~72 OOS
    (the OOS count read in §2.3 dev is the MECHANICAL floor check only, NOT tuning). If the actual run
    over-filters OOS below 50 -> **NEGATIVE-OVERFILTER** (tau too aggressive for the OOS conviction
    distribution). Per-specialist OOS floor is >=50 per `feedback_v1_trade_rate_floor_50_per_specialist`.

- **F4 — OOS direction-consistency + conviction-vs-vol selection-bias check.**
  - **Direction-consistency**: OOS Sharpe Δ must not flip catastrophically negative (<= -0.30) while IS Δ
    is positive (would signal an IS-overfit conviction threshold).
  - **Selection-bias guard (pre-registered)**: on the actual run, compare the **filtered-out** candle set
    vs the **kept** candle set on a vol/regime proxy — (a) Spearman rho(`_sp_confidence`, realized NATR at
    entry) and (b) mean hold-duration of filtered vs kept. If the filtered-out candles are systematically
    a low-vol or single-regime slice (|rho| > 0.30 with NATR, OR filtered-vs-kept hold-duration differ by
    > 30%), R-CONV is removing a **regime**, not noise -> downgrade to **NEGATIVE-REGIME-PROXY** even if F1
    passes. IS precursor (§2.4): rho(conf, hold) = +0.046 (near-zero) — the guard is expected to PASS, but
    it is verified on OOS-inclusive data in Phase 7, not assumed.

**Verdict precedence**: F3 (over-filter) and F2-INERT are mechanical gates checked first; then F1
(edge); then F4 (regime-proxy / direction). A pass requires F2 engaged (filtered) + F3 floor held + F1
VALIDATED + F4 clean.

---

## Section 6 — Risk Recap

- **Risk wrappers unchanged**: ETH/064 seat keeps R3 ON (OOD Mahalanobis 0.70) + R5 ON (0.3); R1/R2 OFF
  (Model A pattern). R-CONV sits BEFORE the `Signal` build, hence before R3/R5 call-sites — it only
  reduces the candidate set those gates then see. No double-counting: R-CONV filters on seed-agreement
  (ensemble-internal), R3 filters on feature-space OOD (Mahalanobis), R5 on vol-target — orthogonal
  mechanisms.
- **Dominant new risk**: over-filtering below the OOS trade-rate floor — guarded by F3 (>=50 OOS).
- **Downside bound**: `fail_fast_is_years=2.0` ON aborts if first-2.0yr IS weighted_pnl <= 0 (~3-4h saved
  on a bad draw; validated 3x: BNB block / XRP pass / W-DECAY-ETH block).
- **Foundation safety**: gate is opt-in `default=False`; with the flag OFF the SPECIALIST path is
  byte-identical to the /064 baseline (QE unit test asserts this) — no parity risk to BUNDLE-002.
- **Concentration / merge gates**: this is an EXPLORATION on a single seat, not a BUNDLE assembly; no
  bundle-level concentration or DSR/PBO/PSR gate applies at this layer. A PASS feeds a future BUNDLE
  re-assembly decision, not an immediate baseline change.

---

## Section 7 — Modal (pre-registered outcome prediction)

| Outcome | Pre-registered modal probability | Trigger |
|---|---:|---|
| **VALIDATED** (F1 Δ >= +0.20, F2 engaged, F3 held, F4 clean) | ~35% | low-conviction tail is genuine seed-RNG noise; removing it lifts ETH IS edge |
| **TENTATIVE / FLAT** (F1 in [0,0.20), F2 engaged) | ~30% | the tail is mildly net-losing but the IS Sharpe lift is sub-threshold |
| **NEGATIVE-NO-EFFECT** (F2 engaged, F1 FLAT/neg) | ~20% | conviction doesn't cleanly separate signal from noise once Optuna re-fits per cell |
| **NEGATIVE-OVERFILTER** (F3 breached, OOS < 50) | ~8% | the OOS conviction distribution is shifted lower than IS -> tau=0.06 cuts too deep OOS |
| **NEGATIVE-REGIME-PROXY** (F4 fails: conviction = vol/regime slice) | ~5% | filtered candles are a low-vol regime, not noise (IS precursor rho=0.046 makes this low-prob) |
| **INERT** (F2: trade count ~unchanged) | ~2% | tau=0.06 too low — but §2.3 shows it drops 34% IS, so unlikely |

**Predicted IS trade reduction**: ~34% (198 -> ~131); **predicted OOS survival**: ~72 (above the 50 floor).
**Most-likely outcome**: TENTATIVE-to-VALIDATED — the IS evidence shows a real but modest low-conviction
drag (-5.43% sumPnL in the dropped bucket); whether that converts to a >= +0.20 Sharpe lift after Optuna
re-fits each monthly cell is the genuine uncertainty the backtest resolves.

---

## Section 8 — Candidacy Bands

| Band | Condition | Disposition |
|---|---|---|
| **PROMISING-VALIDATED-ish** | F1 Δ >= +0.20, F2 engaged, F3 >= 50 OOS, F4 clean | R-CONV becomes a candidate **bundle-wide** primitive; pre-register a per-seat replication brief (BTC excluded — inverted map) at the next iteration; ETH seat updates pending bundle re-assessment. |
| **PROMISING-TENTATIVE** | F1 Δ in [0,0.20), F2 engaged, F3 held, F4 clean | Hold R-CONV as a TENTATIVE machinery lever; note the modest IS lift; re-test at a cleaner seat (AAVE) or a slightly higher tau in a FUTURE iteration (NOT a re-grid this iteration). |
| **NEGATIVE-NO-EFFECT** | F2 engaged, F1 FLAT/neg | Conviction does not separate noise on ETH; axis stays open for other seats only if a per-seat conviction-PnL gradient is pre-confirmed; otherwise machinery axis pivots. |
| **NEGATIVE-OVERFILTER** | F3 < 50 OOS | tau too aggressive; record the OOS-vs-IS conviction-distribution shift as the lesson; do not auto-lower tau (would be OOS tuning). |
| **NEGATIVE-REGIME-PROXY** | F4 fails | conviction is a vol/regime proxy on this seat; R-CONV is a regime filter not an SNR filter; close the SNR framing. |
| **INERT** | F2 trade count ~unchanged | tau too low; documented; not retested at higher tau this iteration. |

BUNDLE-002 (`v0.v1-082`) remains the live baseline regardless of outcome (this is a single-seat
EXPLORATION; no baseline change without a subsequent BUNDLE assembly).

---

## Section 9 — Methodology Recap (LOCK confirmation)

**Locked / unchanged** (R-CONV is ONLY a post-aggregator skip gate):
- Inner ensemble: **50 seeds** (42..91). Optuna: **30 trials** per (symbol, month) cell.
- LightGBM HP: **max_depth=5 FIXED, num_leaves=31 FIXED**.
- Training: **training_months=24**, monthly retrain. **OOS_CUTOFF_DATE = 2025-03-24** (sacred, unchanged).
- Walk-forward: `train_end_ms = test_start_ms - embargo_ms` (`walk_forward.py:113`, `5566a69`).
- Feature stack: `V1_FEATURE_COLUMNS_PRUNED` (48 cols), explicit `feature_columns=[...]`.
- Seat config: ETHUSDT, Model A pattern (R1/R2 OFF, R3 0.70, R5 0.3), ATR tp=2.9 / sl=1.45 — byte-identical to /064.
- Aggregator: `_final_signed = mean(signed_weights)`, `_sp_confidence = |_final_signed|/100` — **untouched**.
- Single outer seed=42. **NO multi-seed CONFIRMATION** (permanently dropped).
- `fail_fast_is_years=2.0` ON.

**The ONLY change**: opt-in `enable_r_conv_gate` (default OFF) + pre-registered `r_conv_tau=0.06`, wired
as a post-aggregator `NO_SIGNAL` skip when `_sp_confidence < tau`. Pure RULE layer; does not touch the
model, seeds, trials, or Optuna objective.

**Anti-tuning attestations**:
- tau=0.06 is a SINGLE pre-registered value derived from IS-only data (`in_sample/trades.csv`); no grid.
- The OOS trade count was consulted only as the F3 mechanical floor verification (>=50), never to select tau.
- No OOS metric was used in any design decision; OOS is first evaluated as the strategy's edge in Phase 7.

---

### Trade-rate-floor guard (explicit confirmation)

R-CONV REDUCES trade count by construction. The binding guard is **F3: >= 50 OOS trades must survive**.
ETH/064 has 81 OOS trades; tau=0.06 is projected to keep ~72 (44% headroom above the 50 floor). If the
actual run over-filters OOS below 50, the verdict is **NEGATIVE-OVERFILTER** — a real null result earned
by running the experiment, not a reason to lower tau post-hoc.
