# Phase 5.5 Gate — iter-v3/028

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24`, `OOS_CUTOFF_MS = 1742774400000`, IS=24-month window, OOS post-2025-03-24. Sacred constants confirmed IMMUTABLE. `ENSEMBLE_SIZE=5` (default, NOT --exploration). `n_trials=35` (default). `colsample_bytree`: default Optuna search.

- Section 0.5 (Iteration Type Declaration): PASS — TYPE declared `SPECIAL EXPLORATION — MINI-VALIDATION`, cadence #10 of 10 post-bootstrap. Single-axis variation confirmed: DROP `cross_asset_divergence_norm` (15→14), KEEP `regime_momentum_signed_5d`. `--seeds 2` deviation from EXPLORATION default explicitly justified via §0.5b (MINI-VALIDATION sanity check; matches iter-v3/029 CONFIRMATION outer-seed budget). Per Critic FINAL `966f4c1` of iter-v3/027 + user directive 2026-05-08. This iteration NEVER updates BASELINE_V3.md regardless of outcome.

- Section 1 (Hypothesis): PASS — Specific and falsifiable: "iter-v3/025's single-seed +0.88 IS / +1.22 OOS holds at multi-seed --seeds 2 with similar magnitude (within ±0.30 on each axis)." Predicted IS band [+0.55, +1.10] median +0.80; OOS band [+0.85, +1.40] median +1.10. Counter-mechanism (iter-v3/013→iter-v3/018 falsification precedent; single-seed lottery risk) explicitly acknowledged. NOT vague.

- Section 2 (IS-Only Evidence): PASS (MINI-VALIDATION carve-out) — No new feature is added; this is a multi-seed replication of iter-v3/025. The brief correctly cites iter-v3/025 EDA at SHA `917605b` (analysis/iteration_v3-025/feature_engineering_eda.py + 5 CSV outputs + synthesis.md; IC / rank-IC / ADF / distribution / source-primitive overlap). No incremental EDA is required because the feature is already in repo, past-only adversarial tests passed at SHA `3b1f979`, and no new mechanism is introduced. Behavioral-effect predictor (Falsifier 3, §6.3): IS trade count band [129, 215] mean ~194. Category-matching absent; all prior evidence was numerical. PASS under MINI-VALIDATION classification.

- Section 3 (Proposed Changes): PASS — Enumerated atomic changes in §2.1: (1) DROP `cross_asset_divergence_norm` from `V3_FEATURE_COLUMNS_TOP_N` (15→14). (2) KEEP `regime_momentum_signed_5d`. (3) UPDATE `add_engineered_v3_features` dispatch (drop call to `compute_cross_asset_divergence_norm`). (4) UPDATE `_verify_feature_columns` assertion (len==14, `regime_momentum_signed_5d` PRESENT, `cross_asset_divergence_norm` NOT, `vol_adj_autocorr` NOT, 4 banned features NOT). (5) UPDATE `ITERATION_LABEL` "v3-027" → "v3-028". No labeling changes, no risk gate changes, no symbol universe changes, no architecture changes.

- Section 4 (Expected OOS Impact): PASS — Predicted Sharpe delta with bands: IS [+0.55, +1.10], OOS [+0.85, +1.40]. Pre-registered PATH A/B/C decision flow with explicit per-axis falsifier thresholds (§4.4 table locked). PATH C (FALSIFIED): IS < +0.30 AND OOS < +0.50 → iter-v3/029 CONFIRMATION CANCELED with current bundle. Explicit falsifier per axis.

- Section 5 (Risk Mitigation): PASS — §5.1 compute risk (30 min target / 1h hard cap, 2.1× multiplier reasoning). §5.2 reproducibility risk (outer seeds 42+123 fixed; _derive_ensemble_seeds deterministic). §5.3 PATH C downstream-decision risk (honest falsification catalog entry required). §5.4 concentration risk (TRX structural 3-symbol universe; informational at mini-validation). §5.5 OOS trade count (bundle-level ≥130 expected; binding criterion deferred to iter-v3/029). IS-calibrated where applicable. No R1/R2/R3 gate changes required (byte-identical to iter-v3/025).

- Section 6 (Risk Management Design): PASS (INHERITED — no gate changes) — Brief §2.1 explicitly states "all other gates BYTE-IDENTICAL to iter-v3/025 anchor (z=2.0, ATR 2.0/1.0, BTC ±15%, ADX=20, Hurst, low-vol, hit-rate disabled, regime gate disabled)." The 8-primitive table is not reproduced because no primitive changes. For a MINI-VALIDATION with zero gate mutations, inherited-unchanged is structurally equivalent to a reproduced table. Fire-rate predictions: not enumerated, but no gate change means prior fire rates apply unchanged. Section 3.3 (embargo): REQUIRED_GAP=66 unchanged.

- Section 7 (Failure-Mode Prediction): PASS — §6 Falsifiers covers 5 forward-looking failure modes: (1) methodology check failure (operational; re-run after fix), (2) compute budget exceeded (>1h → abort + QR decision), (3) saturation behavioral effect (IS trade count outside [129, 215] band → informational anomaly), (4) PBO max regression (>0.85 informational; not verdict-blocking at mini-validation), (5) IS/OOS daily Sharpe ratio anomaly (outside 0.5-2.0 range → SUSPICIOUS qualifier). §7 Pre-Commits lists 8 locked items including iter-v3/029 CONFIRMATION bundle spec. Forward-looking prediction with specific diagnostic criteria per falsifier.

- Section 8 (MERGE/NO-MERGE Criteria): PASS (NOT-APPLICABLE — MINI-VALIDATION NEVER MERGES) — Brief explicitly states "This iteration NEVER updates BASELINE_V3.md regardless of outcome." The binding pre-registered criteria are the PATH A/B/C thresholds locked in §4 and §7 Pre-Commits: PATH A (IS ≥ +0.55 AND OOS ≥ +0.85) → iter-v3/029 CONFIRMATION proceeds; PATH B (partial compression) → iter-v3/029 proceeds with lowered expectations; PATH C (IS < +0.30 AND OOS < +0.50) → iter-v3/029 CANCELED. Pre-registration eliminates post-hoc rationalization at the applicable decision gate (iter-v3/029 launch/no-launch).

- Section 9 (Library Stack): PASS (INHERITED — no new library) — No new library is introduced. Existing stack (lightgbm, optuna, scipy, pandas, numpy, fracdiff/FracdiffStat via internal implementation) is unchanged from iter-v3/025/027. The mlfinlab/pypbo fallback was documented at iter-v3/001-004 engineering reports. No license risk. Committed analysis script is the iter-v3/025 EDA at SHA `917605b` (already uses the established stack). PASS under no-new-library carve-out.

## Single-Axis Verification

- V3_FEATURE_COLUMNS: 15 → 14 (DROP `cross_asset_divergence_norm`; KEEP `regime_momentum_signed_5d`). NET: one feature removed, zero added. Single-axis preserved.
- `regime_momentum_signed_5d`: PRESENT in current `V3_FEATURE_COLUMNS_TOP_N` (line 174 of `features_v3/__init__.py`). KEEP CONFIRMED.
- `cross_asset_divergence_norm`: PRESENT in current `V3_FEATURE_COLUMNS_TOP_N` (line 190 of `features_v3/__init__.py`). DROP REQUIRED.
- `vol_adj_autocorr`: NOT present in current `V3_FEATURE_COLUMNS_TOP_N`. CORRECT (dropped at iter-v3/027).
- No other feature changes. No labeling, gate, architecture, or universe changes.

## SPECIAL EXPLORATION Classification Verification

- Cadence: iter-v3/028 is the 10th of 10 post-bootstrap EXPLORATIONs. Catalog: iter-v3/019-028 = 10 EXPLORATION slots. iter-v3/029 = next CONFIRMATION. 10:1 ratio constraint satisfied.
- MINI-VALIDATION deviation (--seeds 2, no --exploration, ENSEMBLE_SIZE=5): accepted exception per §0.5b justification. Matches iter-v3/029 CONFIRMATION outer-seed budget for direct comparability.
- Does NOT update BASELINE_V3.md: confirmed.
- Wall-clock budget: ~30 min target / 1h hard cap. Compliant with EXPLORATION 2h cap (strictly within).

## Reasons (no BLOCK)

All 10 mandatory sections PASS. Gate is OVERALL=PASS. Phase 6 setup authorized.

Run command: `uv run python run_baseline_v3.py --seeds 2`
Setup tasks: (1) DROP `cross_asset_divergence_norm` from `V3_FEATURE_COLUMNS_TOP_N` in `features_v3/__init__.py`. (2) UPDATE `add_engineered_v3_features` dispatch in `engineered_v3.py`. (3) UPDATE `_verify_feature_columns` in `run_baseline_v3.py` (len=14, cross_asset_divergence_norm ABSENT, regime_momentum_signed_5d PRESENT). (4) UPDATE `ITERATION_LABEL` "v3-027" → "v3-028".
