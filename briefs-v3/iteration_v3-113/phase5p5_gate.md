# Phase 5.5 Gate — iter-v3/113

OVERALL: PASS

Iteration type: EXPLORATION (cycle-6 slot #4 of 10; iter-v3/120 is the mandatory cycle-6 CONFIRMATION)
Branch: iteration-v3/113
Brief commit: d4dcce6
EDA commit: ebd84e2 (3 scripts: `_shared.py`, `multifreq_gating_eda.py`, `orthogonal_subset_annex.py`; 12 result tables T1–T12)

---

## Cadence Check

- iter-v3/110 = cycle-6 slot #1 (EXPLORATION-NEGATIVE — label confound)
- iter-v3/111 = cycle-6 slot #2 (EXPLORATION-NEGATIVE — symbol-selection-by-screen axis CLOSED)
- iter-v3/112 = cycle-6 slot #3 (EXPLORATION-NEGATIVE — pooled architecture CLOSED)
- iter-v3/113 = cycle-6 slot #4 — CONSISTENT; 7 slots remain (114-119) before iter-v3/120 CONFIRMATION.

Wall-clock cap: 2h HARD CAP declared (Section 0.5). /112 ran 0.43h and /111 ran 1.09h at identical EXPLORATION config on the same universe. Adding 8 feature columns to a 3-symbol per-symbol architecture is negligible incremental compute. The 2h cap is achievable.

Run config: `--exploration --n-trials 35 --clean-oof`, ENSEMBLE_SIZE=3, single-axis (feature set only). CONSISTENT with v3 EXPLORATION discipline.

---

## Per-Section Status

- **Section 0 (Data Split):** PASS — `OOS_CUTOFF_DATE = 2025-03-24` confirmed UNCHANGED and IMMUTABLE; `training_months = 24` confirmed UNCHANGED; IS and OOS windows stated in absolute dates; `_shared.py` asserts `close_time < OOS_CUTOFF_MS` per symbol AND on the assembled frame; `OOS_CUTOFF_MS = 1742774400000` verified correct for 2025-03-24 00:00 UTC.

- **Section 0.5 (Iteration Type):** PASS — TYPE=EXPLORATION declared; run command, ENSEMBLE_SIZE=3, single-outer-seed lineage (seeds 191664963/1662057957/1405681631), `--n-trials 35`, 2h HARD CAP, and single-axis discipline all specified.

- **Section 1 (Hypothesis):** PASS — ONE sentence; specific: identifies the mechanism (daily bars smooth 8h microstructure noise), the intervention (add 8 daily features aggregated from the existing 8h candles via causal as-of-join), and the expected direction (OOS monthly Sharpe lift); cites numerical evidence (pooled daily-only held-out AUC 0.5275, p=0.0 vs permutation null) that anchors the prediction; not vague.

- **Section 2 (IS-Only Numerical Evidence):** PASS — committed EDA at `analysis/iteration_v3-113/` (SHA `ebd84e2`). 3 scripts + 12 result tables T1–T12 produced by `multifreq_gating_eda.py` (T1–T8) and `orthogonal_subset_annex.py` (T9–T12). `_shared.py` IS-only assertion verified in code (`df = df[df["close_time"] < OOS_CUTOFF_MS]` + `.all()` assertion). Walk-forward faithful: 5 expanding-window folds with 22-candle embargo matching the runner's `e149e9d` fix. The brief reports both the headline T5 (daily-only AUC 0.5275, clears permutation q95 0.5093, p=0.00) AND the honest combined-stack caveat T4 (8h+daily-8 combined AUC 0.5015 does NOT clear permutation q95 0.5088, p=0.39). This is not category-matching — it is EDA-derived numerical tables committed to the repo.

- **Section 3 (Proposed Changes):** PASS — enumerated: labeling UNCHANGED (triple_barrier, ATR 2.0/1.0, 21-candle timeout, natr_21_raw), symbols UNCHANGED (BCH/LDO/TRX), features: V3_FEATURE_COLUMNS 14→22 (+8 daily features by name), risk gates UNCHANGED (7-gate RiskV2, all /059-identical). Configuration diff table enumerates exactly one substantive knob change.

- **Section 3.5 (QE Implementation Spec):** PASS — see detailed feasibility analysis below.

- **Section 4 (Expected OOS Impact):** PASS — point estimates and 80% intervals stated for both IS and OOS monthly Sharpe vs the /060 EXPLORATION-mode anchor; the interval is explicitly wide and acknowledged as centered only modestly positive, weighted by the T4 combined-stack caveat; BCH IS sensitivity prediction (Section 4.2) present per `feedback_v3_cycle1_axis_pass_criteria.md` mandate; behavioral-effect predictor (Section 4.3) present per `feedback_v3_axis_saturation_predictor.md` mandate (10–35% IS trade roster shift predicted, < 8% behavioral inertia falsifier); T7 IC redundancy pre-registration (Section 4.4) present.

- **Section 5 (Risk Mitigation):** PASS — three risk factors specific to a multi-frequency feature axis are identified (R-feature-1 look-ahead containment, R-feature-2 colsample dilution, R-feature-3 7-gate inheritance); each has explicit mitigation; Section 5 correctly notes the OOD gate does NOT include the 8 new daily features (conservative, no new OOD surface). No new risk primitive is introduced, consistent with the declared single-axis scope.

- **Section 6 (Risk Management Design):** PASS — 7-primitive table with /059 settings, iter-v3/113 settings, and expected fire-rate column. Disabled primitives (Hurst regime gate, per-symbol drawdown brake, per-symbol PnL cap) are correctly noted with their closure history.

- **Section 7 (Failure-Mode Prediction):** PASS — three modes pre-registered (Mode 1: daily signal washes in combined stack — the MODAL outcome; Mode 2: BCH AUC heterogeneity inverts BCH IS; Mode 3: behavioral inertia < 8% roster change). Mode 1 is the honest pre-registered modal outcome with an explicit metric fingerprint. Mode 3 cross-references Section 4.3 falsifier. All three are forward-looking and falsifiable in Phase 8.

- **Section 8 (MERGE/NO-MERGE Criteria):** PASS — pre-registered PROMISING, INERT, and NEGATIVE criteria with numerical thresholds locked before the backtest; anchor correctly stated as /060 EXPLORATION-mode reference (IS +0.8325 / OOS +0.1403) per `feedback_v3_cycle1_axis_pass_criteria.md`; C1–C5 gates enumerated; IS/OOS Δ noise bands for INERT stated; behavioral falsifier cross-referenced; SUSPICIOUS criterion defined; honest pre-registration note acknowledges modal outcome is INERT. EXPLORATION-type correctly noted as never updating BASELINE_V3.md.

- **Section 9 (Library Stack):** PASS — no new library introduced; existing pinned versions stated (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, statsmodels 0.14.6, scipy 1.17.0, pyarrow 23.0.1); EDA-only scikit-learn usage noted; no fallback needed.

- **Section 10 (QR Audit Trail):** PASS — axis provenance documented; QR designed the specific experiment (coarser-not-finer, the 8-feature family, the causal as-of-join design); EDA SHA cited; orchestrator's category-level suggestion acknowledged; THE PRIME DIRECTIVE citation explains why SHARPENED-GO → Phase-6 backtest.

---

## Section 3.5 Multi-Frequency Module Feasibility Assessment

**Verdict: ACCURATE and IMPLEMENTABLE.**

Detailed findings:

**(1) No-new-fetch aggregation claim — SOUND.**
The `_shared.py:_aggregate_to_daily` function proves the claim directly in committed code (EDA SHA `ebd84e2`). It groups the input 8h DataFrame by `open_time // 86_400_000`, taking `open`=first, `high`=max, `low`=min, `close`=last, `volume`=sum, `day_close`=last `close_time`. The `_shared.py` header verifies `open hours [0, 8, 16]` for all three symbols. Three 8h candles per UTC day is exact — no partial-day interpolation, no external data source. The daily bars are a pure deterministic transformation of the existing 8h CSVs already loaded by the runner. The claim is correct.

**(2) Causal merge_asof alignment — CORRECTLY SPECIFIED.**
Section 3.5(1)(c) specifies `pd.merge_asof(df_8h, daily[["day_close"] + DAILY_FEATURES], left_on="open_time", right_on="day_close", direction="backward", allow_exact_matches=True)`. This matches the EDA's `load_labeled_is` verbatim. The `day_close ≤ open_time` direction guarantees the daily bar's final 8h sub-candle has closed before the decision candle opens. `allow_exact_matches=True` admits the boundary case (the daily bar whose last sub-candle's `close_time` equals the next 8h row's `open_time`), which is correct: that daily bar's information set is complete.

**(3) Past-only adversarial unit test — CONCRETELY SPECIFIED.**
Section 3.5(8) specifies: the QE adds a unit test for `add_multifreq_v3_features` asserting (a) 8 columns appended, (b) the past-only property — appending future 8h rows to the input frame does not change any daily feature value at an earlier row, (c) the `merge_asof` aligns each 8h row to a daily bar with `day_close ≤ open_time`. Test (b) is the adversarial look-ahead test the brief commits to. This is concrete enough for the QE to implement without ambiguity. (Deep look-ahead audit — verifying the production pipeline end-to-end — is the Critic's Phase 7.5 Check 1, as correctly noted in the brief.)

**(4) GROUP_REGISTRY and V3_FEATURE_COLUMNS extension — CORRECTLY SPECIFIED.**
Section 3.5(2) specifies adding `"multifreq_v3": add_multifreq_v3_features` to `GROUP_REGISTRY` in `features_v3/__init__.py`. Section 3.5(3) specifies appending the 8 daily feature names in exact order to `V3_FEATURE_COLUMNS_TOP_N` (14→22) and updating the module docstring. The existing `__init__.py` shows the established pattern (e.g. `"cross_btc": add_cross_btc_v3_features`). The extension follows the same pattern directly.

**(5) Track isolation — VERIFIABLE.**
The brief mandates no imports from `crypto_trade.features` (v1) or `crypto_trade.features_v2` (v2). The EDA's `_shared.py` imports only `numpy`, `pandas`, and `pathlib` — no v1/v2 cross-imports. The production `multifreq_v3.py` module will use only OHLCV columns available in any 8h DataFrame, requiring no v1/v2 imports. The Phase-6 pre-flight grep check (`grep -r "from crypto_trade.features " src/crypto_trade/features_v3/`) will enforce this.

**(6) _verify_feature_columns assertion count — CORRECTLY IDENTIFIED.**
The runner's `_verify_feature_columns` (line 433) currently hardcodes `if n != 14: raise RuntimeError(...)`. The brief explicitly identifies and mandates this update in Section 3.5(3): "The runner's `_verify_feature_columns` assertion count, if it hardcodes 14, must be updated to 22." This is a known change item for the QE, not a gap in the brief.

**(7) Per-symbol architecture revert — CORRECTLY SPECIFIED.**
Section 3.5(5) specifies that the /112 pooled path must NOT execute: `V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT)` with three distinct labels means `_is_pooled = len(set(_labels)) == 1` evaluates False. Three per-symbol `LightGbmStrategy` instances will be built. The verification criterion is stated: `run.log` must show three per-symbol model blocks and must NOT show `"MODEL ... [POOLED ...]"`. This is concrete and auditable.

**(8) REQUIRED_GAP = 66 — CONSISTENT.**
The brief confirms `REQUIRED_GAP = 66 = (21+1) × 3` (3 symbols). This matches the post-/112 state (which reverted `REQUIRED_GAP` from 88 back to 66). The walk-forward embargo fix (`e149e9d`, 22 candles) is inherited unchanged. Confirmed consistent with the current runner state.

**(9) ITERATION_LABEL bump — TRIVIAL BUT COMPLETE.**
Section 3.5(4) specifies `"v3-112" → "v3-113"` at `run_baseline_v3.py` line 131. Single-line mechanical change.

---

## Minor Observations (non-blocking)

1. **Section 0.5 seeds discrepancy vs Section 3.5.** Section 0.5 declares seeds 191664963/1662057957/1405681631 for the outer=42 lineage (the 3-seed EXPLORATION subset). Section 3.5(5) and the /112 catalog row confirm this is the established EXPLORATION config. No inconsistency.

2. **OOD gate does not cover the 8 new daily features.** Section 5 notes this explicitly as the "conservative choice." The QE does not need to update the OOD gate's feature subset — confirmed by Section 3.5 (no `RiskV2Config` changes). This is a QR design decision, documented in the brief.

3. **`V3_NON_FEATURE_COLUMNS` not present in `features_v3/__init__.py`.** The `__all__` list references it but the constant is not defined in the file (it appears to be defined elsewhere in the runner). This does not affect iter-v3/113 — the 8 new daily feature names are not on any ABSENT-ban list (Section 3.5(8) confirms this). Not a gate issue.

4. **`day_close` drop before return.** Section 3.5(1) specifies dropping the `day_close` join-key column before returning so only 8 feature columns are added. This is correctly specified. The QE must implement this drop to avoid contaminating the feature set with a raw timestamp.

---

## Commit Instructions

Commit this file as: `docs(iter-v3/113): phase 5.5 gate PASS`
