# Iteration v3-092 — Research Brief — the cycle-3 CONFIRMATION: a multi-seed CONFIRMATION-grade verdict that formally closes the cross-sectional `LGBMRanker` line

**Iteration**: iter-v3/092
**Type**: CONFIRMATION (cycle-3 CONFIRMATION slot — the iteration that follows the /082-091 10-EXPLORATION cadence)
**Branch**: `iteration-v3/092` (off the /091 closeout `c6a03ed`)
**Date**: 2026-05-17
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` — **IMMUTABLE** (`src/crypto_trade/config.py`, `OOS_CUTOFF_MS = 1742774400000`).
- `training_months = 24` — **IMMUTABLE**.
- IS = every bar with `open_time < OOS_CUTOFF_MS`. OOS = every bar at/after it.
- The QR sees OOS for the FIRST time in Phase 7. Every design parameter in this brief — the horizon H, the score mode, the seed set, the cost-aware construction constants — is selected on **IS data only** (the committed /088/089/091 cross-sectional EDAs and the corrected /091 horizon grid) or set **a-priori from cited research**. This is scrutinised in Section 10.3.
- **NO CHEATING.** This is a CONFIRMATION. The configuration /092 validates is pre-registered in this brief (Section 3). The QR does not see the multi-seed OOS book until Phase 7. There is no OOS-informed parameter anywhere in this brief.

## Section 0.5 — Iteration Type Declaration

iter-v3/092 is the **cycle-3 CONFIRMATION**. Cycle 3 = iter-v3/082-091, ten EXPLORATIONs, now complete (the /091 closeout, `diary-v3/iteration_v3-091.md` Section 8, records the 10/10 cadence closed).

A v3 CONFIRMATION normally multi-seed-validates the cycle's best clean PROMISING EXPLORATION result. **Cycle 3 produced zero clean PROMISING results** (the /091 retrospective ledger: /082-087 six per-symbol axes all NEGATIVE-class; /088-091 a four-iteration cross-sectional re-architecture that produced v3's first genuine OOS *signal transfer* but never a net-positive OOS *book*). There is no PROMISING EXPLORATION to confirm.

So /092's role is different but legitimate and cadence-respecting, and it is exactly what the /091 closeout recommended (`diary-v3/iteration_v3-091.md` Section 9.2) and the /091 Critic mandated (`review.md` Recommendation 2): **/092 is a multi-seed CONFIRMATION-grade verdict on the cross-sectional `LGBMRanker` architecture** — giving v3's most substantial cycle-3 effort (the /088-091 re-architecture, all single-seed=42) the rigorous multi-seed close it owes before cycle 4 re-architects into a new signal class.

This is a CONFIRMATION-grade *closing verdict*, **not an edge hunt**. The hypothesis (Section 1) is that the cross-sectional `LGBMRanker` line, multi-seed-validated in its best-faith form, does not reach a net-positive OOS book and does not beat the /059 canonical baseline — formally closing it. The honest pre-registered expected outcome (Section 7, Section 8) is **CONFIRMATION-NO-MERGE**. The multi-seed run is what *definitively establishes* whether the cross-sectional line has anything — the four single-seed EXPLORATIONs carry lottery noise (the /091 reference book's OOS +0.4613 single-seed inversion is the proof), and a multi-seed verdict is the rigorous close v3 owes the line.

Per `feedback_v3_iter018_confirmation_baseline_validation.md` (the iter-v3/018 precedent — a CONFIRMATION that is a multi-seed *validation* run, not a bundle assembly): /092 carries **NO new edge axis**, **NO bundling**, **NO axis variation**. It runs the pre-registered cross-sectional configuration at the v3 CONFIRMATION spec and reports the multi-seed verdict.

This brief **supersedes the cycle-3 incremental plan** (`briefs-v3/cycle3_plan.md`) for the CONFIRMATION slot.

---

## Section 1 — Hypothesis

### 1.1 — What the four-iteration cross-sectional line established

The cross-sectional `LGBMRanker` line (`diary-v3/iteration_v3-088.md` → `091`):

- **/088 (RE-ARCHITECTURE, ARCHITECTURE-PARTIAL)** — stood up a pooled `LGBMRanker(lambdarank)` over a 22-symbol cross-section, dollar-neutral tercile long-short. **OOS rank-IC +0.0430 ± 0.3317, n = 1255, t ≈ +4.59** — v3's first genuine OOS signal transfer in ~27 EXPLORATIONs. The BOOK lost (OOS net monthly Sharpe −0.5418): a sign inversion + every-bar turnover drag.
- **/089 (CORRECTED build, CONSTRUCTION-PARTIAL)** — sign fix + cost-aware construction (quintile legs, 3-bar overlapping holds, no-trade band, hard turnover ceiling). OOS net lifted to −0.0985 (a +0.44 lift) — but the /090 and /091 closeouts both record this honestly as a **one-time MECHANICAL gain** (a sign-error fix + a turnover-excess fix — removing drag, not adding edge). The book turned gross-positive (OOS gross monthly Sharpe +0.1717).
- **/090 (feature expansion, FEATURE-EXPANSION-FALSIFIED, Critic OVERALL=BLOCK)** — the first genuine attempt to ADD gross edge (a researched, multivariate-tested, redundancy-cut 2-feature downside-risk expansion). It FAILED — OOS gross monthly Sharpe fell to +0.1558 (corrected recompute); the gross signal did not respond to feature work.
- **/091 (model-free scoring function, CONSTRUCTION-FALSIFIED)** — replaced the trained ranker with a parameter-free trailing-21-bar-return score. It FAILED — OOS gross monthly Sharpe turned net-NEGATIVE (−0.0178); F1 and F2 both fired.

The honest four-iteration ledger (`diary-v3/iteration_v3-091.md` Section 6): **OOS net monthly Sharpe /088 −0.5418 → /089 −0.0985 → /090 −0.0770 → /091 −0.0995 — near-breakeven, NEVER net-positive.** The line produced a genuine but faint OOS rank-IC (+0.03 to +0.04) and zero net-positive OOS books across four iterations.

### 1.2 — The single-seed problem the cross-sectional line carries

Every cross-sectional iteration /088-091 ran at **single-seed (seed=42)**: the trained `LGBMRanker` at `ensemble_size=1`; the /091 model-free book is deterministic (no seed). The lottery risk this carries is not hypothetical — it is *demonstrated*. The /091 reference `LGBMRanker` book (`reports-v3/iteration_v3-091/reference_lgbmranker/`) shows **IS net monthly Sharpe −0.1107 / OOS net monthly Sharpe +0.4613** — an IS/OOS ratio of −4.17, a textbook single-seed inversion artifact (`feedback_v3_engineered_features_dont_stack.md`, the iter-v3/026/027 precedent; the /091 Critic Item 4 root-caused it: `frac_positive_paths` 0.356 — IS-weak, a noisy single-seed fit that drew a lucky OOS window). The /091 closeout records this explicitly: **the +0.4613 single-seed draw must NOT be cited as evidence the trained `LGBMRanker` "works."**

A single-seed result — positive *or* negative — on a faint-rank-IC architecture is a lottery draw. The cross-sectional line cannot be honestly *closed* (or *revived*) on single-seed evidence. A multi-seed verdict is the only rigorous close.

### 1.3 — The /092 hypothesis

> **The cross-sectional `LGBMRanker` architecture, when run in its best-faith form (the trained `LGBMRanker` at the corrected-/091-horizon-EDA-best H=21 — Section 3.1) and validated multi-seed at the v3 CONFIRMATION spec (`--seeds 2`, `ENSEMBLE_SIZE=5`, `n_trials=35` — 10 models/cell), does NOT reach a net-positive OOS book and does NOT beat the /059 canonical baseline (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791) on the multi-seed mean. The single-seed cross-sectional results across /088-091 — including the /091 reference book's OOS +0.4613 — are lottery draws; the multi-seed mean regresses toward the IS-weak `frac_positive_paths ≈ 0.36` reading. /092 formally closes the cross-sectional `LGBMRanker` momentum-rank line as a route to a merge-grade book, on rigorous multi-seed evidence rather than a single-seed result. The honest expected classification is CONFIRMATION-NO-MERGE.**

This is a CONFIRMATION-grade closing verdict. It is honest framing — it is not defeatism, and it is not an edge hunt. The cross-sectional architecture produced a real, statistically-significant OOS *signal transfer* (the rank-IC) — that knowledge is worth carrying forward. But across four single-seed iterations it never produced a net-positive *book*, the two genuine edge attempts (/090, /091) both failed, and the corrected /091 horizon EDA itself shows even the best-faith trained-ranker form (H=21, 35-trial) reaches only IS net monthly Sharpe +0.0944 — far below the +1.0 floor. /092's job is to convert "four single-seed iterations suggest the line does not work" into "a multi-seed CONFIRMATION-grade verdict establishes the line does not reach merge grade" — the rigorous close. The honest pre-registered modal outcome is CONFIRMATION-NO-MERGE; the brief weights a multi-seed revival of the line at a small but non-zero tail (Section 7), and Section 4 pre-registers exactly what a multi-seed result would have to clear to revive it.

### 1.4 — The closing verdict covers the WHOLE cross-sectional line

The /092 multi-seed dimension applies to the **trained `LGBMRanker` book only** — that is the book with a seed-dependent Optuna/model surface. The /091 **model-free book is parameter-free and deterministic**: its /091 result (IS net +0.0170 / OOS net −0.0995, OOS gross −0.0178; CONSTRUCTION-FALSIFIED) is already final — there is no seed variance to validate, and re-running it would reproduce the same numbers bit-for-bit. So /092's closing verdict covers the whole cross-sectional line by composition:

- **The trained `LGBMRanker` book** — multi-seed-validated in /092 (this brief). The closing verdict on the trained book is the /092 multi-seed result.
- **The model-free book** — already settled at /091 (CONSTRUCTION-FALSIFIED; OOS gross net-negative). /092 does not re-run it; the /092 diary will cite the /091 settled result as the model-free leg of the closing verdict.

The /092 closing verdict, stated once in the Phase-8 diary, is: *the cross-sectional momentum-rank line — trained `LGBMRanker` (multi-seed, /092) and model-free score (/091) — is closed as a route to a merge-grade book.*

---

## Section 2 — IS-Only Numerical Evidence

This is a CONFIRMATION; per `feedback_v3_eda_walkforward_faithful.md` and the /091 Critic Recommendation 1, **/092 introduces minimal new EDA** and cites the existing committed cross-sectional EDA. The evidence below is all from already-committed `analysis/iteration_v3-088/`, `/089/`, `/091/` scripts and the corrected /091 horizon grid. **No new EDA script is committed for /092.** The reasoning for the H=21 configuration choice (Section 3.1) rests entirely on the committed, *embargo-corrected* /091 horizon grid.

### 2.1 — The corrected /091 horizon grid — the trained `LGBMRanker` is horizon-sensitive, and H=3 (the /089 setting) is its WORST horizon

The /091 EDA `analysis/iteration_v3-091/holding_horizon_eda.py` scanned the holding-horizon grid {3, 7, 14, 21, 28, 35} bars, training the actual `cross_sectional.py` `LGBMRanker` per horizon on a horizon-matched label, with the **corrected** walk-forward embargo (`embargo_ms = (XS_HORIZON+1)·interval_ms` — the /091 Phase-5.5-BLOCK fix; the prior bug over-embargoed by N=22×). `H1_horizon_grid.csv` (trained ranker, EDA's 8-trial budget):

| H (bars) | ~days | XS_REQUIRED_GAP | IS-train rank-IC | IS gross monthly Sharpe | IS net monthly Sharpe | IS turnover/bar | IS fees/\|gross\| |
|---:|---:|---:|---:|---:|---:|---:|---:|
| **3** | 1.0 | 88 | +0.2033 | +0.0537 | **−0.2917** | 0.1205 | 0.057 |
| 7 | 2.33 | 176 | +0.2502 | −0.1651 | −0.3112 | 0.0924 | 0.924 |
| 14 | 4.67 | 330 | +0.3659 | +0.0108 | −0.0746 | 0.0349 | 7.954 |
| **21** | 7.0 | 484 | +0.4002 | **+0.0510** | **−0.0125** | 0.0243 | 1.246 |
| 28 | 9.33 | 638 | +0.4031 | +0.0292 | −0.0093 | 0.0177 | 1.318 |
| 35 | 11.67 | 792 | +0.4153 | +0.0381 | −0.0016 | 0.0147 | 1.042 |

The finding is decisive: **H=3 — the /089/090/091 trained-ranker incumbent — is the WORST horizon on IS net spread monthly Sharpe (−0.2917).** The IS-train rank-IC climbs monotonically with H (the `LGBMRanker` learns a stronger horizon-matched signal at longer horizons: +0.2033 at H=3 → +0.4002 at H=21), and the longer-horizon books also collapse turnover (0.1205/bar at H=3 → 0.0243/bar at H=21). The /089 H=3 trained book was the trained ranker at its weakest horizon.

### 2.2 — H=21 is the corrected-EDA-best trained-ranker horizon at the FULL 35-trial runner budget — M2

`H1_horizon_grid.csv` ran the trained ranker at the EDA's light 8-trial budget. The /091 EDA's M-block then ran the **trial-budget sensitivity** at H=21 — `M2_lgbmranker_trial_budget.csv`:

| n_optuna_trials | config | trained `LGBMRanker` gross monthly Sharpe | trained `LGBMRanker` net monthly Sharpe | mean IS-train rank-IC | turnover/bar |
|---:|---|---:|---:|---:|---:|
| 8 | 8-trial (H1-EDA) | +0.0510 | −0.0125 | +0.4002 | 0.0243 |
| **35** | **35-trial (runner)** | **+0.1534** | **+0.0944** | +0.3977 | 0.0249 |

At H=21 the trained `LGBMRanker` at the **full 35-trial runner budget** reaches **IS net monthly Sharpe +0.0944 / IS gross monthly Sharpe +0.1534** — the trained ranker's best-faith IS form across the entire grid. (Note the M2 35-trial figure is a *single-seed* EDA measurement — /092 multi-seed-validates exactly this.) Among the trained-ranker horizons, H=21 is the corrected-EDA IS-best at the runner's actual trial budget. This is the basis for the Section-3.1 decision to validate the trained ranker **at H=21**, not at the /089 H=3 setting.

### 2.3 — Why the /092 configuration must be the BEST-faith form, not the /089 incumbent

A closing verdict must test the architecture's *best-faith* form — a verdict that fails the trained `LGBMRanker` at H=3 (its worst horizon, Section 2.1) would be a strawman close. The corrected /091 horizon EDA hands /092 the trained ranker's IS-best horizon (H=21, M2 35-trial IS net +0.0944), so /092 multi-seed-validates **the trained `LGBMRanker` at H=21** — the configuration that gives the cross-sectional `LGBMRanker` architecture its single fairest shot. If the multi-seed mean of the trained ranker's *best-faith* form does not clear the floors, the line is closed on the strongest possible evidence.

This is also why /092 is not the /091 model-free book: the /091 model-free book at H=21 is already settled (CONSTRUCTION-FALSIFIED, OOS gross net-negative −0.0178, deterministic — no seed variance) and the /091 EDA M2 shows the trained ranker at H=21/35-trial *beats* the model-free book on IS net (+0.0944 vs the model-free book's runner IS net +0.0170). The trained `LGBMRanker` at H=21 is the cross-sectional line's best-faith trained form; that is what /092 closes the verdict on.

### 2.4 — The honest read of the IS evidence — even the best-faith form is far sub-floor

The IS evidence is unambiguous and it is the basis for the honest pre-registered CONFIRMATION-NO-MERGE expectation (Section 7, Section 8):

1. The trained `LGBMRanker` at its best-faith IS configuration (H=21, 35-trial) reaches **IS net monthly Sharpe +0.0944** (M2). That is a *positive* IS net book — a real improvement over the /089 H=3 incumbent (IS net −0.1960) — but it is **an order of magnitude below the +1.0 IS floor**.
2. The IS gross monthly Sharpe at the best-faith form is +0.1534 (M2) — the cross-sectional gross spread is genuinely thin, as four iterations established.
3. The /091 corrected horizon grid shows no horizon lifts the trained ranker's IS net spread above breakeven-plus-a-bit (the H1 grid max is H=35 at −0.0016 on the 8-trial EDA budget; M2's 35-trial H=21 reaches +0.0944).
4. The cross-sectional OOS rank-IC across /088-091 is +0.03 to +0.04 — real (it transfers) but faint.

A best-faith IS net monthly Sharpe of +0.0944 cannot, on any honest reading, produce an OOS multi-seed mean clearing the +1.0 OOS floor. The IS evidence pre-registers the CONFIRMATION-NO-MERGE expectation — and /092 runs the multi-seed validation to *establish* it rigorously rather than assert it from single-seed EDA.

### 2.5 — Why no new EDA is committed for /092 (the /091 Critic Recommendation 1 discipline)

The /091 closeout's load-bearing process lesson (`diary-v3/iteration_v3-091.md` Section 4; Critic Recommendation 1) is the **EDA-vs-runner IS-window mismatch**: the /091 brief's predictions rested on an EDA harness (`model_free_horizon_scan` / `_run_cost_aware_book`) that scored the *full* 2020-04→2025-03 IS panel with **no walk-forward segmentation**, while the runner's walk-forward IS book is structurally restricted to 2022-03→2025-03 (the first 24 months are training-only). The EDA's M1b sub-period table proves the gap: the excluded 2020-21 third carries net +0.5564, so a full-panel EDA number is inflated relative to the runner.

/092 does not commit a new EDA precisely to avoid re-introducing that flaw. The /092 configuration choice (H=21) rests on the **`H1_horizon_grid.csv`** — which IS walk-forward-faithful: `holding_horizon_eda.py::train_rankers_for_horizon` + `is_internal_backtest` run a *true* IS-internal monthly walk-forward (`_generate_xs_monthly_splits(training_months=24)`, train on IS months, predict the next IS month — `holding_horizon_eda.py` lines 258-386, 504-545). The H1 grid's IS net figures are measured on the runner's own walk-forward cadence, so they are runner-faithful for the *trained-ranker* path. The M2 trial-budget table is the same harness at the runner's 35-trial budget. (The M1-block model-free numbers — `M1a`/`M1b`/`M2_model_free` — are the ones that carry the full-panel flaw; /092 cites **only** the trained-ranker `H1`/`M2` figures, which are walk-forward-faithful, and the /091 model-free settled result for the model-free leg.) The /092 verdict is gated on the runner's own multi-seed `comparison.csv` artifacts (Section 4) — never an EDA number.

---

## Section 3 — Proposed Changes (the /092 build spec — the QE Phase-6 build)

iter-v3/092 is a CONFIRMATION-grade multi-seed *validation* run. There is **no new edge axis**. The /092 build has exactly two components: (A) the pre-registered cross-sectional configuration to validate, and (B) **multi-seed support built into the cross-sectional runner** — which the runner does not currently have.

### 3.1 — The configuration /092 multi-seed-validates (pre-registered, LOCKED)

The configuration is the cross-sectional `LGBMRanker` architecture in its **best-faith form**, fully pre-registered:

| Component | /092 value | Source |
|---|---|---|
| Score mode | **`score_mode="trained"`** — the pooled `LGBMRanker(lambdarank)`, monthly walk-forward | `cross_sectional.py` — the /088/089 model; the trained book is the seed-dependent book a multi-seed run validates. The /091 model-free book is parameter-free/deterministic — already settled at /091; not re-run (Section 1.4). |
| **Horizon H** | **`XS_HORIZON = 21`** (and the horizon-matched `XS_HOLD_BARS = 21`) | Corrected /091 horizon EDA — `H1_horizon_grid.csv` + `M2_lgbmranker_trial_budget.csv`: H=21 is the trained ranker's corrected-EDA-best IS net horizon at the 35-trial runner budget (IS net +0.0944). The /089 H=3 setting is the trained ranker's WORST horizon (Section 2.1) — a closing verdict tests the best-faith form. |
| Universe | the 22-symbol `XS_UNIVERSE` | /088 — unchanged across the whole cross-sectional line. |
| Feature stack | the 13-feature cross-sectional stack (`V3_FEATURE_COLUMNS_TOP_N` minus `btc_ret_14d`), cross-sectionally rank-normalized | /088 — unchanged. The /090 downside-feature expansion stays REVERTED (FALSIFIED). `XS_FEATURE_COLUMNS` = 13. |
| Label | `label_cross_sectional_rank`, **horizon-matched at H=21** forward-return tercile grade | /091 — the horizon-matched label (a longer hold requires the label to predict the H=21-bar-forward rank). |
| Cost-aware construction | quintile legs (`XS_QUANTILE_FRAC = 0.20`), 21-bar overlapping holds (`XS_HOLD_BARS = 21`), no-trade band (`XS_NO_TRADE_BAND = 0.020`), hard turnover ceiling (`XS_TURNOVER_CEILING = 0.138`) | /089 — RETAINED verbatim. The /089 construction is the established cross-sectional construction baseline. |
| Embargo | walk-forward `embargo_ms = (XS_HORIZON+1)·interval_ms`; CPCV `XS_REQUIRED_GAP = (H+1)·N = 484` | /091 — the corrected embargo (the /091 Phase-5.5-BLOCK fix). At H=21 these are already the live constants in `cross_sectional.py` — verified Section 3.4. |
| Sign | LONG the top quantile (high score = predicted future winner), SHORT the bottom | /089 — the SIGN FIX, RETAINED. |

**This configuration is bit-identical to the `score_mode="trained"` reference book the /091 runner already produces** — `XS_HORIZON = 21`, `XS_HOLD_BARS = 21`, the 13-feature stack, the /089 construction, the corrected embargo are all already the live state of `cross_sectional.py` (Section 3.4). The /092 build does **not** change the configuration or add a score path. The *only* /092 build work is making the runner produce this book **multi-seed** instead of single-seed.

### 3.2 — The multi-seed CONFIRMATION spec (the v3 CONFIRMATION standard)

Per `feedback_v3_outer_seed_cap_2_v3.md` (v3 CONFIRMATION runs use `--seeds 2` max — 5 inner × 2 outer = **10 models/cell**, vs 25; inner ensemble stays at 5 for live-prediction variance reduction; supersedes the 10-seed rule for v3) and `feedback_v3_confirmation_n_trials_35.md` (v3 CONFIRMATION default `--n-trials 35`):

- **Outer seeds**: `--seeds 2` → outer seed set **{42, 123}** (the v3 canonical outer-seed lineage — `BASELINE_V3.md` "Unified 10-Seed Ensemble Architecture": seeds 0-4 are the outer=42 lineage, seeds 5-9 the outer=123 lineage; the two-outer CONFIRMATION uses the lineage roots 42 and 123).
- **Inner ensemble**: `ENSEMBLE_SIZE = 5` per outer seed.
- **Total**: 5 inner × 2 outer = **10 trained `LGBMRanker` models per (walk-forward month) cell**.
- **Optuna trials**: `n_trials = 35` per model.

### 3.3 — Multi-seed support MUST be built into the cross-sectional runner — a Phase-6 build item for the QE

**The cross-sectional runner does NOT currently support multi-seed.** The /088-091 cross-sectional runs were all single-seed=42:
- `run_cross_sectional_v3.py::_run_one_book` (lines 678-760) constructs **one** `CrossSectionalRankStrategy` with **one** `seed=args.seed` (default 42), `ensemble_size=1` hardcoded in the `_write_xs_reports` call (line 759).
- `CrossSectionalRankStrategy.__init__` (`cross_sectional.py` lines 512-539) takes a single `seed` and trains **one** `LGBMRanker` per month (`_train_for_month` lines 545-602 — one `TPESampler(seed=self.seed)`, one `study`, one `self._model`).
- There is no inner ensemble and no outer-seed loop anywhere in the cross-sectional path.

This is QE work in `src`/runner code — **the QR does NOT implement it**; it is specified here precisely as a mandatory /092 Phase-6 build item, exactly as the /090 closeout flagged the gross-Sharpe runner artifact as a /091 setup item (`feedback_v3_methodology_axis_integration_test.md` discipline — a methodology/instrumentation build the QR specs and the QE implements). The QE builds multi-seed support at the /092 setup commit, before the /092 backtest.

**The precise multi-seed spec the QE must implement:**

1. **An outer-seed loop over {42, 123}.** The runner runs the cross-sectional walk-forward backtest twice — once per outer seed. The two outer seeds are passed explicitly (a runner constant `CONFIRMATION_OUTER_SEEDS = (42, 123)`, not a CLI default), with a `--seeds` argument controlling the count (`--seeds 2` → the first 2 elements of `CONFIRMATION_OUTER_SEEDS`).

   **`--seeds` naming-conflict note (mandatory — for the QE).** The per-symbol baseline runner `run_baseline_v3.py` also has a `--seeds` argument, but it was **DEPRECATED at iter-v3/059** (`run_baseline_v3.py` lines 2604-2611) — that runner's outer-seed loop was eliminated and a passed `--seeds` value now prints a `WARNING` and is *ignored*. The cross-sectional runner's `--seeds` is a **NEW, independent argument** added by /092 to `run_cross_sectional_v3.py` (which has no `--seeds` argument today): it has **different semantics** — it actively controls the cross-sectional runner's outer-seed count (selecting the first N elements of `CONFIRMATION_OUTER_SEEDS`). The QE **must NOT** copy the per-symbol runner's deprecation behaviour into the cross-sectional runner: the cross-sectional `--seeds` is live and functional, emits **no** deprecation warning, and is **not** ignored. The name coincidence with the deprecated per-symbol `--seeds` is incidental; the two arguments live in two different runners and do not share code.

2. **A 5-model inner ensemble per outer seed.** For each outer seed `s`, derive 5 inner seeds via `_derive_ensemble_seeds(s, 5)` — the **same** seed-derivation the v3 per-symbol baseline uses (referenced in `BASELINE_V3.md` "Unified 10-Seed Ensemble Architecture": `ENSEMBLE_SEEDS[0:5] == _derive_ensemble_seeds(42, 5)`, `[5:10] == _derive_ensemble_seeds(123, 5)`).

   **Reuse mechanism — SPECIFIED (mechanism A — copy verbatim, no `src/` change).** `_derive_ensemble_seeds` is a **module-private function in `run_baseline_v3.py` (lines 119-128 at `c6a03ed`)** — it is NOT in any importable `src/` module, so it cannot be `import`-ed. The QE **copies the `_derive_ensemble_seeds` function body verbatim from `run_baseline_v3.py` lines 119-128 into `run_cross_sectional_v3.py`** (a self-contained module-private function in the cross-sectional runner). The function body to copy is exactly:

   ```python
   def _derive_ensemble_seeds(outer_seed: int, size: int = 5) -> list[int]:
       rng = np.random.default_rng(outer_seed)
       return [int(s) for s in rng.integers(low=0, high=2**31 - 1, size=size)]
   ```

   This is the minimal-footprint mechanism: it leaves the stable per-symbol runner `run_baseline_v3.py` **completely untouched** (no `src/` change, no per-symbol-runner test update). Mechanism B (moving the helper to a shared `src/crypto_trade/strategies/ml/` module and importing it in both runners) was considered and **rejected** for /092: /092 is a *closing* CONFIRMATION on a line being set down, so a `src/`-level refactor that perturbs the per-symbol baseline runner is unwarranted footprint for a one-shot multi-seed validation. The copied function is verbatim-identical, so it reproduces the `BASELINE_V3.md` lineage bit-for-bit. The QE does NOT re-derive or modify the function — copy it exactly. The integration test (item 7(iv)) **imports `_derive_ensemble_seeds` from `run_cross_sectional_v3`** (the copied function) to verify it reproduces the `BASELINE_V3.md` lineage values.

   For each (walk-forward month) cell, train **5** `LGBMRanker` models, one per inner seed. **The inner-ensemble prediction is the arithmetic mean of the 5 models' `predict()` score vectors** at each (timestamp, symbol) — averaged on the *raw ranker score*, then the cross-sectional quantile cut and the /089 construction are applied to the averaged score. (Averaging the score, not the positions, is the correct ensemble point — the score is the model output; the quantile/construction is deterministic given the score. This mirrors the per-symbol baseline's proba-averaging — `BASELINE_V3.md`: "one inference path with proba averaging across all 10 models".)

3. **Per-outer-seed reports + a multi-seed aggregate.** Each outer seed `s` writes a full report set to `reports-v3/iteration_v3-092/seed_<s>/` (the same `comparison.csv` / `cpcv_paths.csv` / `dsr.json` / `rank_ic.csv` / `in_sample/` / `out_of_sample/` layout the cross-sectional runner already emits via `_write_xs_reports`). The runner then writes a **multi-seed aggregate** to `reports-v3/iteration_v3-092/`:
   - `comparison.csv` — the **multi-seed-mean** IS and OOS monthly Sharpe, gross monthly Sharpe, MaxDD, turnover/bar, rank-IC, plus the **per-seed values** for each (so the spread across the 2 outer seeds is visible) and the **min across seeds** for each headline metric.
   - `ensemble_summary.json` — one row per outer seed with {outer_seed, IS monthly Sharpe, OOS monthly Sharpe, IS gross, OOS gross, OOS rank-IC, frac_positive_paths, IS turnover/bar}, plus the multi-seed mean and the multi-seed min. (Naming mirrors the per-symbol baseline's `ensemble_summary.json`.)
   - `dsr.json` — DSR / PBO / PSR computed on the multi-seed-aggregated book (Section 4.3 specifies the inputs).
4. **The CPCV `frac_positive_paths`** is computed per outer seed and the aggregate reports the **mean** `frac_positive_paths` across the 2 outer seeds (the existing `_compute_xs_cpcv` runs per seed; the aggregate averages).

5. **A 2-seed Pareto check.** The aggregate reports whether **both** outer seeds are individually OOS-net-positive (the v3 CONFIRMATION Pareto gate, Section 4 — Gate 10). This is a boolean in `ensemble_summary.json`.

6. **Reproducibility.** Each outer seed pins its `TPESampler` and `LGBMRanker(random_state=...)` to its derived inner seeds. `feature_columns = XS_FEATURE_COLUMNS` passed explicitly (the existing `ValueError`-on-empty guard stays). `ITERATION_LABEL = "v3-092"`.

7. **Smoke test + integration test (mandatory — `feedback_v3_methodology_axis_integration_test.md`).** Because multi-seed support is a runner-architecture change, the /092 build MUST include: (a) a fast smoke test asserting the outer-seed loop runs twice and produces two `seed_<s>/` report sets and one aggregate; (b) an integration test in `tests/strategies/ml/test_cross_sectional.py` asserting (i) the 5 inner models per cell are distinct objects with the 5 derived seeds, (ii) the inner-ensemble score is the arithmetic mean of the 5 `predict()` vectors, (iii) the aggregate `comparison.csv` multi-seed-mean equals the mean of the two `seed_<s>/comparison.csv` values, (iv) `_derive_ensemble_seeds(42,5)` and `_derive_ensemble_seeds(123,5)` reproduce the `BASELINE_V3.md` lineage tuple — i.e. the cross-sectional runner reuses the *same* derivation as the per-symbol baseline.

**What multi-seed support does NOT touch:** the model architecture (`LGBMRanker(lambdarank)` unchanged), the 13-feature stack, the /089 cost-aware construction, the H=21 horizon/label, the corrected embargo, the `XS_UNIVERSE`. The /091 model-free `score_mode` path is left intact but unused by /092 (the /092 run is `score_mode="trained"` only). This is a *seed-dimension* build, nothing else — exactly the iter-v3/018 CONFIRMATION discipline (multi-seed validation, no axis variation).

### 3.4 — What is ALREADY the live runner state (no /092 build needed)

The /092 configuration (Section 3.1) is already the live state of `cross_sectional.py` at `c6a03ed` — verified:
- `XS_HORIZON = 21` (`cross_sectional.py` line 95), `XS_REQUIRED_GAP = (H+1)·N = 484` (line 107), `XS_HOLD_BARS = 21`.
- `XS_QUANTILE_FRAC = 0.20`, `XS_NO_TRADE_BAND = 0.020`, `XS_TURNOVER_CEILING = 0.138` — the /089 construction constants.
- The corrected embargo `embargo_ms = (XS_HORIZON+1)·interval_ms` (`cross_sectional.py` line 998; `run_cross_sectional_v3.py` line 915) — the /091 fix.
- `XS_FEATURE_COLUMNS` = the 13-feature base, `/090` downside features reverted (`run_cross_sectional_v3.py` lines 104-107, `_verify_feature_columns` lines 184-212).
- The `gross_monthly_sharpe` shared-helper runner artifact (`_monthly_sharpe`, the /091 SETUP-2 fix) — RETAINED; the multi-seed aggregate's `comparison.csv` reuses it.

So the /092 build is **purely** the Section-3.3 multi-seed support. The QE confirms the Section-3.4 state at the setup commit and then builds the multi-seed loop.

### 3.5 — Phase-6 build scope (the QE Phase-6 build, ordered)

1. **Setup commit** — `ITERATION_LABEL "v3-092"`; confirm the Section-3.4 live state; add `CONFIRMATION_OUTER_SEEDS = (42, 123)`; add the `--seeds` count argument.
2. Build the multi-seed support per Section 3.3 (outer-seed loop + 5-model inner ensemble + score-averaging + per-seed and aggregate reports + `ensemble_summary.json` + the 2-seed Pareto boolean).
3. Add the smoke test + the integration test (Section 3.3 item 7).
4. Run the multi-seed cross-sectional backtest: `uv run python run_cross_sectional_v3.py --skip-features --seeds 2 --n-trials 35` (`--skip-features` if the 22 v3 parquets are fresh). Emit per-seed reports + the multi-seed aggregate.
5. Write the engineering report — report the **multi-seed-mean** IS/OOS monthly Sharpe + gross + the per-seed spread + `frac_positive_paths` mean + the 2-seed Pareto boolean + DSR/PBO/PSR on the aggregate, and evaluate every Section-4 gate.

### 3.6 — Risk framework

Unchanged from the /089 cross-sectional construction — the cross-sectional book is risk-managed structurally (Section 5/6). /092 adds no new risk primitive (it is a multi-seed validation, not a new axis). The multi-seed ensemble is itself a variance-reduction control (Section 5).

---

## Section 4 — Pre-Registered MERGE / NO-MERGE Numerical Criteria

### 4.1 — The standard CONFIRMATION merge gates

iter-v3/092 is a CONFIRMATION. The standard v3 CONFIRMATION merge gates apply — evaluated on the **multi-seed-mean** book (the trained `LGBMRanker` at H=21, 10 models/cell). The cross-sectional book is a market-neutral long-short book; per the /088/089/091 brief Section 4.1 it is not directly comparable in *return-distribution shape* to the /059 per-symbol book — but the **absolute floors are the absolute floors** (the v3 merge floors are not architecture-conditional), and /092's whole purpose is the verdict against them.

| # | Gate | Threshold | Evaluated on |
|---|---|---|---|
| G1 | IS monthly Sharpe | ≥ +1.0 | multi-seed mean |
| G2 | OOS monthly Sharpe | ≥ +1.0 | multi-seed mean |
| G3 | OOS / IS monthly Sharpe ratio | ≥ 0.5 | multi-seed mean (evaluated only when both are positive; if either ≤ 0, G3 N/A and G1/G2 govern) |
| G4 | DSR (Deflated Sharpe Ratio) | > 0.95 | multi-seed-aggregate book |
| G5 | PBO (Probability of Backtest Overfitting) | < 0.4 | multi-seed-aggregate book |
| G6 | PSR (Probabilistic Sharpe Ratio) | > 0.95 | multi-seed-aggregate book |
| G7 | OOS trade count | ≥ 130 total | multi-seed-aggregate book |
| G8 | Top-symbol concentration | ≤ 30% of OOS book PnL | multi-seed-aggregate book |
| G9 | OOS rank-IC | > 0 | multi-seed mean (the cross-sectional architecture-validity signal) |
| G10 | 2-seed Pareto | BOTH outer seeds individually OOS-net-positive | per-seed `ensemble_summary.json` |

### 4.2 — Pre-registered CONFIRMATION-MERGE / CONFIRMATION-NO-MERGE criteria (LOCKED)

Evaluated in Phase 7 against the multi-seed-aggregate runner artifacts. **These are gates, not predictions** (`feedback_v3_per_symbol_target_axis_falsifier.md`).

**CONFIRMATION-MERGE** fires **only if ALL of the following hold**:
- G1 **AND** G2 — IS multi-seed-mean monthly Sharpe ≥ +1.0 **AND** OOS multi-seed-mean monthly Sharpe ≥ +1.0; **AND**
- G3 — OOS/IS multi-seed-mean ratio ≥ 0.5; **AND**
- G4 **AND** G5 **AND** G6 — DSR > 0.95 **AND** PBO < 0.4 **AND** PSR > 0.95; **AND**
- G7 — OOS aggregate trade count ≥ 130; **AND**
- G8 — top-symbol OOS concentration ≤ 30%; **AND**
- G9 — OOS multi-seed-mean rank-IC > 0; **AND**
- G10 — both outer seeds individually OOS-net-positive.

**CONFIRMATION-NO-MERGE** fires if **any** CONFIRMATION-MERGE conjunct fails. Given the IS evidence (Section 2.4 — the best-faith IS net monthly Sharpe is +0.0944, an order of magnitude below the +1.0 floor), CONFIRMATION-NO-MERGE is the **honest pre-registered expected outcome** (Section 7, Section 8).

### 4.3 — DSR / PBO / PSR inputs (pre-registered, for the QE)

The cross-sectional path has historically emitted DSR/PSR sentinels at EXPLORATION (`feedback_v3_dsr_mode_artifact.md` — EXPLORATION-mode DSR is a regime-specific artifact). **/092 is a CONFIRMATION, not an EXPLORATION** — so DSR/PBO/PSR are computed for real and are MERGE gates (G4/G5/G6). The QE computes them on the multi-seed-aggregate book:
- **PSR** — Probabilistic Sharpe Ratio of the multi-seed-aggregate OOS monthly-Sharpe series against a benchmark Sharpe of 0, using the OOS monthly return series (15 OOS months — `out_of_sample/monthly_pnl.csv`), with the standard skew/kurtosis correction.
- **DSR** — the Deflated Sharpe Ratio: PSR deflated for the trial count. The trial count for /092 is the CONFIRMATION trial budget — `n_trials × ENSEMBLE_SIZE × n_outer_seeds = 35 × 5 × 2 = 350` per (walk-forward month) cell; the QE uses the v3 CONFIRMATION DSR convention (the same `dsr.py` path the per-symbol baseline uses — the QE locates the canonical v3 DSR helper and applies it; per `feedback_v3_methodology_post_hoc_input_traceback.md`, the QE documents in the engineering report the exact code path and the exact SR granularity fed to `psr()` — trade-level vs monthly — so the input granularity is not a hidden assumption).
- **PBO** — via CPCV: the multi-seed-aggregate `cpcv_paths.csv` `frac_positive_paths` informs the PBO; the cross-sectional `_compute_xs_cpcv` already computes the actual long-short net-return Sharpe per CPCV path (the /089 CPCV-proxy fix). PBO = the fraction of CPCV paths where the IS-selected configuration underperforms the path's OOS median.

If DSR/PBO/PSR are structurally not computable on the multi-seed-aggregate cross-sectional book (e.g. too few OOS months for a stable PSR), the QE emits an **honest sentinel with an explicit note** (NOT a fabricated value) and the gate is recorded as a FAIL — a CONFIRMATION cannot MERGE on an uncomputable gate. This is the `feedback_v3_methodology_axis_integration_test.md` discipline.

### 4.4 — BASELINE_V3.md update policy

Per `feedback_v3_strict_both_is_oos_baseline.md` and `feedback_v3_baseline_update_policy.md`: **/092 updates `BASELINE_V3.md` ONLY if it beats the /059 canonical baseline (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791) on BOTH IS Sharpe AND OOS Sharpe (multi-seed mean) AND both Pareto seeds are positive.** Given the IS evidence (best-faith IS net +0.0944), this is not the expected outcome — the honest expectation is **BASELINE_V3.md UNCHANGED**, /059 stays canonical, tag `v0.v3-059`. /092 does **not** touch `BASELINE_V3.md` unless the multi-seed run — against the Section-7 expectation — clears the policy. The `feedback_v3_iter018_baseline_bootstrap.md` one-time bootstrap exception does NOT apply (v3 has had a formal baseline since /018; /059 is the current canonical anchor).

### 4.5 — The honest note on the cross-sectional book's comparability

The cross-sectional long-short book and the /059 per-symbol book are different return objects (different beta, turnover, distribution). But /092's verdict does not rest on a delta-vs-/059 comparison — it rests on the **absolute floors** (G1/G2) and the **architecture-internal gates** (G9 rank-IC; G10 Pareto; G4-G6 DSR/PBO/PSR). The /059 comparison enters only at the BASELINE_V3.md update gate (Section 4.4) and there the rule is unambiguous: beat /059 on BOTH axes or BASELINE_V3.md is UNCHANGED.

---

## Section 5 — Risk Mitigation

Per `feedback_v3_risk_mitigation_design.md`, every merge-candidate iteration carries a Risk Mitigation section. /092's controls are the /089 cost-aware cross-sectional construction's structural controls, **plus** the multi-seed ensemble itself as the /092-specific risk addition:

| Risk | Mitigation | IS-calibrated / a-priori | Simulated historical effect |
|---|---|---|---|
| **Single-seed lottery (the /092-specific risk)** | The multi-seed CONFIRMATION ensemble — 10 models/cell (5 inner × 2 outer), score-averaged | a-priori (`feedback_v3_outer_seed_cap_2_v3.md`) | The /091 reference book's single-seed OOS +0.4613 vs IS −0.1107 (ratio −4.17) is the documented single-seed-inversion artifact a multi-seed mean dissolves; /092 measures the multi-seed mean directly |
| Turnover / fee drag | 21-bar overlapping holds + no-trade band τ=0.020 + the HARD turnover ceiling 0.138 | IS-selected (/089 EDA + the /091 horizon grid: H=21 IS turnover/bar 0.0243) | /091 H1 grid: at H=21 the IS turnover/bar is 0.0243 — far inside the 0.138 ceiling; the longer hold collapses the drag |
| Directional market drawdown | dollar-neutral long-short construction | a-priori (construction) | /088-091: market beta removed by design |
| Single-symbol concentration | quintile long-short — ~4-5 names/leg | a-priori (construction) | /091 H1 grid: max IS symbol concentration at H=21 is 11.3% — structurally < 30% |
| High-vol-symbol domination | inverse-vol weighting within each leg + portfolio vol-targeting | a-priori (standard cross-sectional construction) | /088-091: per-symbol concentration capped |
| Listing non-stationarity | 60-day (180-bar) listing burn-in per symbol | a-priori (crypto pitfall) | /088-091: applied; signal measured with it active |
| Label look-ahead | `XS_REQUIRED_GAP = 484` pooled-CPCV purge; walk-forward `embargo_ms = (H+1)·interval_ms` (the corrected /091 embargo) | a-priori (formula); /091 Phase-5.5 + Critic verified | /091 Critic Check 1/2 PASS — the corrected embargo verified at both code sites |

The /092-specific risk addition is the **multi-seed ensemble**, and its purpose IS the risk control — it is the mechanism by which /092 produces a lottery-robust verdict rather than a single-seed draw.

## Section 6 — Risk Management Design

The cross-sectional book is risk-managed by construction (Section 5) — dollar-neutral + inverse-vol + vol-targeting + quintile diversification + 21-bar overlapping-hold tranching + the no-trade band + the HARD turnover ceiling. The legacy v3 7-gate per-symbol stack stays **deferred** for the cross-sectional path (re-introducing per-symbol gates onto a market-neutral cross-sectional book would confound the verdict — the same honest scoping call /088/089/091 made; the cross-sectional gate re-design was never reached because the line never produced a net-positive book to gate). /092 adds no new gate — it is a multi-seed validation of the existing construction, not a new risk axis.

---

## Section 7 — Pre-Registered Failure-Mode Prediction (honest)

This is a CONFIRMATION-grade closing verdict; the prediction distribution reflects that the IS evidence (Section 2.4) points firmly at sub-floor, and that the cross-sectional line's four-iteration ledger is near-breakeven-never-positive. The honest distribution:

- **≈70% — the modal outcome: CONFIRMATION-NO-MERGE, the multi-seed verdict cleanly closes the line.** The multi-seed-mean OOS monthly Sharpe lands near breakeven — roughly **[−0.20, +0.30]** — far below the +1.0 OOS floor; the multi-seed-mean IS monthly Sharpe lands roughly **[−0.05, +0.25]** (around the M2 best-faith single-seed +0.0944, with multi-seed averaging tightening it); the OOS rank-IC stays faintly positive (G9 passes — the architecture's signal transfer is real); G1/G2 fail decisively. The single-seed reference-book OOS +0.4613 regresses toward the IS-weak `frac_positive_paths ≈ 0.36` mean, as predicted. **This is the expected result** — a rigorous multi-seed close of the cross-sectional `LGBMRanker` line, exactly the disciplined verdict /092 exists to deliver.
- **≈15% — CONFIRMATION-NO-MERGE, but the multi-seed book is net-negative both windows.** The multi-seed mean lands negative on IS and/or OOS (the H=21 best-faith IS form's +0.0944 does not survive multi-seed averaging, or the OOS regime is momentum-compressing — the /091 closeout's documented OOS-window risk). Still CONFIRMATION-NO-MERGE; the line is closed harder.
- **≈10% — CONFIRMATION-NO-MERGE, but one or both outer seeds draw a lucky OOS window** (a partial repeat of the /091 reference-book single-seed inversion at the 2-outer-seed level). The multi-seed mean is dragged up by one seed but G10 (both seeds positive) and/or the +1.0 floors still fail. Recorded honestly: a 2-outer-seed CONFIRMATION is more robust than single-seed but is not immune to a correlated lucky draw — the brief names this so it is not rationalized post-hoc; it does not change the CONFIRMATION-NO-MERGE verdict.
- **≈5% — against expectation, CONFIRMATION-MERGE.** The multi-seed mean clears BOTH +1.0 floors, DSR/PBO/PSR pass, both Pareto seeds positive. The IS evidence (best-faith IS net +0.0944, an order of magnitude below +1.0) makes this the tail — named honestly, not expected. If it fires, the cross-sectional line is revived and BASELINE_V3.md is evaluated per Section 4.4.

The single most-likely outcome is the **≈70% CONFIRMATION-NO-MERGE clean close** — named here, honestly, as the expected result of a multi-seed CONFIRMATION-grade verdict on a four-iteration line whose best-faith IS form is an order of magnitude below the merge floor. /092 is not predicted to find edge; it is predicted to *close the verdict rigorously*, and that is its legitimate, cadence-respecting job.

---

## Section 8 — Pre-Registered Classification Taxonomy (LOCKED)

iter-v3/092 is the cycle-3 CONFIRMATION. The classification is a CONFIRMATION classification, evaluated in disjunctive precedence (first match canonical), on the multi-seed-aggregate runner artifacts:

### 8.1 — CONFIRMATION-MERGE
Fires iff **every** CONFIRMATION-MERGE conjunct in Section 4.2 holds — G1∧G2∧G3∧G4∧G5∧G6∧G7∧G8∧G9∧G10. The multi-seed-validated cross-sectional `LGBMRanker` book clears all absolute floors and all CONFIRMATION gates. The cross-sectional line is **revived** as a merge-grade architecture; BASELINE_V3.md is evaluated per Section 4.4 (updated iff /092 beats /059 on BOTH IS and OOS multi-seed mean). Honest pre-registered probability: **≈5%** (Section 7).

### 8.2 — CONFIRMATION-NO-MERGE (the honest modal outcome)
Fires iff **NOT 8.1** — any CONFIRMATION-MERGE conjunct in Section 4.2 fails. The multi-seed verdict establishes that the cross-sectional `LGBMRanker` momentum-rank line, in its best-faith form, does not reach a merge-grade book. **NO-MERGE.** BASELINE_V3.md UNCHANGED — /059 canonical, tag `v0.v3-059`. The /092 closing verdict (Section 1.4) is recorded in the Phase-8 diary: the cross-sectional momentum-rank line — trained `LGBMRanker` (multi-seed, /092) and model-free score (settled at /091) — is **formally closed** as a route to a merge-grade book; cycle 4 re-architects into a new signal class (the /091 closeout Section 9.3 records the candidate directions — derivatives-microstructure state-conditioning, crypto statistical arbitrage, regime-switching TSMOM — for the cycle-4 QR; /092 does not pre-commit cycle 4). The `cross_sectional.py` infrastructure is RETAINED as code (it is not deleted — it is a working, audited, reusable cross-sectional engine); but the momentum-rank *strategy* on it is closed. Honest pre-registered probability: **≈95%** (Section 7: 70% clean close + 15% net-negative + 10% lucky-draw-but-still-fails).

### 8.3 — CONFIRMATION-INCONCLUSIVE
Fires only if the Phase-6 multi-seed build did not reach a runnable two-outer-seed cross-sectional backtest (e.g. the multi-seed support build failed and only a single-seed book was produced). Recorded for completeness; the multi-seed support is a well-scoped build on the RETAINED, runnable `cross_sectional.py` infrastructure (Section 3.3), so this is not expected. If it fires, /092 is re-run as a corrected build — a CONFIRMATION that did not produce its CONFIRMATION-spec artifact cannot be filed as either MERGE or NO-MERGE.

**The honest pre-registered classification is CONFIRMATION-NO-MERGE (8.2).** This is stated plainly, in advance: /092 is a CONFIRMATION-grade closing verdict, the IS evidence points firmly sub-floor, and the legitimate value of /092 is the *rigorous multi-seed close* of v3's most substantial cycle-3 effort — not an edge discovery. A CONFIRMATION-NO-MERGE that definitively closes the cross-sectional `LGBMRanker` line on multi-seed evidence is a successful, cadence-respecting CONFIRMATION.

**A CONFIRMATION cannot be filed without its CONFIRMATION-spec multi-seed run completing.** BASELINE_V3.md stays `v0.v3-059` unless 8.1 fires AND the Section-4.4 policy is cleared.

---

## Section 9 — Library Stack Declaration

- **LightGBM** — `LGBMRanker` with `objective="lambdarank"` (the RETAINED /088 model; unchanged). Already a v3 dependency. The multi-seed build trains 10 `LGBMRanker` instances per cell (5 inner × 2 outer) instead of 1 — a count change, not a library change.
- **Optuna** — hyperparameter search (existing v3 dependency); `TPESampler` seeded per inner seed; CV objective = IS rank-IC. `n_trials = 35` per model (the v3 CONFIRMATION default).
- **pandas / numpy** — pooled-panel construction, the overlapping-tranche book, the no-trade band, the turnover diagnostic, the CPCV path net-return computation, the multi-seed score-averaging and report aggregation.
- **The v3 DSR/PBO/PSR helpers** — the canonical v3 `validation_v3` / `dsr` path (already a v3 dependency; `run_cross_sectional_v3.py` already imports `combinatorial_purged_cv` from `validation_v3`). /092 computes DSR/PBO/PSR for real (CONFIRMATION gates G4-G6) — the QE reuses the canonical v3 helpers, no new dependency.
- **No new third-party dependency.** Every /092 build component — the outer-seed loop, the 5-model inner ensemble, the score-averaging, the report aggregation, the multi-seed `comparison.csv`/`ensemble_summary.json` — is pure pandas/numpy + the existing LightGBM/Optuna stack on the RETAINED `cross_sectional.py`.

## Section 10 — QR Audit Trail

### 10.1 — The orchestrator dispatch and the QR call

The orchestrator dispatch LOCKED the **role** of /092 — the cycle-3 CONFIRMATION as a multi-seed CONFIRMATION-grade verdict on the cross-sectional `LGBMRanker` line (per the /091 closeout Section 9.2 recommendation and the /091 Critic Recommendation 2). Per `feedback_v3_axis_selection_quant_discipline.md`, the QR owns every *design* decision within that role. The QR's calls in this brief:

1. **The configuration to validate — the trained `LGBMRanker` at H=21, NOT the /089 H=3 incumbent.** The dispatch explicitly left this to the QR ("You decide the exact configuration /092 multi-seed-validates — the /089 H=3 cost-aware book, OR the `LGBMRanker` at the corrected-EDA-best horizon — and justify it"). The QR's call: **H=21**, on the committed, walk-forward-faithful corrected /091 horizon grid (`H1_horizon_grid.csv` — H=3 is the trained ranker's WORST horizon; `M2_lgbmranker_trial_budget.csv` — H=21 at the full 35-trial runner budget reaches the trained ranker's best-faith IS net +0.0944). A closing verdict must test the architecture's best-faith form (Section 2.3); validating it at H=3 would be a strawman close. This is the QR's EDA-grounded call.
2. **The score mode — `score_mode="trained"` only.** The /091 model-free book is parameter-free/deterministic — its /091 result is final; the multi-seed dimension applies only to the seed-dependent trained book (Section 1.4). The QR's call: /092 multi-seed-validates the trained book; the closing verdict covers the model-free leg by citing the settled /091 result.
3. **No new EDA.** Per the /091 Critic Recommendation 1 (the EDA-vs-runner IS-window-mismatch lesson), /092 commits no new EDA and rests the configuration choice on the committed, walk-forward-faithful trained-ranker horizon grid (Section 2.5). The QR's call: avoid re-introducing the /091 EDA-fidelity flaw by citing only walk-forward-faithful committed numbers.
4. **The honest framing — CONFIRMATION-NO-MERGE as the pre-registered modal outcome.** The QR's call: state plainly, in Section 1, 7, 8, that the expected outcome is CONFIRMATION-NO-MERGE and that /092's legitimate value is the rigorous multi-seed close, not an edge hunt — the /091 Critic Recommendation 2 mandates that /092 must NOT bundle the cross-sectional book as a validated edge ingredient, and this brief honours that throughout.

### 10.2 — Literature / methodology grounding

/092 is a multi-seed validation run, not a new-edge iteration — it carries no new literature axis. The methodology grounding it rests on:
- **The v3 CONFIRMATION conventions** — `feedback_v3_outer_seed_cap_2_v3.md` (the `--seeds 2` / 10-models/cell CONFIRMATION spec), `feedback_v3_confirmation_n_trials_35.md` (the `n_trials=35` CONFIRMATION default), `feedback_v3_iter018_confirmation_baseline_validation.md` (the iter-v3/018 precedent — a CONFIRMATION that is a multi-seed validation, not a bundle).
- **The seed-as-lottery discipline** — `feedback_v3_engineered_features_dont_stack.md` (the iter-v3/026/027 single-seed-inversion precedent), `feedback_v3_single_seed_frozen_baseline.md` (single-seed EXPLORATION determinism). The /091 reference book's OOS +0.4613 single-seed inversion is the direct, in-line proof that the cross-sectional line cannot be closed on single-seed evidence.
- **The cross-sectional architecture's own literature** — already cited in the /088/089 briefs (Poh/Lim/Zohren learning-to-rank arXiv 2012.07149; Jegadeesh-Titman overlapping-portfolio construction; Constantinides/Davis-Norman no-trade-region theory; the Han-Kang-Ryu SSRN 4675565 weekly cross-sectional crypto-momentum horizon that grounds the H=21 ~7-day choice). /092 inherits these; it adds none.

### 10.3 — No-cheating audit

Per `feedback_no_cheating.md` — every design parameter selected on IS data only or a-priori, and /092 is a CONFIRMATION so the discipline is strict:

- **OOS_CUTOFF_DATE / training_months** — IMMUTABLE, untouched.
- **The horizon H=21** — selected on the committed, walk-forward-faithful corrected /091 horizon grid (`H1_horizon_grid.csv` + `M2_lgbmranker_trial_budget.csv`) — both IS-only, both measured on the runner's own walk-forward cadence (`holding_horizon_eda.py::train_rankers_for_horizon` trains on IS months and predicts the next IS month; no OOS row read). OOS never informed the horizon choice.
- **The seed set {42, 123}** — the v3 canonical outer-seed lineage roots (`BASELINE_V3.md` "Unified 10-Seed Ensemble Architecture"); a-priori, not data-selected.
- **The cost-aware construction constants** (quintile 0.20, hold 21, no-trade band 0.020, turnover ceiling 0.138) — RETAINED from /089, all /089-IS-grounded.
- **The 13-feature stack, the universe, the H=21 label, the corrected embargo** — RETAINED from /091, all /088/089/091-IS-grounded.
- **No new EDA** — /092 commits none; the configuration choice rests on already-committed walk-forward-faithful evidence (Section 2.5).
- **The QR sees OOS for the first time in Phase 7.** Every Section-4 gate is a pre-registered evaluation gate, not a tuned parameter. The /091 reference book's OOS +0.4613 is cited in this brief only as a *single-seed-artifact warning* — it is NOT used to inform any /092 parameter, and the brief explicitly pre-registers (Section 1.3, 7) that the multi-seed mean is expected to regress away from it.

### 10.4 — The honest senior read

iter-v3/092 is the cycle-3 CONFIRMATION, and it is an honest one. Cycle 3 produced zero clean PROMISING results, so there is no edge bundle to confirm — and the /091 Critic was explicit that /092 must NOT manufacture one. /092's legitimate, cadence-respecting role is the **rigorous multi-seed close** of v3's most substantial cycle-3 effort: the four-iteration cross-sectional `LGBMRanker` re-architecture (/088-091, all single-seed). The cross-sectional architecture produced v3's first genuine OOS *signal transfer* — that is real knowledge and it is why the line earned a CONFIRMATION-grade close rather than a single-seed abandonment. But across four iterations it never produced a net-positive *book*, the two genuine edge attempts (/090, /091) both failed, and the corrected /091 horizon EDA shows even the best-faith trained-ranker form (H=21, 35-trial) reaches only IS net monthly Sharpe +0.0944 — an order of magnitude below the +1.0 floor. /092 multi-seed-validates that best-faith form at the v3 CONFIRMATION spec, against pre-registered floors, with the honest expectation of CONFIRMATION-NO-MERGE — and the multi-seed run is what converts "four single-seed iterations suggest the line does not work" into a rigorous, lottery-robust verdict. The build is well-scoped: the configuration is already the live runner state (Section 3.4), so the only Phase-6 work is multi-seed support for the cross-sectional runner — specified precisely (Section 3.3) as a QE build item with a mandatory integration test, exactly the discipline the /090 closeout established. /092 is not predicted to find edge. It is predicted to close the cross-sectional `LGBMRanker` line's verdict honestly and rigorously, and hand cycle 4 a clean slate. That is the relentless, honest, top-quant-firm-grade execution the mission demands.

## Section 11 — Reproducibility Stamp

- **EDA SHA**: none — /092 commits NO new EDA (the /091 Critic Recommendation 1 discipline). The configuration choice (H=21) rests on the already-committed, walk-forward-faithful /091 horizon grid: `analysis/iteration_v3-091/holding_horizon_eda.py` (EDA SHA `d4ad137`) — `H1_horizon_grid.csv`, `H2_model_free_horizon_scan.csv`, `H3_horizon_summary.csv`, `M2_lgbmranker_trial_budget.csv`.
- **Brief SHA**: this research brief — committed to `iteration-v3/092`; this Section-11 SHA is backfilled in the immediately-following commit.
- **Setup SHA**: TBD — the /092 setup commit (`ITERATION_LABEL "v3-092"`; `CONFIRMATION_OUTER_SEEDS = (42, 123)`; the `--seeds` count argument; confirm the Section-3.4 live state) — backfilled here after the Phase-6 setup.
- **Phase 5.5 gate SHA**: TBD — the QE independent Phase-5.5 gate on this brief.
- **Reports**: `reports-v3/iteration_v3-092/` (the multi-seed aggregate) + `reports-v3/iteration_v3-092/seed_42/` + `reports-v3/iteration_v3-092/seed_123/` (the per-outer-seed reports).
- **Run mode**: **CONFIRMATION** — multi-seed (`--seeds 2` → outer seeds {42, 123}, `ENSEMBLE_SIZE = 5` per outer seed → 10 models/cell), `n_trials = 35`. Wall-clock estimate: a 10-models/cell cross-sectional run scales ~10× the /090 single-seed cross-sectional run (~20 min) ≈ **~3-4h** — within the 6h v3 CONFIRMATION cap (`feedback_v3_cadence_discipline.md`). (The /091 dual-book run was ~24m for the trained reference book at 1 model/cell; 10 models/cell ≈ ~4h; the model-free book is not run by /092, saving its ~45s.) If the run trends past ~5h, the QE flags it before the 6h cap.
- **The /092 configuration** — the trained `LGBMRanker` (`score_mode="trained"`), H=21, the 13-feature stack, the /089 cost-aware construction, the corrected embargo, the 22-symbol `XS_UNIVERSE` — is bit-identical to the `score_mode="trained"` reference book the /091 runner already produces; the only /092 build delta is the multi-seed support (Section 3.3).
- **Cycle position**: iter-v3/092 is the cycle-3 CONFIRMATION (the /082-091 10-EXPLORATION cadence is complete). Cycle 4 opens at iter-v3/093 as a fresh EXPLORATION (a re-architecture into a new signal class — the /091 closeout Section 9.3 records the candidate directions for the cycle-4 QR; /092 does not pre-commit cycle 4).
