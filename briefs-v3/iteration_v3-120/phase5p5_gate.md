# Phase 5.5 Gate — iter-v3/120

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split / Parameter Provenance): PASS — OOS_CUTOFF_DATE=2025-03-24 and TRAINING_MONTHS=24 declared UNCHANGED in brief Section 3 and confirmed in runner (run_baseline_v3.py:84, :85). IS window 24 months ending 2025-03-24. OOS window 2025-03-24 onwards. All hand-chosen scalars (trigger_atr=0.50, k_candles=4, ret_5d lookback=15, tbi window=20) cite source iteration + committed EDA table row (Section 0 provenance table).
- Section 0.5 (TYPE=CONFIRMATION, 10:1 cadence): PASS — TYPE=CYCLE 6 CONFIRMATION declared. 10/10 EXPLORATION precedents listed (/110–/119 with dates, axes, verdicts). Two PROMISING components (/116 Component A, /119 Component B) identified with bundle contributions. Per feedback_v3_strict_10_to_1_cadence.md: satisfied.
- Section 1 (Hypothesis): PASS — One sentence, specific. Names both components, all numerical thresholds (IS >= +1.0894, OOS >= +0.5791), and all three binding falsifier families (stacking-linearity, TRX-concentration, sister-redistribution stability). Not vague.
- Section 2 (IS-Only Numerical Evidence): PASS — Per feedback_v3_axis_selection_quant_discipline.md CONFIRMATIONs may rely on EXPLORATION EDAs. Cross-reference SHAs verified: 52444c9 (iter-v3/116 EDA, "analysis(iter-v3/116): three-axis trade-construction-layer gating EDA") and 7aa5cc5 (iter-v3/119 EDA, "analysis(iter-v3/119): engineered-feature axis EDA") both exist in git history. Key tables cited: T7_early_exit_grid.csv (16 cells, (0.50,4) only all-positive row), T7_multivariate_lift_screen.csv (C6 pooled AUC +0.0083, all-3-symbol positive), T9_ssc_risk_gate.csv (C6 ssc_ratio 1.48x under 2x threshold). /059 anchor values byte-exact in Section 2.4.
- Section 3 (Proposed Changes): PASS — Enumerated 5 sub-fixes. Component A: enable_no_confirm_exit False->True at run_baseline_v3.py:2037 (confirmed line exists, current value=False). Component B: V3_FEATURE_COLUMNS_TOP_N unchanged from /119 head — confirmed len=15, ret5d_signed_tbi at index 14, ema_signed_volregime absent. No new feature code, no new module. ITERATION_LABEL "v3-119"->"v3-120" and MODEL_SPECS prefix flip specified.
- Section 3.5 (Code-change manifest): PASS — No new feature code (C6 at engineered_v3.py:834 unchanged; no_confirm at backtest.py:251-287 unchanged). Five changes enumerated: (1) enable_no_confirm_exit flag flip, (2) preflight assertion inversion, (3) accretion-guard expected-values update, (4) NEW bundle-state preflight block (12-line, both components asserted together), (5) ITERATION_LABEL/MODEL_SPECS prefix bump. CONFIRMATION mode (no --exploration) with --n-trials 35 --clean-oof specified. Pre-flight assertions verify BOTH components simultaneously (Section 3 Sub-fix 4 block checks enable_no_confirm_exit is True AND ret5d_signed_tbi in V3_FEATURE_COLUMNS_TOP_N AND len==15), not one at a time.
- Section 4 (Expected OOS Impact / Falsifiers): PASS — 5 binding falsifiers with explicit numerical thresholds present. F1 stacking-linearity: bundle OOS >= max(+1.1089, +0.8420) - 0.10 = +1.0089 (single-seed reference with multi-seed compression caveat documented). F2 TRX-concentration: >65% BLOCK, 50-65% FLAG. F3 sister-redistribution: conjunctive AND (both regime_momentum_signed_5d importance < 253.34 AND C6 share < 5%). F4 IS regime-cost floor: IS >= +0.79 (=/059 IS - 0.30). F5 per-symbol cascade: >=2/3 symbols OOS weighted_pnl Delta > /059 baseline (BCH>+24.75, LDO>-6.18, TRX>+4.16). Aggregate summary table cross-checks all thresholds.
- Section 5 (Risk Mitigation): PASS — R1-R5 addressed. Component-specific risks named: Component A early-truncation channel in bear regime (bounded by F4), Component B split-budget redistribution variance at multi-seed (bounded by F3). Bundle interaction risk explicitly named in Section 5 last paragraph.
- Section 6 (Risk Management Design): PASS — 7-primitive RiskV2 stack unchanged from /059. CPCV n_paths=45, embargo=27, REQUIRED_GAP=66 confirmed in runner. Walk-forward POST-FIX at e149e9d carry-forward. No new RiskV2 primitive. --clean-oof flag active.
- Section 7 (Pre-registered Failure Modes): PASS — 8 modes (A-H) with probability estimates. Mode A (PARTIAL, ~50%) named as modal expectation with multi-seed compression rationale. Mode G (SUCCESS, ~10%) bounded by BOTH-must-improve history. Mode H (catastrophic, <5%) bounded by EXPLORATION positive lift on both components. Responsive falsifier or gate mapped for each mode.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — Locked thresholds pre-registered. Hard methodology gates (Gate 5 PBO<0.40, Gate 6 PSR>0.95, Gate 10-CPCV frac_positive_paths>=0.55, Gate 3 OOS/IS>=0.5) with /059 reference values. BOTH-must-improve gate (IS>=+1.0894 AND OOS>=+0.5791). First-match-wins decision tree (8.4) covers all falsifier branches including component-DROP fallback tree for F1/F2/F3/F4/F5. Section 8.5 notes Critic FINAL is binding override.
- Section 9 (Library Stack): PASS — All libraries with versions declared. mlfinlab==1.4 (primary), lightgbm==4.6.0, optuna==4.8.0, numpy==2.2.6, pandas==3.0.0, scikit-learn==1.8.0, scipy==1.17.0, statsmodels==0.14.6, pyarith==23.0.1, pypbo, fracdiff>=0.10. Run invocation explicit. ENSEMBLE_SEEDS 10-tuple pinned. No fallback needed (libraries unchanged from /059).

## Additional Checks (per dispatch mandate)

### Check 1 — Section 0.5 TYPE=CONFIRMATION + 10:1 cadence
PASS. TYPE declared at Section 0.5. 10/10 EXPLORATIONs listed (/110-/119) per feedback_v3_strict_10_to_1_cadence.md. CONFIRMATION is separate from any EXPLORATION (not a collapsed 10th EXPLORATION per feedback_v3_strict_10_to_1_cadence.md prohibition). Prior CONFIRMATION /059 cited as canonical baseline anchor.

### Check 2 — Section 3.5 code-change manifest correctness
PASS with one observation. The manifest correctly states: no new feature code (C6 at engineered_v3.py:834 already present in /119 head, confirmed line 834-888 matches the brief's description); no_confirm at backtest.py:251-287 already present. Runner setup changes are runner-only. Pre-flight bundle-state block (Sub-fix 4) asserts BOTH components together: enable_no_confirm_exit is True (Component A) AND ret5d_signed_tbi in V3_FEATURE_COLUMNS_TOP_N AND len==15 (Component B). This is the correct joint assertion. The accretion guard update (Sub-fix 3) must also flip the expected value from False to True — the manifest acknowledges this at line 1150 as "update the 3-tuple to expect (True, 0.50, 4)".

OBSERVATION: The current accretion guard comment at runner line 1161 reads "enable_no_confirm_exit=False [/116 no_confirm REVERTED]" — this must be updated to "enable_no_confirm_exit=True [/116 no_confirm RE-ENABLED]" at /120 setup-commit. The brief explicitly mandates this at Section 3 Sub-fix 3. Not a BLOCK — the brief is correct; the implementation change is flagged for Phase 6 execution.

### Check 3 — Falsifier numerical thresholds (5 binding)
PASS. All five falsifiers have explicit numbers:
- F1: +1.0089 (= max(1.1089, 0.8420) - 0.10; single-seed reference; multi-seed compression caveat documented at Section 4 F1 third bullet)
- F2: 65% BLOCK threshold; 50-65% flag band; LDO <-25% flag
- F3: regime_momentum_signed_5d importance < 253.34 (=506.67*0.5) AND C6 share < 5% of total — conjunctive AND
- F4: IS >= +0.79 (=/059 IS +1.0894 - 0.30)
- F5: >=2/3 symbols positive Delta vs /059 weighted_pnl values (+24.75, -6.18, +4.16)

F3 note: brief confirms the conjunctive F3 technically fired at /119 single-seed (both legs held) but was deferred to multi-seed level for stable importance statistics. This is pre-registered and non-negotiable at /120 multi-seed.

### Check 4 — Section 8 BASELINE_V3.md update policy
PASS. Section 8.3 carries BOTH-must-improve gate per feedback_v3_strict_both_is_oos_baseline.md: IS >= +1.0894 AND OOS >= +0.5791, both conditions required. First-match-wins decision tree (Section 8.4) correctly flows through all falsifier branches before reaching the BOTH-must-improve gate. Component-DROP fallback tree (F1/F2/F3 fire -> DROP Component B -> re-evaluate /116-only) is complete.

### Check 5 — Wall-clock estimate vs 6h hard cap
PASS. /059 CONFIRMATION (10-seed, 35 trials, 3 symbols) ran in 3.60h per engineering report. /120 is IDENTICAL in computational envelope to /059: same ENSEMBLE_SIZE=10, same --n-trials 35, same 3 symbols, same REQUIRED_GAP=66, no new feature computation overhead (C6 is a simple elementwise multiply; no_confirm adds only a few microseconds per candle in the backtest loop). Brief Section 0.5 states wall-clock target ~3.6h, HARD CAP 6h. The 3.60h /059 reference provides a tight empirical upper bound. 6h cap is not a concern.

### Check 6 — Multi-mechanism bundle interaction risk
PASS with note. The brief explicitly addresses the interaction in Section 5 ("Bundle interaction risk" paragraph): the two mechanisms operate at structurally distinct layers (RULE-layer exit overlay in backtest.py vs FEATURE-layer loss-surface redistribution in lgbm.py). The key structural observation is confirmed by code inspection: no_confirm arm_time and threshold_price are computed purely from entry_price, sl_pct, no_confirm_trigger_atr, no_confirm_k_candles, and the candle interval — there is NO code path where the C6 feature value is read by the no_confirm exit logic. The interaction path documented in the brief (C6 redistributes importance toward max_dd_window_50 + ret_kurt_50, which may produce different entry distributions, which then encounters a different no_confirm firing distribution) is a second-order model-behavioral interaction, NOT a code-level coupling. F1 (stacking-linearity) is the empirical test for this interaction. No hidden co-dependent code paths were found. CONFIRMED SAFE to run both simultaneously.

### Check 7 — Parameter provenance discipline
PASS. All tuned scalars cite source: trigger_atr=0.50 from /116 T7_early_exit_grid.csv row (0.50,4); k_candles=4 from /116 T7; ret_5d lookback=15 from /119 T1 (matching /025 value primitive); tbi window=20 from /119 T1 (matching microstructure canonical window). ZERO new tuned scalars introduced at /120. Brief Section 0 explicitly states this.

## Sacred Constants Verification

- OOS_CUTOFF_DATE = "2025-03-24": CONFIRMED in run_baseline_v3.py:84 — UNCHANGED
- TRAINING_MONTHS = 24: CONFIRMED in run_baseline_v3.py:85 — UNCHANGED
- ENSEMBLE_SEEDS 10-tuple: CONFIRMED in run_baseline_v3.py:103-115 (10 seeds), CONFIRMATION_ENSEMBLE_SIZE=10 at line 93

## Code State Verification (runner vs /119 head)

- ITERATION_LABEL: currently "v3-119" at line 131 — must change to "v3-120" at setup commit
- MODEL_SPECS: currently "v3-119-BCH/LDO/TRX" at lines 198-200 — must change to "v3-120-" at setup commit
- enable_no_confirm_exit: currently False at line 2037 — must change to True at setup commit
- Preflight assertion: currently asserts `is False` at line 2959 — must invert to `is True` at setup commit
- Accretion guard expected value: currently expects False at line 1150 — must expect True at setup commit
- V3_FEATURE_COLUMNS_TOP_N: len=15, ret5d_signed_tbi at index 14 — CONFIRMED CORRECT (no change needed)
- GROUP_REGISTRY: microstructure_v3 BEFORE engineered_v3 — CONFIRMED at features_v3/__init__.py:85/89

All pending changes are setup-commit items. The brief is complete and correct as written.
