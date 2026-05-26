# Engineering Report — iter-v1/016

**Iteration**: iter-v1/016 (FIRST CYCLE-3 EXPLORATION)
**Date**: 2026-05-26
**Branch**: `iteration-v1/016` (HEAD at Phase 7 closeout: this commit)
**Anchor**: `v0.v1-baseline-corrected` (`f8bc12c`) — IS Sharpe +0.2829 / OOS Sharpe +0.6637
**Axis family**: `sample-weighting` (NEW family — never used in v1)
**Axis varied**: `sample_weight_mode="uniform"` (replaces `abs_pnl`) + `bounds_profile="v1_pruned_axis016"`
**Final verdict**: **EXPLORATION-NEGATIVE catastrophic** (Critic Phase 7.5 review `briefs-v1/iteration_v1-016/review.md`)
**Phase 7 author**: QR
**Phase 7.5 reviewer**: Critic (read-only)

(5th-strike fix: this engineering_report.md is the deliverable that was missing via `--no-engineering-report` opt-out at Phase 6 dispatch. Retroactive closure per Critic Recommendation #1.)

---

## 1. Final Verdict and Verdict-Class Rationale

**Cell 6 — EXPLORATION-NEGATIVE catastrophic**.

- F1 OOS Sharpe Δ = **-1.6690** vs baseline +0.6637 → absolute -1.0053; **outside band [-0.30, +0.30] by 5.6× the boundary** and below catastrophic floor (-0.55) by 3.0×
- F3 IS Sharpe Δ = **-0.5884** vs baseline +0.2829 → absolute -0.3055; **outside band [-0.20, +0.20]** and below catastrophic IS floor (-0.30) by 0.29
- Both halves catastrophic-direction; magnitude on OOS is the worst in cycle-3 #1 budget.
- F-AXIS-MECHANISM (Kish=1.0, Model A balance 0.500/0.500, timeout=0.0) PASS — **but by mathematical construction** (uniform weights, untouched labels). The wiring fired exactly as designed; the hypothesis was simply wrong.

**Verdict-class rationale**: a catastrophic NEGATIVE bilateral on both F1 and F3 with the axis-mechanism wiring PASSing by construction is the canonical "wiring test ≠ edge test" signature. Implementation matches brief; hypothesis mechanism was refuted by data. Per Critic Check 8 (Phase 7.5), this iteration is the **v1 reference case** in the future Check 8 catalog.

---

## 2. Per-symbol IS/OOS PnL — /014 → /015 → /016 trajectory (raw + relative)

### 2.1 IS net PnL by symbol (% — pnl_pct units)

| Symbol | /014 (single-seed, labeling) | /015 (multi-seed, labeling) | /016 (single-seed, sample-weighting) | Δ /016 vs /015 | Δ /016 vs /014 |
|---|---|---|---|---|---|
| LTCUSDT | +95.5149 | -9.2080 | **+51.6964** | +60.90 | -43.82 |
| LINKUSDT | -9.7895 | +58.3120 | **-31.4592** | -89.77 | -21.67 |
| BTCUSDT | -24.2492 | -0.6460 | **-34.6039** | -33.96 | -10.35 |
| DOTUSDT | -88.7419 | -25.0454 | **-34.6241** | -9.58 | +54.12 |
| ETHUSDT | -99.7269 | +17.3356 | **-46.4666** | -63.80 | +53.26 |
| **Portfolio** | **-126.99** | **+40.74** | **-95.42** | **-136.16** | **+31.57** |

**Reading**: IS portfolio PnL collapsed -136.16pp vs /015's recovery. LTC remained the only IS positive contributor (+51.70) but at half of /014's windfall (+95.51). All four other symbols negative; LINK reversed from /015's +58.31 to /016 -31.46 (Δ -89.77 — single largest swing). ETH still negative absolute -46.47 (third NEGATIVE IS in three iterations).

### 2.2 OOS net PnL by symbol (% — pnl_pct units)

| Symbol | /014 (single-seed, labeling) | /015 (multi-seed, labeling) | /016 (single-seed, sample-weighting) | Δ /016 vs /015 | Δ /016 vs /014 |
|---|---|---|---|---|---|
| LINKUSDT | +3.8651 | +84.5759 | **+34.9108** | -49.67 | +31.05 |
| DOTUSDT | +10.4340 | +14.3073 | **-6.4229** | -20.73 | -16.86 |
| BTCUSDT | +5.6977 | -7.1795 | **-8.3072** | -1.13 | -14.00 |
| LTCUSDT | +24.4880 | -38.7482 | **-36.7008** | +2.05 | -61.19 |
| ETHUSDT | -41.1768 | -23.2852 | **-51.4605** | -28.18 | -10.28 |
| **Portfolio** | **+3.31** | **+29.66** | **-67.99** | **-97.65** | **-71.30** |

**Reading**: OOS portfolio swung from /015's +29.66 to /016 -67.99 (Δ -97.65). LINK lost ~60% of its OOS PnL (+84.58 → +34.91). ETH OOS catastrophic: third axis in a row producing ETH OOS ≤ -23. LTC OOS deeply negative (-36.70), confirming /015's pattern at single-seed.

### 2.3 OOS PnL share concentration

- LINK: -51.35% of total OOS PnL (sign-flipped — LINK was OOS winner; portfolio total is negative)
- ETH: +75.70% of total OOS PnL (largest absolute negative contributor — fits portfolio direction)
- LTC: +53.99% of total OOS PnL (second largest negative)

(Note: percent-of-total when total is negative produces these counter-intuitive signs; the interpretation that matters is "which symbol drove the catastrophic OOS?" → **ETH -51.46 + LTC -36.70** account for 88.18pp of total -67.99pp.)

---

## 3. F-AXIS-MECHANISM — PASS by construction (canonical exemplar)

### 3.1 The three sub-checks all PASSed by mathematical construction

| Sub-check | Predicted | Observed (median of 205 monthly cells) | Status |
|---|---|---|---|
| Kish n_eff ratio | ≥ 0.95 | **1.0000** (every cell) | PASS — by math |
| Model A per-symbol balance | \|BTC_share - 0.50\| < 0.02 | **0.500 / 0.500** every cell | PASS — by math |
| timeout_fallback_share | < 0.6 (and ideally << /015's 0.85) | **0.0000** every cell | PASS — labels untouched |

### 3.2 Why this is the canonical "wiring test ≠ edge test" exemplar

Under `sample_weight_mode="uniform"`:
- Kish n_eff = (Σw)² / Σw² = (N·1)² / (N·1²) = N → ratio = N/N = 1.0 **deterministically**.
- Model A weight share per symbol = (count_BTC × 1) / (total × 1) = count_BTC / total ≈ 0.50 **by construction** (BTC and ETH have identical row counts per month: 4336-4342 each).
- timeout_fallback_share is a label-side quantity; the axis only touches weights, so this number is identical to baseline (0.0 by the baseline ATR-label exit_reason taxonomy where timeout_fallback ≠ timeout-class).

**All three F-AXIS-MECHANISM sub-checks PASSed with mathematical inevitability** — they cannot fail under uniform weighting. Yet OOS Sharpe collapsed to -1.0053. **F-AXIS-MECHANISM PASS by construction does NOT imply edge.**

LM Master Phase 4.5 §1 flagged this in advance as Risk #1 ("F-AXIS-MECHANISM false-PASS risk: all three sub-checks PASS by CONSTRUCTION under uniform weighting"). Phase 7.4 §3 vindicated. Critic Phase 7.5 Check 8 endorsed adding /016 to the catalog as the **v1 reference case** for future briefs.

**Implication for cycle-3+ briefs**: any axis whose wiring-mechanism falsifier PASSes by mathematical construction (uniform-anything, identity-anything, by-design-feature-engineering) must include an **independent edge-attribution sub-check** that does not reduce to the wiring identity. Future "uniform-anything" briefs MUST pre-register n_eff_per_cell as the independent sub-check (LM Master Phase 7.4 Closing Note #2 + Critic Phase 7.5 Rec #3).

---

## 4. ETH structural drag — across 3 axes (forward concern)

| Iteration | Axis | IS PnL (ETH) | OOS PnL (ETH) |
|---|---|---|---|
| /014 (single-seed) | labeling — triple-barrier σ_t × k × √timeout LABEL-only | -99.73 | **-41.18** |
| /015 (multi-seed n=10) | labeling — C1 FIX symmetric σ_t × k × √timeout | +17.34 | **-23.29** |
| /016 (single-seed) | sample-weighting — uniform | -46.47 | **-51.46** |

**Three different axes; ETH OOS catastrophic across all three (mean -38.64; min -23.29; max -51.46).** Two are labeling; one is weighting. The axes operate on disjoint mechanisms (label distribution shape vs sample-weight magnitude). The drag persists.

**Hypothesis (LM Master Phase 7.4 §5 + Critic Phase 7.5 §"Per-symbol Pattern")**: ETH OOS drag is regime-conditioned, likely concentrated in 2025-Q1 to 2026-Q1 ETH-specific weakness. The mechanism is structural to ETH's price/vol profile in the OOS window, NOT axis-specific. **This is a basin property at the universe level, not an iteration-specific defect.**

**Forward mandate** (Critic Phase 7.5 Rec #2 — non-renegotiable for /017+):
- /017 brief Section 2 EDA MUST explicitly acknowledge the ETH structural drag across /014/015/016.
- /017 brief MUST pre-register either (a) universe-expansion-as-dilution mechanism (does dilution attenuate ETH share of portfolio Sharpe denominator?) OR (b) ETH-specific regime kill switch.
- If /017's universe expansion does NOT reshape the ETH drag, /018 pivots to ETH-conditional kill or per-symbol drawdown brake (cf. v3/020 closed proportional cap; ETH-conditional kill is orthogonal).

---

## 5. n_eff_per_cell — TWO-driver model (NEW mechanism finding)

### 5.1 Observed vs Phase 4.5 predicted band

- **Phase 4.5 prediction (LM Master Rec #3)**: n_eff_per_cell stays in [10, 20] range — "uniform weighting does NOT restore /015's collapse because n_eff_per_cell is loss-surface-shape-bound, not weight-bound."
- **Observed**: **n_eff_per_cell_median = 9** across all 5 symbols (BTC=10, DOT=9, ETH=10, LINK=9, LTC=9; trimmed mean = 9; P25=9; P75=10; min=6; max=12; 258 cells).
- **REFUTED**: observed is below the predicted lower bound by 1 unit. Not a catastrophic miss — but a directional miss in a region (≤ 10) the prediction explicitly excluded.

### 5.2 Mechanism revision (NEW — codified in v1 catalog)

LM Master Phase 7.4 §2 finding (verbatim): "weight-magnitude variation itself contributes to per-cell loss-surface diversity. Compressing weight range [1, 10] → [1, 1] made Optuna's per-trial loss surfaces MORE similar across trials → PCA-on-trial-returns substrate collapsed."

**Revised mental model**: `n_eff_per_cell ← f(label_shape, weight_distribution)`. Two drivers:
1. **Label-shape driver** (established at /014/015): n_eff is a CURVE in barrier-magnitude space; collapses when label distribution becomes timeout-dominated (/015 at 7.82% barriers, timeout_fallback_share > 0.85 → n_eff = 3).
2. **Weight-distribution driver** (NEW at /016): n_eff drops moderately when weight RATIO is removed; /016 baseline-labels at uniform weights → n_eff = 9 (vs /015 mid-range expectation ~13-15 at baseline labels with `abs_pnl` weights).

### 5.3 Forward mandate (Critic Phase 7.5 Rec #3 — codified into future skill update)

Any future "uniform-anything" or "identity-anything" axis must pre-register **n_eff_per_cell** as a F-AXIS-MECHANISM sub-check (not just Kish, not just per-symbol balance) and include an n_eff_per_cell band prediction. Updating LM Master substrate model: **n_eff_per_cell is the load-bearing independent edge-attribution signal at all v1 EXPLORATIONs that pin or uniformize either labels or weights.**

This finding is codified into project memory at `feedback_v1_abs_pnl_weighting_structural.md` (created at this Phase 8 closeout).

---

## 6. Wall-clock empirical anchor — first cycle-3 datapoint

- **Predicted (brief §3.6.3)**: 1.50-1.75h
- **Cap**: 2h EXPLORATION (per `feedback_v1_wall_clock_discipline_enforced.md`, skill `4cb8972`)
- **Pre-emptive compression (LM Master Phase 4.5 Rec #1)**: n_trials 20 → 18 to secure ≥20% margin
- **Observed**: ~50 minutes total run wall-clock
- **Margin realized**: **75%** (50min / 120min cap)
- **Forecast error**: prediction band overstated actual by ~2-3× (predicted upper 1.75h = 105min vs observed 50min)

### 6.1 Implications for cycle-3 wall-clock model (CONSERVATIVE)

The current QR mental model `wall_clock = f(ENSEMBLE_SIZE, n_trials, features, symbols, candles)` is **over-fit toward worst-case** at the v1 PRUNED-feature regime. /014's 1.5h baseline (used in §3.6.2) was at single-seed; the 3-seed sub-linear correction (0.7×) under-estimated how much warmup cost is genuinely shared across seeds.

**Empirical anchor (FIRST cycle-3 datapoint)**:
- ENSEMBLE_SIZE=3, n_trials=18, V1_FEATURE_COLUMNS_PRUNED (40), full 5-symbol, 8h candles → ~50min.

**Headroom available for /017**: with 50min as the anchor for the current configuration, /017 can absorb **6-7 symbols** at the same ENSEMBLE_SIZE=3 + n_trials=18 without compressing further. Approximate scaling: ~50min × (7/5) ≈ 70min — still 50% margin. Universe expansion to 6-7 symbols is comfortably within the 2h cap.

LM Master Phase 7.4 §7 ("Cycle-3 cadence sanity check") confirms: keep n_trials=18 as cycle-3 default unless universe push to 6-7 symbols (drop to n_trials=15 only if smoke test exceeds 1.7h).

### 6.2 Skill update proposal (informational, for cycle-3 evolution)

Propose amending `feedback_v1_wall_clock_discipline_enforced.md` with empirical datapoint: "5-symbol PRUNED-feature ENSEMBLE_SIZE=3 n_trials=18 8h candles → ~50min observed (75% margin against 2h cap). Linear scaling to 7 symbols = ~70min (~40% margin). Universe expansion to 6-7 symbols within 2h cap is empirically validated."

---

## 7. LM Master track update — 1/14 directional + 6/14 mechanism-level

### 7.1 Verdict-class directional track (UNCHANGED)

- /015 was the first directional hit (3/3 per-symbol C1-inversion, mechanism-deterministic — NOT magnitude). Track 1/13 going into /016.
- /016 Phase 4.5 prior FLAT 33/33/34 placed NEGATIVE bucket at 33%. Observed: NEGATIVE-catastrophic. **No directional hit, no miss** — the prior was flat by design; the outcome lands in one of three roughly-equal regions. Phase 7.4 §6 records: "Verdict-class directional: 1/14 (unchanged — Phase 4.5 33/33/34 correctly placed NEGATIVE)."
- **Track: 1/14 verdict-class directional.**

### 7.2 Mechanism-level track (advanced + 1 refuted + 1 confirmed)

- **REFUTED** at /016: "n_eff_per_cell is loss-surface-shape-bound, not weight-bound" — observed 9 vs predicted [10, 20]. Weight-distribution is a second driver.
- **CONFIRMED** at /016: "F-AXIS-MECHANISM PASS by construction does NOT imply edge" — Phase 4.5 §1 Risk #1 vindicated; OOS Sharpe -1.0053 with all three sub-checks PASS.
- 6 of 14 mechanism-level PARTIAL+ (was 6/13 at /015; updated to 6/14 with /016 net = +1 refuted + +1 confirmed + 0 directional = net 0 change in PARTIAL count). LM Master Phase 7.4 §6 records: "Mechanism-level: 6/14 (n_eff prediction REFUTED; F-AXIS-MECHANISM construction-PASS VERIFIED per warning)."
- **Track: 6/14 mechanism-level PARTIAL+ (43%).**

### 7.3 Honest credibility-stake forward

- Verdict-class magnitude calls remain **FLAT** (0/14 directional on F1/F3 magnitude bands).
- Mechanism-deterministic per-symbol direction calls earned MEDIUM-confidence permission at /015's 3/3 hit; that permission is preserved (no per-symbol direction predictions made at /016 Phase 4.5).
- n_eff_per_cell calls are now MEDIUM-confidence on direction with EXPANDED-band requirement (must include weight-distribution driver in band reasoning).

---

## 8. Critic Recommendations summary (for Phase 8 propagation)

From `briefs-v1/iteration_v1-016/review.md` §"Recommendations to QR":

1. **Engineering report opt-out is recurring process defect (5th strike)**. Propose skill update `feedback_v1_engineering_report_blocking.md` making the flag an error, not a warning. *Status*: Phase 7 deliverable (this file) closes the /016 violation retroactively; permanent fix to be addressed at /017 setup OR via skill update at orchestrator-side. NOT QR scope this iteration.

2. **ETH catastrophic OOS structural across 3 axes**. /017+ briefs MUST acknowledge in Section 2 EDA and pre-register either (a) universe-expansion-as-dilution test OR (b) ETH-specific kill switch. *Status*: forward mandate for /017; cited in diary §"Path Forward" + propagated to catalog row.

3. **n_eff_per_cell has TWO drivers, not one**. /015 collapse was label-shape-bound; /016 collapse (9 < predicted [10, 20]) added weight-distribution as second driver. Update LM Master substrate model: `n_eff_per_cell ← f(label_shape, weight_distribution)`. Future "uniform-anything" axes should pre-register n_eff_per_cell as F-AXIS-MECHANISM sub-check. *Status*: codified into `feedback_v1_abs_pnl_weighting_structural.md` at this Phase 8 closeout.

---

## 9. Path Forward (verbatim from Critic Phase 7.5)

Cycle-3 §0.6 rotation discipline (prior 5: risk-primitive ×2, methodology-substrate-test ×2, labeling ×1; cycle-3 #1 sample-weighting NEW — now closed):

1. **Universe expansion** — `universe` family (UNUSED since /006; never tested in cycle-2 or cycle-3). Add 1-2 symbols from V1_EXCLUDED_SYMBOLS (SOLUSDT preferred for cycle-2 OOS-rich profile non-correlated-with-BTC; XRPUSDT alternate). 6-symbol universe at ENSEMBLE_SIZE=3 + n_trials=18 estimated 1.7-1.8h. Mechanism: dilute ETH's catastrophic weight in portfolio Sharpe denominator AND test whether basin-lock is universe-bound vs regime-bound. **PRIMARY** per LM Master Phase 7.4 §6.

2. **Model architecture (XGBoost)** — `model-arch` family (UNUSED in v1; matches v3/016 axis priority precedent). Head-to-head LightGBM vs XGBoost on identical V1_FEATURE_COLUMNS_PRUNED + abs_pnl weighting baseline. Deferred to /018+ per user XGBoost-slower flag; needs wall-clock smoke test characterization first. SECONDARY.

3. **ETH-specific regime kill switch / per-symbol drawdown brake** — `risk-primitive` family-variant. IF /017 universe expansion does NOT reshape ETH drag, /018 pivots to ETH-conditional kill (regime-bound gate, NOT threshold-tuning). TERTIARY — conditional on /017 outcome.

---

## 10. Artifacts on Branch

- `comparison.csv` — IS/OOS metrics + n_eff_per_cell_median + r5 fire rates
- `f_axis_mechanism.csv` — 205-cell Kish n_eff and per-symbol weight shares (uniform = 1.0 / 0.5 / 0.5 by construction)
- `in_sample/dsr.json`, `in_sample/per_symbol.csv`, `in_sample/trades.csv`, `in_sample/monthly_pnl.csv`, `in_sample/quantstats.html` + ic_matrix, adf_test, per_regime
- `out_of_sample/...` symmetric set
- `briefs-v1/iteration_v1-016/research_brief.md`, `lgbm_advisor.md` (Phase 4.5 + Phase 7.4), `phase5p5_gate.md`, `critic_preflight.md`, `review.md`
- HEAD at Phase 7 (this commit): TBD — `docs(iter-v1/016): QR Phase 7 evaluation + engineering report (5th-strike fix)`

---

## 11. Trunk merge

**NONE.** EXPLORATION-NEGATIVE catastrophic never updates BASELINE_V1.md. The sample-weighting axis is CLOSED at v1 for both `uniform` (tested at /016) and `uniqueness_only` (Spearman 0.997 with uniform per /016 EDA — closes by inheritance). No re-entry without explicit new evidence on weighting mechanism orthogonal to uniformization.

**Tag**: `v0.v1-016` (applied after Phase 8 closeout commit).
