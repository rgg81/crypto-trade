# Iteration iter-v3/052 — Diary

## Decision: EXPLORATION-NEGATIVE (PATH C-suspicious) — regime_momentum_signed_3d UNIVERSAL SWAP saturation-INERT at single-seed n_trials=35; IS-OOS daily Sharpe ratio 2.327 OUT-OF-BAND fires LOCKED Section 8 PATH C-suspicious trigger; regime_momentum family EXHAUSTED at universal single-seed EXPLORATION scope; cycle 4 #2 of 10

iter-v3/052 = **cycle 4 #2 of 10** EXPLORATIONs post-iter-v3/051 EXPLORATION-NULL-RESULT closeout. **PIVOTED axis** from orchestrator-mandated LDO removal + fracdiff drop (TWO-VARIABLE bundle) — pre-falsified by QR EDA at SHA `0a10581` — to QR-EDA-backed `regime_momentum_signed_3d` UNIVERSAL SWAP (replaces `fracdiff_d05_close` in 15th slot of `V3_FEATURE_COLUMNS_TOP_N`) per /051 EDA RANKED #2 at SHA `290f37b`. SINGLE-AXIS SWAP: net feature count UNCHANGED at 15; V3_MODELS UNCHANGED (3-sym BCH+LDO+TRX); REQUIRED_GAP UNCHANGED (66). Run spec: `--seeds 1 --n-trials 35 --clean-oof` (EXPLORATION-spec; 525 total Optuna trials = 3 syms × 5 inner × 35).

Result: **IS single-seed Sharpe +0.5161 / OOS single-seed Sharpe +1.4295 (seed 42); IS-OOS daily Sharpe ratio 2.3267.** Per the brief Section 8 pre-registered 5-path criteria (LOCKED at brief commit), **PATH C-suspicious fires unambiguously** — IS-OOS daily ratio 2.327 is OUT-OF-BAND of [0.5, 2.0] by 0.327. Per Critic FINAL `34cc46f`:

- PATH A (PROMISING-clean): IS Δ = +0.006 (FAIL ≥+0.05); min rank 14/15 (FAIL ≤10); ratio 2.33 (FAIL band) → NO
- PATH B (PROMISING-INERT): rank ≥14/15 ALL syms (FIRES); |OOS Δ| = 0.924 (FAIL ≤0.30) → NO
- PATH C-clean: IS Δ +0.006 / OOS Δ +0.924 both positive (FAIL conditions) → NO
- **PATH C-suspicious: IS-OOS daily ratio 2.3267 OUT-OF-BAND [0.5, 2.0] → FIRES UNAMBIGUOUSLY**
- PATH D (NULL-RESULT): OOS Δ +0.924 outside (-0.20, +0.20) (FAIL) → NO

**Mechanism (Critic Adversarial Findings #1-3 SHA `34cc46f`):** regime_momentum_signed_3d ranks 14/15 (BCH), 15/15 (LDO), 15/15 (TRX), 15/15 (portfolio) — dead-last or near-dead-last across all symbols. PATH B INERT rank criterion fires across the board. The OOS spike (+0.924 Δ vs /028 anchor) on a feature ranked 15/15 cannot mechanistically attribute to the 3d feature's signal contribution. TRX OOS WR jumped 41.3% → 52.5% on 40 trades — the largest single-symbol WR lift in v3 EXPLORATION history — on a feature that ranks 15/15 for TRX. Tree models cannot manufacture +11pp WR lift from a feature with dead-last split contribution; the lift must come from a different Optuna hyperparameter draw on the 14 base features. CPCV path distribution IDENTICAL to /051 (29/45 positive, median +0.335 to 4 decimals) confirms the OOS spike is OOS-window-localized artifact, NOT broadly distributed cross-path improvement.

**Sister-stacking displacement finding (Critic Adversarial Finding #2):** The 3d ↔ 5d pairwise IC at runtime = 0.4446 — BELOW the 0.50 stacking-risk threshold from iter-v3/026 anti-pattern (`feedback_v3_engineered_features_dont_stack.md`). The brief argued IC 0.43-0.47 was below this protective threshold. **The observed displacement falsifies the threshold's protective claim for sister features**: 5d rank /051 14-15/15 → /052 11-13/15 (RECOVERED 2-3 ranks); 3d rank /052 14-15/15 (DEAD-LAST except BCH at 14). Optuna at n_trials=35 single-seed allocated split budget to ONE of the two regime_momentum variants. Same-family sister-feature competition occurred at moderate IC (0.44), not at the high-IC level where the original /026 rule was framed.

**regime_momentum family EXHAUSTED at universal single-seed EXPLORATION scope.** One CONFIRMATION-MERGE edge (5d at /028 baseline) + zero further universal lifts. The 3d UNIVERSAL axis is CLOSED for cycle 4 per pre-registered Section 7 PATH C-suspicious action: "CLOSE 3d UNIVERSAL axis; document anti-pattern at single-seed engineered feature SWAP; pivot to /053 axis."

Wall-clock: 1.25h (well within 2h EXPLORATION cap). 12/12 standard methodology checks PASS per Critic FINAL `34cc46f` (look-ahead, embargo, IC, ADF, hypothesis-implementation alignment, library pinning, etc.). No tag issued (EXPLORATION).

**Memory rule update applied at orchestrator level**: `feedback_v3_engineered_features_dont_stack.md` EXPANDED 2026-05-11 (iter-v3/052 Critic `34cc46f`) to cover SAME-FAMILY sister stacking at ANY IC. Previously framed around two DIFFERENT engineered features at high IC; /052 evidence shows displacement at moderate IC 0.44 between two sister composed features (`ret_3d × sign(hurst − 0.5)` vs `ret_5d × sign(hurst − 0.5)`). The IC threshold is necessary but not sufficient.

## PIVOT History

**Original orchestrator pick (committed at brief SHA `87e070b`):** TWO-VARIABLE axis bundle:
- DROP LDOUSDT from V3_MODELS (3 → 2 symbols: BCHUSDT, TRXUSDT)
- DROP fracdiff_d05_close from V3_FEATURE_COLUMNS_TOP_N (15 → 14)
- REQUIRED_GAP recompute 66 → 44 = (21+1)×2
- Stated premise: "LDO IS PnL share -14.96% at /051 (drag at IS too)"; "LDO OOS weighted_pnl -17.44 (drag at OOS)"

**QR EDA at SHA `0a10581` (`analysis/iteration_v3-052/ldo_removal_eda.py` + 7 CSVs + synthesis.md):** Pre-falsified the orchestrator premise.

### Premise inversion: net_pnl_pct vs weighted_pnl

The orchestrator's "LDO IS PnL share -14.96%" reading sourced `per_symbol.csv:net_pnl_pct` (sums per-trade raw % returns; IGNORES weight_factor). The Sharpe-relevant metric is `weighted_pnl` (weight_factor × pnl_pct).

| Window | LDO trades (wf>0) | LDO weighted_pnl | wpnl share | LDO WR |
|---|---:|---:|---:|---:|
| IS at /051 | 9 of 11 raw | **+11.155** | **+36.78%** | 33.3% |
| OOS at /051 | 13 of 13 raw | **−17.44** | **−100.08%** | 23.1% |

LDO is an IS CONTRIBUTOR at /051 (+36.78% bundle share, dominated by 3 large take-profit exits) and an OOS DRAG (−100.08% share, 10 SLs vs 3 TPs). The premise inversion was: LDO IS = CONTRIBUTOR, not drag.

### 2-sym counterfactual triggers PATH C-suspicious by construction

| Scenario (from /051 trade roster) | IS Sharpe | OOS Sharpe | IS-OOS daily ratio |
|---|---:|---:|---:|
| 3-sym /051 actual (BCH+LDO+TRX) | +0.4571 | +0.5890 | 1.06 (in-band) |
| 2-sym counterfactual (drop LDO) | +0.2960 | +1.6030 | **3.58 (OUT-OF-BAND)** |
| **Δ (no_LDO − with_LDO)** | **−0.1611** | **+1.0139** | — |

LDO removal: IS Δ **−0.16** (BREAKS BOTH-must-improve gate per `feedback_v3_strict_both_is_oos_baseline.md`); IS-OOS daily ratio **3.58 OUT-OF-BAND** (PATH C-suspicious anti-pattern per `feedback_v3_engineered_features_dont_stack.md`). Structurally identical to per-symbol customization anti-pattern (`feedback_v3_per_symbol_lifts_oos_breaks_is.md`) applied at universe-composition level.

The orchestrator's mandate would have consumed a cycle 4 EXPLORATION slot to mechanically re-confirm an anti-pattern at universe-composition level (zero learning signal beyond confirming what the EDA counterfactual already predicted).

### PIVOT to QR-EDA-backed axis

Per `feedback_v3_axis_selection_quant_discipline.md` rule 2 (sentence 3): "If the orchestrator commits a setup commit ad-hoc, QR must REWRITE the brief and REVERT the setup commit when EDA fails to support it." The PIVOT was mandated, not optional.

QR re-selected from /051 EDA RANKED #2 at SHA `290f37b` (synthesis.md §c3 + candidate_axes_ranking.md §Candidate 2): **regime_momentum_signed_3d UNIVERSAL SWAP** (replace fracdiff_d05_close at 15th slot). EDA backing:

- ADF stationary p=0 ALL 4 syms (axis_c_regime_3d_adf.csv)
- Max |IC| = 0.6192 < 0.70 strict gate; NO carve-out needed
- Univariate ρ significant at ALL 4 syms (mean -0.057; STRONGER than fracdiff -0.044)
- IC with sister 5d feature 0.43-0.47 (moderate; BELOW 0.50 stacking-risk threshold)
- /044 ALGO LONG falsification CONDITIONAL on ALGO universe; ALGO REVERTED at /051+
- compute function existed as dead code (engineered_v3.py:330-376; 1-line dispatch reactivation)
- Same proven family as iter-v3/028 baseline edge ingredient regime_momentum_signed_5d

The /052 PIVOT brief at SHA `41ff0b8` SUPERSEDES the original brief at SHA `87e070b`. Per `feedback_v3_axis_selection_quant_discipline.md` rule 4, Section 10 QR Audit Trail was added documenting the supersession with SHAs for EDA, original brief, and rewritten brief.

## What Was Tested

**Hypothesis (locked in PIVOT brief Section 1):** "ADDING `regime_momentum_signed_3d` to V3_FEATURE_COLUMNS_TOP_N at universal scope (SWAP with fracdiff_d05_close; net count stays 15) — alongside the system-level REVERT carry-forward (3-sym BCH+LDO+TRX, V3_ATR_MULTIPLIERS_PER_SYMBOL = {}, block_long_for = (), REQUIRED_GAP = 66) — investigates whether the orthogonal time-scale variant of the iter-v3/028 edge ingredient regime_momentum_signed_5d captures shorter-horizon (3-bar = 1-day at 8h cadence) regime persistence that the 5-bar variant misses, lifting bundle IS Sharpe vs iter-v3/028 baseline reference +0.5101 while preserving OOS Sharpe ≥ +0.5053."

**Predicted bands (PIVOT brief Section 4):**
- IS Sharpe: +0.58 ± 0.18 (band [+0.40, +0.75]; Δ vs /028 anchor: [-0.10, +0.25])
- OOS Sharpe: +0.55 ± 0.30 (band [+0.25, +0.85]; Δ vs /028 anchor: [-0.25, +0.35])
- IS-OOS daily Sharpe ratio: 1.05 ± 0.45 (band [0.60, 1.50])
- 3d importance rank: top-10 in at least 1 of 3 syms

**Spec (locked in PIVOT brief Section 0.5; setup commit SHA `4cf49e5`):**
- ITERATION_LABEL = "v3-052"
- V3_FEATURE_COLUMNS_TOP_N = 15 features (SWAP 15th element: DROP fracdiff_d05_close; ADD regime_momentum_signed_3d)
- V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols UNCHANGED from /051
- V3_ATR_MULTIPLIERS_PER_SYMBOL = {} UNCHANGED
- block_long_for = () UNCHANGED
- REQUIRED_GAP = 66 = (21+1)×3 UNCHANGED (universe unchanged)
- regime_momentum_signed_5d PRESERVED (iter-v3/028 edge ingredient)
- compute_regime_momentum_signed_3d ACTIVATED from dead code (engineered_v3.py:330-376; 1 dispatch line added)
- compute_fracdiff_d05_close + 5 adversarial tests RETAINED as dead-code (zero revert cost)
- 5 NEW adversarial tests in `tests/features_v3/test_regime_momentum_signed_3d_universal.py` PASS
- Runner: `uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof`
- ENSEMBLE_SIZE = 5 (auto inner ensemble); outer_seeds = 1 (EXPLORATION-spec)
- Wall-clock: 1.25h (within 2h cap)
- Total Optuna trials: 525 = 3 syms × 5 inner × 35

## Headline Numbers

### Single-seed primary (comparison.csv + seed_summary.json; seed 42 only)

| Metric | iter-v3/028 BASELINE (multi-seed mean) | iter-v3/051 (1-seed) | **iter-v3/052 (1-seed)** | Δ vs iter-v3/028 | Δ vs iter-v3/051 |
|---|---:|---:|---:|---:|---:|
| **IS monthly Sharpe** | +0.5101 | +0.4506 | **+0.5161** | **+0.0060** | **+0.0655** |
| **OOS monthly Sharpe** | +0.5053 | +0.5891 | **+1.4295** | **+0.9242** | **+0.8404** |
| **IS daily Sharpe** | — | +0.9685 | **+1.1692** | — | +0.2007 |
| **OOS daily Sharpe** | — | +1.1116 | **+2.7204** | — | +1.6088 |
| **IS-OOS daily Sharpe ratio** | 0.99 | 1.148 (in-band) | **2.3267 (OUT-OF-BAND)** | exits band | +1.179 (exits band) |
| IS Trades | 156 (mean) | 178 | 188 | +32 (+20.5%) | +10 (+5.6%) |
| OOS Trades | 95 (mean) | 96 | 93 | -2 (-2.1%) | -3 (-3.1%) |
| IS MaxDD | 41.43% | 37.37% | 32.58% | -8.9pp better | -4.8pp better |
| OOS MaxDD | 23.53% | 32.75% | 30.42% | +6.9pp worse | -2.3pp better |
| OOS Calmar | 0.92 | 0.53 | 1.4728 | +0.55 | +0.94 |
| OOS Top concentration (BCH wpnl) | 76.47% (TRX) | 67.65% (BCH) | **74.58%** (BCH) | -1.9pp | +6.9pp |
| DSR | 0.0 (structural at /028 multi-seed) | 0.0 (structural) | 0.0 (structural at n_trials=525) | structural artifact | structural |
| PBO | 0.1243 | 0.1168 | **0.1090** | -0.015 | -0.008 |
| frac_positive_paths | 0.644 | 0.644 | **0.644** | identical | identical |
| Median path Sharpe | +0.335 | +0.3350 | **+0.3351** | identical | identical (4 decimal places) |
| PSR | 1.0 | 1.0 | **1.0** | saturation | saturation |
| n_trials | 1050 | 525 | 525 | EXPLORATION spec | EXPLORATION spec |
| n_eff | 19 | 19 | 19 | within range | within range |

**Critical observation:** CPCV path distribution is BIT-IDENTICAL to /051 (29/45 positive paths, median Sharpe +0.335 to 4 decimal places) DESPITE the +0.84 OOS monthly Sharpe jump. This confirms the +0.92 OOS Δ vs /028 anchor is NOT broadly distributed across CPCV paths — it is concentrated in the OOS window where seed=42 produced a favorable BCH+TRX win-rate cluster.

### Per-symbol decomposition (seed 42)

**IS per-symbol:**

| Symbol | trades | win_rate | net_pnl_pct | avg_pnl_pct | pct_of_total_IS_pnl |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 97 | 39.2% | +24.81% | +0.256% | **+62.46%** |
| LDOUSDT | 15 | 40.0% | +24.34% | +1.623% | **+61.26%** |
| TRXUSDT | 76 | 32.9% | -9.42% | -0.124% | **-23.72%** |

BCH carries +62% of IS PnL; **LDO IS recovered to +61% bundle share at 40.0% WR** (vs /051's 27.3% WR / -14.96% share). TRX IS regressed to -23.72% bundle share (vs /051's +10.91%). This is a reversal of /051's IS attribution pattern — driven by Optuna re-tune after the SWAP. The /052 IS LDO recovery is consistent with the EDA hypothesis that fracdiff (parked at /052) was contributing to LDO's IC-collinearity confusion at /051 (axis_c_fracdiff_per_sym_ic.csv showed LDO IC vs vwap_dev_20 = 0.7381).

**OOS per-symbol:**

| Symbol | trades | win_rate | weighted_pnl | net_pnl_pct | concentration_pct |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 39 | 46.2% | **+33.42** | +41.06% | +74.58% |
| TRXUSDT | 40 | **52.5%** | **+25.35** | +32.31% | +56.58% |
| LDOUSDT | 14 | 28.6% | **-13.96** | -18.66% | -31.16% |

BCH OOS drives +74.58% concentration (still well above 30% aspirational gate). TRX OOS WR 52.5% (HIGHEST single-symbol WR in v3 EXPLORATION history) drove the OOS Sharpe spike. **LDO OOS still negative at -13.96** (vs /051's -17.44; slight improvement of +3.48 units in larger positive total). LDO OOS WR 28.6% (vs /051 23.1%) — marginal improvement but still firmly in the below-50% drag territory.

### §8 Pre-registered Path Verdict (mechanical, non-renegotiable)

| Path | Trigger | Observed | Fired? |
|---|---|---|---|
| PATH A (PROMISING-clean) | IS Δ ≥ +0.05 AND OOS Δ ≥ -0.20 AND ratio ∈ [0.5, 2.0] AND rank ≤ 10 in ≥1 sym | IS Δ +0.006 FAIL ≥+0.05; min rank 14 FAIL ≤10; ratio 2.33 FAIL band | NO |
| PATH B (PROMISING-INERT) | rank ≥ 14/15 ALL 3 syms AND \|IS Δ\| ≤ 0.10 AND \|OOS Δ\| ≤ 0.30 | rank FIRES; \|OOS Δ\| 0.924 FAIL ≤0.30 | NO |
| PATH C-clean (NEGATIVE-clean) | IS Δ < -0.10 OR OOS Δ < -0.30 with ratio ∈ band | IS Δ +0.006 / OOS Δ +0.924 both positive | NO |
| **PATH C-suspicious** | **IS-OOS daily ratio outside [0.5, 2.0]** | **2.3267 OUT** | **YES (unambiguous)** |
| PATH D (NULL-RESULT) | IS Δ ∈ (-0.10, +0.05) AND OOS Δ ∈ (-0.20, +0.20) AND axis LEARNED | OOS Δ +0.924 outside (-0.20, +0.20) | NO |

**PATH C-suspicious is the sole path whose conditions are met. No discretion.**

## Why PATH C-suspicious (Critic adjudication, FINAL SHA `34cc46f`)

The pre-registered Section 8 LOCKED PATH C-suspicious trigger fires unambiguously:

1. **IS-OOS daily Sharpe ratio 2.3267 OUT-OF-BAND of [0.5, 2.0] by 0.327.** The band was explicitly designed per `feedback_v3_engineered_features_dont_stack.md` to detect OOS-window-localized artifacts. The observed ratio is 16.3% above the upper bound.

2. **regime_momentum_signed_3d ranks 14-15/15 across ALL 3 symbols and portfolio (saturation-INERT).** The PATH B INERT rank criterion fires across the board. Tree models cannot manufacture +11pp WR lift for TRX from a feature with dead-last split contribution (TRX 3d rank = 15/15).

3. **TRX OOS WR jump 41.3% → 52.5% on rank-15/15 feature = Optuna hyperparameter lottery, NOT signal.** The lift must come from a different Optuna hyperparameter draw on the 14 base features. Per `feedback_v3_single_seed_frozen_baseline.md` REVISED: when V3_FEATURE_COLUMNS_TOP_N changes universally, per-symbol Optuna trajectories perturb — what looks like "axis lift" is search-trajectory artifact on the base 14 features.

4. **CPCV path distribution IDENTICAL to /051** (29/45 positive, median +0.335 to 4 decimal places). The 0.84 OOS Sharpe jump is NOT broadly distributed; it is concentrated in the OOS window where seed=42 hyperparameter region produced a favorable BCH+TRX win-rate cluster (May +19.47%, Jun +9.37%, Jul +9.96% three-month chain accounting for +38.80% PnL).

5. **`feedback_v3_engineered_feature_pivot.md` carve-out does NOT apply.** The carve-out relaxes the STRICT |IC|<0.50 gate for Category 2 composed features to importance ≥ 30 threshold. The PATH C-suspicious ratio-band gate has NO carve-out. The carve-out addresses the IC collinearity gate specifically, not the IS-OOS daily Sharpe ratio band.

The classification is mechanically determined by the pre-registration. No QR clarification could change the verdict without violating `feedback_no_cheating.md` post-hoc renegotiation discipline.

## Sister-Stacking Displacement Finding

**The 0.50 IC threshold did NOT protect against sister-family displacement.**

The brief argued IC 0.43-0.47 with 5d sister was below /026 stacking-risk threshold of 0.50 per `feedback_v3_engineered_features_dont_stack.md`. **The observed displacement falsifies this protective claim for sister features**:

| Symbol | 5d rank at /051 | 5d rank at /052 | 3d rank at /052 |
|---|---:|---:|---:|
| BCH | 14 / 15 | 11 / 15 | 14 / 15 |
| LDO | 15 / 15 | 13 / 15 | 15 / 15 |
| TRX | 12 / 15 | 12 / 15 | 15 / 15 |
| Portfolio | 15 / 15 | 13 / 15 | 15 / 15 |

Runtime sister IC = **0.4446** (vs EDA estimate 0.43-0.47; consistent). Optuna at n_trials=35 single-seed allocated split budget to ONE of the two regime_momentum variants. The 5d feature rose from 14-15/15 at /051 to 11-13/15 at /052, suggesting Optuna at /052 found better configurations for 5d when it no longer competed with fracdiff (which was also bottom-tier at /051). The 3d feature was inserted at the 15th slot and was immediately pushed to dead-last or near-dead-last. **Sister-stacking displacement: 5d recovered signal rank and 3d was assigned the residual importance budget.**

The colsample/split allocation is competitive across same-family features even when pairwise IC is below the redundancy-collinearity threshold. The original /026 rule was framed around two DIFFERENT engineered features (regime_momentum + vol_adj_autocorr) at higher IC. The /052 evidence shows displacement at moderate IC (0.44) when features are time-scale variants of same composition (`ret_Nd × sign(hurst − 0.5)`).

## regime_momentum Family Exhausted at Universal Single-Seed EXPLORATION Scope

One CONFIRMATION-MERGE edge (5d at /028 baseline) + zero further universal lifts:

| Iteration | Variant | Scope | Outcome |
|---|---|---|---|
| iter-v3/025 | regime_momentum_signed_5d ADD | universal | PROMISING (single-seed) |
| iter-v3/028 | regime_momentum_signed_5d (bundle ingredient) | universal | CONFIRMATION-MERGE; BASELINE_V3.md baseline edge |
| iter-v3/052 | regime_momentum_signed_3d UNIVERSAL SWAP | universal | **EXPLORATION-NEGATIVE PATH C-suspicious; CLOSED** |

The 3d UNIVERSAL axis is CLOSED for cycle 4 per pre-registered Section 7 PATH C-suspicious action: "CLOSE 3d UNIVERSAL axis; document anti-pattern at single-seed engineered feature SWAP; pivot to /053 axis."

**Family-level finding:** at n_trials=35 single-seed EXPLORATION-spec, the regime_momentum family operates as a "one-slot" signal — only ONE regime_momentum variant can be learned at a time, even at moderate IC. Multi-seed CONFIRMATION (larger Optuna budget; 2-seed averaging dissolves single-seed lottery artifacts) is the appropriate venue for testing both variants simultaneously. Cycle 4 #3 at /053 should be a DIFFERENT feature family entirely per `feedback_v3_structural_over_knob_exploration.md`.

## LDO Behavior

LDO OOS performance:
- weighted_pnl: **-13.96** (vs /051: -17.44; slight improvement of +3.48 units)
- trades: 14 (vs /051: 13 — one additional trade)
- win rate: 28.6% (vs /051: 23.1% — slight improvement of +5.5pp)
- concentration_pct: -31.16% (vs /051: -100.07% — materially less drag, but only because OOS total grew larger)

LDO OOS weighted_pnl is still negative at -13.96, but the OOS total weighted_pnl expanded to +44.80 (vs /051: +17.43), so LDO's -31.16% concentration share is a smaller fraction of a larger positive total. The slight LDO OOS improvement is within single-seed Optuna noise; it does not represent a structural shift in LDO's signal quality.

LDO IS recovery:
- iter-v3/051 IS: 11 trades, 27.3% WR, net_pnl_pct -5.99%, weighted_pnl share +36.78% (CONTRIBUTOR per /052 EDA correction)
- iter-v3/052 IS: 15 trades, 40.0% WR, net_pnl_pct +24.34%, pct_of_total_pnl +61.26%

At /052, LDO IS is positive on both raw and weighted metrics — a reversion relative to /051. The IS WR rose from 27.3% to 40.0% across 15 trades. This is consistent with the SWAP from fracdiff (which partially overlapped LDO's feature space at IC 0.7381 EDA-level) to regime_momentum_signed_3d (which has lower IC with the existing feature stack at LDO: 0.6139 vs vwap_dev_20). The SWAP reduced signal confusion for LDO IS; however the LDO OOS WR (28.6%) did not recover proportionally, confirming that LDO's OOS issue is in the OOS signal environment (2025 declining-LDO regime), not in feature collinearity. LDO's OOS structural problem persists across the feature SWAP — independent of the 15th slot content.

## Memory Rule Update (orchestrator-applied at SHA `34cc46f`)

**`feedback_v3_engineered_features_dont_stack.md` EXPANDED 2026-05-11 to cover SAME-FAMILY sister stacking at ANY IC.**

Previous formulation (from iter-v3/026):
- Rule framed around two DIFFERENT engineered features at HIGH IC
- 0.50 stacking-risk threshold for "do not stack" decision

Expansion (from iter-v3/052 Critic FINAL `34cc46f` Adversarial Finding #2):
- Sister features from same compose family (same primitive structure with different lookback) DO displace each other at single-seed EXPLORATION even at moderate IC (0.44)
- Proposed addition: "Do NOT stack two engineered features from same compose family (same primitive structure with different lookback) at single-seed EXPLORATION; defer to multi-seed CONFIRMATION."

The /052 evidence (5d rank /051 14-15 → /052 11-13 RECOVERED while 3d /052 14-15 DEAD-LAST) demonstrates same-family sister-feature competition occurs at IC below the 0.50 protective threshold from the original /026 rule. The IC threshold is necessary but not sufficient.

This is the SECOND memory rule update applied at iter-v3/052 (alongside the PIVOT documented via `feedback_v3_axis_selection_quant_discipline.md` rule 4 invocation).

## PIVOT Process Quality Assessment

Despite the PATH C-suspicious verdict, the PIVOT process execution is EXEMPLARY per Critic FINAL `34cc46f` Adversarial Finding #5:

1. **QR EDA correctly inverted the orchestrator premise** via weighted_pnl vs net_pnl_pct correction. The EDA was committed prior to the brief rewrite (SHA `0a10581`) and produced 7 CSV outputs documenting the supersession.

2. **PIVOT brief Section 10 audit trail comprehensively documents the supersession**: orchestrator's original pick (SHA `87e070b`), QR EDA backing (SHA `0a10581` + /051 EDA SHA `290f37b`), setup commit SHA (`4cf49e5`), and `feedback_v3_axis_selection_quant_discipline.md` rule 4 invocation.

3. **Pre-registered Section 8 LOCKED paths CORRECTLY anticipated PATH C-suspicious as 10% tail outcome.** Despite being the 4th-most-likely path in the predicted taxonomy (PATH B at 30%, PATH A at 25%, PATH C-clean at 20%, PATH C-suspicious at 10%, PATH D at 15%), the pre-registration LOCKED the trigger mechanically. The verdict was determined by the data, not by post-hoc adjudication.

4. **Engineering report `5eae673` applied the verdict mechanically** without discretion. The Critic Round 1 PRELIMINARY was skipped (orchestrator dispatched directly with FINAL mode) because the mechanical determination required no QR clarification.

5. **ONE-VARIABLE rule honored cleanly**: 15th slot identity change; net feature count UNCHANGED at 15; V3_MODELS UNCHANGED; REQUIRED_GAP UNCHANGED. No risk-gate threshold changes.

## Critic FINAL `34cc46f` Recommendations for /053

Per Critic FINAL `34cc46f` Recommendations §:

1. **Expand `feedback_v3_engineered_features_dont_stack.md` to cover SAME-FAMILY sister stacking at any IC.** (APPLIED at orchestrator level 2026-05-11.)

2. **regime_momentum family is exhausted at universal single-seed EXPLORATION scope.** Cycle 4 #3 should pivot to structurally distinct feature family per `feedback_v3_structural_over_knob_exploration.md`. Top recommendation: `hurst_drift_50_200` (/051 EDA candidate #4); secondary: CatBoost head-to-head (NEW model architecture per /050 Critic recommendation).

3. **Behavioral-effect predictor needs revision for SWAP axes.** Future SWAP-axis briefs Section 4.4 should add importance-rank-ONLY saturation trigger (rank ≥ N-1/N in ALL syms = saturation regardless of trade-count change), because for SWAPs the trade roster size is bounded by the unchanged 14 base features even when the swap fires INERT. The current saturation falsifier (trade count change < ±5% AND rank ≥ 14/15 ALL syms) requires BOTH conditions — for SWAPs the trade-count condition is weakly informative since base 14 features carry most of the entry/exit signal.

## CPCV Analysis

45 paths generated (REQUIRED_GAP = 66; 3-symbol universe).

| Statistic | iter-v3/052 | iter-v3/051 (reference) | Δ |
|---|---:|---:|---:|
| Paths positive | 29 of 45 (64.4%) | 29 of 45 (64.4%) | identical |
| Median path Sharpe | +0.3351 | +0.3350 | +0.0001 |
| PBO (per-cell mean) | 0.1090 | 0.1168 | -0.008 |
| Q25 path Sharpe | -0.243 | -0.243 | identical |
| Q75 path Sharpe | +0.838 | +0.884 | -0.046 |

The CPCV statistics are essentially identical between /051 and /052. The SWAP of the 15th feature (fracdiff → 3d) produced no structural change in the path-level generalization distribution. **The OOS monthly Sharpe lift (+0.84) is NOT reflected in CPCV paths** — the 45 paths sample the IS+OOS period and path Sharpes reflect the combined window where IS carries more weight. PBO = 0.1090 well below 0.40 threshold (PASS).

This is the cleanest possible demonstration that the OOS spike is an OOS-window-specific artifact, not a broadly distributed cross-path improvement. The IS-OOS daily ratio band (PATH C-suspicious trigger) is designed to catch exactly this OOS-window-localization pattern.

## OOS Monthly Profile

| Month | trades | pnl_pct | Status |
|---|---:|---:|---|
| 2025-04 | 7 | +0.31% | Positive |
| 2025-05 | 7 | **+19.47%** | Positive (large) |
| 2025-06 | 8 | +9.37% | Positive |
| 2025-07 | 11 | +9.96% | Positive |
| 2025-08 | 11 | **-13.52%** | Negative (worst month) |
| 2025-09 | 7 | +4.60% | Positive |
| 2025-10 | 13 | -6.44% | Negative |
| 2025-11 | 8 | +4.18% | Positive |
| 2025-12 | 3 | +4.11% | Positive |
| 2026-01 | 2 | +3.70% | Positive |
| 2026-02 | 4 | -2.44% | Negative |
| 2026-03 | 6 | +4.10% | Positive |
| 2026-04 | 3 | +0.91% | Positive |
| 2026-05 | 3 | +6.50% | Positive |

Positive months: 11 of 14 (78.6%). Negative months: 3 of 14 (vs /051: 5 of 14). The Q2-Q3 2025 cluster of positive months (May +19.47%, Jun +9.37%, Jul +9.96%) is the dominant OOS driver — three consecutive positive months accounting for +38.80% PnL. The worst month is 2025-08 at -13.52%. 2026 (Jan-May) is uniformly low-trade (2-6 trades/month) and mostly positive, suggesting the 3-symbol universe has fewer candidates per month in recent OOS extension.

## Gate Efficacy Table

| Gate | Parameter | Behavior at /052 |
|---|---|---|
| BTC trend filter | lookback=42, threshold=15% | 33 OOS trades killed (~26% of candidates); vs /051's 32 |
| OOD z-score gate | zscore_threshold=2.0, **15-D space** (UNCHANGED count from /051) | embedded; SWAP preserves dimensionality |
| ADX gate | threshold=20.0 global; per-symbol={} | embedded |
| Primitive 10 — BCH direction block | block_long_for=() | REVERTED at /051; UNCHANGED at /052; gate in code but not firing |
| Per-symbol ATR | DEFAULT (2.0, 1.0) all syms | embedded |
| Per-symbol cap | enable_per_symbol_cap=False | DISABLED (CLOSED per /020) |
| Regime gate | enable_regime_gate=False | DISABLED (CLOSED per /022) |

BTC trend killed 33 OOS trades (~26% of candidates) — essentially identical to /051's 32 (~25% kill rate); consistent across the SWAP.

## Bundle Status Update

- **BASELINE_V3.md UNCHANGED at iter-v3/028** (+0.5101 IS / +0.5053 OOS; SHA `b0576df`). iter-v3/052 is EXPLORATION; no MERGE gate evaluation.
- **iter-v3/028 architecture PRESERVED as cycle 4 baseline** (3-sym universe; V3_ATR_MULTIPLIERS_PER_SYMBOL = {}; block_long_for = (); REQUIRED_GAP = 66).
- **regime_momentum_signed_3d UNIVERSAL axis CLOSED** for cycle 4 per Critic FINAL `34cc46f` and pre-registered Section 7 PATH C-suspicious action. Multi-seed CONFIRMATION (iter-v3/061+) is the appropriate venue for retest where single-seed lottery artifacts dissolve.
- **regime_momentum family EXHAUSTED at universal single-seed EXPLORATION scope.** One CONFIRMATION-MERGE edge (5d at /028) + zero further universal lifts.
- **fracdiff_d05_close remains PARKED** (PARKED at /051 closeout; SWAPPED at /052 setup; compute function + 5 tests retained as dead-code coverage at zero revert cost). Status UNCHANGED.
- **regime_momentum_signed_5d PRESERVED in V3_FEATURE_COLUMNS_TOP_N.** Importance rank recovered at /052 (11-13/15 vs /051 14-15/15) when fracdiff no longer competed for bottom-tier split budget — sister-stacking displacement upside.
- **LDO removal axis DEFERRED to multi-seed CONFIRMATION** (iter-v3/061+) where single-seed lottery artifacts dissolve. EDA at /052 SHA `0a10581` pre-falsifies the axis at EXPLORATION-scope (IS Δ -0.16, ratio 3.58 OOB = PATH C-suspicious by construction).
- **Per-symbol architecture (V3_FEATURES_PER_SYMBOL + V3_ATR_MULTIPLIERS_PER_SYMBOL) PRESERVED as code infrastructure.**
- **Primitive 10 (`block_long_for`) PRESERVED as code infrastructure** — mechanism + 7 adversarial tests + GateStats counter REMAIN. Wired value `()` UNCHANGED.
- **compute_regime_momentum_signed_3d ACTIVATED in dispatch** at /052 setup (was dead code at engineered_v3.py:330-376). REMAINS in dispatch as inert column dispatch (column dropped from V3_FEATURE_COLUMNS_TOP_N at /053 setup per CLOSE 3d UNIVERSAL action; compute function + 5 tests retained as zero-revert-cost dead-code coverage).
- **NO TAG ISSUED.** EXPLORATION; only CONFIRMATION-MERGE iterations get `v0.v3-NNN` tags.

## Cycle 4 Cadence: 2/10 EXPLORATIONs advanced

Per `feedback_v3_strict_10_to_1_cadence.md`:

- **Cycle 4 #1 of 10 = iter-v3/051** (fracdiff_d05_close ADD UNIVERSAL; EXPLORATION-NULL-RESULT; PARKED)
- **Cycle 4 #2 of 10 = iter-v3/052** (regime_momentum_signed_3d SWAP UNIVERSAL; **EXPLORATION-NEGATIVE PATH C-suspicious**; CLOSED)
- **Cycle 4 CONFIRMATION at iter-v3/061** (SEPARATE single-seed iter-v3/060 first; do NOT collapse the 10th EXPLORATION into CONFIRMATION)
- **8 more EXPLORATIONs remain** before cycle 4 CONFIRMATION: iter-v3/053 through iter-v3/060
- **Cadence wall-clock caps**: EXPLORATION 2h, CONFIRMATION 6h. iter-v3/052 actual: 1.25h within cap.

**Cycle 4 hypothesis status** (carry-forward from /050 closeout): "lift IS Sharpe to ≥ +0.5101 (BASELINE_V3.md update gate floor) while preserving OOS Sharpe ≥ +0.5053 via UNIVERSAL axes (per-symbol customizations rejected at bundle level)." iter-v3/052 result: IS +0.5161 ≥ +0.5101 (clears IS floor by +0.006 — MARGINAL), but PATH C-suspicious classification (OOS-only artifact) means the lift is not signal-attributable. The cycle 4 hypothesis is NOT YET satisfied via clean PROMISING; 8 EXPLORATIONs remaining.

## iter-v3/053 Axis Priorities

Per Critic FINAL `34cc46f` Recommendation #2 + iter-v3/050 closeout HIGH-priority axis carry-forward:

### HIGH-priority axes for /053

1. **`hurst_drift_50_200` — UNTESTED engineered feature** (per /051 EDA candidate #4; carried forward from /050 + /051 closeouts)
   - Mechanism: difference of two Hurst window measurements (long-horizon 200 minus short-horizon 50); signals regime-transition speed
   - Orthogonal to regime_momentum_signed_5d (different primitive: Hurst-diff vs ret × sign(Hurst))
   - Pre-flight EDA cost: ~1.5h (compute function + 5 adversarial tests + ADF + IC + univariate Spearman + ranking)
   - Aligns with `feedback_v3_engineered_features_proven.md`: NEW composed engineered feature axis
   - Aligns with `feedback_v3_structural_over_knob_exploration.md`: Category 1 structural axis (NEW feature family)

2. **CatBoost head-to-head — NEW model architecture** (per /050 Critic recommendation, NOT-YET-EXPLORED)
   - Mechanism: replace LightGBM with CatBoost; per-symbol fit; same V3_FEATURE_COLUMNS_TOP_N
   - The iter-v3/016 LightGBM→XGBoost test was NEGATIVE clean at n_trials=10 (saturated); CatBoost has distinct optimization defaults (Ordered Boosting; symmetric trees; native categorical handling) and may behave differently
   - Pre-flight cost: ~2.5h (LightGbmStrategy → CatBoostStrategy abstraction + 5 tests + Optuna param translation)
   - Aligns with `feedback_v3_structural_over_knob_exploration.md`: Category 2 structural axis (NEW model arch)

### MEDIUM-priority axis for /053

3. **DSR gate reformulation** (deferred from /028 + /039 + /050)
   - Mechanism: replace DSR > 0.95 absolute threshold with relative DSR (rank-percentile of CPCV path Sharpes); fixes the structural DSR=0 artifact at EXPLORATION-spec n_trials=525
   - Per `feedback_v3_dsr_mode_artifact.md`: EXPLORATION-mode DSR is INFORMATIONAL ONLY; CONFIRMATION-mode DSR uses n_trials=1500 (E[max_SR]=3.37) which still doesn't clear annualized 4.0
   - Pre-flight cost: ~1.5h (DSR computation modification + Critic gate update)
   - Aligns with cycle 4 hypothesis: DSR reformulation could enable IS Sharpe +0.50 to clear MERGE gate

### LOW-priority axes (CLOSED or saturated)

4. ~~LDO removal investigation~~ — DEFERRED to multi-seed CONFIRMATION per /052 EDA pre-falsification at single-seed scope
5. ~~regime_momentum_signed_3d UNIVERSAL retest~~ — CLOSED for cycle 4 (PATH C-suspicious; family exhausted at universal single-seed scope)
6. ~~ADX gate tuning~~ — CLOSED at /015 (`feedback_v3_adx_axis_asymmetric_v3.md`)
7. ~~Per-symbol PnL caps~~ — CLOSED at /020 (`feedback_v3_concentration_is_signal.md`)
8. ~~Per-symbol ATR multipliers~~ — CLOSED at /045-/050 (`feedback_v3_per_symbol_lifts_oos_breaks_is.md`)

### Recommended /053 axis

**hurst_drift_50_200 UNTESTED engineered feature** at universal scope. Rationale:
- Lowest implementation cost (1.5h pre-flight + 1.5h backtest = within EXPLORATION 2h cap)
- Aligns with `feedback_v3_structural_over_knob_exploration.md` Category 1 (NEW feature family)
- Different primitive than regime_momentum (Hurst-diff vs ret × sign(Hurst))
- Adversarial-design check: ADF stationary by construction (bounded difference of two Hurst measurements)

CatBoost head-to-head is also HIGH-priority but at higher implementation cost (~2.5h pre-flight). Reasonable cycle 4 #4 candidate if /053 lands NEGATIVE.

## EDA Priorities for iter-v3/053 (per `feedback_v3_axis_selection_quant_discipline.md`)

Per the rule, the QR must produce numerical tables in `analysis/iteration_v3-053/*.py` with EDA-derived numerical evidence BEFORE locking the brief. EDA priorities:

### EDA Axis 1 — hurst_drift_50_200 compute function

- Source: V3 feature parquets with `hurst_100` and (proposed) `hurst_200` series
- Formula candidate: `hurst_50 − hurst_200` (sign indicates trending → mean-reverting regime drift)
- Stationarity: ADF p<0.05 by construction (bounded difference of two stationary Hurst series)

### EDA Axis 2 — hurst_drift_50_200 IC strict gate (max |IC| < 0.70)

- Compute pairwise IC vs existing 14 features (V3_FEATURE_COLUMNS_TOP_N minus regime_momentum_signed_3d which will be DROPPED at /053 setup; net 14-feature stack)
- Compare to source primitives: `hurst_100` (in V3_FEATURE_COLUMNS_TOP_N); `hurst_diff_100_50` (also in V3_FEATURE_COLUMNS_TOP_N)
- Verify max |IC| < 0.70 strict gate or invoke `feedback_v3_engineered_feature_pivot.md` Category 2 carve-out (importance ≥ 30 threshold)

### EDA Axis 3 — hurst_drift_50_200 univariate Spearman per symbol

- Compute ρ vs forward 1-bar return per symbol (BCH, LDO, TRX)
- Verify significance at p<0.05 across ≥3 of 3 symbols
- Compare effect size to regime_momentum_signed_5d (baseline edge ingredient)

### EDA Axis 4 — hurst_drift_50_200 IC with hurst_100 + hurst_diff_100_50 (sister-stacking risk diagnostic)

- Both source primitives are in V3_FEATURE_COLUMNS_TOP_N
- Per /052 finding (sister-stacking displacement at IC 0.44), monitor IC with same-family Hurst primitives
- If IC > 0.50 with hurst_100 OR hurst_diff_100_50, document stacking risk per UPDATED `feedback_v3_engineered_features_dont_stack.md`

### EDA Axis 5 — Setup commit changes

- DROP `regime_momentum_signed_3d` from `V3_FEATURE_COLUMNS_TOP_N` (CLOSED at /052 per Section 7)
- ADD `hurst_drift_50_200` as 15th element (or 14th if 3d drop reduces to 14)
- Compute function: NEW; not dead code (unlike /052's regime_momentum_signed_3d which existed as dead code)
- 5 adversarial tests in `tests/features_v3/test_hurst_drift_50_200_universal.py`
- ITERATION_LABEL = "v3-053"

## Memory Rule Updates

- **`feedback_v3_engineered_features_dont_stack.md` EXPANDED 2026-05-11** (orchestrator-applied at Critic FINAL `34cc46f`) to cover SAME-FAMILY sister stacking at ANY IC. Previously framed around DIFFERENT families at high IC; /052 evidence shows displacement at moderate IC 0.44 between two sister composed features.
- **`feedback_v3_axis_selection_quant_discipline.md` fired at /052** (PIVOT precedent): orchestrator's LDO-removal pick PRE-FALSIFIED by QR EDA at SHA `0a10581`; PIVOTED to /051 EDA RANKED #2 (regime_momentum_signed_3d UNIVERSAL); Section 10 audit trail documents supersession with SHAs.
- **`feedback_v3_engineered_features_proven.md` UNCHANGED**: regime_momentum family established by 5d at /025 + /028 CONFIRMATION-MERGE; 3d UNIVERSAL CLOSED at /052 does NOT invalidate the proven status of the 5d sibling.
- **`feedback_v3_strict_10_to_1_cadence.md` advances 2/10** for cycle 4. iter-v3/052 is cycle 4 #2; 8 more EXPLORATIONs needed before iter-v3/061 CONFIRMATION.
- **`feedback_v3_dsr_mode_artifact.md` UNCHANGED**: DSR=0.0 at /052 EXPLORATION-spec n_trials=525 is INFORMATIONAL ONLY per established interpretation.
- **`feedback_v3_single_seed_frozen_baseline.md` REVISED interpretation applied at /052**: when V3_FEATURE_COLUMNS_TOP_N changes universally, per-symbol Optuna trajectories perturb — what looks like "axis lift" is search-trajectory artifact on the base 14 features. Verified at /052 (TRX OOS WR +11.2pp on rank-15/15 feature).
- **`feedback_v3_engineered_feature_pivot.md` UNCHANGED**: Category 2 IC carve-out applies to STRICT |IC|<0.50 gate only, NOT to PATH C-suspicious ratio-band gate (Critic FINAL `34cc46f` confirmed).

## Architectural Decisions

- **BASELINE_V3.md UNCHANGED at iter-v3/028** (+0.5101 IS / +0.5053 OOS; SHA `b0576df`). EXPLORATION; no MERGE gate evaluation.
- **iter-v3/028 architecture PRESERVED** as cycle 4 baseline (V3_MODELS = 3-sym; V3_ATR_MULTIPLIERS_PER_SYMBOL = {}; block_long_for = (); REQUIRED_GAP = 66).
- **regime_momentum_signed_3d UNIVERSAL axis CLOSED** for cycle 4. Compute function in dispatch retained as inert column dispatch at /053 setup (column dropped from V3_FEATURE_COLUMNS_TOP_N; compute_regime_momentum_signed_3d retained as zero-revert-cost dead code analogous to fracdiff_d05_close PARKED status).
- **regime_momentum_signed_5d PRESERVED** in V3_FEATURE_COLUMNS_TOP_N (iter-v3/028 edge ingredient; rank recovered to 11-13/15 at /052 from 14-15/15 at /051 due to sister-stacking displacement; family established per `feedback_v3_engineered_features_proven.md`).
- **fracdiff_d05_close remains PARKED** (PARKED at /051 closeout; SWAPPED at /052 setup; compute function + 5 tests retained as zero-revert-cost dead-code coverage).
- **Per-symbol architecture (V3_FEATURES_PER_SYMBOL + V3_ATR_MULTIPLIERS_PER_SYMBOL) PRESERVED as code infrastructure** — validated at multi-seed (/050); no architectural defects.
- **Primitive 10 (`block_long_for`) wired value `()`** UNCHANGED from /051; mechanism + tests + GateStats counter PRESERVED as code.
- **LDO removal axis DEFERRED to multi-seed CONFIRMATION** (iter-v3/061+) where single-seed lottery artifacts dissolve. EDA at /052 SHA `0a10581` pre-falsifies the axis at EXPLORATION-scope.
- **`--clean-oof` guardrail RETAINED** (SHA `6a216b5`). Behavior correct at /052.
- **NO TAG ISSUED.** EXPLORATION; only CONFIRMATION-MERGE iterations get `v0.v3-NNN` tags.

## See Also

- `briefs-v3/iteration_v3-052/research_brief.md` — Phase 5 PIVOT brief (SHA `41ff0b8`; supersedes original SHA `87e070b`)
- `briefs-v3/iteration_v3-052/phase5p5_gate.md` — Phase 5.5 gate PASS
- `briefs-v3/iteration_v3-052/engineering_report.md` — Phase 6/7 engineering report (SHA `5eae673`; PATH C-suspicious classification)
- `briefs-v3/iteration_v3-052/review.md` — Phase 7.5 Critic FINAL (SHA `34cc46f`; EXPLORATION-NEGATIVE PATH C-suspicious)
- `reports-v3/iteration_v3-052/comparison.csv` — primary numerical results (single-seed)
- `reports-v3/iteration_v3-052/seed_summary.json` — per-seed data (1 outer seed)
- `reports-v3/iteration_v3-052/dsr.json` — DSR/PBO/PSR/n_eff (n_trials=525 EXPLORATION-spec)
- `reports-v3/iteration_v3-052/per_cell_pbo.csv` — per-cell PBO
- `reports-v3/iteration_v3-052/cpcv_paths.csv` — CPCV path data (45 paths)
- `reports-v3/iteration_v3-052/ic_matrix.csv` — 3d vs existing 14 features (max |IC|=0.498 vs vwap_dev_20; IC vs 5d sister=0.4446)
- `reports-v3/iteration_v3-052/adf_test.csv` — 3d ADF stationarity per symbol
- `reports-v3/iteration_v3-052/in_sample/per_symbol.csv` — IS per-symbol PnL attribution
- `reports-v3/iteration_v3-052/out_of_sample/per_symbol.csv` — OOS per-symbol PnL attribution
- `reports-v3/iteration_v3-052/in_sample/model_importance_last_month_*.csv` — feature importance per symbol + portfolio (3d rank 14-15/15 ALL syms; 5d recovered to 11-13/15)
- `reports-v3/iteration_v3-052/in_sample/trades.csv` + `out_of_sample/trades.csv` — trade rosters
- `analysis/iteration_v3-052/ldo_removal_eda.py` + 7 CSVs + `synthesis.md` (SHA `0a10581`) — LDO removal supersession EDA
- `analysis/iteration_v3-051/axis_c_regime_3d_compute.py` + 3 CSVs + `synthesis.md` §c3 (SHA `290f37b`) — 3d UNIVERSAL EDA backing
- `src/crypto_trade/features_v3/engineered_v3.py` (lines 330-376) — `compute_regime_momentum_signed_3d` reactivated from dead code
- `src/crypto_trade/features_v3/__init__.py` — V3_FEATURE_COLUMNS_TOP_N (15 elements at /052; revert to 14 at /053 setup with `hurst_drift_50_200` ADD if /053 chosen)
- `run_baseline_v3.py` — ITERATION_LABEL "v3-052"; V3_MODELS 3-sym; block_long_for=()
- `validation_v3.py` — REQUIRED_GAP=66 (UNCHANGED from /051)
- `tests/features_v3/test_regime_momentum_signed_3d_universal.py` — 5 adversarial tests (PASS)
- `tests/features_v3/test_fracdiff_d05_universal.py` — 5 adversarial tests (PASS; dead-code coverage at /052)
- `BASELINE_V3.md` — UNCHANGED at iter-v3/028 (+0.5101 IS / +0.5053 OOS)
- Setup commit SHA `4cf49e5` — V3_FEATURE_COLUMNS_TOP_N SWAP + compute dispatch activation
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_engineered_features_dont_stack.md` — EXPANDED 2026-05-11 (orchestrator-applied at /052)
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_axis_selection_quant_discipline.md` — fired at /052 PIVOT (rule 4 invocation)
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_engineered_features_proven.md` — regime_momentum family proven status preserved (5d at /025+/028)
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_structural_over_knob_exploration.md` — Category 1 (NEW feature family) prioritized for /053
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_strict_10_to_1_cadence.md` — cycle 4 cadence 2/10 advanced
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_dsr_mode_artifact.md` — DSR EXPLORATION-INFORMATIONAL interpretation
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_single_seed_frozen_baseline.md` — REVISED interpretation applied
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_engineered_feature_pivot.md` — Category 2 IC carve-out does NOT cover PATH C-suspicious
- `diary-v3/iteration_v3-051.md` — immediate predecessor (EXPLORATION-NULL-RESULT; cycle 4 #1 of 10)
- `diary-v3/iteration_v3-050.md` — cycle 3 CONFIRMATION-NO-MERGE-revert closeout
- `diary-v3/iteration_v3-028.md` — first CONFIRMATION-MERGE (BASELINE_V3.md anchor; regime_momentum_signed_5d edge ingredient)
- `diary-v3/iteration_v3-025.md` — regime_momentum_signed_5d first PROMISING (single-seed)
- `briefs-v3/exploration_catalog.md` — iter-v3/052 catalog row at diary closure (EXPLORATION-NEGATIVE PATH C-suspicious verdict)
