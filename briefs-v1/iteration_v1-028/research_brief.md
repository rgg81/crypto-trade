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

**The right mechanism for /028 must be BASIN-RELOCATION-INOCULATED** — operate on properties that survive retraining as much as possible. Note (LM Master Rec #2): no mechanism is truly basin-orthogonal-by-construction when it changes labels upstream. `atr_sl` is PARTIAL inoculation, not immunity.

EDA-derived candidate ranking (`analysis/iteration_v1-028/ltc_mechanism_robustness_predictions.csv`):

| Candidate | Δ on baseline roster | Basin inoculation | Notes |
|---|---:|---|---|
| **E_tighter_atr_sl** (cap loss at -3%) | **+36.17%** | **PARTIAL — SL trigger basin-survivable, BUT atr_sl upstream of label generation shifts class balance** | LM Master Rec #2: BOTH basin AND label distribution shift simultaneously. Mechanism more roster-robust than /022's pre-entry gate but NOT immune. |
| C_meta_labeling (conf > 0.85) | +15.56% | NONE — conf is basin output | OOS conf calibration INVERTED ([0.85,1.00) = 23% WR) |
| F_prior_month_drawdown_gate | +2.88% | MEDIUM — stateful but not targeted | only 1 month qualifies; weak signal |
| A_R5_vol_ceiling | +0.77% | PARTIAL | proxy via |pnl|; real impl needs NATR ex-ante |
| B_feature_subset | N/A — requires backtest | NONE — substrate change is the basin | full retrain required; no closed-form proxy |
| D_sample_weighting | N/A — requires backtest | NONE — substrate change is the basin | full retrain required; no closed-form proxy |

**Selected**: **E_tighter_atr_sl per-cohort tuning** for LTC-only Model D' specialist. Quantitative target = baseline `atr_sl=1.75` → **`atr_sl=1.0`** (cap typical loss at ~3% instead of ~5.25%, with TP unchanged at `atr_tp=3.5`). Expected modal lift OOS Sharpe Δ +0.25 to +0.45 (LM Master Rec #5: basin-survival ratio 0.5-0.7 caps the +36% baseline-roster lift).

**Why E ranks #1**:
1. Largest predicted Δ on the baseline roster (+36% PnL → ~+0.8 OOS Sharpe lift IF mechanism survives basin relocation at proportional scale; LM Master Rec #5 caps expected survival at 0.5-0.7 → modal lift +18-25% PnL → OOS Sharpe Δ +0.25 to +0.45).
2. **PARTIAL basin inoculation** (LM Master Rec #2 REFRAMING — supersedes initial "basin-relocation-orthogonal by construction"). atr_sl is **upstream of triple-barrier label generation** (`triple_barrier_labels` reads `atr_sl_multiplier` to set the lower barrier). Tightening 1.75→1.0 narrows lower barrier by 43% and changes the LABELS LightGBM trains on. Class balance shifts: MORE -1 labels with SMALLER magnitudes. The mechanism shifts BOTH basin (Optuna best_params) AND label class distribution simultaneously — TWO basin-relocation vectors, not zero. SL trigger condition still acts on realized price path (a substrate-invariant property) and is more roster-robust than /022's pre-entry asymmetric gate, but the basin Jaccard vs baseline is expected at 0.05-0.15 (similar /022's 0.093).
3. **GENUINELY DIFFERENT from /022**. /022 = pre-entry filter targeting basin-contingent direction asymmetry; /028 = upstream triple-barrier parameter + post-entry magnitude clip targeting basin-survivable loss-tail distribution. The /022 failure mode (gate fires + asymmetry dissolves + trades remain unaffected) does NOT apply (the SL fires on price path, not on a basin-contingent property), but a DIFFERENT failure mode applies: label class balance shift may relocate Optuna away from the regions where the +36% counterfactual lift was concentrated.
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

**H_028**: LTC-only training (Model D' specialist substrate) **+ tighter ATR-based stop-loss multiplier (atr_sl=1.0 vs baseline 1.75)** caps the dominant loss channel of LTC OOS (stop-loss exits at -5 to -7% magnitude) at the cost of converting some take-profit-eligible trades into earlier SL fires. The mechanism is **PARTIAL basin inoculation** (LM Master Rec #2):

(a) The SL trigger fires on the realized price path crossing a multiple of ATR — a property of price dynamics that is more roster-robust than /022's pre-entry asymmetric gate.
(b) HOWEVER, `atr_sl` is upstream of triple-barrier label generation: tightening 1.75→1.0 narrows the lower barrier by 43%, shifts class balance (MORE -1 labels with SMALLER magnitudes), AND relocates the Optuna basin under retraining. So the mechanism shifts BOTH basin AND label class distribution — TWO basin-relocation vectors.
(c) LTC's 8h volatility regime (ATR scale) is substrate-invariant; the trigger CONDITION survives basin relocation, but the EFFECTIVE roster the mechanism operates on does not.
(d) Therefore the +36% baseline-roster counterfactual is bounded by the basin-survival ratio (LM Master Rec #5 estimates 0.5-0.7) → expected lift +18-25% PnL → OOS Sharpe Δ +0.25 to +0.45.

**Predicted outcome** (per Section 5 priors below): modal verdict PROMISING-INERT-favorable (LM Master Rec #5 territory), with the long-tail towards PROMISING reachable only if basin-survival ratio lands ≥0.7 AND F-AXIS #5 OOS TP-exit count ≥1 (LM Master Rec #6: if all 4 baseline OOS TP-eligible trades convert to SL, the mechanism degenerates to loss-clipping-only and verdict cannot exceed PROMISING-INERT regardless of F1).

**Predicted F1 OOS Sharpe Δ band**: [-0.15, +0.55]. Modal +0.25-0.45 per LM Master Rec #5. NEG-CAT (-0.55+) tail at 13% (LM Master Rec #3) — ASYMMETRIC_ROTATION prior class binds NEG-CAT ≥10% AND label class balance shift adds a 2nd basin-relocation vector; not orthogonal-by-construction immunity.

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

**Mitigation (HIGH-RISK with v1-runner-compatible variance budget)**:

Cycle-3 §5.4 multi-seed mandate has TRIPPED (cumulative ≥1σ negative count reached 5). The mandate binds HIGH-RISK axes. /028 IS HIGH-RISK. Multi-seed variance budget REQUIRED.

**v1 runner has NO `--seeds` flag** (LM Master Rec #1 MECHANICAL — `--seeds 2 --ensemble-size 3` would FAIL at argparse). Variance budget mapped to **inner ensemble** per v1-style 10-seed ensemble convention (`feedback_v1_ensemble.md`).

**Effective config (CORRECTED per LM Master Rec #1)**: `--exploration --iteration 028 --pruned-features --n-trials 35 --ensemble-size 10`. Estimated wall-clock ~30 min (CONFIRMATION-mode variance budget at EXPLORATION axis; LTC-only single-cohort). Mode tag stays EXPLORATION (n_trials=35 NOT 50).

**HIGH-RISK declaration with `--ensemble-size 10` variance mitigation** is the cycle-4 working position.

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
    # Single-cohort substrate change + upstream triple-barrier param change.
    # Mechanism is PARTIAL basin inoculation (atr_sl is upstream of label
    # generation; shifts BOTH basin AND label class distribution).
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
    --ensemble-size 10 \
    --n-trials 35 \
    --reports-dir reports-v1/iteration_v1-028
```

**CORRECTION (LM Master Rec #1 ADOPTED)**: v1 runner argparse does NOT have a `--seeds` flag (would fail at argparse). Variance budget mapped to inner ensemble (`--ensemble-size 10`) per v1-style 10-seed ensemble convention (`feedback_v1_ensemble.md`). CONFIRMATION-mode variance budget at EXPLORATION axis (single-cohort cost ≈ 30 min). Mode tag stays EXPLORATION (n_trials=35 NOT 50).

### 3.3 Pinned values

- `V1_ITER028_UNIVERSE = ("LTCUSDT",)` — single-cohort
- `atr_sl = 1.0` (CHANGED; baseline = 1.75); `atr_tp = 3.5` (UNCHANGED)
- `apply_r1 = True` (UNCHANGED — Model D baseline has R1 consecutive-SL cooldown)
- `ensemble_size = 10` (CORRECTED from 3 per LM Master Rec #1)
- `n_trials = 35`
- `V1_FEATURE_COLUMNS_PRUNED` (43 cols — baseline pruned feature set, no feature changes)
- `feature_columns_pinned = list(V1_FEATURE_COLUMNS_PRUNED)` — MANDATORY per v1 skill

### 3.4 LM Master Phase 4.5 Responses

LM Master `briefs-v1/iteration_v1-028/lgbm_advisor.md` issued 7 recommendations across MECHANICAL, REFRAMING, PRIORS, F-AXIS, INOCULATION, MOST-IMPORTANT, /029-STAGING. Per-recommendation responses:

| # | LM Master rec | Response | Rationale |
|---|---|---|---|
| 1 | MECHANICAL: `--ensemble-size 10 --n-trials 35` (NO `--seeds`; v1 runner has no `--seeds` flag) | **ADOPTED** | Brief §3.2/3.3 invocation CORRECTED. v1 runner argparse does not accept `--seeds`. Variance budget mapped to inner ensemble (ensemble_size=10) per v1-style 10-seed ensemble convention (`feedback_v1_ensemble.md`). |
| 2 | REFRAMING: `atr_sl` is upstream of triple-barrier label generation; NOT basin-orthogonal — PARTIAL basin inoculation only (BOTH basin AND label class distribution shift) | **ADOPTED** | §0.4 + §1 reframing updated. Phase 7.4 verdict assignment will compare TWO basin-relocation dimensions: (a) Optuna best_params shift (basin vector), (b) label class balance shift (training distribution vector). |
| 3 | PRIORS: 12/18/35/22/13 (vs QR 15/20/35/20/10); NEG total 35% vs QR 30%; PROMISING tail compressed | **ADOPTED** | §5.1 priors updated. NEG-CAT raised to 13% per ASYMMETRIC_ROTATION binding + 2nd basin-relocation vector argument. PROMISING -3pp (basin-survival ratio 0.5-0.7 caps lift below +0.40). |
| 4 | F-AXIS: pre-register #1 LTC-only PASS; #2 trade-count IS [70,150] / OOS [22,55]; #3 SL fire-rate COUNTER-INTUITIVE 75-90% (tighter SL → MORE fires, not less); #4 n_eff [6,10]; **#5 exit-reason distribution LOAD-BEARING** (TP=0 OOS → verdict capped PROMISING-INERT) | **ADOPTED** | F-AXIS hierarchy refactored. §4 now adds F-AXIS #5 (exit-reason distribution: OOS SL 75-90% / TP 0-8% / timeout 10-20%) as LOAD-BEARING. F-AXIS #3 SL fire-rate counter-intuitive prediction codified (75-90%, not 50-70%). LM Master's tighter trade-count bands (LM [70,150]/[22,55]) noted alongside QR's wider [80,180]/[20,60]. |
| 5 | INOCULATION: PARTIAL not IMMUNITY — baseline-roster +36% × basin-survival ratio 0.5-0.7 = expected /028 lift +18-25% PnL → OOS Sharpe Δ +0.25 to +0.45 (PROMISING-INERT-FAV modal) | **ADOPTED** | §0.4 + §1 narrative updated. Predicted F1 band §1 refined: modal +0.25-0.45 (PROMISING-INERT-FAV territory); PROMISING-tier (Δ≥+0.40) requires survival ratio ≥0.7. |
| 6 | MOST-IMPORTANT: F-AXIS #5 TP-exit count is LOAD-BEARING (NOT F-AXIS #3 SL fire-rate); baseline LTC OOS had 4 TP exits contributing +31.64% PnL; if atr_sl=1.0 converts ≥2 of 4 to SL at retrained roster, net effect collapses below +0.20 OOS Sharpe Δ regardless of clean-clipping of moderate-loss bucket | **ADOPTED** | F-AXIS hierarchy refactored §4: F-AXIS #5 replaces F-AXIS #3 as the LOAD-BEARING diagnostic. §6.2 Failure Mode 6.2 (Tighter SL clips winners) reframed: not just bounded risk but PRIMARY verdict-determining variable. |
| 7 | /029-STAGING: PROMISING → DOT-specialist; PROMISING-INERT-FAV → DOT-specialist; INERT → sample-weighting (López de Prado AFML Ch.4 inverse-concurrency; UNUSED in v1); NEG-clean → sample-weighting; NEG-CAT → FUNDAMENTAL RE-QUESTION (3rd NEG-CAT same prior class closes per-cohort axis permanently); XGBoost OR universe contraction | **ADOPTED** | §11.7 NEW: verdict-conditional /029 staging per LM Master §7 matrix. Replaces §11.1 routing (kept §11.1 for cycle-4 thematic context but §11.7 binds /029 specifically per LM Master). |

**Methodology track**: LM Master Phase 4.5 invocation #6 (cycle-3 was 5/5 methodology + 4/8 directional). Trust budget: methodology recs (#1) ADOPTED unconditionally. Directional recs (#2-7) ADOPTED per merit (consistent with cycle-3 4/8 directional record — LM Master's tail-upweighting was reliably directionally correct).

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
- **Baseline reference**: /022 single-cohort LTC-only single-seed=42 + ensemble_size=3 ran 541 s (~9 min). /028 = ensemble_size=10 + n_trials=35 (vs 18 at /022) ≈ 3.3× = ~30 min modal.

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
- **LM Master band** (Rec #4 ADOPTED): IS [70, 150] modal 105 / OOS [22, 55] modal 35
- **ADOPTED pass band**: QR-wider [80, 180] / [20, 60] (more permissive — minimum-floor envelope). LM Master modals (105/35) used as expected-value reference.
- Tighter SL is expected to DECREASE trade count slightly via R1 cooldown engagement (tighter SL → more SL fires → R1 cooldown engages more → fewer trades net; effect direction reversed from initial QR guess per LM Master Rec #4).

### F-AXIS-MECHANISM (compound 5-sub-check; F-AXIS #5 LOAD-BEARING per LM Master Rec #6)

These verify the MECHANISM operates as designed independent of F1 magnitude. **Hierarchy refactored per LM Master Rec #4 + Rec #6**: F-AXIS #5 (TP-exit count) is the LOAD-BEARING diagnostic for /028, REPLACING F-AXIS #3 SL fire-rate as the verdict-determining variable (F-AXIS #3 was load-bearing at /022; at /028 the SL fire-rate is mechanically forced upward by the tighter SL and is no longer the binding constraint).

- **F-AXIS #1 dispatch** (LM Master pre-registered): `df['symbol'].unique() == ['LTCUSDT']` ✓ — BINARY PASS
- **F-AXIS #2 trade-count band** (LM Master tighter, QR wider): LM IS [70, 150] modal 105 / OOS [22, 55] modal 35 (tighter SL → R1 cooldown engages more); QR safety-margin IS [80, 180] / OOS [20, 60]. **ADOPTED**: pass band = QR-wider IS [80,180] / OOS [20,60], LM Master modals (105/35) used as expected values.
- **F-AXIS #3 SL fire-rate at OOS** — **COUNTER-INTUITIVE prediction** (LM Master Rec #4): tighter SL → INCREASES SL fire-rate (NOT decreases). Predicted OOS SL fire-rate **75-90%** (vs baseline 62%). If observed < 60% → **UNDERFIRING** (basin avoided SL trigger → INERT). If > 90% → **OVERFIRING** ("3% lottery tickets" pattern). PASS band: 60-90%.
- **F-AXIS #4 n_eff_per_cell**: [6, 10] modal 8 (atr_sl change shifts class balance ~10-20%; marginal TPE convergence impact per LM Master Rec #4).
- **F-AXIS #5 exit-reason distribution OOS** — **LOAD-BEARING** (LM Master Rec #6): predicted OOS SL 75-90% / TP 0-8% / timeout 10-20% (baseline 62/12/26).
  - **CRITICAL CONSTRAINT**: If OOS TP-exit count = 0, ALL upside is lost (the 4 baseline TP exits contributed +31.64% PnL; if atr_sl=1.0 converts all of them to SL, mechanism net effect = pure loss-clipping with no upside retention) → **verdict CANNOT exceed PROMISING-INERT regardless of F1 OOS Sharpe magnitude**.
  - If OOS TP-exit count = 1, mechanism partially retains upside; verdict can reach PROMISING-INERT-FAV but not PROMISING.
  - If OOS TP-exit count ≥ 2, mechanism retains material upside; PROMISING reachable.

**Reconciliation discipline (CARRY-FORWARD from /022 §4)**: F-AXIS-MECHANISM passing on its own does NOT imply F1 success. /022 had 4/4 F-AXIS PASS with F1 catastrophic — mechanism ≠ outcome. **NEW (/028)**: F-AXIS #5 FAILURE (TP-exit count = 0) acts as an explicit verdict CEILING regardless of F1 — this is the LOAD-BEARING diagnostic LM Master Rec #6 codifies.

### F-PORTFOLIO (informational; cannot determine verdict)

Single-cohort LTC-only run; no portfolio metric meaningful. INFORMATIONAL.

---

## Section 5 — Predicted Verdict Distribution

Per `feedback_v1_per_cohort_saturation_asymmetric_rotation.md` ASYMMETRIC_ROTATION prior class baseline + mechanism-specific upgrades:

### 5.1 Priors (LM Master Rec #3 ADOPTED — supersedes QR initial 15/20/35/20/10)

| Verdict class | QR initial | LM Master | ADOPTED |
|---|---|---|---|
| PROMISING (F1 ≥ +0.40) | 15% | 12% | **12%** |
| PROMISING-INERT-favorable (+0.20 ≤ F1 < +0.40) | 20% | 18% | **18%** |
| INERT-no-effect (-0.20 ≤ F1 < +0.20) | 35% | 35% | **35%** |
| NEGATIVE-clean (-0.55 < F1 < -0.20) | 20% | 22% | **22%** |
| NEGATIVE-CATASTROPHIC (F1 ≤ -0.55) | 10% | 13% | **13%** |

NEG total **35%** vs QR's initial 30%. PROMISING tail compressed 35% → 30% per LM Master Rec #5 PARTIAL inoculation argument (basin-survival ratio caps lift below +0.40 in modal case).

### 5.2 Rationale

**Why PROMISING tail at 12%** (LM Master Rec #3):
- /022 EDA mechanism counterfactual: +12.45% OOS Δ on baseline roster (small lift)
- /028 EDA mechanism counterfactual: **+36.17% OOS Δ on baseline roster** (3× larger lift)
- Larger pre-mechanism signal supports a non-trivial PROMISING tail; basin-survival ratio 0.5-0.7 caps modal lift at +18-25% PnL → OOS Sharpe Δ +0.25 to +0.45.
- PROMISING-tier (Δ≥+0.40) reachable only if survival ratio ≥0.7 AND F-AXIS #5 OOS TP-exit count ≥1.

**Why NEG-CAT tail at 13%** (LM Master Rec #3, raised from 10%):
- ASYMMETRIC_ROTATION prior class binds NEG-CAT ≥10% per saturation rule.
- atr_sl change adds a 2nd basin-relocation vector (label class balance shift in addition to Optuna best_params shift), elevating tail by +3pp.
- Possible NEG-CAT modes: (a) tighter SL clips winners that would have recovered (false-loss conversion of all 4 baseline TP exits), (b) basin relocation finds a worse roster than baseline + label distribution shift compounds.

**Why INERT modal at 35%** (unchanged):
- PARTIAL inoculation means the basin-relocation failure mode of /022 maps PARTIALLY to INERT here (the SL fires, trades clip, but basin moves elsewhere AND label distribution shifts). The expected outcome on a NEW basin where SL fires equally is INERT — clipping losses + smaller gains = wash.

### 5.3 LM Master priors — ADOPTED (per Rec #3)

LM Master Phase 4.5 priors 12/18/35/22/13 ADOPTED in §5.1 above. NEG total 35% (vs QR initial 30%); PROMISING tail compressed 35% → 30% per LM Master Rec #5 PARTIAL inoculation argument. Track-record context: LM Master tail upweighting was reliably directionally correct at 4/4 mechanism-level forecasts in cycle-3.

---

## Section 6 — Failure Modes

### 6.1 Single-cohort basin lottery with ensemble_size=10 variance budget

Single-cohort isolation IS basin lottery. v1 runner has no `--seeds` flag (LM Master Rec #1); variance mitigation maps to inner ensemble (`--ensemble-size 10`). If the basin lands adversely despite the 10-model inner ensemble averaging, /028 NEG-CAT outcome materializes.

**Mitigation**: inner-ensemble (10 LightGBM models, distinct seeds) averaged at predict time. Per-seed model-level variance internal to ensemble; comparison.csv reports the ensemble-averaged metrics. Phase 7.4 LM Master post-mortem inspects inner-ensemble prediction variance via `forensic.jsonl` decision log if available.

### 6.2 Tighter SL clips winners — PRIMARY verdict-determining variable (LM Master Rec #6 LOAD-BEARING)

A tighter SL converts some near-stop trades that would have recovered into realized losses (false-loss conversion). **This is the DOMINANT verdict-determining variable for /028**, not a bounded SL-tuning trade-off.

**Empirical bound** (from baseline 34-trade OOS roster):
- Baseline LTC OOS had **4 TP exits** contributing **+31.64% PnL**. At baseline `atr_sl=1.75`, TP fired 4× OOS.
- At `atr_sl=1.0`, the SL fires earlier (1.0×ATR) than the TP target (3.5×ATR). Any trade where the price path crosses -1.0×ATR before +3.5×ATR converts to a SL fire.
- **LM Master Rec #6 codifies**: if atr_sl=1.0 converts ≥2 of 4 baseline TP exits to SL fires at the retrained roster, mechanism net effect = (loss-tail clip from -5/-7% to -3%) - (TP→SL conversion cost ≈ +5% lost per converted trade × N converted) → **net effect collapses below +0.20 OOS Sharpe Δ regardless of how cleanly it clips the moderate-loss bucket**.
- **F-AXIS #5 ceiling**: If OOS TP-exit count = 0, ALL upside is lost; verdict cannot exceed PROMISING-INERT regardless of F1 magnitude (the mechanism degenerates to PROMISING-MECHANICAL loss-clipping-only).

**Quantitative scenarios** (baseline-roster descriptive; basin-survival adjusted at the retrained roster):
- 0 of 4 TP→SL: full +36% retained → if survival ratio ≥0.7 → PROMISING (+0.40+)
- 1 of 4 TP→SL: ~+31% retained → if survival ratio ≥0.7 → PROMISING-INERT-FAV (+0.30)
- 2 of 4 TP→SL: ~+27% retained → modal PROMISING-INERT-FAV / borderline PROMISING
- 3 of 4 TP→SL: ~+22% retained → PROMISING-INERT-FAV ceiling (loss-clipping dominates)
- 4 of 4 TP→SL: ~+18% retained → PROMISING-INERT verdict ceiling (PROMISING-MECHANICAL — non-compoundable)

### 6.3 R1 cooldown saturation (per Model D baseline)

Tighter SL means more SL fires; R1 cooldown (K=3 consecutive SL → 27-candle cooldown) fires more often. **Cooldown periods reduce trade count** — net effect could push trade count below F8 lower bound (20 OOS).

**Mitigation**: F8 floor of 20 OOS trades is the LIVE-WALL check. If observed < 20, classify as DEGENERATE_PREDICTOR (analogous to /006 universe outcome).

### 6.4 Stateless mechanism — no deadlock risk

The atr_sl change is a CONFIG modification at training time. No state propagation. No deadlock-impossibility proof needed (vs STATEFUL mechanisms like /054 v3 drawdown brake).

### 6.5 Basin lottery + label class balance shift — TWO basin-relocation vectors (LM Master Rec #2 ADOPTED)

The mechanism is PARTIAL basin inoculation, NOT full orthogonality. The trade ROSTER is basin-determined AND the labels LightGBM trains on shift:

**Vector 1 — Optuna best_params shift (basin vector)**: tighter SL changes the loss surface Optuna optimizes against. Best_params relocate. Expected basin Jaccard vs baseline 0.05-0.15 (similar /022's 0.093).

**Vector 2 — Label class balance shift (training distribution vector)**: atr_sl is upstream of `triple_barrier_labels`. Tightening the lower barrier by 43% (1.75→1.0):
- Increases the count of -1 labels (lower barrier hit more often)
- Decreases magnitude of -1 labels (each labeled loss is now smaller)
- The labeled positive/negative ratio shifts, and within negatives the magnitude distribution shifts
- LightGBM trains on a DIFFERENT label distribution → different decision boundaries → different basin emerges

**Dominant risk**: If both vectors land adversely (basin relocates AND label distribution shift relocates Optuna into a region where the new roster has fewer SL-eligible volatile-regime trades), the mechanism is wasted. The +36% counterfactual is ONLY descriptive on the BASELINE roster.

**Phase 7.4 verdict assignment** MUST compare BOTH vectors:
- (a) Optuna best_params shift report (basin diagnostic)
- (b) Label class balance vs baseline LTC training (count +1 / -1 / 0 — Critic Phase 7.5 priority item #2 per LM Master Phase 4.5 closing)

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
- [ ] `--ensemble-size 10` properly passed (LM Master Rec #1 ADOPTED — v1 runner has no `--seeds` flag; inner ensemble is the variance budget)
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

### 11.7 /029 verdict-conditional staging per LM Master Rec #7 (ADOPTED — supersedes §11.1 for /029 binding)

Per LM Master Phase 4.5 §7 matrix:

| /028 verdict | /029 axis | Rationale |
|---|---|---|
| **PROMISING (12%)** | **DOT-specialist** (DOT pre-classification + DOT-only specialist; pre-classify against ASYMMETRIC_ROTATION rule per LM Master /022 §5 carry-forward) | PROMISING outcome confirms per-cohort axis viable when EDA-driven + basin-relevant. DOT is the remaining unclassified cohort. C×E altcoin de-concentration deferred to /030+. |
| **PROMISING-INERT-FAV (18%)** | **DOT-specialist** (same as PROMISING) | Same routing per LM Master Rec #7 — partial mechanism survival is sufficient evidence to extend per-cohort axis to DOT. |
| **INERT (35% modal)** | **Sample-weighting** (López de Prado AFML Ch.4 inverse-concurrency weighting; UNUSED in v1 catalog — substrate change orthogonal to cycle-3 axes) | INERT outcome indicates per-cohort + ATR-axis saturation; pivot to substrate-level sample-weighting (a NEVER-TRIED axis in v1). |
| **NEG-clean (22%)** | **Sample-weighting** (same as INERT) | INERT + NEG-clean both route to sample-weighting per LM Master Rec #7. |
| **NEG-CAT (13%)** | **FUNDAMENTAL RE-QUESTION** — XGBoost head-to-head OR universe contraction (drop LTC entirely) | **3rd NEG-CAT in same prior class (/020 + /022 + /028) CLOSES per-cohort axis PERMANENTLY** per LM Master Rec #7. Substrate-change pivot mandatory. |

**Binding**: §11.7 SUPERSEDES §11.1 for /029 axis selection. §11.1 retained for cycle-4 thematic context.

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
| 3.4 — LM Master Phase 4.5 Responses | YES | YES (ADOPTED 7/7) | per Rec #1-7 ADOPTED with rationale |
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

**Phase 5.5 readiness**: ALL sections complete; §3.4 + §5.3 LM Master slots ADOPTED post-Phase-4.5 advisory. Brief ready for Phase 5.5 gate evaluation.

---

**END OF BRIEF**
