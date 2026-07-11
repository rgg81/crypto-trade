# DIAG-G — ML cross-sectional residual alpha (flagship): FAMILY DEAD — kill (d) fired (economics)

**Track:** MN3 (two-year-holdout market-neutral). **Date:** 2026-07-11. **Role:** QR (scoring).
**IS-only** 2020-01-01→2024-06-30; holdout SEALED — `mn3_guard_grid` passed on the IS-sliced panel,
**zero reveals, REVEAL-LEDGER untouched** (no `- SPENT token=` line exists). **Pure read** of the
frozen, Critic-ratified walk-forward OOF parquet — **nothing retrained, nothing regenerated**
(`PREFLIGHT-DIAG-G.md`: all four rulings RATIFIED, parquet scorable as-is).

> **MODEL NOTE (mandated disclosure).** This scoring was authored + run on **Opus 4.8, NOT Fable** —
> the charter's Fable mandate is user-suspended this phase (Fable rate-limit; user directed "continue
> on Opus"). Standard unchanged; adversarial burden of proof unchanged. The parquet was frozen and
> Critic-ratified BEFORE this scoring harness existed; who typed the command did not touch the frozen
> spec. Same posture as DIAG-H's Opus finalization.

## Verdict (frozen kill criteria, mechanical): **FAMILY G DEAD — kill (d) fired.**
The flagship produces the **strongest, most stable, most crash-robust cross-sectional signal the
MN/MN3 effort has measured** (pooled OOF IC **+0.0369**, positive in all 3 OOF years and all 5 seeds,
CRASH-bucket spread significantly RIGHT-signed t **+3.21**) — and it **dies on economics**: the weekly
top-minus-bottom quintile book churns **156.6×/yr (~3.0 Σ|dw| per rebal, ~1.5× a full flip)** and its
**phase-agnostic 2×-cost net spread is −5.3%/yr**. A real predictor that does not clear the honest cost
wall at weekly cadence. Kills (a)/(b)/(c)/(e) all PASS; **kill (d) alone kills the family.** Honest fail.

---

## 0. Pre-registered header (PLAN §3.1, restated — the frozen spec, executed verbatim)

- **Model:** LightGBM predicting beta-residualized forward returns; **24 pinned features** (immutable
  once DIAG-G runs), position-pinned `MN3_G_FEATURE_COLUMNS`; **8-config grid, ZERO Optuna**
  (num_leaves∈{15,31} × min_data_in_leaf∈{200,500} × lambda_l2∈{1,10}; fixed lr=0.05, n_est=300 no
  early stopping, feature_fraction=0.8, bagging 0.8/freq1, deterministic); **5 seeds {42,123,456,789,
  1001}, prediction = seed-ensemble mean.**
- **Label:** forward 3-candle (24h) residual TOTAL return (price + funding), winsorized ±20%.
- **Walk-forward:** monthly retrain, trailing 24-month window, **3-candle purge** at every train/OOF
  boundary; OOF span **2022-01 → 2024-06 (30 months)**. Parquet: **109,440 rows = 2,736 OOF candles ×
  40 top-40 members**, 40 pred cols + label; 108,700 finite labels (740 NaN = the 3-candle IS tail).
- **Config selection rule (pre-registered):** highest pooled OOF Spearman IC; **tiebreak → fewer
  leaves, then larger min_data_in_leaf** (simpler wins).
- **IC convention (stated for the record):** "pooled OOF Spearman IC" = mean over all OOF candles of
  the **per-candle CROSS-SECTIONAL Spearman** rank-corr(prediction, winsorized label) — the same
  cross-sectional-IC object the DIAG-J/H univariate bars kill (a) compares against. The pooled-ALL-ROWS
  Spearman is reported alongside as a robustness cross-check (it is a different, level-mixing object;
  the verdict uses the per-candle mean).

**Frozen kill criteria (G dies if ANY fire):** (a) best-config pooled OOF IC < 0.02; (b) IC ≤ 0 in ≥2
of {2022, 2023, 2024-H1}; (c) any of the 5 seeds pooled IC ≤ 0 at the selected config; (d) top-minus-
bottom **quintile** net spread at **weekly (rebal 21, 21-phase mean)** fails 2×-cost coverage;
(e) CRASH-bucket quintile-spread mean return **t < −2**.

### Mandatory disclosures carried into this read (PREFLIGHT-DIAG-G.md — verbatim duty)
- **(R1)** `mkt_fund_agg` = the freeze-time **original §2.1 C3 aggregate-|funding|-LEVEL robust-z**, NOT
  the AMENDMENT-001 §B2 onset-FUND transform (frozen-as-failed under AMENDMENT-002). **Locked immutable
  regardless of the IC found** — the level-persistence property that failed as a crisis TRIGGER is not
  a defect in a conditioning FEATURE. (Verified in code: `mn3_features.py:435-441`.)
- **(R3)** `taker_ls_oi_xz`'s numerator (`sum_taker_long_short_vol_ratio`, taker buy/sell vol ratio) and
  denominator (`count_long_short_ratio`, global L/S account-ratio interval count) are **DIFFERENT
  underlying Binance series** — the feature is the bar-mean taker ratio under the same-interval
  assumption; **stub-robust** (the sanctioned §8.2 consumption) but **not a clean single-endpoint
  per-interval mean.** Do not interpret it as one.
- **(AMENDMENT-003 S3-C4)** DIAG-H's S3-C1 control **FAILED** ("vol-structure axis CLOSED FOREVER"), so
  `rvratio_xz` / `rv_ownpctl` **partially reconstruct the now-CLOSED vol-structure axis inside G** —
  **informational, NOT a G kill**; flagged if either shows high feature importance (§4 below: both LOW).

**Multiple-testing ledger (family G):** opened at **8** (the HP grid; one feature list, one label,
provenance disclosed). Config selection by pooled-IC on OOF is the **registered** selection rule and
spends **no extra trial**. **Ledger closes at 8; no amendment used.** The cap-16 one-revision round is a
"diagnosable-defect" clause — kill (d) is a genuine economic result (real signal, cost-wall), not a
fixable defect, so **the revision round is NOT invoked** (searching slower cadences post-hoc would be
cadence-selection-by-outcome — banned; PLAN §3.1:404-405). A fired kill is final.

---

## 1. Per-config IC table (8 configs × pooled IC + per-seed + per-year) — kill (a)/(b)/(c)

Pooled IC = mean per-candle cross-sectional Spearman(seed-ensemble-mean pred, winsorized label) over
all OOF candles. `rows_IC` = the pooled-ALL-rows cross-check (near-zero by construction — it mixes
across-candle level variation and is NOT the IC object; see note). `seed_min` = min of the 5 per-seed
pooled ICs at that config.

| ci | leaves | min_leaf | l2 | **pooled IC** | rows_IC | 2022 | 2023 | 2024-H1 | seed_min |
|---|---|---|---|---|---|---|---|---|---|
| c0 | 15 | 200 | 1 | +0.0356 | +0.0002 | +0.0347 | +0.0421 | +0.0244 | +0.0317 |
| **c1** | **15** | **200** | **10** | **+0.0369** | +0.0004 | +0.0372 | +0.0433 | +0.0232 | +0.0324 |
| c2 | 15 | 500 | 1 | +0.0364 | +0.0020 | +0.0370 | +0.0420 | +0.0240 | +0.0308 |
| c3 | 15 | 500 | 10 | +0.0349 | +0.0039 | +0.0369 | +0.0391 | +0.0223 | +0.0308 |
| c4 | 31 | 200 | 1 | +0.0314 | +0.0007 | +0.0286 | +0.0366 | +0.0266 | +0.0266 |
| c5 | 31 | 200 | 10 | +0.0318 | +0.0019 | +0.0270 | +0.0382 | +0.0285 | +0.0233 |
| c6 | 31 | 500 | 1 | +0.0339 | +0.0052 | +0.0291 | +0.0399 | +0.0312 | +0.0284 |
| c7 | 31 | 500 | 10 | +0.0348 | +0.0059 | +0.0323 | +0.0393 | +0.0309 | +0.0294 |

**Selected config = c1** (num_leaves=15, min_data_in_leaf=200, lambda_l2=10), pooled IC **+0.0369** — the
max; no tie. Its 5 per-seed pooled ICs: **42:+0.0337, 123:+0.0344, 456:+0.0324, 789:+0.0327,
1001:+0.0342.** All 8 configs land in a **tight +0.031…+0.037 band** — the read is HP-insensitive; the
15-leaf configs edge the 31-leaf ones (simpler generalizes marginally better, as the tiebreak
anticipates).

- **Kill (a) — NOT fired.** Best-config pooled IC **+0.0369 ≥ 0.02** (1.85× the bar). The ML combiner
  **decisively beats** the univariate IC bars of its own inputs: DIAG-J's strongest funding cross-
  sectional IC was |0.018| raw / ≈0 level-controlled; the flagship reaches +0.037 pooled, stable.
- **Kill (b) — NOT fired.** Per-year IC 2022 **+0.0372**, 2023 **+0.0433**, 2024-H1 **+0.0232** — all
  positive, **0/3 non-positive**. No calendar-year instability.
- **Kill (c) — NOT fired.** All 5 seeds at c1 positive (+0.0324…+0.0344), **0/5 non-positive**. No seed
  instability.

> **Note on `rows_IC` ≈ 0.** The pooled-ALL-rows Spearman is near zero at every config — expected and
> not a red flag: pooling 108,700 rows across 2,736 candles mixes each candle's cross-section into one
> distribution, so cross-candle label-level variation swamps the within-candle rank signal. The
> cross-sectional per-candle IC (+0.037) is the correct, tradeable object and the one kill (a) names.

---

## 2. Selected-config economics (kill (d)) — the killing blow

Held-weights **quintile** L/S book (GT twin, not analytic): sort by the c1 seed-ensemble prediction,
**long TOP quintile / short BOTTOM** (direction **+1, a-priori** — the model directly forecasts the
label; unlike DIAG-J there is no sign DOF), **k = n//5 = 8 names/leg** at n=40, weekly **rebal 21** with
full **21-phase tranche sweep**, costs **7.5 bps/side on Σ|dw| + funding inside the return stream**,
**2×-cost twin = gross − 2·cost.** Per-candle residual TOTAL returns recomputed from the IS panel
(`residual_returns` + `load_funding`, IS-guarded — market-data recomputation, not model retrain).

| cadence | gross/yr | net 1×/yr | **NET2× /yr (headline)** | turnover/yr | 21-phase net2× positive |
|---|---|---|---|---|---|
| **rebal 21 (21 phases)** | **+18.2%** | **+6.5%** | **−5.3%** | **156.6×** | **9/21** |

- **21-phase NET2× distribution:** min −76.1%, **median −6.2%**, max +77.4%; positive **9/21**.
  Full: `+39 +77 +40 −6 +20 +3 −38 −39 −76 −8 −27 −56 −41 −9 −13 +2 −62 −6 +35 +17 +36` (%). The ±77/−76
  spread is exactly the phase-lottery the track's phase-sweep rule exists to neutralize — the
  phase-agnostic mean −5.3% is the honest headline, not any single lucky phase.
- **Turnover / cost coverage:** 156.6×/yr over ~52 weekly rebals ⇒ **~3.0 Σ|dw| per rebal** (a full
  quintile flip is 2.0 — the book **more than fully re-forms each week**: the 24h-label ranking is
  noisy week-to-week). Gross **+18.2%** vs a **2×-cost drag of 23.5%** (156.6 × 15 bps) ⇒ **FAILS
  coverage.** Even the 1×-cost net is only +6.5%/yr (a thin, low-Sharpe read); the honest 2× twin is
  **−5.3%**.
- **Kill (d) — FIRED.** Phase-agnostic weekly quintile net2× **−5.3% ≤ 0.**

**Mechanism of the failure:** the signal is real (IC +0.037) but **fast-decaying / high-churn** — a
tree combiner over 24 features at a 24h horizon produces a ranking that turns over ~75% weekly, and at
8h-scale honest costs (7.5 bps/side) that turnover eats a +18% gross down to a negative 2×-cost spread.
This is precisely the failure kill (d) is designed to catch: a model that **predicts** but does not
**trade**. (For scale: DIAG-H's S4/Amihud survivor grossed net2× +17%/yr at **74×** turnover — half of
G's; G's edge-per-turnover is far thinner.)

### Regime buckets (kill (e) instrument — fresh per-candle quintile-spread of the fwd-3c label)
Top-minus-bottom quintile **mean-label spread** per candle, sorted by the c1 prediction, bucketed at
the decision candle (frozen `mn3_regimes` rules). Plain t; fwd-3c overlap ⇒ conservative t/√3 in ( ).

| bucket | mean quintile-spread (fwd-3c label) | t (t/√3) | n candles |
|---|---|---|---|
| **CRASH** | **+0.00491** | **+3.21 (+1.86)** | 354 |
| MANIA | +0.00078 | +0.39 (+0.23) | 293 |
| CHOP | +0.00212 | +3.79 (+2.19) | 2,086 |

- **Kill (e) — NOT fired.** Kill bar is CRASH t < −2 (significantly WRONG-signed). Observed CRASH
  spread is **+0.00491, t +3.21** — **significantly RIGHT-signed.** The flagship's directional call is
  **correct and strongest in CRASH** (mania is where it's weakest, +0.00078, n.s.). **The all-weather
  directional property the doctrine demands HOLDS** — G is not a fair-weather predictor; it is a
  crash-robust one that simply cannot pay its weekly transaction bill. (Echoes DIAG-H's finding that
  the crash-positive axis is real; here it is real gross and dead net.)

---

## 3. Leak-structure confirmation (proportionate; all PASS)

- **t_idx ↔ open_time alignment PASS** — `panel.grid_ms[t_idx] == parquet.open_time` for all 109,440
  rows: the IS-sliced panel my book/features run on is the identical grid the generator used.
- **Walk-forward month coverage PASS** over 30 months — each OOF candle belongs to exactly one month;
  per-month candle count == manifest `n_oof/40`; months contiguous, non-overlapping.
- **Purge PASS** — each month's first-OOF-candle index == manifest `b_idx`, and the last permitted
  training candle (`b_idx − 3 − 1`) has its forward-3c label ending at `b_idx − 1` **< b_idx** (the OOF
  start): the 3-candle purge is intact at every boundary; no train label overlaps any OOF candle.
- **Book decision-lag correct by construction** — the book consumes sig at close[t], first return
  candle t+1; the fwd-3c label window t+1..t+3 never includes candle t (asserted by
  `test_quintile_book_sim_decision_lag`, and the DIAG-J/H `forward_total_residual` window is
  unit-pinned).
- **Feature-rebuild integrity PASS** — the deterministically rebuilt 24-feature matrix's label column
  equals the parquet label row-for-row across all 109,440 OOF rows (faithful rebuild; no drift).

---

## 4. Feature-importance read (model-free proxy — no retrain available) + S3-C4 flag

The generator persisted predictions only (no boosters), and retraining is forbidden this phase, so
LightGBM **gain** importance is unavailable. Instead, from the deterministically-rebuilt frozen feature
matrix (NOT a retrain), over the OOF span: **`pred_track`** = mean per-candle cross-sectional
Spearman(feature, c1 ensemble prediction) — how strongly the model's OUTPUT ranks with the feature (a
monotone-loading proxy); **`uni_ic`** = the feature's standalone cross-sectional IC vs the label.
**Caveat disclosed:** this proxy captures monotone loading, **not** interaction/split (gain) importance
— a feature used mainly in interactions can rank low here.

**Top-10 by |pred_track| (model-loading proxy):**

| rank | feature | pred_track | uni_ic |
|---|---|---|---|
| 1 | ti21_xz | +0.156 | +0.0148 |
| 2 | ti9_xz | +0.142 | +0.0068 |
| 3 | oi_chg90_xz | −0.131 | −0.0626 |
| 4 | **range9_xz** | **−0.129** | **−0.1240** |
| 5 | fund_lvl_xz | −0.125 | −0.0069 |
| 6 | fund_lvl_ownpctl | −0.115 | +0.0064 |
| 7 | ti3_xz | +0.110 | +0.0056 |
| 8 | oi_per_dvol_xz | +0.107 | +0.0812 |
| 9 | fund_mom63_xz | −0.103 | +0.0020 |
| 10 | resmom189_xz | −0.087 | −0.0516 |

The model loads primarily on **taker-imbalance** (ti21/ti9/ti3), **OI dynamics** (oi_chg90,
oi_per_dvol), and **funding level** (fund_lvl_xz / fund_lvl_ownpctl) — the crowding-syndrome trio the
§3.1 mechanism named. `taker_ls_oi_xz` (the R3-disclosed cross-series feature) is NOT in the top-10.

### S3-C4 flag (mandatory)
- **`rvratio_xz`:** rank **19/24** by |pred_track| (=−0.022, uni_ic −0.0323) → **NOT high-importance.**
- **`rv_ownpctl`:** rank **20/24** by |pred_track| (=−0.013, uni_ic −0.0531) → **NOT high-importance.**

**S3-C4 flag = NEGATIVE.** The two features named as partial reconstructions of the CLOSED vol-structure
axis are **near the bottom** of the model's loading — G's IC does **not** rest on resurrecting vol_low
via `rvratio_xz`/`rv_ownpctl`. Disclosure duty discharged.

> **Honest adjacent note (recorded, not an S3-C4 trigger — G is dead regardless).** The **third**
> vol-structure-block feature, **`range9_xz`** ((high−low)/close 9c mean — an intraday-RANGE measure,
> NOT one of the two S3-C4-named RV features and NOT the PLAN's deliberately-excluded RV-LEVEL feature),
> is the model's **strongest single univariate feature** (uni_ic **−0.1240**, the largest |IC| of all 24)
> and rank-4 by loading. Its sign (fade high-range / recently-volatile names) **rhymes with the closed
> vol_low direction.** Two honest reads: (1) some of G's gross edge is a range/vol-structure effect
> adjacent to the closed family — worth a Critic's eye had G survived; (2) notably, `range9_xz` alone
> (|IC| 0.124) is a **stronger** univariate predictor than the full 24-feature model (0.037) — the
> regularized tree blend (min_data 200, feature_fraction 0.8, lambda_l2 10) **dilutes** its dominant
> feature. Since kill (d) kills G on economics, this is recorded color, not an action. Not retrained to
> investigate (forbidden); the pred-track proxy is the ceiling of what a pure read supports.

---

## 5. VERDICT — **FAMILY G DEAD** (kill (d) fired; a/b/c/e all pass)

| kill | criterion | result |
|---|---|---|
| (a) | best-config pooled IC +0.0369 < 0.02 | **ok** (1.85× the bar) |
| (b) | IC ≤ 0 in ≥2 OOF years (0/3) | **ok** |
| (c) | any seed IC ≤ 0 at c1 (0/5) | **ok** |
| **(d)** | **weekly quintile net2× −5.3% ≤ 0** | **FIRED** |
| (e) | CRASH quintile-spread t +3.21 < −2 | **ok** (significantly RIGHT-signed) |

**The flagship dies on economics, not on signal.** Its cross-sectional IC (+0.037) is the strongest,
most stable, most crash-robust the MN/MN3 effort has produced — but the weekly top/bottom-quintile book
churns ~3.0 Σ|dw| per rebal and cannot clear the honest 2×-cost wall (net2× −5.3%). Per the frozen
discipline, a fired kill is final and no revision round is invoked (kill (d) is a real economic result,
not a fixable defect; a post-hoc cadence/turnover search would be banned mining).

**G does NOT bank as a second family candidate** (the capstone-ensemble path needs banked survivors;
DIAG-H's S4/Amihud remains the sole standalone survivor of the field so far). **G's holdout token is
NOT spent and remains available** — but under these frozen kill criteria there is no G construction to
reveal.

### Recorded finding (surfaced, NOT acted on — an orchestrator/USER decision, per the DIAG-H S4 precedent)
The honest asymmetry is: **real, stable, crash-robust cross-sectional signal that fails only on
turnover/cost at weekly quintile-extreme construction.** A *different* construction — **turnover-
suppressed** (continuous IC-proportional weights instead of quintile-extreme; a slower cadence; a
no-trade band; or a signal-EMA to damp week-to-week ranking churn) — *might* clear costs. But any such
book is a **NEW pre-registered construction** that would consume **family G's one-forever holdout
token** (PLAN §6.1 anti-gaming), **not a G rescue** and **not a mechanical continuation.** It requires
its own EXPLORATION brief, Critic pre-flight, and frozen decision map. This is flagged for the
orchestrator/user; it is not spent here. Nothing about the closed vol-structure axis is revived; the
R1 `mkt_fund_agg` level-z definition remains locked-immutable as ratified.

---

## 6. Artifacts

- **Scoring harness:** `analysis/portfolio/mn3_diag_g_score.py` (gitignored analysis tree; guard-first;
  pure parquet read + IS-only market-data recompute for the book/features; verdict mechanical —
  `main()` prints `FAMILY G: DEAD/ALIVE`). Reproduce: `uv run python analysis/portfolio/mn3_diag_g_score.py`.
- **Tests:** `tests/test_mn3_diag_g_score.py` — 7 synthetic unit tests (per-candle IC perfect/inverse +
  min-members/NaN-pred handling; quintile-spread; quintile book weights/cost/direction-mirror;
  book decision-lag; config tiebreak; t-stat). **mn3 subset 120/120 green; ruff clean on both touched
  files.**
- **Frozen inputs (unchanged, unread-for-metrics-beyond-this):** `data/mn3_g/oof_predictions.parquet`
  (git SHA 5c939a60, generated 2026-07-11T13:32Z), `data/mn3_g/oof_manifest.json`.
- **Run log:** deterministic single pass; verdict banner `FAMILY G: DEAD (kill d fired)`.
- **Token ledger:** `REVEAL-LEDGER.md` untouched — zero `- SPENT token=` lines. Holdout never touched;
  no G token spent.
- **Not committed to git** (per instruction).

**Track state:** DIAG-G complete (PLAN §4 order-4). Field so far: DIAG-J DEAD (fold into I), DIAG-H DEAD
as ensemble (S4/Amihud standalone survivor), **DIAG-G DEAD on economics**. Family ledgers: **G:8
(closed, dead)**, H:4, I:11, ~~J:6~~ (closed, dead), K:1. Remaining per the frozen order: DIAG-I
(order-5, structurally-weak Stage-2 regardless), DIAG-K (order-6, double-gated).

*— QR, MN3 track, 2026-07-11 (Opus 4.8, Fable-suspended phase). Pre-registered, scored mechanically,
killed by its own frozen bar. An honest fail: the flagship can forecast (IC +0.037, all-weather,
crash-robust) but its weekly quintile book cannot pay the toll (net2× −5.3%). The signal is real; the
trade is not. The holdout remains sealed.*
