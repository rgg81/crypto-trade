# LightGBM Master Advisor — iter-v1/041 — Phase 4.5 (Pre-Design)

## Context Read
- Track: v1. Anchor: BASELINE_V1 (`v0.v1-baseline-corrected`, IS +0.2829 / OOS +0.6637). Baseline ATR multipliers actually 2.9/1.45 (Model A) and 3.5/1.75 (C/D/E); /041 proposed 1.5/0.75 = **~48% narrower (Model A) and ~57% narrower (C/D/E)** bandwidths.
- /041 axis: triple-barrier tighten TP=1.5×ATR / SL=0.75×ATR (ratio 2:1 PRESERVED). Same 21-candle timeout.
- LABELING family rotation: last touched at /015 (CYCLE-2 CONFIRMATION, NEGATIVE-MULTI-SEED, n_eff=3 collapse via σ_t×√21 magnitude ~7.82%). v1/036 trend-scanning was a sister-family axis. 4-5 iters since LABELING = ADEQUATE rotation; /041 is structurally distinct (FIXED-ATR magnitude, NOT σ_t×√timeout).
- **PRIOR LM MASTER WARNING (load-bearing)**: /015 Phase 7.4 §4 explicitly OPENED axis at "sub-√timeout magnitudes — 3-5% midway range may preserve n_eff ≥ 15." `1.5×ATR_14` on 8h candles for BTC/ETH at recent rv ≈ ~1.0-1.5% per candle puts label barriers at ~1.5-2.3% — **lower than /015's 7.82% but higher than /014's 1.70%, squarely inside the /015-hypothesized "n_eff preservation band"**. /041 is the FIRST iteration to test that hypothesis empirically.

## Recommended Hyperparameter Direction

### 1. Bump `min_data_in_leaf` floor 20 → 50 [HIGH — confirms /038 Rec 2 forward port]
- **What**: tighten the Optuna lower bound; upper bound unchanged.
- **Why**: tighter barriers → denser labels per training cell (more rows reach TP/SL before timeout). Per /015 mechanism note, label-distribution SHAPE drives n_eff. A denser label set at sub-√timeout magnitudes lets shallow trees split on label-noise; min_data_in_leaf=50 enforces structural regularization to prevent the Optuna-IS-basin-overfit failure mode that destroyed /037+/038 (`n_effective_trials=9` recurrence).
- **Expected**: n_eff ≥ 15 in ≥ 4/5 cohorts (mid-band hypothesis test); per-cell IS noise reduction +5-10%.
- **Risk**: if labels are dominated by timeout-fwd-return-sign (i.e. 1.5×ATR is still too wide at v1 vols), tighter min_data_in_leaf has no effect because the label degenerate-distribution problem is upstream.

### 2. HOLD `n_trials=18` + ENSEMBLE_SIZE=3 [HIGH]
- **What**: standard v1 EXPLORATION budget. DO NOT raise.
- **Why**: the basin is structurally NEW (denser labels, different gradient signal). Per /038 Rec doctrine on `feedback_v3_inert_features_at_higher_budget.md`, raising n_trials on a NEW basin amplifies noise capture in the 44-col stack. **Predict n_effective_trials ≥ 15** at /041 (breaks the /037+/038 9-trial recurrence) — denser labels provide a stronger per-trial gradient signal than the sparse-timeout-dominated baseline. If n_eff_trials ≥ 15 verifies at Phase 7.4, the /037+/038 recurrence was label-sparsity-driven, NOT structural-stack-driven — important diagnostic.

### 3. LEAVE `confidence_threshold` Optuna bounds UNCHANGED [MEDIUM — REVISE prior brief intuition]
- **What**: do NOT lower the confidence_threshold lower bound. Hold current Optuna search range.
- **Why**: the prompt's intuition that "more candidate entries means model can be more selective per-entry" is partially right but axis-isolation discipline forbids touching it. If Optuna independently discovers a lower threshold optimum at /041, that's a learned response to the new label set — exactly the kind of basin-migration evidence we want UNCONFOUNDED.

## Recommended Feature-Engineering Direction

### 1. NO feature changes [HIGH]
- **What**: hold `V1_FEATURE_COLUMNS_PRUNED` 44 cols bit-identical to /040 (post-`regime_momentum_signed_5d` swap if /040 PROMISED, else 44 with `basis_zscore_30` still present per /040 outcome).
- **Predicted importance rank SHIFT**:
  - **GAIN**: `mom_rsi_14`, `stat_log_return_5`, `range_spike_16` (shorter-horizon = more aligned with denser-label gradient). Predict rank lift 1-3 positions.
  - **LOSE**: `hurst_100`, `trend_aroon_osc_50`, `vol_atr_14` (longer-horizon — less informative when label horizon shortens). Predict rank drop 2-4 positions.
  - **TOP-3 SWAP probability**: 50-60% that at least one of {vol_atr_14, trend_aroon_osc_50, stat_autocorr_lag5} drops out of top-3 across cohorts; replaced by RSI or stat_log_return_5.
- **Why this matters**: if top-3 ranks STAY bit-identical to /037+/038+/040 (basis_zscore_30 displaced or not), the tighter labels did NOT reorganize the loss surface — label-axis is **producing no informational change to model** = NEG-CLEAN risk.

## F-AXIS Falsifier Predictions

| # | Falsifier | Predicted band | Confidence |
|---|---|---|---|
| F1 modal | OOS Sharpe Δ vs anchor | **[-0.30, +0.15]** | MEDIUM |
| F2 wiring | dispatch banner emits atr_tp=1.5/atr_sl=0.75 | **PASS at 100%** | HIGH |
| F3 trade-count | IS [770, 950] (per /015 dense-label EDA + /038 720 IS baseline + +15-30% labels) | **70% PASS** | MEDIUM |
| F4 OOS Sharpe Δ | per F1 modal | as above | MEDIUM |
| F5 wall-clock | **modal 55-65 min**; +10-15% vs /040 baseline ~50 min from denser-label Optuna fit time | MEDIUM |
| F6 n_eff_trials | ≥ 15 in ≥ 4/5 cohorts (BREAKS /037+/038 recurrence) | **load-bearing** — if fails, basin-locked diagnosis |
| F7 n_eff (label diversity per /015) | ≥ 15 in ≥ 4/5 cohorts at /041 label magnitude | **MEDIUM-HIGH** — central test of /015 §4 mid-band hypothesis |

## Saturation Risks to Flag

**Expectancy compression risk** — tighter barriers + ratio preserved means per-trade expectancy shrinks proportionally (~50%). The hypothesis is that **trade COUNT scales up by enough to compensate for per-trade IR drop**. v1 mean-reversion at 8h is not market-microstructure-fast; expect ~1.4× trade count, ~0.5× per-trade-pnl — net IS PnL approximately FLAT to slightly NEGATIVE. **OOS Sharpe is the load-bearing metric**, not net PnL.

**Noise-vs-signal tradeoff** — shorter forward window = more chop = lower per-trade IR. If Optuna CANNOT navigate the denser-but-noisier basin at n_trials=18, IS Sharpe collapses (the /037 + /038 + /015 failure-mode pattern). The min_data_in_leaf floor 20→50 is the load-bearing mitigation.

**/015 PARTIAL-CLOSED axis re-entry risk** — /015 closed labeling at CALIBRATED magnitude with a documented "sub-√timeout magnitudes 3-5% range may preserve n_eff ≥ 15" carve-out (Phase 7.4 §4). /041 falls inside that carve-out **but at 1.5-2.3% which is BELOW the /015-hypothesized 3-5% band**. There is non-zero probability /041 sits BELOW the n_eff sweet spot and lands at n_eff ~5-10 (worse than /014's 19, better than /015's 3). If Phase 7.4 measures n_eff ≤ 10, labeling axis is **fully closed across the full barrier-magnitude curve** — important structural finding.

**3-iter Optuna-ridge recurrence latent risk** — /037 + /038 hit `n_effective_trials=9`. If /041 also lands ≤ 10 despite denser labels, the ridge pattern is feature-stack-structural (44 cols × 2.9/1.45 ATR labels), NOT label-magnitude-driven. Critical diagnostic.

## Saturation Check

LABELING family last fully exercised at /015 (cycle 2). /036 trend-scanning was sister-family. **4-5 iter gap = ADEQUATE rotation** per `feedback_v3_iter017_metalabeling_mandate.md` doctrine. Tighten-TB at FIXED-ATR (NOT σ_t×√timeout) is structurally orthogonal to /015's mechanism. Axis is OPEN and well-posed.

## What I Did NOT Recommend

- Did NOT recommend `num_leaves` upper-bound change (saturated at 127 per /040).
- Did NOT recommend lowering `confidence_threshold` floor (axis isolation; let Optuna discover).
- Did NOT recommend changing `learning_rate` bounds (axis isolation).
- Did NOT recommend pre-EDA of n_eff vs barrier-magnitude curve (would require runner instrumentation beyond axis scope; defer to Phase 7.4 measurement).
- Did NOT recommend re-introducing dropped features (`basis_zscore_30`) — INERT recurrence verdict from /034-/038 stands.

## Closing Note — REPORT BACK (under 250 words)

**Track record**: prior LM Master at /038 → /040 Phase 4.5 modal predictions were directionally correct on basin-instability mechanism but verdict-class magnitude calls remain at 0/N for v1 verdict-class. /041 advisory continues FLAT verdict-class prior + MEDIUM mechanism-level confidence.

**3 strongest recommendations**:
1. **min_data_in_leaf floor 20 → 50** (HIGH — denser-label overfit mitigation; load-bearing for verdict-class outcome)
2. **HOLD n_trials=18 + ENSEMBLE_SIZE=3** (HIGH — axis isolation; test the "denser labels break /037+/038 ridge" hypothesis cleanly)
3. **Measure n_eff at Phase 7.4 as PRIMARY DIAGNOSTIC** (HIGH — /015's documented n_eff curve makes /041's n_eff_label_distribution the cycle-2-vs-cycle-5 connecting tissue; should be in engineering report)

**Prior probability distribution**:

| Outcome | Probability | Rationale |
|---|---|---|
| **PROMISING-CLEAN** | **15%** | /015 §4 mid-band hypothesis must hold AND 1.5-ATR is sweet-spot AND OOS regime cooperates |
| **PROMISING-INERT-FAV** | **20%** | denser labels reorganize loss surface but RSI/return-shifted ranks net-neutral on OOS |
| **INERT / NULL** | **30%** | MODAL — denser labels yield same basin as baseline (rank-1 features dominate regardless) |
| **NEG-CLEAN** | **25%** | per-trade expectancy compression + Optuna basin-instability dominates trade-count lift |
| **NEG-CATASTROPHIC** | **10%** | n_eff collapses to ≤ 5 like /015 if 1.5-ATR sits BELOW the /015 hypothesized 3-5% band |

**PROMISING-tail combined = 35%** — lower than /040's 65% because /015's CYCLE-2 CONFIRMATION-NEGATIVE-multi-seed is the most decisive same-axis prior available, and the carve-out band hypothesis is unproven (it's a /015 LM Master forward-looking suggestion, not verified).

**1-sentence forecast for /044 substrate**: /041 is **30-35% likely** to add to /044 CONFIRMATION substrate — modal outcome is INERT/NULL with axis closure at the FIXED-ATR magnitude curve, but if n_eff ≥ 15 verifies AND OOS Sharpe Δ clears +0.10, /041 becomes the **first** v1 cycle-5 labeling ingredient and the /044 multi-seed CONFIRMATION must bundle it alongside any /042-/043 PROMISING outcomes.

Relevant files:
- /home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-038/lgbm_advisor.md (§6 Rec 2 source rationale)
- /home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-015/lgbm_advisor.md (Phase 7.4 §4 n_eff curve hypothesis and carve-out band)
- /home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-040/lgbm_advisor.md (most recent v1 Phase 4.5 prior + 3-iter Optuna ridge flag)
- /home/roberto/crypto-trade/.worktrees/quant-research/BASELINE_V1.md (anchor metrics + actual ATR multipliers 2.9/1.45 + 3.5/1.75)
- /home/roberto/crypto-trade/.worktrees/quant-research/run_baseline_v1.py:2412-2452 (per-model ATR multiplier config — relevant for /041 plumbing dispatch)
