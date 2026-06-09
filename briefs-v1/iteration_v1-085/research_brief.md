# Iteration v1-085 — Research Brief

**Track**: v1 (refactored; SPECIALIST + BUNDLE methodology)
**Type**: SPECIALIST (single-coin) — `UNIUSDT`; fresh-alt MINE under the REFINED structure-gated selector; START of a NEW feature-engineering grind (4 features → ~10 over iterations)
**Anchor baseline**: BUNDLE-002 (`v0.v1-082`) — IS monthly Sharpe **+0.7157** / OOS monthly Sharpe **+1.0043** / 4-component union {BTC, ETH, DOT, AAVE}; top-symbol concentration 33.96% (BTC).
**User directive (2026-06-09)**: *"no more confirmation multi seed why are you still recommending this? let's keep the mining. learn from the mistakes. start a new feature engineering set. I don't accept to end now. get one coin and focus on it. start with 4 features, 10. grind a bit."*
**Methodology LOCKED**: 50 inner seeds (42..91) × 30 Optuna trials × specialist_mode × LightGBM; `max_depth=5` FIXED, `num_leaves=31` FIXED; outer seed=42 SPECIALIST budget. NEVER change. The "4 → 10" is the FEATURE-SET size on the stack (52 cols now), NOT seeds/trials.

This iteration is the **direct correction of the /084 mistake** AND the start of a new program. /084 (CRVUSDT) cratered (IS −2.4717, campaign-worst) because a near-zero trivial baseline (+0.069) was admitted as ML headroom when it was actually **pure noise** (case b) — the negative-trivial-baseline selector is NECESSARY but NOT SUFFICIENT. /085 applies the REFINED structure-gate (`feedback_v1_negative_trivial_baseline_selector`): GATE 1 (trivial ≤ +0.15) AND GATE 2 (probe IS Sharpe ≥ +0.30 PRIMARY; max feature-vs-LABEL |IC| ≥ 0.04 SECONDARY; autocorr ≥ 0.03 TERTIARY). UNI is the structure-gated pick — it passes GATE 1 with the **most-negative** trivial baseline in the eligible pool (−0.2485) and carries the **strongest measured autocorrelation structure** in the pool (mag 0.0843), but it is HONESTLY **GATE-2-WEAK** at the 48-col probe (probe −0.243; max feature-label IC 0.0393, a whisker below the secondary gate). The /085 bet is structural and falsifiable: the 48-col probe is BLIND to UNI's structure because `V1_FEATURE_COLUMNS_PRUNED` carries no 3-bar reversion coordinate and no vol-state z-feature; the 4 NEW features are engineered to supply exactly the coordinates the probe could not see. Per the user directive, multi-seed CONFIRMATION is **PERMANENTLY DROPPED** and never proposed again.

---

## Section 0 — Data Split Declaration (Foundation)

- **OOS_CUTOFF_DATE**: `2025-03-24` (IMMUTABLE sacred constant — never changes; `src/crypto_trade/config.py`, `OOS_CUTOFF_MS=1742774400000`).
- **training_months**: `24` (IMMUTABLE sacred constant — never changes).
- **IS window**: ends 2025-03-24; UNI listing 2020-09-18 → **4.51y of pre-OOS data** (`uni_prescreen_results.csv`: `is_years=4.511`, `n_bars≈4995` to OOS cutoff per the IS slice; full CSV 6213 rows incl. OOS). ≥4y data gate PASS.
- **OOS window**: 2025-03-24 → present (2026-06-09); UNI OOS extent ≈ **14.5 months** (`data/UNIUSDT/8h.csv` minus the IS slice).
- **Walk-forward embargo**: `train_end_ms = test_start_ms − embargo_ms` (commit `5566a69`; inherited bit-exactly from the /063→/064→/065→/078→/083→/084 SPECIALIST family).
- **Data freshness**: UNI 8h.csv present (6213 rows); QE re-fetches + regenerates the 52-col parquet before backtest (post-feature hash `c8b8e0a87abb280a` per runner docstring) — `feedback_data_staleness_per_worktree.md`.
- **Sacred constants HELD** per `feedback_training_window.md` + `feedback_no_cheating.md`: no shift, no extension, no trim, no peek. The OOS window is NEVER read during Phases 1–5.

All EDA scripts (`analysis/iteration_v1-085/uni_prescreen.py`, `probe_UNIUSDT.py`, and the eligible-pool sweep `structure_prescreen_*.py`) enforce `open_time < OOS_CUTOFF_MS` for ALL calibration statistics, with an explicit runtime leak assertion (`assert df["open_time"].max() < OOS_CUTOFF_MS`). No OOS file is opened to derive any threshold, IC, probe Sharpe, or feature parameter.

---

## Section 0.5 — Iteration Type Declaration & Cadence

- **TYPE**: **SPECIALIST** — NEW SYMBOL universe-extension (single-coin cohort `("UNIUSDT",)`); fresh-alt MINE.
- **Cycle-7 position**: SPECIALIST-MINE (6th NEW-SYMBOL universe-extension attempt; FIRST under the REFINED structure-gated selector that adds GATE 2 on top of GATE 1). It is also the START of a NEW feature-engineering set per the user directive — a 4-feature UNI-specific mean-reversion stack that will grind toward ~10 over subsequent UNI iterations.
- **Mining context**: under the cycle-6+7 per-symbol regime-specialist mandate (`feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md`), SPECIALIST iterations are single-symbol regime-specialist EXPLORATIONs; feature-engineering is MODAL; the same symbol may appear any number of times (the directive explicitly licenses "get one coin and focus on it… grind a bit"). Axis-family rotation is SUSPENDED; the binding discipline is symbol-cohort orthogonality + pairwise-disjointness vs the live BUNDLE-002 universe.
- **Wall-clock budget**: the methodology-lock spec (50 inner seeds × 30 trials × 24 months) is projected at **~5.5–8h** per the runner docstring — the SAME budget the /078/083/084 seats ran under (user-mandated SPECIALIST budget exceeds the default 2h EXPLORATION cap by design). QE monitors and reports wall-clock; there is NO mid-run wall-clock kill-switch (overrun documented, not killed). Per `feedback_split_engineer_dispatch.md` (>30min backtest), QE does setup-only, orchestrator launches detached, QE writes report.
- **NO MULTI-SEED CONFIRMATION** (user directive, HARD): multi-seed CONFIRMATION is PERMANENTLY DROPPED for this program. It is never proposed in this brief, in the verdict matrix, or as a Path Forward. The /085 verdict is adjudicated entirely at the single-outer-seed SPECIALIST layer with the 50-inner-seed ensemble as the variance control.
- **Verdict frame**: ranked relative to the BUNDLE-002 member IS Sharpe distribution (DOT/063 +1.32, ETH/064 +0.24, BTC/065 +0.07) and the fresh-mine prior set (ATOM/ICP NEGATIVE, FIL/083 −0.82, CRV/084 −2.47). UNI's operative prior is **structure-gated-WEAK** — the 48-col probe is −0.243, so the bet is that the 4 NEW features lift the realized specialist materially above the probe; modal IS Sharpe **+0.10** with very wide bands (Section 4).

---

## Section 0.6 — Architecture-Family Justification (v1-only)

- **Axis family**: `per-cohort-specialization-UNI` (NEW symbol cohort; NEW mean-reversion feature-family set under the per-symbol regime-specialist mandate).
- **Mandate context**: under `feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md`, the standard 5-family axis-rotation discipline is **SUSPENDED**. The relevant discipline is symbol-cohort orthogonality + pairwise-disjointness vs the live BUNDLE-002 universe.
- **Prior 5 SPECIALIST cohorts (running roster + recent attempts)**:
  - iter-v1/064: `per-cohort-specialization-ETH` (ETH specialist; BUNDLE-002 seat 2)
  - iter-v1/065: `per-cohort-specialization-BTC` (BTC specialist; BUNDLE-002 seat 3)
  - iter-v1/078: `per-cohort-specialization-AAVE` (AAVE specialist; BUNDLE-002 seat 4, PROMISING-TENTATIVE)
  - iter-v1/083: `per-cohort-specialization-FIL` (FIL specialist; NEGATIVE-MOMENTUM-DOMINATED; non-roster)
  - iter-v1/084: `per-cohort-specialization-CRV` (CRV specialist; NEGATIVE-MOMENTUM-DOMINATED catastrophic; non-roster)
- **Rotation status**: **VALID** — `UNIUSDT` ∉ {DOT, ETH, BTC, AAVE} (the four live BUNDLE-002 cohorts) and ∉ {LINK, LTC, ATOM, ICP, FIL, CRV} (ALREADY-FAILED) and ∉ `V1_EXCLUDED_SYMBOLS` {SOL, XRP, DOGE, NEAR, BCH, LDO, TRX, BNB}. UNI is a DeFi-AMM-DEX-governance narrative cluster, distinct from store-of-value (BTC) / L1-smart-contract (ETH) / L1-PoS-interop (DOT) / DeFi-lending (AAVE).
- **Pairwise-disjoint**: chosen `UNIUSDT` ∉ {DOT, ETH, BTC, AAVE} (HARD; Critic Check 16 PASS by construction at the SPECIALIST layer; re-verified at any future BUNDLE assembly).
- **One-sentence rationale**: UNI is the empirically-selected pick under the REFINED selector — it clears GATE 1 with the **most-negative** trivial-momentum baseline of all eligible-pool candidates (−0.2485 min-horizon) AND carries the **strongest** return-autocorrelation structure in the pool (mag 0.0843, a clean lag-3-NEGATIVE 1-day mean-reversion signature) — making it a volatility-regime / mean-reversion symbol, the diametric opposite of the FIL/083 clean-trend trap and a genuinely structure-anchored (not narrative) pick, even though it is honestly GATE-2-WEAK at the 48-col probe.

---

## Section 1 — Hypothesis

**A UNIUSDT LightGBM specialist, equipped with a NEW 4-feature UNI-specific mean-reversion set (`rev_extension_z_3`, `vol_state_z_natr_30`, `rev_halflife_50`, `rev_vol_gate_signed`) that supplies the 3-bar reversion + volatility-state coordinates the 48-col `V1_FEATURE_COLUMNS_PRUNED` is BLIND to, extracts a per-symbol IS edge that the 48-col probe (−0.243) and the trivial momentum rule (−0.2485, it whipsaws) cannot — because UNI's exploitable structure is volatility-regime-conditioned short-horizon mean-reversion, not directional momentum.** If true, the realized 52-col specialist IS Sharpe lifts MATERIALLY above the −0.243 probe and clears the F4 TS-mom-beat bar, the 4 reversion features bind (importance), and UNI becomes a candidate seat for a future bundle.

**The /084 → /085 correction (the load-bearing refinement):**

| Selector stage | /084 (CRV, FALSIFIED) | /085 (UNI, REFINED) |
|---|---|---|
| GATE 1 (trivial ≤ +0.15) | +0.069 PASS | **−0.2485 PASS (most negative in pool)** |
| GATE 2 PRIMARY (probe ≥ +0.30) | NOT RUN (the hole that let CRV through) | **−0.243 — FAIL at 48-col (honestly flagged)** |
| GATE 2 SECONDARY (max IC ≥ 0.04) | NOT MEASURED (ic_matrix was family-redundancy) | **0.0393 — WEAK (a whisker below; vol_bb_bandwidth)** |
| GATE 2 TERTIARY (autocorr ≥ 0.03) | NOT MEASURED | **0.0843 — strongest in pool (lag3=−0.0843)** |
| Structure verdict | case (b) pure noise → IS −2.47 | **WEAK-but-structure-anchored; bet = NEW features supply the missing coordinate** |

**Why this is NOT a CRV repeat (the honest distinction)**: CRV's autocorr was near-zero on ALL lags (lag1 −0.026, lag3 −0.024, lag7 −0.003 — choppy, no persistent kernel at any horizon → genuine no-structure). UNI's autocorr is **concentrated** at a single lag: lag3 = −0.0843 (the pool's strongest single-lag signal), with near-zero lag1 (−0.026) and lag7 (+0.0164). A single-lag-concentrated NEGATIVE autocorrelation IS a structure — a 3-bar (~1-day) mean-reversion kernel — whereas CRV's diffuse near-zero autocorr was the absence of one. The 48-col probe under-reads this because `V1_FEATURE_COLUMNS_PRUNED` carries `stat_autocorr_lag5` (the wrong lag) and `vol_natr_14` (the wrong window), neither of which is the lag-3 / natr-30 coordinate the screen flagged.

**PRE-REGISTERED RISK — GATE-2-WEAK is a genuine downside-tilted prior (the honest caveat)**: UNI does NOT clear GATE 2 PRIMARY (probe −0.243) or SECONDARY (IC 0.0393 < 0.04). This is the most important caveat in the iteration. The /084 lesson is explicit that a low/near-zero trivial baseline is necessary-not-sufficient; UNI clears the necessary condition decisively but the sufficiency condition (GATE 2) is WEAK. The whole bet rests on the NEW features supplying structure the probe could not see. If they do not, UNI is the second confirmed case (after CRV) that the locked architecture cannot extract edge from a structure-WEAK fresh alt — which would shift the burden of proof onto the architecture, not the selector. This is pre-registered HERE and hardwired into F4 (Section 4).

**Falsification frame**: the hypothesis is FALSE if (a) UNI fails the per-specialist trade floor (≥50 IS AND ≥50 OOS; F1), OR (b) the NEW reversion features are INERT (the 4 new features collectively contribute < 30 gain AND none ranks < 40/52 in ≥50% months — F2), OR (c) the realized 52-col IS Sharpe fails to lift materially above the −0.243 probe AND fails the TS-mom-beat bar (F3/F4). All are pre-registered HARD falsifiers in Section 4.

---

## Section 2 — IS-Only Evidence

All numbers below are produced by the committed IS-only scripts (reproducible from worktree root; every script enforces `open_time < OOS_CUTOFF_MS` with a runtime leak assertion):
- `analysis/iteration_v1-085/uni_prescreen.py` → `uni_prescreen_results.csv` — UNI GATE-1/GATE-2 structure screen (trivial-momentum, feature-vs-LABEL IC, autocorr).
- `analysis/iteration_v1-085/probe_UNIUSDT.py` → `probe_UNIUSDT_results.csv` — GATE-2 PRIMARY fast single-seed LightGBM probe (48-col stack, seed=42, n_trials=10).
- `analysis/iteration_v1-085/structure_prescreen_*.py` + `*_results.csv` — the eligible-pool sweep (MATIC, GRT, XLM, OP, ALGO, ETC) for selection context.

### 2.1 — The REFINED selector: GATE-1 + GATE-2 structure screen (the "learn from the mistakes" deliverable)

UNI structure profile (IS-only; from `uni_prescreen_results.csv`):

| Quantity | Value | Gate | Verdict |
|---|---:|---|---|
| Data (full / to-OOS) | 4.51y / 4.51y | ≥4y | PASS |
| Trivial momentum Sharpe — 5d | **−0.2485** | — | — |
| Trivial momentum Sharpe — 21d | +0.389 | — | — |
| Trivial momentum Sharpe — 50d | +0.3684 | — | — |
| **trivial_baseline_min (min-horizon)** | **−0.2485** | GATE 1 ≤ +0.15 | **PASS (most negative in pool)** |
| ic_ret_5d / ic_ret_21d / ic_rsi_14 | −0.0026 / +0.0092 / +0.0021 | — | **directional-momentum ICs DEAD** |
| ic_natr_30 | +0.0386 | — | vol-state cluster |
| **ic_vol_bb_bandwidth (max feature-label \|IC\|)** | **0.0393** | GATE 2 SECONDARY ≥ 0.04 | **FAIL (whisker below)** |
| **probe_is_monthly_sharpe (48-col LGBM, seed42, 10 trials)** | **−0.243** | GATE 2 PRIMARY ≥ +0.30 | **FAIL (honestly flagged)** |
| ac_lag1 / ac_lag3 / ac_lag7 | −0.026 / **−0.0843** / +0.0164 | — | **lag-3-NEGATIVE 1-day reversion** |
| **autocorr_mag (max\|.\|)** | **0.0843** | GATE 2 TERTIARY ≥ 0.03 | **PASS (strongest in pool)** |
| structure_signal (literal) | **WEAK** | — | GATE-2-WEAK |

**The honest read (this is the most important caveat in the iteration)**: UNI clears GATE 1 decisively (most-negative −0.2485) and GATE 2 TERTIARY decisively (autocorr 0.0843, the pool's strongest), but it does NOT clear GATE 2 PRIMARY (probe −0.243 < +0.30) nor GATE 2 SECONDARY (max IC 0.0393 < 0.04 by 0.0007). Per the /084 lesson, the probe is the load-bearing gate. UNI fails it on the 48-col stack. **The /085 thesis is explicitly that the 48-col probe is the WRONG instrument for UNI** — it lacks the lag-3 reversion coordinate (PRUNED carries `stat_autocorr_lag5`) and the natr-30 vol-state z-coordinate (PRUNED carries `vol_natr_14`). The screen says the signal concentrates in (1) vol-state (natr_30 IC 0.0386, vol_bb_bandwidth IC 0.0393) and (2) the lag-3 reversion (autocorr 0.0843); the 4 NEW features are built to supply precisely those two coordinates. This is the falsifiable structural bet — and the F-AXIS bands (Section 4) require the 52-col specialist to lift materially ABOVE the −0.243 probe for the bet to land.

### 2.2 — Eligible-pool selection context (why UNI, not another alt)

Eligible-pool sweep (`structure_prescreen_*_results.csv`; IS-only); GATE-1 + GATE-2 status:

| Symbol | data_y | trivial_min | GATE1 | max feature-label IC | autocorr_mag | probe IS Sharpe | structure_signal |
|---|---:|---:|---|---:|---:|---:|---|
| **UNIUSDT** | **4.51** | **−0.2485** | **PASS** | **0.0393** | **0.0843** | **−0.243** | **WEAK ← SELECTED** |
| GRTUSDT | 4.26 | +0.0824 | PASS | 0.0324 | 0.0748 | **−1.5658** | WEAK |
| ALGOUSDT | 4.77 | +0.242 | FAIL | 0.0298 | 0.0612 | — | WEAK |
| ETCUSDT | 5.18 | +0.350 | FAIL | 0.0589 | 0.0616 | — | MODERATE |
| XLMUSDT | 5.17 | +0.3685 | FAIL | 0.0768 | 0.0580 | −0.456 | NOISE (adjudicated) |
| OPUSDT | 2.81 | +0.162 | FAIL (<4y) | 0.0816 | 0.0365 | — | STRONG-literal/<4y |
| MATICUSDT | 3.89 | +0.549 | FAIL (<4y, no OOS) | 0.0517 | 0.0648 | — | MODERATE/<4y |

**UNI is the ONLY eligible-pool candidate that clears GATE 1 with a genuinely NEGATIVE trivial baseline AND has ≥4y data AND has the pool's strongest autocorrelation kernel.** GRT also clears GATE 1 (+0.0824 ≤ +0.15) but its probe craters (−1.5658) and its IC is lower (0.0324) — GRT is a clearer no-structure case. ETC (IC 0.0589 MODERATE) and XLM (IC 0.0768) have higher ICs but FAIL GATE 1 (positive trivial baselines +0.350 / +0.3685 → the FIL/CRV positive-baseline-trap risk) and XLM's probe (−0.456) adjudicates to NOISE despite a STRONG literal IC. OP/MATIC are disqualified at <4y data. The honest summary: **NO eligible-pool candidate cleared GATE 2 PRIMARY** (probe ≥ +0.30) at the 48-col stack — the entire reachable fresh-alt pool is GATE-2-WEAK-or-worse under the locked 48-col architecture. UNI is the BEST-AVAILABLE pick (most-negative GATE-1 + strongest structure kernel + ≥4y), and the /085 bet is that NEW UNI-specific features close the GATE-2 gap the off-the-shelf 48-col stack leaves open. This is the structure-gated mine the directive asked for — applied honestly, with the WEAK verdict stated, not hidden.

### 2.3 — The structure fingerprint: lag-3 reversion + vol-state concentration

UNI's exploitable structure (IS-only) is precisely characterized:
- **Directional momentum is DEAD**: ret_5d IC −0.0026, ret_21d IC +0.0092, rsi_14 IC +0.0021 — all near-zero. The trivial-momentum rule LOSES (min-horizon −0.2485, the most negative in the pool: UNI whipsaws). Any momentum-shaped feature would re-make the FIL/083 clean-trend mistake in reverse.
- **Signal concentrates in volatility STATE**: natr_30 |IC| 0.0386 and vol_bb_bandwidth_20 |IC| 0.0393 are the only two features near the 0.04 secondary gate.
- **Return autocorrelation is single-lag-concentrated and NEGATIVE at lag-3**: ac_lag3 = −0.0843 (pool-strongest), ac_lag1 = −0.026 (near-zero), ac_lag7 = +0.0164 (near-zero). A 3-bar (~1 day) mean-reversion signature — NOT directional persistence. This is the structural difference from CRV (which was near-zero on all lags = no kernel).

The exploitable edge, if any, is **conditioning entries on volatility STATE and fading short-horizon directional extension** — a regime / mean-reversion model, the diametric opposite of the FIL clean-trend trap and the CRV diffuse-noise case.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

- **Declaration**: **HIGH-RISK**.
- **Reason**: this iteration is a **NEW SYMBOL universe-substitution** (UNIUSDT has never been a training-objective for any v1 specialist) STACKED with a NEW 4-feature set (changes the feature-importance allocation surface across 4 new columns at once). Both are HIGH-RISK triggers under the v1 Section 2.5 rubric. The change alters Optuna's training-objective domain. The UNI-specific risk profile: a GATE-2-WEAK structure verdict (probe −0.243, max IC 0.0393), a regime-localized edge thesis (vol-conditioned reversion), and a NEW composed Category-2 feature (`rev_vol_gate_signed`) that mechanically correlates with its primitive.
- **Mitigation (HIGH-RISK; OPT-IN per v1 rule)**: **single-outer-seed=42 EXPLORATION** with 50-INNER-seed averaging (the load-bearing SPECIALIST architecture; the 50-seed inner ensemble is the variance control that makes single-outer-seed basin-lottery a non-issue — `feedback_v1_basin_lottery_vigilance.md` triggers, per-seed spread > 0.50 OR Jaccard < 0.40 OR Spearman ρ < 0.50, are reported at Phase 7.4 as telemetry). **Per the USER DIRECTIVE, multi-seed CONFIRMATION is PERMANENTLY DROPPED and is NOT the mitigation here.** The diary records the single-outer-seed choice and the OOS outcome. **Escalation clause**: recent HIGH-RISK single-seed SPECIALIST deltas are AAVE/076 −0.69, FIL/083 −0.82, CRV/084 −2.47 (three negatives, the last two catastrophic). UNI/085 is the FOURTH HIGH-RISK single-seed in this run. Per the v1 rule the escalation would mandate multi-seed — but the user has EXPLICITLY OVERRIDDEN multi-seed for this program; instead, a NEGATIVE UNI verdict triggers the diary's "burden of proof has shifted to the architecture" finding (the locked stack cannot extract fresh-alt edge), NOT a multi-seed re-run.
- **Attribution-entanglement acknowledgment**: 4 NEW feature columns stacked on a NEW symbol means a NEGATIVE verdict cannot cleanly separate which feature (if any) bound. The per-axis attribution plan is hardwired into Section 4: per-feature walk-forward importance isolates which of the 4 columns the tree used; the TS-mom-beat (F4) and probe-lift (F3) isolate whether the symbol+features beat the 48-col probe and the trivial rule. The user directive ("start a new feature engineering set… start with 4 features") explicitly sanctions the 4-feature stack as one experiment (the START of a grind), so single-axis-isolation across the 4 is RELAXED by directive; the attribution plan keeps the verdict interpretable for the /086 grind step.

---

## Section 3 — Proposed Changes

### 3.1 — Symbol (universe expansion)
- **ADD** `UNIUSDT` as a new single-coin specialist cohort. `V1_ITER085_UNIVERSE = ("UNIUSDT",)` (runner-level; pairwise-disjoint vs BUNDLE-002 {BTC, ETH, DOT, AAVE} per Section 0.6). Critic Check 16 PASS by construction at the SPECIALIST layer.

### 3.2 — Features (4 NEW columns; LOCAL 48 → 52; global PRUNED stays 48)
- **ADD** exactly 4 columns to a LOCAL set `V1_ITER085_FEATURE_COLUMNS = V1_FEATURE_COLUMNS_PRUNED + 4 = 52` (verified `len == 52`, asserted in `__init__.py:242`). **The global `V1_FEATURE_COLUMNS_PRUNED` STAYS at 48** (asserted `len == 48` at `__init__.py:213`) — this preserves the /084-discipline (LOCAL-only) so DOT/ETH/BTC/AAVE/CRV specialists are UNAFFECTED (one-variable-at-a-time). The 4 columns are alphabetically ordered in the tuple: `rev_extension_z_3`, `rev_halflife_50`, `rev_vol_gate_signed`, `vol_state_z_natr_30`. This is the START of the feature grind: /086 may ADD up to ~6 more (toward ~10) WITHOUT redundancy because the 4 here claim the signal / state / speed / interaction quadrants.

The 4 features form an **orthogonal decomposition** of UNI's measured structure (volatility-regime + 3-bar mean-reversion), explicitly NOT momentum-persistence. All landed in `src/crypto_trade/features_v1/` (verified present); all past-only via `.shift(1)`; all clipped [−5,+5]:

| # | Feature | Module / func | Definition (past-only) | Warmup NaN | Quadrant | Predicted rank /52 |
|---|---|---|---|---:|---|---|
| 1 | **`rev_extension_z_3`** | `mean_reversion_v1.py::compute_rev_extension_z_3` | `ret_3 = log(close).diff(3)`; `z = (ret_3 − rmean_50(ret_3)) / rstd_50(ret_3)`; **sign-flipped** `rev_extension_z_3 = (−z).shift(1)`. LEADING NEGATIVE SIGN load-bearing: ac_lag3 NEGATIVE → positive 3-bar extension predicts DOWN → flip so high=expect-bounce. | ~53 | DIRECTION (the reversion signal; UNI's strongest structure, ac_lag3=−0.0843) | 3–9 |
| 2 | **`vol_state_z_natr_30`** | `volatility_v1.py::compute_vol_state_z_natr_30` | `natr_30` (30-bar NATR — the window the screen flagged); `z = (natr_30 − rmean_90(natr_30)) / rstd_90(natr_30)`; `.shift(1)`. Stationarizes the raw NATR level (drifts with regime) → "how unusual is current vol vs recent history". | ~120 | STATE (the regime conditioner; natr_30 \|IC\|=0.0386) | 2–7 |
| 3 | **`rev_halflife_50`** | `composed_v1.py::compute_rev_halflife_50` | Trailing-50-bar AR(1) `phi` = lag-1 corr of 1-bar log returns (`np.corrcoef`, ≥5 obs, std-guarded); `half_life = ln(0.5)/ln(\|phi\|)` for `0<\|phi\|<1` else cap=50; `z` over trailing-90; `.shift(1)`. | ~140 | SPEED (fast-oscillating tradeable regime vs slow chop; new kernel — no reversion-speed feature in v1) | 6–12 |
| 4 | **`rev_vol_gate_signed`** | `composed_v1.py::compute_rev_vol_gate_signed` | `g = 1` when `vol_state_z_natr_30 ≤ 0`; soft linear ramp 1→0 over `(0, +1.0]`; `g = 0` when `> +1.0`; `rev_vol_gate_signed = rev_extension_z_3 × g`. Passes reversion at full strength in compressed-vol (range) regimes; damps to zero in vol-expansion (breakout) regimes. | ~120 | INTERACTION (Category-2 composed capstone; diametric inverse of `regime_momentum_signed_5d`) | 4–10 |

- **Category-2 note (`rev_vol_gate_signed`)**: this feature mechanically correlates with `rev_extension_z_3` by construction (predicted \|IC\| 0.6–0.8). Per `feedback_v3_engineered_feature_pivot.md` the strict \|IC\|<0.50 redundancy gate is INAPPROPRIATE for composed features; the falsifier is importance ≥ 30 gain AND Sharpe-Δ, NOT raw IC. The honest test: does the GATED signal beat the UNGATED `rev_extension_z_3` on IS Sharpe? If yes → vol-regime conditioning is real edge; if the gate is INERT (tree splits on the ungated column and ignores the gated one) → UNI's reversion is NOT regime-conditional and /086 drops this and explores a different gate.
- **Stacking caveat (`feedback_v3_engineered_features_dont_stack`)**: stacking 4 features at once (rather than ONE) is a known risk — engineered features don't stack linearly at single-seed. This is RELAXED by user directive ("start with 4 features"); the per-feature importance attribution (F2) and the gated-vs-ungated test isolate which feature actually bound, feeding the /086 grind decision.
- **Parquet regen**: UNIUSDT parquet regenerated to 52 cols (post-feature hash `c8b8e0a87abb280a` per runner docstring); other symbols UNCHANGED.
- **Track-isolated**: `mean_reversion_v1.py` / `volatility_v1.py` / `composed_v1.py` have ZERO imports from `features_v2` / `features_v3` (Critic Phase 6.0 grep PASS).

### 3.3 — Risk (NO new risk primitive)
- **NO new risk gate this iteration.** Unlike /084 (which stacked R-FADE), /085 isolates the experiment to symbol + 4 features. The reversion-vs-momentum and vol-regime conditioning are encoded in the FEATURES (especially `rev_vol_gate_signed`), not in a post-aggregator risk gate. This keeps the attribution clean (the 4-feature verdict is not confounded by a gate) and matches the directive's "start a new feature engineering set" framing (feature work, not risk work). The inherited risk stack (R3 OOD, R5 vol-target; R1/R2 DISABLED — Model A pattern) is unchanged.

### 3.4 — Methodology (LOCKED per user directive)
- 50 inner seeds (42..91) × 30 Optuna trials × specialist_mode × LightGBM; `max_depth=5` FIXED, `num_leaves=31` FIXED; outer seed=42; ENSEMBLE_SIZE=1 per study (bagging at seed level); `n_startup_trials` per the shared search; `n_estimators` cap per the shared config.
- ATR TP/SL: `atr_tp=2.9 / atr_sl=1.45` (Model A ETH cell; vol-class match for UNI ~80–100% IS vol; kept at default to isolate the 4-feature effect; ATR tuning deferred to a follow-on if PROMISING — single-bit discipline).
- `training_months=24`, monthly retrain, `OOS_CUTOFF_DATE=2025-03-24` (sacred constants; unchanged).
- Walk-forward `train_end_ms = test_start_ms − embargo_ms` (the `5566a69` fix; unchanged).
- Aggregator: mean-of-signed-weights across 50 seeds; R3 OOD applied once (shared).
- **NO MULTI-SEED CONFIRMATION** (user directive, HARD). The "4 features → 10" grind is the FEATURE-SET size on the stack, NOT seeds/trials.

---

## Section 3.5 — LM Master (Phase 4.5) — Per-Recommendation Response

`briefs-v1/iteration_v1-085/lgbm_advisor.md` EXISTS (confidence **LOW-to-MEDIUM, lean LOW**; predicted UNI specialist IS Sharpe **+0.35**, range **+0.10 to +0.65**). The advisor is unusually adversarial — it explicitly REJECTS the directive's "GATE 1 + GATE 2 passed" framing and states the probe FAILED on the 48-col stack (GATE 2 PRIMARY −0.243, SECONDARY 0.0393 marginal-fail). The QR CONCURS fully with this honest reconciliation — it is the same WEAK verdict stated in Section 2.1. Each recommendation and risk flag is responded to below (adopt / modify / reject). Phase 5.5 gate verifies these responses are present.

#### Hyperparameter Recommendations

| LM Master HP item | QR response | Rationale |
|---|---|---|
| **Rec 1 — KEEP methodology fully LOCKED** (50 seeds × 30 trials × `max_depth=5` × `num_leaves=31`); any HP change confounds the feature verdict; `num_leaves=31` is at the soft cap `2^5−1`. | **ADOPTED** | Section 3.4 holds the lock exactly. The only variable under test is the 4-feature set. Required for comparability against the /063/064/065/078/083/084 roster. |
| **Rec 2 — Raise `min_data_in_leaf` floor to ~80–100** IF the runner exposes it (regularize against the 4-feature overfit on a shallow sub-gate IS surface); do NOT add the knob if absent. | **MODIFIED — DEFERRED to /086** | The methodology lock + single-bit discipline mean /085 does NOT modify the Optuna search space this iteration (adding a `min_data_in_leaf` floor is itself an HP-domain change that would confound the pure 4-feature verdict). Per the LM Master's own fallback ("if the runner does NOT expose this knob, do not add it… note it as the first lever to reach for in /086"), this is recorded as the **first /086 lever** if /085 lands IS-positive-but-overfit (IS/OOS ratio < 0.4 at 7.4). |
| **Rec 3 — Confirm `lambda_l1 > 0` is reachable** in the Optuna space (verify, don't change; L1 sparsity concentrates split budget on the 2–3 reversion coordinates). | **ADOPTED (verify-only)** | The standard v1 Optuna space includes `lambda_l1 ∈ [0, ~5]` (not pinned). QE confirms it is searchable at Phase 6; no change. This is the anti-diffuse-importance lever the LM Master flags as the CRV-fingerprint guard. |
| **Post-mortem — watch best-trial `n_estimators` pinning** in high-vol UNI cells (capacity signal). | **ADOPTED (as 7.4 telemetry)** | Phase 7.4 reports the best-trial `n_estimators` distribution across walk-forward months. Flag (NOT fix) if it pins at the cap. |

#### Feature-Engineering Recommendations (per-feature HARD rank falsifiers)

The LM Master ENDORSES the 4-feature SHAPE and pre-registers per-feature importance-rank predictions as HARD falsifiers (learned from /084 where it under-weighted its own flags). The QR ADOPTS all four predictions and HARDWIRES them into F2 (Section 4):

| LM Master per-feature prediction (HARD falsifier) | QR response | Where hardwired |
|---|---|---|
| **`rev_extension_z_3` — predict rank 1–4; "this feature's importance IS the experiment."** If rank 14+/52 INERT → the 3-bar reversion did not survive the triple-barrier label → leading single indicator the iteration failed. | **ADOPTED + HARDWIRED as F2-PRIMARY** | F2 (Section 4): `rev_extension_z_3` INERT (rank ≥ 14/52 in > 50% of UNI test months) is a STANDALONE HARD falsifier → NEGATIVE-INERT-FEATURE, regardless of headline Sharpe. |
| **`vol_state_z_natr_30` — predict rank 3–8** (regime conditioner; utility not primary). | **ADOPTED** | F2 utility-band; reported at 7.4. No standalone falsifier (conditioner role). |
| **`rev_halflife_50` — predict rank 6–12, HIGH instability** (std-of-rank > 3 expected on 8h bars); flag for /086 reconsideration if std-of-rank > 4. | **ADOPTED (as 7.4 telemetry)** | 7.4 reports the per-month rank std for `rev_halflife_50`; std > 4 → /086 reconsideration flag. Noisy-kernel expectation pre-registered (not a falsifier). |
| **`rev_vol_gate_signed` — predict rank 2–6 IF the other three are real; rank 1 = SUSPICIOUS.** If capstone rank 1 AND `rev_extension_z_3` rank 8+ → ANTI-SIGNAL (/084 fingerprint in a new coat), NOT confirmation. | **ADOPTED + HARDWIRED as F2-SUSPICION** | F2 SUSPICION branch (Section 4): `rev_vol_gate_signed` rank 1 WHILE `rev_extension_z_3` rank ≥ 8 → SUSPICIOUS-ANTI-SIGNAL → NOT a PROMISING tag; mandatory 7.4 WR-symmetry check. |
| **IC pre-warning**: `rev_vol_gate_signed` mechanically correlates with `rev_extension_z_3` (Category-2; expect high feature-vs-feature \|IC\|) — do NOT read \|IC\|>0.50 capstone-vs-primitive as redundancy failure (`feedback_v3_engineered_feature_pivot`); the feature-vs-LABEL IC (Critic Check 4) is the relevant test. | **ADOPTED** | Section 3.2 Category-2 note: the falsifier for the capstone is importance ≥ 30 gain AND Sharpe-Δ vs the ungated primitive, NOT raw feature-vs-feature IC. |

#### Saturation / Marginality Risks

| LM Master Risk | QR response | Rationale |
|---|---|---|
| **Risk A (DOMINANT) — the probe is sub-gate (−0.243) and the bet is that 4 NEW features flip it; NO precedent in the v1 win column** (DOT/ETH/BTC/AAVE all cleared structure on the STOCK stack; UNI is the first attempt to manufacture a pass via feature engineering on a probe-rejected coin). | **ADOPTED + HARDWIRED as F3** | F3 (Section 4) makes the probe-lift the load-bearing HARD falsifier: realized 52-col IS Sharpe must exceed the −0.243 probe by ≥ +0.25. Section 1 PRE-REGISTERED RISK + Section 7 modal-failure pre-register this as the most plausible outcome. The "burden has shifted to the architecture" finding is pre-wired into the F3-FAIL diary action. |
| **Risk B — IS-positive / OOS-negative quiet split** (model fits IS reversion timing that drifts OOS; 50-seed ensemble is NOT a guarantee — CRV's −2.47 was at the same lock); IS/OOS ratio < 0.4 is the tell. | **ADOPTED (as 7.4 telemetry)** | Phase 7.4 reports the IS/OOS Sharpe ratio; ratio < 0.4 is recorded as an overfit-drift tell and triggers the /086 `min_data_in_leaf` lever (Rec 2 deferral). |
| **Risk C — the ≥50 OOS trade floor** (UNI reversion entries may be sparse; selective `rev_vol_gate_signed` could push OOS below 50); pre-register expected OOS trade count. | **ADOPTED + PRE-REGISTERED** | Pre-registered expected OOS trade count in Section 4.1 (modal ~90–140 OOS entries, derived from UNI's ~14.5mo OOS pool × the R3+feature selectivity); F1 (Section 4) is the HARD floor. Note: `rev_vol_gate_signed` is a FEATURE (soft signal damp), NOT a hard veto gate, so it does not remove entries the way /084's R-FADE did — the F1 risk is lower than at /084. |

#### LM Master Falsifier Mandate (the "must NOT ignore" items)
- **"Pre-register `rev_extension_z_3`'s importance rank as a HARD falsifier BEFORE the run"** → DONE (F2-PRIMARY above; rank ≥14/52 in >50% months → NEGATIVE-INERT regardless of Sharpe).
- **"Pre-register the expected OOS trade count"** → DONE (Section 4.1: modal ~90–140 OOS; F1 floor ≥50).
- **"If the capstone dominates while primitives go quiet, that is anti-signal not a win"** → DONE (F2-SUSPICION above).

#### Optional Pre-flight (LM Master "highest-value optional", NOT mandated)
- The LM Master flags a single-seed n_trials=10 probe on the **52-col** stack (minutes, not hours) as the highest-value de-risking move: if the 52-col probe STILL prints negative, the feature engineering did not flip the structure and the full 50-seed run is a known-loss. **QR adopts this as an OPTIONAL Phase 6 pre-flight** the QE MAY run before the full 50-seed run; if the 52-col probe lands < −0.10 (i.e. no lift over the 48-col −0.243), QE flags it in the engineering report and the orchestrator MAY abort the full run early (a fail-fast on foreseeably-broken compute, in scope per the Prime Directive's narrow fail-fast clause). This is OPTIONAL, not a gate — the full 50-seed run is the adjudicator either way.

**No multi-seed CONFIRMATION is recommended or entertained** (user directive, HARD). The LM Master makes none.

---

## Section 4 — Expected OOS Impact + Falsifiers (HARD pre-registered)

### 4.1 — Predicted Sharpe delta + confidence band

| Metric | Modal prediction | 90% confidence band | Source |
|---|---:|---|---|
| **IS Sharpe (mean across 50 inner seeds)** | **+0.35** | [+0.10, +0.65] | LM Master Phase 4.5 (LOW-to-MEDIUM confidence; the 4 features must add ~+0.6 over the −0.243 probe to reach the gate — plausible-but-unproven) |
| **IS Sharpe lift vs 48-col probe (−0.243)** | **+0.59** | [+0.34, +0.89] | the load-bearing quantity: the bet IS that the 4 features lift the realized 52-col specialist materially above the probe |
| **IS Sharpe if 4 features INERT/near-INERT** | **≈ −0.10 to −0.25** | [−0.30, +0.00] | LM Master closing note (lands at roughly the probe → SPECIALIST-NEGATIVE) |
| **OOS Sharpe** | **≈ +0.05** | [−0.50, +0.55] | derived (regime-localized reversion edge → high OOS variance; GATE-2-WEAK prior tilts toward 0; Risk B IS/OOS-drift) |
| **OOS Sharpe Δ vs implicit single-coin baseline** | **≈ +0.05** | [−0.50, +0.55] | NEW SYMBOL → no prior UNI anchor; Δ measured vs the implicit `(UNIUSDT,)` cohort under the locked methodology |

**Mechanism breakdown (LM Master)**: the 48-col probe (−0.243) is the pre-registered floor — it shows the off-the-shelf stack cannot read UNI. The NEW features add edge ONLY IF the lag-3 reversion + vol-state coordinates are genuinely tradeable: `rev_extension_z_3` supplies the direction (the load-bearing column; modal +0.30 if it binds at rank 1–4), `vol_state_z_natr_30` + `rev_vol_gate_signed` supply the regime conditioning (modal +0.20 if the gate binds), `rev_halflife_50` is a conditioner (≈+0.00 alone, noisy on 8h bars, value is interaction). Net modal lift ~+0.59 → IS Sharpe ≈ +0.35 (LM Master modal). The LOW-to-MEDIUM confidence and the GATE-2-WEAK prior keep the honest downside live: if the features are INERT/near-INERT the specialist lands at roughly the probe (~−0.10 to −0.25) → SPECIALIST-NEGATIVE with the diary lesson "feature engineering could not manufacture a structure-gate pass on a sub-probe coin." This is NOT predicted to be a CRV-style catastrophe (UNI has a real lag-3 kernel + vol-anchored features → confidently-wrong-at-max-vol is less likely than CRV; no −2.47 crater expected).

**Predicted behavioral effect (per `feedback_axis_saturation_predictor.md`)**: the 4 reversion features SHOULD change the IS trade roster materially vs a 48-col baseline run — predicted **≥ 20% of IS entries change direction or timing** (the features encode fade-vs-follow, which inverts the directional decision on extended bars). Falsifier-tied: if < 10% of IS trades change vs a 48-col UNI control, the features are behaviorally INERT (F2 branch).

**Pre-registered expected trade counts (LM Master Risk C mandate)**: from UNI's ~14.5mo OOS candidate pool (~1,300+ 8h bars) × the R3 OOD gate (~30% gated) × the reversion-model entry selectivity, the modal expected count is **~90–140 OOS entries** and **~180–280 IS entries**. Critically, `rev_vol_gate_signed` is a FEATURE (a soft signal-damp the tree may or may not split on), NOT a hard veto gate — so unlike /084's R-FADE it does NOT mechanically remove entries; the F1 trade-floor risk is therefore LOWER than at /084. F1 (≥50 IS AND ≥50 OOS) is the HARD floor; an F1 breach here would be a model artifact (the tree refusing to trade), not gate-driven attrition.

**Hypothesis-rejection threshold (HARD)**: the PRIMARY hypothesis (UNI is a structure-anchored candidate seat) is REJECTED if ANY of F1–F4 below is breached. The OOS Sharpe is informational at the SPECIALIST EXPLORATION layer (IS is the strike adjudicator).

### 4.2 — Pre-registered HARD falsifiers (frozen at this brief's commit SHA)

#### F1 (HARD) — Trade-rate floor
**Falsified if** the UNI specialist produces **< 50 OOS trades** OR **< 50 IS trades**.
Per `feedback_v1_trade_rate_floor_50_per_specialist.md`: single-symbol specialist floor ≥50 (σ_SR ≈ 0.14 at N=50). 30–49 OOS → the seat is demoted (NO multi-seed re-validation per the user directive — instead the seat is held PROMISING-THIN and only used at a future bundle if the trade count is documented); <30 → auto-reject. UNI OOS has ~14.5 months of candidate bars — a healthy pool, so an F1 breach would be a model/feature artifact, not data-thinness.

#### F2 (HARD) — NEW features INERT or SUSPICIOUS (LM Master per-feature rank falsifiers)
Three sub-branches, all HARD, all pre-registered from the LM Master Phase 4.5 per-feature predictions:
- **F2-PRIMARY (the LM Master "this feature's importance IS the experiment" falsifier)**: **falsified if `rev_extension_z_3` is INERT** — ranks **≥ 14/52 in > 50% of UNI test months** (walk-forward-aggregated). `rev_extension_z_3` is UNI's strongest measured structure (autocorr_mag 0.0843) and the exact coordinate the 48-col stack misses (lag-5 not lag-3). If it does not bind, the 3-bar reversion did not survive the triple-barrier label → **NEGATIVE-INERT-FEATURE regardless of headline Sharpe** (the /084 lesson made concrete). Predicted rank 1–4.
- **F2-COLLECTIVE**: **falsified if** the 4 NEW features **collectively contribute < 30 gain** (summed, walk-forward-aggregated) AND **none ranks < 40/52 in > 50% of months** — the tree ignored all 4 → NEGATIVE-INERT-FEATURE. Drop after ONE verdict (`feedback_v3_inert_features_at_higher_budget.md`).
- **F2-SUSPICION (the LM Master anti-signal falsifier)**: **falsified if** `rev_vol_gate_signed` ranks **1/52 WHILE `rev_extension_z_3` ranks ≥ 8/52** (capstone dominates while the primitive it composes goes quiet) — the /084 fingerprint in a new coat (model leaning on a composed feature because it has nothing else). → **SUSPICIOUS-ANTI-SIGNAL, NOT a PROMISING tag**; mandatory per-month rank-stability + per-direction symmetric-WR check at 7.4 (the /084 anti-celebration rule) before any candidacy.

Phase 7.4 reports the full 52-feature walk-forward gain distribution + per-month rank for all 4 NEW features (incl. `rev_halflife_50` rank-std for the LM Master std>4 /086-reconsideration flag).

#### F3 (HARD) — No lift above the 48-col probe
**Falsified if** the realized 52-col UNI specialist IS Sharpe does **NOT exceed the 48-col probe baseline −0.243 by at least +0.25** (i.e. realized IS Sharpe < +0.00 with the NEW features). The probe is the pre-registered floor: the WHOLE thesis is that the NEW features supply structure the 48-col stack was blind to. If the 52-col specialist lands at or below the probe, the NEW features added no structure the off-the-shelf stack lacked → UNI is the second confirmed case (after CRV) that the locked architecture cannot extract fresh-alt edge → reclassify **NEGATIVE-PROBE-FLAT** and trigger the diary "burden of proof has shifted to the architecture" finding.

#### F4 (HARD) — Momentum/whipsaw-dominated (TS-mom-beat)
**Falsified if** the UNI ML IS Sharpe (mean across 50 inner seeds) does **NOT exceed the trivial min-horizon baseline −0.2485** by a margin that also clears **+0.00** absolute (i.e. ML IS Sharpe ≤ +0.00). UNI's trivial rule LOSES (−0.2485), so the ML head only has to beat ~0 to demonstrate it adds non-momentum edge; but if it cannot clear +0.00, the specialist is no better than not trading → reclassify **NEGATIVE-MOMENTUM-DOMINATED** (the LINK/066 + LTC/067 + FIL/083 + CRV/084 fingerprint, now at a structure-gated symbol — which would FALSIFY the refined selector's sufficiency a second time, a critical finding). Phase 7.4 MUST report the UNI ML IS Sharpe vs the trivial TS-mom at (5d/21d/50d) AND the per-direction win-rate symmetry check (the /084 anti-signal diagnostic: symmetric sub-50% WR in both directions = the model fit noise into a sign-rule).

#### FB1 (BUNDLE-layer falsifier; informational here)
**Reject the UNI+incumbent pairing at any future bundle** if rolling-90day median `corr(UNI_pred, X_pred) ≥ 0.50` for any incumbent X ∈ {DOT, ETH, BTC, AAVE}. UNI is a DeFi-AMM-DEX token; the most likely co-mover is AAVE (DeFi). NOT a /085 SPECIALIST blocker — a pre-registered constraint a future bundle QR inherits.

### 4.3 — Verdict matrix

| F1 | F2 | F3 | F4 | Classification | Future bundle seat? |
|---|---|---|---|---|---|
| PASS | PASS (features bind, not suspicious) | PASS (lift > +0.25 over probe) | PASS (IS > +0.00) | **PROMISING-UNI** (structure bet landed; reversion features bind) | YES (candidate; /086 grinds +6 features) |
| PASS | SUSPICION-branch | any | any | SUSPICIOUS-STRUCTURE-ABSENCE (rank 1–3 + diffuse) | NO until per-month stability + WR-symmetry clears |
| PASS | INERT-branch | any | any | NEGATIVE-INERT-FEATURE (reversion coords added nothing) | NO (drop the 4; /086 picks different features or different coin) |
| any | any | FAIL (probe-flat) | any | NEGATIVE-PROBE-FLAT (architecture cannot read UNI) | NO → diary "burden on architecture" finding |
| any | any | any | FAIL (IS ≤ +0.00) | NEGATIVE-MOMENTUM-DOMINATED (refined-selector sufficiency falsified again) | NO (critical selector finding) |
| FAIL | any | any | any | NEGATIVE-COHORT (UNI too thin — unlikely given ~14.5mo OOS) | NO |

---

## Section 6 — Risk Management Design (primitive table + fire-rate predictions)

Per `feedback_risk_mitigation_design.md`. /085 introduces **NO new risk primitive** (the reversion/regime logic is in the FEATURES, Section 3.3); the inherited Model-A risk stack is unchanged:

| # | Primitive | UNI setting | Predicted IS fire-rate | Predicted OOS fire-rate | Regime coverage / rationale |
|---|---|---|---|---|---|
| R1 | Consecutive-SL cool-down | **DISABLED** | 0% | 0% | Model A pattern (ETH/064, BTC/065, AAVE/078, FIL/083, CRV/084); R1 CATALOG-CLOSED for SPECIALIST_mode (`f81cafc3`). |
| R2 | Drawdown-triggered position scaling | **DISABLED** | 0% | 0% | Model A pattern; R2 is Model E (DOT/063) only. Not introduced — keeps the UNI axis isolated to the 4 features. |
| R3 | OOD Mahalanobis gate (cutoff=0.70, 16 SI features, SHARED) | **ENABLED** | ~30% of candidate bars gated (70th-pct by construction) | **ELEVATED** in UNI's hot-vol OOS regime | Regime-defense vs OOS distribution shift; load-bearing given UNI's hot NATR. The dominant trade-count driver. |
| R5 | Per-coin vol target (45-day rolling) | **ENABLED** | ~continuous (every trade sized by σ_target/σ̂) | same | vt_target_vol=0.3, vt_lookback_days=45, vt_min_scale=0.33, vt_max_scale=2.0. Matches /063/064/065/078/083/084. At UNI's hot NATR, R5 scales positions DOWN — partial vol-overshoot defense. |
| — | `rev_vol_gate_signed` (FEATURE-level soft vol-gate, not a risk gate) | active in the 52-col stack | ~continuous (soft ramp; damps reversion signal in vol-expansion) | same | The feature-encoded analogue of a regime gate: passes the reversion signal at full strength in compressed-vol (range) regimes and damps to zero in vol-expansion (breakout) regimes. Reported at 7.4 as a feature-effect, not a risk-fire-rate. |
| — | SL-hit rate (label-barrier, not a gate; reported for vol telemetry) | ATR(2.9,1.45) | predicted moderate–high (UNI hot vol) | expected ≥ IS | Phase 7.4 reports SL-hit rate + triple-barrier label mix. Informational; NO ATR change this iteration. |

**Simulated historical effect**: R3 (~30% gated) + R5 (continuous sizing) are the same stack as the proven ETH/BTC/AAVE seats; no NEW risk primitive means no new fire-rate to calibrate. The vol-regime conditioning is delivered through `rev_vol_gate_signed` at the feature layer — its effect is measured by the gated-vs-ungated IS Sharpe comparison (Section 3.2 honest test), not as a veto-rate.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure (modal, pre-registered before the backtest is read): NEGATIVE-PROBE-FLAT (F3) — the NEW features lift the −0.243 probe but not enough to clear +0.00.** UNI is GATE-2-WEAK (probe −0.243, IC 0.0393); the bet is that the 4 features close the gap, but the modal honest outcome is a partial lift (e.g. IS Sharpe −0.10 to +0.10) — structure-anchored but sub-floor. In metrics: realized 52-col IS Sharpe in [−0.10, +0.10], the 4 features bind at mid-table rank (F2 PASS), but the lift over the probe is < +0.25. This is NOT a CRV catastrophe — UNI has a real lag-3 kernel, so it should not blow up to −2.47; it should land "structure present but marginal." That outcome still advances the program: it confirms the structure-gate found a real-but-thin kernel and tells /086 whether to grind +6 more UNI features (if F2 binds) or pivot coin (if F3 fails clean).

**Second-most-plausible: NEGATIVE-INERT-FEATURE (F2 INERT branch).** The depth-5 tree on the 48-col stack already approximates the reversion via existing volatility/return columns, so the 4 NEW columns are redundant and the tree ignores them (collective gain < 30; < 10% of IS trades change vs a 48-col control). In metrics: the 4 reversion features rank ≥40/52 in most months; IS Sharpe ≈ the −0.243 probe. → drop the 4, /086 either re-engineers (different reversion encoding) or pivots.

**Third (the CRV-shadow, lower probability here): SUSPICIOUS-STRUCTURE-ABSENCE (F2 SUSPICION branch).** A reversion feature lands rank 1–3 with diffuse gain elsewhere AND the per-direction WR is symmetric sub-50% — the /084 fingerprint. UNI's single-lag-concentrated autocorr makes this LESS likely than for CRV (which had no kernel), but the F2 SUSPICION branch + the mandatory 7.4 WR-symmetry check are the guard. If it fires, the "structure" was noise-fitting, not the lag-3 kernel → treat as NEGATIVE, NOT a PROMISING tag.

Gates that catch each: F3 (probe-lift) for the marginal failure, F2 INERT for the redundant-feature failure, F2 SUSPICION + 7.4 WR-symmetry for the noise-fit failure, F4 + per-regime decomposition for the momentum/whipsaw failure.

---

## Section 8 — Pre-Registered MERGE / NO-MERGE Criteria (F-AXIS absolute bands)

Pre-registered BEFORE the backtest is read (frozen at this brief's commit SHA). The verdict is MECHANICAL against these bands — no post-hoc re-tuning (`feedback_no_cheating.md`). At the SPECIALIST EXPLORATION layer the operative gate is the F-AXIS band below; the absolute IS Sharpe > 1.0 / OOS Sharpe > 1.0 merge floors apply at any future bundle assembly, NOT at /085 SPECIALIST. **NO multi-seed CONFIRMATION is part of any band (user directive).**

### 8.1 — SPECIALIST candidacy bands (primary verdict)

| Band | Condition (mean IS Sharpe across 50 inner seeds) | Verdict | Action |
|---|---|---|---|
| **PROMISING-STRONG** | IS Sharpe ≥ +0.40 **AND** IS trades ≥ 50 **AND** OOS trades ≥ 50 **AND** F2/F3/F4 PASS | SPECIALIST-PROMISING-STRONG | UNI enters future-bundle candidate roster; /086 grinds +6 features (toward ~10) on the UNI cohort. |
| **PROMISING-TENTATIVE** | +0.10 ≤ IS Sharpe < +0.40 **AND** IS trades ≥ 50 **AND** OOS trades ≥ 50 **AND** F2 PASS **AND** F3 PASS (lift > +0.25 over probe) **AND** F4 PASS | SPECIALIST-PROMISING-TENTATIVE | UNI held at REDUCED confidence; /086 continues the UNI feature grind to push IS Sharpe toward the STRONG band. |
| **NEGATIVE** | IS Sharpe < +0.10 **OR** IS trades < 50 **OR** OOS trades < 50 **OR** F2 FAIL/SUSPICION-unresolved **OR** F3 FAIL **OR** F4 FAIL | SPECIALIST-NEGATIVE (subtype per Section 4.3 matrix) | UNI DROPPED from the candidate roster (subtype-specific); /086 either re-engineers UNI features or pivots coin per the structure-gate. |

### 8.2 — Absolute HARD gates (any single failure → NO-seat)

| Gate | Threshold | Source |
|---|---|---|
| IS trades | ≥ 50 | `feedback_v1_trade_rate_floor_50_per_specialist.md` (F1) |
| OOS trades | ≥ 50 (30–49 → PROMISING-THIN, documented; <30 → auto-reject) | `feedback_v1_trade_rate_floor_50_per_specialist.md` (F1) |
| NEW-feature collective importance | ≥ 30 gain (or ≥1 of 4 ranks <40 in ≥50% months); rank 1–3 + diffuse → SUSPICION | LM Master /084 lesson #2 (F2) |
| Probe lift | realized 52-col IS Sharpe > probe (−0.243) + 0.25 | this brief (F3) |
| ML IS Sharpe vs trivial | > +0.00 absolute AND > trivial min-horizon (−0.2485) | refined selector (F4) |

### 8.3 — Future-bundle MERGE gates (inherited at assembly; informational here)
At any future bundle assembly the standard v1 BUNDLE merge gates apply (NOT at /085 SPECIALIST): IS Sharpe > 1.0 AND OOS Sharpe > 1.0 (`feedback_sharpe_floor.md`); OOS/IS ratio ≥ 0.5; top-symbol OOS PnL ≤ 30% (a UNI seat expands the BUNDLE-002 denominator, pulling BTC's 33.96% toward the gate); pairwise-disjoint universe (Critic Check 16); backtest-live parity (Critic Check 15). Pre-registered so the next bundle QR inherits them; /085 itself is gated on Section 8.1/8.2 only. **NO multi-seed CONFIRMATION is required or proposed (user directive).**

---

## Section 9 — Library Stack Declaration

The /085 SPECIALIST trains LightGBM via the shared `LightGbmStrategy` + Optuna search (v1-native ML stack). Versions pinned in the active `uv` environment:

| Library | Version | Role |
|---|---|---|
| Python | 3.13.x | Runtime |
| lightgbm | 4.6.0 | Specialist model head (`max_depth=5`, `num_leaves=31`, `use_missing=True` for the warmup NaN on the 4 reversion features) |
| optuna | 4.8.0 | Hyperparameter search (30 trials, TPE sampler) |
| numpy | 2.2.x | Feature math (3-bar log-return z, AR(1) `np.corrcoef` half-life, NATR z, soft vol-gate ramp), R3 Mahalanobis, EDA |
| pandas | 3.0.x | Kline / feature-parquet I/O, rolling z-windows, walk-forward windowing, IS-only filtering |
| scikit-learn | 1.8.x | Mahalanobis covariance for R3 OOD gate; metrics |
| scipy | 1.17.x | `spearmanr` for the GATE-2 feature-vs-label IC screen; percentile calibration in the EDA |
| quantstats | 0.0.x | OOS tearsheet (optional reporting convention; Phase 7) |

**No new third-party dependencies introduced.** The 4 NEW features use the existing `mean_reversion_v1.py` / `volatility_v1.py` / `composed_v1.py` modules (numpy/pandas only). No `pyarrow`-version change. DSR/PBO/PSR are bundle-layer informational metrics, NOT computed at the SPECIALIST EXPLORATION layer. Track isolation HARD: the 3 feature modules have ZERO imports from `features_v2` / `features_v3`.

---

## Section 11 — Bundle Composition & Parity (forward-looking; SPECIALIST layer)

This iteration produces a SPECIALIST, not a bundle. Section 11 pre-registers the constraints a UNI seat must satisfy at any future bundle assembly so the next QR inherits them.

### 11.A — Pairwise-disjoint universe (HARD; `feedback_v1_bundle_no_coin_overlap.md` Critic Check 16)
A future bundle including UNI = {BTC, ETH, DOT, AAVE, **UNI**} would be 5 pairwise-disjoint single-coin specialists. UNI ∩ {each incumbent} = ∅ (Section 0.6). The UNI seat owns `{UNIUSDT}` and only `{UNIUSDT}`; the 4 reversion features and the 52-col stack are UNI-LOCAL (computed for UNI's parquet only; global PRUNED stays 48) and carry no cross-seat parity risk under symbol-routed dispatch.

### 11.B — Bundle weights IS-only (`feedback_v1_bundle_weight_is_only.md` Critic Check 17)
NO bundle-level weights (per the pure pairwise-disjoint union precedent at /071, /082): each specialist's per-trade `weight_factor` encodes vol-targeting + risk-wrapper effects. The UNI seat introduces no allocation degree of freedom. Critic Check 17 N/A by triviality.

### 11.C — Backtest-live parity (HARD; `feedback_v1_backtest_live_parity_hard.md` Critic Check 15)
A future bundle decision rule extends the BUNDLE-002 symbol-routed dispatch with one branch (`if symbol == "UNIUSDT": return spec_085.get_signal(symbol, t)`). Bit-identical in backtest (post-hoc trades.csv union) and at `live/engine.py:_tick` (per-symbol dispatch). No aggregation, no netting, no shared portfolio state. The 4 reversion features read only past-only `.shift(1)` values (available in both backtest and live), so they are parity-clean; there is no R-FADE-style stateful gate. At assembly, `engine.py:_initial_setup` must add `UNIUSDT` to the 8h kline-fetch list and regenerate the 52-col UNI parquet. Critic Check 15 is N/A at /085 EXPLORATION (no bundle assembly); verified at assembly.

### 11.D — Concentration trajectory (informational)
At BUNDLE-002, top-symbol OOS concentration is **33.96%** (BTC) > 30% gate. A 5th seat expands the denominator; if UNI contributes a non-trivial positive OOS PnL share, BTC's share is mechanically pulled toward the 25% equal-weight ceiling for N=5 and is expected to cross below the 30% gate. **Caveat (FB1)**: UNI is a DeFi-AMM token; if its PnL co-moves with AAVE (DeFi-lending) the denominator expansion is partly illusory for diversification — FB1 (Section 4) checks the predicted-signal correlation at assembly.

### 11.E — Snapshot-validity inheritance
Per `BASELINE_V1.md` §POST-CODE-REVIEW: the BUNDLE-002 anchor numbers are pre-fix snapshots; the post-fix delta (C2/H1, H5/H10, H8/H9) is in-flight. The UNI specialist run inherits whatever code state the QE uses at Phase 6; the brief cites BUNDLE-002 snapshot numbers as the anchor and acknowledges the post-fix delta is open. The UNI runner (`run_iteration_085.py`) is a thin dispatch wrapper and is NOT touched by the in-flight library fixes except insofar as it calls the shared `LightGbmStrategy`.

---

## Risk Mitigation (project-mandated section)

Per `feedback_risk_mitigation_design.md`, the UNI specialist's active risk stack (full table with fire-rate predictions in Section 6):
- **R3 OOD Mahalanobis gate** (cutoff=0.70, 16 SI features) — inherited (Model A pattern). Simulated historical effect: identical to the ETH/BTC/AAVE/FIL/CRV seats (R3-only); ELEVATED OOS fire-rate expected in UNI's hot-vol OOS regime.
- **R5 per-coin vol target** (45-day rolling, target_vol=0.3, min_scale=0.33) — inherited; at UNI's hot NATR scales positions DOWN, partial vol-overshoot defense.
- **NO new risk primitive** — the reversion/regime conditioning is delivered at the FEATURE layer (`rev_vol_gate_signed`), keeping the 4-feature verdict unconfounded by a gate.
- **R1 / R2 DISABLED** for the UNI seat (Model A pattern). Not introduced — keeps the UNI axis isolated to the 4 features.
- **Concentration cap**: enforced at the bundle layer (Section 11.D), not the SPECIALIST layer.

---

## Kill-Switch Criteria (mid-flight)
- UNI specialist run is the methodology-lock SPECIALIST budget (~5.5–8h projected); there is NO wall-clock kill-switch (matches /078/083/084); overrun is documented in the engineering report, not killed.
- F1 breach detected mid-run via OOS trade count → complete the run (need the count for the verdict matrix), then classify per Section 4.
- Feature-importance artifact missing → QE must emit the UNI walk-forward feature importance for all 52 columns; without it F2 is unverifiable and the iteration cannot be classified (BLOCK-PENDING-FIX).
- 48-col probe-lift unverifiable → the −0.243 probe is the pre-registered F3 floor (`probe_UNIUSDT_results.csv`); the realized 52-col IS Sharpe is compared against it directly (no extra control run needed).
- **NO multi-seed re-run is ever triggered** (user directive). A NEGATIVE verdict is classified per Section 4.3 and recorded; if F3 fails clean, the diary records the "burden of proof has shifted to the architecture" finding.
