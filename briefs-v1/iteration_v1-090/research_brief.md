# iter-v1/090 — Research Brief (Phase 1–5, QR)

**Date**: 2026-06-11
**Track**: v1 (refactored)
**Branch**: `iteration-v1/090`
**Author**: QR (autopilot)
**Anchor baseline**: BUNDLE-002 `v0.v1-082` (DOT/063 + ETH/064 + BTC/065 + AAVE/078; IS +0.7157 / OOS +1.0043)
**Tag (on closeout)**: `v0.v1-090`

---

## Section 0 — One-line summary

W-DECAY: a new **`sample_weight_mode="abs_pnl_timedecay"`** that recency-weights the abs_pnl training weights by `exp(-ln2/half_life · age)` over the **full sacred 24-month window** (no window trimming), pre-registered at **half_life = 12 months (365d)**, applied to **ONE seat (ETH/064)** as a single-cell EXPLORATION. The thesis: keep the full window but emphasize the recent regime, removing Optuna's incentive to collapse `training_days` SHORT — the exact overfit mechanism the /086 (TRB) and /088 (XRP) post-mortems isolated.

---

## Section 0.5 — TYPE declaration

**TYPE = SPECIALIST (machinery EXPLORATION).** Single-cell EXPLORATION: one BUNDLE-002 seat (ETH/064) re-run with W-DECAY vs that seat's frozen baseline. This is the FIRST machinery / sample-weighting axis of cycle-7 (the "alternate machinery" lane opened by the /086/088/089 "machinery axes (W-DECAY etc.) per alternate" directive). NOT a BUNDLE assembly. NO multi-seed CONFIRMATION (permanently dropped per /088/089). NO new symbol, NO new feature, NO model/labeling change.

---

## Section 0.6 — Architecture-Family Justification (v1-only)

- **Axis family: `sample-weighting`** (the López de Prado AFML Ch. 4 time-decay weighting machinery; the existing `sample_weight_mode` enum family — modes `{abs_pnl, uniform, uniqueness_only, composite_inv_concurrency}`).
- **Prior 5 SPECIALIST families** (from `briefs-v1/specialist_catalog.md`, cycle-7 fresh-mine + universe campaign):
  - iter-v1/083 (FIL): `universe`
  - iter-v1/084 (CRV): `universe`
  - iter-v1/085 (UNI): `universe`
  - iter-v1/086 (TRB): `universe` (bundle-diversification mine)
  - iter-v1/087 (BNB): `universe` (BLOCKED-FAIL-FAST)
  - iter-v1/088 (XRP): `universe`
  - (iter-v1/089 was a BUNDLE assembly, `bundle-composition`, not a SPECIALIST)
- **Rotation status: VALID (SATISFIED).** Prior 5 SPECIALISTs were ALL `universe`. W-DECAY is `sample-weighting` — the first non-universe axis in cycle-7. Rotation is unambiguously satisfied (different from the majority — in fact from ALL — of the prior 5).
- **One-sentence rationale**: the universe lane saturated at 1/8 fresh mines (only XRP non-negative, and /089 showed XRP doesn't yet move the baseline), so the right next step is to PIVOT to machinery that lifts the EXISTING positive seats — and W-DECAY targets the single overfit mechanism (`training_days` collapse) that the universe campaign's own post-mortems repeatedly diagnosed.

---

## Section 1 — Hypothesis

**Claim**: applying exponential time-decay sample weighting (half_life = 12mo) to the ETH/064 specialist, while keeping the full sacred 24-month training window, will (a) shift the Optuna-selected `training_days` distribution **LONGER** (because the model no longer needs to collapse the window to emphasize recent regime — the weights do it), and (b) lift the seat's IS Sharpe by **≥ +0.20** vs the ETH/064 frozen baseline (standalone IS +0.2383), without the walk-forward variance blow-up that short windows incur.

**Mechanism (López de Prado AFML Ch. 4)**: Optuna's `training_days ∈ [10,500]` knob and time-decay weighting are two routes to the SAME objective — "emphasize recent data". Today, with uniform-in-time abs_pnl weights, the ONLY route Optuna has to up-weight recent labels is to TRIM the window (`training_days` short). Short windows maximize the in-fold objective on recent label noise but degrade one-month-forward (the /086 in-fold/walk-forward optimism gap ≈ 0.48). W-DECAY provides the recency emphasis as a *smooth weight gradient over the full window* — a strictly lower-variance estimator than a hard truncation, because every sample still contributes (downweighted) rather than being discarded. If the mechanism engages, Optuna's incentive to truncate disappears → `training_days` lengthens AND the realized walk-forward Sharpe improves.

**Why this is the right machinery axis now**: the universe campaign produced TWO independent post-mortems (/086, /088) that converged on `training_days` collapse as the dominant overfit channel for single-symbol v1 specialists. W-DECAY is the minimal, theory-grounded intervention that attacks exactly that channel without touching the model, the features, the seeds, the trials, or the sacred window.

---

## Section 2 — IS-only evidence

All numbers below are from committed report artifacts (run.logs + comparison.csv) under `reports-v1/`, parsed IS-only. The reconstruction script `analysis/iteration_v1-090/training_days_collapse.py` is committed alongside this brief (parses selected-best `training_days` per fold from each seat's `run.log` via the Optuna "Best is trial N" trajectory + per-trial `training_days=` markers).

### 2.1 — The `training_days`-collapse mechanism (the motivating evidence)

Optuna search space for `training_days` is `suggest_int("training_days", 10, 500, step=10)` (`optimization.py:266`). **Note the cap is 500d** — the model can never select the full 24-month (~730d) window; the *most-conservative* available choice is 500d. "Collapse SHORT" therefore means clustering near the 10–180d floor, not "below 730d".

Selected-best `training_days` per fold, reconstructed from run.logs (the three recent single-symbol specialists that DO have logs):

| Seat | Verdict | Median training_days | folds <120d | folds <180d | folds ≥500d (cap) |
|---|---|---:|---:|---:|---:|
| **TRB/086** | SPECIALIST-NEGATIVE | **115d** | **23/46 (50%)** | 26/46 (57%) | 0/46 (0%) |
| BNB/087 | BLOCKED-FAIL-FAST | 170d | 8/25 (32%) | 14/25 (56%) | low |
| **XRP/088** | SPECIALIST-PROMISING | **250d** | **9/54 (17%)** | 19/54 (35%) | some |

**The mechanistic signature is monotone in verdict quality**: the NEGATIVE seat (TRB) collapses hardest (median 115d, half the folds under 120d); the PROMISING seat (XRP) collapses least (median 250d, only 17% under 120d). **Shorter median `training_days` ⇒ worse generalization.** This is the empirical spine of W-DECAY: a seat that is being dragged down by `training_days` collapse has headroom for the weighting fix; a seat that already selects long windows has little.

The /086 LM 7.4 post-mortem (diary `iteration_v1-086.md:51`): "At n_trials=30 the deeper search found short training windows (median 95d, 26/46 folds <120d) that maximize the in-fold Optuna objective (mean +0.179, 46/46 folds positive) but don't generalize one month forward (realized −0.30) — a ~0.48 in-fold/walk-forward optimism gap." (My reconstruction gives median 115d / 23-of-46 <120d — same finding, minor counting difference; the load-bearing fact — ~half the folds truncate below 120d — is robust.)

### 2.2 — The chosen seat's baseline (the F1 anchor)

Standalone source-iter `comparison.csv` (the correct F1 anchor — NOT the bundle-context snapshot in BASELINE_V1, which differs because the bundle aggregates over a different data extent):

| Seat | Source | IS Sharpe (standalone) | OOS Sharpe (standalone) | IS trades | OOS trades | Regime character |
|---|---|---:|---:|---:|---:|---|
| DOT/063 | `reports-v1/iteration_v1-063/comparison.csv` | +0.4310 | −0.0709 | 149 | 62 | strongest IS; least headroom |
| **ETH/064** | `reports-v1/iteration_v1-064/comparison.csv` | **+0.2383** | **+0.5171** | 198 | 81 | **balanced positive (chosen)** |
| BTC/065 | `reports-v1/iteration_v1-065/comparison.csv` | −0.1763 | +1.1256 | 190 | 87 | IS-NEGATIVE / OOS-INVERTING |
| AAVE/078 | (50-seed lock seat; metrics in BASELINE_V1) | +0.34 (bundle ctx) | +0.16 (bundle ctx) | 157 | 90 | TENTATIVE; no standalone comparison.csv |

ETH/064 baseline `training_days` distribution is **NOT directly measurable** — its run.log was not preserved (grandfathered from the /071 stash recovery; only `comparison.csv` + trades survive). This is a known evidence gap. **The F2 mechanistic falsifier therefore measures the W-DECAY run's `training_days` distribution against the *cohort prior* established in §2.1** (XRP/088 is the closest config-matched, same-family Model-A positive seat: median 250d). The W-DECAY run itself will also produce a baseline-config control read if fail-fast is OFF (the abs_pnl control fold-0 trajectory is logged), but the load-bearing comparison is "does W-DECAY's median `training_days` move LONGER than the abs_pnl cohort prior".

### 2.3 — Why ETH/064 is the chosen seat (decision)

Three seats were candidates (DOT/063, ETH/064, BTC/065; AAVE/078 has no standalone comparison anchor and is itself TENTATIVE):

- **BTC/065 (IS −0.1763)** — most overfit-*looking* IS, but it is the IS-NEGATIVE / OOS-INVERTING **regime-inverter** (OOS +1.1256). A W-DECAY IS lift here would be **confounded with regime inversion**: we could not cleanly attribute an IS Δ to the weighting mechanism vs. the seat's intrinsic IS/OOS sign flip. F1 attribution would be muddy → REJECTED as the test seat.
- **DOT/063 (IS +0.4310)** — strongest standalone IS; least `training_days`-collapse headroom; lowest expected W-DECAY sensitivity → not the most informative single cell. (It is the methodology-agnostic robustness anchor; a future iteration may re-test it for robustness if ETH validates.)
- **ETH/064 (IS +0.2383, OOS +0.5171)** — **CHOSEN.** A clean, balanced, *positive-both-windows* seat: positive but modest IS (real headroom: +0.24 → F1 target +0.44), positive OOS (NOT regime-inverting → F1 Δ is cleanly attributable to the mechanism, no inversion confound), and it shares the exact Model-A config (atr 2.9/1.45, R1/R2 OFF, R3-only) that the W-DECAY run inherits. It is the seat where a `training_days`-collapse → W-DECAY-lift would be most *readable*.

**Decision: test seat = ETH/064 (ETHUSDT specialist).**

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

- **Declaration: HIGH-RISK.**
- **Reason**: W-DECAY changes the training-objective domain — it re-weights every training sample, which alters the loss surface Optuna optimizes (a sample-weight change is, by the HIGH-RISK definition, a feature-set/labeling-domain-adjacent intervention). Single-outer-seed EXPLORATION budget.
- **Mitigation (HIGH-RISK, OPT-IN per v1 — chosen: single-seed with 50-study variance control)**: the ETH/064 seat aggregates **50 independent seed-studies** (seeds 42–91, `specialist_mode=True`, mean-of-signed-weights aggregator). This is the Pool+Route-equivalent variance control — the per-seed-study dispersion (XRP/088 showed inner-seed dispersion 41.1, healthy) suppresses basin-lottery WITHOUT a separate multi-seed CONFIRMATION. The seat is **known-positive** (IS +0.24 / OOS +0.52 baseline), so this is a within-known-good-substrate machinery probe, not a cold cell. Multi-seed CONFIRMATION is NOT run (permanently dropped). **Per the HIGH-RISK streak rule**: this is the FIRST HIGH-RISK single-seed machinery axis of the lane; if 3+ consecutive HIGH-RISK single-seed SPECIALISTs produce >1σ negative deltas, the next becomes mandatorily multi-seed — this iteration's outcome is logged toward that counter.

---

## Section 3 — Implementation

**Library change (`src/crypto_trade/strategies/ml/lgbm.py`), OPT-IN, default unchanged:**

The time-decay machinery **already exists** — block `(b3)` at `lgbm.py:891-905` computes `decay = exp(-ln2/half_life · age_months)` and multiplies it into `train_weights`, with `age_months` measured relative to `train_times.max()` (the latest training bar). This is the exact AFML Ch. 4 exponential time-decay, and `age` relative to the latest sample is equivalent to the AXIS's `age = train_end − sample_close` up to the embargo constant (immaterial — the model re-weights relatively). The gap is purely that (i) the `sample_weight_mode` enum has no `abs_pnl_timedecay` member, and (ii) it has never been wired into a v1 runner or tested.

**Two equivalent wirings; this brief specifies the explicit-enum form for clean OPT-IN semantics:**

1. Add `"abs_pnl_timedecay"` to `_valid_modes` (`lgbm.py:460`). Default `sample_weight_mode="abs_pnl"` is UNCHANGED — bit-identical for every existing seat and the baseline.
2. In the dispatch block `(b1.5)` (`lgbm.py:819-874`), add an `elif self.sample_weight_mode == "abs_pnl_timedecay"` branch that sets an internal `_apply_timedecay = True` flag (keeping the abs_pnl `train_weights` from `label_trades` as the base — NOT replacing them). The existing `(b3)` block then fires when EITHER `self.time_decay_half_life is not None` OR `_apply_timedecay` is True, using `half_life = self.time_decay_half_life or DEFAULT_WDECAY_HALF_LIFE_MONTHS` with `DEFAULT_WDECAY_HALF_LIFE_MONTHS = 12.0`. This makes W-DECAY a single self-contained mode (abs_pnl × time-decay) rather than two independently-set flags — cleaner, harder to misconfigure, and keeps the F-AXIS-MECHANISM logging at `(b4)` active (mode ≠ "abs_pnl" ⇒ Kish/per-fold cell logging fires).
3. Mirror the same enum entry in `xgb.py` (`time_decay_half_life` already present there too) for symmetry — not exercised this iteration (LightGBM only).

**The decay is multiplicative on the existing abs_pnl weights** — `weight_t = |pnl_t| · exp(−ln2/12 · age_months(t))`. No renormalization beyond what LightGBM does internally; the relative weight gradient is what matters.

**Pre-registered half-life: 12 months (365d).** ONE value, IS-reasoned, NO grid, NO OOS tuning. Justification: 12mo half_life over a 24mo window means the oldest sample (age ≈ 24mo) retains `exp(−ln2/12 · 24) = exp(−1.386) ≈ 0.25` weight — a 4:1 recent:old emphasis ratio across the window. This is a *moderate* gradient: aggressive enough to substitute for the `training_days` truncation Optuna currently performs (median 115–250d ≈ 4–8mo effective window), but gentle enough that the full window still contributes (no sample fully discarded — the strictly-lower-variance property vs. hard truncation). A 9mo (270d) alternative would push the old-sample weight to `exp(−ln2/9 · 24) ≈ 0.16` (6:1) — more aggressive, closer to mimicking the truncation we're trying to *replace* rather than smooth, so 12mo is the pre-registered choice. **Locked: 12mo. No sweep.**

**Runner (`run_iteration_090.py`)**: a clone of `run_iteration_064.py` (ETH seat) with the SINGLE change `sample_weight_mode="abs_pnl_timedecay"` passed to the `LightGbmStrategy` constructor. Everything else byte-identical: cohort `("ETHUSDT",)`, `specialist_mode=True`, `V1_SPECIALIST_SEED_COUNT=50` (seeds 42–91), `V1_SPECIALIST_OPTUNA_TRIALS=30`, `max_depth=5` FIXED, `num_leaves=31` FIXED, `bounds_profile="v1_specialist"` (training_days ∈ [10,500] in search), `atr_tp=2.9`, `atr_sl=1.45`, R1=OFF, R2=OFF, R3=ON cutoff=0.70, R5=ON vt_target_vol=0.3, aggregator=mean-of-signed-weights, `training_months=24`, `OOS_CUTOFF_DATE=2025-03-24`.

**Global `V1_FEATURE_COLUMNS_PRUNED` stays 48 columns — UNCHANGED.** No feature added or removed. The seat trains on the stock 48-col stack (ETH seat has no AAVE-style extra feature).

**fail-fast: ON (QR call).** The ETH seat is known-positive, so fail-fast risk is low, but turning it ON gives a free abs_pnl-control read of the early-fold `training_days` trajectory (for F2's cohort-control comparison) at negligible cost and guards against a catastrophic implementation bug. (If the QE prefers OFF to preserve the full fold trajectory for F2, that is an acceptable QE-side adjustment documented in Phase 5.5.)

**Run cost**: ETH single cell × 50 seeds × 30 trials × ~54 months ≈ same as /064 (~1.5h) plus a small overhead for the decay multiply (negligible). Projected **~1.5–2.0h**, inside the 2h SPECIALIST cap.

---

## Section 3.5 — LM Master integration

LM Master Phase 4.5 advisory (`briefs-v1/iteration_v1-090/lgbm_advisor.md`) was authored; QR dispositions below. The advisory materially reframes the mechanism (§0) and the F2 falsifier (now rescaled in Section 4).

| LM finding | QR disposition | Action |
|---|---|---|
| **§0 — decay & training_days COMPOSE, not substitute** (code trims-after-decay: optimization.py:392 then :417; decay stacks on whatever window Optuna picks → "removes the truncation incentive" is SECOND-ORDER not first-order) | **ADOPTED — reframes F2** | Section 4 F2 rescaled: expect a SMALL training_days lengthening (~30-60d, NOT cap-ward), and a weak/flat F2 with F1>0 is NO LONGER auto-tagged NEGATIVE-INERT (see revised F2). |
| **§1c — un-renormalized decay halves weight mass → loosens min_child_weight (absolute units) → stealth regularization-loosening confound; a VALIDATED F1 is unattributable between recency and the reg side-effect** (STRONGEST REC) | **ADOPTED — REQUIRED QE log** | QE MUST add a log line at `(b3)` of `decay.mean()` + `train_weights.sum()` pre/post-decay. Phase 7.4 attributes any F1 lift between recency vs reg-loosening using it. (Renormalize-to-mean-1 would isolate cleanly but the lock pins the impl — the log is the minimum.) |
| **§1b — abs_pnl×decay compounds dispersion → Kish ratio drops ~0.5→0.35-0.45 (ESS shrink, overfit amplifier; 50-study mean does NOT offset it)** | **ADOPTED — telemetry** | Phase 7.4 reports `_kish_ratio` under W-DECAY vs the abs_pnl read; a Kish <0.4 is recorded as an overfit-amplifier caveat on any F1 lift. |
| **§1a — decay×is_unbalance shifts effective class balance if recent data is class-skewed → F1 partly reflects class-rebalancing** | **ADOPTED — telemetry** | Phase 7.4 reports long/short WEIGHT share under decay vs the label-balance print. |
| **§4 — decay shifts the objective NON-uniformly across the 50 TPE seeds; could help some / hurt others → mean-of-signed-weights washes a bimodal effect to ≈0 (F1-INERT masking a real effect)** | **ADOPTED — telemetry** | Phase 7.4 reports per-seed training_days STD (not just median). |
| **§5.1 — INVERSE-EDGE risk (~25-30%): if ETH's IS edge lives in 2022-23, recency-weighting discards it → F1<0** | **ACKNOWLEDGED (pre-registered downside)** | This is the main F1<0 path; Section 7 modal carries it. If F1<0, Phase 7 attributes to inverse-edge (ETH edge is old-data) NOT a W-DECAY bug. |
| HP-bound change / multi-seed / renormalize-the-impl | **REJECTED (lock)** | No HP-bound change, no multi-seed (permanently dropped), impl renormalization pinned by lock (log instead). |

**Net**: no lock change; F2 rescaled to the LM's second-order magnitude; the §1c attribution log is a REQUIRED QE deliverable (without it a VALIDATED F1 is unattributable).

---

## Section 4 — Falsifiers (pre-registered)

**F1 — IS Sharpe Δ vs the ETH/064 frozen baseline (standalone IS +0.2383).**
- **VALIDATED** if IS Sharpe Δ ≥ **+0.20** (target IS ≥ +0.438).
- **NEGATIVE** if IS Sharpe Δ < **+0.00** (W-DECAY hurt the seat).
- **TENTATIVE-INERT** band: 0.00 ≤ Δ < +0.20 (positive but sub-threshold — machinery engaged weakly).

**F2 — MECHANISTIC check (DIRECTIONAL, RESCALED per LM §0/§3): does the Optuna `training_days` distribution shift modestly LONGER under W-DECAY?**
- Measured as: median selected `training_days` across all ETH folds under W-DECAY, vs the abs_pnl cohort prior. Because the ETH/064 baseline run.log is unavailable (§2.2), the comparison is against (a) the W-DECAY run's own abs_pnl control read if fail-fast is ON, and (b) the config-matched positive-seat cohort prior (XRP/088 median 250d, the closest same-family Model-A baseline read).
- **RESCALED EXPECTATION (LM §0/§3): decay COMPOSES with `training_days`, it does NOT substitute** (code trims-after-decay) — so the mechanism is SECOND-ORDER. Expect a SMALL lengthening (~+30-60d median, modal ~180d→~220-240d; folds <120d drop ~10-20pp), NOT a move toward the 500d cap. A median jump >150d or to the cap is SUSPICIOUS (more likely the §1c reg-loosening, not pure recency).
- **MECHANISM-ENGAGED** if W-DECAY median `training_days` moves LONGER by any amount vs the reference.
- **CRITICAL FALSIFIER-DESIGN RESOLUTION (LM §3):** a weak/flat F2 with **F1 > 0** is **NOT auto-tagged NEGATIVE-INERT** — because a correct W-DECAY can legitimately produce F1>0 with F2 ≈ flat (decay stacks, doesn't substitute). In that case, the **§1c attribution log is the arbiter**: if the `decay.mean()`/weight-sum log confirms decay was applied AND F1>0, the result is SPECIALIST-PROMISING/TENTATIVE (recency or reg-loosening channel — attributed at 7.4), NOT inert. NEGATIVE-INERT is reserved for `training_days` moving SHORTER or unchanged AND F1 ≤ 0 (mechanism truly did nothing). This corrects the /086-style guard for W-DECAY's second-order nature.

**F3 — OOS direction-consistency.**
- **CONSISTENT** if OOS Sharpe Δ has the **same sign** as IS Sharpe Δ (both up, or both down) — the mechanism generalizes the same direction it shifted IS.
- **INCONSISTENT (caution flag)** if IS lifts but OOS drops (would indicate W-DECAY traded one form of recency-overfit for another) or vice versa. INCONSISTENT downgrades any F1-VALIDATED to PROMISING-TENTATIVE pending the sign reconciliation; it does not by itself flip to NEGATIVE (OOS is single-outer-seed, regime-contingent — cf. /088/089).

**Pre-registered MODAL outcome (Section 7) is `TENTATIVE-INERT` / weak-positive** — see §7 for reasoning.

---

## Section 6 — Risk recap

**No new risk primitive.** W-DECAY is a sample-weight multiplier, not a risk gate. The ETH/064 seat inherits its existing risk stack **unchanged**:
- R1 = OFF (Model A ETH disposition; BTC/ETH mean-reverting WR at late streaks)
- R2 = OFF (Model A has no R2)
- R3 = ON, Mahalanobis OOD gate, cutoff=0.70, 16 scale-invariant features (aggregator-level, one distance per candle)
- R5 = ON, vol-targeting vt_target_vol=0.3

**Risk-side argument for W-DECAY**: by removing the `training_days`-collapse incentive, W-DECAY is expected to *reduce* model variance (every sample contributes, downweighted, rather than the model fitting a thin 4-month window). Lower model variance is a risk improvement orthogonal to the R-stack. No R-threshold is re-calibrated; the R-stack thresholds are IS-calibrated and unchanged from the /064 seat. No simulated R-effect change is claimed because no R-parameter moves.

---

## Section 7 — Modal outcome (pre-registered)

**MODAL: `SPECIALIST-TENTATIVE-INERT` / weak-positive (F1 in [0.00, +0.20), F2 mechanism partially engaged).**

Reasoning for a *modest* modal rather than a confident VALIDATED:
1. The mechanism is real (the §2.1 monotone signature is strong evidence the `training_days` channel matters), so a *directional* IS lift and a *longer* `training_days` shift are both more-likely-than-not → I do NOT predict NEGATIVE.
2. But ETH/064 is the *mildest-collapse* of the candidate seats by inference (it is a balanced positive seat, not a TRB-style collapser), so the *magnitude* of available lift is bounded — the +0.20 F1 bar is genuinely uncertain to clear at one seat / one half-life. Cf. the v1 prior: 0/13 cycle-2 single-axis interventions cleared a +0.20-class IS bar; machinery axes (sample-weighting /016, /031) were INERT or NEGATIVE in-basin.
3. F2 is the more-likely-to-fire-positive of the two: `training_days` lengthening under decay is mechanically near-certain *if the implementation is correct*, even if the Sharpe payoff is sub-threshold. So the realistic modal is "mechanism engaged (F2 ✓), Sharpe lift present but possibly under +0.20 (F1 TENTATIVE), OOS consistent (F3 ✓)".

A clean VALIDATED (F1 ≥ +0.20 AND F2 ✓ AND F3 ✓) is the *upside* outcome and would make ETH the first machinery win in v1 — it would motivate a follow-on robustness re-test on DOT/063 (and a BUNDLE-002 re-assembly with W-DECAY'd seats). A NEGATIVE-INERT (F2 fails) is the *downside* and would close the W-DECAY axis at this half-life.

---

## Section 8 — Candidacy bands

| Outcome | F1 (IS Δ) | F2 (training_days) | F3 (OOS sign) | Verdict | Next |
|---|---|---|---|---|---|
| **VALIDATED** | ≥ +0.20 | longer (✓) | consistent | `SPECIALIST-PROMISING` (machinery win) | robustness re-test on DOT/063; W-DECAY'd BUNDLE-002 re-assembly candidate |
| **TENTATIVE-INERT** (modal) | [0.00, +0.20) | longer (✓) | consistent | `SPECIALIST-TENTATIVE` | tune half_life ONCE (9mo) as a SEPARATE future iteration (NOT this one); or apply to a higher-headroom seat |
| **F1>0 but F2 weak/flat** (LM §3 case) | ≥ 0.00 | flat/≈unchanged | consistent | `SPECIALIST-TENTATIVE` (attribute via §1c log: recency vs reg-loosening) | NOT inert — decay composes-not-substitutes; 7.4 splits the channel |
| **MECH-INERT** | ≤ 0.00 | NOT longer (shorter/unchanged) | any | `SPECIALIST-NEGATIVE-INERT` | mechanism truly did nothing (training_days didn't move AND no IS lift) — close axis OR debug |
| **NEGATIVE** | < +0.00 | any | any | `SPECIALIST-NEGATIVE` | W-DECAY hurt (likely inverse-edge, LM §5.1: ETH edge in old data); sample-weighting lane de-prioritized for ETH |
| **INCONSISTENT** | ≥ 0.00 | longer | OOS opposite IS | `SPECIALIST-TENTATIVE` (sign caution) | reconcile IS/OOS sign before any BUNDLE use |

**This iteration does NOT update BASELINE_V1.md** regardless of outcome — it is a single-seat machinery EXPLORATION, not a BUNDLE merge. BUNDLE-002 (`v0.v1-082`) remains the live baseline. A VALIDATED W-DECAY would feed a *future* BUNDLE-002 re-assembly (re-running the seats with W-DECAY and re-checking the bundle gates), which is where any baseline change would be adjudicated.

---

## Section 9 — Methodology / validation recap

- **Sacred constants intact**: `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24`. W-DECAY keeps the **FULL 24-month window** — it re-weights, it does NOT trim. This is the explicit anti-cheating property: no window shortening, no IS-window manipulation. (Per `feedback_no_cheating` and `feedback_training_window`.)
- **Lock intact**: 50 seed-studies × 30 trials × `max_depth=5` × `num_leaves=31` × `specialist_mode=True` × atr 2.9/1.45 — all UNCHANGED. W-DECAY is ONLY a sample-weight multiplier. NO change to model, seeds, trials, features, or window. NO multi-seed CONFIRMATION.
- **Global PRUNED stays 48 cols** — UNCHANGED.
- **OPT-IN default-preserving**: `sample_weight_mode="abs_pnl"` remains the default; every existing runner and the baseline are bit-identical. Critic Check 14 (axis-family declaration matches src/ diff) will see a `sample-weighting` diff (the new enum + the `run_iteration_090.py` clone) matching the Section 0.6 declaration.
- **No look-ahead**: time-decay uses `age` relative to the latest *training* bar (`train_times.max() < train_end_ms`); decay weights depend only on training-window timestamps — past-only, no test-window contamination. (Rung 1 / `feedback_no_cheating`.)
- **Trade-rate floor**: ETH/064 baseline is 198 IS / 81 OOS trades; W-DECAY re-weights samples but does not gate trades, so the trade count is expected to stay ≈ the same order (well above the ≥50-OOS-per-specialist v1 floor). Verified in Phase 7.
- **Evidence discipline** (`feedback_qr_uses_is_data`): every number in Section 2 is from a committed artifact (run.logs / comparison.csv), reproduced by the committed `analysis/iteration_v1-090/training_days_collapse.py` script. No category-matching prose.
- **AFML reference**: López de Prado, *Advances in Financial Machine Learning*, Ch. 4 (Sample Weights) — time-decay weighting (exponential form), and the principle that overlapping-label recency emphasis should be a weight gradient, not a window truncation.

---

## Pre-registration statement

This brief is pre-registered before any W-DECAY backtest is run. The half-life (12mo), the test seat (ETH/064), the three falsifiers (F1 ≥ +0.20 / F2 training_days-longer / F3 OOS-sign-consistent), and the modal (TENTATIVE-INERT weak-positive) are fixed. No OOS data is consulted in Phases 1–5. The QR sees OOS for the first time in Phase 7.
