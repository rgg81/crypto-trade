# LightGBM Master Advisor — iter-v1/039 — Phase 4.5 (Pre-Design, RETARGETED AXIS)

## Context Read
- Track: v1, baseline `v0.v1-baseline-corrected` (IS +0.2829 / OOS +0.6637).
- **Axis pivot**: DD-brake REJECTED at EDA stage (mechanism BACKWARD 3/5 sym; LINK skipped-trade mean +2.06%/trade). New axis = **Per-cohort Sortino × LINK+DOT specialist hybrid** (Path Forward #1 from `axis_rejected.md`).
- /036 substrate: LINK+DOT trend-scan specialists, OOS Sharpe +1.7465 (Δ +1.08, **largest single-seed lift in v1 history**), 50/50 PnL split (LINK 48.94% / DOT 51.06%), 105 OOS trades.
- /037 Sortino on 5-cohort baseline: OOS Δ +0.18 but mechanism DIVERGENT — DOT carried 78.62% OOS PnL, LINK -42.9pp HURT; Jaccard 0.102 (basin-relocation).
- Config: `--symbols LINKUSDT,DOTUSDT --label-mode trend_scanning --optuna-objective sortino --ensemble-size 3 --n-trials 18 --seeds 1`.

## Mechanism Interaction Prediction (LOAD-BEARING)

Trend-scanning labels produce ~40% fewer labels per training-window than triple-barrier (significance threshold on Wald-t over forward window kills marginal/chop bars). Sortino objective penalizes IS downside-std. **Combined effect**: Sortino searches a SPARSER loss surface for low-downside-std basins.

Two regime predictions:
1. **PROMISING-CLEAN if** /036's labels select for "stable trends" but residual IS downside-std is the binding constraint (Sortino reselects HP toward LINK-tail-protection). Predicted lift: OOS Δ over /036's +1.08 by +0.10 to +0.30 → **Δ vs baseline +1.18 to +1.38**.
2. **NEG / INERT if** /036 already exhausts the downside-clip degree-of-freedom (trend-scanning's significance filter mechanically removes chop trades = primary downside source). Sortino has no incremental gradient signal → reduces to /036 numeric or worse via basin lottery.

Per /037 evidence (downside-std GREW +11.7% under Sortino on 5-cohort), the mechanism-as-stated is REFUTED at v1 — Sortino's actual basin behavior on v1 is right-tail concentration, not left-tail clipping.

## Per-Symbol Concentration Sensitivity (DECISIVE DIAGNOSTIC)

/037 produced DOT 78.62% / LINK -42.9pp on 5-cohort. /036 produced 50/50 LINK+DOT on 2-cohort. **The 78/22 vs 50/50 fork is the load-bearing falsifier**:

| /039 observed split | Interpretation | Routing |
|---|---|---|
| **DOT ≥ 70% / LINK ≤ 30%** | /037 DOT-skew is INTRINSIC TO SORTINO (substrate-independent); LINK incompatible with Sortino regardless of label-mode | PROMISING-DOT-ONLY; /044 = DOT-Sortino-trend-scan specialist alone |
| **40-60% / 40-60% (balanced)** | /037 DOT-skew was 5-cohort confound; Sortino COMPOUNDS with /036 substrate cleanly | PROMISING-CLEAN; /044 = full hybrid CONFIRMATION substrate |
| **LINK ≥ 70% / DOT ≤ 30%** | Sortino × trend-scan inverts /037 asymmetry; unprecedented; flag for multi-seed | PROMISING-LINK-ONLY (suspicious; needs /044 multi-seed isolation) |
| **NEG bundle (both < +0.20 over /036)** | Mechanisms COLLIDE; non-orthogonal at single-seed | INERT; cycle-5 routing unchanged |

This is the cleanest mechanism diagnostic available in cycle-5 — the answer directly resolves the /037 closeout open question (Recommendation 2 from /037 review: "pre-register Sortino × /036 stacking compounding test").

## n_trials=18 Adequacy Analysis

For 2 cohorts at n_trials=18 → **9 trials/cohort effective search density**. Compare:
- Baseline 5-cohort: 18/5 = 3.6 trials/cohort (Optuna shares budget across pool)
- /036 2-cohort: 18/2 = 9 trials/cohort
- /039 2-cohort + Sortino: 9 trials/cohort BUT on a sparser label set (trend-scanning ~60% labels of triple-barrier)

The search-density-per-label is roughly 18/2 × (1/0.6) = **15-effective trials/cohort/label-density** — well ABOVE the /037 n_effective_trials=9 ceiling that caused basin-narrowness FAIL in /037 (F-AXIS #3 Jaccard 0.102). Net: **n_trials=18 is ADEQUATE — do not bump.** Single-seed is the binding constraint, not trial budget.

## F-AXIS Falsifier Recommendations

- **F2 wiring**: dispatch banner `[iter-v1/039] PER-COHORT-SORTINO-HYBRID ACTIVE` with **2 asserts**: `label_mode_arg == "trend_scanning"` AND `optuna_objective_arg == "sortino"` AND `set(symbols) == {"LINKUSDT", "DOTUSDT"}`. Verify per-cell Sortino values logged in run.log; spot-check 3 cells have non-NaN downside_std.
- **F3 per-symbol PnL Δ LOAD-BEARING**: LINK OOS PnL Δ vs /036 ∈ [-20pp, +30pp]; DOT OOS PnL Δ vs /036 ∈ [-20pp, +30pp]. Outside band → mechanism diverged. **The SIGN match (both positive OR both negative) determines orthogonality vs collision.**
- **F4 bundle Δ band**: OOS Δ vs **/036 anchor +1.7465** (not baseline) ∈ [+0.10, +0.30] PROMISING; [-0.15, +0.10] INERT (stacking failure); < -0.15 NEG-COLLISION. Anchor against /036 because /036 is the substrate; comparing against baseline obscures the compounding question.
- **F5 wall-clock**: anchor /036 ~25 min (2 cohorts, same config). Sortino adds negligible cost (one mask + std on subset). Modal 25-35 min; hard cap 60 min.
- **F6 (recommended NEW) trade-roster Jaccard vs /036**: PRIMARY mechanism diagnostic. Jaccard ∈ [0.50, 0.85] = clean compounding (basin reuse with marginal Sortino re-selection). < 0.30 = basin migration (PROMISING-BASIN-RELOCATION subtype, needs multi-seed). > 0.95 = TECHNICAL-FAILURE-SILENT-NO-OP (Sortino didn't activate). Jaccard < 0.20 with /037-style DOT-skew = /037 mechanism reproduced on 2-cohort.

## Saturation / Double-REPEAT Check

This axis is a **double-REPEAT**:
- **Loss-function family**: last used /037 (1 iter ago). 2-iter recurrence allowed; 5+ same-family forbidden. Counter at 2 of 5.
- **Per-cohort-specialization family**: last used /036 (3 iter ago, with /037 + /038 between). Counter at 2 of 5.

Both within tolerance per `feedback_v3_strict_10_to_1_cadence.md`. Acceptability ground: the axis is the **direct compoundability test of two previously-PROMISING axes** — Critic /037 closeout Rec 2 explicitly pre-registered this stacking probe. NOT a third independent attempt at either family. Acknowledge in brief Section 0.6 as JUSTIFIED double-REPEAT, not unconstrained rotation.

**Prior probability distribution** (calibrated against /037 mechanism failure + /036 substrate strength):

| Outcome | Prior |
|---|---|
| PROMISING-CLEAN (Δ vs /036 ≥ +0.10, balanced 50/50) | 18% |
| PROMISING-DOT-ONLY (Δ vs /036 ≥ +0.10 but DOT-skewed > 70%) | 22% |
| PROMISING-LINK-ONLY (Δ vs /036 ≥ +0.10 but LINK-skewed > 70%) | 5% |
| PROMISING-INERT-FAV / INERT (Δ vs /036 ∈ [-0.15, +0.10]) | 28% |
| NEG-COLLISION (Δ vs /036 < -0.15; mechanisms collide) | 22% |
| NEG-CATASTROPHIC (Δ vs /036 < -0.40; substrate dissolution) | 5% |

Combined PROMISING 45% vs combined NEG 27%. **PROMISING-DOT-ONLY is the modal outcome (22%)** — consistent with /037's DOT-Sortino-affinity observation and /036's bimodal LINK+DOT discovery; Sortino mathematically rewards DOT's lower-variance trade roster more than LINK's.

## What I Did NOT Recommend

- **No `class_weight='balanced'` adjustment** — trend-scanning produces 3-class labels with natural ~33/33/33 split (significance-filtered to whichever class survives Wald-t); class imbalance is not the bottleneck.
- **No `min_data_in_leaf` bump** despite sparser labels — Sortino's basin selection at single-seed is sensitive to leaf-data minimums but bumping breaks single-axis isolation (mixes with loss-function change). Defer to /044 CONFIRMATION multi-seed if PROMISING.
- **No feature subset pruning** — V1_FEATURE_COLUMNS_PRUNED (43 cols) is the /036 substrate; preserving feature space ensures clean compounding attribution.

## /044 Routing Implication (Predicted)

If F4 PROMISING-CLEAN (18% prior) → /044 CONFIRMATION = **Sortino × LINK+DOT trend-scan specialist** 10-seed validation; bundle substrate locked.

If F4 PROMISING-DOT-ONLY (22% prior, modal) → /044 splits: either (a) DOT-Sortino-trend-scan specialist alone OR (b) /036 + /037 as SEPARATE strictly-accretive decisions (per `feedback_v3_promising_mechanical_subtype.md` — non-compoundable across iterations). LM Master leans toward (b) — preserves /036's 50/50 diversification.

If F4 INERT/NEG (55% combined prior, modal regime) → **mechanisms collide; /044 CONFIRMATION = /036 ALONE** (single-axis trend-scan specialist). /037 Sortino reverts to standalone candidate for /045+ EXPLORATION on a DIFFERENT substrate (e.g. baseline 5-cohort triple-barrier — already tested at /037 and found mechanism-divergent, so effectively axis CLOSED).

**The 45% PROMISING prior is the highest of any v1 cycle-5 EXPLORATION since /036.** The directness of the compoundability question + /037's open-question pre-registration justify this iteration regardless of outcome.

## Closing Note

**Confidence: MEDIUM-HIGH on non-zero effect, MEDIUM on PROMISING direction.** The DOT-skew under Sortino is the single most likely outcome — and is itself informative for /044 routing whether PROMISING or INERT. **Single most important non-ignorable**: brief Section 4 verdict matrix MUST anchor against /036 (+1.7465), NOT against baseline (+0.6637) — otherwise a +0.30 numeric over baseline looks like PROMISING when it's actually a -0.78 collision against the actual substrate. The /037 closeout already documented the compounding-test pre-registration; the brief should cite that pre-registration verbatim in Section 0 to lock the anchor selection.

Relevant files referenced:
- `/home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-037/lgbm_advisor.md`
- `/home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-037/review.md`
- `/home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-036/research_brief.md`
- `/home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-036/review.md`
- `/home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-039/axis_rejected.md`
- `/home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-039/lgbm_advisor.md` (prior — DD-brake axis; this advisory supersedes for retargeted axis)
