# Iteration v1-084 — Research Brief

**Track**: v1 (refactored; SPECIALIST + BUNDLE methodology)
**Type**: SPECIALIST (single-coin) — 5th specialist candidate for BUNDLE-003 (CRVUSDT)
**Anchor baseline**: BUNDLE-002 (`v0.v1-082`) — IS monthly Sharpe +0.7157 / OOS monthly Sharpe +1.0043 / 694 IS + 320 OOS trades; 4-component union {BTC, ETH, DOT, AAVE}
**User directive (2026-06-09)**: *"option 3. learn from the mistake and try to improve the symbol selection and eda"*
**Methodology LOCKED**: 50 inner seeds (42..91) × 30 Optuna trials × specialist_mode × LightGBM; `max_depth=5` FIXED, `num_leaves=31` FIXED; outer seed=42 SPECIALIST budget. NEVER change.
**LM Master verdict**: MEDIUM confidence; predicted CRV specialist IS Sharpe **+0.55** (range +0.30 to +0.80); if R-FADE INERT, feature-alone IS ≈ +0.45. Dominant failure path: R-FADE either INERT (<3% fire) OR over-vetoes below the ≥50 OOS floor.

This iteration is the **direct correction of the /083 mistake**. /083 (FILUSDT) failed on the positive-baseline trap (F4 NEGATIVE-MOMENTUM-DOMINATED): FIL had a strongly POSITIVE trivial TS-momentum baseline (+1.45 at (5,1)), so the depth-5 ML head had no headroom and degenerated into a negative-Sharpe momentum proxy. /084 applies the **REFORMED SELECTION RULE** — prefer the symbol with the MOST NEGATIVE / near-zero trivial-momentum Sharpe — and re-aims the two genuine /083 learnings (the OI-family feature; the post-aggregator gate pattern) onto that reformed-selector pick: CRVUSDT. It is authored under the cycle-6/cycle-7 per-symbol regime-specialist mandate (`feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md`), under which axis-family rotation is suspended and feature-engineering is MODAL.

---

## Section 0 — Data Split Declaration (Foundation)

- **OOS_CUTOFF_DATE**: `2025-03-24` (IMMUTABLE sacred constant — never changes; `src/crypto_trade/config.py`, `OOS_CUTOFF_MS=1742774400000`)
- **training_months**: `24` (IMMUTABLE sacred constant — never changes)
- **IS window**: 2023-03-24 → 2025-03-24 (24-month walk-forward training window; CRV IS roster = 2,193 8h candles in the strict IS window per the OI-feature audit, 4,995 IS bars total back to listing per the trivial-momentum EDA)
- **OOS window**: 2025-03-24 → present (2026-06-09); CRV OOS extent = **1,326 8h candles** (~14.5 months) per `data/CRVUSDT/8h.csv`
- **Walk-forward embargo**: `train_end_ms = test_start_ms − embargo_ms` (commit `5566a69`; inherited bit-exactly from the /063 → /064 → /065 → /078 → /083 SPECIALIST family)
- **Data freshness**: CRV last `close_time` age 9.0h (< 16h staleness guard, PASS); OI cache extends to the same bar.
- **Sacred constants HELD** per `feedback_training_window.md` + `feedback_no_cheating.md`: no shift, no extension, no trim, no peek. The OOS window is NEVER read during Phases 1–5.

All EDA scripts (`analysis/iteration_v1-084/eda_crv_deep.py`, `eda.py`, `eda_gala_chz_axs_crv.py`, `eda_oi_fade_calib.py`) enforce `open_time < OOS_CUTOFF_MS` for ALL calibration statistics, with an explicit runtime leak assertion (`assert df["open_time"].max() < OOS_CUTOFF_MS`). No OOS file is opened to derive any threshold, band edge, or signal — including the pre-registered R-FADE `fade_z`.

---

## Section 0.5 — Iteration Type Declaration & Cadence

- **TYPE**: **SPECIALIST** — NEW SYMBOL universe-extension (single-coin cohort `("CRVUSDT",)`).
- **Cycle-7 position**: SPECIALIST-MINE (5th NEW-SYMBOL universe-extension; the FIRST under the REFORMED negative-baseline selector after /083 falsified the narrative-orthogonality selector).
- **Mining context**: under the cycle-6+7 per-symbol regime-specialist mandate, SPECIALIST iterations are single-symbol regime-specialist EXPLORATIONs; the user directive 2026-06-09 ("learn from the mistake and try to improve the symbol selection and eda") authorizes CRVUSDT as a NEW SYMBOL with a re-aimed NEW feature and a NEW risk primitive, selected by the empirically-validated trivial-baseline rule rather than narrative.
- **Wall-clock budget**: **2h hard cap** is the EXPLORATION default; the methodology-lock spec (50 inner seeds × 30 trials × 24 months ≈ 36,000 fits) is projected at **~5.5–8h** per the runner docstring — this is the SAME methodology-lock budget the /078 AAVE seat and /083 FIL seat ran under (user-mandated SPECIALIST budget exceeds the default cap by design). QE monitors and reports wall-clock at Phase 7.4; there is NO mid-run kill-switch for wall-clock (overrun documented, not killed).
- **Verdict frame**: ranked relative to the BUNDLE-002 member IS Sharpe distribution (DOT/063 +1.32, ETH/064 +0.24, BTC/065 +0.07; the NEW-SYMBOL-at-locked-stack prior set is AAVE/076 −0.69 → /078 rescue +0.34 and FIL/083 −0.82). CRV's operative prior is the LM Master modal **+0.55** (MEDIUM headroom), bounded below DOT's +1.32 (CRV headroom is regime-narrow) and above the FIL −0.82 disaster (CRV trivial baseline is no longer dominant).

---

## Section 0.6 — Architecture-Family Justification (v1-only)

- **Axis family**: `per-cohort-specialization-CRV` (NEW symbol cohort; modal feature-family + risk-primitive composition under the per-symbol regime-specialist mandate).
- **Mandate context**: under `feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md` (2026-06-01 user directive, 2 cycles MINIMUM), the standard 5-family axis-rotation discipline is **SUSPENDED**. SPECIALIST iterations are single-symbol regime-specialist EXPLORATIONs; feature-engineering is MODAL; the same symbol may appear any number of times; CONFIRMATION assembles regime-complementary specialists from the running roster. The relevant discipline is therefore NOT axis-family rotation but **symbol-cohort orthogonality + pairwise-disjointness vs the live BUNDLE-002 universe**.
- **Prior 5 SPECIALIST cohorts (running roster feeding BUNDLE-002 + recent attempts)**:
  - iter-v1/063: `per-cohort-specialization-DOT` (DOT specialist; BUNDLE-002 seat 1)
  - iter-v1/064: `per-cohort-specialization-ETH` (ETH specialist; BUNDLE-002 seat 2)
  - iter-v1/065: `per-cohort-specialization-BTC` (BTC specialist; BUNDLE-002 seat 3)
  - iter-v1/078: `per-cohort-specialization-AAVE` (AAVE specialist; BUNDLE-002 seat 4, PROMISING-TENTATIVE)
  - iter-v1/083: `per-cohort-specialization-FIL` (FIL specialist; SPECIALIST-NEGATIVE-MOMENTUM-DOMINATED; non-roster)
- **Rotation status**: **VALID** — `CRVUSDT` ∉ {DOT, ETH, BTC, AAVE} (the four live BUNDLE-002 cohorts) and ∉ {LINK, LTC, ATOM, ICP, FIL} (ALREADY-FAIL) and ∉ `V1_EXCLUDED_SYMBOLS` {SOL, XRP, DOGE, NEAR, BCH, LDO, TRX, BNB}. The new cohort is a fresh DeFi-AMM-governance narrative cluster, distinct from store-of-value (BTC) / L1-smart-contract (ETH) / L1-PoS-interop (DOT) / DeFi-lending (AAVE).
- **One-sentence rationale**: CRVUSDT is the empirically-selected pick under the REFORMED selector — it has the **lowest min-across-horizon trivial-momentum Sharpe (+0.069) of all 12 surveyed candidates**, with a strongly NEGATIVE bear-regime trivial Sharpe (−0.924), meaning trivial momentum is systematically wrong in CRV's dominant bear+chop regimes — exactly the headroom a non-linear depth-5 head needs and exactly the precondition FIL/083 lacked.

---

## Section 1 — Hypothesis

**A CRVUSDT LightGBM specialist, selected by the REFORMED negative-trivial-baseline rule (min-horizon trivial Sharpe +0.069; bear-regime −0.924), equipped with the sign-aware 30-bar OI-price divergence feature (`oi_price_divergence_30`, re-aimed from the /083 OI family) and an OI-divergence-conditional fade gate (R-FADE), extracts a per-symbol IS+OOS edge that the trivial momentum rule cannot — because CRV does NOT trend cleanly — making it a strictly-accretive 5th BUNDLE-003 seat that expands the denominator and dilutes the 33.96% BTC top-symbol concentration toward the ≤30% gate.**

**The /083→/084 correction (the load-bearing reform):**

| Selector | /083 (FALSIFIED) | /084 (REFORMED) |
|---|---|---|
| Rule | narrative orthogonality ("storage-economics is regime-orthogonal") | trivial TS-momentum Sharpe, IS-only, MOST NEGATIVE preferred |
| Symbol | FILUSDT | CRVUSDT |
| Trivial baseline | **+1.45 (5,1) — POSITIVE → no ML headroom** | **+0.069 min-horizon — near-zero; bear −0.924 → ML headroom** |
| Outcome | ML IS −0.82 (degenerate momentum proxy); F4 FAIL | predicted IS +0.55 (LM Master MEDIUM) |

The empirical precedent set is now triple-confirmed: LINK/066 (+positive trivial → NEGATIVE), LTC/067 (+positive → NEGATIVE), FIL/083 (+1.45 → NEGATIVE) ALL failed the positive-baseline trap; DOT/063 (negative/weak trivial → IS +1.32) and AAVE/078 (negative pre-rescue → WORKED) both had headroom. CRV is the deliberate inverse of FIL under this rule.

**Why the OI feature binds to the FEATURE, not the symbol (the /083 transplant)**: at FIL/083 the OI-family bound cleanly — `oi_delta_30_z90` rank 7/49 and `fil_oi_price_divergence_30` rank 11/49 — yet the symbol failed F4. The /083 diary lesson #2 is explicit: *"A feature can bind while the symbol fails… decouple the verified learning (the OI-family feature) from the failed carrier (the FIL symbol) — transplant the feature to a seat that has headroom."* /084 is that transplant: the sign-aware OI-price divergence feature, on a negative-baseline symbol.

**PRE-REGISTERED RISK — barely-positive (not strongly negative) baseline (LM Master Risk Flag 2, the honest caveat)**: CRV's +0.069 min-horizon is MEDIUM headroom, NOT HIGH. The strongest precedents (DOT, AAVE) had genuinely NEGATIVE pre-rescue baselines; CRV's headroom is **regime-localized** (bear −0.924, chop −0.055, bull +2.570). The ML edge — IF it materializes — will be concentrated in bear+chop months (4,138 of 4,931 IS bars), and the monthly-Sharpe dispersion is very high (std 3.567). This dispersion is the edge source AND the overfit risk simultaneously. This is pre-registered HERE and hardwired into F4 (Section 4): if the CRV ML IS Sharpe does not exceed the trivial +0.069 min-horizon AND the trivial +0.293 (21d) baseline, the specialist adds nothing over momentum and is reclassified NEGATIVE-MOMENTUM-DOMINATED — a MUCH lower bar to clear than FIL's +1.45, by construction of the reform.

**Falsification frame**: the hypothesis is FALSE if (a) the CRV specialist fails the per-specialist trade floor (≥50 IS AND ≥50 OOS; F1), OR (b) the NEW feature is INERT (importance < 30 / rank ≥40 in >50% months — F2), OR (c) the R-FADE gate is mechanically inert OR over-vetoes below the OOS floor (F3), OR (d) the ML IS Sharpe fails to beat the trivial momentum baseline (F4). All four are pre-registered HARD falsifiers in Section 4.

---

## Section 2 — IS-Only Evidence

All numbers below are produced by the committed IS-only scripts (reproducible from worktree root; every script enforces `open_time < OOS_CUTOFF_MS` with a runtime leak assertion):
- `analysis/iteration_v1-084/eda_crv_deep.py` — mandate items 1–5 (trivial-momentum curve, per-regime, NATR, data-extent, pooled-baseline shape).
- `analysis/iteration_v1-084/eda.py` + `eda_gala_chz_axs_crv.py` — candidate-pool sweep (the 12-symbol selection table).
- `analysis/iteration_v1-084/eda_oi_fade_calib.py` — mandate items 6–7 (OI-divergence distribution + R-FADE `fade_z` calibration).

### 2.1 — The REFORMED selector: trivial-momentum candidate pool (the "improve the symbol selection" deliverable)

Trivial TS-momentum Sharpe, IS-only, fee-adjusted (0.05%/side, turnover-aware), long-if-ret>0 / short-if-ret<0, sorted by min-across-horizon (most negative first):

| Symbol | data_y | IS_bars | s5 | s21 | s50 | **min-horizon** | NATR p50 | verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| ARBUSDT | 2.00 | 2195 | +0.631 | +0.005 | +0.876 | +0.005 | 4.122 | NONE (<4y) |
| **CRVUSDT** | **5.77** | **4995** | **+0.343** | **+0.293** | **+0.068** | **+0.068** | **5.683** | **MEDIUM ← SELECTED** |
| OPUSDT | 2.81 | 3080 | +1.079 | +0.162 | +0.275 | +0.162 | 4.866 | NONE (<4y) |
| ALGOUSDT | 4.77 | 5225 | +0.242 | +0.402 | +0.735 | +0.242 | 4.667 | LOW |
| MANAUSDT | 4.02 | 4395 | +0.263 | +0.673 | +0.810 | +0.263 | 4.400 | LOW |
| ETCUSDT | 5.18 | 5681 | +0.865 | +0.350 | +0.513 | +0.350 | 4.171 | LOW |
| SANDUSDT | 4.16 | 4542 | +1.800 | +0.447 | +0.940 | +0.447 | 4.925 | LOW |
| CHZUSDT | 5.11 | 4569 | +0.939 | +0.825 | +0.454 | +0.454 | 4.714 | LOW |
| EGLDUSDT | 4.52 | 4956 | +0.619 | +0.749 | +0.961 | +0.619 | 4.494 | LOW |
| GALAUSDT | 4.66 | 3849 | +0.854 | +0.627 | +0.991 | +0.627 | 5.085 | LOW |
| FTMUSDT | 4.49 | 4911 | +0.676 | +1.254 | +0.765 | +0.676 | 5.845 | LOW |
| AXSUSDT | 5.49 | 4755 | +0.906 | +1.166 | +1.504 | +0.906 | 4.692 | NONE (FIL-trap) |

**CRVUSDT is the lowest-min-horizon eligible (≥4y) candidate at +0.068.** ARB (+0.005) and OP (+0.162) are lower/comparable but disqualified at <4y data. Among ≥4y candidates CRV is unambiguously the most-neutral trivial baseline. This is the empirically-grounded inverse of the /083 narrative selector. Note the trivial baseline is horizon-dependent (the mandate's reason to compute multiple horizons): CRV's 50d is essentially flat (+0.068), 21d +0.293, 5d +0.343 — the longer the horizon, the LESS the trivial rule works, which is the headroom signal.

### 2.2 — Per-regime trivial Sharpe (the real prize: bear/chop are where momentum is WRONG)

CRV trivial-21d-momentum Sharpe by regime (50-bar vol-normalized slope tag; IS-only):

| Regime | IS bars | trivial Sharpe (21d) |
|---|---:|---:|
| bull | 793 | **+2.570** |
| bear | 695 | **−0.924** |
| chop | 3,443 | **−0.055** |

**The headroom is regime-localized.** In bull regimes the trivial rule is strongly right (+2.57) — ML has NO room there and should not fight it. In bear (−0.924) and chop (−0.055) — which are **4,138 of 4,931 IS bars (84%)** — trivial momentum is wrong or flat. That is precisely where a non-linear depth-5 head + the OI-divergence regime conditioner has room to add edge. This is the structural reason CRV passes the reformed gate where FIL (positive across all regimes) failed.

### 2.3 — NATR vol profile, autocorrelation, pooled-baseline shape (mandate items 3 + 5)

| Quantity | Value | Note |
|---|---:|---|
| NATR(14) rolling-30 p10 / p25 / p50 / p75 / p90 | 3.33 / 4.09 / **5.68** / 7.89 / 10.01 (%) | HOTTER than DOT/AAVE (~4–5% p50); LM Master Flag 3 |
| Bar-return autocorr lag1 / lag3 / lag7 | −0.0260 / −0.0236 / −0.0025 | near-zero / mild mean-reversion → LightGBM-exploitable non-linearly |
| Pooled-baseline (21d trivial) PnL skew / kurt / %pos | +0.061 / +5.27 / 47.7% | fat-tailed (kurt 5.27); sub-50% win-rate consistent with a directional-edge-absent baseline |
| IS monthly trivial-Sharpe mean / std / n | +0.062 / **3.567** / 55 | VERY high monthly dispersion → bear-localized edge + overfit risk (LM Master Flag 2) |

**Vol-overshoot read (LM Master Flag 3 / HP Rec observation)**: CRV NATR p50 5.68% (rolling-30) is materially hotter than the bundle's cooler symbols. At fixed ATR 2.9/1.45 the SL distance scales with realized ATR, so this is partly self-normalizing — but the triple-barrier label mix (timeout/SL/TP) will skew vs cooler symbols and the SL-hit rate is expected high. This is a Phase 7.4 telemetry item, NOT an ATR change at this iteration (single-bit discipline).

### 2.4 — oi_price_divergence_30 feature distribution (mandate item 6; the re-aimed /083 OI family)

`oi_price_divergence_30[t] = zscore_90( sign(oi_delta_30[t]) − sign(ret_30[t]) ).shift(1)`, all components past-only, clipped [−10,+10]. Computed via the PRODUCTION `crypto_trade.features_v1.open_interest_v1.add_oi_price_divergence_30_feature` on the full frame (120-bar warmup consumes pre-IS bars; OI cache starts 2021-12-01, ~479 days before IS start). IS-only slice (n=2,193):

| Quantity | Value |
|---|---:|
| IS NaN | 121 (5.52%) — intermittent OI-cache gaps inside IS; benign (LightGBM `use_missing=True`) |
| mean / std | +0.0249 / 1.1709 |
| nonzero fraction | 99.6% |
| percentiles p1 / p5 / p25 / p50 / p75 / p95 / p99 | −2.58 / −1.92 / −0.77 / +0.08 / +0.93 / +1.77 / +2.47 |
| frac \|z\|>1.5 / >2.0 / >2.5 | 0.2066 / **0.0719** / 0.0222 |

The distribution is well-behaved and near-symmetric; the sign-difference operator yields a genuinely new column (it quantizes both legs to {−1,0,+1} and z-scores the {−2,0,+2} disagreement — magnitude discarded, only directional CONFLICT survives). LM Master pre-warns expected \|IC\| vs `oi_delta_30_z90` ≈ 0.15–0.35 (clears the Critic redundancy threshold; no Category-2 IC carve-out needed — this is NOT an algebraic sister of `oi_delta_30_z90`).

### 2.5-evidence — R-FADE fade_z calibration (mandate item 7; pre-registered BEFORE OOS)

The gate vetoes an entry when the trade direction OPPOSES the OI-divergence sign AND `|oi_div| > fade_z`. To pre-register `fade_z` IS-only, the calibration tabulates a per-bar forward-return proxy (using the trivial-21d-momentum direction as a stand-in for the ML signal) conditioned on AGREE vs DISAGREE × `|z|` buckets. **Trade-aligned forward return (bps), IS-only:**

| `|z|` bucket | AGREE n / mean_bps | DISAGREE n / mean_bps | DISAGREE − AGREE |
|---|---:|---:|---:|
| \|z\|<1.0 | 562 / +5.04 | 570 / +24.42 | +19.4 |
| 1.0–1.5 | 134 / −54.82 | 320 / +14.40 | +69.2 |
| 1.5–2.0 | 118 / −7.44 | 147 / +10.46 | +17.9 |
| **2.0–2.5** | 62 / +31.14 | 40 / **−4.09** | **−35.2** |
| \|z\|≥2.5 | 26 / −46.10 | 20 / −12.69 | +33.4 |

**Honest read (this is the most important caveat in the iteration)**: the relationship is NOT cleanly monotone. The ONLY bucket where DISAGREE underperforms AGREE by a meaningful margin is **2.0–2.5 (−35.2 bps)** — and the support is thin (40 DISAGREE bars). The `|z|≥2.5` bucket actually REVERSES (DISAGREE outperforms). The proxy is noisy: the trivial-21d direction is NOT the ML signal direction, so the calibration is directional guidance, not a guarantee. The pre-registration rule (lowest `|z|` bucket where DISAGREE underperforms AGREE by ≥5 bps) selects the **2.0–2.5 lower edge → `fade_z = 2.0`**, which matches the runner default (`OI_DIVERGENCE_FADE_Z = 2.0`, FROZEN at brief commit, anti-tuning assertion in `run_iteration_084.py:239`). At `fade_z=2.0` the gate is eligible on only **7.2% of bars** (frac `|z|>2.0`), and fires on the subset of those that are also DISAGREE entries — so the realized veto rate is far lower, raising the genuine INERT risk (F3 branch a).

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

- **Declaration**: **HIGH-RISK**
- **Reason**: this iteration is a **NEW SYMBOL universe-substitution** (CRVUSDT has never been a training-objective for any v1 specialist) STACKED with a NEW feature column (changes the feature-importance allocation surface) AND a NEW risk primitive (R-FADE alters the eligible-trade set Optuna's downstream PnL is measured against). All three are HIGH-RISK triggers under the v1 Section 2.5 rubric. The change alters Optuna's training-objective domain. The CRV-specific risk profile: a barely-positive (+0.069, not negative) baseline with bear-localized headroom (Flag 2), very high monthly dispersion (std 3.567), a hot-vol loss surface (NATR p50 5.68%, Flag 3), and a thin/non-monotone R-FADE calibration (Section 2.5-evidence) that makes the gate the highest-variance element.
- **Mitigation (HIGH-RISK; OPT-IN per v1 rule)**: **single-seed=42 EXPLORATION** with 50-INNER-seed averaging (the load-bearing SPECIALIST architecture; the 50-seed inner ensemble is the variance control that makes single-seed basin-lottery a non-issue — the failure mode that killed BTC/065 + DOT at single-seed cycle-6 EXPLORATION). Per the v1 rule, HIGH-RISK declaration is MANDATORY but multi-outer-seed validation is OPT-IN at SPECIALIST budget; it is **DEFERRED** to a follow-on CONFIRMATION if /084 verdicts PROMISING AND `feedback_v1_basin_lottery_vigilance.md` triggers fire (per-seed spread > 0.50 OR Jaccard < 0.40 OR Spearman ρ < 0.50). The diary records the single-seed choice and the OOS outcome. **Escalation clause**: per the v1 rule, if 3+ consecutive HIGH-RISK single-seed SPECIALISTs produce >1σ negative deltas in a row, the next HIGH-RISK iteration becomes mandatorily multi-seed. (Recent HIGH-RISK single-seed SPECIALIST deltas: AAVE/076 −0.69, FIL/083 −0.82 — two negatives; CRV/084 is the third HIGH-RISK single-seed in this run. If /084 also lands >1σ negative, the NEXT HIGH-RISK iteration is mandatorily multi-seed.)
- **Attribution-entanglement acknowledgment**: two NEW axes stacked (feature + risk) on a NEW symbol means a NEGATIVE verdict cannot cleanly separate the contributions. The per-axis attribution plan is hardwired into Section 4: the R-FADE-OFF control run isolates the risk primitive; importance rank isolates the feature; the TS-mom-beat (F4) isolates the symbol/headroom. The user directive ("improve the symbol selection and eda") + the /083 transplant lesson sanction the feature+risk stack; the attribution plan makes the verdict interpretable.

---

## Section 3 — Proposed Changes

### 3.1 — Symbol (universe expansion)
- **ADD** `CRVUSDT` as a new single-coin specialist cohort. `V1_ITER084_UNIVERSE = ("CRVUSDT",)`.
- Pairwise-disjoint vs BUNDLE-002 {BTC, ETH, DOT, AAVE} (Section 0.6). No overlap; Critic Check 16 PASS by construction at the SPECIALIST layer (full BUNDLE-universe disjointness re-verified at BUNDLE-003 assembly).

### 3.2 — Feature (1 new column; 48 → 49)
- **ADD** exactly one column `oi_price_divergence_30` to `V1_FEATURE_COLUMNS_PRUNED` (48 → **49**; verified `len == 49`, asserted in `__init__.py:213` and `run_iteration_084.py:217`). Inserted alphabetically between `oi_delta_30_z90` and `regime_momentum_signed_5d`.
- Computed (all components past-only via `.shift(1)`) in `src/crypto_trade/features_v1/open_interest_v1.py::add_oi_price_divergence_30_feature` (already landed):
  - `oi_delta_30 = sum_open_interest.pct_change(30)` (clipped [−1.0, +5.0]) from `data/open_interest/CRVUSDT/8h.csv`, merge_asof-backward / exact 8h-int merge into the klines
  - `ret_30 = log(close).diff(30)`
  - `div_raw = sign(oi_delta_30) − sign(ret_30)` ∈ {−2, 0, +2} (nonzero only when OI and price disagree on direction)
  - `oi_price_divergence_30 = z90(div_raw).shift(1)` where `z90 = (x − rmean_90) / (rstd_90)`; an extra `.shift(1)` on the final output guards that bar t uses at most bars ≤ t−1. Clipped [−10, +10].
- NaN warmup ~120 bars (30 for delta + 90 for z); filled by LightGBM native NaN handling. OI cache covers 2021-12 → present (full IS after warmup; PASS).
- **NON_FEATURE intermediates**: `oi_delta_30`, `ret_30`, `div_raw` are computed internally and discarded — they are NOT passed as model columns (the function appends only `oi_price_divergence_30`).
- Track-isolated: `open_interest_v1.py` has ZERO imports from `features_v2` / `features_v3` (Critic Phase 6.0 grep PASS).
- **Parquet regen confirmed**: pre-feature 48-col hash `e0292892e28a0f51` → post-feature 49-col hash `274348d5eb93f9d6` (runner docstring lines 48–49).

### 3.3 — Risk (R-FADE — NEW primitive)
- **ADD** R-FADE OI-divergence-conditional fade gate to `LightGbmStrategy` as canonical `enable_X` kwargs (default OFF → bit-identical to all prior runs):
  - `enable_oi_divergence_fade_gate: bool = False` (True ONLY in the CRV specialist cell)
  - `oi_divergence_fade_z: float = 2.0` (IS-calibrated literal, pre-registered Section 2.5-evidence; FROZEN — runner asserts `== 2.0` at line 239)
  - `oi_divergence_fade_column: str = "oi_price_divergence_30"`
- **Logic** (`lgbm.py:1910-1993`, already landed; verified to match the directive): post-aggregator, stateless. At entry, the VETO-OUTRIGHT variant fires when:
  - `signal.direction == +1` (long) AND `oi_div < −fade_z` (bearish OI tilt contradicts the long), OR
  - `signal.direction == −1` (short) AND `oi_div > +fade_z` (bullish OI tilt contradicts the short).
  When the gate fires, `get_signal` returns `Signal(direction=0, weight=0)` and logs a `decision_log` event `kind="oi_divergence_fade_gate"`. When divergence AGREES with the trade OR `|z| ≤ fade_z`, no change. NaN/inf oi_div → pass through (conservative).
- **Cascade placement** (`lgbm.py:2157`, verified): fires AFTER the AXIS-R mid-bull veto (line 2135) and after R3 OOD / aggregation — it is the last post-aggregator gate before sizing. State-free, evaluated per candle, identical in backtest and live (the gate reads only the past-only `oi_price_divergence_30` feature value, available in both contexts → parity-clean).
- **Note vs the directive's "raise confidence threshold" option**: the directive offered two implementations (raise the elevated-tau bar OR veto outright). The landed implementation is the **VETO-OUTRIGHT** variant — the cleaner, fully-stateless, parity-trivial form, reusing the AXIS-R /074 pattern exactly. This is documented as the intentional choice (the elevated-tau variant would require threading per-seed margins through the aggregator, adding state and parity risk).
- CRV specialist cell ONLY; R-FADE is not enabled for any other cohort.

### 3.4 — Methodology (LOCKED per user directive)
- 50 inner seeds (42..91) × 30 Optuna trials × specialist_mode × LightGBM; `max_depth=5` FIXED, `num_leaves=31` FIXED; `min_child_samples` removed from search (LGBM default 20); `n_estimators` cap 500; `n_startup_trials=10`; outer seed=42.
- ATR TP/SL: `atr_tp=2.9 / atr_sl=1.45` (Model A ETH cell; vol-class match for CRV; kept at default for this first CRV pass to isolate the feature + R-FADE effects; ATR tuning deferred to a follow-on if PROMISING).
- `training_months=24`, monthly retrain, `OOS_CUTOFF_DATE=2025-03-24` (sacred constants; unchanged).
- Walk-forward `train_end_ms = test_start_ms − embargo_ms` (the `5566a69` fix; unchanged).
- Aggregator: mean-of-signed-weights across 50 seeds; R3 OOD applied once (shared); R-FADE applied last.

### 3.5 — LM Master (Phase 4.5) — Per-Recommendation Response

`briefs-v1/iteration_v1-084/lgbm_advisor.md` EXISTS (MEDIUM confidence). Each recommendation and risk flag is responded to below (adopt / modify / reject + rationale). Phase 5.5 gate verifies these responses are present.

#### Hyperparameter Recommendations

| LM Master HP item | QR response | Rationale |
|---|---|---|
| **No HP change within the lock — and that is the correct call.** Holding `max_depth=5`/`num_leaves=31`/50-seed/30-trial is the right hyperparameter decision, not an omission (CRV's ~1.5–2.0k rows/cell are well inside `num_leaves=31` capacity; the 50-seed ensemble is the variance control). | **ADOPTED** | Section 3.4 holds the lock exactly. No Optuna-domain HP change. The lock is also required for comparability against the /063/064/065/078/083 specialist roster. |
| **Post-mortem observation (NOT an action now)**: watch best-trial `learning_rate`/`n_estimators` spread across the hot 2022 months; if `n_estimators` pins at the 500 cap in high-vol cells, that is a capacity signal to flag at /085. | **ADOPTED (as 7.4 telemetry)** | Phase 7.4 post-mortem will report the best-trial `n_estimators` distribution across walk-forward months. Flag (NOT fix) if it pins at 500 in the high-vol CRV cells. No HP change at /084. |

#### Feature-Engineering Recommendations

| LM Master Feature-Eng item | QR response | Rationale |
|---|---|---|
| **Rec 1 — `oi_price_divergence_30` is GO** with one caveat. Sign-difference operator makes it genuinely new (NOT a Category-2 algebraic sister of `oi_delta_30_z90`); expected \|IC\| ≈ 0.15–0.35 (clears redundancy, no carve-out needed). Expected importance rank **8–14 of 49** (regime/crowding CONDITIONER, not primary driver). If rank 1–3, treat as SUSPICIOUS (sign-features rarely dominate gain) and check per-month stability. | **ADOPTED** | Section 2.4 + F2 (Section 4) adopt importance ≥ 30 (and rank < 40 in ≥50% months) as the carve-out-aware falsifier. The expected rank 8–14 is the modal prediction; rank 1–3 is flagged SUSPICIOUS for per-month stability check at 7.4; rank ≥40 is the INERT-DROP trigger (drop after ONE verdict per `feedback_v3_inert_features_at_higher_budget.md`). |
| **Rec 2 — Do NOT stack a second OI variant this iteration** (single-axis isolation; `oi_delta_5_z30` short-window companion would confound the divergence verdict with a window-stacking effect per `feedback_v3_engineered_features_dont_stack`). Hold for /085 if /084 PROMISING. | **ADOPTED** | Section 3.2 adds exactly ONE feature column. No second OI variant. The `oi_delta_5_z30` companion stays REVERTED (per /058 closeout). Stacking deferred to /085 conditional on a PROMISING /084. |

#### Risk Flags / Saturation Risks

| LM Master Flag | QR response | Rationale |
|---|---|---|
| **Flag 1 (HIGHEST variance) — R-FADE is the dominant failure path, not the feature.** Two modes: (a) near-zero fire rate (<3% of candidate entries) → INERT → relabel PROMISING-FEATURE not PROMISING-RISK; (b) trade-rate floor breach (VETO-only gate removes trades; CRV must clear ≥50 OOS AFTER veto). MUST pre-register expected veto count from IS calibration. | **ADOPTED + HARDWIRED** | Section 2.5-evidence pre-registers: at `fade_z=2.0`, only 7.2% of bars are `|z|>2.0`-eligible, and the gate fires on the DISAGREE subset of those (realized veto rate far lower → genuine INERT risk). F3 (Section 4) requires the **R-FADE-OFF control run** so the marginal veto effect is isolated; F3 branch (a) = INERT (0 trades changed) → relabel PROMISING-FEATURE-ONLY; F3 branch (b) = over-veto below ≥50 OOS floor while control clears it. |
| **Flag 2 (MEDIUM) — CRV's +0.069 is barely-positive, not negative; headroom is bear-localized (−0.924); monthly std 3.567 is the edge source AND overfit risk.** Expect IS Sharpe carried by a minority of bear-regime windows. | **ADOPTED + HARDWIRED** | Pre-registered in Section 1 (PRE-REGISTERED RISK paragraph) + Section 2.2. F4 (Section 4) sets the TS-mom-beat bar at the trivial min-horizon +0.069 AND 21d +0.293 (a much lower bar than FIL's +1.45 by reform construction). Phase 7.4 must report per-regime / monthly IS Sharpe decomposition to confirm the edge is bear-localized (not a single-month accident — the /083 diary lesson #4). |
| **Flag 3 (MEDIUM) — hot-vol regime weighting** (NATR p50 7.885% rolling-30 single-bar; loss surface dominated by high-vol bars; triple-barrier label mix may skew; flag IS label distribution + class balance if it drifts past ~70/30). | **ADOPTED (as 7.4 telemetry)** | Section 2.3 records the NATR profile. Phase 7.4 reports the IS triple-barrier label balance (timeout/SL/TP mix + long/short class balance). No `class_weight` change now (would confound the feature/R-FADE verdict); a post-mortem trigger only if IS positive-class < 30% (LM Master "What I did NOT recommend"). |
| **Rejections noted**: no `num_leaves`/`max_depth` bump; no `class_weight='balanced'`; no second OI feature / XGBoost swap / labeling change (all single-axis-discipline rejections). | **CONCUR (all rejected as advised)** | Section 3.4 holds the lock; Section 3.2 is single-feature; no labeling/model-arch change. Single-axis discipline preserved (the iteration tests exactly TWO things — one feature + one gate — on one reformed-selection symbol). |

**LM Master confidence: MEDIUM.** QR concurs and is HONEST about the downgrade from the directive's framing: the directive's premise ("prefer the MOST NEGATIVE trivial baseline") is correct, but CRV's realized baseline is +0.069 (near-zero), NOT negative — there was no ≥4y candidate with a genuinely negative min-horizon baseline in the surveyed pool. CRV is the BEST AVAILABLE pick under the reform, with MEDIUM (regime-localized) headroom, not HIGH. The single most load-bearing risk is R-FADE (INERT or over-veto), pre-registered as F3.

---

## Section 4 — Expected OOS Impact + Falsifiers (HARD pre-registered)

### 4.1 — Predicted Sharpe delta + confidence interval (from LM Master Phase 4.5)

| Metric | Modal prediction | 90% confidence band | Source |
|---|---:|---|---|
| **IS Sharpe (mean across 50 inner seeds)** | **+0.55** | [+0.30, +0.80] | LM Master Phase 4.5 (MEDIUM headroom; bounded below DOT +1.32, above FIL −0.82) |
| **IS Sharpe if R-FADE INERT (feature-alone)** | **+0.45** | [+0.25, +0.70] | LM Master closing note |
| **OOS Sharpe** | **≈ +0.20** | [−0.30, +0.60] | derived (regime-localized edge → high OOS variance; bear-OOS dependent) |
| **OOS Sharpe Δ vs implicit single-coin baseline** | **≈ +0.20 (modal slightly positive)** | [−0.30, +0.60] | NEW SYMBOL → no prior CRV anchor; Δ measured vs the implicit `(CRVUSDT,)` cohort under the locked methodology |

**Mechanism breakdown** (LM Master): the reformed selector removes the FIL positive-baseline trap (the −0.15 to −0.97 drag that killed /083); CRV's bear+chop headroom (84% of IS bars where trivial is wrong/flat) is the edge source (≈+0.40–0.55); the OI-divergence feature adds ≈+0.10 IF utility-band (0 if INERT); R-FADE is net ≈0 on point-Sharpe but ELEVATES the σ of the estimate (INERT or over-veto). Net mechanism estimate ≈+0.55 modal, with very high monthly dispersion (std 3.567) widening the band.

**Hypothesis-rejection threshold (HARD)**: the PRIMARY hypothesis (CRV is a strictly-accretive BUNDLE-003 5th seat) is **REJECTED** if the OOS Sharpe falls below **+0.0** with adequate trades (F1-pass), OR if ANY of F1–F4 below is breached. The OOS Sharpe is informational at the SPECIALIST EXPLORATION layer (IS is the strike adjudicator) but the +0.0 threshold is pre-registered so the next CONFIRMATION QR has a frozen reference.

### 4.2 — Pre-registered HARD falsifiers

All falsifiers are pre-registered BEFORE the backtest is read (frozen at this brief's commit SHA). A breach of ANY HARD falsifier classifies the CRV specialist as NOT a BUNDLE-003 seat (subtype as specified).

#### F1 (HARD) — Trade-rate floor
**Falsified if** the CRV specialist produces **< 50 OOS trades** OR **< 50 IS trades**.
Per `feedback_v1_trade_rate_floor_50_per_specialist.md`: single-symbol specialist OOS floor is ≥50 (σ_SR ≈ 0.14 at N=50). 30–49 OOS trades → demote to 7-outer-seed re-validation requirement before any BUNDLE-003 seat; <30 → auto-reject. R-FADE over-veto is the prime suspect for an F1 breach (it is a VETO-only gate); the F3 R-FADE-OFF control isolates whether R-FADE is the sole cause. CRV OOS has 1,326 candidate bars (~14.5 months) — a healthy candidate pool, so an F1 breach would be R-FADE-driven, not data-thinness.

#### F2 (HARD) — Feature INERT
**Falsified if** `oi_price_divergence_30` importance (gain-based, walk-forward-aggregated across CRV test months) is **< 30**, OR equivalently the feature ranks **≥ 40/49 in > 50% of CRV test months**.
Expected modal rank 8–14/49 (LM Master Rec 1 regime-conditioner band). An importance < 30 verdict classifies CRV as NEGATIVE-INERT-FEATURE (the sign-aware divergence added nothing the existing `oi_delta_30_z90` + price-return features didn't supply); the feature is DROPPED after ONE verdict (no higher-budget retest, per `feedback_v3_inert_features_at_higher_budget.md`). A rank 1–3 outcome is SUSPICIOUS (sign-features rarely dominate gain) → mandatory per-month stability check at 7.4 before trusting it.

#### F3 (HARD) — R-FADE mechanically inert OR destroys trade count
**Falsified if** R-FADE is **mechanically inert** (enabling `enable_oi_divergence_fade_gate=True` changes the CRV trade roster by **0 trades** vs the R-FADE-OFF control, i.e. the gate never fires on any DISAGREE entry — Section 2.5-evidence shows the gate is eligible on only 7.2% of bars at `fade_z=2.0`, so INERT is a live risk) **OR** R-FADE **destroys trade count** (R-FADE-ON CRV OOS trades < 50 while the R-FADE-OFF control has ≥ 50 — the gate is the sole cause of an F1 breach).
Both branches require the **R-FADE-OFF control run** alongside the R-FADE-ON CRV run so the marginal R-FADE effect is isolated — this is a pre-registered requirement on the QE Phase 6 deliverable (two CRV runs: R-FADE-ON and R-FADE-OFF). The INERT branch (a) → relabel as PROMISING-FEATURE-ONLY (still a valid feature test; the R-FADE bit is dropped). There is NO `fade_z` re-calibration branch (unlike /083's R6 floor): `fade_z=2.0` is FROZEN per the anti-tuning assertion; if the gate is INERT we relabel rather than re-tune (re-tuning `fade_z` post-hoc on the same data would be the `feedback_no_cheating` violation).

#### F4 (HARD) — Momentum-dominated (TS-mom-beat; REFORMED bar)
**Falsified if** the CRV ML IS Sharpe (mean across 50 inner seeds) does **NOT exceed BOTH** the trivial min-horizon baseline **+0.069** AND the trivial 21d baseline **+0.293** (the two reformed-selector reference points).
This is the REFORMED, MUCH-LOWER bar vs FIL's +1.45 — by construction of the reform, a near-zero trivial baseline means the ML head only has to clear ≈+0.29 to demonstrate it is adding edge beyond momentum. If the CRV ML IS Sharpe ≤ +0.293, the specialist adds nothing over a momentum rule → reclassify **NEGATIVE-MOMENTUM-DOMINATED** (the LINK/066 + LTC/067 + FIL/083 fingerprint, now at a reformed-selected symbol — which would FALSIFY the reform itself, a critical finding). The Phase 7.4 post-mortem MUST report the CRV ML IS Sharpe vs the trivial TS-mom IS Sharpe at the (5d/21d/50d) cells AND the per-regime decomposition (bear-localized edge confirmation).

#### FB1 (BUNDLE-layer falsifier; HARD at BUNDLE-003 assembly)
**Reject the CRV+incumbent pairing at BUNDLE-003** if rolling-90day median `corr(CRV_pred, X_pred) ≥ 0.50` for any incumbent X ∈ {DOT, ETH, BTC, AAVE}. This is NOT a /084 SPECIALIST blocker — it is a pre-registered constraint the BUNDLE-003 CONFIRMATION QR inherits. CRV is a DeFi-AMM token; the most likely co-mover is AAVE (DeFi-lending) — the predicted-signal correlation must be checked at assembly. If triggered, the CRV seat is `SPECIALIST-PROMISING-but-BUNDLE-CONTESTED`.

### 4.3 — Verdict matrix

| F1 | F2 | F3 | F4 | Classification | BUNDLE-003 seat? |
|---|---|---|---|---|---|
| PASS | PASS | PASS (binds) | PASS | **PROMISING-CRV** (feature + R-FADE both bind; ML beats trivial) | YES (candidate, PENDING FB1) |
| PASS | PASS | INERT-branch (a) | PASS | PROMISING-FEATURE-ONLY (R-FADE droppable) | YES with R-FADE disabled (PENDING FB1) |
| PASS | FAIL | any | PASS | NEGATIVE-INERT-FEATURE | NO (on this hypothesis) |
| PASS | any | any | FAIL | NEGATIVE-MOMENTUM-DOMINATED (reform-falsifying if at +0.069 symbol) | NO (ML adds nothing over momentum) |
| FAIL (R-FADE cause) | any | over-veto-branch (b) | any | NEGATIVE-R-FADE-OVERKILL | NO (R-FADE too aggressive at fade_z=2.0; do NOT re-tune — relabel) |
| FAIL (not R-FADE) | any | any | any | NEGATIVE-COHORT (CRV itself too thin) | NO |

---

## Section 6 — Risk Management Design (primitive table + fire-rate predictions)

The CRV specialist's active risk stack and the NEW R-FADE primitive, with IS-calibrated fire-rate predictions (Model A pattern + the CRV-only R-FADE). Predictions derived from the IS-only EDA (Section 2) and the LM Master Phase 4.5 cascade analysis. Per `feedback_risk_mitigation_design.md`.

| # | Primitive | CRV setting | Predicted IS fire-rate | Predicted OOS fire-rate | Regime coverage / rationale |
|---|---|---|---|---|---|
| R1 | Consecutive-SL cool-down | **DISABLED** | 0% | 0% | Model A pattern (matches ETH/064, BTC/065, AAVE/078, FIL/083); R1 CATALOG-CLOSED for SPECIALIST_mode (`f81cafc3`). |
| R2 | Drawdown-triggered position scaling | **DISABLED** | 0% | 0% | Model A pattern; R2 is Model E (DOT/063) only. Not introduced — keeps the CRV risk axis isolated to R-FADE. |
| R3 | OOD Mahalanobis gate (cutoff=0.70, 16 SI features, SHARED) | **ENABLED** | ~30% of candidate bars gated (70th-pct by construction) | **ELEVATED** in bear-OOS (CRV's hot vol + bear regime push more bars OOD) | Regime-defense vs OOS distribution shift; load-bearing given CRV's high monthly dispersion. The dominant secondary trade-count driver (with R-FADE). |
| R5 | Per-coin vol target (45-day rolling) | **ENABLED** | ~continuous (every trade sized by σ_target/σ̂); ≈full-coverage | same | vt_target_vol=0.3, vt_lookback_days=45, vt_min_scale=0.33, vt_max_scale=2.0. Matches /063/064/065/078/083. At CRV's hot NATR (p50 5.68%) R5 scales positions DOWN — partial defense against the vol-overshoot (Flag 3). |
| **R-FADE** | **OI-divergence fade gate (NEW; veto-outright; fade_z=2.0, col=oi_price_divergence_30)** | **eligible on 7.2% of bars (\|z\|>2.0); fires on the DISAGREE subset → realized veto rate predicted LOW (≈1–4% of entries)** | **UNKNOWN; \|z\|>2.0 frac may shift in bear-OOS** — the dominant INERT-vs-overkill risk (Flag 1) | Confidence-gate / veto semantics: when the model's direction OPPOSES a strong OI-divergence signal (\|z\|>2.0), the entry is vetoed (the 2.0–2.5 bucket is the only IS bucket where DISAGREE underperforms AGREE, by −35.2 bps). **NO re-calibration branch: fade_z=2.0 is FROZEN. If INERT → relabel PROMISING-FEATURE-ONLY; if over-veto → NEGATIVE-R-FADE-OVERKILL (do NOT re-tune).** |
| — | SL-hit rate (label-barrier, not a gate; reported for Flag 3) | ATR(2.9,1.45) | **predicted high (CRV NATR p50 5.68% rolling-30, hotter than bundle)** | **expected ≥ IS** | Phase 7.4 reports SL-hit rate + triple-barrier label mix (timeout/SL/TP). Informational; NO ATR change at this iteration. |

**Compound cascade prediction (LM Master Flag 1, the load-bearing risk)**: R3 (~30% gated) then R-FADE (≈1–4% of surviving entries vetoed at fade_z=2.0) compound sequentially. CRV OOS has 1,326 candidate bars — far healthier than FIL's thin pool — so the modal R-FADE concern is **INERT (too few vetoes to matter)**, NOT over-veto. The R-FADE-OFF control run (F3) is the diagnostic: if R-FADE-ON and R-FADE-OFF produce identical rosters, R-FADE is INERT (branch a → PROMISING-FEATURE-ONLY); if R-FADE-ON drops below 50 OOS while OFF clears it, R-FADE is over-aggressive (branch b → NEGATIVE-R-FADE-OVERKILL).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure (modal, pre-registered before the backtest is read): R-FADE is INERT.** At `fade_z=2.0`, only 7.2% of bars carry `|z|>2.0`, and the gate fires only on the DISAGREE subset of those (model direction opposing a strong OI-divergence signal). The realized veto rate is predicted at ≈1–4% of entries — quite possibly **0 trades changed vs the R-FADE-OFF control** (F3 branch a). In that case the iteration collapses to a clean single-feature test: VALID, but it must be relabeled PROMISING-FEATURE-ONLY (or NEGATIVE-INERT-FEATURE), NOT credited as a risk-primitive win. The R-FADE-OFF control + the `decision_log` `oi_divergence_fade_gate` event count make this DIAGNOSABLE rather than a black-box result. This is the LM Master's #1 flagged risk and is bigger than the feature itself.

**Second-most-plausible failure: NEGATIVE-MOMENTUM-DOMINATED at a reformed-selected symbol (F4) — the reform-falsifying outcome.** CRV's trivial baseline is near-zero (+0.069 min, +0.293 21d), so the bar is low. But if the depth-5 ML head STILL cannot clear +0.293, that would be a critical finding: it would mean the reformed selector (negative trivial baseline → ML headroom) is NOT sufficient — that even at a no-trend symbol the depth-5 head fails to extract edge. In metrics: CRV ML IS Sharpe ≤ +0.293, with the OI-divergence feature dispersed (no dominant signal) and per-regime decomposition showing no bear-localized edge. This would re-open the selector question, not just close the symbol.

**Third: edge is a single-month / single-regime accident, not generalization (Flag 2; the /083 lesson #4).** CRV's monthly Sharpe dispersion is very high (std 3.567); the headroom is bear-localized (−0.924). A "good IS Sharpe" carried by one or two bear-regime windows is NOT a repeatable edge. In metrics: IS Sharpe positive but per-regime/per-month decomposition shows the entire edge in ≤2 windows. The Phase 7.4 per-regime + monthly decomposition is the mandatory check (always decompose a regime-localized edge before crediting it). Gates that catch each: F3 (R-FADE-OFF control) for the INERT failure, F4 (TS-mom-beat + per-regime decomposition) for the momentum-dominated and accident failures.

---

## Section 8 — Pre-Registered MERGE / NO-MERGE Criteria (F-AXIS absolute bands)

Pre-registered BEFORE the backtest is read (frozen at this brief's commit SHA). The verdict is MECHANICAL against these bands — no post-hoc re-tuning (`feedback_no_cheating.md`). At the SPECIALIST EXPLORATION layer the operative gate is the F-AXIS band below (PROMISING / NEGATIVE for BUNDLE-003 candidacy); the absolute IS Sharpe > 1.0 / OOS Sharpe > 1.0 merge floors apply at BUNDLE-003 assembly time, not at /084 SPECIALIST.

### 8.1 — SPECIALIST candidacy bands (primary verdict)

| Band | Condition (mean IS Sharpe across 50 inner seeds) | Verdict | Action |
|---|---|---|---|
| **PROMISING-STRONG** | IS Sharpe ≥ +0.50 **AND** IS trades ≥ 50 **AND** OOS trades ≥ 50 **AND** F2/F3/F4 PASS | SPECIALIST-PROMISING-STRONG | CRV enters BUNDLE-003 candidate roster at HIGH confidence (PENDING FB1 pred-corr check); multi-outer-seed CONFIRMATION queued. |
| **PROMISING-TENTATIVE** | +0.20 ≤ IS Sharpe < +0.50 **AND** IS trades ≥ 50 **AND** OOS trades ≥ 50 **AND** F2/F4 PASS (F3 may be INERT → PROMISING-FEATURE-ONLY) | SPECIALIST-PROMISING-TENTATIVE | CRV enters BUNDLE-003 candidate roster at REDUCED confidence (PENDING FB1); basin-lottery vigilance determines whether multi-seed CONFIRMATION is required before inclusion. |
| **NEGATIVE** | IS Sharpe < +0.20 **OR** IS trades < 50 **OR** OOS trades < 50 **OR** F2 FAIL **OR** F4 FAIL **OR** R-FADE over-veto (F3 branch b) | SPECIALIST-NEGATIVE (subtype per Section 4.3 matrix) | CRV DROPPED from BUNDLE-003 candidate roster (subtype-specific). |

### 8.2 — Absolute HARD gates (any single failure → NO-MERGE-as-BUNDLE-003-seat)

| Gate | Threshold | Source |
|---|---|---|
| IS trades | ≥ 50 | `feedback_v1_trade_rate_floor_50_per_specialist.md` (F1) |
| OOS trades | ≥ 50 (30–49 → 7-seed re-validation; <30 → auto-reject) | `feedback_v1_trade_rate_floor_50_per_specialist.md` (F1) |
| Feature importance | ≥ 30 (or rank < 40 in ≥50% months) | LM Master Rec 1 (F2) |
| R-FADE marginal effect | binds non-trivially (F3 branch a → relabel PROMISING-FEATURE-ONLY) AND does not solely cause F1 breach (F3 branch b → NEGATIVE) | this brief (F3) |
| ML IS Sharpe vs trivial TS-mom | > +0.293 (21d) AND > +0.069 (min-horizon) | reformed selector (F4) |
| CRV/incumbent pred-corr (BUNDLE-003 layer) | < 0.50 median for co-inclusion | this brief (FB1) |

### 8.3 — BUNDLE-003 MERGE gates (inherited at assembly; informational here)
At BUNDLE-003 assembly time the standard v1 BUNDLE merge gates apply (NOT at /084 SPECIALIST): IS Sharpe > 1.0 AND OOS Sharpe > 1.0 (`feedback_sharpe_floor.md`); OOS/IS ratio ≥ 0.5; top-symbol OOS PnL ≤ 30% (CRV's accretion is the mechanism expected to pull BTC's 33.96% below 30% — Section 11.D); seed validation (mean Sharpe > 0, ≥7/10 profitable); pairwise-disjoint universe (Critic Check 16); backtest-live parity (Critic Check 15). Pre-registered so the next CONFIRMATION QR inherits them; /084 itself is gated on Section 8.1/8.2 only.

---

## Section 9 — Library Stack Declaration

The /084 SPECIALIST trains LightGBM via the shared `LightGbmStrategy` + Optuna search (v1-native ML stack). Versions pinned in the active `uv` environment:

| Library | Version | Role |
|---|---|---|
| Python | 3.13.x | Runtime |
| lightgbm | 4.6.0 | Specialist model head (`max_depth=5`, `num_leaves=31`, `use_missing=True` for the 5.5% IS-NaN on `oi_price_divergence_30`) |
| optuna | 4.8.0 | Hyperparameter search (30 trials, TPE sampler, `n_startup_trials=10`) |
| numpy | 2.2.x | Feature math, OI-price divergence z-score, R-FADE evaluation, EDA |
| pandas | 3.0.x | Kline / OI / feature-parquet I/O, walk-forward windowing, IS-only filtering |
| scikit-learn | 1.8.x | Mahalanobis covariance for R3 OOD gate; metrics |
| scipy | 1.17.x | Statistical helpers (z-score, percentile calibration in the EDA) |
| quantstats | 0.0.x | OOS tearsheet (optional reporting convention; Phase 7) |

**No new third-party dependencies introduced.** The NEW feature uses the existing `open_interest_v1.py` module (numpy/pandas only); the R-FADE gate uses only numpy. No `mlfinlab`/`mlfinpy`/`pypbo`/`fracdiff` in the v1 SPECIALIST path — DSR/PBO/PSR are CONFIRMATION/BUNDLE-layer informational metrics, not computed at the SPECIALIST EXPLORATION layer. Track isolation HARD: `open_interest_v1.py` has ZERO imports from `features_v2`/`features_v3`.

---

## Section 11 — Bundle Composition & Parity (forward-looking; SPECIALIST layer)

This iteration produces a SPECIALIST, not a BUNDLE. Section 11 pre-registers the constraints the CRV seat must satisfy at BUNDLE-003 assembly so the next CONFIRMATION QR inherits them.

### 11.A — Pairwise-disjoint universe (HARD; `feedback_v1_bundle_no_coin_overlap.md` Critic Check 16)
BUNDLE-003 (if CRV PROMISING) = {BTC, ETH, DOT, AAVE, **CRV**} — 5 pairwise-disjoint single-coin specialists. CRV ∩ {each incumbent} = ∅ (Section 0.6). Each coin owned by EXACTLY ONE component. The CRV seat owns `{CRVUSDT}` and only `{CRVUSDT}`; the R-FADE gate and `oi_price_divergence_30` feature are CRV-local (the feature is computed for all symbols but only CRV is traded by this specialist) and carry no cross-seat parity risk under symbol-routed dispatch.

### 11.B — Bundle weights IS-only (`feedback_v1_bundle_weight_is_only.md` Critic Check 17)
NO bundle-level weights (per the pure pairwise-disjoint union precedent at /071, /082): each specialist's per-trade `weight_factor` already encodes vol-targeting + risk-wrapper effects. The CRV seat introduces no allocation degree of freedom. Critic Check 17 N/A by triviality.

### 11.C — Backtest-live parity (HARD; `feedback_v1_backtest_live_parity_hard.md` Critic Check 15)
The BUNDLE-003 decision rule extends the BUNDLE-002 symbol-routed dispatch with one branch:
```python
def bundle_signal(symbol, t):
    if symbol == "DOTUSDT":  return spec_063.get_signal(symbol, t)
    if symbol == "ETHUSDT":  return spec_064.get_signal(symbol, t)
    if symbol == "BTCUSDT":  return spec_065.get_signal(symbol, t)
    if symbol == "AAVEUSDT": return spec_078.get_signal(symbol, t)
    if symbol == "CRVUSDT":  return spec_084.get_signal(symbol, t)  # NEW seat; R-FADE + 49-col stack CRV-local
    return None
```
Bit-identical in backtest (post-hoc trades.csv union) and at `live/engine.py:_tick` (per-symbol dispatch). No aggregation, no netting, no portfolio-level shared state. R-FADE fires inside `spec_084.get_signal` identically in backtest and live (it reads only the past-only `oi_price_divergence_30` feature, available in both contexts; verified stateless at `lgbm.py:1910-1993`). At BUNDLE-003 assembly, `engine.py:_initial_setup` must add `CRVUSDT` to the kline-fetch list (8h interval) AND `fetch-oi --symbols CRVUSDT` to the OI-cache refresh. Critic Check 15 is N/A at /084 EXPLORATION (no bundle assembly); verified at BUNDLE-003.

### 11.D — Concentration trajectory (informational)
At BUNDLE-002, top-symbol OOS concentration is **33.96%** (BTC) > 30% gate. Adding a 5th seat expands the denominator; if CRV contributes a non-trivial positive OOS PnL share, BTC's share is mechanically pulled toward the 25% equal-weight ceiling for N=5 and is expected to cross below the 30% gate for the first time. This is the structural reason the user directive prioritizes universe expansion. **Caveat (FB1)**: CRV is a DeFi-AMM token; if its PnL co-moves with AAVE (DeFi-lending) the denominator expansion is partly illusory for diversification — FB1 (Section 4) checks the predicted-signal correlation at assembly.

### 11.E — Snapshot-validity inheritance
Per `BASELINE_V1.md` §POST-CODE-REVIEW: the BUNDLE-002 anchor numbers are pre-fix snapshots; the post-fix delta (C2/H1, H5/H10, H8/H9) is in-flight. The CRV specialist run inherits whatever code state the QE uses at Phase 6; the brief cites BUNDLE-002 snapshot numbers as the anchor and acknowledges the post-fix delta is open. The CRV runner (`run_iteration_084.py`) is a thin dispatch wrapper and is NOT touched by the in-flight library fixes except insofar as it calls the shared `LightGbmStrategy`.

---

## Risk Mitigation (project-mandated section)

Per `feedback_risk_mitigation_design.md`, the CRV specialist's active risk stack and the NEW R-FADE primitive (full table with fire-rate predictions in Section 6):
- **R3 OOD Mahalanobis gate** (cutoff=0.70, 16 SI features) — inherited (Model A pattern). Simulated historical effect: identical to the ETH/BTC/AAVE/FIL seats (R3-only); ELEVATED OOS fire-rate expected in CRV's bear/hot-vol OOS regime, compounding with R-FADE.
- **R-FADE OI-divergence fade gate** (NEW; veto-outright; `fade_z=2.0`, `col=oi_price_divergence_30`) — IS-calibrated (Section 2.5-evidence: the 2.0–2.5 `|z|` bucket is the only IS bucket where DISAGREE underperforms AGREE, by −35.2 bps; support is thin and non-monotone, so the gate is the highest-variance element). Simulated historical IS effect: eligible on 7.2% of bars (`|z|>2.0`); fires on the DISAGREE subset → predicted realized veto ≈1–4% of entries (modal INERT risk). **fade_z=2.0 is FROZEN (anti-tuning, runner assertion); NO post-hoc re-calibration branch — if INERT relabel PROMISING-FEATURE-ONLY, if over-veto classify NEGATIVE-R-FADE-OVERKILL.**
- **R5 per-coin vol target** (45-day rolling, target_vol=0.3, min_scale=0.33) — inherited; at CRV's hot NATR (p50 5.68%) scales positions DOWN, partial defense against the Flag-3 vol-overshoot.
- **R1 / R2 DISABLED** for the CRV seat (Model A pattern; consistent with ETH/BTC/AAVE/FIL). Not introduced — keeps the CRV risk axis isolated to R-FADE.
- **Concentration cap**: enforced at the BUNDLE-003 layer (Section 11.D), not the SPECIALIST layer.

---

## Kill-Switch Criteria (mid-flight)
- CRV specialist run is the methodology-lock SPECIALIST budget (~5.5–8h projected); there is NO wall-clock kill-switch (matches /078, /083); overrun is documented in the engineering report, not killed.
- F1 breach detected mid-run via OOS trade count → complete the run (need the count for the verdict matrix), then classify per Section 4; the F3 R-FADE-OFF control isolates whether R-FADE is the sole cause (no fade_z re-tune — relabel/classify).
- Feature-importance artifact missing → QE must emit CRV walk-forward feature importance; without it F2 is unverifiable and the iteration cannot be classified (BLOCK-PENDING-FIX).
- R-FADE-OFF control run missing → F3 is unverifiable (the marginal R-FADE effect cannot be isolated); QE MUST run both R-FADE-ON and R-FADE-OFF CRV cells (BLOCK-PENDING-FIX).
