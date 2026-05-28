# Iteration iter-v1/028 — Research Brief

**Iter**: iter-v1/028
**Cycle**: 4 EXPLORATION #1 of 10 (NEW CYCLE — first iteration after cycle-3 closure 2026-05-28)
**Branch**: `iteration-v1/028` (from `9744202` cycle-3 closeout HEAD)
**Axis family**: `per-cohort-specialization-LTC-v2` (NEW; **differentiates from /022's** `per-cohort-specialization-LTC`)
**Anchor**: `v0.v1-baseline-corrected` (BASELINE_V1.md commit `f8bc12c`) — UNCHANGED
**Wall-clock budget**: 30 min target / 2h hard cap (single-cohort EXPLORATION; sub-15-min modal precedent at /022)

---

## Section 0 — Position in cycle / pivot context

### 0.1 Cycle-4 cadence position

- Cycle-3 closed 2026-05-28 at /027 CONFIRMATION-TECHNICAL-FAILURE. 10 EXPLORATIONs + 1 sanity + 1 TF (`briefs-v1/cycle3_closeout.md`).
- **Cycle-4 EXPLORATION #1 of 10**. CONFIRMATION earliest at /038 (assuming sequential EXPLORATIONs).
- BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`); only CONFIRMATION-MERGE updates baseline per `feedback_v3_baseline_update_policy.md`.

### 0.2 D-specialist mandate (LM Master /027 §9 binding regardless of /027 outcome)

LM Master /027 advisory §9 explicitly bound the cycle-4 first or second EXPLORATION to **D-specialist axis MANDATORY regardless of /027 verdict**. Quoting verbatim:

> **INERT (35% modal)** → /028 = **D-specialist axis MANDATORY**. LTC -1.05 is the dominant ceiling. Sister: sample-weighting OR XGBoost head-to-head
> **Single most important thing for QR**: LTC drag irrecoverable within /027 scope; **cycle-4 D-specialist EXPLORATION mandatory regardless of /027 verdict**.

The /027 TF leaves /027's multi-seed methodology question UNANSWERED. The D-specialist mandate stands because the LTC drag (baseline OOS -47.25% net PnL; per-trade Sharpe -0.267) is a SEPARATE cycle-4 inheritance from cycle-3 closeout §4.1.

### 0.3 LTC prior class (CARRIED OVER from /022 §0.3 — analysis already committed)

From `analysis/iteration_v1-022/ltc_prior_class.csv`:

| Field | Value | Class implication |
|---|---|---|
| Class | `ASYMMETRIC_ROTATION-INVERSE_IS-MARGINAL_OOS-CAT` | INVIABLE for bare isolation per saturation rule |
| IS net PnL | +3.27% | marginal IS positive |
| OOS net PnL | -47.25% | catastrophic OOS |
| IS H1 / H2 | +14.76% / -11.49% | sign reversal — rotation prior |
| Per-trade Sharpe IS / OOS | +0.004 / -0.267 | edge collapses OOS |
| IS direction asymmetry | longs -10.82% / shorts +14.10% | direction-asymmetric |
| OOS regime concentration | top 2 worst months ≈ 77% of OOS loss | concentrated |

**Per saturation rule** (`feedback_v1_per_cohort_saturation_asymmetric_rotation.md`): single-cohort isolation alone OR isolation + asymmetric one-sided gate are BOTH catastrophic for ASYMMETRIC_ROTATION cohorts (n=2 confirmation: BTC /020 -0.86; LTC /022 -1.17). New approach REQUIRED.

### 0.4 Mechanism selection — basin-relocation-robust criterion

This is the SINGLE LEVER that distinguishes /028 from /022. The /022 mechanism failed because:

1. /022 used an asymmetric long-suppress BTC-trend gate **at PRE-ENTRY**.
2. The gate targeted the baseline LTC OOS 89% long-direction drag — a basin-CONTINGENT property.
3. Single-cohort retraining produced a ~90% NEW roster (Jaccard 0.093 OOS / 0.10 IS — 79% non-overlap).
4. In the retrained basin, the targeted asymmetry DISSOLVED (76% long retrained vs 96% baseline; OOS short drag grew 4.6×).
5. The pre-entry gate by construction cannot touch trades it doesn't see, and acts on a property that no longer exists.

**The right mechanism for /028 must be BASIN-RELOCATION-ORTHOGONAL** — operate on properties that survive retraining regardless of which trades the model selects.

EDA-derived candidate ranking (`analysis/iteration_v1-028/ltc_mechanism_robustness_predictions.csv`):

| Candidate | Δ on baseline roster | Basin-orthogonal? | Notes |
|---|---:|---|---|
| **E_tighter_atr_sl** (cap loss at -3%) | **+36.17%** | **YES — post-entry SL acts on price path** | universal magnitude clip; mechanism survives roster change |
| C_meta_labeling (conf > 0.85) | +15.56% | NO — conf is basin output | OOS conf calibration INVERTED ([0.85,1.00) = 23% WR) |
| F_prior_month_drawdown_gate | +2.88% | MEDIUM — stateful but not targeted | only 1 month qualifies; weak signal |
| A_R5_vol_ceiling | +0.77% | PARTIAL | proxy via |pnl|; real impl needs NATR ex-ante |
| B_feature_subset | N/A — requires backtest | YES — substrate change | full retrain required; no closed-form proxy |
| D_sample_weighting | N/A — requires backtest | YES — substrate change | full retrain required; no closed-form proxy |

**Selected**: **E_tighter_atr_sl per-cohort tuning** for LTC-only Model D' specialist. Quantitative target = baseline `atr_sl=1.75` → **`atr_sl=1.0`** (cap typical loss at ~3% instead of ~5.25%, with TP unchanged at `atr_tp=3.5`).

**Why E ranks #1**:
1. Largest predicted Δ on the baseline roster (+36% PnL → ~+0.8 OOS Sharpe lift if mechanism survives basin relocation at proportional scale).
2. **Post-entry mechanism — basin-relocation-orthogonal by construction**. The SL fires when the realized price path crosses a multiple of ATR; it does not select trades, and its trigger condition is invariant under model retraining (LTC's volatility regime is not basin-dependent).
3. **GENUINELY DIFFERENT from /022**. /022 = pre-entry filter targeting basin-contingent direction asymmetry; /028 = post-entry magnitude clip targeting basin-invariant loss-tail distribution. The /022 failure mode (gate fires + asymmetry dissolves + trades remain unaffected) does NOT apply.
4. Addresses the EDA's dominant loss channel: stop_loss exits account for 21 of 34 baseline OOS trades and -97.9% of total loss — meta-mechanism in the data, not a researcher-imposed gate.
5. Stateless — no deadlock risk, no STATEFUL gate proof needed.

### 0.5 Cadence ledger summary

| Cycle | EXPLORATIONs | CONFIRMATIONs | Merges |
|---|---|---|---|
| 1 | /001-/005 | - | 0 |
| 2 | /006-/014 + /015-CONF | /015 | 0 (NEG-CAT catastrophic) |
| 3 | /016-/025 + /026 sanity + /027 TF | /027 | 0 (TECHNICAL FAILURE) |
| **4 (THIS)** | **/028 #1 of 10** | (earliest /038) | (pending) |

### 0.6 Axis Rotation Discipline + Family Declaration (v1 mandatory)

- **This iter's family**: `per-cohort-specialization-LTC-v2`. NEW 15th family. DIFFERENTIATES from /022's `per-cohort-specialization-LTC` because the orthogonal mechanism is post-entry magnitude clip (atr_sl) NOT pre-entry direction filter (BTC-trend gate).
- **Prior 5 EXPLORATION families** (going INTO /028, looking back from /025 — the last EXPLORATION, since /026 sanity and /027 TF don't count as EXPLORATIONs):
  - /021: methodology-pivot
  - /022: per-cohort-specialization-LTC
  - /023: feature-family (funding-rate)
  - /024: model-arch (regime-conditional)
  - /025: feature-family (OI delta)
- **Rotation status**: **VALID**. `per-cohort-specialization-LTC-v2` is in NONE of the prior 5 (different mechanism class from /022's literal name; per `feedback_v1_per_cohort_saturation_asymmetric_rotation.md` saturation rule the NEW mechanism class is what distinguishes families).
- **Rotation rationale**: The prior 5 are dispersed across 4 distinct families (methodology, per-cohort, feature ×2, model-arch). No 5-of-5 monoculture; rotation discipline is honored.

### 0.7 LM Master Phase 4.5 coordination slot

Phase 4.5 advisory expected after this Phase 5 brief commits. Brief Section 3.4 below RESERVED for LM Master responses post-Phase-4.5 (per v1 skill).

---

## Section 1 — Hypothesis

**H_028**: LTC-only training (Model D' specialist substrate) **+ tighter ATR-based stop-loss multiplier (atr_sl=1.0 vs baseline 1.75)** caps the dominant loss channel of LTC OOS (stop-loss exits at -5 to -7% magnitude) without sacrificing the upside (take-profit and timeout-positive trades are largely untouched). The mechanism is BASIN-RELOCATION-ORTHOGONAL because:

(a) The SL trigger fires on the realized price path crossing a multiple of ATR — a property of price dynamics, NOT of the trade-selection decision.
(b) LTC's 8h volatility regime (ATR scale) is substrate-invariant across LTC-in-pool baseline vs LTC-only retrained: both train on the same LTC kline data, only the universe composition changes the loss surface, not the volatility regime.
(c) Therefore the mechanism's targeting (loss magnitude > 3% in ATR-normalized units) survives the 79% basin relocation observed in /022.

**Predicted outcome** (per Section 5 priors below): modal verdict INERT or PROMISING-INERT-favorable, with the long-tail towards PROMISING reachable only if both substrate-change basin relocation lands favorably AND tighter SL ratio mechanism survives at the new roster's loss-tail distribution.

**Predicted F1 OOS Sharpe Δ band**: [-0.15, +0.55]. NEG-CAT (-0.55+) tail downweighted vs /022 because the mechanism is fundamentally different from the saturation-rule failure mode; PROMISING (+0.55+) tail upweighted vs /022 because the EDA counterfactual is +36% on the baseline roster (a 5× larger pre-mechanism signal than /022's +12% EDA).

---

## Section 2 — IS-Only Evidence (EDA results)

All evidence derived from committed analysis script `analysis/iteration_v1-028/ltc_oos_catastrophe_eda.py` (commit `5f76b4a`). Re-runs reproducibly from baseline + /022 reports (read-only inputs).

### 2.1 Baseline LTC trade distribution (anchor numbers — UNCHANGED)

| Sample | n_trades | net_pnl_pct | win_rate | per_trade_sharpe |
|---|---|---|---|---|
| IS | 124 | +3.27% | 47.0% (Model D' /022 numbers) / 39.5% (baseline 5-model) | +0.004 |
| OOS | 34 | **-47.25%** | 29.4% | **-0.267** |

### 2.2 Direction-split attribution (`ltc_baseline_trade_attribution.csv`)

| Sample | Direction | n | net_pnl_pct | per_trade_sharpe | share_of_total |
|---|---|---|---|---|---|
| IS | long | 74 | -10.82% | -0.021 | -330.6% (denom small +3.27) |
| IS | short | 50 | +14.10% | +0.040 | +430.6% |
| OOS | long | 19 | **-45.44%** | -0.456 | **+96.2%** |
| OOS | short | 15 | -1.81% | -0.024 | +3.8% |

**Direction asymmetry**: OOS longs lost -45.4%, shorts only -1.8%. The 89% long-direction drag at baseline confirmed.

### 2.3 OOS loss-channel ranking (`ltc_oos_loss_channels.csv` top 5)

| Channel | trade_share | net_pnl_pct | share_of_loss | win_rate |
|---|---|---|---|---|
| **exit_reason=stop_loss** | **62%** (21/34) | **-97.90%** | **+207.2%** | **0%** |
| pnl_bucket=moderate_loss [-7,-4) | 29% | -53.04% | +112.3% | 0% |
| direction=long | 56% | -45.44% | +96.2% | 26% |
| pnl_bucket=small_loss [-4,0) | 35% | -34.70% | +73.4% | 0% |
| conf=[0.85,1.00) | 38% | -31.69% | +67.1% | 23% |
| pnl_bucket=big_win (>=4%) | 21% (7/34) | +52.64% | -111.4% | 100% |
| exit_reason=take_profit | 12% | +31.64% | -67.0% | 100% |
| exit_reason=timeout | 26% | +19.01% | -40.2% | 67% |

**The dominant loss channel is stop_loss exits**: 21 of 34 trades (62%), -97.9% PnL (denominator-normalized = +207% of total — the SL channel alone is more than 2× the total loss in absolute terms, balanced by the +50% upside from TP+timeout). The pnl-magnitude distribution shows 10 trades in the moderate-loss [-7,-4) bucket = -53.0% PnL = 112% of total loss — these are the trades a tighter SL would clip from -5 to -7% down to -3%.

### 2.4 Tighter-SL counterfactual (`ltc_mechanism_robustness_predictions.csv`)

Closed-form counterfactual on baseline 34-trade OOS roster, clipping losses at -3.0% (matches `atr_sl=1.0` with typical LTC NATR ~3% — approximate):

- Observed baseline OOS net_pnl: **-47.25%**
- Counterfactual with -3% loss cap: **-11.08%**
- **Δ on baseline roster: +36.17%**
- 18 of 34 trades affected (the ones currently > -3% loss)
- This is descriptively valid (would have improved baseline OOS by +36% IF the mechanism survives basin relocation at proportional scale)

### 2.5 Confidence calibration check (`ltc_oos_confidence_distribution.csv`)

| Sample | conf_bucket | n_trades | win_rate | avg_pnl |
|---|---|---|---|---|
| IS | [0.55,0.70) | 11 | 36.4% | +0.10% |
| IS | [0.70,0.80) | 39 | 35.9% | -1.14% |
| IS | [0.80,0.90) | 48 | 39.6% | +0.09% |
| IS | [0.90,1.01) | 26 | 46.2% | +1.62% |
| OOS | [0.55,0.70) | 3 | 33.3% | -0.30% |
| OOS | [0.70,0.80) | 12 | 33.3% | -1.25% |
| **OOS** | **[0.80,0.90)** | **16** | **25.0%** | **-1.67%** |
| OOS | [0.90,1.01) | 3 | 33.3% | -1.52% |

**Confidence is INVERTED OOS**: the highest-confidence [0.85,1.00) bucket has the WORST win rate (25%) and worst avg PnL. This refutes meta-labeling (Option C) as a candidate — confidence is basin-output and is calibrated incorrectly OOS. The tighter-SL mechanism is **immune** because it does not condition on confidence.

### 2.6 Basin-relocation diagnostic (`ltc_022_basin_relocation_diagnostic.csv`)

| Sample | baseline n | /022 n | overlap | Jaccard | baseline-only PnL | /022-only PnL |
|---|---|---|---|---|---|---|
| IS | 124 | 117 | 22 | 0.101 | -27.10% | +59.36% |
| OOS | 34 | 48 | 7 | **0.093** | -38.71% | -36.98% |

**79% of baseline OOS trades did NOT exist in /022's retrained roster.** This confirms the saturation rule prediction: single-cohort LTC training produces a fundamentally different roster. **/028's mechanism must survive this retraining.**

### 2.7 Monthly OOS loss clustering (`ltc_monthly_loss_clustering.csv`)

Top 3 worst months:
- 2026-01: 5 trades, all longs, -24.09% (single largest monthly drag)
- 2026-04: 5 trades, all shorts, -12.46% (gate-of-/022 would have done nothing)
- 2025-11: 2 trades, both longs, -8.43%

The /022 asymmetric long-suppress gate would have done nothing for 2026-04 (all shorts) — confirming the asymmetric-gate dead path at the data level.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1 mandatory)

**Declaration: HIGH-RISK**

**Reason**: This axis combines (a) **per-cohort isolation** (LTC-only training, which changes Optuna's training-objective domain — the loss surface no longer averages BTC+ETH+LINK+DOT cohorts) AND (b) **labeling-parameter modification** (atr_sl multiplier 1.75 → 1.0, which directly changes triple-barrier label boundaries — Optuna's labeled-positive/negative split shifts).

**Both sub-axes change Optuna's training-objective domain** per `feedback_v1_high_risk_declaration_discipline.md`:
- LTC-only universe: optimization target changes from "Sharpe across 5 cohort substrate" to "Sharpe on LTC-only substrate"
- atr_sl=1.0 vs 1.75: triple-barrier upper/lower barriers move, label class balance shifts

**Mitigation (HIGH-RISK opt-in per v1 lighter footing)**:

Per `feedback_v3_iter017_meta_labeling_mandate.md` and v1's optional multi-seed: **single-seed=42 EXPLORATION budget** (consistent with /016-/025 single-axis tests). Multi-seed validation deferred to /038+ CONFIRMATION if /028 produces PROMISING-class verdict.

**Why opt-in is appropriate here**:
- Cumulative ≥1σ negative count reached 5 in cycle-3 (per `cycle3_closeout.md` §5.4). The multi-seed mandate has TRIPPED.
- However, the multi-seed mandate per cycle-3 §5.4 binds **HIGH-RISK axes**. /028 IS HIGH-RISK.
- **OVERRIDE**: this iteration BIND mits MULTI-SEED. Set `--seeds 2` minimum for /028 in run command (per cycle-4 §5.4 inheritance). ENSEMBLE_SIZE remains 3 at EXPLORATION budget; n_trials=35.

**Effective config**: `--seeds 2 --ensemble-size 3 --n-trials 35`. Estimated wall-clock 25-40 min (LTC-only single-cohort with 2 outer seeds; per /022 baseline 9 min × 2 seeds × moderate Optuna scaling ≈ 30 min).

**HIGH-RISK declaration with multi-seed mitigation** is the WORKING POSITION that survived cycle-3 §5.4 review.

---

## Section 3 — Implementation Spec

### 3.1 Code changes (single src/ file: `run_baseline_v1.py`)

Single elif dispatch branch added to runner. Mirrors /022 V1_ITER022_UNIVERSE pattern with two parameter changes:

```python
# In src/crypto_trade/features_v1/__init__.py:
V1_ITER028_UNIVERSE: tuple[str, ...] = ("LTCUSDT",)

# In run_baseline_v1.py, NEW elif branch (estimate ~50 lines):
elif set(symbols) == set(V1_ITER028_UNIVERSE) and iteration_label == "v1-028":
    # iter-v1/028: D-specialist (LTC-only) + tighter atr_sl (1.0 vs 1.75 baseline)
    # Single-cohort substrate change + post-entry magnitude clip.
    # Mechanism is basin-relocation-orthogonal by construction.
    results_d, faxm_d, _strat_d = run_model(
        "D' (LTC-only + tighter SL)",
        ("LTCUSDT",),
        atr_tp=3.5,                # UNCHANGED from baseline Model D
        atr_sl=1.0,                # CHANGED from 1.75 — tighter SL is the axis
        apply_r1=True,             # UNCHANGED (Model D has R1)
        # NO R2, NO R3 changes — baseline Model D config preserved
        n_trials=n_trials,
        ensemble_size=ensemble_size,
        oof_persist_path=OOF_PARQUET_PATH,
        feature_columns=active_feature_columns,
        bounds_profile=bounds_profile,
        **_r5_kwargs,
    )
    all_results = results_d
    _all_faxm_logs = faxm_d
    _r5_model_results = [results_d]
    _post_dispatch_fi_strategies = [("Model_D_LTC_specialist", _strat_d)]
```

### 3.2 CLI invocation

```bash
uv run python run_baseline_v1.py \
    --symbols LTCUSDT \
    --iteration-label v1-028 \
    --exploration \
    --seeds 2 \
    --ensemble-size 3 \
    --n-trials 35 \
    --reports-dir reports-v1/iteration_v1-028
```

### 3.3 Pinned values

- `V1_ITER028_UNIVERSE = ("LTCUSDT",)` — single-cohort
- `atr_sl = 1.0` (CHANGED; baseline = 1.75); `atr_tp = 3.5` (UNCHANGED)
- `apply_r1 = True` (UNCHANGED — Model D baseline has R1 consecutive-SL cooldown)
- `seeds = (42, 123)` (multi-seed mitigation per cycle-3 §5.4)
- `ensemble_size = 3`
- `n_trials = 35`
- `V1_FEATURE_COLUMNS_PRUNED` (43 cols — baseline pruned feature set, no feature changes)
- `feature_columns_pinned = list(V1_FEATURE_COLUMNS_PRUNED)` — MANDATORY per v1 skill

### 3.4 LM Master Phase 4.5 Responses

**RESERVED FOR LM MASTER PHASE 4.5 ADVISORY** (filled in by QR after Phase 4.5 fires).

### 3.5 Axis Family Declaration (v1 mandatory)

- **Axis family**: `per-cohort-specialization-LTC-v2` (NEW 15th family)
- **Justification for NEW family vs reuse of /022's literal `per-cohort-specialization-LTC`**:
  - /022 mechanism: pre-entry asymmetric long-suppress BTC-trend gate at -4%. Targets basin-contingent direction asymmetry.
  - /028 mechanism: post-entry tighter ATR-based SL multiplier (1.0 vs 1.75). Targets basin-invariant loss-tail magnitude.
  - DIFFERENT mechanism class → DIFFERENT family per `feedback_v1_per_cohort_saturation_asymmetric_rotation.md` (mechanism class distinguishes families).
- **Critic Check 14 verification**: src/ diff is bounded to (a) NEW `V1_ITER028_UNIVERSE` constant + export, (b) NEW elif branch in runner. NO changes to risk_v2/gates/feature definitions. Single mechanism class change.

### 3.6 Wall-Clock Estimate (CRITICAL — Phase 5.5 BLOCK if missing or > 1.6h)

- **Modal estimate**: 30 min
- **High estimate**: 60 min (Optuna TPE variance at n_trials=35 × 2 seeds)
- **Hard cap**: 2h (skill EXPLORATION cap)
- **Kill-switch**: 90 min (engineer terminates if wall-clock exceeds 1.5h projected against the 2h cap)
- **Baseline reference**: /022 single-cohort LTC-only single-seed=42 ran 541 s (~9 min). /028 = 2 seeds + larger n_trials (35 vs 18 at /022) ≈ 2× = ~30 min modal.

---

## Section 4 — Falsifiers (F1-F8 + F-AXIS-MECHANISM)

### F1 — LTC-only OOS per-trade Sharpe Δ vs baseline LTC-in-pool OOS per-trade Sharpe anchor

- **Anchor**: baseline LTC-in-pool OOS per-trade Sharpe = **-0.267** (from `reports-v1/iteration_v1-baseline/out_of_sample/per_symbol.csv` derived)
- Anchor-frame BINDING per `feedback_v1_anchor_frame_ambiguity.md` (carried over from /022 §4): use comparison.csv daily-annualized "sharpe" semantics post-multi-seed; multi-seed mean.

| Outcome | F1 OOS Sharpe Δ band | Verdict class |
|---|---|---|
| PROMISING-strong | Δ ≥ +0.40 | **PROMISING** |
| PROMISING-borderline | +0.20 ≤ Δ < +0.40 | **PROMISING-INERT-favorable** |
| INERT | -0.20 ≤ Δ < +0.20 | **INERT-no-effect** |
| NEGATIVE-CLEAN | -0.55 < Δ < -0.20 | **NEGATIVE-clean** |
| **NEGATIVE-CATASTROPHIC** | **Δ ≤ -0.55** | **NEGATIVE-CATASTROPHIC** (saturation rule prediction) |

### F2 — Embargo/look-ahead PASS (structural; automatic)

`walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` (the iter-v3/058 fix). Foundation discipline; Phase 6.0 Critic re-verifies.

### F3 — LTC-only IS per-trade Sharpe Δ vs baseline LTC-in-pool IS per-trade Sharpe anchor

- **Anchor**: baseline LTC-in-pool IS per-trade Sharpe = **+0.004** (from /022 §0.3 — same data)
- **F3 INERT band**: |Δ| < 0.15
- **F3 catastrophic floor**: F3 ≤ -0.30 (basin sign reversal in IS = catastrophic regardless of OOS)

### F4 — Feature ADF stationarity (informational; no new features)

No new features added (feature_columns_pinned = baseline V1_FEATURE_COLUMNS_PRUNED). F4 INFORMATIONAL.

### F5 — PSR_monthly_vs_0 OOS (basin-health signal)

- **Floor**: PSR_monthly_vs_0 OOS ≥ 0.10 (above noise band; structural)
- /022 OOS PSR = 0.011 (catastrophic). /028 OOS PSR > 0.10 is mechanism-survival evidence.
- INFORMATIONAL; does not flip verdict on its own.

### F6 — Per-symbol IS direction (vacuous — only 1 symbol)

LTC-only dispatch ensures 100% LTC trades. F-AXIS #1 (per Section 4.X) verifies.

### F7 — Per-symbol IS/OOS sign agreement (LTC only)

- Pre-registered: LTC IS net_pnl_pct sign × LTC OOS net_pnl_pct sign
- baseline anchor: IS +3.27% (positive) / OOS -47.25% (negative) → DISAGREEMENT (baseline already F7 FAIL)
- /028 F7: IS positive ∧ OOS positive → **PASS**. Otherwise FAIL (CARRIES baseline's F7 fail forward — informational).

### F8 — LTC-only trade count band

- **QR band**: IS trades ∈ [80, 180]; OOS trades ∈ [20, 60]
- **LM Master band** (to be populated post-Phase-4.5)
- Tighter SL is expected to INCREASE trade count slightly (R1 cooldown fires more often after more stop-losses; net effect uncertain; trade count band wide).

### F-AXIS-MECHANISM (compound 4-sub-check; LOAD-BEARING per /022 lesson)

These verify the MECHANISM operates as designed independent of F1 magnitude:

- **F-AXIS #1 dispatch**: `df['symbol'].unique() == ['LTCUSDT']` ✓ (single-cohort)
- **F-AXIS #2 SL fire rate**: `(df['exit_reason'] == 'stop_loss').mean() ∈ [0.40, 0.75]` (tighter SL means MORE SL fires per trade exit; baseline LTC OOS SL share was 62%; expect 50-70%)
- **F-AXIS #3 loss magnitude clip**: `(df[df['exit_reason']=='stop_loss']['net_pnl_pct'].mean()) ∈ [-3.5%, -2.5%]` (tighter SL caps SL fires near -3%; baseline was -5 to -7%)
- **F-AXIS #4 n_eff_per_cell ∈ [6, 10]** (consistent with /022; tighter SL doesn't change Optuna budget but may shift label class balance — see LM Master Phase 4.5 for refinement)

**Reconciliation discipline (CARRY-FORWARD from /022 §4)**: F-AXIS-MECHANISM passing on its own does NOT imply F1 success. /022 had 4/4 F-AXIS PASS with F1 catastrophic — mechanism ≠ outcome. /028 F1 verdict = OOS Sharpe direction independent of F-AXIS-MECHANISM.

### F-PORTFOLIO (informational; cannot determine verdict)

Single-cohort LTC-only run; no portfolio metric meaningful. INFORMATIONAL.

---

## Section 5 — Predicted Verdict Distribution

Per `feedback_v1_per_cohort_saturation_asymmetric_rotation.md` ASYMMETRIC_ROTATION prior class baseline + mechanism-specific upgrades:

### 5.1 QR initial priors (pre-LM-Master)

| Verdict class | Probability |
|---|---|
| PROMISING (F1 ≥ +0.40) | **15%** |
| PROMISING-INERT-favorable (+0.20 ≤ F1 < +0.40) | **20%** |
| INERT-no-effect (-0.20 ≤ F1 < +0.20) | **35%** |
| NEGATIVE-clean (-0.55 < F1 < -0.20) | **20%** |
| NEGATIVE-CATASTROPHIC (F1 ≤ -0.55) | **10%** |

### 5.2 Rationale

**Why PROMISING tail is HIGHER (15%) vs /022's 5%**:
- /022 EDA mechanism counterfactual: +12.45% OOS Δ on baseline roster (small lift)
- /028 EDA mechanism counterfactual: **+36.17% OOS Δ on baseline roster** (3× larger lift)
- Larger pre-mechanism signal supports higher PROMISING tail at the same basin-survival probability.
- **CRITICAL**: this assumes basin-survival probability is ≈ 50-60% (mechanism's basin-orthogonality property). If basin survival is closer to /022's failure (effectively 0% — mechanism dissolved), the +36% is illusory.

**Why NEG-CAT tail is LOWER (10%) vs /022's also 10%**:
- /028 mechanism (post-entry SL) is structurally different from /022 mechanism (pre-entry gate). The /022 NEG-CAT mode (gate dissolves under basin relocation) does NOT apply.
- However, ASYMMETRIC_ROTATION cohort prior class still binds NEG-CAT at 10-15% per saturation rule; /028 keeps 10% as a conservative lower bound.
- Possible NEG-CAT modes: (a) tighter SL clips winners that would have recovered (false-loss conversion), (b) basin relocation finds a worse roster than baseline (mechanism does nothing).

**Why INERT modal is HIGHER (35%) vs /022's also ~40%**:
- The mechanism is BASIN-ORTHOGONAL, so the basin-relocation failure mode (which gave /022 its NEG-CAT) maps to INERT here (the SL fires, trades clip, but basin moves elsewhere). The expected outcome on a NEW basin where SL fires equally is INERT — clipping losses + smaller gains = wash.
- Pre-Phase-4.5 LM Master will likely retune; expect /028 to retain ~30-40% INERT modal.

### 5.3 LM Master priors slot

LM Master Phase 4.5 will provide refined priors (likely similar magnitude but different bin shape per /022 lesson — LM Master tail upweighting was reliably directionally correct at 4/4 mechanism-level forecasts in cycle-3). QR will adopt or contrast post-Phase-4.5.

---

## Section 6 — Failure Modes

### 6.1 Single-cohort basin lottery at multi-seed=2

Single-cohort isolation IS basin lottery; 2 outer seeds is the minimum mitigation. If both seeds land in adverse basins (basin lottery × 2), /028 NEG-CAT outcome materializes.

**Mitigation**: explicit 2-seed average reported in comparison.csv (handled by runner). Per-seed Sharpe variance flagged in engineering_report.md.

### 6.2 Tighter SL clips winners

A tighter SL converts some near-stop trades that would have recovered into realized losses (false-loss conversion). This is a known SL-tuning trade-off.

**Empirical bound** (from baseline 34-trade OOS roster):
- Trades with `exit_reason == 'take_profit'` (4 OOS trades = 12% of OOS) cleared the +TP barrier. At `atr_sl=1.0`, NONE of these would convert to stop-losses (the SL fires before TP, but TP fires require crossing +3.5×ATR — if SL is now 1.0×ATR, the SL fires earlier, before TP can fire).
- This is a real risk: take-profit trades are bounded by the SL/TP race condition. At baseline `atr_sl=1.75`, TP fired 4× OOS. At `atr_sl=1.0`, some of these may convert to SL fires.
- Mechanism's net effect = (loss-tail clip from -5/-7% to -3%) vs (TP conversion to SL = +5% lost per converted trade × N converted).

**Quantitative check**: if 2 of 4 TP trades convert to SL, net change = +36% PnL (loss clip gain) - 8% (TP→SL conversion cost) = ~+28%. Mechanism still net positive.

### 6.3 R1 cooldown saturation (per Model D baseline)

Tighter SL means more SL fires; R1 cooldown (K=3 consecutive SL → 27-candle cooldown) fires more often. **Cooldown periods reduce trade count** — net effect could push trade count below F8 lower bound (20 OOS).

**Mitigation**: F8 floor of 20 OOS trades is the LIVE-WALL check. If observed < 20, classify as DEGENERATE_PREDICTOR (analogous to /006 universe outcome).

### 6.4 Stateless mechanism — no deadlock risk

The atr_sl change is a CONFIG modification at training time. No state propagation. No deadlock-impossibility proof needed (vs STATEFUL mechanisms like /054 v3 drawdown brake).

### 6.5 Basin still lottery despite orthogonality

The mechanism is basin-orthogonal, but the trade ROSTER is still basin-determined. If the new basin places no trades in volatile regimes, the SL never fires and the mechanism is wasted. The +36% counterfactual is ONLY descriptive on the BASELINE roster.

**This is the dominant risk for /028**. The mechanism IS robust, but only when it fires. The new roster may have fewer SL-eligible trades.

### 6.6 PROMISING-MECHANICAL adjacency risk

Per `feedback_promising_mechanical_subtype.md`: if /028 produces a PROMISING outcome that is drag-removal mechanical (just clipping losses) rather than signal-new, classify as PROMISING-MECHANICAL (non-compoundable). This is a definitional distinction at Phase 7+8 closeout; not a falsifier at design time.

### 6.7 Wall-clock breach (low probability)

2-seed × n_trials=35 × LTC-only ≈ 30 min modal. Outliers (Optuna TPE variance) could push to 60-90 min. **Kill at 90 min** per Section 3.6.

---

## Section 7 — Optional / informational metrics

- **n_eff_per_cell_median** (basin-substrate-test sister): tracks Optuna effective trials per (symbol, month) cell. Baseline /022 = 8. Expected /028 ≈ 8-10 (tighter SL shifts label class balance but doesn't change TPE budget).
- **DSR / PSR** (EXPLORATION-mode informational per `feedback_v3_dsr_mode_artifact.md`).
- **Per-month trade count** (calibration check vs F8 bands).
- **Per-trade hold time** (calibration check; tighter SL reduces avg hold).
- **SL fire rate** (F-AXIS #2 directly).
- **Mean loss magnitude in SL trades** (F-AXIS #3 directly).

---

## Section 8 — Verdict Matrix

| Row | F1 | F3 | F-AXIS 1-4 | F8 | Verdict class |
|---|---|---|---|---|---|
| 1 | ≥+0.40 | IS positive | ALL PASS | inside | PROMISING |
| 2 | +0.20 to +0.40 | IS positive | ALL PASS | inside | PROMISING-INERT-favorable |
| 3 | -0.20 to +0.20 | IS positive | ALL PASS | inside | INERT-no-effect |
| 4 | -0.20 to +0.20 | IS negative | ALL PASS | inside | INERT-CONTAMINATED (IS sign flip; non-compoundable) |
| 5 | -0.55 to -0.20 | IS positive or neg | ALL PASS | inside | NEGATIVE-clean (mechanism-passes-outcome-fails per /022 pattern) |
| 6 | ≤-0.55 | any | any | any | **NEGATIVE-CATASTROPHIC** (saturation prediction) |
| 7 | any | any | F-AXIS #1 FAIL (LTC-only dispatch fails) | any | TECHNICAL FAILURE |
| 8 | any | any | any | F8 OUTSIDE | DEGENERATE (trade count out of band) |

---

## Section 9 — Library Stack

- `mlfinlab==1.4` (validation; not modified at /028)
- `pypbo` (PBO; not invoked at single-cohort EXPLORATION)
- `fracdiff>=0.10` (not used at /028 — no new features)
- `statsmodels` (ADF informational; not invoked)
- LightGBM (baseline strategy; atr_sl is upstream of LightGBM at triple-barrier labeling stage)

No new dependencies. No version bumps required.

---

## Section 10 — Implementation Spec (CRITICAL detail)

### 10.1 No `--no-engineering-report` flag at launch (per /017/019/020/021/022 Rec)

Engineer launches with default engineering_report.md generation enabled. Per `feedback_v1_engineering_report_contract.md` and cycle-3 §5 carry-forward.

### 10.2 Reports artifacts expected

```
reports-v1/iteration_v1-028/
├── comparison.csv
├── engineering_report.md         (REQUIRED for Phase 7.5)
├── in_sample/
│   ├── trades.csv
│   ├── per_symbol.csv
│   ├── monthly_pnl.csv
│   ├── daily_pnl.csv
│   ├── dsr.json
│   ├── feature_importance_Model_D_LTC_specialist.csv
│   ├── ic_matrix.csv
│   ├── adf_test.csv
│   ├── per_regime.csv
│   └── quantstats.html
└── out_of_sample/                 (same structure)
```

### 10.3 Pre-flight verification (Engineer in Phase 6 setup)

- [ ] `V1_ITER028_UNIVERSE = ("LTCUSDT",)` exported from `crypto_trade.features_v1`
- [ ] runner elif branch dispatches LTC-only at `iteration_label == "v1-028"`
- [ ] `atr_sl=1.0` literal in the new elif branch
- [ ] kline data fresh (`data/LTCUSDT/8h.csv` mtime within 16h)
- [ ] V1_FEATURE_COLUMNS_PRUNED has 43 features (assert in runner)
- [ ] 2 outer seeds (42, 123) properly passed via `--seeds 2`
- [ ] Phase 5.5 gate PASS commit referenced in engineer setup commit

### 10.4 Engineer launch protocol — engineering report blocking

Per /017/019/020/021/022 Critic Rec carry-forward: engineering_report.md MUST be present at Phase 7.5 dispatch. If absent at dispatch, Critic emits BLOCK-PENDING-FIX per /022 BLOCK-PENDING-FIX precedent.

**Brief Section 10.4 pre-commitment**: "no Phase 7.5 Critic dispatch without engineering_report.md present (CARRY-FORWARD from /022)".

### 10.5 Wall-clock kill-switch

- Modal expected ≈ 30 min
- HIGH expected ≈ 60 min
- HARD CAP = 2h
- Kill at 90 min (Engineer's `--time-limit-min 90` flag if needed)

### 10.6 Critic Phase 7.5 Watch List (forward-binding)

Per LM Master /027 Closing + cycle-3 §5.1 lesson on defensive runtime checks:

- **NEW defensive check item**: any NEW assert added in src/ must be unit-tested with a real instance (NOT mock/partial fake) — Phase 6.0 pre-flight verifies. No new asserts in /028 per Section 3.1 (clean spec, no F-AXIS-#1 mandate at /028).
- **F-AXIS reconciliation table** mandatory in engineering_report.md (per /022 §4 carry-forward).
- **Anchor-frame BINDING**: pre-compute per-cohort LTC-only daily-annualized Sharpe directly from comparison.csv; lock F1 to comparison.csv "sharpe" semantics.

---

## Section 11 — Alternates for /029+ (cycle-4 EXPLORATIONs #2-10)

### 11.1 Verdict-conditional /029 routing

- **PROMISING (F1 ≥ +0.40)**: /029 = **C×E altcoin de-concentration** axis MANDATORY per /027 §9 + cycle-3 §4.2 (C_link × E_dot OOS Pearson +0.6027 breach unresolved). Candidate mechanism = per-cohort drawdown brake (STATEFUL — deadlock proof required) OR vol-target ceiling on altcoin cohort.
- **INERT/NEGATIVE-clean**: /029 = **sample-weighting** (López de Prado AFML Ch. 4 uniqueness weighting OR hard-negative oversampling). NEVER-TRIED in v1 catalog. Cycle-3 §4.3 cycle-4 candidate.
- **NEGATIVE-CATASTROPHIC**: /029 = **substrate-change pivot** (XGBoost head-to-head — cycle-3 §4.3 candidate B). Saturation rule deepens; D-specialist axis irrecoverable.

### 11.2 /030-/033 = combinatorial exploration of remaining cycle-4 candidates

Depending on /028+/029 outcomes:
- C×E altcoin de-concentration (if not already at /029)
- Sample-weighting (if not already at /029)
- XGBoost head-to-head (if not already at /029)
- Meta-labeling architecture (deferred per v3/017 PATH C precedent risk)

### 11.3 /034-/037 = secondary candidates

- DOT pre-classification + DOT-only specialist (only if DOT class = POSITIVE_EVERYWHERE per `feedback_v1_per_cohort_saturation_asymmetric_rotation.md`)
- Universe contraction to 4-symbol pool (drop LTC entirely)
- Risk gate threshold tuning (low priority per cycle-3 knob-tuning dead path)

### 11.4 /038 first cycle-4 CONFIRMATION

Bundling decision deferred until cycle-4 EXPLORATIONs complete. Earliest at /038 (after 10 EXPLORATIONs).

### 11.5 Lessons forward-binding (codified at this brief)

- **EDA-driven mechanism selection MANDATORY** at brief Section 0.4. Counterfactual on baseline roster + basin-orthogonality reasoning required.
- **Per-cohort with ATR/SL tuning** is a DIFFERENT axis class from per-cohort with regime gates. Mechanism class distinguishes families.
- **HIGH-RISK + multi-seed mitigation** combo is the cycle-4 default for any axis touching Optuna training-objective domain.

---

## Section 12 — Catalog Closeout Plan (Phase 8)

After Phase 7 evaluation completes:

1. Append `/028` row to `briefs-v1/exploration_catalog.md` with axis, family, IS Δ, OOS Δ, verdict.
2. Update `cycle3_closeout.md` reference if any cycle-3 finding revised by /028 evidence.
3. Issue tag `v0.v1-028` at Phase 8 commit.
4. Update LM Master directional + methodology track records.
5. If verdict = PROMISING, add to /038 CONFIRMATION substrate candidate list.
6. Decision summary appended to next iteration's brief Section 0.

---

## Section 13 — Phase 5.5 self-check (QR pre-handoff)

QR self-check matrix per v1 skill §"Phase 5.5 Gate":

| Section | Required | Present | Notes |
|---|---|---|---|
| 0 — Position in cycle / pivot context | YES | YES | §0.1-0.7 complete |
| 0.6 — Axis Family Declaration + Rotation Discipline | YES (v1 mandatory) | YES | NEW family + rotation VALID + rationale |
| 1 — Hypothesis | YES | YES | H_028 single-line + predicted band |
| 2 — IS-Only Evidence (numerical tables) | YES | YES | §2.1-2.7 from committed analysis script `5f76b4a` |
| 2.5 — HIGH-RISK Axis Declaration | YES (v1 mandatory) | YES | HIGH-RISK + multi-seed mitigation declared |
| 3 — Implementation Spec | YES | YES | §3.1-3.6 single src/ file change |
| 3.4 — LM Master Phase 4.5 Responses | RESERVED | RESERVED | filled post-Phase-4.5 |
| 3.5 — Axis Family Declaration | YES | YES | NEW 15th family + Critic Check 14 verification path |
| 3.6 — Wall-Clock Estimate | YES (BLOCK if missing) | YES | 30 min modal, 90 min kill |
| 4 — Falsifiers (F1-F8 + F-AXIS-MECHANISM) | YES | YES | per /022 carry-forward |
| 5 — Predicted Verdict Distribution | YES | YES | priors with rationale + LM Master slot |
| 6 — Failure Modes | YES | YES | §6.1-6.7 |
| 7 — Optional / informational metrics | YES | YES | §7 |
| 8 — Verdict Matrix | YES | YES | Rows 1-8 |
| 9 — Library Stack | YES | YES | no version bumps |
| 10 — Implementation Spec (CRITICAL detail) | YES | YES | §10.1-10.6 |
| 11 — Alternates for /029+ | YES | YES | verdict-conditional routing + dead paths |
| 12 — Catalog Closeout Plan | YES | YES | Phase 8 actions |
| 13 — Phase 5.5 self-check | YES | YES | (this section) |

**Phase 5.5 readiness**: ALL sections complete except RESERVED §3.4 + §5.3 LM Master slots. Phase 4.5 LM Master advisory expected NEXT.

---

**END OF BRIEF**
