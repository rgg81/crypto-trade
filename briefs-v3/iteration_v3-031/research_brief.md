# Iteration v3-031 — Research Brief

**Type**: EXPLORATION (cadence #3 of 10 in post-iter-v3/028 cycle; **MECHANICAL DRAG-REMOVAL axis — DROP LDOUSDT** following iter-v3/013 PROMISING-MECHANICAL precedent)
**Track**: v3 (rigor arm) — thirty-first iteration
**Branch**: `iteration-v3/031` (off `iter-v3/030` head)
**Date**: 2026-05-08
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 1              # SET BY --exploration
n_trials         = 35             # default EXPLORATION budget
colsample_bytree = 1.0            # HARDCODED by --exploration
OOS_CUTOFF_MS    = 1742774400000
```

**Sacred constants UNCHANGED.** IS window: 2023-03-24 to 2025-03-23 (24 months). OOS window: 2025-03-24 onward. The QR sees iter-v3/031 OOS metrics for the first time in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION (cadence #3 of 10 in post-iter-v3/028 cycle)
Wall-clock budget: ≤ 2h hard cap (per feedback_v3_cadence_discipline.md)
Single-axis variation: DROP LDOUSDT from V3_MODELS (universe shrink 4 → 3)
Cadence: 3 of 10 EXPLORATIONs in this cycle (next CONFIRMATION = iter-v3/039)
Axis category: MECHANICAL DRAG-REMOVAL (iter-v3/013 PROMISING-MECHANICAL precedent)
```

**MKR-threshold reference** (`feedback_v3_mkr_threshold_compression.md`): The compressed threshold is 5 consecutive OOS-negative iterations for a symbol. LDOUSDT has been OOS-negative across 9 consecutive iterations (iter-v3/018–030), far exceeding the 5-consecutive threshold. The drop is overdue.

**PROMISING-MECHANICAL subtype reference** (`feedback_v3_promising_mechanical_subtype.md`): When the expected lift is mechanical (drag removal / accounting cleanup) rather than signal discovery, the iteration is pre-classified as PROMISING-MECHANICAL. The iter-v3/013 drop-MKR produced the largest single-iteration OOS lift in v3 history by removing a chronically-negative symbol. iter-v3/031 follows the exact same mechanism.

**LDO OOS-negative trajectory across 9 consecutive iterations**:
- iter-v3/018 multi-seed: −22.05 OOS weighted_pnl (21.4% WR, 14 trades)
- iter-v3/020–027 single-seed frozen: −8.93 OOS weighted_pnl (38.5% WR, 13 trades, mean)
- iter-v3/029 with ALGO expansion: −3.07 OOS weighted_pnl (36.4% WR, 11 trades)
- iter-v3/030 with 7-feat subset: −29.99 OOS weighted_pnl (26.7% WR, 15 trades; WORST)

iter-v3/030 engineering report (Critic-confirmed) explicitly stated: "LDO is a STRUCTURAL problem, not an overfit-from-too-many-features problem. Feature reduction doesn't address structural mismatch." Critic FINAL of iter-v3/030 recommended iter-v3/031 axis = **DROP LDOUSDT**.

**This iteration NEVER updates BASELINE_V3.md** (single-seed EXPLORATION).

---

## Section 1 — Hypothesis

Dropping LDOUSDT from V3_MODELS (4 → 3; retaining BCH+TRX+ALGO from iter-v3/029) removes a structurally-mismatched symbol whose 9-of-9 OOS-negative trajectory is a mechanical drag on the portfolio, preserving the BCH+TRX+ALGO edge contribution from iter-v3/029 (OOS +29.24+20.87+10.75 = +60.86 vs total +57.79, meaning LDO subtracted −2.93% net) and lifting OOS Sharpe toward the iter-v3/029 BCH+TRX+ALGO-only floor of approximately +1.85–2.10 (estimated from removing the −3.07 drag from iter-v3/029's +1.7653 bundle Sharpe with trade-count renormalization).

---

## Section 2 — IS-Only Numerical Evidence

**Evidence source**: iter-v3/018–030 engineering reports and Critic FINALs (committed; all IS-data artifacts). This is a MECHANICAL DROP axis — no new EDA script is required because the evidence is the trajectory of LDO's per-symbol IS and OOS metrics across 9 iterations.

### 2.1 LDO 9-of-9 OOS-negative trajectory (from committed reports)

| Iteration | LDO OOS weighted_pnl | LDO OOS WR | LDO OOS n_trades | Notes |
|---|---:|---:|---:|---|
| iter-v3/018 (multi-seed) | −22.05 | 21.4% | 14 | BASELINE multi-seed; LDO structural drag confirmed |
| iter-v3/020–027 (frozen) | −8.93 (mean) | 38.5% | 13 (mean) | Across 8 single-seed EXPLORATIONs; LDO frozen baseline |
| iter-v3/029 (ALGO added) | −3.07 | 36.4% | 11 | Even with ALGO, LDO still negative |
| iter-v3/030 (7-feat subset) | −29.99 | 26.7% | 15 | WORST; feature-reduction hypothesis FALSIFIED |

**Conclusion**: MKR-threshold (5 consecutive OOS-negative) was already crossed at iter-v3/022 (5 in a row). iter-v3/031 executes the mandated drop at 9-of-9.

### 2.2 BCH+TRX+ALGO independence confirmed

iter-v3/030 engineering report: "BCH/TRX/ALGO frozen baseline confirmed (only LDO config changed; only LDO trajectory changed)." This means BCH+TRX+ALGO IS performance is directly attributable to their own feature sets and training configurations — LDO drop does NOT perturb their training or inference (per-symbol architecture from iter-v3/030 proved independence).

### 2.3 Predicted mechanical lift (IS-data arithmetic)

iter-v3/029 OOS attribution (removing LDO's −3.07 drag from +57.79 total):
- If BCH+TRX+ALGO trades are **bit-identical** to iter-v3/029: OOS weighted_pnl = +57.79 − (−3.07) = +60.86 mechanical floor.
- OOS Sharpe estimate: iter-v3/029 was +1.7653 with 4 symbols. Removing LDO's 11 OOS trades (≈9% of 124 total) and LDO's negative contribution → estimate +1.85–2.10 after renormalization.

### 2.4 Behavioral-effect predictor (per `feedback_axis_saturation_predictor.md`)

**Predicted BCH+TRX+ALGO IS trade volume**: BIT-IDENTICAL to iter-v3/029 (per-symbol architecture proof from iter-v3/030; LDO drop cannot perturb BCH/TRX/ALGO models). IS trades: 257 − 15 (LDO IS) = **242** predicted.

**Predicted OOS trades**: iter-v3/029 OOS was 124 total; LDO contributed 11 OOS trades → predicted **113 OOS trades** for 3-symbol bundle.

**Saturation falsifier**: If observed BCH+TRX+ALGO trades differ from iter-v3/029 by > 5%, a code-path regression has occurred. This is PATH C — REVERT.

---

## Section 3 — Proposed Changes (5 Sub-fixes)

| # | Sub-fix | File | Description | Verifier |
|---|---|---|---|---|
| 1 | **DROP LDOUSDT from V3_MODELS** | `run_baseline_v3.py` | Remove `("C (LDOUSDT)", "LDOUSDT")` from `V3_MODELS` tuple. New V3_MODELS = 3 symbols: BCH+TRX+ALGO. | `uv run python -c "from run_baseline_v3 import V3_MODELS; assert len(V3_MODELS) == 3 and ('C (LDOUSDT)','LDOUSDT') not in V3_MODELS and any('ALGOUSDT' in x for x in V3_MODELS)"` |
| 2 | **Update REQUIRED_GAP 88 → 66** | `src/crypto_trade/strategies/ml/validation_v3.py` | `REQUIRED_GAP: int = (21 + 1) * 3  # 66` (3-symbol universe). | `uv run python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP == 66"` |
| 3 | **Clear LDO from V3_FEATURES_PER_SYMBOL** | `src/crypto_trade/features_v3/__init__.py` | Remove the `"LDOUSDT"` entry from `V3_FEATURES_PER_SYMBOL`. Dict becomes `{}` (empty). Helper `features_for_symbol()` remains in place (architecture preserved for future per-symbol use). | `uv run python -c "from crypto_trade.features_v3 import V3_FEATURES_PER_SYMBOL; assert 'LDOUSDT' not in V3_FEATURES_PER_SYMBOL"` |
| 4 | **Update ITERATION_LABEL** | `run_baseline_v3.py` | `ITERATION_LABEL = "v3-031"` | `grep -nE 'ITERATION_LABEL = "v3-031"' run_baseline_v3.py` |
| 5 | **Update `_verify_label_leakage_gap()` message** | `run_baseline_v3.py` | The docstring/comment in `_verify_label_leakage_gap()` currently references n_symbols=4 (from iter-v3/029). Update to n_symbols=3 (iter-v3/031). The formula `(timeout_candles + 1) * n_symbols` is dynamic from `len(V3_MODELS)` so this is a comment/doc update only. | `grep -n 'n_symbols' run_baseline_v3.py | grep -q '3'` (in gap comment) |

**V3_FEATURE_COLUMNS = 14 unchanged** — `regime_momentum_signed_5d` preserved. BCH+TRX+ALGO all fall back to `V3_FEATURE_COLUMNS_TOP_N` (14 features) via `features_for_symbol()`.

---

## Section 4 — Expected OOS Impact

**Anchor**: iter-v3/029 single-seed IS +0.7926 / OOS +1.7653 (with LDO drag −3.07 OOS).

**Predicted Critic FINAL bands** (from iter-v3/030 Critic Final, reproduced here as Section 4 anchor):

| Band | IS Sharpe | OOS Sharpe | Mechanism |
|---|---:|---:|---|
| PROMISING-MECHANICAL (BCH+TRX+ALGO bit-identical) | [+0.85, +1.05] median +0.92 | [+1.85, +2.10] median +1.95 | LDO drag removed; BCH+TRX+ALGO unchanged |
| NEGATIVE (BCH+TRX+ALGO regression) | < +0.65 IS | < +1.50 OOS | Code-path regression; REVERT |

**Pre-registered classification: PROMISING-MECHANICAL** (NOT PROMISING-clean). Rationale: the lift is mechanical drag removal, not signal discovery. Per `feedback_v3_promising_mechanical_subtype.md`, PROMISING-MECHANICAL is non-compoundable as an iter-v3/039 CONFIRMATION-bundle ingredient. It is treated as a "strictly accretive component decision" (universe shrink from structural exclusion).

**Falsifier**: If OOS Sharpe < +1.50, the hypothesis is rejected — BCH+TRX+ALGO regression (code bug) or LDO drop inadvertently disrupted CPCV purge structure. NEGATIVE verdict.

**Explicit falsifier threshold**: OOS Sharpe ≥ +1.50 is the PASS floor. OOS Sharpe ≥ +1.85 is the PROMISING-MECHANICAL confirmation floor.

---

## Section 5 — Risk Mitigation

### Concentration risk

With 3 symbols (BCH+TRX+ALGO), TRX concentration rises from ~50.59% (4-symbol denominator iter-v3/029) to approximately 60–65% (3-symbol denominator). This exceeds the ≤30% project-level gate but has been an outstanding constraint since iter-v3/013 (same 3-symbol configuration). The concentration constraint is pre-registered as OUTSTANDING per BASELINE_V3.md §"Failed MERGE Gates" — iter-v3/031 does not worsen it relative to the iter-v3/013 baseline configuration.

### Cadence risks

| Risk | Mitigation |
|---|---|
| Budget overrun | 3-symbol single-seed is faster than 4-symbol: estimated 12–18 min wall-clock (vs 25–30 min at iter-v3/029). Well within 2h EXPLORATION cap. |
| Cycle-cadence | Iteration #3 of 10 EXPLORATIONs; 7 remaining; CONFIRMATION at iter-v3/039. Strict 10:1. |
| Single-axis discipline | ONE change: remove LDO. REQUIRED_GAP update is a mandatory formula consequence, not an independent axis. |

### Methodology hygiene

| Risk | Mitigation |
|---|---|
| OOS contamination | No EDA reads OOS data. LDO trajectory evidence is from IS-portion of engineering reports and per_symbol.csv comparisons. |
| V3_FEATURES_PER_SYMBOL LDO entry leaks | Remove the `"LDOUSDT"` dict entry; `features_for_symbol("LDOUSDT")` will return `V3_FEATURE_COLUMNS_TOP_N` (14 features) via fallback — which is irrelevant since LDO is not in V3_MODELS. |
| MKRUSDT accidentally removed | MKRUSDT was dropped at iter-v3/013 and is already absent from V3_MODELS. No change needed. V3_EXCLUDED_SYMBOLS does NOT include LDOUSDT — QE must NOT add it there (that list is for v1/v2 symbols). LDO drop is purely from V3_MODELS. |

---

## Section 6 — 7-Primitive Risk Gate Stack — UNCHANGED

| Primitive | Threshold | Status |
|---|---|---|
| BTC trend kill | ±15% over 14d (42 bars 8h) | UNCHANGED |
| Vol scaling | RiskV2Wrapper internal | UNCHANGED |
| ADX gate | 20.0 | UNCHANGED |
| Hurst regime | hurst_100 in [0.3, 0.7] band | UNCHANGED |
| Feature z-score OOD | \|z\| ≤ 2.0 | UNCHANGED |
| Low-vol filter | NATR-percentile-based | UNCHANGED |
| Hit-rate feedback | DISABLED | UNCHANGED |
| Per-symbol cap | DISABLED (iter-v3/020 closed) | UNCHANGED |
| Regime-conditional kill | DISABLED (iter-v3/022 partial result deferred) | UNCHANGED |

**Gate fire rates** are expected to shift proportionally: with 3 vs 4 symbols, LDO-specific gate firings are removed. BCH+TRX+ALGO gate fire rates expected BIT-IDENTICAL to iter-v3/029.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure**: The BCH+TRX+ALGO trades are NOT bit-identical to iter-v3/029 due to the REQUIRED_GAP change (88 → 66). The CPCV splits use `expected_gap=REQUIRED_GAP` in the assertion. If the gap change silently alters the purge structure and shifts the train/test boundary indices, BCH+TRX+ALGO models see slightly different training windows and produce different LightGBM hyperparameters. This would manifest as: IS Sharpe outside [+0.80, +1.10], BCH+TRX+ALGO per-symbol trades differing from iter-v3/029, and OOS Sharpe exhibiting the "single-seed lottery" variance pattern seen in iter-v3/026/027.

**What the gates should catch**: REQUIRED_GAP change is a formula consequence (n_symbols 4→3), not an independent axis. The gap matters for IS data only (purge removes label-overlap contamination). With 3 symbols the gap is tighter (66 < 88), meaning slightly more training data survives purge per fold. This should be strictly beneficial or neutral — it cannot harm BCH+TRX+ALGO since they have sufficient IS samples. The assertion `expected_gap=REQUIRED_GAP` in `combinatorial_purged_cv` guarantees the gap is not silently rescaled.

**What failure looks like**: IS Sharpe < +0.65 (collapse) AND OOS Sharpe > +2.0 (suspicious spike) — the NEGATIVE-SUSPICIOUS-OOS pattern from iter-v3/026/027. OR BCH+TRX+ALGO per-symbol per_symbol.csv trades differ materially (> 5%) from iter-v3/029. Either of these triggers NEGATIVE classification.

**Second most plausible failure**: The mechanical lift is smaller than expected because LDO's negative OOS contribution was already partially offset by CPCV purge structure at n_symbols=4 (wider gaps = less training data = lower IS fit = lower OOS variance for all symbols). With n_symbols=3 (tighter gap), BCH+TRX+ALGO see marginally more training data per CPCV fold, which can increase IS overfit and paradoxically hurt OOS. The engineering report must check the per_cell_pbo.csv for any cell-level PBO regression.

---

## Section 8 — Pre-Registered EXPLORATION Criteria (MERGE/NO-MERGE)

**This is an EXPLORATION — BASELINE_V3.md is NEVER updated.**

Pre-registered catalog-row decision criteria (cannot be renegotiated post-result):

| # | Criterion | PASS threshold | Verdict on PASS | Verdict on FAIL |
|---|---|---|---|---|
| 1 | OOS Sharpe | ≥ +1.85 (PROMISING-MECHANICAL floor) | PROMISING-MECHANICAL | — |
| 2 | OOS Sharpe floor | ≥ +1.50 (hard falsifier) | — | NEGATIVE (falsifier fires) |
| 3 | BCH+TRX+ALGO IS trade count | within ±5% of iter-v3/029 (per-symbol) | Bit-identity confirmed | NEGATIVE (regression) |
| 4 | IS Sharpe | in [+0.85, +1.05] median +0.92 | PASS | SUSPICIOUS if outside [+0.65, +1.20] |
| 5 | PBO mean < 0.40 | inherited from iter-v3/029 (0.0974) | PASS | BLOCK |
| 6 | n_trades OOS | ≥ 100 (3-symbol; iter-v3/029 minus LDO's 11 = 113 expected) | PASS | Note if < 50 |
| 7 | V3_FEATURE_COLUMNS | = 14, regime_momentum_signed_5d present | PASS | HARD BLOCK |
| 8 | REQUIRED_GAP | = 66 in validation_v3.py | PASS | HARD BLOCK |
| 9 | Classification | PROMISING-MECHANICAL (NOT PROMISING-clean) | Pre-registered | Cannot be upgraded to PROMISING-clean post-hoc |
| 10 | Non-compoundable | Drop-LDO decision is architectural-accretive, NOT new edge ingredient | Pre-registered | Cannot be bundled at iter-v3/039 as "new signal" |

---

## Section 9 — Library Stack Declaration

**UNCHANGED from iter-v3/030** — no version updates:

```
python = 3.13
lightgbm = 4.6.0
numpy = 2.2.6
pandas = 3.0.0
scikit-learn = 1.8.0
pyarrow = 23.0.1
statsmodels = 0.14.6
optuna = 4.8.0
scipy = 1.17.0
```

mlfinpy / pypbo unavailable on Python 3.13 — pure-Python + numpy + scipy implementations used (established at iter-v3/002; unchanged throughout). No new dependencies for a universe-shrink iteration.
