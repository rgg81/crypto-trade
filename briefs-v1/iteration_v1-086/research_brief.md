# iter-v1/086 — Research Brief (Phase 1–5 QR)

**Date**: 2026-06-10
**Track**: v1 (refactored)
**Branch**: `iteration-v1/086`
**TYPE**: SPECIALIST — single-coin cohort `("TRBUSDT",)` (Tellor); **bundle-diversification mine on the STOCK 48-col feature stack — NO new features**.
**Cycle**: 7, structure-gated fresh-alt mining (the **6th mine**, and the FIRST to clear the GATE-2 PRIMARY probe).
**Author**: QR (autopilot)
**Anchor**: BUNDLE-002 (`v0.v1-082`; DOT+ETH+BTC+AAVE; IS +0.7157 / OOS +1.0043).
**Methodology**: LOCKED (per-symbol regime-specialist mandate; multi-seed CONFIRMATION PERMANENTLY DROPPED).

---

## Section 0 — Context / Hypothesis

The v1 fresh-alt mining campaign sits at **0/5** (ATOM, ICP, FIL/083, CRV/084, UNI/085 all SPECIALIST-NEGATIVE). The /084 + /085 closeouts converted the soft selection heuristic into a **HARD reject ladder**:

- **GATE 0 — bundle-diversification (NEW this iteration)**: the live bundle is now 4 seats `{DOT, ETH, BTC, AAVE}`; the next seat must *diversify the PnL stream*, not duplicate it. Per user directive 2026-06-10 — *"next, pick a symbol with less correlation with the symbols we have chosen for the bundle."*
- **GATE 1 — negative trivial-momentum baseline** (`feedback_v1_negative_trivial_baseline_selector`): a *positive* trivial baseline means trend already captures the move and the ML head has no headroom (the FIL/083 trap). PASS iff min-horizon trivial Sharpe ≤ +0.15.
- **GATE 2 PRIMARY — learnable-structure probe, now a HARD REJECT** (`feedback_v1_negative_trivial_baseline_selector`, reaffirmed at /085): a single-seed=42, n_trials=10, 48-col stock-stack, real ATR-barrier-label, IS-only walk-forward LightGBM probe must clear **IS Sharpe ≥ +0.30** *before* a specialist brief is authored. CRV/084 (probe would have been negative) and UNI/085 (probe −0.243, then a 6.6h crater) are the two precedents that earned this gate its teeth.

**TRBUSDT is the first fresh-mine candidate to clear all three gates.** Critically, /084's Critic Path Forward authorized exactly this move: *"STRUCTURE-GATED 6th mine ONLY IF (1) and (2) are exhausted … the next fresh alt MUST clear GATE 2 (probe IS Sharpe ≥ +0.30) at the cheap probe stage BEFORE a full specialist brief."* TRB clears it at **+0.4930** — 64% above the bar.

**The /085 failure mode we are explicitly avoiding**: UNI/085 cratered because it FAILED the probe and the brief then bet that 4 NEW reversal features would manufacture a pass — they ranked 42/52 and 39/52 (inert) and *worsened* IS by Δ−0.46 below the probe (the inert-features-amplify-noise-at-higher-budget mechanism). **TRB does the opposite**: the edge is already present in the stock 48-col `V1_FEATURE_COLUMNS_PRUNED`, so we **add ZERO features**. This is the cleanest possible cohort-mine — pure SYMBOL-dimension isolation, no feature-engineering surface for the noise-amplification trap to attach to.

**One-line hypothesis** (see Section 1): *A TRBUSDT single-coin LightGBM specialist on the STOCK 48-col stack — selected as the lowest-correlation eligible seat vs the live 4-coin bundle — produces a positive IS edge (probe-consistent, ≥ +0.30) AND, by virtue of its low return-correlation with the bundle, is a bundle-accretive diversifier even at a moderate standalone Sharpe.*

---

## Section 0.5 — Iteration Type + Verdict Frame

- **Iteration type**: SPECIALIST (single-coin cohort, single-axis = SYMBOL dimension). NOT a BUNDLE/CONFIRMATION (no baseline update possible).
- **Budget**: SPECIALIST — 50 inner seeds (42..91) × 30 Optuna trials, ENSEMBLE_SIZE=1, single outer seed=42, `specialist_mode`, ~6h wall-clock (within the 9h BUNDLE cap; above the 2h EXPLORATION-knob cap because this is a per-cohort SPECIALIST under the regime-specialist mandate, mirroring the AAVE/078 + UNI/085 50-inner-seed methodology-lock spec).
- **Verdict frame** (Phase 7.5 Critic): `SPECIALIST-VALIDATED` (roster-eligible, bundle candidate) / `SPECIALIST-PROMISING` (roster-eligible, TENTATIVE) / `SPECIALIST-NEGATIVE` (dropped). No MERGE this iteration regardless of outcome — a positive verdict makes TRB a **BUNDLE-003 candidate seat**, evaluated at a future BUNDLE assembly.
- **Multi-seed CONFIRMATION**: PERMANENTLY DROPPED (user directive). The 50-inner-seed ensemble is the variance control (see Section 2.5). NOT proposed.

---

## Section 0.6 — Architecture-Family Justification (v1-only)

- **Axis family**: `per-cohort-specialization-TRB` (NEW symbol cohort; STOCK feature stack; NO feature-family change; NO new risk primitive; NO labeling change).
- **Prior 5 SPECIALIST cohorts** (from `briefs-v1/specialist_catalog.md` + diaries):
  - iter-v1/065: `per-cohort-specialization-BTC`
  - iter-v1/078: `per-cohort-specialization-AAVE`
  - iter-v1/083: `per-cohort-specialization-FIL`
  - iter-v1/084: `per-cohort-specialization-CRV`
  - iter-v1/085: `per-cohort-specialization-UNI`
- **Rotation status**: **VALID.** Under the per-symbol regime-specialist mandate (`feedback_v1_cycle6_per_symbol_regime_specialist_mandate`), axis-family rotation is SUSPENDED for cycle-6/7 — single-symbol cohort discoveries are the modal axis. Independent of the suspension, the cohort `per-cohort-specialization-TRB` is distinct from all 5 prior cohorts (TRB ∉ {BTC, AAVE, FIL, CRV, UNI}). TRB ∉ BUNDLE-002 (`{DOT, ETH, BTC, AAVE}`), ∉ the failed-mine set (`{LINK, LTC, ATOM, ICP, FIL, CRV, UNI}`), ∉ `V1_EXCLUDED_SYMBOLS` (`{XRP, DOGE, NEAR, BCH, LDO, TRX, BNB}` — verified: TRB is Tellor, distinct from TRX/Tron).
- **One-sentence rationale**: TRB is the lowest-bundle-correlation eligible symbol AND the first fresh-mine candidate to clear the GATE-2 structure probe on the stock stack, so it is the single best next seat to test whether a structure-present, low-correlation alt can be bundle-accretive — the conjunction that 5 prior fresh mines never reached.

---

## Section 1 — Hypothesis

**H1 (primary)**: A TRBUSDT single-coin LightGBM specialist trained on the STOCK 48-col `V1_FEATURE_COLUMNS_PRUNED` set (R1 OFF, R2 OFF, R3 ON-shared 0.70, R5 vol-targeting ON, ATR TP 2.9 / SL 1.45) produces a realized 50-inner-seed **IS monthly Sharpe ≥ +0.30**, consistent with the single-seed=42 GATE-2 probe (+0.4930), confirming that TRB carries learnable momentum/trend structure the locked architecture can extract.

**H2 (diversification, the load-bearing bundle thesis)**: TRB's return stream has the LOWEST pairwise correlation with the live bundle of any eligible candidate (avg 0.548, evenly spread, no single-member spike). A low-correlation seat lifts *bundle* Sharpe through PnL-stream decorrelation even at a moderate standalone Sharpe — so the candidacy bar for TRB is set by its diversification value, not by a high standalone number.

**What would falsify** (formal bands in Section 4): a realized 50-seed IS Sharpe that collapses below +0.00 falsifies H1 (the single-seed probe was a lucky basin); a realized IS Sharpe below the trivial min-horizon −0.179 falsifies the "ML beats trivial momentum" premise.

**Why momentum/trend, not reversion** (the diametric opposite of UNI's failed bet): GATE-2 SECONDARY top-IC features (Section 2) are `mom_macd_line_12_26_9` (max |IC| 0.3863), `trend_adx_14`, `vol_atr_14`, `interact_rsi_x_adx`, `interact_natr_x_adx` — a momentum/trend-flavored structure fingerprint. UNI/085 bet on a lag-3 *reversion* kernel that died inside the ATR stop distance; TRB's structure is the family the locked ATR-barrier label is built to capture, and it is already encoded in the stock stack.

---

## Section 2 — IS-Only EDA Evidence (GATE 0 / 1 / 2)

All scripts and CSVs are committed under `analysis/iteration_v1-086/`; every series is truncated to `open_time < OOS_CUTOFF (2025-03-24)` — **OOS is never read for selection** (per `feedback_no_cheating`, verified in-code, not in prose). Data extent: **4.55 IS years** (2020-09 → 2025-03-23), last kline 2026-06-09, **48/48 PRUNED columns present** in the parquet.

### GATE 0 — Bundle-diversification correlation screen
Source: `analysis/iteration_v1-086/bundle_diversification_corr.{py,csv}`. 8h log-return correlations, IS-only, vs the live bundle basket `{DOT, ETH, BTC, AAVE}`.

| Symbol | avg pairwise corr vs bundle | corr vs EW-bundle | max single-member corr (member) | corr_BTC | corr_DOT | corr_ETH | corr_AAVE |
|---|---:|---:|---|---:|---:|---:|---:|
| **TRBUSDT** | **0.5481** (LOWEST eligible) | 0.6135 | 0.5655 (ETH) | 0.5261 | 0.5648 | 0.5655 | 0.5358 |
| STORJUSDT | 0.5505 | 0.6168 | 0.5670 (DOT) | … | … | … | … |
| SFPUSDT | 0.5611 | 0.6190 | 0.5883 (DOT) | … | … | … | … |
| …(52 more, all higher) | … | … | … | … | … | … | … |

**TRB is the lowest-average-correlation eligible candidate in the entire screened universe** (56 symbols). The correlation is **evenly spread** — max single-member coupling is 0.5655 (ETH), only 0.039 above the average, so there is no hidden tight-coupling-to-one-member artifact (the screen explicitly flags candidates that are low-on-average but tightly coupled to one member; TRB is not one). This is the H2 diversification rationale: a 0.55-correlated PnL stream decorrelates the bundle.

### GATE 1 — Trivial TS-momentum baseline (IS-only, multi-horizon, fee-adjusted)
Source: same CSV (`triv_s5/s21/s50`, `trivial_baseline_min_horizon`). `sign(close.pct_change(n)).shift(1) * bar_ret`, fee 0.05%/side turnover-aware, annualized √(3·365), horizons {5d=15bar, 21d=63bar, 50d=150bar}.

| Horizon | TRB trivial Sharpe |
|---|---:|
| 5d (15 bar) | −0.179 |
| 21d (63 bar) | −0.116 |
| 50d (150 bar) | +0.418 |
| **min-horizon (selector)** | **−0.179** |

**GATE 1 PASS**: min-horizon −0.179 ≤ +0.15. TRB does not trend trivially at the short horizon → there is residual edge headroom for the ML head (the DOT/063 + AAVE/078 winning profile, NOT the FIL/083 +1.45 positive-baseline trap). Note the 50d horizon is mildly positive (+0.418) — a longer-cadence trend exists, but the short-horizon residual is the headroom signal the gate targets.

### GATE 2 PRIMARY — learnable-structure probe (HARD REJECT gate)
Source: `analysis/iteration_v1-086/probe_TRBUSDT.{py,csv}`. Single-seed=42, n_trials=10, max_depth=5 FIXED, num_leaves=31 FIXED, 48-col stock stack, real ATR-barrier label (TP 2.9× / SL 1.45×), R1/R2 OFF, R5 vol-targeting ON, OOD OFF (probe speed), IS-only walk-forward (24-mo train / 1-mo test).

| Probe metric | Value | Gate | Verdict |
|---|---:|---|---|
| **IS monthly Sharpe** | **+0.4930** | ≥ +0.30 | **PASS** (64% above bar) |
| IS trades | 180 | — | strong count (well above the 50-IS floor) |

**GATE 2 PRIMARY PASS.** This is the first fresh-mine candidate to clear the probe under the locked stack. The probe is the load-bearing gate: at +0.4930 it sits between the AAVE/078 (rescued, +0.34) and DOT/063 (+1.32) profiles — i.e., a structure-present coin, not a CRV-style pure-noise (case b) or FIL-style trivially-trending (positive-baseline) reject.

### GATE 2 SECONDARY — max feature-vs-label |IC| (direct, walk-forward-averaged)
Source: same probe script (`gate2_secondary_max_ic`). Direct feature-vs-label Spearman IC (the replacement for the family-redundancy `ic_matrix.csv` the /084 closeout flagged as the hole that let CRV through).

| Top feature (by mean |IC| across folds) | mean |IC| |
|---|---:|
| **mom_macd_line_12_26_9** | **0.3863** (max) |
| trend_adx_14 | (high) |
| vol_atr_14 | (high) |
| interact_rsi_x_adx | (high) |
| interact_natr_x_adx | (high) |

**GATE 2 SECONDARY PASS**: max |IC| 0.3863 ≥ 0.04 (well clear). The top-IC features are **momentum/trend-flavored** — the structure family the ATR-barrier directional label is built to capture, and the diametric opposite of UNI's failed reversion bet. This is the structural reason the stock 48-col stack already carries the edge and NO new features are warranted.

### EDA synthesis
TRB clears the full HARD ladder: lowest bundle-correlation (GATE 0) + negative short-horizon trivial baseline (GATE 1) + structure-probe pass (GATE 2 PRIMARY +0.4930) + strong momentum/trend feature-IC (GATE 2 SECONDARY 0.3863). The edge is in the stock stack; the experiment is whether the 50-seed specialist reproduces the probe and the low correlation holds OOS as a bundle diversifier.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

- **Declaration**: **HIGH-RISK.**
- **Reason**: this axis changes Optuna's training-objective domain — it substitutes a NEW symbol's data (TRBUSDT) into the per-cohort head. New-symbol substitution is a HIGH-RISK axis per the v1 plan (universe/cohort substitution alters the training distribution).
- **Mitigation**: **50-inner-seed ensemble (seeds 42..91)** is the variance control — not multi-outer-seed CONFIRMATION (PERMANENTLY DROPPED per user directive). The 50-inner-seed spec mirrors the AAVE/078 + UNI/085 methodology-lock. The `cross_seed_sharpe_std` reported in `comparison.csv` is the basin-lottery adjudicator: UNI/085 converged to `cross_seed_sharpe_std = 0.000` (its negative was structurally robust, NOT a lottery artifact), so the same metric will tell us whether TRB's +0.4930 single-seed probe is a stable basin or a lucky draw. Per `feedback_v1_basin_lottery_vigilance`, a per-seed spread > 0.50 triggers a verdict downgrade — but at 50 inner seeds the ensemble itself collapses single-seed variance, so this is the appropriate variance control for the single-outer-seed SPECIALIST budget.
- **HIGH-RISK single-seed-streak tracking**: this is a single-outer-seed HIGH-RISK iteration. Per the v1 plan, if 3+ HIGH-RISK single-(outer-)seed SPECIALISTs produce >1σ negative deltas in a row, the next becomes mandatorily multi-seed. The recent fresh-mine streak (FIL/083, CRV/084, UNI/085) was negative — TRB is the FIRST to clear the structure probe, so its prior is materially different; the streak counter context is noted for the Phase 8 diary.

---

## Section 3 — Implementation (for QE)

**This brief is authored by the QR; the QE owns all `src/` changes. No production code is written by the QR.**

### 3.1 Cohort + universe
- `V1_ITER086_UNIVERSE = ("TRBUSDT",)` — single-coin cohort dispatch. Runner asserts `set(cfg.symbols) == set(V1_ITER086_UNIVERSE)`; all other dispatch branches dropped.
- Universe-disjointness assertion: `set(cfg.symbols).isdisjoint(V1_EXCLUDED_SYMBOLS)` (TRB ∉ excluded — verified).
- Specialist head: **Model_A_TRB_specialist** pattern.

### 3.2 Feature stack — STOCK 48 cols, NO new features
- `feature_columns = list(V1_FEATURE_COLUMNS_PRUNED)` — **48 cols, STOCK.**
- **Global `V1_FEATURE_COLUMNS_PRUNED` stays at 48.** NO `V1_ITER086_*` local feature additions. NO new feature engineering. This is the load-bearing one-variable discipline of this iteration (the explicit avoidance of the /085 inert-feature failure mode). Critic Check 8 (hypothesis-implementation alignment) verifies the diff adds zero feature columns.
- Feature-column pinning MANDATORY: pass the explicit 48-col list (never None/empty/auto-discovered).

### 3.3 Risk wrapper (NO new primitive)
- **R1 OFF** (`risk_consecutive_sl_limit=0`) — Model A pattern.
- **R2 OFF** (`risk_drawdown_scale_enabled=False`) — Model A pattern.
- **R3 ON, shared 0.70 cutoff** (OOD Mahalanobis, 16 scale-invariant features) — same as all 4 incumbent seats.
- **R5 vol-targeting ON** (`vol_targeting=True`, target 0.3, 45-day lookback, min_scale 0.33, max_scale 2.0) — same as incumbents.
- NO new risk primitive. (Note the /085 R5 cold-start amplifier observation — see Section 6 — applies to any fresh-listed alt; TRB's 4.55 IS years means a long vol history, but the early-IS cold-start window is still flagged for the diary.)

### 3.4 Label + barriers (UNCHANGED)
- Real ATR-barrier triple-barrier label: `atr_tp=2.9`, `atr_sl=1.45`, timeout 21 bars (10080 min), past-only ATR (no labeling-window leak). `training_months=24` FIXED. Walk-forward `train_end_ms = test_start_ms - embargo_ms` (the iter-v3/058 fix at `walk_forward.py:113` — must NOT regress).

### 3.5 Ensemble + Optuna (SPECIALIST budget)
- **50 inner seeds (42..91)**, **30 Optuna trials** per (symbol, month) cell, **ENSEMBLE_SIZE=1**, **single outer seed=42**, `specialist_mode`, mean-of-signed-weights aggregator. `max_depth=5` FIXED, `num_leaves=31` FIXED. ~6h wall-clock (split-engineer dispatch per `feedback_split_engineer_dispatch` since > 30 min).

### 3.6 Reports
- `reports-v1/iteration_v1-086/{in_sample,out_of_sample}/` + `comparison.csv` with `cross_seed_sharpe_std`, per-symbol attribution, DSR/PSR (informational at SPECIALIST budget). Phase 8 HARD rule: `git add reports-v1/iteration_v1-086/` before the diary commit.

---

## Section 3.5 — LM Master Phase 4.5 Integration

The LightGBM Master Phase 4.5 advisory (`briefs-v1/iteration_v1-086/lgbm_advisor.md`) was authored after this brief; the QR responses to each recommendation are below.

| LM rec | QR disposition | Rationale |
|---|---|---|
| **Rec 1 — HP landing predictions** (lr ~0.018, reg_alpha 0.8–2.0, colsample 0.65–0.75, training_days 240–320 modal ~300; SHORT <120d landing = red flag) | **NOTED (no action — within-lock prediction)** | These are predicted landings, not bound changes; the `v1_pruned` Optuna search is unchanged. Phase 7.4 will check the realized `training_days` distribution against the predicted MEDIUM-LONG window; a SHORT (<120d) landing is pre-registered as a short-horizon-noise red flag. |
| **Rec 2 — 50-seed mean IS ≈ +0.48 [+0.38,+0.62]; cross_seed_std predicted [0.05,0.20]** | **ADOPTED as the modal anchor** | Tightens Section 7's modal to ~+0.48. The pre-registered basin-lottery falsifier (cross_seed_std > 0.40 with positive single-seed but mean < +0.20) is folded into F2. |
| **Rec 3 — feature-importance prediction (vol_atr_14 r1-2; mom_macd_line ≤5 DISCRIMINATING; trend_adx_14 r3-7; oi_delta_30_z90 r2-4)** | **ADOPTED as a Phase 7.4 pre-registered check + NEW F5 below** | The discriminating prediction (MACD/ADX must bind ABOVE the shared vol_atr_14/oi_delta anchors) is load-bearing for the diversification thesis and is hereby promoted to a formal falsifier (F5). |
| **Rec 4 — R5 cold-start telemetry (isolate 2020-09→2020-10-15 first-45-day IS PnL)** | **ADOPTED as Phase 7.4 telemetry** | Already in Section 6 R5 note; Phase 8 diary must attribute any early-IS magnitude spike to R5 cold-start, not structure (the /085 forensic discipline). |
| **Rec 5 — diversification is CONDITIONAL; 0.548 is the least-correlated SURVIVOR not a classic low-corr; compute realized PnL-stream corr, not return-corr proxy** | **ADOPTED — promoted to F5 + bundle-assembly precondition** | This is the single most important caveat. The 0.548 is return-correlation; the BUNDLE-003 seat decision must use the realized TRB-specialist-PnL vs bundle-PnL correlation. See F5. |
| **(implicit) "add a feature" / change the lock** | **REJECTED by design** | The entire /086 thesis is that the edge is in the stock 48-col stack; adding features is the /085 crater mechanism. No HP-bound or lock changes (max_depth=5, num_leaves=31, n_trials=30, 50 seeds all fixed). |

**Net**: no HP-bound or feature changes (all within-lock); the LM's diversification-conditionality (Rec 3 + Rec 5) is promoted to a formal falsifier F5 and a BUNDLE-assembly precondition.

---

## Section 4 — Falsifiers + Verdict Bands

Since there are **no new features**, the falsifiers are framed around realized Sharpe vs the probe and vs the bundle-member IS distribution (NOT feature-importance ranks).

- **F1 — trade-rate floor**: realized **≥ 50 OOS trades AND ≥ 50 IS trades** (per `feedback_v1_trade_rate_floor_50_per_specialist`; the probe already showed 180 IS trades, so a strong count is expected). FAIL < 30 OOS → auto-reject; 30–49 OOS → 7-outer-seed validation or baseline-anchor fallback.
- **F2 — probe-consistency**: realized 50-seed **IS Sharpe ≥ +0.30** (consistent with the +0.4930 single-seed probe). If it collapses **below +0.00** → **NEGATIVE-PROBE-INCONSISTENT** (the single-seed probe was a lucky basin) — but `cross_seed_sharpe_std` adjudicates: a low std with a positive mean confirms a stable basin; a high std (> 0.50) with a positive single-seed but negative ensemble mean is the basin-lottery signature.
- **F3 — SPECIALIST candidacy** (positions TRB vs the BUNDLE-002 member IS distribution: DOT +1.32, ETH +0.24, BTC +0.07, AAVE +0.34):
  - **VALIDATED** iff IS Sharpe **≥ +0.50** (clears the probe and is bundle-competitive — ETH/BTC/AAVE-class or better).
  - **PROMISING** iff IS Sharpe ∈ **[+0.20, +0.50]** (below the probe but plausibly bundle-accretive via low correlation).
  - **NEGATIVE** iff IS Sharpe **< +0.20**.
- **F4 — TS-mom-beat**: realized IS Sharpe must **exceed the trivial min-horizon −0.179 AND clear +0.00**. FAIL (IS < 0) → NEGATIVE-MOMENTUM-DOMINATED (worse than not trading IS).

- **F5 — diversification-conditionality (NEW, promoted from LM Master Rec 3 + Rec 5; load-bearing for the bundle-seat decision)**: TRB's diversification value is CONDITIONAL on its momentum tier binding ABOVE the bundle-shared anchors. Two pre-registered Phase 7.4 checks: (a) **importance-ordering** — `mom_macd_line_12_26_9` AND/OR `trend_adx_14` must rank in the TRB IS top-5, ABOVE the shared `vol_atr_14`/`oi_delta_30_z90` anchors NOT being the *sole* top-2; if `vol_atr_14` + `oi_delta_30_z90` dominate AND MACD/ADX sit rank > 8, TRB is **re-learning the shared bundle basis** → diversification thesis WEAKENED (flag `DIVERSIFIER-DEGENERATE`); (b) **realized PnL-stream correlation** — Phase 7.4 must compute the TRB-specialist daily-PnL vs equal-weight-bundle daily-PnL correlation (IS-only); the BUNDLE-003 seat decision uses THIS realized number, NOT the 0.548 return-correlation proxy. A PROMISING standalone (F3 [+0.20,+0.50]) is bundle-accretive ONLY if realized PnL-corr comes in BELOW ~0.55. **Reframe (LM Rec 5): 0.548 is the least-correlated SURVIVOR of a high-baseline universe (STORJ 0.5505 essentially tied), NOT a classically low-corr diversifier — the benefit is REAL but MODEST and must be earned via differentiated trade-timing, verified in Phase 7.4.**

**Pre-registered bundle-fit note**: TRB's value is as a LOW-CORRELATION diversifier (H2). A moderate standalone IS Sharpe in the **[+0.20, +0.50]** band could still be **bundle-accretive** if the realized PnL-stream correlation (F5b, NOT the 0.548 return-corr proxy) holds low OOS — i.e., a PROMISING standalone with confirmed low PnL-correlation AND F5a importance-ordering pass is a legitimate BUNDLE-003 candidate seat, evaluated for accretion at the future BUNDLE assembly, NOT discarded for being sub-+0.50. This pre-registration prevents post-hoc rationalization in either direction: a sub-+0.20 result is NEGATIVE regardless of correlation; a [+0.20,+0.50] result is PROMISING-pending-bundle-fit (F5a + F5b must pass); a ≥+0.50 result is VALIDATED.

---

## Section 6 — Risk Mitigation (R1–R5 recap)

No new risk primitive is introduced; the recap states the inherited stack and its IS-calibrated thresholds:

- **R1 (consecutive-SL cooldown)**: **OFF** for the TRB specialist (Model A pattern — IS analysis on BTC/ETH showed late-streak edge; the Model-A convention carries to single-coin specialists with R3-only wrappers; matches ETH/064, BTC/065, AAVE/078).
- **R2 (drawdown-triggered scaling)**: **OFF** (Model A pattern). Symmetric portfolio brakes are a documented dead path (increased MaxDD 55%); not introduced.
- **R3 (OOD Mahalanobis gate)**: **ON, shared 0.70 cutoff**, 16 scale-invariant features — identical to all 4 incumbent seats; IS-calibrated at the 70th-percentile cutoff inherited from the baseline. Simulated historical effect: R3 at 0.70 is the standard gate active across BUNDLE-002; no per-symbol re-tune (per-symbol OOD on top of portfolio OOD is a dead path).
- **R5 (vol-targeting)**: **ON**, target 0.3, 45-day lookback, scale ∈ [0.33, 2.0]. **Cold-start flag** (carried from the /085 diagnosis): the first ~45 days of a fresh-alt's IS can run at full weight_factor before the vol history accumulates, amplifying any early-IS magnitude. TRB has 4.55 IS years, so the cold-start window is a small fraction of IS — but the Phase 8 diary must attribute any early-IS magnitude spike to the R5 cold-start, not to the symbol's structure (the /085 forensic showed 94% of UNI's catastrophic IS magnitude was an R5 cold-start artifact in 2022-09). This is an attribution discipline, not a new primitive.

---

## Section 7 — Pre-Registered Modal Outcome

**Modal prediction**: TRB realizes an **IS monthly Sharpe in the [+0.30, +0.55] band** (probe-consistent), with `cross_seed_sharpe_std < 0.30` (stable basin, not a lottery), **≥ 130 IS trades and ≥ 50 OOS trades**, landing in the **F3 VALIDATED (≥+0.50) or upper-PROMISING ([+0.20,+0.50])** band. This is the FIRST structure-gated fresh mine, so the prior is materially more favorable than the 0/5 blind-mine base rate — but the conjunction "negative-baseline AND structure-present → positive specialist under the locked stack" remains formally UNTESTED (the /084 caveat), so a PROMISING (not VALIDATED) outcome is the single most likely cell.

**Confidence**: MEDIUM. The probe is the strongest pre-flight evidence any v1 fresh mine has carried, but single-seed probe → 50-seed reproduction has a real basin-translation gap (the cycle-6/7 basin-lottery rate was 100% on single-seed PROMISING tags, which is precisely why the 50-inner-seed ensemble is mandated here). The OOS number is informational only (the QR sees it for the first time in Phase 7) and is NOT part of the candidacy decision at SPECIALIST budget.

**What would surprise me**: an IS Sharpe < +0.00 (F2 FAIL) — that would mean the +0.4930 probe was a lucky single-seed basin and would, for the first time, falsify the GATE-2 probe's predictive value (CRV + UNI validated it on the *reject* side; TRB is the first test of the *pass* side).

---

## Section 8 — SPECIALIST Candidacy Bands

| Realized IS Sharpe | Band | Roster action | Bundle-fit |
|---|---|---|---|
| ≥ +0.50 | **SPECIALIST-VALIDATED** | enters BUNDLE-003 candidate roster | bundle-competitive (ETH/BTC/AAVE-class or better) AND low-correlation diversifier |
| [+0.20, +0.50] | **SPECIALIST-PROMISING-TENTATIVE** | enters roster, TENTATIVE | bundle-accretive IFF 0.548 correlation holds OOS; evaluated for accretion at BUNDLE assembly |
| < +0.20 (≥ 0) | **SPECIALIST-NEGATIVE** | TRB dropped | not bundle-accretive at this standalone level |
| < +0.00 | **SPECIALIST-NEGATIVE (PROBE-INCONSISTENT)** | TRB dropped; probe-side GATE-2 predictive value re-examined | — |

**Candidacy is standalone-IS-driven with an explicit low-correlation carve-out**: TRB does NOT need a ≥+0.50 standalone Sharpe to be a useful BUNDLE-003 seat — its diversification value (lowest bundle-correlation in the eligible universe) means a [+0.20, +0.50] PROMISING result is a legitimate candidate seat. The actual bundle-accretion test (does adding TRB lift bundle Sharpe?) is deferred to the future BUNDLE-003 assembly, with IS-only weights and pairwise-disjoint universe per the standing HARD rules (`feedback_v1_bundle_no_coin_overlap`, `feedback_v1_bundle_weight_is_only`, `feedback_v1_backtest_live_parity_hard`).

---

## Section 9 — Methodology / Validation Recap

- **No-cheating**: every EDA series is IS-only (`open_time < OOS_CUTOFF_MS`), verified in-code in both committed scripts (not trusted from prose). OOS is never read for selection. Sacred constants held: `OOS_CUTOFF_DATE=2025-03-24`, `training_months=24`.
- **Look-ahead**: ATR for the triple-barrier is past-only; walk-forward embargo `train_end_ms = test_start_ms - embargo_ms` (the foundation fix; Phase 6.0 Critic re-verifies it has not regressed).
- **Feature-column pinning**: explicit 48-col `V1_FEATURE_COLUMNS_PRUNED` list passed to `LightGbmStrategy`; never None/empty.
- **One-variable discipline**: the ONLY change vs the incumbent specialist template is the SYMBOL (TRBUSDT). Stock 48-col stack, R3-only wrapper, ATR 2.9/1.45 label, 24-mo walk-forward — all unchanged. Global `V1_FEATURE_COLUMNS_PRUNED` stays 48. Critic Check 8 + Check 14 verify the diff matches this declaration.
- **Validation suite at SPECIALIST budget**: DSR/PSR/PBO computed and reported but **INFORMATIONAL ONLY** at single-outer-seed SPECIALIST budget (per the v3-precedent `feedback_v3_dsr_mode_artifact` — EXPLORATION/SPECIALIST-budget DSR is a regime-specific artifact, not a CONFIRMATION-grade merge gate). `cross_seed_sharpe_std` is the operative basin-stability metric.
- **Library stack**: LightGBM (locked head), `statsmodels` adfuller (informational ADF), scipy spearman (GATE-2 IC). No new libraries.
- **Multi-seed CONFIRMATION**: PERMANENTLY DROPPED (user directive). The 50-inner-seed ensemble is the variance control. NOT proposed.

---

## Summary

TRBUSDT (Tellor) is the FIRST fresh-mine candidate to clear the full HARD gate ladder — GATE 0 lowest bundle-correlation (0.548), GATE 1 negative short-horizon trivial baseline (−0.179), GATE 2 PRIMARY structure-probe PASS (+0.4930), GATE 2 SECONDARY momentum/trend feature-IC (0.3863). The specialist trades the STOCK 48-col stack with ZERO new features (explicitly avoiding the /085 inert-feature crater), as a low-correlation BUNDLE-003 diversifier candidate. Global `V1_FEATURE_COLUMNS_PRUNED` stays 48. No new risk primitive. Single-outer-seed HIGH-RISK with the 50-inner-seed ensemble as variance control. No MERGE this iteration; a positive verdict makes TRB a BUNDLE-003 candidate seat.
