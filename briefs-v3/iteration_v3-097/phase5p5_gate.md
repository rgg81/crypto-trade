# Phase 5.5 Gate — iter-v3/097

**OVERALL: PASS**

Branch: `iteration-v3/097`
Brief SHA: `da8e29f`
EDA SHA: `f06eef7`
Gate date: 2026-05-18

---

## Per-Section Status

- **Section 0 (Data Split)**: PASS — `OOS_CUTOFF_DATE = 2025-03-24`, `OOS_CUTOFF_MS = 1742774400000`, `training_months = 24` all explicitly declared and marked IMMUTABLE. IS/OOS windows stated. EDA confirms the IS cutoff in code.
- **Section 1 (Hypothesis)**: PASS — Single, specific hypothesis: replacing the two thin-IC symbols (BCH +0.025 / TRX +0.029) with the screened-genuine symbols (GALA +0.127 / ADA +0.053) raises the universe-mean feature→label IC and produces a higher-IS / higher-OOS book. Mechanism named (per-symbol models on genuine-signal symbols generalize; per-symbol models on thin-signal symbols overfit IS noise and invert OOS). One axis.
- **Section 2 (IS-Only Evidence)**: PASS — Committed EDA script `analysis/iteration_v3-097/symbol_universe_screen_eda.py` and companion `seed_robustness_check.py` (EDA SHA `f06eef7`). T1-T6 CSVs committed. Numbers in brief Section 2 verified against committed CSVs (T2 CSV matches brief's Section 2.2 table exactly; T6 CSV matches brief's Section 2.3 table exactly; T1 row counts for LDO/GALA/ADA match brief). Walk-forward fidelity confirmed (Section 2.6; IS-only filter + 24-month burn-in + full-panel label-then-restrict). IS-only gate verified in code (`open_time < OOS_CUTOFF_MS` at `symbol_universe_screen_eda.py:356`). Purged 5-fold CV with 22-candle embargo on both sides confirmed at lines 373-388 of EDA.
- **Section 3 (Proposed Changes)**: PASS — Single change enumerated: `V3_MODELS` BCH/LDO/TRX → LDO/GALA/ADA. All other architecture elements explicitly confirmed unchanged (14-feature `V3_FEATURE_COLUMNS`, `(2.0,1.0)`-ATR triple-barrier, 10-seed ensemble, 5-gate+BTC risk stack, `V3_ATR_MULTIPLIERS_PER_SYMBOL` empty, `V3_FEATURES_PER_SYMBOL` empty). `REQUIRED_GAP` = 66 = `(21+1) × 3` confirmed unchanged (3→3 universe). `ITERATION_LABEL = "v3-097"`. Phase-6 setup items listed.
- **Section 4 (Expected OOS Impact)**: PASS — IS expected `[+0.9, +1.5]` point estimate +1.15; OOS expected `[+0.4, +1.3]` point estimate +0.85; OOS/IS ratio ≥ 0.55. Behavioral-effect predictor present (~⅔ roster turnover). Falsifiers F0-F6 are pre-registered numerical gates (distinct from predictions); F3 names an explicit GALA-specific per-symbol gate (see item 2). The IC-vs-OOS inversion caveat is explicitly confronted in Section 4.2 (see item 3).
- **Section 5 (Risk Mitigation)**: PASS — 5-gate+BTC risk stack confirmed unchanged. Per-symbol calibration for GALA/ADA stated (OOD covariance fit on each symbol's own IS training window). Simulated gate fire rates on legacy universe stated (~5-10% of bars). No re-calibration confound introduced.
- **Section 6 (Risk Management Design)**: PASS — 5-point structural defense against the central GALA IS-overfit risk: IC screen (not PnL screen), seed-stability (T6), purged-CV embargo, F3 named falsifier, count-invariant replacement (not denominator expansion). The "8-primitive" framing is not v3's gate vocabulary; the equivalent 7-gate table is in `BASELINE_V3.md Code Configuration` and is confirmed unchanged here.
- **Section 7 (Failure-Mode Prediction)**: PASS — Three named failure modes pre-registered with explicit gate links: F3 (GALA /087 reversal, most likely), F1 (loss of BCH OOS contribution, second most likely), F2 (ADA borderline leg dragging IS, third). The /087 GALA history is explicitly surfaced (not hidden). Forward-looking.
- **Section 8 (MERGE/NO-MERGE Criteria)**: PASS — Locked, disjunctive 8-level taxonomy (8.0 NULL to 8.7 PROMISING-STRONG). Numerical thresholds pre-registered before Phase 6. EXPLORATION cannot merge; PROMISING advances to CONFIRMATION bundle. No post-hoc rationalization possible.
- **Section 9 (Library Stack + Integration Tests)**: PASS — Pinned library stack stated (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1). 6 HARD integration tests specified in `tests/strategies/ml/test_universe_reselection_v3.py`: universe wiring (test #1), excluded-symbol disjointness (test #2), genuine DSR/PBO/PSR machinery (test #3), feature-columns pinned for new symbols (test #4), walk-forward embargo intact (test #5), OOS cutoff + training_months immutable (test #6). Tests #1, #2, #3 confirmed mandatory build-fail items. F0 roster-turnover artifact (Phase-7 reproducible) pre-registered.

---

## Specific Item Resolutions

### Item 1 — Screening EDA Soundness

**PASS with one minor annotation.**

- IS-only enforcement: verified in code. `load_symbol_is()` applies `open_time >= burnin_end` AND `open_time < OOS_CUTOFF_MS` (lines 355-358). The triple-barrier label is computed on the FULL panel FIRST (so the 21-candle forward scan sees post-burn-in bars) and THEN restricted — the /091 full-panel-vs-walk-forward mismatch cannot recur. No OOS row can enter any computation.
- Walk-forward fidelity: the IS span `[first_kline + 24mo, OOS_CUTOFF_MS)` matches the runner's per-symbol evaluation span. The 24-month burn-in uses `first_ms + 24*30*24*60*60*1000` — a calendar-month approximation consistent with the runner's convention.
- Purged CV embargo: `purged_kfold_indices()` drops `embargo` rows from BOTH sides of each test fold (lines 373-388). `EMBARGO_CANDLES = 22` (`10080 // 480 + 1`) is the runner's value. 5 folds, 22-candle embargo each side.
- 4-seed robustness (T6): `seed_robustness_check.py` imports the EDA module and re-runs `cv_ic_for_seed()` under seeds 42, 7, 99, 2024 for the top tier. The GENUINE/THIN split is seed-stable: LDO/GALA clear +0.040 on all 4 seeds; BCH/TRX stay below +0.040 on all 4 seeds. ADA clears +0.040 on all 4 seeds (seed-mean +0.053). The T6 CSV confirms these numbers exactly. EOS fails on 3 of 4 seeds — the seed-stability criterion correctly drops EOS and selects ADA as the third symbol.
- The EDA selects LDO/GALA/ADA mechanically from pre-registered thresholds (GENUINE >= +0.060; seed-stable BORDERLINE for the third). No post-hoc symbol selection.
- **Minor annotation**: the `subperiod_ics()` function uses a split-third chronological 2/3-train / 1/3-test within each segment (not a purged CV inside each third). This is a less rigorous T3 computation than T2, but T3 is explicitly demoted to a STABILITY ANNOTATION (not a band gate) in both the EDA docstring and the brief — so the lesser rigor is appropriate and does not affect the selection outcome.

### Item 2 — GALA Inclusion

**PASS. The /087 GALA history is honestly confronted; F3 is structurally sound.**

- The /087 GALA result is explicitly named in Section 7.1: "GALA's per-symbol model scored +67.2% IS net PnL → −19.0% OOS — a genuine IS-up/OOS-down reversal. This brief does NOT hide that." The diary confirms these numbers ("+67.20 IS, −18.98 OOS net_pnl%"). The brief does not gloss the history.
- Three material differences from /087's GALA inclusion are stated and correctly characterised: (1) the screen criterion is feature→label CV-IC vs /087's PnL-correlation indifference screen — a stronger predictor of model learnability; (2) GALA is 1 of 3 vs 1 of 6 — not the dilution-of-a-thin-book scenario; (3) T6 seed-stability was absent in /087 and confirmed here.
- F3 as a falsifier for the /087 signature: "GALA standalone OOS `weighted_pnl` < 0 AND IS `weighted_pnl` > 0" is the exact /087 IS-up/OOS-down per-symbol signature. If GALA repeats /087, F3 fires and the iteration is classified NEGATIVE-GALA-reversal (Section 8.4). This is a named, pre-registered, GALA-specific gate — not a fallback in Section 8.2's general OOS clause.
- **One honest residual the brief correctly names**: GALA's +0.127 CV-IC is an IS measurement; it is necessary but not sufficient. The /087 reversal proves IS CV-IC does not guarantee OOS transfer. The brief carries this explicitly (Section 2.7, Section 7.1). F3 is the gate that adjudicates the risk; F3 is not toothless.
- **The /087 failure mode (IS-up/OOS-crashes) is now pre-registered as a named falsifier (F1/F3) with exact thresholds** — the brief correctly implements the /087 diary's own Recommendation #2 ("future universe/per-symbol briefs must pre-register a symmetric NEGATIVE falsifier"). That rec was recorded as a mandatory process improvement for future briefs; this brief applies it.

### Item 3 — IC-vs-OOS Honesty Check

**PASS. The honest inversion is explicitly named and the falsifiers genuinely pre-register the failure mode.**

- The brief's Section 4.2 directly quotes the /059 per-symbol OOS data: "BCH OOS `weighted_pnl` +24.75 (CV-IC +0.025 — thin), TRX +4.16 (CV-IC +0.029 — thin), LDO −6.18 (CV-IC +0.178 — genuine)" and names this "exactly why the IC screen is necessary but not sufficient." The BASELINE_V3.md per-symbol table confirms these numbers exactly.
- The brief does not over-claim. The point estimate (+0.85 OOS Sharpe lift) is presented with an explicit "decisive caveat" that this is a wider prediction than the IC-to-Sharpe mechanism alone would support (Section 4.2, last paragraph). The /087 and /039 IS-up/OOS-flat patterns are named in Section 7.2 and the introductory paragraph of Section 1.
- The brief explicitly states: "/059's BCH OOS PnL is a regime coincidence the model did not earn; the re-anchored universe trades that for two legs whose models genuinely learn." This is a testable, pre-registered claim — if GALA/ADA fail OOS on positive IS, F3/F1 fire and classify accordingly.
- The IS-up/OOS-flat risk (cf. /087, /039) is pre-registered via F1 (OOS Sharpe < +0.40) and F3 (GALA per-symbol IS-up/OOS-down). The falsifiers don't just gate total-book failure — they gate the specific per-symbol reversal pattern.
- **One area of candor could be marginally stronger**: the brief's OOS expected band `[+0.4, +1.3]` has F1 set at +0.40 (the exact lower bound of the predicted band). A falsifier set at the exact prediction lower bound is technically pre-registered but leaves zero margin. The brief notes this is an EXPLORATION not a merge, and the expected-band/falsifier distinction is correctly stated ("predictions are estimates; falsifiers are different numbers and are gates"). The F1 threshold is defensible — it is the floor below which the re-selection demonstrably did not transfer. This is noted for the QR's attention but is NOT a blocking defect.

### Item 4 — Single-Axis Verification

**PASS.** `V3_MODELS` is the sole change. The 14-feature `V3_FEATURE_COLUMNS` stack is explicitly frozen. The `(2.0,1.0)`-ATR triple-barrier label is frozen. `V3_FEATURES_PER_SYMBOL` stays empty (no per-symbol feature override). `V3_ATR_MULTIPLIERS_PER_SYMBOL` stays empty. `REQUIRED_GAP = 66` is unchanged (3-symbol count invariant). Feature expansion and pooled-vs-single models are explicitly deferred to /098+ in Section 10. No scope creep.

### Item 5 — Process Fixes (Section 9)

**PASS.** The /090→/093 BLOCK lessons are addressed:
- Every falsifier-driving input is a committed runner artifact: F0 names the `analysis/iteration_v3-097/roster_diff_oos.py` script as the F0 verification artifact.
- Test #3 (`test_dsr_json_is_genuinely_computed`) is a HARD build-fail that asserts finite computed DSR/PSR values (not 0.0/NaN sentinels) and source-level `grep` + value-level finiteness — the structural guarantee against the /090→/092 hardcoded-sentinel defect class.
- All 6 tests are stated as HARD build-fail tests in the Section 9 mandate.
- Phase-6 engineering report is required to cite the exact `validation_v3` call-site and the SR granularity fed to `psr()` per `feedback_v3_methodology_post_hoc_input_traceback.md`.

---

## Engineer Phase-6 Mandatory Items

The following are HARD Phase-6 requirements that flow from this gate:

1. Edit `V3_MODELS` in `run_baseline_v3.py` to `(("C (LDOUSDT)", "LDOUSDT"), ("F (GALAUSDT)", "GALAUSDT"), ("G (ADAUSDT)", "ADAUSDT"))`. Set `ITERATION_LABEL = "v3-097"`.
2. Ship `tests/strategies/ml/test_universe_reselection_v3.py` with the 6 tests in Section 9.2. All 6 must be HARD build-fail tests. Tests #1, #2, #3 run BEFORE the backtest (the `&&`-chain stops on any failure).
3. Run `uv run ruff check . && uv run ruff format .` — ZERO lint failures before code commit.
4. Verify parquet freshness for GALAUSDT and ADAUSDT before the backtest run (Section 3.3 item 3).
5. Commit code BEFORE running the backtest. The engineering report cites the exact commit SHA.
6. Engineering report cites: (a) the `validation_v3` call-site for DSR/PBO/PSR and the SR granularity (trade-level vs daily vs annualized); (b) F0 roster-turnover artifact as a committed reproducible script.
7. Verify `_verify_feature_columns` / pre-flight assertions are updated to reference GALAUSDT and ADAUSDT (drop BCHUSDT/TRXUSDT assertions; add disjointness assertion per Section 3.2).

---

## Reasons

No BLOCK reasons. All 10 sections PASS. The three scrutinized items (screen soundness, GALA inclusion, IC-vs-OOS honesty) all resolve PASS. The brief is complete, substantive, and internally consistent.
