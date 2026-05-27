# iter-v1/024 — Research Brief (Phases 2-5)

**Branch**: `iteration-v1/024` from `iteration-v1/023` HEAD `bbe5c3b` (tag `v0.v1-023`).

**Anchor**: `v0.v1-baseline-corrected` (`BASELINE_V1.md` commit `f8bc12c`). Portfolio IS Sharpe **+0.2829** / OOS Sharpe **+0.6637** / OOS trades 189 / 5-sym universe / 4 models (A, C, D, E). Portfolio comparison.csv "sharpe" semantics = monthly daily-annualized.

**Track**: v1 (refactored 2026-05-23). 13 phases. LightGBM Master + Critic.

**Iteration type**: EXPLORATION (cycle-3 #9 of 10).

---

## Section 0 — Position in cycle / pivot context

### 0.1 Cycle-3 cadence position

- Cycle-3 EXPLORATION #9 of 10 (CONFIRMATION earliest at /027; one more EXPLORATION /025 to follow).
- Prior cycle-3 ledger: /016 sample-weighting NEG-CAT; /017 universe NEG-INERT; /018 LINK-only PROMISING-INERT-FAVORABLE; /019 ETH+gate PROMISING; /020 BTC-only NEG-CAT; /021 methodology-pivot PROMISING-METHODOLOGY non-compoundable; /022 LTC-only NEG-CAT; /023 funding-rate feature LEARNED-NEGATIVE clean.
- Cycle-3 totals so far: 2 PROMISING + 1 PROMISING-METHODOLOGY + 1 PROMISING-INERT-FAVORABLE + 1 LEARNED-NEGATIVE + 2 NEGATIVE clean + 2 NEGATIVE-CATASTROPHIC + 0 merges.

### 0.2 Convergent axis-rotation routing — REGIME-CONDITIONAL SUB-MODELS

Three-way convergence routes /024 to **regime-conditional sub-models** (model-arch family):

1. **USER STRATEGIC DIRECTIVE** (Phase 8 prompt verbatim): "be bold. diversification is the key. multiple smaller models each model performing well under different regimes". /024 is the FIRST iteration that directly operationalizes this thesis.
2. **LM Master /023 Phase 7.4 §4 PRIMARY recommendation (Option B)**: regime-conditional sub-models harvest the +78.55% IS PnL ORACLE band that LightGBM-at-pool averaged over.
3. **Critic /023 Phase 7.5 Path Forward #2**: "Train 2 sub-models per cohort (|funding_z30|>1.5 vs ≤1.5); STATELESS regime gate. DUAL GATE evidence supports 3/4 cohorts. HIGH-RISK MANDATORY."

### 0.3 Anchor-frame BINDING (LOCKED from /022 closeout — UNCHANGED)

Per /022 Critic Rec #3 ELEVATED to BINDING + /023 LOAD-BEARING re-confirmation:
- F1 frame = `reports-v1/iteration_v1-baseline/comparison.csv` "sharpe" row, OOS column = daily-annualized monthly Sharpe via `_compute_daily_sharpe()`.
- F1 OOS Sharpe Δ anchor = **+0.6637** (portfolio daily-annualized monthly).
- F3 IS Sharpe Δ anchor = **+0.2829** (portfolio daily-annualized monthly).
- OOS total trades anchor = 189; IS total trades anchor = 621.

### 0.4 Verdict subtype context — LEARNED-NEGATIVE feeds /024 hypothesis

/023 LEARNED-NEGATIVE diary sub-classifier is the LOAD-BEARING input to /024:
- v1 LEARNED funding (portfolio 5.40% > 4.76% uniform parity; Pool A 6.88% top of 4 cohorts).
- But OOS Sharpe Δ NEGATIVE because the model averaged over regimes (Section 1 mechanism).
- ORACLE +78.55% concentration in z30 ∈ [-2, -1] band was the **tail-load-bearing** signal LightGBM-at-pool could not isolate at single-seed n_trials=18.
- /024 hypothesis: partition the training data BEFORE Optuna's loss surface integrates over regimes → 2 sub-models can specialize → harvest the tail edge that /023 left on the table.

### 0.5 Cadence ledger summary

Cycle-3 EXPLORATION position: **#9 of 10**. Remaining slots: /024 + /025 + (optional /026 sanity) before /027 CONFIRMATION earliest.

### 0.6 Architecture-Family Justification (v1-only)

- **Axis family**: `model-arch` (**NEW 16th family** — FIRST model-architecture axis in cycle-3 and FIRST multi-model architecture EVER in v1 history; cycle-1 /003 per-symbol Model A split was the only prior `model-arch` usage and was NEGATIVE).
- **Prior 5 EXPLORATION families** (going INTO /024):
  - /019: per-cohort-specialization-ETH
  - /020: per-cohort-specialization-BTC
  - /021: methodology-pivot
  - /022: per-cohort-specialization-LTC
  - /023: feature-family (funding-rate)
- **Rotation status**: **VALID** — `model-arch` is in NONE of the prior 5. Rotation rule honored unambiguously. Last `model-arch` was /003 in cycle-1 (NEGATIVE outcome). After /003, twenty iterations without a `model-arch` axis.
- **One-sentence rationale**: USER STRATEGIC DIRECTIVE "multiple smaller models per regime" + LM Master /023 PRIMARY + Critic /023 Path Forward #2 = three-way CONVERGENT routing on a NEW family that directly tests whether regime-conditional architecture can harvest /023's LEARNED-NEGATIVE tail.

### 0.7 Wall-clock estimate

Each sub-model is trained on partition of the cohort's training rows:
- Pool A extreme partition: ~14% × ~5727 × 2 syms = ~1573 IS bars
- Pool A normal partition: ~86% × ~5727 × 2 syms = ~9582 IS bars
- LINK/LTC/DOT extreme partition: ~709-802 / ~5025-5687 bars

Per-cohort dispatch = 2 × ENSEMBLE_SIZE=3 sub-models. Walk-forward window = same 24m as baseline. Trade-stream merge is post-hoc (negligible compute).

- Pool A: 2× of baseline Model A (Pool A is the slowest cohort, ~2.5h at full ENSEMBLE / 50 trials) ≈ 30 min at ENSEMBLE=3 + n_trials=18 + 2 sub-models = ~30-40 min.
- LINK + LTC + DOT: each ~10-15 min at 2× sub-models = ~30-45 min total.
- **Estimate: 60-80 min** (target above 60-min ideal but acceptable for first multi-model-arch iteration).
- HARD CAP **2h** (cycle-3 EXPLORATION discipline `4cb8972`).

---

## Section 1 — Hypothesis

**H_AXIS**: Training 2 LightGBM sub-models per cohort partitioned by funding-regime extremity (`|funding_rate_zscore_30| > 1.5` vs `≤ 1.5`) and routing each bar's signal to the regime-matched sub-model at inference **harvests the IS-anchored tail edge that pool training averages over**, producing positive F1 OOS Sharpe Δ ≥ +0.10 vs anchor +0.6637.

**Mechanism story** (load-bearing for /024):

1. **/023 confirmed signal exists in the data**: v1 LEARNED funding (portfolio gain share 5.40% > uniform parity 4.76%; Pool A top 6.88%). The signal IS in the loss surface — Phase 4.5 DUAL GATE measured it.
2. **/023 confirmed signal does not translate at pool**: at single-seed n_trials=18, LightGBM trees at depth 3-5 cannot easily decompose the joint surface `funding-z30 × momentum × volatility × direction` AND simultaneously optimize CV loss across ~3500 IS trades — best-trial parameters target the MEAN funding effect (which is near zero).
3. **Regime partition flattens the joint surface**: each sub-model sees only one regime's training rows. The extreme sub-model's CV loss is dominated by extreme-regime label distribution; the normal sub-model's by normal. Optuna lands in 2 DIFFERENT BASINS, each optimal for its regime — the basin-level pool effect /021 H1 surfaced as load-bearing.
4. **STATELESS regime gate enforces routing at inference**: at bar t, compute `funding_rate_zscore_30(t)` from past-only data, route to extreme- or normal-regime sub-model. No state. No deadlock. Same `.shift(1)` past-only discipline as /023.
5. **The +78.55% ORACLE band is harvestable in principle**: from `regime_oracle_attribution.csv`, Pool A ORACLE Δ = **+54.2pp** vs baseline IS PnL; LINK +30.6pp; LTC +42.0pp; DOT +16.4pp. The total IS PnL ceiling under perfect regime-direction conditioning is **+142.5pp gains** across 4 cohorts vs baseline +50.98% portfolio IS — a 2.8× theoretical lift.

**Specific quantitative prediction**: per /022 + /023 basin-relocation precedent, ORACLE-attributable lift dissolves by ~60-80% under retraining (Jaccard 0.10/0.09 → ~90% new roster). Realistic IS lift estimate: 0.6 × 142pp × 0.20 = ~17pp (after dissolution). Translated to F1 OOS Sharpe Δ via baseline Sharpe-to-PnL slope: ~+0.05 to +0.25 OOS Sharpe Δ.

**Direction of expected lift**: POSITIVE if the regime gate routes correctly AND extreme-regime sub-model develops the short-bias the EDA reveals. NEGATIVE-INERT if extreme regime sample sizes are too thin for stable sub-model training (DOT 8 trades borderline). NEGATIVE-CATASTROPHIC if extreme sub-model overfit on 1573 Pool A bars and the regime-gate routes the OOS into the overfit zone.

**ORACLE EDA caveat (per `feedback_v3_oracle_eda_validity.md`)**: the +54.2pp / +42pp / +30.6pp / +16.4pp ORACLE deltas are descriptively valid because the regime gate is STATELESS. They do NOT predict /024 trade-roster outcome — basin relocation at retraining will dissolve the specific Pool A baseline trades. The mechanism (extreme-regime short-bias from sign-flip) is causal and roster-agnostic; the specific PnL share will not reproduce.

---

## Section 2 — IS-only Evidence (numerical tables from committed analysis)

EDA scripts at `analysis/iteration_v1-024/regime_eda.py` (commit pending in this brief commit). All computations use IS-only data (`open_time < OOS_CUTOFF_MS = 1742774400000`).

### 2.1 Regime sample size per cohort

From `analysis/iteration_v1-024/regime_sample_size.csv`:

| Cohort | Symbols | IS bars | Extreme bars | Normal bars | Extreme % | IS trades | Trades in extreme | Trades in normal | Trades extreme % |
|---|---|---|---|---|---|---|---|---|---|
| Pool A | BTCUSDT+ETHUSDT | 11155 | 1573 | 9582 | **14.10%** | 252 | **40** | 212 | 15.87% |
| Model C | LINKUSDT | 5562 | 709 | 4853 | 12.75% | 146 | **17** | 129 | 11.64% |
| Model D | LTCUSDT | 5657 | 802 | 4855 | 14.18% | 124 | **17** | 107 | 13.71% |
| Model E | DOTUSDT | 4975 | 726 | 4249 | 14.59% | 93 | **8** | 85 | 8.60% |

**Key observations**:
- Extreme regime fires 12.75-14.59% of IS bars across cohorts — clean ~14% as user predicted.
- Trade extreme % (8.6-15.87%) closely matches bar extreme % (12.75-14.59%) for 3 of 4 cohorts (DOT 8.6% < 14.59% bar rate — DOT model already under-emits trades in extreme regime).
- **DOT extreme trade count = 8 — THIN sample; Pool A 40 (most stable), LINK 17, LTC 17**.
- Extreme sub-model training rows: 709-1573 bars per cohort — above LightGBM's stability floor (`min_child_samples` bounds [3, 30] in v1_pruned profile; n_eff_per_cell EDA shows 5-10 across 4 cohorts at baseline, this halves under extreme partition).

### 2.2 Direction sign-flip in EXTREME regime (load-bearing mechanism support)

From `analysis/iteration_v1-024/regime_direction_attribution.csv`:

| Cohort | Regime | Direction | N trades | Win rate | Mean PnL % | Sum PnL % |
|---|---|---|---|---|---|---|
| **Pool A** | EXTREME | longs | 18 | 27.8% | **-0.0313** | -0.56% |
| **Pool A** | EXTREME | **shorts** | 22 | **50.0%** | **+0.389%** | **+8.56%** |
| **Pool A** | NORMAL | longs | 101 | 40.6% | +0.114% | +11.46% |
| **Pool A** | NORMAL | shorts | 111 | 31.5% | -0.588% | -65.30% |
| **Model C** (LINK) | EXTREME | longs | 10 | **10.0%** | **-4.70%** | **-47.03%** |
| **Model C** (LINK) | EXTREME | **shorts** | 7 | **85.7%** | **+7.42%** | **+51.94%** |
| **Model C** (LINK) | NORMAL | longs | 72 | 52.8% | +1.94% | +139.77% |
| **Model C** (LINK) | NORMAL | shorts | 57 | 36.8% | -1.27% | -72.62% |
| **Model D** (LTC) | EXTREME | longs | 10 | 20.0% | **-2.67%** | -26.66% |
| **Model D** (LTC) | EXTREME | **shorts** | 7 | **57.1%** | **+2.59%** | **+18.10%** |
| **Model D** (LTC) | NORMAL | longs | 64 | 39.1% | +0.25% | +15.84% |
| **Model D** (LTC) | NORMAL | shorts | 43 | 41.9% | -0.09% | -4.01% |
| Model E (DOT) | EXTREME | longs | 5 | 60.0% | +0.64% | +3.20% |
| Model E (DOT) | EXTREME | shorts | 3 | 33.3% | -1.70% | -5.09% |
| Model E (DOT) | NORMAL | longs | 51 | 41.2% | +0.43% | +22.19% |
| Model E (DOT) | NORMAL | shorts | 34 | 41.2% | +0.19% | +6.33% |

**Critical findings**:
- **Direction sign-flip CONFIRMED in 3 of 4 cohorts** (Pool A, LINK, LTC). EXTREME regime: longs negative-PnL, shorts positive-PnL. Symmetric in normal regime: longs positive, shorts negative.
- **LINK extreme regime is the cleanest signal**: longs −4.70% mean / shorts +7.42% mean (12.1pp sign-flip per trade); shorts 85.7% WR / longs 10.0% WR.
- **Pool A extreme regime confirms /023 mechanism**: in EXTREME regime, shorts +8.56pp / longs −0.56pp (modest but directionally consistent). In NORMAL regime, longs +11.46pp / shorts −65.30pp.
- **DOT is the OUTLIER**: extreme-regime longs +3.20% / shorts −5.09% (reversed). DOT is the one cohort where extreme-funding is not a short signal. Combined with the 8-trade sample (~ thin), DOT sub-model is at HIGH risk of overfitting to a small reverse-signal subset.
- **NORMAL regime shows the symmetric pattern**: longs profitable (+22pp/LINK +140pp/Pool A +11pp); shorts catastrophic (NORMAL ETH+BTC shorts -65pp). Tightening the longs in NORMAL and shorts in EXTREME is the LightGBM-learnable specialization.

### 2.3 Regime persistence (regime-like vs noise-like)

From `analysis/iteration_v1-024/regime_persistence.csv`:

| Symbol | n_extreme_runs | Mean extreme run | Median | P90 | Max | Normal run mean | Flip rate/bar | Classification |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 483 | 1.677 | 1.0 | 3.0 | 8 | 9.97 | **0.1715** | MIXED |
| ETHUSDT | 488 | 1.564 | 1.0 | 3.0 | 7 | 9.73 | **0.1768** | MIXED |
| LINKUSDT | 415 | 1.708 | 1.0 | 3.0 | 10 | 11.67 | **0.1493** | MIXED |
| LTCUSDT | 465 | 1.725 | 1.0 | 4.0 | 9 | 10.42 | **0.1644** | MIXED |
| DOTUSDT | 418 | 1.737 | 1.0 | 3.0 | 12 | 10.14 | **0.1681** | MIXED |

**Key observations**:
- **Flip rate per bar = 0.15-0.18** across all 5 symbols → classified MIXED (between pure REGIME at < 0.10 and pure NOISE at > 0.20). The regime is **not strongly persistent** — median extreme run = 1 bar (single-bar flickers).
- **P90 extreme run = 3 bars; max 7-12 bars**. Extreme periods of 24-96 hours are rare but exist (max DOT 12 bars = 4 days extreme).
- **Implication for /024**: the regime gate will fire frequently (~14% of bars) but each fire-window is short (median 1 bar). The extreme-regime sub-model must produce stable signals on **scattered** training rows rather than dense regime-blocks. This is more challenging than persistent-regime conditioning.
- **Sub-model basin stability**: 1573 Pool A bars / 709 LINK bars / 802 LTC bars / 726 DOT bars are the TRAINING ROWS for the extreme sub-model. Each cohort's extreme partition is "1573 scattered single bars" not "1573 contiguous bars" — labeling integrity from `label_trades` past-only triple-barrier should still hold (each bar's label uses past-only sigma).

### 2.4 Cross-cohort extreme-regime overlap

From `analysis/iteration_v1-024/regime_cross_cohort_overlap.csv`:

| Pair | Both extreme % | A extreme % | B extreme % | P(B \| A) | P(A \| B) | Pearson corr |
|---|---|---|---|---|---|---|
| BTC+ETH | 5.39% | 15.16% | 14.35% | 35.5% | 37.5% | **0.2554** |
| BTC+LINK | 4.30% | 15.16% | 13.03% | 28.4% | 33.0% | 0.1927 |
| BTC+LTC | 5.36% | 15.16% | 14.54% | 35.4% | 36.9% | 0.2501 |
| BTC+DOT | 4.19% | 15.16% | 14.79% | 27.7% | 28.4% | 0.1533 |
| ETH+LINK | 4.56% | 14.35% | 13.03% | 31.8% | 35.0% | 0.2277 |
| ETH+LTC | 5.53% | 14.35% | 14.54% | 38.6% | 38.1% | 0.2791 |
| ETH+DOT | 4.36% | 14.35% | 14.79% | 30.4% | 29.5% | 0.1801 |
| LINK+LTC | 5.49% | 13.03% | 14.54% | **42.2%** | 37.8% | **0.3032** |
| LINK+DOT | 5.51% | 13.03% | 14.79% | **42.3%** | 37.3% | **0.3001** |
| LTC+DOT | 5.26% | 14.54% | 14.79% | 36.2% | 35.5% | 0.2483 |

**Key observations**:
- **Conditional P(B extreme | A extreme) = 28-42%** across all pairs. The 5 symbols partially share extreme-funding regimes but are NOT fully synchronized. When BTC is extreme, ETH is ALSO extreme 35.5% of the time (vs 14.35% unconditional → 2.5× lift).
- **Highest cross-cohort overlap is LINK+LTC and LINK+DOT at 42%** — but Pool A's BTC+ETH overlap is only 35.5%. Pool A trains its extreme sub-model on rows where EITHER BTC or ETH is extreme; 5.39% of bars have both extreme.
- **5.4% baseline overlap rate** means there is room for sub-model specialization at the cross-asset level. The signal source is partially asset-idiosyncratic.
- **Implication**: regime gates fire COHORT-INDEPENDENT (each cohort's gate uses its own symbols' z30); cross-cohort synchronization is INFORMATIONAL only, NOT a routing decision.

### 2.5 ORACLE attribution (theoretical IS PnL ceiling)

From `analysis/iteration_v1-024/regime_oracle_attribution.csv`:

| Cohort | N extreme | N normal | Baseline extreme PnL | Baseline normal PnL | Baseline total | ORACLE extreme | ORACLE normal | ORACLE total | ORACLE Δ vs baseline |
|---|---|---|---|---|---|---|---|---|---|
| Pool A | 40 | 212 | −22.34% | −3.54% | −25.87% | 0.00% | +28.37% | +28.37% | **+54.24pp** |
| Model C (LINK) | 17 | 129 | +23.04% | +73.36% | +96.40% | +39.77% | +87.20% | +126.97% | **+30.57pp** |
| Model D (LTC) | 17 | 107 | −4.21% | +9.05% | +4.84% | +14.77% | +32.07% | +46.84% | **+42.00pp** |
| Model E (DOT) | 8 | 85 | +0.15% | −16.34% | −16.19% | +0.22% | +0.00% | +0.22% | **+16.41pp** |

**Key observations**:
- ORACLE total Δ across 4 cohorts = **+143.22pp** vs baseline cumulative IS portfolio.
- The Pool A ORACLE +54.24pp is the LARGEST single-cohort theoretical ceiling. Pool A's baseline IS PnL was NEGATIVE (-25.87%); under perfect regime-direction conditioning it becomes +28.37% — flipping the loss to gain.
- LINK's ORACLE +30.57pp is the most ACHIEVABLE since LINK already has +96.40% baseline (room to extend, not flip).
- DOT's ORACLE +16.41pp comes ENTIRELY from EXTREME-regime trimming (DOT EXTREME longs +0.22% vs shorts −5.09%; the ORACLE keeps only longs in EXTREME, drops shorts).
- **Dissolution factor**: per /022 + /023 basin-relocation, expect 60-80% of ORACLE to dissolve under retraining. Realistic IS Δ estimate: **~17-29pp** (143pp × 0.12-0.20).
- **PER-COHORT translation**: Pool A retains the largest theoretical lift; DOT borderline because (a) baseline IS PnL already negative, (b) extreme sample only 8 trades.

### 2.6 ORACLE EDA caveat (per `feedback_v3_oracle_eda_validity.md`)

Regime gate is STATELESS (no signal-emission state propagation; z30 at bar t is past-only by `.shift(1)`). ORACLE EDA is descriptively valid; specifically:

- **Causal claim VALID**: extreme regime is a different signal-generating distribution from normal regime. Per-regime sub-model trained on its partition learns the per-regime label distribution. Regime gate at inference routes correctly.
- **Trade-roster prediction INVALID**: the specific +143pp ORACLE Δ assumes baseline roster + perfect regime-direction split. The retrained ensemble produces a NEW roster (~80-90% non-overlap), so the +143pp specific PnL share will not reproduce.
- **Realistic outcome envelope**: F1 OOS Sharpe Δ ∈ [-0.10, +0.30] with mode ~+0.05 — accounting for (a) basin-relocation dissolution of ORACLE, (b) sub-model basin variance at single-seed, (c) /023 prior of LEARNED-NEGATIVE → some persistence of pool architecture limitations.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only — MANDATORY per Critic /023)

**Declaration**: **HIGH-RISK** (Critic /023 Path Forward #2 "HIGH-RISK MANDATORY").

**Reason**: model-arch axis is FIRST multi-model architecture in v1; introduces 2× sub-models per cohort (8 sub-models vs baseline 4); thin extreme-regime sample (Pool A 1573 / LINK 709 / LTC 802 / DOT 726 bars) raises Optuna's effective sample size below baseline; per-cohort Pool A is the LEAST DATA-DENSE cohort going forward (1573 bars vs baseline 11155 bars for extreme sub-model = -86% effective training data); /023 LEARNED-NEGATIVE precedent suggests basin-level edge is fragile at single-seed.

**Mitigation (HIGH-RISK opt-in per v1 rules)**: NO multi-seed validation opt-in for /024 EXPLORATION (single-seed=42 EXPLORATION default for axis isolation; v1 EXPLORATION budget standard).

**RATIONALE for skipping multi-seed mitigation**:
- /024 is #9 of 10 cycle-3 EXPLORATIONs; multi-seed would consume ~3-4h CONFIRMATION-spec budget, well above 2h EXPLORATION HARD CAP.
- Per v1 rule: "if 3+ HIGH-RISK single-seed EXPLORATIONs produce >1σ negative deltas, the next HIGH-RISK iteration becomes mandatorily multi-seed". Cycle-3 HIGH-RISK NEG-CAT lineage: /014 (HIGH-RISK NEG), /015 (HIGH-RISK NEG-CAT CONFIRMATION), /020 (HIGH-RISK NEG-CAT). 3 NEG already; /022 (HIGH-RISK NEG-CAT) is the 4th. **However the rule reads >1σ NEGATIVE — /023 was NEG-clean at 3bp inside threshold (NOT >1σ). The rule fires when /020 NEG-CAT (Δ -0.86, ~2.5σ) + /022 NEG-CAT (Δ -1.17, ~3.5σ) + ONE more >1σ NEG.** Critic /023 expressed concern but did NOT formally trigger the rule because /023 was NEG-clean at threshold. /024 is the THIRD HIGH-RISK single-seed iteration after the 2 NEG-CAT precedents — at the threshold of the rule.
- /024 architecture is genuinely DIFFERENT from prior NEG-CAT axes (model-arch vs per-cohort isolation/feature-family). The dissolution mechanism is also different (regime partition vs cohort isolation). Single-seed is justified for the FIRST exploration of this architectural mechanism; if /024 is NEG-CAT or any >1σ negative, /025 becomes mandatorily multi-seed regardless of family.

**Pre-commit (binding)**:
- If /024 verdict ∈ {PROMISING, PROMISING-INERT-FAVORABLE} → /025 explores funding-FAMILY × regime-gate variants OR adds a 3rd regime layer (e.g. tri-partition `[|z|<0.5, 0.5<|z|<1.5, |z|>1.5]`).
- If /024 verdict = INERT → axis CLOSED for cycle-3; /025 pivots to per-cohort drawdown brake (Path Forward #1 from /023) — STATEFUL → MANDATORY deadlock-impossibility proof.
- If /024 verdict ∈ {NEGATIVE clean, NEGATIVE-CATASTROPHIC} → /025 mandatory multi-seed (3+ HIGH-RISK trip rule); axis remains live OR pivots to per-cohort drawdown brake at multi-seed depending on Critic post-mortem.

---

## Section 3 — Proposed Changes

### 3.1 NEW source module: `src/crypto_trade/strategies/regime_gate_v1.py`

Implements:
- `RegimeGateConfig(threshold=1.5, z30_column="funding_rate_zscore_30", enabled=True)` — frozen dataclass; mirror of `BtcTrendFilterConfig` structural pattern.
- `route_trades_by_regime(trades_extreme, trades_normal, master_df, config)` — post-hoc trade-stream router. Given two trade lists (from extreme sub-model + normal sub-model) and a master kline DF (for z30 lookup at each trade's open_time), returns the routed trade list: for each trade, look up z30 at its open_time, choose the trade from the matched sub-model's roster. STATELESS (numpy boolean mask; no persistent state).
- `evaluate_regime_at_signal(z30_value, config)` — single-signal helper returning regime label (live-engine parity).
- `RegimeGateStats` — diagnostic dataclass: n_extreme_fired, n_normal_fired, n_routed, fire-rate.

**Track isolation**: ZERO imports from `crypto_trade.features_v2` or `crypto_trade.features_v3`. Module lives under `strategies/` (not `features_v1/`).

### 3.2 Runner dispatch: `run_baseline_v1.py:V1_ITER024`

NEW dispatch branch after the `iter-v1/023` branch:
- `V1_ITER024_UNIVERSE = V1_BASELINE_UNIVERSE` (same 5 syms as /023; full baseline universe).
- `V1_ITER024_REGIME_THRESHOLD = 1.5` (matches Phase 1 EDA).
- `iteration_label == "v1-024"` triggers regime-conditional dispatch.

Per cohort (Pool A, C, D, E): run `run_model()` TWICE with `data_filter_callback` parameter (NEW kwarg) selecting either `|z30| > 1.5` (extreme sub-model) or `|z30| ≤ 1.5` (normal sub-model). The kwarg routes through to `LightGbmStrategy._train_for_month()` which filters `train_indices` to the regime-matched subset BEFORE labeling.

Then for each cohort's 2 trade-lists, call `route_trades_by_regime(...)` to produce the cohort's final trade list. Merge across 4 cohorts as usual.

**Implementation choice rationale**: post-hoc routing requires running 2 backtests per cohort, which is wasteful (each backtest produces a full trade roster but only the regime-matched subset is used). The cleaner alternative is **train-time partition**: pass `data_filter_callback` to `LightGbmStrategy` that filters `train_indices` BEFORE labeling. The strategy then produces ONE trade roster per sub-model that only emits trades for its regime, because at inference, when `get_signal()` checks z30 at the current bar and the sub-model is trained only on its regime, predictions on out-of-regime bars will be unreliable. To enforce CLEAN regime gating, we wrap each sub-model with the regime gate at signal-time.

**Final implementation**: 2 sub-models per cohort. Each sub-model is a `LightGbmStrategy(data_filter=lambda month_df: regime_filter(month_df, target_regime), ...)`. At inference, a thin `RegimeRoutedStrategy(extreme_strategy, normal_strategy, regime_config)` wrapper computes z30 at signal time and dispatches to the matching sub-strategy.

### 3.3 LightGbmStrategy `data_filter_callback` extension

**Modify** `src/crypto_trade/strategies/ml/lgbm.py` `LightGbmStrategy.__init__` to accept `data_filter_callback: Callable[[np.ndarray], np.ndarray] | None = None` — applies to `train_indices` inside `_train_for_month()` BEFORE labeling. Backward-compatible (default `None` = no filter; bit-identical to baseline).

```python
# In _train_for_month(), after line ~507:
train_indices = np.where(
    (self._open_time_arr >= split.train_start_ms)
    & (self._open_time_arr < split.train_end_ms)
)[0]
if self.data_filter_callback is not None:
    mask = self.data_filter_callback(self._master.iloc[train_indices])
    train_indices = train_indices[mask]
if len(train_indices) < 10:
    return
```

The callback is also applied at inference time inside `get_signal()` to enforce "this sub-model only fires on its regime bars" — but a cleaner approach is the `RegimeRoutedStrategy` wrapper that dispatches at signal-time without modifying `LightGbmStrategy`'s prediction path.

### 3.4 LM Master Phase 4.5 Responses

**LM Master Phase 4.5 has NOT YET been dispatched for /024**. Once dispatched, this section is updated with QR responses per Phase 4.5 protocol. Brief Section 3.4 below RESERVED for LM Master responses; the brief commits at Phase 5 close with this section noting "LM Master Phase 4.5 PENDING — Section 3.4 will be populated post-advisory at brief revision commit".

Convergent priors carried from /023 LM Master advisory (Phase 7.4 §4 Option B):
- LM Master /023 recommended regime-conditional architecture as PRIMARY for /024.
- LM Master /023 §4 mandated DUAL GATE strengthening at /023; equivalent mandate at /024 likely on per-sub-model gain-share check (each sub-model's funding-feature importance × regime-matched-trade rate).
- LM Master /023 §5 tightened n_eff band to [5, 10] at 40-col profile; per-sub-model n_eff is critical given THIN extreme partition (Pool A extreme = ~14% of baseline rows).

QR EXPECTS LM Master to:
1. Raise INERT mass to 50-55% (LEARNED-NEGATIVE / basin-relocation lessons from /023 transferred).
2. Tighten extreme sub-model importance gate (rank ≤ 14/42 on ≥ 2 cohorts is the /023 DUAL GATE; for /024 may add per-cohort sub-model gain-share floor).
3. Recommend either ROUTING-FIRE-RATE BAND (e.g. extreme sub-model fires on 10-18% of bars × cohort) OR per-cohort sub-model trade-count floor (extreme sub-model emits ≥3 trades/month IS to avoid model degeneracy at single-seed).
4. Provide its own verdict-class priors (modal INERT 45-55%; PROMISING-clean 12-15%; PROMISING-INERT-FAV 6-10%; NEG clean 15-20%; NEG-CAT 5-10%; PROMISING-METHODOLOGY 2-5%).

This section will be UPDATED at brief revision commit post-Phase 4.5.

---

## Section 4 — Falsifiers

### 4.1 Primary falsifiers (Sharpe-Δ)

| Falsifier | Threshold | Decision Tier |
|---|---|---|
| **F1 OOS Sharpe Δ vs anchor +0.6637** | ≥ +0.10 | PROMISING |
| F1 OOS Sharpe Δ | [-0.55, +0.10) | INERT or PROMISING-INERT depending on mechanism |
| F1 OOS Sharpe Δ | ≤ -0.55 | NEGATIVE-CATASTROPHIC |
| F3 IS Sharpe Δ vs anchor +0.2829 | ≥ +0.10 | IS-positive; sign-consistent if F1 also positive |
| F3 IS Sharpe Δ | ≤ -0.30 | IS-catastrophic; reject regardless of OOS |

### 4.2 F-AXIS-MECHANISM falsifiers (mechanism integrity)

**F-AXIS-MECHANISM #1 — Dispatch correctness (binary)** (LOAD-BEARING):
- Each cohort produces 2 sub-model trade rosters labeled `extreme_<cohort>` and `normal_<cohort>` in `trades.csv` (NEW `model_name` column distinguishes).
- 8 unique `model_name` values in `trades.csv`: `Model_A_extreme`, `Model_A_normal`, `Model_C_extreme`, `Model_C_normal`, `Model_D_extreme`, `Model_D_normal`, `Model_E_extreme`, `Model_E_normal`.
- Engineering report MUST emit `per_cohort_per_regime_breakdown.csv` (8 rows × 12 columns: trades, wins, win_rate, net_pnl_pct, weighted_pnl, mean_z30_at_open, max_z30, min_z30, regime, cohort, train_bars, oos_trades).

**F-AXIS-MECHANISM #2 — Trade count bands**:
- IS trade count ∈ [400, 850] (baseline 621 ± 35% — wider band than /023's [500, 750] because regime partition reshapes trade emission rate).
- OOS trade count ∈ [120, 280] (baseline 189 ± 30%).
- OUTSIDE either band → trade-rate destabilization; flag for diary inspection.

**F-AXIS-MECHANISM #3 — Regime gate fire rate** (per-cohort):
- Per-cohort extreme sub-model fire rate (its share of cohort total IS trades) ∈ [8%, 25%] — baseline EDA shows 9-16% across cohorts.
- Per-cohort extreme sub-model fire rate OOS ∈ [5%, 30%] — wider OOS band per /022 + /023 precedent that OOS fire rates can drift.
- Falsifier: if any cohort's extreme fire rate IS or OOS falls outside the band → regime gate not engaging; downgrade F-AXIS #1.

**F-AXIS-MECHANISM #4 — Per-cohort sub-model n_eff_per_cell** (per /008 methodology substrate):
- Per-cohort EXTREME sub-model n_eff_per_cell ∈ **[3, 9]** (thin partition expected; THIN floor at 3 reflects 700-1573 bars vs baseline 5000-11000).
- Per-cohort NORMAL sub-model n_eff_per_cell ∈ [5, 10] (matches /023).
- Falsifier: if extreme sub-model n_eff_per_cell < 3 → label-collapse; if ≥ 12 → over-dispersed.

### 4.3 Composite verdict matrix (Section 8 row format)

See Section 8.

---

## Section 5 — Predicted Verdict Priors

### 5.1 Verdict priors (QR initial; awaiting LM Master Phase 4.5 RECALIBRATION)

| Verdict class | QR initial (pre-LM) | Rationale |
|---|---|---|
| **PROMISING (F1 Δ ≥ +0.10 + F-AXIS #1 PROMISING)** | **15%** | ORACLE +143pp ceiling suggests room; LEARNED-NEGATIVE at /023 means signal IS present but mis-extracted at pool — regime partition theoretically fixes this; but basin-relocation dissolution + thin extreme partition + DOT outlier = downweighted from naive +30% |
| **PROMISING-INERT-FAVORABLE (F1 Δ ≥ +0.10 + F-AXIS #1 not clean)** | **8%** | Lift via Optuna basin lottery on partition; less likely than feature-family /023 because 2 sub-models doubles the lottery surface but also doubles parameter-space cost |
| **INERT (F1 Δ ∈ [-0.30, +0.10) + F-AXIS #1 INERT)** | **42% (MODAL)** | Most likely: regime partition fragments training data, both sub-models under-train, predictions converge to pool baseline behavior |
| **NEGATIVE clean (F1 Δ ∈ [-0.55, -0.30))** | **18%** | Thin extreme partition (DOT 8 trades; LINK/LTC 17 trades) → extreme sub-model overfits; OOS routes into the overfit zone |
| **NEGATIVE-CATASTROPHIC (F1 Δ ≤ -0.55)** | **12%** | Higher than /023 (8%) because multi-model architecture is FIRST in v1 — basin-relocation across 2 sub-models is multiplicative; DOT outlier (3 trades short, contrary direction) could anchor sub-model to wrong direction |
| **PROMISING-METHODOLOGY (substrate finding)** | **5%** | Architectural axis may surface methodology insights (e.g. partition-stability diagnostic) without compoundable edge |

**Total**: 100%. **Modal: INERT at 42%** (LM Master may shift toward NEG +5pp per /023 LEARNED-NEGATIVE precedent transferring; PROMISING tail compressed to ~23% combined).

**Mass-shifting catalysts (post-LM Master Phase 4.5)**:
- IF LM Master predicts INERT modal ≥ 50% AND tail-weight NEG ≥ 25% → QR adopts LM Master priors per `feedback_iteration_quality.md` deference rule at ≥ 5pp.
- IF LM Master predicts PROMISING modal ≥ 30% → unusual; QR investigates; likely indicates LM Master sees strong basin-stability evidence.
- IF LM Master adds per-cohort sub-model gain-share gate → Section 4.2 F-AXIS-MECHANISM #1 strengthened.

---

## Section 6 — Failure Modes

### 6.1 Mode A: INERT — both sub-models converge to pool behavior (modal — 42% prior)

**Pattern**: extreme sub-model and normal sub-model produce trade rosters that overlap substantially (Jaccard > 0.30) with baseline pool's roster. F1 OOS Sharpe Δ flat (-0.30 to +0.10). Per-cohort regime fire rates near baseline trade-emission rate.

**Diagnostic**: F-AXIS-MECHANISM #1 dispatch PASS (8 sub-models trained); F-AXIS-MECHANISM #3 fire rates inside band but sub-model trade roster Jaccard with baseline > 0.30 → "sub-models converged to pool behavior despite partition". This means LightGBM treats the partition as noise (e.g. funding-z30 already partially encoded by features, partition adds no new information).

**Implication for cycle-3**: regime-conditional architecture CLOSED for cycle-3 at single-seed budget. /025 pivots to per-cohort drawdown brake (Path Forward #1 from /023) OR open-interest delta (different feature family, NEW sister primitive).

**Path Forward**: pre-committed via /025 routing matrix in Section 11.

### 6.2 Mode B: NEGATIVE — extreme sub-model overfit catastrophe

**Pattern**: F1 OOS Sharpe Δ ∈ [-0.55, -0.30) clean OR ≤ -0.55 catastrophic. Extreme sub-model has high IS Sharpe but OOS drift catastrophic; normal sub-model behaves like baseline. Combined trade roster pollutes baseline behavior with extreme sub-model's bad OOS picks.

**Diagnostic**: per-cohort EXTREME sub-model IS-OOS Sharpe Δ << -0.30 while NORMAL sub-model IS-OOS Sharpe Δ near zero. Per-cohort breakdown reveals which sub-model dragged.

**Implication**: per /023 LEARNED-NEGATIVE pattern at sub-model level — extreme sub-model LEARNS its regime IS but OOS retrained roster has different regime trajectories; sub-model amplifies the dissolution.

### 6.3 Mode C: PROMISING clean (15% prior — basin-level edge harvested)

**Pattern**: F1 OOS Sharpe Δ ≥ +0.10 (≥ +0.7637 OOS Sharpe absolute). F-AXIS-MECHANISM #1 dispatch + fire-rate bands all in range. Per-cohort EXTREME sub-model produces a SHORT-biased trade roster in extreme regime (matching EDA Section 2.2 short-direction edge). NORMAL sub-model produces a LONG-biased roster (matching NORMAL section longs +).

**Diagnostic**: per-cohort breakdown shows extreme sub-model short trades net positive, normal sub-model long trades net positive. The partition harvested the direction sign-flip that the ORACLE EDA Section 2.2 quantified.

**Implication**: /027 CONFIRMATION includes regime-conditional architecture as 3rd alpha-enhancement component.

### 6.4 Mode D: PROMISING-INERT-FAVORABLE (8% prior)

**Pattern**: F1 OOS Sharpe Δ ≥ +0.10 BUT F-AXIS-MECHANISM #1 mechanism NOT clean (extreme + normal sub-model trade rosters substantially overlap baseline). Lift not attributable to regime mechanism.

**Diagnostic**: Optuna lottery at 2× sub-model parameter space surface produced a better-luck combination. NOT bundleable.

### 6.5 Mode E: DOT outlier dominates

**Pattern**: DOT sub-models (extreme partition only 8 trades) produce noisy trade rosters that diverge from other 3 cohorts. Pool A + LINK + LTC sub-models PROMISING but DOT sub-models NEG. Portfolio F1 Δ mixed (~0).

**Diagnostic**: per-cohort breakdown shows DOT (extreme + normal) is the source of drag.

**Implication**: future /024 variant could exclude DOT from regime conditioning (DOT stays in baseline pool dispatch).

---

## Section 7 — Pre-registered failure-mode predictions

### 7.1 LM Master Phase 4.5 will adjudicate

LM Master Phase 4.5 produces verdict-class priors at `briefs-v1/iteration_v1-024/lgbm_advisor.md`. QR will adopt LM Master priors over Section 5 if LM Master tail-class re-weighting > 5pp per `feedback_iteration_quality.md`.

### 7.2 Pre-committed verdict-mass-shifting rules

- IF LM Master predicts EXTREME sub-model n_eff_per_cell < 3 for ≥ 2 cohorts → QR shifts NEG-tail mass +5pp (toward 30%); investigates whether to drop DOT extreme partition.
- IF LM Master proposes adding per-cohort sub-model gain-share gate → Section 4.2 F-AXIS-MECHANISM #1 strengthened with explicit threshold table.
- IF LM Master strongly recommends multi-seed mitigation (against QR single-seed default) → QR reconsiders Section 2.5 mitigation declaration.

---

## Section 8 — MERGE/NO-MERGE Verdict Matrix

| Row | F1 OOS Sharpe Δ | F3 IS Sharpe Δ | F-AXIS #1 (8 sub-models per regime) | F-AXIS #3 fire rate | n_eff | Verdict |
|---|---|---|---|---|---|---|
| 1 | ≥ +0.10 | ≥ +0.10 | 8 sub-models dispatched; per-cohort breakdown shows partition signal; extreme sub-model short-bias evident | per-cohort IS [8%, 25%] | extreme [3,9], normal [5,10] | **PROMISING (clean)** — /027 bundle candidate |
| 2 | ≥ +0.10 | ≥ +0.10 | 8 sub-models dispatched but extreme + normal sub-model trade rosters ≥ 30% overlap baseline | any | extreme [3,9] | PROMISING-INERT-FAVORABLE — NOT bundleable, catalog only |
| 3 | ≥ +0.10 | ∈ [-0.10, +0.10) | partial | any | extreme [3,9] | PROMISING-WEAK — sign-consistent but IS noise |
| 4 | ∈ [-0.10, +0.10) | any | INERT (sub-models converge to pool) | any | extreme [3,9] | **INERT** — architectural mechanism CLOSED for cycle-3 |
| 5 | ∈ [-0.55, -0.10) | any | any | any | extreme [3,9] | NEGATIVE clean — axis CLOSED for cycle-3 |
| 6 | ≤ -0.55 | any | any | any | any | **NEGATIVE-CATASTROPHIC** — 3rd cycle-3 HIGH-RISK NEG-CAT formally trips multi-seed mandate for /025 |
| 7 | any | ≤ -0.30 | any | any | any | IS-catastrophic — reject regardless of OOS |
| 8 | any | any | any | per-cohort outside [8%, 25%] IS or [5%, 30%] OOS for ≥ 2 cohorts | any | F-AXIS #3 FAIL — regime gate not engaging; downgrade to INERT |
| 9 | any | any | any | any | extreme < 3 OR ≥ 12 for ≥ 2 cohorts | n_eff degenerate — methodology issue, separate diary section |

**NO-MERGE if** Row 4, 5, 6, 7, 8, OR 9 fires. **MERGE candidate to /027 bundle if** Row 1 fires (clean PROMISING).

---

## Section 9 — Library Stack

- `pandas>=2.0` — DataFrame ops (existing).
- `numpy>=1.24` — z-score lookups (existing).
- `lightgbm>=4.5.0` — already used by `LightGbmStrategy`; no change.
- No NEW external dependencies.
- Existing test suite under `tests/` validates `LightGbmStrategy`, `risk_v2.py` patterns; NEW `tests/strategies/test_regime_gate_v1.py` validates `RegimeGateConfig` + `route_trades_by_regime` + past-only z30 lookup.

---

## Section 10 — Run Protocol

### 10.1 Pre-Phase 6 gates

- Phase 5.5 gate (Engineer): verifies brief sections 0.5/0.6/2.5/3.4 present; verifies LM Master integration; verifies cadence + axis rotation rules.
- Phase 6.0 pre-flight (Critic): static scan for look-ahead in `regime_gate_v1.py` (z30 lookup must use `.shift(1)` via parquet column already past-only); `data_filter_callback` integration with `_train_for_month()` must preserve walk-forward boundaries; `train_end_ms = test_start_ms - embargo_ms` regression check.

### 10.2 Engineering dispatch parameters

- Single-seed EXPLORATION: `--seed 42`, `--n-trials 18`, `ENSEMBLE_SIZE=3`, V1_FEATURE_COLUMNS_PRUNED 42 cols (unchanged from /023 — keeps funding columns since regime gate reads z30 from parquet).
- Universe: full V1_BASELINE_UNIVERSE (BTC, ETH, LINK, LTC, DOT). 4 cohorts × 2 sub-models = **8 LightGBM sub-models trained**.
- No HIGH-RISK multi-seed validation opt-in (per Section 2.5 — single-seed for axis isolation).

### 10.3 Kill criteria

- Wall-clock > 110 min → engineer SIGTERM the backtest; document in engineering_report.md.
- Feature pipeline failure (parquet missing funding columns) → BLOCK; no F-AXIS-MECHANISM evaluation.
- Any sub-model fails to train (extreme partition < 100 rows for a (cohort, month) cell) → graceful degrade (sub-model skip-month); document in engineering_report.md.
- Per-cohort EXTREME sub-model trade count < 5 IS total → suggests partition too thin; document but do not BLOCK.

### 10.4 Engineering report — BINDING contract (6th cycle-3 incident risk at /024)

**Per /023 Critic FINAL Recommendation #3 (CARRY-FORWARD from /020/021/022 Rec #1) BINDING**:

This brief LOAD-BEARINGLY pre-commits: **NO Phase 7.5 Critic dispatch without `reports-v1/iteration_v1-024/engineering_report.md` present**. Incident rate of 5/5 cycle-3 iterations confirms brief-level contracts insufficient; the orchestrator-layer fix is the actual solution but is OUT-OF-SCOPE for this brief (skill-maintainer scope per /023 Rec #3).

**Pre-commit content** (engineering_report.md must document):
1. Implementation summary (NEW src/crypto_trade/strategies/regime_gate_v1.py + data_filter_callback in LightGbmStrategy + V1_ITER024 dispatch + run_baseline_v1.py 8-sub-model orchestration).
2. Backtest configuration (single-seed=42, ENSEMBLE_SIZE=3, n_trials=18, V1_FEATURE_COLUMNS_PRUNED 42 cols, V1_BASELINE_UNIVERSE 5 syms, 4 cohorts × 2 sub-models).
3. Wall-clock + per-sub-model timing breakdown (8 sub-models).
4. F-AXIS-MECHANISM #1-4 measurement values + thresholds (per-cohort × per-regime breakdown CSV).
5. ALL test commands run + outputs (tests/strategies/test_regime_gate_v1.py).
6. Anomaly notes (sub-model skip-months, thin partitions, DOT outlier behavior) + reproduce command.

**Mandatory deliverable**: `per_cohort_per_regime_breakdown.csv` (8 rows = 4 cohorts × 2 regimes) with columns: cohort, regime, train_bars, trades_is, trades_oos, win_rate_is, win_rate_oos, net_pnl_is, net_pnl_oos, sharpe_is, sharpe_oos, mean_z30_at_open.

### 10.5 Test suite additions

`tests/strategies/test_regime_gate_v1.py` (NEW):
- Verify `RegimeGateConfig` defaults match Section 3.1.
- Verify `route_trades_by_regime` correctly routes by z30 lookup (e.g. trade A at z30=2.0 routes to extreme list; trade B at z30=0.5 routes to normal list).
- Verify `evaluate_regime_at_signal` returns correct label.
- Past-only invariant: z30 lookup at trade.open_time uses parquet's z30 column (which is past-only by /023 `.shift(1)` design).
- Edge cases: missing z30 (early bars NaN) → trade defaults to normal sub-model.

Integration test (`tests/test_run_baseline_v1_iter024.py` NEW):
- Verify V1_ITER024 dispatch produces 8 sub-models when iteration_label="v1-024".
- Verify per_cohort_per_regime_breakdown.csv schema.

### 10.6 Reproduce command

```
uv run python run_baseline_v1.py \
  --pruned-features \
  --iteration-label v1-024 \
  --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT \
  --interval 8h \
  --n-trials 18 \
  --exploration \
  --seeds 1 \
  --seed 42 \
  --output-dir reports-v1/iteration_v1-024/
```

(Engineer to confirm `--iteration-label` flag exists; current runner uses `iteration_label` argparse arg, default "baseline".)

---

## Section 11 — Conditional Roadmap (/025+)

### 11.1 If /024 = PROMISING (clean) — Row 1

**/025 priority**: regime-conditional VARIANTS — explore tri-partition `[|z|<0.5, 0.5<|z|<1.5, |z|>1.5]` OR stack regime gates on different feature families (e.g. regime by funding × regime by BTC trend). Family `model-arch` REPEAT (same family allowed within bundle-building phase).

**/026**: pre-CONFIRMATION sanity (final EXPLORATION).

**/027 CONFIRMATION**: 3-component bundle = pool baseline + LINK specialist (/018) + ETH+gate specialist (/019) + **regime-conditional architecture (/024)** as 3rd alpha-enhancement component. Bundle target +1.30-1.60 OOS Sharpe under multi-seed correlation drag.

### 11.2 If /024 = PROMISING-INERT-FAVORABLE — Row 2

**/025 priority**: open-interest delta family (different feature family) OR per-cohort drawdown brake (Path Forward #1 from /023). Regime-conditional axis is "lift without mechanism" → NOT bundleable to /027.

**/027 substrate UNCHANGED** vs /023 post-state (pool + LINK + ETH+gate; no /024 contribution).

### 11.3 If /024 = INERT — Row 4 (MODAL)

**/025 priority**: per-cohort drawdown brake — family `risk-primitive`; STATEFUL → MANDATORY deadlock-impossibility proof per A8 catalog + iter-v3/054 lesson.

**/027 substrate UNCHANGED** vs /023 post-state.

### 11.4 If /024 = NEGATIVE clean — Row 5

Same as 11.3. Axis CLOSED for cycle-3.

### 11.5 If /024 = NEGATIVE-CATASTROPHIC — Row 6

**3rd cycle-3 >1σ HIGH-RISK NEG-CAT trip**: /025 mandatory multi-seed HIGH-RISK iteration. /025 axis: open-interest delta family at multi-seed (NEW non-OHLCV feature family) OR per-cohort drawdown brake at multi-seed.

### 11.6 /027 bundle composition impact

- **/024 PROMISING** → 3rd alpha-enhancement (regime-conditional architecture) → bundle target +1.30-1.60.
- **/024 PROMISING-INERT-FAVORABLE / INERT / NEG clean** → bundle UNCHANGED at +1.20-1.50 (pool + LINK + ETH+gate).
- **/024 NEG-CAT** → bundle UNCHANGED + /025 mandatory multi-seed.

### 11.7 LM Master /025 staging matrix (placeholder until Phase 4.5)

LM Master Phase 4.5 will produce a similar /025 staging matrix in `lgbm_advisor.md`. QR will adopt LM Master staging if it differs materially from Section 11.1-11.5 above.

### 11.8 If /024 = sample-size-too-small (Row 9)

Methodology issue. /025 advances to /025's original menu (NOT regime-conditional related); /024 catalogued as NEGATIVE n_eff-degenerate. Investigate per-cohort sub-model n_eff × partition-thinness interaction in separate analysis.

---

## Section 12 — Roll-back Protocol

### 12.1 Code roll-back

- `src/crypto_trade/strategies/regime_gate_v1.py` is NEW module — roll-back = file deletion.
- `src/crypto_trade/strategies/ml/lgbm.py:data_filter_callback` extension is backward-compatible (default None preserves bit-identical baseline behavior) — roll-back = parameter removal.
- `run_baseline_v1.py:V1_ITER024` dispatch branch is NEW elif — roll-back = elif removal.
- V1_FEATURE_COLUMNS_PRUNED unchanged at 42 cols (funding columns kept from /023 since regime gate reads z30 from parquet).

### 12.2 Trunk merge plan

Per `feedback_v3_baseline_update_policy.md` adopted by v1: BASELINE_V1.md UPDATE NOT triggered unless CONFIRMATION-MERGE. /024 is EXPLORATION; even PROMISING verdict does NOT update baseline.

**Trunk merge** (if /024 verdict in {PROMISING, INERT, NEG-clean} — non-CAT, non-failure):
- `src/crypto_trade/strategies/regime_gate_v1.py` — NEW module, additive, backward-compatible. Merges to trunk via branch HEAD.
- `src/crypto_trade/strategies/ml/lgbm.py:data_filter_callback` — backward-compatible (default None). Merges to trunk.
- `run_baseline_v1.py:V1_ITER024_*` — opt-in dispatch elif (not invoked at default baseline). Stays on branch (opt-in opt-out).

**Trunk merge** (if /024 verdict = NEG-CAT or failure):
- All src/ changes STAY ON BRANCH (no trunk merge).
- Only diary + brief + EDA scripts cherry-pick to trunk.

### 12.3 BASELINE_V1.md UPDATE NOT triggered

Per `feedback_v3_baseline_update_policy.md`: only CONFIRMATION-MERGE updates baseline. /024 is EXPLORATION → BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`).

---

## Section 13 — Self-Check

### 13.1 Brief contains all 11 required QR sections per v1 skill

- [x] Section 0 (Position in cycle / pivot context) with 0.5 cadence, 0.6 axis-family, 0.7 wall-clock
- [x] Section 1 (Hypothesis with mechanism story)
- [x] Section 2 (IS-only Evidence — 5 EDA tables from committed scripts)
- [x] Section 2.5 (HIGH-RISK declaration)
- [x] Section 3 (Proposed Changes; 3.4 LM Master responses RESERVED PENDING)
- [x] Section 4 (Falsifiers — F1 + F-AXIS-MECHANISM #1-4)
- [x] Section 5 (Predicted verdict priors; QR initial, awaiting LM Master recalibration)
- [x] Section 6 (Failure modes A-E)
- [x] Section 7 (Pre-registered failure-mode predictions, mass-shifting rules)
- [x] Section 8 (MERGE/NO-MERGE verdict matrix — 9 rows)
- [x] Section 9 (Library stack)
- [x] Section 10 (Run protocol — gates, dispatch, kill, engineering report, tests, reproduce)
- [x] Section 11 (Conditional roadmap /025+; 11.6 /027 bundle impact; 11.7 LM Master staging placeholder)
- [x] Section 12 (Roll-back; trunk merge plan)
- [x] Section 13 (Self-check — this section)

### 13.2 Anchor numbers cited correctly

- F1 anchor +0.6637 OOS Sharpe (BASELINE_V1.md line 65 comparison.csv "sharpe" row OOS)
- F3 anchor +0.2829 IS Sharpe (BASELINE_V1.md line 65 comparison.csv "sharpe" row IS)
- OOS trades 189; IS trades 621 (BASELINE_V1.md line 70)

### 13.3 LOAD-BEARING priors from /023 honored

- LEARNED-NEGATIVE classification carried forward (Section 0.4 + Section 1)
- DUAL GATE gain-share evidence 3/4 cohorts informs hypothesis (Pool A 6.88%, LINK 5.65%, DOT 5.49%)
- Per-cohort SATURATION rule honored (model-arch is NEW family, NOT per-cohort isolation)
- Anchor-frame BINDING (F1 = comparison.csv "sharpe" daily-annualized; Section 0.3)
- engineering_report.md BINDING contract (Section 10.4)

### 13.4 ORACLE EDA caveat applied

Section 1 + Section 2.6 explicitly disclaim: ORACLE +143pp ceiling is descriptively valid (regime gate STATELESS); does NOT predict /024 outcome. Realistic F1 OOS Sharpe Δ envelope ∈ [-0.10, +0.30] with mode ~+0.05.

### 13.5 Axis Rotation Discipline honored

Section 0.6 declares prior 5: {ETH per-cohort /019, BTC per-cohort /020, methodology-pivot /021, LTC per-cohort /022, feature-family /023}. model-arch is NOT in this set. Rotation VALID. Phase 5.5 gate will verify.

### 13.6 USER STRATEGIC DIRECTIVE alignment

User's verbatim: "be bold. diversification is the key. multiple smaller models each model performing well under different regimes."
- "be bold" → model-arch family is NEW 16th family, FIRST multi-model architecture in v1.
- "diversification is the key" → 8 sub-models across 4 cohorts × 2 regimes = first architectural diversification at MODEL layer.
- "multiple smaller models each model performing well under different regimes" → exact mechanism. Extreme sub-model specializes on extreme-regime training rows; normal sub-model on normal.
- "many risk controls to test, features, labels. just use your imagination" → /024 picks the SOLE bold option (model-arch); /025 staging matrix preserves freedom to explore further (risk controls, features, labels) in /026.

### 13.7 BOLD vs incremental classification

**This iteration is GENUINELY BOLD**:
- First multi-model architecture in v1 history (20+ iterations).
- 8 sub-models trained (vs 4 baseline) — 2× architectural complexity.
- Direct test of user's "smaller models per regime" thesis with ORACLE-quantified ceiling (+143pp IS theoretical max).
- HIGH-RISK declaration MANDATORY (Critic /023 Path Forward #2).
- /025 staging matrix preserves 5 alternative axes if /024 fails.

This is NOT an incremental tweak. It is a STRUCTURAL ARCHITECTURE shift from "pool-with-features" to "regime-conditional-sub-models". If PROMISING, /027 bundle gains a 3rd genuinely-novel alpha-enhancement component. If NEGATIVE, the architectural ceiling for current cohort/feature/risk substrate is rigorously bounded.
