# iter-v3/128 Research Brief — Cycle-7 EXPLORATION #7 — WILD axis: 6-symbol sector-pure L1 universe at 8h with rolling-endpoint methodology fix (BCH/LDO/TRX → ATOM+RUNE+AVAX+HBAR+ICP+ALGO)

**Axis**: WHOLESALE V3_MODELS replacement BCH/LDO/TRX → **ATOMUSDT + RUNEUSDT + AVAXUSDT + HBARUSDT + ICPUSDT + ALGOUSDT**. Cardinality 3→6 expansion + sector-pure L1 composition. All other architecture bit-identical to /121: 14-feature V3_FEATURE_COLUMNS_TOP_N, +2/-1 ATR triple-barrier K=21, /116 no_confirm (trigger_atr=0.50, k_candles=4), 7-gate RiskV2, ENSEMBLE_SIZE=3 (EXPLORATION), n_trials=35. /127 per-symbol drawdown brake REVERTED to disabled (axis CLOSED at /127). REQUIRED_GAP grows 66 → 132 = (21+1)×6.

**Lineage discipline**: First cycle-7 EXPLORATION under the **WILD axis creativity HARD MANDATE** per `feedback_v3_qr_axis_creativity_mandate.md` (2026-05-21 user push-back). The mandate explicitly rejects the cycle-7 "axis exhausted" narrative. Under LIFTED constraints (any non-v1/v2/MKR symbol; any candle frequency), the unexplored search space is COMBINATORIALLY MASSIVE. The brief MUST:
1. Brainstorm 5+ WILD candidates (DONE — `analysis/iteration_v3-128/synthesis.md`)
2. Combine multiple structural levers (DONE — NEW universe × NEW cardinality × sector-pure composition × rolling-endpoint methodology fix)
3. Reject the "axis exhausted" narrative (DONE — the universe-substitution axis at cardinality 3 is closed by 8 prior NEGATIVEs; cardinality-expansion under LIFTED constraints has NEVER been tested with sector-pure composition)
4. Bake the rolling-endpoint methodology fix INTO the EDA (DONE — `analysis/iteration_v3-128/eda.py` computes AUC + importance rank at 3 IS endpoint slices: 2023-Q1, 2024-Q1, 2025-Q1)

NEW-feature axes are FORBIDDEN at /127+ per `feedback_v3_eda_methodology_falsified.md` (the methodology was FALSIFIED at /126 3-occurrence pattern). /128 is a UNIVERSE axis (NOT a NEW-feature axis) — the FORBIDDEN ban does NOT apply.

**Cycle**: 7 EXPLORATION slot **#7 of 10**. Cycle-7 catalog state at /127 closeout: 6/6 NEGATIVE (5 NEGATIVE-catastrophic, 1 NEGATIVE-INERT). /128 is slot 7/10 under LIFTED constraints regime + WILD-mandate regime.

**Anchor (per-criterion annotation)**: PUBLIC = /121 multi-seed CONFIRMATION-MERGE BASELINE (IS monthly Sharpe **+1.3108** / OOS monthly Sharpe **+0.9682**). ADJUSTED = /121 architecturally-adjusted EXPLORATION-mode estimate (IS ≈ +1.06 / OOS ≈ +0.85) per `feedback_v3_dsr_mode_artifact.md` 3-seed-vs-10-seed proba-averaging compression factor. **Note**: anchor comparison is FRAUGHT under wholesale universe substitution — the /121 anchor is BCH/LDO/TRX-specific. Per /125 closeout finding ("cohort-shaped architecture"), comparison against the BCH/LDO/TRX anchor on a different universe measures the COMPOUND change (universe + per-symbol Optuna re-convergence). Section 8 falsifier evaluation uses the PUBLIC anchor as the comparison reference; the comparison is structurally appropriate for GO/NO-GO at the universe-axis level.

---

## Section 0 — Data Split declaration

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are UNCHANGED. Sacred constants immutable.

- **IS window**: 8h candle stream from per-symbol earliest 8h candle close through `OOS_CUTOFF_DATE = 2025-03-24` (exclusive).
  - ATOMUSDT earliest IS: 2020-02-07
  - RUNEUSDT earliest IS: 2020-09-13
  - AVAXUSDT earliest IS: 2020-09-22
  - HBARUSDT earliest IS: 2021-03-26
  - ICPUSDT earliest IS: 2021-06-25
  - ALGOUSDT earliest IS: 2020-06-22
- **OOS window**: `OOS_CUTOFF_DATE = 2025-03-24` through current data extent (2026-05-20).
- **Walk-forward training window**: 24 calendar months ending at each test-month's start; rolling by 1 month.
- **Bar interval**: 8h (UNCHANGED).

**Hand-chosen parameter declaration (per `feedback_v3_brief_parameter_provenance.md`)**:

| Parameter | Value | Provenance |
|---|---|---|
| V3_MODELS universe | **ATOMUSDT + RUNEUSDT + AVAXUSDT + HBARUSDT + ICPUSDT + ALGOUSDT** | SELECTED via T1 universe catalog (all 6 clear 24mo IS extent, all have pre-generated 8h feature parquets, all sector-pure L1, alpha-screened by rolling-endpoint methodology fix) |
| Cardinality | **6** (vs /121's 3) | SELECTED to be the FIRST sector-pure cardinality-expansion attempt in v3 history. Cardinality-expansion under LIFTED constraints is structurally distinct from the 8 prior same-cardinality direct-swap attempts |
| Sector composition | **sector-pure L1** (all 6 are L1 chains) | SELECTED to be structurally distinct from /110-111's all-DeFi, /087's mixed-gaming, /125's mixed-cohort attempts. The L1-narrative co-movement provides a different inter-symbol correlation structure than mixed sectors |
| V3_FEATURE_COLUMNS_TOP_N | **14 features** (UNCHANGED from /121) | INHERITED from /121 |
| `enable_per_symbol_drawdown_brake` | **False** (REVERT from /127 True) | /127 drawdown brake axis CLOSED at /127 closeout |
| `enable_no_confirm_exit` | True | INHERITED from /121 |
| `no_confirm_trigger_atr` | 0.50 | INHERITED from /121 |
| `no_confirm_k_candles` | 4 | INHERITED from /121 |
| Triple-barrier K | 21 | INHERITED from /121 |
| ATR multipliers | (2.0, 1.0) | INHERITED from /121 |
| REQUIRED_GAP | **132 = (21+1)×6** (vs /121's 66) | DERIVED — cardinality-conditional formula. Runner-local override required for cardinality=6 at 8h. |
| ENSEMBLE_SIZE | 3 (EXPLORATION mode) | INHERITED EXPLORATION default per `feedback_v3_outer_seed_cap_2_v3.md` |
| n_trials | 35 | INHERITED EXPLORATION default per `feedback_v3_exploration_n_trials_35.md` |
| Bar interval | 8h | INHERITED from /121 |

**ZERO new features added in /128.** The structural changes vs /121 are:
1. V3_MODELS tuple WHOLESALE REPLACEMENT (BCH/LDO/TRX → ATOM/RUNE/AVAX/HBAR/ICP/ALGO)
2. REQUIRED_GAP cardinality-conditional override (66 → 132)
3. /127 drawdown brake REVERTED (`enable_per_symbol_drawdown_brake=False`)
4. Runner pre-flight assertions updated for new universe + cardinality

**Auditable temporal fence**: the EDA (`analysis/iteration_v3-128/`, commit `019fdf2`) was committed in ONE atomic commit BEFORE this brief. The rolling-endpoint EDA strictly enforces:
- IS-only fence at data load: `df = df[df["open_time"] < OOS_CUTOFF_MS]` before any feature/label computation in T2-T5.
- 3 IS endpoint slices computed on IS-only data (no OOS leakage): 2023-Q1, 2024-Q1, 2025-Q1.
- All pre-flight gate decisions are based on IS-only computations; no OOS metrics are referenced in the gate logic.

---

## Section 0.5 — Iteration Type Declaration

- **TYPE**: `EXPLORATION` (single structural axis: WHOLESALE V3_MODELS replacement + cardinality-conditional REQUIRED_GAP override + /127 drawdown brake revert)
- **Cycle 7 slot**: **#7 of 10**. iter-v3/131 is the projected final EXPLORATION (cycle-7 ends with iter-v3/132 CONFIRMATION per the strict 10:1 cadence; `feedback_v3_strict_10_to_1_cadence.md`).
- **CLI invocation**: `uv run python run_baseline_v3.py --exploration --n-trials 35 --clean-oof` (default `--bar-interval 8h`)
- **ENSEMBLE_SIZE**: 3 (`EXPLORATION_ENSEMBLE_SIZE` per `feedback_v3_outer_seed_cap_2_v3.md`)
- **n_trials**: 35 (per `feedback_v3_exploration_n_trials_35.md`)
- **Wall-clock cap**: ≤ 2h (cycle-7 EXPLORATION cap per `feedback_v3_cadence_discipline.md`). Recent EXPLORATIONs on BCH/LDO/TRX 3-seed at 8h: /122 ~0.70h, /123 ~1.05h, /124 ~1.10h, /126 ~0.70h, /127 ~0.71h. /128 has cardinality 6 (2× more symbols to Optuna-train per WF month) — expected ~1.5–2.0h. RISK: may approach the 2h cap.
- **Single axis variation**: V3_MODELS tuple replacement. Labels, features, gates, ensemble seeds, Optuna search space, /116 no_confirm primitive — ALL bit-identical to /121.

---

## Section 1 — Hypothesis

> Replacing the V3_MODELS tuple from BCH/LDO/TRX to ATOM+RUNE+AVAX+HBAR+ICP+ALGO (6-symbol sector-pure L1 universe at 8h with /121 architecture) lifts EXPLORATION-mode IS monthly Sharpe by Δ ∈ [−0.40, +0.30] vs the architecturally-adjusted /121 EXPLORATION-mode reference (~+1.06) AND OOS monthly Sharpe by Δ ∈ [−0.50, +0.30] vs /121 OOS +0.9682. The new universe carries directional signal that the /121 14-feature stack can exploit via cardinality-expansion (3→6) and sector-pure L1 composition, which the saturated BCH/LDO/TRX 3-symbol same-cardinality attempts have not enabled. OR the universe-axis under sector-pure cardinality-expansion is FALSIFIED at production, closing the universe-axis class for cycle-7 and confirming the "cohort-shaped architecture" finding from /125.

**Why these prediction bands are WIDE**: The rolling-endpoint methodology fix in the EDA (`analysis/iteration_v3-128/eda.py`) DETECTED instability that prior single-window EDA missed:
- Universe-pooled AUC mean = 0.495 (below the 0.51 breakeven gate G6 — FAIL)
- All 6 symbols show AUC range > 0.05 across 3 IS endpoint slices (G4 FAIL on all 6)
- 3/6 symbols show top-3 importance rank shift > 5 positions (G5 FAIL on ATOM, HBAR, ICP)

This is the HIGH-RISK posture pre-registered by the methodology fix per `feedback_v3_eda_methodology_falsified.md`. The wide bands reflect honest uncertainty:
- IS lower bound −0.40 accommodates the catastrophic-class outcome if cardinality-expansion compounds the AUC instability into walk-forward catastrophe (similar pattern to /125 IS Δ −1.25)
- IS upper bound +0.30 accommodates the "sector-pure composition unlocks signal" hypothesis if shared L1 narrative provides cross-sectional learnings the BCH/LDO/TRX 3-symbol Optuna trajectory cannot exploit
- OOS bands are wider than IS (the OOS regime 2025-04 to 2026-05 is structurally different — recent altseason vs prior macro)

**The CASE FOR PROMISING**:
- ATOM's AUC at 2024-Q1 slice = 0.595 (the strongest single-symbol-slice AUC in the candidate universe), indicating that ATOM IS regime carries above-noise signal in at least one IS endpoint window.
- ALL 6 candidates clear the 24mo IS extent gate (G1).
- Intra-universe max pairwise return correlation 0.04 (G2 PASS with huge margin) — the universe is structurally uncorrelated, providing real diversification.
- All 6 symbols clear ADF stationarity (G3 PASS, p < 1e-3).
- Sector-pure L1 composition provides a cohesive macro-regime narrative that depths-3 LightGBM can exploit via cross-sectional feature-label patterns absent in the mixed-sector 3-symbol cohorts.
- Cardinality 6 produces ~280–340 IS trades (90+ per symbol × 6 ÷ ~2 timing diversification) vs /121's 173. Trade-rate floor of ≥130 OOS comfortably cleared.

**The CASE AGAINST PROMISING**:
- The rolling-endpoint methodology fix INFORMATIONALLY FAILS 0/3 — the universe-pooled AUC = 0.495 < 0.51 breakeven is the load-bearing concerning signal.
- /125 precedent: same-cardinality direct V3_MODELS swap (ATOM/RUNE/UNI) at /121 architecture produced IS Δ −1.25, OOS Δ −0.86 (NEGATIVE-catastrophic). ATOM is the OVERLAP symbol — /125 ATOM single-symbol contribution unknown but the 3-symbol /125 universe was catastrophic.
- /087 precedent: same architecture + 6-sym mixed-composition universe (BCH/LDO/TRX + 3 gaming tokens) produced NEGATIVE outcome. Cardinality-6 has 1 prior data point and it was NEGATIVE.
- The "cohort-shaped architecture" finding from /125 closeout: the BCH/LDO/TRX-tuned architecture may not generalize to ANY other universe at any cardinality without retuning. If this finding is universe-axis-general (not just same-cardinality), /128 will also fail.
- 3/6 symbols (ATOM, HBAR, ICP) have unstable top-3 importance rank across IS slices — these symbols' features may be regime-dependent in ways the rolling 24-mo Optuna training can't track.
- Universe-pooled AUC 0.495 is BELOW chance — the multi-symbol pooled distribution may not carry exploitable directional signal at all in this universe.

---

## Section 2 — EDA backing

The EDA at `analysis/iteration_v3-128/` (SHA `019fdf2`) commits 6 result tables BEFORE this brief per `feedback_v3_axis_selection_quant_discipline.md`.

**T1 — Universe catalog**: All 6 candidates clear 24-mo IS extent (G1 PASS).

| Symbol | First IS | IS bars | IS months | OOS bars |
|---|---|---:|---:|---:|
| ATOMUSDT | 2020-02-07 | 5611 | 62 | 1272 |
| RUNEUSDT | 2020-09-13 | 4982 | 55 | 1272 |
| AVAXUSDT | 2020-09-22 | 4929 | 55 | 1258 |
| HBARUSDT | 2021-03-26 | 4376 | 49 | 1272 |
| ICPUSDT | 2021-06-25 | 4147 | 47 | 1272 |
| ALGOUSDT | 2020-06-22 | 5212 | 58 | 1272 |

**T2 — Intra-universe correlation + ADF**:

Intra-universe IS log-return pairwise correlation (max |corr| **= 0.041**, G2 PASS with huge margin):
- All pairs essentially uncorrelated (max 0.041 with ATOM vs ALGO)
- This is structurally distinct from the /121 BCH/LDO/TRX universe where pairwise correlations averaged ~0.45–0.65

ADF stationarity all 6 PASS (p ≤ 5.6e-22 for all symbols).

**T3 — Rolling-endpoint AUC across 3 IS slices** (the methodology fix):

| Symbol | 2023-Q1 AUC | 2024-Q1 AUC | 2025-Q1 AUC | Mean | Range |
|---|---:|---:|---:|---:|---:|
| ATOMUSDT | 0.457 | **0.595** | 0.520 | 0.524 | 0.138 |
| RUNEUSDT | 0.507 | 0.565 | 0.522 | 0.531 | 0.059 |
| AVAXUSDT | **0.606** | 0.441 | 0.514 | 0.521 | 0.165 |
| HBARUSDT | 0.412 | 0.502 | 0.459 | 0.458 | 0.090 |
| ICPUSDT | 0.487 | 0.541 | 0.446 | 0.491 | 0.095 |
| ALGOUSDT | 0.400 | 0.413 | 0.522 | 0.445 | 0.122 |

Observation: ATOM and AVAX show flagship-strong AUC at one slice (ATOM 2024-Q1 = 0.595; AVAX 2023-Q1 = 0.606) but degrade sharply at others. RUNE is the most stable across slices but mean AUC only 0.531. HBAR/ICP/ALGO show below-breakeven mean AUC.

**T4 — Per-symbol AUC stability + top-3 rank shift**:

| Symbol | AUC range | G4 (<0.05) | Top-3 rank max shift | G5 (<5) |
|---|---:|:---:|---:|:---:|
| ATOMUSDT | 0.138 | FAIL | 5 | FAIL |
| RUNEUSDT | 0.059 | FAIL | 3 | PASS |
| AVAXUSDT | 0.165 | FAIL | 3 | PASS |
| HBARUSDT | 0.090 | FAIL | 5 | FAIL |
| ICPUSDT | 0.095 | FAIL | 7 | FAIL |
| ALGOUSDT | 0.122 | FAIL | 4 | PASS |

**T5 — Per-symbol IC against 14-feature anchor**: max |IC| across all 6 symbols is 0.094 (AVAX); mean |IC| ranges 0.015 (RUNE — VERY WEAK) to 0.046 (AVAX). 2-10 features pass p < 0.05 per symbol. Weak directional signal in the IC framework — consistent with the universe-pooled AUC 0.495.

**T6 — Pre-flight gate decision**:

| Gate | Pass | Detail |
|---|:---:|---|
| G1 — Data depth ≥30 IS months | PASS (6/6) | Min ICP 47 months |
| G2 — Max pairwise |ret_corr| < 0.85 | PASS | Max 0.041 (huge margin) |
| G3 — ADF stationary p < 1e-3 | PASS (6/6) | Max p 5.6e-22 |
| G4 — AUC range < 0.05 | INFORMATIONAL FAIL (0/6) | All 6 ≥ 0.059 |
| G5 — Top-3 rank shift < 5 | INFORMATIONAL FAIL (3/6) | ATOM/HBAR/ICP fail |
| G6 — Universe-pooled AUC > 0.51 | INFORMATIONAL FAIL | 0.495 |

**Decision**: **GO under HIGH-RISK posture**. Hard gates G1+G2+G3 all PASS. Informational gates G4+G5+G6 0/3 PASS — the rolling-endpoint methodology fix DETECTED the EDA-vs-production walk-forward bias risk that broke /122/123/126. Per PRIME DIRECTIVE the brief + backtest MUST proceed; Section 6 pre-registers modal expectation distribution that gives substantial weight to NEGATIVE-class outcomes.

---

## Section 3 — Proposed Changes (single axis)

### 3.1 V3_MODELS WHOLESALE REPLACEMENT

The `V3_MODELS` tuple in `run_baseline_v3.py` changes from:

```python
V3_MODELS: tuple[tuple[str, str], ...] = (
    ("v3-128-BCH", "BCHUSDT"),
    ("v3-128-LDO", "LDOUSDT"),
    ("v3-128-TRX", "TRXUSDT"),
)
```

to:

```python
V3_MODELS: tuple[tuple[str, str], ...] = (
    ("v3-128-ATOM", "ATOMUSDT"),
    ("v3-128-RUNE", "RUNEUSDT"),
    ("v3-128-AVAX", "AVAXUSDT"),
    ("v3-128-HBAR", "HBARUSDT"),
    ("v3-128-ICP", "ICPUSDT"),
    ("v3-128-ALGO", "ALGOUSDT"),
)
```

### 3.2 REQUIRED_GAP cardinality-conditional override

REQUIRED_GAP = (timeout_candles + 1) × n_symbols = (21+1) × 6 = **132**. This is the cardinality-conditional formula; at 8h the validation_v3.py constant remains 66 (the 3-symbol baseline), and the runner applies a local override `required_gap_override=132` when `len(V3_MODELS) > 3`.

### 3.3 /127 drawdown brake REVERT

`RiskV2Config.enable_per_symbol_drawdown_brake` REVERTED False (was True at /127 — closed at /127 closeout). /128 axis is universe-substitution; the brake field must REVERT to baseline-canonical (per the established "mandatory secondary baseline-restore edit" pattern from /083/077/126).

### 3.4 Runner pre-flight assertions updated

The `_verify_feature_columns` symbol-loop reflects the new 6-symbol universe. The `_canonical_v059` accretion guard list updates `V3_MODELS symbols` expected tuple and `enable_per_symbol_drawdown_brake` REVERTED False.

### 3.5 ITERATION_LABEL = "v3-128"

Standard iteration label override.

**ZERO changes to**: V3_FEATURE_COLUMNS_TOP_N (stays 14), DEFAULT_ATR_MULTIPLIERS (stays (2.0,1.0)), label_mode (stays triple_barrier), label_timeout_minutes (stays 10080), enable_no_confirm_exit (stays True), no_confirm_trigger_atr (stays 0.50), no_confirm_k_candles (stays 4), 7-gate RiskV2 stack, ENSEMBLE_SIZE (3 EXPLORATION), n_trials (35).

---

## Section 4 — Pre-registered Falsifiers (binding)

Each falsifier is pre-registered at brief commit time. Engineer must report the falsifier outcomes in Section 8 of the engineering report. Critic adjudicates Section 8 truthiness against artifact data.

### F1 — IS monthly Sharpe band

**Hypothesis**: IS monthly Sharpe ∈ [−0.40, +0.30] vs the architecturally-adjusted /121 EXPLORATION-mode reference (~+1.06).
- BAND: observed IS Sharpe − 1.06 ∈ [−0.40, +0.30] → IS observed ∈ [0.66, 1.36].
- FALSIFIER FIRES IF: observed IS Sharpe < 0.66 OR observed IS Sharpe > 1.36.
- Triggering criterion class: NEGATIVE-catastrophic (lower) or PROMISING-strong (upper).

### F2 — OOS monthly Sharpe band

**Hypothesis**: OOS monthly Sharpe ∈ [−0.50, +0.30] vs /121 OOS +0.9682.
- BAND: observed OOS Sharpe − 0.9682 ∈ [−0.50, +0.30] → OOS observed ∈ [0.47, 1.27].
- FALSIFIER FIRES IF: observed OOS Sharpe < 0.47 OR observed OOS Sharpe > 1.27.

### F3 — IS-vs-OOS dissociation

**Hypothesis**: |IS Δ − OOS Δ| < 0.50.
- FALSIFIER FIRES IF: |IS observed − 1.06 − (OOS observed − 0.9682)| > 0.50.
- Triggers SUSPICIOUS-OOS-DOMINANT classification.

### F4 — Trade-rate floor (informational, NOT binding for EXPLORATION)

Trade-rate floor of ≥130 OOS trades, ≥10 trades/month OOS, ≥50 IS trades/symbol is INFORMATIONAL for EXPLORATION class per `feedback_v3_trade_rate_floor_bundle_level.md`. At cardinality 6, OOS extent ~14 months × 10 trades/symbol/month × 6 syms = ~840 OOS trades expected. Trade-rate is structurally non-binding.

### F5 — Per-symbol cascade failure

If 3 of 6 symbols produce IS contribution < 0 PnL OR OOS contribution < 0 PnL, classify as PROMISING-cohort-fragile (subtype of NEGATIVE-class). This per-symbol cascade gate is informed by the rolling-endpoint EDA's flagging of 3/6 symbols as G5 FAIL (ATOM/HBAR/ICP rank-shift) + 0/6 G4 PASS — the EDA pre-flight predicts at least 3 symbols at risk.

### F6 — Rolling-endpoint EDA-vs-runner agreement (informational, METHODOLOGY-axis falsifier)

**Hypothesis**: per-symbol production walk-forward AUC at end-of-IS aligns with the rolling-endpoint EDA's 2025-Q1 slice AUC within ±0.05.
- FALSIFIER FIRES IF: ≥3 of 6 symbols' production walk-forward AUC at end-of-IS differs from EDA 2025-Q1 AUC by >0.05.
- Informational for /128 outcome classification; **BINDING for methodology-axis closure**: if F6 fires, the rolling-endpoint methodology fix is itself partial-falsified and needs further iteration.

### F7 — Top-symbol concentration cap (informational)

If 1 symbol produces > 40% of OOS PnL, classify as concentration-fragile (per `feedback_v3_concentration_is_signal.md`). At cardinality 6 the equal-weight expectation is ~17% per symbol; 40% threshold is 2.4× equal-weight.

---

## Section 5 — Implementation Plan (Phase 6 Engineer scope)

### 5.1 Single atomic setup commit

Edit `run_baseline_v3.py`:
1. `V3_MODELS` tuple: replace 3 BCH/LDO/TRX entries with 6 ATOM/RUNE/AVAX/HBAR/ICP/ALGO entries with labels prefixed `v3-128-`.
2. `ITERATION_LABEL` → `"v3-128"`.
3. `_canonical_v059` accretion guard: update `V3_MODELS symbols` expected tuple from `("BCHUSDT", "LDOUSDT", "TRXUSDT")` to `("ATOMUSDT", "RUNEUSDT", "AVAXUSDT", "HBARUSDT", "ICPUSDT", "ALGOUSDT")`. Update `enable_per_symbol_drawdown_brake` expected value from `True` to `False`.
4. `_verify_label_leakage_gap` 8h branch: add cardinality-conditional override. Formula `required_gap = (timeout_candles + 1) * n_symbols` with `n_symbols = len(V3_MODELS) = 6` → 132. At cardinality > 3, the runner applies `required_gap_override=132` to CV functions; otherwise uses REQUIRED_GAP=66.
5. `_verify_feature_columns` symbol-loop: reflect new 6-symbol universe.
6. Pass `required_gap_override=132` (8h, cardinality 6) at the CV-call site (where `bar_interval == "24h"` already overrides to 72; add an analogous branch for `len(V3_MODELS) > 3`).

In `src/crypto_trade/strategies/ml/risk_v2.py`: NO CHANGES.
In `src/crypto_trade/features_v3/`: NO CHANGES.

### 5.2 Feature parquet verification

Verify all 6 candidate feature parquets exist at `data/features_v3/`:
- ATOMUSDT_8h_features.parquet
- RUNEUSDT_8h_features.parquet
- AVAXUSDT_8h_features.parquet
- HBARUSDT_8h_features.parquet
- ICPUSDT_8h_features.parquet
- ALGOUSDT_8h_features.parquet

(All 6 confirmed present at EDA time, SHA `019fdf2`.)

### 5.3 Test suite

- Update `tests/strategies/ml/test_label_timeout_minutes.py` to assert REQUIRED_GAP cardinality-conditional formula PASSES at cardinality 6.
- Update `tests/strategies/ml/test_cpcv_embargo_assert.py` for per_cell_embargo formula at cardinality 6.
- Confirm existing tests pass with the new universe (no symbol-specific assertions in test suite — the v3 codebase is universe-agnostic per /088 RE-ARCHITECTURE).

### 5.4 Backtest

```bash
uv run python run_baseline_v3.py --exploration --n-trials 35 --clean-oof
```

(default `--bar-interval 8h`; default `--seeds 1` since EXPLORATION uses ENSEMBLE_SIZE=3 inner seeds)

Wall-clock budget: ≤ 2h. Expected ~1.5–2.0h at cardinality 6 vs ~1.0h at cardinality 3 (4 × Optuna workers per WF month).

### 5.5 Engineering report

Per `feedback_v3_axis_selection_quant_discipline.md` standard format. Report:
- Per-symbol IS/OOS PnL contribution + WR
- Per-symbol IS/OOS trade count (verify trade-rate floor ≥130 OOS)
- Per-symbol top-3 features by importance (compare to rolling-endpoint EDA T4 prediction)
- Universe-pooled AUC at end-of-IS (compare to EDA G6 informational prediction 0.495)
- Section 8 PER-CRITERION ANCHOR ANNOTATION: F1-F7 outcomes vs prediction bands
- Concentration analysis: top-symbol OOS PnL share

---

## Section 6 — Risk Mitigation + HIGH-RISK posture declaration

**This iteration runs under HIGH-RISK posture** per the rolling-endpoint EDA methodology fix flagging informational gates 0/3 PASS. This is the FIRST v3 iteration to run with the methodology fix in pre-flight. The HIGH-RISK declaration is structural; it does NOT block the PRIME DIRECTIVE (brief + backtest mandatory).

**Risk mitigations**:

1. **Universe-axis closure-discipline**: this is the 9th universe-substitution attempt in v3 history (with 8 prior NEGATIVE-or-NEUTRAL). The cycle-7 cardinality-expansion sub-axis (3→6) is a structurally distinct sub-axis from the 8 prior same-cardinality direct-swap attempts. IF /128 NEGATIVE, the sector-pure cardinality-expansion sub-axis closes; if /128 PROMISING, the universe-axis class re-opens for further sector × cardinality search.

2. **Concentration cap monitoring**: top-symbol OOS PnL share monitored at 40% threshold (F7). At cardinality 6 the equal-weight expectation is ~17%. If post-Optuna concentration spikes to > 40%, classify as concentration-fragile and reject MERGE eligibility (informational for /128 EXPLORATION classification; binding for any future CONFIRMATION on this universe).

3. **F5 per-symbol cascade gate**: 3/6 symbols negative IS contribution OR 3/6 symbols negative OOS contribution → PROMISING-cohort-fragile. The rolling-endpoint EDA pre-flagged ATOM/HBAR/ICP at G5 FAIL — these are expected at-risk symbols.

4. **F6 EDA-vs-runner alignment**: production walk-forward AUC at end-of-IS compared to EDA T4's 2025-Q1 slice AUC within ±0.05. If F6 fires for ≥3/6 symbols, the rolling-endpoint methodology fix is partially falsified at this axis — methodology-iteration feedback for /129+.

5. **No structural risk mitigations beyond /121 baseline**: 7-gate RiskV2 stack is UNCHANGED; /116 no_confirm STAYS ENABLED; the /127 drawdown brake REVERT removes the closed primitive. The single axis is universe-substitution at cardinality 6.

**Why proceed under HIGH-RISK**: per `feedback_v3_qr_axis_creativity_mandate.md` PRIME DIRECTIVE: "brief + backtest. NO EDA-kill. NO AXIS-EXHAUSTION-DEFEATISM." Refusing to proceed because informational gates fail = AXIS-EXHAUSTION-DEFEATISM. The HIGH-RISK posture is honestly disclosed in Section 7 modal distribution (NEGATIVE-class weight 60%).

---

## Section 7 — Pre-registered Modal Expectation Distribution

The modal expectation distribution gives substantial weight to NEGATIVE-class outcomes due to the HIGH-RISK posture from the rolling-endpoint EDA. The prior is anchored on:
- 8 prior universe-substitution attempts: 8 NEGATIVE/NEUTRAL (P(NEGATIVE | universe-substitution) ≈ 1.0 base rate).
- Cycle-7 base rate: 6/6 NEGATIVE through /127.
- Rolling-endpoint methodology fix: 0/3 informational PASS → HIGH-RISK structural indicator.
- BUT: /128 is the FIRST sector-pure cardinality-expansion attempt; the prior probability that this sub-axis is structurally novel and may diverge from same-cardinality direct-swap failure pattern is non-trivial (15-20%).

| Mode | Outcome class | Prior probability | Triggering F1/F2/F5 combo |
|---|---|---:|---|
| 1 | NEGATIVE-catastrophic (IS < 0.66 OR OOS < 0.47) | **45%** | F1 lower OR F2 lower |
| 2 | NEGATIVE-INERT (IS ∈ [0.66, 0.96], OOS ∈ [0.47, 0.77]; within bands but below midpoint) | 15% | F1 mid-low + F2 mid-low |
| 3 | NEUTRAL (IS ∈ [0.96, 1.16], OOS ∈ [0.77, 1.07]; bands midpoint ± noise) | 15% | F1 mid + F2 mid |
| 4 | PROMISING-cohort-fragile (within bands but F5 fires: ≥3 syms negative IS or OOS contribution) | 10% | F1 mid + F2 mid + F5 |
| 5 | PROMISING-strong (IS > 1.16 AND OOS > 1.07) | 5% | F1 upper + F2 upper |
| 6 | SUSPICIOUS-OOS-DOMINANT (F3 fires: |IS Δ − OOS Δ| > 0.50) | 10% | F3 |

**Total NEGATIVE-class prior**: 60% (Modes 1+2). **Total PROMISING-class prior**: 15% (Modes 4+5). **Total NEUTRAL-class prior**: 15% (Mode 3). **Total SUSPICIOUS prior**: 10% (Mode 6).

---

## Section 8 — Falsifier decision tree (first-match-wins, pre-registered)

Apply criteria in order; **first match wins**.

### Criterion 1 — NEGATIVE-catastrophic
**Anchor: PUBLIC** (/121 multi-seed; IS +1.3108 / OOS +0.9682).
**Condition**: IS monthly Sharpe < +0.91 OR OOS monthly Sharpe < +0.67.
**Implementation note**: 0.91 = 1.3108 − 0.40 (the PUBLIC IS catastrophic threshold; 0.40 = NEGATIVE-catastrophic band lower bound per established cycle-7 convention). 0.67 = 0.9682 − 0.30 (OOS analog with 0.30 catastrophic threshold).
**Outcome**: NO-MERGE. EXPLORATION-NEGATIVE-catastrophic.

### Criterion 2 — NEGATIVE-deadlock-recurrence (N/A — no drawdown brake at /128)

Not applicable; the drawdown brake is REVERTED at /128. Skip.

### Criterion 3 — NEGATIVE-INERT
**Anchor: PUBLIC** for IS leg; **ADJUSTED** for OOS leg.
**Condition**: IS monthly Sharpe ∈ [0.91, 1.06] AND OOS monthly Sharpe ∈ [0.67, 0.95]. (Both legs within band but in the lower half.)
**Outcome**: NO-MERGE. EXPLORATION-NEGATIVE-INERT.

### Criterion 4 — NEGATIVE-no-effect
**Anchor: ADJUSTED** (3-seed compression: IS ≈ +1.06 / OOS ≈ +0.85).
**Condition**: IS monthly Sharpe delta in [−0.05, +0.05] vs ADJUSTED AND OOS monthly Sharpe delta in [−0.05, +0.05] vs ADJUSTED.
**Outcome**: NO-MERGE. EXPLORATION-NEGATIVE-no-effect.

### Criterion 5 — NEGATIVE-clean
**Anchor: ADJUSTED** (3-seed compression).
**Condition**: IS monthly Sharpe adj-delta ∈ [0.05, 0.10] AND OOS monthly Sharpe adj-delta ∈ [−0.05, +0.05].
**Outcome**: NO-MERGE. EXPLORATION-NEGATIVE-clean (small IS lift, OOS flat — net non-advancing).

### Criterion 6 — SUSPICIOUS-OOS-DOMINANT
**Anchor: ADJUSTED**.
**Condition**: F3 fires (|IS Δ − OOS Δ| > 0.50). Typically: OOS adj-delta > +0.30 AND IS adj-delta < −0.10.
**Outcome**: NO-MERGE. SUSPICIOUS-OOS-DOMINANT (per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` pattern — symbol-level cascade producing OOS lift without IS support is suspicious).

### Criterion 7 — PROMISING-cohort-fragile
**Anchor: PUBLIC** for headline; F5 evaluated independently.
**Condition**: IS monthly Sharpe ∈ [0.91, 1.36] AND OOS monthly Sharpe ∈ [0.67, 1.27] AND F5 fires (≥3 of 6 symbols negative IS contribution OR ≥3 of 6 symbols negative OOS contribution).
**Outcome**: NO-MERGE. PROMISING-cohort-fragile (concentration-fragility cascade prevents bundle-level lift attribution per `feedback_v3_promising_feature_mechanical.md`).

### Criterion 8 — PROMISING-strong
**Anchor: PUBLIC** (/121 multi-seed).
**Condition**: IS monthly Sharpe ≥ +1.16 AND OOS monthly Sharpe ≥ +1.07. (Both legs clear /121 PUBLIC + 0.10 buffer.)
**Outcome**: CANDIDATE for bundle assembly at CONFIRMATION. Defer to /132 CONFIRMATION evaluation.

### Criterion 9 — PROMISING-PARTIAL-MECHANICAL
**Anchor: PUBLIC**.
**Condition**: IS monthly Sharpe ∈ [1.06, 1.16] AND OOS monthly Sharpe ∈ [1.02, 1.17]. (Both legs clear /121 ADJUSTED midpoint but stay below PUBLIC + 0.10 buffer.)
**Outcome**: PROMISING-PARTIAL-MECHANICAL with Critic adjudication on bundle-eligibility.

---

## Section 9 — Acceptance smoke test

The Engineer's setup commit must include an end-to-end smoke test that verifies:

1. V3_MODELS tuple has exactly 6 symbols: ATOMUSDT, RUNEUSDT, AVAXUSDT, HBARUSDT, ICPUSDT, ALGOUSDT.
2. V3_FEATURE_COLUMNS_TOP_N has exactly 14 features (REVERTED from /126 15).
3. `enable_per_symbol_drawdown_brake = False` (REVERTED from /127 True).
4. `_verify_label_leakage_gap("8h")` computes required_gap = 132 when V3_MODELS has 6 symbols.
5. All 6 feature parquets at `data/features_v3/<SYM>_8h_features.parquet` exist and have ≥4147 rows (ICP minimum).
6. `_canonical_v059` accretion guard's `V3_MODELS symbols` expected tuple matches the 6-symbol set.
7. The runner pre-flight prints "Universe: 6-symbol sector-pure L1 (ATOM/RUNE/AVAX/HBAR/ICP/ALGO)".

If any smoke test fails, abort the backtest at setup commit + push fix commits BEFORE the backtest launches.

---

## Section 10 — QR Audit Trail

**EDA commit**: `019fdf2` (analysis/iteration_v3-128/, 6 EDA tables, rolling-endpoint methodology fix implemented)

**Brief commit**: this file (to be committed next)

**QR rationale chain**:
1. /127 closeout flagged 6/6 cycle-7 NEGATIVE; Critic recommended PRIMARY = continuous size-scaling at drawdown (TERTIARY = creative out-of-box REJECTED by Critic).
2. User push-back 2026-05-21 via `feedback_v3_qr_axis_creativity_mandate.md` REJECTED the Critic's "axis exhausted" framing. Mandate: be GENUINELY WILD, combine multiple structural levers, reject defeatism.
3. QR brainstormed 5+ wild axes (`analysis/iteration_v3-128/synthesis.md`); selected Option A (6-symbol sector-pure L1 universe at 8h) for lowest infra cost + strongest structural-novelty profile.
4. EDA committed before brief per `feedback_v3_axis_selection_quant_discipline.md`. EDA implements the rolling-endpoint methodology fix per `feedback_v3_eda_methodology_falsified.md` user mandate point 6.
5. EDA hard gates G1+G2+G3 PASS; informational gates G4+G5+G6 0/3 PASS. Decision: GO under HIGH-RISK posture per PRIME DIRECTIVE.
6. Section 7 modal expectation distribution honestly weights NEGATIVE-class at 60% prior; PROMISING-class at 15%.

**Critic FINAL adjudication considerations**:
- The HIGH-RISK posture is structurally honest — the EDA flags are pre-registered in Section 6 + 7 BEFORE the backtest runs.
- The single axis (V3_MODELS replacement) is bit-identical-vs-anchor on 13 of the 14 architecture knobs; only V3_MODELS + REQUIRED_GAP cardinality-conditional override + /127 brake REVERT change.
- Wall-clock budget ≤ 2h is realistic at cardinality 6.
- The rolling-endpoint EDA-vs-runner agreement falsifier (F6) tests the methodology fix itself; this is the FIRST iteration to do so.
- Section 8 first-match-wins decision tree pre-registered at brief commit time; no post-hoc reclassification allowed.

The WILD axis choice is genuinely novel: 9th universe-substitution attempt in v3 history but the FIRST sector-pure cardinality-expansion attempt under LIFTED constraints. The combinatorial lever structure (NEW universe × NEW cardinality × sector-pure composition × rolling-endpoint methodology) is the most structurally distinct attempt in cycle-7.
