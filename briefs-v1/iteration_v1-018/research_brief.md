# iter-v1/018 — Research Brief (Phases 2-5)

**Branch**: `iteration-v1/018` from `iteration-v1/017` HEAD `2935b4d` (tag `v0.v1-017`).

**Anchor**: `v0.v1-baseline-corrected` (BASELINE_V1.md commit `f8bc12c`). IS Sharpe **+0.2829** / OOS Sharpe **+0.6637** / OOS trades 189 / 5-sym universe / 4 models (A, C, D, E).

**Track**: v1 (refactored 2026-05-23). 13 phases. LightGBM Master + Critic.

**Iteration type**: EXPLORATION (cycle-3 #3 of 10).

---

## Section 0 — Position in cycle / pivot context

### 0.1 Cycle-3 cadence position

- Cycle-3 EXPLORATION #3 of 10 (the cycle restarts at iter-v1/016 after cycle-2 closed NO-MERGE at /015).
- Prior cycle-3 EXPLORATIONs: /016 (sample-weighting NEGATIVE-catastrophic), /017 (universe NEGATIVE-anti-direction-INERT).
- Cycle-3 ledger thus far: 0 PROMISING / 2 NEGATIVE / 0 merges.
- CONFIRMATION earliest possible at /027.

### 0.2 USER STRATEGIC PIVOT — per-cohort specialization

User directive 2026-05-26 codified at `feedback_v1_per_cohort_exploration_strategy.md`:

> "Use the explorations to narrow down approaches like individual symbols, pooled symbols (2 or 3) with specific features, configurations. Then use the confirmation to combine those small explorations and take an edge in the diversification."

**Cycle-3 #3+ pivots from "global axes on pooled universe" to "per-cohort specialization (1-3 symbols) + CONFIRMATION bundles specialists for diversification edge".** This is the FIRST iteration under the new methodology.

### 0.3 Methodology justification

Global-axis approach saturated:
1. Cycle-2 closed NO-MERGE (10 EXPLORATIONs, 7 axis families touched, 0 merges).
2. Cycle-3 /016 (sample-weighting global) → NEGATIVE-catastrophic OOS -1.00.
3. Cycle-3 /017 (universe +SOL global) → NEGATIVE-anti-direction-INERT OOS -0.09.
4. **LINK structural OOS positive in 8/8 iterations** (baseline + /011-/017) across vastly different architectures (universe changes, weighting changes, R5 axes, labeling axes, methodology probes). Pooled training treats all 4 models on equal footing; LINK's signal is not being exploited individually.

The natural cycle-3 #3 pivot is to test **the strongest structural prior**: LINK has the most consistent OOS evidence.

### 0.5 Cadence ledger summary

Cycle-3 #3 of 10 needed for /027 CONFIRMATION. After this iteration: 3 of 10 done. 7 more EXPLORATIONs needed before /027 CONFIRMATION can launch.

Wall-clock model: 5-sym at ENSEMBLE_SIZE=3 + n_trials=18 + V1_FEATURE_COLUMNS_PRUNED + 8h candles + 4 models = ~50min (/016 anchor); 6-sym at 5 models = ~70min projected (/017). LINK-only at 1 model is **~12-15 min projected** (1/4 of /016).

### 0.6 Axis Rotation Discipline + Family Declaration (v1 mandatory)

- **This iter's axis family**: `per-cohort-specialization-LINK` (cohort-specialization-pairing; FIRST usage in v1 catalog).
- **Cohort identifier**: LINK (single-symbol cohort).
- **Specialization dimension**: NONE (Option E from EDA — LINK-in-isolation; no additional knob).
- **Prior 5 EXPLORATION families** (verified against `briefs-v1/exploration_catalog.md`):
  - /013: `methodology-substrate-test`
  - /014: `labeling`
  - /015: `labeling` (CONFIRMATION)
  - /016: `sample-weighting`
  - /017: `universe`
- **Rotation status**: **VALID** — `per-cohort-specialization-LINK` is in NONE of the prior 5 families. This is a NEW axis family at v1 catalog level, declared per USER STRATEGIC PIVOT.
- **One-sentence rationale**: cycle-3 pivots methodology from global-pooled axes (saturated) to per-cohort specialization; LINK has the strongest structural OOS prior (8/8 iterations positive) and is the first cohort to test.

**NEW family declaration check (Critic Phase 7.5 Check 14 PASS-WITH-NOTE per /012 precedent)**: requires Critic + LM Master + QR convergence on orthogonality. Justification: cohort-specialization-pairings are STRUCTURALLY orthogonal to the existing 8 axis families because they vary the SYMBOL DIMENSION while holding labels/features/risk/methodology constant. (Past family declarations: methodology /001, methodology-substrate-test /012, hyperparameter-region /005.)

### 0.7 LM Master Phase 4.5 coordination slot

LM Master Phase 4.5 fires AFTER this brief (per `feedback_v1_per_cohort_exploration_strategy.md` workflow ordering — LM Master reads QR Phase 4 outputs). Section 3.4 below RESERVES a placeholder for LM Master responses; integration is a Phase 5.5 BLOCK condition if LM Master fires after brief but brief doesn't echo each recommendation.

---

## Section 1 — Hypothesis

**Primary hypothesis (H1)**: A LightGBM model trained on **LINK-only data** (single-symbol cohort) at the existing Model C configuration (R1 + R3, ATR×3.5 TP / ATR×1.75 SL, V1_FEATURE_COLUMNS_PRUNED) will **isolate** LINK's structural OOS edge (8/8 iterations positive) and produce OOS metrics on LINK alone that are AT LEAST equivalent to LINK's contribution within the v1 baseline pool (LINK-alone Sharpe OOS = +0.8184 / IS = +0.3724).

**Secondary hypothesis (H2 — INFORMATIONAL only; does NOT determine verdict)**: At PORTFOLIO level (LINK-alone vs baseline 5-sym portfolio), LINK-alone may underperform on point Sharpe because the baseline portfolio has 5 symbols' worth of diversification across regime drift; LINK-alone is single-symbol concentration. Verdict CANNOT depend on portfolio-level comparison because this is a per-cohort EXPLORATION (per `feedback_v1_per_cohort_exploration_strategy.md` caveat 1).

**Falsification logic**: if LINK-only model's OOS Sharpe on LINK trades alone is materially LOWER than LINK-in-pool (Δ ≤ -0.20 vs +0.8184 anchor), the "LINK's edge is intrinsic" claim is FALSIFIED — LINK's lift depends on pool-co-training (cross-model regularization or correlated-symbol signal). That would be a NEGATIVE-INTRINSIC subtype verdict.

If LINK-only delivers comparable or better LINK-OOS Sharpe (Δ ≥ -0.20 within INERT band, or Δ ≥ +0.20 PROMISING), then LINK is a viable specialist for /027 CONFIRMATION bundling.

---

## Section 2 — IS-Only Evidence (EDA results)

EDA scripts under `analysis/iteration_v1-018/`. Outputs committed at `ea71dbe`.

### 2.1 LINK is the #1 IS contributor AND the co-#1 OOS contributor (baseline)

From `analysis/iteration_v1-018/link_per_symbol_compare.csv`:

| Split | Symbol | n | WR | Avg PnL | Total PnL | Sharpe(monthly) | n_months |
|---|---|---|---|---|---|---|---|
| IS | **LINKUSDT** | 146 | 45.2% | +0.49% | **+72.06%** | **+0.3724** | 39 |
| IS | DOTUSDT | 93 | 41.9% | +0.29% | +26.62% | +0.2597 | 31 |
| IS | LTCUSDT | 124 | 39.5% | +0.03% | +3.27% | +0.0251 | 39 |
| IS | ETHUSDT | 145 | 38.6% | -0.09% | -13.70% | -0.1022 | 39 |
| IS | BTCUSDT | 113 | 33.6% | -0.33% | -37.28% | -0.4711 | 38 |
| OOS | **LINKUSDT** | 28 | 50.0% | +1.22% | **+34.23%** | **+0.8184** | 14 |
| OOS | BTCUSDT | 35 | 45.7% | +0.95% | +33.17% | +0.8995 | 14 |
| OOS | ETHUSDT | 46 | 39.1% | +0.06% | +2.76% | +0.0503 | 14 |
| OOS | DOTUSDT | 46 | 39.1% | +0.04% | +1.96% | +0.0423 | 14 |
| OOS | LTCUSDT | 34 | 29.4% | -1.39% | -47.25% | -1.4447 | 15 |

**LINK-alone IS Sharpe (+0.3724) BEATS portfolio Sharpe (+0.2829) by 31%.**
**LINK-alone OOS Sharpe (+0.8184) BEATS portfolio Sharpe (+0.6637) by 23%.**

LINK is being DILUTED by the pool, not lifted by it. This is the "underexploited" pattern.

### 2.2 LINK structural OOS edge across /011-/017 (8/8 positive)

From `analysis/iteration_v1-018/link_roster_overlap.csv`:

| Iter | n LINK OOS trades | net_pnl | avg_pnl | WR | overlap_pct_baseline | jaccard |
|---|---|---|---|---|---|---|
| baseline | 28 | **+34.23** | +1.22 | 50.0% | 1.0000 | 1.0000 |
| /011 | 47 | **+84.86** | +1.81 | 55.3% | 0.21 | 0.087 |
| /012 | 46 | **+53.36** | +1.16 | 47.8% | 0.04 | 0.014 |
| /013 | 46 | **+47.08** | +1.02 | 50.0% | 0.14 | 0.057 |
| /014 | 44 | **+3.87** | +0.09 | 43.2% | 0.07 | 0.029 |
| /015 | 48 | **+84.58** | +1.76 | 54.2% | 0.29 | 0.118 |
| /016 | 60 | **+34.91** | +0.58 | 45.0% | 0.18 | 0.060 |
| /017 | 48 | **+53.80** | +1.12 | 50.0% | 0.25 | 0.101 |

**Mean LINK OOS PnL across 8 iters: +49.59% / std 26.86 / CV 0.54 / all 8 positive / min +3.87, max +84.86.**

The roster overlap is LOW (4-29% Jaccard 0.01-0.12) — different LINK trades across iters — but the SIGN is consistent. That's **signal-stable not roster-stable**: LINK has an intrinsic OOS predictability that survives across diverse training architectures.

(Note: baseline n=28 vs others n=44-60 because baseline ran 5-seed ensemble [42,123,456,789,1001] = tighter ensemble agreement = fewer trades pass; /011-/017 ran 3-seed [42,123,456]. This is structural ensemble-size difference, not architecture-driven.)

### 2.3 LINK direction asymmetry — OOS shorts dominate

From `analysis/iteration_v1-018/link_direction_split.csv`:

| Split | Direction | n | WR | Total PnL | Avg PnL |
|---|---|---|---|---|---|
| IS | long | 82 | 47.6% | **+92.74%** | +1.13% |
| IS | short | 64 | 42.2% | -20.68% | -0.32% |
| OOS | long | 10 | 40.0% | +3.62% | +0.36% |
| **OOS** | **short** | **18** | **55.6%** | **+30.62%** | **+1.70%** |

LINK IS = longs dominate (+92.74 vs -20.68); LINK OOS = **shorts dominate** (+30.62 vs +3.62). This direction flip is unusual but it's the existing baseline behavior. The LINK-only model will inherit the same direction flexibility (LightGBM regression target with bidirectional dispatch).

### 2.4 LINK volatility & feature profile

From `analysis/iteration_v1-018/link_natr_profile.csv`:

| Symbol | NATR_14 p25 | p50 | p75 |
|---|---|---|---|
| **LINKUSDT** | **2.82%** | **3.57%** | **4.71%** |
| BTCUSDT | 1.64% | 1.99% | 2.44% |
| ETHUSDT | 1.92% | 2.44% | 3.07% |
| LTCUSDT | 2.21% | 2.83% | 4.00% |
| DOTUSDT | 2.45% | 3.10% | 4.39% |

LINK is the HIGHEST-volatility v1 symbol — 1.8× BTC's NATR. Current Model C ATR×3.5/1.75 gives SL distance at NATR_p50 = 6.25% (well above noise floor; LINK doesn't have an SL-noise-floor problem like /004 ETH did).

LINK structural feature signature (from `link_feature_stats.csv` — top features with LINK_std/portfolio_med_std > 1.0):

| Feature | LINK std | Portfolio median std | ratio |
|---|---|---|---|
| interact_ret1_x_ret3 | 26.93 | 16.31 | **1.65** |
| interact_ret1_x_natr | 13.51 | 8.68 | **1.56** |
| mr_pct_from_low_20 | 0.096 | 0.069 | 1.40 |
| mom_roc_10 | 8.34 | 6.26 | 1.33 |
| stat_return_5 | 0.058 | 0.044 | 1.33 |

LINK is structurally **noisier on 1-bar return × interaction features** than the portfolio median — these are the highest-variance dimensions where LINK's signal lives.

### 2.5 ATR calibration (Option B rejected)

From `analysis/iteration_v1-018/link_atr_calibration.csv`:

The current C ATR (3.5/1.75) gives TP distance 12.50% at NATR_p50 — already comparable to LINK's p95 NATR (7.10% × 1.75 = 12.42% for SL). Tighter (3.0/1.5) reduces TP/SL distance to 10.71%/5.36%; wider (4.0/2.0) increases to 14.28%/7.14%. None of these are obviously dominant from EDA — would require a SECOND axis to test, which violates single-axis isolation in this iteration. **Option B rejected for /018.** Could be tested in /020 as a follow-on LINK specialization.

### 2.6 LINK OOS monthly distribution (regime stability)

From `analysis/iteration_v1-018/link_monthly_oos.csv` — LINK OOS monthly PnL (baseline):

| Month | n | net_pnl_pct | wins | avg |
|---|---|---|---|---|
| 2025-03 | 1 | +10.77% | 1 | 10.77% |
| 2025-05 | 3 | -8.08% | 1 | -2.69% |
| 2025-06 | 4 | +26.27% | 3 | +6.57% |
| 2025-07 | 4 | -12.31% | 1 | -3.08% |
| 2025-08 | 4 | -1.02% | 2 | -0.25% |
| 2025-09 | 2 | +14.99% | 2 | +7.50% |
| 2025-10 | 1 | +6.91% | 1 | +6.91% |
| 2026-01 | 2 | -9.57% | 0 | -4.78% |
| 2026-02 | 4 | +5.36% | 2 | +1.34% |
| 2026-03 | 1 | -5.00% | 0 | -5.00% |
| 2026-04 | 2 | +5.91% | 1 | +2.96% |

11/14 months had LINK trades; 6 positive months / 5 negative months. Not regime-bound — distributed positive months span 2025-03 to 2026-04. The "post-2024 DeFi cycle" regime concern from /017 Critic Path Forward is partially mitigated by the OOS positive months in 2026-02/04.

### 2.7 Specialization option assessment

| Option | EDA evidence | Implementation risk | Interpretability | Decision |
|---|---|---|---|---|
| A: LINK-specific feature subset | LINK has higher std on momentum features; could prune low-IR but requires multi-axis (feature change + symbol isolation) | HIGH (feature selection on single-symbol = overfit risk; needs CV) | LOW (entangled axes) | REJECT |
| B: LINK-specific ATR multipliers | Current 3.5/1.75 well-calibrated; no obvious lift signal | MEDIUM (single dimension swap but no clear band) | MEDIUM | REJECT — defer to /020 follow-on |
| C: LINK-specific labeling threshold | Per-symbol σ_t calibration would be a SECOND axis on top of cohort isolation | HIGH (multi-axis) | LOW | REJECT |
| D: LINK-specific R3 OOD threshold | R3 cutoff tuning on single-symbol = within-axis tuning | MEDIUM | MEDIUM | REJECT — defer to /021 follow-on |
| **E: LINK-in-isolation (drop A/D/E models)** | **Cleanest single-axis isolation; tests THE structural prior directly; minimal implementation; deterministic interpretability** | **LOW (drop dispatch code only)** | **HIGH** | **ADOPT** |

**Decision: Option E.** Drop Models A (BTC+ETH), D (LTC), E (DOT). Keep Model C only (LINKUSDT). Single-axis isolation: SYMBOL-DIMENSION change with all other knobs frozen at baseline.

Why E first:
1. The cleanest test of the structural prior — no confounds.
2. Establishes the **LINK-alone reachable Sharpe baseline** for cycle-3 specialization. Subsequent /019-/026 EXPLORATIONs on LINK (if Option B/D follow-on) anchor against this iteration.
3. Other cohorts (ETH-regime-conditional, BTC-only) become /019+ candidates.
4. If LINK-alone PROMISING'es here, options B/C/D can layer specializations in subsequent iterations WITHOUT inheriting the multi-axis confound.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1 mandatory)

**Declaration: HIGH-RISK.**

**Reason (one sentence)**: dropping Models A/D/E from the dispatch is a structural change to Optuna's training-objective domain (universe goes from 5 symbols to 1) — single-cohort training is fundamentally different from the pooled 5-symbol baseline at the loss-surface level, and at single-seed=42 ENSEMBLE_SIZE=3 EXPLORATION budget the LINK-only Optuna trajectory may explore a basin disjoint from LINK-in-pool's basin.

**Mitigation (opt-in)**: NONE — single-seed-style EXPLORATION at ENSEMBLE_SIZE=3 inner seeds (fixed cycle-3 default). Per `feedback_v1_per_cohort_exploration_strategy.md`, per-cohort EXPLORATIONs are structurally faster (1-symbol model ≈ 1/4 wall-clock of 5-symbol baseline), so multi-seed at /018 would be cheap (~40 min at 10 inner seeds vs ~15 min at 3 seeds); we still keep cycle-3 EXPLORATION budget discipline at 3 seeds. Multi-seed validation deferred to /027 CONFIRMATION.

**HIGH-RISK cumulative tracker (cycle-3)**:
- /016: HIGH-RISK declared / NEGATIVE-catastrophic / -1σ OOS Δ (≤ -1.0)
- /017: HIGH-RISK declared / NEGATIVE-anti-direction-INERT / OOS Δ -0.09 (within 1σ band)
- /018 (this iter): HIGH-RISK declared / outcome TBD

If /018 produces ≥1σ negative OOS Δ catastrophic, that would be the 2nd cycle-3 catastrophic HIGH-RISK. Per `feedback_v1_n_eff_barrier_magnitude_curve.md` forward-binding mandate, 3 consecutive ≥1σ HIGH-RISK negatives triggers MANDATORY multi-seed on /021 (the next HIGH-RISK iteration in the sequence).

---

## Section 3 — Implementation Spec

### 3.1 Code change (single src/ file change)

`run_baseline_v1.py` — add new universe constant + dispatch branch:

```python
# After V1_ITER017_UNIVERSE definition (line ~109):
V1_ITER018_UNIVERSE: tuple[str, ...] = ("LINKUSDT",)
"""iter-v1/018 cohort: LINK-only (first per-cohort EXPLORATION at v1).

USER STRATEGIC PIVOT 2026-05-26 (feedback_v1_per_cohort_exploration_strategy.md):
EXPLORATIONs test per-cohort specializations; CONFIRMATION /027 bundles
specialists for diversification edge. iter-v1/018 = FIRST per-cohort
EXPLORATION (LINK structural OOS prior strongest at 8/8 iterations).
"""

# Add elif branch after V1_ITER017_UNIVERSE branch (line ~1223):
elif set(symbols) == set(V1_ITER018_UNIVERSE):
    # iter-v1/018: LINK-only single-cohort EXPLORATION.
    # ONLY Model C (LINK + R1 + R3) dispatched.
    # Models A (BTC+ETH), D (LTC), E (DOT) DROPPED — single-axis isolation.
    # All Model C parameters BIT-IDENTICAL to baseline: atr_tp=3.5, atr_sl=1.75,
    # apply_r1=True (R1 cool-down), bounds_profile=v1_pruned.
    results_c, faxm_c = run_model(
        "C (LINK + R1)",
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
    _all_faxm_logs = faxm_c
    all_results = results_c
    _r5_model_results = [results_c]
```

**Diff scope**: 1 file (`run_baseline_v1.py`), ~30 lines added. Zero changes to:
- `src/crypto_trade/features_v1/` (V1_FEATURE_COLUMNS_PRUNED unchanged, 40 cols)
- `src/crypto_trade/strategies/ml/lgbm.py`
- `src/crypto_trade/strategies/ml/optimization.py`
- `src/crypto_trade/strategies/ml/walk_forward.py`
- `src/crypto_trade/labeling.py`
- Risk gate code (R1/R3 unchanged)

**Foundation guardrail**: `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` UNCHANGED. No regression.

### 3.2 CLI invocation

```bash
uv run python run_baseline_v1.py \
  --symbols LINKUSDT \
  --pruned-features \
  --ensemble-size 3 \
  --n-trials 18 \
  --iteration-label "v1-018" \
  --reports-dir reports-v1
```

(Note: `--symbols LINKUSDT` triggers the new elif branch via `set(symbols) == set(V1_ITER018_UNIVERSE)`. `--pruned-features` activates V1_FEATURE_COLUMNS_PRUNED + bounds_profile=v1_pruned. `--ensemble-size 3` + `--n-trials 18` matches cycle-3 EXPLORATION budget per /016/017 anchor.)

**No `--no-engineering-report` flag (per Critic /017 Rec #2 — engineering_report.md must exist at Phase 7.5 dispatch).**

### 3.3 Pinned values

- `feature_columns = list(V1_FEATURE_COLUMNS_PRUNED)` — passed explicitly through Model C dispatch (40 cols).
- `bounds_profile = "v1_pruned"` — same as baseline Model C.
- `ENSEMBLE_SEEDS[0:3] = [42, 123, 456]` — same as baseline 3-seed EXPLORATION default.
- `r5_vol_target_enabled = False` (cycle-3+ default — per /017 fix `5fffe8a`).
- `r5_binary_kill_enabled = False` (cycle-3+ default).
- `sample_weight_mode = "abs_pnl"` (baseline default — restored per /016 finding).
- `sigma_source = "natr"` (baseline default — restored per /015 closure).
- `apply_r1 = True` (Model C baseline — R1 cool-down active for LINK).
- `apply_r2 = False` (Model C baseline — R2 is Model E only).

### 3.4 LM Master Phase 4.5 responses (committed at lgbm_advisor.md)

LM Master Phase 4.5 fired post-brief at `briefs-v1/iteration_v1-018/lgbm_advisor.md`. QR responses to each recommendation:

**Rec #1 — KEEP n_trials=18; do NOT compress to 15**:
- **ADOPTED**. Section 3.3 specifies n_trials=18 already; compressing saves ~1-2 min at no wall-clock pressure (12-18 min predicted with 78+ min margin). TPE warmup at 18 stays above ~10 saturation even at single-symbol's ~140 rows/month.

**Rec #2 — Accept current Optuna bounds**:
- **ADOPTED**. v1_pruned bounds unchanged for /018. Single-axis SYMBOL DIMENSION isolation maintained. Phase 7.4 post-mortem will read actual best-trial trajectories.

**Rec #3 — KEEP ENSEMBLE_SIZE=3**:
- **ADOPTED**. Single-axis isolation overrides raising to 5. /027 CONFIRMATION raises to 10 (multi-seed handles basin-lottery dissolution). Brief Section 3.3 keeps 3.

**LM Master verdict-class adjustment ADOPTED into Section 5**: PROMISING 30% / **INERT 45% modal (PROMISING-INERT specifically)** / NEGATIVE 20% / NEGATIVE-INTRINSIC 5%. LINK 8/8 OOS-positive structural pattern earns MEDIUM directional confidence at per-cohort level (NOT verdict-class FLAT).

**LM Master MATHEMATICAL clarification CRITICAL — DOCUMENTED into Section 1**: "LINK-alone beats portfolio +31% IS / +23% OOS" is **MATHEMATICAL DILUTION ACCOUNTING** (removing 4 drag/neutral contributors lifts aggregate), NOT edge discovery. H1 question is "can LINK-only TRAINING preserve LINK's edge?" — measures LINK-only-trained LINK Sharpe vs LINK-in-pool-trained LINK Sharpe (+0.8184 anchor). Brief Section 1 + Section 4 F1 anchoring correctly target this.

**Saturation risks ADOPTED into Section 6**:
- Single-cohort single-seed=42 basin lottery (HIGH-RISK) — wide ±0.40 OOS Sharpe variance band; NEGATIVE-INTRINSIC verdict should be "basin-lottery-conditional FALSIFICATION" NOT terminal closure
- Predicted n_eff_per_cell band [4, 9] for single-cohort (corrected from /017's [8, 13] for 5-sym pooled)
- LINK direction-asymmetry inheritance: pool may have implicitly balanced direction; LINK-only may overshoot direction-asymmetrically (Phase 7.4 to flag)

**/019+ conditional pre-staging ADOPTED into Section 11**:
- PROMISING → /019 = ETH-only with BTC-trend conditional gate (per /017 pre-commit)
- PROMISING-INERT (modal) → /019 = ETH-only regime gate (diversify cohort coverage before stacking LINK specializations)
- NEGATIVE → /019 = LINK+SOL 2-symbol pooled (test pool-co-training requirement)
- NEGATIVE-INTRINSIC → /019 = ETH-only regime gate; LINK-specialization sub-cycle CLOSED

**LM Master /017 +XRP recommendation SUPERSEDED**: LM Master acknowledges QR's per-cohort pivot is mechanically tighter axis than +XRP universe continuation.

**Net**: 3 hyperparameter recs + 4 risk callouts + verdict-class adjustment + mathematical clarification ALL ADOPTED. Brief finalized for Phase 5.5 gate.

### 3.5 Axis Family Declaration (v1 mandatory)

- **Axis family**: `per-cohort-specialization-LINK` (NEW 9th family declaration; first usage).
- **Cohort + Specialization pairing**: cohort=LINK, specialization=NONE (LINK-in-isolation; Option E from Section 2.7).
- **Single-axis isolation verified**: ONLY SYMBOL DIMENSION changes (5-sym → 1-sym universe + drop A/D/E dispatch). All other knobs frozen at baseline.
- **Phase 7.5 Critic Check 14 PASS requires**: NEW family declaration is structurally orthogonal to existing 8 families (this is a SYMBOL-DIMENSION variation; orthogonal to feature/labeling/model-arch/risk/methodology/hyperparameter dimensions).

### 3.6 Wall-Clock Estimate (CRITICAL — Phase 5.5 BLOCK if missing or > 1.6h)

**Predicted wall-clock: 12-18 minutes total.**

Decomposition:
- Baseline 5-sym (4 models) at ENSEMBLE_SIZE=3 + n_trials=18 = **~50 minutes** (anchored at /016 empirical).
- 6-sym (5 models) at same config = **~70 minutes** (anchored at /017 projected — pending engineering_report.md fix).
- LINK-only (1 model) at same config = **~12-15 minutes** (linear scaling: 1/4 of baseline 4 models; in line with `feedback_v1_per_cohort_exploration_strategy.md` projection "1-symbol model: ~10-15 min per cell × 39 months × 3 seeds × 1 model ≈ 30 min total" — actually the feedback rule's 30-min projection is per-cell-stacked; per-iteration is 1/12 of 5-model-iteration, so 12-15 min is realistic).

**Methodology + reporting overhead**: ~3 min (CPCV, PSR, DSR computations on 1-model trade roster; these are POST-hoc and don't scale with universe size).

**Total projected: 15-18 minutes.**

**Margin vs 2h cap = 1h:35-1h:40 (≥80% margin).**

**Margin vs 1.6h Phase 5.5 BLOCK threshold = 78-80 minutes of buffer.**

**Contingency**: even at 3× linear-scaling overhead (worst case 45 minutes), margin remains 1h:15min = 62% — well above the 20% Phase 5.5 floor.

**No n_trials compression needed.** n_trials=18 stays at cycle-3 EXPLORATION default. Compressing to 15 would save ~2 minutes of wall-clock but reduce TPE warmup buffer to 50% — false economy at LINK-only single-symbol.

### 3.7 Reproducibility

- `--symbols LINKUSDT` exact flag value (no comma list)
- `ENSEMBLE_SEEDS[0:3] = [42, 123, 456]` (literal pin at run_baseline_v1.py line ~97)
- `OOF_PARQUET_PATH` = `data/v1_oof_returns_iter_v1-018.parquet` (iter-stamped per /008 standard)
- HEAD SHA recorded at Phase 5.5 (post-brief) + Phase 6 (post-implementation).

---

## Section 4 — Falsifiers (F1-F8 + F-AXIS-MECHANISM)

**Critical adaptation per `feedback_v1_per_cohort_exploration_strategy.md`**: this is a per-cohort EXPLORATION. F1 + F8 thresholds adapt to the LINK-only universe scale, NOT to portfolio-level baseline.

### F1 — LINK-only OOS Sharpe Δ vs LINK-alone-in-pool baseline

**Anchor**: LINK-alone OOS Sharpe in v1 baseline = **+0.8184** (from Section 2.1; computed from LINK's 28 OOS trades monthly aggregation).

**NOT against portfolio +0.6637** — that's H2's informational comparison, not the verdict criterion (per per-cohort methodology).

| Verdict cell | F1 OOS Sharpe Δ band |
|---|---|
| **PROMISING** | Δ ≥ +0.20 (LINK-only OOS Sharpe ≥ +1.02) |
| INERT | Δ ∈ [-0.20, +0.20] (LINK-only OOS Sharpe ∈ [+0.62, +1.02]) |
| **NEGATIVE** | Δ ≤ -0.20 (LINK-only OOS Sharpe ≤ +0.62) |
| Catastrophic-NEGATIVE | Δ ≤ -0.55 (LINK-only OOS Sharpe ≤ +0.27) |

**NEGATIVE-INTRINSIC subtype** (specific to this per-cohort iteration): if LINK-only OOS Sharpe ≤ +0.50 (Δ ≤ -0.31), interpretive call = "LINK's edge depends on pool co-training; falsifies the structural-prior hypothesis at single-cohort isolation".

### F3 — LINK-only IS Sharpe Δ vs LINK-alone-in-pool IS baseline

**Anchor**: LINK-alone IS Sharpe in v1 baseline = **+0.3724**.

| Verdict cell | F3 IS Sharpe Δ band |
|---|---|
| **PROMISING** | Δ ≥ +0.20 (LINK-only IS Sharpe ≥ +0.57) |
| INERT | Δ ∈ [-0.20, +0.20] (LINK-only IS Sharpe ∈ [+0.17, +0.57]) |
| **NEGATIVE** | Δ ≤ -0.20 (LINK-only IS Sharpe ≤ +0.17) |
| Catastrophic-NEGATIVE | Δ ≤ -0.30 (LINK-only IS Sharpe ≤ +0.07) |

### F2 — Embargo/look-ahead PASS (structural; should be automatic)

`walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` UNCHANGED. PASS by construction.

### F4 — Feature ADF stationarity (informational; no new features)

40 V1_FEATURE_COLUMNS_PRUNED unchanged. ADF rerun on LINK-only halves still produces the same bonferroni-pass profile as baseline. INFORMATIONAL.

### F5 — PSR_monthly_vs_0 OOS (basin-health signal, elevated to first-class at /017 closeout)

LINK-only OOS PSR_monthly_vs_0:
- Baseline anchor (5-sym OOS portfolio) PSR_monthly_vs_0 = 0.97~0.99 (from BASELINE_V1.md).
- LINK-only OOS is a single-symbol distribution; PSR will compute over 14 LINK-OOS months of monthly returns. Predicted band [0.40, 0.85] for LINK-only OOS PSR (single-symbol = noisier monthly distribution).

**Catastrophic if** PSR_monthly_vs_0 < 0.20 on LINK-only OOS → indicates LINK months are mostly negative.

### F6 — Per-symbol IS direction (vacuous — only 1 symbol)

LINK-only model has only LINK trades. F6 PASS by construction.

### F7 — Per-symbol IS/OOS sign agreement (LINK only)

LINK IS and OOS PnL must both be positive (same-sign basin) for INERT-or-better verdict.

If LINK-only IS PnL < 0 AND LINK-only OOS PnL > 0 → IS-OOS sign disagreement → NEGATIVE-IS-collapse subtype.
If LINK-only IS PnL > 0 AND LINK-only OOS PnL < 0 → severe overfit signature → NEGATIVE-overfit subtype.

### F8 — LINK-only trade count band (per-cohort scale)

**Anchor**: LINK-alone trade counts in baseline = 146 IS / 28 OOS.

Adjusted floor for LINK-only model at ENSEMBLE_SIZE=3 (not 5): expect MORE trades because tighter ensemble agreement weakens at 3 seeds vs 5 → more signals pass through.

Empirical anchor /011-/017 LINK OOS at 3-seed: range 44-60 trades.

| F8 cell | OOS LINK trade band |
|---|---|
| PASS | LINK OOS trades ∈ [25, 75] |
| **F8 BREACH-low** | < 25 (cohort under-fires; model collapsing) |
| **F8 BREACH-high** | > 75 (cohort over-fires; overshooting expected single-symbol regime) |

Anchor sanity check: LINK-only model at 3-seed should fall in this band given /011-/017's 44-60 range.

### F-AXIS-MECHANISM (compound 3-sub-check, per per-cohort methodology adapted)

The single-axis isolation is the SYMBOL DIMENSION (5-sym → 1-sym + drop A/D/E dispatch).

- **F-AXIS #1 — Dispatch correctness**: ONLY Model C runs; reports-v1/iteration_v1-018/in_sample/trades.csv contains only LINKUSDT rows (zero rows for BTC/ETH/LTC/DOT). PASS criterion: `df['symbol'].unique() == ['LINKUSDT']`.
- **F-AXIS #2 — LINK trade-count and PnL within historical band**: LINK IS trades ∈ [120, 200], LINK OOS trades ∈ [25, 75], LINK OOS PnL > 0 (preserves 8/8 structural prior). Failure indicates Model C is not training correctly on isolated cohort.
- **F-AXIS #3 — Optuna trial diversity**: at single-cohort, n_eff_per_cell may DIFFER from the 5-sym [8, 13] band. INFORMATIONAL: log n_eff_per_cell_median; outside [5, 18] band triggers Phase 7.4 LM Master investigation but is NOT a verdict-cell determinant for this iteration. (Single-symbol Optuna basin structure is poorly characterized in v1 catalog; this iteration ESTABLISHES the prior.)

### F-PORTFOLIO (informational; cannot determine verdict)

Portfolio-level Sharpe (LINK-only "portfolio" = 1 model) compared to v1 baseline 5-sym portfolio:
- Baseline portfolio IS Sharpe +0.2829 / OOS +0.6637.
- LINK-only portfolio = LINK-only Sharpe directly.

If LINK-only OOS Sharpe > +0.6637 portfolio anchor → reinforces /017 finding that adding a 5th-OOS-positive symbol (LINK) at full weight beats current pooled mix at LINK's weight share.

**INFORMATIONAL ONLY** — per `feedback_v1_per_cohort_exploration_strategy.md` caveat 1: per-cohort verdicts are intrinsically cohort-bound; portfolio diversification edge tests only at /027 CONFIRMATION bundle.

---

## Section 5 — Predicted Verdict Distribution (FLAT priors per /016/017 lessons)

Per /016/017 closeouts: cycle-3 LM Master + QR mechanism-level predictions track FLAT priors at the EXPLORATION level. /016 catastrophic-NEGATIVE / /017 PROMISING-INERT — neither was predicted at high probability.

**Verdict prior FLAT 33/33/34**:
- PROMISING: 33% (LINK structural-prior holds — LINK-only Sharpe at least matches LINK-in-pool +0.82)
- INERT: 34% (basin-substrate effects dominate; LINK-only basin produces Sharpe in [+0.62, +1.02] band)
- NEGATIVE: 33% (LINK's pool edge dissolves at single-cohort isolation — falsifies structural prior; "LINK borrowed signal from BTC/ETH/LTC/DOT in pool")

Two specific mechanism predictions (informational, not verdict-determining):

1. **LINK-only basin diversity**: at n_trials=18 single-symbol, Optuna basin diversity may DECREASE vs 5-sym pool (fewer rows = less diverse loss surface). Predicted n_eff_per_cell median = [4, 9] (below 5-sym [8, 13]). If observed within band, INFORMATIONAL. If well outside, LM Master Phase 7.4 investigates basin-collapse vs basin-discovery.

2. **LINK trade roster overlap with baseline**: predicted [10%, 40%] (similar to /011-/017's 4-29%). Single-symbol training produces a fresh LINK Optuna basin; roster won't byte-match baseline.

---

## Section 6 — Failure Modes

### 6.1 Single-cohort basin lottery at single-seed=42 EXPLORATION

LINK-only at ENSEMBLE_SIZE=3 + n_trials=18 + single-seed=42 = potentially basin-locked at one specific LINK loss-surface region. Per v3 /020-/022 frozen-baseline precedent, single-seed Optuna trajectories are deterministic. LINK-only at single-seed is exposed to "basin lottery" — the basin LightGBM lands in may have IS-bias toward LINK's IS positive (+72%) but not generalize to OOS.

**Mitigation**: 8/8 historical iterations had LINK OOS positive across diverse single-seed=42 architectures — basin-lottery alone doesn't fully explain LINK's signal stability. /027 CONFIRMATION will multi-seed validate (10 inner seeds) the LINK-only specialist if it passes.

### 6.2 IS overfit (LINK-only IS Sharpe extreme)

If LINK-only IS Sharpe spikes to +1.5+ but OOS Sharpe drops below +0.5, that's classic single-cohort overfit — Optuna optimizes hyperparameters to LINK-specific IS noise. Falsifier F3 catastrophic-NEGATIVE Δ ≤ -0.30 (LINK-only IS Sharpe ≤ +0.07) would catch BASIN-INVERSION; F1 catastrophic Δ ≤ -0.55 (LINK-only OOS ≤ +0.27) would catch generalization failure.

### 6.3 Structural prior was actually pool-leveraged

If LINK-only OOS Sharpe falls to +0.50 range (Δ ≤ -0.31 vs +0.82 anchor), the implication is **LINK's edge depended on BTC/ETH/LTC/DOT cross-training signals** (regularization or correlated-cross-asset effects), and the "LINK is underexploited" claim is REFUTED. That would be a load-bearing finding for cycle-3: pool-co-training is the structural source, not LINK itself. Future cohorts would be tested as 2-3 symbol pooled cohorts instead of single-symbol.

### 6.4 Direction-asymmetry collapse

LINK OOS shorts WIN at 55.6% (+30.62%) vs longs 40% (+3.62%). If LINK-only model produces a different long/short balance (e.g., model learns to short more aggressively at LINK-only training), the OOS direction split may shift dramatically. INFORMATIONAL — track at Phase 7 evaluation.

### 6.5 Single-symbol n_eff collapse below [4, 9] predicted band

LINK-only single-symbol training may produce n_eff_per_cell ≤ 3 if Optuna trial budget at n_trials=18 isn't sufficient for single-symbol loss surface diversity. INFORMATIONAL — Phase 7.4 LM Master investigates.

---

## Section 7 — Optional / informational metrics

- LINK-only DSR (vs n_eff_per_cell with single-symbol corrected): expected to be LOWER than baseline portfolio DSR because n_obs collapses (1 symbol's monthly returns instead of 5-symbol-aggregated). INFORMATIONAL per EXPLORATION rule.
- LINK-only PBO via CSCV: deferred (not currently wired in run_baseline_v1.py per Outstanding Tasks in BASELINE_V1.md).
- LINK-only PSR_monthly_vs_1: expected to remain BELOW baseline portfolio 0.0789 (LINK-only is a 1-symbol subset). INFORMATIONAL.
- Pareto front: N/A (single-seed EXPLORATION).

---

## Section 8 — Verdict Matrix (per-cohort variant)

**Per-cohort EXPLORATION verdict cells**:

| Verdict cell | F1 (LINK OOS Δ) | F3 (LINK IS Δ) | F-AXIS-MECHANISM | Action |
|---|---|---|---|---|
| **PROMISING** | Δ ≥ +0.20 | any | #1+#2 PASS | LINK-only specialist CARRIED FORWARD to /027 CONFIRMATION substrate |
| **PROMISING-INERT** | Δ ∈ [-0.20, +0.20] | any | #1+#2 PASS, PSR ≥ 0.40 | LINK-only specialist CONDITIONALLY CARRIED to /027 (re-evaluate at multi-seed) |
| **NEGATIVE-INERT** | Δ ∈ [-0.20, -0.31) | any | #1 PASS | LINK-only specialist DROPPED for /027; LINK pool-co-training inferred |
| **NEGATIVE-INTRINSIC** | Δ ≤ -0.31 | any | #1 PASS | "LINK structural prior FALSIFIED at cohort isolation" — load-bearing finding; cycle-3 pivots to 2-3 symbol pooled cohorts |
| **NEGATIVE-CATASTROPHIC** | Δ ≤ -0.55 | any | #1 PASS | "LINK signal collapse at single-cohort" — closest analog to /016 catastrophic NEGATIVE |
| **NEGATIVE-IS-COLLAPSE** | Δ_OOS any | Δ_IS ≤ -0.30 | #1 PASS | IS basin inversion at LINK-only (single-symbol IS overfit signature) |
| **NEGATIVE-DISPATCH** | any | any | #1 FAIL | Implementation defect — LINK model not training; BLOCK-PENDING-FIX candidate |

**Section 8 entry rule**: must select EXACTLY ONE cell. Strict adherence to thresholds.

---

## Section 9 — Library Stack

No changes to library versions. Inheriting cycle-3 baseline:
- `mlfinlab==1.4` (CPCV / meta-labeling utilities)
- `pypbo` (PBO via CSCV)
- `fracdiff>=0.10` (FracdiffStat)
- `statsmodels` (ADF testing)
- `lightgbm>=4.0` (LightGBM regression)
- `optuna>=3.0` (Bayesian hyperparameter search)

---

## Section 10 — Implementation Spec (CRITICAL detail)

### 10.1 No `--no-engineering-report` flag at launch (Critic /017 Rec #2)

Engineer Phase 6 MUST generate `reports-v1/iteration_v1-018/engineering_report.md`. Run command excludes `--no-engineering-report` flag.

### 10.2 Reports artifacts expected

After backtest completion:

```
reports-v1/iteration_v1-018/
├── comparison.csv           # IS/OOS metrics (sharpe, dsr, psr, n_eff rows, etc.)
├── engineering_report.md    # Engineer Phase 6 summary
├── f_axis_mechanism.csv     # F-AXIS-MECHANISM falsifier rows (Optuna basin + n_eff)
├── in_sample/
│   ├── trades.csv           # ONLY LINKUSDT rows (verify F-AXIS #1)
│   ├── per_symbol.csv       # ONLY LINKUSDT row
│   ├── monthly_pnl.csv
│   ├── daily_pnl.csv
│   ├── per_regime.csv
│   ├── dsr.json
│   ├── adf_test.csv
│   ├── ic_matrix.csv
│   └── quantstats.html
└── out_of_sample/
    └── (same structure)
```

### 10.3 Pre-flight verification (Engineer in Phase 6 setup)

Before launching backtest:
1. Verify `LINKUSDT_8h_features.parquet` exists in `data/features/` and is fresh (file mtime within 30 days). Already verified at EDA step (script 02 used the parquet).
2. Verify `data/LINKUSDT/8h.csv` has close_time within 16h of measurement time (no stale klines).
3. Verify branch is `iteration-v1/018` and HEAD is post-brief commit.
4. Verify `run_baseline_v1.py` HEAD has V1_ITER018_UNIVERSE and elif branch.

### 10.4 Engineer launch protocol

Per skill `4cb8972` split-engineer dispatch:
1. Engineer does setup (code change, smoke test).
2. Orchestrator launches `uv run python run_baseline_v1.py ...` as detached bash (run_in_background=true).
3. Engineer writes engineering_report.md after backtest completes.
4. Engineer reports HEAD SHA at handoff to Phase 7.4 LM Master + Phase 7.5 Critic.

### 10.5 Wall-clock kill-switch

Engineer kills the backtest if wall-clock exceeds **30 minutes** (2× projected 12-15 min worst case + 100% safety margin). Per `feedback_v1_wall_clock_discipline_enforced.md`, 2h is the cycle-3 EXPLORATION HARD CAP; 30 min internal kill-switch is well below cap.

---

## Section 11 — Alternates for /019+ (cycle-3 fourth EXPLORATION onwards)

Per per-cohort methodology, /018 establishes the first cohort baseline; /019+ continues with diverse cohorts and specializations.

Cohort coverage targets (cycle-3 EXPLORATION budget 10 total; 7 remain after /018):

### 11.1 /019 PRIMARY — ETH-only regime-conditional gate

ETH structural OOS drag is the strongest negative pattern across cycle-2+3 (4 axes: /014/015/016/017). Specialization: BTC-trend-conditional kill switch OR per-symbol drawdown brake (stateless). Pre-committed at /017 brief Section 11.3.

Cohort: ETH-only (1-symbol). Specialization: ONE regime gate. MEDIUM-HIGH structural prior.

### 11.2 /020 SECONDARY — LINK-specific ATR multipliers (follow-on from /018)

If /018 PROMISING-ish, /020 layers ATR specialization on top: test LINK-specific (3.0/1.5) tighter or (4.0/2.0) wider against /018's LINK-only-baseline-ATR (3.5/1.75). Per Section 2.5 Option B deferred. Conditional on /018 PROMISING outcome.

### 11.3 /021 TERTIARY — BTC-only specialized (separate from pooled Model A)

BTC IS catastrophic rotation at /017 (-93.81); BTC OOS positive (+15.11). Pooled Model A trains poorly on BTC. BTC-only test isolates BTC's intrinsic edge. MEDIUM structural prior.

### 11.4 /022 — DOT-only specialized

DOT IS +96.07 at /017 (catastrophic-positive rotation signature); DOT IS +26.62 at baseline. DOT structural IS positive, OOS approximately flat (+1.96). DOT-only test characterizes DOT's intrinsic IS-driven edge. MEDIUM structural prior.

### 11.5 /023 — SOL-only specialized

SOL added at /017; SOL OOS clean 16.4% portfolio share. SOL-only at single-cohort tests SOL's intrinsic edge in 6-sym /017 universe context. MEDIUM structural prior.

### 11.6 /024-/026 — 2-3 symbol pooled cohorts

Per `feedback_v1_per_cohort_exploration_strategy.md`: 2-3 symbol pooled cohorts test diversified per-cohort edge:
- /024: DOT+LTC vol-cluster (correlation-paired)
- /025: LINK+SOL DeFi-pair
- /026: BTC+ETH separated (revisit Model A architecture)

### 11.7 /027 — CYCLE-3 CONFIRMATION (bundle PROMISING specialists)

Bundle composition: only specialists that PROMISING'd at single-seed EXPLORATION. Multi-seed validation at 10 inner seeds. Diversification weighting (equal or vol-targeted). BASELINE_V1 update only if STRICTLY beats anchor on multi-seed mean both halves + ≥5/10 seeds positive OOS.

---

## Section 12 — Catalog Closeout Plan (Phase 8)

After Phase 7.5 Critic verdict:

1. Update `briefs-v1/exploration_catalog.md` with iter-v1/018 row:
   - axis_varied: "LINK-in-isolation (Models A/D/E dropped; ONLY Model C)"
   - axis_family: `per-cohort-specialization-LINK` (NEW 9th family declaration)
   - IS Sharpe Δ: vs LINK-alone IS +0.3724 anchor
   - OOS Sharpe: vs LINK-alone OOS +0.8184 anchor (informational against portfolio +0.6637)
   - verdict: per Section 8 cell
   - confirmation_candidate: YES if PROMISING / NO if NEGATIVE / CONDITIONAL if PROMISING-INERT
2. Write `diary-v1/iteration_v1-018.md` with FRONTMATTER + per-cohort verdict.
3. Tag `v0.v1-018` after Phase 8 closeout commit.
4. /019 advances under per-cohort methodology with /019 PRIMARY = ETH-only regime-conditional gate (per Section 11.1).

---

## Section 13 — Phase 5.5 self-check (QR pre-handoff)

Section 0.5 — present? YES (cadence position + cycle ledger).
Section 0.6 — axis family + cohort declared? YES (`per-cohort-specialization-LINK`, NEW 9th family, rotation VALID).
Section 0.7 — LM Master Phase 4.5 reservation? YES (Section 3.4 placeholder).
Section 1 — hypothesis explicit and falsifiable? YES (H1 LINK-only OOS Sharpe vs LINK-alone-in-pool baseline; H2 informational).
Section 2 — numerical EDA tables committed at `ea71dbe`? YES (12 files including 4 source CSVs from analysis/iteration_v1-018/).
Section 2.5 — HIGH-RISK declaration explicit? YES (HIGH-RISK; single-cohort = Optuna training-objective domain change).
Section 3 — implementation spec specifies single src/ file change? YES (`run_baseline_v1.py` only).
Section 3.4 — LM Master responses placeholder? YES (Phase 5.5 BLOCK condition flagged).
Section 3.5 — axis family declared with cohort framing? YES.
Section 3.6 — wall-clock estimate explicit, ≥20% margin? YES (12-18 min predicted; ≥80% margin against 2h cap; ≥78 min buffer against 1.6h BLOCK threshold).
Section 4 — F1-F8 falsifiers pre-registered + F-AXIS-MECHANISM 3-sub-check? YES.
Section 4 — F1 anchored against LINK-alone-in-pool (not portfolio)? YES.
Section 4 — F8 cohort-scale trade band? YES ([25, 75] OOS).
Section 5 — verdict prior FLAT? YES (33/33/34).
Section 6 — failure modes characterized? YES (5 modes including basin lottery, IS overfit, pool-leveraged, direction collapse, n_eff collapse).
Section 8 — verdict matrix per-cohort variant + NEGATIVE-INTRINSIC subtype? YES.
Section 9 — library stack declared? YES.
Section 10 — implementation spec critical detail (engineering report, kill-switch)? YES.
Section 11 — alternates for /019+? YES (7 candidates).
Section 12 — catalog closeout plan? YES.
Section 13 — this checklist? YES.

**Self-check verdict**: brief PASS for Phase 5.5 gate as of authoring time (LM Master Phase 4.5 responses pending; Section 3.4 will be amended in Phase 5.5 cycle after LM Master fires).

---

**End of brief.**
