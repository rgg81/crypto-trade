# LightGBM Master Advisor — iter-v1/011 — Phase 4.5 (Pre-Design)

## Context Read

- **Track**: v1
- **Baseline**: `v0.v1-baseline-corrected` (commit `f8bc12c`), IS Sharpe +0.2829 / OOS Sharpe +0.6637, 40-feature pruned set, 5-seed ensemble.
- **Prior iter /010 outcome**: EXPLORATION-NEGATIVE PROMISING-INERT-with-IS-basin-shift (LTC IS 119.84% of total PnL = textbook single-seed Optuna lottery on weight-touching axis).
- **QR's tentative axis**: R5-BINARY-KILL-LOW at NATR_14 < 2.0% (skip entry if low-NATR). EDA-driven inversion of the 3-way convergent NATR > 7% recommendation.
- **My track record**: 0/8 directional + 2 PARTIAL; new rule from /010 Phase 7.4: position-sizing-weight axes have HIGH basin-shift probability (40-60%) at single-seed. **This axis is NOT weight-touching** — it's a pre-entry STATELESS filter that drops samples before they reach the loss.

## Recommended Hyperparameter Direction (3 items)

### 1. Keep `n_trials=35, ENSEMBLE_SIZE=3, single-seed=42` UNCHANGED for /011
- **What**: do NOT bump any Optuna budget knob in /011; preserve EXPLORATION canonical knobs.
- **Why**: the EDA's cross-roster sign-agreement (+0.046 BASELINE, +0.115 /010-EXPLORATION at threshold 2.0%) is the strongest pre-registered signal in cycle-2 to date. Bumping n_trials would conflate axis effect with budget effect. The EDA already used the SAME budget the runner will use; cross-roster oracle is methodologically clean.
- **Expected effect**: maintains comparison fidelity against /010 + baseline; isolates the binary-kill mechanism.
- **Risk**: low.

### 2. Pre-bind `feature_fraction = 1.0` in the v1_pruned bounds profile for /011
- **What**: pin `feature_fraction=1.0` for /011 Optuna search (keep `bagging_fraction` and `bagging_freq` tunable). Currently `feature_fraction` tunable in v1_pruned profile creates an axis-orthogonal basin-shift source.
- **Why**: with 40 features and 35 trials at single-seed, allowing `feature_fraction ∈ [0.4, 1.0]` adds a hyperparameter dimension that historically (per /005-/010 IS variance) re-routes which features each cell sees. Pinning isolates the R5-BINARY-KILL axis effect from feature-subsampling lottery. This is EXPLORATION-mode isolation hygiene, sister to v3's CONFIRMATION-spec pinning.
- **Expected effect**: tighter P10/P90 OOS Δ band; reduces basin-shift probability from ~25-30% to ~15-20% for this axis class.
- **Risk**: marginally reduces ensemble diversity — defensible at EXPLORATION; revert at /012 CONFIRMATION if PROMISING.

### 3. NO `min_data_in_leaf` adjustment
- **What**: leave `min_data_in_leaf` at the v1_pruned default (current bounds).
- **Why**: R5-BINARY-KILL drops ~18% of IS training samples (per Section 2.3 oracle). The model's per-cell training row count drops from ~1240 to ~1015 per (model, month) cell. This is comfortably above any per-leaf saturation point at v1_pruned's defaults. Bumping `min_data_in_leaf` here would over-regularize the already-thinner training set.

## Recommended Feature-Engineering Direction (1 item)

### 1. NO feature changes for /011
- **What**: do NOT add or drop features. V1_FEATURE_COLUMNS_PRUNED stays at 40 columns identical to /008-/010.
- **Why**: the axis is RULE-layer (entry filter); mixing in a feature change would conflate two axes and break the cross-roster oracle prediction. If PROMISING, /012 CONFIRMATION can layer feature work; not now.

## Saturation Risks to Flag

1. **The cross-roster oracle's magnitude divergence (+0.046 vs +0.115 = 2.5× spread) is a basin-sensitivity signal, NOT independent corroboration.** Both rosters share the same NATR_14 column (a model FEATURE in v1_pruned). The /010 roster already learned a partly-different loss surface; that it ALSO produces positive oracle Δ at the same threshold is informative, but the magnitude spread says: the SIGN is robust, the MAGNITUDE will depend on which basin /011's Optuna lands in. **Predicted P50 OOS Δ ≈ +0.05 (closer to BASELINE oracle, not the optimistic /010 oracle)** because /011 will run at canonical EXPLORATION budget against the BASELINE-style hyperparameter region, NOT /010's post-basin-shifted region.

2. **F6 roster-overlap diagnostic predicted ≥75% — I expect actual ≈ 70-78%.** Binary-kill mechanically preserves 81% of trades (those above threshold); if Optuna re-optimizes substantially the post-kill training distribution, basin shift could pull overlap to 65-72%. The QR's F6 tripwire at 61% is appropriate but I'd flag 65-70% as suspicious-not-tripwire territory.

3. **Per-symbol concentration risk is asymmetric vs /010.** Per Section 2.4: kill_low at 2.0% removes the BCH-equivalent loser cluster on ETH (2.5-3 bucket, -7.65 weighted PnL), LTC (<2.5 + 2.5-3, -8.19 total), DOT (2.5-3, -7.12). These three symbols are the systematic OOS LOSERS in baseline. **The OOS gainer asymmetry is therefore likely ETH/LTC/DOT-led, NOT LTC-led** like /010 was — different concentration pattern. F3 IS Δ in the OVERSHOOT-FLAG band (+0.05 to +0.30) remains plausible at ~20-25% probability.

## What I Did NOT Recommend, and Why

I did NOT recommend tightening `num_leaves` upper bound or `max_depth` upper bound. Rationale: the binary-kill primitive doesn't increase per-tree complexity demands; the 40-feature × ~225 rows-per-cell × 35-trial budget is already well-matched. Bumping anything here would obscure the axis effect.

I did NOT recommend running a parallel multi-seed validation alongside the single-seed /011. Rationale: HIGH-RISK pre-commit (Section 2.5) already covers this — IF PROMISING, /012 fires at multi-seed CONFIRMATION-spec. Pre-running multi-seed at /011 would consume compute that's better deployed AFTER the verdict-class is known.

I did NOT recommend changing `early_stopping_rounds` — the Critic Path Forward Option 3 (per-cell early-stop with inner hold-out) is the proper methodology axis for that, and is correctly deferred to /012/013 if /011 is NEGATIVE.

## Basin-Shift Probability Estimate for Entry-Filter Axis (v1-only, NEW calibration)

My /010 Phase 7.4 rule: position-sizing-weight axes → 40-60% basin-shift at single-seed.

**For STATELESS entry-filter axes (R5-BINARY-KILL class), my prior is 20-30% basin-shift.** Three reasons it's lower than weight-touching:

1. **No multiplicative loss interaction**: the entry filter drops samples BEFORE the GBM loss sees them. The retained samples enter the loss with their ORIGINAL weight (no scale modification). The loss surface basin is unchanged within the retained sample space.
2. **Mechanical roster-preservation floor of 81-82%**: 18% of samples are deterministically dropped (NATR < 2.0% = data-deterministic). The remaining 82% have UNCHANGED features, labels, and weights vs baseline. Optuna's gradient signal on the 82% retained samples is qualitatively the same shape as baseline's gradient — only the per-cell sample count drops.
3. **Empirical /008 precedent**: methodology axes (PCA, walk-forward) produced byte-identical predictions when the mechanism didn't touch the loss directly. R5-BINARY-KILL is closer to /008 than to /010 in that taxonomy.

**This raises my modal-outcome prediction**: PROMISING (OOS Δ ∈ [+0.05, +0.12]) at ~45% probability, PROMISING-INERT at ~30%, OVERSHOOT-FLAG at ~15%, NEGATIVE at ~10%. Verdict-class HIGH confidence; signed-magnitude LOW confidence.

## Specific /011 Risks

- **Catastrophic IS overshoot (like /010 LTC 119.84%)**: low probability ~15%. Mechanism asymmetry — kill_low removes losers symmetrically across ETH/LTC/DOT (not concentrating on one symbol), so the LTC-style 24× multiplicative move is unlikely. If F3 fires, more likely to land in OVERSHOOT-FLAG (+0.05 to +0.30) than catastrophic (>+0.30).
- **Per-symbol oracle gain attribution**: per Section 2.4, the largest oracle-delta sources are ETH (eliminating the 2.5-3 bucket -7.65) and DOT (eliminating 2.5-3 bucket -7.12). Both have low base-rate concentration in baseline. /011 OOS gainers should be **ETH and DOT-led, NOT LTC**.
- **Skip-entry semantics**: brief Section 3.1 places the R5-BINARY-KILL block BEFORE cooldown / vt_scale / R2 (correct). The filter fires PRE-loss; Optuna trains on the filtered training roster (the kill is a deterministic data filter, not a post-hoc trade filter). This means Optuna's CV objective DOES see a different training distribution per cell — but only via deterministic sample drop, not via re-weighted loss.

## /012 Pre-Stage Conditional on /011 Outcome

- **PROMISING (OOS Δ ≥ +0.05)**: /012 = multi-seed CONFIRMATION-spec of R5-BINARY-KILL with `min_pct ∈ {1.75, 2.0, 2.25}` 3-point ablation at ENSEMBLE_SIZE=10 + 10 outer seeds × n_trials=50. Per HIGH-RISK pre-commit (Section 2.5).
- **PROMISING-INERT (OOS Δ ∈ [-0.05, +0.05])**: binary-kill 2.0% subtype CLOSED at single-seed. /012 must pivot to UNUSED family. Recommended: **labeling axis (Critic Path Forward Option 2, triple-barrier σ_t source)** OR **per-cell early-stop methodology (Option 3)**. Defer model-arch (XGBoost head-to-head) to /013+ since v1 cycle-1 already tested LightGBM-vs-XGBoost variants.
- **OVERSHOOT-FLAG (IS Δ ∈ (+0.05, +0.30], OOS in INERT band)**: per Critic Rec #1 — treat as /010-clone. NOT a multi-seed re-test candidate; pivot to UNUSED family at /012. The OVERSHOOT-FLAG class is informationally a "single-seed basin lottery confirmation" finding, NOT an axis-worth-multi-seed signal.
- **NEGATIVE (OOS Δ < -0.05)**: both binary-kill AND proportional-scaling R5 subtypes CLOSED at v1 single-seed. ENTIRE risk-primitive family CLOSED at v1 single-seed EXPLORATION. /012 MUST pivot to labeling, methodology, or universe — not risk-primitive.
- **NEGATIVE-mis-calibrated (F2 OOS fire rate < 5% or > 60%)**: re-calibrate threshold ∈ {1.5, 2.5} at /012 (same family, parameter region shift); no other family change.

## Honest Confidence

**Verdict-class HIGH confidence**: I have ~80% confidence the verdict will land in {PROMISING, PROMISING-INERT, OVERSHOOT-FLAG} — the three "axis fires and produces non-catastrophic outcome" classes. NEGATIVE / NEGATIVE-catastrophic combined ≤ 20%.

**Signed-magnitude LOW confidence**: my /010 Phase 7.4 modal-outcome miss on basin-shift was 3-4× off; I'm not going to anchor /011 on a specific Δ point estimate. P50 ≈ +0.05 (closer to BASELINE oracle); P10/P90 width ~0.30 (QR's 0.45 width is more conservative — defensible).

**Single most important non-ignorable point**: the EDA inversion is mechanistically sound (high-NATR entries are confidence-gated to high-conviction winners; low-NATR entries are mean-reverting noise — a textbook signal-to-noise inversion). The /010 candle-level p90 = 6.3% vs entry-time-conditional p90 = 4.30% mismatch is the structural insight; the convergent 3-way recommendation was wrong because we all anchored on candle-level distribution without confidence-gate conditioning. **Per THE PRIME DIRECTIVE, the QR was right to invert. I was wrong at /010 Phase 7.4; the EDA-discovered axis is the live experiment.**

---

# LightGBM Master Advisor — iter-v1/011 — Phase 7.4 (Post-Mortem)

## Context Read

- **Headline (verified)**: IS Sharpe +0.7678 (Δ +0.4849), OOS Sharpe +1.0709 (Δ +0.4072), OOS/IS = 1.395 (anti-overfit), 180 OOS trades, R5-BINARY-KILL fire rate IS 18.3% / OOS 21.7% (F2 in-band).
- **F6 BASELINE-roster overlap = 16.7%** (30 / 180) — well below 61% tripwire, catastrophic basin shift on paper.
- **F6 vs /010-roster = 93.3%** (168 / 180) — mechanically near-identical to /010's basin minus ~12 trades.
- **LTC IS roster basin /010 vs /011 = 93.3%** (97 / 104 LTC IS trades) — Optuna found the SAME LTC basin both runs. vs BASELINE LTC IS = 22%.
- Brief Section 1 hypothesis: kill_low @ 2.0% removes ETH/LTC/DOT 2.5-3 loser cluster; predicted OOS Δ +0.05 to +0.12.

## 1. Verdict-Class Call + Dual-Firing Resolution

Pre-registered dual: F1 PROMISING (OOS Δ +0.41) AND F3 catastrophic-basin-shift (IS Δ +0.48 > +0.30). **My call: `PROMISING-with-OVERSHOOT-SUBTYPE` (compound)**, NOT pure PROMISING and NOT pure OVERSHOOT-FLAG.

The compound classification is the only honest read. F6 vs baseline at 16.7% is mechanically incompatible with "the R5-BINARY-KILL primitive doing the work" — a primitive that drops 18% of trades should preserve ~82% of the baseline roster (Section 4 F6 tripwire calculus). Instead /011 retains 93% of /010's basin and only 17% of baseline's. The IS Δ +0.48 is NOT mechanical loser-cluster removal; it's the **same single-seed=42 Optuna basin /010 found**, this time delivered by an axis whose post-kill training distribution happens to lock onto a positive-OOS-transfer region.

The OOS Δ +0.41 is real — but the mechanism is not what the brief hypothesized. The OVERSHOOT-FLAG class was pre-registered for IS-overshoot + OOS-INERT; we got IS-overshoot + OOS-confirmed. The brief did not pre-register this cell because no one expected it. Verdict subtype must explicitly note: **the axis WORKED but for the wrong reason** — basin lottery that landed positive instead of negative.

## 2. Calibration Update — The /010+/011 Twin Basin

**Hypothesis confirmed with quantitative evidence**: Optuna at single-seed=42 + n_trials=35 + ENSEMBLE_SIZE=3 + V1_FEATURE_COLUMNS_PRUNED finds a STRUCTURAL LTC-dominated basin whenever any non-trivial axis fires. LTC IS roster overlap /010↔/011 = 93.3%; baseline↔/011 = 22%. IS Δ ≈ +0.48 in BOTH /010 (proportional R5) and /011 (binary kill) is the SAME basin re-discovered by Optuna under different axis primitives.

The structural pattern distinguishing /011-OOS-transfer from /010-OOS-cancel:

| Property | /010 | /011 |
|---|---|---|
| IS Δ | +0.47 | +0.48 |
| LTC IS pct | 119.83% | 106.48% |
| LINK OOS pnl | +80.92 | +84.86 |
| BTC OOS pnl | +44.88 | +51.28 |
| LTC OOS pnl | **−43.52** | **−19.12** |
| ETH OOS pnl | **−11.36** | **−2.90** |
| OOS Δ vs baseline | −0.03 | **+0.41** |

The LTC IS basin is the same; the OOS difference is that /011's entry filter mechanically removed ~12 of the worst low-NATR LTC/ETH OOS trades that /010 still entered. **The kill_low DOES do mechanical work — just not in the direction the brief hypothesized**. It's not "the basin transfers OOS in /011 but cancels in /010". It's: **both runs have the same basin; /011 adds a small downstream OOS-cleanup filter on top of the basin**.

This is structurally `PROMISING-MECHANICAL` (v3 subtype): the lift is mechanical drag-removal layered on a basin-lottery substrate. The basin-lottery cannot be repeated at multi-seed; the drag-removal might.

## 3. Per-Symbol Concentration Triage

**LTC IS 106.48%** — second consecutive iteration of LTC dominating IS at single-seed=42. With 93.3% roster overlap to /010, this is no longer a "fragile basin" hypothesis — it's a **confirmed structural property of (seed=42, 40-feature pruned, n_trials=35)**. Dissolves at multi-seed. Non-stationary across seeds; do not interpret as edge signal.

**BTC OOS 17 trades / WR 70.6%** — 12 wins / 5 losses. F2.5 should NOT formally fire (35.80% concentration is below the 30% cap nominally but borderline; trade count 17 is below the "≥10 trades/symbol/month" credibility floor when normalized to ~14 OOS months → 1.2 trades/month BTC). The Q1 2026 BTC trade cluster is a 3-month regime concentration; if Q1 2026 happens to be a BTC short-trending regime, the 11 shorts hitting could be REGIME ALPHA rather than persistent edge. This is the single most overfit-vulnerable cell in /011. Critic should investigate.

**LINK OOS 59.24%** — but +84.86 vs baseline +34.23 = +50.6 lift. LINK OOS in /010 was +80.92; /011 is +84.86 = +5% incremental from /010 → /011. This is NOT new LINK signal; **LINK leadership was already a /010 property**. Genuine new signal claim refuted.

Net concentration verdict: **all three "extreme" concentrations are inherited from /010's basin**. The only differential vs /010 is BTC reduced from 38 to 17 trades while improving WR 44.7% → 70.6% (kill-low removed BTC's losers selectively). This IS the only mechanism-attributable effect.

## 4. HIGH-RISK Pre-Commit vs 10:1 Cadence

**Original recommendation: Option (c) — `PROMISING-MECHANICAL VALIDATION` run at multi-seed=3-5 inner × n_trials=35** based on structural reasoning (basin dissolution test).

**Orchestrator override**: Option (c) is invalidated by user-stated non-negotiables in `feedback_long_run_caution.md` (2h EXPLORATION cap; ENSEMBLE_SIZE=3 EXPLORATION-only) + `feedback_v1_seed_count_non_negotiable.md` (3 inner seeds for EXPLORATION; 10 for CONFIRMATION only). At 3 inner seeds × n_trials=35, wall-clock at ~3h exceeds 2h cap; at ENSEMBLE_SIZE=5, violates seed-count rule.

**Default to Option (a)**: /012 = EXPLORATION (cycle-2 #7), CONFIRMATION at /015 (cycle-2 #11). HIGH-RISK pre-commit in brief Section 2.5 is honored conceptually but timing deferred to /015. Per the cadence non-negotiable, the basin-dissolution test happens at /015 multi-outer-seed CONFIRMATION.

## 5. PSR_monthly_vs_1 = 0.566 — Credible CONFIRMATION Candidate?

**No — basin lottery doubt swamps the PSR signal.** PSR=0.566 means 57% probability OOS Sharpe ≥ 1.0 IF you treat the observation as a single-draw from a stationary distribution. The /011 OOS is NOT a single draw from a stationary distribution; it's a draw from the **(seed=42, n_trials=35, ENSEMBLE=3) basin lottery**. The 16.7% F6 baseline-overlap proves the basin assignment matters more than the axis. PSR computed on this single basin's daily/monthly returns is conditional on the basin — it cannot price the cross-seed uncertainty that produced this basin.

For a credible CONFIRMATION-candidate signal, I need ≥2 of 3 independent-seed basins clearing OOS Sharpe > +0.85. /011's PSR vs 1.0 at 0.566 is informative but not sufficient.

## 6. Critic Phase 7.5 Pre-Flags

Critic should focus on these patterns:

1. **F6 catastrophic shift**: roster overlap vs baseline = 16.7%, far below the brief's pre-registered 61% tripwire. Brief Section 8 verdict gates didn't pre-register `F6 < 61% AND F1 ≥ +0.05`. Critic should grade this pre-registration gap.

2. **LTC IS 93.3% basin overlap with /010**: the IS Δ +0.48 is NOT the binary-kill primitive's first-order effect. Same Optuna basin re-discovered.

3. **BTC OOS Feb-Apr 2026 regime concentration**: 12 of 17 BTC trades in Q1 2026; 11 of 17 are shorts. Single-regime alpha pattern — historically this is the failure mode in /005-/006. Critic should investigate.

4. **PSR_monthly_vs_1 OOS 0.566**: observation is borderline; combined with the basin-lottery substrate, the unconditional probability OOS Sharpe ≥ 1.0 is materially lower than 0.566. Critic should NOT treat PSR=0.566 as "57% confidence" without conditioning caveats.

5. **F2.5 per-symbol concentration**: LINK 59.24% OOS > 30% cap; BTC 35.80% > 30% cap. The brief did not pre-register an explicit F2.5 numerical condition in Section 8 verdict gates.

## What This Iteration Confirms / Refutes About Prior LM Master Advisory

- **Modal verdict class correct**: predicted PROMISING ~45%; actual class is `PROMISING-with-OVERSHOOT-SUBTYPE`.
- **Basin-shift probability (20-30% for entry-filter axes)**: WRONG. /011 produced 93.3% LTC IS basin overlap with /010 — the basin shift is IDENTICAL across the two mechanism classes at single-seed=42. **NEW RULE for v1 single-seed=42 calibration: ANY non-trivial axis (entry filter OR weight-touching) re-discovers the same Optuna basin**. The mechanism distinction I made was structurally wrong; the basin is seed-property-driven, not axis-property-driven.
- **OOS gainer prediction (ETH/DOT-led)**: WRONG. LINK + BTC led OOS.
- **P50 OOS Δ +0.05 prediction**: actual +0.41 — 8× under-prediction.
- Track record: 0/9 directional + 3 PARTIAL.

## Closing Note for Critic (Phase 7.5)

The smoking gun is **F6 baseline-overlap = 16.7% + LTC IS roster /010↔/011 overlap = 93.3%**. This single pair of numbers reframes the verdict from "axis edge found" to "single-seed basin lottery + small mechanical OOS cleanup". The Critic's 8-check verdict should NOT BLOCK on this — the OOS Δ +0.41 is real and clears the +1.0 OOS Sharpe floor — but the multi-seed durability question is the binding-constraint for treating /011 as merge-track.

Catalog should record /011 as a **NEW v1 verdict subtype**: `PROMISING-OVERSHOOT-BASIN-INHERITED` — distinct from /010's PROMISING-INERT-with-IS-basin-shift in that the basin transfers to OOS. The two iterations together establish the rule: at v1 single-seed=42, the (LTC, n_trials=35, 40-feature) basin is stable across axis primitives; the differential is whether the axis mechanically cleans up downstream OOS drag. Future v1 EXPLORATIONs cannot anchor on single-seed Sharpe-Δ as edge signal — only on **multi-seed dissolution test** at /015 CONFIRMATION.
