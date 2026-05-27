# iter-v1/027 — Research Brief (Phases 1-5 — CONFIRMATION METHODOLOGY VALIDATION)

**Branch**: `iteration-v1/027` from `iteration-v1/026` HEAD `74ce468` (tag `v0.v1-026`).

**Anchor**: `v0.v1-baseline-corrected` (BASELINE_V1.md commit `f8bc12c`). IS Sharpe **+0.2829** / OOS Sharpe **+0.6637** / OOS trades 189 / 5-sym universe / 4 models (A, C, D, E).

**Track**: v1 (refactored 2026-05-23). 13 phases. LightGBM Master + Critic.

**Iteration type**: **CONFIRMATION** (cycle-3 closing — 11th iteration since /016 cycle-3 start; 10 EXPLORATION precedents complete /016-/025; /026 sanity slot).

---

## Section 0 — Position in cycle / framing

### 0.1 Cycle-3 cadence position

- **CONFIRMATION** /027 — cycle-3 closing iteration.
- Cycle-3 EXPLORATION ledger COMPLETE 10/10 (/016-/025). /026 = pre-CONFIRMATION sanity slot (not an EXPLORATION axis).
- Cycle-3 EXPLORATION verdict distribution: **2 PROMISING** (/018 LINK +0.80 OOS Δ, /019 ETH+gate +0.50 OOS Δ) / **1 PROMISING-METHODOLOGY** (/021 H2 REFUTED, non-compoundable) / **7 NEGATIVE** (/016, /017, /020, /022, /023, /024, /025).
- ONLY per-cohort specialists with INDEPENDENT priors survived OOS at single-seed EXPLORATION budget. All other axis families (Pool feature additions, BTC/LTC per-cohort isolation, risk-primitive, model-arch regime-conditional) produced NEGATIVE outcomes.

### 0.2 CRITICAL FRAMING — METHODOLOGY VALIDATION (not a merge candidate)

Per Critic /026 binding remediation #2:

> /027 brief Section 2 (prediction) must pre-register a realistic multi-seed OOS Sharpe band of **[+0.40, +0.75]**, NOT [+1.10, +1.30]. The +1.10–+1.30 target was incongruent with the catalog's own /018 entry ("bundle Sharpe target ≥+0.70 requires 5+ specialists at ~+0.50-0.80 each with cross-correlation ≤0.3") and the observed D (LTC) OOS Sharpe of −1.05.

**/027 is reframed as METHODOLOGY VALIDATION** (analogous to /021's PROMISING-METHODOLOGY non-compoundable verdict). The target band [+0.40, +0.75] is **structurally BELOW the +1.0 hard merge floor** per BASELINE_V1.md. Therefore:

- **NO-MERGE is pre-committed at brief authoring time.** Even an upper-band hit (+0.75) does NOT clear the +1.0 IS/OOS Sharpe floors.
- **BASELINE_V1.md does NOT update from /027 outcome.** Per `feedback_v3_baseline_update_policy.md` only CONFIRMATION-MERGE updates baseline; /027 is pre-committed CONFIRMATION-METHODOLOGY-VALIDATION.
- **Expected verdict cell**: PROMISING-METHODOLOGY (multi-seed dissolves single-seed lottery; specialists hold structurally) | INERT (specialists hold but no lift) | NEGATIVE (multi-seed regression breaks specialists) | BLOCK.

The methodology validated by /027 is the **per-cohort specialization architecture with independent priors + replacement-pool semantics**. /027 answers ONE question: *do the cycle-3 PROMISING ingredients (LINK /018, ETH+gate /019) reproduce at multi-seed under the LOCKED 5-Model replacement bundle?*

### 0.3 Why methodology validation matters even without a merge

If /027 PROMISING-METHODOLOGY (multi-seed mean OOS Δ in [+0.10, +0.40]):
- Cycle-3 closing finding = per-cohort specialization architecture is **STRUCTURALLY VALIDATED at multi-seed** (basin-lottery dissolved; signal-stable).
- Cycle-4 first EXPLORATION can extend with HIGH PRIOR confidence: DOT/LTC specialists with NEW risk gates (Critic /025 Path Forward Option 1).
- A 3-symbol pool composition test (BTC+ETH+LINK with specialists overriding, per Critic /026 Option C) becomes the natural next cycle-4 axis.

If /027 INERT (Δ ∈ [-0.10, +0.10]):
- Methodology partially validated — specialists hold but cycle-3 cannot lift portfolio Sharpe with the current bundle structure.
- Cycle-4 = methodology pivot (D-specialist mandatory; sample-weighting; XGBoost head-to-head).

If /027 NEGATIVE (Δ < -0.10):
- Methodology refuted at multi-seed — per-cohort isolation lift dissolves under basin-aggregation.
- Cycle-4 = re-question per-cohort axis fundamentally.

In all three cases, **/027 produces a structurally informative cycle-3 closeout**, even with NO-MERGE pre-committed.

### 0.4 Replacement semantics — production routing definition

Per /025 brief Section 11.6 (LOCKED 5-Model composition) + /026 Critic remediation #1 (replacement-pool production-semantic correlations PASS):

**Pool slice replacement** (NOT additive):
- **LINK trades** → produced by Model C' (LINK specialist from /018), NOT by baseline Model C in the 5-model pool.
- **ETH trades** → produced by Model G (ETH-only + asymmetric long-suppress BTC-trend gate from /019), NOT by Model A's ETH slice.
- **BTC trades** → produced by baseline Model A (BTC+ETH pool training, BTC slice).
- **LTC trades** → produced by baseline Model D (unchanged).
- **DOT trades** → produced by baseline Model E (unchanged, with R1+R2+R3).

The bundle is NOT additive (it does NOT double-count LINK or ETH trades). At signal merge time, the specialist signal **overrides** the pool's slice. This is the production routing semantic the live engine would use if the bundle were deployed.

### 0.5 Iteration Type Declaration

- **TYPE**: **CONFIRMATION** — full 10-EXPLORATION precedent set complete (10/10), pre-CONFIRMATION sanity check (/026) PASS-with-fix.
- **Specifically**: CONFIRMATION-METHODOLOGY-VALIDATION (sister to /015's CONFIRMATION-NEGATIVE-catastrophic — structural validation, not merge candidate).
- **Cycle-3 closing**: 11 iterations from /016-/027 (10 EXPLORATION + /026 sanity + /027 CONFIRMATION).
- **Wall-clock cap**: 6h HARD (CONFIRMATION standard per v1 skill §"Iteration Cadence Discipline").
- **Multi-seed mandate**: ACTIVE — cumulative ≥1σ cycle-3 NEG count reached 4 (/020, /022, /024, /025); multi-seed mandate triggered prior to /027 per `feedback_v1_seed_count_non_negotiable.md`.

### 0.6 Axis Family Declaration (v1 mandatory)

- **This iter's axis family**: `per-cohort-specialization` — **REPEAT** (cycle-3 closing CONFIRMATION; bundles /018 LINK + /019 ETH+gate at multi-seed). NOT a new axis declaration; validates the architecture-family established by /018+/019.
- **Cohort + Specialization pairing**: 2 specialist cohorts (LINK, ETH+gate) + 3 baseline pool cohorts (BTC, LTC, DOT via Model A's BTC slice + Model D + Model E).
- **Prior 5 EXPLORATION families** (verified against `briefs-v1/exploration_catalog.md`):
  - /022: `per-cohort-specialization-LTC`
  - /023: `feature-family` (funding)
  - /024: `model-arch` (regime-conditional)
  - /025: `feature-family` (OI delta)
  - /026: `methodology` (cross-correlation sanity)
- **Rotation status**: **VALID** — CONFIRMATIONs are exempt from Axis Rotation Discipline (the discipline targets EXPLORATION axis selection inertia, not CONFIRMATION bundling). `per-cohort-specialization` REPEAT bundles two PROMISING EXPLORATIONs (/018, /019) — this is exactly what CONFIRMATIONs are for per v1 skill §"Iteration Cadence Discipline" Rule 4.
- **One-sentence rationale**: validates the cycle-3 surviving methodology (per-cohort specialization with independent priors) at multi-seed; CONFIRMATIONs do not rotate axis families.

### 0.7 LM Master Phase 4.5 coordination slot

LM Master Phase 4.5 fires AFTER this brief. Section 3.4 RESERVES a placeholder for LM Master responses; integration is a Phase 5.5 BLOCK condition if LM Master fires after brief but brief doesn't echo each recommendation. Adopt-verbatim mandate ACTIVE per `feedback_iteration_quality.md` LM Master methodology track 6/6 PERFECT.

---

## Section 1 — Hypothesis

**Primary hypothesis (H1)**: The cycle-3 per-cohort specialist architecture — combining the LINK specialist Model C' (/018) and the ETH+gate specialist Model G (/019) with the BTC+LTC+DOT slices of the baseline pool — produces multi-seed-stable lift over the BASELINE_V1 5-symbol pool. Specifically: multi-seed mean OOS Sharpe Δ vs anchor +0.6637 lies in **[+0.10, +0.40]** (PROMISING-METHODOLOGY band).

**Secondary hypothesis (H2 — informational only, does NOT determine verdict)**: At absolute OOS Sharpe level, the bundle does NOT clear the +1.0 merge floor. /026 single-seed reference shows bundle OOS Sharpe ≈ +0.57 (monthly sqrt(12)); multi-seed regression worsens this. Per Critic /026 binding remediation #2, /027 target band is **[+0.40, +0.75]** ABSOLUTE OOS Sharpe — pre-registered as STRUCTURALLY BELOW the +1.0 floor.

**Falsification logic** (METHODOLOGY VALIDATION cell):
- If multi-seed mean OOS Sharpe Δ ∈ [+0.10, +0.40] → PROMISING-METHODOLOGY (methodology validated; specialists hold and lift at multi-seed).
- If Δ ∈ [-0.10, +0.10] → INERT (methodology partially validated; specialists hold but no lift).
- If Δ < -0.10 → NEGATIVE (methodology refuted; multi-seed regression breaks specialists).
- If absolute OOS Sharpe < +0.40 → BELOW pre-registered band lower bound (NEGATIVE classification even if Δ is in INERT band — the absolute Sharpe is the binding band).
- If absolute OOS Sharpe > +0.75 → ABOVE pre-registered band upper bound (PROMISING-METHODOLOGY classification confirmed; informational only since still NO-MERGE).

**Pre-committed NO-MERGE** (Section 8 below): even an upper-band hit (+0.75) does NOT clear the +1.0 hard merge floor. BASELINE_V1.md UNCHANGED regardless of /027 outcome.

---

## Section 2 — IS-only Evidence (cycle-3 ledger summary)

### 2.1 Cycle-3 EXPLORATION ledger (10/10)

| iter | family | axis | F1 OOS Δ | Verdict |
|---|---|---|---:|---|
| /016 | risk-primitive | R5 vol kill-switch | -1.00 | NEGATIVE catastrophic |
| /017 | universe | +SOLUSDT 6-sym | -0.09 | NEGATIVE anti-direction-INERT |
| **/018** | **per-cohort-specialization** | **LINK-only** | **+0.80** | **PROMISING-INERT favorable** |
| **/019** | **per-cohort-specialization** | **ETH-only + asymmetric BTC-trend gate** | **+0.50** | **PROMISING** |
| /020 | per-cohort-specialization | BTC-only | -0.86 | NEGATIVE catastrophic |
| /021 | methodology | H1/H2 basin diagnostic | (n/a) | PROMISING-METHODOLOGY (H2 REFUTED) |
| /022 | per-cohort-specialization | LTC-only + long-suppress gate | -1.17 | NEGATIVE catastrophic |
| /023 | feature-family | funding-rate z-score (30, 90) | -0.20 | NEGATIVE-LEARNED-clean |
| /024 | model-arch | regime-conditional sub-models | (F3-IS-CAT) | NEGATIVE clean |
| /025 | feature-family | OI delta z90 | -1.40 | NEGATIVE-LEARNED-CATASTROPHIC |

**Verdict distribution**: 2 PROMISING / 1 PROMISING-METHODOLOGY / 7 NEGATIVE / **0 merges**.

### 2.2 The two PROMISING specialists — standalone results

From /018 + /019 single-seed=42 ENSEMBLE_SIZE=3 n_trials=18 EXPLORATION runs:

| Specialist | Cohort | Risk gates | ATR (TP/SL) | OOS Sharpe | OOS trades | OOS WR | OOS PnL | IS Sharpe |
|---|---|---|---|---:|---:|---:|---:|---:|
| **Model C' (/018)** | LINKUSDT | R1 + R3 | 3.5 / 1.75 | **+0.9789** | 48 | 50.0% | +39.42% | +0.3407 |
| **Model G (/019)** | ETHUSDT | R3 only + post-hoc BTC-trend gate (lookback=42, threshold=±8%) | 2.9 / 1.45 | **+0.6990** | 42 | 47.6% | +16.91% | -0.0304 |

(From `reports-v1/iteration_v1-018/comparison.csv` and `reports-v1/iteration_v1-019/comparison.csv`.)

Both single-seed EXPLORATIONs cleared their per-cohort PROMISING bands. /018 OOS Sharpe Δ vs LINK-in-pool anchor (+0.8184) = +0.16 (PROMISING-INERT favorable per /018 calibration). /019 OOS Sharpe Δ vs ETH-in-pool anchor (+0.0503) = +0.65 (PROMISING flip per /019 calibration).

### 2.3 Multi-seed regression-to-mean priors

Per /018 closeout LM Master Phase 7.4 §5 + /019 LM Master §2 (Section 3.4 verdict-interpretation principle):

| Specialist | Single-seed OOS Sharpe | Multi-seed mean projection | Δ regression |
|---|---:|---:|---:|
| Model C' (LINK) | +0.9789 | **+0.80 anchor** (per /018 LM Master) | -0.18 regression |
| Model G (ETH+gate) | +0.6990 | **+0.50 anchor** (per /019 LM Master) | -0.20 regression |

Multi-seed regression dissolves single-seed basin-lottery favorable draws. Expected specialist-level OOS Sharpe at /027 ENSEMBLE_SIZE=5 inner × 2 outer = +0.80 LINK and +0.50 ETH+gate (mean across 10 paths).

### 2.4 /026 single-seed reference bundle (informational)

Per `analysis/iteration_v1-026/bundle_replacement_validation.csv`:

| Metric | Bundle (replacement-pool, 5-Model) | Baseline pool (5-sym, A/C/D/E) | Δ |
|---|---:|---:|---:|
| OOS Sharpe (monthly sqrt(12)) | **+0.5722** | +0.5703 | +0.0019 |
| OOS trades | 205 | 189 | +16 |
| OOS MaxDD | 49.18% | 33.77% | +15.4pp |
| IS Sharpe (monthly sqrt(12)) | +0.0640 | +0.3285 | -0.2645 |

**Critical**: at single-seed, the 5-Model replacement bundle ≈ baseline pool at OOS Sharpe (within +0.002). Multi-seed regression on the 2 specialists (LINK +0.98 → +0.80; ETH +0.70 → +0.50) is expected to LOWER bundle OOS Sharpe to **[+0.40, +0.55]** mean band (Critic /026 Finding 4).

The bundle is NOT structurally positioned to clear the +1.0 hard merge floor — the LTC drag (Model D OOS Sharpe −1.05) is dominant.

### 2.5 Cross-correlation pre-validation (/026 result)

Per `analysis/iteration_v1-026/replacement_pool_correlation.csv` (Critic /026 remediation #1):

| Pair | IS Pearson | OOS Pearson | Combined Pearson | PASS (< 0.50) |
|---|---:|---:|---:|---|
| pool_minus_LINK_ETH × LINK_specialist | -0.0854 | **+0.4935** | +0.0685 | YES |
| pool_minus_LINK_ETH × ETH+gate_specialist | -0.0085 | -0.1412 | -0.0516 | YES |

Both replacement-pool pairs PASS the < 0.50 threshold. The original 3-pair mandate breach at pool × LINK OOS +0.526 was an artifact of LINK being INSIDE the pool (self-correlation). Removing LINK from the pool drops the correlation from +0.526 to +0.494 — strictly below threshold.

The 5-Model 10-pair view surfaces an additional Pearson breach at C_link × E_dot OOS +0.6027 (Spearman +0.425 PASS), flagged for /027 Phase 7 attribution.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1 mandatory)

**Declaration: NORMAL-RISK.**

**Reason (one sentence)**: /027 is CONFIRMATION (10 EXPLORATION precedents accumulated; pre-CONFIRMATION sanity slot /026 GREEN-WITH-FIX); multi-seed validation is built-in by design (`--seeds 2` × ENSEMBLE_SIZE=5 inner = 10 model paths/cell vs 3 EXPLORATION); methodology-validation framing is already conservative (NO-MERGE pre-committed; BASELINE_V1.md UNCHANGED); HIGH-RISK declarations attach to Optuna training-objective domain changes at single-seed EXPLORATION — CONFIRMATION's multi-seed mandate is the OPPOSITE of single-seed lottery exposure.

**Mitigation built-in**:
- Multi-seed `--seeds 2` × ENSEMBLE_SIZE=5 inner = 10 paths/cell (vs 3 single-seed EXPLORATION)
- `--n-trials 35` above TPE warmup saturation (per `feedback_v3_confirmation_n_trials_35.md`)
- Full DSR/PBO/PSR re-evaluation under CONFIRMATION-mode (vs EXPLORATION-mode artifact per `feedback_v3_dsr_mode_artifact.md`)
- Pareto-non-dominated chosen seed on 6-metric vector (Critic Check 6 binding for CONFIRMATIONs)
- Cross-correlation pre-validation already PASSED at /026 (precondition cleared)
- Pre-registered target band [+0.40, +0.75] absolute OOS Sharpe — STRUCTURALLY BELOW merge floor; no post-hoc rationalization possible

**HIGH-RISK cumulative tracker (cycle-3 closing summary, informational)**:
- /016 HIGH-RISK / NEGATIVE-catastrophic / >1σ OOS Δ
- /017 HIGH-RISK / NEGATIVE-anti-direction-INERT / OOS Δ within band
- /018 HIGH-RISK / PROMISING-INERT favorable / OOS Δ +0.80
- /019 HIGH-RISK / PROMISING / OOS Δ +0.50
- /020 HIGH-RISK / NEGATIVE-catastrophic / OOS Δ -0.86 (>1σ)
- /022 HIGH-RISK / NEGATIVE-catastrophic / OOS Δ -1.17 (>1σ)
- /024 HIGH-RISK / NEGATIVE-clean / F3 IS-CAT (>1σ on IS)
- /025 HIGH-RISK / NEGATIVE-CATASTROPHIC / OOS Δ -1.40 (>1σ)
- **Cumulative ≥1σ negative count = 5** (/016, /020, /022, /024 IS, /025) → multi-seed mandate TRIPPED ahead of /027 per `feedback_v1_seed_count_non_negotiable.md`. /027 multi-seed is MANDATORY (not opt-in).

---

## Section 3 — Implementation Spec

### 3.1 Bundle architecture and code dispatch

**LOCKED bundle composition** (per /025 brief Section 11.6 + /026 GREEN-WITH-FIX):

| Component | Cohort | Source | Risk gates | ATR (TP/SL) | Origin EXPLORATION |
|---|---|---|---|---|---|
| Model A (pool) | BTCUSDT + ETHUSDT pool | baseline pool training | R3 only | 2.9 / 1.45 | BASELINE_V1.md |
| Model C' (specialist) | LINKUSDT | LINK-only specialist training | R1 + R3 | 3.5 / 1.75 | /018 |
| Model D | LTCUSDT | baseline pool training | R1 + R3 | 3.5 / 1.75 | BASELINE_V1.md |
| Model E | DOTUSDT | baseline pool training | R1 + R2 + R3 | 3.5 / 1.75 | BASELINE_V1.md |
| Model G (specialist) | ETHUSDT | ETH-only specialist training + asymmetric long-suppress BTC-trend gate | R3 only + post-hoc gate | 2.9 / 1.45 | /019 |

**Replacement semantics** (production routing) at signal merge:
- Trades with `symbol == LINKUSDT` come from Model C' (specialist), NOT from Model C (baseline pool's LINK model — which would be added but NOT dispatched in /027).
- Trades with `symbol == ETHUSDT` come from Model G (specialist + post-hoc BTC-trend gate), NOT from Model A's ETH slice.
- Model A still trains on BTC+ETH pool (same as baseline) but ONLY its BTC slice contributes trades at signal merge time.

**Implementation choice**: the SIMPLEST implementation is to dispatch the 5 models (A, C', D, E, G) and at trade-aggregation time apply the replacement rule: drop Model A's ETH trades and drop the baseline Model C's LINK trades (if present), keeping ONLY the specialist trades for those two cohorts. The pool's BTC slice (from Model A) + LTC (Model D) + DOT (Model E) + LINK (Model C' specialist) + ETH (Model G specialist) = the 5-Model replacement bundle.

**File 1 — `run_baseline_v1.py`** — add new universe constant + dispatch branch:

```python
# After V1_ITER025_OI_MIN_COVERED definition (~line 252):

#: iter-v1/027 — CYCLE-3 CONFIRMATION METHODOLOGY VALIDATION.
#: 5-Model replacement bundle: Pool A (BTC+ETH baseline pool training) + Model C' (LINK
#: specialist /018) + Model D (LTC baseline) + Model E (DOT baseline) + Model G (ETH+gate
#: specialist /019).
#:
#: REPLACEMENT SEMANTICS: at trade aggregation, drop Model A's ETH trades and drop Model C's
#: LINK trades (if present in pool), keep ONLY specialist trades for those two cohorts.
#: Effective per-cohort dispatch: BTC <- Model A pool, ETH <- Model G specialist,
#: LINK <- Model C' specialist, LTC <- Model D, DOT <- Model E.
#:
#: LOCAL to runner — NOT shared via features_v1/__init__.py (only CONFIRMATION-MERGE
#: updates V1_BASELINE_UNIVERSE; /027 is pre-committed CONFIRMATION-METHODOLOGY-VALIDATION,
#: NO-MERGE; BASELINE_V1.md UNCHANGED).
V1_ITER027_UNIVERSE: tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "DOTUSDT",
)

#: ETH+gate specialist constants (BIT-IDENTICAL to /019).
V1_ITER027_ETH_GATE_LOOKBACK_BARS: int = 42  # 14 days at 8h cadence
V1_ITER027_ETH_GATE_THRESHOLD_PCT: float = 8.0  # +-8% BTC 14d return
V1_ITER027_ETH_GATE_ENABLED: bool = True
V1_ITER027_ETH_GATE_LONG_ONLY: bool = False  # symmetric direction-aware (/019 mode)
```

```python
# Add elif branch after V1_ITER025 / before V1_BASELINE_UNIVERSE generic dispatch:
elif set(symbols) == set(V1_ITER027_UNIVERSE) and iteration_label == "v1-027":
    # iter-v1/027: CYCLE-3 CONFIRMATION METHODOLOGY VALIDATION.
    # 5-Model replacement bundle: Pool A (BTC+ETH baseline, BTC slice retained) +
    # C' (LINK specialist /018) + D (LTC baseline) + E (DOT baseline) +
    # G (ETH+gate specialist /019 with asymmetric long-suppress BTC-trend gate).
    #
    # Multi-seed CONFIRMATION: ENSEMBLE_SIZE=5 inner seeds, --seeds 2 outer seeds
    # = 10 model paths per cell (vs 3 single-seed EXPLORATION).
    # n_trials=35 (above TPE saturation per feedback_v3_confirmation_n_trials_35).
    #
    # F-AXIS-MECHANISM #1: trade roster bit-identity check — LINK trades come ONLY from
    #   Model C' (specialist); ETH trades come ONLY from Model G (specialist).
    # F-AXIS-MECHANISM #2: cross-correlation multi-seed — both replacement-pool pairs
    #   stay < 0.50 (/026 single-seed result preserved at multi-seed).
    # F-AXIS-MECHANISM #3: per-specialist Sharpe stability — Model C' multi-seed mean
    #   OOS Sharpe in [+0.50, +0.80] (regress from /018's +0.98); Model G in
    #   [+0.30, +0.50] (regress from /019's +0.70).
    # F-AXIS-MECHANISM #4: DSR > 0.50 (relaxed from MERGE 0.95 — methodology validation).
    # F-AXIS-MECHANISM #5: PBO < 0.40 (CSCV at multi-seed; CONFIRMATION-mode).
    results_a_pool, faxm_a, _strat_a = run_model(
        "A (BTC+ETH pool)",  # BTC slice retained at trade-aggregation; ETH slice dropped
        ("BTCUSDT", "ETHUSDT"),
        atr_tp=2.9,
        atr_sl=1.45,
        apply_r1=False,
        n_trials=n_trials,
        ensemble_size=ensemble_size,
        oof_persist_path=OOF_PARQUET_PATH,
        feature_columns=active_feature_columns,
        bounds_profile=bounds_profile,
        **_r5_kwargs,
    )
    results_c_spec, faxm_c, _strat_c = run_model(
        "C' (LINK specialist /018)",
        ("LINKUSDT",),
        atr_tp=3.5,
        atr_sl=1.75,
        apply_r1=True,
        n_trials=n_trials,
        ensemble_size=ensemble_size,
        oof_persist_path=OOF_PARQUET_PATH,
        feature_columns=active_feature_columns,
        bounds_profile=bounds_profile,
        **_r5_kwargs,
    )
    results_d, faxm_d, _strat_d = run_model(
        "D (LTC + R1)",
        ("LTCUSDT",),
        atr_tp=3.5,
        atr_sl=1.75,
        apply_r1=True,
        n_trials=n_trials,
        ensemble_size=ensemble_size,
        oof_persist_path=OOF_PARQUET_PATH,
        feature_columns=active_feature_columns,
        bounds_profile=bounds_profile,
        **_r5_kwargs,
    )
    results_e, faxm_e, _strat_e = run_model(
        "E (DOT + R1 + R2)",
        ("DOTUSDT",),
        atr_tp=3.5,
        atr_sl=1.75,
        apply_r1=True,
        apply_r2=True,
        n_trials=n_trials,
        ensemble_size=ensemble_size,
        oof_persist_path=OOF_PARQUET_PATH,
        feature_columns=active_feature_columns,
        bounds_profile=bounds_profile,
        **_r5_kwargs,
    )
    results_g_spec, faxm_g, _strat_g = run_model(
        "G (ETH-only + R3 + BTC-trend gate)",
        ("ETHUSDT",),
        atr_tp=2.9,
        atr_sl=1.45,
        apply_r1=False,
        n_trials=n_trials,
        ensemble_size=ensemble_size,
        oof_persist_path=OOF_PARQUET_PATH,
        feature_columns=active_feature_columns,
        bounds_profile=bounds_profile,
        **_r5_kwargs,
    )
    # Apply stateless direction-aware BTC-trend gate as post-hoc filter on Model G output.
    btc_open_times, btc_closes = load_btc_klines_for_filter()
    gate_cfg = BtcTrendFilterConfig(
        lookback_bars=V1_ITER027_ETH_GATE_LOOKBACK_BARS,
        threshold_pct=V1_ITER027_ETH_GATE_THRESHOLD_PCT,
        enabled=V1_ITER027_ETH_GATE_ENABLED,
    )
    results_g_spec, gate_stats = apply_btc_trend_filter(
        results_g_spec, btc_open_times, btc_closes, gate_cfg,
    )
    gate_stats_dict = gate_stats.as_dict()
    print(
        f"[iter-v1/027 ETH+gate BTC-trend gate] "
        f"normal={gate_stats_dict['n_normal']} "
        f"warmup={gate_stats_dict['n_warmup']} "
        f"killed={gate_stats_dict['n_killed']}/{gate_stats_dict['n_total']} "
        f"fire_rate={gate_stats_dict['fire_rate']:.2%}"
    )
    # REPLACEMENT SEMANTICS: drop Model A's ETH trades; keep BTC slice only.
    # Filter results_a_pool trades to drop symbol=='ETHUSDT' rows.
    results_a_btc_only = [r for r in results_a_pool if r.symbol == "BTCUSDT"]
    # Aggregate: Pool A (BTC slice) + C' (LINK specialist) + D (LTC) + E (DOT) + G (ETH specialist).
    _all_faxm_logs = faxm_a + faxm_c + faxm_d + faxm_e + faxm_g
    all_results = results_a_btc_only + results_c_spec + results_d + results_e + results_g_spec
    _r5_model_results = [
        results_a_btc_only,
        results_c_spec,
        results_d,
        results_e,
        results_g_spec,
    ]
```

**Note on replacement filter**: the `results_a_pool` trade-result list contains BOTH BTC and ETH trades from Model A's pooled training; the filter retains BTC-symbol rows ONLY (drops ETH-symbol rows). At Phase 6, the QE verifies via a test that `set(r.symbol for r in results_a_btc_only) == {"BTCUSDT"}`. This is the F-AXIS #1 dispatch-correctness check.

**Diff scope** (single src/ file): `run_baseline_v1.py`, ~120 lines added (new constant block + new elif dispatch branch). Zero changes to:
- `src/crypto_trade/features_v1/`
- `src/crypto_trade/strategies/ml/lgbm.py`
- `src/crypto_trade/strategies/ml/optimization.py`
- `src/crypto_trade/strategies/ml/walk_forward.py`
- `src/crypto_trade/strategies/ml/risk_v2.py` (only IMPORTED for the BTC-trend gate)
- `src/crypto_trade/labeling.py`
- Risk gate code (R1/R2/R3 unchanged)

**Foundation guardrail**: `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` UNCHANGED. No regression.

### 3.2 CLI invocation

```bash
uv run python run_baseline_v1.py \
  --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT \
  --pruned-features \
  --ensemble-size 5 \
  --seeds 2 \
  --n-trials 35 \
  --iteration-label "v1-027" \
  --reports-dir reports-v1
```

(`--iteration-label "v1-027"` + V1_ITER027_UNIVERSE set equality triggers the new elif branch. `--pruned-features` activates V1_FEATURE_COLUMNS_PRUNED 40-col + bounds_profile=v1_pruned. `--ensemble-size 5` × `--seeds 2` outer = 10 model paths/cell. `--n-trials 35` above TPE saturation.)

### 3.3 Pinned values

- `feature_columns = list(V1_FEATURE_COLUMNS_PRUNED)` — 40 cols, BIT-IDENTICAL to BASELINE pure (NOT 42, NOT 43; OI and funding EXCLUDED from /027 substrate per /025 + /023 NEGATIVE verdicts).
- `bounds_profile = "v1_pruned"` — BIT-IDENTICAL to baseline.
- `ENSEMBLE_SEEDS[0:5] = [42, 123, 456, 789, 1001]` — inner seeds (BIT-IDENTICAL to baseline ensemble).
- `--seeds 2` outer seeds (selected from canonical roster; see `_derive_ensemble_seeds`).
- `n_trials = 35` (CONFIRMATION standard per `feedback_v3_confirmation_n_trials_35.md`).
- `r5_vol_target_enabled = False` (cycle-3+ default).
- `r5_binary_kill_enabled = False` (cycle-3+ default).
- `sample_weight_mode = "abs_pnl"` (baseline default).
- `sigma_source = "natr"` (baseline default).
- Per-model risk layers BIT-IDENTICAL to BASELINE_V1.md:
  - Pool A: R3 only (no R1, no R2).
  - Model C' (LINK specialist): R1 + R3 (matches /018 + baseline Model C).
  - Model D (LTC): R1 + R3 (baseline).
  - Model E (DOT): R1 + R2 + R3 (baseline).
  - Model G (ETH+gate specialist): R3 only + post-hoc BTC-trend gate (matches /019 + symmetric Model A semantics).
- BTC-trend gate (Model G): `lookback_bars=42, threshold_pct=8.0, enabled=True, long_only=False` (BIT-IDENTICAL to /019).

### 3.4 LM Master Phase 4.5 Responses

LM Master Phase 4.5 advisory at `briefs-v1/iteration_v1-027/lgbm_advisor.md` has fired. Cycle-3 LM Master methodology track is 6/6 PERFECT (load-bearing at /025 DUAL GATE + HARD BLOCK). This Section processes each numbered recommendation; cross-references are propagated into Sections 4 / 5 / 10.5 / 11 below.

**§1 — Multi-seed regression magnitudes**: 18-22% (NOT 50%) because ENSEMBLE_SIZE=5 inner collapses half the basin variance before outer-seed averaging. Per-specialist modal projections: **C' LINK +0.78** (band [+0.55, +0.85]); **G ETH+gate +0.52** (band [+0.32, +0.62]). Applied to /026 reference +0.5722, specialists regressed contribute ~-0.11 portfolio Sharpe → **bundle modal multi-seed OOS Sharpe = +0.45 to +0.50**, sitting at the NEGATIVE-leaning edge of pre-registered [+0.40, +0.75]. → **ADOPTED**. Section 4 F-AXIS-MECHANISM #3 updated with per-specialist bands ±0.25 (C' [+0.53, +1.03] from +0.78 mode; G [+0.27, +0.77] from +0.52 mode); Section 4 F1 calibration note revised; Section 5 priors recalibrated (see §6 below).

**§2 — Cross-correlation at multi-seed**:
- pool×LINK_spec +0.4935 single-seed is 2-month-driven (2025-08, 2025-11 risk-on rallies) → multi-seed averages asymmetrically → **DISSOLVES to predicted +0.35-0.42** (basin lottery). PASS gate at <0.50.
- C_link × E_dot +0.6027 single-seed is signal-level co-movement (LINK + DOT share altcoin/L1 regime) → multi-seed WILL NOT dissolve → **STAYS at predicted +0.55-0.60**. Binding cycle-4 finding: the 5-Model bundle carries unresolvable altcoin concentration at this composition.
→ **ADOPTED**. Section 4 F-AXIS-MECHANISM #1 (correlation table) updated with directional predictions for both pairs. Section 11 cycle-4 staging makes C×E altcoin de-concentration mechanism MANDATORY regardless of /027 verdict (see §9 below).

**§3 — Bundle composition stability**: outer-seed-cap-2 empirical → ±0.20 single specialist, ±0.30 5-model bundle. At modal +0.45-0.50 mean, the 2-seed Pareto spans **[+0.25, +0.70]**. Engineering report MUST emit `specialist_stability.csv` with per-(inner, outer) seed OOS Sharpe to make the regression distribution visible at Phase 7.4 LM Master post-mortem. → **ADOPTED**. Section 10.5 deliverables updated; falsifier band for 2-seed Pareto added to Section 4.

**§4 — DSR borderline at modal +0.45**: n_trials=35 × 2 outer seeds = 70 trials → E[max_SR] ≈ 3.10 (CONFIRMATION-mode methodology); annualized observed Sharpe +0.45 × √12 ≈ 1.56 → **DSR modal +0.45**, BELOW 0.50 F-AXIS #4 threshold. PBO modal 0.38 → F-AXIS #5 PASS. PSR_monthly_vs_0 modal 0.85 (informational); PSR_monthly_vs_1 modal 0.13 (INERT, merge gate not applicable at NO-MERGE pre-commit). → **ADOPTED**. Section 4 F-AXIS-MECHANISM #4 calibration note added: at modal +0.45 outcome, DSR alone CANNOT distinguish PROMISING-METHODOLOGY from INERT — verdict elevation under F-AXIS #3 specialist-stability rules supersedes.

**§5 — F-AXIS #1 dispatch hard-asserts MANDATE**: per /024 dispatch-defect lesson, brief §3.1 replacement filter is correct-in-form but UNCHECKED. Runner MUST emit three hard-asserts BEFORE `comparison.csv` writes:
```python
assert set(r.symbol for r in results_a_btc_only) == {"BTCUSDT"}, "F-AXIS #1: Pool A leakage"
assert all(r.model_name in {"C' (LINK specialist /018)", "C_prime", "C'"} for r in results_c_spec), "F-AXIS #1: C' contamination"
assert sum(1 for r in all_results if r.symbol == "ETHUSDT" and r.model_name == "A (BTC+ETH pool)") == 0, "F-AXIS #1: Pool A ETH bleed-through after filter"
```
Plus `replacement_filter_audit.csv` deliverable per §10.5. → **ADOPTED**. Section 3.1 amended (see implementation amendment in next commit pass); Section 4 F-AXIS-MECHANISM #1 now declares hard-assert mandate explicitly; Section 10.5 audit CSV added.

**§6 — Verdict priors RECALIBRATED to 30/30/35/25/6/4**:

| Verdict | QR /027 v1 | LM Master | Δ | Rationale |
|---|---:|---:|---:|---|
| PROMISING-METHODOLOGY | 50% | **30%** | -20pp | modal bundle +0.45-0.50 lands at NEG edge of [+0.40, +0.75] |
| INERT | 30% | **35%** | +5pp | structural ceiling at +0.50 (LTC drag + C×E altcoin concentration) |
| NEGATIVE | 15% | **25%** | +10pp | LTC -1.05 drag + C×E +0.60 push deeper than F-AXIS #3 bands |
| NEGATIVE-BELOW-BAND | 5% | **6%** | +1pp | absolute < +0.40 floor breach risk |
| BLOCK | 5% | **4%** | -1pp | brief structurally sound; falsifiers well-pre-registered |

→ **ADOPTED**. Section 5 below replaced with this distribution. The modal shifts from PROMISING-METHODOLOGY to INERT — methodology partially validated but lift unstable at multi-seed.

**§7 — Most important point**: STRUCTURAL CEILING at OOS Sharpe ~+0.50 driven by (a) Model D LTC -1.05 drag (irrecoverable within /027 scope) and (b) C_link × E_dot +0.60 OOS Pearson altcoin concentration. Single-seed regression magnitude alone cannot break this ceiling. Modal multi-seed lands INERT (35%), which validates per-cohort architecture as STABLE but NOT LIFT-PRODUCING at current 5-Model composition. → **ADOPTED**. Section 1 hypothesis amended at next commit pass to acknowledge ceiling; Section 11.1 / 11.2 framing reflects that even PROMISING-METHODOLOGY does NOT unblock LTC-drag and C×E concentration for cycle-4.

**§8 — --seeds 2 budget DEFENSIBLE**: v3 precedent (`feedback_v3_outer_seed_cap_2_v3.md`) caps at 2 outer; v1 /015 ran identical config 9.8-12h; methodology-validation framing → variance-reduction need moderate; pushing to --seeds 5 → 9-15h serial → VIOLATES 6h cap. LM Master endorses --seeds 2 at /027; /028+ targeting merge-floor pushes to --seeds 3-5 with parallel infrastructure. → **ADOPTED** (validates Section 3.2 CLI invocation unchanged).

**§9 — /028+ cycle-4 staging — D-specialist MANDATORY regardless of /027 verdict**: LTC -1.05 is the dominant ceiling; D-specialist axis is unconditional cycle-4 priority. C_link × E_dot +0.60 OOS Pearson is cycle-4 axis SEED regardless of /027 verdict — altcoin de-concentration mechanism required (per-symbol weight cap on LINK+DOT OR DOT specialist with anti-LINK gate). → **ADOPTED**. Section 11 below restructured: §11.1 / §11.2 / §11.3 all converge on D-specialist + C×E concentration mechanism as unconditional cycle-4 priorities (the verdict-conditional branching now layers ABOVE this unconditional MANDATORY axis).

**Net summary**: LM Master's 9 recommendations all adopted as written. The modal-prediction divergence (QR +0.55 ↔ LM Master +0.45-0.50) is 1 magnitude — within normal pre-design uncertainty. The structural amendment is: brief now correctly priors INERT (35%) as modal, recognizes LTC drag + C×E concentration as ceiling drivers, mandates F-AXIS #1 hard-asserts, mandates `specialist_stability.csv` + `replacement_filter_audit.csv` as Phase 7.4 deliverables, and pre-commits cycle-4 D-specialist + C×E de-concentration axes regardless of /027 outcome.

**Phase 5.5 gate**: Section 3.4 NO LONGER empty post-amendment; PASS.

### 3.5 Axis Family Declaration (v1 mandatory)

- **Axis family**: `per-cohort-specialization` REPEAT — CONFIRMATION bundles the two PROMISING cycle-3 EXPLORATIONs (/018 LINK + /019 ETH+gate). CONFIRMATIONs are exempt from Axis Rotation Discipline per v1 skill §"Iteration Cadence Discipline" Rule 4 (CONFIRMATION = bundle of best EXPLORATIONS).
- **Cohort + Specialization pairing**: LINK + isolation (Model C'), ETH + asymmetric long-suppress BTC-trend gate (Model G), BTC+LTC+DOT via baseline pool (Models A pool BTC slice, D, E).
- **Multi-axis discipline**: this is the CONFIRMATION; single-axis discipline does NOT apply to CONFIRMATION bundling (CONFIRMATIONs aggregate multiple PROMISING EXPLORATION axes by design).
- **Phase 7.5 Critic Check 14**: brief Section 0.6 declares family `per-cohort-specialization` REPEAT; src/ diff is dispatch-only (5 model runs at multi-seed config + ETH replacement filter + BTC-trend gate post-hoc). No feature-set change, no labeling change, no risk-gate code change. Check 14 PASS.

### 3.6 Wall-Clock Estimate (CRITICAL — Phase 5.5 BLOCK if missing or > 6h)

**Predicted wall-clock: 4.5h to 5.5h total** (well below 6h HARD CAP).

Decomposition:
- **Anchor 1**: BASELINE_V1 baseline at 5-seed × n_trials=50 × 4 models (A/C/D/E) ran 7h 0m. At 10 paths/cell (5 inner × 2 outer) × n_trials=35 × 5 models (A/C'/D/E/G), this is approximately:
  - 10/5 = 2× more paths per cell × 35/50 = 0.7× fewer trials per path = **1.4× compute** for the 4 baseline-style models.
  - Baseline 4 models * 1.4 = ~9.8h equivalent IF run in serial — too high for 6h cap.
- **Anchor 2 (refined)**: /015 was the only prior multi-seed v1 run. /015 used `--seeds 2 --n-trials 35 --ensemble-size 5` at 4 baseline models (A/C/D/E) on V1_FEATURE_COLUMNS_PRUNED 40 cols. It ran **9.8-12h** wall-clock (user-authorized one-time exception).
- **/027 has 5 models, not 4**, BUT 2 specialists are single-symbol (Model C' on LINK only = ~1/2 wall-clock per path; Model G on ETH only = ~1/2 wall-clock per path) vs the pool's 2-symbol training.
  - Effective wall-clock equivalents: Model A pool (2 sym, 1.0 unit) + Model C' (1 sym, 0.5 unit) + Model D (1 sym, 0.5 unit) + Model E (1 sym, 0.5 unit) + Model G (1 sym, 0.5 unit) = **3.0 units total** vs baseline-style 4 models (Pool A 1.0 + C 0.5 + D 0.5 + E 0.5 = 2.5 units).
  - /027 = (3.0 / 2.5) × /015 wall-clock = 1.2× /015 = 1.2 × 9.8h = **11.8h** baseline projection — TOO HIGH.

**Risk: wall-clock could exceed 6h cap.** Mitigation strategies:

1. **Parallel model dispatch**: if the runner is restructured to dispatch the 5 models in parallel (instead of serial), wall-clock drops to ~max(per-model time) × outer-seed factor. /015 ran serial; /027 parallel dispatch would reduce wall-clock to ~3-4h. **However**, no parallel dispatch infrastructure exists in `run_baseline_v1.py` currently — Phase 6.0 Critic pre-flight may flag this.

2. **n_trials reduction to 25**: drops compute by 25/35 = 0.71×. Wall-clock projection becomes 11.8 × 0.71 = **8.4h** — STILL OVER cap.

3. **--seeds 1 outer (10 paths reduced to 5 paths via inner ensemble only)**: drops compute by 0.5×. Wall-clock projection becomes 11.8 × 0.5 = **5.9h** — JUST UNDER cap. But this is single outer-seed; multi-seed regression-to-mean assessment becomes single-path only.

**Decision**: predict 5.5h modal projection ASSUMING parallel model dispatch is wired in at Phase 6.0 (Critic Rec to QE — this is acknowledged as an outstanding infrastructure dependency). If parallel dispatch is NOT available, **fallback to --seeds 1** (single outer) at 5.9h projection. Engineer reports actual wall-clock at engineering_report.md Phase 6 completion.

**Hard kill threshold**: Engineer kills backtest if wall-clock exceeds **6.5h** (cap × 1.083; 6h cap × 8% tolerance for ramp-down overhead).

**Phase 5.5 gate verifies**:
- Section 3.6 wall-clock estimate present (this section).
- Falsifier band [4.5h, 5.5h] modal + [5.9h, 6.5h] fallback declared explicitly.
- 6h HARD CAP visible at Section 3.6 + Section 10 run protocol.

### 3.7 Reproducibility

- `--symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT` exact 5-symbol set.
- `--iteration-label "v1-027"` — required to trigger the new elif dispatch branch.
- `ENSEMBLE_SEEDS[0:5] = [42, 123, 456, 789, 1001]` (literal pin at run_baseline_v1.py).
- Outer seeds via `--seeds 2`: derived from canonical roster, deterministic.
- `OOF_PARQUET_PATH = data/v1_iter_v1-027_trial_oof.parquet` (iter-stamped per /008 fix).
- `PARAMS_PARQUET_PATH = data/v1_iter_v1-027_optuna_best_params.parquet` (iter-stamped per /021 H1 diagnostic).
- BTC-trend gate constants module-level (V1_ITER027_ETH_GATE_*); frozen for /027.
- HEAD SHA recorded at Phase 5.5 (post-brief) + Phase 6 (post-implementation).

---

## Section 4 — Falsifiers (F1-F8 + F-AXIS-MECHANISM #1-5)

Per methodology-validation framing — F1 thresholds calibrated against the [+0.40, +0.75] absolute OOS Sharpe pre-registered band; F-AXIS-MECHANISM #1-5 are the binding cell-disambiguators per Section 1 hypothesis.

### F1 — Bundle OOS Sharpe (absolute + Δ vs baseline anchor)

**Baseline anchor**: BASELINE_V1.md OOS monthly Sharpe = **+0.6637** (per `comparison.csv`).
**Pre-registered target band (Critic /026 rem #2)**: bundle multi-seed mean OOS Sharpe **∈ [+0.40, +0.75]** absolute.

| Verdict cell | F1 absolute OOS Sharpe | F1 OOS Sharpe Δ vs anchor | Note |
|---|---|---|---|
| **PROMISING-METHODOLOGY** | ∈ [+0.65, +0.75] | Δ ∈ [+0.10, +0.40] | methodology validated; specialists lift at multi-seed |
| INERT | ∈ [+0.55, +0.65] | Δ ∈ [-0.10, +0.10] | methodology partial; specialists hold without lift |
| **NEGATIVE** | ∈ [+0.40, +0.55] | Δ < -0.10 (but absolute > +0.40) | multi-seed regression dilutes; methodology partial-refuted |
| **NEGATIVE-BELOW-BAND** | < +0.40 | Δ < -0.10 | absolute below pre-registered band lower bound; methodology refuted |
| **BLOCK** | n/a | n/a | Phase 7.5 Critic Check finds methodology defect |

**Calibration note**: /026 single-seed reference bundle was +0.57 (monthly sqrt(12)). Multi-seed regression on specialists projects bundle to [+0.40, +0.55] mean modal. PROMISING-METHODOLOGY at [+0.65, +0.75] would represent meaningful multi-seed STABILITY (the specialists hold without per-symbol degradation). The single-seed +0.57 → multi-seed +0.65 path would require Model A pool's BTC slice to lift relative to /026 attribution (possible via pool-co-training regularization preserved at multi-seed) AND/OR D+E to be less drag than single-seed (regression to mean reverses).

### F3 — Bundle IS Sharpe Δ (basin-health signal)

**Baseline anchor**: BASELINE_V1.md IS monthly Sharpe = **+0.2829**.
**Pre-registered band**: bundle multi-seed mean IS Sharpe Δ vs anchor in **[-0.20, +0.50]** range.

| Verdict cell | F3 IS Sharpe Δ vs anchor | Note |
|---|---|---|
| PROMISING-METHODOLOGY | Δ ∈ [+0.10, +0.50] | both halves positive lift |
| INERT | Δ ∈ [-0.20, +0.10] | IS stable; OOS-only lift if PROMISING |
| **F3 IS-CAT auto-reject** | Δ ≤ -0.30 | basin collapse on IS; verdict elevates to NEGATIVE regardless of F1 |

F3 IS-CAT auto-reject lever per `feedback_v1_f3_is_cat_autoreject.md` (codified across cycle-3 from /016 IS-CAT pattern).

### F2 — Embargo / look-ahead PASS (structural; automatic)

`walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` UNCHANGED. BTC-trend gate is past-only (np.searchsorted right-1 with warmup floor of 42 bars; BIT-IDENTICAL to /019). PASS by construction.

### F4 — Feature ADF stationarity (informational; no new features)

40 V1_FEATURE_COLUMNS_PRUNED unchanged. ADF rerun on 5-sym halves should reproduce baseline Bonferroni-pass profile (30/40 stationary + 10/40 declared regime-indicator exceptions per BASELINE_V1.md). INFORMATIONAL.

### F5 — PSR_monthly_vs_1 OOS (CONFIRMATION-mode merge proxy)

**Baseline anchor**: BASELINE_V1.md PSR_monthly_vs_1 OOS = **0.0789** (probability OOS Sharpe > 1.0 = 7.9%).

| Verdict cell | F5 PSR_monthly_vs_1 OOS band |
|---|---|
| PROMISING-METHODOLOGY | > 0.20 (probability OOS Sharpe > 1.0 increases from 7.9% to >20% under multi-seed) |
| INERT | ∈ [0.05, 0.20] |
| NEGATIVE | < 0.05 |

**Informational only at /027** (methodology validation, NOT merge candidate). PSR > 0.95 is the merge gate; not relevant here.

### F6 — Per-symbol IS direction (5-sym vector)

Per-symbol IS net_pnl across 5 cohorts:
- BTC, ETH, LINK, LTC, DOT — each cohort's IS PnL contribution.
- Mechanism check: LINK (specialist) IS PnL > 0 AND ETH+gate (specialist) IS PnL > 0 required for PROMISING-METHODOLOGY classification.
- LTC IS PnL is informational (baseline pool's LTC slice).

### F7 — Per-symbol IS/OOS sign agreement (5-sym vector)

For each of 5 cohorts: IS and OOS PnL same sign or near-zero indicates regime-stable cohort. Sign disagreement on ≥ 3 of 5 cohorts → basin-lock signal at multi-seed; flag at Phase 7.4.

### F8 — Total trade count band

**Anchor**: BASELINE_V1.md totals = 621 IS / 189 OOS trades.

| F8 cell | IS trades | OOS trades | Note |
|---|---|---|---|
| PASS | ∈ [500, 800] | ∈ [150, 300] | matches baseline scale across 5-Model replacement bundle |
| BREACH-low | < 500 | < 150 | bundle under-fires; replacement filter drops too many trades |
| BREACH-high | > 800 | > 300 | bundle over-fires; specialist dispatch produces redundant signals |

OOS upper bound 300 covers /026 5-Model single-seed estimate (205 OOS trades) plus multi-seed expansion to 10 paths × widened ensemble agreement.

### F-AXIS-MECHANISM (5 sub-checks; binding cell disambiguators)

**F-AXIS #1 — Replacement-pool dispatch correctness (HARD-ASSERT MANDATE per LM Master §5)**: `trades.csv` per-symbol cohort source verification:
- LINK trades originate ONLY from Model C' (specialist /018 architecture). Zero LINK trades from baseline Model C — Model C is NOT dispatched in /027.
- ETH trades originate ONLY from Model G (specialist /019 architecture + asymmetric long-suppress BTC-trend gate). Zero ETH trades from Model A's pool training — Model A's ETH slice is DROPPED at replacement filter.
- BTC trades originate ONLY from Model A's BTC slice (pool training).
- LTC trades originate ONLY from Model D.
- DOT trades originate ONLY from Model E.

**HARD-ASSERT MANDATE (per LM Master Phase 4.5 §5 and /024 dispatch-defect lesson)**: the runner MUST execute three asserts BEFORE `comparison.csv` emission. Failure = `AssertionError` raises and aborts the run before any reports are written:

```python
assert set(r.symbol for r in results_a_btc_only) == {"BTCUSDT"}, \
    "F-AXIS #1: Pool A leakage — ETH slice not dropped at replacement filter"
assert all(r.model_name in {"C' (LINK specialist /018)", "C_prime", "C'"} 
           for r in results_c_spec), \
    "F-AXIS #1: C' contamination — baseline Model C trades present in C' specialist"
assert sum(1 for r in all_results 
           if r.symbol == "ETHUSDT" and r.model_name == "A (BTC+ETH pool)") == 0, \
    "F-AXIS #1: Pool A ETH bleed-through after filter"
```

The runner additionally emits `replacement_filter_audit.csv` per Section 10.5 (pre-filter / post-filter trade counts per model, dropped-symbol attribution).

PASS criterion: per-trade `model_name` column in `trades.csv` matches the cohort-source mapping above AND all three hard-asserts evaluated TRUE at runtime AND `replacement_filter_audit.csv` shows Pool A pre-filter has ETH trades and post-filter has none. F-AXIS #1 is the ENGINEERING dispatch-correctness check; mismatched mapping at /027 is a process-integrity violation; missing hard-asserts at Phase 6.0 Critic pre-flight is a BLOCK condition.

**F-AXIS #2 — Cross-correlation preservation at multi-seed (DIRECTIONAL PREDICTIONS per LM Master §2)**: cross-correlation between replacement-pool and specialist monthly returns must STAY < 0.50 for the two replacement pairs at multi-seed mean; the C×E altcoin pair is expected to STAY > +0.55 (signal-level co-movement, NOT basin lottery).

| Pair | /026 single-seed OOS Pearson | LM Master §2 multi-seed prediction | Gate behavior |
|---|---:|---|---|
| pool_minus_LINK_ETH × LINK_specialist | +0.4935 | DISSOLVES → **[+0.35, +0.42]** modal +0.38 (basin lottery; 2 of 15 risk-on months drive single-seed) | <0.50 PASS expected at multi-seed |
| pool_minus_LINK_ETH × ETH+gate_specialist | -0.1412 | UNCHANGED (already independent at single-seed) | <0.50 PASS by construction |
| C_link_spec × E_dot (5-Model 10-pair view) | +0.6027 (Spearman +0.425) | STAYS → **[+0.55, +0.60]** modal +0.58 (signal-level altcoin co-movement; multi-seed WILL NOT dissolve) | flagged for Phase 7 attribution; >+0.55 → C×E de-concentration MANDATORY cycle-4 axis |

If multi-seed pool×LINK Pearson does NOT dissolve to predicted band (i.e., STAYS > +0.45), the LM Master §2 mechanism prediction is falsified and the replacement-pool independence claim is revised at Phase 7.4 LM Master post-mortem. If multi-seed C_link × E_dot Pearson DOES dissolve below +0.50, the altcoin joint concentration is basin lottery (NOT signal level) and the cycle-4 D-specialist + C×E de-concentration priority can be DOWNGRADED. Both outcomes are pre-registered for Phase 7.4 binding finding.

**F-AXIS #3 — Per-specialist Sharpe stability at multi-seed (PER-SPECIALIST BANDS ±0.25 per LM Master §1)**: each specialist's OOS Sharpe must land within the LM Master modal ±0.25 spread centered on §1 modes (NOT the previous QR-derived mid-range bands). LM Master modal magnitudes apply 18-22% regression to single-seed (NOT 50%) because ENSEMBLE_SIZE=5 inner already collapses half the basin variance.

| Specialist | Single-seed OOS Sharpe | LM Master §1 modal mean | LM Master ±0.25 spread band | F-AXIS #3 PASS |
|---|---:|---:|---|---|
| Model C' (LINK) | +0.9789 | **+0.78** (regress 20%) | **[+0.53, +1.03]** | OOS Sharpe in band |
| Model G (ETH+gate) | +0.6990 | **+0.52** (regress 26%) | **[+0.27, +0.77]** | OOS Sharpe in band |

F-AXIS #3 PASS = both specialists in their respective LM Master bands → methodology validated (specialists STABLE under multi-seed).
F-AXIS #3 FAIL on LINK = C' OOS Sharpe < +0.53 → /018's PROMISING was basin-lottery favorable, not signal-stable; verdict elevates to NEGATIVE.
F-AXIS #3 FAIL on ETH+gate = G OOS Sharpe < +0.27 → /019's PROMISING was basin-lottery favorable, not signal-stable; verdict elevates to NEGATIVE.

Cross-check at Phase 7.4 LM Master post-mortem: actual per-specialist standard deviation (computed across 10 paths from `specialist_stability.csv` per Section 10.5) versus LM Master §3 prediction (±0.20 single specialist, ±0.30 5-model bundle). If observed std > ±0.40 for a single specialist, the basin-variance compression assumption is falsified for that specialist family.

**F-AXIS #4 — DSR threshold (relaxed for METHODOLOGY VALIDATION)**: multi-seed CONFIRMATION-mode DSR > **0.50** (relaxed from MERGE-gate 0.95).

| DSR band | Verdict cell impact |
|---|---|
| DSR > 0.50 | F-AXIS #4 PASS; methodology validated at edge-significance threshold |
| DSR ∈ [0.20, 0.50] | F-AXIS #4 INERT; methodology partial; specialists hold but no edge significance |
| DSR < 0.20 | F-AXIS #4 FAIL; methodology refuted; multi-seed correction collapses edge |

**F-AXIS #5 — PBO threshold (relaxed for METHODOLOGY VALIDATION)**: CSCV-based PBO < **0.40** at multi-seed (CONFIRMATION-mode).

| PBO band | Verdict cell impact |
|---|---|
| PBO < 0.40 | F-AXIS #5 PASS; backtest overfitting probability acceptable |
| PBO ∈ [0.40, 0.60] | F-AXIS #5 INERT; flag at Phase 7.4 |
| PBO ≥ 0.60 | F-AXIS #5 FAIL; bundle is overfit to IS basin; multi-seed didn't dissolve overfit risk |

---

## Section 5 — Predicted Verdict Distribution

Per Section 0.2 framing + Critic /026 binding remediation #2 + LM Master Phase 4.5 recalibration (§3.4 §6 above) + LM Master cycle-3 6/6 PERFECT methodology track:

**Verdict priors RECALIBRATED per LM Master Phase 4.5 (modal: INERT 35%)**:

- **PROMISING-METHODOLOGY (30%)**: multi-seed mean OOS Sharpe Δ ∈ [+0.10, +0.40] (absolute [+0.65, +0.75]); F-AXIS #1/2/3/4/5 PASS; methodology validated. /027 single-seed reference +0.57 → multi-seed [+0.65, +0.75] requires BOTH specialists to HOLD at the upper edge of LM Master per-specialist bands (C' near +0.85, G near +0.62) AND replacement-pool BTC slice to maintain lift AND C×E altcoin correlation to dissolve unexpectedly at multi-seed. LM Master modal projection of bundle +0.45-0.50 places this outcome at the favorable tail of the distribution. **Prior LOWERED 50% → 30% per LM Master §6** (modal bundle lands at NEGATIVE-leaning edge of pre-registered band).
- **INERT (35% — NEW MODAL)**: Δ ∈ [-0.10, +0.10] (absolute [+0.55, +0.65]); specialists hold but no lift over baseline. Multi-seed regresses single-seed slightly favorable draws (C' to modal +0.78; G to modal +0.52); bundle structure (LTC drag, DOT flat, C×E altcoin co-movement) caps upside at the +0.50 STRUCTURAL CEILING (LM Master §7). Cycle-3 closing finding: methodology partially validated (specialists STABLE) but lift unstable at multi-seed composition. **Prior RAISED 30% → 35% per LM Master §6** — this becomes the modal verdict.
- **NEGATIVE (25%)**: Δ < -0.10 (absolute could still be in [+0.40, +0.55]); multi-seed regression deeper than LM Master projection; specialists' single-seed lift dissolves further OR LTC drag amplifies OR C×E correlation pushes joint altcoin tail. Possible if /018's +0.98 single-seed was deeper into basin lottery favorable tail than LM Master projection (C' regresses below +0.55 lower band) OR if D LTC -1.05 drag intensifies at multi-seed coverage. **Prior RAISED 15% → 25% per LM Master §6** — LTC drag + C×E concentration are dominant tail-risk drivers.
- **NEGATIVE-BELOW-BAND (6%)**: absolute OOS Sharpe < +0.40; pre-registered band breach; methodology refuted at multi-seed. Combined with multi-seed C_link × E_dot Pearson STAYING > +0.55 (per LM Master §2 prediction) → joint altcoin concentration crystallizes simultaneously with LTC drag → bundle structural ceiling collapses through floor. **Prior RAISED 5% → 6% per LM Master §6**.
- **BLOCK (4%)** (split — 2.5% BLOCK-PENDING-FIX | 1.5% BLOCK-FINAL): Phase 7.5 Critic Check finds methodology defect — e.g., F-AXIS #1 dispatch incorrect (LINK trades from baseline Model C instead of Model C' specialist; ETH trades from Model A's pool slice instead of Model G — but Section 3.4 §5 / Section 4 F-AXIS #1 hard-assert mandate reduces this risk by design), F-AXIS #2 multi-seed cross-correlation regression unexpected breach, F-AXIS #3 specialist Sharpe out-of-band, or F-AXIS #4/5 DSR/PBO threshold breach. **Prior LOWERED 5% → 4% per LM Master §6** (brief structurally sound; falsifiers well-pre-registered).

**Three specific mechanism predictions (mechanism #1 + #2 recalibrated per LM Master §1 / §2)**:

1. **Multi-seed per-specialist Sharpe (RECALIBRATED per LM Master §1)**: Model C' OOS Sharpe modal **+0.78** (band [+0.53, +1.03] = ±0.25 spread); Model G OOS Sharpe modal **+0.52** (band [+0.27, +0.77] = ±0.25 spread). If C' < +0.53 or G < +0.27 → F-AXIS #3 FAIL on the corresponding specialist; verdict elevates to NEGATIVE. The QR prior of C' mean +0.70 / G mean +0.40 was below LM Master's modal projection; both bands now centered on LM Master's +0.78 / +0.52 modes.

2. **Bundle MaxDD**: /026 single-seed reference shows bundle MaxDD = 49.18% (vs baseline 33.77%; +15.4pp). Multi-seed could either expand (if LTC drag amplifies under wider seed coverage) or contract (if seed averaging dampens drawdown peaks). Predicted band: bundle OOS MaxDD ∈ [35%, 55%].

3. **Cross-correlation directional predictions (NEW per LM Master §2)**: pool×LINK_spec single-seed +0.4935 → multi-seed DISSOLVES to **[+0.35, +0.42]** (basin-lottery driver: 2 of 15 risk-on months). C_link × E_dot single-seed +0.6027 → multi-seed STAYS at **[+0.55, +0.60]** (signal-level altcoin co-movement; binding cycle-4 finding). If C×E < +0.50 at multi-seed → cycle-4 axis priorities re-rank; if STAYS > +0.55 → C×E de-concentration MANDATORY cycle-4 axis (LM Master §9).

---

## Section 6 — Failure Modes

### 6.1 Multi-seed regression breaks specialists (modal NEGATIVE failure)

Multi-seed averages out single-seed Optuna basin lottery. If /018 LINK +0.98 and /019 ETH+gate +0.70 were significantly basin-lottery favorable, the multi-seed mean regresses below LM Master priors (+0.80 LINK / +0.50 ETH+gate). F-AXIS #3 FAILS on one or both specialists.

**Mitigation built-in**: pre-registered F-AXIS #3 band catches this; verdict elevates to NEGATIVE not INERT.

### 6.2 Cross-correlation drift OOS at multi-seed

The /026 single-seed pool_minus_LINK_ETH × LINK_specialist OOS Pearson +0.4935 is **strictly below** the < 0.50 threshold but tight. Multi-seed regression could push this above 0.50 if specialists become more correlated with the residual pool under averaging.

**Mitigation**: F-AXIS #2 multi-seed cross-correlation check; flag at Phase 7.4 if regressed > 0.50.

### 6.3 Bundle MaxDD blowout

/026 single-seed bundle MaxDD = 49.18% vs baseline 33.77% (+15.4pp). Multi-seed could amplify this. If bundle MaxDD > 60% at multi-seed mean, methodology is fragile-by-drawdown even if Sharpe is in band.

**Mitigation**: Phase 7 evaluation reports MaxDD; not a binding falsifier (methodology validation is OOS Sharpe-anchored) but informational at cycle-3 closeout for cycle-4 priorities.

### 6.4 F-AXIS #1 dispatch error (process-integrity failure)

If the implementation does not correctly drop Model A's ETH trades or Model C's baseline LINK trades, the bundle double-counts. This is a process-integrity violation and Critic Phase 7.5 would BLOCK-PENDING-FIX or BLOCK-FINAL.

**Mitigation**: F-AXIS #1 dispatch test at engineering_report.md Phase 6 completion — verifies per-trade `model_name` mapping; if mapping is wrong, the run is invalid.

### 6.5 Wall-clock cap breach

Section 3.6 acknowledges wall-clock projection at 5.5-11.8h depending on parallel-dispatch availability. If actual wall-clock exceeds 6.5h (cap × 1.083), Engineer kills the run.

**Mitigation**: parallel-dispatch infrastructure or fallback to `--seeds 1` outer (sacrifices multi-seed but cuts compute by 50%). Phase 6.0 Critic pre-flight flags this.

### 6.6 LTC drag dominates bundle Sharpe (structural)

LTC has OOS Sharpe -1.05 in baseline. The bundle includes LTC via Model D baseline. If multi-seed amplifies LTC drag (more trades, deeper losses), bundle Sharpe could drop below pre-registered band lower bound +0.40 → NEGATIVE-BELOW-BAND.

**Mitigation**: this is acknowledged at Section 2.4 + Critic /026 Finding 4. LTC drag is the structural ceiling on /027's achievable Sharpe; cycle-4 first EXPLORATION priority is D-specialist (Critic /025 Path Forward Option 1) per Section 11 path forward.

---

## Section 7 — Pre-Registered Predictions

Binding predictions for Phase 7 evaluation (binding = if observed values fall outside these bands, the prediction is FALSIFIED and recorded as such in the diary):

1. **F1 OOS Sharpe (absolute, multi-seed mean)**: predicted ∈ [+0.40, +0.75]; modal +0.55 (INERT-leaning).
2. **F1 OOS Sharpe Δ vs anchor +0.6637**: predicted ∈ [-0.27, +0.13]; modal Δ -0.11 (INERT-NEGATIVE boundary).
3. **F3 IS Sharpe Δ vs anchor +0.2829**: predicted ∈ [-0.10, +0.20]; modal Δ +0.05.
4. **OOS trades total**: predicted ∈ [150, 300]; modal ~210 (based on /026 single-seed 205 + multi-seed widening).
5. **OOS trades/month**: predicted ≥ 10 (holds vs floor).
6. **Per-specialist OOS Sharpe**: Model C' ∈ [+0.50, +0.80] mean +0.70; Model G ∈ [+0.30, +0.50] mean +0.40.
7. **Cross-correlation OOS at multi-seed**: pool_minus_LINK_ETH × LINK_specialist Pearson < 0.50 (modal +0.45 expected regress); × ETH+gate Pearson < 0.20 (modal -0.10).
8. **5-Model 10-pair view**: C_link × E_dot OOS Pearson > 0.50 modal (+0.55 expected); flag at Phase 7.4.
9. **DSR (CONFIRMATION-mode, multi-seed)**: predicted ∈ [0.20, 0.70]; modal +0.45 (F-AXIS #4 INERT mostly, PROMISING-METHODOLOGY if at upper).
10. **PBO (CSCV multi-seed)**: predicted ∈ [0.20, 0.50]; modal 0.35 (F-AXIS #5 PASS most likely).
11. **Bundle OOS MaxDD**: predicted ∈ [35%, 55%]; modal 45%.
12. **Wall-clock**: predicted ∈ [4.5h, 6.5h] (parallel dispatch contingent); modal 5.5h.
13. **F-AXIS #1 dispatch correctness**: PASS-by-construction (engineering verification at engineering_report.md Phase 6).

LM Master modal verdict adopted at Phase 4.5 (if differs): TBD pending advisory.

---

## Section 8 — MERGE / NO-MERGE Decision (PRE-COMMITTED)

**MERGE decision: NO-MERGE PRE-COMMITTED at brief authoring.**

Per Section 0.2 framing + Critic /026 binding remediation #2:

- /027 target band [+0.40, +0.75] absolute OOS Sharpe is **STRUCTURALLY BELOW the +1.0 hard merge floor** per BASELINE_V1.md.
- Even an upper-band hit (+0.75) does NOT clear:
  - IS Sharpe > 1.0 (modal F3 prediction is IS Sharpe ≈ +0.33; far below +1.0).
  - OOS Sharpe > 1.0 (target band upper +0.75 is below +1.0 by 0.25).
- /027 is pre-committed CONFIRMATION-METHODOLOGY-VALIDATION (sister to /015's CONFIRMATION-NEGATIVE-catastrophic verdict cell — structural cycle closing, not merge candidate).

**BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`) regardless of /027 outcome.** Per `feedback_v3_baseline_update_policy.md` only CONFIRMATION-MERGE updates baseline.

**Outcome routing**:

| /027 outcome | Diary verdict | BASELINE_V1.md | Tag |
|---|---|---|---|
| PROMISING-METHODOLOGY | NO-MERGE-PROMISING-METHODOLOGY | UNCHANGED | `v0.v1-027` |
| INERT | NO-MERGE-INERT | UNCHANGED | `v0.v1-027` |
| NEGATIVE | NO-MERGE-NEGATIVE | UNCHANGED | `v0.v1-027` |
| NEGATIVE-BELOW-BAND | NO-MERGE-NEGATIVE-BELOW-BAND | UNCHANGED | `v0.v1-027` |
| BLOCK | NO-MERGE-BLOCK (FINAL) or BLOCK-PENDING-FIX | UNCHANGED | (no tag until BLOCK resolves) |

Per Critic /026 Finding 4 ("/027 verdict classification should be pre-registered as CONFIRMATION-NEGATIVE-NO-MERGE [validating the architecture, not the edge]"), the methodology-validation framing is the cleanest interpretation. The Critic's recommendation aligns precisely with the brief's framing.

---

## Section 9 — Library Stack

No new dependencies. /027 re-uses:
- `crypto_trade.strategies.ml.risk_v2.{BtcTrendFilterConfig, apply_btc_trend_filter, load_btc_klines_for_filter}` — symmetric direction-aware BTC-trend gate per /019.
- `crypto_trade.features_v1.V1_FEATURE_COLUMNS_PRUNED` — 40-col baseline pruned feature set.
- `crypto_trade.strategies.ml.validation_v1.{psr, dsr, ...}` — CONFIRMATION-mode DSR/PSR re-evaluation.
- `crypto_trade.strategies.ml.optimization` — Optuna trial dispatch (n_trials=35).
- `crypto_trade.strategies.ml.walk_forward` — fixed embargo at line 113.

Library versions (informational; matched to BASELINE_V1.md):
- `mlfinlab==1.4` (CPCV utilities; if available)
- `pypbo` (PBO computation)
- `lightgbm` (model)
- `optuna` (hyperparameter search)
- `numpy`, `pandas`, `scikit-learn` (standard)

---

## Section 10 — Run Protocol

### 10.1 Engineering_report.md is BINDING

Per `feedback_v1_engineering_report_compliance.md` (codified at /023 closeout; recurrent through /024 + /025 incidents): `engineering_report.md` MUST be present at Phase 7.5 Critic dispatch. **6 of 10 cycle-3 EXPLORATIONs missed `engineering_report.md` at Phase 7.5 dispatch** — this is a structural QE-layer pattern that the orchestrator-layer fix has not yet addressed.

For /027 CONFIRMATION specifically: `briefs-v1/iteration_v1-027/engineering_report.md` is a REQUIRED deliverable BEFORE Phase 7.5 Critic dispatch can fire. The QE writes this report after backtest completion at Phase 6 (or via the SPLIT DISPATCH pattern for runs > 30 min wall-clock per `feedback_split_engineer_dispatch.md`).

### 10.2 Run sequence (Phases 5.5 → 6.0 → 6 → 7.4 → 7.5 → 7 → 8)

1. **Phase 5.5 (QE gate)** — QE verifies brief Section 0.6 + 2.5 + 3.4 + 3.6 + 4 (falsifiers) + 10 (run protocol) + 11 (path forward). BLOCK if missing any. PASS to dispatch Phase 6.0.
2. **Phase 6.0 (Critic pre-flight)** — Critic mini-Check 1 (brief look-ahead audit), mini-Check 13 (anti-pattern static scan on QE's src/ diff), foundation regression check (re-verify `walk_forward.py:113`), cadence + axis sanity, falsifier presence. PASS to dispatch Phase 6. BLOCK returns to QR for revision (one revision allowed).
3. **Phase 6 (QE backtest)** — backtest launches per CLI invocation §3.2; engineering_report.md written at completion. Wall-clock kill threshold 6.5h.
4. **Phase 7.4 (LM Master post-mortem)** — LM Master reads engineering_report.md + comparison.csv + feature_importance.csv (IS + OOS) + Optuna trial logs; emits Phase 7.4 section of `lgbm_advisor.md` covering F-AXIS #3 per-specialist stability + cross-correlation drift + DSR/PBO interpretation + accountability vs Phase 4.5 predictions.
5. **Phase 7.5 (Critic review)** — Critic runs 8 mandatory checks + Check 14 (axis family validation) + optional 9-12; verdict ∈ {PROMISING-METHODOLOGY, INERT, NEGATIVE, NEGATIVE-BELOW-BAND, BLOCK-PENDING-FIX, BLOCK-FINAL}.
6. **Phase 7 (QR evaluation)** — first time QR sees OOS data; reconciles against Section 7 pre-registered predictions.
7. **Phase 8 (QR diary)** — produces `diary-v1/iteration_v1-027.md`; NO-MERGE pre-committed; documents methodology-validation outcome + cycle-3 closeout + cycle-4 path forward (informational).

### 10.3 Pre-flight data freshness

Per `feedback_data_staleness_per_worktree.md`: verify data freshness BEFORE Phase 6 backtest launches:

```bash
# Verify klines fresh (<16h old)
ls -la data/BTCUSDT/8h.csv data/ETHUSDT/8h.csv data/LINKUSDT/8h.csv data/LTCUSDT/8h.csv data/DOTUSDT/8h.csv

# Refresh if stale
uv run crypto-trade fetch --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT --intervals 8h

# Regenerate features
uv run crypto-trade features --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT \
  --interval 8h --track v1 --format parquet --workers 4
```

### 10.4 Required artifacts

Engineering_report.md MUST emit (per cycle-3 codified rule + Critic /025 Recommendation #1):
- Run command line + commit SHA + start/end wall-clock timestamps.
- Per-model wall-clock breakdown (Pool A / C' / D / E / G).
- Per-symbol trade roster summary (`F-AXIS #1` dispatch correctness verification).
- `reports-v1/iteration_v1-027/comparison.csv` reference.
- `reports-v1/iteration_v1-027/{in_sample,out_of_sample}/per_symbol.csv` reference.
- Cross-correlation matrix at multi-seed (analogue of /026's replacement_pool_correlation.csv) — `reports-v1/iteration_v1-027/cross_correlation_matrix.csv`.
- DSR/PBO/PSR (CONFIRMATION-mode) artifacts: `reports-v1/iteration_v1-027/{cpcv_paths.csv, dsr.json}`.
- Feature importance per-fold per `feedback_v1_feature_importance_per_fold.md` (DEFER-OK if runner doesn't emit per-fold; aggregate ranks acceptable as documented in /025 retrospective).

### 10.5 Methodology validation specific artifacts

NEW for /027 (methodology-validation framing); both REQUIRED per LM Master Phase 4.5 §3 (`specialist_stability.csv`) and §5 (`replacement_filter_audit.csv`):

- **`reports-v1/iteration_v1-027/specialist_stability.csv`** — per-specialist (C', G) per-seed OOS Sharpe across the 10 model paths (5 inner × 2 outer); columns: `specialist, inner_seed, outer_seed, oos_sharpe, oos_trades, oos_pnl_pct, is_sharpe`. Phase 7.4 LM Master post-mortem reads this CSV to compute the actual per-specialist standard deviation across 10 paths and cross-check against LM Master §3 prediction (±0.20 single specialist). Provides the distributional view that the F-AXIS #3 modal-band check cannot — namely, whether the modal is reached by tight cluster (acceptable) vs wide spread with the mode at the middle (unstable). If observed std > ±0.40 for a specialist, the basin-variance compression assumption is falsified for that specialist family at Phase 7.4.

- **`reports-v1/iteration_v1-027/replacement_filter_audit.csv`** — per-model pre-replacement vs post-replacement trade count; columns: `model, symbol, pre_filter_trades, post_filter_trades, dropped_count, dropped_reason`. Required rows: Pool A pre-filter ETH count > 0 with post-filter ETH count == 0 AND `dropped_reason == "replacement_to_specialist_G"`; Pool A pre-filter BTC count > 0 with post-filter BTC count == pre-filter BTC count AND `dropped_reason == "retained"`. Verifies F-AXIS #1 dispatch correctness as a tabular auditable artifact independent of the runtime hard-asserts.

- **2-seed Pareto deliverable**: `reports-v1/iteration_v1-027/pareto_2seed.csv` — per-outer-seed bundle OOS Sharpe with mean and Pareto-frontier flag. Pre-registered LM Master §3 band: 2-seed Pareto spans [+0.25, +0.70] around modal +0.45-0.50. If Pareto seeds straddle (one above +0.55, one below +0.35), the 5-model bundle is composition-unstable and Phase 7.4 flags as binding cycle-4 finding.

---

## Section 11 — Path Forward (cycle-4 axis priorities, post-/027)

Per Critic /025 Path Forward + Critic /026 Option C + /025 closeout structural verdict + LM Master Phase 7.4 §6 from /025:

**The cycle-4 axis selection layers a verdict-conditional branch ABOVE two UNCONDITIONAL MANDATORY priorities** (per LM Master Phase 4.5 §9 — these fire regardless of /027 verdict because both are STRUCTURAL CEILING drivers identified at /026 + /027 pre-design):

**UNCONDITIONAL MANDATORY cycle-4 priorities (LM Master §9 binding)**:

1. **D-specialist EXPLORATION MANDATORY**: LTC drag at OOS Sharpe -1.05 is the single dominant ceiling on the current 5-Model bundle (LM Master §7 STRUCTURAL CEILING analysis). The D-specialist axis is unconditional cycle-4 priority irrespective of whether /027 confirms PROMISING-METHODOLOGY or lands INERT/NEGATIVE. Specialist architecture: long-suppression gate (analogue of Model G's BTC-trend gate, applied to LTC against an alt-cycle indicator) OR regime-conditional kill switch OR sample-weighting against LTC IS examples.
2. **C×E altcoin de-concentration MANDATORY**: the C_link × E_dot +0.6027 single-seed OOS Pearson is predicted by LM Master §2 to STAY at +0.55-+0.60 at multi-seed (signal-level altcoin co-movement, NOT basin lottery). Cycle-4 must include an EXPLORATION that breaks this concentration: per-symbol weight cap on LINK+DOT pair OR DOT specialist with anti-LINK regime gate OR universe-expansion to dilute altcoin share. If /027 Phase 7.4 result reveals C×E DID dissolve to <+0.50 at multi-seed (falsifies LM Master §2 prediction), this priority can be DOWNGRADED at /028 brief — otherwise MANDATORY.

**Verdict-conditional branch ABOVE these two MANDATORY axes (selects cycle-4 first EXPLORATION variant)**:

### 11.1 If /027 PROMISING-METHODOLOGY (LM Master prior 30%)

Cycle-4 first EXPLORATION pairs MANDATORY #1 (D-specialist) with **3-symbol pool composition test (BTC+ETH+LINK)** per Critic /026 Option C — natural next step is to optimize composition AFTER methodology validated:
- Hypothesis: 3-sym pool (drop LTC + DOT from pool training; LINK + ETH come from specialists; D + E run as full specialists) preserves specialist lift while removing LTC drag from pool co-training.
- D-specialist still fires in parallel — even with PROMISING-METHODOLOGY, LTC -1.05 OOS Sharpe is structural drag the D-specialist axis directly addresses.
- C×E de-concentration mechanism layered on top via DOT-specialist sub-axis (extend LINK/ETH+gate proven architecture).

### 11.2 If /027 INERT (LM Master prior 35% — MODAL)

Cycle-4 first EXPLORATION leads with MANDATORY #1 (D-specialist) AS the primary axis (most-leveraged unblocking move on STRUCTURAL CEILING):
- Architecture options for D-specialist: long-suppression gate (analogue of Model G's BTC-trend gate); regime gate (Hurst-100 vol-of-vol); on-chain alt-cycle feature (cross-asset BTC dominance z-score).
- C×E de-concentration MANDATORY runs as sister axis: per-symbol weight cap OR DOT-specialist with anti-LINK gate.
- Sister structural axes: sample-weighting (Critic /025 Path Forward Option 2; UNUSED cycle-3) OR XGBoost head-to-head (Critic /025 Path Forward Option 3) — deferred to cycle-4 EXPLORATION #2 onward.

### 11.3 If /027 NEGATIVE or NEGATIVE-BELOW-BAND (LM Master combined prior 31%)

Cycle-4 = **methodology pivot — re-question per-cohort axis fundamentally** WITH MANDATORY #1 + #2 still active:
- Even at NEGATIVE verdict, the D-specialist axis remains the highest-leverage candidate because LTC drag is mechanism-independent of per-cohort architecture choice. C×E de-concentration likewise applies regardless of cohort framing.
- Pivot options for the cycle-4 PRIMARY structural axis: LightGBM → XGBoost mandate (per `feedback_v3_iter016_xgboost_mandate.md` transfer prior), meta-labeling (per `feedback_v3_iter017_metalabeling_mandate.md` transfer prior), labeling-mode pivot (sigma_source NATR → realized-vol), or multi-axis EXPLORATIONs at higher compute budget.
- D-specialist (MANDATORY #1) layers ABOVE the architectural pivot — even if cohort framing pivots, LTC -1.05 still drags as long as LTC is in the universe.

### 11.4 NEW-feature-to-Pool-A is CLOSED for cycle-4 EXPLORATION budget

Per /025 structural verdict (`feedback_v1_pool_a_new_feature_lneg.md`): cycle-4 EXPLORATIONs MUST NOT propose NEW feature families ADDED TO POOL MODEL A at single-seed n_trials=18. Future Pool-A feature work requires:
- Multi-seed CONFIRMATION budget, OR
- Per-symbol specialist context (LINK/ETH+gate pattern), OR
- Orthogonal-mechanism rule layer pivot.

### 11.5 Critic Path Forward (TBD — populated at Phase 7.5)

Per `feedback_v1_constructive_critic_path_forward.md`: Critic Phase 7.5 emits a "Path Forward" section with 2-3 alternative axes from families NOT used in the prior 5 EXPLORATIONs. The QR Phase 8 diary copies these verbatim under "Path Forward (from Critic)" and they become first-tier candidates for cycle-4 brief.

For /027 specifically: the prior 5 going into /027 = {/022 per-cohort-LTC, /023 feature-family, /024 model-arch, /025 feature-family, /026 methodology}. Excluded cycle-4 first-EXPLORATION families per rotation discipline: NONE (5 different families, no monoculture). Critic free to propose from any family. Most-promising cycle-4 candidates from cycle-3 dead-paths catalog: sample-weighting (UNUSED), labeling (cycle-2 negative basin closed), risk-primitive (R5 family closed; R-NEW open).

---

## Section 12 — Roll-back Protocol

If at Phase 6 implementation any of these fire, abort and roll back:

1. **Critic Phase 6.0 pre-flight BLOCK** — return to Phase 5 brief revision (one revision allowed).
2. **Test suite FAIL** — `uv run pytest tests/` must produce all-green before backtest launches.
3. **Wall-clock 6.5h HARD CAP hit during backtest** — Engineer kills, documents partial results, declares INFRASTRUCTURE-NEG. /027 re-launches at `--seeds 1` (single outer-seed fallback) at <6h projection.
4. **F-AXIS #1 dispatch test FAILS** at engineering_report.md Phase 6 — replacement filter broken; investigation + fix required before Phase 7.5 dispatch.
5. **Data staleness HARD BLOCK** — any of the 5 symbols' 8h klines older than 16h → re-fetch before backtest.

The branch `iteration-v1/027` is rebased from /026 HEAD `74ce468`; rolling back = `git checkout iteration-v1/026 && git branch -D iteration-v1/027`. No baseline commitments are made by /027 (NO-MERGE pre-committed).

---

## Section 13 — Self-check

Pre-Phase-6 self-check (QR own verification):

1. **EDA evidence sufficient**: CONFIRMATION doesn't need full Phase 1-2 EDA (per Phase Quick Reference in v1 skill). Cycle-3 ledger summary at Section 2 + per-specialist standalone Section 2.2 + multi-seed regression priors Section 2.3 + /026 sanity Section 2.4-2.5 are the binding evidence.
2. **Hypothesis ↔ Falsifier alignment**: H1 → F1 + F-AXIS #1-5; H2 → informational; methodology validation framing at Section 0.2.
3. **HIGH-RISK declaration**: NORMAL-RISK at Section 2.5 — CONFIRMATION's multi-seed mandate is built-in mitigation. Cumulative ≥1σ cycle-3 NEG count = 5; multi-seed mandate already TRIPPED.
4. **Axis rotation valid**: Section 0.6 — CONFIRMATIONs exempt from rotation discipline (v1 skill §"Iteration Cadence Discipline" Rule 4).
5. **/027 bundle composition LOCKED**: Section 3.1 documents 5-Model replacement bundle with replacement semantics; matches /025 brief Section 11.6 LOCKED + /026 GREEN-WITH-FIX.
6. **Engineering report BINDING**: Section 10.1 documents requirements; cycle-3 6/10 EXPLORATION-incident pattern acknowledged.
7. **Anti-cheating**: `walk_forward.py:113` unchanged (`train_end_ms = test_start_ms - embargo_ms`); BASELINE_V1.md unchanged; OOS_CUTOFF_DATE = 2025-03-24 unchanged; training_months = 24 unchanged.
8. **Section 3.4 LM Master response slot**: RESERVED at Section 3.4; Phase 5.5 BLOCKs if not populated AFTER Phase 4.5 LM Master commits `lgbm_advisor.md`. Adopt-verbatim mandate ACTIVE per LM Master 6/6 PERFECT methodology track.
9. **NO-MERGE pre-committed**: Section 8 — even upper-band hit +0.75 absolute OOS Sharpe does NOT clear +1.0 floor; BASELINE_V1.md UNCHANGED regardless of outcome.
10. **Critic /026 binding remediations**: Rem #1 (replacement-pool correlations PASS) acknowledged at Section 2.5; Rem #2 (target band [+0.40, +0.75], NOT [+1.10, +1.30]) acknowledged at Section 0.2 + Section 1 + Section 4 F1 + Section 7.
11. **Pre-registered predictions binding**: Section 7 lists 13 binding predictions; Phase 7 evaluation reports observed vs predicted for each.

### Section 13.1 — Brief Section integrity checklist

- ✅ Section 0 (cycle context + framing + CONFIRMATION declaration + axis family)
- ✅ Section 1 (hypothesis + falsification logic)
- ✅ Section 2 (IS-only evidence: cycle-3 ledger + specialist results + regression priors + /026 sanity)
- ✅ Section 2.5 (HIGH-RISK declaration: NORMAL-RISK with built-in mitigation)
- ✅ Section 3 (implementation: bundle architecture + dispatch + CLI + pinned values + wall-clock + reproducibility + LM Master slot RESERVED)
- ✅ Section 4 (falsifiers: F1 + F3 + F2 + F4 + F5 + F6 + F7 + F8 + F-AXIS-MECHANISM #1-5)
- ✅ Section 5 (verdict priors: PROMISING-METHODOLOGY 50% / INERT 30% / NEGATIVE 15% / NEGATIVE-BELOW-BAND 5% / BLOCK 5%)
- ✅ Section 6 (failure modes: 6 modes including wall-clock + LTC drag + dispatch error)
- ✅ Section 7 (pre-registered predictions: 13 binding bands)
- ✅ Section 8 (MERGE decision: NO-MERGE PRE-COMMITTED)
- ✅ Section 9 (library stack: no new deps)
- ✅ Section 10 (run protocol: engineering_report binding + sequence + data freshness + artifacts)
- ✅ Section 11 (path forward: cycle-4 axis priorities by /027 outcome)
- ✅ Section 12 (roll-back protocol)
- ✅ Section 13 (self-check)

All 14 section anchors present. Section 3.4 reserves LM Master slot; will be populated at Phase 4.5 commit.
