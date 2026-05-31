# iter-v1/037 — Research Brief

**Iteration**: iter-v1/037
**Date**: 2026-05-31
**TYPE**: EXPLORATION
**Cycle**: 5, EXP 4 of 10
**Branch**: `iteration-v1/037`
**Author**: QR (autopilot)

---

## Section 0 — Hypothesis

**H1 (PRIMARY)**: Replacing Optuna's per-trial scoring metric from **Sharpe** (`mean/std`) to **Sortino** (`mean/downside_std`) on the 5-cohort BASELINE_V1 architecture surfaces hyperparameter regions that Sharpe under-rewards because they reduce LEFT-TAIL trade losses without proportionally lifting mean PnL. Modal expected OOS bundle Sharpe Δ = **+0.10 to +0.30** vs anchor (`BASELINE_V1` IS +0.2829 / OOS +0.6637), driven by reduced drawdown exposure on left-skewed cohorts and improved trade-quality concentration.

**H1a (mechanism)**: Sharpe penalizes upside variance equally with downside variance. On a right-skewed PnL distribution (positive skew, mean > median), Sharpe-maximizing Optuna selects HP regions that DAMPEN upside vol — counterproductive when crypto futures returns are by construction right-tailed (TP/SL ratio of 2x and triple-barrier first-hit dynamics). Sortino targets the asymmetric downside-only deviation, so Optuna's basin selection is now sensitive to STRATEGIES THAT MISS BAD TRADES rather than strategies that smooth all trades.

**H1b (falsifiable)**: If bundle OOS Sharpe Δ < +0.05 AND OOS Max DD improvement is ≤ -2pp absolute, the Sortino-vs-Sharpe loss-function swap is INERT at v1 EXPLORATION budget (n_trials=18, single seed) on the current PnL distribution shape. Loss-function axis CLOSED at v1 EXPLORATION budget.

---

## Section 0.5 — Iteration Type, Cadence Position, Wall-Clock

- **TYPE**: EXPLORATION
- **Cadence**: cycle-5 EXPLORATION 4 of 10. Cycle-5 prior precedents: /034 (basis_zscore_30, NEG-INERT), /035 (trend-scanning labels, NEG-CAT bundle but bimodal LINK+DOT positive), /036 (LINK+DOT trend-scan specialist, **PROMISING-CLEAN — largest single-seed OOS lift in v1 history**).
- **NO kill-switches** (user directive 2026-05-30 stands for cycle-5).
- **Wall-clock target**: ~50 min modal at v1 EXPLORATION standard (n_trials=18, ENSEMBLE_SIZE=3, single outer seed=42). Sortino objective adds **NEGLIGIBLE per-trial cost** vs Sharpe (same vector arithmetic, one extra mask + std on subset). 2h soft cap with 60% margin.

---

## Section 0.6 — Axis-Family Rotation (v1-only)

- **Axis family**: `loss-function` (**NEW 12th axis family** in v1 catalog — never used in cycles 1-4 or cycles 5/034-036)
- **Prior 5 EXPLORATION families** (from `briefs-v1/exploration_catalog.md`):
  - iter-v1/032: sample-weighting-isolation (basin-lottery ablation)
  - iter-v1/033: hyperparameter-region (CONFIRMATION; BLOCK-FINAL)
  - iter-v1/034: feature-family (basis z-score)
  - iter-v1/035: labeling (trend-scanning)
  - iter-v1/036: per-cohort-specialization-LINK+DOT-trend-scan
- **Rotation status**: **VALID** — `loss-function` is structurally orthogonal to all prior 5 families. The Optuna training-objective FORMULA changes, not the labels (unchanged from baseline), not the features (V1_FEATURE_COLUMNS_PRUNED 44 cols including /034 basis_zscore_30 unchanged), not the architecture (5-cohort A/C/D/E unchanged), not the sample weights (abs_pnl unchanged). 12th family declaration is structural — formally orthogonal to the other 11. Per `feedback_v1_per_cohort_exploration_strategy.md` + v1 catalog precedent, NEW family declaration requires Critic + LM Master + QR 3-way convergence at Phase 7.5 (deferred to closeout; pre-declared by QR here).
- **One-sentence rationale**: cycle-5 mandates structural axes; the Optuna scoring function has never been varied in v1 history; right-skewed crypto PnL distributions (per Section 1 EDA, skew +0.58 to +0.89 across cohorts; Sortino/Sharpe ratio 3.0-4.0x) provide a mechanically grounded reason to expect the Sortino objective to surface different hyperparameter regions than Sharpe.

---

## Section 1 — IS-Only Evidence (Sortino vs Sharpe diagnostic per cohort)

EDA script: `analysis/iteration_v1-037/sortino_vs_sharpe_diagnostic.py` (IS-only, reads `reports-v1/iteration_v1-baseline/in_sample/trades.csv`, 621 trades).

Computes trade-level Sharpe (`mean/std`) vs Sortino (`mean/downside_std`) per cohort. CRITICAL: this is a DIAGNOSTIC of the loss-surface shape Sortino would optimize — it is NOT a predictor of OOS lift. The OOS lift depends on whether Optuna's basin reselection at n_trials=18 finds regions that GENERALIZE.

### Section 1.1 — Per-cohort PnL distribution shape (IS-only)

| Cohort | n trades | mean (pp) | std (pp) | down_std (pp) | Sharpe | Sortino | **Sortino/Sharpe** | down_frac | skew |
|---|---|---|---|---|---|---|---|---|---|
| PORTFOLIO | 621 | +0.1821 | 6.7001 | 2.1351 | +0.0272 | +0.0853 | **+3.14** | 59.7% | +0.79 |
| Model A (BTC+ETH) | 258 | -0.0976 | 5.4069 | 1.8049 | -0.0180 | -0.0541 | **+3.00** | 62.8% | +0.89 |
| Model C (LINK) | 146 | +0.5936 | 8.1403 | 2.0119 | +0.0729 | +0.2950 | **+4.05** | 54.8% | +0.58 |
| Model D (LTC) | 124 | +0.1264 | 6.8674 | 1.8439 | +0.0184 | +0.0685 | **+3.72** | 60.5% | +0.86 |
| Model E (DOT) | 93 | +0.3863 | 7.1563 | 2.2401 | +0.0540 | +0.1724 | **+3.19** | 58.1% | +0.70 |

**Key observations**:

1. **Sortino/Sharpe ratio = 3.0–4.0x across ALL cohorts** — uniformly above the 1.5x rule-of-thumb "meaningful asymmetry" threshold. The loss-surface gradient under Sortino is **structurally different** from Sharpe across all 4 models.
2. **All cohorts right-skewed** (skew +0.58 to +0.89) — winners are larger than losers in trade-level PnL, consistent with TP×2.9-3.5 / SL×1.45-1.75 baseline barriers. Sharpe penalizes upside variance; Sortino does not. **This is the precise asymmetry the loss-function swap exploits.**
3. **Downside std is ~30-37% of total std** — meaning the SUBSET of trades Sortino actually scores is much smaller than Sharpe's denominator. Optuna at n_trials=18 will search for HP regions where loss-trades are FEWER and SMALLER, not necessarily where winners are STABLER (Sharpe's incentive).
4. **Model C (LINK) has the highest Sortino/Sharpe ratio (4.05x)** — the most asymmetric distribution among cohorts. C is the cohort with the largest expected basin shift under Sortino.
5. **Model A (BTC+ETH) is negative under both metrics** — the loss-surface reshape on a NEGATIVE-mean pool may FAIL to find a better region (Sortino doesn't make a losing strategy win — it just changes which hyperparameters get scored higher). Sortino's incentive on negative-mean cohorts is to MINIMIZE the absolute downside std, which can drive Optuna toward zero-trade or hyper-conservative regions.

### Section 1.2 — What Sortino does NOT change

- Triple-barrier labels (σ_t EWMA 14d) — UNCHANGED from baseline
- Sample weighting (`abs_pnl`) — UNCHANGED from baseline
- Feature columns (`V1_FEATURE_COLUMNS_PRUNED` = 44 cols including basis_zscore_30) — UNCHANGED from /034
- Risk gates (R1 ON C/D/E, R2 ON E only, R3 ON all 4 models) — UNCHANGED
- LightGBM hyperparameter search space (`v1_pruned` bounds_profile) — UNCHANGED
- Backtest engine, fees, slippage — UNCHANGED

The ONLY change is the scalar Optuna study returns per trial: `mean(pnls) / std(pnls)` → `mean(pnls) / std(pnls[pnls<0])`.

### Section 1.3 — Theoretical positioning (López de Prado AFML & Sortino literature)

- Sortino is canonical for ASYMMETRIC return distributions where the investor explicitly tolerates upside variance but penalizes downside (Sortino & Price 1994 in *Journal of Investing*).
- AFML Ch.14 §14.3 implicitly suggests Sharpe is appropriate when returns are Gaussian; for fat-tailed left-skewed series, deflated alternatives apply.
- Crypto futures TP/SL labels generate RIGHT-SKEWED returns by construction (TP×2-3.5 / SL×1.45-1.75 with first-hit dynamics + timeout-at-zero-EV), making Sortino the THEORETICALLY APPROPRIATE objective for v1's labeling architecture.

**However**: theoretical appropriateness ≠ guaranteed OOS lift at Optuna n_trials=18 single-seed. The basin Optuna finds under a new metric is non-deterministic; the LightGBM hyperparameter space has multiple local optima per cohort. The OOS lift depends on whether the Sortino-optimal basin GENERALIZES better than the Sharpe-optimal basin — which is empirically determined by this backtest, not by the EDA alone.

---

## Section 2 — Falsifiers (F-AXIS #1-#5)

Five falsifiers, each disjunctive (any one firing → axis-mechanism failed):

### F-AXIS #1 — Wiring proof (Optuna scoring function changes)

**PASS criterion**: First Optuna trial's per-fold log line shows `Sortino=X.XXXX` instead of `Sharpe=X.XXXX` (verbose>0 path; new branch in `compute_sortino_with_threshold`). Per-cell prints "OPTUNA OBJECTIVE: sortino" banner ≥ 95% of cells (target 100%). If < 80%, **BLOCK-PENDING-FIX (silent-fallback to Sharpe)**.

### F-AXIS #2 — Trade-count band (does Optuna search FIND non-trivial trades under Sortino?)

**Modal prediction**: IS trade-count ∈ [560, 690] (baseline 621 ±10%). OOS trade-count ∈ [165, 215] (baseline 189 modal). Risk asymmetry: Sortino's incentive on negative-mean Model A could drive it to zero-trade regions (basin lottery).
**PASS criterion**: portfolio IS trades ≥ 500 AND OOS trades ≥ 130 (the trade-rate floor from `feedback_trade_rate_floor.md`).
**FAIL**: OOS < 130 → **TECHNICAL-FAILURE-LOSS-SURFACE-COLLAPSE** (Sortino drove Optuna to over-restrictive HP region; axis is NOT inherently broken but EXPLORATION budget at n_trials=18 is too low to recover).

### F-AXIS #3 — Per-cohort basin migration (Sortino actually reselects different HP regions)

**PASS criterion**: Per-cell best `learning_rate` Spearman correlation vs baseline ≤ 0.85 across all 4 model cohorts (LOWER correlation = MORE basin migration). If Spearman > 0.95 for ≥3 of 4 cohorts, **TECHNICAL-FAILURE-SILENT-NO-OP** (Sortino is mechanically identical to Sharpe at this loss-surface curvature — unexpected given Section 1's 3-4x ratio).
**Diagnostic**: read `data/v1_iter037_optuna_best_params.parquet` post-run; compute Spearman per (model_role, training_month) vs baseline params parquet.

### F-AXIS #4 — Downside-deviation actually shrinks (mechanism validation)

**PASS criterion**: Bundle OOS downside std (computed from `out_of_sample/trades.csv` pnl_pct[pnl_pct<0]) is ≤ 90% of baseline OOS downside std. If downside std INCREASES vs baseline, Sortino MIGHT have over-fit IS downside (basin found IS-quiet region that doesn't generalize) → **NEG-OVER-FIT-IS-DOWNSIDE**.
**Caveat**: at single-seed=42 EXPLORATION budget, this metric has noise floor ~±15%; report INFORMATIONAL.

### F-AXIS #5 — Asymmetric verdict matrix (load-bearing)

**LOAD-BEARING** transferred from /030+ pattern: bundle OOS TP-exit count ≥ 15 portfolio AND Model D OOS TP ≥ 3 (LTC catastrophe pre-vet from /028 §6). If Sortino-optimal basin zeros LTC TP-exits, the upside vanishes alongside the loss-clip — INERT-FAVORABLE downside masking.
**PASS criterion**: OOS TP-exit count ≥ 15 portfolio AND Model D OOS TP ≥ 3.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

- **Declaration**: **NORMAL-RISK**
- **Reason**: The loss-function swap changes ONLY the scalar Optuna returns per trial. It does NOT change the Optuna training-objective DOMAIN (the per-row weight vector, the LightGBM loss function, the labels, the features, or the search space bounds). The downstream basin selection differs, but the per-trial computation is structurally identical to Sharpe — same data, same fold splits, same gap, same cv_splits, same threshold gate. Compare to /031 (sample-weighting via per-row weight inversion = HIGH-RISK — reshapes per-row gradient): /037 reshapes ONLY the per-trial AGGREGATE statistic.
- **Mitigation (optional, NOT adopted)**: HIGH-RISK declaration would mandate multi-seed validation. /037 single-outer-seed=42 EXPLORATION is acceptable under the v1 NORMAL-RISK pattern; if PROMISING, the CONFIRMATION at cycle-5 closeout will multi-seed-validate per `feedback_seed_validation.md`.

---

## Section 3 — Implementation Design

### Section 3.1 — Scope summary

| File | Change | LoC est |
|---|---|---|
| `src/crypto_trade/strategies/ml/optimization.py` | NEW `compute_sortino_with_threshold()` + threading `optuna_objective` param through `_objective` + `optimize_and_train` | ~80 |
| `src/crypto_trade/strategies/ml/lgbm.py` | NEW `optuna_objective: str = "sharpe"` ctor param + plumb through to `optimize_and_train` | ~15 |
| `run_baseline_v1.py` | NEW `--optuna-objective {sharpe, sortino}` CLI flag + new `elif iteration_label == "v1-037"` dispatch + add `v1-037` to baseline catch-all exclusion tuple (per `/030 LESSON`) | ~110 |
| `tests/test_iteration_v1_037.py` | NEW 8+ tests | ~250 |

### Section 3.2 — Sortino formula (canonical)

```python
def compute_sortino_with_threshold(
    y_proba: np.ndarray,
    long_pnls: np.ndarray,
    short_pnls: np.ndarray,
    threshold: float,
    min_trades: int = 20,
    ternary: bool = False,
) -> float:
    """Compute Sortino from actual PnLs, filtering by prediction confidence.

    Sortino = mean(pnls) / downside_std(pnls)
    where downside_std = std of pnls[pnls < 0] (ddof=0).

    Returns -10.0 penalty if:
      - fewer than min_trades survive the filter
      - downside_std is zero (no negative trades — would give +inf, not actionable)
      - |sortino| > 100 (numerical overflow guard, same as Sharpe path)
    """
    # ... same masking/prediction logic as compute_sharpe_with_threshold ...
    pnls = np.where(y_pred == 1, long_pnls[mask], short_pnls[mask])
    mean = pnls.mean()
    downside = pnls[pnls < 0]
    if len(downside) < 2:
        return -10.0
    down_std = downside.std()
    if down_std == 0:
        return -10.0
    sortino = float(mean / down_std)
    if abs(sortino) > 100:
        return -10.0
    return sortino
```

### Section 3.3 — `_objective` dispatch

Inside `optimization._objective`:

```python
optuna_objective = trial.study.user_attrs.get("optuna_objective", "sharpe")
if optuna_objective == "sortino":
    score_fn = compute_sortino_with_threshold
elif optuna_objective == "sharpe":
    score_fn = compute_sharpe_with_threshold
else:
    raise ValueError(f"Unknown optuna_objective: {optuna_objective!r}")

# Use score_fn at line 313 (replaces direct compute_sharpe_with_threshold call):
score = score_fn(y_proba, long_pnls[val_idx], short_pnls[val_idx], confidence_threshold, ternary=ternary)
scores.append(score)
```

Variable rename `sharpes` → `scores`. `mean_sharpe` → `mean_score`. Per-trial log:
```
[trial N] Sortino=X.XXXX (folds: ...)   # when objective=sortino
[trial N] Sharpe=X.XXXX (folds: ...)    # when objective=sharpe (BIT-IDENTICAL to baseline)
```

### Section 3.4 — `optimize_and_train` plumbing

Add `optuna_objective: str = "sharpe"` parameter (default preserves BIT-IDENTITY for ALL existing callers). Inside, before `study.optimize(...)`:
```python
study.set_user_attr("optuna_objective", optuna_objective)
```
This mirrors the existing `fast_mode` propagation pattern (line 424 in current optimization.py). `_objective` reads it from `trial.study.user_attrs` as shown in Section 3.3.

### Section 3.5 — `LightGbmStrategy.__init__` parameter

Add `optuna_objective: str = "sharpe"` parameter at lgbm.py line ~192 (sister to `bounds_profile`). Store as `self._optuna_objective`. Validate in ctor:
```python
if optuna_objective not in ("sharpe", "sortino"):
    raise ValueError(f"optuna_objective must be 'sharpe' or 'sortino'; got {optuna_objective!r}")
```
Pass through to `optimize_and_train()` call site at lgbm.py line ~973 (alongside existing `bounds_profile=self._bounds_profile`).

### Section 3.6 — `run_baseline_v1.py` CLI flag + dispatch

Add CLI flag adjacent to `--sample-weight-mode` (line ~1802):
```python
parser.add_argument(
    "--optuna-objective",
    choices=["sharpe", "sortino"],
    default="sharpe",
    help=(
        "Optuna study objective metric (iter-v1/037). "
        "'sharpe' (default) is BIT-IDENTICAL to baseline. "
        "'sortino' uses mean/downside_std — iter-v1/037 axis. "
        "Targets right-skewed PnL distributions where Sharpe penalizes upside variance."
    ),
)
```

Resolve at runtime (after args parse):
```python
optuna_objective_arg = getattr(args, "optuna_objective", "sharpe")
```

Add NEW `elif iteration_label == "v1-037" and set(symbols) == set(V1_BASELINE_UNIVERSE):` dispatch branch (after the `v1-036` branch at line ~3595). The dispatch is BIT-IDENTICAL to baseline structure (Models A/C/D/E, baseline universe, V1_FEATURE_COLUMNS_PRUNED including basis_zscore_30, NO label/feature/weight changes) EXCEPT pass `optuna_objective=optuna_objective_arg` to each `run_model()` call:
```python
results_a, faxm_a, _strat_a = run_model(
    "A (BTC/ETH)",
    ("BTCUSDT", "ETHUSDT"),
    atr_tp=2.9, atr_sl=1.45,
    apply_r1=False,
    n_trials=n_trials,
    ensemble_size=ensemble_size,
    oof_persist_path=OOF_PARQUET_PATH,
    feature_columns=active_feature_columns,
    bounds_profile=bounds_profile,
    optuna_objective=optuna_objective_arg,  # NEW
    **_r5_kwargs,
)
# ... C/D/E identical pattern ...
```

Print dispatch banner:
```python
print(
    f"[iter-v1/037] SORTINO OBJECTIVE: optuna_objective={optuna_objective_arg!r}. "
    f"Loss-function axis (NEW 12th family). "
    f"ENSEMBLE_SIZE={ensemble_size} (inner), seeds=1 (outer), n_trials={n_trials}."
)
```

### Section 3.7 — `/030 LESSON` mandate (line 3686 exclusion tuple)

ADD `"v1-037",` to the baseline catch-all exclusion tuple at run_baseline_v1.py line ~3686. Without this, the catch-all (line ~3680) fires FIRST when `iteration_label == "v1-037"` AND symbols match V1_BASELINE_UNIVERSE, silently bypassing the /037 dispatch branch and producing a BASELINE backtest mislabeled as /037 (the /030 dispatch defect that wasted 51 min compute).

### Section 3.8 — `run_model()` signature change

Add `optuna_objective: str = "sharpe"` parameter to the `run_model()` function (which constructs `LightGbmStrategy`). Pass through to `LightGbmStrategy(... optuna_objective=optuna_objective ...)`. Default preserves BIT-IDENTITY for all existing callers.

---

## Section 4 — Verdict Matrix

| Verdict | F1 (binary lift) | F-AXIS evaluation | Routing |
|---|---|---|---|
| **PROMISING-CLEAN** | OOS bundle Sharpe Δ ≥ +0.10 AND all F-AXIS #1-#5 PASS | All 5 falsifiers PASS | /045 = stack Sortino w/ /036 LINK+DOT trend-scan specialist (potentially compoundable per LM Master cross-layer orthogonality precedent) |
| **PROMISING-INERT-FAV** | OOS bundle Sharpe Δ ∈ [+0.05, +0.10) AND OOS Max DD improvement ≥ -5pp | F-AXIS #4 PASS | /038 = NEW axis family (regime gating or per-cohort Sortino) |
| **INERT-NO-EFFECT** | \|OOS bundle Sharpe Δ\| < +0.05 AND F-AXIS #3 Spearman > 0.95 | F-AXIS #3 FAIL (silent-no-op) | Loss-function axis CLOSED at v1 EXPLORATION; /038 = different family |
| **NEG-OVER-FILTER** | OOS bundle Sharpe Δ ∈ (-0.20, -0.05) | F-AXIS #2 PASS but Optuna found IS-tight basin that fails OOS | /038 = NEW family + Sortino axis CLOSED for v1 EXPLORATION budget |
| **NEG-CATASTROPHIC** | OOS bundle Sharpe Δ ≤ -0.20 | F-AXIS #2 FAIL (OOS < 130 trades) OR loss-surface collapse | /038 = NEW family + Sortino axis CLOSED (mechanism = basin-relocation under negative-mean Model A cohort) |
| **TECHNICAL-FAILURE-SILENT-FALLBACK** | comparison.csv matches baseline byte-exactly | F-AXIS #1 FAIL (banner not printed) | BLOCK-PENDING-FIX; re-run with dispatch defect repaired |

**LM Master priors** (best guess, refined at Phase 4.5 dispatch): PROMISING-CLEAN 17% / PROMISING-INERT-FAV 24% / INERT-NO-EFFECT 30% MODAL / NEG-OVER 18% / NEG-CAT 11%. Combined PROMISING 41% vs combined NEG 29%. MEDIUM directional confidence — no v1 precedent for loss-function axis.

---

## Section 5 — Risk Mitigation

Per `feedback_risk_mitigation_design.md`: every merge-candidate iteration includes a Risk Mitigation section with IS-calibrated thresholds + simulated historical effect. For /037 EXPLORATION:

- **R1 (per-symbol SL cooldown)**: UNCHANGED from baseline. K=3 SLs → 27-candle cooldown on Models C/D/E. R1 OFF for Model A pool (BTC+ETH baseline behavior).
- **R2 (drawdown scaling for Model E)**: UNCHANGED from baseline. 7% DD → scale to floor 0.33.
- **R3 (OOD Mahalanobis gate)**: UNCHANGED from baseline. 70th-percentile cutoff on 16 scale-invariant features. ALL 4 models.
- **R5 (vol-target ceiling, kill-switch)**: AUTO-DISABLED when `sample_weight_mode != "abs_pnl"`. /037 has `sample_weight_mode == "abs_pnl"` (UNCHANGED from baseline), so R5 stays at baseline state.

**Sortino-specific risk**: Optuna at Sortino-mode on negative-mean Model A cohort may select HP regions with 0 OOS trades (trivial "no trades = no downside" basin). Mitigation = F-AXIS #2 (OOS trade-count floor 130) catches this at Phase 7 review.

**Simulated historical effect**: not applicable for pure loss-function swap — there are no thresholds/gates to back-test on prior iterations' trade rosters. The IS Sortino EDA in Section 1.1 is the closest analogue.

---

## Section 6 — Anti-Cheating Self-Check

- [x] EDA script `analysis/iteration_v1-037/sortino_vs_sharpe_diagnostic.py` reads `reports-v1/iteration_v1-baseline/in_sample/trades.csv` ONLY (IS-only by file path).
- [x] No OOS file reads in EDA. No `out_of_sample/` reference in EDA script.
- [x] No parameter tuning on OOS data — Sortino formula is parameter-free; thresholds (n_trials=18, ENSEMBLE_SIZE=3, seed=42) are baseline EXPLORATION standard.
- [x] OOS_CUTOFF_DATE = 2025-03-24 and training_months = 24 UNCHANGED.
- [x] Backtest will run on full available data, no date trimming.
- [x] Hypothesis falsifiers F1-F5 pre-registered above Phase 6 dispatch.

---

## Section 7 — LM Master Phase 4.5 Recommendation Handling

LM Master Phase 4.5 to be invoked AFTER Phase 5.5 dispatch readiness check (between Phase 5.5 and Phase 6.0 per v1 refactored workflow).

QR's pre-LM-Master expectations (to be updated if LM Master adjudicates differently):

- **Hyperparameter recs**: NONE expected — n_trials=18 / ENSEMBLE_SIZE=3 / bounds_profile=v1_pruned is v1 EXPLORATION standard. The Sortino swap does NOT change the search space.
- **Feature-engineering recs**: NONE expected — features UNCHANGED from /034 (V1_FEATURE_COLUMNS_PRUNED 44 cols including basis_zscore_30).
- **Saturation risks**: LM Master may flag that single-seed=42 EXPLORATION on loss-function axis has high per-cohort basin-lottery noise (esp. Model A negative-mean). QR position: ACCEPT noise as v1 EXPLORATION discipline; multi-seed validation at /044 CONFIRMATION (if PROMISING).
- **Confidence assessment**: MEDIUM (no v1 precedent for loss-function axis).

Brief Section 3 will be UPDATED if LM Master Phase 4.5 recs adjudicate any change (modify or reject explicitly).

---

## Section 8 — Falsifiers Summary (Phase 7 evaluation gate)

Phase 7 QR must compute:

1. F-AXIS #1: grep `[iter-v1/037] SORTINO OBJECTIVE` lines in run.log — count ≥ 95% of expected cells.
2. F-AXIS #2: portfolio OOS trades from `reports-v1/iteration_v1-037/comparison.csv` ≥ 130.
3. F-AXIS #3: read `data/v1_iter037_optuna_best_params.parquet`, compute Spearman `learning_rate` per `(model_role, train_month)` vs baseline → median across cohorts ≤ 0.85 PASS / > 0.95 FAIL.
4. F-AXIS #4: compute OOS downside std from `out_of_sample/trades.csv` pnl_pct[<0] → ≤ 90% of baseline OOS downside std.
5. F-AXIS #5: count OOS TP exits ≥ 15 portfolio AND Model D ≥ 3.

Verdict matrix Section 4 applies.

---

## Section 9 — Library Stack

- **No new dependencies**. Pure numpy/pandas masking + std reductions; Optuna interface unchanged.
- Sortino formula is canonical (Sortino & Price 1994) — single-file in `optimization.py` parallel to `compute_sharpe_with_threshold`.

---

## Section 10 — Symbol Exclusion + Reproducibility + Test Mandate

### Section 10.1 — Symbol exclusion

- v1 universe UNCHANGED: BTC, ETH, LINK, LTC, DOT.
- v2 universe symbols (DOGE, NEAR, SOL, XRP) excluded — v1 track only.

### Section 10.2 — Reproducibility

- Single outer seed = 42 (deterministic Optuna TPE sampler init).
- Inner ENSEMBLE_SIZE=3 with seeds [42, 123, 456] (v1 EXPLORATION default).
- n_trials=18 (v1 EXPLORATION default per `feedback_v1_trial_budget_standardization.md` retracted; current default 18).
- bounds_profile = `v1_pruned` (44-feature pruned set).
- Sortino formula deterministic given (`y_proba`, `long_pnls`, `short_pnls`, `threshold`).

### Section 10.3 — Test mandate (8+ tests per `/030 LESSON`)

`tests/test_iteration_v1_037.py` MUST include:

1. **CLI flag parsing**: `--optuna-objective sharpe` and `--optuna-objective sortino` both accepted; invalid value raises argparse error.
2. **`compute_sortino_with_threshold` formula correctness**: synthetic PnL array with known mean, std, downside_std; assert Sortino = mean / downside_std within 1e-9.
3. **Sortino zero-downside guard**: all-positive PnL array → returns -10.0 penalty (no division by zero).
4. **Sortino min-trades guard**: filter that retains < 20 trades → returns -10.0.
5. **Sortino overflow guard**: synthetic distribution producing |Sortino| > 100 → returns -10.0.
6. **`optimize_and_train` plumbing**: when `optuna_objective="sortino"`, study.user_attr is set and `_objective` reads it.
7. **`LightGbmStrategy` ctor validation**: invalid `optuna_objective` raises ValueError.
8. **Backward-compat BIT-IDENTITY**: when `optuna_objective="sharpe"` (default), all output is IDENTICAL to baseline path (call Sharpe path explicitly, compare to Sortino-path-with-flag-off byte-by-byte on synthetic data).
9. **Dispatch banner**: when `iteration_label="v1-037"`, banner string contains "SORTINO OBJECTIVE" and "Loss-function axis (NEW 12th family)".
10. **Baseline catch-all exclusion**: `v1-037` is in the exclusion tuple at run_baseline_v1.py line 3686.
11. **`run_model()` parameter propagation**: when called with `optuna_objective="sortino"`, the constructed `LightGbmStrategy._optuna_objective == "sortino"`.

### Section 10.4 — Anti-cheating self-check

- [x] EDA reads IS-only.
- [x] No OOS file references in design.
- [x] Sortino formula has no tunable parameter against OOS.

### Section 10.5 — Phase 5.5 dispatch readiness

Phase 5.5 gate checks:
- [x] Brief Section 0.6 axis-family declared (`loss-function` NEW 12th family; rotation VALID).
- [x] Brief Section 2.5 NORMAL-RISK declared with rationale.
- [x] Brief Section 3 implementation design includes ALL 4 modified files + LoC estimates.
- [x] Brief Section 4 verdict matrix with 6 outcomes.
- [x] Brief Section 7 LM Master Phase 4.5 placeholder (recs adjudication deferred to Phase 4.5 dispatch).
- [x] Brief Section 10.3 test mandate ≥ 8 tests (11 listed).
- [x] EDA Section 1.1 numerical table cites IS-only `reports-v1/iteration_v1-baseline/in_sample/trades.csv`.
- [x] `/030 LESSON` Section 3.7 mandates `v1-037` added to catch-all exclusion tuple.

**Dispatch CLI (Phase 6 target)**:
```bash
uv run python run_baseline_v1.py \
  --exploration \
  --iteration 37 \
  --n-trials 18 \
  --pruned-features \
  --optuna-objective sortino
```

Expected wall-clock: ~50 min modal at v1 EXPLORATION standard; 2h soft cap (60% margin).

---

**End of Brief.**
