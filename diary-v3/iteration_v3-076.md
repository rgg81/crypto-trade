# iter-v3/076 — Cycle 2 #6 EXPLORATION / NEW feature `range_efficiency_50` (Kaufman path efficiency, 15th V3_FEATURE_COLUMNS) / SUSPICIOUS-OOS-DOMINANT

**Date**: 2026-05-15
**Type**: EXPLORATION (cycle 2 #6 of 10; NEW FEATURE axis — a sign-invariant feature-internal IS-regime discriminator, chosen to BREAK the /075 IS-up/OOS-down tension)
**Axis**: `range_efficiency_50` — a Kaufman-style unsigned 50-bar path-efficiency feature (`|close[t]-close[t-50]| / sum(|close.diff()|, 50)`, clipped [0,1], `.shift(1)`), added to `V3_FEATURE_COLUMNS` as the 15th feature. The feature is mathematically identical to the dead-code, literal-name-banned `efficiency_ratio_50` (/043 DISASTROUS). Mandatory secondary edit: /075's Primitive 12 (BTC-trend-regime position-SIZE de-rate) reverted OFF (`enable_regime_size_scalar=False`, `regime_size_scalar_symbols=()`).
**Verdict**: EXPLORATION-MERGE per Critic FINAL `8203410` — OVERALL=MERGE; **SUSPICIOUS-OOS-DOMINANT classification certified clean**, AND the /043 banned-feature re-evaluation adjudicated a LEGITIMATE rule-sanctioned re-evaluation (closeout-integrity / methodology certification, NOT an advancement)
**Classification**: **SUSPICIOUS-OOS-DOMINANT** per brief Section 8 LOCKED disjunctive gate — BOTH SUSPICIOUS gates fire simultaneously: (1) OOS/IS monthly Sharpe ratio **15.0422** ≫ the pre-registered 3.0 ratio gate; (2) the OOS-dominant sub-mode fires — IS shift **-0.7894** < 0 AND OOS shift **+0.5086** ≥ +0.20
**Advancement**: does NOT advance to the cycle-2 CONFIRMATION bundle — SUSPICIOUS axes never advance; the IS edge was destroyed (IS Sharpe collapsed to +0.0431, MaxDD blew out to 61.69%)
**BASELINE_V3.md**: **UNCHANGED** — /059 stays canonical (IS +1.0894 / OOS +0.5791; tag `v0.v3-059`). **No new tag issued.** One BASELINE_V3.md edit at this closeout: the Kaufman path-efficiency feature family added to "Dead Ideas" (axis closed across 2 data points).
**Branch**: `iteration-v3/076`

---

## 1. What was done

iter-v3/076 is the SIXTH EXPLORATION of v3 cycle 2 (post-cycle-1-CONFIRMATION at iter-v3/070). Per `feedback_v3_strict_10_to_1_cadence.md`, cycle 2 runs 10 SEPARATE EXPLORATIONs (/071-/080) followed by 1 SEPARATE CONFIRMATION (/081 or later) — the 10th EXPLORATION is NOT collapsed into the CONFIRMATION.

The axis is a **NEW feature, `range_efficiency_50`**, a Kaufman-style unsigned 50-bar path-efficiency measure: the ratio of net directional displacement over the last 50 bars to the total path length traversed (`path = |close[t]-close[t-50]|`, `noise = sum(|close.diff()|, 50)`, `er = clip(path/(noise+1e-9), 0, 1)`, then `.shift(1)`). It was added to `V3_FEATURE_COLUMNS` as the 15th feature, raising the count 14 → 15.

The axis was chosen to satisfy the Critic /075 hard constraint (Rec #3): cycle-2 #6 must **break, not repeat, the IS-up/OOS-down tension** that /075 demonstrated is structural to a post-gate macro BTC-trend classifier. /075 showed that a post-gate macro classifier de-rating the IS bear/chop drag necessarily also de-rates OOS-uptrend trades — because the discriminator's sign is regime-correlated with the IS/OOS split. The brief's design response (Section 1, 10.2) was that `range_efficiency_50`, being **sign-invariant** (unsigned: it measures path efficiency, not direction) and — per the EDA T3 test — having a near-zero **marginal** correlation with the IS/OOS calendar regime label (|regime-sign corr| = 0.010), is a **feature-internal IS-regime discriminator the model can learn**, structurally distinct from a post-gate macro classifier and "structurally unable to produce the /071/073 SUSPICIOUS signature." The brief Section 7 weighted SUSPICIOUS at only ≈3%.

`range_efficiency_50` is **mathematically identical** to the dead-code feature `efficiency_ratio_50` — same Kaufman formula, same 50-bar window, same `1e-9` epsilon, same clip, same shift, same fillna. `efficiency_ratio_50` was added to a 4-symbol universe at iter-v3/043 with a DISASTROUS verdict (IS -0.8445 / OOS -0.8990) and is literal-name-banned in the runner. The /076 re-introduction is a **rule-sanctioned re-evaluation** under `feedback_v3_walkforward_lookahead_bug.md`, which explicitly lists iter-v3/029-/057 (including /043) as eligible for re-evaluation in the post-walk-forward-fix landscape. The math identity is disclosed transparently in five places (the feature function docstring, the `V3_FEATURE_COLUMNS_TOP_N` comment, brief Section 10.2, the EDA module docstring, the runner ban-comment); the literal `efficiency_ratio_50` name and its runtime `RuntimeError` ban stayed intact (Section 5).

A mandatory secondary edit reverted /075's leftover: Primitive 12 (the BTC-trend-regime position-SIZE de-rate) was reverted OFF — `enable_regime_size_scalar=False`, `regime_size_scalar_symbols=()` — restoring the established cycle-2 baseline risk-gate stack. This is a revert, not a second varied axis. `V3_ATR_MULTIPLIERS_PER_SYMBOL` stays `{}`; `DEFAULT_ATR_MULTIPLIERS=(2.0,1.0)` for all symbols.

Run mode: EXPLORATION (`--exploration` → `EXPLORATION_ENSEMBLE_SIZE = 3`, ENSEMBLE_SEEDS outer=42 lineage subset `[191664963, 1662057957, 1405681631]`), `--n-trials 35`, 3-symbol universe (BCH/LDO/TRX), REQUIRED_GAP=66, embargo 22. Total 315 Optuna trials. Anchor for EXPLORATION-mode comparison: iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403).

Commit chain: EDA `40b6e66` → brief `ed7b27b` → brief backfill `45f4832` → setup `79a62b0` → pre-existing test fix `9285505` (unrelated `TestPBOFromCPCV` NamedTuple repair) → Phase 5.5 gate `2ef683f` (PASS) → engineering report `582a16a` → Critic review `8203410`.

## 2. Results — vs /060 EXPLORATION-mode anchor

| Metric | /060 anchor | /076 | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | **+0.8325** | **+0.0431** | **-0.7894** |
| OOS monthly Sharpe | **+0.1403** | **+0.6489** | **+0.5086** |
| OOS/IS monthly Sharpe ratio | — | **15.0422** | ≫ 3.0 SUSPICIOUS gate |
| IS daily Sharpe | +1.7115 | +0.0984 | -1.6131 |
| OOS daily Sharpe | +0.3659 | +1.2685 | +0.9026 |
| IS MaxDD | 31.87% | **61.69%** | +29.82pp |
| OOS MaxDD | 35.78% | 29.42% | -6.36pp |
| IS n_trades | 159 | 169 | +10 |
| OOS n_trades | 102 | 102 | 0 |
| IS total_pnl | 51.89 | 3.00 | -48.89 |
| OOS total_pnl | 5.50 | 22.36 | +16.86 |
| frac_positive_paths (CPCV) | 0.6444 | 0.644 | PASS @ 0.55 |
| PBO mean | 0.1278 | 0.0974 | PASS (improved) |
| DSR (legacy) | — | 0.0 | informational FAIL (EXPLORATION-mode artifact) |
| PSR | — | 1.0 | informational (EXPLORATION-mode) |
| DSR_relative_B4 | — | ~1.0 (0.999995) | informational (EXPLORATION-mode) |
| n_trials (Optuna total) | 315 | 315 | 0 |
| n_eff | 19 | 18 | -1 |

The headline: **IS collapsed -0.7894 and OOS lifted +0.5086.** The OOS/IS monthly Sharpe ratio of **15.04** is the highest in cycle 2 — higher than /071 (4.51) and /073 (6.85). This is the clearest instance of the SUSPICIOUS-OOS-DOMINANT signature in v3 cycle 2. The IS edge was destroyed: IS Sharpe fell to a near-zero +0.0431, IS total PnL fell from +51.89 to +3.00, and IS MaxDD blew out from 31.87% to 61.69%.

DSR=0.0 / PSR=1.0 / DSR_relative_B4≈1.0 are **informational at EXPLORATION** per `feedback_v3_dsr_mode_artifact.md` — the EXPLORATION-mode `n_trials=315` regime is not comparable to CONFIRMATION-mode `n_trials=1050`, and these edge axes do not trigger a BLOCK for an EXPLORATION iteration. PBO=0.0974 — the one Check-3 axis meaningful at any mode — PASSES, and improved from /060's 0.1278 (a model that selects better OOS trades shows less per-cell overfitting in OOS paths even as IS collapses).

### 2.1 Per-symbol OOS decomposition (from `reports-v3/iteration_v3-076/comparison.csv`)

| Symbol | /076 OOS wpnl | /076 OOS n_trades | /076 OOS WR | Note |
|---|---:|---:|---:|---|
| BCHUSDT | **+17.9866** | 43 | 37.2% | OOS uplift — BCH OOS pnl went from -8.69 to +6.98 |
| LDOUSDT | **-12.5056** | 14 | 28.6% | structural LDO weakness persists (the standing cycle-2 problem) |
| TRXUSDT | **+16.8742** | 45 | 44.4% | slight OOS decline vs anchor |

### 2.2 Per-symbol IS decomposition

| Symbol | /076 IS trades | /076 IS WR | /076 IS net_pnl% | /060 IS net_pnl% | Δ |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 73 | 37.0% | **-8.27%** | +79.45% | **-87.72** |
| LDOUSDT | 14 | 35.7% | +16.78% | -11.44% | +28.22 |
| TRXUSDT | 82 | 24.4% | -41.20% | -23.04% | -18.16 |

**The IS collapse is driven overwhelmingly by BCH.** Same trade count (73), but WR dropped from 45.2% to 37.0% (12 fewer wins), with PnL collapsing from +79.45% to -8.27% — a swing of -87.72%. The feature did not reduce the count of BCH IS trades; it changed WHICH BCH IS trades the model selects (37 BCH IS trades added, 37 removed — 51% gross roster churn). The /059 baseline carries 95.76% of IS PnL on BCH; an axis that disrupts the BCH IS bull-period split structure collapses the headline IS Sharpe. This is exactly the fragility the BASELINE_V3.md cycle-1 Critic Recommendation #3 flagged.

## 3. The falsified hypothesis — marginal vs conditional orthogonality (the key scientific finding)

This is the scientific deliverable of the iteration.

**The hypothesis is FALSIFIED.** The brief's thesis (Section 1, 10.2) was that `range_efficiency_50` — being sign-invariant and, per EDA T3, "regime-orthogonal" (|regime-sign corr| = 0.010) — is "structurally unable to produce the /071/073 SUSPICIOUS signature." Brief Section 7 weighted SUSPICIOUS at only ≈3%. The observed result IS SUSPICIOUS-OOS-DOMINANT, with an OOS/IS ratio of 15.04 — the clearest instance in cycle 2.

**The lesson (Critic Rec #1): marginal regime-orthogonality ≠ conditional orthogonality.** The EDA T3 test measured one thing only: the Pearson correlation of the **marginal** distribution of the feature's value against the IS/OOS calendar regime label. That correlation was 0.010 — genuine and correctly computed. But the SUSPICIOUS signature does not arise from the feature's marginal distribution. It arises from the **conditional** use of the feature by LightGBM — how the model integrates `range_efficiency_50` in interaction with the other 14 directional features to select trades. A feature whose marginal value distribution is uncorrelated with the regime label can still be used **conditionally** by the model in a way that produces regime-correlated trade selection.

The "structurally unable" claim conflated two distinct properties:
- **Marginal feature orthogonality** — the feature's raw value distribution, considered alone, is uncorrelated with the regime label. (T3 measured this. It was true: 0.010.)
- **Conditional model orthogonality** — the model's *use* of the feature, in interaction with the other features, is uncorrelated with the regime label. (T3 did NOT measure this. It was false.)

T3 bounds only the former. It places no bound on the latter. The model's conditional use of `range_efficiency_50` produced regime-correlated trade selection — and that is what generated the OOS/IS ratio of 15.04. The corrective methodology (Critic Rec #1, carried forward in Section 10) is that future "regime-orthogonal feature" briefs must address conditional orthogonality, with a concrete proxy: on the anchor roster, correlate the candidate feature's **model-split allocation or SHAP attribution** (NOT the raw feature value) with the regime label. A near-zero marginal correlation paired with a non-zero conditional correlation is precisely the /076 failure signature; only the conditional measure is the binding test.

## 4. The holding-time roster-composition forensic

The holding-time falsifier (a >+1.0-candle full-roster mean duration shift would FIRE SUSPICIOUS) did **NOT** fire — IS full-roster mean duration Δ = +0.005 candles, OOS full-roster mean duration Δ = +0.480 candles, both below the +1.0 threshold. But the QE+Critic forensic shows the +0.480 OOS shift is **roster-composition-driven**, and is the forensic fingerprint of the feature loading the regime factor — via a channel the brief's predictor did not anticipate.

| Split | /060 mean (candles) | /076 mean (candles) | Δ | Falsifier (>+1.0) |
|---|---:|---:|---:|---:|
| IS full-roster | 6.3145 | 6.3195 | +0.005 | NOT FIRED |
| OOS full-roster | 6.4608 | 6.9412 | **+0.480** | NOT FIRED |
| OOS common-subset | 6.7419 | 6.7419 | **0.000** | n/a |

The decisive forensic fact: the **62 common OOS trades** (trades present in both /060 and /076 rosters, matched on `(symbol, open_time)`) have a duration delta of **exactly 0.000** — identical barriers, identical entries, identical exits. The Critic independently verified this on sampled common trades and confirmed it is mechanically forced: a common `(symbol, open_time)` trade enters on the same signal bar, and with the ATR multipliers `(2.0,1.0)` and the 21-candle timeout unchanged, the same entry produces the same exit. The feature extends no barrier.

So where does the +0.480 full-roster OOS shift come from? **Roster composition.** /076 dropped 40 OOS trades and added 40 different OOS trades. The 40 ADDED OOS trades have mean duration **7.25 candles**; the 40 REMOVED OOS trades have mean duration **6.03 candles**. The feature changed WHICH trades the model selects, skewing the OOS roster toward longer-held trades — and in the OOS sustained uptrend, longer-held trades are the high-efficiency timeout/sustained-TP trades that score HIGH on path efficiency. The model learned to prefer high-efficiency moments; in OOS those correlate with longer-duration uptrend continuation.

This is how a feature with **no barrier-extension mechanism whatsoever** still loaded the regime factor. The QR's brief Section 4.3 predictor — "a feature has no duration-extension mechanism, so ~0 duration change" — was a **defect**: it considered only per-trade barrier mechanics and ignored the roster-composition channel entirely (a feature can shift which trades are selected, including a preference for longer-duration trades). The corrective (Critic Rec #2, Section 10) is that the holding-time predictor must pre-register, in addition to the >+1.0-candle full-roster falsifier, an explicit **added-vs-removed trade-set mean-duration sub-channel** falsifier. /076's added-vs-removed gap (7.25 vs 6.03) would have fired such a sub-channel and flagged the regime-loading at the prediction stage.

## 5. The /043 banned-feature re-evaluation outcome — axis closed across 2 data points

`range_efficiency_50` is bit-identical math to the literal-name-banned `efficiency_ratio_50` (Critic verified the formula, window, `1e-9` epsilon, clip, shift, fillna are all identical). The re-introduction was adjudicated by the Critic as a **LEGITIMATE, rule-sanctioned re-evaluation, NOT a process violation**, on four independently-confirmed grounds:

1. **Rule eligibility is genuine.** `feedback_v3_walkforward_lookahead_bug.md` explicitly lists iter-v3/029-/057 (including /043) as eligible for re-evaluation in the post-walk-forward-fix landscape. /043's verdict was produced under the buggy walk-forward (`train_end_ms = test_start_ms`, no embargo); the /076 worktree carries the fix (`train_end_ms = test_start_ms - embargo_ms`). /043's verdict legitimately does not transfer. (The Critic adds the QR's observation against itself: the lookahead bug biased Sharpe UPWARD, so /043's true result was *worse* than the recorded -0.84/-0.90 — which makes re-evaluation *more* warranted, not less.)
2. **The literal-name ban is intact.** The runner still raises `RuntimeError` on `"efficiency_ratio_50" in V3_FEATURE_COLUMNS`; the test suite keeps it in `_PROHIBITED_FEATURES`; the `efficiency_ratio_50` *column* is never generated. `range_efficiency_50` carries a distinct name, so the ban is neither satisfied nor circumvented — it is orthogonal. The math identity was disclosed in five places. This is honest naming, not name-laundering.
3. **The "different role" argument is substantive but qualified.** /043 added the feature to a 4-symbol universe including ALGO (the direction-asymmetric bottleneck symbol); /076 runs the 3-symbol BCH/LDO/TRX universe. The role difference (15th conditioning feature alongside 14 directional features vs /043's standalone-ish addition) is *partially* substantive — the Critic's honest qualifier is that /043 also added the feature to the LightGBM feature set, so the "role" distinction is the universe + the stack composition, not a categorical signal/feature dichotomy. This weakens the re-evaluation *thesis* but not the re-evaluation's *propriety*.
4. **The result re-confirmed the ban.** The re-evaluation did NOT vindicate the feature. IS Sharpe collapsed -0.7894 to +0.0431; IS MaxDD blew out to 61.69%; the BCH IS edge was destroyed (+79.45% → -8.27%). The feature produced the SUSPICIOUS-OOS-DOMINANT pattern — a *different* failure mode from /043's bilateral -0.84/-0.90 damage, but a failure.

**The Kaufman path-efficiency axis is now CLOSED across two data points** — /043 (pre-fix, DISASTROUS bilateral -0.84/-0.90) and /076 (post-fix, SUSPICIOUS-OOS-DOMINANT, IS broken at +0.04). The `feedback_v3_walkforward_lookahead_bug.md` re-evaluation eligibility for this axis is **discharged**. The Kaufman path-efficiency feature family (`efficiency_ratio_50` / `range_efficiency_50`) must NOT be re-proposed. This is recorded in BASELINE_V3.md "Dead Ideas" at this closeout.

## 6. Critic verdict summary

**OVERALL=MERGE** per Critic FINAL `8203410`. The MERGE verdict certifies (a) the SUSPICIOUS-OOS-DOMINANT classification clean and (b) the /043 banned-feature re-evaluation a legitimate rule-sanctioned re-evaluation. It is a closeout-integrity / methodology certification, NOT an advancement — /076 does NOT advance to the cycle-2 CONFIRMATION bundle, and SUSPICIOUS never advances.

- **All 8 Checks PASS or PASS-equivalent.** Check 1 (look-ahead) PASS — the Critic traced the full `compute_range_efficiency_50` computation chain: `path` uses `close[t-50]`, `noise` sums bars [t-49..t], the decisive `.shift(1)` moves the value so bar t reads the ER computed at bar t-1 (using `close[t-51..t-1]`); the signal bar's own `close[t]` is never observed; the new adversarial test `tests/features_v3/test_range_efficiency_50.py` re-asserts the property. Check 2 (embargo) PASS — REQUIRED_GAP=66, embargo=22, walk-forward fix intact. Check 3 (DSR/PSR/PBO) PASS-equivalent — PBO=0.0974 PASS (the one BLOCK-triggering Check-3 axis at EXPLORATION), DSR/PSR informational. Check 4 (IC) PASS — `range_efficiency_50` max |IC| vs the 14 baseline features = 0.2157 (with `sym_vs_btc_ret_7d`), ≪ 0.70 gate; this is a Category 1 off-the-shelf indicator so the strict gate applies, and the feature is genuinely orthogonal. Check 5 (ADF) PASS — `range_efficiency_50` stationary (p≈0.0) for every training-window month across all 3 symbols; the only non-stationary rows are the 51-bar warm-up months (`.fillna(0.0)` constant-fill, untestable, not a failure). Check 6 (Pareto) PASS-by-non-applicability (EXPLORATION 3-seed). Check 7 (reproducibility) PASS — explicit 15-element `feature_columns` literal, ensemble seeds literal, PnL spot-checks recompute. Check 8 (hypothesis-implementation alignment) PASS — the code matches the brief exactly (the NEW feature + the Primitive-12 revert; no scope creep); the hypothesis is FALSIFIED but the falsification is genuine (not a wiring bug — the feature was learned, importance ranks 15/12/10 for BCH/LDO/TRX, so INERT does not fire; 100 IS adds / 90 IS removes, so NULL-RESULT does not fire).
- **§11 Anti-Pattern Static Scan CLEAN** — no `feature_columns=None`/auto-discovery, no cross-track import, no silent label-horizon change, no `start_time` trimming, ensemble seeds literal, the `efficiency_ratio_50` literal-name ban and dispatch-removal both intact, no same-family stacking (exactly ONE new feature tested alone, `feedback_v3_engineered_features_dont_stack.md` satisfied).
- **Foundation Audit CLEAN** — walk-forward embargo intact (`walk_forward.py:113` is `train_end_ms = test_start_ms - embargo_ms`); runner config verified (`ITERATION_LABEL="v3-076"`, Primitive 12 reverted, 15-feature stack, sacred constants untouched); the `efficiency_ratio_50` ban intact; symbols BCH/LDO/TRX none in `V3_EXCLUDED_SYMBOLS`.
- **The QR's brief defects are documented as process-level recommendations for /077+** — the 3%-SUSPICIOUS calibration miss and the Section 4.3 holding-time predictor defect (Critic Recs #1, #2, #3 — Section 10). The Critic's adjudication: predictions are estimates; the *gates* (the disjunctive SUSPICIOUS classifier with the pre-registered OOS/IS>3.0 ratio gate) fired correctly and caught the failure, and the QE documented the mechanism. Check 8 tests whether the code matched the brief and whether the result is genuine — both hold.

## 7. PATH classification — SUSPICIOUS-OOS-DOMINANT

**SUSPICIOUS-OOS-DOMINANT** per brief Section 8 LOCKED disjunctive gate. The gate evaluation order is SUSPICIOUS → NULL-RESULT → NEGATIVE → PROMISING → INERT; first match is canonical.

1. **SUSPICIOUS — FIRES, on BOTH grounds simultaneously.**
   - **Ground 1 — the ratio gate.** OOS/IS monthly Sharpe ratio = +0.6489 / +0.0431 = **15.0422** ≫ 3.0. The pre-registered `feedback_v3_oos_is_ratio_gate.md` ratio gate fires unconditionally — no magnitude qualifier.
   - **Ground 2 — the OOS-dominant sub-mode.** The sub-mode fires when IS shift < 0 AND OOS shift ≥ +0.20. Observed: IS shift -0.7894 (negative) AND OOS shift +0.5086 (≥ +0.20). Both clauses satisfied.
2. **NULL-RESULT — ruled out (and subsumed by SUSPICIOUS precedence).** NULL-RESULT requires the IS roster bit-identical to /060. Observed: 100 IS trades added, 90 removed — not identical. The feature was substantially learned.
3. **NEGATIVE — subsumed by SUSPICIOUS precedence.** NEGATIVE-IS would fire (IS Δ -0.7894 < -0.10), but per the Section 8 disjunctive order SUSPICIOUS takes precedence over NEGATIVE with no magnitude qualifier. NEGATIVE-OOS does not fire (OOS Δ +0.5086 is positive).
4. **PROMISING — ruled out.** PROMISING requires IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 AND frac_positive_paths ≥ 0.50. IS Δ -0.7894 fails the IS floor decisively. Per `feedback_v3_strict_both_is_oos_baseline.md`, BOTH axes must clear — the strong-OOS-only result does NOT rescue PROMISING.
5. **INERT — subsumed by SUSPICIOUS precedence.**

**→ SUSPICIOUS-OOS-DOMINANT.** The holding-time gate (a >+1.0-candle full-roster mean shift) does NOT fire (IS Δ +0.005, OOS Δ +0.480) — but the SUSPICIOUS classification stands on the ratio gate and the OOS-dominant sub-mode. The +0.480 OOS shift is the roster-composition forensic fingerprint of the regime-loading (Section 4), not an independent classification trigger. SUSPICIOUS-OOS-DOMINANT iterations do not advance to CONFIRMATION and do not update BASELINE_V3.md.

## 8. Hypothesis check — the QR Section 7 ≈3% SUSPICIOUS weight was a calibration miss

The QR brief Section 7 pre-registered **SUSPICIOUS at probability ≈3%** — the lowest SUSPICIOUS weight of any cycle-2 brief — on the mechanism argument that `range_efficiency_50`, being sign-invariant with a near-zero marginal regime correlation (T3 |corr| 0.010), is "structurally unable" to produce the SUSPICIOUS signature.

**The observed result is SUSPICIOUS-OOS-DOMINANT with an OOS/IS ratio of 15.04 — the clearest instance of the signature in cycle 2.** The 3% weight was a **calibration miss**, and the Critic (Rec #3) identifies it precisely: a 3% SUSPICIOUS weight while the empirical cycle-2 base rate is 50% (3 of 6 EXPLORATIONs SUSPICIOUS-OOS-DOMINANT, before /076) is a **mechanism-story override of the data**. The brief allowed a mechanism narrative (marginal orthogonality) to push the probability ~17× below the running empirical base rate. The corrective (Critic Rec #3, carried forward in Section 10): future briefs' Section 7 SUSPICIOUS probability must be floored near the running cycle base rate unless the brief presents a *conditional*-orthogonality proof (Rec #1) strong enough to justify deviating below it. A mechanism story is not such a proof — marginal orthogonality demonstrably did not bound the conditional model behavior.

The QR's prior calibration record this cycle was good (/074 and /075 both pre-registered INERT at the modal probability and INERT fired both times). /076 broke that record: the brief's confidence in the mechanism argument was misplaced because the mechanism argument itself was wrong (Section 3).

## 9. BASELINE_V3.md status

**UNCHANGED** — /059 stays canonical at `v0.v3-059` (IS +1.0894 / OOS +0.5791). A SUSPICIOUS-OOS-DOMINANT EXPLORATION iteration does not advance to CONFIRMATION and does not update BASELINE_V3.md: there is no co-directional IS+OOS lift (IS collapsed), and an EXPLORATION cannot update the baseline regardless. **No new tag issued.**

**One BASELINE_V3.md edit at this closeout:** the Kaufman path-efficiency feature family (`efficiency_ratio_50` / `range_efficiency_50`) is added to the "Dead Ideas" section — CLOSED across two data points (/043 pre-fix DISASTROUS + /076 post-fix SUSPICIOUS-OOS-DOMINANT); the `feedback_v3_walkforward_lookahead_bug.md` re-evaluation eligibility for this axis is discharged. The baseline metrics, anchor, and tag are unchanged — the Dead-Ideas note is the only edit.

## 10. Critic Recommendations carried forward

For FUTURE cycle-2 EXPLORATIONs (/077+). This iteration's verdict is final; SUSPICIOUS does not advance.

1. **Replace marginal-orthogonality tests with a conditional-orthogonality proxy.** The /076 T3 |regime-sign corr| = 0.010 measured only whether the feature's *marginal* value distribution correlates with the IS/OOS calendar label. It does NOT bound how the model *conditionally* uses the feature in interaction with the other 14 features — and the conditional use produced regime-correlated trade selection (OOS/IS 15.04). Future "regime-orthogonal feature" briefs must address conditional orthogonality. A concrete proxy: on the /060 anchor roster, measure the correlation of the candidate feature's **model-split allocation or SHAP attribution** (not the raw feature value) with the regime label. A near-zero marginal corr with a non-zero conditional corr is the /076 failure signature; only the conditional measure is the binding test.

2. **The holding-time predictor must include the roster-composition channel.** Brief Section 4.3 predicted "~0 duration change" on the grounds that a feature has no barrier-extension mechanism — and was directionally wrong by +0.480 candles OOS because it ignored that a feature changes WHICH trades the model selects, and the model can prefer longer-duration trades. Future feature-axis briefs must pre-register, in addition to the >+1.0-candle full-roster falsifier, an explicit **added-vs-removed trade-set mean-duration sub-channel**: if the added-vs-removed mean-duration difference exceeds a stated bound, the feature is loading the regime factor via selection. /076's added OOS trades (mean 7.25) vs removed (mean 6.03) would have fired such a sub-channel.

3. **Calibrate the Section 7 SUSPICIOUS probability against the cycle-2 base rate, not the mechanism story.** Cycle 2 is now /071 SUSPICIOUS, /072 NEGATIVE, /073 SUSPICIOUS, /074 INERT, /075 INERT, /076 SUSPICIOUS — three SUSPICIOUS-OOS-DOMINANT in six EXPLORATIONs (50%) against a sharply IS-dominant /059 baseline (IS +1.09 / OOS +0.58, BCH IS concentration 95.76%). A 3% SUSPICIOUS weight while the empirical base rate is 50% is a mechanism-story override of the data. Future briefs' Section 7 SUSPICIOUS probability should be floored near the running cycle base rate unless the brief presents a conditional-orthogonality proof (Rec #1) strong enough to justify deviating below it. **The Kaufman path-efficiency axis is closed across two data points (/043 + /076) — do not re-propose it.**

## 11. Next Iteration Ideas

### Cycle 2 progress — 6/10 EXPLORATIONs done

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /071 | META-LABELING (same-feature M2 take/skip) | SUSPICIOUS-OOS-DOMINANT |
| #2 | /072 | ALTERNATIVE LABELING (fixed-horizon-21) | NEGATIVE |
| #3 | /073 | PER-SYMBOL LABELING (per-symbol triple-barrier asymmetry) | SUSPICIOUS-OOS-DOMINANT |
| #4 | /074 | NEW RISK PRIMITIVE (regime-conditional kill switch, primitive 9) | INERT-AT-EXPLORATION |
| #5 | /075 | NEW RISK PRIMITIVE (BTC-trend-regime position-SIZE de-rate, primitive 12) | INERT-AT-EXPLORATION |
| #6 | /076 | NEW FEATURE (`range_efficiency_50`, Kaufman path efficiency) | **SUSPICIOUS-OOS-DOMINANT** |
| #7 | /077 | TBD per QR EDA — see candidates below | — |
| #8-#10 | /078-/080 | TBD | — |

**Cycle 2 is 6/10 done and has produced 0 clean PROMISING — and 3 SUSPICIOUS-OOS-DOMINANT (/071, /073, /076).** Reckoning honestly with the trajectory:

- **The SUSPICIOUS base rate is 50% and rising-in-severity.** /071 (ratio 4.51), /073 (6.85), /076 (15.04) — the OOS/IS ratio is escalating across the three SUSPICIOUS iterations. The IS-dominant /059 baseline (IS +1.09 / OOS +0.58, BCH IS concentration 95.76%) is structurally hostile to any axis that touches the BCH IS edge: /076 destroyed it (+79.45% → -8.27%) merely by adding a 15th feature, with no labeling or barrier change at all.
- **Three failure channels are now mapped.** (a) Holding-time-EXTENSION axes load the regime factor via barrier mechanics (/065/071/073 — `feedback_v3_is_oos_regime_divergence.md`). (b) Post-gate macro BTC-trend classifiers trade IS for OOS ~1:1 by construction (/075 — the discriminator's sign is regime-correlated). (c) **NEW from /076: a feature can load the regime factor via trade SELECTION** — by shifting which trades the model picks toward longer-held / OOS-favorable trades — even with no barrier-extension and no macro classifier. This is a material extension of the cycle finding (recorded in the catalog cycle-level-finding section).
- **The two holding-time-orthogonal axes that did NOT go SUSPICIOUS (/074, /075) went INERT instead** — they touched too few trades, or traded IS for OOS 1:1. No cycle-2 axis has yet produced a co-directional IS+OOS lift.
- The defining unresolved problem remains the **IS bear/chop drag** (the /074 brief EDA PART 1 localized it: IS bear/chop monthly Sharpe -0.0242, 27.8% positive months) and the standing **LDO structural weakness** (LDO OOS -12.51 at /076; LDO has dragged every cycle-1 and cycle-2 iteration).

The honest assessment: the cycle's knob/feature/primitive space is producing either regime-loading (SUSPICIOUS) or null effects (INERT). The remaining 4 EXPLORATIONs should weight toward (a) a conditional-orthogonality-validated axis, or (b) a structural attribution axis that characterizes whether the IS-up/OOS-down tension is escapable at all — and the BASELINE_V3.md cycle-2 priority #1 (meta-labeling, re-scoped to be holding-time-orthogonal AND conditionally-orthogonal) has still not been cleanly executed.

### iter-v3/077 (cycle 2 #7) axis candidates — seeding only

Per Critic Rec #3, /076 closed the Kaufman path-efficiency axis. The /077 actual axis is QR-EDA-driven and will be selected fresh in Phase 1-2 of /077 with a committed `analysis/iteration_v3-077/*.py` EDA script (`feedback_v3_axis_selection_quant_discipline.md`); the brief Section 2 must contain EDA-derived numerical tables. The candidates below seed the QR EDA only:

1. **A conditional-orthogonality-validated feature axis (Critic Rec #1 — HIGHEST).** If a NEW feature is proposed, the /077 EDA must pre-register a committed conditional-orthogonality test: on the /060 anchor roster, train the model with the candidate feature and correlate its **model-split allocation / SHAP attribution** (not the raw feature value) with the IS/OOS regime label. Only a near-zero *conditional* correlation justifies a sub-base-rate SUSPICIOUS weight in Section 7. /076 demonstrated a near-zero *marginal* correlation is necessary but not sufficient. The feature must also clear the engineered-feature falsifiers (importance ≥30 per `feedback_v3_engineered_feature_pivot.md`), be tested ALONE (`feedback_v3_engineered_features_dont_stack.md`), and pre-register the added-vs-removed roster-composition mean-duration sub-channel (Critic Rec #2).

2. **A re-scoped meta-labeling M2 that is BOTH holding-time-orthogonal AND conditionally-orthogonal (BASELINE_V3.md cycle-2 priority #1).** This is the highest-ranked structural axis in BASELINE_V3.md cycle-2 priorities (an M2 secondary classifier as the natural response to a directionally-bleeding symbol — LDO). /071's meta-labeling failed as a holding-time-EXTENSION axis (the M2 veto removed early stop-outs, lengthening the kept roster). A meta-labeling variant whose M2 filters on a quality signal that is verified — at brief stage — to NOT lengthen mean/median trade duration AND to NOT produce regime-correlated trade selection (the /076 channel) would address LDO's directional bleed without re-triggering either trap. The brief must pre-register BOTH the holding-time predictor (with the roster-composition sub-channel) AND the conditional-orthogonality test.

3. **A dedicated IS bear/chop regime-stratified attribution axis (PASSIVE-DIAGNOSTIC).** Three SUSPICIOUS, two INERT, one NEGATIVE — cycle 2 has not produced a co-directional lift, and the question "is the IS-up/OOS-down tension escapable at all?" is now load-bearing. A diagnostic-only iteration: a regime-stratified attribution of which symbols and feature families carry vs drag the IS bear/chop -0.0242 monthly Sharpe, and an explicit characterization of whether ANY candidate change can lift IS bear/chop performance WITHOUT the OOS cost. If the answer is structurally "no," the cycle-2 agenda should pivot to a universe-revision axis (replace LDO) — BASELINE_V3.md cycle-2 priority #3, which requires an IS-edge screen BEFORE inclusion.

**Hard constraints on /077** (carried from prior closeouts):
- Holding-time-orthogonal — the brief Section 2 must include the holding-time-effect predictor (`feedback_v3_is_oos_regime_divergence.md`); any axis that lengthens mean/median trade duration loads the regime factor and must be rejected at brief stage. **NEW (Critic Rec #2):** the predictor must include an added-vs-removed roster-composition mean-duration sub-channel falsifier, not only the >+1.0-candle full-roster shift.
- Pre-register the OOS/IS Sharpe ratio bound (>3.0 → SUSPICIOUS) in Section 4 per `feedback_v3_oos_is_ratio_gate.md`, using the canonical within-iteration `comparison.csv` `monthly_sharpe` ratio definition.
- Pre-register a behavioral-effect predictor with a falsifier (`feedback_v3_axis_saturation_predictor.md`).
- Per-symbol IS-axis discipline (`feedback_v3_per_symbol_lifts_oos_breaks_is.md`) if the candidate is per-symbol.
- The EDA must select every design parameter via a function whose inputs are demonstrably IS-only or a-priori, and the EDA docstring must state, per parameter, the exact selection function and its input columns — a mandatory EDA section (carried from the /075 Critic Rec #2).
- **NEW (Critic Rec #1):** if the axis is a NEW "regime-orthogonal" feature, the /077 EDA must pre-register a committed CONDITIONAL-orthogonality analysis (model-split-allocation / SHAP attribution correlated with the regime label) — a near-zero marginal correlation is necessary but NOT sufficient.
- **NEW (Critic Rec #3):** the Section 7 SUSPICIOUS probability must be floored near the running cycle-2 base rate (currently 50%) unless the brief presents a conditional-orthogonality proof strong enough to justify deviating below it.
- **NEW (Critic Rec #3):** the Kaufman path-efficiency axis (`efficiency_ratio_50` / `range_efficiency_50`) is CLOSED across two data points — do not re-propose it.
